import unittest
import math
from simulation.components.floater import Floater
from config.config import G, RHO_WATER

class TestValidation(unittest.TestCase):
    def test_depth_dependent_buoyancy(self):
        """Depth-Dependent Buoyancy Test: Verify basic buoyancy calculation works."""
        floater = Floater(volume=0.5, mass=10.0, area=0.1)
        # Test basic buoyancy calculation
        floater.set_filled(True)
        floater.fill_progress = 1.0
        
        # Buoyant force should be volume * water_density * g (upward force only)
        # Volume = 0.5 m³
        # Expected buoyant force = 0.5 * 1000 * 9.81 = 4905 N
        buoyant_force = floater.compute_buoyant_force()
        expected_force = 0.5 * 1000 * 9.81  # Volume buoyancy
        
        # Check that the calculated force matches expected
        self.assertAlmostEqual(buoyant_force, expected_force, delta=1.0, 
                              msg=f"Buoyant force {buoyant_force} not close to expected {expected_force}")

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
