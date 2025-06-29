"""
Integration Manager for KPP Simulation Stage 3
Coordinates validation, optimization, and component integration.
"""

import logging
import os
import sys
import time
from typing import Any, Dict, List, Optional

# Add project path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from simulation.optimization.parameter_optimizer import ParameterOptimizer
from simulation.physics.advanced_event_handler import AdvancedEventHandler

# from simulation.physics.physics_engine import PhysicsEngine  # TODO: Implement PhysicsEngine
from simulation.physics.state_synchronizer import StateSynchronizer
from validation.physics_validation import ValidationFramework


class IntegrationManager:
    """
    Manages integration between validation, optimization, and existing components.
    Provides a unified interface for Stage 3 functionality.
    """

    def __init__(self, simulation_engine: Optional[Any] = None):
        self.simulation_engine = simulation_engine
        self.validation_framework = ValidationFramework()
        self.parameter_optimizer = ParameterOptimizer(self.validation_framework)

        # Integration status
        self.integration_status = {
            "validation_active": False,
            "optimization_active": False,
            "components_integrated": False,
            "last_validation": None,
            "last_optimization": None,
        }

        # Performance tracking
        self.performance_history = []
        self.integration_metrics = {
            "total_validations": 0,
            "successful_validations": 0,
            "total_optimizations": 0,
            "successful_optimizations": 0,
            "component_integration_attempts": 0,
            "successful_integrations": 0,
        }

        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

        # Set up default optimization parameters
        self.parameter_optimizer.setup_default_parameters()

        self.logger.info("Integration Manager initialized")

    def integrate_with_simulation_engine(self, simulation_engine) -> Dict[str, Any]:
        """
        Integrate validation and optimization with existing simulation engine.

        Args:
            simulation_engine: SimulationEngine instance to integrate with

        Returns:
            Dict with integration results
        """
        self.logger.info("Starting simulation engine integration...")
        self.integration_metrics["component_integration_attempts"] += 1

        try:
            self.simulation_engine = simulation_engine

            # Verify required components exist
            integration_checks = self._verify_simulation_components()

            if not integration_checks["all_components_present"]:
                missing = integration_checks["missing_components"]
                self.logger.warning(f"Missing components: {missing}")
                return {
                    "success": False,
                    "reason": "missing_components",
                    "missing_components": missing,
                    "integration_checks": integration_checks,
                }

            # Enhance existing components with validation hooks
            self._add_validation_hooks()

            # Integrate optimization capabilities
            self._integrate_optimization_system()

            # Set up real-time monitoring
            self._setup_real_time_monitoring()

            self.integration_status["components_integrated"] = True
            self.integration_metrics["successful_integrations"] += 1

            self.logger.info("Simulation engine integration completed successfully")

            return {
                "success": True,
                "integration_checks": integration_checks,
                "enhanced_capabilities": [
                    "real_time_validation",
                    "parameter_optimization",
                    "performance_monitoring",
                    "automatic_error_detection",
                ],
            }

        except Exception as e:
            self.logger.error(f"Integration failed: {e}")
            return {"success": False, "reason": "integration_error", "error": str(e)}

    def _verify_simulation_components(self) -> Dict[str, Any]:
        """Verify that all required simulation components are present."""

        if self.simulation_engine is None:
            return {
                "all_components_present": False,
                "present_components": [],
                "missing_components": ["simulation_engine"],
                "advanced_components": [],
                "total_components": 0,
            }

        required_components = {
            "physics_engine": "physics_engine",
            "floaters": "floaters",
            "advanced_event_handler": "event_handler",
            "state_synchronizer": "state_synchronizer",
        }

        present_components = []
        missing_components = []

        for component_name, attribute_name in required_components.items():
            if hasattr(self.simulation_engine, attribute_name):
                present_components.append(component_name)
            else:
                missing_components.append(component_name)

        # Check for optional advanced components
        optional_components = {
            "integrated_drivetrain": "integrated_drivetrain",
            "generator": "generator",
            "grid_services": "grid_services",
        }

        advanced_components = []
        for component_name, attribute_name in optional_components.items():
            if hasattr(self.simulation_engine, attribute_name):
                advanced_components.append(component_name)

        return {
            "all_components_present": len(missing_components) == 0,
            "present_components": present_components,
            "missing_components": missing_components,
            "advanced_components": advanced_components,
            "total_components": len(present_components),
        }

    def _add_validation_hooks(self):
        """Add validation hooks to simulation engine."""

        if self.simulation_engine is None:
            self.logger.error("Cannot add validation hooks: simulation engine is None")
            return

        # Store original step method
        if not hasattr(self.simulation_engine, "_original_step"):
            self.simulation_engine._original_step = self.simulation_engine.step

        # Create enhanced step method with validation
        def enhanced_step(dt=None):
            # Run original step (pass dt if provided)
            if self.simulation_engine is not None:
                if dt is not None:
                    step_result = self.simulation_engine._original_step(dt)
                else:
                    step_result = self.simulation_engine._original_step()

                # Add validation if active
                if self.integration_status["validation_active"]:
                    self._validate_step_results()

                return step_result
            return None

        # Replace step method
        self.simulation_engine.step = enhanced_step

        self.logger.info("Validation hooks added to simulation engine")

    def _integrate_optimization_system(self):
        """Integrate optimization system with simulation engine."""

        if self.simulation_engine is None:
            self.logger.error(
                "Cannot integrate optimization system: simulation engine is None"
            )
            return

        # Add optimization interface to simulation engine
        self.simulation_engine.optimize_parameters = self.optimize_parameters
        self.simulation_engine.get_optimization_status = self.get_optimization_status
        self.simulation_engine.apply_optimal_parameters = self.apply_optimal_parameters

        self.logger.info("Optimization system integrated")

    def _setup_real_time_monitoring(self):
        """Set up real-time performance monitoring."""

        # Initialize monitoring data
        self.monitoring_data = {
            "step_count": 0,
            "validation_count": 0,
            "last_performance_check": time.time(),
            "performance_metrics": {
                "avg_step_time": 0.0,
                "validation_success_rate": 1.0,
                "physics_consistency_score": 1.0,
                "energy_conservation_score": 1.0,
            },
        }

        self.logger.info("Real-time monitoring activated")

    def _validate_step_results(self):
        """Validate results after each simulation step."""
        try:
            # Quick validation checks
            if (
                self.simulation_engine is not None
                and hasattr(self.simulation_engine, "floaters")
                and hasattr(self.simulation_engine, "physics_engine")
            ):

                # Check physics consistency
                chain_velocity = getattr(self.simulation_engine, "chain_velocity", 0.0)
                time_step = self.simulation_engine.physics_engine.params["time_step"]

                validation_result = (
                    self.validation_framework.validate_physics_consistency(
                        self.simulation_engine.floaters, chain_velocity, time_step
                    )
                )

                # Update monitoring metrics
                self.monitoring_data["validation_count"] += 1
                if validation_result["passed"]:
                    self.monitoring_data["performance_metrics"][
                        "physics_consistency_score"
                    ] = (
                        0.99
                        * self.monitoring_data["performance_metrics"][
                            "physics_consistency_score"
                        ]
                        + 0.01 * 1.0
                    )
                else:
                    self.monitoring_data["performance_metrics"][
                        "physics_consistency_score"
                    ] = (
                        0.99
                        * self.monitoring_data["performance_metrics"][
                            "physics_consistency_score"
                        ]
                        + 0.01 * 0.0
                    )
                    self.logger.warning("Physics consistency validation failed")

        except Exception as e:
            self.logger.warning(f"Step validation failed: {e}")

    def run_comprehensive_validation(self) -> Dict[str, Any]:
        """Run comprehensive validation on the integrated system."""
        self.logger.info("Running comprehensive validation...")

        if not self.simulation_engine:
            return {"success": False, "reason": "No simulation engine connected"}

        self.integration_metrics["total_validations"] += 1

        try:
            # Run validation suite
            validation_result = self.validation_framework.run_comprehensive_validation(
                self.simulation_engine
            )

            # Store results
            self.integration_status["last_validation"] = validation_result

            # Check if validation passed
            summary = validation_result["summary"]
            validation_passed = summary["overall_status"] == "PASSED"

            if validation_passed:
                self.integration_metrics["successful_validations"] += 1
                self.integration_status["validation_active"] = True
                self.logger.info(
                    f"Comprehensive validation PASSED ({summary['passed_tests']}/{summary['total_tests']} tests)"
                )
            else:
                self.logger.warning(
                    f"Comprehensive validation FAILED ({summary['passed_tests']}/{summary['total_tests']} tests)"
                )

                # Log recommendations
                for recommendation in validation_result["recommendations"]:
                    self.logger.info(f"Recommendation: {recommendation}")

            return {
                "success": validation_passed,
                "validation_result": validation_result,
                "summary": summary,
                "recommendations": validation_result["recommendations"],
            }

        except Exception as e:
            self.logger.error(f"Comprehensive validation failed: {e}")
            return {"success": False, "reason": "validation_error", "error": str(e)}

    def optimize_parameters(
        self, target: str = "efficiency", max_iterations: int = 50
    ) -> Dict[str, Any]:
        """
        Optimize simulation parameters.

        Args:
            target: Optimization target ("efficiency", "stability", "power_output")
            max_iterations: Maximum optimization iterations

        Returns:
            Dict with optimization results
        """
        self.logger.info(f"Starting parameter optimization for {target}")

        if not self.simulation_engine:
            return {"success": False, "reason": "No simulation engine connected"}

        self.integration_metrics["total_optimizations"] += 1

        try:
            # Set optimization parameters
            self.parameter_optimizer.max_iterations = max_iterations

            # Run optimization
            optimization_result = self.parameter_optimizer.optimize_for_performance(
                self.simulation_engine, target
            )

            # Store results
            self.integration_status["last_optimization"] = optimization_result

            if optimization_result["success"]:
                self.integration_metrics["successful_optimizations"] += 1
                self.integration_status["optimization_active"] = True

                best_score = optimization_result["best_score"]
                total_iterations = optimization_result["total_iterations"]

                self.logger.info(f"Parameter optimization completed successfully")
                self.logger.info(
                    f"Best {target} score: {best_score:.4f} after {total_iterations} iterations"
                )

                # Log best parameters
                best_params = optimization_result["best_parameters"]
                self.logger.info("Best parameters:")
                for param_name, value in best_params.items():
                    self.logger.info(f"  {param_name}: {value:.4f}")
            else:
                self.logger.warning("Parameter optimization failed to converge")

            return optimization_result

        except Exception as e:
            self.logger.error(f"Parameter optimization failed: {e}")
            return {"success": False, "reason": "optimization_error", "error": str(e)}

    def apply_optimal_parameters(self) -> Dict[str, Any]:
        """Apply the best parameters found during optimization."""

        if not self.parameter_optimizer.best_configuration:
            return {
                "success": False,
                "reason": "No optimal parameters available. Run optimization first.",
            }

        try:
            # Apply best parameters
            best_params = self.parameter_optimizer.best_configuration
            self.parameter_optimizer._apply_parameters(
                self.simulation_engine, best_params
            )

            self.logger.info("Optimal parameters applied successfully")
            self.logger.info("Applied parameters:")
            for param_name, value in best_params.items():
                self.logger.info(f"  {param_name}: {value:.4f}")

            return {"success": True, "applied_parameters": best_params}

        except Exception as e:
            self.logger.error(f"Failed to apply optimal parameters: {e}")
            return {"success": False, "reason": "application_error", "error": str(e)}

    def get_integration_status(self) -> Dict[str, Any]:
        """Get current integration status and metrics."""

        # Calculate success rates
        validation_success_rate = self.integration_metrics[
            "successful_validations"
        ] / max(self.integration_metrics["total_validations"], 1)

        optimization_success_rate = self.integration_metrics[
            "successful_optimizations"
        ] / max(self.integration_metrics["total_optimizations"], 1)

        integration_success_rate = self.integration_metrics[
            "successful_integrations"
        ] / max(self.integration_metrics["component_integration_attempts"], 1)

        return {
            "integration_status": self.integration_status,
            "integration_metrics": self.integration_metrics,
            "success_rates": {
                "validation": validation_success_rate,
                "optimization": optimization_success_rate,
                "integration": integration_success_rate,
            },
            "monitoring_data": getattr(self, "monitoring_data", {}),
            "capabilities": {
                "validation_framework": True,
                "parameter_optimization": True,
                "real_time_monitoring": self.integration_status[
                    "components_integrated"
                ],
                "automatic_optimization": self.integration_status[
                    "optimization_active"
                ],
                "continuous_validation": self.integration_status["validation_active"],
            },
        }

    def get_optimization_status(self) -> Dict[str, Any]:
        """Get current optimization status."""
        return self.parameter_optimizer.get_optimization_summary()

    def get_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary."""

        # Get validation metrics
        validation_metrics = self.validation_framework.get_performance_metrics()

        # Get optimization summary
        optimization_summary = self.parameter_optimizer.get_optimization_summary()

        # Combine with integration metrics
        return {
            "integration_metrics": self.integration_metrics,
            "validation_metrics": validation_metrics,
            "optimization_summary": optimization_summary,
            "monitoring_data": getattr(self, "monitoring_data", {}),
            "last_validation_result": self.integration_status.get("last_validation"),
            "last_optimization_result": self.integration_status.get(
                "last_optimization"
            ),
        }

    def save_integration_results(self, filepath: str):
        """Save integration results to file."""

        results = {
            "integration_status": self.integration_status,
            "integration_metrics": self.integration_metrics,
            "performance_summary": self.get_performance_summary(),
            "timestamp": time.time(),
        }

        import json

        with open(filepath, "w") as f:
            json.dump(results, f, indent=2)

        self.logger.info(f"Integration results saved to {filepath}")

    def reset_integration(self):
        """Reset integration status and metrics."""

        self.integration_status = {
            "validation_active": False,
            "optimization_active": False,
            "components_integrated": False,
            "last_validation": None,
            "last_optimization": None,
        }

        self.integration_metrics = {
            "total_validations": 0,
            "successful_validations": 0,
            "total_optimizations": 0,
            "successful_optimizations": 0,
            "component_integration_attempts": 0,
            "successful_integrations": 0,
        }

        # Reset framework metrics
        self.validation_framework.reset_metrics()
        self.parameter_optimizer.optimization_history.clear()

        self.logger.info("Integration status and metrics reset")
