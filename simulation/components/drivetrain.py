"""
Drivetrain & gearbox module.
Handles conversion of chain force to generator torque, gear ratio, and efficiency.
"""

from typing import Optional

class Drivetrain:
    """
    Represents the mechanical drivetrain that converts chain force to generator torque.
    Handles gear ratio and efficiency.
    """
    def __init__(self, gear_ratio: float = 1.0, efficiency: float = 1.0, sprocket_radius: float = 1.0):
        """
        :param gear_ratio: Ratio between chain sprocket and generator shaft
        :param efficiency: Drivetrain efficiency (0-1)
        :param sprocket_radius: Radius of the chain sprocket (m)
        """
        self.gear_ratio = gear_ratio
        self.efficiency = efficiency
        self.sprocket_radius = sprocket_radius

    def compute_torque(self, chain_force: float) -> float:
        """
        Calculate the torque delivered to the generator shaft given net force on the chain.
        :param chain_force: Net force from floaters on the chain (N)
        :return: Output torque at generator shaft (Nm)
        """
        chain_torque = chain_force * self.sprocket_radius
        output_torque = chain_torque * self.gear_ratio * self.efficiency
        return output_torque

    def calculate_torque(self, chain_force: float) -> float:
        """
        Calculate the torque delivered to the generator shaft given net force on the chain.
        :param chain_force: Net force from floaters on the chain (N)
        :return: Output torque at generator shaft (Nm)
        """
        return self.compute_torque(chain_force)

    def apply_load(self, generator_torque: float) -> float:
        """
        Determine how the generator's resistance feeds back to the chain (stub for future expansion).
        :param generator_torque: Torque applied by generator load (Nm)
        :return: Adjusted chain force (N)
        """
        # For now, just a placeholder; in future, could reduce chain acceleration based on load
        return generator_torque / (self.sprocket_radius * self.gear_ratio) if self.sprocket_radius > 0 else 0.0

    def update_params(self, params: dict) -> None:
        """
        Update drivetrain parameters dynamically.
        :param params: Dictionary of parameters to update.
        """
        self.gear_ratio = params.get('gear_ratio', self.gear_ratio)
        self.efficiency = params.get('efficiency', self.efficiency)
        self.sprocket_radius = params.get('sprocket_radius', self.sprocket_radius)
