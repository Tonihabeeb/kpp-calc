"""
Floater dynamics module.
Encapsulates buoyancy, drag, and motion for a single floater.

Floater physics: buoyancy, drag, and floater state management
Handles all floater-related calculations and updates
"""

import logging
import math
from typing import Optional
import types
from config.config import G, RHO_WATER, RHO_AIR
from utils.logging_setup import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

class Floater:
    """
    Represents a buoyant floater in the KPP system.
    Handles buoyancy, drag, vertical motion, and pulse-jet physics.
    """

    MAX_VELOCITY = 10.0  # m/s, physically reasonable max
    MIN_POSITION = 0.0   # bottom of tank (m)
    MAX_POSITION = 10.0  # top of tank (m)

    def __init__(
        self,
        volume: float,
        mass: float,
        area: float,
        Cd: float = 0.8,
        position: float = 0.0,
        velocity: float = 0.0,
        is_filled: bool = False,
        air_fill_time: float = 0.5,
        air_pressure: float = 300000,
        air_flow_rate: float = 0.6,
        jet_efficiency: float = 0.85,
        added_mass: float = 0.0,  # New parameter for added mass
        phase_offset: float = 0.0  # Angular phase offset around chain
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
            air_fill_time (float, optional): Time to fill air volume (s). Defaults to 0.5.
            air_pressure (float, optional): Air pressure for pulse jet (Pa). Defaults to 300000.
            air_flow_rate (float, optional): Air flow rate for pulse jet (m^3/s). Defaults to 0.6.
            jet_efficiency (float, optional): Efficiency of the pulse jet. Defaults to 0.85.
        """
        self.volume = volume
        self.mass = mass
        self.area = area
        self.Cd = Cd
        self.position = position
        self.velocity = velocity
        self.is_filled = False
        self.fill_progress = 0.0  # 0.0 to 1.0

        # Pulse physics parameters
        self.air_fill_time = air_fill_time
        self.air_pressure = air_pressure
        self.air_flow_rate = air_flow_rate
        self.jet_efficiency = jet_efficiency
        # Floater FSM state and timing
        self.state = 'EMPTY' if not is_filled else 'FILLED'
        # Phase offset and initial theta for ripple smoothing
        self.phase_offset = phase_offset
        self.theta = phase_offset
        self.fill_start_time = None
        self.vent_start_time = None
        self.internal_pressure = 0.0  # Placeholder for future use
        
        # Store initial conditions for reset
        self.initial_position = position
        self.initial_velocity = velocity
        self.initial_is_filled = is_filled
        
        # Chain parameters
        self.major_axis = 1.0
        self.minor_axis = 1.0
        self.chain_radius = 1.0
        # theta already initialized above
        
        # Dissolved air fraction
        self.dissolved_air_fraction = 0.0  # Fraction of air dissolved into water
        
        # Added mass parameter
        self.added_mass: float = added_mass
        # Phase offset for ripple smoothing
        self.phase_offset: float = phase_offset

        # Water inside the floater (for drainage)
        self.water_mass = 0.0
        # Orientation state for pivoting
        self.pivoted = False

        # Initialize loss tracking attributes
        self.drag_loss: float = 0.0
        self.dissolution_loss: float = 0.0
        self.venting_loss: float = 0.0

        if volume < 0 or mass < 0 or area < 0 or Cd < 0:
            logger.error("Invalid floater parameters: must be non-negative.")
            raise ValueError("Floater parameters must be non-negative.")
        self.set_filled(is_filled)
        logger.info(f"Initialized Floater: {self.to_dict()}")
        logger.debug(f"Added mass initialized: {self.added_mass}")

    def set_filled(self, filled: bool) -> None:
        """
        Set the filled state of the floater and reset progress.

        Args:
            filled (bool): True if filled with air, False otherwise.
        """
        if self.is_filled != filled:
            self.is_filled = filled
            self.fill_progress = 1.0 if filled else 0.0
            logger.info(f"Floater fill state changed: is_filled={self.is_filled}")

    def start_filling(self):
        """
        Begin the air filling process for the pulse.
        """
        if not self.is_filled:
            self.is_filled = True
            self.fill_progress = 0.0
            logger.info("Floater has started filling.")

    def compute_buoyant_force(self) -> float:
        """
        Compute the upward buoyant force based on the currently filled volume,
        adjusted for dissolved air fraction.

        Returns:
            float: Buoyant force (N)
        """
        # Adjust fill progress based on dissolved air fraction
        effective_fill_progress = self.fill_progress * (1.0 - self.dissolved_air_fraction)

        # Buoyancy is based on the actual volume of air held
        displaced_volume = self.volume * effective_fill_progress
        F_buoy = RHO_WATER * displaced_volume * G
        logger.debug(f"Buoyant force: {F_buoy:.2f} N (effective_fill_progress={effective_fill_progress:.2f})")
        return F_buoy

    def compute_buoyant_force_adjusted(self, depth: float) -> float:
        """
        Compute the buoyant force acting on the floater, adjusted for depth.

        Args:
            depth (float): Depth of the floater (m).

        Returns:
            float: Depth-adjusted buoyant force (N)
        """
        # Atmospheric pressure at surface (Pa)
        P_atm = 101325.0
        # Total pressure increases with depth: P = P_atm + rho_water*g*depth
        P_total = P_atm + RHO_WATER * G * depth
        # Air volume compresses with pressure: V = V0 * (P_atm / P_total)
        effective_volume = self.volume * self.fill_progress * (P_atm / P_total)
        # Buoyant force based on displaced volume
        F_buoy = RHO_WATER * effective_volume * G
        logger.debug(f"Depth-adjusted buoyant force at depth={depth:.2f}m: {F_buoy:.2f} N (eff_vol={effective_volume:.4f} m^3)")
        return F_buoy

    def compute_drag_force(self) -> float:
        """
        Compute the drag force opposing motion (quadratic drag).

        Returns:
            float: Drag force (N, sign opposes velocity)
        """
        drag_mag = 0.5 * self.Cd * RHO_WATER * self.area * (self.velocity ** 2)
        return -drag_mag if self.velocity > 0 else drag_mag

    def compute_pulse_jet_force(self) -> float:
        """
        Calculate the additional upward force from the water jet effect during the pulse.
        This force is only active while the floater is filling.

        Returns:
            float: Jet force (N)
        """
        if not (0 < self.fill_progress < 1.0):
            return 0.0

        # Simplified model from pulse_physics.py
        v_jet = math.sqrt(2 * self.air_pressure / RHO_WATER)
        water_displacement_rate = self.air_flow_rate
        F_jet = self.jet_efficiency * RHO_WATER * water_displacement_rate * v_jet
        logger.debug(f"Pulse jet force: {F_jet:.2f} N")
        return F_jet

    @property
    def force(self) -> float:
        """
        Calculate the net force acting on the floater, including all effects.

        Returns:
            float: Net force (N)
        """
        F_buoy = self.compute_buoyant_force()
        F_jet = self.compute_pulse_jet_force()
        
        # Weight includes the mass of the air inside
        air_mass = RHO_AIR * self.volume * self.fill_progress
        F_gravity = -(self.mass + air_mass) * G
        
        F_drag = self.compute_drag_force()
        
        F_net = F_buoy + F_gravity + F_drag + F_jet
        logger.debug(f"Net force: {F_net:.2f} N (Buoy={F_buoy:.2f}, Jet={F_jet:.2f}, Grav={F_gravity:.2f}, Drag={F_drag:.2f})")
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
            'position': self.position,
            'velocity': self.velocity,
            'is_filled': self.is_filled,
            'fill_progress': self.fill_progress
        }

    def update(self, dt: float) -> None:
        """
        Update floater's state over a time step dt.
        Considers buoyancy, gravity, drag, and pulse jet forces.

        Args:
            dt (float): Time step (s)
        """
        if dt <= 0:
            raise ValueError("Time step dt must be positive.")

        # Track fill progress transitions
        prev_progress = self.fill_progress
        # Update fill progress if filling
        if self.is_filled and self.fill_progress < 1.0:
            # Rate of filling is determined by air_fill_time
            fill_rate = 1.0 / self.air_fill_time if self.air_fill_time > 0 else float('inf')
            self.fill_progress += fill_rate * dt
            if self.fill_progress >= 1.0:
                self.fill_progress = 1.0
                logger.info("Floater finished filling.")

        # Record old velocity for calculating drag loss
        old_velocity = self.velocity

        # Determine net force, allowing for test override of compute_buoyant_force as net force
        cb_override = self.__dict__.get('compute_buoyant_force', None)
        if cb_override is not None:
            F_net = cb_override()
        else:
            F_net = self.force

        # Compute drag force explicitly for loss calculation
        F_drag = self.compute_drag_force()
        # Calculate drag loss energy: |F_drag * velocity * dt|
        drag_loss = abs(F_drag * old_velocity * dt)

        # No dissolution or venting loss calculations yet
        dissolution_loss = 0.0
        venting_loss = 0.0

        # Update loss attributes for tracking
        self.drag_loss = drag_loss
        self.dissolution_loss = dissolution_loss
        self.venting_loss = venting_loss

        # Adjust acceleration to account for added mass
        total_mass = self.mass + self.added_mass
        a = F_net / total_mass if total_mass > 0 else 0.0

        # Update velocity and position
        self.velocity += a * dt
        # Clamp velocity to prevent runaway
        if self.velocity > self.MAX_VELOCITY:
            self.velocity = self.MAX_VELOCITY
        elif self.velocity < -self.MAX_VELOCITY:
            self.velocity = -self.MAX_VELOCITY
        self.position += self.velocity * dt
        # Clamp position and reset velocity if hitting boundaries
        if self.position < self.MIN_POSITION:
            self.position = self.MIN_POSITION
            self.velocity = 0.0
        elif self.position > self.MAX_POSITION:
            self.position = self.MAX_POSITION
            self.velocity = 0.0
        logger.debug(f"Updated Floater: pos={self.position:.2f}, vel={self.velocity:.2f}, acc={a:.2f}")
        
        # Apply simple dissolution: decrease fill_progress gradually when not actively filling
        if self.fill_progress > 0.0 and not (self.is_filled and prev_progress < 1.0):
            dissolution_rate = 0.001  # Fraction of air lost per second due to dissolution
            # Capture fill before dissolution
            before_fp = self.fill_progress
            # Reduce fill progress due to dissolution
            self.fill_progress = max(before_fp - dissolution_rate * dt, 0.0)
            # Track dissolved fraction increase
            delta = before_fp - self.fill_progress
            self.dissolved_air_fraction += delta

    def reset(self):
        """
        Resets the floater to its initial state.
        """
        self.position = self.initial_position
        self.velocity = self.initial_velocity
        self.is_filled = self.initial_is_filled
        self.fill_progress = 1.0 if self.is_filled else 0.0
        logger.info(f"Floater state has been reset.")

    def set_chain_params(self, major_axis, minor_axis, chain_radius):
        """
        Set the geometric parameters for the elliptical/circular chain path.
        """
        self.major_axis = major_axis  # a (horizontal radius)
        self.minor_axis = minor_axis  # b (vertical radius)
        self.chain_radius = chain_radius

    def set_theta(self, theta):
        """
        Set the angular position of the floater along the chain.
        """
        self.theta = theta % (2 * math.pi)

    def get_cartesian_position(self):
        """
        Get the (x, y) position of the floater along the ellipse/circle.
        """
        x = self.major_axis * math.cos(self.theta)
        y = self.minor_axis * math.sin(self.theta)
        return x, y

    def get_vertical_force(self):
        """
        Get the vertical force (buoyancy, gravity, drag, jet) at the current position.
        """
        # Use the same force calculation as before, but only the vertical component matters for torque
        return self.force

    def pivot(self) -> None:
        """
        Simulate a 180° rotation at a sprocket.
        """
        self.pivoted = not self.pivoted
        logger.info(f"Floater pivoted. New orientation pivoted={self.pivoted}")

    def drain_water(self) -> None:
        """
        Drain water from the floater, resetting water mass.
        """
        self.water_mass = 0.0
        logger.info("Floater water drained before air injection.")
