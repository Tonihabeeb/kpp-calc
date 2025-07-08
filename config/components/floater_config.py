import logging
from typing import Any, Dict
from dataclasses import dataclass, field
from ..core.base_config import BaseConfig
"""
Floater-specific configuration for the KPP simulator.
"""

@dataclass
class FloaterConfig(BaseConfig):
    """Floater system configuration parameters"""
    
    # Physical properties
    mass_empty: float = 10.0  # kg
    volume: float = 0.4  # m³
    radius: float = 0.1  # m
    height: float = 0.5  # m
    material_density: float = 2500.0  # kg/m³
    
    # Pressure settings
    max_pressure: float = 500000.0  # Pa
    min_pressure: float = 100000.0  # Pa
    target_pressure: float = 300000.0  # Pa
    pressure_tolerance: float = 10000.0  # Pa
    
    # Thermal properties
    thermal_conductivity: float = 50.0  # W/m·K
    specific_heat: float = 900.0  # J/kg·K
    max_temperature: float = 373.15  # K (100°C)
    min_temperature: float = 273.15  # K (0°C)
    
    # Buoyancy settings
    water_density: float = 1000.0  # kg/m³
    air_density: float = 1.225  # kg/m³
    gravity: float = 9.81  # m/s²
    
    # Control parameters
    fill_rate: float = 0.1  # m³/s
    empty_rate: float = 0.1  # m³/s
    state_transition_time: float = 5.0  # seconds
    error_threshold: int = 3  # consecutive errors
    
    # Performance limits
    max_velocity: float = 10.0  # m/s
    max_acceleration: float = 20.0  # m/s²
    max_force: float = 10000.0  # N
    
    # Validation settings
    validation_enabled: bool = True
    strict_validation: bool = False
    
    def validate(self) -> None:
        """Validate floater configuration parameters"""
        super().validate()
        
        if self.mass_empty <= 0:
            raise ValueError("mass_empty must be positive")
        if self.volume <= 0:
            raise ValueError("volume must be positive")
        if self.radius <= 0:
            raise ValueError("radius must be positive")
        if self.height <= 0:
            raise ValueError("height must be positive")
        if self.max_pressure <= self.min_pressure:
            raise ValueError("max_pressure must be greater than min_pressure")
        if self.max_temperature <= self.min_temperature:
            raise ValueError("max_temperature must be greater than min_temperature")
        if self.fill_rate <= 0:
            raise ValueError("fill_rate must be positive")
        if self.empty_rate <= 0:
            raise ValueError("empty_rate must be positive")

