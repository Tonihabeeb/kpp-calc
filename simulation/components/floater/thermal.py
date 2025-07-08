import math
import logging
import time
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from enum import Enum

"""
Thermal effects on floater physics.
Handles heat transfer, temperature effects, and thermal expansion.
"""

class HeatTransferMode(str, Enum):
    """Heat transfer mode enumeration"""
    CONDUCTION = "conduction"
    CONVECTION = "convection"
    RADIATION = "radiation"
    COMBINED = "combined"

@dataclass
class ThermalState:
    """Thermal state data structure"""
    temperature: float = 293.15  # K
    heat_capacity: float = 900.0  # J/kg·K
    thermal_conductivity: float = 50.0  # W/m·K
    thermal_expansion: float = 2.1e-4  # 1/K
    heat_generation_rate: float = 0.0  # W
    heat_transfer_rate: float = 0.0  # W
    thermal_efficiency: float = 1.0

@dataclass
class ThermalConfig:
    """Thermal model configuration"""
    initial_temperature: float = 293.15  # K
    ambient_temperature: float = 293.15  # K
    material_density: float = 2500.0  # kg/m³
    specific_heat: float = 900.0  # J/kg·K
    thermal_conductivity: float = 50.0  # W/m·K
    thermal_expansion: float = 2.1e-4  # 1/K
    convection_coefficient: float = 25.0  # W/m²·K
    radiation_emissivity: float = 0.9
    surface_area: float = 0.5  # m²

class ThermalModel:
    """
    Comprehensive thermal model for floater physics.
    Handles heat transfer, temperature effects, and thermal optimization.
    """
    
    def __init__(self, config: Optional[ThermalConfig] = None):
        """
        Initialize the thermal model.
        
        Args:
            config: Thermal model configuration
        """
        self.config = config or ThermalConfig()
        self.logger = logging.getLogger(__name__)
        
        # Physics constants
        self.stefan_boltzmann = 5.67e-8  # W/m²·K⁴
        
        # Thermal state
        self.thermal_state = ThermalState(
            temperature=self.config.initial_temperature,
            heat_capacity=self.config.specific_heat,
            thermal_conductivity=self.config.thermal_conductivity,
            thermal_expansion=self.config.thermal_expansion
        )
        
        # Performance tracking
        self.thermal_history: List[ThermalState] = []
        self.total_heat_generated = 0.0
        self.total_heat_transferred = 0.0
        
        # Performance metrics
        self.performance_metrics = {
            'average_temperature': 0.0,
            'temperature_variance': 0.0,
            'thermal_efficiency': 0.0,
            'heat_recovery_rate': 0.0,
            'cooling_efficiency': 0.0
        }
        
        self.logger.info("Thermal model initialized at %.1f K", self.config.initial_temperature)
    
    def calculate_heat_capacity(self, mass: float, specific_heat: Optional[float] = None) -> float:
        """
        Calculate heat capacity.
        
        Args:
            mass: Mass (kg)
            specific_heat: Specific heat capacity (J/kg·K)
            
        Returns:
            Heat capacity (J/K)
        """
        try:
            if specific_heat is None:
                specific_heat = self.config.specific_heat
            
            heat_capacity = mass * specific_heat
            return heat_capacity
            
        except Exception as e:
            self.logger.error("Error calculating heat capacity: %s", e)
            return 0.0
    
    def calculate_thermal_expansion(self, initial_length: float, temperature_change: float) -> float:
        """
        Calculate thermal expansion.
        
        Args:
            initial_length: Initial length (m)
            temperature_change: Temperature change (K)
            
        Returns:
            Length change (m)
        """
        try:
            # Linear thermal expansion: ΔL = α × L₀ × ΔT
            length_change = self.config.thermal_expansion * initial_length * temperature_change
            return length_change
            
        except Exception as e:
            self.logger.error("Error calculating thermal expansion: %s", e)
            return 0.0
    
    def calculate_volume_expansion(self, initial_volume: float, temperature_change: float) -> float:
        """
        Calculate volume expansion.
        
        Args:
            initial_volume: Initial volume (m³)
            temperature_change: Temperature change (K)
            
        Returns:
            Volume change (m³)
        """
        try:
            # Volumetric thermal expansion: ΔV = 3α × V₀ × ΔT
            volume_change = 3 * self.config.thermal_expansion * initial_volume * temperature_change
            return volume_change
            
        except Exception as e:
            self.logger.error("Error calculating volume expansion: %s", e)
            return 0.0
    
    def calculate_conduction_heat_transfer(self, temperature_difference: float,
                                         area: float, thickness: float) -> float:
        """
        Calculate conduction heat transfer.
        
        Args:
            temperature_difference: Temperature difference (K)
            area: Cross-sectional area (m²)
            thickness: Material thickness (m)
            
        Returns:
            Heat transfer rate (W)
        """
        try:
            # Conduction: Q = k × A × ΔT / L
            heat_transfer_rate = (self.config.thermal_conductivity * area * 
                                temperature_difference / thickness)
            return heat_transfer_rate
            
        except Exception as e:
            self.logger.error("Error calculating conduction heat transfer: %s", e)
            return 0.0
    
    def calculate_convection_heat_transfer(self, temperature_difference: float,
                                         area: Optional[float] = None) -> float:
        """
        Calculate convection heat transfer.
        
        Args:
            temperature_difference: Temperature difference (K)
            area: Surface area (m²)
            
        Returns:
            Heat transfer rate (W)
        """
        try:
            if area is None:
                area = self.config.surface_area
            
            # Convection: Q = h × A × ΔT
            heat_transfer_rate = self.config.convection_coefficient * area * temperature_difference
            return heat_transfer_rate
            
        except Exception as e:
            self.logger.error("Error calculating convection heat transfer: %s", e)
            return 0.0
    
    def calculate_radiation_heat_transfer(self, surface_temperature: float,
                                        ambient_temperature: float,
                                        area: Optional[float] = None) -> float:
        """
        Calculate radiation heat transfer.
        
        Args:
            surface_temperature: Surface temperature (K)
            ambient_temperature: Ambient temperature (K)
            area: Surface area (m²)
            
        Returns:
            Heat transfer rate (W)
        """
        try:
            if area is None:
                area = self.config.surface_area
            
            # Radiation: Q = ε × σ × A × (T₁⁴ - T₂⁴)
            heat_transfer_rate = (self.config.radiation_emissivity * self.stefan_boltzmann * 
                                area * (surface_temperature ** 4 - ambient_temperature ** 4))
            return heat_transfer_rate
            
        except Exception as e:
            self.logger.error("Error calculating radiation heat transfer: %s", e)
            return 0.0
    
    def calculate_combined_heat_transfer(self, surface_temperature: float,
                                       ambient_temperature: float,
                                       area: Optional[float] = None) -> float:
        """
        Calculate combined heat transfer (convection + radiation).
        
        Args:
            surface_temperature: Surface temperature (K)
            ambient_temperature: Ambient temperature (K)
            area: Surface area (m²)
            
        Returns:
            Total heat transfer rate (W)
        """
        try:
            if area is None:
                area = self.config.surface_area
            
            temperature_difference = surface_temperature - ambient_temperature
            
            # Convection heat transfer
            convection_heat = self.calculate_convection_heat_transfer(temperature_difference, area)
            
            # Radiation heat transfer
            radiation_heat = self.calculate_radiation_heat_transfer(surface_temperature, ambient_temperature, area)
            
            # Combined heat transfer
            total_heat_transfer = convection_heat + radiation_heat
            
            return total_heat_transfer
            
        except Exception as e:
            self.logger.error("Error calculating combined heat transfer: %s", e)
            return 0.0
    
    def calculate_thermal_buoyancy(self, water_temperature: float, air_temperature: float,
                                 volume: float) -> float:
        """
        Calculate thermal buoyancy enhancement.
        
        Args:
            water_temperature: Water temperature (K)
            air_temperature: Air temperature (K)
            volume: Air volume (m³)
            
        Returns:
            Thermal buoyancy factor
        """
        try:
            # Reference temperature
            ref_temperature = 293.15  # K (20°C)
            
            # Water density change with temperature
            water_density = 1000.0 * (1.0 - 2.1e-4 * (water_temperature - ref_temperature))
            
            # Air density change with temperature (ideal gas law)
            air_density = 1.225 * (ref_temperature / air_temperature)
            
            # Buoyancy force: F_b = ρ_water × V × g
            gravity = 9.81  # m/s²
            buoyancy_force = water_density * volume * gravity
            
            # Thermal enhancement factor
            thermal_factor = 1.0 + 0.001 * (air_temperature - water_temperature) / 100.0
            
            return buoyancy_force * thermal_factor
            
        except Exception as e:
            self.logger.error("Error calculating thermal buoyancy: %s", e)
            return 0.0
    
    def update_temperature(self, heat_generation: float, time_step: float,
                         ambient_temperature: Optional[float] = None) -> float:
        """
        Update temperature based on heat generation and transfer.
        
        Args:
            heat_generation: Heat generation rate (W)
            time_step: Time step (s)
            ambient_temperature: Ambient temperature (K)
            
        Returns:
            New temperature (K)
        """
        try:
            if ambient_temperature is None:
                ambient_temperature = self.config.ambient_temperature
            
            # Calculate heat transfer to environment
            heat_transfer = self.calculate_combined_heat_transfer(
                self.thermal_state.temperature, ambient_temperature
            )
            
            # Net heat input
            net_heat = heat_generation - heat_transfer
            
            # Calculate temperature change
            # Q = m × c × ΔT, so ΔT = Q / (m × c)
            mass = 16.0  # kg (estimated floater mass)
            heat_capacity = self.calculate_heat_capacity(mass)
            
            if heat_capacity > 0:
                temperature_change = net_heat * time_step / heat_capacity
            else:
                temperature_change = 0.0
            
            # Update temperature
            new_temperature = self.thermal_state.temperature + temperature_change
            
            # Update thermal state
            self.thermal_state.temperature = new_temperature
            self.thermal_state.heat_generation_rate = heat_generation
            self.thermal_state.heat_transfer_rate = heat_transfer
            
            # Calculate thermal efficiency
            if heat_generation > 0:
                self.thermal_state.thermal_efficiency = heat_transfer / heat_generation
            else:
                self.thermal_state.thermal_efficiency = 1.0
            
            # Update tracking
            self.total_heat_generated += heat_generation * time_step
            self.total_heat_transferred += heat_transfer * time_step
            
            # Add to history
            self.thermal_history.append(ThermalState(
                temperature=new_temperature,
                heat_capacity=self.thermal_state.heat_capacity,
                thermal_conductivity=self.thermal_state.thermal_conductivity,
                thermal_expansion=self.thermal_state.thermal_expansion,
                heat_generation_rate=heat_generation,
                heat_transfer_rate=heat_transfer,
                thermal_efficiency=self.thermal_state.thermal_efficiency
            ))
            
            # Update performance metrics
            self._update_performance_metrics()
            
            return new_temperature
            
        except Exception as e:
            self.logger.error("Error updating temperature: %s", e)
            return self.thermal_state.temperature
    
    def calculate_thermal_stress(self, temperature_gradient: float,
                               material_properties: Dict[str, float]) -> float:
        """
        Calculate thermal stress.
        
        Args:
            temperature_gradient: Temperature gradient (K/m)
            material_properties: Material properties dictionary
            
        Returns:
            Thermal stress (Pa)
        """
        try:
            # Thermal stress: σ = E × α × ΔT
            youngs_modulus = material_properties.get('youngs_modulus', 200e9)  # Pa
            thermal_expansion = material_properties.get('thermal_expansion', 2.1e-4)  # 1/K
            
            # Simplified calculation
            thermal_stress = youngs_modulus * thermal_expansion * temperature_gradient
            
            return thermal_stress
            
        except Exception as e:
            self.logger.error("Error calculating thermal stress: %s", e)
            return 0.0
    
    def optimize_thermal_parameters(self, target_temperature: float,
                                  current_temperature: float) -> Dict[str, float]:
        """
        Optimize thermal parameters for target temperature.
        
        Args:
            target_temperature: Target temperature (K)
            current_temperature: Current temperature (K)
            
        Returns:
            Optimized parameters
        """
        try:
            temperature_difference = target_temperature - current_temperature
            
            # Calculate required heat transfer
            if temperature_difference > 0:
                # Heating required
                required_heat = temperature_difference * self.thermal_state.heat_capacity
                cooling_efficiency = 0.0
                heating_efficiency = 1.0
            else:
                # Cooling required
                required_heat = abs(temperature_difference) * self.thermal_state.heat_capacity
                cooling_efficiency = 1.0
                heating_efficiency = 0.0
            
            # Calculate optimal heat transfer coefficient
            optimal_convection_coefficient = required_heat / (self.config.surface_area * abs(temperature_difference))
            
            return {
                'required_heat': required_heat,
                'temperature_difference': temperature_difference,
                'optimal_convection_coefficient': optimal_convection_coefficient,
                'cooling_efficiency': cooling_efficiency,
                'heating_efficiency': heating_efficiency
            }
            
        except Exception as e:
            self.logger.error("Error optimizing thermal parameters: %s", e)
            return {}
    
    def _update_performance_metrics(self) -> None:
        """Update performance metrics."""
        try:
            if len(self.thermal_history) > 0:
                # Calculate average temperature
                temperatures = [state.temperature for state in self.thermal_history]
                self.performance_metrics['average_temperature'] = sum(temperatures) / len(temperatures)
                
                # Calculate temperature variance
                if len(temperatures) > 1:
                    mean_temp = self.performance_metrics['average_temperature']
                    variance = sum((t - mean_temp) ** 2 for t in temperatures) / (len(temperatures) - 1)
                    self.performance_metrics['temperature_variance'] = variance
                
                # Calculate thermal efficiency
                efficiencies = [state.thermal_efficiency for state in self.thermal_history]
                self.performance_metrics['thermal_efficiency'] = sum(efficiencies) / len(efficiencies)
                
                # Calculate heat recovery rate
                if self.total_heat_generated > 0:
                    self.performance_metrics['heat_recovery_rate'] = self.total_heat_transferred / self.total_heat_generated
                
                # Calculate cooling efficiency
                if len(self.thermal_history) >= 2:
                    recent_temp = self.thermal_history[-1].temperature
                    previous_temp = self.thermal_history[-2].temperature
                    if previous_temp > recent_temp:
                        self.performance_metrics['cooling_efficiency'] = 1.0
                    else:
                        self.performance_metrics['cooling_efficiency'] = 0.0
                        
        except Exception as e:
            self.logger.error("Error updating performance metrics: %s", e)
    
    def get_thermal_state(self) -> ThermalState:
        """
        Get current thermal state.
        
        Returns:
            Current thermal state
        """
        return self.thermal_state
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Get performance metrics.
        
        Returns:
            Performance metrics dictionary
        """
        return self.performance_metrics.copy()
    
    def get_thermal_history(self, limit: Optional[int] = None) -> List[ThermalState]:
        """
        Get thermal history.
        
        Args:
            limit: Maximum number of entries to return
            
        Returns:
            List of thermal states
        """
        if limit is None:
            return self.thermal_history.copy()
        else:
            return self.thermal_history[-limit:]
    
    def reset(self) -> None:
        """Reset thermal model state."""
        self.thermal_state = ThermalState(
            temperature=self.config.initial_temperature,
            heat_capacity=self.config.specific_heat,
            thermal_conductivity=self.config.thermal_conductivity,
            thermal_expansion=self.config.thermal_expansion
        )
        self.thermal_history.clear()
        self.total_heat_generated = 0.0
        self.total_heat_transferred = 0.0
        self.performance_metrics = {
            'average_temperature': 0.0,
            'temperature_variance': 0.0,
            'thermal_efficiency': 0.0,
            'heat_recovery_rate': 0.0,
            'cooling_efficiency': 0.0
        }
        self.logger.info("Thermal model reset")

