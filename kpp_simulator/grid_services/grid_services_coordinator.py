"""
Grid Services Coordinator for KPP Simulator
Coordinates all grid services and manages service delivery
"""

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
from datetime import datetime, timedelta

from ..core.physics_engine import PhysicsEngine
from ..electrical.electrical_system import IntegratedElectricalSystem
from ..control_systems.control_system import IntegratedControlSystem


class ServiceType(Enum):
    """Types of grid services"""
    FREQUENCY_RESPONSE = "frequency_response"
    VOLTAGE_SUPPORT = "voltage_support"
    ENERGY_STORAGE = "energy_storage"
    ECONOMIC_OPTIMIZATION = "economic_optimization"
    DEMAND_RESPONSE = "demand_response"
    POWER_QUALITY = "power_quality"
    SYNTHETIC_INERTIA = "synthetic_inertia"
    BLACK_START = "black_start"


class ServicePriority(Enum):
    """Service priority levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ServiceStatus(Enum):
    """Service status states"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    STANDBY = "standby"
    ERROR = "error"
    MAINTENANCE = "maintenance"


@dataclass
class ServiceRequest:
    """Represents a grid service request"""
    service_type: ServiceType
    priority: ServicePriority
    magnitude: float
    duration: timedelta
    timestamp: datetime
    request_id: str
    source: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    status: ServiceStatus = ServiceStatus.INACTIVE
    response_time: Optional[timedelta] = None
    completion_time: Optional[timedelta] = None


@dataclass
class ServicePerformance:
    """Performance metrics for a service"""
    service_type: ServiceType
    response_time: float
    accuracy: float
    availability: float
    revenue: float
    cost: float
    efficiency: float
    uptime: float
    downtime: float
    total_requests: int
    successful_requests: int
    failed_requests: int


@dataclass
class ServiceConfiguration:
    """Configuration for a grid service"""
    service_type: ServiceType
    enabled: bool
    priority: ServicePriority
    capacity: float
    response_time_target: float
    accuracy_target: float
    cost_per_mwh: float
    revenue_per_mwh: float
    parameters: Dict[str, Any] = field(default_factory=dict)


class GridServicesCoordinator:
    """
    Coordinates all grid services and manages service delivery
    
    Features:
    - Service coordination and prioritization
    - Resource allocation and optimization
    - Performance monitoring and analytics
    - Revenue optimization and cost management
    - Communication with grid operators and markets
    """
    
    def __init__(self, 
                 physics_engine: PhysicsEngine,
                 electrical_system: IntegratedElectricalSystem,
                 control_system: IntegratedControlSystem):
        """
        Initialize the Grid Services Coordinator
        
        Args:
            physics_engine: Core physics engine
            electrical_system: Integrated electrical system
            control_system: Integrated control system
        """
        self.physics_engine = physics_engine
        self.electrical_system = electrical_system
        self.control_system = control_system
        
        # Service management
        self.is_active = False
        self.active_services: Dict[ServiceType, ServiceConfiguration] = {}
        self.service_requests: List[ServiceRequest] = []
        self.service_performance: Dict[ServiceType, ServicePerformance] = {}
        
        # Resource allocation
        self.available_capacity = 1000.0  # kW
        self.allocated_capacity: Dict[ServiceType, float] = {}
        self.capacity_limits = {
            ServiceType.FREQUENCY_RESPONSE: 300.0,  # kW
            ServiceType.VOLTAGE_SUPPORT: 200.0,
            ServiceType.ENERGY_STORAGE: 400.0,
            ServiceType.ECONOMIC_OPTIMIZATION: 500.0,
            ServiceType.DEMAND_RESPONSE: 300.0,
            ServiceType.POWER_QUALITY: 150.0,
            ServiceType.SYNTHETIC_INERTIA: 100.0,
            ServiceType.BLACK_START: 50.0
        }
        
        # Performance tracking
        self.performance_metrics = {
            'total_revenue': 0.0,
            'total_cost': 0.0,
            'total_profit': 0.0,
            'service_uptime': 1.0,
            'average_response_time': 0.0,
            'service_accuracy': 0.0,
            'customer_satisfaction': 1.0
        }
        
        # Communication interfaces
        self.grid_operator_interface = None
        self.market_interface = None
        self.control_center_interface = None
        
        # Initialize service configurations
        self._initialize_service_configs()
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        self.logger.info("Grid Services Coordinator initialized")
    
    def _initialize_service_configs(self):
        """Initialize service configurations"""
        
        # Frequency Response Service
        self.active_services[ServiceType.FREQUENCY_RESPONSE] = ServiceConfiguration(
            service_type=ServiceType.FREQUENCY_RESPONSE,
            enabled=True,
            priority=ServicePriority.HIGH,
            capacity=300.0,
            response_time_target=0.5,  # seconds
            accuracy_target=0.95,
            cost_per_mwh=50.0,
            revenue_per_mwh=80.0,
            parameters={
                'droop_characteristic': 0.05,
                'dead_band': 0.01,
                'response_time': 0.5
            }
        )
        
        # Voltage Support Service
        self.active_services[ServiceType.VOLTAGE_SUPPORT] = ServiceConfiguration(
            service_type=ServiceType.VOLTAGE_SUPPORT,
            enabled=True,
            priority=ServicePriority.MEDIUM,
            capacity=200.0,
            response_time_target=1.0,
            accuracy_target=0.90,
            cost_per_mwh=30.0,
            revenue_per_mwh=60.0,
            parameters={
                'voltage_range': (0.95, 1.05),
                'reactive_power_capacity': 0.3,
                'response_time': 1.0
            }
        )
        
        # Energy Storage Service
        self.active_services[ServiceType.ENERGY_STORAGE] = ServiceConfiguration(
            service_type=ServiceType.ENERGY_STORAGE,
            enabled=True,
            priority=ServicePriority.MEDIUM,
            capacity=400.0,
            response_time_target=0.2,
            accuracy_target=0.98,
            cost_per_mwh=40.0,
            revenue_per_mwh=70.0,
            parameters={
                'storage_capacity': 1000.0,  # kWh
                'charge_efficiency': 0.95,
                'discharge_efficiency': 0.95,
                'response_time': 0.2
            }
        )
        
        # Economic Optimization Service
        self.active_services[ServiceType.ECONOMIC_OPTIMIZATION] = ServiceConfiguration(
            service_type=ServiceType.ECONOMIC_OPTIMIZATION,
            enabled=True,
            priority=ServicePriority.LOW,
            capacity=500.0,
            response_time_target=5.0,
            accuracy_target=0.85,
            cost_per_mwh=20.0,
            revenue_per_mwh=50.0,
            parameters={
                'optimization_horizon': 24,  # hours
                'price_forecast_accuracy': 0.85,
                'response_time': 5.0
            }
        )
        
        # Demand Response Service
        self.active_services[ServiceType.DEMAND_RESPONSE] = ServiceConfiguration(
            service_type=ServiceType.DEMAND_RESPONSE,
            enabled=True,
            priority=ServicePriority.MEDIUM,
            capacity=300.0,
            response_time_target=2.0,
            accuracy_target=0.90,
            cost_per_mwh=25.0,
            revenue_per_mwh=55.0,
            parameters={
                'curtailment_capacity': 300.0,
                'response_time': 2.0,
                'notification_time': 1.0
            }
        )
        
        # Power Quality Service
        self.active_services[ServiceType.POWER_QUALITY] = ServiceConfiguration(
            service_type=ServiceType.POWER_QUALITY,
            enabled=True,
            priority=ServicePriority.HIGH,
            capacity=150.0,
            response_time_target=0.1,
            accuracy_target=0.99,
            cost_per_mwh=60.0,
            revenue_per_mwh=100.0,
            parameters={
                'harmonic_filtering': True,
                'power_factor_correction': True,
                'response_time': 0.1
            }
        )
        
        # Synthetic Inertia Service
        self.active_services[ServiceType.SYNTHETIC_INERTIA] = ServiceConfiguration(
            service_type=ServiceType.SYNTHETIC_INERTIA,
            enabled=True,
            priority=ServicePriority.CRITICAL,
            capacity=100.0,
            response_time_target=0.05,
            accuracy_target=0.99,
            cost_per_mwh=80.0,
            revenue_per_mwh=120.0,
            parameters={
                'inertia_constant': 5.0,
                'response_time': 0.05,
                'rocof_detection': True
            }
        )
        
        # Black Start Service
        self.active_services[ServiceType.BLACK_START] = ServiceConfiguration(
            service_type=ServiceType.BLACK_START,
            enabled=False,
            priority=ServicePriority.CRITICAL,
            capacity=50.0,
            response_time_target=10.0,
            accuracy_target=0.95,
            cost_per_mwh=200.0,
            revenue_per_mwh=500.0,
            parameters={
                'startup_time': 10.0,
                'fuel_availability': True,
                'response_time': 10.0
            }
        )
    
    def start(self):
        """Start the grid services coordinator"""
        self.is_active = True
        self.logger.info("Grid Services Coordinator started")
    
    def stop(self):
        """Stop the grid services coordinator"""
        self.is_active = False
        self.logger.info("Grid Services Coordinator stopped")
    
    def update(self, dt: float):
        """
        Update the grid services coordinator
        
        Args:
            dt: Time step in seconds
        """
        if not self.is_active:
            return
        
        # Process service requests
        self._process_service_requests(dt)
        
        # Update service performance
        self._update_service_performance(dt)
        
        # Optimize resource allocation
        self._optimize_resource_allocation()
        
        # Update performance metrics
        self._update_performance_metrics()
    
    def request_service(self, 
                       service_type: ServiceType,
                       priority: ServicePriority,
                       magnitude: float,
                       duration: timedelta,
                       source: str = "grid_operator",
                       parameters: Optional[Dict[str, Any]] = None) -> str:
        """
        Request a grid service
        
        Args:
            service_type: Type of service requested
            priority: Priority level of the request
            magnitude: Magnitude of the service (kW)
            duration: Duration of the service
            source: Source of the request
            parameters: Additional parameters
            
        Returns:
            Request ID
        """
        request_id = f"{service_type.value}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        
        request = ServiceRequest(
            service_type=service_type,
            priority=priority,
            magnitude=magnitude,
            duration=duration,
            timestamp=datetime.now(),
            request_id=request_id,
            source=source,
            parameters=parameters or {}
        )
        
        self.service_requests.append(request)
        
        self.logger.info(f"Service request received: {service_type.value} - {priority.value} - {magnitude:.2f} kW")
        
        return request_id
    
    def _process_service_requests(self, dt: float):
        """Process active service requests"""
        current_time = datetime.now()
        
        for request in self.service_requests:
            if request.status == ServiceStatus.INACTIVE:
                # Check if service can be provided
                if self._can_provide_service(request):
                    self._activate_service(request)
                else:
                    self.logger.warning(f"Cannot provide service: {request.service_type.value} - Insufficient capacity")
            
            elif request.status == ServiceStatus.ACTIVE:
                # Check if service duration has expired
                if current_time - request.timestamp >= request.duration:
                    self._complete_service(request)
    
    def _can_provide_service(self, request: ServiceRequest) -> bool:
        """Check if a service can be provided"""
        
        # Check if service is enabled
        if not self.active_services[request.service_type].enabled:
            return False
        
        # Check capacity availability
        required_capacity = request.magnitude
        available_capacity = self._get_available_capacity(request.service_type)
        
        return available_capacity >= required_capacity
    
    def _get_available_capacity(self, service_type: ServiceType) -> float:
        """Get available capacity for a service type"""
        total_capacity = self.active_services[service_type].capacity
        allocated_capacity = self.allocated_capacity.get(service_type, 0.0)
        return max(0.0, total_capacity - allocated_capacity)
    
    def _activate_service(self, request: ServiceRequest):
        """Activate a service request"""
        request.status = ServiceStatus.ACTIVE
        request.response_time = datetime.now() - request.timestamp
        
        # Allocate capacity
        current_allocated = self.allocated_capacity.get(request.service_type, 0.0)
        self.allocated_capacity[request.service_type] = current_allocated + request.magnitude
        
        # Notify control system
        self._notify_control_system(request)
        
        self.logger.info(f"Service activated: {request.service_type.value} - {request.magnitude:.2f} kW")
    
    def _complete_service(self, request: ServiceRequest):
        """Complete a service request"""
        request.status = ServiceStatus.INACTIVE
        request.completion_time = datetime.now() - request.timestamp
        
        # Deallocate capacity
        current_allocated = self.allocated_capacity.get(request.service_type, 0.0)
        self.allocated_capacity[request.service_type] = max(0.0, current_allocated - request.magnitude)
        
        # Calculate revenue and cost
        revenue = self._calculate_service_revenue(request)
        cost = self._calculate_service_cost(request)
        
        # Update performance metrics
        self.performance_metrics['total_revenue'] += revenue
        self.performance_metrics['total_cost'] += cost
        self.performance_metrics['total_profit'] += (revenue - cost)
        
        self.logger.info(f"Service completed: {request.service_type.value} - Revenue: ${revenue:.2f}, Cost: ${cost:.2f}")
    
    def _notify_control_system(self, request: ServiceRequest):
        """Notify the control system of service activation"""
        # This would interface with the control system to activate the appropriate service
        pass
    
    def _calculate_service_revenue(self, request: ServiceRequest) -> float:
        """Calculate revenue for a completed service"""
        config = self.active_services[request.service_type]
        energy_mwh = (request.magnitude * request.duration.total_seconds() / 3600) / 1000
        return energy_mwh * config.revenue_per_mwh
    
    def _calculate_service_cost(self, request: ServiceRequest) -> float:
        """Calculate cost for a completed service"""
        config = self.active_services[request.service_type]
        energy_mwh = (request.magnitude * request.duration.total_seconds() / 3600) / 1000
        return energy_mwh * config.cost_per_mwh
    
    def _update_service_performance(self, dt: float):
        """Update service performance metrics"""
        for service_type, config in self.active_services.items():
            if service_type not in self.service_performance:
                self.service_performance[service_type] = ServicePerformance(
                    service_type=service_type,
                    response_time=0.0,
                    accuracy=0.0,
                    availability=1.0,
                    revenue=0.0,
                    cost=0.0,
                    efficiency=0.0,
                    uptime=1.0,
                    downtime=0.0,
                    total_requests=0,
                    successful_requests=0,
                    failed_requests=0
                )
            
            # Update performance based on recent requests
            recent_requests = [r for r in self.service_requests 
                             if r.service_type == service_type and 
                             r.timestamp > datetime.now() - timedelta(hours=1)]
            
            if recent_requests:
                performance = self.service_performance[service_type]
                performance.total_requests = len(recent_requests)
                performance.successful_requests = len([r for r in recent_requests if r.status == ServiceStatus.INACTIVE])
                performance.failed_requests = performance.total_requests - performance.successful_requests
                
                if performance.total_requests > 0:
                    performance.availability = performance.successful_requests / performance.total_requests
    
    def _optimize_resource_allocation(self):
        """Optimize resource allocation across services"""
        # Simple optimization: prioritize higher revenue services
        total_available = self.available_capacity
        
        # Sort services by revenue per MWh
        sorted_services = sorted(
            self.active_services.items(),
            key=lambda x: x[1].revenue_per_mwh,
            reverse=True
        )
        
        for service_type, config in sorted_services:
            if config.enabled:
                # Allocate capacity based on priority and revenue
                allocation = min(config.capacity, total_available * 0.3)  # Max 30% per service
                self.allocated_capacity[service_type] = allocation
                total_available -= allocation
    
    def _update_performance_metrics(self):
        """Update overall performance metrics"""
        if self.performance_metrics['total_revenue'] > 0:
            self.performance_metrics['service_accuracy'] = np.mean([
                perf.accuracy for perf in self.service_performance.values()
            ])
            
            self.performance_metrics['average_response_time'] = np.mean([
                perf.response_time for perf in self.service_performance.values()
            ])
    
    def get_service_status(self, service_type: ServiceType) -> ServiceStatus:
        """Get status of a specific service"""
        if service_type in self.active_services:
            return ServiceStatus.ACTIVE if self.active_services[service_type].enabled else ServiceStatus.INACTIVE
        return ServiceStatus.ERROR
    
    def enable_service(self, service_type: ServiceType):
        """Enable a grid service"""
        if service_type in self.active_services:
            self.active_services[service_type].enabled = True
            self.logger.info(f"Service enabled: {service_type.value}")
    
    def disable_service(self, service_type: ServiceType):
        """Disable a grid service"""
        if service_type in self.active_services:
            self.active_services[service_type].enabled = False
            self.logger.info(f"Service disabled: {service_type.value}")
    
    def get_available_services(self) -> List[ServiceType]:
        """Get list of available services"""
        return [service_type for service_type, config in self.active_services.items() 
                if config.enabled]
    
    def get_service_performance(self, service_type: ServiceType) -> Optional[ServicePerformance]:
        """Get performance metrics for a specific service"""
        return self.service_performance.get(service_type)
    
    def get_overall_performance(self) -> Dict[str, Any]:
        """Get overall performance metrics"""
        return self.performance_metrics.copy()
    
    def get_resource_allocation(self) -> Dict[ServiceType, float]:
        """Get current resource allocation"""
        return self.allocated_capacity.copy()
    
    def set_service_priority(self, service_type: ServiceType, priority: ServicePriority):
        """Set priority for a service"""
        if service_type in self.active_services:
            self.active_services[service_type].priority = priority
            self.logger.info(f"Service priority updated: {service_type.value} - {priority.value}")
    
    def get_service_configuration(self, service_type: ServiceType) -> Optional[ServiceConfiguration]:
        """Get configuration for a specific service"""
        return self.active_services.get(service_type)
    
    def update_service_configuration(self, service_type: ServiceType, config: ServiceConfiguration):
        """Update configuration for a specific service"""
        self.active_services[service_type] = config
        self.logger.info(f"Service configuration updated: {service_type.value}")
    
    def clear_service_requests(self):
        """Clear all service requests"""
        self.service_requests.clear()
        self.logger.info("Service requests cleared")
    
    def get_active_requests(self) -> List[ServiceRequest]:
        """Get list of active service requests"""
        return [r for r in self.service_requests if r.status == ServiceStatus.ACTIVE] 