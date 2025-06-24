"""
Test Suite for Phase 5: Enhanced Loss Modeling
Tests comprehensive friction, thermal, and loss tracking functionality.
"""

import pytest
import numpy as np
import math
from simulation.physics.losses import DrivetrainLosses, ElectricalLosses, ComponentState, LossComponents
from simulation.physics.thermal import ThermalModel, ThermalState
from simulation.physics.integrated_loss_model import IntegratedLossModel, create_standard_kpp_enhanced_loss_model
from simulation.engine import SimulationEngine
import queue

class TestDrivetrainLosses:
    """Test comprehensive drivetrain loss modeling"""
    
    def test_drivetrain_losses_initialization(self):
        """Test drivetrain loss model initialization"""
        losses = DrivetrainLosses()
        assert losses.bearing_friction_coeff > 0
        assert losses.gear_mesh_efficiency < 1.0
        assert losses.seal_friction_coeff > 0
        assert losses.windage_coefficient > 0
        assert losses.clutch_friction_coeff > 0
      def test_bearing_friction_calculation(self):
        """Test bearing friction with temperature dependence"""
        losses = DrivetrainLosses()
        
        # Test at room temperature
        component_state = ComponentState(torque=1000.0, speed=100.0, temperature=20.0)
        friction_loss = losses.calculate_bearing_friction_losses(component_state)
        assert friction_loss > 0
        
        # Test temperature dependence - higher temp should increase friction
        hot_state = ComponentState(torque=1000.0, speed=100.0, temperature=80.0)
        hot_friction = losses.calculate_bearing_friction_losses(hot_state)
        assert hot_friction > friction_loss
    
    def test_gear_mesh_losses(self):
        """Test gear mesh losses with load dependence"""
        losses = DrivetrainLosses()
        
        # Test low load
        low_load_state = ComponentState(torque=500.0, speed=100.0, load_factor=0.2)
        low_loss = losses.calculate_gear_mesh_losses(low_load_state)
        
        # Test high load
        high_load_state = ComponentState(torque=2000.0, speed=100.0, load_factor=0.8)
        high_loss = losses.calculate_gear_mesh_losses(high_load_state)
        
        assert high_loss > low_loss
        assert low_loss > 0
    
    def test_windage_losses(self):
        """Test windage losses with speed squared dependence"""
        losses = DrivetrainLosses()
        
        # Test low speed
        low_speed_state = ComponentState(speed=50.0, temperature=20.0)
        low_windage = losses.calculate_windage_losses(low_speed_state)
        
        # Test high speed (4x speed should give ~16x windage)
        high_speed_state = ComponentState(speed=200.0, temperature=20.0)
        high_windage = losses.calculate_windage_losses(high_speed_state)
        
        assert high_windage > low_windage
        # Should be approximately 16x for 4x speed increase
        assert high_windage / low_windage > 10  # Allow some tolerance
    
    def test_comprehensive_loss_calculation(self):
        """Test comprehensive loss calculation"""
        losses = DrivetrainLosses()
        
        component_state = ComponentState(
            torque=1500.0,
            speed=150.0,
            temperature=45.0,
            load_factor=0.6
        )
        
        total_losses = losses.calculate_comprehensive_losses(component_state)
        
        assert isinstance(total_losses, LossComponents)
        assert total_losses.bearing_friction > 0
        assert total_losses.gear_mesh_losses > 0
        assert total_losses.windage_losses > 0
        assert total_losses.total_losses > 0
        assert total_losses.total_losses == (
            total_losses.bearing_friction +
            total_losses.gear_mesh_losses +
            total_losses.seal_friction +
            total_losses.windage_losses +
            total_losses.clutch_losses
        )

class TestElectricalLosses:
    """Test electrical loss modeling"""
    
    def test_electrical_losses_initialization(self):
        """Test electrical loss model initialization"""
        losses = ElectricalLosses()
        assert hasattr(losses, 'copper_resistivity')
        assert hasattr(losses, 'iron_loss_constant')
        assert hasattr(losses, 'switching_loss_constant')
    
    def test_copper_losses(self):
        """Test I²R copper losses"""
        losses = ElectricalLosses()
        
        electrical_state = {
            'current': 100.0,
            'voltage': 480.0,
            'temperature': 40.0
        }
        
        copper_loss = losses.calculate_copper_losses(electrical_state)
        assert copper_loss > 0
        
        # Test current squared dependence
        high_current_state = electrical_state.copy()
        high_current_state['current'] = 200.0
        high_copper_loss = losses.calculate_copper_losses(high_current_state)
        
        # Should be approximately 4x for 2x current
        assert high_copper_loss / copper_loss > 3.5
        assert high_copper_loss / copper_loss < 4.5
    
    def test_iron_losses(self):
        """Test iron losses (hysteresis and eddy current)"""
        losses = ElectricalLosses()
        
        electrical_state = {
            'frequency': 60.0,
            'flux_density': 1.0,
            'temperature': 40.0
        }
        
        iron_loss = losses.calculate_iron_losses(electrical_state)
        assert iron_loss > 0
        
        # Test frequency dependence
        high_freq_state = electrical_state.copy()
        high_freq_state['frequency'] = 120.0
        high_iron_loss = losses.calculate_iron_losses(high_freq_state)
        
        assert high_iron_loss > iron_loss
    
    def test_switching_losses(self):
        """Test switching losses in power electronics"""
        losses = ElectricalLosses()
        
        electrical_state = {
            'switching_frequency': 5000.0,
            'current': 100.0,
            'voltage': 480.0,
            'temperature': 50.0
        }
        
        switching_loss = losses.calculate_switching_losses(electrical_state)
        assert switching_loss > 0
        
        # Test switching frequency dependence
        high_switch_state = electrical_state.copy()
        high_switch_state['switching_frequency'] = 10000.0
        high_switching_loss = losses.calculate_switching_losses(high_switch_state)
        
        assert high_switching_loss > switching_loss

class TestThermalModel:
    """Test thermal modeling functionality"""
    
    def test_thermal_model_initialization(self):
        """Test thermal model initialization"""
        thermal = ThermalModel(ambient_temperature=25.0)
        assert thermal.ambient_temperature == 25.0
        assert len(thermal.component_thermal_states) > 0
    
    def test_heat_generation_calculation(self):
        """Test heat generation from power losses"""
        thermal = ThermalModel()
        
        component_losses = {
            'bearing_friction': 500.0,
            'gear_mesh_losses': 1000.0,
            'electrical_losses': 2000.0
        }
        
        heat_generated = thermal.calculate_heat_generation(component_losses)
        assert heat_generated > 0
        assert heat_generated == sum(component_losses.values())
    
    def test_heat_transfer_calculation(self):
        """Test heat transfer via conduction, convection, and radiation"""
        thermal = ThermalModel(ambient_temperature=20.0)
        
        thermal_state = ThermalState(
            temperature=60.0,
            surface_area=2.0,
            thermal_conductivity=50.0
        )
        
        heat_transfer = thermal.calculate_heat_transfer('test_component', thermal_state)
        assert heat_transfer > 0  # Should transfer heat to cooler ambient
    
    def test_temperature_update(self):
        """Test temperature update based on heat balance"""
        thermal = ThermalModel(ambient_temperature=20.0)
        
        component_name = 'gearbox'
        initial_temp = thermal.component_thermal_states[component_name].temperature
        
        # Add significant heat generation
        heat_generation = 5000.0  # 5kW
        dt = 1.0  # 1 second
        
        thermal.update_component_temperature(component_name, heat_generation, dt)
        
        final_temp = thermal.component_thermal_states[component_name].temperature
        assert final_temp > initial_temp  # Temperature should increase
    
    def test_temperature_effects_on_efficiency(self):
        """Test temperature effects on component efficiency"""
        thermal = ThermalModel()
        
        # Test efficiency at different temperatures
        efficiency_20c = thermal.get_temperature_efficiency_factor('generator', 20.0)
        efficiency_80c = thermal.get_temperature_efficiency_factor('generator', 80.0)
        efficiency_120c = thermal.get_temperature_efficiency_factor('generator', 120.0)
        
        # Efficiency should decrease with increasing temperature
        assert efficiency_80c < efficiency_20c
        assert efficiency_120c < efficiency_80c
        
        # All should be between 0 and 1
        assert 0 < efficiency_120c < efficiency_80c < efficiency_20c <= 1.0

class TestIntegratedLossModel:
    """Test integrated loss model combining all effects"""
    
    def test_integrated_model_initialization(self):
        """Test integrated loss model initialization"""
        model = create_standard_kpp_enhanced_loss_model(25.0)
        assert isinstance(model, IntegratedLossModel)
        assert model.thermal_model.ambient_temperature == 25.0
        assert hasattr(model, 'drivetrain_losses')
        assert hasattr(model, 'electrical_losses')
    
    def test_system_loss_calculation(self):
        """Test comprehensive system loss calculation"""
        model = create_standard_kpp_enhanced_loss_model(20.0)
        
        # Create realistic system state
        system_state = {
            'drivetrain': {
                'sprocket': {'torque': 1000.0, 'speed': 10.0, 'temperature': 30.0, 'load_factor': 0.4},
                'gearbox': {'torque': 1500.0, 'speed': 100.0, 'temperature': 45.0, 'load_factor': 0.6},
                'clutch': {'torque': 1400.0, 'speed': 380.0, 'temperature': 40.0, 'load_factor': 0.8},
                'flywheel': {'torque': 1350.0, 'speed': 375.0, 'temperature': 35.0, 'load_factor': 0.7}
            },
            'generator': {
                'torque': 1300.0,
                'speed': 375.0,
                'load_factor': 0.75,
                'efficiency': 0.94
            },
            'electrical': {
                'current': 800.0,
                'voltage': 480.0,
                'frequency': 60.0,
                'temperature': 40.0,
                'switching_frequency': 5000.0,
                'flux_density': 1.0
            }
        }
        
        enhanced_state = model.update_system_losses(system_state, dt=1.0)
        
        assert hasattr(enhanced_state, 'system_losses')
        assert hasattr(enhanced_state, 'performance_metrics')
        assert enhanced_state.system_losses.total_system_losses > 0
        assert 0 < enhanced_state.system_losses.system_efficiency < 1.0
    
    def test_thermal_mechanical_coupling(self):
        """Test thermal-mechanical coupling effects"""
        model = create_standard_kpp_enhanced_loss_model(20.0)
        
        # Run system for several time steps to build up heat
        system_state = {
            'drivetrain': {
                'gearbox': {'torque': 2000.0, 'speed': 200.0, 'temperature': 20.0, 'load_factor': 0.8}
            },
            'generator': {
                'torque': 1800.0,
                'speed': 375.0,
                'load_factor': 0.9,
                'efficiency': 0.94
            },
            'electrical': {
                'current': 1000.0,
                'voltage': 480.0,
                'frequency': 60.0,
                'temperature': 20.0,
                'switching_frequency': 5000.0,
                'flux_density': 1.2
            }
        }
        
        # First update
        state1 = model.update_system_losses(system_state, dt=10.0)
        initial_efficiency = state1.system_losses.system_efficiency
        
        # Second update with accumulated heat
        state2 = model.update_system_losses(system_state, dt=10.0)
        final_efficiency = state2.system_losses.system_efficiency
        
        # Efficiency should decrease due to thermal effects
        assert final_efficiency <= initial_efficiency
    
    def test_performance_metrics_tracking(self):
        """Test performance metrics calculation and tracking"""
        model = create_standard_kpp_enhanced_loss_model(20.0)
        
        system_state = {
            'drivetrain': {
                'gearbox': {'torque': 1500.0, 'speed': 150.0, 'temperature': 40.0, 'load_factor': 0.6}
            },
            'generator': {
                'torque': 1400.0,
                'speed': 375.0,
                'load_factor': 0.8,
                'efficiency': 0.94
            },
            'electrical': {
                'current': 800.0,
                'voltage': 480.0,
                'frequency': 60.0,
                'temperature': 40.0,
                'switching_frequency': 5000.0,
                'flux_density': 1.0
            }
        }
        
        enhanced_state = model.update_system_losses(system_state, dt=1.0)
        metrics = enhanced_state.performance_metrics
        
        # Check required performance metrics
        assert 'total_mechanical_losses' in metrics
        assert 'total_electrical_losses' in metrics
        assert 'total_thermal_losses' in metrics
        assert 'system_efficiency' in metrics
        assert 'power_quality_factor' in metrics
        assert 'thermal_stability_factor' in metrics
        
        # Validate metric ranges
        assert 0 < metrics['system_efficiency'] < 1.0
        assert 0 <= metrics['power_quality_factor'] <= 1.0
        assert 0 <= metrics['thermal_stability_factor'] <= 1.0
    
    def test_reset_functionality(self):
        """Test reset functionality of integrated loss model"""
        model = create_standard_kpp_enhanced_loss_model(20.0)
        
        # Run some updates to change state
        system_state = {
            'drivetrain': {
                'gearbox': {'torque': 1500.0, 'speed': 150.0, 'temperature': 60.0, 'load_factor': 0.6}
            },
            'generator': {'torque': 1400.0, 'speed': 375.0, 'load_factor': 0.8, 'efficiency': 0.94},
            'electrical': {'current': 800.0, 'voltage': 480.0, 'frequency': 60.0, 'temperature': 60.0, 'switching_frequency': 5000.0, 'flux_density': 1.0}
        }
        
        # Update to change temperatures
        model.update_system_losses(system_state, dt=100.0)
        
        # Check that temperatures have changed
        gearbox_temp_before = model.thermal_model.component_thermal_states['gearbox'].temperature
        assert gearbox_temp_before > 20.0  # Should be heated up
        
        # Reset the model
        model.reset()
        
        # Check that temperatures are reset
        gearbox_temp_after = model.thermal_model.component_thermal_states['gearbox'].temperature
        assert gearbox_temp_after == 20.0  # Should be back to ambient

class TestEngineIntegration:
    """Test integration of enhanced loss model with simulation engine"""
    
    def test_engine_with_enhanced_loss_model(self):
        """Test simulation engine with enhanced loss model integration"""
        params = {
            'time_step': 0.1,
            'num_floaters': 2,
            'floater_volume': 0.3,
            'target_power': 530000.0,
            'ambient_temperature': 25.0
        }
        
        data_queue = queue.Queue()
        engine = SimulationEngine(params, data_queue)
        
        # Verify enhanced loss model is initialized
        assert hasattr(engine, 'enhanced_loss_model')
        assert engine.enhanced_loss_model.thermal_model.ambient_temperature == 25.0
    
    def test_engine_reset_with_loss_model(self):
        """Test engine reset includes enhanced loss model reset"""
        params = {
            'time_step': 0.1,
            'num_floaters': 2,
            'floater_volume': 0.3,
            'target_power': 530000.0,
            'ambient_temperature': 30.0
        }
        
        data_queue = queue.Queue()
        engine = SimulationEngine(params, data_queue)
        
        # Run a step to change state
        engine.step(0.1)
        
        # Reset and verify
        engine.reset()
        
        # Check that loss model temperatures are reset
        gearbox_temp = engine.enhanced_loss_model.thermal_model.component_thermal_states['gearbox'].temperature
        assert gearbox_temp == 30.0  # Should match ambient
    
    def test_engine_step_with_loss_tracking(self):
        """Test simulation step includes loss tracking and thermal updates"""
        params = {
            'time_step': 0.1,
            'num_floaters': 2,
            'floater_volume': 0.3,
            'target_power': 100000.0,  # Lower power for stable test
            'ambient_temperature': 20.0
        }
        
        data_queue = queue.Queue()
        engine = SimulationEngine(params, data_queue)
        
        # Take several steps
        for _ in range(5):
            engine.step(0.1)
        
        # Verify that loss model is being updated (temperatures should change)
        thermal_states = engine.enhanced_loss_model.thermal_model.component_thermal_states
        
        # At least one component should show thermal activity
        temp_changes = [abs(state.temperature - 20.0) for state in thermal_states.values()]
        assert any(change > 0.1 for change in temp_changes), "No thermal activity detected"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
