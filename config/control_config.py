"""
Control System Configuration
Defines configuration for the KPP integrated control system.
"""

from dataclasses import dataclass, field
from typing import Dict

from .core.base_config import BaseConfig
from .core.validation import ConfigValidator


@dataclass
class TimingControllerConfig(BaseConfig):
    """Configuration for timing controller"""

    num_floaters: int = 8
    prediction_horizon: float = 5.0
    optimization_window: float = 2.0

    def validate(self) -> bool:
        """Validate timing controller configuration"""
        validator = ConfigValidator()

        validator.check_positive_int(self.num_floaters, "num_floaters")
        validator.check_positive_float(self.prediction_horizon, "prediction_horizon")
        validator.check_positive_float(self.optimization_window, "optimization_window")
        validator.check_range(self.num_floaters, 1, 20, "num_floaters")
        validator.check_range(self.prediction_horizon, 0.1, 30.0, "prediction_horizon")
        validator.check_range(self.optimization_window, 0.1, 10.0, "optimization_window")

        return validator.is_valid()


@dataclass
class LoadManagerConfig(BaseConfig):
    """Configuration for load manager"""

    target_power: float = 530000.0  # 530 kW (aligned with legacy config)
    power_tolerance: float = 0.05  # 5%
    max_ramp_rate: float = 50000.0  # 50 kW/s

    def validate(self) -> bool:
        """Validate load manager configuration"""
        validator = ConfigValidator()

        validator.check_positive_float(self.target_power, "target_power")
        validator.check_positive_float(self.power_tolerance, "power_tolerance")
        validator.check_positive_float(self.max_ramp_rate, "max_ramp_rate")
        validator.check_range(self.target_power, 1000.0, 1000000.0, "target_power")
        validator.check_range(self.power_tolerance, 0.01, 0.2, "power_tolerance")
        validator.check_range(self.max_ramp_rate, 1000.0, 100000.0, "max_ramp_rate")

        return validator.is_valid()


@dataclass
class GridStabilityConfig(BaseConfig):
    """Configuration for grid stability controller"""

    nominal_voltage: float = 480.0
    nominal_frequency: float = 50.0
    voltage_regulation_band: float = 0.05
    frequency_regulation_band: float = 0.1

    def validate(self) -> bool:
        """Validate grid stability configuration"""
        validator = ConfigValidator()

        validator.check_positive_float(self.nominal_voltage, "nominal_voltage")
        validator.check_positive_float(self.nominal_frequency, "nominal_frequency")
        validator.check_positive_float(self.voltage_regulation_band, "voltage_regulation_band")
        validator.check_positive_float(self.frequency_regulation_band, "frequency_regulation_band")
        validator.check_range(self.nominal_voltage, 100.0, 1000.0, "nominal_voltage")
        validator.check_range(self.nominal_frequency, 25.0, 60.0, "nominal_frequency")
        validator.check_range(self.voltage_regulation_band, 0.01, 0.2, "voltage_regulation_band")
        validator.check_range(self.frequency_regulation_band, 0.01, 0.5, "frequency_regulation_band")

        return validator.is_valid()


@dataclass
class FaultDetectorConfig(BaseConfig):
    """Configuration for fault detector"""

    monitoring_interval: float = 0.1
    auto_recovery_enabled: bool = True
    predictive_maintenance_enabled: bool = True

    def validate(self) -> bool:
        """Validate fault detector configuration"""
        validator = ConfigValidator()

        validator.check_positive_float(self.monitoring_interval, "monitoring_interval")
        validator.check_range(self.monitoring_interval, 0.01, 1.0, "monitoring_interval")

        return validator.is_valid()


@dataclass
class ControlSystemConfig(BaseConfig):
    """Configuration for integrated control system"""

    # Component configurations
    timing: TimingControllerConfig = field(default_factory=TimingControllerConfig)
    load_manager: LoadManagerConfig = field(default_factory=LoadManagerConfig)
    grid_stability: GridStabilityConfig = field(default_factory=GridStabilityConfig)
    fault_detector: FaultDetectorConfig = field(default_factory=FaultDetectorConfig)

    # Control coordination config
    control_priority_weights: Dict[str, float] = field(
        default_factory=lambda: {
            "safety": 1.0,
            "fault_response": 0.9,
            "grid_stability": 0.8,
            "load_management": 0.7,
            "timing_optimization": 0.6,
            "efficiency_optimization": 0.5,
        }
    )
    emergency_response_enabled: bool = True
    adaptive_control_enabled: bool = True

    def validate(self) -> bool:
        """Validate control system configuration"""
        validator = ConfigValidator()

        # Validate component configs
        if not self.timing.validate():
            validator.add_error("timing configuration is invalid")

        if not self.load_manager.validate():
            validator.add_error("load_manager configuration is invalid")

        if not self.grid_stability.validate():
            validator.add_error("grid_stability configuration is invalid")

        if not self.fault_detector.validate():
            validator.add_error("fault_detector configuration is invalid")

        # Validate priority weights
        if self.control_priority_weights:
            for priority, weight in self.control_priority_weights.items():
                if not isinstance(weight, (int, float)) or weight < 0 or weight > 1:
                    validator.add_error(f"Invalid priority weight for {priority}: {weight}")

        return validator.is_valid()

    def to_dict(self) -> Dict:
        """Convert configuration to dictionary"""
        return {
            "timing": self.timing.to_dict(),
            "load_manager": self.load_manager.to_dict(),
            "grid_stability": self.grid_stability.to_dict(),
            "fault_detector": self.fault_detector.to_dict(),
            "control_priority_weights": self.control_priority_weights,
            "emergency_response_enabled": self.emergency_response_enabled,
            "adaptive_control_enabled": self.adaptive_control_enabled,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "ControlSystemConfig":
        """Create configuration from dictionary"""
        timing_data = data.get("timing", {})
        load_manager_data = data.get("load_manager", {})
        grid_stability_data = data.get("grid_stability", {})
        fault_detector_data = data.get("fault_detector", {})

        return cls(
            timing=TimingControllerConfig.from_dict(timing_data),
            load_manager=LoadManagerConfig.from_dict(load_manager_data),
            grid_stability=GridStabilityConfig.from_dict(grid_stability_data),
            fault_detector=FaultDetectorConfig.from_dict(fault_detector_data),
            control_priority_weights=data.get("control_priority_weights"),
            emergency_response_enabled=data.get("emergency_response_enabled", True),
            adaptive_control_enabled=data.get("adaptive_control_enabled", True),
        )
