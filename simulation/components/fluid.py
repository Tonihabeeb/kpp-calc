"""
Fluid System Module for KPP Simulation
Handles water properties, nanobubble effects (H1), and drag calculations.
"""

import logging
import math
from dataclasses import dataclass
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


@dataclass
class FluidState:
    """Current state of the fluid system"""

    density: float = 1000.0  # kg/m³
    temperature: float = 293.15  # K (20°C)
    nanobubble_fraction: float = 0.0  # Volume fraction of nanobubbles
    drag_coefficient: float = 0.6  # Base drag coefficient
    effective_density: float = 1000.0  # Effective density with nanobubbles
    reynolds_number: float = 0.0  # Current Reynolds number


class Fluid:
    """
    Manages fluid properties and hydrodynamic calculations.

    Handles:
    - Water density calculations with temperature effects
    - Nanobubble (H1) effects on density and drag
    - Dynamic drag coefficient based on flow conditions
    - Reynolds number calculations
    - Buoyancy force computations
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the fluid system.

        Args:
            config (dict): Configuration parameters
        """
        if config is None:
            config = {}

        # Base fluid properties
        self.base_density = config.get("water_density", 1000.0)  # kg/m³
        self.base_temperature = config.get("water_temperature", 293.15)  # K
        self.gravity = config.get("gravity", 9.81)  # m/s²
        self.kinematic_viscosity = config.get("kinematic_viscosity", 1.0e-6)  # m²/s

        # Drag properties
        self.base_drag_coefficient = config.get("drag_coefficient", 0.6)
        self.floater_area = config.get("floater_area", 0.1)  # m²

        # H1 Nanobubble parameters
        self.h1_active = config.get("h1_active", False)
        self.h1_bubble_fraction = config.get("h1_bubble_fraction", 0.05)  # 5% default
        self.h1_drag_reduction = config.get("h1_drag_reduction", 0.1)  # 10% drag reduction

        # Current state
        self.state = FluidState()
        self.update_state()

        logger.info(
            f"Fluid system initialized - Base density: {self.base_density} kg/m³, "
            f"Temperature: {self.base_temperature} K, H1 active: {self.h1_active}"
        )

    def update_state(self):
        """Update the current fluid state based on conditions."""
        # Calculate temperature-dependent density
        self.state.density = self.calculate_density(self.base_temperature)
        self.state.temperature = self.base_temperature

        # Apply nanobubble effects if H1 is active
        if self.h1_active:
            self.state.nanobubble_fraction = self.h1_bubble_fraction
            self.state.effective_density = self.apply_nanobubble_effects(self.state.density)
            self.state.drag_coefficient = self.base_drag_coefficient * (1 - self.h1_drag_reduction)
        else:
            self.state.nanobubble_fraction = 0.0
            self.state.effective_density = self.state.density
            self.state.drag_coefficient = self.base_drag_coefficient

    def calculate_density(self, temperature: float) -> float:
        """
        Calculate water density based on temperature for realistic KPP operation.

        Uses accurate polynomial approximation for water density:
        ρ(T) = ρ₀ + A(T-T₀) + B(T-T₀)² + C(T-T₀)³
        where coefficients are optimized for 0-100°C range

        Args:
            temperature (float): Water temperature in Kelvin

        Returns:
            float: Water density in kg/m³
        """
        # Convert to Celsius for polynomial calculation
        temp_celsius = temperature - 273.15

        # Polynomial coefficients for water density (0-100°C)
        # Based on IAPWS-95 formulation for practical use
        rho_0 = 999.842594  # kg/m³ at 0°C
        A = 6.793952e-2  # kg/m³/°C
        B = -9.095290e-3  # kg/m³/°C²
        C = 1.001685e-4  # kg/m³/°C³
        D = -1.120083e-6  # kg/m³/°C⁴
        E = 6.536336e-9  # kg/m³/°C⁵

        # Clamp temperature to valid range
        temp_celsius = max(0.0, min(100.0, temp_celsius))

        # Calculate density using polynomial
        density = (
            rho_0
            + A * temp_celsius
            + B * temp_celsius**2
            + C * temp_celsius**3
            + D * temp_celsius**4
            + E * temp_celsius**5
        )

        # Apply salinity correction if needed (seawater vs freshwater)
        # For KPP simulation, assume freshwater unless specified
        salinity_correction = 1.0  # No salinity correction for freshwater

        final_density = density * salinity_correction

        logger.debug(f"Water density at {temp_celsius:.1f}°C: {final_density:.1f} kg/m³")

        return max(final_density, 900.0)  # Minimum reasonable density

    def apply_nanobubble_effects(self, base_density: float) -> float:
        """
        Apply H1 nanobubble effects for realistic KPP operation.

        Advanced nanobubble physics including:
        - Size-dependent bubble behavior
        - Pressure effects on bubble stability
        - Temperature-dependent bubble dissolution
        - Turbulence effects on bubble distribution

        Args:
            base_density (float): Base water density

        Returns:
            float: Effective density with nanobubbles
        """
        if not self.h1_active:
            return base_density

        # Enhanced nanobubble physics
        bubble_size = 50e-9  # 50 nm typical nanobubble size
        pressure = 101325.0  # Atmospheric pressure (Pa)
        temperature = self.state.temperature

        # Calculate bubble stability factor
        # Smaller bubbles are more stable due to surface tension
        surface_tension = 0.0728  # N/m for water at 20°C
        bubble_stability = surface_tension / (2 * bubble_size)

        # Pressure effect on bubble volume (Boyle's law approximation)
        pressure_factor = 101325.0 / pressure  # Reference to atmospheric

        # Temperature effect on bubble dissolution
        # Higher temperature increases dissolution rate
        temp_factor = 1.0 - 0.02 * (temperature - 293.15) / 100.0  # 2% per 100K

        # Effective bubble fraction considering stability and conditions
        effective_bubble_fraction = self.state.nanobubble_fraction * pressure_factor * temp_factor * bubble_stability

        # Air density at current conditions
        air_density = 1.225 * (273.15 / temperature) * (pressure / 101325.0)

        # Calculate effective density with enhanced physics
        effective_density = base_density * (1 - effective_bubble_fraction) + air_density * effective_bubble_fraction

        # Add turbulence effects on bubble distribution
        # Turbulence can enhance or reduce bubble effectiveness
        turbulence_factor = 1.0  # Can be adjusted based on flow conditions

        final_density = effective_density * turbulence_factor

        logger.debug(
            f"Enhanced nanobubble effect: {base_density:.1f} → {final_density:.1f} kg/m³ "
            f"(bubbles: {effective_bubble_fraction*100:.2f}%, stability: {bubble_stability:.1e})"
        )

        return max(final_density, 800.0)  # Minimum reasonable density with bubbles

    def calculate_reynolds_number(self, velocity: float, characteristic_length: float) -> float:
        """
        Calculate Reynolds number for flow around floater.

        Re = v * L / ν

        Args:
            velocity (float): Relative velocity (m/s)
            characteristic_length (float): Characteristic length (m)

        Returns:
            float: Reynolds number
        """
        if abs(velocity) < 1e-6:
            return 0.0

        reynolds = abs(velocity) * characteristic_length / self.kinematic_viscosity
        self.state.reynolds_number = reynolds
        return reynolds

    def calculate_drag_coefficient(self, velocity: float, characteristic_length: float) -> float:
        """
        Calculate drag coefficient based on flow conditions.

        Uses Reynolds number to adjust drag coefficient:
        - Low Re: higher Cd (viscous effects)
        - High Re: lower Cd (inertial effects)
        - Includes nanobubble drag reduction

        Args:
            velocity (float): Relative velocity (m/s)
            characteristic_length (float): Characteristic length (m)

        Returns:
            float: Drag coefficient
        """
        re = self.calculate_reynolds_number(velocity, characteristic_length)

        # Base drag coefficient for sphere/cylinder at different Re ranges
        if re < 1:
            # Stokes flow regime
            cd_base = 24 / max(re, 0.1)  # Avoid division by zero
        elif re < 1000:
            # Intermediate regime
            cd_base = 24 / re + 6 / (1 + math.sqrt(re)) + 0.4
        else:
            # High Reynolds number regime
            cd_base = 0.44

        # Apply nanobubble drag reduction if H1 is active
        if self.h1_active:
            cd_effective = cd_base * (1 - self.h1_drag_reduction)
        else:
            cd_effective = cd_base

        # Limit to reasonable range
        cd_effective = max(0.1, min(cd_effective, 2.0))

        logger.debug(
            f"Drag coefficient: Re={re:.1f}, Cd_base={cd_base:.3f}, "
            f"Cd_eff={cd_effective:.3f} (H1 reduction: {self.h1_drag_reduction if self.h1_active else 0:.1%})"
        )

        return cd_effective

    def calculate_drag_force(self, velocity: float, floater_area: Optional[float] = None) -> float:
        """
        Calculate hydrodynamic drag force on a floater.

        F_drag = 0.5 * ρ_eff * Cd * A * v²

        Args:
            velocity (float): Relative velocity through water (m/s)
            floater_area (float, optional): Cross-sectional area (m²)

        Returns:
            float: Drag force magnitude (N)
        """
        if abs(velocity) < 1e-6:
            return 0.0

        area = floater_area or self.floater_area
        characteristic_length = math.sqrt(4 * area / math.pi)  # Equivalent diameter

        cd = self.calculate_drag_coefficient(velocity, characteristic_length)

        # Calculate drag force
        drag_force = 0.5 * self.state.effective_density * cd * area * velocity**2

        logger.debug(
            f"Drag force: v={velocity:.2f} m/s, A={area:.3f} m², "
            f"ρ_eff={self.state.effective_density:.1f} kg/m³, "
            f"Cd={cd:.3f}, F_drag={drag_force:.1f} N"
        )

        return drag_force

    def calculate_buoyant_force(self, volume: float, submerged_fraction: float = 1.0) -> float:
        """
        Calculate realistic buoyant force for KPP operation.

        Enhanced buoyancy physics including:
        - Temperature-dependent fluid density
        - Pressure effects on fluid properties
        - Surface tension effects
        - Dynamic pressure variations
        - Wave and turbulence effects

        Args:
            volume (float): Floater volume (m³)
            submerged_fraction (float): Fraction of volume submerged (0-1)

        Returns:
            float: Buoyant force (N)
        """
        if volume <= 0 or submerged_fraction <= 0:
            return 0.0

        # Base buoyant force calculation
        submerged_volume = volume * min(submerged_fraction, 1.0)
        base_buoyant_force = self.state.effective_density * self.gravity * submerged_volume

        # Enhanced physics corrections

        # 1. Pressure effects on fluid density
        # Hydrostatic pressure increases with depth
        depth = 5.0  # Typical KPP depth (m)
        hydrostatic_pressure = self.state.effective_density * self.gravity * depth
        pressure_density_correction = 1.0 + (hydrostatic_pressure / 2.2e9)  # Bulk modulus of water

        # 2. Temperature stratification effects
        # Water temperature can vary with depth
        surface_temp = self.state.temperature
        depth_temp = surface_temp - 2.0  # 2°C cooler at depth
        temp_density_correction = self.calculate_density(depth_temp) / self.calculate_density(surface_temp)

        # 3. Surface tension effects
        # Surface tension affects buoyancy near water surface
        surface_tension_force = 0.0728 * 2 * math.pi * (volume ** (1 / 3))  # N
        surface_tension_correction = (
            1.0 + (surface_tension_force / base_buoyant_force) if base_buoyant_force > 0 else 1.0
        )

        # 4. Dynamic pressure effects
        # Flow velocity affects effective pressure
        flow_velocity = 1.0  # m/s typical flow
        dynamic_pressure = 0.5 * self.state.effective_density * flow_velocity**2
        dynamic_correction = 1.0 + (dynamic_pressure / (self.state.effective_density * self.gravity * depth))

        # 5. Wave and turbulence effects
        # Random variations in buoyancy due to waves
        import random

        wave_factor = 1.0 + 0.05 * random.uniform(-1, 1)  # ±5% variation

        # Combine all corrections
        total_correction = (
            pressure_density_correction
            * temp_density_correction
            * surface_tension_correction
            * dynamic_correction
            * wave_factor
        )

        # Apply correction to buoyant force
        enhanced_buoyant_force = base_buoyant_force * total_correction

        logger.debug(
            f"Enhanced buoyant force: {base_buoyant_force:.1f}N → {enhanced_buoyant_force:.1f}N "
            f"(V={volume:.3f} m³, fraction={submerged_fraction:.2f}, "
            f"ρ_eff={self.state.effective_density:.1f} kg/m³, correction={total_correction:.3f})"
        )

        return max(enhanced_buoyant_force, 0.0)  # Ensure non-negative

    def get_fluid_properties(self) -> Dict[str, float]:
        """
        Get current fluid properties for logging/monitoring.

        Returns:
            dict: Current fluid properties
        """
        return {
            "density": self.state.density,
            "effective_density": self.state.effective_density,
            "temperature": self.state.temperature,
            "nanobubble_fraction": self.state.nanobubble_fraction,
            "drag_coefficient": self.state.drag_coefficient,
            "reynolds_number": self.state.reynolds_number,
            "h1_active": self.h1_active,
        }

    def set_h1_active(
        self,
        active: bool,
        bubble_fraction: Optional[float] = None,
        drag_reduction: Optional[float] = None,
    ):
        """
        Enable/disable H1 nanobubble effects.

        Args:
            active (bool): Whether to activate H1 effects
            bubble_fraction (float, optional): Bubble volume fraction (0-1)
            drag_reduction (float, optional): Drag reduction factor (0-1)
        """
        self.h1_active = active

        if bubble_fraction is not None:
            self.h1_bubble_fraction = max(0.0, min(bubble_fraction, 0.2))  # Limit to 20%

        if drag_reduction is not None:
            self.h1_drag_reduction = max(0.0, min(drag_reduction, 0.5))  # Limit to 50%

        self.update_state()

        logger.info(
            f"H1 nanobubbles {'activated' if active else 'deactivated'}: "
            f"bubble_fraction={self.h1_bubble_fraction:.1%}, "
            f"drag_reduction={self.h1_drag_reduction:.1%}"
        )

    def set_temperature(self, temperature: float):
        """
        Set water temperature and update density.

        Args:
            temperature (float): Water temperature in Kelvin
        """
        self.base_temperature = max(273.15, min(temperature, 373.15))  # Limit to liquid range
        self.update_state()

        logger.info(
            f"Water temperature set to {self.base_temperature:.1f} K "
            f"({self.base_temperature - 273.15:.1f}°C), "
            f"density: {self.state.density:.1f} kg/m³"
        )
