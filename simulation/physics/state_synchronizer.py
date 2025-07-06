"""
State Synchronization System for KPP Simulation (Stage 2)
Ensures immediate synchronization between floater state changes and physics calculations.
"""

import logging
import time

logger = logging.getLogger(__name__)


class StateSynchronizer:
    """
    Manages synchronization between floater state changes and physics engine calculations.
    Ensures that mass updates, state transitions, and position changes are immediately
    reflected in all dependent systems.
    """

    def __init__(self, physics_engine, event_handler):
        """
        Initialize state synchronizer.

        Args:
            physics_engine: Reference to physics engine
            event_handler: Reference to event handler
        """
        self.physics_engine = physics_engine
        self.event_handler = event_handler

        # State tracking
        self.floater_snapshots = {}  # floater_id -> last known state
        self.pending_updates = []  # Queue of pending synchronization updates
        self.sync_validation_enabled = True

        # Performance tracking
        self.sync_operations = 0
        self.sync_failures = 0
        self.last_sync_time = 0.0

        logger.info("StateSynchronizer initialized")

    def synchronize_floater_state(self, floater, floater_id, immediate=True):
        """
        Synchronize a single floater's state across all systems.

        Args:
            floater: Floater object to synchronize
            floater_id: Unique identifier for the floater
            immediate (bool): If True, apply changes immediately

        Returns:
            dict: Synchronization result
        """
        try:
            # Capture current state
            current_state = self._capture_floater_state(floater, floater_id)

            # Check if state changed
            state_changed = self._detect_state_change(floater_id, current_state)

            if state_changed:
                # Apply synchronization
                if immediate:
                    result = self._apply_immediate_sync(floater, floater_id, current_state)
                else:
                    result = self._queue_sync_update(floater, floater_id, current_state)

                # Update snapshot
                self.floater_snapshots[floater_id] = current_state.copy()

                # Validate synchronization if enabled
                if self.sync_validation_enabled:
                    self._validate_synchronization(floater, floater_id, current_state)

                self.sync_operations += 1

                logger.debug(f"Synchronized floater {floater_id}: {result['changes']}")

                return result
            else:
                return {"success": True, "changes": [], "reason": "no_change"}

        except Exception as e:
            self.sync_failures += 1
            logger.error(f"Synchronization failed for floater {floater_id}: {e}")
            return {"success": False, "error": str(e)}

    def synchronize_all_floaters(self, floaters, current_time=0.0):
        """
        Synchronize all floaters in the system.

        Args:
            floaters: List of floater objects
            current_time: Current simulation time

        Returns:
            dict: Comprehensive synchronization results
        """
        self.last_sync_time = current_time
        sync_results = []
        total_changes = 0

        for i, floater in enumerate(floaters):
            result = self.synchronize_floater_state(floater, i, immediate=True)
            sync_results.append(result)

            if result["success"]:
                total_changes += len(result.get("changes", []))

        # Process any pending updates
        pending_processed = self._process_pending_updates()

        # Update physics engine energy tracking
        if hasattr(self.event_handler, "energy_input"):
            self.physics_engine.energy_input = self.event_handler.energy_input

        return {
            "synchronized_floaters": len(floaters),
            "total_changes": total_changes,
            "sync_results": sync_results,
            "pending_updates_processed": pending_processed,
            "sync_operations_total": self.sync_operations,
            "sync_failure_rate": self.sync_failures / max(1, self.sync_operations),
            "last_sync_time": current_time,
        }

    def validate_system_consistency(self, floaters):
        """
        Validate that all systems are in consistent state.

        Args:
            floaters: List of floater objects

        Returns:
            dict: Validation results
        """
        inconsistencies = []

        for i, floater in enumerate(floaters):
            # Check mass consistency
            mass_issues = self._validate_mass_consistency(floater, i)
            if mass_issues:
                inconsistencies.extend(mass_issues)

            # Check state consistency
            state_issues = self._validate_state_consistency(floater, i)
            if state_issues:
                inconsistencies.extend(state_issues)

            # Check physics consistency
            physics_issues = self._validate_physics_consistency(floater, i)
            if physics_issues:
                inconsistencies.extend(physics_issues)

        return {
            "consistent": len(inconsistencies) == 0,
            "inconsistencies": inconsistencies,
            "total_floaters_checked": len(floaters),
        }

    def _capture_floater_state(self, floater, floater_id):
        """Capture complete floater state."""
        return {
            "mass": getattr(floater, "mass", 0.0),
            "state": getattr(floater, "state", "unknown"),
            "is_filled": getattr(floater, "is_filled", False),
            "volume": getattr(floater, "volume", 0.0),
            "container_mass": getattr(floater, "container_mass", 0.0),
            "angle": getattr(floater, "angle", getattr(floater, "theta", 0.0)),
            "velocity": getattr(floater, "velocity", 0.0),
            "position": getattr(floater, "position", 0.0),
            "timestamp": time.time(),
        }

    def _detect_state_change(self, floater_id, current_state):
        """Detect if floater state has changed."""
        if floater_id not in self.floater_snapshots:
            return True  # First time seeing this floater

        previous_state = self.floater_snapshots[floater_id]

        # Check critical state changes
        critical_changes = ["mass", "state", "is_filled"]

        for key in critical_changes:
            if current_state.get(key) != previous_state.get(key):
                return True

        # Check significant position/velocity changes
        angle_change = abs(current_state.get("angle", 0) - previous_state.get("angle", 0))
        if angle_change > 0.1:  # Significant angular change
            return True

        return False

    def _apply_immediate_sync(self, floater, floater_id, current_state):
        """Apply synchronization changes immediately."""
        changes = []

        # Synchronize mass with state
        if current_state["state"] == "light" and current_state["is_filled"]:
            # Air-filled state
            expected_mass = current_state["container_mass"]
            if abs(floater.mass - expected_mass) > 0.1:
                floater.mass = expected_mass
                changes.append(f"mass_corrected_to_{expected_mass}")

        elif current_state["state"] == "heavy" and not current_state["is_filled"]:
            # Water-filled state
            water_mass = 1000.0 * current_state["volume"]  # RHO_WATER * volume
            expected_mass = current_state["container_mass"] + water_mass
            if abs(floater.mass - expected_mass) > 0.1:
                floater.mass = expected_mass
                changes.append(f"mass_corrected_to_{expected_mass}")

        # Ensure state consistency
        if hasattr(floater, "state") and hasattr(floater, "is_filled"):
            if floater.state == "light" and not floater.is_filled:
                floater.is_filled = True
                changes.append("is_filled_corrected_to_true")
            elif floater.state == "heavy" and floater.is_filled:
                floater.is_filled = False
                changes.append("is_filled_corrected_to_false")

        # Update physics engine if needed
        if hasattr(floater, "velocity") and hasattr(self.physics_engine, "v_chain"):
            # Sync floater velocity with chain velocity if appropriate
            if self.physics_engine.is_floater_ascending(floater):
                expected_velocity = self.physics_engine.v_chain
            else:
                expected_velocity = -self.physics_engine.v_chain

            if abs(floater.velocity - expected_velocity) > 0.1:
                floater.velocity = expected_velocity
                changes.append(f"velocity_synced_to_{expected_velocity:.3f}")

        return {"success": True, "changes": changes, "floater_id": floater_id}

    def _queue_sync_update(self, floater, floater_id, current_state):
        """Queue synchronization update for later processing."""
        update = {
            "floater": floater,
            "floater_id": floater_id,
            "state": current_state,
            "timestamp": time.time(),
        }

        self.pending_updates.append(update)

        return {
            "success": True,
            "changes": ["queued_for_sync"],
            "floater_id": floater_id,
        }

    def _process_pending_updates(self):
        """Process all pending synchronization updates."""
        processed = 0

        while self.pending_updates:
            update = self.pending_updates.pop(0)

            try:
                self._apply_immediate_sync(update["floater"], update["floater_id"], update["state"])
                processed += 1
            except Exception as e:
                logger.error(f"Failed to process pending update: {e}")

        return processed

    def _validate_synchronization(self, floater, floater_id, expected_state):
        """Validate that synchronization was successful."""
        actual_state = self._capture_floater_state(floater, floater_id)

        # Check critical properties
        if actual_state["mass"] != expected_state["mass"]:
            logger.warning(f"Mass sync validation failed for floater {floater_id}")

        if actual_state["state"] != expected_state["state"]:
            logger.warning(f"State sync validation failed for floater {floater_id}")

    def _validate_mass_consistency(self, floater, floater_id):
        """Validate mass consistency with state."""
        issues = []

        container_mass = getattr(floater, "container_mass", 50.0)
        volume = getattr(floater, "volume", 0.04)
        water_mass = 1000.0 * volume

        if hasattr(floater, "state"):
            if floater.state == "light":
                expected_mass = container_mass
                if abs(floater.mass - expected_mass) > 1.0:
                    issues.append(
                        f"Floater {floater_id}: light state but mass={floater.mass:.1f}, expected={expected_mass:.1f}"
                    )

            elif floater.state == "heavy":
                expected_mass = container_mass + water_mass
                if abs(floater.mass - expected_mass) > 1.0:
                    issues.append(
                        f"Floater {floater_id}: heavy state but mass={floater.mass:.1f}, expected={expected_mass:.1f}"
                    )

        return issues

    def _validate_state_consistency(self, floater, floater_id):
        """Validate state field consistency."""
        issues = []

        if hasattr(floater, "state") and hasattr(floater, "is_filled"):
            if floater.state == "light" and not floater.is_filled:
                issues.append(f"Floater {floater_id}: state=light but is_filled=False")
            elif floater.state == "heavy" and floater.is_filled:
                issues.append(f"Floater {floater_id}: state=heavy but is_filled=True")

        return issues

    def _validate_physics_consistency(self, floater, floater_id):
        """Validate physics-related consistency."""
        issues = []

        # Check velocity consistency with chain
        if hasattr(floater, "velocity") and hasattr(self.physics_engine, "v_chain"):
            chain_velocity = self.physics_engine.v_chain

            if self.physics_engine.is_floater_ascending(floater):
                expected_velocity = chain_velocity
            else:
                expected_velocity = -chain_velocity

            if abs(floater.velocity - expected_velocity) > 0.5:
                issues.append(
                    f"Floater {floater_id}: velocity={floater.velocity:.3f}, expected={expected_velocity:.3f}"
                )

        return issues

    def get_sync_status(self):
        """Get synchronization system status."""
        return {
            "sync_operations": self.sync_operations,
            "sync_failures": self.sync_failures,
            "success_rate": (self.sync_operations - self.sync_failures) / max(1, self.sync_operations),
            "pending_updates": len(self.pending_updates),
            "tracked_floaters": len(self.floater_snapshots),
            "last_sync_time": self.last_sync_time,
            "validation_enabled": self.sync_validation_enabled,
        }
