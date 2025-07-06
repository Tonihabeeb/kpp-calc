"""
Floater component package.
Provides modular floater physics and control.
"""

from .buoyancy import BuoyancyCalculator
from .core import Floater, FloaterConfig, LegacyFloaterConfig
from .pneumatic import PneumaticState, PneumaticSystem
from .state_machine import FloaterStateMachine
from .thermal import ThermalModel
from .validation import FloaterValidator

__all__ = [
    "Floater",
    "FloaterConfig",
    "LegacyFloaterConfig",
    "PneumaticSystem",
    "PneumaticState",
    "BuoyancyCalculator",
    "FloaterStateMachine",
    "ThermalModel",
    "FloaterValidator",
]
