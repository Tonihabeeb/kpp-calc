"""
KPP Pneumatic System Package

This package implements the comprehensive pneumatic system for the Kinetic Power Plant,
providing realistic modeling of air compression, storage, injection, and control systems.

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

from .air_compression import (
    AirCompressionSystem,
    CompressorSpec,
    PressureTankSpec,
    create_standard_kpp_compressor
)

from .pressure_control import (
    PressureControlSystem,
    PressureControlSettings,
    CompressorState,
    SafetyLevel,
    create_standard_kpp_pressure_controller
)

from .injection_control import (
    AirInjectionController,
    InjectionValveSpec,
    InjectionSettings,
    FloaterInjectionRequest,
    InjectionState,
    ValveState,
    create_standard_kpp_injection_controller
)

from .pressure_expansion import PressureExpansionPhysics

from .venting_system import (
    AutomaticVentingSystem,
    VentingTrigger,
    AirReleasePhysics
)

from .pressure_expansion import (
    PressureExpansionPhysics
)

from .thermodynamics import (
    AdvancedThermodynamics,
    ThermodynamicProperties,
    CompressionThermodynamics,
    ExpansionThermodynamics,
    ThermalBuoyancyCalculator
)

from .heat_exchange import (
    IntegratedHeatExchange,
    AirWaterHeatExchange,
    WaterThermalReservoir,
    CompressionHeatRecovery,
    HeatTransferCoefficients
)

__all__ = [
    # Phase 1 - Air Compression and Storage
    'AirCompressionSystem',
    'CompressorSpec', 
    'PressureTankSpec',
    'create_standard_kpp_compressor',
    'PressureControlSystem',
    'PressureControlSettings',
    'CompressorState',
    'SafetyLevel',
    'create_standard_kpp_pressure_controller',
    
    # Phase 2 - Air Injection Control
    'AirInjectionController',
    'InjectionValveSpec',
    'InjectionSettings',
    'FloaterInjectionRequest',
    'InjectionState',
    'ValveState',
    'create_standard_kpp_injection_controller',
    
    # Phase 3 - Buoyancy and Ascent Dynamics
    'PressureExpansionPhysics',
    
    # Phase 4 - Venting and Reset Mechanism
    'AutomaticVentingSystem',
    'VentingTrigger',
    'AirReleasePhysics',
    
    # Phase 5 - Thermodynamic Modeling and Thermal Boost
    'AdvancedThermodynamics',
    'ThermodynamicProperties',
    'CompressionThermodynamics',
    'ExpansionThermodynamics',
    'ThermalBuoyancyCalculator',
    'IntegratedHeatExchange',
    'AirWaterHeatExchange',
    'WaterThermalReservoir',
    'CompressionHeatRecovery',
    'HeatTransferCoefficients'
]

__version__ = "1.0.0"
