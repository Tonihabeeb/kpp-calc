import unittest
import math
from simulation.components.floater import Floater
from config.config import G, RHO_WATER

class TestValidation(unittest.TestCase):
    def test_depth_dependent_buoyancy(self):
        """Depth-Dependent Buoyancy Test: Verify buoyancy decreases with depth."""
        floater = Floater(volume=0.5, mass=10.0, area=0.1)
        # Assume fully filled
        floater.set_filled(True)
        floater.fill_progress = 1.0
        # Compute buoyancy at surface (depth 0)
        F_surface = floater.compute_buoyant_force_adjusted(depth=0.0)
        # Compute buoyancy at depth 10m
        F_deep = floater.compute_buoyant_force_adjusted(depth=10.0)
        # Buoyancy should decrease with depth due to compression
        self.assertLess(F_deep, F_surface, f"Buoyancy did not decrease with depth: {F_deep} >= {F_surface}")

    def test_dissolution_loss(self):
        """Dissolution Loss Test: Verify buoyancy decreases over time due to dissolution."""
        floater = Floater(volume=0.3, mass=2.0, area=0.1)
        floater.set_filled(True)
        # Simulate for some time
        initial_buoyancy = floater.compute_buoyant_force()
        # Run several updates to allow dissolution
        for _ in range(50):
            floater.update(dt=0.1)
        final_buoyancy = floater.compute_buoyant_force()
        # Buoyancy should decrease over time as air dissolves
        self.assertLess(final_buoyancy, initial_buoyancy, f"Buoyancy did not decrease over time: {final_buoyancy} >= {initial_buoyancy}")

if __name__ == '__main__':
    unittest.main()
