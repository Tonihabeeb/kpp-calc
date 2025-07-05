"""
Pneumatic system for floater air injection and venting.
Handles air filling, venting, and pressure management.
"""

import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class PneumaticState:
    """Represents the current pneumatic state of a floater"""
    fill_state: str = "empty"  # 'empty', 'filling', 'full', 'venting'
    air_fill_level: float = 0.0  # 0.0 to 1.0
    pneumatic_pressure: float = 101325.0  # Pa
    target_air_volume: float = 0.0  # m³
    injection_start_time: float = 0.0
    total_air_injected: float = 0.0
    injection_complete: bool = False
    air_temperature: float = 293.15  # K
    last_injection_energy: float = 0.0  # J
    thermal_energy_contribution: float = 0.0  # J
    expansion_work_done: float = 0.0  # J
    venting_energy_loss: float = 0.0  # J

class PneumaticSystem:
    """Handles pneumatic operations for a single floater"""
    
    def __init__(self, 
                 air_fill_time: float = 0.5,
                 air_pressure: float = 300000,
                 air_flow_rate: float = 0.6,
                 jet_efficiency: float = 0.85):
        self.air_fill_time = air_fill_time
        self.air_pressure = air_pressure
        self.air_flow_rate = air_flow_rate
        self.jet_efficiency = jet_efficiency
        self.state = PneumaticState()
    
    def start_injection(self, target_volume: float, injection_pressure: float, 
                       current_time: float) -> bool:
        """Start air injection process"""
        if self.state.fill_state != "empty":
            logger.warning("Cannot start injection: floater not empty")
            return False
        
        self.state.fill_state = "filling"
        self.state.target_air_volume = target_volume
        self.state.pneumatic_pressure = injection_pressure
        self.state.injection_start_time = current_time
        self.state.total_air_injected = 0.0
        self.state.injection_complete = False
        
        logger.info(f"Started air injection: target={target_volume:.3f}m³")
        return True
    
    def update_injection(self, injected_volume: float, dt: float) -> None:
        """Update injection progress"""
        if self.state.fill_state != "filling":
            return
        
        self.state.total_air_injected += injected_volume
        self.state.air_fill_level = min(1.0, 
            self.state.total_air_injected / self.state.target_air_volume)
        
        # Check if injection is complete
        if self.state.air_fill_level >= 1.0:
            self.complete_injection()
    
    def complete_injection(self) -> None:
        """Complete the injection process"""
        self.state.fill_state = "full"
        self.state.injection_complete = True
        self.state.air_fill_level = 1.0
        logger.info("Air injection completed")
    
    def start_venting(self, current_time: float) -> bool:
        """Start air venting process"""
        if self.state.fill_state != "full":
            logger.warning("Cannot start venting: floater not full")
            return False
        
        self.state.fill_state = "venting"
        logger.info("Started air venting")
        return True
    
    def update_venting(self, venting_rate: float, dt: float) -> bool:
        """Update venting progress"""
        if self.state.fill_state != "venting":
            return False
        
        # Reduce air fill level
        air_volume_lost = venting_rate * dt
        self.state.air_fill_level = max(0.0, 
            self.state.air_fill_level - air_volume_lost)
        
        # Check if venting is complete
        if self.state.air_fill_level <= 0.0:
            self.complete_venting()
            return True
        
        return False
    
    def complete_venting(self) -> None:
        """Complete the venting process"""
        self.state.fill_state = "empty"
        self.state.air_fill_level = 0.0
        self.state.total_air_injected = 0.0
        logger.info("Air venting completed")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current pneumatic status"""
        return {
            "fill_state": self.state.fill_state,
            "air_fill_level": self.state.air_fill_level,
            "pneumatic_pressure": self.state.pneumatic_pressure,
            "target_air_volume": self.state.target_air_volume,
            "total_air_injected": self.state.total_air_injected,
            "injection_complete": self.state.injection_complete,
            "air_temperature": self.state.air_temperature,
            "last_injection_energy": self.state.last_injection_energy,
            "thermal_energy_contribution": self.state.thermal_energy_contribution,
            "expansion_work_done": self.state.expansion_work_done,
            "venting_energy_loss": self.state.venting_energy_loss
        }
    
    def reset(self) -> None:
        """Reset pneumatic system to initial state"""
        self.state = PneumaticState()
