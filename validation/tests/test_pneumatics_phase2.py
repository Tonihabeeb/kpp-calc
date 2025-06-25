"""
Test suite for Phase 2: Air Injection Control System

This module tests the air injection control system including:
- Injection valve operation and timing
- Pressure calculations for different depths
- Flow rate control and pressure drop compensation
- Multi-floater coordination and queue management
- Floater pneumatic state management
"""

import unittest
import math
from unittest.mock import Mock, patch
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from simulation.pneumatics import (
    AirInjectionController,
    InjectionValveSpec,
    InjectionSettings,
    FloaterInjectionRequest,
    InjectionState,
    ValveState,
    create_standard_kpp_injection_controller
)

from simulation.components.floater import Floater


class TestAirInjectionController(unittest.TestCase):
    """Test the air injection controller functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.injection_controller = create_standard_kpp_injection_controller()
        self.ambient_pressure = 101325.0  # Pa
        
    def test_initialization(self):
        """Test injection controller initialization."""
        self.assertEqual(self.injection_controller.valve_state, ValveState.CLOSED)
        self.assertEqual(self.injection_controller.valve_position, 0.0)
        self.assertEqual(len(self.injection_controller.injection_queue), 0)
        self.assertIsNone(self.injection_controller.current_injection)
    
    def test_required_injection_pressure_calculation(self):
        """Test calculation of required injection pressure for different depths."""
        # Test surface injection (depth = 0)
        surface_pressure = self.injection_controller.calculate_required_injection_pressure(0.0)
        expected_surface = self.ambient_pressure + self.injection_controller.settings.pressure_margin
        self.assertAlmostEqual(surface_pressure, expected_surface, places=0)
        
        # Test at 10m depth
        depth_10m = 10.0
        pressure_10m = self.injection_controller.calculate_required_injection_pressure(depth_10m)
        water_density = self.injection_controller.water_density
        gravity = self.injection_controller.gravity
        hydrostatic_10m = water_density * gravity * depth_10m
        expected_10m = self.ambient_pressure + hydrostatic_10m + self.injection_controller.settings.pressure_margin
        self.assertAlmostEqual(pressure_10m, expected_10m, places=0)
        
        # Pressure should increase with depth
        pressure_20m = self.injection_controller.calculate_required_injection_pressure(20.0)
        self.assertGreater(pressure_20m, pressure_10m)
    
    def test_injection_flow_rate_calculation(self):
        """Test injection flow rate calculation based on pressure differences."""
        # Test with adequate supply pressure
        supply_pressure = 300000.0  # 3 bar
        injection_pressure = 200000.0  # 2 bar
        
        # Set valve fully open
        self.injection_controller.valve_position = 1.0
        
        flow_rate = self.injection_controller.calculate_injection_flow_rate(
            supply_pressure, injection_pressure)
        
        self.assertGreater(flow_rate, 0.0)
        self.assertLessEqual(flow_rate, self.injection_controller.valve_spec.max_flow_rate)
        
        # Test with insufficient supply pressure
        insufficient_supply = 150000.0  # 1.5 bar
        no_flow_rate = self.injection_controller.calculate_injection_flow_rate(
            insufficient_supply, injection_pressure)
        
        self.assertEqual(no_flow_rate, 0.0)
    
    def test_injection_request_management(self):
        """Test adding and managing injection requests."""
        # Create test injection request
        request = FloaterInjectionRequest(
            floater_id="test_floater_1",
            depth=5.0,
            target_volume=0.05,  # 50L
            position=0.0,
            timestamp=0.0
        )
        
        # Add request to queue
        success = self.injection_controller.add_injection_request(request)
        self.assertTrue(success)
        self.assertEqual(len(self.injection_controller.injection_queue), 1)
        
        # Check that injection pressure was calculated
        self.assertGreater(request.injection_pressure, self.ambient_pressure)
    
    def test_injection_queue_overflow(self):
        """Test injection queue overflow handling."""
        # Fill queue to maximum capacity
        for i in range(self.injection_controller.settings.max_queue_size):
            request = FloaterInjectionRequest(
                floater_id=f"floater_{i}",
                depth=5.0,
                target_volume=0.05,
                position=0.0,
                timestamp=float(i)
            )
            success = self.injection_controller.add_injection_request(request)
            self.assertTrue(success)
        
        # Try to add one more (should fail)
        overflow_request = FloaterInjectionRequest(
            floater_id="overflow_floater",
            depth=5.0,
            target_volume=0.05,
            position=0.0,
            timestamp=100.0
        )
        success = self.injection_controller.add_injection_request(overflow_request)
        self.assertFalse(success)
    
    def test_valve_position_control(self):
        """Test valve position control and timing."""
        dt = 0.01  # 10ms time step
        
        # Start valve opening
        self.injection_controller.valve_state = ValveState.OPENING
        
        # Update valve position several times
        total_time = 0.0
        response_time = self.injection_controller.valve_spec.response_time
        
        while total_time < response_time:
            self.injection_controller.update_valve_position(dt)
            total_time += dt
            
            # Valve position should increase
            if total_time < response_time:
                self.assertGreater(self.injection_controller.valve_position, 0.0)
                self.assertLess(self.injection_controller.valve_position, 1.0)
        
        # Should be fully open after response time
        self.assertEqual(self.injection_controller.valve_position, 1.0)
        self.assertEqual(self.injection_controller.valve_state, ValveState.OPEN)
    
    def test_injection_process_execution(self):
        """Test complete injection process execution."""
        # Create and add injection request
        request = FloaterInjectionRequest(
            floater_id="test_floater",
            depth=10.0,
            target_volume=0.02,  # 20L
            position=0.0,
            timestamp=0.0
        )
        
        self.injection_controller.add_injection_request(request)
        
        # Simulate injection process
        dt = 0.1
        current_time = 0.0
        supply_pressure = 350000.0  # 3.5 bar (adequate supply)
        
        # Run injection steps
        for _ in range(50):  # 5 seconds maximum
            results = self.injection_controller.injection_step(dt, current_time, supply_pressure)
            current_time += dt
            
            # Check if injection completed
            if (self.injection_controller.current_injection is None and 
                self.injection_controller.valve_state == ValveState.CLOSED):
                break
        
        # Verify injection was processed
        self.assertEqual(len(self.injection_controller.injection_queue), 0)
        self.assertGreater(self.injection_controller.total_injections, 0)
    
    def test_supply_pressure_checking(self):
        """Test supply pressure adequacy checking."""
        required_pressure = 250000.0  # 2.5 bar
        
        # Adequate supply pressure
        adequate_supply = 280000.0  # 2.8 bar
        can_supply = self.injection_controller.can_supply_injection_pressure(
            adequate_supply, required_pressure)
        self.assertTrue(can_supply)
        
        # Inadequate supply pressure
        inadequate_supply = 240000.0  # 2.4 bar
        cannot_supply = self.injection_controller.can_supply_injection_pressure(
            inadequate_supply, required_pressure)
        self.assertFalse(cannot_supply)
    
    def test_water_displacement_work_calculation(self):
        """Test water displacement work calculation."""
        injected_volume = 0.05  # 50L
        depth = 10.0  # 10m
        
        work = self.injection_controller.calculate_water_displacement_work(
            injected_volume, depth)
        
        # Work = ρ * g * V * H
        water_density = self.injection_controller.water_density
        gravity = self.injection_controller.gravity
        expected_work = water_density * gravity * injected_volume * depth
        
        self.assertAlmostEqual(work, expected_work, places=1)
        self.assertGreater(work, 0.0)
    
    def test_injection_system_reset(self):
        """Test injection system reset functionality."""
        # Set up some state
        self.injection_controller.valve_state = ValveState.OPEN
        self.injection_controller.valve_position = 0.5
        self.injection_controller.total_injections = 5
        
        # Add a request to queue
        request = FloaterInjectionRequest("test", 5.0, 0.02, 0.0, 0.0)
        self.injection_controller.add_injection_request(request)
        
        # Reset system
        self.injection_controller.reset_injection_system()
        
        # Verify reset
        self.assertEqual(self.injection_controller.valve_state, ValveState.CLOSED)
        self.assertEqual(self.injection_controller.valve_position, 0.0)
        self.assertEqual(len(self.injection_controller.injection_queue), 0)
        self.assertEqual(self.injection_controller.total_injections, 0)


class TestFloaterPneumaticEnhancements(unittest.TestCase):
    """Test the pneumatic enhancements to the Floater class."""
    
    def setUp(self):
        """Set up test floater."""
        self.floater = Floater(
            volume=0.1,  # 100L floater
            mass=10.0,   # 10kg
            area=0.5,    # 0.5m² cross-section
            position=0.0
        )
    
    def test_pneumatic_state_initialization(self):
        """Test pneumatic state initialization."""
        self.assertEqual(self.floater.pneumatic_fill_state, 'empty')
        self.assertEqual(self.floater.air_fill_level, 0.0)
        self.assertEqual(self.floater.pneumatic_pressure, 101325.0)
        self.assertFalse(self.floater.ready_for_injection)
    
    def test_position_based_state_updates(self):
        """Test position-based state flag updates."""
        # Test at bottom station
        self.floater.update_pneumatic_state(
            current_position=0.0,
            bottom_station_pos=0.0,
            position_tolerance=0.1
        )
        
        self.assertTrue(self.floater.at_bottom_station)
        self.assertFalse(self.floater.at_top_station)
        self.assertTrue(self.floater.ready_for_injection)
        
        # Test at top station
        self.floater.pneumatic_fill_state = 'full'
        self.floater.update_pneumatic_state(
            current_position=10.0,
            bottom_station_pos=0.0,
            top_station_pos=10.0,
            position_tolerance=0.1
        )
        
        self.assertFalse(self.floater.at_bottom_station)
        self.assertTrue(self.floater.at_top_station)
    
    def test_pneumatic_injection_process(self):
        """Test pneumatic injection process."""
        # Position floater at bottom station
        self.floater.update_pneumatic_state(0.0, 0.0, 10.0, 0.1)
        
        # Start injection
        target_volume = 0.05  # 50L
        injection_pressure = 250000.0  # 2.5 bar
        current_time = 0.0
        
        success = self.floater.start_pneumatic_injection(
            target_volume, injection_pressure, current_time)
        self.assertTrue(success)
        self.assertEqual(self.floater.pneumatic_fill_state, 'filling')
        
        # Simulate injection progress
        dt = 0.1
        injected_volume = 0.01  # 10L per step
        
        for _ in range(5):  # Inject 50L total
            self.floater.update_pneumatic_injection(injected_volume, dt)
        
        # Should be completed
        self.assertEqual(self.floater.pneumatic_fill_state, 'full')
        self.assertTrue(self.floater.injection_complete)
        self.assertEqual(self.floater.total_air_injected, target_volume)
    
    def test_pneumatic_venting_process(self):
        """Test pneumatic venting process."""
        # Set floater to full state at top station
        self.floater.pneumatic_fill_state = 'full'
        self.floater.air_fill_level = 1.0
        self.floater.total_air_injected = 0.05
        self.floater.update_pneumatic_state(10.0, 0.0, 10.0, 0.1)
        
        # Start venting
        success = self.floater.start_pneumatic_venting(0.0)
        self.assertTrue(success)
        self.assertEqual(self.floater.pneumatic_fill_state, 'venting')
          # Simulate venting progress
        dt = 0.1
        venting_rate = 0.02  # 20L/s
        
        complete = False
        for _ in range(30):  # Allow more time for complete venting
            complete = self.floater.update_pneumatic_venting(venting_rate, dt)
            if complete:
                break
        
        # Should be completed
        self.assertTrue(complete)
        self.assertEqual(self.floater.pneumatic_fill_state, 'empty')
        self.assertAlmostEqual(self.floater.air_fill_level, 0.0, places=2)
    
    def test_pneumatic_buoyant_force_calculation(self):
        """Test pneumatic buoyant force calculation with pressure effects."""
        # Set up floater with air
        self.floater.total_air_injected = 0.05  # 50L
        self.floater.pneumatic_pressure = 250000.0  # 2.5 bar
        
        # Test at surface (depth = 0)
        surface_force = self.floater.get_pneumatic_buoyant_force(0.0)
        self.assertGreater(surface_force, 0.0)
        
        # Test at depth (should be less due to compression)
        depth_force = self.floater.get_pneumatic_buoyant_force(10.0)
        self.assertGreater(depth_force, 0.0)
        self.assertLess(depth_force, surface_force)  # Air compressed at depth
    
    def test_pneumatic_status_reporting(self):
        """Test pneumatic status reporting."""
        status = self.floater.get_pneumatic_status()
        
        # Check all expected fields are present
        expected_fields = [
            'pneumatic_fill_state', 'air_fill_level', 'air_fill_percentage',
            'pneumatic_pressure_pa', 'pneumatic_pressure_bar',
            'total_air_injected_l', 'displaced_water_volume_l',
            'water_displacement_work_j', 'at_bottom_station', 'at_top_station',
            'ready_for_injection', 'injection_requested', 'injection_complete'
        ]
        
        for field in expected_fields:
            self.assertIn(field, status)
        
        # Check specific values
        self.assertEqual(status['pneumatic_fill_state'], 'empty')
        self.assertEqual(status['air_fill_percentage'], 0.0)


class TestIntegratedInjectionSystem(unittest.TestCase):
    """Test integrated injection system with air compression and control."""
    
    def setUp(self):
        """Set up integrated test system."""
        from simulation.pneumatics import (
            create_standard_kpp_compressor,
            create_standard_kpp_pressure_controller
        )
        
        # Create integrated pneumatic system
        self.air_system = create_standard_kpp_compressor()
        self.pressure_controller = create_standard_kpp_pressure_controller(2.5)
        self.injection_controller = create_standard_kpp_injection_controller()
        
        # Connect components
        self.pressure_controller.set_air_compressor(self.air_system)
        
        # Build up pressure first
        self._build_system_pressure()
    
    def _build_system_pressure(self):
        """Build up system pressure for testing."""
        dt = 1.0
        current_time = 0.0
        
        # Run pressure buildup for 60 seconds
        for _ in range(60):
            self.pressure_controller.control_step(dt, current_time)
            current_time += dt
            
            # Check if adequate pressure is reached
            if self.air_system.tank_pressure >= 250000.0:  # 2.5 bar
                break
    
    def test_coordinated_injection_cycle(self):
        """Test coordinated injection cycle with pressure control."""
        # Create floater and injection request
        floater = Floater(volume=0.1, mass=10.0, area=0.5, position=0.0)
        floater.update_pneumatic_state(0.0, 0.0, 10.0, 0.1)  # At bottom station
        
        request = FloaterInjectionRequest(
            floater_id="test_floater",
            depth=5.0,
            target_volume=0.05,  # 50L
            position=0.0,
            timestamp=0.0
        )
        
        # Add injection request
        self.injection_controller.add_injection_request(request)
        
        # Simulate coordinated operation
        dt = 0.1
        current_time = 0.0
        
        for _ in range(100):  # 10 seconds maximum
            # Update pressure control
            pressure_results = self.pressure_controller.control_step(dt, current_time)
            
            # Update injection control
            injection_results = self.injection_controller.injection_step(
                dt, current_time, self.air_system.tank_pressure)
              # Update floater if injection is active
            if injection_results['active_injection'] == "test_floater":
                # Start floater injection if not already started
                if floater.pneumatic_fill_state == 'empty':
                    floater.start_pneumatic_injection(
                        request.target_volume, 
                        request.injection_pressure, 
                        current_time
                    )
                
                air_consumed = injection_results['air_consumed']
                floater.update_pneumatic_injection(air_consumed, dt)
                
                # Consume air from tank
                if air_consumed > 0:
                    self.air_system.consume_air_from_tank(air_consumed)
            elif floater.pneumatic_fill_state == 'filling':
                # Injection controller finished, complete floater injection
                floater.complete_pneumatic_injection()
            
            current_time += dt
            
            # Check if injection completed
            if floater.injection_complete:
                break
        
        # Verify successful injection
        self.assertTrue(floater.injection_complete)
        self.assertEqual(floater.pneumatic_fill_state, 'full')
        self.assertGreater(floater.total_air_injected, 0.0)
    
    def test_multiple_floater_coordination(self):
        """Test coordination of multiple floater injections."""
        # Create multiple injection requests
        requests = []
        for i in range(3):
            request = FloaterInjectionRequest(
                floater_id=f"floater_{i}",
                depth=5.0 + i * 2.0,  # Different depths
                target_volume=0.03,   # 30L each
                position=0.0,
                timestamp=float(i)
            )
            requests.append(request)
            self.injection_controller.add_injection_request(request)
        
        # Simulate system operation
        dt = 0.1
        current_time = 0.0
        completed_injections = 0
        
        for _ in range(300):  # 30 seconds maximum
            # Update pressure control
            self.pressure_controller.control_step(dt, current_time)
            
            # Update injection control
            injection_results = self.injection_controller.injection_step(
                dt, current_time, self.air_system.tank_pressure)
            
            # Consume air from tank if injecting
            air_consumed = injection_results['air_consumed']
            if air_consumed > 0:
                self.air_system.consume_air_from_tank(air_consumed)
            
            current_time += dt
            
            # Check if all injections completed
            if self.injection_controller.total_injections >= 3:
                break
        
        # Verify all injections were processed
        self.assertGreaterEqual(self.injection_controller.total_injections, 3)
        self.assertEqual(len(self.injection_controller.injection_queue), 0)


if __name__ == '__main__':
    unittest.main()
