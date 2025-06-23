"""
Generator & power calculation module.
Handles conversion of mechanical torque and speed to electrical power.
"""

from typing import Optional


class Generator:
    """
    Represents the generator converting mechanical input to electrical power.
    Handles efficiency and power calculation.
    """

    def __init__(self, efficiency: float = 1.0):
        """
        :param efficiency: Generator efficiency (0-1)
        """
        self.efficiency = efficiency

    def compute_power(self, torque: float, angular_speed: float) -> float:
        """
        Compute instantaneous power output.
        :param torque: Input torque (Nm)
        :param angular_speed: Angular speed (rad/s)
        :return: Power output (W)
        """
        return torque * angular_speed * self.efficiency

    def update(self, dt: float, input_torque: float) -> None:
        """
        Update internal state (stub for future expansion).
        :param dt: Time step (s)
        :param input_torque: Input torque (Nm)
        """
        # For now, assume quasi-steady state; expand for electrical dynamics if needed
        pass
