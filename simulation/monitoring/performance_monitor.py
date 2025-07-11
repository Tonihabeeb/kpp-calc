import time
import threading
import psutil
import os
import logging
import numpy as np
from typing import Any, Callable, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from collections import deque
from datetime import datetime
import json

"""
Enhanced Performance monitoring module for KPP simulation.
Handles detailed performance analysis, bottleneck detection, and real-time monitoring.
"""

@dataclass
class PerformanceMetrics:
    """Individual step performance metrics"""
    timestamp: float
    step_duration: float
    physics_time: float
    electrical_time: float
    mechanical_time: float
    control_time: float
    memory_usage: float
    cpu_usage: float
    component_times: Dict[str, float] = field(default_factory=dict)
    bottleneck_components: List[str] = field(default_factory=list)

@dataclass
class PerformanceAlert:
    """Performance alert with severity and details"""
    timestamp: float
    alert_type: str
    severity: str  # 'low', 'medium', 'high', 'critical'
    message: str
    metrics: Dict[str, Any]
    component: Optional[str] = None

@dataclass
class EnergySnapshot:
    """Snapshot of energy states at a point in time"""
    timestamp: float
    buoyant_work: float = 0.0  # Work done by buoyancy
    gravity_work: float = 0.0   # Work done by gravity
    drag_loss: float = 0.0      # Energy lost to drag
    compressor_work: float = 0.0  # Energy used by compressor
    generator_work: float = 0.0   # Energy produced by generator
    kinetic_energy: float = 0.0   # Current kinetic energy of system
    net_power: float = 0.0        # Net power output
    chain_speed: float = 0.0      # Chain speed at this instant
    efficiency: float = 0.0       # Instantaneous efficiency

@dataclass
class SystemState:
    """System state snapshot"""
    timestamp: float
    component_states: Dict[str, Any]
    performance_metrics: Dict[str, Any]

class PerformanceMonitor:
    """Enhanced performance monitoring with bottleneck detection and real-time analysis"""
    
    def __init__(self, 
                 log_interval: float = 0.1,
                 alert_thresholds: Optional[Dict[str, float]] = None,
                 max_history_size: int = 1000):
        self.logger = logging.getLogger(__name__)
        
        # Performance tracking
        self.performance_history: List[PerformanceMetrics] = []
        self.energy_log: List[EnergySnapshot] = []
        self.state_history: List[SystemState] = []
        self.alerts: List[PerformanceAlert] = []
        
        # Configuration
        self.log_interval = log_interval
        self.last_log_time = 0.0
        self.max_history_size = max_history_size
        
        # Alert thresholds
        self.alert_thresholds = alert_thresholds or {
            'step_duration_ms': 50.0,      # 50ms max step time
            'memory_usage_mb': 500.0,      # 500MB max memory
            'cpu_usage_percent': 80.0,     # 80% max CPU
            'component_time_ms': 20.0,     # 20ms max per component
            'error_rate_percent': 5.0      # 5% max error rate
        }
        
        # Statistics tracking
        self.cumulative_stats = {
            'total_steps': 0,
            'total_physics_time': 0.0,
            'total_electrical_time': 0.0,
            'total_mechanical_time': 0.0,
            'total_control_time': 0.0,
            'peak_step_duration': 0.0,
            'avg_step_duration': 0.0,
            'total_runtime': 0.0,
            'error_count': 0,
            'alert_count': 0
        }
        
        # Component performance tracking
        self.component_performance: Dict[str, Dict[str, Any]] = {}
        
        # Moving averages for smoothed metrics
        self.power_window = deque(maxlen=50)
        self.speed_window = deque(maxlen=50)
        self.step_time_window = deque(maxlen=100)
        
        # Thread safety
        self.lock = threading.Lock()
        
        # Alert callbacks
        self.alert_callbacks: List[Callable[[PerformanceAlert], None]] = []
        
        # Start monitoring thread
        self.monitoring_active = True
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitoring_thread.start()
        
    def register_alert_callback(self, callback: Callable[[PerformanceAlert], None]):
        """Register callback for performance alerts"""
        self.alert_callbacks.append(callback)
    
    def should_log(self, current_time: float) -> bool:
        """Check if enough time has passed to log new data"""
        return (current_time - self.last_log_time) >= self.log_interval
    
    def record_step_performance(self, 
                              step_duration: float,
                              component_times: Dict[str, float],
                              memory_usage: Optional[float] = None,
                              cpu_usage: Optional[float] = None) -> PerformanceMetrics:
        """Record detailed performance metrics for a simulation step"""
        
        # Get system metrics if not provided
        if memory_usage is None:
            memory_usage = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        if cpu_usage is None:
            cpu_usage = psutil.cpu_percent()
        
        # Calculate component times
        physics_time = component_times.get('physics', 0.0)
        electrical_time = component_times.get('electrical', 0.0)
        mechanical_time = component_times.get('mechanical', 0.0)
        control_time = component_times.get('control', 0.0)
        
        # Identify bottlenecks
        bottleneck_components = []
        for component, time_taken in component_times.items():
            if time_taken * 1000 > self.alert_thresholds['component_time_ms']:
                bottleneck_components.append(component)
        
        # Create metrics object
        metrics = PerformanceMetrics(
            timestamp=time.time(),
            step_duration=step_duration,
            physics_time=physics_time,
            electrical_time=electrical_time,
            mechanical_time=mechanical_time,
            control_time=control_time,
            memory_usage=memory_usage,
            cpu_usage=cpu_usage,
            component_times=component_times.copy(),
            bottleneck_components=bottleneck_components
        )
        
        with self.lock:
            # Add to history
            self.performance_history.append(metrics)
            if len(self.performance_history) > self.max_history_size:
                self.performance_history.pop(0)
            
            # Update statistics
            self._update_statistics(metrics)
            
            # Update component performance tracking
            self._update_component_performance(component_times)
            
            # Check for alerts
            self._check_alerts(metrics)
            
            # Update moving averages
            self.step_time_window.append(step_duration * 1000)  # Convert to ms
        
        return metrics
    
    def _update_statistics(self, metrics: PerformanceMetrics):
        """Update cumulative statistics"""
        self.cumulative_stats['total_steps'] += 1
        self.cumulative_stats['total_physics_time'] += metrics.physics_time
        self.cumulative_stats['total_electrical_time'] += metrics.electrical_time
        self.cumulative_stats['total_mechanical_time'] += metrics.mechanical_time
        self.cumulative_stats['total_control_time'] += metrics.control_time
        self.cumulative_stats['peak_step_duration'] = max(
            self.cumulative_stats['peak_step_duration'], 
            metrics.step_duration
        )
        
        # Update average step duration
        total_steps = self.cumulative_stats['total_steps']
        current_avg = self.cumulative_stats['avg_step_duration']
        self.cumulative_stats['avg_step_duration'] = (
            (current_avg * (total_steps - 1) + metrics.step_duration) / total_steps
        )
    
    def _update_component_performance(self, component_times: Dict[str, float]):
        """Update component-specific performance tracking"""
        for component, time_taken in component_times.items():
            if component not in self.component_performance:
                self.component_performance[component] = {
                    'total_time': 0.0,
                    'call_count': 0,
                    'avg_time': 0.0,
                    'peak_time': 0.0,
                    'last_update': time.time()
                }
            
            comp_stats = self.component_performance[component]
            comp_stats['total_time'] += time_taken
            comp_stats['call_count'] += 1
            comp_stats['avg_time'] = comp_stats['total_time'] / comp_stats['call_count']
            comp_stats['peak_time'] = max(comp_stats['peak_time'], time_taken)
            comp_stats['last_update'] = time.time()
    
    def _check_alerts(self, metrics: PerformanceMetrics):
        """Check for performance alerts and generate them"""
        alerts = []
        
        # Step duration alert
        if metrics.step_duration * 1000 > self.alert_thresholds['step_duration_ms']:
            alerts.append(PerformanceAlert(
                timestamp=metrics.timestamp,
                alert_type='step_duration',
                severity='high' if metrics.step_duration * 1000 > 100 else 'medium',
                message=f"Step duration exceeded threshold: {metrics.step_duration*1000:.1f}ms",
                metrics={'step_duration_ms': metrics.step_duration * 1000},
                component='simulation_loop'
            ))
        
        # Memory usage alert
        if metrics.memory_usage > self.alert_thresholds['memory_usage_mb']:
            alerts.append(PerformanceAlert(
                timestamp=metrics.timestamp,
                alert_type='memory_usage',
                severity='high' if metrics.memory_usage > 1000 else 'medium',
                message=f"Memory usage exceeded threshold: {metrics.memory_usage:.1f}MB",
                metrics={'memory_usage_mb': metrics.memory_usage},
                component='system'
            ))
        
        # CPU usage alert
        if metrics.cpu_usage > self.alert_thresholds['cpu_usage_percent']:
            alerts.append(PerformanceAlert(
                timestamp=metrics.timestamp,
                alert_type='cpu_usage',
                severity='medium',
                message=f"CPU usage exceeded threshold: {metrics.cpu_usage:.1f}%",
                metrics={'cpu_usage_percent': metrics.cpu_usage},
                component='system'
            ))
        
        # Component performance alerts
        for component in metrics.bottleneck_components:
            alerts.append(PerformanceAlert(
                timestamp=metrics.timestamp,
                alert_type='component_performance',
                severity='medium',
                message=f"Component {component} taking too long: {metrics.component_times[component]*1000:.1f}ms",
                metrics={'component_time_ms': metrics.component_times[component] * 1000},
                component=component
            ))
        
        # Add alerts and trigger callbacks
        for alert in alerts:
            self.alerts.append(alert)
            if len(self.alerts) > self.max_history_size:
                self.alerts.pop(0)
            
            self.cumulative_stats['alert_count'] += 1
            
            # Trigger callbacks
            for callback in self.alert_callbacks:
                try:
                    callback(alert)
                except Exception as e:
                    self.logger.error(f"Error in alert callback: {e}")
    
    def log_energy_state(self, time: float, buoyant: float, gravity: float, 
                        drag: float, compressor: float, generator: float,
                        kinetic: float, chain_speed: float):
        """Log instantaneous energy state"""
        if not self.should_log(time):
            return
            
        efficiency = abs(generator / compressor) if compressor > 0 else 0.0
        
        snapshot = EnergySnapshot(
            timestamp=time,
            buoyant_work=buoyant,
            gravity_work=gravity,
            drag_loss=drag,
            compressor_work=compressor,
            generator_work=generator,
            kinetic_energy=kinetic,
            net_power=generator - compressor,
            chain_speed=chain_speed,
            efficiency=efficiency
        )
        
        with self.lock:
            self.energy_log.append(snapshot)
            if len(self.energy_log) > self.max_history_size:
                self.energy_log.pop(0)
            
            # Update moving averages
            self.power_window.append(generator - compressor)
            self.speed_window.append(chain_speed)
            
            self.last_log_time = time
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary"""
        with self.lock:
            recent_metrics = self.performance_history[-100:] if self.performance_history else []
            
            if not recent_metrics:
                return {
                    'status': 'no_data',
                    'message': 'No performance data available'
                }
            
            # Calculate recent statistics
            recent_step_times = [m.step_duration * 1000 for m in recent_metrics]
            recent_memory = [m.memory_usage for m in recent_metrics]
            recent_cpu = [m.cpu_usage for m in recent_metrics]
            
            # Identify top bottlenecks
            component_bottlenecks = {}
            for component, stats in self.component_performance.items():
                if stats['avg_time'] * 1000 > 5.0:  # Components taking >5ms on average
                    component_bottlenecks[component] = {
                        'avg_time_ms': stats['avg_time'] * 1000,
                        'peak_time_ms': stats['peak_time'] * 1000,
                        'call_count': stats['call_count']
                    }
            
            # Sort bottlenecks by average time
            sorted_bottlenecks = sorted(
                component_bottlenecks.items(),
                key=lambda x: x[1]['avg_time_ms'],
                reverse=True
            )
            
            return {
                'status': 'active',
                'current_performance': {
                    'avg_step_time_ms': np.mean(recent_step_times) if recent_step_times else 0,
                    'peak_step_time_ms': np.max(recent_step_times) if recent_step_times else 0,
                    'avg_memory_mb': np.mean(recent_memory) if recent_memory else 0,
                    'avg_cpu_percent': np.mean(recent_cpu) if recent_cpu else 0,
                    'target_fps': 50,  # Target 50Hz
                    'actual_fps': 1000 / np.mean(recent_step_times) if recent_step_times and np.mean(recent_step_times) > 0 else 0
                },
                'cumulative_stats': self.cumulative_stats.copy(),
                'top_bottlenecks': sorted_bottlenecks[:5],  # Top 5 bottlenecks
                'recent_alerts': len([a for a in self.alerts if time.time() - a.timestamp < 60]),  # Alerts in last minute
                'component_performance': self.component_performance,
                'recommendations': self._generate_recommendations(recent_metrics, sorted_bottlenecks)
            }
    
    def _generate_recommendations(self, recent_metrics: List[PerformanceMetrics], 
                                bottlenecks: List[Tuple[str, Dict]]) -> List[str]:
        """Generate performance improvement recommendations"""
        recommendations = []
        
        if not recent_metrics:
            return recommendations
        
        avg_step_time = np.mean([m.step_duration * 1000 for m in recent_metrics])
        
        # Step time recommendations
        if avg_step_time > 50:
            recommendations.append("Consider reducing simulation complexity or increasing time step")
        elif avg_step_time > 20:
            recommendations.append("Monitor for performance degradation during long runs")
        
        # Bottleneck-specific recommendations
        for component, stats in bottlenecks[:3]:  # Top 3 bottlenecks
            if stats['avg_time_ms'] > 20:
                recommendations.append(f"Optimize {component} component (avg: {stats['avg_time_ms']:.1f}ms)")
            elif stats['avg_time_ms'] > 10:
                recommendations.append(f"Profile {component} component for potential optimization")
        
        # Memory recommendations
        recent_memory = [m.memory_usage for m in recent_metrics]
        if recent_memory and np.mean(recent_memory) > 400:
            recommendations.append("Monitor memory usage - consider implementing memory cleanup")
        
        # CPU recommendations
        recent_cpu = [m.cpu_usage for m in recent_metrics]
        if recent_cpu and np.mean(recent_cpu) > 70:
            recommendations.append("High CPU usage detected - consider load balancing or optimization")
        
        return recommendations
    
    def _monitoring_loop(self):
        """Background monitoring loop"""
        while self.monitoring_active:
            try:
                # Update system metrics periodically
                self._update_system_metrics()
                time.sleep(5.0)  # Update every 5 seconds
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                time.sleep(10.0)  # Wait longer on error
    
    def _update_system_metrics(self):
        """Update system-wide metrics"""
        try:
            process = psutil.Process()
            
            # Memory usage
            memory_info = process.memory_info()
            memory_percent = process.memory_percent()
            
            # CPU usage
            cpu_percent = process.cpu_percent()
            
            # Log system metrics
            self.logger.debug(f"System metrics - Memory: {memory_info.rss/1024/1024:.1f}MB ({memory_percent:.1f}%), CPU: {cpu_percent:.1f}%")
            
        except Exception as e:
            self.logger.error(f"Error updating system metrics: {e}")
    
    def export_performance_data(self, filename: str):
        """Export performance data to JSON file"""
        try:
            with self.lock:
                data = {
                    'export_timestamp': datetime.now().isoformat(),
                    'performance_history': [
                        {
                            'timestamp': m.timestamp,
                            'step_duration': m.step_duration,
                            'memory_usage': m.memory_usage,
                            'cpu_usage': m.cpu_usage,
                            'component_times': m.component_times,
                            'bottleneck_components': m.bottleneck_components
                        }
                        for m in self.performance_history
                    ],
                    'component_performance': self.component_performance,
                    'cumulative_stats': self.cumulative_stats,
                    'alerts': [
                        {
                            'timestamp': a.timestamp,
                            'alert_type': a.alert_type,
                            'severity': a.severity,
                            'message': a.message,
                            'component': a.component
                        }
                        for a in self.alerts
                    ]
                }
            
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2)
            
            self.logger.info(f"Performance data exported to {filename}")
            
        except Exception as e:
            self.logger.error(f"Error exporting performance data: {e}")
    
    def clear_history(self):
        """Clear performance history"""
        with self.lock:
            self.performance_history.clear()
            self.energy_log.clear()
            self.state_history.clear()
            self.alerts.clear()
            self.component_performance.clear()
            self.cumulative_stats = {
                'total_steps': 0,
                'total_physics_time': 0.0,
                'total_electrical_time': 0.0,
                'total_mechanical_time': 0.0,
                'total_control_time': 0.0,
                'peak_step_duration': 0.0,
                'avg_step_duration': 0.0,
                'total_runtime': 0.0,
                'error_count': 0,
                'alert_count': 0
            }
    
    def stop(self):
        """Stop the performance monitor"""
        self.monitoring_active = False
        if self.monitoring_thread.is_alive():
            self.monitoring_thread.join(timeout=5.0)

# Global performance monitor instance
_performance_monitor: Optional[PerformanceMonitor] = None
_monitor_lock = threading.Lock()

def get_performance_monitor() -> PerformanceMonitor:
    """Get or create the global PerformanceMonitor instance"""
    global _performance_monitor
    
    if _performance_monitor is None:
        with _monitor_lock:
            if _performance_monitor is None:
                _performance_monitor = PerformanceMonitor()
    
    return _performance_monitor

