"""
Enhanced drag force calculations for KPP simulator.
Implements proper fluid dynamics with Reynolds number effects.
"""

from dataclasses import dataclass
from typing import Optional
import numpy as np
import logging

@dataclass
class DragResult:
    """Results from drag calculation"""
    force: float  # Net drag force magnitude (N)
    coefficient: float  # Actual drag coefficient used
    reynolds_number: float  # Reynolds number for the flow
    dynamic_pressure: float  # Dynamic pressure (Pa)
    power_loss: float  # Power lost to drag (W)

class EnhancedDragCalculator:
    """
    Enhanced drag calculator that handles:
    - Proper quadratic drag formula
    - Reynolds number effects
    - Variable coefficients
    - Power loss tracking
    """
    
    def __init__(self, 
                 base_drag_coefficient: float = 0.47,  # Sphere default
                 fluid_viscosity: float = 1.0e-3,  # Water at 20°C (Pa·s)
                 min_reynolds: float = 1.0,
                 max_reynolds: float = 1.0e6):
        """
        Initialize the drag calculator.
        
        Args:
            base_drag_coefficient: Base drag coefficient for the floater shape
            fluid_viscosity: Dynamic viscosity of the fluid
            min_reynolds: Minimum Reynolds number for calculations
            max_reynolds: Maximum Reynolds number for calculations
        """
        self.base_cd = base_drag_coefficient
        self.viscosity = fluid_viscosity
        self.min_reynolds = min_reynolds
        self.max_reynolds = max_reynolds
        self.logger = logging.getLogger(__name__)
        
        # Performance tracking
        self.calculation_count = 0
        self.total_calculation_time = 0.0
    
    def calculate_reynolds_number(self, 
                                velocity: float,
                                characteristic_length: float,
                                fluid_density: float) -> float:
        """
        Calculate Reynolds number for the flow.
        
        Args:
            velocity: Flow velocity (m/s)
            characteristic_length: Characteristic length (e.g. diameter) (m)
            fluid_density: Fluid density (kg/m³)
            
        Returns:
            Reynolds number (dimensionless)
        """
        return max(self.min_reynolds,
                  min(self.max_reynolds,
                      abs(velocity) * characteristic_length * fluid_density / self.viscosity))
    
    def get_drag_coefficient(self, reynolds: float) -> float:
        """
        Get drag coefficient based on Reynolds number.
        Implements a simplified version of the drag crisis curve.
        
        Args:
            reynolds: Reynolds number
            
        Returns:
            Drag coefficient
        """
        # Simplified drag crisis model
        if reynolds < 1e3:
            # Laminar regime
            return self.base_cd
        elif reynolds < 2e5:
            # Transitional regime
            return self.base_cd * (1.0 + 0.1 * np.log10(reynolds/1e3))
        else:
            # Post-crisis regime (reduced drag)
            return self.base_cd * 0.2
    
    def calculate_drag(self,
                      velocity: float,
                      cross_section: float,
                      fluid_density: float,
                      characteristic_length: float) -> DragResult:
        """
        Calculate drag force with all effects.
        
        Args:
            velocity: Relative velocity between fluid and floater (m/s)
            cross_section: Cross-sectional area perpendicular to flow (m²)
            fluid_density: Density of the fluid (kg/m³)
            characteristic_length: Characteristic length for Reynolds number (m)
            
        Returns:
            DragResult with force and associated data
        """
        try:
            # Calculate Reynolds number
            reynolds = self.calculate_reynolds_number(velocity, characteristic_length, fluid_density)
            
            # Get appropriate drag coefficient
            cd = self.get_drag_coefficient(reynolds)
            
            # Calculate dynamic pressure
            dynamic_pressure = 0.5 * fluid_density * velocity * abs(velocity)
            
            # Calculate drag force
            drag_force = cd * cross_section * dynamic_pressure
            
            # Calculate power loss
            power_loss = abs(drag_force * velocity)
            
            return DragResult(
                force=drag_force,
                coefficient=cd,
                reynolds_number=reynolds,
                dynamic_pressure=dynamic_pressure,
                power_loss=power_loss
            )
            
        except Exception as e:
            self.logger.error(f"Drag calculation failed: {e}")
            # Return zero-force result rather than failing
            return DragResult(0.0, self.base_cd, 0.0, 0.0, 0.0)
    
    def get_performance_metrics(self):
        """Get calculator performance metrics"""
        return {
            'total_calculations': self.calculation_count,
            'average_calculation_time': (
                self.total_calculation_time / self.calculation_count 
                if self.calculation_count > 0 else 0.0
            )
        } 