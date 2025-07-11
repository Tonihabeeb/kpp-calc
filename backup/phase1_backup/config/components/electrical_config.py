"""
Electrical system configuration for KPP simulator.
"""

from dataclasses import dataclass
from typing import Optional

@dataclass
class ElectricalConfig:
    """Configuration for electrical power system"""
    
    # Generator settings
    generator_efficiency: float = 0.95
    generator_max_power: float = 100000.0  # W (100 kW)
    generator_min_power: float = 1000.0  # W (1 kW)
    
    # Grid settings
    grid_voltage: float = 480.0  # V
    grid_frequency: float = 60.0  # Hz
    grid_connection_type: str = "infinite_bus"
    
    # Power flow settings
    enable_power_flow: bool = True
    power_flow_tolerance: float = 1e-6
    max_power_flow_iterations: int = 50
    
    # Load modeling
    load_type: str = "constant_power"
    load_power_factor: float = 0.95
    
    # H3 enhancement settings
    h3_clutch_response_time: float = 0.1  # seconds
    h3_pulse_duration: float = 2.0  # seconds
    h3_coast_duration: float = 2.0  # seconds
