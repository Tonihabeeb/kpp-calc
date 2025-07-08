import math
import logging
import time
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

"""
Advanced Generator Model for Phase 3 Implementation
Enhanced electromagnetic modeling with realistic generator characteristics.
"""

class GeneratorType(str, Enum):
    """Generator type enumeration"""
    SYNCHRONOUS = "synchronous"
    INDUCTION = "induction"
    PERMANENT_MAGNET = "permanent_magnet"
    WOUND_ROTOR = "wound_rotor"

class GeneratorSystemState(str, Enum):
    """Generator system state enumeration"""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    OVERLOADED = "overloaded"
    FAULT = "fault"
    MAINTENANCE = "maintenance"

@dataclass
class GeneratorState:
    """Generator state data structure"""
    speed: float = 0.0  # RPM
    torque: float = 0.0  # N·m
    power_output: float = 0.0  # W
    voltage: float = 0.0  # V
    current: float = 0.0  # A
    frequency: float = 0.0  # Hz
    efficiency: float = 0.0
    temperature: float = 293.15  # K
    field_current: float = 0.0  # A (for synchronous generators)
    power_factor: float = 1.0
    reactive_power: float = 0.0  # VAR

@dataclass
class GeneratorConfig:
    """Generator configuration"""
    generator_type: GeneratorType = GeneratorType.SYNCHRONOUS
    rated_power: float = 50000.0  # W (50 kW)
    rated_voltage: float = 400.0  # V (3-phase)
    rated_frequency: float = 50.0  # Hz
    rated_speed: float = 1500.0  # RPM
    rated_torque: float = 318.3  # N·m
    number_of_poles: int = 4
    stator_resistance: float = 0.1  # Ω
    rotor_resistance: float = 0.05  # Ω (for induction)
    stator_reactance: float = 0.5  # Ω
    rotor_reactance: float = 0.3  # Ω (for induction)
    magnetizing_reactance: float = 10.0  # Ω
    moment_of_inertia: float = 2.0  # kg·m²
    copper_loss_coefficient: float = 0.02  # W/K
    iron_loss_coefficient: float = 0.01  # W/K
    mechanical_loss_coefficient: float = 0.005  # W/K

class AdvancedGenerator:
    """
    Advanced generator with comprehensive electromagnetic modeling.
    Handles different generator types, efficiency modeling, and control systems.
    """
    
    def __init__(self, config: Optional[GeneratorConfig] = None):
        """
        Initialize the advanced generator.
        
        Args:
            config: Generator configuration
        """
        self.config = config or GeneratorConfig()
        self.logger = logging.getLogger(__name__)
        
        # Generator state
        self.generator_state = GeneratorState()
        self.system_state = GeneratorSystemState.STOPPED
        
        # Performance tracking
        self.performance_metrics = {
            'total_energy_generated': 0.0,  # kWh
            'total_energy_consumed': 0.0,  # kWh
            'peak_power_output': 0.0,  # W
            'average_efficiency': 0.0,
            'copper_losses': 0.0,  # kWh
            'iron_losses': 0.0,  # kWh
            'mechanical_losses': 0.0,  # kWh
            'operating_hours': 0.0,  # hours
            'fault_count': 0
        }
        
        # Operation history
        self.operation_history: List[Dict[str, Any]] = []
        
        # Control parameters
        self.voltage_setpoint = self.config.rated_voltage
        self.frequency_setpoint = self.config.rated_frequency
        self.power_setpoint = 0.0
        
        # Protection systems
        self.overcurrent_protection = True
        self.overvoltage_protection = True
        self.overtemperature_protection = True
        self.overspeed_protection = True
        
        # Physics constants
        self.pi = math.pi
        self.mu_0 = 4 * self.pi * 1e-7  # H/m (permeability of free space)
        
        self.logger.info("Advanced generator initialized: %s, %.1f kW", 
                        self.config.generator_type.value, self.config.rated_power / 1000)
    
    def start_generator(self, mechanical_torque: float, speed: float) -> bool:
        """
        Start the generator.
        
        Args:
            mechanical_torque: Mechanical input torque (N·m)
            speed: Rotational speed (RPM)
            
        Returns:
            True if generator started successfully
        """
        try:
            if self.system_state != GeneratorSystemState.STOPPED:
                self.logger.warning("Cannot start generator in state: %s", self.system_state)
                return False
            
            # Validate input parameters
            if mechanical_torque <= 0 or speed <= 0:
                self.logger.error("Invalid mechanical torque or speed")
                return False
            
            # Transition to starting state
            self.system_state = GeneratorSystemState.STARTING
            
            # Calculate electrical output
            electrical_power = self._calculate_electrical_power(mechanical_torque, speed)
            
            if electrical_power > 0:
                # Update generator state
                self.generator_state.speed = speed
                self.generator_state.torque = mechanical_torque
                self.generator_state.power_output = electrical_power
                self.generator_state.frequency = self._calculate_frequency(speed)
                self.generator_state.voltage = self._calculate_voltage(speed, electrical_power)
                self.generator_state.current = electrical_power / (self.generator_state.voltage * math.sqrt(3))
                self.generator_state.efficiency = electrical_power / (mechanical_torque * speed * 2 * self.pi / 60)
                
                # Transition to running state
                self.system_state = GeneratorSystemState.RUNNING
                
                # Update performance metrics
                self._update_performance_metrics(mechanical_torque, speed, electrical_power)
                
                # Record operation
                self._record_operation('generator_start', {
                    'mechanical_torque': mechanical_torque,
                    'speed': speed,
                    'electrical_power': electrical_power,
                    'efficiency': self.generator_state.efficiency
                })
                
                self.logger.info("Generator started: %.1f W output at %.1f RPM", electrical_power, speed)
                return True
            else:
                self.system_state = GeneratorSystemState.STOPPED
                self.logger.error("Failed to generate electrical power")
                return False
                
        except Exception as e:
            self.logger.error("Error starting generator: %s", e)
            self._handle_fault("generator_start_error", str(e))
            return False
    
    def stop_generator(self) -> bool:
        """
        Stop the generator.
        
        Returns:
            True if generator stopped successfully
        """
        try:
            if self.system_state not in [GeneratorSystemState.RUNNING, GeneratorSystemState.OVERLOADED]:
                self.logger.warning("Cannot stop generator in state: %s", self.system_state)
                return False
            
            # Reset generator state
            self.generator_state.speed = 0.0
            self.generator_state.torque = 0.0
            self.generator_state.power_output = 0.0
            self.generator_state.voltage = 0.0
            self.generator_state.current = 0.0
            self.generator_state.frequency = 0.0
            self.generator_state.efficiency = 0.0
            
            # Transition to stopped state
            self.system_state = GeneratorSystemState.STOPPED
            
            # Record operation
            self._record_operation('generator_stop', {
                'final_power': self.generator_state.power_output,
                'total_energy_generated': self.performance_metrics['total_energy_generated']
            })
            
            self.logger.info("Generator stopped")
            return True
            
        except Exception as e:
            self.logger.error("Error stopping generator: %s", e)
            self._handle_fault("generator_stop_error", str(e))
            return False
    
    def update_generator_state(self, mechanical_torque: float, speed: float) -> bool:
        """
        Update generator state based on mechanical input.
        
        Args:
            mechanical_torque: Mechanical input torque (N·m)
            speed: Rotational speed (RPM)
            
        Returns:
            True if update successful
        """
        try:
            if self.system_state not in [GeneratorSystemState.RUNNING, GeneratorSystemState.OVERLOADED]:
                return False
            
            # Calculate new electrical output
            electrical_power = self._calculate_electrical_power(mechanical_torque, speed)
            
            # Update generator state
            self.generator_state.speed = speed
            self.generator_state.torque = mechanical_torque
            self.generator_state.power_output = electrical_power
            self.generator_state.frequency = self._calculate_frequency(speed)
            self.generator_state.voltage = self._calculate_voltage(speed, electrical_power)
            self.generator_state.current = electrical_power / (self.generator_state.voltage * math.sqrt(3))
            self.generator_state.efficiency = electrical_power / (mechanical_torque * speed * 2 * self.pi / 60)
            
            # Update performance metrics
            self._update_performance_metrics(mechanical_torque, speed, electrical_power)
            
            # Check protection systems
            self._check_protection_systems()
            
            return True
            
        except Exception as e:
            self.logger.error("Error updating generator state: %s", e)
            self._handle_fault("state_update_error", str(e))
            return False
    
    def _calculate_electrical_power(self, mechanical_torque: float, speed: float) -> float:
        """
        Calculate electrical power output from mechanical input.
        
        Args:
            mechanical_torque: Mechanical input torque (N·m)
            speed: Rotational speed (RPM)
            
        Returns:
            Electrical power output (W)
        """
        try:
            # Calculate mechanical power
            mechanical_power = mechanical_torque * speed * 2 * self.pi / 60  # W
            
            # Calculate losses
            copper_losses = self._calculate_copper_losses(speed)
            iron_losses = self._calculate_iron_losses(speed)
            mechanical_losses = self._calculate_mechanical_losses(speed)
            
            # Calculate electrical power
            electrical_power = mechanical_power - copper_losses - iron_losses - mechanical_losses
            
            # Ensure non-negative output
            electrical_power = max(0.0, electrical_power)
            
            # Limit to rated power
            electrical_power = min(electrical_power, self.config.rated_power)
            
            return electrical_power
            
        except Exception as e:
            self.logger.error("Error calculating electrical power: %s", e)
            return 0.0
    
    def _calculate_frequency(self, speed: float) -> float:
        """
        Calculate electrical frequency from mechanical speed.
        
        Args:
            speed: Rotational speed (RPM)
            
        Returns:
            Electrical frequency (Hz)
        """
        try:
            # f = (P × n) / 120
            # where P is number of poles and n is speed in RPM
            frequency = (self.config.number_of_poles * speed) / 120
            return frequency
            
        except Exception as e:
            self.logger.error("Error calculating frequency: %s", e)
            return 0.0
    
    def _calculate_voltage(self, speed: float, power: float) -> float:
        """
        Calculate generator voltage.
        
        Args:
            speed: Rotational speed (RPM)
            power: Electrical power (W)
            
        Returns:
            Generator voltage (V)
        """
        try:
            # Simplified voltage calculation
            # V = V_rated × (n/n_rated) × (P/P_rated)^0.5
            speed_factor = speed / self.config.rated_speed
            power_factor = math.sqrt(power / self.config.rated_power) if self.config.rated_power > 0 else 0.0
            
            voltage = self.config.rated_voltage * speed_factor * power_factor
            
            # Ensure reasonable bounds
            voltage = max(0.0, min(voltage, self.config.rated_voltage * 1.1))
            
            return voltage
            
        except Exception as e:
            self.logger.error("Error calculating voltage: %s", e)
            return 0.0
    
    def _calculate_copper_losses(self, speed: float) -> float:
        """
        Calculate copper losses.
        
        Args:
            speed: Rotational speed (RPM)
            
        Returns:
            Copper losses (W)
        """
        try:
            # Copper losses: P_cu = I² × R
            # Simplified calculation based on speed
            speed_factor = speed / self.config.rated_speed
            current_factor = speed_factor  # Assume current proportional to speed
            
            copper_losses = (current_factor ** 2) * self.config.stator_resistance * 3  # 3-phase
            
            return copper_losses
            
        except Exception as e:
            self.logger.error("Error calculating copper losses: %s", e)
            return 0.0
    
    def _calculate_iron_losses(self, speed: float) -> float:
        """
        Calculate iron losses.
        
        Args:
            speed: Rotational speed (RPM)
            
        Returns:
            Iron losses (W)
        """
        try:
            # Iron losses: P_fe = k_fe × f² × B²
            # Simplified calculation based on speed
            frequency = self._calculate_frequency(speed)
            speed_factor = speed / self.config.rated_speed
            
            iron_losses = self.config.iron_loss_coefficient * (frequency ** 2) * (speed_factor ** 2)
            
            return iron_losses
            
        except Exception as e:
            self.logger.error("Error calculating iron losses: %s", e)
            return 0.0
    
    def _calculate_mechanical_losses(self, speed: float) -> float:
        """
        Calculate mechanical losses.
        
        Args:
            speed: Rotational speed (RPM)
            
        Returns:
            Mechanical losses (W)
        """
        try:
            # Mechanical losses: P_mech = k_mech × ω³
            # Simplified calculation based on speed
            speed_factor = speed / self.config.rated_speed
            
            mechanical_losses = self.config.mechanical_loss_coefficient * (speed_factor ** 3)
            
            return mechanical_losses
            
        except Exception as e:
            self.logger.error("Error calculating mechanical losses: %s", e)
            return 0.0
    
    def _update_performance_metrics(self, mechanical_torque: float, speed: float, electrical_power: float) -> None:
        """
        Update performance metrics.
        
        Args:
            mechanical_torque: Mechanical input torque (N·m)
            speed: Rotational speed (RPM)
            electrical_power: Electrical power output (W)
        """
        try:
            # Calculate mechanical power
            mechanical_power = mechanical_torque * speed * 2 * self.pi / 60
            
            # Update energy tracking
            self.performance_metrics['total_energy_consumed'] += mechanical_power * 0.001  # kWh
            self.performance_metrics['total_energy_generated'] += electrical_power * 0.001  # kWh
            
            # Update peak power
            if electrical_power > self.performance_metrics['peak_power_output']:
                self.performance_metrics['peak_power_output'] = electrical_power
            
            # Update losses
            copper_losses = self._calculate_copper_losses(speed)
            iron_losses = self._calculate_iron_losses(speed)
            mechanical_losses = self._calculate_mechanical_losses(speed)
            
            self.performance_metrics['copper_losses'] += copper_losses * 0.001  # kWh
            self.performance_metrics['iron_losses'] += iron_losses * 0.001  # kWh
            self.performance_metrics['mechanical_losses'] += mechanical_losses * 0.001  # kWh
            
            # Update operating hours
            self.performance_metrics['operating_hours'] += 0.001  # hours
            
            # Calculate average efficiency
            if self.performance_metrics['total_energy_consumed'] > 0:
                self.performance_metrics['average_efficiency'] = (
                    self.performance_metrics['total_energy_generated'] / 
                    self.performance_metrics['total_energy_consumed']
                )
            
        except Exception as e:
            self.logger.error("Error updating performance metrics: %s", e)
    
    def _check_protection_systems(self) -> None:
        """Check all protection systems."""
        try:
            # Overcurrent protection
            if self.generator_state.current > self.config.rated_power / (self.config.rated_voltage * math.sqrt(3)) * 1.2:
                self._handle_fault("overcurrent", f"Current {self.generator_state.current:.1f} A exceeds limit")
            
            # Overvoltage protection
            if self.generator_state.voltage > self.config.rated_voltage * 1.1:
                self._handle_fault("overvoltage", f"Voltage {self.generator_state.voltage:.1f} V exceeds limit")
            
            # Overtemperature protection
            if self.generator_state.temperature > 353.15:  # 80°C
                self._handle_fault("overtemperature", f"Temperature {self.generator_state.temperature:.1f} K exceeds limit")
            
            # Overspeed protection
            if self.generator_state.speed > self.config.rated_speed * 1.2:
                self._handle_fault("overspeed", f"Speed {self.generator_state.speed:.1f} RPM exceeds limit")
                
        except Exception as e:
            self.logger.error("Error checking protection systems: %s", e)
    
    def _handle_fault(self, fault_type: str, fault_message: str) -> None:
        """
        Handle generator faults.
        
        Args:
            fault_type: Type of fault
            fault_message: Fault message
        """
        try:
            self.logger.error("Generator fault: %s - %s", fault_type, fault_message)
            
            # Update system state
            self.system_state = GeneratorSystemState.FAULT
            
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
                'generator_state': {
                    'system_state': self.system_state.value,
                    'speed': self.generator_state.speed,
                    'torque': self.generator_state.torque,
                    'power_output': self.generator_state.power_output,
                    'voltage': self.generator_state.voltage,
                    'frequency': self.generator_state.frequency,
                    'efficiency': self.generator_state.efficiency
                }
            }
            
            self.operation_history.append(operation_record)
            
        except Exception as e:
            self.logger.error("Error recording operation: %s", e)
    
    def get_generator_state(self) -> GeneratorState:
        """
        Get current generator state.
        
        Returns:
            Current generator state
        """
        return self.generator_state
    
    def get_system_state(self) -> GeneratorSystemState:
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
    
    def is_running(self) -> bool:
        """
        Check if generator is running.
        
        Returns:
            True if running
        """
        return self.system_state in [GeneratorSystemState.RUNNING, GeneratorSystemState.OVERLOADED]
    
    def get_efficiency(self) -> float:
        """
        Get current generator efficiency.
        
        Returns:
            Current efficiency (0.0 to 1.0)
        """
        return self.generator_state.efficiency
    
    def reset(self) -> None:
        """Reset generator to initial state."""
        self.generator_state = GeneratorState()
        self.system_state = GeneratorSystemState.STOPPED
        self.operation_history.clear()
        self.performance_metrics = {
            'total_energy_generated': 0.0,
            'total_energy_consumed': 0.0,
            'peak_power_output': 0.0,
            'average_efficiency': 0.0,
            'copper_losses': 0.0,
            'iron_losses': 0.0,
            'mechanical_losses': 0.0,
            'operating_hours': 0.0,
            'fault_count': 0
        }
        self.logger.info("Generator reset")

def create_kmp_generator(config: Optional[GeneratorConfig] = None) -> AdvancedGenerator:
    """
    Factory function to create a KMP generator.
    
    Args:
        config: Generator configuration
        
    Returns:
        AdvancedGenerator instance
    """
    if config is None:
        config = GeneratorConfig()
        config.generator_type = GeneratorType.SYNCHRONOUS
        config.rated_power = 50000.0  # 50 kW
        config.rated_voltage = 400.0  # 400 V
        config.rated_frequency = 50.0  # 50 Hz
        config.rated_speed = 1500.0  # 1500 RPM
    
    return AdvancedGenerator(config)

