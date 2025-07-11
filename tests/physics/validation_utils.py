"""
Validation utilities for physics calculations.
"""

import numpy as np
from typing import Dict, Any, List, Tuple

class PhysicsValidator:
    """Validator for physics calculations"""
    
    def __init__(self):
        self.reference_data = self._load_reference_data()
    
    def _load_reference_data(self) -> Dict[str, Any]:
        """Load reference data for validation"""
        return {
            'water_density_20c': 998.2,  # kg/m^3 at 20C
            'air_density_20c': 1.204,    # kg/m^3 at 20C
            'gravity': 9.81,             # m/s^2
            'atmospheric_pressure': 101325.0,  # Pa
        }
    
    def validate_fluid_properties(self, temperature: float, pressure: float, 
                                density: float, fluid: str = 'water') -> bool:
        """Validate fluid properties against reference data"""
        if fluid == 'water':
            # Simple validation - density should be close to reference
            expected_density = self.reference_data['water_density_20c']
            tolerance = 0.05  # 5%
            return abs(density - expected_density) / expected_density <= tolerance
        return True
    
    def validate_force_calculation(self, force: float, expected_range: Tuple[float, float]) -> bool:
        """Validate force calculation is within expected range"""
        min_force, max_force = expected_range
        return min_force <= force <= max_force
    
    def validate_energy_conservation(self, initial_energy: float, final_energy: float,
                                   tolerance: float = 0.01) -> bool:
        """Validate energy conservation"""
        if initial_energy == 0:
            return True
        energy_change = abs(final_energy - initial_energy) / abs(initial_energy)
        return energy_change <= tolerance
    
    def validate_physical_constraints(self, values: Dict[str, float]) -> List[str]:
        """Validate physical constraints and return list of violations"""
        violations = []
        
        # Check for negative masses
        if 'mass' in values and values['mass'] < 0:
            violations.append("Mass cannot be negative")
        
        # Check for negative volumes
        if 'volume' in values and values['volume'] < 0:
            violations.append("Volume cannot be negative")
        
        # Check for negative forces
        if 'force' in values and values['force'] < 0:
            violations.append("Force cannot be negative")
        
        return violations
