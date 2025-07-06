"""
Grid Disturbance Handler for KPP System
Handles grid frequency and voltage disturbances with appropriate responses.
"""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional

import numpy as np

logger = logging.getLogger(__name__)


class DisturbanceType(Enum):
    """Types of grid disturbances"""

    FREQUENCY_HIGH = "frequency_high"
    FREQUENCY_LOW = "frequency_low"
    VOLTAGE_HIGH = "voltage_high"
    VOLTAGE_LOW = "voltage_low"
    VOLTAGE_UNBALANCE = "voltage_unbalance"
    HARMONIC_DISTORTION = "harmonic_distortion"
    TRANSIENT_SPIKE = "transient_spike"
    GRID_OUTAGE = "grid_outage"


class ResponseMode(Enum):
    """Grid disturbance response modes"""

    RIDE_THROUGH = "ride_through"
    FREQUENCY_SUPPORT = "frequency_support"
    VOLTAGE_SUPPORT = "voltage_support"
    LOAD_SHEDDING = "load_shedding"
    DISCONNECT = "disconnect"


@dataclass
class DisturbanceEvent:
    """Grid disturbance event record"""

    disturbance_type: DisturbanceType
    start_time: float
    end_time: Optional[float] = None
    magnitude: float = 0.0
    duration: float = 0.0
    response_mode: ResponseMode = ResponseMode.RIDE_THROUGH
    response_time: float = 0.0
    resolved: bool = False


@dataclass
class GridLimits:
    """Grid operating limits and thresholds"""

    # Frequency limits (Hz)
    nominal_frequency: float = 50.0
    frequency_deadband: float = 0.05  # ±0.05 Hz normal operation
    frequency_warning: float = 0.1  # ±0.1 Hz warning threshold
    frequency_critical: float = 0.5  # ±0.5 Hz critical threshold
    frequency_emergency: float = 1.0  # ±1.0 Hz emergency threshold

    # Voltage limits (V)
    nominal_voltage: float = 480.0
    voltage_deadband: float = 12.0  # ±2.5% normal operation
    voltage_warning: float = 24.0  # ±5% warning threshold
    voltage_critical: float = 48.0  # ±10% critical threshold
    voltage_emergency: float = 72.0  # ±15% emergency threshold

    # Response timing (seconds)
    fast_response_time: float = 0.1
    normal_response_time: float = 1.0
    slow_response_time: float = 5.0


class GridDisturbanceHandler:
    """
    Handles grid disturbances and implements appropriate response strategies.

    Features:
    - Real-time grid condition monitoring
    - Disturbance classification and response
    - Frequency and voltage support capabilities
    - Load shedding and ride-through logic
    - Grid code compliance
    """

    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize grid disturbance handler.

        Args:
            config: Configuration parameters
        """
        self.config = config or {}
        self.limits = GridLimits()

        # Grid state tracking
        self.grid_frequency = self.limits.nominal_frequency
        self.grid_voltage = self.limits.nominal_voltage
        self.grid_connected = True

        # Disturbance tracking
        self.active_disturbances: List[DisturbanceEvent] = []
        self.disturbance_history: List[DisturbanceEvent] = []
        self.current_response_mode = ResponseMode.RIDE_THROUGH

        # Response state
        self.frequency_support_active = False
        self.voltage_support_active = False
        self.load_shedding_active = False
        self.ride_through_active = False

        # Performance metrics
        self.response_metrics = {
            "total_disturbances": 0,
            "successful_ride_throughs": 0,
            "frequency_support_events": 0,
            "voltage_support_events": 0,
            "load_shedding_events": 0,
            "disconnection_events": 0,
            "average_response_time": 0.0,
        }

        # Frequency response parameters
        self.frequency_droop = self.config.get("frequency_droop", 0.05)  # 5% droop
        self.frequency_deadband = self.config.get("frequency_deadband", 0.05)  # Hz
        self.max_frequency_response = self.config.get("max_frequency_response", 0.2)  # 20% power

        # Voltage support parameters
        self.voltage_droop = self.config.get("voltage_droop", 0.02)  # 2% droop
        self.voltage_deadband = self.config.get("voltage_deadband", 12.0)  # V
        self.max_reactive_power = self.config.get("max_reactive_power", 0.3)  # 30% of rated

        logger.info("GridDisturbanceHandler initialized")

    def monitor_grid_conditions(self, system_state: Dict, current_time: float) -> Dict:
        """
        Monitor grid conditions and detect disturbances.

        Args:
            system_state: Current system state
            current_time: Current simulation time

        Returns:
            Dict: Grid disturbance status and response commands
        """
        # Update grid measurements
        self.grid_frequency = system_state.get("grid_frequency", self.limits.nominal_frequency)
        self.grid_voltage = system_state.get("grid_voltage", self.limits.nominal_voltage)
        self.grid_connected = system_state.get("grid_connected", True)

        # Detect new disturbances
        self._detect_grid_disturbances(current_time)

        # Process active disturbances
        response_commands = self._process_disturbances(system_state, current_time)

        # Update disturbance resolution
        self._update_disturbance_resolution(current_time)

        # Update metrics
        self._update_response_metrics()

        return response_commands

    def _detect_grid_disturbances(self, current_time: float) -> List[DisturbanceEvent]:
        """Detect grid disturbances based on current measurements"""
        new_disturbances = []

        # Check frequency disturbances
        freq_error = abs(self.grid_frequency - self.limits.nominal_frequency)
        if freq_error > self.limits.frequency_deadband:
            disturbance_type = (
                DisturbanceType.FREQUENCY_HIGH
                if self.grid_frequency > self.limits.nominal_frequency
                else DisturbanceType.FREQUENCY_LOW
            )

            # Check if this is a new disturbance
            if not any(d.disturbance_type == disturbance_type and not d.resolved for d in self.active_disturbances):
                new_disturbances.append(
                    DisturbanceEvent(
                        disturbance_type=disturbance_type,
                        start_time=current_time,
                        magnitude=freq_error,
                    )
                )

        # Check voltage disturbances
        voltage_error = abs(self.grid_voltage - self.limits.nominal_voltage)
        if voltage_error > self.limits.voltage_deadband:
            disturbance_type = (
                DisturbanceType.VOLTAGE_HIGH
                if self.grid_voltage > self.limits.nominal_voltage
                else DisturbanceType.VOLTAGE_LOW
            )

            # Check if this is a new disturbance
            if not any(d.disturbance_type == disturbance_type and not d.resolved for d in self.active_disturbances):
                new_disturbances.append(
                    DisturbanceEvent(
                        disturbance_type=disturbance_type,
                        start_time=current_time,
                        magnitude=voltage_error,
                    )
                )

        # Check for grid outage
        if not self.grid_connected:
            if not any(
                d.disturbance_type == DisturbanceType.GRID_OUTAGE and not d.resolved for d in self.active_disturbances
            ):
                new_disturbances.append(
                    DisturbanceEvent(
                        disturbance_type=DisturbanceType.GRID_OUTAGE,
                        start_time=current_time,
                        magnitude=1.0,  # Binary condition
                    )
                )

        # Add new disturbances to active list
        for disturbance in new_disturbances:
            self.active_disturbances.append(disturbance)
            self.disturbance_history.append(disturbance)
            self.response_metrics["total_disturbances"] += 1
            logger.warning(
                f"Grid disturbance detected: {disturbance.disturbance_type.value} - magnitude: {disturbance.magnitude:.3f}"
            )

        return new_disturbances

    def _process_disturbances(self, system_state: Dict, current_time: float) -> Dict:
        """Process active disturbances and generate response commands"""

        if not self.active_disturbances:
            return self._generate_normal_operation_commands()

        # Determine response mode based on disturbance severity
        response_mode = self._determine_response_mode()
        self.current_response_mode = response_mode

        # Generate response commands based on mode
        if response_mode == ResponseMode.RIDE_THROUGH:
            return self._generate_ride_through_commands(system_state, current_time)

        elif response_mode == ResponseMode.FREQUENCY_SUPPORT:
            return self._generate_frequency_support_commands(system_state, current_time)

        elif response_mode == ResponseMode.VOLTAGE_SUPPORT:
            return self._generate_voltage_support_commands(system_state, current_time)

        elif response_mode == ResponseMode.LOAD_SHEDDING:
            return self._generate_load_shedding_commands(system_state, current_time)

        elif response_mode == ResponseMode.DISCONNECT:
            return self._generate_disconnect_commands(system_state, current_time)

        else:
            return self._generate_normal_operation_commands()

    def _determine_response_mode(self) -> ResponseMode:
        """Determine appropriate response mode based on active disturbances"""

        # Check for emergency conditions (require disconnection)
        for disturbance in self.active_disturbances:
            if not disturbance.resolved:
                if disturbance.disturbance_type == DisturbanceType.GRID_OUTAGE:
                    return ResponseMode.DISCONNECT

                if (
                    disturbance.disturbance_type in [DisturbanceType.FREQUENCY_HIGH, DisturbanceType.FREQUENCY_LOW]
                    and disturbance.magnitude > self.limits.frequency_emergency
                ):
                    return ResponseMode.DISCONNECT

                if (
                    disturbance.disturbance_type in [DisturbanceType.VOLTAGE_HIGH, DisturbanceType.VOLTAGE_LOW]
                    and disturbance.magnitude > self.limits.voltage_emergency
                ):
                    return ResponseMode.DISCONNECT

        # Check for critical conditions (require load shedding)
        for disturbance in self.active_disturbances:
            if not disturbance.resolved:
                if (
                    disturbance.disturbance_type in [DisturbanceType.FREQUENCY_HIGH, DisturbanceType.FREQUENCY_LOW]
                    and disturbance.magnitude > self.limits.frequency_critical
                ):
                    return ResponseMode.LOAD_SHEDDING

                if (
                    disturbance.disturbance_type in [DisturbanceType.VOLTAGE_HIGH, DisturbanceType.VOLTAGE_LOW]
                    and disturbance.magnitude > self.limits.voltage_critical
                ):
                    return ResponseMode.LOAD_SHEDDING

        # Check for conditions requiring active support
        for disturbance in self.active_disturbances:
            if not disturbance.resolved:
                if (
                    disturbance.disturbance_type in [DisturbanceType.FREQUENCY_HIGH, DisturbanceType.FREQUENCY_LOW]
                    and disturbance.magnitude > self.limits.frequency_warning
                ):
                    return ResponseMode.FREQUENCY_SUPPORT

                if (
                    disturbance.disturbance_type in [DisturbanceType.VOLTAGE_HIGH, DisturbanceType.VOLTAGE_LOW]
                    and disturbance.magnitude > self.limits.voltage_warning
                ):
                    return ResponseMode.VOLTAGE_SUPPORT

        # Default to ride-through for minor disturbances
        return ResponseMode.RIDE_THROUGH

    def _generate_normal_operation_commands(self) -> Dict:
        """Generate commands for normal grid operation"""
        return {
            "grid_disturbance_active": False,
            "response_mode": "normal",
            "frequency_support_active": False,
            "voltage_support_active": False,
            "load_shedding_active": False,
            "grid_disconnect_required": False,
        }

    def _generate_ride_through_commands(self, system_state: Dict, current_time: float) -> Dict:
        """Generate ride-through commands for minor disturbances"""
        self.ride_through_active = True
        self.response_metrics["successful_ride_throughs"] += 1

        return {
            "grid_disturbance_active": True,
            "response_mode": "ride_through",
            "ride_through_active": True,
            "monitoring_enhanced": True,
            "protection_sensitivity_reduced": True,
            "control_commands": {
                "damping_increased": True,
                "response_time_reduced": True,
            },
        }

    def _generate_frequency_support_commands(self, system_state: Dict, current_time: float) -> Dict:
        """Generate frequency support commands"""
        self.frequency_support_active = True
        self.response_metrics["frequency_support_events"] += 1

        # Calculate frequency response
        freq_error = self.grid_frequency - self.limits.nominal_frequency
        frequency_response = 0.0

        if abs(freq_error) > self.frequency_deadband:
            # Droop control: reduce power for high frequency, increase for low frequency
            frequency_response = -freq_error * self.frequency_droop
            frequency_response = np.clip(
                frequency_response,
                -self.max_frequency_response,
                self.max_frequency_response,
            )

        return {
            "grid_disturbance_active": True,
            "response_mode": "frequency_support",
            "frequency_support_active": True,
            "frequency_error": freq_error,
            "frequency_response": frequency_response,
            "control_commands": {
                "power_adjustment": frequency_response,
                "response_time": self.limits.fast_response_time,
                "droop_control_active": True,
            },
        }

    def _generate_voltage_support_commands(self, system_state: Dict, current_time: float) -> Dict:
        """Generate voltage support commands"""
        self.voltage_support_active = True
        self.response_metrics["voltage_support_events"] += 1

        # Calculate voltage response
        voltage_error = self.grid_voltage - self.limits.nominal_voltage
        voltage_response = 0.0

        if abs(voltage_error) > self.voltage_deadband:
            # Reactive power support: inject reactive power for low voltage, absorb for high voltage
            voltage_response = -voltage_error * self.voltage_droop
            voltage_response = np.clip(voltage_response, -self.max_reactive_power, self.max_reactive_power)

        return {
            "grid_disturbance_active": True,
            "response_mode": "voltage_support",
            "voltage_support_active": True,
            "voltage_error": voltage_error,
            "voltage_response": voltage_response,
            "control_commands": {
                "reactive_power_adjustment": voltage_response,
                "response_time": self.limits.normal_response_time,
                "voltage_droop_active": True,
            },
        }

    def _generate_load_shedding_commands(self, system_state: Dict, current_time: float) -> Dict:
        """Generate load shedding commands for severe disturbances"""
        self.load_shedding_active = True
        self.response_metrics["load_shedding_events"] += 1

        # Determine load shedding percentage based on disturbance severity
        load_shed_percentage = 0.0

        for disturbance in self.active_disturbances:
            if not disturbance.resolved:
                if disturbance.disturbance_type in [
                    DisturbanceType.FREQUENCY_HIGH,
                    DisturbanceType.FREQUENCY_LOW,
                ]:
                    if disturbance.magnitude > self.limits.frequency_critical:
                        load_shed_percentage = max(load_shed_percentage, min(75.0, disturbance.magnitude * 100))

                elif disturbance.disturbance_type in [
                    DisturbanceType.VOLTAGE_HIGH,
                    DisturbanceType.VOLTAGE_LOW,
                ]:
                    if disturbance.magnitude > self.limits.voltage_critical:
                        load_shed_percentage = max(load_shed_percentage, min(50.0, disturbance.magnitude / 10))

        return {
            "grid_disturbance_active": True,
            "response_mode": "load_shedding",
            "load_shedding_active": True,
            "load_shed_percentage": load_shed_percentage,
            "control_commands": {
                "power_limit": (100.0 - load_shed_percentage) / 100.0,
                "response_time": self.limits.fast_response_time,
                "emergency_mode": True,
            },
        }

    def _generate_disconnect_commands(self, system_state: Dict, current_time: float) -> Dict:
        """Generate grid disconnect commands for emergency conditions"""
        self.response_metrics["disconnection_events"] += 1

        return {
            "grid_disturbance_active": True,
            "response_mode": "disconnect",
            "grid_disconnect_required": True,
            "emergency_disconnect": True,
            "control_commands": {
                "immediate_shutdown": True,
                "grid_isolation": True,
                "protection_trip": True,
            },
        }

    def _update_disturbance_resolution(self, current_time: float):
        """Update disturbance resolution status"""
        for disturbance in self.active_disturbances:
            if disturbance.resolved:
                continue

            # Check if disturbance conditions have cleared
            if self._is_disturbance_resolved(disturbance):
                disturbance.resolved = True
                disturbance.end_time = current_time
                disturbance.duration = current_time - disturbance.start_time
                logger.info(
                    f"Grid disturbance resolved: {disturbance.disturbance_type.value} after {disturbance.duration:.1f}s"
                )

        # Remove resolved disturbances from active list
        self.active_disturbances = [d for d in self.active_disturbances if not d.resolved]

        # Reset response modes if no active disturbances
        if not self.active_disturbances:
            self.frequency_support_active = False
            self.voltage_support_active = False
            self.load_shedding_active = False
            self.ride_through_active = False
            self.current_response_mode = ResponseMode.RIDE_THROUGH

    def _is_disturbance_resolved(self, disturbance: DisturbanceEvent) -> bool:
        """Check if a disturbance has been resolved"""

        if disturbance.disturbance_type == DisturbanceType.FREQUENCY_HIGH:
            return self.grid_frequency <= self.limits.nominal_frequency + self.limits.frequency_deadband

        elif disturbance.disturbance_type == DisturbanceType.FREQUENCY_LOW:
            return self.grid_frequency >= self.limits.nominal_frequency - self.limits.frequency_deadband

        elif disturbance.disturbance_type == DisturbanceType.VOLTAGE_HIGH:
            return self.grid_voltage <= self.limits.nominal_voltage + self.limits.voltage_deadband

        elif disturbance.disturbance_type == DisturbanceType.VOLTAGE_LOW:
            return self.grid_voltage >= self.limits.nominal_voltage - self.limits.voltage_deadband

        elif disturbance.disturbance_type == DisturbanceType.GRID_OUTAGE:
            return self.grid_connected

        return False

    def _update_response_metrics(self):
        """Update response performance metrics"""
        if self.active_disturbances:
            # Calculate average response time for resolved disturbances
            resolved_disturbances = [d for d in self.disturbance_history if d.resolved and d.response_time > 0]
            if resolved_disturbances:
                avg_response = sum(d.response_time for d in resolved_disturbances) / len(resolved_disturbances)
                self.response_metrics["average_response_time"] = avg_response

    def get_disturbance_status(self) -> Dict:
        """Get current grid disturbance status"""
        return {
            "grid_connected": self.grid_connected,
            "grid_frequency": self.grid_frequency,
            "grid_voltage": self.grid_voltage,
            "active_disturbances": len(self.active_disturbances),
            "current_response_mode": self.current_response_mode.value,
            "frequency_support_active": self.frequency_support_active,
            "voltage_support_active": self.voltage_support_active,
            "load_shedding_active": self.load_shedding_active,
            "ride_through_active": self.ride_through_active,
            "disturbance_history_count": len(self.disturbance_history),
            "response_metrics": self.response_metrics,
        }

    def reset(self):
        """Reset grid disturbance handler"""
        logger.info("GridDisturbanceHandler reset")
        self.active_disturbances = []
        self.current_response_mode = ResponseMode.RIDE_THROUGH
        self.frequency_support_active = False
        self.voltage_support_active = False
        self.load_shedding_active = False
        self.ride_through_active = False
        self.grid_frequency = self.limits.nominal_frequency
        self.grid_voltage = self.limits.nominal_voltage
        self.grid_connected = True
