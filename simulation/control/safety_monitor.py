"""
Safety monitoring system for KPP simulator.
"""

import numpy as np
from typing import Dict, Any, List, Callable
from enum import Enum

class SafetyLevel(Enum):
    """Safety levels"""
    NORMAL = "normal"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"

class SafetyMonitor:
    """Safety monitoring system"""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize safety monitor"""
        self.config = config
        
        # Safety thresholds
        self.max_speed = config.get('max_speed', 100.0)  # RPM
        self.max_torque = config.get('max_torque', 1000.0)  # N*m
        self.max_power = config.get('max_power', 20000.0)  # W
        self.max_pressure = config.get('max_pressure', 1000000.0)  # Pa
        
        # Monitoring state
        self.current_level = SafetyLevel.NORMAL
        self.active_warnings = []
        self.safety_callbacks = []
        
        # Event tracking
        self.safety_events = []
        
        print("SafetyMonitor initialized")
        
    def add_safety_callback(self, callback: Callable[[SafetyLevel, str], None]) -> None:
        """Add safety callback function"""
        self.safety_callbacks.append(callback)
        
    def check_speed_safety(self, speed: float) -> SafetyLevel:
        """Check speed safety"""
        if speed > self.max_speed * 1.2:
            return SafetyLevel.EMERGENCY
        elif speed > self.max_speed:
            return SafetyLevel.CRITICAL
        elif speed > self.max_speed * 0.9:
            return SafetyLevel.WARNING
        else:
            return SafetyLevel.NORMAL
            
    def check_torque_safety(self, torque: float) -> SafetyLevel:
        """Check torque safety"""
        if torque > self.max_torque * 1.2:
            return SafetyLevel.EMERGENCY
        elif torque > self.max_torque:
            return SafetyLevel.CRITICAL
        elif torque > self.max_torque * 0.9:
            return SafetyLevel.WARNING
        else:
            return SafetyLevel.NORMAL
            
    def check_power_safety(self, power: float) -> SafetyLevel:
        """Check power safety"""
        if power > self.max_power * 1.2:
            return SafetyLevel.EMERGENCY
        elif power > self.max_power:
            return SafetyLevel.CRITICAL
        elif power > self.max_power * 0.9:
            return SafetyLevel.WARNING
        else:
            return SafetyLevel.NORMAL
            
    def check_pressure_safety(self, pressure: float) -> SafetyLevel:
        """Check pressure safety"""
        if pressure > self.max_pressure * 1.2:
            return SafetyLevel.EMERGENCY
        elif pressure > self.max_pressure:
            return SafetyLevel.CRITICAL
        elif pressure > self.max_pressure * 0.9:
            return SafetyLevel.WARNING
        else:
            return SafetyLevel.NORMAL
            
    def update_safety_status(self, system_state: Dict[str, Any]) -> SafetyLevel:
        """Update overall safety status"""
        safety_levels = []
        
        # Check speed
        if 'speed_rpm' in system_state:
            speed_level = self.check_speed_safety(system_state['speed_rpm'])
            safety_levels.append(speed_level)
            
        # Check torque
        if 'torque' in system_state:
            torque_level = self.check_torque_safety(system_state['torque'])
            safety_levels.append(torque_level)
            
        # Check power
        if 'power' in system_state:
            power_level = self.check_power_safety(system_state['power'])
            safety_levels.append(power_level)
            
        # Check pressure
        if 'pressure' in system_state:
            pressure_level = self.check_pressure_safety(system_state['pressure'])
            safety_levels.append(pressure_level)
            
        # Determine overall safety level
        if SafetyLevel.EMERGENCY in safety_levels:
            new_level = SafetyLevel.EMERGENCY
        elif SafetyLevel.CRITICAL in safety_levels:
            new_level = SafetyLevel.CRITICAL
        elif SafetyLevel.WARNING in safety_levels:
            new_level = SafetyLevel.WARNING
        else:
            new_level = SafetyLevel.NORMAL
            
        # Update level and trigger callbacks if changed
        if new_level != self.current_level:
            self._trigger_safety_change(new_level)
            
        self.current_level = new_level
        return new_level
        
    def _trigger_safety_change(self, new_level: SafetyLevel) -> None:
        """Trigger safety level change callbacks"""
        old_level = self.current_level
        self.current_level = new_level
        
        # Log safety event
        event = {
            'time': 0.0,  # Will be set by caller
            'old_level': old_level.value,
            'new_level': new_level.value
        }
        self.safety_events.append(event)
        
        # Call safety callbacks
        for callback in self.safety_callbacks:
            try:
                callback(new_level, f"Safety level changed from {old_level.value} to {new_level.value}")
            except Exception as e:
                print(f"Safety callback error: {e}")
                
    def get_safety_status(self) -> Dict[str, Any]:
        """Get current safety status"""
        return {
            'current_level': self.current_level.value,
            'active_warnings': self.active_warnings,
            'event_count': len(self.safety_events),
            'max_speed': self.max_speed,
            'max_torque': self.max_torque,
            'max_power': self.max_power,
            'max_pressure': self.max_pressure
        }
        
    def get_recent_safety_events(self, count: int = 10) -> List[Dict[str, Any]]:
        """Get recent safety events"""
        return self.safety_events[-count:] if self.safety_events else []
