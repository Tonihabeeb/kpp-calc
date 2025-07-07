"""
Physics Engine for the KPP Simulation.
Handles core physics calculations and provides a unified interface for all physics operations.
"""

import logging
import math
from typing import Any, Dict, List, Optional, Tuple

from ..schemas import PhysicsResults, FloaterPhysicsData, EnhancedPhysicsData, FloaterState
from ..managers.physics_manager import PhysicsManager

logger = logging.getLogger(__name__)


class PhysicsEngine:
    """
    Core physics engine that coordinates all physics calculations.
    
    This class provides a unified interface for:
    - Floater force calculations
    - Chain dynamics
    - Enhanced physics (H1/H2/H3)
    - Energy conservation
    - Physics validation
    """
    
    def __init__(self, params: Optional[Dict[str, Any]] = None):
        """
        Initialize the physics engine.
        
        Args:
            params: Physics parameters dictionary
        """
        self.params = params if params is not None else {}
        self.time_step = self.params.get('time_step', 0.01)
        self.gravity = self.params.get('gravity', 9.81)
        self.water_density = self.params.get('water_density', 1000.0)
        self.air_density = self.params.get('air_density', 1.225)
        
        # Physics managers
        self.physics_manager = None
        
        # State tracking
        self.total_energy = 0.0
        self.total_power = 0.0
        self.step_count = 0
        
        logger.info("PhysicsEngine initialized")
    
    def initialize(self, engine) -> bool:
        """
        Initialize physics engine with simulation engine reference.
        
        Args:
            engine: Reference to the main SimulationEngine
            
        Returns:
            bool: True if initialization successful
        """
        try:
            self.physics_manager = PhysicsManager(engine)
            logger.info("PhysicsEngine managers initialized")
            return True
        except Exception as e:
            logger.error(f"PhysicsEngine initialization failed: {e}")
            return False
    
    def calculate_floater_forces(self, floaters: List[Any], dt: float) -> Dict[str, float]:
        """
        Calculate forces for all floaters.
        
        Args:
            floaters: List of floater objects or single floater object
            dt: Time step in seconds
            
        Returns:
            Dictionary containing total forces
        """
        # Handle both single floater and list of floaters
        if not isinstance(floaters, list):
            floaters = [floaters]
        
        if not floaters:
            return {
                "total_vertical_force": 0.0,
                "base_buoy_force": 0.0,
                "enhanced_buoy_force": 0.0,
                "thermal_enhanced_force": 0.0,
                "pulse_force": 0.0,
                "drag_force": 0.0,
            }
        
        total_vertical_force = 0.0
        base_buoy_force = 0.0
        enhanced_buoy_force = 0.0
        thermal_enhanced_force = 0.0
        pulse_force = 0.0
        drag_force = 0.0
        
        for floater in floaters:
            try:
                # Base buoyant force
                base_buoyancy = floater.compute_buoyant_force()
                base_buoy_force += base_buoyancy
                
                # Enhanced physics (if available)
                enhanced_buoyancy = base_buoyancy
                if hasattr(floater, 'calculate_enhanced_buoyancy'):
                    enhanced_buoyancy = floater.calculate_enhanced_buoyancy()
                
                enhanced_buoy_force += enhanced_buoyancy
                
                # Thermal enhancement
                thermal_buoyancy = enhanced_buoyancy
                if hasattr(floater, 'calculate_thermal_buoyancy'):
                    thermal_buoyancy = floater.calculate_thermal_buoyancy()
                
                thermal_enhanced_force += thermal_buoyancy
                
                # Pulse force
                if hasattr(floater, 'compute_pulse_jet_force'):
                    jet_force = floater.compute_pulse_jet_force()
                    pulse_force += jet_force
                
                # Drag force
                if hasattr(floater, 'compute_drag_force'):
                    drag = floater.compute_drag_force()
                    drag_force += abs(drag)
                
                # Net force calculation
                weight = floater.config.mass * self.gravity
                net_force = thermal_buoyancy - weight
                
                # Apply drag direction based on motion
                if hasattr(floater, 'velocity'):
                    if floater.velocity > 0:  # Moving up
                        net_force -= drag_force
                    elif floater.velocity < 0:  # Moving down
                        net_force += drag_force
                
                total_vertical_force += net_force
                
            except Exception as e:
                logger.warning(f"Error calculating forces for floater: {e}")
                continue
        
        return {
            "total_vertical_force": total_vertical_force,
            "base_buoy_force": base_buoy_force,
            "enhanced_buoy_force": enhanced_buoy_force,
            "thermal_enhanced_force": thermal_enhanced_force,
            "pulse_force": pulse_force,
            "drag_force": drag_force,
        }
    
    def update_chain_dynamics(self, floaters: List[Any], total_force: float, dt: float) -> Dict[str, Any]:
        """
        Update chain dynamics based on total force.
        
        Args:
            floaters: List of floater objects
            total_force: Total vertical force from all floaters
            dt: Time step in seconds
            
        Returns:
            Dictionary containing chain dynamics results
        """
        try:
            # Calculate chain acceleration
            total_mass = sum(f.config.mass for f in floaters) if floaters else 1.0
            chain_acceleration = total_force / total_mass
            
            # Update floater positions based on chain motion
            chain_velocity = 0.0
            if hasattr(self, 'chain_velocity'):
                chain_velocity = self.chain_velocity
                self.chain_velocity += chain_acceleration * dt
            
            # Update individual floater velocities
            for floater in floaters:
                if hasattr(floater, 'velocity'):
                    floater.velocity = chain_velocity
                
                # Update position
                if hasattr(floater, 'position'):
                    floater.position += chain_velocity * dt
            
            return {
                "chain_velocity": chain_velocity,
                "chain_acceleration": chain_acceleration,
                "total_mass": total_mass,
                "chain_tension": abs(total_force),
            }
            
        except Exception as e:
            logger.error(f"Chain dynamics update failed: {e}")
            return {
                "chain_velocity": 0.0,
                "chain_acceleration": 0.0,
                "total_mass": 1.0,
                "chain_tension": 0.0,
            }
    
    def calculate_energy_balance(self, floaters: List[Any], dt: float) -> Dict[str, float]:
        """
        Calculate energy balance for the system.
        
        Args:
            floaters: List of floater objects
            dt: Time step in seconds
            
        Returns:
            Dictionary containing energy values
        """
        try:
            # Kinetic energy
            kinetic_energy = 0.0
            for floater in floaters:
                if hasattr(floater, 'velocity') and hasattr(floater, 'config'):
                    kinetic_energy += 0.5 * floater.config.mass * floater.velocity ** 2
            
            # Potential energy
            potential_energy = 0.0
            for floater in floaters:
                if hasattr(floater, 'position') and hasattr(floater, 'config'):
                    potential_energy += floater.config.mass * self.gravity * floater.position
            
            # Energy losses
            drag_loss = sum(getattr(f, 'drag_loss', 0.0) for f in floaters)
            venting_loss = sum(getattr(f, 'venting_loss', 0.0) for f in floaters)
            
            # Total energy
            total_energy = kinetic_energy + potential_energy
            
            # Update running totals
            self.total_energy += total_energy * dt
            self.total_power = total_energy / dt if dt > 0 else 0.0
            
            return {
                "kinetic_energy": kinetic_energy,
                "potential_energy": potential_energy,
                "total_energy": total_energy,
                "drag_loss": drag_loss,
                "venting_loss": venting_loss,
                "system_power": self.total_power,
            }
            
        except Exception as e:
            logger.error(f"Energy balance calculation failed: {e}")
            return {
                "kinetic_energy": 0.0,
                "potential_energy": 0.0,
                "total_energy": 0.0,
                "drag_loss": 0.0,
                "venting_loss": 0.0,
                "system_power": 0.0,
            }
    
    def validate_physics(self, floaters: List[Any]) -> Dict[str, Any]:
        """
        Validate physics calculations for consistency.
        
        Args:
            floaters: List of floater objects
            
        Returns:
            Dictionary containing validation results
        """
        try:
            validation_results = {
                "passed": True,
                "warnings": [],
                "errors": [],
            }
            
            # Check for NaN or infinite values
            for i, floater in enumerate(floaters):
                if hasattr(floater, 'velocity') and not math.isfinite(floater.velocity):
                    validation_results["errors"].append(f"Floater {i}: Invalid velocity")
                    validation_results["passed"] = False
                
                if hasattr(floater, 'position') and not math.isfinite(floater.position):
                    validation_results["errors"].append(f"Floater {i}: Invalid position")
                    validation_results["passed"] = False
            
            # Check energy conservation
            if self.total_energy < 0:
                validation_results["warnings"].append("Negative total energy detected")
            
            # Check for extreme values
            if self.total_power > 1e6:  # 1 MW
                validation_results["warnings"].append("Extremely high power detected")
            
            return validation_results
            
        except Exception as e:
            logger.error(f"Physics validation failed: {e}")
            return {
                "passed": False,
                "warnings": [],
                "errors": [f"Validation error: {str(e)}"],
            }
    
    def step(self, floaters: List[Any], dt: float) -> PhysicsResults:
        """
        Execute one physics step.
        
        Args:
            floaters: List of floater objects
            dt: Time step in seconds
            
        Returns:
            PhysicsResults object containing all physics data
        """
        try:
            self.step_count += 1
            
            # Calculate forces
            force_results = self.calculate_floater_forces(floaters, dt)
            
            # Update chain dynamics
            chain_results = self.update_chain_dynamics(
                floaters, 
                force_results["total_vertical_force"], 
                dt
            )
            
            # Calculate energy balance
            energy_results = self.calculate_energy_balance(floaters, dt)
            
            # Validate physics
            validation_results = self.validate_physics(floaters)
            
            # Build floater data
            floater_data = []
            for i, floater in enumerate(floaters):
                try:
                    floater_data.append(
                        FloaterPhysicsData(
                            id=i,
                            position=getattr(floater, 'position', 0.0),
                            velocity=getattr(floater, 'velocity', 0.0),
                            buoyancy_force=floater.compute_buoyant_force(),
                            drag_force=abs(floater.compute_drag_force()) if hasattr(floater, 'compute_drag_force') else 0.0,
                            pulse_force=floater.compute_pulse_jet_force() if hasattr(floater, 'compute_pulse_jet_force') else 0.0,
                            net_force=getattr(floater, 'force', 0.0),
                            state=FloaterState.EMPTY,
                            fill_progress=getattr(floater, 'fill_progress', 0.0),
                            is_filled=getattr(floater, 'is_filled', False),
                        )
                    )
                except Exception as e:
                    logger.warning(f"Error building floater data for floater {i}: {e}")
                    continue
            
            # Build enhanced physics data
            enhanced_physics = EnhancedPhysicsData(
                h1_nanobubbles={},
                h2_thermal={},
                h3_pulse={},
                drag_reduction_factor=1.0,
                thermal_enhancement=1.0,
            )
            
            # Create PhysicsResults
            return PhysicsResults(
                total_vertical_force=force_results["total_vertical_force"],
                base_buoy_force=force_results["base_buoy_force"],
                enhanced_buoy_force=force_results["enhanced_buoy_force"],
                thermal_enhanced_force=force_results["thermal_enhanced_force"],
                pulse_force=force_results["pulse_force"],
                drag_force=force_results["drag_force"],
                net_force=force_results["total_vertical_force"],
                floater_data=floater_data,
                enhanced_physics=enhanced_physics,
                chain_dynamics=chain_results,
            )
            
        except Exception as e:
            logger.error(f"Physics step failed: {e}")
            # Return empty results on failure
            return PhysicsResults(
                total_vertical_force=0.0,
                base_buoy_force=0.0,
                enhanced_buoy_force=0.0,
                thermal_enhanced_force=0.0,
                pulse_force=0.0,
                drag_force=0.0,
                net_force=0.0,
                floater_data=[],
                enhanced_physics=EnhancedPhysicsData(
                    h1_nanobubbles={},
                    h2_thermal={},
                    h3_pulse={},
                    drag_reduction_factor=1.0,
                    thermal_enhancement=1.0,
                ),
                chain_dynamics={},
            )
    
    def reset(self) -> None:
        """Reset physics engine state."""
        self.total_energy = 0.0
        self.total_power = 0.0
        self.step_count = 0
        logger.info("PhysicsEngine reset")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get physics engine statistics."""
        return {
            "step_count": self.step_count,
            "total_energy": self.total_energy,
            "total_power": self.total_power,
            "time_step": self.time_step,
            "gravity": self.gravity,
            "water_density": self.water_density,
            "air_density": self.air_density,
        }
