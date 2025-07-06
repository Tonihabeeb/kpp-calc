"""
Configuration schemas for the KPP simulator.
Defines the structure and validation rules for different configuration types.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field



class ConfigSchema(BaseModel):
    """Base schema for configuration validation"""

    class Config:
        extra = "forbid"

    def get_required_fields(self) -> List[str]:
        """Get list of required configuration fields"""
        return [field for field, info in self.__fields__.items() if info.required]

    def get_optional_fields(self) -> List[str]:
        """Get list of optional configuration fields"""
        return [field for field, info in self.__fields__.items() if not info.required]

    def get_field_descriptions(self) -> Dict[str, str]:
        """Get descriptions for all configuration fields"""
        descriptions = {}
        for field, info in self.__fields__.items():
            if hasattr(info.field_info, "description"):
                descriptions[field] = info.field_info.description
            else:
                descriptions[field] = f"Field: {field}"
        return descriptions


class FloaterSchema(ConfigSchema):
    """Schema for floater configuration"""

    # Physical properties
    volume: float = Field(gt=0, le=10, description="Floater volume in m³")
    mass: float = Field(gt=0, le=1000, description="Floater mass in kg")
    drag_coefficient: float = Field(ge=0, le=2, description="Drag coefficient")

    # Pneumatic properties
    air_fill_time: float = Field(gt=0, le=10, description="Air fill time in seconds")
    air_pressure: float = Field(gt=50000, le=1000000, description="Air pressure in Pa")
    air_flow_rate: float = Field(gt=0, le=10, description="Air flow rate in m³/s")
    jet_efficiency: float = Field(ge=0, le=1, description="Jet efficiency (0-1)")

    # Thermal properties
    heat_transfer_coefficient: float = Field(gt=0, le=1000, description="Heat transfer coefficient in W/m²K")
    specific_heat_air: float = Field(gt=0, description="Specific heat of air in J/kg·K")
    specific_heat_water: float = Field(gt=0, description="Specific heat of water in J/kg·K")


class ElectricalSchema(ConfigSchema):
    """Schema for electrical system configuration"""

    # Generator properties
    generator_efficiency: float = Field(ge=0, le=1, description="Generator efficiency (0-1)")
    max_power: float = Field(gt=0, le=100000, description="Maximum power in watts")
    voltage: float = Field(gt=0, le=1000, description="Operating voltage in volts")
    frequency: float = Field(gt=0, le=100, description="Operating frequency in Hz")

    # Power electronics
    inverter_efficiency: float = Field(ge=0, le=1, description="Inverter efficiency (0-1)")
    power_factor: float = Field(ge=0, le=1, description="Power factor (0-1)")

    # Grid interface
    grid_voltage: float = Field(gt=0, le=1000, description="Grid voltage in volts")
    grid_frequency: float = Field(gt=0, le=100, description="Grid frequency in Hz")


class DrivetrainSchema(ConfigSchema):
    """Schema for integrated_drivetrain configuration"""

    # Chain properties
    chain_length: float = Field(gt=0, description="Chain length in meters")
    sprocket_ratio: float = Field(gt=0, description="Sprocket ratio")
    chain_efficiency: float = Field(ge=0, le=1, description="Chain efficiency (0-1)")

    # Gearbox properties
    gear_ratio: float = Field(gt=0, description="Gear ratio")
    gearbox_efficiency: float = Field(ge=0, le=1, description="Gearbox efficiency (0-1)")

    # Flywheel properties
    flywheel_mass: float = Field(gt=0, le=1000, description="Flywheel mass in kg")
    flywheel_radius: float = Field(gt=0, le=10, description="Flywheel radius in meters")


class ControlSchema(ConfigSchema):
    """Schema for control system configuration"""

    # PID parameters
    kp: float = Field(description="Proportional gain")
    ki: float = Field(description="Integral gain")
    kd: float = Field(description="Derivative gain")

    # Control limits
    max_velocity: float = Field(gt=0, le=100, description="Maximum velocity in m/s")
    max_acceleration: float = Field(gt=0, le=100, description="Maximum acceleration in m/s²")

    # Safety parameters
    emergency_stop_velocity: float = Field(gt=0, le=100, description="Emergency stop velocity threshold in m/s")
    position_tolerance: float = Field(gt=0, le=1, description="Position tolerance in meters")


class SimulationSchema(ConfigSchema):
    """Schema for simulation configuration"""

    # Timing
    time_step: float = Field(gt=0, le=1, description="Simulation time step in seconds")
    max_time: float = Field(gt=0, le=86400, description="Maximum simulation time in seconds")

    # Physics
    gravity: float = Field(gt=0, le=20, description="Gravitational acceleration in m/s²")
    water_density: float = Field(gt=0, le=2000, description="Water density in kg/m³")
    air_density: float = Field(gt=0, le=10, description="Air density in kg/m³")

    # Tank
    tank_height: float = Field(gt=0, le=100, description="Tank height in meters")
    tank_diameter: float = Field(gt=0, le=100, description="Tank diameter in meters")

    # System
    num_floaters: int = Field(gt=0, le=100, description="Number of floaters")
    num_chains: int = Field(gt=0, le=10, description="Number of chains")


# Schema registry
SCHEMA_REGISTRY = {
    "floater": FloaterSchema,
    "electrical": ElectricalSchema,
    "integrated_drivetrain": DrivetrainSchema,
    "control": ControlSchema,
    "simulation": SimulationSchema,
}


def get_schema(config_type: str) -> Optional[ConfigSchema]:
    """Get configuration schema by type"""
    return SCHEMA_REGISTRY.get(config_type)


def validate_config_against_schema(config: Dict[str, Any], config_type: str) -> bool:
    """Validate configuration against its schema"""
    schema_class = get_schema(config_type)
    if not schema_class:
        return False

    try:
        schema_class(**config)
        return True
    except Exception:
        return False
