"""
Performance monitoring system for KPP Simulator.

This module provides comprehensive performance monitoring including:
- Step execution time tracking
- Memory usage monitoring
- Error rate tracking
- Performance alerts and warnings
"""

import time
import threading
import logging
import psutil
import os
from typing import Dict, Any, List, Optional, Callable
from collections import deque, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """Performance metrics for a single simulation step."""
    timestamp: float
    step_duration: float
    memory_usage_mb: float
    cpu_usage_percent: float
    error_count: int = 0
    warning_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'timestamp': self.timestamp,
            'step_duration': self.step_duration,
            'memory_usage_mb': self.memory_usage_mb,
            'cpu_usage_percent': self.cpu_usage_percent,
            'error_count': self.error_count,
            'warning_count': self.warning_count
        }


@dataclass
class PerformanceAlert:
    """Performance alert with severity and details."""
    timestamp: float
    severity: str  # 'info', 'warning', 'error', 'critical'
    category: str  # 'performance', 'memory', 'error_rate', 'system'
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'timestamp': self.timestamp,
            'severity': self.severity,
            'category': self.category,
            'message': self.message,
            'details': self.details
        }


class PerformanceMonitor:
    """Comprehensive performance monitoring system."""
    
    def __init__(self, 
                 max_history: int = 1000,
                 alert_thresholds: Optional[Dict[str, float]] = None,
                 enable_system_monitoring: bool = True):
        """
        Initialize performance monitor.
        
        Args:
            max_history: Maximum number of metrics to keep in history
            alert_thresholds: Custom alert thresholds
            enable_system_monitoring: Whether to monitor system resources
        """
        self.max_history = max_history
        self.enable_system_monitoring = enable_system_monitoring
        
        # Performance history
        self.metrics_history = deque(maxlen=max_history)
        self.alerts_history = deque(maxlen=max_history)
        
        # Current metrics
        self.current_metrics = PerformanceMetrics(
            timestamp=time.time(),
            step_duration=0.0,
            memory_usage_mb=0.0,
            cpu_usage_percent=0.0
        )
        
        # Statistics
        self.stats = {
            'total_steps': 0,
            'total_errors': 0,
            'total_warnings': 0,
            'avg_step_duration': 0.0,
            'max_step_duration': 0.0,
            'min_step_duration': float('inf'),
            'avg_memory_usage': 0.0,
            'max_memory_usage': 0.0,
            'avg_cpu_usage': 0.0,
            'max_cpu_usage': 0.0
        }
        
        # Alert thresholds
        self.alert_thresholds = alert_thresholds or {
            'step_duration_warning': 0.1,  # seconds
            'step_duration_error': 0.5,    # seconds
            'memory_usage_warning': 500.0, # MB
            'memory_usage_error': 1000.0,  # MB
            'cpu_usage_warning': 80.0,     # percent
            'cpu_usage_error': 95.0,       # percent
            'error_rate_warning': 0.1,     # 10% error rate
            'error_rate_error': 0.3        # 30% error rate
        }
        
        # Thread safety
        self.lock = threading.RLock()
        
        # Alert callbacks
        self.alert_callbacks: List[Callable[[PerformanceAlert], None]] = []
        
        # System monitoring
        self.process = psutil.Process(os.getpid()) if enable_system_monitoring else None
        
        logger.info("Performance monitor initialized")
    
    def record_step(self, step_duration: float, error_count: int = 0, warning_count: int = 0) -> None:
        """
        Record performance metrics for a simulation step.
        
        Args:
            step_duration: Duration of the step in seconds
            error_count: Number of errors in this step
            warning_count: Number of warnings in this step
        """
        with self.lock:
            # Get system metrics if enabled
            memory_usage_mb = 0.0
            cpu_usage_percent = 0.0
            
            if self.enable_system_monitoring and self.process:
                try:
                    memory_info = self.process.memory_info()
                    memory_usage_mb = memory_info.rss / 1024 / 1024  # Convert to MB
                    cpu_usage_percent = self.process.cpu_percent()
                except Exception as e:
                    logger.warning(f"Failed to get system metrics: {e}")
            
            # Create metrics
            metrics = PerformanceMetrics(
                timestamp=time.time(),
                step_duration=step_duration,
                memory_usage_mb=memory_usage_mb,
                cpu_usage_percent=cpu_usage_percent,
                error_count=error_count,
                warning_count=warning_count
            )
            
            # Update current metrics
            self.current_metrics = metrics
            
            # Add to history
            self.metrics_history.append(metrics)
            
            # Update statistics
            self._update_stats(metrics)
            
            # Check for alerts
            self._check_alerts(metrics)
    
    def add_alert_callback(self, callback: Callable[[PerformanceAlert], None]) -> None:
        """Add a callback function to be called when alerts are generated."""
        with self.lock:
            self.alert_callbacks.append(callback)
    
    def get_current_metrics(self) -> PerformanceMetrics:
        """Get current performance metrics."""
        with self.lock:
            return self.current_metrics
    
    def get_metrics_history(self, limit: Optional[int] = None) -> List[PerformanceMetrics]:
        """Get performance metrics history."""
        with self.lock:
            if limit is None:
                return list(self.metrics_history)
            else:
                return list(self.metrics_history)[-limit:]
    
    def get_alerts_history(self, limit: Optional[int] = None) -> List[PerformanceAlert]:
        """Get alerts history."""
        with self.lock:
            if limit is None:
                return list(self.alerts_history)
            else:
                return list(self.alerts_history)[-limit:]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get performance statistics."""
        with self.lock:
            return self.stats.copy()
    
    def get_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary."""
        with self.lock:
            recent_metrics = list(self.metrics_history)[-100:] if self.metrics_history else []
            recent_alerts = list(self.alerts_history)[-50:] if self.alerts_history else []
            
            # Calculate recent averages
            if recent_metrics:
                avg_step_duration = sum(m.step_duration for m in recent_metrics) / len(recent_metrics)
                avg_memory_usage = sum(m.memory_usage_mb for m in recent_metrics) / len(recent_metrics)
                avg_cpu_usage = sum(m.cpu_usage_percent for m in recent_metrics) / len(recent_metrics)
                total_errors = sum(m.error_count for m in recent_metrics)
                total_warnings = sum(m.warning_count for m in recent_metrics)
            else:
                avg_step_duration = 0.0
                avg_memory_usage = 0.0
                avg_cpu_usage = 0.0
                total_errors = 0
                total_warnings = 0
            
            return {
                'current_metrics': self.current_metrics.to_dict(),
                'stats': self.stats,
                'recent_averages': {
                    'step_duration': avg_step_duration,
                    'memory_usage_mb': avg_memory_usage,
                    'cpu_usage_percent': avg_cpu_usage,
                    'error_count': total_errors,
                    'warning_count': total_warnings
                },
                'recent_alerts': [alert.to_dict() for alert in recent_alerts],
                'alert_thresholds': self.alert_thresholds,
                'monitoring_enabled': self.enable_system_monitoring
            }
    
    def clear_history(self) -> None:
        """Clear performance history."""
        with self.lock:
            self.metrics_history.clear()
            self.alerts_history.clear()
            logger.info("Performance history cleared")
    
    def _update_stats(self, metrics: PerformanceMetrics) -> None:
        """Update performance statistics."""
        self.stats['total_steps'] += 1
        self.stats['total_errors'] += metrics.error_count
        self.stats['total_warnings'] += metrics.warning_count
        
        # Update step duration stats
        self.stats['max_step_duration'] = max(self.stats['max_step_duration'], metrics.step_duration)
        self.stats['min_step_duration'] = min(self.stats['min_step_duration'], metrics.step_duration)
        
        # Update average step duration
        total_duration = self.stats['avg_step_duration'] * (self.stats['total_steps'] - 1) + metrics.step_duration
        self.stats['avg_step_duration'] = total_duration / self.stats['total_steps']
        
        # Update memory stats
        self.stats['max_memory_usage'] = max(self.stats['max_memory_usage'], metrics.memory_usage_mb)
        total_memory = self.stats['avg_memory_usage'] * (self.stats['total_steps'] - 1) + metrics.memory_usage_mb
        self.stats['avg_memory_usage'] = total_memory / self.stats['total_steps']
        
        # Update CPU stats
        self.stats['max_cpu_usage'] = max(self.stats['max_cpu_usage'], metrics.cpu_usage_percent)
        total_cpu = self.stats['avg_cpu_usage'] * (self.stats['total_steps'] - 1) + metrics.cpu_usage_percent
        self.stats['avg_cpu_usage'] = total_cpu / self.stats['total_steps']
    
    def _check_alerts(self, metrics: PerformanceMetrics) -> None:
        """Check for performance alerts and generate them if needed."""
        alerts = []
        
        # Check step duration
        if metrics.step_duration > self.alert_thresholds['step_duration_error']:
            alerts.append(PerformanceAlert(
                timestamp=metrics.timestamp,
                severity='error',
                category='performance',
                message=f"Step duration too high: {metrics.step_duration:.3f}s",
                details={'step_duration': metrics.step_duration, 'threshold': self.alert_thresholds['step_duration_error']}
            ))
        elif metrics.step_duration > self.alert_thresholds['step_duration_warning']:
            alerts.append(PerformanceAlert(
                timestamp=metrics.timestamp,
                severity='warning',
                category='performance',
                message=f"Step duration high: {metrics.step_duration:.3f}s",
                details={'step_duration': metrics.step_duration, 'threshold': self.alert_thresholds['step_duration_warning']}
            ))
        
        # Check memory usage
        if metrics.memory_usage_mb > self.alert_thresholds['memory_usage_error']:
            alerts.append(PerformanceAlert(
                timestamp=metrics.timestamp,
                severity='error',
                category='memory',
                message=f"Memory usage too high: {metrics.memory_usage_mb:.1f}MB",
                details={'memory_usage_mb': metrics.memory_usage_mb, 'threshold': self.alert_thresholds['memory_usage_error']}
            ))
        elif metrics.memory_usage_mb > self.alert_thresholds['memory_usage_warning']:
            alerts.append(PerformanceAlert(
                timestamp=metrics.timestamp,
                severity='warning',
                category='memory',
                message=f"Memory usage high: {metrics.memory_usage_mb:.1f}MB",
                details={'memory_usage_mb': metrics.memory_usage_mb, 'threshold': self.alert_thresholds['memory_usage_warning']}
            ))
        
        # Check CPU usage
        if metrics.cpu_usage_percent > self.alert_thresholds['cpu_usage_error']:
            alerts.append(PerformanceAlert(
                timestamp=metrics.timestamp,
                severity='error',
                category='system',
                message=f"CPU usage too high: {metrics.cpu_usage_percent:.1f}%",
                details={'cpu_usage_percent': metrics.cpu_usage_percent, 'threshold': self.alert_thresholds['cpu_usage_error']}
            ))
        elif metrics.cpu_usage_percent > self.alert_thresholds['cpu_usage_warning']:
            alerts.append(PerformanceAlert(
                timestamp=metrics.timestamp,
                severity='warning',
                category='system',
                message=f"CPU usage high: {metrics.cpu_usage_percent:.1f}%",
                details={'cpu_usage_percent': metrics.cpu_usage_percent, 'threshold': self.alert_thresholds['cpu_usage_warning']}
            ))
        
        # Check error rate (if we have enough data)
        if self.stats['total_steps'] > 10:
            error_rate = self.stats['total_errors'] / self.stats['total_steps']
            if error_rate > self.alert_thresholds['error_rate_error']:
                alerts.append(PerformanceAlert(
                    timestamp=metrics.timestamp,
                    severity='error',
                    category='error_rate',
                    message=f"Error rate too high: {error_rate:.1%}",
                    details={'error_rate': error_rate, 'threshold': self.alert_thresholds['error_rate_error']}
                ))
            elif error_rate > self.alert_thresholds['error_rate_warning']:
                alerts.append(PerformanceAlert(
                    timestamp=metrics.timestamp,
                    severity='warning',
                    category='error_rate',
                    message=f"Error rate high: {error_rate:.1%}",
                    details={'error_rate': error_rate, 'threshold': self.alert_thresholds['error_rate_warning']}
                ))
        
        # Add alerts to history and trigger callbacks
        for alert in alerts:
            self.alerts_history.append(alert)
            logger.warning(f"Performance alert: {alert.severity.upper()} - {alert.message}")
            
            # Trigger callbacks
            for callback in self.alert_callbacks:
                try:
                    callback(alert)
                except Exception as e:
                    logger.error(f"Alert callback failed: {e}") 