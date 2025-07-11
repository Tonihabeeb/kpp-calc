"""
Enhanced drag modeling with Reynolds number dependence.
"""

import numpy as np
from typing import Dict, Any, Optional

class EnhancedDragModel:
    """Enhanced drag model with Reynolds number dependence"""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize enhanced drag model"""
        self.config = config
        
        # Drag coefficient settings
        self.base_drag_coefficient = config.get('drag_coefficient', 0.8)
        self.enable_reynolds_dependent = config.get('enable_reynolds_dependent_drag', True)
        self.reynolds_threshold = config.get('reynolds_threshold', 2300.0)
        
        # Turbulence settings
        self.enable_turbulence = config.get('enable_turbulence', False)
        self.turbulence_intensity = config.get('turbulence_intensity', 0.05)
        
        # Performance settings
        self.enable_cache = config.get('enable_drag_cache', True)
        self.cache_size = config.get('drag_cache_size', 500)
        
        # Initialize cache
        self.drag_cache = {}
        
        print("EnhancedDragModel initialized")
        
    def calculate_reynolds_number(self, velocity: float, characteristic_length: float, 
                                density: float, viscosity: float) -> float:
        """Calculate Reynolds number"""
        if viscosity == 0:
            return 0.0
        return abs(velocity) * characteristic_length * density / viscosity
        
    def get_drag_coefficient(self, reynolds_number: float) -> float:
        """Get drag coefficient based on Reynolds number"""
        if not self.enable_reynolds_dependent:
            return self.base_drag_coefficient
            
        # Simplified Reynolds-dependent drag coefficient
        # For laminar flow (Re < 2300)
        if reynolds_number < self.reynolds_threshold:
            # Laminar flow - drag coefficient decreases with Re
            if reynolds_number < 1:
                return 24.0  # Stokes flow
            else:
                return 24.0 / reynolds_number
        else:
            # Turbulent flow - drag coefficient is roughly constant
            return self.base_drag_coefficient
            
    def calculate_drag_force(self, velocity: np.ndarray, characteristic_length: float,
                           cross_sectional_area: float, density: float, 
                           viscosity: float) -> np.ndarray:
        """Calculate drag force with enhanced modeling"""
        
        # Calculate velocity magnitude
        velocity_magnitude = np.linalg.norm(velocity)
        
        if velocity_magnitude == 0:
            return np.array([0.0, 0.0, 0.0])
            
        # Calculate Reynolds number
        reynolds_number = self.calculate_reynolds_number(
            velocity_magnitude, characteristic_length, density, viscosity
        )
        
        # Get drag coefficient
        drag_coefficient = self.get_drag_coefficient(reynolds_number)
        
        # Calculate drag force magnitude
        drag_magnitude = 0.5 * density * drag_coefficient * cross_sectional_area * velocity_magnitude**2
        
        # Calculate drag direction (opposite to velocity)
        drag_direction = -velocity / velocity_magnitude
        
        # Apply drag force
        drag_force = drag_direction * drag_magnitude
        
        # Add turbulence effects if enabled
        if self.enable_turbulence:
            turbulence_force = self.calculate_turbulence_force(velocity, density, cross_sectional_area)
            drag_force += turbulence_force
            
        return drag_force
        
    def calculate_turbulence_force(self, velocity: np.ndarray, density: float, 
                                 cross_sectional_area: float) -> np.ndarray:
        """Calculate additional force due to turbulence"""
        # Simplified turbulence model
        velocity_magnitude = np.linalg.norm(velocity)
        
        # Turbulence force is proportional to velocity squared and turbulence intensity
        turbulence_magnitude = 0.5 * density * self.turbulence_intensity * cross_sectional_area * velocity_magnitude**2
        
        # Random direction for turbulence
        random_direction = np.random.randn(3)
        random_direction = random_direction / np.linalg.norm(random_direction)
        
        return random_direction * turbulence_magnitude
        
    def get_drag_force_simple(self, velocity: np.ndarray, cross_sectional_area: float,
                            density: float) -> np.ndarray:
        """Calculate drag force using simple model (for backward compatibility)"""
        velocity_magnitude = np.linalg.norm(velocity)
        
        if velocity_magnitude == 0:
            return np.array([0.0, 0.0, 0.0])
            
        drag_magnitude = 0.5 * density * self.base_drag_coefficient * cross_sectional_area * velocity_magnitude**2
        drag_direction = -velocity / velocity_magnitude
        
        return drag_direction * drag_magnitude
