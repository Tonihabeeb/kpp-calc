"""
Phase 1.2: Pressure Control System for KPP Pneumatic System

This module implements the pressure control and monitoring system that manages
the air compressor operation to maintain optimal tank pressure.

Key Features:
- Hysteresis-based pressure control
- Pressure monitoring and safety systems
- Energy-efficient compressor cycling
- Configurable pressure setpoints and safety margins
"""

import logging
from typing import Dict, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
from utils.logging_setup import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

class CompressorState(Enum):
    """Compressor operating states."""
    OFF = "off"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    FAULT = "fault"

class SafetyLevel(Enum):
    """System safety levels."""
    NORMAL = "normal"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"

@dataclass
class PressureControlSettings:
    """Pressure control system settings."""
    target_pressure: float = 250000.0  # Pa (2.5 atm)
    high_pressure_setpoint: float = 270000.0  # Pa (turn off compressor)
    low_pressure_setpoint: float = 200000.0  # Pa (turn on compressor)
    critical_low_pressure: float = 150000.0  # Pa (system warning)
    emergency_high_pressure: float = 320000.0  # Pa (emergency shutdown)
    pressure_hysteresis: float = 20000.0  # Pa (hysteresis band)
    max_pressure_rate: float = 50000.0  # Pa/s (maximum allowed pressure rise rate)
    min_cycle_time: float = 30.0  # seconds (minimum compressor cycle time)

class PressureControlSystem:
    """
    Comprehensive pressure control system with safety monitoring.
    
    This system implements:
    - Hysteresis-based pressure control
    - Safety monitoring and shutdown procedures
    - Energy-efficient compressor cycling
    - Pressure rate limiting and monitoring
    """
    
    def __init__(self, 
                 control_settings: Optional[PressureControlSettings] = None,
                 air_compressor=None):
        """
        Initialize the pressure control system.
        
        Args:
            control_settings: Pressure control settings
            air_compressor: AirCompressionSystem instance to control
        """
        self.settings = control_settings or PressureControlSettings()
        self.air_compressor = air_compressor
          # Control state
        self.compressor_state = CompressorState.OFF
        self.safety_level = SafetyLevel.NORMAL
        self.last_start_time = 0.0
        self.last_stop_time = -self.settings.min_cycle_time  # Allow immediate start on first run
        self.cycle_count = 0
        
        # Pressure monitoring
        self.pressure_history = []
        self.max_history_length = 100
        self.last_pressure = 0.0
        self.pressure_rate = 0.0
        
        # Safety and fault tracking
        self.fault_conditions = set()
        self.safety_warnings = set()
        self.emergency_stop_active = False
        self.manual_override = False
        
        # Performance tracking
        self.total_runtime = 0.0
        self.total_cycles = 0
        self.pressure_violations = 0
        
        logger.info(f"PressureControlSystem initialized: target={self.settings.target_pressure/1000:.1f} kPa")
    
    def set_air_compressor(self, air_compressor) -> None:
        """Set the air compressor system to control."""
        self.air_compressor = air_compressor
        logger.info("Air compressor system connected to pressure controller")
    
    def update_pressure_history(self, current_pressure: float, dt: float) -> None:
        """Update pressure history and calculate pressure rate."""
        self.pressure_history.append(current_pressure)
        
        # Limit history length
        if len(self.pressure_history) > self.max_history_length:
            self.pressure_history.pop(0)
        
        # Calculate pressure rate
        if self.last_pressure > 0 and dt > 0:
            self.pressure_rate = (current_pressure - self.last_pressure) / dt
        
        self.last_pressure = current_pressure
    
    def check_safety_conditions(self, current_pressure: float) -> SafetyLevel:
        """
        Check safety conditions and update safety level.
        
        Args:
            current_pressure: Current tank pressure in Pa
            
        Returns:
            Current safety level
        """
        self.safety_warnings.clear()
        
        # Check for emergency conditions
        if current_pressure >= self.settings.emergency_high_pressure:
            self.safety_warnings.add("EMERGENCY_HIGH_PRESSURE")
            return SafetyLevel.EMERGENCY
        
        # Check for critical conditions
        if current_pressure <= self.settings.critical_low_pressure:
            self.safety_warnings.add("CRITICAL_LOW_PRESSURE")
            return SafetyLevel.CRITICAL
        
        # Check pressure rate
        if abs(self.pressure_rate) > self.settings.max_pressure_rate:
            self.safety_warnings.add("EXCESSIVE_PRESSURE_RATE")
            return SafetyLevel.WARNING
          # Check for compressor faults
        if self.air_compressor and hasattr(self.air_compressor, 'fault_detected'):
            if self.air_compressor.fault_detected:
                self.safety_warnings.add("COMPRESSOR_FAULT")
                return SafetyLevel.WARNING
        
        return SafetyLevel.NORMAL
    
    def should_start_compressor(self, current_pressure: float, current_time: float) -> bool:
        """
        Determine if compressor should start.
        
        Args:
            current_pressure: Current tank pressure in Pa
            current_time: Current simulation time in seconds
            
        Returns:
            True if compressor should start
        """
        # Check basic pressure conditions
        if current_pressure >= self.settings.low_pressure_setpoint:
            return False
        
        # Check safety conditions - only EMERGENCY stops compressor start
        # CRITICAL low pressure should actually trigger compressor start!
        if self.safety_level == SafetyLevel.EMERGENCY:
            return False
        
        # Check minimum cycle time
        time_since_last_stop = current_time - self.last_stop_time
        if time_since_last_stop < self.settings.min_cycle_time:
            return False
        
        # Check for manual override
        if self.manual_override:
            return False
        
        # Check emergency stop
        if self.emergency_stop_active:
            return False
        
        return True
    
    def should_stop_compressor(self, current_pressure: float, current_time: float) -> bool:
        """
        Determine if compressor should stop.
        
        Args:
            current_pressure: Current tank pressure in Pa
            current_time: Current simulation time in seconds
            
        Returns:
            True if compressor should stop
        """
        # Emergency conditions
        if self.safety_level == SafetyLevel.EMERGENCY:
            return True
        
        # Emergency stop
        if self.emergency_stop_active:
            return True
        
        # Target pressure reached
        if current_pressure >= self.settings.high_pressure_setpoint:
            return True
        
        # Manual override
        if self.manual_override:
            return True
        
        return False
    
    def update_compressor_state(self, current_time: float) -> CompressorState:
        """
        Update compressor state based on current conditions.
        
        Args:
            current_time: Current simulation time in seconds
            
        Returns:
            New compressor state
        """
        if not self.air_compressor:
            return CompressorState.FAULT
        
        current_pressure = self.air_compressor.tank_pressure
        
        # Update safety conditions
        self.safety_level = self.check_safety_conditions(current_pressure)
        
        # State machine logic
        if self.compressor_state == CompressorState.OFF:
            if self.should_start_compressor(current_pressure, current_time):
                self.compressor_state = CompressorState.STARTING
                self.last_start_time = current_time
                self.cycle_count += 1
                logger.info(f"Starting compressor cycle #{self.cycle_count}: "
                           f"pressure={current_pressure/1000:.1f} kPa")
        
        elif self.compressor_state == CompressorState.STARTING:
            # Transition to running (could add startup delay here)
            self.compressor_state = CompressorState.RUNNING
        
        elif self.compressor_state == CompressorState.RUNNING:
            if self.should_stop_compressor(current_pressure, current_time):
                self.compressor_state = CompressorState.STOPPING
                self.last_stop_time = current_time
                runtime = current_time - self.last_start_time
                self.total_runtime += runtime
                logger.info(f"Stopping compressor: pressure={current_pressure/1000:.1f} kPa, "
                           f"runtime={runtime:.1f}s")
        
        elif self.compressor_state == CompressorState.STOPPING:
            # Transition to off (could add shutdown delay here)
            self.compressor_state = CompressorState.OFF
        
        elif self.compressor_state == CompressorState.FAULT:
            # Remain in fault until manually reset
            pass
        
        return self.compressor_state
    
    def control_step(self, dt: float, current_time: float) -> Dict[str, Any]:
        """
        Execute one control step.
        
        Args:
            dt: Time step in seconds
            current_time: Current simulation time in seconds
            
        Returns:
            Control step results
        """
        if not self.air_compressor:
            return {'error': 'No air compressor connected'}
        
        current_pressure = self.air_compressor.tank_pressure
        
        # Update pressure monitoring
        self.update_pressure_history(current_pressure, dt)
        
        # Update compressor state
        new_state = self.update_compressor_state(current_time)
          # Control compressor operation
        compressor_results = {}
        if new_state == CompressorState.RUNNING:
            # Run compressor to high pressure setpoint for proper hysteresis control
            compressor_results = self.air_compressor.run_compressor(dt, self.settings.high_pressure_setpoint)
        else:
            # Compressor off
            compressor_results = {
                'running': False,
                'power_consumed': 0.0,
                'air_compressed': 0.0,
                'work_done': 0.0,
                'heat_generated': 0.0,
                'tank_pressure': current_pressure
            }
        
        # Check for pressure violations
        if current_pressure > self.settings.emergency_high_pressure or \
           current_pressure < self.settings.critical_low_pressure:
            self.pressure_violations += 1
        
        return {
            'compressor_state': new_state.value,
            'safety_level': self.safety_level.value,
            'tank_pressure': current_pressure,
            'pressure_rate': self.pressure_rate,
            'target_pressure': self.settings.target_pressure,
            'cycle_count': self.cycle_count,
            'total_runtime': self.total_runtime,
            'safety_warnings': list(self.safety_warnings),
            'compressor_results': compressor_results
        }
    
    def emergency_stop(self) -> None:
        """Activate emergency stop."""
        self.emergency_stop_active = True
        self.compressor_state = CompressorState.OFF
        logger.warning("EMERGENCY STOP ACTIVATED")
    
    def reset_emergency_stop(self) -> None:
        """Reset emergency stop."""
        self.emergency_stop_active = False
        logger.info("Emergency stop reset")
    
    def set_manual_override(self, override: bool) -> None:
        """Set manual override state."""
        self.manual_override = override
        if override:
            self.compressor_state = CompressorState.OFF
        logger.info(f"Manual override {'activated' if override else 'deactivated'}")
    
    def update_target_pressure(self, new_target: float) -> None:
        """
        Update target pressure and recalculate setpoints.
        
        Args:
            new_target: New target pressure in Pa
        """
        self.settings.target_pressure = new_target
        # Automatically adjust setpoints
        self.settings.high_pressure_setpoint = new_target + self.settings.pressure_hysteresis
        self.settings.low_pressure_setpoint = new_target - self.settings.pressure_hysteresis
        
        logger.info(f"Target pressure updated to {new_target/1000:.1f} kPa")
    
    def get_control_status(self) -> Dict[str, Any]:
        """Get comprehensive control system status."""
        current_pressure = self.air_compressor.tank_pressure if self.air_compressor else 0.0
        
        return {
            'compressor_state': self.compressor_state.value,
            'safety_level': self.safety_level.value,
            'current_pressure_pa': current_pressure,
            'current_pressure_bar': current_pressure / 100000.0,
            'target_pressure_pa': self.settings.target_pressure,
            'target_pressure_bar': self.settings.target_pressure / 100000.0,
            'pressure_rate_pa_per_sec': self.pressure_rate,
            'cycle_count': self.cycle_count,
            'total_runtime_hours': self.total_runtime / 3600.0,
            'pressure_violations': self.pressure_violations,
            'emergency_stop_active': self.emergency_stop_active,
            'manual_override': self.manual_override,
            'safety_warnings': list(self.safety_warnings),
            'high_setpoint_pa': self.settings.high_pressure_setpoint,
            'low_setpoint_pa': self.settings.low_pressure_setpoint,
            'pressure_ok_for_injection': current_pressure >= self.settings.low_pressure_setpoint
        }
    
    def calculate_efficiency_metrics(self) -> Dict[str, float]:
        """Calculate control system efficiency metrics."""
        if self.total_runtime == 0:
            return {'duty_cycle': 0.0, 'avg_cycle_time': 0.0}
        
        total_time = self.total_runtime + (self.cycle_count * self.settings.min_cycle_time)
        duty_cycle = self.total_runtime / total_time if total_time > 0 else 0.0
        avg_cycle_time = self.total_runtime / self.cycle_count if self.cycle_count > 0 else 0.0
        
        return {
            'duty_cycle': duty_cycle,
            'avg_cycle_time': avg_cycle_time,
            'cycles_per_hour': self.cycle_count / (total_time / 3600.0) if total_time > 0 else 0.0
        }
    
    def reset_control_system(self) -> None:
        """Reset control system to initial state."""
        self.compressor_state = CompressorState.OFF
        self.safety_level = SafetyLevel.NORMAL
        self.last_start_time = 0.0
        self.last_stop_time = 0.0
        self.cycle_count = 0
        self.pressure_history.clear()
        self.last_pressure = 0.0
        self.pressure_rate = 0.0
        self.fault_conditions.clear()
        self.safety_warnings.clear()
        self.emergency_stop_active = False
        self.manual_override = False
        self.total_runtime = 0.0
        self.total_cycles = 0
        self.pressure_violations = 0
        
        logger.info("Pressure control system reset")


def create_standard_kpp_pressure_controller(target_pressure_bar: float = 2.5) -> PressureControlSystem:
    """
    Create a standard KPP pressure control system.
    
    Args:
        target_pressure_bar: Target pressure in bar
        
    Returns:
        Configured pressure control system
    """
    target_pa = target_pressure_bar * 100000.0
    
    settings = PressureControlSettings(
        target_pressure=target_pa,
        high_pressure_setpoint=target_pa + 20000.0,  # +0.2 bar
        low_pressure_setpoint=target_pa - 20000.0,   # -0.2 bar
        critical_low_pressure=target_pa - 50000.0,   # -0.5 bar
        emergency_high_pressure=target_pa + 70000.0, # +0.7 bar
        pressure_hysteresis=20000.0,  # 0.2 bar
        max_pressure_rate=50000.0,    # 0.5 bar/s
        min_cycle_time=30.0           # 30 seconds
    )
    
    return PressureControlSystem(settings)
