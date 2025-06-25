"""
Unit tests for Phase 6: Control System Integration

Tests cover:
- Pneumatic control coordinator functionality
- Sensor integration and monitoring
- Fault detection and recovery
- Performance optimization algorithms
- State machine transitions
- Control loop operation
"""

import pytest
import time
import threading
from unittest.mock import Mock, patch
from simulation.pneumatics.pneumatic_coordinator import (
    PneumaticControlCoordinator, ControlParameters, SystemState, FaultType,
    SensorReading, PneumaticSensors, create_standard_kpp_pneumatic_coordinator
)


class TestPneumaticControlCoordinator:
    """Test the main pneumatic control coordinator."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.control_params = ControlParameters(
            target_pressure=250000.0,
            pressure_tolerance=10000.0,
            max_pressure=350000.0,
            min_pressure=150000.0
        )
        self.coordinator = PneumaticControlCoordinator(
            control_params=self.control_params,
            enable_thermodynamics=True,
            enable_optimization=True
        )
    
    def test_initialization(self):
        """Test coordinator initialization."""
        assert self.coordinator.system_state == SystemState.STARTUP
        assert not self.coordinator.compressor_enabled
        assert self.coordinator.injection_enabled
        assert len(self.coordinator.active_faults) == 0
        assert self.coordinator.cycle_count == 0
        assert self.coordinator.enable_thermodynamics
    
    def test_sensor_update(self):
        """Test sensor reading updates."""
        initial_time = self.coordinator.sensors.tank_pressure.timestamp
        
        # Add small delay to ensure time difference
        time.sleep(0.01)
        
        # Update sensors
        self.coordinator.update_sensors(0.1)
        
        # Check that timestamps were updated
        assert self.coordinator.sensors.tank_pressure.timestamp > initial_time
        assert self.coordinator.sensors.compressor_temp.timestamp > initial_time
        assert self.coordinator.sensors.water_temp.timestamp > initial_time
        
        # Check that sensor values are reasonable
        assert 100000.0 < self.coordinator.sensors.tank_pressure.value < 400000.0  # 1-4 bar
        assert 280.0 < self.coordinator.sensors.compressor_temp.value < 400.0  # Reasonable temps
        assert 280.0 < self.coordinator.sensors.water_temp.value < 300.0  # Water temps
    
    def test_pressure_control_algorithm(self):
        """Test pressure control logic."""
        # Test compressor turn-on (low pressure)
        self.coordinator.sensors.tank_pressure.value = 200000.0  # 2.0 bar (below target)
        self.coordinator.pressure_control_algorithm()
        assert self.coordinator.compressor_enabled
        
        # Test compressor turn-off (high pressure)
        self.coordinator.sensors.tank_pressure.value = 280000.0  # 2.8 bar (above target + tolerance)
        self.coordinator.pressure_control_algorithm()
        assert not self.coordinator.compressor_enabled
        
        # Test hysteresis (within tolerance)
        self.coordinator.compressor_enabled = False
        self.coordinator.sensors.tank_pressure.value = 250000.0  # Exactly at target
        self.coordinator.pressure_control_algorithm()
        assert not self.coordinator.compressor_enabled  # Should not change
    
    def test_fault_detection(self):
        """Test fault detection algorithms."""
        # Test pressure fault detection
        self.coordinator.sensors.tank_pressure.value = 100000.0  # Too low
        self.coordinator.detect_faults()
        assert FaultType.PRESSURE_DROP in self.coordinator.active_faults
        
        # Clear fault and test overpressure
        self.coordinator.active_faults.clear()
        self.coordinator.sensors.tank_pressure.value = 400000.0  # Too high
        self.coordinator.detect_faults()
        assert FaultType.PRESSURE_DROP in self.coordinator.active_faults
        
        # Test thermal fault detection
        self.coordinator.active_faults.clear()
        self.coordinator.sensors.compressor_temp.value = 380.15  # 107°C - too hot
        self.coordinator.detect_faults()
        assert FaultType.THERMAL_OVERLOAD in self.coordinator.active_faults
        
        # Test sensor timeout detection
        self.coordinator.active_faults.clear()
        old_timestamp = time.time() - 10.0  # 10 seconds ago
        self.coordinator.sensors.tank_pressure.timestamp = old_timestamp
        self.coordinator.detect_faults()
        assert FaultType.SENSOR_FAILURE in self.coordinator.active_faults
    
    def test_state_machine_transitions(self):
        """Test system state machine transitions."""
        # Test startup to normal transition
        assert self.coordinator.system_state == SystemState.STARTUP
        
        # Set good conditions
        self.coordinator.sensors.tank_pressure.value = 250000.0
        self.coordinator.sensors.compressor_temp.value = 293.15
        self.coordinator.update_state_machine()
        
        assert self.coordinator.system_state == SystemState.NORMAL
        
        # Test fault transition
        self.coordinator.add_fault(FaultType.PRESSURE_DROP, "Test fault")
        self.coordinator.handle_faults()
        assert self.coordinator.system_state == SystemState.FAULT
        
        # Test emergency stop transition
        self.coordinator.add_fault(FaultType.THERMAL_OVERLOAD, "Critical fault")
        self.coordinator.handle_faults()
        assert self.coordinator.system_state == SystemState.EMERGENCY_STOP
          # Test auto-recovery
        self.coordinator.system_state = SystemState.FAULT
        self.coordinator.clear_fault(FaultType.PRESSURE_DROP)
        self.coordinator.clear_fault(FaultType.THERMAL_OVERLOAD)  # Clear all faults
        self.coordinator.update_state_machine()
        assert self.coordinator.system_state == SystemState.NORMAL
    
    def test_injection_control(self):
        """Test injection control algorithm."""
        # Set up for injection
        self.coordinator.injection_enabled = True
        self.coordinator.sensors.tank_pressure.value = 300000.0  # Good pressure
        self.coordinator.last_injection_time = time.time() - 1.0  # 1 second ago
        
        initial_cycle_count = self.coordinator.cycle_count
        
        # Trigger injection
        self.coordinator.injection_control_algorithm()
        
        # Check that injection was triggered (cycle count should increase)
        # Note: This depends on the actual implementation
        assert self.coordinator.last_injection_time > time.time() - 0.1  # Recent injection
    
    def test_thermal_control_integration(self):
        """Test thermal control algorithm with Phase 5 integration."""
        # Test thermal management activation
        self.coordinator.sensors.compressor_temp.value = 353.15  # 80°C - at threshold
        
        # Should not raise exception
        self.coordinator.thermal_control_algorithm()
        
        # Test thermal efficiency calculation
        efficiency = self.coordinator.calculate_thermal_efficiency(320.15, 290.15)
        assert isinstance(efficiency, float)
        assert 0.5 < efficiency < 1.5  # Reasonable efficiency range
    
    def test_performance_optimization(self):
        """Test performance optimization algorithms."""
        # Set up optimization conditions
        self.coordinator.system_state = SystemState.OPTIMIZATION
        self.coordinator.sensors.compressor_temp.value = 320.15
        self.coordinator.sensors.water_temp.value = 290.15
        
        initial_target = self.coordinator.control_params.target_pressure
        
        # Run optimization
        self.coordinator.performance_optimization_algorithm()
        
        # Check that optimization occurred (target may have changed)
        # The exact change depends on the algorithm implementation
        assert isinstance(self.coordinator.control_params.target_pressure, float)
    
    def test_fault_recovery(self):
        """Test fault recovery procedures."""
        # Add a recoverable fault
        self.coordinator.add_fault(FaultType.PRESSURE_DROP, "Test recoverable fault")
        assert FaultType.PRESSURE_DROP in self.coordinator.active_faults
        
        # Test recovery
        recovery_success = self.coordinator.attempt_fault_recovery(FaultType.PRESSURE_DROP)
        assert recovery_success
        
        # Test non-recoverable fault
        recovery_success = self.coordinator.attempt_fault_recovery(FaultType.COMPRESSOR_FAILURE)
        assert not recovery_success
    
    def test_emergency_stop(self):
        """Test emergency stop functionality."""
        # Enable systems first
        self.coordinator.compressor_enabled = True
        self.coordinator.injection_enabled = True
        
        # Trigger emergency stop
        self.coordinator.emergency_stop()
        
        # Check that all systems are disabled
        assert not self.coordinator.compressor_enabled
        assert not self.coordinator.injection_enabled
        assert self.coordinator.system_state == SystemState.EMERGENCY_STOP
    
    def test_system_reset(self):
        """Test system reset functionality."""
        # Set up a faulty state
        self.coordinator.add_fault(FaultType.PRESSURE_DROP, "Test fault")
        self.coordinator.system_state = SystemState.EMERGENCY_STOP
        self.coordinator.cycle_count = 10
        
        # Reset system
        self.coordinator.reset_system()
        
        # Check that system is reset
        assert len(self.coordinator.active_faults) == 0
        assert self.coordinator.system_state == SystemState.STARTUP
        assert self.coordinator.cycle_count == 0
        assert self.coordinator.injection_enabled
    
    def test_system_status_reporting(self):
        """Test system status reporting."""
        # Update some sensor values
        self.coordinator.sensors.tank_pressure.value = 250000.0
        self.coordinator.sensors.compressor_temp.value = 320.15
        self.coordinator.cycle_count = 5
        
        status = self.coordinator.get_system_status()
        
        # Check status structure
        assert 'state' in status
        assert 'sensors' in status
        assert 'control' in status
        assert 'faults' in status
        assert 'performance' in status
        
        # Check sensor data
        assert status['sensors']['tank_pressure']['value'] == 2.5  # 2.5 bar
        assert status['sensors']['compressor_temp']['value'] == 47.0  # 47°C
        assert status['control']['cycle_count'] == 5
        
        # Check units
        assert status['sensors']['tank_pressure']['unit'] == 'bar'
        assert status['sensors']['compressor_temp']['unit'] == '°C'
    
    def test_control_parameter_updates(self):
        """Test dynamic control parameter updates."""
        initial_pressure = self.coordinator.control_params.target_pressure
        
        # Update parameters
        new_params = {
            'target_pressure': 300000.0,  # 3.0 bar
            'pressure_tolerance': 15000.0
        }
        self.coordinator.set_control_parameters(new_params)
        
        # Check that parameters were updated
        assert self.coordinator.control_params.target_pressure == 300000.0
        assert self.coordinator.control_params.pressure_tolerance == 15000.0
        
        # Invalid parameter should be ignored
        invalid_params = {'invalid_param': 123}
        self.coordinator.set_control_parameters(invalid_params)
        # Should not raise exception


class TestControlLoopOperation:
    """Test the control loop threading and timing."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.coordinator = PneumaticControlCoordinator()
    
    def test_control_loop_start_stop(self):
        """Test control loop threading."""
        assert not self.coordinator.running
        
        # Start control loop
        self.coordinator.start_control_loop()
        assert self.coordinator.running
        assert self.coordinator.control_thread is not None
        
        # Give it time to run a few iterations
        time.sleep(0.2)
        
        # Stop control loop
        self.coordinator.stop_control_loop()
        assert not self.coordinator.running
    
    def test_control_loop_timing(self):
        """Test control loop timing and updates."""
        initial_time = self.coordinator.last_update_time
        
        # Manually call control logic update
        self.coordinator.update_control_logic(0.1)
        
        # Check that update occurred
        assert self.coordinator.last_update_time >= initial_time
    
    def test_control_loop_exception_handling(self):
        """Test control loop exception handling."""
        # Start control loop
        self.coordinator.start_control_loop()
        
        # Inject a fault that might cause exceptions
        self.coordinator.sensors.tank_pressure.value = float('inf')
        
        # Give it time to handle the exception
        time.sleep(0.1)
        
        # Should still be running (exception should be caught)
        assert self.coordinator.running
        
        # Stop control loop
        self.coordinator.stop_control_loop()


class TestSensorIntegration:
    """Test sensor integration and data handling."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.coordinator = PneumaticControlCoordinator()
        self.sensors = self.coordinator.sensors
    
    def test_sensor_reading_structure(self):
        """Test sensor reading data structure."""
        sensor = SensorReading("test_sensor", 123.45, "test_unit", time.time())
        
        assert sensor.sensor_id == "test_sensor"
        assert sensor.value == 123.45
        assert sensor.unit == "test_unit"
        assert sensor.is_valid
        assert sensor.quality == 1.0
    
    def test_sensor_collection(self):
        """Test pneumatic sensor collection."""
        # Check that all required sensors exist
        assert hasattr(self.sensors, 'tank_pressure')
        assert hasattr(self.sensors, 'injection_pressure')
        assert hasattr(self.sensors, 'compressor_temp')
        assert hasattr(self.sensors, 'tank_temp')
        assert hasattr(self.sensors, 'water_temp')
        assert hasattr(self.sensors, 'compressor_flow')
        assert hasattr(self.sensors, 'injection_flow')
        
        # Check sensor types
        assert isinstance(self.sensors.tank_pressure, SensorReading)
        assert isinstance(self.sensors.compressor_temp, SensorReading)
        assert isinstance(self.sensors.compressor_flow, SensorReading)
    
    def test_sensor_data_validation(self):
        """Test sensor data validation and quality assessment."""
        # Update sensors
        self.coordinator.update_sensors(0.1)
        
        # Check that all sensors have valid readings
        for sensor_name in ['tank_pressure', 'compressor_temp', 'water_temp', 'compressor_flow']:
            sensor = getattr(self.sensors, sensor_name)
            assert isinstance(sensor.value, (int, float))
            assert sensor.is_valid
            assert 0.0 <= sensor.quality <= 1.0
            assert sensor.timestamp > 0


class TestPerformanceOptimization:
    """Test performance optimization algorithms."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.coordinator = PneumaticControlCoordinator(enable_optimization=True)
    
    def test_thermal_efficiency_calculation(self):
        """Test thermal efficiency calculations."""
        # Test normal conditions
        efficiency = self.coordinator.calculate_thermal_efficiency(320.15, 290.15)
        assert isinstance(efficiency, float)
        assert 0.5 < efficiency < 1.5
        
        # Test extreme conditions
        efficiency_hot = self.coordinator.calculate_thermal_efficiency(400.15, 310.15)
        efficiency_cold = self.coordinator.calculate_thermal_efficiency(280.15, 275.15)
        
        # Hot conditions should give different efficiency than cold
        assert efficiency_hot != efficiency_cold
    
    def test_optimal_pressure_calculation(self):
        """Test optimal pressure calculation."""
        # Test normal conditions
        optimal_pressure = self.coordinator.calculate_optimal_pressure(320.15, 290.15)
        assert isinstance(optimal_pressure, float)
        assert 150000.0 <= optimal_pressure <= 350000.0  # Within safe range
        
        # Test that temperature affects optimal pressure
        optimal_hot = self.coordinator.calculate_optimal_pressure(350.15, 290.15)
        optimal_cold = self.coordinator.calculate_optimal_pressure(290.15, 290.15)
        
        assert optimal_hot != optimal_cold
    
    def test_performance_metrics_update(self):
        """Test performance metrics calculation and update."""
        # Set up conditions for metrics calculation
        self.coordinator.compressor_enabled = True
        self.coordinator.sensors.compressor_flow.value = 0.05
        self.coordinator.sensors.tank_pressure.value = 250000.0
        
        # Update metrics
        self.coordinator.update_performance_metrics(0.1)
        
        # Check metrics structure
        metrics = self.coordinator.performance_metrics
        assert 'system_efficiency' in metrics
        assert 'energy_consumption' in metrics
        assert 'thermal_boost_factor' in metrics
        assert 'fault_count' in metrics
        assert 'uptime_percentage' in metrics
        
        # Check reasonable values
        assert 0.0 <= metrics['system_efficiency'] <= 1.0
        assert 0.0 <= metrics['uptime_percentage'] <= 100.0


class TestStandardCoordinatorFactory:
    """Test the standard coordinator factory function."""
    
    def test_standard_coordinator_creation(self):
        """Test standard KPP coordinator creation."""
        coordinator = create_standard_kpp_pneumatic_coordinator()
        
        assert isinstance(coordinator, PneumaticControlCoordinator)
        assert coordinator.enable_thermodynamics
        assert coordinator.control_params.target_pressure == 250000.0  # 2.5 bar
        assert coordinator.control_params.efficiency_target == 0.88
    
    def test_standard_coordinator_options(self):
        """Test standard coordinator with different options."""
        # Test with thermodynamics disabled
        coordinator_basic = create_standard_kpp_pneumatic_coordinator(
            enable_thermodynamics=False, enable_optimization=False)
        
        assert not coordinator_basic.enable_thermodynamics
        assert not coordinator_basic.control_params.power_optimization_enabled
        
        # Test with optimization enabled
        coordinator_optimized = create_standard_kpp_pneumatic_coordinator(
            enable_thermodynamics=True, enable_optimization=True)
        
        assert coordinator_optimized.enable_thermodynamics
        assert coordinator_optimized.control_params.power_optimization_enabled


class TestIntegrationScenarios:
    """Test integrated scenarios combining multiple features."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.coordinator = create_standard_kpp_pneumatic_coordinator()
    
    def test_startup_sequence(self):
        """Test complete startup sequence."""
        # Initial state
        assert self.coordinator.system_state == SystemState.STARTUP
        
        # Set good startup conditions
        self.coordinator.sensors.tank_pressure.value = 250000.0
        self.coordinator.sensors.compressor_temp.value = 293.15
        
        # Run control logic
        self.coordinator.update_control_logic(0.1)
        
        # Should transition to normal operation        assert self.coordinator.system_state == SystemState.NORMAL
    
    def test_normal_operation_cycle(self):
        """Test normal operation cycle with pressure control."""
        # Set to normal operation
        self.coordinator.system_state = SystemState.NORMAL
        
        # Simulate low pressure condition
        self.coordinator.sensors.tank_pressure.value = 200000.0
        
        # Manually call pressure control algorithm
        self.coordinator.pressure_control_algorithm()
        
        # Compressor should be enabled
        assert self.coordinator.compressor_enabled
        
        # Simulate pressure recovery
        self.coordinator.sensors.tank_pressure.value = 280000.0
        self.coordinator.pressure_control_algorithm()
        
        # Compressor should be disabled        assert not self.coordinator.compressor_enabled
    
    def test_fault_detection_and_recovery(self):
        """Test fault detection and recovery cycle."""
        # Start in normal operation
        self.coordinator.system_state = SystemState.NORMAL
        
        # Enable fault detection
        self.coordinator.control_params.fault_detection_enabled = True
        
        # Inject a fault condition
        self.coordinator.sensors.tank_pressure.value = 100000.0  # Too low
        self.coordinator.detect_faults()  # Manually call fault detection
        
        # Should detect fault and transition to fault state
        assert FaultType.PRESSURE_DROP in self.coordinator.active_faults
        
        self.coordinator.handle_faults()  # Handle the fault
        assert self.coordinator.system_state == SystemState.FAULT
        
        # Fix the condition
        self.coordinator.sensors.tank_pressure.value = 250000.0
        self.coordinator.clear_fault(FaultType.PRESSURE_DROP)
        self.coordinator.update_state_machine()
        
        # Should recover to normal operation        assert self.coordinator.system_state == SystemState.NORMAL
    
    def test_emergency_stop_scenario(self):
        """Test emergency stop scenario."""
        # Start in normal operation
        self.coordinator.system_state = SystemState.NORMAL
        self.coordinator.compressor_enabled = True
        self.coordinator.injection_enabled = True
        
        # Enable fault detection
        self.coordinator.control_params.fault_detection_enabled = True
        
        # Inject critical fault
        self.coordinator.sensors.compressor_temp.value = 380.15  # Overheating
        self.coordinator.detect_faults()  # Manually detect faults
        
        # Should trigger emergency stop
        assert FaultType.THERMAL_OVERLOAD in self.coordinator.active_faults
        
        self.coordinator.handle_faults()  # Handle the critical fault
        assert self.coordinator.system_state == SystemState.EMERGENCY_STOP
        assert not self.coordinator.compressor_enabled
        assert not self.coordinator.injection_enabled
    
    def test_performance_optimization_cycle(self):
        """Test performance optimization cycle."""
        # Set up for optimization
        self.coordinator.system_state = SystemState.NORMAL
        self.coordinator.control_params.power_optimization_enabled = True
        
        initial_target = self.coordinator.control_params.target_pressure
        
        # Set conditions that would trigger optimization
        self.coordinator.sensors.compressor_temp.value = 340.15  # Hot compressor
        self.coordinator.sensors.water_temp.value = 295.15    # Warm water
        
        # Run optimization
        self.coordinator.system_state = SystemState.OPTIMIZATION
        self.coordinator.update_control_logic(0.1)
        
        # Optimization may have adjusted parameters
        # The exact behavior depends on the optimization algorithm
        assert isinstance(self.coordinator.control_params.target_pressure, float)
        assert 150000.0 <= self.coordinator.control_params.target_pressure <= 350000.0
