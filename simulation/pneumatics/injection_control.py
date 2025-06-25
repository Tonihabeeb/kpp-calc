"""
Phase 2.1: Air Injection Control System for KPP Pneumatic System

This module implements the comprehensive air injection control system that manages
valve timing, pressure delivery, and multi-floater coordination.

Key Features:
- PLC-based valve timing control synchronized with floater positioning
- Dynamic injection pressure management for different depths
- Multi-floater coordination and queue management
- Flow rate control and pressure drop compensation
"""

import logging
import math
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
from utils.logging_setup import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

class InjectionState(Enum):
    """Air injection states."""
    IDLE = "idle"
    READY = "ready"
    INJECTING = "injecting"
    COMPLETED = "completed"
    FAILED = "failed"

class ValveState(Enum):
    """Injection valve states."""
    CLOSED = "closed"
    OPENING = "opening"
    OPEN = "open"
    CLOSING = "closing"

@dataclass
class InjectionValveSpec:
    """Injection valve specifications."""
    response_time: float = 0.1  # seconds (valve opening/closing time)
    max_flow_rate: float = 0.02  # m³/s at standard conditions
    pressure_drop_coefficient: float = 0.1  # Pressure drop factor
    min_operating_pressure: float = 150000.0  # Pa (minimum pressure to operate)

@dataclass
class InjectionSettings:
    """Air injection control settings."""
    injection_duration: float = 2.0  # seconds (standard injection time)
    pressure_margin: float = 10000.0  # Pa (pressure above hydrostatic requirement)
    max_injection_pressure: float = 350000.0  # Pa (safety limit)
    flow_control_factor: float = 0.8  # Factor for flow rate control
    position_tolerance: float = 0.1  # meters (position detection tolerance)
    max_queue_size: int = 10  # Maximum floaters in injection queue

class FloaterInjectionRequest:
    """Request for air injection into a floater."""
    
    def __init__(self, floater_id: str, depth: float, target_volume: float, 
                 position: float, timestamp: float):
        """
        Initialize injection request.
        
        Args:
            floater_id: Unique identifier for the floater
            depth: Current depth in meters
            target_volume: Target air volume to inject (m³)
            position: Current position along chain
            timestamp: Request timestamp
        """
        self.floater_id = floater_id
        self.depth = depth
        self.target_volume = target_volume
        self.position = position
        self.timestamp = timestamp
        self.state = InjectionState.READY
        self.injected_volume = 0.0
        self.injection_pressure = 0.0
        self.start_time = 0.0
        self.completion_time = 0.0

class AirInjectionController:
    """
    Comprehensive air injection control system.
    
    This system manages:
    - Valve timing control synchronized with floater positions
    - Dynamic pressure delivery based on depth requirements
    - Multi-floater coordination and queue management
    - Flow rate control and pressure drop compensation
    """
    
    def __init__(self, 
                 valve_spec: Optional[InjectionValveSpec] = None,
                 injection_settings: Optional[InjectionSettings] = None,
                 water_density: float = 1000.0,  # kg/m³
                 gravity: float = 9.81):  # m/s²
        """
        Initialize the air injection controller.
        
        Args:
            valve_spec: Injection valve specifications
            injection_settings: Injection control settings
            water_density: Water density for hydrostatic calculations
            gravity: Gravitational acceleration
        """
        self.valve_spec = valve_spec or InjectionValveSpec()
        self.settings = injection_settings or InjectionSettings()
        self.water_density = water_density
        self.gravity = gravity
        
        # Control state
        self.valve_state = ValveState.CLOSED
        self.current_injection = None
        self.injection_queue = []
        self.valve_position = 0.0  # 0.0 = closed, 1.0 = fully open
        
        # Performance tracking
        self.total_injections = 0
        self.successful_injections = 0
        self.failed_injections = 0
        self.total_air_injected = 0.0
        self.total_injection_time = 0.0
        
        # Pressure and flow monitoring
        self.current_flow_rate = 0.0
        self.injection_pressure = 0.0
        self.pressure_drop = 0.0
        
        logger.info(f"AirInjectionController initialized: "
                   f"valve response {self.valve_spec.response_time:.1f}s, "
                   f"max flow {self.valve_spec.max_flow_rate*1000:.1f} L/s")
    
    def calculate_required_injection_pressure(self, depth: float) -> float:
        """
        Calculate minimum injection pressure required for given depth.
        
        Args:
            depth: Water depth in meters
            
        Returns:
            Required injection pressure in Pa
        """
        # Hydrostatic pressure at depth
        hydrostatic_pressure = self.water_density * self.gravity * depth
        
        # Add atmospheric pressure and safety margin
        required_pressure = 101325.0 + hydrostatic_pressure + self.settings.pressure_margin
        
        # Limit to maximum injection pressure
        return min(required_pressure, self.settings.max_injection_pressure)
    
    def calculate_injection_flow_rate(self, supply_pressure: float, 
                                    injection_pressure: float) -> float:
        """
        Calculate injection flow rate based on pressure difference.
        
        Args:
            supply_pressure: Tank supply pressure in Pa
            injection_pressure: Required injection pressure in Pa
            
        Returns:
            Flow rate in m³/s at standard conditions
        """
        if supply_pressure <= injection_pressure:
            return 0.0
        
        # Pressure drop across valve
        pressure_drop = supply_pressure - injection_pressure
        self.pressure_drop = pressure_drop
        
        # Flow rate calculation (simplified orifice flow)
        max_flow = self.valve_spec.max_flow_rate * self.valve_position
        pressure_factor = math.sqrt(pressure_drop / 100000.0)  # Normalized to 1 bar
        
        flow_rate = max_flow * pressure_factor * self.settings.flow_control_factor
        
        return min(flow_rate, self.valve_spec.max_flow_rate)
    
    def add_injection_request(self, request: FloaterInjectionRequest) -> bool:
        """
        Add floater injection request to queue.
        
        Args:
            request: Injection request to add
            
        Returns:
            True if request was added successfully
        """
        if len(self.injection_queue) >= self.settings.max_queue_size:
            logger.warning(f"Injection queue full, rejecting request for floater {request.floater_id}")
            return False
        
        # Calculate required injection pressure
        request.injection_pressure = self.calculate_required_injection_pressure(request.depth)
        
        # Add to queue
        self.injection_queue.append(request)
        
        logger.info(f"Added injection request for floater {request.floater_id}: "
                   f"depth={request.depth:.1f}m, volume={request.target_volume*1000:.1f}L, "
                   f"pressure={request.injection_pressure/1000:.1f} kPa")
        
        return True
    
    def can_supply_injection_pressure(self, supply_pressure: float, 
                                    required_pressure: float) -> bool:
        """
        Check if supply pressure is sufficient for injection.
        
        Args:
            supply_pressure: Available supply pressure in Pa
            required_pressure: Required injection pressure in Pa
            
        Returns:
            True if supply pressure is adequate
        """
        return supply_pressure >= (required_pressure + self.settings.pressure_margin)
    
    def start_injection(self, request: FloaterInjectionRequest, 
                       current_time: float) -> bool:
        """
        Start air injection for given request.
        
        Args:
            request: Injection request to start
            current_time: Current simulation time
            
        Returns:
            True if injection started successfully
        """
        if self.current_injection is not None:
            logger.warning(f"Cannot start injection for {request.floater_id}: injection already in progress")
            return False
        
        # Start injection
        self.current_injection = request
        request.state = InjectionState.INJECTING
        request.start_time = current_time
        self.valve_state = ValveState.OPENING
        
        self.total_injections += 1
        
        logger.info(f"Starting injection for floater {request.floater_id}: "
                   f"target={request.target_volume*1000:.1f}L at {request.injection_pressure/1000:.1f} kPa")
        
        return True
    
    def update_valve_position(self, dt: float) -> None:
        """
        Update valve position based on state and timing.
        
        Args:
            dt: Time step in seconds
        """
        if self.valve_state == ValveState.OPENING:
            # Open valve
            opening_rate = 1.0 / self.valve_spec.response_time
            self.valve_position += opening_rate * dt
            
            if self.valve_position >= 1.0:
                self.valve_position = 1.0
                self.valve_state = ValveState.OPEN
                
        elif self.valve_state == ValveState.CLOSING:
            # Close valve
            closing_rate = 1.0 / self.valve_spec.response_time
            self.valve_position -= closing_rate * dt
            
            if self.valve_position <= 0.0:
                self.valve_position = 0.0
                self.valve_state = ValveState.CLOSED
    
    def injection_step(self, dt: float, current_time: float, 
                      supply_pressure: float) -> Dict[str, Any]:
        """
        Execute one injection control step.
        
        Args:
            dt: Time step in seconds
            current_time: Current simulation time
            supply_pressure: Available supply pressure from tank
            
        Returns:
            Injection step results
        """
        # Update valve position
        self.update_valve_position(dt)
        
        # Process current injection
        if self.current_injection is not None:
            request = self.current_injection
            
            # Calculate flow rate
            self.current_flow_rate = self.calculate_injection_flow_rate(
                supply_pressure, request.injection_pressure)
            
            # Inject air
            if self.valve_state == ValveState.OPEN and self.current_flow_rate > 0:
                injected_this_step = self.current_flow_rate * dt
                request.injected_volume += injected_this_step
                self.total_air_injected += injected_this_step
                
                # Check if injection is complete
                injection_time = current_time - request.start_time
                volume_complete = request.injected_volume >= request.target_volume
                time_complete = injection_time >= self.settings.injection_duration
                
                if volume_complete or time_complete:
                    # Complete injection
                    request.completion_time = current_time
                    request.state = InjectionState.COMPLETED
                    self.valve_state = ValveState.CLOSING
                    
                    if volume_complete:
                        self.successful_injections += 1
                        logger.info(f"Injection completed for floater {request.floater_id}: "
                                   f"injected {request.injected_volume*1000:.1f}L in {injection_time:.1f}s")
                    else:
                        self.failed_injections += 1
                        logger.warning(f"Injection timeout for floater {request.floater_id}: "
                                      f"only injected {request.injected_volume*1000:.1f}L of {request.target_volume*1000:.1f}L")
                    
                    self.total_injection_time += injection_time
                    self.current_injection = None
        
        # Check for new injections
        if (self.current_injection is None and 
            self.valve_state == ValveState.CLOSED and 
            len(self.injection_queue) > 0):
            
            # Find next suitable injection
            for i, request in enumerate(self.injection_queue):
                if self.can_supply_injection_pressure(supply_pressure, request.injection_pressure):
                    # Start this injection
                    self.injection_queue.pop(i)
                    self.start_injection(request, current_time)
                    break
        
        return {
            'valve_state': self.valve_state.value,
            'valve_position': self.valve_position,
            'current_flow_rate': self.current_flow_rate,
            'injection_pressure': self.injection_pressure,
            'pressure_drop': self.pressure_drop,
            'queue_length': len(self.injection_queue),
            'active_injection': self.current_injection.floater_id if self.current_injection else None,
            'injected_volume': self.current_injection.injected_volume if self.current_injection else 0.0,
            'air_consumed': self.current_flow_rate * dt if self.current_injection else 0.0
        }
    
    def get_injection_status(self) -> Dict[str, Any]:
        """Get comprehensive injection system status."""
        efficiency = (self.successful_injections / self.total_injections 
                     if self.total_injections > 0 else 0.0)
        
        avg_injection_time = (self.total_injection_time / self.successful_injections 
                             if self.successful_injections > 0 else 0.0)
        
        return {
            'valve_state': self.valve_state.value,
            'valve_position': self.valve_position,
            'current_flow_rate_l_per_s': self.current_flow_rate * 1000.0,
            'injection_pressure_bar': self.injection_pressure / 100000.0,
            'pressure_drop_bar': self.pressure_drop / 100000.0,
            'queue_length': len(self.injection_queue),
            'total_injections': self.total_injections,
            'successful_injections': self.successful_injections,
            'failed_injections': self.failed_injections,
            'injection_efficiency': efficiency,
            'total_air_injected_m3': self.total_air_injected,
            'avg_injection_time_s': avg_injection_time,
            'active_injection_id': self.current_injection.floater_id if self.current_injection else None
        }
    
    def calculate_water_displacement_work(self, injected_volume: float, 
                                        depth: float) -> float:
        """
        Calculate mechanical work done by water displacement.
        
        Args:
            injected_volume: Volume of air injected (m³)
            depth: Water depth (m)
            
        Returns:
            Work done in Joules
        """
        # Work = ρ * g * V * H (energy to lift displaced water)
        work = self.water_density * self.gravity * injected_volume * depth
        return work
    
    def reset_injection_system(self) -> None:
        """Reset injection system to initial state."""
        self.valve_state = ValveState.CLOSED
        self.current_injection = None
        self.injection_queue.clear()
        self.valve_position = 0.0
        self.current_flow_rate = 0.0
        self.injection_pressure = 0.0
        self.pressure_drop = 0.0
        
        # Reset performance counters
        self.total_injections = 0
        self.successful_injections = 0
        self.failed_injections = 0
        self.total_air_injected = 0.0
        self.total_injection_time = 0.0
        
        logger.info("Air injection system reset to initial state")


def create_standard_kpp_injection_controller() -> AirInjectionController:
    """Create a standard KPP air injection controller with realistic parameters."""
    valve_spec = InjectionValveSpec(
        response_time=0.1,  # 100ms valve response
        max_flow_rate=0.05,  # 50 L/s maximum flow (increased for better performance)
        pressure_drop_coefficient=0.1,
        min_operating_pressure=150000.0  # 1.5 bar minimum
    )
    
    injection_settings = InjectionSettings(
        injection_duration=3.0,  # 3 second standard injection (increased)
        pressure_margin=10000.0,  # 0.1 bar safety margin
        max_injection_pressure=350000.0,  # 3.5 bar maximum
        flow_control_factor=0.9,  # 90% flow control efficiency (improved)
        position_tolerance=0.1,  # 10cm position tolerance
        max_queue_size=10  # Up to 10 floaters in queue
    )
    
    return AirInjectionController(valve_spec, injection_settings)
