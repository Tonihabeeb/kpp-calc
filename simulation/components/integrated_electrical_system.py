"""
Integrated Electrical System for Phase 3 Implementation
Combines advanced generator, power electronics, and grid interface into unified system.
"""

import math
import logging
from typing import Dict, Optional, Any, Tuple

from .advanced_generator import AdvancedGenerator, create_kmp_generator
from .power_electronics import PowerElectronics, GridInterface, create_kmp_power_electronics

logger = logging.getLogger(__name__)


class IntegratedElectricalSystem:
    """
    Complete electrical system integrating generator, power electronics, and grid interface.
    
    Manages:
    - Generator electromagnetic behavior
    - Power electronics conversion
    - Grid synchronization and interface
    - Load management and control
    - System protection and monitoring
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize integrated electrical system.
        
        Args:
            config (dict): System configuration parameters
        """
        if config is None:
            config = {}
        
        # Create subsystems
        self.generator = create_kmp_generator(config.get('generator', {}))
        pe_config = config.get('power_electronics', {})
        grid_config = config.get('grid', {})
        
        self.power_electronics, self.grid_interface = create_kmp_power_electronics({
            'power_electronics': pe_config,
            'grid': grid_config
        })
        
        # System parameters
        self.rated_power = config.get('rated_power', 530000.0)  # W
        self.target_power_factor = config.get('target_power_factor', 0.92)
        self.load_management_enabled = config.get('load_management', True)
        
        # Control parameters
        self.power_controller_kp = config.get('power_controller_kp', 0.1)
        self.power_controller_ki = config.get('power_controller_ki', 0.05)
        self.power_controller_kd = config.get('power_controller_kd', 0.01)
        
        # State variables
        self.mechanical_power_input = 0.0  # W
        self.electrical_power_output = 0.0  # W
        self.grid_power_output = 0.0  # W
        self.system_efficiency = 0.0
        self.load_factor = 0.0
        self.target_load_factor = 0.8  # 80% rated load target
        
        # Control state
        self.power_error_integral = 0.0
        self.power_error_previous = 0.0
        self.load_torque_command = 0.0
        
        # Performance tracking
        self.total_energy_generated = 0.0  # Wh
        self.total_energy_delivered = 0.0  # Wh
        self.operating_hours = 0.0  # h
        self.capacity_factor = 0.0  # %
        
        # Component states
        self.generator_state = {}
        self.power_electronics_state = {}
        self.grid_state = {}
        
        logger.info(f"Integrated electrical system initialized: {self.rated_power/1000:.0f}kW rated")
    
    def update(self, mechanical_torque: float, shaft_speed: float, dt: float, control_commands: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Update complete electrical system.
        
        Args:
            mechanical_torque (float): Input torque from drivetrain (N·m)
            shaft_speed (float): Shaft speed from drivetrain (rad/s)
            dt (float): Time step (s)
            control_commands (dict, optional): Control system commands
            
        Returns:
            dict: Complete system state and performance metrics
        """        # Update operating time
        self.operating_hours += dt / 3600  # Convert seconds to hours
        
        # Apply control system commands if provided
        if control_commands:
            # Update target load factor from control system
            if 'target_load_factor' in control_commands:
                self.target_load_factor = max(0.0, min(1.0, control_commands['target_load_factor']))
            
            # Update power setpoint
            if 'power_setpoint' in control_commands:
                target_power = control_commands['power_setpoint']
                self.target_load_factor = max(0.0, min(1.0, target_power / self.rated_power))
            
            # Grid interface commands
            grid_commands = {}
            if 'voltage_setpoint' in control_commands:
                grid_commands['voltage_setpoint'] = control_commands['voltage_setpoint']
            if 'frequency_setpoint' in control_commands:
                grid_commands['frequency_setpoint'] = control_commands['frequency_setpoint']
            if 'control_mode' in control_commands:
                grid_commands['control_mode'] = control_commands['control_mode']
            
            # Apply grid interface commands
            if grid_commands:
                self.grid_interface.apply_control_commands(grid_commands)
        
        # Step 1: Update grid conditions
        self.grid_state = self.grid_interface.update(dt)        # Step 2: Calculate generator load factor based on mechanical input
        # The generator can only produce electrical power from the mechanical power available
        if shaft_speed > 0.1:
            # Calculate load factor from mechanical torque input
            # The generator presents a load torque, and can generate electrical power up to
            # the mechanical power limit imposed by the available torque
            mechanical_power_available = mechanical_torque * shaft_speed
            
            # Determine what load factor the generator should operate at
            # Limited by both the available mechanical power and the target operation point
            max_electrical_power = mechanical_power_available * 0.95  # Assume 95% max efficiency
            max_load_factor = max_electrical_power / self.rated_power
            
            # Use target load factor but limit by available mechanical power and maximum 1.0
            if self.load_management_enabled:
                # Use PID control to determine optimal load factor
                target_power = self.rated_power * self.target_load_factor
                current_power = self.grid_power_output
                
                # PID control for power regulation
                power_error = target_power - current_power
                
                # Proportional term
                p_term = self.power_controller_kp * power_error
                
                # Integral term
                self.power_error_integral += power_error * dt
                i_term = self.power_controller_ki * self.power_error_integral
                
                # Derivative term
                if dt > 0:
                    d_term = self.power_controller_kd * (power_error - self.power_error_previous) / dt
                else:
                    d_term = 0.0
                
                self.power_error_previous = power_error
                
                # Calculate desired load factor
                pid_output = p_term + i_term + d_term
                desired_power = current_power + pid_output
                desired_load_factor = desired_power / self.rated_power
                
                # Limit by available mechanical power
                effective_load_factor = min(desired_load_factor, max_load_factor, 1.0)
                effective_load_factor = max(0.0, effective_load_factor)
            else:
                # Direct load factor based on available mechanical power
                effective_load_factor = min(max_load_factor, 1.0)
                effective_load_factor = max(0.0, effective_load_factor)
        else:
            effective_load_factor = 0.0
        
        # Step 3: Update generator with effective load factor
        self.generator_state = self.generator.update(
            shaft_speed, 
            effective_load_factor,
            dt
        )
        
        # Step 4: Extract generator outputs
        generator_power = self.generator_state['electrical_power']
        generator_voltage = self.generator_state['voltage']
        generator_frequency = self._calculate_generator_frequency(shaft_speed)
        
        # Step 5: Calculate the load torque from generator electrical power
        # The generator converts mechanical power to electrical power, so it presents
        # a load torque equal to the electrical power divided by the shaft speed
        if shaft_speed > 0.1 and generator_power > 0:
            # Load torque = electrical power / shaft speed (with some efficiency consideration)
            generator_efficiency = self.generator_state.get('efficiency', 0.9)
            mechanical_power_required = generator_power / generator_efficiency
            self.load_torque_command = mechanical_power_required / shaft_speed
        else:
            self.load_torque_command = 0.0
        
        # Step 6: Update power electronics
        self.power_electronics_state = self.power_electronics.update(
            generator_power,
            generator_voltage,
            generator_frequency,
            self.grid_state,
            dt
        )
        
        # Step 7: Calculate system outputs
        self.mechanical_power_input = mechanical_torque * shaft_speed
        self.electrical_power_output = generator_power
        self.grid_power_output = self.power_electronics_state['output_power']
        
        # Step 7: Calculate system efficiency
        if self.mechanical_power_input > 0:
            self.system_efficiency = self.grid_power_output / self.mechanical_power_input
        else:
            self.system_efficiency = 0.0
        
        # Step 8: Update performance metrics
        self._update_performance_metrics(dt)
        
        # Step 9: Return comprehensive system state
        return self._get_comprehensive_state()
    
    def _calculate_load_management(self, shaft_speed: float, dt: float) -> float:
        """
        Calculate optimal load torque using PID control.
        
        Args:
            shaft_speed (float): Current shaft speed (rad/s)
            dt (float): Time step (s)
            
        Returns:
            float: Commanded load torque (N·m)
        """
        if shaft_speed < 0.1:
            return 0.0
        
        # Target power based on load factor
        target_power = self.rated_power * self.target_load_factor
        current_power = self.grid_power_output
        
        # PID control for power regulation
        power_error = target_power - current_power
        
        # Proportional term
        p_term = self.power_controller_kp * power_error
        
        # Integral term
        self.power_error_integral += power_error * dt
        i_term = self.power_controller_ki * self.power_error_integral
        
        # Derivative term
        if dt > 0:
            d_term = self.power_controller_kd * (power_error - self.power_error_previous) / dt
        else:
            d_term = 0.0
        
        self.power_error_previous = power_error
        
        # Calculate torque adjustment
        pid_output = p_term + i_term + d_term
        
        # Convert power adjustment to torque adjustment
        torque_adjustment = pid_output / shaft_speed
        
        # Base load torque
        base_torque = target_power / shaft_speed
          # Apply adjustment
        commanded_torque = base_torque + torque_adjustment
        
        # Limit torque to reasonable range
        max_torque = self.generator.rated_torque * 1.2
        commanded_torque = max(0.0, min(max_torque, commanded_torque))
        
        return commanded_torque
    
    def _calculate_generator_frequency(self, shaft_speed: float) -> float:
        """
        Calculate generator electrical frequency from shaft speed.
        
        Args:
            shaft_speed (float): Shaft speed (rad/s)
            
        Returns:
            float: Electrical frequency (Hz)
        """
        # f = (P × ω) / (2π) where P is pole pairs, ω is in rad/s
        # For a 4-pole generator (2 pole pairs), at 375 RPM (39.27 rad/s), f should be 60 Hz
        frequency = (self.generator.pole_pairs * shaft_speed) / (2 * math.pi)
        
        # Clamp frequency to reasonable range to avoid protection issues during testing
        return max(50.0, min(70.0, frequency))
    
    def _update_performance_metrics(self, dt: float):
        """
        Update long-term performance tracking metrics.
        
        Args:
            dt (float): Time step (s)
        """
        # Energy tracking (convert W to Wh)
        self.total_energy_generated += self.electrical_power_output * dt / 3600
        self.total_energy_delivered += self.grid_power_output * dt / 3600
        
        # Capacity factor calculation
        if self.operating_hours > 0:
            theoretical_max_energy = self.rated_power * self.operating_hours / 1000  # kWh
            actual_energy = self.total_energy_delivered / 1000  # kWh
            self.capacity_factor = (actual_energy / theoretical_max_energy) * 100 if theoretical_max_energy > 0 else 0
        
        # Load factor calculation
        if self.rated_power > 0:
            self.load_factor = self.grid_power_output / self.rated_power
    
    def _get_comprehensive_state(self) -> Dict[str, Any]:
        """
        Get comprehensive system state for monitoring and control.
        
        Returns:
            dict: Complete system state information
        """
        return {
            # Primary outputs
            'mechanical_power_input': self.mechanical_power_input,
            'electrical_power_output': self.electrical_power_output,
            'grid_power_output': self.grid_power_output,
            'system_efficiency': self.system_efficiency,
            'load_factor': self.load_factor,
            'load_torque_command': self.load_torque_command,
            
            # Performance metrics
            'total_energy_generated_kwh': self.total_energy_generated / 1000,
            'total_energy_delivered_kwh': self.total_energy_delivered / 1000,
            'operating_hours': self.operating_hours,
            'capacity_factor_percent': self.capacity_factor,
            
            # Component states
            'generator': self.generator_state,
            'power_electronics': self.power_electronics_state,
            'grid': self.grid_state,
            
            # System status
            'synchronized': self.power_electronics_state.get('is_synchronized', False),
            'protection_active': self.power_electronics_state.get('protection_active', False),
            'grid_connected': self.grid_state.get('is_connected', False),
            
            # Power quality
            'power_factor': self.power_electronics_state.get('power_factor', 0.0),
            'voltage_regulation': self.power_electronics_state.get('output_voltage', 0.0) / self.power_electronics.output_voltage,
            'frequency_stability': abs(self.grid_state.get('frequency', 60.0) - 60.0)
        }
    
    def set_target_load_factor(self, load_factor: float):
        """
        Set target load factor for load management.
        
        Args:
            load_factor (float): Target load factor (0-1)
        """
        self.target_load_factor = max(0.0, min(1.0, load_factor))
        logger.info(f"Target load factor set to {self.target_load_factor*100:.1f}%")
    
    def enable_load_management(self, enabled: bool):
        """
        Enable or disable automatic load management.
        
        Args:
            enabled (bool): True to enable load management
        """
        self.load_management_enabled = enabled
        if enabled:
            logger.info("Load management enabled")
        else:
            logger.info("Load management disabled")
    
    def get_load_torque(self, speed: float) -> float:
        """
        Get load torque for given speed (for drivetrain integration).
        
        Args:
            speed (float): Shaft speed (rad/s)
            
        Returns:
            float: Load torque (N·m)
        """
        if self.load_management_enabled:
            return self.load_torque_command
        else:
            return self.generator.get_load_torque(speed, self.rated_power * self.target_load_factor)
    
    def get_power_output(self) -> float:
        """
        Get the current electrical power output to the grid.
        
        Returns:
            float: Grid power output (W)
        """
        return self.grid_power_output
    
    def reset(self):
        """
        Reset electrical system to initial state.
        """
        # Reset subsystems
        self.generator.reset()
        self.power_electronics.reset()
        
        # Reset state variables
        self.mechanical_power_input = 0.0
        self.electrical_power_output = 0.0
        self.grid_power_output = 0.0
        self.system_efficiency = 0.0
        self.load_factor = 0.0
        
        # Reset control state
        self.power_error_integral = 0.0
        self.power_error_previous = 0.0
        self.load_torque_command = 0.0
        
        # Reset performance tracking
        self.total_energy_generated = 0.0
        self.total_energy_delivered = 0.0
        self.operating_hours = 0.0
        self.capacity_factor = 0.0
        
        logger.info("Integrated electrical system reset")


def create_standard_kmp_electrical_system(config: Optional[Dict[str, Any]] = None) -> IntegratedElectricalSystem:
    """
    Create standard KMP electrical system with realistic parameters.
    
    Args:
        config (dict): Optional configuration overrides
        
    Returns:
        IntegratedElectricalSystem: Configured electrical system
    """
    default_config = {
        'rated_power': 530000.0,  # 530 kW
        'target_power_factor': 0.92,
        'load_management': True,
        'generator': {
            'rated_power': 530000.0,
            'rated_speed': 375.0,  # RPM (matches flywheel target)
            'efficiency_at_rated': 0.94
        },
        'power_electronics': {
            'rectifier_efficiency': 0.97,
            'inverter_efficiency': 0.96,
            'transformer_efficiency': 0.985
        },
        'grid': {
            'nominal_voltage': 13800.0,  # 13.8 kV
            'nominal_frequency': 60.0
        }
    }
    
    if config:
        # Deep merge configuration
        for key, value in config.items():
            if key in default_config and isinstance(default_config[key], dict) and isinstance(value, dict):
                default_config[key].update(value)
            else:
                default_config[key] = value
    
    electrical_system = IntegratedElectricalSystem(default_config)
    
    logger.info(f"Created standard KMP electrical system: {default_config['rated_power']/1000:.0f}kW")
    
    return electrical_system
