"""
Fault Detection and Recovery System for KPP Power System
Implements comprehensive system monitoring and protection.
"""

import logging
from collections import deque
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional

import numpy as np

logger = logging.getLogger(__name__)


class FaultSeverity(Enum):
    """Fault severity levels"""

    INFO = "info"
    WARNING = "warning"
    MINOR = "minor"
    MAJOR = "major"
    CRITICAL = "critical"


class FaultCategory(Enum):
    """Fault categories"""

    MECHANICAL = "mechanical"
    ELECTRICAL = "electrical"
    CONTROL = "control"
    COMMUNICATION = "communication"
    THERMAL = "thermal"
    SAFETY = "safety"


@dataclass
class SystemFault:
    """System fault information"""

    fault_id: str
    category: FaultCategory
    severity: FaultSeverity
    description: str
    start_time: float
    duration: float
    location: str
    parameters: Dict
    recovery_actions: List[str]
    auto_recovery_possible: bool


class FaultDetector:
    """
    Comprehensive fault detection and recovery system.

    Monitors all system components and provides:
    - Real-time fault detection
    - Fault classification and prioritization
    - Automatic recovery procedures
    - System health monitoring
    - Predictive maintenance alerts
    """

    def __init__(
        self,
        monitoring_interval: float = 0.1,
        fault_threshold_multiplier: float = 1.0,
        auto_recovery_enabled: bool = True,
        predictive_maintenance_enabled: bool = True,
    ):
        """
        Initialize fault detector.

        Args:
            monitoring_interval: Fault monitoring update interval (seconds)
            fault_threshold_multiplier: Threshold multiplier for sensitivity adjustment
            auto_recovery_enabled: Enable automatic fault recovery
            predictive_maintenance_enabled: Enable predictive maintenance monitoring
        """
        self.monitoring_interval = monitoring_interval
        self.fault_threshold_multiplier = fault_threshold_multiplier
        self.auto_recovery_enabled = auto_recovery_enabled
        self.predictive_maintenance_enabled = predictive_maintenance_enabled

        # Fault tracking
        self.active_faults: List[SystemFault] = []
        self.fault_history: deque = deque(maxlen=500)
        self.fault_statistics: Dict = {}

        # Monitoring thresholds
        self.thresholds = self._initialize_thresholds()

        # Component health tracking
        self.component_health: Dict[str, float] = {}
        self.health_trends: Dict[str, deque] = {}

        # Performance baselines
        self.performance_baselines: Dict = {}
        self.baseline_update_counter = 0

        # Fault detection algorithms
        self.fault_detectors = self._initialize_fault_detectors()

        # Recovery procedures
        self.recovery_procedures = self._initialize_recovery_procedures()

        # System state tracking
        self.last_system_state: Dict = {}
        self.state_change_rate: Dict = {}

        # Predictive maintenance
        self.maintenance_alerts: List[Dict] = []
        self.component_wear_tracking: Dict = {}

        # Timing
        self.current_time = 0.0
        self.last_update_time = 0.0

        logger.info(f"FaultDetector initialized with {len(self.fault_detectors)} detection algorithms")

    def update(self, system_state: Dict, dt: float) -> Dict:
        """
        Update fault detection and recovery system.

        Args:
            system_state: Current system state
            dt: Time step

        Returns:
            Fault detection results and recovery commands
        """
        self.current_time += dt

        # Update component health monitoring
        self._update_component_health(system_state)

        # Update performance baselines
        self._update_performance_baselines(system_state)

        # Run fault detection algorithms
        detected_faults = self._run_fault_detection(system_state, dt)

        # Process new faults
        new_faults = self._process_detected_faults(detected_faults)

        # Update existing faults
        self._update_existing_faults(dt)

        # Execute recovery procedures
        recovery_actions = self._execute_recovery_procedures(system_state)

        # Generate predictive maintenance alerts
        maintenance_alerts = self._generate_maintenance_alerts(system_state)

        # Update system health metrics
        system_health = self._calculate_system_health()

        # Generate fault summary
        fault_summary = self._generate_fault_summary()

        return {
            "fault_detector_output": {
                "new_faults": new_faults,
                "active_faults": len(self.active_faults),
                "recovery_actions": recovery_actions,
                "maintenance_alerts": maintenance_alerts,
                "system_health": system_health,
            },
            "fault_summary": fault_summary,
            "component_health": self.component_health.copy(),
            "critical_faults": [f for f in self.active_faults if f.severity == FaultSeverity.CRITICAL],
            "recovery_status": self._get_recovery_status(),
            "detector_status": self._get_detector_status(),
        }

    def _initialize_thresholds(self) -> Dict:
        """Initialize fault detection thresholds"""
        base_thresholds = {
            # Mechanical thresholds
            "chain_tension_max": 15000.0,  # N
            "chain_tension_min": 100.0,  # N
            "sprocket_speed_max": 500.0,  # RPM
            "gearbox_efficiency_min": 0.7,
            "clutch_slip_max": 0.2,
            "flywheel_speed_max": 400.0,  # RPM
            "vibration_max": 10.0,  # mm/s
            # Electrical thresholds
            "generator_efficiency_min": 0.7,
            "power_electronics_efficiency_min": 0.8,
            "grid_voltage_min": 432.0,  # V (90%)
            "grid_voltage_max": 528.0,  # V (110%)
            "grid_frequency_min": 59.0,  # Hz
            "grid_frequency_max": 61.0,  # Hz
            "power_factor_min": 0.8,
            "current_thd_max": 0.05,
            "voltage_thd_max": 0.03,
            # Thermal thresholds
            "generator_temp_max": 120.0,  # °C
            "gearbox_temp_max": 100.0,  # °C
            "power_electronics_temp_max": 85.0,  # °C
            "ambient_temp_max": 50.0,  # °C
            # Control thresholds
            "response_time_max": 1.0,  # seconds
            "control_error_max": 0.1,  # fraction
            "communication_timeout": 5.0,  # seconds
            # Performance thresholds
            "overall_efficiency_min": 0.6,
            "power_output_deviation_max": 0.2,  # 20%
            "stability_index_min": 0.7,
        }

        # Apply threshold multiplier
        thresholds = {}
        for key, value in base_thresholds.items():
            if "min" in key or "efficiency" in key:
                thresholds[key] = value / self.fault_threshold_multiplier
            else:
                thresholds[key] = value * self.fault_threshold_multiplier

        return thresholds

    def _initialize_fault_detectors(self) -> Dict:
        """Initialize fault detection algorithms"""
        return {
            "mechanical_fault_detector": MechanicalFaultDetector(self.thresholds),
            "electrical_fault_detector": ElectricalFaultDetector(self.thresholds),
            "thermal_fault_detector": ThermalFaultDetector(self.thresholds),
            "control_fault_detector": ControlFaultDetector(self.thresholds),
            "performance_fault_detector": PerformanceFaultDetector(self.thresholds),
            "safety_fault_detector": SafetyFaultDetector(self.thresholds),
        }

    def _initialize_recovery_procedures(self) -> Dict:
        """Initialize automatic recovery procedures"""
        return {
            "electrical_disconnect": {
                "triggers": ["critical_electrical_fault", "grid_fault"],
                "actions": ["disconnect_grid", "shutdown_generator"],
                "recovery_time": 10.0,
            },
            "mechanical_protection": {
                "triggers": ["overspeed", "excessive_vibration", "bearing_failure"],
                "actions": ["emergency_brake", "clutch_disengage"],
                "recovery_time": 5.0,
            },
            "thermal_protection": {
                "triggers": ["overtemperature"],
                "actions": ["reduce_load", "increase_cooling"],
                "recovery_time": 30.0,
            },
            "load_shedding": {
                "triggers": ["power_quality_fault", "grid_instability"],
                "actions": ["reduce_electrical_load", "improve_power_factor"],
                "recovery_time": 15.0,
            },
            "system_restart": {
                "triggers": ["multiple_critical_faults"],
                "actions": ["controlled_shutdown", "system_reset", "gradual_restart"],
                "recovery_time": 60.0,
            },
        }

    def _update_component_health(self, system_state: Dict):
        """Update component health monitoring"""

        # Extract component data
        components = {
            "floaters": self._assess_floater_health(system_state),
            "integrated_drivetrain": self._assess_drivetrain_health(system_state),
            "generator": self._assess_generator_health(system_state),
            "power_electronics": self._assess_power_electronics_health(system_state),
            "integrated_control_system": self._assess_control_health(system_state),
        }

        # Update health scores
        for component, health in components.items():
            self.component_health[component] = health

            # Track health trends
            if component not in self.health_trends:
                self.health_trends[component] = deque(maxlen=100)
            self.health_trends[component].append(health)

    def _assess_floater_health(self, system_state: Dict) -> float:
        """Assess floater system health"""
        floaters_data = system_state.get("floaters", [])
        if not floaters_data:
            return 0.5

        health_scores = []
        for floater in floaters_data:
            # Check for proper operation
            fill_efficiency = floater.get("fill_efficiency", 0.8)
            dissolution_rate = floater.get("dissolution_rate", 0.0)

            # Health based on efficiency and dissolution
            health = fill_efficiency * (1.0 - min(0.5, dissolution_rate * 10))
            health_scores.append(health)

        return float(np.mean(health_scores)) if health_scores else 0.5

    def _assess_drivetrain_health(self, system_state: Dict) -> float:
        """Assess mechanical integrated_drivetrain health"""
        drivetrain_output = system_state.get("drivetrain_output", {})

        # Check key integrated_drivetrain metrics
        efficiency = drivetrain_output.get("overall_efficiency", 0.8)
        vibration = drivetrain_output.get("vibration_level", 1.0)
        temperature = drivetrain_output.get("temperature", 60.0)

        # Calculate health score
        efficiency_score = min(1.0, efficiency / 0.85)
        vibration_score = max(0.0, 1.0 - vibration / 5.0)
        temperature_score = max(0.0, 1.0 - max(0, temperature - 80) / 40)

        health = (efficiency_score + vibration_score + temperature_score) / 3.0
        return max(0.0, min(1.0, health))

    def _assess_generator_health(self, system_state: Dict) -> float:
        """Assess generator health"""
        electrical_output = system_state.get("electrical_output", {})

        efficiency = electrical_output.get("generator_efficiency", 0.9)
        temperature = electrical_output.get("generator_temperature", 75.0)
        vibration = electrical_output.get("generator_vibration", 1.0)

        efficiency_score = min(1.0, efficiency / 0.92)
        temperature_score = max(0.0, 1.0 - max(0, temperature - 100) / 20)
        vibration_score = max(0.0, 1.0 - vibration / 3.0)

        health = (efficiency_score + temperature_score + vibration_score) / 3.0
        return max(0.0, min(1.0, health))

    def _assess_power_electronics_health(self, system_state: Dict) -> float:
        """Assess power electronics health"""
        electrical_output = system_state.get("electrical_output", {})

        efficiency = electrical_output.get("power_electronics_efficiency", 0.9)
        temperature = electrical_output.get("inverter_temperature", 60.0)
        thd = electrical_output.get("current_thd", 0.02)

        efficiency_score = min(1.0, efficiency / 0.9)
        temperature_score = max(0.0, 1.0 - max(0, temperature - 70) / 15)
        thd_score = max(0.0, 1.0 - thd / 0.05)

        health = (efficiency_score + temperature_score + thd_score) / 3.0
        return max(0.0, min(1.0, health))

    def _assess_control_health(self, system_state: Dict) -> float:
        """Assess control system health"""
        # Check control system responsiveness and accuracy
        control_error = system_state.get("control_error", 0.0)
        response_time = system_state.get("response_time", 0.1)
        communication_status = system_state.get("communication_ok", True)

        error_score = max(0.0, 1.0 - control_error / 0.1)
        response_score = max(0.0, 1.0 - max(0, response_time - 0.5) / 1.0)
        comm_score = 1.0 if communication_status else 0.0

        health = (error_score + response_score + comm_score) / 3.0
        return max(0.0, min(1.0, health))

    def _update_performance_baselines(self, system_state: Dict):
        """Update performance baselines for drift detection"""
        self.baseline_update_counter += 1

        # Update baselines every 100 iterations
        if self.baseline_update_counter % 100 == 0:
            key_metrics = {
                "power_output": system_state.get("power", 0.0),
                "overall_efficiency": system_state.get("overall_efficiency", 0.0),
                "chain_tension": system_state.get("chain_tension", 0.0),
                "generator_speed": system_state.get("flywheel_speed_rpm", 0.0),
            }

            for metric, value in key_metrics.items():
                if value > 0:  # Only update with valid data
                    if metric not in self.performance_baselines:
                        self.performance_baselines[metric] = deque(maxlen=50)
                    self.performance_baselines[metric].append(value)

    def _run_fault_detection(self, system_state: Dict, dt: float) -> List[Dict]:
        """Run all fault detection algorithms"""
        all_detected_faults = []

        for detector_name, detector in self.fault_detectors.items():
            try:
                detected_faults = detector.detect_faults(system_state, self.performance_baselines)
                for fault in detected_faults:
                    fault["detector"] = detector_name
                all_detected_faults.extend(detected_faults)
            except Exception as e:
                logger.error(f"Error in {detector_name}: {e}")

        return all_detected_faults

    def _process_detected_faults(self, detected_faults: List[Dict]) -> List[SystemFault]:
        """Process newly detected faults"""
        new_faults = []

        for fault_data in detected_faults:
            # Check if fault already exists
            existing_fault = self._find_existing_fault(fault_data["fault_id"])

            if existing_fault:
                # Update existing fault
                existing_fault.duration = self.current_time - existing_fault.start_time
                existing_fault.parameters.update(fault_data.get("parameters", {}))
            else:
                # Create new fault
                fault = SystemFault(
                    fault_id=fault_data["fault_id"],
                    category=FaultCategory(fault_data.get("category", "mechanical")),
                    severity=FaultSeverity(fault_data.get("severity", "minor")),
                    description=fault_data.get("description", "Unknown fault"),
                    start_time=self.current_time,
                    duration=0.0,
                    location=fault_data.get("location", "unknown"),
                    parameters=fault_data.get("parameters", {}),
                    recovery_actions=fault_data.get("recovery_actions", []),
                    auto_recovery_possible=fault_data.get("auto_recovery_possible", True),
                )

                self.active_faults.append(fault)
                new_faults.append(fault)

                logger.warning(f"New {fault.severity.value} fault detected: {fault.description}")

        return new_faults

    def _find_existing_fault(self, fault_id: str) -> Optional[SystemFault]:
        """Find existing fault by ID"""
        return next((f for f in self.active_faults if f.fault_id == fault_id), None)

    def _update_existing_faults(self, dt: float):
        """Update duration of existing faults and check for clearance"""
        cleared_faults = []

        for fault in self.active_faults:
            fault.duration += dt

            # Check if fault has been cleared (simplified logic)
            if self._is_fault_cleared(fault):
                cleared_faults.append(fault)
                self.fault_history.append(fault)
                logger.info(f"Fault cleared: {fault.description} (duration: {fault.duration:.1f}s)")

        # Remove cleared faults
        for fault in cleared_faults:
            self.active_faults.remove(fault)

    def _is_fault_cleared(self, fault: SystemFault) -> bool:
        """Check if a fault condition has been cleared"""
        # Simplified fault clearance logic
        # In practice, this would re-evaluate the specific fault condition

        # Auto-clear faults after reasonable time if no severe degradation
        if fault.severity in [FaultSeverity.INFO, FaultSeverity.WARNING]:
            return fault.duration > 10.0  # Clear minor faults after 10 seconds
        elif fault.severity == FaultSeverity.MINOR:
            return fault.duration > 30.0  # Clear minor faults after 30 seconds
        else:
            return False  # Major and critical faults require manual intervention

    def _execute_recovery_procedures(self, system_state: Dict) -> List[Dict]:
        """Execute automatic recovery procedures"""
        if not self.auto_recovery_enabled:
            return []

        recovery_actions = []

        # Check for recovery triggers
        for procedure_name, procedure in self.recovery_procedures.items():
            for fault in self.active_faults:
                fault_trigger = f"{fault.category.value}_{fault.severity.value}_fault"

                if fault_trigger in procedure["triggers"] or fault.fault_id in procedure["triggers"]:
                    # Execute recovery procedure
                    action = {
                        "procedure": procedure_name,
                        "fault_id": fault.fault_id,
                        "actions": procedure["actions"],
                        "estimated_recovery_time": procedure["recovery_time"],
                        "status": "initiated",
                    }
                    recovery_actions.append(action)

                    logger.info(f"Initiating recovery procedure '{procedure_name}' for fault {fault.fault_id}")

        return recovery_actions

    def _generate_maintenance_alerts(self, system_state: Dict) -> List[Dict]:
        """Generate predictive maintenance alerts"""
        if not self.predictive_maintenance_enabled:
            return []

        alerts = []

        # Check component health trends
        for component, health_trend in self.health_trends.items():
            if len(health_trend) >= 10:
                # Calculate health trend
                recent_health = list(health_trend)[-10:]
                health_slope = np.polyfit(range(10), recent_health, 1)[0]

                # Alert if health is declining
                if health_slope < -0.01:  # Declining by 1% per update
                    alert = {
                        "component": component,
                        "alert_type": "declining_health",
                        "current_health": health_trend[-1],
                        "trend_slope": health_slope,
                        "recommended_action": f"Schedule maintenance for {component}",
                        "urgency": "medium" if health_slope < -0.02 else "low",
                    }
                    alerts.append(alert)

        return alerts

    def _calculate_system_health(self) -> Dict:
        """Calculate overall system health metrics"""
        if not self.component_health:
            return {"overall": 0.5, "components": {}}

        # Weight components by criticality
        component_weights = {
            "floaters": 0.2,
            "integrated_drivetrain": 0.25,
            "generator": 0.25,
            "power_electronics": 0.2,
            "integrated_control_system": 0.1,
        }

        weighted_health = 0.0
        total_weight = 0.0

        for component, health in self.component_health.items():
            weight = component_weights.get(component, 0.1)
            weighted_health += health * weight
            total_weight += weight

        overall_health = weighted_health / total_weight if total_weight > 0 else 0.5

        # Adjust for active faults
        fault_penalty = len(self.active_faults) * 0.1
        critical_fault_penalty = len([f for f in self.active_faults if f.severity == FaultSeverity.CRITICAL]) * 0.3

        overall_health = max(0.0, overall_health - fault_penalty - critical_fault_penalty)

        return {
            "overall": overall_health,
            "components": self.component_health.copy(),
            "fault_impact": fault_penalty + critical_fault_penalty,
            "health_trend": self._calculate_health_trend(),
        }

    def _calculate_health_trend(self) -> str:
        """Calculate overall health trend"""
        if not self.component_health:
            return "unknown"

        # Simple trend calculation based on recent component health
        trends = []
        for component, health_deque in self.health_trends.items():
            if len(health_deque) >= 5:
                recent = list(health_deque)[-5:]
                trend = (recent[-1] - recent[0]) / 4  # Average change per update
                trends.append(trend)

        if not trends:
            return "stable"

        avg_trend = np.mean(trends)
        if avg_trend > 0.01:
            return "improving"
        elif avg_trend < -0.01:
            return "declining"
        else:
            return "stable"

    def _generate_fault_summary(self) -> Dict:
        """Generate fault summary report"""
        severity_counts = {severity: 0 for severity in FaultSeverity}
        category_counts = {category: 0 for category in FaultCategory}

        for fault in self.active_faults:
            severity_counts[fault.severity] += 1
            category_counts[fault.category] += 1

        return {
            "total_active_faults": len(self.active_faults),
            "severity_breakdown": {k.value: v for k, v in severity_counts.items()},
            "category_breakdown": {k.value: v for k, v in category_counts.items()},
            "critical_fault_ids": [f.fault_id for f in self.active_faults if f.severity == FaultSeverity.CRITICAL],
            "oldest_fault_duration": max([f.duration for f in self.active_faults], default=0.0),
            "recent_fault_rate": len(self.fault_history) / max(1, self.current_time / 3600),  # Faults per hour
        }

    def _get_recovery_status(self) -> Dict:
        """Get recovery system status"""
        return {
            "auto_recovery_enabled": self.auto_recovery_enabled,
            "active_recovery_procedures": 0,  # Would track active procedures
            "successful_recoveries": 0,  # Would track successful recoveries
            "failed_recoveries": 0,  # Would track failed recoveries
        }

    def _get_detector_status(self) -> Dict:
        """Get fault detector status"""
        return {
            "monitoring_interval": self.monitoring_interval,
            "active_detectors": len(self.fault_detectors),
            "detection_sensitivity": self.fault_threshold_multiplier,
            "predictive_maintenance_enabled": self.predictive_maintenance_enabled,
            "baseline_metrics_tracked": len(self.performance_baselines),
        }

    def reset(self):
        """Reset fault detector state"""
        self.active_faults.clear()
        self.fault_history.clear()
        self.component_health.clear()
        self.health_trends.clear()
        self.performance_baselines.clear()
        self.maintenance_alerts.clear()

        self.current_time = 0.0
        self.last_update_time = 0.0
        self.baseline_update_counter = 0

        logger.info("FaultDetector reset")


# Specialized fault detectors


class MechanicalFaultDetector:
    """Mechanical system fault detector"""

    def __init__(self, thresholds: Dict):
        self.thresholds = thresholds

    def detect_faults(self, system_state: Dict, baselines: Dict) -> List[Dict]:
        faults = []

        # Check chain tension
        chain_tension = system_state.get("chain_tension", 0.0)
        if chain_tension > self.thresholds["chain_tension_max"]:
            faults.append(
                {
                    "fault_id": "chain_tension_high",
                    "category": "mechanical",
                    "severity": "major",
                    "description": f"Chain tension too high: {chain_tension:.1f}N",
                    "location": "chain_system",
                }
            )

        # Check flywheel overspeed
        flywheel_speed = system_state.get("flywheel_speed_rpm", 0.0)
        if flywheel_speed > self.thresholds["flywheel_speed_max"]:
            faults.append(
                {
                    "fault_id": "flywheel_overspeed",
                    "category": "mechanical",
                    "severity": "critical",
                    "description": f"Flywheel overspeed: {flywheel_speed:.1f} RPM",
                    "location": "flywheel",
                }
            )

        return faults


class ElectricalFaultDetector:
    """Electrical system fault detector"""

    def __init__(self, thresholds: Dict):
        self.thresholds = thresholds

    def detect_faults(self, system_state: Dict, baselines: Dict) -> List[Dict]:
        faults = []

        electrical_output = system_state.get("electrical_output", {})

        # Check grid voltage
        grid_voltage = electrical_output.get("grid_voltage", 480.0)
        if not (self.thresholds["grid_voltage_min"] <= grid_voltage <= self.thresholds["grid_voltage_max"]):
            faults.append(
                {
                    "fault_id": "grid_voltage_fault",
                    "category": "electrical",
                    "severity": "major",
                    "description": f"Grid voltage out of range: {grid_voltage:.1f}V",
                    "location": "grid_interface",
                }
            )

        # Check generator efficiency
        gen_efficiency = electrical_output.get("generator_efficiency", 0.9)
        if gen_efficiency < self.thresholds["generator_efficiency_min"]:
            faults.append(
                {
                    "fault_id": "generator_efficiency_low",
                    "category": "electrical",
                    "severity": "minor",
                    "description": f"Generator efficiency low: {gen_efficiency:.3f}",
                    "location": "generator",
                }
            )

        return faults


class ThermalFaultDetector:
    """Thermal system fault detector"""

    def __init__(self, thresholds: Dict):
        self.thresholds = thresholds

    def detect_faults(self, system_state: Dict, baselines: Dict) -> List[Dict]:
        faults = []

        electrical_output = system_state.get("electrical_output", {})

        # Check generator temperature
        gen_temp = electrical_output.get("generator_temperature", 75.0)
        if gen_temp > self.thresholds["generator_temp_max"]:
            faults.append(
                {
                    "fault_id": "generator_overtemp",
                    "category": "thermal",
                    "severity": "major" if gen_temp > 130 else "minor",
                    "description": f"Generator overtemperature: {gen_temp:.1f}°C",
                    "location": "generator",
                }
            )

        return faults


class ControlFaultDetector:
    """Control system fault detector"""

    def __init__(self, thresholds: Dict):
        self.thresholds = thresholds

    def detect_faults(self, system_state: Dict, baselines: Dict) -> List[Dict]:
        faults = []

        # Check control response
        response_time = system_state.get("response_time", 0.1)
        if response_time > self.thresholds["response_time_max"]:
            faults.append(
                {
                    "fault_id": "control_response_slow",
                    "category": "control",
                    "severity": "minor",
                    "description": f"Control response slow: {response_time:.2f}s",
                    "location": "integrated_control_system",
                }
            )

        return faults


class PerformanceFaultDetector:
    """Performance degradation fault detector"""

    def __init__(self, thresholds: Dict):
        self.thresholds = thresholds

    def detect_faults(self, system_state: Dict, baselines: Dict) -> List[Dict]:
        faults = []

        # Check overall efficiency
        efficiency = system_state.get("overall_efficiency", 0.8)
        if efficiency < self.thresholds["overall_efficiency_min"]:
            faults.append(
                {
                    "fault_id": "system_efficiency_low",
                    "category": "electrical",  # Use valid category
                    "severity": "minor",
                    "description": f"System efficiency low: {efficiency:.3f}",
                    "location": "system",
                }
            )

        return faults


class SafetyFaultDetector:
    """Safety system fault detector"""

    def __init__(self, thresholds: Dict):
        self.thresholds = thresholds

    def detect_faults(self, system_state: Dict, baselines: Dict) -> List[Dict]:
        faults = []

        # Check emergency conditions
        emergency_stop = system_state.get("emergency_stop_active", False)
        if emergency_stop:
            faults.append(
                {
                    "fault_id": "emergency_stop_active",
                    "category": "safety",
                    "severity": "critical",
                    "description": "Emergency stop activated",
                    "location": "safety_system",
                }
            )

        return faults
