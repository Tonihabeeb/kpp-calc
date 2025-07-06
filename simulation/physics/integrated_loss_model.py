"""
Integrated Enhanced Loss Model for KPP System
Combines mechanical, electrical, and thermal loss models for comprehensive system analysis.
"""

import logging
from dataclasses import dataclass
from typing import Dict

import numpy as np

from simulation.physics.losses import (
    ComponentState,
    DrivetrainLosses,
    ElectricalLosses,
    LossComponents,
)
from simulation.physics.thermal import ThermalModel, ThermalState

logger = logging.getLogger(__name__)


@dataclass
class SystemLosses:
    """Complete system loss breakdown"""

    mechanical_losses: LossComponents
    electrical_losses: float
    thermal_losses: float
    total_system_losses: float
    system_efficiency: float


@dataclass
class EnhancedSystemState:
    """Enhanced system state including thermal and loss information"""

    component_states: Dict[str, ComponentState]
    thermal_states: Dict[str, ThermalState]
    electrical_state: Dict[str, float]
    system_losses: SystemLosses
    performance_metrics: Dict[str, float]


class IntegratedLossModel:
    """
    Integrated loss model combining mechanical, electrical, and thermal effects.

    Features:
    - Comprehensive loss tracking across all system components
    - Thermal-mechanical coupling (temperature affects efficiency)
    - Electrical-thermal coupling (losses generate heat)
    - Real-time performance monitoring and optimization
    """

    def __init__(self, ambient_temperature: float = 20.0):
        """
        Initialize integrated loss model.

        Args:
            ambient_temperature: Ambient temperature in °C
        """
        self.drivetrain_losses = DrivetrainLosses()
        self.electrical_losses = ElectricalLosses()
        self.thermal_model = ThermalModel(ambient_temperature)

        # Performance tracking
        self.efficiency_history = []
        self.loss_history = []
        self.thermal_history = []

        # System configuration
        self.system_config = {}

        # Warning thresholds
        self.efficiency_warning_threshold = 0.70  # 70% efficiency warning
        self.temperature_warning_threshold = 80.0  # 80°C temperature warning

        logger.info("IntegratedLossModel initialized with comprehensive loss and thermal modeling")

    def initialize_system_components(self, config: Dict):
        """
        Initialize system components with configuration parameters.

        Args:
            config: System configuration dictionary
        """
        self.system_config = config

        # Initialize thermal components based on configuration
        ambient_temp = config.get("ambient_temperature", 20.0)

        # Standard KPP thermal components
        thermal_components = {
            "sprocket": ThermalState(
                temperature=ambient_temp,
                heat_capacity=500.0,
                mass=config.get("sprocket_mass", 25.0),
                surface_area=config.get("sprocket_surface_area", 0.5),
                thermal_conductivity=50.0,
            ),
            "gearbox": ThermalState(
                temperature=ambient_temp,
                heat_capacity=500.0,
                mass=config.get("gearbox_mass", 200.0),
                surface_area=config.get("gearbox_surface_area", 2.0),
                thermal_conductivity=50.0,
            ),
            "clutch": ThermalState(
                temperature=ambient_temp,
                heat_capacity=500.0,
                mass=config.get("clutch_mass", 50.0),
                surface_area=config.get("clutch_surface_area", 0.5),
                thermal_conductivity=50.0,
            ),
            "flywheel": ThermalState(
                temperature=ambient_temp,
                heat_capacity=500.0,
                mass=config.get("flywheel_mass", 500.0),
                surface_area=config.get("flywheel_surface_area", 3.0),
                thermal_conductivity=50.0,
            ),
            "generator": ThermalState(
                temperature=ambient_temp,
                heat_capacity=800.0,
                mass=config.get("generator_mass", 300.0),
                surface_area=config.get("generator_surface_area", 4.0),
                thermal_conductivity=100.0,
            ),
        }

        for name, thermal_state in thermal_components.items():
            self.thermal_model.add_component(name, thermal_state)

        logger.info(f"Initialized {len(thermal_components)} thermal components")

    def update_system_losses(self, system_state: Dict, dt: float) -> EnhancedSystemState:
        """
        Update comprehensive system losses including thermal effects.

        Args:
            system_state: Current system state dictionary
            dt: Time step in seconds

        Returns:
            EnhancedSystemState with complete loss and thermal information
        """
        # Extract component states
        component_states = self._extract_component_states(system_state)

        # Calculate mechanical losses with thermal effects
        mechanical_losses = self._calculate_enhanced_mechanical_losses(component_states)

        # Calculate electrical losses
        electrical_state = system_state.get("electrical", {})
        electrical_losses_value = self.electrical_losses.calculate_total_electrical_losses(electrical_state)

        # Calculate heat generation from losses
        heat_sources = self._calculate_heat_generation(mechanical_losses, electrical_losses_value, component_states)

        # Update thermal model
        self.thermal_model.update_all_temperatures(heat_sources, dt)

        # Calculate thermal effects on efficiency
        self._calculate_thermal_efficiency_effects(component_states)

        # Calculate total system losses
        total_losses = mechanical_losses.total_losses + electrical_losses_value
        input_power = system_state.get("input_power", 1.0)
        system_efficiency = max(0.0, (input_power - total_losses) / input_power) if input_power > 0 else 0.0

        # Create system losses summary
        system_losses = SystemLosses(
            mechanical_losses=mechanical_losses,
            electrical_losses=electrical_losses_value,
            thermal_losses=0.0,  # Thermal losses are captured in efficiency reduction
            total_system_losses=total_losses,
            system_efficiency=system_efficiency,
        )

        # Get thermal states
        thermal_states = self.thermal_model.get_system_thermal_state()

        # Calculate performance metrics
        performance_metrics = self._calculate_performance_metrics(system_losses, thermal_states, system_state)
        # Create enhanced system state
        enhanced_state = EnhancedSystemState(
            component_states=component_states,
            thermal_states=self.thermal_model.component_states,  # Use actual ThermalState objects
            electrical_state=electrical_state,
            system_losses=system_losses,
            performance_metrics=performance_metrics,
        )

        # Update tracking
        self._update_performance_tracking(enhanced_state)

        # Check for warnings
        self._check_system_warnings(enhanced_state)

        return enhanced_state

    def _extract_component_states(self, system_state: Dict) -> Dict[str, ComponentState]:
        """Extract component states from system state dictionary"""
        component_states = {}

        # Extract states for each component
        components = ["sprocket", "gearbox", "clutch", "flywheel", "generator"]

        for component in components:
            component_data = system_state.get(component, {})

            # Get thermal state
            thermal_temp = 20.0
            if component in self.thermal_model.component_states:
                thermal_temp = self.thermal_model.component_states[component].temperature

            component_states[component] = ComponentState(
                torque=component_data.get("torque", 0.0),
                speed=component_data.get("speed", 0.0),
                temperature=thermal_temp,
                load_factor=component_data.get("load_factor", 0.0),
                efficiency=component_data.get("efficiency", 1.0),
            )

        return component_states

    def _calculate_enhanced_mechanical_losses(self, component_states: Dict[str, ComponentState]) -> LossComponents:
        """Calculate mechanical losses with thermal coupling"""
        # Apply thermal effects to component states
        enhanced_states = {}
        for name, state in component_states.items():
            enhanced_efficiency = self.thermal_model.calculate_temperature_effects_on_efficiency(name, state.efficiency)

            enhanced_state = ComponentState(
                torque=state.torque,
                speed=state.speed,
                temperature=state.temperature,
                load_factor=state.load_factor,
                efficiency=enhanced_efficiency,
            )
            enhanced_states[name] = enhanced_state

        # Calculate losses with thermal effects
        losses = self.drivetrain_losses.calculate_total_losses(enhanced_states, self.system_config)

        return losses

    def _calculate_heat_generation(
        self,
        mechanical_losses: LossComponents,
        electrical_losses: float,
        component_states: Dict[str, ComponentState],
    ) -> Dict[str, float]:
        """Calculate heat generation from all loss sources"""
        heat_sources = {}

        # Distribute mechanical losses to components
        total_mechanical_power = sum(abs(state.torque * state.speed) for state in component_states.values())

        if total_mechanical_power > 0:
            for component_name, state in component_states.items():
                component_power = abs(state.torque * state.speed)
                power_fraction = component_power / total_mechanical_power

                # Distribute different loss types based on component
                component_heat = 0.0

                if "bearing" in component_name or "sprocket" in component_name:
                    component_heat += mechanical_losses.bearing_friction * power_fraction
                    component_heat += mechanical_losses.seal_friction * power_fraction

                if "gear" in component_name or "gearbox" in component_name:
                    component_heat += mechanical_losses.gear_mesh_losses * power_fraction
                    component_heat += mechanical_losses.windage_losses * power_fraction

                if "clutch" in component_name:
                    component_heat += mechanical_losses.clutch_losses

                heat_sources[component_name] = component_heat

        # Add electrical losses to generator
        if "generator" in heat_sources:
            heat_sources["generator"] += electrical_losses
        else:
            heat_sources["generator"] = electrical_losses

        return heat_sources

    def _calculate_thermal_efficiency_effects(self, component_states: Dict[str, ComponentState]) -> Dict[str, float]:
        """Calculate how thermal effects modify component efficiency"""
        thermal_factors = {}

        for component_name, state in component_states.items():
            thermal_factor = self.thermal_model.calculate_temperature_effects_on_efficiency(
                component_name, 1.0  # Base efficiency of 1.0 to get the factor
            )
            thermal_factors[component_name] = thermal_factor

        return thermal_factors

    def _calculate_performance_metrics(
        self, system_losses: SystemLosses, thermal_states: Dict, system_state: Dict
    ) -> Dict[str, float]:
        """Calculate comprehensive performance metrics"""
        metrics = {}

        # Efficiency metrics
        metrics["system_efficiency"] = system_losses.system_efficiency
        metrics["mechanical_efficiency"] = 1.0 - (
            system_losses.mechanical_losses.total_losses / max(1.0, system_state.get("input_power", 1.0))
        )
        metrics["electrical_efficiency"] = 1.0 - (
            system_losses.electrical_losses / max(1.0, system_state.get("electrical_power", 1.0))
        )

        # Thermal metrics
        avg_temperature = np.mean([state["temperature"] for state in thermal_states.values()])
        max_temperature = max([state["temperature"] for state in thermal_states.values()])

        metrics["average_temperature"] = avg_temperature
        metrics["max_temperature"] = max_temperature
        metrics["thermal_margin"] = 100.0 - max_temperature  # Margin to 100°C

        # Loss breakdown percentages
        if system_losses.total_system_losses > 0:
            metrics["bearing_loss_percent"] = (
                system_losses.mechanical_losses.bearing_friction / system_losses.total_system_losses
            ) * 100
            metrics["gear_loss_percent"] = (
                system_losses.mechanical_losses.gear_mesh_losses / system_losses.total_system_losses
            ) * 100
            metrics["electrical_loss_percent"] = (
                system_losses.electrical_losses / system_losses.total_system_losses
            ) * 100
        else:
            metrics["bearing_loss_percent"] = 0.0
            metrics["gear_loss_percent"] = 0.0
            metrics["electrical_loss_percent"] = 0.0
        # Performance indices
        metrics["power_density"] = system_state.get("output_power", 0.0) / max(1.0, float(avg_temperature - 20.0))
        metrics["thermal_efficiency_index"] = system_losses.system_efficiency * (100.0 / max(50.0, max_temperature))

        return metrics

    def _update_performance_tracking(self, enhanced_state: EnhancedSystemState):
        """Update performance tracking histories"""
        self.efficiency_history.append(enhanced_state.system_losses.system_efficiency)
        self.loss_history.append(enhanced_state.system_losses.total_system_losses)

        # Track thermal history
        avg_temp = enhanced_state.performance_metrics.get("average_temperature", 20.0)
        self.thermal_history.append(avg_temp)

        # Limit history size
        max_history = 1000
        if len(self.efficiency_history) > max_history:
            self.efficiency_history = self.efficiency_history[-max_history:]
            self.loss_history = self.loss_history[-max_history:]
            self.thermal_history = self.thermal_history[-max_history:]

    def _check_system_warnings(self, enhanced_state: EnhancedSystemState):
        """Check for system warnings and log them"""
        # Efficiency warnings
        if enhanced_state.system_losses.system_efficiency < self.efficiency_warning_threshold:
            logger.warning(
                f"System efficiency below threshold: {enhanced_state.system_losses.system_efficiency:.3f} < {self.efficiency_warning_threshold}"
            )

        # Temperature warnings
        max_temp = enhanced_state.performance_metrics.get("max_temperature", 0.0)
        if max_temp > self.temperature_warning_threshold:
            logger.warning(
                f"System temperature above threshold: {max_temp:.1f}°C > {self.temperature_warning_threshold}°C"
            )
        # Check thermal limits
        thermal_limits = self.thermal_model.check_thermal_limits()
        for component, status in thermal_limits.items():
            if isinstance(status, dict) and status.get("over_limit", False):
                logger.warning(
                    f"Component {component} over thermal limit: {status['temperature']:.1f}°C > {status['limit']:.1f}°C"
                )

    def get_system_performance_summary(self) -> Dict:
        """Get comprehensive system performance summary"""
        if not self.efficiency_history:
            return {"status": "No data available"}

        summary = {
            "current_efficiency": (self.efficiency_history[-1] if self.efficiency_history else 0.0),
            "average_efficiency": np.mean(self.efficiency_history),
            "min_efficiency": np.min(self.efficiency_history),
            "max_efficiency": np.max(self.efficiency_history),
            "current_losses": self.loss_history[-1] if self.loss_history else 0.0,
            "average_losses": np.mean(self.loss_history),
            "current_temperature": (self.thermal_history[-1] if self.thermal_history else 20.0),
            "max_temperature": np.max(self.thermal_history),
            "thermal_model_components": len(self.thermal_model.component_states),
            "data_points": len(self.efficiency_history),
        }

        return summary

    def reset(self):
        """Reset the integrated loss model"""
        self.drivetrain_losses.reset()
        self.thermal_model.reset()
        self.efficiency_history.clear()
        self.loss_history.clear()
        self.thermal_history.clear()

        logger.info("IntegratedLossModel reset")


from typing import Any, Dict, Union


def create_standard_kpp_enhanced_loss_model(
    config_or_temp: Union[float, Dict[str, Any]] = 20.0,
) -> IntegratedLossModel:
    """
    Create standard KPP enhanced loss model with realistic parameters.

    Args:
        config_or_temp: Either ambient temperature (float, °C) or config dict

    Returns:
        Configured IntegratedLossModel
    """

    # If a dict is passed, treat as config dict
    if isinstance(config_or_temp, dict):
        config = config_or_temp.copy()
        ambient_temp = config.get("ambient_temperature", 20.0)
        model = IntegratedLossModel(ambient_temp)
        model.initialize_system_components(config)
        logger.info(f"Created KPP enhanced loss model from config dict (ambient_temperature={ambient_temp}°C)")
        return model
    else:
        ambient_temp = float(config_or_temp)
        model = IntegratedLossModel(ambient_temp)
        # Standard KPP configuration
        config = {
            "ambient_temperature": ambient_temp,
            "sprocket_mass": 25.0,  # kg
            "sprocket_surface_area": 0.5,  # m²
            "gearbox_mass": 200.0,  # kg
            "gearbox_surface_area": 2.0,  # m²
            "clutch_mass": 50.0,  # kg
            "clutch_surface_area": 0.5,  # m²
            "flywheel_mass": 500.0,  # kg
            "flywheel_surface_area": 3.0,  # m²
            "generator_mass": 300.0,  # kg
            "generator_surface_area": 4.0,  # m²
            "gear_ratios": {
                "sprocket": 1.0,
                "gearbox": 39.4,
                "clutch": 1.0,
                "flywheel": 1.0,
                "generator": 1.0,
            },
        }
        model.initialize_system_components(config)
        logger.info(f"Created standard KPP enhanced loss model with ambient temperature {ambient_temp}°C")
        return model
