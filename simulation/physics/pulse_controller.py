"""
H3 Pulse Control Implementation  
Implements pulse-and-coast operation with clutch control.

This module implements Hypothesis 3: pulse-and-coast operation where the generator
load is cyclically engaged/disengaged to optimize energy extraction efficiency.
"""

import math
import logging
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class PulsePhase(Enum):
    """Current phase of pulse operation"""
    COAST = "coast"  # Clutch disengaged, free spinning
    PULSE = "pulse"  # Clutch engaged, generator load applied

@dataclass
class PulseState:
    """Current pulse control state"""
    enabled: bool = False
    phase: PulsePhase = PulsePhase.COAST
    clutch_engaged: bool = False
    time_in_phase: float = 0.0  # Time in current phase (s)
    phase_duration: float = 2.0  # Duration of current phase (s)
    pulse_duty_cycle: float = 0.5  # Fraction of time in pulse phase
    generator_load_factor: float = 0.0  # Current load factor (0-1)
    energy_accumulated: float = 0.0  # Energy accumulated during coast (J)
    avg_power_output: float = 0.0  # Average power output (W)

class PulseController:
    """
    Manages H3 pulse-and-coast operation for KPP system.
    
    Controls clutch engagement/disengagement to optimize energy extraction
    by allowing the system to accumulate kinetic energy during coast phases
    and extract it efficiently during pulse phases.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize pulse controller.
        
        Args:
            config (dict): Configuration parameters
        """
        if config is None:
            config = {}
        
        # H3 pulse parameters
        self.h3_enabled = config.get('h3_enabled', False)
        self.pulse_interval = config.get('pulse_interval', 4.0)  # Total cycle time (s)
        self.duty_cycle = config.get('pulse_duty_cycle', 0.5)  # Pulse fraction (0-1)
        self.coast_duration = self.pulse_interval * (1 - self.duty_cycle)
        self.pulse_duration = self.pulse_interval * self.duty_cycle
        
        # Clutch parameters
        self.clutch_engagement_time = config.get('clutch_engagement_time', 0.2)  # s
        self.clutch_efficiency = config.get('clutch_efficiency', 0.95)  # 95% efficient
        self.clutch_inertia = config.get('clutch_inertia', 2.0)  # kg⋅m²
        
        # Generator load control
        self.max_generator_load = config.get('max_generator_load', 1000.0)  # N⋅m
        self.load_ramp_rate = config.get('load_ramp_rate', 2000.0)  # N⋅m/s
        self.optimal_rpm = config.get('optimal_generator_rpm', 375.0)  # RPM
        
        # System inertia for energy calculations
        self.flywheel_inertia = config.get('flywheel_inertia', 50.0)  # kg⋅m²
        self.system_inertia = config.get('system_inertia', 100.0)  # kg⋅m² total
        
        # Performance optimization
        self.adaptive_timing = config.get('adaptive_timing', True)
        self.efficiency_threshold = config.get('efficiency_threshold', 0.6)  # 60%
        self.timing_adjustment_factor = config.get('timing_adjustment', 0.1)
        
        # Current state
        self.state = PulseState()
        self.state.phase_duration = self.coast_duration
        self.cycle_start_time = 0.0
        self.last_efficiency = 0.0
        
        logger.info(f"Pulse controller initialized - H3 enabled: {self.h3_enabled}, "
                   f"interval: {self.pulse_interval:.1f}s, duty cycle: {self.duty_cycle:.1%}")
    
    def update(self, current_time: float, system_speed: float, 
              generator_torque: float, dt: float) -> PulseState:
        """
        Update pulse control state.
        
        Args:
            current_time (float): Current simulation time (s)
            system_speed (float): Current system angular velocity (rad/s)
            generator_torque (float): Current generator torque (N⋅m)
            dt (float): Time step (s)
            
        Returns:
            PulseState: Updated pulse state
        """
        if not self.h3_enabled:
            self.state.enabled = False
            self.state.clutch_engaged = True  # Normal continuous operation
            self.state.generator_load_factor = 1.0
            return self.state
        
        self.state.enabled = True
        self.state.time_in_phase += dt
        
        # Check for phase transition
        if self.state.time_in_phase >= self.state.phase_duration:
            self._transition_phase(current_time, system_speed)
        
        # Update clutch and generator load based on current phase
        self._update_clutch_and_load(system_speed, generator_torque, dt)
        
        # Update performance metrics
        self._update_performance_metrics(system_speed, generator_torque, dt)
        
        # Adaptive timing adjustment if enabled
        if self.adaptive_timing:
            self._adapt_timing()
        
        logger.debug(f"Pulse state: phase={self.state.phase.value}, "
                    f"time_in_phase={self.state.time_in_phase:.1f}s, "
                    f"clutch_engaged={self.state.clutch_engaged}, "
                    f"load_factor={self.state.generator_load_factor:.2f}")
        
        return self.state
    
    def _transition_phase(self, current_time: float, system_speed: float):
        """
        Transition between pulse and coast phases.
        
        Args:
            current_time (float): Current time (s)
            system_speed (float): System speed (rad/s)
        """
        old_phase = self.state.phase
        
        if self.state.phase == PulsePhase.COAST:
            # Transition to pulse phase
            self.state.phase = PulsePhase.PULSE
            self.state.phase_duration = self.pulse_duration
            self.state.clutch_engaged = True
            
            # Calculate energy accumulated during coast
            kinetic_energy = 0.5 * self.system_inertia * system_speed**2
            self.state.energy_accumulated = kinetic_energy
            
            logger.info(f"t={current_time:.1f}s: Transition COAST → PULSE, "
                       f"accumulated energy: {kinetic_energy:.1f} J, "
                       f"system speed: {system_speed:.2f} rad/s")
        else:
            # Transition to coast phase
            self.state.phase = PulsePhase.COAST
            self.state.phase_duration = self.coast_duration
            self.state.clutch_engaged = False
            
            logger.info(f"t={current_time:.1f}s: Transition PULSE → COAST, "
                       f"system speed: {system_speed:.2f} rad/s")
        
        self.state.time_in_phase = 0.0
    
    def _update_clutch_and_load(self, system_speed: float, generator_torque: float, dt: float):
        """
        Update clutch engagement and generator load based on current phase.
        
        Args:
            system_speed (float): System speed (rad/s)
            generator_torque (float): Current generator torque (N⋅m)
            dt (float): Time step (s)
        """
        if self.state.phase == PulsePhase.COAST:
            # Coast phase: clutch disengaged, no generator load
            self.state.clutch_engaged = False
            self.state.generator_load_factor = 0.0
            
        elif self.state.phase == PulsePhase.PULSE:
            # Pulse phase: clutch engaged, variable generator load
            self.state.clutch_engaged = True
            
            # Ramp up load factor during early pulse phase
            if self.state.time_in_phase < self.clutch_engagement_time:
                ramp_progress = self.state.time_in_phase / self.clutch_engagement_time
                self.state.generator_load_factor = ramp_progress
            else:
                # Optimize load based on speed
                optimal_speed_rpm = self.optimal_rpm * 2 * math.pi / 60  # Convert to rad/s
                current_speed_rpm = system_speed * 60 / (2 * math.pi)
                
                # Load factor based on speed ratio
                if system_speed > 0.1:  # Avoid division by zero
                    speed_ratio = current_speed_rpm / self.optimal_rpm
                    
                    # Optimal loading curve (peak at optimal speed)
                    if speed_ratio < 1.0:
                        self.state.generator_load_factor = speed_ratio
                    else:
                        # Reduce load above optimal speed to prevent over-braking
                        self.state.generator_load_factor = 1.0 / (1 + 0.5 * (speed_ratio - 1))
                else:
                    self.state.generator_load_factor = 0.1  # Minimum load
                
                # Limit load factor
                self.state.generator_load_factor = max(0.1, min(self.state.generator_load_factor, 1.0))
    
    def _update_performance_metrics(self, system_speed: float, generator_torque: float, dt: float):
        """
        Update performance tracking metrics.
        
        Args:
            system_speed (float): System speed (rad/s)
            generator_torque (float): Generator torque (N⋅m)
            dt (float): Time step (s)
        """
        # Calculate instantaneous power output
        if self.state.clutch_engaged:
            instantaneous_power = generator_torque * system_speed * self.state.generator_load_factor
        else:
            instantaneous_power = 0.0
        
        # Update average power (exponential moving average)
        alpha = dt / max(self.pulse_interval, dt)  # Time constant = pulse interval
        self.state.avg_power_output = (1 - alpha) * self.state.avg_power_output + alpha * instantaneous_power
    
    def _adapt_timing(self):
        """
        Adapt pulse timing based on system performance.
        """
        if self.state.avg_power_output <= 0:
            return
        
        # Calculate efficiency estimate (simplified)
        theoretical_power = self.max_generator_load * self.optimal_rpm * 2 * math.pi / 60
        current_efficiency = self.state.avg_power_output / theoretical_power if theoretical_power > 0 else 0
        
        # Adjust timing if efficiency is below threshold
        if current_efficiency < self.efficiency_threshold:
            if current_efficiency > self.last_efficiency:
                # Improving - continue current direction
                pass
            else:
                # Getting worse - adjust duty cycle
                if self.duty_cycle > 0.3:
                    self.duty_cycle -= self.timing_adjustment_factor * 0.05
                else:
                    self.duty_cycle += self.timing_adjustment_factor * 0.05
                
                # Update phase durations
                self.coast_duration = self.pulse_interval * (1 - self.duty_cycle)
                self.pulse_duration = self.pulse_interval * self.duty_cycle
                
                logger.debug(f"Adapted pulse timing: duty_cycle={self.duty_cycle:.2f}, "
                           f"efficiency={current_efficiency:.1%}")
        
        self.last_efficiency = current_efficiency
    
    def get_generator_load_torque(self, base_torque: float) -> float:
        """
        Calculate effective generator load torque based on pulse state.
        
        Args:
            base_torque (float): Base generator torque (N⋅m)
            
        Returns:
            float: Effective generator torque (N⋅m)
        """
        if not self.state.enabled or not self.state.clutch_engaged:
            return 0.0
        
        effective_torque = base_torque * self.state.generator_load_factor * self.clutch_efficiency
        
        return min(effective_torque, self.max_generator_load)
    
    def calculate_energy_efficiency(self, input_energy: float, time_period: float) -> float:
        """
        Calculate pulse-and-coast energy efficiency.
        
        Args:
            input_energy (float): Input energy over time period (J)
            time_period (float): Time period (s)
            
        Returns:
            float: Energy efficiency (0-1)
        """
        if input_energy <= 0 or time_period <= 0:
            return 0.0
        
        # Output energy is average power times time
        output_energy = self.state.avg_power_output * time_period
        
        efficiency = output_energy / input_energy
        
        return max(0.0, min(efficiency, 1.0))
    
    def get_system_status(self) -> Dict[str, Any]:
        """
        Get current pulse control system status.
        
        Returns:
            dict: System status information
        """
        return {
            'h3_enabled': self.h3_enabled,
            'pulse_interval': self.pulse_interval,
            'duty_cycle': self.duty_cycle,
            'current_phase': self.state.phase.value,
            'time_in_phase': self.state.time_in_phase,
            'clutch_engaged': self.state.clutch_engaged,
            'generator_load_factor': self.state.generator_load_factor,
            'avg_power_output': self.state.avg_power_output,
            'energy_accumulated': self.state.energy_accumulated,
            'adaptive_timing': self.adaptive_timing
        }
    
    def set_h3_enabled(self, enabled: bool):
        """
        Enable or disable H3 pulse control.
        
        Args:
            enabled (bool): Whether to enable H3 pulse control
        """
        self.h3_enabled = enabled
        if not enabled:
            # Reset to continuous operation
            self.state.clutch_engaged = True
            self.state.generator_load_factor = 1.0
            self.state.phase = PulsePhase.PULSE
        
        logger.info(f"H3 pulse control {'enabled' if enabled else 'disabled'}")
    
    def update_parameters(self, params: Dict[str, Any]):
        """
        Update pulse control parameters.
        
        Args:
            params (dict): Parameter updates
        """
        if 'h3_enabled' in params:
            self.h3_enabled = bool(params['h3_enabled'])
        
        if 'pulse_interval' in params:
            self.pulse_interval = max(1.0, min(params['pulse_interval'], 20.0))
        
        if 'pulse_duty_cycle' in params:
            self.duty_cycle = max(0.2, min(params['pulse_duty_cycle'], 0.8))
        
        # Recalculate durations
        self.coast_duration = self.pulse_interval * (1 - self.duty_cycle)
        self.pulse_duration = self.pulse_interval * self.duty_cycle
        
        logger.info(f"Pulse parameters updated: enabled={self.h3_enabled}, "
                   f"interval={self.pulse_interval:.1f}s, duty_cycle={self.duty_cycle:.1%}")
    
    def reset_cycle(self):
        """Reset pulse cycle to beginning of coast phase."""
        self.state.phase = PulsePhase.COAST
        self.state.time_in_phase = 0.0
        self.state.phase_duration = self.coast_duration
        self.state.clutch_engaged = False
        self.state.generator_load_factor = 0.0
        self.cycle_start_time = 0.0
        
        logger.info("Pulse cycle reset to coast phase")
    
    def get_current_phase(self) -> str:
        """
        Get the current pulse phase.
        
        Returns:
            str: Current phase ('pulse' or 'coast')
        """
        return self.state.phase.value
