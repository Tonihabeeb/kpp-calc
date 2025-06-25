"""
Advanced Generator Model for Phase 3 Implementation
Enhanced electromagnetic modeling with realistic generator characteristics.
"""

import math
import logging
from typing import Dict, Tuple, Optional, Any
import numpy as np

logger = logging.getLogger(__name__)


class AdvancedGenerator:
    """
    Advanced generator model with realistic electromagnetic characteristics.
    
    Models:
    - Electromagnetic torque curves
    - Efficiency maps based on speed and load
    - Magnetic saturation effects
    - Iron losses (hysteresis and eddy current)
    - Copper losses (I²R)
    - Mechanical losses (bearing friction, windage)
    - Grid synchronization requirements
    - Reactive power and power factor
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize advanced generator with comprehensive electromagnetic modeling.
        
        Args:
            config (dict): Generator configuration parameters
        """
        if config is None:
            config = {}
            
        # Basic electrical parameters
        self.rated_power = config.get('rated_power', 530000.0)  # W
        self.rated_voltage = config.get('rated_voltage', 480.0)  # V (line-to-line)
        self.rated_frequency = config.get('rated_frequency', 60.0)  # Hz
        self.rated_speed = config.get('rated_speed', 375.0)  # RPM
        self.pole_pairs = config.get('pole_pairs', 4)  # Number of pole pairs
        
        # Electromagnetic parameters
        self.stator_resistance = config.get('stator_resistance', 0.02)  # Ohms per phase
        self.stator_reactance = config.get('stator_reactance', 0.15)  # Ohms per phase
        self.magnetizing_reactance = config.get('magnetizing_reactance', 3.0)  # Ohms
        self.rotor_resistance = config.get('rotor_resistance', 0.025)  # Ohms referred to stator
        self.rotor_reactance = config.get('rotor_reactance', 0.18)  # Ohms referred to stator
        
        # Mechanical parameters
        self.rotor_inertia = config.get('rotor_inertia', 12.0)  # kg⋅m²
        self.bearing_friction_coeff = config.get('bearing_friction', 0.001)  # N⋅m⋅s/rad
        self.windage_loss_coeff = config.get('windage_loss', 0.5)  # W⋅s²/rad²
        
        # Efficiency curve parameters
        self.iron_loss_constant = config.get('iron_loss_constant', 2500.0)  # W
        self.copper_loss_factor = config.get('copper_loss_factor', 1.2)  # Multiplier for I²R losses
        
        # Control parameters
        self.max_slip = config.get('max_slip', 0.05)  # Maximum slip for stable operation
        self.min_excitation = config.get('min_excitation', 0.1)  # Minimum field excitation
        self.power_factor_target = config.get('power_factor', 0.92)  # Target power factor
        
        # State variables
        self.angular_velocity = 0.0  # rad/s
        self.slip = 0.0  # Per unit slip
        self.torque = 0.0  # N⋅m
        self.electrical_power = 0.0  # W
        self.mechanical_power = 0.0  # W
        self.efficiency = 0.0  # Overall efficiency
        self.power_factor = 0.0  # Current power factor
        self.field_excitation = 1.0  # Per unit field excitation
        
        # Loss breakdown
        self.iron_losses = 0.0  # W
        self.copper_losses = 0.0  # W
        self.mechanical_losses = 0.0  # W
        self.total_losses = 0.0  # W
        
        # Calculated constants
        self.rated_omega = self.rated_speed * (2 * math.pi / 60)  # rad/s
        self.synchronous_speed = 120 * self.rated_frequency / (2 * self.pole_pairs)  # RPM
        self.synchronous_omega = self.synchronous_speed * (2 * math.pi / 60)  # rad/s
        self.rated_torque = self.rated_power / self.rated_omega  # N⋅m
        
        logger.info(f"Advanced generator initialized: {self.rated_power/1000:.0f}kW, "
                   f"{self.rated_speed}RPM, {self.pole_pairs} pole pairs")
    
    def update(self, shaft_speed: float, load_factor: float, dt: float) -> Dict[str, float]:
        """
        Update generator state with advanced electromagnetic modeling.
        
        Args:
            shaft_speed (float): Mechanical shaft speed (rad/s)
            load_factor (float): Electrical load factor (0-1)
            dt (float): Time step (s)
            
        Returns:
            dict: Generator state and performance metrics
        """
        self.angular_velocity = shaft_speed
        
        # Calculate slip
        self.slip = (self.synchronous_omega - shaft_speed) / self.synchronous_omega
        self.slip = max(min(self.slip, self.max_slip), -self.max_slip)  # Limit slip
        
        # Calculate electromagnetic torque
        self.torque = self._calculate_electromagnetic_torque(self.slip, load_factor)
        
        # Calculate mechanical power input
        self.mechanical_power = self.torque * shaft_speed
        
        # Calculate losses
        self._calculate_losses(shaft_speed, load_factor)
        
        # Calculate electrical power output
        self.electrical_power = max(0.0, self.mechanical_power - self.total_losses)
        
        # Calculate overall efficiency
        if self.mechanical_power > 0:
            self.efficiency = self.electrical_power / self.mechanical_power
        else:
            self.efficiency = 0.0
            
        # Calculate power factor
        self.power_factor = self._calculate_power_factor(load_factor)
        
        return self._get_state_dict()
    
    def _calculate_electromagnetic_torque(self, slip: float, load_factor: float) -> float:
        """
        Calculate electromagnetic torque using equivalent circuit model.
        
        Args:
            slip (float): Generator slip (per unit)
            load_factor (float): Load factor (0-1)
            
        Returns:
            float: Electromagnetic torque (N⋅m)
        """
        if abs(slip) < 1e-6:
            slip = 1e-6  # Avoid division by zero
            
        # Equivalent circuit calculations
        rotor_resistance_effective = self.rotor_resistance / slip
        
        # Total impedance
        z_real = self.stator_resistance + rotor_resistance_effective
        z_imag = self.stator_reactance + self.rotor_reactance
        z_magnitude = math.sqrt(z_real**2 + z_imag**2)
        
        # Current calculation (simplified)
        voltage_per_phase = self.rated_voltage / math.sqrt(3)
        current = (voltage_per_phase * load_factor * self.field_excitation) / z_magnitude
        
        # Torque calculation
        torque_constant = (3 * self.pole_pairs) / self.synchronous_omega
        torque = torque_constant * (current**2 * self.rotor_resistance / slip)
        
        # Apply saturation effects
        saturation_factor = self._calculate_saturation_factor(current)
        torque *= saturation_factor
        
        return min(torque, self.rated_torque * 1.5)  # Limit maximum torque
    
    def _calculate_saturation_factor(self, current: float) -> float:
        """
        Calculate magnetic saturation effects.
        
        Args:
            current (float): Stator current (A)
            
        Returns:
            float: Saturation factor (0-1)
        """
        rated_current = self.rated_power / (math.sqrt(3) * self.rated_voltage * self.power_factor_target)
        current_ratio = current / rated_current
        
        # Simplified saturation curve
        if current_ratio < 0.8:
            return 1.0
        elif current_ratio < 1.2:
            return 1.0 - 0.2 * (current_ratio - 0.8) / 0.4
        else:
            return 0.8 - 0.3 * (current_ratio - 1.2)
    
    def _calculate_losses(self, speed: float, load_factor: float):
        """
        Calculate detailed loss breakdown.
        
        Args:
            speed (float): Shaft speed (rad/s)
            load_factor (float): Load factor (0-1)
        """
        # Iron losses (proportional to speed²)
        speed_ratio = speed / self.rated_omega
        self.iron_losses = self.iron_loss_constant * (speed_ratio**2)
        
        # Copper losses (proportional to current²)
        current_ratio = load_factor * self.field_excitation
        self.copper_losses = (self.rated_power * 0.02) * (current_ratio**2) * self.copper_loss_factor
        
        # Mechanical losses
        friction_loss = self.bearing_friction_coeff * speed
        windage_loss = self.windage_loss_coeff * (speed**2)
        self.mechanical_losses = friction_loss + windage_loss
        
        # Total losses
        self.total_losses = self.iron_losses + self.copper_losses + self.mechanical_losses
    
    def _calculate_power_factor(self, load_factor: float) -> float:
        """
        Calculate power factor based on loading conditions.
        
        Args:
            load_factor (float): Load factor (0-1)
            
        Returns:
            float: Power factor
        """
        # Power factor typically decreases at light loads
        if load_factor < 0.3:
            return self.power_factor_target * (0.6 + 0.4 * load_factor / 0.3)
        else:
            return self.power_factor_target
    
    def get_load_torque(self, speed: float, target_power: Optional[float] = None) -> float:
        """
        Calculate required load torque for given speed and power.
        
        Args:
            speed (float): Shaft speed (rad/s)
            target_power (float): Desired power output (W)
            
        Returns:
            float: Required load torque (N⋅m)
        """
        # Ensure we have a valid target power
        if target_power is None:
            power_to_use = self.rated_power
        else:
            power_to_use = target_power
            
        # Ensure target_power is valid
        if not isinstance(power_to_use, (int, float)) or power_to_use <= 0:
            power_to_use = self.rated_power
            
        if speed < 0.1:
            return 0.0
            
        # Account for efficiency
        estimated_efficiency = self._estimate_efficiency(speed, power_to_use / self.rated_power)
        
        # Ensure we have valid efficiency
        if estimated_efficiency is None or estimated_efficiency <= 0:
            estimated_efficiency = 0.85  # Default efficiency
        
        mechanical_power_needed = power_to_use / estimated_efficiency
        
        return mechanical_power_needed / speed
    
    def _estimate_efficiency(self, speed: float, load_factor: float) -> float:
        """
        Estimate efficiency for given operating conditions.
        
        Args:
            speed (float): Shaft speed (rad/s)
            load_factor (float): Load factor (0-1)
            
        Returns:
            float: Estimated efficiency
        """
        # Simplified efficiency estimation
        speed_ratio = speed / self.rated_omega
        
        # Base efficiency curve
        if load_factor < 0.2:
            base_eff = 0.75
        elif load_factor < 0.5:
            base_eff = 0.85 + 0.08 * (load_factor - 0.2) / 0.3
        elif load_factor < 1.0:
            base_eff = 0.93 - 0.01 * (load_factor - 0.5) / 0.5
        else:
            base_eff = 0.92 - 0.05 * (load_factor - 1.0)
            
        # Speed correction
        if speed_ratio < 0.8:
            speed_factor = 0.95
        elif speed_ratio < 1.2:
            speed_factor = 1.0
        else:
            speed_factor = 0.98
            
        return max(0.5, base_eff * speed_factor)
    
    def _get_state_dict(self) -> Dict[str, float]:
        """
        Get comprehensive generator state.
        
        Returns:
            dict: Complete generator state information
        """
        return {
            # Primary outputs
            'electrical_power': self.electrical_power,
            'mechanical_power': self.mechanical_power,
            'torque': self.torque,
            'efficiency': self.efficiency,
            'power_factor': self.power_factor,
            
            # Operating conditions
            'speed_rpm': self.angular_velocity * 60 / (2 * math.pi),
            'slip': self.slip,
            'field_excitation': self.field_excitation,
            
            # Loss breakdown
            'iron_losses': self.iron_losses,
            'copper_losses': self.copper_losses,
            'mechanical_losses': self.mechanical_losses,
            'total_losses': self.total_losses,
            
            # Electrical parameters
            'voltage': self.rated_voltage,
            'frequency': self.rated_frequency,
            'synchronous_speed_rpm': self.synchronous_speed
        }
    
    def set_field_excitation(self, excitation: float):
        """
        Set generator field excitation.
        
        Args:
            excitation (float): Field excitation (per unit, 0-1.2)
        """
        self.field_excitation = max(self.min_excitation, min(1.2, excitation))
        logger.debug(f"Generator field excitation set to {self.field_excitation:.3f} pu")
    
    def reset(self):
        """
        Reset generator to initial state.
        """
        self.angular_velocity = 0.0
        self.slip = 0.0
        self.torque = 0.0
        self.electrical_power = 0.0
        self.mechanical_power = 0.0
        self.efficiency = 0.0
        self.power_factor = 0.0
        self.field_excitation = 1.0
        
        self.iron_losses = 0.0
        self.copper_losses = 0.0
        self.mechanical_losses = 0.0
        self.total_losses = 0.0
        
        logger.info("Advanced generator state reset")


def create_kmp_generator(config: Optional[Dict[str, Any]] = None) -> AdvancedGenerator:
    """
    Create a standard KMP generator with realistic parameters.
    
    Args:
        config (dict): Optional configuration overrides
        
    Returns:
        AdvancedGenerator: Configured generator instance
    """
    default_config = {
        'rated_power': 530000.0,  # 530 kW
        'rated_voltage': 480.0,   # 480V line-to-line
        'rated_frequency': 60.0,  # 60 Hz
        'rated_speed': 375.0,     # 375 RPM (matches flywheel target)
        'pole_pairs': 4,          # 8-pole machine
        'efficiency_at_rated': 0.94,  # 94% efficiency at rated conditions
        'power_factor': 0.92      # 92% power factor
    }
    
    if config:
        default_config.update(config)
    
    generator = AdvancedGenerator(default_config)
    logger.info(f"Created KMP generator: {default_config['rated_power']/1000:.0f}kW, "
               f"{default_config['rated_speed']}RPM")
    
    return generator
