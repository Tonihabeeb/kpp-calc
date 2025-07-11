"""
Integrated Drivetrain System for KPP Simulator
This replaces the legacy drivetrain.py with the new integrated system.
"""

import math
import logging
import time
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass
from enum import Enum

"""
Integrated Drivetrain System for Phase 3 Implementation
Complete mechanical power transmission system combining sprockets, gearbox, clutch, and flywheel.
This represents the complete mechanical power transmission system for the KPP.
"""

class DrivetrainSystemState(str, Enum):
    """Drivetrain system state enumeration"""
    IDLE = "idle"
    STARTING = "starting"
    OPERATING = "operating"
    OVERLOADED = "overloaded"
    FAULT = "fault"
    MAINTENANCE = "maintenance"

class ClutchState(str, Enum):
    """Clutch state enumeration"""
    DISENGAGED = "disengaged"
    ENGAGING = "engaging"
    ENGAGED = "engaged"
    SLIPPING = "slipping"
    FAULT = "fault"

@dataclass
class DrivetrainState:
    """Drivetrain state data structure"""
    input_speed: float = 0.0  # RPM
    input_torque: float = 0.0  # N·m
    input_power: float = 0.0  # W
    output_speed: float = 0.0  # RPM
    output_torque: float = 0.0  # N·m
    output_power: float = 0.0  # W
    efficiency: float = 0.0
    chain_tension: float = 0.0  # N
    clutch_state: ClutchState = ClutchState.DISENGAGED
    flywheel_speed: float = 0.0  # RPM
    flywheel_energy: float = 0.0  # J

@dataclass
class DrivetrainConfig:
    """Drivetrain configuration"""
    rated_power: float = 50000.0  # W (50 kW)
    rated_speed: float = 1500.0  # RPM
    rated_torque: float = 318.3  # N·m
    gear_ratio: float = 1.0
    sprocket_ratio: float = 1.0
    clutch_torque_capacity: float = 500.0  # N·m
    flywheel_moment_of_inertia: float = 10.0  # kg·m²
    max_chain_tension: float = 50000.0  # N
    efficiency_nominal: float = 0.95
    max_speed: float = 2000.0  # RPM

class IntegratedDrivetrain:
    """
    Complete mechanical power transmission system.
    Integrates sprockets, gearbox, clutch, and flywheel for power transmission.
    """
    
    def __init__(self, config: Optional[DrivetrainConfig] = None):
        """
        Initialize the integrated drivetrain system.
        
        Args:
            config: Drivetrain configuration
        """
        self.config = config or DrivetrainConfig()
        self.logger = logging.getLogger(__name__)
        
        # System state
        self.drivetrain_state = DrivetrainState()
        self.system_state = DrivetrainSystemState.IDLE
        
        # Performance tracking
        self.performance_metrics = {
            'total_energy_transmitted': 0.0,  # kWh
            'total_energy_losses': 0.0,  # kWh
            'peak_power_transmitted': 0.0,  # W
            'average_efficiency': 0.0,
            'mechanical_losses': 0.0,  # kWh
            'clutch_losses': 0.0,  # kWh
            'bearing_losses': 0.0,  # kWh
            'operating_hours': 0.0,  # hours
            'fault_count': 0
        }
        
        # Operation history
        self.operation_history: List[Dict[str, Any]] = []
        
        # Control parameters
        self.speed_setpoint = self.config.rated_speed
        self.torque_setpoint = 0.0
        self.clutch_engagement_threshold = 0.1  # 10% of rated torque
        
        # Protection systems
        self.overspeed_protection = True
        self.overtorque_protection = True
        self.overload_protection = True
        self.chain_tension_protection = True
        
        # Component interfaces (will be initialized by external systems)
        self.sprockets = None
        self.gearbox = None
        self.clutch = None
        self.flywheel = None
        
        # Loss coefficients
        self.mechanical_loss_coefficient = 0.02  # W/N·m
        self.clutch_loss_coefficient = 0.01  # W/N·m
        self.bearing_loss_coefficient = 0.005  # W/RPM
        
        self.logger.info("Integrated drivetrain initialized: %.1f kW, %.1f RPM", 
                        self.config.rated_power / 1000, self.config.rated_speed)
    
    def start_drivetrain(self, input_speed: float, input_torque: float) -> bool:
        """
        Start the drivetrain system.
        
        Args:
            input_speed: Input speed (RPM)
            input_torque: Input torque (N·m)
            
        Returns:
            True if drivetrain started successfully
        """
        try:
            if self.system_state != DrivetrainSystemState.IDLE:
                self.logger.warning("Cannot start drivetrain in state: %s", self.system_state)
                return False
            
            # Validate input parameters
            if input_speed <= 0 or input_torque <= 0:
                self.logger.error("Invalid input speed or torque")
                return False
            
            # Transition to starting state
            self.system_state = DrivetrainSystemState.STARTING
            
            # Calculate input power
            input_power = input_torque * input_speed * 2 * math.pi / 60  # W
            
            # Calculate output power and parameters
            output_power = self._calculate_output_power(input_power, input_speed, input_torque)
            
            if output_power > 0:
                # Update drivetrain state
                self.drivetrain_state.input_speed = input_speed
                self.drivetrain_state.input_torque = input_torque
                self.drivetrain_state.input_power = input_power
                self.drivetrain_state.output_power = output_power
                self.drivetrain_state.efficiency = output_power / input_power
                
                # Calculate output parameters
                self._calculate_output_parameters(input_speed, input_torque)
                
                # Update clutch state
                self._update_clutch_state(input_torque)
                
                # Update flywheel state
                self._update_flywheel_state(input_speed, input_torque)
                
                # Transition to operating state
                self.system_state = DrivetrainSystemState.OPERATING
                
                # Update performance metrics
                self._update_performance_metrics(input_power, output_power)
                
                # Record operation
                self._record_operation('drivetrain_start', {
                    'input_speed': input_speed,
                    'input_torque': input_torque,
                    'input_power': input_power,
                    'output_power': output_power,
                    'efficiency': self.drivetrain_state.efficiency,
                    'clutch_state': self.drivetrain_state.clutch_state.value
                })
                
                self.logger.info("Drivetrain started: %.1f W output at %.1f RPM (%.1f%% efficiency)", 
                               output_power, input_speed, self.drivetrain_state.efficiency * 100)
                return True
            else:
                self.system_state = DrivetrainSystemState.IDLE
                self.logger.error("Failed to start drivetrain")
                return False
                
        except Exception as e:
            self.logger.error("Error starting drivetrain: %s", e)
            self._handle_fault("drivetrain_start_error", str(e))
            return False
    
    def stop_drivetrain(self) -> bool:
        """
        Stop the drivetrain system.
        
        Returns:
            True if drivetrain stopped successfully
        """
        try:
            if self.system_state == DrivetrainSystemState.IDLE:
                self.logger.warning("Cannot stop drivetrain in state: %s", self.system_state)
                return False
            
            # Reset drivetrain state
            self.drivetrain_state.input_speed = 0.0
            self.drivetrain_state.input_torque = 0.0
            self.drivetrain_state.input_power = 0.0
            self.drivetrain_state.output_speed = 0.0
            self.drivetrain_state.output_torque = 0.0
            self.drivetrain_state.output_power = 0.0
            self.drivetrain_state.efficiency = 0.0
            self.drivetrain_state.chain_tension = 0.0
            self.drivetrain_state.clutch_state = ClutchState.DISENGAGED
            self.drivetrain_state.flywheel_speed = 0.0
            self.drivetrain_state.flywheel_energy = 0.0
            
            # Transition to idle state
            self.system_state = DrivetrainSystemState.IDLE
            
            # Record operation
            self._record_operation('drivetrain_stop', {
                'final_power': self.drivetrain_state.output_power,
                'total_energy_transmitted': self.performance_metrics['total_energy_transmitted']
            })
            
            self.logger.info("Drivetrain stopped")
            return True
            
        except Exception as e:
            self.logger.error("Error stopping drivetrain: %s", e)
            self._handle_fault("drivetrain_stop_error", str(e))
            return False
    
    def update_drivetrain_state(self, input_speed: float, input_torque: float) -> bool:
        """
        Update drivetrain state based on input parameters.
        
        Args:
            input_speed: Input speed (RPM)
            input_torque: Input torque (N·m)
            
        Returns:
            True if update successful
        """
        try:
            if self.system_state not in [DrivetrainSystemState.OPERATING, DrivetrainSystemState.OVERLOADED]:
                return False
            
            # Calculate new input power
            input_power = input_torque * input_speed * 2 * math.pi / 60  # W
            
            # Calculate new output power
            output_power = self._calculate_output_power(input_power, input_speed, input_torque)
            
            # Update drivetrain state
            self.drivetrain_state.input_speed = input_speed
            self.drivetrain_state.input_torque = input_torque
            self.drivetrain_state.input_power = input_power
            self.drivetrain_state.output_power = output_power
            self.drivetrain_state.efficiency = output_power / input_power if input_power > 0 else 0.0
            
            # Calculate output parameters
            self._calculate_output_parameters(input_speed, input_torque)
            
            # Update clutch state
            self._update_clutch_state(input_torque)
            
            # Update flywheel state
            self._update_flywheel_state(input_speed, input_torque)
            
            # Update performance metrics
            self._update_performance_metrics(input_power, output_power)
            
            # Check protection systems
            self._check_protection_systems()
            
            return True
            
        except Exception as e:
            self.logger.error("Error updating drivetrain state: %s", e)
            self._handle_fault("state_update_error", str(e))
            return False
    
    def _calculate_output_power(self, input_power: float, input_speed: float, input_torque: float) -> float:
        """
        Calculate output power from input power.
        
        Args:
            input_power: Input power (W)
            input_speed: Input speed (RPM)
            input_torque: Input torque (N·m)
            
        Returns:
            Output power (W)
        """
        try:
            # Calculate losses
            mechanical_losses = self._calculate_mechanical_losses(input_torque)
            clutch_losses = self._calculate_clutch_losses(input_torque)
            bearing_losses = self._calculate_bearing_losses(input_speed)
            
            total_losses = mechanical_losses + clutch_losses + bearing_losses
            
            # Calculate output power
            output_power = input_power - total_losses
            
            # Ensure non-negative output
            output_power = max(0.0, output_power)
            
            # Limit to rated power
            output_power = min(output_power, self.config.rated_power)
            
            return output_power
            
        except Exception as e:
            self.logger.error("Error calculating output power: %s", e)
            return 0.0
    
    def _calculate_output_parameters(self, input_speed: float, input_torque: float) -> None:
        """
        Calculate output speed and torque.
        
        Args:
            input_speed: Input speed (RPM)
            input_torque: Input torque (N·m)
        """
        try:
            # Calculate output speed through gearbox and sprocket ratios
            self.drivetrain_state.output_speed = input_speed / (self.config.gear_ratio * self.config.sprocket_ratio)
            
            # Calculate output torque (considering efficiency)
            self.drivetrain_state.output_torque = input_torque * self.config.gear_ratio * self.config.sprocket_ratio * self.drivetrain_state.efficiency
            
            # Calculate chain tension
            self.drivetrain_state.chain_tension = self._calculate_chain_tension(input_torque)
            
        except Exception as e:
            self.logger.error("Error calculating output parameters: %s", e)
    
    def _calculate_chain_tension(self, input_torque: float) -> float:
        """
        Calculate chain tension.
        
        Args:
            input_torque: Input torque (N·m)
            
        Returns:
            Chain tension (N)
        """
        try:
            # Simplified chain tension calculation
            # T = 2 × T_input / D_sprocket
            sprocket_diameter = 0.5  # m (assumed)
            chain_tension = 2 * input_torque / sprocket_diameter
            
            return chain_tension
            
        except Exception as e:
            self.logger.error("Error calculating chain tension: %s", e)
            return 0.0
    
    def _update_clutch_state(self, input_torque: float) -> None:
        """
        Update clutch state based on input torque.
        
        Args:
            input_torque: Input torque (N·m)
        """
        try:
            engagement_threshold = self.config.clutch_torque_capacity * self.clutch_engagement_threshold
            
            if input_torque >= engagement_threshold:
                if self.drivetrain_state.clutch_state == ClutchState.DISENGAGED:
                    self.drivetrain_state.clutch_state = ClutchState.ENGAGING
                elif self.drivetrain_state.clutch_state == ClutchState.ENGAGING:
                    self.drivetrain_state.clutch_state = ClutchState.ENGAGED
                elif self.drivetrain_state.clutch_state == ClutchState.ENGAGED:
                    # Check for slipping condition
                    if input_torque > self.config.clutch_torque_capacity:
                        self.drivetrain_state.clutch_state = ClutchState.SLIPPING
            else:
                self.drivetrain_state.clutch_state = ClutchState.DISENGAGED
                
        except Exception as e:
            self.logger.error("Error updating clutch state: %s", e)
    
    def _update_flywheel_state(self, input_speed: float, input_torque: float) -> None:
        """
        Update flywheel state.
        
        Args:
            input_speed: Input speed (RPM)
            input_torque: Input torque (N·m)
        """
        try:
            # Update flywheel speed (assume direct coupling)
            self.drivetrain_state.flywheel_speed = input_speed
            
            # Calculate flywheel energy: E = 0.5 × I × ω²
            angular_velocity = input_speed * 2 * math.pi / 60  # rad/s
            self.drivetrain_state.flywheel_energy = 0.5 * self.config.flywheel_moment_of_inertia * (angular_velocity ** 2)
            
        except Exception as e:
            self.logger.error("Error updating flywheel state: %s", e)
    
    def _calculate_mechanical_losses(self, input_torque: float) -> float:
        """
        Calculate mechanical losses.
        
        Returns:
            Mechanical losses (W)
        """
        try:
            # Mechanical losses: P_mech = k_mech × T
            mechanical_losses = self.mechanical_loss_coefficient * input_torque
            
            return mechanical_losses
            
        except Exception as e:
            self.logger.error("Error calculating mechanical losses: %s", e)
            return 0.0
    
    def _calculate_clutch_losses(self, input_torque: float) -> float:
        """
        Calculate clutch losses.
        
        Returns:
            Clutch losses (W)
        """
        try:
            # Clutch losses depend on clutch state
            if self.drivetrain_state.clutch_state == ClutchState.SLIPPING:
                clutch_losses = self.clutch_loss_coefficient * input_torque
            else:
                clutch_losses = 0.0
            
            return clutch_losses
            
        except Exception as e:
            self.logger.error("Error calculating clutch losses: %s", e)
            return 0.0
    
    def _calculate_bearing_losses(self, input_speed: float) -> float:
        """
        Calculate bearing losses.
        
        Returns:
            Bearing losses (W)
        """
        try:
            # Bearing losses: P_bearing = k_bearing × ω
            bearing_losses = self.bearing_loss_coefficient * input_speed
            
            return bearing_losses
            
        except Exception as e:
            self.logger.error("Error calculating bearing losses: %s", e)
            return 0.0
    
    def _update_performance_metrics(self, input_power: float, output_power: float) -> None:
        """
        Update performance metrics.
        
        Args:
            input_power: Input power (W)
            output_power: Output power (W)
        """
        try:
            # Update energy tracking
            self.performance_metrics['total_energy_transmitted'] += input_power * 0.001  # kWh
            self.performance_metrics['total_energy_losses'] += (input_power - output_power) * 0.001  # kWh
            
            # Update peak power
            if input_power > self.performance_metrics['peak_power_transmitted']:
                self.performance_metrics['peak_power_transmitted'] = input_power
            
            # Update losses
            mechanical_losses = self._calculate_mechanical_losses(self.drivetrain_state.input_torque)
            clutch_losses = self._calculate_clutch_losses(self.drivetrain_state.input_torque)
            bearing_losses = self._calculate_bearing_losses(self.drivetrain_state.input_speed)
            
            self.performance_metrics['mechanical_losses'] += mechanical_losses * 0.001  # kWh
            self.performance_metrics['clutch_losses'] += clutch_losses * 0.001  # kWh
            self.performance_metrics['bearing_losses'] += bearing_losses * 0.001  # kWh
            
            # Update operating hours
            self.performance_metrics['operating_hours'] += 0.001  # hours
            
            # Calculate average efficiency
            if self.performance_metrics['total_energy_transmitted'] > 0:
                self.performance_metrics['average_efficiency'] = (
                    (self.performance_metrics['total_energy_transmitted'] - 
                     self.performance_metrics['total_energy_losses']) / 
                    self.performance_metrics['total_energy_transmitted']
                )
            
        except Exception as e:
            self.logger.error("Error updating performance metrics: %s", e)
    
    def _check_protection_systems(self) -> None:
        """Check all protection systems."""
        try:
            # Overspeed protection
            if self.drivetrain_state.input_speed > self.config.max_speed:
                self._handle_fault("overspeed", f"Speed {self.drivetrain_state.input_speed:.1f} RPM exceeds limit")
            
            # Overtorque protection
            if self.drivetrain_state.input_torque > self.config.rated_torque * 1.2:
                self._handle_fault("overtorque", f"Torque {self.drivetrain_state.input_torque:.1f} N·m exceeds limit")
            
            # Overload protection
            if self.drivetrain_state.input_power > self.config.rated_power * 1.1:
                self._handle_fault("overload", f"Power {self.drivetrain_state.input_power:.1f} W exceeds limit")
            
            # Chain tension protection
            if self.drivetrain_state.chain_tension > self.config.max_chain_tension:
                self._handle_fault("excessive_chain_tension", f"Chain tension {self.drivetrain_state.chain_tension:.1f} N exceeds limit")
                
        except Exception as e:
            self.logger.error("Error checking protection systems: %s", e)
    
    def _handle_fault(self, fault_type: str, fault_message: str) -> None:
        """
        Handle drivetrain faults.
        
        Args:
            fault_type: Type of fault
            fault_message: Fault message
        """
        try:
            self.logger.error("Drivetrain fault: %s - %s", fault_type, fault_message)
            
            # Update system state
            self.system_state = DrivetrainSystemState.FAULT
            
            # Update performance metrics
            self.performance_metrics['fault_count'] += 1
            
            # Record fault
            self._record_operation('fault', {
                'fault_type': fault_type,
                'fault_message': fault_message,
                'system_state': self.system_state.value
            })
            
        except Exception as e:
            self.logger.error("Error handling fault: %s", e)
    
    def _record_operation(self, operation_type: str, data: Dict[str, Any]) -> None:
        """
        Record operation in history.
        
        Args:
            operation_type: Type of operation
            data: Operation data
        """
        try:
            operation_record = {
                'timestamp': time.time(),
                'type': operation_type,
                'data': data,
                'drivetrain_state': {
                    'system_state': self.system_state.value,
                    'input_power': self.drivetrain_state.input_power,
                    'output_power': self.drivetrain_state.output_power,
                    'efficiency': self.drivetrain_state.efficiency,
                    'clutch_state': self.drivetrain_state.clutch_state.value,
                    'chain_tension': self.drivetrain_state.chain_tension,
                    'flywheel_energy': self.drivetrain_state.flywheel_energy
                }
            }
            
            self.operation_history.append(operation_record)
            
        except Exception as e:
            self.logger.error("Error recording operation: %s", e)
    
    def get_drivetrain_state(self) -> DrivetrainState:
        """
        Get current drivetrain state.
        
        Returns:
            Current drivetrain state
        """
        return self.drivetrain_state
    
    def get_state(self) -> Dict[str, Any]:
        """
        Get the current drivetrain state as a dictionary for API compatibility.
        
        Returns:
            Dictionary representation of drivetrain state
        """
        return {
            'input_speed': self.drivetrain_state.input_speed,
            'input_torque': self.drivetrain_state.input_torque,
            'input_power': self.drivetrain_state.input_power,
            'output_speed': self.drivetrain_state.output_speed,
            'output_torque': self.drivetrain_state.output_torque,
            'output_power': self.drivetrain_state.output_power,
            'efficiency': self.drivetrain_state.efficiency,
            'chain_tension': self.drivetrain_state.chain_tension,
            'clutch_state': self.drivetrain_state.clutch_state.value,
            'flywheel_speed': self.drivetrain_state.flywheel_speed,
            'flywheel_energy': self.drivetrain_state.flywheel_energy,
            'system_state': self.system_state.value,
            'chain_radius': 1.0,  # For compatibility with existing code
            'angular_velocity': self.drivetrain_state.input_speed * 2 * math.pi / 60,  # rad/s
            'angular_position': 0.0  # Would need to track this over time
        }
    
    def get_system_state(self) -> DrivetrainSystemState:
        """
        Get current system state.
        
        Returns:
            Current system state
        """
        return self.system_state
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Get performance metrics.
        
        Returns:
            Performance metrics dictionary
        """
        return self.performance_metrics.copy()
    
    def get_operation_history(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get operation history.
        
        Args:
            limit: Maximum number of operations to return
            
        Returns:
            List of operation records
        """
        if limit is None:
            return self.operation_history.copy()
        else:
            return self.operation_history[-limit:]
    
    def is_operating(self) -> bool:
        """
        Check if drivetrain is operating.
        
        Returns:
            True if operating
        """
        return self.system_state in [DrivetrainSystemState.OPERATING, DrivetrainSystemState.OVERLOADED]
    
    def get_efficiency(self) -> float:
        """
        Get current drivetrain efficiency.
        
        Returns:
            Current efficiency (0.0 to 1.0)
        """
        return self.drivetrain_state.efficiency
    
    def get_chain_tension(self) -> float:
        """
        Get current chain tension.
        
        Returns:
            Current chain tension (N)
        """
        return self.drivetrain_state.chain_tension
    
    def get_clutch_state(self) -> ClutchState:
        """
        Get current clutch state.
        
        Returns:
            Current clutch state
        """
        return self.drivetrain_state.clutch_state
    
    def get_flywheel_energy(self) -> float:
        """
        Get current flywheel energy.
        
        Returns:
            Current flywheel energy (J)
        """
        return self.drivetrain_state.flywheel_energy
    
    def reset(self) -> None:
        """Reset drivetrain to initial state."""
        self.drivetrain_state = DrivetrainState()
        self.system_state = DrivetrainSystemState.IDLE
        self.operation_history.clear()
        self.performance_metrics = {
            'total_energy_transmitted': 0.0,
            'total_energy_losses': 0.0,
            'peak_power_transmitted': 0.0,
            'average_efficiency': 0.0,
            'mechanical_losses': 0.0,
            'clutch_losses': 0.0,
            'bearing_losses': 0.0,
            'operating_hours': 0.0,
            'fault_count': 0
        }
        self.logger.info("Integrated drivetrain reset")

    def update(self, dt: float) -> None:
        """
        Update drivetrain state for a simulation timestep.
        Args:
            dt: Time step in seconds
        """
        try:
            # Advance operating hours
            self.performance_metrics['operating_hours'] += dt / 3600.0
            # Optionally update performance metrics or simulate wear, losses, etc.
            # For now, just update average efficiency if possible
            if self.drivetrain_state.input_power > 0:
                self.performance_metrics['average_efficiency'] = self.drivetrain_state.output_power / self.drivetrain_state.input_power
        except Exception as e:
            self.logger.error("Error updating drivetrain: %s", e)

    def get_comprehensive_state(self) -> Dict[str, Any]:
        """
        Get comprehensive drivetrain state including all parameters.
        
        Returns:
            Comprehensive state dictionary
        """
        try:
            return {
                'system_state': self.system_state.value,
                'drivetrain_state': {
                    'input_speed': self.drivetrain_state.input_speed,
                    'input_torque': self.drivetrain_state.input_torque,
                    'input_power': self.drivetrain_state.input_power,
                    'output_speed': self.drivetrain_state.output_speed,
                    'output_torque': self.drivetrain_state.output_torque,
                    'output_power': self.drivetrain_state.output_power,
                    'efficiency': self.drivetrain_state.efficiency,
                    'chain_tension': self.drivetrain_state.chain_tension,
                    'clutch_state': self.drivetrain_state.clutch_state.value,
                    'flywheel_speed': self.drivetrain_state.flywheel_speed,
                    'flywheel_energy': self.drivetrain_state.flywheel_energy
                },
                'performance_metrics': self.performance_metrics.copy(),
                'config': {
                    'rated_power': self.config.rated_power,
                    'rated_speed': self.config.rated_speed,
                    'rated_torque': self.config.rated_torque,
                    'gear_ratio': self.config.gear_ratio,
                    'sprocket_ratio': self.config.sprocket_ratio,
                    'efficiency_nominal': self.config.efficiency_nominal
                }
            }
        except Exception as e:
            self.logger.error("Error getting comprehensive state: %s", e)
            return {
                'system_state': 'error',
                'error': str(e)
            }

def create_standard_kpp_drivetrain() -> IntegratedDrivetrain:
    """
    Create a standard KPP drivetrain with default configuration.
    
    Returns:
        IntegratedDrivetrain: Configured drivetrain instance
    """
    config = DrivetrainConfig(
        rated_power=50000.0,  # 50 kW
        rated_speed=1500.0,   # 1500 RPM
        rated_torque=318.3,   # N·m
        gear_ratio=1.0,
        sprocket_ratio=1.0,
        clutch_torque_capacity=500.0,  # N·m
        flywheel_moment_of_inertia=10.0,  # kg·m²
        max_chain_tension=50000.0,  # N
        efficiency_nominal=0.95,
        max_speed=2000.0  # RPM
    )
    
    return IntegratedDrivetrain(config)


