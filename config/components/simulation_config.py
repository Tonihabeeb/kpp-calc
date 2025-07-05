"""
Simulation configuration for the KPP simulator.
Contains simulation-wide parameters and enhanced physics settings.
"""

from dataclasses import dataclass, field
from ..core.base_config import BaseConfig


@dataclass
class SimulationConfig(BaseConfig):
    """Configuration for simulation-wide parameters"""
    
    # Time parameters
    time_step: float = field(default=0.1)
    simulation_duration: float = field(default=3600.0)
    
    # Pulse control parameters
    pulse_interval: float = field(default=2.0)
    pulse_duration: float = field(default=0.5)
    
    # Enhanced physics parameters (H1/H2/H3)
    h1_nanobubbles_active: bool = field(default=False)
    h1_enhancement_factor: float = field(default=1.2)
    h1_drag_reduction: float = field(default=0.3)
    
    h2_thermal_active: bool = field(default=False)
    h2_enhancement_factor: float = field(default=1.15)
    h2_thermal_gradient: float = field(default=0.1)
    
    h3_pulse_active: bool = field(default=False)
    h3_pulse_force: float = field(default=100.0)
    
    # Physics parameters
    water_density: float = field(default=1000.0)
    water_temperature: float = field(default=293.15)
    gravity: float = field(default=9.81)
    
    # Performance parameters
    target_power: float = field(default=530000.0)
    target_rpm: float = field(default=375.0)
    
    # System parameters
    tank_height: float = field(default=25.0)
    num_floaters: int = field(default=8) 