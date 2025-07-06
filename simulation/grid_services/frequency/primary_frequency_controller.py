"""
Primary Frequency Controller

Provides fast frequency response for grid stability through primary frequency control.
Implements droop control with configurable dead band and response characteristics.

Response time: <2 seconds
Dead band: ±0.02 Hz (configurable)
Droop setting: 2-5% (configurable)
Response range: ±10% of rated power
"""

import math
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class PrimaryFrequencyConfig:
    """Configuration for Primary Frequency Control"""

    droop_setting: float = 0.04  # 4% droop
    dead_band: float = 0.02  # ±0.02 Hz
    response_range: float = 0.10  # ±10% of rated power
    response_time_max: float = 2.0  # 2 seconds maximum response time
    nominal_frequency: float = 60.0  # Hz
    enable_response: bool = True

    def validate(self):
        """Validate configuration parameters"""
        assert 0.02 <= self.droop_setting <= 0.05, "Droop setting must be 2-5%"
        assert 0.01 <= self.dead_band <= 0.05, "Dead band must be 0.01-0.05 Hz"
        assert 0.05 <= self.response_range <= 0.20, "Response range must be 5-20%"


class PrimaryFrequencyController:
    """
    Primary Frequency Controller for fast grid frequency response.

    Implements IEEE 1547 compliant primary frequency response with:
    - Fast response (<2 seconds)
    - Configurable droop characteristics
    - Dead band implementation
    - Response limiting and rate control
    """

    def __init__(self, config: Optional[PrimaryFrequencyConfig] = None):
        self.config = config or PrimaryFrequencyConfig()
        self.config.validate()

        # State variables
        self.current_response = 0.0  # Current power response (p.u.)
        self.target_response = 0.0  # Target power response (p.u.)
        self.frequency_history = []  # Frequency measurement history
        self.response_active = False
        self.last_update_time = time.time()

        # Performance tracking
        self.response_count = 0
        self.total_response_time = 0.0
        self.max_response_magnitude = 0.0
        # Rate limiting
        self.max_response_rate = 2.0  # 200% per second max rate (faster for primary response)

    def update(self, grid_frequency: float, dt: float, rated_power: float) -> Dict[str, Any]:
        """
        Update primary frequency control response.

        Args:
            grid_frequency: Current grid frequency (Hz)
            dt: Time step (seconds)
            rated_power: System rated power (MW)

        Returns:
            Dictionary containing control commands and status
        """
        current_time = time.time()

        # Update frequency history
        self.frequency_history.append({"frequency": grid_frequency, "timestamp": current_time})

        # Keep only recent history (last 10 seconds)
        cutoff_time = current_time - 10.0
        self.frequency_history = [entry for entry in self.frequency_history if entry["timestamp"] > cutoff_time]

        if not self.config.enable_response:
            return self._create_response_dict(0.0, "Disabled")

        # Calculate frequency deviation
        frequency_error = grid_frequency - self.config.nominal_frequency

        # Apply dead band
        if abs(frequency_error) <= self.config.dead_band:
            self.target_response = 0.0
            status = "Within dead band"
        else:
            # Calculate droop response: ΔP = -ΔF / droop * response_range
            effective_error = frequency_error - math.copysign(self.config.dead_band, frequency_error)
            self.target_response = -(effective_error / self.config.droop_setting) * self.config.response_range

            # Limit response to configured range
            self.target_response = max(
                -self.config.response_range,
                min(self.config.response_range, self.target_response),
            )

            status = "Active response"
            self.response_active = True

        # Apply rate limiting to smooth response
        response_change = self.target_response - self.current_response
        max_change = self.max_response_rate * dt

        if abs(response_change) > max_change:
            response_change = math.copysign(max_change, response_change)

        self.current_response += response_change

        # Update performance metrics
        if abs(self.current_response) > 0.001:  # 0.1% threshold
            if not hasattr(self, "_response_start_time"):
                self._response_start_time = current_time

            response_time = current_time - self._response_start_time
            if response_time <= self.config.response_time_max:
                self.response_count += 1
                self.total_response_time += response_time
        else:
            if hasattr(self, "_response_start_time"):
                delattr(self, "_response_start_time")

        # Track maximum response
        self.max_response_magnitude = max(self.max_response_magnitude, abs(self.current_response))

        self.last_update_time = current_time

        return self._create_response_dict(self.current_response * rated_power, status)

    def _create_response_dict(self, power_command: float, status: str) -> Dict[str, Any]:
        """Create standardized response dictionary"""
        return {
            "power_command_mw": power_command,
            "response_pu": self.current_response,
            "target_response_pu": self.target_response,
            "status": status,
            "service_type": "primary_frequency_control",
            "response_active": self.response_active,
            "timestamp": self.last_update_time,
        }

    def get_performance_metrics(self) -> Dict[str, float]:
        """Get performance metrics for monitoring and optimization"""
        avg_response_time = self.total_response_time / self.response_count if self.response_count > 0 else 0.0

        return {
            "average_response_time": avg_response_time,
            "response_count": self.response_count,
            "max_response_magnitude": self.max_response_magnitude,
            "current_response": self.current_response,
            "droop_setting": self.config.droop_setting,
            "dead_band": self.config.dead_band,
        }

    def reset(self):
        """Reset controller state"""
        self.current_response = 0.0
        self.target_response = 0.0
        self.frequency_history.clear()
        self.response_active = False
        self.response_count = 0
        self.total_response_time = 0.0
        self.max_response_magnitude = 0.0

        if hasattr(self, "_response_start_time"):
            delattr(self, "_response_start_time")

    def update_configuration(self, new_config: PrimaryFrequencyConfig):
        """Update controller configuration"""
        new_config.validate()
        self.config = new_config

    def is_responding(self) -> bool:
        """Check if controller is actively responding to frequency deviation"""
        return abs(self.current_response) > 0.001  # 0.1% threshold


def create_standard_primary_frequency_controller() -> PrimaryFrequencyController:
    """Create a standard primary frequency controller with typical settings"""
    config = PrimaryFrequencyConfig(
        droop_setting=0.04,  # 4% droop
        dead_band=0.02,  # ±0.02 Hz
        response_range=0.10,  # ±10% response
        response_time_max=2.0,
        nominal_frequency=60.0,
        enable_response=True,
    )
    return PrimaryFrequencyController(config)
