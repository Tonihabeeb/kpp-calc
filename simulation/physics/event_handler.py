"""
Event Handler for KPP Simulation
Manages floater state transitions (injection/venting) and energy tracking.
"""

import logging
import math

from config.config import RHO_WATER, G

logger = logging.getLogger(__name__)


class EventHandler:
    """
    Handles floater state transition events (air injection and venting)
    with proper energy accounting.
    """

    def __init__(self, tank_depth=10.0):
        """
        Initialize event handler.

        Args:
            tank_depth (float): Depth of water tank (m) for pressure calculations
        """
        self.tank_depth = tank_depth
        self.bottom_zone = 0.1  # radians - angular zone for injection
        self.top_zone = 0.1  # radians - angular zone for venting
        self.energy_input = 0.0  # Total compressor energy input (J)

        # Track which floaters have been processed this cycle to avoid double-processing
        self.processed_injection = set()
        self.processed_venting = set()

        logger.info(f"EventHandler initialized with tank_depth={tank_depth}m")

    def handle_injection(self, floater, floater_id=None):
        """
        Handle air injection at bottom of tank.

        Args:
            floater: Floater object to inject air into
            floater_id: Unique identifier for floater (optional)

        Returns:
            bool: True if injection occurred, False otherwise
        """
        # Use floater object id if no explicit id provided
        if floater_id is None:
            floater_id = id(floater)

        # Check if floater is in bottom zone and is heavy
        if self._is_at_bottom(floater) and self._is_heavy(floater):
            # Check if already processed this cycle
            if floater_id not in self.processed_injection:
                # Perform injection
                self._inject_air(floater)

                # Calculate and track energy consumption
                energy_cost = self._calculate_injection_energy(floater)
                self.energy_input += energy_cost

                # Mark as processed
                self.processed_injection.add(floater_id)

                logger.info(
                    f"Air injection: floater_id={floater_id}, "
                    f"energy_cost={energy_cost:.1f}J, "
                    f"total_energy_input={self.energy_input:.1f}J"
                )

                return True

        return False

    def handle_venting(self, floater, floater_id=None):
        """
        Handle air venting at top of tank.

        Args:
            floater: Floater object to vent air from
            floater_id: Unique identifier for floater (optional)

        Returns:
            bool: True if venting occurred, False otherwise
        """
        # Use floater object id if no explicit id provided
        if floater_id is None:
            floater_id = id(floater)

        # Check if floater is in top zone and is light
        if self._is_at_top(floater) and self._is_light(floater):
            # Check if already processed this cycle
            if floater_id not in self.processed_venting:
                # Perform venting
                self._vent_air(floater)

                # Mark as processed
                self.processed_venting.add(floater_id)

                logger.info(f"Air venting: floater_id={floater_id}")

                return True

        return False

    def process_all_events(self, floaters):
        """
        Process injection and venting events for all floaters.

        Args:
            floaters: List of floater objects

        Returns:
            dict: Summary of events processed
        """
        injection_count = 0
        venting_count = 0

        for i, floater in enumerate(floaters):
            # Handle injection
            if self.handle_injection(floater, floater_id=i):
                injection_count += 1

            # Handle venting
            if self.handle_venting(floater, floater_id=i):
                venting_count += 1

        return {
            "injections": injection_count,
            "ventings": venting_count,
            "total_energy_input": self.energy_input,
        }

    def reset_cycle_tracking(self):
        """
        Reset the tracking of processed floaters for a new cycle.
        Call this periodically to allow floaters to be processed again.
        """
        self.processed_injection.clear()
        self.processed_venting.clear()

    def _is_at_bottom(self, floater):
        """Check if floater is in bottom injection zone."""
        angle = self._get_floater_angle(floater)
        return angle < self.bottom_zone

    def _is_at_top(self, floater):
        """Check if floater is in top venting zone."""
        angle = self._get_floater_angle(floater)
        return abs(angle - math.pi) < self.top_zone

    def _get_floater_angle(self, floater):
        """Get normalized angle of floater (0 to 2π)."""
        if hasattr(floater, "angle"):
            return floater.angle % (2 * math.pi)
        elif hasattr(floater, "theta"):
            return floater.theta % (2 * math.pi)
        else:
            logger.warning("Floater has no angle/theta attribute")
            return 0.0

    def _is_heavy(self, floater):
        """Check if floater is in heavy (water-filled) state."""
        if hasattr(floater, "state"):
            return floater.state == "heavy"
        elif hasattr(floater, "is_filled"):
            return not floater.is_filled  # is_filled=True means air-filled (light)
        else:
            # Default assumption based on mass
            container_mass = getattr(floater, "container_mass", 50.0)
            return floater.mass > container_mass * 1.5

    def _is_light(self, floater):
        """Check if floater is in light (air-filled) state."""
        if hasattr(floater, "state"):
            return floater.state == "light"
        elif hasattr(floater, "is_filled"):
            return floater.is_filled  # is_filled=True means air-filled (light)
        else:
            # Default assumption based on mass
            container_mass = getattr(floater, "container_mass", 50.0)
            return floater.mass <= container_mass * 1.5

    def _inject_air(self, floater):
        """Perform air injection state transition."""
        # Update floater state
        if hasattr(floater, "state"):
            floater.state = "light"
        if hasattr(floater, "is_filled"):
            floater.is_filled = True

        # Update floater mass (remove water mass)
        container_mass = getattr(floater, "container_mass", 50.0)
        floater.mass = container_mass

        logger.debug(f"Air injected: new_mass={floater.mass:.1f}kg")

    def _vent_air(self, floater):
        """Perform air venting state transition."""
        # Update floater state
        if hasattr(floater, "state"):
            floater.state = "heavy"
        if hasattr(floater, "is_filled"):
            floater.is_filled = False

        # Update floater mass (add water mass back)
        container_mass = getattr(floater, "container_mass", 50.0)
        volume = getattr(floater, "volume", 0.04)  # m³
        water_mass = RHO_WATER * volume
        floater.mass = container_mass + water_mass

        logger.debug(f"Air vented: new_mass={floater.mass:.1f}kg")

    def _calculate_injection_energy(self, floater):
        """
        Calculate energy required for air injection.

        Args:
            floater: Floater object

        Returns:
            float: Energy required in Joules
        """
        # Pressure at injection depth (Pascal)
        P_atm = 101325  # Pa
        P_depth = P_atm + RHO_WATER * G * self.tank_depth

        # Volume of air to inject (approximately floater volume)
        volume = getattr(floater, "volume", 0.04)  # m³

        # Simple isothermal work calculation: W = P * V
        # More sophisticated: W = P_atm * V * ln(P_depth / P_atm)
        # Using simple approximation for now
        energy_required = P_depth * volume

        logger.debug(
            f"Injection energy: P_depth={P_depth:.0f}Pa, "
            f"volume={volume:.3f}m³, energy={energy_required:.1f}J"
        )

        return energy_required

    def get_energy_summary(self):
        """
        Get summary of energy consumption.

        Returns:
            dict: Energy consumption summary
        """
        return {
            "total_energy_input": self.energy_input,
            "tank_depth": self.tank_depth,
            "injection_pressure": 101325 + RHO_WATER * G * self.tank_depth,
        }
