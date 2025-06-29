"""
Pydantic schemas for the KPP Simulator.
Provides type safety and validation for all data structures used in the simulation.
"""

from typing import Dict, List, Optional, Any, Union
from enum import Enum
from pydantic import BaseModel, Field, field_validator, model_validator
import math


class FloaterState(str, Enum):
    """Possible states for a floater."""
    EMPTY = "empty"
    FILLING = "filling"
    FILLED = "filled"
    VENTING = "venting"


class ControlMode(str, Enum):
    """Control system operating modes."""
    NORMAL = "normal"
    STARTUP = "startup"
    EMERGENCY = "emergency"
    MAINTENANCE = "maintenance"
    GRID_SUPPORT = "grid_support"


class ComponentStatus(str, Enum):
    """Component operational status."""
    ONLINE = "online"
    OFFLINE = "offline"
    FAULT = "fault"
    MAINTENANCE = "maintenance"


# Physics Data Schemas
class FloaterPhysicsData(BaseModel):
    """Physics data for a single floater."""
    id: int = Field(..., ge=0, description="Floater identifier")
    position: float = Field(..., description="Position along chain (radians)")
    velocity: float = Field(..., description="Velocity (m/s)")
    acceleration: float = Field(default=0.0, description="Acceleration (m/s²)")
    buoyancy_force: float = Field(default=0.0, description="Buoyancy force (N)")
    drag_force: float = Field(default=0.0, description="Drag force (N)")
    pulse_force: float = Field(default=0.0, description="Pulse jet force (N)")
    net_force: float = Field(default=0.0, description="Net force (N)")
    state: FloaterState = Field(default=FloaterState.EMPTY, description="Current state")
    fill_progress: float = Field(default=0.0, ge=0.0, le=1.0, description="Fill progress (0-1)")
    is_filled: bool = Field(default=False, description="Whether floater is filled")
    
    @field_validator('position')
    @classmethod
    def validate_position(cls, v):
        """Normalize position to [0, 2π]."""
        return v % (2 * math.pi)


class EnhancedPhysicsData(BaseModel):
    """Enhanced physics effects data (H1/H2/H3)."""
    h1_nanobubbles: Dict[str, Any] = Field(default_factory=dict, description="H1 nanobubble effects")
    h2_thermal: Dict[str, Any] = Field(default_factory=dict, description="H2 thermal effects")
    h3_pulse: Dict[str, Any] = Field(default_factory=dict, description="H3 pulse control")
    drag_reduction_factor: float = Field(default=1.0, ge=0.0, le=1.0, description="Drag reduction factor")
    thermal_enhancement: float = Field(default=1.0, ge=0.0, le=2.0, description="Thermal enhancement factor")


class PhysicsResults(BaseModel):
    """Complete physics calculation results."""
    total_vertical_force: float = Field(..., description="Total vertical force (N)")
    base_buoy_force: float = Field(default=0.0, description="Base buoyancy force (N)")
    enhanced_buoy_force: float = Field(default=0.0, description="Enhanced buoyancy force (N)")
    thermal_enhanced_force: float = Field(default=0.0, description="Thermal enhanced force (N)")
    pulse_force: float = Field(default=0.0, description="Pulse force (N)")
    drag_force: float = Field(default=0.0, description="Total drag force (N)")
    net_force: float = Field(..., description="Net force on system (N)")
    floater_data: List[FloaterPhysicsData] = Field(default_factory=list, description="Individual floater data")
    enhanced_physics: EnhancedPhysicsData = Field(default_factory=EnhancedPhysicsData, description="Enhanced physics data")
    chain_dynamics: Dict[str, Any] = Field(default_factory=dict, description="Chain dynamics data")


# System Data Schemas
class DrivetrainData(BaseModel):
    """Drivetrain system data."""
    flywheel_speed_rpm: float = Field(default=0.0, ge=0.0, description="Flywheel speed (RPM)")
    chain_speed_rpm: float = Field(default=0.0, description="Chain speed (RPM)")
    gearbox_ratio: float = Field(default=39.4, gt=0.0, description="Gearbox ratio")
    clutch_engaged: bool = Field(default=False, description="Clutch engagement status")
    clutch_engagement: float = Field(default=0.0, ge=0.0, le=1.0, description="Clutch engagement level")
    input_torque: float = Field(default=0.0, description="Input torque (N⋅m)")
    output_torque: float = Field(default=0.0, description="Output torque (N⋅m)")
    load_torque: float = Field(default=0.0, description="Load torque (N⋅m)")
    system_efficiency: float = Field(default=0.0, ge=0.0, le=1.0, description="System efficiency")
    status: ComponentStatus = Field(default=ComponentStatus.ONLINE, description="Drivetrain status")


class ElectricalData(BaseModel):
    """Electrical system data."""
    power_output: float = Field(default=0.0, ge=0.0, description="Power output (W)")
    grid_power: float = Field(default=0.0, description="Grid power (W)")
    load_torque: float = Field(default=0.0, description="Electrical load torque (N⋅m)")
    voltage: float = Field(default=480.0, gt=0.0, description="Voltage (V)")
    frequency: float = Field(default=60.0, gt=0.0, description="Frequency (Hz)")
    power_factor: float = Field(default=0.95, ge=-1.0, le=1.0, description="Power factor")
    reactive_power: float = Field(default=0.0, description="Reactive power (VAR)")
    system_efficiency: float = Field(default=0.0, ge=0.0, le=1.0, description="Electrical efficiency")
    synchronized: bool = Field(default=False, description="Grid synchronization status")
    load_factor: float = Field(default=0.0, ge=0.0, le=1.0, description="Load factor")
    status: ComponentStatus = Field(default=ComponentStatus.ONLINE, description="Electrical status")


class ControlData(BaseModel):
    """Control system data."""
    control_mode: ControlMode = Field(default=ControlMode.NORMAL, description="Current control mode")
    timing_commands: Dict[str, Any] = Field(default_factory=dict, description="Timing control commands")
    load_commands: Dict[str, Any] = Field(default_factory=dict, description="Load control commands")
    grid_commands: Dict[str, Any] = Field(default_factory=dict, description="Grid control commands")
    fault_status: Dict[str, bool] = Field(default_factory=dict, description="Fault status indicators")
    performance_metrics: Dict[str, float] = Field(default_factory=dict, description="Control performance metrics")
    setpoints: Dict[str, float] = Field(default_factory=dict, description="Control setpoints")
    feedback: Dict[str, float] = Field(default_factory=dict, description="Control feedback values")
    status: ComponentStatus = Field(default=ComponentStatus.ONLINE, description="Control system status")


class SystemResults(BaseModel):
    """Complete system update results."""
    drivetrain: DrivetrainData = Field(default_factory=DrivetrainData, description="Drivetrain data")
    electrical: ElectricalData = Field(default_factory=ElectricalData, description="Electrical data")
    control: ControlData = Field(default_factory=ControlData, description="Control data")
    transient: Dict[str, Any] = Field(default_factory=dict, description="Transient event data")
    enhanced_losses: Dict[str, Any] = Field(default_factory=dict, description="Enhanced loss model data")
    grid_services: Dict[str, Any] = Field(default_factory=dict, description="Grid services data")
    pneumatic_executed: bool = Field(default=False, description="Pneumatic control executed")
    final_torque: float = Field(default=0.0, description="Final output torque (N⋅m)")
    electrical_load_torque: float = Field(default=0.0, description="Electrical load torque (N⋅m)")


class ElectricalSystemOutput(BaseModel):
    """Electrical system update output."""
    electrical_load_torque: float = Field(default=0.0, description="Electrical load torque (N⋅m)")
    power_output: float = Field(default=0.0, ge=0.0, description="Power output (W)")
    grid_power: float = Field(default=0.0, description="Grid power (W)")
    voltage: float = Field(default=480.0, gt=0.0, description="Voltage (V)")
    frequency: float = Field(default=60.0, gt=0.0, description="Frequency (Hz)")
    power_factor: float = Field(default=0.95, ge=-1.0, le=1.0, description="Power factor")
    reactive_power: float = Field(default=0.0, description="Reactive power (VAR)")
    system_efficiency: float = Field(default=0.0, ge=0.0, le=1.0, description="Electrical efficiency")
    synchronized: bool = Field(default=False, description="Grid synchronization status")
    grid_services_active: bool = Field(default=False, description="Grid services active")
    status: ComponentStatus = Field(default=ComponentStatus.ONLINE, description="Electrical status")


class SystemState(BaseModel):
    """System state for control and monitoring."""
    time: float = Field(..., ge=0.0, description="Current time (s)")
    power_output: float = Field(default=0.0, ge=0.0, description="Power output (W)")
    speed_rpm: float = Field(default=0.0, description="Speed (RPM)")
    torque: float = Field(default=0.0, description="Torque (N⋅m)")
    total_vertical_force: float = Field(default=0.0, description="Total vertical force (N)")
    net_force: float = Field(default=0.0, description="Net force (N)")
    drivetrain_status: ComponentStatus = Field(default=ComponentStatus.ONLINE, description="Drivetrain status")
    electrical_status: ComponentStatus = Field(default=ComponentStatus.ONLINE, description="Electrical status")
    control_status: ComponentStatus = Field(default=ComponentStatus.ONLINE, description="Control status")
    fault_flags: Dict[str, bool] = Field(default_factory=dict, description="System fault flags")
    performance_data: Dict[str, float] = Field(default_factory=dict, description="Performance data")


class GridServicesState(BaseModel):
    """Grid services state and control."""
    frequency_regulation_active: bool = Field(default=False, description="Frequency regulation active")
    voltage_support_active: bool = Field(default=False, description="Voltage support active")
    reactive_power_support: bool = Field(default=False, description="Reactive power support active")
    grid_frequency: float = Field(default=60.0, gt=0.0, description="Grid frequency (Hz)")
    grid_voltage: float = Field(default=480.0, gt=0.0, description="Grid voltage (V)")
    power_setpoint: float = Field(default=0.0, description="Power setpoint (W)")
    reactive_setpoint: float = Field(default=0.0, description="Reactive power setpoint (VAR)")
    participation_factor: float = Field(default=1.0, ge=0.0, le=1.0, description="Grid service participation factor")
    status: ComponentStatus = Field(default=ComponentStatus.ONLINE, description="Grid services status")


class TransientEventState(BaseModel):
    """Transient event handling state."""
    fault_detected: bool = Field(default=False, description="Fault detected")
    fault_type: Optional[str] = Field(default=None, description="Type of fault")
    fault_severity: Optional[str] = Field(default=None, description="Fault severity level")
    recovery_active: bool = Field(default=False, description="Recovery procedure active")
    emergency_shutdown: bool = Field(default=False, description="Emergency shutdown active")
    ride_through_active: bool = Field(default=False, description="Fault ride-through active")
    time_since_fault: float = Field(default=0.0, ge=0.0, description="Time since fault (s)")
    status: ComponentStatus = Field(default=ComponentStatus.ONLINE, description="Transient handling status")


# State Management Schemas
class EnergyLossData(BaseModel):
    """Energy loss tracking data."""
    drag_loss: float = Field(default=0.0, ge=0.0, description="Drag losses (J)")
    dissolution_loss: float = Field(default=0.0, ge=0.0, description="Dissolution losses (J)")
    venting_loss: float = Field(default=0.0, ge=0.0, description="Venting losses (J)")
    mechanical_loss: float = Field(default=0.0, ge=0.0, description="Mechanical losses (J)")
    electrical_loss: float = Field(default=0.0, ge=0.0, description="Electrical losses (J)")
    thermal_loss: float = Field(default=0.0, ge=0.0, description="Thermal losses (J)")
    total_loss: float = Field(default=0.0, ge=0.0, description="Total losses (J)")
    net_energy: float = Field(default=0.0, description="Net energy (J)")


class PerformanceMetrics(BaseModel):
    """System performance metrics."""
    overall_efficiency: float = Field(default=0.0, ge=0.0, le=1.0, description="Overall system efficiency")
    power_efficiency: float = Field(default=0.0, ge=0.0, le=1.0, description="Power conversion efficiency")
    mechanical_efficiency: float = Field(default=0.0, ge=0.0, le=1.0, description="Mechanical efficiency")
    electrical_efficiency: float = Field(default=0.0, ge=0.0, le=1.0, description="Electrical efficiency")
    capacity_factor: float = Field(default=0.0, ge=0.0, le=1.0, description="Capacity factor")
    availability: float = Field(default=0.0, ge=0.0, le=1.0, description="System availability")
    uptime: float = Field(default=0.0, ge=0.0, description="Uptime (hours)")


class SimulationState(BaseModel):
    """Complete simulation state data."""
    time: float = Field(..., ge=0.0, description="Simulation time (s)")
    dt: float = Field(..., gt=0.0, description="Time step (s)")
    physics: PhysicsResults = Field(..., description="Physics calculation results")
    systems: SystemResults = Field(..., description="System update results")
    energy_losses: EnergyLossData = Field(default_factory=EnergyLossData, description="Energy loss data")
    performance: PerformanceMetrics = Field(default_factory=PerformanceMetrics, description="Performance metrics")
    status: ComponentStatus = Field(default=ComponentStatus.ONLINE, description="Overall system status")


# Configuration Schemas
class SimulationParams(BaseModel):
    """Simulation parameters with validation."""
    # Time parameters
    time_step: float = Field(default=0.1, gt=0.0, le=1.0, description="Simulation time step (s)")
    
    # Floater parameters
    num_floaters: int = Field(default=8, ge=1, le=20, description="Number of floaters")
    floater_volume: float = Field(default=0.3, gt=0.0, description="Floater volume (m³)")
    floater_mass_empty: float = Field(default=18.0, gt=0.0, description="Empty floater mass (kg)")
    floater_area: float = Field(default=0.035, gt=0.0, description="Floater cross-sectional area (m²)")
    drag_coefficient: float = Field(default=0.8, gt=0.0, description="Drag coefficient")
    
    # Drivetrain parameters
    sprocket_radius: float = Field(default=1.0, gt=0.0, description="Sprocket radius (m)")
    sprocket_teeth: int = Field(default=20, ge=10, le=100, description="Number of sprocket teeth")
    gear_ratio: float = Field(default=39.4, gt=1.0, description="Gear ratio")
    flywheel_inertia: float = Field(default=50.0, gt=0.0, description="Flywheel moment of inertia (kg⋅m²)")
    drivetrain_efficiency: float = Field(default=0.95, gt=0.0, le=1.0, description="Drivetrain efficiency")
    
    # Electrical parameters
    target_power: float = Field(default=530000.0, gt=0.0, description="Target power output (W)")
    target_rpm: float = Field(default=375.0, gt=0.0, description="Target RPM")
    generator_efficiency: float = Field(default=0.94, gt=0.0, le=1.0, description="Generator efficiency")
    
    # Pneumatic parameters
    target_pressure: float = Field(default=5.0, gt=0.0, le=10.0, description="Target pressure (bar)")
    air_fill_time: float = Field(default=0.5, gt=0.0, description="Air fill time (s)")
    
    # Physics parameters
    water_density: float = Field(default=1000.0, gt=0.0, description="Water density (kg/m³)")
    water_temperature: float = Field(default=293.15, gt=200.0, lt=400.0, description="Water temperature (K)")
    gravity: float = Field(default=9.81, gt=0.0, description="Gravitational acceleration (m/s²)")
    
    # Enhanced physics parameters
    h1_enabled: bool = Field(default=False, description="Enable H1 nanobubble physics")
    h2_enabled: bool = Field(default=False, description="Enable H2 thermal physics")
    h3_enabled: bool = Field(default=False, description="Enable H3 pulse control")
    nanobubble_frac: float = Field(default=0.0, ge=0.0, le=0.2, description="Nanobubble fraction")
    drag_reduction_factor: float = Field(default=0.12, ge=0.0, le=0.5, description="Drag reduction factor")
    thermal_efficiency: float = Field(default=0.75, ge=0.0, le=1.0, description="Thermal efficiency")
    
    @field_validator('target_rpm')
    @classmethod
    def validate_rpm_range(cls, v):
        """Validate RPM is within reasonable range."""
        if not (50.0 <= v <= 1000.0):
            raise ValueError("target_rpm must be between 50 and 1000 RPM")
        return v
    
    @field_validator('num_floaters')
    @classmethod
    def validate_floater_count(cls, v):
        """Validate floater count is even for balanced operation."""
        if v % 2 != 0:
            raise ValueError("num_floaters should be even for balanced operation")
        return v
    
    @model_validator(mode='after')
    def validate_enhanced_physics(self):
        """Validate enhanced physics parameter consistency."""
        if self.h1_enabled and self.nanobubble_frac <= 0.0:
            raise ValueError("nanobubble_frac must be > 0 when h1_enabled is True")
        
        if self.h2_enabled and self.thermal_efficiency <= 0.0:
            raise ValueError("thermal_efficiency must be > 0 when h2_enabled is True")
            
        return self


class ManagerInterface(BaseModel):
    """Base interface for all manager classes."""
    manager_type: str = Field(..., description="Type of manager")
    status: ComponentStatus = Field(default=ComponentStatus.ONLINE, description="Manager status")
    last_update_time: Optional[float] = Field(default=None, description="Last update timestamp")
    error_count: int = Field(default=0, ge=0, description="Error count since initialization")
    performance_metrics: Dict[str, float] = Field(default_factory=dict, description="Performance metrics")


# Response Schemas for API
class SimulationStepResponse(BaseModel):
    """Response from a simulation step."""
    success: bool = Field(..., description="Whether step completed successfully")
    state: Optional[SimulationState] = Field(default=None, description="Current simulation state")
    error_message: Optional[str] = Field(default=None, description="Error message if failed")
    execution_time: float = Field(default=0.0, ge=0.0, description="Step execution time (s)")
    warnings: List[str] = Field(default_factory=list, description="Warning messages")


class HealthCheckResponse(BaseModel):
    """System health check response."""
    overall_status: ComponentStatus = Field(..., description="Overall system status")
    managers: Dict[str, ComponentStatus] = Field(..., description="Individual manager statuses")
    uptime: float = Field(..., ge=0.0, description="System uptime (s)")
    error_counts: Dict[str, int] = Field(..., description="Error counts by component")
    performance: PerformanceMetrics = Field(..., description="Current performance metrics")
    timestamp: float = Field(..., description="Health check timestamp")


# Error Schemas
class ValidationError(BaseModel):
    """Validation error details."""
    field: str = Field(..., description="Field that failed validation")
    error_type: str = Field(..., description="Type of validation error")
    message: str = Field(..., description="Error message")
    invalid_value: Any = Field(..., description="Invalid value that caused error")


class SimulationError(BaseModel):
    """Simulation error details."""
    error_code: str = Field(..., description="Error code")
    error_type: str = Field(..., description="Type of error")
    message: str = Field(..., description="Error message")
    component: Optional[str] = Field(default=None, description="Component that caused error")
    timestamp: float = Field(..., description="Error timestamp")
    stack_trace: Optional[str] = Field(default=None, description="Stack trace if available")


# Export all schemas for easy import
__all__ = [
    # Enums
    'FloaterState', 'ControlMode', 'ComponentStatus',
    # Physics schemas
    'FloaterPhysicsData', 'EnhancedPhysicsData', 'PhysicsResults',
    # System schemas
    'DrivetrainData', 'ElectricalData', 'ControlData', 'SystemResults',
    'ElectricalSystemOutput', 'SystemState', 'GridServicesState', 'TransientEventState',
    # State schemas
    'EnergyLossData', 'PerformanceMetrics', 'SimulationState',
    # Configuration schemas
    'SimulationParams', 'ManagerInterface',
    # Response schemas
    'SimulationStepResponse', 'HealthCheckResponse',
    # Error schemas
    'ValidationError', 'SimulationError'
]
