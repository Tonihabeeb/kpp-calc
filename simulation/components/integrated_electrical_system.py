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
class ElectricalState:
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
        self.electrical_state = ElectricalState()
        self.system_state = ElectricalState.IDLE
        
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
        self.generator = None
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
        
        self.logger.info("Integrated electrical system initialized")
    
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
            
            # Transition to starting state
            self.system_state = ElectricalState.STARTING
            
            # Calculate electrical power output
            electrical_power = self._calculate_electrical_power(mechanical_power, speed)
            
            if electrical_power > 0:
                # Update system state
                self.electrical_state.power_output = electrical_power
                self.electrical_state.voltage = self.voltage_setpoint
                self.electrical_state.frequency = self.frequency_setpoint
                self.electrical_state.current = electrical_power / (self.electrical_state.voltage * math.sqrt(3))
                
                # Calculate efficiency
                self.electrical_state.efficiency = electrical_power / mechanical_power
                
                # Transition to generating state
                self.system_state = ElectricalState.GENERATING
                
                # Update performance metrics
                self.performance_metrics['total_energy_consumed'] += mechanical_power * 0.001  # kWh
                self.performance_metrics['total_energy_generated'] += electrical_power * 0.001  # kWh
                
                if electrical_power > self.performance_metrics['peak_power_output']:
                    self.performance_metrics['peak_power_output'] = electrical_power
                
                # Record operation
                self._record_operation('generation_start', {
                    'mechanical_power': mechanical_power,
                    'electrical_power': electrical_power,
                    'speed': speed,
                    'efficiency': self.electrical_state.efficiency
                })
                
                self.logger.info("Generation started: %.1f W output at %.1f RPM", electrical_power, speed)
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
    
    def _check_protection_systems(self) -> None:
        """Check all protection systems."""
        try:
            # Overcurrent protection
            if self.electrical_state.current > self.config.max_current:
                self._handle_fault("overcurrent", f"Current {self.electrical_state.current:.1f} A exceeds limit")
            
            # Overvoltage protection
            if self.electrical_state.voltage > self.config.rated_voltage * 1.1:
                self._handle_fault("overvoltage", f"Voltage {self.electrical_state.voltage:.1f} V exceeds limit")
            
            # Overtemperature protection
            if self.electrical_state.temperature > self.config.max_temperature:
                self._handle_fault("overtemperature", f"Temperature {self.electrical_state.temperature:.1f} K exceeds limit")
            
            # Frequency protection
            frequency_tolerance = 2.0  # Hz
            if abs(self.electrical_state.frequency - self.config.rated_frequency) > frequency_tolerance:
                self._handle_fault("frequency_deviation", f"Frequency {self.electrical_state.frequency:.1f} Hz out of range")
                
        except Exception as e:
            self.logger.error("Error checking protection systems: %s", e)
    
    def _handle_fault(self, fault_type: str, fault_message: str) -> None:
        """
        Handle electrical system faults.
        
        Args:
            fault_type: Type of fault
            fault_message: Fault message
        """
        try:
            self.logger.error("Electrical fault: %s - %s", fault_type, fault_message)
            
            # Update system state
            self.system_state = ElectricalState.FAULT
            self.electrical_state.grid_connection_state = GridConnectionState.FAULT
            
            # Update performance metrics
            self.performance_metrics['fault_count'] += 1
            
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
    
    def get_electrical_state(self) -> ElectricalState:
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
        self.electrical_state = ElectricalState()
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

    def update(self, dt: float) -> None:
        """
        Update electrical system state for a simulation timestep.
        
        Args:
            dt: Time step in seconds
        """
        try:
            # Update temperature based on power output
            if self.electrical_state.power_output > 0:
                # Simplified thermal model
                heat_generation = self.electrical_state.power_output * (1 - self.electrical_state.efficiency)
                thermal_resistance = 0.1  # K/W (simplified)
                temperature_rise = heat_generation * thermal_resistance * dt
                self.electrical_state.temperature += temperature_rise
            
            # Update grid connection time if connected
            if self.system_state == ElectricalState.GRID_CONNECTED:
                self.performance_metrics['grid_connection_time'] += dt
            
            # Check protection systems
            self._check_protection_systems()
            
        except Exception as e:
            self.logger.error("Error updating electrical system: %s", e)
            self._handle_fault("update_error", str(e))

