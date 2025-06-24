"""
Unit tests for the refactored PneumaticSystem.
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from simulation.components.pneumatics import PneumaticSystem
from simulation.components.floater import Floater

class TestPneumaticSystem(unittest.TestCase):
    def setUp(self):
        """Set up a default pneumatic system and a floater."""
        self.pneumatics = PneumaticSystem(target_pressure=5.0, tank_pressure=5.0)
        self.floater = Floater(volume=0.3, mass=18.0, area=0.035)

    def test_initialization(self):
        """Test correct initialization of the pneumatic system."""
        self.assertEqual(self.pneumatics.tank_pressure, 5.0)
        self.assertFalse(self.pneumatics.compressor_on)

    def test_trigger_injection_success(self):
        """Test that triggering an injection successfully starts the floater filling."""
        success = self.pneumatics.trigger_injection(self.floater)
        self.assertTrue(success)
        self.assertTrue(self.floater.is_filled)
        self.assertLess(self.pneumatics.tank_pressure, 5.0)

    def test_trigger_injection_failure(self):
        """Test that injection fails if tank pressure is too low."""
        self.pneumatics.tank_pressure = 1.0
        success = self.pneumatics.trigger_injection(self.floater)
        self.assertFalse(success)
        self.assertFalse(self.floater.is_filled)

    def test_compressor_auto_on(self):
        """Test that the compressor turns on automatically when pressure is low."""
        self.pneumatics.tank_pressure = 4.0
        self.pneumatics.update(dt=0.1)
        self.assertTrue(self.pneumatics.compressor_on)

    def test_compressor_auto_off(self):
        """Test that the compressor turns off when target pressure is reached."""
        self.pneumatics.tank_pressure = 4.9
        self.pneumatics.compressor_on = True
        self.pneumatics.update(dt=1.0) # Give it time to increase pressure
        self.pneumatics.update(dt=1.0)
        self.assertFalse(self.pneumatics.compressor_on)
        self.assertEqual(self.pneumatics.tank_pressure, 5.0)

    def test_vent_air(self):
        """Test that venting air correctly updates the floater state."""
        self.floater.set_filled(True)
        self.pneumatics.vent_air(self.floater)
        self.assertFalse(self.floater.is_filled)

if __name__ == '__main__':
    unittest.main()
