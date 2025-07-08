import numpy as np
import math
import logging
import time
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from collections import deque
from enum import Enum

"""
Timing Optimization Controller for KPP System
Implements intelligent pulse timing and load coordination for optimal energy transfer.
"""

class TimingState(str, Enum):
    """Timing controller state enumeration"""
    IDLE = "idle"
    OPTIMIZING = "optimizing"
    SYNCHRONIZED = "synchronized"
    FAULT = "fault"

class EventType(str, Enum):
    """Event type enumeration"""
    INJECTION = "injection"
    VENTING = "venting"
    SYNCHRONIZATION = "synchronization"
    OPTIMIZATION = "optimization"

@dataclass
class TimingEvent:
    """Timing event data structure"""
    event_type: EventType
    timestamp: float
    position: float  # degrees
    power_level: float  # W
    success: bool
    optimization_score: float

@dataclass
class TimingConfig:
    """Timing controller configuration"""
    injection_angle: float = 180.0  # degrees (bottom position)
    venting_angle: float = 0.0  # degrees (top position)
    angular_tolerance: float = 5.0  # degrees
    optimization_enabled: bool = True
    synchronization_threshold: float = 0.1  # seconds
    max_optimization_iterations: int = 100

class TimingController:
    """
    Advanced timing controller for KPP system optimization.
    Handles injection timing, venting timing, and synchronization control.
    """
    
    def __init__(self, config: Optional[TimingConfig] = None):
        """
        Initialize the timing controller.
        
        Args:
            config: Timing controller configuration
        """
        self.config = config or TimingConfig()
        self.logger = logging.getLogger(__name__)
        
        # System state
        self.timing_state = TimingState.IDLE
        self.current_position = 0.0  # degrees
        self.current_power = 0.0  # W
        self.last_injection_time = 0.0
        self.last_venting_time = 0.0
        
        # Performance tracking
        self.performance_metrics = {
            'total_events': 0,
            'successful_events': 0,
            'average_timing_accuracy': 0.0,  # degrees
            'optimization_savings': 0.0,  # kWh
            'synchronization_score': 0.0,  # 0-100
            'operating_hours': 0.0,  # hours
            'timing_errors': 0
        }
        
        # Event history
        self.event_history: List[TimingEvent] = []
        self.recent_events: deque = deque(maxlen=100)
        
        # Optimization parameters
        self.optimization_active = False
        self.optimization_target = 0.0
        self.optimization_history: List[Dict[str, Any]] = []
        
        # Timing parameters
        self.injection_timing = self.config.injection_angle
        self.venting_timing = self.config.venting_angle
        self.timing_tolerance = self.config.angular_tolerance
        
        # Synchronization parameters
        self.sync_threshold = self.config.synchronization_threshold
        self.last_sync_time = 0.0
        self.sync_accuracy = 0.0
        
        self.logger.info("Timing controller initialized")
    
    def start_timing_control(self) -> bool:
        """
        Start timing control.
        
        Returns:
            True if timing control started successfully
        """
        try:
            if self.timing_state != TimingState.IDLE:
                self.logger.warning("Cannot start timing control in state: %s", self.timing_state)
                return False
            
            # Initialize timing parameters
            self.timing_state = TimingState.SYNCHRONIZED
            
            # Record operation
            self._record_event(EventType.SYNCHRONIZATION, 0.0, 0.0, True, 1.0)
            
            self.logger.info("Timing control started")
            return True
            
        except Exception as e:
            self.logger.error("Error starting timing control: %s", e)
            self._handle_fault("timing_start_error", str(e))
            return False
    
    def stop_timing_control(self) -> bool:
        """
        Stop timing control.
        
        Returns:
            True if timing control stopped successfully
        """
        try:
            if self.timing_state == TimingState.IDLE:
                self.logger.warning("Timing control already stopped")
                return False
            
            # Stop optimization if active
            if self.optimization_active:
                self._stop_optimization()
            
            # Reset timing state
            self.timing_state = TimingState.IDLE
            self.current_position = 0.0
            self.current_power = 0.0
            
            self.logger.info("Timing control stopped")
            return True
            
        except Exception as e:
            self.logger.error("Error stopping timing control: %s", e)
            self._handle_fault("timing_stop_error", str(e))
            return False
    
    def update_timing_state(self, position: float, power: float) -> bool:
        """
        Update timing state based on current position and power.
        
        Args:
            position: Current angular position (degrees)
            power: Current power level (W)
            
        Returns:
            True if update successful
        """
        try:
            if self.timing_state == TimingState.IDLE:
                return False
            
            # Update current state
            self.current_position = position
            self.current_power = power
            
            # Check for injection event
            if self._should_inject():
                self._execute_injection()
            
            # Check for venting event
            if self._should_vent():
                self._execute_venting()
            
            # Update performance metrics
            self._update_performance_metrics()
            
            # Execute optimization if active
            if self.optimization_active:
                self._execute_timing_optimization()
            
            return True
            
        except Exception as e:
            self.logger.error("Error updating timing state: %s", e)
            self._handle_fault("state_update_error", str(e))
            return False
    
    def _should_inject(self) -> bool:
        """
        Check if injection should occur.
        
        Returns:
            True if injection should occur
        """
        try:
            # Check if position is near injection angle
            position_error = abs(self.current_position - self.injection_timing)
            
            # Check if enough time has passed since last injection
            time_since_last = time.time() - self.last_injection_time
            min_interval = 1.0  # minimum 1 second between injections
            
            return (position_error <= self.timing_tolerance and 
                   time_since_last >= min_interval)
            
        except Exception as e:
            self.logger.error("Error checking injection condition: %s", e)
            return False
    
    def _should_vent(self) -> bool:
        """
        Check if venting should occur.
        
        Returns:
            True if venting should occur
        """
        try:
            # Check if position is near venting angle
            position_error = abs(self.current_position - self.venting_timing)
            
            # Check if enough time has passed since last venting
            time_since_last = time.time() - self.last_venting_time
            min_interval = 1.0  # minimum 1 second between venting
            
            return (position_error <= self.timing_tolerance and 
                   time_since_last >= min_interval)
            
        except Exception as e:
            self.logger.error("Error checking venting condition: %s", e)
            return False
    
    def _execute_injection(self) -> None:
        """Execute injection event."""
        try:
            # Calculate timing accuracy
            timing_accuracy = self._calculate_timing_accuracy(self.injection_timing)
            
            # Determine success based on timing accuracy
            success = timing_accuracy <= self.timing_tolerance
            
            # Calculate optimization score
            optimization_score = self._calculate_optimization_score(timing_accuracy, self.current_power)
            
            # Record injection event
            self._record_event(EventType.INJECTION, self.current_position, 
                             self.current_power, success, optimization_score)
            
            # Update last injection time
            self.last_injection_time = time.time()
            
            # Update performance metrics
            self.performance_metrics['total_events'] += 1
            if success:
                self.performance_metrics['successful_events'] += 1
            
            self.logger.info("Injection executed at %.1f° (accuracy: %.1f°)", 
                           self.current_position, timing_accuracy)
            
        except Exception as e:
            self.logger.error("Error executing injection: %s", e)
    
    def _execute_venting(self) -> None:
        """Execute venting event."""
        try:
            # Calculate timing accuracy
            timing_accuracy = self._calculate_timing_accuracy(self.venting_timing)
            
            # Determine success based on timing accuracy
            success = timing_accuracy <= self.timing_tolerance
            
            # Calculate optimization score
            optimization_score = self._calculate_optimization_score(timing_accuracy, self.current_power)
            
            # Record venting event
            self._record_event(EventType.VENTING, self.current_position, 
                             self.current_power, success, optimization_score)
            
            # Update last venting time
            self.last_venting_time = time.time()
            
            # Update performance metrics
            self.performance_metrics['total_events'] += 1
            if success:
                self.performance_metrics['successful_events'] += 1
            
            self.logger.info("Venting executed at %.1f° (accuracy: %.1f°)", 
                           self.current_position, timing_accuracy)
            
        except Exception as e:
            self.logger.error("Error executing venting: %s", e)
    
    def _calculate_timing_accuracy(self, target_angle: float) -> float:
        """
        Calculate timing accuracy.
        
        Args:
            target_angle: Target angle (degrees)
            
        Returns:
            Timing accuracy (degrees)
        """
        try:
            # Calculate angular error
            error = abs(self.current_position - target_angle)
            
            # Normalize to 0-180 degrees
            if error > 180:
                error = 360 - error
            
            return error
            
        except Exception as e:
            self.logger.error("Error calculating timing accuracy: %s", e)
            return 180.0  # Maximum error
    
    def _calculate_optimization_score(self, timing_accuracy: float, power: float) -> float:
        """
        Calculate optimization score.
        
        Args:
            timing_accuracy: Timing accuracy (degrees)
            power: Current power (W)
            
        Returns:
            Optimization score (0-1)
        """
        try:
            # Timing component (0-0.5)
            timing_score = max(0, 0.5 - (timing_accuracy / 180.0) * 0.5)
            
            # Power component (0-0.5)
            power_score = min(0.5, power / 50000.0 * 0.5)  # Normalize to 50 kW
            
            return timing_score + power_score
            
        except Exception as e:
            self.logger.error("Error calculating optimization score: %s", e)
            return 0.0
    
    def start_optimization(self) -> bool:
        """
        Start timing optimization.
        
        Returns:
            True if optimization started successfully
        """
        try:
            if not self.config.optimization_enabled:
                self.logger.warning("Optimization not enabled")
                return False
            
            if self.optimization_active:
                self.logger.warning("Optimization already active")
                return False
            
            self.optimization_active = True
            self.timing_state = TimingState.OPTIMIZING
            
            # Set optimization target
            self.optimization_target = self._calculate_optimization_target()
            
            # Record optimization start
            self._record_event(EventType.OPTIMIZATION, self.current_position, 
                             self.current_power, True, 1.0)
            
            self.logger.info("Timing optimization started")
            return True
            
        except Exception as e:
            self.logger.error("Error starting optimization: %s", e)
            return False
    
    def _stop_optimization(self) -> None:
        """Stop timing optimization."""
        try:
            self.optimization_active = False
            
            if self.timing_state == TimingState.OPTIMIZING:
                self.timing_state = TimingState.SYNCHRONIZED
            
            self.logger.info("Timing optimization stopped")
            
        except Exception as e:
            self.logger.error("Error stopping optimization: %s", e)
    
    def _calculate_optimization_target(self) -> float:
        """
        Calculate optimization target.
        
        Returns:
            Optimization target value
        """
        try:
            # Calculate target based on recent performance
            if len(self.recent_events) > 0:
                recent_scores = [event.optimization_score for event in self.recent_events]
                target = sum(recent_scores) / len(recent_scores)
                return min(1.0, target * 1.1)  # Aim for 10% improvement
            else:
                return 0.8  # Default target
            
        except Exception as e:
            self.logger.error("Error calculating optimization target: %s", e)
            return 0.8
    
    def _execute_timing_optimization(self) -> None:
        """Execute timing optimization algorithm."""
        try:
            # Simplified optimization algorithm
            # In practice, this would use advanced optimization techniques
            
            current_score = self._calculate_optimization_score(
                self._calculate_timing_accuracy(self.injection_timing),
                self.current_power
            )
            
            # Adjust timing parameters for better performance
            if current_score < self.optimization_target:
                self._adjust_timing_parameters()
            
            # Record optimization iteration
            optimization_record = {
                'timestamp': time.time(),
                'current_score': current_score,
                'target_score': self.optimization_target,
                'injection_timing': self.injection_timing,
                'venting_timing': self.venting_timing,
                'timing_tolerance': self.timing_tolerance
            }
            
            self.optimization_history.append(optimization_record)
            
            # Update optimization savings
            if current_score > 0.8:  # Good performance
                self.performance_metrics['optimization_savings'] += 0.001  # kWh
            
        except Exception as e:
            self.logger.error("Error executing timing optimization: %s", e)
    
    def _adjust_timing_parameters(self) -> None:
        """Adjust timing parameters for optimization."""
        try:
            # Analyze recent events for timing patterns
            if len(self.recent_events) >= 10:
                injection_events = [e for e in self.recent_events if e.event_type == EventType.INJECTION]
                venting_events = [e for e in self.recent_events if e.event_type == EventType.VENTING]
                
                # Adjust injection timing based on successful events
                if injection_events:
                    successful_injections = [e for e in injection_events if e.success]
                    if successful_injections:
                        avg_position = sum(e.position for e in successful_injections) / len(successful_injections)
                        self.injection_timing = avg_position
                
                # Adjust venting timing based on successful events
                if venting_events:
                    successful_venting = [e for e in venting_events if e.success]
                    if successful_venting:
                        avg_position = sum(e.position for e in successful_venting) / len(successful_venting)
                        self.venting_timing = avg_position
                
                # Adjust tolerance based on performance
                success_rate = self.performance_metrics['successful_events'] / max(1, self.performance_metrics['total_events'])
                if success_rate < 0.8:  # Low success rate
                    self.timing_tolerance = min(10.0, self.timing_tolerance * 1.1)  # Increase tolerance
                elif success_rate > 0.95:  # High success rate
                    self.timing_tolerance = max(2.0, self.timing_tolerance * 0.9)  # Decrease tolerance
            
        except Exception as e:
            self.logger.error("Error adjusting timing parameters: %s", e)
    
    def _update_performance_metrics(self) -> None:
        """Update performance metrics."""
        try:
            # Update operating hours
            self.performance_metrics['operating_hours'] += 0.001  # hours
            
            # Calculate average timing accuracy
            if len(self.event_history) > 0:
                recent_events = self.event_history[-50:]  # Last 50 events
                accuracies = []
                
                for event in recent_events:
                    if event.event_type in [EventType.INJECTION, EventType.VENTING]:
                        target_angle = (self.injection_timing if event.event_type == EventType.INJECTION 
                                      else self.venting_timing)
                        accuracy = self._calculate_timing_accuracy(target_angle)
                        accuracies.append(accuracy)
                
                if accuracies:
                    self.performance_metrics['average_timing_accuracy'] = sum(accuracies) / len(accuracies)
            
            # Calculate synchronization score
            if self.performance_metrics['total_events'] > 0:
                success_rate = self.performance_metrics['successful_events'] / self.performance_metrics['total_events']
                self.performance_metrics['synchronization_score'] = success_rate * 100
            
        except Exception as e:
            self.logger.error("Error updating performance metrics: %s", e)
    
    def _record_event(self, event_type: EventType, position: float, power: float, 
                     success: bool, optimization_score: float) -> None:
        """
        Record timing event.
        
        Args:
            event_type: Type of event
            position: Position at event (degrees)
            power: Power at event (W)
            success: Whether event was successful
            optimization_score: Optimization score
        """
        try:
            event = TimingEvent(
                event_type=event_type,
                timestamp=time.time(),
                position=position,
                power_level=power,
                success=success,
                optimization_score=optimization_score
            )
            
            self.event_history.append(event)
            self.recent_events.append(event)
            
        except Exception as e:
            self.logger.error("Error recording event: %s", e)
    
    def _handle_fault(self, fault_type: str, fault_message: str) -> None:
        """
        Handle timing controller faults.
        
        Args:
            fault_type: Type of fault
            fault_message: Fault message
        """
        try:
            self.logger.error("Timing fault: %s - %s", fault_type, fault_message)
            
            # Update system state
            self.timing_state = TimingState.FAULT
            
            # Update performance metrics
            self.performance_metrics['timing_errors'] += 1
            
        except Exception as e:
            self.logger.error("Error handling fault: %s", e)
    
    def get_timing_state(self) -> TimingState:
        """
        Get current timing state.
        
        Returns:
            Current timing state
        """
        return self.timing_state
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Get performance metrics.
        
        Returns:
            Performance metrics dictionary
        """
        return self.performance_metrics.copy()
    
    def get_event_history(self, limit: Optional[int] = None) -> List[TimingEvent]:
        """
        Get event history.
        
        Args:
            limit: Maximum number of events to return
            
        Returns:
            List of timing events
        """
        if limit is None:
            return self.event_history.copy()
        else:
            return self.event_history[-limit:]
    
    def get_optimization_history(self) -> List[Dict[str, Any]]:
        """
        Get optimization history.
        
        Returns:
            List of optimization records
        """
        return self.optimization_history.copy()
    
    def is_optimizing(self) -> bool:
        """
        Check if optimization is active.
        
        Returns:
            True if optimizing
        """
        return self.optimization_active
    
    def get_timing_parameters(self) -> Dict[str, float]:
        """
        Get current timing parameters.
        
        Returns:
            Dictionary of timing parameters
        """
        return {
            'injection_timing': self.injection_timing,
            'venting_timing': self.venting_timing,
            'timing_tolerance': self.timing_tolerance,
            'current_position': self.current_position,
            'current_power': self.current_power
        }
    
    def reset(self) -> None:
        """Reset timing controller to initial state."""
        self.timing_state = TimingState.IDLE
        self.current_position = 0.0
        self.current_power = 0.0
        self.event_history.clear()
        self.recent_events.clear()
        self.optimization_history.clear()
        self.optimization_active = False
        self.performance_metrics = {
            'total_events': 0,
            'successful_events': 0,
            'average_timing_accuracy': 0.0,
            'optimization_savings': 0.0,
            'synchronization_score': 0.0,
            'operating_hours': 0.0,
            'timing_errors': 0
        }
        self.logger.info("Timing controller reset")

