"""
H1: Nanobubble drag/density reduction logic for KPP simulator.
"""

class H1Nanobubbles:
    """
    Applies nanobubble effects to environment properties.
    """
    @staticmethod
    def apply_density_reduction(base_density: float, reduction_factor: float) -> float:
        """
        Reduce water density by a given factor.
        """
        return base_density * (1.0 - reduction_factor)

    @staticmethod
    def apply_drag_reduction(base_drag: float, reduction_factor: float) -> float:
        """
        Reduce drag by a given factor.
        """
        return base_drag * (1.0 - reduction_factor)
