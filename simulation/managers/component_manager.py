"""
Component Manager for the KPP Simulation Engine.
Handles component coordination, pulse control, and basic system updates.
"""

import logging
from typing import Dict, List, Any, Optional
from .base_manager import BaseManager, ManagerType
from ..schemas import ComponentStatus

logger = logging.getLogger(__name__)


class ComponentManager(BaseManager):
    """
    Manages component-level operations for the KPP simulation including:
    - Component initialization and updates
    - Pulse trigger coordination
    - Pneumatic system management
    - Legacy component compatibility
    """

    def __init__(self, engine):
        """
        Initialize the ComponentManager with reference to the main engine.
        
        Args:
            engine: Reference to the main SimulationEngine instance
        """
        super().__init__(engine, ManagerType.COMPONENT)

    def update(self, dt: float, *args, **kwargs) -> Dict[str, Any]:
        """
        Main update method required by BaseManager.
        
        Args:
            dt: Time step in seconds
            
        Returns:
            Dictionary containing component update results
        """
        return self.update_components(dt)

    def update_components(self, dt: float) -> Dict[str, Any]:
        """
        Update all components and handle pulse triggering.
        
        Args:
            dt: Time step in seconds
            
        Returns:
            Dictionary containing component update results
        """
        # 1. Check for pulse trigger
        pulse_triggered = self.check_and_trigger_pulse(dt)
        
        # 2. Update pneumatic system
        self.engine.pneumatics.update(dt)
        
        # 3. Update thermal and fluid system states
        self.engine.fluid_system.update_state()
        self.engine.thermal_model.update_state()
        
        # 4. Update individual floaters
        for floater in self.engine.floaters:
            floater.update(dt)
        
        # 5. Handle pneumatic performance tracking if available
        pneumatic_executed = self._update_pneumatic_performance_tracking(dt)
        
        return {
            "pulse_triggered": pulse_triggered,
            "pneumatic_executed": pneumatic_executed,
            "components_updated": True
        }

    def check_and_trigger_pulse(self, dt: float) -> bool:
        """
        Check for pulse trigger conditions and execute if appropriate.
        
        Args:
            dt: Time step in seconds
            
        Returns:
            True if pulse was triggered
        """
        pulse_interval = self.engine.params.get("pulse_interval", 2.0)
        
        if self.engine.time - self.engine.last_pulse_time >= pulse_interval:
            # Find a floater ready for pulsing
            for i, floater in enumerate(self.engine.floaters):
                x, y = floater.get_cartesian_position()
                # Trigger pulse if floater is near bottom and ready to fill
                if y <= 0.1 and not floater.is_filled:
                    self.engine.pneumatics.trigger_injection(floater)
                    self.engine.last_pulse_time = self.engine.time
                    self.engine.pulse_count += 1
                    logger.debug(f"Pulse triggered for floater {i} at t={self.engine.time:.2f}s")
                    return True
                
        return False

    def update_basic_components(self, dt: float) -> None:
        """
        Update basic component states that don't require complex coordination.
        
        Args:
            dt: Time step in seconds
        """
        # Update pneumatic system
        self.engine.pneumatics.update(dt)
        
        # Update thermal and fluid system states (legacy components)
        self.engine.fluid_system.update_state()
        self.engine.thermal_model.update_state()
        
        logger.debug("Basic components updated")

    def log_system_status(self, dt: float) -> None:
        """
        Log system status information for monitoring.
        
        Args:
            dt: Time step in seconds
        """
        if self.engine.time % 1.0 < dt:  # Log every second
            logger.debug(
                f"Fluid system: H1_active={self.engine.fluid_system.h1_active}, "
                f"effective_density={self.engine.fluid_system.state.effective_density:.1f} kg/m³"
            )
            logger.debug(
                f"Thermal system: H2_active={self.engine.thermal_model.h2_active}, "
                f"buoyancy_enhancement={self.engine.thermal_model.state.buoyancy_enhancement:.1%}"
            )
            logger.debug(
                f"Enhanced physics - H1: {self.engine.h1_nanobubbles_active}, "
                f"H2: {self.engine.h2_thermal_active}, H3: {self.engine.h3_pulse_active}"
            )

    def update_legacy_drivetrain_compatibility(self, drivetrain_output: Dict[str, Any],
                                              final_output_speed: float) -> None:
        """
        Update legacy drivetrain for compatibility with existing monitoring systems.
        
        Args:
            drivetrain_output: Integrated drivetrain output
            final_output_speed: Final output speed in rad/s
        """
        # For legacy compatibility, update the old drivetrain with equivalent values
        self.engine.drivetrain.omega_chain = drivetrain_output.get("chain_speed_rpm", 0.0) * (
            2 * 3.14159 / 60
        )
        self.engine.drivetrain.omega_flywheel = final_output_speed
        
        logger.debug("Legacy drivetrain compatibility updated")

    def get_component_status(self) -> Dict[str, Any]:
        """
        Get comprehensive component status for monitoring.
        
        Returns:
            Dictionary containing component status information
        """
        return {
            "pneumatics": {
                "tank_pressure": self.engine.pneumatics.tank_pressure,
                "compressor_running": getattr(self.engine.pneumatics, "compressor_running", False),
                "target_pressure": getattr(self.engine.pneumatics, "target_pressure", 5.0),
            },
            "floaters": {
                "count": len(self.engine.floaters),
                "filled_count": sum(1 for f in self.engine.floaters if getattr(f, "is_filled", False)),
                "average_velocity": (
                    sum(abs(getattr(f, "velocity", 0.0)) for f in self.engine.floaters) / len(self.engine.floaters)
                    if self.engine.floaters else 0.0
                ),
            },
            "chain": {
                "tension": getattr(self.engine, "chain_tension", 0.0),
                "angular_speed": (
                    self.engine.chain_system.get_angular_speed()
                    if hasattr(self.engine, "chain_system")
                    else 0.0
                ),
                "chain_speed": (
                    self.engine.chain_system.get_chain_speed()
                    if hasattr(self.engine, "chain_system")
                    else 0.0
                ),
            },
            "enhanced_physics": {
                "h1_nanobubbles": {
                    "active": self.engine.h1_nanobubbles_active,
                    "force_contribution": getattr(self.engine, "h1_nanobubble_force", 0.0),
                },
                "h2_thermal": {
                    "active": self.engine.h2_thermal_active,
                    "force_contribution": getattr(self.engine, "h2_thermal_force", 0.0),
                },
                "h3_pulse": {
                    "active": self.engine.h3_pulse_active,
                    "force_contribution": getattr(self.engine, "h3_pulse_force", 0.0),
                },
            },
        }

    def validate_component_states(self) -> List[str]:
        """
        Validate component states and return any warnings.
        
        Returns:
            List of warning messages
        """
        warnings = []
        
        # Check pneumatic system
        if self.engine.pneumatics.tank_pressure < 1.0:
            warnings.append("Tank pressure critically low")
            
        # Check floater states
        filled_count = sum(1 for f in self.engine.floaters if getattr(f, "is_filled", False))
        if filled_count == 0:
            warnings.append("No floaters are air-filled")
            
        # Check chain tension
        if abs(getattr(self.engine, "chain_tension", 0.0)) > 50000.0:
            warnings.append("Chain tension exceeds safe limits")
            
        # Check enhanced physics consistency
        if (self.engine.h1_nanobubbles_active and 
            not hasattr(self.engine, "nanobubble_physics")):
            warnings.append("H1 nanobubble physics enabled but not initialized")
            
        if (self.engine.h2_thermal_active and 
            not hasattr(self.engine, "thermal_physics")):
            warnings.append("H2 thermal physics enabled but not initialized")
            
        if (self.engine.h3_pulse_active and 
            not hasattr(self.engine, "pulse_controller")):
            warnings.append("H3 pulse physics enabled but not initialized")
            
        return warnings

    def handle_emergency_conditions(self, system_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check for and handle emergency conditions.
        
        Args:
            system_state: Current system state
            
        Returns:
            Emergency response actions taken
        """
        emergency_actions = {
            "emergency_stop": False,
            "reduce_power": False,
            "vent_pressure": False,
            "actions_taken": [],
        }
        
        # Check for over-pressure
        if self.engine.pneumatics.tank_pressure > 8.0:
            emergency_actions["vent_pressure"] = True
            emergency_actions["actions_taken"].append("Venting excess pressure")
            logger.warning("Emergency pressure venting triggered")
            
        # Check for excessive chain tension
        chain_tension = abs(system_state.get("chain_tension", 0.0))
        if chain_tension > 60000.0:
            emergency_actions["emergency_stop"] = True
            emergency_actions["actions_taken"].append("Emergency stop due to chain tension")
            logger.error("Emergency stop triggered due to excessive chain tension")
            
        # Check for electrical system faults
        if system_state.get("electrical_power_output", 0.0) < 0:
            emergency_actions["reduce_power"] = True
            emergency_actions["actions_taken"].append("Reducing power due to electrical fault")
            logger.warning("Power reduction triggered due to electrical fault")
            
        return emergency_actions

    def get_diagnostics(self) -> Dict[str, Any]:
        """
        Get detailed component diagnostics for troubleshooting.
        
        Returns:
            Dictionary containing diagnostic information
        """
        diagnostics = {
            "simulation_time": self.engine.time,
            "time_step": self.engine.dt,
            "pulse_count": getattr(self.engine, "pulse_count", 0),
            "total_energy": getattr(self.engine, "total_energy", 0.0),
            "component_status": self.get_component_status(),
            "validation_warnings": self.validate_component_states(),
            "memory_usage": {
                "floater_count": len(self.engine.floaters),
                "data_log_size": len(getattr(self.engine, "data_log", [])),
                "output_data_size": len(getattr(self.engine, "output_data", [])),
            },
        }
        
        return diagnostics

    def _update_pneumatic_performance_tracking(self, dt: float) -> bool:
        """
        Update pneumatic performance tracking if available.
        
        Args:
            dt: Time step in seconds
            
        Returns:
            True if pneumatic operations were executed
        """
        pneumatic_executed = False
        
        # Check if pneumatic coordinator exists and update performance metrics
        if hasattr(self.engine, 'pneumatic_coordinator'):
            try:
                # Check if the coordinator has an update method
                if hasattr(self.engine.pneumatic_coordinator, 'update_metrics'):
                    self.engine.pneumatic_coordinator.update_metrics(dt)
                    pneumatic_executed = True
                elif hasattr(self.engine.pneumatic_coordinator, 'update'):
                    self.engine.pneumatic_coordinator.update(dt)
                    pneumatic_executed = True
                # If no update method, just mark as executed (coordinator exists)
                else:
                    pneumatic_executed = True
            except Exception as e:
                logger.debug(f"Pneumatic coordinator update not available: {e}")
        
        # Check if pneumatic energy analyzer exists
        if hasattr(self.engine, 'pneumatic_energy_analyzer'):
            try:
                # Check if the analyzer has an update method
                if hasattr(self.engine.pneumatic_energy_analyzer, 'update_analysis'):
                    self.engine.pneumatic_energy_analyzer.update_analysis(dt)
                elif hasattr(self.engine.pneumatic_energy_analyzer, 'analyze'):
                    self.engine.pneumatic_energy_analyzer.analyze(dt)
            except Exception as e:
                logger.debug(f"Pneumatic energy analyzer update not available: {e}")
                
        return pneumatic_executed
