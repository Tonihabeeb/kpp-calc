"""
Advanced thermodynamics module for pneumatic floater system.

This module handles:
- Compression heat management and cooling
- Expansion cooling/heating during ascent
- Thermal buoyancy boost from water heat
- Temperature-dependent gas properties
- Heat transfer between air and water

Phase 5 of pneumatics upgrade implementation.
"""

import logging
import math
from typing import Dict, Optional, Tuple

from config.config import RHO_WATER, G

logger = logging.getLogger(__name__)


class ThermodynamicProperties:
    """
    Thermodynamic properties and calculations for air and water.
    """

    def __init__(self):
        """Initialize thermodynamic constants and properties."""
        # Gas constants
        self.R_specific_air = 287.0  # J/(kg·K) - specific gas constant for air
        self.gamma_air = 1.4  # Heat capacity ratio for air
        self.cp_air = 1005.0  # J/(kg·K) - specific heat at constant pressure
        self.cv_air = 718.0  # J/(kg·K) - specific heat at constant volume

        # Water properties
        self.cp_water = 4186.0  # J/(kg·K) - specific heat of water
        self.rho_water = RHO_WATER  # kg/m³

        # Standard conditions
        self.T_standard = 293.15  # K (20°C)
        self.P_standard = 101325.0  # Pa

        # Air density at standard conditions (kg/m³)
        self.rho_air_standard = self.P_standard / (
            self.R_specific_air * self.T_standard
        )

        logger.info("ThermodynamicProperties initialized")

    def air_density(self, pressure: float, temperature: float) -> float:
        """
        Calculate air density using ideal gas law.

        Args:
            pressure: Pressure (Pa)
            temperature: Temperature (K)

        Returns:
            Air density (kg/m³)
        """
        return pressure / (self.R_specific_air * temperature)

    def air_mass_from_volume(
        self, volume: float, pressure: float, temperature: float
    ) -> float:
        """
        Calculate air mass from volume at given conditions.

        Args:
            volume: Air volume (m³)
            pressure: Pressure (Pa)
            temperature: Temperature (K)

        Returns:
            Air mass (kg)
        """
        density = self.air_density(pressure, temperature)
        return density * volume

    def air_volume_from_mass(
        self, mass: float, pressure: float, temperature: float
    ) -> float:
        """
        Calculate air volume from mass at given conditions.

        Args:
            mass: Air mass (kg)
            pressure: Pressure (Pa)
            temperature: Temperature (K)

        Returns:
            Air volume (m³)
        """
        density = self.air_density(pressure, temperature)
        return mass / density if density > 0 else 0.0


class CompressionThermodynamics:
    """
    Handles thermodynamics of air compression process.
    """

    def __init__(self):
        """Initialize compression thermodynamics."""
        self.props = ThermodynamicProperties()

        # Compression parameters
        self.compression_efficiency = 0.85  # Overall compression efficiency
        self.intercooling_effectiveness = 0.8  # Heat exchanger effectiveness
        self.ambient_temperature = 293.15  # K (20°C)

        # Heat transfer coefficients
        self.compressor_heat_transfer_coeff = 50.0  # W/(m²·K)
        self.intercooler_heat_transfer_coeff = 200.0  # W/(m²·K)

        logger.info("CompressionThermodynamics initialized")

    def adiabatic_compression_temperature(
        self, T_initial: float, P_initial: float, P_final: float
    ) -> float:
        """
        Calculate final temperature for adiabatic compression.

        Uses: T2 = T1 * (P2/P1)^((γ-1)/γ)

        Args:
            T_initial: Initial temperature (K)
            P_initial: Initial pressure (Pa)
            P_final: Final pressure (Pa)

        Returns:
            Final temperature (K)
        """
        if P_initial <= 0 or P_final <= 0:
            return T_initial

        pressure_ratio = P_final / P_initial
        exponent = (self.props.gamma_air - 1) / self.props.gamma_air

        T_final = T_initial * (pressure_ratio**exponent)

        logger.debug(
            f"Adiabatic compression: {T_initial:.1f}K → {T_final:.1f}K "
            f"(P: {P_initial/1000:.1f} → {P_final/1000:.1f} kPa)"
        )

        return T_final

    def isothermal_compression_work(
        self, volume_initial: float, P_initial: float, P_final: float
    ) -> float:
        """
        Calculate work required for isothermal compression.

        Uses: W = P1*V1 * ln(P2/P1)

        Args:
            volume_initial: Initial volume (m³)
            P_initial: Initial pressure (Pa)
            P_final: Final pressure (Pa)

        Returns:
            Compression work (J)
        """
        if P_initial <= 0 or P_final <= P_initial:
            return 0.0

        work = P_initial * volume_initial * math.log(P_final / P_initial)

        logger.debug(f"Isothermal compression work: {work/1000:.1f} kJ")

        return work

    def adiabatic_compression_work(
        self, volume_initial: float, P_initial: float, P_final: float, T_initial: float
    ) -> float:
        """
        Calculate work required for adiabatic compression.

        Uses: W = (P2*V2 - P1*V1) / (γ-1)

        Args:
            volume_initial: Initial volume (m³)
            P_initial: Initial pressure (Pa)
            P_final: Final pressure (Pa)
            T_initial: Initial temperature (K)

        Returns:
            Compression work (J)
        """
        if P_initial <= 0 or P_final <= P_initial:
            return 0.0

        # Calculate final temperature and volume
        T_final = self.adiabatic_compression_temperature(T_initial, P_initial, P_final)
        volume_final = volume_initial * (P_initial / P_final) * (T_final / T_initial)

        work = (P_final * volume_final - P_initial * volume_initial) / (
            self.props.gamma_air - 1
        )

        logger.debug(f"Adiabatic compression work: {work/1000:.1f} kJ")

        return work

    def compression_heat_generation(
        self, compression_work: float, efficiency: Optional[float] = None
    ) -> float:
        """
        Calculate heat generated during compression.

        Args:
            compression_work: Work input for compression (J)
            efficiency: Compression efficiency (optional)

        Returns:
            Heat generated (J)
        """
        if efficiency is None:
            efficiency = self.compression_efficiency

        # Heat generated = input energy - useful work stored
        # Useful work = theoretical work, input energy = theoretical work / efficiency
        input_energy = compression_work / efficiency
        heat_generated = input_energy - compression_work

        logger.debug(
            f"Compression heat: {heat_generated/1000:.1f} kJ "
            f"(efficiency: {efficiency:.1%})"
        )

        return heat_generated

    def intercooling_temperature_drop(
        self, T_hot: float, heat_removed: float, air_mass: float
    ) -> float:
        """
        Calculate temperature drop due to intercooling.

        Args:
            T_hot: Initial hot air temperature (K)
            heat_removed: Heat removed by cooling (J)
            air_mass: Mass of air being cooled (kg)

        Returns:
            Final temperature after cooling (K)
        """
        if air_mass <= 0:
            return T_hot

        # ΔT = Q / (m * cp)
        temperature_drop = heat_removed / (air_mass * self.props.cp_air)
        T_final = max(self.ambient_temperature, T_hot - temperature_drop)

        logger.debug(
            f"Intercooling: {T_hot:.1f}K → {T_final:.1f}K "
            f"(heat removed: {heat_removed/1000:.1f} kJ)"
        )

        return T_final


class ExpansionThermodynamics:
    """
    Handles thermodynamics of air expansion during ascent.
    """

    def __init__(self, water_temperature: float = 293.15):
        """
        Initialize expansion thermodynamics.

        Args:
            water_temperature: Water temperature (K)
        """
        self.props = ThermodynamicProperties()
        self.water_temperature = water_temperature

        # Heat transfer parameters
        self.heat_transfer_coefficient = 100.0  # W/(m²·K) - air to water
        self.floater_surface_area = 0.5  # m² - approximate floater surface area

        # Expansion modes
        self.expansion_modes = {
            "adiabatic": self._adiabatic_expansion,
            "isothermal": self._isothermal_expansion,
            "mixed": self._mixed_expansion,
        }

        logger.info(
            f"ExpansionThermodynamics initialized (water temp: {water_temperature:.1f}K)"
        )

    def _adiabatic_expansion(
        self, volume_initial: float, P_initial: float, P_final: float, T_initial: float
    ) -> Tuple[float, float]:
        """
        Calculate adiabatic expansion (no heat transfer).

        Returns:
            Tuple of (final_volume, final_temperature)
        """
        if P_initial <= 0 or P_final <= 0:
            return volume_initial, T_initial

        # T2 = T1 * (P2/P1)^((γ-1)/γ)
        pressure_ratio = P_final / P_initial
        exponent = (self.props.gamma_air - 1) / self.props.gamma_air
        T_final = T_initial * (pressure_ratio**exponent)

        # V2 = V1 * (P1/P2) * (T2/T1)
        volume_final = volume_initial * (P_initial / P_final) * (T_final / T_initial)

        return volume_final, T_final

    def _isothermal_expansion(
        self, volume_initial: float, P_initial: float, P_final: float, T_initial: float
    ) -> Tuple[float, float]:
        """
        Calculate isothermal expansion (constant temperature).

        Returns:
            Tuple of (final_volume, final_temperature)
        """
        if P_initial <= 0 or P_final <= 0:
            return volume_initial, T_initial

        # T2 = T1 (constant temperature)
        T_final = T_initial

        # V2 = V1 * (P1/P2)
        volume_final = volume_initial * (P_initial / P_final)

        return volume_final, T_final

    def _mixed_expansion(
        self,
        volume_initial: float,
        P_initial: float,
        P_final: float,
        T_initial: float,
        heat_transfer_rate: float = 0.5,
    ) -> Tuple[float, float]:
        """
        Calculate mixed expansion (partial heat transfer).

        Args:
            heat_transfer_rate: Rate of heat transfer (0=adiabatic, 1=isothermal)

        Returns:
            Tuple of (final_volume, final_temperature)
        """
        # Calculate both extremes
        V_adiabatic, T_adiabatic = self._adiabatic_expansion(
            volume_initial, P_initial, P_final, T_initial
        )
        V_isothermal, T_isothermal = self._isothermal_expansion(
            volume_initial, P_initial, P_final, T_initial
        )

        # Interpolate based on heat transfer rate
        V_final = V_adiabatic + heat_transfer_rate * (V_isothermal - V_adiabatic)
        T_final = T_adiabatic + heat_transfer_rate * (T_isothermal - T_adiabatic)

        return V_final, T_final

    def expansion_with_heat_transfer(
        self,
        volume_initial: float,
        P_initial: float,
        P_final: float,
        T_initial: float,
        expansion_mode: str = "mixed",
        expansion_time: float = 10.0,
    ) -> Dict:
        """
        Calculate expansion with heat transfer from water.

        Args:
            volume_initial: Initial air volume (m³)
            P_initial: Initial pressure (Pa)
            P_final: Final pressure (Pa)
            T_initial: Initial temperature (K)
            expansion_mode: Type of expansion ('adiabatic', 'isothermal', 'mixed')
            expansion_time: Time for expansion process (s)

        Returns:
            Dictionary with expansion results
        """
        if expansion_mode not in self.expansion_modes:
            logger.warning(f"Unknown expansion mode: {expansion_mode}, using 'mixed'")
            expansion_mode = "mixed"

        # Calculate expansion
        if expansion_mode == "mixed":
            # Calculate heat transfer rate based on time and surface area
            heat_transfer_rate = min(
                1.0, expansion_time / 20.0
            )  # Full heat transfer in 20s
            volume_final, T_final = self._mixed_expansion(
                volume_initial, P_initial, P_final, T_initial, heat_transfer_rate
            )
        else:
            volume_final, T_final = self.expansion_modes[expansion_mode](
                volume_initial, P_initial, P_final, T_initial
            )

        # Calculate heat transfer from water
        temperature_difference = self.water_temperature - T_final
        heat_transfer_area = self.floater_surface_area
        heat_transfer = (
            self.heat_transfer_coefficient
            * heat_transfer_area
            * temperature_difference
            * expansion_time
        )

        # Adjust final temperature based on heat transfer
        air_mass = self.props.air_mass_from_volume(volume_initial, P_initial, T_initial)
        if air_mass > 0 and heat_transfer > 0:
            temperature_rise = heat_transfer / (air_mass * self.props.cp_air)
            T_final = min(self.water_temperature, T_final + temperature_rise)

            # Recalculate volume with adjusted temperature
            volume_final = (
                volume_initial * (P_initial / P_final) * (T_final / T_initial)
            )

        # Calculate thermal energy boost
        thermal_energy_boost = heat_transfer if heat_transfer > 0 else 0.0

        results = {
            "initial_volume": volume_initial,
            "final_volume": volume_final,
            "initial_temperature": T_initial,
            "final_temperature": T_final,
            "initial_pressure": P_initial,
            "final_pressure": P_final,
            "expansion_ratio": (
                volume_final / volume_initial if volume_initial > 0 else 1.0
            ),
            "heat_transfer": heat_transfer,
            "thermal_energy_boost": thermal_energy_boost,
            "air_mass": air_mass,
            "expansion_mode": expansion_mode,
        }

        logger.debug(
            f"Expansion ({expansion_mode}): "
            f"{volume_initial*1000:.1f}L → {volume_final*1000:.1f}L, "
            f"{T_initial:.1f}K → {T_final:.1f}K, "
            f"thermal boost: {thermal_energy_boost/1000:.1f} kJ"
        )

        return results


class ThermalBuoyancyCalculator:
    """
    Calculates thermal buoyancy boost from heat transfer.
    """

    def __init__(self):
        """Initialize thermal buoyancy calculator."""
        self.props = ThermodynamicProperties()

        logger.info("ThermalBuoyancyCalculator initialized")

    def thermal_buoyancy_boost(
        self, base_buoyant_force: float, thermal_expansion_results: Dict
    ) -> Dict:
        """
        Calculate additional buoyant force from thermal expansion.

        Args:
            base_buoyant_force: Base buoyant force without thermal effects (N)
            thermal_expansion_results: Results from expansion calculation

        Returns:
            Dictionary with thermal buoyancy results
        """
        # Extract expansion data
        volume_initial = thermal_expansion_results["initial_volume"]
        volume_final = thermal_expansion_results["final_volume"]
        thermal_energy = thermal_expansion_results["thermal_energy_boost"]

        # Additional displaced volume due to thermal expansion
        thermal_volume_increase = volume_final - volume_initial

        # Additional buoyant force from thermal expansion
        thermal_buoyant_force = RHO_WATER * G * thermal_volume_increase

        # Total buoyant force
        total_buoyant_force = base_buoyant_force + thermal_buoyant_force

        # Thermal boost percentage
        if base_buoyant_force > 0:
            thermal_boost_percentage = (
                thermal_buoyant_force / base_buoyant_force
            ) * 100
        else:
            thermal_boost_percentage = 0.0

        results = {
            "base_buoyant_force": base_buoyant_force,
            "thermal_buoyant_force": thermal_buoyant_force,
            "total_buoyant_force": total_buoyant_force,
            "thermal_volume_increase": thermal_volume_increase,
            "thermal_energy_boost": thermal_energy,
            "thermal_boost_percentage": thermal_boost_percentage,
        }

        logger.debug(
            f"Thermal buoyancy boost: {thermal_buoyant_force:.1f}N "
            f"({thermal_boost_percentage:.1f}% increase)"
        )

        return results

    def thermal_efficiency_factor(
        self, thermal_energy_input: float, mechanical_work_output: float
    ) -> float:
        """
        Calculate thermal efficiency factor for energy conversion.

        Args:
            thermal_energy_input: Thermal energy from heat transfer (J)
            mechanical_work_output: Mechanical work from thermal buoyancy (J)

        Returns:
            Thermal efficiency factor (dimensionless)
        """
        if thermal_energy_input <= 0:
            return 0.0

        efficiency = mechanical_work_output / thermal_energy_input

        logger.debug(
            f"Thermal efficiency: {efficiency:.1%} "
            f"({mechanical_work_output/1000:.1f} kJ / {thermal_energy_input/1000:.1f} kJ)"
        )

        return efficiency


class AdvancedThermodynamics:
    """
    Main class coordinating all thermodynamic calculations.
    """

    def __init__(
        self, water_temperature: float = 293.15, expansion_mode: str = "mixed"
    ):
        """
        Initialize advanced thermodynamics system.

        Args:
            water_temperature: Water temperature (K)
            expansion_mode: Default expansion mode
        """
        self.props = ThermodynamicProperties()
        self.compression = CompressionThermodynamics()
        self.expansion = ExpansionThermodynamics(water_temperature)
        self.thermal_buoyancy = ThermalBuoyancyCalculator()

        self.water_temperature = water_temperature
        self.expansion_mode = expansion_mode

        logger.info(
            f"AdvancedThermodynamics initialized "
            f"(water: {water_temperature:.1f}K, mode: {expansion_mode})"
        )

    def complete_thermodynamic_cycle(
        self,
        initial_air_volume: float,
        injection_pressure: float,
        surface_pressure: float,
        injection_temperature: float,
        ascent_time: float,
        base_buoyant_force: float,
    ) -> Dict:
        """
        Calculate complete thermodynamic cycle for a floater.

        Args:
            initial_air_volume: Initial air volume at surface conditions (m³)
            injection_pressure: Pressure during injection (Pa)
            surface_pressure: Final pressure at surface (Pa)
            injection_temperature: Temperature during injection (K)
            ascent_time: Time for ascent (s)
            base_buoyant_force: Base buoyant force without thermal effects (N)

        Returns:
            Complete thermodynamic analysis results
        """
        # 1. Compression analysis (for reference)
        compression_work_isothermal = self.compression.isothermal_compression_work(
            initial_air_volume, surface_pressure, injection_pressure
        )
        compression_work_adiabatic = self.compression.adiabatic_compression_work(
            initial_air_volume,
            surface_pressure,
            injection_pressure,
            self.compression.ambient_temperature,
        )
        compression_heat = self.compression.compression_heat_generation(
            compression_work_adiabatic
        )

        # 2. Expansion analysis during ascent
        expansion_results = self.expansion.expansion_with_heat_transfer(
            initial_air_volume,
            injection_pressure,
            surface_pressure,
            injection_temperature,
            self.expansion_mode,
            ascent_time,
        )

        # 3. Thermal buoyancy boost
        thermal_results = self.thermal_buoyancy.thermal_buoyancy_boost(
            base_buoyant_force, expansion_results
        )

        # 4. Energy balance
        total_thermal_energy = expansion_results["thermal_energy_boost"]
        thermal_work_output = (
            thermal_results["thermal_buoyant_force"] * 10.0
        )  # Assume 10m ascent
        thermal_efficiency = self.thermal_buoyancy.thermal_efficiency_factor(
            total_thermal_energy, thermal_work_output
        )

        # 5. Complete results
        complete_results = {
            "compression": {
                "isothermal_work": compression_work_isothermal,
                "adiabatic_work": compression_work_adiabatic,
                "heat_generated": compression_heat,
            },
            "expansion": expansion_results,
            "thermal_buoyancy": thermal_results,
            "energy_balance": {
                "thermal_energy_input": total_thermal_energy,
                "thermal_work_output": thermal_work_output,
                "thermal_efficiency": thermal_efficiency,
            },
            "performance_metrics": {
                "volume_expansion_ratio": expansion_results["expansion_ratio"],
                "thermal_boost_percentage": thermal_results["thermal_boost_percentage"],
                "total_buoyant_force": thermal_results["total_buoyant_force"],
            },
        }

        logger.info(
            f"Complete thermodynamic cycle: "
            f"volume ratio {expansion_results['expansion_ratio']:.2f}, "
            f"thermal boost {thermal_results['thermal_boost_percentage']:.1f}%"
        )

        return complete_results

    def update_water_temperature(self, new_temperature: float):
        """Update water temperature for all calculations."""
        self.water_temperature = new_temperature
        self.expansion.water_temperature = new_temperature
        logger.info(f"Water temperature updated to {new_temperature:.1f}K")

    def update_expansion_mode(self, new_mode: str):
        """Update expansion mode."""
        if new_mode in self.expansion.expansion_modes:
            self.expansion_mode = new_mode
            logger.info(f"Expansion mode updated to {new_mode}")
        else:
            logger.warning(f"Invalid expansion mode: {new_mode}")

    def analyze_complete_cycle(
        self,
        initial_volume: float,
        injection_pressure: float,
        surface_pressure: float,
        injection_temperature: float,
        ascent_time: float,
        base_buoyant_force: float,
    ) -> Dict:
        """
        Analyze complete thermodynamic cycle - alias for complete_thermodynamic_cycle.

        This method provides compatibility for demo files that expect this method name.
        """
        return self.complete_thermodynamic_cycle(
            initial_volume,
            injection_pressure,
            surface_pressure,
            injection_temperature,
            ascent_time,
            base_buoyant_force,
        )
