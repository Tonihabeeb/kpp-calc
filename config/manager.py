"""
Configuration manager for the KPP simulator.
Handles loading, validation, and hot-reload of configurations.
"""

import json
import logging
from typing import Any, Dict, List, Optional

# Optional watchdog import for hot-reload functionality
try:
    from watchdog.events import FileSystemEventHandler  # type: ignore
    from watchdog.observers import Observer  # type: ignore

    WATCHDOG_AVAILABLE = True
    FileSystemEventHandlerBase = FileSystemEventHandler
    ObserverClass = Observer
                
except ImportError:
    WATCHDOG_AVAILABLE = False
    # Create dummy base classes when watchdog is not available
    class FileSystemEventHandlerBase:
        """Dummy base class when watchdog is not available"""
        def __init__(self):
            pass
    
    class ObserverClass:
        """Dummy observer class when watchdog is not available"""
        def __init__(self):
            pass
        
        def schedule(self, *args, **kwargs):
            pass
        
        def start(self):
            pass
        
        def stop(self):
            pass
        
        def join(self):
            pass


# Ensure FileSystemEventHandlerBase is always available
if not WATCHDOG_AVAILABLE:
    # FileSystemEventHandlerBase is already defined in the except block
    pass
else:
    # When watchdog is available, FileSystemEventHandlerBase is already set to FileSystemEventHandler
    pass


class ConfigFileHandler(FileSystemEventHandlerBase):  # type: ignore
    """File system event handler for configuration hot-reload"""

    def __init__(self, config_manager: "ConfigManager"):
        super().__init__()
        self.config_manager = config_manager

    def on_modified(self, event):
        """Handle file modification events"""
        if WATCHDOG_AVAILABLE and not event.is_directory and event.src_path.endswith(".json"):
            logger.info(f"Configuration file modified: {event.src_path}")
            self.config_manager.reload_config()

from .components.control_config import ControlConfig
from .components.drivetrain_config import DrivetrainConfig
from .components.electrical_config import ElectricalConfig
from .components.floater_config import FloaterConfig
from .components.simulation_config import SimulationConfig
from .core.validation import ConfigValidator

logger = logging.getLogger(__name__)


class ConfigManager:
    """Manages configuration loading, validation, and hot-reload"""

    def __init__(self, config_file: Optional[str] = None):
        """Initialize the configuration manager."""
        import os
        from pathlib import Path
        
        self.config_file = config_file or "config/presets/default.json"
        self.config_dir = Path("config/presets")
        self.simulation_config = None
        self.floater_config = None
        self.electrical_config = None
        self.drivetrain_config = None
        self.control_config = None
        
        # Initialize hot-reload attributes
        self.observer = None
        self.file_handler = None

        # Load configuration
        self.load_default_config()

    def load_default_config(self) -> None:
        """Load default configuration"""
        logger.info("Loading default configuration")

        # Create default configurations
        self.simulation_config = SimulationConfig()
        self.floater_config = FloaterConfig()
        self.electrical_config = ElectricalConfig()
        self.drivetrain_config = DrivetrainConfig()
        self.control_config = ControlConfig()

        # Validate configurations
        self.validate_all_configs()

    def load_config_from_file(self, config_name: str) -> bool:
        """Load configuration from JSON file"""
        config_file = self.config_dir / f"{config_name}.json"

        if not config_file.exists():
            logger.error(f"Configuration file not found: {config_file}")
            return False

        try:
            with open(config_file, "r") as f:
                config_data = json.load(f)

            # Load each component configuration
            if "simulation" in config_data:
                self.simulation_config = SimulationConfig(**config_data["simulation"])

            if "floater" in config_data:
                self.floater_config = FloaterConfig(**config_data["floater"])

            if "electrical" in config_data:
                self.electrical_config = ElectricalConfig(**config_data["electrical"])

            if "integrated_drivetrain" in config_data:
                self.drivetrain_config = DrivetrainConfig(**config_data["integrated_drivetrain"])

            if "control" in config_data:
                self.control_config = ControlConfig(**config_data["control"])

            # Validate configurations
            if self.validate_all_configs():
                logger.info(f"Configuration loaded successfully: {config_name}")
                return True
            else:
                logger.error(f"Configuration validation failed: {config_name}")
                return False

        except Exception as e:
            logger.error(f"Error loading configuration {config_name}: {e}")
            return False

    def save_config_to_file(self, config_name: str) -> bool:
        """Save current configuration to JSON file"""
        config_file = self.config_dir / f"{config_name}.json"

        try:
            config_data = {}
            
            # Safely get config data with null checks
            if self.simulation_config:
                to_dict_method = getattr(self.simulation_config, "to_dict", None)
                config_data["simulation"] = to_dict_method() if to_dict_method else {}
            
            if self.floater_config:
                to_dict_method = getattr(self.floater_config, "to_dict", None)
                config_data["floater"] = to_dict_method() if to_dict_method else {}
            
            if self.electrical_config:
                to_dict_method = getattr(self.electrical_config, "to_dict", None)
                config_data["electrical"] = to_dict_method() if to_dict_method else {}
            
            if self.drivetrain_config:
                to_dict_method = getattr(self.drivetrain_config, "to_dict", None)
                config_data["integrated_drivetrain"] = to_dict_method() if to_dict_method else {}
            
            if self.control_config:
                to_dict_method = getattr(self.control_config, "to_dict", None)
                config_data["control"] = to_dict_method() if to_dict_method else {}

            with open(config_file, "w") as f:
                json.dump(config_data, f, indent=2)

            logger.info(f"Configuration saved successfully: {config_name}")
            return True

        except Exception as e:
            logger.error(f"Error saving configuration {config_name}: {e}")
            return False

    def validate_all_configs(self) -> bool:
        """Validate all configuration components"""
        all_valid = True

        # Validate individual configurations
        configs = [
            ("simulation", self.simulation_config),
            ("floater", self.floater_config),
            ("electrical", self.electrical_config),
            ("integrated_drivetrain", self.drivetrain_config),
            ("control", self.control_config),
        ]

        for name, config in configs:
            if config is not None:
                # Legacy configs don't have is_valid method
                if hasattr(config, "is_valid") and not config.is_valid():
                    logger.error(f"Configuration validation failed for {name}")
                    all_valid = False

        # Validate cross-component constraints
        if all_valid:
            combined_config = self.get_combined_config()
            is_valid, errors = ConfigValidator.validate_config(combined_config)

            if not is_valid:
                logger.error(f"Cross-component validation failed: {errors}")
                all_valid = False

        return all_valid

    def get_combined_config(self) -> Dict[str, Any]:
        """Get combined configuration from all components"""
        combined = {}

        if self.simulation_config:
            to_dict_method = getattr(self.simulation_config, "to_dict", None)
            if to_dict_method:
                combined.update(to_dict_method())

        if self.floater_config:
            to_dict_method = getattr(self.floater_config, "to_dict", None)
            if to_dict_method:
                combined.update(to_dict_method())

        if self.electrical_config:
            to_dict_method = getattr(self.electrical_config, "to_dict", None)
            if to_dict_method:
                combined.update(to_dict_method())

        if self.drivetrain_config:
            to_dict_method = getattr(self.drivetrain_config, "to_dict", None)
            if to_dict_method:
                combined.update(to_dict_method())

        if self.control_config:
            to_dict_method = getattr(self.control_config, "to_dict", None)
            if to_dict_method:
                combined.update(to_dict_method())

        return combined

    def get_warnings(self) -> List[str]:
        """Get configuration warnings"""
        combined_config = self.get_combined_config()
        return ConfigValidator.get_warnings(combined_config)

    def start_hot_reload(self) -> None:
        """Start hot-reload monitoring"""
        if not WATCHDOG_AVAILABLE:
            logger.warning("Hot-reload not available: watchdog package not installed")
            return

        if self.observer is None:
            self.observer = ObserverClass()
            self.file_handler = ConfigFileHandler(self)
            self.observer.schedule(self.file_handler, str(self.config_dir), recursive=False)
            self.observer.start()
            logger.info("Configuration hot-reload started")

    def stop_hot_reload(self) -> None:
        """Stop hot-reload monitoring"""
        if not WATCHDOG_AVAILABLE:
            return

        if self.observer is not None:
            self.observer.stop()
            self.observer.join()
            self.observer = None
            self.file_handler = None
            logger.info("Configuration hot-reload stopped")

    def reload_config(self) -> None:
        """Reload configuration from current file"""
        # This would reload from the currently active configuration file
        # For now, just reload default
        self.load_default_config()

    def get_available_configs(self) -> List[str]:
        """Get list of available configuration files"""
        configs = []
        for file in self.config_dir.glob("*.json"):
            configs.append(file.stem)
        return configs

    def update_config(self, component: str, **kwargs) -> bool:
        """Update specific configuration component"""
        config_map = {
            "simulation": self.simulation_config,
            "floater": self.floater_config,
            "electrical": self.electrical_config,
            "integrated_drivetrain": self.drivetrain_config,
            "control": self.control_config,
        }

        config = config_map.get(component)
        if config is None:
            logger.error(f"Unknown configuration component: {component}")
            return False

        try:
            if hasattr(config, 'update'):
                config.update(**kwargs)
            else:
                # Fallback for configs without update method
                for key, value in kwargs.items():
                    if hasattr(config, key):
                        setattr(config, key, value)
            return self.validate_all_configs()
        except Exception as e:
            logger.error(f"Error updating {component} configuration: {e}")
            return False

    def get_config(self, component: str):
        """Get specific configuration component by name"""
        config_map = {
            "simulation": self.simulation_config,
            "floater": self.floater_config,
            "electrical": self.electrical_config,
            "integrated_drivetrain": self.drivetrain_config,
            "control": self.control_config,
        }

        config = config_map.get(component)
        if config is None:
            logger.error(f"Unknown configuration component: {component}")
            return None

        return config

    def get_all_parameters(self) -> dict:
        """Return all configuration parameters as a dictionary."""
        result = {}
        
        if self.simulation_config:
            to_dict_method = getattr(self.simulation_config, "to_dict", None)
            result["simulation"] = to_dict_method() if to_dict_method else {}
        
        if self.floater_config:
            to_dict_method = getattr(self.floater_config, "to_dict", None)
            result["floater"] = to_dict_method() if to_dict_method else {}
        
        if self.electrical_config:
            to_dict_method = getattr(self.electrical_config, "to_dict", None)
            result["electrical"] = to_dict_method() if to_dict_method else {}
        
        if self.drivetrain_config:
            to_dict_method = getattr(self.drivetrain_config, "to_dict", None)
            result["integrated_drivetrain"] = to_dict_method() if to_dict_method else {}
        
        if self.control_config:
            to_dict_method = getattr(self.control_config, "to_dict", None)
            result["control"] = to_dict_method() if to_dict_method else {}
        
        return result
