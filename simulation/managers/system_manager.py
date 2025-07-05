"""
System Manager for the KPP Simulation Engine.
Handles system-level operations including component coordination,
electrical system management, and control system integration.
"""

import logging
from typing import Dict, List, Any, Tuple, Optional
from .base_manager import BaseManager, ManagerType
from ..schemas import (
    ElectricalSystemOutput, SystemState, GridServicesState, TransientEventState,
    PhysicsResults, SystemResults
)

logger = logging.getLogger(__name__)


class SystemManager(BaseManager):
    """
    Manages system-level operations for the KPP simulation including:
    - Component coordination and integration
    - Electrical system management
    - Control system integration
    - Grid services coordination
    - Transient event handling
    """

    def __init__(self, engine):
        """
        Initialize the SystemManager with reference to the main engine.
        
        Args:
            engine: Reference to the main SimulationEngine instance
        """
        super().__init__(engine, ManagerType.SYSTEM)

    def update(self, dt: float, *args, **kwargs) -> Dict[str, Any]:
        """
        Main update method required by BaseManager.
        
        Args:
            dt: Time step in seconds
            
        Returns:
            Dictionary containing system update results
        """
        # This will be implemented when we refactor the full system
        return {}

    def update_electrical_system(self, preliminary_torque: float, 
                                preliminary_speed_rad_s: float, dt: float,
                                control_commands: Dict[str, Any]) -> ElectricalSystemOutput:
        """
        Update the integrated electrical system with mechanical input and control commands.
        
        Args:
            preliminary_torque: Preliminary mechanical torque
            preliminary_speed_rad_s: Preliminary speed in rad/s
            dt: Time step in seconds
            control_commands: Control system commands
            
        Returns:
            Electrical system output data
        """
        # Extract control commands
        timing_commands = control_commands.get("timing_commands", {})
        load_commands = control_commands.get("load_commands", {})
        grid_commands = control_commands.get("grid_commands", {})
        control_mode = control_commands.get("control_mode", "normal")

        # Build electrical configuration updates
        electrical_config_updates = {
            "target_load_factor": load_commands.get("target_load_factor", 0.8),
            "power_setpoint": load_commands.get(
                "power_setpoint", self.get_config_param("target_power", 530000.0)
            ),
            "voltage_setpoint": grid_commands.get("voltage_setpoint", 480.0),
            "frequency_setpoint": grid_commands.get("frequency_setpoint", 60.0),
            "control_mode": control_mode,
        }

        # Update integrated electrical system
        electrical_output_dict = self.engine.integrated_electrical_system.update(
            preliminary_torque, preliminary_speed_rad_s, dt, electrical_config_updates
        )
        
        # Convert to Pydantic model
        electrical_output = ElectricalSystemOutput(
            electrical_load_torque=electrical_output_dict.get("load_torque", 0.0),
            power_output=electrical_output_dict.get("grid_power_output", 0.0),
            grid_power=electrical_output_dict.get("grid_power", 0.0),
            voltage=electrical_output_dict.get("grid_voltage", 480.0),
            frequency=electrical_output_dict.get("grid_frequency", 60.0),
            power_factor=electrical_output_dict.get("power_factor", 0.95),
            reactive_power=electrical_output_dict.get("reactive_power", 0.0),
            system_efficiency=electrical_output_dict.get("efficiency", 0.0),
            synchronized=electrical_output_dict.get("synchronized", False),
            grid_services_active=electrical_output_dict.get("grid_services_active", False)
        )
        
        logger.debug(f"Electrical system updated: power={electrical_output.power_output:.1f}W")
        return electrical_output

    def update_drivetrain_with_load(self, electrical_load_torque: float, dt: float) -> Dict[str, Any]:
        """
        Update the drivetrain system with actual electrical load feedback.
        
        Args:
            electrical_load_torque: Load torque from electrical system
            dt: Time step in seconds
            
        Returns:
            Final drivetrain output data
        """
        # Update drivetrain with load feedback
        drivetrain_output = self.engine.integrated_drivetrain.update(
            self.engine.chain_tension, electrical_load_torque, dt
        )
        
        logger.debug(f"Drivetrain updated with load: {electrical_load_torque:.1f}Nm")
        return drivetrain_output

    def update_control_system(self, system_state: Dict[str, Any], dt: float) -> Dict[str, Any]:
        """
        Update the integrated control system with current system state.
        
        Args:
            system_state: Current comprehensive system state
            dt: Time step in seconds
            
        Returns:
            Control system output commands
        """
        control_output = self.engine.integrated_control_system.update(system_state, dt)
        
        # Execute pneumatic control if available
        if hasattr(
            self.engine.integrated_control_system.timing_controller,
            "execute_pneumatic_control",
        ):
            pneumatic_executed = self.engine.integrated_control_system.timing_controller.execute_pneumatic_control(
                self.engine.pneumatics, self.engine.floaters
            )
            control_output["pneumatic_executed"] = pneumatic_executed
        
        logger.debug(f"Control system updated: mode={control_output.get('control_mode', 'normal')}")
        return control_output

    def update_transient_events(self, system_state: Dict[str, Any], 
                               electrical_output: Dict[str, Any],
                               preliminary_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update transient event controller with comprehensive system state.
        
        Args:
            system_state: Basic system state
            electrical_output: Electrical system outputs
            preliminary_state: Preliminary drivetrain state
            
        Returns:
            Transient event commands
        """
        # Build comprehensive system state for transient event monitoring
        comprehensive_system_state = system_state.copy()
        comprehensive_system_state.update({
            "flywheel_speed_rpm": preliminary_state.get("gearbox", {}).get("output_speed_rpm", 0.0),
            "chain_speed_rpm": preliminary_state.get("sprocket", {}).get("top", {}).get("speed_rpm", 0.0),
            "torque": preliminary_state.get("gearbox", {}).get("output_torque", 0.0),
            "grid_voltage": electrical_output.get("grid_voltage", 480.0),
            "grid_frequency": electrical_output.get("grid_frequency", 60.0),
            "grid_connected": electrical_output.get("synchronized", False),
            "component_temperatures": {
                "sprocket": 20.0,
                "gearbox": 20.0,
                "clutch": 20.0,
                "flywheel": 20.0,
                "generator": 20.0,
            },
        })

        # Update transient event controller
        transient_commands = self.engine.transient_controller.update_transient_events(
            comprehensive_system_state, self.engine.time
        )
        
        logger.debug("Transient event controller updated")
        return transient_commands

    def update_enhanced_loss_model(self, final_output_torque: float, 
                                 final_output_speed: float,
                                 grid_power_output: float,
                                 electrical_output: Dict[str, Any],
                                 drivetrain_output: Dict[str, Any],
                                 dt: float) -> Dict[str, Any]:
        """
        Update the enhanced loss model with system performance data.
        
        Args:
            final_output_torque: Final drivetrain output torque
            final_output_speed: Final drivetrain output speed
            grid_power_output: Grid power output
            electrical_output: Electrical system outputs
            drivetrain_output: Drivetrain outputs
            dt: Time step
            
        Returns:
            Enhanced loss model state
        """
        enhanced_system_state = {
            "input_power": abs(final_output_torque * final_output_speed),
            "output_power": grid_power_output,
            "electrical_power": grid_power_output,
            "sprocket": {
                "torque": drivetrain_output.get("sprocket_torque", 0.0),
                "speed": drivetrain_output.get("chain_speed", 0.0),
                "load_factor": 0.5,
                "efficiency": 0.98,
            },
            "gearbox": {
                "torque": final_output_torque,
                "speed": final_output_speed,
                "load_factor": min(1.0, abs(final_output_torque) / 2000.0),
                "efficiency": drivetrain_output.get("gearbox_efficiency", 0.885),
            },
            "clutch": {
                "torque": final_output_torque,
                "speed": final_output_speed,
                "load_factor": min(1.0, abs(final_output_torque) / 2000.0),
                "efficiency": drivetrain_output.get("clutch_efficiency", 0.95),
            },
            "flywheel": {
                "torque": final_output_torque,
                "speed": final_output_speed,
                "load_factor": min(1.0, abs(final_output_torque) / 2000.0),
                "efficiency": drivetrain_output.get("flywheel_efficiency", 0.98),
            },
            "generator": {
                "torque": electrical_output.get("load_torque_command", 0.0),
                "speed": final_output_speed,
                "load_factor": electrical_output.get("load_factor", 0.0),
                "efficiency": electrical_output.get("system_efficiency", 0.0),
            },
            "electrical": {
                "current": grid_power_output / max(480.0, electrical_output.get("grid_voltage", 480.0)),
                "voltage": electrical_output.get("grid_voltage", 480.0),
                "frequency": electrical_output.get("grid_frequency", 60.0),
                "temperature": 40.0,  # Estimate electrical system temperature
                "switching_frequency": 5000.0,
                "flux_density": 1.0,
            },
        }
        
        enhanced_state = self.engine.enhanced_loss_model.update_system_losses(
            enhanced_system_state, dt
        )
        
        # Convert enhanced state to dict for schema compatibility
        if hasattr(enhanced_state, 'model_dump'):
            enhanced_state_dict = enhanced_state.model_dump()
        elif hasattr(enhanced_state, '__dict__'):
            enhanced_state_dict = enhanced_state.__dict__
        else:
            enhanced_state_dict = enhanced_state if isinstance(enhanced_state, dict) else {}
        
        logger.debug("Enhanced loss model updated")
        return enhanced_state_dict

    def update_grid_services(self, electrical_output: Dict[str, Any],
                           grid_power_output: float) -> Dict[str, Any]:
        """
        Update grid services coordinator with current grid conditions.
        
        Args:
            electrical_output: Electrical system outputs
            grid_power_output: Grid power output
            
        Returns:
            Grid services response
        """
        from simulation.grid_services import GridConditions
        
        # Build grid conditions for grid services
        grid_conditions = GridConditions(
            frequency=electrical_output.get("grid_frequency", 60.0),
            voltage=electrical_output.get("grid_voltage", 480.0),
            active_power=grid_power_output / 1000.0,  # Convert to MW
            reactive_power=electrical_output.get("reactive_power", 0.0) / 1000.0,  # Convert to MVAR
            grid_connected=electrical_output.get("synchronized", False),
            agc_signal=self.engine.params.get("agc_signal", 0.0),  # AGC regulation signal
            timestamp=self.engine.time,
        )

        # Get system rated power from parameters
        rated_power_mw = self.engine.params.get("rated_power_mw", 0.53)  # Default 530kW = 0.53MW

        # Update grid services coordinator
        grid_services_response = self.engine.grid_services_coordinator.update(
            grid_conditions, self.engine.dt, rated_power_mw
        )
        
        logger.debug("Grid services coordinator updated")
        return grid_services_response

    def execute_pneumatic_control(self, control_output: Dict[str, Any]) -> bool:
        """
        Execute pneumatic control commands if available.
        
        Args:
            control_output: Control system output
            
        Returns:
            True if pneumatic control was executed
        """
        return control_output.get("pneumatic_executed", False)

    def update_pneumatic_performance_tracking(self, dt: float) -> None:
        """
        Update pneumatic system performance tracking if available.
        
        Args:
            dt: Time step in seconds
        """
        if hasattr(self.engine, "pneumatic_coordinator") and hasattr(
            self.engine, "pneumatic_performance_analyzer"
        ):
            from config.config import RHO_WATER, G
            
            # Get pneumatic system data for performance tracking
            pneumatic_power = (
                getattr(self.engine.pneumatics, "compressor_power", 4200.0)
                if getattr(self.engine.pneumatics, "compressor_running", False)
                else 0.0
            )

            # Calculate mechanical power contribution from pneumatic system
            total_pneumatic_force = sum(
                f.compute_buoyant_force() - f.volume * RHO_WATER * G
                for f in self.engine.floaters
                if getattr(f, "is_filled", False)
            )
            chain_speed = getattr(
                self.engine.drivetrain, "omega_chain", 0.0
            ) * self.engine.params.get("sprocket_radius", 1.0)
            mechanical_power_from_pneumatics = total_pneumatic_force * chain_speed

            # Record performance snapshot if compressor is active
            if pneumatic_power > 0:
                avg_depth = (
                    sum(f.position for f in self.engine.floaters) / len(self.engine.floaters)
                    if self.engine.floaters
                    else 10.0
                )

                self.engine.pneumatic_performance_analyzer.record_performance_snapshot(
                    electrical_power=pneumatic_power,
                    mechanical_power=max(0, mechanical_power_from_pneumatics),
                    thermal_power=pneumatic_power * 0.05,  # Assume 5% thermal boost
                    compression_efficiency=0.85,  # Standard efficiency
                    expansion_efficiency=0.90,  # Standard efficiency
                    depth=avg_depth,
                )
                
                logger.debug("Pneumatic performance tracking updated")

    def update_systems(self, dt: float, physics_results: PhysicsResults) -> SystemResults:
        """
        Update all system components including drivetrain, electrical, control, and grid services.
        
        Args:
            dt: Time step in seconds
            physics_results: Results from physics calculations (Pydantic model)
            
        Returns:
            SystemResults containing all system update results
        """
        # Extract physics data from Pydantic model
        total_vertical_force = physics_results.total_vertical_force
        net_force = physics_results.net_force
        
        # 1. Calculate preliminary drivetrain torque for electrical system
        # Use the net force to calculate torque on the sprocket
        sprocket_radius = getattr(self.engine.top_sprocket, 'radius', 1.0)
        preliminary_torque = net_force * sprocket_radius
        
        # 2. Update electrical system to get load torque requirements
        # First get basic control commands
        basic_control = {"timing_commands": {}, "load_commands": {}}
        preliminary_speed = 0.0  # Will be calculated from drivetrain
        electrical_output = self.update_electrical_system(
            preliminary_torque, preliminary_speed, dt, basic_control
        )
        electrical_load_torque = electrical_output.electrical_load_torque
        
        # 3. Update drivetrain with actual electrical load
        drivetrain_output = self.update_drivetrain_with_load(electrical_load_torque, dt)
        
        # 4. Build system state for control system
        system_state = {
            "time": self.engine.time,
            "dt": dt,
            "total_vertical_force": total_vertical_force,
            "net_force": net_force,
            "preliminary_torque": preliminary_torque,
            "electrical_load_torque": electrical_load_torque,
            "drivetrain": drivetrain_output,
            "electrical": electrical_output.model_dump(),  # Convert to dict for backward compatibility
            "physics": physics_results,
        }
        
        # 5. Update control system
        control_output = self.update_control_system(system_state, dt)
        
        # 6. Update transient events
        preliminary_state = {"torque": preliminary_torque, "speed": preliminary_speed}
        transient_response = self.update_transient_events(system_state, electrical_output.model_dump(), preliminary_state)
        
        # 7. Update enhanced loss model
        final_torque = drivetrain_output.get("output_torque", preliminary_torque)
        final_speed = drivetrain_output.get("output_speed", preliminary_speed)
        grid_power = electrical_output.grid_power
        enhanced_losses = self.update_enhanced_loss_model(
            final_torque, final_speed, grid_power, electrical_output.model_dump(), drivetrain_output, dt
        )
        
        # 8. Update grid services
        grid_power = electrical_output.grid_power
        grid_response = self.update_grid_services(electrical_output.model_dump(), grid_power)
        
        # 9. Execute pneumatic control if needed
        pneumatic_executed = self.execute_pneumatic_control(control_output)
        
        # 10. Update pneumatic performance tracking
        self.update_pneumatic_performance_tracking(dt)
        
        # Combine all system results into Pydantic model
        system_results = SystemResults(
            drivetrain=self._convert_drivetrain_to_schema(drivetrain_output),
            electrical=self._convert_electrical_to_schema(electrical_output.model_dump()),
            control=self._convert_control_to_schema(control_output),
            transient=transient_response,
            enhanced_losses=enhanced_losses,
            grid_services=grid_response,
            pneumatic_executed=pneumatic_executed,
            final_torque=final_torque,
            electrical_load_torque=electrical_load_torque,
        )
        
        return system_results

    def _convert_drivetrain_to_schema(self, drivetrain_output: Dict[str, Any]):
        """Convert drivetrain output to DrivetrainData schema."""
        from ..schemas import DrivetrainData
        return DrivetrainData(
            flywheel_speed_rpm=drivetrain_output.get("flywheel_speed_rpm", 0.0),
            chain_speed_rpm=drivetrain_output.get("chain_speed_rpm", 0.0),
            input_torque=drivetrain_output.get("input_torque", 0.0),
            output_torque=drivetrain_output.get("output_torque", 0.0),
            load_torque=drivetrain_output.get("load_torque", 0.0),
            clutch_engaged=drivetrain_output.get("clutch_engaged", False),
            clutch_engagement=drivetrain_output.get("clutch_engagement", 0.0),
            system_efficiency=drivetrain_output.get("efficiency", 0.0)
        )
    
    def _convert_electrical_to_schema(self, electrical_output: Dict[str, Any]):
        """Convert electrical output to ElectricalData schema."""
        from ..schemas import ElectricalData
        return ElectricalData(
            power_output=electrical_output.get("power_output", 0.0),
            grid_power=electrical_output.get("grid_power", 0.0),
            load_torque=electrical_output.get("electrical_load_torque", 0.0),
            voltage=electrical_output.get("voltage", 480.0),
            frequency=electrical_output.get("frequency", 60.0),
            power_factor=electrical_output.get("power_factor", 0.95),
            reactive_power=electrical_output.get("reactive_power", 0.0),
            system_efficiency=electrical_output.get("system_efficiency", 0.0),
            synchronized=electrical_output.get("synchronized", False),
            load_factor=electrical_output.get("load_factor", 0.0)
        )
    
    def _convert_control_to_schema(self, control_output: Dict[str, Any]):
        """Convert control output to ControlData schema."""
        from ..schemas import ControlData
        return ControlData(
            timing_commands=control_output.get("timing_commands", {}),
            load_commands=control_output.get("load_commands", {}),
            grid_commands=control_output.get("grid_commands", {}),
            fault_status=control_output.get("fault_status", {}),
            performance_metrics=control_output.get("performance_metrics", {}),
            setpoints=control_output.get("setpoints", {}),
            feedback=control_output.get("feedback", {})
        )

    # ...existing methods...
