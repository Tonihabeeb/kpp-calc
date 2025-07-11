"""
Floater physics model using PyChrono rigid bodies.
"""

import numpy as np
from typing import Dict, Any, Optional

class FloaterBody:
    """Floater as PyChrono rigid body"""
    
    def __init__(self, config: Dict[str, Any], floater_id: int):
        """Initialize floater body"""
        self.config = config
        self.floater_id = floater_id
        
        # Set mass and inertia
        self.mass = config.get('mass', 10.0)
        self.volume = config.get('volume', 0.4)
        self.radius = config.get('radius', 0.1)
        
        # Calculate inertia for cylinder
        height = self.volume / (np.pi * self.radius**2)
        self.inertia_xx = (1/12) * self.mass * (3 * self.radius**2 + height**2)
        self.inertia_yy = (1/12) * self.mass * (3 * self.radius**2 + height**2)
        self.inertia_zz = (1/2) * self.mass * self.radius**2
        
        # Set initial position and velocity
        initial_pos = config.get('initial_position', [0, 0, 0])
        self.position = np.array(initial_pos, dtype=np.float64)
        self.velocity = np.array([0.0, 0.0, 0.0], dtype=np.float64)
        self.acceleration = np.array([0.0, 0.0, 0.0], dtype=np.float64)
        
        # Store properties
        self.height = height
        
        # Applied forces
        self.applied_forces = []
        
        print(f"FloaterBody {floater_id} initialized")
        
    def apply_force(self, force: np.ndarray, point: 'Optional[np.ndarray]' = None) -> None:
        """Apply force to floater"""
        if point is None:
            point = np.array([0.0, 0.0, 0.0])
        
        # Store force for physics update
        self.applied_forces.append({
            'force': force,
            'point': point
        })
        
    def update(self, dt: float) -> None:
        """Update floater physics for one time step"""
        # Calculate net force
        net_force = np.array([0.0, 0.0, 0.0])
        for force_data in self.applied_forces:
            net_force += force_data['force']
        
        # Clear applied forces
        self.applied_forces = []
        
        # Calculate acceleration (F = ma)
        self.acceleration = net_force / self.mass
        
        # Update velocity (v = v0 + a*t)
        self.velocity += self.acceleration * dt
        
        # Update position (x = x0 + v*t)
        self.position += self.velocity * dt
        
    def get_position(self) -> np.ndarray:
        """Get current position"""
        return self.position.copy()
        
    def get_velocity(self) -> np.ndarray:
        """Get current velocity"""
        return self.velocity.copy()
        
    def get_state(self) -> Dict[str, Any]:
        """Get current state"""
        return {
            'floater_id': self.floater_id,
            'position': self.position.tolist(),
            'velocity': self.velocity.tolist(),
            'mass': self.mass,
            'volume': self.volume,
            'radius': self.radius
        }
