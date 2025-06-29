"""
H3 Pulse Controller Implementation
Pulse and coast control system for clutch management
"""

import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class PulseController:
    """
    H3 Hypothesis: Pulse Mode Control System

    This class manages:
    - Pulse timing and duration control
    - Clutch engagement/disengagement
    - Duty cycle optimization
    - Coast phase energy recovery
    """

    def __init__(
        self,
        enabled: bool = False,
        pulse_duration: float = 5.0,
        coast_duration: float = 5.0,
        initial_phase: str = "pulse",
    ):
        """
        Initialize pulse control system.

        Args:
            enabled: Whether pulse control is active
            pulse_duration: Duration of pulse phase (seconds)
            coast_duration: Duration of coast phase (seconds)
            initial_phase: Starting phase ('pulse' or 'coast')
        """
        self.enabled = enabled
        self.pulse_duration = pulse_duration
        self.coast_duration = coast_duration

        # Internal state
        self.active = False
        self.current_phase = initial_phase
        self.phase_timer = 0.0
        self.clutch_engaged = True  # Start with clutch engaged
        self.cycle_count = 0

        # Performance tracking
        self.total_pulse_time = 0.0
        self.total_coast_time = 0.0
        self.phase_transitions = 0

        # Calculate duty cycle
        self.duty_cycle = self.pulse_duration / (
            self.pulse_duration + self.coast_duration
        )

        logger.info(
            f"PulseController initialized: enabled={enabled}, "
            f"pulse={pulse_duration}s, coast={coast_duration}s, "
            f"duty_cycle={self.duty_cycle:.2f}"
        )

    def update(
        self,
        current_time: float,
        dt: float,
        system_state: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Update pulse controller state for this time step.

        Args:
            current_time: Current simulation time (seconds)
            dt: Time step (seconds)
            system_state: Optional system state dictionary

        Returns:
            Dictionary with pulse controller status
        """
        if not self.enabled:
            self.active = False
            self.clutch_engaged = True  # Default to engaged when disabled
            return self.get_status()

        self.active = True
        self.phase_timer += dt

        # Check for phase transitions
        if self.current_phase == "pulse" and self.phase_timer >= self.pulse_duration:
            self._switch_to_coast()
        elif self.current_phase == "coast" and self.phase_timer >= self.coast_duration:
            self._switch_to_pulse()

        # Update clutch state based on current phase
        self.clutch_engaged = self.current_phase == "pulse"

        # Update timing statistics
        if self.current_phase == "pulse":
            self.total_pulse_time += dt
        else:
            self.total_coast_time += dt

        logger.debug(
            f"Pulse update: phase={self.current_phase}, "
            f"timer={self.phase_timer:.1f}s, "
            f"clutch={self.clutch_engaged}"
        )

        return self.get_status()

    def _switch_to_coast(self) -> None:
        """Switch from pulse to coast phase."""
        self.current_phase = "coast"
        self.phase_timer = 0.0
        self.phase_transitions += 1
        logger.info(f"Switched to COAST phase (transition #{self.phase_transitions})")

    def _switch_to_pulse(self) -> None:
        """Switch from coast to pulse phase."""
        self.current_phase = "pulse"
        self.phase_timer = 0.0
        self.phase_transitions += 1
        self.cycle_count += 1
        logger.info(f"Switched to PULSE phase (cycle #{self.cycle_count})")

    def force_phase(self, phase: str) -> bool:
        """
        Force controller to specific phase.

        Args:
            phase: Phase to switch to ('pulse' or 'coast')

        Returns:
            True if phase change successful
        """
        if phase not in ["pulse", "coast"]:
            logger.warning(f"Invalid phase: {phase}")
            return False

        if self.current_phase != phase:
            old_phase = self.current_phase
            self.current_phase = phase
            self.phase_timer = 0.0
            self.phase_transitions += 1

            logger.info(f"Forced phase change: {old_phase} -> {phase}")

        return True

    def get_phase_info(self) -> Dict[str, Any]:
        """
        Get detailed phase timing information.

        Returns:
            Dictionary with phase details
        """
        total_time = self.total_pulse_time + self.total_coast_time
        actual_duty_cycle = self.total_pulse_time / max(total_time, 1e-6)

        return {
            "current_phase": self.current_phase,
            "phase_timer": self.phase_timer,
            "time_remaining": self._get_time_remaining(),
            "cycle_count": self.cycle_count,
            "phase_transitions": self.phase_transitions,
            "total_pulse_time": self.total_pulse_time,
            "total_coast_time": self.total_coast_time,
            "actual_duty_cycle": actual_duty_cycle,
            "target_duty_cycle": self.duty_cycle,
        }

    def _get_time_remaining(self) -> float:
        """Get time remaining in current phase."""
        if self.current_phase == "pulse":
            return max(0, self.pulse_duration - self.phase_timer)
        else:
            return max(0, self.coast_duration - self.phase_timer)

    def update_timing(
        self, new_pulse_duration: float, new_coast_duration: float
    ) -> None:
        """
        Update pulse and coast durations.

        Args:
            new_pulse_duration: New pulse duration (seconds)
            new_coast_duration: New coast duration (seconds)
        """
        self.pulse_duration = max(0.1, new_pulse_duration)
        self.coast_duration = max(0.1, new_coast_duration)
        self.duty_cycle = self.pulse_duration / (
            self.pulse_duration + self.coast_duration
        )

        logger.info(
            f"Updated timing: pulse={self.pulse_duration}s, "
            f"coast={self.coast_duration}s, duty_cycle={self.duty_cycle:.3f}"
        )

    def get_clutch_torque_multiplier(self) -> float:
        """
        Get torque multiplier based on clutch engagement.

        Returns:
            Torque multiplier (1.0 for engaged, 0.0 for disengaged)
        """
        if not self.active:
            return 1.0  # Full engagement when pulse control disabled

        return 1.0 if self.clutch_engaged else 0.0

    def get_status(self) -> Dict[str, Any]:
        """
        Get current pulse controller status.

        Returns:
            Status dictionary
        """
        return {
            "enabled": self.enabled,
            "active": self.active,
            "current_phase": self.current_phase,
            "clutch_engaged": self.clutch_engaged,
            "pulse_duration": self.pulse_duration,
            "coast_duration": self.coast_duration,
            "duty_cycle": self.duty_cycle,
            "phase_timer": self.phase_timer,
            "time_remaining": self._get_time_remaining(),
            "cycle_count": self.cycle_count,
            "phase_transitions": self.phase_transitions,
        }
