"""
Test Suite for Phase 7: Performance Analysis and Optimization

Comprehensive tests for energy analysis and performance metrics modules.
"""

import unittest
import time
import math
from unittest.mock import MagicMock, patch

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from simulation.pneumatics.energy_analysis import (
    EnergyAnalyzer, EnergyBalance, PowerMetrics, EnergyFlow, EnergyFlowType,
    create_standard_energy_analyzer
)
from simulation.pneumatics.performance_metrics import (
    PerformanceAnalyzer, PerformanceSnapshot, EROIAnalysis, CapacityAnalysis,
    OptimizationTarget, OptimizationRecommendation, create_standard_performance_analyzer
)


class TestEnergyAnalyzer(unittest.TestCase):
    """Test cases for EnergyAnalyzer class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.analyzer = EnergyAnalyzer(analysis_window=60.0, sampling_rate=10.0)
    
    def test_initialization(self):
        """Test energy analyzer initialization."""
        self.assertEqual(self.analyzer.analysis_window, 60.0)
        self.assertEqual(self.analyzer.sampling_rate, 10.0)
        self.assertEqual(len(self.analyzer.energy_balances), 0)
        self.assertEqual(len(self.analyzer.power_metrics), 0)
        self.assertEqual(self.analyzer.cumulative_energy_input, 0.0)
    
    def test_compression_energy_calculation(self):
        """Test compression energy calculations."""
        # Test isothermal compression
        result = self.analyzer.calculate_compression_energy(
            initial_pressure=101325.0,
            final_pressure=250000.0,
            volume=0.01,
            temperature=293.15,
            compression_mode='isothermal'
        )
        
        self.assertGreater(result['ideal_work'], 0)
        self.assertGreater(result['heat_generated'], 0)
        self.assertAlmostEqual(result['pressure_ratio'], 250000.0/101325.0, places=3)
        self.assertEqual(result['compression_mode'], 'isothermal')
        
        # Test adiabatic compression
        result_adiabatic = self.analyzer.calculate_compression_energy(
            initial_pressure=101325.0,
            final_pressure=250000.0,
            volume=0.01,
            temperature=293.15,
            compression_mode='adiabatic'
        )
        
        self.assertGreater(result_adiabatic['ideal_work'], 0)
        self.assertNotEqual(result['ideal_work'], result_adiabatic['ideal_work'])
    
    def test_expansion_energy_calculation(self):
        """Test expansion energy calculations."""
        result = self.analyzer.calculate_expansion_energy(
            initial_pressure=250000.0,
            final_pressure=101325.0,
            volume=0.01,
            temperature=293.15,
            expansion_mode='mixed'
        )
        
        self.assertGreater(result['ideal_work'], 0)
        self.assertGreater(result['heat_absorbed'], 0)
        self.assertAlmostEqual(result['pressure_ratio'], 250000.0/101325.0, places=3)
    
    def test_pneumatic_storage_energy(self):
        """Test pneumatic storage energy calculation."""
        # Test with compressed air
        stored_energy = self.analyzer.calculate_pneumatic_storage_energy(
            pressure=250000.0,
            volume=0.01,
            reference_pressure=101325.0
        )
        self.assertGreater(stored_energy, 0)
        
        # Test with atmospheric pressure
        stored_energy_zero = self.analyzer.calculate_pneumatic_storage_energy(
            pressure=101325.0,
            volume=0.01,
            reference_pressure=101325.0
        )
        self.assertEqual(stored_energy_zero, 0.0)
        
        # Test with pressure below reference
        stored_energy_negative = self.analyzer.calculate_pneumatic_storage_energy(
            pressure=50000.0,
            volume=0.01,
            reference_pressure=101325.0
        )
        self.assertEqual(stored_energy_negative, 0.0)
    
    def test_thermal_energy_contribution(self):
        """Test thermal energy contribution calculations."""
        result = self.analyzer.calculate_thermal_energy_contribution(
            air_temperature=320.15,   # 47°C
            water_temperature=288.15, # 15°C
            volume=0.01,
            heat_transfer_coefficient=100.0
        )
        
        self.assertGreater(result['thermal_energy'], 0)
        self.assertGreater(result['heat_transfer_rate'], 0)
        self.assertGreater(result['thermal_efficiency'], 1.0)
        self.assertEqual(result['temperature_difference'], 320.15 - 288.15)
    
    def test_energy_balance_recording(self):
        """Test energy balance recording."""
        balance = self.analyzer.record_energy_balance(
            electrical_input=10000.0,
            pneumatic_storage=8000.0,
            mechanical_output=6000.0,
            heat_losses=2000.0,
            venting_losses=500.0
        )
        
        self.assertEqual(balance.electrical_input, 10000.0)
        self.assertEqual(balance.mechanical_work, 6000.0)
        self.assertEqual(balance.compression_efficiency, 0.8)  # 8000/10000
        self.assertEqual(balance.expansion_efficiency, 0.75)   # 6000/8000
        self.assertEqual(balance.overall_efficiency, 0.6)     # 6000/10000
        
        self.assertEqual(len(self.analyzer.energy_balances), 1)
        self.assertEqual(self.analyzer.cumulative_energy_input, 10000.0)
        self.assertEqual(self.analyzer.cumulative_energy_output, 6000.0)
    
    def test_power_metrics_recording(self):
        """Test power metrics recording."""
        metrics = self.analyzer.record_power_metrics(
            compressor_power=5000.0,
            mechanical_power=4000.0,
            heat_loss_rate=500.0
        )
        
        self.assertEqual(metrics.compressor_power, 5000.0)
        self.assertEqual(metrics.mechanical_power, 4000.0)
        self.assertEqual(metrics.instantaneous_efficiency, 0.8)  # 4000/5000
        
        self.assertEqual(len(self.analyzer.power_metrics), 1)
    
    def test_energy_flow_recording(self):
        """Test energy flow recording."""
        flow = self.analyzer.record_energy_flow(
            flow_type=EnergyFlowType.ELECTRICAL_INPUT,
            value=1000.0,
            description="Test electrical input"
        )
        
        self.assertEqual(flow.flow_type, EnergyFlowType.ELECTRICAL_INPUT)
        self.assertEqual(flow.value, 1000.0)
        self.assertEqual(flow.description, "Test electrical input")
        
        self.assertEqual(len(self.analyzer.energy_flows), 1)
    
    def test_efficiency_calculations(self):
        """Test efficiency calculation methods."""
        # Record some test data
        for i in range(5):
            self.analyzer.record_energy_balance(
                electrical_input=10000.0,
                pneumatic_storage=8000.0,
                mechanical_output=6000.0 + i * 200,  # Varying output
                heat_losses=2000.0,
                venting_losses=500.0
            )
        
        efficiency_metrics = self.analyzer.get_current_efficiency()
        
        self.assertIn('overall_efficiency', efficiency_metrics)
        self.assertIn('compression_efficiency', efficiency_metrics)
        self.assertIn('expansion_efficiency', efficiency_metrics)
        self.assertIn('peak_efficiency', efficiency_metrics)
        self.assertIn('average_efficiency', efficiency_metrics)
        
        self.assertGreater(efficiency_metrics['overall_efficiency'], 0)
        self.assertGreater(efficiency_metrics['peak_efficiency'], 0)
    
    def test_energy_summary(self):
        """Test energy summary calculations."""
        # Record some test data
        self.analyzer.record_energy_balance(
            electrical_input=10000.0,
            pneumatic_storage=8000.0,
            mechanical_output=6000.0,
            heat_losses=2000.0,
            venting_losses=500.0
        )
        
        summary = self.analyzer.get_energy_summary()
        
        self.assertEqual(summary['total_input'], 10000.0)
        self.assertEqual(summary['total_output'], 6000.0)
        self.assertEqual(summary['total_losses'], 2500.0)
        self.assertEqual(summary['cumulative_efficiency'], 0.6)
    
    def test_energy_conservation_validation(self):
        """Test energy conservation validation."""
        # Record balanced energy data
        self.analyzer.record_energy_balance(
            electrical_input=10000.0,
            pneumatic_storage=8000.0,
            mechanical_output=6000.0,
            heat_losses=2500.0,
            venting_losses=1500.0
        )
        
        validation = self.analyzer.validate_energy_conservation(tolerance=0.01)
        
        self.assertTrue(validation['valid'])
        self.assertLess(validation['relative_error'], 0.01)
        
        # Test with unbalanced data
        self.analyzer.record_energy_balance(
            electrical_input=1000.0,   # Much less input
            pneumatic_storage=8000.0,
            mechanical_output=6000.0,
            heat_losses=2500.0,
            venting_losses=1500.0
        )
        
        validation_invalid = self.analyzer.validate_energy_conservation(tolerance=0.01)
        self.assertFalse(validation_invalid['valid'])


class TestPerformanceAnalyzer(unittest.TestCase):
    """Test cases for PerformanceAnalyzer class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.analyzer = PerformanceAnalyzer(
            rated_power=5000.0,
            analysis_window=300.0,
            baseline_efficiency=0.75
        )
    
    def test_initialization(self):
        """Test performance analyzer initialization."""
        self.assertEqual(self.analyzer.rated_power, 5000.0)
        self.assertEqual(self.analyzer.analysis_window, 300.0)
        self.assertEqual(self.analyzer.baseline_efficiency, 0.75)
        self.assertEqual(len(self.analyzer.performance_snapshots), 0)
    
    def test_performance_snapshot_recording(self):
        """Test performance snapshot recording."""
        snapshot = self.analyzer.record_performance_snapshot(
            electrical_power=4000.0,
            mechanical_power=3200.0,
            thermal_power=200.0,
            compression_efficiency=0.85,
            expansion_efficiency=0.80,
            ambient_temp=293.15,
            water_temp=288.15,
            depth=10.0
        )
        
        self.assertEqual(snapshot.electrical_power, 4000.0)
        self.assertEqual(snapshot.mechanical_power, 3200.0)
        self.assertEqual(snapshot.thermal_power, 200.0)
        self.assertAlmostEqual(snapshot.instantaneous_efficiency, 0.85, places=2)  # (3200+200)/4000
        self.assertAlmostEqual(snapshot.capacity_factor, 0.8, places=2)  # 4000/5000
        
        self.assertEqual(len(self.analyzer.performance_snapshots), 1)
    
    def test_eroi_analysis(self):
        """Test EROI analysis calculation."""
        # Record some performance data
        for i in range(10):
            self.analyzer.record_performance_snapshot(
                electrical_power=4000.0,
                mechanical_power=3000.0 + i * 50,  # Varying output
                thermal_power=200.0,
                compression_efficiency=0.85,
                expansion_efficiency=0.80
            )
        
        eroi_analysis = self.analyzer.calculate_eroi_analysis(time_window=3600.0)
        
        self.assertGreater(eroi_analysis.energy_invested, 0)
        self.assertGreater(eroi_analysis.energy_returned, 0)
        self.assertGreater(eroi_analysis.eroi_ratio, 0)
        self.assertGreater(eroi_analysis.compressor_investment, 0)
        self.assertEqual(len(self.analyzer.eroi_analyses), 1)
    
    def test_capacity_analysis(self):
        """Test capacity analysis calculation."""
        # Record varying power data
        power_levels = [1000.0, 3000.0, 5000.0, 4000.0, 2000.0]
        for power in power_levels:
            self.analyzer.record_performance_snapshot(
                electrical_power=power,
                mechanical_power=power * 0.8,
                thermal_power=100.0
            )
        
        capacity_analysis = self.analyzer.calculate_capacity_analysis(time_window=3600.0)
        
        self.assertEqual(capacity_analysis.rated_power, 5000.0)
        self.assertGreater(capacity_analysis.actual_power, 0)
        self.assertEqual(capacity_analysis.peak_power, 5000.0)
        self.assertGreater(capacity_analysis.capacity_factor, 0)
        self.assertEqual(capacity_analysis.utilization_factor, 1.0)  # All snapshots operational
    
    def test_optimization_recommendations(self):
        """Test optimization recommendation generation."""
        # Record suboptimal performance data
        for i in range(5):
            self.analyzer.record_performance_snapshot(
                electrical_power=3000.0,
                mechanical_power=1800.0,  # Low efficiency (60%)
                thermal_power=50.0,       # Low thermal boost
                compression_efficiency=0.70,
                expansion_efficiency=0.65
            )
        
        recommendations = self.analyzer.generate_optimization_recommendations()
        
        self.assertGreater(len(recommendations), 0)
        
        # Check that recommendations have required fields
        for rec in recommendations:
            self.assertIsInstance(rec.target, OptimizationTarget)
            self.assertIsInstance(rec.parameter, str)
            self.assertIsInstance(rec.current_value, (int, float))
            self.assertIsInstance(rec.recommended_value, (int, float))
            self.assertIsInstance(rec.expected_improvement, (int, float))
            self.assertIsInstance(rec.confidence, (int, float))
            self.assertTrue(0 <= rec.confidence <= 1)
    
    def test_power_factor_calculation(self):
        """Test power factor calculation."""
        # Record some performance data
        for i in range(5):
            self.analyzer.record_performance_snapshot(
                electrical_power=4000.0,
                mechanical_power=3200.0
            )
        
        power_factor = self.analyzer.calculate_power_factor(time_window=60.0)
        
        self.assertGreater(power_factor, 0)
        self.assertLessEqual(power_factor, 1.0)
    
    def test_system_availability(self):
        """Test system availability calculation."""
        # Record mixed operational and non-operational data
        operational_powers = [4000.0, 3500.0, 4500.0]
        non_operational_powers = [0.0, 0.0]
        
        for power in operational_powers + non_operational_powers:
            self.analyzer.record_performance_snapshot(
                electrical_power=power,
                mechanical_power=power * 0.8 if power > 0 else 0
            )
        
        availability = self.analyzer.calculate_system_availability(time_window=3600.0)
        
        expected_availability = len(operational_powers) / (len(operational_powers) + len(non_operational_powers))
        self.assertAlmostEqual(availability, expected_availability, places=2)
    
    def test_performance_summary(self):
        """Test performance summary generation."""
        # Record some performance data
        for i in range(10):
            self.analyzer.record_performance_snapshot(
                electrical_power=4000.0 + i * 100,
                mechanical_power=3000.0 + i * 80,
                thermal_power=200.0
            )
        
        summary = self.analyzer.get_performance_summary()
        
        required_keys = [
            'average_efficiency', 'peak_efficiency', 'average_power', 'peak_power',
            'capacity_factor', 'thermal_efficiency', 'availability', 'power_factor',
            'baseline_comparison', 'peak_efficiency_achieved'
        ]
        
        for key in required_keys:
            self.assertIn(key, summary)
            self.assertIsInstance(summary[key], (int, float))
    
    def test_trend_analysis(self):
        """Test trend analysis calculation."""
        # Record data with improving efficiency trend
        for i in range(10):
            efficiency_improvement = i * 0.01  # 1% improvement per step
            base_power = 4000.0
            improved_output = base_power * (0.75 + efficiency_improvement)
            
            self.analyzer.record_performance_snapshot(
                electrical_power=base_power,
                mechanical_power=improved_output,
                thermal_power=100.0
            )
            
            time.sleep(0.01)  # Small delay to create time differences
        
        trend_analysis = self.analyzer.get_trend_analysis(window_hours=1.0)
        
        if trend_analysis:  # May be empty if insufficient data points
            self.assertIn('efficiency_trend', trend_analysis)
            self.assertIn('power_trend', trend_analysis)
            self.assertIn('efficiency_stability', trend_analysis)
            self.assertIn('data_points', trend_analysis)


class TestFactoryFunctions(unittest.TestCase):
    """Test cases for factory functions."""
    
    def test_create_standard_energy_analyzer(self):
        """Test standard energy analyzer creation."""
        analyzer = create_standard_energy_analyzer(analysis_window=120.0)
        
        self.assertIsInstance(analyzer, EnergyAnalyzer)
        self.assertEqual(analyzer.analysis_window, 120.0)
        self.assertEqual(analyzer.sampling_rate, 10.0)
    
    def test_create_standard_performance_analyzer(self):
        """Test standard performance analyzer creation."""
        analyzer = create_standard_performance_analyzer(rated_power=6000.0)
        
        self.assertIsInstance(analyzer, PerformanceAnalyzer)
        self.assertEqual(analyzer.rated_power, 6000.0)
        self.assertEqual(analyzer.analysis_window, 300.0)
        self.assertEqual(analyzer.baseline_efficiency, 0.80)


class TestIntegrationScenarios(unittest.TestCase):
    """Integration tests for combined energy and performance analysis."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.energy_analyzer = create_standard_energy_analyzer()
        self.performance_analyzer = create_standard_performance_analyzer()
    
    def test_complete_cycle_analysis(self):
        """Test complete pneumatic cycle analysis."""
        # Simulate a complete pneumatic cycle
        cycle_data = [
            # Compression phase
            {'electrical': 5000.0, 'mechanical': 0.0, 'phase': 'compression'},
            {'electrical': 5000.0, 'mechanical': 0.0, 'phase': 'compression'},
            {'electrical': 5000.0, 'mechanical': 0.0, 'phase': 'compression'},
            
            # Injection phase
            {'electrical': 2000.0, 'mechanical': 4000.0, 'phase': 'injection'},
            {'electrical': 2000.0, 'mechanical': 4000.0, 'phase': 'injection'},
            
            # Expansion/ascent phase
            {'electrical': 1000.0, 'mechanical': 3500.0, 'phase': 'expansion'},
            {'electrical': 1000.0, 'mechanical': 3500.0, 'phase': 'expansion'},
            {'electrical': 1000.0, 'mechanical': 3500.0, 'phase': 'expansion'},
            
            # Venting phase
            {'electrical': 500.0, 'mechanical': 0.0, 'phase': 'venting'},
            {'electrical': 500.0, 'mechanical': 0.0, 'phase': 'venting'},
        ]
        
        # Record data in both analyzers
        for i, data in enumerate(cycle_data):
            # Energy analysis
            self.energy_analyzer.record_power_metrics(
                compressor_power=data['electrical'],
                mechanical_power=data['mechanical']
            )
            
            # Performance analysis
            self.performance_analyzer.record_performance_snapshot(
                electrical_power=data['electrical'],
                mechanical_power=data['mechanical'],
                thermal_power=100.0
            )
            
            time.sleep(0.01)  # Small delay
        
        # Analyze results
        energy_summary = self.energy_analyzer.get_energy_summary()
        performance_summary = self.performance_analyzer.get_performance_summary()
        
        # Verify we have meaningful results
        self.assertGreater(len(self.energy_analyzer.power_metrics), 0)
        self.assertGreater(len(self.performance_analyzer.performance_snapshots), 0)
        
        if performance_summary:
            self.assertIn('average_efficiency', performance_summary)
            self.assertGreater(performance_summary['average_efficiency'], 0)
    
    def test_efficiency_optimization_workflow(self):
        """Test efficiency optimization workflow."""
        # Start with poor efficiency
        for i in range(5):
            self.performance_analyzer.record_performance_snapshot(
                electrical_power=5000.0,
                mechanical_power=2500.0,  # 50% efficiency
                thermal_power=100.0
            )
        
        # Generate optimization recommendations
        recommendations = self.performance_analyzer.generate_optimization_recommendations()
        
        # Verify recommendations were generated
        self.assertGreater(len(recommendations), 0)
          # Find efficiency recommendation
        efficiency_recs = [r for r in recommendations 
                          if r.target == OptimizationTarget.MAXIMIZE_EFFICIENCY]
        
        if efficiency_recs:
            rec = efficiency_recs[0]
            self.assertGreater(rec.expected_improvement, 0)
            self.assertGreater(rec.confidence, 0)
        
        # Reset performance history to measure post-optimization performance
        self.performance_analyzer.reset_performance_history()
        
        # Simulate implementing recommendations (improved efficiency)
        for i in range(5):
            self.performance_analyzer.record_performance_snapshot(
                electrical_power=5000.0,
                mechanical_power=4000.0,  # 80% efficiency (improved)
                thermal_power=200.0       # Better thermal boost
            )
        
        # Check improvement
        final_summary = self.performance_analyzer.get_performance_summary()
        if final_summary:
            self.assertGreater(final_summary['average_efficiency'], 0.75)


if __name__ == '__main__':
    # Configure test discovery
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestEnergyAnalyzer))
    suite.addTests(loader.loadTestsFromTestCase(TestPerformanceAnalyzer))
    suite.addTests(loader.loadTestsFromTestCase(TestFactoryFunctions))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegrationScenarios))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Exit with appropriate code
    sys.exit(0 if result.wasSuccessful() else 1)
