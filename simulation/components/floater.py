"""
Floater dynamics module.
Encapsulates buoyancy, drag, and motion for a single floater.

Floater physics: buoyancy, drag, and floater state management
Handles all floater-related calculations and updates
Phase 3 enhancement: Enhanced buoyancy physics with pressure expansion
"""

import logging
import math
from typing import Optional, Dict, Any
import types
from config.config import G, RHO_WATER, RHO_AIR
from utils.logging_setup import setup_logging
# Phase 3: Import pressure expansion physics
from simulation.pneumatics.pressure_expansion import PressureExpansionPhysics

setup_logging()
logger = logging.getLogger(__name__)

class Floater:
    """
    Represents a buoyant floater in the KPP system    def get_pneumatic_status(self) -> Dict[str, Any]:
    Handles buoyancy, drag, vertical motion, and pulse-jet physics.
    """

    MAX_VELOCITY = 10.0  # m/s, physically reasonable max
    MIN_POSITION = 0.0   # bottom of tank (m)
    MAX_POSITION = 10.0  # top of tank (m)

    def __init__(
        self,
        volume: float,
        mass: float,
        area: float,
        Cd: float = 0.8,
        position: float = 0.0,
        velocity: float = 0.0,
        is_filled: bool = False,
        air_fill_time: float = 0.5,
        air_pressure: float = 300000,
        air_flow_rate: float = 0.6,
        jet_efficiency: float = 0.85,
        added_mass: float = 0.0,  # New parameter for added mass
        phase_offset: float = 0.0,  # Angular phase offset around chain
        tank_height: float = 10.0,  # Phase 3: Tank height for depth calculations
        expansion_mode: str = "mixed"  # Phase 3: Air expansion mode
    ):
        """
        Initialize a Floater.

        Args:
            volume (float): Volume of the floater (m^3)
            mass (float): Mass of the floater (kg)
            area (float): Cross-sectional area for drag (m^2)
            Cd (float, optional): Drag coefficient (dimensionless). Defaults to 0.8.
            position (float, optional): Initial vertical position (m). Defaults to 0.0.
            velocity (float, optional): Initial vertical velocity (m/s). Defaults to 0.0.
            is_filled (bool, optional): Whether the floater is filled with air (buoyant). Defaults to False.
            air_fill_time (float, optional): Time to fill air volume (s). Defaults to 0.5.
            air_pressure (float, optional): Air pressure for pulse jet (Pa). Defaults to 300000.
            air_flow_rate (float, optional): Air flow rate for pulse jet (m^3/s). Defaults to 0.6.
            jet_efficiency (float, optional): Efficiency of the pulse jet. Defaults to 0.85.
        """
        self.volume = volume
        self.mass = mass
        self.area = area
        self.Cd = Cd
        self.position = position
        self.velocity = velocity
        self.is_filled = False
        self.fill_progress = 0.0  # 0.0 to 1.0

        # Pulse physics parameters
        self.air_fill_time = air_fill_time
        self.air_pressure = air_pressure
        self.air_flow_rate = air_flow_rate
        self.jet_efficiency = jet_efficiency
        # Floater FSM state and timing
        self.state = 'EMPTY' if not is_filled else 'FILLED'
        # Phase offset and initial theta for ripple smoothing
        self.phase_offset = phase_offset
        self.theta = phase_offset
        self.fill_start_time = None
        self.vent_start_time = None
        self.internal_pressure = 0.0  # Placeholder for future use
        
        # Store initial conditions for reset
        self.initial_position = position
        self.initial_velocity = velocity
        self.initial_is_filled = is_filled
        
        # Chain parameters
        self.major_axis = 1.0
        self.minor_axis = 1.0
        self.chain_radius = 1.0
        # theta already initialized above
        
        # Dissolved air fraction
        self.dissolved_air_fraction = 0.0  # Fraction of air dissolved into water
        
        # Added mass parameter
        self.added_mass: float = added_mass
        # Phase offset for ripple smoothing
        self.phase_offset: float = phase_offset

        # Water inside the floater (for drainage)
        self.water_mass = 0.0
        # Orientation state for pivoting
        self.pivoted = False

        # Initialize loss tracking attributes
        self.drag_loss: float = 0.0
        self.dissolution_loss: float = 0.0
        self.venting_loss: float = 0.0

        # Phase 3: Enhanced buoyancy and pressure expansion
        self.tank_height = tank_height
        self.expansion_mode = expansion_mode
        self.pressure_physics = PressureExpansionPhysics()
        
        # Phase 3: Enhanced air state tracking
        self.injection_depth = 0.0  # Depth where air was injected
        self.initial_air_pressure = 101325.0  # Pressure when air was injected
        self.current_air_pressure = 101325.0  # Current air pressure
        self.dissolved_air_fraction_enhanced = 0.0  # Enhanced dissolution tracking
        self.expansion_state = {}  # Store current expansion state

        # Pneumatic state management (Phase 2.2 enhancement)
        self.pneumatic_fill_state = 'empty'  # 'empty', 'filling', 'full', 'venting'
        self.air_fill_level = 0.0  # 0.0 to 1.0 (fraction of total volume filled with air)
        self.pneumatic_pressure = 101325.0  # Pa (current air pressure inside floater)
        self.target_air_volume = 0.0  # m³ (target air volume for current injection)
        self.injection_start_time = 0.0  # Time when current injection started
        self.total_air_injected = 0.0  # m³ (total air injected during current cycle)
        self.injection_complete = False  # Flag for injection completion
        
        # Water displacement tracking
        self.displaced_water_volume = 0.0  # m³ (volume of water displaced by air)
        self.water_displacement_work = 0.0  # J (work done displacing water)
        
        # Position-based state tracking
        self.at_bottom_station = False  # True when positioned for air injection
        self.at_top_station = False  # True when positioned for air venting
        self.ready_for_injection = False  # True when positioned and ready
        self.injection_requested = False  # True when injection has been requested
        
        # Phase 7: Enhanced pneumatic properties for energy analysis
        self.air_temperature = 293.15  # K (temperature of air inside floater)
        self.last_injection_energy = 0.0  # J (energy used in last injection)
        self.thermal_energy_contribution = 0.0  # J (thermal energy boost from water heat)
        self.expansion_work_done = 0.0  # J (work done by air expansion during ascent)
        self.venting_energy_loss = 0.0  # J (energy lost during venting process)
        
        # Pneumatic efficiency tracking
        self.injection_efficiency = 0.85  # Efficiency of air injection process
        self.expansion_efficiency = 0.90  # Efficiency of air expansion during ascent
        
        # Enhanced thermal properties for heat exchange modeling
        self.surface_area_air_water = 0.0  # m² (air-water interface area)
        self.heat_transfer_coefficient = 150.0  # W/m²K (air-water heat transfer)
        
        if volume < 0 or mass < 0 or area < 0 or Cd < 0:
            logger.error("Invalid floater parameters: must be non-negative.")
            raise ValueError("Floater parameters must be non-negative.")
        self.set_filled(is_filled)
        logger.info(f"Initialized Floater: {self.to_dict()}")
        logger.debug(f"Added mass initialized: {self.added_mass}")

    def set_filled(self, filled: bool) -> None:
        """
        Set the filled state of the floater and reset progress.

        Args:
            filled (bool): True if filled with air, False otherwise.
        """
        if self.is_filled != filled:
            self.is_filled = filled
            self.fill_progress = 1.0 if filled else 0.0
            logger.info(f"Floater fill state changed: is_filled={self.is_filled}")

    def start_filling(self):
        """
        Begin the air filling process for the pulse.
        """
        if not self.is_filled:
            self.is_filled = True
            self.fill_progress = 0.0
            logger.info("Floater has started filling.")

    def compute_buoyant_force(self) -> float:
        """
        Compute the upward buoyant force based on the currently filled volume,
        adjusted for dissolved air fraction.

        Returns:
            float: Buoyant force (N)
        """
        # Phase 3: Use enhanced calculation if pneumatic system is active
        if hasattr(self, 'pressure_physics') and self.total_air_injected > 0:
            return self.compute_enhanced_buoyant_force()
        
        # Original calculation for legacy compatibility
        # Adjust fill progress based on dissolved air fraction
        effective_fill_progress = self.fill_progress * (1.0 - self.dissolved_air_fraction)

        # Buoyancy is based on the actual volume of air held
        displaced_volume = self.volume * effective_fill_progress
        F_buoy = RHO_WATER * displaced_volume * G
        logger.debug(f"Buoyant force: {F_buoy:.2f} N (effective_fill_progress={effective_fill_progress:.2f})")
        return F_buoy

    def compute_enhanced_buoyant_force(self, use_expansion_physics: bool = True) -> float:
        """
        Enhanced buoyant force calculation with pressure expansion physics (Phase 3).
        
        Args:
            use_expansion_physics: Whether to use pressure expansion calculations
            
        Returns:
            float: Enhanced buoyant force (N)
        """
        if not use_expansion_physics or self.total_air_injected <= 0:
            # Fall back to basic calculation
            return self.compute_buoyant_force()
        
        # Calculate current depth
        current_depth = self.pressure_physics.get_depth_from_position(
            self.position, self.tank_height)
        
        # Get expansion state
        self.expansion_state = self.pressure_physics.get_expansion_state(
            initial_depth=self.injection_depth,
            current_depth=current_depth,
            initial_air_volume=self.total_air_injected,
            expansion_mode=self.expansion_mode
        )
        
        # Update current air pressure
        self.current_air_pressure = self.expansion_state['current_pressure']
        
        # Calculate gas dissolution effects
        self.dissolved_air_fraction_enhanced = self.pressure_physics.calculate_gas_dissolution(
            air_pressure=self.current_air_pressure,
            current_dissolved_fraction=self.dissolved_air_fraction_enhanced,
            dt=0.01  # Use small time step for smooth dissolution
        )
        
        # Get effective air volume after expansion and dissolution
        expanded_volume = self.expansion_state['expanded_volume']
        effective_air_volume = self.pressure_physics.calculate_effective_air_volume(
            expanded_volume, self.dissolved_air_fraction_enhanced)
        
        # Calculate buoyant force
        buoyant_force = self.pressure_physics.calculate_buoyancy_from_expansion(
            floater_total_volume=self.volume,
            effective_air_volume=effective_air_volume
        )        
        logger.debug(f"Enhanced buoyancy: depth={current_depth:.2f}m, "
                    f"expanded_vol={expanded_volume*1000:.1f}L, "
                    f"effective_vol={effective_air_volume*1000:.1f}L, "
                    f"F_buoy={buoyant_force:.2f}N")
        
        return buoyant_force

    def compute_drag_force(self) -> float:
        """
        Compute the drag force opposing motion (quadratic drag).

        Returns:
            float: Drag force (N, sign opposes velocity)
        """
        drag_mag = 0.5 * self.Cd * RHO_WATER * self.area * (self.velocity ** 2)
        return -drag_mag if self.velocity > 0 else drag_mag

    def compute_pulse_jet_force(self) -> float:
        """
        Calculate the additional upward force from the water jet effect during the pulse.
        This force is only active while the floater is actively filling.

        Returns:
            float: Jet force (N)
        """
        # Phase 3: Check if pneumatic system is actively filling
        if hasattr(self, 'pneumatic_fill_state'):
            # Use pneumatic state - only active during filling
            if self.pneumatic_fill_state != 'filling':
                return 0.0
        else:
            # Legacy system - only active while fill progress is changing
            if not (0 < self.fill_progress < 1.0):
                return 0.0

        # Simplified model from pulse_physics.py
        v_jet = math.sqrt(2 * self.air_pressure / RHO_WATER)
        water_displacement_rate = self.air_flow_rate
        F_jet = self.jet_efficiency * RHO_WATER * water_displacement_rate * v_jet
        logger.debug(f"Pulse jet force: {F_jet:.2f} N")
        return F_jet

    @property
    def force(self) -> float:
        """
        Calculate the net force acting on the floater, including all effects.

        Returns:
            float: Net force (N)
        """
        F_buoy = self.compute_buoyant_force()
        F_jet = self.compute_pulse_jet_force()
        
        # Weight includes the mass of the air inside
        air_mass = RHO_AIR * self.volume * self.fill_progress
        F_gravity = -(self.mass + air_mass) * G
        
        F_drag = self.compute_drag_force()
        
        F_net = F_buoy + F_gravity + F_drag + F_jet
        logger.debug(f"Net force: {F_net:.2f} N (Buoy={F_buoy:.2f}, Jet={F_jet:.2f}, Grav={F_gravity:.2f}, Drag={F_drag:.2f})")
        return F_net

    def to_dict(self) -> dict:
        """
        Serialize the floater's state to a dictionary.

        Returns:
            dict: Dictionary representation of the floater's state.
        """
        return {
            'volume': self.volume,
            'mass': self.mass,
            'position': self.position,
            'velocity': self.velocity,
            'is_filled': self.is_filled,
            'fill_progress': self.fill_progress
        }

    def update(self, dt: float) -> None:
        """
        Update floater's state over a time step dt.
        Considers buoyancy, gravity, drag, and pulse jet forces.

        Args:
            dt (float): Time step (s)
        """
        if dt <= 0:
            raise ValueError("Time step dt must be positive.")

        # Track fill progress transitions
        prev_progress = self.fill_progress
        # Update fill progress if filling
        if self.is_filled and self.fill_progress < 1.0:
            # Rate of filling is determined by air_fill_time
            fill_rate = 1.0 / self.air_fill_time if self.air_fill_time > 0 else float('inf')
            self.fill_progress += fill_rate * dt
            if self.fill_progress >= 1.0:
                self.fill_progress = 1.0
                logger.info("Floater finished filling.")

        # Record old velocity for calculating drag loss
        old_velocity = self.velocity

        # Determine net force, allowing for test override of compute_buoyant_force as net force
        cb_override = self.__dict__.get('compute_buoyant_force', None)
        if cb_override is not None:
            F_net = cb_override()
        else:
            F_net = self.force

        # Compute drag force explicitly for loss calculation
        F_drag = self.compute_drag_force()
        # Calculate drag loss energy: |F_drag * velocity * dt|
        drag_loss = abs(F_drag * old_velocity * dt)

        # No dissolution or venting loss calculations yet
        dissolution_loss = 0.0
        venting_loss = 0.0

        # Update loss attributes for tracking
        self.drag_loss = drag_loss
        self.dissolution_loss = dissolution_loss
        self.venting_loss = venting_loss

        # Adjust acceleration to account for added mass
        total_mass = self.mass + self.added_mass
        a = F_net / total_mass if total_mass > 0 else 0.0

        # Update velocity and position
        self.velocity += a * dt
        # Clamp velocity to prevent runaway
        if self.velocity > self.MAX_VELOCITY:
            self.velocity = self.MAX_VELOCITY
        elif self.velocity < -self.MAX_VELOCITY:
            self.velocity = -self.MAX_VELOCITY
        self.position += self.velocity * dt
        # Clamp position and reset velocity if hitting boundaries
        if self.position < self.MIN_POSITION:
            self.position = self.MIN_POSITION
            self.velocity = 0.0
        elif self.position > self.MAX_POSITION:
            self.position = self.MAX_POSITION
            self.velocity = 0.0
        logger.debug(f"Updated Floater: pos={self.position:.2f}, vel={self.velocity:.2f}, acc={a:.2f}")
          # Apply simple dissolution: decrease fill_progress gradually when not actively filling
        if self.fill_progress > 0.0 and not (self.is_filled and prev_progress < 1.0):
            dissolution_rate = 0.001  # Fraction of air lost per second due to dissolution
            # Capture fill before dissolution
            before_fp = self.fill_progress
            # Reduce fill progress due to dissolution
            self.fill_progress = max(before_fp - dissolution_rate * dt, 0.0)
            # Track dissolved fraction increase
            delta = before_fp - self.fill_progress
            self.dissolved_air_fraction += delta

        # Phase 3: Update enhanced dissolution tracking for pneumatic system
        if hasattr(self, 'pressure_physics') and self.total_air_injected > 0:
            current_depth = self.pressure_physics.get_depth_from_position(
                self.position, self.tank_height)
            current_pressure = self.pressure_physics.get_pressure_at_depth(current_depth)
            
            # Update enhanced dissolution
            self.dissolved_air_fraction_enhanced = self.pressure_physics.calculate_gas_dissolution(
                air_pressure=current_pressure,
                current_dissolved_fraction=self.dissolved_air_fraction_enhanced,
                dt=dt
            )

    def reset(self):
        """
        Resets the floater to its initial state.
        """
        self.position = self.initial_position
        self.velocity = self.initial_velocity
        self.is_filled = self.initial_is_filled
        self.fill_progress = 1.0 if self.is_filled else 0.0
        logger.info(f"Floater state has been reset.")

    # === Pneumatic State Management Methods (Phase 2.2) ===
    
    def update_pneumatic_state(self, current_position: float, 
                              bottom_station_pos: float = 0.0,
                              top_station_pos: float = 10.0,
                              position_tolerance: float = 0.1) -> None:
        """
        Update position-based pneumatic state flags.
        
        Args:
            current_position: Current floater position
            bottom_station_pos: Position of bottom injection station
            top_station_pos: Position of top venting station  
            position_tolerance: Position tolerance for station detection
        """
        # Update position flags
        self.at_bottom_station = abs(current_position - bottom_station_pos) <= position_tolerance
        self.at_top_station = abs(current_position - top_station_pos) <= position_tolerance
          # Update readiness for injection
        self.ready_for_injection = (self.at_bottom_station and 
                                   self.pneumatic_fill_state == 'empty' and
                                   not self.injection_requested)
    
    def start_pneumatic_injection(self, target_volume: float, 
                                 injection_pressure: float,
                                 current_time: float) -> bool:
        """
        Start pneumatic air injection process.
        
        Args:
            target_volume: Target air volume to inject (m³)
            injection_pressure: Injection pressure (Pa)
            current_time: Current simulation time
            
        Returns:
            True if injection started successfully
        """
        if not self.ready_for_injection:
            return False
        
        self.pneumatic_fill_state = 'filling'
        self.target_air_volume = target_volume
        self.pneumatic_pressure = injection_pressure
        self.injection_start_time = current_time
        self.injection_requested = True
        self.injection_complete = False
        self.air_fill_level = 0.0
        self.total_air_injected = 0.0
        
        # Phase 3: Record injection conditions for expansion calculations
        self.injection_depth = self.pressure_physics.get_depth_from_position(
            self.position, self.tank_height)
        self.initial_air_pressure = injection_pressure
        self.current_air_pressure = injection_pressure
        
        logger.info(f"Pneumatic injection started: target={target_volume*1000:.1f}L at {injection_pressure/1000:.1f} kPa, "
                   f"depth={self.injection_depth:.2f}m")
        return True
    
    def update_pneumatic_injection(self, injected_volume: float, dt: float) -> None:
        """
        Update pneumatic injection progress.
        
        Args:
            injected_volume: Volume of air injected this time step (m³)
            dt: Time step duration (s)
        """
        if self.pneumatic_fill_state != 'filling':
            return
        
        # Update air fill level
        self.total_air_injected += injected_volume
        self.air_fill_level = min(1.0, self.total_air_injected / self.volume)
        
        # Update displaced water volume
        self.displaced_water_volume = self.total_air_injected
        
        # Calculate work done displacing water
        depth = max(0.0, self.position)  # Assume position represents depth
        self.water_displacement_work += RHO_WATER * G * injected_volume * depth
        
        # Check if injection is complete
        if (self.total_air_injected >= self.target_air_volume or 
            self.air_fill_level >= 1.0):
            self.complete_pneumatic_injection()
    
    def complete_pneumatic_injection(self) -> None:
        """Complete the pneumatic injection process."""
        self.pneumatic_fill_state = 'full'
        self.injection_complete = True
        self.is_filled = True  # Update legacy fill state
        self.fill_progress = self.air_fill_level  # Update legacy fill progress
        
        logger.info(f"Pneumatic injection completed: filled {self.air_fill_level*100:.1f}% "
                   f"({self.total_air_injected*1000:.1f}L)")
    
    def start_pneumatic_venting(self, current_time: float) -> bool:
        """
        Start pneumatic air venting process.
        
        Args:
            current_time: Current simulation time
            
        Returns:
            True if venting started successfully
        """
        if not (self.at_top_station and self.pneumatic_fill_state == 'full'):
            return False
        
        self.pneumatic_fill_state = 'venting'
        self.vent_start_time = current_time
        
        logger.info("Pneumatic venting started")
        return True
    
    def update_pneumatic_venting(self, venting_rate: float, dt: float) -> bool:
        """
        Update pneumatic venting progress.
        
        Args:
            venting_rate: Air venting rate (m³/s)
            dt: Time step duration (s)
            
        Returns:
            True if venting is complete
        """
        if self.pneumatic_fill_state != 'venting':
            return False
        
        # Vent air
        air_vented = venting_rate * dt
        self.total_air_injected = max(0.0, self.total_air_injected - air_vented)
        self.air_fill_level = self.total_air_injected / self.volume if self.volume > 0 else 0.0
        
        # Update displaced water volume
        self.displaced_water_volume = self.total_air_injected
          # Check if venting is complete (threshold of 0.5% for more reliable completion)
        if self.air_fill_level <= 0.005:  # 0.5% threshold for complete venting
            self.complete_pneumatic_venting()
            return True
        
        return False
    
    def complete_pneumatic_venting(self) -> None:
        """Complete the pneumatic venting process."""
        self.pneumatic_fill_state = 'empty'
        self.air_fill_level = 0.0
        self.total_air_injected = 0.0
        self.displaced_water_volume = 0.0
        self.pneumatic_pressure = 101325.0  # Reset to atmospheric
        self.injection_requested = False
        self.injection_complete = False
        
        # Update legacy state
        self.is_filled = False
        self.fill_progress = 0.0
        
        logger.info("Pneumatic venting completed - floater reset to empty state")
    
    def get_pneumatic_buoyant_force(self, depth: Optional[float] = None) -> float:
        """
        Calculate buoyant force based on pneumatic air content with pressure effects.
        
        Args:
            depth: Current depth (uses position if None)
            
        Returns:
            Buoyant force in Newtons
        """
        if depth is None:
            depth = max(0.0, self.position)
        
        # Calculate pressure at depth
        pressure_at_depth = 101325.0 + RHO_WATER * G * depth
        
        # Calculate effective air volume considering compression
        if self.pneumatic_pressure > 0:
            # Air compresses according to Boyle's law
            effective_air_volume = (self.total_air_injected * 
                                   self.pneumatic_pressure / pressure_at_depth)
        else:
            effective_air_volume = 0.0
        
        # Buoyant force = weight of displaced water
        buoyant_force = RHO_WATER * G * effective_air_volume
        
        return buoyant_force
    
    def get_pneumatic_status(self) -> Dict[str, Any]:
        """Get comprehensive pneumatic status."""
        return {
            'pneumatic_fill_state': self.pneumatic_fill_state,
            'air_fill_level': self.air_fill_level,
            'air_fill_percentage': self.air_fill_level * 100.0,
            'pneumatic_pressure_pa': self.pneumatic_pressure,
            'pneumatic_pressure_bar': self.pneumatic_pressure / 100000.0,
            'total_air_injected_l': self.total_air_injected * 1000.0,
            'displaced_water_volume_l': self.displaced_water_volume * 1000.0,
            'water_displacement_work_j': self.water_displacement_work,
            'at_bottom_station': self.at_bottom_station,
            'at_top_station': self.at_top_station,
            'ready_for_injection': self.ready_for_injection,
            'injection_requested': self.injection_requested,
            'injection_complete': self.injection_complete
        }

    def set_chain_params(self, major_axis, minor_axis, chain_radius):
        """
        Set the geometric parameters for the elliptical/circular chain path.
        """
        self.major_axis = major_axis  # a (horizontal radius)
        self.minor_axis = minor_axis  # b (vertical radius)
        self.chain_radius = chain_radius

    def set_theta(self, theta):
        """
        Set the angular position of the floater along the chain.
        """
        self.theta = theta % (2 * math.pi)

    def get_cartesian_position(self):
        """
        Get the (x, y) position of the floater along the ellipse/circle.
        """
        x = self.major_axis * math.cos(self.theta)
        y = self.minor_axis * math.sin(self.theta)
        return x, y

    def get_vertical_force(self):
        """
        Get the vertical force (buoyancy, gravity, drag, jet) at the current position.
        """
        # Use the same force calculation as before, but only the vertical component matters for torque
        return self.force

    def pivot(self) -> None:
        """
        Simulate a 180° rotation at a sprocket.
        """
        self.pivoted = not self.pivoted
        logger.info(f"Floater pivoted. New orientation pivoted={self.pivoted}")

    def drain_water(self) -> None:
        """
        Drain water from the floater, resetting water mass.
        """
        self.water_mass = 0.0
        logger.info("Floater water drained before air injection.")

    # === Phase 4: Venting and Reset Methods ===
    
    def check_venting_trigger(self, venting_system) -> bool:
        """
        Check if this floater should trigger venting.
        
        Args:
            venting_system: AutomaticVentingSystem instance
            
        Returns:
            True if venting should be triggered
        """
        floater_id = f"floater_{id(self)}"  # Simple ID based on object ID
        return venting_system.check_venting_trigger(
            floater_id, self.position, getattr(self, 'tilt_angle', 0.0))
    
    def start_venting_process(self, venting_system, current_time: float) -> bool:
        """
        Start the venting process for this floater.
        
        Args:
            venting_system: AutomaticVentingSystem instance
            current_time: Current simulation time
            
        Returns:
            True if venting was started successfully
        """
        if self.pneumatic_fill_state != 'full' or self.total_air_injected <= 0:
            return False
        
        floater_id = f"floater_{id(self)}"
        
        # Start venting in the system
        venting_state = venting_system.start_venting(
            floater_id=floater_id,
            initial_air_volume=self.total_air_injected,
            initial_air_pressure=self.current_air_pressure,
            floater_total_volume=self.volume,
            current_time=current_time
        )
        
        # Update floater state
        self.pneumatic_fill_state = 'venting'
        self.vent_start_time = current_time
        
        logger.info(f"Floater venting started at position {self.position:.2f}m")
        return True
    
    def update_venting_process(self, venting_system, dt: float) -> bool:
        """
        Update the venting process for this floater.
        
        Args:
            venting_system: AutomaticVentingSystem instance
            dt: Time step duration
            
        Returns:
            True if venting is complete
        """
        if self.pneumatic_fill_state != 'venting':
            return False
        
        floater_id = f"floater_{id(self)}"
        
        try:
            # Update venting in the system
            venting_state = venting_system.update_venting_process(
                floater_id, self.position, dt)
            
            # Sync floater state with venting system
            self.total_air_injected = venting_state['current_air_volume']
            self.current_air_pressure = venting_state['current_air_pressure']
            self.air_fill_level = self.total_air_injected / self.volume if self.volume > 0 else 0.0
            self.displaced_water_volume = self.total_air_injected
            
            # Update water mass in floater
            water_volume = venting_state['water_volume']
            self.water_mass = RHO_WATER * water_volume
            
            # Check if venting is complete
            if venting_state['venting_complete']:
                self.complete_venting_process(venting_system)
                return True
                
        except ValueError:
            # Venting process not found - already completed
            logger.warning(f"Venting process not found for floater")
            return True
        
        return False
    
    def complete_venting_process(self, venting_system) -> None:
        """
        Complete the venting process and reset floater to heavy state.
        
        Args:
            venting_system: AutomaticVentingSystem instance
        """
        floater_id = f"floater_{id(self)}"
        
        # Reset pneumatic state to empty
        self.pneumatic_fill_state = 'empty'
        self.air_fill_level = 0.0
        self.total_air_injected = 0.0
        self.displaced_water_volume = 0.0
        self.current_air_pressure = 101325.0  # Atmospheric pressure
        self.injection_requested = False
        self.injection_complete = False
        
        # Reset legacy state
        self.is_filled = False
        self.fill_progress = 0.0
        
        # Update water mass to full floater volume
        self.water_mass = RHO_WATER * self.volume
        
        # Clean up venting system tracking
        venting_system.cleanup_completed_venting(floater_id)
        
        logger.info(f"Floater venting completed - reset to heavy state with {self.water_mass:.1f} kg water")
    
    def get_venting_status(self, venting_system) -> Optional[Dict[str, Any]]:
        """
        Get current venting status for this floater.
        
        Args:
            venting_system: AutomaticVentingSystem instance
            
        Returns:
            Venting status dictionary or None
        """
        floater_id = f"floater_{id(self)}"
        return venting_system.get_venting_status(floater_id)
    
    def is_ready_for_descent(self) -> bool:
        """
        Check if floater is ready for descent phase after venting.
        
        Returns:
            True if floater is heavy and ready to descend
        """
        return (self.pneumatic_fill_state == 'empty' and 
                self.total_air_injected <= 0.001 and  # Essentially no air
                self.water_mass > 0.9 * RHO_WATER * self.volume)  # >90% filled with water
