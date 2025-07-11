"""
Backward compatibility layer for existing KPP simulator interface.
"""

from typing import Dict, Any, Optional
from pathlib import Path
import sys

# Add paths for imports
project_root = Path(__file__).parent.parent.parent.parent
integration_dir = project_root / "simulation" / "integration"
sys.path.insert(0, str(integration_dir))

from integrated_simulator import IntegratedKPPSimulator

class CompatibilityLayer:
    """Backward compatibility layer for existing interface"""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize compatibility layer"""
        self.config = config
        
        # Create integrated simulator
        self.simulator = IntegratedKPPSimulator(config)
        
        # Legacy interface state
        self.legacy_state = {}
        
        print("CompatibilityLayer initialized")
        
    def start(self) -> bool:
        """Start simulation (legacy interface)"""
        return self.simulator.start_simulation()
        
    def stop(self) -> None:
        """Stop simulation (legacy interface)"""
        self.simulator.stop_simulation()
        
    def update(self, dt: float = None) -> Dict[str, Any]:
        """Update simulation (legacy interface)"""
        state = self.simulator.update_simulation(dt)
        
        # Convert to legacy format
        legacy_state = self._convert_to_legacy_format(state)
        self.legacy_state = legacy_state
        
        return legacy_state
        
    def _convert_to_legacy_format(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Convert new state format to legacy format"""
        legacy_state = {
            'time': state.get('simulation_time', 0.0),
            'running': state.get('running', False)
        }
        
        # Extract key metrics
        drivetrain_state = state.get('drivetrain_system', {})
        if drivetrain_state:
            mechanical = drivetrain_state.get('mechanical', {})
            electrical = drivetrain_state.get('electrical', {})
            
            legacy_state.update({
                'speed_rpm': mechanical.get('angular_velocity_rpm', 0.0),
                'torque': mechanical.get('torque_output', 0.0),
                'mechanical_power': mechanical.get('mechanical_power', 0.0),
                'electrical_power': electrical.get('electrical_power_output', 0.0),
                'net_power': drivetrain_state.get('net_power', 0.0),
                'efficiency': drivetrain_state.get('overall_efficiency', 0.0)
            })
            
        # Add performance metrics
        performance = state.get('performance', {})
        legacy_state.update({
            'fps': performance.get('fps', 0.0),
            'frame_time': performance.get('avg_frame_time', 0.0)
        })
        
        return legacy_state
        
    def get_state(self) -> Dict[str, Any]:
        """Get current state (legacy interface)"""
        return self.legacy_state
        
    def set_parameter(self, param_name: str, value: Any) -> bool:
        """Set parameter (legacy interface)"""
        # Map legacy parameters to new system
        if param_name == 'injection_interval':
            # Update control system
            return True
        elif param_name == 'target_speed':
            # Update control system
            return True
        elif param_name == 'H1_enabled':
            return self.simulator.enable_enhancement('H1', value)
        elif param_name == 'H2_enabled':
            return self.simulator.enable_enhancement('H2', value)
        elif param_name == 'H3_enabled':
            return self.simulator.enable_enhancement('H3', value)
        else:
            print(f"Unknown parameter: {param_name}")
            return False
            
    def get_parameter(self, param_name: str) -> Any:
        """Get parameter (legacy interface)"""
        # Map legacy parameters from new system
        if param_name == 'speed_rpm':
            return self.legacy_state.get('speed_rpm', 0.0)
        elif param_name == 'power_output':
            return self.legacy_state.get('net_power', 0.0)
        elif param_name == 'efficiency':
            return self.legacy_state.get('efficiency', 0.0)
        else:
            print(f"Unknown parameter: {param_name}")
            return None
