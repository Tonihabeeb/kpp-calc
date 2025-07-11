"""
Integrated control system for KPP simulation.
Handles all control aspects including grid synchronization,
power regulation, and fault handling.
"""

import logging
from dataclasses import dataclass
from typing import Dict, Any, Optional

class ControlConfig:
    """Configuration for control system"""
    def __init__(self, **kwargs):
        self.max_power = kwargs.get('max_power', 50000.0)  # W
        self.max_speed = kwargs.get('max_speed', 2000.0)  # RPM
        self.target_frequency = kwargs.get('target_frequency', 50.0)  # Hz
        self.response_time_target = kwargs.get('response_time_target', 0.1)  # seconds
        self.optimization_enabled = kwargs.get('optimization_enabled', True)
        self.fault_tolerance = kwargs.get('fault_tolerance', 0.05)  # 5%
        self.pid_kp = kwargs.get('pid_kp', 1.0)
        self.pid_ki = kwargs.get('pid_ki', 0.1)
        self.pid_kd = kwargs.get('pid_kd', 0.01)
        self.grid_sync_tolerance = kwargs.get('grid_sync_tolerance', 0.02)  # 2%

@dataclass
class ControlState:
    """State of the control system"""
    power_setpoint: float
    current_power: float
    frequency: float
    is_grid_connected: bool
    optimization_active: bool
    faults: Dict[str, Any]
    mode: str
    status: str

class IntegratedControlSystem:
    """
    Integrated control system for KPP simulation.
    Handles power regulation, grid synchronization, and fault management.
    """
    
    def __init__(self, config: ControlConfig):
        """Initialize control system with configuration"""
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Operating state
        self.power_setpoint = 0.0
        self.current_power = 0.0
        self.frequency = config.target_frequency
        self.is_grid_connected = False
        self.optimization_active = config.optimization_enabled
        
        # Control mode
        self.mode = "STANDBY"  # STANDBY, STARTUP, RUNNING, SHUTDOWN, FAULT
        self.status = "READY"
        
        # Fault tracking
        self.faults = {}
        
        # PID control
        self.pid_error_sum = 0.0
        self.pid_last_error = 0.0
        
        self.logger.info("Integrated control system initialized")
    
    def get_state(self) -> ControlState:
        """Get current control system state"""
        return ControlState(
            power_setpoint=self.power_setpoint,
            current_power=self.current_power,
            frequency=self.frequency,
            is_grid_connected=self.is_grid_connected,
            optimization_active=self.optimization_active,
            faults=self.faults.copy(),
            mode=self.mode,
            status=self.status
        )
    
    def update(self, time_step: float, system_state: Any) -> None:
        """
        Update control system state.
        
        Args:
            time_step: Time step in seconds
            system_state: Current system state
        """
        try:
            # Update power tracking
            if system_state.total_power is not None:
                self.current_power = system_state.total_power
            
            # PID control for power regulation
            error = self.power_setpoint - self.current_power
            
            # Proportional term
            p_term = self.config.pid_kp * error
            
            # Integral term
            self.pid_error_sum += error * time_step
            i_term = self.config.pid_ki * self.pid_error_sum
            
            # Derivative term
            d_term = self.config.pid_kd * (error - self.pid_last_error) / time_step
            self.pid_last_error = error
            
            # Combined control output
            control_output = p_term + i_term + d_term
            
            # Apply control limits
            control_output = max(-self.config.max_power, min(control_output, self.config.max_power))
            
            # Update frequency based on power balance
            if self.is_grid_connected:
                self.frequency = self.config.target_frequency
            else:
                # Simplified frequency calculation
                nominal_power = self.config.max_power
                freq_deviation = (self.current_power - nominal_power) / nominal_power
                self.frequency = self.config.target_frequency * (1 + freq_deviation * self.config.grid_sync_tolerance)
            
            # Check for faults
            self._check_faults(system_state)
            
            # Update mode based on conditions
            self._update_mode(system_state)
            
        except Exception as e:
            self.logger.error(f"Error in control system update: {e}")
            self.faults["control_error"] = str(e)
            self.mode = "FAULT"
    
    def _check_faults(self, system_state: Any) -> None:
        """Check for system faults"""
        # Clear old faults
        self.faults.clear()
        
        # Check power limits
        if abs(self.current_power) > self.config.max_power * (1 + self.config.fault_tolerance):
            self.faults["power_limit"] = f"Power exceeds limit: {self.current_power:.2f} W"
        
        # Check frequency
        if abs(self.frequency - self.config.target_frequency) > self.config.target_frequency * self.config.grid_sync_tolerance:
            self.faults["frequency"] = f"Frequency deviation: {self.frequency:.2f} Hz"
        
        # Check component faults
        if hasattr(system_state, 'errors') and system_state.errors:
            for error in system_state.errors:
                self.faults[f"component_{error.component}"] = error.message
    
    def _update_mode(self, system_state: Any) -> None:
        """Update control mode based on system state"""
        if self.faults:
            self.mode = "FAULT"
            return
        
        if self.mode == "STANDBY":
            if self.power_setpoint > 0:
                self.mode = "STARTUP"
        
        elif self.mode == "STARTUP":
            if self.current_power >= self.power_setpoint * 0.9:  # 90% of setpoint
                self.mode = "RUNNING"
        
        elif self.mode == "RUNNING":
            if self.power_setpoint <= 0:
                self.mode = "SHUTDOWN"
        
        elif self.mode == "SHUTDOWN":
            if self.current_power <= 0:
                self.mode = "STANDBY"
    
    def set_power_setpoint(self, setpoint: float) -> None:
        """Set power setpoint"""
        self.power_setpoint = max(0, min(setpoint, self.config.max_power))
    
    def connect_to_grid(self) -> bool:
        """Attempt to connect to grid"""
        if abs(self.frequency - self.config.target_frequency) <= self.config.target_frequency * self.config.grid_sync_tolerance:
            self.is_grid_connected = True
            return True
        return False
    
    def disconnect_from_grid(self) -> None:
        """Disconnect from grid"""
        self.is_grid_connected = False
    
    def reset(self) -> None:
        """Reset control system state"""
        self.power_setpoint = 0.0
        self.current_power = 0.0
        self.frequency = self.config.target_frequency
        self.is_grid_connected = False
        self.mode = "STANDBY"
        self.faults.clear()
        self.pid_error_sum = 0.0
        self.pid_last_error = 0.0

