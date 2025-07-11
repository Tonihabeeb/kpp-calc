"""
Enhanced pneumatic system with gradual filling and pressure dynamics.
"""

import numpy as np
from typing import Dict, Any, Optional
import sys
from pathlib import Path

# Add paths for imports
project_root = Path(__file__).parent.parent.parent.parent
thermo_dir = project_root / "simulation" / "physics" / "thermodynamics"
sys.path.insert(0, str(thermo_dir))

from air_system import AirThermodynamics
from pneumatic_events import PneumaticEventSystem

class EnhancedPneumaticSystem:
    """Enhanced pneumatic system with thermodynamic modeling"""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize enhanced pneumatic system"""
        self.config = config
        
        # Initialize components
        self.air_thermo = AirThermodynamics(config.get('air_thermo', {}))
        self.event_system = PneumaticEventSystem(config.get('events', {}))
        
        # System parameters
        self.compressor_pressure = config.get('compressor_pressure', 500000.0)  # Pa
        self.floater_volume = config.get('floater_volume', 0.4)  # m^3
        self.ambient_pressure = config.get('ambient_pressure', 101325.0)  # Pa
        self.ambient_temperature = config.get('ambient_temperature', 293.15)  # K
        
        # Floater states
        self.floater_states = {}  # floater_id -> state
        
        # Energy tracking
        self.total_compressor_energy = 0.0
        self.total_injection_energy = 0.0
        
        print("EnhancedPneumaticSystem initialized")
        
    def initialize_floater(self, floater_id: int, initial_state: str = 'water_filled') -> None:
        """Initialize a floater's pneumatic state"""
        self.floater_states[floater_id] = {
            'state': initial_state,  # 'water_filled', 'air_filled', 'filling'
            'air_mass': 0.0,  # kg
            'air_pressure': self.ambient_pressure,  # Pa
            'air_temperature': self.ambient_temperature,  # K
            'fill_fraction': 0.0,  # 0.0 = water filled, 1.0 = air filled
            'injection_start_time': None,
            'last_update_time': 0.0
        }
        
    def start_air_injection(self, floater_id: int) -> bool:
        """Start air injection for a floater"""
        if floater_id not in self.floater_states:
            self.initialize_floater(floater_id)
            
        floater_state = self.floater_states[floater_id]
        
        if floater_state['state'] == 'filling':
            print(f"Floater {floater_id} is already being filled")
            return False
            
        # Start injection
        floater_state['state'] = 'filling'
        floater_state['injection_start_time'] = self.event_system.env.now
        
        # Start SimPy event
        self.event_system.start_injection(floater_id, self.compressor_pressure)
        
        print(f"Started air injection for floater {floater_id}")
        return True
        
    def update_floater_filling(self, floater_id: int, current_time: float, dt: float) -> None:
        """Update floater filling process"""
        if floater_id not in self.floater_states:
            return
            
        floater_state = self.floater_states[floater_id]
        
        if floater_state['state'] != 'filling':
            return
            
        # Calculate filling progress
        injection_duration = self.config.get('events', {}).get('injection_duration', 0.5)
        elapsed_time = current_time - floater_state['injection_start_time']
        
        if elapsed_time >= injection_duration:
            # Filling complete
            floater_state['state'] = 'air_filled'
            floater_state['fill_fraction'] = 1.0
            floater_state['air_pressure'] = self.compressor_pressure
            floater_state['air_temperature'] = self.ambient_temperature
            
            # Calculate final air mass
            air_density = self.air_thermo.get_air_density(
                floater_state['air_temperature'], floater_state['air_pressure']
            )
            floater_state['air_mass'] = air_density * self.floater_volume
            
            print(f"Floater {floater_id} filling complete")
        else:
            # Gradual filling
            fill_progress = elapsed_time / injection_duration
            floater_state['fill_fraction'] = fill_progress
            
            # Calculate current air properties
            current_pressure = self.ambient_pressure + fill_progress * (self.compressor_pressure - self.ambient_pressure)
            current_temp = self.ambient_temperature  # Simplified - no temperature change during filling
            
            floater_state['air_pressure'] = current_pressure
            floater_state['air_temperature'] = current_temp
            
            # Calculate current air mass
            air_density = self.air_thermo.get_air_density(current_temp, current_pressure)
            floater_state['air_mass'] = air_density * self.floater_volume * fill_progress
            
    def release_air(self, floater_id: int) -> None:
        """Release air from a floater"""
        if floater_id not in self.floater_states:
            return
            
        floater_state = self.floater_states[floater_id]
        
        # Calculate energy released
        if floater_state['air_mass'] > 0:
            expansion_work = self.air_thermo.calculate_expansion_work(
                floater_state['air_pressure'], self.ambient_pressure,
                floater_state['air_temperature'], floater_state['air_mass']
            )
            self.total_injection_energy += expansion_work
            
        # Reset floater state
        floater_state['state'] = 'water_filled'
        floater_state['fill_fraction'] = 0.0
        floater_state['air_mass'] = 0.0
        floater_state['air_pressure'] = self.ambient_pressure
        floater_state['air_temperature'] = self.ambient_temperature
        
        print(f"Released air from floater {floater_id}")
        
    def calculate_compressor_energy(self, injection_count: int) -> float:
        """Calculate total compressor energy for given number of injections"""
        # Simplified calculation - in practice would be more complex
        compression_work_per_injection = self.air_thermo.calculate_compression_work(
            self.ambient_pressure, self.compressor_pressure,
            self.ambient_temperature, 1.0  # 1 kg of air
        )
        
        return compression_work_per_injection * injection_count
        
    def get_floater_state(self, floater_id: int) -> Dict[str, Any]:
        """Get current state of a floater"""
        if floater_id not in self.floater_states:
            return {}
        return self.floater_states[floater_id].copy()
        
    def get_system_status(self) -> Dict[str, Any]:
        """Get overall pneumatic system status"""
        air_filled_count = sum(1 for state in self.floater_states.values() 
                              if state['state'] == 'air_filled')
        filling_count = sum(1 for state in self.floater_states.values() 
                           if state['state'] == 'filling')
        
        return {
            'total_floaters': len(self.floater_states),
            'air_filled_count': air_filled_count,
            'filling_count': filling_count,
            'compressor_pressure': self.compressor_pressure,
            'total_compressor_energy': self.total_compressor_energy,
            'total_injection_energy': self.total_injection_energy,
            'event_system_state': self.event_system.get_system_state()
        }
