"""
Integrated drivetrain system combining sprockets, gearbox, clutch, and flywheel.
This represents the complete mechanical power transmission system for the KPP.
"""

import math
from typing import Optional, Dict, Any
import logging

from .sprocket import Sprocket
from .gearbox import create_kpp_gearbox, Gearbox
from .one_way_clutch import OneWayClutch, PulseCoastController
from .flywheel import Flywheel, FlywheelController

logger = logging.getLogger(__name__)


class IntegratedDrivetrain:
    """
    Complete drivetrain system integrating all mechanical components
    from chain tension input to generator output.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the integrated drivetrain system.
        
        Args:
            config (dict): Configuration parameters for all components
        """
        if config is None:
            config = {}
        
        # Initialize all drivetrain components
        self.top_sprocket = Sprocket(
            radius=config.get('sprocket_radius', 1.0),
            tooth_count=config.get('sprocket_teeth', 20),
            position='top'
        )
        
        self.bottom_sprocket = Sprocket(
            radius=config.get('sprocket_radius', 1.0),
            tooth_count=config.get('sprocket_teeth', 20),
            position='bottom'
        )
        
        self.gearbox = create_kpp_gearbox()
        
        self.one_way_clutch = OneWayClutch(
            engagement_threshold=config.get('clutch_engagement_threshold', 0.1),
            disengagement_threshold=config.get('clutch_disengagement_threshold', -0.05),
            max_torque=config.get('clutch_max_torque', 10000.0)
        )
        
        self.flywheel = Flywheel(
            moment_of_inertia=config.get('flywheel_inertia', 500.0),
            max_speed=config.get('flywheel_max_speed', 400.0),
            mass=config.get('flywheel_mass', 1000.0)
        )
        
        # Controllers
        self.pulse_coast_controller = PulseCoastController(self.one_way_clutch)
        self.flywheel_controller = FlywheelController(
            self.flywheel, 
            target_speed=config.get('target_generator_speed', 375.0) * 2 * math.pi / 60  # Convert RPM to rad/s
        )
        
        # System state
        self.chain_tension = 0.0  # N
        self.generator_load_torque = 0.0  # N·m
        self.total_power_loss = 0.0  # W
        self.system_efficiency = 0.0
        
        # Performance tracking
        self.total_energy_input = 0.0  # J
        self.total_energy_output = 0.0  # J
        self.operating_time = 0.0  # s
        
    def update(self, chain_tension: float, generator_load_torque: float, dt: float) -> Dict[str, float]:
        """
        Update the complete drivetrain system.
        
        Args:
            chain_tension (float): Tension in the chain from floaters (N)
            generator_load_torque (float): Load torque from generator (N·m)
            dt (float): Time step (s)
            
        Returns:
            dict: System outputs including power, torque, and speeds
        """
        self.chain_tension = chain_tension
        self.generator_load_torque = generator_load_torque
        self.operating_time += dt
        
        # Step 1: Convert chain tension to rotational torque via sprocket
        self.top_sprocket.update(chain_tension, dt)
        sprocket_power = self.top_sprocket.get_power_output()
        
        # Step 2: Speed and torque conversion through gearbox
        self.gearbox.update(self.top_sprocket.angular_velocity, self.top_sprocket.torque)
        gearbox_power = self.gearbox.get_output_power()
        
        # Step 3: Pulse-and-coast operation through one-way clutch
        clutch_output_torque = self.pulse_coast_controller.update(
            self.gearbox.output_torque,
            self.gearbox.output_shaft_speed,
            self.flywheel.angular_velocity,
            dt
        )
        
        # Step 4: Energy buffering and speed stabilization via flywheel
        # The flywheel receives input from clutch and provides output to generator
        net_flywheel_torque = clutch_output_torque - generator_load_torque
        flywheel_reaction, overspeed_active = self.flywheel_controller.update(net_flywheel_torque, dt)
        
        # Step 5: Calculate system outputs
        outputs = self._calculate_system_outputs()
        
        # Step 6: Update performance metrics
        self._update_performance_metrics(dt)
        
        logger.debug(f"Drivetrain: chain={chain_tension:.0f}N → sprocket={self.top_sprocket.torque:.0f}N·m → "
                    f"gearbox={self.gearbox.output_torque:.0f}N·m → flywheel={self.flywheel.get_rpm():.0f}RPM")
        
        return outputs
    
    def _calculate_system_outputs(self) -> Dict[str, float]:
        """
        Calculate all system outputs for monitoring and control.
        
        Returns:
            dict: Complete system state and outputs
        """
        # Power calculations
        input_power = self.chain_tension * self.top_sprocket.get_chain_speed()
        output_power = self.generator_load_torque * self.flywheel.angular_velocity
        
        # Efficiency calculation
        if input_power > 0:
            self.system_efficiency = output_power / input_power
        else:
            self.system_efficiency = 0.0
        
        # Total power losses
        self.total_power_loss = (self.top_sprocket.drive_shaft.power * (1 - self.top_sprocket.efficiency) +
                               self.gearbox.total_power_loss +
                               self.one_way_clutch.engagement_losses)
        
        return {
            # Power flow
            'input_power': input_power,
            'output_power': output_power,
            'power_loss': self.total_power_loss,
            'system_efficiency': self.system_efficiency,
            
            # Speeds (RPM)
            'chain_speed_rpm': self.top_sprocket.get_rpm(),
            'gearbox_input_rpm': self.gearbox.get_input_rpm(),
            'gearbox_output_rpm': self.gearbox.get_output_rpm(),
            'flywheel_speed_rpm': self.flywheel.get_rpm(),
            
            # Torques (N·m)
            'chain_tension': self.chain_tension,
            'sprocket_torque': self.top_sprocket.torque,
            'gearbox_output_torque': self.gearbox.output_torque,
            'clutch_transmitted_torque': self.one_way_clutch.transmitted_torque,
            'generator_load_torque': self.generator_load_torque,
            
            # Flywheel state
            'flywheel_stored_energy': self.flywheel.stored_energy,
            'flywheel_speed_stability': self.flywheel.get_speed_stability(),
            
            # Clutch state
            'clutch_engaged': self.one_way_clutch.is_engaged,
            'clutch_engagement_factor': self.one_way_clutch.engagement_factor,
            
            # System metrics
            'overall_gear_ratio': self.gearbox.overall_ratio,
            'operating_time': self.operating_time
        }
    
    def _update_performance_metrics(self, dt: float):
        """
        Update long-term performance tracking metrics.
        
        Args:
            dt (float): Time step (s)
        """
        # Energy tracking
        input_power = self.chain_tension * self.top_sprocket.get_chain_speed()
        output_power = self.generator_load_torque * self.flywheel.angular_velocity
        
        self.total_energy_input += input_power * dt
        self.total_energy_output += output_power * dt
    
    def get_comprehensive_state(self) -> Dict[str, Any]:
        """
        Get comprehensive state information from all components.
        
        Returns:
            dict: Complete drivetrain state
        """
        return {
            'sprocket': {
                'top': {
                    'torque': self.top_sprocket.torque,
                    'speed_rpm': self.top_sprocket.get_rpm(),
                    'chain_speed': self.top_sprocket.get_chain_speed(),
                    'power_output': self.top_sprocket.get_power_output()
                }
            },
            'gearbox': {
                'input_speed_rpm': self.gearbox.get_input_rpm(),
                'output_speed_rpm': self.gearbox.get_output_rpm(),
                'input_torque': self.gearbox.input_torque,
                'output_torque': self.gearbox.output_torque,
                'overall_ratio': self.gearbox.overall_ratio,
                'efficiency': self.gearbox.overall_efficiency,
                'power_loss': self.gearbox.total_power_loss
            },
            'clutch': self.one_way_clutch.get_state(),
            'flywheel': self.flywheel.get_state(),
            'pulse_coast_controller': self.pulse_coast_controller.get_state(),
            'flywheel_controller': self.flywheel_controller.get_state(),
            'system': {
                'efficiency': self.system_efficiency,
                'total_power_loss': self.total_power_loss,
                'total_energy_input_kj': self.total_energy_input / 1000.0,
                'total_energy_output_kj': self.total_energy_output / 1000.0,
                'operating_time': self.operating_time
            }
        }
    
    def reset(self):
        """Reset all drivetrain components to initial conditions."""
        self.top_sprocket.reset()
        self.bottom_sprocket.reset()
        self.gearbox.reset()
        self.one_way_clutch.reset()
        self.flywheel.reset()
        
        # Reset system state
        self.chain_tension = 0.0
        self.generator_load_torque = 0.0
        self.total_power_loss = 0.0
        self.system_efficiency = 0.0
        self.total_energy_input = 0.0
        self.total_energy_output = 0.0
        self.operating_time = 0.0
    
    def apply_emergency_stop(self):
        """Apply emergency braking to stop the system safely."""
        # Apply maximum braking to flywheel
        emergency_braking_torque = 2000.0  # N·m
        self.flywheel.apply_braking_torque(emergency_braking_torque)
        
        # Disengage clutch
        self.one_way_clutch.is_engaged = False
        self.one_way_clutch.engagement_factor = 0.0
        
        logger.warning("Emergency stop applied to drivetrain")
    
    def get_power_flow_summary(self) -> str:
        """
        Get a human-readable summary of power flow through the system.
        
        Returns:
            str: Power flow summary
        """
        state = self._calculate_system_outputs()
        
        return (f"Power Flow: {state['input_power']:.0f}W input → "
                f"Sprocket({self.top_sprocket.efficiency*100:.1f}%) → "
                f"Gearbox({self.gearbox.overall_efficiency*100:.1f}%, {self.gearbox.overall_ratio:.1f}:1) → "                f"Clutch({'ENGAGED' if self.one_way_clutch.is_engaged else 'COAST'}) → "
                f"Flywheel({self.flywheel.get_rpm():.0f}RPM, {self.flywheel.stored_energy/1000:.1f}kJ) → "
                f"{state['output_power']:.0f}W output "
                f"(η={state['system_efficiency']*100:.1f}%)")
    
    def get_status(self) -> Dict[str, float]:
        """
        Get current status of the integrated drivetrain system
        
        Returns:
            Dict containing current drivetrain status data
        """
        return {
            'shaft_speed': self.flywheel.angular_velocity * 60 / (2 * math.pi),  # Convert to RPM
            'flywheel_speed': self.flywheel.angular_velocity * 60 / (2 * math.pi),
            'gearbox_ratio': self.gearbox.overall_ratio,
            'gearbox_efficiency': self.gearbox.overall_efficiency,
            'chain_tension': self.chain_tension,
            'generator_load_torque': self.generator_load_torque,
            'power_loss': self.total_power_loss,
            'system_efficiency': self.system_efficiency,
            'input_energy': self.total_energy_input,
            'output_energy': self.total_energy_output,
            'operating_time': self.operating_time
        }


def create_standard_kpp_drivetrain(config: Optional[Dict[str, Any]] = None) -> IntegratedDrivetrain:
    """
    Create a standard KPP drivetrain configuration based on the technical specifications.
    
    Args:
        config (dict): Optional configuration overrides
        
    Returns:
        IntegratedDrivetrain: Configured drivetrain system
    """
    standard_config = {
        'sprocket_radius': 1.0,  # m
        'sprocket_teeth': 20,
        'flywheel_inertia': 500.0,  # kg·m²
        'flywheel_max_speed': 400.0,  # rad/s (~3800 RPM)
        'flywheel_mass': 1000.0,  # kg
        'target_generator_speed': 375.0,  # RPM
        'clutch_engagement_threshold': 0.1,  # rad/s
        'clutch_disengagement_threshold': -0.05,  # rad/s
        'clutch_max_torque': 15000.0  # N·m
    }
    
    if config:
        standard_config.update(config)
    
    drivetrain = IntegratedDrivetrain(standard_config)
    
    logger.info(f"Created standard KPP drivetrain: "
               f"gear_ratio={drivetrain.gearbox.overall_ratio:.1f}:1, "
               f"flywheel_inertia={drivetrain.flywheel.moment_of_inertia:.0f}kg·m², "
               f"target_speed={standard_config['target_generator_speed']:.0f}RPM")
    
    return drivetrain
