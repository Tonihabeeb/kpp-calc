import math
import logging
import time
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

"""
Environment (Water & Hydrodynamics) module.
Encapsulates water properties and H1/H2 hypothesis logic for the KPP simulator.
"""

class EnvironmentType(str, Enum):
    """Environment type enumeration"""
    STANDARD = "standard"
    TROPICAL = "tropical"
    ARCTIC = "arctic"
    HIGH_ALTITUDE = "high_altitude"
    UNDERWATER = "underwater"

class WeatherCondition(str, Enum):
    """Weather condition enumeration"""
    CLEAR = "clear"
    CLOUDY = "cloudy"
    RAINY = "rainy"
    WINDY = "windy"
    STORMY = "stormy"

@dataclass
class EnvironmentState:
    """Environment state data structure"""
    temperature: float = 293.15  # K
    pressure: float = 101325.0  # Pa
    humidity: float = 0.6  # 60% relative humidity
    altitude: float = 0.0  # m above sea level
    water_temperature: float = 293.15  # K
    water_depth: float = 10.0  # m
    wind_speed: float = 0.0  # m/s
    weather_condition: WeatherCondition = WeatherCondition.CLEAR
    environment_type: EnvironmentType = EnvironmentType.STANDARD

@dataclass
class EnvironmentConfig:
    """Environment system configuration"""
    sea_level_pressure: float = 101325.0  # Pa
    sea_level_temperature: float = 288.15  # K (15°C)
    temperature_lapse_rate: float = 0.0065  # K/m
    pressure_scale_height: float = 8500.0  # m
    earth_radius: float = 6371000.0  # m
    gravity_sea_level: float = 9.81  # m/s²
    water_density_standard: float = 1000.0  # kg/m³
    water_viscosity_standard: float = 0.001  # Pa·s
    air_density_standard: float = 1.225  # kg/m³
    air_viscosity_standard: float = 1.81e-5  # Pa·s

class EnvironmentSystem:
    """
    Comprehensive environment modeling system for KPP simulation.
    Handles environmental conditions, water properties, and atmospheric effects.
    """
    
    def __init__(self, config: Optional[EnvironmentConfig] = None):
        """
        Initialize the environment system.
        
        Args:
            config: Environment system configuration
        """
        self.config = config or EnvironmentConfig()
        self.logger = logging.getLogger(__name__)
        
        # Environment state
        self.environment_state = EnvironmentState()
        
        # Performance tracking
        self.performance_metrics = {
            'temperature_variations': 0.0,
            'pressure_variations': 0.0,
            'humidity_effects': 0.0,
            'altitude_effects': 0.0,
            'weather_impact': 0.0
        }
        
        # Environmental history
        self.environment_history: List[Dict[str, Any]] = []
        
        # Physics constants
        self.gas_constant = 287.1  # J/kg·K (dry air)
        self.water_vapor_constant = 461.5  # J/kg·K
        self.latent_heat_vaporization = 2.26e6  # J/kg
        
        self.logger.info("Environment system initialized")
    
    def calculate_atmospheric_pressure(self, altitude: float) -> float:
        """
        Calculate atmospheric pressure at given altitude.
        
        Args:
            altitude: Altitude above sea level (m)
            
        Returns:
            Atmospheric pressure (Pa)
        """
        try:
            # Barometric formula: P = P₀ × exp(-h/H)
            # where H is the scale height
            pressure = self.config.sea_level_pressure * math.exp(-altitude / self.config.pressure_scale_height)
            return pressure
            
        except Exception as e:
            self.logger.error("Error calculating atmospheric pressure: %s", e)
            return self.config.sea_level_pressure
    
    def calculate_atmospheric_temperature(self, altitude: float) -> float:
        """
        Calculate atmospheric temperature at given altitude.
        
        Args:
            altitude: Altitude above sea level (m)
            
        Returns:
            Atmospheric temperature (K)
        """
        try:
            # Linear temperature lapse rate: T = T₀ - L × h
            # where L is the lapse rate
            temperature = self.config.sea_level_temperature - self.config.temperature_lapse_rate * altitude
            return temperature
            
        except Exception as e:
            self.logger.error("Error calculating atmospheric temperature: %s", e)
            return self.config.sea_level_temperature
    
    def calculate_gravity_at_altitude(self, altitude: float) -> float:
        """
        Calculate gravitational acceleration at given altitude.
        
        Args:
            altitude: Altitude above sea level (m)
            
        Returns:
            Gravitational acceleration (m/s²)
        """
        try:
            # g = g₀ × (R/(R+h))²
            # where R is Earth's radius
            gravity = self.config.gravity_sea_level * (self.config.earth_radius / (self.config.earth_radius + altitude)) ** 2
            return gravity
            
        except Exception as e:
            self.logger.error("Error calculating gravity at altitude: %s", e)
            return self.config.gravity_sea_level
    
    def calculate_water_density(self, temperature: float, pressure: float, salinity: float = 0.035) -> float:
        """
        Calculate water density based on temperature, pressure, and salinity.
        
        Args:
            temperature: Water temperature (K)
            pressure: Water pressure (Pa)
            salinity: Water salinity (kg/kg)
            
        Returns:
            Water density (kg/m³)
        """
        try:
            # Reference conditions
            ref_temperature = 273.15  # K (0°C)
            ref_pressure = 101325.0  # Pa
            ref_density = self.config.water_density_standard
            
            # Temperature effect (simplified)
            # Water density decreases with temperature above 4°C
            temp_factor = 1.0 - 2.1e-4 * (temperature - ref_temperature)
            
            # Pressure effect (water is nearly incompressible)
            pressure_factor = 1.0 + 4.5e-10 * (pressure - ref_pressure)
            
            # Salinity effect
            salinity_factor = 1.0 + 0.8 * salinity
            
            # Combined effect
            density = ref_density * temp_factor * pressure_factor * salinity_factor
            
            return density
            
        except Exception as e:
            self.logger.error("Error calculating water density: %s", e)
            return self.config.water_density_standard
    
    def calculate_water_viscosity(self, temperature: float, salinity: float = 0.035) -> float:
        """
        Calculate water viscosity based on temperature and salinity.
        
        Args:
            temperature: Water temperature (K)
            salinity: Water salinity (kg/kg)
            
        Returns:
            Water viscosity (Pa·s)
        """
        try:
            # Reference conditions
            ref_temperature = 273.15  # K (0°C)
            ref_viscosity = self.config.water_viscosity_standard
            
            # Temperature effect (simplified exponential model)
            temp_factor = math.exp(-0.02 * (temperature - ref_temperature))
            
            # Salinity effect (increases viscosity)
            salinity_factor = 1.0 + 0.1 * salinity
            
            # Combined effect
            viscosity = ref_viscosity * temp_factor * salinity_factor
            
            return viscosity
            
        except Exception as e:
            self.logger.error("Error calculating water viscosity: %s", e)
            return self.config.water_viscosity_standard
    
    def calculate_air_density(self, temperature: float, pressure: float, humidity: float) -> float:
        """
        Calculate air density based on temperature, pressure, and humidity.
        
        Args:
            temperature: Air temperature (K)
            pressure: Air pressure (Pa)
            humidity: Relative humidity (0.0 to 1.0)
            
        Returns:
            Air density (kg/m³)
        """
        try:
            # Dry air density (ideal gas law)
            dry_air_density = pressure / (self.gas_constant * temperature)
            
            # Water vapor density
            saturation_pressure = self._calculate_saturation_pressure(temperature)
            water_vapor_pressure = humidity * saturation_pressure
            water_vapor_density = water_vapor_pressure / (self.water_vapor_constant * temperature)
            
            # Total air density (dry air + water vapor)
            total_density = dry_air_density + water_vapor_density
            
            return total_density
            
        except Exception as e:
            self.logger.error("Error calculating air density: %s", e)
            return self.config.air_density_standard
    
    def _calculate_saturation_pressure(self, temperature: float) -> float:
        """
        Calculate saturation vapor pressure.
        
        Args:
            temperature: Temperature (K)
            
        Returns:
            Saturation vapor pressure (Pa)
        """
        try:
            # Simplified Antoine equation
            # log₁₀(P) = A - B/(C + T)
            # where T is in Celsius
            temp_celsius = temperature - 273.15
            
            if temp_celsius > 0:
                # For water above 0°C
                A, B, C = 8.07131, 1730.63, 233.426
            else:
                # For ice below 0°C
                A, B, C = 9.09685, 1838.675, 233.426
            
            log_pressure = A - B / (C + temp_celsius)
            pressure = 10 ** log_pressure * 133.322  # Convert mmHg to Pa
            
            return pressure
            
        except Exception as e:
            self.logger.error("Error calculating saturation pressure: %s", e)
            return 2337.0  # Pa (saturation pressure at 20°C)
    
    def calculate_hydrostatic_pressure(self, depth: float, water_density: float) -> float:
        """
        Calculate hydrostatic pressure at given depth.
        
        Args:
            depth: Water depth (m)
            water_density: Water density (kg/m³)
            
        Returns:
            Hydrostatic pressure (Pa)
        """
        try:
            # Hydrostatic pressure: P = ρ × g × h
            gravity = self.calculate_gravity_at_altitude(self.environment_state.altitude)
            pressure = water_density * gravity * depth
            
            # Add atmospheric pressure
            atmospheric_pressure = self.calculate_atmospheric_pressure(self.environment_state.altitude)
            total_pressure = atmospheric_pressure + pressure
            
            return total_pressure
            
        except Exception as e:
            self.logger.error("Error calculating hydrostatic pressure: %s", e)
            return self.config.sea_level_pressure
    
    def calculate_wind_effects(self, wind_speed: float, surface_area: float) -> Dict[str, float]:
        """
        Calculate wind effects on the system.
        
        Args:
            wind_speed: Wind speed (m/s)
            surface_area: Exposed surface area (m²)
            
        Returns:
            Dictionary of wind effects
        """
        try:
            # Air density at current conditions
            air_density = self.calculate_air_density(
                self.environment_state.temperature,
                self.environment_state.pressure,
                self.environment_state.humidity
            )
            
            # Wind force: F = 0.5 × ρ × C_d × A × v²
            drag_coefficient = 1.0  # Simplified
            wind_force = 0.5 * air_density * drag_coefficient * surface_area * wind_speed ** 2
            
            # Wind power: P = 0.5 × ρ × A × v³
            wind_power = 0.5 * air_density * surface_area * wind_speed ** 3
            
            # Cooling effect (simplified)
            heat_transfer_coefficient = 25.0  # W/m²·K
            temperature_difference = 10.0  # K (assumed)
            cooling_power = heat_transfer_coefficient * surface_area * temperature_difference * (wind_speed / 5.0)
            
            return {
                'wind_force': wind_force,
                'wind_power': wind_power,
                'cooling_power': cooling_power,
                'air_density': air_density
            }
            
        except Exception as e:
            self.logger.error("Error calculating wind effects: %s", e)
            return {
                'wind_force': 0.0,
                'wind_power': 0.0,
                'cooling_power': 0.0,
                'air_density': self.config.air_density_standard
            }
    
    def calculate_weather_effects(self, weather_condition: WeatherCondition) -> Dict[str, float]:
        """
        Calculate weather effects on the system.
        
        Args:
            weather_condition: Current weather condition
            
        Returns:
            Dictionary of weather effects
        """
        try:
            effects = {
                'visibility_reduction': 0.0,
                'temperature_modification': 0.0,
                'humidity_modification': 0.0,
                'wind_modification': 0.0
            }
            
            if weather_condition == WeatherCondition.CLOUDY:
                effects['visibility_reduction'] = 0.3
                effects['temperature_modification'] = -2.0  # K
                effects['humidity_modification'] = 0.1
                
            elif weather_condition == WeatherCondition.RAINY:
                effects['visibility_reduction'] = 0.7
                effects['temperature_modification'] = -3.0  # K
                effects['humidity_modification'] = 0.3
                effects['wind_modification'] = 2.0  # m/s
                
            elif weather_condition == WeatherCondition.WINDY:
                effects['wind_modification'] = 5.0  # m/s
                effects['temperature_modification'] = -1.0  # K
                
            elif weather_condition == WeatherCondition.STORMY:
                effects['visibility_reduction'] = 0.9
                effects['temperature_modification'] = -5.0  # K
                effects['humidity_modification'] = 0.4
                effects['wind_modification'] = 10.0  # m/s
            
            return effects
            
        except Exception as e:
            self.logger.error("Error calculating weather effects: %s", e)
            return {
                'visibility_reduction': 0.0,
                'temperature_modification': 0.0,
                'humidity_modification': 0.0,
                'wind_modification': 0.0
            }
    
    def update_environment_state(self, temperature: Optional[float] = None,
                               pressure: Optional[float] = None,
                               humidity: Optional[float] = None,
                               altitude: Optional[float] = None,
                               water_temperature: Optional[float] = None,
                               water_depth: Optional[float] = None,
                               wind_speed: Optional[float] = None,
                               weather_condition: Optional[WeatherCondition] = None) -> None:
        """
        Update environment state with new conditions.
        
        Args:
            temperature: Air temperature (K)
            pressure: Air pressure (Pa)
            humidity: Relative humidity (0.0 to 1.0)
            altitude: Altitude above sea level (m)
            water_temperature: Water temperature (K)
            water_depth: Water depth (m)
            wind_speed: Wind speed (m/s)
            weather_condition: Weather condition
        """
        try:
            # Update provided parameters
            if temperature is not None:
                self.environment_state.temperature = temperature
            if pressure is not None:
                self.environment_state.pressure = pressure
            if humidity is not None:
                self.environment_state.humidity = humidity
            if altitude is not None:
                self.environment_state.altitude = altitude
            if water_temperature is not None:
                self.environment_state.water_temperature = water_temperature
            if water_depth is not None:
                self.environment_state.water_depth = water_depth
            if wind_speed is not None:
                self.environment_state.wind_speed = wind_speed
            if weather_condition is not None:
                self.environment_state.weather_condition = weather_condition
            
            # Calculate derived parameters if altitude changed
            if altitude is not None:
                self.environment_state.pressure = self.calculate_atmospheric_pressure(altitude)
                self.environment_state.temperature = self.calculate_atmospheric_temperature(altitude)
            
            # Apply weather effects
            weather_effects = self.calculate_weather_effects(self.environment_state.weather_condition)
            self.environment_state.temperature += weather_effects['temperature_modification']
            self.environment_state.humidity += weather_effects['humidity_modification']
            self.environment_state.wind_speed += weather_effects['wind_modification']
            
            # Update performance metrics
            self._update_performance_metrics()
            
            # Record environment state
            self._record_environment_state()
            
        except Exception as e:
            self.logger.error("Error updating environment state: %s", e)
    
    def _update_performance_metrics(self) -> None:
        """Update performance metrics."""
        try:
            # Calculate variations from standard conditions
            temp_variation = abs(self.environment_state.temperature - self.config.sea_level_temperature)
            pressure_variation = abs(self.environment_state.pressure - self.config.sea_level_pressure)
            
            self.performance_metrics['temperature_variations'] = temp_variation
            self.performance_metrics['pressure_variations'] = pressure_variation
            self.performance_metrics['humidity_effects'] = self.environment_state.humidity
            self.performance_metrics['altitude_effects'] = self.environment_state.altitude
            self.performance_metrics['weather_impact'] = 1.0 if self.environment_state.weather_condition != WeatherCondition.CLEAR else 0.0
            
        except Exception as e:
            self.logger.error("Error updating performance metrics: %s", e)
    
    def _record_environment_state(self) -> None:
        """Record environment state in history."""
        try:
            state_record = {
                'timestamp': time.time(),
                'temperature': self.environment_state.temperature,
                'pressure': self.environment_state.pressure,
                'humidity': self.environment_state.humidity,
                'altitude': self.environment_state.altitude,
                'water_temperature': self.environment_state.water_temperature,
                'water_depth': self.environment_state.water_depth,
                'wind_speed': self.environment_state.wind_speed,
                'weather_condition': self.environment_state.weather_condition.value,
                'environment_type': self.environment_state.environment_type.value
            }
            
            self.environment_history.append(state_record)
            
        except Exception as e:
            self.logger.error("Error recording environment state: %s", e)
    
    def get_environment_state(self) -> EnvironmentState:
        """
        Get current environment state.
        
        Returns:
            Current environment state
        """
        return self.environment_state
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Get performance metrics.
        
        Returns:
            Performance metrics dictionary
        """
        return self.performance_metrics.copy()
    
    def get_environment_history(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get environment history.
        
        Args:
            limit: Maximum number of records to return
            
        Returns:
            List of environment records
        """
        if limit is None:
            return self.environment_history.copy()
        else:
            return self.environment_history[-limit:]
    
    def get_water_properties(self) -> Dict[str, float]:
        """
        Get current water properties.
        
        Returns:
            Dictionary of water properties
        """
        try:
            water_density = self.calculate_water_density(
                self.environment_state.water_temperature,
                self.calculate_hydrostatic_pressure(self.environment_state.water_depth, 1000.0)
            )
            
            water_viscosity = self.calculate_water_viscosity(self.environment_state.water_temperature)
            
            return {
                'density': water_density,
                'viscosity': water_viscosity,
                'temperature': self.environment_state.water_temperature,
                'depth': self.environment_state.water_depth,
                'pressure': self.calculate_hydrostatic_pressure(self.environment_state.water_depth, water_density)
            }
            
        except Exception as e:
            self.logger.error("Error getting water properties: %s", e)
            return {
                'density': self.config.water_density_standard,
                'viscosity': self.config.water_viscosity_standard,
                'temperature': self.environment_state.water_temperature,
                'depth': self.environment_state.water_depth,
                'pressure': self.config.sea_level_pressure
            }
    
    def update(self, dt: float, temperature: Optional[float] = None, pressure: Optional[float] = None,
               humidity: Optional[float] = None, altitude: Optional[float] = None,
               water_temperature: Optional[float] = None, water_depth: Optional[float] = None,
               wind_speed: Optional[float] = None, weather_condition: Optional[WeatherCondition] = None) -> Dict[str, Any]:
        """
        Update environment state and properties.
        
        Args:
            dt: Time step in seconds
            temperature: Atmospheric temperature (K)
            pressure: Atmospheric pressure (Pa)
            humidity: Relative humidity (0.0 to 1.0)
            altitude: Altitude above sea level (m)
            water_temperature: Water temperature (K)
            water_depth: Water depth (m)
            wind_speed: Wind speed (m/s)
            weather_condition: Weather condition
            
        Returns:
            Updated state dictionary
        """
        try:
            # Update environment state
            self.update_environment_state(
                temperature=temperature,
                pressure=pressure,
                humidity=humidity,
                altitude=altitude,
                water_temperature=water_temperature,
                water_depth=water_depth,
                wind_speed=wind_speed,
                weather_condition=weather_condition
            )
            
            # Record environment state
            self._record_environment_state()
            
            # Update performance metrics
            self._update_performance_metrics()
            
            return self.get_state()
            
        except Exception as e:
            self.logger.error(f"Environment update error: {e}")
            return self.get_state()
    
    def get_state(self) -> Dict[str, Any]:
        """Get current environment system state."""
        return {
            'environment_state': {
                'temperature': self.environment_state.temperature,
                'pressure': self.environment_state.pressure,
                'humidity': self.environment_state.humidity,
                'altitude': self.environment_state.altitude,
                'water_temperature': self.environment_state.water_temperature,
                'water_depth': self.environment_state.water_depth,
                'wind_speed': self.environment_state.wind_speed,
                'weather_condition': self.environment_state.weather_condition.value,
                'environment_type': self.environment_state.environment_type.value
            },
            'performance_metrics': self.performance_metrics.copy(),
            'environment_history_count': len(self.environment_history),
            'water_properties': self.get_water_properties()
        }
    
    def reset(self) -> None:
        """Reset environment system to initial state."""
        self.environment_state = EnvironmentState()
        self.environment_history.clear()
        self.performance_metrics = {
            'temperature_variations': 0.0,
            'pressure_variations': 0.0,
            'humidity_effects': 0.0,
            'altitude_effects': 0.0,
            'weather_impact': 0.0
        }
        self.logger.info("Environment system reset")

# Alias for compatibility
Environment = EnvironmentSystem

