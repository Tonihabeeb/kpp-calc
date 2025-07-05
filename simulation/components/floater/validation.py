"""
Validation for floater parameters and state.
Ensures physical constraints and operational limits.
"""

import logging
from typing import Dict, Any, List, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ValidationResult:
    """Result of parameter validation"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    corrected_values: Dict[str, Any]

class FloaterValidator:
    """Validates floater parameters and state"""
    
    def __init__(self):
        self.constraints = self._define_constraints()
    
    def _define_constraints(self) -> Dict[str, Dict[str, Any]]:
        """Define physical and operational constraints"""
        return {
            'volume': {
                'min': 0.01,  # m³
                'max': 10.0,  # m³
                'description': 'Floater volume'
            },
            'mass': {
                'min': 0.1,   # kg
                'max': 1000.0, # kg
                'description': 'Floater mass'
            },
            'drag_coefficient': {
                'min': 0.0,
                'max': 2.0,
                'description': 'Drag coefficient'
            },
            'position': {
                'min': 0.0,   # m
                'max': 25.0,  # m
                'description': 'Vertical position'
            },
            'velocity': {
                'min': -10.0, # m/s
                'max': 10.0,  # m/s
                'description': 'Vertical velocity'
            },
            'air_pressure': {
                'min': 50000,  # Pa
                'max': 1000000, # Pa
                'description': 'Air pressure'
            }
        }
    
    def validate_parameters(self, params: Dict[str, Any]) -> ValidationResult:
        """Validate floater parameters"""
        errors = []
        warnings = []
        corrected_values = {}
        
        for param_name, value in params.items():
            if param_name in self.constraints:
                constraint = self.constraints[param_name]
                
                # Check minimum value
                if value < constraint['min']:
                    errors.append(
                        f"{constraint['description']} ({param_name}) "
                        f"must be >= {constraint['min']}, got {value}"
                    )
                    corrected_values[param_name] = constraint['min']
                
                # Check maximum value
                elif value > constraint['max']:
                    errors.append(
                        f"{constraint['description']} ({param_name}) "
                        f"must be <= {constraint['max']}, got {value}"
                    )
                    corrected_values[param_name] = constraint['max']
        
        # Cross-parameter validation
        cross_validation_result = self._validate_cross_parameters(params)
        errors.extend(cross_validation_result['errors'])
        warnings.extend(cross_validation_result['warnings'])
        
        is_valid = len(errors) == 0
        
        return ValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            corrected_values=corrected_values
        )
    
    def _validate_cross_parameters(self, params: Dict[str, Any]) -> Dict[str, List[str]]:
        """Validate relationships between parameters"""
        errors = []
        warnings = []
        
        # Check density constraint
        if 'volume' in params and 'mass' in params:
            volume = params['volume']
            mass = params['mass']
            
            if volume > 0:
                density = mass / volume
                if density > 1000:  # Water density
                    errors.append(
                        f"Floater density ({density:.1f} kg/m³) "
                        f"exceeds water density (1000 kg/m³)"
                    )
                elif density > 800:
                    warnings.append(
                        f"High floater density ({density:.1f} kg/m³) "
                        f"may affect buoyancy"
                    )
        
        # Check position within tank height
        if 'position' in params and 'tank_height' in params:
            position = params['position']
            tank_height = params['tank_height']
            
            if position > tank_height:
                errors.append(
                    f"Position ({position}m) exceeds tank height ({tank_height}m)"
                )
        
        return {'errors': errors, 'warnings': warnings}
    
    def validate_state(self, state: Dict[str, Any]) -> ValidationResult:
        """Validate floater state"""
        errors = []
        warnings = []
        corrected_values = {}
        
        # Check air fill level
        air_fill_level = state.get('air_fill_level', 0.0)
        if not 0.0 <= air_fill_level <= 1.0:
            errors.append(f"Air fill level must be 0-1, got {air_fill_level}")
            corrected_values['air_fill_level'] = max(0.0, min(1.0, air_fill_level))
        
        # Check velocity limits
        velocity = state.get('velocity', 0.0)
        if abs(velocity) > 10.0:
            warnings.append(f"High velocity detected: {velocity} m/s")
        
        # Check position bounds
        position = state.get('position', 0.0)
        if position < 0.0:
            errors.append(f"Position cannot be negative: {position}")
            corrected_values['position'] = 0.0
        
        is_valid = len(errors) == 0
        
        return ValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            corrected_values=corrected_values
        )
