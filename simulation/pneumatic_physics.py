"""
Physics Integration Module for KPP Pneumatic System

This module provides physics calculations and property functions that integrate
pneumatic system calculations with the main simulation physics.

Key Features:
- Pneumatic force calculations
- Thermodynamic property functions  
- Gas law implementations
- Heat transfer calculations
- Integration with existing KPP physics
"""

import math
import logging
from typing import Dict, Tuple, Optional, Any
from config.config import G, RHO_WATER, RHO_AIR

# Import pneumatic physics modules
from simulation.pneumatics.thermodynamics import AdvancedThermodynamics
from simulation.pneumatics.heat_exchange import IntegratedHeatExchange
from simulation.pneumatics.pressure_expansion import PressureExpansionPhysics

logger = logging.getLogger(__name__)


class KPPPhysicsCalculator:
    """
    Integrated physics calculator for KPP system with pneumatic enhancement.
    
    Combines traditional KPP physics with advanced pneumatic system calculations.
    """
    
    def __init__(self):
        """Initialize the physics calculator with pneumatic integration."""
        self.thermodynamics = AdvancedThermodynamics()
        self.heat_exchange = IntegratedHeatExchange()
        self.pressure_expansion = PressureExpansionPhysics()
        
        # Standard conditions
        self.standard_pressure = 101325.0  # Pa
        self.standard_temperature = 293.15  # K (20°C)
        
        logger.info("KPP Physics Calculator initialized with pneumatic integration")
    
    def calculate_pneumatic_force_contribution(self, 
                                             floater_volume: float,
                                             air_fill_fraction: float,
                                             depth: float,
                                             air_pressure: Optional[float] = None) -> Dict[str, float]:
        """
        Calculate the force contribution from pneumatic system.
        
        Args:
            floater_volume: Total floater volume (m³)
            air_fill_fraction: Fraction of volume filled with air (0-1)
            depth: Current depth below surface (m)
            air_pressure: Air pressure inside floater (Pa), if None calculate from depth
            
        Returns:
            Dictionary with force components
        """
        if air_pressure is None:
            # Calculate pressure based on depth (hydrostatic + atmospheric)
            air_pressure = self.standard_pressure + RHO_WATER * G * depth
        
        # Volume of air inside floater
        air_volume = floater_volume * air_fill_fraction
        
        # Volume of displaced water (due to air presence)
        displaced_volume = air_volume
        
        # Buoyant force from displaced water
        buoyant_force = displaced_volume * RHO_WATER * G
        
        # Additional force from pressure difference (if any)
        pressure_force = 0.0
        if air_pressure > self.standard_pressure + RHO_WATER * G * depth:
            # Overpressure contributes to additional force
            pressure_diff = air_pressure - (self.standard_pressure + RHO_WATER * G * depth)
            # Approximate effective area (bottom of floater)
            effective_area = (3 * floater_volume / (4 * math.pi)) ** (2/3) * math.pi
            pressure_force = pressure_diff * effective_area
        
        return {
            'buoyant_force': buoyant_force,
            'pressure_force': pressure_force,
            'total_pneumatic_force': buoyant_force + pressure_force,
            'displaced_volume': displaced_volume,
            'air_volume': air_volume
        }
    
    def calculate_thermodynamic_properties(self,
                                         pressure: float,
                                         temperature: float,
                                         volume: float) -> Dict[str, float]:
        """
        Calculate thermodynamic properties of air at given conditions.
        
        Args:
            pressure: Air pressure (Pa)
            temperature: Air temperature (K)
            volume: Air volume (m³)
            
        Returns:
            Dictionary with thermodynamic properties
        """
        # Gas constant for air
        R_air = 287.0  # J/kg·K
        
        # Air density from ideal gas law
        air_density = pressure / (R_air * temperature)
        
        # Air mass
        air_mass = air_density * volume
        
        # Internal energy (for monatomic gas, adjust for air)
        cv_air = 718.0  # J/kg·K (specific heat at constant volume)
        internal_energy = air_mass * cv_air * temperature
        
        # Enthalpy
        cp_air = 1005.0  # J/kg·K (specific heat at constant pressure)
        enthalpy = air_mass * cp_air * temperature
        
        return {
            'density': air_density,
            'mass': air_mass,
            'internal_energy': internal_energy,
            'enthalpy': enthalpy,
            'specific_heat_cp': cp_air,
            'specific_heat_cv': cv_air
        }
    
    def calculate_gas_expansion_work(self,
                                   initial_pressure: float,
                                   final_pressure: float,
                                   volume: float,
                                   process_type: str = 'isothermal') -> Dict[str, Any]:
        """
        Calculate work done during gas expansion.
        
        Args:
            initial_pressure: Initial pressure (Pa)
            final_pressure: Final pressure (Pa)
            volume: Gas volume (m³)
            process_type: 'isothermal', 'adiabatic', or 'polytropic'
            
        Returns:
            Dictionary with work calculations
        """
        if process_type == 'isothermal':
            # Isothermal expansion: W = nRT * ln(Vf/Vi) = P1*V1 * ln(P1/P2)
            work_done = initial_pressure * volume * math.log(initial_pressure / final_pressure)
            
        elif process_type == 'adiabatic':
            # Adiabatic expansion: W = (P1*V1 - P2*V2) / (γ-1)
            gamma = 1.4  # Heat capacity ratio for air
            final_volume = volume * (initial_pressure / final_pressure) ** (1/gamma)
            work_done = (initial_pressure * volume - final_pressure * final_volume) / (gamma - 1)
            
        else:  # polytropic with n = 1.2 (typical for real processes)
            n = 1.2
            final_volume = volume * (initial_pressure / final_pressure) ** (1/n)
            work_done = (initial_pressure * volume - final_pressure * final_volume) / (n - 1)
        
        # Efficiency factor for real-world losses
        efficiency = 0.85 if process_type == 'isothermal' else 0.90
        useful_work = work_done * efficiency
        
        return {
            'ideal_work': work_done,
            'useful_work': useful_work,
            'efficiency': efficiency,
            'process_type': process_type
        }
    
    def calculate_heat_transfer(self,
                              air_temperature: float,
                              water_temperature: float,
                              surface_area: float,
                              heat_transfer_coefficient: float = 150.0,
                              time_duration: float = 1.0) -> Dict[str, Any]:
        """
        Calculate heat transfer between air and water.
        
        Args:
            air_temperature: Temperature of air (K)
            water_temperature: Temperature of water (K)
            surface_area: Air-water interface area (m²)
            heat_transfer_coefficient: Heat transfer coefficient (W/m²K)
            time_duration: Duration of heat transfer (s)
            
        Returns:
            Dictionary with heat transfer calculations
        """
        # Temperature difference
        temp_difference = air_temperature - water_temperature
        
        # Heat transfer rate (W)
        heat_transfer_rate = heat_transfer_coefficient * surface_area * temp_difference
        
        # Total heat transferred
        heat_transferred = heat_transfer_rate * time_duration
        
        # Direction of heat transfer
        heat_direction = "air_to_water" if temp_difference > 0 else "water_to_air"
        
        return {
            'heat_transfer_rate': abs(heat_transfer_rate),
            'heat_transferred': abs(heat_transferred),
            'temperature_difference': temp_difference,
            'heat_direction': heat_direction,
            'heat_transfer_coefficient': heat_transfer_coefficient
        }
    
    def calculate_pneumatic_power(self,
                                volume_flow_rate: float,
                                pressure_rise: float,
                                compressor_efficiency: float = 0.85) -> Dict[str, float]:
        """
        Calculate pneumatic power requirements.
        
        Args:
            volume_flow_rate: Air volume flow rate (m³/s)
            pressure_rise: Pressure increase (Pa)
            compressor_efficiency: Compressor efficiency (0-1)
            
        Returns:
            Dictionary with power calculations
        """
        # Ideal power required (isothermal compression)
        ideal_power = volume_flow_rate * pressure_rise
        
        # Actual power including inefficiencies
        actual_power = ideal_power / compressor_efficiency
        
        # Heat generation rate
        heat_generation_rate = actual_power - ideal_power
        
        return {
            'ideal_power': ideal_power,
            'actual_power': actual_power,
            'compressor_efficiency': compressor_efficiency,
            'heat_generation_rate': heat_generation_rate
        }
    
    def validate_energy_conservation(self,
                                   energy_inputs: Dict[str, float],
                                   energy_outputs: Dict[str, float],
                                   tolerance: float = 0.05) -> Dict[str, Any]:
        """
        Validate energy conservation in pneumatic calculations.
        
        Args:
            energy_inputs: Dictionary of energy inputs (J)
            energy_outputs: Dictionary of energy outputs (J)
            tolerance: Acceptable energy balance error (fraction)
            
        Returns:
            Dictionary with validation results
        """
        total_input = sum(energy_inputs.values())
        total_output = sum(energy_outputs.values())
        
        energy_balance = total_input - total_output
        relative_error = abs(energy_balance) / total_input if total_input > 0 else 0.0
        
        conservation_valid = relative_error <= tolerance
        
        return {
            'total_input': total_input,
            'total_output': total_output,
            'energy_balance': energy_balance,
            'relative_error': relative_error,
            'conservation_valid': conservation_valid,
            'tolerance': tolerance,
            'energy_inputs': energy_inputs,
            'energy_outputs': energy_outputs
        }


# Factory function for easy integration
def create_kpp_physics_calculator() -> KPPPhysicsCalculator:
    """
    Create a standard KPP physics calculator with pneumatic integration.
    
    Returns:
        Configured KPPPhysicsCalculator instance
    """
    return KPPPhysicsCalculator()


# Convenience functions for common calculations
def calculate_buoyant_force(volume: float, depth: float = 0.0) -> float:
    """
    Calculate buoyant force for a given volume at depth.
    
    Args:
        volume: Displaced volume (m³)
        depth: Depth below surface (m)
        
    Returns:
        Buoyant force (N)
    """
    return volume * RHO_WATER * G


def calculate_hydrostatic_pressure(depth: float) -> float:
    """
    Calculate hydrostatic pressure at given depth.
    
    Args:
        depth: Depth below surface (m)
        
    Returns:
        Hydrostatic pressure (Pa)
    """
    return 101325.0 + RHO_WATER * G * depth


def calculate_air_mass(volume: float, pressure: float, temperature: float) -> float:
    """
    Calculate air mass from volume, pressure, and temperature.
    
    Args:
        volume: Air volume (m³)
        pressure: Air pressure (Pa)
        temperature: Air temperature (K)
        
    Returns:
        Air mass (kg)
    """
    R_air = 287.0  # J/kg·K
    density = pressure / (R_air * temperature)
    return density * volume
