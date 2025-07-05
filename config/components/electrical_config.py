"""
Electrical system configuration for the KPP simulator.
"""

from typing import Dict, Any
import logging
from dataclasses import dataclass, field
from ..core.base_config import BaseConfig

logger = logging.getLogger(__name__)

@dataclass
class ElectricalConfig(BaseConfig):
    """Configuration for electrical system parameters"""
    
    # Generator properties
    rated_power: float = field(default=530000.0, metadata={"description": "Rated power in W", "min": 0})
    rated_speed: float = field(default=375.0, metadata={"description": "Rated speed in RPM", "min": 0})
    efficiency_at_rated: float = field(default=0.94, metadata={"description": "Efficiency at rated load", "min": 0, "max": 1})
    
    # Power electronics properties
    rectifier_efficiency: float = field(default=0.97, metadata={"description": "Rectifier efficiency", "min": 0, "max": 1})
    inverter_efficiency: float = field(default=0.96, metadata={"description": "Inverter efficiency", "min": 0, "max": 1})
    transformer_efficiency: float = field(default=0.985, metadata={"description": "Transformer efficiency", "min": 0, "max": 1})
    
    # Grid interface properties
    nominal_voltage: float = field(default=480.0, metadata={"description": "Nominal voltage in V", "min": 0})
    nominal_frequency: float = field(default=60.0, metadata={"description": "Nominal frequency in Hz", "min": 0})
    voltage_regulation_band: float = field(default=0.05, metadata={"description": "Voltage regulation band", "min": 0, "max": 1})
    frequency_regulation_band: float = field(default=0.1, metadata={"description": "Frequency regulation band", "min": 0, "max": 1})
    
    # Load management properties
    load_management: bool = field(default=True, metadata={"description": "Enable load management"})
    target_load_factor: float = field(default=0.8, metadata={"description": "Target load factor", "min": 0, "max": 1})
    
    def validate_physics_constraints(self) -> bool:
        """Validate physics constraints"""
        try:
            # Validate efficiency values
            if not 0 <= self.efficiency_at_rated <= 1:
                logger.warning("Generator efficiency must be between 0 and 1")
                return False
            
            if not 0 <= self.rectifier_efficiency <= 1:
                logger.warning("Rectifier efficiency must be between 0 and 1")
                return False
                
            if not 0 <= self.inverter_efficiency <= 1:
                logger.warning("Inverter efficiency must be between 0 and 1")
                return False
                
            if not 0 <= self.transformer_efficiency <= 1:
                logger.warning("Transformer efficiency must be between 0 and 1")
                return False
                
            if not 0 <= self.target_load_factor <= 1:
                logger.warning("Target load factor must be between 0 and 1")
                return False
                
            return True
        except Exception as e:
            logger.error(f"Validation error: {e}")
            return False 