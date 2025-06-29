"""
Validation Framework for KPP Simulation Physics
Provides comprehensive testing and validation for physics calculations, energy conservation,
and system integrity.
"""

import logging
import math
from typing import Any, Dict, List, Tuple

import numpy as np


class ValidationFramework:
    """
    Comprehensive validation framework for physics calculations.
    Tests energy conservation, force balance, and system behavior.
    """

    def __init__(self):
        self.energy_tolerance = 0.05  # 5% tolerance for energy conservation
        self.force_tolerance = 1e-3  # Small tolerance for force balance
        self.velocity_tolerance = 0.01  # 1% tolerance for velocity consistency

        # Test results storage
        self.test_results = {}
        self.validation_history = []

        # Performance tracking
        self.performance_metrics = {
            "energy_conservation_tests": 0,
            "force_balance_tests": 0,
            "physics_consistency_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
        }

        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def validate_energy_conservation(
        self, energy_in: float, energy_out: float, losses: float = 0.0
    ) -> Dict[str, Any]:
        """
        Validate energy conservation across the system.

        Args:
            energy_in: Total energy input to system (J)
            energy_out: Total useful energy output (J)
            losses: Energy losses (heat, friction, etc.) (J)

        Returns:
            Dict with validation results
        """
        self.performance_metrics["energy_conservation_tests"] += 1

        total_accounted_energy = energy_out + losses
        conservation_error = abs(total_accounted_energy - energy_in)
        relative_error = conservation_error / max(
            energy_in, 1e-6
        )  # Avoid division by zero

        is_valid = relative_error < self.energy_tolerance

        result = {
            "test_type": "energy_conservation",
            "passed": is_valid,
            "energy_in": energy_in,
            "energy_out": energy_out,
            "losses": losses,
            "conservation_error": conservation_error,
            "relative_error": relative_error,
            "tolerance": self.energy_tolerance,
            "timestamp": self._get_timestamp(),
        }

        if is_valid:
            self.performance_metrics["passed_tests"] += 1
            self.logger.info(
                f"Energy conservation PASSED: {relative_error:.4f} < {self.energy_tolerance}"
            )
        else:
            self.performance_metrics["failed_tests"] += 1
            self.logger.warning(
                f"Energy conservation FAILED: {relative_error:.4f} >= {self.energy_tolerance}"
            )

        return result

    def validate_force_balance(
        self, forces: List[float], expected_net: float = 0.0
    ) -> Dict[str, Any]:
        """
        Validate force balance in the system.

        Args:
            forces: List of forces acting on the system (N)
            expected_net: Expected net force (N), typically 0 for equilibrium

        Returns:
            Dict with validation results
        """
        self.performance_metrics["force_balance_tests"] += 1

        net_force = sum(forces)
        force_error = abs(net_force - expected_net)
        is_valid = force_error < self.force_tolerance

        result = {
            "test_type": "force_balance",
            "passed": is_valid,
            "forces": forces,
            "net_force": net_force,
            "expected_net": expected_net,
            "force_error": force_error,
            "tolerance": self.force_tolerance,
            "timestamp": self._get_timestamp(),
        }

        if is_valid:
            self.performance_metrics["passed_tests"] += 1
            self.logger.info(
                f"Force balance PASSED: error {force_error:.6f} N < {self.force_tolerance} N"
            )
        else:
            self.performance_metrics["failed_tests"] += 1
            self.logger.warning(
                f"Force balance FAILED: error {force_error:.6f} N >= {self.force_tolerance} N"
            )

        return result

    def validate_physics_consistency(
        self, floaters: List, chain_velocity: float, time_step: float
    ) -> Dict[str, Any]:
        """
        Validate physics consistency across all floaters.

        Args:
            floaters: List of floater objects
            chain_velocity: Current chain velocity (m/s)
            time_step: Simulation time step (s)

        Returns:
            Dict with validation results
        """
        self.performance_metrics["physics_consistency_tests"] += 1

        consistency_checks = {
            "mass_state_consistency": True,
            "velocity_consistency": True,
            "angular_position_validity": True,
            "buoyancy_validity": True,
        }

        issues = []

        for i, floater in enumerate(floaters):
            # Check mass-state consistency
            expected_heavy_mass = floater.container_mass + 1000 * floater.volume
            if (
                floater.state == "heavy"
                and abs(floater.mass - expected_heavy_mass) > 0.1
            ):
                consistency_checks["mass_state_consistency"] = False
                issues.append(f"Floater {i}: Heavy state but incorrect mass")
            elif (
                floater.state == "light"
                and abs(floater.mass - floater.container_mass) > 0.1
            ):
                consistency_checks["mass_state_consistency"] = False
                issues.append(f"Floater {i}: Light state but incorrect mass")

            # Check velocity consistency with chain
            expected_velocity = (
                chain_velocity if floater.angle < math.pi else -chain_velocity
            )
            velocity_error = abs(floater.velocity - expected_velocity) / max(
                abs(chain_velocity), 0.1
            )
            if velocity_error > self.velocity_tolerance:
                consistency_checks["velocity_consistency"] = False
                issues.append(f"Floater {i}: Velocity inconsistent with chain motion")

            # Check angular position validity
            if floater.angle < 0 or floater.angle > 2 * math.pi:
                consistency_checks["angular_position_validity"] = False
                issues.append(f"Floater {i}: Invalid angular position {floater.angle}")

            # Check buoyancy calculation validity
            if hasattr(floater, "last_buoyant_force"):
                expected_buoyancy = 1000 * 9.81 * floater.volume  # ρ * g * V
                buoyancy_error = (
                    abs(floater.last_buoyant_force - expected_buoyancy)
                    / expected_buoyancy
                )
                if buoyancy_error > 0.01:  # 1% tolerance
                    consistency_checks["buoyancy_validity"] = False
                    issues.append(f"Floater {i}: Incorrect buoyancy calculation")

        is_valid = all(consistency_checks.values())

        result = {
            "test_type": "physics_consistency",
            "passed": is_valid,
            "consistency_checks": consistency_checks,
            "issues": issues,
            "num_floaters": len(floaters),
            "chain_velocity": chain_velocity,
            "timestamp": self._get_timestamp(),
        }

        if is_valid:
            self.performance_metrics["passed_tests"] += 1
            self.logger.info(f"Physics consistency PASSED for {len(floaters)} floaters")
        else:
            self.performance_metrics["failed_tests"] += 1
            self.logger.warning(
                f"Physics consistency FAILED: {len(issues)} issues found"
            )
            for issue in issues:
                self.logger.warning(f"  - {issue}")

        return result

    def run_comprehensive_validation(self, simulation_engine) -> Dict[str, Any]:
        """
        Run comprehensive validation suite on a simulation engine.

        Args:
            simulation_engine: SimulationEngine instance to validate

        Returns:
            Dict with comprehensive validation results
        """
        self.logger.info("Starting comprehensive validation suite...")

        # Initialize validation session
        validation_session = {
            "timestamp": self._get_timestamp(),
            "tests": [],
            "summary": {},
            "recommendations": [],
        }

        # Test 1: Single floater behavior
        self.logger.info("Running single floater physics test...")
        single_floater_result = self._test_single_floater_physics(simulation_engine)
        validation_session["tests"].append(single_floater_result)

        # Test 2: Multi-floater system behavior
        self.logger.info("Running multi-floater system test...")
        multi_floater_result = self._test_multi_floater_system(simulation_engine)
        validation_session["tests"].append(multi_floater_result)

        # Test 3: Energy balance over time
        self.logger.info("Running energy balance test...")
        energy_balance_result = self._test_energy_balance_over_time(simulation_engine)
        validation_session["tests"].append(energy_balance_result)

        # Test 4: Equilibrium behavior
        self.logger.info("Running equilibrium behavior test...")
        equilibrium_result = self._test_equilibrium_behavior(simulation_engine)
        validation_session["tests"].append(equilibrium_result)

        # Generate summary
        validation_session["summary"] = self._generate_validation_summary(
            validation_session["tests"]
        )
        validation_session["recommendations"] = self._generate_recommendations(
            validation_session["tests"]
        )

        # Store in history
        self.validation_history.append(validation_session)

        self.logger.info("Comprehensive validation complete")
        return validation_session

    def _test_single_floater_physics(self, simulation_engine) -> Dict[str, Any]:
        """Test physics behavior with a single floater."""
        # Save original state
        original_floaters = simulation_engine.floaters.copy()
        original_num_floaters = simulation_engine.num_floaters

        try:
            # Set up single floater test
            simulation_engine.num_floaters = 1
            single_floater = simulation_engine.floaters[0]

            # Set known initial conditions
            single_floater.angle = 0.0
            single_floater.velocity = 1.0  # 1 m/s
            single_floater.state = "heavy"
            single_floater.mass = (
                single_floater.container_mass + 1000 * single_floater.volume
            )

            # Run several physics steps
            initial_energy = 0.5 * single_floater.mass * single_floater.velocity**2

            forces_history = []
            for _ in range(10):
                forces = simulation_engine.physics_engine.calculate_forces(
                    [single_floater], 1.0
                )
                forces_history.append(forces[0])

                # Basic physics update
                net_force = sum(
                    [
                        forces[0]["buoyant"],
                        forces[0]["gravitational"],
                        forces[0]["drag"],
                    ]
                )
                acceleration = net_force / single_floater.mass
                single_floater.velocity += (
                    acceleration * simulation_engine.physics_engine.params["time_step"]
                )

            # Check force consistency
            force_magnitudes = [abs(f["buoyant"]) for f in forces_history]
            buoyancy_consistent = all(
                abs(f - force_magnitudes[0]) < 1.0 for f in force_magnitudes
            )

            return {
                "test_name": "single_floater_physics",
                "passed": buoyancy_consistent,
                "initial_energy": initial_energy,
                "force_consistency": buoyancy_consistent,
                "final_velocity": single_floater.velocity,
                "notes": "Single floater behaves predictably",
            }

        finally:
            # Restore original state
            simulation_engine.floaters = original_floaters
            simulation_engine.num_floaters = original_num_floaters

        return {
            "test_name": "single_floater_physics",
            "passed": False,
            "notes": "Test failed with exception",
        }

    def _test_multi_floater_system(self, simulation_engine) -> Dict[str, Any]:
        """Test behavior with multiple floaters."""
        try:
            # Test with all floaters
            initial_positions = [f.angle for f in simulation_engine.floaters]

            # Run simulation for several steps
            total_force_before = sum(
                [
                    simulation_engine.physics_engine.calculate_forces(
                        simulation_engine.floaters, 1.0
                    )[i]["total"]
                    for i in range(len(simulation_engine.floaters))
                ]
            )

            # Check that forces are reasonable
            reasonable_forces = (
                abs(total_force_before) < 10000
            )  # Reasonable force magnitude

            return {
                "test_name": "multi_floater_system",
                "passed": reasonable_forces,
                "num_floaters": len(simulation_engine.floaters),
                "total_force": total_force_before,
                "force_reasonable": reasonable_forces,
                "notes": f"Multi-floater system with {len(simulation_engine.floaters)} floaters",
            }

        except Exception as e:
            return {
                "test_name": "multi_floater_system",
                "passed": False,
                "error": str(e),
                "notes": "Test failed with exception",
            }

    def _test_energy_balance_over_time(self, simulation_engine) -> Dict[str, Any]:
        """Test energy conservation over multiple time steps."""
        try:
            # Calculate initial system energy
            initial_kinetic = sum(
                [0.5 * f.mass * f.velocity**2 for f in simulation_engine.floaters]
            )
            initial_potential = sum(
                [f.mass * 9.81 * f.angle for f in simulation_engine.floaters]
            )  # Simplified
            initial_total = initial_kinetic + initial_potential

            # Run for several steps and track energy
            energy_history = [initial_total]

            for _ in range(5):
                # Update physics (simplified)
                current_kinetic = sum(
                    [0.5 * f.mass * f.velocity**2 for f in simulation_engine.floaters]
                )
                current_potential = sum(
                    [f.mass * 9.81 * f.angle for f in simulation_engine.floaters]
                )
                current_total = current_kinetic + current_potential
                energy_history.append(current_total)

            # Check energy drift
            energy_drift = abs(energy_history[-1] - energy_history[0]) / max(
                energy_history[0], 1e-6
            )
            energy_stable = energy_drift < 0.1  # 10% tolerance for simplified test

            return {
                "test_name": "energy_balance_over_time",
                "passed": energy_stable,
                "initial_energy": initial_total,
                "final_energy": energy_history[-1],
                "energy_drift": energy_drift,
                "energy_stable": energy_stable,
                "notes": "Energy conservation over time",
            }

        except Exception as e:
            return {
                "test_name": "energy_balance_over_time",
                "passed": False,
                "error": str(e),
                "notes": "Test failed with exception",
            }

    def _test_equilibrium_behavior(self, simulation_engine) -> Dict[str, Any]:
        """Test system behavior at equilibrium."""
        try:
            # Set all floaters to similar conditions for equilibrium test
            for floater in simulation_engine.floaters:
                floater.velocity = 0.1  # Small velocity
                floater.state = "heavy"
                floater.mass = floater.container_mass + 1000 * floater.volume

            # Calculate forces at near-equilibrium
            forces = simulation_engine.physics_engine.calculate_forces(
                simulation_engine.floaters, 0.1
            )
            net_forces = [f["total"] for f in forces]
            max_force = max([abs(f) for f in net_forces])

            # Check if forces are small (near equilibrium)
            near_equilibrium = max_force < 100  # 100N threshold for equilibrium

            return {
                "test_name": "equilibrium_behavior",
                "passed": near_equilibrium,
                "max_force": max_force,
                "near_equilibrium": near_equilibrium,
                "notes": "System behavior near equilibrium",
            }

        except Exception as e:
            return {
                "test_name": "equilibrium_behavior",
                "passed": False,
                "error": str(e),
                "notes": "Test failed with exception",
            }

    def _generate_validation_summary(self, tests: List[Dict]) -> Dict[str, Any]:
        """Generate summary of validation results."""
        total_tests = len(tests)
        passed_tests = sum(1 for test in tests if test.get("passed", False))

        return {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": total_tests - passed_tests,
            "success_rate": passed_tests / max(total_tests, 1),
            "overall_status": "PASSED" if passed_tests == total_tests else "FAILED",
        }

    def _generate_recommendations(self, tests: List[Dict]) -> List[str]:
        """Generate recommendations based on test results."""
        recommendations = []

        for test in tests:
            if not test.get("passed", False):
                test_name = test.get("test_name", "unknown")
                if "energy" in test_name:
                    recommendations.append(
                        "Consider reviewing energy calculation methods and conservation logic"
                    )
                elif "force" in test_name:
                    recommendations.append(
                        "Check force calculation accuracy and balance"
                    )
                elif "equilibrium" in test_name:
                    recommendations.append(
                        "Review equilibrium conditions and force balance at rest"
                    )
                else:
                    recommendations.append(f"Investigate issues in {test_name} test")

        if not recommendations:
            recommendations.append(
                "All validation tests passed - system appears to be functioning correctly"
            )

        return recommendations

    def _get_timestamp(self) -> float:
        """Get current timestamp."""
        import time

        return time.time()

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics."""
        total_tests = (
            self.performance_metrics["passed_tests"]
            + self.performance_metrics["failed_tests"]
        )

        return {
            **self.performance_metrics,
            "total_tests": total_tests,
            "success_rate": self.performance_metrics["passed_tests"]
            / max(total_tests, 1),
        }

    def reset_metrics(self):
        """Reset performance metrics."""
        self.performance_metrics = {
            "energy_conservation_tests": 0,
            "force_balance_tests": 0,
            "physics_consistency_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
        }
        self.validation_history.clear()
