"""
Generator & power calculation module.
Handles conversion of mechanical torque and speed to electrical power.

Generator logic: calculates power output based on drivetrain input
Handles generator state and output calculations
"""

import logging
import math
from typing import Optional

from utils.logging_setup import setup_logging

setup_logging()
logger = logging.getLogger(__name__)


class Generator:
    """
    Represents the generator converting mechanical input to electrical power.
    Models a 530kW generator connected to a heat resistor load.
    """

    def __init__(
        self,
        efficiency: float = 0.92,
        target_power: float = 530000.0,  # Watts
        target_rpm: float = 375.0,
    ):
        """
        Initialize a Generator.

        Args:
            efficiency (float): Generator efficiency (0-1).
            target_power (float): Target power output (W).
            target_rpm (float): Target RPM for rated power.
        """
        if not (0 <= efficiency <= 1):
            logger.error("Invalid generator efficiency: must be in [0,1].")
            raise ValueError("Generator efficiency must be in [0,1].")
        self.efficiency = efficiency
        self.target_power = target_power
        self.target_rpm = target_rpm
        self.target_omega = target_rpm * (2 * math.pi / 60)
        self.target_load_torque = (
            self.target_power / self.target_omega if self.target_omega > 0 else 0
        )
        logger.info(
            f"Initialized Generator: efficiency={efficiency}, target_power={target_power}W, target_rpm={target_rpm} RPM"
        )

    def set_user_load(self, user_load_torque: float):
        """
        Set a user-defined load torque (Nm) to override the default generator load.
        """
        self.user_load_torque = user_load_torque

    def get_load_torque(self, current_omega: float) -> float:
        """
        Calculate the resistive load torque from the generator based on its current speed.
        This simulates the behavior of a generator connected to a resistive load.

        Args:
            current_omega (float): The current angular velocity of the generator shaft (rad/s).

        Returns:
            float: The resistive load torque (Nm).
        """
        # If user load is set, use it
        if hasattr(self, "user_load_torque") and self.user_load_torque is not None:
            return self.user_load_torque

        speed_ratio = current_omega / self.target_omega if self.target_omega > 0 else 0

        if speed_ratio < 0.3:
            # Partial load at low speeds (proportional to speed squared)
            load_torque = self.target_load_torque * 0.2 * (speed_ratio**2)
        elif speed_ratio <= 1.1:
            # Rated operation zone - constant power load behavior
            load_torque = self.target_power / current_omega
        else:
            # Over-speed - increased load to prevent runaway
            load_torque = self.target_load_torque * (1.5 + 0.5 * (speed_ratio - 1.1))

        logger.debug(
            f"Generator load torque: {load_torque:.2f} Nm at {current_omega:.2f} rad/s"
        )
        return load_torque

    def calculate_power_output(self, current_omega: float) -> float:
        """
        Compute instantaneous power output based on the generator's load characteristics.

        Args:
            current_omega (float): Current angular speed of the generator shaft (rad/s).

        Returns:
            float: Power output (W).
        """
        load_torque = self.get_load_torque(current_omega)
        power_consumed = load_torque * current_omega
        power_output = power_consumed * self.efficiency
        logger.debug(f"Calculated power output: {power_output:.2f} W")
        return power_output

    def update_params(self, params: dict) -> None:
        """
        Update generator parameters dynamically.

        Args:
            params (dict): Dictionary of parameters to update.
        """
        old_eff = self.efficiency
        self.efficiency = params.get("generator_efficiency", self.efficiency)
        self.target_power = params.get("target_power", self.target_power)
        self.target_rpm = params.get("target_rpm", self.target_rpm)
        self.target_omega = self.target_rpm * (2 * math.pi / 60)
        self.target_load_torque = (
            self.target_power / self.target_omega if self.target_omega > 0 else 0
        )
        logger.info(
            f"Updated Generator params. Efficiency from {old_eff} to {self.efficiency}"
        )

    def reset(self):
        """
        Resets the generator to its initial state. Currently a no-op.
        """
        logger.info("Generator state has been reset.")
