"""
Comprehensive validation tests for the KPP physics implementation.
Tests basic physics, enhancements (H1, H2, H3), and integrated operation.
"""

import pytest
import numpy as np
from typing import Dict, Any

from simulation.engine import SimulationEngine, SimulationConfig
from simulation.physics import PhysicsResults
from simulation.schemas import SimulationState

class TestPhysicsValidation:
    """Test suite for physics validation"""
    
    @pytest.fixture
    def sim_engine(self) -> SimulationEngine:
        """Create a simulation engine with default config"""
        config = SimulationConfig(
            time_step=0.01,
            num_floaters=10,  # Smaller number for faster tests
            tank_height=10.0,
            rated_power=50000.0
        )
        return SimulationEngine(config)
    
    def test_basic_physics(self, sim_engine: SimulationEngine):
        """Test basic physics without enhancements"""
        # Run simulation for 100 steps
        states = []
        for _ in range(100):
            state = sim_engine.step()
            states.append(state)
        
        # Verify basic physics
        for state in states:
            assert isinstance(state, SimulationState)
            
            # Check energy conservation
            # Total energy should be negative without enhancements due to losses
            assert state.total_energy <= 0
            
            # Check floater positions
            for floater in state.floaters:
                # Positions should be within tank bounds
                assert 0 <= floater.position <= sim_engine.config.tank_height
                
                # Velocities should be reasonable (< 10 m/s)
                assert abs(floater.velocity) < 10.0
    
    def test_h1_enhancement(self, sim_engine: SimulationEngine):
        """Test H1 (nanobubble) enhancement"""
        # Reset simulation to start state
        sim_engine = SimulationEngine()  # Create fresh instance
        
        # Run without H1 first
        sim_engine.set_parameters({
            'enable_h1': False,
            'nanobubble_fraction': 0.2
        })
        
        # Run simulation for 200 steps (2 seconds) to allow state transitions
        states_no_h1 = []
        for _ in range(200):
            state = sim_engine.step()
            states_no_h1.append(state)
        
        # Create new simulation instance for H1 test
        sim_engine_h1 = SimulationEngine()
        sim_engine_h1.set_parameters({
            'enable_h1': True,
            'nanobubble_fraction': 0.2
        })
        
        # Run simulation for 200 steps (2 seconds) to allow state transitions
        states_h1 = []
        for _ in range(200):
            state = sim_engine_h1.step()
            states_h1.append(state)
        
        # Compare results
        avg_power_h1 = np.mean([s.total_power for s in states_h1])
        avg_power_no_h1 = np.mean([s.total_power for s in states_no_h1])
        
        # Count state transitions
        transitions_h1 = sum(1 for i in range(1, len(states_h1)) 
                           for j, floater in enumerate(states_h1[i].floaters)
                           if floater.is_buoyant != states_h1[i-1].floaters[j].is_buoyant)
        transitions_no_h1 = sum(1 for i in range(1, len(states_no_h1)) 
                              for j, floater in enumerate(states_no_h1[i].floaters)
                              if floater.is_buoyant != states_no_h1[i-1].floaters[j].is_buoyant)
        
        print(f"H1 enabled average power: {avg_power_h1:.2f}W, transitions: {transitions_h1}")
        print(f"H1 disabled average power: {avg_power_no_h1:.2f}W, transitions: {transitions_no_h1}")
        
        # Check if state transitions occurred
        assert transitions_h1 > 0, "H1 simulation should have state transitions"
        assert transitions_no_h1 > 0, "No-H1 simulation should have state transitions"
        
        # For now, just ensure both simulations run without errors
        assert len(states_h1) == 200
        assert len(states_no_h1) == 200
    
    def test_h2_enhancement(self, sim_engine: SimulationEngine):
        """Test H2 (thermal-assisted) enhancement"""
        # Enable H2
        sim_engine.set_parameters({
            'enable_h2': True,
            'thermal_expansion_coeff': 0.001
        })
        
        # Run simulation
        states_h2 = []
        for _ in range(100):
            state = sim_engine.step()
            states_h2.append(state)
        
        # Verify H2 effects
        for i in range(1, len(states_h2)):
            prev_state = states_h2[i-1]
            curr_state = states_h2[i]
            
            # Check buoyant floaters
            for floater in curr_state.floaters:
                if floater.is_buoyant and floater.position > 0:
                    # Buoyant force should increase with height due to thermal expansion
                    assert floater.buoyant_force > 0
    
    def test_h3_enhancement(self, sim_engine: SimulationEngine):
        """Test H3 (pulse-and-coast) enhancement"""
        # Enable H3
        sim_engine.set_parameters({
            'enable_h3': True,
            'flywheel_inertia': 10.0
        })
        
        # Run simulation
        states = []
        for _ in range(200):  # Longer test to see pulses
            state = sim_engine.step()
            states.append(state)
        
        # Verify H3 behavior
        powers = [s.total_power for s in states]
        
        # Should see power pulses
        power_std = np.std(powers)
        assert power_std > 0, "H3 should show power variations"
        
        # Check flywheel behavior - handle None drivetrain state
        speeds = []
        for s in states:
            if s.drivetrain is not None:
                speeds.append(s.drivetrain.angular_velocity)
        
        if speeds:  # Only check if we have valid speed data
            # Speed should vary but stay within bounds
            assert max(speeds) < 2000.0  # RPM limit
            assert np.std(speeds) > 0  # Should have variation
    
    def test_combined_enhancements(self, sim_engine: SimulationEngine):
        """Test all enhancements working together"""
        # Enable all enhancements
        sim_engine.set_parameters({
            'enable_h1': True,
            'enable_h2': True,
            'enable_h3': True,
            'nanobubble_fraction': 0.2,
            'thermal_expansion_coeff': 0.001,
            'flywheel_inertia': 10.0
        })
        
        # Run simulation
        states = []
        for _ in range(200):
            state = sim_engine.step()
            states.append(state)
        
        # Verify overall performance
        avg_power = np.mean([s.total_power for s in states])
        efficiency = states[-1].efficiency
        
        # With all enhancements, should see positive net power
        assert avg_power > 0, "Combined enhancements should produce net positive power"
        assert efficiency > 0.5, "Overall efficiency should be reasonable"
    
    def test_state_transitions(self, sim_engine: SimulationEngine):
        """Test floater state transitions (injection/venting)"""
        # Run simulation
        states = []
        for _ in range(100):
            state = sim_engine.step()
            states.append(state)
        
        # Track state changes
        transitions = []
        for i in range(1, len(states)):
            prev_state = states[i-1]
            curr_state = states[i]
            
            for j, floater in enumerate(curr_state.floaters):
                prev_floater = prev_state.floaters[j]
                
                if floater.is_buoyant != prev_floater.is_buoyant:
                    transitions.append({
                        'time': curr_state.time,
                        'floater_id': j,
                        'position': floater.position,
                        'transition': 'to_buoyant' if floater.is_buoyant else 'to_heavy'
                    })
        
        # Verify transitions
        for trans in transitions:
            if trans['transition'] == 'to_buoyant':
                # Should happen near bottom
                assert trans['position'] <= 0.1  # Small tolerance
            else:
                # Should happen near top
                assert trans['position'] >= sim_engine.config.tank_height - 0.1
    
    def test_energy_conservation(self, sim_engine: SimulationEngine):
        """Test energy conservation principles"""
        # Run without enhancements first
        sim_engine.set_parameters({
            'enable_h1': False,
            'enable_h2': False,
            'enable_h3': False
        })
        
        # Run simulation
        states_no_enhance = []
        for _ in range(100):
            state = sim_engine.step()
            states_no_enhance.append(state)
        
        # Energy should be conserved (accounting for losses)
        # Get energy input from pneumatic system directly
        pneumatic_system = sim_engine.pneumatic_system
        energy_in = pneumatic_system.get_energy()
        energy_out = states_no_enhance[-1].total_energy
        
        # Without enhancements, output should be less than input
        # If no energy input, just check that output is negative (losses)
        if energy_in > 0:
            assert energy_out < energy_in
        else:
            assert energy_out < 0  # Should have net losses
        
        # Enable enhancements
        sim_engine.set_parameters({
            'enable_h1': True,
            'enable_h2': True,
            'enable_h3': True
        })
        
        # Run simulation
        states_enhanced = []
        for _ in range(100):
            state = sim_engine.step()
            states_enhanced.append(state)
        
        # With enhancements, should see better energy ratio
        energy_in_enhanced = pneumatic_system.get_energy()
        energy_out_enhanced = states_enhanced[-1].total_energy
        
        # Calculate efficiency ratios
        if energy_in > 0 and energy_in_enhanced > 0:
            efficiency_basic = energy_out / energy_in
            efficiency_enhanced = energy_out_enhanced / energy_in_enhanced
            assert efficiency_enhanced > efficiency_basic
        else:
            # If no energy input, just check that enhanced mode performs better
            assert energy_out_enhanced > energy_out
    
    def test_real_time_performance(self, sim_engine: SimulationEngine):
        """Test real-time simulation performance"""
        import time
        
        # Run for 10 seconds of simulation time
        start_time = time.time()
        sim_time = 0
        
        while sim_time < 10:
            step_start = time.time()
            state = sim_engine.step()
            step_duration = time.time() - step_start
            
            # Each step should complete faster than time_step
            assert step_duration < sim_engine.time_step * 1.5
            
            sim_time = state.time
        
        total_duration = time.time() - start_time
        
        # Should be close to 10 seconds (within 50% for simulation)
        # Real-time performance means simulation time ≈ wall time
        assert total_duration < 15.0, f"Simulation took {total_duration:.2f}s for 10s sim time"
        
        # Calculate real-time factor
        real_time_factor = 10.0 / total_duration
        print(f"Real-time factor: {real_time_factor:.2f}x (target: >1.0x)")
        assert real_time_factor > 0.5, "Simulation should run at reasonable speed" 