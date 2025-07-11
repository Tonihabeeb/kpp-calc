"""
Integration layer between PyChrono and existing floater system.
"""

from typing import Dict, Any, List
import numpy as np
from chrono_system import ChronoSystem
from floater_body import FloaterBody
from chain_system import ChainSystem
from force_applicator import ForceApplicator

class ChronoIntegrationLayer:
    """Integration layer for PyChrono physics"""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize integration layer"""
        self.config = config
        
        # Initialize PyChrono components
        self.chrono_system = ChronoSystem(config.get('chrono', {}))
        self.chain_system = ChainSystem(config.get('chain', {}))
        self.force_applicator = ForceApplicator(config.get('forces', {}))
        
        # Store floaters
        self.floaters = []
        
        # Simulation state
        self.water_level = config.get('water_level', 0.0)
        self.fluid_velocity = np.array([0.0, 0.0, 0.0])
        
        print("ChronoIntegrationLayer initialized")
        
    def create_floater(self, floater_config: Dict[str, Any], floater_id: int) -> FloaterBody:
        """Create a new floater with PyChrono physics"""
        floater_body = FloaterBody(floater_config, floater_id)
        self.chrono_system.add_body(floater_body)
        self.floaters.append(floater_body)
        
        # Add to chain system
        angle = 2 * np.pi * floater_id / len(self.floaters) if self.floaters else 0
        self.chain_system.add_floater_constraint(floater_body, angle)
        
        return floater_body
        
    def update_simulation(self, dt: float) -> None:
        """Update simulation for one time step"""
        # Apply forces to all floaters
        for floater in self.floaters:
            self.force_applicator.apply_forces_to_floater(floater, self.water_level, self.fluid_velocity)
            
        # Update chain physics
        self.chain_system.update_chain_physics(dt)
        
        # Step simulation
        self.chrono_system.step(dt)
        
    def get_floater_states(self) -> List[Dict[str, Any]]:
        """Get states of all floaters"""
        return [floater.get_state() for floater in self.floaters]
        
    def get_system_state(self) -> Dict[str, Any]:
        """Get overall system state"""
        return {
            'chrono_state': self.chrono_system.get_system_state(),
            'chain_velocity': self.chain_system.get_chain_velocity(),
            'chain_tension': self.chain_system.get_chain_tension(),
            'num_floaters': len(self.floaters)
        }
        
    def apply_torque_to_chain(self, torque: float) -> None:
        """Apply torque to the chain system"""
        self.chain_system.apply_torque_to_sprocket(torque)
        
    def set_water_level(self, level: float) -> None:
        """Set water level for buoyancy calculations"""
        self.water_level = level
        
    def set_fluid_velocity(self, velocity: np.ndarray) -> None:
        """Set fluid velocity for drag calculations"""
        self.fluid_velocity = velocity
