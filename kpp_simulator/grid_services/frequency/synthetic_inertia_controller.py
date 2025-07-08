"""
Synthetic Inertia Controller for KPP Simulator
Implements synthetic inertia with ROCOF detection and fast response
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


class InertiaMode(Enum):
    """Synthetic inertia modes"""
    ACTIVE = "active"
    STANDBY = "standby"
    DISABLED = "disabled"
    EMERGENCY = "emergency"


class ROCOFThreshold(Enum):
    """ROCOF threshold levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ROCOFEvent:
    """ROCOF event data"""
    timestamp: datetime
    rocof_value: float
    threshold_level: ROCOFThreshold
    frequency_deviation: float
    response_triggered: bool
    response_time: float


@dataclass
class InertiaResponse:
    """Synthetic inertia response data"""
    timestamp: datetime
    power_response: float
    response_time: float
    inertia_constant: float
    rocof_value: float
    frequency_deviation: float
    energy_delivered: float


@dataclass
class InertiaConfiguration:
    """Synthetic inertia configuration"""
    inertia_constant: float  # seconds
    rocof_threshold: float  # Hz/s
    response_time: float  # seconds
    max_power_response: float  # kW
    energy_capacity: float  # kWh
    recovery_time: float  # seconds


class SyntheticInertiaController:
    """
    Synthetic Inertia Controller for fast frequency response
    
    Features:
    - ROCOF detection and classification
    - Virtual inertia emulation
    - Fast response (<500ms)
    - Configurable inertia constant
    - Frequency transient response
    - Energy management and recovery
    """
    
    def __init__(self, 
                 physics_engine: PhysicsEngine,
                 electrical_system: IntegratedElectricalSystem,
                 control_system: IntegratedControlSystem):
        """
        Initialize the Synthetic Inertia Controller
        
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
        self.current_mode = InertiaMode.STANDBY
        self.is_responding = False
        
        # Inertia configuration
        self.config = InertiaConfiguration(
            inertia_constant=5.0,  # seconds
            rocof_threshold=0.1,  # Hz/s
            response_time=0.05,  # 50ms
            max_power_response=100.0,  # kW
            energy_capacity=50.0,  # kWh
            recovery_time=10.0  # seconds
        )
        
        # ROCOF detection
        self.frequency_history: List[Tuple[datetime, float]] = []
        self.rocof_history: List[float] = []
        self.rocof_events: List[ROCOFEvent] = []
        
        # Response tracking
        self.inertia_responses: List[InertiaResponse] = []
        self.current_power_response = 0.0
        self.energy_delivered = 0.0
        self.last_response_time = 0.0
        
        # Performance tracking
        self.performance_metrics = {
            'total_rocof_events': 0,
            'successful_responses': 0,
            'average_response_time': 0.0,
            'max_power_response': 0.0,
            'total_energy_delivered': 0.0,
            'availability': 1.0,
            'response_accuracy': 0.0
        }
        
        # ROCOF thresholds
        self.rocof_thresholds = {
            ROCOFThreshold.LOW: 0.05,      # Hz/s
            ROCOFThreshold.MEDIUM: 0.1,
            ROCOFThreshold.HIGH: 0.2,
            ROCOFThreshold.CRITICAL: 0.5
        }
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        self.logger.info("Synthetic Inertia Controller initialized")
    
    def start(self):
        """Start the synthetic inertia controller"""
        self.is_active = True
        self.current_mode = InertiaMode.ACTIVE
        self.logger.info("Synthetic Inertia Controller started")
    
    def stop(self):
        """Stop the synthetic inertia controller"""
        self.is_active = False
        self.current_mode = InertiaMode.DISABLED
        self.is_responding = False
        self.logger.info("Synthetic Inertia Controller stopped")
    
    def update(self, dt: float):
        """
        Update the synthetic inertia controller
        
        Args:
            dt: Time step in seconds
        """
        if not self.is_active:
            return
        
        # Measure current frequency
        current_frequency = self._measure_frequency()
        current_time = datetime.now()
        
        # Store frequency measurement
        self.frequency_history.append((current_time, current_frequency))
        
        # Limit history size
        if len(self.frequency_history) > 1000:
            self.frequency_history.pop(0)
        
        # Calculate ROCOF
        rocof = self._calculate_rocof()
        if rocof is not None:
            self.rocof_history.append(rocof)
            
            # Limit ROCOF history size
            if len(self.rocof_history) > 1000:
                self.rocof_history.pop(0)
            
            # Check for ROCOF events
            self._check_rocof_events(rocof, current_frequency, current_time)
        
        # Update response if active
        if self.is_responding:
            self._update_inertia_response(dt)
        
        # Update performance metrics
        self._update_performance_metrics(dt)
    
    def _measure_frequency(self) -> float:
        """Measure current grid frequency"""
        # Get frequency from electrical system
        electrical_state = self.electrical_system.get_state()
        frequency = electrical_state.get('frequency', 50.0)
        
        # Add measurement noise (simulated)
        noise = np.random.normal(0, 0.001)  # 1 mHz noise
        return frequency + noise
    
    def _calculate_rocof(self) -> Optional[float]:
        """Calculate rate of change of frequency (ROCOF)"""
        if len(self.frequency_history) < 2:
            return None
        
        # Use last two measurements for ROCOF calculation
        current_time, current_freq = self.frequency_history[-1]
        previous_time, previous_freq = self.frequency_history[-2]
        
        time_diff = (current_time - previous_time).total_seconds()
        if time_diff > 0:
            rocof = (current_freq - previous_freq) / time_diff
            return rocof
        
        return None
    
    def _check_rocof_events(self, rocof: float, frequency: float, timestamp: datetime):
        """Check for ROCOF events and trigger responses"""
        # Determine threshold level
        threshold_level = self._get_rocof_threshold_level(rocof)
        
        # Check if ROCOF exceeds threshold
        if abs(rocof) > self.config.rocof_threshold:
            # Create ROCOF event
            event = ROCOFEvent(
                timestamp=timestamp,
                rocof_value=rocof,
                threshold_level=threshold_level,
                frequency_deviation=frequency - 50.0,
                response_triggered=False,
                response_time=0.0
            )
            
            self.rocof_events.append(event)
            self.performance_metrics['total_rocof_events'] += 1
            
            # Trigger inertia response
            if not self.is_responding:
                self._trigger_inertia_response(rocof, frequency, timestamp)
                event.response_triggered = True
                event.response_time = self.config.response_time
            
            self.logger.warning(f"ROCOF event detected: {rocof:.3f} Hz/s - {threshold_level.value}")
    
    def _get_rocof_threshold_level(self, rocof: float) -> ROCOFThreshold:
        """Get ROCOF threshold level"""
        abs_rocof = abs(rocof)
        
        if abs_rocof >= self.rocof_thresholds[ROCOFThreshold.CRITICAL]:
            return ROCOFThreshold.CRITICAL
        elif abs_rocof >= self.rocof_thresholds[ROCOFThreshold.HIGH]:
            return ROCOFThreshold.HIGH
        elif abs_rocof >= self.rocof_thresholds[ROCOFThreshold.MEDIUM]:
            return ROCOFThreshold.MEDIUM
        else:
            return ROCOFThreshold.LOW
    
    def _trigger_inertia_response(self, rocof: float, frequency: float, timestamp: datetime):
        """Trigger synthetic inertia response"""
        self.is_responding = True
        self.last_response_time = timestamp
        
        # Calculate power response based on inertia constant
        # P = H * f_nominal * df/dt
        power_response = self.config.inertia_constant * 50.0 * rocof
        
        # Limit power response
        power_response = np.clip(power_response, -self.config.max_power_response, self.config.max_power_response)
        
        self.current_power_response = power_response
        
        # Apply power response
        self._apply_power_response(power_response)
        
        # Record response
        response = InertiaResponse(
            timestamp=timestamp,
            power_response=power_response,
            response_time=self.config.response_time,
            inertia_constant=self.config.inertia_constant,
            rocof_value=rocof,
            frequency_deviation=frequency - 50.0,
            energy_delivered=0.0
        )
        
        self.inertia_responses.append(response)
        self.performance_metrics['successful_responses'] += 1
        
        self.logger.info(f"Inertia response triggered: {power_response:.2f} kW - ROCOF: {rocof:.3f} Hz/s")
    
    def _update_inertia_response(self, dt: float):
        """Update ongoing inertia response"""
        # Calculate energy delivered
        energy_delivered = abs(self.current_power_response) * dt / 3600  # kWh
        self.energy_delivered += energy_delivered
        self.performance_metrics['total_energy_delivered'] += energy_delivered
        
        # Update latest response
        if self.inertia_responses:
            self.inertia_responses[-1].energy_delivered += energy_delivered
        
        # Check if response should end
        response_duration = (datetime.now() - self.last_response_time).total_seconds()
        if response_duration >= self.config.recovery_time:
            self._end_inertia_response()
    
    def _end_inertia_response(self):
        """End inertia response and recover"""
        self.is_responding = False
        self.current_power_response = 0.0
        
        # Apply zero power response
        self._apply_power_response(0.0)
        
        self.logger.info("Inertia response ended")
    
    def _apply_power_response(self, power_response: float):
        """Apply power response to the system"""
        # Notify electrical system of power response
        # This would interface with the electrical system to adjust power output
        self.logger.debug(f"Applied inertia power response: {power_response:.2f} kW")
    
    def _update_performance_metrics(self, dt: float):
        """Update performance metrics"""
        # Update average response time
        if self.inertia_responses:
            response_times = [r.response_time for r in self.inertia_responses[-100:]]
            self.performance_metrics['average_response_time'] = np.mean(response_times)
        
        # Update max power response
        if self.inertia_responses:
            max_power = max([abs(r.power_response) for r in self.inertia_responses])
            self.performance_metrics['max_power_response'] = max_power
        
        # Update availability
        if self.performance_metrics['total_rocof_events'] > 0:
            self.performance_metrics['availability'] = (
                self.performance_metrics['successful_responses'] / 
                self.performance_metrics['total_rocof_events']
            )
        
        # Update response accuracy
        if self.inertia_responses:
            # Calculate accuracy based on response time vs target
            accuracies = []
            for response in self.inertia_responses[-100:]:
                if response.response_time <= self.config.response_time:
                    accuracies.append(1.0)
                else:
                    accuracies.append(self.config.response_time / response.response_time)
            
            if accuracies:
                self.performance_metrics['response_accuracy'] = np.mean(accuracies)
    
    def set_inertia_constant(self, inertia_constant: float):
        """Set synthetic inertia constant"""
        self.config.inertia_constant = inertia_constant
        self.logger.info(f"Inertia constant set to: {inertia_constant:.1f} seconds")
    
    def set_rocof_threshold(self, threshold: float):
        """Set ROCOF threshold"""
        self.config.rocof_threshold = threshold
        self.logger.info(f"ROCOF threshold set to: {threshold:.3f} Hz/s")
    
    def set_response_time(self, response_time: float):
        """Set response time target"""
        self.config.response_time = response_time
        self.logger.info(f"Response time set to: {response_time:.3f} seconds")
    
    def set_max_power_response(self, max_power: float):
        """Set maximum power response"""
        self.config.max_power_response = max_power
        self.logger.info(f"Maximum power response set to: {max_power:.1f} kW")
    
    def set_energy_capacity(self, energy_capacity: float):
        """Set energy capacity"""
        self.config.energy_capacity = energy_capacity
        self.logger.info(f"Energy capacity set to: {energy_capacity:.1f} kWh")
    
    def set_recovery_time(self, recovery_time: float):
        """Set recovery time"""
        self.config.recovery_time = recovery_time
        self.logger.info(f"Recovery time set to: {recovery_time:.1f} seconds")
    
    def get_current_status(self) -> Dict[str, Any]:
        """Get current controller status"""
        return {
            'is_active': self.is_active,
            'current_mode': self.current_mode.value,
            'is_responding': self.is_responding,
            'current_power_response': self.current_power_response,
            'energy_delivered': self.energy_delivered,
            'current_frequency': self._measure_frequency(),
            'current_rocof': self._calculate_rocof() or 0.0
        }
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics"""
        return self.performance_metrics.copy()
    
    def get_rocof_events(self, duration: timedelta = timedelta(hours=1)) -> List[ROCOFEvent]:
        """Get ROCOF events for specified duration"""
        cutoff_time = datetime.now() - duration
        return [e for e in self.rocof_events if e.timestamp >= cutoff_time]
    
    def get_inertia_responses(self, duration: timedelta = timedelta(hours=1)) -> List[InertiaResponse]:
        """Get inertia responses for specified duration"""
        cutoff_time = datetime.now() - duration
        return [r for r in self.inertia_responses if r.timestamp >= cutoff_time]
    
    def get_frequency_history(self, duration: timedelta = timedelta(minutes=5)) -> List[Tuple[datetime, float]]:
        """Get frequency history for specified duration"""
        cutoff_time = datetime.now() - duration
        return [(t, f) for t, f in self.frequency_history if t >= cutoff_time]
    
    def get_rocof_history(self, duration: timedelta = timedelta(minutes=5)) -> List[float]:
        """Get ROCOF history for specified duration"""
        cutoff_time = datetime.now() - duration
        cutoff_index = len(self.frequency_history) - len([t for t, _ in self.frequency_history if t >= cutoff_time])
        return self.rocof_history[cutoff_index:] if cutoff_index < len(self.rocof_history) else []
    
    def clear_history(self):
        """Clear all history data"""
        self.frequency_history.clear()
        self.rocof_history.clear()
        self.rocof_events.clear()
        self.inertia_responses.clear()
        self.logger.info("History cleared")
    
    def reset_performance_metrics(self):
        """Reset performance metrics"""
        self.performance_metrics = {
            'total_rocof_events': 0,
            'successful_responses': 0,
            'average_response_time': 0.0,
            'max_power_response': 0.0,
            'total_energy_delivered': 0.0,
            'availability': 1.0,
            'response_accuracy': 0.0
        }
        
        self.energy_delivered = 0.0
        self.logger.info("Performance metrics reset") 