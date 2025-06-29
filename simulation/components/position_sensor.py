"""
PositionSensor module for KPP simulator.
Simulates a binary position sensor that triggers when a floater crosses a certain position.
"""


class PositionSensor:
    """
    Simulates a binary position sensor for a floater.
    Triggers when the floater crosses a threshold position.
    """

    def __init__(self, position_threshold: float, trigger_when: str = "above"):
        """
        Args:
            position_threshold (float): The position threshold to trigger the sensor.
            trigger_when (str): Condition for triggering, "above" or "below" the threshold.
        """
        self.position_threshold = position_threshold
        self.trigger_when = trigger_when

    def check(self, floater) -> bool:
        """
        Check if the floater triggers the sensor.
        Args:
            floater: Floater object with a position attribute.
        Returns:
            bool: True if triggered, False otherwise.
        """
        if self.trigger_when == "above":
            return floater.position >= self.position_threshold
        elif self.trigger_when == "below":
            return floater.position <= self.position_threshold
        return False
