"""
Simulation Configuration for KPP Simulator
Manages simulation parameters and performance settings
"""

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
from datetime import datetime, timedelta


class SimulationMode(Enum):
    """Simulation modes"""
    REAL_TIME = "real_time"
    FAST_FORWARD = "fast_forward"
    STEP_BY_STEP = "step_by_step"
    BATCH = "batch"
    OPTIMIZATION = "optimization"


class PhysicsAccuracy(Enum):
    """Physics accuracy levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    ULTRA = "ultra"


class PerformanceLevel(Enum):
    """Performance levels"""
    MINIMAL = "minimal"
    STANDARD = "standard"
    HIGH = "high"
    MAXIMUM = "maximum"


@dataclass
class TimeConfiguration:
    """Time configuration parameters"""
    time_step: float = 0.01  # seconds
    simulation_duration: float = 3600.0  # seconds
    real_time_factor: float = 1.0  # real-time speed factor
    max_time_step: float = 0.1  # maximum time step
    min_time_step: float = 0.001  # minimum time step
    adaptive_time_step: bool = True
    output_interval: float = 1.0  # seconds between outputs


@dataclass
class PhysicsConfiguration:
    """Physics configuration parameters"""
    gravity: float = 9.81  # m/s²
    water_density: float = 1000.0  # kg/m³
    air_density: float = 1.225  # kg/m³
    atmospheric_pressure: float = 101325.0  # Pa
    temperature: float = 20.0  # °C
    accuracy_level: PhysicsAccuracy = PhysicsAccuracy.HIGH
    enable_thermal_effects: bool = True
    enable_friction: bool = True
    enable_turbulence: bool = True


@dataclass
class PerformanceConfiguration:
    """Performance configuration parameters"""
    performance_level: PerformanceLevel = PerformanceLevel.STANDARD
    max_iterations_per_step: int = 100
    convergence_tolerance: float = 1e-6
    enable_multithreading: bool = True
    thread_count: int = 4
    memory_limit: int = 1024  # MB
    enable_caching: bool = True
    cache_size: int = 1000


@dataclass
class OutputConfiguration:
    """Output configuration parameters"""
    enable_logging: bool = True
    log_level: str = "INFO"
    enable_data_output: bool = True
    output_format: str = "CSV"
    output_directory: str = "output"
    enable_plots: bool = True
    plot_interval: float = 10.0  # seconds
    enable_video: bool = False
    video_fps: int = 30


@dataclass
class DebugConfiguration:
    """Debug configuration parameters"""
    enable_debug_mode: bool = False
    debug_level: int = 1
    enable_profiling: bool = False
    enable_memory_tracking: bool = False
    enable_error_tracking: bool = True
    max_error_count: int = 1000
    enable_validation: bool = True


class SimulationConfig:
    """
    Simulation Configuration Manager
    
    Features:
    - Time step configuration and management
    - Physics parameter settings
    - Performance optimization settings
    - Output and logging configuration
    - Debug and validation settings
    - Configuration validation and error handling
    """
    
    def __init__(self):
        """Initialize the Simulation Configuration"""
        # Configuration sections
        self.time_config = TimeConfiguration()
        self.physics_config = PhysicsConfiguration()
        self.performance_config = PerformanceConfiguration()
        self.output_config = OutputConfiguration()
        self.debug_config = DebugConfiguration()
        
        # Simulation state
        self.simulation_mode = SimulationMode.REAL_TIME
        self.is_configured = False
        self.config_version = "1.0.0"
        self.last_modified = datetime.now()
        
        # Validation rules
        self.validation_rules = {
            'time_step': {'min': 0.001, 'max': 1.0, 'type': float},
            'simulation_duration': {'min': 1.0, 'max': 86400.0, 'type': float},
            'real_time_factor': {'min': 0.1, 'max': 100.0, 'type': float},
            'gravity': {'min': 0.0, 'max': 20.0, 'type': float},
            'water_density': {'min': 800.0, 'max': 1200.0, 'type': float},
            'air_density': {'min': 0.5, 'max': 2.0, 'type': float},
            'temperature': {'min': -50.0, 'max': 100.0, 'type': float},
            'thread_count': {'min': 1, 'max': 32, 'type': int},
            'memory_limit': {'min': 64, 'max': 16384, 'type': int}
        }
        
        # Configuration history
        self.config_history: List[Dict[str, Any]] = []
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        self.logger.info("Simulation Configuration initialized")
    
    def validate_configuration(self) -> Tuple[bool, List[str]]:
        """
        Validate the current configuration
        
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        # Validate time configuration
        if not self._validate_time_config():
            errors.append("Time configuration validation failed")
        
        # Validate physics configuration
        if not self._validate_physics_config():
            errors.append("Physics configuration validation failed")
        
        # Validate performance configuration
        if not self._validate_performance_config():
            errors.append("Performance configuration validation failed")
        
        # Validate output configuration
        if not self._validate_output_config():
            errors.append("Output configuration validation failed")
        
        # Validate debug configuration
        if not self._validate_debug_config():
            errors.append("Debug configuration validation failed")
        
        is_valid = len(errors) == 0
        self.is_configured = is_valid
        
        if is_valid:
            self.logger.info("Configuration validation passed")
        else:
            self.logger.error(f"Configuration validation failed: {errors}")
        
        return is_valid, errors
    
    def _validate_time_config(self) -> bool:
        """Validate time configuration"""
        try:
            # Check time step
            if not (self.validation_rules['time_step']['min'] <= 
                   self.time_config.time_step <= 
                   self.validation_rules['time_step']['max']):
                return False
            
            # Check simulation duration
            if not (self.validation_rules['simulation_duration']['min'] <= 
                   self.time_config.simulation_duration <= 
                   self.validation_rules['simulation_duration']['max']):
                return False
            
            # Check real time factor
            if not (self.validation_rules['real_time_factor']['min'] <= 
                   self.time_config.real_time_factor <= 
                   self.validation_rules['real_time_factor']['max']):
                return False
            
            # Check time step consistency
            if self.time_config.min_time_step > self.time_config.max_time_step:
                return False
            
            if not (self.time_config.min_time_step <= 
                   self.time_config.time_step <= 
                   self.time_config.max_time_step):
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Time configuration validation error: {e}")
            return False
    
    def _validate_physics_config(self) -> bool:
        """Validate physics configuration"""
        try:
            # Check gravity
            if not (self.validation_rules['gravity']['min'] <= 
                   self.physics_config.gravity <= 
                   self.validation_rules['gravity']['max']):
                return False
            
            # Check water density
            if not (self.validation_rules['water_density']['min'] <= 
                   self.physics_config.water_density <= 
                   self.validation_rules['water_density']['max']):
                return False
            
            # Check air density
            if not (self.validation_rules['air_density']['min'] <= 
                   self.physics_config.air_density <= 
                   self.validation_rules['air_density']['max']):
                return False
            
            # Check temperature
            if not (self.validation_rules['temperature']['min'] <= 
                   self.physics_config.temperature <= 
                   self.validation_rules['temperature']['max']):
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Physics configuration validation error: {e}")
            return False
    
    def _validate_performance_config(self) -> bool:
        """Validate performance configuration"""
        try:
            # Check thread count
            if not (self.validation_rules['thread_count']['min'] <= 
                   self.performance_config.thread_count <= 
                   self.validation_rules['thread_count']['max']):
                return False
            
            # Check memory limit
            if not (self.validation_rules['memory_limit']['min'] <= 
                   self.performance_config.memory_limit <= 
                   self.validation_rules['memory_limit']['max']):
                return False
            
            # Check convergence tolerance
            if self.performance_config.convergence_tolerance <= 0:
                return False
            
            # Check max iterations
            if self.performance_config.max_iterations_per_step <= 0:
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Performance configuration validation error: {e}")
            return False
    
    def _validate_output_config(self) -> bool:
        """Validate output configuration"""
        try:
            # Check output format
            valid_formats = ['CSV', 'JSON', 'XML', 'HDF5']
            if self.output_config.output_format not in valid_formats:
                return False
            
            # Check plot interval
            if self.output_config.plot_interval <= 0:
                return False
            
            # Check video FPS
            if self.output_config.video_fps <= 0:
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Output configuration validation error: {e}")
            return False
    
    def _validate_debug_config(self) -> bool:
        """Validate debug configuration"""
        try:
            # Check debug level
            if not (0 <= self.debug_config.debug_level <= 5):
                return False
            
            # Check max error count
            if self.debug_config.max_error_count <= 0:
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Debug configuration validation error: {e}")
            return False
    
    def set_time_configuration(self, **kwargs):
        """Set time configuration parameters"""
        for key, value in kwargs.items():
            if hasattr(self.time_config, key):
                setattr(self.time_config, key, value)
                self.logger.info(f"Time configuration updated: {key} = {value}")
        
        self.last_modified = datetime.now()
    
    def set_physics_configuration(self, **kwargs):
        """Set physics configuration parameters"""
        for key, value in kwargs.items():
            if hasattr(self.physics_config, key):
                setattr(self.physics_config, key, value)
                self.logger.info(f"Physics configuration updated: {key} = {value}")
        
        self.last_modified = datetime.now()
    
    def set_performance_configuration(self, **kwargs):
        """Set performance configuration parameters"""
        for key, value in kwargs.items():
            if hasattr(self.performance_config, key):
                setattr(self.performance_config, key, value)
                self.logger.info(f"Performance configuration updated: {key} = {value}")
        
        self.last_modified = datetime.now()
    
    def set_output_configuration(self, **kwargs):
        """Set output configuration parameters"""
        for key, value in kwargs.items():
            if hasattr(self.output_config, key):
                setattr(self.output_config, key, value)
                self.logger.info(f"Output configuration updated: {key} = {value}")
        
        self.last_modified = datetime.now()
    
    def set_debug_configuration(self, **kwargs):
        """Set debug configuration parameters"""
        for key, value in kwargs.items():
            if hasattr(self.debug_config, key):
                setattr(self.debug_config, key, value)
                self.logger.info(f"Debug configuration updated: {key} = {value}")
        
        self.last_modified = datetime.now()
    
    def set_simulation_mode(self, mode: SimulationMode):
        """Set simulation mode"""
        self.simulation_mode = mode
        self.logger.info(f"Simulation mode set to: {mode.value}")
    
    def get_configuration_summary(self) -> Dict[str, Any]:
        """Get configuration summary"""
        return {
            'version': self.config_version,
            'last_modified': self.last_modified.isoformat(),
            'is_configured': self.is_configured,
            'simulation_mode': self.simulation_mode.value,
            'time_config': {
                'time_step': self.time_config.time_step,
                'simulation_duration': self.time_config.simulation_duration,
                'real_time_factor': self.time_config.real_time_factor,
                'adaptive_time_step': self.time_config.adaptive_time_step
            },
            'physics_config': {
                'accuracy_level': self.physics_config.accuracy_level.value,
                'gravity': self.physics_config.gravity,
                'water_density': self.physics_config.water_density,
                'temperature': self.physics_config.temperature,
                'enable_thermal_effects': self.physics_config.enable_thermal_effects
            },
            'performance_config': {
                'performance_level': self.performance_config.performance_level.value,
                'thread_count': self.performance_config.thread_count,
                'memory_limit': self.performance_config.memory_limit,
                'enable_multithreading': self.performance_config.enable_multithreading
            },
            'output_config': {
                'enable_logging': self.output_config.enable_logging,
                'log_level': self.output_config.log_level,
                'output_format': self.output_config.output_format,
                'enable_plots': self.output_config.enable_plots
            },
            'debug_config': {
                'enable_debug_mode': self.debug_config.enable_debug_mode,
                'debug_level': self.debug_config.debug_level,
                'enable_validation': self.debug_config.enable_validation
            }
        }
    
    def save_configuration(self, filepath: str) -> bool:
        """Save configuration to file"""
        try:
            import json
            
            config_data = {
                'version': self.config_version,
                'last_modified': self.last_modified.isoformat(),
                'simulation_mode': self.simulation_mode.value,
                'time_config': self.time_config.__dict__,
                'physics_config': {
                    **self.physics_config.__dict__,
                    'accuracy_level': self.physics_config.accuracy_level.value
                },
                'performance_config': {
                    **self.performance_config.__dict__,
                    'performance_level': self.performance_config.performance_level.value
                },
                'output_config': self.output_config.__dict__,
                'debug_config': self.debug_config.__dict__
            }
            
            with open(filepath, 'w') as f:
                json.dump(config_data, f, indent=2)
            
            self.logger.info(f"Configuration saved to: {filepath}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save configuration: {e}")
            return False
    
    def load_configuration(self, filepath: str) -> bool:
        """Load configuration from file"""
        try:
            import json
            
            with open(filepath, 'r') as f:
                config_data = json.load(f)
            
            # Load simulation mode
            if 'simulation_mode' in config_data:
                self.simulation_mode = SimulationMode(config_data['simulation_mode'])
            
            # Load time configuration
            if 'time_config' in config_data:
                for key, value in config_data['time_config'].items():
                    if hasattr(self.time_config, key):
                        setattr(self.time_config, key, value)
            
            # Load physics configuration
            if 'physics_config' in config_data:
                for key, value in config_data['physics_config'].items():
                    if key == 'accuracy_level':
                        self.physics_config.accuracy_level = PhysicsAccuracy(value)
                    elif hasattr(self.physics_config, key):
                        setattr(self.physics_config, key, value)
            
            # Load performance configuration
            if 'performance_config' in config_data:
                for key, value in config_data['performance_config'].items():
                    if key == 'performance_level':
                        self.performance_config.performance_level = PerformanceLevel(value)
                    elif hasattr(self.performance_config, key):
                        setattr(self.performance_config, key, value)
            
            # Load output configuration
            if 'output_config' in config_data:
                for key, value in config_data['output_config'].items():
                    if hasattr(self.output_config, key):
                        setattr(self.output_config, key, value)
            
            # Load debug configuration
            if 'debug_config' in config_data:
                for key, value in config_data['debug_config'].items():
                    if hasattr(self.debug_config, key):
                        setattr(self.debug_config, key, value)
            
            # Validate loaded configuration
            is_valid, errors = self.validate_configuration()
            if not is_valid:
                self.logger.warning(f"Loaded configuration has validation errors: {errors}")
            
            self.last_modified = datetime.now()
            self.logger.info(f"Configuration loaded from: {filepath}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to load configuration: {e}")
            return False
    
    def reset_to_defaults(self):
        """Reset configuration to default values"""
        self.time_config = TimeConfiguration()
        self.physics_config = PhysicsConfiguration()
        self.performance_config = PerformanceConfiguration()
        self.output_config = OutputConfiguration()
        self.debug_config = DebugConfiguration()
        self.simulation_mode = SimulationMode.REAL_TIME
        
        self.last_modified = datetime.now()
        self.logger.info("Configuration reset to defaults")
    
    def get_validation_rules(self) -> Dict[str, Any]:
        """Get validation rules"""
        return self.validation_rules.copy()
    
    def add_validation_rule(self, parameter: str, rule: Dict[str, Any]):
        """Add a custom validation rule"""
        self.validation_rules[parameter] = rule
        self.logger.info(f"Validation rule added for parameter: {parameter}")
    
    def clear_configuration_history(self):
        """Clear configuration history"""
        self.config_history.clear()
        self.logger.info("Configuration history cleared") 