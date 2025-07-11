import time
import math
import logging
from typing import Any, Dict, Optional, List
from dataclasses import dataclass
from collections import deque

"""
Voltage Regulator

Provides automatic voltage regulation (AVR) services for maintaining voltage
stability at the point of interconnection through reactive power control.

Response time: <500ms for fast voltage changes
Voltage range: 0.95-1.05 p.u.
Reactive power capacity: ±30% of rated power
Dead band: ±1% of nominal voltage
Droop: 2-5% typical
"""

@dataclass
class VoltageRegulatorConfig:
    """Configuration for voltage regulator"""
    nominal_voltage: float = 1.0  # p.u.
    voltage_range: tuple = (0.95, 1.05)  # p.u.
    dead_band: float = 0.01  # ±1%
    droop: float = 0.04  # 4%
    reactive_power_capacity: float = 0.30  # 30% of rated power
    response_time: float = 0.5  # seconds
    rated_power: float = 1000.0  # kVA

class VoltageRegulator:
    """
    Automatic voltage regulator (AVR) for maintaining grid voltage stability
    through reactive power control.
    """
    
    def __init__(self, config: Optional[VoltageRegulatorConfig] = None):
        """Initialize the voltage regulator"""
        self.config = config or VoltageRegulatorConfig()
        self.logger = logging.getLogger(__name__)
        
        # Controller state
        self.enabled = False
        self.last_update_time = 0.0
        self.current_reactive_power = 0.0  # kVAr
        self.target_reactive_power = 0.0  # kVAr
        
        # Performance tracking
        self.response_history: deque = deque(maxlen=1000)
        self.performance_metrics = {
            'total_activations': 0,
            'average_response_time': 0.0,
            'voltage_deviations_corrected': 0,
            'reactive_energy_provided': 0.0,  # kVArh
            'availability': 100.0  # %
        }
        
        self.logger.info("Voltage regulator initialized")
    
    def enable(self) -> bool:
        """Enable the regulator"""
        try:
            self.enabled = True
            self.logger.info("Voltage regulator enabled")
            return True
        except Exception as e:
            self.logger.error(f"Failed to enable regulator: {e}")
            return False
    
    def disable(self) -> bool:
        """Disable the regulator"""
        try:
            self.enabled = False
            self.current_reactive_power = 0.0
            self.target_reactive_power = 0.0
            self.logger.info("Voltage regulator disabled")
            return True
        except Exception as e:
            self.logger.error(f"Failed to disable regulator: {e}")
            return False
    
    def update(self, voltage: float, time_step: float) -> float:
        """
        Update regulator based on measured voltage
        
        Args:
            voltage: Measured voltage in p.u.
            time_step: Time step since last update in seconds
            
        Returns:
            Reactive power adjustment in kVAr
        """
        if not self.enabled:
            return 0.0
            
        try:
            # Calculate voltage deviation
            deviation = voltage - self.config.nominal_voltage
            
            # Check if deviation is within dead band
            if abs(deviation) <= self.config.dead_band:
                self.target_reactive_power = 0.0
                return self._adjust_reactive_power(time_step)
            
            # Calculate droop response
            # Q = -1/droop * voltage_deviation * rated_power
            response = -(1.0 / self.config.droop) * (deviation / self.config.nominal_voltage)
            
            # Limit response to reactive power capacity
            response = max(min(response, self.config.reactive_power_capacity),
                         -self.config.reactive_power_capacity)
            
            # Calculate target reactive power
            self.target_reactive_power = response * self.config.rated_power
            
            # Update metrics
            self._update_metrics(deviation, response)
            
            # Return reactive power adjustment
            return self._adjust_reactive_power(time_step)
            
        except Exception as e:
            self.logger.error(f"Error in voltage regulation update: {e}")
            return 0.0
    
    def _adjust_reactive_power(self, time_step: float) -> float:
        """
        Adjust reactive power output towards target with ramp rate limiting
        
        Args:
            time_step: Time step in seconds
            
        Returns:
            Actual reactive power adjustment in kVAr
        """
        # Calculate maximum reactive power change for this time step
        max_change = (self.config.rated_power * self.config.reactive_power_capacity * 
                     time_step / self.config.response_time)
        
        # Calculate desired reactive power change
        desired_change = self.target_reactive_power - self.current_reactive_power
        
        # Limit reactive power change
        actual_change = max(min(desired_change, max_change), -max_change)
        
        # Update current reactive power
        self.current_reactive_power += actual_change
        
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
            self.performance_metrics['voltage_deviations_corrected'] += 1
        
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
        """Get regulator state"""
        return {
            'enabled': self.enabled,
            'current_reactive_power': self.current_reactive_power,
            'target_reactive_power': self.target_reactive_power,
            'metrics': self.performance_metrics
        }
    
    def reset(self) -> None:
        """Reset regulator state"""
        self.enabled = False
        self.current_reactive_power = 0.0
        self.target_reactive_power = 0.0
        self.response_history.clear()
        self.performance_metrics = {
            'total_activations': 0,
            'average_response_time': 0.0,
            'voltage_deviations_corrected': 0,
            'reactive_energy_provided': 0.0,
            'availability': 100.0
        }


def create_standard_voltage_regulator() -> VoltageRegulator:
    """
    Create a voltage regulator with standard configuration.
    
    Returns:
        VoltageRegulator instance with standard settings
    """
    config = VoltageRegulatorConfig(
        nominal_voltage=1.0,
        voltage_range=(0.95, 1.05),
        dead_band=0.01,
        droop=0.04,
        reactive_power_capacity=0.30,
        response_time=0.5,
        rated_power=1000.0
    )
    return VoltageRegulator(config)

