"""
Environment component for KPP simulation.
Handles water properties, pressure, and enhancement effects.
"""

import math
import logging
from dataclasses import dataclass
from typing import Dict, Any, Optional

@dataclass
class EnvironmentConfig:
    """Configuration for environment"""
    def __init__(self, **kwargs):
        self.water_density = kwargs.get('water_density', 1000.0)  # kg/m³
        self.water_temperature = kwargs.get('water_temperature', 20.0)  # °C
        self.enable_h1 = kwargs.get('enable_h1', False)
        self.nanobubble_fraction = kwargs.get('nanobubble_fraction', 0.2)
        self.enable_h2 = kwargs.get('enable_h2', False)
        self.thermal_expansion_coeff = kwargs.get('thermal_expansion_coeff', 0.001)  # /K

class Environment:
    """
    Environment class.
    Handles water properties, pressure, and enhancement effects.
    """
    
    def __init__(self, config: EnvironmentConfig):
        """Initialize environment with configuration"""
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Basic properties
        self.water_density = config.water_density
        self.water_temperature = config.water_temperature
        self.base_density = config.water_density
        
        # Enhancement states
        self.h1_enabled = config.enable_h1
        self.h2_enabled = config.enable_h2
        self.nanobubble_fraction = config.nanobubble_fraction
        self.thermal_expansion_coeff = config.thermal_expansion_coeff
        
        # Dynamic state
        self.pressure = 101325.0  # Pa (1 atm)
        self.temperature_delta = 0.0  # K
        self.effective_density = self.water_density
        self.effective_viscosity = 1.0e-3  # Pa·s
        
        # Enhancement effects
        self.h1_effect = 0.0
        self.h2_effect = 0.0
        
        self.logger.info("Environment initialized")
    
    def compute_effective_density(self, is_ascending: bool) -> float:
        """
        Compute effective water density considering H1 effects.
        
        Args:
            is_ascending: Whether the floater is on ascending side (buoyant)
            
        Returns:
            float: Effective water density in kg/m³
        """
        if not self.h1_enabled:
            return self.base_density
            
        # H1 effect only applies to descending side (non-buoyant floaters)
        # Nanobubbles are injected at the bottom and affect the descending water column
        if is_ascending:
            return self.base_density  # No density reduction on ascending side
        
        # Only reduce density on descending side
        density_reduction = self.base_density * self.nanobubble_fraction
        
        # Ensure density doesn't go below minimum
        min_density = 100.0  # kg/m³
        return max(min_density, self.base_density - density_reduction)
    
    def compute_drag_coefficient(self, is_ascending: bool, base_cd: float = 0.8) -> float:
        """
        Compute drag coefficient considering H1 effects.
        
        Args:
            is_ascending: Whether the floater is on ascending side (buoyant)
            base_cd: Base drag coefficient without H1 effects
            
        Returns:
            float: Modified drag coefficient
        """
        if not self.h1_enabled:
            return base_cd
            
        # H1 reduces drag only on descending side (non-buoyant floaters)
        # Nanobubbles reduce turbulence in the descending water column
        if is_ascending:
            return base_cd  # No drag reduction on ascending side
        
        # Only reduce drag on descending side
        drag_reduction = base_cd * self.nanobubble_fraction
        
        # Ensure Cd doesn't go below minimum
        min_cd = 0.1
        return max(min_cd, base_cd - drag_reduction)
    
    def compute_buoyant_force(self, volume: float, depth: float, is_ascending: bool) -> Dict[str, float]:
        """
        Compute buoyant force with H2 thermal effects.
        
        Args:
            volume: Floater volume in m³
            depth: Current depth in meters
            is_ascending: Whether the floater is ascending
            
        Returns:
            Dictionary containing buoyancy calculations
        """
        # Get base density considering H1
        rho = self.compute_effective_density(is_ascending)
        g = 9.81  # m/s²
        
        # Base buoyant force
        base_force = rho * volume * g
        
        if not self.h2_enabled or not is_ascending:
            return {
                'force': base_force,
                'effective_volume': volume,
                'h2_boost': 0.0
            }
        
        # H2 thermal expansion effects
        # As floater rises, air expands more due to heat absorption
        height_fraction = 1.0 - (depth / 10.0)  # Normalized height (assume 10m depth)
        temperature_rise = 20.0 * height_fraction  # Maximum 20°C rise
        
        # Volume expansion from temperature
        expansion_factor = 1.0 + (self.thermal_expansion_coeff * temperature_rise)
        effective_volume = volume * expansion_factor
        
        # Enhanced buoyant force
        enhanced_force = rho * effective_volume * g
        h2_boost = enhanced_force - base_force
        
        return {
            'force': enhanced_force,
            'effective_volume': effective_volume,
            'h2_boost': h2_boost
        }
    
    def compute_drag_force(self, velocity: float, cross_section: float, is_ascending: bool) -> float:
        """
        Compute drag force considering H1 effects.
        
        Args:
            velocity: Relative velocity in m/s
            cross_section: Cross-sectional area in m²
            is_ascending: Whether the floater is on ascending side
            
        Returns:
            float: Drag force in N
        """
        # Get effective density and drag coefficient
        rho = self.compute_effective_density(is_ascending)
        cd = self.compute_drag_coefficient(is_ascending)
        
        # Drag force = ½ρCdAv²
        return 0.5 * rho * cd * cross_section * velocity * abs(velocity)  # abs(v) for correct sign
    
    def update(self, time_step: float) -> None:
        """
        Update environment state.
        
        Args:
            time_step: Time step in seconds
        """
        try:
            # Update H1 effects (nanobubbles)
            if self.h1_enabled:
                # Calculate average density reduction across ascending/descending sides
                density_reduction_asc = self.base_density * self.nanobubble_fraction
                density_reduction_desc = self.base_density * self.nanobubble_fraction * 1.5
                avg_reduction = (density_reduction_asc + density_reduction_desc) / 2
                
                self.effective_density = self.base_density - avg_reduction
                self.h1_effect = avg_reduction / self.base_density
            else:
                self.effective_density = self.base_density
                self.h1_effect = 0.0
            
            # Update H2 effects (thermal)
            if self.h2_enabled:
                # Temperature affects density and expansion
                self.temperature_delta = max(0, self.temperature_delta)
                
                # Density change from base temperature
                density_change = self.base_density * self.thermal_expansion_coeff * self.temperature_delta
                self.effective_density -= density_change
                
                # Track thermal effect
                self.h2_effect = density_change / self.base_density
            else:
                self.temperature_delta = 0.0
                self.h2_effect = 0.0
            
            # Update viscosity based on temperature
            base_temp = 293.15  # 20°C in K
            current_temp = base_temp + self.temperature_delta
            self.effective_viscosity = 1.0e-3 * math.exp(1500 * (1/current_temp - 1/base_temp))
            
        except Exception as e:
            self.logger.error(f"Error in environment update: {e}")
            raise
    
    def get_state(self) -> Dict[str, Any]:
        """Get current environment state"""
        return {
            'water_density': self.effective_density,
            'water_temperature': self.water_temperature + self.temperature_delta,
            'pressure': self.pressure,
            'viscosity': self.effective_viscosity,
            'h1_enabled': self.h1_enabled,
            'h1_effect': self.h1_effect,
            'h2_enabled': self.h2_enabled,
            'h2_effect': self.h2_effect,
            'thermal_expansion_coeff': self.thermal_expansion_coeff
        }
    
    def set_h1_enabled(self, enabled: bool) -> None:
        """Enable/disable H1 enhancement"""
        self.h1_enabled = enabled
        if not enabled:
            self.h1_effect = 0.0
    
    def set_h2_enabled(self, enabled: bool) -> None:
        """Enable/disable H2 enhancement"""
        self.h2_enabled = enabled
        if not enabled:
            self.h2_effect = 0.0
            self.temperature_delta = 0.0
    
    def set_temperature_delta(self, delta: float) -> None:
        """Set temperature change from base temperature"""
        self.temperature_delta = delta
    
    def set_pressure(self, pressure: float) -> None:
        """Set ambient pressure"""
        self.pressure = pressure
    
    def get_density(self) -> float:
        """Get current effective water density"""
        return self.effective_density
    
    def get_viscosity(self) -> float:
        """Get current effective water viscosity"""
        return self.effective_viscosity
    
    def get_pressure(self) -> float:
        """Get current ambient pressure"""
        return self.pressure
    
    def get_temperature(self) -> float:
        """Get current water temperature"""
        return self.water_temperature + self.temperature_delta

    def set_nanobubble_fraction(self, fraction: float) -> None:
        """
        Set the nanobubble fraction for H1 enhancement.
        
        Args:
            fraction: Nanobubble fraction (0.0 to 1.0)
        """
        if not 0.0 <= fraction <= 1.0:
            raise ValueError("Nanobubble fraction must be between 0.0 and 1.0")
        self.nanobubble_fraction = fraction
        
    def set_thermal_expansion_coeff(self, coeff: float) -> None:
        """
        Set the thermal expansion coefficient for H2 enhancement.
        
        Args:
            coeff: Thermal expansion coefficient (/K)
        """
        if coeff < 0:
            raise ValueError("Thermal expansion coefficient must be non-negative")
        self.thermal_expansion_coeff = coeff

