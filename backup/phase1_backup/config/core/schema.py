from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
"""
Configuration schemas for the KPP simulator.
Defines the structure and validation rules for different configuration types.
"""

class ConfigSchema(BaseModel):
    """
    Base configuration schema for the KPP simulator.
    Provides validation and structure for configuration data.
    """
    
    # Simulation parameters
    simulation_duration: float = Field(default=3600.0, description="Simulation duration in seconds")
    time_step: float = Field(default=0.01, description="Time step in seconds")
    max_iterations: int = Field(default=1000000, description="Maximum simulation iterations")
    
    # Physics parameters
    gravity: float = Field(default=9.81, description="Gravitational acceleration (m/s²)")
    water_density: float = Field(default=1000.0, description="Water density (kg/m³)")
    air_density: float = Field(default=1.225, description="Air density (kg/m³)")
    
    # Floater parameters
    floater_count: int = Field(default=10, description="Number of floaters")
    floater_volume: float = Field(default=0.4, description="Floater volume (m³)")
    floater_mass: float = Field(default=16.0, description="Floater mass (kg)")
    
    # Chain parameters
    chain_length: float = Field(default=100.0, description="Chain length (m)")
    chain_mass_per_meter: float = Field(default=10.0, description="Chain mass per meter (kg/m)")
    chain_diameter: float = Field(default=0.02, description="Chain diameter (m)")
    
    # Electrical parameters
    generator_efficiency: float = Field(default=0.95, description="Generator efficiency")
    electrical_power_rating: float = Field(default=50000.0, description="Electrical power rating (W)")
    voltage: float = Field(default=480.0, description="System voltage (V)")
    
    # Control parameters
    control_mode: str = Field(default="automatic", description="Control mode")
    target_power: float = Field(default=25000.0, description="Target power output (W)")
    safety_margins: Dict[str, float] = Field(default_factory=dict, description="Safety margins")
    
    # Performance parameters
    performance_tracking: bool = Field(default=True, description="Enable performance tracking")
    logging_level: str = Field(default="INFO", description="Logging level")
    data_export: bool = Field(default=True, description="Enable data export")
    
    class Config:
        """Pydantic configuration"""
        validate_assignment = True
        extra = "forbid"
    
    def validate_configuration(self) -> List[str]:
        """
        Validate the configuration and return any errors.
        
        Returns:
            List of validation error messages
        """
        errors = []
        
        # Check for positive values
        if self.simulation_duration <= 0:
            errors.append("simulation_duration must be positive")
        
        if self.time_step <= 0:
            errors.append("time_step must be positive")
        
        if self.max_iterations <= 0:
            errors.append("max_iterations must be positive")
        
        if self.gravity <= 0:
            errors.append("gravity must be positive")
        
        if self.water_density <= 0:
            errors.append("water_density must be positive")
        
        if self.air_density <= 0:
            errors.append("air_density must be positive")
        
        if self.floater_count <= 0:
            errors.append("floater_count must be positive")
        
        if self.floater_volume <= 0:
            errors.append("floater_volume must be positive")
        
        if self.floater_mass <= 0:
            errors.append("floater_mass must be positive")
        
        if self.chain_length <= 0:
            errors.append("chain_length must be positive")
        
        if self.chain_mass_per_meter <= 0:
            errors.append("chain_mass_per_meter must be positive")
        
        if self.chain_diameter <= 0:
            errors.append("chain_diameter must be positive")
        
        if not 0 <= self.generator_efficiency <= 1:
            errors.append("generator_efficiency must be between 0 and 1")
        
        if self.electrical_power_rating <= 0:
            errors.append("electrical_power_rating must be positive")
        
        if self.voltage <= 0:
            errors.append("voltage must be positive")
        
        if self.target_power <= 0:
            errors.append("target_power must be positive")
        
        return errors
    
    def get_configuration_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the configuration.
        
        Returns:
            Dictionary containing configuration summary
        """
        return {
            'simulation_parameters': {
                'duration': self.simulation_duration,
                'time_step': self.time_step,
                'max_iterations': self.max_iterations
            },
            'physics_parameters': {
                'gravity': self.gravity,
                'water_density': self.water_density,
                'air_density': self.air_density
            },
            'floater_parameters': {
                'count': self.floater_count,
                'volume': self.floater_volume,
                'mass': self.floater_mass
            },
            'chain_parameters': {
                'length': self.chain_length,
                'mass_per_meter': self.chain_mass_per_meter,
                'diameter': self.chain_diameter
            },
            'electrical_parameters': {
                'generator_efficiency': self.generator_efficiency,
                'power_rating': self.electrical_power_rating,
                'voltage': self.voltage
            },
            'control_parameters': {
                'mode': self.control_mode,
                'target_power': self.target_power,
                'safety_margins': self.safety_margins
            },
            'performance_parameters': {
                'tracking_enabled': self.performance_tracking,
                'logging_level': self.logging_level,
                'data_export_enabled': self.data_export
            }
        }

