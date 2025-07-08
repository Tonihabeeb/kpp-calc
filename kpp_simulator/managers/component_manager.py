"""
Component Manager for KPP Simulator
Coordinates component lifecycle and system integration
"""

import logging
import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any, Callable
from datetime import datetime, timedelta
import queue

from ..core.physics_engine import PhysicsEngine
from ..electrical.electrical_system import IntegratedElectricalSystem
from ..control_systems.control_system import IntegratedControlSystem
from ..grid_services.grid_services_coordinator import GridServicesCoordinator


class ComponentStatus(Enum):
    """Component status states"""
    INITIALIZING = "initializing"
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    MAINTENANCE = "maintenance"
    SHUTDOWN = "shutdown"


class ComponentType(Enum):
    """Component types"""
    PHYSICS_ENGINE = "physics_engine"
    ELECTRICAL_SYSTEM = "electrical_system"
    CONTROL_SYSTEM = "control_system"
    GRID_SERVICES = "grid_services"
    FLOATER_SYSTEM = "floater_system"
    PNEUMATIC_SYSTEM = "pneumatic_system"
    FLUID_SYSTEM = "fluid_system"
    ENVIRONMENT_SYSTEM = "environment_system"


@dataclass
class ComponentInfo:
    """Component information"""
    component_id: str
    component_type: ComponentType
    status: ComponentStatus
    start_time: datetime
    last_update: datetime
    update_count: int
    error_count: int
    performance_metrics: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ComponentMessage:
    """Inter-component message"""
    timestamp: datetime
    sender: str
    receiver: str
    message_type: str
    data: Any
    priority: int = 0


class ComponentManager:
    """
    Component Manager for KPP Simulator
    
    Features:
    - Component lifecycle management
    - Inter-component communication
    - Performance monitoring and optimization
    - Error handling and recovery
    - System integration coordination
    - Thread safety and synchronization
    """
    
    def __init__(self):
        """Initialize the Component Manager"""
        # Component registry
        self.components: Dict[str, Any] = {}
        self.component_info: Dict[str, ComponentInfo] = {}
        self.component_dependencies: Dict[str, List[str]] = {}
        
        # Communication system
        self.message_queue: queue.Queue = queue.Queue()
        self.message_handlers: Dict[str, List[Callable]] = {}
        self.message_history: List[ComponentMessage] = []
        
        # Manager state
        self.is_active = False
        self.update_interval = 0.01  # seconds
        self.max_message_history = 1000
        
        # Threading
        self.update_thread = None
        self.message_thread = None
        self.thread_lock = threading.Lock()
        
        # Performance tracking
        self.performance_metrics = {
            'total_updates': 0,
            'total_messages': 0,
            'average_update_time': 0.0,
            'component_count': 0,
            'active_components': 0,
            'error_rate': 0.0
        }
        
        # Event callbacks
        self.event_callbacks: Dict[str, List[Callable]] = {
            'component_started': [],
            'component_stopped': [],
            'component_error': [],
            'message_sent': [],
            'message_received': []
        }
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        self.logger.info("Component Manager initialized")
    
    def start(self):
        """Start the component manager"""
        if self.is_active:
            self.logger.warning("Component Manager already active")
            return
        
        self.is_active = True
        
        # Start update thread
        self.update_thread = threading.Thread(target=self._update_loop, daemon=True)
        self.update_thread.start()
        
        # Start message processing thread
        self.message_thread = threading.Thread(target=self._message_loop, daemon=True)
        self.message_thread.start()
        
        self.logger.info("Component Manager started")
    
    def stop(self):
        """Stop the component manager"""
        if not self.is_active:
            return
        
        self.is_active = False
        
        # Wait for threads to finish
        if self.update_thread and self.update_thread.is_alive():
            self.update_thread.join(timeout=5.0)
        
        if self.message_thread and self.message_thread.is_alive():
            self.message_thread.join(timeout=5.0)
        
        # Stop all components
        self._stop_all_components()
        
        self.logger.info("Component Manager stopped")
    
    def register_component(self, component_id: str, component: Any, 
                          component_type: ComponentType, 
                          dependencies: Optional[List[str]] = None) -> bool:
        """
        Register a component with the manager
        
        Args:
            component_id: Unique component identifier
            component: Component instance
            component_type: Type of component
            dependencies: List of component dependencies
            
        Returns:
            True if registration successful
        """
        try:
            with self.thread_lock:
                if component_id in self.components:
                    self.logger.warning(f"Component {component_id} already registered")
                    return False
                
                # Register component
                self.components[component_id] = component
                self.component_dependencies[component_id] = dependencies or []
                
                # Create component info
                component_info = ComponentInfo(
                    component_id=component_id,
                    component_type=component_type,
                    status=ComponentStatus.INITIALIZING,
                    start_time=datetime.now(),
                    last_update=datetime.now(),
                    update_count=0,
                    error_count=0
                )
                self.component_info[component_id] = component_info
                
                # Update performance metrics
                self.performance_metrics['component_count'] = len(self.components)
                
                self.logger.info(f"Component registered: {component_id} ({component_type.value})")
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to register component {component_id}: {e}")
            return False
    
    def unregister_component(self, component_id: str) -> bool:
        """Unregister a component"""
        try:
            with self.thread_lock:
                if component_id not in self.components:
                    self.logger.warning(f"Component {component_id} not found")
                    return False
                
                # Stop component if active
                component = self.components[component_id]
                if hasattr(component, 'stop'):
                    try:
                        component.stop()
                    except Exception as e:
                        self.logger.warning(f"Error stopping component {component_id}: {e}")
                
                # Remove from registry
                del self.components[component_id]
                del self.component_info[component_id]
                del self.component_dependencies[component_id]
                
                # Update performance metrics
                self.performance_metrics['component_count'] = len(self.components)
                
                self.logger.info(f"Component unregistered: {component_id}")
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to unregister component {component_id}: {e}")
            return False
    
    def start_component(self, component_id: str) -> bool:
        """Start a component"""
        try:
            with self.thread_lock:
                if component_id not in self.components:
                    self.logger.error(f"Component {component_id} not found")
                    return False
                
                component = self.components[component_id]
                component_info = self.component_info[component_id]
                
                # Check dependencies
                if not self._check_dependencies(component_id):
                    self.logger.error(f"Component {component_id} dependencies not met")
                    return False
                
                # Start component
                if hasattr(component, 'start'):
                    component.start()
                    component_info.status = ComponentStatus.ACTIVE
                    component_info.last_update = datetime.now()
                    
                    # Trigger event callback
                    self._trigger_event('component_started', component_id)
                    
                    self.logger.info(f"Component started: {component_id}")
                    return True
                else:
                    self.logger.error(f"Component {component_id} has no start method")
                    return False
                
        except Exception as e:
            self.logger.error(f"Failed to start component {component_id}: {e}")
            self._handle_component_error(component_id, e)
            return False
    
    def stop_component(self, component_id: str) -> bool:
        """Stop a component"""
        try:
            with self.thread_lock:
                if component_id not in self.components:
                    self.logger.error(f"Component {component_id} not found")
                    return False
                
                component = self.components[component_id]
                component_info = self.component_info[component_id]
                
                # Stop component
                if hasattr(component, 'stop'):
                    component.stop()
                    component_info.status = ComponentStatus.INACTIVE
                    
                    # Trigger event callback
                    self._trigger_event('component_stopped', component_id)
                    
                    self.logger.info(f"Component stopped: {component_id}")
                    return True
                else:
                    self.logger.error(f"Component {component_id} has no stop method")
                    return False
                
        except Exception as e:
            self.logger.error(f"Failed to stop component {component_id}: {e}")
            return False
    
    def send_message(self, sender: str, receiver: str, message_type: str, 
                    data: Any, priority: int = 0) -> bool:
        """Send a message between components"""
        try:
            message = ComponentMessage(
                timestamp=datetime.now(),
                sender=sender,
                receiver=receiver,
                message_type=message_type,
                data=data,
                priority=priority
            )
            
            # Add to message queue
            self.message_queue.put(message)
            
            # Update performance metrics
            self.performance_metrics['total_messages'] += 1
            
            # Trigger event callback
            self._trigger_event('message_sent', message)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send message: {e}")
            return False
    
    def register_message_handler(self, message_type: str, handler: Callable):
        """Register a message handler"""
        if message_type not in self.message_handlers:
            self.message_handlers[message_type] = []
        
        self.message_handlers[message_type].append(handler)
        self.logger.info(f"Message handler registered for type: {message_type}")
    
    def register_event_callback(self, event_type: str, callback: Callable):
        """Register an event callback"""
        if event_type in self.event_callbacks:
            self.event_callbacks[event_type].append(callback)
            self.logger.info(f"Event callback registered for: {event_type}")
    
    def get_component_status(self, component_id: str) -> Optional[ComponentStatus]:
        """Get component status"""
        if component_id in self.component_info:
            return self.component_info[component_id].status
        return None
    
    def get_component_info(self, component_id: str) -> Optional[ComponentInfo]:
        """Get component information"""
        return self.component_info.get(component_id)
    
    def get_all_components(self) -> Dict[str, ComponentInfo]:
        """Get all component information"""
        return self.component_info.copy()
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics"""
        # Update active component count
        active_count = sum(1 for info in self.component_info.values() 
                          if info.status == ComponentStatus.ACTIVE)
        self.performance_metrics['active_components'] = active_count
        
        return self.performance_metrics.copy()
    
    def get_message_history(self, limit: int = 100) -> List[ComponentMessage]:
        """Get recent message history"""
        return self.message_history[-limit:]
    
    def _update_loop(self):
        """Main update loop for components"""
        while self.is_active:
            try:
                start_time = time.time()
                
                with self.thread_lock:
                    # Update all active components
                    for component_id, component in self.components.items():
                        component_info = self.component_info[component_id]
                        
                        if component_info.status == ComponentStatus.ACTIVE:
                            try:
                                # Update component
                                if hasattr(component, 'update'):
                                    component.update(self.update_interval)
                                
                                # Update component info
                                component_info.last_update = datetime.now()
                                component_info.update_count += 1
                                
                            except Exception as e:
                                self._handle_component_error(component_id, e)
                
                # Update performance metrics
                update_time = time.time() - start_time
                self.performance_metrics['total_updates'] += 1
                
                # Calculate average update time
                if self.performance_metrics['total_updates'] > 0:
                    current_avg = self.performance_metrics['average_update_time']
                    new_avg = (current_avg * (self.performance_metrics['total_updates'] - 1) + update_time) / self.performance_metrics['total_updates']
                    self.performance_metrics['average_update_time'] = new_avg
                
                # Sleep for remaining time
                sleep_time = max(0, self.update_interval - update_time)
                if sleep_time > 0:
                    time.sleep(sleep_time)
                
            except Exception as e:
                self.logger.error(f"Update loop error: {e}")
                time.sleep(self.update_interval)
    
    def _message_loop(self):
        """Message processing loop"""
        while self.is_active:
            try:
                # Get message from queue
                try:
                    message = self.message_queue.get(timeout=1.0)
                except queue.Empty:
                    continue
                
                # Process message
                self._process_message(message)
                
                # Add to history
                self.message_history.append(message)
                if len(self.message_history) > self.max_message_history:
                    self.message_history.pop(0)
                
            except Exception as e:
                self.logger.error(f"Message loop error: {e}")
    
    def _process_message(self, message: ComponentMessage):
        """Process a component message"""
        try:
            # Check if receiver exists
            if message.receiver in self.components:
                component = self.components[message.receiver]
                
                # Call message handler if available
                if hasattr(component, 'handle_message'):
                    component.handle_message(message)
                
                # Call registered message handlers
                if message.message_type in self.message_handlers:
                    for handler in self.message_handlers[message.message_type]:
                        try:
                            handler(message)
                        except Exception as e:
                            self.logger.error(f"Message handler error: {e}")
                
                # Trigger event callback
                self._trigger_event('message_received', message)
                
            else:
                self.logger.warning(f"Message receiver not found: {message.receiver}")
                
        except Exception as e:
            self.logger.error(f"Message processing error: {e}")
    
    def _check_dependencies(self, component_id: str) -> bool:
        """Check if component dependencies are met"""
        dependencies = self.component_dependencies.get(component_id, [])
        
        for dep_id in dependencies:
            if dep_id not in self.components:
                self.logger.error(f"Component {component_id} dependency not found: {dep_id}")
                return False
            
            dep_info = self.component_info[dep_id]
            if dep_info.status != ComponentStatus.ACTIVE:
                self.logger.error(f"Component {component_id} dependency not active: {dep_id}")
                return False
        
        return True
    
    def _handle_component_error(self, component_id: str, error: Exception):
        """Handle component error"""
        try:
            component_info = self.component_info[component_id]
            component_info.status = ComponentStatus.ERROR
            component_info.error_count += 1
            
            # Update error rate
            total_components = len(self.components)
            if total_components > 0:
                error_components = sum(1 for info in self.component_info.values() 
                                     if info.status == ComponentStatus.ERROR)
                self.performance_metrics['error_rate'] = error_components / total_components
            
            # Trigger event callback
            self._trigger_event('component_error', component_id, error)
            
            self.logger.error(f"Component {component_id} error: {error}")
            
        except Exception as e:
            self.logger.error(f"Error handling component error: {e}")
    
    def _trigger_event(self, event_type: str, *args):
        """Trigger an event callback"""
        if event_type in self.event_callbacks:
            for callback in self.event_callbacks[event_type]:
                try:
                    callback(*args)
                except Exception as e:
                    self.logger.error(f"Event callback error: {e}")
    
    def _stop_all_components(self):
        """Stop all components"""
        for component_id in list(self.components.keys()):
            try:
                self.stop_component(component_id)
            except Exception as e:
                self.logger.error(f"Error stopping component {component_id}: {e}")
    
    def clear_message_history(self):
        """Clear message history"""
        self.message_history.clear()
        self.logger.info("Message history cleared")
    
    def reset_performance_metrics(self):
        """Reset performance metrics"""
        self.performance_metrics = {
            'total_updates': 0,
            'total_messages': 0,
            'average_update_time': 0.0,
            'component_count': len(self.components),
            'active_components': 0,
            'error_rate': 0.0
        }
        self.logger.info("Performance metrics reset") 