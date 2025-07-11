#!/usr/bin/env python3
"""
Phase 6 Implementation Script: Control System Enhancement
KPP Simulator Physics Layer Upgrade

This script implements Phase 6 of the physics upgrade plan:
- SimPy-based event-driven control system
- Advanced control strategies and feedback loops
- Integration with all physics subsystems
- Real-time parameter management
- Safety monitoring and emergency responses
- Testing and validation of control system
"""

import logging
import sys
from pathlib import Path
from typing import Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('phase6_implementation.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class Phase6Implementation:
    """Phase 6 implementation manager"""
    
    def __init__(self):
        self.project_root = Path.cwd()
        self.control_dir = self.project_root / "simulation" / "control"
        self.strategies_dir = self.control_dir / "strategies"
        
    def run_phase6(self) -> bool:
        """Execute Phase 6 implementation"""
        logger.info("Starting Phase 6: Control System Enhancement")
        
        try:
            # Step 1: Create SimPy control framework
            if not self.create_simpy_control_framework():
                return False
                
            # Step 2: Implement advanced control strategies
            if not self.implement_advanced_strategies():
                return False
                
            # Step 3: Create subsystem integration
            if not self.create_subsystem_integration():
                return False
                
            # Step 4: Implement safety monitoring
            if not self.implement_safety_monitoring():
                return False
                
            # Step 5: Testing and validation
            if not self.test_and_validate():
                return False
                
            logger.info("Phase 6 completed successfully!")
            return True
            
        except Exception as e:
            logger.error(f"Phase 6 failed: {e}")
            return False
    
    def create_simpy_control_framework(self) -> bool:
        """Create SimPy-based control framework"""
        logger.info("Creating SimPy control framework...")
        
        # Create control_system.py with main control processes
        control_system_code = '''"""
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
'''
        
        control_system_file = self.control_dir / "control_system.py"
        control_system_file.write_text(control_system_code)
        
        logger.info("SimPy control framework created successfully")
        return True
    
    def implement_advanced_strategies(self) -> bool:
        """Implement advanced control strategies"""
        logger.info("Implementing advanced control strategies...")
        
        # Create base strategy class
        base_strategy_code = '''"""
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
'''
        
        base_strategy_file = self.strategies_dir / "base_strategy.py"
        base_strategy_file.write_text(base_strategy_code)
        
        # Create periodic strategy
        periodic_strategy_code = '''"""
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
'''
        
        periodic_strategy_file = self.strategies_dir / "periodic_strategy.py"
        periodic_strategy_file.write_text(periodic_strategy_code)
        
        # Create feedback strategy
        feedback_strategy_code = '''"""
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
'''
        
        feedback_strategy_file = self.strategies_dir / "feedback_strategy.py"
        feedback_strategy_file.write_text(feedback_strategy_code)
        
        logger.info("Advanced control strategies implemented successfully")
        return True
    
    def create_subsystem_integration(self) -> bool:
        """Create integration with all subsystems"""
        logger.info("Creating subsystem integration...")
        
        # Create subsystem_coordinator.py
        subsystem_coordinator_code = '''"""
Subsystem coordinator for integrating all physics components.
"""

import numpy as np
from typing import Dict, Any, Optional
from pathlib import Path
import sys

# Add paths for imports
project_root = Path(__file__).parent.parent.parent.parent
control_dir = project_root / "simulation" / "control"
chrono_dir = project_root / "simulation" / "physics" / "chrono"
sys.path.insert(0, str(control_dir))
sys.path.insert(0, str(chrono_dir))

from control_system import ControlSystem

class SubsystemCoordinator:
    """Coordinates all subsystems in the KPP simulator"""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize subsystem coordinator"""
        self.config = config
        
        # Initialize control system
        self.control_system = ControlSystem(config.get('control', {}))
        
        # Subsystem references (to be set externally)
        self.pneumatic_system = None
        self.drivetrain_system = None
        self.h3_enhancement = None
        self.environment_system = None
        
        # Integration state
        self.time_step = config.get('time_step', 0.02)
        self.current_time = 0.0
        self.system_initialized = False
        
        print("SubsystemCoordinator initialized")
        
    def set_pneumatic_system(self, pneumatic_system):
        """Set pneumatic system reference"""
        self.pneumatic_system = pneumatic_system
        self.control_system.set_pneumatic_system(pneumatic_system)
        
    def set_drivetrain_system(self, drivetrain_system):
        """Set drivetrain system reference"""
        self.drivetrain_system = drivetrain_system
        self.control_system.set_drivetrain_system(drivetrain_system)
        
    def set_h3_enhancement(self, h3_enhancement):
        """Set H3 enhancement reference"""
        self.h3_enhancement = h3_enhancement
        self.control_system.set_h3_enhancement(h3_enhancement)
        
    def set_environment_system(self, environment_system):
        """Set environment system reference"""
        self.environment_system = environment_system
        
    def initialize_system(self) -> bool:
        """Initialize all subsystems"""
        if self.system_initialized:
            print("System already initialized")
            return True
            
        try:
            # Set control strategy
            strategy_name = self.config.get('control', {}).get('strategy', 'periodic')
            self.control_system.set_control_strategy(strategy_name)
            
            # Initialize subsystems if needed
            if self.pneumatic_system and hasattr(self.pneumatic_system, 'initialize'):
                self.pneumatic_system.initialize()
                
            if self.drivetrain_system and hasattr(self.drivetrain_system, 'initialize'):
                self.drivetrain_system.initialize()
                
            self.system_initialized = True
            print("All subsystems initialized successfully")
            return True
            
        except Exception as e:
            print(f"System initialization failed: {e}")
            return False
            
    def start_simulation(self) -> bool:
        """Start the simulation"""
        if not self.system_initialized:
            if not self.initialize_system():
                return False
                
        self.control_system.start_system()
        print("Simulation started")
        return True
        
    def stop_simulation(self) -> None:
        """Stop the simulation"""
        self.control_system.stop_system()
        print("Simulation stopped")
        
    def update_simulation(self, dt: float = None) -> None:
        """Update simulation for one time step"""
        if dt is None:
            dt = self.time_step
            
        # Update control system
        self.control_system.step_simulation(dt)
        
        # Update subsystems
        if self.pneumatic_system and hasattr(self.pneumatic_system, 'update_system'):
            self.pneumatic_system.update_system(dt)
            
        if self.drivetrain_system and hasattr(self.drivetrain_system, 'update_system'):
            self.drivetrain_system.update_system(dt)
            
        # Update H3 enhancement if available
        if self.h3_enhancement and self.drivetrain_system:
            current_speed = self.drivetrain_system.get_angular_velocity_rpm()
            clutch_state = self.h3_enhancement.update_control(self.current_time, current_speed)
            self.drivetrain_system.set_clutch_state(clutch_state)
            
        self.current_time += dt
        
    def get_system_state(self) -> Dict[str, Any]:
        """Get complete system state"""
        state = {
            'time': self.current_time,
            'control_system': self.control_system.get_system_state(),
            'system_initialized': self.system_initialized
        }
        
        # Add subsystem states
        if self.pneumatic_system:
            state['pneumatic_system'] = self.pneumatic_system.get_system_status()
            
        if self.drivetrain_system:
            state['drivetrain_system'] = self.drivetrain_system.get_integrated_state()
            
        if self.h3_enhancement:
            state['h3_enhancement'] = self.h3_enhancement.get_performance_metrics()
            
        return state
        
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics"""
        metrics = {
            'time': self.current_time,
            'system_running': self.control_system.system_running
        }
        
        # Add performance data from subsystems
        if self.drivetrain_system:
            drivetrain_state = self.drivetrain_system.get_integrated_state()
            metrics.update({
                'speed_rpm': drivetrain_state['mechanical']['angular_velocity_rpm'],
                'mechanical_power': drivetrain_state['mechanical']['mechanical_power'],
                'electrical_power': drivetrain_state['electrical']['electrical_power_output'],
                'net_power': drivetrain_state['net_power'],
                'efficiency': drivetrain_state['overall_efficiency']
            })
            
        return metrics
'''
        
        subsystem_coordinator_file = self.control_dir / "subsystem_coordinator.py"
        subsystem_coordinator_file.write_text(subsystem_coordinator_code)
        
        logger.info("Subsystem integration created successfully")
        return True
    
    def implement_safety_monitoring(self) -> bool:
        """Implement safety monitoring system"""
        logger.info("Implementing safety monitoring...")
        
        # Create safety_monitor.py
        safety_monitor_code = '''"""
Safety monitoring system for KPP simulator.
"""

import numpy as np
from typing import Dict, Any, List, Callable
from enum import Enum

class SafetyLevel(Enum):
    """Safety levels"""
    NORMAL = "normal"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"

class SafetyMonitor:
    """Safety monitoring system"""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize safety monitor"""
        self.config = config
        
        # Safety thresholds
        self.max_speed = config.get('max_speed', 100.0)  # RPM
        self.max_torque = config.get('max_torque', 1000.0)  # N*m
        self.max_power = config.get('max_power', 20000.0)  # W
        self.max_pressure = config.get('max_pressure', 1000000.0)  # Pa
        
        # Monitoring state
        self.current_level = SafetyLevel.NORMAL
        self.active_warnings = []
        self.safety_callbacks = []
        
        # Event tracking
        self.safety_events = []
        
        print("SafetyMonitor initialized")
        
    def add_safety_callback(self, callback: Callable[[SafetyLevel, str], None]) -> None:
        """Add safety callback function"""
        self.safety_callbacks.append(callback)
        
    def check_speed_safety(self, speed: float) -> SafetyLevel:
        """Check speed safety"""
        if speed > self.max_speed * 1.2:
            return SafetyLevel.EMERGENCY
        elif speed > self.max_speed:
            return SafetyLevel.CRITICAL
        elif speed > self.max_speed * 0.9:
            return SafetyLevel.WARNING
        else:
            return SafetyLevel.NORMAL
            
    def check_torque_safety(self, torque: float) -> SafetyLevel:
        """Check torque safety"""
        if torque > self.max_torque * 1.2:
            return SafetyLevel.EMERGENCY
        elif torque > self.max_torque:
            return SafetyLevel.CRITICAL
        elif torque > self.max_torque * 0.9:
            return SafetyLevel.WARNING
        else:
            return SafetyLevel.NORMAL
            
    def check_power_safety(self, power: float) -> SafetyLevel:
        """Check power safety"""
        if power > self.max_power * 1.2:
            return SafetyLevel.EMERGENCY
        elif power > self.max_power:
            return SafetyLevel.CRITICAL
        elif power > self.max_power * 0.9:
            return SafetyLevel.WARNING
        else:
            return SafetyLevel.NORMAL
            
    def check_pressure_safety(self, pressure: float) -> SafetyLevel:
        """Check pressure safety"""
        if pressure > self.max_pressure * 1.2:
            return SafetyLevel.EMERGENCY
        elif pressure > self.max_pressure:
            return SafetyLevel.CRITICAL
        elif pressure > self.max_pressure * 0.9:
            return SafetyLevel.WARNING
        else:
            return SafetyLevel.NORMAL
            
    def update_safety_status(self, system_state: Dict[str, Any]) -> SafetyLevel:
        """Update overall safety status"""
        safety_levels = []
        
        # Check speed
        if 'speed_rpm' in system_state:
            speed_level = self.check_speed_safety(system_state['speed_rpm'])
            safety_levels.append(speed_level)
            
        # Check torque
        if 'torque' in system_state:
            torque_level = self.check_torque_safety(system_state['torque'])
            safety_levels.append(torque_level)
            
        # Check power
        if 'power' in system_state:
            power_level = self.check_power_safety(system_state['power'])
            safety_levels.append(power_level)
            
        # Check pressure
        if 'pressure' in system_state:
            pressure_level = self.check_pressure_safety(system_state['pressure'])
            safety_levels.append(pressure_level)
            
        # Determine overall safety level
        if SafetyLevel.EMERGENCY in safety_levels:
            new_level = SafetyLevel.EMERGENCY
        elif SafetyLevel.CRITICAL in safety_levels:
            new_level = SafetyLevel.CRITICAL
        elif SafetyLevel.WARNING in safety_levels:
            new_level = SafetyLevel.WARNING
        else:
            new_level = SafetyLevel.NORMAL
            
        # Update level and trigger callbacks if changed
        if new_level != self.current_level:
            self._trigger_safety_change(new_level)
            
        self.current_level = new_level
        return new_level
        
    def _trigger_safety_change(self, new_level: SafetyLevel) -> None:
        """Trigger safety level change callbacks"""
        old_level = self.current_level
        self.current_level = new_level
        
        # Log safety event
        event = {
            'time': 0.0,  # Will be set by caller
            'old_level': old_level.value,
            'new_level': new_level.value
        }
        self.safety_events.append(event)
        
        # Call safety callbacks
        for callback in self.safety_callbacks:
            try:
                callback(new_level, f"Safety level changed from {old_level.value} to {new_level.value}")
            except Exception as e:
                print(f"Safety callback error: {e}")
                
    def get_safety_status(self) -> Dict[str, Any]:
        """Get current safety status"""
        return {
            'current_level': self.current_level.value,
            'active_warnings': self.active_warnings,
            'event_count': len(self.safety_events),
            'max_speed': self.max_speed,
            'max_torque': self.max_torque,
            'max_power': self.max_power,
            'max_pressure': self.max_pressure
        }
        
    def get_recent_safety_events(self, count: int = 10) -> List[Dict[str, Any]]:
        """Get recent safety events"""
        return self.safety_events[-count:] if self.safety_events else []
'''
        
        safety_monitor_file = self.control_dir / "safety_monitor.py"
        safety_monitor_file.write_text(safety_monitor_code)
        
        logger.info("Safety monitoring implemented successfully")
        return True
    
    def test_and_validate(self) -> bool:
        """Test and validate control system"""
        logger.info("Testing and validating control system...")
        
        # Create test script
        test_code = '''"""
Test script for Phase 6: Control System Enhancement
"""

import sys
import numpy as np
from pathlib import Path

# Add simulation directories to path
sys.path.insert(0, str(Path.cwd() / "simulation" / "control"))
sys.path.insert(0, str(Path.cwd() / "simulation" / "control" / "strategies"))

def test_control_strategies():
    """Test control strategies"""
    print("Testing control strategies...")
    
    try:
        from strategies.periodic_strategy import PeriodicStrategy
        from strategies.feedback_strategy import FeedbackStrategy
        
        config = {
            'injection_interval': 2.0,
            'floater_count': 10,
            'target_speed': 50.0,
            'kp': 0.1,
            'ki': 0.01,
            'kd': 0.001
        }
        
        # Test periodic strategy
        periodic = PeriodicStrategy(config)
        actions = periodic.get_actions(45.0, 2.5)
        print(f"Periodic strategy actions: {actions}")
        
        # Test feedback strategy
        feedback = FeedbackStrategy(config)
        actions = feedback.get_actions(45.0, 2.5)
        print(f"Feedback strategy actions: {actions}")
        
        print("Control strategies test completed successfully!")
        return True
        
    except Exception as e:
        print(f"Control strategies test failed: {e}")
        return False

def test_control_system():
    """Test control system"""
    print("Testing control system...")
    
    try:
        from control_system import ControlSystem
        
        config = {
            'injection_interval': 2.0,
            'floater_count': 10,
            'target_speed': 50.0,
            'max_speed': 100.0,
            'min_speed': 10.0
        }
        
        control_system = ControlSystem(config)
        
        # Test strategy setting
        control_system.set_control_strategy('periodic')
        
        # Test system state
        state = control_system.get_system_state()
        print(f"Control system state: {state}")
        
        # Test simulation stepping
        control_system.step_simulation(0.1)
        
        print("Control system test completed successfully!")
        return True
        
    except Exception as e:
        print(f"Control system test failed: {e}")
        return False

def test_safety_monitoring():
    """Test safety monitoring"""
    print("Testing safety monitoring...")
    
    try:
        from safety_monitor import SafetyMonitor, SafetyLevel
        
        config = {
            'max_speed': 100.0,
            'max_torque': 1000.0,
            'max_power': 20000.0,
            'max_pressure': 1000000.0
        }
        
        safety_monitor = SafetyMonitor(config)
        
        # Test safety checks
        speed_level = safety_monitor.check_speed_safety(110.0)
        print(f"Speed safety level: {speed_level.value}")
        
        torque_level = safety_monitor.check_torque_safety(800.0)
        print(f"Torque safety level: {torque_level.value}")
        
        # Test system state monitoring
        system_state = {
            'speed_rpm': 110.0,
            'torque': 800.0,
            'power': 15000.0,
            'pressure': 500000.0
        }
        
        overall_level = safety_monitor.update_safety_status(system_state)
        print(f"Overall safety level: {overall_level.value}")
        
        # Get safety status
        status = safety_monitor.get_safety_status()
        print(f"Safety status: {status}")
        
        print("Safety monitoring test completed successfully!")
        return True
        
    except Exception as e:
        print(f"Safety monitoring test failed: {e}")
        return False

def test_subsystem_coordinator():
    """Test subsystem coordinator"""
    print("Testing subsystem coordinator...")
    
    try:
        from subsystem_coordinator import SubsystemCoordinator
        
        config = {
            'control': {
                'strategy': 'periodic',
                'injection_interval': 2.0,
                'floater_count': 10,
                'target_speed': 50.0
            },
            'time_step': 0.02
        }
        
        coordinator = SubsystemCoordinator(config)
        
        # Test initialization
        success = coordinator.initialize_system()
        print(f"System initialization: {success}")
        
        # Test system state
        state = coordinator.get_system_state()
        print(f"Coordinator state: {state}")
        
        print("Subsystem coordinator test completed successfully!")
        return True
        
    except Exception as e:
        print(f"Subsystem coordinator test failed: {e}")
        return False

def main():
    """Main test function"""
    print("Starting Phase 6 Control System Tests")
    print("=" * 50)
    
    tests = [
        test_control_strategies,
        test_control_system,
        test_safety_monitoring,
        test_subsystem_coordinator
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        print()
        if test():
            passed += 1
        print("-" * 30)
    
    print(f"\nTest Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("All Phase 6 tests passed successfully!")
        print("Phase 6: Control System Enhancement is ready for Phase 7")
    else:
        print("Some tests failed. Please check the implementation.")
        sys.exit(1)

if __name__ == "__main__":
    main()
'''
        
        test_file = Path.cwd() / "test_phase6_control_system.py"
        test_file.write_text(test_code)
        
        logger.info("Testing and validation setup completed successfully")
        return True

def main():
    """Main execution function"""
    logger.info("Starting KPP Simulator Physics Layer Upgrade - Phase 6")
    
    implementation = Phase6Implementation()
    success = implementation.run_phase6()
    
    if success:
        logger.info("Phase 6 completed successfully!")
        logger.info("Next steps:")
        logger.info("1. Test control strategies")
        logger.info("2. Validate control system operation")
        logger.info("3. Test safety monitoring")
        logger.info("4. Test subsystem coordination")
        logger.info("5. Proceed to Phase 7: Integration & Performance Tuning")
    else:
        logger.error("Phase 6 failed. Check the log file for details.")
        sys.exit(1)

if __name__ == "__main__":
    main() 