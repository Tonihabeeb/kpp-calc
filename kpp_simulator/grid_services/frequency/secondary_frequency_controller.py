"""
Secondary Frequency Controller for KPP Simulator
Implements secondary frequency control with AGC integration
"""

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
from datetime import datetime, timedelta

from ...core.physics_engine import PhysicsEngine
from ...electrical.electrical_system import IntegratedElectricalSystem
from ...control_systems.control_system import IntegratedControlSystem


class AGCStatus(Enum):
    """AGC status states"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    MAINTENANCE = "maintenance"


class RegulationMode(Enum):
    """Regulation modes"""
    REGULATION_UP = "regulation_up"
    REGULATION_DOWN = "regulation_down"
    NEUTRAL = "neutral"


@dataclass
class AGCSignal:
    """AGC signal data"""
    timestamp: datetime
    signal_value: float
    signal_type: str
    priority: int
    source: str
    quality: float


@dataclass
class RegulationAction:
    """Regulation action data"""
    timestamp: datetime
    power_adjustment: float
    regulation_mode: RegulationMode
    response_time: float
    accuracy: float
    agc_signal: Optional[AGCSignal] = None


@dataclass
class RegulationPerformance:
    """Regulation performance metrics"""
    regulation_up_capacity: float
    regulation_down_capacity: float
    response_time: float
    accuracy: float
    availability: float
    ramp_rate: float
    total_regulation_energy: float


class SecondaryFrequencyController:
    """
    Secondary Frequency Controller for AGC and regulation services
    
    Features:
    - AGC signal processing and integration
    - Bidirectional power adjustment
    - Regulation service management
    - Ramp rate limiting and accuracy requirements
    - Performance monitoring and optimization
    """
    
    def __init__(self, 
                 physics_engine: PhysicsEngine,
                 electrical_system: IntegratedElectricalSystem,
                 control_system: IntegratedControlSystem):
        """
        Initialize the Secondary Frequency Controller
        
        Args:
            physics_engine: Core physics engine
            electrical_system: Integrated electrical system
            control_system: Integrated control system
        """
        self.physics_engine = physics_engine
        self.electrical_system = electrical_system
        self.control_system = control_system
        
        # Control state
        self.is_active = False
        self.agc_status = AGCStatus.INACTIVE
        self.current_regulation_mode = RegulationMode.NEUTRAL
        
        # AGC parameters
        self.agc_signal_history: List[AGCSignal] = []
        self.current_agc_signal: Optional[AGCSignal] = None
        self.agc_response_time = 1.0  # seconds
        self.agc_accuracy_target = 0.95
        
        # Regulation parameters
        self.regulation_up_capacity = 200.0  # kW
        self.regulation_down_capacity = 200.0  # kW
        self.ramp_rate_limit = 50.0  # kW/min
        self.regulation_accuracy = 0.02  # 2% accuracy
        
        # Performance tracking
        self.regulation_history: List[RegulationAction] = []
        self.regulation_performance = RegulationPerformance(
            regulation_up_capacity=self.regulation_up_capacity,
            regulation_down_capacity=self.regulation_down_capacity,
            response_time=0.0,
            accuracy=0.0,
            availability=1.0,
            ramp_rate=0.0,
            total_regulation_energy=0.0
        )
        
        # Control parameters
        self.current_power_adjustment = 0.0
        self.target_power_adjustment = 0.0
        self.last_regulation_time = 0.0
        
        # PID controller for regulation
        self.pid_kp = 50.0
        self.pid_ki = 5.0
        self.pid_kd = 2.0
        self.pid_integral = 0.0
        self.pid_previous_error = 0.0
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        self.logger.info("Secondary Frequency Controller initialized")
    
    def start(self):
        """Start the secondary frequency controller"""
        self.is_active = True
        self.agc_status = AGCStatus.ACTIVE
        self.logger.info("Secondary Frequency Controller started")
    
    def stop(self):
        """Stop the secondary frequency controller"""
        self.is_active = False
        self.agc_status = AGCStatus.INACTIVE
        self.current_regulation_mode = RegulationMode.NEUTRAL
        self.logger.info("Secondary Frequency Controller stopped")
    
    def update(self, dt: float):
        """
        Update the secondary frequency controller
        
        Args:
            dt: Time step in seconds
        """
        if not self.is_active:
            return
        
        # Process AGC signals
        self._process_agc_signals()
        
        # Execute regulation if AGC signal is active
        if self.current_agc_signal and self.agc_status == AGCStatus.ACTIVE:
            self._execute_regulation(dt)
        else:
            self._recover_to_neutral(dt)
        
        # Update performance metrics
        self._update_performance_metrics(dt)
    
    def receive_agc_signal(self, signal_value: float, signal_type: str = "regulation", 
                          priority: int = 1, source: str = "control_center") -> str:
        """
        Receive AGC signal from control center
        
        Args:
            signal_value: AGC signal value (-1 to 1)
            signal_type: Type of AGC signal
            priority: Signal priority
            source: Signal source
            
        Returns:
            Signal ID
        """
        signal_id = f"agc_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        
        agc_signal = AGCSignal(
            timestamp=datetime.now(),
            signal_value=signal_value,
            signal_type=signal_type,
            priority=priority,
            source=source,
            quality=0.98  # Simulated quality
        )
        
        self.agc_signal_history.append(agc_signal)
        self.current_agc_signal = agc_signal
        
        # Limit history size
        if len(self.agc_signal_history) > 1000:
            self.agc_signal_history.pop(0)
        
        self.logger.info(f"AGC signal received: {signal_value:.3f} - {signal_type}")
        
        return signal_id
    
    def _process_agc_signals(self):
        """Process AGC signals and determine regulation requirements"""
        if not self.current_agc_signal:
            return
        
        # Check signal age
        signal_age = (datetime.now() - self.current_agc_signal.timestamp).total_seconds()
        if signal_age > 30.0:  # 30 second timeout
            self.current_agc_signal = None
            return
        
        # Determine regulation mode based on signal value
        signal_value = self.current_agc_signal.signal_value
        
        if signal_value > 0.01:  # Dead band
            self.current_regulation_mode = RegulationMode.REGULATION_UP
            self.target_power_adjustment = signal_value * self.regulation_up_capacity
        elif signal_value < -0.01:
            self.current_regulation_mode = RegulationMode.REGULATION_DOWN
            self.target_power_adjustment = signal_value * self.regulation_down_capacity
        else:
            self.current_regulation_mode = RegulationMode.NEUTRAL
            self.target_power_adjustment = 0.0
    
    def _execute_regulation(self, dt: float):
        """Execute regulation based on AGC signal"""
        # Apply ramp rate limiting
        max_adjustment = self.ramp_rate_limit * dt / 60.0  # Convert to per-second rate
        
        if abs(self.target_power_adjustment - self.current_power_adjustment) > max_adjustment:
            if self.target_power_adjustment > self.current_power_adjustment:
                self.current_power_adjustment += max_adjustment
            else:
                self.current_power_adjustment -= max_adjustment
        else:
            # Apply PID control for smooth regulation
            self.current_power_adjustment = self._apply_pid_control(self.target_power_adjustment, dt)
        
        # Apply power adjustment
        self._apply_power_adjustment(self.current_power_adjustment)
        
        # Record regulation action
        self._record_regulation_action()
        
        self.logger.debug(f"Regulation: {self.current_regulation_mode.value} - {self.current_power_adjustment:.2f} kW")
    
    def _apply_pid_control(self, target_power: float, dt: float) -> float:
        """Apply PID control for smooth regulation"""
        error = target_power - self.current_power_adjustment
        
        # Proportional term
        p_term = self.pid_kp * error
        
        # Integral term
        self.pid_integral += error * dt
        i_term = self.pid_ki * self.pid_integral
        
        # Derivative term
        d_term = self.pid_kd * (error - self.pid_previous_error) / dt
        self.pid_previous_error = error
        
        # Calculate output
        output = p_term + i_term + d_term
        
        return output
    
    def _apply_power_adjustment(self, power_adjustment: float):
        """Apply power adjustment to the system"""
        # Notify electrical system of power adjustment
        # This would interface with the electrical system to adjust power output
        self.logger.debug(f"Applied regulation adjustment: {power_adjustment:.2f} kW")
    
    def _recover_to_neutral(self, dt: float):
        """Recover to neutral regulation when no AGC signal"""
        if self.current_regulation_mode != RegulationMode.NEUTRAL:
            # Gradually reduce power adjustment
            recovery_rate = 20.0  # kW/s
            reduction = recovery_rate * dt
            
            if self.current_power_adjustment > 0:
                self.current_power_adjustment = max(0, self.current_power_adjustment - reduction)
            else:
                self.current_power_adjustment = min(0, self.current_power_adjustment + reduction)
            
            if abs(self.current_power_adjustment) < 1.0:
                self.current_power_adjustment = 0.0
                self.current_regulation_mode = RegulationMode.NEUTRAL
                self.pid_integral = 0.0  # Reset integral term
    
    def _record_regulation_action(self):
        """Record regulation action"""
        action = RegulationAction(
            timestamp=datetime.now(),
            power_adjustment=self.current_power_adjustment,
            regulation_mode=self.current_regulation_mode,
            response_time=self.agc_response_time,
            accuracy=self.regulation_accuracy,
            agc_signal=self.current_agc_signal
        )
        
        self.regulation_history.append(action)
        
        # Limit history size
        if len(self.regulation_history) > 1000:
            self.regulation_history.pop(0)
    
    def _update_performance_metrics(self, dt: float):
        """Update performance metrics"""
        # Update regulation energy
        self.regulation_performance.total_regulation_energy += abs(self.current_power_adjustment) * dt / 3600  # kWh
        
        # Calculate average response time
        if len(self.regulation_history) > 0:
            response_times = [action.response_time for action in self.regulation_history[-100:]]
            self.regulation_performance.response_time = np.mean(response_times)
        
        # Calculate accuracy
        if len(self.regulation_history) > 0:
            accuracies = [action.accuracy for action in self.regulation_history[-100:]]
            self.regulation_performance.accuracy = np.mean(accuracies)
        
        # Calculate ramp rate
        if len(self.regulation_history) > 1:
            recent_actions = self.regulation_history[-10:]
            if len(recent_actions) >= 2:
                time_diff = (recent_actions[-1].timestamp - recent_actions[0].timestamp).total_seconds() / 60.0  # minutes
                power_diff = abs(recent_actions[-1].power_adjustment - recent_actions[0].power_adjustment)
                if time_diff > 0:
                    self.regulation_performance.ramp_rate = power_diff / time_diff
        
        # Calculate availability
        if len(self.regulation_history) > 0:
            recent_actions = self.regulation_history[-100:]
            active_actions = [a for a in recent_actions if a.regulation_mode != RegulationMode.NEUTRAL]
            self.regulation_performance.availability = len(active_actions) / len(recent_actions)
    
    def set_regulation_capacity(self, regulation_up: float, regulation_down: float):
        """Set regulation capacity"""
        self.regulation_up_capacity = regulation_up
        self.regulation_down_capacity = regulation_down
        self.regulation_performance.regulation_up_capacity = regulation_up
        self.regulation_performance.regulation_down_capacity = regulation_down
        
        self.logger.info(f"Regulation capacity updated: Up={regulation_up:.1f} kW, Down={regulation_down:.1f} kW")
    
    def set_ramp_rate_limit(self, ramp_rate: float):
        """Set ramp rate limit"""
        self.ramp_rate_limit = ramp_rate
        self.logger.info(f"Ramp rate limit set to: {ramp_rate:.1f} kW/min")
    
    def set_agc_response_time(self, response_time: float):
        """Set AGC response time"""
        self.agc_response_time = response_time
        self.logger.info(f"AGC response time set to: {response_time:.1f} seconds")
    
    def set_pid_parameters(self, kp: float, ki: float, kd: float):
        """Set PID controller parameters"""
        self.pid_kp = kp
        self.pid_ki = ki
        self.pid_kd = kd
        self.pid_integral = 0.0  # Reset integral term
        
        self.logger.info(f"PID parameters updated: Kp={kp}, Ki={ki}, Kd={kd}")
    
    def get_current_status(self) -> Dict[str, Any]:
        """Get current controller status"""
        return {
            'is_active': self.is_active,
            'agc_status': self.agc_status.value,
            'regulation_mode': self.current_regulation_mode.value,
            'current_power_adjustment': self.current_power_adjustment,
            'target_power_adjustment': self.target_power_adjustment,
            'agc_signal_value': self.current_agc_signal.signal_value if self.current_agc_signal else 0.0
        }
    
    def get_regulation_performance(self) -> RegulationPerformance:
        """Get regulation performance metrics"""
        return self.regulation_performance
    
    def get_agc_signal_history(self, duration: timedelta = timedelta(hours=1)) -> List[AGCSignal]:
        """Get AGC signal history for specified duration"""
        cutoff_time = datetime.now() - duration
        return [s for s in self.agc_signal_history if s.timestamp >= cutoff_time]
    
    def get_regulation_history(self, duration: timedelta = timedelta(hours=1)) -> List[RegulationAction]:
        """Get regulation history for specified duration"""
        cutoff_time = datetime.now() - duration
        return [r for r in self.regulation_history if r.timestamp >= cutoff_time]
    
    def clear_agc_history(self):
        """Clear AGC signal history"""
        self.agc_signal_history.clear()
        self.logger.info("AGC signal history cleared")
    
    def clear_regulation_history(self):
        """Clear regulation history"""
        self.regulation_history.clear()
        self.logger.info("Regulation history cleared")
    
    def reset_performance_metrics(self):
        """Reset performance metrics"""
        self.regulation_performance = RegulationPerformance(
            regulation_up_capacity=self.regulation_up_capacity,
            regulation_down_capacity=self.regulation_down_capacity,
            response_time=0.0,
            accuracy=0.0,
            availability=1.0,
            ramp_rate=0.0,
            total_regulation_energy=0.0
        )
        
        self.logger.info("Performance metrics reset") 