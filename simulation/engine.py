# SimulationEngine: orchestrates all simulation modules
# Coordinates state updates, manages simulation loop, and handles cross-module interactions
"""
Simulation engine class.
Coordinates all simulation components and manages the simulation loop.
"""

import time
import json
import threading
import logging
import math
from typing import Optional
from simulation.components.floater import Floater
from simulation.components.drivetrain import Drivetrain
from simulation.components.advanced_generator import AdvancedGenerator
from simulation.components.environment import Environment
from simulation.components.pneumatics import PneumaticSystem
from simulation.components.control import Control
from simulation.components.sensors import Sensors
from simulation.components.clutch import OverrunningClutch
from simulation.components.sprocket import Sprocket
from simulation.components.gearbox import create_kpp_gearbox
from simulation.components.integrated_drivetrain import IntegratedDrivetrain, create_standard_kpp_drivetrain
from simulation.components.integrated_electrical_system import IntegratedElectricalSystem, create_standard_kmp_electrical_system
from simulation.control.integrated_control_system import IntegratedControlSystem, create_standard_kpp_control_system
from simulation.physics.integrated_loss_model import IntegratedLossModel, create_standard_kpp_enhanced_loss_model
from simulation.control.transient_event_controller import TransientEventController
from utils.logging_setup import setup_logging
from simulation.grid_services import GridServicesCoordinator, GridConditions, create_standard_grid_services_coordinator
from config.config import G, RHO_WATER  # Add physics constants
# Import new physics modules
from simulation.components.chain import Chain
from simulation.components.fluid import Fluid
from simulation.components.thermal import ThermalModel
# Stage 2: Import H1, H2, H3 enhanced physics modules
from simulation.physics.nanobubble_physics import NanobubblePhysics
from simulation.physics.thermal_physics import ThermalPhysics  
from simulation.physics.pulse_controller import PulseController
# Phase 8: Import new physics engine and event handler
from simulation.physics.physics_engine import PhysicsEngine
from simulation.physics.event_handler import EventHandler
# Stage 4: Import real-time optimization and monitoring
from simulation.optimization.real_time_optimizer import RealTimeOptimizer
from simulation.monitoring.real_time_monitor import RealTimeController

setup_logging()
logger = logging.getLogger(__name__)

class SimulationEngine:
    """
    Main simulation engine for the KPP system.
    Orchestrates all components and manages simulation state and loop.
    """
    def __init__(self, params, data_queue):
        """
        Initialize the simulation engine and all components.

        Args:
            params (dict): Simulation parameters.
            data_queue (queue.Queue): Queue for streaming simulation data.
        """
        self.params = params
        self.data_queue = data_queue
        self.running = False
        self.time = 0.0
        self.dt = params.get('time_step', 0.1)
        self.last_pulse_time = -999 # Allow immediate first pulse        self.environment = Environment()
        self.pneumatics = PneumaticSystem(
            target_pressure=params.get('target_pressure', 5.0)
        )
        
        # Initialize the new integrated drivetrain system
        drivetrain_config = {
            'sprocket_radius': params.get('sprocket_radius', 1.0),
            'sprocket_teeth': params.get('sprocket_teeth', 20),
            'clutch_engagement_threshold': params.get('clutch_engagement_threshold', 0.1),
            'flywheel_moment_of_inertia': params.get('flywheel_inertia', 50.0),
            'flywheel_target_speed': params.get('flywheel_target_speed', 375.0),
            'pulse_coast_pulse_duration': params.get('pulse_duration', 2.0),
            'pulse_coast_coast_duration': params.get('coast_duration', 1.0)        }
        self.integrated_drivetrain = create_standard_kpp_drivetrain(drivetrain_config)
        
        # Initialize the integrated electrical system (Phase 3)
        electrical_config = {
            'rated_power': params.get('target_power', 530000.0),
            'load_management': params.get('electrical_load_management', True),
            'target_load_factor': params.get('electrical_load_factor', 0.8),
            'generator': {
                'rated_power': params.get('target_power', 530000.0),
                'rated_speed': params.get('target_rpm', 375.0),
                'efficiency_at_rated': params.get('generator_efficiency', 0.94)
            },
            'power_electronics': {
                'rectifier_efficiency': params.get('pe_rectifier_efficiency', 0.97),
                'inverter_efficiency': params.get('pe_inverter_efficiency', 0.96),
                'transformer_efficiency': params.get('pe_transformer_efficiency', 0.985)
            }        }
        self.integrated_electrical_system = create_standard_kmp_electrical_system(electrical_config)
        
        # Initialize the integrated control system (Phase 4)
        control_config = {
            'num_floaters': params.get('num_floaters', 8),
            'target_power': params.get('target_power', 530000.0),
            'prediction_horizon': params.get('control_prediction_horizon', 5.0),
            'optimization_window': params.get('control_optimization_window', 2.0),
            'power_tolerance': params.get('control_power_tolerance', 0.05),
            'max_ramp_rate': params.get('control_max_ramp_rate', 50000.0),
            'nominal_voltage': params.get('grid_nominal_voltage', 480.0),
            'nominal_frequency': params.get('grid_nominal_frequency', 60.0),
            'voltage_regulation_band': params.get('grid_voltage_regulation_band', 0.05),
            'frequency_regulation_band': params.get('grid_frequency_regulation_band', 0.1),
            'monitoring_interval': params.get('control_monitoring_interval', 0.1),
            'auto_recovery_enabled': params.get('control_auto_recovery', True),
            'predictive_maintenance_enabled': params.get('control_predictive_maintenance', True),
            'emergency_response_enabled': params.get('control_emergency_response', True),
            'adaptive_control_enabled': params.get('control_adaptive_enabled', True)        }
        self.integrated_control_system = create_standard_kpp_control_system(control_config)
          # Initialize enhanced loss model (Phase 5)
        ambient_temperature = params.get('ambient_temperature', 20.0)
        self.integrated_loss_model = create_standard_kpp_enhanced_loss_model(ambient_temperature)
        # Legacy alias for compatibility
        self.enhanced_loss_model = self.integrated_loss_model
        
        # Initialize transient event controller (Phase 6)
        transient_config = {
            'startup': {
                'target_startup_speed': params.get('startup_target_speed', 100.0),
                'target_operational_speed': params.get('target_rpm', 375.0),
                'acceleration_rate': params.get('startup_acceleration_rate', 10.0),
                'sync_retry_limit': params.get('startup_sync_retries', 3)
            },
            'emergency': {
                'max_flywheel_speed': params.get('emergency_max_flywheel_speed', 450.0),
                'max_tank_pressure': params.get('emergency_max_pressure', 8.0),
                'max_component_temperature': params.get('emergency_max_temperature', 85.0),
                'max_torque': params.get('emergency_max_torque', 3000.0)
            },
            'grid': {
                'frequency_droop': params.get('grid_frequency_droop', 0.05),
                'voltage_droop': params.get('grid_voltage_droop', 0.02),
                'max_frequency_response': params.get('grid_max_freq_response', 0.2),
                'max_reactive_power': params.get('grid_max_reactive_power', 0.3)
            },
            'auto_startup': params.get('auto_startup_enabled', True),
            'auto_recovery': params.get('auto_recovery_enabled', True),
            'grid_support': params.get('grid_support_enabled', True)
        }
        self.transient_controller = TransientEventController(transient_config)
        
        # Keep legacy drivetrain for compatibility during transition
        self.drivetrain = Drivetrain(
            gear_ratio=params.get('gear_ratio', 16.7),
            efficiency=params.get('drivetrain_efficiency', 0.95),
            sprocket_radius=params.get('sprocket_radius', 0.5),
            flywheel_inertia=params.get('flywheel_inertia', 50.0)
        )
        # Replace legacy generator with advanced generator for main simulation loop
        advanced_generator_config = {
            'rated_power': params.get('target_power', 530000.0),
            'rated_speed': params.get('target_rpm', 375.0),  # RPM
            'rated_frequency': params.get('grid_nominal_frequency', 50.0),
            'power_factor': params.get('generator_power_factor', 0.92)
        }
        self.generator = AdvancedGenerator(advanced_generator_config)
        self.floaters = [
            Floater(
                volume=params.get('floater_volume', 0.3),
                mass=params.get('floater_mass_empty', 18.0),
                area=params.get('floater_area', 0.035),
                Cd=params.get('floater_Cd', 0.8),
                air_fill_time=params.get('air_fill_time', 0.5),
                added_mass=params.get('floater_added_mass', 5.0),
                phase_offset=2*math.pi*i/params.get('num_floaters',1)
            )
            for i in range(params.get('num_floaters', 1))
        ]        
        self.control = Control(self)
        self.sensors = Sensors(self)
        self.clutch = OverrunningClutch(
            tau_eng=params.get('clutch_tau_eng', 200),
            slip_time=params.get('clutch_slip_time', 0.2),
            w_min=params.get('clutch_w_min', 5),
            w_max=params.get('clutch_w_max', 40)
        )
        
        # Legacy drivetrain components (kept for compatibility during transition)
        self.top_sprocket = Sprocket(
            radius=params.get('sprocket_radius', 1.0),
            tooth_count=params.get('sprocket_teeth', 20),
            position='top'
        )
        self.bottom_sprocket = Sprocket(
            radius=params.get('sprocket_radius', 1.0),
            tooth_count=params.get('sprocket_teeth', 20),
            position='bottom'
        )
        self.gearbox = create_kpp_gearbox()
          # Chain properties
        self.chain_length = params.get('chain_length', 50.0)  # Total chain length (m)
        self.chain_mass_per_meter = params.get('chain_mass_per_meter', 10.0)  # kg/m
        self.chain_tension = 0.0  # Current chain tension (N)
        
        self.data_log = []
        self.total_energy = 0.0
        self.pulse_count = 0
        self.thread: Optional[threading.Thread] = None
        logger.info("SimulationEngine initialized with integrated drivetrain system.")
        # Initialize default chain geometry for torque calculations
        self.set_chain_geometry()        # Initialize grid services coordinator (Phase 7)
        grid_services_config = {
            'enable_frequency_services': params.get('enable_frequency_services', True),
            'enable_voltage_services': params.get('enable_voltage_services', True),
            'enable_demand_response': params.get('enable_demand_response', True),
            'enable_energy_storage': params.get('enable_energy_storage', True),
            'enable_economic_optimization': params.get('enable_economic_optimization', True),
            'max_simultaneous_services': params.get('max_simultaneous_services', 5),
            'max_frequency_response': params.get('max_frequency_response', 0.15),
            'max_voltage_response': params.get('max_voltage_response', 0.10),
            'max_storage_response': params.get('max_storage_response', 0.20)        }
        self.grid_services_coordinator = create_standard_grid_services_coordinator()
        
        # Initialize new physics modules (Chain, Fluid, Thermal)
        # Chain system configuration
        chain_config = {
            'sprocket_radius': params.get('sprocket_radius', 1.0),
            'tank_height': params.get('tank_height', 10.0),
            'chain_mass_per_meter': params.get('chain_mass_per_meter', 10.0),
            'num_floaters': params.get('num_floaters', 8),
            'max_tension': params.get('max_chain_tension', 50000.0),
            'elastic_modulus': params.get('chain_elastic_modulus', 200e9),
            'cross_sectional_area': params.get('chain_cross_section', 0.001)
        }
        self.chain_system = Chain(chain_config)
        
        # Fluid system configuration
        fluid_config = {
            'water_density': params.get('water_density', 1000.0),
            'water_temperature': params.get('water_temperature', 293.15),
            'gravity': params.get('gravity', 9.81),
            'kinematic_viscosity': params.get('kinematic_viscosity', 1.0e-6),
            'drag_coefficient': params.get('drag_coefficient', 0.6),
            'floater_area': params.get('floater_area', 0.1),
            'h1_active': params.get('h1_active', False),
            'h1_bubble_fraction': params.get('h1_bubble_fraction', 0.05),
            'h1_drag_reduction': params.get('h1_drag_reduction', 0.1)
        }
        self.fluid_system = Fluid(fluid_config)
        
        # Thermal model configuration
        thermal_config = {
            'water_temperature': params.get('water_temperature', 293.15),
            'ambient_temperature': params.get('ambient_temperature', 293.15),
            'h2_active': params.get('h2_active', False),
            'h2_efficiency': params.get('h2_efficiency', 0.8),
            'h2_buoyancy_boost': params.get('h2_buoyancy_boost', 0.05),
            'h2_compression_improvement': params.get('h2_compression_improvement', 0.15)
        }
        self.thermal_model = ThermalModel(thermal_config)
        
        # Stage 2: Initialize H1, H2, H3 enhanced physics modules
        # H1: Nanobubble Physics (drag/density reduction)
        h1_config = {
            'bubble_volume_fraction': params.get('h1_bubble_fraction', 0.05),
            'drag_reduction_factor': params.get('h1_drag_reduction', 0.1),
            'density_reduction_factor': params.get('h1_density_reduction', 0.02),
            'activation_depth': params.get('h1_activation_depth', 2.0),
            'decay_rate': params.get('h1_decay_rate', 0.1),
            'h1_enabled': params.get('h1_active', False)
        }
        self.nanobubble_physics = NanobubblePhysics(h1_config)
        
        # H2: Thermal Physics (thermal expansion/boost)
        h2_config = {
            'thermal_coefficient': params.get('h2_thermal_coefficient', 0.0002),
            'heat_capacity_ratio': params.get('h2_heat_capacity_ratio', 1.4),
            'heat_transfer_coefficient': params.get('h2_heat_transfer_coeff', 50.0),
            'ambient_temperature': params.get('ambient_temperature', 293.15),
            'water_temperature': params.get('water_temperature', 293.15),
            'h2_enabled': params.get('h2_active', False)
        }
        self.thermal_physics = ThermalPhysics(h2_config)
        
        # H3: Pulse Controller (pulse-and-coast clutch control)
        h3_config = {
            'pulse_duration': params.get('h3_pulse_duration', 2.0),
            'coast_duration': params.get('h3_coast_duration', 3.0),
            'clutch_engagement_threshold': params.get('h3_clutch_threshold', 0.1),
            'torque_modulation_factor': params.get('h3_torque_modulation', 0.8),
            'efficiency_boost': params.get('h3_efficiency_boost', 0.05),
            'enabled': params.get('h3_active', False)
        }
            'enabled': params.get('h3_active', False)
        }
        self.pulse_controller = PulseController(h3_config)
        
        logger.info("Chain, Fluid, and Thermal systems initialized")
          # Initialize Phase 7 pneumatic coordinator integration
        from simulation.pneumatics.pneumatic_coordinator import create_standard_kpp_pneumatic_coordinator
        from simulation.pneumatics.energy_analysis import create_standard_energy_analyzer
        from simulation.pneumatics.performance_metrics import create_standard_performance_analyzer
          # Pneumatic system coordinator configuration
        enable_thermal_mgmt = params.get('thermal_management_enabled', True)
        enable_optimization = params.get('pneumatic_optimization_enabled', True)
        
        self.pneumatic_coordinator = create_standard_kpp_pneumatic_coordinator(
            enable_thermodynamics=enable_thermal_mgmt,
            enable_optimization=enable_optimization
        )
          # Initialize Phase 7 energy analysis and performance monitoring
        compressor_power = params.get('compressor_power', 4200.0)  # 4.2 kW
        self.pneumatic_energy_analyzer = create_standard_energy_analyzer(analysis_window=60.0)
        self.pneumatic_performance_analyzer = create_standard_performance_analyzer(rated_power=compressor_power)
        
        logger.info("Pneumatic coordinator and performance analysis systems initialized")
        
        # Phase 8: Initialize new physics engine and enhanced event handler (Stage 2)
        physics_params = {
            'time_step': self.dt,
            'chain_mass': self.chain_length * self.chain_mass_per_meter,
            'friction_coefficient': params.get('friction_coefficient', 0.01),
            'adaptive_timestep': params.get('adaptive_timestep_enabled', False),
            'min_timestep': params.get('min_timestep', 0.01),
            'max_timestep': params.get('max_timestep', 0.2)
        }
        self.physics_engine = PhysicsEngine(physics_params)
        
        # Store number of floaters for validation framework
        self.num_floaters = params.get('num_floaters', 1)
        
        # Initialize advanced event handler for floater state transitions (Stage 2)
        tank_depth = params.get('tank_depth', 10.0)
        optimization_params = {
            'adaptive_pressure': params.get('adaptive_pressure_enabled', True),
            'pressure_safety_factor': params.get('pressure_safety_factor', 1.2),
            'min_injection_pressure': params.get('min_injection_pressure', 150000),
            'efficiency_target': params.get('energy_efficiency_target', 0.4)
        }
        
        # Import and initialize advanced event handler
        from simulation.physics.advanced_event_handler import AdvancedEventHandler
        self.advanced_event_handler = AdvancedEventHandler(tank_depth, optimization_params)
        
        # Stage 4: Initialize real-time optimization and monitoring systems
        target_fps = params.get('target_fps', 10.0)
        self.real_time_optimizer = RealTimeOptimizer(target_fps)
        self.real_time_controller = RealTimeController()
        
        # Configure performance mode based on params
        performance_mode = params.get('performance_mode', 'balanced')
        self.real_time_controller.configure_performance_mode(performance_mode)
        
        logger.info(f"Real-time optimization initialized: target_fps={target_fps}, mode={performance_mode}")
        
        # Initialize state synchronizer for immediate consistency (Stage 2)
        from simulation.physics.state_synchronizer import StateSynchronizer
        
        self.state_synchronizer = StateSynchronizer(self.physics_engine, self.advanced_event_handler)
        
        logger.info("Enhanced physics engine, advanced event handler, and state synchronizer initialized")
        logger.info(f"Stage 2 features: adaptive_pressure={optimization_params['adaptive_pressure']}, "
                   f"efficiency_target={optimization_params['efficiency_target']}")

    def update_params(self, params):
        """
        Update simulation parameters and component parameters.
        """
        self.params.update(params)
        self.drivetrain.update_params(self.params)
        # TODO: Implement parameter updates for AdvancedGenerator if needed
        # self.generator.update_params(self.params)
        
        # Update existing floaters instead of recreating them
        for floater in self.floaters:
            floater.volume = self.params.get('floater_volume', floater.volume)
            floater.mass = self.params.get('floater_mass_empty', floater.mass)
            floater.area = self.params.get('floater_area', floater.area)
            floater.Cd = self.params.get('floater_Cd', floater.Cd)
            floater.air_fill_time = self.params.get('air_fill_time', floater.air_fill_time)

        logger.info("Simulation parameters updated.")

    def trigger_pulse(self):
        """
        Trigger air injection pulse on the next available floater via the pneumatic system.
        """
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
        # Force an initial pulse at t=0 to kick off the system
        if self.time == 0.0:
            logger.info("Forcing initial pulse at t=0.0")
            self.trigger_pulse()
        while self.running:
            logger.debug(f"Step start: t={self.time:.2f}")
            for i, floater in enumerate(self.floaters):
                logger.debug(f"Floater {i}: theta={getattr(floater, 'theta', 0.0):.2f}, filled={getattr(floater, 'is_filled', False)}, pos={floater.get_cartesian_position() if hasattr(floater, 'get_cartesian_position') else 'N/A'}")
            logger.debug(f"Drivetrain: omega_chain={getattr(self.drivetrain, 'omega_chain', 0.0):.2f}, omega_flywheel={getattr(self.drivetrain, 'omega_flywheel', 0.0):.2f}, clutch_engaged={getattr(self.drivetrain, 'clutch_engaged', False)}")
            logger.debug(f"Generator: angular_velocity={getattr(self.generator, 'angular_velocity', 0.0):.2f}, electrical_power={getattr(self.generator, 'electrical_power', 0.0):.2f}")
            self.step(self.dt)
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

    def step(self, dt):
        """
        Perform a single simulation step using the enhanced physics engine and real-time optimization (Stage 4).
        """
        if dt <= 0:
            raise ValueError("Time step dt must be positive.")

        # Stage 4: Real-time optimized simulation loop
        step_start_time = time.time()
        
        # 1. Synchronize floater states before processing
        sync_summary = self.state_synchronizer.synchronize_all_floaters(self.floaters, self.time)
        
        # 2. Handle floater state transitions with advanced event processing
        event_summary = self.advanced_event_handler.process_all_events(self.floaters, self.time)
        
        # 3. Update physics engine energy input from injections
        self.physics_engine.energy_input = self.advanced_event_handler.energy_input
        
        # 4. Get generator torque and sprocket radius
        sprocket_radius = self.params.get('sprocket_radius', 1.0)
        
        # Use dynamic generator control if available, otherwise constant torque
        generator_torque = self.params.get('generator_torque', 500.0)  # N⋅m
        
        # 5. Real-time force calculation optimization
        optimization_result = self.real_time_optimizer.optimize_force_calculations(self.floaters)
        
        # 6. Perform enhanced physics engine step with adaptive timestep
        # Prepare H1, H2, H3 enhanced physics modules for passing to physics engine
        enhanced_physics = {
            'nanobubble': self.nanobubble_physics,
            'thermal': self.thermal_physics, 
            'pulse_controller': self.pulse_controller
        }
        
        # Apply H3 pulse controller effects before physics step
        if self.pulse_controller.state.enabled:
            # Update pulse controller state
            system_speed = abs(self.physics_engine.v_chain) if hasattr(self.physics_engine, 'v_chain') else 0.0
            pulse_result = self.pulse_controller.update(self.time, system_speed, generator_torque, dt)
            # Get modified generator torque from pulse controller
            generator_torque = self.pulse_controller.get_generator_load_torque(generator_torque)
        
        physics_state = self.physics_engine.step(
            self.floaters, 
            generator_torque, 
            sprocket_radius,
            enhanced_physics
        )
        
        # 7. Real-time optimization and monitoring
        optimization_recommendations = self.real_time_optimizer.optimize_step(physics_state, step_start_time)
        
        # Apply adaptive timestep if recommended
        if optimization_recommendations.get('adjust_timestep', False):
            new_dt = optimization_recommendations['new_timestep']
            if abs(new_dt - dt) > 1e-6:
                self.dt = new_dt
                logger.debug(f"Adaptive timestep: {dt:.4f} → {new_dt:.4f}")
        
        # 8. Post-simulation state validation and synchronization
        validation_results = self.state_synchronizer.validate_system_consistency(self.floaters)
        if not validation_results['consistent']:
            logger.warning(f"State inconsistencies detected: {len(validation_results['inconsistencies'])} issues")
        
        # 9. Update legacy components for compatibility
        self._update_legacy_components(dt, physics_state)
        
        # 10. Real-time data processing and streaming
        performance_data = self.real_time_optimizer.get_performance_report()
        rt_processing_result = self.real_time_controller.process_realtime_data(
            physics_state, performance_data
        )
        
        # 11. Enhanced data logging with Stage 4 metrics  
        self._log_simulation_data(physics_state, event_summary, optimization_recommendations, rt_processing_result)
        self.time += dt
    
    def _update_legacy_components(self, dt, physics_state):
        """
        Update legacy components to maintain compatibility.
        
        Args:
            dt (float): Time step
            physics_state (dict): State from physics engine
        """
        # Update pneumatic system
        self.pneumatics.update(dt)
        
        # Update thermal and fluid systems
        if hasattr(self, 'fluid_system'):
            self.fluid_system.update_state()
        if hasattr(self, 'thermal_model'):
            self.thermal_model.update_state()
        
        # Update drivetrain with physics engine outputs
        if hasattr(self, 'drivetrain'):
            # Convert chain velocity to angular velocity
            sprocket_radius = self.params.get('sprocket_radius', 1.0)
            omega = physics_state['angular_velocity']
            self.drivetrain.omega_chain = omega
            self.drivetrain.omega_flywheel = omega  # Simplified for now
        
        # Update generator
        if hasattr(self, 'generator'):
            self.generator.angular_velocity = physics_state['angular_velocity']
            self.generator.electrical_power = physics_state['power_output']
        
        # Update chain tension
        self.chain_tension = abs(physics_state['net_force_total'] / sprocket_radius) if sprocket_radius > 0 else 0.0
        
        # Reset event handler cycle tracking periodically
        if self.time % 5.0 < dt:  # Every 5 seconds
            self.advanced_event_handler.reset_cycle_tracking()
    
    def _log_simulation_data(self, physics_state, event_summary, optimization_recommendations=None, rt_processing_result=None):
        """
        Log simulation data for streaming and analysis (Enhanced for Stage 4).
        
        Args:
            physics_state (dict): State from physics engine
            event_summary (dict): Summary of events processed
            optimization_recommendations (dict): Real-time optimization recommendations
            rt_processing_result (dict): Real-time processing results
        """
        # Create enhanced data entry for logging/streaming
        data_entry = {
            'time': physics_state['time'],
            'chain_velocity': physics_state['chain_velocity'],
            'chain_acceleration': physics_state['chain_acceleration'],
            'net_force': physics_state['net_force_total'],
            'angular_velocity': physics_state['angular_velocity'],
            'power_output': physics_state['power_output'],
            'energy_output': physics_state['energy_output'],
            'energy_input': physics_state['energy_input'],
            'net_energy': physics_state['energy_output'] - physics_state['energy_input'],
            'injections': event_summary['injections'],
            'ventings': event_summary['ventings'],
            'floater_count': len(self.floaters),
            'floaters': [
                {
                    'id': i,
                    'angle': getattr(f, 'angle', getattr(f, 'theta', 0.0)),
                    'state': getattr(f, 'state', 'unknown'),
                    'is_filled': getattr(f, 'is_filled', False),
                    'mass': f.mass,
                    'velocity': getattr(f, 'velocity', 0.0)
                }
                for i, f in enumerate(self.floaters)
            ]
        }
        
        # Stage 2: Add advanced event handler metrics
        if hasattr(self.advanced_event_handler, 'get_energy_analysis'):
            energy_analysis = self.advanced_event_handler.get_energy_analysis()
            data_entry.update({
                'average_injection_energy': energy_analysis.get('average_energy_per_injection', 0.0),
                'injection_success_rate': energy_analysis.get('injection_success_rate', 1.0),
                'estimated_system_efficiency': energy_analysis.get('estimated_system_efficiency', 0.0),
                'energy_optimization_active': event_summary.get('energy_optimization_active', False)
            })
        
        # Stage 4: Add real-time optimization metrics
        if optimization_recommendations:
            data_entry.update({
                'optimization_timestep_adjusted': optimization_recommendations.get('adjust_timestep', False),
                'optimization_timestep': optimization_recommendations.get('new_timestep', self.dt),
                'optimization_warnings': len(optimization_recommendations.get('warnings', [])),
                'stability_score': optimization_recommendations.get('stability_score', 1.0),
                'continue_simulation': optimization_recommendations.get('continue', True)
            })
        
        # Stage 4: Add real-time processing metrics
        if rt_processing_result:
            data_entry.update({
                'rt_processed': rt_processing_result.get('processed', False),
                'rt_alerts': len(rt_processing_result.get('alerts', [])),
                'rt_recovery_actions': len(rt_processing_result.get('recovery_actions', [])),
                'rt_streaming_enabled': rt_processing_result.get('streaming_status', {}).get('enabled', False),
                'rt_subscribers': rt_processing_result.get('streaming_status', {}).get('subscribers', 0)
            })
        
        # Add to data log
        self.data_log.append(data_entry)
        
        # Stream data to clients if queue exists
        if hasattr(self, 'data_queue') and self.data_queue:
            try:
                self.data_queue.put_nowait(data_entry)
            except:
                pass  # Queue might be full, ignore
        
        # Enhanced logging with Stage 4 metrics
        if self.time % 10.0 < self.dt:  # Every 10 seconds
            efficiency = (physics_state['energy_output'] / physics_state['energy_input'] * 100) if physics_state['energy_input'] > 0 else 0
            
            log_msg = (f"t={self.time:.1f}s: P_out={physics_state['power_output']:.1f}W, "
                      f"v_chain={physics_state['chain_velocity']:.3f}m/s, "
                      f"efficiency={efficiency:.1}%")
            
            # Add Stage 4 metrics to log
            if optimization_recommendations:
                stability = optimization_recommendations.get('stability_score', 1.0)
                log_msg += f", stability={stability:.2f}"
                
            if rt_processing_result:
                alerts = len(rt_processing_result.get('alerts', []))
                if alerts > 0:
                    log_msg += f", alerts={alerts}"
            
            logger.info(log_msg)
    
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
                floater.state = 'FILLED'
            else:
                floater.is_filled = False
                floater.fill_progress = 0.0
                floater.state = 'EMPTY'
        # Ensure one floater at injection is ready to fill (simulate injection point at theta=0)
        self.floaters[0].set_theta(0.0)
        self.floaters[0].is_filled = True
        self.floaters[0].fill_progress = 0.0
        self.floaters[0].state = 'FILLING'
        logger.info("Floaters initialized for calibrated startup: ascending side buoyant, descending side drawing, one ready for injection.")
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
    
    def set_h1_nanobubbles(self, active: bool, bubble_fraction: float = 0.05, 
                          drag_reduction: float = 0.1):
        """
        Enable/disable H1 nanobubble effects.
        
        Args:
            active (bool): Whether to activate H1 nanobubble effects
            bubble_fraction (float): Volume fraction of nanobubbles (0-0.2)
            drag_reduction (float): Drag reduction factor (0-0.5)
        """
        self.fluid_system.set_h1_active(active, bubble_fraction, drag_reduction)
        logger.info(f"H1 nanobubbles {'activated' if active else 'deactivated'}: "
                   f"bubble_fraction={bubble_fraction:.1%}, drag_reduction={drag_reduction:.1%}")
    
    def set_h2_thermal(self, active: bool, efficiency: float = 0.8, 
                      buoyancy_boost: float = 0.05, compression_improvement: float = 0.15):
        """
        Enable/disable H2 isothermal thermal effects.
        
        Args:
            active (bool): Whether to activate H2 thermal effects
            efficiency (float): H2 process efficiency (0-1)
            buoyancy_boost (float): Buoyancy enhancement factor (0-0.3)
            compression_improvement (float): Compression work reduction (0-0.5)
        """
        self.thermal_model.set_h2_active(active, efficiency, buoyancy_boost, compression_improvement)
        logger.info(f"H2 thermal effects {'activated' if active else 'deactivated'}: "
                   f"efficiency={efficiency:.1%}, buoyancy_boost={buoyancy_boost:.1%}, "
                   f"compression_improvement={compression_improvement:.1%}")
    
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
            'chain_system': self.chain_system.get_state(),
            'fluid_system': self.fluid_system.get_fluid_properties(),
            'thermal_system': self.thermal_model.get_thermal_properties(),
            'h1_status': {
                'active': self.fluid_system.h1_active,
                'bubble_fraction': self.fluid_system.h1_bubble_fraction,
                'drag_reduction': self.fluid_system.h1_drag_reduction,
                'effective_density': self.fluid_system.state.effective_density
            },
            'h2_status': {
                'active': self.thermal_model.h2_active,
                'efficiency': self.thermal_model.h2_efficiency,
                'buoyancy_enhancement': self.thermal_model.state.buoyancy_enhancement,
                'compression_work_reduction': self.thermal_model.state.compression_work_reduction
            }
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
        base_buoy = latest_state.get('base_buoy_force', 0.0)
        enhanced_buoy = latest_state.get('enhanced_buoy_force', base_buoy)
        thermal_buoy = latest_state.get('thermal_enhanced_force', enhanced_buoy)
        
        h1_enhancement = (enhanced_buoy - base_buoy) / max(base_buoy, 1.0) if base_buoy > 0 else 0.0
        h2_enhancement = (thermal_buoy - enhanced_buoy) / max(enhanced_buoy, 1.0) if enhanced_buoy > 0 else 0.0
        total_enhancement = (thermal_buoy - base_buoy) / max(base_buoy, 1.0) if base_buoy > 0 else 0.0
        
        return {
            'h1_buoyancy_enhancement': h1_enhancement,
            'h2_thermal_enhancement': h2_enhancement,
            'total_physics_enhancement': total_enhancement,
            'base_buoyant_force': base_buoy,
            'h1_enhanced_force': enhanced_buoy,
            'h2_thermal_force': thermal_buoy,
            'fluid_properties': self.fluid_system.get_fluid_properties(),
            'thermal_properties': self.thermal_model.get_thermal_properties()
        }
    
    def collect_state(self) -> dict:
        """
        Collect current simulation state for API consumption.
        
        Returns:
            dict: Current simulation state
        """
        try:
            # Get the latest data from the data queue
            if hasattr(self, 'data_queue') and not self.data_queue.empty():
                latest_data = None
                # Get the most recent data from queue
                while not self.data_queue.empty():
                    try:
                        latest_data = self.data_queue.get_nowait()
                    except:
                        break
                if latest_data:
                    return latest_data
            
            # Fallback: create state from current engine state
            return {
                'time': getattr(self, 'time', 0.0),
                'chain_velocity': getattr(self, 'chain_velocity', 0.0),
                'power': getattr(self, 'power_output', 0.0),
                'torque': getattr(self, 'torque', 0.0),
                'avg_floater_velocity': 0.0,
                'floaters': [
                    {
                        'id': i,
                        'angle': getattr(f, 'angle', getattr(f, 'theta', 0.0)),
                        'state': getattr(f, 'state', 'unknown'),
                        'is_filled': getattr(f, 'is_filled', False),
                        'mass': f.mass,
                        'velocity': getattr(f, 'velocity', 0.0)
                    }
                    for i, f in enumerate(getattr(self, 'floaters', []))
                ],
                'status': 'running' if getattr(self, 'running', False) else 'stopped'
            }
        except Exception as e:
            logger.error(f"Error collecting state: {e}")
            return {
                'time': 0.0,
                'chain_velocity': 0.0,
                'power': 0.0,
                'torque': 0.0,
                'avg_floater_velocity': 0.0,
                'floaters': [],
                'status': 'error',
                'error': str(e)
            }
