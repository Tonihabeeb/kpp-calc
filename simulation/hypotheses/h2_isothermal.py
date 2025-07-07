        import math
"""
H2: Isothermal compression logic for KPP simulator.
"""


class H2Isothermal:
    """
    Applies isothermal compression effects to pneumatic calculations.
    """

    @staticmethod
    def compute_injection_work(volume: float, pressure: float) -> float:
        """
        Compute work for isothermal air injection (W = P*V*ln(P2/P1)).
        """
