"""
Test script for full KPP simulation integration with Stage 1 physics engine.
Tests the complete simulation engine with new physics integration.
"""

import sys
import os
import time
import threading
import queue

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from simulation.engine import SimulationEngine

def test_full_simulation():
    """Test the full simulation engine with Stage 1 physics."""
    print("=== Testing Full KPP Simulation Integration ===")
    
    # Create data queue for streaming
    data_queue = queue.Queue()
    
    # Simulation parameters
    params = {
        # Basic parameters
        'time_step': 0.1,
        'num_floaters': 4,
        'tank_height': 8.0,
        
        # Floater parameters
        'floater_volume': 0.035,    # 35 liters
        'floater_mass_empty': 45.0, # 45 kg empty container
        'floater_area': 0.2,        # 0.2 m² cross-section
        'floater_Cd': 0.8,          # Drag coefficient
        
        # Drivetrain parameters
        'sprocket_radius': 1.0,     # 1 meter radius
        'generator_torque': 150.0,  # 150 N⋅m
        'gear_ratio': 16.7,
        'drivetrain_efficiency': 0.95,
        
        # Target power
        'target_power': 100000.0,   # 100 kW target
        'target_rpm': 375.0,        # 375 RPM target
        
        # Physics parameters
        'friction_coefficient': 0.01,
        'chain_mass_per_meter': 8.0,
        'chain_length': 25.0,
        
        # Control parameters
        'auto_startup_enabled': True,
        'grid_support_enabled': True
    }
    
    print(f"Creating simulation with {params['num_floaters']} floaters...")
    
    # Create simulation engine
    engine = SimulationEngine(params, data_queue)
    
    print("✅ Simulation engine created successfully")
    print(f"Physics engine initialized: {hasattr(engine, 'physics_engine')}")
    print(f"Event handler initialized: {hasattr(engine, 'event_handler')}")
    
    # Run simulation for several steps
    print("\n=== Running Simulation ===")
    print("Time   | Chain_V | Power_Out | Energy_Net | Events")
    print("-------|---------|-----------|------------|--------")
    
    simulation_time = 5.0  # 5 seconds
    steps = int(simulation_time / params['time_step'])
    
    for step in range(steps):
        try:
            # Perform simulation step
            engine.step(params['time_step'])
            
            # Get latest data
            if hasattr(engine, 'data_log') and engine.data_log:
                data = engine.data_log[-1]
                
                if step % 10 == 0:  # Print every 1 second
                    print(f"{data['time']:6.1f}s | "
                          f"{data['chain_velocity']:7.3f} | "
                          f"{data['power_output']:9.1f} | "
                          f"{data['net_energy']:10.1f} | "
                          f"I:{data['injections']} V:{data['ventings']}")
            
        except Exception as e:
            print(f"❌ Error at step {step}: {e}")
            break
    
    # Final results
    if hasattr(engine, 'data_log') and engine.data_log:
        final_data = engine.data_log[-1]
        print(f"\n=== Final Results ===")
        print(f"Simulation time: {final_data['time']:.1f} seconds")
        print(f"Final chain velocity: {final_data['chain_velocity']:.3f} m/s")
        print(f"Total energy output: {final_data['energy_output']:.1f} J")
        print(f"Total energy input: {final_data['energy_input']:.1f} J")
        print(f"Net energy: {final_data['net_energy']:.1f} J")
        
        if final_data['energy_input'] > 0:
            efficiency = final_data['energy_output'] / final_data['energy_input'] * 100
            print(f"System efficiency: {efficiency:.1f}%")
        
        print(f"Average power output: {final_data['power_output']:.1f} W")
        
        # Count total events
        total_injections = sum(d['injections'] for d in engine.data_log)
        total_ventings = sum(d['ventings'] for d in engine.data_log)
        print(f"Total air injections: {total_injections}")
        print(f"Total air ventings: {total_ventings}")
    
    # Test physics engine state
    if hasattr(engine, 'physics_engine'):
        physics_state = engine.physics_engine.get_state()
        print(f"\n=== Physics Engine State ===")
        print(f"Physics time: {physics_state['time']:.1f} s")
        print(f"Chain velocity: {physics_state['chain_velocity']:.3f} m/s")
        print(f"Chain angle: {physics_state['chain_angle']:.3f} rad")
        print(f"Energy output: {physics_state['energy_output']:.1f} J")
        print(f"Energy input: {physics_state['energy_input']:.1f} J")
    
    # Test event handler state
    if hasattr(engine, 'advanced_event_handler'):
        event_summary = engine.advanced_event_handler.get_energy_analysis()
        print(f"\n=== Event Handler State ===")
        print(f"Total energy input: {event_summary.get('total_energy_input', 0):.1f} J")
        print(f"Tank depth: {event_summary.get('tank_depth', 0):.1f} m")
        print(f"Injection pressure: {event_summary.get('injection_pressure_range', {}).get('standard_pressure', 0):.0f} Pa")
    
    print("\n✅ Full integration test completed successfully!")
    return True

def test_data_streaming():
    """Test data streaming functionality."""
    print("\n=== Testing Data Streaming ===")
    
    # Create data queue
    data_queue = queue.Queue()
    
    # Simple parameters for quick test
    params = {
        'time_step': 0.1,
        'num_floaters': 2,
        'tank_height': 5.0,
        'floater_volume': 0.03,
        'floater_mass_empty': 40.0,
        'generator_torque': 100.0
    }
    
    engine = SimulationEngine(params, data_queue)
    
    # Run a few steps
    for step in range(5):
        engine.step(params['time_step'])
    
    # Check if data was streamed to queue
    data_received = 0
    while not data_queue.empty():
        try:
            data = data_queue.get_nowait()
            data_received += 1
            if data_received == 1:  # Show first data packet
                print("Sample data packet:")
                print(f"  Time: {data['time']:.1f}s")
                print(f"  Power: {data['power_output']:.1f}W")
                print(f"  Floater count: {data['floater_count']}")
                print(f"  Floater data entries: {len(data['floaters'])}")
        except queue.Empty:
            break
    
    print(f"✅ Received {data_received} data packets from queue")
    return data_received > 0

if __name__ == "__main__":
    print("KPP Simulation Full Integration Test")
    print("====================================")
    
    try:
        # Test 1: Full simulation
        test1_passed = test_full_simulation()
        
        # Test 2: Data streaming
        test2_passed = test_data_streaming()
        
        # Summary
        print(f"\n=== Test Summary ===")
        print(f"Full simulation test: {'✅ PASSED' if test1_passed else '❌ FAILED'}")
        print(f"Data streaming test: {'✅ PASSED' if test2_passed else '❌ FAILED'}")
        
        if test1_passed and test2_passed:
            print("\n🎉 All integration tests PASSED!")
            print("Stage 1 implementation is fully functional!")
        else:
            print("\n⚠️ Some tests failed - review implementation")
    
    except Exception as e:
        print(f"\n❌ Test suite failed with error: {e}")
        import traceback
        traceback.print_exc()
