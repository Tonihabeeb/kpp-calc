"""
Thermal effects on floater physics.
Handles heat transfer, temperature effects, and thermal expansion.
"""

import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ThermalState:
    """Thermal state of a floater"""

    air_temperature: float = 293.15  # K
    water_temperature: float = 293.15  # K
    surface_area_air_water: float = 0.0  # m²
    heat_transfer_coefficient: float = 150.0  # W/m²K
    thermal_energy_contribution: float = 0.0  # J
    expansion_work_done: float = 0.0  # J


class ThermalModel:
    """Models thermal effects on floater physics"""

    def __init__(
        self,
        heat_transfer_coefficient: float = 150.0,
        specific_heat_air: float = 1005.0,  # J/kg·K
        specific_heat_water: float = 4186.0,
    ):  # J/kg·K
        self.heat_transfer_coefficient = heat_transfer_coefficient
        self.specific_heat_air = specific_heat_air
        self.specific_heat_water = specific_heat_water

    def calculate_heat_transfer(
        self, air_volume: float, water_volume: float, air_temp: float, water_temp: float, surface_area: float, dt: float
    ) -> float:
        """Calculate heat transfer between air and water"""
        if surface_area <= 0 or abs(air_temp - water_temp) < 0.1:
            return 0.0

        # Heat transfer rate (W)
        heat_rate = self.heat_transfer_coefficient * surface_area * (water_temp - air_temp)

        # Heat energy transferred (J)
        heat_energy = heat_rate * dt

        return heat_energy

    def update_temperatures(
        self, thermal_state: ThermalState, heat_energy: float, air_mass: float, water_mass: float, dt: float
    ) -> ThermalState:
        """Update temperatures based on heat transfer"""
        if air_mass <= 0 or water_mass <= 0:
            return thermal_state

        # Temperature changes
        air_temp_change = heat_energy / (air_mass * self.specific_heat_air)
        water_temp_change = -heat_energy / (water_mass * self.specific_heat_water)

        # Update temperatures
        new_air_temp = thermal_state.air_temperature + air_temp_change
        new_water_temp = thermal_state.water_temperature + water_temp_change

        # Update thermal state
        thermal_state.air_temperature = new_air_temp
        thermal_state.water_temperature = new_water_temp
        thermal_state.thermal_energy_contribution = heat_energy

        return thermal_state

    def calculate_thermal_expansion(self, volume: float, temperature: float, reference_temp: float = 293.15) -> float:
        """Calculate thermal expansion of air volume"""
        # Thermal expansion coefficient for air (1/K)
        alpha_air = 3.67e-3

        if temperature > reference_temp:
            expansion_ratio = 1 + alpha_air * (temperature - reference_temp)
            expanded_volume = volume * expansion_ratio
            return expanded_volume - volume
        else:
            return 0.0

    def calculate_expansion_work(self, pressure: float, volume_change: float) -> float:
        """Calculate work done by thermal expansion"""
        # Work = P * ΔV
        return pressure * volume_change
