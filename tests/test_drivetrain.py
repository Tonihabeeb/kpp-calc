"""
Unit tests for the Drivetrain class.
"""
import unittest
from simulation.components.drivetrain import Drivetrain

class TestDrivetrain(unittest.TestCase):
    def test_compute_torque(self):
        dt = Drivetrain(gear_ratio=2.0, efficiency=0.9, sprocket_radius=0.5)
        torque = dt.compute_torque(100)
        self.assertAlmostEqual(torque, 100 * 0.5 * 2.0 * 0.9)

    def test_apply_load(self):
        dt = Drivetrain(gear_ratio=2.0, efficiency=0.9, sprocket_radius=0.5)
        chain_force = dt.apply_load(90)
        self.assertAlmostEqual(chain_force, 90 / (0.5 * 2.0))

    def test_update_params(self):
        dt = Drivetrain(gear_ratio=2.0, efficiency=0.9, sprocket_radius=0.5)
        dt.update_params({'gear_ratio': 3.0, 'efficiency': 0.8, 'sprocket_radius': 0.4})
        self.assertEqual(dt.gear_ratio, 3.0)
        self.assertEqual(dt.efficiency, 0.8)
        self.assertEqual(dt.sprocket_radius, 0.4)

if __name__ == "__main__":
    unittest.main()
