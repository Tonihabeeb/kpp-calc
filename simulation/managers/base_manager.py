import time
import logging
from typing import Any, Dict, Optional
from simulation.schemas import ComponentStatus, ManagerInterface, SimulationError
from enum import Enum
from abc import ABC, abstractmethod
"""
Base manager interface and common utilities for KPP Simulator managers.
Provides standardized interface, error handling, and performance monitoring.
"""

