import logging
from typing import Any, Dict, Type, TypeVar
from dataclasses import asdict, dataclass, field, fields
"""
Base configuration classes for the KPP simulator.
Provides type-safe configuration with validation.
"""

T = TypeVar('T', bound='BaseConfig')

@dataclass
class BaseConfig:
    """
    Base configuration class for the KPP simulator.
    Provides type-safe configuration with validation and serialization.
    """
    def validate(self) -> None:
        """Validate configuration fields. Override in subclasses for custom validation."""
        # Example: Check for None values (can be extended)
        for f in fields(self):
            value = getattr(self, f.name)
            if value is None:
                raise ValueError(f"Config field '{f.name}' cannot be None.")

    def to_dict(self) -> Dict[str, Any]:
        """Serialize config to a dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls: Type[T], data: Dict[str, Any]) -> T:
        """Create config from a dictionary."""
        return cls(**data)

