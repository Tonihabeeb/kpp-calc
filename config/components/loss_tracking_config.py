"""
Loss Tracking System Configuration
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional

@dataclass
class LossTrackingConfig:
    """Configuration for loss tracking system"""
    
    # Physics constants
    bearing_friction_coefficient: float = 0.001  # Default friction coefficient
    windage_coefficient: float = 0.1  # Default windage coefficient
    electrical_resistance: float = 0.1  # Default electrical resistance (ohms)
    thermal_conductivity: float = 50.0  # Default thermal conductivity (W/m·K)
    
    # System parameters
    time_step: float = 0.01  # Default time step (s)
    max_history_length: int = 1000  # Maximum number of history entries
    
    # Optimization thresholds
    min_efficiency_threshold: float = 0.8  # Minimum acceptable efficiency
    max_temperature_rise: float = 50.0  # Maximum acceptable temperature rise (K)
    mechanical_loss_threshold: float = 0.4  # Threshold for mechanical loss warnings
    electrical_loss_threshold: float = 0.3  # Threshold for electrical loss warnings
    thermal_loss_threshold: float = 0.2  # Threshold for thermal loss warnings
    
    # Component-specific parameters
    bearing_diameter: float = 0.05  # Default bearing diameter (m)
    generator_radius: float = 0.2  # Default generator radius (m)
    generator_length: float = 0.1  # Default generator length (m)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        return {
            'bearing_friction_coefficient': self.bearing_friction_coefficient,
            'windage_coefficient': self.windage_coefficient,
            'electrical_resistance': self.electrical_resistance,
            'thermal_conductivity': self.thermal_conductivity,
            'time_step': self.time_step,
            'max_history_length': self.max_history_length,
            'min_efficiency_threshold': self.min_efficiency_threshold,
            'max_temperature_rise': self.max_temperature_rise,
            'mechanical_loss_threshold': self.mechanical_loss_threshold,
            'electrical_loss_threshold': self.electrical_loss_threshold,
            'thermal_loss_threshold': self.thermal_loss_threshold,
            'bearing_diameter': self.bearing_diameter,
            'generator_radius': self.generator_radius,
            'generator_length': self.generator_length
        }
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'LossTrackingConfig':
        """Create configuration from dictionary"""
        return cls(**{
            k: v for k, v in config_dict.items()
            if k in cls.__dataclass_fields__
        })

def create_default_config() -> LossTrackingConfig:
    """Create default loss tracking configuration"""
    return LossTrackingConfig()

def create_high_efficiency_config() -> LossTrackingConfig:
    """Create configuration optimized for high efficiency"""
    return LossTrackingConfig(
        bearing_friction_coefficient=0.0005,  # Lower friction
        windage_coefficient=0.05,  # Lower windage losses
        electrical_resistance=0.05,  # Lower electrical resistance
        thermal_conductivity=100.0,  # Better heat dissipation
        min_efficiency_threshold=0.9,  # Higher efficiency requirement
        max_temperature_rise=30.0  # Stricter temperature control
    )

def create_high_power_config() -> LossTrackingConfig:
    """Create configuration optimized for high power operation"""
    return LossTrackingConfig(
        bearing_friction_coefficient=0.002,  # Higher friction tolerance
        windage_coefficient=0.15,  # Higher windage tolerance
        electrical_resistance=0.15,  # Higher resistance tolerance
        thermal_conductivity=75.0,  # Enhanced heat dissipation
        min_efficiency_threshold=0.75,  # Lower efficiency requirement
        max_temperature_rise=60.0,  # Higher temperature tolerance
        mechanical_loss_threshold=0.5,  # Higher mechanical loss tolerance
        electrical_loss_threshold=0.4,  # Higher electrical loss tolerance
        thermal_loss_threshold=0.3  # Higher thermal loss tolerance
    ) 