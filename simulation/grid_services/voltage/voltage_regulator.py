"""
Voltage Regulator

Provides automatic voltage regulation (AVR) services for maintaining voltage
stability at the point of interconnection through reactive power control.

Response time: <500ms for fast voltage changes
Voltage range: 0.95-1.05 p.u.
Reactive power capacity: ±30% of rated power
Dead band: ±1% of nominal voltage
Droop: 2-5% typical
"""

import math
import time
from collections import deque
from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class VoltageRegulatorConfig:
    """Configuration for Voltage Regulator"""

    reactive_capacity: float = 0.30  # ±30% of rated power
    voltage_deadband: float = 0.01  # ±1% voltage dead band
    droop_setting: float = 0.03  # 3% droop
    response_time_ms: float = 500.0  # 500ms response time
    voltage_range_min: float = 0.95  # Minimum voltage (p.u.)
    voltage_range_max: float = 1.05  # Maximum voltage (p.u.)
    enable_regulation: bool = True
    filter_time_constant: float = 0.1  # 100ms filter

    def validate(self):
        """Validate configuration parameters"""
        assert 0.20 <= self.reactive_capacity <= 0.50, "Reactive capacity must be 20-50%"
        assert 0.005 <= self.voltage_deadband <= 0.02, "Voltage deadband must be 0.5-2%"
        assert 0.02 <= self.droop_setting <= 0.06, "Droop setting must be 2-6%"
        assert 100.0 <= self.response_time_ms <= 1000.0, "Response time must be 100-1000ms"


class VoltageRegulator:
    """
    Voltage Regulator for automatic voltage regulation and reactive power control.

    Implements IEEE 1547 compliant voltage regulation with:
    - Deadband and droop characteristics
    - Fast response to voltage variations
    - Reactive power injection/absorption
    - Performance monitoring and validation
    """

    def __init__(self, config: Optional[VoltageRegulatorConfig] = None):
        self.config = config or VoltageRegulatorConfig()
        self.config.validate()

        # State variables
        self.measured_voltage = 1.0  # Current voltage measurement (p.u.)
        self.voltage_reference = 1.0  # Voltage reference setpoint (p.u.)
        self.reactive_power_output = 0.0  # Current reactive power output (p.u.)
        self.regulation_active = False

        # Filtering for voltage measurement
        self.voltage_filter = 1.0
        self.alpha = 1.0 - math.exp(-1.0 / (self.config.filter_time_constant * 60.0))  # Filter coefficient

        # Voltage history for performance tracking
        self.voltage_history = deque(maxlen=1000)  # Store ~16 minutes at 1Hz
        self.reactive_power_history = deque(maxlen=1000)

        # Performance metrics
        self.regulation_count = 0
        self.voltage_violations = 0
        self.total_regulation_time = 0.0
        self.last_update_time = time.time()

    def update(self, voltage_pu: float, dt: float, rated_power: float) -> Dict[str, Any]:
        """
        Update voltage regulator with current voltage measurement.

        Args:
            voltage_pu: Measured voltage (p.u.)
            dt: Time step (seconds)
            rated_power: System rated power (MW)

        Returns:
            Dictionary containing control commands and status
        """
        current_time = time.time()

        if not self.config.enable_regulation:
            return self._create_response_dict(0.0, "Voltage regulation disabled", rated_power)

        # Input validation
        if voltage_pu < 0.5 or voltage_pu > 1.5:
            return self._create_response_dict(0.0, "Invalid voltage measurement", rated_power)

        # Apply low-pass filter to voltage measurement
        self.voltage_filter = (1 - self.alpha) * self.voltage_filter + self.alpha * voltage_pu
        self.measured_voltage = self.voltage_filter

        # Calculate voltage error relative to reference
        voltage_error = self.measured_voltage - self.voltage_reference

        # Apply deadband
        if abs(voltage_error) <= self.config.voltage_deadband:
            voltage_error = 0.0
            self.regulation_active = False
            status = "Within deadband"
        else:
            # Apply deadband offset
            if voltage_error > 0:
                voltage_error -= self.config.voltage_deadband
            else:
                voltage_error += self.config.voltage_deadband

            self.regulation_active = True
            status = "Voltage regulation active"

        # Calculate reactive power response using droop characteristic
        # Negative sign: voltage low → inject reactive power (positive Q)
        if abs(voltage_error) > 0:
            reactive_power_cmd = -voltage_error / self.config.droop_setting
        else:
            reactive_power_cmd = 0.0

        # Limit reactive power to available capacity
        reactive_power_cmd = max(
            -self.config.reactive_capacity,
            min(self.config.reactive_capacity, reactive_power_cmd),
        )

        # Apply rate limiting based on response time
        max_rate = self.config.reactive_capacity / (self.config.response_time_ms / 1000.0)
        rate_change = reactive_power_cmd - self.reactive_power_output

        if abs(rate_change) > max_rate * dt:
            rate_change = math.copysign(max_rate * dt, rate_change)

        self.reactive_power_output += rate_change

        # Check for voltage limit violations
        if (
            self.measured_voltage < self.config.voltage_range_min
            or self.measured_voltage > self.config.voltage_range_max
        ):
            self.voltage_violations += 1
            status += f" - Voltage violation: {self.measured_voltage:.3f} p.u."

        # Store history for performance analysis
        self.voltage_history.append(
            {
                "voltage": self.measured_voltage,
                "voltage_reference": self.voltage_reference,
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
        if self.regulation_active:
            self.regulation_count += 1
            self.total_regulation_time += dt

        self.last_update_time = current_time

        return self._create_response_dict(self.reactive_power_output, status, rated_power)

    def set_voltage_reference(self, voltage_reference: float):
        """Set voltage reference setpoint"""
        if 0.95 <= voltage_reference <= 1.05:
            self.voltage_reference = voltage_reference
        else:
            raise ValueError("Voltage reference must be between 0.95 and 1.05 p.u.")

    def _create_response_dict(self, reactive_power_pu: float, status: str, rated_power: float) -> Dict[str, Any]:
        """Create standardized response dictionary"""
        return {
            "reactive_power_pu": reactive_power_pu,
            "reactive_power_mvar": reactive_power_pu * rated_power,
            "measured_voltage": self.measured_voltage,
            "voltage_reference": self.voltage_reference,
            "voltage_error": self.measured_voltage - self.voltage_reference,
            "status": status,
            "service_type": "voltage_regulation",
            "regulation_active": self.regulation_active,
            "timestamp": self.last_update_time,
        }

    def get_performance_metrics(self) -> Dict[str, float]:
        """Get performance metrics for monitoring and optimization"""
        # Calculate average regulation time
        avg_regulation_time = self.total_regulation_time / self.regulation_count if self.regulation_count > 0 else 0.0

        # Calculate voltage stability metrics
        if len(self.voltage_history) > 1:
            voltages = [entry["voltage"] for entry in self.voltage_history]
            voltage_std = math.sqrt(sum((v - sum(voltages) / len(voltages)) ** 2 for v in voltages) / len(voltages))
            voltage_range = max(voltages) - min(voltages)
        else:
            voltage_std = 0.0
            voltage_range = 0.0

        # Calculate reactive power utilization
        if len(self.reactive_power_history) > 0:
            reactive_powers = [entry["reactive_power"] for entry in self.reactive_power_history]
            max_reactive_utilization = max(abs(q) for q in reactive_powers) / self.config.reactive_capacity
        else:
            max_reactive_utilization = 0.0

        return {
            "average_regulation_time": avg_regulation_time,
            "regulation_count": self.regulation_count,
            "voltage_violations": self.voltage_violations,
            "voltage_stability_std": voltage_std,
            "voltage_range": voltage_range,
            "max_reactive_utilization": max_reactive_utilization,
            "current_voltage": self.measured_voltage,
            "current_reactive_power": self.reactive_power_output,
            "reactive_capacity": self.config.reactive_capacity,
        }

    def reset(self):
        """Reset regulator state"""
        self.measured_voltage = 1.0
        self.voltage_reference = 1.0
        self.reactive_power_output = 0.0
        self.regulation_active = False
        self.voltage_filter = 1.0
        self.voltage_history.clear()
        self.reactive_power_history.clear()
        self.regulation_count = 0
        self.voltage_violations = 0
        self.total_regulation_time = 0.0
        self.last_update_time = time.time()

    def update_configuration(self, new_config: VoltageRegulatorConfig):
        """Update regulator configuration"""
        new_config.validate()
        self.config = new_config
        # Recalculate filter coefficient
        self.alpha = 1.0 - math.exp(-1.0 / (self.config.filter_time_constant * 60.0))

    def is_regulating(self) -> bool:
        """Check if regulator is actively providing voltage support"""
        return self.regulation_active


def create_standard_voltage_regulator() -> VoltageRegulator:
    """Create a standard voltage regulator with typical utility settings"""
    config = VoltageRegulatorConfig(
        reactive_capacity=0.30,  # 30% reactive power capacity
        voltage_deadband=0.01,  # ±1% voltage deadband
        droop_setting=0.03,  # 3% droop
        response_time_ms=500.0,  # 500ms response time
        voltage_range_min=0.95,  # 0.95 p.u. minimum
        voltage_range_max=1.05,  # 1.05 p.u. maximum
        enable_regulation=True,
        filter_time_constant=0.1,  # 100ms filter
    )
    return VoltageRegulator(config)
