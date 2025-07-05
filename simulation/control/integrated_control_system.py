"""
Integrated Control System for KPP Power Generation
Combines all Phase 4 advanced control components into a unified system.
"""

import logging
from collections import deque
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np

from .fault_detector import FaultDetector, FaultSeverity
from .grid_stability_controller import GridStabilityController, GridStabilityMode
from .load_manager import LoadManager, LoadProfile
from .timing_controller import TimingController

# Import new config system with backward compatibility
try:
    from config import ControlSystemConfig
    NEW_CONFIG_AVAILABLE = True
except ImportError:
    NEW_CONFIG_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class LegacyControlSystemConfig:
    """Legacy configuration for integrated control system (for backward compatibility)"""

    # Timing controller config
    num_floaters: int = 8
    prediction_horizon: float = 5.0
    optimization_window: float = 2.0

    # Load manager config
    target_power: float = 530000.0  # 530 kW (aligned with modular config)
    power_tolerance: float = 0.05  # 5%
    max_ramp_rate: float = 50000.0  # 50 kW/s

    # Grid stability config
    nominal_voltage: float = 480.0
    nominal_frequency: float = 50.0
    voltage_regulation_band: float = 0.05
    frequency_regulation_band: float = 0.1

    # Fault detector config
    monitoring_interval: float = 0.1
    auto_recovery_enabled: bool = True
    predictive_maintenance_enabled: bool = True

    # Control coordination config
    control_priority_weights: Optional[Dict[str, float]] = None
    emergency_response_enabled: bool = True
    adaptive_control_enabled: bool = True


class IntegratedControlSystem:
    """
    Integrated advanced control system for KPP power generation.

    Coordinates and manages:
    - Timing optimization controller
    - Load management system
    - Grid stability controller
    - Fault detection and recovery

    Provides unified control with prioritized decision making and
    coordinated response to system conditions.
    """

    def __init__(self, config: Union[ControlSystemConfig, "LegacyControlSystemConfig"]):
        """
        Initialize integrated control system.

        Args:
            config: Control system configuration (new or legacy format)
        """
        self.config = config
        
        # Handle both new and legacy config formats
        if NEW_CONFIG_AVAILABLE and isinstance(config, ControlSystemConfig):
            # New config format
            self._init_with_new_config(config)
        else:
            # Legacy config format
            self._init_with_legacy_config(config)

    def _init_with_new_config(self, config: ControlSystemConfig):
        """Initialize with new config format"""
        # Initialize control components
        self.timing_controller = TimingController(
            num_floaters=config.timing.num_floaters,
            prediction_horizon=config.timing.prediction_horizon,
            optimization_window=config.timing.optimization_window,
        )

        self.load_manager = LoadManager(
            target_power=config.load_manager.target_power,
            power_tolerance=config.load_manager.power_tolerance,
            max_ramp_rate=config.load_manager.max_ramp_rate,
        )

        self.grid_stability_controller = GridStabilityController(
            rated_power=config.load_manager.target_power,
            nominal_voltage=config.grid_stability.nominal_voltage,
            nominal_frequency=config.grid_stability.nominal_frequency,
            voltage_regulation_band=config.grid_stability.voltage_regulation_band,
            frequency_regulation_band=config.grid_stability.frequency_regulation_band,
        )

        self.fault_detector = FaultDetector(
            monitoring_interval=config.fault_detector.monitoring_interval,
            auto_recovery_enabled=config.fault_detector.auto_recovery_enabled,
            predictive_maintenance_enabled=config.fault_detector.predictive_maintenance_enabled,
        )

        # Initialize common components
        self._init_common_components(config)

    def _init_with_legacy_config(self, config: "LegacyControlSystemConfig"):
        """Initialize with legacy config format"""
        # Initialize control components
        self.timing_controller = TimingController(
            num_floaters=config.num_floaters,
            prediction_horizon=config.prediction_horizon,
            optimization_window=config.optimization_window,
        )

        self.load_manager = LoadManager(
            target_power=config.target_power,
            power_tolerance=config.power_tolerance,
            max_ramp_rate=config.max_ramp_rate,
        )

        self.grid_stability_controller = GridStabilityController(
            rated_power=config.target_power,
            nominal_voltage=config.nominal_voltage,
            nominal_frequency=config.nominal_frequency,
            voltage_regulation_band=config.voltage_regulation_band,
            frequency_regulation_band=config.frequency_regulation_band,
        )

        self.fault_detector = FaultDetector(
            monitoring_interval=config.monitoring_interval,
            auto_recovery_enabled=config.auto_recovery_enabled,
            predictive_maintenance_enabled=config.predictive_maintenance_enabled,
        )

        # Initialize common components
        self._init_common_components(config)

    def _init_common_components(self, config):
        """Initialize components common to both config formats"""
        # Control coordination
        self.control_priorities = config.control_priority_weights or {
            "safety": 1.0,
            "fault_response": 0.9,
            "grid_stability": 0.8,
            "load_management": 0.7,
            "timing_optimization": 0.6,
            "efficiency_optimization": 0.5,
        }
        # System state
        self.current_time = 0.0
        self.system_mode = "normal"
        self.control_mode = "automatic"  # Add missing control_mode
        self.power_setpoint = 0.0  # Add missing power_setpoint
        self.control_output = 0.0  # Add missing control_output
        self.emergency_response_active = False
        self.adaptive_control_active = config.adaptive_control_enabled

        # Performance tracking
        self.control_performance: deque = deque(maxlen=100)
        self.system_stability_history: deque = deque(maxlen=200)
        self.efficiency_history: deque = deque(maxlen=100)

        # Control outputs
        self.last_control_outputs = {}
        self.control_override_active = False

        # Coordination algorithms
        self.decision_arbitrator = ControlDecisionArbitrator(self.control_priorities)
        self.adaptive_tuner = (
            AdaptiveControlTuner() if config.adaptive_control_enabled else None
        )

        logger.info(
            f"IntegratedControlSystem initialized with {len(self.control_priorities)} control priorities"
        )

    def update(self, system_state: Dict, dt: float) -> Dict:
        """
        Update integrated control system.

        Args:
            system_state: Current system state
            dt: Time step

        Returns:
            Unified control commands and system status
        """
        self.current_time += dt

        # Update all control components
        control_outputs = self._update_control_components(system_state, dt)

        # Detect and respond to emergencies
        emergency_status = self._handle_emergency_conditions(control_outputs)

        # Coordinate control decisions
        coordinated_commands = self._coordinate_control_decisions(
            control_outputs, system_state
        )

        # Apply adaptive control adjustments
        if self.adaptive_control_active:
            coordinated_commands = self._apply_adaptive_control(
                coordinated_commands, system_state
            )

        # Update performance tracking
        self._update_performance_tracking(system_state, coordinated_commands)

        # Generate system status
        system_status = self._generate_system_status(control_outputs, emergency_status)

        return {
            "integrated_control_output": coordinated_commands,
            "control_components_status": control_outputs,
            "emergency_status": emergency_status,
            "system_mode": self.system_mode,
            "system_health": self._calculate_system_health(control_outputs),
            "control_performance": self._get_control_performance(),
            "system_status": system_status,
        }

    def _update_control_components(self, system_state: Dict, dt: float) -> Dict:
        """Update all individual control components"""
        outputs = {}

        try:
            # Update timing controller
            outputs["timing_controller"] = self.timing_controller.update(
                system_state, dt
            )
        except Exception as e:
            logger.error(f"Timing controller error: {e}")
            outputs["timing_controller"] = {"error": str(e)}

        try:
            # Update load manager
            outputs["load_manager"] = self.load_manager.update(system_state, dt)
        except Exception as e:
            logger.error(f"Load manager error: {e}")
            outputs["load_manager"] = {"error": str(e)}

        try:
            # Update grid stability controller
            outputs["grid_stability"] = self.grid_stability_controller.update(
                system_state, dt
            )
        except Exception as e:
            logger.error(f"Grid stability controller error: {e}")
            outputs["grid_stability"] = {"error": str(e)}

        try:
            # Update fault detector
            outputs["fault_detector"] = self.fault_detector.update(system_state, dt)
        except Exception as e:
            logger.error(f"Fault detector error: {e}")
            outputs["fault_detector"] = {"error": str(e)}

        return outputs

    def _handle_emergency_conditions(self, control_outputs: Dict) -> Dict:
        """Handle emergency conditions and safety responses"""
        emergency_status = {
            "emergency_active": False,
            "emergency_type": None,
            "response_actions": [],
            "estimated_recovery_time": 0.0,
        }

        # Check for critical faults
        fault_output = control_outputs.get("fault_detector", {})
        critical_faults = fault_output.get("critical_faults", [])

        if critical_faults:
            emergency_status.update(
                {
                    "emergency_active": True,
                    "emergency_type": "critical_fault",
                    "response_actions": ["emergency_shutdown", "isolate_faults"],
                    "estimated_recovery_time": 300.0,  # 5 minutes
                }
            )
            self.system_mode = "emergency"
            self.emergency_response_active = True
            logger.critical(
                f"Emergency: {len(critical_faults)} critical faults detected"
            )

        # Check for grid stability emergencies
        grid_output = control_outputs.get("grid_stability", {})
        grid_mode = grid_output.get("operating_mode", "normal")

        if grid_mode == "emergency_disconnect":
            emergency_status.update(
                {
                    "emergency_active": True,
                    "emergency_type": "grid_emergency",
                    "response_actions": [
                        "disconnect_grid",
                        "maintain_islanded_operation",
                    ],
                    "estimated_recovery_time": 120.0,  # 2 minutes
                }
            )
            self.system_mode = "grid_emergency"
            logger.critical("Emergency: Grid disconnection required")

        # Check for load management emergencies
        load_output = control_outputs.get("load_manager", {})
        emergency_load_reduction = load_output.get("load_manager_output", {}).get(
            "emergency_load_reduction", 0.0
        )

        if emergency_load_reduction > 0.5:  # >50% load reduction
            emergency_status.update(
                {
                    "emergency_active": True,
                    "emergency_type": "load_emergency",
                    "response_actions": ["reduce_power_output", "stabilize_system"],
                    "estimated_recovery_time": 60.0,  # 1 minute
                }
            )
            if self.system_mode == "normal":
                self.system_mode = "load_emergency"
            logger.warning(
                f"Emergency: {emergency_load_reduction*100:.1f}% load reduction active"
            )

        # Recovery check
        if not emergency_status["emergency_active"] and self.emergency_response_active:
            self.emergency_response_active = False
            self.system_mode = "recovery"
            logger.info("Emergency conditions cleared, entering recovery mode")

        # Normal operation check
        if self.system_mode == "recovery" and self._check_system_stable(
            control_outputs
        ):
            self.system_mode = "normal"
            logger.info("System recovered, returning to normal operation")

        return emergency_status

    def _coordinate_control_decisions(
        self, control_outputs: Dict, system_state: Dict
    ) -> Dict:
        """Coordinate control decisions using priority-based arbitration"""

        # Extract control commands from each component
        timing_commands = control_outputs.get("timing_controller", {}).get(
            "timing_controller_output", {}
        )
        load_commands = control_outputs.get("load_manager", {}).get(
            "load_manager_output", {}
        )
        grid_commands = control_outputs.get("grid_stability", {}).get(
            "grid_stability_output", {}
        )
        fault_commands = control_outputs.get("fault_detector", {}).get(
            "fault_detector_output", {}
        )

        # Use decision arbitrator to coordinate commands
        coordinated_commands = self.decision_arbitrator.arbitrate_decisions(
            timing_commands=timing_commands,
            load_commands=load_commands,
            grid_commands=grid_commands,
            fault_commands=fault_commands,
            system_state=system_state,
            emergency_active=self.emergency_response_active,
        )

        # Apply emergency overrides if needed
        if self.emergency_response_active:
            coordinated_commands = self._apply_emergency_overrides(
                coordinated_commands, control_outputs
            )

        return coordinated_commands

    def _apply_emergency_overrides(self, commands: Dict, control_outputs: Dict) -> Dict:
        """Apply emergency overrides to control commands"""
        emergency_commands = commands.copy()

        if self.system_mode == "emergency":
            # Critical fault response
            emergency_commands.update(
                {
                    "emergency_shutdown": True,
                    "target_load_factor": 0.0,
                    "grid_connection_enable": False,
                    "injection_command": False,
                }
            )

        elif self.system_mode == "grid_emergency":
            # Grid emergency response
            emergency_commands.update(
                {
                    "grid_connection_enable": False,
                    "target_load_factor": 0.5,  # Reduce to 50% for island operation
                    "voltage_reference": 480.0,
                    "frequency_reference": 50.0,
                }
            )

        elif self.system_mode == "load_emergency":
            # Load emergency response
            emergency_commands.update(
                {
                    "target_load_factor": min(
                        0.3, commands.get("target_load_factor", 0.5)
                    ),
                    "ramp_rate": commands.get("ramp_rate", 10000)
                    * 2,  # Faster response
                }
            )

        return emergency_commands

    def _apply_adaptive_control(self, commands: Dict, system_state: Dict) -> Dict:
        """Apply adaptive control adjustments"""
        if not self.adaptive_tuner:
            return commands

        # Apply adaptive tuning based on system performance
        adaptive_adjustments = self.adaptive_tuner.calculate_adjustments(
            commands, system_state, self.control_performance
        )

        # Merge adaptive adjustments
        adapted_commands = commands.copy()
        adapted_commands.update(adaptive_adjustments)

        return adapted_commands

    def _check_system_stable(self, control_outputs: Dict) -> bool:
        """Check if system is stable and ready for normal operation"""

        # Check fault status
        fault_output = control_outputs.get("fault_detector", {})
        active_faults = fault_output.get("fault_detector_output", {}).get(
            "active_faults", 0
        )
        if active_faults > 2:  # More than 2 active faults
            return False

        # Check grid stability
        grid_output = control_outputs.get("grid_stability", {})
        grid_stability = grid_output.get("overall_stability_index", 0.0)
        if grid_stability < 0.8:
            return False

        # Check load management
        load_output = control_outputs.get("load_manager", {})
        power_error = load_output.get("power_error", 0.0)
        if power_error > self._get_target_power() * 0.2:  # >20% power error
            return False

        return True

    def _update_performance_tracking(self, system_state: Dict, commands: Dict):
        """Update control performance tracking"""

        # Calculate control performance metrics
        power_error = abs(system_state.get("power", 0.0) - self._get_target_power())
        efficiency = system_state.get("overall_efficiency", 0.0)
        stability_index = system_state.get("stability_index", 1.0)

        performance_metrics = {
            "time": self.current_time,
            "power_error": power_error,
            "efficiency": efficiency,
            "stability_index": stability_index,
            "system_mode": self.system_mode,
            "emergency_active": self.emergency_response_active,
        }

        self.control_performance.append(performance_metrics)

        # Track system stability
        self.system_stability_history.append(
            {
                "time": self.current_time,
                "stability": stability_index,
                "mode": self.system_mode,
            }
        )

        # Track efficiency
        if efficiency > 0:
            self.efficiency_history.append(
                {"time": self.current_time, "efficiency": efficiency}
            )

    def _calculate_system_health(self, control_outputs: Dict) -> Dict:
        """Calculate overall system health from control outputs"""

        # Component health scores
        health_scores = {}

        # Fault detector health
        fault_output = control_outputs.get("fault_detector", {})
        fault_health = fault_output.get("fault_detector_output", {}).get(
            "system_health", {}
        )
        health_scores["fault_system"] = fault_health.get("overall", 0.5)

        # Grid stability health
        grid_output = control_outputs.get("grid_stability", {})
        health_scores["grid_stability"] = grid_output.get(
            "overall_stability_index", 0.5
        )

        # Load management health
        load_output = control_outputs.get("load_manager", {})
        load_efficiency = load_output.get("efficiency_optimization", 0.5)
        health_scores["load_management"] = load_efficiency

        # Timing controller health
        timing_output = control_outputs.get("timing_controller", {})
        timing_confidence = timing_output.get("timing_confidence", 0.5)
        health_scores["timing_control"] = timing_confidence

        # Calculate weighted overall health
        weights = {
            "fault_system": 0.3,
            "grid_stability": 0.3,
            "load_management": 0.2,
            "timing_control": 0.2,
        }
        overall_health = sum(
            health_scores.get(comp, 0.5) * weight for comp, weight in weights.items()
        )

        return {
            "overall_health": overall_health,
            "component_health": health_scores,
            "health_trend": self._calculate_health_trend(),
        }

    def _calculate_health_trend(self) -> str:
        """Calculate health trend based on recent performance"""
        if len(self.control_performance) < 10:
            return "unknown"

        recent_efficiency = [
            p["efficiency"] for p in list(self.control_performance)[-10:]
        ]
        recent_stability = [
            p["stability_index"] for p in list(self.control_performance)[-10:]
        ]

        # Calculate trends
        eff_trend = (
            np.polyfit(range(10), recent_efficiency, 1)[0] if recent_efficiency else 0
        )
        stab_trend = (
            np.polyfit(range(10), recent_stability, 1)[0] if recent_stability else 0
        )

        avg_trend = (eff_trend + stab_trend) / 2

        if avg_trend > 0.001:
            return "improving"
        elif avg_trend < -0.001:
            return "declining"
        else:
            return "stable"

    def _get_control_performance(self) -> Dict:
        """Get control performance metrics"""
        if not self.control_performance:
            return {"average_efficiency": 0.0, "average_stability": 0.0, "uptime": 0.0}

        recent_performance = list(self.control_performance)[-20:]  # Last 20 updates

        avg_efficiency = np.mean([p["efficiency"] for p in recent_performance])
        avg_stability = np.mean([p["stability_index"] for p in recent_performance])

        # Calculate uptime (time not in emergency mode)
        normal_time = sum(1 for p in recent_performance if p["system_mode"] == "normal")
        uptime = normal_time / len(recent_performance) if recent_performance else 0.0

        return {
            "average_efficiency": avg_efficiency,
            "average_stability": avg_stability,
            "uptime": uptime,
            "emergency_events": sum(
                1 for p in recent_performance if p["emergency_active"]
            ),
            "mode_distribution": self._get_mode_distribution(recent_performance),
        }

    def _get_mode_distribution(self, performance_data: List[Dict]) -> Dict:
        """Get distribution of system modes"""
        mode_counts = {}
        for p in performance_data:
            mode = p["system_mode"]
            mode_counts[mode] = mode_counts.get(mode, 0) + 1

        total = len(performance_data)
        return (
            {mode: count / total for mode, count in mode_counts.items()}
            if total > 0
            else {}
        )

    def _generate_system_status(
        self, control_outputs: Dict, emergency_status: Dict
    ) -> Dict:
        """Generate comprehensive system status"""
        return {
            "integrated_control_active": True,
            "system_mode": self.system_mode,
            "emergency_response_active": self.emergency_response_active,
            "adaptive_control_active": self.adaptive_control_active,
            "control_components_operational": len(
                [c for c in control_outputs.values() if "error" not in c]
            ),
            "total_control_components": len(control_outputs),
            "system_uptime": self.current_time,
            "last_emergency": emergency_status.get("emergency_type", "none"),
            "control_override_active": self.control_override_active,
        }

    def set_emergency_mode(self, emergency_type: str):
        """Manually set emergency mode"""
        self.system_mode = "emergency"
        self.emergency_response_active = True
        logger.critical(f"Manual emergency mode activated: {emergency_type}")

    def clear_emergency_mode(self):
        """Manually clear emergency mode"""
        self.emergency_response_active = False
        self.system_mode = "recovery"
        logger.info("Emergency mode manually cleared")

    def adjust_target_power(self, new_target: float):
        """Adjust target power for all relevant controllers"""
        # Update config based on format
        if NEW_CONFIG_AVAILABLE and hasattr(self.config, 'load_manager'):
            self.config.load_manager.target_power = new_target
        else:
            self.config.target_power = new_target
        self.load_manager.adjust_target_power(new_target)
        logger.info(f"Target power adjusted to {new_target/1000:.1f}kW")

    def add_load_profile(self, profile: LoadProfile):
        """Add load profile to load manager"""
        self.load_manager.add_load_profile(profile)

    def reset(self):
        """Reset all control components"""
        self.timing_controller.reset()
        self.load_manager.reset()
        self.grid_stability_controller.reset()
        self.fault_detector.reset()

        self.current_time = 0.0
        self.system_mode = "normal"
        self.emergency_response_active = False

        self.control_performance.clear()
        self.system_stability_history.clear()
        self.efficiency_history.clear()

        logger.info("IntegratedControlSystem reset")

    def get_status(self) -> Dict[str, Any]:
        """
        Get current status of the integrated control system

        Returns:
            Dict containing current control system status data
        """
        return {
            "mode": self.control_mode,
            "setpoint": self.power_setpoint,
            "output": self.control_output,
            "timing_status": getattr(self.timing_controller, "get_state", lambda: {})(),
            "load_management": {
                "target_power": self.load_manager.target_power,
                "current_power": getattr(self.load_manager, "current_power", 0.0),
                "power_error": getattr(self.load_manager, "power_error", 0.0),
            },
            "grid_stability": {
                "voltage_regulation": getattr(
                    self.grid_stability_controller, "voltage_regulation_active", False
                ),
                "frequency_regulation": getattr(
                    self.grid_stability_controller, "frequency_regulation_active", False
                ),
                "grid_compliance": getattr(
                    self.grid_stability_controller, "grid_compliance", True
                ),
            },
            "fault_status": {
                "active_faults": getattr(self.fault_detector, "active_faults", []),
                "fault_count": getattr(self.fault_detector, "total_faults_detected", 0),
                "system_health": getattr(
                    self.fault_detector, "system_health_score", 1.0
                ),
            },
            "performance": {
                "efficiency": getattr(self, "system_efficiency", 0.0),
                "power_factor": getattr(self, "power_factor", 0.95),
                "uptime": getattr(self, "uptime_hours", 0.0),
            },
        }

    def _get_target_power(self):
        """Get target power from config, supporting both legacy and modular config."""
        if NEW_CONFIG_AVAILABLE and hasattr(self.config, 'load_manager'):
            return self.config.load_manager.target_power
        return self.config.target_power


class ControlDecisionArbitrator:
    """Arbitrates between conflicting control decisions"""

    def __init__(self, priorities: Dict[str, float]):
        self.priorities = priorities

    def arbitrate_decisions(
        self,
        timing_commands: Dict,
        load_commands: Dict,
        grid_commands: Dict,
        fault_commands: Dict,
        system_state: Dict,
        emergency_active: bool,
    ) -> Dict:
        """Arbitrate between control commands using priority weights"""

        # Start with default commands
        arbitrated_commands = {
            "injection_command": False,
            "target_floater_id": None,
            "target_load_factor": 0.5,
            "grid_connection_enable": True,
            "emergency_shutdown": False,
        }

        # Apply commands in priority order
        command_sources = [
            ("fault_response", fault_commands),
            ("grid_stability", grid_commands),
            ("load_management", load_commands),
            ("timing_optimization", timing_commands),
        ]

        # Sort by priority
        command_sources.sort(key=lambda x: self.priorities.get(x[0], 0.0), reverse=True)

        # Apply commands in priority order
        for source_name, commands in command_sources:
            if commands and not commands.get("error"):
                # Apply non-conflicting commands
                for key, value in commands.items():
                    if key not in arbitrated_commands or value is not None:
                        arbitrated_commands[key] = value

        # Emergency override
        if emergency_active:
            arbitrated_commands["emergency_shutdown"] = True
            arbitrated_commands["target_load_factor"] = 0.0

        return arbitrated_commands


class AdaptiveControlTuner:
    """Adaptive control parameter tuning"""

    def __init__(self):
        self.learning_rate = 0.01
        self.performance_history = deque(maxlen=50)

    def calculate_adjustments(
        self, commands: Dict, system_state: Dict, performance_history: deque
    ) -> Dict:
        """Calculate adaptive adjustments to control parameters"""

        adjustments = {}

        # Simple adaptive logic - adjust based on recent performance
        if len(performance_history) >= 10:
            recent_efficiency = [
                p["efficiency"] for p in list(performance_history)[-10:]
            ]
            avg_efficiency = np.mean(recent_efficiency)

            # If efficiency is declining, make conservative adjustments
            if avg_efficiency < 0.7:
                # Reduce target load factor slightly
                current_load = commands.get("target_load_factor", 0.5)
                adjustments["target_load_factor"] = max(0.1, current_load * 0.95)

                # Reduce ramp rate for smoother operation
                current_ramp = commands.get("ramp_rate", 10000)
                adjustments["ramp_rate"] = current_ramp * 0.9

        return adjustments


def create_standard_kpp_control_system(
    config_overrides: Optional[Dict] = None,
    use_new_config: bool = True,
) -> IntegratedControlSystem:
    """
    Create a standard KPP integrated control system with default configuration.

    Args:
        config_overrides: Optional configuration overrides
        use_new_config: Whether to use new config system (default: True)

    Returns:
        Configured IntegratedControlSystem
    """

    if NEW_CONFIG_AVAILABLE and use_new_config:
        # Use new config system
        config = ControlSystemConfig()
        
        # Apply overrides to new config structure
        if config_overrides:
            # Handle nested overrides
            for key, value in config_overrides.items():
                if hasattr(config, key):
                    if isinstance(value, dict) and hasattr(getattr(config, key), 'to_dict'):
                        # Nested config override
                        current_config = getattr(config, key)
                        for subkey, subvalue in value.items():
                            if hasattr(current_config, subkey):
                                setattr(current_config, subkey, subvalue)
                    else:
                        # Direct attribute override
                        setattr(config, key, value)
    else:
        # Use legacy config system
        config = LegacyControlSystemConfig(
            num_floaters=8,
            prediction_horizon=5.0,
            optimization_window=2.0,
            target_power=530000.0,  # 530 kW to match Phase 3
            power_tolerance=0.05,
            max_ramp_rate=50000.0,
            nominal_voltage=480.0,
            nominal_frequency=50.0,
            voltage_regulation_band=0.05,
            frequency_regulation_band=0.1,
            monitoring_interval=0.1,
            auto_recovery_enabled=True,
            predictive_maintenance_enabled=True,
            emergency_response_enabled=True,
            adaptive_control_enabled=True,
        )

        # Apply overrides
        if config_overrides:
            for key, value in config_overrides.items():
                if hasattr(config, key):
                    setattr(config, key, value)

    return IntegratedControlSystem(config)
