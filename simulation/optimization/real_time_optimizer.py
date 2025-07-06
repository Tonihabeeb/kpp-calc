"""
Real-time Optimization System for KPP Simulation
Stage 4: Performance optimization, adaptive time stepping, and real-time monitoring
"""

import logging
import math
import statistics
import time
from collections import deque
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class PerformanceProfiler:
    """Performance profiling and monitoring for simulation components"""

    def __init__(self, window_size: int = 100):
        self.window_size = window_size
        self.timings = {
            "physics": deque(maxlen=window_size),
            "events": deque(maxlen=window_size),
            "state_sync": deque(maxlen=window_size),
            "validation": deque(maxlen=window_size),
            "output": deque(maxlen=window_size),
            "total": deque(maxlen=window_size),
        }
        self.counters = {
            "steps": 0,
            "state_changes": 0,
            "validation_failures": 0,
            "optimization_adjustments": 0,
        }

    def record_timing(self, component: str, duration: float):
        """Record timing data for a component"""
        if component in self.timings:
            self.timings[component].append(duration)

    def increment_counter(self, counter: str):
        """Increment a performance counter"""
        if counter in self.counters:
            self.counters[counter] += 1

    def get_stats(self, component: str) -> Dict[str, float]:
        """Get performance statistics for a component"""
        if component not in self.timings or not self.timings[component]:
            return {"avg": 0.0, "min": 0.0, "max": 0.0, "std": 0.0}

        data = list(self.timings[component])
        return {
            "avg": statistics.mean(data),
            "min": min(data),
            "max": max(data),
            "std": statistics.stdev(data) if len(data) > 1 else 0.0,
        }

    def get_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary"""
        summary = {"counters": self.counters.copy(), "timings": {}}

        for component in self.timings:
            summary["timings"][component] = self.get_stats(component)

        # Calculate derived metrics
        if self.timings["total"]:
            total_stats = summary["timings"]["total"]
            summary["fps"] = 1.0 / total_stats["avg"] if total_stats["avg"] > 0 else 0.0
            summary["efficiency"] = (
                1.0 - (summary["timings"]["validation"]["avg"] / total_stats["avg"]) if total_stats["avg"] > 0 else 0.0
            )

        return summary


class AdaptiveTimestepper:
    """Adaptive time stepping for numerical stability and performance"""

    def __init__(self, initial_dt: float = 0.1, min_dt: float = 0.01, max_dt: float = 0.5):
        self.dt = initial_dt
        self.min_dt = min_dt
        self.max_dt = max_dt
        self.target_error = 1e-4
        self.performance_factor = 0.8  # Aim for 80% of target frame time
        self.stability_history = deque(maxlen=10)

    def adapt_timestep(
        self,
        computation_time: float,
        target_frame_time: float,
        error_estimate: Optional[float] = None,
    ) -> float:
        """Adapt timestep based on performance and accuracy"""

        # Performance-based adaptation
        performance_ratio = computation_time / target_frame_time

        if performance_ratio > self.performance_factor:
            # Too slow, increase timestep
            performance_adjustment = min(1.2, 1.0 / performance_ratio)
        elif performance_ratio < self.performance_factor * 0.5:
            # Very fast, decrease timestep for accuracy
            performance_adjustment = 0.9
        else:
            performance_adjustment = 1.0

        # Error-based adaptation (if available)
        error_adjustment = 1.0
        if error_estimate is not None:
            if error_estimate > self.target_error:
                error_adjustment = 0.8  # Reduce timestep for accuracy
            elif error_estimate < self.target_error * 0.1:
                error_adjustment = 1.1  # Increase timestep

        # Combined adjustment
        adjustment = min(performance_adjustment, error_adjustment)
        new_dt = self.dt * adjustment

        # Apply limits
        new_dt = max(self.min_dt, min(self.max_dt, new_dt))

        # Check stability
        self.stability_history.append(abs(new_dt - self.dt) / self.dt)
        if len(self.stability_history) >= 5:
            avg_change = statistics.mean(self.stability_history)
            if avg_change > 0.1:  # Too much variation
                new_dt = (self.dt + new_dt) / 2  # Smooth transition

        self.dt = new_dt
        return self.dt


class NumericalStabilityMonitor:
    """Monitor and handle numerical stability issues"""

    def __init__(self):
        self.max_velocity = 10.0  # m/s
        self.max_acceleration = 50.0  # m/s²
        self.max_force = 100000.0  # N
        self.stability_violations = deque(maxlen=20)

    def check_stability(self, state: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Check system state for numerical stability"""
        violations = []

        # Check velocities
        v_chain = state.get("v_chain", 0.0)
        if abs(v_chain) > self.max_velocity:
            violations.append(f"Chain velocity too high: {v_chain:.2f} m/s")

        # Check accelerations
        a_chain = state.get("a_chain", 0.0)
        if abs(a_chain) > self.max_acceleration:
            violations.append(f"Chain acceleration too high: {a_chain:.2f} m/s²")

        # Check forces
        forces = state.get("forces", {})
        for force_type, force_value in forces.items():
            if abs(force_value) > self.max_force:
                violations.append(f"{force_type} force too high: {force_value:.2f} N")

        # Check for NaN or infinite values
        for key, value in state.items():
            if isinstance(value, (int, float)):
                if math.isnan(value) or math.isinf(value):
                    violations.append(f"Invalid value for {key}: {value}")

        is_stable = len(violations) == 0
        self.stability_violations.append(len(violations))

        return is_stable, violations

    def get_stability_score(self) -> float:
        """Get stability score (0-1, higher is better)"""
        if not self.stability_violations:
            return 1.0

        total_violations = sum(self.stability_violations)
        max_possible = len(self.stability_violations) * 5  # Assume max 5 violations per step
        return max(0.0, 1.0 - (total_violations / max_possible))


class RealTimeOptimizer:
    """Main real-time optimization coordinator"""

    def __init__(self, target_fps: float = 10.0):
        self.target_fps = target_fps
        self.target_frame_time = 1.0 / target_fps

        self.profiler = PerformanceProfiler()
        self.timestepper = AdaptiveTimestepper()
        self.stability_monitor = NumericalStabilityMonitor()

        self.optimization_enabled = True
        self.vectorization_enabled = True
        self.adaptive_timestep_enabled = True

        logger.info(f"RealTimeOptimizer initialized: target_fps={target_fps}, frame_time={self.target_frame_time:.3f}s")

    def optimize_step(self, simulation_state: Dict[str, Any], step_start_time: float) -> Dict[str, Any]:
        """Optimize a single simulation step"""

        recommendations = {
            "continue": True,
            "adjust_timestep": False,
            "new_timestep": self.timestepper.dt,
            "warnings": [],
            "stability_score": 1.0,
        }

        if not self.optimization_enabled:
            return recommendations

        # Check numerical stability
        is_stable, violations = self.stability_monitor.check_stability(simulation_state)
        recommendations["stability_score"] = self.stability_monitor.get_stability_score()

        if not is_stable:
            recommendations["warnings"].extend(violations)
            if len(violations) > 3:  # Critical instability
                recommendations["continue"] = False
                logger.error(f"Critical numerical instability detected: {violations}")

        # Performance optimization
        current_time = time.time()
        step_duration = current_time - step_start_time
        self.profiler.record_timing("total", step_duration)

        # Adaptive timestep adjustment
        if self.adaptive_timestep_enabled:
            error_estimate = self._estimate_integration_error(simulation_state)
            new_dt = self.timestepper.adapt_timestep(step_duration, self.target_frame_time, error_estimate)

            if abs(new_dt - self.timestepper.dt) > 1e-6:
                recommendations["adjust_timestep"] = True
                recommendations["new_timestep"] = new_dt
                self.profiler.increment_counter("optimization_adjustments")

        # Update counters
        self.profiler.increment_counter("steps")

        return recommendations

    def _estimate_integration_error(self, state: Dict[str, Any]) -> float:
        """Estimate integration error for adaptive timestep"""
        # Simple error estimation based on acceleration changes
        a_chain = abs(state.get("a_chain", 0.0))
        v_chain = abs(state.get("v_chain", 0.0))

        # Higher acceleration or velocity suggests need for smaller timestep
        error_estimate = (a_chain * self.timestepper.dt**2 + v_chain * self.timestepper.dt) / 100.0

        return error_estimate

    def optimize_force_calculations(self, floaters: List[Any]) -> Dict[str, Any]:
        """Optimize force calculations using vectorization where possible"""

        if not self.vectorization_enabled or len(floaters) < 2:
            return {"optimized": False, "method": "sequential"}

        # For small numbers of floaters, sequential is often faster
        # due to overhead of vectorization setup
        if len(floaters) < 4:
            return {"optimized": False, "method": "sequential_preferred"}

        try:
            # Batch process similar calculations
            masses = [f.mass for f in floaters]
            volumes = [f.volume for f in floaters]
            positions = [f.angle for f in floaters]

            # This could be extended with numpy for true vectorization
            # For now, we just batch the operations
            return {
                "optimized": True,
                "method": "batched",
                "batch_size": len(floaters),
                "masses": masses,
                "volumes": volumes,
                "positions": positions,
            }

        except Exception as e:
            logger.warning(f"Force calculation optimization failed: {e}")
            return {"optimized": False, "method": "fallback_sequential"}

    def get_performance_report(self) -> Dict[str, Any]:
        """Generate comprehensive performance report"""

        summary = self.profiler.get_performance_summary()

        # Add optimization-specific metrics
        summary["optimization"] = {
            "adaptive_timestep_enabled": self.adaptive_timestep_enabled,
            "vectorization_enabled": self.vectorization_enabled,
            "current_timestep": self.timestepper.dt,
            "stability_score": self.stability_monitor.get_stability_score(),
            "target_fps": self.target_fps,
            "actual_fps": summary.get("fps", 0.0),
        }

        # Performance recommendations
        recommendations = []
        if summary.get("fps", 0.0) < self.target_fps * 0.8:
            recommendations.append("Consider increasing timestep or reducing validation frequency")
        if summary["optimization"]["stability_score"] < 0.9:
            recommendations.append("Numerical stability issues detected - consider parameter tuning")
        if summary["counters"]["validation_failures"] > summary["counters"]["steps"] * 0.1:
            recommendations.append("High validation failure rate - review physics consistency")

        summary["recommendations"] = recommendations

        return summary

    def enable_optimization(self, vectorization: bool = True, adaptive_timestep: bool = True):
        """Enable/disable optimization features"""
        self.optimization_enabled = True
        self.vectorization_enabled = vectorization
        self.adaptive_timestep_enabled = adaptive_timestep

        logger.info(f"Optimization enabled: vectorization={vectorization}, adaptive_timestep={adaptive_timestep}")

    def disable_optimization(self):
        """Disable all optimization features"""
        self.optimization_enabled = False
        logger.info("Real-time optimization disabled")


class DataStreamOptimizer:
    """Optimize data streaming and output for real-time operation"""

    def __init__(self, base_sample_rate: float = 10.0):
        self.base_sample_rate = base_sample_rate
        self.adaptive_sampling = True
        self.compression_enabled = True
        self.priority_data = ["v_chain", "power_output", "efficiency"]
        self.output_buffer = deque(maxlen=1000)

    def optimize_data_output(self, full_data: Dict[str, Any], performance_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize data output based on performance and priorities"""

        if not self.adaptive_sampling:
            return full_data

        # Adjust sampling rate based on performance
        current_fps = performance_metrics.get("fps", self.base_sample_rate)

        if current_fps < self.base_sample_rate * 0.8:
            # Reduce data output frequency
            sample_factor = max(0.5, current_fps / self.base_sample_rate)
        else:
            sample_factor = 1.0

        # Priority-based data selection
        optimized_data = {}

        # Always include priority data
        for key in self.priority_data:
            if key in full_data:
                optimized_data[key] = full_data[key]

        # Include additional data based on performance
        if sample_factor > 0.8:
            # Good performance, include more data
            additional_keys = ["floater_states", "forces", "energy_metrics"]
            for key in additional_keys:
                if key in full_data:
                    optimized_data[key] = full_data[key]

        if sample_factor > 0.9:
            # Excellent performance, include debug data
            debug_keys = ["validation_results", "optimization_metrics"]
            for key in debug_keys:
                if key in full_data:
                    optimized_data[key] = full_data[key]

        # Add metadata
        optimized_data["_metadata"] = {
            "sample_factor": sample_factor,
            "compression_enabled": self.compression_enabled,
            "timestamp": time.time(),
        }

        return optimized_data

    def configure_streaming(
        self,
        sample_rate: float,
        adaptive: bool = True,
        priority_data: Optional[List[str]] = None,
    ):
        """Configure data streaming parameters"""
        self.base_sample_rate = sample_rate
        self.adaptive_sampling = adaptive

        if priority_data:
            self.priority_data = priority_data

        logger.info(f"Data streaming configured: rate={sample_rate}Hz, adaptive={adaptive}")
