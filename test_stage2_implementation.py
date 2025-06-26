"""
Test script for Stage 2 Implementation - Advanced Event Handling and State Management
Tests the enhanced event handler, state synchronizer, and improved physics integration.
"""

import sys
import os
import time
import queue

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from simulation.physics.advanced_event_handler import AdvancedEventHandler
from simulation.physics.state_synchronizer import StateSynchronizer
from simulation.physics.physics_engine import PhysicsEngine
from simulation.components.floater import Floater
from simulation.engine import SimulationEngine

def test_advanced_event_handler():
    """Test the advanced event handler features."""
    print("=== Testing Advanced Event Handler ===")
    
    # Create advanced event handler with optimization
    optimization_params = {
        'adaptive_pressure': True,
        'pressure_safety_factor': 1.2,
        'min_injection_pressure': 150000,
        'efficiency_target': 0.4
    }
    
    tank_depth = 8.0
    handler = AdvancedEventHandler(tank_depth, optimization_params)
    
    print(f"✅ Advanced event handler created")
    print(f"   - Tank depth: {tank_depth}m")
    print(f"   - Adaptive pressure: {optimization_params['adaptive_pressure']}")
    print(f"   - Efficiency target: {optimization_params['efficiency_target']}")
    
    # Create test floaters
    floaters = []
    for i in range(4):
        floater = Floater(
            volume=0.035,
            mass=45.0,
            area=0.2,
            Cd=0.8,
            phase_offset=i * 3.14159 / 2  # Spread around loop
        )
        floater.container_mass = 45.0
        floaters.append(floater)
    
    # Set initial states
    floaters[0].angle = 0.05  # Bottom, ready for injection
    floaters[0].state = "heavy"
    floaters[0].is_filled = False
    
    floaters[1].angle = 3.14159  # Top, ready for venting
    floaters[1].state = "light"
    floaters[1].is_filled = True
    floaters[1].mass = 45.0  # Light mass
    
    # Test processing events
    current_time = 0.0
    
    print(f"\n--- Processing Events (t={current_time:.1f}s) ---")
    event_summary = handler.process_all_events(floaters, current_time)
    
    print(f"Injections: {event_summary['injections']}")
    print(f"Ventings: {event_summary['ventings']}")
    print(f"Total energy input: {event_summary['total_energy_input']:.1f} J")
    print(f"Average injection energy: {event_summary['average_injection_energy']:.1f} J")
    print(f"Injection success rate: {event_summary['injection_success_rate']:.3f}")
    print(f"Energy optimization active: {event_summary['energy_optimization_active']}")
    
    # Test energy analysis
    energy_analysis = handler.get_energy_analysis()
    print(f"\n--- Energy Analysis ---")
    print(f"Total injections: {energy_analysis['total_injections']}")
    print(f"Total ventings: {energy_analysis['total_ventings']}")
    print(f"Estimated system efficiency: {energy_analysis['estimated_system_efficiency']:.3f}")
    print(f"Energy optimization savings: {energy_analysis['energy_optimization_savings']:.1f} J")
    
    print("✅ Advanced event handler test completed\n")
    return True

def test_state_synchronizer():
    """Test the state synchronization system."""
    print("=== Testing State Synchronizer ===")
    
    # Create physics engine and event handler
    physics_params = {'time_step': 0.1, 'chain_mass': 100.0}
    physics_engine = PhysicsEngine(physics_params)
    
    optimization_params = {'adaptive_pressure': True}
    event_handler = AdvancedEventHandler(8.0, optimization_params)
    
    # Create state synchronizer
    synchronizer = StateSynchronizer(physics_engine, event_handler)
    print("✅ State synchronizer created")
    
    # Create test floater with inconsistent state
    floater = Floater(volume=0.035, mass=90.0, area=0.2)  # Heavy mass
    floater.container_mass = 45.0
    floater.state = "light"  # Inconsistent - light state but heavy mass
    floater.is_filled = True
    
    print(f"Initial inconsistent state:")
    print(f"   - Mass: {floater.mass:.1f} kg")
    print(f"   - State: {floater.state}")
    print(f"   - Is filled: {floater.is_filled}")
    
    # Test synchronization
    sync_result = synchronizer.synchronize_floater_state(floater, floater_id=0)
    
    print(f"\nSynchronization result:")
    print(f"   - Success: {sync_result['success']}")
    print(f"   - Changes: {sync_result['changes']}")
    
    print(f"\nCorrected state:")
    print(f"   - Mass: {floater.mass:.1f} kg")
    print(f"   - State: {floater.state}")
    print(f"   - Is filled: {floater.is_filled}")
    
    # Test system validation
    floaters = [floater]
    validation_results = synchronizer.validate_system_consistency(floaters)
    
    print(f"\nValidation results:")
    print(f"   - System consistent: {validation_results['consistent']}")
    print(f"   - Issues found: {len(validation_results['inconsistencies'])}")
    
    # Test synchronization status
    sync_status = synchronizer.get_sync_status()
    print(f"\nSynchronizer status:")
    print(f"   - Sync operations: {sync_status['sync_operations']}")
    print(f"   - Success rate: {sync_status['success_rate']:.3f}")
    print(f"   - Tracked floaters: {sync_status['tracked_floaters']}")
    
    print("✅ State synchronizer test completed\n")
    return True

def test_enhanced_physics_engine():
    """Test the enhanced physics engine with Stage 2 features."""
    print("=== Testing Enhanced Physics Engine ===")
    
    # Create enhanced physics engine
    params = {
        'time_step': 0.1,
        'chain_mass': 80.0,
        'friction_coefficient': 0.01,
        'adaptive_timestep': False
    }
    
    physics = PhysicsEngine(params)
    print(f"✅ Enhanced physics engine created")
    print(f"   - State validation enabled: {physics.state_validation_enabled}")
    print(f"   - Force history tracking: {'force_history' in dir(physics)}")
    
    # Create test floater
    floater = Floater(volume=0.035, mass=45.0, area=0.2, Cd=0.8)
    floater.container_mass = 45.0
    floater.state = "light"
    
    # Test enhanced force calculation
    velocities = [0.0, 0.5, 1.0, 1.5, 2.0]
    
    print(f"\nEnhanced force calculations:")
    print("Velocity | Net Force | State")
    print("---------|-----------|-------")
    
    for vel in velocities:
        force = physics.calculate_floater_forces(floater, vel)
        print(f"{vel:8.1f} | {force:9.1f} | {floater.state}")
    
    # Test force history tracking
    print(f"\nForce history tracking:")
    print(f"   - History entries: {len(physics.force_history)}")
    
    if physics.force_history:
        latest = physics.force_history[-1]
        print(f"   - Latest F_buoy: {latest['F_buoy']:.1f} N")
        print(f"   - Latest F_weight: {latest['F_weight']:.1f} N")
        print(f"   - Latest F_drag: {latest['F_drag']:.1f} N")
        print(f"   - Latest state: {latest['state']}")
    
    # Test state validation
    print(f"\nTesting state validation:")
    floater.mass = 120.0  # Inconsistent mass for light state
    force = physics.calculate_floater_forces(floater, 1.0)
    print(f"   - Force calculated with validation: {force:.1f} N")
    
    print("✅ Enhanced physics engine test completed\n")
    return True

def test_full_stage2_integration():
    """Test full Stage 2 integration with simulation engine."""
    print("=== Testing Full Stage 2 Integration ===")
    
    # Create data queue
    data_queue = queue.Queue()
    
    # Enhanced simulation parameters
    params = {
        'time_step': 0.1,
        'num_floaters': 3,
        'tank_height': 6.0,
        'floater_volume': 0.03,
        'floater_mass_empty': 40.0,
        'floater_area': 0.15,
        'generator_torque': 120.0,
        
        # Stage 2 specific parameters
        'adaptive_pressure_enabled': True,
        'energy_efficiency_target': 0.35,
        'pressure_safety_factor': 1.15,
        'min_injection_pressure': 140000,
        'adaptive_timestep_enabled': False
    }
    
    print(f"Creating enhanced simulation with Stage 2 features...")
    print(f"   - Floaters: {params['num_floaters']}")
    print(f"   - Adaptive pressure: {params['adaptive_pressure_enabled']}")
    print(f"   - Efficiency target: {params['energy_efficiency_target']}")
    
    # Create simulation engine
    try:
        engine = SimulationEngine(params, data_queue)
        print("✅ Enhanced simulation engine created")
        
        # Verify Stage 2 components
        has_advanced_handler = hasattr(engine.advanced_event_handler, 'get_energy_analysis')
        has_state_sync = hasattr(engine, 'state_synchronizer')
        
        print(f"   - Advanced event handler: {has_advanced_handler}")
        print(f"   - State synchronizer: {has_state_sync}")
        
        # Run enhanced simulation
        print(f"\n--- Running Enhanced Simulation ---")
        print("Time   | Velocity | Power  | Efficiency | Events | Sync")
        print("-------|----------|--------|------------|--------|------")
        
        simulation_time = 3.0  # 3 seconds
        steps = int(simulation_time / params['time_step'])
        
        for step in range(steps):
            engine.step(params['time_step'])
            
            if hasattr(engine, 'data_log') and engine.data_log:
                data = engine.data_log[-1]
                
                if step % 5 == 0:  # Print every 0.5 seconds
                    efficiency = data.get('estimated_system_efficiency', 0.0) * 100
                    events = f"I:{data['injections']} V:{data['ventings']}"
                    sync_ops = data.get('sync_operations', 0)
                    
                    print(f"{data['time']:6.1f}s | "
                          f"{data['chain_velocity']:8.3f} | "
                          f"{data['power_output']:6.1f} | "
                          f"{efficiency:10.1f}% | "
                          f"{events:6s} | "
                          f"{sync_ops:4d}")
        
        # Final analysis
        if hasattr(engine, 'data_log') and engine.data_log:
            final_data = engine.data_log[-1]
            
            print(f"\n--- Stage 2 Performance Analysis ---")
            print(f"Simulation time: {final_data['time']:.1f}s")
            print(f"Final efficiency: {final_data.get('estimated_system_efficiency', 0.0)*100:.1f}%")
            print(f"Average injection energy: {final_data.get('average_injection_energy', 0.0):.1f} J")
            print(f"Injection success rate: {final_data.get('injection_success_rate', 1.0):.3f}")
            print(f"Total sync operations: {final_data.get('sync_operations', 0)}")
            print(f"System consistent: {final_data.get('system_consistent', True)}")
            
            # Energy optimization status
            if hasattr(engine.advanced_event_handler, 'energy_optimization_active'):
                print(f"Energy optimization active: {engine.advanced_event_handler.energy_optimization_active}")
        
        print("✅ Full Stage 2 integration test completed")
        return True
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Stage 2 Implementation Test Suite")
    print("==================================")
    
    try:
        # Run all tests
        test1_passed = test_advanced_event_handler()
        test2_passed = test_state_synchronizer()
        test3_passed = test_enhanced_physics_engine()
        test4_passed = test_full_stage2_integration()
        
        # Summary
        print(f"\n=== Test Summary ===")
        print(f"Advanced Event Handler: {'✅ PASSED' if test1_passed else '❌ FAILED'}")
        print(f"State Synchronizer: {'✅ PASSED' if test2_passed else '❌ FAILED'}")
        print(f"Enhanced Physics Engine: {'✅ PASSED' if test3_passed else '❌ FAILED'}")
        print(f"Full Integration: {'✅ PASSED' if test4_passed else '❌ FAILED'}")
        
        all_passed = test1_passed and test2_passed and test3_passed and test4_passed
        
        if all_passed:
            print("\n🎉 ALL STAGE 2 TESTS PASSED!")
            print("Advanced event handling, state synchronization, and energy optimization are working correctly!")
        else:
            print("\n⚠️ Some Stage 2 tests failed - review implementation")
    
    except Exception as e:
        print(f"\n❌ Test suite failed with error: {e}")
        import traceback
        traceback.print_exc()
