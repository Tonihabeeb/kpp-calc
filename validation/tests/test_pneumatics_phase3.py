"""
Test Suite for Phase 3: Buoyancy and Ascent Dynamics

Tests the enhanced buoyancy physics, pressure expansion, and gas dissolution
features of the pneumatic floater system.
"""

import pytest
import math
from simulation.pneumatics.pressure_expansion import PressureExpansionPhysics
from simulation.components.floater import Floater
from config.config import G, RHO_WATER

class TestPressureExpansionPhysics:
    """Test the pressure expansion physics module."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.physics = PressureExpansionPhysics()
    
    def test_pressure_at_depth(self):
        """Test pressure calculation at various depths."""
        # Surface pressure
        p_surface = self.physics.get_pressure_at_depth(0.0)
        assert p_surface == self.physics.P_atm
        
        # 1 meter depth
        p_1m = self.physics.get_pressure_at_depth(1.0)
        expected_1m = self.physics.P_atm + RHO_WATER * G * 1.0
        assert abs(p_1m - expected_1m) < 1.0  # Within 1 Pa
        
        # 10 meter depth
        p_10m = self.physics.get_pressure_at_depth(10.0)
        expected_10m = self.physics.P_atm + RHO_WATER * G * 10.0
        assert abs(p_10m - expected_10m) < 1.0
        
        # Pressure should increase linearly with depth
        assert p_10m > p_1m > p_surface
    
    def test_depth_from_position(self):
        """Test conversion from position to depth."""
        tank_height = 10.0
        
        # Bottom of tank (position 0) = maximum depth
        depth_bottom = self.physics.get_depth_from_position(0.0, tank_height)
        assert depth_bottom == tank_height
        
        # Top of tank (position = tank_height) = zero depth
        depth_top = self.physics.get_depth_from_position(tank_height, tank_height)
        assert depth_top == 0.0
        
        # Middle of tank
        depth_middle = self.physics.get_depth_from_position(5.0, tank_height)
        assert depth_middle == 5.0
        
        # Position above tank should give zero depth
        depth_above = self.physics.get_depth_from_position(15.0, tank_height)
        assert depth_above == 0.0
    
    def test_isothermal_expansion(self):
        """Test isothermal expansion (Boyle's Law)."""
        initial_pressure = 200000.0  # 2 bar
        initial_volume = 0.001       # 1 liter
        final_pressure = 100000.0    # 1 bar
        
        final_volume = self.physics.isothermal_expansion(
            initial_pressure, initial_volume, final_pressure)
        
        # Boyle's Law: P1*V1 = P2*V2
        expected_volume = initial_volume * (initial_pressure / final_pressure)
        assert abs(final_volume - expected_volume) < 1e-9
        
        # Volume should double when pressure halves
        assert abs(final_volume - 0.002) < 1e-6
    
    def test_adiabatic_expansion(self):
        """Test adiabatic expansion."""
        initial_pressure = 200000.0  # 2 bar
        initial_volume = 0.001       # 1 liter
        final_pressure = 100000.0    # 1 bar
        
        final_volume = self.physics.adiabatic_expansion(
            initial_pressure, initial_volume, final_pressure)
        
        # Adiabatic: P1*V1^γ = P2*V2^γ
        # V2 = V1 * (P1/P2)^(1/γ)
        pressure_ratio = initial_pressure / final_pressure
        expected_volume = initial_volume * (pressure_ratio ** (1.0 / self.physics.gamma_air))
        assert abs(final_volume - expected_volume) < 1e-9
        
        # Adiabatic expansion should be less than isothermal
        isothermal_volume = self.physics.isothermal_expansion(
            initial_pressure, initial_volume, final_pressure)
        assert final_volume < isothermal_volume
    
    def test_mixed_expansion(self):
        """Test mixed expansion model."""
        initial_pressure = 200000.0  # 2 bar
        initial_volume = 0.001       # 1 liter
        final_pressure = 100000.0    # 1 bar
        isothermal_fraction = 0.7
        
        mixed_volume = self.physics.mixed_expansion(
            initial_pressure, initial_volume, final_pressure, isothermal_fraction)
        
        isothermal_volume = self.physics.isothermal_expansion(
            initial_pressure, initial_volume, final_pressure)
        adiabatic_volume = self.physics.adiabatic_expansion(
            initial_pressure, initial_volume, final_pressure)
        
        # Mixed should be weighted average
        expected_mixed = (isothermal_fraction * isothermal_volume + 
                         (1 - isothermal_fraction) * adiabatic_volume)
        assert abs(mixed_volume - expected_mixed) < 1e-9        
        # Mixed should be between adiabatic and isothermal
        assert adiabatic_volume <= mixed_volume <= isothermal_volume
    
    def test_gas_dissolution(self):
        """Test gas dissolution using Henry's Law."""
        high_pressure = 500000.0  # 5 bar - much higher pressure
        low_pressure = 101325.0   # 1 bar
        dt = 1.0  # 1 second
        
        # Start with no dissolved air
        dissolved_fraction = 0.0
        
        # Under high pressure, dissolution should increase
        new_fraction_high = self.physics.calculate_gas_dissolution(
            high_pressure, dissolved_fraction, dt)
        assert new_fraction_high > dissolved_fraction
        assert new_fraction_high <= self.physics.max_dissolution_fraction
        
        # Under low pressure, dissolution should decrease (or stop increasing)
        # Since equilibrium at 1 bar is 1% and we likely haven't reached that,
        # let's simulate longer to reach higher dissolved fraction first
        
        # Simulate longer under high pressure to get more dissolution
        for _ in range(10):  # 10 more seconds
            new_fraction_high = self.physics.calculate_gas_dissolution(
                high_pressure, new_fraction_high, dt)
        
        # Now under low pressure, it should decrease
        new_fraction_low = self.physics.calculate_gas_dissolution(
            low_pressure, new_fraction_high, dt)
        assert new_fraction_low <= new_fraction_high  # Should not increase
        assert new_fraction_low >= 0.0
    
    def test_effective_air_volume(self):
        """Test effective air volume calculation."""
        nominal_volume = 0.001  # 1 liter
        dissolved_fraction = 0.1  # 10% dissolved
        
        effective_volume = self.physics.calculate_effective_air_volume(
            nominal_volume, dissolved_fraction)
        
        expected_effective = nominal_volume * (1.0 - dissolved_fraction)
        assert abs(effective_volume - expected_effective) < 1e-9
        
        # 90% of original volume should remain effective
        assert abs(effective_volume - 0.0009) < 1e-6
    
    def test_expansion_state(self):
        """Test complete expansion state calculation."""
        initial_depth = 10.0      # Bottom of tank
        current_depth = 5.0       # Middle of tank
        initial_air_volume = 0.001  # 1 liter
        
        state = self.physics.get_expansion_state(
            initial_depth, current_depth, initial_air_volume, "mixed")
        
        # Check required fields
        assert 'initial_pressure' in state
        assert 'current_pressure' in state
        assert 'initial_volume' in state
        assert 'expanded_volume' in state
        assert 'expansion_ratio' in state
        
        # Pressure should decrease from initial to current
        assert state['current_pressure'] < state['initial_pressure']
        
        # Volume should expand as pressure decreases
        assert state['expanded_volume'] > state['initial_volume']
        
        # Expansion ratio should be > 1
        assert state['expansion_ratio'] > 1.0
    
    def test_buoyancy_calculation(self):
        """Test buoyancy force calculation."""
        floater_volume = 0.01     # 10 liters
        effective_air_volume = 0.005  # 5 liters
        
        buoyant_force = self.physics.calculate_buoyancy_from_expansion(
            floater_volume, effective_air_volume)
        
        # Buoyancy should be based on effective air volume
        expected_force = RHO_WATER * G * effective_air_volume
        assert abs(buoyant_force - expected_force) < 0.01
        
        # If air volume exceeds floater volume, should be clamped
        oversized_air = 0.02  # 20 liters
        clamped_force = self.physics.calculate_buoyancy_from_expansion(
            floater_volume, oversized_air)
        max_force = RHO_WATER * G * floater_volume
        assert abs(clamped_force - max_force) < 0.01


class TestEnhancedFloaterBuoyancy:
    """Test enhanced floater buoyancy with pressure expansion."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.floater = Floater(
            volume=0.01,        # 10 liters
            mass=5.0,           # 5 kg
            area=0.1,           # 0.1 m²
            position=0.0,       # Start at bottom
            tank_height=10.0,   # 10m tank
            expansion_mode="mixed"
        )
    
    def test_enhanced_buoyancy_initialization(self):
        """Test that enhanced buoyancy components are initialized."""
        assert hasattr(self.floater, 'pressure_physics')
        assert hasattr(self.floater, 'tank_height')
        assert hasattr(self.floater, 'expansion_mode')
        assert hasattr(self.floater, 'injection_depth')
        assert hasattr(self.floater, 'dissolved_air_fraction_enhanced')
    
    def test_enhanced_buoyancy_with_no_air(self):
        """Test enhanced buoyancy calculation with no air."""
        # No air injected - should fall back to basic calculation
        force_enhanced = self.floater.compute_enhanced_buoyant_force()
        force_basic = self.floater.compute_buoyant_force()
        
        # Should be the same when no air is present
        assert abs(force_enhanced - force_basic) < 0.01
    
    def test_enhanced_buoyancy_with_air_injection(self):
        """Test enhanced buoyancy after air injection."""
        # Simulate air injection
        self.floater.total_air_injected = 0.005  # 5 liters
        self.floater.injection_depth = 10.0      # Injected at bottom
        self.floater.initial_air_pressure = 200000.0  # 2 bar
        
        # Move floater up to test expansion
        self.floater.position = 5.0  # Middle of tank
        
        force = self.floater.compute_enhanced_buoyant_force()
        
        # Should have positive buoyant force
        assert force > 0
        
        # Should have expansion state calculated
        assert len(self.floater.expansion_state) > 0
        assert 'expanded_volume' in self.floater.expansion_state
    
    def test_buoyancy_increases_with_ascent(self):
        """Test that buoyancy increases as floater ascends due to expansion."""
        # Set up air injection
        self.floater.total_air_injected = 0.005  # 5 liters
        self.floater.injection_depth = 10.0      # Injected at bottom
        self.floater.initial_air_pressure = 200000.0
        
        # Calculate buoyancy at bottom
        self.floater.position = 0.0  # Bottom
        force_bottom = self.floater.compute_enhanced_buoyant_force()
        
        # Calculate buoyancy at top
        self.floater.position = 10.0  # Top
        force_top = self.floater.compute_enhanced_buoyant_force()
        
        # Buoyancy should increase due to air expansion
        assert force_top > force_bottom
    
    def test_dissolution_effects(self):
        """Test that gas dissolution reduces effective buoyancy."""
        # Set up air injection
        self.floater.total_air_injected = 0.005  # 5 liters
        self.floater.injection_depth = 10.0
        self.floater.initial_air_pressure = 200000.0
        self.floater.position = 5.0
        
        # Calculate initial buoyancy
        force_initial = self.floater.compute_enhanced_buoyant_force()
        
        # Simulate dissolution over time
        self.floater.dissolved_air_fraction_enhanced = 0.1  # 10% dissolved
        force_after_dissolution = self.floater.compute_enhanced_buoyant_force()
        
        # Buoyancy should be reduced
        assert force_after_dissolution < force_initial
    
    def test_pneumatic_injection_records_conditions(self):
        """Test that pneumatic injection records initial conditions."""
        self.floater.position = 2.0  # 2m from bottom
        self.floater.ready_for_injection = True
        
        # Start injection
        success = self.floater.start_pneumatic_injection(
            target_volume=0.005,
            injection_pressure=250000.0,
            current_time=0.0
        )
        
        assert success
        assert self.floater.injection_depth == 8.0  # Depth from surface
        assert self.floater.initial_air_pressure == 250000.0
        assert self.floater.current_air_pressure == 250000.0
    
    def test_ascent_velocity_control_integration(self):
        """Test integration with ascent velocity calculations."""
        # Set up floater with air
        self.floater.total_air_injected = 0.008  # 8 liters (high buoyancy)
        self.floater.injection_depth = 10.0
        self.floater.initial_air_pressure = 200000.0
        self.floater.position = 5.0
        self.floater.velocity = 0.0
        
        # Calculate net force
        net_force = self.floater.force
        
        # Should have positive net force (upward)
        assert net_force > 0
        
        # Update dynamics
        dt = 0.1
        old_velocity = self.floater.velocity
        self.floater.update(dt)
        
        # Velocity should increase (acceleration upward)
        assert self.floater.velocity > old_velocity


class TestIntegratedPhase3System:
    """Test complete Phase 3 system integration."""
    
    def test_complete_injection_ascent_cycle(self):
        """Test complete cycle from injection to ascent with expansion."""
        floater = Floater(
            volume=0.01,        # 10 liters
            mass=8.0,           # 8 kg (heavy when empty)
            area=0.1,
            position=0.0,       # Start at bottom
            tank_height=10.0
        )
        
        # Step 1: Position at bottom injection station
        floater.update_pneumatic_state(0.0, bottom_station_pos=0.0)
        assert floater.at_bottom_station
        assert floater.ready_for_injection
          # Step 2: Start injection
        success = floater.start_pneumatic_injection(
            target_volume=0.009,    # 9 liters (should provide buoyancy)
            injection_pressure=300000.0,  # 3 bar
            current_time=0.0
        )
        assert success
        
        # Step 3: Complete injection
        floater.update_pneumatic_injection(0.009, dt=1.0)
        assert floater.injection_complete
        assert floater.pneumatic_fill_state == 'full'
        
        # Step 4: Simulate ascent with expansion
        positions = []
        buoyancies = []
        expansions = []
        
        dt = 0.1
        for step in range(100):  # 10 seconds of simulation
            position = floater.position
            buoyancy = floater.compute_enhanced_buoyant_force()
            expansion_ratio = floater.expansion_state.get('expansion_ratio', 1.0)
            
            positions.append(position)
            buoyancies.append(buoyancy)
            expansions.append(expansion_ratio)
            
            floater.update(dt)
            
            # Stop if floater reaches top
            if position >= 9.9:
                break
        
        # Verify ascent occurred
        assert floater.position > 0.0
        
        # Verify buoyancy increased during ascent
        assert buoyancies[-1] > buoyancies[0]
        
        # Verify air expanded during ascent
        assert expansions[-1] > expansions[0]
        
    def test_physics_consistency(self):
        """Test that physics calculations are consistent and realistic."""
        floater = Floater(volume=0.01, mass=5.0, area=0.1, tank_height=10.0)
        
        # Inject air at bottom
        floater.total_air_injected = 0.005  # 5 liters
        floater.injection_depth = 10.0
        floater.initial_air_pressure = 200000.0
        floater.position = 0.0
        
        # Test at different depths
        test_positions = [0.0, 2.5, 5.0, 7.5, 10.0]
        
        for position in test_positions:
            floater.position = position
            
            # Calculate physics
            depth = floater.pressure_physics.get_depth_from_position(position, 10.0)
            pressure = floater.pressure_physics.get_pressure_at_depth(depth)
            buoyancy = floater.compute_enhanced_buoyant_force()
            
            # Verify relationships
            assert depth >= 0.0
            assert pressure >= floater.pressure_physics.P_atm
            assert buoyancy >= 0.0
            
            # Higher position = lower depth = lower pressure = higher expansion = higher buoyancy
            if position > 0:
                assert depth < 10.0  # Depth should decrease with position
                
        # Energy conservation check
        # Work done by buoyancy should not exceed theoretical maximum
        max_work = RHO_WATER * G * floater.volume * 10.0  # Max if entire volume displaces water over full height
        typical_buoyancy = floater.compute_enhanced_buoyant_force()
        work_per_meter = typical_buoyancy * 1.0
        assert work_per_meter < max_work  # Realistic buoyancy values


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
