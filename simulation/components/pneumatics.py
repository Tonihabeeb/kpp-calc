import logging
import math
import time
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from enum import Enum

"""
Pneumatic System module.
Handles air injection, venting, and compressor logic for the KPP simulator.
Includes Phase 5 advanced thermodynamic modeling and thermal boost capabilities.
"""

class CompressorState(str, Enum):
    """Compressor state enumeration"""
    IDLE = "idle"
    RUNNING = "running"
    OVERLOADED = "overloaded"
    MAINTENANCE = "maintenance"
    ERROR = "error"

@dataclass
class PneumaticState:
    """Pneumatic system state data structure"""
    current_pressure: float = 101325.0  # Pa
    total_volume: float = 0.0  # m³
    temperature: float = 293.15  # K
    compressor_state: CompressorState = CompressorState.IDLE
    compressor_efficiency: float = 0.85
    power_consumption: float = 0.0  # W
    total_work: float = 0.0  # J
    heat_generated: float = 0.0  # J

@dataclass
class PneumaticConfig:
    """Pneumatic system configuration"""
    max_pressure: float = 500000.0  # Pa
    min_pressure: float = 100000.0  # Pa
    compressor_power: float = 5000.0  # W
    compressor_efficiency: float = 0.85
    heat_exchange_coefficient: float = 25.0  # W/m²·K
    surface_area: float = 1.0  # m²
    ambient_temperature: float = 293.15  # K
    isothermal_efficiency: float = 0.9
    adiabatic_efficiency: float = 0.8

class PneumaticSystem:
    """
    Comprehensive pneumatic system for the KPP simulator.
    Handles air injection, venting, compressor operations, and thermodynamic modeling.
    """
    
    def __init__(self, config: Optional[PneumaticConfig] = None):
        """
        Initialize the pneumatic system.
        
        Args:
            config: Configuration for the pneumatic system
        """
        self.config = config or PneumaticConfig()
        self.logger = logging.getLogger(__name__)
        
        # System state
        self.pneumatic_state = PneumaticState()
        self.pneumatic_state.compressor_efficiency = self.config.compressor_efficiency
        
        # Performance tracking
        self.performance_metrics = {
            'total_injections': 0,
            'total_venting': 0,
            'total_energy_consumed': 0.0,
            'total_work_done': 0.0,
            'average_efficiency': 0.0,
            'peak_pressure': 0.0,
            'total_heat_generated': 0.0
        }
        
        # Operation history
        self.operation_history: List[Dict[str, Any]] = []
        
        # Error tracking
        self.error_count = 0
        self.last_error = None
        
        self.logger.info("Pneumatic system initialized")
    
    def inject_air(self, pressure: float, volume: float) -> bool:
        """
        Inject air into the system.
        
        Args:
            pressure: Injection pressure in Pa
            volume: Volume of air to inject in m³
            
        Returns:
            True if injection was successful
        """
        try:
            # Validate injection parameters
            if pressure < self.config.min_pressure or pressure > self.config.max_pressure:
                self.logger.error("Invalid injection pressure: %.0f Pa", pressure)
                return False
            
            if volume <= 0:
                self.logger.error("Invalid injection volume: %.3f m³", volume)
                return False
            
            # Calculate compression work
            work = self._calculate_compression_work(pressure, volume)
            
            # Check compressor capacity
            if not self._check_compressor_capacity(work):
                self.logger.warning("Compressor capacity exceeded")
                return False
            
            # Update system state
            self.pneumatic_state.current_pressure = pressure
            self.pneumatic_state.total_volume += volume
            self.pneumatic_state.total_work += work
            
            # Calculate power consumption
            injection_time = self._estimate_injection_time(volume, pressure)
            power_consumption = work / injection_time if injection_time > 0 else 0.0
            self.pneumatic_state.power_consumption = power_consumption
            
            # Calculate heat generation
            heat_generated = self._calculate_heat_generation(work)
            self.pneumatic_state.heat_generated += heat_generated
            
            # Update compressor state
            self._update_compressor_state(power_consumption)
            
            # Update performance metrics
            self.performance_metrics['total_injections'] += 1
            self.performance_metrics['total_energy_consumed'] += work
            self.performance_metrics['total_work_done'] += work
            self.performance_metrics['total_heat_generated'] += heat_generated
            
            if pressure > self.performance_metrics['peak_pressure']:
                self.performance_metrics['peak_pressure'] = pressure
            
            # Record operation
            self._record_operation('injection', {
                'pressure': pressure,
                'volume': volume,
                'work': work,
                'power_consumption': power_consumption,
                'heat_generated': heat_generated
            })
            
            self.logger.info("Air injection successful: %.3f m³ at %.0f Pa (work: %.1f J)", 
                           volume, pressure, work)
            return True
            
        except (ValueError, TypeError) as e:
            self.logger.error("Invalid parameter during air injection: %s", e)
            self._handle_error("injection_parameter_error", str(e))
            return False
        except RuntimeError as e:
            self.logger.error("Runtime error during air injection: %s", e)
            self._handle_error("injection_runtime_error", str(e))
            return False
        except Exception as e:
            self.logger.error("Unexpected error during air injection: %s", e)
            self._handle_error("injection_error", str(e))
            return False
    
    def vent_air(self, pressure: float, volume: float) -> bool:
        """
        Vent air from the system.
        
        Args:
            pressure: Venting pressure in Pa
            volume: Volume of air to vent in m³
            
        Returns:
            True if venting was successful
        """
        try:
            # Validate venting parameters
            if pressure < self.config.min_pressure or pressure > self.config.max_pressure:
                self.logger.error("Invalid venting pressure: %.0f Pa", pressure)
                return False
            
            if volume <= 0 or volume > self.pneumatic_state.total_volume:
                self.logger.error("Invalid venting volume: %.3f m³", volume)
                return False
            
            # Calculate expansion work (negative for venting)
            work = self._calculate_expansion_work(pressure, volume)
            
            # Update system state
            self.pneumatic_state.current_pressure = pressure
            self.pneumatic_state.total_volume -= volume
            self.pneumatic_state.total_work += work  # Work is negative for venting
            
            # Calculate heat exchange during venting
            heat_exchange = self._calculate_venting_heat_exchange(volume, pressure)
            self.pneumatic_state.heat_generated += heat_exchange
            
            # Update compressor state (idle during venting)
            self.pneumatic_state.compressor_state = CompressorState.IDLE
            self.pneumatic_state.power_consumption = 0.0
            
            # Update performance metrics
            self.performance_metrics['total_venting'] += 1
            self.performance_metrics['total_energy_consumed'] += abs(work)
            
            # Record operation
            self._record_operation('venting', {
                'pressure': pressure,
                'volume': volume,
                'work': work,
                'heat_exchange': heat_exchange
            })
            
            self.logger.info("Air venting successful: %.3f m³ at %.0f Pa (work: %.1f J)", 
                           volume, pressure, work)
            return True
            
        except (ValueError, TypeError) as e:
            self.logger.error("Invalid parameter during air venting: %s", e)
            self._handle_error("venting_parameter_error", str(e))
            return False
        except RuntimeError as e:
            self.logger.error("Runtime error during air venting: %s", e)
            self._handle_error("venting_runtime_error", str(e))
            return False
        except Exception as e:
            self.logger.error("Unexpected error during air venting: %s", e)
            self._handle_error("venting_error", str(e))
            return False
    
    def _calculate_compression_work(self, final_pressure: float, volume: float) -> float:
        """
        Calculate compression work using isothermal compression.
        
        Args:
            final_pressure: Final pressure (Pa)
            volume: Volume to compress (m³)
            
        Returns:
            Compression work (J)
        """
        try:
            initial_pressure = 101325.0  # Atmospheric pressure
            
            # Isothermal compression work: W = P₁V₁ × ln(P₂/P₁)
            if final_pressure > initial_pressure:
                work = initial_pressure * volume * math.log(final_pressure / initial_pressure)
            else:
                work = 0.0
            
            # Apply isothermal efficiency
            work = work / self.config.isothermal_efficiency
            
            return work
            
        except Exception as e:
            self.logger.error("Error calculating compression work: %s", e)
            return 0.0
    
    def _calculate_expansion_work(self, pressure: float, volume: float) -> float:
        """
        Calculate expansion work during venting.
        
        Args:
            pressure: Venting pressure (Pa)
            volume: Volume being vented (m³)
            
        Returns:
            Expansion work (J, negative)
        """
        try:
            # Expansion work (negative): W = -P × V
            work = -pressure * volume
            
            return work
            
        except Exception as e:
            self.logger.error("Error calculating expansion work: %s", e)
            return 0.0
    
    def _calculate_heat_generation(self, work: float) -> float:
        """
        Calculate heat generation during compression.
        
        Args:
            work: Compression work (J)
            
        Returns:
            Heat generated (J)
        """
        try:
            # Heat generation based on compressor efficiency
            # Q = W × (1 - η) / η
            if self.pneumatic_state.compressor_efficiency > 0:
                heat_generated = work * (1 - self.pneumatic_state.compressor_efficiency) / self.pneumatic_state.compressor_efficiency
            else:
                heat_generated = 0.0
            
            return heat_generated
            
        except Exception as e:
            self.logger.error("Error calculating heat generation: %s", e)
            return 0.0
    
    def _calculate_venting_heat_exchange(self, volume: float, pressure: float) -> float:
        """
        Calculate heat exchange during venting.
        
        Args:
            volume: Venting volume (m³)
            pressure: Venting pressure (Pa)
            
        Returns:
            Heat exchange (J)
        """
        try:
            # Simplified heat exchange calculation
            # Q = h × A × ΔT × t
            # For venting, assume cooling effect
            temperature_difference = 50.0  # K (assumed cooling)
            venting_time = volume / 0.1  # s (assumed flow rate)
            
            heat_exchange = (self.config.heat_exchange_coefficient * 
                           self.config.surface_area * 
                           temperature_difference * 
                           venting_time)
            
            return -heat_exchange  # Negative for cooling
            
        except Exception as e:
            self.logger.error("Error calculating venting heat exchange: %s", e)
            return 0.0
    
    def _check_compressor_capacity(self, work: float) -> bool:
        """
        Check if compressor can handle the work.
        
        Args:
            work: Required work (J)
            
        Returns:
            True if compressor can handle the work
        """
        try:
            # Calculate required power
            estimated_time = 1.0  # s (assumed injection time)
            required_power = work / estimated_time
            
            # Check against compressor capacity
            max_power = self.config.compressor_power
            
            return required_power <= max_power
            
        except Exception as e:
            self.logger.error("Error checking compressor capacity: %s", e)
            return False
    
    def _estimate_injection_time(self, volume: float, pressure: float) -> float:
        """
        Estimate injection time based on volume and pressure.
        
        Args:
            volume: Volume to inject (m³)
            pressure: Injection pressure (Pa)
            
        Returns:
            Estimated injection time (s)
        """
        try:
            # Simplified time estimation
            # Higher pressure and volume require more time
            base_time = 0.5  # s
            pressure_factor = pressure / 101325.0
            volume_factor = volume / 0.1  # m³
            
            injection_time = base_time * pressure_factor * volume_factor
            
            return max(0.1, min(10.0, injection_time))  # Bounded between 0.1 and 10 seconds
            
        except Exception as e:
            self.logger.error("Error estimating injection time: %s", e)
            return 1.0
    
    def _update_compressor_state(self, power_consumption: float) -> None:
        """
        Update compressor state based on power consumption.
        
        Args:
            power_consumption: Current power consumption (W)
        """
        try:
            max_power = self.config.compressor_power
            
            if power_consumption == 0:
                self.pneumatic_state.compressor_state = CompressorState.IDLE
            elif power_consumption <= max_power * 0.8:
                self.pneumatic_state.compressor_state = CompressorState.RUNNING
            elif power_consumption <= max_power:
                self.pneumatic_state.compressor_state = CompressorState.OVERLOADED
            else:
                self.pneumatic_state.compressor_state = CompressorState.ERROR
                
        except Exception as e:
            self.logger.error("Error updating compressor state: %s", e)
            self.pneumatic_state.compressor_state = CompressorState.ERROR
    
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
                    'pressure': self.pneumatic_state.current_pressure,
                    'volume': self.pneumatic_state.total_volume,
                    'temperature': self.pneumatic_state.temperature,
                    'compressor_state': self.pneumatic_state.compressor_state.value
                }
            }
            
            self.operation_history.append(operation_record)
            
        except Exception as e:
            self.logger.error("Error recording operation: %s", e)
    
    def _handle_error(self, error_type: str, error_message: str) -> None:
        """
        Handle errors and update error tracking.
        
        Args:
            error_type: Type of error
            error_message: Error message
        """
        self.error_count += 1
        self.last_error = f"{error_type}: {error_message}"
        self.pneumatic_state.compressor_state = CompressorState.ERROR
        
        self.logger.error("Pneumatic system error: %s", self.last_error)
    
    def get_system_state(self) -> PneumaticState:
        """
        Get current pneumatic system state.
        
        Returns:
            Current pneumatic state
        """
        return self.pneumatic_state
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Get performance metrics.
        
        Returns:
            Performance metrics dictionary
        """
        # Calculate average efficiency
        if self.performance_metrics['total_energy_consumed'] > 0:
            self.performance_metrics['average_efficiency'] = (
                self.performance_metrics['total_work_done'] / 
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
    
    def is_compressor_available(self) -> bool:
        """
        Check if compressor is available for operation.
        
        Returns:
            True if compressor is available
        """
        return self.pneumatic_state.compressor_state in [
            CompressorState.IDLE, CompressorState.RUNNING
        ]
    
    def get_compressor_efficiency(self) -> float:
        """
        Get current compressor efficiency.
        
        Returns:
            Compressor efficiency (0.0 to 1.0)
        """
        return self.pneumatic_state.compressor_efficiency
    
    def reset(self) -> None:
        """Reset pneumatic system to initial state."""
        self.pneumatic_state = PneumaticState()
        self.pneumatic_state.compressor_efficiency = self.config.compressor_efficiency
        self.operation_history.clear()
        self.error_count = 0
        self.last_error = None
        self.performance_metrics = {
            'total_injections': 0,
            'total_venting': 0,
            'total_energy_consumed': 0.0,
            'total_work_done': 0.0,
            'average_efficiency': 0.0,
            'peak_pressure': 0.0,
            'total_heat_generated': 0.0
        }
        self.logger.info("Pneumatic system reset")

    def update(self, dt: float) -> None:
        """
        Update the pneumatic system state.
        
        Args:
            dt: Time step in seconds
        """
        try:
            # Update temperature based on heat exchange
            self._update_temperature(dt)
            
            # Update compressor state if running
            if self.pneumatic_state.compressor_state == CompressorState.RUNNING:
                self._update_compressor_operation(dt)
            
            # Update performance metrics
            self._update_performance_metrics(dt)
            
        except Exception as e:
            self.logger.error("Error updating pneumatic system: %s", e)
            self._handle_error("update_error", str(e))

    def get_state(self) -> Dict[str, Any]:
        """
        Get the current pneumatic system state.
        
        Returns:
            Dictionary containing system state
        """
        return {
            'current_pressure': self.pneumatic_state.current_pressure,
            'total_volume': self.pneumatic_state.total_volume,
            'temperature': self.pneumatic_state.temperature,
            'compressor_state': self.pneumatic_state.compressor_state.value,
            'compressor_efficiency': self.pneumatic_state.compressor_efficiency,
            'power_consumption': self.pneumatic_state.power_consumption,
            'total_work': self.pneumatic_state.total_work,
            'heat_generated': self.pneumatic_state.heat_generated,
            'performance_metrics': self.performance_metrics.copy(),
            'error_count': self.error_count
        }

    def _update_temperature(self, dt: float) -> None:
        """Update system temperature based on heat exchange."""
        # Calculate heat exchange with environment
        heat_exchange = self.config.heat_exchange_coefficient * self.config.surface_area * \
                       (self.config.ambient_temperature - self.pneumatic_state.temperature)
        
        # Update temperature (simplified thermal model)
        heat_capacity = 1000.0  # J/K (approximate for air)
        temperature_change = heat_exchange * dt / heat_capacity
        self.pneumatic_state.temperature += temperature_change

    def _update_compressor_operation(self, dt: float) -> None:
        """Update compressor operation during running state."""
        # Simulate compressor operation
        if self.pneumatic_state.power_consumption > 0:
            work_done = self.pneumatic_state.power_consumption * dt
            self.pneumatic_state.total_work += work_done
            
            # Calculate heat generation
            heat_generated = work_done * (1 - self.pneumatic_state.compressor_efficiency)
            self.pneumatic_state.heat_generated += heat_generated

    def _update_performance_metrics(self, dt: float) -> None:
        """Update performance metrics."""
        if self.performance_metrics['total_work_done'] > 0:
            self.performance_metrics['average_efficiency'] = \
                self.performance_metrics['total_work_done'] / self.performance_metrics['total_energy_consumed']

