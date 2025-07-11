"""
Thermodynamics configuration for KPP simulator.
"""

from dataclasses import dataclass
from typing import Optional

@dataclass
class ThermodynamicsConfig:
    """Configuration for thermodynamic calculations"""
    
    # Fluid properties
    water_reference_temp: float = 293.15  # K (20C)
    water_reference_pressure: float = 101325.0  # Pa (1 atm)
    air_reference_temp: float = 293.15  # K (20C)
    air_reference_pressure: float = 101325.0  # Pa (1 atm)
    
    # Property caching
    enable_property_cache: bool = True
    cache_size: int = 1000
    cache_ttl: float = 3600.0  # seconds
    
    # H2 enhancement settings
    h2_thermal_expansion_coeff: float = 0.0034  # /K for air
    h2_heat_transfer_coeff: float = 1000.0  # W/m^2*K
    
    # Error handling
    fallback_to_constants: bool = True
    max_property_error: float = 0.05  # 5% error tolerance
