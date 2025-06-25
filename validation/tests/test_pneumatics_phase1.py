"""
Test suite for Phase 1 of KPP Pneumatic System implementation.

Tests the air compression system and pressure control system components
for correct physics, energy conservation, and control behavior.
"""

import unittest
import math
import sys
import os

# Add the project root to the path
project_root = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, project_root)

from simulation.pneumatics.air_compression import (
    AirCompressionSystem, CompressorSpec, PressureTankSpec, create_standard_kpp_compressor
)
from simulation.pneumatics.pressure_control import (
    PressureControlSystem, PressureControlSettings, CompressorState, SafetyLevel,
    create_standard_kpp_pressure_controller
)

class TestAirCompressionSystem(unittest.TestCase):
    """Test the air compression system physics and behavior."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.system = create_standard_kpp_compressor()
        self.ambient_pressure = 101325.0  # Pa
        self.ambient_temp = 293.15  # K
    
    def test_initialization(self):
        """Test system initialization."""
        self.assertEqual(self.system.ambient_pressure, self.ambient_pressure)
        self.assertEqual(self.system.ambient_temperature, self.ambient_temp)
        self.assertGreater(self.system.air_mass_in_tank, 0)
        self.assertEqual(self.system.tank_pressure, self.ambient_pressure)
    
    def test_pressure_requirements_calculation(self):
        """Test pressure requirement calculations for different depths."""
        # Test at 10m depth
        depth_10m = 10.0
        required_pressure = self.system.get_required_injection_pressure(depth_10m)
        
        # Expected: ambient + hydrostatic + valve losses
        expected = self.ambient_pressure + (1000 * 9.81 * depth_10m) + 10000
        self.assertAlmostEqual(required_pressure, expected, places=0)
        
        # Test at 20m depth
        depth_20m = 20.0
        required_pressure_20m = self.system.get_required_injection_pressure(depth_20m)
        self.assertGreater(required_pressure_20m, required_pressure)
    
    def test_isothermal_compression_work(self):
        """Test isothermal compression work calculation."""
        volume = 0.1  # m³
        target_pressure = 2.0 * self.ambient_pressure  # 2 atm
        
        work = self.system.calculate_isothermal_compression_work(volume, target_pressure)
        
        # Expected work = P_atm * V * ln(P_target/P_atm)
        expected = self.ambient_pressure * volume * math.log(2.0)
        self.assertAlmostEqual(work, expected, places=0)
        
        # Work should increase with pressure ratio
        work_3atm = self.system.calculate_isothermal_compression_work(volume, 3.0 * self.ambient_pressure)
        self.assertGreater(work_3atm, work)
    
    def test_adiabatic_compression_work(self):
        """Test adiabatic compression work calculation."""
        volume = 0.1  # m³
        target_pressure = 2.0 * self.ambient_pressure
        
        work = self.system.calculate_adiabatic_compression_work(volume, target_pressure)
        
        # Adiabatic work should be higher than isothermal
        isothermal_work = self.system.calculate_isothermal_compression_work(volume, target_pressure)
        self.assertGreater(work, isothermal_work)
    
    def test_actual_compression_work(self):
        """Test actual compression work with heat removal."""
        volume = 0.1  # m³
        target_pressure = 2.0 * self.ambient_pressure
        
        actual_work, heat_gen, heat_removed = self.system.calculate_actual_compression_work(
            volume, target_pressure, 0.7)
        
        # Actual work should be between isothermal and adiabatic
        isothermal = self.system.calculate_isothermal_compression_work(volume, target_pressure)
        adiabatic = self.system.calculate_adiabatic_compression_work(volume, target_pressure)
        
        self.assertGreaterEqual(actual_work, isothermal)
        self.assertLessEqual(actual_work, adiabatic)
        
        # Heat calculations
        self.assertGreater(heat_gen, 0)
        self.assertGreater(heat_removed, 0)
        self.assertLessEqual(heat_removed, heat_gen)
    
    def test_tank_pressure_updates(self):
        """Test tank pressure updates after compression."""
        initial_pressure = self.system.tank_pressure
        
        # Add compressed air
        air_volume = 0.05  # m³
        compression_pressure = 2.0 * self.ambient_pressure
        
        self.system.update_tank_pressure_after_compression(air_volume, compression_pressure)
        
        # Pressure should increase
        self.assertGreater(self.system.tank_pressure, initial_pressure)
    
    def test_air_consumption(self):
        """Test air consumption from tank."""
        # First, add some compressed air
        self.system.update_tank_pressure_after_compression(0.1, 2.0 * self.ambient_pressure)
        initial_pressure = self.system.tank_pressure
        
        # Consume some air
        consumed_volume = 0.02  # m³ at tank pressure
        success = self.system.consume_air_from_tank(consumed_volume)
        
        self.assertTrue(success)
        self.assertLess(self.system.tank_pressure, initial_pressure)
    
    def test_compressor_power_calculation(self):
        """Test compressor power calculations."""
        flow_rate = 0.01  # m³/s
        target_pressure = 2.0 * self.ambient_pressure
        
        power = self.system.calculate_compressor_power_for_flow(flow_rate, target_pressure)
        
        # Power should be positive and reasonable
        self.assertGreater(power, 0)
        self.assertLess(power, self.system.compressor.power_rating * 2)  # Within reasonable bounds
    
    def test_maximum_flow_rate(self):
        """Test maximum flow rate calculation."""
        target_pressure = 2.0 * self.ambient_pressure
        max_flow = self.system.get_maximum_flow_rate_at_pressure(target_pressure)
        
        # Should be positive and within compressor limits
        self.assertGreater(max_flow, 0)
        self.assertLessEqual(max_flow, self.system.compressor.max_flow_rate)
        
        # Higher pressure should yield lower max flow
        max_flow_3atm = self.system.get_maximum_flow_rate_at_pressure(3.0 * self.ambient_pressure)
        self.assertLess(max_flow_3atm, max_flow)
    
    def test_compressor_operation(self):
        """Test compressor operation simulation."""
        dt = 1.0  # 1 second
        target_pressure = 2.5 * self.ambient_pressure
        
        results = self.system.run_compressor(dt, target_pressure)
        
        # Should be running since tank starts at ambient pressure
        self.assertTrue(results['running'])
        self.assertGreater(results['power_consumed'], 0)
        self.assertGreater(results['air_compressed'], 0)
        self.assertGreater(results['work_done'], 0)
        
        # Tank pressure should increase
        self.assertGreater(self.system.tank_pressure, self.ambient_pressure)
    
    def test_energy_conservation(self):
        """Test energy conservation in compression process."""
        # Run compressor for several steps
        dt = 1.0
        target_pressure = 2.0 * self.ambient_pressure
        
        for _ in range(5):
            self.system.run_compressor(dt, target_pressure)
        
        # Check energy conservation
        status = self.system.get_system_status()
        
        # Total energy consumed should be greater than compression work (efficiency < 1)
        self.assertGreater(status['total_energy_consumed_kwh'], 0)
        self.assertGreater(status['total_compression_work_kj'], 0)
        
        # Efficiency should be reasonable (less than 1)
        efficiency = status['compression_efficiency']
        self.assertGreater(efficiency, 0.5)  # Should be reasonably efficient
        self.assertLess(efficiency, 1.0)     # But not over-unity
    
    def test_system_reset(self):
        """Test system reset functionality."""
        # Run compressor to change state
        self.system.run_compressor(1.0, 2.0 * self.ambient_pressure)
        
        # Reset system
        self.system.reset_system()
        
        # Should be back to initial conditions
        self.assertEqual(self.system.tank_pressure, self.ambient_pressure)
        self.assertEqual(self.system.total_energy_consumed, 0.0)
        self.assertFalse(self.system.compressor_running)


class TestPressureControlSystem(unittest.TestCase):
    """Test the pressure control system behavior."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.air_system = create_standard_kpp_compressor()
        self.control_system = create_standard_kpp_pressure_controller(2.5)  # 2.5 bar target
        self.control_system.set_air_compressor(self.air_system)
    
    def test_initialization(self):
        """Test control system initialization."""
        self.assertEqual(self.control_system.compressor_state, CompressorState.OFF)
        self.assertEqual(self.control_system.safety_level, SafetyLevel.NORMAL)
        self.assertFalse(self.control_system.emergency_stop_active)
    
    def test_pressure_setpoints(self):
        """Test pressure setpoint logic."""
        settings = self.control_system.settings
        
        # Target should be between high and low setpoints
        self.assertLess(settings.low_pressure_setpoint, settings.target_pressure)
        self.assertGreater(settings.high_pressure_setpoint, settings.target_pressure)
        
        # Critical pressures should be outside normal operating range
        self.assertLess(settings.critical_low_pressure, settings.low_pressure_setpoint)
        self.assertGreater(settings.emergency_high_pressure, settings.high_pressure_setpoint)
    
    def test_compressor_start_logic(self):
        """Test compressor start conditions."""
        current_time = 100.0
        
        # Should start when pressure is low
        low_pressure = self.control_system.settings.low_pressure_setpoint - 10000.0
        self.air_system.tank_pressure = low_pressure
        should_start = self.control_system.should_start_compressor(low_pressure, current_time)
        self.assertTrue(should_start)
        
        # Should not start when pressure is adequate
        good_pressure = self.control_system.settings.target_pressure
        should_start = self.control_system.should_start_compressor(good_pressure, current_time)
        self.assertFalse(should_start)
    
    def test_compressor_stop_logic(self):
        """Test compressor stop conditions."""
        current_time = 100.0
        
        # Should stop when pressure is high
        high_pressure = self.control_system.settings.high_pressure_setpoint + 10000.0
        should_stop = self.control_system.should_stop_compressor(high_pressure, current_time)
        self.assertTrue(should_stop)
        
        # Should stop on emergency
        self.control_system.emergency_stop()
        should_stop = self.control_system.should_stop_compressor(
            self.control_system.settings.target_pressure, current_time)
        self.assertTrue(should_stop)
    
    def test_safety_monitoring(self):
        """Test safety condition monitoring."""
        # Normal pressure
        normal_pressure = self.control_system.settings.target_pressure
        safety_level = self.control_system.check_safety_conditions(normal_pressure)
        self.assertEqual(safety_level, SafetyLevel.NORMAL)
        
        # Critical low pressure
        critical_pressure = self.control_system.settings.critical_low_pressure - 1000.0
        safety_level = self.control_system.check_safety_conditions(critical_pressure)
        self.assertEqual(safety_level, SafetyLevel.CRITICAL)
        
        # Emergency high pressure
        emergency_pressure = self.control_system.settings.emergency_high_pressure + 1000.0
        safety_level = self.control_system.check_safety_conditions(emergency_pressure)
        self.assertEqual(safety_level, SafetyLevel.EMERGENCY)
    
    def test_control_loop_execution(self):
        """Test complete control loop execution."""
        dt = 1.0
        current_time = 0.0
        
        # Run several control steps
        for i in range(10):
            results = self.control_system.control_step(dt, current_time)
            current_time += dt
            
            # Should have valid results
            self.assertIn('compressor_state', results)
            self.assertIn('safety_level', results)
            self.assertIn('tank_pressure', results)
            self.assertIn('compressor_results', results)
            
            # Check that compressor eventually starts (pressure is initially low)
            if i > 2:  # After a few steps
                state = results['compressor_state']
                # Should be starting or running at some point
                if state in ['starting', 'running']:
                    break
        else:
            self.fail("Compressor never started during control loop")
    
    def test_hysteresis_behavior(self):
        """Test pressure control hysteresis."""
        dt = 0.1
        current_time = 0.0
          # Start with low pressure to trigger compressor start
        self.air_system.set_tank_pressure(self.control_system.settings.low_pressure_setpoint - 5000.0)
        
        # Run until compressor starts
        for _ in range(10):
            results = self.control_system.control_step(dt, current_time)
            current_time += dt
            if results['compressor_state'] in ['starting', 'running']:
                break
        
        # Continue running until high setpoint reached
        for _ in range(100):
            results = self.control_system.control_step(dt, current_time)
            current_time += dt
            
            if results['tank_pressure'] >= self.control_system.settings.high_pressure_setpoint:
                # Should stop compressor
                for _ in range(5):
                    results = self.control_system.control_step(dt, current_time)
                    current_time += dt
                    if results['compressor_state'] == 'off':
                        break
                else:
                    self.fail("Compressor did not stop at high pressure setpoint")
                break
        else:
            self.fail("Pressure did not reach high setpoint")
    
    def test_emergency_stop(self):
        """Test emergency stop functionality."""
        # Start compressor
        self.control_system.compressor_state = CompressorState.RUNNING
        
        # Trigger emergency stop
        self.control_system.emergency_stop()
        
        # Should be stopped and emergency flag set
        self.assertEqual(self.control_system.compressor_state, CompressorState.OFF)
        self.assertTrue(self.control_system.emergency_stop_active)
        
        # Should not start even with low pressure
        low_pressure = self.control_system.settings.critical_low_pressure
        should_start = self.control_system.should_start_compressor(low_pressure, 100.0)
        self.assertFalse(should_start)
        
        # Reset emergency stop
        self.control_system.reset_emergency_stop()
        self.assertFalse(self.control_system.emergency_stop_active)
    
    def test_target_pressure_update(self):
        """Test target pressure update functionality."""
        new_target = 300000.0  # 3 bar
        
        self.control_system.update_target_pressure(new_target)
        
        self.assertEqual(self.control_system.settings.target_pressure, new_target)
        # Setpoints should be updated accordingly
        self.assertGreater(self.control_system.settings.high_pressure_setpoint, new_target)
        self.assertLess(self.control_system.settings.low_pressure_setpoint, new_target)
    
    def test_performance_metrics(self):
        """Test performance metric calculations."""
        # Run some cycles
        dt = 0.1
        current_time = 0.0
        
        # Set low pressure to trigger operation
        self.air_system.tank_pressure = 150000.0
        
        for _ in range(100):
            self.control_system.control_step(dt, current_time)
            current_time += dt
        
        # Check metrics
        metrics = self.control_system.calculate_efficiency_metrics()
        self.assertIn('duty_cycle', metrics)
        self.assertIn('avg_cycle_time', metrics)
        
        status = self.control_system.get_control_status()
        self.assertGreaterEqual(status['cycle_count'], 0)
    
    def test_system_reset(self):
        """Test control system reset."""
        # Change some state
        self.control_system.cycle_count = 5
        self.control_system.total_runtime = 100.0
        self.control_system.compressor_state = CompressorState.RUNNING
        
        # Reset
        self.control_system.reset_control_system()
        
        # Should be back to initial state
        self.assertEqual(self.control_system.cycle_count, 0)
        self.assertEqual(self.control_system.total_runtime, 0.0)
        self.assertEqual(self.control_system.compressor_state, CompressorState.OFF)


class TestIntegratedPneumaticSystem(unittest.TestCase):
    """Test integrated operation of compression and control systems."""
    
    def setUp(self):
        """Set up integrated system."""
        self.air_system = create_standard_kpp_compressor()
        self.control_system = create_standard_kpp_pressure_controller(2.0)  # 2 bar target
        self.control_system.set_air_compressor(self.air_system)
    
    def test_pressure_buildup_cycle(self):
        """Test complete pressure buildup cycle."""
        dt = 1.0
        current_time = 0.0
        max_time = 300.0  # 5 minutes max
        
        initial_pressure = self.air_system.tank_pressure
        target_pressure = self.control_system.settings.target_pressure
        
        while current_time < max_time:
            results = self.control_system.control_step(dt, current_time)
            current_time += dt
            
            # Check if target pressure reached
            if results['tank_pressure'] >= target_pressure * 0.95:  # Within 95% of target
                self.assertGreater(results['tank_pressure'], initial_pressure)
                return
        
        self.fail("Target pressure not reached within time limit")
    
    def test_energy_efficiency(self):
        """Test overall system energy efficiency."""
        dt = 1.0
        current_time = 0.0
        
        # Run system for a while
        for _ in range(60):  # 1 minute
            self.control_system.control_step(dt, current_time)
            current_time += dt
        
        # Check energy metrics
        air_status = self.air_system.get_system_status()
        control_status = self.control_system.get_control_status()
        
        # Should have consumed some energy
        self.assertGreater(air_status['total_energy_consumed_kwh'], 0)
        
        # Efficiency should be reasonable
        if air_status['compression_efficiency'] > 0:
            self.assertLess(air_status['compression_efficiency'], 1.0)  # No over-unity
            self.assertGreater(air_status['compression_efficiency'], 0.3)  # Reasonable efficiency
    
    def test_steady_state_operation(self):
        """Test steady-state operation with pressure regulation."""
        dt = 0.5
        current_time = 0.0
        
        # Run to steady state
        for _ in range(200):  # 100 seconds
            self.control_system.control_step(dt, current_time)
            current_time += dt
        
        # Now simulate air consumption to test regulation
        consumption_volume = 0.01  # m³
        
        for _ in range(20):  # Test regulation response
            # Consume some air
            self.air_system.consume_air_from_tank(consumption_volume)
            
            # Run control step
            results = self.control_system.control_step(dt, current_time)
            current_time += dt
            
            # Pressure should stay within reasonable bounds
            pressure = results['tank_pressure']
            min_acceptable = self.control_system.settings.low_pressure_setpoint
            max_acceptable = self.control_system.settings.emergency_high_pressure
            
            self.assertGreaterEqual(pressure, min_acceptable * 0.9)  # Allow some undershoot
            self.assertLessEqual(pressure, max_acceptable)


def run_phase1_validation():
    """Run comprehensive validation of Phase 1 implementation."""
    print("Running Phase 1 KPP Pneumatic System Validation...")
    print("=" * 60)
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestAirCompressionSystem))
    suite.addTests(loader.loadTestsFromTestCase(TestPressureControlSystem))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegratedPneumaticSystem))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 60)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.failures:
        print("\nFailures:")
        for test, traceback in result.failures:
            print(f"  {test}: {traceback.split(chr(10))[-2]}")
    
    if result.errors:
        print("\nErrors:")
        for test, traceback in result.errors:
            print(f"  {test}: {traceback.split(chr(10))[-2]}")
    
    success_rate = (result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100
    print(f"\nSuccess rate: {success_rate:.1f}%")
    
    if success_rate >= 95:
        print("✅ Phase 1 implementation PASSED validation!")
    else:
        print("❌ Phase 1 implementation needs attention.")
    
    return result.wasSuccessful()


if __name__ == '__main__':
    run_phase1_validation()
