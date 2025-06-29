"""
Thermal Model for KPP System
Comprehensive thermal dynamics modeling including heat generation, transfer, and effects on efficiency.
"""

import logging
import math
from dataclasses import dataclass
from typing import Dict, List, Optional

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class ThermalState:
    """Thermal state for a component"""

    temperature: float = 20.0  # °C
    heat_generation: float = 0.0  # W
    heat_capacity: float = 1000.0  # J/kg·K
    mass: float = 100.0  # kg
    surface_area: float = 1.0  # m²
    thermal_conductivity: float = 50.0  # W/m·K


@dataclass
class ThermalProperties:
    """Thermal properties for different materials"""

    steel_conductivity: float = 50.0  # W/m·K
    aluminum_conductivity: float = 205.0  # W/m·K
    copper_conductivity: float = 400.0  # W/m·K
    air_conductivity: float = 0.026  # W/m·K
    oil_conductivity: float = 0.14  # W/m·K


class ThermalModel:
    """
    Comprehensive thermal model for the KPP drivetrain system.

    Models:
    - Heat generation from losses
    - Heat transfer via conduction, convection, and radiation
    - Temperature effects on material properties and efficiency
    - Thermal mass and time constants
    """

    def __init__(self, ambient_temperature: float = 20.0):
        """
        Initialize thermal model.

        Args:
            ambient_temperature: Ambient temperature in °C
        """
        self.ambient_temperature = ambient_temperature
        self.thermal_properties = ThermalProperties()

        # Component thermal states
        self.component_states = {}

        # Heat transfer coefficients
        self.convection_coefficient = 25.0  # W/m²·K (forced air cooling)
        self.radiation_coefficient = 5.0  # W/m²·K (radiation to ambient)
        self.conduction_coefficient = 100.0  # W/m²·K (internal conduction)

        # Thermal time constants
        self.thermal_time_constant = 300.0  # seconds (5 minutes)

        # Temperature tracking
        self.temperature_history = {}
        self.max_temperatures = {}

        logger.info(
            f"ThermalModel initialized with ambient temperature {ambient_temperature}°C"
        )

    def add_component(self, component_name: str, thermal_state: ThermalState):
        """Add a component to the thermal model"""
        self.component_states[component_name] = thermal_state
        self.temperature_history[component_name] = []
        self.max_temperatures[component_name] = thermal_state.temperature

        logger.debug(f"Added thermal component: {component_name}")

    def calculate_heat_generation(
        self, component_name: str, power_loss: float
    ) -> float:
        """
        Calculate heat generation from power losses.

        All power losses are converted to heat.
        """
        if component_name in self.component_states:
            self.component_states[component_name].heat_generation = power_loss

        return power_loss

    def calculate_convective_heat_transfer(self, component: ThermalState) -> float:
        """
        Calculate convective heat transfer to ambient air.

        Q = h * A * (T_surface - T_ambient)
        """
        temp_difference = component.temperature - self.ambient_temperature
        heat_transfer = (
            self.convection_coefficient * component.surface_area * temp_difference
        )

        return heat_transfer

    def calculate_radiative_heat_transfer(self, component: ThermalState) -> float:
        """
        Calculate radiative heat transfer to ambient.

        Simplified radiation model: Q = ε * σ * A * (T⁴ - T_amb⁴)
        Linearized for small temperature differences.
        """
        temp_difference = component.temperature - self.ambient_temperature
        heat_transfer = (
            self.radiation_coefficient * component.surface_area * temp_difference
        )

        return heat_transfer

    def calculate_conductive_heat_transfer(
        self,
        component1: ThermalState,
        component2: ThermalState,
        contact_area: float = 0.1,
    ) -> float:
        """
        Calculate conductive heat transfer between components.

        Q = k * A * (T1 - T2) / L
        """
        temp_difference = component1.temperature - component2.temperature
        # Assume 1cm conduction path length
        conduction_length = 0.01  # m

        heat_transfer = (
            self.thermal_properties.steel_conductivity
            * contact_area
            * temp_difference
            / conduction_length
        )

        return heat_transfer

    def update_component_temperature(self, component_name: str, dt: float):
        """
        Update component temperature based on heat generation and transfer.

        Uses lumped capacitance model: m*c*dT/dt = Q_gen - Q_loss
        """
        if component_name not in self.component_states:
            return

        component = self.component_states[component_name]

        # Heat generation (from losses)
        heat_generated = component.heat_generation

        # Heat losses
        convective_loss = self.calculate_convective_heat_transfer(component)
        radiative_loss = self.calculate_radiative_heat_transfer(component)

        # Net heat flow
        net_heat_flow = heat_generated - convective_loss - radiative_loss

        # Temperature change
        thermal_capacity = component.mass * component.heat_capacity
        temp_change = (net_heat_flow * dt) / thermal_capacity

        # Apply thermal time constant to prevent rapid temperature changes
        time_factor = dt / self.thermal_time_constant
        damped_temp_change = temp_change * min(1.0, time_factor)

        # Update temperature
        component.temperature += damped_temp_change

        # Ensure temperature doesn't go below ambient
        component.temperature = max(component.temperature, self.ambient_temperature)

        # Track maximum temperature
        self.max_temperatures[component_name] = max(
            self.max_temperatures[component_name], component.temperature
        )

        # Store temperature history
        self.temperature_history[component_name].append(component.temperature)

        # Limit history size
        if len(self.temperature_history[component_name]) > 1000:
            self.temperature_history[component_name] = self.temperature_history[
                component_name
            ][-1000:]

    def calculate_temperature_effects_on_efficiency(
        self, component_name: str, base_efficiency: float
    ) -> float:
        """
        Calculate how temperature affects component efficiency.

        Different components have different temperature sensitivity:
        - Mechanical components: efficiency decreases at high temperatures
        - Electrical components: efficiency decreases at high temperatures
        - Lubrication: viscosity changes affect efficiency
        """
        if component_name not in self.component_states:
            return base_efficiency

        temperature = self.component_states[component_name].temperature

        # Define optimal temperature ranges for different component types
        if "bearing" in component_name.lower():
            # Bearings work best at moderate temperatures (40-80°C)
            optimal_temp = 60.0
            temp_sensitivity = 0.002  # 0.2% per degree deviation
        elif "gear" in component_name.lower():
            # Gears work best at moderate temperatures (50-90°C)
            optimal_temp = 70.0
            temp_sensitivity = 0.001  # 0.1% per degree deviation
        elif "generator" in component_name.lower():
            # Electrical components prefer cooler operation (20-60°C)
            optimal_temp = 40.0
            temp_sensitivity = 0.003  # 0.3% per degree deviation
        elif "clutch" in component_name.lower():
            # Clutches can handle higher temperatures (60-120°C)
            optimal_temp = 90.0
            temp_sensitivity = 0.0015  # 0.15% per degree deviation
        else:
            # Default case
            optimal_temp = 50.0
            temp_sensitivity = 0.002

        # Calculate efficiency factor
        temp_deviation = abs(temperature - optimal_temp)
        efficiency_factor = 1.0 - (temp_sensitivity * temp_deviation)

        # Apply limits
        efficiency_factor = max(0.5, min(1.0, efficiency_factor))

        adjusted_efficiency = base_efficiency * efficiency_factor

        return adjusted_efficiency

    def calculate_thermal_expansion_effects(
        self, component_name: str
    ) -> Dict[str, float]:
        """
        Calculate thermal expansion effects on component clearances and fits.

        Thermal expansion can affect:
        - Bearing clearances
        - Gear mesh quality
        - Seal effectiveness
        """
        if component_name not in self.component_states:
            return {"expansion_factor": 1.0, "clearance_change": 0.0}

        temperature = self.component_states[component_name].temperature
        temp_rise = temperature - 20.0  # Reference temperature

        # Steel thermal expansion coefficient: ~12e-6 /°C
        expansion_coefficient = 12e-6

        # Calculate expansion factor
        expansion_factor = 1.0 + (expansion_coefficient * temp_rise)

        # Clearance change (assuming 0.1mm nominal clearance)
        nominal_clearance = 0.0001  # m
        clearance_change = nominal_clearance * expansion_coefficient * temp_rise

        return {
            "expansion_factor": expansion_factor,
            "clearance_change": clearance_change,
            "temp_rise": temp_rise,
        }

    def update_all_temperatures(self, heat_sources: Dict[str, float], dt: float):
        """
        Update temperatures for all components in the system.

        Args:
            heat_sources: Dictionary of heat generation rates (W) for each component
            dt: Time step (s)
        """
        # Update heat generation for all components
        for component_name, heat_rate in heat_sources.items():
            self.calculate_heat_generation(component_name, heat_rate)

        # Update temperatures
        for component_name in self.component_states.keys():
            self.update_component_temperature(component_name, dt)

    def get_system_thermal_state(self) -> Dict[str, Dict]:
        """Get comprehensive thermal state of the system"""
        thermal_state = {}

        for component_name, component in self.component_states.items():
            thermal_state[component_name] = {
                "temperature": component.temperature,
                "heat_generation": component.heat_generation,
                "max_temperature": self.max_temperatures[component_name],
                "temp_rise": component.temperature - self.ambient_temperature,
                "thermal_expansion": self.calculate_thermal_expansion_effects(
                    component_name
                ),
            }

        return thermal_state

    def check_thermal_limits(self) -> Dict[str, bool]:
        """Check if any components exceed thermal limits"""
        thermal_limits = {
            "bearing": 120.0,  # °C
            "gear": 130.0,  # °C
            "generator": 80.0,  # °C
            "clutch": 150.0,  # °C
            "default": 100.0,  # °C
        }

        limit_status = {}

        for component_name, component in self.component_states.items():
            # Determine component type and limit
            component_type = "default"
            for comp_type in thermal_limits.keys():
                if comp_type in component_name.lower():
                    component_type = comp_type
                    break

            limit = thermal_limits[component_type]
            over_limit = component.temperature > limit

            limit_status[component_name] = {
                "over_limit": over_limit,
                "temperature": component.temperature,
                "limit": limit,
                "margin": limit - component.temperature,
            }

        return limit_status

    def reset(self):
        """Reset thermal model state"""
        for component_name in self.component_states.keys():
            self.component_states[component_name].temperature = self.ambient_temperature
            self.component_states[component_name].heat_generation = 0.0
            self.temperature_history[component_name].clear()
            self.max_temperatures[component_name] = self.ambient_temperature

        logger.info("ThermalModel state reset")


def create_standard_kpp_thermal_model(ambient_temp: float = 20.0) -> ThermalModel:
    """
    Create standard KPP thermal model with typical component configurations.

    Args:
        ambient_temp: Ambient temperature in °C

    Returns:
        Configured ThermalModel
    """
    thermal_model = ThermalModel(ambient_temp)

    # Add typical KPP components
    components = {
        "sprocket_bearing": ThermalState(
            temperature=ambient_temp,
            heat_capacity=500.0,  # Steel bearing
            mass=5.0,  # 5 kg bearing
            surface_area=0.1,  # 0.1 m² surface area
            thermal_conductivity=50.0,
        ),
        "gearbox": ThermalState(
            temperature=ambient_temp,
            heat_capacity=500.0,  # Steel gears and housing
            mass=200.0,  # 200 kg gearbox
            surface_area=2.0,  # 2 m² surface area
            thermal_conductivity=50.0,
        ),
        "clutch": ThermalState(
            temperature=ambient_temp,
            heat_capacity=500.0,  # Steel and friction materials
            mass=50.0,  # 50 kg clutch
            surface_area=0.5,  # 0.5 m² surface area
            thermal_conductivity=50.0,
        ),
        "flywheel": ThermalState(
            temperature=ambient_temp,
            heat_capacity=500.0,  # Cast iron flywheel
            mass=500.0,  # 500 kg flywheel
            surface_area=3.0,  # 3 m² surface area
            thermal_conductivity=50.0,
        ),
        "generator": ThermalState(
            temperature=ambient_temp,
            heat_capacity=800.0,  # Copper and steel
            mass=300.0,  # 300 kg generator
            surface_area=4.0,  # 4 m² surface area
            thermal_conductivity=100.0,
        ),
    }

    for name, state in components.items():
        thermal_model.add_component(name, state)

    logger.info(f"Created standard KPP thermal model with {len(components)} components")

    return thermal_model
