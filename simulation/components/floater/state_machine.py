import logging
import time
from typing import Callable, Optional, Dict, List, Any
from enum import Enum
from dataclasses import dataclass
"""
State machine for floater operation cycles.
Manages transitions between empty, filling, full, and venting states.
"""

class FloaterState(str, Enum):
    """Floater state enumeration"""
    EMPTY = "empty"
    FILLING = "filling"
    FULL = "full"
    VENTING = "venting"
    ERROR = "error"
    MAINTENANCE = "maintenance"

class StateTransitionEvent(str, Enum):
    """State transition event types"""
    INJECTION_START = "injection_start"
    INJECTION_COMPLETE = "injection_complete"
    VENTING_START = "venting_start"
    VENTING_COMPLETE = "venting_complete"
    ERROR_DETECTED = "error_detected"
    MAINTENANCE_START = "maintenance_start"
    MAINTENANCE_COMPLETE = "maintenance_complete"
    RESET = "reset"

@dataclass
class StateTransition:
    """State transition data"""
    from_state: FloaterState
    to_state: FloaterState
    event: StateTransitionEvent
    timestamp: float
    conditions_met: bool
    error_message: Optional[str] = None

@dataclass
class StateMachineConfig:
    """State machine configuration"""
    min_fill_level: float = 0.95  # 95% full threshold
    max_fill_level: float = 1.0   # 100% full threshold
    min_empty_level: float = 0.05  # 5% empty threshold
    max_empty_level: float = 0.0   # 0% empty threshold
    transition_timeout: float = 30.0  # seconds
    error_threshold: int = 3  # consecutive errors before ERROR state

class FloaterStateMachine:
    """
    State machine for floater operation cycles.
    Manages state transitions, event handling, and state persistence.
    """
    
    def __init__(self, config: Optional[StateMachineConfig] = None):
        """
        Initialize the state machine.
        
        Args:
            config: State machine configuration
        """
        self.config = config or StateMachineConfig()
        self.logger = logging.getLogger(__name__)
        
        # Current state
        self.current_state = FloaterState.EMPTY
        self.previous_state = FloaterState.EMPTY
        
        # State tracking
        self.state_history: List[StateTransition] = []
        self.state_start_time = time.time()
        self.state_duration = 0.0
        
        # Performance metrics
        self.performance_metrics = {
            'total_transitions': 0,
            'successful_transitions': 0,
            'failed_transitions': 0,
            'average_cycle_time': 0.0,
            'error_count': 0,
            'maintenance_count': 0
        }
        
        # Event handlers
        self.event_handlers: Dict[StateTransitionEvent, List[Callable]] = {
            event: [] for event in StateTransitionEvent
        }
        
        # Error tracking
        self.consecutive_errors = 0
        self.last_error_time = 0.0
        self.error_messages: List[str] = []
        
        # Transition conditions
        self.transition_conditions = {
            (FloaterState.EMPTY, FloaterState.FILLING): self._can_transition_to_filling,
            (FloaterState.FILLING, FloaterState.FULL): self._can_transition_to_full,
            (FloaterState.FULL, FloaterState.VENTING): self._can_transition_to_venting,
            (FloaterState.VENTING, FloaterState.EMPTY): self._can_transition_to_empty,
            (FloaterState.ERROR, FloaterState.EMPTY): self._can_transition_from_error,
            (FloaterState.MAINTENANCE, FloaterState.EMPTY): self._can_transition_from_maintenance
        }
        
        self.logger.info("State machine initialized with state: %s", self.current_state)
    
    def register_event_handler(self, event: StateTransitionEvent, handler: Callable) -> None:
        """
        Register an event handler.
        
        Args:
            event: Event type to handle
            handler: Handler function
        """
        if event in self.event_handlers:
            self.event_handlers[event].append(handler)
            self.logger.debug("Registered handler for event: %s", event)
    
    def trigger_event(self, event: StateTransitionEvent, **kwargs) -> bool:
        """
        Trigger a state transition event.
        
        Args:
            event: Event to trigger
            **kwargs: Additional event data
            
        Returns:
            True if transition successful, False otherwise
        """
        try:
            self.logger.debug("Triggering event: %s", event)
            
            # Determine target state based on event
            target_state = self._get_target_state(event)
            
            if target_state is None:
                self.logger.warning("No target state for event: %s", event)
                return False
            
            # Check if transition is valid
            if not self._is_valid_transition(self.current_state, target_state):
                self.logger.warning("Invalid transition: %s -> %s", self.current_state, target_state)
                return False
            
            # Check transition conditions
            if not self._check_transition_conditions(self.current_state, target_state, **kwargs):
                self.logger.warning("Transition conditions not met: %s -> %s", self.current_state, target_state)
                return False
            
            # Perform transition
            success = self._perform_transition(target_state, event, **kwargs)
            
            if success:
                # Call event handlers
                self._call_event_handlers(event, **kwargs)
            
            return success
            
        except Exception as e:
            self.logger.error("Error triggering event %s: %s", event, e)
            self._handle_error(f"event_trigger_error: {str(e)}")
            return False
    
    def _get_target_state(self, event: StateTransitionEvent) -> Optional[FloaterState]:
        """
        Get target state for an event.
        
        Args:
            event: Event type
            
        Returns:
            Target state or None if no valid target
        """
        event_to_state = {
            StateTransitionEvent.INJECTION_START: FloaterState.FILLING,
            StateTransitionEvent.INJECTION_COMPLETE: FloaterState.FULL,
            StateTransitionEvent.VENTING_START: FloaterState.VENTING,
            StateTransitionEvent.VENTING_COMPLETE: FloaterState.EMPTY,
            StateTransitionEvent.ERROR_DETECTED: FloaterState.ERROR,
            StateTransitionEvent.MAINTENANCE_START: FloaterState.MAINTENANCE,
            StateTransitionEvent.MAINTENANCE_COMPLETE: FloaterState.EMPTY,
            StateTransitionEvent.RESET: FloaterState.EMPTY
        }
        
        return event_to_state.get(event)
    
    def _is_valid_transition(self, from_state: FloaterState, to_state: FloaterState) -> bool:
        """
        Check if a transition is valid.
        
        Args:
            from_state: Current state
            to_state: Target state
            
        Returns:
            True if transition is valid
        """
        valid_transitions = {
            FloaterState.EMPTY: [FloaterState.FILLING, FloaterState.MAINTENANCE],
            FloaterState.FILLING: [FloaterState.FULL, FloaterState.EMPTY, FloaterState.ERROR],
            FloaterState.FULL: [FloaterState.VENTING, FloaterState.ERROR],
            FloaterState.VENTING: [FloaterState.EMPTY, FloaterState.ERROR],
            FloaterState.ERROR: [FloaterState.EMPTY, FloaterState.MAINTENANCE],
            FloaterState.MAINTENANCE: [FloaterState.EMPTY]
        }
        
        return to_state in valid_transitions.get(from_state, [])
    
    def _check_transition_conditions(self, from_state: FloaterState, to_state: FloaterState, **kwargs) -> bool:
        """
        Check if transition conditions are met.
        
        Args:
            from_state: Current state
            to_state: Target state
            **kwargs: Additional data for condition checking
            
        Returns:
            True if conditions are met
        """
        transition_key = (from_state, to_state)
        
        if transition_key in self.transition_conditions:
            return self.transition_conditions[transition_key](**kwargs)
        
        return True  # Default to allowing transition
    
    def _perform_transition(self, target_state: FloaterState, event: StateTransitionEvent, **kwargs) -> bool:
        """
        Perform the state transition.
        
        Args:
            target_state: Target state
            event: Triggering event
            **kwargs: Additional event data
            
        Returns:
            True if transition successful
        """
        try:
            # Update state duration
            current_time = time.time()
            self.state_duration = current_time - self.state_start_time
            
            # Create transition record
            transition = StateTransition(
                from_state=self.current_state,
                to_state=target_state,
                event=event,
                timestamp=current_time,
                conditions_met=True
            )
            
            # Update state
            self.previous_state = self.current_state
            self.current_state = target_state
            self.state_start_time = current_time
            
            # Add to history
            self.state_history.append(transition)
            
            # Update performance metrics
            self.performance_metrics['total_transitions'] += 1
            self.performance_metrics['successful_transitions'] += 1
            
            # Reset error count on successful transition
            if target_state != FloaterState.ERROR:
                self.consecutive_errors = 0
            
            self.logger.info("State transition: %s -> %s (event: %s)", 
                           self.previous_state, self.current_state, event)
            
            return True
            
        except Exception as e:
            self.logger.error("Error performing transition: %s", e)
            self._handle_error(f"transition_error: {str(e)}")
            return False
    
    def _call_event_handlers(self, event: StateTransitionEvent, **kwargs) -> None:
        """
        Call registered event handlers.
        
        Args:
            event: Event type
            **kwargs: Event data
        """
        try:
            if event in self.event_handlers:
                for handler in self.event_handlers[event]:
                    try:
                        handler(event, **kwargs)
                    except Exception as e:
                        self.logger.error("Error in event handler: %s", e)
                        
        except Exception as e:
            self.logger.error("Error calling event handlers: %s", e)
    
    def _handle_error(self, error_message: str) -> None:
        """
        Handle errors and update error tracking.
        
        Args:
            error_message: Error message
        """
        self.consecutive_errors += 1
        self.last_error_time = time.time()
        self.error_messages.append(error_message)
        
        self.performance_metrics['error_count'] += 1
        self.performance_metrics['failed_transitions'] += 1
        
        # Transition to ERROR state if threshold exceeded
        if self.consecutive_errors >= self.config.error_threshold:
            self._perform_transition(FloaterState.ERROR, StateTransitionEvent.ERROR_DETECTED)
    
    # Transition condition methods
    def _can_transition_to_filling(self, **kwargs) -> bool:
        """Check if can transition to filling state."""
        air_fill_level = kwargs.get('air_fill_level', 0.0)
        return air_fill_level <= self.config.max_empty_level
    
    def _can_transition_to_full(self, **kwargs) -> bool:
        """Check if can transition to full state."""
        air_fill_level = kwargs.get('air_fill_level', 0.0)
        return air_fill_level >= self.config.min_fill_level
    
    def _can_transition_to_venting(self, **kwargs) -> bool:
        """Check if can transition to venting state."""
        air_fill_level = kwargs.get('air_fill_level', 0.0)
        return air_fill_level >= self.config.min_fill_level
    
    def _can_transition_to_empty(self, **kwargs) -> bool:
        """Check if can transition to empty state."""
        air_fill_level = kwargs.get('air_fill_level', 0.0)
        return air_fill_level <= self.config.max_empty_level
    
    def _can_transition_from_error(self, **kwargs) -> bool:
        """Check if can transition from error state."""
        # Allow transition if enough time has passed since last error
        time_since_error = time.time() - self.last_error_time
        return time_since_error > self.config.transition_timeout
    
    def _can_transition_from_maintenance(self, **kwargs) -> bool:
        """Check if can transition from maintenance state."""
        # Allow transition if maintenance is complete
        maintenance_complete = kwargs.get('maintenance_complete', False)
        return maintenance_complete
    
    def get_current_state(self) -> FloaterState:
        """
        Get current state.
        
        Returns:
            Current state
        """
        return self.current_state
    
    def get_state_duration(self) -> float:
        """
        Get duration of current state.
        
        Returns:
            State duration in seconds
        """
        return time.time() - self.state_start_time
    
    def get_state_history(self, limit: Optional[int] = None) -> List[StateTransition]:
        """
        Get state transition history.
        
        Args:
            limit: Maximum number of transitions to return
            
        Returns:
            List of state transitions
        """
        if limit is None:
            return self.state_history.copy()
        else:
            return self.state_history[-limit:]
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Get performance metrics.
        
        Returns:
            Performance metrics dictionary
        """
        return self.performance_metrics.copy()
    
    def get_error_messages(self) -> List[str]:
        """
        Get error messages.
        
        Returns:
            List of error messages
        """
        return self.error_messages.copy()
    
    def is_in_error_state(self) -> bool:
        """
        Check if currently in error state.
        
        Returns:
            True if in error state
        """
        return self.current_state == FloaterState.ERROR
    
    def is_in_maintenance_state(self) -> bool:
        """
        Check if currently in maintenance state.
        
        Returns:
            True if in maintenance state
        """
        return self.current_state == FloaterState.MAINTENANCE
    
    def reset(self) -> None:
        """Reset state machine to initial state."""
        self.current_state = FloaterState.EMPTY
        self.previous_state = FloaterState.EMPTY
        self.state_history.clear()
        self.state_start_time = time.time()
        self.state_duration = 0.0
        self.consecutive_errors = 0
        self.last_error_time = 0.0
        self.error_messages.clear()
        self.performance_metrics = {
            'total_transitions': 0,
            'successful_transitions': 0,
            'failed_transitions': 0,
            'average_cycle_time': 0.0,
            'error_count': 0,
            'maintenance_count': 0
        }
        self.logger.info("State machine reset")

