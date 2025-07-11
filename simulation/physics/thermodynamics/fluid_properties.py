"""
Fluid properties using CoolProp for accurate thermophysical data.
"""

import numpy as np
from typing import Dict, Any, Optional
import CoolProp.CoolProp as CP

class FluidProperties:
    """Fluid properties calculator using CoolProp"""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize fluid properties calculator"""
        self.config = config
        
        # Reference conditions
        self.water_reference_temp = config.get('water_reference_temp', 293.15)  # K
        self.water_reference_pressure = config.get('water_reference_pressure', 101325.0)  # Pa
        self.air_reference_temp = config.get('air_reference_temp', 293.15)  # K
        self.air_reference_pressure = config.get('air_reference_pressure', 101325.0)  # Pa
        
        # Property caching
        self.enable_cache = config.get('enable_property_cache', True)
        self.cache_size = config.get('cache_size', 1000)
        self.cache_ttl = config.get('cache_ttl', 3600.0)  # seconds
        
        # Initialize cache
        self.property_cache = {}
        
        # Error handling
        self.fallback_to_constants = config.get('fallback_to_constants', True)
        self.max_error = config.get('max_property_error', 0.05)  # 5%
        
        print("FluidProperties initialized with CoolProp")
        
    def get_water_density(self, temperature: float, pressure: float) -> float:
        """Get water density at given temperature and pressure"""
        try:
            # Use CoolProp to get water density
            density = CP.PropsSI('D', 'T', temperature, 'P', pressure, 'Water')
            return density
        except Exception as e:
            print(f"CoolProp error for water density: {e}")
            if self.fallback_to_constants:
                # Fallback to constant density at reference conditions
                return 998.2  # kg/m^3 at 20C
            else:
                raise e
                
    def get_water_viscosity(self, temperature: float, pressure: float) -> float:
        """Get water viscosity at given temperature and pressure"""
        try:
            # Use CoolProp to get water viscosity
            viscosity = CP.PropsSI('V', 'T', temperature, 'P', pressure, 'Water')
            return viscosity
        except Exception as e:
            print(f"CoolProp error for water viscosity: {e}")
            if self.fallback_to_constants:
                # Fallback to constant viscosity at reference conditions
                return 1.0e-3  # Pa*s at 20C
            else:
                raise e
                
    def get_air_density(self, temperature: float, pressure: float) -> float:
        """Get air density at given temperature and pressure"""
        try:
            # Use CoolProp to get air density
            density = CP.PropsSI('D', 'T', temperature, 'P', pressure, 'Air')
            return density
        except Exception as e:
            print(f"CoolProp error for air density: {e}")
            if self.fallback_to_constants:
                # Fallback to constant density at reference conditions
                return 1.204  # kg/m^3 at 20C
            else:
                raise e
                
    def get_air_viscosity(self, temperature: float, pressure: float) -> float:
        """Get air viscosity at given temperature and pressure"""
        try:
            # Use CoolProp to get air viscosity
            viscosity = CP.PropsSI('V', 'T', temperature, 'P', pressure, 'Air')
            return viscosity
        except Exception as e:
            print(f"CoolProp error for air viscosity: {e}")
            if self.fallback_to_constants:
                # Fallback to constant viscosity at reference conditions
                return 1.8e-5  # Pa*s at 20C
            else:
                raise e
                
    def get_fluid_properties(self, fluid: str, temperature: float, pressure: float) -> Dict[str, float]:
        """Get comprehensive fluid properties"""
        if fluid.lower() == 'water':
            return {
                'density': self.get_water_density(temperature, pressure),
                'viscosity': self.get_water_viscosity(temperature, pressure),
                'temperature': temperature,
                'pressure': pressure
            }
        elif fluid.lower() == 'air':
            return {
                'density': self.get_air_density(temperature, pressure),
                'viscosity': self.get_air_viscosity(temperature, pressure),
                'temperature': temperature,
                'pressure': pressure
            }
        else:
            raise ValueError(f"Unknown fluid: {fluid}")
            
    def validate_properties(self, properties: Dict[str, float], fluid: str) -> bool:
        """Validate fluid properties against expected ranges"""
        if fluid.lower() == 'water':
            # Check density range (0-100C)
            if not (950 <= properties['density'] <= 1000):
                return False
            # Check viscosity range
            if not (0.3e-3 <= properties['viscosity'] <= 1.8e-3):
                return False
        elif fluid.lower() == 'air':
            # Check density range (0-100C)
            if not (0.9 <= properties['density'] <= 1.3):
                return False
            # Check viscosity range
            if not (1.5e-5 <= properties['viscosity'] <= 2.2e-5):
                return False
                
        return True
