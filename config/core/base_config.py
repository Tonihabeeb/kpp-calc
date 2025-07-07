"""
Base configuration classes for the KPP simulator.
Provides type-safe configuration with validation.
"""

import logging
from dataclasses import asdict, dataclass
from typing import Any, Dict

logger = logging.getLogger(__name__)


@dataclass
class BaseConfig:
    """Base configuration class with common validation and utilities (dataclass version)"""

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        """Create configuration from dictionary"""
        # Filter data to only include fields that exist in the dataclass
        if hasattr(cls, '__dataclass_fields__'):
            field_names = set(cls.__dataclass_fields__.keys())
            filtered_data = {k: v for k, v in data.items() if k in field_names}
            return cls(**filtered_data)
        else:
            # Fallback for non-dataclass cases
            return cls(**data)

    def update(self, **kwargs) -> None:
        """Update configuration with new values"""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
            else:
                logger.warning(f"Unknown configuration key: {key}")

    def validate_physics_constraints(self) -> bool:
        """Validate physics constraints (to be overridden by subclasses)"""
        return True

    def get_validation_errors(self) -> list[str]:
        """Get list of validation errors"""
        try:
            self.validate_physics_constraints()
            return []
        except Exception as e:
            return [str(e)]

    def is_valid(self) -> bool:
        """Check if configuration is valid"""
        return len(self.get_validation_errors()) == 0


@dataclass
class SimulationConfig(BaseConfig):
    """Base configuration for simulation parameters"""

    # Simulation timing
    time_step: float = 0.01  # Simulation time step in seconds
    max_time: float = 3600.0  # Maximum simulation time in seconds

    # Physics settings
    gravity: float = 9.81  # Gravitational acceleration in m/s²
    water_density: float = 1000.0  # Water density in kg/m³
    air_density: float = 1.225  # Air density in kg/m³

    # Tank dimensions
    tank_height: float = 10.0  # Tank height in meters
    tank_diameter: float = 2.0  # Tank diameter in meters

    # Remove Pydantic validators; validation can be handled in validate_physics_constraints if needed
