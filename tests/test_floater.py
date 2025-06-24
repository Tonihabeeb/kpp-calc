"""
Unit tests for the updated Floater component.
"""
import unittest
import sys
import os
from config.config import G, RHO_WATER, RHO_AIR

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from simulation.components.floater import Floater

class TestFloater(unittest.TestCase):
    def setUp(self):
        """Set up a default floater for tests."""
        self.floater = Floater(
            volume=0.3,
            mass=18.0,
            area=0.035,
            Cd=0.8,
            air_fill_time=0.5,
            air_pressure=300000,
            air_flow_rate=0.6,
            jet_efficiency=0.85
        )

    def test_initialization(self):
        """Test that the floater initializes with correct default values."""
        self.assertEqual(self.floater.volume, 0.3)
        self.assertEqual(self.floater.mass, 18.0)
        self.assertFalse(self.floater.is_filled)
        self.assertEqual(self.floater.fill_progress, 0.0)
        self.assertEqual(self.floater.position, 0.0)
        self.assertEqual(self.floater.velocity, 0.0)

    def test_start_filling(self):
        """Test the process of starting to fill the floater."""
        self.floater.start_filling()
        self.assertTrue(self.floater.is_filled)
        self.assertEqual(self.floater.fill_progress, 0.0)

    def test_update_filling_progress(self):
        """Test that the fill progress correctly updates over time."""
        self.floater.start_filling()
        self.floater.update(dt=0.1)
        self.assertAlmostEqual(self.floater.fill_progress, 0.2) # 0.1 / 0.5
        self.floater.update(dt=0.4)
        self.assertEqual(self.floater.fill_progress, 1.0)

    def test_force_calculation_when_empty(self):
        """Test net force on an empty, stationary floater (should be just gravity)."""
        expected_force = -self.floater.mass * G
        self.assertAlmostEqual(self.floater.force, expected_force)

    def test_force_calculation_when_full(self):
        """Test net force on a fully filled, stationary floater."""
        self.floater.set_filled(True)
        buoyancy = RHO_WATER * self.floater.volume * G
        air_mass = RHO_AIR * self.floater.volume
        gravity = -(self.floater.mass + air_mass) * G
        expected_force = buoyancy + gravity
        self.assertAlmostEqual(self.floater.force, expected_force)

    def test_pulse_jet_force(self):
        """Test that the pulse jet force is active only during filling."""
        self.assertEqual(self.floater.compute_pulse_jet_force(), 0.0)
        self.floater.start_filling()
        self.floater.update(dt=0.01) # Start filling
        self.assertGreater(self.floater.compute_pulse_jet_force(), 0)
        self.floater.update(dt=0.5) # Finish filling
        self.assertEqual(self.floater.compute_pulse_jet_force(), 0.0)

    def test_update_kinematics(self):
        """Test that the floater's position and velocity update correctly."""
        self.floater.set_filled(True) # Make it buoyant
        initial_pos = self.floater.position
        initial_vel = self.floater.velocity
        self.floater.update(dt=0.1)
        self.assertNotEqual(self.floater.position, initial_pos)
        self.assertNotEqual(self.floater.velocity, initial_vel)
        self.assertGreater(self.floater.velocity, 0) # Should be moving up

    def test_pivot_and_drain(self):
        """Test pivoting toggles orientation and drain_water resets water mass."""
        # Initial pivot state
        self.assertFalse(self.floater.pivoted)
        # Toggle pivot
        self.floater.pivot()
        self.assertTrue(self.floater.pivoted)
        self.floater.pivot()
        self.assertFalse(self.floater.pivoted)
        # Test water drainage
        self.floater.water_mass = 5.0
        self.floater.drain_water()
        self.assertEqual(self.floater.water_mass, 0.0)

if __name__ == '__main__':
    unittest.main()
