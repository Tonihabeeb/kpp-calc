"""
Enhanced environment integration with CoolProp and H1 enhancement.
"""

from typing import Dict, Any, Optional
import numpy as np
from fluid_properties import FluidProperties
from drag_model import EnhancedDragModel
from h1_enhancement import H1Enhancement

class EnhancedEnvironment:
    """Enhanced environment with CoolProp and H1 enhancement"""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize enhanced environment"""
        self.config = config
        
        # Initialize components
        self.fluid_properties = FluidProperties(config.get('thermodynamics', {}))
        self.drag_model = EnhancedDragModel(config.get('drag', {}))
        self.h1_enhancement = H1Enhancement(config.get('h1', {}))
        
        # Environment state
        self.water_temperature = config.get('water_temperature', 293.15)  # K
        self.water_pressure = config.get('water_pressure', 101325.0)  # Pa
        self.air_temperature = config.get('air_temperature', 293.15)  # K
        self.air_pressure = config.get('air_pressure', 101325.0)  # Pa
        
        # Fluid velocity field
        self.fluid_velocity = np.array([0.0, 0.0, 0.0])
        
        print("EnhancedEnvironment initialized")
        
    def get_water_properties(self) -> Dict[str, float]:
        """Get water properties with H1 enhancement"""
        # Get base properties from CoolProp
        base_properties = self.fluid_properties.get_fluid_properties(
            'water', self.water_temperature, self.water_pressure
        )
        
        # Apply H1 enhancement
        if self.h1_enhancement.enabled:
            base_properties['density'] = self.h1_enhancement.get_effective_density(
                base_properties['density']
            )
            
        return base_properties
        
    def get_air_properties(self) -> Dict[str, float]:
        """Get air properties"""
        return self.fluid_properties.get_fluid_properties(
            'air', self.air_temperature, self.air_pressure
        )
        
    def calculate_buoyancy_force(self, volume: float, position: np.ndarray, 
                               water_level: float) -> np.ndarray:
        """Calculate buoyancy force with enhanced fluid properties"""
        # Get water properties
        water_props = self.get_water_properties()
        water_density = water_props['density']
        
        # Calculate submerged volume
        if position[1] < water_level:
            submerged_volume = volume
        else:
            submerged_volume = 0.0
            
        # Buoyancy force = rho * V * g
        gravity = 9.81
        buoyancy_magnitude = water_density * submerged_volume * gravity
        buoyancy_force = np.array([0.0, buoyancy_magnitude, 0.0])
        
        return buoyancy_force
        
    def calculate_drag_force(self, velocity: np.ndarray, characteristic_length: float,
                           cross_sectional_area: float) -> np.ndarray:
        """Calculate drag force with enhanced modeling"""
        # Get water properties
        water_props = self.get_water_properties()
        water_density = water_props['density']
        water_viscosity = water_props['viscosity']
        
        # Get effective drag coefficient with H1 enhancement
        base_drag_coeff = self.drag_model.base_drag_coefficient
        effective_drag_coeff = self.h1_enhancement.get_effective_drag_coefficient(base_drag_coeff)
        
        # Calculate relative velocity
        relative_velocity = velocity - self.fluid_velocity
        
        # Use enhanced drag model
        drag_force = self.drag_model.calculate_drag_force(
            relative_velocity, characteristic_length, cross_sectional_area,
            water_density, water_viscosity
        )
        
        return drag_force
        
    def set_water_temperature(self, temperature: float) -> None:
        """Set water temperature"""
        self.water_temperature = temperature
        
    def set_water_pressure(self, pressure: float) -> None:
        """Set water pressure"""
        self.water_pressure = pressure
        
    def set_fluid_velocity(self, velocity: np.ndarray) -> None:
        """Set fluid velocity field"""
        self.fluid_velocity = velocity
        
    def enable_h1(self) -> None:
        """Enable H1 enhancement"""
        self.h1_enhancement.enable()
        
    def disable_h1(self) -> None:
        """Disable H1 enhancement"""
        self.h1_enhancement.disable()
        
    def set_h1_fraction(self, fraction: float) -> None:
        """Set H1 nanobubble fraction"""
        self.h1_enhancement.set_nanobubble_fraction(fraction)
        
    def get_environment_state(self) -> Dict[str, Any]:
        """Get current environment state"""
        water_props = self.get_water_properties()
        air_props = self.get_air_properties()
        
        return {
            'water_temperature': self.water_temperature,
            'water_pressure': self.water_pressure,
            'water_density': water_props['density'],
            'water_viscosity': water_props['viscosity'],
            'air_temperature': self.air_temperature,
            'air_pressure': self.air_pressure,
            'air_density': air_props['density'],
            'air_viscosity': air_props['viscosity'],
            'fluid_velocity': self.fluid_velocity.tolist(),
            'h1_status': self.h1_enhancement.get_status()
        }
