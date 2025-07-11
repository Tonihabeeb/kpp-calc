"""
Base class for control strategies.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List

class ControlStrategy(ABC):
    """Abstract base class for control strategies"""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize strategy"""
        self.config = config
        
    @abstractmethod
    def get_actions(self, current_speed: float, current_time: float) -> List[Dict[str, Any]]:
        """Get control actions based on current state"""
        pass
        
    @abstractmethod
    def get_strategy_name(self) -> str:
        """Get strategy name"""
        pass
