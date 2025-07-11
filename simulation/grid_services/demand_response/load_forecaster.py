import time
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
import numpy as np
from collections import deque

@dataclass
class LoadForecastConfig:
    """Configuration for load forecasting"""
    forecast_horizon: int = 24  # Hours to forecast ahead
    update_interval: float = 900.0  # Seconds between updates (15 min)
    history_length: int = 168  # Hours of history to maintain (1 week)
    confidence_level: float = 0.95  # Confidence level for predictions
    min_samples: int = 96  # Minimum samples before forecasting (24h at 15min)

@dataclass
class LoadForecastState:
    """State for load forecasting system"""
    last_update: float = 0.0
    load_history: deque = field(default_factory=lambda: deque(maxlen=672))  # 1 week at 15min
    forecast_values: List[float] = field(default_factory=list)
    forecast_confidence: List[tuple] = field(default_factory=list)
    forecast_timestamp: float = 0.0
    metrics: Dict[str, float] = field(default_factory=lambda: {
        'mape': 0.0,  # Mean Absolute Percentage Error
        'rmse': 0.0,  # Root Mean Square Error
        'forecast_accuracy': 0.0,  # % within confidence interval
        'last_update_duration': 0.0  # Seconds
    })

class LoadForecaster:
    """
    Load forecasting system using time series analysis and pattern recognition
    for demand response applications.
    """
    
    def __init__(self, config: Optional[LoadForecastConfig] = None):
        """Initialize load forecaster"""
        self.config = config or LoadForecastConfig()
        self.state = LoadForecastState()
    
    def update(self, load_data: Dict[str, Any], time_step: float) -> Dict[str, Any]:
        """
        Update load forecasting model with new data
        
        Args:
            load_data: Current load measurements and metadata
            time_step: Time step since last update in seconds
            
        Returns:
            Dictionary containing forecast values and confidence intervals
        """
        try:
            # Add new data point to history
            self._update_history(load_data)
            
            current_time = time.time()
            if (current_time - self.state.last_update >= self.config.update_interval and
                len(self.state.load_history) >= self.config.min_samples):
                # Generate new forecast
                self._generate_forecast()
                self._update_metrics()
                self.state.last_update = current_time
            
            return self.get_forecast()
            
        except Exception as e:
            # On error, return last valid forecast
            return self.get_forecast()
    
    def _update_history(self, load_data: Dict[str, Any]) -> None:
        """Update load history with new measurement"""
        load = load_data.get('active_power', 0.0)
        self.state.load_history.append({
            'timestamp': time.time(),
            'load': load,
            'temperature': load_data.get('temperature', 20.0),
            'day_type': load_data.get('day_type', 'weekday')
        })
    
    def _generate_forecast(self) -> None:
        """Generate load forecast using time series analysis"""
        try:
            # Convert history to numpy arrays
            history = list(self.state.load_history)
            times = np.array([d['timestamp'] for d in history])
            loads = np.array([d['load'] for d in history])
            temps = np.array([d['temperature'] for d in history])
            
            # Calculate basic statistics
            mean_load = np.mean(loads)
            std_load = np.std(loads)
            
            # Find daily and weekly patterns
            samples_per_day = 96  # 15min intervals
            daily_pattern = self._calculate_pattern(loads, samples_per_day)
            weekly_pattern = self._calculate_pattern(loads, samples_per_day * 7)
            
            # Generate forecast points
            forecast_points = int(self.config.forecast_horizon * 4)  # 15min intervals
            forecast = []
            confidence = []
            
            for i in range(forecast_points):
                # Combine patterns for prediction
                time_of_day = i % samples_per_day
                day_of_week = (i // samples_per_day) % 7
                
                base_prediction = (
                    0.5 * daily_pattern[time_of_day] +
                    0.3 * weekly_pattern[day_of_week * samples_per_day + time_of_day] +
                    0.2 * mean_load
                )
                
                # Add confidence intervals
                confidence_width = std_load * 1.96  # 95% confidence
                confidence.append((
                    base_prediction - confidence_width,
                    base_prediction + confidence_width
                ))
                forecast.append(base_prediction)
            
            # Update state
            self.state.forecast_values = forecast
            self.state.forecast_confidence = confidence
            self.state.forecast_timestamp = time.time()
            
        except Exception as e:
            # Keep previous forecast on error
            pass
    
    def _calculate_pattern(self, data: np.ndarray, period: int) -> np.ndarray:
        """Calculate average pattern over a given period"""
        if len(data) < period:
            return np.zeros(period)
            
        # Reshape data into periods
        n_periods = len(data) // period
        shaped = data[:n_periods * period].reshape(-1, period)
        
        # Calculate mean pattern
        return np.mean(shaped, axis=0)
    
    def _update_metrics(self) -> None:
        """Update forecast performance metrics"""
        try:
            # Get actual vs predicted values
            history = list(self.state.load_history)
            actual = np.array([d['load'] for d in history[-96:]])  # Last 24h
            predicted = np.array(self.state.forecast_values[:96])
            
            if len(actual) != len(predicted):
                return
                
            # Calculate MAPE
            mape = np.mean(np.abs((actual - predicted) / actual)) * 100
            
            # Calculate RMSE
            rmse = np.sqrt(np.mean((actual - predicted) ** 2))
            
            # Calculate forecast accuracy (% within confidence interval)
            in_interval = sum(1 for i, val in enumerate(actual)
                            if (self.state.forecast_confidence[i][0] <= val <=
                                self.state.forecast_confidence[i][1]))
            accuracy = (in_interval / len(actual)) * 100
            
            # Update metrics
            self.state.metrics = {
                'mape': float(mape),
                'rmse': float(rmse),
                'forecast_accuracy': float(accuracy),
                'last_update_duration': float(time.time() - self.state.last_update)
            }
            
        except Exception as e:
            pass
    
    def get_forecast(self) -> Dict[str, Any]:
        """Get current forecast and metrics"""
        return {
            'forecast_values': self.state.forecast_values,
            'forecast_confidence': self.state.forecast_confidence,
            'forecast_timestamp': self.state.forecast_timestamp,
            'metrics': self.state.metrics
        }
    
    def reset(self) -> None:
        """Reset forecaster state"""
        self.state = LoadForecastState()

def create_standard_load_forecaster(config: Optional[Dict[str, Any]] = None) -> LoadForecaster:
    """
    Factory function to create a standard load forecaster with optional configuration
    
    Args:
        config: Optional dictionary with configuration parameters
        
    Returns:
        Configured LoadForecaster instance
    """
    if config is None:
        return LoadForecaster()
        
    forecast_config = LoadForecastConfig(
        forecast_horizon=config.get('forecast_horizon', 24),
        update_interval=config.get('update_interval', 900.0),
        history_length=config.get('history_length', 168),
        confidence_level=config.get('confidence_level', 0.95),
        min_samples=config.get('min_samples', 96)
    )
    
    return LoadForecaster(config=forecast_config)

