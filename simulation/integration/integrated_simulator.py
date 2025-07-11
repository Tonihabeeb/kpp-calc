"""
Complete integrated KPP simulator with all physics upgrades.
"""

import numpy as np
import time
from typing import Dict, Any, Optional, List
from pathlib import Path
import sys

# Add paths for imports
project_root = Path(__file__).parent.parent.parent.parent
chrono_dir = project_root / "simulation" / "physics" / "chrono"
control_dir = project_root / "simulation" / "control"
thermo_dir = project_root / "simulation" / "physics" / "thermodynamics"
electrical_dir = project_root / "simulation" / "physics" / "electrical"
sys.path.insert(0, str(chrono_dir))
sys.path.insert(0, str(control_dir))
sys.path.insert(0, str(thermo_dir))
sys.path.insert(0, str(electrical_dir))

from integrated_drivetrain import IntegratedDrivetrain
from subsystem_coordinator import SubsystemCoordinator
from enhanced_pneumatics import EnhancedPneumaticSystem
from air_system import AirThermodynamics
from generator_model import GeneratorModel
from h2_enhancement import H2Enhancement
from h3_enhancement import H3Enhancement
from safety_monitor import SafetyMonitor

class IntegratedKPPSimulator:
    """Complete integrated KPP simulator with all physics upgrades"""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize integrated simulator"""
        self.config = config
        
        # Performance tracking
        self.start_time = time.time()
        self.frame_count = 0
        self.avg_frame_time = 0.0
        self.max_frame_time = 0.0
        
        # Initialize all subsystems
        self._initialize_subsystems()
        
        # Integration state
        self.simulation_time = 0.0
        self.time_step = config.get('time_step', 0.02)
        self.running = False
        
        print("IntegratedKPPSimulator initialized with all physics upgrades")
        
    def _initialize_subsystems(self):
        """Initialize all physics subsystems"""
        # Air thermodynamics
        self.air_thermo = AirThermodynamics(self.config.get('air_thermo', {}))
        
        # Pneumatic system
        pneumatic_config = self.config.get('pneumatic', {})
        pneumatic_config['air_thermo'] = self.config.get('air_thermo', {})
        self.pneumatic_system = EnhancedPneumaticSystem(pneumatic_config)
        
        # H2 enhancement
        self.h2_enhancement = H2Enhancement(self.config.get('h2', {}))
        
        # Drivetrain system
        drivetrain_config = self.config.get('drivetrain', {})
        self.drivetrain_system = IntegratedDrivetrain(drivetrain_config)
        
        # H3 enhancement
        self.h3_enhancement = H3Enhancement(self.config.get('h3', {}))
        
        # Safety monitor
        self.safety_monitor = SafetyMonitor(self.config.get('safety', {}))
        
        # Subsystem coordinator
        coordinator_config = self.config.get('control', {})
        self.coordinator = SubsystemCoordinator(coordinator_config)
        
        # Connect subsystems
        self.coordinator.set_pneumatic_system(self.pneumatic_system)
        self.coordinator.set_drivetrain_system(self.drivetrain_system)
        self.coordinator.set_h3_enhancement(self.h3_enhancement)
        
    def start_simulation(self) -> bool:
        """Start the integrated simulation"""
        if self.running:
            print("Simulation already running")
            return False
            
        # Initialize system
        if not self.coordinator.initialize_system():
            print("Failed to initialize system")
            return False
            
        # Start simulation
        if not self.coordinator.start_simulation():
            print("Failed to start simulation")
            return False
            
        self.running = True
        self.start_time = time.time()
        print("Integrated simulation started")
        return True
        
    def stop_simulation(self) -> None:
        """Stop the integrated simulation"""
        self.running = False
        self.coordinator.stop_simulation()
        print("Integrated simulation stopped")
        
    def update_simulation(self, dt: float = None) -> Dict[str, Any]:
        """Update simulation for one time step"""
        if not self.running:
            return {}
            
        frame_start = time.time()
        
        if dt is None:
            dt = self.time_step
            
        # Update coordinator (includes all subsystems)
        self.coordinator.update_simulation(dt)
        
        # Update simulation time
        self.simulation_time += dt
        
        # Update performance tracking
        frame_time = time.time() - frame_start
        self.frame_count += 1
        self.avg_frame_time = (self.avg_frame_time * (self.frame_count - 1) + frame_time) / self.frame_count
        self.max_frame_time = max(self.max_frame_time, frame_time)
        
        # Get system state
        state = self._get_complete_state()
        
        # Update safety monitoring
        safety_state = {
            'speed_rpm': state.get('drivetrain', {}).get('mechanical', {}).get('angular_velocity_rpm', 0.0),
            'torque': state.get('drivetrain', {}).get('mechanical', {}).get('torque_output', 0.0),
            'power': state.get('drivetrain', {}).get('net_power', 0.0),
            'pressure': state.get('pneumatic_system', {}).get('compressor_pressure', 0.0)
        }
        
        safety_level = self.safety_monitor.update_safety_status(safety_state)
        state['safety_level'] = safety_level.value
        
        return state
        
    def _get_complete_state(self) -> Dict[str, Any]:
        """Get complete system state"""
        state = {
            'simulation_time': self.simulation_time,
            'performance': {
                'frame_count': self.frame_count,
                'avg_frame_time': self.avg_frame_time,
                'max_frame_time': self.max_frame_time,
                'fps': 1.0 / self.avg_frame_time if self.avg_frame_time > 0 else 0.0
            }
        }
        
        # Add subsystem states
        state.update(self.coordinator.get_system_state())
        
        return state
        
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics"""
        return {
            'total_runtime': time.time() - self.start_time,
            'simulation_time': self.simulation_time,
            'frame_count': self.frame_count,
            'avg_frame_time': self.avg_frame_time,
            'max_frame_time': self.max_frame_time,
            'fps': 1.0 / self.avg_frame_time if self.avg_frame_time > 0 else 0.0,
            'real_time_factor': self.simulation_time / (time.time() - self.start_time) if time.time() > self.start_time else 0.0
        }
        
    def enable_enhancement(self, enhancement: str, enabled: bool = True) -> bool:
        """Enable or disable an enhancement"""
        if enhancement == 'H1':
            # H1 is handled in environment system
            print(f"H1 enhancement {'enabled' if enabled else 'disabled'}")
            return True
        elif enhancement == 'H2':
            if enabled:
                self.h2_enhancement.enable()
            else:
                self.h2_enhancement.disable()
            return True
        elif enhancement == 'H3':
            if enabled:
                self.h3_enhancement.enable()
            else:
                self.h3_enhancement.disable()
            return True
        else:
            print(f"Unknown enhancement: {enhancement}")
            return False
            
    def set_control_strategy(self, strategy: str) -> bool:
        """Set control strategy"""
        return self.coordinator.control_system.set_control_strategy(strategy)
        
    def get_system_status(self) -> Dict[str, Any]:
        """Get complete system status"""
        return {
            'running': self.running,
            'simulation_time': self.simulation_time,
            'performance': self.get_performance_metrics(),
            'safety': self.safety_monitor.get_safety_status(),
            'enhancements': {
                'H1': True,  # Always available
                'H2': self.h2_enhancement.enabled if hasattr(self.h2_enhancement, 'enabled') else False,
                'H3': self.h3_enhancement.enabled if hasattr(self.h3_enhancement, 'enabled') else False
            }
        }
