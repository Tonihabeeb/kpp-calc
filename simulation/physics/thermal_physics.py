"""
H2 Thermal Physics Implementation
Implements thermal expansion and buoyancy boost for ascending floaters.

This module implements Hypothesis 2: thermal expansion of air in ascending floaters
due to heat exchange with warmer water provides additional buoyancy boost.
"""

import math
import logging
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ThermalState:
    """Current thermal state for a floater"""
    active: bool = False
    air_temperature: float = 293.15  # K
    water_temperature: float = 293.15  # K
    expansion_factor: float = 1.0  # Volume expansion ratio
    buoyancy_boost: float = 0.0  # Additional buoyancy force (N)
    compression_work_savings: float = 0.0  # Energy savings (J)
    heat_transfer_rate: float = 0.0  # Heat transfer rate (W)

class ThermalPhysics:
    """
    Manages H2 thermal expansion effects for KPP floaters.
    
    Applies to ascending floaters to model isothermal expansion
    due to heat exchange with surrounding water.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize thermal physics.
        
        Args:
            config (dict): Configuration parameters
        """
        if config is None:
            config = {}
        
        # Physical constants
        self.gas_constant = config.get('gas_constant', 287.0)  # J/(kg·K) for air
        self.gamma = config.get('heat_capacity_ratio', 1.4)  # Heat capacity ratio
        self.water_density = config.get('water_density', 1000.0)  # kg/m³
        self.air_density = config.get('air_density', 1.225)  # kg/m³
        self.gravity = config.get('gravity', 9.81)  # m/s²
        
        # H2 parameters
        self.h2_enabled = config.get('h2_enabled', False)
        self.base_efficiency = config.get('thermal_efficiency', 0.75)  # 75% of ideal isothermal
        self.water_temperature = config.get('water_temperature', 293.15)  # K (20°C)
        self.reference_temperature = config.get('reference_temperature', 293.15)  # K
        
        # Heat transfer parameters
        self.heat_transfer_coefficient = config.get('heat_transfer_coefficient', 200.0)  # W/(m²·K)
        self.floater_surface_area = config.get('surface_area', 2.0)  # m² (air-water interface)
        self.thermal_time_constant = config.get('thermal_time_constant', 5.0)  # seconds
        
        # Expansion limits for safety
        self.max_expansion_factor = config.get('max_expansion_factor', 1.25)  # 25% maximum
        self.min_temperature_diff = config.get('min_temperature_diff', 1.0)  # K
        
        logger.info(f"Thermal physics initialized - H2 enabled: {self.h2_enabled}, "
                   f"efficiency: {self.base_efficiency:.1%}, "
                   f"water temp: {self.water_temperature:.1f} K")
    
    def apply_thermal_effects(self, floater, velocity: float, is_ascending: bool,
                            ascent_height: float = 0.0, dt: float = 0.1) -> ThermalState:
        """
        Apply H2 thermal expansion effects to a floater.
        
        Args:
            floater: Floater object
            velocity (float): Current velocity (m/s)
            is_ascending (bool): True if floater is ascending
            ascent_height (float): Height ascended since injection (m)
            dt (float): Time step (s)
            
        Returns:
            ThermalState: Current thermal effects
        """
        state = ThermalState()
        
        # Only apply to ascending floaters with air when H2 is enabled
        if not self.h2_enabled or not is_ascending:
            return state
        
        # Check if floater has air content
        air_volume = getattr(floater, 'volume', 0.3) * getattr(floater, 'fill_progress', 0.0)
        if air_volume <= 0.01:  # Minimum air volume threshold
            return state
        
        # Calculate thermal expansion
        state = self._calculate_thermal_expansion(floater, ascent_height, dt)
        
        # Calculate buoyancy boost
        state.buoyancy_boost = self._calculate_buoyancy_boost(floater, state.expansion_factor)
        
        # Calculate compression work savings
        state.compression_work_savings = self._calculate_work_savings(floater, state.expansion_factor)
        
        state.active = True
        
        logger.debug(f"H2 thermal effects: expansion={state.expansion_factor:.3f}, "
                    f"buoyancy_boost={state.buoyancy_boost:.1f} N, "
                    f"air_temp={state.air_temperature:.1f} K, "
                    f"heat_transfer={state.heat_transfer_rate:.1f} W")
        
        return state
    
    def _calculate_thermal_expansion(self, floater, ascent_height: float, dt: float) -> ThermalState:
        """
        Calculate thermal expansion based on heat exchange with water.
        
        Args:
            floater: Floater object
            ascent_height (float): Height ascended (m)
            dt (float): Time step (s)
            
        Returns:
            ThermalState: Updated thermal state
        """
        state = ThermalState()
        
        # Get floater air properties
        air_volume = getattr(floater, 'volume', 0.3) * getattr(floater, 'fill_progress', 1.0)
        air_mass = self.air_density * air_volume
        
        # Current air temperature (start at injection temperature)
        current_air_temp = getattr(floater, 'air_temperature', self.reference_temperature)
        
        # Temperature difference drives heat transfer
        temp_diff = self.water_temperature - current_air_temp
        
        if abs(temp_diff) < self.min_temperature_diff:
            state.air_temperature = current_air_temp
            state.water_temperature = self.water_temperature
            state.expansion_factor = 1.0
            return state
        
        # Heat transfer rate calculation
        # Q = h * A * ΔT
        heat_transfer_rate = (self.heat_transfer_coefficient * 
                            self.floater_surface_area * temp_diff)
        
        # Temperature change rate
        # dT/dt = Q / (m * c_p)
        specific_heat = 1005.0  # J/(kg·K) for air at constant pressure
        temp_change_rate = heat_transfer_rate / (air_mass * specific_heat)
        
        # Update air temperature with exponential approach to water temperature
        # Using first-order thermal dynamics
        tau = self.thermal_time_constant
        alpha = 1 - math.exp(-dt / tau)
        new_air_temp = current_air_temp + alpha * temp_diff
        
        # Limit temperature change rate for stability
        max_temp_change = 5.0 * dt  # 5 K/s maximum
        if abs(new_air_temp - current_air_temp) > max_temp_change:
            new_air_temp = current_air_temp + math.copysign(max_temp_change, temp_diff)
        
        # Calculate expansion factor for isothermal process
        # For ideal gas: V₂/V₁ = T₂/T₁ (constant pressure approximation)
        expansion_factor = new_air_temp / self.reference_temperature
        
        # Apply efficiency factor (real expansion is less than ideal)
        effective_expansion = 1.0 + (expansion_factor - 1.0) * self.base_efficiency
        
        # Limit expansion for safety
        effective_expansion = min(effective_expansion, self.max_expansion_factor)
        
        # Update state
        state.air_temperature = new_air_temp
        state.water_temperature = self.water_temperature
        state.expansion_factor = effective_expansion
        state.heat_transfer_rate = heat_transfer_rate
        
        # Update floater's air temperature if possible
        if hasattr(floater, 'air_temperature'):
            floater.air_temperature = new_air_temp
        
        return state
    
    def _calculate_buoyancy_boost(self, floater, expansion_factor: float) -> float:
        """
        Calculate additional buoyancy force from thermal expansion.
        
        Args:
            floater: Floater object
            expansion_factor (float): Volume expansion ratio
            
        Returns:
            float: Additional buoyancy force (N)
        """
        if expansion_factor <= 1.0:
            return 0.0
        
        # Base air volume and expansion
        base_air_volume = getattr(floater, 'volume', 0.3) * getattr(floater, 'fill_progress', 1.0)
        expanded_volume = base_air_volume * expansion_factor
        additional_volume = expanded_volume - base_air_volume
        
        # Additional buoyancy from expanded volume
        # F_b = ρ_water * g * ΔV
        additional_buoyancy = self.water_density * self.gravity * additional_volume
        
        return additional_buoyancy
    
    def _calculate_work_savings(self, floater, expansion_factor: float) -> float:
        """
        Calculate compression work savings due to thermal assistance.
        
        Args:
            floater: Floater object
            expansion_factor (float): Volume expansion ratio
            
        Returns:
            float: Work savings (J)
        """
        if expansion_factor <= 1.0:
            return 0.0
        
        # Estimate work savings from thermal energy input
        # W_saved = ∫ P dV for thermal expansion
        base_volume = getattr(floater, 'volume', 0.3) * getattr(floater, 'fill_progress', 1.0)
        pressure = getattr(floater, 'current_air_pressure', 101325.0)  # Pa
        
        # For isothermal expansion: W = P * V * ln(V₂/V₁)
        if expansion_factor > 1.001:  # Avoid log(1) = 0
            work_savings = pressure * base_volume * math.log(expansion_factor)
        else:
            work_savings = 0.0
        
        return work_savings
    
    def calculate_enhanced_buoyancy(self, base_buoyancy: float, 
                                  thermal_state: ThermalState) -> float:
        """
        Calculate enhanced buoyancy with thermal effects.
        
        Args:
            base_buoyancy (float): Base buoyant force (N)
            thermal_state (ThermalState): Current thermal state
            
        Returns:
            float: Enhanced buoyant force (N)
        """
        if not thermal_state.active:
            return base_buoyancy
        
        enhanced_buoyancy = base_buoyancy + thermal_state.buoyancy_boost
        
        logger.debug(f"Thermal buoyancy enhancement: "
                    f"base={base_buoyancy:.1f} N, boost={thermal_state.buoyancy_boost:.1f} N, "
                    f"enhanced={enhanced_buoyancy:.1f} N")
        
        return enhanced_buoyancy
    
    def calculate_compression_work_reduction(self, base_work: float,
                                           thermal_state: ThermalState) -> float:
        """
        Calculate reduced compression work with thermal assistance.
        
        Args:
            base_work (float): Base compression work (J)
            thermal_state (ThermalState): Current thermal state
            
        Returns:
            float: Reduced compression work (J)
        """
        if not thermal_state.active:
            return base_work
        
        # Apply work reduction based on thermal efficiency
        work_reduction = base_work * 0.15 * self.base_efficiency  # Up to 15% reduction
        reduced_work = max(base_work - work_reduction, 0.1 * base_work)
        
        logger.debug(f"Compression work reduction: "
                    f"base={base_work:.1f} J, reduction={work_reduction:.1f} J, "
                    f"reduced={reduced_work:.1f} J")
        
        return reduced_work
    
    def get_system_status(self) -> Dict[str, Any]:
        """
        Get current thermal system status.
        
        Returns:
            dict: System status information
        """
        return {
            'h2_enabled': self.h2_enabled,
            'thermal_efficiency': self.base_efficiency,
            'water_temperature': self.water_temperature,
            'reference_temperature': self.reference_temperature,
            'heat_transfer_coefficient': self.heat_transfer_coefficient,
            'max_expansion_factor': self.max_expansion_factor,
            'thermal_time_constant': self.thermal_time_constant
        }
    
    def set_h2_enabled(self, enabled: bool):
        """
        Enable or disable H2 thermal effects.
        
        Args:
            enabled (bool): Whether to enable H2 effects
        """
        self.h2_enabled = enabled
        logger.info(f"H2 thermal physics {'enabled' if enabled else 'disabled'}")
    
    def set_water_temperature(self, temperature: float):
        """
        Set water temperature.
        
        Args:
            temperature (float): Water temperature in Kelvin
        """
        self.water_temperature = max(273.15, min(temperature, 373.15))  # Limit to liquid range
        logger.info(f"Water temperature set to {self.water_temperature:.1f} K "
                   f"({self.water_temperature - 273.15:.1f}°C)")
    
    def update_parameters(self, params: Dict[str, Any]):
        """
        Update thermal physics parameters.
        
        Args:
            params (dict): Parameter updates
        """
        if 'h2_enabled' in params:
            self.h2_enabled = bool(params['h2_enabled'])
        
        if 'thermal_efficiency' in params:
            self.base_efficiency = max(0.0, min(params['thermal_efficiency'], 1.0))
        
        if 'water_temperature' in params:
            # Convert from Celsius if needed
            temp = params['water_temperature']
            if temp < 100:  # Assume Celsius
                temp += 273.15
            self.set_water_temperature(temp)
        
        logger.info(f"Thermal parameters updated: enabled={self.h2_enabled}, "
                   f"efficiency={self.base_efficiency:.1%}, "
                   f"water_temp={self.water_temperature:.1f} K")
