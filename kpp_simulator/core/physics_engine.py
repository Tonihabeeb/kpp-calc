"""
Enhanced Physics Engine for KPP Simulator
Integrates advanced buoyancy and drag calculations with validation
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
import logging
import time

from simulation.physics.buoyancy import EnhancedBuoyancyCalculator, BuoyancyResult
from simulation.physics.drag import EnhancedDragCalculator, DragResult
from simulation.components.floater.thermal import ThermalModel, ThermalState
from simulation.physics.validation import PhysicsValidator, ValidationResult

@dataclass
class PhysicsConfig:
    """Physics engine configuration"""
    gravity: float = 9.81  # m/s^2
    water_density: float = 1000.0  # kg/m^3
    air_density: float = 1.225  # kg/m^3
    temperature: float = 293.15  # K
    time_step: float = 0.01  # seconds
    max_iterations: int = 50
    convergence_tolerance: float = 1e-6
    
    # Enhanced parameters
    characteristic_length: float = 0.2  # m (for Reynolds calculations)
    fluid_viscosity: float = 1.0e-3  # Pa·s
    base_drag_coefficient: float = 0.47  # dimensionless
    thermal_conductivity: float = 50.0  # W/m·K
    specific_heat: float = 900.0  # J/kg·K

@dataclass
class PhysicsState:
    """Physics engine state"""
    time: float = 0.0
    position: np.ndarray = field(default_factory=lambda: np.zeros(3))
    velocity: np.ndarray = field(default_factory=lambda: np.zeros(3))
    acceleration: np.ndarray = field(default_factory=lambda: np.zeros(3))
    forces: Dict[str, np.ndarray] = field(default_factory=dict)
    energy: Dict[str, float] = field(default_factory=dict)
    
    # Enhanced state tracking
    buoyancy_results: Optional[BuoyancyResult] = None
    drag_results: Optional[DragResult] = None
    thermal_state: Optional[ThermalState] = None

class PhysicsEngine:
    """
    Enhanced Physics Engine for KPP Simulator
    
    Features:
    - Real-time physics calculations
    - Force and energy tracking
    - Multi-body dynamics
    - Environmental effects
    - Performance optimization
    - Enhanced buoyancy with depth effects
    - Enhanced drag with Reynolds number effects
    - Thermal integration
    """
    
    def __init__(self, config: Optional[PhysicsConfig] = None):
        """Initialize physics engine"""
        self.config = config or PhysicsConfig()
        self.state = PhysicsState()
        self.logger = logging.getLogger(__name__)
        
        # Initialize enhanced calculators
        self.buoyancy_calculator = EnhancedBuoyancyCalculator(
            water_density=self.config.water_density,
            gravity=self.config.gravity
        )
        
        self.drag_calculator = EnhancedDragCalculator(
            base_drag_coefficient=self.config.base_drag_coefficient,
            fluid_viscosity=self.config.fluid_viscosity
        )
        
        # Add validator
        self.validator = PhysicsValidator(tolerance=1e-3)
        self.validation_results = {}
        
        # Performance tracking
        self.performance_metrics = {
            'total_iterations': 0,
            'average_convergence_steps': 0.0,
            'total_calculations': 0,
            'calculation_time': 0.0,
            'last_update_time': 0.0
        }
        
        self.logger.info("Enhanced Physics Engine initialized")
    
    def update(self, time_step: Optional[float] = None) -> bool:
        """
        Update physics state with enhanced calculations
        
        Args:
            time_step: Time step in seconds (optional, uses config value if not provided)
            
        Returns:
            True if update successful
        """
        try:
            # Store initial state for validation
            initial_energy = self.state.energy.copy()
            
            # Perform normal update
            success = self._perform_update(time_step)
            if not success:
                return False
            
            # Run validation checks
            self.validation_results = self.validator.run_all_validations(
                self.get_state(),
                {
                    'volume': 1.0,  # TODO: Get from config
                    'water_density': self.config.water_density,
                    'gravity': self.config.gravity,
                    'cross_section': np.pi * (self.config.characteristic_length/2)**2,
                    'time_step': time_step or self.config.time_step,
                    'characteristic_length': self.config.characteristic_length
                }
            )
            
            # Log validation failures
            for name, result in self.validation_results.items():
                if not result.passed:
                    self.logger.warning(
                        f"Physics validation failed - {name}: {result.error_message}"
                    )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Physics update failed: {e}")
            return False
    
    def _perform_update(self, time_step: Optional[float] = None) -> bool:
        """Internal update method separated for validation"""
        dt = time_step or self.config.time_step
        
        # Calculate forces with enhanced physics
        self._calculate_forces()
        
        # Update kinematics with proper Euler integration
        self._update_kinematics(dt)
        
        # Update energy accounting
        self._update_energy()
        
        # Update time and performance metrics
        self.state.time += dt
        self.performance_metrics['total_iterations'] += 1
        
        return True
    
    def _calculate_forces(self):
        """Calculate all forces with enhanced physics"""
        # Reset forces
        self.state.forces = {}
        
        # Get current depth (z-coordinate, negative is deeper)
        depth = max(0.0, -self.state.position[2])
        
        # Calculate buoyancy with enhanced model
        self.state.buoyancy_results = self.buoyancy_calculator.calculate_buoyancy(
            floater_volume=1.0,  # TODO: Get from configuration
            depth=depth,
            air_fill_level=0.5,  # TODO: Get from floater state
            thermal_state=self.state.thermal_state
        )
        
        buoyancy_force = np.array([0, 0, self.state.buoyancy_results.force])
        self.state.forces['buoyancy'] = buoyancy_force
        
        # Calculate gravity
        mass = 1.0  # TODO: Get from configuration
        gravity_force = np.array([0, 0, -self.config.gravity * mass])
        self.state.forces['gravity'] = gravity_force
        
        # Calculate drag with enhanced model
        velocity_magnitude = float(np.linalg.norm(self.state.velocity))
        if velocity_magnitude > 0:
            velocity_direction = self.state.velocity / velocity_magnitude
            
            self.state.drag_results = self.drag_calculator.calculate_drag(
                velocity=velocity_magnitude,
                cross_section=float(np.pi * (self.config.characteristic_length/2)**2),
                fluid_density=float(self.config.water_density),
                characteristic_length=float(self.config.characteristic_length)
            )
            
            # Drag always opposes motion
            drag_force = -velocity_direction * self.state.drag_results.force
            self.state.forces['drag'] = drag_force
        else:
            self.state.forces['drag'] = np.zeros(3, dtype=float).copy()
        # Sum all forces
        total_force = np.zeros(3, dtype=float)
        for force in self.state.forces.values():
            total_force += force
        self.state.forces['total'] = total_force
    
    def _update_kinematics(self, dt: float):
        """Update position and velocity with proper Euler integration"""
        # Get total force
        total_force = self.state.forces['total']
        
        # Calculate acceleration (F = ma)
        mass = 1.0  # TODO: Get from configuration
        self.state.acceleration = total_force / mass
        
        # Update velocity (v = v0 + at)
        self.state.velocity += self.state.acceleration * dt
        
        # Update position (x = x0 + vt + 0.5at^2)
        self.state.position += (self.state.velocity * dt + 
                              0.5 * self.state.acceleration * dt * dt)
    
    def _update_energy(self):
        """Update energy calculations with enhanced accounting"""
        # Reset energy
        self.state.energy = {}
        
        mass = 1.0  # TODO: Get from configuration
        
        # Kinetic energy
        velocity_magnitude = float(np.linalg.norm(self.state.velocity))
        kinetic_energy = 0.5 * mass * velocity_magnitude * velocity_magnitude
        self.state.energy['kinetic'] = float(kinetic_energy)
        
        # Potential energy (relative to water surface at z=0)
        potential_energy = mass * self.config.gravity * abs(self.state.position[2])
        self.state.energy['potential'] = potential_energy
        
        # Drag power loss (if drag results available)
        if self.state.drag_results:
            self.state.energy['drag_loss'] = self.state.drag_results.power_loss
        
        # Total mechanical energy
        self.state.energy['total'] = kinetic_energy + potential_energy
    
    def get_state(self) -> Dict[str, Any]:
        """Get current physics state with enhanced data"""
        state_dict = {
            'time': self.state.time,
            'position': self.state.position.tolist(),
            'velocity': self.state.velocity.tolist(),
            'acceleration': self.state.acceleration.tolist(),
            'forces': {k: v.tolist() for k, v in self.state.forces.items()},
            'energy': self.state.energy
        }
        
        # Add enhanced physics results if available
        if self.state.buoyancy_results:
            state_dict['buoyancy_results'] = {
                'force': self.state.buoyancy_results.force,
                'displaced_volume': self.state.buoyancy_results.displaced_volume,
                'effective_density': self.state.buoyancy_results.effective_density,
                'submersion_factor': self.state.buoyancy_results.submersion_factor,
                'depth_pressure': self.state.buoyancy_results.depth_pressure
            }
            
        if self.state.drag_results:
            state_dict['drag_results'] = {
                'force': self.state.drag_results.force,
                'coefficient': self.state.drag_results.coefficient,
                'reynolds_number': self.state.drag_results.reynolds_number,
                'power_loss': self.state.drag_results.power_loss
            }
            
        # Add validation results if available
        if self.validation_results:
            state_dict['validation'] = {
                name: {
                    'passed': result.passed,
                    'error_margin': result.error_margin,
                    'description': result.description,
                    'error_message': result.error_message
                }
                for name, result in self.validation_results.items()
            }
        
        return state_dict
    
    def reset(self):
        """Reset physics engine state"""
        self.state = PhysicsState()
        self.performance_metrics = {
            'total_iterations': 0,
            'average_convergence_steps': 0.0,
            'total_calculations': 0,
            'calculation_time': 0.0,
            'last_update_time': 0.0
        }
        self.logger.info("Physics Engine reset") 