import math
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, root_validator, validator
from enum import Enum
from dataclasses import dataclass

"""
Pydantic schemas for the KPP Simulator.
Provides type safety and validation for all data structures used in the simulation.
"""

class FloaterState(str, Enum):
    """Floater state enumeration"""
    EMPTY = "empty"
    FILLING = "filling"
    FULL = "full"
    VENTING = "venting"

@dataclass
class PhysicsResults:
    """Physics calculation results"""
    time: float = 0.0
    total_torque: float = 0.0
    total_power: float = 0.0
    efficiency: float = 0.0
    active_floaters: int = 0
    total_floaters: int = 0
    step_time: float = 0.0
    error: Optional[str] = None

@dataclass
class FloaterPhysicsData:
    """Floater physics data"""
    position: float = 0.0
    velocity: float = 0.0
    acceleration: float = 0.0
    mass: float = 16.0
    volume: float = 0.4
    area: float = 0.1
    drag_coefficient: float = 0.6
    air_fill_level: float = 0.0
    state: FloaterState = FloaterState.EMPTY

@dataclass
class EnhancedPhysicsData:
    """Enhanced physics data with additional metrics"""
    basic_data: FloaterPhysicsData
    buoyant_force: float = 0.0
    gravitational_force: float = 0.0
    drag_force: float = 0.0
    net_force: float = 0.0
    torque: float = 0.0
    power: float = 0.0
    energy: float = 0.0

class SystemState(BaseModel):
    """System state model"""
    time: float = Field(default=0.0, description="Current simulation time")
    total_energy: float = Field(default=0.0, description="Total system energy")
    total_power: float = Field(default=0.0, description="Total system power")
    efficiency: float = Field(default=0.0, description="System efficiency")
    active_floaters: int = Field(default=0, description="Number of active floaters")
    total_floaters: int = Field(default=0, description="Total number of floaters")
    
    class Config:
        validate_assignment = True

class PerformanceMetrics(BaseModel):
    """Performance metrics model"""
    step_count: int = Field(default=0, description="Number of simulation steps")
    error_count: int = Field(default=0, description="Number of errors")
    average_step_time: float = Field(default=0.0, description="Average step time")
    total_energy: float = Field(default=0.0, description="Total energy")
    total_power: float = Field(default=0.0, description="Total power")
    efficiency: float = Field(default=0.0, description="System efficiency")
    
    class Config:
        validate_assignment = True

class EnergyLossData(BaseModel):
    """Energy loss data model"""
    mechanical_losses: float = Field(default=0.0, description="Mechanical losses")
    electrical_losses: float = Field(default=0.0, description="Electrical losses")
    thermal_losses: float = Field(default=0.0, description="Thermal losses")
    friction_losses: float = Field(default=0.0, description="Friction losses")
    total_losses: float = Field(default=0.0, description="Total losses")
    
    @root_validator
    def calculate_total_losses(cls, values):
        """Calculate total losses"""
        values['total_losses'] = (
            values.get('mechanical_losses', 0.0) +
            values.get('electrical_losses', 0.0) +
            values.get('thermal_losses', 0.0) +
            values.get('friction_losses', 0.0)
        )
        return values

class SimulationState(BaseModel):
    """Simulation state model"""
    time: float = Field(default=0.0, description="Current simulation time")
    is_running: bool = Field(default=False, description="Simulation running status")
    step_count: int = Field(default=0, description="Current step count")
    error_count: int = Field(default=0, description="Error count")
    
    class Config:
        validate_assignment = True

class SystemResults(BaseModel):
    """System results model"""
    time: float = Field(default=0.0, description="Result time")
    total_torque: float = Field(default=0.0, description="Total torque")
    total_power: float = Field(default=0.0, description="Total power")
    efficiency: float = Field(default=0.0, description="System efficiency")
    active_floaters: int = Field(default=0, description="Active floaters")
    total_floaters: int = Field(default=0, description="Total floaters")
    
    class Config:
        validate_assignment = True

