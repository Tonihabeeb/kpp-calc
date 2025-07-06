"""
State Manager for the KPP Simulation Engine.
Handles state tracking, data collection, and simulation output management.
"""

import logging
from typing import Any, Dict, Optional

from ..schemas import EnergyLossData, PerformanceMetrics, PhysicsResults, SimulationState, SystemResults, SystemState
from .base_manager import BaseManager, ManagerType

logger = logging.getLogger(__name__)


class StateManager(BaseManager):
    """
    Manages simulation state tracking and data collection including:
    - System state aggregation
    - Simulation output data formatting
    - Performance metrics tracking
    - Energy accounting
    """

    def __init__(self, engine):
        """
        Initialize the StateManager with reference to the main engine.

        Args:
            engine: Reference to the main SimulationEngine instance
        """
        super().__init__(engine, ManagerType.STATE)

        # State tracking variables
        self.energy_losses = EnergyLossData()

    def update(self, dt: float, *args, **kwargs) -> Dict[str, Any]:
        """
        Main update method required by BaseManager.

        Args:
            dt: Time step in seconds

        Returns:
            Dictionary containing state update results
        """
        # This will be implemented when we refactor the full system
        return {}

    def build_system_state(
        self,
        total_vertical_force: float,
        base_buoy_force: float,
        enhanced_buoy_force: float,
        thermal_enhanced_force: float,
        pulse_force: float,
        preliminary_state: Dict[str, Any],
    ) -> SystemState:
        """
        Build comprehensive system state for control system and monitoring.

        Args:
            total_vertical_force: Total vertical force from all floaters
            base_buoy_force: Base buoyancy force
            enhanced_buoy_force: Enhanced buoyancy force
            thermal_enhanced_force: Thermal enhancement force
            pulse_force: Pulse force contribution
            preliminary_state: Preliminary integrated_drivetrain state

        Returns:
            Comprehensive system state dictionary
        """
        # Calculate energy losses
        self._update_energy_losses()

        # Get preliminary mechanical values
        preliminary_torque = preliminary_state.get("gearbox", {}).get("output_torque", 0.0)
        preliminary_speed_rpm = preliminary_state.get("gearbox", {}).get("output_speed_rpm", 0.0)

        # Create SystemState Pydantic model
        system_state = SystemState(
            time=self.engine.time,
            power_output=0.0,  # Will be updated with electrical data
            speed_rpm=preliminary_speed_rpm,
            torque=preliminary_torque,
            total_vertical_force=total_vertical_force,
            net_force=total_vertical_force,  # Will be refined
            performance_data={
                "base_buoy_force": base_buoy_force,
                "enhanced_buoy_force": enhanced_buoy_force,
                "thermal_enhanced_force": thermal_enhanced_force,
                "pulse_force": pulse_force,
                "chain_tension": self.engine.chain_tension,
                "tank_pressure": self.engine.pneumatics.tank_pressure,
            },
        )

        logger.debug("System state built")
        return system_state

    def build_simulation_output(
        self,
        system_state: SystemState,
        electrical_output: Dict[str, Any],
        drivetrain_output: Dict[str, Any],
        control_output: Dict[str, Any],
        enhanced_state: Optional[Dict[str, Any]] = None,
        grid_services_response: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Build comprehensive simulation output data.

        Args:
            system_state: System state data
            electrical_output: Electrical system outputs
            drivetrain_output: IntegratedDrivetrain outputs
            control_output: Control system outputs
            enhanced_state: Enhanced loss model state (optional)
            grid_services_response: Grid services response (optional)

        Returns:
            Complete simulation step output
        """
        # Extract key values
        grid_power_output = electrical_output.get("grid_power_output", 0.0)
        final_output_torque = drivetrain_output.get("gearbox_output_torque", 0.0)
        final_output_speed_rpm = drivetrain_output.get("flywheel_speed_rpm", 0.0)

        # Build comprehensive output
        output_data = {
            "time": self.engine.time,
            "forces": {
                "total_vertical_force": system_state.total_vertical_force,
                "base_buoy_force": system_state.performance_data.get("base_buoy_force", 0.0),
                "enhanced_buoy_force": system_state.performance_data.get("enhanced_buoy_force", 0.0),
                "thermal_enhanced_force": system_state.performance_data.get("thermal_enhanced_force", 0.0),
                "pulse_force": system_state.performance_data.get("pulse_force", 0.0),
                "chain_tension": system_state.performance_data.get("chain_tension", 0.0),
                # Enhanced physics forces
                "h1_nanobubble_force": getattr(self.engine, "h1_nanobubble_force", 0.0),
                "h2_thermal_force": getattr(self.engine, "h2_thermal_force", 0.0),
                "h3_pulse_force": getattr(self.engine, "h3_pulse_force", 0.0),
            },
            "mechanical": {
                "output_torque": final_output_torque,
                "output_speed_rpm": final_output_speed_rpm,
                "mechanical_power": abs(final_output_torque * final_output_speed_rpm * 2 * 3.14159 / 60),
                "chain_speed": drivetrain_output.get("chain_speed", 0.0),
                "flywheel_energy": drivetrain_output.get("flywheel_energy", 0.0),
                "clutch_engaged": drivetrain_output.get("clutch_engaged", False),
                "gearbox_efficiency": drivetrain_output.get("gearbox_efficiency", 0.885),
            },
            "electrical": {
                "grid_power_output": grid_power_output,
                "grid_voltage": electrical_output.get("grid_voltage", 480.0),
                "grid_frequency": electrical_output.get("grid_frequency", 60.0),
                "system_efficiency": electrical_output.get("system_efficiency", 0.0),
                "load_factor": electrical_output.get("load_factor", 0.0),
                "synchronized": electrical_output.get("synchronized", False),
                "reactive_power": electrical_output.get("reactive_power", 0.0),
            },
            "control": {
                "control_mode": control_output.get("control_mode", "normal"),
                "fault_status": control_output.get("fault_status", {}),
                "timing_commands": control_output.get("timing_commands", {}),
                "load_commands": control_output.get("load_commands", {}),
                "grid_commands": control_output.get("grid_commands", {}),
            },
            "pneumatics": {
                "tank_pressure": system_state.performance_data.get("tank_pressure", 0.0),
                "compressor_running": False,  # Will be updated with actual data
            },
            "floaters": [],  # Will be updated with actual floater data
            "energy_losses": self.energy_losses.model_dump(),
            "physics_systems": {
                "chain_system": {},  # Will be updated with actual data
                "fluid_system": {},  # Will be updated with actual data
                "thermal_system": {},  # Will be updated with actual data
                "enhanced_physics": {
                    "h1_active": getattr(self.engine, "h1_nanobubbles_active", False),
                    "h2_active": getattr(self.engine, "h2_thermal_active", False),
                    "h3_active": getattr(self.engine, "h3_pulse_active", False),
                },
            },
        }

        # Add enhanced loss model data if available
        if enhanced_state:
            output_data["enhanced_losses"] = enhanced_state

        # Add grid services data if available
        if grid_services_response:
            output_data["grid_services"] = grid_services_response

        logger.debug(f"Simulation output built: power={grid_power_output:.1f}W")
        return output_data

    def _update_energy_losses(self) -> None:
        """Update energy losses from all floaters."""
        drag_loss = sum(getattr(f, "drag_loss", 0.0) for f in self.engine.floaters)
        dissolution_loss = sum(getattr(f, "dissolution_loss", 0.0) for f in self.engine.floaters)
        venting_loss = sum(getattr(f, "venting_loss", 0.0) for f in self.engine.floaters)

        # Update the Pydantic model
        self.energy_losses = EnergyLossData(
            drag_loss=drag_loss, dissolution_loss=dissolution_loss, venting_loss=venting_loss
        )

    def get_performance_metrics(self) -> Dict[str, float]:
        """
        Calculate and return key performance metrics.

        Returns:
            Dictionary of performance metrics
        """
        # Calculate overall system efficiency
        mechanical_power = abs(
            getattr(self.engine, "final_output_torque", 0.0) * getattr(self.engine, "final_output_speed", 0.0)
        )
        electrical_power = getattr(self.engine, "grid_power_output", 0.0)
        overall_efficiency = electrical_power / mechanical_power if mechanical_power > 0 else 0.0

        # Calculate force utilization
        total_buoyant_force = sum(f.compute_buoyant_force() for f in self.engine.floaters)
        force_utilization = (
            getattr(self.engine, "total_vertical_force", 0.0) / total_buoyant_force if total_buoyant_force > 0 else 0.0
        )

        # Calculate energy loss rates
        total_energy_loss = (
            self.energy_losses.drag_loss
            + self.energy_losses.dissolution_loss
            + self.energy_losses.venting_loss
            + self.energy_losses.mechanical_loss
            + self.energy_losses.electrical_loss
            + self.energy_losses.thermal_loss
        )

        return {
            "overall_efficiency": overall_efficiency,
            "mechanical_power": mechanical_power,
            "electrical_power": electrical_power,
            "force_utilization": force_utilization,
            "total_buoyant_force": total_buoyant_force,
            "total_energy_loss": total_energy_loss,
            "drag_loss_ratio": self.energy_losses.drag_loss / total_energy_loss if total_energy_loss > 0 else 0.0,
            "dissolution_loss_ratio": (
                self.energy_losses.dissolution_loss / total_energy_loss if total_energy_loss > 0 else 0.0
            ),
            "venting_loss_ratio": self.energy_losses.venting_loss / total_energy_loss if total_energy_loss > 0 else 0.0,
        }

    def log_step_summary(self, output_data: Dict[str, Any]) -> None:
        """
        Log a summary of the simulation step.

        Args:
            output_data: Complete simulation output data
        """
        if self.engine.time % 1.0 < self.engine.dt:  # Log every second
            forces = output_data["forces"]
            mechanical = output_data["mechanical"]
            electrical = output_data["electrical"]

            logger.info(
                f"t={self.engine.time:.1f}s: "
                f"Power={electrical['grid_power_output']:.0f}W, "
                f"RPM={mechanical['output_speed_rpm']:.0f}, "
                f"Force={forces['total_vertical_force']:.0f}N, "
                f"Efficiency={electrical['system_efficiency']:.1%}"
            )

            # Log enhanced physics if active
            enhanced_physics = output_data["physics_systems"]["enhanced_physics"]
            if any(enhanced_physics.values()):
                active_systems = [k for k, v in enhanced_physics.items() if v]
                logger.info(f"Enhanced physics active: {', '.join(active_systems)}")

    def queue_data_if_available(self, output_data: Dict[str, Any]) -> None:
        """
        Queue simulation data if data queue is available.

        Args:
            output_data: Complete simulation output data
        """
        if self.engine.data_queue:
            try:
                self.engine.data_queue.put_nowait(output_data)
            except Exception as e:
                logger.warning(f"Failed to queue data: {e}")

    def update_time(self, dt: float) -> None:
        """
        Update simulation time.

        Args:
            dt: Time step in seconds
        """
        self.engine.time += dt
        logger.debug(f"Simulation time updated to {self.engine.time:.3f}s")

    def get_latest_state(self) -> Optional[SimulationState]:
        """
        Get the latest simulation state if available.

        Returns:
            Latest SimulationState or None if not available
        """
        if hasattr(self, "_latest_state"):
            return self._latest_state
        return None

    def collect_and_log_state(
        self, dt: float, physics_results: PhysicsResults, system_results: SystemResults
    ) -> SimulationState:
        """
        Collect all state data, log the step, and prepare output data.

        Args:
            dt: Time step in seconds
            physics_results: Results from physics calculations (Pydantic model)
            system_results: Results from system updates (Pydantic model)

        Returns:
            Complete simulation state data as Pydantic model
        """
        # Extract key data from Pydantic models
        total_vertical_force = physics_results.total_vertical_force
        drivetrain_data = system_results.integrated_drivetrain
        electrical_data = system_results.electrical
        system_results.control

        # 1. Build system state
        base_buoy_force = physics_results.base_buoy_force
        enhanced_buoy_force = physics_results.enhanced_buoy_force
        thermal_enhanced_force = physics_results.thermal_enhanced_force
        pulse_force = physics_results.pulse_force
        preliminary_state = {"torque": drivetrain_data.output_torque}

        system_state = self.build_system_state(
            total_vertical_force,
            base_buoy_force,
            enhanced_buoy_force,
            thermal_enhanced_force,
            pulse_force,
            preliminary_state,
        )

        # 2. Create complete simulation state
        performance_metrics = PerformanceMetrics(
            overall_efficiency=electrical_data.system_efficiency,
            power_efficiency=electrical_data.system_efficiency,
            mechanical_efficiency=drivetrain_data.system_efficiency,
            electrical_efficiency=electrical_data.system_efficiency,
        )

        simulation_state = SimulationState(
            time=self.engine.time,
            dt=dt,
            physics=physics_results,
            systems=system_results,
            energy_losses=self.energy_losses,
            performance=performance_metrics,
        )

        # 3. Log step summary (simple approach for Pydantic models)
        if self.engine.time % 1.0 < self.engine.dt:  # Log every second
            logger.info(
                f"t={self.engine.time:.1f}s: "
                f"Power={simulation_state.systems.electrical.power_output:.0f}W, "
                f"Force={simulation_state.physics.total_vertical_force:.0f}N, "
                f"Efficiency={simulation_state.systems.electrical.system_efficiency:.1%}"
            )

        # 4. Queue data for streaming if available (no-op for now)

        # 5. Update internal energy tracking
        self._update_energy_losses()

        # Store the latest state for external access
        self._latest_state = simulation_state

        return simulation_state

    def get_stats(self) -> Dict[str, Any]:
        """Get state manager statistics."""
        return {
            "energy_losses": self.energy_losses.model_dump() if hasattr(self.energy_losses, 'model_dump') else {},
            "manager_type": "state",
            "initialized": True,
        }
