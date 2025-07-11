"""
Integrated drivetrain system combining mechanical and electrical components.
"""

import numpy as np
from typing import Dict, Any, Optional
import sys
from pathlib import Path

# Add paths for imports
project_root = Path(__file__).parent.parent.parent.parent
chrono_dir = project_root / "simulation" / "physics" / "chrono"
electrical_dir = project_root / "simulation" / "physics" / "electrical"
sys.path.insert(0, str(chrono_dir))
sys.path.insert(0, str(electrical_dir))

from drivetrain_system import DrivetrainSystem
from generator_model import GeneratorModel

class IntegratedDrivetrain:
    """Integrated drivetrain combining mechanical and electrical systems"""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize integrated drivetrain"""
        self.config = config
        
        # Initialize subsystems
        self.mechanical_system = DrivetrainSystem(config.get('mechanical', {}))
        self.electrical_system = GeneratorModel(config.get('electrical', {}))
        
        # Integration parameters
        self.time_step = config.get('time_step', 0.02)  # s
        self.current_time = 0.0
        
        # Performance tracking
        self.net_power = 0.0  # W (electrical output - compressor input)
        self.overall_efficiency = 0.0
        
        print("IntegratedDrivetrain initialized")
        
    def apply_chain_torque(self, torque: float) -> None:
        """Apply torque from chain to mechanical system"""
        self.mechanical_system.apply_torque(torque)
        
    def set_clutch_state(self, engaged: bool) -> None:
        """Set clutch engagement state"""
        self.mechanical_system.set_clutch_state(engaged)
        
    def set_compressor_power(self, power: float) -> None:
        """Set compressor power consumption (to be subtracted from net output)"""
        self.compressor_power = power
        
    def update_system(self, dt: float = None) -> None:
        """Update both mechanical and electrical systems"""
        if dt is None:
            dt = self.time_step
            
        # Update mechanical system
        self.mechanical_system.update_dynamics(dt)
        
        # Get mechanical power and feed to electrical system
        mechanical_power = self.mechanical_system.get_mechanical_power()
        self.electrical_system.set_mechanical_power(mechanical_power)
        
        # Calculate electrical output
        electrical_output = self.electrical_system.calculate_electrical_output()
        
        # Update energy tracking
        self.electrical_system.update_energy(dt)
        
        # Calculate net power (electrical output - compressor input)
        compressor_power = getattr(self, 'compressor_power', 0.0)
        self.net_power = electrical_output['electrical_power'] - compressor_power
        
        # Calculate overall efficiency
        if mechanical_power > 0:
            self.overall_efficiency = self.net_power / mechanical_power
        else:
            self.overall_efficiency = 0.0
            
        self.current_time += dt
        
    def get_mechanical_state(self) -> Dict[str, Any]:
        """Get mechanical system state"""
        return self.mechanical_system.get_system_state()
        
    def get_electrical_state(self) -> Dict[str, Any]:
        """Get electrical system state"""
        return self.electrical_system.get_system_state()
        
    def get_integrated_state(self) -> Dict[str, Any]:
        """Get complete integrated system state"""
        mechanical_state = self.get_mechanical_state()
        electrical_state = self.get_electrical_state()
        
        return {
            'time': self.current_time,
            'mechanical': mechanical_state,
            'electrical': electrical_state,
            'net_power': self.net_power,
            'overall_efficiency': self.overall_efficiency,
            'compressor_power': getattr(self, 'compressor_power', 0.0)
        }
        
    def get_angular_velocity(self) -> float:
        """Get angular velocity in rad/s"""
        return self.mechanical_system.get_angular_velocity()
        
    def get_angular_velocity_rpm(self) -> float:
        """Get angular velocity in RPM"""
        return self.mechanical_system.get_angular_velocity_rpm()
        
    def get_mechanical_power(self) -> float:
        """Get mechanical power in W"""
        return self.mechanical_system.get_mechanical_power()
        
    def get_electrical_power(self) -> float:
        """Get electrical power output in W"""
        return self.electrical_system.get_electrical_power()
        
    def get_net_power(self) -> float:
        """Get net power output (electrical - compressor) in W"""
        return self.net_power
        
    def get_efficiency(self) -> float:
        """Get overall system efficiency"""
        return self.overall_efficiency
