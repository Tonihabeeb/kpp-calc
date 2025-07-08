import logging
import time
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

"""
Validation for floater parameters and state.
Ensures physical constraints and operational limits.
"""

class ValidationLevel(str, Enum):
    """Validation level enumeration"""
    BASIC = "basic"
    STRICT = "strict"
    COMPREHENSIVE = "comprehensive"

class ValidationResult(str, Enum):
    """Validation result enumeration"""
    PASS = "pass"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

@dataclass
class ValidationIssue:
    """Validation issue data structure"""
    level: ValidationResult
    category: str
    message: str
    parameter: Optional[str] = None
    value: Optional[Any] = None
    expected_range: Optional[Tuple[float, float]] = None
    timestamp: float = 0.0

@dataclass
class ValidationReport:
    """Validation report data structure"""
    overall_result: ValidationResult
    issues: List[ValidationIssue]
    validation_time: float
    checks_performed: int
    checks_passed: int
    checks_failed: int
    performance_score: float

@dataclass
class ValidationConfig:
    """Validation configuration"""
    validation_level: ValidationLevel = ValidationLevel.COMPREHENSIVE
    max_air_fill_level: float = 1.0
    min_air_fill_level: float = 0.0
    max_pressure: float = 500000.0  # Pa
    min_pressure: float = 100000.0  # Pa
    max_temperature: float = 373.15  # K (100°C)
    min_temperature: float = 273.15  # K (0°C)
    max_velocity: float = 10.0  # m/s
    max_acceleration: float = 20.0  # m/s²
    max_force: float = 10000.0  # N
    min_cycle_time: float = 1.0  # seconds
    max_cycle_time: float = 300.0  # seconds
    error_threshold: int = 3

class FloaterValidator:
    """
    Comprehensive floater validation system.
    Validates parameters, state consistency, and performance.
    """
    
    def __init__(self, config: Optional[ValidationConfig] = None):
        """
        Initialize the floater validator.
        
        Args:
            config: Validation configuration
        """
        self.config = config or ValidationConfig()
        self.logger = logging.getLogger(__name__)
        
        # Validation tracking
        self.validation_history: List[ValidationReport] = []
        self.total_validations = 0
        self.successful_validations = 0
        
        # Performance tracking
        self.performance_metrics = {
            'average_validation_time': 0.0,
            'validation_success_rate': 0.0,
            'critical_issues_count': 0,
            'warning_count': 0
        }
        
        self.logger.info("Floater validator initialized with level: %s", self.config.validation_level)
    
    def validate_floater(self, floater_data: Dict[str, Any]) -> ValidationReport:
        """
        Perform comprehensive floater validation.
        
        Args:
            floater_data: Floater data dictionary
            
        Returns:
            Validation report
        """
        start_time = time.time()
        issues: List[ValidationIssue] = []
        
        try:
            # Parameter validation
            param_issues = self._validate_parameters(floater_data)
            issues.extend(param_issues)
            
            # State consistency validation
            state_issues = self._validate_state_consistency(floater_data)
            issues.extend(state_issues)
            
            # Performance validation
            perf_issues = self._validate_performance(floater_data)
            issues.extend(perf_issues)
            
            # Physics validation
            physics_issues = self._validate_physics(floater_data)
            issues.extend(physics_issues)
            
            # Calculate overall result
            overall_result = self._calculate_overall_result(issues)
            
            # Calculate performance score
            performance_score = self._calculate_performance_score(issues)
            
            # Create validation report
            validation_time = time.time() - start_time
            checks_performed = len(issues)
            checks_passed = len([i for i in issues if i.level == ValidationResult.PASS])
            checks_failed = len([i for i in issues if i.level in [ValidationResult.ERROR, ValidationResult.CRITICAL]])
            
            report = ValidationReport(
                overall_result=overall_result,
                issues=issues,
                validation_time=validation_time,
                checks_performed=checks_performed,
                checks_passed=checks_passed,
                checks_failed=checks_failed,
                performance_score=performance_score
            )
            
            # Update tracking
            self._update_tracking(report)
            
            return report
            
        except Exception as e:
            self.logger.error("Error during validation: %s", e)
            critical_issue = ValidationIssue(
                level=ValidationResult.CRITICAL,
                category="validation_error",
                message=f"Validation error: {str(e)}",
                timestamp=time.time()
            )
            
            return ValidationReport(
                overall_result=ValidationResult.CRITICAL,
                issues=[critical_issue],
                validation_time=time.time() - start_time,
                checks_performed=1,
                checks_passed=0,
                checks_failed=1,
                performance_score=0.0
            )
    
    def _validate_parameters(self, floater_data: Dict[str, Any]) -> List[ValidationIssue]:
        """
        Validate floater parameters.
        
        Args:
            floater_data: Floater data
            
        Returns:
            List of validation issues
        """
        issues: List[ValidationIssue] = []
        current_time = time.time()
        
        # Air fill level validation
        air_fill_level = floater_data.get('air_fill_level', 0.0)
        if not (self.config.min_air_fill_level <= air_fill_level <= self.config.max_air_fill_level):
            issues.append(ValidationIssue(
                level=ValidationResult.ERROR,
                category="parameter_validation",
                message="Air fill level out of range",
                parameter="air_fill_level",
                value=air_fill_level,
                expected_range=(self.config.min_air_fill_level, self.config.max_air_fill_level),
                timestamp=current_time
            ))
        
        # Pressure validation
        pressure = floater_data.get('pressure', 101325.0)
        if not (self.config.min_pressure <= pressure <= self.config.max_pressure):
            issues.append(ValidationIssue(
                level=ValidationResult.ERROR,
                category="parameter_validation",
                message="Pressure out of range",
                parameter="pressure",
                value=pressure,
                expected_range=(self.config.min_pressure, self.config.max_pressure),
                timestamp=current_time
            ))
        
        # Temperature validation
        temperature = floater_data.get('temperature', 293.15)
        if not (self.config.min_temperature <= temperature <= self.config.max_temperature):
            issues.append(ValidationIssue(
                level=ValidationResult.WARNING,
                category="parameter_validation",
                message="Temperature out of normal range",
                parameter="temperature",
                value=temperature,
                expected_range=(self.config.min_temperature, self.config.max_temperature),
                timestamp=current_time
            ))
        
        # Velocity validation
        velocity = floater_data.get('velocity', 0.0)
        if abs(velocity) > self.config.max_velocity:
            issues.append(ValidationIssue(
                level=ValidationResult.ERROR,
                category="parameter_validation",
                message="Velocity exceeds maximum",
                parameter="velocity",
                value=velocity,
                expected_range=(-self.config.max_velocity, self.config.max_velocity),
                timestamp=current_time
            ))
        
        # Force validation
        force = floater_data.get('net_force', 0.0)
        if abs(force) > self.config.max_force:
            issues.append(ValidationIssue(
                level=ValidationResult.CRITICAL,
                category="parameter_validation",
                message="Force exceeds maximum safe limit",
                parameter="net_force",
                value=force,
                expected_range=(-self.config.max_force, self.config.max_force),
                timestamp=current_time
            ))
        
        return issues
    
    def _validate_state_consistency(self, floater_data: Dict[str, Any]) -> List[ValidationIssue]:
        """
        Validate state consistency.
        
        Args:
            floater_data: Floater data
            
        Returns:
            List of validation issues
        """
        issues: List[ValidationIssue] = []
        current_time = time.time()
        
        # State-air fill consistency
        state = floater_data.get('state', 'unknown')
        air_fill_level = floater_data.get('air_fill_level', 0.0)
        
        if state == 'empty' and air_fill_level > 0.1:
            issues.append(ValidationIssue(
                level=ValidationResult.ERROR,
                category="state_consistency",
                message="Empty state but significant air fill level",
                parameter="state_air_fill_consistency",
                value=f"state={state}, air_fill={air_fill_level}",
                timestamp=current_time
            ))
        
        if state == 'full' and air_fill_level < 0.9:
            issues.append(ValidationIssue(
                level=ValidationResult.ERROR,
                category="state_consistency",
                message="Full state but low air fill level",
                parameter="state_air_fill_consistency",
                value=f"state={state}, air_fill={air_fill_level}",
                timestamp=current_time
            ))
        
        # Mass consistency
        mass = floater_data.get('mass', 0.0)
        volume = floater_data.get('volume', 0.4)
        air_fill_level = floater_data.get('air_fill_level', 0.0)
        
        # Calculate expected mass
        base_mass = 10.0  # kg (container mass)
        water_volume = volume * (1.0 - air_fill_level)
        water_mass = water_volume * 1000.0  # kg/m³
        air_mass = volume * air_fill_level * 1.225  # kg/m³
        expected_mass = base_mass + water_mass + air_mass
        
        mass_tolerance = 0.5  # kg
        if abs(mass - expected_mass) > mass_tolerance:
            issues.append(ValidationIssue(
                level=ValidationResult.WARNING,
                category="state_consistency",
                message="Mass inconsistency detected",
                parameter="mass_consistency",
                value=f"actual={mass:.2f}, expected={expected_mass:.2f}",
                timestamp=current_time
            ))
        
        return issues
    
    def _validate_performance(self, floater_data: Dict[str, Any]) -> List[ValidationIssue]:
        """
        Validate performance metrics.
        
        Args:
            floater_data: Floater data
            
        Returns:
            List of validation issues
        """
        issues: List[ValidationIssue] = []
        current_time = time.time()
        
        # Cycle time validation
        cycle_time = floater_data.get('cycle_time', 0.0)
        if cycle_time > 0:
            if cycle_time < self.config.min_cycle_time:
                issues.append(ValidationIssue(
                    level=ValidationResult.WARNING,
                    category="performance_validation",
                    message="Cycle time too short",
                    parameter="cycle_time",
                    value=cycle_time,
                    expected_range=(self.config.min_cycle_time, self.config.max_cycle_time),
                    timestamp=current_time
                ))
            
            if cycle_time > self.config.max_cycle_time:
                issues.append(ValidationIssue(
                    level=ValidationResult.ERROR,
                    category="performance_validation",
                    message="Cycle time too long",
                    parameter="cycle_time",
                    value=cycle_time,
                    expected_range=(self.config.min_cycle_time, self.config.max_cycle_time),
                    timestamp=current_time
                ))
        
        # Efficiency validation
        efficiency = floater_data.get('efficiency', 1.0)
        if efficiency < 0.5:
            issues.append(ValidationIssue(
                level=ValidationResult.WARNING,
                category="performance_validation",
                message="Low efficiency detected",
                parameter="efficiency",
                value=efficiency,
                expected_range=(0.5, 1.0),
                timestamp=current_time
            ))
        
        # Energy consumption validation
        energy_consumed = floater_data.get('total_energy_consumed', 0.0)
        energy_generated = floater_data.get('total_energy_generated', 0.0)
        
        if energy_consumed > 0 and energy_generated > 0:
            energy_ratio = energy_generated / energy_consumed
            if energy_ratio < 0.8:
                issues.append(ValidationIssue(
                    level=ValidationResult.WARNING,
                    category="performance_validation",
                    message="Low energy efficiency",
                    parameter="energy_efficiency",
                    value=energy_ratio,
                    expected_range=(0.8, 2.0),
                    timestamp=current_time
                ))
        
        return issues
    
    def _validate_physics(self, floater_data: Dict[str, Any]) -> List[ValidationIssue]:
        """
        Validate physics calculations.
        
        Args:
            floater_data: Floater data
            
        Returns:
            List of validation issues
        """
        issues: List[ValidationIssue] = []
        current_time = time.time()
        
        # Buoyancy force validation
        buoyancy_force = floater_data.get('buoyancy_force', 0.0)
        volume = floater_data.get('volume', 0.4)
        air_fill_level = floater_data.get('air_fill_level', 0.0)
        
        # Calculate expected buoyancy force
        water_density = 1000.0  # kg/m³
        gravity = 9.81  # m/s²
        displaced_volume = volume * (1.0 - air_fill_level)
        expected_buoyancy = water_density * displaced_volume * gravity
        
        buoyancy_tolerance = 10.0  # N
        if abs(buoyancy_force - expected_buoyancy) > buoyancy_tolerance:
            issues.append(ValidationIssue(
                level=ValidationResult.WARNING,
                category="physics_validation",
                message="Buoyancy force calculation inconsistency",
                parameter="buoyancy_force",
                value=f"actual={buoyancy_force:.1f}, expected={expected_buoyancy:.1f}",
                timestamp=current_time
            ))
        
        # Energy conservation validation
        net_force = floater_data.get('net_force', 0.0)
        mass = floater_data.get('mass', 10.0)
        acceleration = floater_data.get('acceleration', 0.0)
        
        # F = ma validation
        expected_force = mass * acceleration
        force_tolerance = 5.0  # N
        if abs(net_force - expected_force) > force_tolerance:
            issues.append(ValidationIssue(
                level=ValidationResult.WARNING,
                category="physics_validation",
                message="Force-acceleration relationship inconsistency",
                parameter="force_acceleration",
                value=f"F={net_force:.1f}, ma={expected_force:.1f}",
                timestamp=current_time
            ))
        
        return issues
    
    def _calculate_overall_result(self, issues: List[ValidationIssue]) -> ValidationResult:
        """
        Calculate overall validation result.
        
        Args:
            issues: List of validation issues
            
        Returns:
            Overall validation result
        """
        if not issues:
            return ValidationResult.PASS
        
        # Check for critical issues
        if any(issue.level == ValidationResult.CRITICAL for issue in issues):
            return ValidationResult.CRITICAL
        
        # Check for errors
        if any(issue.level == ValidationResult.ERROR for issue in issues):
            return ValidationResult.ERROR
        
        # Check for warnings
        if any(issue.level == ValidationResult.WARNING for issue in issues):
            return ValidationResult.WARNING
        
        return ValidationResult.PASS
    
    def _calculate_performance_score(self, issues: List[ValidationIssue]) -> float:
        """
        Calculate performance score.
        
        Args:
            issues: List of validation issues
            
        Returns:
            Performance score (0.0 to 1.0)
        """
        if not issues:
            return 1.0
        
        # Weight issues by severity
        weights = {
            ValidationResult.PASS: 0.0,
            ValidationResult.WARNING: 0.1,
            ValidationResult.ERROR: 0.3,
            ValidationResult.CRITICAL: 0.6
        }
        
        total_penalty = sum(weights.get(issue.level, 0.0) for issue in issues)
        max_penalty = len(issues) * 0.6  # Worst case: all critical
        
        if max_penalty == 0:
            return 1.0
        
        score = 1.0 - (total_penalty / max_penalty)
        return max(0.0, min(1.0, score))
    
    def _update_tracking(self, report: ValidationReport) -> None:
        """
        Update validation tracking.
        
        Args:
            report: Validation report
        """
        self.total_validations += 1
        
        if report.overall_result in [ValidationResult.PASS, ValidationResult.WARNING]:
            self.successful_validations += 1
        
        # Update performance metrics
        self.performance_metrics['average_validation_time'] = (
            (self.performance_metrics['average_validation_time'] * (self.total_validations - 1) + report.validation_time) /
            self.total_validations
        )
        
        self.performance_metrics['validation_success_rate'] = self.successful_validations / self.total_validations
        
        critical_count = len([i for i in report.issues if i.level == ValidationResult.CRITICAL])
        warning_count = len([i for i in report.issues if i.level == ValidationResult.WARNING])
        
        self.performance_metrics['critical_issues_count'] += critical_count
        self.performance_metrics['warning_count'] += warning_count
        
        # Add to history
        self.validation_history.append(report)
    
    def get_validation_history(self, limit: Optional[int] = None) -> List[ValidationReport]:
        """
        Get validation history.
        
        Args:
            limit: Maximum number of reports to return
            
        Returns:
            List of validation reports
        """
        if limit is None:
            return self.validation_history.copy()
        else:
            return self.validation_history[-limit:]
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Get performance metrics.
        
        Returns:
            Performance metrics dictionary
        """
        return self.performance_metrics.copy()
    
    def get_recent_issues(self, hours: float = 24.0) -> List[ValidationIssue]:
        """
        Get recent validation issues.
        
        Args:
            hours: Time window in hours
            
        Returns:
            List of recent issues
        """
        cutoff_time = time.time() - (hours * 3600)
        recent_issues = []
        
        for report in self.validation_history:
            if report.validation_time >= cutoff_time:
                recent_issues.extend(report.issues)
        
        return recent_issues
    
    def reset(self) -> None:
        """Reset validator state."""
        self.validation_history.clear()
        self.total_validations = 0
        self.successful_validations = 0
        self.performance_metrics = {
            'average_validation_time': 0.0,
            'validation_success_rate': 0.0,
            'critical_issues_count': 0,
            'warning_count': 0
        }
        self.logger.info("Floater validator reset")

