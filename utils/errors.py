"""Custom exception classes and error handling hooks (stub)."""

class SimulationError(Exception):
    pass

class ConfigError(SimulationError):
    pass

class PhysicsError(SimulationError):
    pass

class ControlError(SimulationError):
    pass
