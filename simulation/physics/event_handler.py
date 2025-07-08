import math
import logging
import time
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from config.config import RHO_WATER, G

"""
Event Handler for KPP Simulation
Manages floater state transitions (injection/venting) and energy tracking.
"""

class EventType(str, Enum):
    """Event type enumeration"""
    INJECTION = "injection"
    VENTING = "venting"
    STATE_CHANGE = "state_change"
    ERROR = "error"

class ZoneType(str, Enum):
    """Zone type enumeration"""
    INJECTION_ZONE = "injection_zone"
    VENTING_ZONE = "venting_zone"
    TRANSITION_ZONE = "transition_zone"

@dataclass
class EventData:
    """Event data structure"""
    event_type: EventType
    floater_id: int
    timestamp: float
    position: float
    angle: float
    energy_cost: float = 0.0
    success: bool = True
    error_message: Optional[str] = None

@dataclass
class ZoneConfig:
    """Zone configuration"""
    zone_type: ZoneType
    start_angle: float
    end_angle: float
    tolerance: float = 0.1  # radians
    min_interval: float = 0.5  # seconds

class EventHandler:
    """
    Enhanced event handler for KPP simulation.
    Manages floater state transitions, energy tracking, and event optimization.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the event handler.
        
        Args:
            config: Configuration dictionary for event handling
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # Physics constants
        self.rho_water = RHO_WATER
        self.gravity = G
        self.atmospheric_pressure = 101325.0  # Pa
        
        # Event tracking
        self.events: List[EventData] = []
        self.last_event_time: Dict[int, float] = {}
        self.event_count = 0
        self.success_count = 0
        self.error_count = 0
        
        # Energy tracking
        self.total_energy_cost = 0.0
        self.total_compression_work = 0.0
        self.total_thermal_energy = 0.0
        self.energy_efficiency = 0.0
        
        # Zone configuration
        self.injection_zone = ZoneConfig(
            zone_type=ZoneType.INJECTION_ZONE,
            start_angle=0.0,  # Bottom position
            end_angle=0.2,    # 0.2 radians ≈ 11.5 degrees
            tolerance=0.05,
            min_interval=0.5
        )
        
        self.venting_zone = ZoneConfig(
            zone_type=ZoneType.VENTING_ZONE,
            start_angle=math.pi - 0.2,  # Top position
            end_angle=math.pi + 0.2,    # ±0.2 radians around top
            tolerance=0.05,
            min_interval=0.5
        )
        
        # Performance metrics
        self.performance_metrics = {
            'total_events': 0,
            'successful_events': 0,
            'failed_events': 0,
            'average_energy_cost': 0.0,
            'total_energy_cost': 0.0,
            'efficiency': 0.0
        }
        
        self.logger.info("Event handler initialized")
    
    def calculate_angular_position(self, position: float, tank_height: float = 10.0) -> float:
        """
        Convert linear position to angular position on the chain.
        
        Args:
            position: Linear position (m)
            tank_height: Tank height (m)
            
        Returns:
            Angular position (radians)
        """
        # Normalize position to 0-1 range
        normalized_position = position / tank_height
        
        # Convert to angle (0 = bottom, π = top)
        angle = normalized_position * math.pi
        
        return angle
    
    def is_in_zone(self, angle: float, zone: ZoneConfig) -> bool:
        """
        Check if floater is in a specific zone.
        
        Args:
            angle: Current angular position (radians)
            zone: Zone configuration
            
        Returns:
            True if in zone, False otherwise
        """
        # Normalize angle to 0-2π range
        angle = angle % (2 * math.pi)
        
        # Check if angle is within zone bounds
        if zone.start_angle <= zone.end_angle:
            return zone.start_angle - zone.tolerance <= angle <= zone.end_angle + zone.tolerance
        else:
            # Handle zones that cross 0/2π boundary
            return (angle >= zone.start_angle - zone.tolerance or 
                   angle <= zone.end_angle + zone.tolerance)
    
    def can_trigger_event(self, floater_id: int, event_type: EventType) -> bool:
        """
        Check if an event can be triggered for a floater.
        
        Args:
            floater_id: Floater identifier
            event_type: Type of event to trigger
            
        Returns:
            True if event can be triggered, False otherwise
        """
        current_time = time.time()
        last_time = self.last_event_time.get(floater_id, 0.0)
        
        # Get minimum interval for event type
        if event_type == EventType.INJECTION:
            min_interval = self.injection_zone.min_interval
        elif event_type == EventType.VENTING:
            min_interval = self.venting_zone.min_interval
        else:
            min_interval = 0.1  # Default minimum interval
        
        # Check if enough time has passed
        return (current_time - last_time) >= min_interval
    
    def calculate_compression_work(self, volume: float, initial_pressure: float, 
                                 final_pressure: float) -> float:
        """
        Calculate compression work using isothermal compression formula.
        
        Args:
            volume: Volume of air (m³)
            initial_pressure: Initial pressure (Pa)
            final_pressure: Final pressure (Pa)
            
        Returns:
            Compression work (Joules)
        """
        # Isothermal compression work: W = P × V × ln(P_final/P_initial)
        if initial_pressure <= 0 or final_pressure <= 0:
            return 0.0
        
        work = initial_pressure * volume * math.log(final_pressure / initial_pressure)
        return work
    
    def calculate_injection_energy_cost(self, floater: Any, target_volume: float) -> float:
        """
        Calculate energy cost for air injection.
        
        Args:
            floater: Floater object
            target_volume: Target air volume (m³)
            
        Returns:
            Energy cost (Joules)
        """
        try:
            # Get floater properties
            position = getattr(floater, 'position', 0.0)
            tank_height = self.config.get('tank_height', 10.0)
            
            # Calculate depth and pressure
            depth = max(0.0, tank_height - position)
            hydrostatic_pressure = self.rho_water * self.gravity * depth
            final_pressure = self.atmospheric_pressure + hydrostatic_pressure
            
            # Calculate compression work
            compression_work = self.calculate_compression_work(
                target_volume, self.atmospheric_pressure, final_pressure
            )
            
            # Add thermal effects (simplified)
            thermal_factor = 1.1  # 10% thermal losses
            total_energy = compression_work * thermal_factor
            
            return total_energy
            
        except Exception as e:
            self.logger.error("Error calculating injection energy cost: %s", e)
            return 0.0
    
    def handle_injection_event(self, floater: Any, floater_id: int, 
                             target_volume: float = 0.4) -> EventData:
        """
        Handle air injection event.
        
        Args:
            floater: Floater object
            floater_id: Floater identifier
            target_volume: Target air volume (m³)
            
        Returns:
            Event data
        """
        current_time = time.time()
        position = getattr(floater, 'position', 0.0)
        angle = self.calculate_angular_position(position)
        
        # Check if in injection zone
        if not self.is_in_zone(angle, self.injection_zone):
            return EventData(
                event_type=EventType.ERROR,
                floater_id=floater_id,
                timestamp=current_time,
                position=position,
                angle=angle,
                success=False,
                error_message="Not in injection zone"
            )
        
        # Check if event can be triggered
        if not self.can_trigger_event(floater_id, EventType.INJECTION):
            return EventData(
                event_type=EventType.ERROR,
                floater_id=floater_id,
                timestamp=current_time,
                position=position,
                angle=angle,
                success=False,
                error_message="Event interval too short"
            )
        
        try:
            # Calculate energy cost
            energy_cost = self.calculate_injection_energy_cost(floater, target_volume)
            
            # Update floater state
            floater.air_fill_level = 1.0  # Fill completely
            floater.state = "full"
            
            # Update tracking
            self.last_event_time[floater_id] = current_time
            self.total_energy_cost += energy_cost
            self.total_compression_work += energy_cost
            
            # Create event data
            event_data = EventData(
                event_type=EventType.INJECTION,
                floater_id=floater_id,
                timestamp=current_time,
                position=position,
                angle=angle,
                energy_cost=energy_cost,
                success=True
            )
            
            # Update performance metrics
            self._update_performance_metrics(event_data)
            
            self.logger.info("Injection event successful for floater %d: energy=%.2f J", 
                           floater_id, energy_cost)
            
            return event_data
            
        except Exception as e:
            self.logger.error("Error in injection event: %s", e)
            return EventData(
                event_type=EventType.ERROR,
                floater_id=floater_id,
                timestamp=current_time,
                position=position,
                angle=angle,
                success=False,
                error_message=str(e)
            )
    
    def handle_venting_event(self, floater: Any, floater_id: int) -> EventData:
        """
        Handle air venting event.
        
        Args:
            floater: Floater object
            floater_id: Floater identifier
            
        Returns:
            Event data
        """
        current_time = time.time()
        position = getattr(floater, 'position', 0.0)
        angle = self.calculate_angular_position(position)
        
        # Check if in venting zone
        if not self.is_in_zone(angle, self.venting_zone):
            return EventData(
                event_type=EventType.ERROR,
                floater_id=floater_id,
                timestamp=current_time,
                position=position,
                angle=angle,
                success=False,
                error_message="Not in venting zone"
            )
        
        # Check if event can be triggered
        if not self.can_trigger_event(floater_id, EventType.VENTING):
            return EventData(
                event_type=EventType.ERROR,
                floater_id=floater_id,
                timestamp=current_time,
                position=position,
                angle=angle,
                success=False,
                error_message="Event interval too short"
            )
        
        try:
            # Calculate energy recovery (simplified)
            energy_recovery = 0.0  # No energy recovery in venting
            
            # Update floater state
            floater.air_fill_level = 0.0  # Empty completely
            floater.state = "empty"
            
            # Update tracking
            self.last_event_time[floater_id] = current_time
            
            # Create event data
            event_data = EventData(
                event_type=EventType.VENTING,
                floater_id=floater_id,
                timestamp=current_time,
                position=position,
                angle=angle,
                energy_cost=energy_recovery,
                success=True
            )
            
            # Update performance metrics
            self._update_performance_metrics(event_data)
            
            self.logger.info("Venting event successful for floater %d", floater_id)
            
            return event_data
            
        except Exception as e:
            self.logger.error("Error in venting event: %s", e)
            return EventData(
                event_type=EventType.ERROR,
                floater_id=floater_id,
                timestamp=current_time,
                position=position,
                angle=angle,
                success=False,
                error_message=str(e)
            )
    
    def process_floater_events(self, floater: Any, floater_id: int) -> List[EventData]:
        """
        Process all events for a floater.
        
        Args:
            floater: Floater object
            floater_id: Floater identifier
            
        Returns:
            List of event data
        """
        events = []
        position = getattr(floater, 'position', 0.0)
        angle = self.calculate_angular_position(position)
        state = getattr(floater, 'state', 'empty')
        
        # Check for injection event (empty floater in injection zone)
        if (state == 'empty' and 
            self.is_in_zone(angle, self.injection_zone) and
            self.can_trigger_event(floater_id, EventType.INJECTION)):
            
            injection_event = self.handle_injection_event(floater, floater_id)
            events.append(injection_event)
        
        # Check for venting event (full floater in venting zone)
        elif (state == 'full' and 
              self.is_in_zone(angle, self.venting_zone) and
              self.can_trigger_event(floater_id, EventType.VENTING)):
            
            venting_event = self.handle_venting_event(floater, floater_id)
            events.append(venting_event)
        
        return events
    
    def _update_performance_metrics(self, event_data: EventData) -> None:
        """
        Update performance metrics with event data.
        
        Args:
            event_data: Event data to process
        """
        self.performance_metrics['total_events'] += 1
        
        if event_data.success:
            self.performance_metrics['successful_events'] += 1
            self.success_count += 1
        else:
            self.performance_metrics['failed_events'] += 1
            self.error_count += 1
        
        # Update energy metrics
        self.performance_metrics['total_energy_cost'] += event_data.energy_cost
        
        # Calculate average energy cost
        if self.performance_metrics['total_events'] > 0:
            self.performance_metrics['average_energy_cost'] = (
                self.performance_metrics['total_energy_cost'] / 
                self.performance_metrics['total_events']
            )
        
        # Calculate efficiency (simplified)
        if self.performance_metrics['total_events'] > 0:
            self.performance_metrics['efficiency'] = (
                self.performance_metrics['successful_events'] / 
                self.performance_metrics['total_events']
            )
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Get current performance metrics.
        
        Returns:
            Performance metrics dictionary
        """
        return self.performance_metrics.copy()
    
    def get_energy_summary(self) -> Dict[str, float]:
        """
        Get energy summary.
        
        Returns:
            Energy summary dictionary
        """
        return {
            'total_energy_cost': self.total_energy_cost,
            'total_compression_work': self.total_compression_work,
            'total_thermal_energy': self.total_thermal_energy,
            'energy_efficiency': self.energy_efficiency
        }
    
    def reset(self) -> None:
        """Reset event handler state."""
        self.events.clear()
        self.last_event_time.clear()
        self.event_count = 0
        self.success_count = 0
        self.error_count = 0
        self.total_energy_cost = 0.0
        self.total_compression_work = 0.0
        self.total_thermal_energy = 0.0
        self.energy_efficiency = 0.0
        self.performance_metrics = {
            'total_events': 0,
            'successful_events': 0,
            'failed_events': 0,
            'average_energy_cost': 0.0,
            'total_energy_cost': 0.0,
            'efficiency': 0.0
        }
        self.logger.info("Event handler reset")

