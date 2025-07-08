try:
    from .integrated_loss_model import IntegratedLossModel
except ImportError:
    class IntegratedLossModel:
        pass

# Physics package for KPP simulation
# Contains advanced physics models and loss calculations

