"""
Main simulation module for KPP system.
Integrates all components and handles time-stepping physics calculations.
"""

from dataclasses import dataclass
from typing import List, Dict, Optional
import numpy as np
import pandas as pd
from datetime import datetime

from .components.floater.enhanced_floater import EnhancedFloater, FloaterState
from .components.environment import Environment
from .components.pneumatics import PneumaticSystem
from .components.drivetrain import IntegratedDrivetrain
from .control.controller import Controller, ControlConfig, SystemState

@dataclass
class SimulationConfig:
    """Configuration parameters for KPP simulation"""
    # Tank geometry
    tank_height: float = 10.0  # m
    tank_diameter: float = 2.0  # m
    
    # Floater parameters
    num_floaters: int = 12
    floater_volume: float = 0.04  # m³
    floater_mass_empty: float = 5.0  # kg
    floater_cross_section: float = 0.1  # m²
    
    # Environment parameters
    water_density: float = 1000.0  # kg/m³
    gravity: float = 9.81  # m/s²
    drag_coefficient: float = 0.6
    
    # Drivetrain parameters
    sprocket_radius: float = 0.25  # m
    flywheel_inertia: float = 50.0  # kg·m²
    
    # Enhancement flags
    h1_enabled: bool = False  # Nanobubble drag reduction
    h1_density_reduction: float = 0.0  # e.g., 0.05 for 5% reduction
    
    h2_enabled: bool = False  # Thermal (isothermal) enhancement
    h2_buoyancy_boost: float = 0.0  # e.g., 0.05 for 5% boost
    
    h3_enabled: bool = False  # Pulse-and-coast
    h3_coast_time: float = 5.0  # s
    h3_pulse_time: float = 2.0  # s
    h3_pulse_torque: float = 800.0  # N·m

class KPP_Simulation:
    """
    Main simulation class for Kinetic Power Plant.
    
    Integrates all components:
    - Floaters with enhanced physics
    - Environment with H1/H2 effects
    - Pneumatic system for air injection
    - Drivetrain with H3 capability
    - Control system for coordination
    """
    
    def __init__(self, config: Optional[SimulationConfig] = None):
        """Initialize simulation with given configuration"""
        self.config = config or SimulationConfig()
        
        # Initialize environment
        self.environment = Environment(
            density=self.config.water_density,
            gravity=self.config.gravity,
            drag_coefficient=self.config.drag_coefficient
        )
        self.environment.H1_active = self.config.h1_enabled
        self.environment.H1_density_reduction = self.config.h1_density_reduction
        self.environment.H2_active = self.config.h2_enabled
        self.environment.H2_buoyancy_boost = self.config.h2_buoyancy_boost
        
        # Initialize pneumatic system
        self.pneumatics = PneumaticSystem()
        
        # Initialize drivetrain
        self.drivetrain = Drivetrain(
            sprocket_radius=self.config.sprocket_radius,
            flywheel_inertia=self.config.flywheel_inertia
        )
        
        # Initialize control system
        control_config = ControlConfig(
            h3_enabled=self.config.h3_enabled,
            coast_time=self.config.h3_coast_time,
            pulse_time=self.config.h3_pulse_time,
            pulse_generator_torque=self.config.h3_pulse_torque
        )
        self.controller = Controller(control_config)
        
        # Create floaters
        self.floaters: List[EnhancedFloater] = []
        self._initialize_floaters()
        
        # Simulation state
        self.time = 0.0
        self.cycle_count = 0
        self.total_generator_energy = 0.0
        self.total_compressor_energy = 0.0
        
        # Data logging
        self.log_data: List[Dict] = []
        
    def _initialize_floaters(self) -> None:
        """Create and position floaters around the chain"""
        loop_length = 2 * self.config.tank_height
        spacing = loop_length / self.config.num_floaters
        
        for i in range(self.config.num_floaters):
            floater = EnhancedFloater(
                volume=self.config.floater_volume,
                mass_empty=self.config.floater_mass_empty,
                cross_section=self.config.floater_cross_section
            )
            
            # Position floater along chain
            s_position = i * spacing
            floater.s_position = s_position
            
            # Set initial state (alternating)
            if i < self.config.num_floaters // 2:
                floater.state = FloaterState.AIR  # ascending side
            else:
                floater.state = FloaterState.WATER  # descending side
            
            # Update vertical position
            if s_position <= self.config.tank_height:
                floater.vertical_position = s_position
            else:
                floater.vertical_position = 2 * self.config.tank_height - s_position
            
            self.floaters.append(floater)
            self.controller.initialize_floater(i, floater.state)
    
    def _compute_forces(self) -> float:
        """
        Compute net force on chain from all floaters.
        Returns net upward force (N).
        """
        net_force = 0.0
        chain_speed = self.drivetrain.get_chain_speed()
        
        for floater in self.floaters:
            # Get effective water density (may be reduced by H1)
            rho = self.environment.effective_density(floater.state)
            
            # Compute forces
            buoyant_force = floater.compute_buoyant_force(rho, self.environment.gravity)
            if self.environment.H2_active and floater.state == FloaterState.AIR:
                buoyant_force *= (1 + self.environment.H2_buoyancy_boost)
            
            weight = floater.compute_weight(self.environment.gravity)
            
            # Drag depends on direction
            if floater.state == FloaterState.AIR:  # ascending
                drag = floater.compute_drag_force(
                    rho, 
                    self.environment.drag_coefficient,
                    floater.cross_section,
                    chain_speed
                )
                net_force += (buoyant_force - weight - drag)
            else:  # descending
                drag = floater.compute_drag_force(
                    rho,
                    self.environment.drag_coefficient,
                    floater.cross_section,
                    chain_speed
                )
                net_force += (buoyant_force + drag - weight)
        
        return net_force
    
    def _handle_transitions(self, dt: float) -> None:
        """Handle floater transitions at top and bottom"""
        for i, floater in enumerate(self.floaters):
            # Check bottom transition
            if self.controller.handle_bottom_sensor(i, floater.vertical_position):
                energy_used = self.pneumatics.inject_air(
                    floater,
                    self.environment,
                    depth=self.config.tank_height
                )
                self.total_compressor_energy += energy_used
            
            # Check top transition
            if self.controller.handle_top_sensor(i, floater.vertical_position):
                self.pneumatics.vent_air(floater)
    
    def _update_positions(self, dt: float) -> None:
        """Update positions of all floaters based on chain speed"""
        chain_speed = self.drivetrain.get_chain_speed()
        loop_length = 2 * self.config.tank_height
        
        for floater in self.floaters:
            # Update chain position
            floater.s_position = (floater.s_position + chain_speed * dt) % loop_length
            
            # Update vertical position for visualization/logging
            if floater.s_position <= self.config.tank_height:
                floater.vertical_position = floater.s_position
            else:
                floater.vertical_position = 2 * self.config.tank_height - floater.s_position
    
    def _log_state(self) -> None:
        """Log current simulation state"""
        chain_speed = self.drivetrain.get_chain_speed()
        clutch_engaged = self.drivetrain.clutch_engaged
        
        # Compute instantaneous powers
        if clutch_engaged:
            generator_power = self.drivetrain.generator_torque * self.drivetrain.omega
        else:
            generator_power = 0.0
        
        self.total_generator_energy += generator_power * self.dt
        
        state = {
            'time': self.time,
            'chain_speed': chain_speed,
            'clutch_engaged': clutch_engaged,
            'generator_power': generator_power,
            'total_generator_energy': self.total_generator_energy,
            'total_compressor_energy': self.total_compressor_energy,
            'net_energy': self.total_generator_energy - self.total_compressor_energy,
            'system_state': self.controller.system_state,
            'cycle_count': self.controller.cycle_count
        }
        
        self.log_data.append(state)
    
    def step(self, dt: float) -> None:
        """
        Advance simulation by one time step.
        
        Args:
            dt: Time step size (seconds)
        """
        self.dt = dt  # Store for logging
        
        # 1. Get control actions
        control = self.controller.update(self.time, self.drivetrain.get_chain_speed())
        
        if control['system_state'] == SystemState.EMERGENCY_STOP:
            return
        
        # 2. Update drivetrain control
        if control['clutch_engaged'] != self.drivetrain.clutch_engaged:
            if control['clutch_engaged']:
                total_mass = sum(fl.mass for fl in self.floaters)
                self.drivetrain.engage_clutch(
                    chain_inertia=total_mass * (self.drivetrain.radius**2)
                )
            else:
                self.drivetrain.disengage_clutch()
        
        self.drivetrain.generator_torque = control['generator_torque']
        
        # 3. Compute net force
        net_force = self._compute_forces()
        
        # 4. Update drivetrain dynamics
        total_mass = sum(fl.mass for fl in self.floaters)
        self.drivetrain.update_dynamics(net_force, total_mass, dt)
        
        # 5. Update floater positions
        self._update_positions(dt)
        
        # 6. Handle transitions (injection/venting)
        if control['can_inject'] and control['can_vent']:
            self._handle_transitions(dt)
        
        # 7. Log state
        self._log_state()
        
        # 8. Advance time
        self.time += dt
    
    def run(self, duration: float, dt: float = 0.1) -> pd.DataFrame:
        """
        Run simulation for specified duration.
        
        Args:
            duration: Total simulation time (seconds)
            dt: Time step size (seconds)
        
        Returns:
            DataFrame containing simulation log
        """
        num_steps = int(duration / dt)
        
        for _ in range(num_steps):
            self.step(dt)
            
            if self.controller.system_state == SystemState.EMERGENCY_STOP:
                break
        
        return pd.DataFrame(self.log_data)
    
    def get_metrics(self) -> Dict:
        """Get summary metrics from simulation"""
        return {
            'total_time': self.time,
            'total_generator_energy': self.total_generator_energy,
            'total_compressor_energy': self.total_compressor_energy,
            'net_energy': self.total_generator_energy - self.total_compressor_energy,
            'average_power': (self.total_generator_energy - self.total_compressor_energy) / self.time if self.time > 0 else 0,
            'cycle_count': self.controller.cycle_count,
            'emergency_count': self.controller.emergency_count
        } 