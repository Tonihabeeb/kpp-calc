"""
Demand Response Services Package

This package provides demand response capabilities including load curtailment,
peak shaving, load forecasting, and economic optimization of energy consumption
and generation dispatch.
"""

try:
    from .peak_shaving_controller import PeakShavingController
except ImportError:
    class PeakShavingController:
        pass

try:
    from .load_forecaster import (
        LoadForecaster,
        LoadForecastConfig,
        create_standard_load_forecaster
    )
except ImportError:
    class LoadForecaster:
        pass
    
    class LoadForecastConfig:
        pass
    
    def create_standard_load_forecaster():
        return None

try:
    from .load_curtailment_controller import (
        LoadCurtailmentController,
        LoadCurtailmentConfig,
        create_standard_load_curtailment_controller
    )
except ImportError:
    class LoadCurtailmentController:
        pass
    
    class LoadCurtailmentConfig:
        pass
    
    def create_standard_load_curtailment_controller():
        return None

