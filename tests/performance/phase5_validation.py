import pytest
import time
import numpy as np
from typing import Dict, Any
from simulation.monitoring.performance_monitor import PerformanceMonitor
from simulation.monitoring.real_time_monitor import RealTimeMonitor
from simulation.engine import SimulationEngine
from simulation.grid_services.grid_services_coordinator import GridServicesCoordinator
from simulation.components.integrated_electrical_system import IntegratedElectricalSystem

class TestPhase5Validation:
    """Comprehensive validation tests for Phase 5 optimization."""
    
    @pytest.fixture
    def setup_monitoring(self):
        """Set up monitoring systems."""
        perf_monitor = PerformanceMonitor(alert_threshold=70.0, sampling_interval=0.1)
        real_monitor = RealTimeMonitor(buffer_size=1000)
        return perf_monitor, real_monitor
    
    @pytest.fixture
    def setup_simulation(self):
        """Set up simulation components."""
        engine = SimulationEngine()
        coordinator = GridServicesCoordinator()
        electrical_system = IntegratedElectricalSystem()
        
        engine.register_component('grid_coordinator', coordinator)
        engine.register_component('electrical_system', electrical_system)
        
        return engine
    
    def test_system_optimization_metrics(self, setup_monitoring, setup_simulation):
        """Test system-wide optimization metrics collection and analysis."""
        perf_monitor, real_monitor = setup_monitoring
        engine = setup_simulation
        
        # Start monitoring
        perf_monitor.start_monitoring()
        
        # Run simulation steps
        for _ in range(100):
            perf_monitor.start_component_timing('simulation_step')
            engine.step()
            perf_monitor.stop_component_timing('simulation_step')
            
            # Record system state
            state = engine.get_state()
            real_monitor.update(state)
            
            time.sleep(0.01)  # Small delay between steps
        
        # Get performance summary
        summary = perf_monitor.get_performance_summary()
        
        # Verify metrics collection
        assert 'system_resources' in summary
        assert 'component_performance' in summary
        assert 'optimization_metrics' in summary
        
        # Check optimization scores
        assert summary['optimization_metrics']['mechanical_efficiency']['current'] > 0
        assert summary['optimization_metrics']['electrical_efficiency']['current'] > 0
    
    def test_real_time_optimization_suggestions(self, setup_monitoring, setup_simulation):
        """Test real-time optimization suggestion generation."""
        _, real_monitor = setup_monitoring
        engine = setup_simulation
        
        # Run simulation with suboptimal parameters
        state = {
            'mechanical_efficiency': 0.75,  # Below threshold
            'electrical_efficiency': 0.85,  # Below threshold
            'total_power_output': 1500.0,   # Below minimum
            'chain_tension': 46000.0,       # Above maximum
            'floater_positions': [0.0, 1.0, 2.0],
            'mechanical_losses': 2000.0,
            'electrical_losses': 1500.0,
            'thermal_losses': 500.0,
            'grid_frequency': 50.0,
            'grid_voltage': 230.0,
            'power_factor': 0.95
        }
        
        real_monitor.update(state)
        summary = real_monitor.get_performance_summary()
        
        # Verify optimization suggestions
        assert len(real_monitor.optimization_suggestions) > 0
        assert any(s['category'] == 'mechanical' for s in real_monitor.optimization_suggestions)
        assert any(s['category'] == 'electrical' for s in real_monitor.optimization_suggestions)
    
    def test_component_performance_tracking(self, setup_monitoring, setup_simulation):
        """Test detailed component performance tracking."""
        perf_monitor, _ = setup_monitoring
        engine = setup_simulation
        
        perf_monitor.start_monitoring()
        
        # Test multiple components
        components = ['electrical_system', 'grid_coordinator', 'physics_engine']
        
        for component in components:
            perf_monitor.start_component_timing(component)
            time.sleep(0.05)  # Simulate component execution
            perf_monitor.stop_component_timing(component)
        
        summary = perf_monitor.get_performance_summary()
        
        # Verify component timing tracking
        assert 'component_performance' in summary
        for component in components:
            assert component in summary['component_performance']
            assert summary['component_performance'][component]['average_time'] > 0
    
    def test_system_efficiency_optimization(self, setup_monitoring, setup_simulation):
        """Test system efficiency optimization tracking."""
        perf_monitor, real_monitor = setup_monitoring
        engine = setup_simulation
        
        initial_state = {
            'mechanical_efficiency': 0.80,
            'electrical_efficiency': 0.85,
            'total_power_output': 2500.0
        }
        
        # Record initial metrics
        real_monitor.update(initial_state)
        
        # Simulate optimization improvements
        improved_state = {
            'mechanical_efficiency': 0.88,
            'electrical_efficiency': 0.92,
            'total_power_output': 3000.0
        }
        
        real_monitor.update(improved_state)
        
        summary = real_monitor.get_performance_summary()
        
        # Verify efficiency improvements
        assert summary['mechanical_efficiency']['trend'] == 'increasing'
        assert summary['electrical_efficiency']['trend'] == 'increasing'
        assert summary['power_output']['current'] > summary['power_output']['average']
    
    def test_performance_alerts_and_bottlenecks(self, setup_monitoring, setup_simulation):
        """Test performance alert generation and bottleneck detection."""
        perf_monitor, _ = setup_monitoring
        
        # Simulate high resource usage
        for _ in range(10):
            perf_monitor.start_component_timing('heavy_component')
            time.sleep(0.2)  # Simulate slow component
            perf_monitor.stop_component_timing('heavy_component')
        
        summary = perf_monitor.get_performance_summary()
        
        # Verify alerts and bottlenecks
        assert len(summary['alerts']) > 0
        assert any(alert['type'] == 'slow_component' for alert in summary['alerts'])
        
        # Check component metrics
        assert 'heavy_component' in summary['component_performance']
        assert summary['component_performance']['heavy_component']['average_time'] > 0.1 