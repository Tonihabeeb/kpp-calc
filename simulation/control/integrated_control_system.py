import numpy as np
import logging
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass
from collections import deque
from .timing_controller import TimingController
from .load_manager import LoadManager, LoadProfile
from .grid_stability_controller import GridStabilityController
from .fault_detector import FaultDetector
    from config.components.control_config import ControlConfig as ControlSystemConfig
"""
Integrated Control System for KPP Power Generation
Combines all Phase 4 advanced control components into a unified system.
"""

