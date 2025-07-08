import math
import logging
from typing import Any, Dict, Optional
from dataclasses import dataclass
from config.config import RHO_AIR, RHO_WATER, G
"""
Buoyancy calculations for floater physics.
Handles buoyant force, pressure effects, and density calculations.
"""

@dataclass
class BuoyancyResult:
    """Buoyancy calculation result"""
    buoyancy_force: float = 0.0  # N
    displaced_volume: float = 0.0  # m³
    pressure_effect: float = 1.0  # Pressure correction factor
    thermal_effect: float = 1.0  # Thermal correction factor
    total_effect: float = 1.0  # Combined correction factor
    efficiency: float = 1.0  # Buoyancy efficiency

@dataclass
class BuoyancyConfig:
    """Buoyancy calculation configuration"""
    water_density: float = RHO_WATER  # kg/m³
    air_density: float = RHO_AIR  # kg/m³
    gravity: float = G  # m/s²
    atmospheric_pressure: float = 101325.0  # Pa
    pressure_coefficient: float = 1.0e-5  # 1/Pa
    thermal_coefficient: float = 2.1e-4  # 1/K

class BuoyancyCalculator:
    """
    Comprehensive buoyancy calculation system.
    Handles basic buoyancy, pressure effects, thermal effects, and advanced calculations.
    """
    
    def __init__(self, config: Optional[BuoyancyConfig] = None):
        """
        Initialize the buoyancy calculator.
        
        Args:
            config: Buoyancy calculation configuration
        """
        self.config = config or BuoyancyConfig()
        self.logger = logging.getLogger(__name__)
        
        # Performance tracking
        self.calculation_count = 0
        self.average_buoyancy_force = 0.0
        self.max_buoyancy_force = 0.0
        
        self.logger.info("Buoyancy calculator initialized")
    
    def calculate_basic_buoyancy(self, volume: float, water_density: Optional[float] = None) -> float:
        """
        Calculate basic buoyancy force using Archimedes' principle.
        
        Args:
            volume: Displaced volume (m³)
            water_density: Water density (kg/m³), defaults to config value
            
        Returns:
            Buoyancy force (N)
        """
        try:
            if water_density is None:
                water_density = self.config.water_density
            
            # Archimedes' principle: F_b = ρ_water × V × g
            buoyancy_force = water_density * volume * self.config.gravity
            
            # Update tracking
            self.calculation_count += 1
            self.average_buoyancy_force = (
                (self.average_buoyancy_force * (self.calculation_count - 1) + buoyancy_force) /
                self.calculation_count
            )
            
            if buoyancy_force > self.max_buoyancy_force:
                self.max_buoyancy_force = buoyancy_force
            
            return buoyancy_force
            
        except Exception as e:
            self.logger.error("Error calculating basic buoyancy: %s", e)
            return 0.0
    
    def calculate_pressure_effects(self, depth: float, pressure: float) -> float:
        """
        Calculate pressure effects on buoyancy.
        
        Args:
            depth: Depth below water surface (m)
            pressure: Current pressure (Pa)
            
        Returns:
            Pressure correction factor
        """
        try:
            # Hydrostatic pressure: P = ρ_water × g × h
            hydrostatic_pressure = self.config.water_density * self.config.gravity * depth
            
            # Pressure effect on water density (simplified)
            # Water is nearly incompressible, so effect is small
            pressure_effect = 1.0 + self.config.pressure_coefficient * (pressure - self.config.atmospheric_pressure)
            
            # Ensure reasonable bounds
            pressure_effect = max(0.95, min(1.05, pressure_effect))
            
            return pressure_effect
            
        except Exception as e:
            self.logger.error("Error calculating pressure effects: %s", e)
            return 1.0
    
    def calculate_thermal_effects(self, water_temperature: float, air_temperature: float) -> float:
        """
        Calculate thermal effects on buoyancy.
        
        Args:
            water_temperature: Water temperature (K)
            air_temperature: Air temperature (K)
            
        Returns:
            Thermal correction factor
        """
        try:
            # Reference temperature
            ref_temperature = 293.15  # K (20°C)
            
            # Water density change with temperature
            # Simplified: ρ_water = ρ_ref × (1 - α × ΔT)
            water_temp_change = water_temperature - ref_temperature
            water_density_factor = 1.0 - self.config.thermal_coefficient * water_temp_change
            
            # Air density change with temperature (ideal gas law)
            # ρ_air = ρ_ref × (T_ref / T)
            air_density_factor = ref_temperature / air_temperature
            
            # Combined thermal effect
            thermal_effect = water_density_factor / air_density_factor
            
            # Ensure reasonable bounds
            thermal_effect = max(0.9, min(1.1, thermal_effect))
            
            return thermal_effect
            
        except Exception as e:
            self.logger.error("Error calculating thermal effects: %s", e)
            return 1.0
    
    def calculate_air_fill_effects(self, air_fill_level: float, total_volume: float) -> float:
        """
        Calculate effects of air fill level on buoyancy.
        
        Args:
            air_fill_level: Air fill level (0.0 to 1.0)
            total_volume: Total floater volume (m³)
            
        Returns:
            Air fill correction factor
        """
        try:
            # Calculate effective displaced volume
            # Air-filled portion doesn't contribute to buoyancy
            effective_volume = total_volume * (1.0 - air_fill_level)
            
            # Air fill effect
            air_fill_effect = 1.0 - air_fill_level
            
            # Ensure reasonable bounds
            air_fill_effect = max(0.0, min(1.0, air_fill_effect))
            
            return air_fill_effect
            
        except Exception as e:
            self.logger.error("Error calculating air fill effects: %s", e)
            return 1.0
    
    def calculate_nanobubble_effects(self, nanobubble_concentration: float) -> float:
        """
        Calculate nanobubble effects on buoyancy.
        
        Args:
            nanobubble_concentration: Nanobubble concentration (bubbles/m³)
            
        Returns:
            Nanobubble correction factor
        """
        try:
            # Nanobubble effect on water density
            # Simplified model: reduced effective density
            bubble_volume_fraction = nanobubble_concentration * 1e-18  # Very small bubbles
            density_reduction = bubble_volume_fraction * (self.config.water_density - self.config.air_density)
            
            # Nanobubble effect factor
            nanobubble_effect = 1.0 - density_reduction / self.config.water_density
            
            # Ensure reasonable bounds
            nanobubble_effect = max(0.99, min(1.01, nanobubble_effect))
            
            return nanobubble_effect
            
        except Exception as e:
            self.logger.error("Error calculating nanobubble effects: %s", e)
            return 1.0
    
    def calculate_depth_effects(self, depth: float) -> float:
        """
        Calculate depth effects on buoyancy.
        
        Args:
            depth: Depth below water surface (m)
            
        Returns:
            Depth correction factor
        """
        try:
            # Water density increases slightly with depth
            # Simplified: ρ_water = ρ_surface × (1 + β × h)
            depth_coefficient = 1e-6  # 1/m
            depth_effect = 1.0 + depth_coefficient * depth
            
            # Ensure reasonable bounds
            depth_effect = max(1.0, min(1.01, depth_effect))
            
            return depth_effect
            
        except Exception as e:
            self.logger.error("Error calculating depth effects: %s", e)
            return 1.0
    
    def calculate_comprehensive_buoyancy(self, volume: float, depth: float = 0.0,
                                       pressure: Optional[float] = None,
                                       water_temperature: float = 293.15,
                                       air_temperature: float = 293.15,
                                       air_fill_level: float = 0.0,
                                       nanobubble_concentration: float = 0.0) -> BuoyancyResult:
        """
        Calculate comprehensive buoyancy with all effects.
        
        Args:
            volume: Total volume (m³)
            depth: Depth below water surface (m)
            pressure: Current pressure (Pa)
            water_temperature: Water temperature (K)
            air_temperature: Air temperature (K)
            air_fill_level: Air fill level (0.0 to 1.0)
            nanobubble_concentration: Nanobubble concentration (bubbles/m³)
            
        Returns:
            Comprehensive buoyancy result
        """
        try:
            # Calculate base buoyancy
            base_buoyancy = self.calculate_basic_buoyancy(volume)
            
            # Calculate correction factors
            pressure_effect = self.calculate_pressure_effects(depth, pressure or self.config.atmospheric_pressure)
            thermal_effect = self.calculate_thermal_effects(water_temperature, air_temperature)
            air_fill_effect = self.calculate_air_fill_effects(air_fill_level, volume)
            nanobubble_effect = self.calculate_nanobubble_effects(nanobubble_concentration)
            depth_effect = self.calculate_depth_effects(depth)
            
            # Combined effect
            total_effect = (pressure_effect * thermal_effect * air_fill_effect * 
                          nanobubble_effect * depth_effect)
            
            # Calculate final buoyancy force
            final_buoyancy = base_buoyancy * total_effect
            
            # Calculate effective displaced volume
            effective_volume = volume * air_fill_effect
            
            # Calculate efficiency (ratio of actual to theoretical buoyancy)
            theoretical_buoyancy = self.config.water_density * volume * self.config.gravity
            efficiency = final_buoyancy / max(theoretical_buoyancy, 1e-6)
            
            return BuoyancyResult(
                buoyancy_force=final_buoyancy,
                displaced_volume=effective_volume,
                pressure_effect=pressure_effect,
                thermal_effect=thermal_effect,
                total_effect=total_effect,
                efficiency=efficiency
            )
            
        except Exception as e:
            self.logger.error("Error calculating comprehensive buoyancy: %s", e)
            return BuoyancyResult()
    
    def calculate_multi_phase_buoyancy(self, volumes: Dict[str, float],
                                     densities: Dict[str, float]) -> float:
        """
        Calculate buoyancy for multi-phase systems.
        
        Args:
            volumes: Dictionary of phase volumes (m³)
            densities: Dictionary of phase densities (kg/m³)
            
        Returns:
            Total buoyancy force (N)
        """
        try:
            total_buoyancy = 0.0
            
            for phase, volume in volumes.items():
                if phase in densities:
                    phase_density = densities[phase]
                    phase_buoyancy = self.calculate_basic_buoyancy(volume, phase_density)
                    total_buoyancy += phase_buoyancy
            
            return total_buoyancy
            
        except Exception as e:
            self.logger.error("Error calculating multi-phase buoyancy: %s", e)
            return 0.0
    
    def calculate_dynamic_buoyancy(self, volume: float, velocity: float,
                                 acceleration: float = 0.0) -> float:
        """
        Calculate dynamic buoyancy effects.
        
        Args:
            volume: Volume (m³)
            velocity: Velocity (m/s)
            acceleration: Acceleration (m/s²)
            
        Returns:
            Dynamic buoyancy force (N)
        """
        try:
            # Static buoyancy
            static_buoyancy = self.calculate_basic_buoyancy(volume)
            
            # Dynamic effects (simplified)
            # Added mass effect
            added_mass_factor = 1.0 + 0.5 * abs(velocity) / 10.0  # 50% added mass at 10 m/s
            
            # Acceleration effect
            acceleration_effect = 1.0 + 0.1 * abs(acceleration) / 9.81  # 10% effect at 1g
            
            # Combined dynamic effect
            dynamic_factor = added_mass_factor * acceleration_effect
            
            dynamic_buoyancy = static_buoyancy * dynamic_factor
            
            return dynamic_buoyancy
            
        except Exception as e:
            self.logger.error("Error calculating dynamic buoyancy: %s", e)
            return 0.0
    
    def optimize_buoyancy_parameters(self, target_buoyancy: float,
                                   current_volume: float) -> Dict[str, float]:
        """
        Optimize buoyancy parameters for target force.
        
        Args:
            target_buoyancy: Target buoyancy force (N)
            current_volume: Current volume (m³)
            
        Returns:
            Optimized parameters
        """
        try:
            # Calculate required volume for target buoyancy
            required_volume = target_buoyancy / (self.config.water_density * self.config.gravity)
            
            # Calculate volume difference
            volume_difference = required_volume - current_volume
            
            # Calculate optimal air fill level
            optimal_air_fill = max(0.0, min(1.0, volume_difference / current_volume))
            
            # Calculate optimal pressure
            optimal_pressure = self.config.atmospheric_pressure * (1.0 + optimal_air_fill)
            
            return {
                'required_volume': required_volume,
                'volume_difference': volume_difference,
                'optimal_air_fill': optimal_air_fill,
                'optimal_pressure': optimal_pressure,
                'efficiency': current_volume / max(required_volume, 1e-6)
            }
            
        except Exception as e:
            self.logger.error("Error optimizing buoyancy parameters: %s", e)
            return {}
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Get performance metrics.
        
        Returns:
            Performance metrics dictionary
        """
        return {
            'calculation_count': self.calculation_count,
            'average_buoyancy_force': self.average_buoyancy_force,
            'max_buoyancy_force': self.max_buoyancy_force,
            'efficiency': self.average_buoyancy_force / max(self.max_buoyancy_force, 1e-6)
        }
    
    def reset(self) -> None:
        """Reset buoyancy calculator state."""
        self.calculation_count = 0
        self.average_buoyancy_force = 0.0
        self.max_buoyancy_force = 0.0
        self.logger.info("Buoyancy calculator reset")

