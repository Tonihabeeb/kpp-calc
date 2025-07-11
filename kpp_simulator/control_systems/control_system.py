"""
Integrated Control System for KPP Simulator
Manages control systems and automation
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
import logging
from enum import Enum

class ControlMode(Enum):
    """Control system modes"""
    MANUAL = "manual"
    AUTOMATIC = "automatic"
    OPTIMIZATION = "optimization"
    EMERGENCY = "emergency"
    MAINTENANCE = "maintenance"

@dataclass
class ControlConfig:
    """Control system configuration"""
    update_rate: float = 100.0  # Hz
    response_time: float = 0.01  # seconds
    pid_gains: Dict[str, float] = field(default_factory=lambda: {
        'kp': 1.0,
        'ki': 0.1,
        'kd': 0.01
    })

@dataclass
class ControlState:
    """Control system state"""
    mode: ControlMode = ControlMode.MANUAL
    setpoint: float = 0.0
    measured_value: float = 0.0
    control_output: float = 0.0
    error: float = 0.0
    integral_error: float = 0.0
    derivative_error: float = 0.0
    last_update_time: float = 0.0

class IntegratedControlSystem:
    """
    Integrated Control System for KPP Simulator
    
    Features:
    - Multiple control modes
    - PID control implementation
    - Setpoint management
    - Performance monitoring
    - Safety interlocks
    """
    
    def __init__(self, config: Optional[ControlConfig] = None):
        """Initialize control system"""
        self.config = config or ControlConfig()
        self.state = ControlState()
        self.logger = logging.getLogger(__name__)
        
        # Performance tracking
        self.performance_metrics = {
            'total_updates': 0,
            'average_error': 0.0,
            'max_error': 0.0,
            'response_time': 0.0,
            'stability_index': 1.0
        }
        
        # Safety limits
        self.safety_limits = {
            'max_output': 1.0,
            'max_error': 0.5,
            'max_integral': 10.0,
            'max_derivative': 5.0
        }
        
        self.logger.info("Integrated Control System initialized")
    
    def update(self, measured_value: float, setpoint: float, time_step: float) -> float:
        """
        Update control system
        
        Args:
            measured_value: Current measured value
            setpoint: Target setpoint
            time_step: Time step in seconds
            
        Returns:
            Control output value
        """
        try:
            # Update state
            self.state.measured_value = measured_value
            self.state.setpoint = setpoint
            
            # Calculate error
            current_error = setpoint - measured_value
            
            # Update error tracking
            self.state.error = current_error
            self.state.integral_error += current_error * time_step
            if time_step > 0:
                self.state.derivative_error = (current_error - self.state.error) / time_step
            
            # Apply anti-windup to integral term
            self.state.integral_error = np.clip(
                self.state.integral_error,
                -self.safety_limits['max_integral'],
                self.safety_limits['max_integral']
            )
            
            # Calculate PID terms
            p_term = self.config.pid_gains['kp'] * current_error
            i_term = self.config.pid_gains['ki'] * self.state.integral_error
            d_term = self.config.pid_gains['kd'] * self.state.derivative_error
            
            # Calculate control output
            control_output = p_term + i_term + d_term
            
            # Apply output limits
            control_output = np.clip(
                control_output,
                -self.safety_limits['max_output'],
                self.safety_limits['max_output']
            )
            
            # Update state
            self.state.control_output = control_output
            self.state.last_update_time += time_step
            
            # Update metrics
            self._update_metrics(current_error, time_step)
            
            return control_output
            
        except Exception as e:
            self.logger.error(f"Control system update failed: {e}")
            return 0.0
    
    def set_mode(self, mode: ControlMode) -> bool:
        """Set control mode"""
        try:
            if mode == self.state.mode:
                return True
                
            # Validate mode transition
            if not self._validate_mode_transition(mode):
                return False
            
            # Update mode
            self.state.mode = mode
            
            # Reset state for mode change
            self._reset_state()
            
            self.logger.info(f"Control mode changed to: {mode.value}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to set control mode: {e}")
            return False
    
    def _validate_mode_transition(self, new_mode: ControlMode) -> bool:
        """Validate mode transition"""
        # Always allow transition to emergency mode
        if new_mode == ControlMode.EMERGENCY:
            return True
            
        # Validate specific transitions
        if self.state.mode == ControlMode.EMERGENCY:
            # Only allow transition to manual from emergency
            return new_mode == ControlMode.MANUAL
            
        if self.state.mode == ControlMode.MAINTENANCE:
            # Only allow transition to manual from maintenance
            return new_mode == ControlMode.MANUAL
            
        # All other transitions allowed
        return True
    
    def _reset_state(self):
        """Reset control state"""
        self.state.setpoint = 0.0
        self.state.control_output = 0.0
        self.state.error = 0.0
        self.state.integral_error = 0.0
        self.state.derivative_error = 0.0
    
    def _update_metrics(self, current_error: float, time_step: float):
        """Update performance metrics"""
        self.performance_metrics['total_updates'] += 1
        
        # Update error metrics
        abs_error = abs(current_error)
        self.performance_metrics['max_error'] = max(
            self.performance_metrics['max_error'],
            abs_error
        )
        
        # Update average error with exponential moving average
        alpha = 0.05  # Smoothing factor
        self.performance_metrics['average_error'] = (
            (1 - alpha) * self.performance_metrics['average_error'] +
            alpha * abs_error
        )
        
        # Update response time if error crosses zero
        if (self.state.error * current_error) < 0:
            self.performance_metrics['response_time'] = time_step
        
        # Update stability index
        if abs_error > self.safety_limits['max_error']:
            self.performance_metrics['stability_index'] *= 0.95
        else:
            self.performance_metrics['stability_index'] = min(
                1.0,
                self.performance_metrics['stability_index'] * 1.01
            )
    
    def get_state(self) -> Dict[str, Any]:
        """Get current control system state"""
        return {
            'mode': self.state.mode.value,
            'setpoint': self.state.setpoint,
            'measured_value': self.state.measured_value,
            'control_output': self.state.control_output,
            'error': self.state.error,
            'integral_error': self.state.integral_error,
            'derivative_error': self.state.derivative_error,
            'last_update_time': self.state.last_update_time
        }
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get performance metrics"""
        return self.performance_metrics.copy()
    
    def reset(self):
        """Reset control system"""
        self.state = ControlState()
        self.performance_metrics = {
            'total_updates': 0,
            'average_error': 0.0,
            'max_error': 0.0,
            'response_time': 0.0,
            'stability_index': 1.0
        }
        self.logger.info("Control system reset") 