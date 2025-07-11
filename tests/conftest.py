"""
Pytest configuration and fixtures for KPP simulator tests.
"""

import os
import sys
import pytest
import logging
from typing import Dict, Any

# Add project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

from simulation.engine import SimulationEngine, SimulationConfig
from simulation.physics import PhysicsEngine, PhysicsConfig, PhysicsState
from simulation.components.floater.enhanced_floater import EnhancedFloater, EnhancedFloaterConfig
from simulation.components.environment import Environment, EnvironmentConfig
from simulation.components.pneumatics import PneumaticSystem, PneumaticConfig
from simulation.components.drivetrain import IntegratedDrivetrain, DrivetrainConfig

@pytest.fixture
def sim_config() -> SimulationConfig:
    """Create a default simulation configuration"""
    return SimulationConfig(
        time_step=0.01,
        num_floaters=10,
        tank_height=10.0,
        rated_power=50000.0,
        enable_h1=False,
        enable_h2=False,
        enable_h3=False
    )

@pytest.fixture
def physics_config() -> PhysicsConfig:
    """Create a default physics configuration"""
    return PhysicsConfig(
        time_step=0.01,
        tank_height=10.0,
        max_velocity=10.0,
        max_acceleration=5.0,
        max_angular_velocity=20.0
    )

@pytest.fixture
def floater_config() -> EnhancedFloaterConfig:
    """Create a default floater configuration"""
    return EnhancedFloaterConfig(
        volume=0.04,  # 40L
        mass_empty=5.0,  # 5kg
        cross_section=0.1  # 0.1m²
    )

@pytest.fixture
def env_config() -> EnvironmentConfig:
    """Create a default environment configuration"""
    return EnvironmentConfig(
        water_density=1000.0,
        water_temperature=20.0,
        enable_h1=False,
        nanobubble_fraction=0.2,
        enable_h2=False,
        thermal_expansion_coeff=0.001
    )

@pytest.fixture
def drivetrain_config() -> DrivetrainConfig:
    """Create a default drivetrain configuration"""
    return DrivetrainConfig(
        chain_radius=1.0,
        generator_efficiency=0.92,
        mechanical_efficiency=0.95,
        enable_h3=False,
        flywheel_inertia=10.0
    )

@pytest.fixture
def pneumatic_config() -> PneumaticConfig:
    """Create a default pneumatic system configuration"""
    return PneumaticConfig(
        enable_h2=False,
        thermal_expansion_coeff=0.001,
        isothermal_efficiency=0.9
    )

@pytest.fixture
def sim_engine(sim_config: SimulationConfig) -> SimulationEngine:
    """Create a simulation engine with default configuration"""
    return SimulationEngine(sim_config)

@pytest.fixture
def physics_engine(physics_config: PhysicsConfig) -> PhysicsEngine:
    """Create a physics engine with default configuration"""
    return PhysicsEngine(physics_config)

@pytest.fixture
def floater(floater_config: EnhancedFloaterConfig) -> EnhancedFloater:
    """Create a floater with default configuration"""
    return EnhancedFloater(floater_config)

@pytest.fixture
def environment(env_config: EnvironmentConfig) -> Environment:
    """Create an environment with default configuration"""
    return Environment(env_config)

@pytest.fixture
def drivetrain(drivetrain_config: DrivetrainConfig) -> Drivetrain:
    """Create a drivetrain with default configuration"""
    return Drivetrain(drivetrain_config)

@pytest.fixture
def pneumatic_system(pneumatic_config: PneumaticConfig) -> PneumaticSystem:
    """Create a pneumatic system with default configuration"""
    return PneumaticSystem(pneumatic_config)

