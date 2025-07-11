"""
Force application system for KPP simulator.
"""

import numpy as np
from typing import Dict, Any

class ForceApplicator:
    """System for applying forces to floaters"""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize force applicator"""
        self.config = config
        self.water_density = config.get('water_density', 1000.0)
        self.gravity = 9.81
        
        print("ForceApplicator initialized")
        
    def calculate_buoyancy_force(self, floater_body, water_level: float) -> np.ndarray:
        """Calculate buoyancy force on floater"""
        position = floater_body.get_position()
        volume = floater_body.volume
        
        # Calculate submerged volume
        if position[1] < water_level:
            # Floater is submerged
            submerged_volume = volume
        else:
            # Floater is partially submerged or above water
            submerged_volume = 0.0
            
        # Buoyancy force = rho * V * g
        buoyancy_magnitude = self.water_density * submerged_volume * self.gravity
        buoyancy_force = np.array([0.0, buoyancy_magnitude, 0.0])
        
        return buoyancy_force
        
    def calculate_drag_force(self, floater_body, fluid_velocity: np.ndarray) -> np.ndarray:
        """Calculate drag force on floater"""
        velocity = floater_body.get_velocity()
        relative_velocity = velocity - fluid_velocity
        
        # Simplified drag calculation
        # F_drag = 0.5 * rho * C_d * A * v^2
        drag_coefficient = 0.8
        cross_sectional_area = np.pi * floater_body.radius**2
        
        velocity_magnitude = np.linalg.norm(relative_velocity)
        if velocity_magnitude > 0:
            drag_magnitude = 0.5 * self.water_density * drag_coefficient * cross_sectional_area * velocity_magnitude**2
            drag_direction = -relative_velocity / velocity_magnitude
            drag_force = drag_direction * drag_magnitude
        else:
            drag_force = np.array([0.0, 0.0, 0.0])
            
        return drag_force
        
    def apply_forces_to_floater(self, floater_body, water_level: float, 
                               fluid_velocity: np.ndarray) -> None:
        """Apply all forces to a floater"""
        # Calculate forces
        buoyancy_force = self.calculate_buoyancy_force(floater_body, water_level)
        drag_force = self.calculate_drag_force(floater_body, fluid_velocity)
        
        # Apply forces
        floater_body.apply_force(buoyancy_force)
        floater_body.apply_force(drag_force)
        
        # Apply gravitational force
        gravity_force = np.array([0.0, -floater_body.mass * self.gravity, 0.0])
        floater_body.apply_force(gravity_force)
