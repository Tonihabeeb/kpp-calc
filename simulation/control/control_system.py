"""
Main control system using SimPy for event-driven coordination.
"""

import simpy
import numpy as np
from typing import Dict, Any, Optional, List
from pathlib import Path
import sys

# Add paths for imports
project_root = Path(__file__).parent.parent.parent.parent
control_dir = project_root / "simulation" / "control"
chrono_dir = project_root / "simulation" / "physics" / "chrono"
sys.path.insert(0, str(control_dir))
sys.path.insert(0, str(chrono_dir))

from strategies.base_strategy import ControlStrategy
from strategies.periodic_strategy import PeriodicStrategy
from strategies.feedback_strategy import FeedbackStrategy

class ControlSystem:
    """Main control system coordinating all subsystems"""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize control system"""
        self.config = config
        
        # Create SimPy environment
        self.env = simpy.Environment()
        
        # Control parameters
        self.injection_interval = config.get('injection_interval', 2.0)  # s
        self.floater_count = config.get('floater_count', 10)
        self.target_speed = config.get('target_speed', 50.0)  # RPM
        self.max_speed = config.get('max_speed', 100.0)  # RPM
        self.min_speed = config.get('min_speed', 10.0)  # RPM
        
        # System state
        self.current_strategy = None
        self.system_running = False
        self.emergency_stop = False
        
        # Subsystem references (to be set by integration)
        self.pneumatic_system = None
        self.drivetrain_system = None
        self.h3_enhancement = None
        
        # Process tracking
        self.active_processes = []
        self.event_log = []
        
        print("ControlSystem initialized with SimPy")
        
    def set_pneumatic_system(self, pneumatic_system):
        """Set reference to pneumatic system"""
        self.pneumatic_system = pneumatic_system
        
    def set_drivetrain_system(self, drivetrain_system):
        """Set reference to drivetrain system"""
        self.drivetrain_system = drivetrain_system
        
    def set_h3_enhancement(self, h3_enhancement):
        """Set reference to H3 enhancement"""
        self.h3_enhancement = h3_enhancement
        
    def start_system(self) -> None:
        """Start the control system"""
        if self.system_running:
            print("System already running")
            return
            
        self.system_running = True
        self.emergency_stop = False
        
        # Start main control processes
        self.env.process(self._main_control_loop())
        self.env.process(self._speed_monitoring())
        self.env.process(self._safety_monitoring())
        
        print("Control system started")
        
    def stop_system(self) -> None:
        """Stop the control system"""
        self.system_running = False
        self.emergency_stop = True
        
        # Interrupt all active processes
        for process in self.active_processes:
            if hasattr(process, 'interrupt'):
                process.interrupt()
                
        print("Control system stopped")
        
    def set_control_strategy(self, strategy_name: str) -> bool:
        """Set the control strategy"""
        if strategy_name == 'periodic':
            self.current_strategy = PeriodicStrategy(self.config)
        elif strategy_name == 'feedback':
            self.current_strategy = FeedbackStrategy(self.config)
        else:
            print(f"Unknown strategy: {strategy_name}")
            return False
            
        print(f"Control strategy set to: {strategy_name}")
        return True
        
    def _main_control_loop(self):
        """Main control loop process"""
        while self.system_running and not self.emergency_stop:
            try:
                # Get current system state
                current_speed = self.drivetrain_system.get_angular_velocity_rpm() if self.drivetrain_system else 0.0
                
                # Execute current strategy
                if self.current_strategy:
                    actions = self.current_strategy.get_actions(current_speed, self.env.now)
                    yield from self._execute_actions(actions)
                
                # Wait for next control cycle
                yield self.env.timeout(0.1)  # 100ms control cycle
                
            except simpy.Interrupt:
                print("Main control loop interrupted")
                break
                
    def _speed_monitoring(self):
        """Speed monitoring process"""
        while self.system_running and not self.emergency_stop:
            try:
                if self.drivetrain_system:
                    current_speed = self.drivetrain_system.get_angular_velocity_rpm()
                    
                    # Check speed limits
                    if current_speed > self.max_speed:
                        print(f"WARNING: Speed {current_speed:.1f} RPM exceeds maximum {self.max_speed} RPM")
                        self._trigger_safety_response('speed_limit_exceeded')
                    elif current_speed < self.min_speed:
                        print(f"WARNING: Speed {current_speed:.1f} RPM below minimum {self.min_speed} RPM")
                        
                yield self.env.timeout(0.5)  # Check every 500ms
                
            except simpy.Interrupt:
                print("Speed monitoring interrupted")
                break
                
    def _safety_monitoring(self):
        """Safety monitoring process"""
        while self.system_running and not self.emergency_stop:
            try:
                # Check for emergency conditions
                if self.emergency_stop:
                    self._trigger_safety_response('emergency_stop')
                    break
                    
                yield self.env.timeout(1.0)  # Check every second
                
            except simpy.Interrupt:
                print("Safety monitoring interrupted")
                break
                
    def _execute_actions(self, actions: List[Dict[str, Any]]):
        """Execute control actions"""
        for action in actions:
            action_type = action.get('type')
            
            if action_type == 'inject_floater':
                floater_id = action.get('floater_id')
                if self.pneumatic_system:
                    self.pneumatic_system.start_air_injection(floater_id)
                    self._log_event(f"inject_floater_{floater_id}")
                    
            elif action_type == 'set_clutch':
                engaged = action.get('engaged', True)
                if self.drivetrain_system:
                    self.drivetrain_system.set_clutch_state(engaged)
                    self._log_event(f"clutch_{'engaged' if engaged else 'disengaged'}")
                    
            elif action_type == 'wait':
                duration = action.get('duration', 0.1)
                yield self.env.timeout(duration)
                
    def _trigger_safety_response(self, response_type: str) -> None:
        """Trigger safety response"""
        print(f"SAFETY RESPONSE: {response_type}")
        
        if response_type == 'emergency_stop':
            self.stop_system()
        elif response_type == 'speed_limit_exceeded':
            # Reduce power or disengage clutch
            if self.drivetrain_system:
                self.drivetrain_system.set_clutch_state(False)
                
        self._log_event(f"safety_response_{response_type}")
        
    def _log_event(self, event_type: str) -> None:
        """Log control event"""
        event = {
            'time': self.env.now,
            'type': event_type
        }
        self.event_log.append(event)
        
    def step_simulation(self, dt: float) -> None:
        """Step the control simulation forward"""
        self.env.run(until=self.env.now + dt)
        
    def get_system_state(self) -> Dict[str, Any]:
        """Get control system state"""
        return {
            'time': self.env.now,
            'system_running': self.system_running,
            'emergency_stop': self.emergency_stop,
            'current_strategy': type(self.current_strategy).__name__ if self.current_strategy else None,
            'target_speed': self.target_speed,
            'injection_interval': self.injection_interval,
            'active_processes': len(self.active_processes),
            'event_count': len(self.event_log)
        }
        
    def get_recent_events(self, count: int = 10) -> List[Dict[str, Any]]:
        """Get recent control events"""
        return self.event_log[-count:] if self.event_log else []
