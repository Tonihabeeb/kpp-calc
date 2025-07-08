import math
import logging
import time
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
from ..schemas import PhysicsResults, FloaterPhysicsData, EnhancedPhysicsData, FloaterState
from ..managers.physics_manager import PhysicsManager
"""
Physics Engine for the KPP Simulation.
Handles core physics calculations
     and provides a unified interface for all physics operations.
"""

@dataclass
class PhysicsState:
    """Physics state data structure"""
    time: float = 0.0
    dt: float = 0.01
    total_energy: float = 0.0
    total_power: float = 0.0
    efficiency: float = 0.0
    floater_count: int = 0
    active_floaters: int = 0

@dataclass
class ForceResult:
    """Force calculation result"""
    buoyant_force: float = 0.0
    gravitational_force: float = 0.0
    drag_force: float = 0.0
    net_force: float = 0.0
    torque: float = 0.0
    power: float = 0.0

class PhysicsEngine:
    """
    Core physics calculation engine for the KPP simulator.
    Handles force calculations, time integration, and energy tracking.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the physics engine.
        
        Args:
            config: Configuration dictionary for physics parameters
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # Physics constants
        self.gravity = 9.81  # m/s²
        self.water_density = 1000.0  # kg/m³
        self.air_density = 1.225  # kg/m³
        
        # Simulation parameters
        self.time = 0.0
        self.dt = self.config.get('time_step', 0.01)
        self.max_velocity = self.config.get('max_velocity', 10.0)  # m/s
        self.max_acceleration = self.config.get('max_acceleration', 50.0)  # m/s²
        
        # State tracking
        self.state = PhysicsState()
        self.energy_history = []
        self.performance_metrics = {
            'total_energy': 0.0,
            'total_power': 0.0,
            'efficiency': 0.0,
            'step_count': 0,
            'error_count': 0
        }
        
        # Component references (to be set by simulation engine)
        self.floaters: List[Any] = []
        self.chain_radius = self.config.get('chain_radius', 1.0)  # m
        
        self.logger.info("Physics engine initialized with dt=%.3f s", self.dt)
    
    def set_floaters(self, floaters: List[Any]) -> None:
        """
        Set the floater list for physics calculations.
        
        Args:
            floaters: List of floater objects
        """
        self.floaters = floaters
        self.state.floater_count = len(floaters)
        self.logger.info("Set %d floaters for physics calculations", len(floaters))
    
    def calculate_buoyant_force(self, volume: float, depth: float, air_fill_level: float = 0.0) -> float:
        """
        Calculate buoyant force using Archimedes' principle.
        
        Args:
            volume: Volume of the floater (m³)
            depth: Depth below water surface (m)
            air_fill_level: Fraction of volume filled with air (0.0 to 1.0)
            
        Returns:
            Buoyant force in Newtons
        """
        # Pressure increases with depth
        pressure = 101325 + self.water_density * self.gravity * depth
        
        # Effective density depends on air fill level
        effective_density = self.water_density * (1.0 - air_fill_level) + self.air_density * air_fill_level
        
        # Buoyant force: F_b = ρ_water × V × g
        buoyant_force = effective_density * volume * self.gravity
        
        return buoyant_force
    
    def calculate_gravitational_force(self, mass: float) -> float:
        """
        Calculate gravitational force.
        
        Args:
            mass: Mass of the object (kg)
            
        Returns:
            Gravitational force in Newtons
        """
        return mass * self.gravity
    
    def calculate_drag_force(self, velocity: float, area: float, drag_coefficient: float, 
                           fluid_density: Optional[float] = None) -> float:
        """
        Calculate drag force using the drag equation.
        
        Args:
            velocity: Velocity of the object (m/s)
            area: Cross-sectional area (m²)
            drag_coefficient: Drag coefficient (dimensionless)
            fluid_density: Fluid density (kg/m³), defaults to water density
            
        Returns:
            Drag force in Newtons
        """
        if fluid_density is None:
            fluid_density = self.water_density
        
        # Drag force: F_d = 0.5 × ρ × C_d × A × v²
        drag_force = 0.5 * fluid_density * drag_coefficient * area * velocity * abs(velocity)
        
        return drag_force
    
    def calculate_net_force(self, floater: Any) -> ForceResult:
        """
        Calculate net force on a floater.
        
        Args:
            floater: Floater object with position, velocity, mass, volume, etc.
            
        Returns:
            ForceResult containing all force components
        """
        try:
            # Extract floater properties
            position = getattr(floater, 'position', 0.0)
            velocity = getattr(floater, 'velocity', 0.0)
            mass = getattr(floater, 'mass', 16.0)  # Default mass
            volume = getattr(floater, 'volume', 0.4)  # Default volume
            area = getattr(floater, 'area', 0.1)  # Default area
            drag_coefficient = getattr(floater, 'drag_coefficient', 0.6)  # Default Cd
            air_fill_level = getattr(floater, 'air_fill_level', 0.0)  # Default air fill
            
            # Calculate depth (assuming tank height of 10m)
            tank_height = self.config.get('tank_height', 10.0)
            depth = max(0.0, tank_height - position)
            
            # Calculate individual forces
            buoyant_force = self.calculate_buoyant_force(volume, depth, air_fill_level)
            gravitational_force = self.calculate_gravitational_force(mass)
            drag_force = self.calculate_drag_force(velocity, area, drag_coefficient)
            
            # Net force (positive upward)
            net_force = buoyant_force - gravitational_force - drag_force
            
            # Calculate torque and power (simplified)
            torque = net_force * self.chain_radius
            power = torque * velocity / self.chain_radius  # P = τ × ω
            
            return ForceResult(
                buoyant_force=buoyant_force,
                gravitational_force=gravitational_force,
                drag_force=drag_force,
                net_force=net_force,
                torque=torque,
                power=power
            )
            
        except Exception as e:
            self.logger.error("Error calculating net force: %s", e)
            self.performance_metrics['error_count'] += 1
            return ForceResult()
    
    def integrate_motion(self, floater: Any, force_result: ForceResult) -> None:
        """
        Integrate motion using Euler method.
        
        Args:
            floater: Floater object to update
            force_result: Calculated forces
        """
        try:
            # Current state
            current_position = getattr(floater, 'position', 0.0)
            current_velocity = getattr(floater, 'velocity', 0.0)
            mass = getattr(floater, 'mass', 16.0)
            
            # Calculate acceleration: F = ma → a = F/m
            acceleration = force_result.net_force / mass
            
            # Apply acceleration limits
            acceleration = max(-self.max_acceleration, min(self.max_acceleration, acceleration))
            
            # Euler integration
            new_velocity = current_velocity + acceleration * self.dt
            new_position = current_position + new_velocity * self.dt
            
            # Apply velocity limits
            new_velocity = max(-self.max_velocity, min(self.max_velocity, new_velocity))
            
            # Apply position constraints (tank boundaries)
            tank_height = self.config.get('tank_height', 10.0)
            new_position = max(0.0, min(tank_height, new_position))
            
            # Update floater state
            floater.position = new_position
            floater.velocity = new_velocity
            floater.acceleration = acceleration
            
            # Update energy tracking
            self._update_energy_tracking(force_result, new_velocity)
            
        except Exception as e:
            self.logger.error("Error integrating motion: %s", e)
            self.performance_metrics['error_count'] += 1
    
    def _update_energy_tracking(self, force_result: ForceResult, velocity: float) -> None:
        """
        Update energy tracking metrics.
        
        Args:
            force_result: Force calculation result
            velocity: Current velocity
        """
        # Update total energy (kinetic + potential)
        kinetic_energy = 0.5 * 16.0 * velocity * velocity  # Simplified mass
        self.state.total_energy += kinetic_energy * self.dt
        
        # Update total power
        self.state.total_power += force_result.power * self.dt
        
        # Calculate efficiency (simplified)
        if self.state.total_energy > 0:
            self.state.efficiency = self.state.total_power / self.state.total_energy
        else:
            self.state.efficiency = 0.0
        
        # Update performance metrics
        self.performance_metrics['total_energy'] = self.state.total_energy
        self.performance_metrics['total_power'] = self.state.total_power
        self.performance_metrics['efficiency'] = self.state.efficiency
        self.performance_metrics['step_count'] += 1
    
    def step(self) -> PhysicsResults:
        """
        Perform one physics simulation step.
        
        Returns:
            PhysicsResults containing simulation state
        """
        start_time = time.time()
        
        try:
            # Update simulation time
            self.time += self.dt
            self.state.time = self.time
            
            # Track active floaters
            active_count = 0
            total_torque = 0.0
            total_power = 0.0
            
            # Process each floater
            for floater in self.floaters:
                # Calculate forces
                force_result = self.calculate_net_force(floater)
                
                # Integrate motion
                self.integrate_motion(floater, force_result)
                
                # Update totals
                total_torque += force_result.torque
                total_power += force_result.power
                
                # Check if floater is active (has significant velocity or force)
                if abs(floater.velocity) > 0.1 or abs(force_result.net_force) > 1.0:
                    active_count += 1
            
            # Update state
            self.state.active_floaters = active_count
            
            # Create results
            results = PhysicsResults(
                time=self.time,
                total_torque=total_torque,
                total_power=total_power,
                efficiency=self.state.efficiency,
                active_floaters=active_count,
                total_floaters=len(self.floaters),
                step_time=time.time() - start_time
            )
            
            # Log performance periodically
            if self.performance_metrics['step_count'] % 1000 == 0:
                self.logger.info("Physics step %d: torque=%.2f Nm, power=%.2f W, efficiency=%.3f", 
                               self.performance_metrics['step_count'], total_torque, total_power, self.state.efficiency)
            
            return results
            
        except Exception as e:
            self.logger.error("Error in physics step: %s", e)
            self.performance_metrics['error_count'] += 1
            return PhysicsResults(time=self.time, error=str(e))
    
    def get_state(self) -> PhysicsState:
        """
        Get current physics state.
        
        Returns:
            Current physics state
        """
        return self.state
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Get performance metrics.
        
        Returns:
            Performance metrics dictionary
        """
        return self.performance_metrics.copy()
    
    def reset(self) -> None:
        """Reset physics engine state."""
        self.time = 0.0
        self.state = PhysicsState()
        self.performance_metrics = {
            'total_energy': 0.0,
            'total_power': 0.0,
            'efficiency': 0.0,
            'step_count': 0,
            'error_count': 0
        }
        self.logger.info("Physics engine reset")
    
    def validate_physics(self) -> bool:
        """
        Validate physics calculations.
        
        Returns:
            True if physics are valid, False otherwise
        """
        try:
            # Test buoyancy calculation
            test_buoyancy = self.calculate_buoyant_force(1.0, 5.0, 0.0)
            expected_buoyancy = self.water_density * 1.0 * self.gravity
            if abs(test_buoyancy - expected_buoyancy) > 1e-6:
                self.logger.error("Buoyancy calculation validation failed")
                return False
            
            # Test gravitational force
            test_gravity = self.calculate_gravitational_force(10.0)
            expected_gravity = 10.0 * self.gravity
            if abs(test_gravity - expected_gravity) > 1e-6:
                self.logger.error("Gravitational force calculation validation failed")
                return False
            
            # Test drag force
            test_drag = self.calculate_drag_force(5.0, 0.1, 0.6)
            expected_drag = 0.5 * self.water_density * 0.6 * 0.1 * 25.0
            if abs(test_drag - expected_drag) > 1e-6:
                self.logger.error("Drag force calculation validation failed")
                return False
            
            self.logger.info("Physics validation passed")
            return True
            
        except Exception as e:
            self.logger.error("Physics validation error: %s", e)
            return False

