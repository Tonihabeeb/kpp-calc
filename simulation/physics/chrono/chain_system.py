"""
Chain system for KPP simulator using PyChrono constraints.
"""

import numpy as np
from typing import List, Dict, Any

class ChainSystem:
    """Chain system with sprockets and constraints"""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize chain system"""
        self.config = config
        self.chain_radius = config.get('chain_radius', 1.0)
        
        # Create sprocket bodies
        self.top_sprocket = self._create_sprocket("top_sprocket", [0, 5, 0])
        self.bottom_sprocket = self._create_sprocket("bottom_sprocket", [0, -5, 0])
        
        # Store constraints
        self.constraints = []
        
        # Chain state
        self.chain_velocity = 0.0
        self.chain_tension = 0.0
        
        print("ChainSystem initialized")
        
    def _create_sprocket(self, name: str, position: List[float]):
        """Create sprocket body"""
        sprocket = {
            'name': name,
            'position': np.array(position),
            'mass': 10.0,
            'inertia': np.array([1.0, 1.0, 1.0]),
            'angular_velocity': 0.0,
            'angular_position': 0.0
        }
        return sprocket
        
    def add_floater_constraint(self, floater_body, angle: float) -> None:
        """Add floater to chain with constraint"""
        # Create constraint data
        constraint = {
            'floater': floater_body,
            'angle': angle,
            'type': 'revolute'
        }
        
        self.constraints.append(constraint)
        
    def update_chain_physics(self, dt: float) -> None:
        """Update chain physics"""
        # Calculate chain velocity from sprocket rotation
        self.chain_velocity = self.top_sprocket['angular_velocity'] * self.chain_radius
        
        # Update sprocket positions based on chain motion
        # This is a simplified model - will be enhanced with PyChrono
        
    def get_chain_velocity(self) -> float:
        """Get chain linear velocity"""
        return self.chain_velocity
        
    def get_chain_tension(self) -> float:
        """Calculate chain tension from forces"""
        # Simplified tension calculation
        # In practice, this would be more complex with PyChrono
        return self.chain_tension
        
    def apply_torque_to_sprocket(self, torque: float, sprocket_name: str = "top_sprocket") -> None:
        """Apply torque to sprocket"""
        if sprocket_name == "top_sprocket":
            sprocket = self.top_sprocket
        else:
            sprocket = self.bottom_sprocket
            
        # Calculate angular acceleration (torque = I * alpha)
        angular_acceleration = torque / sprocket['inertia'][2]
        
        # Update angular velocity
        sprocket['angular_velocity'] += angular_acceleration * 0.02  # Assume 20ms timestep
        
        # Update angular position
        sprocket['angular_position'] += sprocket['angular_velocity'] * 0.02
