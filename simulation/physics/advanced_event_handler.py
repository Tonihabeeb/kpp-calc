"""
Advanced Event Handler for KPP Simulation (Stage 2)
Enhanced state management, energy tracking, and event handling.
"""

import logging
import math

from config.config import RHO_WATER, G

logger = logging.getLogger(__name__)


class AdvancedEventHandler:
    """
    Advanced event handler with sophisticated state management,
    energy optimization, and predictive event timing.
    """

    def __init__(self, tank_depth=10.0, optimization_params=None):
        """
        Initialize advanced event handler.

        Args:
            tank_depth (float): Depth of water tank (m)
            optimization_params (dict): Parameters for energy optimization
        """
        self.tank_depth = tank_depth

        # Zone configuration (improved from basic handler)
        self.bottom_zone = 0.08  # radians - tighter injection zone
        self.top_zone = 0.08  # radians - tighter venting zone

        # Energy tracking
        self.energy_input = 0.0  # Total compressor energy input (J)
        self.energy_per_injection = []  # Track individual injection energies
        self.cumulative_injections = 0
        self.cumulative_ventings = 0

        # Advanced state tracking
        self.floater_states = {}  # floater_id -> state history
        self.injection_history = {}  # floater_id -> injection timestamps
        self.venting_history = {}  # floater_id -> venting timestamps

        # Cycle tracking for efficiency
        self.processed_injection = set()
        self.processed_venting = set()
        self.cycle_reset_interval = 2 * math.pi  # Reset after full rotation
        self.last_cycle_reset = 0.0

        # Energy optimization parameters
        opt_params = optimization_params or {}
        self.adaptive_pressure = opt_params.get("adaptive_pressure", True)
        self.pressure_safety_factor = opt_params.get("pressure_safety_factor", 1.2)
        self.min_injection_pressure = opt_params.get("min_injection_pressure", 150000)  # Pa
        self.energy_efficiency_target = opt_params.get("efficiency_target", 0.4)  # 40%

        # Performance metrics
        self.injection_success_rate = 1.0
        self.average_injection_energy = 0.0
        self.energy_optimization_active = False

        logger.info(
            f"AdvancedEventHandler initialized: depth={tank_depth}m, " f"adaptive_pressure={self.adaptive_pressure}"
        )

    def handle_injection(self, floater, floater_id=None, current_time=0.0):
        """
        Handle air injection with advanced energy optimization.

        Args:
            floater: Floater object
            floater_id: Unique identifier
            current_time: Current simulation time

        Returns:
            dict: Injection result with energy and efficiency data
        """
        if floater_id is None:
            floater_id = id(floater)

        # Check injection conditions
        if not self._can_inject(floater, floater_id):
            return {"success": False, "reason": "conditions_not_met"}

        # Calculate optimal injection pressure
        injection_pressure = self._calculate_optimal_pressure(floater, current_time)

        # Perform injection
        energy_cost = self._perform_injection(floater, injection_pressure)

        # Update tracking
        self._update_injection_tracking(floater_id, current_time, energy_cost)

        # Mark as processed
        self.processed_injection.add(floater_id)

        result = {
            "success": True,
            "energy_cost": energy_cost,
            "pressure_used": injection_pressure,
            "floater_id": floater_id,
            "efficiency_estimate": self._estimate_injection_efficiency(energy_cost),
        }

        logger.info(
            f"Advanced injection: floater_id={floater_id}, "
            f"energy={energy_cost:.1f}J, pressure={injection_pressure:.0f}Pa"
        )

        return result

    def handle_venting(self, floater, floater_id=None, current_time=0.0):
        """
        Handle air venting with state synchronization.

        Args:
            floater: Floater object
            floater_id: Unique identifier
            current_time: Current simulation time

        Returns:
            dict: Venting result with state information
        """
        if floater_id is None:
            floater_id = id(floater)

        # Check venting conditions
        if not self._can_vent(floater, floater_id):
            return {"success": False, "reason": "conditions_not_met"}

        # Perform venting
        self._perform_venting(floater)

        # Update tracking
        self._update_venting_tracking(floater_id, current_time)

        # Mark as processed
        self.processed_venting.add(floater_id)

        result = {
            "success": True,
            "floater_id": floater_id,
            "venting_time": current_time,
            "cycle_completed": self._check_cycle_completion(floater_id),
        }

        logger.info(f"Advanced venting: floater_id={floater_id}, time={current_time:.1f}s")

        return result

    def process_all_events(self, floaters, current_time=0.0):
        """
        Process all floater events with advanced coordination.

        Args:
            floaters: List of floater objects
            current_time: Current simulation time

        Returns:
            dict: Comprehensive event processing results
        """
        injection_results = []
        venting_results = []

        # Reset cycle tracking if needed
        self._check_cycle_reset(current_time)

        # Process each floater
        for i, floater in enumerate(floaters):
            # Handle injection
            inj_result = self.handle_injection(floater, floater_id=i, current_time=current_time)
            if inj_result["success"]:
                injection_results.append(inj_result)

            # Handle venting
            vent_result = self.handle_venting(floater, floater_id=i, current_time=current_time)
            if vent_result["success"]:
                venting_results.append(vent_result)

        # Update energy optimization
        self._update_energy_optimization()

        return {
            "injections": len(injection_results),
            "ventings": len(venting_results),
            "injection_results": injection_results,
            "venting_results": venting_results,
            "total_energy_input": self.energy_input,
            "average_injection_energy": self.average_injection_energy,
            "injection_success_rate": self.injection_success_rate,
            "energy_optimization_active": self.energy_optimization_active,
        }

    def get_energy_analysis(self):
        """
        Get comprehensive energy analysis.

        Returns:
            dict: Detailed energy analysis
        """
        len(self.injection_history)

        return {
            "total_energy_input": self.energy_input,
            "total_injections": self.cumulative_injections,
            "total_ventings": self.cumulative_ventings,
            "average_energy_per_injection": self.average_injection_energy,
            "energy_per_injection_history": self.energy_per_injection.copy(),
            "injection_success_rate": self.injection_success_rate,
            "estimated_system_efficiency": self._calculate_system_efficiency(),
            "tank_depth": self.tank_depth,
            "injection_pressure_range": self._get_pressure_range(),
            "energy_optimization_savings": self._calculate_optimization_savings(),
        }

    def _can_inject(self, floater, floater_id):
        """Check if injection is possible."""
        return self._is_at_bottom(floater) and self._is_heavy(floater) and floater_id not in self.processed_injection

    def _can_vent(self, floater, floater_id):
        """Check if venting is possible."""
        return self._is_at_top(floater) and self._is_light(floater) and floater_id not in self.processed_venting

    def _calculate_optimal_pressure(self, floater, current_time):
        """
        Calculate optimal injection pressure based on conditions.

        Returns:
            float: Optimal pressure in Pascal
        """
        # Base pressure at depth
        P_atm = 101325  # Pa
        P_depth = P_atm + RHO_WATER * G * self.tank_depth

        if self.adaptive_pressure and self.energy_optimization_active:
            # Adaptive pressure based on recent performance
            recent_efficiency = self._get_recent_efficiency()

            if recent_efficiency < self.energy_efficiency_target:
                # Reduce pressure to save energy
                pressure_reduction = 0.9
            else:
                # Maintain or slightly increase pressure
                pressure_reduction = 1.0

            optimal_pressure = P_depth * pressure_reduction * self.pressure_safety_factor
        else:
            # Standard pressure calculation
            optimal_pressure = P_depth * self.pressure_safety_factor

        # Ensure minimum pressure
        return max(optimal_pressure, self.min_injection_pressure)

    def _perform_injection(self, floater, pressure):
        """
        Perform the actual injection and calculate energy cost.

        Returns:
            float: Energy cost in Joules
        """
        # State transition
        if hasattr(floater, "state"):
            floater.state = "light"
        if hasattr(floater, "is_filled"):
            floater.is_filled = True

        # Update mass
        container_mass = getattr(floater, "container_mass", 50.0)
        floater.mass = container_mass

        # Calculate energy cost
        volume = getattr(floater, "volume", 0.04)

        # More sophisticated energy calculation considering compression work
        P_atm = 101325
        if pressure > P_atm:
            # Isothermal compression work: W = P_atm * V * ln(P_final / P_atm)
            energy_cost = P_atm * volume * math.log(pressure / P_atm)
        else:
            # Fallback to simple calculation
            energy_cost = pressure * volume

        self.energy_input += energy_cost
        return energy_cost

    def _perform_venting(self, floater):
        """Perform the actual venting."""
        # State transition
        if hasattr(floater, "state"):
            floater.state = "heavy"
        if hasattr(floater, "is_filled"):
            floater.is_filled = False

        # Update mass
        container_mass = getattr(floater, "container_mass", 50.0)
        volume = getattr(floater, "volume", 0.04)
        water_mass = RHO_WATER * volume
        floater.mass = container_mass + water_mass

    def _update_injection_tracking(self, floater_id, time, energy):
        """Update injection tracking data."""
        if floater_id not in self.injection_history:
            self.injection_history[floater_id] = []

        self.injection_history[floater_id].append({"time": time, "energy": energy})

        self.energy_per_injection.append(energy)
        self.cumulative_injections += 1

        # Update running average
        self.average_injection_energy = sum(self.energy_per_injection) / len(self.energy_per_injection)

    def _update_venting_tracking(self, floater_id, time):
        """Update venting tracking data."""
        if floater_id not in self.venting_history:
            self.venting_history[floater_id] = []

        self.venting_history[floater_id].append({"time": time})
        self.cumulative_ventings += 1

    def _update_energy_optimization(self):
        """Update energy optimization parameters."""
        if len(self.energy_per_injection) >= 5:  # Need some data
            self.energy_optimization_active = True

            # Calculate recent success rate
            recent_injections = min(10, len(self.energy_per_injection))
            recent_energies = self.energy_per_injection[-recent_injections:]

            # Simple success metric: consistent energy consumption
            energy_variance = sum((e - self.average_injection_energy) ** 2 for e in recent_energies) / len(
                recent_energies
            )
            energy_std = math.sqrt(energy_variance)

            # High consistency = high success rate
            if energy_std < self.average_injection_energy * 0.2:
                self.injection_success_rate = 0.95
            else:
                self.injection_success_rate = max(0.7, 1.0 - energy_std / self.average_injection_energy)

    def _get_recent_efficiency(self):
        """Get recent injection efficiency estimate."""
        if len(self.energy_per_injection) < 3:
            return 0.3  # Default low efficiency

        recent_energies = self.energy_per_injection[-3:]
        avg_recent = sum(recent_energies) / len(recent_energies)

        # Efficiency inversely related to energy consumption
        # Lower energy = higher efficiency
        baseline_energy = self.min_injection_pressure * 0.04  # Baseline for 40L
        return max(0.1, baseline_energy / avg_recent)

    def _calculate_system_efficiency(self):
        """Calculate overall system efficiency estimate."""
        if self.cumulative_injections == 0:
            return 0.0

        # Simple efficiency metric based on energy consistency
        if len(self.energy_per_injection) > 1:
            energy_std = math.sqrt(
                sum((e - self.average_injection_energy) ** 2 for e in self.energy_per_injection)
                / len(self.energy_per_injection)
            )
            consistency = max(0.0, 1.0 - energy_std / self.average_injection_energy)
            return consistency * self.injection_success_rate

        return self.injection_success_rate

    def _get_pressure_range(self):
        """Get pressure range used for injections."""
        P_atm = 101325
        P_depth = P_atm + RHO_WATER * G * self.tank_depth

        return {
            "min_pressure": self.min_injection_pressure,
            "standard_pressure": P_depth * self.pressure_safety_factor,
            "depth_pressure": P_depth,
        }

    def _calculate_optimization_savings(self):
        """Calculate energy savings from optimization."""
        if not self.energy_optimization_active or len(self.energy_per_injection) < 5:
            return 0.0

        # Compare recent energy usage to initial baseline
        baseline_energies = self.energy_per_injection[:3]
        recent_energies = self.energy_per_injection[-3:]

        baseline_avg = sum(baseline_energies) / len(baseline_energies)
        recent_avg = sum(recent_energies) / len(recent_energies)

        savings_per_injection = max(0.0, baseline_avg - recent_avg)
        total_optimized_injections = max(0, self.cumulative_injections - 3)

        return savings_per_injection * total_optimized_injections

    def _check_cycle_completion(self, floater_id):
        """Check if floater completed a full cycle."""
        return (
            floater_id in self.injection_history
            and floater_id in self.venting_history
            and len(self.injection_history[floater_id]) == len(self.venting_history[floater_id])
        )

    def _check_cycle_reset(self, current_time):
        """Check if cycle tracking should be reset."""
        if current_time - self.last_cycle_reset > 5.0:  # Reset every 5 seconds
            self.reset_cycle_tracking()
            self.last_cycle_reset = current_time

    def reset_cycle_tracking(self):
        """Reset cycle tracking for new cycle."""
        self.processed_injection.clear()
        self.processed_venting.clear()

    # Utility methods (same as basic event handler)
    def _is_at_bottom(self, floater):
        """Check if floater is in bottom injection zone."""
        angle = self._get_floater_angle(floater)
        return angle < self.bottom_zone

    def _is_at_top(self, floater):
        """Check if floater is in top venting zone."""
        angle = self._get_floater_angle(floater)
        return abs(angle - math.pi) < self.top_zone

    def _get_floater_angle(self, floater):
        """Get normalized angle of floater."""
        if hasattr(floater, "angle"):
            return floater.angle % (2 * math.pi)
        elif hasattr(floater, "theta"):
            return floater.theta % (2 * math.pi)
        else:
            logger.warning("Floater has no angle/theta attribute")
            return 0.0

    def _is_heavy(self, floater):
        """Check if floater is in heavy state."""
        if hasattr(floater, "state"):
            return floater.state == "heavy"
        elif hasattr(floater, "is_filled"):
            return not floater.is_filled
        else:
            container_mass = getattr(floater, "container_mass", 50.0)
            return floater.mass > container_mass * 1.5

    def _is_light(self, floater):
        """Check if floater is in light state."""
        if hasattr(floater, "state"):
            return floater.state == "light"
        elif hasattr(floater, "is_filled"):
            return floater.is_filled
        else:
            container_mass = getattr(floater, "container_mass", 50.0)
            return floater.mass <= container_mass * 1.5

    def _estimate_injection_efficiency(self, energy_cost):
        """
        Estimate injection efficiency based on energy cost.

        Args:
            energy_cost (float): Energy cost of injection in Joules

        Returns:
            float: Estimated efficiency (0.0 to 1.0)
        """
        if len(self.energy_per_injection) == 0:
            return 0.3  # Default efficiency estimate

        # Compare to average energy consumption
        if self.average_injection_energy > 0:
            # Lower energy relative to average = higher efficiency
            efficiency = min(1.0, self.average_injection_energy / energy_cost * 0.4)
        else:
            efficiency = 0.3

        return max(0.1, efficiency)  # Minimum 10% efficiency
