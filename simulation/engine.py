"""
SimulationEngine: orchestrates all simulation modules.
Coordinates state updates, manages simulation loop, and handles cross-module interactions.
"""

import json
import logging
import math
import queue
import threading
import time
from typing import Any, Dict, List, Optional, Union

from config.config import RHO_WATER, G  # Add physics constants

# Import Pydantic schemas for type safety
from simulation.schemas import (
    SimulationParams, SimulationState, SimulationStepResponse,
    PhysicsResults, SystemResults, ComponentStatus, ManagerInterface,
    SimulationError, ValidationError, HealthCheckResponse
)

# Import new physics modules
from simulation.components.chain import Chain
from simulation.components.clutch import OverrunningClutch
from simulation.components.control import Control
from simulation.components.drivetrain import Drivetrain
from simulation.components.environment import Environment
from simulation.components.floater import Floater
from simulation.components.fluid import Fluid
from simulation.components.gearbox import create_kpp_gearbox
from simulation.components.generator import Generator
from simulation.components.integrated_drivetrain import (
    IntegratedDrivetrain,
    create_standard_kpp_drivetrain,
)
from simulation.components.integrated_electrical_system import (
    IntegratedElectricalSystem,
    create_standard_kmp_electrical_system,
)
from simulation.components.pneumatics import PneumaticSystem
from simulation.components.sensors import Sensors
from simulation.components.sprocket import Sprocket
from simulation.components.thermal import ThermalModel
from simulation.control.integrated_control_system import (
    IntegratedControlSystem,
    create_standard_kpp_control_system,
)
from simulation.control.transient_event_controller import TransientEventController
from simulation.grid_services import (
    GridConditions,
    GridServicesCoordinator,
    create_standard_grid_services_coordinator,
)
from simulation.physics.integrated_loss_model import (
    IntegratedLossModel,
    create_standard_kpp_enhanced_loss_model,
)

# Import H1, H2, H3 enhanced physics
from simulation.physics.nanobubble_physics import NanobubblePhysics
from simulation.physics.pulse_controller import PulseController
from simulation.physics.thermal_physics import ThermalPhysics
from utils.logging_setup import setup_logging

# Import new manager classes for modular architecture
from simulation.managers.physics_manager import PhysicsManager
from simulation.managers.system_manager import SystemManager
from simulation.managers.state_manager import StateManager
from simulation.managers.component_manager import ComponentManager

setup_logging()
logger = logging.getLogger(__name__)


class SimulationEngine:
    """
    Main simulation engine for the KPP system.
    Orchestrates all components and manages simulation state and loop.
    """

    def __init__(self, params: Union[Dict[str, Any], SimulationParams], data_queue: queue.Queue) -> None:
        """
        Initialize the simulation engine and all components.

        Args:
            params: Simulation parameters dictionary or SimulationParams schema
            data_queue: Queue for streaming simulation data
        """
        # Convert and validate parameters using Pydantic schema
        if isinstance(params, dict):
            try:
                self.validated_params = SimulationParams(**params)
                self.params = params  # Keep original dict for legacy compatibility
            except Exception as e:
                logger.error(f"Parameter validation failed: {e}")
                # Fallback to original dict with warnings
                self.params = params
                self.validated_params = None
                logger.warning("Using unvalidated parameters - some features may not work correctly")
        else:
            self.validated_params = params
            self.params = params.model_dump()  # Convert to dict for legacy code

        # Use validated parameters when available, fallback to dict lookup
        def get_param(key: str, default: Any = None) -> Any:
            if self.validated_params:
                return getattr(self.validated_params, key, default)
            return self.params.get(key, default)

        self.data_queue = data_queue
        self.running = False
        self.time = 0.0
        self.dt = get_param("time_step", 0.1)
        self.last_pulse_time = -999  # Allow immediate first pulse
        self.environment = Environment()
        self.pneumatics = PneumaticSystem(
            target_pressure=get_param("target_pressure", 5.0)
        )

        # Initialize the new integrated drivetrain system
        drivetrain_config = {
            "sprocket_radius": get_param("sprocket_radius", 1.0),
            "sprocket_teeth": get_param("sprocket_teeth", 20),
            "clutch_engagement_threshold": get_param(
                "clutch_engagement_threshold", 0.1
            ),
            "flywheel_moment_of_inertia": get_param("flywheel_inertia", 50.0),
            "flywheel_target_speed": get_param("flywheel_target_speed", 375.0),
            "pulse_coast_pulse_duration": get_param("pulse_duration", 2.0),
            "pulse_coast_coast_duration": get_param("coast_duration", 1.0),
        }
        self.integrated_drivetrain = create_standard_kpp_drivetrain(drivetrain_config)

        # Initialize the integrated electrical system (Phase 3)
        electrical_config = {
            "rated_power": get_param("target_power", 530000.0),
            "load_management": get_param("electrical_load_management", True),
            "target_load_factor": get_param("electrical_load_factor", 0.8),
            "generator": {
                "rated_power": get_param("target_power", 530000.0),
                "rated_speed": get_param("target_rpm", 375.0),
                "efficiency_at_rated": get_param("generator_efficiency", 0.94),
            },
            "power_electronics": {
                "rectifier_efficiency": get_param("pe_rectifier_efficiency", 0.97),
                "inverter_efficiency": get_param("pe_inverter_efficiency", 0.96),
                "transformer_efficiency": get_param(
                    "pe_transformer_efficiency", 0.985
                ),
            },
        }
        self.integrated_electrical_system = create_standard_kmp_electrical_system(
            electrical_config
        )

        # Initialize the integrated control system (Phase 4)
        control_config = {
            "num_floaters": get_param("num_floaters", 8),
            "target_power": get_param("target_power", 530000.0),
            "prediction_horizon": get_param("control_prediction_horizon", 5.0),
            "optimization_window": get_param("control_optimization_window", 2.0),
            "power_tolerance": get_param("control_power_tolerance", 0.05),
            "max_ramp_rate": get_param("control_max_ramp_rate", 50000.0),
            "nominal_voltage": get_param("grid_nominal_voltage", 480.0),
            "nominal_frequency": get_param("grid_nominal_frequency", 60.0),
            "voltage_regulation_band": get_param("grid_voltage_regulation_band", 0.05),
            "frequency_regulation_band": get_param(
                "grid_frequency_regulation_band", 0.1
            ),
            "monitoring_interval": get_param("control_monitoring_interval", 0.1),
            "auto_recovery_enabled": get_param("control_auto_recovery", True),
            "predictive_maintenance_enabled": get_param(
                "control_predictive_maintenance", True
            ),
            "emergency_response_enabled": get_param(
                "control_emergency_response", True
            ),
            "adaptive_control_enabled": get_param("control_adaptive_enabled", True),
        }
        self.integrated_control_system = create_standard_kpp_control_system(
            control_config
        )
        # Initialize enhanced loss model (Phase 5)
        ambient_temperature = get_param("ambient_temperature", 20.0)
        self.integrated_loss_model = create_standard_kpp_enhanced_loss_model(
            ambient_temperature
        )
        # Legacy alias for compatibility
        self.enhanced_loss_model = self.integrated_loss_model

        # Initialize transient event controller (Phase 6)
        transient_config = {
            "startup": {
                "target_startup_speed": get_param("startup_target_speed", 100.0),
                "target_operational_speed": get_param("target_rpm", 375.0),
                "acceleration_rate": get_param("startup_acceleration_rate", 10.0),
                "sync_retry_limit": get_param("startup_sync_retries", 3),
            },
            "emergency": {
                "max_flywheel_speed": get_param("emergency_max_flywheel_speed", 450.0),
                "max_tank_pressure": get_param("emergency_max_pressure", 8.0),
                "max_component_temperature": get_param(
                    "emergency_max_temperature", 85.0
                ),
                "max_torque": get_param("emergency_max_torque", 3000.0),
            },
            "grid": {
                "frequency_droop": get_param("grid_frequency_droop", 0.05),
                "voltage_droop": get_param("grid_voltage_droop", 0.02),
                "max_frequency_response": get_param("grid_max_freq_response", 0.2),
                "max_reactive_power": get_param("grid_max_reactive_power", 0.3),
            },
            "auto_startup": get_param("auto_startup_enabled", True),
            "auto_recovery": get_param("auto_recovery_enabled", True),
            "grid_support": get_param("grid_support_enabled", True),
        }
        self.transient_controller = TransientEventController(transient_config)

        # Keep legacy drivetrain for compatibility during transition
        self.drivetrain = Drivetrain(
            gear_ratio=get_param("gear_ratio", 16.7),
            efficiency=get_param("drivetrain_efficiency", 0.95),
            sprocket_radius=get_param("sprocket_radius", 0.5),
            flywheel_inertia=get_param("flywheel_inertia", 50.0),
        )
        # Keep legacy generator for compatibility during transition
        self.generator = Generator(
            efficiency=get_param("generator_efficiency", 0.92),
            target_power=get_param("target_power", 530000.0),
            target_rpm=get_param("target_rpm", 375.0),
        )
        self.floaters = [
            Floater(
                volume=get_param("floater_volume", 0.3),
                mass=get_param("floater_mass_empty", 18.0),
                area=get_param("floater_area", 0.035),
                drag_coefficient=get_param("drag_coefficient", 0.8),
                air_fill_time=get_param("air_fill_time", 0.5),
                added_mass=get_param("floater_added_mass", 5.0),
                phase_offset=2 * math.pi * i / get_param("num_floaters", 1),
            )
            for i in range(get_param("num_floaters", 1))
        ]
        self.control = Control(self)
        self.sensors = Sensors(self)
        self.clutch = OverrunningClutch(
            tau_eng=get_param("clutch_tau_eng", 200),
            slip_time=get_param("clutch_slip_time", 0.2),
            w_min=get_param("clutch_w_min", 5),
            w_max=get_param("clutch_w_max", 40),
        )

        # Legacy drivetrain components (kept for compatibility during transition)
        self.top_sprocket = Sprocket(
            radius=get_param("sprocket_radius", 1.0),
            tooth_count=get_param("sprocket_teeth", 20),
            position="top",
        )
        self.bottom_sprocket = Sprocket(
            radius=get_param("sprocket_radius", 1.0),
            tooth_count=get_param("sprocket_teeth", 20),
            position="bottom",
        )
        self.gearbox = create_kpp_gearbox()
        # Chain properties
        self.chain_length = get_param("chain_length", 50.0)  # Total chain length (m)
        self.chain_mass_per_meter = get_param("chain_mass_per_meter", 10.0)  # kg/m
        self.chain_tension = 0.0  # Current chain tension (N)

        self.data_log = []
        self.output_data = []  # For analysis collection in SSE streaming
        self.total_energy = 0.0
        self.pulse_count = 0
        self.thread = None
        
        # Initialize grid services response tracking
        self._last_grid_services_response = {}

        # Initialize H1, H2, H3 Enhanced Physics (Stage 2)
        physics_config = {
            "water_density": get_param("water_density", 1000.0),
            "water_temperature": get_param("water_temperature", 293.15),
            "gravity": get_param("gravity", 9.81),
        }

        # H1 Nanobubble Physics
        h1_config = physics_config.copy()
        h1_config.update(
            {
                "h1_enabled": get_param("h1_enabled", False),
                "nanobubble_fraction": get_param("nanobubble_frac", 0.0),
                "drag_reduction_factor": get_param("drag_reduction_factor", 0.12),
                "bubble_generator_power": get_param(
                    "nanobubble_generation_power", 2500.0
                ),
            }
        )
        self.nanobubble_physics = NanobubblePhysics(
            enabled=h1_config["h1_enabled"],
            nanobubble_fraction=h1_config["nanobubble_fraction"],
            generation_power=h1_config["bubble_generator_power"],
            max_drag_reduction=h1_config["drag_reduction_factor"],
        )

        # H2 Thermal Physics
        h2_config = physics_config.copy()
        h2_config.update(
            {
                "h2_enabled": get_param("h2_enabled", False),
                "thermal_efficiency": get_param("thermal_efficiency", 0.75),
                "water_temperature": get_param("water_temperature", 293.15),
                "surface_area": get_param("floater_area", 0.035)
                * 2.0,  # Air-water interface
            }
        )
        self.thermal_physics = ThermalPhysics(
            enabled=h2_config["h2_enabled"],
            thermal_coefficient=0.0001,  # Default thermal expansion coefficient
            thermal_efficiency=h2_config["thermal_efficiency"],
            target_temperature=h2_config["water_temperature"],
        )

        # H3 Pulse Controller
        h3_config = {
            "h3_enabled": get_param("h3_enabled", False),
            "pulse_enabled": get_param("pulse_enabled", False),
            "pulse_duration": get_param("pulse_duration", 5.0),
            "coast_duration": get_param("coast_duration", 5.0),
            "pulse_duty_cycle": get_param("pulse_duty_cycle", 0.5),
        }
        self.pulse_controller = PulseController(
            enabled=h3_config["h3_enabled"],
            pulse_duration=h3_config["pulse_duration"],
            coast_duration=h3_config["coast_duration"],
            initial_phase="pulse",
        )

        # Enhanced physics state tracking
        self.h1_nanobubbles_active = h1_config["h1_enabled"]
        self.h2_thermal_active = h2_config["h2_enabled"]
        self.h3_pulse_active = h3_config["h3_enabled"]
        self.enhanced_physics_enabled = any(
            [self.h1_nanobubbles_active, self.h2_thermal_active, self.h3_pulse_active]
        )

        logger.info("SimulationEngine initialized with integrated drivetrain system.")
        logger.info(
            f"Enhanced physics: H1={self.h1_nanobubbles_active}, "
            f"H2={self.h2_thermal_active}, H3={self.h3_pulse_active}"
        )
        # Initialize default chain geometry for torque calculations
        self.set_chain_geometry()        # Initialize grid services coordinator (Phase 7)
        grid_services_config = {
            "enable_frequency_services": get_param("enable_frequency_services", True),
            "enable_voltage_services": get_param("enable_voltage_services", True),
            "enable_demand_response": get_param("enable_demand_response", True),
            "enable_energy_storage": get_param("enable_energy_storage", True),
            "enable_economic_optimization": get_param(
                "enable_economic_optimization", True
            ),
            "max_simultaneous_services": get_param("max_simultaneous_services", 5),
            "max_frequency_response": get_param("max_frequency_response", 0.15),
            "max_voltage_response": get_param("max_voltage_response", 0.10),
            "max_storage_response": get_param("max_storage_response", 0.20),
        }
        self.grid_services_coordinator = create_standard_grid_services_coordinator()

        # Initialize new physics modules (Chain, Fluid, Thermal)
        # Chain system configuration
        chain_config = {
            "sprocket_radius": get_param("sprocket_radius", 1.0),
            "tank_height": get_param("tank_height", 10.0),
            "chain_mass_per_meter": get_param("chain_mass_per_meter", 10.0),
            "num_floaters": get_param("num_floaters", 8),
            "max_tension": get_param("max_chain_tension", 50000.0),
            "elastic_modulus": get_param("chain_elastic_modulus", 200e9),
            "cross_sectional_area": get_param("chain_cross_section", 0.001),
        }
        self.chain_system = Chain(chain_config)

        # Fluid system configuration
        fluid_config = {
            "water_density": get_param("water_density", 1000.0),
            "water_temperature": get_param("water_temperature", 293.15),
            "gravity": get_param("gravity", 9.81),
            "kinematic_viscosity": get_param("kinematic_viscosity", 1.0e-6),
            "drag_coefficient": get_param("drag_coefficient", 0.6),
            "floater_area": get_param("floater_area", 0.1),
            "h1_active": get_param("h1_active", False),
            "h1_bubble_fraction": get_param("h1_bubble_fraction", 0.05),
            "h1_drag_reduction": get_param("h1_drag_reduction", 0.1),
        }
        self.fluid_system = Fluid(fluid_config)

        # Thermal model configuration
        thermal_config = {
            "water_temperature": get_param("water_temperature", 293.15),
            "ambient_temperature": get_param("ambient_temperature", 293.15),
            "h2_active": get_param("h2_active", False),
            "h2_efficiency": get_param("h2_efficiency", 0.8),
            "h2_buoyancy_boost": get_param("h2_buoyancy_boost", 0.05),
            "h2_compression_improvement": get_param(
                "h2_compression_improvement", 0.15
            ),
        }
        self.thermal_model = ThermalModel(thermal_config)

        logger.info("Chain, Fluid, and Thermal systems initialized")
        # Initialize Phase 7 pneumatic coordinator integration
        from simulation.pneumatics.energy_analysis import (
            create_standard_energy_analyzer,
        )
        from simulation.pneumatics.performance_metrics import (
            create_standard_performance_analyzer,
        )
        from simulation.pneumatics.pneumatic_coordinator import (
            create_standard_kpp_pneumatic_coordinator,
        )

        # Pneumatic system coordinator configuration
        enable_thermal_mgmt = get_param("thermal_management_enabled", True)
        enable_optimization = get_param("pneumatic_optimization_enabled", True)

        self.pneumatic_coordinator = create_standard_kpp_pneumatic_coordinator(
            enable_thermodynamics=enable_thermal_mgmt,
            enable_optimization=enable_optimization,
        )
        # Initialize Phase 7 energy analysis and performance monitoring
        compressor_power = get_param("compressor_power", 4200.0)  # 4.2 kW
        self.pneumatic_energy_analyzer = create_standard_energy_analyzer(
            analysis_window=60.0
        )
        self.pneumatic_performance_analyzer = create_standard_performance_analyzer(
            rated_power=compressor_power
        )

        logger.info(
            "Pneumatic coordinator and performance analysis systems initialized"
        )

        # Initialize the new manager classes for modular architecture
        self.physics_manager = PhysicsManager(self)
        self.system_manager = SystemManager(self)
        self.state_manager = StateManager(self)
        self.component_manager = ComponentManager(self)
        
        logger.info("Manager classes initialized: PhysicsManager, SystemManager, StateManager, ComponentManager")

    def update_params(self, params: Dict[str, Any]):
        """
        Update simulation parameters and component parameters.
        This method now updates the integrated systems directly.
        """
        self.params.update(params)
        
        # Update validated Pydantic model if it exists
        if self.validated_params:
            try:
                updated_data = self.validated_params.model_dump()
                updated_data.update(params)
                self.validated_params = SimulationParams(**updated_data)
            except Exception as e:
                logger.warning(f"Failed to re-validate parameters after update: {e}")

        # Re-initialize integrated systems with new parameters
        if hasattr(self, 'integrated_drivetrain') and self.integrated_drivetrain:
            drivetrain_config = getattr(self.integrated_drivetrain, 'config', {})
            if not isinstance(drivetrain_config, dict):
                drivetrain_config = {}
            drivetrain_config.update(params)
            self.integrated_drivetrain = create_standard_kpp_drivetrain(drivetrain_config)

        if hasattr(self, 'integrated_electrical_system') and self.integrated_electrical_system:
            electrical_config = getattr(self.integrated_electrical_system, 'config', {})
            if not isinstance(electrical_config, dict):
                electrical_config = {}
            electrical_config.update(params)
            self.integrated_electrical_system = create_standard_kmp_electrical_system(electrical_config)

        if hasattr(self, 'integrated_control_system') and self.integrated_control_system:
            # Convert config dataclass to dict if needed
            control_config = getattr(self.integrated_control_system, 'config', {})
            if hasattr(control_config, '__dict__'):
                control_config = dict(control_config.__dict__)
            elif not isinstance(control_config, dict):
                control_config = {}
            control_config.update(params)
            self.integrated_control_system = create_standard_kpp_control_system(control_config)

        if hasattr(self, 'enhanced_loss_model') and self.enhanced_loss_model:
            loss_model_config = getattr(self.enhanced_loss_model, 'config', {})
            if not isinstance(loss_model_config, dict):
                loss_model_config = {}
            loss_model_config.update(params)
            self.integrated_loss_model = create_standard_kpp_enhanced_loss_model(loss_model_config)

        # Update existing floaters
        for floater in self.floaters:
            floater.volume = self.params.get("floater_volume", floater.volume)
            floater.mass = self.params.get("floater_mass_empty", floater.mass)
            floater.area = self.params.get("floater_area", floater.area)
            floater.drag_coefficient = self.params.get("drag_coefficient", floater.drag_coefficient)
            floater.air_fill_time = self.params.get("air_fill_time", floater.air_fill_time)

        logger.info("Simulation parameters updated for all integrated systems.")

    def trigger_pulse(self):
        """
        Trigger air injection pulse on the next available floater via the pneumatic system.
        """
        for floater in self.floaters:
            if not floater.is_filled and floater.fill_progress == 0.0:
                if self.pneumatics.trigger_injection(floater):
                    self.pulse_count += 1
                    logger.info(
                        f"Pulse triggered on a floater. Total pulses: {self.pulse_count}"
                    )
                    return True
        logger.info("No available floater or insufficient pressure for pulse trigger.")
        return False

    def run(self):
        self.running = True
        logger.info("Simulation loop started.")
        # Force an initial pulse at t=0 to kick off the system
        if self.time == 0.0:
            logger.info("Forcing initial pulse at t=0.0")
            self.trigger_pulse()
        while self.running:
            logger.debug(f"Step start: t={self.time:.2f}")
            for i, floater in enumerate(self.floaters):
                logger.debug(
                    f"Floater {i}: theta={getattr(floater, 'theta', 0.0):.2f}, filled={getattr(floater, 'is_filled', False)}, pos={floater.get_cartesian_position() if hasattr(floater, 'get_cartesian_position') else 'N/A'}"
                )
            logger.debug(
                f"Drivetrain: omega_chain={getattr(self.drivetrain, 'omega_chain', 0.0):.2f}, omega_flywheel={getattr(self.drivetrain, 'omega_flywheel', 0.0):.2f}, clutch_engaged={getattr(self.drivetrain, 'clutch_engaged', False)}"
            )
            logger.debug(
                f"Generator: target_omega={getattr(self.generator, 'target_omega', 0.0):.2f}, target_power={getattr(self.generator, 'target_power', 0.0):.2f}"
            )
            self.step(self.dt)
            time.sleep(self.dt)
        logger.info("Simulation loop stopped.")

    def stop(self):
        self.running = False
        logger.info("Simulation stopped.")

    def set_chain_geometry(self, major_axis=5.0, minor_axis=10.0):
        """
        Set the geometry of the elliptical/circular chain and initialize floater theta values.
        """
        self.chain_major_axis = major_axis
        self.chain_minor_axis = minor_axis
        self.chain_radius = (major_axis + minor_axis) / 2  # Approximate mean radius
        n = len(self.floaters)
        for i, floater in enumerate(self.floaters):
            floater.set_chain_params(major_axis, minor_axis, self.chain_radius)
            floater.set_theta(2 * math.pi * i / n)

    def step(self, dt: float) -> Union[Dict[str, Any], SimulationState]:
        """
        Perform a single simulation step using the modular manager architecture.

        Args:
            dt: Time step in seconds (must be positive)

        Returns:
            SimulationState: Complete simulation state after the step
            (or Dict for backward compatibility)
        """
        if dt <= 0:
            raise ValueError("Time step dt must be positive.")

        # 1. Component updates and pulse triggers
        self.component_manager.update_components(dt)
        
        # 2. Physics calculations (floater forces, enhanced H1/H2/H3 physics, chain dynamics)
        physics_results = self.physics_manager.calculate_all_physics(dt)
        
        # 3. System updates (drivetrain, electrical, control, grid services)
        system_results = self.system_manager.update_systems(dt, physics_results)
        
        # 4. State management (logging, data collection, energy tracking)
        state_data = self.state_manager.collect_and_log_state(
            dt, physics_results, system_results
        )
        
        # 5. Update simulation time
        self.time += dt
        
        return state_data

    def log_state(
        self,
        power_output,
        torque,
        base_buoy_force=None,
        pulse_force=None,
        total_vertical_force=None,
        tau_net=None,
        tau_to_generator=None,
        clutch_c=None,
        clutch_state=None,
        drag_loss=None,
        dissolution_loss=None,
        venting_loss=None,
        net_energy=None,
        control_output=None,
        electrical_output=None,
        pneumatic_executed=False,
        enhanced_state=None,
    ):
        """
        Collect and log the current state of the simulation, including all advanced integrated systems.
        """
        print(
            f"LOG_STATE: t={self.time:.2f}, power={power_output:.2f}, torque={torque:.2f}, base_buoy_force={base_buoy_force}, pulse_force={pulse_force}, clutch_c={clutch_c}, clutch_state={clutch_state}, drag_loss={drag_loss}, dissolution_loss={dissolution_loss}, venting_loss={venting_loss}, net_energy={net_energy}"
        )

        # Get advanced drivetrain state (primary source)
        try:
            integrated_drivetrain_state = (
                self.integrated_drivetrain.get_comprehensive_state()
            )
        except AttributeError:
            # Fallback to basic system outputs if comprehensive state not available
            try:
                integrated_drivetrain_state = (
                    self.integrated_drivetrain._calculate_system_outputs()
                )
            except AttributeError:
                # Final fallback to empty state
                integrated_drivetrain_state = {}

        # Get legacy drivetrain state for compatibility
        legacy_drivetrain_state = (
            self.drivetrain.get_state()
        )  # Use integrated state when available, extract key values for compatibility
        if integrated_drivetrain_state and isinstance(
            integrated_drivetrain_state, dict
        ):
            # Safely extract nested values with proper type checking
            def safe_get_nested(data, *keys, default=0.0):
                """Safely get nested dictionary values"""
                current = data
                for key in keys:
                    if isinstance(current, dict) and key in current:
                        current = current[key]
                    else:
                        return default
                return current if current is not None else default

            drivetrain_state = {
                "omega_flywheel_rpm": integrated_drivetrain_state.get(
                    "flywheel_speed_rpm",
                    safe_get_nested(
                        integrated_drivetrain_state, "flywheel", "speed_rpm"
                    ),
                ),
                "omega_chain_rpm": integrated_drivetrain_state.get(
                    "chain_speed_rpm",
                    safe_get_nested(
                        integrated_drivetrain_state, "sprocket", "top", "speed_rpm"
                    ),
                ),
                "clutch_engaged": integrated_drivetrain_state.get(
                    "clutch_engaged",
                    safe_get_nested(
                        integrated_drivetrain_state,
                        "clutch",
                        "is_engaged",
                        default=False,
                    ),
                ),
                "flywheel_speed_rpm": integrated_drivetrain_state.get(
                    "flywheel_speed_rpm", 0.0
                ),
                "gearbox_output_torque": integrated_drivetrain_state.get(
                    "gearbox_output_torque", 0.0
                ),
                "system_efficiency": integrated_drivetrain_state.get(
                    "system_efficiency",
                    safe_get_nested(
                        integrated_drivetrain_state, "system", "efficiency"
                    ),
                ),
            }
        else:
            # Use legacy state as fallback
            drivetrain_state = legacy_drivetrain_state.copy()
            drivetrain_state.update(
                {
                    "flywheel_speed_rpm": legacy_drivetrain_state.get(
                        "omega_flywheel_rpm", 0.0
                    ),
                    "gearbox_output_torque": 0.0,
                    "system_efficiency": 0.0,
                }
            )

        # Compute overall mechanical efficiency (output electrical power / mechanical input power)
        omega_fly_rpm = drivetrain_state.get("flywheel_speed_rpm", 0.0)
        omega_fly = omega_fly_rpm * (2 * math.pi / 60)
        if torque and omega_fly:
            overall_eff = power_output / (torque * omega_fly)
        else:
            overall_eff = 0.0
        # Compute average floater velocity
        if self.floaters:
            avg_velocity = sum(abs(f.velocity) for f in self.floaters) / len(
                self.floaters
            )
        else:
            avg_velocity = 0.0
        state = {
            "time": self.time,
            "power": power_output,
            "torque": torque,
            "base_buoy_force": base_buoy_force,
            "pulse_force": pulse_force,
            "total_vertical_force": total_vertical_force,
            "tau_net": tau_net,
            "tau_to_generator": tau_to_generator,
            "clutch_c": clutch_c,
            "clutch_state": clutch_state,
            "total_energy": self.total_energy,
            "pulse_count": self.pulse_count,
            "flywheel_speed_rpm": drivetrain_state["omega_flywheel_rpm"],
            "chain_speed_rpm": drivetrain_state["omega_chain_rpm"],
            "clutch_engaged": drivetrain_state["clutch_engaged"],
            "tank_pressure": self.pneumatics.tank_pressure,
            "overall_efficiency": overall_eff,
            "avg_floater_velocity": avg_velocity,
            "floaters": [f.to_dict() for f in self.floaters],
        }

        # Include energy loss and net energy data
        state["drag_loss"] = drag_loss
        state["dissolution_loss"] = dissolution_loss
        state["venting_loss"] = venting_loss
        state["net_energy"] = net_energy  # Include enhanced loss model data (Phase 5)
        if enhanced_state is not None:
            state["enhanced_losses"] = {
                "total_system_losses": enhanced_state.system_losses.total_system_losses,
                "system_efficiency": enhanced_state.system_losses.system_efficiency,
                "mechanical_losses": {
                    "bearing_friction": enhanced_state.system_losses.mechanical_losses.bearing_friction,
                    "gear_mesh_losses": enhanced_state.system_losses.mechanical_losses.gear_mesh_losses,
                    "seal_friction": enhanced_state.system_losses.mechanical_losses.seal_friction,
                    "windage_losses": enhanced_state.system_losses.mechanical_losses.windage_losses,
                    "clutch_losses": enhanced_state.system_losses.mechanical_losses.clutch_losses,
                    "total_losses": enhanced_state.system_losses.mechanical_losses.total_losses,
                },
                "electrical_losses": enhanced_state.system_losses.electrical_losses,
                "thermal_losses": enhanced_state.system_losses.thermal_losses,
            }
            state["thermal_state"] = enhanced_state.performance_metrics
            state["component_temperatures"] = {
                name: thermal_state.temperature
                for name, thermal_state in enhanced_state.thermal_states.items()
            }

        # Include control system data
        if control_output:
            state["control_mode"] = control_output.get("control_mode", "normal")
            state["timing_commands"] = control_output.get("timing_commands", {})
            state["load_commands"] = control_output.get("load_commands", {})
            state["grid_commands"] = control_output.get("grid_commands", {})
            state["fault_status"] = control_output.get("fault_status", {})
            state["control_performance"] = control_output.get("performance_metrics", {})
            state["pneumatic_control_executed"] = pneumatic_executed

        # Include electrical system data
        if electrical_output:
            state["electrical_load_torque"] = electrical_output.get(
                "load_torque_command", 0.0
            )
            state["grid_power_output"] = electrical_output.get("grid_power_output", 0.0)
            state["electrical_efficiency"] = electrical_output.get(
                "system_efficiency", 0.0
            )
            state["electrical_synchronized"] = electrical_output.get(
                "synchronized", False
            )
            state["electrical_load_factor"] = electrical_output.get("load_factor", 0.0)
            state["grid_voltage"] = electrical_output.get("grid_voltage", 480.0)
            state["grid_frequency"] = electrical_output.get("grid_frequency", 60.0)
        # Include grid services data (Phase 7)
        if hasattr(self, "_last_grid_services_response"):
            state["grid_services"] = {
                "total_power_command_mw": self._last_grid_services_response.get(
                    "total_power_command_mw", 0.0
                ),
                "active_services": self._last_grid_services_response.get(
                    "active_services", []
                ),
                "service_count": self._last_grid_services_response.get(
                    "service_count", 0
                ),
                "coordination_status": self._last_grid_services_response.get(
                    "status", "No services active"
                ),
                "frequency_services": {},
                "grid_conditions": getattr(self, "_last_grid_conditions", {}),
            }

            # Include detailed grid services performance metrics
            grid_services_metrics = (
                self.grid_services_coordinator.get_performance_metrics()
            )
            state["grid_services_performance"] = grid_services_metrics
        else:
            # Grid services not yet active
            state["grid_services"] = {
                "total_power_command_mw": 0.0,
                "active_services": [],
                "service_count": 0,
                "coordination_status": "Grid services not initialized",
                "frequency_services": {},
                "grid_conditions": {},
            }

        # Include pneumatic performance analysis data (Phase 7)
        if hasattr(self, "pneumatic_performance_analyzer"):
            pneumatic_summary = (
                self.pneumatic_performance_analyzer.get_performance_summary()
            )
            if pneumatic_summary:
                state["pneumatic_performance"] = {
                    "average_efficiency": pneumatic_summary.get(
                        "average_efficiency", 0.0
                    ),
                    "peak_efficiency": pneumatic_summary.get("peak_efficiency", 0.0),
                    "capacity_factor": pneumatic_summary.get("capacity_factor", 0.0),
                    "thermal_efficiency": pneumatic_summary.get(
                        "thermal_efficiency", 1.0
                    ),
                    "power_factor": pneumatic_summary.get("power_factor", 0.0),
                    "availability": pneumatic_summary.get("availability", 0.0),
                }

                # Add optimization recommendations if any exist
                recommendations = (
                    self.pneumatic_performance_analyzer.generate_optimization_recommendations()
                )
                if recommendations:
                    state["pneumatic_optimization"] = {
                        "recommendation_count": len(recommendations),
                        "latest_recommendations": [
                            {
                                "target": rec.target.value,
                                "expected_improvement": rec.expected_improvement,
                                "confidence": rec.confidence,
                                "description": rec.description,
                            }
                            for rec in recommendations[:3]  # Top 3 recommendations
                        ],
                    }
            else:
                state["pneumatic_performance"] = {
                    "average_efficiency": 0.0,
                    "peak_efficiency": 0.0,
                    "capacity_factor": 0.0,
                    "thermal_efficiency": 1.0,
                    "power_factor": 0.0,
                    "availability": 0.0,
                }

        # Include pneumatic energy analysis data
        if hasattr(self, "pneumatic_energy_analyzer"):
            energy_summary = self.pneumatic_energy_analyzer.get_energy_summary()
            if energy_summary:
                state["pneumatic_energy"] = {
                    "total_input_energy": energy_summary.get("total_input_energy", 0.0),
                    "total_output_energy": energy_summary.get(
                        "total_output_energy", 0.0
                    ),
                    "overall_efficiency": energy_summary.get("overall_efficiency", 0.0),
                    "thermal_contribution": energy_summary.get(
                        "thermal_contribution", 0.0
                    ),
                }
                # Include energy conservation validation
                conservation = (
                    self.pneumatic_energy_analyzer.validate_energy_conservation()
                )
                state["pneumatic_energy"]["conservation_valid"] = conservation.get(
                    "conservation_valid", True
                )
                state["pneumatic_energy"]["energy_balance_error"] = conservation.get(
                    "conservation_error_percent", 0.0
                )

        self.data_log.append(state)
        self.data_queue.put(state)
        logger.debug(
            f"Step: t={self.time:.2f}, power={power_output:.2f}, torque={torque:.2f}, base_buoy_force={base_buoy_force}, pulse_force={pulse_force}, clutch_c={clutch_c}, clutch_state={clutch_state}"
        )

        return state

    def collect_state(self):
        """
        Return the latest simulation state.
        """
        if not self.data_log:
            return {}
        return self.data_log[-1]

    def start_thread(self):
        if self.thread is None or not self.thread.is_alive():
            self.thread = threading.Thread(target=self.run, daemon=True)
            self.thread.start()
            logger.info("Simulation thread started.")

    def reset(self):
        """
        Resets the entire simulation to its initial state.
        """
        self.time = 0.0
        self.total_energy = 0.0
        self.pulse_count = 0
        self.last_pulse_time = -999
        self.data_log.clear()

        self.drivetrain.reset()
        self.integrated_drivetrain.reset()
        self.integrated_electrical_system.reset()
        self.integrated_control_system.reset()
        self.enhanced_loss_model.reset()
        self.transient_controller.reset()
        self.generator.reset()
        self.pneumatics.reset()
        for i, floater in enumerate(self.floaters):
            floater.reset()
            # Set the first floater unfilled at the bottom to kickstart the cycle
            if i == 0:
                floater.is_filled = False
                floater.fill_progress = 0.0
                floater.set_theta(0.0)
            else:
                floater.is_filled = True
                floater.fill_progress = 1.0
                floater.set_theta(2 * math.pi * i / len(self.floaters))
        # Set chain geometry and trigger a pulse for the first floater
        self.set_chain_geometry()
        # --- Calibrated startup: set floaters for continuous movement ---
        n = len(self.floaters)
        for i, floater in enumerate(self.floaters):
            floater.set_theta(2 * math.pi * i / n)
            x, y = floater.get_cartesian_position()
            if y > 0:
                floater.is_filled = True
                floater.fill_progress = 1.0
                floater.state = "FILLED"
            else:
                floater.is_filled = False
                floater.fill_progress = 0.0
                floater.state = "EMPTY"
        # Ensure one floater at injection is ready to fill (simulate injection point at theta=0)
        self.floaters[0].set_theta(0.0)
        self.floaters[0].is_filled = True
        self.floaters[0].fill_progress = 0.0
        self.floaters[0].state = "FILLING"
        logger.info(
            "Floaters initialized for calibrated startup: ascending side buoyant, descending side drawing, one ready for injection."
        )
        self.pneumatics.trigger_injection(self.floaters[0])
        with self.data_queue.mutex:
            self.data_queue.queue.clear()
        logger.info("Simulation engine has been reset.")

    def initiate_startup(self, reason: str = "Manual startup") -> bool:
        """
        Initiate system startup sequence.

        Args:
            reason: Reason for startup initiation

        Returns:
            bool: True if startup initiated successfully
        """
        return self.transient_controller.initiate_startup(self.time, reason)

    def trigger_emergency_stop(self, reason: str):
        """
        Trigger emergency stop sequence.

        Args:
            reason: Reason for emergency stop

        Returns:
            Emergency stop response dictionary
        """
        return self.transient_controller.trigger_emergency_stop(reason, self.time)

    def get_transient_status(self):
        """Get comprehensive transient event status"""
        return self.transient_controller.get_transient_status()

    def acknowledge_transient_event(self, event_type: str, event_id: str = ""):
        """
        Acknowledge a transient event.

        Args:
            event_type: Type of event to acknowledge
            event_id: Specific event ID (if applicable)

        Returns:
            bool: True if event acknowledged successfully
        """
        event_id_param = event_id if event_id else event_type
        return self.transient_controller.acknowledge_event(event_type, event_id_param)

    # New Physics Module Control Methods

    def set_h1_nanobubbles(
        self, active: bool, bubble_fraction: float = 0.05, drag_reduction: float = 0.1
    ):
        """
        Enable/disable H1 nanobubble effects.

        Args:
            active (bool): Whether to activate H1 nanobubble effects
            bubble_fraction (float): Volume fraction of nanobubbles (0-0.2)
            drag_reduction (float): Drag reduction factor (0-0.5)
        """
        self.fluid_system.set_h1_active(active, bubble_fraction, drag_reduction)
        logger.info(
            f"H1 nanobubbles {'activated' if active else 'deactivated'}: "
            f"bubble_fraction={bubble_fraction:.1%}, drag_reduction={drag_reduction:.1%}"
        )

    def set_h2_thermal(
        self,
        active: bool,
        efficiency: float = 0.8,
        buoyancy_boost: float = 0.05,
        compression_improvement: float = 0.15,
    ):
        """
        Enable/disable H2 isothermal thermal effects.

        Args:
            active (bool): Whether to activate H2 thermal effects
            efficiency (float): H2 process efficiency (0-1)
            buoyancy_boost (float): Buoyancy enhancement factor (0-0.3)
            compression_improvement (float): Compression work reduction (0-0.5)
        """
        self.thermal_model.set_h2_active(
            active, efficiency, buoyancy_boost, compression_improvement
        )
        logger.info(
            f"H2 thermal effects {'activated' if active else 'deactivated'}: "
            f"efficiency={efficiency:.1%}, buoyancy_boost={buoyancy_boost:.1%}, "
            f"compression_improvement={compression_improvement:.1%}"
        )

    def set_water_temperature(self, temperature_celsius: float):
        """
        Set water temperature.

        Args:
            temperature_celsius (float): Water temperature in Celsius
        """
        temperature_kelvin = temperature_celsius + 273.15
        self.fluid_system.set_temperature(temperature_kelvin)
        self.thermal_model.set_water_temperature(temperature_kelvin)
        logger.info(f"Water temperature set to {temperature_celsius:.1f}°C")

    def get_physics_status(self) -> dict:
        """
        Get comprehensive status of all physics modules.

        Returns:
            dict: Physics system status
        """
        return {
            "chain_system": self.chain_system.get_state(),
            "fluid_system": self.fluid_system.get_fluid_properties(),
            "thermal_system": self.thermal_model.get_thermal_properties(),
            "h1_status": {
                "active": self.fluid_system.h1_active,
                "bubble_fraction": self.fluid_system.h1_bubble_fraction,
                "drag_reduction": self.fluid_system.h1_drag_reduction,
                "effective_density": self.fluid_system.state.effective_density,
            },
            "h2_status": {
                "active": self.thermal_model.h2_active,
                "efficiency": self.thermal_model.h2_efficiency,
                "buoyancy_enhancement": self.thermal_model.state.buoyancy_enhancement,
                "compression_work_reduction": self.thermal_model.state.compression_work_reduction,
            },
        }

    def enable_enhanced_physics(self, h1_active: bool = True, h2_active: bool = True):
        """
        Enable both H1 and H2 enhanced physics effects.

        Args:
            h1_active (bool): Enable H1 nanobubble effects
            h2_active (bool): Enable H2 thermal effects
        """
        if h1_active:
            self.set_h1_nanobubbles(True)
        if h2_active:
            self.set_h2_thermal(True)

        logger.info(f"Enhanced physics enabled: H1={h1_active}, H2={h2_active}")

    def disable_enhanced_physics(self):
        """Disable all enhanced physics effects (H1 and H2)."""
        self.set_h1_nanobubbles(False)
        self.set_h2_thermal(False)
        logger.info("All enhanced physics effects disabled")

    def get_enhanced_performance_metrics(self) -> dict:
        """
        Calculate performance metrics with enhanced physics effects.

        Returns:
            dict: Enhanced performance metrics
        """
        if not self.data_log:
            return {}

        latest_state = self.data_log[-1]

        # Calculate enhancement factors
        base_buoy = latest_state.get("base_buoy_force", 0.0)
        enhanced_buoy = latest_state.get("enhanced_buoy_force", base_buoy)
        thermal_buoy = latest_state.get("thermal_enhanced_force", enhanced_buoy)

        h1_enhancement = (
            (enhanced_buoy - base_buoy) / max(base_buoy, 1.0) if base_buoy > 0 else 0.0
        )
        h2_enhancement = (
            (thermal_buoy - enhanced_buoy) / max(enhanced_buoy, 1.0)
            if enhanced_buoy > 0
            else 0.0
        )
        total_enhancement = (
            (thermal_buoy - base_buoy) / max(base_buoy, 1.0) if base_buoy > 0 else 0.0
        )

        return {
            "h1_buoyancy_enhancement": h1_enhancement,
            "h2_thermal_enhancement": h2_enhancement,
            "total_physics_enhancement": total_enhancement,
            "base_buoyant_force": base_buoy,
            "h1_enhanced_force": enhanced_buoy,
            "h2_thermal_force": thermal_buoy,
            "fluid_properties": self.fluid_system.get_fluid_properties(),
            "thermal_properties": self.thermal_model.get_thermal_properties(),
        }

    def get_output_data(self) -> Dict[str, Any]:
        """
        Get comprehensive simulation output data for SSE streaming.
        Uses the new schema-driven data where available.

        Returns:
            dict: Complete simulation state data structure (legacy format for SSE compatibility)
        """
        try:
            # Try to get schema-based state first
            if hasattr(self, 'state_manager') and self.state_manager:
                latest_state = self.state_manager.get_latest_state()
                if latest_state:
                    # Convert SimulationState to dict for SSE compatibility
                    return self._convert_simulation_state_to_dict(latest_state)
            
            # Fallback to legacy data gathering
            return self._get_legacy_output_data()

        except Exception as e:
            logger.error(f"Error generating output data: {e}")
            return {"error": str(e)}

    def get_simulation_state(self) -> Optional[SimulationState]:
        """
        Get the current simulation state as a validated Pydantic model.
        
        Returns:
            SimulationState: Current simulation state or None if not available
        """
        if hasattr(self, 'state_manager') and self.state_manager:
            return self.state_manager.get_latest_state()
        return None

    def _convert_simulation_state_to_dict(self, state: SimulationState) -> Dict[str, Any]:
        """
        Convert SimulationState schema to legacy dict format for SSE compatibility.
        
        Args:
            state: SimulationState schema object
            
        Returns:
            dict: Legacy format dict
        """
        try:
            # Convert the schema to dict while maintaining SSE compatibility
            state_dict = state.model_dump()
            
            # Restructure for legacy SSE format
            return {
                "timestamp": time.time(),
                "time": state_dict["time"],
                "torque": state_dict["physics"]["net_force"] * getattr(self, "chain_radius", 1.0),  # Convert force to torque
                "power": state_dict["systems"]["electrical"]["power_output"],
                "efficiency": state_dict["performance"]["overall_efficiency"],
                "torque_components": {
                    "buoyant": state_dict["physics"]["base_buoy_force"] * getattr(self, "chain_radius", 1.0),
                    "drag": state_dict["physics"]["drag_force"] * getattr(self, "chain_radius", 1.0),
                    "generator": state_dict["systems"]["electrical"]["load_torque"],
                },
                "floaters": state_dict["physics"]["floater_data"],
                "system_state": {
                    "h1_active": getattr(self, "h1_nanobubbles_active", False),
                    "h2_active": getattr(self, "h2_thermal_active", False),
                    "h3_active": getattr(self, "h3_pulse_active", False),
                    "enhanced_physics_enabled": getattr(self, "enhanced_physics_enabled", False),
                },
                "eff_drivetrain": state_dict["systems"]["drivetrain"]["system_efficiency"],
                "eff_pneumatic": getattr(self, "eff_pneumatic", 0.75),
                "physics_status": {
                    "h1_nanobubbles": state_dict["physics"]["enhanced_physics"]["h1_nanobubbles"],
                    "h2_thermal": state_dict["physics"]["enhanced_physics"]["h2_thermal"],
                    "h3_pulse": state_dict["physics"]["enhanced_physics"]["h3_pulse"],
                },
                "enhanced_forces": {
                    "h1_nanobubble_force": state_dict["physics"]["enhanced_buoy_force"] - state_dict["physics"]["base_buoy_force"],
                    "h2_thermal_force": state_dict["physics"]["thermal_enhanced_force"] - state_dict["physics"]["enhanced_buoy_force"],
                    "h3_pulse_force": state_dict["physics"]["pulse_force"],
                },
                "parameters": {
                    "nanobubble_frac": getattr(self, "nanobubble_frac", 0.0),
                    "thermal_coeff": getattr(self, "thermal_coeff", 0.0),
                    "pulse_enabled": getattr(self, "pulse_enabled", False),
                },
            }
        except Exception as e:
            logger.warning(f"Failed to convert SimulationState to dict: {e}, using legacy format")
            return self._get_legacy_output_data()

    def _get_legacy_output_data(self) -> Dict[str, Any]:
        """
        Legacy output data gathering for backward compatibility.
        
        Returns:
            dict: Legacy format simulation data
        """
        # Get basic simulation state
        current_time = getattr(self, "time", 0.0)
        total_torque = getattr(self, "torque_total", 0.0)
        power_output = getattr(self, "power_output", 0.0)
        efficiency = getattr(self, "efficiency", 0.0)

        # Get floater data
        floaters_data = []
        if hasattr(self, "floaters"):
            for i, floater in enumerate(self.floaters):
                floaters_data.append(
                    {
                        "id": i,
                        "buoyancy": floater.compute_buoyant_force(),
                        "drag": abs(floater.compute_drag_force()),
                        "net_force": floater.force,
                        "pulse_force": floater.compute_pulse_jet_force(),
                        "position": getattr(floater, "position", 0.0),
                        "velocity": getattr(floater, "velocity", 0.0),
                        "state": getattr(floater, "state", "unknown"),
                    }
                )

        # Compile output data
        return {
            "timestamp": time.time(),
            "time": current_time,
            "torque": total_torque,
            "power": power_output,
            "efficiency": efficiency,
            "torque_components": {
                "buoyant": getattr(self, "torque_buoyant", 0.0),
                "drag": getattr(self, "torque_drag", 0.0),
                "generator": getattr(self, "torque_generator", 0.0),
            },
            "floaters": floaters_data,
            "system_state": {
                "h1_active": getattr(self, "h1_nanobubbles_active", False),
                "h2_active": getattr(self, "h2_thermal_active", False),
                "h3_active": getattr(self, "h3_pulse_active", False),
                "enhanced_physics_enabled": getattr(
                    self, "enhanced_physics_enabled", False
                ),
            },
            "eff_drivetrain": getattr(self, "eff_drivetrain", 0.85),
            "eff_pneumatic": getattr(self, "eff_pneumatic", 0.75),
            "physics_status": {
                "h1_nanobubbles": (
                    self.nanobubble_physics.get_status()
                    if hasattr(self, "nanobubble_physics")
                    else {}
                ),
                "h2_thermal": (
                    self.thermal_physics.get_status()
                    if hasattr(self, "thermal_physics")
                    else {}
                ),
                "h3_pulse": (
                    self.pulse_controller.get_status()
                    if hasattr(self, "pulse_controller")
                    else {}
                ),
            },
            "enhanced_forces": {
                "h1_nanobubble_force": getattr(self, "h1_nanobubble_force", 0.0),
                "h2_thermal_force": getattr(self, "h2_thermal_force", 0.0),
                "h3_pulse_force": getattr(self, "h3_pulse_force", 0.0),
            },
            "parameters": {
                "nanobubble_frac": getattr(self, "nanobubble_frac", 0.0),
                "thermal_coeff": getattr(self, "thermal_coeff", 0.0),
                "pulse_enabled": getattr(self, "pulse_enabled", False),
            },
        }
