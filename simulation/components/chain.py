"""
Chain & Motion Integration Module for KPP Simulation
Manages the kinematic coupling of multiple floaters on the endless chain loop and their synchronized motion.
"""

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class ChainState:
    """State of the chain system"""

    angular_velocity: float = 0.0  # rad/s
    linear_velocity: float = 0.0  # m/s
    total_length: float = 0.0  # m
    tension: float = 0.0  # N
    total_floaters: int = 0
    active_floaters: int = 0


class Chain:
    """
    Manages the kinematic coupling of multiple floaters on the endless chain loop.

    Handles:
    - Synchronized motion of all floaters
    - Chain dynamics and tension calculation
    - Position tracking and loop transitions
    - Force distribution along the chain
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the chain system.

        Args:
            config (dict): Configuration parameters
        """
        if config is None:
            config = {}

        # Chain geometry
        self.sprocket_radius = config.get("sprocket_radius", 1.0)  # m
        self.tank_height = config.get("tank_height", 10.0)  # m
        self.total_length = 2 * self.tank_height  # Simplified loop length

        # Chain properties
        self.mass_per_meter = config.get("chain_mass_per_meter", 10.0)  # kg/m
        self.total_chain_mass = self.mass_per_meter * self.total_length
        self.elastic_modulus = config.get("chain_elastic_modulus", 200e9)  # Pa
        self.cross_sectional_area = config.get("chain_cross_section", 0.001)  # m²

        # Motion state
        self.angular_velocity = 0.0  # rad/s
        self.linear_velocity = 0.0  # m/s
        self.tension = 0.0  # N

        # Floater tracking
        self.floaters = []
        self.floater_spacing = 0.0  # Will be calculated when floaters are added

        # Performance tracking
        self.total_distance_traveled = 0.0  # m
        self.operating_time = 0.0  # s
        self.max_tension = 0.0  # N

        logger.info(f"Chain initialized: radius={self.sprocket_radius}m, length={self.total_length}m")

    def add_floaters(self, floaters: List) -> None:
        """
        Add floaters to the chain system and establish their initial positions.

        Args:
            floaters (list): List of Floater objects
        """
        self.floaters = floaters
        if len(floaters) > 0:
            self.floater_spacing = self.total_length / len(floaters)

            # Initialize floater positions evenly around the loop
            for i, floater in enumerate(floaters):
                position = i * self.floater_spacing
                floater.set_chain_position(position)

        logger.info(f"Added {len(floaters)} floaters to chain with spacing {self.floater_spacing:.2f}m")

    def advance(self, dt: float, net_force: float = 0.0) -> Dict[str, float]:
        """
        Move the chain and all attached floaters by one time step.

        Args:
            dt (float): Time step (s)
            net_force (float): Net force on the chain (N)

        Returns:
            dict: Chain state information
        """
        # Calculate chain tension from net force and chain dynamics
        self.tension = self._calculate_chain_tension(net_force)

        # Update chain velocity based on forces and inertia
        self._update_chain_velocity(net_force, dt)

        # Move all floaters along the chain
        distance_moved = self.linear_velocity * dt
        self._advance_floaters(distance_moved)

        # Update tracking
        self.total_distance_traveled += abs(distance_moved)
        self.operating_time += dt
        self.max_tension = max(self.max_tension, abs(self.tension))

        return self.get_state()

    def _calculate_chain_tension(self, net_force: float) -> float:
        """
        Calculate chain tension based on net force and chain properties.

        Args:
            net_force (float): Net force on chain (N)

        Returns:
            float: Chain tension (N)
        """
        # Basic tension calculation - can be enhanced with elasticity effects
        base_tension = net_force

        # Add dynamic effects from acceleration
        if len(self.floaters) > 0:
            total_mass = self.total_chain_mass + sum(f.get_total_mass() for f in self.floaters)
            acceleration = net_force / max(total_mass, 1.0)
            dynamic_tension = total_mass * acceleration * 0.1  # Dynamic factor
            tension = base_tension + dynamic_tension
        else:
            tension = base_tension

        return tension

    def _update_chain_velocity(self, net_force: float, dt: float) -> None:
        """
        Update chain velocity based on forces and system inertia.

        Args:
            net_force (float): Net force on chain (N)
            dt (float): Time step (s)
        """
        if len(self.floaters) > 0:
            # Calculate total system mass
            total_mass = self.total_chain_mass + sum(f.get_total_mass() for f in self.floaters)

            # Simple Euler integration for velocity
            acceleration = net_force / max(total_mass, 1.0)
            self.linear_velocity += acceleration * dt

            # Convert to angular velocity
            self.angular_velocity = self.linear_velocity / self.sprocket_radius

            # Apply some drag/damping to prevent unrealistic speeds
            damping_factor = 0.99  # 1% damping per time step
            self.linear_velocity *= damping_factor
            self.angular_velocity *= damping_factor

    def _advance_floaters(self, distance: float) -> None:
        """
        Move all floaters along the chain by the specified distance.

        Args:
            distance (float): Distance to move (m)
        """
        for floater in self.floaters:
            # Get current position
            current_pos = floater.get_chain_position()

            # Calculate new position (wrapping around the loop)
            new_pos = (current_pos + distance) % self.total_length

            # Update floater position
            floater.set_chain_position(new_pos)

            # Update floater's vertical position for physics calculations
            vertical_pos = self._chain_position_to_vertical(new_pos)
            floater.set_vertical_position(vertical_pos)

    def _chain_position_to_vertical(self, chain_position: float) -> float:
        """
        Convert chain position to vertical position in the tank.

        Args:
            chain_position (float): Position along chain (m)

        Returns:
            float: Vertical position in tank (m)
        """
        # Simple mapping for a vertical loop
        if chain_position <= self.tank_height:
            # Ascending side
            return chain_position
        else:
            # Descending side
            return 2 * self.tank_height - chain_position

    def synchronize(self, floaters: List) -> None:
        """
        Re-align or initialize floaters on the chain.

        Args:
            floaters (list): List of Floater objects to synchronize
        """
        self.floaters = floaters
        if len(floaters) > 0:
            self.floater_spacing = self.total_length / len(floaters)

            # Evenly distribute floaters along the loop
            for i, floater in enumerate(floaters):
                position = i * self.floater_spacing
                floater.set_chain_position(position)

                # Set initial vertical position
                vertical_pos = self._chain_position_to_vertical(position)
                floater.set_vertical_position(vertical_pos)

        logger.info(f"Synchronized {len(floaters)} floaters on chain")

    def get_chain_speed(self) -> float:
        """Get current linear chain speed."""
        return self.linear_velocity

    def get_angular_speed(self) -> float:
        """Get current angular speed."""
        return self.angular_velocity

    def get_tension(self) -> float:
        """Get current chain tension."""
        return self.tension

    def get_state(self) -> Dict[str, float]:
        """
        Get comprehensive chain state.

        Returns:
            dict: Chain state data
        """
        return {
            "linear_velocity": self.linear_velocity,
            "angular_velocity": self.angular_velocity,
            "tension": self.tension,
            "total_length": self.total_length,
            "floater_count": len(self.floaters),
            "floater_spacing": self.floater_spacing,
            "total_distance_traveled": self.total_distance_traveled,
            "operating_time": self.operating_time,
            "max_tension": self.max_tension,
            "chain_mass": self.total_chain_mass,
        }

    def reset(self) -> None:
        """Reset chain to initial state."""
        self.angular_velocity = 0.0
        self.linear_velocity = 0.0
        self.tension = 0.0
        self.total_distance_traveled = 0.0
        self.operating_time = 0.0
        self.max_tension = 0.0

        logger.info("Chain system reset to initial state")


def create_standard_kpp_chain(config: Optional[Dict[str, Any]] = None) -> Chain:
    """
    Create a standard KPP chain system with typical parameters.

    Args:
        config (dict): Optional configuration overrides

    Returns:
        Chain: Configured chain system
    """
    default_config = {
        "sprocket_radius": 1.0,
        "tank_height": 10.0,
        "chain_mass_per_meter": 10.0,
        "chain_elastic_modulus": 200e9,
        "chain_cross_section": 0.001,
    }

    if config:
        default_config.update(config)

    return Chain(default_config)
