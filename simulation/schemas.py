"""
Data structures and schemas for the KPP simulator.
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Protocol
from enum import Enum

class ComponentStatus(Enum):
    """Status of a simulation component"""
    INITIALIZING = "initializing"
    READY = "ready"
    RUNNING = "running"
    ERROR = "error"
    STOPPED = "stopped"

class ManagerType(Enum):
    """Types of simulation managers"""
    PHYSICS = "physics"
    CONTROL = "control"
    GRID = "grid"
    COMPONENT = "component"

class ManagerInterface(Protocol):
    """Protocol defining the interface for simulation managers"""
    def initialize(self) -> bool:
        """Initialize the manager"""
        ...
    
    def update(self, state: Any, time_step: float) -> Any:
        """Update the manager state"""
        ...
    
    def get_state(self) -> Any:
        """Get current manager state"""
        ...
    
    def cleanup(self) -> None:
        """Clean up resources"""
        ...
    
    @property
    def type(self) -> ManagerType:
        """Get manager type"""
        ...
    
    @property
    def status(self) -> ComponentStatus:
        """Get current status"""
        ...

@dataclass
class SimulationError:
    """Error information for simulation issues"""
    message: str
    error_code: str = "SIMULATION_ERROR"
    component: Optional[str] = None
    severity: str = "error"
    timestamp: Optional[float] = None

@dataclass
class FloaterState:
    """State of a single floater"""
    position: float
    velocity: float
    is_buoyant: bool
    buoyant_force: float
    drag_force: float
    net_force: float
    mass: float = 0.0
    volume: float = 0.0
    h1_effect: Optional[dict] = None
    h2_effect: Optional[dict] = None

@dataclass
class DrivetrainState:
    """State of the drivetrain system"""
    angular_velocity: float  # rad/s
    angular_position: float  # rad
    torque: float  # N·m
    power: float  # W
    is_clutch_engaged: bool
    flywheel_energy: float  # J

@dataclass
class PneumaticState:
    """State of the pneumatic system"""
    pressure: float  # Pa
    temperature: float  # K
    flow_rate: float  # m³/s
    energy_input: float  # J
    is_injecting: bool
    is_venting: bool

@dataclass
class EnvironmentState:
    """State of the environment"""
    water_density: float  # kg/m³
    water_temperature: float  # K
    nanobubble_density: Optional[float] = None  # kg/m³
    thermal_expansion: Optional[float] = None

@dataclass
class PhysicsResults:
    """Results from physics calculations"""
    total_power: float  # W
    total_energy: float  # J
    efficiency: float
    mechanical_power: float  # W
    electrical_power: float  # W
    losses: Dict[str, float]  # Different types of losses
    h3_state: Optional[dict] = None

@dataclass
class FloaterPhysicsData:
    """Detailed physics data for a floater"""
    forces: Dict[str, float]
    energy: Dict[str, float]
    position_data: Dict[str, float]

@dataclass
class EnhancedPhysicsData:
    """Data specific to physics enhancements"""
    h1_effect: Optional[Dict[str, float]] = None
    h2_effect: Optional[Dict[str, float]] = None
    h3_effect: Optional[Dict[str, float]] = None

@dataclass
class GridConditions:
    """Grid conditions and parameters"""
    frequency: float  # Hz
    voltage: float  # pu
    power: float  # W
    power_factor: float

@dataclass
class BatteryState:
    """State of energy storage system"""
    state_of_charge: float
    power: float
    energy: float
    temperature: float

@dataclass
class SystemState:
    """State of a system component"""
    status: ComponentStatus
    error: Optional[SimulationError] = None
    data: Optional[Dict[str, Any]] = None

@dataclass
class SimulationState:
    """Complete state of the simulation"""
    time: float
    step_count: int
    total_power: float
    total_energy: float
    efficiency: float
    environment: Optional[EnvironmentState]
    pneumatics: Optional[PneumaticState]
    drivetrain: Optional[DrivetrainState]
    floaters: List[FloaterState]
    control: Optional[Any]
    grid_services: Optional[Any]
    errors: List[SimulationError]
    component_status: Dict[str, ComponentStatus]

