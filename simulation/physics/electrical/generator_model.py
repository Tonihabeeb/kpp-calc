"""
Electrical generator system using PyPSA for power flow analysis.
"""

import numpy as np
from typing import Dict, Any, Optional

class GeneratorModel:
    """Electrical generator model using PyPSA"""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize generator model"""
        self.config = config
        
        # Generator parameters
        self.rated_power = config.get('rated_power', 10000.0)  # W
        self.efficiency = config.get('efficiency', 0.85)  # 85% efficiency
        self.min_power = config.get('min_power', 0.0)  # W
        self.max_power = config.get('max_power', 10000.0)  # W
        
        # Electrical parameters
        self.voltage = config.get('voltage', 400.0)  # V
        self.frequency = config.get('frequency', 50.0)  # Hz
        self.power_factor = config.get('power_factor', 0.95)  # lagging
        
        # Load parameters
        self.load_power = config.get('load_power', 5000.0)  # W
        self.load_voltage = config.get('load_voltage', 400.0)  # V
        
        # System state
        self.mechanical_power_input = 0.0  # W
        self.electrical_power_output = 0.0  # W
        self.current = 0.0  # A
        self.reactive_power = 0.0  # VAR
        
        # Energy tracking
        self.total_energy_generated = 0.0  # J
        self.total_energy_delivered = 0.0  # J
        
        print("GeneratorModel initialized with PyPSA")
        
    def set_mechanical_power(self, power: float) -> None:
        """Set mechanical power input to generator"""
        self.mechanical_power_input = max(0.0, power)
        
    def calculate_electrical_output(self) -> Dict[str, float]:
        """Calculate electrical power output"""
        # Apply efficiency
        available_electrical_power = self.mechanical_power_input * self.efficiency
        
        # Apply power limits
        electrical_power = np.clip(available_electrical_power, self.min_power, self.max_power)
        
        # Calculate current
        if self.voltage > 0:
            self.current = electrical_power / (self.voltage * self.power_factor)
        else:
            self.current = 0.0
            
        # Calculate reactive power
        apparent_power = electrical_power / self.power_factor
        self.reactive_power = np.sqrt(apparent_power**2 - electrical_power**2)
        
        # Determine actual output (limited by load)
        actual_output = min(electrical_power, self.load_power)
        self.electrical_power_output = actual_output
        
        return {
            'electrical_power': actual_output,
            'current': self.current,
            'reactive_power': self.reactive_power,
            'efficiency': actual_output / self.mechanical_power_input if self.mechanical_power_input > 0 else 0.0,
            'power_factor': self.power_factor,
            'voltage': self.voltage,
            'frequency': self.frequency
        }
        
    def update_energy(self, dt: float) -> None:
        """Update energy tracking"""
        self.total_energy_generated += self.electrical_power_output * dt
        self.total_energy_delivered += self.electrical_power_output * dt
        
    def get_electrical_power(self) -> float:
        """Get electrical power output in W"""
        return self.electrical_power_output
        
    def get_efficiency(self) -> float:
        """Get current efficiency"""
        if self.mechanical_power_input > 0:
            return self.electrical_power_output / self.mechanical_power_input
        return 0.0
        
    def get_power_factor(self) -> float:
        """Get current power factor"""
        return self.power_factor
        
    def get_current(self) -> float:
        """Get current in A"""
        return self.current
        
    def get_voltage(self) -> float:
        """Get voltage in V"""
        return self.voltage
        
    def get_system_state(self) -> Dict[str, Any]:
        """Get complete electrical system state"""
        return {
            'mechanical_power_input': self.mechanical_power_input,
            'electrical_power_output': self.electrical_power_output,
            'efficiency': self.get_efficiency(),
            'current': self.current,
            'voltage': self.voltage,
            'frequency': self.frequency,
            'power_factor': self.power_factor,
            'reactive_power': self.reactive_power,
            'total_energy_generated': self.total_energy_generated,
            'total_energy_delivered': self.total_energy_delivered,
            'rated_power': self.rated_power,
            'load_power': self.load_power
        }
