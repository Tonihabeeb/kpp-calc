"""
Floater Configuration for KPP Simulator
Manages floater physical properties and operational parameters
"""

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any
import numpy as np


class FloaterType(Enum):
    """Floater types"""
    STANDARD = "standard"
    ENHANCED = "enhanced"
    PREMIUM = "premium"
    CUSTOM = "custom"


class MaterialType(Enum):
    """Floater material types"""
    STEEL = "steel"
    ALUMINUM = "aluminum"
    COMPOSITE = "composite"
    PLASTIC = "plastic"
    CERAMIC = "ceramic"


class FloaterState(Enum):
    """Floater operational states"""
    EMPTY = "empty"
    FILLING = "filling"
    FULL = "full"
    VENTING = "venting"
    MAINTENANCE = "maintenance"
    ERROR = "error"


@dataclass
class PhysicalProperties:
    """Floater physical properties"""
    mass_empty: float = 1000.0  # kg
    mass_full: float = 2000.0  # kg
    volume: float = 1.0  # m³
    diameter: float = 1.0  # m
    height: float = 1.0  # m
    material: MaterialType = MaterialType.STEEL
    density: float = 7850.0  # kg/m³
    thermal_conductivity: float = 50.0  # W/(m·K)
    specific_heat: float = 460.0  # J/(kg·K)
    expansion_coefficient: float = 12e-6  # 1/K


@dataclass
class OperationalParameters:
    """Floater operational parameters"""
    max_pressure: float = 10.0  # bar
    min_pressure: float = 0.1  # bar
    max_temperature: float = 80.0  # °C
    min_temperature: float = -20.0  # °C
    fill_rate: float = 0.1  # m³/s
    vent_rate: float = 0.1  # m³/s
    max_velocity: float = 5.0  # m/s
    max_acceleration: float = 10.0  # m/s²
    cycle_time: float = 60.0  # seconds


@dataclass
class PerformanceSettings:
    """Floater performance settings"""
    efficiency_target: float = 0.95
    response_time: float = 1.0  # seconds
    accuracy_threshold: float = 0.01  # m
    stability_margin: float = 0.1
    wear_factor: float = 1e-6  # per cycle
    maintenance_interval: int = 1000  # cycles
    performance_degradation: float = 0.001  # per hour


@dataclass
class SafetyParameters:
    """Floater safety parameters"""
    pressure_safety_factor: float = 1.5
    temperature_safety_factor: float = 1.2
    velocity_safety_factor: float = 1.3
    emergency_shutdown_time: float = 2.0  # seconds
    max_cycles_before_maintenance: int = 5000
    safety_margin: float = 0.2
    enable_safety_interlocks: bool = True


class FloaterConfig:
    """
    Floater Configuration Manager
    
    Features:
    - Physical properties management
    - Operational parameter settings
    - Performance optimization settings
    - Safety parameter configuration
    - Validation rules and error handling
    - Configuration persistence and loading
    """
    
    def __init__(self, floater_id: str = "floater_001"):
        """
        Initialize the Floater Configuration
        
        Args:
            floater_id: Unique identifier for the floater
        """
        self.floater_id = floater_id
        self.floater_type = FloaterType.STANDARD
        
        # Configuration sections
        self.physical_properties = PhysicalProperties()
        self.operational_parameters = OperationalParameters()
        self.performance_settings = PerformanceSettings()
        self.safety_parameters = SafetyParameters()
        
        # Configuration state
        self.is_configured = False
        self.config_version = "1.0.0"
        self.last_modified = datetime.now()
        
        # Validation rules
        self.validation_rules = {
            'mass_empty': {'min': 100.0, 'max': 10000.0, 'type': float},
            'mass_full': {'min': 200.0, 'max': 20000.0, 'type': float},
            'volume': {'min': 0.1, 'max': 100.0, 'type': float},
            'diameter': {'min': 0.1, 'max': 10.0, 'type': float},
            'height': {'min': 0.1, 'max': 10.0, 'type': float},
            'density': {'min': 1000.0, 'max': 20000.0, 'type': float},
            'max_pressure': {'min': 0.1, 'max': 100.0, 'type': float},
            'min_pressure': {'min': 0.01, 'max': 10.0, 'type': float},
            'max_temperature': {'min': 0.0, 'max': 200.0, 'type': float},
            'min_temperature': {'min': -50.0, 'max': 100.0, 'type': float},
            'fill_rate': {'min': 0.01, 'max': 1.0, 'type': float},
            'vent_rate': {'min': 0.01, 'max': 1.0, 'type': float},
            'max_velocity': {'min': 0.1, 'max': 20.0, 'type': float},
            'max_acceleration': {'min': 1.0, 'max': 50.0, 'type': float},
            'cycle_time': {'min': 10.0, 'max': 600.0, 'type': float},
            'efficiency_target': {'min': 0.5, 'max': 1.0, 'type': float},
            'response_time': {'min': 0.1, 'max': 10.0, 'type': float},
            'accuracy_threshold': {'min': 0.001, 'max': 0.1, 'type': float},
            'stability_margin': {'min': 0.01, 'max': 0.5, 'type': float},
            'wear_factor': {'min': 1e-8, 'max': 1e-4, 'type': float},
            'maintenance_interval': {'min': 100, 'max': 10000, 'type': int},
            'performance_degradation': {'min': 1e-6, 'max': 1e-2, 'type': float},
            'pressure_safety_factor': {'min': 1.1, 'max': 3.0, 'type': float},
            'temperature_safety_factor': {'min': 1.1, 'max': 2.0, 'type': float},
            'velocity_safety_factor': {'min': 1.1, 'max': 2.0, 'type': float},
            'emergency_shutdown_time': {'min': 0.5, 'max': 10.0, 'type': float},
            'max_cycles_before_maintenance': {'min': 100, 'max': 20000, 'type': int},
            'safety_margin': {'min': 0.05, 'max': 0.5, 'type': float}
        }
        
        # Configuration history
        self.config_history: List[Dict[str, Any]] = []
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"Floater Configuration initialized for {floater_id}")
    
    def validate_configuration(self) -> Tuple[bool, List[str]]:
        """
        Validate the current configuration
        
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        # Validate physical properties
        if not self._validate_physical_properties():
            errors.append("Physical properties validation failed")
        
        # Validate operational parameters
        if not self._validate_operational_parameters():
            errors.append("Operational parameters validation failed")
        
        # Validate performance settings
        if not self._validate_performance_settings():
            errors.append("Performance settings validation failed")
        
        # Validate safety parameters
        if not self._validate_safety_parameters():
            errors.append("Safety parameters validation failed")
        
        # Validate consistency
        if not self._validate_consistency():
            errors.append("Configuration consistency validation failed")
        
        is_valid = len(errors) == 0
        self.is_configured = is_valid
        
        if is_valid:
            self.logger.info("Floater configuration validation passed")
        else:
            self.logger.error(f"Floater configuration validation failed: {errors}")
        
        return is_valid, errors
    
    def _validate_physical_properties(self) -> bool:
        """Validate physical properties"""
        try:
            props = self.physical_properties
            
            # Check mass consistency
            if props.mass_full <= props.mass_empty:
                return False
            
            # Check volume consistency
            if props.volume <= 0:
                return False
            
            # Check dimensions
            if props.diameter <= 0 or props.height <= 0:
                return False
            
            # Check density
            if props.density <= 0:
                return False
            
            # Check thermal properties
            if props.thermal_conductivity <= 0 or props.specific_heat <= 0:
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Physical properties validation error: {e}")
            return False
    
    def _validate_operational_parameters(self) -> bool:
        """Validate operational parameters"""
        try:
            params = self.operational_parameters
            
            # Check pressure range
            if params.min_pressure >= params.max_pressure:
                return False
            
            # Check temperature range
            if params.min_temperature >= params.max_temperature:
                return False
            
            # Check flow rates
            if params.fill_rate <= 0 or params.vent_rate <= 0:
                return False
            
            # Check velocity and acceleration
            if params.max_velocity <= 0 or params.max_acceleration <= 0:
                return False
            
            # Check cycle time
            if params.cycle_time <= 0:
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Operational parameters validation error: {e}")
            return False
    
    def _validate_performance_settings(self) -> bool:
        """Validate performance settings"""
        try:
            settings = self.performance_settings
            
            # Check efficiency target
            if not (0 < settings.efficiency_target <= 1):
                return False
            
            # Check response time
            if settings.response_time <= 0:
                return False
            
            # Check accuracy threshold
            if settings.accuracy_threshold <= 0:
                return False
            
            # Check stability margin
            if not (0 < settings.stability_margin < 1):
                return False
            
            # Check wear factor
            if settings.wear_factor <= 0:
                return False
            
            # Check maintenance interval
            if settings.maintenance_interval <= 0:
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Performance settings validation error: {e}")
            return False
    
    def _validate_safety_parameters(self) -> bool:
        """Validate safety parameters"""
        try:
            safety = self.safety_parameters
            
            # Check safety factors
            if (safety.pressure_safety_factor <= 1 or 
                safety.temperature_safety_factor <= 1 or 
                safety.velocity_safety_factor <= 1):
                return False
            
            # Check shutdown time
            if safety.emergency_shutdown_time <= 0:
                return False
            
            # Check maintenance cycles
            if safety.max_cycles_before_maintenance <= 0:
                return False
            
            # Check safety margin
            if not (0 < safety.safety_margin < 1):
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Safety parameters validation error: {e}")
            return False
    
    def _validate_consistency(self) -> bool:
        """Validate configuration consistency"""
        try:
            # Check that mass_full > mass_empty
            if self.physical_properties.mass_full <= self.physical_properties.mass_empty:
                return False
            
            # Check that max_pressure > min_pressure
            if self.operational_parameters.max_pressure <= self.operational_parameters.min_pressure:
                return False
            
            # Check that max_temperature > min_temperature
            if self.operational_parameters.max_temperature <= self.operational_parameters.min_temperature:
                return False
            
            # Check that maintenance interval is reasonable
            if self.performance_settings.maintenance_interval > self.safety_parameters.max_cycles_before_maintenance:
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Configuration consistency validation error: {e}")
            return False
    
    def set_physical_properties(self, **kwargs):
        """Set physical properties"""
        for key, value in kwargs.items():
            if hasattr(self.physical_properties, key):
                setattr(self.physical_properties, key, value)
                self.logger.info(f"Physical property updated: {key} = {value}")
        
        self.last_modified = datetime.now()
    
    def set_operational_parameters(self, **kwargs):
        """Set operational parameters"""
        for key, value in kwargs.items():
            if hasattr(self.operational_parameters, key):
                setattr(self.operational_parameters, key, value)
                self.logger.info(f"Operational parameter updated: {key} = {value}")
        
        self.last_modified = datetime.now()
    
    def set_performance_settings(self, **kwargs):
        """Set performance settings"""
        for key, value in kwargs.items():
            if hasattr(self.performance_settings, key):
                setattr(self.performance_settings, key, value)
                self.logger.info(f"Performance setting updated: {key} = {value}")
        
        self.last_modified = datetime.now()
    
    def set_safety_parameters(self, **kwargs):
        """Set safety parameters"""
        for key, value in kwargs.items():
            if hasattr(self.safety_parameters, key):
                setattr(self.safety_parameters, key, value)
                self.logger.info(f"Safety parameter updated: {key} = {value}")
        
        self.last_modified = datetime.now()
    
    def set_floater_type(self, floater_type: FloaterType):
        """Set floater type"""
        self.floater_type = floater_type
        self.logger.info(f"Floater type set to: {floater_type.value}")
    
    def set_material(self, material: MaterialType):
        """Set floater material"""
        self.physical_properties.material = material
        
        # Update density based on material
        material_densities = {
            MaterialType.STEEL: 7850.0,
            MaterialType.ALUMINUM: 2700.0,
            MaterialType.COMPOSITE: 1600.0,
            MaterialType.PLASTIC: 1200.0,
            MaterialType.CERAMIC: 4000.0
        }
        
        if material in material_densities:
            self.physical_properties.density = material_densities[material]
        
        self.logger.info(f"Material set to: {material.value}")
    
    def calculate_buoyancy_force(self, water_density: float = 1000.0) -> float:
        """Calculate buoyancy force"""
        volume = self.physical_properties.volume
        return water_density * volume * 9.81  # N
    
    def calculate_mass_ratio(self) -> float:
        """Calculate mass ratio (full/empty)"""
        return self.physical_properties.mass_full / self.physical_properties.mass_empty
    
    def calculate_pressure_rating(self) -> float:
        """Calculate pressure rating with safety factor"""
        return self.operational_parameters.max_pressure * self.safety_parameters.pressure_safety_factor
    
    def calculate_thermal_capacity(self) -> float:
        """Calculate thermal capacity"""
        mass = self.physical_properties.mass_empty
        specific_heat = self.physical_properties.specific_heat
        return mass * specific_heat  # J/K
    
    def get_configuration_summary(self) -> Dict[str, Any]:
        """Get configuration summary"""
        return {
            'floater_id': self.floater_id,
            'floater_type': self.floater_type.value,
            'version': self.config_version,
            'last_modified': self.last_modified.isoformat(),
            'is_configured': self.is_configured,
            'physical_properties': {
                'mass_empty': self.physical_properties.mass_empty,
                'mass_full': self.physical_properties.mass_full,
                'volume': self.physical_properties.volume,
                'diameter': self.physical_properties.diameter,
                'height': self.physical_properties.height,
                'material': self.physical_properties.material.value,
                'density': self.physical_properties.density
            },
            'operational_parameters': {
                'max_pressure': self.operational_parameters.max_pressure,
                'min_pressure': self.operational_parameters.min_pressure,
                'max_temperature': self.operational_parameters.max_temperature,
                'min_temperature': self.operational_parameters.min_temperature,
                'fill_rate': self.operational_parameters.fill_rate,
                'vent_rate': self.operational_parameters.vent_rate,
                'cycle_time': self.operational_parameters.cycle_time
            },
            'performance_settings': {
                'efficiency_target': self.performance_settings.efficiency_target,
                'response_time': self.performance_settings.response_time,
                'accuracy_threshold': self.performance_settings.accuracy_threshold,
                'maintenance_interval': self.performance_settings.maintenance_interval
            },
            'safety_parameters': {
                'pressure_safety_factor': self.safety_parameters.pressure_safety_factor,
                'temperature_safety_factor': self.safety_parameters.temperature_safety_factor,
                'emergency_shutdown_time': self.safety_parameters.emergency_shutdown_time,
                'enable_safety_interlocks': self.safety_parameters.enable_safety_interlocks
            },
            'calculated_properties': {
                'buoyancy_force': self.calculate_buoyancy_force(),
                'mass_ratio': self.calculate_mass_ratio(),
                'pressure_rating': self.calculate_pressure_rating(),
                'thermal_capacity': self.calculate_thermal_capacity()
            }
        }
    
    def save_configuration(self, filepath: str) -> bool:
        """Save configuration to file"""
        try:
            import json
            
            config_data = {
                'floater_id': self.floater_id,
                'version': self.config_version,
                'last_modified': self.last_modified.isoformat(),
                'floater_type': self.floater_type.value,
                'physical_properties': self.physical_properties.__dict__,
                'operational_parameters': self.operational_parameters.__dict__,
                'performance_settings': self.performance_settings.__dict__,
                'safety_parameters': self.safety_parameters.__dict__
            }
            
            # Convert enums to strings
            config_data['physical_properties']['material'] = self.physical_properties.material.value
            
            with open(filepath, 'w') as f:
                json.dump(config_data, f, indent=2)
            
            self.logger.info(f"Floater configuration saved to: {filepath}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save floater configuration: {e}")
            return False
    
    def load_configuration(self, filepath: str) -> bool:
        """Load configuration from file"""
        try:
            import json
            
            with open(filepath, 'r') as f:
                config_data = json.load(f)
            
            # Load basic properties
            if 'floater_id' in config_data:
                self.floater_id = config_data['floater_id']
            
            if 'floater_type' in config_data:
                self.floater_type = FloaterType(config_data['floater_type'])
            
            # Load physical properties
            if 'physical_properties' in config_data:
                for key, value in config_data['physical_properties'].items():
                    if key == 'material':
                        self.physical_properties.material = MaterialType(value)
                    elif hasattr(self.physical_properties, key):
                        setattr(self.physical_properties, key, value)
            
            # Load operational parameters
            if 'operational_parameters' in config_data:
                for key, value in config_data['operational_parameters'].items():
                    if hasattr(self.operational_parameters, key):
                        setattr(self.operational_parameters, key, value)
            
            # Load performance settings
            if 'performance_settings' in config_data:
                for key, value in config_data['performance_settings'].items():
                    if hasattr(self.performance_settings, key):
                        setattr(self.performance_settings, key, value)
            
            # Load safety parameters
            if 'safety_parameters' in config_data:
                for key, value in config_data['safety_parameters'].items():
                    if hasattr(self.safety_parameters, key):
                        setattr(self.safety_parameters, key, value)
            
            # Validate loaded configuration
            is_valid, errors = self.validate_configuration()
            if not is_valid:
                self.logger.warning(f"Loaded configuration has validation errors: {errors}")
            
            self.last_modified = datetime.now()
            self.logger.info(f"Floater configuration loaded from: {filepath}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to load floater configuration: {e}")
            return False
    
    def reset_to_defaults(self):
        """Reset configuration to default values"""
        self.physical_properties = PhysicalProperties()
        self.operational_parameters = OperationalParameters()
        self.performance_settings = PerformanceSettings()
        self.safety_parameters = SafetyParameters()
        self.floater_type = FloaterType.STANDARD
        
        self.last_modified = datetime.now()
        self.logger.info("Floater configuration reset to defaults")
    
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
        self.logger.info("Floater configuration history cleared") 