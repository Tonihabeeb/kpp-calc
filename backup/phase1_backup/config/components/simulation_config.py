from dataclasses import dataclass, field
from typing import Dict, Any, Optional
from ..core.base_config import BaseConfig
"""
Simulation configuration for the KPP simulator.
Contains simulation-wide parameters and enhanced physics settings.
"""

@dataclass
class SimulationConfig(BaseConfig):
    """Simulation-wide configuration parameters"""
    
    # Time settings
    time_step: float = 0.01  # seconds
    max_simulation_time: float = 3600.0  # seconds (1 hour)
    real_time_factor: float = 1.0  # simulation speed multiplier
    
    # Physics settings
    gravity: float = 9.81  # m/s²
    water_density: float = 1000.0  # kg/m³
    air_density: float = 1.225  # kg/m³
    atmospheric_pressure: float = 101325.0  # Pa
    
    # System parameters
    num_floaters: int = 10
    chain_length: float = 100.0  # meters
    max_chain_tension: float = 50000.0  # N
    max_chain_speed: float = 60.0  # m/s
    
    # Electrical system
    electrical_engagement_threshold: float = 2000.0  # W
    max_electrical_power: float = 50000.0  # W (50 kW)
    grid_voltage: float = 400.0  # V
    grid_frequency: float = 50.0  # Hz
    
    # Performance limits
    max_pressure: float = 500000.0  # Pa
    min_pressure: float = 100000.0  # Pa
    max_temperature: float = 373.15  # K (100°C)
    min_temperature: float = 273.15  # K (0°C)
    
    # Control parameters
    control_update_rate: float = 100.0  # Hz
    emergency_shutdown_enabled: bool = True
    auto_restart_enabled: bool = True
    
    # Logging and monitoring
    log_level: str = "INFO"
    data_logging_enabled: bool = True
    performance_monitoring_enabled: bool = True
    
    # Validation settings
    validation_enabled: bool = True
    strict_validation: bool = False
    
    def validate(self) -> None:
        """Validate simulation configuration parameters"""
        super().validate()
        
        if self.time_step <= 0:
            raise ValueError("time_step must be positive")
        if self.max_simulation_time <= 0:
            raise ValueError("max_simulation_time must be positive")
        if self.num_floaters <= 0:
            raise ValueError("num_floaters must be positive")
        if self.chain_length <= 0:
            raise ValueError("chain_length must be positive")
        if self.max_chain_tension <= 0:
            raise ValueError("max_chain_tension must be positive")
        if self.max_chain_speed <= 0:
            raise ValueError("max_chain_speed must be positive")
        if self.max_pressure <= self.min_pressure:
            raise ValueError("max_pressure must be greater than min_pressure")
        if self.max_temperature <= self.min_temperature:
            raise ValueError("max_temperature must be greater than min_temperature")

