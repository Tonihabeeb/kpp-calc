import time
import math
import logging
from typing import Any, Dict, Optional, List
from dataclasses import dataclass
from collections import deque

"""
Power Factor Controller

Provides power factor control and reactive power optimization for efficient
grid operation and compliance with utility interconnection requirements.

Response time: <1 second
Power factor range: 0.85 leading to 0.85 lagging
Reactive power capacity: ±30% of rated power
Dead band: ±0.02 power factor
Priority: Lower than voltage regulation
"""

@dataclass
class PowerFactorConfig:
    """Configuration for power factor controller"""
    target_power_factor: float = 0.98  # Target power factor
    power_factor_range: tuple = (0.85, 0.85)  # (leading, lagging)
    dead_band: float = 0.02  # ±2%
    reactive_power_capacity: float = 0.30  # 30% of rated power
    response_time: float = 1.0  # seconds
    rated_power: float = 1000.0  # kVA
    priority_factor: float = 0.5  # Priority relative to voltage regulation

class PowerFactorController:
    """
    Power factor controller for maintaining optimal power factor and
    reactive power utilization.
    """
    
    def __init__(self, config: Optional[PowerFactorConfig] = None):
        """Initialize the power factor controller"""
        self.config = config or PowerFactorConfig()
        self.logger = logging.getLogger(__name__)
        
        # Controller state
        self.enabled = False
        self.last_update_time = 0.0
        self.current_reactive_power = 0.0  # kVAr
        self.target_reactive_power = 0.0  # kVAr
        self.current_power_factor = 1.0
        
        # Performance tracking
        self.response_history: deque = deque(maxlen=1000)
        self.performance_metrics = {
            'total_adjustments': 0,
            'average_response_time': 0.0,
            'power_factor_deviations_corrected': 0,
            'reactive_energy_provided': 0.0,  # kVArh
            'availability': 100.0,  # %
            'average_power_factor': 1.0
        }
        
        self.logger.info("Power factor controller initialized")
    
    def enable(self) -> bool:
        """Enable the controller"""
        try:
            self.enabled = True
            self.logger.info("Power factor controller enabled")
            return True
        except Exception as e:
            self.logger.error(f"Failed to enable controller: {e}")
            return False
    
    def disable(self) -> bool:
        """Disable the controller"""
        try:
            self.enabled = False
            self.current_reactive_power = 0.0
            self.target_reactive_power = 0.0
            self.current_power_factor = 1.0
            self.logger.info("Power factor controller disabled")
            return True
        except Exception as e:
            self.logger.error(f"Failed to disable controller: {e}")
            return False
    
    def update(self, active_power: float, power_factor: float, time_step: float) -> float:
        """
        Update controller based on measured power and power factor
        
        Args:
            active_power: Measured active power in kW
            power_factor: Measured power factor
            time_step: Time step since last update in seconds
            
        Returns:
            Reactive power adjustment in kVAr
        """
        if not self.enabled:
            return 0.0
            
        try:
            # Store current power factor
            self.current_power_factor = power_factor
            
            # Calculate power factor deviation
            deviation = power_factor - self.config.target_power_factor
            
            # Check if deviation is within dead band
            if abs(deviation) <= self.config.dead_band:
                self.target_reactive_power = 0.0
                return self._adjust_reactive_power(time_step)
            
            # Calculate required reactive power for target power factor
            target_reactive_power = self._calculate_required_reactive_power(
                active_power, self.config.target_power_factor
            )
            
            # Limit reactive power to capacity
            max_reactive_power = self.config.rated_power * self.config.reactive_power_capacity
            self.target_reactive_power = max(min(target_reactive_power, max_reactive_power),
                                          -max_reactive_power)
            
            # Update metrics
            self._update_metrics(deviation, self.target_reactive_power)
            
            # Return reactive power adjustment
            return self._adjust_reactive_power(time_step)
            
        except Exception as e:
            self.logger.error(f"Error in power factor control update: {e}")
            return 0.0
    
    def _calculate_required_reactive_power(self, active_power: float, 
                                        target_pf: float) -> float:
        """
        Calculate required reactive power for target power factor
        
        Args:
            active_power: Active power in kW
            target_pf: Target power factor
            
        Returns:
            Required reactive power in kVAr
        """
        # Q = P * tan(arccos(PF))
        phi = math.acos(target_pf)
        return active_power * math.tan(phi)
    
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
        
        # Apply priority factor to change rate
        max_change *= self.config.priority_factor
        
        # Limit reactive power change
        actual_change = max(min(desired_change, max_change), -max_change)
        
        # Update current reactive power
        self.current_reactive_power += actual_change
        
        return actual_change
    
    def _update_metrics(self, deviation: float, reactive_power: float) -> None:
        """Update performance metrics"""
        timestamp = time.time()
        
        # Record response
        self.response_history.append({
            'timestamp': timestamp,
            'deviation': deviation,
            'reactive_power': reactive_power,
            'power_factor': self.current_power_factor
        })
        
        # Update metrics
        self.performance_metrics['total_adjustments'] += 1
        if abs(deviation) > self.config.dead_band and abs(deviation) < 2 * self.config.dead_band:
            self.performance_metrics['power_factor_deviations_corrected'] += 1
        
        # Update average power factor
        if len(self.response_history) > 0:
            power_factors = [record['power_factor'] for record in self.response_history]
            self.performance_metrics['average_power_factor'] = sum(power_factors) / len(power_factors)
        
        # Calculate average response time
        if len(self.response_history) >= 2:
            response_times = []
            for i in range(1, len(self.response_history)):
                if (abs(self.response_history[i]['reactive_power']) > 0.01 * self.config.rated_power and 
                    abs(self.response_history[i-1]['reactive_power']) <= 0.01 * self.config.rated_power):
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
            'current_reactive_power': self.current_reactive_power,
            'target_reactive_power': self.target_reactive_power,
            'current_power_factor': self.current_power_factor,
            'metrics': self.performance_metrics
        }
    
    def reset(self) -> None:
        """Reset controller state"""
        self.enabled = False
        self.current_reactive_power = 0.0
        self.target_reactive_power = 0.0
        self.current_power_factor = 1.0
        self.response_history.clear()
        self.performance_metrics = {
            'total_adjustments': 0,
            'average_response_time': 0.0,
            'power_factor_deviations_corrected': 0,
            'reactive_energy_provided': 0.0,
            'availability': 100.0,
            'average_power_factor': 1.0
        }


def create_standard_power_factor_controller() -> PowerFactorController:
    """
    Create a power factor controller with standard configuration.
    
    Returns:
        PowerFactorController instance with standard settings
    """
    config = PowerFactorConfig(
        target_power_factor=0.98,
        power_factor_range=(0.85, 0.85),
        dead_band=0.02,
        reactive_power_capacity=0.30,
        response_time=1.0,
        rated_power=1000.0,
        priority_factor=0.5
    )
    return PowerFactorController(config)

