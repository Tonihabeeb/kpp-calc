"""
Power Factor Controller

Provides power factor control and reactive power optimization for efficient
grid operation and compliance with utility interconnection requirements.

Response time: <1 second
Power factor range: 0.85 leading to 0.85 lagging
Reactive power capacity: ±30% of rated power
Dead band: ±0.02 power factor
Priority: Lower than voltage regulation
"""

import math
import time
from collections import deque
from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class PowerFactorConfig:
    """Configuration for Power Factor Controller"""

    reactive_capacity: float = 0.30  # ±30% of rated power
    power_factor_target: float = 1.0  # Target power factor (unity)
    power_factor_deadband: float = 0.02  # ±0.02 power factor deadband
    power_factor_range_min: float = 0.85  # Minimum allowable power factor
    power_factor_range_max: float = 1.0  # Maximum power factor (unity)
    response_time_s: float = 1.0  # 1 second response time
    enable_control: bool = True
    priority_level: int = 2  # Lower priority than voltage regulation

    def validate(self):
        """Validate configuration parameters"""
        assert 0.20 <= self.reactive_capacity <= 0.50, "Reactive capacity must be 20-50%"
        assert 0.85 <= self.power_factor_target <= 1.0, "Target power factor must be 0.85-1.0"
        assert 0.01 <= self.power_factor_deadband <= 0.05, "Deadband must be 0.01-0.05"
        assert 0.5 <= self.response_time_s <= 5.0, "Response time must be 0.5-5.0 seconds"


class PowerFactorController:
    """
    Power Factor Controller for maintaining desired power factor through
    reactive power adjustment.

    Implements utility-grade power factor control with:
    - Configurable target power factor
    - Deadband operation
    - Coordination with voltage regulation
    - Performance monitoring and optimization
    """

    def __init__(self, config: Optional[PowerFactorConfig] = None):
        self.config = config or PowerFactorConfig()
        self.config.validate()

        # State variables
        self.measured_power_factor = 1.0  # Current power factor measurement
        self.active_power = 0.0  # Current active power output (p.u.)
        self.reactive_power_output = 0.0  # Current reactive power output (p.u.)
        self.control_active = False

        # Power factor history for performance tracking
        self.power_factor_history = deque(maxlen=3600)  # Store 1 hour at 1Hz
        self.reactive_power_history = deque(maxlen=3600)

        # Performance metrics
        self.control_count = 0
        self.power_factor_violations = 0
        self.total_control_time = 0.0
        self.last_update_time = time.time()

        # Control state
        self.enabled = True
        self.coordinated_mode = True  # Coordinate with voltage regulation

    def update(
        self,
        active_power_pu: float,
        reactive_power_pu: float,
        dt: float,
        rated_power: float,
        voltage_regulation_active: bool = False,
    ) -> Dict[str, Any]:
        """
        Update power factor controller with current power measurements.

        Args:
            active_power_pu: Active power output (p.u.)
            reactive_power_pu: Current reactive power (p.u.)
            dt: Time step (seconds)
            rated_power: System rated power (MW)
            voltage_regulation_active: Whether voltage regulation is active

        Returns:
            Dictionary containing control commands and status
        """
        current_time = time.time()

        if not self.config.enable_control or not self.enabled:
            return self._create_response_dict(0.0, "Power factor control disabled", rated_power)

        # Defer to voltage regulation if coordinated mode is active
        if self.coordinated_mode and voltage_regulation_active:
            return self._create_response_dict(0.0, "Deferred to voltage regulation", rated_power)

        # Store current measurements
        self.active_power = active_power_pu

        # Calculate current power factor
        if abs(active_power_pu) > 0.01:  # Minimum power threshold
            apparent_power = math.sqrt(active_power_pu**2 + reactive_power_pu**2)
            if apparent_power > 0:
                self.measured_power_factor = abs(active_power_pu) / apparent_power
                # Determine leading/lagging
                pf_sign = 1.0 if reactive_power_pu <= 0 else -1.0  # Leading is positive
                self.measured_power_factor *= pf_sign
            else:
                self.measured_power_factor = 1.0
        else:
            self.measured_power_factor = 1.0
            self.control_active = False
            return self._create_response_dict(0.0, "Insufficient active power", rated_power)

        # Calculate power factor error
        pf_error = self.config.power_factor_target - abs(self.measured_power_factor)

        # Apply deadband
        if abs(pf_error) <= self.config.power_factor_deadband:
            pf_error = 0.0
            self.control_active = False
            status = "Within deadband"
        else:
            # Apply deadband offset
            if pf_error > 0:
                pf_error -= self.config.power_factor_deadband
            else:
                pf_error += self.config.power_factor_deadband

            self.control_active = True
            status = "Power factor control active"

        # Calculate required reactive power to achieve target power factor
        reactive_power_cmd = 0.0
        if abs(pf_error) > 0 and abs(self.active_power) > 0.01:
            # Calculate reactive power needed for target power factor
            target_pf = self.config.power_factor_target
            if target_pf < 1.0:
                # For non-unity power factor targets
                target_reactive = self.active_power * math.sqrt((1 / target_pf**2) - 1)
                # Determine sign based on whether we need leading or lagging
                if pf_error > 0:  # Need to improve power factor (reduce reactive power)
                    target_reactive = -abs(target_reactive) if reactive_power_pu > 0 else abs(target_reactive)
                else:  # Power factor too high, may need more reactive power
                    target_reactive = abs(target_reactive) if reactive_power_pu <= 0 else -abs(target_reactive)
            else:
                # Unity power factor target
                target_reactive = 0.0

            # Calculate command as difference from current
            reactive_power_cmd = target_reactive - reactive_power_pu

        # Limit reactive power to available capacity
        reactive_power_cmd = max(
            -self.config.reactive_capacity,
            min(self.config.reactive_capacity, reactive_power_cmd),
        )

        # Apply rate limiting based on response time
        max_rate = self.config.reactive_capacity / self.config.response_time_s
        rate_change = reactive_power_cmd - self.reactive_power_output

        if abs(rate_change) > max_rate * dt:
            rate_change = math.copysign(max_rate * dt, rate_change)

        self.reactive_power_output += rate_change

        # Check for power factor violations
        if abs(self.measured_power_factor) < self.config.power_factor_range_min:
            self.power_factor_violations += 1
            status += f" - PF violation: {self.measured_power_factor:.3f}"

        # Store history for performance analysis
        self.power_factor_history.append(
            {
                "power_factor": self.measured_power_factor,
                "target": self.config.power_factor_target,
                "timestamp": current_time,
            }
        )

        self.reactive_power_history.append(
            {
                "reactive_power": self.reactive_power_output,
                "target": reactive_power_cmd,
                "timestamp": current_time,
            }
        )

        # Update performance metrics
        if self.control_active:
            self.control_count += 1
            self.total_control_time += dt

        self.last_update_time = current_time

        return self._create_response_dict(self.reactive_power_output, status, rated_power)

    def set_power_factor_target(self, power_factor_target: float):
        """Set power factor target setpoint"""
        if 0.85 <= power_factor_target <= 1.0:
            self.config.power_factor_target = power_factor_target
        else:
            raise ValueError("Power factor target must be between 0.85 and 1.0")

    def enable_coordination(self, enable: bool):
        """Enable/disable coordination with voltage regulation"""
        self.coordinated_mode = enable

    def _create_response_dict(self, reactive_power_pu: float, status: str, rated_power: float) -> Dict[str, Any]:
        """Create standardized response dictionary"""
        return {
            "reactive_power_pu": reactive_power_pu,
            "reactive_power_mvar": reactive_power_pu * rated_power,
            "measured_power_factor": self.measured_power_factor,
            "power_factor_target": self.config.power_factor_target,
            "power_factor_error": self.config.power_factor_target - abs(self.measured_power_factor),
            "status": status,
            "service_type": "power_factor_control",
            "control_active": self.control_active,
            "timestamp": self.last_update_time,
        }

    def get_performance_metrics(self) -> Dict[str, float]:
        """Get performance metrics for monitoring and optimization"""
        # Calculate average control time
        avg_control_time = self.total_control_time / self.control_count if self.control_count > 0 else 0.0

        # Calculate power factor stability metrics
        if len(self.power_factor_history) > 1:
            power_factors = [entry["power_factor"] for entry in self.power_factor_history]
            pf_mean = sum(power_factors) / len(power_factors)
            pf_std = math.sqrt(sum((pf - pf_mean) ** 2 for pf in power_factors) / len(power_factors))
        else:
            pf_mean = self.measured_power_factor
            pf_std = 0.0

        # Calculate reactive power utilization
        if len(self.reactive_power_history) > 0:
            reactive_powers = [entry["reactive_power"] for entry in self.reactive_power_history]
            max_reactive_utilization = max(abs(q) for q in reactive_powers) / self.config.reactive_capacity
        else:
            max_reactive_utilization = 0.0

        return {
            "average_control_time": avg_control_time,
            "control_count": self.control_count,
            "power_factor_violations": self.power_factor_violations,
            "power_factor_mean": pf_mean,
            "power_factor_std": pf_std,
            "max_reactive_utilization": max_reactive_utilization,
            "current_power_factor": self.measured_power_factor,
            "current_reactive_power": self.reactive_power_output,
            "reactive_capacity": self.config.reactive_capacity,
        }

    def reset(self):
        """Reset controller state"""
        self.measured_power_factor = 1.0
        self.active_power = 0.0
        self.reactive_power_output = 0.0
        self.control_active = False
        self.power_factor_history.clear()
        self.reactive_power_history.clear()
        self.control_count = 0
        self.power_factor_violations = 0
        self.total_control_time = 0.0
        self.last_update_time = time.time()

    def update_configuration(self, new_config: PowerFactorConfig):
        """Update controller configuration"""
        new_config.validate()
        self.config = new_config

    def is_controlling(self) -> bool:
        """Check if controller is actively controlling power factor"""
        return self.control_active


def create_standard_power_factor_controller() -> PowerFactorController:
    """Create a standard power factor controller with typical utility settings"""
    config = PowerFactorConfig(
        reactive_capacity=0.30,  # 30% reactive power capacity
        power_factor_target=1.0,  # Unity power factor target
        power_factor_deadband=0.02,  # ±0.02 power factor deadband
        power_factor_range_min=0.85,  # 0.85 minimum power factor
        power_factor_range_max=1.0,  # Unity maximum
        response_time_s=1.0,  # 1 second response time
        enable_control=True,
        priority_level=2,  # Lower priority than voltage regulation
    )
    return PowerFactorController(config)
