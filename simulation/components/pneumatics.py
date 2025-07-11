"""
Pneumatic system component for KPP simulation.
Handles air injection, compression, and thermal effects.
"""

import math
import logging
from dataclasses import dataclass
from typing import Dict, Any, Optional

@dataclass
class PneumaticConfig:
    """Configuration for pneumatic system"""
    def __init__(self, **kwargs):
        self.enable_h2 = kwargs.get('enable_h2', False)
        self.thermal_expansion_coeff = kwargs.get('thermal_expansion_coeff', 0.001)  # /K
        self.isothermal_efficiency = kwargs.get('isothermal_efficiency', 0.9)
        self.max_pressure = kwargs.get('max_pressure', 10.0e5)  # Pa (10 bar)
        self.min_pressure = kwargs.get('min_pressure', 1.0e5)  # Pa (1 bar)
        self.compressor_power = kwargs.get('compressor_power', 5000.0)  # W
        self.storage_volume = kwargs.get('storage_volume', 0.5)  # m³

class PneumaticSystem:
    """
    Pneumatic system class.
    Handles air injection, compression, and thermal effects.
    """
    
    def __init__(self, config: PneumaticConfig):
        """Initialize pneumatic system with configuration"""
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Basic properties
        self.storage_pressure = self.config.min_pressure
        self.storage_temperature = 293.15  # K (20°C)
        self.storage_volume = self.config.storage_volume
        
        # Enhancement states
        self.h2_enabled = config.enable_h2
        self.thermal_expansion_coeff = config.thermal_expansion_coeff
        
        # Operating state
        self.compressor_power = 0.0
        self.injection_power = 0.0
        self.total_energy = 0.0
        self.air_mass = self.storage_pressure * self.storage_volume / (287.05 * self.storage_temperature)
        
        # Enhancement effects
        self.h2_effect = 0.0
        
        self.logger.info("Pneumatic system initialized")
    
    def compute_thermal_expansion(self, depth: float, volume: float) -> Dict[str, float]:
        """
        Compute thermal expansion effects for H2 enhancement.
        
        Args:
            depth: Current depth in meters
            volume: Air volume in m³
            
        Returns:
            Dictionary containing expansion effects
        """
        if not self.h2_enabled:
            return {
                'expanded_volume': volume,
                'pressure_ratio': 1.0,
                'energy_saved': 0.0
            }
        
        # Base pressure at depth
        depth_pressure = 1000.0 * 9.81 * abs(depth)  # Pa
        
        # Temperature effect on expansion
        # As air rises, it can absorb heat to maintain higher pressure
        height_fraction = 1.0 - (depth / 10.0)  # Normalized height (assume 10m depth)
        temperature_rise = 20.0 * height_fraction  # Maximum 20°C rise
        
        # Thermal expansion effect
        expansion_factor = 1.0 + (self.thermal_expansion_coeff * temperature_rise)
        expanded_volume = volume * expansion_factor
        
        # Pressure ratio considering thermal effects
        # In isothermal process, P1V1 = P2V2
        pressure_ratio = volume / expanded_volume
        
        # Energy saved due to thermal assistance
        # Less work needed due to heat absorption from surroundings
        energy_saved = depth_pressure * volume * (1.0 - pressure_ratio)
        
        return {
            'expanded_volume': expanded_volume,
            'pressure_ratio': pressure_ratio,
            'energy_saved': energy_saved
        }
    
    def update(self, time_step: float) -> Dict[str, Any]:
        """
        Update pneumatic system state.
        
        Args:
            time_step: Time step in seconds
            
        Returns:
            Dictionary containing system state
        """
        try:
            # Update compressor state
            if self.storage_pressure < self.config.max_pressure:
                # Compressor running
                self.compressor_power = self.config.compressor_power
                
                # Calculate mass flow rate with H2 consideration
                power_available = self.compressor_power * self.config.isothermal_efficiency
                if self.h2_enabled:
                    # Higher efficiency due to thermal assistance
                    power_available *= (1.0 + self.thermal_expansion_coeff * 20.0)  # Assume 20°C rise
                
                pressure_ratio = self.storage_pressure / self.config.min_pressure
                mass_flow = power_available / (287.05 * self.storage_temperature * math.log(pressure_ratio))
                
                # Update storage state
                self.air_mass += mass_flow * time_step
                self.storage_pressure = self.air_mass * 287.05 * self.storage_temperature / self.storage_volume
                
            else:
                # Compressor off
                self.compressor_power = 0.0
            
            # Update thermal effects (H2)
            if self.h2_enabled:
                # Temperature affects pressure and efficiency
                base_temp = 293.15  # 20°C in K
                temp_rise = 20.0  # Maximum temperature rise
                self.storage_temperature = base_temp + (temp_rise * self.h2_enabled)
                
                # Pressure increase from thermal expansion
                pressure_increase = self.storage_pressure * self.thermal_expansion_coeff * temp_rise
                self.storage_pressure += pressure_increase
                
                # Track effect magnitude
                self.h2_effect = pressure_increase / self.storage_pressure
            else:
                self.storage_temperature = 293.15
                self.h2_effect = 0.0
            
            # Update energy consumption
            self.total_energy += (self.compressor_power + self.injection_power) * time_step
            
            # Reset injection power (only active during injection)
            self.injection_power = 0.0
            
            return self.get_state()
            
        except Exception as e:
            self.logger.error(f"Error in pneumatic system update: {e}")
            raise
    
    def get_state(self) -> Dict[str, Any]:
        """Get current pneumatic system state"""
        return {
            'storage_pressure': self.storage_pressure,
            'storage_temperature': self.storage_temperature,
            'compressor_power': self.compressor_power,
            'injection_power': self.injection_power,
            'total_energy': self.total_energy,
            'h2_enabled': self.h2_enabled,
            'h2_effect': self.h2_effect
        }
    
    def set_h2_enabled(self, enabled: bool) -> None:
        """Enable/disable H2 enhancement"""
        self.h2_enabled = enabled
        if not enabled:
            self.h2_effect = 0.0
    
    def set_thermal_expansion_coeff(self, coeff: float) -> None:
        """Set thermal expansion coefficient for H2 enhancement"""
        self.thermal_expansion_coeff = coeff
    
    def inject_air(self, floater: Any) -> float:
        """
        Inject air into a floater.
        
        Args:
            floater: Floater object to inject air into
            
        Returns:
            Energy required for injection
        """
        try:
            if self.storage_pressure > self.config.min_pressure:
                # Calculate base requirements
                depth_pressure = 1000.0 * 9.81 * abs(floater.position)
                volume = floater.volume
                
                # Get thermal expansion effects
                thermal_effects = self.compute_thermal_expansion(floater.position, volume)
                
                # Energy calculation considering H2
                if self.h2_enabled:
                    # Use expanded volume and reduced pressure ratio
                    volume = thermal_effects['expanded_volume']
                    pressure_ratio = thermal_effects['pressure_ratio']
                    energy = depth_pressure * volume * math.log(self.storage_pressure / depth_pressure * pressure_ratio)
                    energy -= thermal_effects['energy_saved']
                else:
                    # Standard isothermal compression energy
                    energy = depth_pressure * volume * math.log(self.storage_pressure / depth_pressure)
                
                # Update storage state
                air_mass = depth_pressure * volume / (287.05 * self.storage_temperature)
                self.air_mass -= air_mass
                self.storage_pressure = self.air_mass * 287.05 * self.storage_temperature / self.storage_volume
                
                # Update power and energy tracking
                self.injection_power = energy / 0.01  # Assume 10ms injection time
                self.total_energy += energy
                
                # Update H2 effect tracking
                if self.h2_enabled:
                    self.h2_effect = thermal_effects['energy_saved'] / energy
                
                return energy
                
            return 0.0
            
        except Exception as e:
            self.logger.error(f"Error in air injection: {e}")
            raise
    
    def get_pressure(self) -> float:
        """Get current storage pressure"""
        return self.storage_pressure
    
    def get_temperature(self) -> float:
        """Get current storage temperature"""
        return self.storage_temperature
    
    def get_power(self) -> float:
        """Get current power consumption"""
        return self.compressor_power + self.injection_power
    
    def get_energy(self) -> float:
        """Get total energy consumption"""
        return self.total_energy
    
    def vent_air(self, floater: Any) -> None:
        """
        Vent air from a floater.
        
        Args:
            floater: Floater object to vent air from
        """
        try:
            # Venting is essentially free - air is released to atmosphere
            # No energy input required, but we track the event
            if floater.is_buoyant:
                # Air is released to atmosphere
                # No energy calculation needed for venting
                pass
                
        except Exception as e:
            self.logger.error(f"Error in air venting: {e}")
            raise

