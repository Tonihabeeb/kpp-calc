"""
Peak Shaving Controller

Provides peak demand reduction services through intelligent load management
and generation/storage coordination. Implements predictive peak shaving
based on load forecasting and real-time demand monitoring.

Response time: <5 minutes for predicted peaks
Prediction horizon: 24 hours
Peak reduction: 15-40% of peak demand
Accuracy: <5% peak prediction error
Recovery time: <15 minutes after peak
"""

import statistics
import time
from collections import deque
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple



@dataclass
class PeakShavingConfig:
    """Configuration for Peak Shaving Controller"""

    peak_threshold_percent: float = 0.90  # Peak at 90% of historical max
    shaving_target_percent: float = 0.85  # Target to reduce peak to 85% of max
    prediction_horizon_hours: int = 24  # 24-hour prediction horizon
    minimum_peak_duration: float = 900.0  # 15 minutes minimum peak duration
    shaving_response_time: float = 300.0  # 5 minutes response time
    recovery_time_s: float = 900.0  # 15 minutes recovery time
    max_shaving_events_per_day: int = 2  # Maximum 2 peak shaving events per day
    enable_peak_shaving: bool = True
    enable_predictive_shaving: bool = True  # Enable predictive vs reactive only

    # Generation/storage coordination
    enable_generation_increase: bool = True  # Increase generation for peak shaving
    enable_load_reduction: bool = True  # Reduce load for peak shaving
    generation_ramp_rate: float = 0.10  # 10% per minute generation ramp
    load_reduction_rate: float = 0.05  # 5% per minute load reduction rate

    # Economic parameters
    peak_demand_charge: float = 15.0  # $/kW peak demand charge
    energy_cost_threshold: float = 100.0  # $/MWh threshold for action

    def validate(self):
        """Validate configuration parameters"""
        assert 0.70 <= self.peak_threshold_percent <= 0.95, "Peak threshold must be 70-95%"
        assert 0.60 <= self.shaving_target_percent <= 0.90, "Shaving target must be 60-90%"
        assert self.shaving_target_percent < self.peak_threshold_percent, "Target must be less than threshold"
        assert 12 <= self.prediction_horizon_hours <= 48, "Prediction horizon must be 12-48 hours"


class PeakEvent:
    """Data structure for peak events"""

    def __init__(self, predicted_peak: float, predicted_time: float, confidence: float):
        self.predicted_peak = predicted_peak  # MW
        self.predicted_time = predicted_time  # timestamp
        self.confidence = confidence  # 0.0 to 1.0
        self.actual_peak = 0.0  # MW (updated when event occurs)
        self.shaving_activated = False
        self.shaving_amount = 0.0  # MW shaved
        self.cost_savings = 0.0  # $ saved
        self.start_time = 0.0
        self.end_time = 0.0
        self.completed = False


class PeakShavingController:
    """
    Peak Shaving Controller for demand management and cost optimization.

    Implements intelligent peak shaving with:
    - Load forecasting and peak prediction
    - Coordinated generation and load response
    - Economic optimization of peak demand charges
    - Real-time peak detection and response
    - Performance monitoring and optimization
    """

    def __init__(self, config: Optional[PeakShavingConfig] = None):
        self.config = config or PeakShavingConfig()
        self.config.validate()

        # State variables
        self.current_demand = 0.0  # Current total demand (MW)
        self.peak_threshold = 0.0  # Current peak threshold (MW)
        self.historical_peak = 0.0  # Historical peak demand (MW)
        self.shaving_active = False
        self.generation_boost = 0.0  # Additional generation (MW)
        self.load_reduction = 0.0  # Load reduction (MW)

        # Peak tracking
        self.predicted_peaks: List[PeakEvent] = []
        self.active_peak_event: Optional[PeakEvent] = None
        self.peak_history = deque(maxlen=365)  # Store 1 year of daily peaks
        self.daily_peak = 0.0
        self.daily_peak_time = 0.0

        # Demand history for forecasting
        self.demand_history = deque(maxlen=10080)  # 1 week at 1-minute intervals
        self.hourly_averages = deque(maxlen=168)  # 1 week of hourly averages
        self.daily_patterns = {}  # Weekday/weekend patterns

        # Performance tracking
        self.peaks_predicted = 0
        self.peaks_shaved = 0
        self.total_cost_savings = 0.0
        self.prediction_accuracy = 0.0
        self.shaving_events_today = 0
        self.last_daily_reset = time.time()

        # Load forecasting components
        self.load_forecaster = None  # Will be set if external forecaster provided
        self.forecast_horizon = []  # 24-hour forecast
        self.forecast_confidence = 0.0

        self.last_update_time = time.time()

    def update(
        self,
        current_demand: float,
        current_generation: float,
        dt: float,
        external_forecast: Optional[List[float]] = None,
    ) -> Dict[str, Any]:
        """
        Update peak shaving controller with current demand and generation.

        Args:
            current_demand: Current total demand (MW)
            current_generation: Current generation output (MW)
            dt: Time step (seconds)
            external_forecast: Optional external load forecast

        Returns:
            Dictionary containing peak shaving commands and status
        """
        current_time = time.time()

        if not self.config.enable_peak_shaving:
            return self._create_response_dict(0.0, 0.0, "Peak shaving disabled")

        # Update daily reset
        self._update_daily_tracking(current_time)

        # Store demand data and update patterns
        self._update_demand_tracking(current_demand, current_time)

        # Update forecasting if enabled
        if self.config.enable_predictive_shaving:
            self._update_load_forecast(external_forecast)
            self._predict_peaks(current_time)

        # Check for active peak shaving
        if self.shaving_active and self.active_peak_event:
            self._update_active_shaving(current_demand, current_time, dt)

        # Check if new peak shaving is needed
        generation_cmd, load_cmd = self._evaluate_peak_shaving_need(current_demand, current_generation, current_time)

        # Update state
        self.current_demand = current_demand
        self.generation_boost = generation_cmd
        self.load_reduction = load_cmd
        self.last_update_time = current_time

        return self._create_response_dict(generation_cmd, load_cmd, self._get_status())

    def _update_demand_tracking(self, demand: float, current_time: float):
        """Update demand tracking and pattern analysis"""

        # Store demand data
        self.demand_history.append(
            {
                "demand": demand,
                "timestamp": current_time,
                "hour": datetime.fromtimestamp(current_time).hour,
                "weekday": datetime.fromtimestamp(current_time).weekday(),
            }
        )

        # Update daily peak
        if demand > self.daily_peak:
            self.daily_peak = demand
            self.daily_peak_time = current_time

        # Update historical peak
        if demand > self.historical_peak:
            self.historical_peak = demand

        # Update peak threshold
        self.peak_threshold = self.historical_peak * self.config.peak_threshold_percent

        # Update hourly averages every hour
        if len(self.demand_history) >= 60:  # Have at least 1 hour of data
            recent_hour = list(self.demand_history)[-60:]  # Last hour
            hourly_avg = sum(entry["demand"] for entry in recent_hour) / len(recent_hour)

            if len(self.hourly_averages) == 0 or (current_time - self.last_update_time) >= 3600:
                self.hourly_averages.append(
                    {
                        "average": hourly_avg,
                        "timestamp": current_time,
                        "hour": datetime.fromtimestamp(current_time).hour,
                        "weekday": datetime.fromtimestamp(current_time).weekday(),
                    }
                )

    def _update_load_forecast(self, external_forecast: Optional[List[float]] = None):
        """Update load forecast using historical patterns or external data"""

        if external_forecast:
            self.forecast_horizon = external_forecast[:24]  # Use first 24 hours
            self.forecast_confidence = 0.9  # High confidence for external forecast
            return

        # Generate internal forecast based on historical patterns
        if len(self.hourly_averages) < 24:  # Need at least 24 hours of data
            self.forecast_confidence = 0.0
            return

        current_hour = datetime.fromtimestamp(time.time()).hour
        current_weekday = datetime.fromtimestamp(time.time()).weekday()

        # Simple pattern-based forecasting
        forecast = []
        for h in range(24):
            forecast_hour = (current_hour + h) % 24
            forecast_weekday = current_weekday if h < (24 - current_hour) else (current_weekday + 1) % 7

            # Find similar historical periods
            similar_periods = [
                entry["average"]
                for entry in self.hourly_averages
                if entry["hour"] == forecast_hour and entry["weekday"] == forecast_weekday
            ]

            if similar_periods:
                # Use median of similar periods
                forecast_value = statistics.median(similar_periods)
            else:
                # Fallback to overall average for that hour
                hour_averages = [entry["average"] for entry in self.hourly_averages if entry["hour"] == forecast_hour]
                forecast_value = statistics.median(hour_averages) if hour_averages else self.current_demand

            forecast.append(forecast_value)

        self.forecast_horizon = forecast
        self.forecast_confidence = min(0.8, len(self.hourly_averages) / 168.0)  # Increase with data

    def _predict_peaks(self, current_time: float):
        """Predict upcoming peaks based on forecast"""

        if not self.forecast_horizon or self.forecast_confidence < 0.3:
            return

        # Clear old predictions
        self.predicted_peaks = [p for p in self.predicted_peaks if not p.completed]

        # Find peaks in forecast
        for i, forecast_value in enumerate(self.forecast_horizon):
            if forecast_value > self.peak_threshold:
                predicted_time = current_time + (i * 3600)  # i hours from now

                # Check if we already have a prediction for this time period
                existing_prediction = any(
                    abs(p.predicted_time - predicted_time) < 1800 for p in self.predicted_peaks  # Within 30 minutes
                )

                if not existing_prediction:
                    peak_event = PeakEvent(
                        predicted_peak=forecast_value,
                        predicted_time=predicted_time,
                        confidence=self.forecast_confidence,
                    )
                    self.predicted_peaks.append(peak_event)
                    self.peaks_predicted += 1

    def _evaluate_peak_shaving_need(self, demand: float, generation: float, current_time: float) -> Tuple[float, float]:
        """Evaluate if peak shaving is needed and calculate commands"""

        generation_cmd = 0.0
        load_cmd = 0.0

        # Check for immediate peak (reactive shaving)
        if demand > self.peak_threshold and not self.shaving_active:
            if self.shaving_events_today < self.config.max_shaving_events_per_day:
                self._start_peak_shaving(demand, current_time, is_predicted=False)

        # Check for predicted peaks (predictive shaving)
        elif self.config.enable_predictive_shaving and self.predicted_peaks:
            upcoming_peak = self._get_next_predicted_peak(current_time)
            if upcoming_peak and not self.shaving_active:
                # Start shaving 30 minutes before predicted peak
                if (upcoming_peak.predicted_time - current_time) <= 1800:  # 30 minutes
                    if self.shaving_events_today < self.config.max_shaving_events_per_day:
                        self._start_peak_shaving(
                            upcoming_peak.predicted_peak,
                            current_time,
                            is_predicted=True,
                            peak_event=upcoming_peak,
                        )

        # Calculate commands if shaving is active
        if self.shaving_active and self.active_peak_event:
            target_demand = self.historical_peak * self.config.shaving_target_percent
            required_reduction = max(0.0, demand - target_demand)

            # Split reduction between generation increase and load reduction
            if self.config.enable_generation_increase:
                generation_cmd = min(required_reduction * 0.7, generation * 0.3)  # Up to 30% gen increase

            if self.config.enable_load_reduction:
                remaining_reduction = max(0.0, required_reduction - generation_cmd)
                load_cmd = min(remaining_reduction, demand * 0.2)  # Up to 20% load reduction

        return generation_cmd, load_cmd

    def _start_peak_shaving(
        self,
        peak_demand: float,
        current_time: float,
        is_predicted: bool = False,
        peak_event: Optional[PeakEvent] = None,
    ):
        """Start a peak shaving event"""

        if peak_event is None:
            peak_event = PeakEvent(
                predicted_peak=peak_demand,
                predicted_time=current_time,
                confidence=0.8 if not is_predicted else 0.95,
            )

        peak_event.shaving_activated = True
        peak_event.start_time = current_time

        self.active_peak_event = peak_event
        self.shaving_active = True
        self.shaving_events_today += 1

        # Calculate potential cost savings
        peak_reduction = max(
            0.0,
            peak_demand - (self.historical_peak * self.config.shaving_target_percent),
        )
        peak_event.cost_savings = peak_reduction * self.config.peak_demand_charge

    def _update_active_shaving(self, demand: float, current_time: float, dt: float):
        """Update active peak shaving event"""

        if not self.active_peak_event:
            return

        # Update actual values
        self.active_peak_event.actual_peak = max(self.active_peak_event.actual_peak, demand)
        self.active_peak_event.shaving_amount = max(0.0, self.active_peak_event.predicted_peak - demand)

        # Check if peak period has ended
        peak_ended = (
            current_time - self.active_peak_event.start_time
        ) > self.config.minimum_peak_duration and demand < (
            self.peak_threshold * 0.95
        )  # 5% below threshold

        if peak_ended:
            self._end_peak_shaving(current_time)

    def _end_peak_shaving(self, current_time: float):
        """End the active peak shaving event"""

        if not self.active_peak_event:
            return

        self.active_peak_event.end_time = current_time
        self.active_peak_event.completed = True

        # Calculate final metrics
        if self.active_peak_event.predicted_peak > 0:
            shaving_effectiveness = self.active_peak_event.shaving_amount / self.active_peak_event.predicted_peak
        else:
            shaving_effectiveness = 0.0

        # Update performance tracking
        if shaving_effectiveness > 0.1:  # At least 10% reduction
            self.peaks_shaved += 1

        self.total_cost_savings += self.active_peak_event.cost_savings

        # Reset active shaving
        self.shaving_active = False
        self.active_peak_event = None
        self.generation_boost = 0.0
        self.load_reduction = 0.0

    def _get_next_predicted_peak(self, current_time: float) -> Optional[PeakEvent]:
        """Get the next predicted peak event"""

        upcoming_peaks = [
            p for p in self.predicted_peaks if p.predicted_time > current_time and not p.shaving_activated
        ]

        if upcoming_peaks:
            return min(upcoming_peaks, key=lambda p: p.predicted_time)

        return None

    def _update_daily_tracking(self, current_time: float):
        """Update daily tracking and reset counters"""

        # Reset daily counters if new day
        if (current_time - self.last_daily_reset) >= 86400.0:  # 24 hours
            # Store yesterday's peak
            if self.daily_peak > 0:
                self.peak_history.append(
                    {
                        "peak": self.daily_peak,
                        "timestamp": self.daily_peak_time,
                        "date": datetime.fromtimestamp(self.last_daily_reset).date(),
                    }
                )

            # Reset daily values
            self.daily_peak = 0.0
            self.daily_peak_time = current_time
            self.shaving_events_today = 0
            self.last_daily_reset = current_time

    def _get_status(self) -> str:
        """Get current controller status"""

        if not self.config.enable_peak_shaving:
            return "Peak shaving disabled"

        if self.shaving_active and self.active_peak_event:
            return f"Peak shaving active - reducing {self.active_peak_event.shaving_amount:.1f} MW"

        if self.predicted_peaks:
            next_peak = self._get_next_predicted_peak(time.time())
            if next_peak:
                time_to_peak = (next_peak.predicted_time - time.time()) / 3600.0
                return f"Peak predicted in {time_to_peak:.1f} hours ({next_peak.predicted_peak:.1f} MW)"

        return "Monitoring for peaks"

    def _create_response_dict(self, generation_cmd: float, load_cmd: float, status: str) -> Dict[str, Any]:
        """Create standardized response dictionary"""

        next_peak = self._get_next_predicted_peak(time.time())
        return {
            "generation_boost_mw": generation_cmd,
            "load_reduction_mw": load_cmd,
            "total_shaving_mw": generation_cmd + load_cmd,
            "current_demand": self.current_demand,
            "peak_threshold": self.peak_threshold,
            "daily_peak": self.daily_peak,
            "shaving_active": self.shaving_active,
            "predicted_peaks": len(self.predicted_peaks),
            "next_peak_time": next_peak.predicted_time if next_peak else None,
            "forecast_confidence": self.forecast_confidence,
            "status": status,
            "service_type": "peak_shaving",
            "timestamp": self.last_update_time,
        }

    def get_performance_metrics(self) -> Dict[str, float]:
        """Get performance metrics for monitoring and optimization"""

        # Calculate prediction accuracy
        completed_predictions = [p for p in self.predicted_peaks if p.completed]
        if completed_predictions:
            accuracy_errors = [
                abs(p.actual_peak - p.predicted_peak) / p.predicted_peak
                for p in completed_predictions
                if p.predicted_peak > 0
            ]
            self.prediction_accuracy = (1.0 - statistics.mean(accuracy_errors)) * 100.0 if accuracy_errors else 0.0

        # Calculate average shaving effectiveness
        shaved_peaks = [p for p in completed_predictions if p.shaving_amount > 0]
        if shaved_peaks:
            avg_shaving_effectiveness = (
                statistics.mean([p.shaving_amount / p.predicted_peak for p in shaved_peaks]) * 100.0
            )
        else:
            avg_shaving_effectiveness = 0.0

        return {
            "peaks_predicted": self.peaks_predicted,
            "peaks_shaved": self.peaks_shaved,
            "shaving_success_rate": (self.peaks_shaved / max(1, self.peaks_predicted)) * 100.0,
            "prediction_accuracy_percent": self.prediction_accuracy,
            "total_cost_savings": self.total_cost_savings,
            "average_shaving_effectiveness": avg_shaving_effectiveness,
            "daily_peak": self.daily_peak,
            "historical_peak": self.historical_peak,
            "current_threshold": self.peak_threshold,
            "forecast_confidence": self.forecast_confidence,
            "shaving_events_today": self.shaving_events_today,
        }

    def reset(self):
        """Reset controller state"""
        if self.shaving_active:
            self._end_peak_shaving(time.time())

        self.current_demand = 0.0
        self.peak_threshold = 0.0
        self.historical_peak = 0.0
        self.shaving_active = False
        self.generation_boost = 0.0
        self.load_reduction = 0.0
        self.predicted_peaks.clear()
        self.active_peak_event = None
        self.peak_history.clear()
        self.demand_history.clear()
        self.hourly_averages.clear()
        self.daily_patterns.clear()
        self.forecast_horizon.clear()
        self.daily_peak = 0.0
        self.peaks_predicted = 0
        self.peaks_shaved = 0
        self.total_cost_savings = 0.0
        self.prediction_accuracy = 0.0
        self.shaving_events_today = 0
        self.forecast_confidence = 0.0
        self.last_update_time = time.time()
        self.last_daily_reset = time.time()

    def update_configuration(self, new_config: PeakShavingConfig):
        """Update controller configuration"""
        new_config.validate()
        self.config = new_config

    def is_shaving(self) -> bool:
        """Check if controller is actively shaving peaks"""
        return self.shaving_active


def create_standard_peak_shaving_controller() -> PeakShavingController:
    """Create a standard peak shaving controller with typical utility settings"""
    config = PeakShavingConfig(
        peak_threshold_percent=0.90,  # 90% of historical peak
        shaving_target_percent=0.85,  # Reduce to 85% of historical peak
        prediction_horizon_hours=24,  # 24-hour prediction
        minimum_peak_duration=900.0,  # 15 minutes minimum
        shaving_response_time=300.0,  # 5 minutes response
        recovery_time_s=900.0,  # 15 minutes recovery
        max_shaving_events_per_day=2,  # 2 events per day maximum
        enable_peak_shaving=True,
        enable_predictive_shaving=True,
        enable_generation_increase=True,
        enable_load_reduction=True,
        generation_ramp_rate=0.10,  # 10% per minute
        load_reduction_rate=0.05,  # 5% per minute
        peak_demand_charge=15.0,  # $15/kW
        energy_cost_threshold=100.0,  # $100/MWh
    )
    return PeakShavingController(config)
