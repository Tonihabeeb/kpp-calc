import threading
from typing import Dict, Any, Optional

class StateManager:
    """
    Thread-safe state manager for simulation state.
    Provides safe access to the latest simulation state.
    """
    
    def __init__(self):
        """Initialize the state manager"""
        self.lock = threading.Lock()
        self._state = None
    
    def update_state(self, new_state: Dict[str, Any]):
        """Update the stored state thread-safely"""
        with self.lock:
            self._state = new_state.copy() if new_state else None
    
    def get_state(self) -> Optional[Dict[str, Any]]:
        """Get a copy of the current state thread-safely"""
        with self.lock:
            return self._state.copy() if self._state is not None else None

