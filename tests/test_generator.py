"""
Unit tests for the refactored Generator component.
"""
import unittest
import sys
import os
import math

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from simulation.components.generator import Generator

class TestGenerator(unittest.TestCase):
    def setUp(self):
        """Set up a default generator for tests."""
        self.generator = Generator(
            efficiency=0.92,
            target_power=530000.0,
            target_rpm=375.0
        )
        self.target_omega = 375.0 * (2 * math.pi / 60)

    def test_initialization(self):
        """Test correct initialization of generator properties."""
        self.assertEqual(self.generator.target_power, 530000.0)
        self.assertAlmostEqual(self.generator.target_omega, 39.27, places=2)

    def test_load_torque_at_zero_speed(self):
        """Test that load torque is zero at zero speed."""
        self.assertEqual(self.generator.get_load_torque(0), 0)

    def test_load_torque_at_target_speed(self):
        """Test load torque at the rated target speed."""
        expected_torque = 530000.0 / self.target_omega
        self.assertAlmostEqual(self.generator.get_load_torque(self.target_omega), expected_torque)

    def test_load_torque_above_target_speed(self):
        """Test that load torque increases when over-speed."""
        torque_at_target = self.generator.get_load_torque(self.target_omega)
        torque_above_target = self.generator.get_load_torque(self.target_omega * 1.2)
        self.assertGreater(torque_above_target, torque_at_target)

    def test_power_output_at_target_speed(self):
        """Test power output at the rated target speed."""
        expected_power = 530000.0 * 0.92 # target_power * efficiency
        power = self.generator.calculate_power_output(self.target_omega)
        self.assertAlmostEqual(power, expected_power)

    def test_power_output_at_low_speed(self):
        """Test that power output is low at low speeds."""
        power_low = self.generator.calculate_power_output(self.target_omega * 0.2)
        power_target = self.generator.calculate_power_output(self.target_omega)
        self.assertLess(power_low, power_target)

if __name__ == '__main__':
    unittest.main()
