"""
KPP Simulator Configuration Package

Provides configuration management and validation for the KPP simulator.
This package handles parameter validation, configuration loading, and
hot-reload capabilities.

Components:
- Configuration Manager: Main configuration handling
- Parameter Validation: Schema validation and constraints
- Configuration Presets: Predefined configuration sets
"""

# Import from main config package
from config.manager import ConfigManager
from config.core.base_config import BaseConfig

__all__ = [
    "ConfigManager",
    "BaseConfig",
] 