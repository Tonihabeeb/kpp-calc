import logging
from typing import Dict, Optional
from simulation.control.startup_controller import StartupController
try:
    from simulation.control.grid_disturbance_handler import GridDisturbanceHandler
except ImportError:
    class GridDisturbanceHandler:
        pass

from simulation.control.emergency_response import EmergencyResponseSystem
from enum import Enum
from dataclasses import dataclass
"""
Transient Event Controller for KPP System
Coordinates startup, emergency response, and grid disturbance handling.
"""

