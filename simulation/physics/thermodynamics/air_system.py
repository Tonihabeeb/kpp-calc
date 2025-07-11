"""
Air thermodynamics using CoolProp for accurate property calculations.
"""

import numpy as np
from typing import Dict, Any, Optional
import CoolProp.CoolProp as CP

class AirThermodynamics:
    """Air thermodynamics calculator using CoolProp"""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize air thermodynamics"""
        self.config = config
        
        # Reference conditions
        self.air_reference_temp = config.get('air_reference_temp', 293.15)  # K
        self.air_reference_pressure = config.get('air_reference_pressure', 101325.0)  # Pa
        
        # H2 enhancement settings
        self.h2_thermal_expansion_coeff = config.get('h2_thermal_expansion_coeff', 0.0034)  # /K
        self.h2_heat_transfer_coeff = config.get('h2_heat_transfer_coeff', 1000.0)  # W/m^2*K
        
        # Error handling
        self.fallback_to_constants = config.get('fallback_to_constants', True)
        
        print("AirThermodynamics initialized with CoolProp")
        
    def get_air_density(self, temperature: float, pressure: float) -> float:
        """Get air density at given temperature and pressure"""
        try:
            density = CP.PropsSI('D', 'T', temperature, 'P', pressure, 'Air')
            return density
        except Exception as e:
            print(f"CoolProp error for air density: {e}")
            if self.fallback_to_constants:
                # Ideal gas law approximation
                R = 287.1  # J/kg*K (specific gas constant for air)
                return pressure / (R * temperature)
            else:
                raise e
                
    def get_air_pressure(self, temperature: float, density: float) -> float:
        """Get air pressure at given temperature and density"""
        try:
            pressure = CP.PropsSI('P', 'T', temperature, 'D', density, 'Air')
            return pressure
        except Exception as e:
            print(f"CoolProp error for air pressure: {e}")
            if self.fallback_to_constants:
                # Ideal gas law approximation
                R = 287.1  # J/kg*K
                return density * R * temperature
            else:
                raise e
                
    def get_air_temperature(self, pressure: float, density: float) -> float:
        """Get air temperature at given pressure and density"""
        try:
            temperature = CP.PropsSI('T', 'P', pressure, 'D', density, 'Air')
            return temperature
        except Exception as e:
            print(f"CoolProp error for air temperature: {e}")
            if self.fallback_to_constants:
                # Ideal gas law approximation
                R = 287.1  # J/kg*K
                return pressure / (density * R)
            else:
                raise e
                
    def calculate_compression_work(self, initial_pressure: float, final_pressure: float,
                                 initial_temp: float, mass: float, 
                                 process_type: str = 'isothermal') -> float:
        """Calculate compression work"""
        try:
            if process_type == 'isothermal':
                # Isothermal compression work = nRT * ln(P2/P1)
                R = 287.1  # J/kg*K
                work = mass * R * initial_temp * np.log(final_pressure / initial_pressure)
            elif process_type == 'adiabatic':
                # Adiabatic compression work
                gamma = 1.4  # Specific heat ratio for air
                work = mass * R * initial_temp * (gamma / (gamma - 1)) *                        ((final_pressure / initial_pressure)**((gamma - 1) / gamma) - 1)
            else:
                raise ValueError(f"Unknown process type: {process_type}")
                
            return work
        except Exception as e:
            print(f"Error calculating compression work: {e}")
            return 0.0
            
    def calculate_expansion_work(self, initial_pressure: float, final_pressure: float,
                               initial_temp: float, mass: float,
                               process_type: str = 'isothermal') -> float:
        """Calculate expansion work"""
        # Expansion work is negative compression work
        return -self.calculate_compression_work(initial_pressure, final_pressure,
                                              initial_temp, mass, process_type)
                                              
    def calculate_h2_thermal_effect(self, air_temp: float, water_temp: float,
                                  heat_transfer_area: float, time_duration: float) -> Dict[str, float]:
        """Calculate H2 thermal effect (air heating from water)"""
        # Heat transfer from water to air
        heat_transfer_rate = self.h2_heat_transfer_coeff * heat_transfer_area * (water_temp - air_temp)
        total_heat_transferred = heat_transfer_rate * time_duration
        
        # Temperature change of air
        air_specific_heat = 1005.0  # J/kg*K
        air_mass = 1.0  # kg (assumed)
        temperature_change = total_heat_transferred / (air_mass * air_specific_heat)
        
        # New air temperature
        new_air_temp = air_temp + temperature_change
        
        # Thermal expansion effect
        expansion_factor = 1.0 + self.h2_thermal_expansion_coeff * temperature_change
        
        return {
            'heat_transferred': total_heat_transferred,
            'temperature_change': temperature_change,
            'new_temperature': new_air_temp,
            'expansion_factor': expansion_factor
        }
