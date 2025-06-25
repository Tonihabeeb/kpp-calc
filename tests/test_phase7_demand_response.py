"""
Unit tests for Phase 7 Week 3: Demand Response Services

Tests for load curtailment, peak shaving, and load forecasting services
in the KPP grid services system.
"""

import pytest
import time
import math
from unittest.mock import Mock, patch

# Import the demand response services
from simulation.grid_services.demand_response.load_curtailment_controller import (
    LoadCurtailmentController, LoadCurtailmentConfig, CurtailmentType, CurtailmentPriority,
    create_standard_load_curtailment_controller
)
from simulation.grid_services.demand_response.peak_shaving_controller import (
    PeakShavingController, PeakShavingConfig, PeakEvent,
    create_standard_peak_shaving_controller
)
from simulation.grid_services.demand_response.load_forecaster import (
    LoadForecaster, LoadForecastConfig, ForecastPoint,
    create_standard_load_forecaster
)
from simulation.grid_services.grid_services_coordinator import GridServicesCoordinator, GridConditions


class TestLoadCurtailmentController:
    """Test cases for Load Curtailment Controller"""
    
    def test_initialization(self):
        """Test controller initialization"""
        controller = LoadCurtailmentController()
        assert controller.config.max_curtailment_percent == 0.30
        assert controller.config.response_time_s == 60.0
        assert not controller.curtailment_active
        assert controller.total_curtailment_energy == 0.0
        
    def test_factory_function(self):
        """Test factory function creates working controller"""
        controller = create_standard_load_curtailment_controller()
        assert isinstance(controller, LoadCurtailmentController)
        assert controller.config.max_curtailment_percent == 0.30
          def test_emergency_curtailment_activation(self):
        """Test emergency curtailment activation"""
        controller = LoadCurtailmentController()
        
        # Create emergency conditions
        emergency_conditions = {
            'grid_frequency_low': True,
            'grid_frequency_high': False,
            'voltage_low': False,
            'voltage_high': False,
            'system_overload': False
        }
        
        grid_conditions = {
            'emergency_conditions': emergency_conditions,
            'electricity_price': 100.0,
            'utility_signal': 0.0,
            'timestamp': time.time()
        }
        
        response = controller.update(10.0, 1.0, grid_conditions)  # current_load=10.0 MW
        
        assert response['curtailment_active']
        assert response['curtailment_type'] == CurtailmentType.EMERGENCY.value
        assert response['curtailment_amount'] > 0
        assert controller.curtailment_active
        
    def test_economic_curtailment_activation(self):
        """Test economic curtailment activation"""
        controller = LoadCurtailmentController()
        
        # No emergency conditions, high electricity price
        emergency_conditions = {
            'grid_frequency_low': False,
            'grid_frequency_high': False,
            'voltage_low': False,
            'voltage_high': False,
            'system_overload': False
        }
        
        data = {
            'current_load': 10.0,  # MW
            'emergency_conditions': emergency_conditions,
            'electricity_price': 150.0,  # High price triggers economic curtailment
            'utility_signal': 0.0,
            'timestamp': time.time()
        }
        
        response = controller.update(data, 1.0)
        
        assert response['curtailment_active']
        assert response['curtailment_type'] == CurtailmentType.ECONOMIC.value
        assert response['curtailment_amount'] > 0
        
    def test_curtailment_limits(self):
        """Test curtailment respects maximum limits"""
        config = LoadCurtailmentConfig(max_curtailment_percent=0.20)  # 20% max
        controller = LoadCurtailmentController(config)
        
        emergency_conditions = {
            'grid_frequency_low': True,
            'grid_frequency_high': False,
            'voltage_low': False,
            'voltage_high': False,
            'system_overload': True  # Multiple emergency conditions
        }
        
        data = {
            'current_load': 10.0,  # MW
            'emergency_conditions': emergency_conditions,
            'electricity_price': 100.0,
            'utility_signal': 0.0,
            'timestamp': time.time()
        }
        
        response = controller.update(data, 1.0)
        
        assert response['curtailment_active']
        assert response['curtailment_amount'] <= 10.0 * 0.20  # Should not exceed 20% of 10MW
        
    def test_curtailment_event_tracking(self):
        """Test curtailment event tracking and limits"""
        controller = LoadCurtailmentController()
        
        emergency_conditions = {
            'grid_frequency_low': True,
            'grid_frequency_high': False,
            'voltage_low': False,
            'voltage_high': False,
            'system_overload': False
        }
        
        data = {
            'current_load': 10.0,
            'emergency_conditions': emergency_conditions,
            'electricity_price': 100.0,
            'utility_signal': 0.0,
            'timestamp': time.time()
        }
        
        # First event should activate
        response1 = controller.update(data, 1.0)
        assert response1['curtailment_active']
        assert controller.events_today == 1
        
        # Complete the event
        controller.curtailment_active = False
        controller.current_event = None
        
        # Wait sufficient time and trigger another event
        time.sleep(0.1)  # Short wait for testing
        data['timestamp'] = time.time()
        response2 = controller.update(data, 1.0)
        
        # Should still activate (within daily limits)
        assert response2['curtailment_active']
        assert controller.events_today == 2
        
    def test_no_curtailment_normal_conditions(self):
        """Test no curtailment under normal conditions"""
        controller = LoadCurtailmentController()
        
        emergency_conditions = {
            'grid_frequency_low': False,
            'grid_frequency_high': False,
            'voltage_low': False,
            'voltage_high': False,
            'system_overload': False
        }
        
        data = {
            'current_load': 10.0,
            'emergency_conditions': emergency_conditions,
            'electricity_price': 50.0,  # Normal price
            'utility_signal': 0.0,
            'timestamp': time.time()
        }
        
        response = controller.update(data, 1.0)
        
        assert not response['curtailment_active']
        assert response['curtailment_amount'] == 0.0
        assert not controller.curtailment_active


class TestPeakShavingController:
    """Test cases for Peak Shaving Controller"""
    
    def test_initialization(self):
        """Test controller initialization"""
        controller = PeakShavingController()
        assert controller.config.peak_threshold_percent == 0.90
        assert controller.config.shaving_target_percent == 0.85
        assert not controller.shaving_active
        assert controller.historical_peak == 0.0
        
    def test_factory_function(self):
        """Test factory function creates working controller"""
        controller = create_standard_peak_shaving_controller()
        assert isinstance(controller, PeakShavingController)
        assert controller.config.peak_threshold_percent == 0.90
        
    def test_peak_detection_and_shaving(self):
        """Test peak detection and shaving activation"""
        controller = PeakShavingController()
        
        # Set historical peak
        controller.historical_peak = 10.0  # MW
        controller.peak_threshold = controller.historical_peak * controller.config.peak_threshold_percent
        
        # Current demand exceeds threshold
        data = {
            'current_demand': 9.5,  # MW (above 90% of 10MW = 9MW threshold)
            'current_generation': 5.0,
            'load_forecast': [{'timestamp': time.time() + 3600, 'predicted_load': 9.8, 'confidence': 0.9}],
            'electricity_price': 80.0,
            'timestamp': time.time()
        }
        
        response = controller.update(data, 1.0)
        
        assert response['shaving_active']
        assert response['generation_boost'] > 0 or response['load_reduction'] > 0
        assert controller.shaving_active
        
    def test_peak_prediction_from_forecast(self):
        """Test peak prediction from load forecast"""
        controller = PeakShavingController()
        controller.historical_peak = 10.0
        controller.peak_threshold = 9.0
        
        # Forecast shows upcoming peak
        future_time = time.time() + 1800  # 30 minutes from now
        data = {
            'current_demand': 7.0,  # Below threshold now
            'current_generation': 5.0,
            'load_forecast': [
                {'timestamp': future_time, 'predicted_load': 9.5, 'confidence': 0.95}  # Above threshold
            ],
            'electricity_price': 80.0,
            'timestamp': time.time()
        }
        
        response = controller.update(data, 1.0)
        
        # Should detect predicted peak
        assert len(controller.predicted_peaks) > 0
        predicted_peak = controller.predicted_peaks[0]
        assert predicted_peak.predicted_peak == 9.5
        assert predicted_peak.confidence == 0.95
        
    def test_cost_savings_calculation(self):
        """Test cost savings calculation for peak shaving"""
        controller = PeakShavingController()
        controller.historical_peak = 10.0
        controller.peak_threshold = 9.0
        
        data = {
            'current_demand': 9.5,
            'current_generation': 5.0,
            'load_forecast': [],
            'electricity_price': 80.0,
            'timestamp': time.time()
        }
        
        response = controller.update(data, 1.0)
        
        if response['shaving_active']:
            assert 'cost_savings' in response
            assert response['cost_savings'] >= 0
            
    def test_generation_and_load_coordination(self):
        """Test coordination between generation increase and load reduction"""
        config = PeakShavingConfig(
            enable_generation_increase=True,
            enable_load_reduction=True,
            generation_ramp_rate=0.15,  # 15% per minute
            load_reduction_rate=0.10    # 10% per minute
        )
        controller = PeakShavingController(config)
        controller.historical_peak = 10.0
        controller.peak_threshold = 9.0
        
        data = {
            'current_demand': 9.5,
            'current_generation': 5.0,
            'load_forecast': [],
            'electricity_price': 80.0,
            'timestamp': time.time()
        }
        
        response = controller.update(data, 1.0)
        
        if response['shaving_active']:
            # Should use both generation increase and load reduction
            total_response = response['generation_boost'] + response['load_reduction']
            assert total_response > 0
            
    def test_no_shaving_below_threshold(self):
        """Test no shaving activation below threshold"""
        controller = PeakShavingController()
        controller.historical_peak = 10.0
        controller.peak_threshold = 9.0
        
        data = {
            'current_demand': 8.0,  # Below threshold
            'current_generation': 5.0,
            'load_forecast': [],
            'electricity_price': 80.0,
            'timestamp': time.time()
        }
        
        response = controller.update(data, 1.0)
        
        assert not response['shaving_active']
        assert response['generation_boost'] == 0.0
        assert response['load_reduction'] == 0.0


class TestLoadForecaster:
    """Test cases for Load Forecaster"""
    
    def test_initialization(self):
        """Test forecaster initialization"""
        forecaster = LoadForecaster()
        assert forecaster.config.forecast_horizon_hours == 24
        assert forecaster.config.accuracy_target_mape == 5.0
        assert len(forecaster.current_forecast) == 0
        assert forecaster.total_forecasts == 0
        
    def test_factory_function(self):
        """Test factory function creates working forecaster"""
        forecaster = create_standard_load_forecaster()
        assert isinstance(forecaster, LoadForecaster)
        assert forecaster.config.forecast_horizon_hours == 24
        
    def test_load_data_update(self):
        """Test load data update and storage"""
        forecaster = LoadForecaster()
        
        data = {
            'current_load': 8.5,
            'timestamp': time.time(),
            'temperature': 22.0,
            'hour_of_day': 14.5,  # 2:30 PM
            'day_of_week': 2      # Wednesday
        }
        
        forecaster.update(data, 1.0)
        
        assert len(forecaster.load_history) == 1
        assert forecaster.load_history[0]['load'] == 8.5
        assert forecaster.load_history[0]['temperature'] == 22.0
        
    def test_forecast_generation(self):
        """Test forecast generation with sufficient historical data"""
        forecaster = LoadForecaster()
        
        # Add some historical data
        base_time = time.time()
        for i in range(100):  # 100 data points
            data = {
                'current_load': 8.0 + 2.0 * math.sin(i * 0.1),  # Sinusoidal pattern
                'timestamp': base_time + i * 3600,  # Hourly data
                'temperature': 20.0 + 5.0 * math.sin(i * 0.05),
                'hour_of_day': (i % 24),
                'day_of_week': (i // 24) % 7
            }
            forecaster.update(data, 1.0)
        
        # Generate forecast
        forecast = forecaster.get_forecast(horizon_hours=6)
        
        assert len(forecast) == 6
        for point in forecast:
            assert isinstance(point, ForecastPoint)
            assert point.predicted_load > 0
            assert 0.0 <= point.confidence <= 1.0
            
    def test_forecast_accuracy_tracking(self):
        """Test forecast accuracy tracking"""
        forecaster = LoadForecaster()
        
        # Create a simple forecast point
        forecast_point = ForecastPoint(
            timestamp=time.time(),
            predicted_load=10.0,
            confidence=0.9,
            method='test'
        )
        
        # Update with actual value
        forecast_point.update_actual(9.5)
        
        assert forecast_point.actual_load == 9.5
        assert forecast_point.error == 5.0  # 5% error
        
    def test_pattern_analysis(self):
        """Test historical pattern analysis"""
        forecaster = LoadForecaster()
        
        # Add regular pattern data
        base_time = time.time()
        for day in range(7):  # One week of data
            for hour in range(24):
                load = 5.0 + 3.0 * math.sin((hour - 6) * math.pi / 12)  # Daily pattern
                data = {
                    'current_load': load,
                    'timestamp': base_time + day * 86400 + hour * 3600,
                    'temperature': 20.0,
                    'hour_of_day': hour,
                    'day_of_week': day
                }
                forecaster.update(data, 1.0)
        
        # Should detect patterns
        forecaster._analyze_patterns()
        
        assert len(forecaster.hourly_patterns) > 0
        assert len(forecaster.weekday_patterns) > 0
        
    def test_mape_calculation(self):
        """Test MAPE (Mean Absolute Percentage Error) calculation"""
        forecaster = LoadForecaster()
        
        # Add some forecast accuracy data
        errors = [2.0, 3.0, 1.5, 4.0, 2.5]  # Percentage errors
        for error in errors:
            forecaster.forecast_accuracy_history.append(error)
        
        mape = forecaster.get_forecast_accuracy()
        expected_mape = sum(errors) / len(errors)
        
        assert abs(mape - expected_mape) < 0.01
        
    def test_forecast_confidence_adjustment(self):
        """Test forecast confidence adjustment based on accuracy"""
        forecaster = LoadForecaster()
        
        # Simulate poor accuracy history
        for _ in range(10):
            forecaster.forecast_accuracy_history.append(10.0)  # 10% error
        
        # Generate forecast with adjusted confidence
        data = {
            'current_load': 8.0,
            'timestamp': time.time(),
            'temperature': 20.0,
            'hour_of_day': 12,
            'day_of_week': 3
        }
        
        forecaster.update(data, 1.0)
        
        # Should reduce confidence due to poor accuracy
        forecast = forecaster.get_forecast(horizon_hours=1)
        if forecast:
            assert forecast[0].confidence < 0.9  # Lower confidence


class TestDemandResponseIntegration:
    """Test integration of demand response services with grid services coordinator"""
    
    def test_demand_response_integration(self):
        """Test demand response services integration in coordinator"""
        from simulation.grid_services.grid_services_coordinator import create_standard_grid_services_coordinator
        
        coordinator = create_standard_grid_services_coordinator()
        
        # Check that demand response services are initialized
        assert hasattr(coordinator, 'load_curtailment_controller')
        assert hasattr(coordinator, 'peak_shaving_controller')
        assert hasattr(coordinator, 'load_forecaster')
        
    def test_coordinator_status_includes_demand_response(self):
        """Test coordinator status includes demand response services"""
        from simulation.grid_services.grid_services_coordinator import create_standard_grid_services_coordinator
        
        coordinator = create_standard_grid_services_coordinator()
        status = coordinator.get_service_status()
        
        assert 'load_curtailment' in status
        assert 'peak_shaving' in status
        assert 'load_forecaster' in status
        
    def test_demand_response_service_commands(self):
        """Test demand response service command generation"""
        from simulation.grid_services.grid_services_coordinator import (
            create_standard_grid_services_coordinator, GridConditions
        )
        
        coordinator = create_standard_grid_services_coordinator()
        
        # Create emergency conditions that should trigger load curtailment
        grid_conditions = GridConditions(
            frequency=59.4,  # Low frequency emergency
            voltage=480.0,
            active_power=15.0,  # High load
            reactive_power=2.0,
            grid_connected=True,
            agc_signal=0.0,
            timestamp=time.time()
        )
        
        response = coordinator.update(grid_conditions, 1.0, rated_power=20.0)
        
        # Should have some demand response activity
        assert 'active_services' in response
        # Emergency conditions should trigger some response
        assert response['total_power_command'] != 0.0 or len(coordinator.service_commands) > 0


if __name__ == '__main__':
    # Run the tests
    pytest.main([__file__, '-v'])
