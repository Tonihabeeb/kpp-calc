"""
Unit tests for the Floater class.
"""
import unittest
from simulation.components.floater import Floater

class TestFloater(unittest.TestCase):
    def test_buoyant_force_air_filled(self):
        floater = Floater(volume=0.1, mass=10, area=0.01, Cd=0.8, is_filled=True)
        self.assertGreater(floater.compute_buoyant_force(), 0)

    def test_buoyant_force_water_filled(self):
        floater = Floater(volume=0.1, mass=10, area=0.01, Cd=0.8, is_filled=False)
        self.assertEqual(floater.compute_buoyant_force(), 0)

    def test_drag_force(self):
        floater = Floater(volume=0.1, mass=10, area=0.01, Cd=0.8, velocity=2.0, is_filled=True)
        drag = floater.compute_drag_force()
        self.assertTrue(isinstance(drag, float))

    def test_update(self):
        floater = Floater(volume=0.1, mass=10, area=0.01, Cd=0.8, velocity=0.0, is_filled=True)
        floater.update(0.1, {}, 0.0)
        self.assertTrue(isinstance(floater.position, float))
        self.assertTrue(isinstance(floater.velocity, float))

    def test_set_filled(self):
        floater = Floater(volume=0.1, mass=10, area=0.01, Cd=0.8)
        floater.set_filled(True)
        self.assertTrue(floater.is_filled)
        floater.set_filled(False)
        self.assertFalse(floater.is_filled)

if __name__ == "__main__":
    unittest.main()
