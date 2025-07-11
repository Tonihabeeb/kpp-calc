from typing import Any, Dict
from dataclasses import dataclass, field
from ..core.base_config import BaseConfig

"""
IntegratedDrivetrain configuration for the KPP simulator.
Defines parameters for the integrated integrated_drivetrain system.
"""

@dataclass
class DrivetrainConfig(BaseConfig):
    """Drivetrain system configuration parameters"""
    
    # Mechanical properties
    total_mass: float = 1000.0  # kg
    moment_of_inertia: float = 50.0  # kg·m²
    gear_ratio: float = 10.0  # dimensionless
    efficiency: float = 0.95  # dimensionless
    
    # Chain system
    chain_length: float = 100.0  # meters
    chain_mass_per_meter: float = 10.0  # kg/m
    chain_tension_max: float = 50000.0  # N
    chain_speed_max: float = 60.0  # m/s
    
    # Floater system
    num_floaters: int = 10
    floater_mass: float = 16.0  # kg
    floater_volume: float = 0.4  # m³
    floater_spacing: float = 10.0  # meters
    
    # Power transmission
    mechanical_power_max: float = 100000.0  # W (100 kW)
    torque_max: float = 1000.0  # N·m
    speed_max: float = 1500.0  # RPM
    
    # Control parameters
    speed_control_enabled: bool = True
    tension_control_enabled: bool = True
    emergency_stop_enabled: bool = True
    
    # Performance limits
    acceleration_max: float = 10.0  # m/s²
    deceleration_max: float = 15.0  # m/s²
    jerk_max: float = 50.0  # m/s³
    
    # Safety settings
    safety_factor: float = 2.0  # dimensionless
    overload_protection: bool = True
    overspeed_protection: bool = True
    
    # Monitoring
    vibration_monitoring: bool = True
    temperature_monitoring: bool = True
    wear_monitoring: bool = True
    
    def validate(self) -> None:
        """Validate drivetrain configuration parameters"""
        super().validate()
        
        if self.total_mass <= 0:
            raise ValueError("total_mass must be positive")
        if self.moment_of_inertia <= 0:
            raise ValueError("moment_of_inertia must be positive")
        if self.gear_ratio <= 0:
            raise ValueError("gear_ratio must be positive")
        if self.efficiency <= 0 or self.efficiency > 1:
            raise ValueError("efficiency must be between 0 and 1")
        if self.chain_length <= 0:
            raise ValueError("chain_length must be positive")
        if self.chain_tension_max <= 0:
            raise ValueError("chain_tension_max must be positive")
        if self.chain_speed_max <= 0:
            raise ValueError("chain_speed_max must be positive")
        if self.num_floaters <= 0:
            raise ValueError("num_floaters must be positive")
        if self.mechanical_power_max <= 0:
            raise ValueError("mechanical_power_max must be positive")
        if self.torque_max <= 0:
            raise ValueError("torque_max must be positive")
        if self.speed_max <= 0:
            raise ValueError("speed_max must be positive")
        if self.safety_factor <= 0:
            raise ValueError("safety_factor must be positive")

