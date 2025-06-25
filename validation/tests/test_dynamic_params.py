import unittest
from simulation.engine import SimulationEngine
import queue

class TestDynamicParameterTuning(unittest.TestCase):
    def test_update_drag_coefficient(self):
        """Verify that updating drag coefficient dynamically affects drag force calculation."""
        data_q = queue.Queue()
        params = {
            'num_floaters': 1,
            'floater_Cd': 1.0,
            'floater_area': 0.5,
            'time_step': 0.1
        }
        engine = SimulationEngine(params, data_q)
        engine.reset()
        floater = engine.floaters[0]
        # Set filled to ensure drag is computed
        floater.set_filled(True)
        floater.velocity = 2.0
        # Compute initial drag force
        initial_drag = floater.compute_drag_force()
        # Update parameters: change drag coeff
        new_Cd = 2.0
        engine.update_params({'floater_Cd': new_Cd})
        # Floater.Cd should be updated
        self.assertEqual(floater.Cd, new_Cd)
        # New drag force should reflect updated Cd (doubling Cd roughly doubles drag)
        new_drag = floater.compute_drag_force()
        self.assertAlmostEqual(new_drag, initial_drag * (new_Cd/1.0), places=5)

    def test_update_air_fill_time(self):
        """Verify that updating air fill time dynamically affects filling progress."""
        data_q = queue.Queue()
        params = {'num_floaters': 1, 'air_fill_time': 1.0, 'time_step': 0.1}
        engine = SimulationEngine(params, data_q)
        engine.reset()
        floater = engine.floaters[0]
        # Start filling with default air_fill_time
        floater.start_filling()
        floater.update(engine.dt)
        progress_default = floater.fill_progress
        # Update fill time to shorter time -> faster fill
        engine.update_params({'air_fill_time': 0.5})
        # Reset fill progress to zero
        floater.fill_progress = 0.0
        floater.start_filling()
        floater.update(engine.dt)
        progress_new = floater.fill_progress
        self.assertGreater(progress_new, progress_default)

if __name__ == '__main__':
    unittest.main()
