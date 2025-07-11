"""
Control module for KPP simulation.
Handles state machine logic, sensor handling, and H3 pulse-and-coast timing.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Dict, Tuple
import time

class SystemState(str, Enum):
    """System operational states"""
    STARTUP = "startup"
    RUNNING = "running"
    EMERGENCY_STOP = "emergency_stop"
    SHUTDOWN = "shutdown"

class FloaterState(str, Enum):
    """Individual floater states"""
    ASCENDING = "ascending"  # Air-filled, moving up
    DESCENDING = "descending"  # Water-filled, moving down
    TRANSITION_BOTTOM = "transition_bottom"  # At bottom, being filled with air
    TRANSITION_TOP = "transition_top"  # At top, being vented

@dataclass
class ControlConfig:
    """Configuration parameters for control system"""
    # H3 pulse-and-coast parameters
    h3_enabled: bool = False
    coast_time: float = 5.0  # seconds to coast (clutch disengaged)
    pulse_time: float = 2.0  # seconds to pulse (clutch engaged)
    
    # Generator control
    base_generator_torque: float = 500.0  # N·m
    pulse_generator_torque: float = 800.0  # N·m during pulse phase
    
    # Safety limits
    max_chain_speed: float = 2.0  # m/s
    min_chain_speed: float = 0.1  # m/s
    emergency_chain_speed: float = 3.0  # m/s (trigger emergency stop)
    
    # Position thresholds
    bottom_trigger_height: float = 0.1  # m (height to trigger bottom transition)
    top_trigger_height: float = 9.9  # m (height to trigger top transition, assuming 10m tank)

class Controller:
    """
    Main control system for KPP operation.
    
    Features:
    - State machine logic for system operation
    - Sensor monitoring and event handling
    - H3 pulse-and-coast timing coordination
    - Safety monitoring and emergency response
    """
    
    def __init__(self, config: Optional[ControlConfig] = None):
        """Initialize controller with given configuration"""
        self.config = config or ControlConfig()
        
        # System state
        self.system_state = SystemState.STARTUP
        self.h3_phase_start_time = 0.0
        self.clutch_engaged = True
        
        # Floater tracking
        self.floater_states: Dict[int, FloaterState] = {}  # floater_id -> state
        
        # Performance monitoring
        self.cycle_count = 0
        self.last_emergency_time = 0.0
        self.emergency_count = 0
        
    def initialize_floater(self, floater_id: int, initial_state: FloaterState) -> None:
        """Register a new floater with the controller"""
        self.floater_states[floater_id] = initial_state
    
    def check_safety_limits(self, chain_speed: float) -> bool:
        """
        Check if system is operating within safety limits.
        Returns True if safe, False if emergency stop needed.
        """
        if abs(chain_speed) > self.config.emergency_chain_speed:
            self.system_state = SystemState.EMERGENCY_STOP
            self.emergency_count += 1
            self.last_emergency_time = time.time()
            return False
        return True
    
    def handle_bottom_sensor(self, floater_id: int, height: float) -> bool:
        """
        Handle floater reaching bottom position.
        Returns True if air injection should be triggered.
        """
        if height <= self.config.bottom_trigger_height:
            if self.floater_states[floater_id] == FloaterState.DESCENDING:
                self.floater_states[floater_id] = FloaterState.TRANSITION_BOTTOM
                return True
        return False
    
    def handle_top_sensor(self, floater_id: int, height: float) -> bool:
        """
        Handle floater reaching top position.
        Returns True if water filling should be triggered.
        """
        if height >= self.config.top_trigger_height:
            if self.floater_states[floater_id] == FloaterState.ASCENDING:
                self.floater_states[floater_id] = FloaterState.TRANSITION_TOP
                return True
        return False
    
    def update_floater_state(self, floater_id: int, new_state: FloaterState) -> None:
        """Update tracked state of a floater after state transition"""
        self.floater_states[floater_id] = new_state
        if new_state == FloaterState.ASCENDING:
            self.cycle_count += 1
    
    def get_h3_control(self, current_time: float) -> Tuple[bool, float]:
        """
        Get H3 control outputs (clutch state and generator torque).
        Returns (clutch_engaged, generator_torque).
        """
        if not self.config.h3_enabled:
            return True, self.config.base_generator_torque
        
        # Compute phase timing
        cycle_time = self.config.coast_time + self.config.pulse_time
        phase_time = (current_time - self.h3_phase_start_time) % cycle_time
        
        # Determine if we're in coast or pulse phase
        if phase_time < self.config.coast_time:
            # Coast phase: clutch disengaged, no generator torque
            return False, 0.0
        else:
            # Pulse phase: clutch engaged, high generator torque
            return True, self.config.pulse_generator_torque
    
    def update(self, current_time: float, chain_speed: float) -> Dict:
        """
        Main control update function. Called each simulation step.
        Returns dict of control actions and system state.
        """
        # Check safety limits first
        is_safe = self.check_safety_limits(chain_speed)
        
        if not is_safe:
            return {
                'system_state': SystemState.EMERGENCY_STOP,
                'clutch_engaged': True,  # Emergency engages clutch
                'generator_torque': self.config.pulse_generator_torque,  # High torque to stop
                'can_inject': False,
                'can_vent': False
            }
        
        # Normal operation
        if self.system_state == SystemState.STARTUP:
            if abs(chain_speed) > self.config.min_chain_speed:
                self.system_state = SystemState.RUNNING
                self.h3_phase_start_time = current_time
        
        # Get H3 control outputs
        clutch_engaged, generator_torque = self.get_h3_control(current_time)
        
        return {
            'system_state': self.system_state,
            'clutch_engaged': clutch_engaged,
            'generator_torque': generator_torque,
            'can_inject': True,
            'can_vent': True
        }
    
    def get_performance_metrics(self) -> Dict:
        """Get current performance metrics"""
        return {
            'cycle_count': self.cycle_count,
            'emergency_count': self.emergency_count,
            'system_state': self.system_state,
            'h3_enabled': self.config.h3_enabled
        }
    
    def reset(self) -> None:
        """Reset controller to initial state"""
        self.system_state = SystemState.STARTUP
        self.h3_phase_start_time = 0.0
        self.clutch_engaged = True
        self.cycle_count = 0
        self.emergency_count = 0
        self.floater_states.clear() 