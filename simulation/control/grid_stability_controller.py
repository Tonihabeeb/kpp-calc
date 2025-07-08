import numpy as np
import logging
import time
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
from dataclasses import dataclass
from collections import deque

"""
Grid Stability Controller for KPP Power System
Implements advanced grid interaction and stability maintenance.
"""

class GridState(str, Enum):
    """Grid stability state enumeration"""
    NORMAL = "normal"
    FREQUENCY_CONTROL = "frequency_control"
    VOLTAGE_CONTROL = "voltage_control"
    EMERGENCY = "emergency"
    FAULT = "fault"

class ControlMode(str, Enum):
    """Control mode enumeration"""
    MANUAL = "manual"
    AUTOMATIC = "automatic"
    DROOP = "droop"
    ISOCHRONOUS = "isochronous"

class GridEvent(str, Enum):
    """Grid event type enumeration"""
    FREQUENCY_DEVIATION = "frequency_deviation"
    VOLTAGE_DEVIATION = "voltage_deviation"
    POWER_QUALITY_ISSUE = "power_quality_issue"
    GRID_FAULT = "grid_fault"
    STABILITY_RESTORED = "stability_restored"

@dataclass
class GridParameters:
    """Grid parameters data structure"""
    frequency: float  # Hz
    voltage: float  # V
    power_factor: float  # 0-1
    active_power: float  # W
    reactive_power: float  # VAR
    harmonic_distortion: float  # %
    phase_angle: float  # degrees

@dataclass
class GridConfig:
    """Grid stability controller configuration"""
    nominal_frequency: float = 50.0  # Hz
    nominal_voltage: float = 400.0  # V (line-to-line)
    frequency_tolerance: float = 0.1  # Hz
    voltage_tolerance: float = 0.05  # 5%
    power_factor_target: float = 0.95
    response_time_target: float = 0.1  # seconds
    droop_percentage: float = 5.0  # %
    max_reactive_power: float = 20000.0  # VAR

class GridStabilityController:
    """
    Advanced grid stability controller for KPP power system.
    Handles frequency control, voltage regulation, and power quality management.
    """
    
    def __init__(self, config: Optional[GridConfig] = None):
        """
        Initialize the grid stability controller.
        
        Args:
            config: Grid stability controller configuration
        """
        self.config = config or GridConfig()
        self.logger = logging.getLogger(__name__)
        
        # System state
        self.grid_state = GridState.NORMAL
        self.control_mode = ControlMode.AUTOMATIC
        
        # Grid parameters
        self.current_grid_params = GridParameters(
            frequency=self.config.nominal_frequency,
            voltage=self.config.nominal_voltage,
            power_factor=1.0,
            active_power=0.0,
            reactive_power=0.0,
            harmonic_distortion=0.0,
            phase_angle=0.0
        )
        
        # Performance tracking
        self.performance_metrics = {
            'frequency_regulation_time': 0.0,  # seconds
            'voltage_regulation_time': 0.0,  # seconds
            'power_quality_score': 100.0,  # 0-100
            'stability_events': 0,
            'grid_faults': 0,
            'operating_hours': 0.0,  # hours
            'frequency_deviations': 0,
            'voltage_deviations': 0
        }
        
        # Control history
        self.control_history: deque = deque(maxlen=1000)
        self.grid_events: List[Dict[str, Any]] = []
        
        # Frequency control
        self.frequency_control_active = False
        self.frequency_setpoint = self.config.nominal_frequency
        self.frequency_droop = self.config.droop_percentage / 100.0
        self.frequency_response_time = 0.0
        
        # Voltage control
        self.voltage_control_active = False
        self.voltage_setpoint = self.config.nominal_voltage
        self.voltage_droop = 0.03  # 3% voltage droop
        self.voltage_response_time = 0.0
        
        # Power quality
        self.power_quality_monitoring = True
        self.harmonic_threshold = 5.0  # %
        self.power_factor_threshold = 0.9
        
        # PID controllers
        self.frequency_pid = PIDController(1.0, 0.1, 0.01)
        self.voltage_pid = PIDController(1.0, 0.1, 0.01)
        self.power_factor_pid = PIDController(0.5, 0.05, 0.005)
        
        self.logger.info("Grid stability controller initialized")
    
    def start_grid_control(self) -> bool:
        """
        Start grid stability control.
        
        Returns:
            True if grid control started successfully
        """
        try:
            if self.grid_state != GridState.NORMAL:
                self.logger.warning("Cannot start grid control in state: %s", self.grid_state)
                return False
            
            # Initialize control systems
            self.frequency_control_active = True
            self.voltage_control_active = True
            self.power_quality_monitoring = True
            
            # Set control mode
            self.control_mode = ControlMode.AUTOMATIC
            
            # Record start event
            self._record_grid_event(GridEvent.STABILITY_RESTORED, "Grid control started")
            
            self.logger.info("Grid stability control started")
            return True
            
        except Exception as e:
            self.logger.error("Error starting grid control: %s", e)
            self._handle_fault("grid_start_error", str(e))
            return False
    
    def stop_grid_control(self) -> bool:
        """
        Stop grid stability control.
        
        Returns:
            True if grid control stopped successfully
        """
        try:
            if self.grid_state == GridState.FAULT:
                self.logger.warning("Cannot stop grid control in fault state")
                return False
            
            # Stop control systems
            self.frequency_control_active = False
            self.voltage_control_active = False
            self.power_quality_monitoring = False
            
            # Set control mode
            self.control_mode = ControlMode.MANUAL
            
            # Reset grid state
            self.grid_state = GridState.NORMAL
            
            self.logger.info("Grid stability control stopped")
            return True
            
        except Exception as e:
            self.logger.error("Error stopping grid control: %s", e)
            self._handle_fault("grid_stop_error", str(e))
            return False
    
    def update_grid_parameters(self, frequency: float, voltage: float, 
                              active_power: float, reactive_power: float,
                              power_factor: float, harmonic_distortion: float,
                              phase_angle: float) -> bool:
        """
        Update grid parameters.
        
        Args:
            frequency: Grid frequency (Hz)
            voltage: Grid voltage (V)
            active_power: Active power (W)
            reactive_power: Reactive power (VAR)
            power_factor: Power factor (0-1)
            harmonic_distortion: Harmonic distortion (%)
            phase_angle: Phase angle (degrees)
            
        Returns:
            True if update successful
        """
        try:
            # Update current grid parameters
            self.current_grid_params = GridParameters(
                frequency=frequency,
                voltage=voltage,
                power_factor=power_factor,
                active_power=active_power,
                reactive_power=reactive_power,
                harmonic_distortion=harmonic_distortion,
                phase_angle=phase_angle
            )
            
            # Check for grid events
            self._check_grid_events()
            
            # Execute control actions
            if self.frequency_control_active:
                self._execute_frequency_control()
            
            if self.voltage_control_active:
                self._execute_voltage_control()
            
            if self.power_quality_monitoring:
                self._execute_power_quality_control()
            
            # Update performance metrics
            self._update_performance_metrics()
            
            # Record control action
            self._record_control_action()
            
            return True
            
        except Exception as e:
            self.logger.error("Error updating grid parameters: %s", e)
            self._handle_fault("parameter_update_error", str(e))
            return False
    
    def _check_grid_events(self) -> None:
        """Check for grid events and stability issues."""
        try:
            # Check frequency deviation
            frequency_error = abs(self.current_grid_params.frequency - self.config.nominal_frequency)
            if frequency_error > self.config.frequency_tolerance:
                self._handle_frequency_deviation(frequency_error)
            
            # Check voltage deviation
            voltage_error = abs(self.current_grid_params.voltage - self.config.nominal_voltage) / self.config.nominal_voltage
            if voltage_error > self.config.voltage_tolerance:
                self._handle_voltage_deviation(voltage_error)
            
            # Check power quality
            if self.current_grid_params.harmonic_distortion > self.harmonic_threshold:
                self._handle_power_quality_issue("harmonic_distortion", 
                                               self.current_grid_params.harmonic_distortion)
            
            if self.current_grid_params.power_factor < self.power_factor_threshold:
                self._handle_power_quality_issue("low_power_factor", 
                                               self.current_grid_params.power_factor)
            
        except Exception as e:
            self.logger.error("Error checking grid events: %s", e)
    
    def _handle_frequency_deviation(self, frequency_error: float) -> None:
        """
        Handle frequency deviation.
        
        Args:
            frequency_error: Frequency error (Hz)
        """
        try:
            self.logger.warning("Frequency deviation detected: %.3f Hz", frequency_error)
            
            # Update performance metrics
            self.performance_metrics['frequency_deviations'] += 1
            
            # Record grid event
            self._record_grid_event(GridEvent.FREQUENCY_DEVIATION, 
                                  f"Frequency error: {frequency_error:.3f} Hz")
            
            # Update grid state
            if frequency_error > self.config.frequency_tolerance * 2:
                self.grid_state = GridState.FREQUENCY_CONTROL
            
            # Execute frequency control
            if self.frequency_control_active:
                self._execute_frequency_control()
            
        except Exception as e:
            self.logger.error("Error handling frequency deviation: %s", e)
    
    def _handle_voltage_deviation(self, voltage_error: float) -> None:
        """
        Handle voltage deviation.
        
        Args:
            voltage_error: Voltage error (per unit)
        """
        try:
            self.logger.warning("Voltage deviation detected: %.1f%%", voltage_error * 100)
            
            # Update performance metrics
            self.performance_metrics['voltage_deviations'] += 1
            
            # Record grid event
            self._record_grid_event(GridEvent.VOLTAGE_DEVIATION, 
                                  f"Voltage error: {voltage_error:.1%}")
            
            # Update grid state
            if voltage_error > self.config.voltage_tolerance * 2:
                self.grid_state = GridState.VOLTAGE_CONTROL
            
            # Execute voltage control
            if self.voltage_control_active:
                self._execute_voltage_control()
            
        except Exception as e:
            self.logger.error("Error handling voltage deviation: %s", e)
    
    def _handle_power_quality_issue(self, issue_type: str, value: float) -> None:
        """
        Handle power quality issue.
        
        Args:
            issue_type: Type of power quality issue
            value: Issue value
        """
        try:
            self.logger.warning("Power quality issue detected: %s = %.2f", issue_type, value)
            
            # Record grid event
            self._record_grid_event(GridEvent.POWER_QUALITY_ISSUE, 
                                  f"{issue_type}: {value:.2f}")
            
            # Update power quality score
            self._update_power_quality_score(issue_type, value)
            
        except Exception as e:
            self.logger.error("Error handling power quality issue: %s", e)
    
    def _execute_frequency_control(self) -> None:
        """Execute frequency control."""
        try:
            # Calculate frequency error
            frequency_error = self.config.nominal_frequency - self.current_grid_params.frequency
            
            # Apply droop control if enabled
            if self.control_mode == ControlMode.DROOP:
                droop_adjustment = self._calculate_frequency_droop()
                frequency_error += droop_adjustment
            
            # Calculate control response
            control_response = self.frequency_pid.calculate(frequency_error)
            
            # Apply control action
            power_adjustment = self._apply_frequency_control(control_response)
            
            # Update response time
            self.frequency_response_time = self._calculate_response_time()
            
            # Record control action
            self._record_frequency_control(frequency_error, control_response, power_adjustment)
            
        except Exception as e:
            self.logger.error("Error executing frequency control: %s", e)
    
    def _execute_voltage_control(self) -> None:
        """Execute voltage control."""
        try:
            # Calculate voltage error
            voltage_error = self.config.nominal_voltage - self.current_grid_params.voltage
            
            # Apply droop control if enabled
            if self.control_mode == ControlMode.DROOP:
                droop_adjustment = self._calculate_voltage_droop()
                voltage_error += droop_adjustment
            
            # Calculate control response
            control_response = self.voltage_pid.calculate(voltage_error)
            
            # Apply control action
            reactive_power_adjustment = self._apply_voltage_control(control_response)
            
            # Update response time
            self.voltage_response_time = self._calculate_response_time()
            
            # Record control action
            self._record_voltage_control(voltage_error, control_response, reactive_power_adjustment)
            
        except Exception as e:
            self.logger.error("Error executing voltage control: %s", e)
    
    def _execute_power_quality_control(self) -> None:
        """Execute power quality control."""
        try:
            # Calculate power factor error
            power_factor_error = self.config.power_factor_target - self.current_grid_params.power_factor
            
            # Calculate control response
            control_response = self.power_factor_pid.calculate(power_factor_error)
            
            # Apply power factor correction
            reactive_power_adjustment = self._apply_power_factor_control(control_response)
            
            # Record control action
            self._record_power_quality_control(power_factor_error, control_response, reactive_power_adjustment)
            
        except Exception as e:
            self.logger.error("Error executing power quality control: %s", e)
    
    def _calculate_frequency_droop(self) -> float:
        """
        Calculate frequency droop adjustment.
        
        Returns:
            Frequency droop adjustment (Hz)
        """
        try:
            # Calculate droop based on active power
            power_percentage = self.current_grid_params.active_power / 50000.0  # Normalize to 50 kW
            droop_adjustment = power_percentage * self.frequency_droop * self.config.nominal_frequency
            return droop_adjustment
            
        except Exception as e:
            self.logger.error("Error calculating frequency droop: %s", e)
            return 0.0
    
    def _calculate_voltage_droop(self) -> float:
        """
        Calculate voltage droop adjustment.
        
        Returns:
            Voltage droop adjustment (V)
        """
        try:
            # Calculate droop based on reactive power
            reactive_power_percentage = self.current_grid_params.reactive_power / self.config.max_reactive_power
            droop_adjustment = reactive_power_percentage * self.voltage_droop * self.config.nominal_voltage
            return droop_adjustment
            
        except Exception as e:
            self.logger.error("Error calculating voltage droop: %s", e)
            return 0.0
    
    def _apply_frequency_control(self, control_response: float) -> float:
        """
        Apply frequency control action.
        
        Args:
            control_response: Control response from PID
            
        Returns:
            Power adjustment (W)
        """
        try:
            # Limit control response
            max_power_adjustment = 10000.0  # 10 kW
            power_adjustment = max(-max_power_adjustment, 
                                 min(max_power_adjustment, control_response))
            
            # Apply power adjustment
            # In practice, this would interface with the power system
            self.logger.debug("Frequency control: power adjustment %.1f W", power_adjustment)
            
            return power_adjustment
            
        except Exception as e:
            self.logger.error("Error applying frequency control: %s", e)
            return 0.0
    
    def _apply_voltage_control(self, control_response: float) -> float:
        """
        Apply voltage control action.
        
        Args:
            control_response: Control response from PID
            
        Returns:
            Reactive power adjustment (VAR)
        """
        try:
            # Limit control response
            max_reactive_adjustment = 5000.0  # 5 kVAR
            reactive_adjustment = max(-max_reactive_adjustment, 
                                    min(max_reactive_adjustment, control_response))
            
            # Apply reactive power adjustment
            # In practice, this would interface with the power system
            self.logger.debug("Voltage control: reactive power adjustment %.1f VAR", reactive_adjustment)
            
            return reactive_adjustment
            
        except Exception as e:
            self.logger.error("Error applying voltage control: %s", e)
            return 0.0
    
    def _apply_power_factor_control(self, control_response: float) -> float:
        """
        Apply power factor control action.
        
        Args:
            control_response: Control response from PID
            
        Returns:
            Reactive power adjustment (VAR)
        """
        try:
            # Limit control response
            max_reactive_adjustment = 3000.0  # 3 kVAR
            reactive_adjustment = max(-max_reactive_adjustment, 
                                    min(max_reactive_adjustment, control_response))
            
            # Apply reactive power adjustment
            # In practice, this would interface with the power system
            self.logger.debug("Power factor control: reactive power adjustment %.1f VAR", reactive_adjustment)
            
            return reactive_adjustment
            
        except Exception as e:
            self.logger.error("Error applying power factor control: %s", e)
            return 0.0
    
    def _calculate_response_time(self) -> float:
        """
        Calculate control response time.
        
        Returns:
            Response time (seconds)
        """
        try:
            # Simplified response time calculation
            # In practice, this would be based on actual system dynamics
            return 0.05  # 50ms typical response time
            
        except Exception as e:
            self.logger.error("Error calculating response time: %s", e)
            return 0.1
    
    def _update_power_quality_score(self, issue_type: str, value: float) -> None:
        """
        Update power quality score.
        
        Args:
            issue_type: Type of power quality issue
            value: Issue value
        """
        try:
            # Calculate penalty based on issue type and value
            if issue_type == "harmonic_distortion":
                penalty = min(20, value / self.harmonic_threshold * 10)
            elif issue_type == "low_power_factor":
                penalty = min(15, (self.power_factor_threshold - value) * 100)
            else:
                penalty = 5
            
            # Update power quality score
            self.performance_metrics['power_quality_score'] = max(0, 
                self.performance_metrics['power_quality_score'] - penalty)
            
        except Exception as e:
            self.logger.error("Error updating power quality score: %s", e)
    
    def _update_performance_metrics(self) -> None:
        """Update performance metrics."""
        try:
            # Update operating hours
            self.performance_metrics['operating_hours'] += 0.001  # hours
            
            # Update regulation times
            if self.frequency_control_active:
                self.performance_metrics['frequency_regulation_time'] = self.frequency_response_time
            
            if self.voltage_control_active:
                self.performance_metrics['voltage_regulation_time'] = self.voltage_response_time
            
        except Exception as e:
            self.logger.error("Error updating performance metrics: %s", e)
    
    def _record_grid_event(self, event_type: GridEvent, message: str) -> None:
        """
        Record grid event.
        
        Args:
            event_type: Type of grid event
            message: Event message
        """
        try:
            event_record = {
                'timestamp': time.time(),
                'event_type': event_type.value,
                'message': message,
                'grid_state': self.grid_state.value,
                'frequency': self.current_grid_params.frequency,
                'voltage': self.current_grid_params.voltage,
                'power_factor': self.current_grid_params.power_factor
            }
            
            self.grid_events.append(event_record)
            
            # Update stability events count
            if event_type != GridEvent.STABILITY_RESTORED:
                self.performance_metrics['stability_events'] += 1
            
        except Exception as e:
            self.logger.error("Error recording grid event: %s", e)
    
    def _record_control_action(self) -> None:
        """Record control action."""
        try:
            control_record = {
                'timestamp': time.time(),
                'grid_state': self.grid_state.value,
                'control_mode': self.control_mode.value,
                'frequency': self.current_grid_params.frequency,
                'voltage': self.current_grid_params.voltage,
                'active_power': self.current_grid_params.active_power,
                'reactive_power': self.current_grid_params.reactive_power,
                'power_factor': self.current_grid_params.power_factor
            }
            
            self.control_history.append(control_record)
            
        except Exception as e:
            self.logger.error("Error recording control action: %s", e)
    
    def _record_frequency_control(self, error: float, response: float, adjustment: float) -> None:
        """
        Record frequency control action.
        
        Args:
            error: Frequency error
            response: Control response
            adjustment: Power adjustment
        """
        try:
            self.logger.debug("Frequency control: error=%.3f Hz, response=%.1f, adjustment=%.1f W", 
                            error, response, adjustment)
            
        except Exception as e:
            self.logger.error("Error recording frequency control: %s", e)
    
    def _record_voltage_control(self, error: float, response: float, adjustment: float) -> None:
        """
        Record voltage control action.
        
        Args:
            error: Voltage error
            response: Control response
            adjustment: Reactive power adjustment
        """
        try:
            self.logger.debug("Voltage control: error=%.1f V, response=%.1f, adjustment=%.1f VAR", 
                            error, response, adjustment)
            
        except Exception as e:
            self.logger.error("Error recording voltage control: %s", e)
    
    def _record_power_quality_control(self, error: float, response: float, adjustment: float) -> None:
        """
        Record power quality control action.
        
        Args:
            error: Power factor error
            response: Control response
            adjustment: Reactive power adjustment
        """
        try:
            self.logger.debug("Power quality control: error=%.3f, response=%.1f, adjustment=%.1f VAR", 
                            error, response, adjustment)
            
        except Exception as e:
            self.logger.error("Error recording power quality control: %s", e)
    
    def _handle_fault(self, fault_type: str, fault_message: str) -> None:
        """
        Handle grid stability controller faults.
        
        Args:
            fault_type: Type of fault
            fault_message: Fault message
        """
        try:
            self.logger.error("Grid fault: %s - %s", fault_type, fault_message)
            
            # Update system state
            self.grid_state = GridState.FAULT
            
            # Update performance metrics
            self.performance_metrics['grid_faults'] += 1
            
            # Record grid event
            self._record_grid_event(GridEvent.GRID_FAULT, f"{fault_type}: {fault_message}")
            
        except Exception as e:
            self.logger.error("Error handling fault: %s", e)
    
    def get_grid_state(self) -> GridState:
        """
        Get current grid state.
        
        Returns:
            Current grid state
        """
        return self.grid_state
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Get performance metrics.
        
        Returns:
            Performance metrics dictionary
        """
        return self.performance_metrics.copy()
    
    def get_current_grid_parameters(self) -> GridParameters:
        """
        Get current grid parameters.
        
        Returns:
            Current grid parameters
        """
        return self.current_grid_params
    
    def get_control_history(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get control history.
        
        Args:
            limit: Maximum number of records to return
            
        Returns:
            List of control history records
        """
        history_list = list(self.control_history)
        if limit is None:
            return history_list
        else:
            return history_list[-limit:]
    
    def get_grid_events(self) -> List[Dict[str, Any]]:
        """
        Get grid events.
        
        Returns:
            List of grid events
        """
        return self.grid_events.copy()
    
    def is_frequency_control_active(self) -> bool:
        """
        Check if frequency control is active.
        
        Returns:
            True if frequency control is active
        """
        return self.frequency_control_active
    
    def is_voltage_control_active(self) -> bool:
        """
        Check if voltage control is active.
        
        Returns:
            True if voltage control is active
        """
        return self.voltage_control_active
    
    def set_control_mode(self, control_mode: ControlMode) -> bool:
        """
        Set control mode.
        
        Args:
            control_mode: Control mode to set
            
        Returns:
            True if mode set successfully
        """
        try:
            self.control_mode = control_mode
            self.logger.info("Control mode changed to %s", control_mode.value)
            return True
            
        except Exception as e:
            self.logger.error("Error setting control mode: %s", e)
            return False
    
    def reset(self) -> None:
        """Reset grid stability controller to initial state."""
        self.grid_state = GridState.NORMAL
        self.control_mode = ControlMode.AUTOMATIC
        self.frequency_control_active = False
        self.voltage_control_active = False
        self.power_quality_monitoring = False
        self.control_history.clear()
        self.grid_events.clear()
        self.performance_metrics = {
            'frequency_regulation_time': 0.0,
            'voltage_regulation_time': 0.0,
            'power_quality_score': 100.0,
            'stability_events': 0,
            'grid_faults': 0,
            'operating_hours': 0.0,
            'frequency_deviations': 0,
            'voltage_deviations': 0
        }
        self.logger.info("Grid stability controller reset")


class PIDController:
    """
    PID controller for grid stability control.
    """
    
    def __init__(self, kp: float, ki: float, kd: float):
        """
        Initialize PID controller.
        
        Args:
            kp: Proportional gain
            ki: Integral gain
            kd: Derivative gain
        """
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.previous_error = 0.0
        self.integral = 0.0
        self.output = 0.0
    
    def calculate(self, error: float) -> float:
        """
        Calculate PID output.
        
        Args:
            error: Error signal
            
        Returns:
            Controller output
        """
        # Proportional term
        p_term = self.kp * error
        
        # Integral term
        self.integral += error
        i_term = self.ki * self.integral
        
        # Derivative term
        derivative = error - self.previous_error
        d_term = self.kd * derivative
        
        # Calculate output
        self.output = p_term + i_term + d_term
        
        # Update previous error
        self.previous_error = error
        
        return self.output
    
    def reset(self) -> None:
        """Reset controller state."""
        self.previous_error = 0.0
        self.integral = 0.0
        self.output = 0.0

