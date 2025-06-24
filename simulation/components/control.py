"""
Control system module.
Coordinates high-level control logic for the KPP simulator (stub for future expansion).
"""

# High-level control logic for the simulation (stub, ready for extension)
# Manages control strategies and system-level decisions

import logging
from utils.logging_setup import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

class Control:
    """
    Control system for the KPP simulator.
    Monitors and coordinates actions between subsystems (now with rule-based closed-loop logic).
    """
    def __init__(self, simulation=None, floaters=None, pneumatic=None, sensors=None, top_sensor=None, bottom_sensor=None):
        """
        Initialize the control system.

        Args:
            simulation: Reference to the Simulation object (optional).
            floaters: List of Floater objects.
            pneumatic: PneumaticSystem object.
            sensors: Sensors manager object.
            top_sensor: PositionSensor for top position.
            bottom_sensor: PositionSensor for bottom position.
        """
        self.simulation = simulation
        self.floaters = floaters
        self.pneumatic = pneumatic
        self.sensors = sensors
        self.top_sensor = top_sensor
        self.bottom_sensor = bottom_sensor
        logger.info("Control system initialized.")

    def update(self, dt: float) -> None:
        """
        Update control logic (rule-based closed-loop).

        Args:
            dt (float): Time step (s).
        """
        if not self.floaters or not self.pneumatic or not self.top_sensor or not self.bottom_sensor:
            logger.warning("Control update skipped: missing references to floaters, pneumatic, or sensors.")
            return
        for floater in self.floaters:
            # Inject air at the bottom if not filled
            if self.bottom_sensor.check(floater) and not floater.is_filled:
                self.pneumatic.trigger_injection(floater)
            # Vent air at the top if filled
            if self.top_sensor.check(floater) and floater.is_filled:
                self.pneumatic.vent_air(floater)
        logger.debug("Control update completed for all floaters.")
