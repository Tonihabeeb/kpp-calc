"""
Periodic control strategy for basic operation.
"""

from typing import Dict, Any, List
from .base_strategy import ControlStrategy

class PeriodicStrategy(ControlStrategy):
    """Periodic control strategy with fixed timing"""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize periodic strategy"""
        super().__init__(config)
        self.injection_interval = config.get('injection_interval', 2.0)
        self.floater_count = config.get('floater_count', 10)
        self.current_floater = 0
        self.last_injection_time = 0.0
        
    def get_actions(self, current_speed: float, current_time: float) -> List[Dict[str, Any]]:
        """Get periodic control actions"""
        actions = []
        
        # Check if it's time for next injection
        if current_time - self.last_injection_time >= self.injection_interval:
            actions.append({
                'type': 'inject_floater',
                'floater_id': self.current_floater
            })
            
            # Update for next injection
            self.current_floater = (self.current_floater + 1) % self.floater_count
            self.last_injection_time = current_time
            
        return actions
        
    def get_strategy_name(self) -> str:
        """Get strategy name"""
        return 'periodic'
