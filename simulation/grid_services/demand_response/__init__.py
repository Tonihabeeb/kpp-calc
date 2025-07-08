try:
    from .peak_shaving_controller import PeakShavingController
except ImportError:
    class PeakShavingController:
        pass

from .load_forecaster import LoadForecaster, create_standard_load_forecaster
try:
    from .load_curtailment_controller import LoadCurtailmentController
except ImportError:
    class LoadCurtailmentController:
        pass

"""
Demand Response Services Package

This package provides demand response capabilities including load curtailment,
peak shaving, load forecasting, and economic optimization of energy consumption
and generation dispatch.
"""

