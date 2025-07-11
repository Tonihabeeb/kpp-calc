"""
Enhanced buoyancy calculations for KPP simulator.
Implements Archimedes principle with depth effects and thermal integration.
"""

from dataclasses import dataclass
from typing import Optional
import numpy as np
import logging

from simulation.components.floater.thermal import ThermalModel, ThermalState

@dataclass
class BuoyancyResult:
    """Results from buoyancy calculation"""
    force: float  # Net buoyant force (N)
    displaced_volume: float  # Actual volume of water displaced (m³)
    effective_density: float  # Effective density of displaced fluid (kg/m³)
    submersion_factor: float  # Fraction of floater submerged (0-1)
    depth_pressure: float  # Pressure at current depth (Pa)

class EnhancedBuoyancyCalculator:
    """
    Enhanced buoyancy calculator that handles:
    - Proper Archimedes principle implementation
    - Depth-dependent effects
    - Partial submersion
    - Thermal integration
    - Real-time performance tracking
    """
    
    def __init__(self, water_density: float = 1000.0, gravity: float = 9.81):
        """
        Initialize the buoyancy calculator.
        
        Args:
            water_density: Base density of water (kg/m³)
            gravity: Gravitational acceleration (m/s²)
        """
        self.water_density = water_density
        self.gravity = gravity
        self.logger = logging.getLogger(__name__)
        
        # Performance tracking
        self.calculation_count = 0
        self.total_calculation_time = 0.0
        
    def calculate_buoyancy(self, 
                          floater_volume: float,
                          depth: float,
                          air_fill_level: float,
                          thermal_state: Optional[ThermalState] = None) -> BuoyancyResult:
        """
        Calculate buoyancy force with all effects.
        
        Args:
            floater_volume: Total volume of floater (m³)
            depth: Current depth below surface (m)
            air_fill_level: Fraction of floater filled with air (0-1)
            thermal_state: Optional thermal state for temperature effects
            
        Returns:
            BuoyancyResult with force and associated data
        """
        try:
            # Calculate submersion factor based on depth and geometry
            # For now assume simple linear relationship
            submersion_factor = min(1.0, max(0.0, depth / floater_volume**(1/3)))
            
            # Calculate effective displaced volume
            # This accounts for partial filling and submersion
            effective_volume = floater_volume * submersion_factor * (1.0 - air_fill_level)
            
            # Calculate pressure at depth
            depth_pressure = self.water_density * self.gravity * depth + 101325.0  # Add atmospheric
            
            # Calculate effective density including thermal effects
            effective_density = self.water_density
            if thermal_state:
                # Adjust density based on temperature
                # Simple linear approximation for water
                temp_diff = thermal_state.temperature - 293.15  # Difference from 20°C
                effective_density *= (1.0 - 0.0002 * temp_diff)  # Approximate thermal expansion
            
            # Calculate buoyant force (Archimedes principle)
            buoyant_force = effective_density * effective_volume * self.gravity
            
            return BuoyancyResult(
                force=buoyant_force,
                displaced_volume=effective_volume,
                effective_density=effective_density,
                submersion_factor=submersion_factor,
                depth_pressure=depth_pressure
            )
            
        except Exception as e:
            self.logger.error(f"Buoyancy calculation failed: {e}")
            # Return zero-force result rather than failing
            return BuoyancyResult(0.0, 0.0, self.water_density, 0.0, 101325.0)
    
    def get_performance_metrics(self):
        """Get calculator performance metrics"""
        return {
            'total_calculations': self.calculation_count,
            'average_calculation_time': (
                self.total_calculation_time / self.calculation_count 
                if self.calculation_count > 0 else 0.0
            )
        } 