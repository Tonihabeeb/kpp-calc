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
        self.energy_used = 0.0
        logger.info(f"PneumaticSystem initialized: pressure={tank_pressure} bar, volume={tank_volume} m^3")

    def trigger_injection(self, floater) -> bool:
        """
        Trigger the air injection process for a floater.

        Args:
            floater: The Floater object to start filling.

        Returns:
            bool: True if injection was successfully started, False otherwise.
        """
        # Simplified check for available pressure
        if self.tank_pressure > 1.5: # Some threshold above atmospheric
            floater.start_filling()
            # Model a pressure drop for the injection
            pressure_drop = floater.volume / self.tank_volume * 0.5 # Simplified model
            self.tank_pressure -= pressure_drop
            logger.info(f"Triggered injection for a floater. Tank pressure dropped to {self.tank_pressure:.2f} bar.")
            return True
        else:
            logger.warning("Injection failed: tank pressure too low.")
            return False

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
            self.compressor_on = False
            logger.info("Compressor reached target pressure and turned OFF.")
        # If compressor is on and pressure is below target, increase pressure gradually
        if self.compressor_on:
            # Simplified pressure increase model
            pressure_increase = (self.compressor_power / self.tank_volume) * dt * 0.1
            self.tank_pressure += pressure_increase
            self.energy_used += self.compressor_power * dt
            logger.debug(f"Compressor running: pressure={self.tank_pressure:.2f} bar, energy_used={self.energy_used:.2f} kJ")
        # Clamp pressure to target if slightly exceeded due to increment
        if self.tank_pressure > self.target_pressure:
            self.tank_pressure = self.target_pressure
