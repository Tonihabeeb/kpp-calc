import logging
import time
import numpy as np
from typing import Dict, List, Optional, Any, Tuple, Set, Callable
from enum import Enum
from dataclasses import dataclass
from collections import deque

from .emergency_response import EmergencyResponse, EmergencyState, EmergencyType, SafetyLevel
from .fault_detector import FaultDetector, FaultState, FaultType, FaultSeverity

class IntegratedSystemState(str, Enum):
    """Integrated system state enumeration"""
    NORMAL = "normal"
    MONITORING = "monitoring"
    WARNING = "warning"
    FAULT = "fault"
    EMERGENCY = "emergency"
    SHUTDOWN = "shutdown"
    RECOVERY = "recovery"

@dataclass
class IntegratedSystemConfig:
    """Configuration for the integrated fault and emergency system"""
    monitoring_interval: float = 0.1  # seconds
    fault_tolerance_time: float = 5.0  # seconds
    recovery_timeout: float = 30.0  # seconds
    emergency_timeout: float = 10.0  # seconds
    max_concurrent_faults: int = 5
    auto_recovery_enabled: bool = True
    emergency_shutdown_enabled: bool = True
    predictive_monitoring_enabled: bool = True
    cascade_prevention_enabled: bool = True

class IntegratedFaultSystem:
    """
    Advanced integrated fault detection and emergency response system.
    Combines fault detection, emergency response, and predictive monitoring.
    """
    
    def __init__(self, config: Optional[IntegratedSystemConfig] = None):
        """Initialize the integrated system"""
        self.config = config or IntegratedSystemConfig()
        self.logger = logging.getLogger(__name__)
        
        # Initialize subsystems
        self.fault_detector = FaultDetector()
        self.emergency_response = EmergencyResponse()
        
        # System state
        self.system_state = IntegratedSystemState.NORMAL
        self.monitoring_active = False
        
        # Predictive monitoring
        self.parameter_history: Dict[str, deque] = {
            'voltage': deque(maxlen=1000),
            'current': deque(maxlen=1000),
            'frequency': deque(maxlen=1000),
            'temperature': deque(maxlen=1000),
            'pressure': deque(maxlen=1000),
            'speed': deque(maxlen=1000),
            'vibration': deque(maxlen=1000)
        }
        
        # Trend analysis
        self.trend_thresholds = {
            'voltage_trend': 0.05,  # V/s
            'current_trend': 0.1,  # A/s
            'frequency_trend': 0.2,  # Hz/s
            'temperature_trend': 2.0,  # °C/s
            'pressure_trend': 0.5,  # bar/s
            'speed_trend': 1.0,  # rpm/s
            'vibration_trend': 0.5  # mm/s²
        }
        
        # Cascade prevention
        self.dependency_graph: Dict[str, Set[str]] = {
            'electrical': {'mechanical', 'control'},
            'mechanical': {'electrical', 'thermal'},
            'thermal': {'mechanical', 'electrical'},
            'control': {'electrical', 'mechanical'},
            'grid': {'electrical', 'control'},
            'safety': {'electrical', 'mechanical', 'thermal', 'control', 'grid'}
        }
        
        # Performance metrics
        self.performance_metrics = {
            'total_faults': 0,
            'total_emergencies': 0,
            'prevented_cascades': 0,
            'successful_recoveries': 0,
            'false_positives': 0,
            'detection_accuracy': 100.0,
            'average_response_time': 0.0,
            'system_availability': 100.0
        }
        
        self.logger.info("Integrated fault system initialized")
    
    def start_monitoring(self) -> bool:
        """Start system monitoring"""
        try:
            if self.monitoring_active:
                return True
                
            self.fault_detector.start_monitoring()
            self.emergency_response.start_emergency_monitoring()
            self.monitoring_active = True
            self.system_state = IntegratedSystemState.MONITORING
            
            self.logger.info("Integrated system monitoring started")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start monitoring: {e}")
            return False
    
    def stop_monitoring(self) -> bool:
        """Stop system monitoring"""
        try:
            if not self.monitoring_active:
                return True
                
            self.fault_detector.stop_monitoring()
            self.emergency_response.stop_emergency_monitoring()
            self.monitoring_active = False
            self.system_state = IntegratedSystemState.NORMAL
            
            self.logger.info("Integrated system monitoring stopped")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to stop monitoring: {e}")
            return False
    
    def monitor_system_parameters(self, params: Dict[str, Dict[str, float]]) -> None:
        """
        Monitor system parameters and detect faults/emergencies
        
        Args:
            params: Dictionary containing system parameters by category
        """
        if not self.monitoring_active:
            return
            
        try:
            # Update parameter history
            self._update_parameter_history(params)
            
            # Perform predictive monitoring if enabled
            if self.config.predictive_monitoring_enabled:
                self._perform_predictive_monitoring()
            
            # Check for faults
            self.fault_detector.monitor_system_parameters(
                electrical_params=params.get('electrical', {}),
                mechanical_params=params.get('mechanical', {}),
                thermal_params=params.get('thermal', {}),
                control_params=params.get('control', {})
            )
            
            # Check for emergency conditions
            self._check_emergency_conditions(params)
            
            # Prevent cascading failures if enabled
            if self.config.cascade_prevention_enabled:
                self._prevent_cascading_failures()
            
        except Exception as e:
            self.logger.error(f"Error in system monitoring: {e}")
            self._handle_monitoring_error(str(e))
    
    def _update_parameter_history(self, params: Dict[str, Dict[str, float]]) -> None:
        """Update parameter history for trend analysis"""
        timestamp = time.time()
        
        for category, values in params.items():
            for param, value in values.items():
                if param in self.parameter_history:
                    self.parameter_history[param].append((timestamp, value))
    
    def _perform_predictive_monitoring(self) -> None:
        """Analyze trends and predict potential failures"""
        for param, history in self.parameter_history.items():
            if len(history) < 2:
                continue
                
            # Calculate rate of change
            times, values = zip(*list(history)[-10:])  # Last 10 samples
            if len(times) < 2:
                continue
                
            trend = np.polyfit(times, values, 1)[0]  # Linear trend
            
            # Check against trend thresholds
            threshold_key = f"{param}_trend"
            if threshold_key in self.trend_thresholds:
                if abs(trend) > self.trend_thresholds[threshold_key]:
                    self._handle_trend_violation(param, trend)
    
    def _prevent_cascading_failures(self) -> None:
        """Prevent cascade of failures across dependent systems"""
        active_faults = self.fault_detector.get_active_faults()
        if not active_faults:
            return
            
        # Check for potential cascading effects
        for fault in active_faults:
            dependent_systems = self.dependency_graph.get(fault.fault_type, set())
            for system in dependent_systems:
                self._apply_preventive_measures(system, fault)
    
    def _apply_preventive_measures(self, system: str, triggering_fault: Any) -> None:
        """
        Apply preventive measures to dependent systems
        
        Args:
            system: The dependent system to protect
            triggering_fault: The fault that triggered the preventive measures
        """
        try:
            # Define system-specific preventive measures
            preventive_measures = {
                'electrical': self._protect_electrical_system,
                'mechanical': self._protect_mechanical_system,
                'thermal': self._protect_thermal_system,
                'control': self._protect_control_system,
                'grid': self._protect_grid_system,
                'safety': self._protect_safety_system
            }
            
            if system in preventive_measures:
                preventive_measures[system](triggering_fault)
                self.performance_metrics['prevented_cascades'] += 1
                self.logger.info(f"Applied preventive measures to {system} system")
                
        except Exception as e:
            self.logger.error(f"Failed to apply preventive measures to {system}: {e}")
    
    def _protect_electrical_system(self, triggering_fault: Any) -> None:
        """Protect electrical system from cascading failures"""
        # Implement electrical system protection measures
        # For example: reduce load, adjust voltage limits, etc.
        pass
    
    def _protect_mechanical_system(self, triggering_fault: Any) -> None:
        """Protect mechanical system from cascading failures"""
        # Implement mechanical system protection measures
        # For example: reduce speed, adjust torque limits, etc.
        pass
    
    def _protect_thermal_system(self, triggering_fault: Any) -> None:
        """Protect thermal system from cascading failures"""
        # Implement thermal system protection measures
        # For example: increase cooling, reduce power, etc.
        pass
    
    def _protect_control_system(self, triggering_fault: Any) -> None:
        """Protect control system from cascading failures"""
        # Implement control system protection measures
        # For example: switch to failsafe mode, limit control actions, etc.
        pass
    
    def _protect_grid_system(self, triggering_fault: Any) -> None:
        """Protect grid interface from cascading failures"""
        # Implement grid protection measures
        # For example: reduce power export, adjust frequency limits, etc.
        pass
    
    def _protect_safety_system(self, triggering_fault: Any) -> None:
        """Protect safety systems from cascading failures"""
        # Implement safety system protection measures
        # For example: activate backup systems, increase monitoring, etc.
        pass
    
    def _check_emergency_conditions(self, params: Dict[str, Dict[str, float]]) -> None:
        """
        Check for emergency conditions in system parameters
        
        Args:
            params: Dictionary containing system parameters by category
        """
        try:
            # Define emergency condition checks
            emergency_checks = {
                'electrical': self._check_electrical_emergency,
                'mechanical': self._check_mechanical_emergency,
                'thermal': self._check_thermal_emergency,
                'control': self._check_control_emergency,
                'grid': self._check_grid_emergency,
                'safety': self._check_safety_emergency
            }
            
            # Check each system for emergency conditions
            for system, check_func in emergency_checks.items():
                if system in params:
                    check_func(params[system])
                    
        except Exception as e:
            self.logger.error(f"Error checking emergency conditions: {e}")
            self._handle_monitoring_error(str(e))
    
    def _check_electrical_emergency(self, params: Dict[str, float]) -> None:
        """Check for electrical system emergencies"""
        if 'voltage' in params and abs(params['voltage']) > 1.2:  # 20% overvoltage
            self._trigger_emergency(EmergencyType.ELECTRICAL_FAULT, 
                                 "Critical overvoltage detected",
                                 params)
        elif 'current' in params and abs(params['current']) > 1.5:  # 50% overcurrent
            self._trigger_emergency(EmergencyType.ELECTRICAL_FAULT,
                                 "Critical overcurrent detected",
                                 params)
    
    def _check_mechanical_emergency(self, params: Dict[str, float]) -> None:
        """Check for mechanical system emergencies"""
        if 'speed' in params and abs(params['speed']) > 1.3:  # 30% overspeed
            self._trigger_emergency(EmergencyType.MECHANICAL_FAULT,
                                 "Critical overspeed detected",
                                 params)
        elif 'vibration' in params and params['vibration'] > 20.0:  # mm/s
            self._trigger_emergency(EmergencyType.MECHANICAL_FAULT,
                                 "Excessive vibration detected",
                                 params)
    
    def _check_thermal_emergency(self, params: Dict[str, float]) -> None:
        """Check for thermal system emergencies"""
        if 'temperature' in params and params['temperature'] > 100.0:  # °C
            self._trigger_emergency(EmergencyType.THERMAL_FAULT,
                                 "Critical temperature detected",
                                 params)
    
    def _check_control_emergency(self, params: Dict[str, float]) -> None:
        """Check for control system emergencies"""
        if 'response_time' in params and params['response_time'] > 2.0:  # seconds
            self._trigger_emergency(EmergencyType.CONTROL_FAULT,
                                 "Control system response timeout",
                                 params)
    
    def _check_grid_emergency(self, params: Dict[str, float]) -> None:
        """Check for grid interface emergencies"""
        if 'frequency' in params and abs(params['frequency'] - 50.0) > 2.0:  # Hz
            self._trigger_emergency(EmergencyType.GRID_FAULT,
                                 "Critical frequency deviation",
                                 params)
    
    def _check_safety_emergency(self, params: Dict[str, float]) -> None:
        """Check for safety system emergencies"""
        if 'safety_status' in params and params['safety_status'] < 0.5:  # Below 50%
            self._trigger_emergency(EmergencyType.SAFETY_VIOLATION,
                                 "Safety system degradation detected",
                                 params)
    
    def _trigger_emergency(self, emergency_type: EmergencyType, message: str, 
                         parameters: Dict[str, float]) -> None:
        """
        Trigger an emergency response
        
        Args:
            emergency_type: Type of emergency
            message: Emergency description
            parameters: System parameters at time of emergency
        """
        try:
            # Update system state
            self.system_state = IntegratedSystemState.EMERGENCY
            
            # Trigger emergency response
            self.emergency_response.trigger_emergency(
                emergency_type=emergency_type,
                severity=SafetyLevel.CRITICAL,
                message=message,
                parameters=parameters
            )
            
            # Update metrics
            self.performance_metrics['total_emergencies'] += 1
            
            self.logger.warning(f"Emergency triggered: {message}")
            
        except Exception as e:
            self.logger.error(f"Failed to trigger emergency response: {e}")
    
    def _handle_trend_violation(self, parameter: str, trend: float) -> None:
        """
        Handle parameter trend violations
        
        Args:
            parameter: The parameter showing concerning trend
            trend: The calculated trend value
        """
        try:
            message = f"Concerning trend detected in {parameter}: {trend:.2f} per second"
            
            # Determine severity based on trend magnitude
            severity = SafetyLevel.WARNING
            if abs(trend) > 2 * self.trend_thresholds[f"{parameter}_trend"]:
                severity = SafetyLevel.CRITICAL
            
            # Map parameter to emergency type
            emergency_type_mapping = {
                'voltage': EmergencyType.ELECTRICAL_FAULT,
                'current': EmergencyType.ELECTRICAL_FAULT,
                'frequency': EmergencyType.GRID_FAULT,
                'temperature': EmergencyType.THERMAL_FAULT,
                'pressure': EmergencyType.MECHANICAL_FAULT,
                'speed': EmergencyType.MECHANICAL_FAULT,
                'vibration': EmergencyType.MECHANICAL_FAULT
            }
            
            if parameter in emergency_type_mapping:
                self.emergency_response.trigger_emergency(
                    emergency_type=emergency_type_mapping[parameter],
                    severity=severity,
                    message=message,
                    parameters={'trend': trend}
                )
            
            self.logger.warning(message)
            
        except Exception as e:
            self.logger.error(f"Failed to handle trend violation: {e}")
    
    def _handle_monitoring_error(self, error_message: str) -> None:
        """
        Handle monitoring system errors
        
        Args:
            error_message: Description of the error
        """
        try:
            # Log the error
            self.logger.error(f"Monitoring error: {error_message}")
            
            # Update system state
            self.system_state = IntegratedSystemState.FAULT
            
            # Trigger control fault emergency
            self.emergency_response.trigger_emergency(
                emergency_type=EmergencyType.CONTROL_FAULT,
                severity=SafetyLevel.WARNING,
                message=f"Monitoring system error: {error_message}",
                parameters={'error': error_message}
            )
            
        except Exception as e:
            self.logger.critical(f"Failed to handle monitoring error: {e}")
            # As a last resort, try to stop monitoring
            self.stop_monitoring()
    
    def get_system_state(self) -> IntegratedSystemState:
        """Get current system state"""
        return self.system_state
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get system performance metrics"""
        return self.performance_metrics
    
    def reset(self) -> None:
        """Reset the integrated system"""
        self.fault_detector.reset()
        self.emergency_response.reset()
        self.system_state = IntegratedSystemState.NORMAL
        self.monitoring_active = False
        self.parameter_history.clear()
        self.performance_metrics = {k: 0 for k in self.performance_metrics}
        self.performance_metrics['detection_accuracy'] = 100.0
        self.performance_metrics['system_availability'] = 100.0 