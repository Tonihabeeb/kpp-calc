"""
Startup Sequence Controller for KPP System
Manages safe and efficient system startup procedures.
"""

import logging
import time
from enum import Enum
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

class StartupPhase(Enum):
    """Startup sequence phases"""
    INITIALIZATION = "initialization"
    SYSTEM_CHECKS = "system_checks"
    PRESSURE_BUILD = "pressure_build"
    FIRST_INJECTION = "first_injection"
    ACCELERATION = "acceleration"
    SYNCHRONIZATION = "synchronization"
    OPERATIONAL = "operational"
    FAILED = "failed"

@dataclass
class StartupConditions:
    """Required conditions for startup progression"""
    min_tank_pressure: float = 4.0  # bar
    max_component_temperature: float = 60.0  # °C
    min_system_voltage: float = 450.0  # V
    max_system_voltage: float = 510.0  # V
    target_frequency: float = 60.0  # Hz
    frequency_tolerance: float = 0.5  # Hz
    min_floater_count: int = 2  # minimum operational floaters

@dataclass
class StartupMetrics:
    """Startup performance metrics"""
    startup_time: float = 0.0
    phase_times: Dict[str, float] = field(default_factory=dict)
    max_acceleration: float = 0.0
    sync_attempts: int = 0
    fault_count: int = 0

class StartupController:
    """
    Controls the complete system startup sequence.
    
    Manages safe progression through startup phases with comprehensive
    condition checking and fault handling.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize startup controller.
        
        Args:
            config: Configuration parameters for startup sequence
        """
        self.config = config or {}
        self.conditions = StartupConditions()
        self.metrics = StartupMetrics()
        
        # Current state
        self.current_phase = StartupPhase.INITIALIZATION
        self.phase_start_time = 0.0
        self.startup_start_time = 0.0
        self.is_startup_active = False
        
        # Phase timeouts (seconds)
        self.phase_timeouts = {
            StartupPhase.INITIALIZATION: 10.0,
            StartupPhase.SYSTEM_CHECKS: 15.0,
            StartupPhase.PRESSURE_BUILD: 30.0,
            StartupPhase.FIRST_INJECTION: 20.0,
            StartupPhase.ACCELERATION: 60.0,
            StartupPhase.SYNCHRONIZATION: 30.0
        }
        
        # Startup parameters
        self.target_startup_speed = self.config.get('target_startup_speed', 100.0)  # RPM
        self.target_operational_speed = self.config.get('target_operational_speed', 375.0)  # RPM
        self.acceleration_rate = self.config.get('acceleration_rate', 10.0)  # RPM/s
        self.sync_retry_limit = self.config.get('sync_retry_limit', 3)
        
        # State tracking
        self.system_checks_passed = False
        self.first_injection_completed = False
        self.sync_attempt_count = 0
        self.fault_conditions = []
        
        logger.info("StartupController initialized")
    
    def initiate_startup(self, current_time: float) -> bool:
        """
        Initiate the startup sequence.
        
        Args:
            current_time: Current simulation time
            
        Returns:
            bool: True if startup initiated successfully
        """
        if self.is_startup_active:
            logger.warning("Startup already in progress")
            return False
        
        logger.info("Initiating system startup sequence")
        self.is_startup_active = True
        self.startup_start_time = current_time
        self.phase_start_time = current_time
        self.current_phase = StartupPhase.INITIALIZATION
        self.metrics = StartupMetrics()
        self.fault_conditions = []
        
        return True
    
    def update_startup_sequence(self, system_state: Dict, current_time: float) -> Dict:
        """
        Update the startup sequence based on current system state.
        
        Args:
            system_state: Current system state
            current_time: Current simulation time
            
        Returns:
            Dict: Startup commands and status
        """
        if not self.is_startup_active:
            return {'startup_active': False}
        
        # Check for timeout
        phase_duration = current_time - self.phase_start_time
        if phase_duration > self.phase_timeouts.get(self.current_phase, 60.0):
            logger.error(f"Startup phase {self.current_phase.value} timed out after {phase_duration:.1f}s")
            return self._handle_startup_failure("Phase timeout")
        
        # Process current phase
        startup_commands = self._process_current_phase(system_state, current_time)
        
        # Update metrics
        self.metrics.startup_time = current_time - self.startup_start_time
        if self.current_phase.value not in self.metrics.phase_times:
            self.metrics.phase_times[self.current_phase.value] = 0.0
        self.metrics.phase_times[self.current_phase.value] = phase_duration
        
        return startup_commands
    
    def _process_current_phase(self, system_state: Dict, current_time: float) -> Dict:
        """Process the current startup phase"""
        
        if self.current_phase == StartupPhase.INITIALIZATION:
            return self._process_initialization_phase(system_state, current_time)
        
        elif self.current_phase == StartupPhase.SYSTEM_CHECKS:
            return self._process_system_checks_phase(system_state, current_time)
        
        elif self.current_phase == StartupPhase.PRESSURE_BUILD:
            return self._process_pressure_build_phase(system_state, current_time)
        
        elif self.current_phase == StartupPhase.FIRST_INJECTION:
            return self._process_first_injection_phase(system_state, current_time)
        
        elif self.current_phase == StartupPhase.ACCELERATION:
            return self._process_acceleration_phase(system_state, current_time)
        
        elif self.current_phase == StartupPhase.SYNCHRONIZATION:
            return self._process_synchronization_phase(system_state, current_time)
        
        elif self.current_phase == StartupPhase.OPERATIONAL:
            return self._process_operational_phase(system_state, current_time)
        
        else:
            return self._handle_startup_failure("Unknown startup phase")
    
    def _process_initialization_phase(self, system_state: Dict, current_time: float) -> Dict:
        """Process initialization phase"""
        logger.info("Startup Phase: Initialization")
        
        # Initialize system components
        commands = {
            'startup_active': True,
            'current_phase': self.current_phase.value,
            'pneumatic_commands': {
                'compressor_enabled': True,
                'tank_isolation': False
            },
            'electrical_commands': {
                'generator_enable': False,
                'grid_connect': False
            },
            'control_commands': {
                'timing_mode': 'manual',
                'load_limit': 0.0
            }
        }
        
        # Progress to system checks
        self._advance_to_next_phase(StartupPhase.SYSTEM_CHECKS, current_time)
        
        return commands
    
    def _process_system_checks_phase(self, system_state: Dict, current_time: float) -> Dict:
        """Process system checks phase"""
        logger.info("Startup Phase: System Checks")
        
        # Perform comprehensive system checks
        checks_passed = self._perform_system_checks(system_state)
        
        commands = {
            'startup_active': True,
            'current_phase': self.current_phase.value,
            'system_checks_status': checks_passed,
            'pneumatic_commands': {
                'compressor_enabled': True,
                'pressure_setpoint': self.conditions.min_tank_pressure
            }
        }
        
        if checks_passed['all_passed']:
            self.system_checks_passed = True
            self._advance_to_next_phase(StartupPhase.PRESSURE_BUILD, current_time)
            logger.info("System checks passed, advancing to pressure build")
        
        return commands
    
    def _process_pressure_build_phase(self, system_state: Dict, current_time: float) -> Dict:
        """Process pressure build phase"""
        logger.info("Startup Phase: Pressure Build")
        
        tank_pressure = system_state.get('pneumatics', {}).get('tank_pressure', 0.0)
        
        commands = {
            'startup_active': True,
            'current_phase': self.current_phase.value,
            'pneumatic_commands': {
                'compressor_enabled': True,
                'pressure_setpoint': self.conditions.min_tank_pressure + 1.0  # Build extra pressure
            }
        }
        
        # Check if sufficient pressure is available
        if tank_pressure >= self.conditions.min_tank_pressure:
            self._advance_to_next_phase(StartupPhase.FIRST_INJECTION, current_time)
            logger.info(f"Pressure build complete ({tank_pressure:.1f} bar), advancing to first injection")
        
        return commands
    
    def _process_first_injection_phase(self, system_state: Dict, current_time: float) -> Dict:
        """Process first injection phase"""
        logger.info("Startup Phase: First Injection")
        
        commands = {
            'startup_active': True,
            'current_phase': self.current_phase.value,
            'pneumatic_commands': {
                'injection_enabled': True,
                'injection_pressure': self.conditions.min_tank_pressure * 0.8,  # Gentle first injection
                'target_floater': 0  # Start with first floater
            },
            'control_commands': {
                'timing_mode': 'startup',
                'load_limit': 0.1  # Very light load
            }
        }
        
        # Check for successful first injection and initial movement
        chain_speed = system_state.get('chain_speed_rpm', 0.0)
        if chain_speed > 5.0:  # Some movement detected
            self.first_injection_completed = True
            self._advance_to_next_phase(StartupPhase.ACCELERATION, current_time)
            logger.info("First injection successful, advancing to acceleration")
        
        return commands
    
    def _process_acceleration_phase(self, system_state: Dict, current_time: float) -> Dict:
        """Process acceleration phase"""
        logger.info("Startup Phase: Acceleration")
        
        current_speed = system_state.get('flywheel_speed_rpm', 0.0)
        target_speed = min(self.target_startup_speed, 
                          self.target_operational_speed * (current_time - self.phase_start_time) / 30.0)
        
        commands = {
            'startup_active': True,
            'current_phase': self.current_phase.value,
            'pneumatic_commands': {
                'injection_enabled': True,
                'injection_pressure': self.conditions.min_tank_pressure,
                'injection_frequency': min(2.0, target_speed / 50.0)  # Gradual frequency increase
            },
            'control_commands': {
                'timing_mode': 'acceleration',
                'speed_setpoint': target_speed,
                'load_limit': 0.3  # Gradually increase load
            }
        }
        
        # Track maximum acceleration
        if 'flywheel_acceleration' in system_state:
            self.metrics.max_acceleration = max(self.metrics.max_acceleration, 
                                               abs(system_state['flywheel_acceleration']))
        
        # Check if ready for synchronization
        if current_speed >= self.target_startup_speed:
            self._advance_to_next_phase(StartupPhase.SYNCHRONIZATION, current_time)
            logger.info(f"Acceleration complete ({current_speed:.1f} RPM), advancing to synchronization")
        
        return commands
    
    def _process_synchronization_phase(self, system_state: Dict, current_time: float) -> Dict:
        """Process synchronization phase"""
        logger.info("Startup Phase: Synchronization")
        
        commands = {
            'startup_active': True,
            'current_phase': self.current_phase.value,
            'electrical_commands': {
                'generator_enable': True,
                'synchronization_enable': True,
                'grid_connect_ready': True
            },
            'control_commands': {
                'timing_mode': 'synchronization',
                'speed_setpoint': self.target_operational_speed,
                'load_limit': 0.5
            }
        }
        
        # Check synchronization status
        synchronized = system_state.get('synchronized', False)
        grid_frequency = system_state.get('grid_frequency', 0.0)
        frequency_error = abs(grid_frequency - self.conditions.target_frequency)
        
        if synchronized and frequency_error < self.conditions.frequency_tolerance:
            self._advance_to_next_phase(StartupPhase.OPERATIONAL, current_time)
            logger.info("Synchronization successful, startup complete")
        elif frequency_error > self.conditions.frequency_tolerance * 2:
            self.sync_attempt_count += 1
            if self.sync_attempt_count >= self.sync_retry_limit:
                return self._handle_startup_failure("Synchronization failed after multiple attempts")
            logger.warning(f"Synchronization attempt {self.sync_attempt_count} failed, retrying")
        
        self.metrics.sync_attempts = self.sync_attempt_count
        
        return commands
    
    def _process_operational_phase(self, system_state: Dict, current_time: float) -> Dict:
        """Process operational phase - startup complete"""
        logger.info("Startup Phase: Operational - Startup Complete")
        
        self.is_startup_active = False
        self.metrics.startup_time = current_time - self.startup_start_time
        
        logger.info(f"Startup sequence completed successfully in {self.metrics.startup_time:.1f}s")
        
        return {
            'startup_active': False,
            'startup_complete': True,
            'current_phase': self.current_phase.value,
            'startup_metrics': self.metrics,
            'electrical_commands': {
                'generator_enable': True,
                'grid_connect': True
            },
            'control_commands': {
                'timing_mode': 'normal',
                'load_limit': 1.0  # Full operational load
            }
        }
    
    def _perform_system_checks(self, system_state: Dict) -> Dict:
        """Perform comprehensive system checks"""
        checks = {
            'pneumatic_system': True,
            'electrical_system': True,
            'mechanical_system': True,
            'thermal_system': True,
            'control_system': True,
            'all_passed': True
        }
        
        # Check pneumatic system
        pneumatics = system_state.get('pneumatics', {})
        if pneumatics.get('tank_pressure', 0.0) < 2.0:  # Minimum pressure for checks
            checks['pneumatic_system'] = False
            self.fault_conditions.append("Insufficient pneumatic pressure for startup")
        
        # Check electrical system
        if system_state.get('component_temperatures', {}).get('generator', 100.0) > self.conditions.max_component_temperature:
            checks['electrical_system'] = False
            self.fault_conditions.append("Generator temperature too high for startup")
        
        # Check mechanical system
        floater_count = len(system_state.get('floaters', []))
        if floater_count < self.conditions.min_floater_count:
            checks['mechanical_system'] = False
            self.fault_conditions.append(f"Insufficient floaters for startup ({floater_count} < {self.conditions.min_floater_count})")
        
        # Check thermal system
        component_temps = system_state.get('component_temperatures', {})
        max_temp = max(component_temps.values()) if component_temps else 0.0
        if max_temp > self.conditions.max_component_temperature:
            checks['thermal_system'] = False
            self.fault_conditions.append(f"Component temperature too high for startup ({max_temp:.1f}°C)")
        
        # Overall check
        checks['all_passed'] = all(checks[key] for key in checks if key != 'all_passed')
        
        if not checks['all_passed']:
            self.metrics.fault_count += 1
            logger.warning(f"System checks failed: {self.fault_conditions}")
        
        return checks
    
    def _advance_to_next_phase(self, next_phase: StartupPhase, current_time: float):
        """Advance to the next startup phase"""
        logger.info(f"Advancing from {self.current_phase.value} to {next_phase.value}")
        self.current_phase = next_phase
        self.phase_start_time = current_time
    
    def _handle_startup_failure(self, reason: str) -> Dict:
        """Handle startup failure"""
        logger.error(f"Startup failed: {reason}")
        self.current_phase = StartupPhase.FAILED
        self.is_startup_active = False
        self.fault_conditions.append(reason)
        self.metrics.fault_count += 1
        
        return {
            'startup_active': False,
            'startup_failed': True,
            'failure_reason': reason,
            'fault_conditions': self.fault_conditions,
            'emergency_commands': {
                'pneumatic_stop': True,
                'electrical_disconnect': True,
                'mechanical_brake': True
            }
        }
    
    def abort_startup(self, reason: str = "Manual abort") -> Dict:
        """Abort the startup sequence"""
        if not self.is_startup_active:
            return {'startup_active': False}
        
        logger.warning(f"Startup aborted: {reason}")
        return self._handle_startup_failure(f"Aborted: {reason}")
    
    def get_startup_status(self) -> Dict:
        """Get current startup status"""
        return {
            'startup_active': self.is_startup_active,
            'current_phase': self.current_phase.value,
            'metrics': self.metrics,
            'fault_conditions': self.fault_conditions,
            'system_checks_passed': self.system_checks_passed,
            'first_injection_completed': self.first_injection_completed
        }
    
    def reset(self):
        """Reset startup controller"""
        logger.info("StartupController reset")
        self.current_phase = StartupPhase.INITIALIZATION
        self.is_startup_active = False
        self.metrics = StartupMetrics()
        self.fault_conditions = []
        self.system_checks_passed = False
        self.first_injection_completed = False
        self.sync_attempt_count = 0
