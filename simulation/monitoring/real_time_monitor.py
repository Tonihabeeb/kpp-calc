"""
Real-time Data Streaming and Monitoring System for KPP Simulation
Stage 4: Enhanced data streaming, monitoring, and error recovery
"""

import logging
import time
import uuid
from collections import deque
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class DataStreamManager:
    """Manages real-time data streaming with buffering and flow control"""

    def __init__(self, max_buffer_size: int = 1000):
        self.max_buffer_size = max_buffer_size
        self.data_buffer = deque(maxlen=max_buffer_size)
        self.subscribers = {}
        self.stream_enabled = True
        self.compression_enabled = False
        self.sample_interval = 0.1  # 10 Hz default
        self.last_sample_time = 0.0

        # Metrics
        self.bytes_streamed = 0
        self.samples_streamed = 0
        self.dropped_samples = 0

    def add_subscriber(
        self,
        subscriber_id: str,
        callback: Callable,
        sample_rate: Optional[float] = None,
    ) -> str:
        """Add a data stream subscriber"""
        if subscriber_id in self.subscribers:
            logger.warning(f"Subscriber {subscriber_id} already exists, replacing")

        self.subscribers[subscriber_id] = {
            "callback": callback,
            "sample_rate": sample_rate or (1.0 / self.sample_interval),
            "last_update": 0.0,
            "enabled": True,
            "error_count": 0,
        }

        logger.info(f"Added subscriber {subscriber_id} with sample rate {sample_rate or 'default'}")
        return subscriber_id

    def remove_subscriber(self, subscriber_id: str):
        """Remove a data stream subscriber"""
        if subscriber_id in self.subscribers:
            del self.subscribers[subscriber_id]
            logger.info(f"Removed subscriber {subscriber_id}")

    def stream_data(self, data: Dict[str, Any], timestamp: Optional[float] = None):
        """Stream data to all subscribers"""
        if not self.stream_enabled:
            return

        current_time = timestamp or time.time()

        # Check sampling interval
        if current_time - self.last_sample_time < self.sample_interval:
            return

        self.last_sample_time = current_time

        # Add metadata
        stream_data = {
            "timestamp": current_time,
            "data": data,
            "metadata": {
                "buffer_size": len(self.data_buffer),
                "subscribers": len(self.subscribers),
                "samples_streamed": self.samples_streamed,
            },
        }

        # Buffer data
        self.data_buffer.append(stream_data)

        # Stream to subscribers
        for sub_id, subscriber in self.subscribers.items():
            if not subscriber["enabled"]:
                continue

            # Check subscriber sample rate
            if current_time - subscriber["last_update"] < (1.0 / subscriber["sample_rate"]):
                continue

            try:
                subscriber["callback"](stream_data)
                subscriber["last_update"] = current_time
                subscriber["error_count"] = 0
            except Exception as e:
                subscriber["error_count"] += 1
                logger.error(f"Error streaming to subscriber {sub_id}: {e}")

                # Disable problematic subscribers
                if subscriber["error_count"] > 5:
                    subscriber["enabled"] = False
                    logger.warning(f"Disabled subscriber {sub_id} due to repeated errors")

        self.samples_streamed += 1

    def get_recent_data(self, count: int = 10) -> List[Dict[str, Any]]:
        """Get recent data samples"""
        return list(self.data_buffer)[-count:]

    def configure_streaming(self, enabled: bool = True, sample_rate: float = 10.0, compression: bool = False):
        """Configure streaming parameters"""
        self.stream_enabled = enabled
        self.sample_interval = 1.0 / sample_rate
        self.compression_enabled = compression

        logger.info(f"Streaming configured: enabled={enabled}, rate={sample_rate}Hz, compression={compression}")


class RealTimeMonitor:
    """Real-time monitoring and alerting system"""

    def __init__(self):
        self.monitors = {}
        self.alerts = deque(maxlen=100)
        self.alert_callbacks = {}

    def add_monitor(
        self,
        monitor_id: str,
        data_path: str,
        threshold: float,
        condition: str = "greater",
        alert_level: str = "warning",
    ):
        """Add a monitoring rule"""
        self.monitors[monitor_id] = {
            "data_path": data_path,
            "threshold": threshold,
            "condition": condition,  # 'greater', 'less', 'equal', 'not_equal'
            "alert_level": alert_level,  # 'info', 'warning', 'error', 'critical'
            "last_triggered": 0.0,
            "trigger_count": 0,
            "enabled": True,
        }

        logger.info(f"Added monitor {monitor_id}: {data_path} {condition} {threshold}")

    def check_monitors(self, data: Dict[str, Any], timestamp: float):
        """Check all monitoring rules against current data"""
        for monitor_id, monitor in self.monitors.items():
            if not monitor["enabled"]:
                continue

            value = self._get_nested_value(data, monitor["data_path"])
            if value is None:
                continue

            triggered = False
            condition = monitor["condition"]
            threshold = monitor["threshold"]

            if condition == "greater" and value > threshold:
                triggered = True
            elif condition == "less" and value < threshold:
                triggered = True
            elif condition == "equal" and abs(value - threshold) < 1e-6:
                triggered = True
            elif condition == "not_equal" and abs(value - threshold) > 1e-6:
                triggered = True

            if triggered:
                self._trigger_alert(monitor_id, monitor, value, timestamp)

    def _get_nested_value(self, data: Dict[str, Any], path: str) -> Optional[float]:
        """Get value from nested dictionary using dot notation"""
        try:
            keys = path.split(".")
            value = data
            for key in keys:
                value = value[key]
            return float(value) if isinstance(value, (int, float)) else None
        except (KeyError, TypeError, ValueError):
            return None

    def _trigger_alert(self, monitor_id: str, monitor: Dict[str, Any], value: float, timestamp: float):
        """Trigger an alert"""
        monitor["last_triggered"] = timestamp
        monitor["trigger_count"] += 1

        alert = {
            "id": str(uuid.uuid4()),
            "monitor_id": monitor_id,
            "timestamp": timestamp,
            "level": monitor["alert_level"],
            "message": f"{monitor['data_path']} = {value:.3f} {monitor['condition']} {monitor['threshold']}",
            "value": value,
            "threshold": monitor["threshold"],
        }

        self.alerts.append(alert)

        # Call alert callbacks
        for callback_id, callback in self.alert_callbacks.items():
            try:
                callback(alert)
            except Exception as e:
                logger.error(f"Error in alert callback {callback_id}: {e}")

        # Log alert
        log_level = getattr(logging, monitor["alert_level"].upper(), logging.INFO)
        logger.log(log_level, f"Alert {monitor_id}: {alert['message']}")

    def add_alert_callback(self, callback_id: str, callback: Callable):
        """Add callback for alert notifications"""
        self.alert_callbacks[callback_id] = callback

    def get_recent_alerts(self, level: Optional[str] = None, count: int = 10) -> List[Dict[str, Any]]:
        """Get recent alerts"""
        alerts = list(self.alerts)

        if level:
            alerts = [a for a in alerts if a["level"] == level]

        return alerts[-count:]

    def monitor_system_health(self, system_state: Dict[str, Any]) -> Dict[str, Any]:
        """Monitor overall system health and return metrics."""
        health_metrics = {
            "status": "healthy",
            "cpu_usage": system_state.get("cpu_usage", 0.0),
            "memory_usage": system_state.get("memory_usage", 0.0),
            "floater_count": system_state.get("floater_count", 0),
            "error_count": len(system_state.get("errors", [])),
            "timestamp": time.time(),
            "alerts": len(self.alerts),
        }

        # Determine overall health status
        if health_metrics["error_count"] > 0 or health_metrics["cpu_usage"] > 90:
            health_metrics["status"] = "unhealthy"
        elif health_metrics["cpu_usage"] > 70 or health_metrics["memory_usage"] > 80:
            health_metrics["status"] = "warning"

        return health_metrics


class ErrorRecoverySystem:
    """Automated error detection and recovery system"""

    def __init__(self):
        self.recovery_strategies = {}
        self.error_history = deque(maxlen=100)
        self.recovery_attempts = {}
        self.max_recovery_attempts = 3

    def register_recovery_strategy(self, error_type: str, strategy: Callable):
        """Register a recovery strategy for a specific error type"""
        self.recovery_strategies[error_type] = strategy
        logger.info(f"Registered recovery strategy for {error_type}")

    def handle_error(self, error_type: str, error_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle an error with appropriate recovery strategy"""

        error_record = {
            "timestamp": time.time(),
            "type": error_type,
            "data": error_data,
            "context": context,
            "recovery_attempted": False,
            "recovery_successful": False,
        }

        self.error_history.append(error_record)

        # Check if we've tried recovering from this error too many times
        attempt_key = f"{error_type}_{hash(str(error_data))}"
        attempts = self.recovery_attempts.get(attempt_key, 0)

        if attempts >= self.max_recovery_attempts:
            logger.error(f"Max recovery attempts exceeded for {error_type}")
            return {
                "recovered": False,
                "action": "escalate",
                "message": f"Maximum recovery attempts ({self.max_recovery_attempts}) exceeded",
            }

        # Attempt recovery
        if error_type in self.recovery_strategies:
            try:
                self.recovery_attempts[attempt_key] = attempts + 1
                error_record["recovery_attempted"] = True

                recovery_result = self.recovery_strategies[error_type](error_data, context)

                if recovery_result.get("success", False):
                    error_record["recovery_successful"] = True
                    logger.info(f"Successfully recovered from {error_type}")
                    return {
                        "recovered": True,
                        "action": recovery_result.get("action", "continue"),
                        "message": recovery_result.get("message", "Recovery successful"),
                    }
                else:
                    logger.warning(
                        f"Recovery failed for {error_type}: {recovery_result.get('message', 'Unknown reason')}"
                    )

            except Exception as e:
                logger.error(f"Recovery strategy failed for {error_type}: {e}")

        return {
            "recovered": False,
            "action": "continue",
            "message": f"No recovery strategy available for {error_type}",
        }

    def get_error_summary(self) -> Dict[str, Any]:
        """Get summary of recent errors and recovery attempts"""

        total_errors = len(self.error_history)
        recovery_attempted = sum(1 for e in self.error_history if e["recovery_attempted"])
        recovery_successful = sum(1 for e in self.error_history if e["recovery_successful"])

        error_types = {}
        for error in self.error_history:
            error_type = error["type"]
            if error_type not in error_types:
                error_types[error_type] = {"count": 0, "recovery_rate": 0.0}
            error_types[error_type]["count"] += 1

        # Calculate recovery rates
        for error_type in error_types:
            type_errors = [e for e in self.error_history if e["type"] == error_type]
            attempted = sum(1 for e in type_errors if e["recovery_attempted"])
            successful = sum(1 for e in type_errors if e["recovery_successful"])

            if attempted > 0:
                error_types[error_type]["recovery_rate"] = successful / attempted

        return {
            "total_errors": total_errors,
            "recovery_attempted": recovery_attempted,
            "recovery_successful": recovery_successful,
            "overall_recovery_rate": (recovery_successful / recovery_attempted if recovery_attempted > 0 else 0.0),
            "error_types": error_types,
            "recent_errors": list(self.error_history)[-10:],
        }


class RealTimeController:
    """Main controller for real-time operation, streaming, and monitoring"""

    def __init__(self):
        self.stream_manager = DataStreamManager()
        self.monitor = RealTimeMonitor()
        self.error_recovery = ErrorRecoverySystem()

        self.enabled = True
        self.performance_mode = "balanced"  # 'performance', 'balanced', 'accuracy'

        # Setup default monitors
        self._setup_default_monitors()

        # Setup default recovery strategies
        self._setup_default_recovery_strategies()

        logger.info("RealTimeController initialized")

    def _setup_default_monitors(self):
        """Setup default monitoring rules"""

        # Physics monitors
        self.monitor.add_monitor("high_velocity", "v_chain", 8.0, "greater", "warning")
        self.monitor.add_monitor("high_acceleration", "a_chain", 40.0, "greater", "warning")
        self.monitor.add_monitor("low_efficiency", "efficiency", 0.3, "less", "warning")

        # Performance monitors
        self.monitor.add_monitor("low_fps", "metadata.fps", 5.0, "less", "warning")
        self.monitor.add_monitor(
            "high_computation_time",
            "metadata.computation_time",
            0.2,
            "greater",
            "warning",
        )

        # Stability monitors
        self.monitor.add_monitor("stability_critical", "metadata.stability_score", 0.5, "less", "critical")
        self.monitor.add_monitor("validation_failures", "metadata.validation_failures", 5, "greater", "error")

    def _setup_default_recovery_strategies(self):
        """Setup default error recovery strategies"""

        def numerical_instability_recovery(error_data, context):
            """Recovery strategy for numerical instability"""
            # Reduce timestep and reset velocities if needed
            suggestions = {
                "reduce_timestep": True,
                "reset_extreme_values": True,
                "increase_damping": True,
            }

            return {
                "success": True,
                "action": "adjust_parameters",
                "message": "Applied numerical stability corrections",
                "suggestions": suggestions,
            }

        def performance_degradation_recovery(error_data, context):
            """Recovery strategy for performance issues"""
            suggestions = {
                "increase_timestep": True,
                "reduce_output_frequency": True,
                "disable_detailed_validation": True,
            }

            return {
                "success": True,
                "action": "optimize_performance",
                "message": "Applied performance optimizations",
                "suggestions": suggestions,
            }

        self.error_recovery.register_recovery_strategy("numerical_instability", numerical_instability_recovery)
        self.error_recovery.register_recovery_strategy("performance_degradation", performance_degradation_recovery)

    def process_realtime_data(
        self, simulation_data: Dict[str, Any], performance_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process real-time data through streaming, monitoring, and error handling"""

        if not self.enabled:
            return {"processed": False, "reason": "controller_disabled"}

        timestamp = time.time()

        # Combine data
        combined_data = {
            **simulation_data,
            "metadata": {
                **performance_data,
                "timestamp": timestamp,
                "performance_mode": self.performance_mode,
            },
        }

        # Check monitors
        self.monitor.check_monitors(combined_data, timestamp)

        # Stream data
        self.stream_manager.stream_data(combined_data, timestamp)

        # Check for errors and apply recovery if needed
        recovery_actions = self._check_and_recover_errors(combined_data)

        return {
            "processed": True,
            "timestamp": timestamp,
            "alerts": self.monitor.get_recent_alerts(count=5),
            "recovery_actions": recovery_actions,
            "streaming_status": {
                "enabled": self.stream_manager.stream_enabled,
                "subscribers": len(self.stream_manager.subscribers),
                "samples_streamed": self.stream_manager.samples_streamed,
            },
        }

    def _check_and_recover_errors(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check for errors and apply recovery strategies"""

        recovery_actions = []

        # Check stability
        stability_score = data.get("metadata", {}).get("stability_score", 1.0)
        if stability_score < 0.7:
            recovery = self.error_recovery.handle_error(
                "numerical_instability",
                {"stability_score": stability_score},
                {"data": data},
            )
            recovery_actions.append(recovery)

        # Check performance
        fps = data.get("metadata", {}).get("fps", 10.0)
        if fps < 5.0:
            recovery = self.error_recovery.handle_error("performance_degradation", {"fps": fps}, {"data": data})
            recovery_actions.append(recovery)

        return recovery_actions

    def configure_performance_mode(self, mode: str):
        """Configure performance mode"""
        valid_modes = ["performance", "balanced", "accuracy"]
        if mode not in valid_modes:
            raise ValueError(f"Invalid mode {mode}, must be one of {valid_modes}")

        self.performance_mode = mode

        # Adjust settings based on mode
        if mode == "performance":
            self.stream_manager.configure_streaming(sample_rate=5.0)
        elif mode == "balanced":
            self.stream_manager.configure_streaming(sample_rate=10.0)
        elif mode == "accuracy":
            self.stream_manager.configure_streaming(sample_rate=20.0)

        logger.info(f"Performance mode set to {mode}")

    def get_status_report(self) -> Dict[str, Any]:
        """Get comprehensive status report"""

        return {
            "controller": {
                "enabled": self.enabled,
                "performance_mode": self.performance_mode,
            },
            "streaming": {
                "enabled": self.stream_manager.stream_enabled,
                "subscribers": len(self.stream_manager.subscribers),
                "samples_streamed": self.stream_manager.samples_streamed,
                "buffer_size": len(self.stream_manager.data_buffer),
            },
            "monitoring": {
                "monitors": len(self.monitor.monitors),
                "recent_alerts": self.monitor.get_recent_alerts(count=5),
                "total_alerts": len(self.monitor.alerts),
            },
            "error_recovery": self.error_recovery.get_error_summary(),
        }
