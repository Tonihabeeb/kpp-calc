import math
import logging
import time
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

"""
Thermal Model for KPP System
Comprehensive thermal dynamics modeling including heat generation, transfer,
     and effects on efficiency.
"""

class HeatTransferMode(str, Enum):
    """Heat transfer mode enumeration"""
    CONDUCTION = "conduction"
    CONVECTION = "convection"
    RADIATION = "radiation"
    COMBINED = "combined"

@dataclass
class ThermalProperties:
    """Thermal properties data structure"""
    temperature: float = 293.15  # K (20°C)
    density: float = 1000.0  # kg/m³
    specific_heat: float = 4186.0  # J/kg·K
    thermal_conductivity: float = 0.6  # W/m·K
    thermal_expansion: float = 2.1e-4  # 1/K
    viscosity: float = 1.002e-3  # Pa·s

@dataclass
class HeatTransferResult:
    """Heat transfer calculation result"""
    mode: HeatTransferMode
    heat_transfer_rate: float = 0.0  # W
    heat_transfer_coefficient: float = 0.0  # W/m²·K
    temperature_change: float = 0.0  # K
    efficiency_impact: float = 0.0

@dataclass
class ThermalState:
    """Thermal state data structure"""
    water_temperature: float = 293.15  # K
    air_temperature: float = 293.15  # K
    component_temperatures: Dict[str, float] = None
    heat_generation_rate: float = 0.0  # W
    heat_transfer_rate: float = 0.0  # W
    thermal_efficiency: float = 1.0
    
    def __post_init__(self):
        if self.component_temperatures is None:
            self.component_temperatures = {}

class ThermalPhysics:
    """
    Comprehensive thermal physics model for KPP simulation.
    Handles heat transfer, temperature effects, and thermal efficiency.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the thermal physics model.
        
        Args:
            config: Configuration dictionary for thermal modeling
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # Physics constants
        self.stefan_boltzmann = 5.67e-8  # W/m²·K⁴
        self.gravity = 9.81  # m/s²
        
        # Thermal tracking
        self.thermal_history: List[ThermalState] = []
        self.total_heat_generated = 0.0
        self.total_heat_transferred = 0.0
        
        # Performance metrics
        self.performance_metrics = {
            'average_efficiency': 0.0,
            'peak_efficiency': 0.0,
            'thermal_losses': 0.0,
            'heat_recovery': 0.0,
            'temperature_stability': 0.0
        }
        
        # Material properties
        self.water_properties = ThermalProperties(
            temperature=293.15,
            density=1000.0,
            specific_heat=4186.0,
            thermal_conductivity=0.6,
            thermal_expansion=2.1e-4,
            viscosity=1.002e-3
        )
        
        self.air_properties = ThermalProperties(
            temperature=293.15,
            density=1.225,
            specific_heat=1005.0,
            thermal_conductivity=0.024,
            thermal_expansion=3.4e-3,
            viscosity=1.81e-5
        )
        
        # Heat transfer coefficients
        self.convection_coefficient_water = self.config.get('convection_coefficient_water', 500.0)  # W/m²·K
        self.convection_coefficient_air = self.config.get('convection_coefficient_air', 25.0)  # W/m²·K
        self.radiation_emissivity = self.config.get('radiation_emissivity', 0.9)
        
        # Thermal optimization
        self.thermal_optimization_enabled = True
        self.target_temperature = 293.15  # K
        self.temperature_tolerance = 5.0  # K
        
        self.logger.info("Thermal physics model initialized")
    
    def calculate_temperature_dependent_properties(self, material: str, 
                                                 temperature: float) -> ThermalProperties:
        """
        Calculate temperature-dependent material properties.
        
        Args:
            material: Material type ('water' or 'air')
            temperature: Temperature (K)
            
        Returns:
            Updated thermal properties
        """
        try:
            if material.lower() == 'water':
                # Water properties as function of temperature
                # Density: ρ = ρ₀[1 - α(T - T₀)]
                base_density = 1000.0
                thermal_expansion = 2.1e-4
                ref_temperature = 293.15
                density = base_density * (1 - thermal_expansion * (temperature - ref_temperature))
                
                # Specific heat: approximately constant for water
                specific_heat = 4186.0
                
                # Thermal conductivity: k = k₀ + β(T - T₀)
                base_conductivity = 0.6
                conductivity_coefficient = 0.001
                thermal_conductivity = base_conductivity + conductivity_coefficient * (temperature - ref_temperature)
                
                # Viscosity: μ = μ₀ * exp(α/T)
                base_viscosity = 1.002e-3
                viscosity_coefficient = 2000.0
                viscosity = base_viscosity * math.exp(viscosity_coefficient / temperature)
                
                return ThermalProperties(
                    temperature=temperature,
                    density=density,
                    specific_heat=specific_heat,
                    thermal_conductivity=thermal_conductivity,
                    thermal_expansion=thermal_expansion,
                    viscosity=viscosity
                )
                
            elif material.lower() == 'air':
                # Air properties as function of temperature
                # Density: ρ = P/(R*T) (ideal gas law)
                pressure = 101325.0  # Pa
                gas_constant = 287.0  # J/kg·K
                density = pressure / (gas_constant * temperature)
                
                # Specific heat: approximately constant for air
                specific_heat = 1005.0
                
                # Thermal conductivity: k = k₀ * (T/T₀)^0.8
                base_conductivity = 0.024
                ref_temperature = 273.15
                thermal_conductivity = base_conductivity * (temperature / ref_temperature) ** 0.8
                
                # Viscosity: μ = μ₀ * (T/T₀)^0.7
                base_viscosity = 1.81e-5
                viscosity = base_viscosity * (temperature / ref_temperature) ** 0.7
                
                return ThermalProperties(
                    temperature=temperature,
                    density=density,
                    specific_heat=specific_heat,
                    thermal_conductivity=thermal_conductivity,
                    thermal_expansion=3.4e-3,
                    viscosity=viscosity
                )
            else:
                raise ValueError(f"Unknown material: {material}")
                
        except Exception as e:
            self.logger.error("Error calculating temperature-dependent properties: %s", e)
            return ThermalProperties(temperature=temperature)
    
    def calculate_conduction_heat_transfer(self, thermal_conductivity: float,
                                         area: float, thickness: float,
                                         temperature_difference: float) -> HeatTransferResult:
        """
        Calculate conduction heat transfer.
        
        Args:
            thermal_conductivity: Thermal conductivity (W/m·K)
            area: Cross-sectional area (m²)
            thickness: Material thickness (m)
            temperature_difference: Temperature difference (K)
            
        Returns:
            Heat transfer result
        """
        try:
            # Conduction: Q = k * A * ΔT / L
            heat_transfer_rate = thermal_conductivity * area * temperature_difference / thickness
            
            # Heat transfer coefficient: h = k / L
            heat_transfer_coefficient = thermal_conductivity / thickness
            
            # Temperature change (simplified)
            temperature_change = temperature_difference * 0.1  # 10% of difference
            
            return HeatTransferResult(
                mode=HeatTransferMode.CONDUCTION,
                heat_transfer_rate=heat_transfer_rate,
                heat_transfer_coefficient=heat_transfer_coefficient,
                temperature_change=temperature_change,
                efficiency_impact=0.0
            )
            
        except Exception as e:
            self.logger.error("Error calculating conduction heat transfer: %s", e)
            return HeatTransferResult(mode=HeatTransferMode.CONDUCTION)
    
    def calculate_convection_heat_transfer(self, heat_transfer_coefficient: float,
                                         area: float, temperature_difference: float) -> HeatTransferResult:
        """
        Calculate convection heat transfer.
        
        Args:
            heat_transfer_coefficient: Convection coefficient (W/m²·K)
            area: Surface area (m²)
            temperature_difference: Temperature difference (K)
            
        Returns:
            Heat transfer result
        """
        try:
            # Convection: Q = h * A * ΔT
            heat_transfer_rate = heat_transfer_coefficient * area * temperature_difference
            
            # Temperature change (simplified)
            temperature_change = temperature_difference * 0.2  # 20% of difference
            
            # Efficiency impact (simplified)
            efficiency_impact = -0.01 * abs(temperature_difference) / 100.0  # 1% per 100K
            
            return HeatTransferResult(
                mode=HeatTransferMode.CONVECTION,
                heat_transfer_rate=heat_transfer_rate,
                heat_transfer_coefficient=heat_transfer_coefficient,
                temperature_change=temperature_change,
                efficiency_impact=efficiency_impact
            )
            
        except Exception as e:
            self.logger.error("Error calculating convection heat transfer: %s", e)
            return HeatTransferResult(mode=HeatTransferMode.CONVECTION)
    
    def calculate_radiation_heat_transfer(self, emissivity: float, area: float,
                                        temperature1: float, temperature2: float) -> HeatTransferResult:
        """
        Calculate radiation heat transfer.
        
        Args:
            emissivity: Surface emissivity
            area: Surface area (m²)
            temperature1: Surface temperature (K)
            temperature2: Ambient temperature (K)
            
        Returns:
            Heat transfer result
        """
        try:
            # Radiation: Q = ε * σ * A * (T₁⁴ - T₂⁴)
            heat_transfer_rate = (emissivity * self.stefan_boltzmann * area * 
                                (temperature1 ** 4 - temperature2 ** 4))
            
            # Heat transfer coefficient (simplified)
            heat_transfer_coefficient = emissivity * self.stefan_boltzmann * (temperature1 + temperature2) / 2
            
            # Temperature change (simplified)
            temperature_change = (temperature1 - temperature2) * 0.05  # 5% of difference
            
            return HeatTransferResult(
                mode=HeatTransferMode.RADIATION,
                heat_transfer_rate=heat_transfer_rate,
                heat_transfer_coefficient=heat_transfer_coefficient,
                temperature_change=temperature_change,
                efficiency_impact=0.0
            )
            
        except Exception as e:
            self.logger.error("Error calculating radiation heat transfer: %s", e)
            return HeatTransferResult(mode=HeatTransferMode.RADIATION)
    
    def calculate_air_water_heat_exchange(self, water_temperature: float, air_temperature: float,
                                        surface_area: float, flow_rate: float = 0.1) -> HeatTransferResult:
        """
        Calculate air-water heat exchange.
        
        Args:
            water_temperature: Water temperature (K)
            air_temperature: Air temperature (K)
            surface_area: Heat exchange surface area (m²)
            flow_rate: Flow rate (m³/s)
            
        Returns:
            Heat transfer result
        """
        try:
            # Get temperature-dependent properties
            water_props = self.calculate_temperature_dependent_properties('water', water_temperature)
            air_props = self.calculate_temperature_dependent_properties('air', air_temperature)
            
            # Calculate temperature difference
            temperature_difference = water_temperature - air_temperature
            
            # Use convection heat transfer
            # Combined heat transfer coefficient
            combined_coefficient = (self.convection_coefficient_water + self.convection_coefficient_air) / 2
            
            # Heat transfer rate
            heat_transfer_rate = combined_coefficient * surface_area * temperature_difference
            
            # Temperature change
            temperature_change = temperature_difference * 0.15  # 15% of difference
            
            # Efficiency impact
            efficiency_impact = -0.005 * abs(temperature_difference) / 50.0  # 0.5% per 50K
            
            return HeatTransferResult(
                mode=HeatTransferMode.CONVECTION,
                heat_transfer_rate=heat_transfer_rate,
                heat_transfer_coefficient=combined_coefficient,
                temperature_change=temperature_change,
                efficiency_impact=efficiency_impact
            )
            
        except Exception as e:
            self.logger.error("Error calculating air-water heat exchange: %s", e)
            return HeatTransferResult(mode=HeatTransferMode.CONVECTION)
    
    def calculate_compressor_thermal_effects(self, compression_work: float,
                                           initial_temperature: float,
                                           compression_ratio: float = 2.0) -> HeatTransferResult:
        """
        Calculate compressor thermal effects.
        
        Args:
            compression_work: Compression work (J)
            initial_temperature: Initial temperature (K)
            compression_ratio: Compression ratio
            
        Returns:
            Heat transfer result
        """
        try:
            # Adiabatic compression temperature rise
            # T₂ = T₁ * (P₂/P₁)^((γ-1)/γ)
            gamma = 1.4  # Specific heat ratio for air
            final_temperature = initial_temperature * (compression_ratio ** ((gamma - 1) / gamma))
            
            # Heat generation from compression
            heat_generation = compression_work * 0.1  # 10% of work becomes heat
            
            # Temperature rise
            temperature_rise = final_temperature - initial_temperature
            
            # Efficiency impact
            efficiency_impact = -0.02 * temperature_rise / 100.0  # 2% per 100K rise
            
            return HeatTransferResult(
                mode=HeatTransferMode.COMBINED,
                heat_transfer_rate=heat_generation,
                heat_transfer_coefficient=0.0,
                temperature_change=temperature_rise,
                efficiency_impact=efficiency_impact
            )
            
        except Exception as e:
            self.logger.error("Error calculating compressor thermal effects: %s", e)
            return HeatTransferResult(mode=HeatTransferMode.COMBINED)
    
    def calculate_thermal_buoyancy(self, water_temperature: float, air_temperature: float,
                                 volume: float) -> float:
        """
        Calculate thermal buoyancy enhancement.
        
        Args:
            water_temperature: Water temperature (K)
            air_temperature: Air temperature (K)
            volume: Air volume (m³)
            
        Returns:
            Buoyancy enhancement factor
        """
        try:
            # Get temperature-dependent densities
            water_props = self.calculate_temperature_dependent_properties('water', water_temperature)
            air_props = self.calculate_temperature_dependent_properties('air', air_temperature)
            
            # Calculate density difference
            density_difference = water_props.density - air_props.density
            
            # Buoyancy force: F_b = ρ_water * V * g
            buoyancy_force = water_props.density * volume * self.gravity
            
            # Thermal enhancement factor
            # Warmer water = lower density = reduced buoyancy
            # Warmer air = lower density = increased buoyancy
            thermal_factor = 1.0 + 0.001 * (air_temperature - water_temperature) / 100.0
            
            return buoyancy_force * thermal_factor
            
        except Exception as e:
            self.logger.error("Error calculating thermal buoyancy: %s", e)
            return 0.0
    
    def calculate_thermal_efficiency(self, thermal_state: ThermalState) -> float:
        """
        Calculate thermal efficiency.
        
        Args:
            thermal_state: Current thermal state
            
        Returns:
            Thermal efficiency (0.0 to 1.0)
        """
        try:
            # Base efficiency
            base_efficiency = 1.0
            
            # Temperature stability penalty
            temperature_variance = abs(thermal_state.water_temperature - self.target_temperature)
            if temperature_variance > self.temperature_tolerance:
                stability_penalty = 0.05 * (temperature_variance - self.temperature_tolerance) / 10.0
                base_efficiency -= stability_penalty
            
            # Heat recovery bonus
            if thermal_state.heat_transfer_rate > 0:
                recovery_bonus = 0.02 * min(thermal_state.heat_transfer_rate / 1000.0, 1.0)
                base_efficiency += recovery_bonus
            
            # Component temperature penalties
            for component, temperature in thermal_state.component_temperatures.items():
                if temperature > 350.0:  # 77°C
                    temp_penalty = 0.01 * (temperature - 350.0) / 50.0
                    base_efficiency -= temp_penalty
            
            # Ensure efficiency is within bounds
            thermal_efficiency = max(0.0, min(1.0, base_efficiency))
            
            return thermal_efficiency
            
        except Exception as e:
            self.logger.error("Error calculating thermal efficiency: %s", e)
            return 1.0
    
    def update_thermal_state(self, thermal_state: ThermalState, 
                           heat_generation: float, time_step: float) -> ThermalState:
        """
        Update thermal state based on heat generation and transfer.
        
        Args:
            thermal_state: Current thermal state
            heat_generation: Heat generation rate (W)
            time_step: Time step (s)
            
        Returns:
            Updated thermal state
        """
        try:
            # Update heat generation
            thermal_state.heat_generation_rate = heat_generation
            
            # Calculate heat transfer
            if thermal_state.component_temperatures:
                total_heat_transfer = 0.0
                for component, temperature in thermal_state.component_temperatures.items():
                    # Calculate heat transfer to environment
                    ambient_temp = 293.15  # K
                    surface_area = 0.1  # m² (estimated)
                    
                    heat_transfer = self.calculate_convection_heat_transfer(
                        self.convection_coefficient_air, surface_area, temperature - ambient_temp
                    )
                    total_heat_transfer += heat_transfer.heat_transfer_rate
                
                thermal_state.heat_transfer_rate = total_heat_transfer
            
            # Update temperatures (simplified)
            heat_capacity = 1000.0  # J/K (estimated)
            temperature_change = (heat_generation - thermal_state.heat_transfer_rate) * time_step / heat_capacity
            
            thermal_state.water_temperature += temperature_change * 0.1  # 10% affects water
            thermal_state.air_temperature += temperature_change * 0.9   # 90% affects air
            
            # Update component temperatures
            if thermal_state.component_temperatures:
                for component in thermal_state.component_temperatures:
                    thermal_state.component_temperatures[component] += temperature_change * 0.5
            
            # Calculate thermal efficiency
            thermal_state.thermal_efficiency = self.calculate_thermal_efficiency(thermal_state)
            
            # Update tracking
            self.total_heat_generated += heat_generation * time_step
            self.total_heat_transferred += thermal_state.heat_transfer_rate * time_step
            self.thermal_history.append(ThermalState(
                water_temperature=thermal_state.water_temperature,
                air_temperature=thermal_state.air_temperature,
                component_temperatures=thermal_state.component_temperatures.copy() if thermal_state.component_temperatures else {},
                heat_generation_rate=thermal_state.heat_generation_rate,
                heat_transfer_rate=thermal_state.heat_transfer_rate,
                thermal_efficiency=thermal_state.thermal_efficiency
            ))
            
            # Update performance metrics
            self._update_performance_metrics(thermal_state)
            
            return thermal_state
            
        except Exception as e:
            self.logger.error("Error updating thermal state: %s", e)
            return thermal_state
    
    def _update_performance_metrics(self, thermal_state: ThermalState) -> None:
        """
        Update performance metrics with thermal state.
        
        Args:
            thermal_state: Thermal state to process
        """
        try:
            # Update average efficiency
            if len(self.thermal_history) > 0:
                avg_efficiency = sum(state.thermal_efficiency for state in self.thermal_history) / len(self.thermal_history)
                self.performance_metrics['average_efficiency'] = avg_efficiency
            
            # Update peak efficiency
            if thermal_state.thermal_efficiency > self.performance_metrics['peak_efficiency']:
                self.performance_metrics['peak_efficiency'] = thermal_state.thermal_efficiency
            
            # Update thermal losses
            self.performance_metrics['thermal_losses'] = thermal_state.heat_transfer_rate
            
            # Update heat recovery
            if thermal_state.heat_transfer_rate > 0:
                self.performance_metrics['heat_recovery'] += thermal_state.heat_transfer_rate * 0.01  # 1% recovery
            
            # Update temperature stability
            temp_variance = abs(thermal_state.water_temperature - self.target_temperature)
            self.performance_metrics['temperature_stability'] = 1.0 - (temp_variance / 100.0)
            
        except Exception as e:
            self.logger.error("Error updating performance metrics: %s", e)
    
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
        """Reset thermal physics state."""
        self.thermal_history.clear()
        self.total_heat_generated = 0.0
        self.total_heat_transferred = 0.0
        self.performance_metrics = {
            'average_efficiency': 0.0,
            'peak_efficiency': 0.0,
            'thermal_losses': 0.0,
            'heat_recovery': 0.0,
            'temperature_stability': 0.0
        }
        self.logger.info("Thermal physics model reset")

