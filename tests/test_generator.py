"""
Unit tests for the Generator class.
"""
import unittest
from simulation.components.generator import Generator

class TestGenerator(unittest.TestCase):
    def test_calculate_power(self):
        gen = Generator(efficiency=0.9)
        power = gen.calculate_power(100, 10)
        self.assertAlmostEqual(power, 100 * 10 * 0.9)

    def test_update_params(self):
        gen = Generator(efficiency=0.9)
        gen.update_params({'efficiency': 0.8})
        self.assertEqual(gen.efficiency, 0.8)

    def test_update_stub(self):
        gen = Generator(efficiency=0.9)
        # Should not raise
        gen.update(0.1, 100)

if __name__ == "__main__":
    unittest.main()
