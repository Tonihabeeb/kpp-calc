"""
Pressure expansion physics for pneumatic floater system.

This module handles:
- Gas expansion models (isothermal vs adiabatic)
- Pressure equalization during ascent
- Volume changes and buoyancy effects
- Gas dissolution/release in water (Henry's law)

Phase 3 of pneumatics upgrade implementation.
"""

import math
import logging
from typing import Tuple, Dict, Optional
from config.config import G, RHO_WATER

logger = logging.getLogger(__name__)

class PressureExpansionPhysics:
    """
    Handles pressure and volume changes for air-filled floaters during ascent.
    
    Key Physics:
    - Boyle's Law for isothermal expansion: P1*V1 = P2*V2
    - Adiabatic expansion: P1*V1^γ = P2*V2^γ 
    - Henry's Law for gas dissolution: C = k_H * P_gas
    - Pressure-depth relationship: P = P_atm + ρ*g*h
    """
    
    def __init__(self):
        """Initialize pressure expansion physics parameters."""
        # Standard atmospheric pressure (Pa)
        self.P_atm = 101325.0
        
        # Adiabatic index for air (dimensionless)
        self.gamma_air = 1.4
        
        # Henry's law constant for air in water at 20°C (mol/(L·atm))
        # Typical value for air dissolution
        self.henry_constant_air = 8.7e-4  # mol/(L·atm)
        
        # Water temperature (K) - affects dissolution
        self.water_temp = 293.15  # 20°C
        
        # Gas dissolution rate constants (1/s)
        self.dissolution_rate = 0.01  # Rate of air dissolving into water
        self.release_rate = 0.05      # Rate of dissolved air being released
        
        # Maximum dissolved air fraction
        self.max_dissolution_fraction = 0.15  # 15% of air can dissolve
        
    def get_pressure_at_depth(self, depth: float) -> float:
        """
        Calculate absolute pressure at given depth.
        
        Args:
            depth (float): Depth below water surface (m)
            
        Returns:
            float: Absolute pressure (Pa)
        """
        return self.P_atm + RHO_WATER * G * depth
    
    def get_depth_from_position(self, position: float, tank_height: float = 10.0) -> float:
        """
        Convert floater position to depth below surface.
        
        Args:
            position (float): Floater position from bottom (m)
            tank_height (float): Total tank height (m)
            
        Returns:
            float: Depth below surface (m)
        """
        return max(0.0, tank_height - position)
    
    def isothermal_expansion(self, 
                           initial_pressure: float, 
                           initial_volume: float,
                           final_pressure: float) -> float:
        """
        Calculate final volume using isothermal expansion (Boyle's Law).
        
        Args:
            initial_pressure (float): Initial pressure (Pa)
            initial_volume (float): Initial air volume (m³)
            final_pressure (float): Final pressure (Pa)
            
        Returns:
            float: Final air volume (m³)
        """
        if final_pressure <= 0:
            logger.warning(f"Invalid final pressure: {final_pressure}")
            return initial_volume
            
        final_volume = initial_volume * (initial_pressure / final_pressure)
        
        logger.debug(f"Isothermal expansion: P1={initial_pressure:.0f} Pa, "
                    f"V1={initial_volume:.6f} m³ → P2={final_pressure:.0f} Pa, "
                    f"V2={final_volume:.6f} m³")
        
        return final_volume
    
    def adiabatic_expansion(self, 
                          initial_pressure: float, 
                          initial_volume: float,
                          final_pressure: float) -> float:
        """
        Calculate final volume using adiabatic expansion.
        
        For adiabatic process: P1*V1^γ = P2*V2^γ
        Therefore: V2 = V1 * (P1/P2)^(1/γ)
        
        Args:
            initial_pressure (float): Initial pressure (Pa)
            initial_volume (float): Initial air volume (m³)
            final_pressure (float): Final pressure (Pa)
            
        Returns:
            float: Final air volume (m³)
        """
        if final_pressure <= 0:
            logger.warning(f"Invalid final pressure: {final_pressure}")
            return initial_volume
            
        pressure_ratio = initial_pressure / final_pressure
        final_volume = initial_volume * (pressure_ratio ** (1.0 / self.gamma_air))
        
        logger.debug(f"Adiabatic expansion: P1={initial_pressure:.0f} Pa, "
                    f"V1={initial_volume:.6f} m³ → P2={final_pressure:.0f} Pa, "
                    f"V2={final_volume:.6f} m³")
        
        return final_volume
    
    def mixed_expansion(self, 
                       initial_pressure: float, 
                       initial_volume: float,
                       final_pressure: float,
                       isothermal_fraction: float = 0.7) -> float:
        """
        Calculate expansion using a mix of isothermal and adiabatic processes.
        
        Real gas expansion in water is often between pure isothermal and adiabatic
        due to heat transfer from surrounding water.
        
        Args:
            initial_pressure (float): Initial pressure (Pa)
            initial_volume (float): Initial air volume (m³)
            final_pressure (float): Final pressure (Pa)
            isothermal_fraction (float): Fraction of isothermal behavior (0-1)
            
        Returns:
            float: Final air volume (m³)
        """
        isothermal_vol = self.isothermal_expansion(initial_pressure, initial_volume, final_pressure)
        adiabatic_vol = self.adiabatic_expansion(initial_pressure, initial_volume, final_pressure)
        
        # Weighted average of the two expansion models
        final_volume = (isothermal_fraction * isothermal_vol + 
                       (1 - isothermal_fraction) * adiabatic_vol)
        
        logger.debug(f"Mixed expansion (f_iso={isothermal_fraction:.2f}): "
                    f"V_isothermal={isothermal_vol:.6f}, V_adiabatic={adiabatic_vol:.6f}, "
                    f"V_final={final_volume:.6f}")
        
        return final_volume
    
    def calculate_gas_dissolution(self, 
                                air_pressure: float, 
                                current_dissolved_fraction: float,
                                dt: float) -> float:
        """
        Calculate change in dissolved air fraction using Henry's Law.
        
        Henry's Law: C = k_H * P_gas
        The dissolution rate depends on pressure and current saturation.
        
        Args:
            air_pressure (float): Current air pressure in floater (Pa)
            current_dissolved_fraction (float): Current fraction of air dissolved (0-1)
            dt (float): Time step (s)
            
        Returns:
            float: New dissolved air fraction (0-1)
        """
        # Convert pressure to atm for Henry's law calculation
        pressure_atm = air_pressure / self.P_atm        # Calculate equilibrium dissolved fraction based on pressure
        # Higher pressure → more dissolution, up to maximum
        # Henry's Law: dissolved concentration proportional to pressure
        pressure_atm = air_pressure / self.P_atm
        
        # Base equilibrium at 1 atm - start with small amount
        base_equilibrium = 0.01  # 1% at 1 atm
        
        # Scale with pressure (higher pressure = more dissolution)
        equilibrium_fraction = min(self.max_dissolution_fraction, 
                                 base_equilibrium * pressure_atm)
        
        # Rate of change towards equilibrium
        if current_dissolved_fraction < equilibrium_fraction:
            # Dissolving air into water
            delta = (equilibrium_fraction - current_dissolved_fraction) * self.dissolution_rate * dt
        else:
            # Releasing dissolved air (slower rate)
            delta = (equilibrium_fraction - current_dissolved_fraction) * (self.release_rate * 0.8) * dt
        
        new_fraction = max(0.0, min(self.max_dissolution_fraction, 
                                   current_dissolved_fraction + delta))
        
        if abs(delta) > 1e-6:
            logger.debug(f"Gas dissolution: P={pressure_atm:.2f} atm, "
                        f"dissolved: {current_dissolved_fraction:.4f} → {new_fraction:.4f}")
        
        return new_fraction
    
    def calculate_effective_air_volume(self, 
                                     nominal_air_volume: float,
                                     dissolved_fraction: float) -> float:
        """
        Calculate effective air volume accounting for dissolution.
        
        Args:
            nominal_air_volume (float): Nominal air volume injected (m³)
            dissolved_fraction (float): Fraction of air dissolved in water (0-1)
            
        Returns:
            float: Effective air volume providing buoyancy (m³)
        """
        effective_volume = nominal_air_volume * (1.0 - dissolved_fraction)
        return max(0.0, effective_volume)
    
    def get_expansion_state(self, 
                          initial_depth: float,
                          current_depth: float,
                          initial_air_volume: float,
                          expansion_mode: str = "mixed") -> Dict[str, float]:
        """
        Calculate complete expansion state for air volume during ascent.
        
        Args:
            initial_depth (float): Initial depth when air was injected (m)
            current_depth (float): Current depth (m)
            initial_air_volume (float): Initial air volume at injection (m³)
            expansion_mode (str): "isothermal", "adiabatic", or "mixed"
            
        Returns:
            Dict with expansion state information
        """
        # Calculate pressures
        initial_pressure = self.get_pressure_at_depth(initial_depth)
        current_pressure = self.get_pressure_at_depth(current_depth)
        
        # Calculate expanded volume based on mode
        if expansion_mode == "isothermal":
            expanded_volume = self.isothermal_expansion(initial_pressure, initial_air_volume, current_pressure)
        elif expansion_mode == "adiabatic":
            expanded_volume = self.adiabatic_expansion(initial_pressure, initial_air_volume, current_pressure)
        else:  # mixed
            expanded_volume = self.mixed_expansion(initial_pressure, initial_air_volume, current_pressure)
        
        # Calculate expansion ratio
        expansion_ratio = expanded_volume / initial_air_volume if initial_air_volume > 0 else 1.0
        
        return {
            'initial_pressure': initial_pressure,
            'current_pressure': current_pressure,
            'initial_volume': initial_air_volume,
            'expanded_volume': expanded_volume,
            'expansion_ratio': expansion_ratio,
            'pressure_drop': initial_pressure - current_pressure,
            'volume_gain': expanded_volume - initial_air_volume
        }

    def calculate_buoyancy_from_expansion(self, 
                                        floater_total_volume: float,
                                        effective_air_volume: float) -> float:
        """
        Calculate buoyant force based on effective air displacement.
        
        Args:
            floater_total_volume (float): Total floater volume (m³)
            effective_air_volume (float): Volume of air providing buoyancy (m³)
            
        Returns:
            float: Buoyant force (N)
        """
        # Buoyancy is based on volume of water displaced by air
        displaced_volume = min(effective_air_volume, floater_total_volume)
        buoyant_force = RHO_WATER * G * displaced_volume
        
        logger.debug(f"Buoyancy calculation: air_vol={effective_air_volume:.6f} m³, "
                    f"displaced_vol={displaced_volume:.6f} m³, F_buoy={buoyant_force:.2f} N")
        
        return buoyant_force
