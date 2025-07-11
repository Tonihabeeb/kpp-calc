"""
H2 Enhancement: Thermal effects for improved buoyancy.
"""

import numpy as np
from typing import Dict, Any

class H2Enhancement:
    """H2 Enhancement: Thermal effects on air buoyancy"""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize H2 enhancement"""
        self.config = config
        
        # H2 parameters
        self.thermal_expansion_coeff = config.get('h2_thermal_expansion_coeff', 0.0034)  # /K
        self.heat_transfer_coeff = config.get('h2_heat_transfer_coeff', 1000.0)  # W/m^2*K
        self.water_temperature = config.get('water_temperature', 293.15)  # K
        
        # Enhancement state
        self.enabled = False
        self.heat_transfer_area = 1.0  # m^2 (assumed)
        
        print("H2 Enhancement initialized")
        
    def enable(self) -> None:
        """Enable H2 enhancement"""
        self.enabled = True
        print("H2 Enhancement enabled")
        
    def disable(self) -> None:
        """Disable H2 enhancement"""
        self.enabled = False
        print("H2 Enhancement disabled")
        
    def calculate_thermal_buoyancy_boost(self, air_temperature: float, 
                                       air_mass: float, time_duration: float) -> Dict[str, float]:
        """Calculate thermal buoyancy boost from H2 enhancement"""
        if not self.enabled:
            return {
                'buoyancy_boost': 0.0,
                'temperature_increase': 0.0,
                'volume_expansion': 1.0
            }
            
        # Heat transfer from water to air
        heat_transfer_rate = self.heat_transfer_coeff * self.heat_transfer_area * (self.water_temperature - air_temperature)
        total_heat_transferred = heat_transfer_rate * time_duration
        
        # Temperature change of air
        air_specific_heat = 1005.0  # J/kg*K
        temperature_increase = total_heat_transferred / (air_mass * air_specific_heat)
        new_air_temperature = air_temperature + temperature_increase
        
        # Thermal expansion
        volume_expansion = 1.0 + self.thermal_expansion_coeff * temperature_increase
        
        # Buoyancy boost (additional buoyant force)
        # Simplified calculation - in practice would use actual density changes
        buoyancy_boost_factor = volume_expansion - 1.0
        
        return {
            'buoyancy_boost': buoyancy_boost_factor,
            'temperature_increase': temperature_increase,
            'volume_expansion': volume_expansion,
            'new_temperature': new_air_temperature
        }
        
    def apply_thermal_effects(self, floater_state: Dict[str, Any], 
                            time_duration: float) -> Dict[str, Any]:
        """Apply thermal effects to a floater state"""
        if not self.enabled:
            return floater_state.copy()
            
        # Calculate thermal effects
        thermal_effects = self.calculate_thermal_buoyancy_boost(
            floater_state['air_temperature'],
            floater_state['air_mass'],
            time_duration
        )
        
        # Update floater state
        updated_state = floater_state.copy()
        updated_state['air_temperature'] = thermal_effects['new_temperature']
        updated_state['h2_thermal_boost'] = thermal_effects['buoyancy_boost']
        updated_state['h2_volume_expansion'] = thermal_effects['volume_expansion']
        
        return updated_state
        
    def get_enhancement_factor(self, air_temperature: float, time_duration: float) -> float:
        """Get H2 enhancement factor"""
        if not self.enabled:
            return 1.0
            
        # Calculate enhancement factor based on thermal effects
        thermal_effects = self.calculate_thermal_buoyancy_boost(
            air_temperature, 1.0, time_duration  # Assume 1 kg of air
        )
        
        return thermal_effects['volume_expansion']
        
    def get_status(self) -> Dict[str, Any]:
        """Get H2 enhancement status"""
        return {
            'enabled': self.enabled,
            'thermal_expansion_coeff': self.thermal_expansion_coeff,
            'heat_transfer_coeff': self.heat_transfer_coeff,
            'water_temperature': self.water_temperature,
            'heat_transfer_area': self.heat_transfer_area
        }
