"""
Floater dynamics module.
Encapsulates buoyancy, drag, and motion for a single floater.
"""

from typing import Optional
from config.config import G, RHO_WATER

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
        :param volume: Volume of the floater (m^3)
        :param mass: Mass of the floater (kg)
        :param area: Cross-sectional area for drag (m^2)
        :param Cd: Drag coefficient (dimensionless)
        :param position: Initial vertical position (m)
        :param velocity: Initial vertical velocity (m/s)
        :param is_filled: Whether the floater is filled with air (buoyant)
        """

        self.volume = volume
        self.mass = mass
        self.area = area
        self.Cd = Cd
        self.position = position
        self.velocity = velocity
        self.is_filled = is_filled

    def compute_buoyant_force(self) -> float:
        """
        Compute the upward buoyant force on the floater.
        :return: Buoyant force (N)
        """

        displaced_volume = self.volume if self.is_filled else 0.0
        return RHO_WATER * displaced_volume * G

    def compute_drag_force(self) -> float:
        """
        Compute the drag force opposing motion (quadratic drag).
        :return: Drag force (N, sign opposes velocity)
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
        :return: Net force (N)
        """
        F_buoy = self.compute_buoyant_force()
        F_gravity = -self.mass * G
        F_drag = self.compute_drag_force()
        return F_buoy + F_gravity + F_drag

    def to_dict(self) -> dict:
        """
        Serialize the floater's state to a dictionary.
        :return: Dictionary representation of the floater's state.
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
        :param dt: Time step (s)
        :param params: Simulation parameters
        :param time: Current simulation time (s)
        """

        F_net = self.force
        a = F_net / self.mass if self.mass > 0 else 0.0
        self.velocity += a * dt
        self.position += self.velocity * dt
        # TODO: Integrate with chain module for cyclic position reset at top/bottom
        # TODO: Add hooks for H1/H2 effects
