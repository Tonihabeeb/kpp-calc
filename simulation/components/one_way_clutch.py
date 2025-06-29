"""
One-way clutch (overrunning clutch) for the KPP drivetrain system.
Implements pulse-and-coast operation with selective engagement.
"""

import logging
import math
from typing import Optional

logger = logging.getLogger(__name__)


class OneWayClutch:
    """
    One-way clutch that engages when input speed exceeds output speed,
    and disengages (freewheels) when output speed exceeds input speed.
    This enables pulse-and-coast operation in the KPP drivetrain.
    """

    def __init__(
        self,
        engagement_threshold: float = 0.1,
        disengagement_threshold: float = -0.05,
        max_torque: float = 10000.0,
        engagement_time: float = 0.05,
    ):
        """
        Initialize the one-way clutch.

        Args:
            engagement_threshold (float): Speed difference (rad/s) to engage clutch (input > output)
            disengagement_threshold (float): Speed difference (rad/s) to disengage clutch (input < output)
            max_torque (float): Maximum torque the clutch can transmit (N·m)
            engagement_time (float): Time for smooth engagement transition (s)
        """
        self.engagement_threshold = engagement_threshold
        self.disengagement_threshold = disengagement_threshold
        self.max_torque = max_torque
        self.engagement_time = engagement_time

        # State variables
        self.is_engaged = False
        self.engagement_factor = 0.0  # 0.0 = fully disengaged, 1.0 = fully engaged
        self.input_speed = 0.0  # rad/s
        self.output_speed = 0.0  # rad/s
        self.transmitted_torque = 0.0  # N·m

        # Engagement dynamics
        self.engagement_rate = 1.0 / engagement_time  # Rate of engagement/disengagement

        # Performance tracking
        self.total_engagement_cycles = 0
        self.total_transmitted_energy = 0.0  # J
        self.engagement_losses = 0.0  # W (power loss during engagement)

    def update(
        self, input_speed: float, output_speed: float, input_torque: float, dt: float
    ) -> float:
        """
        Update the clutch state and calculate transmitted torque.

        Args:
            input_speed (float): Input shaft angular velocity (rad/s)
            output_speed (float): Output shaft angular velocity (rad/s)
            input_torque (float): Input torque available (N·m)
            dt (float): Time step (s)

        Returns:
            float: Transmitted torque to output (N·m)
        """
        self.input_speed = input_speed
        self.output_speed = output_speed

        # Calculate speed difference (positive = input faster than output)
        speed_difference = input_speed - output_speed

        # Determine engagement state based on speed difference
        target_engaged = self._should_engage(speed_difference)

        # Update engagement factor with smooth transition
        if target_engaged and not self.is_engaged:
            # Start engaging
            self.is_engaged = True
            self.total_engagement_cycles += 1
            logger.debug(f"Clutch engaging: speed_diff={speed_difference:.3f} rad/s")

        elif not target_engaged and self.is_engaged:
            # Start disengaging
            logger.debug(f"Clutch disengaging: speed_diff={speed_difference:.3f} rad/s")

        # Update engagement factor smoothly
        if target_engaged:
            self.engagement_factor = min(
                1.0, self.engagement_factor + self.engagement_rate * dt
            )
        else:
            self.engagement_factor = max(
                0.0, self.engagement_factor - self.engagement_rate * dt
            )
            if self.engagement_factor <= 0.0:
                self.is_engaged = False

        # Calculate transmitted torque
        self.transmitted_torque = self._calculate_transmitted_torque(
            input_torque, speed_difference
        )

        # Calculate engagement losses (slip losses during partial engagement)
        self._calculate_engagement_losses(speed_difference, dt)

        # Track energy transmission
        transmitted_power = self.transmitted_torque * output_speed
        self.total_transmitted_energy += transmitted_power * dt

        logger.debug(
            f"Clutch: engaged={self.is_engaged}, factor={self.engagement_factor:.3f}, "
            f"torque_in={input_torque:.1f}, torque_out={self.transmitted_torque:.1f}"
        )

        return self.transmitted_torque

    def _should_engage(self, speed_difference: float) -> bool:
        """
        Determine if clutch should be engaged based on speed difference.

        Args:
            speed_difference (float): Input speed - output speed (rad/s)

        Returns:
            bool: True if clutch should engage
        """
        if not self.is_engaged:
            # Engage if input is sufficiently faster than output
            return speed_difference > self.engagement_threshold
        else:
            # Disengage if output becomes faster than input (with hysteresis)
            return speed_difference > self.disengagement_threshold

    def _calculate_transmitted_torque(
        self, input_torque: float, speed_difference: float
    ) -> float:
        """
        Calculate the torque transmitted through the clutch.

        Args:
            input_torque (float): Available input torque (N·m)
            speed_difference (float): Speed difference across clutch (rad/s)

        Returns:
            float: Transmitted torque (N·m)
        """
        if self.engagement_factor <= 0.0:
            # Fully disengaged - no torque transmission
            return 0.0

        # Base transmitted torque proportional to engagement factor
        base_torque = input_torque * self.engagement_factor

        # Apply torque capacity limit
        max_torque_available = self.max_torque * self.engagement_factor
        transmitted_torque = min(abs(base_torque), max_torque_available)

        # Maintain sign of input torque
        if input_torque < 0:
            transmitted_torque = -transmitted_torque

        # Additional damping during engagement to prevent shock loads
        if self.engagement_factor < 1.0 and abs(speed_difference) > 0.1:
            damping_factor = 0.8  # Reduce torque during engagement transients
            transmitted_torque *= damping_factor

        return transmitted_torque

    def _calculate_engagement_losses(self, speed_difference: float, dt: float):
        """
        Calculate power losses due to slip during engagement.

        Args:
            speed_difference (float): Speed difference across clutch (rad/s)
            dt (float): Time step (s)
        """
        if 0.0 < self.engagement_factor < 1.0:
            # Power loss due to slip = torque × speed difference
            slip_loss = abs(self.transmitted_torque * speed_difference)
            self.engagement_losses = slip_loss
        else:
            self.engagement_losses = 0.0

    def get_state(self) -> dict:
        """
        Get current clutch state for monitoring and logging.

        Returns:
            dict: Clutch state information
        """
        return {
            "is_engaged": self.is_engaged,
            "engagement_factor": self.engagement_factor,
            "input_speed_rpm": self.input_speed * 60 / (2 * math.pi),
            "output_speed_rpm": self.output_speed * 60 / (2 * math.pi),
            "speed_difference": self.input_speed - self.output_speed,
            "transmitted_torque": self.transmitted_torque,
            "engagement_losses": self.engagement_losses,
            "total_cycles": self.total_engagement_cycles,
            "total_energy_transmitted": self.total_transmitted_energy / 1000.0,  # kJ
        }

    def reset(self):
        """Reset the clutch to initial conditions."""
        self.is_engaged = False
        self.engagement_factor = 0.0
        self.input_speed = 0.0
        self.output_speed = 0.0
        self.transmitted_torque = 0.0
        self.total_engagement_cycles = 0
        self.total_transmitted_energy = 0.0
        self.engagement_losses = 0.0


class PulseCoastController:
    """
    Controller that coordinates clutch operation with floater injection timing
    to optimize pulse-and-coast operation.
    """

    def __init__(self, clutch: OneWayClutch, pulse_detection_threshold: float = 100.0):
        """
        Initialize the pulse-coast controller.

        Args:
            clutch (OneWayClutch): The clutch to control
            pulse_detection_threshold (float): Torque increase threshold to detect pulse (N·m)
        """
        self.clutch = clutch
        self.pulse_detection_threshold = pulse_detection_threshold

        # State tracking
        self.last_torque = 0.0
        self.pulse_detected = False
        self.coast_phase = False
        self.pulse_count = 0

        # Performance metrics
        self.total_pulse_energy = 0.0  # J
        self.total_coast_energy = 0.0  # J
        self.efficiency_ratio = 0.0

    def update(
        self, input_torque: float, input_speed: float, output_speed: float, dt: float
    ) -> float:
        """
        Update the pulse-coast controller and clutch.

        Args:
            input_torque (float): Input torque from drivetrain (N·m)
            input_speed (float): Input shaft speed (rad/s)
            output_speed (float): Output shaft speed (rad/s)
            dt (float): Time step (s)

        Returns:
            float: Transmitted torque (N·m)
        """
        # Detect torque pulses (floater injections)
        torque_change = input_torque - self.last_torque

        if torque_change > self.pulse_detection_threshold and not self.pulse_detected:
            self.pulse_detected = True
            self.coast_phase = False
            self.pulse_count += 1
            logger.info(f"Pulse detected: torque increase of {torque_change:.1f} N·m")

        elif torque_change < -self.pulse_detection_threshold and self.pulse_detected:
            self.pulse_detected = False
            self.coast_phase = True
            logger.info(
                f"Coast phase initiated: torque decrease of {torque_change:.1f} N·m"
            )

        # Update clutch with current conditions
        transmitted_torque = self.clutch.update(
            input_speed, output_speed, input_torque, dt
        )

        # Track energy in pulse vs coast phases
        power = transmitted_torque * output_speed
        if self.pulse_detected:
            self.total_pulse_energy += power * dt
        elif self.coast_phase:
            self.total_coast_energy += power * dt

        # Calculate efficiency ratio (coast energy / pulse energy)
        if self.total_pulse_energy > 0:
            self.efficiency_ratio = self.total_coast_energy / self.total_pulse_energy

        self.last_torque = input_torque
        return transmitted_torque

    def get_state(self) -> dict:
        """Get controller state for monitoring."""
        state = self.clutch.get_state()
        state.update(
            {
                "pulse_detected": self.pulse_detected,
                "coast_phase": self.coast_phase,
                "pulse_count": self.pulse_count,
                "pulse_energy_kj": self.total_pulse_energy / 1000.0,
                "coast_energy_kj": self.total_coast_energy / 1000.0,
                "efficiency_ratio": self.efficiency_ratio,
            }
        )
        return state
