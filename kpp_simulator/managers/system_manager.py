"""
System Manager for KPP Simulator
Coordinates overall system management and integration
"""

import logging
import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any, Callable
from datetime import datetime, timedelta
import psutil
import os

from .component_manager import ComponentManager
from ..config.manager import ConfigManager
from ..core.physics_engine import PhysicsEngine
from ..electrical.electrical_system import IntegratedElectricalSystem
from ..control_systems.control_system import IntegratedControlSystem
from ..grid_services.grid_services_coordinator import GridServicesCoordinator


class SystemStatus(Enum):
    """System status states"""
    INITIALIZING = "initializing"
    STARTING = "starting"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"
    MAINTENANCE = "maintenance"


class SystemMode(Enum):
    """System operation modes"""
    SIMULATION = "simulation"
    REAL_TIME = "real_time"
    OPTIMIZATION = "optimization"
    TESTING = "testing"
    MAINTENANCE = "maintenance"


@dataclass
class SystemMetrics:
    """System performance metrics"""
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    disk_usage: float = 0.0
    network_usage: float = 0.0
    simulation_time: float = 0.0
    real_time_factor: float = 1.0
    update_rate: float = 0.0
    error_count: int = 0
    warning_count: int = 0
    component_count: int = 0
    active_components: int = 0


@dataclass
class SystemEvent:
    """System event record"""
    timestamp: datetime
    event_type: str
    severity: str
    message: str
    data: Any = None


class SystemManager:
    """
    System Manager for KPP Simulator
    
    Features:
    - Overall system coordination and management
    - Performance monitoring and optimization
    - Resource management and allocation
    - Error handling and recovery
    - System integration and communication
    - Health monitoring and maintenance
    """
    
    def __init__(self):
        """Initialize the System Manager"""
        # System state
        self.status = SystemStatus.INITIALIZING
        self.mode = SystemMode.SIMULATION
        self.is_active = False
        
        # Managers
        self.component_manager = ComponentManager()
        self.config_manager = ConfigManager()
        
        # Core components (will be initialized later)
        self.physics_engine = None
        self.electrical_system = None
        self.control_system = None
        self.grid_services = None
        
        # System metrics
        self.system_metrics = SystemMetrics()
        self.metrics_history: List[Tuple[datetime, SystemMetrics]] = []
        
        # Event tracking
        self.system_events: List[SystemEvent] = []
        self.event_callbacks: Dict[str, List[Callable]] = {}
        
        # Performance monitoring
        self.monitoring_thread = None
        self.monitoring_interval = 1.0  # seconds
        self.max_metrics_history = 1000
        self.max_events_history = 1000
        
        # Resource limits
        self.resource_limits = {
            'max_cpu_usage': 0.9,  # 90%
            'max_memory_usage': 0.8,  # 80%
            'max_disk_usage': 0.9,  # 90%
            'min_update_rate': 10.0,  # Hz
            'max_error_rate': 0.1  # 10%
        }
        
        # Threading
        self.thread_lock = threading.Lock()
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        self.logger.info("System Manager initialized")
    
    def initialize_system(self) -> bool:
        """Initialize the complete system"""
        try:
            self.status = SystemStatus.INITIALIZING
            self.logger.info("Initializing KPP Simulator system...")
            
            # Load configurations
            if not self.config_manager.load_all_configurations():
                self.logger.error("Failed to load system configurations")
                return False
            
            # Initialize core components
            if not self._initialize_core_components():
                self.logger.error("Failed to initialize core components")
                return False
            
            # Register components with component manager
            if not self._register_components():
                self.logger.error("Failed to register components")
                return False
            
            # Start managers
            self.component_manager.start()
            self.config_manager.start()
            
            self.status = SystemStatus.STOPPED
            self.logger.info("System initialization completed successfully")
            return True
            
        except Exception as e:
            self.status = SystemStatus.ERROR
            self.logger.error(f"System initialization failed: {e}")
            return False
    
    def start_system(self) -> bool:
        """Start the system"""
        try:
            if self.status == SystemStatus.RUNNING:
                self.logger.warning("System already running")
                return True
            
            self.status = SystemStatus.STARTING
            self.logger.info("Starting KPP Simulator system...")
            
            # Start components in dependency order
            component_start_order = [
                'physics_engine',
                'electrical_system',
                'control_system',
                'grid_services'
            ]
            
            for component_id in component_start_order:
                if not self.component_manager.start_component(component_id):
                    self.logger.error(f"Failed to start component: {component_id}")
                    self.status = SystemStatus.ERROR
                    return False
            
            # Start monitoring
            self.is_active = True
            self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
            self.monitoring_thread.start()
            
            self.status = SystemStatus.RUNNING
            self._log_system_event("SYSTEM_STARTED", "INFO", "System started successfully")
            self.logger.info("KPP Simulator system started successfully")
            return True
            
        except Exception as e:
            self.status = SystemStatus.ERROR
            self.logger.error(f"System start failed: {e}")
            return False
    
    def stop_system(self) -> bool:
        """Stop the system"""
        try:
            if self.status == SystemStatus.STOPPED:
                self.logger.warning("System already stopped")
                return True
            
            self.status = SystemStatus.STOPPING
            self.logger.info("Stopping KPP Simulator system...")
            
            # Stop monitoring
            self.is_active = False
            if self.monitoring_thread and self.monitoring_thread.is_alive():
                self.monitoring_thread.join(timeout=5.0)
            
            # Stop component manager
            self.component_manager.stop()
            
            # Stop config manager
            self.config_manager.stop()
            
            self.status = SystemStatus.STOPPED
            self._log_system_event("SYSTEM_STOPPED", "INFO", "System stopped successfully")
            self.logger.info("KPP Simulator system stopped successfully")
            return True
            
        except Exception as e:
            self.status = SystemStatus.ERROR
            self.logger.error(f"System stop failed: {e}")
            return False
    
    def pause_system(self) -> bool:
        """Pause the system"""
        try:
            if self.status != SystemStatus.RUNNING:
                self.logger.warning("System not running, cannot pause")
                return False
            
            self.status = SystemStatus.PAUSED
            self._log_system_event("SYSTEM_PAUSED", "INFO", "System paused")
            self.logger.info("System paused")
            return True
            
        except Exception as e:
            self.logger.error(f"System pause failed: {e}")
            return False
    
    def resume_system(self) -> bool:
        """Resume the system"""
        try:
            if self.status != SystemStatus.PAUSED:
                self.logger.warning("System not paused, cannot resume")
                return False
            
            self.status = SystemStatus.RUNNING
            self._log_system_event("SYSTEM_RESUMED", "INFO", "System resumed")
            self.logger.info("System resumed")
            return True
            
        except Exception as e:
            self.logger.error(f"System resume failed: {e}")
            return False
    
    def set_system_mode(self, mode: SystemMode) -> bool:
        """Set system operation mode"""
        try:
            old_mode = self.mode
            self.mode = mode
            
            self._log_system_event("MODE_CHANGED", "INFO", 
                                  f"System mode changed from {old_mode.value} to {mode.value}")
            self.logger.info(f"System mode changed: {old_mode.value} -> {mode.value}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to set system mode: {e}")
            return False
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        return {
            'status': self.status.value,
            'mode': self.mode.value,
            'is_active': self.is_active,
            'metrics': {
                'cpu_usage': self.system_metrics.cpu_usage,
                'memory_usage': self.system_metrics.memory_usage,
                'disk_usage': self.system_metrics.disk_usage,
                'simulation_time': self.system_metrics.simulation_time,
                'real_time_factor': self.system_metrics.real_time_factor,
                'update_rate': self.system_metrics.update_rate,
                'error_count': self.system_metrics.error_count,
                'component_count': self.system_metrics.component_count,
                'active_components': self.system_metrics.active_components
            },
            'components': self.component_manager.get_all_components(),
            'config_status': self.config_manager.get_configuration_summary()
        }
    
    def get_performance_metrics(self) -> SystemMetrics:
        """Get current performance metrics"""
        return self.system_metrics
    
    def get_metrics_history(self, duration: timedelta = timedelta(hours=1)) -> List[Tuple[datetime, SystemMetrics]]:
        """Get metrics history for specified duration"""
        cutoff_time = datetime.now() - duration
        return [(t, m) for t, m in self.metrics_history if t >= cutoff_time]
    
    def get_system_events(self, severity: Optional[str] = None, 
                         duration: timedelta = timedelta(hours=1)) -> List[SystemEvent]:
        """Get system events"""
        cutoff_time = datetime.now() - duration
        events = [e for e in self.system_events if e.timestamp >= cutoff_time]
        
        if severity:
            events = [e for e in events if e.severity == severity]
        
        return events
    
    def register_event_callback(self, event_type: str, callback: Callable):
        """Register an event callback"""
        if event_type not in self.event_callbacks:
            self.event_callbacks[event_type] = []
        
        self.event_callbacks[event_type].append(callback)
        self.logger.info(f"Event callback registered for: {event_type}")
    
    def _initialize_core_components(self) -> bool:
        """Initialize core system components"""
        try:
            # Initialize physics engine
            from ..core.physics_engine import PhysicsConfig
            physics_config = PhysicsConfig()
            self.physics_engine = PhysicsEngine(physics_config)
            
            # Initialize electrical system
            from ..electrical.electrical_system import ElectricalConfig
            electrical_config = ElectricalConfig()
            self.electrical_system = IntegratedElectricalSystem(electrical_config)
            
            # Initialize control system
            from ..control_systems.control_system import ControlConfig
            control_config = ControlConfig()
            self.control_system = IntegratedControlSystem(control_config)
            
            # Initialize grid services
            self.grid_services = GridServicesCoordinator(
                self.physics_engine,
                self.electrical_system,
                self.control_system
            )
            
            self.logger.info("Core components initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize core components: {e}")
            return False
    
    def _register_components(self) -> bool:
        """Register components with component manager"""
        try:
            # Register core components
            components = [
                ('physics_engine', self.physics_engine, 'PHYSICS_ENGINE', []),
                ('electrical_system', self.electrical_system, 'ELECTRICAL_SYSTEM', ['physics_engine']),
                ('control_system', self.control_system, 'CONTROL_SYSTEM', ['physics_engine', 'electrical_system']),
                ('grid_services', self.grid_services, 'GRID_SERVICES', ['electrical_system', 'control_system'])
            ]
            
            for component_id, component, component_type, dependencies in components:
                if not self.component_manager.register_component(component_id, component, component_type, dependencies):
                    self.logger.error(f"Failed to register component: {component_id}")
                    return False
            
            self.logger.info("All components registered successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to register components: {e}")
            return False
    
    def _monitoring_loop(self):
        """System monitoring loop"""
        while self.is_active:
            try:
                start_time = time.time()
                
                # Update system metrics
                self._update_system_metrics()
                
                # Check resource limits
                self._check_resource_limits()
                
                # Store metrics history
                self._store_metrics_history()
                
                # Sleep for remaining time
                elapsed_time = time.time() - start_time
                sleep_time = max(0, self.monitoring_interval - elapsed_time)
                if sleep_time > 0:
                    time.sleep(sleep_time)
                
            except Exception as e:
                self.logger.error(f"Monitoring loop error: {e}")
                time.sleep(self.monitoring_interval)
    
    def _update_system_metrics(self):
        """Update system performance metrics"""
        try:
            # Get system resource usage
            self.system_metrics.cpu_usage = psutil.cpu_percent(interval=0.1)
            self.system_metrics.memory_usage = psutil.virtual_memory().percent / 100.0
            self.system_metrics.disk_usage = psutil.disk_usage('/').percent / 100.0
            
            # Get component manager metrics
            component_metrics = self.component_manager.get_performance_metrics()
            self.system_metrics.component_count = component_metrics['component_count']
            self.system_metrics.active_components = component_metrics['active_components']
            
            # Calculate update rate
            if component_metrics['total_updates'] > 0:
                self.system_metrics.update_rate = 1.0 / component_metrics['average_update_time']
            
            # Update simulation time (simplified)
            if self.status == SystemStatus.RUNNING:
                self.system_metrics.simulation_time += self.monitoring_interval
            
            # Update error count
            self.system_metrics.error_count = component_metrics.get('error_count', 0)
            
        except Exception as e:
            self.logger.error(f"Failed to update system metrics: {e}")
    
    def _check_resource_limits(self):
        """Check system resource limits"""
        try:
            # Check CPU usage
            if self.system_metrics.cpu_usage > self.resource_limits['max_cpu_usage']:
                self._log_system_event("RESOURCE_WARNING", "WARNING", 
                                      f"High CPU usage: {self.system_metrics.cpu_usage:.1f}%")
            
            # Check memory usage
            if self.system_metrics.memory_usage > self.resource_limits['max_memory_usage']:
                self._log_system_event("RESOURCE_WARNING", "WARNING", 
                                      f"High memory usage: {self.system_metrics.memory_usage:.1f}%")
            
            # Check disk usage
            if self.system_metrics.disk_usage > self.resource_limits['max_disk_usage']:
                self._log_system_event("RESOURCE_WARNING", "WARNING", 
                                      f"High disk usage: {self.system_metrics.disk_usage:.1f}%")
            
            # Check update rate
            if self.system_metrics.update_rate < self.resource_limits['min_update_rate']:
                self._log_system_event("PERFORMANCE_WARNING", "WARNING", 
                                      f"Low update rate: {self.system_metrics.update_rate:.1f} Hz")
            
            # Check error rate
            total_components = self.system_metrics.component_count
            if total_components > 0:
                error_rate = self.system_metrics.error_count / total_components
                if error_rate > self.resource_limits['max_error_rate']:
                    self._log_system_event("ERROR_RATE_WARNING", "WARNING", 
                                          f"High error rate: {error_rate:.1f}%")
            
        except Exception as e:
            self.logger.error(f"Failed to check resource limits: {e}")
    
    def _store_metrics_history(self):
        """Store metrics in history"""
        try:
            # Create a copy of current metrics
            metrics_copy = SystemMetrics(
                cpu_usage=self.system_metrics.cpu_usage,
                memory_usage=self.system_metrics.memory_usage,
                disk_usage=self.system_metrics.disk_usage,
                network_usage=self.system_metrics.network_usage,
                simulation_time=self.system_metrics.simulation_time,
                real_time_factor=self.system_metrics.real_time_factor,
                update_rate=self.system_metrics.update_rate,
                error_count=self.system_metrics.error_count,
                warning_count=self.system_metrics.warning_count,
                component_count=self.system_metrics.component_count,
                active_components=self.system_metrics.active_components
            )
            
            self.metrics_history.append((datetime.now(), metrics_copy))
            
            # Limit history size
            if len(self.metrics_history) > self.max_metrics_history:
                self.metrics_history.pop(0)
                
        except Exception as e:
            self.logger.error(f"Failed to store metrics history: {e}")
    
    def _log_system_event(self, event_type: str, severity: str, message: str, data: Any = None):
        """Log a system event"""
        try:
            event = SystemEvent(
                timestamp=datetime.now(),
                event_type=event_type,
                severity=severity,
                message=message,
                data=data
            )
            
            self.system_events.append(event)
            
            # Limit events history
            if len(self.system_events) > self.max_events_history:
                self.system_events.pop(0)
            
            # Trigger event callbacks
            if event_type in self.event_callbacks:
                for callback in self.event_callbacks[event_type]:
                    try:
                        callback(event)
                    except Exception as e:
                        self.logger.error(f"Event callback error: {e}")
            
            # Log based on severity
            if severity == "ERROR":
                self.logger.error(f"System event: {message}")
            elif severity == "WARNING":
                self.logger.warning(f"System event: {message}")
            else:
                self.logger.info(f"System event: {message}")
                
        except Exception as e:
            self.logger.error(f"Failed to log system event: {e}")
    
    def clear_metrics_history(self):
        """Clear metrics history"""
        self.metrics_history.clear()
        self.logger.info("Metrics history cleared")
    
    def clear_system_events(self):
        """Clear system events"""
        self.system_events.clear()
        self.logger.info("System events cleared")
    
    def get_system_health(self) -> Dict[str, Any]:
        """Get system health assessment"""
        health_status = "HEALTHY"
        issues = []
        
        # Check resource usage
        if self.system_metrics.cpu_usage > 0.8:
            health_status = "WARNING"
            issues.append(f"High CPU usage: {self.system_metrics.cpu_usage:.1f}%")
        
        if self.system_metrics.memory_usage > 0.8:
            health_status = "WARNING"
            issues.append(f"High memory usage: {self.system_metrics.memory_usage:.1f}%")
        
        if self.system_metrics.error_count > 10:
            health_status = "CRITICAL"
            issues.append(f"High error count: {self.system_metrics.error_count}")
        
        # Check component status
        component_status = self.component_manager.get_all_components()
        error_components = [cid for cid, info in component_status.items() 
                           if info.status.value == "error"]
        
        if error_components:
            health_status = "CRITICAL"
            issues.append(f"Components in error: {error_components}")
        
        return {
            'status': health_status,
            'issues': issues,
            'timestamp': datetime.now().isoformat()
        } 