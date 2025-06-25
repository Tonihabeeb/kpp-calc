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
from simulation.components.floater import Floater
from simulation.components.drivetrain import Drivetrain
from simulation.components.generator import Generator
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
        self.enhanced_loss_model = create_standard_kpp_enhanced_loss_model(ambient_temperature)
        
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
        # Keep legacy generator for compatibility during transition
        self.generator = Generator(
            efficiency=params.get('generator_efficiency', 0.92),
            target_power=params.get('target_power', 530000.0),
            target_rpm=params.get('target_rpm', 375.0)
        )
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
        self.thread = None
        logger.info("SimulationEngine initialized with integrated drivetrain system.")
        # Initialize default chain geometry for torque calculations
        self.set_chain_geometry()

        # Initialize grid services coordinator (Phase 7)
        grid_services_config = {
            'enable_frequency_services': params.get('enable_frequency_services', True),
            'enable_voltage_services': params.get('enable_voltage_services', False),  # TODO: Enable in Week 2
            'enable_demand_response': params.get('enable_demand_response', False),   # TODO: Enable in Week 3
            'enable_energy_storage': params.get('enable_energy_storage', False),    # TODO: Enable in Week 4
            'enable_economic_optimization': params.get('enable_economic_optimization', False), # TODO: Enable in Week 5
            'max_simultaneous_services': params.get('max_simultaneous_services', 3),
            'max_frequency_response': params.get('max_frequency_response', 0.15),
            'max_voltage_response': params.get('max_voltage_response', 0.10),
            'max_storage_response': params.get('max_storage_response', 0.20)
        }
        self.grid_services_coordinator = create_standard_grid_services_coordinator()
        
    def update_params(self, params):
        """
        Update simulation parameters and component parameters.
        """
        self.params.update(params)
        self.drivetrain.update_params(self.params)
        self.generator.update_params(self.params)
        
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
            logger.debug(f"Generator: target_omega={getattr(self.generator, 'target_omega', 0.0):.2f}, target_power={getattr(self.generator, 'target_power', 0.0):.2f}")
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
        Perform a single simulation step using the modular components.
        """
        if dt <= 0:
            raise ValueError("Time step dt must be positive.")

        # 1. Check for pulse trigger
        if self.time - self.last_pulse_time >= self.params.get('pulse_interval', 2.0):
            if self.trigger_pulse():
                self.last_pulse_time = self.time

        # 2. Update component states
        self.pneumatics.update(dt)

        # 2a. Update chain kinematics: advance all floaters' theta
        omega_chain = self.drivetrain.omega_chain
        for floater in self.floaters:
            prev_theta = getattr(floater, 'theta', 0.0)
            floater.set_theta(prev_theta + omega_chain * dt)
            # If floater completes a revolution, vent and reset
            # Detect top sprocket crossing (180° pivot)
            if prev_theta % (2*math.pi) < math.pi and floater.theta % (2*math.pi) >= math.pi:
                floater.pivot()

            # Detect bottom sprocket crossing (360° pivot + water drainage)
            if prev_theta < 2 * math.pi and floater.theta >= 2 * math.pi:
                floater.pivot()
                floater.drain_water()
                floater.is_filled = False
                floater.fill_progress = 0.0
                # Trigger air injection after drainage
                self.pneumatics.trigger_injection(floater)
            floater.update(dt)

        # After kinematics update, track energy losses
        drag_loss_sum = sum(f.drag_loss for f in self.floaters)
        dissolution_loss_sum = sum(f.dissolution_loss for f in self.floaters)
        venting_loss_sum = sum(f.venting_loss for f in self.floaters)        # 3. Calculate chain tension from all floaters
        total_vertical_force = 0.0
        base_buoy_force = 0.0
        pulse_force = 0.0
        
        for i, floater in enumerate(self.floaters):
            x, y = floater.get_cartesian_position()
            vertical_force = floater.get_vertical_force()
            # Log per-floater forces
            logger.debug(f"Floater {i}: x={x:.2f}, y={y:.2f}, vertical_force={vertical_force:.2f}, is_filled={floater.is_filled}, fill_progress={floater.fill_progress:.2f}, state={getattr(floater, 'state', 'N/A')}")
            
            # Sum up vertical forces to calculate chain tension
            total_vertical_force += vertical_force
            
            # Track component forces for debugging
            buoy_force = floater.compute_buoyant_force()
            base_buoy_force += buoy_force
            
            jet_force = floater.compute_pulse_jet_force()
            if abs(jet_force) > 1e-3:
                pulse_force += jet_force
          # Update chain tension (positive = upward tension)
        self.chain_tension = total_vertical_force
          # 4. Get drivetrain output torque and speed from integrated drivetrain
        # The integrated drivetrain handles the full conversion from chain tension to mechanical output
        drivetrain_output = self.integrated_drivetrain.update(self.chain_tension, 0.0, dt)  # Temporary zero load
        
        # Extract mechanical values for electrical system
        output_torque = drivetrain_output.get('gearbox_output_torque', 0.0)
        output_speed_rpm = drivetrain_output.get('flywheel_speed_rpm', 0.0)
        output_speed_rad_s = output_speed_rpm * (2 * math.pi / 60)  # Convert to rad/s
        
        # 5. Build system state for control system
        system_state = {
            'time': self.time,
            'chain_tension': self.chain_tension,
            'mechanical_torque': output_torque,
            'mechanical_speed_rpm': output_speed_rpm,
            'mechanical_speed_rad_s': output_speed_rad_s,
            'total_vertical_force': total_vertical_force,
            'base_buoy_force': base_buoy_force,
            'pulse_force': pulse_force,
            'floater_states': [f.to_dict() for f in self.floaters],
            'pneumatics': {
                'tank_pressure': self.pneumatics.tank_pressure,
                'compressor_running': getattr(self.pneumatics, 'compressor_running', False)
            },
            'energy_losses': {
                'drag_loss': drag_loss_sum,
                'dissolution_loss': dissolution_loss_sum,
                'venting_loss': venting_loss_sum
            }
        }        # 6. Update integrated control system with current state
        control_output = self.integrated_control_system.update(system_state, dt)
        
        # Extract control system commands
        timing_commands = control_output.get('timing_commands', {})
        load_commands = control_output.get('load_commands', {})
        grid_commands = control_output.get('grid_commands', {})
        fault_status = control_output.get('fault_status', {})
        control_mode = control_output.get('control_mode', 'normal')
        
        # Execute pneumatic control through timing controller
        pneumatic_executed = False
        if hasattr(self.integrated_control_system.timing_controller, 'execute_pneumatic_control'):
            pneumatic_executed = self.integrated_control_system.timing_controller.execute_pneumatic_control(
                self.pneumatics, self.floaters
            )
        
        # Apply control system recommendations
        # Pulse timing control
        pulse_timing_adjustment = timing_commands.get('pulse_timing_adjustment', 0.0)
        pulse_interval_adjustment = timing_commands.get('pulse_interval_adjustment', 0.0)
        
        # Load management
        target_load_factor = load_commands.get('target_load_factor', 0.8)
        power_setpoint = load_commands.get('power_setpoint', self.params.get('target_power', 530000.0))
        
        # Grid stability
        voltage_setpoint = grid_commands.get('voltage_setpoint', 480.0)
        frequency_setpoint = grid_commands.get('frequency_setpoint', 60.0)
          # 7. Update integrated electrical system with mechanical input and control commands
        electrical_config_updates = {
            'target_load_factor': target_load_factor,
            'power_setpoint': power_setpoint,
            'voltage_setpoint': voltage_setpoint,
            'frequency_setpoint': frequency_setpoint,
            'control_mode': control_mode
        }
        electrical_output = self.integrated_electrical_system.update(output_torque, output_speed_rad_s, dt, electrical_config_updates)
        
        # 8. Update transient event controller (Phase 6)
        # Build comprehensive system state for transient event monitoring
        comprehensive_system_state = system_state.copy()
        comprehensive_system_state.update({
            'flywheel_speed_rpm': output_speed_rpm,
            'chain_speed_rpm': drivetrain_output.get('chain_speed_rpm', 0.0),
            'torque': output_torque,
            'grid_voltage': electrical_output.get('grid_voltage', 480.0),
            'grid_frequency': electrical_output.get('grid_frequency', 60.0),
            'grid_connected': electrical_output.get('synchronized', False),
            'component_temperatures': {
                'sprocket': 20.0, 'gearbox': 20.0, 'clutch': 20.0, 
                'flywheel': 20.0, 'generator': 20.0
            }
        })
        
        # Update transient event controller
        transient_commands = self.transient_controller.update_transient_events(comprehensive_system_state, self.time)
        
        # 9. Update drivetrain again with actual electrical load torque
        electrical_load_torque = electrical_output.get('load_torque_command', 0.0)
        grid_power_output = electrical_output.get('grid_power_output', 0.0)
        electrical_efficiency = electrical_output.get('system_efficiency', 0.0)
          # Extract electrical system outputs
        electrical_load_torque = electrical_output.get('load_torque_command', 0.0)
        grid_power_output = electrical_output.get('grid_power_output', 0.0)
        electrical_efficiency = electrical_output.get('system_efficiency', 0.0)
        
        # 10. Update drivetrain again with actual electrical load torque
          # This provides the proper load feedback to the mechanical system
        drivetrain_output = self.integrated_drivetrain.update(self.chain_tension, electrical_load_torque, dt)
        
        # Get final drivetrain values after load feedback
        final_output_torque = drivetrain_output.get('gearbox_output_torque', 0.0)
        final_output_speed = drivetrain_output.get('flywheel_speed_rpm', 0.0) * (2 * math.pi / 60)
          # 11. Update enhanced loss model (Phase 5)
        enhanced_system_state = {
            'input_power': abs(output_torque * output_speed_rad_s),
            'output_power': grid_power_output,
            'electrical_power': grid_power_output,
            'sprocket': {
                'torque': drivetrain_output.get('sprocket_torque', 0.0),
                'speed': drivetrain_output.get('chain_speed', 0.0),
                'load_factor': 0.5,
                'efficiency': 0.98
            },
            'gearbox': {
                'torque': output_torque,
                'speed': output_speed_rad_s,
                'load_factor': min(1.0, abs(output_torque) / 2000.0),
                'efficiency': drivetrain_output.get('gearbox_efficiency', 0.885)
            },
            'clutch': {
                'torque': output_torque,
                'speed': output_speed_rad_s,
                'load_factor': min(1.0, abs(output_torque) / 2000.0),
                'efficiency': drivetrain_output.get('clutch_efficiency', 0.95)
            },
            'flywheel': {
                'torque': final_output_torque,
                'speed': final_output_speed,
                'load_factor': min(1.0, abs(final_output_torque) / 2000.0),
                'efficiency': drivetrain_output.get('flywheel_efficiency', 0.98)
            },
            'generator': {
                'torque': electrical_load_torque,
                'speed': final_output_speed,
                'load_factor': electrical_output.get('load_factor', 0.0),
                'efficiency': electrical_efficiency
            },
            'electrical': {
                'current': grid_power_output / max(480.0, electrical_output.get('grid_voltage', 480.0)),
                'voltage': electrical_output.get('grid_voltage', 480.0),
                'frequency': electrical_output.get('grid_frequency', 60.0),
                'temperature': 40.0,  # Estimate electrical system temperature
                'switching_frequency': 5000.0,
                'flux_density': 1.0
            }
        }
        
        enhanced_state = self.enhanced_loss_model.update_system_losses(enhanced_system_state, dt)
        
        # 10. Update control system with electrical results for feedback
        electrical_state = {
            'electrical_power_output': grid_power_output,
            'electrical_efficiency': electrical_efficiency,
            'load_torque': electrical_load_torque,
            'synchronized': electrical_output.get('synchronized', False),
            'load_factor': electrical_output.get('load_factor', 0.0),
            'grid_voltage': electrical_output.get('grid_voltage', 480.0),
            'grid_frequency': electrical_output.get('grid_frequency', 60.0),
            'enhanced_losses': enhanced_state.system_losses,
            'thermal_state': enhanced_state.performance_metrics        }
        system_state.update(electrical_state)
        
        logger.info(f"Integrated System: chain_tension={self.chain_tension:.2f}N, "
                   f"mech_torque={final_output_torque:.2f}N·m, mech_speed={final_output_speed:.2f}rad/s, "
                   f"elec_load={electrical_load_torque:.2f}N·m, grid_power={grid_power_output/1000:.1f}kW")
        logger.info(f"Electrical: sync={electrical_output.get('synchronized', False)}, "
                   f"efficiency={electrical_efficiency:.3f}, load_factor={electrical_output.get('load_factor', 0):.3f}")
        logger.info(f"Control: mode={control_mode}, timing_adj={pulse_timing_adjustment:.3f}, "
                   f"load_target={target_load_factor:.3f}, faults={len(fault_status.get('active_faults', []))}")
        
        # 10. Calculate final power output
        power_output = grid_power_output  # Use grid power output from electrical system
        
        self.total_energy += power_output * dt        # For legacy compatibility, update the old drivetrain with equivalent values
        # This maintains compatibility with existing logging and monitoring systems
        self.drivetrain.omega_chain = drivetrain_output.get('chain_speed_rpm', 0.0) * (2 * math.pi / 60)
        self.drivetrain.omega_flywheel = final_output_speed
        
        # Calculate derived values for logging compatibility
        tau_net = final_output_torque - electrical_load_torque
        tau_to_generator = drivetrain_output.get('clutch_transmitted_torque', final_output_torque)
        clutch_engagement_factor = drivetrain_output.get('clutch_engagement_factor', 0.0)
        clutch_engaged = drivetrain_output.get('clutch_engaged', False)# 7. Track energy losses
        # Capture clutch state for logging
        clutch_state_val = 'engaged' if clutch_engaged else 'disengaged'
        drag_loss_sum = sum(f.drag_loss for f in self.floaters)
        dissolution_loss_sum = sum(f.dissolution_loss for f in self.floaters)
        venting_loss_sum = sum(f.venting_loss for f in self.floaters)
          # Compute net energy balance
        net_energy_balance = power_output - (drag_loss_sum + dissolution_loss_sum + venting_loss_sum)        
        self.log_state(
            power_output,
            final_output_torque,
            base_buoy_force=base_buoy_force,  # Updated variable name
            pulse_force=pulse_force,          # Updated variable name
            total_vertical_force=total_vertical_force,  # Updated variable name
            tau_net=tau_net,
            tau_to_generator=tau_to_generator,
            clutch_c=clutch_engagement_factor,
            clutch_state=clutch_state_val,
            drag_loss=drag_loss_sum,
            dissolution_loss=dissolution_loss_sum,
            venting_loss=venting_loss_sum,
            net_energy=net_energy_balance,
            control_output=control_output,
            electrical_output=electrical_output,
            pneumatic_executed=pneumatic_executed,
            enhanced_state=enhanced_state
        )# 8. Collect and log data
        self.time += dt
        
        # Return the complete state data for external access
        return self.collect_state()

    def log_state(self, power_output, torque, base_buoy_force=None, pulse_force=None, total_vertical_force=None, tau_net=None, tau_to_generator=None, clutch_c=None, clutch_state=None, drag_loss=None, dissolution_loss=None, venting_loss=None, net_energy=None, control_output=None, electrical_output=None, pneumatic_executed=False, enhanced_state=None):
        """
        Collect and log the current state of the simulation, including force breakdowns and clutch state.
        """
        print(f"LOG_STATE: t={self.time:.2f}, power={power_output:.2f}, torque={torque:.2f}, base_buoy_force={base_buoy_force}, pulse_force={pulse_force}, clutch_c={clutch_c}, clutch_state={clutch_state}, drag_loss={drag_loss}, dissolution_loss={dissolution_loss}, venting_loss={venting_loss}, net_energy={net_energy}")
        drivetrain_state = self.drivetrain.get_state()
        # Compute overall mechanical efficiency (output electrical power / mechanical input power)
        omega_fly = drivetrain_state['omega_flywheel_rpm'] * (2 * math.pi / 60)
        if torque and omega_fly:
            overall_eff = power_output / (torque * omega_fly)
        else:
            overall_eff = 0.0
        # Compute average floater velocity
        if self.floaters:
            avg_velocity = sum(abs(f.velocity) for f in self.floaters) / len(self.floaters)
        else:
            avg_velocity = 0.0
        state = {
            'time': self.time,
            'power': power_output,
            'torque': torque,
            'base_buoy_force': base_buoy_force,
            'pulse_force': pulse_force,
            'total_vertical_force': total_vertical_force,
            'tau_net': tau_net,
            'tau_to_generator': tau_to_generator,
            'clutch_c': clutch_c,
            'clutch_state': clutch_state,
            'total_energy': self.total_energy,
            'pulse_count': self.pulse_count,
            'flywheel_speed_rpm': drivetrain_state['omega_flywheel_rpm'],
            'chain_speed_rpm': drivetrain_state['omega_chain_rpm'],
            'clutch_engaged': drivetrain_state['clutch_engaged'],
            'tank_pressure': self.pneumatics.tank_pressure,
            'overall_efficiency': overall_eff,
            'avg_floater_velocity': avg_velocity,
            'floaters': [f.to_dict() for f in self.floaters]        }
        
        # Include energy loss and net energy data
        state['drag_loss'] = drag_loss
        state['dissolution_loss'] = dissolution_loss
        state['venting_loss'] = venting_loss
        state['net_energy'] = net_energy        # Include enhanced loss model data (Phase 5)
        if enhanced_state is not None:
            state['enhanced_losses'] = {
                'total_system_losses': enhanced_state.system_losses.total_system_losses,
                'system_efficiency': enhanced_state.system_losses.system_efficiency,
                'mechanical_losses': {
                    'bearing_friction': enhanced_state.system_losses.mechanical_losses.bearing_friction,
                    'gear_mesh_losses': enhanced_state.system_losses.mechanical_losses.gear_mesh_losses,
                    'seal_friction': enhanced_state.system_losses.mechanical_losses.seal_friction,
                    'windage_losses': enhanced_state.system_losses.mechanical_losses.windage_losses,
                    'clutch_losses': enhanced_state.system_losses.mechanical_losses.clutch_losses,
                    'total_losses': enhanced_state.system_losses.mechanical_losses.total_losses
                },
                'electrical_losses': enhanced_state.system_losses.electrical_losses,
                'thermal_losses': enhanced_state.system_losses.thermal_losses
            }
            state['thermal_state'] = enhanced_state.performance_metrics
            state['component_temperatures'] = {
                name: thermal_state.temperature 
                for name, thermal_state in enhanced_state.thermal_states.items()
            }
        
        # Include control system data
        if control_output:
            state['control_mode'] = control_output.get('control_mode', 'normal')
            state['timing_commands'] = control_output.get('timing_commands', {})
            state['load_commands'] = control_output.get('load_commands', {})
            state['grid_commands'] = control_output.get('grid_commands', {})
            state['fault_status'] = control_output.get('fault_status', {})
            state['control_performance'] = control_output.get('performance_metrics', {})
            state['pneumatic_control_executed'] = pneumatic_executed
        
        # Include electrical system data
        if electrical_output:
            state['electrical_load_torque'] = electrical_output.get('load_torque_command', 0.0)
            state['grid_power_output'] = electrical_output.get('grid_power_output', 0.0)
            state['electrical_efficiency'] = electrical_output.get('system_efficiency', 0.0)
            state['electrical_synchronized'] = electrical_output.get('synchronized', False)
            state['electrical_load_factor'] = electrical_output.get('load_factor', 0.0)
            state['grid_voltage'] = electrical_output.get('grid_voltage', 480.0)
            state['grid_frequency'] = electrical_output.get('grid_frequency', 60.0)        
        # Include grid services data (Phase 7)
        if hasattr(self, '_last_grid_services_response'):
            state['grid_services'] = {
                'total_power_command_mw': self._last_grid_services_response.get('total_power_command_mw', 0.0),
                'active_services': self._last_grid_services_response.get('active_services', []),
                'service_count': self._last_grid_services_response.get('service_count', 0),
                'coordination_status': self._last_grid_services_response.get('status', 'No services active'),
                'frequency_services': self._last_grid_services_response.get('frequency_services', {}),
                'grid_conditions': getattr(self, '_last_grid_conditions', {})
            }
            
            # Include detailed grid services performance metrics
            grid_services_metrics = self.grid_services_coordinator.get_performance_metrics()
            state['grid_services_performance'] = grid_services_metrics
        else:
            # Grid services not yet active
            state['grid_services'] = {
                'total_power_command_mw': 0.0,
                'active_services': [],
                'service_count': 0,
                'coordination_status': 'Grid services not initialized',
                'frequency_services': {},
                'grid_conditions': {}
            }
        
        self.data_log.append(state)
        self.data_queue.put(state)
        logger.debug(f"Step: t={self.time:.2f}, power={power_output:.2f}, torque={torque:.2f}, base_buoy_force={base_buoy_force}, pulse_force={pulse_force}, clutch_c={clutch_c}, clutch_state={clutch_state}")

    def collect_state(self):
        """
        Return the latest simulation state.
        """
        if not self.data_log:
            return {}
        return self.data_log[-1]

    def start_thread(self):
        if not self.thread or not self.thread.is_alive():
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
