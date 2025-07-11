import time
import pytest
import numpy as np
from simulation.grid_services.grid_services_coordinator import GridServicesCoordinator
from simulation.grid_services.storage.battery_storage_system import BatteryStorageSystem
from simulation.grid_services.demand_response.load_curtailment_controller import LoadCurtailmentController
from simulation.grid_services.economic.economic_optimizer import EconomicOptimizer

class TestPhase4Performance:
    @pytest.fixture
    def setup_grid_services(self):
        coordinator = GridServicesCoordinator()
        battery_system = BatteryStorageSystem()
        load_controller = LoadCurtailmentController()
        economic_optimizer = EconomicOptimizer()
        
        coordinator.register_service(battery_system)
        coordinator.register_service(load_controller)
        coordinator.register_service(economic_optimizer)
        
        return {
            'coordinator': coordinator,
            'battery_system': battery_system,
            'load_controller': load_controller,
            'economic_optimizer': economic_optimizer
        }

    @pytest.fixture(autouse=True)
    def cleanup_services(self, setup_grid_services):
        """Cleanup fixture that runs after each test"""
        yield
        coordinator = setup_grid_services['coordinator']
        coordinator.disable()
        coordinator.reset()

    def test_battery_storage_response_time(self, setup_grid_services):
        """Test battery storage system response time to power requests"""
        battery = setup_grid_services['battery_system']
        
        # Warm up the system
        battery.request_power_output(100)
        time.sleep(0.1)
        
        # Measure multiple response times
        response_times = []
        for _ in range(5):
            start_time = time.time()
            battery.request_power_output(1000)  # Request 1MW output
            response_times.append(time.time() - start_time)
            time.sleep(0.1)  # Wait between requests
        
        avg_response_time = np.mean(response_times)
        max_response_time = np.max(response_times)
        
        assert avg_response_time < 0.25, f"Average battery response time {avg_response_time}s exceeds 250ms threshold"
        assert max_response_time < 0.5, f"Maximum battery response time {max_response_time}s exceeds 500ms threshold"
        
    def test_load_curtailment_efficiency(self, setup_grid_services):
        """Test load curtailment controller efficiency"""
        controller = setup_grid_services['load_controller']
        
        # Test multiple curtailment scenarios
        efficiencies = []
        test_scenarios = [
            (2000, 500),  # High load, moderate reduction
            (1500, 300),  # Medium load, small reduction
            (3000, 1000), # High load, large reduction
        ]
        
        for start_load, demand_reduction in test_scenarios:
            controller.set_current_load(start_load)
            achieved_reduction = controller.request_load_reduction(demand_reduction)
            efficiency = (achieved_reduction / demand_reduction) * 100
            efficiencies.append(efficiency)
            time.sleep(0.1)  # Wait between scenarios
        
        avg_efficiency = np.mean(efficiencies)
        min_efficiency = np.min(efficiencies)
        
        assert avg_efficiency >= 90, f"Average load curtailment efficiency {avg_efficiency}% below 90% threshold"
        assert min_efficiency >= 85, f"Minimum load curtailment efficiency {min_efficiency}% below 85% threshold"
        
    def test_economic_optimizer_calculation_speed(self, setup_grid_services):
        """Test economic optimization calculation performance"""
        optimizer = setup_grid_services['economic_optimizer']
        
        # Test multiple optimization scenarios
        calculation_times = []
        test_scenarios = [
            (50, 1500),   # Normal conditions
            (100, 2000),  # High price, high demand
            (30, 1000),   # Low price, low demand
        ]
        
        for market_price, demand_forecast in test_scenarios:
            start_time = time.time()
            optimizer.calculate_optimal_bid(market_price=market_price, demand_forecast=demand_forecast)
            calculation_times.append(time.time() - start_time)
            time.sleep(0.1)  # Wait between calculations
        
        avg_calculation_time = np.mean(calculation_times)
        max_calculation_time = np.max(calculation_times)
        
        assert avg_calculation_time < 0.75, f"Average economic optimization took {avg_calculation_time}s, exceeds 750ms threshold"
        assert max_calculation_time < 1.0, f"Maximum economic optimization took {max_calculation_time}s, exceeds 1s threshold"
        
    def test_coordinator_service_integration(self, setup_grid_services):
        """Test overall grid services coordination performance"""
        coordinator = setup_grid_services['coordinator']
        
        # Enable coordinator
        coordinator.enable()
        
        # Test multiple grid events
        processing_times = []
        test_events = [
            {'frequency_deviation': -0.1, 'voltage_deviation': 0.05, 'market_price': 45.0},
            {'frequency_deviation': 0.15, 'voltage_deviation': -0.03, 'market_price': 55.0},
            {'frequency_deviation': -0.05, 'voltage_deviation': 0.02, 'market_price': 40.0},
        ]
        
        for event in test_events:
            start_time = time.time()
            coordinator.process_grid_event(event)
            processing_times.append(time.time() - start_time)
            time.sleep(0.2)  # Wait between events
        
        avg_processing_time = np.mean(processing_times)
        max_processing_time = np.max(processing_times)
        
        assert avg_processing_time < 1.5, f"Average grid services coordination took {avg_processing_time}s, exceeds 1.5s threshold"
        assert max_processing_time < 2.0, f"Maximum grid services coordination took {max_processing_time}s, exceeds 2s threshold"

    def test_concurrent_service_operations(self, setup_grid_services):
        """Test performance under concurrent service operations"""
        coordinator = setup_grid_services['coordinator']
        
        # Enable coordinator
        coordinator.enable()
        
        # Simulate multiple concurrent grid events with varying complexity
        event_batches = [
            [
                {'frequency_deviation': -0.1, 'timestamp': time.time()},
                {'voltage_deviation': 0.05, 'timestamp': time.time()},
            ],
            [
                {'market_price': 45.0, 'timestamp': time.time()},
                {'demand_spike': True, 'timestamp': time.time()},
                {'frequency_deviation': 0.08, 'timestamp': time.time()},
            ],
            [
                {'voltage_deviation': -0.03, 'timestamp': time.time()},
                {'market_price': 55.0, 'timestamp': time.time()},
                {'frequency_deviation': -0.12, 'timestamp': time.time()},
                {'demand_spike': False, 'timestamp': time.time()},
            ]
        ]
        
        batch_times = []
        for events in event_batches:
            start_time = time.time()
            for event in events:
                coordinator.process_grid_event(event)
            batch_times.append((time.time() - start_time) / len(events))
            time.sleep(0.3)  # Wait between batches
        
        avg_time = np.mean(batch_times)
        max_time = np.max(batch_times)
        
        assert avg_time < 0.5, f"Average concurrent operation time {avg_time}s exceeds 500ms threshold"
        assert max_time < 0.75, f"Maximum concurrent operation time {max_time}s exceeds 750ms threshold"

if __name__ == '__main__':
    pytest.main([__file__, '-v']) 