import math
import logging
import time
import statistics
from typing import Any, Dict, List, Optional, Tuple, Deque
from dataclasses import dataclass
from collections import deque
from enum import Enum
from config.config import RHO_WATER, G

"""
Advanced Event Handler for KPP Simulation (Stage 2)
Enhanced state management, energy tracking, and event handling with optimization.
"""

class OptimizationMode(str, Enum):
    """Optimization mode enumeration"""
    NORMAL = "normal"
    ADAPTIVE = "adaptive"
    PREDICTIVE = "predictive"
    THERMAL = "thermal"

@dataclass
class OptimizationMetrics:
    """Optimization metrics data structure"""
    mode: OptimizationMode
    pressure_adjustment: float = 0.0
    timing_adjustment: float = 0.0
    energy_savings: float = 0.0
    efficiency_improvement: float = 0.0
    success_rate: float = 0.0
    thermal_efficiency: float = 0.0

@dataclass
class ThermalState:
    """Thermal state data structure"""
    water_temperature: float = 293.15  # K (20°C)
    air_temperature: float = 293.15    # K (20°C)
    compressor_temperature: float = 313.15  # K (40°C)
    heat_exchange_rate: float = 0.0
    thermal_efficiency: float = 0.0

class AdvancedEventHandler:
    """
    Advanced event handler with optimization capabilities.
    Implements adaptive pressure control, predictive timing, and thermal integration.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the advanced event handler.
        
        Args:
            config: Configuration dictionary for advanced event handling
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # Physics constants
        self.rho_water = RHO_WATER
        self.gravity = G
        self.atmospheric_pressure = 101325.0  # Pa
        
        # Optimization settings
        self.optimization_mode = OptimizationMode.NORMAL
        self.adaptive_pressure_enabled = True
        self.predictive_timing_enabled = True
        self.thermal_optimization_enabled = True
        
        # Performance tracking
        self.injection_history: Deque[Dict[str, Any]] = deque(maxlen=100)
        self.energy_history: Deque[float] = deque(maxlen=100)
        self.success_history: Deque[bool] = deque(maxlen=100)
        self.timing_history: Deque[float] = deque(maxlen=100)
        
        # Optimization metrics
        self.optimization_metrics = OptimizationMetrics(OptimizationMode.NORMAL)
        self.baseline_energy = 0.0
        self.optimization_savings = 0.0
        
        # Thermal state
        self.thermal_state = ThermalState()
        self.thermal_history: Deque[ThermalState] = deque(maxlen=50)
        
        # Adaptive parameters
        self.base_pressure = self.config.get('base_pressure', 300000.0)  # Pa
        self.pressure_adjustment_factor = 0.1
        self.min_pressure = 200000.0  # Pa
        self.max_pressure = 500000.0  # Pa
        
        # Predictive timing parameters
        self.timing_prediction_window = 10  # events
        self.timing_adjustment_factor = 0.05
        self.min_timing_interval = 0.3  # seconds
        self.max_timing_interval = 2.0  # seconds
        
        # Analytics
        self.analytics = {
            'total_injections': 0,
            'successful_injections': 0,
            'failed_injections': 0,
            'total_energy': 0.0,
            'average_energy': 0.0,
            'energy_variance': 0.0,
            'success_rate': 0.0,
            'efficiency_trend': 0.0,
            'optimization_savings': 0.0
        }
        
        self.logger.info("Advanced event handler initialized with optimization mode: %s", 
                        self.optimization_mode)
    
    def calculate_thermal_effects(self, volume: float, pressure: float, 
                                temperature: float) -> float:
        """
        Calculate thermal effects on compression work.
        
        Args:
            volume: Air volume (m³)
            pressure: Compression pressure (Pa)
            temperature: Temperature (K)
            
        Returns:
            Thermal correction factor
        """
        # Ideal gas law correction for temperature
        reference_temperature = 293.15  # K (20°C)
        temperature_factor = temperature / reference_temperature
        
        # Thermal expansion effects
        thermal_expansion = 1.0 + 0.00367 * (temperature - reference_temperature)
        
        # Heat exchange effects (simplified)
        heat_exchange_factor = 1.0 - 0.05 * (temperature - reference_temperature) / 100.0
        
        # Combined thermal factor
        thermal_factor = temperature_factor * thermal_expansion * heat_exchange_factor
        
        return thermal_factor
    
    def calculate_adaptive_pressure(self, success_rate: float, 
                                  energy_variance: float) -> float:
        """
        Calculate adaptive pressure based on performance metrics.
        
        Args:
            success_rate: Recent success rate (0.0 to 1.0)
            energy_variance: Energy consumption variance
            
        Returns:
            Adjusted pressure (Pa)
        """
        if not self.adaptive_pressure_enabled:
            return self.base_pressure
        
        # Pressure adjustment based on success rate
        if success_rate < 0.8:  # Low success rate
            pressure_adjustment = self.pressure_adjustment_factor * (0.8 - success_rate)
        elif success_rate > 0.95:  # High success rate, can reduce pressure
            pressure_adjustment = -self.pressure_adjustment_factor * (success_rate - 0.95)
        else:
            pressure_adjustment = 0.0
        
        # Additional adjustment based on energy variance
        if energy_variance > 0.2:  # High variance, increase pressure for consistency
            pressure_adjustment += self.pressure_adjustment_factor * 0.1
        
        # Calculate new pressure
        new_pressure = self.base_pressure * (1.0 + pressure_adjustment)
        
        # Apply limits
        new_pressure = max(self.min_pressure, min(self.max_pressure, new_pressure))
        
        # Update optimization metrics
        self.optimization_metrics.pressure_adjustment = pressure_adjustment
        
        return new_pressure
    
    def predict_optimal_timing(self, recent_timings: List[float], 
                             success_rates: List[float]) -> float:
        """
        Predict optimal timing for next injection.
        
        Args:
            recent_timings: Recent timing intervals
            success_rates: Recent success rates
            
        Returns:
            Predicted optimal timing interval (seconds)
        """
        if not self.predictive_timing_enabled or len(recent_timings) < 3:
            return self.config.get('default_timing', 0.5)
        
        try:
            # Calculate average timing
            avg_timing = statistics.mean(recent_timings)
            
            # Calculate timing variance
            timing_variance = statistics.variance(recent_timings)
            
            # Adjust based on success rate trend
            if len(success_rates) >= 3:
                recent_success_rate = statistics.mean(success_rates[-3:])
                if recent_success_rate < 0.8:
                    # Low success rate, increase timing interval
                    timing_adjustment = self.timing_adjustment_factor * (0.8 - recent_success_rate)
                elif recent_success_rate > 0.95:
                    # High success rate, can decrease timing interval
                    timing_adjustment = -self.timing_adjustment_factor * (recent_success_rate - 0.95)
                else:
                    timing_adjustment = 0.0
            else:
                timing_adjustment = 0.0
            
            # Calculate optimal timing
            optimal_timing = avg_timing * (1.0 + timing_adjustment)
            
            # Apply limits
            optimal_timing = max(self.min_timing_interval, 
                               min(self.max_timing_interval, optimal_timing))
            
            # Update optimization metrics
            self.optimization_metrics.timing_adjustment = timing_adjustment
            
            return optimal_timing
            
        except Exception as e:
            self.logger.error("Error predicting optimal timing: %s", e)
            return self.config.get('default_timing', 0.5)
    
    def calculate_thermal_optimization(self, thermal_state: ThermalState) -> float:
        """
        Calculate thermal optimization factor.
        
        Args:
            thermal_state: Current thermal state
            
        Returns:
            Thermal optimization factor
        """
        if not self.thermal_optimization_enabled:
            return 1.0
        
        try:
            # Calculate temperature difference
            temp_diff = thermal_state.water_temperature - thermal_state.air_temperature
            
            # Heat exchange efficiency
            heat_exchange_efficiency = 1.0 - abs(temp_diff) / 100.0
            heat_exchange_efficiency = max(0.5, min(1.0, heat_exchange_efficiency))
            
            # Compressor efficiency based on temperature
            compressor_efficiency = 1.0 - (thermal_state.compressor_temperature - 293.15) / 100.0
            compressor_efficiency = max(0.7, min(1.0, compressor_efficiency))
            
            # Combined thermal efficiency
            thermal_efficiency = heat_exchange_efficiency * compressor_efficiency
            
            # Update thermal state
            thermal_state.thermal_efficiency = thermal_efficiency
            
            return thermal_efficiency
            
        except Exception as e:
            self.logger.error("Error calculating thermal optimization: %s", e)
            return 1.0
    
    def update_analytics(self, injection_data: Dict[str, Any]) -> None:
        """
        Update analytics with injection data.
        
        Args:
            injection_data: Injection event data
        """
        # Add to history
        self.injection_history.append(injection_data)
        
        # Update basic metrics
        self.analytics['total_injections'] += 1
        
        if injection_data.get('success', False):
            self.analytics['successful_injections'] += 1
            self.success_history.append(True)
        else:
            self.analytics['failed_injections'] += 1
            self.success_history.append(False)
        
        # Update energy metrics
        energy = injection_data.get('energy_cost', 0.0)
        self.analytics['total_energy'] += energy
        self.energy_history.append(energy)
        
        # Calculate averages and variances
        if len(self.energy_history) > 0:
            self.analytics['average_energy'] = statistics.mean(self.energy_history)
            if len(self.energy_history) > 1:
                self.analytics['energy_variance'] = statistics.variance(self.energy_history)
        
        # Calculate success rate
        if len(self.success_history) > 0:
            self.analytics['success_rate'] = sum(self.success_history) / len(self.success_history)
        
        # Calculate efficiency trend
        if len(self.energy_history) >= 10:
            recent_energy = statistics.mean(list(self.energy_history)[-10:])
            older_energy = statistics.mean(list(self.energy_history)[-20:-10])
            if older_energy > 0:
                self.analytics['efficiency_trend'] = (older_energy - recent_energy) / older_energy
        
        # Calculate optimization savings
        if self.baseline_energy > 0:
            current_energy = self.analytics['average_energy']
            self.analytics['optimization_savings'] = (self.baseline_energy - current_energy) / self.baseline_energy
            self.optimization_metrics.energy_savings = self.analytics['optimization_savings']
    
    def optimize_injection_parameters(self, floater: Any, floater_id: int) -> Dict[str, Any]:
        """
        Optimize injection parameters based on performance analytics.
        
        Args:
            floater: Floater object
            floater_id: Floater identifier
            
        Returns:
            Optimized parameters dictionary
        """
        # Get recent performance data
        recent_success_rates = []
        recent_timings = []
        
        if len(self.success_history) >= 10:
            recent_success_rates = list(self.success_history)[-10:]
        
        if len(self.timing_history) >= 10:
            recent_timings = list(self.timing_history)[-10:]
        
        # Calculate adaptive pressure
        success_rate = self.analytics['success_rate']
        energy_variance = self.analytics['energy_variance']
        adaptive_pressure = self.calculate_adaptive_pressure(success_rate, energy_variance)
        
        # Predict optimal timing
        optimal_timing = self.predict_optimal_timing(recent_timings, recent_success_rates)
        
        # Calculate thermal optimization
        thermal_factor = self.calculate_thermal_optimization(self.thermal_state)
        
        # Update optimization mode
        if len(self.injection_history) >= 20:
            if self.analytics['success_rate'] > 0.9 and self.analytics['efficiency_trend'] > 0.05:
                self.optimization_mode = OptimizationMode.PREDICTIVE
            elif self.analytics['success_rate'] < 0.8:
                self.optimization_mode = OptimizationMode.ADAPTIVE
            else:
                self.optimization_mode = OptimizationMode.NORMAL
        
        # Update optimization metrics
        self.optimization_metrics.mode = self.optimization_mode
        self.optimization_metrics.success_rate = success_rate
        self.optimization_metrics.thermal_efficiency = thermal_factor
        
        return {
            'pressure': adaptive_pressure,
            'timing': optimal_timing,
            'thermal_factor': thermal_factor,
            'optimization_mode': self.optimization_mode,
            'success_rate': success_rate,
            'energy_savings': self.analytics['optimization_savings']
        }
    
    def handle_advanced_injection(self, floater: Any, floater_id: int, 
                                target_volume: float = 0.4) -> Dict[str, Any]:
        """
        Handle advanced injection with optimization.
        
        Args:
            floater: Floater object
            floater_id: Floater identifier
            target_volume: Target air volume (m³)
            
        Returns:
            Injection result with optimization data
        """
        start_time = time.time()
        
        # Get optimized parameters
        optimized_params = self.optimize_injection_parameters(floater, floater_id)
        
        # Calculate energy cost with thermal effects
        position = getattr(floater, 'position', 0.0)
        tank_height = self.config.get('tank_height', 10.0)
        depth = max(0.0, tank_height - position)
        
        # Calculate pressure with thermal effects
        hydrostatic_pressure = self.rho_water * self.gravity * depth
        final_pressure = self.atmospheric_pressure + hydrostatic_pressure
        
        # Apply thermal optimization
        thermal_factor = optimized_params['thermal_factor']
        effective_pressure = final_pressure * thermal_factor
        
        # Calculate compression work with thermal effects
        compression_work = self.calculate_compression_work(
            target_volume, self.atmospheric_pressure, effective_pressure
        )
        
        # Apply thermal correction
        thermal_correction = self.calculate_thermal_effects(
            target_volume, effective_pressure, self.thermal_state.water_temperature
        )
        
        total_energy = compression_work * thermal_correction
        
        # Update floater state
        floater.air_fill_level = 1.0
        floater.state = "full"
        
        # Record injection data
        injection_data = {
            'floater_id': floater_id,
            'timestamp': start_time,
            'position': position,
            'pressure': optimized_params['pressure'],
            'energy_cost': total_energy,
            'success': True,
            'optimization_mode': optimized_params['optimization_mode'],
            'thermal_factor': thermal_factor,
            'timing': optimized_params['timing']
        }
        
        # Update analytics
        self.update_analytics(injection_data)
        
        # Log optimization results
        if self.analytics['total_injections'] % 10 == 0:
            self.logger.info("Advanced injection %d: mode=%s, success_rate=%.3f, energy_savings=%.1f%%", 
                           self.analytics['total_injections'], 
                           optimized_params['optimization_mode'],
                           optimized_params['success_rate'],
                           optimized_params['energy_savings'] * 100)
        
        return injection_data
    
    def calculate_compression_work(self, volume: float, initial_pressure: float, 
                                 final_pressure: float) -> float:
        """
        Calculate compression work using isothermal compression formula.
        
        Args:
            volume: Volume of air (m³)
            initial_pressure: Initial pressure (Pa)
            final_pressure: Final pressure (Pa)
            
        Returns:
            Compression work (Joules)
        """
        if initial_pressure <= 0 or final_pressure <= 0:
            return 0.0
        
        work = initial_pressure * volume * math.log(final_pressure / initial_pressure)
        return work
    
    def update_thermal_state(self, water_temp: float, air_temp: float, 
                           compressor_temp: float) -> None:
        """
        Update thermal state.
        
        Args:
            water_temp: Water temperature (K)
            air_temp: Air temperature (K)
            compressor_temp: Compressor temperature (K)
        """
        self.thermal_state.water_temperature = water_temp
        self.thermal_state.air_temperature = air_temp
        self.thermal_state.compressor_temperature = compressor_temp
        
        # Calculate heat exchange rate
        temp_diff = water_temp - air_temp
        self.thermal_state.heat_exchange_rate = abs(temp_diff) * 0.1  # Simplified
        
        # Add to thermal history
        self.thermal_history.append(ThermalState(
            water_temperature=water_temp,
            air_temperature=air_temp,
            compressor_temperature=compressor_temp,
            heat_exchange_rate=self.thermal_state.heat_exchange_rate
        ))
    
    def get_optimization_metrics(self) -> OptimizationMetrics:
        """
        Get current optimization metrics.
        
        Returns:
            Optimization metrics
        """
        return self.optimization_metrics
    
    def get_analytics(self) -> Dict[str, Any]:
        """
        Get current analytics.
        
        Returns:
            Analytics dictionary
        """
        return self.analytics.copy()
    
    def get_thermal_state(self) -> ThermalState:
        """
        Get current thermal state.
        
        Returns:
            Thermal state
        """
        return self.thermal_state
    
    def set_baseline_energy(self, baseline: float) -> None:
        """
        Set baseline energy for savings calculation.
        
        Args:
            baseline: Baseline energy consumption
        """
        self.baseline_energy = baseline
        self.logger.info("Baseline energy set to %.2f J", baseline)
    
    def reset(self) -> None:
        """Reset advanced event handler state."""
        self.injection_history.clear()
        self.energy_history.clear()
        self.success_history.clear()
        self.timing_history.clear()
        self.thermal_history.clear()
        
        self.optimization_metrics = OptimizationMetrics(OptimizationMode.NORMAL)
        self.thermal_state = ThermalState()
        
        self.analytics = {
            'total_injections': 0,
            'successful_injections': 0,
            'failed_injections': 0,
            'total_energy': 0.0,
            'average_energy': 0.0,
            'energy_variance': 0.0,
            'success_rate': 0.0,
            'efficiency_trend': 0.0,
            'optimization_savings': 0.0
        }
        
        self.logger.info("Advanced event handler reset")

