"""
Enhanced floater component with physics-based behavior.
"""

import math
from dataclasses import dataclass
from typing import Dict, Any, Optional

from simulation.schemas import FloaterState

@dataclass
class EnhancedFloaterConfig:
    """Configuration for enhanced floater"""
    volume: float  # m³
    mass_empty: float  # kg
    cross_section: float  # m²
    drag_coefficient: float = 0.8
    buoyancy_efficiency: float = 0.95
    max_velocity: float = 10.0  # m/s
    max_acceleration: float = 5.0  # m/s²

class EnhancedFloater:
    """
    Enhanced floater with physics-based behavior.
    Handles buoyancy, drag, and state transitions.
    """
    
    def __init__(self, config: EnhancedFloaterConfig):
        """Initialize floater with configuration"""
        self.config = config
        
        # Physical properties
        self.volume = config.volume
        self.mass_empty = config.mass_empty
        self.cross_section = config.cross_section
        self.drag_coefficient = config.drag_coefficient
        
        # Dynamic state
        self.position = 0.0
        self.velocity = 0.0
        self.acceleration = 0.0
        self.is_buoyant = False
        self.mass_water = 0.0
        self.mass_air = 0.0
        
        # Forces
        self.buoyant_force = 0.0
        self.drag_force = 0.0
        self.weight_force = 0.0
        self.net_force = 0.0
        
        # Enhancement effects
        self.h1_effect = None
        self.h2_effect = None
    
    def get_state(self) -> FloaterState:
        """Get current floater state"""
        return FloaterState(
            position=self.position,
            velocity=self.velocity,
            is_buoyant=self.is_buoyant,
            buoyant_force=self.buoyant_force,
            drag_force=self.drag_force,
            net_force=self.net_force,
            h1_effect=self.h1_effect,
            h2_effect=self.h2_effect
        )
    
    def set_state(self, state: FloaterState) -> None:
        """Set floater state"""
        self.position = state.position
        self.velocity = state.velocity
        self.is_buoyant = state.is_buoyant
        self.buoyant_force = state.buoyant_force
        self.drag_force = state.drag_force
        self.net_force = state.net_force
    
    def get_total_mass(self) -> float:
        """Get total mass including water/air"""
        return self.mass_empty + self.mass_water + self.mass_air
    
    def update(self, time_step: float, environment, gravity: float = 9.81) -> None:
        """
        Update floater state for one time step.
        
        Args:
            time_step: Time step in seconds
            environment: Environment component for water properties
            gravity: Gravitational acceleration (default 9.81 m/s²)
        """
        # Determine if floater is ascending (buoyant) for H1/H2 effects
        is_ascending = self.is_buoyant  # Use buoyant state instead of velocity
        
        # Get effective water density considering H1
        water_density = environment.compute_effective_density(is_ascending)
        
        # Get effective drag coefficient considering H1
        self.drag_coefficient = environment.compute_drag_coefficient(is_ascending, self.config.drag_coefficient)
        
        # Calculate forces with H1/H2 effects
        self._calculate_forces(environment, gravity)
        
        # Update motion
        self._update_motion(time_step)
        
        # Apply limits
        self._apply_limits()
        
        # Track enhancement effects
        if environment.h1_enabled:
            density_reduction = (environment.base_density - water_density) / environment.base_density
            drag_reduction = (self.config.drag_coefficient - self.drag_coefficient) / self.config.drag_coefficient
            self.h1_effect = {
                'density_reduction': density_reduction,
                'drag_reduction': drag_reduction
            }
        else:
            self.h1_effect = None
            
        if environment.h2_enabled and self.is_buoyant:
            buoyancy_calc = environment.compute_buoyant_force(self.volume, abs(self.position), is_ascending)
            self.h2_effect = {
                'volume_expansion': buoyancy_calc['effective_volume'] / self.volume - 1.0,
                'force_boost': buoyancy_calc['h2_boost']
            }
        else:
            self.h2_effect = None
    
    def _calculate_forces(self, environment, gravity: float) -> None:
        """Calculate all forces acting on floater"""
        # Weight force (always down)
        self.weight_force = -self.get_total_mass() * gravity
        
        # Buoyant force with H2 effects
        if self.is_buoyant:
            # Get buoyancy including thermal expansion
            buoyancy_calc = environment.compute_buoyant_force(
                self.volume,
                abs(self.position),
                self.velocity > 0
            )
            self.buoyant_force = buoyancy_calc['force'] * self.config.buoyancy_efficiency
        else:
            # When full of water, buoyant force mostly cancels water weight
            water_density = environment.compute_effective_density(self.velocity > 0)
            displaced_volume = self.volume  # Full volume still displaces water
            water_weight = water_density * displaced_volume * gravity
            self.buoyant_force = water_weight
        
        # Drag force (opposes motion)
        if self.velocity != 0:
            velocity_squared = self.velocity * abs(self.velocity)  # Preserves sign
            water_density = environment.compute_effective_density(self.velocity > 0)
            self.drag_force = -0.5 * self.drag_coefficient * water_density * self.cross_section * velocity_squared
        else:
            self.drag_force = 0.0
        
        # Net force
        self.net_force = self.buoyant_force + self.weight_force + self.drag_force
    
    def _update_motion(self, time_step: float) -> None:
        """Update position and velocity based on forces"""
        # Update acceleration
        self.acceleration = self.net_force / self.get_total_mass()
        
        # Update velocity (v = v0 + at)
        self.velocity += self.acceleration * time_step
        
        # Update position (x = x0 + vt + 1/2at²)
        self.position += self.velocity * time_step + 0.5 * self.acceleration * time_step * time_step
    
    def _apply_limits(self) -> None:
        """Apply velocity and acceleration limits"""
        # Limit velocity
        if abs(self.velocity) > self.config.max_velocity:
            self.velocity = math.copysign(self.config.max_velocity, self.velocity)
        
        # Limit acceleration
        if abs(self.acceleration) > self.config.max_acceleration:
            self.acceleration = math.copysign(self.config.max_acceleration, self.acceleration)
    
    def inject_air(self, environment, pneumatics) -> float:
        """
        Inject air into floater with H2 thermal effects.
        
        Args:
            environment: Environment component for water properties
            pneumatics: Pneumatic system component
            
        Returns:
            Energy required for injection
        """
        if not self.is_buoyant:
            self.is_buoyant = True
            self.mass_water = 0.0  # Expel water
            
            # Consider H2 thermal effects on air density
            if environment.h2_enabled:
                # Warmer air is less dense
                temp_factor = 1.0 - (environment.thermal_expansion_coeff * 20.0)  # Assume 20°C rise
                self.mass_air = 1.225 * self.volume * temp_factor
            else:
                self.mass_air = 1.225 * self.volume  # Fill with air at ~1.225 kg/m³
            
            # Get injection energy from pneumatic system
            return pneumatics.inject_air(self)
            
        return 0.0
    
    def vent_air(self) -> None:
        """Vent air from floater, making it sink"""
        if self.is_buoyant:
            self.is_buoyant = False
            self.mass_air = 0.0
            self.mass_water = 1000.0 * self.volume  # Fill with water 

    def set_buoyant(self, buoyant: bool) -> None:
        """Set the buoyant state of the floater"""
        self.is_buoyant = buoyant
        if buoyant:
            self.mass_water = 0.0
            self.mass_air = 1.225 * self.volume
        else:
            self.mass_air = 0.0
            self.mass_water = 1000.0 * self.volume

    def compute_torque(self, chain_radius: float) -> float:
        """Compute the torque contribution of this floater given the chain radius."""
        return self.net_force * chain_radius

    @property
    def is_ascending(self) -> bool:
        """Return True if the floater is moving upward (ascending), else False."""
        return self.velocity > 0 