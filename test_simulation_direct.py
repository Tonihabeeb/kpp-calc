"""
Comprehensive automated testing suite for KPP simulation engine.
Replaces all previous testing scripts with a unified, direct approach.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(os.path.dirname(__file__), 'simulation'))

print("sys.path:", sys.path)

# Log sys.path to a file for debugging
with open("sys_path_debug.log", "w") as f:
    f.write("\n".join(sys.path))

from simulation.engine import SimulationEngine
import queue
import time
import threading
from simulation.components.floater import Floater  # Adjusted import path

# Set the PYTHONPATH environment variable to include the simulation directory
os.environ['PYTHONPATH'] = os.path.join(os.path.dirname(__file__), 'simulation') + os.pathsep + os.environ.get('PYTHONPATH', '')

def test_simulation_basic_functionality():
    """Test that simulation runs and produces data"""
    print("Testing basic simulation functionality...")
    
    # Create simulation with test parameters
    data_queue = queue.Queue()
    params = {
        'num_floaters': 4,
        'floater_volume': 0.3,
        'time_step': 0.1,
        'pulse_interval': 1.0
    }
    
    engine = SimulationEngine(params, data_queue)
    engine.reset()  # Initialize properly
    
    # Run simulation for a short time
    engine.running = True
    simulation_thread = threading.Thread(target=engine.run, daemon=True)
    simulation_thread.start()
    
    # Let it run for 5 seconds
    time.sleep(5)
    engine.stop()
    
    # Check results
    assert len(engine.data_log) > 0, "No data was logged"
    print(f"✓ Simulation generated {len(engine.data_log)} data points")
    
    # Check that floaters have realistic states
    final_state = engine.data_log[-1]
    assert 'floaters' in final_state, "No floater data in final state"
    print(f"✓ Final state contains floater data")
    
    # Check torque values
    torques = [entry.get('torque', 0) for entry in engine.data_log]
    max_torque = max(abs(t) for t in torques)
    print(f"✓ Max torque recorded: {max_torque:.2f} Nm")
    
    return True

def test_clutch_behavior():
    """Test clutch engagement/disengagement"""
    print("\nTesting clutch behavior...")
    
    data_queue = queue.Queue()
    params = {
        'num_floaters': 4,
        'clutch_tau_eng': 100,  # Low threshold for testing
        'time_step': 0.1
    }
    
    engine = SimulationEngine(params, data_queue)
    engine.reset()
    
    # Run simulation
    engine.running = True
    simulation_thread = threading.Thread(target=engine.run, daemon=True)
    simulation_thread.start()
    
    time.sleep(3)
    engine.stop()
    
    # Check clutch states
    clutch_states = [entry.get('clutch_state', '') for entry in engine.data_log if entry.get('clutch_state')]
    print(f"✓ Clutch states observed: {set(clutch_states)}")
    
    clutch_coefficients = [entry.get('clutch_c', 0) for entry in engine.data_log]
    max_clutch_c = max(clutch_coefficients) if clutch_coefficients else 0
    print(f"✓ Max clutch coefficient: {max_clutch_c:.2f}")
    
    return True

def test_torque_components():
    """Test that torque components are calculated"""
    print("\nTesting torque components...")
    
    data_queue = queue.Queue()
    engine = SimulationEngine({}, data_queue)
    engine.reset()
    
    # Run one simulation step
    engine.step(0.1)
    
    if engine.data_log:
        latest = engine.data_log[-1]
        base_buoy = latest.get('base_buoy_torque', None)
        pulse_torque = latest.get('pulse_torque', None)
        
        print(f"✓ Base buoyancy torque: {base_buoy}")
        print(f"✓ Pulse torque: {pulse_torque}")
        
        assert base_buoy is not None, "Base buoyancy torque not calculated"
        assert pulse_torque is not None, "Pulse torque not calculated"
    
    return True

def test_dissolution_loss():
    """Test dissolution loss and its effect on buoyancy"""
    print("\nTesting dissolution loss...")

    # Create a floater with test parameters
    floater = Floater(
        volume=0.3,
        mass=2.0,
        area=0.1,
        air_pressure=300000  # Pa
    )

    # Set initial fill progress to simulate a partially filled floater
    floater.fill_progress = 0.5

    # Initial buoyancy
    initial_buoyancy = floater.compute_buoyant_force()

    # Simulate for 10 timesteps
    dt = 0.1  # 0.1 seconds per timestep
    for _ in range(10):
        floater.update(dt)

    # Final buoyancy
    final_buoyancy = floater.compute_buoyant_force()

    # Check that buoyancy decreases over time
    assert final_buoyancy < initial_buoyancy, "Buoyancy did not decrease as expected"
    print(f"✓ Buoyancy decreased from {initial_buoyancy:.2f} N to {final_buoyancy:.2f} N")

    # Check that dissolved air fraction increased
    assert floater.dissolved_air_fraction > 0, "Dissolved air fraction did not increase"
    print(f"✓ Dissolved air fraction increased to {floater.dissolved_air_fraction:.4f}")

    return True

def test_added_mass_inertia():
    """Test that acceleration decreases with higher added mass."""
    print("\nTesting added mass inertia...")

    from simulation.components.floater import Floater

    # Create two floaters with different added masses
    floater_low_mass = Floater(volume=0.3, mass=2.0, area=0.1, added_mass=1.0)
    floater_high_mass = Floater(volume=0.3, mass=2.0, area=0.1, added_mass=5.0)

    # Apply the same net force to both floaters
    net_force = 10.0  # N

    # Mock the net force by overriding the compute_buoyant_force method
    floater_low_mass.compute_buoyant_force = lambda: net_force
    floater_high_mass.compute_buoyant_force = lambda: net_force

    # Calculate acceleration for low added mass
    floater_low_mass.update(0.1)
    # Use absolute acceleration magnitude
    acceleration_low = abs(floater_low_mass.velocity) / 0.1

    # Calculate acceleration for high added mass
    floater_high_mass.update(0.1)
    acceleration_high = abs(floater_high_mass.velocity) / 0.1

    # Assert that acceleration is lower for higher added mass
    assert acceleration_high < acceleration_low, "Acceleration did not decrease with higher added mass"
    print(f"✓ Acceleration decreased with higher added mass: {acceleration_low:.2f} m/s² > {acceleration_high:.2f} m/s²")

    return True

def run_all_tests():
    """Run all tests and report results"""
    tests = [
        test_simulation_basic_functionality,
        test_clutch_behavior, 
        test_torque_components,
        test_dissolution_loss,
        test_added_mass_inertia
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
            print(f"✓ {test.__name__} PASSED")
        except Exception as e:
            failed += 1
            print(f"✗ {test.__name__} FAILED: {e}")
    
    print(f"\n--- Test Results ---")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Total: {passed + failed}")
    
    return failed == 0

if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
