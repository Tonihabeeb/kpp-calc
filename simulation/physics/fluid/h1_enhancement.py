"""
H1 Enhancement: Nanobubble effects on fluid properties.
"""

import numpy as np
from typing import Dict, Any

class H1Enhancement:
    """H1 Enhancement: Nanobubble density and drag reduction"""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize H1 enhancement"""
        self.config = config
        
        # H1 parameters
        self.nanobubble_fraction = config.get('h1_nanobubble_fraction', 0.2)
        self.density_reduction = config.get('h1_density_reduction', 0.1)
        self.drag_reduction = config.get('h1_drag_reduction', 0.15)
        
        # Enhancement state
        self.enabled = False
        self.current_fraction = 0.0
        
        print("H1 Enhancement initialized")
        
    def enable(self) -> None:
        """Enable H1 enhancement"""
        self.enabled = True
        self.current_fraction = self.nanobubble_fraction
        print("H1 Enhancement enabled")
        
    def disable(self) -> None:
        """Disable H1 enhancement"""
        self.enabled = False
        self.current_fraction = 0.0
        print("H1 Enhancement disabled")
        
    def set_nanobubble_fraction(self, fraction: float) -> None:
        """Set nanobubble fraction (0.0 to 1.0)"""
        self.current_fraction = np.clip(fraction, 0.0, 1.0)
        
    def get_effective_density(self, base_density: float) -> float:
        """Get effective density with nanobubble reduction"""
        if not self.enabled:
            return base_density
            
        # Reduce density based on nanobubble fraction
        reduction_factor = 1.0 - (self.current_fraction * self.density_reduction)
        return base_density * reduction_factor
        
    def get_effective_drag_coefficient(self, base_drag_coefficient: float) -> float:
        """Get effective drag coefficient with nanobubble reduction"""
        if not self.enabled:
            return base_drag_coefficient
            
        # Reduce drag coefficient based on nanobubble fraction
        reduction_factor = 1.0 - (self.current_fraction * self.drag_reduction)
        return base_drag_coefficient * reduction_factor
        
    def get_enhancement_factor(self) -> float:
        """Get current enhancement factor (1.0 = no enhancement)"""
        if not self.enabled:
            return 1.0
            
        # Calculate overall enhancement factor
        density_factor = 1.0 - (self.current_fraction * self.density_reduction)
        drag_factor = 1.0 - (self.current_fraction * self.drag_reduction)
        
        # Overall factor (lower is better for efficiency)
        return density_factor * drag_factor
        
    def get_status(self) -> Dict[str, Any]:
        """Get H1 enhancement status"""
        return {
            'enabled': self.enabled,
            'nanobubble_fraction': self.current_fraction,
            'density_reduction': self.density_reduction,
            'drag_reduction': self.drag_reduction,
            'enhancement_factor': self.get_enhancement_factor()
        }
