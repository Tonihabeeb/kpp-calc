"""
Fluid dynamics configuration for KPP simulator.
"""

from dataclasses import dataclass
from typing import Optional

@dataclass
class FluidConfig:
    """Configuration for fluid dynamics calculations"""
    
    # Water properties
    water_density: float = 1000.0  # kg/m³
    water_viscosity: float = 1.0e-3  # Pa·s
    water_temperature: float = 293.15  # K
    
    # Drag modeling
    drag_coefficient: float = 0.8
    enable_reynolds_dependent_drag: bool = True
    reynolds_threshold: float = 2300.0
    
    # H1 enhancement settings
    h1_nanobubble_fraction: float = 0.2
    h1_density_reduction: float = 0.1
    h1_drag_reduction: float = 0.15
    
    # Turbulence modeling
    enable_turbulence: bool = False
    turbulence_intensity: float = 0.05
    
    # Performance settings
    enable_drag_cache: bool = True
    drag_cache_size: int = 500
