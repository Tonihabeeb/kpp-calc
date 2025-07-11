import time
import math
import logging
from typing import Any, Dict, Optional, List
from dataclasses import dataclass
from collections import deque

"""
Primary Frequency Controller

Provides fast frequency response for grid stability through primary frequency control.
Implements droop control with configurable dead band and response characteristics.

Response time: <2 seconds
Dead band: ±0.02 Hz (configurable)
Droop setting: 2-5% (configurable)
Response range: ±10% of rated power
"""

@dataclass
class PrimaryFrequencyConfig:
    """Configuration for primary frequency control"""
    nominal_frequency: float = 50.0  # Hz
    dead_band: float = 0.02  # Hz
    droop: float = 0.04  # 4%
    max_response: float = 0.10  # 10% of rated power
    response_time: float = 2.0  # seconds
    rated_power: float = 1000.0  # kW

class PrimaryFrequencyController:
    """
    Primary frequency controller implementing droop control for fast frequency response.
    Provides immediate power adjustment based on frequency deviations.
    """
    
    def __init__(self, config: Optional[PrimaryFrequencyConfig] = None):
        """Initialize the primary frequency controller"""
        self.config = config or PrimaryFrequencyConfig()
        self.logger = logging.getLogger(__name__)
        
        # Controller state
        self.enabled = False
        self.last_update_time = 0.0
        self.current_power = 0.0  # kW
        self.target_power = 0.0  # kW
        
        # Performance tracking
        self.response_history: deque = deque(maxlen=1000)
        self.performance_metrics = {
            'total_activations': 0,
            'average_response_time': 0.0,
            'frequency_deviations_corrected': 0,
            'energy_provided': 0.0,  # kWh
            'availability': 100.0  # %
        }
        
        self.logger.info("Primary frequency controller initialized")
    
    def enable(self) -> bool:
        """Enable the controller"""
        try:
            self.enabled = True
            self.logger.info("Primary frequency controller enabled")
            return True
        except Exception as e:
            self.logger.error(f"Failed to enable controller: {e}")
            return False
    
    def disable(self) -> bool:
        """Disable the controller"""
        try:
            self.enabled = False
            self.current_power = 0.0
            self.target_power = 0.0
            self.logger.info("Primary frequency controller disabled")
            return True
        except Exception as e:
            self.logger.error(f"Failed to disable controller: {e}")
            return False
    
    def update(self, frequency: float, time_step: float) -> float:
        """
        Update controller based on current frequency
        
        Args:
            frequency: Current grid frequency in Hz
            time_step: Time step since last update in seconds
            
        Returns:
            Power adjustment in kW
        """
        if not self.enabled:
            return 0.0
            
        try:
            # Calculate frequency deviation
            deviation = frequency - self.config.nominal_frequency
            
            # Check if deviation is within dead band
            if abs(deviation) <= self.config.dead_band:
                self.target_power = 0.0
                return self._adjust_power(time_step)
            
            # Calculate droop response
            # Power = -1/droop * frequency_deviation * rated_power
            response = -(1.0 / self.config.droop) * (deviation / self.config.nominal_frequency)
            
            # Limit response to maximum
            response = max(min(response, self.config.max_response), -self.config.max_response)
            
            # Calculate target power
            self.target_power = response * self.config.rated_power
            
            # Update metrics
            self._update_metrics(deviation, response)
            
            # Return power adjustment
            return self._adjust_power(time_step)
            
        except Exception as e:
            self.logger.error(f"Error in frequency control update: {e}")
            return 0.0
    
    def _adjust_power(self, time_step: float) -> float:
        """
        Adjust power output towards target with ramp rate limiting
        
        Args:
            time_step: Time step in seconds
            
        Returns:
            Actual power adjustment in kW
        """
        # Calculate maximum power change for this time step
        max_change = (self.config.rated_power * self.config.max_response * 
                     time_step / self.config.response_time)
        
        # Calculate desired power change
        desired_change = self.target_power - self.current_power
        
        # Limit power change
        actual_change = max(min(desired_change, max_change), -max_change)
        
        # Update current power
        self.current_power += actual_change
        
        return actual_change
    
    def _update_metrics(self, deviation: float, response: float) -> None:
        """Update performance metrics"""
        timestamp = time.time()
        
        # Record response
        self.response_history.append({
            'timestamp': timestamp,
            'deviation': deviation,
            'response': response
        })
        
        # Update metrics
        self.performance_metrics['total_activations'] += 1
        if abs(deviation) > self.config.dead_band and abs(deviation) < 2 * self.config.dead_band:
            self.performance_metrics['frequency_deviations_corrected'] += 1
        
        # Calculate average response time
        if len(self.response_history) >= 2:
            response_times = []
            for i in range(1, len(self.response_history)):
                if (abs(self.response_history[i]['response']) > 0.01 and 
                    abs(self.response_history[i-1]['response']) <= 0.01):
                    response_times.append(
                        self.response_history[i]['timestamp'] - 
                        self.response_history[i-1]['timestamp']
                    )
            if response_times:
                self.performance_metrics['average_response_time'] = (
                    sum(response_times) / len(response_times)
                )
    
    def get_state(self) -> Dict[str, Any]:
        """Get controller state"""
        return {
            'enabled': self.enabled,
            'current_power': self.current_power,
            'target_power': self.target_power,
            'metrics': self.performance_metrics
        }
    
    def reset(self) -> None:
        """Reset controller state"""
        self.enabled = False
        self.current_power = 0.0
        self.target_power = 0.0
        self.response_history.clear()
        self.performance_metrics = {
            'total_activations': 0,
            'average_response_time': 0.0,
            'frequency_deviations_corrected': 0,
            'energy_provided': 0.0,
            'availability': 100.0
        }

