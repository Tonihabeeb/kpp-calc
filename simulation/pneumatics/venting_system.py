"""
Automatic Venting System for KPP Pneumatic Floaters

This module implements Phase 4 of the pneumatics upgrade:
- Passive venting mechanisms based on floater position
- Air release dynamics and pressure equalization
- Water refill process for floater reset to heavy state
- Integration with position detection and chain control

Key Physics:
- Rapid pressure drop to atmospheric when venting triggered
- Water inflow rates through floater openings
- Buoyancy state transitions during venting
- Geometric triggers for automatic valve opening
"""

import logging
import math
from typing import Dict, List, Optional, Tuple

from config.config import RHO_WATER, G

logger = logging.getLogger(__name__)


class VentingTrigger:
    """
    Defines conditions that trigger automatic air venting from floaters.
    """

    def __init__(
        self,
        trigger_type: str = "position",
        position_threshold: float = 9.5,  # Position to trigger venting (m)
        tilt_angle_threshold: float = 45.0,  # Tilt angle to trigger venting (degrees)
        surface_breach_depth: float = 0.1,
    ):  # Depth considered "surface breach" (m)
        """
        Initialize venting trigger parameters.

        Args:
            trigger_type: Type of trigger ("position", "tilt", "surface_breach")
            position_threshold: Position above which venting is triggered
            tilt_angle_threshold: Tilt angle above which venting is triggered
            surface_breach_depth: Depth below which surface breach venting occurs
        """
        self.trigger_type = trigger_type
        self.position_threshold = position_threshold
        self.tilt_angle_threshold = math.radians(tilt_angle_threshold)
        self.surface_breach_depth = surface_breach_depth

        logger.info(
            f"VentingTrigger initialized: type={trigger_type}, "
            f"pos_threshold={position_threshold}m, "
            f"tilt_threshold={tilt_angle_threshold}°"
        )

    def should_trigger_venting(
        self,
        floater_position: float,
        floater_tilt: float = 0.0,
        water_depth: float = 10.0,
    ) -> bool:
        """
        Determine if venting should be triggered based on floater state.

        Args:
            floater_position: Current floater position (m)
            floater_tilt: Current floater tilt angle (radians)
            water_depth: Total water depth (m)

        Returns:
            True if venting should be triggered
        """
        if self.trigger_type == "position":
            return floater_position >= self.position_threshold

        elif self.trigger_type == "tilt":
            return abs(floater_tilt) >= self.tilt_angle_threshold

        elif self.trigger_type == "surface_breach":
            depth_from_surface = water_depth - floater_position
            return depth_from_surface <= self.surface_breach_depth

        else:
            logger.warning(f"Unknown trigger type: {self.trigger_type}")
            return False


class AirReleasePhysics:
    """
    Handles the physics of air release during venting process.
    """

    def __init__(self):
        """Initialize air release physics parameters."""
        # Standard atmospheric pressure (Pa)
        self.P_atm = 101325.0

        # Air release characteristics
        self.vent_valve_area = 0.001  # m² (10 cm²)
        self.discharge_coefficient = 0.6  # Typical for sharp-edged orifice

        # Bubble dynamics
        self.bubble_rise_velocity = 0.3  # m/s typical bubble rise speed
        self.air_dissolution_rate = 0.02  # 1/s rate of air dissolving during release

        # Water inflow characteristics
        self.water_inflow_coefficient = 0.8  # Flow coefficient for water entering
        self.floater_opening_area = 0.002  # m² (20 cm²) total opening area

    def calculate_air_release_rate(self, internal_pressure: float, external_pressure: float) -> float:
        """
        Calculate the volumetric flow rate of air being released.

        Uses choked flow theory for high pressure differences and
        standard orifice flow for moderate differences.

        Args:
            internal_pressure: Pressure inside floater (Pa)
            external_pressure: External water pressure (Pa)

        Returns:
            Volumetric air flow rate (m³/s)
        """
        pressure_ratio = external_pressure / internal_pressure

        # Critical pressure ratio for air (γ = 1.4)
        critical_ratio = (2 / (1.4 + 1)) ** (1.4 / (1.4 - 1))  # ≈ 0.528

        if pressure_ratio <= critical_ratio:
            # Choked flow - maximum flow rate
            flow_rate = (
                self.discharge_coefficient
                * self.vent_valve_area
                * internal_pressure
                * math.sqrt(1.4 / (287 * 293.15))
                * (2 / (1.4 + 1)) ** ((1.4 + 1) / (2 * (1.4 - 1)))
            )
        else:
            # Subsonic flow
            pressure_diff = internal_pressure - external_pressure
            if pressure_diff <= 0:
                return 0.0

            # Simplified orifice flow equation
            flow_rate = (
                self.discharge_coefficient * self.vent_valve_area * math.sqrt(2 * pressure_diff / 1.225)
            )  # Air density ≈ 1.225 kg/m³

        logger.debug(
            f"Air release rate: {flow_rate*1000:.1f} L/s "
            f"(P_int={internal_pressure/1000:.1f} kPa, "
            f"P_ext={external_pressure/1000:.1f} kPa)"
        )

        return max(0.0, flow_rate)

    def calculate_water_inflow_rate(
        self, floater_air_volume: float, floater_total_volume: float, depth: float
    ) -> float:
        """
        Calculate the rate of water entering the floater as air is released.

        Args:
            floater_air_volume: Current air volume in floater (m³)
            floater_total_volume: Total floater internal volume (m³)
            depth: Current depth of floater (m)

        Returns:
            Water inflow rate (m³/s)
        """
        # Available volume for water entry
        available_volume = floater_total_volume - floater_air_volume

        if available_volume <= 0:
            return 0.0

        # Hydrostatic pressure driving water inflow
        hydrostatic_pressure = RHO_WATER * G * depth

        # Flow rate based on hydrostatic head and opening area
        inflow_velocity = math.sqrt(2 * hydrostatic_pressure / RHO_WATER)
        inflow_rate = self.water_inflow_coefficient * self.floater_opening_area * inflow_velocity

        # Limit by available volume (can't exceed what fits)
        max_inflow_rate = available_volume / 0.1  # Assume minimum 0.1s to fill

        actual_rate = min(inflow_rate, max_inflow_rate)

        logger.debug(
            f"Water inflow rate: {actual_rate*1000:.1f} L/s "
            f"(depth={depth:.1f}m, available_vol={available_volume*1000:.1f}L)"
        )

        return actual_rate

    def calculate_bubble_escape_time(self, depth: float, bubble_volume: float) -> float:
        """
        Estimate time for air bubbles to reach surface.

        Args:
            depth: Depth from which bubbles start (m)
            bubble_volume: Volume of air bubbles (m³)

        Returns:
            Time for bubbles to reach surface (s)
        """
        # Simple model: constant rise velocity
        escape_time = depth / self.bubble_rise_velocity

        # Account for bubble dissolution during rise
        dissolution_factor = math.exp(-self.air_dissolution_rate * escape_time)
        bubble_volume * dissolution_factor

        logger.debug(f"Bubble escape: {escape_time:.1f}s, " f"volume loss: {(1-dissolution_factor)*100:.1f}%")

        return escape_time


class AutomaticVentingSystem:
    """
    Complete automatic venting system for pneumatic floaters.

    Manages the entire venting process from trigger detection through
    complete air release and water refill.
    """

    def __init__(self, trigger_config: Optional[Dict] = None, tank_height: float = 10.0):
        """
        Initialize the automatic venting system.

        Args:
            trigger_config: Configuration for venting triggers
            tank_height: Total height of the water tank (m)
        """
        # Initialize venting trigger
        if trigger_config is None:
            trigger_config = {
                "trigger_type": "position",
                "position_threshold": 9.0,  # Trigger at 9m height
                "tilt_angle_threshold": 45.0,
                "surface_breach_depth": 0.2,
            }

        self.trigger = VentingTrigger(**trigger_config)
        self.air_physics = AirReleasePhysics()
        self.tank_height = tank_height

        # Venting state tracking
        self.active_venting_floaters = {}  # floater_id -> venting_state

        logger.info(f"AutomaticVentingSystem initialized for {tank_height}m tank")

    def check_venting_trigger(self, floater_id: str, floater_position: float, floater_tilt: float = 0.0) -> bool:
        """
        Check if venting should be triggered for a specific floater.

        Args:
            floater_id: Unique identifier for the floater
            floater_position: Current floater position (m)
            floater_tilt: Current floater tilt angle (radians)

        Returns:
            True if venting should start
        """
        # Don't trigger if already venting
        if floater_id in self.active_venting_floaters:
            return False

        should_vent = self.trigger.should_trigger_venting(floater_position, floater_tilt, self.tank_height)

        if should_vent:
            logger.info(f"Venting triggered for floater {floater_id} at position {floater_position:.2f}m")

        return should_vent

    def start_venting(
        self,
        floater_id: str,
        initial_air_volume: float,
        initial_air_pressure: float,
        floater_total_volume: float,
        current_time: float,
    ) -> Dict:
        """
        Start the venting process for a floater.

        Args:
            floater_id: Unique identifier for the floater
            initial_air_volume: Initial air volume in floater (m³)
            initial_air_pressure: Initial air pressure (Pa)
            floater_total_volume: Total internal volume of floater (m³)
            current_time: Current simulation time (s)

        Returns:
            Venting state dictionary
        """
        venting_state = {
            "floater_id": floater_id,
            "start_time": current_time,
            "initial_air_volume": initial_air_volume,
            "current_air_volume": initial_air_volume,
            "initial_air_pressure": initial_air_pressure,
            "current_air_pressure": initial_air_pressure,
            "floater_total_volume": floater_total_volume,
            "water_volume": floater_total_volume - initial_air_volume,
            "total_air_released": 0.0,
            "venting_complete": False,
            "vent_completion_time": None,
        }

        self.active_venting_floaters[floater_id] = venting_state

        logger.info(
            f"Started venting for floater {floater_id}: "
            f"{initial_air_volume*1000:.1f}L at {initial_air_pressure/1000:.1f} kPa"
        )

        return venting_state

    def update_venting_process(self, floater_id: str, current_position: float, dt: float) -> Dict:
        """
        Update the venting process for a floater over a time step.

        Args:
            floater_id: Unique identifier for the floater
            current_position: Current floater position (m)
            dt: Time step (s)

        Returns:
            Updated venting state
        """
        if floater_id not in self.active_venting_floaters:
            raise ValueError(f"No active venting process for floater {floater_id}")

        state = self.active_venting_floaters[floater_id]

        if state["venting_complete"]:
            return state

        # Calculate current depth and external pressure
        current_depth = max(0.0, self.tank_height - current_position)
        external_pressure = self.air_physics.P_atm + RHO_WATER * G * current_depth

        # Calculate air release rate
        air_release_rate = self.air_physics.calculate_air_release_rate(state["current_air_pressure"], external_pressure)

        # Calculate water inflow rate
        water_inflow_rate = self.air_physics.calculate_water_inflow_rate(
            state["current_air_volume"], state["floater_total_volume"], current_depth
        )

        # Update air volume (air leaves)
        air_released_this_step = air_release_rate * dt
        state["current_air_volume"] = max(0.0, state["current_air_volume"] - air_released_this_step)
        state["total_air_released"] += air_released_this_step

        # Update water volume (water enters)
        water_added_this_step = water_inflow_rate * dt
        state["water_volume"] = min(state["floater_total_volume"], state["water_volume"] + water_added_this_step)

        # Update air pressure (approaches external pressure)
        if state["current_air_volume"] > 0:
            # Simple pressure equalization model
            pressure_equalization_rate = 2.0  # 1/s
            pressure_diff = state["current_air_pressure"] - external_pressure
            pressure_change = -pressure_diff * pressure_equalization_rate * dt
            state["current_air_pressure"] = max(external_pressure, state["current_air_pressure"] + pressure_change)
        else:
            state["current_air_pressure"] = external_pressure

        # Check for venting completion
        if state["current_air_volume"] <= 0.001:  # 1 liter threshold
            self.complete_venting(floater_id, current_position + dt)

        logger.debug(
            f"Venting update {floater_id}: "
            f"air={state['current_air_volume']*1000:.1f}L, "
            f"water={state['water_volume']*1000:.1f}L, "
            f"P={state['current_air_pressure']/1000:.1f} kPa"
        )

        return state

    def complete_venting(self, floater_id: str, completion_time: float) -> Dict:
        """
        Complete the venting process for a floater.

        Args:
            floater_id: Unique identifier for the floater
            completion_time: Time when venting completed (s)

        Returns:
            Final venting state
        """
        if floater_id not in self.active_venting_floaters:
            raise ValueError(f"No active venting process for floater {floater_id}")

        state = self.active_venting_floaters[floater_id]

        # Calculate energy that could be recovered from vented air
        total_vented_volume = state["total_air_released"]
        average_vented_pressure = (state["initial_air_pressure"] + self.air_physics.P_atm) / 2

        # Store venting results for pressure recovery system integration
        state["vented_air_volume"] = total_vented_volume
        state["average_vented_pressure"] = average_vented_pressure
        state["recoverable_energy"] = self._calculate_recoverable_energy(total_vented_volume, average_vented_pressure)

        # Finalize state
        state["current_air_volume"] = 0.0
        state["water_volume"] = state["floater_total_volume"]
        state["current_air_pressure"] = self.air_physics.P_atm
        state["venting_complete"] = True
        state["vent_completion_time"] = completion_time

        venting_duration = completion_time - state["start_time"]

        logger.info(
            f"Venting completed for floater {floater_id} in {venting_duration:.2f}s: "
            f"{state['total_air_released']*1000:.1f}L released, "
            f"recoverable energy: {state['recoverable_energy']/1000:.2f}kJ"
        )

        return state

    def _calculate_recoverable_energy(self, vented_volume: float, vented_pressure: float) -> float:
        """
        Calculate the energy that could be recovered from vented air.

        Args:
            vented_volume: Volume of vented air (m³)
            vented_pressure: Average pressure of vented air (Pa)

        Returns:
            float: Recoverable energy (J)
        """
        if vented_pressure <= self.air_physics.P_atm * 1.5:  # Must be >1.5 atm to be worthwhile
            return 0.0

        # Energy recoverable from pressure difference
        pressure_ratio = vented_pressure / self.air_physics.P_atm
        recoverable_energy = (
            self.air_physics.P_atm * vented_volume * math.log(pressure_ratio) * 0.25  # 25% recovery efficiency
        )

        return max(0.0, recoverable_energy)

    def get_total_vented_air_for_recovery(self) -> Tuple[float, float]:
        """
        Get total vented air available for pressure recovery.

        Returns:
            Tuple[float, float]: (total_volume_m3, average_pressure_pa)
        """
        completed_states = [
            state
            for state in self.active_venting_floaters.values()
            if state.get("venting_complete", False) and "vented_air_volume" in state
        ]

        if not completed_states:
            return 0.0, 0.0

        total_volume = sum(state["vented_air_volume"] for state in completed_states)

        # Weighted average pressure
        if total_volume > 0:
            weighted_pressure = (
                sum(state["vented_air_volume"] * state["average_vented_pressure"] for state in completed_states)
                / total_volume
            )
        else:
            weighted_pressure = 0.0

        return total_volume, weighted_pressure

    def get_venting_status(self, floater_id: str) -> Optional[Dict]:
        """
        Get current venting status for a floater.

        Args:
            floater_id: Unique identifier for the floater

        Returns:
            Venting status dictionary or None if not venting
        """
        return self.active_venting_floaters.get(floater_id)

    def cleanup_completed_venting(self, floater_id: str) -> bool:
        """
        Remove completed venting process from active tracking.

        Args:
            floater_id: Unique identifier for the floater

        Returns:
            True if venting process was removed
        """
        if floater_id in self.active_venting_floaters:
            state = self.active_venting_floaters[floater_id]
            if state["venting_complete"]:
                del self.active_venting_floaters[floater_id]
                logger.info(f"Cleaned up completed venting for floater {floater_id}")
                return True
        return False

    def get_active_venting_floaters(self) -> List[str]:
        """
        Get list of floaters currently undergoing venting.

        Returns:
            List of floater IDs
        """
        return list(self.active_venting_floaters.keys())

    def get_system_status(self) -> Dict:
        """
        Get comprehensive status of the venting system.

        Returns:
            System status dictionary
        """
        active_count = len(self.active_venting_floaters)
        completed_count = sum(1 for state in self.active_venting_floaters.values() if state["venting_complete"])

        return {
            "active_venting_count": active_count,
            "completed_venting_count": completed_count,
            "processing_venting_count": active_count - completed_count,
            "trigger_type": self.trigger.trigger_type,
            "trigger_threshold": self.trigger.position_threshold,
            "tank_height": self.tank_height,
        }
