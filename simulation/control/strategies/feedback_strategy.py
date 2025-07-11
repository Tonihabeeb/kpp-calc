"""
Feedback control strategy with speed regulation.
"""

from typing import Dict, Any, List
from .base_strategy import ControlStrategy

class FeedbackStrategy(ControlStrategy):
    """Feedback control strategy with PID-like control"""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize feedback strategy"""
        super().__init__(config)
        self.target_speed = config.get('target_speed', 50.0)
        self.injection_interval = config.get('injection_interval', 2.0)
        self.floater_count = config.get('floater_count', 10)
        
        # PID-like parameters
        self.kp = config.get('kp', 0.1)  # Proportional gain
        self.ki = config.get('ki', 0.01)  # Integral gain
        self.kd = config.get('kd', 0.001)  # Derivative gain
        
        # Control state
        self.current_floater = 0
        self.last_injection_time = 0.0
        self.speed_error_integral = 0.0
        self.last_speed_error = 0.0
        
    def get_actions(self, current_speed: float, current_time: float) -> List[Dict[str, Any]]:
        """Get feedback control actions"""
        actions = []
        
        # Calculate speed error
        speed_error = self.target_speed - current_speed
        
        # PID-like control
        self.speed_error_integral += speed_error * 0.1  # dt = 0.1s
        speed_error_derivative = (speed_error - self.last_speed_error) / 0.1
        
        # Control output
        control_output = (self.kp * speed_error + 
                         self.ki * self.speed_error_integral + 
                         self.kd * speed_error_derivative)
        
        # Determine injection timing based on control output
        base_interval = self.injection_interval
        adjusted_interval = base_interval * (1.0 - control_output * 0.1)  # Adjust by ±10%
        adjusted_interval = max(0.5, min(5.0, adjusted_interval))  # Limit range
        
        # Check if it's time for injection
        if current_time - self.last_injection_time >= adjusted_interval:
            actions.append({
                'type': 'inject_floater',
                'floater_id': self.current_floater
            })
            
            # Update for next injection
            self.current_floater = (self.current_floater + 1) % self.floater_count
            self.last_injection_time = current_time
            
        # Update error tracking
        self.last_speed_error = speed_error
        
        return actions
        
    def get_strategy_name(self) -> str:
        """Get strategy name"""
        return 'feedback'
