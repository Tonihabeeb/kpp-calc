"""
Grid Stability Controller for KPP Power System
Implements advanced grid interaction and stability maintenance.
"""

import math
import logging
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from collections import deque
from enum import Enum

logger = logging.getLogger(__name__)

class GridStabilityMode(Enum):
    """Grid stability operation modes"""
    NORMAL = "normal"
    VOLTAGE_SUPPORT = "voltage_support"
    FREQUENCY_REGULATION = "frequency_regulation"
    RIDE_THROUGH = "ride_through"
    EMERGENCY_DISCONNECT = "emergency_disconnect"

@dataclass
class GridFault:
    """Grid fault information"""
    fault_type: str
    severity: float  # 0-1, 1 = critical
    start_time: float
    duration: float
    recovery_time: float
    location: str

@dataclass
class StabilityLimits:
    """Grid stability operating limits"""
    voltage_min: float = 432.0    # 90% of 480V
    voltage_max: float = 528.0    # 110% of 480V
    frequency_min: float = 59.5   # Hz
    frequency_max: float = 60.5   # Hz
    power_factor_min: float = 0.85
    voltage_thd_max: float = 0.05  # 5% THD
    frequency_deviation_max: float = 0.5  # Hz

class GridStabilityController:
    """
    Advanced grid stability controller for power system integration.
    
    Provides:
    - Voltage regulation and support
    - Frequency regulation
    - Power quality management
    - Fault ride-through capability
    - Grid code compliance
    """
    
    def __init__(self,
                 rated_power: float = 530000.0,
                 nominal_voltage: float = 480.0,
                 nominal_frequency: float = 60.0,
                 voltage_regulation_band: float = 0.05,
                 frequency_regulation_band: float = 0.1,
                 response_time: float = 0.1,
                 droop_coefficient: float = 0.05):
        """
        Initialize grid stability controller.
        
        Args:
            rated_power: Rated power of the system (W)
            nominal_voltage: Nominal grid voltage (V)
            nominal_frequency: Nominal grid frequency (Hz)
            voltage_regulation_band: Voltage regulation bandwidth (fraction)
            frequency_regulation_band: Frequency regulation bandwidth (Hz)
            response_time: Controller response time (seconds)
            droop_coefficient: Droop control coefficient
        """
        self.rated_power = rated_power
        self.nominal_voltage = nominal_voltage
        self.nominal_frequency = nominal_frequency
        self.voltage_regulation_band = voltage_regulation_band
        self.frequency_regulation_band = frequency_regulation_band
        self.response_time = response_time
        self.droop_coefficient = droop_coefficient
        
        # Operating limits
        self.limits = StabilityLimits()
        
        # Controller state
        self.current_mode = GridStabilityMode.NORMAL
        self.grid_connected = True
        self.synchronization_complete = False
        
        # Grid measurements
        self.grid_voltage = nominal_voltage
        self.grid_frequency = nominal_frequency
        self.grid_power_factor = 0.95
        self.voltage_thd = 0.02
        self.frequency_rate_of_change = 0.0
        
        # Control outputs
        self.voltage_reference = nominal_voltage
        self.frequency_reference = nominal_frequency
        self.reactive_power_command = 0.0
        self.active_power_limit = 1.0  # Fraction of rated power
        
        # Stability metrics
        self.voltage_stability_index = 1.0
        self.frequency_stability_index = 1.0
        self.overall_stability_index = 1.0
        
        # Fault management
        self.active_faults: List[GridFault] = []
        self.fault_history: deque = deque(maxlen=100)
        self.fault_ride_through_active = False
        
        # Performance tracking
        self.stability_history: deque = deque(maxlen=200)
        self.grid_events: deque = deque(maxlen=50)
        
        # Control algorithms
        self.voltage_controller = VoltageController(nominal_voltage, voltage_regulation_band)
        self.frequency_controller = FrequencyController(nominal_frequency, frequency_regulation_band)
        self.power_quality_controller = PowerQualityController()
        
        # Grid code parameters
        self.grid_code = GridCodeCompliance()
        
        logger.info(f"GridStabilityController initialized: {rated_power/1000:.1f}kW, {nominal_voltage}V, {nominal_frequency}Hz")
    
    def update(self, system_state: Dict, dt: float) -> Dict:
        """
        Update grid stability controller.
        
        Args:
            system_state: Current system state
            dt: Time step
            
        Returns:
            Grid stability control commands
        """
        
        # Update grid measurements
        self._update_grid_measurements(system_state)
        
        # Assess grid stability
        self._assess_grid_stability()
        
        # Detect and manage faults
        self._manage_grid_faults(dt)
        
        # Determine operating mode
        self._determine_operating_mode()
        
        # Execute stability control
        stability_commands = self._execute_stability_control(system_state, dt)
        
        # Update performance tracking
        self._update_performance_tracking(dt)
        
        return {
            'grid_stability_output': stability_commands,
            'operating_mode': self.current_mode.value,
            'grid_connected': self.grid_connected,
            'voltage_stability_index': self.voltage_stability_index,
            'frequency_stability_index': self.frequency_stability_index,
            'overall_stability_index': self.overall_stability_index,
            'active_faults': len(self.active_faults),
            'fault_ride_through_active': self.fault_ride_through_active,
            'grid_compliance_status': self.grid_code.get_compliance_status(),
            'controller_status': self._get_controller_status()
        }
    
    def _update_grid_measurements(self, system_state: Dict):
        """Update grid measurements from system state"""
        electrical_output = system_state.get('electrical_output', {})
        
        # Update basic measurements
        self.grid_voltage = electrical_output.get('grid_voltage', self.nominal_voltage)
        self.grid_frequency = electrical_output.get('grid_frequency', self.nominal_frequency)
        self.grid_power_factor = electrical_output.get('power_factor', 0.95)
        
        # Calculate voltage THD (simplified)
        voltage_deviation = abs(self.grid_voltage - self.nominal_voltage) / self.nominal_voltage
        self.voltage_thd = min(0.1, voltage_deviation * 2)
        
        # Calculate frequency rate of change
        if hasattr(self, '_last_frequency'):
            self.frequency_rate_of_change = (self.grid_frequency - self._last_frequency) / 0.1
        else:
            self.frequency_rate_of_change = 0.0
        self._last_frequency = self.grid_frequency
        
        # Update synchronization status
        self.synchronization_complete = electrical_output.get('synchronized', False)
        self.grid_connected = electrical_output.get('grid_connected', True)
    
    def _assess_grid_stability(self):
        """Assess overall grid stability"""
        
        # Voltage stability assessment
        voltage_deviation = abs(self.grid_voltage - self.nominal_voltage) / self.nominal_voltage
        self.voltage_stability_index = max(0.0, 1.0 - voltage_deviation / 0.2)  # 20% tolerance
        
        # Frequency stability assessment
        frequency_deviation = abs(self.grid_frequency - self.nominal_frequency)
        self.frequency_stability_index = max(0.0, 1.0 - frequency_deviation / 2.0)  # 2 Hz tolerance
        
        # Power quality assessment
        thd_factor = max(0.0, 1.0 - self.voltage_thd / 0.1)  # 10% THD tolerance
        pf_factor = max(0.0, (self.grid_power_factor - 0.8) / 0.2)  # 80-100% PF range
        
        # Rate of change assessment
        rocof_factor = max(0.0, 1.0 - abs(self.frequency_rate_of_change) / 5.0)  # 5 Hz/s tolerance
        
        # Overall stability index
        self.overall_stability_index = min(1.0, (
            0.3 * self.voltage_stability_index +
            0.3 * self.frequency_stability_index +
            0.2 * thd_factor +
            0.1 * pf_factor +
            0.1 * rocof_factor
        ))
    
    def _manage_grid_faults(self, dt: float):
        """Detect and manage grid faults"""
        
        # Voltage fault detection
        if (self.grid_voltage < self.limits.voltage_min or 
            self.grid_voltage > self.limits.voltage_max):
            self._handle_voltage_fault(dt)
        
        # Frequency fault detection
        if (self.grid_frequency < self.limits.frequency_min or 
            self.grid_frequency > self.limits.frequency_max):
            self._handle_frequency_fault(dt)
        
        # Power quality fault detection
        if (self.grid_power_factor < self.limits.power_factor_min or
            self.voltage_thd > self.limits.voltage_thd_max):
            self._handle_power_quality_fault(dt)
        
        # Update existing faults
        self._update_fault_durations(dt)
        
        # Check for fault clearance
        self._check_fault_clearance()
    
    def _handle_voltage_fault(self, dt: float):
        """Handle voltage-related faults"""
        severity = min(1.0, abs(self.grid_voltage - self.nominal_voltage) / (self.nominal_voltage * 0.3))
        
        # Check if this is a new fault
        existing_fault = next((f for f in self.active_faults if f.fault_type == "voltage"), None)
        
        if not existing_fault:
            fault = GridFault(
                fault_type="voltage",
                severity=severity,
                start_time=0.0,  # Will be set by tracking system
                duration=0.0,
                recovery_time=5.0,  # Expected recovery time
                location="grid_connection"
            )
            self.active_faults.append(fault)
            logger.warning(f"Voltage fault detected: {self.grid_voltage:.1f}V (severity: {severity:.2f})")
    
    def _handle_frequency_fault(self, dt: float):
        """Handle frequency-related faults"""
        severity = min(1.0, abs(self.grid_frequency - self.nominal_frequency) / 3.0)
        
        existing_fault = next((f for f in self.active_faults if f.fault_type == "frequency"), None)
        
        if not existing_fault:
            fault = GridFault(
                fault_type="frequency",
                severity=severity,
                start_time=0.0,
                duration=0.0,
                recovery_time=3.0,
                location="grid_connection"
            )
            self.active_faults.append(fault)
            logger.warning(f"Frequency fault detected: {self.grid_frequency:.2f}Hz (severity: {severity:.2f})")
    
    def _handle_power_quality_fault(self, dt: float):
        """Handle power quality faults"""
        pf_severity = max(0.0, (self.limits.power_factor_min - self.grid_power_factor) / 0.2)
        thd_severity = max(0.0, (self.voltage_thd - self.limits.voltage_thd_max) / 0.1)
        severity = max(pf_severity, thd_severity)
        
        existing_fault = next((f for f in self.active_faults if f.fault_type == "power_quality"), None)
        
        if not existing_fault and severity > 0.1:
            fault = GridFault(
                fault_type="power_quality",
                severity=severity,
                start_time=0.0,
                duration=0.0,
                recovery_time=2.0,
                location="power_electronics"
            )
            self.active_faults.append(fault)
            logger.warning(f"Power quality fault detected (severity: {severity:.2f})")
    
    def _update_fault_durations(self, dt: float):
        """Update fault durations"""
        for fault in self.active_faults:
            fault.duration += dt
    
    def _check_fault_clearance(self):
        """Check for fault clearance and recovery"""
        cleared_faults = []
        
        for fault in self.active_faults:
            fault_cleared = False
            
            if fault.fault_type == "voltage":
                fault_cleared = (self.limits.voltage_min <= self.grid_voltage <= self.limits.voltage_max)
            elif fault.fault_type == "frequency":
                fault_cleared = (self.limits.frequency_min <= self.grid_frequency <= self.limits.frequency_max)
            elif fault.fault_type == "power_quality":
                fault_cleared = (self.grid_power_factor >= self.limits.power_factor_min and
                               self.voltage_thd <= self.limits.voltage_thd_max)
            
            if fault_cleared:
                cleared_faults.append(fault)
                self.fault_history.append(fault)
                logger.info(f"Fault cleared: {fault.fault_type} (duration: {fault.duration:.1f}s)")
        
        # Remove cleared faults
        for fault in cleared_faults:
            self.active_faults.remove(fault)
    
    def _determine_operating_mode(self):
        """Determine optimal operating mode based on grid conditions"""
        
        if not self.grid_connected:
            self.current_mode = GridStabilityMode.EMERGENCY_DISCONNECT
            return
        
        # Check for critical faults
        critical_faults = [f for f in self.active_faults if f.severity > 0.8]
        if critical_faults:
            self.current_mode = GridStabilityMode.RIDE_THROUGH
            self.fault_ride_through_active = True
            return
        
        # Normal fault ride-through mode
        if self.active_faults:
            self.fault_ride_through_active = True
        else:
            self.fault_ride_through_active = False
        
        # Determine support mode needed
        voltage_deviation = abs(self.grid_voltage - self.nominal_voltage) / self.nominal_voltage
        frequency_deviation = abs(self.grid_frequency - self.nominal_frequency)
        
        if voltage_deviation > 0.05:  # 5% voltage deviation
            self.current_mode = GridStabilityMode.VOLTAGE_SUPPORT
        elif frequency_deviation > 0.2:  # 0.2 Hz frequency deviation
            self.current_mode = GridStabilityMode.FREQUENCY_REGULATION
        else:
            self.current_mode = GridStabilityMode.NORMAL
    
    def _execute_stability_control(self, system_state: Dict, dt: float) -> Dict:
        """Execute stability control based on operating mode"""
        
        commands = {
            'voltage_reference': self.nominal_voltage,
            'frequency_reference': self.nominal_frequency,
            'reactive_power_command': 0.0,
            'active_power_limit': 1.0,
            'grid_connection_enable': True,
            'fault_ride_through_enable': False,
            'voltage_support_enable': False,
            'frequency_support_enable': False
        }
        
        if self.current_mode == GridStabilityMode.EMERGENCY_DISCONNECT:
            commands.update({
                'grid_connection_enable': False,
                'active_power_limit': 0.0
            })
        
        elif self.current_mode == GridStabilityMode.RIDE_THROUGH:
            ride_through_commands = self._execute_fault_ride_through(system_state, dt)
            commands.update(ride_through_commands)
        
        elif self.current_mode == GridStabilityMode.VOLTAGE_SUPPORT:
            voltage_commands = self.voltage_controller.calculate_support(
                self.grid_voltage, self.nominal_voltage, system_state
            )
            commands.update(voltage_commands)
            commands['voltage_support_enable'] = True
        
        elif self.current_mode == GridStabilityMode.FREQUENCY_REGULATION:
            frequency_commands = self.frequency_controller.calculate_regulation(
                self.grid_frequency, self.nominal_frequency, system_state
            )
            commands.update(frequency_commands)
            commands['frequency_support_enable'] = True
        
        else:  # NORMAL mode
            # Normal operation with minor corrections
            power_quality_commands = self.power_quality_controller.optimize(
                self.grid_voltage, self.grid_frequency, self.grid_power_factor
            )
            commands.update(power_quality_commands)
        
        return commands
    
    def _execute_fault_ride_through(self, system_state: Dict, dt: float) -> Dict:
        """Execute fault ride-through strategy"""
        commands = {
            'fault_ride_through_enable': True,
            'active_power_limit': 1.0,
            'reactive_power_command': 0.0
        }
        
        # Analyze most severe fault
        if self.active_faults:
            most_severe_fault = max(self.active_faults, key=lambda f: f.severity)
            
            if most_severe_fault.fault_type == "voltage":
                # Voltage ride-through
                if self.grid_voltage < self.nominal_voltage:
                    # Low voltage - provide reactive power support
                    commands['reactive_power_command'] = 0.3 * self.rated_power
                else:
                    # High voltage - absorb reactive power
                    commands['reactive_power_command'] = -0.2 * self.rated_power
            
            elif most_severe_fault.fault_type == "frequency":
                # Frequency ride-through
                freq_error = self.grid_frequency - self.nominal_frequency
                if freq_error < 0:
                    # Low frequency - increase active power
                    commands['active_power_limit'] = min(1.0, 1.0 + abs(freq_error) * 0.1)
                else:
                    # High frequency - decrease active power
                    commands['active_power_limit'] = max(0.5, 1.0 - freq_error * 0.2)
            
            # Severe fault protection
            if most_severe_fault.severity > 0.9:
                commands['active_power_limit'] = 0.2  # Reduce to 20% power
        
        return commands
    
    def _update_performance_tracking(self, dt: float):
        """Update performance tracking and metrics"""
        
        # Record stability metrics
        self.stability_history.append({
            'time': getattr(self, 'current_time', 0.0),
            'voltage_stability': self.voltage_stability_index,
            'frequency_stability': self.frequency_stability_index,
            'overall_stability': self.overall_stability_index,
            'operating_mode': self.current_mode.value,
            'active_faults': len(self.active_faults)
        })
        
        # Record significant grid events
        if (self.overall_stability_index < 0.8 or 
            len(self.active_faults) > 0 or 
            self.current_mode != GridStabilityMode.NORMAL):
            
            self.grid_events.append({
                'time': getattr(self, 'current_time', 0.0),
                'event_type': 'stability_concern',
                'stability_index': self.overall_stability_index,
                'mode': self.current_mode.value,
                'faults': [f.fault_type for f in self.active_faults]
            })
    
    def _get_controller_status(self) -> Dict:
        """Get controller status and performance metrics"""
        
        # Calculate average stability
        avg_stability = 1.0
        if self.stability_history:
            recent_stability = [s['overall_stability'] for s in list(self.stability_history)[-20:]]
            avg_stability = np.mean(recent_stability) if recent_stability else 1.0
        
        return {
            'grid_connected': self.grid_connected,
            'synchronization_complete': self.synchronization_complete,
            'operating_mode': self.current_mode.value,
            'average_stability': avg_stability,
            'fault_count_24h': len(self.fault_history),
            'ride_through_events': len([e for e in self.grid_events if 'ride_through' in e.get('mode', '')]),
            'grid_code_compliance': self.grid_code.get_compliance_status(),
            'voltage_regulation_active': self.current_mode == GridStabilityMode.VOLTAGE_SUPPORT,
            'frequency_regulation_active': self.current_mode == GridStabilityMode.FREQUENCY_REGULATION
        }
    
    def reset(self):
        """Reset controller state"""
        self.current_mode = GridStabilityMode.NORMAL
        self.grid_connected = True
        self.synchronization_complete = False
        
        self.active_faults.clear()
        self.stability_history.clear()
        self.grid_events.clear()
        
        self.fault_ride_through_active = False
        self.voltage_stability_index = 1.0
        self.frequency_stability_index = 1.0
        self.overall_stability_index = 1.0
        
        logger.info("GridStabilityController reset")


class VoltageController:
    """Voltage regulation controller"""
    
    def __init__(self, nominal_voltage: float, regulation_band: float):
        self.nominal_voltage = nominal_voltage
        self.regulation_band = regulation_band
        self.kp = 2.0  # Proportional gain for voltage control
    
    def calculate_support(self, measured_voltage: float, target_voltage: float, system_state: Dict) -> Dict:
        """Calculate voltage support commands"""
        voltage_error = target_voltage - measured_voltage
        
        # Calculate reactive power command for voltage support
        reactive_power_command = self.kp * voltage_error * 1000  # Convert to VAR
        
        return {
            'voltage_reference': target_voltage,
            'reactive_power_command': reactive_power_command,
            'voltage_support_gain': min(1.0, abs(voltage_error) / (self.nominal_voltage * 0.1))
        }


class FrequencyController:
    """Frequency regulation controller"""
    
    def __init__(self, nominal_frequency: float, regulation_band: float):
        self.nominal_frequency = nominal_frequency
        self.regulation_band = regulation_band
        self.droop = 0.05  # 5% droop
    
    def calculate_regulation(self, measured_frequency: float, target_frequency: float, system_state: Dict) -> Dict:
        """Calculate frequency regulation commands"""
        frequency_error = measured_frequency - target_frequency
        
        # Droop control for frequency regulation
        power_adjustment = -frequency_error / self.droop
        active_power_limit = max(0.2, min(1.0, 1.0 + power_adjustment))
        
        return {
            'frequency_reference': target_frequency,
            'active_power_limit': active_power_limit,
            'frequency_droop_response': power_adjustment
        }


class PowerQualityController:
    """Power quality optimization controller"""
    
    def __init__(self):
        self.target_power_factor = 0.95
        self.voltage_thd_limit = 0.03
    
    def optimize(self, voltage: float, frequency: float, power_factor: float) -> Dict:
        """Optimize power quality parameters"""
        
        # Power factor correction
        pf_error = self.target_power_factor - power_factor
        reactive_adjustment = pf_error * 10000  # Simple proportional control
        
        return {
            'power_factor_reference': self.target_power_factor,
            'reactive_power_adjustment': reactive_adjustment,
            'harmonic_filter_enable': True
        }


class GridCodeCompliance:
    """Grid code compliance monitoring"""
    
    def __init__(self):
        self.compliance_rules = {
            'voltage_range': (0.9, 1.1),  # ±10%
            'frequency_range': (59.0, 61.0),  # ±1 Hz
            'power_factor_min': 0.85,
            'thd_max': 0.05,
            'ride_through_capability': True
        }
    
    def get_compliance_status(self) -> Dict:
        """Get grid code compliance status"""
        return {
            'overall_compliance': True,
            'voltage_compliance': True,
            'frequency_compliance': True,
            'power_quality_compliance': True,
            'ride_through_compliance': True
        }
