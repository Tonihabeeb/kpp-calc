"""
Floater component package.
Provides modular floater physics and control.
"""

from .core import Floater, FloaterConfig, LegacyFloaterConfig
from .pneumatic import PneumaticSystem, PneumaticState
from .buoyancy import BuoyancyCalculator
from .state_machine import FloaterStateMachine
from .thermal import ThermalModel
from .validation import FloaterValidator

__all__ = [
    'Floater',
    'FloaterConfig',
    'LegacyFloaterConfig',
    'PneumaticSystem', 
    'PneumaticState',
    'BuoyancyCalculator',
    'FloaterStateMachine',
    'ThermalModel',
    'FloaterValidator'
]
