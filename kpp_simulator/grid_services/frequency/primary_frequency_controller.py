"""
Primary Frequency Controller for KPP Simulator
Implements primary frequency response with droop control
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


class FrequencyResponseMode(Enum):
    """Frequency response modes"""
    DROOP_CONTROL = "droop_control"
    ISOCHRONOUS = "isochronous"
    DEAD_BAND = "dead_band"
    LINEAR = "linear"


class ResponseState(Enum):
    """Frequency response states"""
    IDLE = "idle"
    RESPONDING = "responding"
    RECOVERING = "recovering"
    ERROR = "error"


@dataclass
class FrequencyMeasurement:
    """Frequency measurement data"""
    timestamp: datetime
    frequency: float
    rocof: float  # Rate of change of frequency
    deviation: float
    quality: float


@dataclass
class ResponseAction:
    """Frequency response action"""
    timestamp: datetime
    power_adjustment: float
    response_time: float
    accuracy: float
    mode: FrequencyResponseMode


@dataclass
class DroopCharacteristic:
    """Droop characteristic configuration"""
    droop_percentage: float  # 5% droop = 0.05
    dead_band: float  # Hz
    response_time: float  # seconds
    max_power_adjustment: float  # kW
    min_power_adjustment: float  # kW


class PrimaryFrequencyController:
    """
    Primary Frequency Controller for grid frequency regulation
    
    Features:
    - Droop control implementation
    - Fast frequency response (<30 seconds)
    - Dead band control
    - Response time optimization
    - Performance monitoring and analytics
    """
    
    def __init__(self, 
                 physics_engine: PhysicsEngine,
                 electrical_system: IntegratedElectricalSystem,
                 control_system: IntegratedControlSystem):
        """
        Initialize the Primary Frequency Controller
        
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
        self.current_mode = FrequencyResponseMode.DROOP_CONTROL
        self.response_state = ResponseState.IDLE
        
        # Frequency parameters
        self.nominal_frequency = 50.0  # Hz
        self.frequency_tolerance = 0.1  # Hz
        self.max_frequency_deviation = 2.0  # Hz
        
        # Droop characteristics
        self.droop_characteristic = DroopCharacteristic(
            droop_percentage=0.05,  # 5% droop
            dead_band=0.01,  # 10 mHz
            response_time=0.5,  # 500ms
            max_power_adjustment=300.0,  # kW
            min_power_adjustment=-300.0  # kW
        )
        
        # Measurement history
        self.frequency_history: List[FrequencyMeasurement] = []
        self.response_history: List[ResponseAction] = []
        
        # Performance tracking
        self.performance_metrics = {
            'response_time': [],
            'accuracy': [],
            'availability': 1.0,
            'total_responses': 0,
            'successful_responses': 0,
            'failed_responses': 0,
            'average_response_time': 0.0,
            'response_accuracy': 0.0
        }
        
        # Control parameters
        self.last_frequency = self.nominal_frequency
        self.last_response_time = 0.0
        self.current_power_adjustment = 0.0
        self.target_power_adjustment = 0.0
        
        # PID controller for smooth response
        self.pid_kp = 100.0
        self.pid_ki = 10.0
        self.pid_kd = 5.0
        self.pid_integral = 0.0
        self.pid_previous_error = 0.0
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        self.logger.info("Primary Frequency Controller initialized")
    
    def start(self):
        """Start the primary frequency controller"""
        self.is_active = True
        self.response_state = ResponseState.IDLE
        self.logger.info("Primary Frequency Controller started")
    
    def stop(self):
        """Stop the primary frequency controller"""
        self.is_active = False
        self.response_state = ResponseState.IDLE
        self.logger.info("Primary Frequency Controller stopped")
    
    def update(self, dt: float):
        """
        Update the primary frequency controller
        
        Args:
            dt: Time step in seconds
        """
        if not self.is_active:
            return
        
        # Measure current frequency
        current_frequency = self._measure_frequency()
        
        # Calculate frequency deviation
        frequency_deviation = current_frequency - self.nominal_frequency
        
        # Check if response is needed
        if self._should_respond(frequency_deviation):
            self._respond_to_frequency_deviation(frequency_deviation, dt)
        else:
            self._recover_to_normal_operation(dt)
        
        # Update performance metrics
        self._update_performance_metrics(dt)
        
        # Store measurement
        self._store_frequency_measurement(current_frequency, frequency_deviation)
    
    def _measure_frequency(self) -> float:
        """Measure current grid frequency"""
        # Get frequency from electrical system
        electrical_state = self.electrical_system.get_state()
        frequency = electrical_state.get('frequency', self.nominal_frequency)
        
        # Add measurement noise (simulated)
        noise = np.random.normal(0, 0.001)  # 1 mHz noise
        return frequency + noise
    
    def _should_respond(self, frequency_deviation: float) -> bool:
        """Determine if frequency response is needed"""
        # Check dead band
        if abs(frequency_deviation) <= self.droop_characteristic.dead_band:
            return False
        
        # Check if deviation is within acceptable range
        if abs(frequency_deviation) > self.max_frequency_deviation:
            return False
        
        return True
    
    def _respond_to_frequency_deviation(self, frequency_deviation: float, dt: float):
        """Respond to frequency deviation"""
        self.response_state = ResponseState.RESPONDING
        
        # Calculate required power adjustment based on droop characteristic
        if self.current_mode == FrequencyResponseMode.DROOP_CONTROL:
            power_adjustment = self._calculate_droop_response(frequency_deviation)
        elif self.current_mode == FrequencyResponseMode.LINEAR:
            power_adjustment = self._calculate_linear_response(frequency_deviation)
        else:
            power_adjustment = self._calculate_dead_band_response(frequency_deviation)
        
        # Apply PID control for smooth response
        power_adjustment = self._apply_pid_control(power_adjustment, dt)
        
        # Limit power adjustment
        power_adjustment = np.clip(
            power_adjustment,
            self.droop_characteristic.min_power_adjustment,
            self.droop_characteristic.max_power_adjustment
        )
        
        # Apply power adjustment
        self._apply_power_adjustment(power_adjustment)
        
        # Record response action
        self._record_response_action(power_adjustment, frequency_deviation)
        
        self.logger.debug(f"Frequency response: {frequency_deviation:.3f} Hz -> {power_adjustment:.2f} kW")
    
    def _calculate_droop_response(self, frequency_deviation: float) -> float:
        """Calculate power adjustment using droop control"""
        # Droop equation: ΔP = -(Δf / f_nominal) / (droop_percentage / 100)
        power_adjustment = -(frequency_deviation / self.nominal_frequency) / (self.droop_characteristic.droop_percentage)
        
        # Convert to power (assuming base power of 1000 kW)
        base_power = 1000.0  # kW
        return power_adjustment * base_power
    
    def _calculate_linear_response(self, frequency_deviation: float) -> float:
        """Calculate power adjustment using linear response"""
        # Linear response: ΔP = k * Δf
        k = 1000.0  # kW/Hz
        return -k * frequency_deviation
    
    def _calculate_dead_band_response(self, frequency_deviation: float) -> float:
        """Calculate power adjustment with dead band"""
        if abs(frequency_deviation) <= self.droop_characteristic.dead_band:
            return 0.0
        
        # Apply dead band correction
        if frequency_deviation > 0:
            corrected_deviation = frequency_deviation - self.droop_characteristic.dead_band
        else:
            corrected_deviation = frequency_deviation + self.droop_characteristic.dead_band
        
        return self._calculate_droop_response(corrected_deviation)
    
    def _apply_pid_control(self, target_power: float, dt: float) -> float:
        """Apply PID control for smooth power adjustment"""
        error = target_power - self.current_power_adjustment
        
        # Proportional term
        p_term = self.pid_kp * error
        
        # Integral term
        self.pid_integral += error * dt
        i_term = self.pid_ki * self.pid_integral
        
        # Derivative term
        d_term = self.pid_kd * (error - self.pid_previous_error) / dt
        self.pid_previous_error = error
        
        # Calculate output
        output = p_term + i_term + d_term
        
        return output
    
    def _apply_power_adjustment(self, power_adjustment: float):
        """Apply power adjustment to the system"""
        self.current_power_adjustment = power_adjustment
        
        # Notify electrical system of power adjustment
        # This would interface with the electrical system to adjust power output
        self.logger.debug(f"Applied power adjustment: {power_adjustment:.2f} kW")
    
    def _recover_to_normal_operation(self, dt: float):
        """Recover to normal operation when frequency is stable"""
        if self.response_state == ResponseState.RESPONDING:
            self.response_state = ResponseState.RECOVERING
        
        # Gradually reduce power adjustment
        if abs(self.current_power_adjustment) > 1.0:
            recovery_rate = 10.0  # kW/s
            reduction = recovery_rate * dt
            
            if self.current_power_adjustment > 0:
                self.current_power_adjustment = max(0, self.current_power_adjustment - reduction)
            else:
                self.current_power_adjustment = min(0, self.current_power_adjustment + reduction)
        
        else:
            self.current_power_adjustment = 0.0
            self.response_state = ResponseState.IDLE
            self.pid_integral = 0.0  # Reset integral term
    
    def _record_response_action(self, power_adjustment: float, frequency_deviation: float):
        """Record frequency response action"""
        action = ResponseAction(
            timestamp=datetime.now(),
            power_adjustment=power_adjustment,
            response_time=self.droop_characteristic.response_time,
            accuracy=0.95,  # Simulated accuracy
            mode=self.current_mode
        )
        
        self.response_history.append(action)
        
        # Limit history size
        if len(self.response_history) > 1000:
            self.response_history.pop(0)
    
    def _store_frequency_measurement(self, frequency: float, deviation: float):
        """Store frequency measurement"""
        # Calculate rate of change of frequency (ROCOF)
        if len(self.frequency_history) > 0:
            dt = (datetime.now() - self.frequency_history[-1].timestamp).total_seconds()
            if dt > 0:
                rocof = (frequency - self.frequency_history[-1].frequency) / dt
            else:
                rocof = 0.0
        else:
            rocof = 0.0
        
        measurement = FrequencyMeasurement(
            timestamp=datetime.now(),
            frequency=frequency,
            rocof=rocof,
            deviation=deviation,
            quality=0.98  # Simulated quality
        )
        
        self.frequency_history.append(measurement)
        
        # Limit history size
        if len(self.frequency_history) > 10000:
            self.frequency_history.pop(0)
    
    def _update_performance_metrics(self, dt: float):
        """Update performance metrics"""
        # Update response time
        if self.response_state == ResponseState.RESPONDING:
            self.last_response_time += dt
        
        # Calculate average response time
        if len(self.response_history) > 0:
            response_times = [action.response_time for action in self.response_history[-100:]]
            self.performance_metrics['average_response_time'] = np.mean(response_times)
        
        # Calculate response accuracy
        if len(self.response_history) > 0:
            accuracies = [action.accuracy for action in self.response_history[-100:]]
            self.performance_metrics['response_accuracy'] = np.mean(accuracies)
    
    def set_droop_characteristic(self, droop_percentage: float, dead_band: float, response_time: float):
        """Set droop characteristic parameters"""
        self.droop_characteristic.droop_percentage = droop_percentage
        self.droop_characteristic.dead_band = dead_band
        self.droop_characteristic.response_time = response_time
        
        self.logger.info(f"Droop characteristic updated: {droop_percentage*100:.1f}% droop, {dead_band*1000:.1f} mHz dead band")
    
    def set_response_mode(self, mode: FrequencyResponseMode):
        """Set frequency response mode"""
        self.current_mode = mode
        self.logger.info(f"Response mode set to: {mode.value}")
    
    def set_pid_parameters(self, kp: float, ki: float, kd: float):
        """Set PID controller parameters"""
        self.pid_kp = kp
        self.pid_ki = ki
        self.pid_kd = kd
        self.pid_integral = 0.0  # Reset integral term
        
        self.logger.info(f"PID parameters updated: Kp={kp}, Ki={ki}, Kd={kd}")
    
    def get_current_status(self) -> Dict[str, Any]:
        """Get current controller status"""
        return {
            'is_active': self.is_active,
            'response_state': self.response_state.value,
            'current_mode': self.current_mode.value,
            'current_frequency': self._measure_frequency(),
            'frequency_deviation': self._measure_frequency() - self.nominal_frequency,
            'current_power_adjustment': self.current_power_adjustment,
            'response_time': self.last_response_time
        }
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics"""
        return self.performance_metrics.copy()
    
    def get_frequency_history(self, duration: timedelta = timedelta(hours=1)) -> List[FrequencyMeasurement]:
        """Get frequency history for specified duration"""
        cutoff_time = datetime.now() - duration
        return [m for m in self.frequency_history if m.timestamp >= cutoff_time]
    
    def get_response_history(self, duration: timedelta = timedelta(hours=1)) -> List[ResponseAction]:
        """Get response history for specified duration"""
        cutoff_time = datetime.now() - duration
        return [r for r in self.response_history if r.timestamp >= cutoff_time]
    
    def reset_performance_metrics(self):
        """Reset performance metrics"""
        self.performance_metrics = {
            'response_time': [],
            'accuracy': [],
            'availability': 1.0,
            'total_responses': 0,
            'successful_responses': 0,
            'failed_responses': 0,
            'average_response_time': 0.0,
            'response_accuracy': 0.0
        }
        
        self.logger.info("Performance metrics reset")
    
    def clear_history(self):
        """Clear measurement and response history"""
        self.frequency_history.clear()
        self.response_history.clear()
        self.logger.info("History cleared") 