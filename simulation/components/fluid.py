"""
Fluid System Module for KPP Simulation
Handles water properties, nanobubble effects (H1), and drag calculations.
"""

import math
import logging
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class FluidState:
    """Current state of the fluid system"""
    density: float = 1000.0  # kg/m³
    temperature: float = 293.15  # K (20°C)
    nanobubble_fraction: float = 0.0  # Volume fraction of nanobubbles
    drag_coefficient: float = 0.6  # Base drag coefficient
    effective_density: float = 1000.0  # Effective density with nanobubbles
    reynolds_number: float = 0.0  # Current Reynolds number

class Fluid:
    """
    Manages fluid properties and hydrodynamic calculations.
    
    Handles:
    - Water density calculations with temperature effects
    - Nanobubble (H1) effects on density and drag
    - Dynamic drag coefficient based on flow conditions
    - Reynolds number calculations
    - Buoyancy force computations
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the fluid system.
        
        Args:
            config (dict): Configuration parameters
        """
        if config is None:
            config = {}
            
        # Base fluid properties
        self.base_density = config.get('water_density', 1000.0)  # kg/m³
        self.base_temperature = config.get('water_temperature', 293.15)  # K
        self.gravity = config.get('gravity', 9.81)  # m/s²
        self.kinematic_viscosity = config.get('kinematic_viscosity', 1.0e-6)  # m²/s
        
        # Drag properties
        self.base_drag_coefficient = config.get('drag_coefficient', 0.6)
        self.floater_area = config.get('floater_area', 0.1)  # m²
        
        # H1 Nanobubble parameters
        self.h1_active = config.get('h1_active', False)
        self.h1_bubble_fraction = config.get('h1_bubble_fraction', 0.05)  # 5% default
        self.h1_drag_reduction = config.get('h1_drag_reduction', 0.1)  # 10% drag reduction
        
        # Current state
        self.state = FluidState()
        self.update_state()
        
        logger.info(f"Fluid system initialized - Base density: {self.base_density} kg/m³, "
                   f"Temperature: {self.base_temperature} K, H1 active: {self.h1_active}")
    
    def update_state(self):
        """Update the current fluid state based on conditions."""
        # Calculate temperature-dependent density
        self.state.density = self.calculate_density(self.base_temperature)
        self.state.temperature = self.base_temperature
        
        # Apply nanobubble effects if H1 is active
        if self.h1_active:
            self.state.nanobubble_fraction = self.h1_bubble_fraction
            self.state.effective_density = self.apply_nanobubble_effects(self.state.density)
            self.state.drag_coefficient = self.base_drag_coefficient * (1 - self.h1_drag_reduction)
        else:
            self.state.nanobubble_fraction = 0.0
            self.state.effective_density = self.state.density
            self.state.drag_coefficient = self.base_drag_coefficient
    
    def calculate_density(self, temperature: float) -> float:
        """
        Calculate water density based on temperature.
        
        Uses simplified linear approximation:
        ρ(T) = ρ₀ * (1 - β * (T - T₀))
        where β ≈ 2.1e-4 /K for water
        
        Args:
            temperature (float): Water temperature in Kelvin
            
        Returns:
            float: Water density in kg/m³
        """
        thermal_expansion_coeff = 2.1e-4  # /K
        reference_temp = 293.15  # 20°C in K
        
        density = self.base_density * (1 - thermal_expansion_coeff * (temperature - reference_temp))
        return max(density, 900.0)  # Minimum reasonable density
    
    def apply_nanobubble_effects(self, base_density: float) -> float:
        """
        Apply H1 nanobubble effects to reduce effective fluid density.
        
        The nanobubbles create a two-phase mixture with reduced overall density:
        ρ_eff = ρ_water * (1 - α) + ρ_air * α
        where α is the bubble volume fraction and ρ_air << ρ_water
        
        Args:
            base_density (float): Base water density
            
        Returns:
            float: Effective density with nanobubbles
        """
        if not self.h1_active:
            return base_density
            
        # Air density is negligible compared to water
        air_density = 1.225  # kg/m³ at standard conditions
        
        effective_density = (base_density * (1 - self.state.nanobubble_fraction) + 
                           air_density * self.state.nanobubble_fraction)
        
        logger.debug(f"Nanobubble effect: {base_density:.1f} → {effective_density:.1f} kg/m³ "
                    f"({self.state.nanobubble_fraction*100:.1f}% bubbles)")
        
        return effective_density
    
    def calculate_reynolds_number(self, velocity: float, characteristic_length: float) -> float:
        """
        Calculate Reynolds number for flow around floater.
        
        Re = v * L / ν
        
        Args:
            velocity (float): Relative velocity (m/s)
            characteristic_length (float): Characteristic length (m)
            
        Returns:
            float: Reynolds number
        """
        if abs(velocity) < 1e-6:
            return 0.0
            
        reynolds = abs(velocity) * characteristic_length / self.kinematic_viscosity
        self.state.reynolds_number = reynolds
        return reynolds
    
    def calculate_drag_coefficient(self, velocity: float, characteristic_length: float) -> float:
        """
        Calculate drag coefficient based on flow conditions.
        
        Uses Reynolds number to adjust drag coefficient:
        - Low Re: higher Cd (viscous effects)
        - High Re: lower Cd (inertial effects)
        - Includes nanobubble drag reduction
        
        Args:
            velocity (float): Relative velocity (m/s)
            characteristic_length (float): Characteristic length (m)
            
        Returns:
            float: Drag coefficient
        """
        re = self.calculate_reynolds_number(velocity, characteristic_length)
        
        # Base drag coefficient for sphere/cylinder at different Re ranges
        if re < 1:
            # Stokes flow regime
            cd_base = 24 / max(re, 0.1)  # Avoid division by zero
        elif re < 1000:
            # Intermediate regime
            cd_base = 24/re + 6/(1 + math.sqrt(re)) + 0.4
        else:
            # High Reynolds number regime
            cd_base = 0.44
        
        # Apply nanobubble drag reduction if H1 is active
        if self.h1_active:
            cd_effective = cd_base * (1 - self.h1_drag_reduction)
        else:
            cd_effective = cd_base
        
        # Limit to reasonable range
        cd_effective = max(0.1, min(cd_effective, 2.0))
        
        logger.debug(f"Drag coefficient: Re={re:.1f}, Cd_base={cd_base:.3f}, "
                    f"Cd_eff={cd_effective:.3f} (H1 reduction: {self.h1_drag_reduction if self.h1_active else 0:.1%})")
        
        return cd_effective
    
    def calculate_drag_force(self, velocity: float, floater_area: Optional[float] = None) -> float:
        """
        Calculate hydrodynamic drag force on a floater.
        
        F_drag = 0.5 * ρ_eff * Cd * A * v²
        
        Args:
            velocity (float): Relative velocity through water (m/s)
            floater_area (float, optional): Cross-sectional area (m²)
            
        Returns:
            float: Drag force magnitude (N)
        """
        if abs(velocity) < 1e-6:
            return 0.0
            
        area = floater_area or self.floater_area
        characteristic_length = math.sqrt(4 * area / math.pi)  # Equivalent diameter
        
        cd = self.calculate_drag_coefficient(velocity, characteristic_length)
        
        # Calculate drag force
        drag_force = 0.5 * self.state.effective_density * cd * area * velocity**2
        
        logger.debug(f"Drag force: v={velocity:.2f} m/s, A={area:.3f} m², "
                    f"ρ_eff={self.state.effective_density:.1f} kg/m³, "
                    f"Cd={cd:.3f}, F_drag={drag_force:.1f} N")
        
        return drag_force
    
    def calculate_buoyant_force(self, volume: float, submerged_fraction: float = 1.0) -> float:
        """
        Calculate buoyant force on a floater.
        
        F_buoyant = ρ_eff * g * V_submerged
        
        Args:
            volume (float): Floater volume (m³)
            submerged_fraction (float): Fraction of volume submerged (0-1)
            
        Returns:
            float: Buoyant force (N)
        """
        if volume <= 0 or submerged_fraction <= 0:
            return 0.0
            
        submerged_volume = volume * min(submerged_fraction, 1.0)
        buoyant_force = self.state.effective_density * self.gravity * submerged_volume
        
        logger.debug(f"Buoyant force: V={volume:.3f} m³, fraction={submerged_fraction:.2f}, "
                    f"ρ_eff={self.state.effective_density:.1f} kg/m³, F_b={buoyant_force:.1f} N")
        
        return buoyant_force
    
    def get_fluid_properties(self) -> Dict[str, float]:
        """
        Get current fluid properties for logging/monitoring.
        
        Returns:
            dict: Current fluid properties
        """
        return {
            'density': self.state.density,
            'effective_density': self.state.effective_density,
            'temperature': self.state.temperature,
            'nanobubble_fraction': self.state.nanobubble_fraction,
            'drag_coefficient': self.state.drag_coefficient,
            'reynolds_number': self.state.reynolds_number,
            'h1_active': self.h1_active
        }
    
    def set_h1_active(self, active: bool, bubble_fraction: Optional[float] = None, 
                      drag_reduction: Optional[float] = None):
        """
        Enable/disable H1 nanobubble effects.
        
        Args:
            active (bool): Whether to activate H1 effects
            bubble_fraction (float, optional): Bubble volume fraction (0-1)
            drag_reduction (float, optional): Drag reduction factor (0-1)
        """
        self.h1_active = active
        
        if bubble_fraction is not None:
            self.h1_bubble_fraction = max(0.0, min(bubble_fraction, 0.2))  # Limit to 20%
            
        if drag_reduction is not None:
            self.h1_drag_reduction = max(0.0, min(drag_reduction, 0.5))  # Limit to 50%
        
        self.update_state()
        
        logger.info(f"H1 nanobubbles {'activated' if active else 'deactivated'}: "
                   f"bubble_fraction={self.h1_bubble_fraction:.1%}, "
                   f"drag_reduction={self.h1_drag_reduction:.1%}")
    
    def set_temperature(self, temperature: float):
        """
        Set water temperature and update density.
        
        Args:
            temperature (float): Water temperature in Kelvin
        """
        self.base_temperature = max(273.15, min(temperature, 373.15))  # Limit to liquid range
        self.update_state()
        
        logger.info(f"Water temperature set to {self.base_temperature:.1f} K "
                   f"({self.base_temperature - 273.15:.1f}°C), "
                   f"density: {self.state.density:.1f} kg/m³")
