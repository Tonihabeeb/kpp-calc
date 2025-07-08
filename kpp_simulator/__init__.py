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
from .managers.thread_safe_engine import ThreadSafeEngine
from .managers.system_manager import SystemManager
from .managers.component_manager import ComponentManager

# Export main classes
__all__ = [
    "ThreadSafeEngine",
    "SystemManager", 
    "ComponentManager",
] 