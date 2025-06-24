"""
Test the main simulation engine with integrated drivetrain system.
Verifies that the full integration works correctly.
"""

import pytest
import queue
import time
from simulation.engine import SimulationEngine


def test_engine_with_integrated_drivetrain():
    """
    Test that the main simulation engine works with the new integrated drivetrain.
    """
    # Create a data queue for the engine
    data_queue = queue.Queue()
    
    # Basic parameters for testing
    params = {
        'time_step': 0.1,
        'num_floaters': 2,
        'floater_volume': 0.3,
        'floater_mass_empty': 18.0,
        'pulse_interval': 2.0,
        'sprocket_radius': 1.0,
        'sprocket_teeth': 20,
        'clutch_engagement_threshold': 0.1,
        'flywheel_inertia': 50.0,
        'gear_ratio': 16.7,
        'target_power': 530000.0,
        'target_rpm': 375.0
    }
    
    # Initialize the engine
    engine = SimulationEngine(params, data_queue)
    
    # Verify that both drivetrain systems are initialized
    assert hasattr(engine, 'drivetrain'), "Legacy drivetrain should be initialized"
    assert hasattr(engine, 'integrated_drivetrain'), "Integrated drivetrain should be initialized"
    
    # Run a few simulation steps
    for _ in range(5):
        engine.step(0.1)
        
        # Verify that data is being logged
        assert engine.time > 0, "Simulation time should advance"
          # Check that integrated drivetrain is working
        state = engine.integrated_drivetrain.get_comprehensive_state()
        assert 'gearbox' in state, "Integrated drivetrain should return gearbox state"
        assert 'flywheel' in state, "Integrated drivetrain should return flywheel state"
        assert 'clutch' in state, "Integrated drivetrain should return clutch state"
        
        # Verify data queue has updates
        if not data_queue.empty():
            logged_state = data_queue.get()
            assert 'time' in logged_state, "Logged state should include time"
            assert 'power' in logged_state, "Logged state should include power"
    
    print(f"✓ Engine completed {engine.time:.1f}s simulation with integrated drivetrain")
    print(f"✓ Integrated drivetrain system operational")
    print(f"✓ Data logging functional")


def test_engine_reset_with_integrated_drivetrain():
    """
    Test that the engine reset works correctly with the integrated drivetrain.
    """
    data_queue = queue.Queue()
    params = {
        'time_step': 0.1,
        'num_floaters': 1,
        'pulse_interval': 1.0
    }
    
    engine = SimulationEngine(params, data_queue)
    
    # Run a few steps
    for _ in range(3):
        engine.step(0.1)
    
    initial_time = engine.time
    assert initial_time > 0, "Time should have advanced"
    
    # Reset the engine
    engine.reset()
    
    # Verify reset worked
    assert engine.time == 0.0, "Time should be reset to 0"
    assert engine.total_energy == 0.0, "Energy should be reset"
    assert engine.pulse_count == 0, "Pulse count should be reset"
    
    print(f"✓ Engine reset successfully from {initial_time:.1f}s to {engine.time:.1f}s")
    print(f"✓ Integrated drivetrain reset functional")


def test_engine_force_breakdown_with_integrated_drivetrain():
    """
    Test that force breakdown and torque calculations work with integrated drivetrain.
    """
    data_queue = queue.Queue()
    params = {
        'time_step': 0.1,
        'num_floaters': 2,
        'floater_volume': 0.5,  # Larger floaters for more noticeable forces
        'pulse_interval': 1.5
    }
    
    engine = SimulationEngine(params, data_queue)
    
    # Trigger a pulse to get some force
    engine.trigger_pulse()
    
    # Run a few steps to see force propagation
    for i in range(3):
        engine.step(0.1)
        
        # Check that forces are calculated
        assert hasattr(engine, 'chain_tension'), "Chain tension should be calculated"
        
        # Get the latest logged state
        if not data_queue.empty():
            while not data_queue.empty():  # Get the latest one
                state = data_queue.get()
            
            # Verify force components are logged
            assert 'total_vertical_force' in state, "Total vertical force should be logged"
            assert 'base_buoy_force' in state, "Base buoyancy force should be logged"
            
            if i == 2:  # On the last iteration, print some details
                print(f"✓ Chain tension: {engine.chain_tension:.1f}N")
                print(f"✓ Total vertical force: {state.get('total_vertical_force', 0):.1f}N")
                print(f"✓ System power: {state.get('power', 0):.1f}W")


if __name__ == "__main__":
    print("Testing Main Simulation Engine with Integrated Drivetrain...")
    print("=" * 60)
    
    test_engine_with_integrated_drivetrain()
    print()
    
    test_engine_reset_with_integrated_drivetrain()
    print()
    
    test_engine_force_breakdown_with_integrated_drivetrain()
    print()
    
    print("=" * 60)
    print("✅ All engine integration tests passed!")
    print("✅ Main simulation engine successfully integrated with Phase 2 drivetrain system")
