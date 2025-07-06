"""
Thermal Modeling Module for KPP Simulation
Handles thermal effects, H2 isothermal expansion, and temperature-dependent properties.
"""

import logging
import math
from dataclasses import dataclass
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


@dataclass
class ThermalState:
    """Current thermal state of the system"""

    water_temperature: float = 293.15  # K
    air_temperature: float = 293.15  # K
    thermal_expansion_rate: float = 0.0  # 1/K
    buoyancy_enhancement: float = 0.0  # Fractional enhancement due to thermal effects
    compression_work_reduction: float = 0.0  # Energy reduction from thermal assistance


class ThermalModel:
    """
    Manages thermal effects in the KPP system.

    Handles:
    - H2 isothermal expansion effects
    - Temperature-dependent density calculations
    - Thermal buoyancy enhancement
    - Heat exchange with environment
    - Compression work optimization
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the thermal model.

        Args:
            config (dict): Configuration parameters
        """
        if config is None:
            config = {}

        # Base thermal properties
        self.water_temperature = config.get("water_temperature", 293.15)  # K (20°C)
        self.ambient_temperature = config.get("ambient_temperature", 293.15)  # K
        self.specific_heat_air = config.get("specific_heat_air", 1005.0)  # J/(kg·K)
        self.specific_heat_water = config.get("specific_heat_water", 4186.0)  # J/(kg·K)

        # Gas properties
        self.gas_constant = 287.0  # J/(kg·K) for air
        self.gamma = 1.4  # Heat capacity ratio for air

        # H2 isothermal parameters
        self.h2_active = config.get("h2_active", False)
        self.h2_efficiency = config.get("h2_efficiency", 0.8)  # How close to ideal isothermal (0-1)
        self.h2_buoyancy_boost = config.get("h2_buoyancy_boost", 0.05)  # 5% default boost
        self.h2_compression_improvement = config.get("h2_compression_improvement", 0.15)  # 15% work reduction

        # Thermal expansion properties
        self.water_expansion_coeff = 2.1e-4  # /K
        self.air_expansion_coeff = 1 / 293.15  # Ideal gas approximation

        # Current state
        self.state = ThermalState()
        self.update_state()

        logger.info(
            f"Thermal model initialized - Water temp: {self.water_temperature:.1f} K, "
            f"H2 active: {self.h2_active}, efficiency: {self.h2_efficiency:.1%}"
        )

    def update_state(self):
        """Update the thermal state based on current conditions."""
        self.state.water_temperature = self.water_temperature
        self.state.air_temperature = self.ambient_temperature
        self.state.thermal_expansion_rate = self.water_expansion_coeff

        # Apply H2 effects if active
        if self.h2_active:
            self.state.buoyancy_enhancement = self.h2_buoyancy_boost * self.h2_efficiency
            self.state.compression_work_reduction = self.h2_compression_improvement * self.h2_efficiency
        else:
            self.state.buoyancy_enhancement = 0.0
            self.state.compression_work_reduction = 0.0

    def calculate_thermal_buoyancy_enhancement(self, base_buoyancy: float, ascent_height: float) -> float:
        """
        Calculate thermal enhancement to buoyancy force due to H2 isothermal expansion.

        In H2, air in ascending floater absorbs heat from water and expands isothermally,
        providing additional buoyancy compared to adiabatic expansion.

        Args:
            base_buoyancy (float): Base buoyant force (N)
            ascent_height (float): Height ascended (m) - affects pressure change

        Returns:
            float: Enhanced buoyant force (N)
        """
        if not self.h2_active or base_buoyancy <= 0:
            return base_buoyancy

        # Calculate pressure change during ascent
        # Assuming hydrostatic pressure: ΔP = ρ_water * g * Δh
        water_density = 1000.0  # kg/m³
        gravity = 9.81  # m/s²
        pressure_change = water_density * gravity * ascent_height

        # For isothermal expansion: P₁V₁ = P₂V₂ at constant T
        # Enhanced buoyancy from volume expansion
        if ascent_height > 0.1:  # Meaningful height change
            # Pressure ratio approximation
            pressure_ratio = 1 + pressure_change / 101325.0  # Atmospheric pressure

            # Volume expansion factor (limited to prevent unrealistic values)
            expansion_factor = min(pressure_ratio, 1.2)  # Limit to 20% expansion

            # Enhanced buoyancy with thermal efficiency
            thermal_enhancement = (expansion_factor - 1) * self.h2_efficiency
            enhanced_buoyancy = base_buoyancy * (1 + thermal_enhancement)

            logger.debug(
                f"H2 thermal enhancement: height={ascent_height:.1f}m, "
                f"expansion={expansion_factor:.3f}, enhancement={thermal_enhancement:.1%}, "
                f"buoyancy: {base_buoyancy:.1f} → {enhanced_buoyancy:.1f} N"
            )

            return enhanced_buoyancy

        # Apply base enhancement for small heights
        enhanced_buoyancy = base_buoyancy * (1 + self.state.buoyancy_enhancement)
        return enhanced_buoyancy

    def calculate_isothermal_compression_work(
        self, volume: float, initial_pressure: float, final_pressure: float
    ) -> float:
        """
        Calculate compression work with H2 thermal assistance.

        For isothermal compression: W = P₁V₁ ln(P₂/P₁)
        H2 reduces this work by utilizing environmental heat.

        Args:
            volume (float): Volume of air to compress (m³)
            initial_pressure (float): Initial pressure (Pa)
            final_pressure (float): Final pressure (Pa)

        Returns:
            float: Compression work (J)
        """
        if volume <= 0 or final_pressure <= initial_pressure:
            return 0.0

        # Calculate ideal isothermal work
        pressure_ratio = final_pressure / initial_pressure
        isothermal_work = initial_pressure * volume * math.log(pressure_ratio)

        # Apply H2 thermal assistance if active
        if self.h2_active:
            # H2 reduces work by utilizing environmental heat
            thermal_assistance = isothermal_work * self.state.compression_work_reduction
            effective_work = isothermal_work - thermal_assistance

            logger.debug(
                f"H2 compression work: ideal={isothermal_work:.1f} J, "
                f"thermal_assistance={thermal_assistance:.1f} J, "
                f"effective={effective_work:.1f} J "
                f"({self.state.compression_work_reduction:.1%} reduction)"
            )

            return max(effective_work, 0.1 * isothermal_work)  # Minimum 10% of ideal work
        else:
            return isothermal_work

    def calculate_adiabatic_compression_work(
        self, volume: float, initial_pressure: float, final_pressure: float
    ) -> float:
        """
        Calculate adiabatic compression work (without thermal assistance).

        For adiabatic compression: W = (P₂V₂ - P₁V₁) / (γ - 1)

        Args:
            volume (float): Initial volume of air (m³)
            initial_pressure (float): Initial pressure (Pa)
            final_pressure (float): Final pressure (Pa)

        Returns:
            float: Compression work (J)
        """
        if volume <= 0 or final_pressure <= initial_pressure:
            return 0.0

        # Calculate final volume for adiabatic process: P₁V₁^γ = P₂V₂^γ
        pressure_ratio = final_pressure / initial_pressure
        final_volume = volume * (pressure_ratio ** (-1 / self.gamma))

        # Adiabatic work
        adiabatic_work = (final_pressure * final_volume - initial_pressure * volume) / (self.gamma - 1)

        logger.debug(
            f"Adiabatic compression work: V₁={volume:.4f} m³, V₂={final_volume:.4f} m³, "
            f"P₁={initial_pressure:.0f} Pa, P₂={final_pressure:.0f} Pa, "
            f"W={adiabatic_work:.1f} J"
        )

        return adiabatic_work

    def calculate_compression_work(self, volume: float, depth: float, use_isothermal: Optional[bool] = None) -> float:
        """
        Calculate compression work for air injection at depth.

        Chooses between isothermal and adiabatic based on H2 status or explicit choice.

        Args:
            volume (float): Volume of air to compress (m³)
            depth (float): Injection depth (m)
            use_isothermal (bool, optional): Force isothermal (True) or adiabatic (False)

        Returns:
            float: Compression work (J)
        """
        if volume <= 0 or depth <= 0:
            return 0.0

        # Calculate pressures
        atmospheric_pressure = 101325.0  # Pa
        water_density = 1000.0  # kg/m³
        gravity = 9.81  # m/s²

        initial_pressure = atmospheric_pressure
        final_pressure = atmospheric_pressure + water_density * gravity * depth

        # Choose compression type
        if use_isothermal is None:
            use_isothermal = self.h2_active

        if use_isothermal:
            work = self.calculate_isothermal_compression_work(volume, initial_pressure, final_pressure)
        else:
            work = self.calculate_adiabatic_compression_work(volume, initial_pressure, final_pressure)

        logger.debug(
            f"Compression work at depth {depth:.1f}m: "
            f"{'isothermal' if use_isothermal else 'adiabatic'} = {work:.1f} J"
        )

        return work

    def calculate_thermal_density_effect(self, base_density: float, temperature_change: float) -> float:
        """
        Calculate density change due to thermal expansion.

        ρ(T) = ρ₀ * (1 - β * ΔT)

        Args:
            base_density (float): Base density at reference temperature (kg/m³)
            temperature_change (float): Temperature change from reference (K)

        Returns:
            float: Adjusted density (kg/m³)
        """
        density_change = base_density * self.water_expansion_coeff * temperature_change
        adjusted_density = base_density - density_change

        # Ensure reasonable limits
        adjusted_density = max(adjusted_density, 900.0)  # Minimum reasonable density
        adjusted_density = min(adjusted_density, 1100.0)  # Maximum reasonable density

        if abs(temperature_change) > 0.1:
            logger.debug(
                f"Thermal density effect: ΔT={temperature_change:.1f}K, "
                f"density: {base_density:.1f} → {adjusted_density:.1f} kg/m³"
            )

        return adjusted_density

    def calculate_heat_exchange_rate(
        self, air_volume: float, temperature_difference: float, surface_area: float
    ) -> float:
        """
        Calculate rate of heat exchange between air and water.

        Simplified model: Q̇ = h * A * ΔT

        Args:
            air_volume (float): Volume of air in floater (m³)
            temperature_difference (float): Temperature difference (K)
            surface_area (float): Heat exchange surface area (m²)

        Returns:
            float: Heat exchange rate (W)
        """
        if abs(temperature_difference) < 0.1:
            return 0.0

        # Simplified heat transfer coefficient for water-air interface
        heat_transfer_coeff = 500.0  # W/(m²·K) - typical for water-air

        heat_rate = heat_transfer_coeff * surface_area * temperature_difference

        logger.debug(
            f"Heat exchange: A={surface_area:.3f} m², ΔT={temperature_difference:.1f}K, " f"Q̇={heat_rate:.1f} W"
        )

        return heat_rate

    def get_thermal_properties(self) -> Dict[str, float]:
        """
        Get current thermal properties for logging/monitoring.

        Returns:
            dict: Current thermal properties
        """
        return {
            "water_temperature": self.state.water_temperature,
            "air_temperature": self.state.air_temperature,
            "thermal_expansion_rate": self.state.thermal_expansion_rate,
            "buoyancy_enhancement": self.state.buoyancy_enhancement,
            "compression_work_reduction": self.state.compression_work_reduction,
            "h2_active": self.h2_active,
            "h2_efficiency": self.h2_efficiency,
        }

    def set_h2_active(
        self,
        active: bool,
        efficiency: Optional[float] = None,
        buoyancy_boost: Optional[float] = None,
        compression_improvement: Optional[float] = None,
    ):
        """
        Enable/disable H2 isothermal effects.

        Args:
            active (bool): Whether to activate H2 effects
            efficiency (float, optional): H2 efficiency (0-1)
            buoyancy_boost (float, optional): Buoyancy enhancement factor (0-1)
            compression_improvement (float, optional): Compression work reduction (0-1)
        """
        self.h2_active = active

        if efficiency is not None:
            self.h2_efficiency = max(0.0, min(efficiency, 1.0))

        if buoyancy_boost is not None:
            self.h2_buoyancy_boost = max(0.0, min(buoyancy_boost, 0.3))  # Limit to 30%

        if compression_improvement is not None:
            self.h2_compression_improvement = max(0.0, min(compression_improvement, 0.5))  # Limit to 50%

        self.update_state()

        logger.info(
            f"H2 isothermal effects {'activated' if active else 'deactivated'}: "
            f"efficiency={self.h2_efficiency:.1%}, "
            f"buoyancy_boost={self.h2_buoyancy_boost:.1%}, "
            f"compression_improvement={self.h2_compression_improvement:.1%}"
        )

    def set_water_temperature(self, temperature: float):
        """
        Set water temperature.

        Args:
            temperature (float): Water temperature in Kelvin
        """
        self.water_temperature = max(273.15, min(temperature, 373.15))  # Limit to liquid range
        self.update_state()

        logger.info(
            f"Water temperature set to {self.water_temperature:.1f} K " f"({self.water_temperature - 273.15:.1f}°C)"
        )

    def set_ambient_temperature(self, temperature: float):
        """
        Set ambient air temperature.

        Args:
            temperature (float): Ambient temperature in Kelvin
        """
        self.ambient_temperature = max(173.15, min(temperature, 373.15))  # Reasonable range
        self.update_state()

        logger.info(
            f"Ambient temperature set to {self.ambient_temperature:.1f} K "
            f"({self.ambient_temperature - 273.15:.1f}°C)"
        )
