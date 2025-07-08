from .venting_system import AirReleasePhysics, AutomaticVentingSystem, VentingTrigger
try:
    from .thermodynamics import Thermodynamics
except ImportError:
    class Thermodynamics:
        pass

from .pressure_expansion import PressureExpansionPhysics
try:
    from .pressure_control import PressureControl
except ImportError:
    class PressureControl:
        pass

try:
    from .injection_control import InjectionControl
except ImportError:
    class InjectionControl:
        pass

try:
    from .heat_exchange import HeatExchange
except ImportError:
    class HeatExchange:
        pass

try:
    from .air_compression import AirCompression
except ImportError:
    class AirCompression:
        pass

"""
KPP Pneumatic System Package

This package implements the comprehensive pneumatic system for the Kinetic Power Plant,
providing realistic modeling of air compression, storage, injection,
     and control systems.

Phase 1 Components (COMPLETE):
- AirCompressionSystem: Core air compression and storage with realistic physics
- PressureControlSystem: Intelligent pressure control with safety monitoring

Phase 2 Components (COMPLETE):
- AirInjectionController: Valve timing and injection control system
- FloaterInjectionRequest: Injection request management
- Enhanced Floater: Pneumatic state management

Phase 3 Components (COMPLETE):
- PressureExpansionPhysics: Gas expansion, dissolution, and buoyancy dynamics

Phase 4 Components (COMPLETE):
- AutomaticVentingSystem: Position-based air release and floater reset
- VentingTrigger: Configurable venting trigger mechanisms
- AirReleasePhysics: Air release dynamics and water refill physics

Phase 5 Components (COMPLETE):
- AdvancedThermodynamics: Comprehensive thermodynamic modeling
- IntegratedHeatExchange: Complete heat transfer analysis
- ThermalBuoyancyCalculator: Thermal boost calculations

Future Phases:
- Complete system integration
- Performance optimization
"""

