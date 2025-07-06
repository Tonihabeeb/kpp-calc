"""
IntegratedDrivetrain configuration for the KPP simulator.
Defines parameters for the integrated integrated_drivetrain system.
"""

from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass
class DrivetrainConfig:
    """Configuration for the integrated integrated_drivetrain system."""

    # Sprocket parameters
    sprocket_radius: float = field(default=1.0, metadata={"description": "Sprocket radius in meters", "unit": "m"})
    sprocket_teeth: int = field(default=20, metadata={"description": "Number of sprocket teeth"})

    # Flywheel parameters
    flywheel_inertia: float = field(
        default=500.0, metadata={"description": "Flywheel moment of inertia", "unit": "kg·m²"}
    )
    flywheel_max_speed: float = field(
        default=400.0, metadata={"description": "Maximum flywheel speed", "unit": "rad/s"}
    )
    flywheel_mass: float = field(default=1000.0, metadata={"description": "Flywheel mass", "unit": "kg"})

    # Target speeds
    target_generator_speed: float = field(
        default=375.0, metadata={"description": "Target generator speed", "unit": "RPM"}
    )

    # Clutch parameters
    clutch_engagement_threshold: float = field(
        default=0.1, metadata={"description": "Clutch engagement threshold", "unit": "rad/s"}
    )
    clutch_disengagement_threshold: float = field(
        default=-0.05, metadata={"description": "Clutch disengagement threshold", "unit": "rad/s"}
    )
    clutch_max_torque: float = field(default=15000.0, metadata={"description": "Maximum clutch torque", "unit": "N·m"})

    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary."""
        return {
            "sprocket_radius": self.sprocket_radius,
            "sprocket_teeth": self.sprocket_teeth,
            "flywheel_inertia": self.flywheel_inertia,
            "flywheel_max_speed": self.flywheel_max_speed,
            "flywheel_mass": self.flywheel_mass,
            "target_generator_speed": self.target_generator_speed,
            "clutch_engagement_threshold": self.clutch_engagement_threshold,
            "clutch_disengagement_threshold": self.clutch_disengagement_threshold,
            "clutch_max_torque": self.clutch_max_torque,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DrivetrainConfig":
        """Create config from dictionary."""
        return cls(**data)
