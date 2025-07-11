"""
Pneumatic system integration for KPP simulation.
Handles:
- Air injection and venting
- Pressure-based state transitions
- Thermal effects on air volume
- System pressure management
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
import logging
from enum import Enum
from dataclasses import dataclass
from simulation.components.floater.enhanced_floater import FloaterState

logger = logging.getLogger(__name__)

@dataclass
class PneumaticSystemConfig:
    """Configuration for pneumatic system"""
    max_pressure: float = 10.0  # bar
    min_pressure: float = 1.0   # bar
    max_flow_rate: float = 0.1  # m³/s
    compressor_power: float = 5000.0  # W
    thermal_efficiency: float = 0.85
    target_fill_time: float = 2.0  # seconds
    target_vent_time: float = 1.5  # seconds

@dataclass
class PneumaticState:
    """State tracking for pneumatic system"""
    system_pressure: float  # bar
    reservoir_volume: float  # m³
    compressor_state: bool  # True if running
    total_energy_used: float  # Joules
    active_ports: List[int]  # Indices of active injection/vent ports

class PneumaticCommand(Enum):
    """Commands for pneumatic system"""
    FILL = "fill"
    VENT = "vent"
    HOLD = "hold"
    EMERGENCY_VENT = "emergency_vent"

def compute_air_properties(pressure: float,
                         temperature: float,
                         volume: float) -> Dict[str, float]:
    """
    Compute air properties using real gas model.
    
    Args:
        pressure: Pressure (bar)
        temperature: Temperature (K)
        volume: Volume (m³)
        
    Returns:
        Dictionary of air properties
    """
    # Input validation
    if temperature <= 0:
        raise ValueError("Temperature must be positive")
    if volume <= 0:
        raise ValueError("Volume must be positive")
        
    # Convert bar to Pa
    p_pa = pressure * 1e5
    
    # Gas constant for air
    R = 287.058  # J/(kg·K)
    
    # Compute density using real gas factor
    # Z ≈ 1 for moderate pressures
    Z = max(0.1, 1.0 - (p_pa/(R*temperature))*1e-5)  # Prevent Z from getting too close to zero
    density = p_pa/(Z*R*temperature)
    
    # Compute mass
    mass = density * volume
    
    # Specific heat ratio
    gamma = 1.4
    
    # Speed of sound
    c = np.sqrt(gamma*R*temperature)
    
    return {
        'density': density,
        'mass': mass,
        'speed_of_sound': c,
        'Z_factor': Z
    }

def compute_flow_rate(p1: float,
                     p2: float,
                     temperature: float,
                     orifice_area: float) -> float:
    """
    Compute air flow rate through orifice.
    
    Args:
        p1: Upstream pressure (bar)
        p2: Downstream pressure (bar)
        temperature: Temperature (K)
        orifice_area: Flow area (m²)
        
    Returns:
        Mass flow rate (kg/s)
    """
    # Convert pressures to Pa
    p1_pa = p1 * 1e5
    p2_pa = p2 * 1e5
    
    # Gas properties
    R = 287.058  # J/(kg·K)
    gamma = 1.4
    
    # Critical pressure ratio
    p_crit = p1_pa * (2/(gamma + 1))**(gamma/(gamma - 1))
    
    # Discharge coefficient
    Cd = 0.85
    
    if p2_pa <= p_crit:
        # Choked flow
        mdot = (Cd * orifice_area * p1_pa * 
                np.sqrt(gamma/(R*temperature)) * 
                (2/(gamma + 1))**((gamma + 1)/(2*(gamma - 1))))
    else:
        # Subsonic flow
        mdot = (Cd * orifice_area * 
                np.sqrt(2*gamma/(gamma - 1) * 
                       p1_pa/temperature * R *
                       ((p2_pa/p1_pa)**(2/gamma) - 
                        (p2_pa/p1_pa)**((gamma + 1)/gamma))))
    
    return mdot

def update_thermal_state(current_temp: float,
                        ambient_temp: float,
                        power_input: float,
                        mass: float,
                        dt: float) -> float:
    """
    Update air temperature considering compression and heat transfer.
    
    Args:
        current_temp: Current temperature (K)
        ambient_temp: Ambient temperature (K)
        power_input: Power input from compression (W)
        mass: Air mass (kg)
        dt: Time step (s)
        
    Returns:
        Updated temperature (K)
    """
    # Specific heat of air
    cp = 1005.0  # J/(kg·K)
    
    # Heat transfer coefficient (simplified)
    h = 10.0  # W/(m²·K)
    surface_area = 0.1  # m² (simplified)
    
    # Temperature change from power input
    dT_power = power_input * dt / (mass * cp)
    
    # Temperature change from heat transfer
    dT_transfer = h * surface_area * (ambient_temp - current_temp) * dt / (mass * cp)
    
    return current_temp + dT_power + dT_transfer

def compute_state_transition(current_state: FloaterState,
                           pressure: float,
                           fill_level: float,
                           temperature: float) -> Optional[FloaterState]:
    """
    Determine if floater should transition to new state.
    
    Args:
        current_state: Current FloaterState
        pressure: Current pressure (bar)
        fill_level: Current fill level (0-1)
        temperature: Current temperature (K)
        
    Returns:
        New state if transition needed, None otherwise
    """
    if current_state == FloaterState.EMPTY and pressure > 1.2:
        return FloaterState.FILLING
    
    elif current_state == FloaterState.FILLING:
        if fill_level >= 0.95:
            return FloaterState.FULL
        elif pressure < 1.1:
            return FloaterState.EMPTY
            
    elif current_state == FloaterState.FULL:
        if pressure < 1.1:
            return FloaterState.VENTING
        elif temperature > 350:  # Over-temperature protection
            return FloaterState.ERROR
            
    elif current_state == FloaterState.VENTING:
        if fill_level <= 0.05:
            return FloaterState.EMPTY
            
    return None

class PneumaticSystem:
    """Manager for pneumatic system simulation"""
    
    def __init__(self, config: PneumaticSystemConfig):
        """Initialize pneumatic system"""
        self.config = config
        self.state = PneumaticState(
            system_pressure=config.min_pressure,
            reservoir_volume=1.0,  # m³
            compressor_state=False,
            total_energy_used=0.0,
            active_ports=[]
        )
        
    def update(self, dt: float, 
               floaters: List[Dict],
               environment: Dict) -> None:
        """
        Update pneumatic system state.
        
        Args:
            dt: Time step (s)
            floaters: List of floater states
            environment: Environmental conditions
        """
        try:
            # Update compressor state based on pressure
            if self.state.system_pressure < self.config.min_pressure:
                self.state.compressor_state = True
            elif self.state.system_pressure > self.config.max_pressure:
                self.state.compressor_state = False
            
            # Compute compressor work
            if self.state.compressor_state:
                power = self.config.compressor_power * self.config.thermal_efficiency
                self.state.total_energy_used += power * dt
                
                # Pressure increase from compression
                dP = (power * dt) / (self.state.reservoir_volume * 1e5)  # bar
                self.state.system_pressure += dP
            
            # Update active ports
            for i, floater in enumerate(floaters):
                if floater['pneumatic_command'] == PneumaticCommand.FILL:
                    if i not in self.state.active_ports:
                        self.state.active_ports.append(i)
                        
                elif floater['pneumatic_command'] == PneumaticCommand.VENT:
                    if i in self.state.active_ports:
                        self.state.active_ports.remove(i)
            
            # Compute flow rates and update pressures
            for i in self.state.active_ports:
                floater = floaters[i]
                
                if floater['pneumatic_command'] == PneumaticCommand.FILL:
                    # Compute fill rate
                    mdot = compute_flow_rate(
                        self.state.system_pressure,
                        floater['internal_pressure'],
                        environment['temperature'],
                        0.0001  # 1cm² orifice
                    )
                    
                    # Update volumes and pressures
                    dV = mdot * dt / compute_air_properties(
                        floater['internal_pressure'],
                        environment['temperature'],
                        floater['air_volume']
                    )['density']
                    
                    floater['air_volume'] = min(
                        floater['air_volume'] + dV,
                        floater['max_volume']
                    )
                    
                    # Update reservoir pressure
                    self.state.system_pressure -= (
                        dV / self.state.reservoir_volume * 
                        self.state.system_pressure
                    )
                    
                elif floater['pneumatic_command'] == PneumaticCommand.VENT:
                    # Compute vent rate
                    mdot = compute_flow_rate(
                        floater['internal_pressure'],
                        1.0,  # Atmospheric pressure
                        environment['temperature'],
                        0.0002  # 2cm² vent
                    )
                    
                    # Update volume
                    dV = mdot * dt / compute_air_properties(
                        floater['internal_pressure'],
                        environment['temperature'],
                        floater['air_volume']
                    )['density']
                    
                    floater['air_volume'] = max(
                        floater['air_volume'] - dV,
                        0.0
                    )
            
            # Update temperatures
            for i in self.state.active_ports:
                floater = floaters[i]
                
                # Get air properties
                props = compute_air_properties(
                    floater['internal_pressure'],
                    floater['temperature'],
                    floater['air_volume']
                )
                
                # Update temperature
                power_input = (self.config.compressor_power * 
                             self.config.thermal_efficiency *
                             (i in self.state.active_ports))
                
                floater['temperature'] = update_thermal_state(
                    floater['temperature'],
                    environment['temperature'],
                    power_input,
                    props['mass'],
                    dt
                )
                
                # Check for state transitions
                new_state = compute_state_transition(
                    floater['state'],
                    floater['internal_pressure'],
                    floater['air_volume'] / floater['max_volume'],
                    floater['temperature']
                )
                
                if new_state is not None:
                    floater['state'] = new_state
                    logger.info(f"Floater {i} transitioned to {new_state}")
                    
                    # Handle error state
                    if new_state == FloaterState.ERROR:
                        floater['pneumatic_command'] = PneumaticCommand.EMERGENCY_VENT
                        logger.warning(f"Floater {i} entered error state - emergency venting")
        
        except Exception as e:
            logger.error(f"Pneumatic system update failed: {e}")
            # Safe state - stop all operations
            self.state.compressor_state = False
            self.state.active_ports = [] 