"""
Synthetic Inertia Controller

Provides virtual inertia response to emulate synchronous generator behavior.
Implements ROCOF (Rate of Change of Frequency) detection and fast response.

Response time: <500ms
ROCOF threshold: 0.5 Hz/s (configurable)
Inertia constant: 2-8 seconds (configurable)
Response duration: 10-30 seconds
Measurement window: 100ms for ROCOF calculation
"""

import time
import math
from typing import Any, Dict, Optional
from dataclasses import dataclass
from collections import deque

@dataclass
class SyntheticInertiaConfig:
    """Configuration for synthetic inertia control"""
    nominal_frequency: float = 50.0  # Hz
    inertia_constant: float = 4.0  # seconds
    rocof_threshold: float = 0.5  # Hz/s
    response_time: float = 0.5  # seconds
    response_duration: float = 20.0  # seconds
    measurement_window: float = 0.1  # seconds
    rated_power: float = 1000.0  # kW

class SyntheticInertiaController:
    """
    Synthetic Inertia Controller implementing virtual inertia response
    for grid frequency stability support.
    """
    
    def __init__(self, config: Optional[SyntheticInertiaConfig] = None):
        """Initialize synthetic inertia controller"""
        self.config = config or SyntheticInertiaConfig()
        
        # Controller state
        self.enabled = False
        self.last_update_time = 0.0
        self.frequency_history = deque(maxlen=int(self.config.measurement_window / 0.01))
        self.current_rocof = 0.0
        self.current_power = 0.0
        self.response_start_time = 0.0
        self.is_responding = False
        
        # Performance tracking
        self.performance_metrics = {
            'total_activations': 0,
            'average_response_time': 0.0,
            'total_energy_provided': 0.0,  # kWh
            'max_rocof_detected': 0.0,  # Hz/s
            'availability': 100.0  # %
        }
    
    def enable(self) -> bool:
        """Enable the controller"""
        self.enabled = True
        return True
    
    def disable(self) -> bool:
        """Disable the controller"""
        self.enabled = False
        self.current_power = 0.0
        self.is_responding = False
        return True
    
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
            # Update frequency history
            self.frequency_history.append(frequency)
            
            # Calculate ROCOF
            if len(self.frequency_history) >= 2:
                freq_change = self.frequency_history[-1] - self.frequency_history[0]
                time_window = len(self.frequency_history) * time_step
                self.current_rocof = freq_change / time_window
            
            # Check if response needed
            if abs(self.current_rocof) > self.config.rocof_threshold and not self.is_responding:
                self.is_responding = True
                self.response_start_time = time.time()
                self.performance_metrics['total_activations'] += 1
                self.performance_metrics['max_rocof_detected'] = max(
                    self.performance_metrics['max_rocof_detected'],
                    abs(self.current_rocof)
                )
            
            # Calculate response
            if self.is_responding:
                response_time = time.time() - self.response_start_time
                
                if response_time > self.config.response_duration:
                    # End response
                    self.is_responding = False
                    self.current_power = 0.0
                else:
                    # Calculate power response
                    # P = 2H * df/dt * Srated
                    power = (2.0 * self.config.inertia_constant * 
                           self.current_rocof * self.config.rated_power)
                    
                    # Apply response time characteristic
                    ramp_factor = min(response_time / self.config.response_time, 1.0)
                    self.current_power = power * ramp_factor
                    
                    # Update energy metrics
                    self.performance_metrics['total_energy_provided'] += (
                        abs(self.current_power) * time_step / 3600.0
                    )
            
            return self.current_power
            
        except Exception as e:
            self.is_responding = False
            self.current_power = 0.0
            return 0.0
    
    def get_state(self) -> Dict[str, Any]:
        """Get controller state"""
        return {
            'enabled': self.enabled,
            'current_rocof': self.current_rocof,
            'current_power': self.current_power,
            'is_responding': self.is_responding,
            'metrics': self.performance_metrics
        }
    
    def reset(self):
        """Reset controller state"""
        self.enabled = False
        self.frequency_history.clear()
        self.current_rocof = 0.0
        self.current_power = 0.0
        self.is_responding = False
        self.performance_metrics = {
            'total_activations': 0,
            'average_response_time': 0.0,
            'total_energy_provided': 0.0,
            'max_rocof_detected': 0.0,
            'availability': 100.0
        }

