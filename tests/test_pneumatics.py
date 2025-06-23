"""
Unit tests for the PneumaticSystem class.
"""
import unittest
from simulation.components.pneumatics import PneumaticSystem

class DummyFloater:
    def __init__(self):
        self.filled = False
        self.volume = 0.05
    def set_filled(self, filled):
        self.filled = filled

class TestPneumaticSystem(unittest.TestCase):
    def test_inject_air(self):
        pneu = PneumaticSystem(tank_pressure=2.0, tank_volume=0.1)
        floater = DummyFloater()
        pneu.inject_air(floater)
        self.assertTrue(floater.filled)
        self.assertLess(pneu.tank_pressure, 2.0)
        self.assertTrue(pneu.compressor_on)

    def test_vent_air(self):
        pneu = PneumaticSystem()
        floater = DummyFloater()
        floater.filled = True
        pneu.vent_air(floater)
        self.assertFalse(floater.filled)

    def test_update_compressor(self):
        pneu = PneumaticSystem(tank_pressure=2.0, target_pressure=2.2, tank_volume=0.1)
        pneu.compressor_on = True
        pneu.update(1.0)
        self.assertGreaterEqual(pneu.tank_pressure, 2.0)
        # Should turn off if target reached
        pneu.tank_pressure = 2.2
        pneu.compressor_on = True
        pneu.update(1.0)
        self.assertFalse(pneu.compressor_on)

if __name__ == "__main__":
    unittest.main()
