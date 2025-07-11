"""
H3 Enhancement: Pulse-and-coast control for improved efficiency.
"""

import numpy as np
from typing import Dict, Any, Optional

class H3Enhancement:
    """H3 Enhancement: Pulse-and-coast control"""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize H3 enhancement"""
        self.config = config
        
        # H3 parameters
        self.pulse_duration = config.get('pulse_duration', 2.0)  # s
        self.coast_duration = config.get('coast_duration', 2.0)  # s
        self.min_speed_threshold = config.get('min_speed_threshold', 10.0)  # RPM
        self.max_speed_threshold = config.get('max_speed_threshold', 100.0)  # RPM
        
        # Control state
        self.enabled = False
        self.current_mode = 'pulse'  # 'pulse' or 'coast'
        self.mode_start_time = 0.0
        self.current_time = 0.0
        
        # Performance tracking
        self.energy_saved = 0.0  # J
        self.power_smoothing_factor = 0.0
        
        print("H3 Enhancement initialized")
        
    def enable(self) -> None:
        """Enable H3 enhancement"""
        self.enabled = True
        self.current_mode = 'pulse'
        self.mode_start_time = self.current_time
        print("H3 Enhancement enabled")
        
    def disable(self) -> None:
        """Disable H3 enhancement"""
        self.enabled = False
        self.current_mode = 'pulse'
        print("H3 Enhancement disabled")
        
    def update_control(self, current_time: float, current_speed: float) -> bool:
        """Update H3 control logic and return clutch engagement state"""
        self.current_time = current_time
        
        if not self.enabled:
            return True  # Always engaged when disabled
            
        # Check if speed is within acceptable range
        if current_speed < self.min_speed_threshold or current_speed > self.max_speed_threshold:
            return True  # Engage clutch for safety
            
        # Calculate time in current mode
        time_in_mode = current_time - self.mode_start_time
        
        # Determine current mode
        if self.current_mode == 'pulse':
            if time_in_mode >= self.pulse_duration:
                # Switch to coast mode
                self.current_mode = 'coast'
                self.mode_start_time = current_time
                print(f"H3: Switching to coast mode at {current_time:.1f}s")
        else:  # coast mode
            if time_in_mode >= self.coast_duration:
                # Switch to pulse mode
                self.current_mode = 'pulse'
                self.mode_start_time = current_time
                print(f"H3: Switching to pulse mode at {current_time:.1f}s")
                
        # Return clutch engagement state
        return self.current_mode == 'pulse'
        
    def calculate_power_smoothing(self, instantaneous_power: float, 
                                smoothed_power: float, dt: float) -> float:
        """Calculate power smoothing effect"""
        if not self.enabled:
            return instantaneous_power
            
        # Apply smoothing based on current mode
        if self.current_mode == 'pulse':
            # During pulse, allow more variation
            smoothing_factor = 0.3
        else:
            # During coast, smooth more aggressively
            smoothing_factor = 0.8
            
        # Exponential smoothing
        alpha = smoothing_factor * dt
        new_smoothed_power = alpha * instantaneous_power + (1 - alpha) * smoothed_power
        
        return new_smoothed_power
        
    def calculate_energy_savings(self, power_without_h3: float, 
                               power_with_h3: float, dt: float) -> float:
        """Calculate energy savings from H3 enhancement"""
        if not self.enabled:
            return 0.0
            
        # Calculate energy difference
        energy_diff = (power_without_h3 - power_with_h3) * dt
        self.energy_saved += max(0, energy_diff)
        
        return energy_diff
        
    def get_control_state(self) -> Dict[str, Any]:
        """Get current control state"""
        return {
            'enabled': self.enabled,
            'current_mode': self.current_mode,
            'mode_start_time': self.mode_start_time,
            'time_in_mode': self.current_time - self.mode_start_time,
            'pulse_duration': self.pulse_duration,
            'coast_duration': self.coast_duration,
            'min_speed_threshold': self.min_speed_threshold,
            'max_speed_threshold': self.max_speed_threshold
        }
        
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics"""
        return {
            'energy_saved': self.energy_saved,
            'power_smoothing_factor': self.power_smoothing_factor,
            'current_mode': self.current_mode,
            'enabled': self.enabled
        }
