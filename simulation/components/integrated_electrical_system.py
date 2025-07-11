import math
import logging
import time
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass
from enum import Enum

"""
Integrated Electrical System for Phase 3 Implementation
Combines advanced generator, power electronics, and grid interface into unified system.
"""

import math
import logging
import time
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass
from enum import Enum

from .advanced_generator import AdvancedGenerator, GeneratorConfig, GeneratorState

class ElectricalState(str, Enum):
    """Electrical system state enumeration"""
    IDLE = "idle"
    STARTING = "starting"
    GENERATING = "generating"
    GRID_CONNECTED = "grid_connected"
    FAULT = "fault"
    MAINTENANCE = "maintenance"

class GridConnectionState(str, Enum):
    """Grid connection state enumeration"""
    DISCONNECTED = "disconnected"
    SYNCHRONIZING = "synchronizing"
    CONNECTED = "connected"
    FAULT = "fault"

@dataclass
class ElectricalStateData:
    """Electrical system state data structure"""
    voltage: float = 0.0  # V
    current: float = 0.0  # A
    frequency: float = 50.0  # Hz
    power_output: float = 0.0  # W
    reactive_power: float = 0.0  # VAR
    power_factor: float = 1.0
    efficiency: float = 0.0
    temperature: float = 293.15  # K
    grid_voltage: float = 0.0  # V
    grid_frequency: float = 50.0  # Hz
    grid_connection_state: GridConnectionState = GridConnectionState.DISCONNECTED

@dataclass
class ElectricalConfig:
    """Electrical system configuration"""
    rated_power: float = 50000.0  # W (50 kW)
    rated_voltage: float = 400.0  # V (3-phase)
    rated_frequency: float = 50.0  # Hz
    rated_speed: float = 1500.0  # RPM
    generator_efficiency: float = 0.95
    power_electronics_efficiency: float = 0.98
    grid_voltage: float = 400.0  # V
    grid_frequency: float = 50.0  # Hz
    max_current: float = 100.0  # A
    max_temperature: float = 353.15  # K (80°C)

class IntegratedElectricalSystem:
    """
    Complete electrical power generation system.
    Integrates generator, power electronics, and grid interface.
    """
    
    def __init__(self, config: Optional[ElectricalConfig] = None):
        """
        Initialize the integrated electrical system.
        
        Args:
            config: Electrical system configuration
        """
        self.config = config or ElectricalConfig()
        self.logger = logging.getLogger(__name__)
        
        # System state
        self.electrical_state = ElectricalStateData()
        self.system_state = ElectricalState.IDLE
        
        # Initialize generator
        generator_config = GeneratorConfig(
            rated_power=self.config.rated_power,
            rated_voltage=self.config.rated_voltage,
            rated_frequency=self.config.rated_frequency,
            rated_speed=self.config.rated_speed
        )
        self.generator = AdvancedGenerator(generator_config)
        
        # Performance tracking
        self.performance_metrics = {
            'total_energy_generated': 0.0,  # kWh
            'total_energy_consumed': 0.0,  # kWh
            'peak_power_output': 0.0,  # W
            'average_efficiency': 0.0,
            'grid_connection_time': 0.0,  # hours
            'fault_count': 0,
            'maintenance_count': 0
        }
        
        # Operation history
        self.operation_history: List[Dict[str, Any]] = []
        
        # Component interfaces (will be initialized by external systems)
        self.power_electronics = None
        self.grid_interface = None
        
        # Protection systems
        self.overcurrent_protection = True
        self.overvoltage_protection = True
        self.overtemperature_protection = True
        self.frequency_protection = True
        
        # Control parameters
        self.voltage_setpoint = self.config.rated_voltage
        self.frequency_setpoint = self.config.rated_frequency
        self.power_setpoint = 0.0
        
        self.logger.info("Integrated electrical system initialized with advanced generator")
    
    def start_generation(self, mechanical_power: float, speed: float) -> bool:
        """
        Start electrical power generation.
        
        Args:
            mechanical_power: Mechanical power input (W)
            speed: Rotational speed (RPM)
            
        Returns:
            True if generation started successfully
        """
        try:
            if self.system_state != ElectricalState.IDLE:
                self.logger.warning("Cannot start generation in state: %s", self.system_state)
                return False
            
            # Validate input parameters
            if mechanical_power <= 0 or speed <= 0:
                self.logger.error("Invalid mechanical power or speed")
                return False
            
            # Calculate mechanical torque
            mechanical_torque = (mechanical_power * 60) / (2 * math.pi * speed)
            
            # Start the generator
            if not self.generator.start_generator(mechanical_torque, speed):
                self.logger.error("Failed to start generator")
                return False
            
            # Transition to starting state
            self.system_state = ElectricalState.STARTING
            
            # Get generator state
            generator_state = self.generator.get_generator_state()
            
            if generator_state.power_output > 0:
                # Update system state
                self.electrical_state.power_output = generator_state.power_output
                self.electrical_state.voltage = generator_state.voltage
                self.electrical_state.frequency = generator_state.frequency
                self.electrical_state.current = generator_state.current
                self.electrical_state.efficiency = generator_state.efficiency
                
                # Transition to generating state
                self.system_state = ElectricalState.GENERATING
                
                # Update performance metrics
                self.performance_metrics['total_energy_consumed'] += mechanical_power * 0.001  # kWh
                self.performance_metrics['total_energy_generated'] += generator_state.power_output * 0.001  # kWh
                
                if generator_state.power_output > self.performance_metrics['peak_power_output']:
                    self.performance_metrics['peak_power_output'] = generator_state.power_output
                
                # Record operation
                self._record_operation('generation_start', {
                    'mechanical_power': mechanical_power,
                    'electrical_power': generator_state.power_output,
                    'speed': speed,
                    'efficiency': self.electrical_state.efficiency
                })
                
                self.logger.info("Generation started: %.1f W output at %.1f RPM", generator_state.power_output, speed)
                return True
            else:
                self.system_state = ElectricalState.IDLE
                self.logger.error("Failed to generate electrical power")
                return False
                
        except Exception as e:
            self.logger.error("Error starting generation: %s", e)
            self._handle_fault("generation_start_error", str(e))
            return False
    
    def stop_generation(self) -> bool:
        """
        Stop electrical power generation.
        
        Returns:
            True if generation stopped successfully
        """
        try:
            if self.system_state not in [ElectricalState.GENERATING, ElectricalState.GRID_CONNECTED]:
                self.logger.warning("Cannot stop generation in state: %s", self.system_state)
                return False
            
            # Disconnect from grid if connected
            if self.system_state == ElectricalState.GRID_CONNECTED:
                self._disconnect_from_grid()
            
            # Reset electrical state
            self.electrical_state.power_output = 0.0
            self.electrical_state.current = 0.0
            self.electrical_state.voltage = 0.0
            self.electrical_state.frequency = 0.0
            self.electrical_state.efficiency = 0.0
            
            # Transition to idle state
            self.system_state = ElectricalState.IDLE
            
            # Record operation
            self._record_operation('generation_stop', {
                'final_power': self.electrical_state.power_output,
                'total_energy_generated': self.performance_metrics['total_energy_generated']
            })
            
            self.logger.info("Generation stopped")
            return True
            
        except Exception as e:
            self.logger.error("Error stopping generation: %s", e)
            self._handle_fault("generation_stop_error", str(e))
            return False
    
    def connect_to_grid(self) -> bool:
        """
        Connect the electrical system to the grid.
        
        Returns:
            True if connection successful
        """
        try:
            if self.system_state != ElectricalState.GENERATING:
                self.logger.warning("Cannot connect to grid in state: %s", self.system_state)
                return False
            
            # Check grid synchronization
            if not self._check_grid_synchronization():
                self.logger.error("Grid synchronization failed")
                return False
            
            # Perform grid connection
            self.electrical_state.grid_connection_state = GridConnectionState.SYNCHRONIZING
            
            # Synchronize voltage and frequency
            self.electrical_state.voltage = self.config.grid_voltage
            self.electrical_state.frequency = self.config.grid_frequency
            self.electrical_state.grid_voltage = self.config.grid_voltage
            self.electrical_state.grid_frequency = self.config.grid_frequency
            
            # Complete connection
            self.electrical_state.grid_connection_state = GridConnectionState.CONNECTED
            self.system_state = ElectricalState.GRID_CONNECTED
            
            # Update performance metrics
            self.performance_metrics['grid_connection_time'] += 0.001  # hours
            
            # Record operation
            self._record_operation('grid_connection', {
                'grid_voltage': self.config.grid_voltage,
                'grid_frequency': self.config.grid_frequency,
                'power_output': self.electrical_state.power_output
            })
            
            self.logger.info("Connected to grid: %.1f V, %.1f Hz", self.config.grid_voltage, self.config.grid_frequency)
            return True
            
        except Exception as e:
            self.logger.error("Error connecting to grid: %s", e)
            self._handle_fault("grid_connection_error", str(e))
            return False
    
    def disconnect_from_grid(self) -> bool:
        """
        Disconnect the electrical system from the grid.
        
        Returns:
            True if disconnection successful
        """
        try:
            if self.system_state != ElectricalState.GRID_CONNECTED:
                self.logger.warning("Not connected to grid")
                return False
            
            # Perform disconnection
            success = self._disconnect_from_grid()
            
            if success:
                self.logger.info("Disconnected from grid")
            
            return success
            
        except Exception as e:
            self.logger.error("Error disconnecting from grid: %s", e)
            self._handle_fault("grid_disconnection_error", str(e))
            return False
    
    def update_power_output(self, mechanical_power: float, speed: float) -> bool:
        """
        Update power output based on mechanical input.
        
        Args:
            mechanical_power: Mechanical power input (W)
            speed: Rotational speed (RPM)
            
        Returns:
            True if update successful
        """
        try:
            if self.system_state not in [ElectricalState.GENERATING, ElectricalState.GRID_CONNECTED]:
                return False
            
            # Calculate new electrical power
            electrical_power = self._calculate_electrical_power(mechanical_power, speed)
            
            # Update electrical state
            self.electrical_state.power_output = electrical_power
            self.electrical_state.current = electrical_power / (self.electrical_state.voltage * math.sqrt(3))
            self.electrical_state.efficiency = electrical_power / mechanical_power if mechanical_power > 0 else 0.0
            
            # Update performance metrics
            self.performance_metrics['total_energy_consumed'] += mechanical_power * 0.001  # kWh
            self.performance_metrics['total_energy_generated'] += electrical_power * 0.001  # kWh
            
            if electrical_power > self.performance_metrics['peak_power_output']:
                self.performance_metrics['peak_power_output'] = electrical_power
            
            # Check protection systems
            self._check_protection_systems()
            
            return True
            
        except Exception as e:
            self.logger.error("Error updating power output: %s", e)
            self._handle_fault("power_update_error", str(e))
            return False
    
    def _calculate_electrical_power(self, mechanical_power: float, speed: float) -> float:
        """
        Calculate electrical power output from mechanical input.
        
        Args:
            mechanical_power: Mechanical power input (W)
            speed: Rotational speed (RPM)
            
        Returns:
            Electrical power output (W)
        """
        try:
            # Check if speed is sufficient for generation
            if speed < self.config.rated_speed * 0.5:  # 50% of rated speed
                return 0.0
            
            # Calculate generator efficiency based on speed
            speed_factor = min(speed / self.config.rated_speed, 1.0)
            generator_efficiency = self.config.generator_efficiency * speed_factor
            
            # Calculate power electronics efficiency
            power_electronics_efficiency = self.config.power_electronics_efficiency
            
            # Calculate total electrical power
            electrical_power = mechanical_power * generator_efficiency * power_electronics_efficiency
            
            # Limit to rated power
            electrical_power = min(electrical_power, self.config.rated_power)
            
            return electrical_power
            
        except Exception as e:
            self.logger.error("Error calculating electrical power: %s", e)
            return 0.0
    
    def _check_grid_synchronization(self) -> bool:
        """
        Check if the system can synchronize with the grid.
        
        Returns:
            True if synchronization is possible
        """
        try:
            # Check voltage synchronization (within 5%)
            voltage_tolerance = 0.05
            voltage_difference = abs(self.electrical_state.voltage - self.config.grid_voltage) / self.config.grid_voltage
            
            # Check frequency synchronization (within 0.1 Hz)
            frequency_tolerance = 0.1
            frequency_difference = abs(self.electrical_state.frequency - self.config.grid_frequency)
            
            return (voltage_difference <= voltage_tolerance and 
                   frequency_difference <= frequency_tolerance)
            
        except Exception as e:
            self.logger.error("Error checking grid synchronization: %s", e)
            return False
    
    def _disconnect_from_grid(self) -> bool:
        """
        Disconnect from the grid.
        
        Returns:
            True if disconnection successful
        """
        try:
            # Update grid connection state
            self.electrical_state.grid_connection_state = GridConnectionState.DISCONNECTED
            
            # Transition to generating state
            self.system_state = ElectricalState.GENERATING
            
            # Record operation
            self._record_operation('grid_disconnection', {
                'final_power': self.electrical_state.power_output
            })
            
            return True
            
        except Exception as e:
            self.logger.error("Error disconnecting from grid: %s", e)
            return False
    
    def _handle_fault(self, fault_type: str, fault_message: str) -> None:
        """
        Handle system fault.
        
        Args:
            fault_type: Type of fault
            fault_message: Fault description
        """
        try:
            self.logger.error("Fault detected: %s - %s", fault_type, fault_message)
            
            # Update system state
            self.system_state = ElectricalState.FAULT
            self.electrical_state.grid_connection_state = GridConnectionState.FAULT
            
            # Disconnect from grid if connected
            if self.is_grid_connected():
                self._disconnect_from_grid()
            
            # Stop generator
            self.generator.stop_generator()
            
            # Update performance metrics
            self.performance_metrics['fault_count'] += 1
            
            # Record fault
            self._record_operation('fault', {
                'type': fault_type,
                'message': fault_message,
                'time': time.time(),
                'state': {
                    'voltage': self.electrical_state.voltage,
                    'current': self.electrical_state.current,
                    'frequency': self.electrical_state.frequency,
                    'temperature': self.electrical_state.temperature
                }
            })
            
            # Attempt automatic recovery for certain fault types
            if fault_type in ['overcurrent', 'overvoltage', 'frequency_deviation']:
                self._attempt_fault_recovery(fault_type)
            
        except Exception as e:
            self.logger.error("Error handling fault: %s", e)
    
    def _attempt_fault_recovery(self, fault_type: str) -> None:
        """
        Attempt to recover from a system fault
        
        Args:
            fault_type: Type of fault that occurred
        """
        try:
            self.logger.info(f"Attempting recovery from fault: {fault_type}")
            
            # Store pre-fault parameters
            pre_fault_state = {
                'voltage': self.electrical_state.voltage,
                'current': self.electrical_state.current,
                'power_factor': self.electrical_state.power_factor,
                'efficiency': self.electrical_state.efficiency,
                'power_output': self.electrical_state.power_output,
                'reactive_power': self.electrical_state.reactive_power
            }
            
            # Reset system to safe state
            self.electrical_state.voltage = self.config.rated_voltage
            self.electrical_state.current = 0.0
            self.electrical_state.power_factor = 1.0
            self.electrical_state.reactive_power = 0.0
            self.electrical_state.power_output = 0.0
            
            # Gradual recovery steps with stability checks
            recovery_steps = [
                ('voltage', pre_fault_state['voltage'], 10),  # Restore voltage in 10 steps
                ('current', pre_fault_state['current'], 20),  # Restore current in 20 steps
                ('power_factor', pre_fault_state['power_factor'], 5),  # Restore PF in 5 steps
                ('reactive_power', pre_fault_state['reactive_power'], 5),  # Restore reactive power in 5 steps
                ('power_output', pre_fault_state['power_output'], 15)  # Restore power in 15 steps
            ]
            
            # Execute recovery steps
            for param, target, steps in recovery_steps:
                current_value = getattr(self.electrical_state, param)
                step_size = (target - current_value) / steps
                
                for i in range(steps):
                    # Gradually adjust parameter
                    new_value = current_value + step_size * (i + 1)
                    setattr(self.electrical_state, param, new_value)
                    
                    # Check system stability
                    if not self._check_system_stability():
                        self.logger.warning(f"Instability detected during {param} recovery")
                        self._handle_fault("recovery_instability", f"System unstable during {param} recovery")
                        return
                    
                    # Allow system to stabilize
                    time.sleep(0.1)
                    
                    # Update efficiency
                    self.electrical_state.efficiency = self._calculate_efficiency()
                    
                    # Check if efficiency is improving
                    if self.electrical_state.efficiency < 0.75 * pre_fault_state['efficiency']:
                        self.logger.warning(f"Low efficiency during {param} recovery")
                        # Adjust recovery parameters
                        step_size *= 0.8  # Reduce step size
                        time.sleep(0.2)  # Allow more stabilization time
            
            # Verify recovery success
            if self.electrical_state.efficiency >= 0.9 * pre_fault_state['efficiency']:
                self.logger.info("Fault recovery successful")
                self._clear_fault()
            else:
                self.logger.error("Failed to restore efficiency after fault recovery")
                self._handle_fault("recovery_failed", "Failed to restore system efficiency")
                
        except Exception as e:
            self.logger.error(f"Error during fault recovery: {e}")
            self._handle_fault("recovery_error", str(e))

    def _check_system_stability(self) -> bool:
        """
        Check system stability during recovery
        
        Returns:
            True if system is stable
        """
        try:
            # Check voltage stability
            if abs(self.electrical_state.voltage - self.config.rated_voltage) > 0.1 * self.config.rated_voltage:
                return False
                
            # Check current limits
            if self.electrical_state.current > self.config.max_current:
                return False
                
            # Check power factor
            if self.electrical_state.power_factor < 0.85:
                return False
                
            # Check frequency stability
            if abs(self.electrical_state.frequency - self.config.rated_frequency) > 0.02 * self.config.rated_frequency:
                return False
                
            # Check temperature
            if self.electrical_state.temperature > self.config.max_temperature:
                return False
                
            # Check efficiency trend
            if len(self.operation_history) >= 5:
                recent_efficiencies = [op['data'].get('efficiency', 0.0) 
                                     for op in self.operation_history[-5:]]
                if all(eff < 0.75 for eff in recent_efficiencies):
                    return False
            
            return True
            
        except Exception:
            return False

    def _calculate_efficiency(self) -> float:
        """
        Calculate current system efficiency
        
        Returns:
            Current efficiency as a ratio
        """
        try:
            if self.electrical_state.power_output > 0:
                # Calculate losses
                copper_losses = (self.electrical_state.current ** 2) * 0.1  # Approximate copper losses
                core_losses = (self.electrical_state.voltage ** 2) * 0.001  # Approximate core losses
                switching_losses = self.electrical_state.power_output * 0.02  # Approximate switching losses
                
                total_losses = copper_losses + core_losses + switching_losses
                total_power = self.electrical_state.power_output + total_losses
                
                return self.electrical_state.power_output / total_power if total_power > 0 else 0.0
            return 0.0
        except Exception:
            return 0.0
    
    def _clear_fault(self) -> None:
        """Clear fault state and restore normal operation"""
        try:
            self.logger.info("Clearing fault state")
            
            # Reset protection systems
            self.overcurrent_protection = True
            self.overvoltage_protection = True
            self.overtemperature_protection = True
            self.frequency_protection = True
            
            # Reset state
            self.system_state = ElectricalState.IDLE
            self.electrical_state.grid_connection_state = GridConnectionState.DISCONNECTED
            
            # Record recovery
            self._record_operation('fault_recovery', {
                'time': time.time(),
                'success': True
            })
            
            self.logger.info("Fault cleared, system ready for operation")
            
        except Exception as e:
            self.logger.error("Error clearing fault: %s", e)
    
    def inject_fault(self, fault_type: str) -> None:
        """
        Inject a fault into the electrical system for testing purposes.
        
        Args:
            fault_type: Type of fault to inject
        """
        try:
            self.logger.info("Injecting fault: %s", fault_type)
            
            if fault_type == "overcurrent":
                self.electrical_state.current = self.config.max_current * 1.1  # 10% over limit
                self._check_protection_systems()
                
            elif fault_type == "overvoltage":
                self.electrical_state.voltage = self.config.rated_voltage * 1.2  # 20% over
                self._check_protection_systems()
                
            elif fault_type == "overtemperature":
                self.electrical_state.temperature = self.config.max_temperature + 20  # 20K over
                self._check_protection_systems()
                
            elif fault_type == "frequency_deviation":
                self.electrical_state.frequency = self.config.rated_frequency * 1.1  # 10% over
                self._check_protection_systems()
                
            elif fault_type == "test_fault":
                # Simulate a recoverable fault
                self.electrical_state.current = self.config.max_current * 1.1
                self.electrical_state.temperature = self.config.max_temperature + 20
                self._check_protection_systems()
                # Start recovery immediately
                self._attempt_fault_recovery('overcurrent')
            
        except Exception as e:
            self.logger.error("Error injecting fault: %s", e)
    
    def _check_protection_systems(self) -> None:
        """Check all protection systems and respond to any violations"""
        try:
            fault_detected = False
            fault_type = "unknown"  # Default fault type
            
            # Check overcurrent protection
            if self.overcurrent_protection and self.electrical_state.current > self.config.max_current:
                fault_detected = True
                fault_type = "overcurrent"
                self.logger.warning("Overcurrent protection triggered: %.1f A", self.electrical_state.current)
            
            # Check overvoltage protection
            if self.overvoltage_protection and self.electrical_state.voltage > self.config.rated_voltage * 1.1:
                fault_detected = True
                fault_type = "overvoltage"
                self.logger.warning("Overvoltage protection triggered: %.1f V", self.electrical_state.voltage)
            
            # Check overtemperature protection
            if self.overtemperature_protection and self.electrical_state.temperature > self.config.max_temperature:
                fault_detected = True
                fault_type = "overtemperature"
                self.logger.warning("Overtemperature protection triggered: %.1f K", self.electrical_state.temperature)
            
            # Check frequency protection
            if self.frequency_protection and abs(self.electrical_state.frequency - self.config.rated_frequency) > 2.0:
                fault_detected = True
                fault_type = "frequency_deviation"
                self.logger.warning("Frequency protection triggered: %.1f Hz", self.electrical_state.frequency)
            
            # Handle any detected faults
            if fault_detected:
                self._handle_fault(fault_type, f"Protection system triggered: {fault_type}")
            
        except Exception as e:
            self.logger.error("Error checking protection systems: %s", e)
            self._handle_fault("protection_system_error", str(e))
    
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
                'system_state': {
                    'electrical_state': self.system_state.value,
                    'grid_connection': self.electrical_state.grid_connection_state.value,
                    'power_output': self.electrical_state.power_output,
                    'voltage': self.electrical_state.voltage,
                    'frequency': self.electrical_state.frequency,
                    'efficiency': self.electrical_state.efficiency
                }
            }
            
            self.operation_history.append(operation_record)
            
        except Exception as e:
            self.logger.error("Error recording operation: %s", e)
    
    def get_electrical_state(self) -> ElectricalStateData:
        """
        Get current electrical state.
        
        Returns:
            Current electrical state
        """
        return self.electrical_state
    
    def get_system_state(self) -> ElectricalState:
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
        # Calculate average efficiency
        if self.performance_metrics['total_energy_consumed'] > 0:
            self.performance_metrics['average_efficiency'] = (
                self.performance_metrics['total_energy_generated'] / 
                self.performance_metrics['total_energy_consumed']
            )
        
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
    
    def is_generating(self) -> bool:
        """
        Check if system is generating power.
        
        Returns:
            True if generating
        """
        return self.system_state in [ElectricalState.GENERATING, ElectricalState.GRID_CONNECTED]
    
    def is_grid_connected(self) -> bool:
        """
        Check if system is connected to grid.
        
        Returns:
            True if grid connected
        """
        return self.system_state == ElectricalState.GRID_CONNECTED
    
    def reset(self) -> None:
        """Reset electrical system to initial state."""
        self.electrical_state = ElectricalStateData()
        self.system_state = ElectricalState.IDLE
        self.operation_history.clear()
        self.performance_metrics = {
            'total_energy_generated': 0.0,
            'total_energy_consumed': 0.0,
            'peak_power_output': 0.0,
            'average_efficiency': 0.0,
            'grid_connection_time': 0.0,
            'fault_count': 0,
            'maintenance_count': 0
        }
        self.logger.info("Electrical system reset")

    def update(self, current_state: Dict[str, Any], time_step: float) -> Dict[str, Any]:
        """
        Update electrical system state.
        
        Args:
            current_state: Current system state including all relevant parameters
            time_step: Time step duration in seconds
            
        Returns:
            Dictionary containing updated electrical state
        """
        try:
            # Extract current values
            mechanical_power = current_state.get('mechanical_power', 0.0)
            speed = current_state.get('speed', 0.0)
            
            # Update generator
            if self.generator:
                # Use the correct method name for AdvancedGenerator
                if hasattr(self.generator, 'update_generator_state'):
                    success = self.generator.update_generator_state(mechanical_power, speed)
                    if success:
                        generator_state = self.generator.get_generator_state()
                        self.electrical_state.power_output = generator_state.power_output
                        self.electrical_state.voltage = generator_state.voltage
                        self.electrical_state.frequency = generator_state.frequency
                        self.electrical_state.current = generator_state.current
                        self.electrical_state.efficiency = generator_state.efficiency
                else:
                    # Fallback for other generator types that might have update method
                    try:
                        # Use getattr to avoid linter errors
                        update_method = getattr(self.generator, 'update', None)
                        if update_method:
                            generator_state = update_method(mechanical_power, speed, time_step)
                            if generator_state:
                                self.electrical_state.power_output = generator_state.power_output
                                self.electrical_state.voltage = generator_state.voltage
                                self.electrical_state.frequency = generator_state.frequency
                                self.electrical_state.current = generator_state.current
                                self.electrical_state.efficiency = generator_state.efficiency
                    except Exception:
                        # Generator doesn't have update method or update failed, skip update
                        pass
            
            # Check protection systems
            self._check_protection_systems()
            
            # Update grid connection if connected
            if self.electrical_state.grid_connection_state == GridConnectionState.CONNECTED:
                self._check_grid_synchronization()
            
            # Calculate total efficiency
            total_efficiency = (self.electrical_state.power_output / mechanical_power 
                              if mechanical_power > 0 else 0.0)
            
            # Return current state
            return {
                'power_output': self.electrical_state.power_output,
                'voltage': self.electrical_state.voltage,
                'frequency': self.electrical_state.frequency,
                'current': self.electrical_state.current,
                'efficiency': total_efficiency,
                'grid_connection_state': self.electrical_state.grid_connection_state.value,
                'system_state': self.system_state.value
            }
            
        except Exception as e:
            self.logger.error(f"Error in electrical system update: {e}")
            self._handle_fault("update_error", str(e))
            return {
                'power_output': 0.0,
                'voltage': 0.0,
                'frequency': 0.0,
                'current': 0.0,
                'efficiency': 0.0,
                'grid_connection_state': GridConnectionState.FAULT.value,
                'system_state': ElectricalState.FAULT.value
            }

