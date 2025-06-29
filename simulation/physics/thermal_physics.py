"""
H2 Thermal Physics Implementation
Temperature-based buoyancy enhancement system
"""

import logging
import math
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class ThermalPhysics:
    """
    H2 Hypothesis: Thermal Enhancement of Buoyancy

    This class models temperature-based effects on:
    - Buoyancy force enhancement through thermal expansion
    - Heat transfer efficiency
    - Temperature-dependent fluid properties
    """

    def __init__(
        self,
        enabled: bool = False,
        thermal_coefficient: float = 0.0001,
        thermal_efficiency: float = 0.75,
        target_temperature: float = 298.15,
    ):
        """
        Initialize thermal physics system.

        Args:
            enabled: Whether thermal system is active
            thermal_coefficient: Thermal expansion coefficient for buoyancy enhancement
            thermal_efficiency: Heat transfer efficiency (0-1)
            target_temperature: Target temperature for thermal enhancement (K)
        """
        self.enabled = enabled
        self.thermal_coefficient = thermal_coefficient
        self.thermal_efficiency = thermal_efficiency
        self.target_temperature = target_temperature

        # Internal state
        self.active = False
        self.current_temperature = 293.15  # Room temperature
        self.buoyancy_multiplier = 1.0
        self.heat_input_rate = 0.0

        # Physical constants
        self.water_thermal_expansion = 2.1e-4  # K⁻¹ at 20°C
        self.water_specific_heat = 4186  # J/(kg·K)

        logger.info(
            f"ThermalPhysics initialized: enabled={enabled}, "
            f"coefficient={thermal_coefficient:.6f}"
        )

    def update(
        self, dt: float, ambient_temperature: float = 293.15, heat_input: float = 0.0
    ) -> None:
        """
        Update thermal effects for this time step.

        Args:
            dt: Time step (seconds)
            ambient_temperature: Ambient water temperature (K)
            heat_input: External heat input rate (W)
        """
        if not self.enabled:
            self.active = False
            self.buoyancy_multiplier = 1.0
            self.heat_input_rate = 0.0
            self.current_temperature = ambient_temperature
            return

        self.active = True
        self.heat_input_rate = heat_input

        # Update temperature based on heat input and cooling
        if heat_input > 0:
            # Heat addition increases temperature
            temperature_rise = (
                heat_input
                * dt
                * self.thermal_efficiency
                / (self.water_specific_heat * 1000)  # Assume 1000 kg of water
            )
            self.current_temperature = min(
                self.target_temperature, self.current_temperature + temperature_rise
            )
        else:
            # Natural cooling toward ambient
            cooling_rate = 0.1  # K/s cooling rate
            temp_diff = self.current_temperature - ambient_temperature
            cooling = cooling_rate * temp_diff * dt
            self.current_temperature = max(
                ambient_temperature, self.current_temperature - cooling
            )

        # Calculate buoyancy enhancement based on temperature difference
        temp_delta = self.current_temperature - ambient_temperature

        # Thermal expansion reduces fluid density, increasing buoyancy
        density_change = self.water_thermal_expansion * temp_delta
        thermal_buoyancy_boost = self.thermal_coefficient * temp_delta

        self.buoyancy_multiplier = 1.0 + thermal_buoyancy_boost

        logger.debug(
            f"Thermal update: T={self.current_temperature:.1f}K, "
            f"boost={thermal_buoyancy_boost:.4f}, "
            f"multiplier={self.buoyancy_multiplier:.4f}"
        )

    def apply_buoyancy_enhancement(self, base_buoyancy: float) -> float:
        """
        Apply thermal enhancement to base buoyancy force.

        Args:
            base_buoyancy: Base buoyancy force (N)

        Returns:
            Enhanced buoyancy force
        """
        if not self.active:
            return base_buoyancy

        return base_buoyancy * self.buoyancy_multiplier

    def get_temperature_effects(self) -> Dict[str, float]:
        """
        Get detailed temperature effects.

        Returns:
            Dictionary with temperature-related properties
        """
        if not self.active:
            return {}

        return {
            "current_temperature_K": self.current_temperature,
            "current_temperature_C": self.current_temperature - 273.15,
            "buoyancy_multiplier": self.buoyancy_multiplier,
            "thermal_expansion_effect": (self.current_temperature - 293.15)
            * self.water_thermal_expansion,
            "heat_input_rate_W": self.heat_input_rate,
            "thermal_efficiency": self.thermal_efficiency,
        }

    def calculate_required_heat_input(self, desired_temp_rise: float) -> float:
        """
        Calculate heat input required for desired temperature rise.

        Args:
            desired_temp_rise: Desired temperature increase (K)

        Returns:
            Required heat input rate (W)
        """
        if not self.enabled:
            return 0.0

        # Heat capacity calculation for water mass
        water_mass = 1000  # kg (approximate)
        required_heat_rate = (
            water_mass
            * self.water_specific_heat
            * desired_temp_rise
            / self.thermal_efficiency
        )

        return required_heat_rate

    def get_status(self) -> Dict[str, Any]:
        """
        Get current thermal system status.

        Returns:
            Status dictionary
        """
        return {
            "enabled": self.enabled,
            "active": self.active,
            "thermal_coefficient": self.thermal_coefficient,
            "thermal_efficiency": self.thermal_efficiency,
            "current_temperature_K": self.current_temperature,
            "current_temperature_C": self.current_temperature - 273.15,
            "target_temperature_K": self.target_temperature,
            "buoyancy_multiplier": self.buoyancy_multiplier,
            "heat_input_rate_W": self.heat_input_rate,
        }
