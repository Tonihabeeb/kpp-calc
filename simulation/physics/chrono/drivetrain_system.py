"""
Enhanced mechanical drivetrain using PyChrono for realistic dynamics.
"""

import numpy as np
from typing import Dict, Any, Optional
import pychrono as chrono

class DrivetrainSystem:
    """Enhanced drivetrain system with PyChrono physics"""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize drivetrain system"""
        self.config = config
        
        # Mechanical parameters
        self.flywheel_inertia = config.get('flywheel_inertia', 10.0)  # kg*m^2
        self.shaft_inertia = config.get('shaft_inertia', 1.0)  # kg*m^2
        self.gearbox_ratio = config.get('gearbox_ratio', 1.0)  # no gearbox by default
        self.chain_radius = config.get('chain_radius', 1.0)  # m
        
        # Clutch parameters
        self.clutch_engaged = True
        self.one_way_clutch = config.get('one_way_clutch', True)
        self.clutch_friction = config.get('clutch_friction', 0.8)
        
        # System state
        self.angular_velocity = 0.0  # rad/s
        self.angular_position = 0.0  # rad
        self.torque_input = 0.0  # N*m
        self.torque_output = 0.0  # N*m
        
        # Energy tracking
        self.kinetic_energy = 0.0
        self.power_input = 0.0
        self.power_output = 0.0
        
        print("DrivetrainSystem initialized with PyChrono")
        
    def set_clutch_state(self, engaged: bool) -> None:
        """Set clutch engagement state"""
        self.clutch_engaged = engaged
        print(f"Clutch {'engaged' if engaged else 'disengaged'}")
        
    def apply_torque(self, torque: float) -> None:
        """Apply input torque to the drivetrain"""
        self.torque_input = torque
        
        # Apply gearbox ratio
        effective_torque = torque * self.gearbox_ratio
        
        # One-way clutch logic
        if self.one_way_clutch and effective_torque < 0:
            # Negative torque - one-way clutch prevents back-driving
            effective_torque = 0.0
            print("One-way clutch preventing negative torque")
            
        # Apply clutch engagement
        if not self.clutch_engaged:
            effective_torque = 0.0
            print("Clutch disengaged - no torque transmission")
            
        self.torque_output = effective_torque
        
    def update_dynamics(self, dt: float) -> None:
        """Update drivetrain dynamics for one time step"""
        # Calculate total inertia
        total_inertia = self.flywheel_inertia + self.shaft_inertia
        
        # Angular acceleration = torque / inertia
        angular_acceleration = self.torque_output / total_inertia
        
        # Update angular velocity (Euler integration)
        self.angular_velocity += angular_acceleration * dt
        
        # Update angular position
        self.angular_position += self.angular_velocity * dt
        
        # Calculate kinetic energy
        self.kinetic_energy = 0.5 * total_inertia * self.angular_velocity**2
        
        # Calculate power
        self.power_input = self.torque_input * self.angular_velocity
        self.power_output = self.torque_output * self.angular_velocity
        
    def get_angular_velocity(self) -> float:
        """Get current angular velocity in rad/s"""
        return self.angular_velocity
        
    def get_angular_velocity_rpm(self) -> float:
        """Get current angular velocity in RPM"""
        return self.angular_velocity * 60.0 / (2.0 * np.pi)
        
    def get_angular_position(self) -> float:
        """Get current angular position in radians"""
        return self.angular_position
        
    def get_chain_velocity(self) -> float:
        """Get chain linear velocity in m/s"""
        return self.angular_velocity * self.chain_radius
        
    def get_mechanical_power(self) -> float:
        """Get mechanical power output in W"""
        return self.power_output
        
    def get_kinetic_energy(self) -> float:
        """Get kinetic energy stored in flywheel in J"""
        return self.kinetic_energy
        
    def get_system_state(self) -> Dict[str, Any]:
        """Get complete system state"""
        return {
            'angular_velocity': self.angular_velocity,
            'angular_velocity_rpm': self.get_angular_velocity_rpm(),
            'angular_position': self.angular_position,
            'chain_velocity': self.get_chain_velocity(),
            'torque_input': self.torque_input,
            'torque_output': self.torque_output,
            'mechanical_power': self.power_output,
            'kinetic_energy': self.kinetic_energy,
            'clutch_engaged': self.clutch_engaged,
            'flywheel_inertia': self.flywheel_inertia,
            'total_inertia': self.flywheel_inertia + self.shaft_inertia
        }
