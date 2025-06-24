"""
Drivetrain & gearbox module.
Handles conversion of chain force to generator torque, gear ratio, and efficiency.

Drivetrain logic: chain, clutch, and generator coupling (H3 logic)
Manages drivetrain state and interactions with other modules
"""

import logging
import math
from typing import Optional
from utils.logging_setup import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

class Drivetrain:
    """
    Represents the mechanical drivetrain that converts chain force to generator torque.
    Handles gear ratio, efficiency, and clutch/flywheel dynamics.
    """
    def __init__(self, 
                 gear_ratio: float = 16.7, 
                 efficiency: float = 0.95, 
                 sprocket_radius: float = 0.5,
                 flywheel_inertia: float = 50.0,
                 chain_inertia: float = 5.0,
                 clutch_threshold: float = 0.1,
                 max_chain_speed_rpm: float = 30.0,
                 max_generator_rpm: float = 400.0,
                 bearing_friction_coeff: float = 0.02,
                 chain_friction_coeff: float = 0.05,
                 max_torque_capacity: float = 20000.0):
        """
        Initialize a Drivetrain.

        Args:
            gear_ratio (float): Ratio between chain sprocket and generator shaft.
            efficiency (float): Drivetrain efficiency (0-1).
            sprocket_radius (float): Radius of the chain sprocket (m).
            flywheel_inertia (float): Inertia of the flywheel (kg*m^2).
            chain_inertia (float): Inertia of the chain system (kg*m^2).
            clutch_threshold (float): Speed difference threshold for clutch engagement (rad/s).
            max_chain_speed_rpm (float): Maximum allowable chain speed (RPM).
            max_generator_rpm (float): Maximum allowable generator speed (RPM).
            bearing_friction_coeff (float): Friction coefficient for bearings.
            chain_friction_coeff (float): Friction coefficient for the chain.
            max_torque_capacity (float): Maximum torque the drivetrain can handle (Nm).
        """
        if gear_ratio <= 0 or not (0 <= efficiency <= 1) or sprocket_radius <= 0:
            logger.error("Invalid drivetrain parameters: gear_ratio and sprocket_radius must be positive, efficiency in [0,1].")
            raise ValueError("Invalid drivetrain parameters.")
        
        self.gear_ratio = gear_ratio
        self.efficiency = efficiency
        self.sprocket_radius = sprocket_radius
        self.I_flywheel = flywheel_inertia
        self.I_chain = chain_inertia
        self.omega_threshold = clutch_threshold
        self.max_chain_omega = max_chain_speed_rpm * (2 * math.pi / 60)
        self.max_generator_omega = max_generator_rpm * (2 * math.pi / 60)
        self.bearing_friction = bearing_friction_coeff
        self.chain_friction = chain_friction_coeff
        self.max_torque = max_torque_capacity

        # State variables
        self.omega_chain = 0.0      # rad/s
        self.omega_flywheel = 0.0   # rad/s
        self.clutch_engaged = False

        logger.info(f"Initialized Drivetrain with detailed physics.")

    def compute_input_torque(self, chain_force: float) -> float:
        """
        Calculate the input torque delivered to the sprocket from the chain.

        Args:
            chain_force (float): Net force from floaters on the chain (N)

        Returns:
            float: Input torque at the chain sprocket (Nm)
        """
        input_torque = chain_force * self.sprocket_radius * self.efficiency
        logger.debug(f"Computed input torque: {input_torque:.2f} Nm (chain_force={chain_force:.2f})")
        return input_torque

    def update_dynamics(self, net_torque: float, load_torque: float, dt: float):
        """
        Update flywheel and chain angular velocities with clutch dynamics.

        Args:
            net_torque (float): Net torque from floaters applied to the chain sprocket (Nm).
            load_torque (float): Resistive torque from the generator (Nm).
            dt (float): Time step (s).
        """
        net_torque = max(-self.max_torque, min(self.max_torque, net_torque))

        # Physics-based friction forces
        T_bearing_chain = self.bearing_friction * self.I_chain * 9.81 * self.omega_chain
        T_bearing_flywheel = self.bearing_friction * self.I_flywheel * 9.81 * self.omega_flywheel
        T_chain_friction = self.chain_friction * abs(self.omega_chain) * self.omega_chain
        
        T_drag_chain = T_bearing_chain + T_chain_friction
        T_drag_flywheel = T_bearing_flywheel + load_torque

        # Determine clutch engagement
        static_friction_threshold = 1.0  # Lowered from 10.0 Nm for easier startup
        speed_difference = abs(self.omega_chain - self.omega_flywheel / self.gear_ratio)
        # Add detailed logging for clutch logic
        logger.debug(f"Clutch logic: speed_difference={speed_difference:.4f}, omega_chain={self.omega_chain:.4f}, net_torque={net_torque:.4f}, static_friction_threshold={static_friction_threshold}")
        # Allow clutch engagement at zero speed if net torque is positive (creep mode)
        if (speed_difference < self.omega_threshold and self.omega_chain >= 0.0) or (self.omega_chain == 0.0 and net_torque > 0):
            logger.debug(f"Clutch engaged: (speed_difference < {self.omega_threshold})={speed_difference < self.omega_threshold}, (omega_chain >= 0.0)={self.omega_chain >= 0.0}, (omega_chain == 0.0 and net_torque > 0)={self.omega_chain == 0.0 and net_torque > 0}")
            self.clutch_engaged = True
            total_inertia = self.I_chain + (self.I_flywheel / (self.gear_ratio ** 2))
            net_force = net_torque - T_drag_chain - (T_drag_flywheel / self.gear_ratio)
            alpha_chain = net_force / total_inertia if total_inertia > 0 else 0
            self.omega_chain += alpha_chain * dt
            self.omega_flywheel = self.omega_chain * self.gear_ratio
        else:
            logger.debug(f"Clutch disengaged: (speed_difference >= {self.omega_threshold})={speed_difference >= self.omega_threshold}, (omega_chain < 0.0)={self.omega_chain < 0.0}, (omega_chain == 0.0 and net_torque <= 0)={self.omega_chain == 0.0 and net_torque <= 0}")
            self.clutch_engaged = False
            alpha_chain = (net_torque - T_drag_chain) / self.I_chain if self.I_chain > 0 else 0
            self.omega_chain += alpha_chain * dt
            
            alpha_flywheel = -T_drag_flywheel / self.I_flywheel if self.I_flywheel > 0 else 0
            self.omega_flywheel += alpha_flywheel * dt

        # Apply mechanical speed limits
        self.omega_chain = min(self.omega_chain, self.max_chain_omega)
        self.omega_flywheel = min(self.omega_flywheel, self.max_generator_omega)
        
        # Ensure non-negative speeds
        self.omega_chain = max(0.0, self.omega_chain)
        self.omega_flywheel = max(0.0, self.omega_flywheel)
        
        logger.debug(f"Drivetrain updated: omega_chain={self.omega_chain:.2f}, omega_flywheel={self.omega_flywheel:.2f}, clutch={self.clutch_engaged}")

    def get_state(self) -> dict:
        """
        Returns the current state of the drivetrain.
        """
        return {
            'omega_chain_rpm': self.omega_chain * 60 / (2 * math.pi),
            'omega_flywheel_rpm': self.omega_flywheel * 60 / (2 * math.pi),
            'clutch_engaged': self.clutch_engaged
        }

    def update_params(self, params: dict) -> None:
        """
        Update drivetrain parameters dynamically.

        Args:
            params (dict): Dictionary of parameters to update.
        """
        self.gear_ratio = params.get('gear_ratio', self.gear_ratio)
        self.efficiency = float(params.get('drivetrain_efficiency', self.efficiency))
        self.sprocket_radius = params.get('sprocket_radius', self.sprocket_radius)
        self.I_flywheel = params.get('flywheel_inertia', self.I_flywheel)
        logger.info(f"Updated Drivetrain params.")

    def reset(self):
        """
        Resets the drivetrain to its initial state.
        """
        self.omega_chain = 0.0
        self.omega_flywheel = 0.0
        self.clutch_engaged = False
        logger.info("Drivetrain state has been reset.")
