"""
Environment (Water & Hydrodynamics) module.
Encapsulates water properties and H1/H2 hypothesis logic for the KPP simulator.
"""

import logging

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
        logger.info(
            f"Environment initialized: density={water_density}, viscosity={water_viscosity}, gravity={gravity}"
        )

    def get_density(self, floater=None) -> float:
        """
        Return the effective water density, applying H1 if enabled.

        Args:
            floater: Optional floater or position for context (not used in Pre-Stage).
        Returns:
            float: Effective water density (kg/m^3).
        """
        # H1: If nanobubble is enabled, reduce density for drag/force calculations.
        if self.nanobubble_enabled:
            density = self.water_density * (1.0 - self.density_reduction_factor)
            logger.debug(f"Nanobubble H1 enabled: density reduced to {density}")
            return density
        return self.water_density

    def get_viscosity(self) -> float:
        """
        Return the water viscosity.
        Returns:
            float: Water viscosity (Pa.s).
        """
        return self.water_viscosity

    def update(self, dt: float) -> None:
        """
        Update environment state (stub for future dynamic effects).
        Args:
            dt (float): Time step (s).
        """
        # For Pre-Stage, assume steady state. In future, could update temperature, nanobubble concentration, etc.
        pass
