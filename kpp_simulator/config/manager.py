"""
Configuration Manager for KPP Simulator
Manages all configuration components and system integration
"""

import logging
import os
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any, Union
import json
import yaml
from datetime import datetime, timedelta

from .components.simulation_config import SimulationConfig
from .components.floater_config import FloaterConfig
from .core.base_config import BaseConfig
from .core.schema import ConfigSchema


class ConfigFormat(Enum):
    """Configuration file formats"""
    JSON = "json"
    YAML = "yaml"
    INI = "ini"
    TOML = "toml"


class ConfigStatus(Enum):
    """Configuration status states"""
    VALID = "valid"
    INVALID = "invalid"
    LOADING = "loading"
    SAVING = "saving"
    ERROR = "error"


@dataclass
class ConfigChange:
    """Configuration change record"""
    timestamp: datetime
    component: str
    parameter: str
    old_value: Any
    new_value: Any
    user: str
    reason: str


@dataclass
class ConfigValidationResult:
    """Configuration validation result"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    component_results: Dict[str, Tuple[bool, List[str]]]


class ConfigManager:
    """
    Configuration Manager for KPP Simulator
    
    Features:
    - Centralized configuration management
    - Multi-format configuration loading/saving
    - Configuration validation and error handling
    - Change tracking and history
    - Component coordination and integration
    - Performance optimization and caching
    """
    
    def __init__(self, config_directory: str = "config"):
        """
        Initialize the Configuration Manager
        
        Args:
            config_directory: Directory for configuration files
        """
        self.config_directory = config_directory
        self.base_config = BaseConfig()
        self.schema = ConfigSchema()
        
        # Component configurations
        self.simulation_config = SimulationConfig()
        self.floater_configs: Dict[str, FloaterConfig] = {}
        
        # Manager state
        self.is_active = False
        self.status = ConfigStatus.VALID
        self.config_format = ConfigFormat.JSON
        self.auto_save = True
        self.backup_enabled = True
        self.max_backups = 10
        
        # Change tracking
        self.config_changes: List[ConfigChange] = []
        self.change_callbacks: Dict[str, List[callable]] = {}
        
        # Performance tracking
        self.performance_metrics = {
            'load_time': 0.0,
            'save_time': 0.0,
            'validation_time': 0.0,
            'total_changes': 0,
            'last_backup': None
        }
        
        # Cache
        self.config_cache: Dict[str, Any] = {}
        self.cache_enabled = True
        self.cache_ttl = 300  # seconds
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        self.logger.info("Configuration Manager initialized")
        
        # Ensure config directory exists
        os.makedirs(config_directory, exist_ok=True)
    
    def start(self):
        """Start the configuration manager"""
        self.is_active = True
        self.logger.info("Configuration Manager started")
    
    def stop(self):
        """Stop the configuration manager"""
        self.is_active = False
        self.logger.info("Configuration Manager stopped")
    
    def load_all_configurations(self) -> bool:
        """Load all configuration files"""
        try:
            self.status = ConfigStatus.LOADING
            start_time = datetime.now()
            
            # Load simulation configuration
            sim_config_path = os.path.join(self.config_directory, "simulation_config.json")
            if os.path.exists(sim_config_path):
                if not self.simulation_config.load_configuration(sim_config_path):
                    self.logger.warning("Failed to load simulation configuration")
            
            # Load floater configurations
            floater_config_dir = os.path.join(self.config_directory, "floaters")
            if os.path.exists(floater_config_dir):
                for filename in os.listdir(floater_config_dir):
                    if filename.endswith('.json'):
                        floater_id = filename.replace('.json', '')
                        floater_config = FloaterConfig(floater_id)
                        config_path = os.path.join(floater_config_dir, filename)
                        if floater_config.load_configuration(config_path):
                            self.floater_configs[floater_id] = floater_config
                            self.logger.info(f"Loaded floater configuration: {floater_id}")
            
            # Validate all configurations
            is_valid, errors = self.validate_all_configurations()
            if not is_valid:
                self.logger.warning(f"Configuration validation warnings: {errors}")
            
            # Update performance metrics
            end_time = datetime.now()
            self.performance_metrics['load_time'] = (end_time - start_time).total_seconds()
            
            self.status = ConfigStatus.VALID
            self.logger.info("All configurations loaded successfully")
            return True
            
        except Exception as e:
            self.status = ConfigStatus.ERROR
            self.logger.error(f"Failed to load configurations: {e}")
            return False
    
    def save_all_configurations(self) -> bool:
        """Save all configuration files"""
        try:
            self.status = ConfigStatus.SAVING
            start_time = datetime.now()
            
            # Create backup if enabled
            if self.backup_enabled:
                self._create_backup()
            
            # Save simulation configuration
            sim_config_path = os.path.join(self.config_directory, "simulation_config.json")
            if not self.simulation_config.save_configuration(sim_config_path):
                self.logger.error("Failed to save simulation configuration")
                return False
            
            # Save floater configurations
            floater_config_dir = os.path.join(self.config_directory, "floaters")
            os.makedirs(floater_config_dir, exist_ok=True)
            
            for floater_id, floater_config in self.floater_configs.items():
                config_path = os.path.join(floater_config_dir, f"{floater_id}.json")
                if not floater_config.save_configuration(config_path):
                    self.logger.error(f"Failed to save floater configuration: {floater_id}")
                    return False
            
            # Update performance metrics
            end_time = datetime.now()
            self.performance_metrics['save_time'] = (end_time - start_time).total_seconds()
            self.performance_metrics['last_backup'] = datetime.now()
            
            self.status = ConfigStatus.VALID
            self.logger.info("All configurations saved successfully")
            return True
            
        except Exception as e:
            self.status = ConfigStatus.ERROR
            self.logger.error(f"Failed to save configurations: {e}")
            return False
    
    def validate_all_configurations(self) -> Tuple[bool, List[str]]:
        """Validate all configurations"""
        try:
            start_time = datetime.now()
            all_errors = []
            component_results = {}
            
            # Validate simulation configuration
            sim_valid, sim_errors = self.simulation_config.validate_configuration()
            component_results['simulation'] = (sim_valid, sim_errors)
            all_errors.extend(sim_errors)
            
            # Validate floater configurations
            for floater_id, floater_config in self.floater_configs.items():
                floater_valid, floater_errors = floater_config.validate_configuration()
                component_results[f'floater_{floater_id}'] = (floater_valid, floater_errors)
                all_errors.extend([f"{floater_id}: {error}" for error in floater_errors])
            
            # Validate base configuration
            base_valid, base_errors = self.base_config.validate_configuration()
            component_results['base'] = (base_valid, base_errors)
            all_errors.extend(base_errors)
            
            # Update performance metrics
            end_time = datetime.now()
            self.performance_metrics['validation_time'] = (end_time - start_time).total_seconds()
            
            is_valid = len(all_errors) == 0
            return is_valid, all_errors
            
        except Exception as e:
            self.logger.error(f"Configuration validation error: {e}")
            return False, [str(e)]
    
    def get_configuration_summary(self) -> Dict[str, Any]:
        """Get comprehensive configuration summary"""
        summary = {
            'manager_status': {
                'is_active': self.is_active,
                'status': self.status.value,
                'config_format': self.config_format.value,
                'auto_save': self.auto_save,
                'backup_enabled': self.backup_enabled
            },
            'performance_metrics': self.performance_metrics.copy(),
            'simulation_config': self.simulation_config.get_configuration_summary(),
            'floater_configs': {},
            'validation_status': {}
        }
        
        # Add floater configurations
        for floater_id, floater_config in self.floater_configs.items():
            summary['floater_configs'][floater_id] = floater_config.get_configuration_summary()
        
        # Add validation status
        is_valid, errors = self.validate_all_configurations()
        summary['validation_status'] = {
            'is_valid': is_valid,
            'error_count': len(errors),
            'errors': errors[:10]  # Limit to first 10 errors
        }
        
        return summary
    
    def create_floater_config(self, floater_id: str) -> FloaterConfig:
        """Create a new floater configuration"""
        if floater_id in self.floater_configs:
            self.logger.warning(f"Floater configuration {floater_id} already exists")
            return self.floater_configs[floater_id]
        
        floater_config = FloaterConfig(floater_id)
        self.floater_configs[floater_id] = floater_config
        
        self.logger.info(f"Created new floater configuration: {floater_id}")
        return floater_config
    
    def remove_floater_config(self, floater_id: str) -> bool:
        """Remove a floater configuration"""
        if floater_id not in self.floater_configs:
            self.logger.warning(f"Floater configuration {floater_id} not found")
            return False
        
        # Remove from memory
        del self.floater_configs[floater_id]
        
        # Remove file if it exists
        floater_config_dir = os.path.join(self.config_directory, "floaters")
        config_path = os.path.join(floater_config_dir, f"{floater_id}.json")
        if os.path.exists(config_path):
            os.remove(config_path)
        
        self.logger.info(f"Removed floater configuration: {floater_id}")
        return True
    
    def get_floater_config(self, floater_id: str) -> Optional[FloaterConfig]:
        """Get a floater configuration"""
        return self.floater_configs.get(floater_id)
    
    def list_floater_configs(self) -> List[str]:
        """List all floater configuration IDs"""
        return list(self.floater_configs.keys())
    
    def update_simulation_config(self, **kwargs) -> bool:
        """Update simulation configuration"""
        try:
            # Record changes
            for key, value in kwargs.items():
                old_value = getattr(self.simulation_config, key, None)
                self._record_change('simulation', key, old_value, value, 'system', 'configuration_update')
            
            # Apply changes
            for key, value in kwargs.items():
                if hasattr(self.simulation_config, key):
                    setattr(self.simulation_config, key, value)
            
            # Auto-save if enabled
            if self.auto_save:
                self.save_all_configurations()
            
            self.logger.info("Simulation configuration updated")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to update simulation configuration: {e}")
            return False
    
    def update_floater_config(self, floater_id: str, **kwargs) -> bool:
        """Update floater configuration"""
        if floater_id not in self.floater_configs:
            self.logger.error(f"Floater configuration {floater_id} not found")
            return False
        
        try:
            floater_config = self.floater_configs[floater_id]
            
            # Record changes
            for key, value in kwargs.items():
                old_value = getattr(floater_config, key, None)
                self._record_change(f'floater_{floater_id}', key, old_value, value, 'system', 'configuration_update')
            
            # Apply changes
            for key, value in kwargs.items():
                if hasattr(floater_config, key):
                    setattr(floater_config, key, value)
            
            # Auto-save if enabled
            if self.auto_save:
                self.save_all_configurations()
            
            self.logger.info(f"Floater configuration {floater_id} updated")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to update floater configuration {floater_id}: {e}")
            return False
    
    def _record_change(self, component: str, parameter: str, old_value: Any, new_value: Any, user: str, reason: str):
        """Record a configuration change"""
        change = ConfigChange(
            timestamp=datetime.now(),
            component=component,
            parameter=parameter,
            old_value=old_value,
            new_value=new_value,
            user=user,
            reason=reason
        )
        
        self.config_changes.append(change)
        self.performance_metrics['total_changes'] += 1
        
        # Limit change history
        if len(self.config_changes) > 1000:
            self.config_changes.pop(0)
        
        # Trigger callbacks
        if component in self.change_callbacks:
            for callback in self.change_callbacks[component]:
                try:
                    callback(change)
                except Exception as e:
                    self.logger.error(f"Change callback error: {e}")
    
    def _create_backup(self):
        """Create configuration backup"""
        try:
            backup_dir = os.path.join(self.config_directory, "backups")
            os.makedirs(backup_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = os.path.join(backup_dir, f"config_backup_{timestamp}")
            os.makedirs(backup_path, exist_ok=True)
            
            # Copy current configuration files
            import shutil
            
            # Copy simulation config
            sim_config_path = os.path.join(self.config_directory, "simulation_config.json")
            if os.path.exists(sim_config_path):
                shutil.copy2(sim_config_path, backup_path)
            
            # Copy floater configs
            floater_config_dir = os.path.join(self.config_directory, "floaters")
            if os.path.exists(floater_config_dir):
                backup_floaters_dir = os.path.join(backup_path, "floaters")
                shutil.copytree(floater_config_dir, backup_floaters_dir)
            
            # Clean old backups
            self._cleanup_old_backups(backup_dir)
            
            self.logger.info(f"Configuration backup created: {backup_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to create backup: {e}")
    
    def _cleanup_old_backups(self, backup_dir: str):
        """Clean up old backup files"""
        try:
            backups = []
            for item in os.listdir(backup_dir):
                item_path = os.path.join(backup_dir, item)
                if os.path.isdir(item_path) and item.startswith("config_backup_"):
                    backups.append((item_path, os.path.getctime(item_path)))
            
            # Sort by creation time (oldest first)
            backups.sort(key=lambda x: x[1])
            
            # Remove old backups
            while len(backups) > self.max_backups:
                oldest_backup = backups.pop(0)
                import shutil
                shutil.rmtree(oldest_backup[0])
                self.logger.info(f"Removed old backup: {oldest_backup[0]}")
                
        except Exception as e:
            self.logger.error(f"Failed to cleanup old backups: {e}")
    
    def register_change_callback(self, component: str, callback: callable):
        """Register a callback for configuration changes"""
        if component not in self.change_callbacks:
            self.change_callbacks[component] = []
        
        self.change_callbacks[component].append(callback)
        self.logger.info(f"Registered change callback for component: {component}")
    
    def unregister_change_callback(self, component: str, callback: callable):
        """Unregister a configuration change callback"""
        if component in self.change_callbacks:
            try:
                self.change_callbacks[component].remove(callback)
                self.logger.info(f"Unregistered change callback for component: {component}")
            except ValueError:
                self.logger.warning(f"Callback not found for component: {component}")
    
    def get_change_history(self, component: Optional[str] = None, 
                          since: Optional[datetime] = None) -> List[ConfigChange]:
        """Get configuration change history"""
        changes = self.config_changes
        
        # Filter by component
        if component:
            changes = [c for c in changes if c.component == component]
        
        # Filter by time
        if since:
            changes = [c for c in changes if c.timestamp >= since]
        
        return changes
    
    def clear_change_history(self):
        """Clear configuration change history"""
        self.config_changes.clear()
        self.performance_metrics['total_changes'] = 0
        self.logger.info("Configuration change history cleared")
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics"""
        return self.performance_metrics.copy()
    
    def reset_performance_metrics(self):
        """Reset performance metrics"""
        self.performance_metrics = {
            'load_time': 0.0,
            'save_time': 0.0,
            'validation_time': 0.0,
            'total_changes': 0,
            'last_backup': None
        }
        self.logger.info("Performance metrics reset") 