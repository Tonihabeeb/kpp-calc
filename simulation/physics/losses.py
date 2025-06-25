"""
Enhanced Loss Modeling for KPP Drivetrain System
Comprehensive tracking of mechanical, electrical, and thermal losses throughout the system.
"""

import math
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass
import numpy as np

logger = logging.getLogger(__name__)

@dataclass
class LossComponents:
    """Individual loss components for tracking"""
    bearing_friction: float = 0.0
    gear_mesh_losses: float = 0.0
    seal_friction: float = 0.0
    windage_losses: float = 0.0
    clutch_losses: float = 0.0
    electrical_losses: float = 0.0
    thermal_losses: float = 0.0
    total_losses: float = 0.0

@dataclass
class ComponentState:
    """State information for loss calculations"""
    torque: float = 0.0
    speed: float = 0.0  # rad/s
    temperature: float = 20.0  # °C
    load_factor: float = 0.0
    efficiency: float = 1.0

class DrivetrainLosses:
    """
    Comprehensive drivetrain loss modeling including:
    - Bearing friction with temperature dependence
    - Gear mesh losses with load dependence  
    - Seal friction with speed dependence
    - Windage losses with speed squared dependence
    - Clutch engagement losses
    """
    
    def __init__(self, 
                 bearing_friction_coeff: float = 0.002,
                 gear_mesh_efficiency: float = 0.98,
                 seal_friction_coeff: float = 0.001,
                 windage_coefficient: float = 1e-6,
                 clutch_friction_coeff: float = 0.05):
        """
        Initialize drivetrain loss model.
        
        Args:
            bearing_friction_coeff: Base bearing friction coefficient
            gear_mesh_efficiency: Base gear mesh efficiency (per stage)
            seal_friction_coeff: Seal friction coefficient
            windage_coefficient: Windage loss coefficient
            clutch_friction_coeff: Clutch friction coefficient
        """
        self.bearing_friction_coeff = bearing_friction_coeff
        self.gear_mesh_efficiency = gear_mesh_efficiency
        self.seal_friction_coeff = seal_friction_coeff
        self.windage_coefficient = windage_coefficient
        self.clutch_friction_coeff = clutch_friction_coeff
        
        # Temperature dependence coefficients
        self.temp_viscosity_coeff = 0.02  # Viscosity change per °C
        self.temp_friction_coeff = 0.001  # Friction change per °C
        
        # Loss tracking
        self.loss_history = []
        self.total_energy_loss = 0.0
        
        logger.info(f"DrivetrainLosses initialized with comprehensive loss modeling")
    
    def calculate_bearing_friction_losses(self, state: ComponentState) -> float:
        """
        Calculate bearing friction losses with temperature dependence.
        
        Friction increases with temperature due to thermal expansion and 
        lubricant viscosity changes.
        """
        # Base friction torque
        base_friction = self.bearing_friction_coeff * abs(state.torque)
        
        # Temperature factor (friction increases with temperature)
        temp_factor = 1.0 + self.temp_friction_coeff * (state.temperature - 20.0)
        
        # Speed factor (slight increase with speed)
        speed_factor = 1.0 + 0.1 * (abs(state.speed) / 100.0)  # 10% increase at 100 rad/s
        
        friction_torque = base_friction * temp_factor * speed_factor
        power_loss = friction_torque * abs(state.speed)
        
        return power_loss
    
    def calculate_gear_mesh_losses(self, state: ComponentState, gear_ratio: float = 1.0) -> float:
        """
        Calculate gear mesh losses with load and temperature dependence.
        
        Gear efficiency decreases under high loads and extreme temperatures.
        """
        if abs(state.torque) < 1e-6:
            return 0.0
        
        # Base efficiency loss
        base_efficiency_loss = 1.0 - self.gear_mesh_efficiency
        
        # Load factor effect (efficiency decreases under high loads)
        load_factor_effect = 1.0 + 0.5 * state.load_factor  # Up to 50% increase at full load
        
        # Temperature effect (efficiency decreases at extreme temperatures)
        optimal_temp = 60.0  # °C
        temp_deviation = abs(state.temperature - optimal_temp)
        temp_factor = 1.0 + 0.002 * temp_deviation  # 0.2% per degree deviation
        
        # Speed factor (slight efficiency decrease at very high speeds)
        speed_factor = 1.0 + 0.0001 * (abs(state.speed) / 100.0)**2
        
        efficiency_loss = base_efficiency_loss * load_factor_effect * temp_factor * speed_factor
        
        input_power = abs(state.torque * state.speed)
        power_loss = input_power * efficiency_loss
        
        return power_loss
    
    def calculate_seal_friction_losses(self, state: ComponentState) -> float:
        """
        Calculate seal friction losses with speed and temperature dependence.
        
        Seal friction increases with speed and varies with temperature.
        """
        # Speed-dependent friction (quadratic with speed)
        speed_friction = self.seal_friction_coeff * (state.speed**2)
        
        # Temperature factor (seal friction varies with temperature)
        # Minimum friction around 40°C, increases at extremes
        optimal_temp = 40.0
        temp_deviation = abs(state.temperature - optimal_temp)
        temp_factor = 1.0 + 0.003 * temp_deviation
        
        power_loss = speed_friction * temp_factor
        
        return max(0.0, power_loss)
    
    def calculate_windage_losses(self, state: ComponentState, component_diameter: float = 0.5) -> float:
        """
        Calculate windage losses from rotating components.
        
        Windage losses are proportional to speed cubed and component size.
        """
        # Windage power ~ ρ * ω³ * D⁵ where ρ=air density, ω=speed, D=diameter
        air_density = 1.225  # kg/m³ at 20°C
        
        # Temperature correction for air density
        temp_kelvin = state.temperature + 273.15
        air_density_corrected = air_density * (293.15 / temp_kelvin)
        
        windage_power = (self.windage_coefficient * 
                        air_density_corrected * 
                        (abs(state.speed)**3) * 
                        (component_diameter**5))
        
        return windage_power
    
    def calculate_clutch_losses(self, state: ComponentState, is_engaged: bool, 
                              slip_speed: float = 0.0) -> float:
        """
        Calculate clutch engagement and slip losses.
        
        Losses occur during engagement and when there's speed differential.
        """
        if not is_engaged:
            return 0.0
        
        # Slip losses (friction during speed differential)
        slip_torque = self.clutch_friction_coeff * abs(state.torque)
        slip_power = slip_torque * abs(slip_speed)
        
        # Engagement losses (additional friction when engaging)
        engagement_power = 0.1 * slip_power if abs(slip_speed) > 0.1 else 0.0
        
        total_power = slip_power + engagement_power
        
        return total_power
    
    def calculate_total_losses(self, component_states: Dict[str, ComponentState], 
                             system_config: Optional[Dict] = None) -> LossComponents:
        """
        Calculate total system losses from all components.
        
        Args:
            component_states: Dictionary of component states
            system_config: System configuration parameters
            
        Returns:
            LossComponents object with detailed loss breakdown
        """
        if system_config is None:
            system_config = {}
        
        losses = LossComponents()
        
        # Calculate losses for each component
        for component_name, state in component_states.items():
            
            # Bearing friction losses
            bearing_loss = self.calculate_bearing_friction_losses(state)
            losses.bearing_friction += bearing_loss
            
            # Gear mesh losses
            gear_ratio = system_config.get(f'{component_name}_gear_ratio', 1.0)
            gear_loss = self.calculate_gear_mesh_losses(state, gear_ratio)
            losses.gear_mesh_losses += gear_loss
            
            # Seal friction losses
            seal_loss = self.calculate_seal_friction_losses(state)
            losses.seal_friction += seal_loss
            
            # Windage losses
            diameter = system_config.get(f'{component_name}_diameter', 0.5)
            windage_loss = self.calculate_windage_losses(state, diameter)
            losses.windage_losses += windage_loss
            
            # Clutch losses (if applicable)
            if 'clutch' in component_name.lower():
                is_engaged = system_config.get(f'{component_name}_engaged', False)
                slip_speed = system_config.get(f'{component_name}_slip_speed', 0.0)
                clutch_loss = self.calculate_clutch_losses(state, is_engaged, slip_speed)
                losses.clutch_losses += clutch_loss
        
        # Calculate total losses
        losses.total_losses = (losses.bearing_friction + losses.gear_mesh_losses + 
                             losses.seal_friction + losses.windage_losses + 
                             losses.clutch_losses + losses.electrical_losses + 
                             losses.thermal_losses)
        
        # Update tracking
        self.total_energy_loss += losses.total_losses
        self.loss_history.append({
            'timestamp': len(self.loss_history),
            'losses': losses
        })
        
        # Keep history limited
        if len(self.loss_history) > 1000:
            self.loss_history = self.loss_history[-1000:]
        
        return losses
    
    def get_efficiency_from_losses(self, input_power: float, losses: LossComponents) -> float:
        """Calculate overall efficiency from loss breakdown"""
        if input_power <= 0:
            return 0.0
        
        output_power = max(0.0, input_power - losses.total_losses)
        efficiency = output_power / input_power
        
        return min(1.0, max(0.0, efficiency))
    
    def get_loss_breakdown_percentage(self, losses: LossComponents) -> Dict[str, float]:
        """Get loss breakdown as percentages"""
        if losses.total_losses <= 0:
            return {loss_type: 0.0 for loss_type in 
                   ['bearing_friction', 'gear_mesh_losses', 'seal_friction', 
                    'windage_losses', 'clutch_losses', 'electrical_losses', 'thermal_losses']}
        
        breakdown = {
            'bearing_friction': (losses.bearing_friction / losses.total_losses) * 100,
            'gear_mesh_losses': (losses.gear_mesh_losses / losses.total_losses) * 100,
            'seal_friction': (losses.seal_friction / losses.total_losses) * 100,
            'windage_losses': (losses.windage_losses / losses.total_losses) * 100,
            'clutch_losses': (losses.clutch_losses / losses.total_losses) * 100,
            'electrical_losses': (losses.electrical_losses / losses.total_losses) * 100,
            'thermal_losses': (losses.thermal_losses / losses.total_losses) * 100
        }
        
        return breakdown
    
    def reset(self):
        """Reset loss tracking"""
        self.loss_history.clear()
        self.total_energy_loss = 0.0
        logger.info("DrivetrainLosses state reset")


class ElectricalLosses:
    """
    Electrical system loss modeling including:
    - Copper losses (I²R)
    - Iron losses (hysteresis and eddy current)  
    - Switching losses in power electronics
    - Transformer losses
    """
    
    def __init__(self):
        """Initialize electrical loss model"""
        # Resistance coefficients
        self.copper_resistance_coeff = 0.02  # Ohms per kW rating
        self.temp_resistance_coeff = 0.004   # Per °C temperature coefficient
        
        # Iron loss coefficients
        self.hysteresis_coeff = 0.001        # Hysteresis loss coefficient
        self.eddy_current_coeff = 0.0005     # Eddy current loss coefficient
        
        # Power electronics coefficients
        self.switching_loss_coeff = 0.005    # Per switching operation
        self.conduction_loss_coeff = 0.02    # Conduction loss factor
        
        logger.info("ElectricalLosses initialized")
    
    def calculate_copper_losses(self, current: float, temperature: float = 20.0) -> float:
        """Calculate I²R copper losses with temperature correction"""
        # Base resistance
        base_resistance = self.copper_resistance_coeff
        
        # Temperature correction (resistance increases with temperature)
        temp_factor = 1.0 + self.temp_resistance_coeff * (temperature - 20.0)
        resistance = base_resistance * temp_factor
        
        copper_loss = (current**2) * resistance
        
        return copper_loss
    
    def calculate_iron_losses(self, frequency: float, flux_density: float, 
                            temperature: float = 20.0) -> float:
        """Calculate iron losses (hysteresis + eddy current)"""
        # Hysteresis losses (proportional to frequency and flux density squared)
        hysteresis_loss = self.hysteresis_coeff * frequency * (flux_density**2)
        
        # Eddy current losses (proportional to frequency squared and flux density squared)
        eddy_loss = self.eddy_current_coeff * (frequency**2) * (flux_density**2)
        
        # Temperature factor (iron losses decrease slightly with temperature)
        temp_factor = 1.0 - 0.001 * (temperature - 20.0)
        
        total_iron_loss = (hysteresis_loss + eddy_loss) * temp_factor
        
        return max(0.0, total_iron_loss)
    
    def calculate_switching_losses(self, switching_frequency: float, voltage: float, 
                                 current: float) -> float:
        """Calculate power electronics switching losses"""
        # Switching loss per operation
        loss_per_switch = self.switching_loss_coeff * voltage * current
        
        # Total switching losses
        switching_loss = loss_per_switch * switching_frequency
        
        return switching_loss
    
    def calculate_total_electrical_losses(self, electrical_state: Dict) -> float:
        """Calculate total electrical system losses"""
        current = electrical_state.get('current', 0.0)
        voltage = electrical_state.get('voltage', 0.0)
        frequency = electrical_state.get('frequency', 60.0)
        temperature = electrical_state.get('temperature', 20.0)
        switching_freq = electrical_state.get('switching_frequency', 5000.0)
        flux_density = electrical_state.get('flux_density', 1.0)
        
        # Calculate individual loss components
        copper_loss = self.calculate_copper_losses(current, temperature)
        iron_loss = self.calculate_iron_losses(frequency, flux_density, temperature)
        switching_loss = self.calculate_switching_losses(switching_freq, voltage, current)
        
        total_loss = copper_loss + iron_loss + switching_loss
        
        return total_loss


def create_standard_kpp_loss_model() -> DrivetrainLosses:
    """Create standard KPP drivetrain loss model with realistic parameters"""
    return DrivetrainLosses(
        bearing_friction_coeff=0.0015,   # Optimized for KPP bearings
        gear_mesh_efficiency=0.985,      # High-quality gears
        seal_friction_coeff=0.0008,      # Low-friction seals
        windage_coefficient=8e-7,        # Reduced windage design
        clutch_friction_coeff=0.03       # Optimized clutch materials
    )
