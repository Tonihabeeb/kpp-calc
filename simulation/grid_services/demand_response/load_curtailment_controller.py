"""
Load Curtailment Controller

Provides emergency load reduction and economic curtailment services for
grid reliability and economic optimization. Implements utility demand
response programs and automated load shedding capabilities.

Response time: <60 seconds for emergency
Curtailment capacity: 10-50% of connected load
Duration: 1 minute to 6 hours
Recovery time: <5 minutes
Frequency: <10 events per month
"""

import math
import time
from collections import deque
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


class CurtailmentType(Enum):
    """Types of load curtailment"""

    EMERGENCY = "emergency"  # Grid emergency conditions
    ECONOMIC = "economic"  # Economic optimization
    RELIABILITY = "reliability"  # Grid reliability service
    PEAK_SHAVING = "peak_shaving"  # Peak demand reduction
    VOLUNTARY = "voluntary"  # Voluntary participation


class CurtailmentPriority(Enum):
    """Priority levels for curtailment actions"""

    CRITICAL = 1  # Grid stability at risk
    HIGH = 2  # Economic or reliability benefit
    MEDIUM = 3  # Optimization opportunity
    LOW = 4  # Optional curtailment


@dataclass
class LoadCurtailmentConfig:
    """Configuration for Load Curtailment Controller"""

    max_curtailment_percent: float = 0.30  # Maximum 30% load reduction
    min_curtailment_duration: float = 60.0  # Minimum 1 minute duration
    max_curtailment_duration: float = 21600.0  # Maximum 6 hours duration
    recovery_time_s: float = 300.0  # 5 minutes recovery time
    response_time_s: float = 60.0  # 60 seconds response time
    max_events_per_day: int = 3  # Maximum 3 events per day
    max_events_per_month: int = 10  # Maximum 10 events per month
    min_interval_between_events: float = 3600.0  # 1 hour minimum between events
    enable_curtailment: bool = True
    enable_emergency_override: bool = True  # Allow emergency override of limits

    # Economic parameters
    curtailment_payment_rate: float = 50.0  # $/MWh for curtailment
    penalty_rate: float = 100.0  # $/MWh penalty for non-compliance

    def validate(self):
        """Validate configuration parameters"""
        assert 0.05 <= self.max_curtailment_percent <= 0.80, "Curtailment must be 5-80%"
        assert (
            60.0 <= self.min_curtailment_duration <= 300.0
        ), "Min duration must be 1-5 minutes"
        assert (
            300.0 <= self.max_curtailment_duration <= 86400.0
        ), "Max duration must be 5min-24hr"
        assert (
            60.0 <= self.response_time_s <= 300.0
        ), "Response time must be 1-5 minutes"


@dataclass
class CurtailmentEvent:
    """Data structure for curtailment events"""

    event_id: str
    event_type: CurtailmentType
    priority: CurtailmentPriority
    requested_reduction: float  # MW
    duration_requested: float  # seconds
    start_time: float  # timestamp
    end_time: Optional[float] = None
    actual_reduction: float = 0.0  # MW achieved
    compliance_rate: float = 0.0  # 0.0 to 1.0
    revenue: float = 0.0  # $ earned

    @property
    def is_active(self) -> bool:
        return self.end_time is None

    @property
    def duration_actual(self) -> float:
        if self.end_time is None:
            return time.time() - self.start_time
        return self.end_time - self.start_time


class LoadCurtailmentController:
    """
    Load Curtailment Controller for demand response and load management.

    Implements utility-grade load curtailment with:
    - Emergency load shedding for grid stability
    - Economic curtailment for market participation
    - Reliability services for grid support
    - Performance monitoring and compliance tracking
    - Revenue optimization and reporting
    """

    def __init__(self, config: Optional[LoadCurtailmentConfig] = None):
        self.config = config or LoadCurtailmentConfig()
        self.config.validate()

        # State variables
        self.current_load_baseline = 0.0  # Baseline load without curtailment (MW)
        self.current_load_actual = 0.0  # Actual load with curtailment (MW)
        self.curtailment_active = False
        self.curtailment_amount = 0.0  # Current curtailment amount (MW)

        # Event management
        self.active_event: Optional[CurtailmentEvent] = None
        self.event_history = deque(maxlen=1000)  # Store event history
        self.pending_events = []  # Queue of pending events

        # Performance tracking
        self.total_events = 0
        self.total_curtailment_energy = 0.0  # MWh curtailed
        self.total_revenue = 0.0  # $ earned
        self.compliance_violations = 0
        self.last_event_time = 0.0

        # Daily/monthly limits tracking
        self.daily_event_count = 0
        self.monthly_event_count = 0
        self.last_daily_reset = time.time()
        self.last_monthly_reset = time.time()

        # Load monitoring
        self.load_history = deque(maxlen=1440)  # 24 hours at 1-minute intervals
        self.baseline_load = 0.0
        self.load_forecast = []

        self.last_update_time = time.time()

    def update(
        self,
        current_load: float,
        dt: float,
        grid_conditions: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Update load curtailment controller with current load and grid conditions.

        Args:
            current_load: Current actual load (MW)
            dt: Time step (seconds)
            grid_conditions: Optional grid condition data

        Returns:
            Dictionary containing curtailment commands and status
        """
        current_time = time.time()
        grid_conditions = grid_conditions or {}

        if not self.config.enable_curtailment:
            return self._create_response_dict(0.0, "Load curtailment disabled")

        # Update daily/monthly counters
        self._update_event_counters(current_time)

        # Store load data and update baseline
        self._update_load_tracking(current_load, current_time)

        # Process any active event
        if self.active_event:
            self._update_active_event(current_load, current_time, dt)

        # Check for new curtailment requests
        curtailment_command = self._check_for_curtailment_needs(
            current_load, grid_conditions, current_time
        )
        # Calculate actual curtailment achieved
        if self.curtailment_active and self.active_event:
            # Use requested reduction if we don't have a good baseline yet
            if self.baseline_load > 0:
                self.curtailment_amount = max(0.0, self.baseline_load - current_load)
            else:
                # Use requested reduction as the target amount when no baseline established
                self.curtailment_amount = self.active_event.requested_reduction
        else:
            self.curtailment_amount = 0.0

        self.current_load_actual = current_load
        self.last_update_time = current_time

        return self._create_response_dict(curtailment_command, self._get_status())

    def request_curtailment(
        self,
        reduction_mw: float,
        duration_s: float,
        event_type: CurtailmentType = CurtailmentType.ECONOMIC,
        priority: CurtailmentPriority = CurtailmentPriority.MEDIUM,
        event_id: Optional[str] = None,
    ) -> bool:
        """
        Request a load curtailment event.

        Args:
            reduction_mw: Requested load reduction (MW)
            duration_s: Requested duration (seconds)
            event_type: Type of curtailment event
            priority: Priority level
            event_id: Optional unique event identifier

        Returns:
            Boolean indicating if request was accepted
        """
        current_time = time.time()

        # Generate event ID if not provided
        if event_id is None:
            event_id = f"{event_type.value}_{int(current_time)}"

        # Validate request
        if not self._validate_curtailment_request(
            reduction_mw, duration_s, event_type, current_time
        ):
            return False

        # Create curtailment event
        event = CurtailmentEvent(
            event_id=event_id,
            event_type=event_type,
            priority=priority,
            requested_reduction=reduction_mw,
            duration_requested=duration_s,
            start_time=current_time,
        )

        # Check if we can start immediately or need to queue
        if self.active_event is None:
            self._start_curtailment_event(event)
            return True
        else:
            # Queue if higher priority, otherwise reject
            if priority.value < self.active_event.priority.value:
                self._end_current_event(current_time)
                self._start_curtailment_event(event)
                return True
            else:
                return False  # Lower priority, reject

    def _validate_curtailment_request(
        self,
        reduction_mw: float,
        duration_s: float,
        event_type: CurtailmentType,
        current_time: float,
    ) -> bool:
        """Validate if curtailment request can be honored"""

        # Check if curtailment is enabled
        if not self.config.enable_curtailment:
            return False

        # Check emergency override
        if (
            event_type == CurtailmentType.EMERGENCY
            and self.config.enable_emergency_override
        ):
            return True  # Emergency override bypasses most limits

        # Check maximum reduction limit
        max_reduction = self.baseline_load * self.config.max_curtailment_percent
        if reduction_mw > max_reduction:
            return False

        # Check duration limits
        if (
            duration_s < self.config.min_curtailment_duration
            or duration_s > self.config.max_curtailment_duration
        ):
            return False

        # Check daily event limit
        if self.daily_event_count >= self.config.max_events_per_day:
            return False

        # Check monthly event limit
        if self.monthly_event_count >= self.config.max_events_per_month:
            return False

        # Check minimum interval between events
        if (
            current_time - self.last_event_time
        ) < self.config.min_interval_between_events:
            return False

        return True

    def _start_curtailment_event(self, event: CurtailmentEvent):
        """Start a new curtailment event"""
        self.active_event = event
        self.curtailment_active = True
        self.total_events += 1
        self.daily_event_count += 1
        self.monthly_event_count += 1
        self.last_event_time = event.start_time

        # Calculate expected revenue
        energy_mwh = event.requested_reduction * (event.duration_requested / 3600.0)
        event.revenue = energy_mwh * self.config.curtailment_payment_rate

    def _update_active_event(self, current_load: float, current_time: float, dt: float):
        """Update the currently active curtailment event"""
        if not self.active_event:
            return

        # Check if event duration has elapsed
        if (
            current_time - self.active_event.start_time
        ) >= self.active_event.duration_requested:
            self._end_current_event(current_time)
            return

        # Update actual reduction achieved
        actual_reduction = max(0.0, self.baseline_load - current_load)
        self.active_event.actual_reduction = actual_reduction

        # Calculate compliance rate
        if self.active_event.requested_reduction > 0:
            self.active_event.compliance_rate = min(
                1.0, actual_reduction / self.active_event.requested_reduction
            )

        # Track energy curtailed
        energy_curtailed_mwh = actual_reduction * (dt / 3600.0)
        self.total_curtailment_energy += energy_curtailed_mwh

        # Check compliance
        if self.active_event.compliance_rate < 0.8:  # Less than 80% compliance
            self.compliance_violations += 1

    def _end_current_event(self, current_time: float):
        """End the currently active curtailment event"""
        if not self.active_event:
            return

        self.active_event.end_time = current_time
        self.curtailment_active = False

        # Calculate final revenue (may include penalties for non-compliance)
        if self.active_event.compliance_rate < 0.8:
            # Apply penalty for non-compliance
            penalty = self.active_event.revenue * 0.5  # 50% penalty
            self.active_event.revenue -= penalty

        self.total_revenue += self.active_event.revenue
        # Move to history
        self.event_history.append(self.active_event)
        self.active_event = None

    def _check_for_curtailment_needs(
        self, current_load: float, grid_conditions: Dict[str, Any], current_time: float
    ) -> float:
        """Check if curtailment is needed based on grid conditions"""

        # Check for emergency conditions (both direct values and emergency_conditions dict)
        emergency_conditions = grid_conditions.get("emergency_conditions", {})

        # Check direct frequency/voltage or emergency conditions flags
        frequency = grid_conditions.get("frequency", 60.0)
        voltage = grid_conditions.get("voltage", 1.0)

        # Emergency conditions from flags
        freq_emergency = (
            emergency_conditions.get("grid_frequency_low", False)
            or emergency_conditions.get("grid_frequency_high", False)
            or frequency < 59.5
            or frequency > 60.5
        )

        voltage_emergency = emergency_conditions.get(
            "voltage_low", False
        ) or emergency_conditions.get("voltage_high", False)

        system_overload = emergency_conditions.get("system_overload", False)

        # Emergency curtailment
        if freq_emergency or voltage_emergency or system_overload:
            if not self.curtailment_active:
                emergency_reduction = (
                    self.baseline_load * 0.20
                    if self.baseline_load > 0
                    else current_load * 0.20
                )
                self.request_curtailment(
                    emergency_reduction,
                    300.0,  # 5 minutes
                    CurtailmentType.EMERGENCY,
                    CurtailmentPriority.CRITICAL,
                    f"emergency_{int(current_time)}",
                )
            return self.active_event.requested_reduction if self.active_event else 0.0

        # Check for economic curtailment opportunities
        market_price = grid_conditions.get(
            "electricity_price", grid_conditions.get("market_price", 50.0)
        )  # $/MWh
        if market_price > 150.0 and not self.curtailment_active:  # High price
            economic_reduction = (
                self.baseline_load * 0.15
                if self.baseline_load > 0
                else current_load * 0.15
            )
            self.request_curtailment(
                economic_reduction,
                3600.0,  # 1 hour
                CurtailmentType.ECONOMIC,
                CurtailmentPriority.MEDIUM,
                f"economic_{int(current_time)}",
            )
            return self.active_event.requested_reduction if self.active_event else 0.0

        return self.active_event.requested_reduction if self.active_event else 0.0

    def _update_load_tracking(self, current_load: float, current_time: float):
        """Update load tracking and baseline calculation"""

        # Store load data
        self.load_history.append(
            {
                "load": current_load,
                "timestamp": current_time,
                "curtailed": self.curtailment_active,
            }
        )

        # Update baseline load (average of non-curtailed periods)
        non_curtailed_loads = [
            entry["load"] for entry in self.load_history if not entry["curtailed"]
        ]

        if non_curtailed_loads:
            # Use recent non-curtailed load as baseline
            recent_loads = non_curtailed_loads[-60:]  # Last hour of non-curtailed data
            self.baseline_load = sum(recent_loads) / len(recent_loads)
        else:
            self.baseline_load = current_load

    def _update_event_counters(self, current_time: float):
        """Update daily and monthly event counters"""

        # Reset daily counter if new day
        if (current_time - self.last_daily_reset) >= 86400.0:  # 24 hours
            self.daily_event_count = 0
            self.last_daily_reset = current_time

        # Reset monthly counter if new month (approximate)
        if (current_time - self.last_monthly_reset) >= 2592000.0:  # 30 days
            self.monthly_event_count = 0
            self.last_monthly_reset = current_time

    def _get_status(self) -> str:
        """Get current controller status"""
        if not self.config.enable_curtailment:
            return "Load curtailment disabled"

        if self.curtailment_active and self.active_event:
            remaining_time = self.active_event.duration_requested - (
                time.time() - self.active_event.start_time
            )
            return (
                f"Curtailment active - {self.active_event.event_type.value} "
                f"({remaining_time:.0f}s remaining)"
            )

        return "Ready for curtailment requests"

    def _create_response_dict(
        self, curtailment_command: float, status: str
    ) -> Dict[str, Any]:
        """Create standardized response dictionary"""
        return {
            "curtailment_command_mw": curtailment_command,
            "baseline_load": self.baseline_load,
            "actual_load": self.current_load_actual,
            "curtailment_amount": self.curtailment_amount,
            "curtailment_active": self.curtailment_active,
            "active_event_id": (
                self.active_event.event_id if self.active_event else None
            ),
            "active_event_type": (
                self.active_event.event_type.value if self.active_event else None
            ),
            "compliance_rate": (
                self.active_event.compliance_rate if self.active_event else 1.0
            ),
            "status": status,
            "service_type": "load_curtailment",
            "timestamp": self.last_update_time,
        }

    def get_performance_metrics(self) -> Dict[str, float]:
        """Get performance metrics for monitoring and optimization"""

        # Calculate average compliance rate
        if len(self.event_history) > 0:
            avg_compliance = sum(
                event.compliance_rate for event in self.event_history
            ) / len(self.event_history)
            total_revenue = sum(event.revenue for event in self.event_history)
            avg_event_duration = sum(
                event.duration_actual for event in self.event_history
            ) / len(self.event_history)
        else:
            avg_compliance = 1.0
            total_revenue = 0.0
            avg_event_duration = 0.0

        # Calculate curtailment capacity utilization
        if self.baseline_load > 0:
            curtailment_capacity = (
                self.baseline_load * self.config.max_curtailment_percent
            )
            current_utilization = (
                self.curtailment_amount / curtailment_capacity
                if curtailment_capacity > 0
                else 0.0
            )
        else:
            current_utilization = 0.0

        return {
            "total_events": self.total_events,
            "daily_events": self.daily_event_count,
            "monthly_events": self.monthly_event_count,
            "average_compliance_rate": avg_compliance,
            "compliance_violations": self.compliance_violations,
            "total_curtailment_energy_mwh": self.total_curtailment_energy,
            "total_revenue": total_revenue,
            "average_event_duration": avg_event_duration,
            "current_curtailment_utilization": current_utilization,
            "baseline_load": self.baseline_load,
            "current_curtailment": self.curtailment_amount,
            "max_curtailment_capacity": self.baseline_load
            * self.config.max_curtailment_percent,
        }

    def reset(self):
        """Reset controller state"""
        if self.active_event:
            self._end_current_event(time.time())

        self.current_load_baseline = 0.0
        self.current_load_actual = 0.0
        self.curtailment_active = False
        self.curtailment_amount = 0.0
        self.active_event = None
        self.event_history.clear()
        self.pending_events.clear()
        self.load_history.clear()
        self.total_events = 0
        self.total_curtailment_energy = 0.0
        self.total_revenue = 0.0
        self.compliance_violations = 0
        self.daily_event_count = 0
        self.monthly_event_count = 0
        self.baseline_load = 0.0
        self.last_update_time = time.time()
        self.last_daily_reset = time.time()
        self.last_monthly_reset = time.time()

    def update_configuration(self, new_config: LoadCurtailmentConfig):
        """Update controller configuration"""
        new_config.validate()
        self.config = new_config

    def is_curtailing(self) -> bool:
        """Check if controller is actively curtailing load"""
        return self.curtailment_active


def create_standard_load_curtailment_controller() -> LoadCurtailmentController:
    """Create a standard load curtailment controller with typical utility settings"""
    config = LoadCurtailmentConfig(
        max_curtailment_percent=0.30,  # 30% maximum curtailment
        min_curtailment_duration=60.0,  # 1 minute minimum
        max_curtailment_duration=21600.0,  # 6 hours maximum
        recovery_time_s=300.0,  # 5 minutes recovery
        response_time_s=60.0,  # 60 seconds response time
        max_events_per_day=3,  # 3 events per day maximum
        max_events_per_month=10,  # 10 events per month maximum
        min_interval_between_events=3600.0,  # 1 hour minimum interval
        enable_curtailment=True,
        enable_emergency_override=True,
        curtailment_payment_rate=50.0,  # $50/MWh
        penalty_rate=100.0,  # $100/MWh penalty
    )
    return LoadCurtailmentController(config)
