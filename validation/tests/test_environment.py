"""
Unit tests for the Environment class.
"""
import unittest
from simulation.components.environment import Environment

class TestEnvironment(unittest.TestCase):
    def test_density_default(self):
        env = Environment()
        self.assertEqual(env.get_density(), 1000.0)

    def test_density_nanobubble(self):
        env = Environment(nanobubble_enabled=True, density_reduction_factor=0.2)
        self.assertAlmostEqual(env.get_density(), 800.0)

    def test_viscosity(self):
        env = Environment(water_viscosity=1.5e-3)
        self.assertEqual(env.get_viscosity(), 1.5e-3)

    def test_update_noop(self):
        env = Environment()
        # Should not raise
        env.update(0.1)

if __name__ == "__main__":
    unittest.main()
