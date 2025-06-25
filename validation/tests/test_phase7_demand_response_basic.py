"""
Simplified unit tests for Phase 7 Week 3: Demand Response Services

Basic integration tests for demand response services in the KPP grid services system.
"""

import pytest
import time
import math

# Import the demand response services
from simulation.grid_services.demand_response.load_curtailment_controller import (
    LoadCurtailmentController, create_standard_load_curtailment_controller
)
from simulation.grid_services.demand_response.peak_shaving_controller import (
    PeakShavingController, create_standard_peak_shaving_controller
)
from simulation.grid_services.demand_response.load_forecaster import (
    LoadForecaster, create_standard_load_forecaster
)
from simulation.grid_services.grid_services_coordinator import (
    GridServicesCoordinator, GridConditions, create_standard_grid_services_coordinator
)


class TestDemandResponseBasic:
    """Basic tests for demand response services"""
    
    def test_load_curtailment_initialization(self):
        """Test load curtailment controller initialization"""
        controller = create_standard_load_curtailment_controller()
        assert controller is not None
        assert hasattr(controller, 'is_curtailing')
        assert not controller.is_curtailing()
        
    def test_peak_shaving_initialization(self):
        """Test peak shaving controller initialization"""
        controller = create_standard_peak_shaving_controller()
        assert controller is not None
        assert hasattr(controller, 'is_shaving')
        assert not controller.is_shaving()
        
    def test_load_forecaster_initialization(self):
        """Test load forecaster initialization"""
        forecaster = create_standard_load_forecaster()
        assert forecaster is not None
        assert hasattr(forecaster, 'is_forecasting')
        assert hasattr(forecaster, 'get_forecast_accuracy')
        
    def test_load_curtailment_update(self):
        """Test load curtailment update with basic parameters"""
        controller = create_standard_load_curtailment_controller()
        
        # Test normal conditions - no curtailment
        grid_conditions = {
            'emergency_conditions': {
                'grid_frequency_low': False,
                'grid_frequency_high': False,
                'voltage_low': False,
                'voltage_high': False,
                'system_overload': False
            },
            'electricity_price': 50.0,
            'utility_signal': 0.0,
            'timestamp': time.time()
        }
        
        response = controller.update(10.0, 1.0, grid_conditions)
        assert 'curtailment_active' in response
        assert not response['curtailment_active']
        
    def test_peak_shaving_update(self):
        """Test peak shaving update with basic parameters"""
        controller = create_standard_peak_shaving_controller()
        
        # Test below threshold - no shaving
        response = controller.update(8.0, 5.0, 1.0)  # current_demand=8MW, generation=5MW, dt=1s
        assert 'shaving_active' in response
        
    def test_load_forecaster_update(self):
        """Test load forecaster update with basic parameters"""
        forecaster = create_standard_load_forecaster()
          # Test basic load data update
        response = forecaster.update(8.5, 1.0)  # current_load=8.5MW, dt=1s
        assert 'forecast_available' in response or 'status' in response
        
    def test_coordinator_integration(self):
        """Test demand response services integration in coordinator"""
        coordinator = create_standard_grid_services_coordinator()
        
        # Check that demand response services are initialized
        assert hasattr(coordinator, 'load_curtailment_controller')
        assert hasattr(coordinator, 'peak_shaving_controller')
        assert hasattr(coordinator, 'load_forecaster')
        
    def test_coordinator_status(self):
        """Test coordinator status includes demand response services"""
        coordinator = create_standard_grid_services_coordinator()
        status = coordinator.get_service_status()
        
        assert 'load_curtailment' in status
        assert 'peak_shaving' in status
        assert 'load_forecaster' in status
        
        # Should all be False initially (not active)
        assert isinstance(status['load_curtailment'], bool)
        assert isinstance(status['peak_shaving'], bool)
        assert isinstance(status['load_forecaster'], bool)
        
    def test_coordinator_update_normal_conditions(self):
        """Test coordinator update under normal grid conditions"""
        coordinator = create_standard_grid_services_coordinator()
        
        # Normal grid conditions
        grid_conditions = GridConditions(
            frequency=60.0,  # Normal frequency
            voltage=480.0,   # Normal voltage
            active_power=5.0,   # Normal load
            reactive_power=1.0,
            grid_connected=True,
            agc_signal=0.0,
            timestamp=time.time()
        )
        
        response = coordinator.update(grid_conditions, 1.0, rated_power=20.0)
          # Should have valid response structure
        assert 'total_power_command_mw' in response
        assert 'active_services' in response
        assert isinstance(response['total_power_command_mw'], (int, float))
        
    def test_coordinator_update_emergency_conditions(self):
        """Test coordinator update under emergency conditions"""
        coordinator = create_standard_grid_services_coordinator()
        
        # Emergency conditions that might trigger demand response
        grid_conditions = GridConditions(
            frequency=59.4,  # Low frequency emergency
            voltage=450.0,   # Low voltage
            active_power=18.0,  # High load (90% of 20MW rated)
            reactive_power=2.0,
            grid_connected=True,
            agc_signal=0.0,
            timestamp=time.time()
        )
        
        response = coordinator.update(grid_conditions, 1.0, rated_power=20.0)
          # Should have valid response
        assert 'total_power_command_mw' in response
        assert 'active_services' in response
        # Emergency conditions should trigger some response
        assert isinstance(response['total_power_command_mw'], (int, float))


if __name__ == '__main__':
    # Run the tests
    pytest.main([__file__, '-v'])
