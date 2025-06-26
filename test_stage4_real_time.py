"""
Stage 4 Implementation Test: Real-time Optimization and Streaming
Tests performance optimization, adaptive timestep, data streaming, and error recovery
"""

import time
import unittest
import logging
import json
from pathlib import Path

# Set up logging to capture test progress
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# Import all necessary modules
from simulation.optimization.real_time_optimizer import (
    RealTimeOptimizer, PerformanceProfiler, AdaptiveTimestepper,
    NumericalStabilityMonitor, DataStreamOptimizer
)
from simulation.monitoring.real_time_monitor import (
    RealTimeController, DataStreamManager, RealTimeMonitor, ErrorRecoverySystem
)
from simulation.components.floater import Floater

class TestStage4RealTimeOptimization(unittest.TestCase):
    """Test Stage 4: Real-time optimization components"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_start_time = time.time()
        logger.info("Setting up Stage 4 test environment")
        
    def tearDown(self):
        """Clean up after each test"""
        test_duration = time.time() - self.test_start_time
        logger.info(f"Test completed in {test_duration:.3f} seconds")
        
    def test_performance_profiler(self):
        """Test performance profiling system"""
        logger.info("Testing PerformanceProfiler...")
        
        profiler = PerformanceProfiler(window_size=10)
        
        # Record some sample timings
        for i in range(15):
            profiler.record_timing('physics', 0.01 + i * 0.001)
            profiler.record_timing('events', 0.005 + i * 0.0005)
            profiler.increment_counter('steps')
            
        # Test statistics
        physics_stats = profiler.get_stats('physics')
        self.assertGreater(physics_stats['avg'], 0)
        self.assertGreater(physics_stats['max'], physics_stats['min'])
        
        # Test performance summary
        summary = profiler.get_performance_summary()
        self.assertIn('counters', summary)
        self.assertIn('timings', summary)
        self.assertEqual(summary['counters']['steps'], 15)
        
        logger.info("✓ PerformanceProfiler working correctly")
        
    def test_adaptive_timestepper(self):
        """Test adaptive timestep system"""
        logger.info("Testing AdaptiveTimestepper...")
        
        timestepper = AdaptiveTimestepper(
            initial_dt=0.1,
            min_dt=0.01,
            max_dt=0.5
        )
        
        # Test performance-based adaptation
        target_frame_time = 0.1
        
        # Slow computation should increase timestep
        slow_computation_time = 0.15
        new_dt = timestepper.adapt_timestep(slow_computation_time, target_frame_time)
        self.assertGreaterEqual(new_dt, timestepper.min_dt)
        self.assertLessEqual(new_dt, timestepper.max_dt)
        
        # Fast computation should decrease timestep
        fast_computation_time = 0.03
        new_dt = timestepper.adapt_timestep(fast_computation_time, target_frame_time)
        self.assertGreaterEqual(new_dt, timestepper.min_dt)
        self.assertLessEqual(new_dt, timestepper.max_dt)
        
        # Test error-based adaptation
        high_error = 1e-3
        initial_dt = timestepper.dt
        new_dt = timestepper.adapt_timestep(0.08, target_frame_time, high_error)
        # With high error, timestep should be reduced (or at least not increase significantly)
        self.assertLessEqual(new_dt, initial_dt * 1.1)  # Allow small increases due to performance
        
        logger.info("✓ AdaptiveTimestepper working correctly")
        
    def test_numerical_stability_monitor(self):
        """Test numerical stability monitoring"""
        logger.info("Testing NumericalStabilityMonitor...")
        
        monitor = NumericalStabilityMonitor()
        
        # Test stable state
        stable_state = {
            'v_chain': 5.0,
            'a_chain': 20.0,
            'forces': {'buoyancy': 1000.0, 'drag': -500.0}
        }
        is_stable, violations = monitor.check_stability(stable_state)
        self.assertTrue(is_stable)
        self.assertEqual(len(violations), 0)
        
        # Test unstable state
        unstable_state = {
            'v_chain': 15.0,  # Too high
            'a_chain': 60.0,  # Too high
            'forces': {'buoyancy': 200000.0}  # Too high
        }
        is_stable, violations = monitor.check_stability(unstable_state)
        self.assertFalse(is_stable)
        self.assertGreater(len(violations), 0)
        
        # Test stability score
        score = monitor.get_stability_score()
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 1.0)
        
        logger.info("✓ NumericalStabilityMonitor working correctly")
        
    def test_real_time_optimizer(self):
        """Test main real-time optimizer"""
        logger.info("Testing RealTimeOptimizer...")
        
        optimizer = RealTimeOptimizer(target_fps=10.0)
        
        # Create test floaters
        test_floaters = []
        for i in range(3):
            floater = Floater(
                volume=0.1,
                mass=100.0,
                area=0.05,
                position=i * 2.0
            )
            # Set angle attribute for physics engine compatibility
            floater.angle = i * 2.0
            test_floaters.append(floater)
            
        # Test force calculation optimization
        optimization_result = optimizer.optimize_force_calculations(test_floaters)
        self.assertIn('optimized', optimization_result)
        self.assertIn('method', optimization_result)
        
        # Test simulation step optimization
        test_state = {
            'v_chain': 3.0,
            'a_chain': 15.0,
            'forces': {'total': 5000.0},
            'time': 1.0
        }
        
        step_start = time.time()
        time.sleep(0.01)  # Simulate computation time
        
        recommendations = optimizer.optimize_step(test_state, step_start)
        self.assertIn('continue', recommendations)
        self.assertIn('stability_score', recommendations)
        self.assertIsInstance(recommendations['continue'], bool)
        
        # Test performance report
        report = optimizer.get_performance_report()
        self.assertIn('optimization', report)
        self.assertIn('recommendations', report)
        
        logger.info("✓ RealTimeOptimizer working correctly")
        
    def test_data_stream_manager(self):
        """Test data streaming system"""
        logger.info("Testing DataStreamManager...")
        
        stream_manager = DataStreamManager(max_buffer_size=10)
        
        # Test subscriber management
        received_data = []
        
        def test_callback(data):
            received_data.append(data)
            
        subscriber_id = stream_manager.add_subscriber('test_sub', test_callback, 20.0)
        self.assertEqual(subscriber_id, 'test_sub')
        self.assertIn('test_sub', stream_manager.subscribers)
        
        # Test data streaming
        test_data = {
            'v_chain': 2.5,
            'power_output': 1000.0,
            'efficiency': 0.8
        }
        
        stream_manager.stream_data(test_data)
        
        # Give callback time to execute
        time.sleep(0.01)
        
        # Check if data was received
        self.assertGreater(len(received_data), 0)
        self.assertIn('data', received_data[0])
        
        # Test subscriber removal
        stream_manager.remove_subscriber('test_sub')
        self.assertNotIn('test_sub', stream_manager.subscribers)
        
        logger.info("✓ DataStreamManager working correctly")
        
    def test_real_time_monitor(self):
        """Test real-time monitoring system"""
        logger.info("Testing RealTimeMonitor...")
        
        monitor = RealTimeMonitor()
        
        # Add test monitors
        monitor.add_monitor('test_velocity', 'v_chain', 8.0, 'greater', 'warning')
        monitor.add_monitor('test_power', 'power_output', 500.0, 'less', 'error')
        
        self.assertEqual(len(monitor.monitors), 2)
        
        # Test monitoring with data that should trigger alerts
        test_data = {
            'v_chain': 10.0,  # Should trigger velocity alert
            'power_output': 300.0  # Should trigger power alert
        }
        
        monitor.check_monitors(test_data, time.time())
        
        # Check if alerts were generated
        recent_alerts = monitor.get_recent_alerts()
        self.assertGreater(len(recent_alerts), 0)
        
        # Test alert levels
        alert_levels = [alert['level'] for alert in recent_alerts]
        self.assertIn('warning', alert_levels)
        self.assertIn('error', alert_levels)
        
        logger.info("✓ RealTimeMonitor working correctly")
        
    def test_error_recovery_system(self):
        """Test automated error recovery"""
        logger.info("Testing ErrorRecoverySystem...")
        
        recovery_system = ErrorRecoverySystem()
        
        # Register test recovery strategy
        def test_recovery_strategy(error_data, context):
            return {
                'success': True,
                'action': 'adjust_parameters',
                'message': 'Test recovery applied'
            }
            
        recovery_system.register_recovery_strategy('test_error', test_recovery_strategy)
        
        # Test error handling
        error_result = recovery_system.handle_error(
            'test_error',
            {'severity': 'medium'},
            {'simulation_time': 10.0}
        )
        
        self.assertTrue(error_result['recovered'])
        self.assertEqual(error_result['action'], 'adjust_parameters')
        
        # Test error summary
        summary = recovery_system.get_error_summary()
        self.assertEqual(summary['total_errors'], 1)
        self.assertEqual(summary['recovery_successful'], 1)
        
        logger.info("✓ ErrorRecoverySystem working correctly")
        
    def test_real_time_controller_integration(self):
        """Test integrated real-time controller"""
        logger.info("Testing RealTimeController integration...")
        
        controller = RealTimeController()
        
        # Test configuration
        controller.configure_performance_mode('performance')
        self.assertEqual(controller.performance_mode, 'performance')
        
        # Test data processing
        simulation_data = {
            'v_chain': 4.0,
            'power_output': 2000.0,
            'efficiency': 0.75
        }
        
        performance_data = {
            'fps': 12.0,
            'computation_time': 0.08,
            'stability_score': 0.95
        }
        
        result = controller.process_realtime_data(simulation_data, performance_data)
        
        self.assertTrue(result['processed'])
        self.assertIn('timestamp', result)
        self.assertIn('streaming_status', result)
        
        # Test status report
        status = controller.get_status_report()
        self.assertIn('controller', status)
        self.assertIn('streaming', status)
        self.assertIn('monitoring', status)
        self.assertIn('error_recovery', status)
        
        logger.info("✓ RealTimeController integration working correctly")
        
    def test_data_stream_optimizer(self):
        """Test data streaming optimization"""
        logger.info("Testing DataStreamOptimizer...")
        
        optimizer = DataStreamOptimizer(base_sample_rate=10.0)
        
        # Test data optimization with good performance
        full_data = {
            'v_chain': 3.0,
            'power_output': 1500.0,
            'efficiency': 0.8,
            'floater_states': [{'id': 0, 'filled': True}],
            'forces': {'total': 2000.0},
            'validation_results': {'consistent': True}
        }
        
        performance_metrics = {'fps': 12.0}
        
        optimized = optimizer.optimize_data_output(full_data, performance_metrics)
        
        # Should include priority data
        self.assertIn('v_chain', optimized)
        self.assertIn('power_output', optimized)
        self.assertIn('efficiency', optimized)
        self.assertIn('_metadata', optimized)
        
        # Test with poor performance
        performance_metrics = {'fps': 3.0}
        optimized_poor = optimizer.optimize_data_output(full_data, performance_metrics)
        
        # Should have reduced data
        self.assertLess(len(optimized_poor), len(optimized))
        
        logger.info("✓ DataStreamOptimizer working correctly")

class TestStage4Integration(unittest.TestCase):
    """Test Stage 4: Integration with simulation engine"""
    
    def test_optimization_integration(self):
        """Test integration of optimization with simulation"""
        logger.info("Testing Stage 4 integration...")
        
        # This test verifies that the optimization components can work together
        optimizer = RealTimeOptimizer(target_fps=10.0)
        controller = RealTimeController()
        
        # Simulate a few optimization cycles
        for i in range(5):
            # Simulate varying performance
            computation_time = 0.05 + i * 0.02
            
            test_state = {
                'v_chain': 2.0 + i * 0.5,
                'a_chain': 10.0 + i * 2.0,
                'power_output': 1000.0 + i * 200.0,
                'time': i * 0.1
            }
            
            step_start = time.time()
            time.sleep(computation_time)
            
            # Test optimization
            recommendations = optimizer.optimize_step(test_state, step_start)
            self.assertIn('continue', recommendations)
            
            # Test real-time processing
            performance_data = optimizer.get_performance_report()
            rt_result = controller.process_realtime_data(test_state, performance_data)
            self.assertTrue(rt_result['processed'])
            
        logger.info("✓ Stage 4 integration working correctly")

def run_stage4_tests():
    """Run all Stage 4 tests"""
    print("=" * 60)
    print("STAGE 4 IMPLEMENTATION TEST: Real-time Optimization and Streaming")
    print("=" * 60)
    
    # Create test suite
    suite = unittest.TestSuite()
    
    # Add all test cases
    test_classes = [
        TestStage4RealTimeOptimization,
        TestStage4Integration
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 60)
    print("STAGE 4 TEST SUMMARY")
    print("=" * 60)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.failures:
        print("\nFAILURES:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback}")
    
    if result.errors:
        print("\nERRORS:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback}")
    
    success = len(result.failures) == 0 and len(result.errors) == 0
    
    if success:
        print("\n✅ ALL STAGE 4 TESTS PASSED!")
        print("Real-time optimization and streaming implementation complete.")
        
        # Save test results
        results = {
            'stage': 4,
            'timestamp': time.time(),
            'tests_run': result.testsRun,
            'failures': len(result.failures),
            'errors': len(result.errors),
            'success': success,
            'components_tested': [
                'RealTimeOptimizer',
                'PerformanceProfiler', 
                'AdaptiveTimestepper',
                'NumericalStabilityMonitor',
                'DataStreamManager',
                'RealTimeMonitor',
                'ErrorRecoverySystem',
                'RealTimeController',
                'DataStreamOptimizer'
            ]
        }
        
        with open('test_stage4_results.json', 'w') as f:
            json.dump(results, f, indent=2)
            
        print("Test results saved to test_stage4_results.json")
    else:
        print("\n❌ STAGE 4 TESTS FAILED!")
        print("Please review and fix the issues before proceeding to Stage 5.")
    
    return success

if __name__ == '__main__':
    run_stage4_tests()
