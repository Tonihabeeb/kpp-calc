"""
Thread-safe simulation engine wrapper.

This module provides a thread-safe wrapper around the SimulationEngine
to prevent race conditions and ensure safe concurrent access.
"""

import logging
import threading
import time
from contextlib import contextmanager
from typing import Any, Callable, Dict, Optional

from ..monitoring.performance_monitor import PerformanceMonitor
from .state_manager import StateManager

logger = logging.getLogger(__name__)


class ThreadSafeEngine:
    """Thread-safe simulation engine wrapper."""

    def __init__(self, engine_factory: Callable, state_manager: Optional[StateManager] = None):
        """
        Initialize thread-safe engine wrapper.

        Args:
            engine_factory: Function to create the simulation engine
            state_manager: Optional state manager for logging
        """
        self.engine_factory = engine_factory
        self.state_manager = state_manager or StateManager(None)  # Pass None as engine placeholder
        self.performance_monitor = PerformanceMonitor()
        self.engine_lock = threading.RLock()
        self._engine = None
        self._initialized = False
        self._last_step_time = 0.0
        self._step_count = 0

        logger.info("ThreadSafeEngine initialized with performance monitoring")

    @property
    def engine(self):
        """Thread-safe engine access."""
        with self.engine_lock:
            return self._engine

    @engine.setter
    def engine(self, value):
        """Thread-safe engine assignment."""
        with self.engine_lock:
            self._engine = value
            self._initialized = value is not None

    def initialize(self, *args, **kwargs) -> bool:
        """
        Thread-safe engine initialization.

        Args:
            *args: Arguments to pass to engine factory
            **kwargs: Keyword arguments to pass to engine factory

        Returns:
            True if initialization successful, False otherwise
        """
        with self.engine_lock:
            try:
                self._engine = self.engine_factory(*args, **kwargs)
                self._initialized = True
                self._step_count = 0
                logger.info("Engine initialized successfully")
                return True
            except Exception as e:
                logger.error(f"Engine initialization failed: {e}")
                self._engine = None
                self._initialized = False
                return False

    def step(self, dt: float) -> Dict[str, Any]:
        """
        Thread-safe simulation step.

        Args:
            dt: Time step in seconds

        Returns:
            Dictionary containing simulation state and status
        """
        with self.engine_lock:
            if not self._initialized or self._engine is None:
                raise RuntimeError("Engine not initialized")

            try:
                # Input validation
                if dt <= 0:
                    raise ValueError(f"Invalid time step: {dt}. Must be > 0.")

                # Execute simulation step
                step_start = time.time()
                result = self._engine.step(dt)
                step_duration = time.time() - step_start

                # Update step tracking
                self._step_count += 1
                self._last_step_time = time.time()

                # Record performance metrics
                error_count = 1 if result.get("status") == "error" else 0
                warning_count = 0  # Could be enhanced to count warnings
                self.performance_monitor.record_step(step_duration, error_count, warning_count)

                # Log state if state manager is available
                if self.state_manager and isinstance(result, dict):
                    add_state_method = getattr(self.state_manager, 'add_state', None)
                    if add_state_method:
                        add_state_method(result)

                # Add performance metrics
                if isinstance(result, dict):
                    result["_performance"] = {
                        "step_duration": step_duration,
                        "step_count": self._step_count,
                        "timestamp": self._last_step_time,
                        "performance_metrics": self.performance_monitor.get_current_metrics().to_dict(),
                    }

                logger.debug(f"Step completed: dt={dt:.3f}s, duration={step_duration:.3f}s")
                return result

            except Exception as e:
                logger.error(f"Simulation step failed: {e}")
                return {
                    "status": "error",
                    "error": str(e),
                    "timestamp": time.time(),
                    "_performance": {"step_duration": 0.0, "step_count": self._step_count, "timestamp": time.time()},
                }

    def get_state(self) -> Optional[Dict[str, Any]]:
        """Get current engine state thread-safely with enhanced error handling."""
        with self.engine_lock:
            if not self._initialized or self._engine is None:
                logger.warning("Engine not initialized, cannot get state")
                return {
                    "error": "Engine not initialized",
                    "timestamp": time.time(),
                    "_wrapper": {
                        "initialized": self._initialized,
                        "step_count": self._step_count,
                        "last_step_time": self._last_step_time,
                    }
                }

            try:
                # Get engine state with timeout protection
                state = self._engine.collect_state()

                # Add wrapper metadata
                state["_wrapper"] = {
                    "initialized": self._initialized,
                    "step_count": self._step_count,
                    "last_step_time": self._last_step_time,
                    "state_manager_stats": self.state_manager.get_stats() if self.state_manager else {},
                }

                return state

            except Exception as e:
                logger.error(f"Failed to get engine state: {e}")
                # Return a safe fallback state instead of None
                return {
                    "error": f"State collection failed: {str(e)}",
                    "timestamp": time.time(),
                    "_wrapper": {
                        "initialized": self._initialized,
                        "step_count": self._step_count,
                        "last_step_time": self._last_step_time,
                        "error": str(e),
                    },
                    # Provide minimal safe state data
                    "time": getattr(self._engine, 'time', 0.0) if self._engine else 0.0,
                    "status": "error",
                    "floaters": [],
                }

    def update_params(self, params: Dict[str, Any]) -> bool:
        """Thread-safe parameter update."""
        with self.engine_lock:
            if not self._initialized or self._engine is None:
                return False

            try:
                self._engine.update_params(params)
                logger.info("Parameters updated successfully")
                return True
            except Exception as e:
                logger.error(f"Parameter update failed: {e}")
                return False

    def reset(self) -> bool:
        """Thread-safe engine reset."""
        with self.engine_lock:
            if not self._initialized or self._engine is None:
                return False

            try:
                self._engine.reset()
                self._step_count = 0
                clear_method = getattr(self.state_manager, 'clear', None)
                if clear_method:
                    clear_method()
                logger.info("Engine reset successfully")
                return True
            except Exception as e:
                logger.error(f"Engine reset failed: {e}")
                return False

    def stop(self) -> bool:
        """Thread-safe engine stop."""
        with self.engine_lock:
            if not self._initialized or self._engine is None:
                return False

            try:
                self._engine.stop()
                logger.info("Engine stopped successfully")
                return True
            except Exception as e:
                logger.error(f"Engine stop failed: {e}")
                return False

    def is_initialized(self) -> bool:
        """Check if engine is initialized."""
        with self.engine_lock:
            return self._initialized and self._engine is not None

    def get_stats(self) -> Dict[str, Any]:
        """Get wrapper statistics."""
        with self.engine_lock:
            return {
                "initialized": self._initialized,
                "step_count": self._step_count,
                "last_step_time": self._last_step_time,
                "state_manager_stats": self.state_manager.get_stats(),
                "performance_stats": self.performance_monitor.get_stats(),
                "performance_summary": self.performance_monitor.get_summary(),
            }

    @contextmanager
    def engine_context(self):
        """Context manager for safe engine access."""
        with self.engine_lock:
            if not self._initialized or self._engine is None:
                raise RuntimeError("Engine not initialized")
            yield self._engine
