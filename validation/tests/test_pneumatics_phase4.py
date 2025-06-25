"""
Test Suite for Phase 4: Venting and Reset Mechanism

Tests the automatic venting system, air release dynamics, and floater
reset functionality of the pneumatic system.
"""

import pytest
import math
from simulation.pneumatics.venting_system import (
    AutomaticVentingSystem, VentingTrigger, AirReleasePhysics
)
from simulation.components.floater import Floater
from config.config import G, RHO_WATER

class TestVentingTrigger:
    """Test the venting trigger mechanisms."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.trigger_position = VentingTrigger(
            trigger_type="position",
            position_threshold=9.0
        )
        
        self.trigger_tilt = VentingTrigger(
            trigger_type="tilt", 
            tilt_angle_threshold=45.0
        )
        
        self.trigger_surface = VentingTrigger(
            trigger_type="surface_breach",
            surface_breach_depth=0.2
        )
    
    def test_position_trigger(self):
        """Test position-based venting trigger."""
        # Below threshold - no trigger
        assert not self.trigger_position.should_trigger_venting(8.5)
        
        # At threshold - trigger
        assert self.trigger_position.should_trigger_venting(9.0)
        
        # Above threshold - trigger
        assert self.trigger_position.should_trigger_venting(9.5)
    
    def test_tilt_trigger(self):
        """Test tilt-based venting trigger."""
        # No tilt - no trigger
        assert not self.trigger_tilt.should_trigger_venting(5.0, 0.0)
        
        # Small tilt - no trigger
        assert not self.trigger_tilt.should_trigger_venting(5.0, math.radians(30))
        
        # Large tilt - trigger (positive)
        assert self.trigger_tilt.should_trigger_venting(5.0, math.radians(50))
        
        # Large tilt - trigger (negative)
        assert self.trigger_tilt.should_trigger_venting(5.0, math.radians(-50))
    
    def test_surface_breach_trigger(self):
        """Test surface breach venting trigger."""
        tank_height = 10.0
        
        # Deep underwater - no trigger
        assert not self.trigger_surface.should_trigger_venting(5.0, 0.0, tank_height)
        
        # Near surface but not breaching - no trigger
        assert not self.trigger_surface.should_trigger_venting(9.5, 0.0, tank_height)
        
        # Surface breach - trigger
        assert self.trigger_surface.should_trigger_venting(9.9, 0.0, tank_height)
        
        # Above surface - trigger
        assert self.trigger_surface.should_trigger_venting(10.1, 0.0, tank_height)


class TestAirReleasePhysics:
    """Test air release and water inflow physics."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.physics = AirReleasePhysics()
    
    def test_air_release_rate_calculation(self):
        """Test air release rate under different pressure conditions."""
        # High pressure difference - should have significant flow
        internal_pressure = 300000.0  # 3 bar
        external_pressure = 101325.0  # 1 bar
        
        flow_rate = self.physics.calculate_air_release_rate(
            internal_pressure, external_pressure)
        
        assert flow_rate > 0.0
        assert flow_rate < 1.0  # Reasonable upper bound
        
        # No pressure difference - no flow
        no_flow = self.physics.calculate_air_release_rate(
            external_pressure, external_pressure)
        
        assert no_flow == 0.0
        
        # Reverse pressure - no flow
        reverse_flow = self.physics.calculate_air_release_rate(
            external_pressure, internal_pressure)
        
        assert reverse_flow == 0.0
    
    def test_choked_vs_subsonic_flow(self):
        """Test that choked flow is properly identified."""
        external_pressure = 101325.0  # 1 bar
        
        # High pressure ratio - should be choked flow
        high_internal = 300000.0  # 3 bar
        choked_flow = self.physics.calculate_air_release_rate(
            high_internal, external_pressure)
        
        # Medium pressure ratio - should be subsonic
        medium_internal = 150000.0  # 1.5 bar
        subsonic_flow = self.physics.calculate_air_release_rate(
            medium_internal, external_pressure)
        
        # Choked flow should be higher than subsonic for equivalent conditions
        assert choked_flow > subsonic_flow
    
    def test_water_inflow_rate_calculation(self):
        """Test water inflow rate calculation."""
        floater_total_volume = 0.01  # 10 liters
        floater_air_volume = 0.005   # 5 liters air
        depth = 5.0  # 5 meters deep
        
        inflow_rate = self.physics.calculate_water_inflow_rate(
            floater_air_volume, floater_total_volume, depth)
        
        assert inflow_rate > 0.0
        assert inflow_rate < 0.1  # Reasonable upper bound
        
        # No available volume - no inflow
        no_inflow = self.physics.calculate_water_inflow_rate(
            floater_total_volume, floater_total_volume, depth)
        
        assert no_inflow == 0.0
        
        # Deeper water should increase inflow rate
        deep_inflow = self.physics.calculate_water_inflow_rate(
            floater_air_volume, floater_total_volume, 10.0)
        
        assert deep_inflow > inflow_rate
    
    def test_bubble_escape_time(self):
        """Test bubble escape time calculation."""
        depth = 5.0
        bubble_volume = 0.001  # 1 liter
        
        escape_time = self.physics.calculate_bubble_escape_time(depth, bubble_volume)
        
        # Should be reasonable time
        assert escape_time > 0.0
        assert escape_time < 100.0  # Less than 100 seconds
        
        # Deeper should take longer
        deep_time = self.physics.calculate_bubble_escape_time(10.0, bubble_volume)
        assert deep_time > escape_time


class TestAutomaticVentingSystem:
    """Test the complete automatic venting system."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.venting_system = AutomaticVentingSystem(
            trigger_config={
                'trigger_type': 'position',
                'position_threshold': 9.0
            },
            tank_height=10.0
        )
    
    def test_system_initialization(self):
        """Test venting system initialization."""
        assert self.venting_system.tank_height == 10.0
        assert self.venting_system.trigger.position_threshold == 9.0
        assert len(self.venting_system.active_venting_floaters) == 0
    
    def test_venting_trigger_check(self):
        """Test venting trigger checking."""
        floater_id = "test_floater_1"
        
        # Below threshold - no trigger
        assert not self.venting_system.check_venting_trigger(floater_id, 8.5)
        
        # Above threshold - trigger
        assert self.venting_system.check_venting_trigger(floater_id, 9.5)
        
        # Start venting process
        self.venting_system.start_venting(
            floater_id, 0.005, 200000.0, 0.01, 0.0)
        
        # Already venting - no trigger
        assert not self.venting_system.check_venting_trigger(floater_id, 9.5)
    
    def test_start_venting_process(self):
        """Test starting the venting process."""
        floater_id = "test_floater_2"
        initial_air_volume = 0.008  # 8 liters
        initial_pressure = 250000.0  # 2.5 bar
        total_volume = 0.01  # 10 liters
        
        state = self.venting_system.start_venting(
            floater_id, initial_air_volume, initial_pressure, total_volume, 10.0)
        
        assert state['floater_id'] == floater_id
        assert state['initial_air_volume'] == initial_air_volume
        assert state['current_air_volume'] == initial_air_volume
        assert state['initial_air_pressure'] == initial_pressure
        assert not state['venting_complete']        # Should be in active tracking
        assert floater_id in self.venting_system.active_venting_floaters

    def test_venting_process_update(self):
        """Test updating the venting process."""
        floater_id = "test_floater_3"
        
        # Start venting with less initial water to ensure room for increase
        self.venting_system.start_venting(
            floater_id, 0.006, 200000.0, 0.01, 0.005)  # Start with less water
        
        initial_state = self.venting_system.get_venting_status(floater_id)
        assert initial_state is not None
        initial_air = initial_state['current_air_volume']
        initial_water = initial_state['water_volume']
        
        # Update venting process with larger time step for more visible change
        dt = 0.5  # Larger time step
        updated_state = self.venting_system.update_venting_process(
            floater_id, 9.0, dt)  # At 9m position
        
        # Air volume should decrease
        assert updated_state['current_air_volume'] < initial_air
        
        # Total released should increase
        assert updated_state['total_air_released'] > 0.0
        
        # Water volume should increase
        assert updated_state['water_volume'] > initial_water
    
    def test_complete_venting_cycle(self):
        """Test a complete venting cycle to completion."""
        floater_id = "test_floater_4"
        
        # Start with small air volume for quick completion
        self.venting_system.start_venting(
            floater_id, 0.001, 150000.0, 0.01, 0.0)
        
        # Run multiple updates to complete venting
        dt = 0.1
        max_steps = 100
        
        for step in range(max_steps):
            state = self.venting_system.update_venting_process(
                floater_id, 9.0, dt)
            
            if state['venting_complete']:
                break
        
        # Should have completed
        final_state = self.venting_system.get_venting_status(floater_id)
        assert final_state is not None, "Venting status should not be None"
        assert final_state['venting_complete']
        assert final_state['current_air_volume'] <= 0.001
        assert final_state['vent_completion_time'] is not None
    
    def test_cleanup_completed_venting(self):
        """Test cleanup of completed venting processes."""
        floater_id = "test_floater_5"
        
        # Start and immediately complete venting
        state = self.venting_system.start_venting(
            floater_id, 0.001, 150000.0, 0.01, 0.0)
        
        # Manually complete for testing
        self.venting_system.complete_venting(floater_id, 1.0)
        
        # Should be marked complete but still tracked
        assert floater_id in self.venting_system.active_venting_floaters
        
        # Cleanup
        cleaned = self.venting_system.cleanup_completed_venting(floater_id)
        assert cleaned
        assert floater_id not in self.venting_system.active_venting_floaters
    
    def test_system_status(self):
        """Test system status reporting."""
        # Initial status
        status = self.venting_system.get_system_status()
        assert status['active_venting_count'] == 0
        assert status['trigger_type'] == 'position'
        
        # Start some venting processes
        self.venting_system.start_venting("floater_1", 0.005, 200000.0, 0.01, 0.0)
        self.venting_system.start_venting("floater_2", 0.003, 180000.0, 0.01, 0.0)
        
        status = self.venting_system.get_system_status()
        assert status['active_venting_count'] == 2
        assert status['processing_venting_count'] == 2


class TestFloaterVentingIntegration:
    """Test floater integration with venting system."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.floater = Floater(
            volume=0.01,
            mass=5.0,
            area=0.1,
            tank_height=10.0
        )
        
        self.venting_system = AutomaticVentingSystem(
            tank_height=10.0
        )
    
    def test_floater_venting_trigger_check(self):
        """Test floater venting trigger checking."""
        # Position floater at venting position
        self.floater.position = 9.5
        
        # Should trigger venting
        should_vent = self.floater.check_venting_trigger(self.venting_system)
        assert should_vent
        
        # Position below threshold
        self.floater.position = 8.0
        should_vent = self.floater.check_venting_trigger(self.venting_system)
        assert not should_vent
    
    def test_floater_start_venting(self):
        """Test starting venting process from floater."""
        # Set up floater with air
        self.floater.pneumatic_fill_state = 'full'
        self.floater.total_air_injected = 0.006  # 6 liters
        self.floater.current_air_pressure = 220000.0
        self.floater.position = 9.2
          # Start venting
        success = self.floater.start_venting_process(self.venting_system, 10.0)
        assert success
        assert self.floater.pneumatic_fill_state == 'venting'
        
        # Check venting system has the process
        floater_id = f"floater_{id(self.floater)}"
        assert floater_id in self.venting_system.active_venting_floaters

    def test_floater_venting_process_update(self):
        """Test floater venting process updates."""
        # Set up floater and start venting
        self.floater.pneumatic_fill_state = 'full'
        self.floater.total_air_injected = 0.008  # 8 liters - less than floater volume (10L)
        self.floater.current_air_pressure = 160000.0  # Lower pressure
        self.floater.position = 15.0  # Deeper position for more controlled venting
        
        self.floater.start_venting_process(self.venting_system, 0.0)
        
        initial_air = self.floater.total_air_injected
        
        # Update venting process with very small time step
        dt = 0.001  # Very small time step to prevent immediate completion
        is_complete = self.floater.update_venting_process(self.venting_system, dt)
        
        # Air should be reduced
        assert self.floater.total_air_injected < initial_air
        
        # Water mass should increase (should be positive now)
        assert self.floater.water_mass > 0.0
        
        # Should not be complete yet with small time step
        assert not is_complete
    
    def test_complete_venting_integration(self):
        """Test complete venting process integration."""
        # Set up floater with small air volume for quick completion
        self.floater.pneumatic_fill_state = 'full'
        self.floater.total_air_injected = 0.001  # 1 liter
        self.floater.current_air_pressure = 150000.0
        self.floater.position = 9.0
        
        # Start venting
        self.floater.start_venting_process(self.venting_system, 0.0)
        
        # Run until completion
        dt = 0.1
        max_steps = 200
        
        for step in range(max_steps):
            is_complete = self.floater.update_venting_process(self.venting_system, dt)
            if is_complete:
                break
        
        # Should be complete and reset
        assert self.floater.pneumatic_fill_state == 'empty'
        assert self.floater.total_air_injected <= 0.001
        assert self.floater.is_ready_for_descent()
        
        # Water mass should be nearly full volume
        expected_water_mass = RHO_WATER * self.floater.volume
        assert abs(self.floater.water_mass - expected_water_mass) < 0.1
    
    def test_floater_ready_for_descent(self):
        """Test floater readiness for descent after venting."""
        # Empty floater should not be ready
        assert not self.floater.is_ready_for_descent()
        
        # Set up as if venting just completed
        self.floater.pneumatic_fill_state = 'empty'
        self.floater.total_air_injected = 0.0
        self.floater.water_mass = RHO_WATER * self.floater.volume
        
        # Should be ready for descent
        assert self.floater.is_ready_for_descent()


class TestIntegratedVentingSystem:
    """Test complete venting system integration."""
    
    def test_complete_ascent_venting_descent_cycle(self):
        """Test complete cycle from ascent through venting to descent readiness."""
        # Create floater and venting system
        floater = Floater(
            volume=0.01,        # 10 liters
            mass=6.0,           # 6 kg
            area=0.1,
            tank_height=10.0
        )
        
        venting_system = AutomaticVentingSystem(tank_height=10.0)
        
        # Phase 1: Set up floater with air (simulating completed ascent)
        floater.pneumatic_fill_state = 'full'
        floater.total_air_injected = 0.007  # 7 liters
        floater.current_air_pressure = 180000.0  # Expanded pressure at top
        floater.position = 9.3  # Near top
        
        # Phase 2: Check venting trigger
        should_vent = floater.check_venting_trigger(venting_system)
        assert should_vent
        
        # Phase 3: Start venting
        venting_started = floater.start_venting_process(venting_system, 20.0)
        assert venting_started
        
        # Phase 4: Run venting process to completion
        dt = 0.05  # Small time steps for accuracy
        max_steps = 1000
        
        venting_steps = 0
        for step in range(max_steps):
            is_complete = floater.update_venting_process(venting_system, dt)
            venting_steps += 1
            
            if is_complete:
                break
        
        # Phase 5: Verify completion
        assert floater.is_ready_for_descent()
        assert floater.pneumatic_fill_state == 'empty'
        assert venting_steps < max_steps  # Should complete before timeout
        
        # Phase 6: Verify physics consistency
        # Most air should be released
        assert floater.total_air_injected < 0.001  # Less than 1 liter remaining
        
        # Floater should be heavy (full of water)
        net_force = floater.compute_enhanced_buoyant_force() - floater.mass * G
        assert net_force < 0  # Should sink
        
        print(f"Venting completed in {venting_steps} steps ({venting_steps*dt:.2f}s)")
        print(f"Final air volume: {floater.total_air_injected*1000:.1f}L")
        print(f"Final water mass: {floater.water_mass:.1f}kg")
        print(f"Net force: {net_force:.1f}N (negative = sinking)")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
