import numpy as np
import logging
import time
from typing import Any, Dict, List, Optional, Union, Tuple
from dataclasses import dataclass
from collections import deque
from enum import Enum
from .timing_controller import TimingController
from .load_manager import LoadManager, LoadProfile
from .grid_stability_controller import GridStabilityController
from .fault_detector import FaultDetector
from config.components.control_config import ControlConfig as ControlSystemConfig
"""
Integrated Control System for KPP Power Generation
Combines all Phase 4 advanced control components into a unified system.
"""

class ControlSystemState(str, Enum):
    """Control system state enumeration"""
    IDLE = "idle"
    STARTING = "starting"
    OPERATING = "operating"
    OPTIMIZING = "optimizing"
    FAULT = "fault"
    MAINTENANCE = "maintenance"

class ControlMode(str, Enum):
    """Control mode enumeration"""
    MANUAL = "manual"
    AUTOMATIC = "automatic"
    OPTIMIZATION = "optimization"
    EMERGENCY = "emergency"

@dataclass
class ControlState:
    """Control system state data structure"""
    system_state: ControlSystemState = ControlSystemState.IDLE
    control_mode: ControlMode = ControlMode.MANUAL
    target_power: float = 0.0  # W
    actual_power: float = 0.0  # W
    target_speed: float = 0.0  # RPM
    actual_speed: float = 0.0  # RPM
    target_frequency: float = 50.0  # Hz
    actual_frequency: float = 50.0  # Hz
    efficiency: float = 0.0
    response_time: float = 0.0  # seconds
    optimization_active: bool = False

@dataclass
class ControlConfig:
    """Control system configuration"""
    max_power: float = 50000.0  # W (50 kW)
    max_speed: float = 2000.0  # RPM
    target_frequency: float = 50.0  # Hz
    response_time_target: float = 0.1  # seconds
    optimization_enabled: bool = True
    fault_tolerance: float = 0.05  # 5%
    pid_kp: float = 1.0
    pid_ki: float = 0.1
    pid_kd: float = 0.01
    grid_sync_tolerance: float = 0.02  # 2%

class IntegratedControlSystem:
    """
    Comprehensive control system for KPP power generation.
    Integrates timing control, load management, grid stability, and fault detection.
    """
    
    def __init__(self, config: Optional[ControlConfig] = None):
        """
        Initialize the integrated control system.
        
        Args:
            config: Control system configuration
        """
        self.config = config or ControlConfig()
        self.logger = logging.getLogger(__name__)
        
        # System state
        self.control_state = ControlState()
        self.system_state = ControlSystemState.IDLE
        
        # Performance tracking
        self.performance_metrics = {
            'total_energy_controlled': 0.0,  # kWh
            'average_response_time': 0.0,  # seconds
            'control_accuracy': 0.0,  # %
            'optimization_savings': 0.0,  # kWh
            'fault_recovery_count': 0,
            'grid_stability_score': 0.0,  # 0-100
            'operating_hours': 0.0,  # hours
            'control_actions': 0
        }
        
        # Operation history
        self.operation_history: List[Dict[str, Any]] = []
        
        # Control components (will be initialized by external systems)
        self.timing_controller = None
        self.load_manager = None
        self.grid_stability = None
        self.fault_detector = None
        
        # PID controllers
        self.power_pid = PIDController(self.config.pid_kp, self.config.pid_ki, self.config.pid_kd)
        self.speed_pid = PIDController(self.config.pid_kp, self.config.pid_ki, self.config.pid_kd)
        self.frequency_pid = PIDController(self.config.pid_kp, self.config.pid_ki, self.config.pid_kd)
        
        # Control parameters
        self.power_setpoint = 0.0
        self.speed_setpoint = 0.0
        self.frequency_setpoint = self.config.target_frequency
        
        # Optimization parameters
        self.optimization_active = False
        self.optimization_target = 0.0
        self.optimization_constraints = {}
        
        # Fault handling
        self.fault_tolerance = self.config.fault_tolerance
        self.last_fault_time = 0.0
        self.fault_recovery_time = 5.0  # seconds
        
        self.logger.info("Integrated control system initialized")
    
    def start_control_system(self) -> bool:
        """
        Start the control system.
        
        Returns:
            True if control system started successfully
        """
        try:
            if self.system_state != ControlSystemState.IDLE:
                self.logger.warning("Cannot start control system in state: %s", self.system_state)
                return False
            
            # Transition to starting state
            self.system_state = ControlSystemState.STARTING
            
            # Initialize control components
            if not self._initialize_control_components():
                self.logger.error("Failed to initialize control components")
                self.system_state = ControlSystemState.IDLE
                return False
            
            # Set initial control parameters
            self.control_state.system_state = ControlSystemState.OPERATING
            self.control_state.control_mode = ControlMode.AUTOMATIC
            
            # Transition to operating state
            self.system_state = ControlSystemState.OPERATING
            
            # Record operation
            self._record_operation('control_start', {
                'control_mode': self.control_state.control_mode.value,
                'target_power': self.power_setpoint,
                'target_speed': self.speed_setpoint
            })
            
            self.logger.info("Control system started in %s mode", self.control_state.control_mode.value)
            return True
            
        except Exception as e:
            self.logger.error("Error starting control system: %s", e)
            self._handle_fault("control_start_error", str(e))
            return False
    
    def stop_control_system(self) -> bool:
        """
        Stop the control system.
        
        Returns:
            True if control system stopped successfully
        """
        try:
            if self.system_state not in [ControlSystemState.OPERATING, ControlSystemState.OPTIMIZING]:
                self.logger.warning("Cannot stop control system in state: %s", self.system_state)
                return False
            
            # Stop optimization if active
            if self.optimization_active:
                self._stop_optimization()
            
            # Reset control state
            self.control_state.system_state = ControlSystemState.IDLE
            self.control_state.control_mode = ControlMode.MANUAL
            self.control_state.target_power = 0.0
            self.control_state.actual_power = 0.0
            self.control_state.target_speed = 0.0
            self.control_state.actual_speed = 0.0
            self.control_state.efficiency = 0.0
            self.control_state.response_time = 0.0
            self.control_state.optimization_active = False
            
            # Transition to idle state
            self.system_state = ControlSystemState.IDLE
            
            # Record operation
            self._record_operation('control_stop', {
                'final_power': self.control_state.actual_power,
                'total_energy_controlled': self.performance_metrics['total_energy_controlled']
            })
            
            self.logger.info("Control system stopped")
            return True
            
        except Exception as e:
            self.logger.error("Error stopping control system: %s", e)
            self._handle_fault("control_stop_error", str(e))
            return False
    
    def update_control_state(self, actual_power: float, actual_speed: float, 
                           actual_frequency: float) -> bool:
        """
        Update control state based on actual system parameters.
        
        Args:
            actual_power: Actual power output (W)
            actual_speed: Actual speed (RPM)
            actual_frequency: Actual frequency (Hz)
            
        Returns:
            True if update successful
        """
        try:
            if self.system_state not in [ControlSystemState.OPERATING, ControlSystemState.OPTIMIZING]:
                return False
            
            # Update control state
            self.control_state.actual_power = actual_power
            self.control_state.actual_speed = actual_speed
            self.control_state.actual_frequency = actual_frequency
            
            # Calculate control response
            control_response = self._calculate_control_response()
            
            # Update performance metrics
            self._update_performance_metrics(actual_power, control_response)
            
            # Check for faults
            self._check_fault_conditions()
            
            # Execute optimization if active
            if self.optimization_active:
                self._execute_optimization()
            
            return True
            
        except Exception as e:
            self.logger.error("Error updating control state: %s", e)
            self._handle_fault("state_update_error", str(e))
            return False
    
    def set_power_setpoint(self, power_setpoint: float) -> bool:
        """
        Set power setpoint.
        
        Args:
            power_setpoint: Target power (W)
            
        Returns:
            True if setpoint set successfully
        """
        try:
            if power_setpoint < 0 or power_setpoint > self.config.max_power:
                self.logger.error("Invalid power setpoint: %.1f W", power_setpoint)
                return False
            
            self.power_setpoint = power_setpoint
            self.control_state.target_power = power_setpoint
            
            # Update PID controller setpoint
            self.power_pid.set_setpoint(power_setpoint)
            
            # Record operation
            self._record_operation('setpoint_change', {
                'parameter': 'power',
                'old_value': self.control_state.target_power,
                'new_value': power_setpoint
            })
            
            self.logger.info("Power setpoint updated to %.1f W", power_setpoint)
            return True
            
        except Exception as e:
            self.logger.error("Error setting power setpoint: %s", e)
            return False
    
    def set_speed_setpoint(self, speed_setpoint: float) -> bool:
        """
        Set speed setpoint.
        
        Args:
            speed_setpoint: Target speed (RPM)
            
        Returns:
            True if setpoint set successfully
        """
        try:
            if speed_setpoint < 0 or speed_setpoint > self.config.max_speed:
                self.logger.error("Invalid speed setpoint: %.1f RPM", speed_setpoint)
                return False
            
            self.speed_setpoint = speed_setpoint
            self.control_state.target_speed = speed_setpoint
            
            # Update PID controller setpoint
            self.speed_pid.set_setpoint(speed_setpoint)
            
            # Record operation
            self._record_operation('setpoint_change', {
                'parameter': 'speed',
                'old_value': self.control_state.target_speed,
                'new_value': speed_setpoint
            })
            
            self.logger.info("Speed setpoint updated to %.1f RPM", speed_setpoint)
            return True
            
        except Exception as e:
            self.logger.error("Error setting speed setpoint: %s", e)
            return False
    
    def set_control_mode(self, control_mode: ControlMode) -> bool:
        """
        Set control mode.
        
        Args:
            control_mode: Control mode to set
            
        Returns:
            True if mode set successfully
        """
        try:
            old_mode = self.control_state.control_mode
            self.control_state.control_mode = control_mode
            
            # Handle mode-specific actions
            if control_mode == ControlMode.OPTIMIZATION:
                self._start_optimization()
            elif control_mode == ControlMode.EMERGENCY:
                self._activate_emergency_mode()
            
            # Record operation
            self._record_operation('mode_change', {
                'old_mode': old_mode.value,
                'new_mode': control_mode.value
            })
            
            self.logger.info("Control mode changed from %s to %s", old_mode.value, control_mode.value)
            return True
            
        except Exception as e:
            self.logger.error("Error setting control mode: %s", e)
            return False
    
    def _initialize_control_components(self) -> bool:
        """
        Initialize control components.
        
        Returns:
            True if initialization successful
        """
        try:
            # Initialize timing controller
            if self.timing_controller is None:
                self.timing_controller = TimingController()
            
            # Initialize load manager
            if self.load_manager is None:
                self.load_manager = LoadManager()
            
            # Initialize grid stability controller
            if self.grid_stability is None:
                self.grid_stability = GridStabilityController()
            
            # Initialize fault detector
            if self.fault_detector is None:
                self.fault_detector = FaultDetector()
            
            return True
            
        except Exception as e:
            self.logger.error("Error initializing control components: %s", e)
            return False
    
    def _calculate_control_response(self) -> Dict[str, float]:
        """
        Calculate control response using PID controllers.
        
        Returns:
            Control response dictionary
        """
        try:
            # Calculate power control response
            power_error = self.power_setpoint - self.control_state.actual_power
            power_response = self.power_pid.calculate(power_error)
            
            # Calculate speed control response
            speed_error = self.speed_setpoint - self.control_state.actual_speed
            speed_response = self.speed_pid.calculate(speed_error)
            
            # Calculate frequency control response
            frequency_error = self.frequency_setpoint - self.control_state.actual_frequency
            frequency_response = self.frequency_pid.calculate(frequency_error)
            
            # Calculate response time
            response_time = self._calculate_response_time()
            
            return {
                'power_response': power_response,
                'speed_response': speed_response,
                'frequency_response': frequency_response,
                'response_time': response_time
            }
            
        except Exception as e:
            self.logger.error("Error calculating control response: %s", e)
            return {
                'power_response': 0.0,
                'speed_response': 0.0,
                'frequency_response': 0.0,
                'response_time': 0.0
            }
    
    def _calculate_response_time(self) -> float:
        """
        Calculate system response time.
        
        Returns:
            Response time (seconds)
        """
        try:
            # Simplified response time calculation
            # In practice, this would be based on actual system dynamics
            power_error = abs(self.power_setpoint - self.control_state.actual_power)
            speed_error = abs(self.speed_setpoint - self.control_state.actual_speed)
            
            # Response time based on error magnitude
            if power_error < self.config.max_power * 0.01:  # 1% error
                response_time = 0.05  # 50ms
            elif power_error < self.config.max_power * 0.05:  # 5% error
                response_time = 0.1   # 100ms
            else:
                response_time = 0.2   # 200ms
            
            return response_time
            
        except Exception as e:
            self.logger.error("Error calculating response time: %s", e)
            return 0.1
    
    def _start_optimization(self) -> None:
        """Start optimization mode."""
        try:
            if not self.config.optimization_enabled:
                self.logger.warning("Optimization not enabled")
                return
            
            self.optimization_active = True
            self.control_state.optimization_active = True
            self.system_state = ControlSystemState.OPTIMIZING
            
            # Set optimization target
            self.optimization_target = self.control_state.actual_power
            
            self.logger.info("Optimization mode activated")
            
        except Exception as e:
            self.logger.error("Error starting optimization: %s", e)
    
    def _stop_optimization(self) -> None:
        """Stop optimization mode."""
        try:
            self.optimization_active = False
            self.control_state.optimization_active = False
            
            if self.system_state == ControlSystemState.OPTIMIZING:
                self.system_state = ControlSystemState.OPERATING
            
            self.logger.info("Optimization mode deactivated")
            
        except Exception as e:
            self.logger.error("Error stopping optimization: %s", e)
    
    def _execute_optimization(self) -> None:
        """Execute optimization algorithm."""
        try:
            # Simplified optimization algorithm
            # In practice, this would use advanced optimization techniques
            
            current_power = self.control_state.actual_power
            current_efficiency = self.control_state.efficiency
            
            # Optimize for efficiency
            if current_efficiency < 0.9:  # Below 90% efficiency
                # Adjust setpoints for better efficiency
                efficiency_improvement = self._calculate_efficiency_improvement()
                self.performance_metrics['optimization_savings'] += efficiency_improvement
            
            # Optimize for grid stability
            grid_stability_score = self._calculate_grid_stability_score()
            self.performance_metrics['grid_stability_score'] = grid_stability_score
            
        except Exception as e:
            self.logger.error("Error executing optimization: %s", e)
    
    def _calculate_efficiency_improvement(self) -> float:
        """
        Calculate potential efficiency improvement.
        
        Returns:
            Efficiency improvement (kWh)
        """
        try:
            # Simplified efficiency improvement calculation
            current_efficiency = self.control_state.efficiency
            target_efficiency = 0.95  # 95% target
            
            if current_efficiency < target_efficiency:
                improvement = (target_efficiency - current_efficiency) * 0.001  # kWh
                return improvement
            else:
                return 0.0
                
        except Exception as e:
            self.logger.error("Error calculating efficiency improvement: %s", e)
            return 0.0
    
    def _calculate_grid_stability_score(self) -> float:
        """
        Calculate grid stability score.
        
        Returns:
            Grid stability score (0-100)
        """
        try:
            # Simplified grid stability calculation
            frequency_error = abs(self.control_state.actual_frequency - self.config.target_frequency)
            power_error = abs(self.control_state.actual_power - self.control_state.target_power)
            
            # Calculate stability score
            frequency_score = max(0, 100 - frequency_error * 1000)  # Penalize frequency errors
            power_score = max(0, 100 - power_error / self.config.max_power * 100)  # Penalize power errors
            
            stability_score = (frequency_score + power_score) / 2
            return min(100, max(0, stability_score))
            
        except Exception as e:
            self.logger.error("Error calculating grid stability score: %s", e)
            return 50.0
    
    def _activate_emergency_mode(self) -> None:
        """Activate emergency mode."""
        try:
            # Set emergency parameters
            self.power_setpoint = 0.0
            self.speed_setpoint = 0.0
            
            # Update control state
            self.control_state.target_power = 0.0
            self.control_state.target_speed = 0.0
            self.control_state.control_mode = ControlMode.EMERGENCY
            
            self.logger.warning("Emergency mode activated")
            
        except Exception as e:
            self.logger.error("Error activating emergency mode: %s", e)
    
    def _update_performance_metrics(self, actual_power: float, control_response: Dict[str, float]) -> None:
        """
        Update performance metrics.
        
        Args:
            actual_power: Actual power output (W)
            control_response: Control response dictionary
        """
        try:
            # Update energy tracking
            self.performance_metrics['total_energy_controlled'] += actual_power * 0.001  # kWh
            
            # Update response time
            response_time = control_response.get('response_time', 0.0)
            self.performance_metrics['average_response_time'] = (
                (self.performance_metrics['average_response_time'] + response_time) / 2
            )
            
            # Update control accuracy
            power_error = abs(self.control_state.target_power - actual_power)
            if self.control_state.target_power > 0:
                accuracy = max(0, 100 - (power_error / self.control_state.target_power * 100))
                self.performance_metrics['control_accuracy'] = (
                    (self.performance_metrics['control_accuracy'] + accuracy) / 2
                )
            
            # Update operating hours
            self.performance_metrics['operating_hours'] += 0.001  # hours
            
            # Update control actions
            self.performance_metrics['control_actions'] += 1
            
        except Exception as e:
            self.logger.error("Error updating performance metrics: %s", e)
    
    def _check_fault_conditions(self) -> None:
        """Check for fault conditions."""
        try:
            # Check power deviation
            power_error = abs(self.control_state.actual_power - self.control_state.target_power)
            if power_error > self.config.max_power * self.fault_tolerance:
                self._handle_fault("power_deviation", f"Power error {power_error:.1f} W exceeds tolerance")
            
            # Check frequency deviation
            frequency_error = abs(self.control_state.actual_frequency - self.config.target_frequency)
            if frequency_error > 2.0:  # 2 Hz tolerance
                self._handle_fault("frequency_deviation", f"Frequency error {frequency_error:.1f} Hz exceeds tolerance")
            
            # Check response time
            if self.control_state.response_time > self.config.response_time_target * 2:
                self._handle_fault("slow_response", f"Response time {self.control_state.response_time:.3f} s exceeds target")
                
        except Exception as e:
            self.logger.error("Error checking fault conditions: %s", e)
    
    def _handle_fault(self, fault_type: str, fault_message: str) -> None:
        """
        Handle control system faults.
        
        Args:
            fault_type: Type of fault
            fault_message: Fault message
        """
        try:
            self.logger.error("Control fault: %s - %s", fault_type, fault_message)
            
            # Update system state
            self.system_state = ControlSystemState.FAULT
            
            # Update performance metrics
            self.performance_metrics['fault_recovery_count'] += 1
            self.last_fault_time = time.time()
            
            # Record fault
            self._record_operation('fault', {
                'fault_type': fault_type,
                'fault_message': fault_message,
                'system_state': self.system_state.value
            })
            
        except Exception as e:
            self.logger.error("Error handling fault: %s", e)
    
    def _record_operation(self, operation_type: str, data: Dict[str, Any]) -> None:
        """
        Record operation in history.
        
        Args:
            operation_type: Type of operation
            data: Operation data
        """
        try:
            operation_record = {
                'timestamp': time.time(),
                'type': operation_type,
                'data': data,
                'control_state': {
                    'system_state': self.system_state.value,
                    'control_mode': self.control_state.control_mode.value,
                    'target_power': self.control_state.target_power,
                    'actual_power': self.control_state.actual_power,
                    'efficiency': self.control_state.efficiency,
                    'response_time': self.control_state.response_time
                }
            }
            
            self.operation_history.append(operation_record)
            
        except Exception as e:
            self.logger.error("Error recording operation: %s", e)
    
    def get_control_state(self) -> ControlState:
        """
        Get current control state.
        
        Returns:
            Current control state
        """
        return self.control_state
    
    def get_system_state(self) -> ControlSystemState:
        """
        Get current system state.
        
        Returns:
            Current system state
        """
        return self.system_state
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Get performance metrics.
        
        Returns:
            Performance metrics dictionary
        """
        return self.performance_metrics.copy()
    
    def get_operation_history(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get operation history.
        
        Args:
            limit: Maximum number of operations to return
            
        Returns:
            List of operation records
        """
        if limit is None:
            return self.operation_history.copy()
        else:
            return self.operation_history[-limit:]
    
    def is_operating(self) -> bool:
        """
        Check if control system is operating.
        
        Returns:
            True if operating
        """
        return self.system_state in [ControlSystemState.OPERATING, ControlSystemState.OPTIMIZING]
    
    def is_optimizing(self) -> bool:
        """
        Check if optimization is active.
        
        Returns:
            True if optimizing
        """
        return self.optimization_active
    
    def reset(self) -> None:
        """Reset control system to initial state."""
        self.control_state = ControlState()
        self.system_state = ControlSystemState.IDLE
        self.operation_history.clear()
        self.performance_metrics = {
            'total_energy_controlled': 0.0,
            'average_response_time': 0.0,
            'control_accuracy': 0.0,
            'optimization_savings': 0.0,
            'fault_recovery_count': 0,
            'grid_stability_score': 0.0,
            'operating_hours': 0.0,
            'control_actions': 0
        }
        self.optimization_active = False
        self.logger.info("Control system reset")


class PIDController:
    """
    PID controller for control system.
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
        self.setpoint = 0.0
        self.previous_error = 0.0
        self.integral = 0.0
        self.output = 0.0
    
    def set_setpoint(self, setpoint: float) -> None:
        """
        Set controller setpoint.
        
        Args:
            setpoint: Target value
        """
        self.setpoint = setpoint
    
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

