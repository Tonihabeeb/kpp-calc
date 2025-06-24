"""
Flywheel energy storage system for the KPP drivetrain.
Implements rotational energy buffering for smooth operation.
"""

import math
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class Flywheel:
    """
    Flywheel energy storage system that smooths out power pulses
    and provides rotational inertia for stable operation.
    """
    
    def __init__(self, moment_of_inertia: float = 500.0, max_speed: float = 400.0, 
                 mass: float = 1000.0, radius: float = 1.0):
        """
        Initialize the flywheel.
        
        Args:
            moment_of_inertia (float): Rotational inertia (kg·m²)
            max_speed (float): Maximum safe angular velocity (rad/s)
            mass (float): Flywheel mass (kg)
            radius (float): Effective radius for energy calculations (m)
        """
        self.moment_of_inertia = moment_of_inertia
        self.max_speed = max_speed
        self.mass = mass
        self.radius = radius
        
        # Dynamic state
        self.angular_velocity = 0.0  # rad/s
        self.angular_acceleration = 0.0  # rad/s²
        self.stored_energy = 0.0  # J
        self.applied_torque = 0.0  # N·m
        
        # Performance tracking
        self.peak_speed = 0.0  # rad/s
        self.total_energy_absorbed = 0.0  # J
        self.total_energy_released = 0.0  # J
        self.speed_variations = []  # For stability analysis
        
        # Physical properties
        self.friction_coefficient = 0.001  # Bearing friction
        self.windage_coefficient = 0.0001  # Air resistance
        self.temperature = 20.0  # °C
        
    def update(self, applied_torque: float, dt: float) -> float:
        """
        Update flywheel dynamics with applied torque.
        
        Args:
            applied_torque (float): Net torque applied to flywheel (N·m)
            dt (float): Time step (s)
            
        Returns:
            float: Reaction torque (opposing acceleration)
        """
        self.applied_torque = applied_torque
        
        # Calculate losses
        friction_torque = self._calculate_friction_losses()
        windage_torque = self._calculate_windage_losses()
        total_loss_torque = friction_torque + windage_torque
        
        # Net torque after losses
        if self.angular_velocity > 0:
            net_torque = applied_torque - total_loss_torque
        else:
            net_torque = applied_torque + total_loss_torque
        
        # Update angular acceleration and velocity
        self.angular_acceleration = net_torque / self.moment_of_inertia
        
        # Store previous velocity for energy tracking
        prev_velocity = self.angular_velocity
        
        # Update angular velocity with speed limiting
        self.angular_velocity += self.angular_acceleration * dt
        self.angular_velocity = max(-self.max_speed, min(self.max_speed, self.angular_velocity))
        
        # Update stored energy
        self.stored_energy = 0.5 * self.moment_of_inertia * self.angular_velocity**2
        
        # Track energy flow
        self._track_energy_flow(prev_velocity, dt)
        
        # Update performance metrics
        self.peak_speed = max(self.peak_speed, abs(self.angular_velocity))
        self.speed_variations.append(self.angular_velocity)
        
        # Keep only recent speed data for analysis
        if len(self.speed_variations) > 1000:
            self.speed_variations = self.speed_variations[-1000:]
        
        # Calculate reaction torque (inertial resistance)
        reaction_torque = self.moment_of_inertia * self.angular_acceleration
        
        logger.debug(f"Flywheel: speed={self.get_rpm():.1f} RPM, "
                    f"energy={self.stored_energy/1000:.1f} kJ, "
                    f"torque_applied={applied_torque:.1f} N·m, "
                    f"reaction={reaction_torque:.1f} N·m")
        
        return reaction_torque
    
    def _calculate_friction_losses(self) -> float:
        """
        Calculate bearing friction losses.
        
        Returns:
            float: Friction torque (N·m)
        """
        # Simple friction model: proportional to speed
        friction_torque = self.friction_coefficient * abs(self.angular_velocity) * self.mass * self.radius
        return friction_torque
    
    def _calculate_windage_losses(self) -> float:
        """
        Calculate aerodynamic losses (windage).
        
        Returns:
            float: Windage torque (N·m)
        """
        # Windage losses proportional to speed squared
        windage_torque = self.windage_coefficient * self.angular_velocity**2 * self.radius**3
        return abs(windage_torque)
    
    def _track_energy_flow(self, prev_velocity: float, dt: float):
        """
        Track energy absorption and release.
        
        Args:
            prev_velocity (float): Previous angular velocity (rad/s)
            dt (float): Time step (s)
        """
        # Calculate energy change
        prev_energy = 0.5 * self.moment_of_inertia * prev_velocity**2
        energy_change = self.stored_energy - prev_energy
        
        if energy_change > 0:
            self.total_energy_absorbed += energy_change
        else:
            self.total_energy_released += abs(energy_change)
    
    def get_rpm(self) -> float:
        """Get angular velocity in RPM."""
        return self.angular_velocity * 60 / (2 * math.pi)
    
    def get_speed_stability(self) -> float:
        """
        Calculate speed stability metric (coefficient of variation).
        
        Returns:
            float: Stability metric (lower is more stable)
        """
        if len(self.speed_variations) < 10:
            return 0.0
        
        recent_speeds = self.speed_variations[-100:]  # Last 100 samples
        if not recent_speeds:
            return 0.0
        
        mean_speed = sum(recent_speeds) / len(recent_speeds)
        if mean_speed == 0:
            return 0.0
        
        variance = sum((speed - mean_speed)**2 for speed in recent_speeds) / len(recent_speeds)
        std_dev = math.sqrt(variance)
        
        # Coefficient of variation (CV)
        cv = std_dev / abs(mean_speed)
        return cv
    
    def get_energy_efficiency(self) -> float:
        """
        Calculate energy efficiency (energy out / energy in).
        
        Returns:
            float: Efficiency ratio (0-1)
        """
        if self.total_energy_absorbed == 0:
            return 0.0
        
        return self.total_energy_released / self.total_energy_absorbed
    
    def apply_braking_torque(self, braking_torque: float) -> float:
        """
        Apply controlled braking for overspeed protection.
        
        Args:
            braking_torque (float): Braking torque to apply (N·m)
            
        Returns:
            float: Actual braking torque applied (N·m)
        """
        # Limit braking torque based on current speed
        max_braking = self.moment_of_inertia * 10.0  # Max 10 rad/s² deceleration
        actual_braking = min(braking_torque, max_braking)
        
        # Apply braking in direction opposite to rotation
        if self.angular_velocity > 0:
            return -actual_braking
        elif self.angular_velocity < 0:
            return actual_braking
        else:
            return 0.0
    
    def get_state(self) -> dict:
        """
        Get current flywheel state for monitoring and logging.
        
        Returns:
            dict: Flywheel state information
        """
        return {
            'angular_velocity_rpm': self.get_rpm(),
            'angular_velocity_rad_s': self.angular_velocity,
            'angular_acceleration': self.angular_acceleration,
            'stored_energy_kj': self.stored_energy / 1000.0,
            'applied_torque': self.applied_torque,
            'peak_speed_rpm': self.peak_speed * 60 / (2 * math.pi),
            'speed_stability': self.get_speed_stability(),
            'energy_efficiency': self.get_energy_efficiency(),
            'total_energy_absorbed_kj': self.total_energy_absorbed / 1000.0,
            'total_energy_released_kj': self.total_energy_released / 1000.0,
            'moment_of_inertia': self.moment_of_inertia,
            'temperature': self.temperature
        }
    
    def reset(self):
        """Reset the flywheel to initial conditions."""
        self.angular_velocity = 0.0
        self.angular_acceleration = 0.0
        self.stored_energy = 0.0
        self.applied_torque = 0.0
        self.peak_speed = 0.0
        self.total_energy_absorbed = 0.0
        self.total_energy_released = 0.0
        self.speed_variations = []


class FlywheelController:
    """
    Controller for optimizing flywheel operation and coordinating
    with other drivetrain components.
    """
    
    def __init__(self, flywheel: Flywheel, target_speed: float = 375.0):
        """
        Initialize the flywheel controller.
        
        Args:
            flywheel (Flywheel): The flywheel to control
            target_speed (float): Target angular velocity (rad/s)
        """
        self.flywheel = flywheel
        self.target_speed = target_speed
        
        # Control parameters
        self.speed_tolerance = 0.1 * target_speed  # 10% tolerance
        self.overspeed_limit = 1.2 * target_speed  # 20% overspeed limit
        
        # PID control parameters
        self.kp = 100.0  # Proportional gain
        self.ki = 10.0   # Integral gain
        self.kd = 1.0    # Derivative gain
        
        # PID state
        self.integral_error = 0.0
        self.previous_error = 0.0
        
        # Performance tracking
        self.control_interventions = 0
        self.overspeed_events = 0
    
    def update(self, input_torque: float, dt: float) -> tuple[float, bool]:
        """
        Update flywheel with speed control.
        
        Args:
            input_torque (float): Input torque from drivetrain (N·m)
            dt (float): Time step (s)
            
        Returns:
            tuple[float, bool]: (reaction_torque, overspeed_protection_active)
        """
        current_speed = self.flywheel.angular_velocity
        
        # Check for overspeed condition
        overspeed_active = False
        if abs(current_speed) > self.overspeed_limit:
            overspeed_active = True
            self.overspeed_events += 1
            
            # Apply emergency braking
            braking_torque = self.flywheel.apply_braking_torque(1000.0)
            total_torque = input_torque + braking_torque
            
            logger.warning(f"Flywheel overspeed: {self.flywheel.get_rpm():.1f} RPM, applying braking")
        else:
            total_torque = input_torque
        
        # Update flywheel with total torque
        reaction_torque = self.flywheel.update(total_torque, dt)
        
        return reaction_torque, overspeed_active
    
    def calculate_pid_correction(self, dt: float) -> float:
        """
        Calculate PID correction for speed control.
        
        Args:
            dt (float): Time step (s)
            
        Returns:
            float: Correction torque (N·m)
        """
        current_speed = self.flywheel.angular_velocity
        error = self.target_speed - current_speed
        
        # PID calculations
        self.integral_error += error * dt
        derivative_error = (error - self.previous_error) / dt if dt > 0 else 0.0
        
        # Calculate correction torque
        correction = (self.kp * error + 
                     self.ki * self.integral_error + 
                     self.kd * derivative_error)
        
        # Limit correction magnitude
        max_correction = 500.0  # N·m
        correction = max(-max_correction, min(max_correction, correction))
        
        self.previous_error = error
        
        if abs(correction) > 10.0:  # Only count significant interventions
            self.control_interventions += 1
        
        return correction
    
    def get_state(self) -> dict:
        """Get controller state."""
        state = self.flywheel.get_state()
        state.update({
            'target_speed_rpm': self.target_speed * 60 / (2 * math.pi),
            'speed_error': self.target_speed - self.flywheel.angular_velocity,
            'control_interventions': self.control_interventions,
            'overspeed_events': self.overspeed_events,
            'integral_error': self.integral_error
        })
        return state
