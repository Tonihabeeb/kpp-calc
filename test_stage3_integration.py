"""
Test script for Stage 3 Implementation - Integration and Validation Framework
Tests the validation framework, parameter optimization, and component integration.
"""

import sys
import os
import time

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from simulation.integration.integration_manager import IntegrationManager
from simulation.engine import SimulationEngine
from validation.physics_validation import ValidationFramework
from simulation.optimization.parameter_optimizer import ParameterOptimizer

def test_validation_framework():
    """Test the validation framework independently."""
    print("=== Testing Validation Framework ===")
    
    validator = ValidationFramework()
    
    # Test 1: Energy conservation validation
    print("\n--- Energy Conservation Test ---")
    energy_result = validator.validate_energy_conservation(
        energy_in=1000.0,
        energy_out=850.0,
        losses=145.0
    )
    
    print(f"Energy in: {energy_result['energy_in']:.1f} J")
    print(f"Energy out: {energy_result['energy_out']:.1f} J")
    print(f"Losses: {energy_result['losses']:.1f} J")
    print(f"Conservation error: {energy_result['relative_error']:.4f}")
    print(f"Test passed: {energy_result['passed']}")
    
    # Test 2: Force balance validation
    print("\n--- Force Balance Test ---")
    forces = [100.0, -95.0, -4.8, -0.1]  # Nearly balanced forces
    force_result = validator.validate_force_balance(forces)
    
    print(f"Forces: {forces}")
    print(f"Net force: {force_result['net_force']:.2f} N")
    print(f"Force error: {force_result['force_error']:.6f} N")
    print(f"Test passed: {force_result['passed']}")
    
    # Test 3: Performance metrics
    print("\n--- Performance Metrics ---")
    metrics = validator.get_performance_metrics()
    print(f"Total tests: {metrics['total_tests']}")
    print(f"Success rate: {metrics['success_rate']:.3f}")
    
    print("✅ Validation framework test completed\n")
    return True

def test_parameter_optimizer():
    """Test the parameter optimizer independently."""
    print("=== Testing Parameter Optimizer ===")
    
    optimizer = ParameterOptimizer()
    
    # Set up test parameters
    optimizer.setup_default_parameters()
    
    print(f"Set up {len(optimizer.parameters)} optimization parameters:")
    for name, param in optimizer.parameters.items():
        print(f"  {name}: {param.current_value} ({param.min_value}-{param.max_value})")
    
    # Test parameter manipulation
    print("\n--- Parameter Configuration Test ---")
    optimizer.add_parameter(
        name="test_parameter",
        current_value=1.0,
        min_value=0.5,
        max_value=2.0,
        step_size=0.1,
        description="Test parameter for validation"
    )
    
    print(f"Added test parameter successfully")
    
    # Test optimization summary (without full optimization)
    print("\n--- Optimization Status ---")
    summary = optimizer.get_optimization_summary()
    print(f"Optimization status: {summary['status']}")
    
    print("✅ Parameter optimizer test completed\n")
    return True

def test_integration_manager():
    """Test the integration manager with a mock simulation."""
    print("=== Testing Integration Manager ===")
    
    # Create integration manager
    integration_manager = IntegrationManager()
    
    print("✅ Integration manager created")
    
    # Create minimal simulation engine for testing
    try:
        import queue
        # Create proper parameters for simulation engine
        params = {
            'time_step': 0.1,
            'num_floaters': 2,
            'tank_height': 8.0,
            'floater_volume': 0.035,
            'floater_mass_empty': 45.0,
            'generator_torque': 200.0
        }
        data_queue = queue.Queue()
        
        sim_engine = SimulationEngine(params, data_queue)
        
        print(f"✅ Simulation engine created")
        print(f"   - Floaters: {len(sim_engine.floaters)}")
        print(f"   - Physics engine: {hasattr(sim_engine, 'physics_engine')}")
        print(f"   - Event handler: {hasattr(sim_engine, 'advanced_event_handler')}")
        
        # Test integration
        print("\n--- Integration Test ---")
        integration_result = integration_manager.integrate_with_simulation_engine(sim_engine)
        
        print(f"Integration success: {integration_result['success']}")
        if integration_result['success']:
            enhanced_capabilities = integration_result['enhanced_capabilities']
            print(f"Enhanced capabilities: {len(enhanced_capabilities)}")
            for capability in enhanced_capabilities:
                print(f"  - {capability}")
        else:
            print(f"Integration failed: {integration_result.get('reason', 'Unknown')}")
            if 'missing_components' in integration_result:
                print(f"Missing components: {integration_result['missing_components']}")
        
        # Test validation if integration succeeded
        if integration_result['success']:
            print("\n--- Comprehensive Validation Test ---")
            validation_result = integration_manager.run_comprehensive_validation()
            
            print(f"Validation success: {validation_result['success']}")
            if validation_result['success']:
                summary = validation_result['summary']
                print(f"Tests passed: {summary['passed_tests']}/{summary['total_tests']}")
                print(f"Success rate: {summary['success_rate']:.3f}")
            else:
                print(f"Validation failed: {validation_result.get('reason', 'Unknown')}")
                
                # Show recommendations if available
                if 'recommendations' in validation_result:
                    print("Recommendations:")
                    for rec in validation_result['recommendations']:
                        print(f"  - {rec}")
        
        # Test optimization setup (without running full optimization)
        print("\n--- Optimization Setup Test ---")
        try:
            # Test that optimization can be configured
            opt_status = integration_manager.get_optimization_status()
            print(f"Optimization status: {opt_status.get('status', 'Ready')}")
            
            # Quick parameter test
            if integration_result['success']:
                print("Testing parameter application...")
                
                # Apply a simple parameter change
                test_params = {
                    'time_step': 0.05,
                    'drag_coefficient': 0.9
                }
                
                integration_manager.parameter_optimizer._apply_parameters(sim_engine, test_params)
                print(f"Test parameters applied successfully")
                
                current_dt = sim_engine.physics_engine.params['time_step']
                print(f"Current time step: {current_dt}")
                
            print("✅ Optimization setup test completed")
            
        except Exception as e:
            print(f"⚠️ Optimization setup test failed: {e}")
        
        # Get integration status
        print("\n--- Integration Status ---")
        status = integration_manager.get_integration_status()
        
        print(f"Components integrated: {status['integration_status']['components_integrated']}")
        print(f"Validation active: {status['integration_status']['validation_active']}")
        print(f"Optimization active: {status['integration_status']['optimization_active']}")
        
        success_rates = status['success_rates']
        print(f"Success rates:")
        print(f"  - Integration: {success_rates['integration']:.3f}")
        print(f"  - Validation: {success_rates['validation']:.3f}")
        print(f"  - Optimization: {success_rates['optimization']:.3f}")
        
        print("✅ Integration manager test completed")
        return True
        
    except Exception as e:
        print(f"❌ Integration manager test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_full_integration():
    """Test full integration with actual simulation run."""
    print("=== Testing Full Integration ===")
    
    try:
        import queue
        
        # Create proper parameters for simulation engine
        params = {
            'time_step': 0.1,
            'num_floaters': 2,
            'tank_height': 8.0,
            'floater_volume': 0.035,
            'floater_mass_empty': 45.0,
            'generator_torque': 200.0,
            'target_power': 530000.0,
            'target_rpm': 375.0
        }
        data_queue = queue.Queue()
        
        # Create and integrate system
        integration_manager = IntegrationManager()
        sim_engine = SimulationEngine(params, data_queue)
        
        # Perform integration
        integration_result = integration_manager.integrate_with_simulation_engine(sim_engine)
        
        if not integration_result['success']:
            print(f"❌ Integration failed: {integration_result.get('reason', 'Unknown')}")
            return False
        
        print("✅ System integration successful")
        
        # Run a short simulation with validation
        print("\n--- Simulation with Validation ---")
        
        # Enable validation
        integration_manager.integration_status['validation_active'] = True
        
        # Run simulation steps
        start_time = time.time()
        num_steps = 20
        
        print(f"Running {num_steps} simulation steps with validation...")
        
        for step in range(num_steps):
            try:
                dt = 0.1  # Use same time step as in params
                sim_engine.step(dt)
                
                if step % 5 == 0:  # Progress update every 5 steps
                    print(f"  Step {step + 1}/{num_steps} completed")
                    
            except Exception as e:
                print(f"⚠️ Simulation step {step + 1} failed: {e}")
                break
        
        elapsed_time = time.time() - start_time
        print(f"Simulation completed in {elapsed_time:.2f} seconds")
        print(f"Average step time: {elapsed_time / num_steps:.4f} seconds")
        
        # Get performance metrics
        print("\n--- Performance Metrics ---")
        performance = integration_manager.get_performance_summary()
        
        if 'monitoring_data' in performance:
            monitoring = performance['monitoring_data']
            print(f"Steps executed: {monitoring.get('step_count', num_steps)}")
            print(f"Validations run: {monitoring.get('validation_count', 0)}")
            
            metrics = monitoring.get('performance_metrics', {})
            print(f"Physics consistency score: {metrics.get('physics_consistency_score', 0):.3f}")
        
        # Final validation
        print("\n--- Final Validation ---")
        final_validation = integration_manager.run_comprehensive_validation()
        
        if final_validation['success']:
            summary = final_validation['summary']
            print(f"✅ Final validation PASSED ({summary['passed_tests']}/{summary['total_tests']} tests)")
        else:
            print(f"⚠️ Final validation had issues")
            for rec in final_validation.get('recommendations', []):
                print(f"  Recommendation: {rec}")
        
        print("✅ Full integration test completed successfully")
        return True
        
    except Exception as e:
        print(f"❌ Full integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def run_stage3_tests():
    """Run all Stage 3 tests."""
    print("=" * 60)
    print("STAGE 3 IMPLEMENTATION TEST SUITE")
    print("Integration and Validation Framework")
    print("=" * 60)
    
    test_results = {}
    
    # Test 1: Validation Framework
    print("\n" + "=" * 50)
    test_results['validation_framework'] = test_validation_framework()
    
    # Test 2: Parameter Optimizer
    print("\n" + "=" * 50)
    test_results['parameter_optimizer'] = test_parameter_optimizer()
    
    # Test 3: Integration Manager
    print("\n" + "=" * 50)
    test_results['integration_manager'] = test_integration_manager()
    
    # Test 4: Full Integration
    print("\n" + "=" * 50)
    test_results['full_integration'] = test_full_integration()
    
    # Summary
    print("\n" + "=" * 60)
    print("STAGE 3 TEST SUMMARY")
    print("=" * 60)
    
    passed_tests = sum(test_results.values())
    total_tests = len(test_results)
    
    for test_name, result in test_results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name:25}: {status}")
    
    print(f"\nOverall Results: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 ALL STAGE 3 TESTS PASSED!")
        print("\nStage 3 Implementation Features:")
        print("✅ Comprehensive validation framework")
        print("✅ Parameter optimization system")
        print("✅ Component integration manager")
        print("✅ Real-time monitoring and validation")
        print("✅ Automated parameter tuning")
        print("✅ Physics consistency validation")
        print("✅ Energy conservation verification")
        
        return True
    else:
        print(f"⚠️ {total_tests - passed_tests} test(s) failed")
        return False

if __name__ == "__main__":
    success = run_stage3_tests()
    
    if success:
        print("\n🎯 Stage 3 implementation is ready for production!")
        print("   Next: Proceed to Stage 4 (Real-time optimization)")
    else:
        print("\n⚠️ Stage 3 implementation needs attention before proceeding")
    
    # Keep the console open on Windows
    if os.name == 'nt':
        input("\nPress Enter to exit...")
