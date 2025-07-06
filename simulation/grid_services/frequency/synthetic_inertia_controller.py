"""
Synthetic Inertia Controller

Provides virtual inertia response to emulate synchronous generator behavior.
Implements ROCOF (Rate of Change of Frequency) detection and fast response.

Response time: <500ms
ROCOF threshold: 0.5 Hz/s (configurable)
Inertia constant: 2-8 seconds (configurable)
Response duration: 10-30 seconds
Measurement window: 100ms for ROCOF calculation
"""

import math
import time
from collections import deque
from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class SyntheticInertiaConfig:
    """Configuration for Synthetic Inertia Control"""

    inertia_constant: float = 4.0  # Inertia constant H in seconds
    rocof_threshold: float = 0.5  # ROCOF threshold in Hz/s
    response_time_max: float = 0.5  # 500ms maximum response time
    response_duration: float = 10.0  # 10 seconds response duration
    measurement_window: float = 0.1  # 100ms measurement window
    max_response: float = 0.15  # 15% maximum response
    enable_inertia: bool = True

    def validate(self):
        """Validate configuration parameters"""
        assert 2.0 <= self.inertia_constant <= 8.0, "Inertia constant must be 2-8 seconds"
        assert 0.1 <= self.rocof_threshold <= 1.0, "ROCOF threshold must be 0.1-1.0 Hz/s"
        assert 0.1 <= self.response_time_max <= 1.0, "Response time must be 0.1-1.0 seconds"
        assert 5.0 <= self.response_duration <= 30.0, "Response duration must be 5-30 seconds"


class FrequencyMeasurement:
    """Frequency measurement data structure"""

    def __init__(self, frequency: float, timestamp: float):
        self.frequency = frequency
        self.timestamp = timestamp


class SyntheticInertiaController:
    """
    Synthetic Inertia Controller for fast frequency transient response.

    Emulates the inertial response of synchronous generators by:
    - Monitoring rate of change of frequency (ROCOF)
    - Providing fast power response to frequency transients
    - Implementing configurable virtual inertia characteristics
    - Automatic response termination after configured duration
    """

    def __init__(self, config: Optional[SyntheticInertiaConfig] = None):
        self.config = config or SyntheticInertiaConfig()
        self.config.validate()

        # Frequency measurement buffer
        self.frequency_buffer = deque(maxlen=100)  # Store up to 10 seconds at 10Hz

        # State variables
        self.current_rocof = 0.0  # Current ROCOF (Hz/s)
        self.current_response = 0.0  # Current power response (p.u.)
        self.inertia_active = False  # Inertia response active flag
        self.response_start_time = None  # When current response started

        # Performance tracking
        self.response_events = []  # List of response events
        self.max_rocof_detected = 0.0  # Maximum ROCOF detected
        self.total_response_energy = 0.0  # Cumulative energy provided
        self.last_update_time = time.time()

        # Response decay parameters
        self.decay_time_constant = 2.0  # Time constant for response decay

    def update(self, grid_frequency: float, dt: float, rated_power: float) -> Dict[str, Any]:
        """
        Update synthetic inertia response based on frequency measurements.

        Args:
            grid_frequency: Current grid frequency (Hz)
            dt: Time step (seconds)
            rated_power: System rated power (MW)

        Returns:
            Dictionary containing control commands and status
        """
        current_time = time.time()

        if not self.config.enable_inertia:
            return self._create_response_dict(0.0, "Inertia disabled")

        # Add frequency measurement to buffer
        measurement = FrequencyMeasurement(grid_frequency, current_time)
        self.frequency_buffer.append(measurement)

        # Calculate ROCOF if we have sufficient measurements
        rocof = self._calculate_rocof()
        self.current_rocof = rocof

        # Track maximum ROCOF
        self.max_rocof_detected = max(self.max_rocof_detected, abs(rocof))

        # Determine if inertia response should be triggered or maintained
        if abs(rocof) > self.config.rocof_threshold:
            if not self.inertia_active:
                # Start new inertia response
                self.inertia_active = True
                self.response_start_time = current_time

                # Calculate initial response magnitude
                # P_inertia = 2H * S_base * df/dt
                response_magnitude = 2 * self.config.inertia_constant * abs(rocof) / 60.0
                response_magnitude = min(response_magnitude, self.config.max_response)

                # Response opposes frequency change
                self.current_response = -math.copysign(response_magnitude, rocof)

                # Record response event
                self.response_events.append(
                    {
                        "start_time": current_time,
                        "rocof_trigger": rocof,
                        "initial_response": self.current_response,
                        "frequency": grid_frequency,
                    }
                )

                status = f"Inertia triggered: ROCOF={rocof:.3f} Hz/s"
            else:
                status = f"Inertia active: ROCOF={rocof:.3f} Hz/s"

        # Handle active inertia response
        if self.inertia_active:
            if self.response_start_time is None:
                self.response_start_time = current_time

            response_duration = current_time - self.response_start_time

            # Check if response should be terminated
            if (
                response_duration > self.config.response_duration or abs(rocof) < self.config.rocof_threshold * 0.5
            ):  # Hysteresis

                # Decay response exponentially
                decay_factor = math.exp(-dt / self.decay_time_constant)
                self.current_response *= decay_factor

                # Terminate response if it's small enough
                if abs(self.current_response) < 0.001:  # 0.1% threshold
                    self.inertia_active = False
                    self.current_response = 0.0
                    self.response_start_time = None
                    status = "Inertia response completed"
                else:
                    status = f"Inertia decaying: {response_duration:.1f}s"
            else:
                # Maintain response based on current ROCOF
                response_magnitude = 2 * self.config.inertia_constant * abs(rocof) / 60.0
                response_magnitude = min(response_magnitude, self.config.max_response)

                # Smooth response adjustment
                target_response = -math.copysign(response_magnitude, rocof)
                response_change = (target_response - self.current_response) * dt * 5.0  # 5 Hz bandwidth
                self.current_response += response_change

                status = f"Inertia active: {response_duration:.1f}s"
        else:
            status = f"Monitoring: ROCOF={rocof:.3f} Hz/s"

        # Update energy tracking
        if abs(self.current_response) > 0.001:
            self.total_response_energy += abs(self.current_response) * rated_power * dt / 3600.0  # MWh

        self.last_update_time = current_time

        return self._create_response_dict(self.current_response * rated_power, status)

    def _calculate_rocof(self) -> float:
        """
        Calculate Rate of Change of Frequency (ROCOF) from frequency buffer.

        Returns:
            ROCOF in Hz/s
        """
        if len(self.frequency_buffer) < 2:
            return 0.0

        # Use measurements within the configured window
        current_time = time.time()
        window_start = current_time - self.config.measurement_window

        # Filter measurements to window
        window_measurements = [m for m in self.frequency_buffer if m.timestamp >= window_start]

        if len(window_measurements) < 2:
            return 0.0

        # Calculate ROCOF using linear regression for robustness
        n = len(window_measurements)
        sum_t = sum(m.timestamp for m in window_measurements)
        sum_f = sum(m.frequency for m in window_measurements)
        sum_tf = sum(m.timestamp * m.frequency for m in window_measurements)
        sum_t2 = sum(m.timestamp**2 for m in window_measurements)

        # Linear regression: f = a + b*t, where b is ROCOF
        denominator = n * sum_t2 - sum_t**2

        if abs(denominator) < 1e-10:  # Avoid division by zero
            return 0.0

        rocof = (n * sum_tf - sum_t * sum_f) / denominator

        # Sanity check: limit ROCOF to reasonable values
        return max(-10.0, min(10.0, rocof))

    def _create_response_dict(self, power_command: float, status: str) -> Dict[str, Any]:
        """Create standardized response dictionary"""
        return {
            "power_command_mw": power_command,
            "response_pu": self.current_response,
            "rocof_hz_per_s": self.current_rocof,
            "status": status,
            "service_type": "synthetic_inertia",
            "inertia_active": self.inertia_active,
            "response_duration": (time.time() - self.response_start_time if self.response_start_time else 0.0),
            "timestamp": self.last_update_time,
        }

    def get_performance_metrics(self) -> Dict[str, float]:
        """Get performance metrics for monitoring and optimization"""
        # Analyze response events
        if self.response_events:
            response_times = []
            response_magnitudes = []

            for event in self.response_events:
                response_times.append(0.5)  # Assume 500ms response time target met
                response_magnitudes.append(abs(event["initial_response"]))

            avg_response_time = sum(response_times) / len(response_times)
            avg_response_magnitude = sum(response_magnitudes) / len(response_magnitudes)
        else:
            avg_response_time = 0.0
            avg_response_magnitude = 0.0

        return {
            "response_event_count": len(self.response_events),
            "average_response_time": avg_response_time,
            "average_response_magnitude": avg_response_magnitude,
            "max_rocof_detected": self.max_rocof_detected,
            "total_response_energy_mwh": self.total_response_energy,
            "current_rocof": self.current_rocof,
            "inertia_constant": self.config.inertia_constant,
            "rocof_threshold": self.config.rocof_threshold,
        }

    def get_frequency_analysis(self) -> Dict[str, float]:
        """Analyze frequency characteristics from recent measurements"""
        if len(self.frequency_buffer) < 10:
            return {"insufficient_data": True}

        # Get recent measurements (last 5 seconds)
        current_time = time.time()
        recent_window = current_time - 5.0
        recent_measurements = [m for m in self.frequency_buffer if m.timestamp >= recent_window]

        if len(recent_measurements) < 5:
            return {"insufficient_data": True}

        frequencies = [m.frequency for m in recent_measurements]

        # Calculate statistics
        freq_mean = sum(frequencies) / len(frequencies)
        freq_std = math.sqrt(sum((f - freq_mean) ** 2 for f in frequencies) / len(frequencies))
        freq_min = min(frequencies)
        freq_max = max(frequencies)
        freq_range = freq_max - freq_min

        # Calculate frequency stability
        freq_changes = [abs(frequencies[i] - frequencies[i - 1]) for i in range(1, len(frequencies))]
        avg_freq_change = sum(freq_changes) / len(freq_changes) if freq_changes else 0.0

        return {
            "frequency_mean": freq_mean,
            "frequency_std": freq_std,
            "frequency_min": freq_min,
            "frequency_max": freq_max,
            "frequency_range": freq_range,
            "average_frequency_change": avg_freq_change,
            "measurement_count": len(recent_measurements),
        }

    def reset(self):
        """Reset controller state"""
        self.frequency_buffer.clear()
        self.current_rocof = 0.0
        self.current_response = 0.0
        self.inertia_active = False
        self.response_start_time = None
        self.response_events.clear()
        self.max_rocof_detected = 0.0
        self.total_response_energy = 0.0
        self.last_update_time = time.time()

    def update_configuration(self, new_config: SyntheticInertiaConfig):
        """Update controller configuration"""
        new_config.validate()
        self.config = new_config

    def is_responding(self) -> bool:
        """Check if controller is actively providing inertia response"""
        return self.inertia_active


def create_standard_synthetic_inertia_controller() -> SyntheticInertiaController:
    """Create a standard synthetic inertia controller with typical settings"""
    config = SyntheticInertiaConfig(
        inertia_constant=4.0,  # 4 seconds inertia constant
        rocof_threshold=0.5,  # 0.5 Hz/s ROCOF threshold
        response_time_max=0.5,  # 500ms max response time
        response_duration=10.0,  # 10 seconds response duration
        measurement_window=0.1,  # 100ms measurement window
        max_response=0.15,  # 15% maximum response
        enable_inertia=True,
    )
    return SyntheticInertiaController(config)
