"""
Heat exchange modeling for pneumatic floater system.

This module handles:
- Air-water heat transfer during ascent
- Water thermal reservoir effects
- Temperature-dependent air properties
- Heat recovery from compression process

Phase 5.2 of pneumatics upgrade implementation.
"""

import logging
import math
from typing import Dict, List, Optional, Tuple

from config.config import RHO_WATER, G

logger = logging.getLogger(__name__)


class HeatTransferCoefficients:
    """
    Heat transfer coefficients for different configurations.
    """

    def __init__(self):
        """Initialize heat transfer coefficients."""
        # Natural convection coefficients (W/(m²·K))
        self.natural_convection_air = 10.0  # Air natural convection
        self.natural_convection_water = 500.0  # Water natural convection

        # Forced convection coefficients (W/(m²·K))
        self.forced_convection_air = 50.0  # Air with movement
        self.forced_convection_water = 2000.0  # Water with flow

        # Material thermal conductivities (W/(m·K))
        self.thermal_conductivity_air = 0.026  # Air at 20°C
        self.thermal_conductivity_water = 0.6  # Water at 20°C
        self.thermal_conductivity_aluminum = 205.0  # Aluminum floater walls
        self.thermal_conductivity_steel = 50.0  # Steel components

        # Wall thicknesses (m)
        self.floater_wall_thickness = 0.003  # 3mm aluminum wall
        self.pipe_wall_thickness = 0.002  # 2mm pipe walls

        logger.info("HeatTransferCoefficients initialized")

    def overall_heat_transfer_coefficient(
        self,
        inner_coefficient: float,
        outer_coefficient: float,
        wall_conductivity: float,
        wall_thickness: float,
    ) -> float:
        """
        Calculate overall heat transfer coefficient through a wall.

        Uses: 1/U = 1/h_inner + t/k + 1/h_outer

        Args:
            inner_coefficient: Inner surface heat transfer coefficient (W/(m²·K))
            outer_coefficient: Outer surface heat transfer coefficient (W/(m²·K))
            wall_conductivity: Wall thermal conductivity (W/(m·K))
            wall_thickness: Wall thickness (m)

        Returns:
            Overall heat transfer coefficient (W/(m²·K))
        """
        thermal_resistance = (
            1 / inner_coefficient
            + wall_thickness / wall_conductivity
            + 1 / outer_coefficient
        )

        overall_coefficient = 1 / thermal_resistance if thermal_resistance > 0 else 0.0

        logger.debug(f"Overall U = {overall_coefficient:.1f} W/(m²·K)")

        return overall_coefficient

    def reynolds_number(
        self, velocity: float, length: float, kinematic_viscosity: float
    ) -> float:
        """
        Calculate Reynolds number for flow characterization.

        Re = V*L/ν

        Args:
            velocity: Flow velocity (m/s)
            length: Characteristic length (m)
            kinematic_viscosity: Kinematic viscosity (m²/s)

        Returns:
            Reynolds number (dimensionless)
        """
        if kinematic_viscosity <= 0:
            return 0.0

        return velocity * length / kinematic_viscosity

    def nusselt_number_cylinder(self, reynolds: float, prandtl: float) -> float:
        """
        Calculate Nusselt number for cylinder in cross flow.

        Uses Churchill-Bernstein correlation for wide Re range.

        Args:
            reynolds: Reynolds number
            prandtl: Prandtl number

        Returns:
            Nusselt number (dimensionless)
        """
        if reynolds < 1:
            return 2.0  # Minimum Nusselt number for cylinder

        # Churchill-Bernstein correlation
        re_factor = (1 + (reynolds / 282000) ** (5 / 8)) ** (4 / 5)
        nusselt = (
            0.3
            + (0.62 * reynolds**0.5 * prandtl ** (1 / 3) * re_factor)
            / (1 + (0.4 / prandtl) ** (2 / 3)) ** 0.25
        )

        return max(2.0, nusselt)


class WaterThermalReservoir:
    """
    Models water as a thermal reservoir with temperature gradients.
    """

    def __init__(
        self,
        tank_height: float = 10.0,
        surface_temperature: float = 293.15,
        bottom_temperature: float = 288.15,
    ):
        """
        Initialize water thermal reservoir.

        Args:
            tank_height: Total tank height (m)
            surface_temperature: Surface water temperature (K)
            bottom_temperature: Bottom water temperature (K)
        """
        self.tank_height = tank_height
        self.surface_temperature = surface_temperature
        self.bottom_temperature = bottom_temperature

        # Water properties
        self.water_density = RHO_WATER  # kg/m³
        self.water_specific_heat = 4186.0  # J/(kg·K)
        self.water_thermal_conductivity = 0.6  # W/(m·K)
        self.water_kinematic_viscosity = 1e-6  # m²/s at 20°C
        self.water_prandtl = 7.0  # Prandtl number for water

        # Calculate temperature gradient
        self.temperature_gradient = (
            surface_temperature - bottom_temperature
        ) / tank_height

        logger.info(
            f"Water thermal reservoir: {bottom_temperature:.1f}K → {surface_temperature:.1f}K"
        )

    def water_temperature_at_depth(self, depth: float) -> float:
        """
        Calculate water temperature at a given depth.

        Args:
            depth: Depth from surface (m)

        Returns:
            Water temperature at depth (K)
        """
        # Linear temperature profile (could be made more complex)
        temperature = self.surface_temperature - self.temperature_gradient * depth

        # Clamp to reasonable bounds
        temperature = max(
            self.bottom_temperature, min(self.surface_temperature, temperature)
        )

        return temperature

    def water_temperature_at_position(self, position: float) -> float:
        """
        Calculate water temperature at floater position.

        Args:
            position: Floater position from bottom (m)

        Returns:
            Water temperature (K)
        """
        depth_from_surface = self.tank_height - position
        return self.water_temperature_at_depth(depth_from_surface)

    def thermal_stratification_effect(
        self, position_initial: float, position_final: float
    ) -> Dict:
        """
        Calculate thermal effects of moving through stratified water.

        Args:
            position_initial: Initial position (m)
            position_final: Final position (m)

        Returns:
            Dictionary with thermal stratification results
        """
        temp_initial = self.water_temperature_at_position(position_initial)
        temp_final = self.water_temperature_at_position(position_final)

        temperature_change = temp_final - temp_initial
        position_change = position_final - position_initial

        # Average temperature during transit
        temp_average = (temp_initial + temp_final) / 2

        results = {
            "initial_water_temperature": temp_initial,
            "final_water_temperature": temp_final,
            "average_water_temperature": temp_average,
            "temperature_change": temperature_change,
            "position_change": position_change,
            "thermal_gradient_effect": abs(temperature_change),
        }

        logger.debug(
            f"Thermal stratification: {temp_initial:.1f}K → {temp_final:.1f}K "
            f"(Δpos: {position_change:.1f}m)"
        )

        return results


class AirWaterHeatExchange:
    """
    Models heat exchange between air inside floaters and surrounding water.
    """

    def __init__(self, floater_geometry: Optional[Dict] = None):
        """
        Initialize air-water heat exchange calculations.

        Args:
            floater_geometry: Dictionary with floater dimensions
        """
        self.heat_coeffs = HeatTransferCoefficients()

        # Default floater geometry
        if floater_geometry is None:
            floater_geometry = {
                "diameter": 0.3,  # m
                "height": 0.4,  # m
                "volume": 0.01,  # m³
                "surface_area": 0.5,  # m²
            }

        self.geometry = floater_geometry

        # Heat transfer area (internal surface exposed to air)
        self.heat_transfer_area = floater_geometry["surface_area"]

        logger.info(
            f"Air-water heat exchange initialized (area: {self.heat_transfer_area:.2f} m²)"
        )

    def convective_heat_transfer_coefficient(
        self, air_velocity: float = 0.0, water_velocity: float = 0.5
    ) -> Tuple[float, float]:
        """
        Calculate convective heat transfer coefficients for air and water sides.

        Args:
            air_velocity: Air velocity inside floater (m/s)
            water_velocity: Water velocity around floater (m/s)

        Returns:
            Tuple of (air_side_coefficient, water_side_coefficient)
        """
        # Air side coefficient
        if air_velocity > 0.1:
            h_air = self.heat_coeffs.forced_convection_air
        else:
            h_air = self.heat_coeffs.natural_convection_air

        # Water side coefficient - includes effect of floater motion
        if water_velocity > 0.1:
            # Calculate Reynolds number for water flow around cylinder
            re_water = self.heat_coeffs.reynolds_number(
                water_velocity,
                self.geometry["diameter"],
                self.heat_coeffs.thermal_conductivity_water / (RHO_WATER * 4186),
            )

            # Calculate Nusselt number
            nu_water = self.heat_coeffs.nusselt_number_cylinder(
                re_water, 7.0
            )  # Prandtl = 7 for water

            # Heat transfer coefficient
            h_water = (
                nu_water
                * self.heat_coeffs.thermal_conductivity_water
                / self.geometry["diameter"]
            )
        else:
            h_water = self.heat_coeffs.natural_convection_water

        logger.debug(
            f"Heat transfer coefficients: air {h_air:.1f}, water {h_water:.1f} W/(m²·K)"
        )

        return h_air, h_water

    def overall_heat_transfer_coefficient(
        self, air_velocity: float = 0.0, water_velocity: float = 0.5
    ) -> float:
        """
        Calculate overall heat transfer coefficient from air to water.

        Args:
            air_velocity: Air velocity inside floater (m/s)
            water_velocity: Water velocity around floater (m/s)

        Returns:
            Overall heat transfer coefficient (W/(m²·K))
        """
        h_air, h_water = self.convective_heat_transfer_coefficient(
            air_velocity, water_velocity
        )

        # Overall coefficient through floater wall
        U_overall = self.heat_coeffs.overall_heat_transfer_coefficient(
            h_air,
            h_water,
            self.heat_coeffs.thermal_conductivity_aluminum,
            self.heat_coeffs.floater_wall_thickness,
        )

        return U_overall

    def heat_transfer_rate(
        self,
        air_temperature: float,
        water_temperature: float,
        air_velocity: float = 0.0,
        water_velocity: float = 0.5,
    ) -> float:
        """
        Calculate instantaneous heat transfer rate.

        Args:
            air_temperature: Air temperature inside floater (K)
            water_temperature: Water temperature (K)
            air_velocity: Air velocity inside floater (m/s)
            water_velocity: Water velocity around floater (m/s)

        Returns:
            Heat transfer rate (W) - positive means heat flows into air
        """
        U = self.overall_heat_transfer_coefficient(air_velocity, water_velocity)
        temperature_difference = water_temperature - air_temperature

        heat_rate = U * self.heat_transfer_area * temperature_difference

        logger.debug(
            f"Heat transfer rate: {heat_rate:.1f} W "
            f"(ΔT: {temperature_difference:.1f}K)"
        )

        return heat_rate

    def heat_transfer_over_time(
        self,
        initial_air_temperature: float,
        water_temperature: float,
        air_mass: float,
        time_duration: float,
        time_step: float = 0.1,
        air_velocity: float = 0.0,
        water_velocity: float = 0.5,
    ) -> Dict:
        """
        Calculate heat transfer and temperature change over time.

        Args:
            initial_air_temperature: Initial air temperature (K)
            water_temperature: Water temperature (K)
            air_mass: Mass of air (kg)
            time_duration: Total time for heat transfer (s)
            time_step: Time step for calculation (s)
            air_velocity: Air velocity inside floater (m/s)
            water_velocity: Water velocity around floater (m/s)

        Returns:
            Dictionary with heat transfer results over time
        """
        # Air properties
        cp_air = 1005.0  # J/(kg·K)

        # Initialize arrays for time series
        times = []
        air_temperatures = []
        heat_rates = []
        cumulative_heat = 0.0

        current_air_temp = initial_air_temperature
        time = 0.0

        while time <= time_duration:
            # Calculate current heat transfer rate
            heat_rate = self.heat_transfer_rate(
                current_air_temp, water_temperature, air_velocity, water_velocity
            )

            # Update air temperature
            if air_mass > 0:
                temp_change = (heat_rate * time_step) / (air_mass * cp_air)
                current_air_temp += temp_change

            # Store results
            times.append(time)
            air_temperatures.append(current_air_temp)
            heat_rates.append(heat_rate)
            cumulative_heat += heat_rate * time_step

            time += time_step

        # Calculate final metrics
        final_temperature = current_air_temp
        temperature_change = final_temperature - initial_air_temperature
        average_heat_rate = (
            cumulative_heat / time_duration if time_duration > 0 else 0.0
        )

        results = {
            "initial_air_temperature": initial_air_temperature,
            "final_air_temperature": final_temperature,
            "water_temperature": water_temperature,
            "temperature_change": temperature_change,
            "total_heat_transferred": cumulative_heat,
            "average_heat_rate": average_heat_rate,
            "time_duration": time_duration,
            "time_series": {
                "times": times,
                "air_temperatures": air_temperatures,
                "heat_rates": heat_rates,
            },
        }

        logger.debug(
            f"Heat transfer over {time_duration:.1f}s: "
            f"{initial_air_temperature:.1f}K → {final_temperature:.1f}K "
            f"(total heat: {cumulative_heat/1000:.1f} kJ)"
        )

        return results


class CompressionHeatRecovery:
    """
    Models heat recovery from the compression process.
    """

    def __init__(self):
        """Initialize compression heat recovery system."""
        self.heat_coeffs = HeatTransferCoefficients()

        # Heat exchanger properties
        self.heat_exchanger_effectiveness = 0.75  # Heat exchanger effectiveness
        self.heat_exchanger_area = 2.0  # m² - heat exchanger surface area
        self.water_flow_rate = 0.01  # m³/s - cooling water flow rate

        # Thermal masses
        self.compressor_thermal_mass = 50.0  # kg equivalent thermal mass
        self.compressor_specific_heat = 500.0  # J/(kg·K) equivalent

        logger.info("Compression heat recovery initialized")

    def recoverable_heat_from_compression(
        self, compression_work: float, compression_efficiency: float = 0.85
    ) -> float:
        """
        Calculate heat available for recovery from compression.

        Args:
            compression_work: Theoretical compression work (J)
            compression_efficiency: Actual compression efficiency

        Returns:
            Recoverable heat (J)
        """
        # Total input energy
        total_energy_input = compression_work / compression_efficiency

        # Heat generated = input energy - useful work
        heat_generated = total_energy_input - compression_work

        # Recoverable fraction (not all heat can be recovered)
        recoverable_fraction = 0.6  # 60% of heat can be recovered
        recoverable_heat = heat_generated * recoverable_fraction

        logger.debug(
            f"Recoverable heat: {recoverable_heat/1000:.1f} kJ "
            f"({recoverable_fraction:.1%} of {heat_generated/1000:.1f} kJ)"
        )

        return recoverable_heat

    def heat_recovery_to_water(
        self,
        recoverable_heat: float,
        water_temperature: float,
        heat_recovery_time: float,
    ) -> Dict:
        """
        Calculate heat recovery to water system.

        Args:
            recoverable_heat: Available heat for recovery (J)
            water_temperature: Initial water temperature (K)
            heat_recovery_time: Time for heat recovery process (s)

        Returns:
            Dictionary with heat recovery results
        """
        # Heat transfer rate
        if heat_recovery_time > 0:
            heat_transfer_rate = recoverable_heat / heat_recovery_time
        else:
            heat_transfer_rate = 0.0

        # Water properties
        water_specific_heat = 4186.0  # J/(kg·K)
        water_density = RHO_WATER

        # Mass of water affected
        water_volume_affected = self.water_flow_rate * heat_recovery_time
        water_mass_affected = water_density * water_volume_affected

        # Temperature rise in water
        if water_mass_affected > 0:
            water_temperature_rise = (
                recoverable_heat * self.heat_exchanger_effectiveness
            ) / (water_mass_affected * water_specific_heat)
        else:
            water_temperature_rise = 0.0

        final_water_temperature = water_temperature + water_temperature_rise

        # Actual heat transferred to water
        actual_heat_transferred = recoverable_heat * self.heat_exchanger_effectiveness

        results = {
            "recoverable_heat": recoverable_heat,
            "actual_heat_transferred": actual_heat_transferred,
            "heat_transfer_rate": heat_transfer_rate,
            "initial_water_temperature": water_temperature,
            "final_water_temperature": final_water_temperature,
            "water_temperature_rise": water_temperature_rise,
            "water_mass_affected": water_mass_affected,
            "heat_recovery_efficiency": self.heat_exchanger_effectiveness,
            "heat_recovery_time": heat_recovery_time,
        }

        logger.debug(
            f"Heat recovery: {actual_heat_transferred/1000:.1f} kJ → "
            f"water temp rise {water_temperature_rise:.2f}K"
        )

        return results


class IntegratedHeatExchange:
    """
    Integrates all heat exchange processes for complete thermal modeling.
    """

    def __init__(
        self,
        tank_height: float = 10.0,
        surface_temperature: float = 293.15,
        bottom_temperature: float = 288.15,
        floater_geometry: Optional[Dict] = None,
    ):
        """
        Initialize integrated heat exchange system.

        Args:
            tank_height: Total tank height (m)
            surface_temperature: Surface water temperature (K)
            bottom_temperature: Bottom water temperature (K)
            floater_geometry: Floater geometry dictionary
        """
        self.water_reservoir = WaterThermalReservoir(
            tank_height, surface_temperature, bottom_temperature
        )
        self.air_water_exchange = AirWaterHeatExchange(floater_geometry)
        self.heat_recovery = CompressionHeatRecovery()

        self.tank_height = tank_height

        logger.info("Integrated heat exchange system initialized")

    def complete_heat_exchange_analysis(
        self,
        floater_position: float,
        air_volume: float,
        air_pressure: float,
        air_temperature: float,
        ascent_velocity: float,
        ascent_time: float,
        compression_work: float = 0.0,
    ) -> Dict:
        """
        Perform complete heat exchange analysis for a floater during ascent.

        Args:
            floater_position: Current floater position (m)
            air_volume: Air volume in floater (m³)
            air_pressure: Air pressure (Pa)
            air_temperature: Initial air temperature (K)
            ascent_velocity: Floater ascent velocity (m/s)
            ascent_time: Time for ascent (s)
            compression_work: Compression work for heat recovery (J)

        Returns:
            Complete heat exchange analysis results
        """
        # 1. Water thermal stratification
        final_position = min(
            self.tank_height, floater_position + ascent_velocity * ascent_time
        )
        stratification = self.water_reservoir.thermal_stratification_effect(
            floater_position, final_position
        )

        # 2. Air-water heat exchange during ascent
        water_temp_average = stratification["average_water_temperature"]

        # Calculate air mass
        R_specific = 287.0  # J/(kg·K)
        air_density = air_pressure / (R_specific * air_temperature)
        air_mass = air_density * air_volume

        # Water velocity relative to floater
        water_velocity = ascent_velocity + 0.1  # Add small circulation velocity

        heat_exchange = self.air_water_exchange.heat_transfer_over_time(
            air_temperature,
            water_temp_average,
            air_mass,
            ascent_time,
            time_step=0.1,
            water_velocity=water_velocity,
        )

        # 3. Compression heat recovery (if applicable)
        heat_recovery_results = None
        if compression_work > 0:
            recoverable_heat = self.heat_recovery.recoverable_heat_from_compression(
                compression_work
            )
            heat_recovery_results = self.heat_recovery.heat_recovery_to_water(
                recoverable_heat,
                stratification["initial_water_temperature"],
                ascent_time,
            )

        # 4. Combined results
        results = {
            "thermal_stratification": stratification,
            "air_water_heat_exchange": heat_exchange,
            "compression_heat_recovery": heat_recovery_results,
            "system_parameters": {
                "floater_position_initial": floater_position,
                "floater_position_final": final_position,
                "air_volume": air_volume,
                "air_pressure": air_pressure,
                "air_mass": air_mass,
                "ascent_velocity": ascent_velocity,
                "ascent_time": ascent_time,
            },
            "thermal_performance": {
                "air_temperature_change": heat_exchange["temperature_change"],
                "total_heat_transferred": heat_exchange["total_heat_transferred"],
                "thermal_efficiency": (
                    heat_exchange["total_heat_transferred"] / max(1.0, compression_work)
                    if compression_work > 0
                    else 0.0
                ),
            },
        }

        logger.info(
            f"Complete heat exchange analysis: "
            f"ΔT_air = {heat_exchange['temperature_change']:.1f}K, "
            f"Q_total = {heat_exchange['total_heat_transferred']/1000:.1f} kJ"
        )

        return results
