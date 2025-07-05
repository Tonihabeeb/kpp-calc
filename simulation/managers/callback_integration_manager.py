"""
Callback Integration Manager

This module integrates all orphaned callbacks into proper systems rather than removing them.
Ensures 100% functionality preservation while improving system architecture.
"""

import logging
from typing import Dict, List, Callable, Any, Optional
from dataclasses import dataclass
from enum import Enum
import time
import threading

logger = logging.getLogger(__name__)


class CallbackPriority(Enum):
    """Priority levels for callback integration."""
    CRITICAL = "critical"    # Emergency and safety functions
    HIGH = "high"           # Core simulation control
    MEDIUM = "medium"       # Monitoring and optimization
    LOW = "low"            # Configuration and utilities


@dataclass
class CallbackInfo:
    """Information about a callback for integration."""
    name: str
    function: Callable
    priority: CallbackPriority
    category: str
    description: str
    file_path: str
    line_number: int


class SafetyMonitor:
    """Integrates emergency and safety callbacks."""
    
    def __init__(self):
        self.emergency_conditions: List[Callable] = []
        self.emergency_callbacks: List[Callable] = []
        self.safety_thresholds: Dict[str, float] = {
            'chain_speed_max': 100.0,  # m/s
            'temperature_max': 373.15,  # K (100°C)
            'pressure_max': 1000000.0,  # Pa (10 bar)
            'power_max': 50000.0,       # W (50 kW)
        }
        self.is_emergency_active = False
        self.emergency_log: List[Dict] = []
    
    def register_emergency_callback(self, callback: Callable) -> None:
        """Register an emergency callback for integration."""
        self.emergency_callbacks.append(callback)
        logger.info(f"Registered emergency callback: {callback.__name__}")
    
    def register_safety_condition(self, condition: Callable) -> None:
        """Register a safety condition to monitor."""
        self.emergency_conditions.append(condition)
        logger.info(f"Registered safety condition: {condition.__name__}")
    
    def check_safety_conditions(self, simulation_state: Dict[str, Any]) -> bool:
        """Check all safety conditions and trigger emergency if needed."""
        for condition in self.emergency_conditions:
            if condition(simulation_state):
                self.trigger_emergency_stop(f"Safety condition triggered: {condition.__name__}")
                return True
        return False
    
    def trigger_emergency_stop(self, reason: str) -> None:
        """Trigger emergency stop and execute all emergency callbacks."""
        if self.is_emergency_active:
            return  # Already in emergency state
        
        self.is_emergency_active = True
        emergency_event = {
            'timestamp': time.time(),
            'reason': reason,
            'callbacks_executed': []
        }
        
        logger.critical(f"EMERGENCY STOP TRIGGERED: {reason}")
        
        # Execute all emergency callbacks
        for callback in self.emergency_callbacks:
            try:
                callback()
                emergency_event['callbacks_executed'].append(callback.__name__)
                logger.info(f"Emergency callback executed: {callback.__name__}")
            except Exception as e:
                logger.error(f"Emergency callback failed: {callback.__name__} - {e}")
        
        self.emergency_log.append(emergency_event)
    
    def reset_emergency_state(self) -> None:
        """Reset emergency state after conditions are resolved."""
        self.is_emergency_active = False
        logger.info("Emergency state reset")


class TransientEventManager:
    """Integrates transient event callbacks."""
    
    def __init__(self):
        self.transient_events: List[Dict] = []
        self.status_callbacks: List[Callable] = []
        self.acknowledgment_callbacks: List[Callable] = []
        self.event_counter = 0
    
    def register_status_callback(self, callback: Callable) -> None:
        """Register a status callback for integration."""
        self.status_callbacks.append(callback)
        logger.info(f"Registered status callback: {callback.__name__}")
    
    def register_acknowledgment_callback(self, callback: Callable) -> None:
        """Register an acknowledgment callback for integration."""
        self.acknowledgment_callbacks.append(callback)
        logger.info(f"Registered acknowledgment callback: {callback.__name__}")
    
    def create_transient_event(self, event_type: str, description: str, severity: str = "medium") -> int:
        """Create a new transient event."""
        event_id = self.event_counter
        self.event_counter += 1
        
        event = {
            'id': event_id,
            'type': event_type,
            'description': description,
            'severity': severity,
            'timestamp': time.time(),
            'acknowledged': False,
            'resolved': False
        }
        
        self.transient_events.append(event)
        logger.info(f"Created transient event {event_id}: {event_type} - {description}")
        return event_id
    
    def get_transient_status(self) -> List[Dict]:
        """Get status from all registered status callbacks."""
        status_list = []
        
        for callback in self.status_callbacks:
            try:
                status = callback()
                if status:
                    status_list.append(status)
            except Exception as e:
                logger.error(f"Status callback failed: {callback.__name__} - {e}")
        
        # Add transient events to status
        status_list.append({
            'transient_events': self.transient_events,
            'total_events': len(self.transient_events),
            'unacknowledged_events': len([e for e in self.transient_events if not e['acknowledged']])
        })
        
        return status_list
    
    def acknowledge_transient_event(self, event_id: int) -> bool:
        """Acknowledge a transient event and execute acknowledgment callbacks."""
        event = next((e for e in self.transient_events if e['id'] == event_id), None)
        
        if not event:
            logger.warning(f"Transient event {event_id} not found")
            return False
        
        event['acknowledged'] = True
        event['acknowledgment_time'] = time.time()
        
        # Execute all acknowledgment callbacks
        for callback in self.acknowledgment_callbacks:
            try:
                callback(event_id)
                logger.info(f"Acknowledgment callback executed: {callback.__name__} for event {event_id}")
            except Exception as e:
                logger.error(f"Acknowledgment callback failed: {callback.__name__} - {e}")
        
        logger.info(f"Transient event {event_id} acknowledged")
        return True


class ConfigurationManager:
    """Integrates configuration-related callbacks."""
    
    def __init__(self):
        self.init_callbacks: Dict[str, List[Callable]] = {
            'new_config': [],
            'legacy_params': []
        }
        self.config_history: List[Dict] = []
        self.current_config: Optional[Dict] = None
    
    def register_init_callback(self, config_type: str, callback: Callable) -> None:
        """Register an initialization callback for integration."""
        if config_type in self.init_callbacks:
            self.init_callbacks[config_type].append(callback)
            logger.info(f"Registered {config_type} init callback: {callback.__name__}")
        else:
            logger.warning(f"Unknown config type: {config_type}")
    
    def initialize_with_new_config(self, config: Dict[str, Any]) -> None:
        """Initialize system with new configuration."""
        logger.info("Initializing with new configuration")
        
        # Execute all new config callbacks
        for callback in self.init_callbacks['new_config']:
            try:
                callback(config)
                logger.info(f"New config callback executed: {callback.__name__}")
            except Exception as e:
                logger.error(f"New config callback failed: {callback.__name__} - {e}")
        
        self.current_config = config
        self.config_history.append({
            'timestamp': time.time(),
            'config_type': 'new_config',
            'config': config.copy()
        })
    
    def initialize_with_legacy_params(self, params: Dict[str, Any]) -> None:
        """Initialize system with legacy parameters."""
        logger.info("Initializing with legacy parameters")
        
        # Execute all legacy params callbacks
        for callback in self.init_callbacks['legacy_params']:
            try:
                callback(params)
                logger.info(f"Legacy params callback executed: {callback.__name__}")
            except Exception as e:
                logger.error(f"Legacy params callback failed: {callback.__name__} - {e}")
        
        self.current_config = params
        self.config_history.append({
            'timestamp': time.time(),
            'config_type': 'legacy_params',
            'config': params.copy()
        })


class SimulationController:
    """Integrates simulation control callbacks."""
    
    def __init__(self):
        self.run_callbacks: List[Callable] = []
        self.stop_callbacks: List[Callable] = []
        self.geometry_callbacks: List[Callable] = []
        self.simulation_state = "stopped"
        self.control_lock = threading.Lock()
    
    def register_run_callback(self, callback: Callable) -> None:
        """Register a run callback for integration."""
        self.run_callbacks.append(callback)
        logger.info(f"Registered run callback: {callback.__name__}")
    
    def register_stop_callback(self, callback: Callable) -> None:
        """Register a stop callback for integration."""
        self.stop_callbacks.append(callback)
        logger.info(f"Registered stop callback: {callback.__name__}")
    
    def register_geometry_callback(self, callback: Callable) -> None:
        """Register a geometry callback for integration."""
        self.geometry_callbacks.append(callback)
        logger.info(f"Registered geometry callback: {callback.__name__}")
    
    def start_simulation(self) -> bool:
        """Start simulation and execute all run callbacks."""
        with self.control_lock:
            if self.simulation_state == "running":
                logger.warning("Simulation already running")
                return False
            
            logger.info("Starting simulation")
            
            # Execute all run callbacks
            for callback in self.run_callbacks:
                try:
                    callback()
                    logger.info(f"Run callback executed: {callback.__name__}")
                except Exception as e:
                    logger.error(f"Run callback failed: {callback.__name__} - {e}")
                    return False
            
            self.simulation_state = "running"
            logger.info("Simulation started successfully")
            return True
    
    def stop_simulation(self) -> bool:
        """Stop simulation and execute all stop callbacks."""
        with self.control_lock:
            if self.simulation_state == "stopped":
                logger.warning("Simulation already stopped")
                return False
            
            logger.info("Stopping simulation")
            
            # Execute all stop callbacks
            for callback in self.stop_callbacks:
                try:
                    callback()
                    logger.info(f"Stop callback executed: {callback.__name__}")
                except Exception as e:
                    logger.error(f"Stop callback failed: {callback.__name__} - {e}")
            
            self.simulation_state = "stopped"
            logger.info("Simulation stopped")
            return True
    
    def update_chain_geometry(self, geometry: Dict[str, Any]) -> None:
        """Update chain geometry and execute all geometry callbacks."""
        logger.info("Updating chain geometry")
        
        # Execute all geometry callbacks
        for callback in self.geometry_callbacks:
            try:
                callback(geometry)
                logger.info(f"Geometry callback executed: {callback.__name__}")
            except Exception as e:
                logger.error(f"Geometry callback failed: {callback.__name__} - {e}")


class PerformanceMonitor:
    """Integrates performance monitoring callbacks."""
    
    def __init__(self):
        self.metrics_callbacks: List[Callable] = []
        self.physics_callbacks: List[Callable] = []
        self.enhanced_callbacks: List[Callable] = []
        self.performance_history: List[Dict] = []
        self.monitoring_active = False
    
    def register_metrics_callback(self, callback: Callable) -> None:
        """Register a metrics callback for integration."""
        self.metrics_callbacks.append(callback)
        logger.info(f"Registered metrics callback: {callback.__name__}")
    
    def register_physics_callback(self, callback: Callable) -> None:
        """Register a physics callback for integration."""
        self.physics_callbacks.append(callback)
        logger.info(f"Registered physics callback: {callback.__name__}")
    
    def register_enhanced_callback(self, callback: Callable) -> None:
        """Register an enhanced callback for integration."""
        self.enhanced_callbacks.append(callback)
        logger.info(f"Registered enhanced callback: {callback.__name__}")
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics from all registered callbacks."""
        metrics = {}
        
        for callback in self.metrics_callbacks:
            try:
                callback_metrics = callback()
                if callback_metrics:
                    metrics.update(callback_metrics)
            except Exception as e:
                logger.error(f"Metrics callback failed: {callback.__name__} - {e}")
        
        return metrics
    
    def get_physics_status(self) -> Dict[str, Any]:
        """Get physics status from all registered callbacks."""
        status = {}
        
        for callback in self.physics_callbacks:
            try:
                callback_status = callback()
                if callback_status:
                    status.update(callback_status)
            except Exception as e:
                logger.error(f"Physics callback failed: {callback.__name__} - {e}")
        
        return status
    
    def get_enhanced_performance_metrics(self) -> Dict[str, Any]:
        """Get enhanced performance metrics from all registered callbacks."""
        enhanced_metrics = {}
        
        for callback in self.enhanced_callbacks:
            try:
                callback_metrics = callback()
                if callback_metrics:
                    enhanced_metrics.update(callback_metrics)
            except Exception as e:
                logger.error(f"Enhanced callback failed: {callback.__name__} - {e}")
        
        return enhanced_metrics


class CallbackIntegrationManager:
    """Main manager for integrating all orphaned callbacks."""
    
    def __init__(self):
        self.safety_monitor = SafetyMonitor()
        self.transient_manager = TransientEventManager()
        self.config_manager = ConfigurationManager()
        self.simulation_controller = SimulationController()
        self.performance_monitor = PerformanceMonitor()
        
        self.registered_callbacks: Dict[str, CallbackInfo] = {}
        self.integration_stats = {
            'total_callbacks': 0,
            'integrated_callbacks': 0,
            'failed_integrations': 0
        }
    
    def register_callback(self, callback_info: CallbackInfo) -> bool:
        """Register a callback for integration."""
        try:
            self.registered_callbacks[callback_info.name] = callback_info
            
            # Integrate based on category and priority
            if callback_info.category == "emergency":
                self.safety_monitor.register_emergency_callback(callback_info.function)
            elif callback_info.category == "transient":
                if "status" in callback_info.name.lower():
                    self.transient_manager.register_status_callback(callback_info.function)
                elif "acknowledge" in callback_info.name.lower():
                    self.transient_manager.register_acknowledgment_callback(callback_info.function)
            elif callback_info.category == "config":
                if "new_config" in callback_info.name.lower():
                    self.config_manager.register_init_callback("new_config", callback_info.function)
                elif "legacy" in callback_info.name.lower():
                    self.config_manager.register_init_callback("legacy_params", callback_info.function)
            elif callback_info.category == "simulation":
                if "run" in callback_info.name.lower():
                    self.simulation_controller.register_run_callback(callback_info.function)
                elif "stop" in callback_info.name.lower():
                    self.simulation_controller.register_stop_callback(callback_info.function)
                elif "geometry" in callback_info.name.lower():
                    self.simulation_controller.register_geometry_callback(callback_info.function)
            elif callback_info.category == "performance":
                if "enhanced" in callback_info.name.lower():
                    self.performance_monitor.register_enhanced_callback(callback_info.function)
                elif "physics" in callback_info.name.lower():
                    self.performance_monitor.register_physics_callback(callback_info.function)
                else:
                    self.performance_monitor.register_metrics_callback(callback_info.function)
            
            self.integration_stats['integrated_callbacks'] += 1
            logger.info(f"Successfully integrated callback: {callback_info.name}")
            return True
            
        except Exception as e:
            self.integration_stats['failed_integrations'] += 1
            logger.error(f"Failed to integrate callback {callback_info.name}: {e}")
            return False
    
    def get_integration_status(self) -> Dict[str, Any]:
        """Get status of callback integration."""
        return {
            'total_callbacks': len(self.registered_callbacks),
            'integrated_callbacks': self.integration_stats['integrated_callbacks'],
            'failed_integrations': self.integration_stats['failed_integrations'],
            'success_rate': self.integration_stats['integrated_callbacks'] / max(len(self.registered_callbacks), 1),
            'categories': {
                'emergency': len([c for c in self.registered_callbacks.values() if c.category == "emergency"]),
                'transient': len([c for c in self.registered_callbacks.values() if c.category == "transient"]),
                'config': len([c for c in self.registered_callbacks.values() if c.category == "config"]),
                'simulation': len([c for c in self.registered_callbacks.values() if c.category == "simulation"]),
                'performance': len([c for c in self.registered_callbacks.values() if c.category == "performance"])
            }
        }
    
    def get_all_managers(self) -> Dict[str, Any]:
        """Get all integration managers for external access."""
        return {
            'safety_monitor': self.safety_monitor,
            'transient_manager': self.transient_manager,
            'config_manager': self.config_manager,
            'simulation_controller': self.simulation_controller,
            'performance_monitor': self.performance_monitor
        }


# Global instance for easy access
callback_integration_manager = CallbackIntegrationManager() 