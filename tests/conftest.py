"""
Pytest Configuration for KPP Simulator Tests
Sets up test infrastructure, fixtures, and utilities
"""

import pytest
import logging
import tempfile
import os
import sys
import json
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Generator, Optional
from unittest.mock import Mock, MagicMock

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from kpp_simulator.config.manager import ConfigManager
from kpp_simulator.managers.component_manager import ComponentManager
from kpp_simulator.managers.system_manager import SystemManager
from kpp_simulator.core.physics_engine import PhysicsEngine
from kpp_simulator.electrical.electrical_system import IntegratedElectricalSystem
from kpp_simulator.control_systems.control_system import IntegratedControlSystem
from kpp_simulator.grid_services.grid_services_coordinator import GridServicesCoordinator


# Configure logging for tests
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Test configuration
TEST_CONFIG = {
    'simulation': {
        'time_step': 0.01,
        'simulation_duration': 10.0,
        'real_time_factor': 1.0
    },
    'physics': {
        'gravity': 9.81,
        'water_density': 1000.0,
        'air_density': 1.225,
        'temperature': 20.0
    },
    'performance': {
        'max_iterations_per_step': 50,
        'convergence_tolerance': 1e-6,
        'enable_multithreading': False  # Disable for tests
    },
    'output': {
        'enable_logging': False,
        'enable_data_output': False,
        'enable_plots': False
    },
    'debug': {
        'enable_debug_mode': True,
        'debug_level': 2,
        'enable_validation': True
    }
}


class TestMetrics:
    """Test performance metrics tracking"""
    
    def __init__(self):
        self.test_start_time = None
        self.test_end_time = None
        self.memory_usage = 0.0
        self.cpu_usage = 0.0
        self.assertion_count = 0
        self.error_count = 0
        self.warning_count = 0
    
    def start_test(self):
        """Start test timing"""
        self.test_start_time = time.time()
    
    def end_test(self):
        """End test timing"""
        self.test_end_time = time.time()
    
    def get_duration(self) -> float:
        """Get test duration in seconds"""
        if self.test_start_time and self.test_end_time:
            return self.test_end_time - self.test_start_time
        return 0.0
    
    def add_assertion(self):
        """Increment assertion count"""
        self.assertion_count += 1
    
    def add_error(self):
        """Increment error count"""
        self.error_count += 1
    
    def add_warning(self):
        """Increment warning count"""
        self.warning_count += 1


class TestDataManager:
    """Manages test data and temporary files"""
    
    def __init__(self):
        self.temp_dir = None
        self.test_files = []
    
    def setup(self):
        """Setup test data manager"""
        self.temp_dir = tempfile.mkdtemp(prefix="kpp_test_")
    
    def teardown(self):
        """Cleanup test data manager"""
        if self.temp_dir and os.path.exists(self.temp_dir):
            import shutil
            shutil.rmtree(self.temp_dir)
    
    def create_temp_file(self, suffix: str = ".json") -> str:
        """Create a temporary file"""
        fd, path = tempfile.mkstemp(suffix=suffix, dir=self.temp_dir)
        os.close(fd)
        self.test_files.append(path)
        return path
    
    def save_test_data(self, data: Dict[str, Any], filename: str) -> str:
        """Save test data to file"""
        filepath = os.path.join(self.temp_dir, filename)
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        self.test_files.append(filepath)
        return filepath
    
    def load_test_data(self, filepath: str) -> Dict[str, Any]:
        """Load test data from file"""
        with open(filepath, 'r') as f:
            return json.load(f)


# Global test objects
test_metrics = TestMetrics()
test_data_manager = TestDataManager()


@pytest.fixture(scope="session")
def test_config() -> Dict[str, Any]:
    """Provide test configuration"""
    return TEST_CONFIG.copy()


@pytest.fixture(scope="session")
def temp_dir() -> Generator[str, None, None]:
    """Provide temporary directory for tests"""
    test_data_manager.setup()
    yield test_data_manager.temp_dir
    test_data_manager.teardown()


@pytest.fixture
def config_manager(temp_dir) -> ConfigManager:
    """Provide configured ConfigManager"""
    config_manager = ConfigManager(temp_dir)
    config_manager.start()
    yield config_manager
    config_manager.stop()


@pytest.fixture
def component_manager() -> ComponentManager:
    """Provide configured ComponentManager"""
    component_manager = ComponentManager()
    component_manager.start()
    yield component_manager
    component_manager.stop()


@pytest.fixture
def system_manager() -> SystemManager:
    """Provide configured SystemManager"""
    system_manager = SystemManager()
    yield system_manager


@pytest.fixture
def physics_engine(test_config) -> PhysicsEngine:
    """Provide configured PhysicsEngine"""
    physics_config = test_config['physics']
    engine = PhysicsEngine(physics_config)
    yield engine


@pytest.fixture
def electrical_system(test_config) -> IntegratedElectricalSystem:
    """Provide configured IntegratedElectricalSystem"""
    electrical_config = {
        'generator': {
            'rated_power': 1000.0,
            'rated_voltage': 400.0,
            'rated_frequency': 50.0
        },
        'power_electronics': {
            'efficiency': 0.95,
            'response_time': 0.01
        }
    }
    system = IntegratedElectricalSystem(electrical_config)
    yield system


@pytest.fixture
def control_system(test_config) -> IntegratedControlSystem:
    """Provide configured IntegratedControlSystem"""
    control_config = {
        'timing': {
            'update_rate': 100.0,
            'response_time': 0.01
        },
        'pid': {
            'kp': 1.0,
            'ki': 0.1,
            'kd': 0.01
        }
    }
    system = IntegratedControlSystem(control_config)
    yield system


@pytest.fixture
def grid_services(physics_engine, electrical_system, control_system) -> GridServicesCoordinator:
    """Provide configured GridServicesCoordinator"""
    grid_config = {
        'frequency_services': {
            'enabled': True,
            'response_time': 0.1
        },
        'voltage_services': {
            'enabled': True,
            'response_time': 0.1
        }
    }
    coordinator = GridServicesCoordinator(
        physics_engine,
        electrical_system,
        control_system,
        grid_config
    )
    yield coordinator


@pytest.fixture
def mock_floater():
    """Provide mock floater for testing"""
    floater = Mock()
    floater.position = 0.0
    floater.velocity = 0.0
    floater.mass = 1000.0
    floater.volume = 1.0
    floater.state = "empty"
    
    # Mock methods
    floater.update.return_value = True
    floater.get_state.return_value = {
        'position': floater.position,
        'velocity': floater.velocity,
        'mass': floater.mass,
        'state': floater.state
    }
    
    return floater


@pytest.fixture
def mock_environment():
    """Provide mock environment for testing"""
    env = Mock()
    env.temperature = 20.0
    env.pressure = 101325.0
    env.water_density = 1000.0
    env.air_density = 1.225
    
    # Mock methods
    env.get_conditions.return_value = {
        'temperature': env.temperature,
        'pressure': env.pressure,
        'water_density': env.water_density,
        'air_density': env.air_density
    }
    
    return env


@pytest.fixture
def test_metrics_fixture():
    """Provide test metrics for tracking"""
    return test_metrics


@pytest.fixture
def test_data_manager_fixture():
    """Provide test data manager"""
    return test_data_manager


# Pytest hooks
def pytest_configure(config):
    """Configure pytest"""
    # Add custom markers
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )
    config.addinivalue_line(
        "markers", "performance: marks tests as performance tests"
    )
    config.addinivalue_line(
        "markers", "stress: marks tests as stress tests"
    )


def pytest_runtest_setup(item):
    """Setup before each test"""
    test_metrics.start_test()
    
    # Log test start
    logging.info(f"Starting test: {item.name}")


def pytest_runtest_teardown(item, nextitem):
    """Teardown after each test"""
    test_metrics.end_test()
    
    # Log test completion
    duration = test_metrics.get_duration()
    logging.info(f"Completed test: {item.name} (duration: {duration:.3f}s)")


def pytest_collection_modifyitems(config, items):
    """Modify test collection"""
    # Add markers based on test names
    for item in items:
        if "test_integration" in item.name:
            item.add_marker(pytest.mark.integration)
        elif "test_performance" in item.name:
            item.add_marker(pytest.mark.performance)
        elif "test_stress" in item.name:
            item.add_marker(pytest.mark.stress)
        else:
            item.add_marker(pytest.mark.unit)


# Test utilities
class TestUtils:
    """Utility functions for tests"""
    
    @staticmethod
    def assert_approximately_equal(actual: float, expected: float, tolerance: float = 1e-6):
        """Assert that two values are approximately equal"""
        test_metrics.add_assertion()
        assert abs(actual - expected) <= tolerance, \
            f"Expected {expected}, got {actual} (tolerance: {tolerance})"
    
    @staticmethod
    def assert_within_range(value: float, min_val: float, max_val: float):
        """Assert that a value is within a range"""
        test_metrics.add_assertion()
        assert min_val <= value <= max_val, \
            f"Value {value} is not within range [{min_val}, {max_val}]"
    
    @staticmethod
    def assert_dict_contains(dictionary: Dict[str, Any], key: str, expected_type: type = None):
        """Assert that a dictionary contains a key with optional type checking"""
        test_metrics.add_assertion()
        assert key in dictionary, f"Key '{key}' not found in dictionary"
        if expected_type:
            assert isinstance(dictionary[key], expected_type), \
                f"Key '{key}' is not of type {expected_type.__name__}"
    
    @staticmethod
    def assert_list_length(lst: list, expected_length: int):
        """Assert that a list has the expected length"""
        test_metrics.add_assertion()
        assert len(lst) == expected_length, \
            f"Expected list length {expected_length}, got {len(lst)}"
    
    @staticmethod
    def create_test_config(overrides: Dict[str, Any] = None) -> Dict[str, Any]:
        """Create test configuration with optional overrides"""
        config = TEST_CONFIG.copy()
        if overrides:
            for key, value in overrides.items():
                if isinstance(value, dict) and key in config:
                    config[key].update(value)
                else:
                    config[key] = value
        return config
    
    @staticmethod
    def wait_for_condition(condition_func: callable, timeout: float = 5.0, 
                          check_interval: float = 0.1) -> bool:
        """Wait for a condition to be true"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            if condition_func():
                return True
            time.sleep(check_interval)
        return False
    
    @staticmethod
    def measure_execution_time(func: callable, *args, **kwargs) -> Tuple[Any, float]:
        """Measure execution time of a function"""
        start_time = time.time()
        result = func(*args, **kwargs)
        execution_time = time.time() - start_time
        return result, execution_time


# Make TestUtils available to all tests
@pytest.fixture
def test_utils():
    """Provide test utilities"""
    return TestUtils


# Performance test helpers
class PerformanceTestHelper:
    """Helper for performance tests"""
    
    @staticmethod
    def benchmark_function(func: callable, iterations: int = 1000, *args, **kwargs) -> Dict[str, float]:
        """Benchmark a function"""
        times = []
        for _ in range(iterations):
            start_time = time.time()
            func(*args, **kwargs)
            times.append(time.time() - start_time)
        
        return {
            'min_time': min(times),
            'max_time': max(times),
            'avg_time': sum(times) / len(times),
            'total_time': sum(times)
        }
    
    @staticmethod
    def assert_performance_threshold(execution_time: float, max_time: float):
        """Assert that execution time is within threshold"""
        test_metrics.add_assertion()
        assert execution_time <= max_time, \
            f"Execution time {execution_time:.6f}s exceeds threshold {max_time:.6f}s"


@pytest.fixture
def performance_helper():
    """Provide performance test helper"""
    return PerformanceTestHelper


# Stress test helpers
class StressTestHelper:
    """Helper for stress tests"""
    
    @staticmethod
    def run_concurrent_operations(operation: callable, num_threads: int = 10, 
                                 num_operations: int = 100) -> Dict[str, Any]:
        """Run operations concurrently"""
        import threading
        import queue
        
        results_queue = queue.Queue()
        errors_queue = queue.Queue()
        
        def worker():
            for _ in range(num_operations):
                try:
                    result = operation()
                    results_queue.put(result)
                except Exception as e:
                    errors_queue.put(e)
        
        threads = []
        for _ in range(num_threads):
            thread = threading.Thread(target=worker)
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        results = []
        while not results_queue.empty():
            results.append(results_queue.get())
        
        errors = []
        while not errors_queue.empty():
            errors.append(errors_queue.get())
        
        return {
            'total_operations': len(results),
            'successful_operations': len(results),
            'failed_operations': len(errors),
            'errors': errors
        }
    
    @staticmethod
    def assert_stress_test_passed(results: Dict[str, Any], min_success_rate: float = 0.95):
        """Assert that stress test passed"""
        test_metrics.add_assertion()
        total_ops = results['total_operations'] + results['failed_operations']
        if total_ops > 0:
            success_rate = results['successful_operations'] / total_ops
            assert success_rate >= min_success_rate, \
                f"Success rate {success_rate:.2%} below threshold {min_success_rate:.2%}"


@pytest.fixture
def stress_helper():
    """Provide stress test helper"""
    return StressTestHelper

