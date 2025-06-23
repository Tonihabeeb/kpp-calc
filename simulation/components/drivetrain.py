"""
Drivetrain & gearbox module.
Handles conversion of chain force to generator torque, gear ratio, and efficiency.

Drivetrain logic: chain, clutch, and generator coupling (H3 logic)
Manages drivetrain state and interactions with other modules
"""

import logging
from typing import Optional
from utils.logging_setup import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

class Drivetrain:
    """
    Represents the mechanical drivetrain that converts chain force to generator torque.
    Handles gear ratio and efficiency.
    """
    def __init__(self, gear_ratio: float = 1.0, efficiency: float = 1.0, sprocket_radius: float = 1.0):
        """
        Initialize a Drivetrain.

        Args:
            gear_ratio (float): Ratio between chain sprocket and generator shaft
            efficiency (float): Drivetrain efficiency (0-1)
            sprocket_radius (float): Radius of the chain sprocket (m)
        """
        if gear_ratio <= 0 or efficiency < 0 or efficiency > 1 or sprocket_radius <= 0:
            logger.error("Invalid drivetrain parameters: gear_ratio and sprocket_radius must be positive, efficiency in [0,1].")
            raise ValueError("Invalid drivetrain parameters.")
        self.gear_ratio = gear_ratio
        self.efficiency = efficiency
        self.sprocket_radius = sprocket_radius
        logger.info(f"Initialized Drivetrain: gear_ratio={gear_ratio}, efficiency={efficiency}, sprocket_radius={sprocket_radius}")

    def compute_torque(self, chain_force: float) -> float:
        """
        Calculate the torque delivered to the generator shaft given net force on the chain.

        Args:
            chain_force (float): Net force from floaters on the chain (N)

        Returns:
            float: Output torque at generator shaft (Nm)
        """
        chain_torque = chain_force * self.sprocket_radius
        output_torque = chain_torque * self.gear_ratio * self.efficiency
        logger.debug(f"Computed torque: {output_torque} Nm (chain_force={chain_force})")
        return output_torque

    def calculate_torque(self, chain_force: float) -> float:
        """
        Alias for compute_torque.

        Args:
            chain_force (float): Net force from floaters on the chain (N)

        Returns:
            float: Output torque at generator shaft (Nm)
        """
        return self.compute_torque(chain_force)

    def apply_load(self, generator_torque: float) -> float:
        """
        Determine how the generator's resistance feeds back to the chain (stub for future expansion).

        Args:
            generator_torque (float): Torque applied by generator load (Nm)

        Returns:
            float: Adjusted chain force (N)
        """
        if self.sprocket_radius <= 0 or self.gear_ratio <= 0:
            logger.error("Invalid sprocket_radius or gear_ratio for load application.")
            return 0.0
        chain_force = generator_torque / (self.sprocket_radius * self.gear_ratio)
        logger.debug(f"Applied load: generator_torque={generator_torque}, chain_force={chain_force}")
        return chain_force

    def update_params(self, params: dict) -> None:
        """
        Update drivetrain parameters dynamically.

        Args:
            params (dict): Dictionary of parameters to update.
        """
        old_params = (self.gear_ratio, self.efficiency, self.sprocket_radius)
        self.gear_ratio = params.get('gear_ratio', self.gear_ratio)
        self.efficiency = float(params.get('efficiency', self.efficiency))
        self.sprocket_radius = params.get('sprocket_radius', self.sprocket_radius)
        logger.info(f"Updated Drivetrain params from {old_params} to (gear_ratio={self.gear_ratio}, efficiency={self.efficiency}, sprocket_radius={self.sprocket_radius})")
