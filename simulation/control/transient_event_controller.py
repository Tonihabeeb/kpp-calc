"""
Transient Event Controller for KPP System
Coordinates startup, emergency response, and grid disturbance handling.
"""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional

from simulation.control.emergency_response import EmergencyResponseSystem, EmergencyType
from simulation.control.grid_disturbance_handler import (
    DisturbanceType,
    GridDisturbanceHandler,
    ResponseMode,
)
from simulation.control.startup_controller import StartupController, StartupPhase

logger = logging.getLogger(__name__)


class SystemState(Enum):
    """Overall system states"""

    OFFLINE = "offline"
    STARTING = "starting"
    OPERATIONAL = "operational"
    EMERGENCY = "emergency"
    SHUTDOWN = "shutdown"
    FAULT = "fault"


class TransientEventPriority(Enum):
    """Event priority levels"""

    EMERGENCY = 1  # Emergency conditions override everything
    STARTUP = 2  # Startup sequences have high priority
    GRID_SUPPORT = 3  # Grid support responses
    NORMAL = 4  # Normal operational events


@dataclass
class SystemStatus:
    """Overall system status"""

    state: SystemState
    startup_active: bool = False
    emergency_active: bool = False
    grid_disturbance_active: bool = False
    operational_time: float = 0.0
    total_startup_count: int = 0
    total_emergency_count: int = 0
    total_grid_events: int = 0


class TransientEventController:
    """
    Coordinates all transient events including startup, emergency response, and grid disturbances.

    Features:
    - Unified event coordination and prioritization
    - State machine management for system states
    - Event conflict resolution
    - Comprehensive system monitoring
    - Performance tracking and optimization
    """

    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize transient event controller.

        Args:
            config: Configuration parameters
        """
        self.config = config or {}

        # Initialize sub-controllers
        self.startup_controller = StartupController(self.config.get("startup", {}))
        self.emergency_system = EmergencyResponseSystem(
            self.config.get("emergency", {})
        )
        self.grid_handler = GridDisturbanceHandler(self.config.get("grid", {}))

        # System state management
        self.system_state = SystemState.OFFLINE
        self.previous_state = SystemState.OFFLINE
        self.state_change_time = 0.0
        self.operational_start_time = 0.0

        # Event coordination
        self.active_events = []
        self.event_queue = []
        self.current_priority = TransientEventPriority.NORMAL

        # System status tracking
        self.status = SystemStatus(state=SystemState.OFFLINE)

        # Performance metrics
        self.metrics = {
            "state_transitions": 0,
            "average_startup_time": 0.0,
            "average_emergency_response_time": 0.0,
            "grid_events_handled": 0,
            "system_availability": 0.0,
            "total_operational_time": 0.0,
        }

        # Configuration parameters
        self.auto_startup_enabled = self.config.get("auto_startup", True)
        self.auto_recovery_enabled = self.config.get("auto_recovery", True)
        self.grid_support_enabled = self.config.get("grid_support", True)

        logger.info("TransientEventController initialized")

    def update_transient_events(self, system_state: Dict, current_time: float) -> Dict:
        """
        Update all transient event handling.

        Args:
            system_state: Current system state
            current_time: Current simulation time

        Returns:
            Dict: Coordinated transient event commands
        """
        # Update system status
        self._update_system_status(system_state, current_time)

        # Process emergency conditions (highest priority)
        emergency_commands = self.emergency_system.monitor_emergency_conditions(
            system_state, current_time
        )

        # Process grid disturbances
        grid_commands = self.grid_handler.monitor_grid_conditions(
            system_state, current_time
        )

        # Process startup sequences
        startup_commands = self.startup_controller.update_startup_sequence(
            system_state, current_time
        )

        # Coordinate and prioritize commands
        coordinated_commands = self._coordinate_transient_commands(
            emergency_commands, grid_commands, startup_commands, current_time
        )

        # Update system state based on coordinated response
        self._update_system_state(coordinated_commands, current_time)

        # Update performance metrics
        self._update_metrics(current_time)

        return coordinated_commands

    def _update_system_status(self, system_state: Dict, current_time: float):
        """Update overall system status"""
        self.status.startup_active = self.startup_controller.is_startup_active
        self.status.emergency_active = self.emergency_system.emergency_active
        self.status.grid_disturbance_active = (
            len(self.grid_handler.active_disturbances) > 0
        )

        # Update operational time
        if self.system_state == SystemState.OPERATIONAL:
            if self.operational_start_time > 0:
                self.status.operational_time = (
                    current_time - self.operational_start_time
                )

    def _coordinate_transient_commands(
        self,
        emergency_cmds: Dict,
        grid_cmds: Dict,
        startup_cmds: Dict,
        current_time: float,
    ) -> Dict:
        """Coordinate and prioritize transient event commands"""

        coordinated = {
            "transient_event_active": False,
            "primary_event_type": "none",
            "event_priority": TransientEventPriority.NORMAL.value,
            "system_state": self.system_state.value,
            "coordinated_commands": {},
        }

        # Priority 1: Emergency conditions override everything
        if emergency_cmds.get("emergency_active", False):
            coordinated.update(
                {
                    "transient_event_active": True,
                    "primary_event_type": "emergency",
                    "event_priority": TransientEventPriority.EMERGENCY.value,
                    "emergency_commands": emergency_cmds,
                    "coordinated_commands": emergency_cmds,
                }
            )
            self.current_priority = TransientEventPriority.EMERGENCY
            return coordinated

        # Priority 2: Startup sequences (when not in emergency)
        if startup_cmds.get("startup_active", False):
            coordinated.update(
                {
                    "transient_event_active": True,
                    "primary_event_type": "startup",
                    "event_priority": TransientEventPriority.STARTUP.value,
                    "startup_commands": startup_cmds,
                    "coordinated_commands": startup_cmds,
                }
            )
            self.current_priority = TransientEventPriority.STARTUP

            # Allow limited grid support during startup if configured
            if self.grid_support_enabled and grid_cmds.get(
                "grid_disturbance_active", False
            ):
                # Only minor grid responses during startup
                if grid_cmds.get("response_mode") in [
                    "ride_through",
                    "frequency_support",
                ]:
                    coordinated["coordinated_commands"].update(
                        {
                            "grid_support": {
                                "limited_response": True,
                                "response_mode": grid_cmds.get("response_mode"),
                                "response_magnitude": min(
                                    0.1, grid_cmds.get("frequency_response", 0.0)
                                ),
                            }
                        }
                    )

            return coordinated

        # Priority 3: Grid support responses (when operational)
        if (
            grid_cmds.get("grid_disturbance_active", False)
            and self.grid_support_enabled
        ):
            coordinated.update(
                {
                    "transient_event_active": True,
                    "primary_event_type": "grid_support",
                    "event_priority": TransientEventPriority.GRID_SUPPORT.value,
                    "grid_commands": grid_cmds,
                    "coordinated_commands": grid_cmds,
                }
            )
            self.current_priority = TransientEventPriority.GRID_SUPPORT
            return coordinated

        # Priority 4: Normal operation
        self.current_priority = TransientEventPriority.NORMAL
        coordinated.update(
            {"system_state": self.system_state.value, "normal_operation": True}
        )

        return coordinated

    def _update_system_state(self, commands: Dict, current_time: float):
        """Update overall system state based on transient events"""
        previous_state = self.system_state

        # Determine new system state based on priority
        # Priority 1: Emergency conditions (highest priority)
        if commands.get("emergency_commands", {}).get("emergency_active", False):
            new_state = SystemState.EMERGENCY

            # Check for shutdown
            if commands.get("emergency_commands", {}).get("emergency_shutdown", False):
                new_state = SystemState.SHUTDOWN

        # Priority 2: Startup completion
        elif commands.get("startup_commands", {}).get("startup_complete", False):
            new_state = SystemState.OPERATIONAL
            self.operational_start_time = current_time

        # Priority 3: Startup active
        elif commands.get("startup_commands", {}).get("startup_active", False):
            new_state = SystemState.STARTING

        # Priority 4: Startup failed
        elif commands.get("startup_commands", {}).get("startup_failed", False):
            new_state = SystemState.FAULT

        # Priority 5: Maintain operational state if currently operational
        elif self.system_state == SystemState.OPERATIONAL:
            new_state = SystemState.OPERATIONAL

        # Default: Offline
        else:
            new_state = SystemState.OFFLINE

        # Update state if changed
        if new_state != self.system_state:
            logger.info(
                f"System state transition: {self.system_state.value} → {new_state.value}"
            )
            self.previous_state = self.system_state
            self.system_state = new_state
            self.status.state = new_state
            self.state_change_time = current_time
            self.metrics["state_transitions"] += 1

            # Update counters
            if new_state == SystemState.STARTING:
                self.status.total_startup_count += 1
            elif new_state == SystemState.EMERGENCY:
                self.status.total_emergency_count += 1

    def initiate_startup(
        self, current_time: float, reason: str = "Manual startup"
    ) -> bool:
        """
        Initiate system startup sequence.

        Args:
            current_time: Current simulation time
            reason: Reason for startup initiation

        Returns:
            bool: True if startup initiated successfully
        """
        if self.system_state in [SystemState.EMERGENCY, SystemState.SHUTDOWN]:
            logger.warning(f"Cannot start system in {self.system_state.value} state")
            return False

        logger.info(f"Initiating system startup: {reason}")
        success = self.startup_controller.initiate_startup(current_time)

        if success:
            self.system_state = SystemState.STARTING
            self.state_change_time = current_time

        return success

    def trigger_emergency_stop(self, reason: str, current_time: float) -> Dict:
        """
        Trigger emergency stop sequence.

        Args:
            reason: Reason for emergency stop
            current_time: Current simulation time

        Returns:
            Dict: Emergency stop response
        """
        logger.critical(f"Emergency stop triggered: {reason}")

        # Trigger emergency response
        emergency_response = self.emergency_system.trigger_manual_emergency_stop(
            reason, current_time
        )

        # Abort any active startup
        if self.startup_controller.is_startup_active:
            self.startup_controller.abort_startup(f"Emergency stop: {reason}")

        # Update system state
        self.system_state = SystemState.EMERGENCY
        self.state_change_time = current_time

        return emergency_response

    def acknowledge_event(
        self, event_type: str, event_id: Optional[str] = None
    ) -> bool:
        """
        Acknowledge a transient event.

        Args:
            event_type: Type of event to acknowledge
            event_id: Specific event ID (if applicable)

        Returns:
            bool: True if event acknowledged successfully
        """
        if event_type == "emergency":
            return self.emergency_system.acknowledge_emergency(event_id or event_type)

        # Add other event acknowledgments as needed
        return False

    def _update_metrics(self, current_time: float):
        """Update performance metrics"""

        # Update startup metrics
        startup_status = self.startup_controller.get_startup_status()
        if startup_status.get("startup_complete", False):
            startup_time = startup_status.get("metrics", {}).get("startup_time", 0.0)
            if startup_time > 0:
                total_startups = self.status.total_startup_count
                avg_startup = self.metrics["average_startup_time"]
                self.metrics["average_startup_time"] = (
                    avg_startup * (total_startups - 1) + startup_time
                ) / total_startups

        # Update emergency response metrics
        emergency_status = self.emergency_system.get_emergency_status()
        emergency_metrics = emergency_status.get("metrics", {})
        self.metrics["average_emergency_response_time"] = emergency_metrics.get(
            "average_response_time", 0.0
        )

        # Update grid event metrics
        grid_status = self.grid_handler.get_disturbance_status()
        self.metrics["grid_events_handled"] = grid_status.get(
            "disturbance_history_count", 0
        )

        # Update operational time and availability
        if self.system_state == SystemState.OPERATIONAL:
            self.metrics[
                "total_operational_time"
            ] += 0.1  # Assuming 0.1s simulation timestep

        # Calculate system availability
        total_time = current_time if current_time > 0 else 1.0
        self.metrics["system_availability"] = (
            self.metrics["total_operational_time"] / total_time
        ) * 100.0

    def get_transient_status(self) -> Dict:
        """Get comprehensive transient event status"""
        return {
            "system_state": self.system_state.value,
            "previous_state": self.previous_state.value,
            "state_change_time": self.state_change_time,
            "current_priority": self.current_priority.value,
            "status": {
                "startup_active": self.status.startup_active,
                "emergency_active": self.status.emergency_active,
                "grid_disturbance_active": self.status.grid_disturbance_active,
                "operational_time": self.status.operational_time,
                "total_startup_count": self.status.total_startup_count,
                "total_emergency_count": self.status.total_emergency_count,
                "total_grid_events": self.status.total_grid_events,
            },
            "startup_status": self.startup_controller.get_startup_status(),
            "emergency_status": self.emergency_system.get_emergency_status(),
            "grid_status": self.grid_handler.get_disturbance_status(),
            "metrics": self.metrics,
            "configuration": {
                "auto_startup_enabled": self.auto_startup_enabled,
                "auto_recovery_enabled": self.auto_recovery_enabled,
                "grid_support_enabled": self.grid_support_enabled,
            },
        }

    def reset(self):
        """Reset all transient event controllers"""
        logger.info("TransientEventController reset")

        # Reset sub-controllers
        self.startup_controller.reset()
        self.emergency_system.reset()
        self.grid_handler.reset()

        # Reset system state
        self.system_state = SystemState.OFFLINE
        self.previous_state = SystemState.OFFLINE
        self.state_change_time = 0.0
        self.operational_start_time = 0.0

        # Reset status
        self.status = SystemStatus(state=SystemState.OFFLINE)

        # Reset events
        self.active_events = []
        self.event_queue = []
        self.current_priority = TransientEventPriority.NORMAL
