"""
Load Management System for KPP Electrical System
Implements dynamic electrical load adjustment for optimal efficiency and grid stability.
"""

import logging
import math
from collections import deque
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class LoadProfile:
    """Load profile definition"""

    target_power: float
    power_tolerance: float
    ramp_rate: float  # kW/s
    priority: int  # 1 = highest, 10 = lowest
    duration: float  # seconds, -1 = indefinite


@dataclass
class GridConditions:
    """Grid condition monitoring"""

    voltage: float
    frequency: float
    power_factor: float
    grid_stability: float  # 0-1, 1 = stable
    fault_detected: bool


class LoadManager:
    """
    Advanced load management system for optimal electrical efficiency.

    Implements dynamic load adjustment based on:
    - Grid conditions and stability
    - Generator efficiency curves
    - Power electronics capabilities
    - System thermal limits
    - Economic optimization
    """

    def __init__(
        self,
        target_power: float = 500000.0,  # 500 kW
        power_tolerance: float = 0.05,  # 5%
        max_ramp_rate: float = 50000.0,  # 50 kW/s
        efficiency_weight: float = 0.4,
        stability_weight: float = 0.3,
        economic_weight: float = 0.3,
        update_interval: float = 0.1,
    ):  # 100ms updates
        """
        Initialize load manager.

        Args:
            target_power: Target electrical power output (W)
            power_tolerance: Acceptable power deviation (fraction)
            max_ramp_rate: Maximum power change rate (W/s)
            efficiency_weight: Weight for efficiency optimization
            stability_weight: Weight for grid stability
            economic_weight: Weight for economic optimization
            update_interval: Control update interval (seconds)
        """
        self.target_power = target_power
        self.power_tolerance = power_tolerance
        self.max_ramp_rate = max_ramp_rate

        # Optimization weights
        self.efficiency_weight = efficiency_weight
        self.stability_weight = stability_weight
        self.economic_weight = economic_weight

        self.update_interval = update_interval

        # PID Controller parameters
        self.kp = 0.8  # Proportional gain
        self.ki = 0.2  # Integral gain
        self.kd = 0.1  # Derivative gain

        # PID state
        self.error_integral = 0.0
        self.last_error = 0.0
        self.last_update_time = 0.0

        # Load control state
        self.current_load_factor = 0.0
        self.commanded_power = 0.0
        self.actual_power = 0.0
        self.power_setpoint = target_power

        # Load profiles
        self.active_profiles: List[LoadProfile] = []
        self.profile_queue: deque = deque()

        # Performance tracking
        self.power_history: deque = deque(maxlen=100)
        self.efficiency_history: deque = deque(maxlen=100)
        self.grid_conditions_history: deque = deque(maxlen=50)

        # Grid condition monitoring
        self.grid_conditions = GridConditions(
            voltage=480.0,
            frequency=50.0,
            power_factor=0.95,
            grid_stability=1.0,
            fault_detected=False,
        )

        # Load shedding and protection
        self.emergency_load_reduction = 0.0
        self.thermal_derate_factor = 1.0
        self.grid_derate_factor = 1.0

        # Economic optimization
        self.power_price = 0.12  # $/kWh
        self.efficiency_price_multiplier = 1.2

        logger.info(
            f"LoadManager initialized: target={target_power/1000:.1f}kW, tolerance={power_tolerance*100:.1f}%"
        )

    def update(self, system_state: Dict, dt: float) -> Dict:
        """
        Update load management and calculate optimal electrical load.

        Args:
            system_state: Current system state including electrical and mechanical data
            dt: Time step

        Returns:
            Load management commands and status
        """
        self.last_update_time += dt

        # Update grid conditions
        self._update_grid_conditions(system_state)

        # Update system state
        self._update_system_state(system_state)

        # Process load profiles
        self._process_load_profiles(dt)

        # Calculate optimal load
        optimal_load = self._calculate_optimal_load(system_state)

        # Apply PID control
        controlled_load = self._apply_pid_control(optimal_load, dt)

        # Apply safety limits and protection
        final_load = self._apply_protection_limits(controlled_load, system_state)

        # Generate load commands
        load_commands = self._generate_load_commands(final_load, system_state)

        # Update performance tracking
        self._update_performance_tracking(system_state, load_commands)

        return {
            "load_manager_output": load_commands,
            "target_load_factor": final_load,
            "power_setpoint": self.power_setpoint,
            "commanded_power": self.commanded_power,
            "actual_power": self.actual_power,
            "power_error": abs(self.actual_power - self.power_setpoint),
            "grid_stability": self.grid_conditions.grid_stability,
            "efficiency_optimization": self._get_efficiency_score(system_state),
            "economic_optimization": self._get_economic_score(system_state),
            "manager_status": self._get_manager_status(),
        }

    def _update_grid_conditions(self, system_state: Dict):
        """Update grid condition monitoring"""
        electrical_output = system_state.get("electrical_output", {})

        # Update grid conditions from electrical system
        self.grid_conditions.voltage = electrical_output.get("grid_voltage", 480.0)
        self.grid_conditions.frequency = electrical_output.get("grid_frequency", 50.0)
        self.grid_conditions.power_factor = electrical_output.get("power_factor", 0.95)
        self.grid_conditions.fault_detected = electrical_output.get(
            "fault_detected", False
        )

        # Calculate grid stability metric
        voltage_stability = max(
            0.0, 1.0 - abs(self.grid_conditions.voltage - 480.0) / 48.0
        )
        frequency_stability = max(
            0.0, 1.0 - abs(self.grid_conditions.frequency - 50.0) / 3.0
        )
        pf_stability = max(
            0.0, 1.0 - abs(self.grid_conditions.power_factor - 0.95) / 0.2
        )

        self.grid_conditions.grid_stability = min(
            1.0, (voltage_stability + frequency_stability + pf_stability) / 3.0
        )

        # Apply fault detection
        if self.grid_conditions.fault_detected:
            self.grid_conditions.grid_stability *= 0.5

        # Record grid conditions
        self.grid_conditions_history.append(
            {"time": self.last_update_time, "conditions": self.grid_conditions}
        )

    def _update_system_state(self, system_state: Dict):
        """Update internal system state"""
        self.actual_power = system_state.get("power", 0.0)

        # Update load factor from electrical system
        electrical_output = system_state.get("electrical_output", {})
        self.current_load_factor = electrical_output.get("load_factor", 0.0)

        # Update thermal conditions
        generator_temp = electrical_output.get("generator_temperature", 75.0)
        max_temp = 120.0  # °C
        self.thermal_derate_factor = max(
            0.5, 1.0 - max(0, generator_temp - 100.0) / (max_temp - 100.0)
        )

        # Update grid derate factor
        self.grid_derate_factor = self.grid_conditions.grid_stability

    def _process_load_profiles(self, dt: float):
        """Process active load profiles and update setpoints"""
        if not self.active_profiles:
            return

        # Process each active profile
        remaining_profiles = []
        for profile in self.active_profiles:
            profile.duration -= dt

            if profile.duration > 0 or profile.duration < 0:  # Keep indefinite profiles
                remaining_profiles.append(profile)

        self.active_profiles = remaining_profiles

        # Calculate weighted setpoint from active profiles
        if self.active_profiles:
            total_weight = sum(1.0 / max(1, p.priority) for p in self.active_profiles)
            weighted_power = sum(
                p.target_power / max(1, p.priority) for p in self.active_profiles
            )
            self.power_setpoint = weighted_power / total_weight
        else:
            self.power_setpoint = self.target_power

    def _calculate_optimal_load(self, system_state: Dict) -> float:
        """Calculate optimal load factor considering all optimization criteria"""

        # Get current system capabilities
        max_power = self._get_maximum_available_power(system_state)

        # Efficiency optimization
        efficiency_load = self._optimize_for_efficiency(system_state, max_power)

        # Stability optimization
        stability_load = self._optimize_for_stability(system_state, max_power)

        # Economic optimization
        economic_load = self._optimize_for_economics(system_state, max_power)

        # Weighted combination
        optimal_load = (
            self.efficiency_weight * efficiency_load
            + self.stability_weight * stability_load
            + self.economic_weight * economic_load
        )

        # Convert to load factor
        if max_power > 0:
            optimal_load_factor = min(1.0, optimal_load / max_power)
        else:
            optimal_load_factor = 0.0

        return optimal_load_factor

    def _get_maximum_available_power(self, system_state: Dict) -> float:
        """Calculate maximum available power considering all constraints"""
        electrical_output = system_state.get("electrical_output", {})

        # Base generator capacity
        rated_power = electrical_output.get("rated_power", 530000.0)

        # Apply thermal derating
        thermal_limited_power = rated_power * self.thermal_derate_factor

        # Apply grid derating
        grid_limited_power = thermal_limited_power * self.grid_derate_factor

        # Apply mechanical limitations
        mechanical_power = system_state.get("mechanical_power_available", float("inf"))
        mechanical_limited_power = min(grid_limited_power, mechanical_power)

        return mechanical_limited_power

    def _optimize_for_efficiency(self, system_state: Dict, max_power: float) -> float:
        """Optimize load for maximum electrical efficiency"""
        electrical_output = system_state.get("electrical_output", {})

        # Get efficiency curve (simplified model)
        load_factors = np.linspace(0.1, 1.0, 10)
        efficiencies = []

        for lf in load_factors:
            # Typical generator efficiency curve
            if lf < 0.2:
                eff = 0.8 * lf / 0.2  # Linear increase to 80% at 20% load
            elif lf < 0.8:
                eff = (
                    0.8 + 0.14 * (lf - 0.2) / 0.6
                )  # Linear increase to 94% at 80% load
            else:
                eff = (
                    0.94 - 0.04 * (lf - 0.8) / 0.2
                )  # Slight decrease to 90% at 100% load
            efficiencies.append(eff)

        # Find load factor with maximum efficiency
        max_eff_idx = np.argmax(efficiencies)
        optimal_load_factor = load_factors[max_eff_idx]

        return optimal_load_factor * max_power

    def _optimize_for_stability(self, system_state: Dict, max_power: float) -> float:
        """Optimize load for system stability"""
        # Target power setpoint
        target_load = min(self.power_setpoint, max_power)

        # Stability considerations
        mechanical_stability = system_state.get("mechanical_stability", 1.0)

        # Reduce load if mechanical system is unstable
        stability_factor = min(1.0, mechanical_stability + 0.2)

        return target_load * stability_factor

    def _optimize_for_economics(self, system_state: Dict, max_power: float) -> float:
        """Optimize load for economic performance"""
        # Economic optimization (simplified)
        # Higher efficiency = higher economic value

        electrical_output = system_state.get("electrical_output", {})
        current_efficiency = electrical_output.get("system_efficiency", 0.8)

        # Prefer operation at high efficiency points
        economic_multiplier = (
            1.0 + (current_efficiency - 0.8) * self.efficiency_price_multiplier
        )

        economic_target = min(self.power_setpoint * economic_multiplier, max_power)

        return economic_target

    def _apply_pid_control(self, target_load_factor: float, dt: float) -> float:
        """Apply PID control for smooth load adjustments"""
        if dt <= 0:
            return self.current_load_factor

        # Calculate error
        error = target_load_factor - self.current_load_factor

        # Integral term
        self.error_integral += error * dt

        # Prevent integral windup
        integral_limit = 0.5
        self.error_integral = max(
            -integral_limit, min(integral_limit, self.error_integral)
        )

        # Derivative term
        error_derivative = (error - self.last_error) / dt if dt > 0 else 0.0

        # PID output
        pid_output = (
            self.kp * error + self.ki * self.error_integral + self.kd * error_derivative
        )

        # Apply rate limiting
        max_change = (self.max_ramp_rate / self.target_power) * dt
        pid_output = max(-max_change, min(max_change, pid_output))

        # Update for next iteration
        self.last_error = error

        # Apply PID correction
        controlled_load = self.current_load_factor + pid_output

        return max(0.0, min(1.0, controlled_load))

    def _apply_protection_limits(self, load_factor: float, system_state: Dict) -> float:
        """Apply protection limits and safety constraints"""

        # Emergency load reduction
        if self.emergency_load_reduction > 0:
            load_factor *= 1.0 - self.emergency_load_reduction

        # Grid fault protection
        if self.grid_conditions.fault_detected:
            load_factor *= 0.5  # Reduce to 50% during grid faults

        # Thermal protection
        load_factor *= self.thermal_derate_factor

        # Frequency-based load shedding
        freq_deviation = abs(self.grid_conditions.frequency - 50.0)
        if freq_deviation > 1.0:  # >1 Hz deviation
            load_factor *= max(0.2, 1.0 - (freq_deviation - 1.0) / 2.0)

        # Voltage-based load reduction
        voltage_deviation = abs(self.grid_conditions.voltage - 480.0)
        if voltage_deviation > 24.0:  # >5% voltage deviation
            load_factor *= max(0.5, 1.0 - (voltage_deviation - 24.0) / 48.0)

        return max(0.0, min(1.0, load_factor))

    def _generate_load_commands(self, load_factor: float, system_state: Dict) -> Dict:
        """Generate load management commands"""

        # Calculate commanded power
        max_power = self._get_maximum_available_power(system_state)
        self.commanded_power = load_factor * max_power

        # Update current load factor
        self.current_load_factor = load_factor

        commands = {
            "target_load_factor": load_factor,
            "commanded_power": self.commanded_power,
            "power_setpoint": self.power_setpoint,
            "ramp_rate": min(
                self.max_ramp_rate, abs(self.commanded_power - self.actual_power) / 0.1
            ),
            "enable_generator": load_factor > 0.05,
            "enable_grid_connection": not self.grid_conditions.fault_detected,
            "load_shed_amount": self.emergency_load_reduction,
            "thermal_derate": 1.0 - self.thermal_derate_factor,
            "grid_derate": 1.0 - self.grid_derate_factor,
        }

        return commands

    def _update_performance_tracking(self, system_state: Dict, load_commands: Dict):
        """Update performance tracking and metrics"""

        # Track power performance
        self.power_history.append(
            {
                "time": self.last_update_time,
                "target": self.power_setpoint,
                "commanded": self.commanded_power,
                "actual": self.actual_power,
                "error": abs(self.actual_power - self.power_setpoint),
            }
        )

        # Track efficiency
        electrical_output = system_state.get("electrical_output", {})
        efficiency = electrical_output.get("system_efficiency", 0.0)
        if efficiency > 0:
            self.efficiency_history.append(
                {
                    "time": self.last_update_time,
                    "efficiency": efficiency,
                    "load_factor": self.current_load_factor,
                }
            )

    def _get_efficiency_score(self, system_state: Dict) -> float:
        """Calculate efficiency optimization score"""
        electrical_output = system_state.get("electrical_output", {})
        current_efficiency = electrical_output.get("system_efficiency", 0.0)

        # Score based on efficiency relative to maximum possible
        max_efficiency = 0.94  # Peak generator efficiency
        efficiency_score = current_efficiency / max_efficiency

        return min(1.0, efficiency_score)

    def _get_economic_score(self, system_state: Dict) -> float:
        """Calculate economic optimization score"""
        # Economic score based on power output and efficiency
        power_utilization = self.actual_power / self.target_power
        efficiency_score = self._get_efficiency_score(system_state)

        economic_score = 0.6 * power_utilization + 0.4 * efficiency_score

        return min(1.0, economic_score)

    def _get_manager_status(self) -> Dict:
        """Get load manager status and performance metrics"""

        # Calculate average performance
        avg_power_error = 0.0
        avg_efficiency = 0.0

        if self.power_history:
            recent_errors = [p["error"] for p in list(self.power_history)[-10:]]
            avg_power_error = np.mean(recent_errors) if recent_errors else 0.0

        if self.efficiency_history:
            recent_eff = [e["efficiency"] for e in list(self.efficiency_history)[-10:]]
            avg_efficiency = np.mean(recent_eff) if recent_eff else 0.0

        return {
            "active_profiles": len(self.active_profiles),
            "average_power_error": avg_power_error,
            "average_efficiency": avg_efficiency,
            "grid_stability": self.grid_conditions.grid_stability,
            "thermal_derate_active": self.thermal_derate_factor < 1.0,
            "grid_derate_active": self.grid_derate_factor < 1.0,
            "emergency_load_reduction": self.emergency_load_reduction,
            "pid_integral_term": self.error_integral,
            "load_factor_range": {
                "current": self.current_load_factor,
                "minimum": 0.0,
                "maximum": 1.0,
            },
        }

    def add_load_profile(self, profile: LoadProfile):
        """Add a new load profile to the active list"""
        self.active_profiles.append(profile)
        self.active_profiles.sort(key=lambda p: p.priority)  # Sort by priority
        logger.info(
            f"Added load profile: {profile.target_power/1000:.1f}kW, priority={profile.priority}"
        )

    def set_emergency_load_reduction(self, reduction_factor: float):
        """Set emergency load reduction (0.0 = normal, 1.0 = full reduction)"""
        self.emergency_load_reduction = max(0.0, min(1.0, reduction_factor))
        logger.warning(f"Emergency load reduction set to {reduction_factor*100:.1f}%")

    def adjust_target_power(self, new_target: float):
        """Adjust target power setpoint"""
        self.target_power = max(0.0, new_target)
        self.power_setpoint = self.target_power
        logger.info(f"Target power adjusted to {new_target/1000:.1f}kW")

    def reset(self):
        """Reset load manager state"""
        self.current_load_factor = 0.0
        self.commanded_power = 0.0
        self.actual_power = 0.0
        self.power_setpoint = self.target_power

        self.error_integral = 0.0
        self.last_error = 0.0
        self.last_update_time = 0.0

        self.active_profiles.clear()
        self.power_history.clear()
        self.efficiency_history.clear()
        self.grid_conditions_history.clear()

        self.emergency_load_reduction = 0.0
        self.thermal_derate_factor = 1.0
        self.grid_derate_factor = 1.0

        logger.info("LoadManager reset")
