import logging
from typing import Any, Dict, List, Tuple, Optional
"""
Configuration validation utilities.
Provides validation logic for configuration parameters.
"""

class ValidationResult:
    def __init__(self, is_valid: bool, errors: Optional[List[str]] = None, warnings: Optional[List[str]] = None):
        self.is_valid = is_valid
        self.errors = errors or []
        self.warnings = warnings or []

class ConfigValidator:
    """
    Validates configuration dictionaries for the KPP simulator.
    """
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def validate_config(self, config: Any) -> ValidationResult:
        """
        Validate a configuration dictionary or object.
        Args:
            config: Configuration dictionary or object
        Returns:
            ValidationResult
        """
        errors = []
        warnings = []
        # Basic validation: check for required keys if dict
        if isinstance(config, dict):
            if not config:
                errors.append("Configuration is empty.")
        # Add more detailed validation as needed
        is_valid = len(errors) == 0
        return ValidationResult(is_valid, errors, warnings)

