"""
Physics Manager for the KPP Simulation Engine.
Handles all physics calculations including floater forces, enhanced H1/H2/H3 physics,
and chain dynamics.
"""

import logging
import math
from typing import Dict, List, Any, Tuple

from simulation.managers.base_manager import BaseManager, ManagerType
from simulation.schemas import (
    PhysicsResults, 
    FloaterPhysicsData, 
    EnhancedPhysicsData,
    FloaterState
)

logger = logging.getLogger(__name__)


class PhysicsManager(BaseManager):
    """
    Manages all physics calculations for the KPP simulation including:
    - Floater force calculations (buoyancy, drag, weight)
    - Enhanced H1 nanobubble physics
    - Enhanced H2 thermal physics  
    - Enhanced H3 pulse control physics
    - Chain dynamics and kinematics
    """

    def __init__(self, engine):
        """
        Initialize the PhysicsManager with reference to the main engine.
        
        Args:
            engine: Reference to the main SimulationEngine instance
        """
        super().__init__(engine, ManagerType.PHYSICS)
        
        # Physics state tracking
        self.h1_nanobubble_force = 0.0
        self.h2_thermal_force = 0.0
        self.h3_pulse_force = 0.0

    def update(self, dt: float) -> PhysicsResults:
        """
        Update physics calculations for one time step.
        
        Args:
            dt: Time step in seconds
            
        Returns:
            PhysicsResults object with all physics data
        """
        return self.calculate_all_physics(dt)

    def calculate_floater_forces(self, dt: float) -> Dict[str, float]:
        """
        Calculate all forces acting on floaters including enhanced physics.
        
        Args:
            dt: Time step in seconds
            
        Returns:
            Dictionary containing force summary and enhanced physics data
        """
        total_vertical_force = 0.0
        base_buoy_force = 0.0
        pulse_force = 0.0
        enhanced_buoy_force = 0.0
        thermal_enhanced_force = 0.0
        h1_nanobubble_force = 0.0
        h2_thermal_force = 0.0
        h3_pulse_force = 0.0

        # Get pulse controller state
        pulse_system_state = {
            "power_output": getattr(self.engine, 'generator', getattr(self.engine, 'integrated_electrical_system', None)),
            "rpm": (
                getattr(self.engine, 'drivetrain', getattr(self.engine, 'integrated_drivetrain', None)).omega_flywheel * 60 / (2 * math.pi)
                if hasattr(getattr(self.engine, 'drivetrain', getattr(self.engine, 'integrated_drivetrain', None)), "omega_flywheel")
                else 0.0
            ),
            "efficiency": getattr(self.engine, 'generator', getattr(self.engine, 'integrated_electrical_system', None)),
            "clutch_engaged": getattr(self.engine, 'clutch', getattr(self.engine, 'integrated_drivetrain', None)),
        }
        
        # Handle pulse controller with backward compatibility
        if hasattr(self.engine, 'pulse_controller'):
            pulse_state = self.engine.pulse_controller.update(self.engine.time, dt, pulse_system_state)
        else:
            # Legacy compatibility - create basic pulse state
            pulse_state = {
                "active": False,
                "power": 0.0,
                "efficiency": 0.92
            }

        for i, floater in enumerate(self.engine.floaters):
            # Get floater position and state with backward compatibility
            if hasattr(floater, 'get_cartesian_position'):
                x, y = floater.get_cartesian_position()
            else:
                # Legacy floater compatibility - use position attribute
                y = getattr(floater, 'position', 0.0)
                x = 0.0  # Legacy floaters don't have x position
            
            is_ascending = y > 0  # Above mid-point
            
            # Get current chain speed for physics calculations
            current_chain_speed = (
                self.engine.chain_system.get_chain_speed()
                if hasattr(self.engine, "chain_system")
                else 2.0
            )
            
            # Calculate forces for this floater
            forces = self._calculate_single_floater_forces(
                floater, x, y, is_ascending, current_chain_speed, dt, pulse_state
            )
            
            # Accumulate forces
            total_vertical_force += forces["net_force"]
            base_buoy_force += forces["base_buoyancy"]
            enhanced_buoy_force += forces["fluid_buoyancy"]
            thermal_enhanced_force += forces["thermal_buoyancy"]
            
            if abs(forces["pulse_force"]) > 1e-3:
                pulse_force += forces["pulse_force"]
                
            h1_nanobubble_force += forces["h1_enhancement"]
            h2_thermal_force += forces["h2_enhancement"]
            h3_pulse_force += forces["h3_enhancement"]
            
            # Enhanced physics logging for first floater
            if i == 0 and self.engine.time % 1.0 < dt:
                self._log_floater_physics(i, x, y, is_ascending, forces, pulse_state)

        # Store enhanced physics forces
        self.h1_nanobubble_force = h1_nanobubble_force
        self.h2_thermal_force = h2_thermal_force
        self.h3_pulse_force = h3_pulse_force

        return {
            "total_vertical_force": total_vertical_force,
            "base_buoy_force": base_buoy_force,
            "pulse_force": pulse_force,
            "enhanced_buoy_force": enhanced_buoy_force,
            "thermal_enhanced_force": thermal_enhanced_force,
            "h1_nanobubble_force": h1_nanobubble_force,
            "h2_thermal_force": h2_thermal_force,
            "h3_pulse_force": h3_pulse_force,
        }

    def _calculate_single_floater_forces(
        self, floater, x: float, y: float, is_ascending: bool, 
        chain_speed: float, dt: float, pulse_state: Dict[str, Any]
    ) -> Dict[str, float]:
        """
        Calculate forces for a single floater including enhanced physics.
        
        Args:
            floater: The floater object
            x, y: Floater position coordinates
            is_ascending: Whether floater is on ascending side
            chain_speed: Current chain speed
            dt: Time step
            pulse_state: Current pulse controller state
            
        Returns:
            Dictionary of force components for this floater
        """
        # Base buoyant force calculation
        base_buoyancy = floater.compute_buoyant_force()
        
        # === H1 NANOBUBBLE PHYSICS ===
        h1_enhanced_buoyancy, nanobubble_state = self._apply_h1_nanobubble_physics(
            base_buoyancy, floater
        )
        h1_enhancement = h1_enhanced_buoyancy - base_buoyancy
        
        # === H2 THERMAL PHYSICS ===
        h2_enhanced_buoyancy = self._apply_h2_thermal_physics(
            base_buoyancy, is_ascending, y, dt
        )
        h2_enhancement = h2_enhanced_buoyancy - base_buoyancy
        
        # === H3 PULSE CONTROL ===
        h3_pulse_force = self._apply_h3_pulse_physics(
            floater, pulse_state
        )
        
        # Combined enhanced physics forces
        combined_buoyancy = max(h1_enhanced_buoyancy, h2_enhanced_buoyancy)
        
        # Legacy enhanced buoyancy calculation (for backward compatibility)
        fluid_buoyancy = self.engine.fluid_system.calculate_buoyant_force(
            floater.volume, 1.0 if getattr(floater, "is_filled", False) else 0.0
        )
        
        # Thermal enhancement using legacy Thermal model
        ascent_height = max(0, y)
        thermal_buoyancy = (
            self.engine.thermal_model.calculate_thermal_buoyancy_enhancement(
                fluid_buoyancy, ascent_height
            )
        )
        
        # Enhanced drag calculation
        drag_force = self._calculate_drag_force(
            nanobubble_state, chain_speed, floater, y
        )
        
        # Calculate net vertical force for this floater
        net_force = self._calculate_net_force(
            floater, combined_buoyancy, drag_force, h3_pulse_force
        )
        
        return {
            "net_force": net_force,
            "base_buoyancy": base_buoyancy,
            "fluid_buoyancy": fluid_buoyancy,
            "thermal_buoyancy": thermal_buoyancy,
            "pulse_force": h3_pulse_force,
            "h1_enhancement": h1_enhancement,
            "h2_enhancement": h2_enhancement,
            "h3_enhancement": h3_pulse_force,
            "drag_force": drag_force,
        }

    def _apply_h1_nanobubble_physics(self, base_buoyancy: float, floater) -> Tuple[float, Any]:
        """
        Apply H1 nanobubble physics enhancement.
        
        Args:
            base_buoyancy: Base buoyant force
            floater: Floater object
            
        Returns:
            Tuple of (enhanced_buoyancy, nanobubble_state)
        """
        # Get H1 configuration parameters
        h1_active = self.get_config_param("h1_nanobubbles_active", False)
        h1_enhancement_factor = self.get_config_param("h1_enhancement_factor", 1.2)
        h1_drag_reduction = self.get_config_param("h1_drag_reduction", 0.3)
        
        if not h1_active:
            # Return base buoyancy with no enhancement
            class NanobubbleState:
                def __init__(self, active, drag_reduction):
                    self.active = active
                    self.drag_reduction = drag_reduction
            
            return base_buoyancy, NanobubbleState(active=False, drag_reduction=0.0)
        
        # Apply nanobubble enhancement
        enhanced_buoyancy = base_buoyancy * h1_enhancement_factor
        
        # Create nanobubble state for drag calculations
        class NanobubbleState:
            def __init__(self, active, drag_reduction):
                self.active = active
                self.drag_reduction = drag_reduction
        
        return enhanced_buoyancy, NanobubbleState(active=True, drag_reduction=h1_drag_reduction)

    def _apply_h2_thermal_physics(self, base_buoyancy: float, is_ascending: bool, 
                                  y: float, dt: float) -> float:
        """
        Apply H2 thermal physics enhancement.
        
        Args:
            base_buoyancy: Base buoyant force
            is_ascending: Whether floater is ascending
            y: Vertical position
            dt: Time step
            
        Returns:
            Enhanced buoyant force
        """
        # Get H2 configuration parameters
        h2_active = self.get_config_param("h2_thermal_active", False)
        h2_enhancement_factor = self.get_config_param("h2_enhancement_factor", 1.15)
        h2_thermal_gradient = self.get_config_param("h2_thermal_gradient", 0.1)
        
        if not h2_active or not is_ascending:
            return base_buoyancy
        
        # Apply thermal enhancement based on height
        height_factor = min(1.0, y * h2_thermal_gradient)
        enhanced_buoyancy = base_buoyancy * (1.0 + (h2_enhancement_factor - 1.0) * height_factor)
        
        return enhanced_buoyancy

    def _apply_h3_pulse_physics(self, floater, pulse_state: Dict[str, Any]) -> float:
        """
        Apply H3 pulse control physics.
        
        Args:
            floater: Floater object
            pulse_state: Current pulse controller state
            
        Returns:
            Pulse force magnitude
        """
        # Get H3 configuration parameters
        h3_active = self.get_config_param("h3_pulse_active", False)
        
        if not h3_active or not pulse_state.get("clutch_engaged", False):
            return 0.0
        
        # Apply pulse force
        pulse_force = self.get_config_param("h3_pulse_force", 100.0)
        return pulse_force

    def _calculate_drag_force(self, nanobubble_state, chain_speed: float, 
                             floater, y: float) -> float:
        """Calculate drag force with nanobubble effects."""
        if nanobubble_state and nanobubble_state.active:
            # H1: Reduced drag
            base_drag = self.engine.fluid_system.calculate_drag_force(
                chain_speed, floater.area
            )
            drag_force = base_drag * (1 - nanobubble_state.drag_reduction)
        else:
            drag_force = self.engine.fluid_system.calculate_drag_force(
                chain_speed, floater.area
            )
            
        # Apply drag force direction based on motion
        if y > 0:  # Ascending side
            drag_force = -drag_force  # Opposes upward motion
        else:  # Descending side
            drag_force = drag_force  # Opposes downward motion
            
        return drag_force

    def _calculate_net_force(self, floater, combined_buoyancy: float, 
                            drag_force: float, pulse_force: float) -> float:
        """Calculate net vertical force for a floater."""
        floater_weight = floater.mass * self.engine.fluid_system.gravity
        
        if getattr(floater, "is_filled", False):
            # Air-filled floater: enhanced buoyancy up, weight down, drag opposing motion
            net_force = combined_buoyancy - floater_weight + drag_force + pulse_force
        else:
            # Water-filled floater: weight + water weight down, drag opposing motion
            water_weight = (
                floater.volume
                * self.engine.fluid_system.state.effective_density
                * self.engine.fluid_system.gravity
            )
            net_force = -(floater_weight + water_weight) + drag_force + pulse_force
            
        return net_force

    def _log_floater_physics(self, floater_idx: int, x: float, y: float, 
                            is_ascending: bool, forces: Dict[str, float], 
                            pulse_state: Dict[str, Any]) -> None:
        """Log detailed physics information for debugging."""
        logger.debug(f"Floater {floater_idx}: x={x:.2f}, y={y:.2f}, is_asc={is_ascending}")
        logger.debug(
            f"  Forces: base_buoy={forces['base_buoyancy']:.1f}, "
            f"drag={forces['drag_force']:.1f}, pulse={forces['pulse_force']:.1f}, "
            f"net={forces['net_force']:.1f}"
        )
        
        if forces['h1_enhancement'] > 0:
            logger.debug(f"  H1: enhancement={forces['h1_enhancement']:.1f}N")
            
        if forces['h2_enhancement'] > 0:
            logger.debug(f"  H2: enhancement={forces['h2_enhancement']:.1f}N")
            
        logger.debug(
            f"  H3: clutch_engaged={pulse_state.get('clutch_engaged', False)}, "
            f"phase={pulse_state.get('current_phase', 'unknown')}"
        )

    def update_chain_dynamics(self, total_vertical_force: float, dt: float) -> Dict[str, Any]:
        """
        Update chain kinematics and floater positions.
        
        Args:
            total_vertical_force: Total vertical force from all floaters
            dt: Time step in seconds
            
        Returns:
            Chain dynamics results
        """
        # Update chain kinematics using the Chain system with calculated force
        chain_results = self.engine.chain_system.advance(dt, total_vertical_force)
        
        # Update floater positions based on chain motion
        for i, floater in enumerate(self.engine.floaters):
            self._update_floater_position(floater, dt)
            
        return chain_results

    def _update_floater_position(self, floater, dt: float) -> None:
        """Update a single floater's position and handle sprocket crossings."""
        prev_theta = getattr(floater, "theta", 0.0)
        
        # Use chain motion to advance floater position
        chain_angular_velocity = self.engine.chain_system.get_angular_speed()
        new_theta = prev_theta + chain_angular_velocity * dt
        floater.set_theta(new_theta)
        
        # Detect top sprocket crossing (180° pivot)
        if (prev_theta % (2 * math.pi) < math.pi 
            and new_theta % (2 * math.pi) >= math.pi):
            floater.pivot()
            
        # Detect bottom sprocket crossing (360° pivot + water drainage)
        if prev_theta < 2 * math.pi and new_theta >= 2 * math.pi:
            floater.pivot()
            floater.drain_water()
            floater.is_filled = False
            floater.fill_progress = 0.0
            # Trigger air injection after drainage
            self.engine.pneumatics.trigger_injection(floater)
            
        floater.update(dt)

    def get_enhanced_physics_state(self) -> Dict[str, Any]:
        """Get enhanced physics state information"""
        return {
            "h1_active": self.get_config_param("h1_nanobubbles_active", False),
            "h1_enhancement_factor": self.get_config_param("h1_enhancement_factor", 1.2),
            "h1_drag_reduction": self.get_config_param("h1_drag_reduction", 0.3),
            "h2_active": self.get_config_param("h2_thermal_active", False),
            "h2_enhancement_factor": self.get_config_param("h2_enhancement_factor", 1.15),
            "h2_thermal_gradient": self.get_config_param("h2_thermal_gradient", 0.1),
            "h3_active": self.get_config_param("h3_pulse_active", False),
            "h3_pulse_force": self.get_config_param("h3_pulse_force", 100.0),
            "h1_nanobubble_force": getattr(self, 'h1_nanobubble_force', 0.0),
            "h2_thermal_force": getattr(self, 'h2_thermal_force', 0.0),
            "h3_pulse_force": getattr(self, 'h3_pulse_force', 0.0),
        }

    def calculate_all_physics(self, dt: float) -> PhysicsResults:
        """
        Calculate all physics for the current time step including floater forces, 
        enhanced physics (H1/H2/H3), and chain dynamics.
        
        Args:
            dt: Time step in seconds
            
        Returns:
            PhysicsResults object containing all physics calculation results
        """
        # 1. Calculate floater forces with enhanced physics
        floater_results = self.calculate_floater_forces(dt)
        
        # 2. Update chain dynamics based on total vertical force
        total_vertical_force = floater_results.get("total_vertical_force", 0.0)
        chain_results = self.update_chain_dynamics(total_vertical_force, dt)
        
        # 3. Get enhanced physics state
        enhanced_state = self.get_enhanced_physics_state()
        
        # 4. Build floater data list
        floater_data = []
        for i, floater in enumerate(self.engine.floaters):
            x, y = floater.get_cartesian_position()
            
            # Determine floater state
            if getattr(floater, 'is_filled', False):
                if getattr(floater, 'fill_progress', 0.0) < 1.0:
                    state = FloaterState.FILLING
                else:
                    state = FloaterState.FILLED
            else:
                state = FloaterState.EMPTY
            
            floater_data.append(FloaterPhysicsData(
                id=i,
                position=getattr(floater, 'theta', 0.0),
                velocity=getattr(floater, 'velocity', 0.0),
                buoyancy_force=floater.compute_buoyant_force(),
                drag_force=abs(floater.compute_drag_force()),
                pulse_force=floater.compute_pulse_jet_force() if hasattr(floater, 'compute_pulse_jet_force') else 0.0,
                net_force=getattr(floater, 'force', 0.0),
                state=state,
                fill_progress=getattr(floater, 'fill_progress', 0.0),
                is_filled=getattr(floater, 'is_filled', False)
            ))
        
        # 5. Build enhanced physics data
        enhanced_physics = EnhancedPhysicsData(
            h1_nanobubbles=enhanced_state.get("h1_nanobubbles", {}),
            h2_thermal=enhanced_state.get("h2_thermal", {}),
            h3_pulse=enhanced_state.get("h3_pulse", {}),
            drag_reduction_factor=enhanced_state.get("drag_reduction_factor", 1.0),
            thermal_enhancement=enhanced_state.get("thermal_enhancement", 1.0)
        )
        
        # 6. Create PhysicsResults object
        return PhysicsResults(
            total_vertical_force=total_vertical_force,
            base_buoy_force=floater_results.get("base_buoy_force", 0.0),
            enhanced_buoy_force=floater_results.get("enhanced_buoy_force", 0.0),
            thermal_enhanced_force=floater_results.get("thermal_enhanced_force", 0.0),
            pulse_force=floater_results.get("pulse_force", 0.0),
            drag_force=floater_results.get("drag_force", 0.0),
            net_force=total_vertical_force,
            floater_data=floater_data,
            enhanced_physics=enhanced_physics,
            chain_dynamics=chain_results
        )
