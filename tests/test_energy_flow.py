import unittest
import queue
from simulation.engine import SimulationEngine

class TestEnergyFlow(unittest.TestCase):
    """Unit tests for tracking energy losses and net energy balance."""
    def test_energy_loss_logging(self):
        # Setup simulation engine with one floater and known time step
        data_q = queue.Queue()
        params = {
            'num_floaters': 1,
            'time_step': 0.1
        }
        engine = SimulationEngine(params, data_q)
        # Monkey patch power output to a fixed value
        engine.generator.calculate_power_output = lambda omega: 100.0

        # Ensure drivetrain speed does not affect calculation
        engine.drivetrain.omega_flywheel = 0.0

        # Perform one simulation step to log state
        engine.step(engine.dt)

        # Retrieve logged state
        state = engine.collect_state()

        # Check that loss keys are present
        self.assertIn('drag_loss', state)
        self.assertIn('dissolution_loss', state)
        self.assertIn('venting_loss', state)
        self.assertIn('net_energy', state)

        # Initial floaters are stationary, so drag_loss should be zero
        self.assertEqual(state['drag_loss'], 0.0)
        # Dissolution and venting are not yet modeled, so zero
        self.assertEqual(state['dissolution_loss'], 0.0)
        self.assertEqual(state['venting_loss'], 0.0)

        # Net energy should equal power_output minus losses
        expected_net = state['power'] - (state['drag_loss'] + state['dissolution_loss'] + state['venting_loss'])
        self.assertAlmostEqual(state['net_energy'], expected_net)

if __name__ == '__main__':
    unittest.main()
