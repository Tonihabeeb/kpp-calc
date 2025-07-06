"""
Parameter Optimization System for KPP Simulation
Provides automated parameter tuning and optimization for simulation performance.
"""

import json
import logging
import math
from dataclasses import dataclass
from typing import Any, Callable, Dict, Tuple

import numpy as np


@dataclass
class OptimizationParameter:
    """Represents a single optimization parameter."""

    name: str
    current_value: float
    min_value: float
    max_value: float
    step_size: float
    description: str


class ParameterOptimizer:
    """
    Advanced parameter optimization system with multiple optimization strategies.
    Supports grid search, gradient descent, and adaptive optimization.
    """

    def __init__(self, validation_framework=None):
        self.validation_framework = validation_framework
        self.parameters = {}
        self.optimization_history = []
        self.best_configuration = None
        self.performance_metrics = {}

        # Optimization settings
        self.max_iterations = 50
        self.convergence_threshold = 0.001
        self.learning_rate = 0.1

        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def add_parameter(
        self,
        name: str,
        current_value: float,
        min_value: float,
        max_value: float,
        step_size: float,
        description: str = "",
    ):
        """Add a parameter for optimization."""
        param = OptimizationParameter(
            name=name,
            current_value=current_value,
            min_value=min_value,
            max_value=max_value,
            step_size=step_size,
            description=description,
        )
        self.parameters[name] = param
        self.logger.info(f"Added optimization parameter: {name} = {current_value}")

    def setup_default_parameters(self):
        """Set up default optimization parameters for KPP simulation."""

        # Physics engine parameters
        self.add_parameter(
            name="time_step",
            current_value=0.1,
            min_value=0.01,
            max_value=0.5,
            step_size=0.01,
            description="Simulation time step (s)",
        )

        self.add_parameter(
            name="drag_coefficient",
            current_value=0.8,
            min_value=0.3,
            max_value=1.5,
            step_size=0.05,
            description="Floater drag coefficient",
        )

        # Generator parameters
        self.add_parameter(
            name="generator_torque",
            current_value=2000.0,
            min_value=500.0,
            max_value=5000.0,
            step_size=100.0,
            description="Generator torque (Nm)",
        )

        # Event handling parameters
        self.add_parameter(
            name="injection_pressure_factor",
            current_value=1.2,
            min_value=1.0,
            max_value=2.0,
            step_size=0.05,
            description="Injection pressure safety factor",
        )

        self.add_parameter(
            name="event_zone_tolerance",
            current_value=0.1,
            min_value=0.05,
            max_value=0.3,
            step_size=0.01,
            description="Event detection zone tolerance (radians)",
        )

        # Floater parameters
        self.add_parameter(
            name="floater_volume",
            current_value=0.035,
            min_value=0.02,
            max_value=0.05,
            step_size=0.002,
            description="Floater volume (m³)",
        )

        self.logger.info(f"Set up {len(self.parameters)} default optimization parameters")

    def optimize_for_performance(self, simulation_engine, optimization_target: str = "efficiency") -> Dict[str, Any]:
        """
        Optimize parameters for simulation performance.

        Args:
            simulation_engine: SimulationEngine instance to optimize
            optimization_target: Target metric ("efficiency", "stability", "power_output")

        Returns:
            Dict with optimization results
        """
        self.logger.info(f"Starting parameter optimization for {optimization_target}")

        # Define objective function based on target
        objective_function = self._get_objective_function(optimization_target)

        # Run optimization algorithm
        if len(self.parameters) <= 3:
            # Use grid search for small parameter spaces
            result = self._grid_search_optimization(simulation_engine, objective_function)
        else:
            # Use gradient-free optimization for larger spaces
            result = self._adaptive_optimization(simulation_engine, objective_function)

        # Update best configuration
        if result["success"]:
            self.best_configuration = result["best_parameters"]
            self.logger.info(f"Optimization completed successfully. Best score: {result['best_score']:.4f}")
        else:
            self.logger.warning("Optimization failed to converge")

        return result

    def _get_objective_function(self, target: str) -> Callable:
        """Get objective function for optimization target."""

        if target == "efficiency":

            def efficiency_objective(simulation_engine, params):
                # Run simulation and calculate efficiency
                try:
                    # Apply parameters
                    self._apply_parameters(simulation_engine, params)

                    # Run short simulation
                    energy_in, energy_out = self._run_efficiency_test(simulation_engine)

                    # Calculate efficiency (higher is better)
                    efficiency = energy_out / max(energy_in, 1e-6)
                    return min(efficiency, 1.0)  # Cap at 100%

                except Exception as e:
                    self.logger.warning(f"Efficiency test failed: {e}")
                    return 0.0  # Return poor score for failed configurations

            return efficiency_objective

        elif target == "stability":

            def stability_objective(simulation_engine, params):
                # Run simulation and measure stability
                try:
                    self._apply_parameters(simulation_engine, params)

                    # Run stability test
                    stability_score = self._run_stability_test(simulation_engine)
                    return stability_score

                except Exception as e:
                    self.logger.warning(f"Stability test failed: {e}")
                    return 0.0

            return stability_objective

        elif target == "power_output":

            def power_objective(simulation_engine, params):
                # Run simulation and measure power output
                try:
                    self._apply_parameters(simulation_engine, params)

                    # Run power output test
                    avg_power = self._run_power_test(simulation_engine)
                    return avg_power / 1000.0  # Normalize to kW

                except Exception as e:
                    self.logger.warning(f"Power test failed: {e}")
                    return 0.0

            return power_objective

        else:
            raise ValueError(f"Unknown optimization target: {target}")

    def _grid_search_optimization(self, simulation_engine, objective_function) -> Dict[str, Any]:
        """Perform grid search optimization."""
        self.logger.info("Running grid search optimization")

        best_score = -float("inf")
        best_params = {}
        iteration_count = 0

        # Generate parameter combinations
        param_names = list(self.parameters.keys())
        param_ranges = []

        for name in param_names:
            param = self.parameters[name]
            values = np.arange(param.min_value, param.max_value + param.step_size, param.step_size)
            param_ranges.append(values)

        # Limit grid size to prevent excessive computation
        total_combinations = 1
        for r in param_ranges:
            total_combinations *= len(r)

        if total_combinations > 1000:
            self.logger.warning(f"Grid search would require {total_combinations} evaluations. Using sampling.")
            # Sample random combinations instead
            return self._random_search_optimization(simulation_engine, objective_function, 100)

        # Evaluate all combinations
        from itertools import product

        for combination in product(*param_ranges):
            params = dict(zip(param_names, combination))

            score = objective_function(simulation_engine, params)
            iteration_count += 1

            if score > best_score:
                best_score = score
                best_params = params.copy()
                self.logger.info(f"New best score: {best_score:.4f} at iteration {iteration_count}")

            # Store iteration result
            self.optimization_history.append(
                {
                    "iteration": iteration_count,
                    "parameters": params.copy(),
                    "score": score,
                    "is_best": score == best_score,
                }
            )

        return {
            "success": True,
            "method": "grid_search",
            "best_score": best_score,
            "best_parameters": best_params,
            "total_iterations": iteration_count,
            "convergence": True,
        }

    def _random_search_optimization(self, simulation_engine, objective_function, max_evaluations) -> Dict[str, Any]:
        """Perform random search optimization."""
        self.logger.info(f"Running random search optimization with {max_evaluations} evaluations")

        best_score = -float("inf")
        best_params = {}

        for iteration in range(max_evaluations):
            # Generate random parameter values
            params = {}
            for name, param in self.parameters.items():
                random_value = np.random.uniform(param.min_value, param.max_value)
                params[name] = random_value

            score = objective_function(simulation_engine, params)

            if score > best_score:
                best_score = score
                best_params = params.copy()
                self.logger.info(f"New best score: {best_score:.4f} at iteration {iteration + 1}")

            # Store iteration result
            self.optimization_history.append(
                {
                    "iteration": iteration + 1,
                    "parameters": params.copy(),
                    "score": score,
                    "is_best": score == best_score,
                }
            )

        return {
            "success": True,
            "method": "random_search",
            "best_score": best_score,
            "best_parameters": best_params,
            "total_iterations": max_evaluations,
            "convergence": True,
        }

    def _adaptive_optimization(self, simulation_engine, objective_function) -> Dict[str, Any]:
        """Perform adaptive optimization using simulated annealing."""
        self.logger.info("Running adaptive optimization")

        # Initialize with current parameter values
        current_params = {name: param.current_value for name, param in self.parameters.items()}
        current_score = objective_function(simulation_engine, current_params)

        best_params = current_params.copy()
        best_score = current_score

        # Simulated annealing parameters
        initial_temperature = 1.0
        cooling_rate = 0.95
        temperature = initial_temperature

        for iteration in range(self.max_iterations):
            # Generate neighbor solution
            new_params = self._generate_neighbor(current_params, temperature)
            new_score = objective_function(simulation_engine, new_params)

            # Accept or reject based on simulated annealing criteria
            score_diff = new_score - current_score
            accept_probability = 1.0 if score_diff > 0 else math.exp(score_diff / temperature)

            if np.random.random() < accept_probability:
                current_params = new_params.copy()
                current_score = new_score

                if new_score > best_score:
                    best_score = new_score
                    best_params = new_params.copy()
                    self.logger.info(f"New best score: {best_score:.4f} at iteration {iteration + 1}")

            # Cool down
            temperature *= cooling_rate

            # Store iteration result
            self.optimization_history.append(
                {
                    "iteration": iteration + 1,
                    "parameters": current_params.copy(),
                    "score": current_score,
                    "temperature": temperature,
                    "is_best": current_score == best_score,
                }
            )

            # Check convergence
            if iteration > 10:
                recent_scores = [h["score"] for h in self.optimization_history[-10:]]
                score_variance = np.var(recent_scores)
                if score_variance < self.convergence_threshold:
                    self.logger.info(f"Converged after {iteration + 1} iterations")
                    break

        return {
            "success": True,
            "method": "adaptive_simulated_annealing",
            "best_score": best_score,
            "best_parameters": best_params,
            "total_iterations": len(self.optimization_history),
            "convergence": (score_variance < self.convergence_threshold if iteration > 10 else False),
        }

    def _generate_neighbor(self, params: Dict[str, float], temperature: float) -> Dict[str, float]:
        """Generate a neighbor solution for adaptive optimization."""
        new_params = params.copy()

        # Randomly select parameter to modify
        param_name = np.random.choice(list(self.parameters.keys()))
        param = self.parameters[param_name]

        # Generate perturbation proportional to temperature
        max_perturbation = (param.max_value - param.min_value) * temperature * 0.1
        perturbation = np.random.normal(0, max_perturbation)

        new_value = params[param_name] + perturbation
        new_value = max(param.min_value, min(param.max_value, new_value))

        new_params[param_name] = new_value
        return new_params

    def _apply_parameters(self, simulation_engine, params: Dict[str, float]):
        """Apply parameter values to simulation engine."""

        # Physics engine parameters
        if "time_step" in params:
            simulation_engine.physics_engine.params["time_step"] = params["time_step"]

        # Floater parameters
        for floater in simulation_engine.floaters:
            if "drag_coefficient" in params:
                floater.Cd = params["drag_coefficient"]
            if "floater_volume" in params:
                floater.volume = params["floater_volume"]
                # Update mass for consistency
                if floater.state == "heavy":
                    floater.mass = floater.container_mass + 1000 * floater.volume

        # Generator parameters
        if hasattr(simulation_engine, "integrated_drivetrain") and "generator_torque" in params:
            if hasattr(simulation_engine.integrated_drivetrain, "generator"):
                simulation_engine.integrated_drivetrain.generator.max_torque = params["generator_torque"]

        # Event handler parameters
        if hasattr(simulation_engine, "advanced_event_handler"):
            if "injection_pressure_factor" in params:
                simulation_engine.advanced_event_handler.optimization_params["pressure_safety_factor"] = params[
                    "injection_pressure_factor"
                ]
            if "event_zone_tolerance" in params:
                simulation_engine.advanced_event_handler.bottom_zone = params["event_zone_tolerance"]
                simulation_engine.advanced_event_handler.top_zone = params["event_zone_tolerance"]

    def _run_efficiency_test(self, simulation_engine) -> Tuple[float, float]:
        """Run test to measure system efficiency."""
        # Reset energy counters
        if hasattr(simulation_engine, "advanced_event_handler"):
            simulation_engine.advanced_event_handler.total_energy_input = 0.0

        # Run simulation for fixed duration
        test_duration = 30.0  # 30 seconds
        time_step = simulation_engine.physics_engine.params["time_step"]
        steps = int(test_duration / time_step)

        initial_energy = sum([0.5 * f.mass * f.velocity**2 for f in simulation_engine.floaters])

        for _ in range(steps):
            try:
                simulation_engine.step()
            except Exception:
                break  # Stop if simulation becomes unstable

        # Calculate energy metrics
        energy_input = getattr(simulation_engine.advanced_event_handler, "total_energy_input", 0.0)
        final_energy = sum([0.5 * f.mass * f.velocity**2 for f in simulation_engine.floaters])
        energy_output = final_energy - initial_energy

        return max(energy_input, 1.0), max(energy_output, 0.0)

    def _run_stability_test(self, simulation_engine) -> float:
        """Run test to measure system stability."""
        # Track velocity variations over time
        velocity_history = []

        test_duration = 20.0  # 20 seconds
        time_step = simulation_engine.physics_engine.params["time_step"]
        steps = int(test_duration / time_step)

        for _ in range(steps):
            try:
                simulation_engine.step()
                avg_velocity = np.mean([abs(f.velocity) for f in simulation_engine.floaters])
                velocity_history.append(avg_velocity)
            except Exception:
                return 0.0  # Unstable simulation

        if len(velocity_history) < 10:
            return 0.0

        # Calculate stability as inverse of velocity variance
        velocity_variance = np.var(velocity_history)
        stability_score = 1.0 / (1.0 + velocity_variance)

        return float(stability_score)

    def _run_power_test(self, simulation_engine) -> float:
        """Run test to measure average power output."""
        power_history = []

        test_duration = 25.0  # 25 seconds
        time_step = simulation_engine.physics_engine.params["time_step"]
        steps = int(test_duration / time_step)

        for _ in range(steps):
            try:
                simulation_engine.step()

                # Calculate instantaneous power from generator
                if hasattr(simulation_engine, "integrated_drivetrain"):
                    power = getattr(simulation_engine.integrated_drivetrain, "power_output", 0.0)
                    power_history.append(power)
                else:
                    power_history.append(0.0)

            except Exception:
                break

        return float(np.mean(power_history)) if power_history else 0.0

    def save_optimization_results(self, filepath: str):
        """Save optimization results to file."""
        results = {
            "parameters": {
                name: {
                    "current_value": param.current_value,
                    "min_value": param.min_value,
                    "max_value": param.max_value,
                    "description": param.description,
                }
                for name, param in self.parameters.items()
            },
            "best_configuration": self.best_configuration,
            "optimization_history": self.optimization_history,
            "performance_metrics": self.performance_metrics,
        }

        with open(filepath, "w") as f:
            json.dump(results, f, indent=2)

        self.logger.info(f"Optimization results saved to {filepath}")

    def load_optimization_results(self, filepath: str):
        """Load optimization results from file."""
        with open(filepath, "r") as f:
            results = json.load(f)

        # Restore parameters
        for name, param_data in results["parameters"].items():
            self.add_parameter(
                name=name,
                current_value=param_data["current_value"],
                min_value=param_data["min_value"],
                max_value=param_data["max_value"],
                step_size=0.01,  # Default step size
                description=param_data["description"],
            )

        self.best_configuration = results.get("best_configuration")
        self.optimization_history = results.get("optimization_history", [])
        self.performance_metrics = results.get("performance_metrics", {})

        self.logger.info(f"Optimization results loaded from {filepath}")

    def get_optimization_summary(self) -> Dict[str, Any]:
        """Get summary of optimization results."""
        if not self.optimization_history:
            return {"status": "No optimization performed yet"}

        scores = [h["score"] for h in self.optimization_history]

        return {
            "total_iterations": len(self.optimization_history),
            "best_score": max(scores),
            "worst_score": min(scores),
            "average_score": np.mean(scores),
            "score_improvement": max(scores) - scores[0] if len(scores) > 1 else 0,
            "best_parameters": self.best_configuration,
            "convergence_achieved": (
                self.optimization_history[-1].get("convergence", False) if self.optimization_history else False
            ),
        }
