"""
Drivetrain module for KPP simulation.
Handles torque calculations, flywheel dynamics, and H3 clutch mechanism.
"""

from dataclasses import dataclass
from typing import Optional
import math

@dataclass
class DrivetrainConfig:
    """Configuration parameters for drivetrain system"""
    # Basic parameters
    chain_radius: float = 1.0  # m
    generator_efficiency: float = 0.95  # Generator conversion efficiency
    mechanical_efficiency: float = 0.90  # Mechanical transmission efficiency
    base_inertia: float = 5.0  # kg·m² (chain + sprockets)
    
    # H3 enhancement parameters
    enable_h3: bool = False  # Enable pulse-and-coast
    flywheel_inertia: float = 10.0  # kg·m² (additional flywheel)
    clutch_engagement_threshold: float = 0.7  # Torque threshold for engagement (0-1)
    clutch_response_time: float = 0.1  # s, Time for clutch to fully engage/disengage
    min_operating_speed: float = 1.0  # rad/s, Minimum speed to maintain
    max_operating_speed: float = 10.0  # rad/s, Maximum safe speed

class Drivetrain:
    """
    Drivetrain system with H3 enhancement support.
    
    Features:
    - Torque calculations from net force
    - Flywheel dynamics and energy storage
    - H3 clutch mechanism for pulse-and-coast
    - Generator coupling and power conversion
    """
    
    def __init__(self, config: Optional[DrivetrainConfig] = None):
        """Initialize drivetrain with given configuration"""
        self.config = config or DrivetrainConfig()
        
        # State variables
        self.angular_velocity = 0.0  # rad/s
        self.angular_position = 0.0  # rad
        self.clutch_engagement = 0.0  # 0 = disengaged, 1 = fully engaged
        self.generator_torque = 0.0  # N·m
        
        # Energy tracking
        self.kinetic_energy = 0.0  # J
        self.output_energy = 0.0  # J
        self.current_power = 0.0  # W
        
        # Calculate total inertia
        self.total_inertia = self.config.base_inertia
        if self.config.enable_h3:
            self.total_inertia += self.config.flywheel_inertia
    
    def get_effective_inertia(self) -> float:
        """
        Get effective rotational inertia of the system.
        
        Returns:
            Total rotational inertia in kg·m²
        """
        return self.total_inertia
    
    def update_clutch_state(self, net_torque: float, dt: float) -> None:
        """
        Update clutch engagement based on H3 logic.
        
        Args:
            net_torque: Current net torque (N·m)
            dt: Time step duration (s)
        """
        if not self.config.enable_h3:
            self.clutch_engagement = 1.0  # Always engaged if H3 disabled
            return
            
        # Normalize torque relative to threshold
        torque_ratio = abs(net_torque) / (self.config.clutch_engagement_threshold * self.total_inertia)
        
        # Determine target engagement
        if torque_ratio > 1.0:
            target_engagement = 1.0  # Engage when torque is high
        else:
            target_engagement = 0.0  # Disengage to coast
        
        # Smooth engagement transition
        rate = dt / self.config.clutch_response_time
        if target_engagement > self.clutch_engagement:
            self.clutch_engagement = min(1.0, self.clutch_engagement + rate)
        else:
            self.clutch_engagement = max(0.0, self.clutch_engagement - rate)
    
    def compute_generator_torque(self) -> float:
        """
        Compute generator resistive torque based on current state.
        
        Returns:
            Generator torque in N·m
        """
        # Base generator torque proportional to speed
        base_torque = -0.5 * self.angular_velocity  # Simple linear model
        
        # Apply clutch engagement factor
        effective_torque = base_torque * self.clutch_engagement
        
        return effective_torque
    
    def update_state(self, net_torque: float, dt: float) -> None:
        """
        Update drivetrain state for one time step.
        
        Args:
            net_torque: Net torque from floaters (N·m)
            dt: Time step duration (s)
        """
        # Update clutch state
        self.update_clutch_state(net_torque, dt)
        
        # Get generator torque
        self.generator_torque = self.compute_generator_torque()
        
        # Compute total torque
        total_torque = (net_torque + self.generator_torque) * self.config.mechanical_efficiency
        
        # Update angular velocity (ω' = τ/I)
        angular_acceleration = total_torque / self.total_inertia
        self.angular_velocity += angular_acceleration * dt
        
        # Enforce speed limits
        self.angular_velocity = max(self.config.min_operating_speed,
                                  min(self.angular_velocity, self.config.max_operating_speed))
        
        # Update position
        self.angular_position += self.angular_velocity * dt
        
        # Update energy tracking
        self.kinetic_energy = 0.5 * self.total_inertia * self.angular_velocity ** 2
        
        # Calculate output power and energy
        if self.clutch_engagement > 0:
            output_power = -self.generator_torque * self.angular_velocity * self.config.generator_efficiency
            self.output_energy += output_power * dt
            self.current_power = output_power
        else:
            self.current_power = 0.0
    
    def get_chain_velocity(self) -> float:
        """
        Get linear chain velocity.
        
        Returns:
            Chain velocity in m/s
        """
        return self.angular_velocity * self.config.chain_radius
    
    def get_state(self) -> dict:
        """
        Get current drivetrain state.
        
        Returns:
            Dictionary of current state values
        """
        return {
            'angular_velocity': self.angular_velocity,
            'angular_position': self.angular_position,
            'clutch_engagement': self.clutch_engagement,
            'kinetic_energy': self.kinetic_energy,
            'output_energy': self.output_energy,
            'current_power': self.current_power,
            'h3_active': self.config.enable_h3
        }
    
    def reset(self) -> None:
        """Reset drivetrain state"""
        self.angular_velocity = 0.0
        self.angular_position = 0.0
        self.clutch_engagement = 0.0
        self.generator_torque = 0.0
        self.kinetic_energy = 0.0
        self.output_energy = 0.0
        self.current_power = 0.0

    def set_h3_enabled(self, enabled: bool) -> None:
        """
        Enable or disable H3 enhancement (pulse-and-coast).
        
        Args:
            enabled: Whether to enable H3 enhancement
        """
        if enabled != self.config.enable_h3:
            self.config.enable_h3 = enabled
            
            # Recalculate total inertia
            self.total_inertia = self.config.base_inertia
            if enabled:
                self.total_inertia += self.config.flywheel_inertia
                
            # Reset clutch state when changing H3 mode
            self.clutch_engagement = 1.0 if not enabled else 0.0
            
            # Reset energy tracking
            self.kinetic_energy = 0.0
            self.output_energy = 0.0
            self.current_power = 0.0
    
    def set_flywheel_inertia(self, inertia: float) -> None:
        """
        Set flywheel inertia for H3 enhancement.
        
        Args:
            inertia: Flywheel inertia in kg·m²
        """
        self.config.flywheel_inertia = inertia
        
        # Recalculate total inertia if H3 is enabled
        if self.config.enable_h3:
            self.total_inertia = self.config.base_inertia + inertia 

    @property
    def chain_radius(self) -> float:
        """Return the chain radius from the config."""
        return self.config.chain_radius 

    def update(self, time_step: float, net_torque: float) -> None:
        """Update drivetrain state for one time step (non-H3 mode)."""
        self.update_state(net_torque, time_step) 