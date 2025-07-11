"""
KPP Simulator Package

A comprehensive simulation framework for Kite Power Plant (KPP) systems.
This package provides advanced simulation capabilities including real-time
physics modeling, electrical system integration, and grid services.

Main Components:
- Simulation Engine: Core physics and system simulation
- Configuration Management: Parameter validation and management
- Grid Services: Electrical grid integration and services
- Control Systems: Advanced control and monitoring systems
- Managers: Thread-safe component management

Version: 1.0.0
"""

__version__ = "1.0.0"
__author__ = "KPP Development Team"
__description__ = "Advanced Kite Power Plant Simulation Framework"

# Import main components
from simulation.engine import SimulationEngine
from simulation.schemas import (
    FloaterState,
    PhysicsResults,
    FloaterPhysicsData,
    EnhancedPhysicsData,
    ComponentStatus,
    ManagerType,
    SimulationError,
    ManagerInterface
)

from simulation.grid_services import (
    GridServicesCoordinator,
    GridServicesConfig,
    GridServicesState,
    GridConditions
)

from simulation.control import (
    IntegratedControlSystem,
    ControlConfig,
    ControlState,
    ControlMode
)

from simulation.physics import (
    PhysicsEngine,
    PhysicsConfig,
    PhysicsState
)

from .managers.thread_safe_engine import ThreadSafeEngine
from .managers.system_manager import SystemManager
from .managers.component_manager import ComponentManager
from .config.manager import ConfigManager

# Export main classes
__all__ = [
    "SimulationEngine",
    "ThreadSafeEngine",
    "SystemManager", 
    "ComponentManager",
    "ConfigManager",
    "FloaterState",
    "PhysicsResults",
    "FloaterPhysicsData",
    "EnhancedPhysicsData",
    "ComponentStatus",
    "ManagerType",
    "SimulationError",
    "ManagerInterface",
    "GridServicesCoordinator",
    "GridServicesConfig",
    "GridServicesState",
    "GridConditions",
    "IntegratedControlSystem",
    "ControlConfig",
    "ControlState",
    "ControlMode",
    "PhysicsEngine",
    "PhysicsConfig",
    "PhysicsState"
] 