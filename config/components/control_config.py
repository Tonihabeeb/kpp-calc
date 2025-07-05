"""
Control system configuration for the KPP simulator.
"""

from dataclasses import dataclass, field
from ..core.base_config import BaseConfig

@dataclass
class ControlConfig(BaseConfig):
    """Configuration for control system parameters"""
    
    # System parameters
    num_floaters: int = field(default=8)
    
    # PID parameters
    kp: float = field(default=100.0)
    ki: float = field(default=10.0)
    kd: float = field(default=5.0)
    
    # Control limits
    max_velocity: float = field(default=10.0)
    max_acceleration: float = field(default=20.0)
    
    # Safety parameters
    emergency_stop_velocity: float = field(default=15.0)
    position_tolerance: float = field(default=0.1)
    
    # Timing parameters
    control_update_rate: float = field(default=100.0)
    safety_check_interval: float = field(default=0.01)
    
    # Thresholds
    min_engagement_velocity: float = field(default=0.5)
    max_position_error: float = field(default=1.0)
    
    # Emergency response
    emergency_stop_enabled: bool = field(default=True)
    emergency_stop_deceleration: float = field(default=50.0)
    
    def get_control_gains(self) -> dict:
        """Get PID control gains"""
        return {
            'kp': self.kp,
            'ki': self.ki,
            'kd': self.kd
        }
    
    def should_engage_control(self, velocity: float, position_error: float) -> bool:
        """Determine if control system should engage"""
        return (abs(velocity) >= self.min_engagement_velocity and 
                abs(position_error) <= self.max_position_error)
    
    def should_emergency_stop(self, velocity: float) -> bool:
        """Determine if emergency stop should be triggered"""
        return (self.emergency_stop_enabled and 
                abs(velocity) > self.emergency_stop_velocity)
    
    def get_control_update_period(self) -> float:
        """Get control update period in seconds"""
        return 1.0 / self.control_update_rate 