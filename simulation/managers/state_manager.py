import logging
from typing import Any, Dict, Optional
from .base_manager import BaseManager, ManagerType
from ..schemas import EnergyLossData, PerformanceMetrics, PhysicsResults, SimulationState, SystemResults, SystemState
"""
State Manager for the KPP Simulation Engine.
Handles state tracking, data collection, and simulation output management.
"""

