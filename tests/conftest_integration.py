#!/usr/bin/env python3
"""Integration test fixtures and configuration"""

import json
import os
import tempfile
from pathlib import Path

import pytest


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
        "Cd": 0.8,
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
                    Cd=0.8,
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
