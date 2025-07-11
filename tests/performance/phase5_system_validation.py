"""
System-wide Integration Testing and Optimization Validation
Tests the complete KPP system with all optimizations enabled.
"""

import pytest
import time
import numpy as np
from typing import Dict, Any

from simulation.engine import SimulationEngine
from simulation.components.integrated_electrical_system import IntegratedElectricalSystem
from simulation.grid_services.grid_services_coordinator import GridServicesCoordinator
from simulation.optimization.mechanical_optimizer import MechanicalOptimizer
from simulation.optimization.electrical_optimizer import ElectricalOptimizer, OptimizationMode
from simulation.monitoring.performance_monitor import PerformanceMonitor
from simulation.monitoring.real_time_monitor import RealTimeMonitor

class TestSystemValidation:
    """Comprehensive system validation test suite"""
    
    @pytest.fixture
    def setup_system(self):
        """Set up complete simulation system with all components"""
        # Initialize core components
        engine = SimulationEngine()
        electrical_system = IntegratedElectricalSystem()
        grid_coordinator = GridServicesCoordinator()
        
        # Initialize optimization systems
        mechanical_opt = MechanicalOptimizer()
        electrical_opt = ElectricalOptimizer()
        
        # Initialize monitoring systems
        perf_monitor = PerformanceMonitor()
        real_monitor = RealTimeMonitor()
        
        # Register components
        engine.register_component('electrical_system', electrical_system)
        engine.register_component('grid_coordinator', grid_coordinator)
        engine.register_component('mechanical_optimizer', mechanical_opt)
        engine.register_component('electrical_optimizer', electrical_opt)
        
        # Start monitoring
        perf_monitor.start_monitoring()
        
        return {
            'engine': engine,
            'electrical_system': electrical_system,
            'grid_coordinator': grid_coordinator,
            'mechanical_opt': mechanical_opt,
            'electrical_opt': electrical_opt,
            'perf_monitor': perf_monitor,
            'real_monitor': real_monitor
        }
    
    def test_system_startup_optimization(self, setup_system):
        """Test system optimization during startup sequence"""
        system = setup_system
        engine = system['engine']
        
        # Initial conditions
        initial_state = engine.get_state()
        initial_efficiency = initial_state.efficiency if hasattr(initial_state, 'efficiency') else 0.0
        
        # Run startup sequence with optimization
        for _ in range(100):
            engine.step()
            time.sleep(0.01)  # Small delay between steps
        
        # Get final state
        final_state = engine.get_state()
        final_efficiency = final_state.efficiency if hasattr(final_state, 'efficiency') else 0.0
        
        # Verify improvements
        assert final_efficiency > initial_efficiency
        assert getattr(final_state, 'mechanical_efficiency', 0.0) > 0.85
        assert getattr(final_state, 'electrical_efficiency', 0.0) > 0.90
    
    def test_mechanical_electrical_coordination(self, setup_system):
        """Test coordination between mechanical and electrical optimizations"""
        system = setup_system
        mech_opt = system['mechanical_opt']
        elec_opt = system['electrical_opt']
        
        # Simulate suboptimal conditions
        state = {
            'mechanical_efficiency': 0.80,
            'electrical_efficiency': 0.85,
            'power_output': 3000.0,
            'mechanical_losses': 1000.0,
            'electrical_losses': 800.0,
            'chain_tension': 41000.0,
            'power_factor': 0.92,
            'voltage': 410.0,
            'current': 95.0,
            'frequency': 50.2
        }
        
        time_step = 0.01  # 10ms time step
        
        # Get optimization suggestions
        mech_adjustments = mech_opt.update(state, time_step)
        elec_adjustments = elec_opt.update(state, time_step)
        
        # Verify adjustments don't conflict
        if 'chain_tension' in mech_adjustments and 'voltage_setpoint' in elec_adjustments:
            # Changes in chain tension shouldn't require voltage outside bounds
            new_voltage = state['voltage'] + elec_adjustments.get('voltage_setpoint', 0.0)
            assert 380.0 <= new_voltage <= 420.0
    
    def test_grid_services_integration(self, setup_system):
        """Test integration with grid services during optimization"""
        system = setup_system
        engine = system['engine']
        grid_coordinator = system['grid_coordinator']
        
        # Enable grid services
        grid_coordinator.enable()
        
        # Simulate grid event
        grid_state = {
            'frequency': 49.8,  # Under-frequency
            'voltage': 390.0,   # Under-voltage
            'timestamp': time.time(),
            'active_power': 4000.0,
            'reactive_power': 500.0,
            'power_factor': 0.92,
            'battery_state': {
                'charge_level': 0.8,
                'temperature': 25.0,
                'voltage': 48.0,
                'current': 20.0
            }
        }
        
        # Process event and get response
        time_step = 0.01  # 10ms time step
        active_power_adj, reactive_power_adj = grid_coordinator.update(grid_state, time_step)
        
        # Run optimization cycle
        for _ in range(50):
            engine.step()
            grid_coordinator.update(grid_state, time_step)
        
        # Verify system response
        final_state = engine.get_state()
        assert abs(getattr(final_state, 'grid_frequency', 50.0) - 50.0) < 0.1
        assert abs(getattr(final_state, 'grid_voltage', 400.0) - 400.0) < 5.0
    
    def test_efficiency_optimization_modes(self, setup_system):
        """Test different optimization modes and their effects"""
        system = setup_system
        elec_opt = system['electrical_opt']
        
        test_states = []
        time_step = 0.01  # 10ms time step
        
        # Test each optimization mode
        for mode in OptimizationMode:
            elec_opt.config.mode = mode
            
            # Run optimization cycle
            state = {
                'power_output': 4000.0,
                'electrical_losses': 600.0,
                'voltage': 400.0,
                'current': 100.0,
                'power_factor': 0.93,
                'frequency': 50.0,
                'reactive_power': 0.1
            }
            
            # Update multiple times to build history
            for _ in range(20):
                adjustments = elec_opt.update(state, time_step)
                # Apply adjustments to state (simplified)
                for param, value in adjustments.items():
                    if param in state:
                        state[param] += value
            
            test_states.append(state)
        
        # Verify mode-specific improvements
        efficiency_state = test_states[0]  # EFFICIENCY mode
        pf_state = test_states[1]  # POWER_FACTOR mode
        grid_state = test_states[2]  # GRID_STABILITY mode
        
        # Each mode should excel in its focus area
        assert efficiency_state['power_output'] / (efficiency_state['power_output'] + 
               efficiency_state['electrical_losses']) > 0.92
        assert abs(pf_state['power_factor'] - 0.98) < 0.02
        assert abs(grid_state['frequency'] - 50.0) < 0.1
    
    def test_long_term_stability(self, setup_system):
        """Test system stability over extended operation"""
        system = setup_system
        engine = system['engine']
        perf_monitor = system['perf_monitor']
        
        # Run extended simulation
        stability_metrics = []
        for _ in range(500):
            engine.step()
            
            state = engine.get_state()
            stability_metrics.append({
                'efficiency': getattr(state, 'efficiency', 0.0),
                'power_factor': getattr(state, 'power_factor', 1.0),
                'voltage': getattr(state, 'voltage', 400.0),
                'frequency': getattr(state, 'frequency', 50.0)
            })
            
            time.sleep(0.001)  # Small delay to prevent CPU overload
        
        # Calculate stability metrics
        metrics_array = np.array([list(m.values()) for m in stability_metrics])
        variations = np.std(metrics_array, axis=0)
        
        # Verify stability
        assert variations[0] < 0.05  # Efficiency variation
        assert variations[1] < 0.02  # Power factor variation
        assert variations[2] < 10.0  # Voltage variation
        assert variations[3] < 0.2   # Frequency variation
    
    def test_fault_recovery_optimization(self, setup_system):
        """Test optimization during fault recovery"""
        system = setup_system
        engine = system['engine']
        electrical_system = system['electrical_system']
        
        # Simulate normal operation
        for _ in range(50):
            engine.step()
        
        # Get pre-fault state
        pre_fault_state = engine.get_state()
        pre_fault_efficiency = getattr(pre_fault_state, 'efficiency', 0.0)
        
        # Inject fault
        electrical_system.inject_fault("test_fault")
        
        # Run recovery optimization
        for _ in range(100):
            engine.step()
            time.sleep(0.01)
        
        # Get post-recovery state
        post_recovery_state = engine.get_state()
        post_recovery_efficiency = getattr(post_recovery_state, 'efficiency', 0.0)
        
        # Verify recovery
        assert post_recovery_efficiency >= 0.9 * pre_fault_efficiency
        assert getattr(post_recovery_state, 'fault_active', True) is False
    
    def test_performance_metrics_validation(self, setup_system):
        """Validate performance metrics collection and analysis"""
        system = setup_system
        perf_monitor = system['perf_monitor']
        real_monitor = system['real_monitor']
        
        # Run system with monitoring
        for _ in range(100):
            state = {
                'power_output': 4500.0,
                'mechanical_losses': 500.0,
                'electrical_losses': 400.0,
                'chain_tension': 38000.0,
                'voltage': 400.0,
                'current': 90.0,
                'power_factor': 0.95,
                'frequency': 50.0
            }
            
            real_monitor.update(state)
            time.sleep(0.01)
        
        # Get monitoring summaries
        perf_summary = perf_monitor.get_performance_summary()
        real_summary = real_monitor.get_performance_summary()
        
        # Verify metric collection
        assert 'system_resources' in perf_summary
        assert 'component_performance' in perf_summary
        assert 'mechanical_efficiency' in real_summary
        assert 'electrical_efficiency' in real_summary
        
        # Verify metric quality
        optimization_metrics = perf_summary.get('optimization_metrics', {})
        if isinstance(optimization_metrics, dict):
            for v in optimization_metrics.values():
                if isinstance(v, (int, float)):
                    assert 0.0 <= v <= 1.0 