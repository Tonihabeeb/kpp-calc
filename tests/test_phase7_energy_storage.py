"""
Unit Tests for Energy Storage Services - Phase 7 Week 4

Tests for Battery Storage System and Grid Stabilization Controller functionality
including energy arbitrage, grid support, and stabilization services.
"""

import pytest
import time
from simulation.grid_services.storage.battery_storage_system import (
    BatteryStorageSystem, BatterySpecs, BatteryMode, create_battery_storage_system
)
from simulation.grid_services.storage.grid_stabilization_controller import (
    GridStabilizationController, StabilizationSpecs, StabilizationMode, create_grid_stabilization_controller
)


class TestBatteryStorageSystem:
    """Test battery storage system functionality"""
    
    def test_battery_initialization(self):
        """Test battery system initialization"""
        battery = create_battery_storage_system(capacity_kwh=500.0, max_power_kw=250.0)
        
        assert battery.specs.nominal_capacity_kwh == 500.0
        assert battery.specs.max_power_kw == 250.0
        assert battery.state.soc == 0.5  # 50% initial SOC
        assert battery.mode == BatteryMode.IDLE
        assert not battery.active
    
    def test_battery_start_stop(self):
        """Test battery service start and stop"""
        battery = create_battery_storage_system()
        
        # Test start
        battery.start_service()
        assert battery.active
        
        # Test stop
        battery.stop_service()
        assert not battery.active
        assert battery.mode == BatteryMode.IDLE
    
    def test_economic_arbitrage_charging(self):
        """Test economic arbitrage charging during low prices"""
        battery = create_battery_storage_system()
        battery.start_service()
        
        # Low electricity price - should charge
        grid_conditions = {
            'electricity_price': 40.0,  # Below charge threshold (50)
            'frequency': 50.0,
            'voltage': 1.0,
            'load_demand': 100.0
        }
        
        status = battery.update(dt=1.0, grid_conditions=grid_conditions)
        
        assert status['active']
        assert status['mode'] == BatteryMode.CHARGING.value
        assert status['power_setpoint_kw'] > 0  # Positive for charging
    
    def test_economic_arbitrage_discharging(self):
        """Test economic arbitrage discharging during high prices"""
        battery = create_battery_storage_system()
        battery.start_service()
        
        # High electricity price - should discharge
        grid_conditions = {
            'electricity_price': 90.0,  # Above discharge threshold (80)
            'frequency': 50.0,
            'voltage': 1.0,
            'load_demand': 100.0
        }
        
        status = battery.update(dt=1.0, grid_conditions=grid_conditions)
        
        assert status['active']
        assert status['mode'] == BatteryMode.DISCHARGING.value
        assert status['power_setpoint_kw'] < 0  # Negative for discharging
    
    def test_frequency_support(self):
        """Test frequency support operation"""
        battery = create_battery_storage_system()
        battery.start_service()
        
        # Under-frequency condition - should discharge to support
        grid_conditions = {
            'electricity_price': 60.0,  # Neutral price
            'frequency': 49.7,  # Under-frequency
            'voltage': 1.0,
            'load_demand': 100.0
        }
        
        status = battery.update(dt=1.0, grid_conditions=grid_conditions)
        
        assert status['active']
        assert status['mode'] == BatteryMode.STABILIZING.value
        assert status['power_setpoint_kw'] < 0  # Discharge to support frequency
    
    def test_soc_limits(self):
        """Test state of charge limits"""
        battery = create_battery_storage_system()
        battery.start_service()
        
        # Set SOC to maximum
        battery.state.soc = 0.95
        battery._update_available_capacity()
        
        # Try to charge at high SOC
        grid_conditions = {
            'electricity_price': 40.0,  # Low price (should charge)
            'frequency': 50.0,
            'voltage': 1.0,
            'load_demand': 100.0
        }
        
        status = battery.update(dt=1.0, grid_conditions=grid_conditions)
        
        # Should not charge significantly at high SOC
        assert abs(status['power_setpoint_kw']) < 10.0
    
    def test_emergency_discharge(self):
        """Test emergency discharge functionality"""
        battery = create_battery_storage_system()
        battery.start_service()
        
        # Emergency discharge
        success = battery.emergency_discharge(100.0)
        
        assert success
        assert battery.mode == BatteryMode.STABILIZING
        assert battery.power_setpoint < 0  # Discharging
    
    def test_performance_tracking(self):
        """Test performance metrics tracking"""
        battery = create_battery_storage_system()
        battery.start_service()
        
        # Simulate charging operation
        grid_conditions = {
            'electricity_price': 40.0,
            'frequency': 50.0,
            'voltage': 1.0,
            'load_demand': 100.0
        }
        
        # Run for several updates
        for _ in range(10):
            battery.update(dt=1.0, grid_conditions=grid_conditions)
        
        status = battery.get_status()
        
        assert status['operation_hours'] > 0
        assert status['total_energy_charged'] > 0
        assert 'total_revenue' in status


class TestGridStabilizationController:
    """Test grid stabilization controller functionality"""
    
    def test_stabilization_initialization(self):
        """Test grid stabilization controller initialization"""
        controller = create_grid_stabilization_controller(max_power_kw=250.0)
        
        assert controller.specs.max_power_kw == 250.0
        assert controller.mode == StabilizationMode.STANDBY
        assert not controller.active
    
    def test_stabilization_start_stop(self):
        """Test stabilization service start and stop"""
        controller = create_grid_stabilization_controller()
        
        # Test start
        controller.start_service()
        assert controller.active
        assert controller.mode == StabilizationMode.STANDBY
        
        # Test stop
        controller.stop_service()
        assert not controller.active
    
    def test_frequency_support_mode(self):
        """Test frequency support mode activation"""
        controller = create_grid_stabilization_controller()
        controller.start_service()
        
        grid_conditions = {
            'frequency': 49.8,  # Under-frequency
            'voltage': 1.0,
            'grid_connected': True,
            'rocof': 0.0
        }
        
        battery_status = {
            'active': True,
            'soc': 0.5,
            'health': 1.0,
            'available_energy_kwh': 200.0,
            'available_capacity_kwh': 200.0
        }
        
        result = controller.update(dt=1.0, grid_conditions=grid_conditions, battery_status=battery_status)
        
        assert result['active']
        assert result['mode'] == StabilizationMode.FREQUENCY_SUPPORT.value
        assert 'control_commands' in result
    
    def test_voltage_support_mode(self):
        """Test voltage support mode activation"""
        controller = create_grid_stabilization_controller()
        controller.start_service()
        
        grid_conditions = {
            'frequency': 50.0,  # Normal frequency
            'voltage': 0.9,  # Under-voltage
            'grid_connected': True,
            'rocof': 0.0
        }
        
        battery_status = {
            'active': True,
            'soc': 0.5,
            'health': 1.0,
            'available_energy_kwh': 200.0,
            'available_capacity_kwh': 200.0
        }
        
        result = controller.update(dt=1.0, grid_conditions=grid_conditions, battery_status=battery_status)
        
        assert result['active']
        assert result['mode'] == StabilizationMode.VOLTAGE_SUPPORT.value
    
    def test_emergency_mode(self):
        """Test emergency mode for severe disturbances"""
        controller = create_grid_stabilization_controller()
        controller.start_service()
        
        grid_conditions = {
            'frequency': 48.5,  # Severe under-frequency
            'voltage': 1.0,
            'grid_connected': True,
            'rocof': -2.5  # High ROCOF
        }
        
        battery_status = {
            'active': True,
            'soc': 0.5,
            'health': 1.0,
            'available_energy_kwh': 200.0,
            'available_capacity_kwh': 200.0
        }
        
        result = controller.update(dt=1.0, grid_conditions=grid_conditions, battery_status=battery_status)
        
        assert result['active']
        assert result['mode'] == StabilizationMode.EMERGENCY.value
    
    def test_black_start_capability(self):
        """Test black start functionality"""
        controller = create_grid_stabilization_controller()
        controller.start_service()
        
        # Grid disconnected
        grid_conditions = {
            'frequency': 0.0,
            'voltage': 0.0,
            'grid_connected': False,
            'rocof': 0.0
        }
        
        battery_status = {
            'active': True,
            'soc': 0.8,  # Good SOC for black start
            'health': 1.0,
            'available_energy_kwh': 300.0,
            'available_capacity_kwh': 100.0
        }
        
        result = controller.update(dt=1.0, grid_conditions=grid_conditions, battery_status=battery_status)
        
        assert result['active']
        assert result['mode'] == StabilizationMode.BLACK_START.value
        if 'control_commands' in result:
            assert result['control_commands']['black_start']
        
    def test_grid_forming_mode(self):
        """Test grid forming mode for islanded operation"""
        controller = create_grid_stabilization_controller()
        controller.start_service()
        
        # Set up conditions for grid forming (not black start)
        grid_conditions = {
            'frequency': 49.95,
            'voltage': 0.98,
            'grid_connected': False,  # Islanded
            'rocof': 0.1
        }
        
        battery_status = {
            'active': True,
            'soc': 0.7,
            'health': 1.0,
            'available_energy_kwh': 250.0,
            'available_capacity_kwh': 150.0
        }
        
        # Override the black start condition by setting grid forming directly
        controller.specs.black_start_capability = False  # Disable black start priority
        
        result = controller.update(dt=1.0, grid_conditions=grid_conditions, battery_status=battery_status)
        
        # Should be in grid forming mode when grid is disconnected and black start is disabled
        assert result['mode'] == StabilizationMode.GRID_FORMING.value
        assert controller.grid_forming_active
    
    def test_performance_tracking(self):
        """Test performance metrics tracking"""
        controller = create_grid_stabilization_controller()
        controller.start_service()
        
        # Simulate multiple events
        grid_conditions = {
            'frequency': 49.85,
            'voltage': 1.0,
            'grid_connected': True,
            'rocof': 0.0
        }
        
        battery_status = {
            'active': True,
            'soc': 0.5,
            'health': 1.0,
            'available_energy_kwh': 200.0,
            'available_capacity_kwh': 200.0
        }
        
        # Run for several updates to trigger events
        for _ in range(5):
            controller.update(dt=1.0, grid_conditions=grid_conditions, battery_status=battery_status)
        
        status = controller._get_status()
        
        assert status['frequency_events'] > 0
        assert status['service_availability'] > 0
        assert status['response_time_ms'] == 500.0
    
    def test_service_capability(self):
        """Test service capability information"""
        controller = create_grid_stabilization_controller()
        
        capability = controller.get_service_capability()
        
        assert capability['frequency_support']
        assert capability['voltage_support']
        assert capability['black_start']
        assert capability['grid_forming']
        assert capability['power_quality']
        assert capability['max_active_power_kw'] == 250.0
        assert capability['response_time_ms'] == 500.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
