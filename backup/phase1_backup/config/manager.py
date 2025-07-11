import logging
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from watchdog.observers import Observer  # type: ignore
    from watchdog.events import FileSystemEventHandler  # type: ignore
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False

from .core.validation import ConfigValidator
from .components.simulation_config import SimulationConfig
from .components.floater_config import FloaterConfig
from .components.electrical_config import ElectricalConfig
from .components.drivetrain_config import DrivetrainConfig
from .components.control_config import ControlConfig

"""
Configuration manager for the KPP simulator.
Handles loading, validation, and hot-reload of configurations.
"""

class ConfigManager:
    """
    Configuration manager for the KPP simulator.
    Handles loading, validation, and hot-reload of configurations.
    """
    
    def __init__(self, config_dir: Optional[str] = None):
        """
        Initialize the configuration manager.
        
        Args:
            config_dir: Directory containing configuration files
        """
        self.config_dir = Path(config_dir) if config_dir else Path(__file__).parent
        self.logger = logging.getLogger(__name__)
        
        # Configuration cache
        self._config_cache: Dict[str, Any] = {}
        self._config_validator = ConfigValidator()
        
        # Hot reload support
        self._observer = None
        self._file_handlers: Dict[str, Any] = {}
        
        self.logger.info("Configuration manager initialized")
    
    def get_config(self, config_type: str) -> Any:
        """
        Get configuration for the specified type.
        
        Args:
            config_type: Type of configuration to retrieve
            
        Returns:
            Configuration object
        """
        if config_type not in self._config_cache:
            self._load_config(config_type)
        
        return self._config_cache[config_type]
    
    def _load_config(self, config_type: str) -> None:
        """
        Load configuration from file.
        
        Args:
            config_type: Type of configuration to load
        """
        try:
            config_file = self.config_dir / f"{config_type}.json"
            
            if config_file.exists():
                with open(config_file, 'r') as f:
                    config_data = json.load(f)
                
                # Validate configuration
                validation_result = self._config_validator.validate_config(config_data)
                if not validation_result.is_valid:
                    self.logger.warning(f"Configuration validation failed for {config_type}: {validation_result.errors}")
                
                self._config_cache[config_type] = config_data
            else:
                # Use default configuration
                self._config_cache[config_type] = self._get_default_config(config_type)
                
        except Exception as e:
            self.logger.error(f"Error loading configuration for {config_type}: {e}")
            self._config_cache[config_type] = self._get_default_config(config_type)
    
    def _get_default_config(self, config_type: str) -> Any:
        """
        Get default configuration for the specified type.
        
        Args:
            config_type: Type of configuration
            
        Returns:
            Default configuration object
        """
        default_configs = {
            'floater': FloaterConfig(),
            'electrical': ElectricalConfig(),
            'drivetrain': DrivetrainConfig(),
            'control': ControlConfig(),
            'simulation': SimulationConfig()
        }
        
        return default_configs.get(config_type, {})
    
    def reload_config(self, config_type: str) -> None:
        """
        Reload configuration for the specified type.
        
        Args:
            config_type: Type of configuration to reload
        """
        if config_type in self._config_cache:
            del self._config_cache[config_type]
        
        self._load_config(config_type)
        self.logger.info(f"Configuration reloaded for {config_type}")
    
    def validate_all_configs(self) -> Dict[str, bool]:
        """
        Validate all loaded configurations.
        
        Returns:
            Dictionary mapping config types to validation results
        """
        results = {}
        
        for config_type in self._config_cache:
            try:
                config_data = self._config_cache[config_type]
                validation_result = self._config_validator.validate_config(config_data)
                results[config_type] = validation_result.is_valid
            except Exception as e:
                self.logger.error(f"Error validating {config_type}: {e}")
                results[config_type] = False
        
        return results

