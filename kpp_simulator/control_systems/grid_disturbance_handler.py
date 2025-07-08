"""
Grid Disturbance Handler for KPP Simulator
Handles grid disturbances and maintains system stability
"""

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
from datetime import datetime, timedelta

from ..core.physics_engine import PhysicsEngine
from ..core.event_handlers import AdvancedEventHandler
from ..electrical.electrical_system import IntegratedElectricalSystem
from ..control_systems.control_system import IntegratedControlSystem


class DisturbanceType(Enum):
    """Types of grid disturbances"""
    VOLTAGE_SAG = "voltage_sag"
    VOLTAGE_SWELL = "voltage_swell"
    FREQUENCY_DEVIATION = "frequency_deviation"
    HARMONIC_DISTORTION = "harmonic_distortion"
    TRANSIENT_FAULT = "transient_fault"
    POWER_OUTAGE = "power_outage"
    GRID_ISLANDING = "grid_islanding"
    LOAD_SURGE = "load_surge"
    GENERATION_DROP = "generation_drop"
    LINE_FAULT = "line_fault"


class DisturbanceSeverity(Enum):
    """Severity levels for grid disturbances"""
    MINOR = "minor"
    MODERATE = "moderate"
    MAJOR = "major"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


class ResponseMode(Enum):
    """Response modes for grid disturbances"""
    AUTOMATIC = "automatic"
    SEMI_AUTOMATIC = "semi_automatic"
    MANUAL = "manual"
    EMERGENCY = "emergency"


@dataclass
class DisturbanceEvent:
    """Represents a grid disturbance event"""
    timestamp: datetime
    disturbance_type: DisturbanceType
    severity: DisturbanceSeverity
    magnitude: float
    duration: timedelta
    location: str
    description: str
    detected: bool = False
    responded: bool = False
    resolved: bool = False
    response_time: Optional[timedelta] = None
    resolution_time: Optional[timedelta] = None


@dataclass
class DisturbanceResponse:
    """Response configuration for a disturbance type"""
    disturbance_type: DisturbanceType
    severity: DisturbanceSeverity
    response_mode: ResponseMode
    actions: List[str]
    thresholds: Dict[str, float]
    timeouts: Dict[str, float]
    recovery_steps: List[str]


@dataclass
class DisturbanceStatistics:
    """Statistics for disturbance handling"""
    total_disturbances: int = 0
    detected_disturbances: int = 0
    responded_disturbances: int = 0
    resolved_disturbances: int = 0
    average_response_time: float = 0.0
    average_resolution_time: float = 0.0
    detection_rate: float = 0.0
    response_rate: float = 0.0
    resolution_rate: float = 0.0
    false_positives: int = 0
    false_negatives: int = 0


class GridDisturbanceHandler:
    """
    Handles grid disturbances and maintains system stability
    
    Features:
    - Real-time disturbance detection and classification
    - Automatic and manual response coordination
    - Recovery procedures and system restoration
    - Performance monitoring and optimization
    - Integration with control and electrical systems
    """
    
    def __init__(self, 
                 physics_engine: PhysicsEngine,
                 event_handler: AdvancedEventHandler,
                 electrical_system: IntegratedElectricalSystem,
                 control_system: IntegratedControlSystem):
        """
        Initialize the Grid Disturbance Handler
        
        Args:
            physics_engine: Core physics engine
            event_handler: Advanced event handler
            electrical_system: Integrated electrical system
            control_system: Integrated control system
        """
        self.physics_engine = physics_engine
        self.event_handler = event_handler
        self.electrical_system = electrical_system
        self.control_system = control_system
        
        # State management
        self.is_active = False
        self.current_mode = ResponseMode.AUTOMATIC
        self.disturbance_history: List[DisturbanceEvent] = []
        self.active_disturbances: List[DisturbanceEvent] = []
        self.response_configs: Dict[Tuple[DisturbanceType, DisturbanceSeverity], DisturbanceResponse] = {}
        
        # Detection parameters
        self.detection_thresholds = {
            DisturbanceType.VOLTAGE_SAG: 0.9,  # 90% of nominal
            DisturbanceType.VOLTAGE_SWELL: 1.1,  # 110% of nominal
            DisturbanceType.FREQUENCY_DEVIATION: 0.5,  # Hz
            DisturbanceType.HARMONIC_DISTORTION: 0.05,  # 5% THD
            DisturbanceType.TRANSIENT_FAULT: 0.1,  # 100ms
            DisturbanceType.POWER_OUTAGE: 0.5,  # 50% power loss
            DisturbanceType.GRID_ISLANDING: 0.1,  # 100ms
            DisturbanceType.LOAD_SURGE: 1.2,  # 120% of nominal
            DisturbanceType.GENERATION_DROP: 0.8,  # 80% of nominal
            DisturbanceType.LINE_FAULT: 0.1  # 100ms
        }
        
        # Response timeouts
        self.response_timeouts = {
            DisturbanceSeverity.MINOR: 5.0,  # seconds
            DisturbanceSeverity.MODERATE: 3.0,
            DisturbanceSeverity.MAJOR: 1.0,
            DisturbanceSeverity.CRITICAL: 0.5,
            DisturbanceSeverity.EMERGENCY: 0.1
        }
        
        # Statistics
        self.statistics = DisturbanceStatistics()
        
        # Performance tracking
        self.performance_metrics = {
            'detection_latency': [],
            'response_latency': [],
            'resolution_time': [],
            'false_positive_rate': 0.0,
            'false_negative_rate': 0.0,
            'system_availability': 1.0
        }
        
        # Initialize response configurations
        self._initialize_response_configs()
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        self.logger.info("Grid Disturbance Handler initialized")
    
    def _initialize_response_configs(self):
        """Initialize response configurations for different disturbance types"""
        
        # Voltage sag response
        self.response_configs[(DisturbanceType.VOLTAGE_SAG, DisturbanceSeverity.MINOR)] = DisturbanceResponse(
            disturbance_type=DisturbanceType.VOLTAGE_SAG,
            severity=DisturbanceSeverity.MINOR,
            response_mode=ResponseMode.AUTOMATIC,
            actions=['monitor_voltage', 'adjust_power_factor'],
            thresholds={'voltage_threshold': 0.95, 'duration_threshold': 1.0},
            timeouts={'response_timeout': 5.0, 'recovery_timeout': 30.0},
            recovery_steps=['restore_voltage', 'verify_stability', 'resume_normal_operation']
        )
        
        # Voltage swell response
        self.response_configs[(DisturbanceType.VOLTAGE_SWELL, DisturbanceSeverity.MODERATE)] = DisturbanceResponse(
            disturbance_type=DisturbanceType.VOLTAGE_SWELL,
            severity=DisturbanceSeverity.MODERATE,
            response_mode=ResponseMode.AUTOMATIC,
            actions=['reduce_voltage', 'activate_protection', 'isolate_system'],
            thresholds={'voltage_threshold': 1.05, 'duration_threshold': 0.5},
            timeouts={'response_timeout': 3.0, 'recovery_timeout': 60.0},
            recovery_steps=['stabilize_voltage', 'check_equipment', 'gradual_restoration']
        )
        
        # Frequency deviation response
        self.response_configs[(DisturbanceType.FREQUENCY_DEVIATION, DisturbanceSeverity.MAJOR)] = DisturbanceResponse(
            disturbance_type=DisturbanceType.FREQUENCY_DEVIATION,
            severity=DisturbanceSeverity.MAJOR,
            response_mode=ResponseMode.AUTOMATIC,
            actions=['adjust_frequency', 'load_shedding', 'activate_backup'],
            thresholds={'frequency_threshold': 0.5, 'duration_threshold': 0.2},
            timeouts={'response_timeout': 1.0, 'recovery_timeout': 120.0},
            recovery_steps=['stabilize_frequency', 'restore_loads', 'verify_synchronization']
        )
        
        # Power outage response
        self.response_configs[(DisturbanceType.POWER_OUTAGE, DisturbanceSeverity.CRITICAL)] = DisturbanceResponse(
            disturbance_type=DisturbanceType.POWER_OUTAGE,
            severity=DisturbanceSeverity.CRITICAL,
            response_mode=ResponseMode.EMERGENCY,
            actions=['emergency_shutdown', 'activate_backup_power', 'isolate_system'],
            thresholds={'power_threshold': 0.5, 'duration_threshold': 0.1},
            timeouts={'response_timeout': 0.5, 'recovery_timeout': 300.0},
            recovery_steps=['verify_safety', 'check_equipment', 'gradual_restart', 'synchronize_grid']
        )
        
        # Grid islanding response
        self.response_configs[(DisturbanceType.GRID_ISLANDING, DisturbanceSeverity.EMERGENCY)] = DisturbanceResponse(
            disturbance_type=DisturbanceType.GRID_ISLANDING,
            severity=DisturbanceSeverity.EMERGENCY,
            response_mode=ResponseMode.EMERGENCY,
            actions=['immediate_shutdown', 'activate_island_mode', 'protect_equipment'],
            thresholds={'isolation_threshold': 0.1, 'duration_threshold': 0.05},
            timeouts={'response_timeout': 0.1, 'recovery_timeout': 600.0},
            recovery_steps=['verify_isolation', 'check_equipment', 'wait_for_grid', 'synchronize_restart']
        )
    
    def start(self):
        """Start the disturbance handler"""
        self.is_active = True
        self.logger.info("Grid Disturbance Handler started")
    
    def stop(self):
        """Stop the disturbance handler"""
        self.is_active = False
        self.logger.info("Grid Disturbance Handler stopped")
    
    def update(self, dt: float):
        """
        Update the disturbance handler
        
        Args:
            dt: Time step in seconds
        """
        if not self.is_active:
            return
        
        # Detect disturbances
        self._detect_disturbances()
        
        # Process active disturbances
        self._process_active_disturbances(dt)
        
        # Update statistics
        self._update_statistics()
        
        # Check for resolved disturbances
        self._check_resolved_disturbances()
    
    def _detect_disturbances(self):
        """Detect new disturbances based on current system state"""
        current_time = datetime.now()
        
        # Get current electrical measurements
        electrical_state = self.electrical_system.get_state()
        
        # Check for voltage disturbances
        nominal_voltage = 400.0  # V
        current_voltage = electrical_state.get('voltage', nominal_voltage)
        
        if current_voltage < nominal_voltage * self.detection_thresholds[DisturbanceType.VOLTAGE_SAG]:
            self._create_disturbance_event(
                DisturbanceType.VOLTAGE_SAG,
                DisturbanceSeverity.MINOR if current_voltage > nominal_voltage * 0.8 else DisturbanceSeverity.MAJOR,
                (nominal_voltage - current_voltage) / nominal_voltage,
                current_time
            )
        
        elif current_voltage > nominal_voltage * self.detection_thresholds[DisturbanceType.VOLTAGE_SWELL]:
            self._create_disturbance_event(
                DisturbanceType.VOLTAGE_SWELL,
                DisturbanceSeverity.MODERATE if current_voltage < nominal_voltage * 1.2 else DisturbanceSeverity.CRITICAL,
                (current_voltage - nominal_voltage) / nominal_voltage,
                current_time
            )
        
        # Check for frequency disturbances
        nominal_frequency = 50.0  # Hz
        current_frequency = electrical_state.get('frequency', nominal_frequency)
        
        if abs(current_frequency - nominal_frequency) > self.detection_thresholds[DisturbanceType.FREQUENCY_DEVIATION]:
            self._create_disturbance_event(
                DisturbanceType.FREQUENCY_DEVIATION,
                DisturbanceSeverity.MAJOR if abs(current_frequency - nominal_frequency) < 2.0 else DisturbanceSeverity.CRITICAL,
                abs(current_frequency - nominal_frequency),
                current_time
            )
        
        # Check for power disturbances
        nominal_power = 1000.0  # W
        current_power = electrical_state.get('power_output', nominal_power)
        
        if current_power < nominal_power * self.detection_thresholds[DisturbanceType.POWER_OUTAGE]:
            self._create_disturbance_event(
                DisturbanceType.POWER_OUTAGE,
                DisturbanceSeverity.CRITICAL if current_power < nominal_power * 0.2 else DisturbanceSeverity.MAJOR,
                (nominal_power - current_power) / nominal_power,
                current_time
            )
    
    def _create_disturbance_event(self, 
                                disturbance_type: DisturbanceType,
                                severity: DisturbanceSeverity,
                                magnitude: float,
                                timestamp: datetime):
        """Create a new disturbance event"""
        
        # Check if similar disturbance is already active
        for active_disturbance in self.active_disturbances:
            if (active_disturbance.disturbance_type == disturbance_type and 
                not active_disturbance.resolved):
                return  # Already handling this type of disturbance
        
        # Create new disturbance event
        event = DisturbanceEvent(
            timestamp=timestamp,
            disturbance_type=disturbance_type,
            severity=severity,
            magnitude=magnitude,
            duration=timedelta(0),
            location="main_grid",
            description=f"{disturbance_type.value} detected with magnitude {magnitude:.3f}",
            detected=True
        )
        
        self.active_disturbances.append(event)
        self.disturbance_history.append(event)
        
        self.logger.warning(f"Disturbance detected: {disturbance_type.value} - {severity.value} - Magnitude: {magnitude:.3f}")
        
        # Update statistics
        self.statistics.total_disturbances += 1
        self.statistics.detected_disturbances += 1
    
    def _process_active_disturbances(self, dt: float):
        """Process active disturbances and execute responses"""
        current_time = datetime.now()
        
        for disturbance in self.active_disturbances:
            if disturbance.resolved:
                continue
            
            # Update duration
            disturbance.duration = current_time - disturbance.timestamp
            
            # Get response configuration
            config_key = (disturbance.disturbance_type, disturbance.severity)
            response_config = self.response_configs.get(config_key)
            
            if not response_config:
                self.logger.warning(f"No response configuration for {disturbance.disturbance_type.value} - {disturbance.severity.value}")
                continue
            
            # Execute response if not already responded
            if not disturbance.responded:
                self._execute_response(disturbance, response_config)
                disturbance.responded = True
                disturbance.response_time = current_time - disturbance.timestamp
                
                self.statistics.responded_disturbances += 1
            
            # Check if disturbance is resolved
            if self._check_disturbance_resolution(disturbance):
                disturbance.resolved = True
                disturbance.resolution_time = current_time - disturbance.timestamp
                self.statistics.resolved_disturbances += 1
                
                self.logger.info(f"Disturbance resolved: {disturbance.disturbance_type.value} - Duration: {disturbance.duration}")
    
    def _execute_response(self, disturbance: DisturbanceEvent, response_config: DisturbanceResponse):
        """Execute response actions for a disturbance"""
        
        self.logger.info(f"Executing response for {disturbance.disturbance_type.value} - {disturbance.severity.value}")
        
        for action in response_config.actions:
            try:
                if action == 'monitor_voltage':
                    self._monitor_voltage()
                elif action == 'adjust_power_factor':
                    self._adjust_power_factor()
                elif action == 'reduce_voltage':
                    self._reduce_voltage()
                elif action == 'activate_protection':
                    self._activate_protection()
                elif action == 'isolate_system':
                    self._isolate_system()
                elif action == 'adjust_frequency':
                    self._adjust_frequency()
                elif action == 'load_shedding':
                    self._load_shedding()
                elif action == 'activate_backup':
                    self._activate_backup()
                elif action == 'emergency_shutdown':
                    self._emergency_shutdown()
                elif action == 'activate_backup_power':
                    self._activate_backup_power()
                elif action == 'immediate_shutdown':
                    self._immediate_shutdown()
                elif action == 'activate_island_mode':
                    self._activate_island_mode()
                elif action == 'protect_equipment':
                    self._protect_equipment()
                else:
                    self.logger.warning(f"Unknown response action: {action}")
                    
            except Exception as e:
                self.logger.error(f"Error executing response action {action}: {e}")
    
    def _check_disturbance_resolution(self, disturbance: DisturbanceEvent) -> bool:
        """Check if a disturbance has been resolved"""
        
        # Get current electrical measurements
        electrical_state = self.electrical_system.get_state()
        nominal_voltage = 400.0
        nominal_frequency = 50.0
        nominal_power = 1000.0
        
        current_voltage = electrical_state.get('voltage', nominal_voltage)
        current_frequency = electrical_state.get('frequency', nominal_frequency)
        current_power = electrical_state.get('power_output', nominal_power)
        
        # Check resolution based on disturbance type
        if disturbance.disturbance_type == DisturbanceType.VOLTAGE_SAG:
            return current_voltage >= nominal_voltage * 0.95
        
        elif disturbance.disturbance_type == DisturbanceType.VOLTAGE_SWELL:
            return current_voltage <= nominal_voltage * 1.05
        
        elif disturbance.disturbance_type == DisturbanceType.FREQUENCY_DEVIATION:
            return abs(current_frequency - nominal_frequency) <= 0.2
        
        elif disturbance.disturbance_type == DisturbanceType.POWER_OUTAGE:
            return current_power >= nominal_power * 0.8
        
        elif disturbance.disturbance_type == DisturbanceType.GRID_ISLANDING:
            # Grid islanding requires manual intervention
            return False
        
        return False
    
    def _check_resolved_disturbances(self):
        """Check for and clean up resolved disturbances"""
        resolved_disturbances = [d for d in self.active_disturbances if d.resolved]
        
        for disturbance in resolved_disturbances:
            self.active_disturbances.remove(disturbance)
            self.logger.info(f"Removed resolved disturbance: {disturbance.disturbance_type.value}")
    
    def _update_statistics(self):
        """Update disturbance handling statistics"""
        if self.statistics.total_disturbances > 0:
            self.statistics.detection_rate = self.statistics.detected_disturbances / self.statistics.total_disturbances
            self.statistics.response_rate = self.statistics.responded_disturbances / self.statistics.total_disturbances
            self.statistics.resolution_rate = self.statistics.resolved_disturbances / self.statistics.total_disturbances
        
        # Calculate average response and resolution times
        response_times = [d.response_time.total_seconds() for d in self.disturbance_history if d.response_time]
        resolution_times = [d.resolution_time.total_seconds() for d in self.disturbance_history if d.resolution_time]
        
        if response_times:
            self.statistics.average_response_time = np.mean(response_times)
        
        if resolution_times:
            self.statistics.average_resolution_time = np.mean(resolution_times)
    
    # Response action implementations
    def _monitor_voltage(self):
        """Monitor voltage levels"""
        self.logger.info("Monitoring voltage levels")
        # Implementation would interface with electrical system monitoring
    
    def _adjust_power_factor(self):
        """Adjust power factor"""
        self.logger.info("Adjusting power factor")
        # Implementation would interface with electrical system controls
    
    def _reduce_voltage(self):
        """Reduce voltage levels"""
        self.logger.info("Reducing voltage levels")
        # Implementation would interface with electrical system controls
    
    def _activate_protection(self):
        """Activate protection systems"""
        self.logger.info("Activating protection systems")
        # Implementation would interface with protection systems
    
    def _isolate_system(self):
        """Isolate system from grid"""
        self.logger.info("Isolating system from grid")
        # Implementation would interface with electrical system isolation
    
    def _adjust_frequency(self):
        """Adjust frequency"""
        self.logger.info("Adjusting frequency")
        # Implementation would interface with frequency control
    
    def _load_shedding(self):
        """Perform load shedding"""
        self.logger.info("Performing load shedding")
        # Implementation would interface with load management
    
    def _activate_backup(self):
        """Activate backup systems"""
        self.logger.info("Activating backup systems")
        # Implementation would interface with backup systems
    
    def _emergency_shutdown(self):
        """Perform emergency shutdown"""
        self.logger.info("Performing emergency shutdown")
        # Implementation would interface with emergency systems
    
    def _activate_backup_power(self):
        """Activate backup power"""
        self.logger.info("Activating backup power")
        # Implementation would interface with backup power systems
    
    def _immediate_shutdown(self):
        """Perform immediate shutdown"""
        self.logger.info("Performing immediate shutdown")
        # Implementation would interface with emergency shutdown systems
    
    def _activate_island_mode(self):
        """Activate island mode"""
        self.logger.info("Activating island mode")
        # Implementation would interface with island mode systems
    
    def _protect_equipment(self):
        """Protect equipment"""
        self.logger.info("Protecting equipment")
        # Implementation would interface with equipment protection systems
    
    def get_statistics(self) -> DisturbanceStatistics:
        """Get current disturbance statistics"""
        return self.statistics
    
    def get_active_disturbances(self) -> List[DisturbanceEvent]:
        """Get list of active disturbances"""
        return self.active_disturbances.copy()
    
    def get_disturbance_history(self) -> List[DisturbanceEvent]:
        """Get disturbance history"""
        return self.disturbance_history.copy()
    
    def set_response_mode(self, mode: ResponseMode):
        """Set the response mode"""
        self.current_mode = mode
        self.logger.info(f"Response mode set to: {mode.value}")
    
    def manual_disturbance_response(self, disturbance_type: DisturbanceType, severity: DisturbanceSeverity):
        """Manually trigger a disturbance response"""
        current_time = datetime.now()
        
        event = DisturbanceEvent(
            timestamp=current_time,
            disturbance_type=disturbance_type,
            severity=severity,
            magnitude=0.0,
            duration=timedelta(0),
            location="manual_trigger",
            description=f"Manual disturbance response triggered: {disturbance_type.value} - {severity.value}",
            detected=True
        )
        
        self.active_disturbances.append(event)
        self.disturbance_history.append(event)
        
        self.logger.info(f"Manual disturbance response triggered: {disturbance_type.value} - {severity.value}")
    
    def clear_disturbance_history(self):
        """Clear disturbance history"""
        self.disturbance_history.clear()
        self.logger.info("Disturbance history cleared")
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics"""
        return self.performance_metrics.copy()
    
    def reset_statistics(self):
        """Reset all statistics"""
        self.statistics = DisturbanceStatistics()
        self.logger.info("Disturbance statistics reset") 