"""
Test Phase 4: Advanced Control Systems
Comprehensive tests for the integrated advanced control system.
"""

import pytest
import numpy as np
import logging
from unittest.mock import Mock, MagicMock

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from simulation.control.timing_controller import TimingController
from simulation.control.load_manager import LoadManager, LoadProfile
from simulation.control.grid_stability_controller import GridStabilityController, GridStabilityMode
from simulation.control.fault_detector import FaultDetector, FaultSeverity
from simulation.control.integrated_control_system import (
    IntegratedControlSystem, 
    ControlSystemConfig,
    create_standard_kpp_control_system
)

# Configure logging for tests
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class TestTimingController:
    """Test timing optimization controller"""
    
    def test_timing_controller_initialization(self):
        """Test timing controller initialization"""
        controller = TimingController(
            num_floaters=8,
            prediction_horizon=5.0,
            optimization_window=2.0
        )
        
        assert controller.num_floaters == 8
        assert controller.prediction_horizon == 5.0
        assert controller.optimization_window == 2.0
        assert len(controller.last_injection_times) == 8
        assert controller.current_time == 0.0
    
    def test_timing_controller_update(self):
        """Test timing controller update with mock system state"""
        controller = TimingController(num_floaters=4)
        
        # Mock system state
        system_state = {
            'chain_speed_rpm': 10.0,
            'power': 400000.0,
            'clutch_engaged': True,
            'floaters': [
                {'theta': 0.0, 'velocity': 1.0, 'is_filled': False},
                {'theta': 1.57, 'velocity': 1.0, 'is_filled': False},
                {'theta': 3.14, 'velocity': 1.0, 'is_filled': True},
                {'theta': 4.71, 'velocity': 1.0, 'is_filled': False}
            ],
            'electrical_output': {
                'load_torque_command': 1000.0
            }
        }
        
        result = controller.update(system_state, 0.1)
        
        # Verify update results
        assert 'timing_controller_output' in result
        assert 'optimal_injection_time' in result
        assert 'predicted_torque' in result
        assert 'controller_status' in result
        
        # Verify controller status
        status = result['controller_status']
        assert 'active_floaters' in status
        assert 'recent_injections' in status
        assert status['active_floaters'] <= 4
    
    def test_injection_timing_optimization(self):
        """Test injection timing optimization logic"""
        controller = TimingController(num_floaters=2, optimization_window=1.0)
        
        # Setup floater states
        system_state = {
            'chain_speed_rpm': 15.0,
            'power': 300000.0,
            'clutch_engaged': True,
            'floaters': [
                {'theta': 1.5, 'velocity': 2.0, 'is_filled': False},  # Near optimal position
                {'theta': 0.0, 'velocity': 1.0, 'is_filled': False}   # Far from optimal
            ]
        }
        
        result = controller.update(system_state, 0.1)
        
        # Should have timing recommendations
        assert result['timing_confidence'] is not None
        if result['optimal_injection_time'] is not None:
            assert result['optimal_injection_time'] >= controller.current_time


class TestLoadManager:
    """Test load management system"""
    
    def test_load_manager_initialization(self):
        """Test load manager initialization"""
        manager = LoadManager(
            target_power=500000.0,
            power_tolerance=0.05,
            max_ramp_rate=50000.0
        )
        
        assert manager.target_power == 500000.0
        assert manager.power_tolerance == 0.05
        assert manager.max_ramp_rate == 50000.0
        assert manager.current_load_factor == 0.0
    
    def test_load_manager_update(self):
        """Test load manager update"""
        manager = LoadManager(target_power=400000.0)
        
        system_state = {
            'power': 350000.0,
            'electrical_output': {
                'grid_voltage': 480.0,
                'grid_frequency': 60.0,
                'power_factor': 0.95,
                'load_factor': 0.7,
                'generator_temperature': 85.0,
                'rated_power': 530000.0
            }
        }
        
        result = manager.update(system_state, 0.1)
        
        # Verify update results
        assert 'load_manager_output' in result
        assert 'target_load_factor' in result
        assert 'power_setpoint' in result
        assert 'actual_power' in result
        
        # Verify load commands
        load_commands = result['load_manager_output']
        assert 'target_load_factor' in load_commands
        assert 'commanded_power' in load_commands
        assert 0.0 <= load_commands['target_load_factor'] <= 1.0
    
    def test_load_profile_management(self):
        """Test load profile management"""
        manager = LoadManager(target_power=400000.0)
        
        # Add a load profile
        profile = LoadProfile(
            target_power=450000.0,
            power_tolerance=0.03,
            ramp_rate=30000.0,
            priority=1,
            duration=5.0
        )
        
        manager.add_load_profile(profile)
        assert len(manager.active_profiles) == 1
        
        # Update with the profile
        system_state = {'power': 400000.0, 'electrical_output': {}}
        result = manager.update(system_state, 1.0)
        
        # Power setpoint should be influenced by the profile
        assert abs(result['power_setpoint'] - 450000.0) < 50000.0


class TestGridStabilityController:
    """Test grid stability controller"""
    
    def test_grid_stability_initialization(self):
        """Test grid stability controller initialization"""
        controller = GridStabilityController(
            rated_power=530000.0,
            nominal_voltage=480.0,
            nominal_frequency=60.0
        )
        
        assert controller.rated_power == 530000.0
        assert controller.nominal_voltage == 480.0
        assert controller.nominal_frequency == 60.0
        assert controller.current_mode == GridStabilityMode.NORMAL
    
    def test_grid_stability_update_normal(self):
        """Test grid stability update under normal conditions"""
        controller = GridStabilityController()
        
        system_state = {
            'electrical_output': {
                'grid_voltage': 480.0,
                'grid_frequency': 60.0,
                'power_factor': 0.95,
                'synchronized': True,
                'grid_connected': True
            }
        }
        
        result = controller.update(system_state, 0.1)
        
        # Verify normal operation
        assert result['operating_mode'] == 'normal'
        assert result['grid_connected'] == True
        assert result['voltage_stability_index'] > 0.9
        assert result['frequency_stability_index'] > 0.9
        assert result['overall_stability_index'] > 0.9
    
    def test_grid_stability_voltage_fault(self):
        """Test grid stability response to voltage fault"""
        controller = GridStabilityController()
        
        # Simulate voltage fault
        system_state = {
            'electrical_output': {
                'grid_voltage': 400.0,  # Low voltage
                'grid_frequency': 60.0,
                'power_factor': 0.95,
                'synchronized': True,
                'grid_connected': True
            }
        }
        
        result = controller.update(system_state, 0.1)
        
        # Should detect voltage issue
        assert result['voltage_stability_index'] < 0.9
        assert result['active_faults'] > 0
        assert result['operating_mode'] in ['voltage_support', 'ride_through']


class TestFaultDetector:
    """Test fault detection system"""
    
    def test_fault_detector_initialization(self):
        """Test fault detector initialization"""
        detector = FaultDetector(
            monitoring_interval=0.1,
            auto_recovery_enabled=True
        )
        
        assert detector.monitoring_interval == 0.1
        assert detector.auto_recovery_enabled == True
        assert len(detector.active_faults) == 0
        assert len(detector.fault_detectors) > 0
    
    def test_fault_detection(self):
        """Test fault detection with various system conditions"""
        detector = FaultDetector()
        
        # Normal system state
        normal_state = {
            'chain_tension': 5000.0,
            'flywheel_speed_rpm': 350.0,
            'power': 400000.0,
            'overall_efficiency': 0.8,
            'electrical_output': {
                'grid_voltage': 480.0,
                'grid_frequency': 60.0,
                'generator_efficiency': 0.9,
                'generator_temperature': 85.0
            }
        }
        
        result = detector.update(normal_state, 0.1)
        fault_summary = result['fault_summary']
        
        # Should have minimal faults under normal conditions
        assert fault_summary['total_active_faults'] <= 2
        
        # Test with fault conditions
        fault_state = {
            'chain_tension': 20000.0,  # High tension
            'flywheel_speed_rpm': 450.0,  # Overspeed
            'power': 100000.0,
            'overall_efficiency': 0.5,  # Low efficiency
            'electrical_output': {
                'grid_voltage': 520.0,  # High voltage
                'grid_frequency': 61.5,  # High frequency
                'generator_efficiency': 0.6,  # Low efficiency
                'generator_temperature': 125.0  # Overtemperature
            }
        }
        
        result = detector.update(fault_state, 0.1)
        fault_summary = result['fault_summary']
        
        # Should detect multiple faults
        assert fault_summary['total_active_faults'] > 0
        assert len(result['critical_faults']) >= 0
    
    def test_component_health_assessment(self):
        """Test component health assessment"""
        detector = FaultDetector()
        
        system_state = {
            'floaters': [
                {'fill_efficiency': 0.9, 'dissolution_rate': 0.01},
                {'fill_efficiency': 0.85, 'dissolution_rate': 0.02}
            ],
            'drivetrain_output': {
                'overall_efficiency': 0.88,
                'vibration_level': 1.5,
                'temperature': 75.0
            },
            'electrical_output': {
                'generator_efficiency': 0.92,
                'generator_temperature': 80.0,
                'generator_vibration': 1.0,
                'power_electronics_efficiency': 0.91,
                'inverter_temperature': 65.0,
                'current_thd': 0.02
            }
        }
        
        result = detector.update(system_state, 0.1)
        component_health = result['component_health']
        
        # All components should have health scores
        expected_components = ['floaters', 'drivetrain', 'generator', 'power_electronics', 'control_system']
        for component in expected_components:
            assert component in component_health
            assert 0.0 <= component_health[component] <= 1.0


class TestIntegratedControlSystem:
    """Test integrated control system"""
    
    def test_integrated_system_initialization(self):
        """Test integrated control system initialization"""
        config = ControlSystemConfig(
            num_floaters=8,
            target_power=500000.0,
            nominal_voltage=480.0,
            nominal_frequency=60.0
        )
        
        system = IntegratedControlSystem(config)
        
        assert system.config.num_floaters == 8
        assert system.config.target_power == 500000.0
        assert system.system_mode == 'normal'
        assert not system.emergency_response_active
        
        # Verify all components are initialized
        assert system.timing_controller is not None
        assert system.load_manager is not None
        assert system.grid_stability_controller is not None
        assert system.fault_detector is not None
    
    def test_integrated_system_update(self):
        """Test integrated system update"""
        config = ControlSystemConfig(target_power=400000.0)
        system = IntegratedControlSystem(config)
        
        # Comprehensive system state
        system_state = {
            'time': 10.0,
            'power': 380000.0,
            'chain_tension': 8000.0,
            'flywheel_speed_rpm': 370.0,
            'chain_speed_rpm': 12.0,
            'clutch_engaged': True,
            'overall_efficiency': 0.82,
            'floaters': [
                {'theta': i * 0.785, 'velocity': 1.5, 'is_filled': i % 2 == 0}
                for i in range(8)
            ],
            'electrical_output': {
                'grid_voltage': 480.0,
                'grid_frequency': 60.0,
                'power_factor': 0.95,
                'load_factor': 0.75,
                'generator_efficiency': 0.92,
                'generator_temperature': 85.0,
                'power_electronics_efficiency': 0.91,
                'synchronized': True,
                'grid_connected': True,
                'load_torque_command': 1200.0
            }
        }
        
        result = system.update(system_state, 0.1)
        
        # Verify comprehensive output
        assert 'integrated_control_output' in result
        assert 'control_components_status' in result
        assert 'emergency_status' in result
        assert 'system_mode' in result
        assert 'system_health' in result
        
        # Verify control components operated
        components_status = result['control_components_status']
        expected_components = ['timing_controller', 'load_manager', 'grid_stability', 'fault_detector']
        for component in expected_components:
            assert component in components_status
            assert 'error' not in components_status[component]
        
        # Verify system health
        system_health = result['system_health']
        assert 'overall_health' in system_health
        assert 'component_health' in system_health
        assert 0.0 <= system_health['overall_health'] <= 1.0
    
    def test_emergency_response(self):
        """Test emergency response functionality"""
        system = create_standard_kpp_control_system()
        
        # Simulate critical fault condition
        critical_state = {
            'power': 100000.0,
            'chain_tension': 25000.0,  # Excessive tension
            'flywheel_speed_rpm': 500.0,  # Overspeed
            'overall_efficiency': 0.3,
            'emergency_stop_active': True,
            'electrical_output': {
                'grid_voltage': 350.0,  # Very low voltage
                'grid_frequency': 58.0,  # Low frequency
                'power_factor': 0.7,
                'generator_temperature': 130.0,  # Overtemperature
                'synchronized': False,
                'grid_connected': False
            }
        }
        
        result = system.update(critical_state, 0.1)
        
        # Should trigger emergency response
        emergency_status = result['emergency_status']
        assert emergency_status['emergency_active'] == True
        assert system.system_mode != 'normal'
        
        # Control commands should reflect emergency state
        commands = result['integrated_control_output']
        assert commands.get('emergency_shutdown') == True or commands.get('target_load_factor', 1.0) < 0.5
    
    def test_factory_function(self):
        """Test factory function for standard system creation"""
        system = create_standard_kpp_control_system()
        
        assert isinstance(system, IntegratedControlSystem)
        assert system.config.target_power == 530000.0  # Default KMP power
        assert system.config.num_floaters == 8
        assert system.config.nominal_voltage == 480.0
        
        # Test with overrides
        overrides = {
            'target_power': 400000.0,
            'num_floaters': 6
        }
        
        custom_system = create_standard_kpp_control_system(overrides)
        assert custom_system.config.target_power == 400000.0
        assert custom_system.config.num_floaters == 6
    
    def test_control_coordination(self):
        """Test control decision coordination"""
        system = create_standard_kpp_control_system()
        
        # System state that would generate conflicting control decisions
        conflicting_state = {
            'power': 450000.0,
            'chain_tension': 12000.0,
            'flywheel_speed_rpm': 380.0,
            'chain_speed_rpm': 15.0,
            'clutch_engaged': True,
            'overall_efficiency': 0.75,
            'floaters': [
                {'theta': i * 0.785, 'velocity': 1.2, 'is_filled': False}
                for i in range(8)
            ],
            'electrical_output': {
                'grid_voltage': 470.0,  # Slightly low
                'grid_frequency': 60.3,  # Slightly high
                'power_factor': 0.88,   # Low power factor
                'load_factor': 0.85,
                'generator_efficiency': 0.89,
                'generator_temperature': 95.0,
                'synchronized': True,
                'grid_connected': True,
                'load_torque_command': 1400.0
            }
        }
        
        result = system.update(conflicting_state, 0.1)
        
        # Should produce coordinated commands
        commands = result['integrated_control_output']
        assert isinstance(commands, dict)
        assert len(commands) > 0
        
        # Commands should be reasonable
        if 'target_load_factor' in commands:
            assert 0.0 <= commands['target_load_factor'] <= 1.0
        if 'injection_command' in commands:
            assert isinstance(commands['injection_command'], bool)


def run_phase4_tests():
    """Run all Phase 4 tests"""
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("=" * 60)
    print("PHASE 4 ADVANCED CONTROL SYSTEMS - COMPREHENSIVE TEST SUITE")
    print("=" * 60)
    
    test_classes = [
        TestTimingController,
        TestLoadManager,
        TestGridStabilityController,
        TestFaultDetector,
        TestIntegratedControlSystem
    ]
    
    total_tests = 0
    passed_tests = 0
    failed_tests = []
    
    for test_class in test_classes:
        print(f"\nTesting {test_class.__name__}...")
        test_methods = [method for method in dir(test_class) if method.startswith('test_')]
        
        for test_method in test_methods:
            total_tests += 1
            try:
                test_instance = test_class()
                getattr(test_instance, test_method)()
                print(f"  ✓ {test_method}")
                passed_tests += 1
            except Exception as e:
                print(f"  ✗ {test_method}: {e}")
                failed_tests.append(f"{test_class.__name__}.{test_method}: {e}")
    
    print("\n" + "=" * 60)
    print("PHASE 4 TEST RESULTS")
    print("=" * 60)
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {len(failed_tests)}")
    print(f"Success Rate: {passed_tests/total_tests*100:.1f}%")
    
    if failed_tests:
        print("\nFailed Tests:")
        for failure in failed_tests:
            print(f"  - {failure}")
    
    print("\nPhase 4 Advanced Control Systems:", "✓ OPERATIONAL" if len(failed_tests) == 0 else f"⚠ {len(failed_tests)} ISSUES")
    
    return len(failed_tests) == 0


if __name__ == "__main__":
    success = run_phase4_tests()
    exit(0 if success else 1)
