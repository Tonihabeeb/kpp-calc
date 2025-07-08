import logging
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
import math

"""
Chain & Motion Integration Module for KPP Simulation
Manages the kinematic coupling of multiple floaters on the endless chain loop
     and their synchronized motion.
"""

@dataclass
class ChainState:
    """Chain system state"""
    length: float = 100.0  # meters
    speed: float = 0.0  # m/s
    tension: float = 0.0  # N
    position: float = 0.0  # meters (current position)
    floater_positions: List[float] = field(default_factory=list)
    is_moving: bool = False
    emergency_stop: bool = False

class Chain:
    """
    Chain system for KPP simulation.
    Manages the endless chain loop and floater synchronization.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the chain system"""
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # Chain parameters
        self.length = self.config.get('length', 100.0)  # meters
        self.max_speed = self.config.get('max_speed', 60.0)  # m/s
        self.max_tension = self.config.get('max_tension', 50000.0)  # N
        self.num_floaters = self.config.get('num_floaters', 10)
        
        # Physics constants
        self.gravity = 9.81  # m/s²
        self.chain_density = 7850.0  # kg/m³ (steel)
        self.chain_cross_section = 0.001  # m²
        
        # State
        self.state = ChainState(
            length=self.length,
            floater_positions=[i * self.length / self.num_floaters for i in range(self.num_floaters)]
        )
        
        # Performance tracking
        self.total_distance = 0.0
        self.operation_time = 0.0
        self.emergency_stops = 0
        
    def update(self, dt: float, mechanical_power: float = 0.0) -> Dict[str, Any]:
        """
        Update chain state based on mechanical power input
        
        Args:
            dt: Time step in seconds
            mechanical_power: Mechanical power input in watts
            
        Returns:
            Updated state dictionary
        """
        try:
            # Calculate chain speed from mechanical power
            if mechanical_power > 0:
                # Simple power to speed conversion (can be enhanced)
                target_speed = min(
                    math.sqrt(2 * mechanical_power / (self.chain_density * self.chain_cross_section * self.length)),
                    self.max_speed
                )
                
                # Smooth speed transition
                speed_change = (target_speed - self.state.speed) * 0.1
                self.state.speed = max(0, min(self.max_speed, self.state.speed + speed_change))
            else:
                # Decay speed when no power
                self.state.speed *= 0.95
                
            # Update position
            if self.state.speed > 0.1:  # Threshold for movement
                self.state.is_moving = True
                self.state.position += self.state.speed * dt
                self.total_distance += self.state.speed * dt
                
                # Wrap position around chain length
                self.state.position = self.state.position % self.length
                
                # Update floater positions
                for i in range(self.num_floaters):
                    self.state.floater_positions[i] = (self.state.position + i * self.length / self.num_floaters) % self.length
            else:
                self.state.is_moving = False
                
            # Calculate chain tension
            self.state.tension = self._calculate_tension()
            
            # Check for emergency conditions
            if self.state.tension > self.max_tension or self.state.speed > self.max_speed:
                self._emergency_stop()
                
            # Update operation time
            self.operation_time += dt
            
            return self.get_state()
            
        except Exception as e:
            self.logger.error(f"Chain update error: {e}")
            self._emergency_stop()
            return self.get_state()
    
    def get_state(self) -> Dict[str, Any]:
        """Get current chain state"""
        return {
            'length': self.state.length,
            'speed': self.state.speed,
            'tension': self.state.tension,
            'position': self.state.position,
            'floater_positions': self.state.floater_positions.copy(),
            'is_moving': self.state.is_moving,
            'emergency_stop': self.state.emergency_stop,
            'total_distance': self.total_distance,
            'operation_time': self.operation_time,
            'emergency_stops': self.emergency_stops
        }
    
    def reset(self) -> None:
        """Reset chain to initial state"""
        self.state = ChainState(
            length=self.length,
            floater_positions=[i * self.length / self.num_floaters for i in range(self.num_floaters)]
        )
        self.total_distance = 0.0
        self.operation_time = 0.0
        self.emergency_stops = 0
        self.logger.info("Chain system reset")
    
    def start(self) -> None:
        """Start the chain system"""
        self.state.emergency_stop = False
        self.logger.info("Chain system started")
    
    def stop(self) -> None:
        """Stop the chain system"""
        self.state.speed = 0.0
        self.state.is_moving = False
        self.logger.info("Chain system stopped")
    
    def _calculate_tension(self) -> float:
        """Calculate current chain tension"""
        if not self.state.is_moving:
            return 0.0
            
        # Basic tension calculation (can be enhanced with more physics)
        mass_per_meter = self.chain_density * self.chain_cross_section
        centrifugal_force = mass_per_meter * self.state.speed ** 2
        gravitational_force = mass_per_meter * self.gravity * self.length * 0.1  # 10% of chain weight
        
        return centrifugal_force + gravitational_force
    
    def _emergency_stop(self) -> None:
        """Execute emergency stop"""
        self.state.emergency_stop = True
        self.state.speed = 0.0
        self.state.is_moving = False
        self.emergency_stops += 1
        self.logger.warning(f"Emergency stop executed (tension: {self.state.tension:.1f}N, speed: {self.state.speed:.1f}m/s)")