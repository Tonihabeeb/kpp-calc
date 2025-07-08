"""
Voltage Regulator for KPP Simulator
Implements automatic voltage regulation and voltage support
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


class VoltageControlMode(Enum):
    """Voltage control modes"""
    AUTOMATIC = "automatic"
    MANUAL = "manual"
    DROOP = "droop"
    DEAD_BAND = "dead_band"
    DISABLED = "disabled"


class VoltageStatus(Enum):
    """Voltage status states"""
    NORMAL = "normal"
    HIGH = "high"
    LOW = "low"
    CRITICAL_HIGH = "critical_high"
    CRITICAL_LOW = "critical_low"
    ERROR = "error"


@dataclass
class VoltageMeasurement:
    """Voltage measurement data"""
    timestamp: datetime
    voltage: float
    reactive_power: float
    power_factor: float
    quality: float


@dataclass
class VoltageAction:
    """Voltage control action"""
    timestamp: datetime
    voltage_adjustment: float
    reactive_power_adjustment: float
    control_mode: VoltageControlMode
    response_time: float
    accuracy: float


@dataclass
class VoltageConfiguration:
    """Voltage regulation configuration"""
    nominal_voltage: float  # V
    voltage_range: Tuple[float, float]  # (min, max) as percentage
    dead_band: float  # percentage
    droop_characteristic: float  # percentage
    response_time: float  # seconds
    max_reactive_power: float  # kVAR
    min_reactive_power: float  # kVAR


class VoltageRegulator:
    """
    Voltage Regulator for automatic voltage regulation
    
    Features:
    - Automatic voltage regulation (AVR)
    - Droop control implementation
    - Voltage dead band control
    - Response time optimization
    - Stability enhancement
    - Reactive power management
    """
    
    def __init__(self, 
                 physics_engine: PhysicsEngine,
                 electrical_system: IntegratedElectricalSystem,
                 control_system: IntegratedControlSystem):
        """
        Initialize the Voltage Regulator
        
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
        self.current_mode = VoltageControlMode.AUTOMATIC
        self.voltage_status = VoltageStatus.NORMAL
        
        # Voltage configuration
        self.config = VoltageConfiguration(
            nominal_voltage=400.0,  # V
            voltage_range=(0.95, 1.05),  # 95% to 105%
            dead_band=0.02,  # 2%
            droop_characteristic=0.03,  # 3%
            response_time=1.0,  # seconds
            max_reactive_power=200.0,  # kVAR
            min_reactive_power=-200.0  # kVAR
        )
        
        # Measurement tracking
        self.voltage_history: List[VoltageMeasurement] = []
        self.voltage_actions: List[VoltageAction] = []
        
        # Control parameters
        self.current_voltage = self.config.nominal_voltage
        self.current_reactive_power = 0.0
        self.target_voltage = self.config.nominal_voltage
        self.voltage_adjustment = 0.0
        self.reactive_power_adjustment = 0.0
        
        # Performance tracking
        self.performance_metrics = {
            'voltage_stability': 1.0,
            'response_time': 0.0,
            'accuracy': 0.0,
            'availability': 1.0,
            'total_adjustments': 0,
            'successful_adjustments': 0,
            'average_response_time': 0.0,
            'voltage_violations': 0
        }
        
        # PID controller for voltage control
        self.pid_kp = 10.0
        self.pid_ki = 2.0
        self.pid_kd = 1.0
        self.pid_integral = 0.0
        self.pid_previous_error = 0.0
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        self.logger.info("Voltage Regulator initialized")
    
    def start(self):
        """Start the voltage regulator"""
        self.is_active = True
        self.current_mode = VoltageControlMode.AUTOMATIC
        self.logger.info("Voltage Regulator started")
    
    def stop(self):
        """Stop the voltage regulator"""
        self.is_active = False
        self.current_mode = VoltageControlMode.DISABLED
        self.logger.info("Voltage Regulator stopped")
    
    def update(self, dt: float):
        """
        Update the voltage regulator
        
        Args:
            dt: Time step in seconds
        """
        if not self.is_active:
            return
        
        # Measure current voltage
        self._measure_voltage()
        
        # Determine voltage status
        self._determine_voltage_status()
        
        # Execute voltage control based on mode
        if self.current_mode == VoltageControlMode.AUTOMATIC:
            self._execute_automatic_voltage_control(dt)
        elif self.current_mode == VoltageControlMode.DROOP:
            self._execute_droop_voltage_control(dt)
        elif self.current_mode == VoltageControlMode.DEAD_BAND:
            self._execute_dead_band_voltage_control(dt)
        
        # Update performance metrics
        self._update_performance_metrics(dt)
        
        # Store voltage measurement
        self._store_voltage_measurement()
    
    def _measure_voltage(self):
        """Measure current voltage and related parameters"""
        # Get electrical state
        electrical_state = self.electrical_system.get_state()
        
        # Extract voltage and reactive power
        self.current_voltage = electrical_state.get('voltage', self.config.nominal_voltage)
        self.current_reactive_power = electrical_state.get('reactive_power', 0.0)
        
        # Calculate power factor
        active_power = electrical_state.get('active_power', 1000.0)
        apparent_power = np.sqrt(active_power**2 + self.current_reactive_power**2)
        power_factor = active_power / apparent_power if apparent_power > 0 else 1.0
        
        # Add measurement noise (simulated)
        voltage_noise = np.random.normal(0, 0.5)  # 0.5V noise
        self.current_voltage += voltage_noise
    
    def _determine_voltage_status(self):
        """Determine current voltage status"""
        voltage_percentage = self.current_voltage / self.config.nominal_voltage
        
        if voltage_percentage > 1.10:  # >110%
            self.voltage_status = VoltageStatus.CRITICAL_HIGH
        elif voltage_percentage > 1.05:  # >105%
            self.voltage_status = VoltageStatus.HIGH
        elif voltage_percentage < 0.90:  # <90%
            self.voltage_status = VoltageStatus.CRITICAL_LOW
        elif voltage_percentage < 0.95:  # <95%
            self.voltage_status = VoltageStatus.LOW
        else:
            self.voltage_status = VoltageStatus.NORMAL
    
    def _execute_automatic_voltage_control(self, dt: float):
        """Execute automatic voltage regulation"""
        # Calculate voltage error
        voltage_error = self.target_voltage - self.current_voltage
        
        # Check dead band
        dead_band_threshold = self.config.nominal_voltage * self.config.dead_band
        if abs(voltage_error) <= dead_band_threshold:
            return  # No action needed
        
        # Apply PID control
        voltage_adjustment = self._apply_pid_control(voltage_error, dt)
        
        # Convert voltage adjustment to reactive power adjustment
        reactive_power_adjustment = self._voltage_to_reactive_power(voltage_adjustment)
        
        # Limit reactive power adjustment
        reactive_power_adjustment = np.clip(
            reactive_power_adjustment,
            self.config.min_reactive_power,
            self.config.max_reactive_power
        )
        
        # Apply adjustments
        self._apply_voltage_adjustments(voltage_adjustment, reactive_power_adjustment)
        
        # Record action
        self._record_voltage_action(voltage_adjustment, reactive_power_adjustment)
        
        self.logger.debug(f"AVR: Voltage error={voltage_error:.2f}V, Q adjustment={reactive_power_adjustment:.2f} kVAR")
    
    def _execute_droop_voltage_control(self, dt: float):
        """Execute droop voltage control"""
        # Calculate voltage deviation
        voltage_deviation = (self.current_voltage - self.config.nominal_voltage) / self.config.nominal_voltage
        
        # Apply droop characteristic
        # V = V_nominal - (Q / Q_max) * droop_percentage * V_nominal
        # Therefore: Q = -V_deviation * Q_max / droop_percentage
        reactive_power_adjustment = -voltage_deviation * self.config.max_reactive_power / self.config.droop_characteristic
        
        # Limit reactive power adjustment
        reactive_power_adjustment = np.clip(
            reactive_power_adjustment,
            self.config.min_reactive_power,
            self.config.max_reactive_power
        )
        
        # Apply adjustment
        self._apply_voltage_adjustments(0.0, reactive_power_adjustment)
        
        # Record action
        self._record_voltage_action(0.0, reactive_power_adjustment)
        
        self.logger.debug(f"Droop control: V deviation={voltage_deviation:.3f}, Q adjustment={reactive_power_adjustment:.2f} kVAR")
    
    def _execute_dead_band_voltage_control(self, dt: float):
        """Execute dead band voltage control"""
        # Calculate voltage error
        voltage_error = self.target_voltage - self.current_voltage
        dead_band_threshold = self.config.nominal_voltage * self.config.dead_band
        
        if abs(voltage_error) <= dead_band_threshold:
            return  # No action needed
        
        # Apply correction outside dead band
        voltage_adjustment = voltage_error
        reactive_power_adjustment = self._voltage_to_reactive_power(voltage_adjustment)
        
        # Limit reactive power adjustment
        reactive_power_adjustment = np.clip(
            reactive_power_adjustment,
            self.config.min_reactive_power,
            self.config.max_reactive_power
        )
        
        # Apply adjustments
        self._apply_voltage_adjustments(voltage_adjustment, reactive_power_adjustment)
        
        # Record action
        self._record_voltage_action(voltage_adjustment, reactive_power_adjustment)
        
        self.logger.debug(f"Dead band control: V error={voltage_error:.2f}V, Q adjustment={reactive_power_adjustment:.2f} kVAR")
    
    def _apply_pid_control(self, error: float, dt: float) -> float:
        """Apply PID control for voltage regulation"""
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
    
    def _voltage_to_reactive_power(self, voltage_adjustment: float) -> float:
        """Convert voltage adjustment to reactive power adjustment"""
        # Simplified conversion: Q ≈ V * I * sin(φ)
        # For small voltage changes: ΔQ ≈ ΔV * I
        # Assuming nominal current of 1000A at 400V
        nominal_current = 1000.0  # A
        conversion_factor = nominal_current / self.config.nominal_voltage
        
        return voltage_adjustment * conversion_factor
    
    def _apply_voltage_adjustments(self, voltage_adjustment: float, reactive_power_adjustment: float):
        """Apply voltage and reactive power adjustments"""
        self.voltage_adjustment = voltage_adjustment
        self.reactive_power_adjustment = reactive_power_adjustment
        
        # Notify electrical system of adjustments
        # This would interface with the electrical system to adjust voltage and reactive power
        self.logger.debug(f"Applied adjustments: V={voltage_adjustment:.2f}V, Q={reactive_power_adjustment:.2f} kVAR")
    
    def _record_voltage_action(self, voltage_adjustment: float, reactive_power_adjustment: float):
        """Record voltage control action"""
        action = VoltageAction(
            timestamp=datetime.now(),
            voltage_adjustment=voltage_adjustment,
            reactive_power_adjustment=reactive_power_adjustment,
            control_mode=self.current_mode,
            response_time=self.config.response_time,
            accuracy=0.95  # Simulated accuracy
        )
        
        self.voltage_actions.append(action)
        
        # Limit history size
        if len(self.voltage_actions) > 1000:
            self.voltage_actions.pop(0)
    
    def _store_voltage_measurement(self):
        """Store voltage measurement"""
        measurement = VoltageMeasurement(
            timestamp=datetime.now(),
            voltage=self.current_voltage,
            reactive_power=self.current_reactive_power,
            power_factor=self.current_reactive_power / np.sqrt(self.current_reactive_power**2 + 1000**2) if self.current_reactive_power != 0 else 1.0,
            quality=0.98  # Simulated quality
        )
        
        self.voltage_history.append(measurement)
        
        # Limit history size
        if len(self.voltage_history) > 10000:
            self.voltage_history.pop(0)
    
    def _update_performance_metrics(self, dt: float):
        """Update performance metrics"""
        # Update voltage stability
        if len(self.voltage_history) > 0:
            recent_voltages = [m.voltage for m in self.voltage_history[-100:]]
            voltage_std = np.std(recent_voltages)
            self.performance_metrics['voltage_stability'] = 1.0 / (1.0 + voltage_std)
        
        # Update response time
        if len(self.voltage_actions) > 0:
            response_times = [action.response_time for action in self.voltage_actions[-100:]]
            self.performance_metrics['average_response_time'] = np.mean(response_times)
        
        # Update accuracy
        if len(self.voltage_actions) > 0:
            accuracies = [action.accuracy for action in self.voltage_actions[-100:]]
            self.performance_metrics['accuracy'] = np.mean(accuracies)
        
        # Update total adjustments
        self.performance_metrics['total_adjustments'] = len(self.voltage_actions)
        
        # Update voltage violations
        if self.voltage_status in [VoltageStatus.CRITICAL_HIGH, VoltageStatus.CRITICAL_LOW]:
            self.performance_metrics['voltage_violations'] += 1
    
    def set_voltage_configuration(self, nominal_voltage: float, voltage_range: Tuple[float, float], 
                                dead_band: float, droop_characteristic: float):
        """Set voltage configuration parameters"""
        self.config.nominal_voltage = nominal_voltage
        self.config.voltage_range = voltage_range
        self.config.dead_band = dead_band
        self.config.droop_characteristic = droop_characteristic
        
        self.logger.info(f"Voltage configuration updated: {nominal_voltage}V, range={voltage_range}, dead_band={dead_band*100:.1f}%, droop={droop_characteristic*100:.1f}%")
    
    def set_reactive_power_limits(self, max_reactive_power: float, min_reactive_power: float):
        """Set reactive power limits"""
        self.config.max_reactive_power = max_reactive_power
        self.config.min_reactive_power = min_reactive_power
        
        self.logger.info(f"Reactive power limits updated: {min_reactive_power:.1f} to {max_reactive_power:.1f} kVAR")
    
    def set_control_mode(self, mode: VoltageControlMode):
        """Set voltage control mode"""
        self.current_mode = mode
        self.logger.info(f"Voltage control mode set to: {mode.value}")
    
    def set_target_voltage(self, target_voltage: float):
        """Set target voltage"""
        self.target_voltage = target_voltage
        self.logger.info(f"Target voltage set to: {target_voltage:.1f}V")
    
    def set_pid_parameters(self, kp: float, ki: float, kd: float):
        """Set PID controller parameters"""
        self.pid_kp = kp
        self.pid_ki = ki
        self.pid_kd = kd
        self.pid_integral = 0.0  # Reset integral term
        
        self.logger.info(f"PID parameters updated: Kp={kp}, Ki={ki}, Kd={kd}")
    
    def get_current_status(self) -> Dict[str, Any]:
        """Get current regulator status"""
        return {
            'is_active': self.is_active,
            'control_mode': self.current_mode.value,
            'voltage_status': self.voltage_status.value,
            'current_voltage': self.current_voltage,
            'target_voltage': self.target_voltage,
            'current_reactive_power': self.current_reactive_power,
            'voltage_adjustment': self.voltage_adjustment,
            'reactive_power_adjustment': self.reactive_power_adjustment
        }
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics"""
        return self.performance_metrics.copy()
    
    def get_voltage_history(self, duration: timedelta = timedelta(hours=1)) -> List[VoltageMeasurement]:
        """Get voltage history for specified duration"""
        cutoff_time = datetime.now() - duration
        return [m for m in self.voltage_history if m.timestamp >= cutoff_time]
    
    def get_voltage_actions(self, duration: timedelta = timedelta(hours=1)) -> List[VoltageAction]:
        """Get voltage actions for specified duration"""
        cutoff_time = datetime.now() - duration
        return [a for a in self.voltage_actions if a.timestamp >= cutoff_time]
    
    def clear_history(self):
        """Clear voltage history and actions"""
        self.voltage_history.clear()
        self.voltage_actions.clear()
        self.logger.info("Voltage history cleared")
    
    def reset_performance_metrics(self):
        """Reset performance metrics"""
        self.performance_metrics = {
            'voltage_stability': 1.0,
            'response_time': 0.0,
            'accuracy': 0.0,
            'availability': 1.0,
            'total_adjustments': 0,
            'successful_adjustments': 0,
            'average_response_time': 0.0,
            'voltage_violations': 0
        }
        
        self.logger.info("Performance metrics reset") 