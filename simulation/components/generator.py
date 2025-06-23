"""
Generator & power calculation module.
Handles conversion of mechanical torque and speed to electrical power.

Generator logic: calculates power output based on drivetrain input
Handles generator state and output calculations
"""

import logging
from typing import Optional
from utils.logging_setup import setup_logging

setup_logging()
logger = logging.getLogger(__name__)


class Generator:
    """
    Represents the generator converting mechanical input to electrical power.
    Handles efficiency and power calculation.
    """

    def __init__(self, efficiency: float = 1.0):
        """
        Initialize a Generator.

        Args:
            efficiency (float): Generator efficiency (0-1)
        """
        if efficiency < 0 or efficiency > 1:
            logger.error("Invalid generator efficiency: must be in [0,1].")
            raise ValueError("Generator efficiency must be in [0,1].")
        self.efficiency = efficiency
        logger.info(f"Initialized Generator: efficiency={efficiency}")

    def calculate_power(self, torque: float, angular_speed: float) -> float:
        """
        Compute instantaneous power output.

        Args:
            torque (float): Input torque (Nm)
            angular_speed (float): Angular speed (rad/s)

        Returns:
            float: Power output (W)
        """
        power = torque * angular_speed * self.efficiency
        logger.debug(f"Calculated power: {power} W (torque={torque}, angular_speed={angular_speed})")
        return power

    def update_params(self, params: dict) -> None:
        """
        Update generator parameters dynamically.

        Args:
            params (dict): Dictionary of parameters to update.
        """
        old_eff = self.efficiency
        self.efficiency = params.get('efficiency', self.efficiency)
        logger.info(f"Updated Generator efficiency from {old_eff} to {self.efficiency}")

    def update(self, dt: float, input_torque: float) -> None:
        """
        Update internal state (stub for future expansion).

        Args:
            dt (float): Time step (s)
            input_torque (float): Input torque (Nm)
        """
        # For now, assume quasi-steady state; expand for electrical dynamics if needed
        logger.debug(f"Update called (dt={dt}, input_torque={input_torque}) - stub")
        pass
