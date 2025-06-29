"""
Pytest configuration and shared fixtures for KPP Simulator testing
"""

import os
import queue
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict
from unittest.mock import MagicMock, Mock

import pytest

# Test configuration constants
TEST_SIMULATION_PARAMS = {
    "dt": 0.1,
    "total_time": 10.0,
    "num_floaters": 4,
    "chain_radius": 7.5,
    "floater_mass": 100.0,
    "floater_volume": 0.15,
    "water_density": 1025.0,
    "drag_coefficient": 0.8,
    "generator_efficiency": 0.9,
    "drivetrain_efficiency": 0.85,
}

TEST_FLOATER_PARAMS = {
    "mass": 100.0,
    "volume": 0.15,
    "drag_coefficient": 0.8,
    "position": 0.0,
    "velocity": 0.0,
    "submerged_fraction": 0.5,
}


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def simulation_params():
    """Standard simulation parameters for testing"""
    return TEST_SIMULATION_PARAMS.copy()


@pytest.fixture
def floater_params():
    """Standard floater parameters for testing"""
    return TEST_FLOATER_PARAMS.copy()


@pytest.fixture
def data_queue():
    """Mock data queue for simulation engine testing"""
    return queue.Queue()


@pytest.fixture
def mock_logger():
    """Mock logger for testing without actual logging"""
    return Mock()


@pytest.fixture
def mock_simulation_engine():
    """Mock SimulationEngine for testing components that depend on it"""
    engine = Mock()
    engine.time = 0.0
    engine.params = TEST_SIMULATION_PARAMS.copy()
    engine.running = False
    engine.data_log = []
    return engine


@pytest.fixture
def mock_floater():
    """Mock Floater for testing physics calculations"""
    floater = Mock()
    floater.mass = TEST_FLOATER_PARAMS["mass"]
    floater.volume = TEST_FLOATER_PARAMS["volume"]
    floater.drag_coefficient = TEST_FLOATER_PARAMS["drag_coefficient"]
    floater.position = TEST_FLOATER_PARAMS["position"]
    floater.velocity = TEST_FLOATER_PARAMS["velocity"]
    floater.submerged_fraction = TEST_FLOATER_PARAMS["submerged_fraction"]
    return floater


@pytest.fixture
def physics_constants():
    """Physics constants for testing calculations"""
    return {
        "gravity": 9.81,  # m/s²
        "water_density": 1025.0,  # kg/m³
        "air_density": 1.225,  # kg/m³
        "atmospheric_pressure": 101325.0,  # Pa
        "water_viscosity": 1.002e-3,  # Pa·s
    }


@pytest.fixture
def sample_simulation_data():
    """Sample simulation state data for testing"""
    return {
        "time": 5.0,
        "torque": 1500.0,
        "power": 750.0,
        "efficiency": 0.85,
        "floaters": [
            {
                "id": 0,
                "buoyancy": 1000.0,
                "drag": 50.0,
                "position": 0.0,
                "velocity": 1.5,
            },
            {
                "id": 1,
                "buoyancy": 950.0,
                "drag": 45.0,
                "position": 1.57,
                "velocity": 1.2,
            },
        ],
    }


@pytest.fixture
def test_config_file(temp_dir):
    """Create a temporary configuration file for testing"""
    config_content = """
{
    "simulation": {
        "dt": 0.1,
        "total_time": 10.0,
        "num_floaters": 4
    },
    "physics": {
        "water_density": 1025.0,
        "gravity": 9.81
    }
}
"""
    config_path = os.path.join(temp_dir, "test_config.json")
    with open(config_path, "w") as f:
        f.write(config_content)
    return config_path


# Integration test fixtures
@pytest.fixture
def temp_workspace():
    """Create a temporary workspace for integration tests"""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def simulation_config():
    """Standard simulation configuration for integration tests"""
    return {
        "dt": 0.1,
        "total_time": 1.0,
        "floater_count": 4,
        "chain_radius": 5.0,
        "fluid_density": 1025.0,
        "test_mode": True,
    }


@pytest.fixture
def mock_data_queue():
    """Mock data queue for integration tests"""
    try:
        import queue

        return queue.Queue()
    except ImportError:
        return None


@pytest.fixture
def floater_test_data():
    """Test data for floater integration tests"""
    return {
        "volume": 1.0,
        "mass": 500.0,
        "area": 2.0,
        "drag_coefficient": 0.8,
        "position": 0.0,
        "velocity": 0.0,
    }


class IntegrationTestHelper:
    """Helper class for integration testing"""

    @staticmethod
    def validate_simulation_state(state_data):
        """Validate simulation state data structure"""
        required_keys = ["timestamp", "time", "torque", "power"]
        return all(key in state_data for key in required_keys)

    @staticmethod
    def create_test_floater_chain(count=4):
        """Create a chain of test floaters"""
        try:
            from simulation.components.floater import Floater

            floaters = []
            for i in range(count):
                floater = Floater(
                    volume=1.0,
                    mass=500.0,
                    area=2.0,
                    drag_coefficient=0.8,
                    position=float(i),
                    velocity=0.0,
                )
                floaters.append(floater)
            return floaters
        except ImportError:
            return []


@pytest.fixture
def integration_helper():
    """Integration test helper instance"""
    return IntegrationTestHelper()


@pytest.fixture(autouse=True)
def setup_test_environment(monkeypatch):
    """Automatically set up test environment for each test"""
    # Set test environment variables
    monkeypatch.setenv("TESTING", "true")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")

    # Mock potentially problematic imports/modules
    mock_modules = ["matplotlib", "numpy", "scipy"]

    for module in mock_modules:
        try:
            __import__(module)
        except ImportError:
            # Create a mock module if it's not available
            mock_module = MagicMock()
            monkeypatch.setitem(sys.modules, module, mock_module)


# Test markers for categorizing tests
pytestmark = [
    pytest.mark.unit,  # Mark all tests in conftest as unit tests by default
]


# Custom pytest hooks
def pytest_configure(config):
    """Configure pytest with custom settings"""
    config.addinivalue_line("markers", "unit: mark test as a unit test")
    config.addinivalue_line("markers", "integration: mark test as an integration test")
    config.addinivalue_line("markers", "slow: mark test as slow running")
    config.addinivalue_line("markers", "physics: mark test as physics calculation test")


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add default markers"""
    for item in items:
        # Add unit marker to tests that don't have integration marker
        if "integration" not in item.keywords:
            item.add_marker(pytest.mark.unit)

        # Add slow marker to tests that might take time
        if "slow" in item.name or "integration" in item.keywords:
            item.add_marker(pytest.mark.slow)


# Test utilities
class TestUtils:
    """Utility functions for testing"""

    @staticmethod
    def assert_close(actual, expected, tolerance=1e-6):
        """Assert that two values are close within tolerance"""
        assert (
            abs(actual - expected) < tolerance
        ), f"Expected {expected}, got {actual} (tolerance: {tolerance})"

    @staticmethod
    def create_mock_with_attrs(**attrs):
        """Create a mock object with specified attributes"""
        mock_obj = Mock()
        for attr, value in attrs.items():
            setattr(mock_obj, attr, value)
        return mock_obj


@pytest.fixture
def test_utils():
    """Provide test utility functions"""
    return TestUtils
