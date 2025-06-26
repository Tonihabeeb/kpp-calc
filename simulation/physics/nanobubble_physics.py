"""
H1 Nanobubble Physics Implementation
Enhances drag and density reduction for descending floaters through nanobubble injection.

This module implements Hypothesis 1: nanobubbles injected into the water around
descending floaters reduce effective fluid density and drag, improving overall efficiency.
"""

import math
import logging
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class NanobubbleState:
    """Current state of nanobubble system for a floater"""
    active: bool = False
    bubble_fraction: float = 0.0  # Volume fraction of nanobubbles (0-1)
    effective_density: float = 1000.0  # kg/m³
    drag_reduction: float = 0.0  # Fraction (0-1)
    injection_rate: float = 0.0  # Bubble injection rate (m³/s)
    energy_cost: float = 0.0  # Energy cost for nanobubble generation (W)

class NanobubblePhysics:
    """
    Manages H1 nanobubble effects for KPP floaters.
    
    Applies to descending floaters only to reduce drag and increase
    relative buoyancy of ascending floaters by comparison.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize nanobubble physics.
        
        Args:
            config (dict): Configuration parameters
        """
        if config is None:
            config = {}
        
        # Physical constants
        self.water_density = config.get('water_density', 1000.0)  # kg/m³
        self.air_density = config.get('air_density', 1.225)  # kg/m³
        self.gravity = config.get('gravity', 9.81)  # m/s²
        
        # H1 parameters
        self.h1_enabled = config.get('h1_enabled', False)
        self.base_bubble_fraction = config.get('nanobubble_fraction', 0.05)  # 5% default
        self.max_bubble_fraction = config.get('max_nanobubble_fraction', 0.15)  # 15% maximum
        self.base_drag_reduction = config.get('drag_reduction_factor', 0.12)  # 12% default
        self.max_drag_reduction = config.get('max_drag_reduction', 0.30)  # 30% maximum
        
        # Bubble generation parameters
        self.bubble_generator_power = config.get('bubble_generator_power', 2500.0)  # W
        self.generation_efficiency = config.get('generation_efficiency', 0.75)  # 75% efficient
        self.bubble_dissolution_rate = config.get('dissolution_rate', 0.02)  # 2% per second
        
        # Velocity dependence parameters
        self.velocity_threshold = config.get('velocity_threshold', 0.5)  # m/s
        self.velocity_scaling_factor = config.get('velocity_scaling', 1.5)
        
        logger.info(f"Nanobubble physics initialized - H1 enabled: {self.h1_enabled}, "
                   f"base fraction: {self.base_bubble_fraction:.1%}, "
                   f"base drag reduction: {self.base_drag_reduction:.1%}")
    
    def apply_nanobubble_effects(self, floater, velocity: float, is_descending: bool) -> NanobubbleState:
        """
        Apply H1 nanobubble effects to a floater.
        
        Args:
            floater: Floater object
            velocity (float): Current velocity (m/s)
            is_descending (bool): True if floater is descending
            
        Returns:
            NanobubbleState: Current nanobubble effects
        """
        state = NanobubbleState()
        
        # Only apply to descending floaters when H1 is enabled
        if not self.h1_enabled or not is_descending:
            state.effective_density = self.water_density
            return state
        
        # Calculate velocity-dependent enhancement
        velocity_factor = self._calculate_velocity_factor(abs(velocity))
        
        # Calculate effective bubble fraction
        effective_fraction = min(
            self.base_bubble_fraction * velocity_factor,
            self.max_bubble_fraction
        )
        
        # Calculate effective density reduction
        state.bubble_fraction = effective_fraction
        state.effective_density = self._calculate_effective_density(effective_fraction)
        
        # Calculate drag reduction
        state.drag_reduction = min(
            self.base_drag_reduction * velocity_factor,
            self.max_drag_reduction
        )
        
        # Calculate injection requirements and energy cost
        floater_volume = getattr(floater, 'volume', 0.3)  # m³
        bubble_volume_rate = effective_fraction * floater_volume * self.bubble_dissolution_rate
        
        state.injection_rate = bubble_volume_rate
        state.energy_cost = self._calculate_energy_cost(bubble_volume_rate)
        state.active = True
        
        logger.debug(f"H1 nanobubbles active: fraction={effective_fraction:.1%}, "
                    f"density={state.effective_density:.1f} kg/m³, "
                    f"drag_reduction={state.drag_reduction:.1%}, "
                    f"energy_cost={state.energy_cost:.1f} W")
        
        return state
    
    def _calculate_velocity_factor(self, velocity: float) -> float:
        """
        Calculate velocity-dependent scaling factor for nanobubble effects.
        
        Higher velocities get more benefit from nanobubbles.
        
        Args:
            velocity (float): Velocity magnitude (m/s)
            
        Returns:
            float: Scaling factor (>= 1.0)
        """
        if velocity < self.velocity_threshold:
            return 1.0
        
        # Logarithmic scaling for realistic behavior
        excess_velocity = velocity - self.velocity_threshold
        scaling = 1.0 + self.velocity_scaling_factor * math.log(1 + excess_velocity)
        
        return min(scaling, 3.0)  # Limit to 3x enhancement maximum
    
    def _calculate_effective_density(self, bubble_fraction: float) -> float:
        """
        Calculate effective fluid density with nanobubbles.
        
        Uses mixture rule: ρ_eff = ρ_water * (1-α) + ρ_air * α
        where α is bubble volume fraction.
        
        Args:
            bubble_fraction (float): Volume fraction of bubbles
            
        Returns:
            float: Effective density (kg/m³)
        """
        if bubble_fraction <= 0:
            return self.water_density
        
        effective_density = (self.water_density * (1 - bubble_fraction) + 
                           self.air_density * bubble_fraction)
        
        return max(effective_density, 800.0)  # Minimum reasonable density
    
    def _calculate_energy_cost(self, bubble_volume_rate: float) -> float:
        """
        Calculate energy cost for nanobubble generation.
        
        Args:
            bubble_volume_rate (float): Volume rate of bubble generation (m³/s)
            
        Returns:
            float: Power required (W)
        """
        if bubble_volume_rate <= 0:
            return 0.0
        
        # Based on compressed air energy and generation efficiency
        # Approximate energy: P = ρ_air * g * h * Q / η
        # where h is effective "lifting" height for bubble compression
        effective_height = 2.0  # meters equivalent pressure head
        
        ideal_power = (self.air_density * self.gravity * effective_height * 
                      bubble_volume_rate)
        
        actual_power = ideal_power / self.generation_efficiency
        
        return min(actual_power, self.bubble_generator_power)  # Limit to generator capacity
    
    def calculate_buoyancy_enhancement(self, base_buoyancy: float, 
                                     nanobubble_state: NanobubbleState) -> float:
        """
        Calculate enhanced buoyancy due to nanobubble density reduction.
        
        Enhanced buoyancy comes from reduced effective fluid density around
        the floater, making it relatively more buoyant.
        
        Args:
            base_buoyancy (float): Base buoyant force (N)
            nanobubble_state (NanobubbleState): Current nanobubble state
            
        Returns:
            float: Enhanced buoyant force (N)
        """
        if not nanobubble_state.active:
            return base_buoyancy
        
        # Calculate relative density change
        density_ratio = nanobubble_state.effective_density / self.water_density
        
        # Enhanced buoyancy is inversely proportional to fluid density
        enhanced_buoyancy = base_buoyancy / density_ratio
        
        logger.debug(f"Buoyancy enhancement: density_ratio={density_ratio:.3f}, "
                    f"buoyancy: {base_buoyancy:.1f} → {enhanced_buoyancy:.1f} N")
        
        return enhanced_buoyancy
    
    def calculate_drag_force_with_nanobubbles(self, base_drag: float, 
                                            nanobubble_state: NanobubbleState) -> float:
        """
        Calculate reduced drag force with nanobubble effects.
        
        Args:
            base_drag (float): Base drag force (N)
            nanobubble_state (NanobubbleState): Current nanobubble state
            
        Returns:
            float: Reduced drag force (N)
        """
        if not nanobubble_state.active:
            return base_drag
        
        # Apply both density and surface effects
        density_factor = nanobubble_state.effective_density / self.water_density
        surface_factor = 1 - nanobubble_state.drag_reduction
        
        # Drag is proportional to density, also reduced by surface effects
        reduced_drag = base_drag * density_factor * surface_factor
        
        logger.debug(f"Drag reduction: density_factor={density_factor:.3f}, "
                    f"surface_factor={surface_factor:.3f}, "
                    f"drag: {base_drag:.1f} → {reduced_drag:.1f} N")
        
        return reduced_drag
    
    def get_system_status(self) -> Dict[str, Any]:
        """
        Get current nanobubble system status.
        
        Returns:
            dict: System status information
        """
        return {
            'h1_enabled': self.h1_enabled,
            'base_bubble_fraction': self.base_bubble_fraction,
            'max_bubble_fraction': self.max_bubble_fraction,
            'base_drag_reduction': self.base_drag_reduction,
            'max_drag_reduction': self.max_drag_reduction,
            'generator_power': self.bubble_generator_power,
            'generation_efficiency': self.generation_efficiency
        }
    
    def set_h1_enabled(self, enabled: bool):
        """
        Enable or disable H1 nanobubble effects.
        
        Args:
            enabled (bool): Whether to enable H1 effects
        """
        self.h1_enabled = enabled
        logger.info(f"H1 nanobubble physics {'enabled' if enabled else 'disabled'}")
    
    def update_parameters(self, params: Dict[str, Any]):
        """
        Update nanobubble physics parameters.
        
        Args:
            params (dict): Parameter updates
        """
        if 'nanobubble_fraction' in params:
            self.base_bubble_fraction = max(0.0, min(params['nanobubble_fraction'], 0.2))
        
        if 'h1_enabled' in params:
            self.h1_enabled = bool(params['h1_enabled'])
        
        logger.info(f"Nanobubble parameters updated: fraction={self.base_bubble_fraction:.1%}, "
                   f"enabled={self.h1_enabled}")
