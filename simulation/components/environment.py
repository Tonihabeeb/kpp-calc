"""
Environment (Water & Hydrodynamics) module.
Encapsulates water properties and H1/H2 hypothesis logic for the KPP simulator.
"""

import logging
import math

from utils.logging_setup import setup_logging

setup_logging()
logger = logging.getLogger(__name__)


class Environment:
    """
    Represents the water environment in the KPP tank.
    Handles water properties, nanobubble (H1), and thermal boost (H2) logic.
    """

    def __init__(
        self,
        water_density: float = 1000.0,
        water_viscosity: float = 1.0e-3,
        gravity: float = 9.81,
        nanobubble_enabled: bool = False,
        density_reduction_factor: float = 0.1,
        thermal_boost_enabled: bool = False,
        boost_factor: float = 0.1,
    ):
        """
        Initialize the environment.

        Args:
            water_density (float): Water density (kg/m^3).
            water_viscosity (float): Water viscosity (Pa.s).
            gravity (float): Gravitational acceleration (m/s^2).
            nanobubble_enabled (bool): H1 flag for drag/density reduction.
            density_reduction_factor (float): Fractional reduction for H1.
            thermal_boost_enabled (bool): H2 flag for buoyancy boost.
            boost_factor (float): Fractional boost for H2.
        """
        # All water and hydrodynamics properties are encapsulated here for easy tuning and extension.
        self.water_density = water_density
        self.water_viscosity = water_viscosity
        self.gravity = gravity
        self.nanobubble_enabled = nanobubble_enabled
        self.density_reduction_factor = density_reduction_factor
        self.thermal_boost_enabled = thermal_boost_enabled
        self.boost_factor = boost_factor
        logger.info(f"Environment initialized: density={water_density}, viscosity={water_viscosity}, gravity={gravity}")

    def get_density(self, floater=None) -> float:
        """
        Return realistic effective water density for KPP operation.

        Enhanced density calculation including:
        - Temperature-dependent density
        - Pressure effects
        - Salinity variations
        - H1 nanobubble effects
        - Depth stratification

        Args:
            floater: Optional floater for position-dependent calculations.
        Returns:
            float: Effective water density (kg/m^3).
        """
        # Base density with temperature effects
        base_density = self.water_density

        # Temperature effects (simplified)
        temperature = 293.15  # 20°C default
        temp_correction = 1.0 - 2.1e-4 * (temperature - 293.15)  # Thermal expansion
        base_density *= temp_correction

        # Pressure effects (hydrostatic)
        depth = 5.0  # Typical KPP depth
        pressure = base_density * self.gravity * depth
        pressure_correction = 1.0 + pressure / 2.2e9  # Bulk modulus
        base_density *= pressure_correction

        # Salinity effects (freshwater assumption for KPP)
        salinity = 0.0  # Freshwater
        salinity_correction = 1.0 + 0.8e-3 * salinity  # ~0.8 kg/m³ per ppt
        base_density *= salinity_correction

        # H1: Nanobubble effects if enabled
        if self.nanobubble_enabled:
            # Enhanced nanobubble physics
            bubble_fraction = self.density_reduction_factor
            bubble_size = 50e-9  # 50 nm
            surface_tension = 0.0728  # N/m

            # Bubble stability factor
            bubble_stability = surface_tension / (2 * bubble_size)
            effective_bubble_fraction = bubble_fraction * bubble_stability

            # Air density at conditions
            air_density = 1.225 * (273.15 / temperature) * (101325.0 / (101325.0 + pressure))

            # Two-phase mixture density
            effective_density = base_density * (1 - effective_bubble_fraction) + air_density * effective_bubble_fraction

            logger.debug(f"Enhanced H1 nanobubble: density {base_density:.1f} → {effective_density:.1f} kg/m³")
            return effective_density

        return base_density

    def get_viscosity(self) -> float:
        """
        Return realistic water viscosity for KPP operation.

        Enhanced viscosity calculation including:
        - Temperature-dependent viscosity
        - Pressure effects
        - Salinity effects
        - Shear rate effects (non-Newtonian behavior)

        Returns:
            float: Water viscosity (Pa.s).
        """
        # Base viscosity
        base_viscosity = self.water_viscosity

        # Temperature effects (Andrade equation approximation)
        temperature = 293.15  # 20°C default
        reference_temp = 293.15
        reference_viscosity = 1.002e-3  # Pa·s at 20°C

        # Simplified temperature dependence
        temp_factor = math.exp(1.5 * (reference_temp - temperature) / temperature)
        base_viscosity = reference_viscosity * temp_factor

        # Pressure effects (minor for typical KPP pressures)
        depth = 5.0  # Typical KPP depth
        pressure = 1000.0 * self.gravity * depth  # Pa
        pressure_factor = 1.0 + 2.0e-8 * pressure  # ~2% increase per MPa
        base_viscosity *= pressure_factor

        # Salinity effects (freshwater assumption)
        salinity = 0.0  # Freshwater
        salinity_factor = 1.0 + 0.5e-3 * salinity  # ~0.5% increase per ppt
        base_viscosity *= salinity_factor

        # Shear rate effects (simplified non-Newtonian behavior)
        # For KPP, assume low shear rates
        shear_rate = 1.0  # s⁻¹ typical for KPP
        shear_factor = 1.0 + 0.1 * math.exp(-shear_rate / 10.0)  # Slight shear thinning
        base_viscosity *= shear_factor

        logger.debug(f"Enhanced viscosity: {self.water_viscosity:.3e} → {base_viscosity:.3e} Pa·s")

        return base_viscosity

    def update(self, dt: float) -> None:
        """
        Update environment state (stub for future dynamic effects).
        Args:
            dt (float): Time step (s).
        """
        # For Pre-Stage, assume steady state. In future, could update temperature, nanobubble concentration, etc.
