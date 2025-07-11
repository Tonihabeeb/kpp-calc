import time
import math
import logging
from typing import Any, Dict, Optional, List
from dataclasses import dataclass
from collections import deque

"""
Secondary Frequency Controller

Provides secondary frequency response through AGC (Automatic Generation Control) signals.
Implements regulation service with bidirectional power adjustment and ramp rate control.

Response time: <5 minutes
AGC signal range: ±1.0 (normalized)
Regulation capacity: ±5% of rated power
Ramp rate: 20% of rated power per minute
Accuracy: ±1% of AGC signal
"""

@dataclass
class SecondaryFrequencyConfig:
    """Configuration for secondary frequency control"""
    regulation_capacity: float = 0.05  # 5% of rated power
    ramp_rate: float = 0.20  # 20% per minute
    response_time: float = 300.0  # 5 minutes
    rated_power: float = 1000.0  # kW
    control_accuracy: float = 0.01  # 1%
    agc_deadband: float = 0.01  # 1% of signal

class SecondaryFrequencyController:
    """
    Secondary frequency controller implementing AGC response for frequency regulation.
    Provides sustained power adjustment based on system operator signals.
    """
    
    def __init__(self, config: Optional[SecondaryFrequencyConfig] = None):
        """Initialize the secondary frequency controller"""
        self.config = config or SecondaryFrequencyConfig()
        self.logger = logging.getLogger(__name__)
        
        # Controller state
        self.enabled = False
        self.last_update_time = 0.0
        self.current_power = 0.0  # kW
        self.target_power = 0.0  # kW
        self.agc_signal = 0.0  # -1.0 to 1.0
        
        # Performance tracking
        self.response_history: deque = deque(maxlen=1000)
        self.performance_metrics = {
            'total_agc_signals': 0,
            'average_response_time': 0.0,
            'control_accuracy': 100.0,  # %
            'energy_provided': 0.0,  # kWh
            'availability': 100.0,  # %
            'successful_responses': 0
        }
        
        self.logger.info("Secondary frequency controller initialized")
    
    def enable(self) -> bool:
        """Enable the controller"""
        try:
            self.enabled = True
            self.logger.info("Secondary frequency controller enabled")
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
            self.agc_signal = 0.0
            self.logger.info("Secondary frequency controller disabled")
            return True
        except Exception as e:
            self.logger.error(f"Failed to disable controller: {e}")
            return False
    
    def update(self, agc_signal: float, time_step: float) -> float:
        """
        Update controller based on AGC signal
        
        Args:
            agc_signal: AGC signal from system operator (-1.0 to 1.0)
            time_step: Time step since last update in seconds
            
        Returns:
            Power adjustment in kW
        """
        if not self.enabled:
            return 0.0
            
        try:
            # Validate and store AGC signal
            self.agc_signal = max(min(agc_signal, 1.0), -1.0)
            
            # Check if signal is within deadband
            if abs(self.agc_signal) <= self.config.agc_deadband:
                self.target_power = 0.0
                return self._adjust_power(time_step)
            
            # Calculate target power based on AGC signal
            self.target_power = (self.agc_signal * self.config.regulation_capacity * 
                               self.config.rated_power)
            
            # Update metrics
            self._update_metrics(self.agc_signal)
            
            # Return power adjustment
            return self._adjust_power(time_step)
            
        except Exception as e:
            self.logger.error(f"Error in AGC response update: {e}")
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
        max_change = (self.config.rated_power * self.config.ramp_rate * 
                     time_step / 60.0)  # Convert from per minute to per second
        
        # Calculate desired power change
        desired_change = self.target_power - self.current_power
        
        # Limit power change
        actual_change = max(min(desired_change, max_change), -max_change)
        
        # Update current power
        self.current_power += actual_change
        
        return actual_change
    
    def _update_metrics(self, agc_signal: float) -> None:
        """Update performance metrics"""
        timestamp = time.time()
        
        # Record response
        self.response_history.append({
            'timestamp': timestamp,
            'agc_signal': agc_signal,
            'power': self.current_power
        })
        
        # Update metrics
        self.performance_metrics['total_agc_signals'] += 1
        
        # Calculate control accuracy
        if len(self.response_history) >= 2:
            # Calculate error between target and actual power
            error = abs(self.current_power - self.target_power) / self.config.rated_power
            
            # Update accuracy metric (100% - error%)
            self.performance_metrics['control_accuracy'] = max(0.0, 100.0 * (1.0 - error))
            
            # Check if response was successful
            if error <= self.config.control_accuracy:
                self.performance_metrics['successful_responses'] += 1
            
            # Calculate response time
            response_times = []
            for i in range(1, len(self.response_history)):
                if (abs(self.response_history[i]['power']) > 0.01 * self.config.rated_power and 
                    abs(self.response_history[i-1]['power']) <= 0.01 * self.config.rated_power):
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
            'agc_signal': self.agc_signal,
            'metrics': self.performance_metrics
        }
    
    def reset(self) -> None:
        """Reset controller state"""
        self.enabled = False
        self.current_power = 0.0
        self.target_power = 0.0
        self.agc_signal = 0.0
        self.response_history.clear()
        self.performance_metrics = {
            'total_agc_signals': 0,
            'average_response_time': 0.0,
            'control_accuracy': 100.0,
            'energy_provided': 0.0,
            'availability': 100.0,
            'successful_responses': 0
        }

