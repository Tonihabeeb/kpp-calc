"""
Floater dynamics module.
Encapsulates buoyancy, drag, and motion for a single floater.

Floater physics: buoyancy, drag, and floater state management
Handles all floater-related calculations and updates
"""

import logging
from typing import Optional
from config.config import G, RHO_WATER
from utils.logging_setup import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

class Floater:
    """
    Represents a buoyant floater in the KPP system.
    Handles buoyancy, drag, and vertical motion.
    """

    def __init__(
        self,
        volume: float,
        mass: float,
        area: float,
        Cd: float = 0.8,
        position: float = 0.0,
        velocity: float = 0.0,
        is_filled: bool = False,
    ):
        """
        Initialize a Floater.

        Args:
            volume (float): Volume of the floater (m^3)
            mass (float): Mass of the floater (kg)
            area (float): Cross-sectional area for drag (m^2)
            Cd (float, optional): Drag coefficient (dimensionless). Defaults to 0.8.
            position (float, optional): Initial vertical position (m). Defaults to 0.0.
            velocity (float, optional): Initial vertical velocity (m/s). Defaults to 0.0.
            is_filled (bool, optional): Whether the floater is filled with air (buoyant). Defaults to False.
        """
        if volume < 0 or mass < 0 or area < 0 or Cd < 0:
            logger.error("Invalid floater parameters: volume, mass, area, and Cd must be non-negative.")
            raise ValueError("Floater parameters must be non-negative.")
        self.volume = volume
        self.mass = mass
        self.area = area
        self.Cd = Cd
        self.position = position
        self.velocity = velocity
        self.is_filled = is_filled
        logger.info(f"Initialized Floater: {self.to_dict()}")

    def set_filled(self, filled: bool) -> None:
        """
        Set the filled state of the floater and log the event.

        Args:
            filled (bool): True if filled with air, False otherwise.
        """
        if self.is_filled != filled:
            self.is_filled = filled
            logger.info(f"Floater fill state changed: is_filled={self.is_filled}")

    def compute_buoyant_force(self) -> float:
        """
        Compute the upward buoyant force on the floater.

        Returns:
            float: Buoyant force (N)
        """
        displaced_volume = self.volume if self.is_filled else 0.0
        F_buoy = RHO_WATER * displaced_volume * G
        logger.debug(f"Buoyant force: {F_buoy} N (is_filled={self.is_filled})")
        return F_buoy

    def compute_drag_force(self) -> float:
        """
        Compute the drag force opposing motion (quadratic drag).

        Returns:
            float: Drag force (N, sign opposes velocity)
        """
        drag_mag = 0.5 * self.Cd * RHO_WATER * self.area * (self.velocity ** 2)
        if self.velocity > 0:
            return -drag_mag  # Upward motion, drag is downward
        else:
            return drag_mag   # Downward motion, drag is upward

    @property
    def force(self) -> float:
        """
        Calculate the net force acting on the floater.

        Returns:
            float: Net force (N)
        """
        F_buoy = self.compute_buoyant_force()
        F_gravity = -self.mass * G
        F_drag = self.compute_drag_force()
        F_net = F_buoy + F_gravity + F_drag
        logger.debug(f"Net force: {F_net} N (Buoy={F_buoy}, Gravity={F_gravity}, Drag={F_drag})")
        return F_net

    def to_dict(self) -> dict:
        """
        Serialize the floater's state to a dictionary.

        Returns:
            dict: Dictionary representation of the floater's state.
        """
        return {
            'volume': self.volume,
            'mass': self.mass,
            'area': self.area,
            'Cd': self.Cd,
            'position': self.position,
            'velocity': self.velocity,
            'is_filled': self.is_filled
        }

    def update(self, dt: float, params: dict, time: float) -> None:
        """
        Update floater's velocity and position over a time step dt using simple physics integration.
        Considers buoyancy, gravity, and drag forces.

        Args:
            dt (float): Time step (s)
            params (dict): Simulation parameters
            time (float): Current simulation time (s)
        """
        if dt <= 0:
            logger.error("Time step dt must be positive.")
            raise ValueError("Time step dt must be positive.")
        F_net = self.force
        a = F_net / self.mass if self.mass > 0 else 0.0
        self.velocity += a * dt
        self.position += self.velocity * dt
        logger.debug(f"Updated Floater: position={self.position}, velocity={self.velocity}, a={a}")
        # TODO: Integrate with chain module for cyclic position reset at top/bottom
        # TODO: Add hooks for H1/H2 effects
