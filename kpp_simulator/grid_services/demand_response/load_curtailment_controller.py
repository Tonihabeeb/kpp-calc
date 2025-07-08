"""
Load Curtailment Controller for KPP Simulator
Implements demand response and load management services
"""

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
from datetime import datetime, timedelta

from ...core.physics_engine import PhysicsEngine
from ...electrical.electrical_system import IntegratedElectricalSystem
from ...control_systems.control_system import IntegratedControlSystem


class CurtailmentMode(Enum):
    """Load curtailment modes"""
    AUTOMATIC = "automatic"
    MANUAL = "manual"
    SCHEDULED = "scheduled"
    EMERGENCY = "emergency"
    DISABLED = "disabled"


class LoadPriority(Enum):
    """Load priority levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    DISPOSABLE = "disposable"


@dataclass
class LoadSegment:
    """Load segment information"""
    segment_id: str
    name: str
    priority: LoadPriority
    current_load: float  # kW
    max_load: float  # kW
    min_load: float  # kW
    curtailment_potential: float  # kW
    is_curtailable: bool
    curtailment_cost: float  # $/kWh


@dataclass
class CurtailmentEvent:
    """Load curtailment event"""
    timestamp: datetime
    event_id: str
    mode: CurtailmentMode
    target_reduction: float  # kW
    actual_reduction: float  # kW
    duration: timedelta
    segments_affected: List[str]
    cost_savings: float
    revenue_generated: float


@dataclass
class DemandResponseConfig:
    """Demand response configuration"""
    max_curtailment: float  # kW
    min_notification_time: float  # minutes
    max_curtailment_duration: float  # hours
    curtailment_cost_threshold: float  # $/kWh
    revenue_per_kwh: float  # $/kWh
    response_time: float  # seconds


class LoadCurtailmentController:
    """
    Load Curtailment Controller for demand response services
    
    Features:
    - Load curtailment management
    - Peak shaving algorithms
    - Demand response coordination
    - Cost-benefit analysis
    - Load prioritization
    - Performance monitoring
    """
    
    def __init__(self, 
                 physics_engine: PhysicsEngine,
                 electrical_system: IntegratedElectricalSystem,
                 control_system: IntegratedControlSystem):
        """
        Initialize the Load Curtailment Controller
        
        Args:
            physics_engine: Core physics engine
            electrical_system: Integrated electrical system
            control_system: Integrated control system
        """
        self.physics_engine = physics_engine
        self.electrical_system = electrical_system
        self.control_system = control_system
        
        # Control state
        self.is_active = False
        self.current_mode = CurtailmentMode.DISABLED
        self.is_curtailing = False
        
        # Configuration
        self.config = DemandResponseConfig(
            max_curtailment=300.0,  # kW
            min_notification_time=15.0,  # minutes
            max_curtailment_duration=4.0,  # hours
            curtailment_cost_threshold=0.50,  # $/kWh
            revenue_per_kwh=0.80,  # $/kWh
            response_time=30.0  # seconds
        )
        
        # Load segments
        self.load_segments: Dict[str, LoadSegment] = {}
        self._initialize_load_segments()
        
        # Curtailment tracking
        self.curtailment_events: List[CurtailmentEvent] = []
        self.active_curtailment: Optional[CurtailmentEvent] = None
        
        # Performance tracking
        self.performance_metrics = {
            'total_curtailment_events': 0,
            'total_energy_curtailed': 0.0,  # kWh
            'total_cost_savings': 0.0,
            'total_revenue_generated': 0.0,
            'average_response_time': 0.0,
            'curtailment_accuracy': 0.0,
            'customer_satisfaction': 1.0,
            'availability': 1.0
        }
        
        # Load history
        self.load_history: List[Tuple[datetime, float]] = []
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        self.logger.info("Load Curtailment Controller initialized")
    
    def _initialize_load_segments(self):
        """Initialize load segments"""
        # Critical loads (cannot be curtailed)
        self.load_segments['critical_1'] = LoadSegment(
            segment_id='critical_1',
            name='Safety Systems',
            priority=LoadPriority.CRITICAL,
            current_load=50.0,
            max_load=50.0,
            min_load=50.0,
            curtailment_potential=0.0,
            is_curtailable=False,
            curtailment_cost=float('inf')
        )
        
        # High priority loads (limited curtailment)
        self.load_segments['high_1'] = LoadSegment(
            segment_id='high_1',
            name='Control Systems',
            priority=LoadPriority.HIGH,
            current_load=100.0,
            max_load=100.0,
            min_load=80.0,
            curtailment_potential=20.0,
            is_curtailable=True,
            curtailment_cost=2.0
        )
        
        # Medium priority loads
        self.load_segments['medium_1'] = LoadSegment(
            segment_id='medium_1',
            name='Auxiliary Equipment',
            priority=LoadPriority.MEDIUM,
            current_load=150.0,
            max_load=150.0,
            min_load=100.0,
            curtailment_potential=50.0,
            is_curtailable=True,
            curtailment_cost=0.5
        )
        
        # Low priority loads
        self.load_segments['low_1'] = LoadSegment(
            segment_id='low_1',
            name='Non-Essential Systems',
            priority=LoadPriority.LOW,
            current_load=200.0,
            max_load=200.0,
            min_load=50.0,
            curtailment_potential=150.0,
            is_curtailable=True,
            curtailment_cost=0.2
        )
        
        # Disposable loads
        self.load_segments['disposable_1'] = LoadSegment(
            segment_id='disposable_1',
            name='Comfort Systems',
            priority=LoadPriority.DISPOSABLE,
            current_load=100.0,
            max_load=100.0,
            min_load=0.0,
            curtailment_potential=100.0,
            is_curtailable=True,
            curtailment_cost=0.1
        )
    
    def start(self):
        """Start the load curtailment controller"""
        self.is_active = True
        self.current_mode = CurtailmentMode.AUTOMATIC
        self.logger.info("Load Curtailment Controller started")
    
    def stop(self):
        """Stop the load curtailment controller"""
        self.is_active = False
        self.current_mode = CurtailmentMode.DISABLED
        self.is_curtailing = False
        self.logger.info("Load Curtailment Controller stopped")
    
    def update(self, dt: float):
        """
        Update the load curtailment controller
        
        Args:
            dt: Time step in seconds
        """
        if not self.is_active:
            return
        
        # Update load measurements
        self._update_load_measurements()
        
        # Check for curtailment opportunities
        if self.current_mode == CurtailmentMode.AUTOMATIC:
            self._check_automatic_curtailment()
        
        # Update active curtailment
        if self.is_curtailing and self.active_curtailment:
            self._update_active_curtailment(dt)
        
        # Update performance metrics
        self._update_performance_metrics(dt)
        
        # Store load history
        self._store_load_history()
    
    def _update_load_measurements(self):
        """Update load measurements for all segments"""
        # Get electrical state
        electrical_state = self.electrical_system.get_state()
        total_load = electrical_state.get('load', 600.0)
        
        # Distribute load across segments (simplified)
        segment_loads = {
            'critical_1': 50.0,
            'high_1': 100.0,
            'medium_1': 150.0,
            'low_1': 200.0,
            'disposable_1': 100.0
        }
        
        # Update segment loads
        for segment_id, load in segment_loads.items():
            if segment_id in self.load_segments:
                self.load_segments[segment_id].current_load = load
    
    def _check_automatic_curtailment(self):
        """Check for automatic curtailment opportunities"""
        # Get current total load
        total_load = sum(segment.current_load for segment in self.load_segments.values())
        
        # Check if load exceeds threshold
        load_threshold = 500.0  # kW
        if total_load > load_threshold and not self.is_curtailing:
            target_reduction = total_load - load_threshold
            self._initiate_curtailment(target_reduction, CurtailmentMode.AUTOMATIC)
    
    def _initiate_curtailment(self, target_reduction: float, mode: CurtailmentMode):
        """Initiate load curtailment"""
        if self.is_curtailing:
            self.logger.warning("Curtailment already in progress")
            return
        
        # Create curtailment event
        event_id = f"curtailment_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        
        event = CurtailmentEvent(
            timestamp=datetime.now(),
            event_id=event_id,
            mode=mode,
            target_reduction=target_reduction,
            actual_reduction=0.0,
            duration=timedelta(0),
            segments_affected=[],
            cost_savings=0.0,
            revenue_generated=0.0
        )
        
        # Execute curtailment
        actual_reduction, affected_segments = self._execute_curtailment(target_reduction)
        
        # Update event
        event.actual_reduction = actual_reduction
        event.segments_affected = affected_segments
        
        # Calculate financial impact
        event.cost_savings = actual_reduction * self.config.curtailment_cost_threshold
        event.revenue_generated = actual_reduction * self.config.revenue_per_kwh
        
        # Store event
        self.curtailment_events.append(event)
        self.active_curtailment = event
        self.is_curtailing = True
        
        self.logger.info(f"Curtailment initiated: {actual_reduction:.1f} kW reduction, {len(affected_segments)} segments affected")
    
    def _execute_curtailment(self, target_reduction: float) -> Tuple[float, List[str]]:
        """Execute load curtailment"""
        remaining_reduction = target_reduction
        affected_segments = []
        total_reduction = 0.0
        
        # Sort segments by priority (lowest priority first)
        priority_order = [LoadPriority.DISPOSABLE, LoadPriority.LOW, LoadPriority.MEDIUM, LoadPriority.HIGH]
        
        for priority in priority_order:
            if remaining_reduction <= 0:
                break
            
            # Get segments with this priority
            segments = [s for s in self.load_segments.values() 
                       if s.priority == priority and s.is_curtailable]
            
            for segment in segments:
                if remaining_reduction <= 0:
                    break
                
                # Calculate possible reduction for this segment
                possible_reduction = min(
                    remaining_reduction,
                    segment.curtailment_potential,
                    segment.current_load - segment.min_load
                )
                
                if possible_reduction > 0:
                    # Apply curtailment
                    segment.current_load -= possible_reduction
                    remaining_reduction -= possible_reduction
                    total_reduction += possible_reduction
                    affected_segments.append(segment.segment_id)
                    
                    self.logger.debug(f"Curtailed {segment.name}: {possible_reduction:.1f} kW")
        
        return total_reduction, affected_segments
    
    def _update_active_curtailment(self, dt: float):
        """Update active curtailment"""
        if not self.active_curtailment:
            return
        
        # Update duration
        self.active_curtailment.duration += timedelta(seconds=dt)
        
        # Check if curtailment should end
        max_duration = timedelta(hours=self.config.max_curtailment_duration)
        if self.active_curtailment.duration >= max_duration:
            self._end_curtailment()
    
    def _end_curtailment(self):
        """End active curtailment"""
        if not self.active_curtailment:
            return
        
        # Restore loads
        self._restore_loads()
        
        # Update performance metrics
        self.performance_metrics['total_curtailment_events'] += 1
        self.performance_metrics['total_energy_curtailed'] += (
            self.active_curtailment.actual_reduction * 
            self.active_curtailment.duration.total_seconds() / 3600
        )
        self.performance_metrics['total_cost_savings'] += self.active_curtailment.cost_savings
        self.performance_metrics['total_revenue_generated'] += self.active_curtailment.revenue_generated
        
        self.logger.info(f"Curtailment ended: {self.active_curtailment.actual_reduction:.1f} kW for {self.active_curtailment.duration}")
        
        # Clear active curtailment
        self.active_curtailment = None
        self.is_curtailing = False
    
    def _restore_loads(self):
        """Restore loads to normal operation"""
        for segment in self.load_segments.values():
            if segment.is_curtailable:
                # Restore to max load
                segment.current_load = segment.max_load
    
    def _update_performance_metrics(self, dt: float):
        """Update performance metrics"""
        # Calculate average response time
        if self.curtailment_events:
            response_times = []
            for event in self.curtailment_events[-50:]:  # Last 50 events
                if event.actual_reduction > 0:
                    response_time = event.duration.total_seconds()
                    response_times.append(response_time)
            
            if response_times:
                self.performance_metrics['average_response_time'] = np.mean(response_times)
        
        # Calculate curtailment accuracy
        if self.curtailment_events:
            accuracies = []
            for event in self.curtailment_events[-50:]:
                if event.target_reduction > 0:
                    accuracy = event.actual_reduction / event.target_reduction
                    accuracies.append(min(1.0, accuracy))
            
            if accuracies:
                self.performance_metrics['curtailment_accuracy'] = np.mean(accuracies)
    
    def _store_load_history(self):
        """Store load history"""
        current_time = datetime.now()
        total_load = sum(segment.current_load for segment in self.load_segments.values())
        
        self.load_history.append((current_time, total_load))
        
        # Limit history size
        if len(self.load_history) > 10000:
            self.load_history.pop(0)
    
    def request_curtailment(self, target_reduction: float, mode: CurtailmentMode = CurtailmentMode.MANUAL) -> str:
        """
        Request load curtailment
        
        Args:
            target_reduction: Target load reduction in kW
            mode: Curtailment mode
            
        Returns:
            Event ID
        """
        if self.is_curtailing:
            raise ValueError("Curtailment already in progress")
        
        if target_reduction > self.config.max_curtailment:
            raise ValueError(f"Target reduction {target_reduction} kW exceeds maximum {self.config.max_curtailment} kW")
        
        self._initiate_curtailment(target_reduction, mode)
        
        return self.active_curtailment.event_id if self.active_curtailment else ""
    
    def end_curtailment(self) -> bool:
        """
        End active curtailment
        
        Returns:
            True if curtailment was ended successfully
        """
        if not self.is_curtailing:
            return False
        
        self._end_curtailment()
        return True
    
    def get_load_segments(self) -> Dict[str, LoadSegment]:
        """Get all load segments"""
        return self.load_segments.copy()
    
    def get_segment_load(self, segment_id: str) -> Optional[float]:
        """Get current load for a specific segment"""
        if segment_id in self.load_segments:
            return self.load_segments[segment_id].current_load
        return None
    
    def set_segment_load(self, segment_id: str, load: float):
        """Set load for a specific segment"""
        if segment_id in self.load_segments:
            segment = self.load_segments[segment_id]
            load = np.clip(load, segment.min_load, segment.max_load)
            segment.current_load = load
            self.logger.info(f"Segment {segment_id} load set to: {load:.1f} kW")
    
    def set_curtailment_mode(self, mode: CurtailmentMode):
        """Set curtailment mode"""
        self.current_mode = mode
        self.logger.info(f"Curtailment mode set to: {mode.value}")
    
    def set_configuration(self, config: DemandResponseConfig):
        """Set demand response configuration"""
        self.config = config
        self.logger.info("Demand response configuration updated")
    
    def get_current_status(self) -> Dict[str, Any]:
        """Get current controller status"""
        total_load = sum(segment.current_load for segment in self.load_segments.values())
        
        return {
            'is_active': self.is_active,
            'curtailment_mode': self.current_mode.value,
            'is_curtailing': self.is_curtailing,
            'total_load': total_load,
            'available_curtailment': self.config.max_curtailment,
            'active_event_id': self.active_curtailment.event_id if self.active_curtailment else None
        }
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics"""
        return self.performance_metrics.copy()
    
    def get_curtailment_events(self, duration: timedelta = timedelta(hours=24)) -> List[CurtailmentEvent]:
        """Get curtailment events for specified duration"""
        cutoff_time = datetime.now() - duration
        return [e for e in self.curtailment_events if e.timestamp >= cutoff_time]
    
    def get_load_history(self, duration: timedelta = timedelta(hours=1)) -> List[Tuple[datetime, float]]:
        """Get load history for specified duration"""
        cutoff_time = datetime.now() - duration
        return [(t, l) for t, l in self.load_history if t >= cutoff_time]
    
    def clear_history(self):
        """Clear curtailment and load history"""
        self.curtailment_events.clear()
        self.load_history.clear()
        self.logger.info("History cleared")
    
    def reset_performance_metrics(self):
        """Reset performance metrics"""
        self.performance_metrics = {
            'total_curtailment_events': 0,
            'total_energy_curtailed': 0.0,
            'total_cost_savings': 0.0,
            'total_revenue_generated': 0.0,
            'average_response_time': 0.0,
            'curtailment_accuracy': 0.0,
            'customer_satisfaction': 1.0,
            'availability': 1.0
        }
        
        self.logger.info("Performance metrics reset") 