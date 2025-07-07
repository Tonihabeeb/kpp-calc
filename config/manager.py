import logging
import json
from typing import Any, Dict, List, Optional
from .core.validation import ConfigValidator
from .components.simulation_config import SimulationConfig
from .components.floater_config import FloaterConfig
from .components.electrical_config import ElectricalConfig
from .components.drivetrain_config import DrivetrainConfig
from .components.control_config import ControlConfig
    from watchdog.observers import Observer  # type: ignore
    from watchdog.events import FileSystemEventHandler  # type: ignore
        import os
        from pathlib import Path
"""
Configuration manager for the KPP simulator.
Handles loading, validation, and hot-reload of configurations.
"""

