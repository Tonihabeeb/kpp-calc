"""
Voltage Support Services Package

This package provides voltage support and reactive power control services
including automatic voltage regulation, power factor control, and dynamic
voltage support for grid stability.
"""

# Import voltage services with fallbacks
try:
    from .voltage_regulator import VoltageRegulator, create_standard_voltage_regulator
except ImportError:
    class VoltageRegulator:
        pass
    
    def create_standard_voltage_regulator():
        return None

try:
    from .power_factor_controller import PowerFactorController
except ImportError:
    class PowerFactorController:
        pass

try:
    from .dynamic_voltage_support import DynamicVoltageSupport
except ImportError:
    class DynamicVoltageSupport:
        pass
"""
Voltage Support Services Package

This package provides voltage support and reactive power control services
including automatic voltage regulation, power factor control, and dynamic
voltage support for grid stability.
"""

