"""
Load Forecaster

Provides load forecasting capabilities for demand response and peak shaving
optimization. Implements multiple forecasting methods including statistical,
machine learning, and pattern-based approaches.

Forecast horizon: 1-48 hours
Update frequency: Every 15 minutes
Accuracy target: <5% MAPE
Methods: Historical patterns, regression, seasonal decomposition
"""

import time
import math
import statistics
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
from collections import deque
from datetime import datetime, timedelta
import numpy as np


@dataclass
class LoadForecastConfig:
    """Configuration for Load Forecaster"""
    forecast_horizon_hours: int = 24        # 24-hour forecast horizon
    forecast_update_interval: float = 900.0 # 15 minutes update interval
    historical_data_days: int = 30          # 30 days of historical data
    seasonal_pattern_weeks: int = 4         # 4 weeks for seasonal patterns
    accuracy_target_mape: float = 5.0       # 5% MAPE target
    confidence_threshold: float = 0.8       # Minimum confidence for forecasts
    enable_weather_correction: bool = False # Weather data integration
    enable_seasonal_adjustment: bool = True # Seasonal pattern adjustment
    enable_trend_analysis: bool = True      # Long-term trend analysis
    
    # Forecasting method weights
    pattern_weight: float = 0.4             # Historical pattern weight
    regression_weight: float = 0.3          # Regression model weight
    seasonal_weight: float = 0.3            # Seasonal decomposition weight
    
    def validate(self):
        """Validate configuration parameters"""
        assert 1 <= self.forecast_horizon_hours <= 48, "Forecast horizon must be 1-48 hours"
        assert 300.0 <= self.forecast_update_interval <= 3600.0, "Update interval must be 5-60 minutes"
        assert 7 <= self.historical_data_days <= 365, "Historical data must be 7-365 days"
        total_weight = self.pattern_weight + self.regression_weight + self.seasonal_weight
        assert abs(total_weight - 1.0) < 0.01, "Method weights must sum to 1.0"


class ForecastPoint:
    """Individual forecast point"""
    def __init__(self, timestamp: float, predicted_load: float, confidence: float, method: str):
        self.timestamp = timestamp
        self.predicted_load = predicted_load
        self.confidence = confidence
        self.method = method
        self.actual_load: Optional[float] = None
        self.error: Optional[float] = None
        
    def update_actual(self, actual_load: float):
        """Update with actual load for accuracy calculation"""
        self.actual_load = actual_load
        if self.predicted_load > 0:
            self.error = abs(actual_load - self.predicted_load) / self.predicted_load * 100.0


class LoadForecaster:
    """
    Load Forecaster for demand prediction and planning.
    
    Implements multiple forecasting methods:
    - Historical pattern matching
    - Linear regression with time features
    - Seasonal decomposition
    - Weather-adjusted forecasting (optional)
    """
    
    def __init__(self, config: Optional[LoadForecastConfig] = None):
        self.config = config or LoadForecastConfig()
        self.config.validate()
        
        # Historical data storage
        self.load_history = deque(maxlen=self.config.historical_data_days * 1440)  # 1-minute data
        self.hourly_data = deque(maxlen=self.config.historical_data_days * 24)    # Hourly averages
        self.daily_data = deque(maxlen=self.config.historical_data_days)          # Daily patterns
        
        # Forecast storage
        self.current_forecast: List[ForecastPoint] = []
        self.forecast_accuracy_history = deque(maxlen=1000)
        self.last_forecast_time = 0.0
        
        # Pattern analysis
        self.weekday_patterns = {}     # Average patterns by weekday
        self.hourly_patterns = {}      # Average patterns by hour
        self.seasonal_patterns = {}    # Seasonal adjustment factors
        self.trend_coefficient = 0.0   # Long-term trend slope
        
        # Performance metrics
        self.total_forecasts = 0
        self.accurate_forecasts = 0  # Within target MAPE
        self.current_mape = 0.0
        self.forecast_bias = 0.0     # Average forecast error
        
        # Model parameters
        self.regression_coefficients = {}
        self.seasonal_factors = {}
        self.pattern_weights = {}
        
        self.last_update_time = time.time()
        
    def update(self, current_load: float, dt: float, 
               weather_data: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
        """
        Update load forecaster with current load data.
        
        Args:
            current_load: Current load measurement (MW)
            dt: Time step (seconds)
            weather_data: Optional weather data for correlation
            
        Returns:
            Dictionary containing forecast data and status
        """
        current_time = time.time()
        
        # Store load data
        self._store_load_data(current_load, current_time)
        
        # Update accuracy of previous forecasts
        self._update_forecast_accuracy(current_load, current_time)
        
        # Check if forecast update is needed
        if self._should_update_forecast(current_time):
            self._generate_forecast(current_time, weather_data)
        
        # Update patterns and models periodically
        if len(self.load_history) > 1440:  # Have at least 1 day of data
            self._update_patterns()
            self._update_regression_model()
            if self.config.enable_seasonal_adjustment:
                self._update_seasonal_factors()
        
        self.last_update_time = current_time
        
        return self._create_response_dict()
    
    def get_forecast(self, hours_ahead: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get current forecast for specified hours ahead.
        
        Args:
            hours_ahead: Number of hours ahead (default: all available)
            
        Returns:
            List of forecast points
        """
        if hours_ahead is None:
            hours_ahead = self.config.forecast_horizon_hours
        
        current_time = time.time()
        forecast_points = []
        
        for point in self.current_forecast:
            hours_from_now = (point.timestamp - current_time) / 3600.0
            if 0 <= hours_from_now <= hours_ahead:
                forecast_points.append({
                    'timestamp': point.timestamp,
                    'hours_ahead': hours_from_now,
                    'predicted_load': point.predicted_load,
                    'confidence': point.confidence,
                    'method': point.method
                })
        
        return forecast_points
    
    def _store_load_data(self, load: float, timestamp: float):
        """Store load data in historical buffers"""
        
        # Store minute-level data
        self.load_history.append({
            'load': load,
            'timestamp': timestamp,
            'hour': datetime.fromtimestamp(timestamp).hour,
            'weekday': datetime.fromtimestamp(timestamp).weekday(),
            'day_of_year': datetime.fromtimestamp(timestamp).timetuple().tm_yday
        })
        
        # Update hourly averages
        if len(self.load_history) >= 60:  # Have enough data for hourly average
            recent_hour = list(self.load_history)[-60:]
            hourly_avg = sum(entry['load'] for entry in recent_hour) / len(recent_hour)
            
            # Check if we need to add new hourly point
            if (len(self.hourly_data) == 0 or 
                (timestamp - self.hourly_data[-1]['timestamp']) >= 3600):
                
                self.hourly_data.append({
                    'load': hourly_avg,
                    'timestamp': timestamp,
                    'hour': datetime.fromtimestamp(timestamp).hour,
                    'weekday': datetime.fromtimestamp(timestamp).weekday()
                })
        
        # Update daily patterns
        if len(self.hourly_data) >= 24:  # Have enough data for daily pattern
            recent_day = list(self.hourly_data)[-24:]
            daily_avg = sum(entry['load'] for entry in recent_day) / len(recent_day)
            
            # Check if we need to add new daily point
            if (len(self.daily_data) == 0 or 
                (timestamp - self.daily_data[-1]['timestamp']) >= 86400):
                
                self.daily_data.append({
                    'load': daily_avg,
                    'timestamp': timestamp,
                    'weekday': datetime.fromtimestamp(timestamp).weekday(),
                    'pattern': [entry['load'] for entry in recent_day]
                })
    
    def _should_update_forecast(self, current_time: float) -> bool:
        """Check if forecast should be updated"""
        
        if not self.current_forecast:  # No forecast exists
            return True
        
        # Check update interval
        if (current_time - self.last_forecast_time) >= self.config.forecast_update_interval:
            return True
        
        # Check if forecast is getting stale
        oldest_forecast_time = min(point.timestamp for point in self.current_forecast)
        if oldest_forecast_time < current_time:  # Past forecasts exist
            return True
        
        return False
    
    def _generate_forecast(self, current_time: float, weather_data: Optional[Dict[str, float]] = None):
        """Generate new load forecast"""
        
        if len(self.hourly_data) < 24:  # Need at least 24 hours of data
            return
        
        self.current_forecast.clear()
        
        for hour_offset in range(self.config.forecast_horizon_hours):
            forecast_time = current_time + (hour_offset * 3600)
            
            # Generate forecast using multiple methods
            pattern_forecast = self._pattern_based_forecast(forecast_time)
            regression_forecast = self._regression_forecast(forecast_time)
            seasonal_forecast = self._seasonal_forecast(forecast_time)
            
            # Combine forecasts using weights
            combined_forecast = (
                pattern_forecast * self.config.pattern_weight +
                regression_forecast * self.config.regression_weight +
                seasonal_forecast * self.config.seasonal_weight
            )
            
            # Calculate confidence based on historical accuracy and data availability
            confidence = self._calculate_forecast_confidence(forecast_time)
            
            # Apply weather adjustment if enabled
            if self.config.enable_weather_correction and weather_data:
                combined_forecast = self._apply_weather_adjustment(combined_forecast, weather_data)
            
            # Create forecast point
            forecast_point = ForecastPoint(
                timestamp=forecast_time,
                predicted_load=combined_forecast,
                confidence=confidence,
                method='combined'
            )
            
            self.current_forecast.append(forecast_point)
        
        self.last_forecast_time = current_time
        self.total_forecasts += 1
    
    def _pattern_based_forecast(self, forecast_time: float) -> float:
        """Generate forecast based on historical patterns"""
        
        forecast_hour = datetime.fromtimestamp(forecast_time).hour
        forecast_weekday = datetime.fromtimestamp(forecast_time).weekday()
        
        # Find similar historical periods
        similar_periods = []
        for entry in self.hourly_data:
            if (entry['hour'] == forecast_hour and 
                entry['weekday'] == forecast_weekday):
                similar_periods.append(entry['load'])
        
        if similar_periods:
            # Use weighted average of recent similar periods
            if len(similar_periods) > 5:
                # Weight recent periods more heavily
                weights = [1.0 + i * 0.1 for i in range(len(similar_periods))]
                weighted_sum = sum(load * weight for load, weight in zip(similar_periods, weights))
                total_weight = sum(weights)
                return weighted_sum / total_weight
            else:
                return statistics.median(similar_periods)
        
        # Fallback to overall hourly average
        hour_loads = [entry['load'] for entry in self.hourly_data if entry['hour'] == forecast_hour]
        return statistics.median(hour_loads) if hour_loads else 0.0
    
    def _regression_forecast(self, forecast_time: float) -> float:
        """Generate forecast using regression model"""
        
        if len(self.hourly_data) < 48:  # Need enough data for regression
            return self._pattern_based_forecast(forecast_time)
        
        # Simple linear regression with time-based features
        forecast_hour = datetime.fromtimestamp(forecast_time).hour
        forecast_weekday = datetime.fromtimestamp(forecast_time).weekday()
        
        # Time-based features
        hour_sin = math.sin(2 * math.pi * forecast_hour / 24)
        hour_cos = math.cos(2 * math.pi * forecast_hour / 24)
        weekday_sin = math.sin(2 * math.pi * forecast_weekday / 7)
        weekday_cos = math.cos(2 * math.pi * forecast_weekday / 7)
        
        # Use stored regression coefficients or calculate basic trend
        if hasattr(self, 'regression_coefficients') and self.regression_coefficients:
            coeffs = self.regression_coefficients
            forecast = (coeffs.get('intercept', 0) +
                       coeffs.get('hour_sin', 0) * hour_sin +
                       coeffs.get('hour_cos', 0) * hour_cos +
                       coeffs.get('weekday_sin', 0) * weekday_sin +
                       coeffs.get('weekday_cos', 0) * weekday_cos +
                       coeffs.get('trend', 0) * (forecast_time / 86400))  # Trend per day
        else:
            # Fallback to pattern-based forecast
            forecast = self._pattern_based_forecast(forecast_time)
        
        return max(0.0, forecast)
    
    def _seasonal_forecast(self, forecast_time: float) -> float:
        """Generate forecast using seasonal decomposition"""
        
        if not self.config.enable_seasonal_adjustment:
            return self._pattern_based_forecast(forecast_time)
        
        # Get base pattern forecast
        base_forecast = self._pattern_based_forecast(forecast_time)
        
        # Apply seasonal adjustment
        day_of_year = datetime.fromtimestamp(forecast_time).timetuple().tm_yday
        seasonal_factor = self.seasonal_factors.get(day_of_year, 1.0)
        
        return base_forecast * seasonal_factor
    
    def _calculate_forecast_confidence(self, forecast_time: float) -> float:
        """Calculate confidence level for forecast"""
        
        hours_ahead = (forecast_time - time.time()) / 3600.0
        
        # Base confidence decreases with time horizon
        base_confidence = max(0.5, 1.0 - (hours_ahead / 48.0))
        
        # Adjust based on historical accuracy
        if self.current_mape > 0:
            accuracy_factor = max(0.5, 1.0 - (self.current_mape / 20.0))  # Scale based on 20% max error
        else:
            accuracy_factor = 0.8  # Default when no history
        
        # Adjust based on data availability
        data_factor = min(1.0, len(self.hourly_data) / (7 * 24))  # Full confidence with 1 week of data
        
        return base_confidence * accuracy_factor * data_factor
    
    def _apply_weather_adjustment(self, base_forecast: float, weather_data: Dict[str, float]) -> float:
        """Apply weather-based adjustments to forecast"""
        
        # Simple temperature-based adjustment
        temperature = weather_data.get('temperature', 20.0)  # Celsius
        
        # Heating/cooling load adjustment
        if temperature < 18.0:  # Heating load
            temp_factor = 1.0 + (18.0 - temperature) * 0.02  # 2% per degree below 18°C
        elif temperature > 24.0:  # Cooling load
            temp_factor = 1.0 + (temperature - 24.0) * 0.03  # 3% per degree above 24°C
        else:
            temp_factor = 1.0
        
        return base_forecast * temp_factor
    
    def _update_patterns(self):
        """Update pattern analysis from historical data"""
        
        # Update weekday patterns
        for weekday in range(7):
            weekday_loads = [entry['load'] for entry in self.hourly_data 
                           if entry['weekday'] == weekday]
            if weekday_loads:
                self.weekday_patterns[weekday] = statistics.mean(weekday_loads)
        
        # Update hourly patterns
        for hour in range(24):
            hour_loads = [entry['load'] for entry in self.hourly_data 
                         if entry['hour'] == hour]
            if hour_loads:
                self.hourly_patterns[hour] = statistics.mean(hour_loads)
    
    def _update_regression_model(self):
        """Update regression model coefficients"""
        
        if len(self.hourly_data) < 48:
            return
        
        # Simple trend calculation
        recent_data = list(self.hourly_data)[-168:]  # Last week
        if len(recent_data) >= 24:
            loads = [entry['load'] for entry in recent_data]
            times = [i for i in range(len(loads))]
            
            # Simple linear trend
            n = len(loads)
            sum_t = sum(times)
            sum_load = sum(loads)
            sum_t_load = sum(t * load for t, load in zip(times, loads))
            sum_t2 = sum(t * t for t in times)
            
            if n * sum_t2 - sum_t * sum_t != 0:
                slope = (n * sum_t_load - sum_t * sum_load) / (n * sum_t2 - sum_t * sum_t)
                intercept = (sum_load - slope * sum_t) / n
                
                self.regression_coefficients = {
                    'intercept': intercept,
                    'trend': slope,
                    'hour_sin': 0.0,  # Could be calculated with more sophisticated regression
                    'hour_cos': 0.0,
                    'weekday_sin': 0.0,
                    'weekday_cos': 0.0
                }
                
                self.trend_coefficient = slope
    
    def _update_seasonal_factors(self):
        """Update seasonal adjustment factors"""
        
        if len(self.daily_data) < 14:  # Need at least 2 weeks
            return
        
        # Calculate seasonal factors by day of year
        daily_averages = {}
        for entry in self.daily_data:
            day_of_year = datetime.fromtimestamp(entry['timestamp']).timetuple().tm_yday
            if day_of_year not in daily_averages:
                daily_averages[day_of_year] = []
            daily_averages[day_of_year].append(entry['load'])
        
        # Calculate overall average
        all_loads = [entry['load'] for entry in self.daily_data]
        overall_average = statistics.mean(all_loads)
        
        # Calculate seasonal factors
        for day_of_year, loads in daily_averages.items():
            if overall_average > 0:
                self.seasonal_factors[day_of_year] = statistics.mean(loads) / overall_average
    
    def _update_forecast_accuracy(self, current_load: float, current_time: float):
        """Update accuracy metrics for previous forecasts"""
        
        # Find forecasts that correspond to current time
        matching_forecasts = [
            point for point in self.current_forecast 
            if abs(point.timestamp - current_time) < 1800  # Within 30 minutes
        ]
        
        for forecast_point in matching_forecasts:
            if forecast_point.actual_load is None:  # Not yet updated
                forecast_point.update_actual(current_load)
                
                # Store accuracy data
                self.forecast_accuracy_history.append(forecast_point.error)
                
                # Update overall accuracy metrics
                if forecast_point.error is not None and forecast_point.error <= self.config.accuracy_target_mape:
                    self.accurate_forecasts += 1
        
        # Calculate current MAPE
        if len(self.forecast_accuracy_history) > 0:
            self.current_mape = statistics.mean(list(self.forecast_accuracy_history))
            
            # Calculate bias
            errors = [point.actual_load - point.predicted_load 
                     for point in self.current_forecast 
                     if point.actual_load is not None and point.predicted_load > 0]
            if errors:
                self.forecast_bias = statistics.mean(errors)
    
    def _create_response_dict(self) -> Dict[str, Any]:
        """Create standardized response dictionary"""
        
        next_24h_forecast = self.get_forecast(24)
        peak_forecast = max(point['predicted_load'] for point in next_24h_forecast) if next_24h_forecast else 0.0
        
        return {
            'forecast_available': len(self.current_forecast) > 0,
            'forecast_horizon_hours': len(self.current_forecast),
            'next_hour_forecast': next_24h_forecast[0]['predicted_load'] if next_24h_forecast else 0.0,
            'peak_forecast_24h': peak_forecast,
            'forecast_confidence': statistics.mean([p.confidence for p in self.current_forecast]) if self.current_forecast else 0.0,
            'current_mape': self.current_mape,
            'forecast_bias': self.forecast_bias,
            'service_type': 'load_forecasting',
            'timestamp': self.last_update_time
        }
    
    def get_performance_metrics(self) -> Dict[str, float]:
        """Get performance metrics for monitoring and optimization"""
        
        accuracy_rate = (self.accurate_forecasts / max(1, self.total_forecasts)) * 100.0
        
        return {
            'total_forecasts': self.total_forecasts,
            'accurate_forecasts': self.accurate_forecasts,
            'accuracy_rate_percent': accuracy_rate,
            'current_mape': self.current_mape,
            'forecast_bias': self.forecast_bias,
            'data_points_available': len(self.load_history),
            'pattern_completeness': min(100.0, len(self.hourly_data) / (7 * 24) * 100.0),
            'trend_coefficient': self.trend_coefficient,
            'seasonal_factors_count': len(self.seasonal_factors)
        }
    
    def reset(self):
        """Reset forecaster state"""
        self.load_history.clear()
        self.hourly_data.clear()
        self.daily_data.clear()
        self.current_forecast.clear()
        self.forecast_accuracy_history.clear()
        self.weekday_patterns.clear()
        self.hourly_patterns.clear()
        self.seasonal_patterns.clear()
        self.regression_coefficients.clear()
        self.seasonal_factors.clear()
        self.pattern_weights.clear()
        self.total_forecasts = 0
        self.accurate_forecasts = 0
        self.current_mape = 0.0
        self.forecast_bias = 0.0
        self.trend_coefficient = 0.0
        self.last_forecast_time = 0.0
        self.last_update_time = time.time()
    
    def update_configuration(self, new_config: LoadForecastConfig):
        """Update forecaster configuration"""
        new_config.validate()
        self.config = new_config

    def is_forecasting(self) -> bool:
        """Check if forecaster is actively forecasting"""
        return len(self.current_forecast) > 0 and time.time() - self.last_forecast_time < self.config.forecast_update_interval * 2
    
    def get_forecast_accuracy(self) -> float:
        """Get current forecast accuracy (MAPE)"""
        if len(self.forecast_accuracy_history) == 0:
            return 0.0
        return sum(self.forecast_accuracy_history) / len(self.forecast_accuracy_history)


def create_standard_load_forecaster() -> LoadForecaster:
    """Create a standard load forecaster with typical utility settings"""
    config = LoadForecastConfig(
        forecast_horizon_hours=24,           # 24-hour forecast
        forecast_update_interval=900.0,      # 15 minutes update
        historical_data_days=30,             # 30 days historical data
        seasonal_pattern_weeks=4,            # 4 weeks seasonal patterns
        accuracy_target_mape=5.0,            # 5% MAPE target
        confidence_threshold=0.8,            # 80% confidence threshold
        enable_weather_correction=False,     # Weather correction disabled initially
        enable_seasonal_adjustment=True,     # Seasonal adjustment enabled
        enable_trend_analysis=True,          # Trend analysis enabled
        pattern_weight=0.4,                  # 40% pattern weight
        regression_weight=0.3,               # 30% regression weight
        seasonal_weight=0.3                  # 30% seasonal weight
    )
    return LoadForecaster(config)
