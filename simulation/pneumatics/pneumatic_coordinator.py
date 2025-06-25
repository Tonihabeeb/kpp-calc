"""
Pneumatic Control Coordinator for Phase 6: Control System Integration

This module implements the master control logic for the entire pneumatic system,
including PLC simulation, sensor integration, fault detection, and performance optimization.

Key Features:
- Real-time pressure regulation and monitoring
- Injection sequencing and timing coordination
- Safety monitoring and emergency shutdown procedures
- Performance optimization algorithms
- Fault detection and recovery systems
"""

import logging
import time
import math
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
import threading
from utils.logging_setup import setup_logging

# Phase 5 integration - use thermodynamic data for optimization
from simulation.pneumatics.thermodynamics import AdvancedThermodynamics
from simulation.pneumatics.heat_exchange import IntegratedHeatExchange

setup_logging()
logger = logging.getLogger(__name__)


class SystemState(Enum):
    """Pneumatic system operational states."""
    STARTUP = "startup"
    NORMAL = "normal"
    OPTIMIZATION = "optimization"
    FAULT = "fault"
    EMERGENCY_STOP = "emergency_stop"
    SHUTDOWN = "shutdown"


class FaultType(Enum):
    """Types of system faults."""
    PRESSURE_DROP = "pressure_drop"
    COMPRESSOR_FAILURE = "compressor_failure"
    INJECTION_FAILURE = "injection_failure"
    THERMAL_OVERLOAD = "thermal_overload"
    SENSOR_FAILURE = "sensor_failure"
    COMMUNICATION_LOSS = "communication_loss"


@dataclass
class SensorReading:
    """Represents a sensor reading with timestamp and validation."""
    sensor_id: str
    value: float
    unit: str
    timestamp: float
    is_valid: bool = True
    quality: float = 1.0  # 0.0 to 1.0


@dataclass
class PneumaticSensors:
    """Collection of pneumatic system sensors."""
    # Pressure sensors (Pa)
    tank_pressure: SensorReading = field(default_factory=lambda: SensorReading("tank_pressure", 0.0, "Pa", time.time()))
    injection_pressure: SensorReading = field(default_factory=lambda: SensorReading("injection_pressure", 0.0, "Pa", time.time()))
    line_pressures: List[SensorReading] = field(default_factory=list)
    
    # Temperature sensors (K)
    compressor_temp: SensorReading = field(default_factory=lambda: SensorReading("compressor_temp", 293.15, "K", time.time()))
    tank_temp: SensorReading = field(default_factory=lambda: SensorReading("tank_temp", 293.15, "K", time.time()))
    water_temp: SensorReading = field(default_factory=lambda: SensorReading("water_temp", 288.15, "K", time.time()))
    
    # Flow sensors (m³/s)
    compressor_flow: SensorReading = field(default_factory=lambda: SensorReading("compressor_flow", 0.0, "m³/s", time.time()))
    injection_flow: SensorReading = field(default_factory=lambda: SensorReading("injection_flow", 0.0, "m³/s", time.time()))
    
    # Position sensors (for floaters)
    floater_positions: List[SensorReading] = field(default_factory=list)


@dataclass
class ControlParameters:
    """Pneumatic system control parameters."""
    # Pressure control
    target_pressure: float = 300000.0  # Pa (3 bar)
    pressure_tolerance: float = 10000.0  # Pa (±0.1 bar)
    max_pressure: float = 350000.0  # Pa (3.5 bar safety limit)
    min_pressure: float = 150000.0  # Pa (1.5 bar minimum)
    
    # Injection control
    injection_duration: float = 2.0  # seconds
    injection_delay: float = 0.1  # seconds between floater injections
    injection_pressure_margin: float = 20000.0  # Pa above hydrostatic
    
    # Thermal control
    max_compressor_temp: float = 353.15  # K (80°C)
    thermal_shutdown_temp: float = 373.15  # K (100°C)
    cooling_threshold: float = 343.15  # K (70°C)
    
    # Performance optimization
    efficiency_target: float = 0.85
    power_optimization_enabled: bool = True
    thermal_optimization_enabled: bool = True
    
    # Fault detection
    sensor_timeout: float = 5.0  # seconds
    fault_detection_enabled: bool = True
    auto_recovery_enabled: bool = True


class PneumaticControlCoordinator:
    """
    Master control coordinator for the pneumatic system.
    
    Implements PLC-like control logic with sensor integration,
    fault detection, and performance optimization.
    """
    
    def __init__(self, 
                 control_params: Optional[ControlParameters] = None,
                 enable_thermodynamics: bool = True,
                 enable_optimization: bool = True):
        """
        Initialize the pneumatic control coordinator.
        
        Args:
            control_params: Control parameters, uses defaults if None
            enable_thermodynamics: Enable Phase 5 thermodynamic optimization
            enable_optimization: Enable performance optimization algorithms
        """
        self.control_params = control_params or ControlParameters()
        self.sensors = PneumaticSensors()
        self.system_state = SystemState.STARTUP
        self.active_faults = set()
        
        # Demo compatibility attributes
        self.control_frequency = 10.0  # 10 Hz control frequency
        self.subsystems = {}  # Dictionary of subsystems
        self.fault_conditions = []  # List of fault conditions
        self.optimization_enabled = enable_optimization
        
        # Phase 5 integration
        self.enable_thermodynamics = enable_thermodynamics
        if enable_thermodynamics:
            self.thermodynamics = AdvancedThermodynamics()
            self.heat_exchange = IntegratedHeatExchange()
        
        # Control state
        self.compressor_enabled = False
        self.injection_enabled = True
        self.last_injection_time = 0.0
        self.cycle_count = 0
        self.control_cycle_count = 0  # Track control cycles for demo compatibility
        
        # Performance tracking
        self.performance_metrics = {
            'system_efficiency': 0.0,
            'energy_consumption': 0.0,
            'thermal_boost_factor': 1.0,
            'fault_count': 0,
            'uptime_percentage': 100.0
        }
        
        # Control loop timing
        self.control_loop_dt = 0.1  # 100ms control loop
        self.last_update_time = time.time()
        
        # Threading for control loop
        self.control_thread = None
        self.running = False
        
        # Initialize subsystems for demo compatibility
        self._initialize_subsystems()
        
        logger.info(f"PneumaticControlCoordinator initialized: thermodynamics={enable_thermodynamics}, optimization={enable_optimization}")
    
    def _initialize_subsystems(self):
        """Initialize subsystem placeholders for demo compatibility."""
        # Create placeholder subsystem objects
        class SubsystemPlaceholder:
            def __init__(self, name):
                self.name = name
                self.is_active = False
                self.is_injecting = False
        
        self.subsystems = {
            'compressor': SubsystemPlaceholder('compressor'),
            'injection': SubsystemPlaceholder('injection'),
            'thermal': SubsystemPlaceholder('thermal'),
            'pressure': SubsystemPlaceholder('pressure')
        }
        
        # Initialize fault conditions
        self.fault_conditions = [
            'pressure_low', 'pressure_high', 'temperature_high',
            'sensor_timeout', 'compressor_fault', 'injection_fault'
        ]
    
    def start_control_loop(self):
        """Start the main control loop in a separate thread."""
        if self.running:
            logger.warning("Control loop already running")
            return
        
        self.running = True
        self.control_thread = threading.Thread(target=self._control_loop, daemon=True)
        self.control_thread.start()
        logger.info("Pneumatic control loop started")
    
    def stop_control_loop(self):
        """Stop the main control loop."""
        if not self.running:
            return
        
        self.running = False
        if self.control_thread:
            self.control_thread.join(timeout=1.0)
        logger.info("Pneumatic control loop stopped")
    
    def _control_loop(self):
        """Main control loop - runs continuously in separate thread."""
        while self.running:
            try:
                current_time = time.time()
                dt = current_time - self.last_update_time
                
                if dt >= self.control_loop_dt:
                    self.update_control_logic(dt)
                    self.last_update_time = current_time
                
                time.sleep(0.01)  # 10ms sleep to prevent excessive CPU usage
                
            except Exception as e:
                logger.error(f"Control loop error: {e}")
                self.add_fault(FaultType.COMMUNICATION_LOSS, f"Control loop exception: {e}")
    
    def update_control_logic(self, dt: float):
        """
        Main control logic update - called every control loop iteration.
        
        Args:
            dt: Time step since last update (seconds)
        """
        # 1. Update sensor readings
        self.update_sensors(dt)
        
        # 2. Fault detection and handling
        self.detect_faults()
        self.handle_faults()
        
        # 3. State machine update
        self.update_state_machine()
        
        # 4. Control algorithms based on current state
        if self.system_state == SystemState.NORMAL:
            self.pressure_control_algorithm()
            self.injection_control_algorithm()
            if self.enable_thermodynamics:
                self.thermal_control_algorithm()
        
        elif self.system_state == SystemState.OPTIMIZATION:
            self.performance_optimization_algorithm()
        
        elif self.system_state == SystemState.FAULT:
            self.fault_recovery_algorithm()
        
        elif self.system_state == SystemState.EMERGENCY_STOP:
            self.emergency_stop_procedure()
        
        # 5. Update performance metrics
        self.update_performance_metrics(dt)
    
    def update_sensors(self, dt: float):
        """Update sensor readings - simulate sensor data acquisition."""
        current_time = time.time()
        
        # In a real system, this would read from actual sensors
        # For simulation, we generate realistic sensor data
        
        # Pressure sensors (simulate some noise and drift)
        base_pressure = 250000.0 + 50000.0 * math.sin(current_time * 0.1)
        pressure_noise = 1000.0 * (0.5 - hash(str(current_time)) % 1000 / 1000.0)
        
        self.sensors.tank_pressure.value = base_pressure + pressure_noise
        self.sensors.tank_pressure.timestamp = current_time
        
        # Temperature sensors
        base_temp = 293.15 + 20.0 * (1.0 if self.compressor_enabled else 0.0)
        temp_noise = 2.0 * (0.5 - hash(str(current_time + 1)) % 1000 / 1000.0)
        
        self.sensors.compressor_temp.value = base_temp + temp_noise
        self.sensors.compressor_temp.timestamp = current_time
        
        # Water temperature varies with depth
        self.sensors.water_temp.value = 288.15 + 5.0 * math.sin(current_time * 0.05)
        self.sensors.water_temp.timestamp = current_time
        
        # Flow sensors
        flow_rate = 0.05 if self.compressor_enabled else 0.0
        self.sensors.compressor_flow.value = flow_rate
        self.sensors.compressor_flow.timestamp = current_time
    
    def detect_faults(self):
        """Detect system faults based on sensor readings and system state."""
        if not self.control_params.fault_detection_enabled:
            return
        
        current_time = time.time()
        
        # Pressure fault detection
        tank_pressure = self.sensors.tank_pressure.value
        if tank_pressure < self.control_params.min_pressure:
            self.add_fault(FaultType.PRESSURE_DROP, f"Tank pressure too low: {tank_pressure/100000:.2f} bar")
        elif tank_pressure > self.control_params.max_pressure:
            self.add_fault(FaultType.PRESSURE_DROP, f"Tank pressure too high: {tank_pressure/100000:.2f} bar")
        
        # Temperature fault detection
        compressor_temp = self.sensors.compressor_temp.value
        if compressor_temp > self.control_params.thermal_shutdown_temp:
            self.add_fault(FaultType.THERMAL_OVERLOAD, f"Compressor overheating: {compressor_temp-273.15:.1f}°C")
        
        # Sensor timeout detection
        for sensor_name in ['tank_pressure', 'compressor_temp', 'water_temp']:
            sensor = getattr(self.sensors, sensor_name)
            if current_time - sensor.timestamp > self.control_params.sensor_timeout:
                self.add_fault(FaultType.SENSOR_FAILURE, f"Sensor timeout: {sensor_name}")
    
    def add_fault(self, fault_type: FaultType, description: str):
        """Add a new fault to the active faults list."""
        if fault_type not in self.active_faults:
            self.active_faults.add(fault_type)
            self.performance_metrics['fault_count'] += 1
            logger.warning(f"Fault detected: {fault_type.value} - {description}")
    
    def clear_fault(self, fault_type: FaultType):
        """Clear a fault from the active faults list."""
        if fault_type in self.active_faults:
            self.active_faults.remove(fault_type)
            logger.info(f"Fault cleared: {fault_type.value}")
    
    def handle_faults(self):
        """Handle active faults based on severity and recovery procedures."""
        if not self.active_faults:
            return
          # Critical faults trigger emergency stop
        critical_faults = {FaultType.THERMAL_OVERLOAD, FaultType.COMPRESSOR_FAILURE}
        if any(fault in self.active_faults for fault in critical_faults):
            self.system_state = SystemState.EMERGENCY_STOP
            self.emergency_stop_procedure()  # Execute emergency stop immediately
            return
        
        # Non-critical faults trigger fault state
        if self.system_state == SystemState.NORMAL:
            self.system_state = SystemState.FAULT
    
    def update_state_machine(self):
        """Update the system state machine based on conditions and faults."""
        if self.system_state == SystemState.STARTUP:
            # Check if startup conditions are met
            if (self.sensors.tank_pressure.value > self.control_params.min_pressure and
                self.sensors.compressor_temp.value < self.control_params.max_compressor_temp and
                not self.active_faults):
                self.system_state = SystemState.NORMAL
                logger.info("System startup complete - entering normal operation")
        
        elif self.system_state == SystemState.FAULT:
            # Check if faults are cleared for auto-recovery
            if not self.active_faults and self.control_params.auto_recovery_enabled:
                self.system_state = SystemState.NORMAL
                logger.info("Faults cleared - returning to normal operation")
        
        elif self.system_state == SystemState.EMERGENCY_STOP:
            # Emergency stop can only be cleared manually
            pass
    
    def pressure_control_algorithm(self):
        """Pressure regulation control algorithm."""
        tank_pressure = self.sensors.tank_pressure.value
        target_pressure = self.control_params.target_pressure
        tolerance = self.control_params.pressure_tolerance
        
        # Hysteresis control to prevent oscillation
        if tank_pressure < (target_pressure - tolerance):
            if not self.compressor_enabled:
                self.compressor_enabled = True
                logger.info(f"Compressor ON: pressure {tank_pressure/100000:.2f} bar < target {target_pressure/100000:.2f} bar")
        
        elif tank_pressure > (target_pressure + tolerance):
            if self.compressor_enabled:
                self.compressor_enabled = False
                logger.info(f"Compressor OFF: pressure {tank_pressure/100000:.2f} bar > target {target_pressure/100000:.2f} bar")
    
    def injection_control_algorithm(self):
        """Injection timing and sequencing control."""
        if not self.injection_enabled:
            return
        
        current_time = time.time()
        
        # Check if enough time has passed since last injection
        if current_time - self.last_injection_time < self.control_params.injection_delay:
            return
        
        # Check if pressure is sufficient for injection
        tank_pressure = self.sensors.tank_pressure.value
        required_pressure = self.control_params.min_pressure + self.control_params.injection_pressure_margin
        
        if tank_pressure < required_pressure:
            logger.debug(f"Injection delayed: insufficient pressure {tank_pressure/100000:.2f} bar")
            return
        
        # Trigger injection (would interface with actual injection system)
        self.trigger_injection()
    
    def thermal_control_algorithm(self):
        """Thermal management control using Phase 5 thermodynamics."""
        if not self.enable_thermodynamics:
            return
        
        compressor_temp = self.sensors.compressor_temp.value
        water_temp = self.sensors.water_temp.value
        
        # Thermal optimization using Phase 5 data
        if compressor_temp > self.control_params.cooling_threshold:
            # Activate cooling measures
            logger.debug(f"Thermal management: compressor cooling activated at {compressor_temp-273.15:.1f}°C")
        
        # Calculate thermal efficiency boost
        if hasattr(self, 'thermodynamics'):
            # Use thermodynamic analysis for optimization
            thermal_efficiency = self.calculate_thermal_efficiency(compressor_temp, water_temp)
            self.performance_metrics['thermal_boost_factor'] = thermal_efficiency
    
    def performance_optimization_algorithm(self):
        """Performance optimization using thermal and pressure data."""
        if not self.control_params.power_optimization_enabled:
            return
        
        # Optimize based on current conditions
        tank_pressure = self.sensors.tank_pressure.value
        compressor_temp = self.sensors.compressor_temp.value
        water_temp = self.sensors.water_temp.value
        
        # Calculate optimal operating point
        optimal_pressure = self.calculate_optimal_pressure(compressor_temp, water_temp)
        
        # Adjust target pressure for optimization
        if abs(optimal_pressure - self.control_params.target_pressure) > 5000.0:  # 0.05 bar
            self.control_params.target_pressure = optimal_pressure
            logger.info(f"Pressure target optimized to {optimal_pressure/100000:.2f} bar")
    
    def fault_recovery_algorithm(self):
        """Fault recovery and system restoration procedures."""
        if not self.control_params.auto_recovery_enabled:
            return
        
        # Attempt to clear recoverable faults
        recoverable_faults = {FaultType.PRESSURE_DROP, FaultType.SENSOR_FAILURE}
        
        for fault_type in list(self.active_faults):
            if fault_type in recoverable_faults:
                # Implement specific recovery procedures
                if self.attempt_fault_recovery(fault_type):
                    self.clear_fault(fault_type)
    
    def emergency_stop_procedure(self):
        """Emergency stop procedure - immediate system shutdown."""
        self.compressor_enabled = False
        self.injection_enabled = False
        logger.critical("Emergency stop activated - all operations halted")
    
    def trigger_injection(self):
        """Trigger pneumatic injection for a floater."""
        current_time = time.time()
        self.last_injection_time = current_time
        self.cycle_count += 1
        
        # Calculate injection parameters using Phase 5 thermodynamics
        injection_params = self.calculate_injection_parameters()
        
        logger.info(f"Injection triggered: cycle {self.cycle_count}, pressure {self.sensors.tank_pressure.value/100000:.2f} bar")
        
        # In real system, this would control actual injection valves
        return injection_params
    
    def calculate_injection_parameters(self) -> Dict[str, float]:
        """Calculate optimal injection parameters using thermodynamic data."""
        tank_pressure = self.sensors.tank_pressure.value
        water_temp = self.sensors.water_temp.value
        
        # Base parameters
        injection_duration = self.control_params.injection_duration
        injection_pressure = tank_pressure
        
        # Phase 5 optimization
        if self.enable_thermodynamics:
            # Use thermodynamic analysis to optimize injection
            thermal_factor = self.calculate_thermal_efficiency(tank_pressure, water_temp)
            injection_duration *= thermal_factor
        
        return {
            'duration': injection_duration,
            'pressure': injection_pressure,
            'timestamp': time.time()
        }
    
    def calculate_thermal_efficiency(self, temperature: float, water_temp: float) -> float:
        """Calculate thermal efficiency factor using Phase 5 thermodynamics."""
        if not hasattr(self, 'thermodynamics'):
            return 1.0
        
        try:
            # Use Phase 5 thermodynamic calculations
            base_efficiency = 0.85
            temp_factor = 1.0 + (temperature - 293.15) / 1000.0  # Simple temperature factor
            water_factor = 1.0 + (water_temp - 288.15) / 500.0   # Water temperature factor
            
            return base_efficiency * temp_factor * water_factor
        
        except Exception as e:
            logger.warning(f"Thermal efficiency calculation failed: {e}")
            return 1.0
    
    def calculate_optimal_pressure(self, compressor_temp: float, water_temp: float) -> float:
        """Calculate optimal operating pressure based on thermal conditions."""
        base_pressure = self.control_params.target_pressure
        
        # Thermal optimization adjustments
        temp_adjustment = (compressor_temp - 293.15) * 1000.0  # Increase pressure for hot air
        water_adjustment = (water_temp - 288.15) * 500.0       # Adjust for water temperature
        
        optimal_pressure = base_pressure + temp_adjustment + water_adjustment
        
        # Constrain to safe operating range
        optimal_pressure = max(self.control_params.min_pressure, 
                             min(self.control_params.max_pressure, optimal_pressure))
        
        return optimal_pressure
    
    def attempt_fault_recovery(self, fault_type: FaultType) -> bool:
        """Attempt to recover from a specific fault type."""
        try:
            if fault_type == FaultType.PRESSURE_DROP:
                # Reset pressure control parameters
                self.control_params.target_pressure = 250000.0  # Reset to conservative value
                return True
            
            elif fault_type == FaultType.SENSOR_FAILURE:
                # Reset sensor readings and restart sensor monitoring
                self.update_sensors(0.1)
                return True
            
            return False
        
        except Exception as e:
            logger.error(f"Fault recovery failed for {fault_type.value}: {e}")
            return False
    
    def update_performance_metrics(self, dt: float):
        """Update system performance metrics."""
        # Calculate system efficiency
        if self.compressor_enabled and self.sensors.compressor_flow.value > 0:
            # Simplified efficiency calculation
            pressure_ratio = self.sensors.tank_pressure.value / 101325.0
            flow_efficiency = self.sensors.compressor_flow.value / 0.05  # Normalize to rated flow
            self.performance_metrics['system_efficiency'] = min(0.95, 0.85 * flow_efficiency / pressure_ratio)
        
        # Update uptime based on faults
        if self.active_faults:
            fault_penalty = len(self.active_faults) * 0.1
            self.performance_metrics['uptime_percentage'] = max(0.0, 100.0 - fault_penalty)
        else:
            self.performance_metrics['uptime_percentage'] = min(100.0, 
                self.performance_metrics['uptime_percentage'] + dt * 0.1)
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status for monitoring and UI."""
        return {
            'state': self.system_state.value,
            'sensors': {
                'tank_pressure': {
                    'value': self.sensors.tank_pressure.value / 100000.0,  # Convert to bar
                    'unit': 'bar',
                    'timestamp': self.sensors.tank_pressure.timestamp
                },
                'compressor_temp': {
                    'value': self.sensors.compressor_temp.value - 273.15,  # Convert to °C
                    'unit': '°C',
                    'timestamp': self.sensors.compressor_temp.timestamp
                },
                'water_temp': {
                    'value': self.sensors.water_temp.value - 273.15,  # Convert to °C
                    'unit': '°C',
                    'timestamp': self.sensors.water_temp.timestamp
                },
                'compressor_flow': {
                    'value': self.sensors.compressor_flow.value * 1000.0,  # Convert to L/s
                    'unit': 'L/s',
                    'timestamp': self.sensors.compressor_flow.timestamp
                }
            },
            'control': {
                'compressor_enabled': self.compressor_enabled,
                'injection_enabled': self.injection_enabled,
                'target_pressure': self.control_params.target_pressure / 100000.0,  # bar
                'cycle_count': self.cycle_count
            },
            'faults': [fault.value for fault in self.active_faults],
            'performance': self.performance_metrics.copy()
        }
    
    def set_control_parameters(self, new_params: Dict[str, Any]):
        """Update control parameters dynamically."""
        for param, value in new_params.items():
            if hasattr(self.control_params, param):
                setattr(self.control_params, param, value)
                logger.info(f"Control parameter updated: {param} = {value}")
    
    def emergency_stop(self):
        """Manually trigger emergency stop."""
        self.system_state = SystemState.EMERGENCY_STOP
        self.emergency_stop_procedure()
        logger.critical("Manual emergency stop triggered")
    
    def reset_system(self):
        """Reset system to startup state (clears emergency stop)."""
        self.active_faults.clear()
        self.system_state = SystemState.STARTUP
        self.compressor_enabled = False
        self.injection_enabled = True
        self.cycle_count = 0
        logger.info("System reset to startup state")
    
    # Demo compatibility methods
    def control_cycle(self, dt: float):
        """Run one control cycle - demo compatibility method."""
        self.update_control_logic(dt)
        self.control_cycle_count += 1
    
    def get_performance_metrics(self) -> Dict[str, float]:
        """Get current performance metrics - demo compatibility method."""
        return self.performance_metrics.copy()
    
    def update_sensor_data(self, sensor_name: str, value: float):
        """Update sensor data manually - demo compatibility method."""
        current_time = time.time()
        
        if sensor_name == 'tank_pressure':
            self.sensors.tank_pressure.value = value
            self.sensors.tank_pressure.timestamp = current_time
        elif sensor_name == 'tank_temperature':
            self.sensors.tank_temp.value = value + 273.15  # Convert C to K
            self.sensors.tank_temp.timestamp = current_time
        elif sensor_name == 'floater_depth':
            # Create or update floater position sensor
            sensor_reading = SensorReading(f"floater_depth", value, "m", current_time)
            if hasattr(self, '_floater_depth'):
                self._floater_depth = sensor_reading
            else:
                self._floater_depth = sensor_reading
        elif sensor_name == 'floater_velocity':
            # Create or update floater velocity sensor
            sensor_reading = SensorReading(f"floater_velocity", value, "m/s", current_time)
            if hasattr(self, '_floater_velocity'):
                self._floater_velocity = sensor_reading
            else:
                self._floater_velocity = sensor_reading
        elif sensor_name == 'ambient_temperature':
            self.sensors.compressor_temp.value = value + 273.15  # Convert C to K
            self.sensors.compressor_temp.timestamp = current_time
        elif sensor_name == 'water_temperature':
            self.sensors.water_temp.value = value + 273.15  # Convert C to K
            self.sensors.water_temp.timestamp = current_time
        
        # Validate sensor reading
        if value < 0 and sensor_name in ['tank_pressure', 'tank_temperature']:
            self.add_fault(FaultType.SENSOR_FAILURE, f"Invalid {sensor_name} reading: {value}")
    
    def set_operational_mode(self, mode: str):
        """Set operational mode - demo compatibility method."""
        if mode == 'injection':
            self.injection_enabled = True
            self.subsystems['injection'].is_active = True
            self.subsystems['injection'].is_injecting = True
            logger.info("Operational mode set to injection")
        elif mode == 'standby':
            self.injection_enabled = False
            self.compressor_enabled = False
            for subsystem in self.subsystems.values():
                subsystem.is_active = False
                subsystem.is_injecting = False
            logger.info("Operational mode set to standby")
        elif mode == 'normal':
            self.system_state = SystemState.NORMAL
            logger.info("Operational mode set to normal")


# Factory function for creating standard KPP pneumatic coordinator
def create_standard_kpp_pneumatic_coordinator(
    enable_thermodynamics: bool = True,
    enable_optimization: bool = True) -> PneumaticControlCoordinator:
    """
    Create a standard KPP pneumatic control coordinator with optimal settings.
    
    Args:
        enable_thermodynamics: Enable Phase 5 thermodynamic integration
        enable_optimization: Enable performance optimization algorithms
        
    Returns:
        Configured PneumaticControlCoordinator instance
    """
    # Standard KPP control parameters
    control_params = ControlParameters(
        target_pressure=250000.0,      # 2.5 bar target
        pressure_tolerance=15000.0,    # ±0.15 bar tolerance
        max_pressure=350000.0,         # 3.5 bar safety limit
        min_pressure=150000.0,         # 1.5 bar minimum
        injection_duration=2.0,        # 2 second injection
        injection_delay=0.5,           # 0.5 second between injections
        max_compressor_temp=353.15,    # 80°C max compressor temp
        efficiency_target=0.88,        # 88% target efficiency
        power_optimization_enabled=enable_optimization,
        thermal_optimization_enabled=enable_thermodynamics
    )
    
    coordinator = PneumaticControlCoordinator(
        control_params=control_params,
        enable_thermodynamics=enable_thermodynamics,
        enable_optimization=enable_optimization
    )
    
    logger.info("Created standard KPP pneumatic control coordinator")
    return coordinator
