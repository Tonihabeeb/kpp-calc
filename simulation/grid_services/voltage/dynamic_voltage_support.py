"""
Dynamic Voltage Support

Provides fast dynamic voltage support for grid stability through rapid
reactive power injection during voltage transients and disturbances.

Response time: <100ms for voltage events
Voltage change threshold: >2% voltage deviation
Maximum reactive power: ±40% of rated power
Hold time: 5-30 seconds after event
Recovery time: <10 seconds
"""

import time
import math
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
from collections import deque


@dataclass
class DynamicVoltageSupportConfig:
    """Configuration for Dynamic Voltage Support"""
    reactive_capacity: float = 0.40              # ±40% of rated power
    voltage_threshold: float = 0.02              # 2% voltage change threshold
    response_time_ms: float = 100.0              # 100ms response time
    hold_time_s: float = 10.0                    # 10 seconds hold time
    recovery_time_s: float = 5.0                 # 5 seconds recovery time
    voltage_rate_threshold: float = 0.10         # 10%/second voltage rate threshold
    enable_support: bool = True
    priority_level: int = 1                      # Highest priority
    min_activation_voltage: float = 0.90         # Minimum voltage for activation
    max_activation_voltage: float = 1.10         # Maximum voltage for activation
    
    def validate(self):
        """Validate configuration parameters"""
        assert 0.30 <= self.reactive_capacity <= 0.50, "Reactive capacity must be 30-50%"
        assert 0.01 <= self.voltage_threshold <= 0.05, "Voltage threshold must be 1-5%"
        assert 50.0 <= self.response_time_ms <= 500.0, "Response time must be 50-500ms"
        assert 1.0 <= self.hold_time_s <= 60.0, "Hold time must be 1-60 seconds"


class VoltageEvent:
    """Voltage event data structure"""
    def __init__(self, event_type: str, magnitude: float, timestamp: float):
        self.event_type = event_type  # 'sag', 'swell', 'transient'
        self.magnitude = magnitude    # Magnitude of voltage change (p.u.)
        self.timestamp = timestamp    # Event start time
        self.duration = 0.0          # Event duration (updated during event)
        self.resolved = False        # Whether event has been resolved


class DynamicVoltageSupport:
    """
    Dynamic Voltage Support for fast reactive power response to voltage events.
    
    Implements grid stability support with:
    - Fast voltage event detection
    - Rapid reactive power injection/absorption
    - Event classification and tracking
    - Coordinated recovery after events
    - Performance monitoring and validation
    """
    
    def __init__(self, config: Optional[DynamicVoltageSupportConfig] = None):
        self.config = config or DynamicVoltageSupportConfig()
        self.config.validate()
        
        # State variables
        self.measured_voltage = 1.0         # Current voltage measurement (p.u.)
        self.baseline_voltage = 1.0         # Baseline voltage before event (p.u.)
        self.reactive_power_output = 0.0    # Current reactive power output (p.u.)
        self.support_active = False
        self.event_detected = False
        
        # Event tracking
        self.active_events: List[VoltageEvent] = []
        self.event_history = deque(maxlen=100)  # Store last 100 events
        self.event_start_time = 0.0
        self.hold_start_time = 0.0
        self.in_hold_phase = False
        self.in_recovery_phase = False
        
        # Voltage monitoring
        self.voltage_history = deque(maxlen=100)  # Store last 10 seconds at 10Hz
        self.last_voltage = 1.0
        self.voltage_rate = 0.0
        
        # Performance metrics
        self.events_detected = 0
        self.total_support_time = 0.0
        self.successful_supports = 0
        self.last_update_time = time.time()
        
    def update(self, voltage_pu: float, dt: float, rated_power: float) -> Dict[str, Any]:
        """
        Update dynamic voltage support with current voltage measurement.
        
        Args:
            voltage_pu: Measured voltage (p.u.)
            dt: Time step (seconds)
            rated_power: System rated power (MW)
            
        Returns:
            Dictionary containing control commands and status
        """
        current_time = time.time()
        
        if not self.config.enable_support:
            return self._create_response_dict(0.0, "Dynamic voltage support disabled", rated_power)
        
        # Input validation
        if voltage_pu < 0.5 or voltage_pu > 1.5:
            return self._create_response_dict(0.0, "Invalid voltage measurement", rated_power)
        
        # Store voltage measurement
        self.measured_voltage = voltage_pu
        
        # Calculate voltage rate of change
        if len(self.voltage_history) > 0:
            self.voltage_rate = (voltage_pu - self.last_voltage) / dt
        else:
            self.voltage_rate = 0.0
        
        self.voltage_history.append({
            'voltage': voltage_pu,
            'timestamp': current_time,
            'rate': self.voltage_rate
        })
        
        # Event detection and classification
        event_detected, event_type, event_magnitude = self._detect_voltage_event(voltage_pu, dt)
        
        # State machine for dynamic voltage support
        if not self.event_detected and event_detected:
            # New event detected
            self._start_voltage_event(event_type, event_magnitude, current_time)
            
        elif self.event_detected:
            # Update ongoing event
            self._update_voltage_event(voltage_pu, current_time, dt)
        
        # Calculate reactive power response
        reactive_power_cmd = self._calculate_reactive_power_response(voltage_pu, current_time)
        
        # Apply rate limiting based on response time
        max_rate = self.config.reactive_capacity / (self.config.response_time_ms / 1000.0)
        rate_change = reactive_power_cmd - self.reactive_power_output
        
        if abs(rate_change) > max_rate * dt:
            rate_change = math.copysign(max_rate * dt, rate_change)
        
        self.reactive_power_output += rate_change
        
        # Determine status
        status = self._get_support_status()
        
        # Update performance metrics
        if self.support_active:
            self.total_support_time += dt
        
        self.last_voltage = voltage_pu
        self.last_update_time = current_time
        
        return self._create_response_dict(self.reactive_power_output, status, rated_power)
    
    def _detect_voltage_event(self, voltage_pu: float, dt: float) -> Tuple[bool, str, float]:
        """Detect voltage events based on magnitude and rate thresholds"""
        if len(self.voltage_history) < 3:  # Need some history for rate calculation
            return False, "", 0.0
        
        # Calculate voltage deviation from baseline
        voltage_deviation = abs(voltage_pu - self.baseline_voltage)
        
        # Check magnitude threshold
        magnitude_event = voltage_deviation > self.config.voltage_threshold
        
        # Check rate threshold
        rate_event = abs(self.voltage_rate) > self.config.voltage_rate_threshold
        
        # Classify event type
        if magnitude_event or rate_event:
            if voltage_pu < self.baseline_voltage - self.config.voltage_threshold:
                event_type = "sag"
                event_magnitude = self.baseline_voltage - voltage_pu
            elif voltage_pu > self.baseline_voltage + self.config.voltage_threshold:
                event_type = "swell" 
                event_magnitude = voltage_pu - self.baseline_voltage
            elif rate_event:
                event_type = "transient"
                event_magnitude = abs(self.voltage_rate) * dt
            else:
                return False, "", 0.0
            
            return True, event_type, event_magnitude
        
        return False, "", 0.0
    
    def _start_voltage_event(self, event_type: str, magnitude: float, timestamp: float):
        """Start tracking a new voltage event"""
        self.event_detected = True
        self.support_active = True
        self.event_start_time = timestamp
        self.baseline_voltage = self.measured_voltage if not self.active_events else self.baseline_voltage
        
        # Create new event
        event = VoltageEvent(event_type, magnitude, timestamp)
        self.active_events.append(event)
        self.events_detected += 1
        
        # Reset phases
        self.in_hold_phase = False
        self.in_recovery_phase = False
    
    def _update_voltage_event(self, voltage_pu: float, current_time: float, dt: float):
        """Update ongoing voltage event"""
        if not self.active_events:
            return
        
        # Check if voltage has returned to normal
        voltage_deviation = abs(voltage_pu - self.baseline_voltage)
        voltage_stable = voltage_deviation < (self.config.voltage_threshold / 2.0)
        rate_stable = abs(self.voltage_rate) < (self.config.voltage_rate_threshold / 2.0)
        
        if voltage_stable and rate_stable and not self.in_hold_phase and not self.in_recovery_phase:
            # Voltage has stabilized, enter hold phase
            self.in_hold_phase = True
            self.hold_start_time = current_time
        
        elif self.in_hold_phase:
            # Check if hold time has elapsed
            if current_time - self.hold_start_time >= self.config.hold_time_s:
                self.in_hold_phase = False
                self.in_recovery_phase = True
                self.hold_start_time = current_time  # Reuse for recovery timing
        
        elif self.in_recovery_phase:
            # Check if recovery time has elapsed
            if current_time - self.hold_start_time >= self.config.recovery_time_s:
                self._end_voltage_event(current_time)
        
        # Update event duration
        for event in self.active_events:
            event.duration = current_time - event.timestamp
    
    def _end_voltage_event(self, timestamp: float):
        """End voltage event and clean up"""
        # Mark events as resolved and move to history
        for event in self.active_events:
            event.resolved = True
            self.event_history.append(event)
        
        self.active_events.clear()
        self.event_detected = False
        self.support_active = False
        self.in_hold_phase = False
        self.in_recovery_phase = False
        self.successful_supports += 1
        
        # Update baseline voltage
        self.baseline_voltage = self.measured_voltage
    
    def _calculate_reactive_power_response(self, voltage_pu: float, current_time: float) -> float:
        """Calculate required reactive power response"""
        if not self.support_active:
            return 0.0
        
        if self.in_recovery_phase:
            # Gradual recovery to zero
            recovery_progress = (current_time - self.hold_start_time) / self.config.recovery_time_s
            return self.reactive_power_output * (1.0 - recovery_progress)
        
        # Calculate response magnitude based on voltage deviation
        voltage_deviation = voltage_pu - self.baseline_voltage
        
        # Proportional response with full capacity at threshold
        response_gain = self.config.reactive_capacity / self.config.voltage_threshold
        reactive_power_cmd = -voltage_deviation * response_gain  # Negative sign for voltage support
        
        # Limit to capacity
        reactive_power_cmd = max(-self.config.reactive_capacity,
                               min(self.config.reactive_capacity, reactive_power_cmd))
        
        return reactive_power_cmd
    
    def _get_support_status(self) -> str:
        """Get current support status description"""
        if not self.support_active:
            return "No voltage events"
        
        if self.in_recovery_phase:
            return "Recovery phase"
        elif self.in_hold_phase:
            return "Hold phase"
        elif self.active_events:
            event_types = [event.event_type for event in self.active_events]
            return f"Active support - {', '.join(set(event_types))}"
        else:
            return "Dynamic voltage support active"
    
    def _create_response_dict(self, reactive_power_pu: float, status: str, rated_power: float) -> Dict[str, Any]:
        """Create standardized response dictionary"""
        return {
            'reactive_power_pu': reactive_power_pu,
            'reactive_power_mvar': reactive_power_pu * rated_power,
            'measured_voltage': self.measured_voltage,
            'baseline_voltage': self.baseline_voltage,
            'voltage_deviation': self.measured_voltage - self.baseline_voltage,
            'voltage_rate': self.voltage_rate,
            'status': status,
            'service_type': 'dynamic_voltage_support',
            'support_active': self.support_active,
            'event_detected': self.event_detected,
            'active_events': len(self.active_events),
            'timestamp': self.last_update_time
        }
    
    def get_performance_metrics(self) -> Dict[str, float]:
        """Get performance metrics for monitoring and optimization"""
        # Calculate average event duration
        if len(self.event_history) > 0:
            avg_event_duration = sum(event.duration for event in self.event_history) / len(self.event_history)
            max_event_magnitude = max(event.magnitude for event in self.event_history)
        else:
            avg_event_duration = 0.0
            max_event_magnitude = 0.0
        
        # Calculate success rate
        success_rate = (self.successful_supports / max(1, self.events_detected)) * 100.0
        
        # Calculate reactive power utilization
        max_reactive_utilization = abs(self.reactive_power_output) / self.config.reactive_capacity
        
        return {
            'events_detected': self.events_detected,
            'successful_supports': self.successful_supports,
            'success_rate_percent': success_rate,
            'average_event_duration': avg_event_duration,
            'max_event_magnitude': max_event_magnitude,
            'total_support_time': self.total_support_time,
            'max_reactive_utilization': max_reactive_utilization,
            'current_voltage': self.measured_voltage,
            'current_reactive_power': self.reactive_power_output,
            'reactive_capacity': self.config.reactive_capacity
        }
    
    def reset(self):
        """Reset support system state"""
        self.measured_voltage = 1.0
        self.baseline_voltage = 1.0
        self.reactive_power_output = 0.0
        self.support_active = False
        self.event_detected = False
        self.active_events.clear()
        self.event_history.clear()
        self.voltage_history.clear()
        self.in_hold_phase = False
        self.in_recovery_phase = False
        self.events_detected = 0
        self.total_support_time = 0.0
        self.successful_supports = 0
        self.last_voltage = 1.0
        self.voltage_rate = 0.0
        self.last_update_time = time.time()
    
    def update_configuration(self, new_config: DynamicVoltageSupportConfig):
        """Update support system configuration"""
        new_config.validate()
        self.config = new_config
    
    def is_supporting(self) -> bool:
        """Check if system is actively providing voltage support"""
        return self.support_active


def create_standard_dynamic_voltage_support() -> DynamicVoltageSupport:
    """Create a standard dynamic voltage support system with typical settings"""
    config = DynamicVoltageSupportConfig(
        reactive_capacity=0.40,           # 40% reactive power capacity
        voltage_threshold=0.02,           # 2% voltage threshold
        response_time_ms=100.0,           # 100ms response time
        hold_time_s=10.0,                 # 10 seconds hold time
        recovery_time_s=5.0,              # 5 seconds recovery time
        voltage_rate_threshold=0.10,      # 10%/second rate threshold
        enable_support=True,
        priority_level=1,                 # Highest priority
        min_activation_voltage=0.90,      # 90% minimum
        max_activation_voltage=1.10       # 110% maximum
    )
    return DynamicVoltageSupport(config)
