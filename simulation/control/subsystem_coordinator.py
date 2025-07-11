"""
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
