"""
Floater-specific configuration for the KPP simulator.
"""

from typing import Dict, Any
import logging
from dataclasses import dataclass, field
from ..core.base_config import BaseConfig

logger = logging.getLogger(__name__)

@dataclass
class FloaterConfig(BaseConfig):
    """Configuration for floater parameters"""
    
    # Physical properties
    volume: float = field(default=0.4, metadata={"description": "Floater volume in m³", "min": 0, "max": 10})
    mass: float = field(default=16.0, metadata={"description": "Floater mass in kg", "min": 0, "max": 1000})
    drag_coefficient: float = field(default=0.6, metadata={"description": "Drag coefficient", "min": 0, "max": 2})
    
    # Pneumatic properties
    air_fill_time: float = field(default=0.5, metadata={"description": "Air fill time in seconds", "min": 0, "max": 10})
    air_pressure: float = field(default=300000.0, metadata={"description": "Air pressure in Pa", "min": 50000, "max": 1000000})
    air_flow_rate: float = field(default=0.6, metadata={"description": "Air flow rate in m³/s", "min": 0, "max": 10})
    jet_efficiency: float = field(default=0.85, metadata={"description": "Jet efficiency (0-1)", "min": 0, "max": 1})
    
    # Thermal properties
    heat_transfer_coefficient: float = field(default=150.0, metadata={"description": "Heat transfer coefficient in W/m²K", "min": 0, "max": 1000})
    specific_heat_air: float = field(default=1005.0, metadata={"description": "Specific heat of air in J/kg·K", "min": 0})
    specific_heat_water: float = field(default=4186.0, metadata={"description": "Specific heat of water in J/kg·K", "min": 0})
    
    # State machine properties
    fill_state: str = field(default="empty", metadata={"description": "Initial fill state"})
    air_fill_level: float = field(default=0.0, metadata={"description": "Initial air fill level (0-1)", "min": 0, "max": 1})
    
    # Validation properties
    max_velocity: float = field(default=60.0, metadata={"description": "Maximum safe velocity in m/s", "min": 0})
    max_position: float = field(default=25.0, metadata={"description": "Maximum safe position in m", "min": 0})
    
    # Tank properties
    tank_height: float = field(default=25.0, metadata={"description": "Tank height in meters", "min": 0})
    area: float = field(default=0.1, metadata={"description": "Floater cross-sectional area in m²", "min": 0})
    
    def validate_physics_constraints(self) -> bool:
        """Validate physics constraints"""
        try:
            # Validate density constraint
            if self.volume > 0:
                density = self.mass / self.volume
                if density > 1000:  # Water density
                    logger.warning(f"Floater density ({density:.1f} kg/m³) exceeds water density")
            
            # Validate air fill level
            if not 0.0 <= self.air_fill_level <= 1.0:
                logger.warning("Air fill level must be between 0.0 and 1.0")
                return False
            
            # Validate fill state
            valid_states = ['empty', 'filling', 'full', 'venting']
            if self.fill_state not in valid_states:
                logger.warning(f"Fill state must be one of: {valid_states}")
                return False
                
            return True
        except Exception as e:
            logger.error(f"Validation error: {e}")
            return False
    
    def get_buoyancy_force(self, water_density: float = 1000.0) -> float:
        """Calculate buoyancy force based on current configuration"""
        return water_density * 9.81 * self.volume
    
    def get_drag_force(self, velocity: float, water_density: float = 1000.0) -> float:
        """Calculate drag force based on current configuration"""
        # Simplified drag calculation (assumes spherical floater)
        area = (3 * self.volume / (4 * 3.14159)) ** (2/3) * 3.14159
        return 0.5 * water_density * velocity**2 * area * self.drag_coefficient
    
    def to_floater_state(self) -> Dict[str, Any]:
        """Convert configuration to floater state dictionary"""
        return {
            'volume': self.volume,
            'mass': self.mass,
            'drag_coefficient': self.drag_coefficient,
            'air_fill_level': self.air_fill_level,
            'fill_state': self.fill_state,
            'pneumatic_pressure': self.air_pressure,
            'air_temperature': 293.15,  # Default temperature
            'water_temperature': 293.15  # Default temperature
        }
    
    def get_thermal_properties(self) -> Dict[str, float]:
        """Get thermal properties for the floater"""
        return {
            'heat_transfer_coefficient': self.heat_transfer_coefficient,
            'specific_heat_air': self.specific_heat_air,
            'specific_heat_water': self.specific_heat_water
        }
    
    def get_pneumatic_properties(self) -> Dict[str, float]:
        """Get pneumatic properties for the floater"""
        return {
            'air_fill_time': self.air_fill_time,
            'air_pressure': self.air_pressure,
            'air_flow_rate': self.air_flow_rate,
            'jet_efficiency': self.jet_efficiency
        } 