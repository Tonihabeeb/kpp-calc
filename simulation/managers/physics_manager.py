import math
import logging
from typing import Any, Dict, Tuple, Optional
import numpy as np
from simulation.schemas import EnhancedPhysicsData, FloaterPhysicsData, FloaterState, PhysicsResults
from simulation.managers.base_manager import BaseManager, ManagerType
"""
Physics Manager for the KPP Simulation Engine.
Handles all physics calculations including floater forces, enhanced H1/H2/H3 physics,
and chain dynamics.
"""


class PhysicsManager(BaseManager):
    """Manager for physics calculations and simulations"""
    
    def __init__(self):
        super().__init__(ManagerType.PHYSICS)
        self.physics_data: Dict[str, FloaterPhysicsData] = {}
        self.enhanced_data: Optional[EnhancedPhysicsData] = None
        self.time_step = 0.01  # 10ms default time step
        
    def initialize(self) -> bool:
        """Initialize the physics manager"""
        try:
            success = super().initialize()
            if success:
                self.physics_data.clear()
                self.enhanced_data = None
            return success
        except Exception as e:
            self.handle_error("PHYSICS_INIT_ERROR", str(e))
            return False
            
    def register_floater(self, floater_id: str) -> bool:
        """Register a new floater for physics calculations"""
        try:
            if self.register_component(floater_id):
                self.physics_data[floater_id] = FloaterPhysicsData(
                    buoyancy_force=0.0,
                    drag_force=0.0,
                    net_force=0.0,
                    state=FloaterState.NEUTRAL,
                    depth=0.0,
                    velocity=0.0,
                    acceleration=0.0,
                    power=0.0
                )
                return True
            return False
        except Exception as e:
            self.handle_error("FLOATER_REGISTRATION_ERROR", str(e), floater_id)
            return False
            
    def update_floater_physics(
        self,
        floater_id: str,
        depth: float,
        velocity: float,
        buoyancy_force: float,
        drag_force: float
    ) -> bool:
        """Update physics calculations for a specific floater"""
        try:
            if floater_id not in self.physics_data:
                return False
                
            data = self.physics_data[floater_id]
            data.depth = depth
            data.velocity = velocity
            data.buoyancy_force = buoyancy_force
            data.drag_force = drag_force
            
            # Calculate derived values
            data.net_force = buoyancy_force - drag_force
            data.acceleration = data.net_force / 100.0  # Assuming 100kg mass
            data.power = abs(data.net_force * velocity)
            
            # Update state
            if velocity > 0.1:
                data.state = FloaterState.RISING
            elif velocity < -0.1:
                data.state = FloaterState.FALLING
            else:
                data.state = FloaterState.NEUTRAL
                
            return True
        except Exception as e:
            self.handle_error("PHYSICS_UPDATE_ERROR", str(e), floater_id)
            return False
            
    def calculate_system_physics(self) -> Optional[EnhancedPhysicsData]:
        """Calculate overall system physics"""
        try:
            if not self.physics_data:
                return None
                
            total_power = sum(data.power for data in self.physics_data.values())
            avg_velocity = np.mean([data.velocity for data in self.physics_data.values()])
            total_force = sum(data.net_force for data in self.physics_data.values())
            
            # Calculate electrical conversion (assuming 85% efficiency)
            electrical_power = total_power * 0.85
            system_efficiency = electrical_power / total_power if total_power > 0 else 0.0
            
            # Calculate chain tension (simplified model)
            chain_tension = abs(total_force) * 1.5  # 50% safety factor
            
            self.enhanced_data = EnhancedPhysicsData(
                mechanical_power=total_power,
                electrical_power=electrical_power,
                system_efficiency=system_efficiency,
                chain_tension=chain_tension,
                floater_forces=self.physics_data.copy(),
                total_force=total_force,
                average_velocity=avg_velocity
            )
            
            return self.enhanced_data
        except Exception as e:
            self.handle_error("SYSTEM_PHYSICS_ERROR", str(e))
            return None
            
    def get_floater_physics(self, floater_id: str) -> Optional[FloaterPhysicsData]:
        """Get physics data for a specific floater"""
        return self.physics_data.get(floater_id)
        
    def get_system_physics(self) -> Optional[EnhancedPhysicsData]:
        """Get the latest system physics calculations"""
        return self.enhanced_data
        
    def set_time_step(self, time_step: float) -> None:
        """Set the simulation time step"""
        if time_step <= 0:
            self.handle_error("INVALID_TIME_STEP", "Time step must be positive")
            return
        self.time_step = time_step

