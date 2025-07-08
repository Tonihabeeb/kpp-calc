import numpy as np
import logging
import time
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
from dataclasses import dataclass
from collections import deque

"""
Grid Disturbance Handler for KPP System
Handles grid frequency and voltage disturbances with appropriate responses.
"""

class DisturbanceState(str, Enum):
    """Grid disturbance state enumeration"""
    NORMAL = "normal"
    MONITORING = "monitoring"
    DETECTED = "detected"
    RESPONDING = "responding"
    RECOVERING = "recovering"
    FAULT = "fault"

class DisturbanceType(str, Enum):
    """Grid disturbance type enumeration"""
    FREQUENCY_DROP = "frequency_drop"
    FREQUENCY_RISE = "frequency_rise"
    VOLTAGE_DROP = "voltage_drop"
    VOLTAGE_RISE = "voltage_rise"
    FREQUENCY_OSCILLATION = "frequency_oscillation"
    VOLTAGE_OSCILLATION = "voltage_oscillation"
    POWER_QUALITY = "power_quality"
    GRID_FAULT = "grid_fault"

class DisturbanceSeverity(str, Enum):
    """Disturbance severity enumeration"""
    MINOR = "minor"
    MODERATE = "moderate"
    MAJOR = "major"
    CRITICAL = "critical"

class ResponseType(str, Enum):
    """Response type enumeration"""
    AUTOMATIC = "automatic"
    MANUAL = "manual"
    COORDINATED = "coordinated"
    EMERGENCY = "emergency"

@dataclass
class DisturbanceEvent:
    """Disturbance event data structure"""
    disturbance_type: DisturbanceType
    severity: DisturbanceSeverity
    timestamp: float
    duration: float  # seconds
    magnitude: float
    parameters: Dict[str, Any]
    resolved: bool = False
    resolution_time: Optional[float] = None

@dataclass
class ResponseAction:
    """Response action data structure"""
    action_type: str
    timestamp: float
    parameters: Dict[str, Any]
    success: bool
    response_time: float  # seconds

@dataclass
class DisturbanceConfig:
    """Grid disturbance handler configuration"""
    monitoring_enabled: bool = True
    auto_response_enabled: bool = True
    coordination_enabled: bool = True
    detection_threshold: float = 0.1  # Hz for frequency, 5% for voltage
    response_timeout: float = 30.0  # seconds
    recovery_timeout: float = 60.0  # seconds

class GridDisturbanceHandler:
    """
    Comprehensive grid disturbance handler for KPP power system.
    Handles disturbance detection, classification, response coordination, and recovery procedures.
    """
    
    def __init__(self, config: Optional[DisturbanceConfig] = None):
        """
        Initialize the grid disturbance handler.
        
        Args:
            config: Grid disturbance handler configuration
        """
        self.config = config or DisturbanceConfig()
        self.logger = logging.getLogger(__name__)
        
        # System state
        self.disturbance_state = DisturbanceState.NORMAL
        self.monitoring_active = False
        
        # Performance tracking
        self.performance_metrics = {
            'total_disturbances': 0,
            'disturbances_resolved': 0,
            'average_response_time': 0.0,  # seconds
            'response_success_rate': 100.0,  # %
            'grid_stability_score': 100.0,  # 0-100
            'operating_hours': 0.0,  # hours
            'coordination_events': 0
        }
        
        # Disturbance tracking
        self.active_disturbances: List[DisturbanceEvent] = []
        self.disturbance_history: List[DisturbanceEvent] = []
        self.response_history: List[ResponseAction] = []
        
        # Detection thresholds
        self.detection_thresholds = {
            DisturbanceType.FREQUENCY_DROP: {
                'minor': 0.1,      # Hz
                'moderate': 0.3,   # Hz
                'major': 0.5,      # Hz
                'critical': 1.0    # Hz
            },
            DisturbanceType.FREQUENCY_RISE: {
                'minor': 0.1,      # Hz
                'moderate': 0.3,   # Hz
                'major': 0.5,      # Hz
                'critical': 1.0    # Hz
            },
            DisturbanceType.VOLTAGE_DROP: {
                'minor': 0.05,     # 5%
                'moderate': 0.10,  # 10%
                'major': 0.15,     # 15%
                'critical': 0.20   # 20%
            },
            DisturbanceType.VOLTAGE_RISE: {
                'minor': 0.05,     # 5%
                'moderate': 0.10,  # 10%
                'major': 0.15,     # 15%
                'critical': 0.20   # 20%
            }
        }
        
        # Response procedures
        self.response_procedures = {
            DisturbanceType.FREQUENCY_DROP: self._respond_to_frequency_drop,
            DisturbanceType.FREQUENCY_RISE: self._respond_to_frequency_rise,
            DisturbanceType.VOLTAGE_DROP: self._respond_to_voltage_drop,
            DisturbanceType.VOLTAGE_RISE: self._respond_to_voltage_rise,
            DisturbanceType.FREQUENCY_OSCILLATION: self._respond_to_frequency_oscillation,
            DisturbanceType.VOLTAGE_OSCILLATION: self._respond_to_voltage_oscillation,
            DisturbanceType.POWER_QUALITY: self._respond_to_power_quality,
            DisturbanceType.GRID_FAULT: self._respond_to_grid_fault
        }
        
        # Recovery procedures
        self.recovery_procedures = {
            DisturbanceType.FREQUENCY_DROP: self._recover_from_frequency_drop,
            DisturbanceType.FREQUENCY_RISE: self._recover_from_frequency_rise,
            DisturbanceType.VOLTAGE_DROP: self._recover_from_voltage_drop,
            DisturbanceType.VOLTAGE_RISE: self._recover_from_voltage_rise,
            DisturbanceType.FREQUENCY_OSCILLATION: self._recover_from_frequency_oscillation,
            DisturbanceType.VOLTAGE_OSCILLATION: self._recover_from_voltage_oscillation,
            DisturbanceType.POWER_QUALITY: self._recover_from_power_quality,
            DisturbanceType.GRID_FAULT: self._recover_from_grid_fault
        }
        
        # Response tracking
        self.response_start_time: Optional[float] = None
        self.recovery_start_time: Optional[float] = None
        
        # Grid parameters history
        self.grid_history: deque = deque(maxlen=1000)
        
        self.logger.info("Grid disturbance handler initialized")
    
    def start_monitoring(self) -> bool:
        """
        Start grid disturbance monitoring.
        
        Returns:
            True if monitoring started successfully
        """
        try:
            if self.monitoring_active:
                self.logger.warning("Monitoring already active")
                return False
            
            self.monitoring_active = True
            self.disturbance_state = DisturbanceState.MONITORING
            
            self.logger.info("Grid disturbance monitoring started")
            return True
            
        except Exception as e:
            self.logger.error("Error starting monitoring: %s", e)
            return False
    
    def stop_monitoring(self) -> bool:
        """
        Stop grid disturbance monitoring.
        
        Returns:
            True if monitoring stopped successfully
        """
        try:
            if not self.monitoring_active:
                self.logger.warning("Monitoring not active")
                return False
            
            self.monitoring_active = False
            self.disturbance_state = DisturbanceState.NORMAL
            
            self.logger.info("Grid disturbance monitoring stopped")
            return True
            
        except Exception as e:
            self.logger.error("Error stopping monitoring: %s", e)
            return False
    
    def monitor_grid_parameters(self, frequency: float, voltage: float, 
                               power_factor: float, harmonic_distortion: float) -> bool:
        """
        Monitor grid parameters for disturbances.
        
        Args:
            frequency: Grid frequency (Hz)
            voltage: Grid voltage (V)
            power_factor: Power factor (0-1)
            harmonic_distortion: Harmonic distortion (%)
            
        Returns:
            True if monitoring successful
        """
        try:
            if not self.monitoring_active:
                return False
            
            # Record grid parameters
            self._record_grid_parameters(frequency, voltage, power_factor, harmonic_distortion)
            
            # Check for disturbances
            self._check_frequency_disturbances(frequency)
            self._check_voltage_disturbances(voltage)
            self._check_power_quality_disturbances(power_factor, harmonic_distortion)
            
            # Execute response procedures if needed
            if self.active_disturbances and self.config.auto_response_enabled:
                self._execute_response_procedures()
            
            # Execute recovery procedures if needed
            if self.config.coordination_enabled:
                self._execute_recovery_procedures()
            
            # Update performance metrics
            self._update_performance_metrics()
            
            return True
            
        except Exception as e:
            self.logger.error("Error monitoring grid parameters: %s", e)
            return False
    
    def _record_grid_parameters(self, frequency: float, voltage: float,
                               power_factor: float, harmonic_distortion: float) -> None:
        """
        Record grid parameters.
        
        Args:
            frequency: Grid frequency (Hz)
            voltage: Grid voltage (V)
            power_factor: Power factor (0-1)
            harmonic_distortion: Harmonic distortion (%)
        """
        try:
            grid_record = {
                'timestamp': time.time(),
                'frequency': frequency,
                'voltage': voltage,
                'power_factor': power_factor,
                'harmonic_distortion': harmonic_distortion
            }
            
            self.grid_history.append(grid_record)
            
        except Exception as e:
            self.logger.error("Error recording grid parameters: %s", e)
    
    def _check_frequency_disturbances(self, frequency: float) -> None:
        """
        Check for frequency disturbances.
        
        Args:
            frequency: Grid frequency (Hz)
        """
        try:
            nominal_frequency = 50.0  # Hz
            frequency_error = frequency - nominal_frequency
            
            # Check for frequency drop
            if frequency_error < 0:
                magnitude = abs(frequency_error)
                if magnitude >= self.detection_thresholds[DisturbanceType.FREQUENCY_DROP]['minor']:
                    severity = self._classify_frequency_severity(magnitude, DisturbanceType.FREQUENCY_DROP)
                    self._detect_disturbance(DisturbanceType.FREQUENCY_DROP, severity, magnitude, 
                                          {'frequency': frequency, 'error': frequency_error})
            
            # Check for frequency rise
            elif frequency_error > 0:
                magnitude = frequency_error
                if magnitude >= self.detection_thresholds[DisturbanceType.FREQUENCY_RISE]['minor']:
                    severity = self._classify_frequency_severity(magnitude, DisturbanceType.FREQUENCY_RISE)
                    self._detect_disturbance(DisturbanceType.FREQUENCY_RISE, severity, magnitude,
                                          {'frequency': frequency, 'error': frequency_error})
            
        except Exception as e:
            self.logger.error("Error checking frequency disturbances: %s", e)
    
    def _check_voltage_disturbances(self, voltage: float) -> None:
        """
        Check for voltage disturbances.
        
        Args:
            voltage: Grid voltage (V)
        """
        try:
            nominal_voltage = 400.0  # V (line-to-line)
            voltage_error = (voltage - nominal_voltage) / nominal_voltage
            
            # Check for voltage drop
            if voltage_error < 0:
                magnitude = abs(voltage_error)
                if magnitude >= self.detection_thresholds[DisturbanceType.VOLTAGE_DROP]['minor']:
                    severity = self._classify_voltage_severity(magnitude, DisturbanceType.VOLTAGE_DROP)
                    self._detect_disturbance(DisturbanceType.VOLTAGE_DROP, severity, magnitude,
                                          {'voltage': voltage, 'error': voltage_error})
            
            # Check for voltage rise
            elif voltage_error > 0:
                magnitude = voltage_error
                if magnitude >= self.detection_thresholds[DisturbanceType.VOLTAGE_RISE]['minor']:
                    severity = self._classify_voltage_severity(magnitude, DisturbanceType.VOLTAGE_RISE)
                    self._detect_disturbance(DisturbanceType.VOLTAGE_RISE, severity, magnitude,
                                          {'voltage': voltage, 'error': voltage_error})
            
        except Exception as e:
            self.logger.error("Error checking voltage disturbances: %s", e)
    
    def _check_power_quality_disturbances(self, power_factor: float, harmonic_distortion: float) -> None:
        """
        Check for power quality disturbances.
        
        Args:
            power_factor: Power factor (0-1)
            harmonic_distortion: Harmonic distortion (%)
        """
        try:
            # Check power factor
            if power_factor < 0.9:  # Low power factor
                magnitude = 1.0 - power_factor
                severity = self._classify_power_quality_severity(magnitude)
                self._detect_disturbance(DisturbanceType.POWER_QUALITY, severity, magnitude,
                                      {'power_factor': power_factor, 'type': 'low_power_factor'})
            
            # Check harmonic distortion
            if harmonic_distortion > 5.0:  # High harmonic distortion
                magnitude = harmonic_distortion
                severity = self._classify_power_quality_severity(magnitude / 10.0)  # Normalize
                self._detect_disturbance(DisturbanceType.POWER_QUALITY, severity, magnitude,
                                      {'harmonic_distortion': harmonic_distortion, 'type': 'high_harmonics'})
            
        except Exception as e:
            self.logger.error("Error checking power quality disturbances: %s", e)
    
    def _classify_frequency_severity(self, magnitude: float, disturbance_type: DisturbanceType) -> DisturbanceSeverity:
        """
        Classify frequency disturbance severity.
        
        Args:
            magnitude: Disturbance magnitude
            disturbance_type: Type of frequency disturbance
            
        Returns:
            Disturbance severity
        """
        try:
            thresholds = self.detection_thresholds[disturbance_type]
            
            if magnitude >= thresholds['critical']:
                return DisturbanceSeverity.CRITICAL
            elif magnitude >= thresholds['major']:
                return DisturbanceSeverity.MAJOR
            elif magnitude >= thresholds['moderate']:
                return DisturbanceSeverity.MODERATE
            else:
                return DisturbanceSeverity.MINOR
                
        except Exception as e:
            self.logger.error("Error classifying frequency severity: %s", e)
            return DisturbanceSeverity.MINOR
    
    def _classify_voltage_severity(self, magnitude: float, disturbance_type: DisturbanceType) -> DisturbanceSeverity:
        """
        Classify voltage disturbance severity.
        
        Args:
            magnitude: Disturbance magnitude
            disturbance_type: Type of voltage disturbance
            
        Returns:
            Disturbance severity
        """
        try:
            thresholds = self.detection_thresholds[disturbance_type]
            
            if magnitude >= thresholds['critical']:
                return DisturbanceSeverity.CRITICAL
            elif magnitude >= thresholds['major']:
                return DisturbanceSeverity.MAJOR
            elif magnitude >= thresholds['moderate']:
                return DisturbanceSeverity.MODERATE
            else:
                return DisturbanceSeverity.MINOR
                
        except Exception as e:
            self.logger.error("Error classifying voltage severity: %s", e)
            return DisturbanceSeverity.MINOR
    
    def _classify_power_quality_severity(self, magnitude: float) -> DisturbanceSeverity:
        """
        Classify power quality disturbance severity.
        
        Args:
            magnitude: Disturbance magnitude
            
        Returns:
            Disturbance severity
        """
        try:
            if magnitude >= 0.3:
                return DisturbanceSeverity.CRITICAL
            elif magnitude >= 0.2:
                return DisturbanceSeverity.MAJOR
            elif magnitude >= 0.1:
                return DisturbanceSeverity.MODERATE
            else:
                return DisturbanceSeverity.MINOR
                
        except Exception as e:
            self.logger.error("Error classifying power quality severity: %s", e)
            return DisturbanceSeverity.MINOR
    
    def _detect_disturbance(self, disturbance_type: DisturbanceType, severity: DisturbanceSeverity,
                           magnitude: float, parameters: Dict[str, Any]) -> None:
        """
        Detect and record a grid disturbance.
        
        Args:
            disturbance_type: Type of disturbance
            severity: Disturbance severity
            magnitude: Disturbance magnitude
            parameters: Disturbance parameters
        """
        try:
            # Create disturbance event
            disturbance_event = DisturbanceEvent(
                disturbance_type=disturbance_type,
                severity=severity,
                timestamp=time.time(),
                duration=0.0,  # Will be updated when resolved
                magnitude=magnitude,
                parameters=parameters
            )
            
            # Add to active disturbances
            self.active_disturbances.append(disturbance_event)
            self.disturbance_history.append(disturbance_event)
            
            # Update performance metrics
            self.performance_metrics['total_disturbances'] += 1
            
            # Update disturbance state
            self.disturbance_state = DisturbanceState.DETECTED
            
            # Record response start time
            if self.response_start_time is None:
                self.response_start_time = time.time()
            
            self.logger.warning("Grid disturbance detected: %s - %s (severity: %s, magnitude: %.3f)", 
                              disturbance_type.value, parameters, severity.value, magnitude)
            
        except Exception as e:
            self.logger.error("Error detecting disturbance: %s", e)
    
    def _execute_response_procedures(self) -> None:
        """Execute response procedures for active disturbances."""
        try:
            if not self.active_disturbances:
                return
            
            # Group disturbances by type
            disturbances_by_type = {}
            for disturbance in self.active_disturbances:
                if disturbance.disturbance_type not in disturbances_by_type:
                    disturbances_by_type[disturbance.disturbance_type] = []
                disturbances_by_type[disturbance.disturbance_type].append(disturbance)
            
            # Execute response for each disturbance type
            for disturbance_type, disturbances in disturbances_by_type.items():
                if disturbance_type in self.response_procedures:
                    response_procedure = self.response_procedures[disturbance_type]
                    response_procedure(disturbances)
            
            # Update disturbance state
            self.disturbance_state = DisturbanceState.RESPONDING
            
        except Exception as e:
            self.logger.error("Error executing response procedures: %s", e)
    
    def _execute_recovery_procedures(self) -> None:
        """Execute recovery procedures."""
        try:
            # Check for resolved disturbances
            resolved_disturbances = []
            
            for disturbance in self.active_disturbances:
                # Check if disturbance is resolved (simplified logic)
                if self._is_disturbance_resolved(disturbance):
                    resolved_disturbances.append(disturbance)
            
            # Execute recovery for resolved disturbances
            for disturbance in resolved_disturbances:
                self._resolve_disturbance(disturbance)
            
        except Exception as e:
            self.logger.error("Error executing recovery procedures: %s", e)
    
    def _is_disturbance_resolved(self, disturbance: DisturbanceEvent) -> bool:
        """
        Check if disturbance is resolved.
        
        Args:
            disturbance: Disturbance event
            
        Returns:
            True if disturbance is resolved
        """
        try:
            # Simplified resolution logic
            # In practice, this would check actual grid conditions
            
            # Check if disturbance has been active for too long
            duration = time.time() - disturbance.timestamp
            if duration > self.config.response_timeout:
                return True
            
            # Check if magnitude has decreased below threshold
            if disturbance.magnitude < self.detection_thresholds.get(disturbance.disturbance_type, {}).get('minor', 0.1):
                return True
            
            return False
            
        except Exception as e:
            self.logger.error("Error checking disturbance resolution: %s", e)
            return False
    
    def _resolve_disturbance(self, disturbance: DisturbanceEvent) -> None:
        """
        Resolve a disturbance.
        
        Args:
            disturbance: Disturbance event to resolve
        """
        try:
            # Mark as resolved
            disturbance.resolved = True
            disturbance.resolution_time = time.time()
            disturbance.duration = disturbance.resolution_time - disturbance.timestamp
            
            # Remove from active disturbances
            if disturbance in self.active_disturbances:
                self.active_disturbances.remove(disturbance)
            
            # Update performance metrics
            self.performance_metrics['disturbances_resolved'] += 1
            
            # Execute recovery procedure
            if disturbance.disturbance_type in self.recovery_procedures:
                recovery_procedure = self.recovery_procedures[disturbance.disturbance_type]
                recovery_procedure(disturbance)
            
            # Update disturbance state if no more active disturbances
            if not self.active_disturbances:
                self.disturbance_state = DisturbanceState.NORMAL
                self.response_start_time = None
            
            self.logger.info("Disturbance resolved: %s (duration: %.1f s)", 
                           disturbance.disturbance_type.value, disturbance.duration)
            
        except Exception as e:
            self.logger.error("Error resolving disturbance: %s", e)
    
    def _respond_to_frequency_drop(self, disturbances: List[DisturbanceEvent]) -> None:
        """
        Respond to frequency drop disturbances.
        
        Args:
            disturbances: List of frequency drop disturbances
        """
        try:
            for disturbance in disturbances:
                self.logger.info("Responding to frequency drop: magnitude %.3f Hz", disturbance.magnitude)
                
                # Execute response action
                response_action = ResponseAction(
                    action_type="frequency_response",
                    timestamp=time.time(),
                    parameters={'magnitude': disturbance.magnitude, 'response': 'increase_power'},
                    success=True,
                    response_time=0.1
                )
                
                self.response_history.append(response_action)
                
        except Exception as e:
            self.logger.error("Error responding to frequency drop: %s", e)
    
    def _respond_to_frequency_rise(self, disturbances: List[DisturbanceEvent]) -> None:
        """
        Respond to frequency rise disturbances.
        
        Args:
            disturbances: List of frequency rise disturbances
        """
        try:
            for disturbance in disturbances:
                self.logger.info("Responding to frequency rise: magnitude %.3f Hz", disturbance.magnitude)
                
                # Execute response action
                response_action = ResponseAction(
                    action_type="frequency_response",
                    timestamp=time.time(),
                    parameters={'magnitude': disturbance.magnitude, 'response': 'decrease_power'},
                    success=True,
                    response_time=0.1
                )
                
                self.response_history.append(response_action)
                
        except Exception as e:
            self.logger.error("Error responding to frequency rise: %s", e)
    
    def _respond_to_voltage_drop(self, disturbances: List[DisturbanceEvent]) -> None:
        """
        Respond to voltage drop disturbances.
        
        Args:
            disturbances: List of voltage drop disturbances
        """
        try:
            for disturbance in disturbances:
                self.logger.info("Responding to voltage drop: magnitude %.1f%%", disturbance.magnitude * 100)
                
                # Execute response action
                response_action = ResponseAction(
                    action_type="voltage_response",
                    timestamp=time.time(),
                    parameters={'magnitude': disturbance.magnitude, 'response': 'increase_reactive_power'},
                    success=True,
                    response_time=0.1
                )
                
                self.response_history.append(response_action)
                
        except Exception as e:
            self.logger.error("Error responding to voltage drop: %s", e)
    
    def _respond_to_voltage_rise(self, disturbances: List[DisturbanceEvent]) -> None:
        """
        Respond to voltage rise disturbances.
        
        Args:
            disturbances: List of voltage rise disturbances
        """
        try:
            for disturbance in disturbances:
                self.logger.info("Responding to voltage rise: magnitude %.1f%%", disturbance.magnitude * 100)
                
                # Execute response action
                response_action = ResponseAction(
                    action_type="voltage_response",
                    timestamp=time.time(),
                    parameters={'magnitude': disturbance.magnitude, 'response': 'decrease_reactive_power'},
                    success=True,
                    response_time=0.1
                )
                
                self.response_history.append(response_action)
                
        except Exception as e:
            self.logger.error("Error responding to voltage rise: %s", e)
    
    def _respond_to_frequency_oscillation(self, disturbances: List[DisturbanceEvent]) -> None:
        """
        Respond to frequency oscillation disturbances.
        
        Args:
            disturbances: List of frequency oscillation disturbances
        """
        try:
            for disturbance in disturbances:
                self.logger.info("Responding to frequency oscillation: magnitude %.3f Hz", disturbance.magnitude)
                
                # Execute response action
                response_action = ResponseAction(
                    action_type="oscillation_response",
                    timestamp=time.time(),
                    parameters={'magnitude': disturbance.magnitude, 'response': 'damping_control'},
                    success=True,
                    response_time=0.2
                )
                
                self.response_history.append(response_action)
                
        except Exception as e:
            self.logger.error("Error responding to frequency oscillation: %s", e)
    
    def _respond_to_voltage_oscillation(self, disturbances: List[DisturbanceEvent]) -> None:
        """
        Respond to voltage oscillation disturbances.
        
        Args:
            disturbances: List of voltage oscillation disturbances
        """
        try:
            for disturbance in disturbances:
                self.logger.info("Responding to voltage oscillation: magnitude %.1f%%", disturbance.magnitude * 100)
                
                # Execute response action
                response_action = ResponseAction(
                    action_type="oscillation_response",
                    timestamp=time.time(),
                    parameters={'magnitude': disturbance.magnitude, 'response': 'voltage_damping'},
                    success=True,
                    response_time=0.2
                )
                
                self.response_history.append(response_action)
                
        except Exception as e:
            self.logger.error("Error responding to voltage oscillation: %s", e)
    
    def _respond_to_power_quality(self, disturbances: List[DisturbanceEvent]) -> None:
        """
        Respond to power quality disturbances.
        
        Args:
            disturbances: List of power quality disturbances
        """
        try:
            for disturbance in disturbances:
                self.logger.info("Responding to power quality issue: magnitude %.3f", disturbance.magnitude)
                
                # Execute response action
                response_action = ResponseAction(
                    action_type="power_quality_response",
                    timestamp=time.time(),
                    parameters={'magnitude': disturbance.magnitude, 'response': 'harmonic_filtering'},
                    success=True,
                    response_time=0.3
                )
                
                self.response_history.append(response_action)
                
        except Exception as e:
            self.logger.error("Error responding to power quality: %s", e)
    
    def _respond_to_grid_fault(self, disturbances: List[DisturbanceEvent]) -> None:
        """
        Respond to grid fault disturbances.
        
        Args:
            disturbances: List of grid fault disturbances
        """
        try:
            for disturbance in disturbances:
                self.logger.critical("Responding to grid fault: magnitude %.3f", disturbance.magnitude)
                
                # Execute response action
                response_action = ResponseAction(
                    action_type="grid_fault_response",
                    timestamp=time.time(),
                    parameters={'magnitude': disturbance.magnitude, 'response': 'emergency_shutdown'},
                    success=True,
                    response_time=0.05
                )
                
                self.response_history.append(response_action)
                
        except Exception as e:
            self.logger.error("Error responding to grid fault: %s", e)
    
    def _recover_from_frequency_drop(self, disturbance: DisturbanceEvent) -> None:
        """
        Recover from frequency drop disturbance.
        
        Args:
            disturbance: Frequency drop disturbance event
        """
        try:
            self.logger.info("Recovering from frequency drop: duration %.1f s", disturbance.duration)
            
            # In practice, this would execute frequency recovery procedures
            # - Gradually reduce power output
            # - Synchronize with grid
            # - Verify frequency stability
            
        except Exception as e:
            self.logger.error("Error recovering from frequency drop: %s", e)
    
    def _recover_from_frequency_rise(self, disturbance: DisturbanceEvent) -> None:
        """
        Recover from frequency rise disturbance.
        
        Args:
            disturbance: Frequency rise disturbance event
        """
        try:
            self.logger.info("Recovering from frequency rise: duration %.1f s", disturbance.duration)
            
            # In practice, this would execute frequency recovery procedures
            # - Gradually increase power output
            # - Synchronize with grid
            # - Verify frequency stability
            
        except Exception as e:
            self.logger.error("Error recovering from frequency rise: %s", e)
    
    def _recover_from_voltage_drop(self, disturbance: DisturbanceEvent) -> None:
        """
        Recover from voltage drop disturbance.
        
        Args:
            disturbance: Voltage drop disturbance event
        """
        try:
            self.logger.info("Recovering from voltage drop: duration %.1f s", disturbance.duration)
            
            # In practice, this would execute voltage recovery procedures
            # - Gradually reduce reactive power
            # - Verify voltage stability
            # - Check power factor
            
        except Exception as e:
            self.logger.error("Error recovering from voltage drop: %s", e)
    
    def _recover_from_voltage_rise(self, disturbance: DisturbanceEvent) -> None:
        """
        Recover from voltage rise disturbance.
        
        Args:
            disturbance: Voltage rise disturbance event
        """
        try:
            self.logger.info("Recovering from voltage rise: duration %.1f s", disturbance.duration)
            
            # In practice, this would execute voltage recovery procedures
            # - Gradually increase reactive power
            # - Verify voltage stability
            # - Check power factor
            
        except Exception as e:
            self.logger.error("Error recovering from voltage rise: %s", e)
    
    def _recover_from_frequency_oscillation(self, disturbance: DisturbanceEvent) -> None:
        """
        Recover from frequency oscillation disturbance.
        
        Args:
            disturbance: Frequency oscillation disturbance event
        """
        try:
            self.logger.info("Recovering from frequency oscillation: duration %.1f s", disturbance.duration)
            
            # In practice, this would execute oscillation recovery procedures
            # - Reduce damping control
            # - Verify frequency stability
            # - Check system dynamics
            
        except Exception as e:
            self.logger.error("Error recovering from frequency oscillation: %s", e)
    
    def _recover_from_voltage_oscillation(self, disturbance: DisturbanceEvent) -> None:
        """
        Recover from voltage oscillation disturbance.
        
        Args:
            disturbance: Voltage oscillation disturbance event
        """
        try:
            self.logger.info("Recovering from voltage oscillation: duration %.1f s", disturbance.duration)
            
            # In practice, this would execute oscillation recovery procedures
            # - Reduce voltage damping
            # - Verify voltage stability
            # - Check system dynamics
            
        except Exception as e:
            self.logger.error("Error recovering from voltage oscillation: %s", e)
    
    def _recover_from_power_quality(self, disturbance: DisturbanceEvent) -> None:
        """
        Recover from power quality disturbance.
        
        Args:
            disturbance: Power quality disturbance event
        """
        try:
            self.logger.info("Recovering from power quality issue: duration %.1f s", disturbance.duration)
            
            # In practice, this would execute power quality recovery procedures
            # - Reduce harmonic filtering
            # - Verify power quality
            # - Check harmonic levels
            
        except Exception as e:
            self.logger.error("Error recovering from power quality: %s", e)
    
    def _recover_from_grid_fault(self, disturbance: DisturbanceEvent) -> None:
        """
        Recover from grid fault disturbance.
        
        Args:
            disturbance: Grid fault disturbance event
        """
        try:
            self.logger.info("Recovering from grid fault: duration %.1f s", disturbance.duration)
            
            # In practice, this would execute grid fault recovery procedures
            # - Check grid conditions
            # - Synchronize with grid
            # - Verify grid stability
            
        except Exception as e:
            self.logger.error("Error recovering from grid fault: %s", e)
    
    def _update_performance_metrics(self) -> None:
        """Update performance metrics."""
        try:
            # Update operating hours
            self.performance_metrics['operating_hours'] += 0.001  # hours
            
            # Calculate response success rate
            if self.response_history:
                successful_responses = sum(1 for response in self.response_history if response.success)
                total_responses = len(self.response_history)
                if total_responses > 0:
                    self.performance_metrics['response_success_rate'] = (successful_responses / total_responses) * 100
            
            # Calculate grid stability score
            if self.disturbance_history:
                resolved_disturbances = sum(1 for d in self.disturbance_history if d.resolved)
                total_disturbances = len(self.disturbance_history)
                if total_disturbances > 0:
                    stability_score = (resolved_disturbances / total_disturbances) * 100
                    self.performance_metrics['grid_stability_score'] = min(100.0, stability_score)
            
        except Exception as e:
            self.logger.error("Error updating performance metrics: %s", e)
    
    def get_disturbance_state(self) -> DisturbanceState:
        """
        Get current disturbance state.
        
        Returns:
            Current disturbance state
        """
        return self.disturbance_state
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Get performance metrics.
        
        Returns:
            Performance metrics dictionary
        """
        return self.performance_metrics.copy()
    
    def get_active_disturbances(self) -> List[DisturbanceEvent]:
        """
        Get active disturbances.
        
        Returns:
            List of active disturbance events
        """
        return self.active_disturbances.copy()
    
    def get_disturbance_history(self, limit: Optional[int] = None) -> List[DisturbanceEvent]:
        """
        Get disturbance history.
        
        Args:
            limit: Maximum number of disturbances to return
            
        Returns:
            List of disturbance events
        """
        if limit is None:
            return self.disturbance_history.copy()
        else:
            return self.disturbance_history[-limit:]
    
    def get_response_history(self) -> List[ResponseAction]:
        """
        Get response history.
        
        Returns:
            List of response actions
        """
        return self.response_history.copy()
    
    def get_grid_history(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get grid history.
        
        Args:
            limit: Maximum number of records to return
            
        Returns:
            List of grid parameter records
        """
        grid_list = list(self.grid_history)
        if limit is None:
            return grid_list
        else:
            return grid_list[-limit:]
    
    def is_monitoring_active(self) -> bool:
        """
        Check if monitoring is active.
        
        Returns:
            True if monitoring is active
        """
        return self.monitoring_active
    
    def is_disturbance_active(self) -> bool:
        """
        Check if disturbance is active.
        
        Returns:
            True if disturbance is active
        """
        return len(self.active_disturbances) > 0
    
    def reset(self) -> None:
        """Reset grid disturbance handler to initial state."""
        self.disturbance_state = DisturbanceState.NORMAL
        self.monitoring_active = False
        self.active_disturbances.clear()
        self.disturbance_history.clear()
        self.response_history.clear()
        self.grid_history.clear()
        self.response_start_time = None
        self.recovery_start_time = None
        
        self.performance_metrics = {
            'total_disturbances': 0,
            'disturbances_resolved': 0,
            'average_response_time': 0.0,
            'response_success_rate': 100.0,
            'grid_stability_score': 100.0,
            'operating_hours': 0.0,
            'coordination_events': 0
        }
        
        self.logger.info("Grid disturbance handler reset")

