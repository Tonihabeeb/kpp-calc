"""
Base manager interface and common utilities for KPP Simulator managers.
Provides standardized interface, error handling, and performance monitoring.
"""

import logging
import time
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, Optional

from simulation.schemas import ComponentStatus, ManagerInterface, SimulationError

logger = logging.getLogger(__name__)


class ManagerType(str, Enum):
    """Types of manager components."""

    PHYSICS = "physics"
    SYSTEM = "system"
    STATE = "state"
    COMPONENT = "component"


class BaseManager(ABC):
    """
    Base class for all simulation managers.
    Provides common functionality for error handling, performance monitoring,
    and standardized interfaces.
    """

    def __init__(self, engine, manager_type: ManagerType):
        """
        Initialize the base manager.

        Args:
            engine: Reference to the main SimulationEngine
            manager_type: Type of manager
        """
        self.engine = engine
        self.manager_type = manager_type
        self.status = ComponentStatus.ONLINE
        self.initialization_time = time.time()
        self.last_update_time = None
        self.error_count = 0
        self.warning_count = 0
        self.performance_metrics = {
            "total_updates": 0,
            "avg_execution_time": 0.0,
            "max_execution_time": 0.0,
            "min_execution_time": float("inf"),
            "errors_per_hour": 0.0,
        }
        self.errors = []
        self.warnings = []

        logger.info(f"{self.manager_type.value.title()}Manager initialized")

    @abstractmethod
    def update(self, dt: float, *args, **kwargs) -> Dict[str, Any]:
        """
        Update the manager for one simulation time step.

        Args:
            dt: Time step in seconds
            *args: Additional positional arguments
            **kwargs: Additional keyword arguments

        Returns:
            Dictionary containing update results
        """

    def safe_update(self, dt: float, *args, **kwargs) -> Dict[str, Any]:
        """
        Safely execute the update method with error handling and performance monitoring.

        Args:
            dt: Time step in seconds
            *args: Additional positional arguments
            **kwargs: Additional keyword arguments

        Returns:
            Dictionary containing update results or error information
        """
        start_time = time.time()

        try:
            # Validate inputs
            self._validate_inputs(dt, *args, **kwargs)

            # Execute update
            result = self.update(dt, *args, **kwargs)

            # Update performance metrics
            execution_time = time.time() - start_time
            self._update_performance_metrics(execution_time)

            # Mark successful update
            self.last_update_time = time.time()
            self.status = ComponentStatus.ONLINE

            return result

        except Exception as e:
            # Handle error
            execution_time = time.time() - start_time
            error = self._handle_error(e, execution_time)

            return {
                "success": False,
                "error": error,
                "manager_type": self.manager_type.value,
                "execution_time": execution_time,
            }

    def _validate_inputs(self, dt: float, *args, **kwargs) -> None:
        """
        Validate input parameters.

        Args:
            dt: Time step in seconds
            *args: Additional positional arguments
            **kwargs: Additional keyword arguments

        Raises:
            ValueError: If inputs are invalid
        """
        if dt <= 0:
            raise ValueError(f"Time step dt must be positive, got {dt}")

        if dt > 1.0:
            self._add_warning(f"Large time step detected: {dt}s")

    def _update_performance_metrics(self, execution_time: float) -> None:
        """
        Update performance metrics after successful execution.

        Args:
            execution_time: Execution time in seconds
        """
        self.performance_metrics["total_updates"] += 1

        # Update execution time statistics
        total_updates = self.performance_metrics["total_updates"]
        current_avg = self.performance_metrics["avg_execution_time"]
        self.performance_metrics["avg_execution_time"] = (
            current_avg * (total_updates - 1) + execution_time
        ) / total_updates

        self.performance_metrics["max_execution_time"] = max(
            self.performance_metrics["max_execution_time"], execution_time
        )

        self.performance_metrics["min_execution_time"] = min(
            self.performance_metrics["min_execution_time"], execution_time
        )

        # Calculate errors per hour
        uptime_hours = (time.time() - self.initialization_time) / 3600.0
        if uptime_hours > 0:
            self.performance_metrics["errors_per_hour"] = self.error_count / uptime_hours

    def _handle_error(self, error: Exception, execution_time: float) -> SimulationError:
        """
        Handle and log an error.

        Args:
            error: The exception that occurred
            execution_time: Time taken before error occurred

        Returns:
            SimulationError object with error details
        """
        self.error_count += 1

        # Create error object
        sim_error = SimulationError(
            error_code=f"{self.manager_type.value.upper()}_ERROR_{self.error_count:03d}",
            error_type=type(error).__name__,
            message=str(error),
            component=f"{self.manager_type.value}_manager",
            timestamp=time.time(),
            stack_trace=None,  # Could add traceback if needed
        )

        # Store error (keep last 10 errors)
        self.errors.append(sim_error)
        if len(self.errors) > 10:
            self.errors.pop(0)

        # Log error
        logger.error(
            f"{self.manager_type.value.title()}Manager error: {sim_error.message} " f"(Code: {sim_error.error_code})"
        )

        # Update status based on error frequency
        if self.error_count > 5:
            self.status = ComponentStatus.FAULT
        elif self.error_count > 2:
            self.status = ComponentStatus.MAINTENANCE

        return sim_error

    def _add_warning(self, message: str) -> None:
        """
        Add a warning message.

        Args:
            message: Warning message
        """
        self.warning_count += 1

        # Store warning (keep last 10 warnings)
        self.warnings.append({"message": message, "timestamp": time.time(), "count": self.warning_count})
        if len(self.warnings) > 10:
            self.warnings.pop(0)

        logger.warning(f"{self.manager_type.value.title()}Manager: {message}")

    def get_status(self) -> ManagerInterface:
        """
        Get current manager status and metrics.

        Returns:
            ManagerInterface object with current status
        """
        return ManagerInterface(
            manager_type=self.manager_type.value,
            status=self.status,
            last_update_time=self.last_update_time,
            error_count=self.error_count,
            performance_metrics=self.performance_metrics,
        )

    def get_health_info(self) -> Dict[str, Any]:
        """
        Get detailed health information for diagnostics.

        Returns:
            Dictionary with detailed health information
        """
        uptime = time.time() - self.initialization_time

        return {
            "manager_type": self.manager_type.value,
            "status": self.status.value,
            "uptime_seconds": uptime,
            "last_update_time": self.last_update_time,
            "error_count": self.error_count,
            "warning_count": self.warning_count,
            "performance_metrics": self.performance_metrics.copy(),
            "recent_errors": [
                {
                    "code": error.error_code,
                    "type": error.error_type,
                    "message": error.message,
                    "timestamp": error.timestamp,
                }
                for error in self.errors[-3:]  # Last 3 errors
            ],
            "recent_warnings": [
                {"message": warning["message"], "timestamp": warning["timestamp"]}
                for warning in self.warnings[-3:]  # Last 3 warnings
            ],
        }

    def reset_metrics(self) -> None:
        """Reset performance metrics and error counts."""
        self.error_count = 0
        self.warning_count = 0
        self.errors.clear()
        self.warnings.clear()
        self.performance_metrics = {
            "total_updates": 0,
            "avg_execution_time": 0.0,
            "max_execution_time": 0.0,
            "min_execution_time": float("inf"),
            "errors_per_hour": 0.0,
        }
        self.status = ComponentStatus.ONLINE
        logger.info(f"{self.manager_type.value.title()}Manager metrics reset")

    def shutdown(self) -> None:
        """Perform cleanup operations before shutdown."""
        logger.info(f"{self.manager_type.value.title()}Manager shutting down")
        self.status = ComponentStatus.OFFLINE

    def get_config_param(self, param_name: str, default_value: Any = None, config_section: Optional[str] = None) -> Any:
        """
        Get configuration parameter with support for both legacy and new config systems.

        Args:
            param_name: Name of the parameter to retrieve
            default_value: Default value if parameter not found
            config_section: Optional config section (e.g., 'floater', 'electrical')

        Returns:
            Configuration parameter value
        """
        # Try new config system first
        if hasattr(self.engine, "use_new_config") and self.engine.use_new_config:
            try:
                if config_section and hasattr(self.engine, "config_manager"):
                    # Get from specific config section
                    config = self.engine.config_manager.get_config(config_section)
                    if config and hasattr(config, param_name):
                        return getattr(config, param_name)
                elif hasattr(self.engine, "config_manager"):
                    # Try to find parameter across all configs
                    all_params = self.engine.config_manager.get_all_parameters()
                    for section, section_params in all_params.items():
                        if param_name in section_params:
                            return section_params[param_name]
            except Exception as e:
                logger.debug(f"New config access failed for {param_name}: {e}")

        # Fall back to legacy config system
        if hasattr(self.engine, "params") and self.engine.params is not None and param_name in self.engine.params:
            return self.engine.params[param_name]

        return default_value

    def get_config_section(self, section_name: str) -> Optional[Dict[str, Any]]:
        """
        Get entire configuration section with support for both legacy and new config systems.

        Args:
            section_name: Name of the configuration section

        Returns:
            Configuration section as dictionary, or None if not found
        """
        # Try new config system first
        if hasattr(self.engine, "use_new_config") and self.engine.use_new_config:
            try:
                if hasattr(self.engine, "config_manager"):
                    config = self.engine.config_manager.get_config(section_name)
                    if config and hasattr(config, "to_dict"):
                        return config.to_dict()
            except Exception as e:
                logger.debug(f"New config section access failed for {section_name}: {e}")

        # Fall back to legacy config system - return relevant subset
        if hasattr(self.engine, "params"):
            # For legacy system, return all params (no sectioning)
            return self.engine.params

        return None

    def validate_config_param(
        self,
        param_name: str,
        param_value: Any,
        min_value: Optional[float] = None,
        max_value: Optional[float] = None,
        param_type: Optional[type] = None,
    ) -> bool:
        """
        Validate a configuration parameter.

        Args:
            param_name: Name of the parameter
            param_value: Value to validate
            min_value: Minimum allowed value (for numeric types)
            max_value: Maximum allowed value (for numeric types)
            param_type: Expected type

        Returns:
            True if valid, False otherwise
        """
        try:
            # Type validation
            if param_type and not isinstance(param_value, param_type):
                logger.warning(
                    f"Config parameter {param_name} has wrong type: expected {param_type}, got {type(param_value)}"
                )
                return False

            # Range validation for numeric types
            if isinstance(param_value, (int, float)):
                if min_value is not None and param_value < min_value:
                    logger.warning(f"Config parameter {param_name} below minimum: {param_value} < {min_value}")
                    return False
                if max_value is not None and param_value > max_value:
                    logger.warning(f"Config parameter {param_name} above maximum: {param_value} > {max_value}")
                    return False

            return True

        except Exception as e:
            logger.error(f"Error validating config parameter {param_name}: {e}")
            return False


class ManagerCoordinator:
    """
    Coordinates multiple managers and provides centralized health monitoring.
    """

    def __init__(self):
        """Initialize the manager coordinator."""
        self.managers: Dict[str, BaseManager] = {}
        self.initialization_time = time.time()

    def register_manager(self, name: str, manager: BaseManager) -> None:
        """
        Register a manager with the coordinator.

        Args:
            name: Manager name
            manager: Manager instance
        """
        self.managers[name] = manager
        logger.info(f"Registered manager: {name}")

    def get_overall_health(self) -> Dict[str, Any]:
        """
        Get overall system health from all managers.

        Returns:
            Dictionary with overall health information
        """
        overall_status = ComponentStatus.ONLINE
        manager_statuses = {}
        total_errors = 0
        total_warnings = 0

        for name, manager in self.managers.items():
            status = manager.get_status()
            manager_statuses[name] = status.status
            total_errors += status.error_count

            # Determine overall status (worst case)
            if status.status == ComponentStatus.FAULT:
                overall_status = ComponentStatus.FAULT
            elif status.status == ComponentStatus.MAINTENANCE and overall_status == ComponentStatus.ONLINE:
                overall_status = ComponentStatus.MAINTENANCE

        uptime = time.time() - self.initialization_time

        return {
            "overall_status": overall_status,
            "manager_statuses": manager_statuses,
            "uptime_seconds": uptime,
            "total_errors": total_errors,
            "total_warnings": total_warnings,
            "manager_count": len(self.managers),
            "timestamp": time.time(),
        }

    def get_performance_summary(self) -> Dict[str, Any]:
        """
        Get performance summary from all managers.

        Returns:
            Dictionary with performance metrics summary
        """
        summary = {"total_updates": 0, "avg_execution_time": 0.0, "max_execution_time": 0.0, "managers": {}}

        total_avg_time = 0.0
        manager_count = 0

        for name, manager in self.managers.items():
            metrics = manager.performance_metrics
            summary["managers"][name] = metrics.copy()

            summary["total_updates"] += metrics["total_updates"]
            summary["max_execution_time"] = max(summary["max_execution_time"], metrics["max_execution_time"])

            if metrics["avg_execution_time"] > 0:
                total_avg_time += metrics["avg_execution_time"]
                manager_count += 1

        if manager_count > 0:
            summary["avg_execution_time"] = total_avg_time / manager_count

        return summary
