"""
Integrated Electrical System for KPP Simulator
Manages electrical power generation, conversion, and grid integration
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
import logging

@dataclass
class ElectricalConfig:
    """Electrical system configuration"""
    rated_power: float = 1000.0  # kW
    rated_voltage: float = 400.0  # V
    rated_frequency: float = 50.0  # Hz
    power_factor: float = 0.95
    efficiency: float = 0.95
    response_time: float = 0.01  # seconds

@dataclass
class ElectricalState:
    """Electrical system state"""
    active_power: float = 0.0  # kW
    reactive_power: float = 0.0  # kVAr
    voltage: float = 400.0  # V
    frequency: float = 50.0  # Hz
    power_factor: float = 1.0
    efficiency: float = 1.0
    temperature: float = 25.0  # °C
    status: str = "idle"

class IntegratedElectricalSystem:
    """
    Integrated Electrical System for KPP Simulator
    
    Features:
    - Power generation and conversion
    - Grid synchronization
    - Power quality management
    - Protection and safety
    - Performance monitoring
    """
    
    def __init__(self, config: Optional[ElectricalConfig] = None):
        """Initialize electrical system"""
        self.config = config or ElectricalConfig()
        self.state = ElectricalState()
        self.logger = logging.getLogger(__name__)
        
        # Performance tracking
        self.performance_metrics = {
            'total_energy_generated': 0.0,  # kWh
            'total_energy_exported': 0.0,  # kWh
            'average_power_factor': 1.0,
            'average_efficiency': 1.0,
            'total_operating_time': 0.0  # hours
        }
        
        # Protection settings
        self.protection_limits = {
            'max_power': self.config.rated_power * 1.1,
            'max_voltage': self.config.rated_voltage * 1.1,
            'min_voltage': self.config.rated_voltage * 0.9,
            'max_frequency': self.config.rated_frequency * 1.02,
            'min_frequency': self.config.rated_frequency * 0.98,
            'max_temperature': 80.0  # °C
        }
        
        self.logger.info("Integrated Electrical System initialized")
    
    def update(self, mechanical_power: float, grid_state: Dict[str, Any], time_step: float) -> bool:
        """
        Update electrical system state
        
        Args:
            mechanical_power: Input mechanical power in kW
            grid_state: Current grid state
            time_step: Time step in seconds
            
        Returns:
            True if update successful
        """
        try:
            # Convert mechanical to electrical power
            electrical_power = self._convert_power(mechanical_power)
            
            # Update system state
            self._update_state(electrical_power, grid_state)
            
            # Check protection limits
            if not self._check_protection_limits():
                return False
            
            # Update metrics
            self._update_metrics(time_step)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Electrical system update failed: {e}")
            return False
    
    def _convert_power(self, mechanical_power: float) -> float:
        """Convert mechanical power to electrical power"""
        # Apply efficiency losses
        electrical_power = mechanical_power * self.config.efficiency
        
        # Apply power factor correction
        apparent_power = electrical_power / self.config.power_factor
        self.state.reactive_power = np.sqrt(apparent_power**2 - electrical_power**2)
        
        return electrical_power
    
    def _update_state(self, electrical_power: float, grid_state: Dict[str, Any]):
        """Update system state"""
        # Update power
        self.state.active_power = electrical_power
        
        # Synchronize with grid
        self.state.voltage = grid_state.get('voltage', self.config.rated_voltage)
        self.state.frequency = grid_state.get('frequency', self.config.rated_frequency)
        
        # Calculate power factor
        if self.state.active_power > 0:
            self.state.power_factor = (self.state.active_power / 
                np.sqrt(self.state.active_power**2 + self.state.reactive_power**2))
        
        # Update efficiency
        self.state.efficiency = self.config.efficiency
        
        # Update status
        if electrical_power > 0:
            self.state.status = "generating"
        else:
            self.state.status = "idle"
    
    def _check_protection_limits(self) -> bool:
        """Check protection limits"""
        if abs(self.state.active_power) > self.protection_limits['max_power']:
            self.logger.warning("Power limit exceeded")
            return False
            
        if self.state.voltage > self.protection_limits['max_voltage']:
            self.logger.warning("Overvoltage condition")
            return False
            
        if self.state.voltage < self.protection_limits['min_voltage']:
            self.logger.warning("Undervoltage condition")
            return False
            
        if self.state.frequency > self.protection_limits['max_frequency']:
            self.logger.warning("Overfrequency condition")
            return False
            
        if self.state.frequency < self.protection_limits['min_frequency']:
            self.logger.warning("Underfrequency condition")
            return False
            
        if self.state.temperature > self.protection_limits['max_temperature']:
            self.logger.warning("Overtemperature condition")
            return False
            
        return True
    
    def _update_metrics(self, time_step: float):
        """Update performance metrics"""
        # Update energy metrics
        energy_generated = self.state.active_power * time_step / 3600.0  # kWh
        self.performance_metrics['total_energy_generated'] += energy_generated
        
        if self.state.active_power > 0:
            self.performance_metrics['total_energy_exported'] += energy_generated
        
        # Update averages
        self.performance_metrics['average_power_factor'] = (
            0.95 * self.performance_metrics['average_power_factor'] +
            0.05 * self.state.power_factor
        )
        
        self.performance_metrics['average_efficiency'] = (
            0.95 * self.performance_metrics['average_efficiency'] +
            0.05 * self.state.efficiency
        )
        
        # Update operating time
        self.performance_metrics['total_operating_time'] += time_step / 3600.0
    
    def get_state(self) -> Dict[str, Any]:
        """Get current electrical system state"""
        return {
            'active_power': self.state.active_power,
            'reactive_power': self.state.reactive_power,
            'voltage': self.state.voltage,
            'frequency': self.state.frequency,
            'power_factor': self.state.power_factor,
            'efficiency': self.state.efficiency,
            'temperature': self.state.temperature,
            'status': self.state.status
        }
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get performance metrics"""
        return self.performance_metrics.copy()
    
    def reset(self):
        """Reset electrical system state"""
        self.state = ElectricalState()
        self.performance_metrics = {
            'total_energy_generated': 0.0,
            'total_energy_exported': 0.0,
            'average_power_factor': 1.0,
            'average_efficiency': 1.0,
            'total_operating_time': 0.0
        }
        self.logger.info("Electrical system reset") 