import time
import threading
import logging
from typing import Any, Callable, Dict, Optional
from contextlib import contextmanager
from .state_manager import StateManager
from ..monitoring.performance_monitor import PerformanceMonitor
"""
Thread-safe simulation engine wrapper.

This module provides a thread-safe wrapper around the SimulationEngine
to prevent race conditions and ensure safe concurrent access.
"""

