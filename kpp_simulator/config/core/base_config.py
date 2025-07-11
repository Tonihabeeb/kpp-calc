"""
Base Configuration for KPP Simulator
Provides base configuration functionality and validation
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
import json
import os

@dataclass
class BaseConfig:
    """Base configuration class"""
    
    def __init__(self):
        """Initialize base configuration"""
        self.config_data: Dict[str, Any] = {}
        self.validation_errors: List[str] = []
        
    def load_configuration(self, config_path: str) -> bool:
        """Load configuration from file"""
        try:
            if not os.path.exists(config_path):
                return False
                
            with open(config_path, 'r') as f:
                self.config_data = json.load(f)
            return True
            
        except Exception as e:
            self.validation_errors.append(f"Failed to load configuration: {e}")
            return False
    
    def save_configuration(self, config_path: str) -> bool:
        """Save configuration to file"""
        try:
            with open(config_path, 'w') as f:
                json.dump(self.config_data, f, indent=2)
            return True
            
        except Exception as e:
            self.validation_errors.append(f"Failed to save configuration: {e}")
            return False
    
    def validate_configuration(self) -> Tuple[bool, List[str]]:
        """Validate configuration"""
        self.validation_errors = []
        
        # Basic validation - check if config_data is not empty
        if not self.config_data:
            self.validation_errors.append("Configuration is empty")
        
        return len(self.validation_errors) == 0, self.validation_errors
    
    def get_value(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        return self.config_data.get(key, default)
    
    def set_value(self, key: str, value: Any) -> bool:
        """Set configuration value"""
        try:
            self.config_data[key] = value
            return True
        except Exception as e:
            self.validation_errors.append(f"Failed to set value: {e}")
            return False
    
    def clear_configuration(self):
        """Clear configuration data"""
        self.config_data = {}
        self.validation_errors = [] 