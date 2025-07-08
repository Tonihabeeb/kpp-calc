from dataclasses import dataclass, field
from ..core.base_config import BaseConfig
"""
Control system configuration for the KPP simulator.
"""

@dataclass
class ControlConfig(BaseConfig):
    """Control system configuration parameters"""
    
    # Control modes
    control_mode: str = "automatic"  # automatic, manual, emergency
    emergency_stop_enabled: bool = True
    auto_restart_enabled: bool = True
    
    # Timing parameters
    control_update_rate: float = 100.0  # Hz
    response_time_target: float = 0.1  # seconds
    settling_time_target: float = 1.0  # seconds
    
    # Power control
    target_power: float = 25000.0  # W (25 kW)
    power_tolerance: float = 1000.0  # W
    power_ramp_rate: float = 5000.0  # W/s
    
    # Speed control
    target_speed: float = 10.0  # m/s
    speed_tolerance: float = 0.5  # m/s
    speed_ramp_rate: float = 2.0  # m/s²
    
    # Pressure control
    target_pressure: float = 300000.0  # Pa
    pressure_tolerance: float = 10000.0  # Pa
    pressure_ramp_rate: float = 50000.0  # Pa/s
    
    # PID parameters
    kp_power: float = 1.0
    ki_power: float = 0.1
    kd_power: float = 0.01
    
    kp_speed: float = 2.0
    ki_speed: float = 0.2
    kd_speed: float = 0.02
    
    kp_pressure: float = 0.5
    ki_pressure: float = 0.05
    kd_pressure: float = 0.005
    
    # Safety limits
    max_power: float = 50000.0  # W
    min_power: float = 0.0  # W
    max_speed: float = 60.0  # m/s
    min_speed: float = 0.0  # m/s
    max_pressure: float = 500000.0  # Pa
    min_pressure: float = 100000.0  # Pa
    
    # Fault handling
    fault_detection_enabled: bool = True
    fault_recovery_enabled: bool = True
    max_fault_count: int = 3
    fault_timeout: float = 30.0  # seconds
    
    # Monitoring
    performance_monitoring: bool = True
    data_logging: bool = True
    alarm_system: bool = True
    
    def validate(self) -> None:
        """Validate control configuration parameters"""
        super().validate()
        
        if self.control_update_rate <= 0:
            raise ValueError("control_update_rate must be positive")
        if self.response_time_target <= 0:
            raise ValueError("response_time_target must be positive")
        if self.settling_time_target <= 0:
            raise ValueError("settling_time_target must be positive")
        if self.target_power < 0:
            raise ValueError("target_power must be non-negative")
        if self.power_tolerance < 0:
            raise ValueError("power_tolerance must be non-negative")
        if self.power_ramp_rate <= 0:
            raise ValueError("power_ramp_rate must be positive")
        if self.target_speed < 0:
            raise ValueError("target_speed must be non-negative")
        if self.speed_tolerance < 0:
            raise ValueError("speed_tolerance must be non-negative")
        if self.speed_ramp_rate <= 0:
            raise ValueError("speed_ramp_rate must be positive")
        if self.target_pressure <= 0:
            raise ValueError("target_pressure must be positive")
        if self.pressure_tolerance < 0:
            raise ValueError("pressure_tolerance must be non-negative")
        if self.pressure_ramp_rate <= 0:
            raise ValueError("pressure_ramp_rate must be positive")
        if self.max_power <= self.min_power:
            raise ValueError("max_power must be greater than min_power")
        if self.max_speed <= self.min_speed:
            raise ValueError("max_speed must be greater than min_speed")
        if self.max_pressure <= self.min_pressure:
            raise ValueError("max_pressure must be greater than min_pressure")

