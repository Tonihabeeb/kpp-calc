"""
Unit tests for Phase 5: Thermodynamic Modeling and Thermal Boost

Tests cover:
- Thermodynamic properties and calculations
- Compression thermodynamics
- Expansion thermodynamics with heat transfer
- Thermal buoyancy boost calculations
- Heat exchange modeling
- Complete thermodynamic cycle analysis
"""

import pytest
import math
import numpy as np
from simulation.pneumatics.thermodynamics import (
    ThermodynamicProperties, CompressionThermodynamics, 
    ExpansionThermodynamics, ThermalBuoyancyCalculator,
    AdvancedThermodynamics
)
from simulation.pneumatics.heat_exchange import (
    HeatTransferCoefficients, WaterThermalReservoir,
    AirWaterHeatExchange, CompressionHeatRecovery,
    IntegratedHeatExchange
)
from config.config import RHO_WATER, G


class TestThermodynamicProperties:
    """Test thermodynamic properties and basic calculations."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.props = ThermodynamicProperties()
    
    def test_initialization(self):
        """Test thermodynamic properties initialization."""
        assert self.props.R_specific_air == 287.0
        assert self.props.gamma_air == 1.4
        assert self.props.cp_air == 1005.0
        assert self.props.cv_air == 718.0
        assert self.props.T_standard == 293.15
        assert self.props.P_standard == 101325.0
        assert self.props.rho_air_standard > 1.0  # Should be around 1.2 kg/m³
    
    def test_air_density_calculation(self):
        """Test air density calculation using ideal gas law."""
        # Standard conditions
        density_std = self.props.air_density(self.props.P_standard, self.props.T_standard)
        assert abs(density_std - self.props.rho_air_standard) < 0.01
        
        # High pressure conditions
        density_high = self.props.air_density(200000.0, 293.15)
        assert density_high > density_std  # Higher pressure = higher density
        
        # High temperature conditions
        density_hot = self.props.air_density(101325.0, 350.0)
        assert density_hot < density_std  # Higher temperature = lower density
    
    def test_air_mass_volume_conversions(self):
        """Test conversions between air mass and volume."""
        volume = 0.01  # 10 liters
        pressure = 200000.0  # 2 bar
        temperature = 293.15  # 20°C
        
        # Volume to mass and back
        mass = self.props.air_mass_from_volume(volume, pressure, temperature)
        volume_check = self.props.air_volume_from_mass(mass, pressure, temperature)
        
        assert mass > 0
        assert abs(volume_check - volume) < 1e-6  # Should match within precision
        
        # Higher pressure should give more mass for same volume
        mass_high = self.props.air_mass_from_volume(volume, 300000.0, temperature)
        assert mass_high > mass


class TestCompressionThermodynamics:
    """Test compression thermodynamics calculations."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.compression = CompressionThermodynamics()
    
    def test_initialization(self):
        """Test compression thermodynamics initialization."""
        assert self.compression.compression_efficiency > 0
        assert self.compression.compression_efficiency <= 1.0
        assert self.compression.ambient_temperature == 293.15
        assert hasattr(self.compression, 'props')
    
    def test_adiabatic_compression_temperature(self):
        """Test adiabatic compression temperature calculation."""
        T_initial = 293.15  # 20°C
        P_initial = 101325.0  # 1 bar
        P_final = 202650.0   # 2 bar
        
        T_final = self.compression.adiabatic_compression_temperature(
            T_initial, P_initial, P_final)
        
        # Should increase temperature
        assert T_final > T_initial
        
        # Check against theoretical: T2 = T1 * (P2/P1)^((γ-1)/γ)
        expected_ratio = (P_final / P_initial) ** ((1.4 - 1) / 1.4)
        expected_T_final = T_initial * expected_ratio
        assert abs(T_final - expected_T_final) < 0.1
    
    def test_isothermal_compression_work(self):
        """Test isothermal compression work calculation."""
        volume = 0.01  # 10 liters
        P_initial = 101325.0
        P_final = 202650.0
        
        work = self.compression.isothermal_compression_work(
            volume, P_initial, P_final)
        
        # Should be positive work input
        assert work > 0
        
        # Check against theoretical: W = P1*V1 * ln(P2/P1)
        expected_work = P_initial * volume * math.log(P_final / P_initial)
        assert abs(work - expected_work) < 1.0
    
    def test_adiabatic_compression_work(self):
        """Test adiabatic compression work calculation."""
        volume = 0.01
        P_initial = 101325.0
        P_final = 202650.0
        T_initial = 293.15
        
        work = self.compression.adiabatic_compression_work(
            volume, P_initial, P_final, T_initial)
        
        # Should be positive work input
        assert work > 0
          # For compression, adiabatic work should be lower than isothermal 
        # because temperature rises during adiabatic compression
        isothermal_work = self.compression.isothermal_compression_work(
            volume, P_initial, P_final)
        assert work < isothermal_work
    
    def test_compression_heat_generation(self):
        """Test compression heat generation calculation."""
        compression_work = 1000.0  # 1 kJ theoretical work
        efficiency = 0.8
        
        heat = self.compression.compression_heat_generation(compression_work, efficiency)
        
        # Heat should be positive
        assert heat > 0
        
        # Heat = input energy - useful work = work/efficiency - work
        expected_heat = compression_work / efficiency - compression_work
        assert abs(heat - expected_heat) < 1.0
    
    def test_intercooling_temperature_drop(self):
        """Test intercooling temperature calculation."""
        T_hot = 350.0  # 77°C hot air
        heat_removed = 5000.0  # 5 kJ removed
        air_mass = 0.012  # 12 grams of air
        
        T_final = self.compression.intercooling_temperature_drop(
            T_hot, heat_removed, air_mass)
        
        # Temperature should decrease
        assert T_final < T_hot
        
        # Should not go below ambient
        assert T_final >= self.compression.ambient_temperature
        
        # Check calculation: ΔT = Q / (m * cp)
        expected_drop = heat_removed / (air_mass * self.compression.props.cp_air)
        expected_T_final = max(self.compression.ambient_temperature, T_hot - expected_drop)
        assert abs(T_final - expected_T_final) < 0.1


class TestExpansionThermodynamics:
    """Test expansion thermodynamics calculations."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.expansion = ExpansionThermodynamics(water_temperature=293.15)
    
    def test_initialization(self):
        """Test expansion thermodynamics initialization."""
        assert self.expansion.water_temperature == 293.15
        assert hasattr(self.expansion, 'props')
        assert 'adiabatic' in self.expansion.expansion_modes
        assert 'isothermal' in self.expansion.expansion_modes
        assert 'mixed' in self.expansion.expansion_modes
    
    def test_adiabatic_expansion(self):
        """Test adiabatic expansion calculation."""
        volume_initial = 0.005  # 5 liters
        P_initial = 200000.0    # 2 bar
        P_final = 101325.0      # 1 bar
        T_initial = 293.15      # 20°C
        
        volume_final, T_final = self.expansion._adiabatic_expansion(
            volume_initial, P_initial, P_final, T_initial)
        
        # Volume should increase
        assert volume_final > volume_initial
        
        # Temperature should decrease
        assert T_final < T_initial
        
        # Check volume expansion: V2 = V1 * (P1/P2) * (T2/T1)
        expected_T_ratio = (P_final / P_initial) ** ((1.4 - 1) / 1.4)
        expected_T_final = T_initial * expected_T_ratio
        assert abs(T_final - expected_T_final) < 0.1
    
    def test_isothermal_expansion(self):
        """Test isothermal expansion calculation."""
        volume_initial = 0.005
        P_initial = 200000.0
        P_final = 101325.0
        T_initial = 293.15
        
        volume_final, T_final = self.expansion._isothermal_expansion(
            volume_initial, P_initial, P_final, T_initial)
        
        # Volume should increase
        assert volume_final > volume_initial
        
        # Temperature should remain constant
        assert abs(T_final - T_initial) < 0.01
        
        # Check Boyle's law: V2 = V1 * (P1/P2)
        expected_volume_final = volume_initial * (P_initial / P_final)
        assert abs(volume_final - expected_volume_final) < 1e-6
    
    def test_mixed_expansion(self):
        """Test mixed expansion calculation."""
        volume_initial = 0.005
        P_initial = 200000.0
        P_final = 101325.0
        T_initial = 293.15
        heat_transfer_rate = 0.5  # 50% heat transfer
        
        volume_final, T_final = self.expansion._mixed_expansion(
            volume_initial, P_initial, P_final, T_initial, heat_transfer_rate)
        
        # Get adiabatic and isothermal results for comparison
        V_adiabatic, T_adiabatic = self.expansion._adiabatic_expansion(
            volume_initial, P_initial, P_final, T_initial)
        V_isothermal, T_isothermal = self.expansion._isothermal_expansion(
            volume_initial, P_initial, P_final, T_initial)
        
        # Mixed results should be between adiabatic and isothermal
        assert V_adiabatic <= volume_final <= V_isothermal
        assert T_adiabatic <= T_final <= T_isothermal
    
    def test_expansion_with_heat_transfer(self):
        """Test complete expansion with heat transfer."""
        volume_initial = 0.006  # 6 liters
        P_initial = 250000.0    # 2.5 bar
        P_final = 101325.0      # 1 bar
        T_initial = 288.15      # 15°C (cooler than water)
        expansion_time = 10.0   # 10 seconds
        
        results = self.expansion.expansion_with_heat_transfer(
            volume_initial, P_initial, P_final, T_initial,
            'mixed', expansion_time)
        
        # Check result structure
        assert 'initial_volume' in results
        assert 'final_volume' in results
        assert 'heat_transfer' in results
        assert 'thermal_energy_boost' in results
        assert 'expansion_ratio' in results
        
        # Volume should increase
        assert results['final_volume'] > results['initial_volume']
        
        # Should have heat transfer from warmer water
        assert results['heat_transfer'] > 0
        
        # Final temperature should increase due to heat transfer
        assert results['final_temperature'] > T_initial


class TestThermalBuoyancyCalculator:
    """Test thermal buoyancy calculations."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.calculator = ThermalBuoyancyCalculator()
    
    def test_initialization(self):
        """Test thermal buoyancy calculator initialization."""
        assert hasattr(self.calculator, 'props')
    
    def test_thermal_buoyancy_boost(self):
        """Test thermal buoyancy boost calculation."""
        base_buoyant_force = 98.1  # ~10 kg buoyancy
        
        # Mock thermal expansion results
        thermal_results = {
            'initial_volume': 0.005,
            'final_volume': 0.006,  # 1 liter increase
            'thermal_energy_boost': 2000.0  # 2 kJ
        }
        
        results = self.calculator.thermal_buoyancy_boost(
            base_buoyant_force, thermal_results)
        
        # Check result structure
        assert 'base_buoyant_force' in results
        assert 'thermal_buoyant_force' in results
        assert 'total_buoyant_force' in results
        assert 'thermal_boost_percentage' in results
        
        # Thermal boost should be positive
        assert results['thermal_buoyant_force'] > 0
        
        # Total should be sum of base and thermal
        expected_total = base_buoyant_force + results['thermal_buoyant_force']
        assert abs(results['total_buoyant_force'] - expected_total) < 0.1
        
        # Check thermal force calculation
        volume_increase = thermal_results['final_volume'] - thermal_results['initial_volume']
        expected_thermal_force = RHO_WATER * G * volume_increase
        assert abs(results['thermal_buoyant_force'] - expected_thermal_force) < 0.1
    
    def test_thermal_efficiency_factor(self):
        """Test thermal efficiency calculation."""
        thermal_energy_input = 5000.0  # 5 kJ input
        mechanical_work_output = 1000.0  # 1 kJ output
        
        efficiency = self.calculator.thermal_efficiency_factor(
            thermal_energy_input, mechanical_work_output)
        
        # Efficiency should be ratio of output to input
        expected_efficiency = mechanical_work_output / thermal_energy_input
        assert abs(efficiency - expected_efficiency) < 1e-6
        assert 0 <= efficiency <= 1.0


class TestAdvancedThermodynamics:
    """Test complete advanced thermodynamics system."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.thermodynamics = AdvancedThermodynamics(
            water_temperature=295.15,  # 22°C
            expansion_mode='mixed'
        )
    
    def test_initialization(self):
        """Test advanced thermodynamics initialization."""
        assert self.thermodynamics.water_temperature == 295.15
        assert self.thermodynamics.expansion_mode == 'mixed'
        assert hasattr(self.thermodynamics, 'props')
        assert hasattr(self.thermodynamics, 'compression')
        assert hasattr(self.thermodynamics, 'expansion')
        assert hasattr(self.thermodynamics, 'thermal_buoyancy')
    
    def test_complete_thermodynamic_cycle(self):
        """Test complete thermodynamic cycle analysis."""
        initial_air_volume = 0.006   # 6 liters at surface
        injection_pressure = 250000.0  # 2.5 bar injection
        surface_pressure = 101325.0    # 1 bar surface
        injection_temperature = 290.15  # 17°C injection temp
        ascent_time = 15.0            # 15 second ascent
        base_buoyant_force = 78.5     # ~8 kg buoyancy
        
        results = self.thermodynamics.complete_thermodynamic_cycle(
            initial_air_volume, injection_pressure, surface_pressure,
            injection_temperature, ascent_time, base_buoyant_force)
        
        # Check result structure
        assert 'compression' in results
        assert 'expansion' in results
        assert 'thermal_buoyancy' in results
        assert 'energy_balance' in results
        assert 'performance_metrics' in results
          # Check compression results
        compression = results['compression']
        assert compression['isothermal_work'] > 0
        assert compression['adiabatic_work'] > 0
        # For compression, adiabatic work should be lower than isothermal
        assert compression['adiabatic_work'] < compression['isothermal_work']
        assert compression['heat_generated'] > 0
        
        # Check expansion results
        expansion = results['expansion']
        assert expansion['final_volume'] > expansion['initial_volume']
        assert expansion['expansion_ratio'] > 1.0
        
        # Check thermal buoyancy
        thermal = results['thermal_buoyancy']
        assert thermal['thermal_buoyant_force'] >= 0
        assert thermal['total_buoyant_force'] >= base_buoyant_force
        
        # Check energy balance
        energy = results['energy_balance']
        assert energy['thermal_energy_input'] >= 0
        assert energy['thermal_work_output'] >= 0
        assert 0 <= energy['thermal_efficiency'] <= 1.0
    
    def test_water_temperature_update(self):
        """Test water temperature update functionality."""
        new_temperature = 298.15  # 25°C
        
        self.thermodynamics.update_water_temperature(new_temperature)
        
        assert self.thermodynamics.water_temperature == new_temperature
        assert self.thermodynamics.expansion.water_temperature == new_temperature
    
    def test_expansion_mode_update(self):
        """Test expansion mode update functionality."""
        new_mode = 'adiabatic'
        
        self.thermodynamics.update_expansion_mode(new_mode)
        
        assert self.thermodynamics.expansion_mode == new_mode


class TestHeatTransferCoefficients:
    """Test heat transfer coefficient calculations."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.coeffs = HeatTransferCoefficients()
    
    def test_initialization(self):
        """Test heat transfer coefficients initialization."""
        assert self.coeffs.natural_convection_air > 0
        assert self.coeffs.natural_convection_water > 0
        assert self.coeffs.forced_convection_water > self.coeffs.natural_convection_water
        assert self.coeffs.thermal_conductivity_water > self.coeffs.thermal_conductivity_air
    
    def test_overall_heat_transfer_coefficient(self):
        """Test overall heat transfer coefficient calculation."""
        h_inner = 50.0  # W/(m²·K)
        h_outer = 1000.0  # W/(m²·K)
        k_wall = 200.0  # W/(m·K)
        t_wall = 0.003  # 3mm
        
        U = self.coeffs.overall_heat_transfer_coefficient(
            h_inner, h_outer, k_wall, t_wall)
        
        # Overall coefficient should be positive but less than minimum of inner/outer
        assert U > 0
        assert U < min(h_inner, h_outer)
        
        # Check against expected calculation
        R_total = 1/h_inner + t_wall/k_wall + 1/h_outer
        expected_U = 1/R_total
        assert abs(U - expected_U) < 0.1
    
    def test_reynolds_number(self):
        """Test Reynolds number calculation."""
        velocity = 2.0  # m/s
        length = 0.3    # m
        kinematic_viscosity = 1e-6  # m²/s
        
        Re = self.coeffs.reynolds_number(velocity, length, kinematic_viscosity)
        
        expected_Re = velocity * length / kinematic_viscosity
        assert abs(Re - expected_Re) < 1e-6
        assert Re > 0
    
    def test_nusselt_number_cylinder(self):
        """Test Nusselt number calculation for cylinder."""
        reynolds = 10000.0
        prandtl = 7.0
        
        Nu = self.coeffs.nusselt_number_cylinder(reynolds, prandtl)
        
        # Nusselt number should be reasonable for these conditions
        assert Nu >= 2.0  # Minimum for cylinder
        assert Nu < 1000.0  # Reasonable upper bound
        
        # Higher Re should give higher Nu
        Nu_high = self.coeffs.nusselt_number_cylinder(50000.0, prandtl)
        assert Nu_high > Nu


class TestWaterThermalReservoir:
    """Test water thermal reservoir modeling."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.reservoir = WaterThermalReservoir(
            tank_height=10.0,
            surface_temperature=295.15,  # 22°C
            bottom_temperature=288.15    # 15°C
        )
    
    def test_initialization(self):
        """Test reservoir initialization."""
        assert self.reservoir.tank_height == 10.0
        assert self.reservoir.surface_temperature == 295.15
        assert self.reservoir.bottom_temperature == 288.15
        assert self.reservoir.temperature_gradient > 0  # Warmer at surface
    
    def test_water_temperature_at_depth(self):
        """Test water temperature calculation at depth."""
        # Surface temperature
        temp_surface = self.reservoir.water_temperature_at_depth(0.0)
        assert abs(temp_surface - self.reservoir.surface_temperature) < 0.1
        
        # Bottom temperature
        temp_bottom = self.reservoir.water_temperature_at_depth(10.0)
        assert abs(temp_bottom - self.reservoir.bottom_temperature) < 0.1
        
        # Mid-depth should be between surface and bottom
        temp_mid = self.reservoir.water_temperature_at_depth(5.0)
        assert self.reservoir.bottom_temperature < temp_mid < self.reservoir.surface_temperature
    
    def test_water_temperature_at_position(self):
        """Test water temperature at floater position."""
        # Bottom position (position = 0)
        temp_bottom_pos = self.reservoir.water_temperature_at_position(0.0)
        assert abs(temp_bottom_pos - self.reservoir.bottom_temperature) < 0.1
        
        # Top position (position = tank_height)
        temp_top_pos = self.reservoir.water_temperature_at_position(10.0)
        assert abs(temp_top_pos - self.reservoir.surface_temperature) < 0.1
    
    def test_thermal_stratification_effect(self):
        """Test thermal stratification effects during ascent."""
        position_initial = 2.0  # Start at 2m
        position_final = 8.0    # End at 8m
        
        results = self.reservoir.thermal_stratification_effect(
            position_initial, position_final)
        
        # Check result structure
        assert 'initial_water_temperature' in results
        assert 'final_water_temperature' in results
        assert 'temperature_change' in results
        
        # Temperature should increase as floater ascends (warmer at surface)
        assert results['final_water_temperature'] > results['initial_water_temperature']
        assert results['temperature_change'] > 0


class TestIntegratedHeatExchange:
    """Test integrated heat exchange system."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.heat_exchange = IntegratedHeatExchange(
            tank_height=10.0,
            surface_temperature=295.15,
            bottom_temperature=288.15
        )
    
    def test_initialization(self):
        """Test integrated heat exchange initialization."""
        assert hasattr(self.heat_exchange, 'water_reservoir')
        assert hasattr(self.heat_exchange, 'air_water_exchange')
        assert hasattr(self.heat_exchange, 'heat_recovery')
        assert self.heat_exchange.tank_height == 10.0
    
    def test_complete_heat_exchange_analysis(self):
        """Test complete heat exchange analysis."""
        floater_position = 3.0      # Start at 3m
        air_volume = 0.006          # 6 liters
        air_pressure = 200000.0     # 2 bar
        air_temperature = 285.15    # 12°C (cooler than water)
        ascent_velocity = 0.5       # 0.5 m/s
        ascent_time = 10.0          # 10 seconds
        compression_work = 2000.0   # 2 kJ compression work
        
        results = self.heat_exchange.complete_heat_exchange_analysis(
            floater_position, air_volume, air_pressure, air_temperature,
            ascent_velocity, ascent_time, compression_work)
        
        # Check result structure
        assert 'thermal_stratification' in results
        assert 'air_water_heat_exchange' in results
        assert 'compression_heat_recovery' in results
        assert 'system_parameters' in results
        assert 'thermal_performance' in results
        
        # Check thermal stratification
        stratification = results['thermal_stratification']
        assert 'temperature_change' in stratification
        assert stratification['temperature_change'] > 0  # Warmer water above
        
        # Check air-water heat exchange
        heat_exchange = results['air_water_heat_exchange']
        assert heat_exchange['temperature_change'] > 0  # Air should warm up
        assert heat_exchange['total_heat_transferred'] > 0
        
        # Check compression heat recovery
        heat_recovery = results['compression_heat_recovery']
        assert heat_recovery is not None
        assert heat_recovery['recoverable_heat'] > 0
        
        # Check system parameters
        params = results['system_parameters']
        assert params['air_volume'] == air_volume
        assert params['ascent_velocity'] == ascent_velocity
        
        # Check thermal performance
        performance = results['thermal_performance']
        assert performance['air_temperature_change'] > 0
        assert performance['total_heat_transferred'] > 0


class TestIntegratedPhase5System:
    """Integration tests for complete Phase 5 system."""
    
    def setup_method(self):
        """Set up integrated test system."""
        self.thermodynamics = AdvancedThermodynamics(
            water_temperature=293.15, expansion_mode='mixed')
        self.heat_exchange = IntegratedHeatExchange(
            tank_height=10.0, surface_temperature=295.15, bottom_temperature=288.15)
    
    def test_combined_thermodynamic_and_heat_exchange(self):
        """Test combined thermodynamic cycle with heat exchange."""
        # Floater parameters
        initial_air_volume = 0.006
        injection_pressure = 250000.0
        surface_pressure = 101325.0
        injection_temperature = 290.15
        base_buoyant_force = 78.5
        
        # Heat exchange parameters
        floater_position = 2.0
        ascent_velocity = 0.4
        ascent_time = 20.0
        
        # Run thermodynamic cycle
        thermo_results = self.thermodynamics.complete_thermodynamic_cycle(
            initial_air_volume, injection_pressure, surface_pressure,
            injection_temperature, ascent_time, base_buoyant_force)
        
        # Run heat exchange analysis
        heat_results = self.heat_exchange.complete_heat_exchange_analysis(
            floater_position, initial_air_volume, injection_pressure,
            injection_temperature, ascent_velocity, ascent_time)
        
        # Both analyses should show positive thermal effects
        assert thermo_results['thermal_buoyancy']['thermal_buoyant_force'] > 0
        assert heat_results['air_water_heat_exchange']['total_heat_transferred'] > 0
        
        # Thermal boost should improve buoyancy
        thermal_boost_pct = thermo_results['thermal_buoyancy']['thermal_boost_percentage']
        assert thermal_boost_pct > 0
        
        # Heat exchange should warm the air
        air_temp_change = heat_results['air_water_heat_exchange']['temperature_change']
        assert air_temp_change > 0
    
    def test_energy_conservation(self):
        """Test energy conservation in thermal processes."""
        # Simple energy balance check
        compression_work = 3000.0  # 3 kJ input
        
        # Heat generation from compression
        heat_generated = self.thermodynamics.compression.compression_heat_generation(compression_work)
        
        # Heat should be less than total input energy
        total_input = compression_work / 0.85  # Assuming 85% efficiency
        assert heat_generated < total_input
        assert heat_generated > 0
        
        # Heat plus useful work should equal input (within efficiency)
        useful_work = compression_work
        assert abs((heat_generated + useful_work) - total_input) < 1.0
    
    def test_thermal_boost_physics_validation(self):
        """Test that thermal boost follows physics principles."""
        # Create thermal expansion scenario
        volume_initial = 0.005
        volume_final = 0.006
        thermal_expansion_results = {
            'initial_volume': volume_initial,
            'final_volume': volume_final,
            'thermal_energy_boost': 1500.0
        }
        
        base_buoyant_force = 49.05  # 5 kg buoyancy
        
        # Calculate thermal boost
        results = self.thermodynamics.thermal_buoyancy.thermal_buoyancy_boost(
            base_buoyant_force, thermal_expansion_results)
        
        # Thermal buoyant force should match Archimedes' principle
        volume_increase = volume_final - volume_initial
        expected_thermal_force = RHO_WATER * G * volume_increase
        
        assert abs(results['thermal_buoyant_force'] - expected_thermal_force) < 0.1
        
        # Boost percentage should be reasonable (not over-unity)
        assert 0 <= results['thermal_boost_percentage'] <= 50  # Max 50% boost is reasonable


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
