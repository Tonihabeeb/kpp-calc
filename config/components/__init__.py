"""
Component-specific configuration classes.
"""

from .control_config import ControlConfig
from .drivetrain_config import DrivetrainConfig
from .electrical_config import ElectricalConfig
from .floater_config import FloaterConfig
from .simulation_config import SimulationConfig

__all__ = ["FloaterConfig", "ElectricalConfig", "DrivetrainConfig", "ControlConfig", "SimulationConfig"]
