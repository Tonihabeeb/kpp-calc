import numpy as np
import logging
import time
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
from dataclasses import dataclass
from collections import deque
"""
Fault Detection and Recovery System for KPP Power System
Implements comprehensive system monitoring and protection.
"""

class FaultState(str, Enum):
    """Fault detector state enumeration"""
    NORMAL = "normal"
    MONITORING = "monitoring"
    ALARM = "alarm"
    FAULT = "fault"
    RECOVERY = "recovery"
    EMERGENCY = "emergency"

class FaultType(str, Enum):
    """Fault type enumeration"""
    ELECTRICAL = "electrical"
    MECHANICAL = "mechanical"
    THERMAL = "thermal"
    CONTROL = "control"
    GRID = "grid"
    SAFETY = "safety"

class FaultSeverity(str, Enum):
    """Fault severity enumeration"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class AlarmType(str, Enum):
    """Alarm type enumeration"""
    WARNING = "warning"
    ALERT = "alert"
    CRITICAL = "critical"
    EMERGENCY = "emergency"

@dataclass
class FaultEvent:
    """Fault event data structure"""
    fault_type: FaultType
    severity: FaultSeverity
    timestamp: float
    message: str
    parameters: Dict[str, Any]
    resolved: bool = False
    resolution_time: Optional[float] = None

@dataclass
class AlarmEvent:
    """Alarm event data structure"""
    alarm_type: AlarmType
    timestamp: float
    message: str
    parameters: Dict[str, Any]
    acknowledged: bool = False
    acknowledgment_time: Optional[float] = None

@dataclass
class FaultConfig:
    """Fault detector configuration"""
    monitoring_enabled: bool = True
    auto_recovery_enabled: bool = True
    emergency_shutdown_enabled: bool = True
    fault_tolerance_time: float = 5.0  # seconds
    recovery_timeout: float = 30.0  # seconds
    max_concurrent_faults: int = 5

class FaultDetector:
    """
    Comprehensive fault detection and recovery system for KPP power system.
    Handles system monitoring, fault identification, alarm generation, and recovery procedures.
    """
    
    def __init__(self, config: Optional[FaultConfig] = None):
        """
        Initialize the fault detector.
        
        Args:
            config: Fault detector configuration
        """
        self.config = config or FaultConfig()
        self.logger = logging.getLogger(__name__)
        
        # System state
        self.fault_state = FaultState.NORMAL
        self.monitoring_active = False
        
        # Performance tracking
        self.performance_metrics = {
            'total_faults_detected': 0,
            'faults_resolved': 0,
            'average_fault_resolution_time': 0.0,  # seconds
            'false_alarms': 0,
            'emergency_shutdowns': 0,
            'operating_hours': 0.0,  # hours
            'system_availability': 100.0  # %
        }
        
        # Fault tracking
        self.active_faults: List[FaultEvent] = []
        self.fault_history: List[FaultEvent] = []
        self.alarm_history: List[AlarmEvent] = []
        self.recovery_history: List[Dict[str, Any]] = []
        
        # Monitoring parameters
        self.monitoring_thresholds = {
            'electrical': {
                'voltage_deviation': 0.1,  # 10%
                'frequency_deviation': 0.5,  # Hz
                'current_overload': 1.2,  # 120%
                'power_factor_low': 0.8
            },
            'mechanical': {
                'speed_deviation': 0.1,  # 10%
                'vibration_high': 10.0,  # mm/s
                'temperature_high': 80.0,  # °C
                'pressure_high': 1.5  # bar
            },
            'thermal': {
                'temperature_critical': 100.0,  # °C
                'thermal_gradient': 20.0,  # °C/min
                'cooling_failure': 0.0  # °C
            },
            'control': {
                'response_time_slow': 1.0,  # seconds
                'control_error_high': 0.1,  # 10%
                'communication_failure': 5.0  # seconds
            }
        }
        
        # Recovery procedures
        self.recovery_procedures = {
            FaultType.ELECTRICAL: self._recover_electrical_fault,
            FaultType.MECHANICAL: self._recover_mechanical_fault,
            FaultType.THERMAL: self._recover_thermal_fault,
            FaultType.CONTROL: self._recover_control_fault,
            FaultType.GRID: self._recover_grid_fault,
            FaultType.SAFETY: self._recover_safety_fault
        }
        
        # Emergency shutdown procedures
        self.emergency_procedures = {
            'immediate_shutdown': self._immediate_shutdown,
            'controlled_shutdown': self._controlled_shutdown,
            'isolation_shutdown': self._isolation_shutdown
        }
        
        self.logger.info("Fault detector initialized")
    
    def start_monitoring(self) -> bool:
        """
        Start fault monitoring.
        
        Returns:
            True if monitoring started successfully
        """
        try:
            if self.monitoring_active:
                self.logger.warning("Monitoring already active")
                return False
            
            self.monitoring_active = True
            self.fault_state = FaultState.MONITORING
            
            self.logger.info("Fault monitoring started")
            return True
            
        except Exception as e:
            self.logger.error("Error starting monitoring: %s", e)
            self._handle_fault("monitoring_start_error", str(e))
            return False
    
    def stop_monitoring(self) -> bool:
        """
        Stop fault monitoring.
        
        Returns:
            True if monitoring stopped successfully
        """
        try:
            if not self.monitoring_active:
                self.logger.warning("Monitoring not active")
                return False
            
            self.monitoring_active = False
            self.fault_state = FaultState.NORMAL
            
            self.logger.info("Fault monitoring stopped")
            return True
            
        except Exception as e:
            self.logger.error("Error stopping monitoring: %s", e)
            return False
    
    def monitor_system_parameters(self, electrical_params: Dict[str, float],
                                 mechanical_params: Dict[str, float],
                                 thermal_params: Dict[str, float],
                                 control_params: Dict[str, float]) -> bool:
        """
        Monitor system parameters for faults.
        
        Args:
            electrical_params: Electrical system parameters
            mechanical_params: Mechanical system parameters
            thermal_params: Thermal system parameters
            control_params: Control system parameters
            
        Returns:
            True if monitoring successful
        """
        try:
            if not self.monitoring_active:
                return False
            
            # Check electrical parameters
            self._check_electrical_faults(electrical_params)
            
            # Check mechanical parameters
            self._check_mechanical_faults(mechanical_params)
            
            # Check thermal parameters
            self._check_thermal_faults(thermal_params)
            
            # Check control parameters
            self._check_control_faults(control_params)
            
            # Update performance metrics
            self._update_performance_metrics()
            
            # Execute recovery procedures if needed
            if self.config.auto_recovery_enabled:
                self._execute_recovery_procedures()
            
            return True
            
        except Exception as e:
            self.logger.error("Error monitoring system parameters: %s", e)
            self._handle_fault("monitoring_error", str(e))
            return False
    
    def _check_electrical_faults(self, params: Dict[str, float]) -> None:
        """
        Check for electrical faults.
        
        Args:
            params: Electrical parameters
        """
        try:
            thresholds = self.monitoring_thresholds['electrical']
            
            # Check voltage deviation
            if 'voltage' in params and 'nominal_voltage' in params:
                voltage_deviation = abs(params['voltage'] - params['nominal_voltage']) / params['nominal_voltage']
                if voltage_deviation > thresholds['voltage_deviation']:
                    self._detect_fault(FaultType.ELECTRICAL, FaultSeverity.MEDIUM,
                                     f"Voltage deviation: {voltage_deviation:.1%}",
                                     {'voltage': params['voltage'], 'deviation': voltage_deviation})
            
            # Check frequency deviation
            if 'frequency' in params and 'nominal_frequency' in params:
                frequency_deviation = abs(params['frequency'] - params['nominal_frequency'])
                if frequency_deviation > thresholds['frequency_deviation']:
                    self._detect_fault(FaultType.ELECTRICAL, FaultSeverity.MEDIUM,
                                     f"Frequency deviation: {frequency_deviation:.1f} Hz",
                                     {'frequency': params['frequency'], 'deviation': frequency_deviation})
            
            # Check current overload
            if 'current' in params and 'rated_current' in params:
                current_ratio = params['current'] / params['rated_current']
                if current_ratio > thresholds['current_overload']:
                    self._detect_fault(FaultType.ELECTRICAL, FaultSeverity.HIGH,
                                     f"Current overload: {current_ratio:.1%}",
                                     {'current': params['current'], 'ratio': current_ratio})
            
            # Check power factor
            if 'power_factor' in params:
                if params['power_factor'] < thresholds['power_factor_low']:
                    self._detect_fault(FaultType.ELECTRICAL, FaultSeverity.LOW,
                                     f"Low power factor: {params['power_factor']:.2f}",
                                     {'power_factor': params['power_factor']})
            
        except Exception as e:
            self.logger.error("Error checking electrical faults: %s", e)
    
    def _check_mechanical_faults(self, params: Dict[str, float]) -> None:
        """
        Check for mechanical faults.
        
        Args:
            params: Mechanical parameters
        """
        try:
            thresholds = self.monitoring_thresholds['mechanical']
            
            # Check speed deviation
            if 'speed' in params and 'nominal_speed' in params:
                speed_deviation = abs(params['speed'] - params['nominal_speed']) / params['nominal_speed']
                if speed_deviation > thresholds['speed_deviation']:
                    self._detect_fault(FaultType.MECHANICAL, FaultSeverity.MEDIUM,
                                     f"Speed deviation: {speed_deviation:.1%}",
                                     {'speed': params['speed'], 'deviation': speed_deviation})
            
            # Check vibration
            if 'vibration' in params:
                if params['vibration'] > thresholds['vibration_high']:
                    self._detect_fault(FaultType.MECHANICAL, FaultSeverity.HIGH,
                                     f"High vibration: {params['vibration']:.1f} mm/s",
                                     {'vibration': params['vibration']})
            
            # Check temperature
            if 'temperature' in params:
                if params['temperature'] > thresholds['temperature_high']:
                    self._detect_fault(FaultType.MECHANICAL, FaultSeverity.MEDIUM,
                                     f"High temperature: {params['temperature']:.1f}°C",
                                     {'temperature': params['temperature']})
            
            # Check pressure
            if 'pressure' in params:
                if params['pressure'] > thresholds['pressure_high']:
                    self._detect_fault(FaultType.MECHANICAL, FaultSeverity.HIGH,
                                     f"High pressure: {params['pressure']:.1f} bar",
                                     {'pressure': params['pressure']})
            
        except Exception as e:
            self.logger.error("Error checking mechanical faults: %s", e)
    
    def _check_thermal_faults(self, params: Dict[str, float]) -> None:
        """
        Check for thermal faults.
        
        Args:
            params: Thermal parameters
        """
        try:
            thresholds = self.monitoring_thresholds['thermal']
            
            # Check critical temperature
            if 'temperature' in params:
                if params['temperature'] > thresholds['temperature_critical']:
                    self._detect_fault(FaultType.THERMAL, FaultSeverity.CRITICAL,
                                     f"Critical temperature: {params['temperature']:.1f}°C",
                                     {'temperature': params['temperature']})
            
            # Check thermal gradient
            if 'thermal_gradient' in params:
                if abs(params['thermal_gradient']) > thresholds['thermal_gradient']:
                    self._detect_fault(FaultType.THERMAL, FaultSeverity.HIGH,
                                     f"High thermal gradient: {params['thermal_gradient']:.1f}°C/min",
                                     {'thermal_gradient': params['thermal_gradient']})
            
            # Check cooling failure
            if 'cooling_temperature' in params:
                if params['cooling_temperature'] > thresholds['cooling_failure']:
                    self._detect_fault(FaultType.THERMAL, FaultSeverity.HIGH,
                                     f"Cooling failure: {params['cooling_temperature']:.1f}°C",
                                     {'cooling_temperature': params['cooling_temperature']})
            
        except Exception as e:
            self.logger.error("Error checking thermal faults: %s", e)
    
    def _check_control_faults(self, params: Dict[str, float]) -> None:
        """
        Check for control faults.
        
        Args:
            params: Control parameters
        """
        try:
            thresholds = self.monitoring_thresholds['control']
            
            # Check response time
            if 'response_time' in params:
                if params['response_time'] > thresholds['response_time_slow']:
                    self._detect_fault(FaultType.CONTROL, FaultSeverity.MEDIUM,
                                     f"Slow response time: {params['response_time']:.1f} s",
                                     {'response_time': params['response_time']})
            
            # Check control error
            if 'control_error' in params:
                if params['control_error'] > thresholds['control_error_high']:
                    self._detect_fault(FaultType.CONTROL, FaultSeverity.MEDIUM,
                                     f"High control error: {params['control_error']:.1%}",
                                     {'control_error': params['control_error']})
            
            # Check communication failure
            if 'communication_delay' in params:
                if params['communication_delay'] > thresholds['communication_failure']:
                    self._detect_fault(FaultType.CONTROL, FaultSeverity.HIGH,
                                     f"Communication failure: {params['communication_delay']:.1f} s",
                                     {'communication_delay': params['communication_delay']})
            
        except Exception as e:
            self.logger.error("Error checking control faults: %s", e)
    
    def _detect_fault(self, fault_type: FaultType, severity: FaultSeverity,
                     message: str, parameters: Dict[str, Any]) -> None:
        """
        Detect and record a fault.
        
        Args:
            fault_type: Type of fault
            severity: Fault severity
            message: Fault message
            parameters: Fault parameters
        """
        try:
            # Create fault event
            fault_event = FaultEvent(
                fault_type=fault_type,
                severity=severity,
                timestamp=time.time(),
                message=message,
                parameters=parameters
            )
            
            # Add to active faults
            self.active_faults.append(fault_event)
            
            # Add to fault history
            self.fault_history.append(fault_event)
            
            # Update performance metrics
            self.performance_metrics['total_faults_detected'] += 1
            
            # Generate alarm
            self._generate_alarm(fault_event)
            
            # Update fault state
            if severity == FaultSeverity.CRITICAL:
                self.fault_state = FaultState.EMERGENCY
                if self.config.emergency_shutdown_enabled:
                    self._execute_emergency_shutdown("critical_fault")
            elif severity == FaultSeverity.HIGH:
                self.fault_state = FaultState.FAULT
            else:
                self.fault_state = FaultState.ALARM
            
            self.logger.warning("Fault detected: %s - %s (severity: %s)", 
                              fault_type.value, message, severity.value)
            
        except Exception as e:
            self.logger.error("Error detecting fault: %s", e)
    
    def _generate_alarm(self, fault_event: FaultEvent) -> None:
        """
        Generate alarm for fault.
        
        Args:
            fault_event: Fault event
        """
        try:
            # Determine alarm type based on severity
            if fault_event.severity == FaultSeverity.CRITICAL:
                alarm_type = AlarmType.EMERGENCY
            elif fault_event.severity == FaultSeverity.HIGH:
                alarm_type = AlarmType.CRITICAL
            elif fault_event.severity == FaultSeverity.MEDIUM:
                alarm_type = AlarmType.ALERT
            else:
                alarm_type = AlarmType.WARNING
            
            # Create alarm event
            alarm_event = AlarmEvent(
                alarm_type=alarm_type,
                timestamp=time.time(),
                message=fault_event.message,
                parameters=fault_event.parameters
            )
            
            # Add to alarm history
            self.alarm_history.append(alarm_event)
            
            self.logger.warning("Alarm generated: %s - %s", alarm_type.value, fault_event.message)
            
        except Exception as e:
            self.logger.error("Error generating alarm: %s", e)
    
    def _execute_recovery_procedures(self) -> None:
        """Execute recovery procedures for active faults."""
        try:
            if not self.active_faults:
                return
            
            # Group faults by type
            faults_by_type = {}
            for fault in self.active_faults:
                if fault.fault_type not in faults_by_type:
                    faults_by_type[fault.fault_type] = []
                faults_by_type[fault.fault_type].append(fault)
            
            # Execute recovery for each fault type
            for fault_type, faults in faults_by_type.items():
                if fault_type in self.recovery_procedures:
                    recovery_procedure = self.recovery_procedures[fault_type]
                    recovery_procedure(faults)
            
        except Exception as e:
            self.logger.error("Error executing recovery procedures: %s", e)
    
    def _recover_electrical_fault(self, faults: List[FaultEvent]) -> None:
        """
        Recover from electrical faults.
        
        Args:
            faults: List of electrical faults
        """
        try:
            for fault in faults:
                if fault.severity == FaultSeverity.CRITICAL:
                    # Critical electrical fault - immediate shutdown
                    self._execute_emergency_shutdown("critical_electrical_fault")
                elif fault.severity == FaultSeverity.HIGH:
                    # High severity - controlled shutdown
                    self._execute_controlled_shutdown("high_electrical_fault")
                else:
                    # Low/medium severity - attempt recovery
                    self._attempt_electrical_recovery(fault)
            
        except Exception as e:
            self.logger.error("Error recovering electrical fault: %s", e)
    
    def _recover_mechanical_fault(self, faults: List[FaultEvent]) -> None:
        """
        Recover from mechanical faults.
        
        Args:
            faults: List of mechanical faults
        """
        try:
            for fault in faults:
                if fault.severity == FaultSeverity.CRITICAL:
                    # Critical mechanical fault - immediate shutdown
                    self._execute_emergency_shutdown("critical_mechanical_fault")
                elif fault.severity == FaultSeverity.HIGH:
                    # High severity - controlled shutdown
                    self._execute_controlled_shutdown("high_mechanical_fault")
                else:
                    # Low/medium severity - attempt recovery
                    self._attempt_mechanical_recovery(fault)
            
        except Exception as e:
            self.logger.error("Error recovering mechanical fault: %s", e)
    
    def _recover_thermal_fault(self, faults: List[FaultEvent]) -> None:
        """
        Recover from thermal faults.
        
        Args:
            faults: List of thermal faults
        """
        try:
            for fault in faults:
                if fault.severity == FaultSeverity.CRITICAL:
                    # Critical thermal fault - immediate shutdown
                    self._execute_emergency_shutdown("critical_thermal_fault")
                elif fault.severity == FaultSeverity.HIGH:
                    # High severity - controlled shutdown
                    self._execute_controlled_shutdown("high_thermal_fault")
                else:
                    # Low/medium severity - attempt recovery
                    self._attempt_thermal_recovery(fault)
            
        except Exception as e:
            self.logger.error("Error recovering thermal fault: %s", e)
    
    def _recover_control_fault(self, faults: List[FaultEvent]) -> None:
        """
        Recover from control faults.
        
        Args:
            faults: List of control faults
        """
        try:
            for fault in faults:
                if fault.severity == FaultSeverity.CRITICAL:
                    # Critical control fault - immediate shutdown
                    self._execute_emergency_shutdown("critical_control_fault")
                elif fault.severity == FaultSeverity.HIGH:
                    # High severity - controlled shutdown
                    self._execute_controlled_shutdown("high_control_fault")
                else:
                    # Low/medium severity - attempt recovery
                    self._attempt_control_recovery(fault)
            
        except Exception as e:
            self.logger.error("Error recovering control fault: %s", e)
    
    def _recover_grid_fault(self, faults: List[FaultEvent]) -> None:
        """
        Recover from grid faults.
        
        Args:
            faults: List of grid faults
        """
        try:
            for fault in faults:
                if fault.severity == FaultSeverity.CRITICAL:
                    # Critical grid fault - immediate shutdown
                    self._execute_emergency_shutdown("critical_grid_fault")
                elif fault.severity == FaultSeverity.HIGH:
                    # High severity - controlled shutdown
                    self._execute_controlled_shutdown("high_grid_fault")
                else:
                    # Low/medium severity - attempt recovery
                    self._attempt_grid_recovery(fault)
            
        except Exception as e:
            self.logger.error("Error recovering grid fault: %s", e)
    
    def _recover_safety_fault(self, faults: List[FaultEvent]) -> None:
        """
        Recover from safety faults.
        
        Args:
            faults: List of safety faults
        """
        try:
            for fault in faults:
                # All safety faults require immediate shutdown
                self._execute_emergency_shutdown("safety_fault")
            
        except Exception as e:
            self.logger.error("Error recovering safety fault: %s", e)
    
    def _attempt_electrical_recovery(self, fault: FaultEvent) -> None:
        """
        Attempt electrical fault recovery.
        
        Args:
            fault: Electrical fault event
        """
        try:
            # Simplified recovery procedure
            # In practice, this would implement specific electrical recovery steps
            
            self.logger.info("Attempting electrical recovery: %s", fault.message)
            
            # Simulate recovery success
            if fault.severity == FaultSeverity.LOW:
                self._resolve_fault(fault)
            
        except Exception as e:
            self.logger.error("Error attempting electrical recovery: %s", e)
    
    def _attempt_mechanical_recovery(self, fault: FaultEvent) -> None:
        """
        Attempt mechanical fault recovery.
        
        Args:
            fault: Mechanical fault event
        """
        try:
            # Simplified recovery procedure
            # In practice, this would implement specific mechanical recovery steps
            
            self.logger.info("Attempting mechanical recovery: %s", fault.message)
            
            # Simulate recovery success
            if fault.severity == FaultSeverity.LOW:
                self._resolve_fault(fault)
            
        except Exception as e:
            self.logger.error("Error attempting mechanical recovery: %s", e)
    
    def _attempt_thermal_recovery(self, fault: FaultEvent) -> None:
        """
        Attempt thermal fault recovery.
        
        Args:
            fault: Thermal fault event
        """
        try:
            # Simplified recovery procedure
            # In practice, this would implement specific thermal recovery steps
            
            self.logger.info("Attempting thermal recovery: %s", fault.message)
            
            # Simulate recovery success
            if fault.severity == FaultSeverity.LOW:
                self._resolve_fault(fault)
            
        except Exception as e:
            self.logger.error("Error attempting thermal recovery: %s", e)
    
    def _attempt_control_recovery(self, fault: FaultEvent) -> None:
        """
        Attempt control fault recovery.
        
        Args:
            fault: Control fault event
        """
        try:
            # Simplified recovery procedure
            # In practice, this would implement specific control recovery steps
            
            self.logger.info("Attempting control recovery: %s", fault.message)
            
            # Simulate recovery success
            if fault.severity == FaultSeverity.LOW:
                self._resolve_fault(fault)
            
        except Exception as e:
            self.logger.error("Error attempting control recovery: %s", e)
    
    def _attempt_grid_recovery(self, fault: FaultEvent) -> None:
        """
        Attempt grid fault recovery.
        
        Args:
            fault: Grid fault event
        """
        try:
            # Simplified recovery procedure
            # In practice, this would implement specific grid recovery steps
            
            self.logger.info("Attempting grid recovery: %s", fault.message)
            
            # Simulate recovery success
            if fault.severity == FaultSeverity.LOW:
                self._resolve_fault(fault)
            
        except Exception as e:
            self.logger.error("Error attempting grid recovery: %s", e)
    
    def _resolve_fault(self, fault: FaultEvent) -> None:
        """
        Resolve a fault.
        
        Args:
            fault: Fault event to resolve
        """
        try:
            # Mark fault as resolved
            fault.resolved = True
            fault.resolution_time = time.time()
            
            # Remove from active faults
            if fault in self.active_faults:
                self.active_faults.remove(fault)
            
            # Update performance metrics
            self.performance_metrics['faults_resolved'] += 1
            
            # Calculate resolution time
            resolution_time = fault.resolution_time - fault.timestamp
            self.performance_metrics['average_fault_resolution_time'] = (
                (self.performance_metrics['average_fault_resolution_time'] + resolution_time) / 2
            )
            
            # Record recovery
            recovery_record = {
                'timestamp': time.time(),
                'fault_type': fault.fault_type.value,
                'severity': fault.severity.value,
                'resolution_time': resolution_time,
                'message': fault.message
            }
            self.recovery_history.append(recovery_record)
            
            # Update fault state if no more active faults
            if not self.active_faults:
                self.fault_state = FaultState.NORMAL
            
            self.logger.info("Fault resolved: %s (resolution time: %.1f s)", 
                           fault.message, resolution_time)
            
        except Exception as e:
            self.logger.error("Error resolving fault: %s", e)
    
    def _execute_emergency_shutdown(self, reason: str) -> None:
        """
        Execute emergency shutdown.
        
        Args:
            reason: Reason for emergency shutdown
        """
        try:
            self.logger.critical("EMERGENCY SHUTDOWN: %s", reason)
            
            # Update performance metrics
            self.performance_metrics['emergency_shutdowns'] += 1
            
            # Update fault state
            self.fault_state = FaultState.EMERGENCY
            
            # Record emergency shutdown
            emergency_record = {
                'timestamp': time.time(),
                'reason': reason,
                'type': 'emergency_shutdown'
            }
            self.recovery_history.append(emergency_record)
            
            # In practice, this would execute actual emergency shutdown procedures
            self.logger.critical("Emergency shutdown procedures executed")
            
        except Exception as e:
            self.logger.error("Error executing emergency shutdown: %s", e)
    
    def _execute_controlled_shutdown(self, reason: str) -> None:
        """
        Execute controlled shutdown.
        
        Args:
            reason: Reason for controlled shutdown
        """
        try:
            self.logger.warning("CONTROLLED SHUTDOWN: %s", reason)
            
            # Update fault state
            self.fault_state = FaultState.FAULT
            
            # Record controlled shutdown
            shutdown_record = {
                'timestamp': time.time(),
                'reason': reason,
                'type': 'controlled_shutdown'
            }
            self.recovery_history.append(shutdown_record)
            
            # In practice, this would execute actual controlled shutdown procedures
            self.logger.warning("Controlled shutdown procedures executed")
            
        except Exception as e:
            self.logger.error("Error executing controlled shutdown: %s", e)
    
    def _immediate_shutdown(self) -> None:
        """Execute immediate shutdown procedure."""
        try:
            self.logger.critical("IMMEDIATE SHUTDOWN EXECUTED")
            # In practice, this would execute immediate shutdown procedures
            
        except Exception as e:
            self.logger.error("Error executing immediate shutdown: %s", e)
    
    def _controlled_shutdown(self) -> None:
        """Execute controlled shutdown procedure."""
        try:
            self.logger.warning("CONTROLLED SHUTDOWN EXECUTED")
            # In practice, this would execute controlled shutdown procedures
            
        except Exception as e:
            self.logger.error("Error executing controlled shutdown: %s", e)
    
    def _isolation_shutdown(self) -> None:
        """Execute isolation shutdown procedure."""
        try:
            self.logger.warning("ISOLATION SHUTDOWN EXECUTED")
            # In practice, this would execute isolation shutdown procedures
            
        except Exception as e:
            self.logger.error("Error executing isolation shutdown: %s", e)
    
    def _update_performance_metrics(self) -> None:
        """Update performance metrics."""
        try:
            # Update operating hours
            self.performance_metrics['operating_hours'] += 0.001  # hours
            
            # Calculate system availability
            total_faults = self.performance_metrics['total_faults_detected']
            resolved_faults = self.performance_metrics['faults_resolved']
            
            if total_faults > 0:
                availability = (resolved_faults / total_faults) * 100
                self.performance_metrics['system_availability'] = min(100.0, availability)
            
        except Exception as e:
            self.logger.error("Error updating performance metrics: %s", e)
    
    def _handle_fault(self, fault_type: str, fault_message: str) -> None:
        """
        Handle fault detector faults.
        
        Args:
            fault_type: Type of fault
            fault_message: Fault message
        """
        try:
            self.logger.error("Fault detector fault: %s - %s", fault_type, fault_message)
            
            # Update fault state
            self.fault_state = FaultState.FAULT
            
            # Record fault
            self._detect_fault(FaultType.CONTROL, FaultSeverity.HIGH,
                             f"Fault detector error: {fault_type}", 
                             {'error_type': fault_type, 'message': fault_message})
            
        except Exception as e:
            self.logger.error("Error handling fault detector fault: %s", e)
    
    def get_fault_state(self) -> FaultState:
        """
        Get current fault state.
        
        Returns:
            Current fault state
        """
        return self.fault_state
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Get performance metrics.
        
        Returns:
            Performance metrics dictionary
        """
        return self.performance_metrics.copy()
    
    def get_active_faults(self) -> List[FaultEvent]:
        """
        Get active faults.
        
        Returns:
            List of active fault events
        """
        return self.active_faults.copy()
    
    def get_fault_history(self, limit: Optional[int] = None) -> List[FaultEvent]:
        """
        Get fault history.
        
        Args:
            limit: Maximum number of faults to return
            
        Returns:
            List of fault events
        """
        if limit is None:
            return self.fault_history.copy()
        else:
            return self.fault_history[-limit:]
    
    def get_alarm_history(self, limit: Optional[int] = None) -> List[AlarmEvent]:
        """
        Get alarm history.
        
        Args:
            limit: Maximum number of alarms to return
            
        Returns:
            List of alarm events
        """
        if limit is None:
            return self.alarm_history.copy()
        else:
            return self.alarm_history[-limit:]
    
    def get_recovery_history(self) -> List[Dict[str, Any]]:
        """
        Get recovery history.
        
        Returns:
            List of recovery records
        """
        return self.recovery_history.copy()
    
    def is_monitoring_active(self) -> bool:
        """
        Check if monitoring is active.
        
        Returns:
            True if monitoring is active
        """
        return self.monitoring_active
    
    def acknowledge_alarm(self, alarm_index: int) -> bool:
        """
        Acknowledge an alarm.
        
        Args:
            alarm_index: Index of alarm to acknowledge
            
        Returns:
            True if alarm acknowledged successfully
        """
        try:
            if 0 <= alarm_index < len(self.alarm_history):
                alarm = self.alarm_history[alarm_index]
                alarm.acknowledged = True
                alarm.acknowledgment_time = time.time()
                
                self.logger.info("Alarm acknowledged: %s", alarm.message)
                return True
            else:
                self.logger.warning("Invalid alarm index: %d", alarm_index)
                return False
                
        except Exception as e:
            self.logger.error("Error acknowledging alarm: %s", e)
            return False
    
    def reset(self) -> None:
        """Reset fault detector to initial state."""
        self.fault_state = FaultState.NORMAL
        self.monitoring_active = False
        self.active_faults.clear()
        self.fault_history.clear()
        self.alarm_history.clear()
        self.recovery_history.clear()
        self.performance_metrics = {
            'total_faults_detected': 0,
            'faults_resolved': 0,
            'average_fault_resolution_time': 0.0,
            'false_alarms': 0,
            'emergency_shutdowns': 0,
            'operating_hours': 0.0,
            'system_availability': 100.0
        }
        self.logger.info("Fault detector reset")

