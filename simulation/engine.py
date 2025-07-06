# SimulationEngine: orchestrates all simulation modules
# Coordinates state updates, manages simulation loop, and handles cross-module interactions
"""
Simulation engine class.
Coordinates all simulation components and manages the simulation loop.
"""

import logging
import math
import threading
import time
from typing import Any, Dict, List, Optional, Union
from queue import Queue

from config import ConfigManager, FloaterConfig
from config.config import RHO_WATER, G  # Add physics constants
from config.parameter_schema import get_default_parameters, validate_kpp_system_parameters

# Import new physics modules
from simulation.components.chain import Chain
from simulation.components.control import Control
from simulation.components.environment import Environment
from simulation.components.floater import Floater, FloaterConfig
from simulation.components.fluid import Fluid
from simulation.components.integrated_drivetrain import create_standard_kpp_drivetrain
from simulation.components.integrated_electrical_system import (
    create_standard_kmp_electrical_system,
)
from simulation.components.pneumatics import PneumaticSystem
from simulation.components.thermal import ThermalModel
from simulation.grid_services.grid_services_coordinator import GridConditions, create_standard_grid_services_coordinator

# Import new config system with backward compatibility
try:
    from config import ConfigManager, FloaterConfig

    NEW_CONFIG_AVAILABLE = True
except ImportError:
    NEW_CONFIG_AVAILABLE = False

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)


class SimulationEngine:
    """
    Main simulation engine for the KPP system.
    Orchestrates all components and manages simulation state and loop.
    """

    def __init__(
        self, 
        data_queue: Optional[Queue] = None, 
        params: Optional[Dict[str, Any]] = None, 
        config_manager: Optional[ConfigManager] = None, 
        use_new_config: bool = False, 
        *args, 
        **kwargs
    ):
        """
        Initialize the SimulationEngine.
        Args:
            data_queue: Optional queue for data exchange
            params: Legacy parameter dictionary
            config_manager: Optional ConfigManager instance for new config system
            use_new_config: Whether to use the new config system (default False)
            *args, **kwargs: Additional arguments
        """
        self.data_queue = data_queue
        self.params = params or {}
        self.config_manager = config_manager
        self.use_new_config = use_new_config
        self.running = False
        self.time = 0.0
        self.dt = self._get_time_step()
        self.last_pulse_time = -999  # Allow immediate first pulse

        # Initialize event queue for logging
        self.log_event_queue = []
        self.max_log_queue_size = 1000  # Prevent memory leaks
        
        # Initialize other attributes
        self.chain_tension = 0.0
        self._last_grid_services_response = None
        self._last_grid_conditions = None
        
        # Initialize components (these will be set up later)
        self.floaters: List[Floater] = []
        self.integrated_drivetrain: Optional[Any] = None  # IntegratedDrivetrain
        self.integrated_electrical_system: Optional[Any] = None  # IntegratedElectricalSystem
        self.integrated_control_system: Optional[Control] = None
        self.grid_services_coordinator: Optional[Any] = None  # GridServicesCoordinator
        self.pneumatics: Optional[PneumaticSystem] = None
        self.fluid_system: Optional[Fluid] = None
        self.thermal_model: Optional[ThermalModel] = None
        self.chain_system: Optional[Chain] = None
        self.pneumatic_performance_analyzer: Optional[Any] = None
        
        # Initialize configs with defaults
        self.floater_config: Optional[FloaterConfig] = None
        self.electrical_config: Optional[Any] = None  # ElectricalConfig
        self.drivetrain_config: Optional[Any] = None  # DrivetrainConfig
        self.control_config: Optional[Any] = None  # ControlConfig
        self.simulation_config: Optional[Any] = None  # SimulationConfig

        if self.use_new_config:
            logger.info("Using new configuration system")
            # Use new config system
            self._init_with_new_config(params)
        else:
            logger.info("Using legacy parameter system")
            # Use legacy parameter system
            self._init_with_legacy_params(params)

    def _init_with_new_config(self, params):
        """Initialize engine using new config system"""
        if self.config_manager is None:
            # Create default config manager if none provided
            self.config_manager = ConfigManager()

        # Get configurations from config manager with fallbacks
        self.floater_config = self.config_manager.get_config("floater")
        if self.floater_config is None:
            logger.warning("Floater config not found, creating default")
            from config.components.floater_config import FloaterConfig
            self.floater_config = FloaterConfig()

        self.electrical_config = self.config_manager.get_config("electrical")
        if self.electrical_config is None:
            logger.warning("Electrical config not found, creating default")
            from config.components.electrical_config import ElectricalConfig
            self.electrical_config = ElectricalConfig()

        self.drivetrain_config = self.config_manager.get_config("integrated_drivetrain")
        if self.drivetrain_config is None:
            logger.warning("IntegratedDrivetrain config not found, creating default")
            from config.components.drivetrain_config import DrivetrainConfig
            self.drivetrain_config = DrivetrainConfig()

        self.control_config = self.config_manager.get_config("control")
        if self.control_config is None:
            logger.warning("Control config not found, creating default")
            from config.components.control_config import ControlConfig
            self.control_config = ControlConfig()

        self.simulation_config = self.config_manager.get_config("simulation")
        if self.simulation_config is None:
            logger.warning("Simulation config not found, creating default")
            from config.components.simulation_config import SimulationConfig
            self.simulation_config = SimulationConfig()

        # Initialize components with new configs
        self._init_components_with_new_config()

        # Store legacy params for backward compatibility
        self.params = params or {}

    def _init_with_legacy_params(self, params):
        """Initialize engine using legacy parameter system"""
        # Validate and scale parameters for full KPP system
        validation_result = validate_kpp_system_parameters(params)
        if not validation_result["valid"]:
            logger.error(f"Parameter validation failed: {validation_result['errors']}")
            raise ValueError(f"Invalid parameters: {validation_result['errors']}")

        if validation_result["warnings"]:
            for warning in validation_result["warnings"]:
                logger.warning(warning)

        # Use validated parameters
        self.params = validation_result["validated_params"]
        self.floater_distribution = validation_result["floater_distribution"]

        logger.info(
            f"KPP System initialized with {self.floater_distribution['total_floaters']} floaters: "
            f"{self.floater_distribution['ascending_floaters']} ascending, "
            f"{self.floater_distribution['descending_floaters']} descending, "
            f"{self.floater_distribution['transition_floaters']} in transition"
        )

        # Initialize components with legacy params
        self._init_components_with_legacy_params()

    def _get_time_step(self):
        """Get time step from appropriate config source"""
        if self.use_new_config:
            # Get from simulation config or use default
            if hasattr(self, "simulation_config") and self.simulation_config:
                return getattr(self.simulation_config, "time_step", 0.1)
            else:
                return 0.1
        else:
            return self.params.get("time_step", 0.1)

    def update_params(self, params):
        """
        Update simulation parameters and component parameters.
        Supports both legacy and new config systems.
        """
        if self.use_new_config:
            # Update new config system
            self._update_new_config(params)
        else:
            # Update legacy parameter system
            self._update_legacy_params(params)

    def _update_new_config(self, params):
        """Update new config system with parameter changes"""
        # Update config manager if provided
        if self.config_manager:
            # Handle nested parameter updates
            for key, value in params.items():
                if "." in key:
                    # Nested parameter (e.g., 'floater.volume')
                    section, param = key.split(".", 1)
                    config = self.config_manager.get_config(section)
                    if config and hasattr(config, param):
                        setattr(config, param, value)
                else:
                    # Direct parameter update
                    self.config_manager.update_config(key, **value)

        # Update component configurations
        if "floater" in params:
            self._update_floater_config(params["floater"])
        if "electrical" in params:
            self._update_electrical_config(params["electrical"])
        if "integrated_drivetrain" in params:
            self._update_drivetrain_config(params["integrated_drivetrain"])
        if "control" in params:
            self._update_control_config(params["control"])

    def _update_legacy_params(self, params):
        """Update legacy parameter system"""
        self.params.update(params)

        # Update existing floaters instead of recreating them
        for floater in self.floaters:
            # Update floater configuration with new parameters
            floater.config.volume = self.params.get("floater_volume", floater.config.volume)
            floater.config.mass = self.params.get("floater_mass_empty", floater.config.mass)
            floater.config.area = self.params.get("floater_area", floater.config.area)
            floater.config.drag_coefficient = self.params.get("floater_Cd", floater.config.drag_coefficient)
            floater.config.air_fill_time = self.params.get("air_fill_time", floater.config.air_fill_time)

        logger.info("Legacy simulation parameters updated.")

    def _update_floater_config(self, floater_params):
        """Update floater configuration"""
        if hasattr(self, "floater_config"):
            for key, value in floater_params.items():
                if hasattr(self.floater_config, key):
                    setattr(self.floater_config, key, value)

            # Update existing floaters
            for floater in self.floaters:
                for key, value in floater_params.items():
                    if hasattr(floater.config, key):
                        setattr(floater.config, key, value)

    def _update_electrical_config(self, electrical_params):
        """Update electrical configuration"""
        if hasattr(self, "electrical_config"):
            for key, value in electrical_params.items():
                if hasattr(self.electrical_config, key):
                    setattr(self.electrical_config, key, value)

    def _update_drivetrain_config(self, drivetrain_params):
        """Update integrated_drivetrain configuration"""
        if hasattr(self, "drivetrain_config"):
            for key, value in drivetrain_params.items():
                if hasattr(self.drivetrain_config, key):
                    setattr(self.drivetrain_config, key, value)

    def _update_control_config(self, control_params):
        """Update control configuration"""
        if hasattr(self, "control_config"):
            for key, value in control_params.items():
                if hasattr(self.control_config, key):
                    setattr(self.control_config, key, value)

    def trigger_pulse(self):
        """
        Trigger air injection pulse on the next available floater via the pneumatic system.
        """
        if not self.pneumatics:
            logger.warning("Pneumatics system not initialized")
            return False
            
        for floater in self.floaters:
            if not floater.is_filled and floater.fill_progress == 0.0:
                if self.pneumatics.trigger_injection(floater):
                    self.pulse_count += 1
                    logger.info(f"Pulse triggered on a floater. Total pulses: {self.pulse_count}")
                    return True
        logger.info("No available floater or insufficient pressure for pulse trigger.")
        return False

    def run(self):
        self.running = True
        logger.info("Simulation loop started.")
        if self.time == 0.0:
            logger.info("Forcing initial pulse at t=0.0")
            self.trigger_pulse()
        while self.running:
            logger.debug(f"Step start: t={self.time:.2f}")
            for i, floater in enumerate(self.floaters):
                logger.debug(
                    f"Floater {i}: theta={getattr(floater, 'theta', 0.0):.2f}, filled={getattr(floater, 'is_filled', False)}, pos={floater.get_cartesian_position() if hasattr(floater, 'get_cartesian_position') else 'N/A'}"
                )
            # Always set chain_speed at the start of step
            if self.integrated_drivetrain:
                try:
                    drivetrain_state = self.integrated_drivetrain.get_comprehensive_state()
                    chain_speed = drivetrain_state.get("sprocket", {}).get("top", {}).get("chain_speed", 2.0)
                except Exception as e:
                    logger.warning(f"Failed to get integrated_drivetrain state: {e}")
                    chain_speed = 2.0
            else:
                chain_speed = 2.0

            # Get electrical system state from integrated electrical system
            if self.integrated_electrical_system:
                try:
                    electrical_state = self.integrated_electrical_system.get_comprehensive_state()
                    logger.debug(
                        f"Electrical: power_output={electrical_state.get('electrical_power_output', 0)/1000:.2f}kW, load_factor={electrical_state.get('load_factor', 0):.3f}"
                    )
                except Exception as e:
                    logger.warning(f"Failed to get electrical state: {e}")
            else:
                logger.warning("Electrical system not initialized")
                
            state = self.step(self.dt)
            # Update latest_state atomically
            with self.latest_state_lock:
                self.latest_state = state
            # Log after step to confirm loop is running
            logger.info(f"Simulation loop running: t={self.time:.2f}")
            # Log queue size
            if self.data_queue:
                logger.info(f"Data queue size: {self.data_queue.qsize()}")
            else:
                logger.info("Data queue not initialized")
            time.sleep(self.dt)
        logger.info("Simulation loop stopped.")

    def stop(self):
        self.running = False
        logger.info("Simulation stopped.")

    def set_chain_geometry(self, major_axis=5.0, minor_axis=10.0):
        """
        Set the geometry of the elliptical/circular chain and initialize floaters' theta.
        """
        self.chain_major_axis = major_axis
        self.chain_minor_axis = minor_axis
        self.chain_radius = (major_axis + minor_axis) / 2  # Approximate mean radius
        n = len(self.floaters)
        for i, floater in enumerate(self.floaters):
            floater.set_chain_params(major_axis, minor_axis, self.chain_radius)
            floater.set_theta(2 * math.pi * i / n)

    def step(self, dt: float) -> Dict[str, Any]:
        """
        Execute one simulation step with comprehensive error handling.

        Args:
            dt: Time step in seconds (must be > 0)

        Returns:
            Dict containing simulation state and status

        Raises:
            ValueError: Invalid time step
            SimulationError: Physics calculation failure
            MemoryError: State logging failure
        """
        # Input validation
        if dt <= 0:
            raise ValueError(f"Invalid time step: {dt}. Must be > 0.")

        step_start = time.time()
        logger.debug(f"[PERF] Simulation step started at {step_start:.3f}")

        try:
            # Step 1: Validate system state
            self._validate_system_state()

            # Step 2: Execute physics calculations
            physics_result = self._execute_physics_step(dt)

            # Step 3: Update electrical system
            electrical_result = self._update_electrical_system(physics_result)

            # Step 4: Log state (with size limits)
            state_data = self._log_state_safely(physics_result, electrical_result)

            step_duration = time.time() - step_start
            logger.debug(f"[PERF] Step completed: dt={dt:.3f}s, duration={step_duration:.3f}s")

            return {
                "status": "success",
                "data": state_data,
                "timestamp": time.time(),
                "_performance": {"step_duration": step_duration, "timestamp": time.time()},
            }

        except Exception as e:
            logger.error(f"Simulation step failed: {e}")
            self._handle_step_failure(e)
            return {
                "status": "error",
                "error": str(e),
                "timestamp": time.time(),
                "_performance": {"step_duration": 0.0, "timestamp": time.time()},
            }

    def _validate_system_state(self) -> None:
        """Validate system state before simulation step."""
        if not hasattr(self, "floaters") or not self.floaters:
            raise RuntimeError("No floaters initialized")

        if not hasattr(self, "integrated_drivetrain"):
            raise RuntimeError("IntegratedDrivetrain not initialized")

        if not hasattr(self, "integrated_electrical_system"):
            raise RuntimeError("Electrical system not initialized")

    def _execute_physics_step(self, dt: float) -> Dict[str, Any]:
        """Execute physics calculations for one simulation step."""
        # 1. Check for pulse trigger
        if self.time - self.last_pulse_time >= self.params.get("pulse_interval", 2.0):
            if self.trigger_pulse():
                self.last_pulse_time = self.time

        # Always set chain_speed at the start of step
        chain_speed = 2.0  # Default chain speed
        if self.integrated_drivetrain:
            try:
                drivetrain_state = self.integrated_drivetrain.get_comprehensive_state()
                chain_speed = drivetrain_state.get("sprocket", {}).get("top", {}).get("chain_speed", 2.0)
            except Exception as e:
                logger.warning(f"Failed to get integrated_drivetrain state: {e}")

        # 2. Update component states
        if self.pneumatics:
            self.pneumatics.update(dt)

        # 2a. Update thermal and fluid system states
        if self.fluid_system:
            self.fluid_system.update_state()
        if self.thermal_model:
            self.thermal_model.update_state()

        # Log thermal and fluid system status for monitoring (event-driven)
        if self.time % 1.0 < dt:  # Log every second
            if self.fluid_system and self.thermal_model:
                self._queue_log_event('thermal_fluid_status', {
                    'h1_active': getattr(self.fluid_system, 'h1_active', False),
                    'effective_density': getattr(self.fluid_system.state, 'effective_density', 1000.0),
                    'h2_active': getattr(self.thermal_model, 'h2_active', False),
                    'buoyancy_enhancement': getattr(self.thermal_model.state, 'buoyancy_enhancement', 1.0)
                })

        # 2a. Update pneumatic system performance tracking
        if (hasattr(self, "pneumatic_coordinator") and hasattr(self, "pneumatic_performance_analyzer") 
            and self.pneumatic_performance_analyzer):
            # Get pneumatic system data for performance tracking
            pneumatic_power = (
                getattr(self.pneumatics, "compressor_power", 4200.0)
                if getattr(self.pneumatics, "compressor_running", False)
                else 0.0
            )

            # Calculate mechanical power contribution from pneumatic system
            # This is the power added to the system by buoyancy from air injection
            total_pneumatic_force = sum(
                f.compute_buoyant_force() - f.volume * RHO_WATER * G
                for f in self.floaters
                if getattr(f, "is_filled", False)
            )

            # Calculate mechanical power from pneumatic forces
            mechanical_power_from_pneumatics = total_pneumatic_force * chain_speed

            # Record performance snapshot if compressor is active
            if pneumatic_power > 0:
                avg_depth = sum(f.position for f in self.floaters) / len(self.floaters) if self.floaters else 10.0

                self.pneumatic_performance_analyzer.record_performance_snapshot(
                    electrical_power=pneumatic_power,
                    mechanical_power=max(0, mechanical_power_from_pneumatics),
                    thermal_power=pneumatic_power * 0.05,  # Assume 5% thermal boost
                    compression_efficiency=0.85,  # Standard efficiency
                    expansion_efficiency=0.90,  # Standard efficiency
                    depth=avg_depth,
                )

        # 2b. First calculate forces using new physics modules to get total force for chain system
        total_vertical_force = 0.0
        base_buoy_force = 0.0
        pulse_force = 0.0
        thermal_enhanced_force = 0.0

        for i, floater in enumerate(self.floaters):
            x, y = floater.get_cartesian_position()

            # Calculate enhanced physics forces using new modules
            # Base buoyant force
            base_buoyancy = floater.compute_buoyant_force()

            # Thermal enhancement using Thermal model (H2 isothermal expansion)
            ascent_height = max(0, y)  # Height above bottom
            thermal_buoyancy = base_buoyancy  # Default to base if thermal model not available
            if self.thermal_model:
                thermal_buoyancy = self.thermal_model.calculate_thermal_buoyancy_enhancement(base_buoyancy, ascent_height)

            # Enhanced drag calculation using Fluid system
            drag_force = 0.0  # Default drag force
            if self.fluid_system:
                drag_force = self.fluid_system.calculate_drag_force(chain_speed, floater.config.area)

            # Apply drag force direction based on motion
            if y > 0:  # Ascending side
                drag_force = -drag_force  # Opposes upward motion
            else:  # Descending side
                drag_force = drag_force  # Opposes downward motion

            # Calculate net vertical force for this floater
            gravity = 9.81  # Default gravity
            if self.fluid_system:
                gravity = getattr(self.fluid_system, 'gravity', 9.81)
            
            floater_weight = floater.config.mass * gravity
            if getattr(floater, "is_filled", False):
                # Air-filled floater: buoyancy up, weight down, drag opposing motion
                net_force = thermal_buoyancy - floater_weight + drag_force
            else:
                # Water-filled floater: weight + water weight down, drag opposing motion
                effective_density = 1000.0  # Default water density
                if self.fluid_system and hasattr(self.fluid_system.state, 'effective_density'):
                    effective_density = self.fluid_system.state.effective_density
                
                water_weight = floater.config.volume * effective_density * gravity
                net_force = -(floater_weight + water_weight) + drag_force

            # Add pulse jet force if applicable
            jet_force = floater.compute_pulse_jet_force()
            net_force += jet_force

            # Sum up forces
            # DIRECTION FIX: Ensure proper chain tension direction
            # Positive forces should create positive chain tension (pulling up)
            total_vertical_force += abs(net_force)
            base_buoy_force += base_buoyancy
            thermal_enhanced_force += thermal_buoyancy

            if abs(jet_force) > 1e-3:
                pulse_force += jet_force

            # Queue enhanced physics per-floater logging (event-driven)
            self._queue_log_event('floater_physics', {
                'floater_id': i,
                'x': x,
                'y': y,
                'base_buoy': base_buoyancy,
                'thermal_buoy': thermal_buoyancy,
                'drag': drag_force,
                'net_force': net_force,
                'is_filled': getattr(floater, 'is_filled', False)
            })

        # Update chain kinematics using the Chain system with calculated force
        # DIRECTION FIX: Use absolute force and ensure positive tension direction
        effective_force = abs(total_vertical_force) if total_vertical_force != 0 else 0
        if self.chain_system:
            self.chain_system.advance(dt, effective_force)

        # Update floater positions based on chain motion
        chain_angular_velocity = 0.0  # Default angular velocity
        if self.chain_system:
            chain_angular_velocity = self.chain_system.get_angular_speed()
            
        for i, floater in enumerate(self.floaters):
            prev_theta = getattr(floater, "theta", 0.0)
            # Use chain motion to advance floater position
            new_theta = prev_theta + chain_angular_velocity * dt
            floater.set_theta(new_theta)

            # Detect top sprocket crossing (180° pivot)
            if prev_theta % (2 * math.pi) < math.pi and new_theta % (2 * math.pi) >= math.pi:
                floater.pivot()

            # Detect bottom sprocket crossing (360° pivot + water drainage)
            if prev_theta < 2 * math.pi and new_theta >= 2 * math.pi:
                floater.pivot()
                floater.drain_water()
                floater.is_filled = False
                floater.fill_progress = 0.0
                # Trigger air injection after drainage
                if self.pneumatics:
                    self.pneumatics.trigger_injection(floater)
            floater.update(dt)

        # After kinematics update, track energy losses
        drag_loss_sum = sum(f.drag_loss for f in self.floaters)
        venting_loss_sum = sum(f.venting_loss for f in self.floaters)

        # Get chain tension from chain system
        self.chain_tension = 0.0  # Default chain tension
        if self.chain_system:
            self.chain_tension = self.chain_system.get_tension()

        # 4. Get drivetrain output torque and speed from integrated drivetrain
        # The integrated drivetrain handles the full conversion from chain tension to mechanical output
        drivetrain_output = {}
        if self.integrated_drivetrain:
            try:
                drivetrain_output = self.integrated_drivetrain.update(self.chain_tension, 0.0, dt)
            except Exception as e:
                logger.warning(f"IntegratedDrivetrain update failed: {e}")

        # Extract mechanical values for electrical system
        output_torque = drivetrain_output.get("gearbox_output_torque", 0.0)
        output_speed_rpm = drivetrain_output.get("flywheel_speed_rpm", 0.0)
        output_speed_rad_s = output_speed_rpm * (2 * math.pi / 60)  # Convert to rad/s

        # 5. Build system state for control system
        system_state = {
            "time": self.time,
            "chain_tension": self.chain_tension,
            "mechanical_torque": output_torque,
            "mechanical_speed_rpm": output_speed_rpm,
            "mechanical_speed_rad_s": output_speed_rad_s,
            "total_vertical_force": total_vertical_force,
            "base_buoy_force": base_buoy_force,
            "pulse_force": pulse_force,
            "floater_states": [f.to_dict() for f in self.floaters],
            "pneumatics": {
                "tank_pressure": getattr(self.pneumatics, "tank_pressure", 0.0) if self.pneumatics else 0.0,
                "compressor_running": getattr(self.pneumatics, "compressor_running", False) if self.pneumatics else False,
            },
            "energy_losses": {"drag_loss": drag_loss_sum, "venting_loss": venting_loss_sum},
            # New physics system data
            "chain_system": self.chain_system.get_state() if self.chain_system else {},
            "fluid_system": self.fluid_system.get_fluid_properties() if self.fluid_system else {},
            "thermal_system": self.thermal_model.get_thermal_properties() if self.thermal_model else {},
        }

        # 6. Update integrated control system with current state
        control_output = {}
        if self.integrated_control_system:
            try:
                control_output = self.integrated_control_system.update(dt)
            except Exception as e:
                logger.warning(f"Control system update failed: {e}")

        # Apply control system commands
        if self.integrated_control_system:
            self.integrated_control_system.update(dt)

        # Apply electrical system commands
        electrical_commands = {
            "target_load_factor": 0.8,  # Default 80% load factor
            "power_setpoint": self.params.get("target_power", 530000.0),
        }

        # 8. Update integrated electrical system with mechanical input and control commands
        electrical_output = {}
        if self.integrated_electrical_system:
            try:
                electrical_output = self.integrated_electrical_system.update(
                    output_torque, output_speed_rad_s, dt, electrical_commands
                )
            except Exception as e:
                logger.warning(f"Electrical system update failed: {e}")

        # 9. Update grid services coordinator (Phase 7)
        grid_services_response = {}
        if self.grid_services_coordinator:
            try:
                grid_conditions = GridConditions(
                    frequency=electrical_output.get("grid_frequency", 60.0),
                    voltage=electrical_output.get("grid_voltage", 480.0),
                    active_power=electrical_output.get("grid_power_output", 0.0) / 1000000.0,  # Convert to MW
                    reactive_power=0.0,  # Default reactive power
                    timestamp=time.time(),
                )

                # Update grid services with current conditions
                rated_power_mw = self.params.get("target_power", 530000.0) / 1000000.0  # Convert to MW
                grid_services_response = self.grid_services_coordinator.update(grid_conditions, dt, rated_power_mw)
                self._last_grid_services_response = grid_services_response
                self._last_grid_conditions = grid_conditions
            except Exception as e:
                logger.warning(f"Grid services update failed: {e}")

        # 10. Update time
        self.time += dt

        return {
            "system_state": system_state,
            "control_output": control_output,
            "electrical_output": electrical_output,
            "grid_services_response": grid_services_response,
            "physics_data": {
                "total_vertical_force": total_vertical_force,
                "base_buoy_force": base_buoy_force,
                "pulse_force": pulse_force,
                "thermal_enhanced_force": thermal_enhanced_force,
                "chain_tension": self.chain_tension,
                "drag_loss": drag_loss_sum,
                "venting_loss": venting_loss_sum,
            },
        }

    def _update_electrical_system(self, physics_result: Dict[str, Any]) -> Dict[str, Any]:
        """Update electrical system with physics results."""
        try:
            electrical_output = physics_result.get("electrical_output", {})
            return electrical_output
        except Exception as e:
            logger.error(f"Electrical system update failed: {e}")
            return {"error": str(e)}

    def _log_state_safely(self, physics_result: Dict[str, Any], electrical_result: Dict[str, Any]) -> Dict[str, Any]:
        """Log state with memory management and error handling."""
        try:
            # Extract key data for logging
            system_state = physics_result.get("system_state", {})
            electrical_output = electrical_result

            # Get power and torque values
            power_output = electrical_output.get("grid_power_output", 0.0)
            torque = system_state.get("mechanical_torque", 0.0)

            # Log state using existing method
            state_data = self.log_state(
                power_output=power_output,
                torque=torque,
                base_buoy_force=physics_result.get("physics_data", {}).get("base_buoy_force"),
                pulse_force=physics_result.get("physics_data", {}).get("pulse_force"),
                total_vertical_force=physics_result.get("physics_data", {}).get("total_vertical_force"),
                drag_loss=physics_result.get("physics_data", {}).get("drag_loss"),
                venting_loss=physics_result.get("physics_data", {}).get("venting_loss"),
                control_output=physics_result.get("control_output"),
                electrical_output=electrical_output,
            )

            return state_data

        except Exception as e:
            logger.error(f"State logging failed: {e}")
            return {"error": f"State logging failed: {str(e)}", "timestamp": time.time()}

    def _handle_step_failure(self, error: Exception) -> None:
        """Handle simulation step failures."""
        logger.error(f"Simulation step failed: {error}")

        # Log error details
        logger.error(f"Error type: {type(error).__name__}")
        logger.error(f"Error message: {str(error)}")

        # Update system status
        if hasattr(self, "latest_state"):
            with self.latest_state_lock:
                self.latest_state["status"] = "error"
                self.latest_state["error"] = str(error)
                self.latest_state["timestamp"] = time.time()

    def log_state(self, **kwargs) -> Dict[str, Any]:
        """Log simulation state with enhanced error handling."""
        try:
            # Validate required parameters
            if not hasattr(self, 'time'):
                logger.error("Engine time not available")
                return {"error": "Engine time not available", "timestamp": time.time()}

            # Get integrated_drivetrain state safely
            drivetrain_state = {}
            try:
                if hasattr(self, 'integrated_drivetrain') and self.integrated_drivetrain:
                    drivetrain_state = self.integrated_drivetrain.get_comprehensive_state()
                else:
                    logger.warning("IntegratedDrivetrain not available, using defaults")
                    drivetrain_state = {
                        "flywheel_speed_rpm": 0.0,
                        "chain_speed_rpm": 0.0,
                        "clutch_engaged": False
                    }
            except Exception as e:
                logger.warning(f"Failed to get integrated_drivetrain state: {e}")
                drivetrain_state = {
                    "flywheel_speed_rpm": 0.0,
                    "chain_speed_rpm": 0.0,
                    "clutch_engaged": False
                }

            # Get electrical output safely
            electrical_output = kwargs.get('electrical_output', {})
            
            # Calculate power and torque safely
            power_output = kwargs.get('power_output', 0.0)
            torque = kwargs.get('torque', 0.0)

            # Calculate efficiency safely
            omega_fly = drivetrain_state.get("flywheel_speed_rpm", 0.0) * 2 * math.pi / 60
            if torque * omega_fly > 0:
                overall_eff = power_output / (torque * omega_fly)
            else:
                overall_eff = 0.0

            # Get energy losses safely
            drag_loss = kwargs.get('drag_loss', 0.0)
            venting_loss = kwargs.get('venting_loss', 0.0)

            # Build state dictionary with safe defaults
            state = {
                "time": self.time,
                "power": power_output,
                "total_power": power_output,  # Add total_power for test compatibility
                "torque": torque,
                "overall_efficiency": overall_eff,
                "efficiency": overall_eff,  # Add efficiency for test compatibility
                "pulse_count": getattr(self, 'pulse_count', 0),
                "flywheel_speed_rpm": drivetrain_state.get("flywheel_speed_rpm", 0.0),
                "chain_speed_rpm": drivetrain_state.get("chain_speed_rpm", 0.0),
                "clutch_engaged": drivetrain_state.get("clutch_engaged", False),
                "tank_pressure": getattr(self.pneumatics, "tank_pressure", 0.0) if hasattr(self, 'pneumatics') and self.pneumatics else 0.0,
                "grid_power_output": electrical_output.get("grid_power_output", 0.0) if electrical_output else 0.0,
                "electrical_efficiency": electrical_output.get("system_efficiency", 0.0) if electrical_output else 0.0,
                "operating_time": self.time,  # Add operating_time for test compatibility
                "status": "running" if getattr(self, "running", False) else "stopped",
                "floaters": [f.to_dict() for f in self.floaters] if hasattr(self, 'floaters') and self.floaters else [],
            }

            # Include energy loss and net energy data
            state["drag_loss"] = drag_loss
            state["venting_loss"] = venting_loss

            # Include control system data safely
            control_output = kwargs.get('control_output', {})
            if control_output:
                state["control_mode"] = control_output.get("control_mode", "normal")
                state["timing_commands"] = control_output.get("timing_commands", {})
                state["load_commands"] = control_output.get("load_commands", {})
                state["grid_commands"] = control_output.get("grid_commands", {})
                state["fault_status"] = control_output.get("fault_status", {})
                state["control_performance"] = control_output.get("performance_metrics", {})

            # Include electrical system data safely
            if electrical_output:
                state["electrical_load_torque"] = electrical_output.get("load_torque_command", 0.0)
                state["grid_power_output"] = electrical_output.get("grid_power_output", 0.0)
                state["electrical_efficiency"] = electrical_output.get("system_efficiency", 0.0)
                state["electrical_synchronized"] = electrical_output.get("synchronized", False)
                state["electrical_load_factor"] = electrical_output.get("load_factor", 0.0)
                state["grid_voltage"] = electrical_output.get("grid_voltage", 480.0)
                state["grid_frequency"] = electrical_output.get("grid_frequency", 60.0)

            # Include grid services data safely (Phase 7)
            if hasattr(self, "_last_grid_services_response") and self._last_grid_services_response:
                state["grid_services"] = {
                    "total_power_command_mw": self._last_grid_services_response.get("total_power_command_mw", 0.0),
                    "active_services": self._last_grid_services_response.get("active_services", []),
                    "service_count": self._last_grid_services_response.get("service_count", 0),
                    "coordination_status": self._last_grid_services_response.get("status", "No services active"),
                    "frequency_services": {},
                    "grid_conditions": getattr(self, "_last_grid_conditions", {}),
                }

                # Include detailed grid services performance metrics safely
                if hasattr(self, 'grid_services_coordinator') and self.grid_services_coordinator:
                    try:
                        grid_services_metrics = self.grid_services_coordinator.get_performance_metrics()
                        state["grid_services_performance"] = grid_services_metrics
                    except Exception as e:
                        logger.warning(f"Failed to get grid services metrics: {e}")
                        state["grid_services_performance"] = {}
            else:
                # Grid services not yet active
                state["grid_services"] = {
                    "total_power_command_mw": 0.0,
                    "active_services": [],
                    "service_count": 0,
                    "coordination_status": "No services active",
                    "frequency_services": {},
                    "grid_conditions": {},
                }

            # Log state to data queue if available
            if hasattr(self, 'data_queue') and self.data_queue:
                try:
                    self.data_queue.put(state)
                except Exception as e:
                    logger.warning(f"Failed to queue state data: {e}")

            return state

        except Exception as e:
            logger.error(f"State logging failed: {e}")
            return {
                "error": f"State logging failed: {str(e)}", 
                "timestamp": time.time(),
                "time": getattr(self, 'time', 0.0),
                "status": "error"
            }

    def collect_state(self):
        """
        Return the latest simulation state.
        """
        if not self.data_log:
            return {}
        return self.data_log[-1]

    def start(self):
        """
        Start the simulation loop. Sets running=True and starts the thread if needed.
        """
        self.running = True
        if not hasattr(self, "thread") or self.thread is None or not self.thread.is_alive():
            self.thread = threading.Thread(target=self.run, daemon=True)
            self.thread.start()
            logger.info("Simulation thread started (from start method).")
        else:
            logger.info("Simulation thread already running; set running=True.")

    def reset(self):
        """
        Resets the entire simulation to its initial state.
        """
        self.time = 0.0
        self.total_energy = 0.0
        self.pulse_count = 0
        self.last_pulse_time = -999
        self.data_log.clear()

        # Legacy drivetrain not used in current implementation
        if self.integrated_drivetrain:
            self.integrated_drivetrain.reset()
        if self.integrated_electrical_system:
            self.integrated_electrical_system.reset()

        # Re-engage electrical load after reset with higher target
        if self.integrated_electrical_system is not None:
            self.integrated_electrical_system.set_target_load_factor(0.9)
            self.integrated_electrical_system.enable_load_management(True)
        logger.info("Electrical load re-engaged after reset: 80% target load factor")

        if self.integrated_control_system:
            self.integrated_control_system.reset()
        if self.pneumatics:
            self.pneumatics.reset()
        # Set chain geometry first
        self.set_chain_geometry()

        # Initialize floaters properly for immediate power generation
        n = len(self.floaters)
        for i, floater in enumerate(self.floaters):
            floater.reset()
            # Set position around the chain
            theta = 2 * math.pi * i / n
            floater.set_theta(theta)
            x, y = floater.get_cartesian_position()

            # Ascending side (y > 0): air-filled for buoyancy
            if y > 0:
                floater.is_filled = True
                floater.fill_progress = 1.0
                floater.state = "FILLED"
                logger.debug(f"Floater {i}: ascending at theta={theta:.2f}, y={y:.2f}, air-filled")
            # Descending side (y <= 0): water-filled for weight
            else:
                floater.is_filled = False
                floater.fill_progress = 0.0
                floater.state = "EMPTY"
                logger.debug(f"Floater {i}: descending at theta={theta:.2f}, y={y:.2f}, water-filled")

        # Trigger initial air injection to get the system started
        bottom_floaters = [f for f in self.floaters if f.get_cartesian_position()[1] <= 1.0]
        if bottom_floaters and self.pneumatics:
            start_floater = bottom_floaters[0]
            if not start_floater.is_filled:
                self.pneumatics.trigger_injection(start_floater)
                logger.info(f"Initial air injection triggered for bottom floater")

        logger.info(
            f"Simulation reset: {n} floaters initialized with {sum(1 for f in self.floaters if f.is_filled)} ascending (air-filled) and {sum(1 for f in self.floaters if not f.is_filled)} descending (water-filled)"
        )

        # Clear data queue if it exists
        if self.data_queue is not None:
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
        logger.info(f"System startup initiated: {reason}")
        return True

    def trigger_emergency_stop(self, reason: str):
        """
        Trigger emergency stop sequence for realistic KPP operation.

        Args:
            reason: Reason for emergency stop

        Returns:
            Emergency stop response dictionary
        """
        logger.critical(f"EMERGENCY STOP TRIGGERED: {reason}")

        # Stop all simulation activity
        self.running = False

        # Emergency shutdown sequence
        emergency_response = {
            "status": "emergency_stop_triggered",
            "reason": reason,
            "timestamp": time.time(),
            "actions_taken": [],
        }

        try:
            # Stop electrical system
            if self.integrated_electrical_system is not None:
                self.integrated_electrical_system.reset()
                emergency_response["actions_taken"].append("electrical_system_shutdown")

            # Stop pneumatic systems
            if self.pneumatics is not None:
                self.pneumatics.reset()
                emergency_response["actions_taken"].append("pneumatic_system_vented")

            # Stop integrated_drivetrain
            if self.integrated_drivetrain is not None:
                self.integrated_drivetrain.reset()
                emergency_response["actions_taken"].append("drivetrain_stopped")

            # Reset all floaters to safe state
            if hasattr(self, "floaters"):
                for floater in self.floaters:
                    floater.emergency_vent()
                emergency_response["actions_taken"].append("floaters_vented")

            # Log emergency event
            emergency_response["actions_taken"].append("emergency_logged")

        except Exception as e:
            logger.error(f"Error during emergency stop: {e}")
            emergency_response["error"] = str(e)

        return emergency_response

    def get_transient_status(self):
        """Get comprehensive transient event status"""
        return {"status": "normal", "active_events": []}

    def acknowledge_transient_event(self, event_type: str, event_id: str = ""):
        """
        Acknowledge a transient event.

        Args:
            event_type: Type of event to acknowledge
            event_id: Specific event ID (if applicable)

        Returns:
            bool: True if event acknowledged successfully
        """
        logger.info(f"Transient event acknowledged: {event_type} {event_id}")
        return True

    # New Physics Module Control Methods

    def set_h1_nanobubbles(self, active: bool, bubble_fraction: float = 0.05, drag_reduction: float = 0.1):
        """
        Enable/disable H1 nanobubble effects.

        Args:
            active (bool): Whether to activate H1 nanobubble effects
            bubble_fraction (float): Volume fraction of nanobubbles (0-0.2)
            drag_reduction (float): Drag reduction factor (0-0.5)
        """
        if self.fluid_system:
            self.fluid_system.set_h1_active(active, bubble_fraction, drag_reduction)
            logger.info(
                f"H1 nanobubbles {'activated' if active else 'deactivated'}: "
                f"bubble_fraction={bubble_fraction:.1%}, drag_reduction={drag_reduction:.1%}"
            )
        else:
            logger.warning("Fluid system not initialized")

    def set_h2_thermal(
        self, active: bool, efficiency: float = 0.8, buoyancy_boost: float = 0.05, compression_improvement: float = 0.15
    ):
        """
        Enable/disable H2 isothermal thermal effects.

        Args:
            active (bool): Whether to activate H2 thermal effects
            efficiency (float): H2 process efficiency (0-1)
            buoyancy_boost (float): Buoyancy enhancement factor (0-0.3)
            compression_improvement (float): Compression work reduction (0-0.5)
        """
        if self.thermal_model:
            self.thermal_model.set_h2_active(active, efficiency, buoyancy_boost, compression_improvement)
            logger.info(
                f"H2 thermal effects {'activated' if active else 'deactivated'}: "
                f"efficiency={efficiency:.1%}, buoyancy_boost={buoyancy_boost:.1%}, "
                f"compression_improvement={compression_improvement:.1%}"
            )
        else:
            logger.warning("Thermal model not initialized")

    def set_water_temperature(self, temperature_celsius: float):
        """
        Set water temperature.

        Args:
            temperature_celsius (float): Water temperature in Celsius
        """
        temperature_kelvin = temperature_celsius + 273.15
        if self.fluid_system is not None:
            self.fluid_system.set_temperature(temperature_kelvin)
        if self.thermal_model is not None:
            self.thermal_model.set_water_temperature(temperature_kelvin)
        logger.info(f"Water temperature set to {temperature_celsius:.1f}°C")

    def get_physics_status(self) -> dict:
        """
        Get comprehensive status of all physics modules.

        Returns:
            dict: Physics system status
        """
        return {
            "chain_system": self.chain_system.get_state() if self.chain_system is not None else {},
            "fluid_system": self.fluid_system.get_fluid_properties() if self.fluid_system is not None else {},
            "thermal_system": self.thermal_model.get_thermal_properties() if self.thermal_model is not None else {},
            "h1_status": {
                "active": self.fluid_system.h1_active if self.fluid_system is not None else False,
                "bubble_fraction": self.fluid_system.h1_bubble_fraction if self.fluid_system is not None else 0.0,
                "drag_reduction": self.fluid_system.h1_drag_reduction if self.fluid_system is not None else 0.0,
                "effective_density": self.fluid_system.state.effective_density if self.fluid_system is not None else 1000.0,
            },
            "h2_status": {
                "active": self.thermal_model.h2_active if self.thermal_model is not None else False,
                "efficiency": self.thermal_model.h2_efficiency if self.thermal_model is not None else 0.0,
                "buoyancy_enhancement": self.thermal_model.state.buoyancy_enhancement if self.thermal_model is not None else 0.0,
                "compression_work_reduction": self.thermal_model.state.compression_work_reduction if self.thermal_model is not None else 0.0,
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
        thermal_buoy = latest_state.get("thermal_enhanced_force", base_buoy)

        h1_enhancement = (thermal_buoy - base_buoy) / max(base_buoy, 1.0) if base_buoy > 0 else 0.0
        total_enhancement = (thermal_buoy - base_buoy) / max(base_buoy, 1.0) if base_buoy > 0 else 0.0

        return {
            "h1_buoyancy_enhancement": h1_enhancement,
            "total_physics_enhancement": total_enhancement,
            "base_buoyant_force": base_buoy,
            "h1_enhanced_force": thermal_buoy,
            "fluid_properties": self.fluid_system.get_fluid_properties(),
            "thermal_properties": self.thermal_model.get_thermal_properties(),
        }

    def get_latest_state(self):
        with self.latest_state_lock:
            return dict(self.latest_state) if self.latest_state else {}

    def get_parameters(self):
        """
        Return all current simulation parameters as a dict.
        Supports both legacy and new config systems.
        """
        if self.use_new_config:
            return self._get_new_config_parameters()
        else:
            return self._get_legacy_parameters()

    def _get_new_config_parameters(self):
        """Get parameters from new config system"""
        params = {}

        # Get parameters from config manager
        if self.config_manager:
            params.update(self.config_manager.get_all_parameters())

        # Add component-specific parameters
        if self.floater_config is not None:
            params["floater"] = getattr(self.floater_config, "to_dict", None)()
        if self.electrical_config is not None:
            params["electrical"] = getattr(self.electrical_config, "to_dict", None)()
        if self.drivetrain_config is not None:
            params["integrated_drivetrain"] = getattr(self.drivetrain_config, "to_dict", None)()
        if self.control_config is not None:
            params["control"] = getattr(self.control_config, "to_dict", None)()

        return params

    def _get_legacy_parameters(self):
        """Get parameters from legacy system"""
        params = get_default_parameters()
        params.update(getattr(self, "params", {}))
        return params

    def set_parameters(self, params):
        """
        Set simulation parameters from a dict.
        Supports both legacy and new config systems.
        """
        self.update_params(params)

    def get_summary(self):
        """
        Return a summary of all key metrics and system state for the frontend.
        """
        if hasattr(self, "get_latest_state"):
            state = self.get_latest_state()
        elif hasattr(self, "collect_state"):
            state = self.collect_state()
        else:
            state = {}

        summary = {
            "time": state.get("time", 0),
            "power": state.get("power", 0),
            "total_power": state.get("power", 0),  # Add total_power for test compatibility
            "torque": state.get("torque", 0),
            "overall_efficiency": state.get("overall_efficiency", 0),
            "efficiency": state.get("overall_efficiency", 0),  # Add efficiency for test compatibility
            "pulse_count": state.get("pulse_count", 0),
            "flywheel_speed_rpm": state.get("flywheel_speed_rpm", 0),
            "grid_power_output": state.get("grid_power_output", 0),
            "electrical_efficiency": state.get("electrical_efficiency", 0),
            "operating_time": state.get("time", 0),  # Add operating_time for test compatibility
            "status": "running" if getattr(self, "running", False) else "stopped",
            # Add more fields as needed for your UI
        }
        return summary

    def _init_components_with_new_config(self):
        """Initialize all components using new config system"""
        # Environment
        self.environment = Environment()

        # Pneumatic system - extract actual values from config objects
        target_pressure = getattr(self.floater_config, "air_pressure", 400000.0)
        self.pneumatics = PneumaticSystem(target_pressure=target_pressure)

        # Floater initialization with new config
        self.floaters = []
        num_floaters = getattr(self.control_config, "num_floaters", 8)
        tank_height = getattr(self.floater_config, "tank_height", 25.0)

        for i in range(num_floaters):
            # Calculate initial position and state
            theta = i * (2 * math.pi / num_floaters)

            # Create floater with new config
            floater = Floater(self.floater_config)

            # Set initial position
            chain_radius = getattr(self.drivetrain_config, "sprocket_radius", 1.2)
            chain_radius += tank_height / 2

            y = (tank_height / 2) * (1 + math.sin(theta))
            floater.position = y

            # Set initial chain parameters
            floater.set_chain_params(major_axis=chain_radius * 2, minor_axis=tank_height, chain_radius=chain_radius)
            floater.set_theta(theta)

            self.floaters.append(floater)

        logger.info(f"Initialized {len(self.floaters)} floaters with new config system")

        # Initialize integrated systems with new configs
        if self.drivetrain_config is not None:
            self.integrated_drivetrain = create_standard_kpp_drivetrain(getattr(self.drivetrain_config, "to_dict", None)())
        else:
            self.integrated_drivetrain = create_standard_kpp_drivetrain({})

        if self.electrical_config is not None:
            self.integrated_electrical_system = create_standard_kmp_electrical_system(getattr(self.electrical_config, "to_dict", None)())
        else:
            self.integrated_electrical_system = create_standard_kmp_electrical_system({})

        self.integrated_control_system = Control(
            simulation=self,
            floaters=self.floaters,
            pneumatic=self.pneumatics,
            target_rpm=getattr(self.control_config, "target_rpm", 375.0) if self.control_config is not None else 375.0,
            Kp=getattr(self.control_config, "kp", 1.0) if self.control_config is not None else 1.0,
            Ki=getattr(self.control_config, "ki", 0.0) if self.control_config is not None else 0.0,
            Kd=getattr(self.control_config, "kd", 0.0) if self.control_config is not None else 0.0,
        )

        # Initialize other components (using defaults for now)

        # Initialize physics modules
        self.fluid_system = Fluid()
        self.thermal_model = ThermalModel()
        self.chain_system = Chain()

        # Initialize grid services coordinator
        self.grid_services_coordinator = create_standard_grid_services_coordinator()

        # Initialize data structures
        self.data_log = []
        self.latest_state = {}
        self.latest_state_lock = threading.Lock()
        self.pulse_count = 0

    def _init_components_with_legacy_params(self):
        """Initialize all components using legacy parameter system"""
        # Environment with scaled parameters
        self.environment = Environment()

        # Pneumatic system with basic configuration
        self.pneumatics = PneumaticSystem(target_pressure=self.params.get("target_pressure", 400000.0))

        # Floater initialization with proper distribution
        self.floaters = []
        num_floaters = self.floater_distribution["total_floaters"]
        tank_height = self.params.get("tank_height", 25.0)

        for i in range(num_floaters):
            # Calculate initial position and state based on distribution
            theta = i * self.floater_distribution["angular_spacing"]

            # Determine if floater is initially ascending (air-filled) or descending (water-filled)

            # Position floater along the chain path (elliptical approximation)
            chain_radius = self.params.get("sprocket_radius", 1.2) + (tank_height / 2)

            y = (tank_height / 2) * (1 + math.sin(theta))  # 0 to tank_height

            # Create configuration for the new modular Floater
            config = FloaterConfig(
                volume=self.params.get("floater_volume", 0.4),
                mass=self.params.get("floater_mass_empty", 16.0),
                area=self.params.get("floater_area", 0.1),
                drag_coefficient=self.params.get("floater_Cd", 0.6),
                air_fill_time=self.params.get("air_fill_time", 0.5),
                air_pressure=self.params.get("air_pressure", 350000),
                air_flow_rate=self.params.get("air_flow_rate", 1.2),
                jet_efficiency=self.params.get("jet_efficiency", 0.85),
                tank_height=tank_height,
            )

            floater = Floater(config)

            # Set initial position
            floater.position = y

            # Set initial chain parameters
            floater.set_chain_params(major_axis=chain_radius * 2, minor_axis=tank_height, chain_radius=chain_radius)
            floater.set_theta(theta)

            self.floaters.append(floater)

        logger.info(f"Initialized {len(self.floaters)} floaters with proper distribution in {tank_height}m tank")

        # Initialize the new integrated drivetrain system
        drivetrain_config = {
            "sprocket_radius": self.params.get("sprocket_radius", 1.0),
            "sprocket_teeth": self.params.get("sprocket_teeth", 20),
            "clutch_engagement_threshold": self.params.get("clutch_engagement_threshold", 0.1),
            "flywheel_moment_of_inertia": self.params.get("flywheel_inertia", 50.0),
            "flywheel_target_speed": self.params.get("flywheel_target_speed", 375.0),
            "pulse_coast_pulse_duration": self.params.get("pulse_duration", 2.0),
            "pulse_coast_coast_duration": self.params.get("coast_duration", 1.0),
        }
        self.integrated_drivetrain = create_standard_kpp_drivetrain(drivetrain_config)

        # Initialize the integrated electrical system (Phase 3)
        electrical_config = {
            "rated_power": self.params.get("target_power", 530000.0),
            "load_management": self.params.get("electrical_load_management", True),
            "target_load_factor": self.params.get("electrical_load_factor", 0.8),
            "generator": {
                "rated_power": self.params.get("target_power", 530000.0),
                "rated_speed": self.params.get("target_rpm", 375.0),
                "efficiency_at_rated": self.params.get("generator_efficiency", 0.94),
            },
            "power_electronics": {
                "rectifier_efficiency": self.params.get("pe_rectifier_efficiency", 0.97),
                "inverter_efficiency": self.params.get("pe_inverter_efficiency", 0.96),
                "transformer_efficiency": self.params.get("pe_transformer_efficiency", 0.985),
            },
        }
        self.integrated_electrical_system = create_standard_kmp_electrical_system(electrical_config)

        # CRITICAL FIX: Set initial electrical load engagement
        self.integrated_electrical_system.set_target_load_factor(0.8)  # 80% rated load
        self.integrated_electrical_system.enable_load_management(True)
        logger.info("Electrical system initialized with 80% target load factor and load management enabled")

        # Initialize the integrated control system (Phase 4)
        control_config = {
            "num_floaters": self.params.get("num_floaters", 8),
            "target_power": self.params.get("target_power", 530000.0),
            "prediction_horizon": self.params.get("control_prediction_horizon", 5.0),
            "optimization_window": self.params.get("control_optimization_window", 2.0),
            "power_tolerance": self.params.get("control_power_tolerance", 0.05),
            "max_ramp_rate": self.params.get("control_max_ramp_rate", 50000.0),
            "nominal_voltage": self.params.get("grid_nominal_voltage", 480.0),
            "nominal_frequency": self.params.get("grid_nominal_frequency", 60.0),
            "voltage_regulation_band": self.params.get("grid_voltage_regulation_band", 0.05),
            "frequency_regulation_band": self.params.get("grid_frequency_regulation_band", 0.1),
            "monitoring_interval": self.params.get("control_monitoring_interval", 0.1),
            "auto_recovery_enabled": self.params.get("control_auto_recovery", True),
            "predictive_maintenance_enabled": self.params.get("control_predictive_maintenance", True),
            "emergency_response_enabled": self.params.get("control_emergency_response", True),
            "adaptive_control_enabled": self.params.get("control_adaptive_enabled", True),
        }
        self.integrated_control_system = Control(
            simulation=self,
            floaters=self.floaters,
            pneumatic=self.pneumatics,
            target_rpm=getattr(self.control_config, "target_rpm", None) if hasattr(self.control_config, "target_rpm") else 375.0,
            Kp=getattr(self.control_config, "kp", None) if hasattr(self.control_config, "kp") else 1.0,
            Ki=getattr(self.control_config, "ki", None) if hasattr(self.control_config, "ki") else 0.0,
            Kd=getattr(self.control_config, "kd", None) if hasattr(self.control_config, "kd") else 0.0,
        )

        # Initialize enhanced loss model (Phase 5)

        # Initialize physics modules
        self.fluid_system = Fluid()
        self.thermal_model = ThermalModel()
        self.chain_system = Chain()

        # Initialize grid services coordinator
        self.grid_services_coordinator = create_standard_grid_services_coordinator()

        # Initialize data structures
        self.data_log = []
        self.latest_state = {}
        self.latest_state_lock = threading.Lock()
        self.pulse_count = 0

    def _queue_log_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """Queue a log event for later processing to avoid circular dependencies."""
        if len(self.log_event_queue) >= self.max_log_queue_size:
            # Remove oldest events to prevent memory leaks
            self.log_event_queue.pop(0)
        
        log_event = {
            'type': event_type,
            'data': data,
            'timestamp': time.time(),
            'simulation_time': self.time
        }
        
        self.log_event_queue.append(log_event)
        
        # Process log events periodically to avoid accumulation
        if len(self.log_event_queue) > 100:
            self._process_log_events()

    def _process_log_events(self) -> None:
        """Process queued log events."""
        while self.log_event_queue:
            event = self.log_event_queue.pop(0)
            
            if event['type'] == 'thermal_fluid_status':
                logger.debug(
                    f"Fluid system: H1_active={event['data']['h1_active']}, "
                    f"effective_density={event['data']['effective_density']:.1f} kg/m³"
                )
                logger.debug(
                    f"Thermal system: H2_active={event['data']['h2_active']}, "
                    f"buoyancy_enhancement={event['data']['buoyancy_enhancement']:.1%}"
                )
            elif event['type'] == 'floater_physics':
                data = event['data']
                logger.debug(
                    f"Floater {data['floater_id']}: x={data['x']:.2f}, y={data['y']:.2f}, "
                    f"base_buoy={data['base_buoy']:.1f}, thermal_buoy={data['thermal_buoy']:.1f}, "
                    f"drag={data['drag']:.1f}, net_force={data['net_force']:.1f}, "
                    f"is_filled={data['is_filled']}"
                )
