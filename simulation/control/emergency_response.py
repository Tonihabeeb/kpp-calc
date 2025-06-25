"""
Emergency Response System for KPP System
Handles emergency conditions and rapid shutdown procedures.
"""

import logging
import time
from enum import Enum
from typing import Dict, List, Optional, Set
from dataclasses import dataclass

logger = logging.getLogger(__name__)

class EmergencyType(Enum):
    """Types of emergency conditions"""
    OVERSPEED = "overspeed"
    OVERPRESSURE = "overpressure"
    OVERTEMPERATURE = "overtemperature"
    ELECTRICAL_FAULT = "electrical_fault"
    MECHANICAL_FAILURE = "mechanical_failure"
    GRID_DISTURBANCE = "grid_disturbance"
    MANUAL_STOP = "manual_stop"
    SAFETY_SYSTEM_FAULT = "safety_system_fault"

class EmergencyPriority(Enum):
    """Emergency priority levels"""
    CRITICAL = 1    # Immediate shutdown required
    HIGH = 2        # Rapid response required
    MEDIUM = 3      # Controlled response required
    LOW = 4         # Monitor and log

@dataclass
class EmergencyCondition:
    """Emergency condition definition"""
    emergency_type: EmergencyType
    priority: EmergencyPriority
    description: str
    detected_time: float
    threshold_value: Optional[float] = None
    current_value: Optional[float] = None
    acknowledged: bool = False
    resolved: bool = False

@dataclass
class EmergencyLimits:
    """Emergency detection limits"""
    max_flywheel_speed: float = 450.0      # RPM
    max_chain_speed: float = 20.0          # m/s
    max_tank_pressure: float = 8.0         # bar
    max_component_temperature: float = 85.0  # °C
    max_current: float = 1200.0            # A
    min_grid_voltage: float = 420.0        # V
    max_grid_voltage: float = 530.0        # V
    min_grid_frequency: float = 58.0       # Hz
    max_grid_frequency: float = 62.0       # Hz
    max_torque: float = 3000.0             # N·m

class EmergencyResponseSystem:
    """
    Comprehensive emergency response and rapid shutdown system.
    
    Features:
    - Multi-level emergency detection
    - Prioritized response procedures
    - Rapid shutdown sequences
    - Safety system monitoring
    - Emergency logging and reporting
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize emergency response system.
        
        Args:
            config: Configuration parameters for emergency system
        """
        self.config = config or {}
        self.limits = EmergencyLimits()
        
        # Emergency state
        self.emergency_active = False
        self.emergency_conditions: List[EmergencyCondition] = []
        self.active_emergencies: Set[EmergencyType] = set()
        
        # Shutdown state
        self.shutdown_initiated = False
        self.shutdown_start_time = 0.0
        self.shutdown_phase = "none"
        self.shutdown_complete = False
        
        # Response timers
        self.detection_time = 0.0
        self.response_time = 0.0
        self.shutdown_time = 0.0
        
        # Emergency priority mapping
        self.emergency_priorities = {
            EmergencyType.OVERSPEED: EmergencyPriority.CRITICAL,
            EmergencyType.OVERPRESSURE: EmergencyPriority.CRITICAL,
            EmergencyType.OVERTEMPERATURE: EmergencyPriority.HIGH,
            EmergencyType.ELECTRICAL_FAULT: EmergencyPriority.HIGH,
            EmergencyType.MECHANICAL_FAILURE: EmergencyPriority.CRITICAL,
            EmergencyType.GRID_DISTURBANCE: EmergencyPriority.MEDIUM,
            EmergencyType.MANUAL_STOP: EmergencyPriority.HIGH,
            EmergencyType.SAFETY_SYSTEM_FAULT: EmergencyPriority.CRITICAL
        }
        
        # Shutdown sequence phases
        self.shutdown_phases = [
            "disconnect_grid",
            "stop_injections", 
            "engage_brakes",
            "isolate_pneumatics",
            "secure_electrical",
            "complete"
        ]
        
        # Performance tracking
        self.emergency_history = []
        self.response_metrics = {
            'total_emergencies': 0,
            'average_detection_time': 0.0,
            'average_response_time': 0.0,
            'fastest_shutdown': float('inf'),
            'false_alarms': 0
        }
        
        logger.info("EmergencyResponseSystem initialized")
    
    def monitor_emergency_conditions(self, system_state: Dict, current_time: float) -> Dict:
        """
        Monitor system for emergency conditions.
        
        Args:
            system_state: Current system state
            current_time: Current simulation time
            
        Returns:
            Dict: Emergency status and response commands
        """
        # Check all emergency conditions
        new_emergencies = self._detect_emergency_conditions(system_state, current_time)
        
        # Process new emergencies
        for emergency in new_emergencies:
            self._handle_new_emergency(emergency, current_time)
        
        # Update emergency response
        response_commands = self._update_emergency_response(system_state, current_time)
        
        # Update metrics
        self._update_emergency_metrics(current_time)
        
        return response_commands
    
    def _detect_emergency_conditions(self, system_state: Dict, current_time: float) -> List[EmergencyCondition]:
        """Detect emergency conditions in system state"""
        new_emergencies = []
        
        # Check overspeed conditions
        flywheel_speed = system_state.get('flywheel_speed_rpm', 0.0)
        if flywheel_speed > self.limits.max_flywheel_speed:
            if EmergencyType.OVERSPEED not in self.active_emergencies:
                new_emergencies.append(EmergencyCondition(
                    emergency_type=EmergencyType.OVERSPEED,
                    priority=self.emergency_priorities[EmergencyType.OVERSPEED],
                    description=f"Flywheel overspeed: {flywheel_speed:.1f} RPM > {self.limits.max_flywheel_speed} RPM",
                    detected_time=current_time,
                    threshold_value=self.limits.max_flywheel_speed,
                    current_value=flywheel_speed
                ))
        
        # Check chain overspeed
        chain_speed = system_state.get('chain_speed_rpm', 0.0) * 0.1047  # Convert to m/s
        if chain_speed > self.limits.max_chain_speed:
            if EmergencyType.OVERSPEED not in self.active_emergencies:
                new_emergencies.append(EmergencyCondition(
                    emergency_type=EmergencyType.OVERSPEED,
                    priority=self.emergency_priorities[EmergencyType.OVERSPEED],
                    description=f"Chain overspeed: {chain_speed:.1f} m/s > {self.limits.max_chain_speed} m/s",
                    detected_time=current_time,
                    threshold_value=self.limits.max_chain_speed,
                    current_value=chain_speed
                ))
        
        # Check overpressure
        tank_pressure = system_state.get('pneumatics', {}).get('tank_pressure', 0.0)
        if tank_pressure > self.limits.max_tank_pressure:
            if EmergencyType.OVERPRESSURE not in self.active_emergencies:
                new_emergencies.append(EmergencyCondition(
                    emergency_type=EmergencyType.OVERPRESSURE,
                    priority=self.emergency_priorities[EmergencyType.OVERPRESSURE],
                    description=f"Tank overpressure: {tank_pressure:.1f} bar > {self.limits.max_tank_pressure} bar",
                    detected_time=current_time,
                    threshold_value=self.limits.max_tank_pressure,
                    current_value=tank_pressure
                ))
        
        # Check overtemperature
        component_temps = system_state.get('component_temperatures', {})
        for component, temp in component_temps.items():
            if temp > self.limits.max_component_temperature:
                if EmergencyType.OVERTEMPERATURE not in self.active_emergencies:
                    new_emergencies.append(EmergencyCondition(
                        emergency_type=EmergencyType.OVERTEMPERATURE,
                        priority=self.emergency_priorities[EmergencyType.OVERTEMPERATURE],
                        description=f"Component overtemperature: {component} at {temp:.1f}°C > {self.limits.max_component_temperature}°C",
                        detected_time=current_time,
                        threshold_value=self.limits.max_component_temperature,
                        current_value=temp
                    ))
                    break  # Only report one overtemperature at a time
        
        # Check electrical faults
        grid_voltage = system_state.get('grid_voltage', 480.0)
        if grid_voltage < self.limits.min_grid_voltage or grid_voltage > self.limits.max_grid_voltage:
            if EmergencyType.ELECTRICAL_FAULT not in self.active_emergencies:
                new_emergencies.append(EmergencyCondition(
                    emergency_type=EmergencyType.ELECTRICAL_FAULT,
                    priority=self.emergency_priorities[EmergencyType.ELECTRICAL_FAULT],
                    description=f"Grid voltage fault: {grid_voltage:.1f}V outside [{self.limits.min_grid_voltage}-{self.limits.max_grid_voltage}]V",
                    detected_time=current_time,
                    threshold_value=self.limits.min_grid_voltage if grid_voltage < self.limits.min_grid_voltage else self.limits.max_grid_voltage,
                    current_value=grid_voltage
                ))
        
        # Check grid frequency
        grid_frequency = system_state.get('grid_frequency', 60.0)
        if grid_frequency < self.limits.min_grid_frequency or grid_frequency > self.limits.max_grid_frequency:
            if EmergencyType.GRID_DISTURBANCE not in self.active_emergencies:
                new_emergencies.append(EmergencyCondition(
                    emergency_type=EmergencyType.GRID_DISTURBANCE,
                    priority=self.emergency_priorities[EmergencyType.GRID_DISTURBANCE],
                    description=f"Grid frequency disturbance: {grid_frequency:.1f}Hz outside [{self.limits.min_grid_frequency}-{self.limits.max_grid_frequency}]Hz",
                    detected_time=current_time,
                    threshold_value=self.limits.min_grid_frequency if grid_frequency < self.limits.min_grid_frequency else self.limits.max_grid_frequency,
                    current_value=grid_frequency
                ))
        
        # Check mechanical failures (torque limits)
        torque = system_state.get('torque', 0.0)
        if abs(torque) > self.limits.max_torque:
            if EmergencyType.MECHANICAL_FAILURE not in self.active_emergencies:
                new_emergencies.append(EmergencyCondition(
                    emergency_type=EmergencyType.MECHANICAL_FAILURE,
                    priority=self.emergency_priorities[EmergencyType.MECHANICAL_FAILURE],
                    description=f"Excessive torque: {abs(torque):.1f} N·m > {self.limits.max_torque} N·m",
                    detected_time=current_time,
                    threshold_value=self.limits.max_torque,
                    current_value=abs(torque)
                ))
        
        return new_emergencies
    
    def _handle_new_emergency(self, emergency: EmergencyCondition, current_time: float):
        """Handle a newly detected emergency condition"""
        logger.error(f"EMERGENCY DETECTED: {emergency.description}")
        
        # Add to emergency conditions
        self.emergency_conditions.append(emergency)
        self.active_emergencies.add(emergency.emergency_type)
        
        # Update metrics
        self.response_metrics['total_emergencies'] += 1
        self.detection_time = current_time
        
        # Activate emergency response
        if not self.emergency_active:
            self.emergency_active = True
            logger.critical("EMERGENCY RESPONSE ACTIVATED")
        
        # Initiate shutdown for critical emergencies
        if emergency.priority == EmergencyPriority.CRITICAL and not self.shutdown_initiated:
            self._initiate_emergency_shutdown(current_time)
    
    def _initiate_emergency_shutdown(self, current_time: float):
        """Initiate emergency shutdown sequence"""
        logger.critical("EMERGENCY SHUTDOWN INITIATED")
        
        self.shutdown_initiated = True
        self.shutdown_start_time = current_time
        self.shutdown_phase = self.shutdown_phases[0]
        self.shutdown_complete = False
    
    def _update_emergency_response(self, system_state: Dict, current_time: float) -> Dict:
        """Update emergency response and generate commands"""
        
        if not self.emergency_active:
            return {'emergency_active': False}
        
        # Generate emergency response commands
        commands = {
            'emergency_active': True,
            'active_emergencies': list(self.active_emergencies),
            'emergency_conditions': [
                {
                    'type': cond.emergency_type.value,
                    'priority': cond.priority.value,
                    'description': cond.description,
                    'detected_time': cond.detected_time,
                    'acknowledged': cond.acknowledged
                }
                for cond in self.emergency_conditions if not cond.resolved
            ]
        }
        
        # Handle shutdown sequence
        if self.shutdown_initiated and not self.shutdown_complete:
            shutdown_commands = self._process_shutdown_sequence(system_state, current_time)
            commands.update(shutdown_commands)
        
        # Generate priority-based response commands
        highest_priority = self._get_highest_priority_emergency()
        if highest_priority:
            priority_commands = self._generate_priority_response(highest_priority)
            commands.update(priority_commands)
        
        # Check for emergency resolution
        self._check_emergency_resolution(system_state, current_time)
        
        return commands
    
    def _process_shutdown_sequence(self, system_state: Dict, current_time: float) -> Dict:
        """Process emergency shutdown sequence"""
        shutdown_duration = current_time - self.shutdown_start_time
        phase_index = min(len(self.shutdown_phases) - 1, int(shutdown_duration / 2.0))  # 2 seconds per phase
        self.shutdown_phase = self.shutdown_phases[phase_index]
        
        shutdown_commands = {
            'emergency_shutdown': True,
            'shutdown_phase': self.shutdown_phase,
            'shutdown_duration': shutdown_duration
        }
        
        # Phase-specific commands
        if self.shutdown_phase == "disconnect_grid":
            shutdown_commands.update({
                'electrical_commands': {
                    'grid_disconnect': True,
                    'generator_emergency_stop': True
                }
            })
        
        elif self.shutdown_phase == "stop_injections":
            shutdown_commands.update({
                'pneumatic_commands': {
                    'injection_stop': True,
                    'compressor_stop': True
                }
            })
        
        elif self.shutdown_phase == "engage_brakes":
            shutdown_commands.update({
                'mechanical_commands': {
                    'emergency_brake': True,
                    'clutch_disengage': True
                }
            })
        
        elif self.shutdown_phase == "isolate_pneumatics":
            shutdown_commands.update({
                'pneumatic_commands': {
                    'tank_isolation': True,
                    'pressure_relief': True
                }
            })
        
        elif self.shutdown_phase == "secure_electrical":
            shutdown_commands.update({
                'electrical_commands': {
                    'power_isolation': True,
                    'control_power_maintain': True  # Keep control power for monitoring
                }
            })
        
        elif self.shutdown_phase == "complete":
            self.shutdown_complete = True
            self.shutdown_time = shutdown_duration
            shutdown_commands.update({
                'shutdown_complete': True,
                'system_secured': True
            })
            logger.critical(f"Emergency shutdown complete in {shutdown_duration:.1f}s")
        
        return shutdown_commands
    
    def _get_highest_priority_emergency(self) -> Optional[EmergencyCondition]:
        """Get the highest priority active emergency"""
        active_conditions = [cond for cond in self.emergency_conditions if not cond.resolved]
        if not active_conditions:
            return None
        
        return min(active_conditions, key=lambda x: x.priority.value)
    
    def _generate_priority_response(self, emergency: EmergencyCondition) -> Dict:
        """Generate response commands based on emergency priority"""
        commands = {}
        
        if emergency.priority == EmergencyPriority.CRITICAL:
            commands.update({
                'immediate_action_required': True,
                'load_shed_percentage': 100,  # Shed all load
                'speed_limit_override': 50.0  # Severe speed limitation
            })
        
        elif emergency.priority == EmergencyPriority.HIGH:
            commands.update({
                'rapid_response_required': True,
                'load_shed_percentage': 75,   # Shed most load
                'speed_limit_override': 200.0  # Moderate speed limitation
            })
        
        elif emergency.priority == EmergencyPriority.MEDIUM:
            commands.update({
                'controlled_response_required': True,
                'load_shed_percentage': 25,   # Shed some load
                'monitoring_enhanced': True
            })
        
        return commands
    
    def _check_emergency_resolution(self, system_state: Dict, current_time: float):
        """Check if emergency conditions have been resolved"""
        resolved_emergencies = []
        
        for emergency in self.emergency_conditions:
            if emergency.resolved:
                continue
            
            # Check if condition is no longer present
            if self._is_emergency_resolved(emergency, system_state):
                emergency.resolved = True
                resolved_emergencies.append(emergency)
                logger.info(f"Emergency resolved: {emergency.description}")
        
        # Remove resolved emergencies from active set
        for emergency in resolved_emergencies:
            if emergency.emergency_type in self.active_emergencies:
                self.active_emergencies.remove(emergency.emergency_type)
        
        # Deactivate emergency response if no active emergencies
        if not self.active_emergencies and self.emergency_active:
            self.emergency_active = False
            logger.info("All emergencies resolved - emergency response deactivated")
    
    def _is_emergency_resolved(self, emergency: EmergencyCondition, system_state: Dict) -> bool:
        """Check if a specific emergency condition is resolved"""
        
        if emergency.emergency_type == EmergencyType.OVERSPEED:
            flywheel_speed = system_state.get('flywheel_speed_rpm', 0.0)
            return flywheel_speed < self.limits.max_flywheel_speed * 0.9  # 10% hysteresis
        
        elif emergency.emergency_type == EmergencyType.OVERPRESSURE:
            tank_pressure = system_state.get('pneumatics', {}).get('tank_pressure', 0.0)
            return tank_pressure < self.limits.max_tank_pressure * 0.9
        
        elif emergency.emergency_type == EmergencyType.OVERTEMPERATURE:
            component_temps = system_state.get('component_temperatures', {})
            max_temp = max(component_temps.values()) if component_temps else 0.0
            return max_temp < self.limits.max_component_temperature * 0.9
        
        elif emergency.emergency_type == EmergencyType.ELECTRICAL_FAULT:
            grid_voltage = system_state.get('grid_voltage', 480.0)
            return (self.limits.min_grid_voltage * 1.05 <= grid_voltage <= self.limits.max_grid_voltage * 0.95)
        
        elif emergency.emergency_type == EmergencyType.GRID_DISTURBANCE:
            grid_frequency = system_state.get('grid_frequency', 60.0)
            return (self.limits.min_grid_frequency * 1.01 <= grid_frequency <= self.limits.max_grid_frequency * 0.99)
        
        elif emergency.emergency_type == EmergencyType.MECHANICAL_FAILURE:
            torque = system_state.get('torque', 0.0)
            return abs(torque) < self.limits.max_torque * 0.8
        
        return False
    
    def trigger_manual_emergency_stop(self, reason: str, current_time: float) -> Dict:
        """Trigger manual emergency stop"""
        logger.critical(f"Manual emergency stop triggered: {reason}")
        
        emergency = EmergencyCondition(
            emergency_type=EmergencyType.MANUAL_STOP,
            priority=self.emergency_priorities[EmergencyType.MANUAL_STOP],
            description=f"Manual emergency stop: {reason}",
            detected_time=current_time
        )
        
        self._handle_new_emergency(emergency, current_time)
        self._initiate_emergency_shutdown(current_time)
        
        return {
            'emergency_active': True,
            'manual_stop_acknowledged': True,
            'shutdown_initiated': True
        }
    
    def acknowledge_emergency(self, emergency_type: str) -> bool:
        """Acknowledge an emergency condition"""
        for emergency in self.emergency_conditions:
            if emergency.emergency_type.value == emergency_type and not emergency.acknowledged:
                emergency.acknowledged = True
                logger.info(f"Emergency acknowledged: {emergency.description}")
                return True
        return False
    
    def _update_emergency_metrics(self, current_time: float):
        """Update emergency response metrics"""
        if self.detection_time > 0 and self.response_time == 0:
            self.response_time = current_time - self.detection_time
            
            # Update average response time
            total = self.response_metrics['total_emergencies']
            avg_response = self.response_metrics['average_response_time']
            self.response_metrics['average_response_time'] = (avg_response * (total - 1) + self.response_time) / total
        
        if self.shutdown_complete and self.shutdown_time < self.response_metrics['fastest_shutdown']:
            self.response_metrics['fastest_shutdown'] = self.shutdown_time
    
    def get_emergency_status(self) -> Dict:
        """Get current emergency system status"""
        return {
            'emergency_active': self.emergency_active,
            'active_emergencies': list(self.active_emergencies),
            'shutdown_initiated': self.shutdown_initiated,
            'shutdown_phase': self.shutdown_phase,
            'shutdown_complete': self.shutdown_complete,
            'emergency_count': len(self.emergency_conditions),
            'unresolved_count': len([e for e in self.emergency_conditions if not e.resolved]),
            'metrics': self.response_metrics
        }
    
    def reset(self):
        """Reset emergency response system"""
        logger.info("EmergencyResponseSystem reset")
        self.emergency_active = False
        self.emergency_conditions = []
        self.active_emergencies = set()
        self.shutdown_initiated = False
        self.shutdown_complete = False
        self.shutdown_phase = "none"
        self.detection_time = 0.0
        self.response_time = 0.0
        self.shutdown_time = 0.0
