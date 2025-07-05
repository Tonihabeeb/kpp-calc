"""
Component-specific configuration classes.
"""

from .floater_config import FloaterConfig
from .electrical_config import ElectricalConfig
from .drivetrain_config import DrivetrainConfig
from .control_config import ControlConfig
from .simulation_config import SimulationConfig

__all__ = [
    'FloaterConfig',
    'ElectricalConfig',
    'DrivetrainConfig',
    'ControlConfig',
    'SimulationConfig'
] 