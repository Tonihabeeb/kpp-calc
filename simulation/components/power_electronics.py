import math
import logging
import time
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

"""
Power Electronics and Grid Interface System for Phase 3 Implementation
Models inverters, transformers, grid synchronization, and power conditioning.
"""

class PowerElectronicsSystemState(str, Enum):
    """Power electronics system state enumeration"""
    IDLE = "idle"
    STARTING = "starting"
    OPERATING = "operating"
    FAULT = "fault"
    MAINTENANCE = "maintenance"

class ConversionType(str, Enum):
    """Power conversion type enumeration"""
    AC_TO_DC = "ac_to_dc"  # Rectifier
    DC_TO_AC = "dc_to_ac"  # Inverter
    DC_TO_DC = "dc_to_dc"  # DC/DC converter
    AC_TO_AC = "ac_to_ac"  # AC/AC converter

@dataclass
class PowerElectronicsState:
    """Power electronics state data structure"""
    input_voltage: float = 0.0  # V
    input_current: float = 0.0  # A
    input_power: float = 0.0  # W
    output_voltage: float = 0.0  # V
    output_current: float = 0.0  # A
    output_power: float = 0.0  # W
    efficiency: float = 0.0
    temperature: float = 293.15  # K
    switching_frequency: float = 0.0  # Hz
    power_factor: float = 1.0
    total_harmonic_distortion: float = 0.0  # %

@dataclass
class PowerElectronicsConfig:
    """Power electronics configuration"""
    rated_power: float = 50000.0  # W (50 kW)
    input_voltage: float = 400.0  # V (3-phase)
    output_voltage: float = 400.0  # V (3-phase)
    switching_frequency: float = 10000.0  # Hz (10 kHz)
    efficiency_nominal: float = 0.98
    power_factor_nominal: float = 0.99
    max_temperature: float = 353.15  # K (80°C)
    cooling_system: bool = True
    protection_enabled: bool = True
    grid_synchronization: bool = True

class PowerElectronics:
    """
    Power electronics system with comprehensive conversion and control.
    Handles AC/DC, DC/AC, DC/DC, and AC/AC conversions with protection.
    """
    
    def __init__(self, config: Optional[PowerElectronicsConfig] = None):
        """
        Initialize the power electronics system.
        
        Args:
            config: Power electronics configuration
        """
        self.config = config or PowerElectronicsConfig()
        self.logger = logging.getLogger(__name__)
        
        # System state
        self.power_state = PowerElectronicsState()
        self.system_state = PowerElectronicsSystemState.IDLE
        
        # Performance tracking
        self.performance_metrics = {
            'total_energy_processed': 0.0,  # kWh
            'total_energy_losses': 0.0,  # kWh
            'peak_power_processed': 0.0,  # W
            'average_efficiency': 0.0,
            'switching_losses': 0.0,  # kWh
            'conduction_losses': 0.0,  # kWh
            'thermal_losses': 0.0,  # kWh
            'operating_hours': 0.0,  # hours
            'fault_count': 0
        }
        
        # Operation history
        self.operation_history: List[Dict[str, Any]] = []
        
        # Control parameters
        self.voltage_setpoint = self.config.output_voltage
        self.frequency_setpoint = 50.0  # Hz
        self.power_setpoint = 0.0
        
        # Protection systems
        self.overcurrent_protection = True
        self.overvoltage_protection = True
        self.overtemperature_protection = True
        self.overload_protection = True
        
        # Conversion efficiency models
        self.switching_loss_coefficient = 0.001  # W/Hz
        self.conduction_loss_coefficient = 0.02  # W/A²
        self.thermal_loss_coefficient = 0.005  # W/K
        
        self.logger.info("Power electronics system initialized: %.1f kW", 
                        self.config.rated_power / 1000)
    
    def start_conversion(self, input_voltage: float, input_current: float, 
                        conversion_type: ConversionType) -> bool:
        """
        Start power conversion.
        
        Args:
            input_voltage: Input voltage (V)
            input_current: Input current (A)
            conversion_type: Type of conversion
            
        Returns:
            True if conversion started successfully
        """
        try:
            if self.system_state != PowerElectronicsSystemState.IDLE:
                self.logger.warning("Cannot start conversion in state: %s", self.system_state)
                return False
            
            # Validate input parameters
            if input_voltage <= 0 or input_current <= 0:
                self.logger.error("Invalid input voltage or current")
                return False
            
            # Transition to starting state
            self.system_state = PowerElectronicsSystemState.STARTING
            
            # Calculate input power
            input_power = input_voltage * input_current * math.sqrt(3)  # 3-phase
            
            # Calculate output power and parameters
            output_power = self._calculate_output_power(input_power, conversion_type)
            
            if output_power > 0:
                # Update power state
                self.power_state.input_voltage = input_voltage
                self.power_state.input_current = input_current
                self.power_state.input_power = input_power
                self.power_state.output_power = output_power
                self.power_state.efficiency = output_power / input_power
                self.power_state.switching_frequency = self.config.switching_frequency
                
                # Calculate output parameters based on conversion type
                self._calculate_output_parameters(conversion_type)
                
                # Transition to operating state
                self.system_state = PowerElectronicsSystemState.OPERATING
                
                # Update performance metrics
                self._update_performance_metrics(input_power, output_power)
                
                # Record operation
                self._record_operation('conversion_start', {
                    'input_voltage': input_voltage,
                    'input_current': input_current,
                    'input_power': input_power,
                    'output_power': output_power,
                    'conversion_type': conversion_type.value,
                    'efficiency': self.power_state.efficiency
                })
                
                self.logger.info("Power conversion started: %.1f W output (%.1f%% efficiency)", 
                               output_power, self.power_state.efficiency * 100)
                return True
            else:
                self.system_state = PowerElectronicsSystemState.IDLE
                self.logger.error("Failed to start power conversion")
                return False
                
        except Exception as e:
            self.logger.error("Error starting conversion: %s", e)
            self._handle_fault("conversion_start_error", str(e))
            return False
    
    def stop_conversion(self) -> bool:
        """
        Stop power conversion.
        
        Returns:
            True if conversion stopped successfully
        """
        try:
            if self.system_state != PowerElectronicsSystemState.OPERATING:
                self.logger.warning("Cannot stop conversion in state: %s", self.system_state)
                return False
            
            # Reset power state
            self.power_state.input_voltage = 0.0
            self.power_state.input_current = 0.0
            self.power_state.input_power = 0.0
            self.power_state.output_voltage = 0.0
            self.power_state.output_current = 0.0
            self.power_state.output_power = 0.0
            self.power_state.efficiency = 0.0
            self.power_state.switching_frequency = 0.0
            
            # Transition to idle state
            self.system_state = PowerElectronicsSystemState.IDLE
            
            # Record operation
            self._record_operation('conversion_stop', {
                'final_power': self.power_state.output_power,
                'total_energy_processed': self.performance_metrics['total_energy_processed']
            })
            
            self.logger.info("Power conversion stopped")
            return True
            
        except Exception as e:
            self.logger.error("Error stopping conversion: %s", e)
            self._handle_fault("conversion_stop_error", str(e))
            return False
    
    def update_conversion_state(self, input_voltage: float, input_current: float,
                               conversion_type: ConversionType) -> bool:
        """
        Update conversion state based on input parameters.
        
        Args:
            input_voltage: Input voltage (V)
            input_current: Input current (A)
            conversion_type: Type of conversion
            
        Returns:
            True if update successful
        """
        try:
            if self.system_state != PowerElectronicsSystemState.OPERATING:
                return False
            
            # Calculate new input power
            input_power = input_voltage * input_current * math.sqrt(3)  # 3-phase
            
            # Calculate new output power
            output_power = self._calculate_output_power(input_power, conversion_type)
            
            # Update power state
            self.power_state.input_voltage = input_voltage
            self.power_state.input_current = input_current
            self.power_state.input_power = input_power
            self.power_state.output_power = output_power
            self.power_state.efficiency = output_power / input_power if input_power > 0 else 0.0
            
            # Calculate output parameters
            self._calculate_output_parameters(conversion_type)
            
            # Update performance metrics
            self._update_performance_metrics(input_power, output_power)
            
            # Check protection systems
            self._check_protection_systems()
            
            return True
            
        except Exception as e:
            self.logger.error("Error updating conversion state: %s", e)
            self._handle_fault("state_update_error", str(e))
            return False
    
    def _calculate_output_power(self, input_power: float, conversion_type: ConversionType) -> float:
        """
        Calculate output power from input power.
        
        Args:
            input_power: Input power (W)
            conversion_type: Type of conversion
            
        Returns:
            Output power (W)
        """
        try:
            # Calculate losses based on conversion type
            switching_losses = self._calculate_switching_losses()
            conduction_losses = self._calculate_conduction_losses()
            thermal_losses = self._calculate_thermal_losses()
            
            total_losses = switching_losses + conduction_losses + thermal_losses
            
            # Calculate output power
            output_power = input_power - total_losses
            
            # Ensure non-negative output
            output_power = max(0.0, output_power)
            
            # Limit to rated power
            output_power = min(output_power, self.config.rated_power)
            
            return output_power
            
        except Exception as e:
            self.logger.error("Error calculating output power: %s", e)
            return 0.0
    
    def _calculate_output_parameters(self, conversion_type: ConversionType) -> None:
        """
        Calculate output voltage and current based on conversion type.
        
        Args:
            conversion_type: Type of conversion
        """
        try:
            if conversion_type == ConversionType.AC_TO_DC:
                # Rectifier: AC to DC
                self.power_state.output_voltage = self.power_state.input_voltage * 1.414  # Peak voltage
                self.power_state.output_current = self.power_state.output_power / self.power_state.output_voltage
                
            elif conversion_type == ConversionType.DC_TO_AC:
                # Inverter: DC to AC
                self.power_state.output_voltage = self.config.output_voltage
                self.power_state.output_current = self.power_state.output_power / (self.power_state.output_voltage * math.sqrt(3))
                
            elif conversion_type == ConversionType.DC_TO_DC:
                # DC/DC converter
                self.power_state.output_voltage = self.config.output_voltage
                self.power_state.output_current = self.power_state.output_power / self.power_state.output_voltage
                
            elif conversion_type == ConversionType.AC_TO_AC:
                # AC/AC converter
                self.power_state.output_voltage = self.config.output_voltage
                self.power_state.output_current = self.power_state.output_power / (self.power_state.output_voltage * math.sqrt(3))
            
            # Calculate power factor and THD
            self.power_state.power_factor = self._calculate_power_factor()
            self.power_state.total_harmonic_distortion = self._calculate_thd()
            
        except Exception as e:
            self.logger.error("Error calculating output parameters: %s", e)
    
    def _calculate_switching_losses(self) -> float:
        """
        Calculate switching losses.
        
        Returns:
            Switching losses (W)
        """
        try:
            # Switching losses: P_sw = k_sw × f_sw × V × I
            switching_losses = (self.switching_loss_coefficient * 
                              self.power_state.switching_frequency * 
                              self.power_state.input_voltage * 
                              self.power_state.input_current)
            
            return switching_losses
            
        except Exception as e:
            self.logger.error("Error calculating switching losses: %s", e)
            return 0.0
    
    def _calculate_conduction_losses(self) -> float:
        """
        Calculate conduction losses.
        
        Returns:
            Conduction losses (W)
        """
        try:
            # Conduction losses: P_cond = k_cond × I²
            conduction_losses = self.conduction_loss_coefficient * (self.power_state.input_current ** 2)
            
            return conduction_losses
            
        except Exception as e:
            self.logger.error("Error calculating conduction losses: %s", e)
            return 0.0
    
    def _calculate_thermal_losses(self) -> float:
        """
        Calculate thermal losses.
        
        Returns:
            Thermal losses (W)
        """
        try:
            # Thermal losses: P_thermal = k_thermal × ΔT
            delta_temperature = self.power_state.temperature - 293.15  # K
            thermal_losses = self.thermal_loss_coefficient * delta_temperature
            
            return thermal_losses
            
        except Exception as e:
            self.logger.error("Error calculating thermal losses: %s", e)
            return 0.0
    
    def _calculate_power_factor(self) -> float:
        """
        Calculate power factor.
        
        Returns:
            Power factor (0.0 to 1.0)
        """
        try:
            # Simplified power factor calculation
            # In practice, this would be more complex based on load characteristics
            base_power_factor = self.config.power_factor_nominal
            
            # Adjust based on load level
            load_factor = self.power_state.input_power / self.config.rated_power
            power_factor = base_power_factor * (0.95 + 0.05 * load_factor)
            
            return min(1.0, max(0.8, power_factor))
            
        except Exception as e:
            self.logger.error("Error calculating power factor: %s", e)
            return 1.0
    
    def _calculate_thd(self) -> float:
        """
        Calculate total harmonic distortion.
        
        Returns:
            THD percentage
        """
        try:
            # Simplified THD calculation
            # In practice, this would be based on actual harmonic analysis
            base_thd = 2.0  # % at nominal load
            
            # Adjust based on load level
            load_factor = self.power_state.input_power / self.config.rated_power
            thd = base_thd * (1.0 + 0.5 * (1.0 - load_factor))
            
            return min(10.0, max(0.1, thd))
            
        except Exception as e:
            self.logger.error("Error calculating THD: %s", e)
            return 2.0
    
    def _update_performance_metrics(self, input_power: float, output_power: float) -> None:
        """
        Update performance metrics.
        
        Args:
            input_power: Input power (W)
            output_power: Output power (W)
        """
        try:
            # Update energy tracking
            self.performance_metrics['total_energy_processed'] += input_power * 0.001  # kWh
            self.performance_metrics['total_energy_losses'] += (input_power - output_power) * 0.001  # kWh
            
            # Update peak power
            if input_power > self.performance_metrics['peak_power_processed']:
                self.performance_metrics['peak_power_processed'] = input_power
            
            # Update losses
            switching_losses = self._calculate_switching_losses()
            conduction_losses = self._calculate_conduction_losses()
            thermal_losses = self._calculate_thermal_losses()
            
            self.performance_metrics['switching_losses'] += switching_losses * 0.001  # kWh
            self.performance_metrics['conduction_losses'] += conduction_losses * 0.001  # kWh
            self.performance_metrics['thermal_losses'] += thermal_losses * 0.001  # kWh
            
            # Update operating hours
            self.performance_metrics['operating_hours'] += 0.001  # hours
            
            # Calculate average efficiency
            if self.performance_metrics['total_energy_processed'] > 0:
                self.performance_metrics['average_efficiency'] = (
                    (self.performance_metrics['total_energy_processed'] - 
                     self.performance_metrics['total_energy_losses']) / 
                    self.performance_metrics['total_energy_processed']
                )
            
        except Exception as e:
            self.logger.error("Error updating performance metrics: %s", e)
    
    def _check_protection_systems(self) -> None:
        """Check all protection systems."""
        try:
            # Overcurrent protection
            max_current = self.config.rated_power / (self.config.input_voltage * math.sqrt(3)) * 1.2
            if self.power_state.input_current > max_current:
                self._handle_fault("overcurrent", f"Current {self.power_state.input_current:.1f} A exceeds limit")
            
            # Overvoltage protection
            if self.power_state.input_voltage > self.config.input_voltage * 1.1:
                self._handle_fault("overvoltage", f"Voltage {self.power_state.input_voltage:.1f} V exceeds limit")
            
            # Overtemperature protection
            if self.power_state.temperature > self.config.max_temperature:
                self._handle_fault("overtemperature", f"Temperature {self.power_state.temperature:.1f} K exceeds limit")
            
            # Overload protection
            if self.power_state.input_power > self.config.rated_power * 1.1:
                self._handle_fault("overload", f"Power {self.power_state.input_power:.1f} W exceeds limit")
                
        except Exception as e:
            self.logger.error("Error checking protection systems: %s", e)
    
    def _handle_fault(self, fault_type: str, fault_message: str) -> None:
        """
        Handle power electronics faults.
        
        Args:
            fault_type: Type of fault
            fault_message: Fault message
        """
        try:
            self.logger.error("Power electronics fault: %s - %s", fault_type, fault_message)
            
            # Update system state
            self.system_state = PowerElectronicsSystemState.FAULT
            
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
                'power_state': {
                    'system_state': self.system_state.value,
                    'input_power': self.power_state.input_power,
                    'output_power': self.power_state.output_power,
                    'efficiency': self.power_state.efficiency,
                    'temperature': self.power_state.temperature,
                    'power_factor': self.power_state.power_factor,
                    'thd': self.power_state.total_harmonic_distortion
                }
            }
            
            self.operation_history.append(operation_record)
            
        except Exception as e:
            self.logger.error("Error recording operation: %s", e)
    
    def get_power_state(self) -> PowerElectronicsState:
        """
        Get current power electronics state.
        
        Returns:
            Current power state
        """
        return self.power_state
    
    def get_system_state(self) -> PowerElectronicsSystemState:
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
    
    def is_operating(self) -> bool:
        """
        Check if power electronics is operating.
        
        Returns:
            True if operating
        """
        return self.system_state == PowerElectronicsSystemState.OPERATING
    
    def get_efficiency(self) -> float:
        """
        Get current conversion efficiency.
        
        Returns:
            Current efficiency (0.0 to 1.0)
        """
        return self.power_state.efficiency
    
    def reset(self) -> None:
        """Reset power electronics to initial state."""
        self.power_state = PowerElectronicsState()
        self.system_state = PowerElectronicsSystemState.IDLE
        self.operation_history.clear()
        self.performance_metrics = {
            'total_energy_processed': 0.0,
            'total_energy_losses': 0.0,
            'peak_power_processed': 0.0,
            'average_efficiency': 0.0,
            'switching_losses': 0.0,
            'conduction_losses': 0.0,
            'thermal_losses': 0.0,
            'operating_hours': 0.0,
            'fault_count': 0
        }
        self.logger.info("Power electronics system reset")

