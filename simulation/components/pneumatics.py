"""
Pneumatic System module.
Handles air injection, venting, and compressor logic for the KPP simulator.
"""

import logging
from utils.logging_setup import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

class PneumaticSystem:
    """
    Represents the compressed air system for floaters.
    Handles injection, venting, and compressor energy tracking.
    """
    def __init__(self,
                 tank_pressure: float = 5.0,  # bar
                 tank_volume: float = 0.1,    # m^3
                 compressor_power: float = 5.0,  # kW
                 target_pressure: float = 5.0):
        """
        Initialize the pneumatic system.

        Args:
            tank_pressure (float): Initial tank pressure (bar).
            tank_volume (float): Tank volume (m^3).
            compressor_power (float): Compressor power (kW).
            target_pressure (float): Target pressure to maintain (bar).
        """
        # All pneumatic state is encapsulated here for clarity and future extension.
        self.tank_pressure = tank_pressure
        self.tank_volume = tank_volume
        self.compressor_power = compressor_power
        self.target_pressure = target_pressure
        self.compressor_on = False
        self.air_available = tank_volume * tank_pressure  # Simplified: total air in tank
        self.energy_used = 0.0
        logger.info(f"PneumaticSystem initialized: pressure={tank_pressure} bar, volume={tank_volume} m^3")

    def inject_air(self, floater) -> None:
        """
        Inject air into a floater at the bottom.
        Args:
            floater: Floater object to fill with air.
        """
        # Only inject if there is enough air and pressure in the tank.
        if self.air_available <= 0 or self.tank_pressure < 0.5:
            logger.warning("Not enough air to inject. Injection skipped.")
            return
        # Fill the floater with air (makes it buoyant)
        floater.set_filled(True)
        air_used = floater.volume  # Assume 1 injection = 1 floater volume
        self.air_available -= air_used
        # Approximate pressure drop using P1V1 = P2V2 (ideal gas, isothermal)
        self.tank_pressure -= air_used / self.tank_volume
        self.compressor_on = True  # Start compressor to restore pressure
        logger.info(f"Injected air into Floater; tank pressure now {self.tank_pressure:.2f} bar")

    def vent_air(self, floater) -> None:
        """
        Vent air from a floater at the top.
        Args:
            floater: Floater object to fill with water (become heavy).
        """
        # Make the floater heavy (filled with water)
        floater.set_filled(False)
        logger.info("Vented air from Floater at top.")
        # No change to tank pressure (assume open vent to atmosphere)

    def update(self, dt: float) -> None:
        """
        Update compressor state and energy usage.
        Args:
            dt (float): Time step (s).
        """
        # Automatically switch compressor ON if pressure is below target
        if self.tank_pressure < self.target_pressure and not self.compressor_on:
            self.compressor_on = True
            logger.info("Compressor turned ON (pressure below target).")
        # Automatically switch compressor OFF if pressure is at or above target
        if self.tank_pressure >= self.target_pressure and self.compressor_on:
            self.tank_pressure = self.target_pressure
            self.compressor_on = False
            logger.info("Compressor reached target pressure and turned OFF.")
        # If compressor is on and pressure is below target, increase pressure gradually
        if self.compressor_on and self.tank_pressure < self.target_pressure:
            pressure_increase = 0.1 * dt  # bar per second (tunable, simple model)
            self.tank_pressure += pressure_increase
            self.air_available = self.tank_volume * self.tank_pressure
            self.energy_used += self.compressor_power * dt
            logger.debug(f"Compressor running: pressure={self.tank_pressure:.2f} bar, energy_used={self.energy_used:.2f} kJ")
        # Clamp pressure to target if slightly exceeded due to increment
        if self.tank_pressure > self.target_pressure:
            self.tank_pressure = self.target_pressure
