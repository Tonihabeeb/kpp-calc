"""Custom exception classes and error handling hooks (stub)."""

class SimulationError(Exception):
    pass

class ConfigError(SimulationError):
    pass

class PhysicsError(SimulationError):
    pass

class ControlError(SimulationError):
    pass

class FloaterError(SimulationError):
    """Exception for errors in Floater computations."""
    def __init__(self, floater_id, message):
        super().__init__(f"Floater {floater_id}: {message}")

class EnvironmentError(SimulationError):
    """Exception for errors in Environment or invalid parameters."""
    pass
