"""
Parameter Schema & Validation for KPP Simulator
Defines validation rules, defaults, and types for all simulation parameters.
"""

import logging
from typing import Any, Dict, List, Union

logger = logging.getLogger(__name__)

# Export list
__all__ = [
    "validate_parameters",
    "validate_parameters_batch",
    "validate_parameter",
    "get_default_parameters",
    "get_parameter_info",
    "get_all_parameter_info",
    "PARAM_SCHEMA",
]

# Complete parameter schema with validation rules
PARAM_SCHEMA = {
    # Core simulation parameters
    "num_floaters": {"type": int, "min": 1, "max": 20, "default": 8},
    "floater_volume": {"type": float, "min": 0.1, "max": 2.0, "default": 0.3},
    "floater_mass_empty": {"type": float, "min": 1.0, "max": 100.0, "default": 18.0},
    "floater_area": {"type": float, "min": 0.01, "max": 0.5, "default": 0.035},
    "drag_coefficient": {"type": float, "min": 0.1, "max": 2.0, "default": 0.8},
    "floater_Cd": {"type": float, "min": 0.1, "max": 2.0, "default": 0.8},  # Legacy alias
    # Pneumatic system parameters
    "air_pressure": {"type": float, "min": 0.1, "max": 10.0, "default": 3.0},
    "air_fill_time": {"type": float, "min": 0.1, "max": 5.0, "default": 0.5},
    "air_flow_rate": {"type": float, "min": 0.1, "max": 2.0, "default": 0.6},
    "jet_efficiency": {"type": float, "min": 0.1, "max": 1.0, "default": 0.85},
    # Drivetrain parameters
    "sprocket_radius": {"type": float, "min": 0.1, "max": 2.0, "default": 0.5},
    "flywheel_inertia": {"type": float, "min": 1.0, "max": 200.0, "default": 50.0},
    "gear_ratio": {"type": float, "min": 1.01, "max": 10.0, "default": 2.5},
    "drivetrain_efficiency": {"type": float, "min": 0.1, "max": 1.0, "default": 0.85},
    # H1 Nanobubble parameters
    "nanobubble_frac": {"type": float, "min": 0.0, "max": 1.0, "default": 0.0},
    "h1_enabled": {"type": bool, "default": False},
    "nanobubble_generation_power": {
        "type": float,
        "min": 0.0,
        "max": 10000.0,
        "default": 2500.0,
    },
    "drag_reduction_factor": {"type": float, "min": 0.0, "max": 0.5, "default": 0.12},
    # H2 Thermal parameters
    "thermal_coeff": {"type": float, "min": 0.0, "max": 1.0, "default": 0.0001},
    "h2_enabled": {"type": bool, "default": False},
    "water_temperature": {
        "type": float,
        "min": 273.15,
        "max": 373.15,
        "default": 293.15,
    },
    "thermal_efficiency": {"type": float, "min": 0.1, "max": 1.0, "default": 0.75},
    # H3 Pulse control parameters
    "pulse_enabled": {"type": bool, "default": False},
    "h3_enabled": {"type": bool, "default": False},
    "pulse_duration": {"type": float, "min": 1.0, "max": 30.0, "default": 5.0},
    "coast_duration": {"type": float, "min": 1.0, "max": 30.0, "default": 5.0},
    "pulse_duty_cycle": {"type": float, "min": 0.1, "max": 0.9, "default": 0.5},
    # Simulation control
    "simulation_speed": {"type": float, "min": 0.1, "max": 10.0, "default": 1.0},
    "time_step": {"type": float, "min": 0.001, "max": 0.1, "default": 0.01},
    "max_simulation_time": {
        "type": float,
        "min": 10.0,
        "max": 3600.0,
        "default": 300.0,
    },
    # Environment parameters
    "water_depth": {"type": float, "min": 1.0, "max": 50.0, "default": 10.0},
    "water_density": {"type": float, "min": 800.0, "max": 1200.0, "default": 1000.0},
    "gravity": {"type": float, "min": 8.0, "max": 12.0, "default": 9.81},
    # Generator load parameters
    "generator_load": {"type": float, "min": 0.0, "max": 1000.0, "default": 100.0},
    "load_resistance": {"type": float, "min": 0.1, "max": 100.0, "default": 10.0},
}


def validate_parameter(name: str, value: Any) -> Dict[str, Any]:
    """
    Validate a single parameter against the schema.

    Args:
        name (str): Parameter name
        value (Any): Parameter value

    Returns:
        Dict containing validation result
    """
    if name not in PARAM_SCHEMA:
        return {"valid": False, "error": f"Unknown parameter: {name}", "value": value}

    schema = PARAM_SCHEMA[name]
    param_type = schema["type"]

    # Type validation
    try:
        if param_type == bool:
            if isinstance(value, str):
                value = value.lower() in ("true", "1", "yes", "on")
            else:
                value = bool(value)
        elif param_type == int:
            value = int(float(value))  # Handle string numbers
        elif param_type == float:
            value = float(value)
        else:
            return {
                "valid": False,
                "error": f"Unsupported parameter type: {param_type}",
                "value": value,
            }
    except (ValueError, TypeError):
        return {
            "valid": False,
            "error": f"Cannot convert {value} to {param_type.__name__}",
            "value": value,
        }

    # Range validation for numeric types
    if param_type in (int, float):
        if "min" in schema and value < schema["min"]:
            return {
                "valid": False,
                "error": f'{name} must be >= {schema["min"]}, got {value}',
                "value": value,
            }
        if "max" in schema and value > schema["max"]:
            return {
                "valid": False,
                "error": f'{name} must be <= {schema["max"]}, got {value}',
                "value": value,
            }

    return {"valid": True, "value": value}


def validate_parameters_batch(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate a batch of parameters.

    Args:
        params (dict): Dictionary of parameter name-value pairs

    Returns:
        Dict containing validation results
    """
    results = {"valid": True, "validated_params": {}, "errors": [], "warnings": []}

    for name, value in params.items():
        validation = validate_parameter(name, value)

        if validation["valid"]:
            results["validated_params"][name] = validation["value"]
        else:
            results["valid"] = False
            results["errors"].append(
                {"parameter": name, "error": validation["error"], "value": value}
            )

    logger.info(
        f"Parameter validation: {len(params)} params, "
        f"{len(results['errors'])} errors"
    )

    return results


def validate_parameters(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate parameters and raise exception on validation errors.
    This is a convenience wrapper around validate_parameters_batch.

    Args:
        params (dict): Dictionary of parameter name-value pairs

    Returns:
        Dict of validated parameters

    Raises:
        ValueError: If any parameter validation fails
    """
    result = validate_parameters_batch(params)

    if not result["valid"]:
        error_messages = [
            f"{err['parameter']}: {err['error']}" for err in result["errors"]
        ]
        raise ValueError(f"Parameter validation failed: {'; '.join(error_messages)}")

    return result["validated_params"]


def get_default_parameters() -> Dict[str, Any]:
    """
    Get dictionary of all default parameter values.

    Returns:
        Dict of parameter defaults
    """
    defaults = {}
    for name, schema in PARAM_SCHEMA.items():
        if "default" in schema:
            defaults[name] = schema["default"]

    logger.debug(f"Retrieved {len(defaults)} default parameters")
    return defaults


def get_parameter_info(name: str) -> Dict[str, Any]:
    """
    Get detailed information about a parameter.

    Args:
        name (str): Parameter name

    Returns:
        Dict containing parameter information
    """
    if name not in PARAM_SCHEMA:
        return {"error": f"Unknown parameter: {name}"}

    info = PARAM_SCHEMA[name].copy()
    info["name"] = name
    return info


def get_all_parameter_info() -> Dict[str, Dict[str, Any]]:
    """
    Get information about all parameters.

    Returns:
        Dict mapping parameter names to their info
    """
    return {name: get_parameter_info(name) for name in PARAM_SCHEMA.keys()}
