"""
Physics module for KPP simulation.
Provides core physics calculations and state management.
"""

from simulation.physics.physics_engine import PhysicsEngine
from simulation.schemas import PhysicsResults

class PhysicsConfig:
    """Configuration for physics calculations"""
    def __init__(self, **kwargs):
        # Basic physics parameters
        self.time_step = kwargs.get('time_step', 0.01)
        self.tank_height = kwargs.get('tank_height', 10.0)
        self.gravity = kwargs.get('gravity', 9.81)
        self.water_density = kwargs.get('water_density', 1000.0)
        self.air_density = kwargs.get('air_density', 1.225)
        self.temperature = kwargs.get('temperature', 293.15)  # K
        
        # Motion limits
        self.max_velocity = kwargs.get('max_velocity', 10.0)  # m/s
        self.max_acceleration = kwargs.get('max_acceleration', 5.0)  # m/s²
        self.max_angular_velocity = kwargs.get('max_angular_velocity', 20.0)  # rad/s
        
        # Numerical parameters
        self.max_iterations = kwargs.get('max_iterations', 50)
        self.convergence_tolerance = kwargs.get('convergence_tolerance', 1e-6)
        
        # Enhancement parameters
        self.enable_h1 = kwargs.get('enable_h1', False)
        self.enable_h2 = kwargs.get('enable_h2', False)
        self.enable_h3 = kwargs.get('enable_h3', False)
        self.nanobubble_fraction = kwargs.get('nanobubble_fraction', 0.2)
        self.thermal_expansion_coeff = kwargs.get('thermal_expansion_coeff', 0.001)
        self.flywheel_inertia = kwargs.get('flywheel_inertia', 10.0)
        
        # Efficiency parameters
        self.mechanical_efficiency = kwargs.get('mechanical_efficiency', 0.95)
        self.electrical_efficiency = kwargs.get('electrical_efficiency', 0.92)

class PhysicsState:
    """State information for physics calculations"""
    def __init__(self):
        self.time = 0.0
        self.total_energy = 0.0
        self.total_power = 0.0
        self.efficiency = 0.0
        self.mechanical_power = 0.0
        self.electrical_power = 0.0
        self.losses = {}
        self.enhancement_data = None

__all__ = ['PhysicsEngine', 'PhysicsConfig', 'PhysicsState', 'PhysicsResults']

