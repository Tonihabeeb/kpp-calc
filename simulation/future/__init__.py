"""
Future enhancement initialization and configuration.
"""

from .enhancement_hooks import (
    EnhancementHooks,
    PhysicsEngineExtension,
    create_enhancement_integration,
    create_migration_plan,
    enable_enhancement_gradually,
    monitor_enhancement_performance,
)
from .hypothesis_framework import (
    DEFAULT_ENHANCEMENT_CONFIG,
    EnhancementConfig,
    HypothesisFramework,
    HypothesisType,
    create_future_framework,
)

__all__ = [
    "HypothesisFramework",
    "HypothesisType",
    "EnhancementConfig",
    "EnhancementHooks",
    "PhysicsEngineExtension",
    "create_future_framework",
    "create_enhancement_integration",
    "enable_enhancement_gradually",
    "monitor_enhancement_performance",
    "create_migration_plan",
    "DEFAULT_ENHANCEMENT_CONFIG",
]

# Version information for future enhancements
FUTURE_FRAMEWORK_VERSION = "1.0.0"
SUPPORTED_HYPOTHESES = [
    HypothesisType.H1_ADVANCED_DYNAMICS,
    HypothesisType.H2_MULTI_PHASE_FLUID,
    HypothesisType.H3_THERMAL_COUPLING,
    HypothesisType.H4_CONTROL_OPTIMIZATION,
    HypothesisType.H5_MACHINE_LEARNING,
]
