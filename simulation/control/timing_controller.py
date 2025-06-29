"""
Timing Optimization Controller for KPP System
Implements intelligent pulse timing and load coordination for optimal energy transfer.
"""

import logging
import math
from collections import deque
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class FloaterTiming:
    """Timing information for a single floater"""

    floater_id: int
    theta: float  # Current position (radians)
    velocity: float  # Angular velocity (rad/s)
    next_injection_time: float  # Predicted next injection time
    last_injection_time: float  # Last injection timestamp
    injection_efficiency: float  # Recent injection efficiency
    is_filled: bool  # Current fill state


@dataclass
class OptimalTiming:
    """Optimal timing result"""

    target_floater_id: int
    injection_time: float
    expected_torque: float
    expected_efficiency: float
    confidence: float


class TimingController:
    """
    Advanced timing optimization controller for coordinated floater injections.

    Implements predictive control to optimize injection timing based on:
    - Current system state
    - Predicted torque requirements
    - Clutch engagement status
    - Generator load conditions
    """

    def __init__(
        self,
        num_floaters: int = 8,
        prediction_horizon: float = 5.0,
        optimization_window: float = 2.0,
        min_injection_interval: float = 1.0,
        torque_prediction_weight: float = 0.4,
        efficiency_weight: float = 0.3,
        stability_weight: float = 0.3,
    ):
        """
        Initialize timing controller.

        Args:
            num_floaters: Number of floaters in the system
            prediction_horizon: Time horizon for predictions (seconds)
            optimization_window: Time window for optimization (seconds)
            min_injection_interval: Minimum time between injections (seconds)
            torque_prediction_weight: Weight for torque prediction in optimization
            efficiency_weight: Weight for efficiency in optimization
            stability_weight: Weight for system stability in optimization
        """
        self.num_floaters = num_floaters
        self.prediction_horizon = prediction_horizon
        self.optimization_window = optimization_window
        self.min_injection_interval = min_injection_interval

        # Optimization weights
        self.torque_weight = torque_prediction_weight
        self.efficiency_weight = efficiency_weight
        self.stability_weight = stability_weight

        # Floater tracking
        self.floater_positions: List[float] = [0.0] * num_floaters
        self.floater_velocities: List[float] = [0.0] * num_floaters
        self.floater_states: List[FloaterTiming] = []

        # Injection scheduling
        self.injection_schedule: deque = deque(maxlen=100)
        self.optimal_engagement_points: List[float] = []
        self.last_injection_times: List[float] = [-999.0] * num_floaters

        # Performance tracking
        self.injection_history: deque = deque(maxlen=50)
        self.efficiency_history: deque = deque(maxlen=50)
        self.torque_history: deque = deque(maxlen=50)
        # System state
        self.current_time = 0.0
        self.chain_speed = 0.0
        self.generator_load = 0.0
        self.clutch_engaged = False
        self.target_torque = 0.0

        # Control commands storage
        self.last_commands = {}

        # Predictive models
        self.torque_predictor = TorquePredictor()
        self.efficiency_estimator = EfficiencyEstimator()

        logger.info(f"TimingController initialized with {num_floaters} floaters")

    def update(self, system_state: Dict, dt: float) -> Dict:
        """
        Update timing controller and generate optimal injection schedule.

        Args:
            system_state: Current system state
            dt: Time step

        Returns:
            Control commands and timing recommendations
        """
        self.current_time += dt

        # Update system state
        self._update_system_state(system_state)

        # Update floater tracking
        self._update_floater_tracking(system_state)

        # Predict future torque requirements
        torque_prediction = self._predict_torque_requirements()

        # Optimize injection timing
        optimal_timing = self._optimize_injection_timing(torque_prediction)
        # Generate control commands
        control_commands = self._generate_control_commands(optimal_timing)

        # Store commands for pneumatic execution
        self.last_commands = control_commands.copy()

        # Update performance tracking
        self._update_performance_tracking(system_state, control_commands)

        return {
            "timing_controller_output": control_commands,
            "optimal_injection_time": (
                optimal_timing.injection_time if optimal_timing else None
            ),
            "target_floater_id": (
                optimal_timing.target_floater_id if optimal_timing else None
            ),
            "predicted_torque": torque_prediction.get("peak_torque", 0.0),
            "injection_efficiency": (
                optimal_timing.expected_efficiency if optimal_timing else 0.0
            ),
            "timing_confidence": optimal_timing.confidence if optimal_timing else 0.0,
            "controller_status": self._get_controller_status(),
        }

    def _update_system_state(self, system_state: Dict):
        """Update internal system state from simulation"""
        self.chain_speed = system_state.get("chain_speed_rpm", 0.0) * (
            2 * math.pi / 60
        )  # Convert to rad/s
        self.generator_load = system_state.get("power", 0.0)
        self.clutch_engaged = system_state.get("clutch_engaged", False)

        # Extract target torque from electrical system
        if "electrical_output" in system_state:
            self.target_torque = system_state["electrical_output"].get(
                "load_torque_command", 0.0
            )

    def _update_floater_tracking(self, system_state: Dict):
        """Update floater position and state tracking"""
        floaters_data = system_state.get("floaters", [])

        for i, floater_data in enumerate(floaters_data[: self.num_floaters]):
            if i < len(self.floater_states):
                # Update existing floater state
                self.floater_states[i].theta = floater_data.get("theta", 0.0)
                self.floater_states[i].velocity = floater_data.get("velocity", 0.0)
                self.floater_states[i].is_filled = floater_data.get("is_filled", False)
            else:
                # Create new floater state
                self.floater_states.append(
                    FloaterTiming(
                        floater_id=i,
                        theta=floater_data.get("theta", 0.0),
                        velocity=floater_data.get("velocity", 0.0),
                        next_injection_time=self.current_time + 1.0,
                        last_injection_time=-999.0,
                        injection_efficiency=0.0,
                        is_filled=floater_data.get("is_filled", False),
                    )
                )

    def _predict_torque_requirements(self) -> Dict:
        """Predict future torque requirements based on system state"""
        return self.torque_predictor.predict(
            current_time=self.current_time,
            chain_speed=self.chain_speed,
            generator_load=self.generator_load,
            clutch_engaged=self.clutch_engaged,
            floater_states=self.floater_states,
            prediction_horizon=self.prediction_horizon,
        )

    def _optimize_injection_timing(
        self, torque_prediction: Dict
    ) -> Optional[OptimalTiming]:
        """
        Optimize injection timing based on predicted torque requirements.

        Args:
            torque_prediction: Predicted torque requirements

        Returns:
            Optimal timing recommendation or None if no injection needed
        """
        if not self.floater_states:
            return None

        best_timing = None
        best_score = -float("inf")

        # Evaluate each floater for potential injection
        for floater in self.floater_states:
            # Skip if recently injected
            if (
                self.current_time - self.last_injection_times[floater.floater_id]
            ) < self.min_injection_interval:
                continue

            # Skip if already filled
            if floater.is_filled:
                continue

            # Calculate potential injection timing
            injection_time = self._calculate_injection_time(floater, torque_prediction)

            if injection_time is None:
                continue

            # Estimate injection outcomes
            expected_torque = self._estimate_injection_torque(floater, injection_time)
            expected_efficiency = self.efficiency_estimator.estimate_efficiency(
                floater, injection_time, self.chain_speed, self.generator_load
            )

            # Calculate optimization score
            score = self._calculate_optimization_score(
                expected_torque, expected_efficiency, injection_time, torque_prediction
            )

            if score > best_score:
                best_score = score
                best_timing = OptimalTiming(
                    target_floater_id=floater.floater_id,
                    injection_time=injection_time,
                    expected_torque=expected_torque,
                    expected_efficiency=expected_efficiency,
                    confidence=min(1.0, score / 100.0),  # Normalize confidence
                )

        return best_timing

    def _calculate_injection_time(
        self, floater: FloaterTiming, torque_prediction: Dict
    ) -> Optional[float]:
        """Calculate optimal injection time for a specific floater"""
        # Predict when floater will be at optimal position for injection
        optimal_theta = math.pi / 2  # Top of chain for maximum buoyancy effect

        # Calculate angular distance to optimal position
        theta_diff = (optimal_theta - floater.theta) % (2 * math.pi)
        if theta_diff > math.pi:
            theta_diff -= 2 * math.pi

        # Estimate time to reach optimal position
        if abs(floater.velocity) > 1e-6:
            time_to_optimal = theta_diff / floater.velocity
        else:
            time_to_optimal = 0.0

        injection_time = self.current_time + time_to_optimal

        # Ensure injection time is within optimization window
        if injection_time > self.current_time + self.optimization_window:
            return None

        return max(self.current_time, injection_time)

    def _estimate_injection_torque(
        self, floater: FloaterTiming, injection_time: float
    ) -> float:
        """Estimate torque contribution from injection"""
        # Base torque from buoyancy (simplified model)
        base_torque = 1000.0  # N⋅m (typical value)

        # Position-dependent efficiency
        theta_at_injection = floater.theta + floater.velocity * (
            injection_time - self.current_time
        )
        position_efficiency = max(0.1, math.sin(theta_at_injection))

        # Speed-dependent efficiency
        speed_efficiency = min(1.0, max(0.3, 1.0 - abs(self.chain_speed - 5.0) / 10.0))

        return base_torque * position_efficiency * speed_efficiency

    def _calculate_optimization_score(
        self,
        expected_torque: float,
        expected_efficiency: float,
        injection_time: float,
        torque_prediction: Dict,
    ) -> float:
        """Calculate optimization score for injection timing"""
        # Torque matching score
        target_torque = torque_prediction.get("peak_torque", 1000.0)
        torque_score = max(0, 100 - abs(expected_torque - target_torque))

        # Efficiency score
        efficiency_score = expected_efficiency * 100

        # Timing score (prefer earlier injections within window)
        time_delay = injection_time - self.current_time
        timing_score = max(0, 100 - (time_delay / self.optimization_window) * 50)
        # Weighted combination
        total_score = (
            self.torque_weight * torque_score
            + self.efficiency_weight * efficiency_score
            + self.stability_weight * timing_score
        )

        return total_score

    def _generate_control_commands(
        self, optimal_timing: Optional[OptimalTiming]
    ) -> Dict:
        """Generate control commands based on optimal timing"""
        commands = {
            "injection_command": False,
            "target_floater_id": None,
            "injection_pressure": 0.0,
            "injection_duration": 0.0,
            "timing_adjustment": 0.0,
            "pneumatic_control": self._get_pneumatic_control_commands(optimal_timing),
        }

        if optimal_timing and optimal_timing.injection_time <= self.current_time + 0.1:
            # Execute injection
            commands["injection_command"] = True
            commands["target_floater_id"] = optimal_timing.target_floater_id
            commands["injection_pressure"] = self._calculate_injection_pressure(
                optimal_timing
            )
            commands["injection_duration"] = self._calculate_injection_duration(
                optimal_timing
            )

            # Record injection
            self.last_injection_times[optimal_timing.target_floater_id] = (
                self.current_time
            )
            self.injection_schedule.append(
                {
                    "time": self.current_time,
                    "floater_id": optimal_timing.target_floater_id,
                    "expected_torque": optimal_timing.expected_torque,
                    "expected_efficiency": optimal_timing.expected_efficiency,
                }
            )

        return commands

    def _get_pneumatic_control_commands(
        self, optimal_timing: Optional[OptimalTiming]
    ) -> Dict:
        """Get pneumatic control commands for direct system interface"""
        if not optimal_timing:
            return {"action": "none"}

        # Check if injection should be executed now
        time_until_injection = optimal_timing.injection_time - self.current_time

        if abs(time_until_injection) <= 0.1:  # Within execution window
            # Direct pneumatic control commands based on optimal timing
            pneumatic_commands = {
                "action": "inject",
                "target_floater_id": optimal_timing.target_floater_id,
                "injection_time": optimal_timing.injection_time,
                "expected_pressure": self._calculate_injection_pressure(optimal_timing),
                "pressure_boost": min(2.0, optimal_timing.expected_efficiency * 2.0),
                "injection_duration": self._calculate_injection_duration(
                    optimal_timing
                ),
                "confidence": optimal_timing.confidence,
            }
        else:
            # Prepare for future injection
            pneumatic_commands = {
                "action": "prepare",
                "target_floater_id": optimal_timing.target_floater_id,
                "injection_time": optimal_timing.injection_time,
                "time_until_injection": time_until_injection,
                "confidence": optimal_timing.confidence,
            }

        return pneumatic_commands

    def execute_pneumatic_control(self, pneumatic_system, floaters) -> bool:
        """
        Directly execute pneumatic control commands on the pneumatic system.

        Args:
            pneumatic_system: The PneumaticSystem instance
            floaters: List of floater objects

        Returns:
            bool: True if pneumatic action was executed, False otherwise
        """
        if not hasattr(self, "last_commands") or not self.last_commands:
            return False

        pneumatic_commands = self.last_commands.get("pneumatic_control", {})

        if pneumatic_commands.get("action") == "inject":
            target_floater_id = pneumatic_commands.get("target_floater_id")

            # Validate floater ID
            if target_floater_id is not None and 0 <= target_floater_id < len(floaters):
                target_floater = floaters[target_floater_id]

                # Execute injection through pneumatic system
                success = pneumatic_system.trigger_injection(target_floater)

                if success:
                    logger.info(
                        f"TimingController executed pneumatic injection on floater {target_floater_id} at time {self.current_time:.2f}"
                    )

                    # Update floater state tracking
                    if target_floater_id < len(self.floater_states):
                        self.floater_states[target_floater_id].last_injection_time = (
                            self.current_time
                        )
                        self.floater_states[target_floater_id].injection_efficiency = (
                            pneumatic_commands.get("confidence", 0.8)
                        )

                    return True
                else:
                    logger.warning(
                        f"TimingController failed to execute pneumatic injection on floater {target_floater_id}"
                    )

        return False

    def _calculate_injection_pressure(self, timing: OptimalTiming) -> float:
        """Calculate optimal injection pressure"""
        # Base pressure
        base_pressure = 300000.0  # Pa (3 bar)

        # Adjust based on expected efficiency
        pressure_multiplier = 0.5 + 0.5 * timing.expected_efficiency

        return base_pressure * pressure_multiplier

    def _calculate_injection_duration(self, timing: OptimalTiming) -> float:
        """Calculate optimal injection duration"""
        # Base duration
        base_duration = 0.5  # seconds

        # Adjust based on system conditions
        load_factor = min(1.0, self.generator_load / 500000.0)  # Normalize to 500kW
        duration_multiplier = 0.5 + 0.5 * load_factor

        return base_duration * duration_multiplier

    def _update_performance_tracking(self, system_state: Dict, control_commands: Dict):
        """Update performance tracking and learning"""
        # Track injection performance
        if control_commands.get("injection_command", False):
            self.injection_history.append(
                {
                    "time": self.current_time,
                    "floater_id": control_commands["target_floater_id"],
                    "system_state": system_state.copy(),
                }
            )

        # Track system efficiency
        efficiency = system_state.get("overall_efficiency", 0.0)
        if efficiency > 0:
            self.efficiency_history.append(efficiency)

        # Track torque performance
        torque = system_state.get("torque", 0.0)
        if torque > 0:
            self.torque_history.append(torque)

    def _get_controller_status(self) -> Dict:
        """Get controller status and performance metrics"""
        return {
            "active_floaters": len([f for f in self.floater_states if not f.is_filled]),
            "recent_injections": len(self.injection_history),
            "average_efficiency": (
                np.mean(self.efficiency_history) if self.efficiency_history else 0.0
            ),
            "average_torque": (
                np.mean(self.torque_history) if self.torque_history else 0.0
            ),
            "optimization_window_utilization": len(self.injection_schedule)
            / max(1, self.optimization_window),
            "prediction_accuracy": (
                self.torque_predictor.get_accuracy()
                if hasattr(self.torque_predictor, "get_accuracy")
                else 0.0
            ),
        }

    def reset(self):
        """Reset controller state"""
        self.floater_states.clear()
        self.injection_schedule.clear()
        self.injection_history.clear()
        self.efficiency_history.clear()
        self.torque_history.clear()
        self.last_injection_times = [-999.0] * self.num_floaters
        self.current_time = 0.0
        logger.info("TimingController reset")


class TorquePredictor:
    """Predictive model for torque requirements"""

    def __init__(self):
        self.prediction_history = deque(maxlen=100)
        self.accuracy_history = deque(maxlen=50)

    def predict(
        self,
        current_time: float,
        chain_speed: float,
        generator_load: float,
        clutch_engaged: bool,
        floater_states: List[FloaterTiming],
        prediction_horizon: float,
    ) -> Dict:
        """Predict future torque requirements"""

        # Simple prediction model based on current conditions
        base_torque = max(
            100.0, generator_load / 1000.0
        )  # Convert power to approximate torque

        # Adjust for chain speed
        speed_factor = min(2.0, max(0.5, chain_speed / 10.0))
        predicted_torque = base_torque * speed_factor

        # Peak torque estimate
        peak_torque = predicted_torque * 1.5
        # Time to peak
        time_to_peak = prediction_horizon * 0.3

        prediction = {
            "base_torque": base_torque,
            "peak_torque": peak_torque,
            "time_to_peak": time_to_peak,
            "prediction_confidence": 0.8,
            "prediction_horizon": prediction_horizon,
        }

        self.prediction_history.append({"time": current_time, "prediction": prediction})

        return prediction

    def get_accuracy(self) -> float:
        """Get prediction accuracy"""
        if not self.accuracy_history:
            return 0.5
        return float(np.mean(self.accuracy_history))


class EfficiencyEstimator:
    """Efficiency estimation for injection timing"""

    def __init__(self):
        self.efficiency_history = deque(maxlen=100)

    def estimate_efficiency(
        self,
        floater: FloaterTiming,
        injection_time: float,
        chain_speed: float,
        generator_load: float,
    ) -> float:
        """Estimate injection efficiency"""

        # Base efficiency
        base_efficiency = 0.7

        # Position-based efficiency
        position_eff = max(0.3, abs(math.sin(floater.theta)))

        # Speed-based efficiency
        optimal_speed = 5.0  # rad/s
        speed_eff = max(0.5, 1.0 - abs(chain_speed - optimal_speed) / 10.0)

        # Load-based efficiency
        load_factor = min(1.0, generator_load / 500000.0)
        load_eff = 0.5 + 0.5 * load_factor

        total_efficiency = base_efficiency * position_eff * speed_eff * load_eff

        return min(1.0, max(0.1, total_efficiency))
