"""
Integrated Loss Model for KPP Simulator
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

class LossType(Enum):
    """Types of losses in the system"""
    MECHANICAL = "mechanical"
    ELECTRICAL = "electrical"
    THERMAL = "thermal"

@dataclass
class LossResult:
    """Result of loss calculation"""
    loss_type: LossType
    power_loss: float
    energy_loss: float
    efficiency: float
    temperature_rise: float
    wear_rate: float

@dataclass
class SystemLosses:
    """System-wide loss data"""
    total_losses: float = 0.0
    mechanical_losses: float = 0.0
    electrical_losses: float = 0.0
    thermal_losses: float = 0.0
    total_power_input: float = 0.0
    overall_efficiency: float = 1.0

class IntegratedLossModel:
    """
    Integrated loss model that calculates various types of losses
    in the KPP system.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize loss model"""
        self.config = config or {}
        
        # Physical constants
        self.bearing_friction_coefficient = self.config.get('bearing_friction_coefficient', 0.001)
        self.windage_coefficient = self.config.get('windage_coefficient', 0.1)
        self.electrical_resistance = self.config.get('electrical_resistance', 0.1)
        self.thermal_conductivity = self.config.get('thermal_conductivity', 50.0)
    
    def calculate_system_losses(self, drivetrain_state: Any, electrical_state: Any) -> SystemLosses:
        """
        Calculate total system losses.
        
        Args:
            drivetrain_state: Current drivetrain state
            electrical_state: Current electrical state
            
        Returns:
            SystemLosses object with all loss components
        """
        # Calculate component losses
        drivetrain_losses = self.calculate_drivetrain_losses(drivetrain_state)
        generator_losses = self.calculate_generator_losses(electrical_state)
        power_electronics_losses = self.calculate_power_electronics_losses(electrical_state)
        
        # Sum up losses by type
        mechanical_losses = sum(loss.power_loss for loss in drivetrain_losses.values())
        electrical_losses = sum(loss.power_loss for loss in generator_losses.values())
        electrical_losses += sum(loss.power_loss for loss in power_electronics_losses.values())
        
        # Calculate thermal losses (from both mechanical and electrical sources)
        thermal_losses = (
            mechanical_losses * 0.1 +  # 10% of mechanical losses become heat
            electrical_losses * 0.2    # 20% of electrical losses become heat
        )
        
        # Calculate total power input (assuming 90% efficiency as baseline)
        total_losses = mechanical_losses + electrical_losses + thermal_losses
        total_power_input = total_losses / 0.1  # Losses are ~10% of input power
        
        # Calculate overall efficiency
        overall_efficiency = 1.0 - (total_losses / total_power_input) if total_power_input > 0 else 1.0
        
        return SystemLosses(
            total_losses=total_losses,
            mechanical_losses=mechanical_losses,
            electrical_losses=electrical_losses,
            thermal_losses=thermal_losses,
            total_power_input=total_power_input,
            overall_efficiency=overall_efficiency
        )
    
    def calculate_drivetrain_losses(self, drivetrain_state: Any) -> Dict[str, LossResult]:
        """
        Calculate drivetrain losses.
        
        Args:
            drivetrain_state: Current drivetrain state
            
        Returns:
            Dictionary of loss results by type
        """
        # Calculate bearing friction losses
        angular_velocity = drivetrain_state.output_speed * 2 * 3.14159 / 60  # RPM to rad/s
        normal_force = drivetrain_state.chain_tension
        bearing_power_loss = (
            self.bearing_friction_coefficient *
            normal_force *
            angular_velocity *
            0.05  # Bearing radius (m)
        )
        
        # Calculate windage losses
        windage_power_loss = (
            self.windage_coefficient *
            angular_velocity ** 3 *
            0.2 ** 4 *  # Rotor radius (m)
            1.225  # Air density (kg/m³)
        )
        
        # Create loss results
        friction_loss = LossResult(
            loss_type=LossType.MECHANICAL,
            power_loss=bearing_power_loss,
            energy_loss=0.0,  # Calculated by tracking system
            efficiency=1.0 - (bearing_power_loss / max(drivetrain_state.input_power, 1e-6)),
            temperature_rise=bearing_power_loss * 0.1,  # Simple thermal model
            wear_rate=bearing_power_loss * 1e-6  # Simple wear model
        )
        
        windage_loss = LossResult(
            loss_type=LossType.MECHANICAL,
            power_loss=windage_power_loss,
            energy_loss=0.0,  # Calculated by tracking system
            efficiency=1.0 - (windage_power_loss / max(drivetrain_state.input_power, 1e-6)),
            temperature_rise=windage_power_loss * 0.05,  # Simple thermal model
            wear_rate=0.0  # No direct wear from windage
        )
        
        return {
            'friction': friction_loss,
            'windage': windage_loss
        }
    
    def calculate_generator_losses(self, electrical_state: Any) -> Dict[str, LossResult]:
        """
        Calculate generator losses.
        
        Args:
            electrical_state: Current electrical state
            
        Returns:
            Dictionary of loss results by type
        """
        # Calculate electrical losses (I²R losses)
        current = electrical_state.current
        electrical_power_loss = (
            self.electrical_resistance *
            current ** 2
        )
        
        # Calculate core losses (simplified model)
        voltage = electrical_state.voltage
        frequency = 50  # Assumed grid frequency
        core_power_loss = (
            0.1 * voltage +  # Hysteresis losses
            0.05 * voltage * frequency  # Eddy current losses
        )
        
        # Create loss results
        electrical_loss = LossResult(
            loss_type=LossType.ELECTRICAL,
            power_loss=electrical_power_loss,
            energy_loss=0.0,  # Calculated by tracking system
            efficiency=1.0 - (electrical_power_loss / max(electrical_state.input_power, 1e-6)),
            temperature_rise=electrical_power_loss * 0.2,  # Simple thermal model
            wear_rate=electrical_power_loss * 1e-7  # Simple wear model
        )
        
        core_loss = LossResult(
            loss_type=LossType.ELECTRICAL,
            power_loss=core_power_loss,
            energy_loss=0.0,  # Calculated by tracking system
            efficiency=1.0 - (core_power_loss / max(electrical_state.input_power, 1e-6)),
            temperature_rise=core_power_loss * 0.1,  # Simple thermal model
            wear_rate=core_power_loss * 1e-8  # Simple wear model
        )
        
        return {
            'electrical': electrical_loss,
            'core': core_loss
        }
    
    def calculate_power_electronics_losses(self, electrical_state: Any) -> Dict[str, LossResult]:
        """
        Calculate power electronics losses.
        
        Args:
            electrical_state: Current electrical state
            
        Returns:
            Dictionary of loss results by type
        """
        # Calculate switching losses
        voltage = electrical_state.voltage
        current = electrical_state.current
        switching_frequency = 10000  # Assumed switching frequency (Hz)
        switching_power_loss = (
            0.1 * voltage * current * switching_frequency * 1e-6  # Simple switching loss model
        )
        
        # Calculate conduction losses
        conduction_power_loss = (
            0.05 * current ** 2  # Simple conduction loss model
        )
        
        # Create loss results
        switching_loss = LossResult(
            loss_type=LossType.ELECTRICAL,
            power_loss=switching_power_loss,
            energy_loss=0.0,  # Calculated by tracking system
            efficiency=1.0 - (switching_power_loss / max(electrical_state.input_power, 1e-6)),
            temperature_rise=switching_power_loss * 0.3,  # Simple thermal model
            wear_rate=switching_power_loss * 1e-6  # Simple wear model
        )
        
        conduction_loss = LossResult(
            loss_type=LossType.ELECTRICAL,
            power_loss=conduction_power_loss,
            energy_loss=0.0,  # Calculated by tracking system
            efficiency=1.0 - (conduction_power_loss / max(electrical_state.input_power, 1e-6)),
            temperature_rise=conduction_power_loss * 0.2,  # Simple thermal model
            wear_rate=conduction_power_loss * 1e-7  # Simple wear model
        )
        
        return {
            'switching': switching_loss,
            'conduction': conduction_loss
        }

