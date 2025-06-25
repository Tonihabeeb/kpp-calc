"""
Grid Stabilization Controller - Phase 7 Week 4 Day 25-28

Advanced grid stabilization services using energy storage including:
- Fast frequency response (<1 second)
- Voltage support from storage inverters
- Black start capability
- Grid restart services
- Power quality improvement

Key Features:
- Ultra-fast frequency response (<1 second)
- Voltage support through reactive power
- Black start and grid restart capabilities
- Power quality filtering and conditioning
- Seamless transition between grid-tied and islanded modes
"""

import math
import time
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum


class StabilizationMode(Enum):
    """Grid stabilization operating modes"""
    STANDBY = "standby"
    FREQUENCY_SUPPORT = "frequency_support"
    VOLTAGE_SUPPORT = "voltage_support"
    BLACK_START = "black_start"
    GRID_FORMING = "grid_forming"
    POWER_QUALITY = "power_quality"
    EMERGENCY = "emergency"


@dataclass
class StabilizationSpecs:
    """Grid stabilization controller specifications"""
    max_power_kw: float = 250.0          # Maximum power output
    response_time_ms: float = 500.0       # Response time in milliseconds
    frequency_deadband: float = 0.02      # Frequency deadband (Hz)
    voltage_deadband: float = 0.02        # Voltage deadband (pu)
    droop_frequency: float = 0.04         # Frequency droop (Hz/pu)
    droop_voltage: float = 0.05           # Voltage droop (V/pu)
    max_reactive_power: float = 150.0     # Maximum reactive power (kVAR)
    black_start_capability: bool = True   # Black start capability
    grid_forming_capability: bool = True  # Grid forming capability


@dataclass
class GridConditions:
    """Current grid conditions for stabilization"""
    frequency: float = 50.0               # Grid frequency (Hz)
    voltage: float = 1.0                  # Grid voltage (pu)
    phase_angle: float = 0.0              # Phase angle (degrees)
    rocof: float = 0.0                    # Rate of change of frequency (Hz/s)
    voltage_thd: float = 0.02             # Voltage total harmonic distortion
    grid_connected: bool = True           # Grid connection status
    fault_detected: bool = False          # Fault detection status


class GridStabilizationController:
    """
    Advanced grid stabilization controller using energy storage.
    
    Provides fast frequency response, voltage support, black start capability,
    and power quality services using battery storage systems.
    """
    
    def __init__(self, specs: Optional[StabilizationSpecs] = None):
        """Initialize grid stabilization controller"""
        self.specs = specs or StabilizationSpecs()
        self.mode = StabilizationMode.STANDBY
        
        # Operating state
        self.active = False
        self.last_update = time.time()
        
        # Control setpoints
        self.active_power_setpoint = 0.0      # Active power setpoint (kW)
        self.reactive_power_setpoint = 0.0    # Reactive power setpoint (kVAR)
        self.frequency_setpoint = 50.0        # Frequency setpoint (Hz)
        self.voltage_setpoint = 1.0           # Voltage setpoint (pu)
        
        # Control gains
        self.kp_frequency = 20.0              # Frequency control proportional gain
        self.ki_frequency = 5.0               # Frequency control integral gain
        self.kp_voltage = 15.0                # Voltage control proportional gain
        self.ki_voltage = 3.0                 # Voltage control integral gain
        
        # Integrator states
        self.frequency_integrator = 0.0
        self.voltage_integrator = 0.0
        
        # Performance tracking
        self.frequency_events = 0
        self.voltage_events = 0
        self.black_start_events = 0
        self.response_times = []
        self.service_availability = 1.0
        self.total_energy_provided = 0.0
        
        # Event detection
        self.last_frequency = 50.0
        self.last_voltage = 1.0
        self.event_start_time = None
        
        # Grid forming parameters
        self.grid_forming_active = False
        self.virtual_impedance = complex(0.1, 0.2)  # Virtual impedance for grid forming
        
    def update(self, dt: float, grid_conditions: Dict[str, Any], 
               battery_status: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update grid stabilization control
        
        Args:
            dt: Time step in seconds
            grid_conditions: Current grid conditions
            battery_status: Battery system status
            
        Returns:
            Grid stabilization status and control commands
        """
        if not self.active:
            return self._get_status()
        
        # Parse grid conditions
        conditions = self._parse_grid_conditions(grid_conditions)
        
        # Detect grid events
        event_detected = self._detect_grid_events(conditions, dt)
        
        # Determine stabilization mode
        self._determine_stabilization_mode(conditions, battery_status)
        
        # Execute stabilization control
        control_commands = self._execute_stabilization_control(conditions, battery_status, dt)
        
        # Update performance metrics
        self._update_performance_metrics(dt, conditions, control_commands)
        
        return {
            **self._get_status(),
            'control_commands': control_commands,
            'event_detected': event_detected
        }
    
    def _parse_grid_conditions(self, grid_conditions: Dict[str, Any]) -> GridConditions:
        """Parse grid conditions from input dictionary"""
        return GridConditions(
            frequency=grid_conditions.get('frequency', 50.0),
            voltage=grid_conditions.get('voltage', 1.0),
            phase_angle=grid_conditions.get('phase_angle', 0.0),
            rocof=grid_conditions.get('rocof', 0.0),
            voltage_thd=grid_conditions.get('voltage_thd', 0.02),
            grid_connected=grid_conditions.get('grid_connected', True),
            fault_detected=grid_conditions.get('fault_detected', False)
        )
    
    def _detect_grid_events(self, conditions: GridConditions, dt: float) -> bool:
        """Detect grid disturbance events"""
        
        event_detected = False
        current_time = time.time()
        
        # Frequency event detection
        freq_deviation = abs(conditions.frequency - 50.0)
        if freq_deviation > self.specs.frequency_deadband:
            if self.event_start_time is None:
                self.event_start_time = current_time
                self.frequency_events += 1
            event_detected = True
        
        # Voltage event detection  
        voltage_deviation = abs(conditions.voltage - 1.0)
        if voltage_deviation > self.specs.voltage_deadband:
            if self.event_start_time is None:
                self.event_start_time = current_time
                self.voltage_events += 1
            event_detected = True
        
        # ROCOF event detection
        if abs(conditions.rocof) > 0.5:  # 0.5 Hz/s threshold
            if self.event_start_time is None:
                self.event_start_time = current_time
            event_detected = True
        
        # Grid disconnect detection
        if not conditions.grid_connected or conditions.fault_detected:
            if self.event_start_time is None:
                self.event_start_time = current_time
            event_detected = True
        
        # Record response time when event ends
        if not event_detected and self.event_start_time is not None:
            response_time = current_time - self.event_start_time
            self.response_times.append(response_time)
            self.event_start_time = None
        
        return event_detected
    
    def _determine_stabilization_mode(self, conditions: GridConditions, battery_status: Dict[str, Any]):
        """Determine optimal stabilization mode"""
        
        battery_available = battery_status.get('active', False) and battery_status.get('soc', 0) > 0.1
        
        # Priority 1: Black start mode
        if not conditions.grid_connected and self.specs.black_start_capability and battery_available:
            self.mode = StabilizationMode.BLACK_START
            return
        
        # Priority 2: Grid forming mode (islanded operation)
        if not conditions.grid_connected and self.specs.grid_forming_capability and battery_available:
            self.mode = StabilizationMode.GRID_FORMING
            return
        
        # Priority 3: Emergency mode (severe grid disturbances)
        if (abs(conditions.frequency - 50.0) > 1.0 or 
            abs(conditions.voltage - 1.0) > 0.15 or
            abs(conditions.rocof) > 2.0):
            self.mode = StabilizationMode.EMERGENCY
            return
        
        # Priority 4: Frequency support
        if abs(conditions.frequency - 50.0) > self.specs.frequency_deadband and battery_available:
            self.mode = StabilizationMode.FREQUENCY_SUPPORT
            return
        
        # Priority 5: Voltage support
        if abs(conditions.voltage - 1.0) > self.specs.voltage_deadband:
            self.mode = StabilizationMode.VOLTAGE_SUPPORT
            return
        
        # Priority 6: Power quality improvement
        if conditions.voltage_thd > 0.05:  # 5% THD threshold
            self.mode = StabilizationMode.POWER_QUALITY
            return
        
        # Default: Standby
        self.mode = StabilizationMode.STANDBY
    
    def _execute_stabilization_control(self, conditions: GridConditions, 
                                     battery_status: Dict[str, Any], dt: float) -> Dict[str, Any]:
        """Execute stabilization control based on current mode"""
        
        control_commands = {
            'active_power_kw': 0.0,
            'reactive_power_kvar': 0.0,
            'frequency_setpoint': 50.0,
            'voltage_setpoint': 1.0,
            'grid_forming': False,
            'black_start': False
        }
        
        if self.mode == StabilizationMode.BLACK_START:
            control_commands.update(self._black_start_control(conditions, battery_status))
            
        elif self.mode == StabilizationMode.GRID_FORMING:
            control_commands.update(self._grid_forming_control(conditions, battery_status, dt))
            
        elif self.mode == StabilizationMode.FREQUENCY_SUPPORT:
            control_commands.update(self._frequency_support_control(conditions, battery_status, dt))
            
        elif self.mode == StabilizationMode.VOLTAGE_SUPPORT:
            control_commands.update(self._voltage_support_control(conditions, battery_status, dt))
            
        elif self.mode == StabilizationMode.EMERGENCY:
            control_commands.update(self._emergency_control(conditions, battery_status))
            
        elif self.mode == StabilizationMode.POWER_QUALITY:
            control_commands.update(self._power_quality_control(conditions, battery_status))
        
        # Apply power limits
        control_commands = self._apply_power_limits(control_commands, battery_status)
        
        return control_commands
    
    def _black_start_control(self, conditions: GridConditions, battery_status: Dict[str, Any]) -> Dict[str, Any]:
        """Black start control sequence"""
        
        self.black_start_events += 1
        
        return {
            'active_power_kw': 50.0,  # Initial energization power
            'reactive_power_kvar': 0.0,
            'frequency_setpoint': 50.0,
            'voltage_setpoint': 1.0,
            'grid_forming': True,
            'black_start': True
        }
    
    def _grid_forming_control(self, conditions: GridConditions, 
                            battery_status: Dict[str, Any], dt: float) -> Dict[str, Any]:
        """Grid forming control for islanded operation"""
        
        self.grid_forming_active = True
        
        # Voltage and frequency regulation in grid forming mode
        voltage_error = self.voltage_setpoint - conditions.voltage
        frequency_error = self.frequency_setpoint - conditions.frequency
        
        # PI control for voltage
        self.voltage_integrator += voltage_error * dt
        voltage_control = (self.kp_voltage * voltage_error + 
                         self.ki_voltage * self.voltage_integrator)
        
        # PI control for frequency
        self.frequency_integrator += frequency_error * dt
        frequency_control = (self.kp_frequency * frequency_error + 
                           self.ki_frequency * self.frequency_integrator)
        
        return {
            'active_power_kw': frequency_control * 10.0,  # Scale to power
            'reactive_power_kvar': voltage_control * 5.0,  # Scale to reactive power
            'frequency_setpoint': self.frequency_setpoint,
            'voltage_setpoint': self.voltage_setpoint,
            'grid_forming': True,
            'black_start': False
        }
    
    def _frequency_support_control(self, conditions: GridConditions, 
                                 battery_status: Dict[str, Any], dt: float) -> Dict[str, Any]:
        """Fast frequency response control"""
        
        frequency_error = conditions.frequency - 50.0
        
        # Droop control
        power_response = -frequency_error / self.specs.droop_frequency * self.specs.max_power_kw
        
        # Add derivative control for ROCOF response
        rocof_response = -conditions.rocof * 50.0  # Fast response to ROCOF
        
        # Total power command
        total_power = power_response + rocof_response
        
        # Apply deadband
        if abs(frequency_error) < self.specs.frequency_deadband:
            total_power = 0.0
        
        return {
            'active_power_kw': total_power,
            'reactive_power_kvar': 0.0,
            'frequency_setpoint': 50.0,
            'voltage_setpoint': 1.0,
            'grid_forming': False,
            'black_start': False
        }
    
    def _voltage_support_control(self, conditions: GridConditions, 
                               battery_status: Dict[str, Any], dt: float) -> Dict[str, Any]:
        """Voltage support through reactive power control"""
        
        voltage_error = conditions.voltage - 1.0
        
        # Droop control for reactive power
        reactive_power = -voltage_error / self.specs.droop_voltage * self.specs.max_reactive_power
        
        # Apply deadband
        if abs(voltage_error) < self.specs.voltage_deadband:
            reactive_power = 0.0
        
        return {
            'active_power_kw': 0.0,
            'reactive_power_kvar': reactive_power,
            'frequency_setpoint': 50.0,
            'voltage_setpoint': 1.0,
            'grid_forming': False,
            'black_start': False
        }
    
    def _emergency_control(self, conditions: GridConditions, battery_status: Dict[str, Any]) -> Dict[str, Any]:
        """Emergency control for severe grid disturbances"""
        
        # Maximum response for emergency conditions
        frequency_error = conditions.frequency - 50.0
        voltage_error = conditions.voltage - 1.0
        
        # Maximum power response
        power_response = 0.0
        if abs(frequency_error) > 0.5:
            power_response = -math.copysign(self.specs.max_power_kw * 0.8, frequency_error)
        
        # Maximum reactive power response
        reactive_response = 0.0
        if abs(voltage_error) > 0.1:
            reactive_response = -math.copysign(self.specs.max_reactive_power * 0.8, voltage_error)
        
        return {
            'active_power_kw': power_response,
            'reactive_power_kvar': reactive_response,
            'frequency_setpoint': 50.0,
            'voltage_setpoint': 1.0,
            'grid_forming': False,
            'black_start': False
        }
    
    def _power_quality_control(self, conditions: GridConditions, battery_status: Dict[str, Any]) -> Dict[str, Any]:
        """Power quality improvement control"""
        
        # Simple power quality control - could be expanded with harmonic filtering
        reactive_power = 0.0
        
        # Voltage support for power quality
        if conditions.voltage_thd > 0.05:
            voltage_correction = (conditions.voltage_thd - 0.02) * 100.0
            reactive_power = -voltage_correction
        
        return {
            'active_power_kw': 0.0,
            'reactive_power_kvar': reactive_power,
            'frequency_setpoint': 50.0,
            'voltage_setpoint': 1.0,
            'grid_forming': False,
            'black_start': False
        }
    
    def _apply_power_limits(self, commands: Dict[str, Any], battery_status: Dict[str, Any]) -> Dict[str, Any]:
        """Apply power and battery limits to control commands"""
        
        # Get battery constraints
        battery_soc = battery_status.get('soc', 0.5)
        battery_health = battery_status.get('health', 1.0)
        available_power = self.specs.max_power_kw * battery_health
        
        # Limit active power based on battery SOC
        if commands['active_power_kw'] > 0:  # Charging (consuming power)
            if battery_soc > 0.9:
                commands['active_power_kw'] *= 0.1  # Reduced charging near full
        else:  # Discharging (providing power)
            if battery_soc < 0.2:
                commands['active_power_kw'] *= 0.1  # Reduced discharging near empty
        
        # Apply absolute power limits
        commands['active_power_kw'] = max(-available_power, 
                                        min(available_power, commands['active_power_kw']))
        
        commands['reactive_power_kvar'] = max(-self.specs.max_reactive_power,
                                            min(self.specs.max_reactive_power, commands['reactive_power_kvar']))
        
        return commands
    
    def _update_performance_metrics(self, dt: float, conditions: GridConditions, 
                                  commands: Dict[str, Any]):
        """Update performance tracking metrics"""
        
        # Track energy provided
        energy_provided = abs(commands['active_power_kw']) * dt / 3600.0  # kWh
        self.total_energy_provided += energy_provided
        
        # Update service availability
        if self.mode != StabilizationMode.STANDBY:
            # Service is available and responding
            self.service_availability = min(1.0, self.service_availability + 0.01 * dt)
        
        # Store grid conditions for trend analysis
        self.last_frequency = conditions.frequency
        self.last_voltage = conditions.voltage
    
    def _get_status(self) -> Dict[str, Any]:
        """Get current grid stabilization status"""
        
        avg_response_time = sum(self.response_times[-10:]) / len(self.response_times[-10:]) if self.response_times else 0.0
        
        return {
            'active': self.active,
            'mode': self.mode.value,
            'active_power_setpoint': self.active_power_setpoint,
            'reactive_power_setpoint': self.reactive_power_setpoint,
            'frequency_setpoint': self.frequency_setpoint,
            'voltage_setpoint': self.voltage_setpoint,
            'grid_forming_active': self.grid_forming_active,
            'frequency_events': self.frequency_events,
            'voltage_events': self.voltage_events,
            'black_start_events': self.black_start_events,
            'avg_response_time': avg_response_time,
            'service_availability': self.service_availability,
            'total_energy_provided': self.total_energy_provided,
            'response_time_ms': self.specs.response_time_ms,
            'black_start_capable': self.specs.black_start_capability,
            'grid_forming_capable': self.specs.grid_forming_capability
        }
    
    def start_service(self):
        """Start grid stabilization service"""
        self.active = True
        self.last_update = time.time()
        self.mode = StabilizationMode.STANDBY
    
    def stop_service(self):
        """Stop grid stabilization service"""
        self.active = False
        self.mode = StabilizationMode.STANDBY
        self.grid_forming_active = False
        self.active_power_setpoint = 0.0
        self.reactive_power_setpoint = 0.0
    
    def initiate_black_start(self) -> bool:
        """Initiate black start sequence"""
        if self.specs.black_start_capability and self.active:
            self.mode = StabilizationMode.BLACK_START
            return True
        return False
    
    def enable_grid_forming(self, enable: bool):
        """Enable or disable grid forming capability"""
        self.specs.grid_forming_capability = enable
        if not enable and self.mode == StabilizationMode.GRID_FORMING:
            self.mode = StabilizationMode.STANDBY
    
    def set_control_parameters(self, frequency_droop: float = None, voltage_droop: float = None,
                             response_time_ms: float = None):
        """Update control parameters"""
        if frequency_droop is not None:
            self.specs.droop_frequency = frequency_droop
        if voltage_droop is not None:
            self.specs.droop_voltage = voltage_droop
        if response_time_ms is not None:
            self.specs.response_time_ms = response_time_ms
    
    def reset_performance_metrics(self):
        """Reset performance tracking metrics"""
        self.frequency_events = 0
        self.voltage_events = 0
        self.black_start_events = 0
        self.response_times.clear()
        self.service_availability = 1.0
        self.total_energy_provided = 0.0
    
    def get_service_capability(self) -> Dict[str, Any]:
        """Get current service capability information"""
        return {
            'frequency_support': True,
            'voltage_support': True,
            'black_start': self.specs.black_start_capability,
            'grid_forming': self.specs.grid_forming_capability,
            'power_quality': True,
            'max_active_power_kw': self.specs.max_power_kw,
            'max_reactive_power_kvar': self.specs.max_reactive_power,
            'response_time_ms': self.specs.response_time_ms,
            'frequency_deadband_hz': self.specs.frequency_deadband,
            'voltage_deadband_pu': self.specs.voltage_deadband
        }
    
    def is_stabilizing(self) -> bool:
        """Check if grid stabilization is currently active"""
        return self.active and self.mode != StabilizationMode.STANDBY
    
    def reset(self):
        """Reset grid stabilization controller to initial state"""
        self.stop_service()
        self.frequency_integrator = 0.0
        self.voltage_integrator = 0.0
        self.event_start_time = None
        self.grid_forming_active = False
        self.reset_performance_metrics()


def create_grid_stabilization_controller(max_power_kw: float = 250.0, 
                                        response_time_ms: float = 500.0) -> GridStabilizationController:
    """
    Factory function to create a grid stabilization controller
    
    Args:
        max_power_kw: Maximum power capability in kW
        response_time_ms: Response time in milliseconds
        
    Returns:
        Configured GridStabilizationController instance
    """
    specs = StabilizationSpecs(
        max_power_kw=max_power_kw,
        response_time_ms=response_time_ms
    )
    return GridStabilizationController(specs)
