"""
Unit tests for the Drivetrain class.
"""
import unittest
import sys
import os
import math

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from simulation.components.drivetrain import Drivetrain

class TestDrivetrain(unittest.TestCase):
    """Unit tests for the refactored Drivetrain component."""

    def setUp(self):
        """Set up a default drivetrain for tests."""
        self.drivetrain = Drivetrain(
            gear_ratio=16.7,
            efficiency=0.95,
            sprocket_radius=0.5,
            flywheel_inertia=50.0,
            chain_inertia=5.0,
            clutch_threshold=0.1
        )

    def test_initialization(self):
        """Test correct initialization of drivetrain properties."""
        self.assertEqual(self.drivetrain.gear_ratio, 16.7)
        self.assertEqual(self.drivetrain.I_flywheel, 50.0)
        self.assertEqual(self.drivetrain.omega_chain, 0.0)
        self.assertEqual(self.drivetrain.omega_flywheel, 0.0)
        self.assertFalse(self.drivetrain.clutch_engaged)

    def test_compute_input_torque(self):
        """Test the calculation of input torque from chain force."""
        chain_force = 1000  # N
        expected_torque = 1000 * 0.5 * 0.95  # force * radius * efficiency
        self.assertAlmostEqual(self.drivetrain.compute_input_torque(chain_force), expected_torque)

    def test_dynamics_no_load(self):
        """Test dynamics update with input torque but no load."""
        self.drivetrain.update_dynamics(net_torque=500, load_torque=0, dt=0.1)
        self.assertGreater(self.drivetrain.omega_chain, 0)
        # Without load, flywheel should also start spinning (due to friction model)
        self.assertGreater(self.drivetrain.omega_flywheel, 0)

    def test_clutch_engagement(self):
        """Test that the clutch engages when speeds are close."""
        self.drivetrain.omega_chain = 1.0
        self.drivetrain.omega_flywheel = 16.65 # Very close to 1.0 * 16.7
        self.drivetrain.update_dynamics(net_torque=0, load_torque=0, dt=0.1)
        self.assertTrue(self.drivetrain.clutch_engaged)

    def test_clutch_disengagement(self):
        """Test that the clutch disengages when speeds are different."""
        self.drivetrain.omega_chain = 1.0
        self.drivetrain.omega_flywheel = 10.0 # Far from 1.0 * 16.7
        self.drivetrain.update_dynamics(net_torque=0, load_torque=0, dt=0.1)
        self.assertFalse(self.drivetrain.clutch_engaged)

    def test_dynamics_with_load(self):
        """Test that load torque slows down the flywheel."""
        self.drivetrain.omega_flywheel = 20.0
        self.drivetrain.update_dynamics(net_torque=0, load_torque=100, dt=0.1)
        self.assertLess(self.drivetrain.omega_flywheel, 20.0)

if __name__ == '__main__':
    unittest.main()
