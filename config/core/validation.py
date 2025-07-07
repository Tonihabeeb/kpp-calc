"""
Configuration validation utilities.
Provides validation logic for configuration parameters.
"""

import logging
from typing import Any, Dict, List, Tuple


logger = logging.getLogger(__name__)


class ConfigValidator:
    """Configuration validation utilities"""
    
    def __init__(self):
        """Initialize validator with error tracking"""
        self.errors = []
        self.warnings = []
    
    def check_positive_int(self, value: int, name: str) -> bool:
        """Check if value is a positive integer"""
        if not isinstance(value, int) or value <= 0:
            self.add_error(f"{name} must be a positive integer, got {value}")
            return False
        return True
    
    def check_positive_float(self, value: float, name: str) -> bool:
        """Check if value is a positive float"""
        if not isinstance(value, (int, float)) or value <= 0:
            self.add_error(f"{name} must be a positive number, got {value}")
            return False
        return True
    
    def check_range(self, value: float, min_val: float, max_val: float, name: str) -> bool:
        """Check if value is within specified range"""
        if not isinstance(value, (int, float)) or value < min_val or value > max_val:
            self.add_error(f"{name} must be between {min_val} and {max_val}, got {value}")
            return False
        return True
    
    def add_error(self, error: str) -> None:
        """Add an error to the validation results"""
        self.errors.append(error)
    
    def add_warning(self, warning: str) -> None:
        """Add a warning to the validation results"""
        self.warnings.append(warning)
    
    def is_valid(self) -> bool:
        """Check if validation passed (no errors)"""
        return len(self.errors) == 0
    
    def get_errors(self) -> List[str]:
        """Get list of validation errors"""
        return self.errors.copy()
    
    def get_validation_warnings(self) -> List[str]:
        """Get list of validation warnings"""
        return self.warnings.copy()
    
    def reset(self) -> None:
        """Reset validator state"""
        self.errors.clear()
        self.warnings.clear()

    @staticmethod
    def validate_physics_constraints(config: Dict[str, Any]) -> List[str]:
        """Validate physics constraints across configuration"""
        errors = []

        # Check density constraints
        if "volume" in config and "mass" in config:
            volume = config["volume"]
            mass = config["mass"]

            if volume > 0:
                density = mass / volume
                if density > 1000:  # Water density
                    errors.append(f"Floater density ({density:.1f} kg/m³) exceeds water density")

        # Check position constraints
        if "position" in config and "tank_height" in config:
            position = config["position"]
            tank_height = config["tank_height"]

            if position > tank_height:
                errors.append(f"Position ({position}m) exceeds tank height ({tank_height}m)")

        # Check velocity constraints
        if "velocity" in config:
            velocity = config["velocity"]
            if abs(velocity) > 60:  # Maximum safe velocity
                errors.append(f"Velocity ({velocity} m/s) exceeds safe limits")

        return errors

    @staticmethod
    def validate_cross_parameter_constraints(config: Dict[str, Any]) -> List[str]:
        """Validate relationships between different parameters"""
        errors = []

        # Check floater count vs tank capacity
        if "num_floaters" in config and "tank_volume" in config:
            num_floaters = config["num_floaters"]
            tank_volume = config["tank_volume"]
            floater_volume = config.get("volume", 0.4)

            total_floater_volume = num_floaters * floater_volume
            if total_floater_volume > tank_volume * 0.8:  # 80% capacity limit
                errors.append(
                    f"Total floater volume ({total_floater_volume:.2f}m³) "
                    f"exceeds 80% of tank capacity ({tank_volume:.2f}m³)"
                )

        return errors

    @staticmethod
    def validate_operational_constraints(config: Dict[str, Any]) -> List[str]:
        """Validate operational constraints"""
        errors = []

        # Check power limits
        if "max_power" in config:
            max_power = config["max_power"]
            if max_power > 100000:  # 100 kW limit
                errors.append(f"Maximum power ({max_power}W) exceeds operational limits")

        # Check pressure limits
        if "air_pressure" in config:
            air_pressure = config["air_pressure"]
            if air_pressure > 1000000:  # 1 MPa limit
                errors.append(f"Air pressure ({air_pressure}Pa) exceeds safety limits")

        return errors

    @staticmethod
    def validate_config(config: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Comprehensive configuration validation"""
        errors = []

        # Physics constraints
        errors.extend(ConfigValidator.validate_physics_constraints(config))

        # Cross-parameter constraints
        errors.extend(ConfigValidator.validate_cross_parameter_constraints(config))

        # Operational constraints
        errors.extend(ConfigValidator.validate_operational_constraints(config))

        is_valid = len(errors) == 0

        if not is_valid:
            logger.warning(f"Configuration validation failed: {errors}")

        return is_valid, errors

    @staticmethod
    def get_warnings(config: Dict[str, Any]) -> List[str]:
        """Get configuration warnings (non-critical issues)"""
        warnings = []

        # Check for suboptimal parameters
        if "volume" in config and config["volume"] < 0.1:
            warnings.append("Small floater volume may affect performance")

        if "mass" in config and config["mass"] > 500:
            warnings.append("Large floater mass may affect buoyancy")

        if "drag_coefficient" in config and config["drag_coefficient"] > 1.5:
            warnings.append("High drag coefficient may reduce efficiency")

        return warnings
