"""Configuration logic and physical constants."""

# Physical constants
G = 9.81  # gravitational acceleration (m/s^2)
RHO_WATER = 1000.0  # density of water (kg/m^3)
RHO_AIR = 1.225  # density of air (kg/m^3)

# Default simulation parameters
default_params = {
    "time_step": 0.1,
    "total_time": 10.0,
    "floater_count": 8,
    # ... add more as needed ...
}

DEFAULT_PARAMS = default_params
