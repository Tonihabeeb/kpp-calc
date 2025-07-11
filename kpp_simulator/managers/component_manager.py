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

from simulation.physics.physics_engine import PhysicsEngine
from simulation.components.integrated_electrical_system import (
    IntegratedElectricalSystem, ElectricalConfig, ElectricalState
)
from simulation.components.integrated_drivetrain import (
    IntegratedDrivetrain, DrivetrainConfig, DrivetrainSystemState
)
from simulation.components.loss_tracking_system import LossTrackingSystem
from simulation.control.integrated_control_system import IntegratedControlSystem
from simulation.grid_services.grid_services_coordinator import GridServicesCoordinator
from simulation.engine import SimulationEngine


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
    DRIVETRAIN_SYSTEM = "drivetrain_system"
    LOSS_TRACKING = "loss_tracking"
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


@dataclass
class SystemStateSnapshot:
    """System-wide state snapshot"""
    timestamp: datetime
    component_states: Dict[str, Any]
    system_health: Dict[str, bool]
    performance_metrics: Dict[str, Any]
    active_faults: List[Dict[str, Any]]
    warnings: List[Dict[str, Any]]


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
        self.update_interval = 0.02  # seconds (50Hz instead of 100Hz)
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
            'message_received': [],
            'system_fault': []
        }
        
        # Simulation state management
        self._loss_tracking_system = None
        self._physics_engine = None
        self._engine = None
        self._simulation_state = {
            'power': 0,
            'torque': 0,
            'rpm': 0,
            'efficiency': 0,
            'floater_positions': [],
            'h1_active': False,
            'h2_active': False,
            'h3_active': False,
            'status': 'stopped',  # Add missing status key
            'step_count': 0,
            'step_time': 0.0,
            'simulation_speed': 1.0,
            'start_time': None,
            'duration': 0,
            'component_states': {
                'electrical_system': {
                    'voltage': 0.0,
                    'current': 0.0,
                    'power_factor': 0.95
                },
                'mechanical_system': {
                    'chain_speed': 0.0,
                    'clutch_engaged': False,
                    'bearing_temp': 25.0
                },
                'pneumatic_system': {
                    'main_valve_open': False,
                    'bypass_valve_open': False,
                    'compressor_active': False,
                    'pressure': 0.0,
                    'temperature': 25.0
                }
            }
        }
        
        # Simulation parameters
        self.simulation_params = {
            'floater_count': 60,
            'floater_mass': 10.0,
            'chain_tension': 500.0,
            'water_level': 5.0,
            'h1_intensity': 0.0,
            'h2_intensity': 0.0,
            'h3_intensity': 0.0
        }
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        
        # Operation history for tracking system operations
        self.operation_history = []
        
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
    
    def initialize_drivetrain_system(self, config: Optional[DrivetrainConfig] = None) -> bool:
        """
        Initialize and register the drivetrain system.
        
        Args:
            config: Optional drivetrain configuration
            
        Returns:
            True if initialization successful
        """
        try:
            # Create drivetrain system
            drivetrain = IntegratedDrivetrain(config)
            
            # Register with component manager
            success = self.register_component(
                component_id="drivetrain_system",
                component=drivetrain,
                component_type=ComponentType.DRIVETRAIN_SYSTEM,
                dependencies=["physics_engine"]  # Drivetrain depends on physics engine
            )
            
            if success:
                self.logger.info("Drivetrain system initialized and registered")
                return True
            else:
                self.logger.error("Failed to register drivetrain system")
                return False
                
        except Exception as e:
            self.logger.error("Error initializing drivetrain system: %s", e)
            return False

    def initialize_electrical_system(self, config: Optional[ElectricalConfig] = None) -> bool:
        """
        Initialize and register the electrical system.
        
        Args:
            config: Optional electrical configuration
            
        Returns:
            True if initialization successful
        """
        try:
            # Create electrical system
            electrical = IntegratedElectricalSystem(config)
            
            # Register with component manager
            success = self.register_component(
                component_id="electrical_system",
                component=electrical,
                component_type=ComponentType.ELECTRICAL_SYSTEM,
                dependencies=["physics_engine"]  # Electrical system depends on physics engine
            )
            
            if success:
                self.logger.info("Electrical system initialized and registered")
                return True
            else:
                self.logger.error("Failed to register electrical system")
                return False
                
        except Exception as e:
            self.logger.error("Error initializing electrical system: %s", e)
            return False

    def get_drivetrain_system(self) -> Optional[IntegratedDrivetrain]:
        """
        Get the drivetrain system component.
        
        Returns:
            Drivetrain system instance if registered, None otherwise
        """
        return self.components.get("drivetrain_system")

    def get_electrical_system(self) -> Optional[IntegratedElectricalSystem]:
        """
        Get the electrical system component.
        
        Returns:
            Electrical system instance if registered, None otherwise
        """
        return self.components.get("electrical_system")
    
    def synchronize_power_systems(self) -> bool:
        """
        Synchronize electrical and drivetrain systems.
        Ensures proper power transfer and state coordination.
        
        Returns:
            True if synchronization successful
        """
        try:
            # Get system components
            drivetrain = self.get_drivetrain_system()
            electrical = self.components.get("electrical_system")
            
            if not drivetrain or not electrical:
                self.logger.error("Cannot synchronize: missing required systems")
                return False
            
            # Get current states
            drivetrain_state = drivetrain.get_drivetrain_state()
            electrical_state = electrical.get_electrical_state()
            
            # Check system states for compatibility
            if (drivetrain.get_system_state() == DrivetrainSystemState.OPERATING and 
                electrical.get_system_state() == ElectricalState.GENERATING):
                
                # Update electrical system based on drivetrain output
                success = electrical.update_power_output(
                    mechanical_power=drivetrain_state.output_power,
                    speed=drivetrain_state.output_speed
                )
                
                if success:
                    # Record synchronization metrics
                    self._record_operation('power_systems_sync', {
                        'mechanical_power': drivetrain_state.output_power,
                        'electrical_power': electrical_state.power_output,
                        'drivetrain_efficiency': drivetrain_state.efficiency,
                        'electrical_efficiency': electrical_state.efficiency,
                        'total_efficiency': (drivetrain_state.efficiency * 
                                          electrical_state.efficiency)
                    })
                    
                    self.logger.info("Power systems synchronized successfully")
                    return True
                else:
                    self.logger.error("Failed to update electrical system")
                    return False
            else:
                self.logger.warning("Systems not in compatible states for synchronization")
                return False
                
        except Exception as e:
            self.logger.error("Error synchronizing power systems: %s", e)
            return False

    def coordinate_system_startup(self) -> bool:
        """
        Coordinate startup sequence between drivetrain and electrical systems.
        
        Returns:
            True if startup sequence successful
        """
        try:
            # Get system components
            drivetrain = self.get_drivetrain_system()
            electrical = self.components.get("electrical_system")
            
            if not drivetrain or not electrical:
                self.logger.error("Cannot start: missing required systems")
                return False
            
            # Start drivetrain first
            if drivetrain.get_system_state() == DrivetrainSystemState.IDLE:
                success = drivetrain.start_drivetrain(
                    input_speed=drivetrain.config.rated_speed * 0.1,  # Start at 10% speed
                    input_torque=drivetrain.config.rated_torque * 0.1  # Start at 10% torque
                )
                
                if not success:
                    self.logger.error("Failed to start drivetrain")
                    return False
            
            # Wait for drivetrain to reach operating state
            if drivetrain.get_system_state() == DrivetrainSystemState.OPERATING:
                # Get current drivetrain state
                drivetrain_state = drivetrain.get_drivetrain_state()
                
                # Start electrical system with drivetrain output
                success = electrical.start_generation(
                    mechanical_power=drivetrain_state.output_power,
                    speed=drivetrain_state.output_speed
                )
                
                if success:
                    self.logger.info("System startup sequence completed successfully")
                    return True
                else:
                    self.logger.error("Failed to start electrical system")
                    drivetrain.stop_drivetrain()  # Stop drivetrain if electrical fails
                    return False
            else:
                self.logger.warning("Drivetrain not in operating state")
                return False
                
        except Exception as e:
            self.logger.error("Error in system startup sequence: %s", e)
            return False

    def coordinate_system_shutdown(self) -> bool:
        """
        Coordinate shutdown sequence between electrical and drivetrain systems.
        
        Returns:
            True if shutdown sequence successful
        """
        try:
            # Get system components
            drivetrain = self.get_drivetrain_system()
            electrical = self.components.get("electrical_system")
            
            if not drivetrain or not electrical:
                self.logger.error("Cannot shutdown: missing required systems")
                return False
            
            # Stop electrical system first
            if electrical.get_system_state() in [ElectricalState.GENERATING, ElectricalState.GRID_CONNECTED]:
                success = electrical.stop_generation()
                if not success:
                    self.logger.error("Failed to stop electrical system")
                    return False
            
            # Stop drivetrain after electrical system
            if drivetrain.get_system_state() == DrivetrainSystemState.OPERATING:
                success = drivetrain.stop_drivetrain()
                if not success:
                    self.logger.error("Failed to stop drivetrain")
                    return False
            
            self.logger.info("System shutdown sequence completed successfully")
            return True
                
        except Exception as e:
            self.logger.error("Error in system shutdown sequence: %s", e)
            return False
    
    def initialize_loss_tracking(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """
        Initialize and register the loss tracking system.
        
        Args:
            config: Optional configuration dictionary
            
        Returns:
            True if initialization successful
        """
        try:
            # Create loss tracking system
            loss_tracking = LossTrackingSystem(config)
            
            # Register with component manager
            success = self.register_component(
                component_id="loss_tracking",
                component=loss_tracking,
                component_type=ComponentType.LOSS_TRACKING,
                dependencies=["drivetrain_system", "electrical_system"]
            )
            
            if success:
                self.logger.info("Loss tracking system initialized and registered")
                return True
            else:
                self.logger.error("Failed to register loss tracking system")
                return False
                
        except Exception as e:
            self.logger.error("Error initializing loss tracking system: %s", e)
            return False

    def get_loss_tracking_system(self) -> Optional[LossTrackingSystem]:
        """
        Get the loss tracking system component.
        
        Returns:
            Loss tracking system instance if registered, None otherwise
        """
        return self.components.get("loss_tracking")

    def update_system_losses(self) -> bool:
        """
        Update system-wide loss tracking.
        
        Returns:
            True if update successful
        """
        try:
            # Get required components
            loss_tracking = self.get_loss_tracking_system()
            drivetrain = self.get_drivetrain_system()
            electrical = self.components.get("electrical_system")
            
            if not all([loss_tracking, drivetrain, electrical]):
                self.logger.error("Cannot update losses: missing required components")
                return False
            
            try:
                # Get current states
                drivetrain_state = drivetrain.get_drivetrain_state() if drivetrain else None
                electrical_state = electrical.get_electrical_state() if electrical else None
                
                if not drivetrain_state or not electrical_state:
                    self.logger.error("Cannot update losses: invalid component states")
                    return False
                
                # Update loss tracking
                if loss_tracking is not None:
                    system_losses = loss_tracking.update(
                        drivetrain_state=drivetrain_state,
                        electrical_state=electrical_state
                    )
                    
                    # Get current state for recording
                    current_state = loss_tracking.get_current_state()
                    if current_state:
                        # Record operation with loss metrics
                        self._record_operation('system_losses_update', {
                            'timestamp': datetime.now(),
                            'total_losses': current_state.system_losses.total_losses,
                            'mechanical_losses': current_state.system_losses.mechanical_losses,
                            'electrical_losses': current_state.system_losses.electrical_losses,
                            'thermal_losses': current_state.system_losses.thermal_losses,
                            'overall_efficiency': current_state.system_losses.overall_efficiency
                        })
                    
                    # Check for optimization suggestions
                    suggestions = loss_tracking.get_optimization_suggestions()
                    if suggestions:
                        self.logger.info("Loss optimization suggestions available: %d", len(suggestions))
                else:
                    self.logger.warning("Loss tracking system not available")
                    return False
                
                return True
            
            except AttributeError as e:
                self.logger.error("Component method not found: %s", e)
                return False
            
        except Exception as e:
            self.logger.error("Error updating system losses: %s", e)
            return False

    def _process_pending_messages(self) -> None:
        """Process pending messages in the message queue"""
        try:
            while not self.message_queue.empty():
                try:
                    message = self.message_queue.get_nowait()
                    self._process_message(message)
                except queue.Empty:
                    break
                    
        except Exception as e:
            self.logger.error("Error processing pending messages: %s", e)

    def _update_loop(self):
        """Main update loop for component management"""
        last_update = time.time()
        
        while self.is_active:
            try:
                start_time = time.time()
                
                # Get current state
                current_time = time.time()
                time_step = current_time - last_update
                last_update = current_time
                current_state = self.get_simulation_state()
                
                # Update all components
                with self.thread_lock:
                    for component_id, component in self.components.items():
                        try:
                            if hasattr(component, 'update'):
                                if component_id == 'physics_engine':
                                    component.update(current_state, time_step)
                                elif component_id == 'electrical_system':
                                    component.update(current_state, time_step)
                                elif component_id == 'simulation_engine':
                                    component.step()
                                elif component_id == 'loss_tracking':
                                    # Get required states from simulation state
                                    if current_state and isinstance(current_state, dict) and 'component_states' in current_state:
                                        drivetrain_state = current_state['component_states'].get('drivetrain_system')
                                        electrical_state = current_state['component_states'].get('electrical_system')
                                        if drivetrain_state and electrical_state:
                                            component.update(drivetrain_state, electrical_state)
                                elif component_id == 'drivetrain_system':
                                    # Handle drivetrain system update with proper state
                                    if hasattr(component, 'update_drivetrain'):
                                        component.update_drivetrain(current_state, time_step)
                                    else:
                                        # Skip update if method doesn't exist
                                        continue
                                else:
                                    component.update(current_state)
                        except Exception as e:
                            self.logger.error(f"Error updating component {component_id}: {e}")
                            self._handle_component_error(component_id, e)
                
                # Check if simulation is running and update it
                if self._simulation_state.get('status') == 'running':
                    # Check duration limit
                    if self._simulation_state.get('duration', 0) > 0:
                        start_time_sim = self._simulation_state.get('start_time')
                        if start_time_sim is not None:
                            elapsed = datetime.now() - start_time_sim
                            if elapsed.total_seconds() >= self._simulation_state.get('duration'):
                                self._simulation_state['status'] = 'paused'
                    
                    # Update simulation if still running
                    if self._simulation_state.get('status') == 'running':
                        with self.thread_lock:
                            self._update_simulation(time_step)
                            self._simulation_state['step_count'] = self._simulation_state.get('step_count', 0) + 1
                
                # Process messages
                self._process_pending_messages()
                
                # Update performance metrics
                self.performance_metrics['total_updates'] += 1
                
                # Sleep to maintain update rate
                elapsed_time = time.time() - start_time
                sleep_time = max(0, self.update_interval - elapsed_time)
                
                if sleep_time > 0:
                    time.sleep(sleep_time)
                    
            except Exception as e:
                self.logger.error(f"Error in update loop: {e}")
                time.sleep(1.0)  # Wait longer on error
        
    def _message_loop(self):
        """Message processing loop"""
        
        while self.is_active:
            try:
                # Get message with timeout
                try:
                    message = self.message_queue.get(timeout=1.0)
                    self._process_message(message)
                except queue.Empty:
                    continue
                    
            except Exception as e:
                self.logger.error(f"Error in message loop: {e}")
                time.sleep(1.0)  # Wait longer on error
        
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

    def _record_operation(self, operation_type: str, data: Dict[str, Any]) -> None:
        """
        Record an operation in the component manager's history.
        
        Args:
            operation_type: Type of operation
            data: Operation data
        """
        try:
            operation = {
                'timestamp': datetime.now(),
                'operation_type': operation_type,
                'data': data
            }
            
            # Assuming operation_history is defined elsewhere or will be added
            # For now, we'll just log the error if it's not defined
            if not hasattr(self, 'operation_history'):
                self.logger.warning("operation_history not defined, cannot record operation.")
                return

            self.operation_history.append(operation)
            
            # Trim history if too long
            if len(self.operation_history) > self.max_message_history:
                self.operation_history = self.operation_history[-self.max_message_history:]
                
        except Exception as e:
            self.logger.error("Error recording operation: %s", e) 

    def monitor_system_state(self) -> SystemStateSnapshot:
        """
        Get a comprehensive snapshot of the entire system state.
        Includes component states, health checks, and performance metrics.
        
        Returns:
            SystemStateSnapshot containing current system state
        """
        try:
            # Get components
            drivetrain = self.get_drivetrain_system()
            electrical = self.components.get("electrical_system")
            
            # Initialize state containers
            component_states = {}
            system_health = {}
            performance_metrics = {}
            active_faults = []
            warnings = []
            
            # Check drivetrain state
            if drivetrain:
                component_states['drivetrain'] = {
                    'state': drivetrain.get_system_state(),
                    'detailed_state': drivetrain.get_drivetrain_state(),
                    'efficiency': drivetrain.get_efficiency(),
                    'chain_tension': drivetrain.get_chain_tension()
                }
                performance_metrics['drivetrain'] = drivetrain.get_performance_metrics()
                
                # Check drivetrain health
                system_health['drivetrain_ok'] = (
                    drivetrain.get_system_state() != DrivetrainSystemState.FAULT and
                    drivetrain.get_chain_tension() <= drivetrain.config.max_chain_tension
                )
            
            # Check electrical system state
            if electrical:
                component_states['electrical'] = {
                    'state': electrical.get_system_state(),
                    'detailed_state': electrical.get_electrical_state(),
                    'efficiency': electrical.get_efficiency() if hasattr(electrical, 'get_efficiency') else None
                }
                performance_metrics['electrical'] = electrical.get_performance_metrics()
                
                # Check electrical health
                system_health['electrical_ok'] = (
                    electrical.get_system_state() != ElectricalState.FAULT
                )
            
            # Check for faults and warnings
            for component_id, component in self.components.items():
                if hasattr(component, 'get_system_state'):
                    if getattr(component, 'get_system_state')() in ['FAULT', 'fault']:
                        active_faults.append({
                            'component': component_id,
                            'timestamp': datetime.now(),
                            'state': getattr(component, 'get_system_state')()
                        })
                
                # Check component-specific warnings
                if component_id == 'drivetrain_system' and drivetrain:
                    if drivetrain.get_chain_tension() > drivetrain.config.max_chain_tension * 0.8:
                        warnings.append({
                            'component': 'drivetrain',
                            'type': 'high_chain_tension',
                            'value': drivetrain.get_chain_tension(),
                            'threshold': drivetrain.config.max_chain_tension * 0.8,
                            'timestamp': datetime.now()
                        })
                
                elif component_id == 'electrical_system' and electrical:
                    electrical_state = electrical.get_electrical_state()
                    if electrical_state.temperature > electrical.config.max_temperature * 0.9:
                        warnings.append({
                            'component': 'electrical',
                            'type': 'high_temperature',
                            'value': electrical_state.temperature,
                            'threshold': electrical.config.max_temperature * 0.9,
                            'timestamp': datetime.now()
                        })
            
            return SystemStateSnapshot(
                timestamp=datetime.now(),
                component_states=component_states,
                system_health=system_health,
                performance_metrics=performance_metrics,
                active_faults=active_faults,
                warnings=warnings
            )
            
        except Exception as e:
            self.logger.error("Error monitoring system state: %s", e)
            return SystemStateSnapshot(
                timestamp=datetime.now(),
                component_states={},
                system_health={'system_error': False},
                performance_metrics={},
                active_faults=[{
                    'component': 'component_manager',
                    'type': 'monitoring_error',
                    'message': str(e),
                    'timestamp': datetime.now()
                }],
                warnings=[]
            )

    def handle_system_fault(self, fault_data: Dict[str, Any]) -> bool:
        """
        Handle a system-wide fault condition.
        Implements graceful shutdown and recovery procedures.
        
        Args:
            fault_data: Information about the fault
            
        Returns:
            True if fault handled successfully
        """
        try:
            self.logger.warning("Handling system fault: %s", fault_data)
            
            # Record fault
            self._record_operation('system_fault', fault_data)
            
            # Stop electrical system first
            electrical = self.components.get("electrical_system")
            if electrical:
                if electrical.get_system_state() in [ElectricalState.GENERATING, ElectricalState.GRID_CONNECTED]:
                    electrical.stop_generation()
            
            # Stop drivetrain
            drivetrain = self.get_drivetrain_system()
            if drivetrain:
                if drivetrain.get_system_state() == DrivetrainSystemState.OPERATING:
                    drivetrain.stop_drivetrain()
            
            # Stop all other components
            self._stop_all_components()
            
            # Trigger fault event callbacks
            self._trigger_event('system_fault', fault_data)
            
            self.logger.info("System fault handled successfully")
            return True
            
        except Exception as e:
            self.logger.error("Error handling system fault: %s", e)
            return False

    def check_system_health(self) -> Dict[str, Any]:
        """
        Perform a comprehensive system health check.
        
        Returns:
            Dictionary containing health check results
        """
        try:
            health_check = {
                'timestamp': datetime.now(),
                'overall_status': 'healthy',
                'components': {},
                'warnings': [],
                'recommendations': []
            }
            
            # Check each component
            for component_id, component in self.components.items():
                component_health = {'status': 'unknown'}
                
                if hasattr(component, 'get_system_state'):
                    state = getattr(component, 'get_system_state')()
                    component_health['status'] = 'healthy' if state not in ['FAULT', 'fault'] else 'fault'
                    component_health['state'] = state
                
                if hasattr(component, 'get_performance_metrics'):
                    metrics = getattr(component, 'get_performance_metrics')()
                    component_health['metrics'] = metrics
                    
                    # Check for performance issues
                    if 'efficiency' in metrics and metrics['efficiency'] < 0.8:
                        health_check['warnings'].append({
                            'component': component_id,
                            'type': 'low_efficiency',
                            'value': metrics['efficiency'],
                            'threshold': 0.8
                        })
                        health_check['recommendations'].append(
                            f"Check {component_id} for efficiency issues"
                        )
                
                health_check['components'][component_id] = component_health
                
                # Update overall status
                if component_health['status'] == 'fault':
                    health_check['overall_status'] = 'fault'
                elif component_health['status'] == 'warning' and health_check['overall_status'] == 'healthy':
                    health_check['overall_status'] = 'warning'
            
            return health_check
            
        except Exception as e:
            self.logger.error("Error checking system health: %s", e)
            return {
                'timestamp': datetime.now(),
                'overall_status': 'error',
                'error': str(e)
            } 

    def initialize_simulation(self):
        """Initialize simulation components"""
        try:
            # Create physics configuration
            from simulation.physics import PhysicsConfig
            physics_config = PhysicsConfig(
                time_step=0.01,
                tank_height=10.0,
                enable_h1=False,
                enable_h2=False,
                enable_h3=False,
                nanobubble_fraction=0.2,
                thermal_expansion_coeff=0.001,
                flywheel_inertia=10.0,
                mechanical_efficiency=0.95,
                electrical_efficiency=0.92
            )
            
            # Initialize physics engine with configuration
            self._physics_engine = PhysicsEngine(physics_config)
            
            # Initialize simulation engine
            self._engine = SimulationEngine()
            
            # Register components
            self.register_component(
                component_id="physics_engine",
                component=self._physics_engine,
                component_type=ComponentType.PHYSICS_ENGINE
            )
            
            self.register_component(
                component_id="simulation_engine",
                component=self._engine,
                component_type=ComponentType.CONTROL_SYSTEM
            )
            
            # Start simulation engine
            self._engine.start()
            
            # Start component manager if not already running
            if not self.is_active:
                self.start()
            
            self.logger.info("Simulation components initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error initializing simulation: {e}")
            return False 

    def get_simulation_state(self) -> Dict[str, Any]:
        """Get current simulation state"""
        if self._engine and hasattr(self._engine, 'get_state'):
            state = self._engine.get_state()
            # Update state from engine
            self._simulation_state.update({
                'power': getattr(state, 'total_power', 0),
                'torque': getattr(state, 'torque', 0),
                'rpm': getattr(state, 'rpm', 0),
                'efficiency': getattr(state, 'efficiency', 0),
                'floater_positions': getattr(state, 'floater_positions', [])
            })
        
        # Ensure component_states exists and is properly structured
        if 'component_states' not in self._simulation_state:
            self._simulation_state['component_states'] = {
                'electrical_system': {
                    'voltage': 0.0,
                    'current': 0.0,
                    'power_factor': 0.95
                },
                'mechanical_system': {
                    'chain_speed': 0.0,
                    'clutch_engaged': False,
                    'bearing_temp': 25.0
                },
                'pneumatic_system': {
                    'main_valve_open': False,
                    'bypass_valve_open': False,
                    'compressor_active': False,
                    'pressure': 0.0,
                    'temperature': 25.0
                }
            }
        
        return self._simulation_state 

    def update_floater_count(self, value: int) -> None:
        """Update floater count"""
        with self.thread_lock:
            self.simulation_params['floater_count'] = value
            if self._engine and hasattr(self._engine, 'set_parameters'):
                self._engine.set_parameters({'floater_count': value})
    
    def update_floater_mass(self, value: float) -> None:
        """Update floater mass"""
        with self.thread_lock:
            self.simulation_params['floater_mass'] = value
            if self._engine and hasattr(self._engine, 'set_parameters'):
                self._engine.set_parameters({'floater_mass': value})
    
    def update_chain_tension(self, value: float) -> None:
        """Update chain tension"""
        with self.thread_lock:
            self.simulation_params['chain_tension'] = value
            if self._engine and hasattr(self._engine, 'set_parameters'):
                self._engine.set_parameters({'chain_tension': value})
    
    def update_water_level(self, value: float) -> None:
        """Update water level"""
        with self.thread_lock:
            self.simulation_params['water_level'] = value
            if self._engine and hasattr(self._engine, 'set_parameters'):
                self._engine.set_parameters({'water_level': value})
    
    def update_h1_intensity(self, value: float) -> None:
        """Update H1 intensity"""
        with self.thread_lock:
            self.simulation_params['h1_intensity'] = value
            if self._engine:
                # Convert intensity (0-1) to enable flag and nanobubble fraction
                enable_h1 = value > 0.0
                nanobubble_fraction = value * 0.3  # Scale to 0-0.3 range
                self._engine.set_parameters({
                    'enable_h1': enable_h1,
                    'nanobubble_fraction': nanobubble_fraction
                })
    
    def update_h2_intensity(self, value: float) -> None:
        """Update H2 intensity"""
        with self.thread_lock:
            self.simulation_params['h2_intensity'] = value
            if self._engine:
                # Convert intensity (0-1) to enable flag and thermal expansion coefficient
                enable_h2 = value > 0.0
                thermal_expansion_coeff = value * 0.002  # Scale to 0-0.002 range
                self._engine.set_parameters({
                    'enable_h2': enable_h2,
                    'thermal_expansion_coeff': thermal_expansion_coeff
                })
    
    def update_h3_intensity(self, value: float) -> None:
        """Update H3 intensity"""
        with self.thread_lock:
            self.simulation_params['h3_intensity'] = value
            if self._engine:
                # Convert intensity (0-1) to enable flag and flywheel inertia
                enable_h3 = value > 0.0
                flywheel_inertia = 5.0 + value * 15.0  # Scale to 5-20 kg·m² range
                self._engine.set_parameters({
                    'enable_h3': enable_h3,
                    'flywheel_inertia': flywheel_inertia
                })
    
    def get_simulation_parameters(self) -> Dict[str, Any]:
        """Get current simulation parameters"""
        return self.simulation_params.copy() 

    def start_compressor(self) -> bool:
        """Start the compressor"""
        try:
            with self.thread_lock:
                # Ensure pneumatic system state exists
                if 'pneumatic_system' not in self._simulation_state:
                    self._simulation_state['pneumatic_system'] = {}
                
                # Get pneumatic system state
                pneumatic_state = self._simulation_state['pneumatic_system']
                
                # Check if compressor is already active
                if pneumatic_state.get('compressor_active', False):
                    self.logger.warning("Compressor already active")
                    return False
                
                # Start compressor
                pneumatic_state['compressor_active'] = True
                pneumatic_state['pressure'] = 1.0  # Initial pressure
                pneumatic_state['temperature'] = 25.0  # Initial temperature
                
                # Also update the component_states structure
                if 'component_states' not in self._simulation_state:
                    self._simulation_state['component_states'] = {}
                if 'pneumatic_system' not in self._simulation_state['component_states']:
                    self._simulation_state['component_states']['pneumatic_system'] = {}
                
                self._simulation_state['component_states']['pneumatic_system']['compressor_active'] = True
                self._simulation_state['component_states']['pneumatic_system']['pressure'] = 1.0
                self._simulation_state['component_states']['pneumatic_system']['temperature'] = 25.0
                
                # Log operation
                self._record_operation('compressor_start', {
                    'timestamp': datetime.now().isoformat(),
                    'success': True
                })
                
                self.logger.info("Compressor started successfully")
                return True
                
        except Exception as e:
            self.logger.error(f"Error starting compressor: {e}")
            return False

    def stop_compressor(self) -> bool:
        """Stop the compressor"""
        try:
            with self.thread_lock:
                # Get pneumatic system state
                pneumatic_state = self._simulation_state.get('pneumatic_system', {})
                if pneumatic_state.get('compressor_active', False):
                    # Update state
                    self._simulation_state['pneumatic_system']['compressor_active'] = False
                    self._simulation_state['pneumatic_system']['pressure'] = 0.0
                    
                    # Log operation
                    self._record_operation('compressor_stop', {
                        'timestamp': datetime.now().isoformat(),
                        'success': True
                    })
                    
                    self.logger.info("Compressor stopped successfully")
                    return True
                    
                self.logger.warning("Compressor already inactive")
                return False
                
        except Exception as e:
            self.logger.error(f"Error stopping compressor: {e}")
            return False

    def update_simulation_state(self, new_state: Dict[str, Any]) -> None:
        """Update simulation state with new values"""
        try:
            with self.thread_lock:
                # Update main simulation metrics
                self._simulation_state.update(new_state)
                
                # Update pneumatic system pressure if compressor is active
                pneumatic_state = self._simulation_state.get('pneumatic_system', {})
                if pneumatic_state.get('compressor_active', False):
                    current_pressure = pneumatic_state.get('pressure', 0.0)
                    if current_pressure < 8.0:  # Max pressure 8 bar
                        self._simulation_state['pneumatic_system']['pressure'] = min(
                            current_pressure + 0.1,  # Pressure increase rate
                            8.0  # Maximum pressure
                        )
                
                # Log state update
                self._record_operation('state_update', {
                    'timestamp': datetime.now().isoformat(),
                    'metrics_updated': list(new_state.keys())
                })
                
        except Exception as e:
            self.logger.error(f"Error updating simulation state: {e}")



    def start_simulation(self, duration: int = 0, speed: float = 1.0) -> bool:
        """Start the simulation"""
        try:
            with self.thread_lock:
                if self._simulation_state.get('status') == 'running':
                    return False
                
                # Update simulation parameters
                self._simulation_state['simulation_speed'] = max(0.1, min(5.0, speed))
                self._simulation_state['duration'] = max(0, duration)
                self._simulation_state['start_time'] = datetime.now()
                self._simulation_state['status'] = 'running'
                self._simulation_state['step_count'] = 0
                self._simulation_state['step_time'] = 0.0
                
                # Don't start a new thread - let the existing _update_loop handle simulation
                # The _update_loop already runs continuously and will pick up the 'running' status
                
                self.logger.info("Simulation started")
                return True
                
        except Exception as e:
            self.logger.error(f"Error starting simulation: {e}")
            return False
    
    def pause_simulation(self) -> bool:
        """Pause the simulation"""
        try:
            with self.thread_lock:
                if self._simulation_state.get('status') == 'running':
                    self._simulation_state['status'] = 'paused'
                    # Explicitly stop drivetrain if present
                    drivetrain = self.get_drivetrain_system()
                    if drivetrain is not None:
                        drivetrain.stop_drivetrain()
                    self.logger.info("Simulation paused")
                    return True
                else:
                    self.logger.info("Simulation not running, cannot pause")
                    return False
        except Exception as e:
            self.logger.error(f"Error pausing simulation: {e}")
            return False
    
    def reset_simulation(self) -> bool:
        """Reset the simulation"""
        try:
            with self.thread_lock:
                # Stop current simulation if running
                if self._simulation_state.get('status') == 'running':
                    self.pause_simulation()
                # Explicitly stop and reset drivetrain if present
                drivetrain = self.get_drivetrain_system()
                if drivetrain is not None:
                    drivetrain.stop_drivetrain()
                    if hasattr(drivetrain, 'reset'):
                        drivetrain.reset()
                # Reset state
                self._simulation_state = {
                    'power': 0,
                    'torque': 0,
                    'rpm': 0,
                    'efficiency': 0,
                    'mechanical_efficiency': 0,
                    'electrical_efficiency': 0,
                    'step_count': 0,
                    'step_time': 0.0,
                    'simulation_speed': 1.0,
                    'status': 'stopped',
                    'start_time': None,
                    'duration': 0,
                    'floater_positions': [],
                    'h1_active': False,
                    'h2_active': False,
                    'h3_active': False,
                    'component_states': {
                        'electrical_system': {
                            'voltage': 0.0,
                            'current': 0.0,
                            'power_factor': 0.95
                        },
                        'mechanical_system': {
                            'chain_speed': 0.0,
                            'clutch_engaged': False,
                            'bearing_temp': 25.0
                        },
                        'pneumatic_system': {
                            'main_valve_open': False,
                            'bypass_valve_open': False,
                            'compressor_active': False,
                            'pressure': 0.0,
                            'temperature': 25.0
                        }
                    }
                }
                self.logger.info("Simulation reset")
                return True
        except Exception as e:
            self.logger.error(f"Error resetting simulation: {e}")
            return False
    
    def set_simulation_speed(self, speed: float) -> bool:
        """Set simulation speed"""
        try:
            with self.thread_lock:
                # Clamp speed between 0.1x and 5.0x
                self._simulation_state['simulation_speed'] = max(0.1, min(5.0, speed))
                self.logger.info(f"Simulation speed set to {speed}x")
                return True
                
        except Exception as e:
            self.logger.error(f"Error setting simulation speed: {e}")
            return False
    
    def _simulation_loop(self):
        """Main simulation loop - optimized for performance with detailed monitoring"""
        try:
            last_update = time.time()
            target_interval = 0.05  # Reduced to 20Hz for better performance (was 50Hz)
            performance_warnings = 0
            
            # Initialize performance monitoring
            from simulation.monitoring.performance_monitor import get_performance_monitor
            performance_monitor = get_performance_monitor()
            
            while self.is_active and self._simulation_state.get('status') == 'running':
                current_time = time.time()
                dt = (current_time - last_update) * self._simulation_state.get('simulation_speed', 1.0)
                
                # Update simulation with detailed timing
                start_step = time.time()
                component_times = {}
                
                with self.thread_lock:
                    # Check duration limit
                    if self._simulation_state.get('duration', 0) > 0:
                        start_time = self._simulation_state.get('start_time')
                        if start_time is not None:
                            elapsed = datetime.now() - start_time
                            if elapsed.total_seconds() >= self._simulation_state.get('duration'):
                                self._simulation_state['status'] = 'paused'
                                break
                    
                    # Update simulation state with component timing
                    start_update = time.time()
                    self._update_simulation(dt)
                    component_times['simulation_update'] = time.time() - start_update
                    
                    self._simulation_state['step_count'] = self._simulation_state.get('step_count', 0) + 1
                
                # Calculate step time and update performance metrics
                step_time = time.time() - start_step
                self._simulation_state['step_time'] = step_time * 1000  # Convert to ms
                
                # Record detailed performance metrics
                try:
                    performance_metrics = performance_monitor.record_step_performance(
                        step_duration=step_time,
                        component_times=component_times
                    )
                    
                    # Update simulation state with performance data
                    self._simulation_state['performance_metrics'] = {
                        'step_duration_ms': step_time * 1000,
                        'memory_usage_mb': performance_metrics.memory_usage,
                        'cpu_usage_percent': performance_metrics.cpu_usage,
                        'bottleneck_components': performance_metrics.bottleneck_components
                    }
                    
                except Exception as e:
                    self.logger.error(f"Error recording performance metrics: {e}")
                
                # Performance monitoring with enhanced logging and adaptive thresholds
                if step_time > target_interval:
                    performance_warnings += 1
                    if performance_warnings <= 3:  # Only log first few warnings
                        self.logger.warning(f"Simulation step taking longer than target ({step_time:.3f}s > {target_interval:.3f}s)")
                        
                        # Get performance summary for debugging
                        try:
                            summary = performance_monitor.get_performance_summary()
                            if summary.get('status') == 'active':
                                bottlenecks = summary.get('top_bottlenecks', [])
                                if bottlenecks:
                                    self.logger.info(f"Top bottlenecks: {bottlenecks[:3]}")
                        except Exception as e:
                            self.logger.error(f"Error getting performance summary: {e}")
                else:
                    performance_warnings = 0  # Reset counter on good performance
                
                # Adaptive sleep to maintain target frequency
                elapsed_since_update = time.time() - current_time
                sleep_time = max(0, target_interval - elapsed_since_update)
                
                if sleep_time > 0:
                    time.sleep(sleep_time)
                
                last_update = current_time
                
        except Exception as e:
            self.logger.error(f"Error in simulation loop: {e}")
            self._simulation_state['status'] = 'error'
    
    def _update_simulation(self, dt: float):
        """Update simulation state - optimized for performance"""
        try:
            # Cache frequently accessed values to reduce dictionary lookups
            rpm = self._simulation_state.get('rpm', 0)
            mech_state = self._simulation_state['component_states']['mechanical_system']
            elec_state = self._simulation_state['component_states']['electrical_system']
            pneumatic_state = self._simulation_state['component_states']['pneumatic_system']
            
            # Update mechanical system with optimized calculations
            if mech_state['clutch_engaged']:
                rpm += dt * 10  # Simple RPM ramp
                torque = 100 + rpm * 0.1  # Simple torque model
                chain_speed = rpm * 0.1047  # RPM to m/s conversion
            else:
                rpm = max(0, rpm - dt * 20)  # RPM decay
                torque = max(0, self._simulation_state.get('torque', 0) - dt * 50)
                chain_speed = rpm * 0.1047
            
            # Update state with cached values
            self._simulation_state['rpm'] = rpm
            self._simulation_state['torque'] = torque
            mech_state['chain_speed'] = chain_speed
            
            # Update electrical system with optimized calculations
            if rpm > 100:  # Minimum RPM for generation
                voltage = 230 + (rpm - 100) * 0.1
                current = torque * 0.1
                power = voltage * current / 1000  # Convert to kW
            else:
                voltage = 0
                current = 0
                power = 0
            
            # Update electrical state
            elec_state['voltage'] = voltage
            elec_state['current'] = current
            self._simulation_state['power'] = power
            
            # Update pneumatic system with optimized calculations
            if pneumatic_state['compressor_active']:
                pressure = pneumatic_state['pressure']
                if pressure < 8.0:  # Max pressure 8 bar
                    pneumatic_state['pressure'] = min(pressure + dt * 0.1, 8.0)
            else:
                pneumatic_state['pressure'] = max(0, pneumatic_state['pressure'] - dt * 0.05)
            
            # Calculate efficiencies with optimized calculations
            if rpm > 0:
                self._simulation_state['mechanical_efficiency'] = min(0.95, 0.5 + rpm / 2000)
            else:
                self._simulation_state['mechanical_efficiency'] = 0
                
            if power > 0:
                self._simulation_state['electrical_efficiency'] = min(0.98, 0.6 + power / 100)
            else:
                self._simulation_state['electrical_efficiency'] = 0
                
        except Exception as e:
            self.logger.error(f"Error updating simulation: {e}")

# Singleton instance
_component_manager: Optional[ComponentManager] = None
_manager_lock = threading.Lock()

def get_component_manager() -> ComponentManager:
    """Get or create the singleton ComponentManager instance"""
    global _component_manager
    
    if _component_manager is None:
        with _manager_lock:
            if _component_manager is None:
                _component_manager = ComponentManager()
    
    return _component_manager 