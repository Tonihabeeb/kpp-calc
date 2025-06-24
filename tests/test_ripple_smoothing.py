import unittest
import math
from simulation.components.floater import Floater
from config.config import G

class TestRippleSmoothing(unittest.TestCase):
    def test_ripple_amplitude_decreases_with_more_floaters(self):
        """Verify that torque ripple amplitude decreases as we add more floaters."""
        num_list = [1, 3, 5]
        amplitudes = []
        for n in num_list:
            torques = []
            # Create floaters evenly phased around the chain
            floaters = [Floater(volume=0.3, mass=18.0, area=0.035, added_mass=0.0, phase_offset=2*math.pi*i/n)
                        for i in range(n)]
            # Sample one full revolution
            steps = int((2*math.pi)/0.1) + 1
            for k in range(steps):
                theta = k * 0.1
                total_torque = 0.0
                for f in floaters:
                    # Set theta with phase offset
                    f.theta = theta + f.phase_offset
                    x, _ = f.get_cartesian_position()
                    # Vertical force is constant gravity for empty floaters
                    vf = f.get_vertical_force()
                    total_torque += vf * x
                torques.append(total_torque)
            amplitudes.append(max(torques) - min(torques))
        # Check that each subsequent amplitude is less than or equal to the previous
        tol = 1e-12
        for i in range(len(amplitudes) - 1):
            prev_amp = amplitudes[i]
            next_amp = amplitudes[i+1]
            # Allow tiny floating-point noise tolerance
            self.assertTrue(next_amp <= prev_amp + tol,
                            f"Amplitude did not decrease (within tol): {next_amp} > {prev_amp}")

if __name__ == '__main__':
    unittest.main()
