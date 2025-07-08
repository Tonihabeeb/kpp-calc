import logging
from dataclasses import dataclass, field
from ..core.base_config import BaseConfig

"""
Electrical system configuration for the KPP simulator.
"""

@dataclass
class ElectricalConfig(BaseConfig):
    """Electrical system configuration parameters"""
    
    # Generator settings
    rated_power: float = 50000.0  # W (50 kW)
    rated_voltage: float = 400.0  # V (3-phase)
    rated_frequency: float = 50.0  # Hz
    rated_speed: float = 1500.0  # RPM
    rated_torque: float = 318.3  # N·m
    number_of_poles: int = 4
    
    # Electrical parameters
    stator_resistance: float = 0.1  # Ω
    rotor_resistance: float = 0.05  # Ω (for induction)
    stator_reactance: float = 0.5  # Ω
    rotor_reactance: float = 0.3  # Ω (for induction)
    magnetizing_reactance: float = 10.0  # Ω
    
    # Grid settings
    grid_voltage: float = 400.0  # V
    grid_frequency: float = 50.0  # Hz
    grid_impedance: float = 0.1  # Ω
    
    # Power electronics
    power_electronics_efficiency: float = 0.98
    switching_frequency: float = 10000.0  # Hz (10 kHz)
    power_factor_nominal: float = 0.99
    
    # Protection and limits
    max_current: float = 100.0  # A
    max_temperature: float = 353.15  # K (80°C)
    overcurrent_protection: bool = True
    overvoltage_protection: bool = True
    undervoltage_protection: bool = True
    
    # Control parameters
    voltage_regulation_enabled: bool = True
    frequency_regulation_enabled: bool = True
    power_factor_correction: bool = True
    grid_synchronization: bool = True
    
    # Performance settings
    moment_of_inertia: float = 2.0  # kg·m²
    copper_loss_coefficient: float = 0.02  # W/K
    iron_loss_coefficient: float = 0.01  # W/K
    mechanical_loss_coefficient: float = 0.005  # W/K
    
    # Engagement settings
    electrical_engagement_threshold: float = 2000.0  # W
    engagement_hysteresis: float = 500.0  # W
    startup_time: float = 5.0  # seconds
    
    def validate(self) -> None:
        """Validate electrical configuration parameters"""
        super().validate()
        
        if self.rated_power <= 0:
            raise ValueError("rated_power must be positive")
        if self.rated_voltage <= 0:
            raise ValueError("rated_voltage must be positive")
        if self.rated_frequency <= 0:
            raise ValueError("rated_frequency must be positive")
        if self.rated_speed <= 0:
            raise ValueError("rated_speed must be positive")
        if self.number_of_poles <= 0:
            raise ValueError("number_of_poles must be positive")
        if self.max_current <= 0:
            raise ValueError("max_current must be positive")
        if self.max_temperature <= 273.15:
            raise ValueError("max_temperature must be above freezing")
        if self.power_electronics_efficiency <= 0 or self.power_electronics_efficiency > 1:
            raise ValueError("power_electronics_efficiency must be between 0 and 1")

