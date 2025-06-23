"""
Sensors module for KPP simulator.
Allows registration and polling of custom sensor objects (e.g., PositionSensor).
"""

import logging
from utils.logging_setup import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

class Sensors:
    """
    Manages a collection of sensor objects and polls them each time-step.
    """
    def __init__(self, simulation=None):
        """
        Initialize the sensors module.

        Args:
            simulation: Reference to the Simulation object (optional).
        """
        self.simulation = simulation
        self.sensors = []
        logger.info("Sensors module initialized.")

    def register(self, sensor):
        """
        Register a new sensor.

        Args:
            sensor: The sensor object to register.
        """
        self.sensors.append(sensor)
        logger.info(f"Registered sensor: {sensor}")

    def poll(self, floater):
        """
        Poll all sensors for a given floater and return triggers.

        Args:
            floater: Floater object to check.

        Returns:
            list: List of triggered sensors.
        """
        triggered = []
        for sensor in self.sensors:
            if hasattr(sensor, 'check') and sensor.check(floater):
                triggered.append(sensor)
        return triggered
