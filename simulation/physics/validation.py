"""
Physics validation module for KPP simulator.
Implements checks to verify physics calculations against theoretical predictions.
"""

from dataclasses import dataclass
from typing import Dict, Optional, Any
import numpy as np
import logging

from .buoyancy import BuoyancyResult
from .drag import DragResult

@dataclass
class ValidationResult:
    """Results from physics validation"""
    passed: bool
    error_margin: float
    theoretical_value: float
    calculated_value: float
    description: str
    error_message: Optional[str] = None

class PhysicsValidator:
    """
    Validates physics calculations against theoretical predictions.
    Ensures conservation laws and proper implementation of formulas.
    """
    
    def __init__(self, tolerance: float = 0.01):
        """
        Initialize the validator.
        
        Args:
            tolerance: Relative error tolerance for validation checks
        """
        self.tolerance = tolerance
        self.logger = logging.getLogger(__name__)
        
    def validate_buoyancy(self, 
                         result: BuoyancyResult,
                         volume: float,
                         water_density: float,
                         gravity: float) -> ValidationResult:
        """
        Validate buoyancy calculation against Archimedes principle.
        
        Args:
            result: Calculated buoyancy result
            volume: Floater volume (m³)
            water_density: Water density (kg/m³)
            gravity: Gravitational acceleration (m/s²)
            
        Returns:
            ValidationResult with comparison details
        """
        # Theoretical maximum buoyant force (fully submerged)
        theoretical_force = water_density * volume * gravity
        
        # Account for partial submersion
        theoretical_force *= result.submersion_factor
        
        # Compare with calculated force
        relative_error = abs(result.force - theoretical_force) / theoretical_force
        
        passed = relative_error <= self.tolerance
        
        return ValidationResult(
            passed=passed,
            error_margin=relative_error,
            theoretical_value=theoretical_force,
            calculated_value=result.force,
            description="Buoyancy force validation",
            error_message=None if passed else f"Buoyancy force error {relative_error:.2%} exceeds tolerance"
        )
    
    def validate_drag(self,
                     result: DragResult,
                     velocity: float,
                     area: float,
                     fluid_density: float) -> ValidationResult:
        """
        Validate drag calculation against theoretical formula.
        
        Args:
            result: Calculated drag result
            velocity: Flow velocity (m/s)
            area: Cross-sectional area (m²)
            fluid_density: Fluid density (kg/m³)
            
        Returns:
            ValidationResult with comparison details
        """
        # Theoretical drag force
        dynamic_pressure = 0.5 * fluid_density * velocity * abs(velocity)
        theoretical_force = result.coefficient * area * dynamic_pressure
        
        # Compare with calculated force
        relative_error = abs(result.force - theoretical_force) / (theoretical_force if theoretical_force != 0 else 1.0)
        
        passed = relative_error <= self.tolerance
        
        return ValidationResult(
            passed=passed,
            error_margin=relative_error,
            theoretical_value=theoretical_force,
            calculated_value=result.force,
            description="Drag force validation",
            error_message=None if passed else f"Drag force error {relative_error:.2%} exceeds tolerance"
        )
    
    def validate_energy_conservation(self,
                                   initial_energy: Dict[str, float],
                                   final_energy: Dict[str, float],
                                   work_done: Dict[str, float]) -> ValidationResult:
        """
        Validate conservation of energy.
        
        Args:
            initial_energy: Initial energy components
            final_energy: Final energy components
            work_done: Work done by various forces
            
        Returns:
            ValidationResult with comparison details
        """
        # Sum initial and final energies
        initial_total = sum(initial_energy.values())
        final_total = sum(final_energy.values())
        
        # Sum work done (negative for work against the system)
        total_work = sum(work_done.values())
        
        # Energy should be conserved: ΔE = W
        energy_change = final_total - initial_total
        
        # Compare energy change with work done
        error = abs(energy_change - total_work)
        relative_error = error / (abs(total_work) if total_work != 0 else 1.0)
        
        passed = relative_error <= self.tolerance
        
        return ValidationResult(
            passed=passed,
            error_margin=relative_error,
            theoretical_value=total_work,
            calculated_value=energy_change,
            description="Energy conservation validation",
            error_message=None if passed else f"Energy conservation error {relative_error:.2%} exceeds tolerance"
        )
    
    def validate_timestep_stability(self,
                                  dt: float,
                                  characteristic_velocity: float,
                                  characteristic_length: float) -> ValidationResult:
        """
        Validate numerical stability of time step.
        Uses CFL-like condition for stability check.
        
        Args:
            dt: Time step (s)
            characteristic_velocity: Typical velocity scale (m/s)
            characteristic_length: Typical length scale (m)
            
        Returns:
            ValidationResult with stability assessment
        """
        # Simple CFL-like condition: dt < dx/v
        if characteristic_velocity > 0:
            theoretical_dt = 0.1 * characteristic_length / characteristic_velocity
        else:
            theoretical_dt = float('inf')
        
        # Check if time step is small enough
        relative_error = dt / theoretical_dt if theoretical_dt != float('inf') else 0.0
        
        passed = relative_error <= 1.0
        
        return ValidationResult(
            passed=passed,
            error_margin=relative_error,
            theoretical_value=theoretical_dt,
            calculated_value=dt,
            description="Time step stability validation",
            error_message=None if passed else f"Time step {dt:.3e}s may be too large for stability"
        )
    
    def run_all_validations(self,
                           physics_state: Dict[str, Any],
                           config: Dict[str, Any]) -> Dict[str, ValidationResult]:
        """
        Run all validation checks on current physics state.
        
        Args:
            physics_state: Current physics state dictionary
            config: Physics configuration dictionary
            
        Returns:
            Dictionary of validation results
        """
        results = {}
        
        try:
            # Validate buoyancy if results available
            if 'buoyancy_results' in physics_state:
                results['buoyancy'] = self.validate_buoyancy(
                    physics_state['buoyancy_results'],
                    config['volume'],
                    config['water_density'],
                    config['gravity']
                )
            
            # Validate drag if results available
            if 'drag_results' in physics_state:
                results['drag'] = self.validate_drag(
                    physics_state['drag_results'],
                    np.linalg.norm(physics_state['velocity']),
                    config['cross_section'],
                    config['water_density']
                )
            
            # Validate energy conservation
            if 'energy' in physics_state:
                results['energy'] = self.validate_energy_conservation(
                    physics_state.get('initial_energy', {}),
                    physics_state['energy'],
                    physics_state.get('work_done', {})
                )
            
            # Validate time step stability
            results['stability'] = self.validate_timestep_stability(
                config['time_step'],
                np.linalg.norm(physics_state['velocity']),
                config['characteristic_length']
            )
            
        except Exception as e:
            self.logger.error(f"Validation failed: {e}")
            
        return results 