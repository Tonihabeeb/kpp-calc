import time
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
import numpy as np
from enum import Enum

class ForecastMethod(Enum):
    """Price forecasting methods"""
    SIMPLE = "simple"  # Moving averages and basic patterns
    ADVANCED = "advanced"  # Time series decomposition
    NEURAL = "neural"  # Neural network based (simulated)
    ENSEMBLE = "ensemble"  # Combination of methods

@dataclass
class PriceForecasterConfig:
    """Configuration for price forecaster"""
    forecast_horizon: int = 24  # Hours to forecast ahead
    update_interval: float = 900.0  # Seconds between updates (15 min)
    history_length: int = 168  # Hours of history to maintain (1 week)
    confidence_level: float = 0.95  # Confidence level for predictions
    min_samples: int = 96  # Minimum samples before forecasting (24h at 15min)
    method: ForecastMethod = ForecastMethod.ENSEMBLE

@dataclass
class ForecastState:
    """State for price forecaster"""
    last_update: float = 0.0
    price_history: List[Dict[str, Any]] = field(default_factory=list)
    forecast_values: Dict[str, List[float]] = field(default_factory=lambda: {
        'energy': [],
        'reserve': [],
        'capacity': []
    })
    forecast_confidence: Dict[str, List[Tuple[float, float]]] = field(
        default_factory=lambda: {
            'energy': [],
            'reserve': [],
            'capacity': []
        })
    forecast_timestamp: float = 0.0
    metrics: Dict[str, float] = field(default_factory=lambda: {
        'mape': 0.0,  # Mean Absolute Percentage Error
        'rmse': 0.0,  # Root Mean Square Error
        'forecast_accuracy': 0.0,  # % within confidence interval
        'last_update_duration': 0.0  # Seconds
    })

class PriceForecaster:
    """
    Price forecaster for market price prediction.
    Implements multiple forecasting methods and ensemble predictions.
    """
    
    def __init__(self, config: Optional[PriceForecasterConfig] = None):
        """Initialize price forecaster"""
        self.config = config or PriceForecasterConfig()
        self.state = ForecastState()
    
    def update(self, market_data: Dict[str, Any], time_step: float) -> Dict[str, Any]:
        """
        Update price forecasts
        
        Args:
            market_data: Current market prices and metadata
            time_step: Time step since last update in seconds
            
        Returns:
            Dictionary containing forecast values and confidence intervals
        """
        try:
            # Add new data point to history
            self._update_history(market_data)
            
            current_time = time.time()
            if (current_time - self.state.last_update >= self.config.update_interval and
                len(self.state.price_history) >= self.config.min_samples):
                # Generate new forecast
                self._generate_forecast()
                self._update_metrics()
                self.state.last_update = current_time
            
            return self.get_forecast()
            
        except Exception as e:
            return self.get_forecast()
    
    def _update_history(self, market_data: Dict[str, Any]) -> None:
        """Update price history with new market data"""
        self.state.price_history.append({
            'timestamp': time.time(),
            'energy_price': market_data.get('energy_price', 0.0),
            'reserve_price': market_data.get('reserve_price', 0.0),
            'capacity_price': market_data.get('capacity_price', 0.0),
            'demand': market_data.get('demand', 0.0),
            'temperature': market_data.get('temperature', 20.0)
        })
        
        # Keep only recent history
        max_history = int(self.config.history_length * 4)  # 15min intervals
        if len(self.state.price_history) > max_history:
            self.state.price_history = self.state.price_history[-max_history:]
    
    def _generate_forecast(self) -> None:
        """Generate price forecasts using selected method"""
        try:
            if self.config.method == ForecastMethod.ENSEMBLE:
                self._generate_ensemble_forecast()
            elif self.config.method == ForecastMethod.ADVANCED:
                self._generate_advanced_forecast()
            elif self.config.method == ForecastMethod.NEURAL:
                self._generate_neural_forecast()
            else:
                self._generate_simple_forecast()
                
            self.state.forecast_timestamp = time.time()
            
        except Exception as e:
            # Keep previous forecast on error
            pass
    
    def _generate_simple_forecast(self) -> None:
        """Generate forecast using simple methods"""
        for price_type in ['energy', 'reserve', 'capacity']:
            # Get historical prices
            prices = np.array([
                d[f'{price_type}_price']
                for d in self.state.price_history
            ])
            
            # Calculate basic statistics
            mean_price = np.mean(prices)
            std_price = np.std(prices)
            
            # Find daily and weekly patterns
            samples_per_day = 96  # 15min intervals
            daily_pattern = self._calculate_pattern(prices, samples_per_day)
            weekly_pattern = self._calculate_pattern(
                prices, samples_per_day * 7)
            
            # Generate forecast points
            forecast_points = int(self.config.forecast_horizon * 4)
            forecast = []
            confidence = []
            
            for i in range(forecast_points):
                # Combine patterns for prediction
                time_of_day = i % samples_per_day
                day_of_week = (i // samples_per_day) % 7
                
                base_prediction = (
                    0.5 * daily_pattern[time_of_day] +
                    0.3 * weekly_pattern[day_of_week * samples_per_day +
                                       time_of_day] +
                    0.2 * mean_price
                )
                
                # Add confidence intervals
                confidence_width = std_price * 1.96  # 95% confidence
                confidence.append((
                    max(0, base_prediction - confidence_width),
                    base_prediction + confidence_width
                ))
                forecast.append(base_prediction)
            
            # Update state
            self.state.forecast_values[price_type] = forecast
            self.state.forecast_confidence[price_type] = confidence
    
    def _generate_advanced_forecast(self) -> None:
        """Generate forecast using time series decomposition"""
        for price_type in ['energy', 'reserve', 'capacity']:
            # Get historical prices
            prices = np.array([
                d[f'{price_type}_price']
                for d in self.state.price_history
            ])
            
            # Decompose time series
            trend = self._calculate_trend(prices)
            seasonal = self._calculate_seasonality(prices)
            residual = prices - trend - seasonal
            
            # Forecast components
            trend_forecast = self._forecast_trend(trend)
            seasonal_forecast = self._forecast_seasonality(seasonal)
            residual_std = np.std(residual)
            
            # Combine forecasts
            forecast_points = int(self.config.forecast_horizon * 4)
            forecast = []
            confidence = []
            
            for i in range(forecast_points):
                prediction = (trend_forecast[i] + seasonal_forecast[i])
                
                # Add confidence intervals
                confidence_width = residual_std * 1.96
                confidence.append((
                    max(0, prediction - confidence_width),
                    prediction + confidence_width
                ))
                forecast.append(prediction)
            
            # Update state
            self.state.forecast_values[price_type] = forecast
            self.state.forecast_confidence[price_type] = confidence
    
    def _generate_neural_forecast(self) -> None:
        """Generate forecast using simulated neural network"""
        for price_type in ['energy', 'reserve', 'capacity']:
            # Get historical prices
            prices = np.array([
                d[f'{price_type}_price']
                for d in self.state.price_history
            ])
            
            # Simulate neural network prediction
            # In reality, this would use a trained neural network
            mean_price = np.mean(prices)
            std_price = np.std(prices)
            
            # Generate forecast points with simulated uncertainty
            forecast_points = int(self.config.forecast_horizon * 4)
            forecast = []
            confidence = []
            
            for i in range(forecast_points):
                # Simulate prediction with increasing uncertainty
                uncertainty = std_price * (1 + i / forecast_points)
                prediction = mean_price + np.random.normal(0, uncertainty * 0.1)
                
                confidence_width = uncertainty * 1.96
                confidence.append((
                    max(0, prediction - confidence_width),
                    prediction + confidence_width
                ))
                forecast.append(prediction)
            
            # Update state
            self.state.forecast_values[price_type] = forecast
            self.state.forecast_confidence[price_type] = confidence
    
    def _generate_ensemble_forecast(self) -> None:
        """Generate forecast using ensemble of methods"""
        # Generate forecasts using all methods
        self._generate_simple_forecast()
        simple_forecast = {k: v.copy() for k, v in
                         self.state.forecast_values.items()}
        simple_confidence = {k: v.copy() for k, v in
                           self.state.forecast_confidence.items()}
        
        self._generate_advanced_forecast()
        advanced_forecast = {k: v.copy() for k, v in
                           self.state.forecast_values.items()}
        advanced_confidence = {k: v.copy() for k, v in
                             self.state.forecast_confidence.items()}
        
        self._generate_neural_forecast()
        neural_forecast = {k: v.copy() for k, v in
                         self.state.forecast_values.items()}
        neural_confidence = {k: v.copy() for k, v in
                           self.state.forecast_confidence.items()}
        
        # Combine forecasts with weighted average
        weights = {'simple': 0.3, 'advanced': 0.4, 'neural': 0.3}
        
        for price_type in ['energy', 'reserve', 'capacity']:
            forecast_points = len(simple_forecast[price_type])
            forecast = []
            confidence = []
            
            for i in range(forecast_points):
                # Weighted average of predictions
                prediction = (
                    weights['simple'] * simple_forecast[price_type][i] +
                    weights['advanced'] * advanced_forecast[price_type][i] +
                    weights['neural'] * neural_forecast[price_type][i]
                )
                
                # Combine confidence intervals
                lower = max(0, min(
                    simple_confidence[price_type][i][0],
                    advanced_confidence[price_type][i][0],
                    neural_confidence[price_type][i][0]
                ))
                upper = max(
                    simple_confidence[price_type][i][1],
                    advanced_confidence[price_type][i][1],
                    neural_confidence[price_type][i][1]
                )
                
                confidence.append((lower, upper))
                forecast.append(prediction)
            
            # Update state
            self.state.forecast_values[price_type] = forecast
            self.state.forecast_confidence[price_type] = confidence
    
    def _calculate_pattern(self, data: np.ndarray, period: int) -> np.ndarray:
        """Calculate average pattern over a given period"""
        if len(data) < period:
            return np.zeros(period)
            
        # Reshape data into periods
        n_periods = len(data) // period
        shaped = data[:n_periods * period].reshape(-1, period)
        
        # Calculate mean pattern
        return np.mean(shaped, axis=0)
    
    def _calculate_trend(self, data: np.ndarray) -> np.ndarray:
        """Calculate trend component using moving average"""
        window = 96  # 24 hours
        if len(data) < window:
            return np.zeros_like(data)
            
        # Simple moving average
        trend = np.convolve(data, np.ones(window)/window, mode='same')
        
        # Pad edges
        trend[:window//2] = trend[window//2]
        trend[-window//2:] = trend[-window//2]
        
        return trend
    
    def _calculate_seasonality(self, data: np.ndarray) -> np.ndarray:
        """Calculate seasonal component"""
        if len(data) < 96:  # Need at least one day
            return np.zeros_like(data)
            
        # Daily seasonality
        daily_pattern = self._calculate_pattern(data, 96)
        
        # Repeat pattern for all days
        n_days = len(data) // 96
        seasonal = np.tile(daily_pattern, n_days)
        
        # Pad remaining points
        remainder = len(data) - len(seasonal)
        if remainder > 0:
            seasonal = np.concatenate([
                seasonal,
                daily_pattern[:remainder]
            ])
        
        return seasonal
    
    def _forecast_trend(self, trend: np.ndarray) -> np.ndarray:
        """Forecast trend component"""
        # Simple linear extrapolation
        x = np.arange(len(trend))
        coeffs = np.polyfit(x, trend, deg=1)
        
        # Project forward
        forecast_points = int(self.config.forecast_horizon * 4)
        x_forecast = np.arange(
            len(trend),
            len(trend) + forecast_points
        )
        
        return np.polyval(coeffs, x_forecast)
    
    def _forecast_seasonality(self, seasonal: np.ndarray) -> np.ndarray:
        """Forecast seasonal component"""
        # Repeat the last day's pattern
        daily_pattern = seasonal[-96:]
        forecast_points = int(self.config.forecast_horizon * 4)
        n_days = forecast_points // 96 + 1
        
        forecast = np.tile(daily_pattern, n_days)[:forecast_points]
        return forecast
    
    def _update_metrics(self) -> None:
        """Update forecast performance metrics"""
        try:
            # Get actual vs predicted values for each price type
            for price_type in ['energy', 'reserve', 'capacity']:
                history = [d[f'{price_type}_price']
                          for d in self.state.price_history[-96:]]  # Last 24h
                predicted = self.state.forecast_values[price_type][:96]
                confidence = self.state.forecast_confidence[price_type][:96]
                
                if len(history) != len(predicted):
                    continue
                    
                # Calculate MAPE
                mape = np.mean(np.abs(
                    (np.array(history) - np.array(predicted)) /
                    np.array(history)
                )) * 100
                
                # Calculate RMSE
                rmse = np.sqrt(np.mean(
                    (np.array(history) - np.array(predicted)) ** 2
                ))
                
                # Calculate forecast accuracy
                in_interval = sum(1 for i, val in enumerate(history)
                                if confidence[i][0] <= val <= confidence[i][1])
                accuracy = (in_interval / len(history)) * 100
                
                # Update metrics
                self.state.metrics.update({
                    f'{price_type}_mape': float(mape),
                    f'{price_type}_rmse': float(rmse),
                    f'{price_type}_accuracy': float(accuracy)
                })
            
            # Overall metrics
            self.state.metrics.update({
                'mape': float(np.mean([
                    self.state.metrics[f'{pt}_mape']
                    for pt in ['energy', 'reserve', 'capacity']
                ])),
                'rmse': float(np.mean([
                    self.state.metrics[f'{pt}_rmse']
                    for pt in ['energy', 'reserve', 'capacity']
                ])),
                'forecast_accuracy': float(np.mean([
                    self.state.metrics[f'{pt}_accuracy']
                    for pt in ['energy', 'reserve', 'capacity']
                ])),
                'last_update_duration': float(time.time() - self.state.last_update)
            })
            
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
        self.state = ForecastState()

def create_price_forecaster(config: Optional[Dict[str, Any]] = None) -> PriceForecaster:
    """
    Factory function to create a price forecaster with optional configuration
    
    Args:
        config: Optional dictionary with configuration parameters
        
    Returns:
        Configured PriceForecaster instance
    """
    if config is None:
        return PriceForecaster()
        
    forecast_config = PriceForecasterConfig(
        forecast_horizon=config.get('forecast_horizon', 24),
        update_interval=config.get('update_interval', 900.0),
        history_length=config.get('history_length', 168),
        confidence_level=config.get('confidence_level', 0.95),
        min_samples=config.get('min_samples', 96),
        method=ForecastMethod(config.get('method', 'ensemble'))
    )
    
    return PriceForecaster(config=forecast_config)

