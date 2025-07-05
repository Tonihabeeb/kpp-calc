"""
State machine for floater operation cycles.
Manages transitions between empty, filling, full, and venting states.
"""

import logging
from enum import Enum
from typing import Optional, Callable
from dataclasses import dataclass

logger = logging.getLogger(__name__)

class FloaterState(Enum):
    """Floater operational states"""
    EMPTY = "empty"
    FILLING = "filling"
    FULL = "full"
    VENTING = "venting"
    TRANSITION = "transition"

@dataclass
class StateTransition:
    """Represents a state transition"""
    from_state: FloaterState
    to_state: FloaterState
    condition: Callable
    action: Optional[Callable] = None

class FloaterStateMachine:
    """Manages floater state transitions"""
    
    def __init__(self):
        self.current_state = FloaterState.EMPTY
        self.transitions = self._define_transitions()
        self.state_history = []
    
    def _define_transitions(self) -> list[StateTransition]:
        """Define all possible state transitions"""
        return [
            StateTransition(
                FloaterState.EMPTY,
                FloaterState.FILLING,
                lambda context: context.get('injection_requested', False),
                self._on_start_filling
            ),
            StateTransition(
                FloaterState.FILLING,
                FloaterState.FULL,
                lambda context: context.get('injection_complete', False),
                self._on_filling_complete
            ),
            StateTransition(
                FloaterState.FULL,
                FloaterState.VENTING,
                lambda context: context.get('venting_requested', False),
                self._on_start_venting
            ),
            StateTransition(
                FloaterState.VENTING,
                FloaterState.EMPTY,
                lambda context: context.get('venting_complete', False),
                self._on_venting_complete
            )
        ]
    
    def update(self, context: dict) -> FloaterState:
        """Update state machine based on current context"""
        old_state = self.current_state
        
        # Check for valid transitions
        for transition in self.transitions:
            if (transition.from_state == self.current_state and 
                transition.condition(context)):
                
                # Execute transition
                if transition.action:
                    transition.action(context)
                
                self.current_state = transition.to_state
                self.state_history.append({
                    'from_state': old_state,
                    'to_state': self.current_state,
                    'timestamp': context.get('time', 0.0)
                })
                
                logger.info(f"Floater state transition: {old_state} -> {self.current_state}")
                break
        
        return self.current_state
    
    def _on_start_filling(self, context: dict) -> None:
        """Action when starting to fill"""
        logger.debug("Starting air injection")
    
    def _on_filling_complete(self, context: dict) -> None:
        """Action when filling is complete"""
        logger.debug("Air injection completed")
    
    def _on_start_venting(self, context: dict) -> None:
        """Action when starting to vent"""
        logger.debug("Starting air venting")
    
    def _on_venting_complete(self, context: dict) -> None:
        """Action when venting is complete"""
        logger.debug("Air venting completed")
    
    def get_state_info(self) -> dict:
        """Get current state information"""
        return {
            'current_state': self.current_state.value,
            'state_history': self.state_history[-10:],  # Last 10 transitions
            'total_transitions': len(self.state_history)
        }
    
    def reset(self) -> None:
        """Reset state machine to initial state"""
        self.current_state = FloaterState.EMPTY
        self.state_history = []
