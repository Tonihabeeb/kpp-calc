import time
import threading
import psutil
import os
import logging
from typing import Any, Callable, Dict, List, Optional
from dataclasses import dataclass, field
from collections import deque
"""
Performance monitoring system for KPP Simulator.

This module provides comprehensive performance monitoring including:
- Step execution time tracking
- Memory usage monitoring
- Error rate tracking
- Performance alerts and warnings
"""

@dataclass
class PerformanceMetrics:
    """Performance metrics data structure."""
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    execution_time: float = 0.0
    error_count: int = 0
    timestamp: float = field(default_factory=time.time)

@dataclass
class PerformanceAlert:
    """Performance alert data structure."""
    alert_type: str = ""
    message: str = ""
    severity: str = "warning"
    timestamp: float = field(default_factory=time.time)
    metrics: Optional[PerformanceMetrics] = None

class PerformanceMonitor:
    """Performance monitoring system."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.metrics_history: List[PerformanceMetrics] = []
        self.alerts: List[PerformanceAlert] = []
        self.is_monitoring = False
        self.monitor_thread = None
    
    def start_monitoring(self):
        """Start performance monitoring."""
        self.is_monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop)
        self.monitor_thread.start()
        self.logger.info("Performance monitoring started")
    
    def stop_monitoring(self):
        """Stop performance monitoring."""
        self.is_monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join()
        self.logger.info("Performance monitoring stopped")
    
    def _monitor_loop(self):
        """Main monitoring loop."""
        while self.is_monitoring:
            try:
                metrics = self._collect_metrics()
                self.metrics_history.append(metrics)
                
                # Check for alerts
                if metrics.cpu_usage > 80.0:
                    alert = PerformanceAlert(
                        alert_type="high_cpu",
                        message=f"High CPU usage: {metrics.cpu_usage:.1f}%",
                        severity="warning",
                        metrics=metrics
                    )
                    self.alerts.append(alert)
                
                time.sleep(1.0)  # Monitor every second
                
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
    
    def _collect_metrics(self) -> PerformanceMetrics:
        """Collect current performance metrics."""
        try:
            cpu_usage = psutil.cpu_percent(interval=0.1)
            memory_usage = psutil.virtual_memory().percent
            
            return PerformanceMetrics(
                cpu_usage=cpu_usage,
                memory_usage=memory_usage,
                execution_time=time.time(),
                error_count=0
            )
        except Exception as e:
            self.logger.error(f"Error collecting metrics: {e}")
            return PerformanceMetrics()
    
    def get_metrics(self) -> List[PerformanceMetrics]:
        """Get performance metrics history."""
        return self.metrics_history.copy()
    
    def get_alerts(self) -> List[PerformanceAlert]:
        """Get performance alerts."""
        return self.alerts.copy()

