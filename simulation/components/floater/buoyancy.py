"""
Buoyancy calculations for floater physics.
Handles buoyant force, pressure effects, and density calculations.
"""

import logging
from dataclasses import dataclass

from config.config import RHO_AIR, RHO_WATER, G

logger = logging.getLogger(__name__)


@dataclass
class BuoyancyResult:
    """Result of buoyancy calculation"""

    buoyant_force: float
    displaced_volume: float
    effective_density: float
    pressure_effect: float
    thermal_effect: float


class BuoyancyCalculator:
    """Calculates buoyant forces and related physics"""

    def __init__(self, tank_height: float = 10.0):
        self.tank_height = tank_height

    def calculate_basic_buoyancy(self, volume: float, depth: float) -> float:
        """Calculate basic buoyant force (Archimedes' principle)"""
        return RHO_WATER * G * volume

    def calculate_enhanced_buoyancy(
        self, volume: float, depth: float, air_fill_level: float, air_pressure: float, water_temperature: float = 293.15
    ) -> BuoyancyResult:
        """Calculate enhanced buoyancy with pressure and thermal effects"""

        # Basic buoyant force
        basic_force = self.calculate_basic_buoyancy(volume, depth)

        # Pressure effect on air volume
        pressure_effect = self._calculate_pressure_effect(volume, depth, air_fill_level, air_pressure)

        # Thermal effect on air expansion
        thermal_effect = self._calculate_thermal_effect(volume, air_fill_level, water_temperature)

        # Effective displaced volume
        air_volume = volume * air_fill_level
        water_volume = volume * (1 - air_fill_level)
        displaced_volume = water_volume + (air_volume * pressure_effect)

        # Total buoyant force
        total_force = basic_force + pressure_effect + thermal_effect

        # Effective density
        effective_density = (RHO_WATER * water_volume + RHO_AIR * air_volume) / volume

        return BuoyancyResult(
            buoyant_force=total_force,
            displaced_volume=displaced_volume,
            effective_density=effective_density,
            pressure_effect=pressure_effect,
            thermal_effect=thermal_effect,
        )

    def _calculate_pressure_effect(
        self, volume: float, depth: float, air_fill_level: float, air_pressure: float
    ) -> float:
        """Calculate pressure effect on buoyancy"""
        # Pressure increases with depth
        water_pressure = 101325 + RHO_WATER * G * depth

        # Air volume changes with pressure (Boyle's law)
        if air_pressure > 0:
            pressure_ratio = water_pressure / air_pressure
            compressed_air_volume = volume * air_fill_level / pressure_ratio
            pressure_effect = RHO_WATER * G * compressed_air_volume
        else:
            pressure_effect = 0.0

        return pressure_effect

    def _calculate_thermal_effect(self, volume: float, air_fill_level: float, water_temperature: float) -> float:
        """Calculate thermal effect on buoyancy"""
        # Air expands with temperature (Charles's law)
        reference_temp = 293.15  # 20°C
        if water_temperature > reference_temp:
            temp_ratio = water_temperature / reference_temp
            expanded_air_volume = volume * air_fill_level * temp_ratio
            thermal_effect = RHO_WATER * G * expanded_air_volume
        else:
            thermal_effect = 0.0

        return thermal_effect
