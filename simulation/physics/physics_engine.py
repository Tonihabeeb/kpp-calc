"""
Physics Engine for KPP Simulation (Enhanced for Stage 2)
Handles core physics calculations with proper time-stepping, force integration,
and advanced state synchronization.
"""

import math
import logging
from config.config import G, RHO_WATER

logger = logging.getLogger(__name__)

class PhysicsEngine:
    """
    Core physics engine for KPP simulation with proper force calculations 
    and time-stepping integration. Enhanced with Stage 2 features.
    """
    
    def __init__(self, params=None):
        """
        Initialize the physics engine with simulation parameters.
        
        Args:
            params (dict): Physics simulation parameters
        """
        self.params = params or {}  # Store parameters for optimizer access
        # Extract parameters with defaults
        self.water_density = params.get('water_density', 1000.0) if params else 1000.0
        self.gravity = params.get('gravity', 9.81) if params else 9.81
        self.buoyancy_factor = params.get('buoyancy_factor', 1.0) if params else 1.0
        self.fluid_damping = params.get('fluid_damping', 0.8) if params else 0.8
        self.chain_stiffness = params.get('chain_stiffness', 100000.0) if params else 100000.0
        
        # Time-stepping parameters  
        self.adaptive_timestep = params.get('adaptive_timestep', False) if params else False
        self.min_timestep = params.get('min_timestep', 0.01) if params else 0.01
        self.max_timestep = params.get('max_timestep', 0.2) if params else 0.2
        self.dt = params.get('dt', 0.1) if params else 0.1  # Default timestep
        
        # Legacy attribute aliases for compatibility
        self.rho_water = self.water_density
        self.g = self.gravity
        self.adaptive_timestep_enabled = self.adaptive_timestep
        self.chain_mass = params.get('chain_mass', 50.0) if params else 50.0
        self.friction_coefficient = params.get('friction_coefficient', 0.1) if params else 0.1
        
        # Simulation state
        self.v_chain = 0.0  # Chain linear velocity (m/s)
        self.theta_chain = 0.0  # Chain rotation angle (rad)
        self.time = 0.0
        
        # Energy tracking (enhanced)
        self.cumulative_energy_out = 0.0  # Electrical energy output (J)
        self.energy_input = 0.0  # Compressor energy input (J)
        self.instantaneous_power = 0.0  # Current power output (W)
        self.peak_power = 0.0  # Peak power achieved (W)
        self.energy_efficiency = 0.0  # Current efficiency ratio
        
        # Stage 2: Advanced tracking
        self.force_history = []  # Track force calculations
        self.velocity_history = []  # Track velocity changes
        self.acceleration_history = []  # Track acceleration
        self.state_validation_enabled = True
        
        logger.info(f"PhysicsEngine (Stage 2) initialized with dt={self.dt}s, "
                   f"adaptive_timestep={self.adaptive_timestep_enabled}")
    
    def calculate_floater_forces(self, floater, velocity):
        """
        Calculate all forces acting on a single floater with enhanced accuracy.
        
        Args:
            floater: Floater object with volume, mass, drag properties
            velocity (float): Floater velocity (m/s, positive = upward)
            
        Returns:
            dict: Detailed force breakdown
        """
        # Buoyant force (constant, always upward)
        volume = getattr(floater, 'volume', 0.04)
        F_buoy = self.rho_water * volume * self.g
        
        # Weight force (depends on floater state with validation)
        container_mass = getattr(floater, 'container_mass', 50.0)
        
        if hasattr(floater, 'state') and floater.state == "light":
            # Air-filled: only container mass
            expected_mass = container_mass
            mass = floater.mass
            
            # State validation
            if self.state_validation_enabled and abs(mass - expected_mass) > 1.0:
                logger.warning(f"Mass inconsistency: light floater has mass={mass:.1f}, expected={expected_mass:.1f}")
                mass = expected_mass  # Use expected mass for force calculation
        else:
            # Water-filled: container + water mass
            water_mass = self.rho_water * volume
            expected_mass = container_mass + water_mass
            mass = floater.mass
            
            # State validation
            if self.state_validation_enabled and abs(mass - expected_mass) > 1.0:
                logger.warning(f"Mass inconsistency: heavy floater has mass={mass:.1f}, expected={expected_mass:.1f}")
                mass = expected_mass  # Use expected mass for force calculation
        
        F_weight = mass * self.g
        
        # Enhanced drag force calculation
        if abs(velocity) > 1e-6:  # Avoid division by zero
            drag_coefficient = getattr(floater, 'Cd', 0.8)
            area = getattr(floater, 'area', 0.2)  # m²
            
            # Reynolds number effects (simplified)
            reynolds = abs(velocity) * math.sqrt(area) * self.rho_water / 1e-6  # Approximate
            if reynolds > 1000:  # Turbulent flow
                effective_cd = drag_coefficient
            else:  # Laminar flow
                effective_cd = drag_coefficient * (1.0 + 24.0 / max(reynolds, 1.0))
            
            F_drag = 0.5 * self.rho_water * effective_cd * area * velocity**2
            # Apply drag opposite to motion direction
            F_drag = -F_drag * math.copysign(1, velocity)
        else:
            F_drag = 0.0
        
        # Net force calculation
        F_net = F_buoy - F_weight + F_drag
        
        # Store force data for analysis
        force_data = {
            'F_buoy': F_buoy,
            'F_weight': F_weight,
            'F_drag': F_drag,
            'F_net': F_net,
            'mass': mass,
            'velocity': velocity,
            'state': getattr(floater, 'state', 'unknown'),
            'time': self.time
        }
        
        # Keep force history for optimization
        self.force_history.append(force_data)
        if len(self.force_history) > 100:  # Limit history size
            self.force_history.pop(0)
        
        logger.debug(f"Enhanced forces: F_buoy={F_buoy:.1f}N, F_weight={F_weight:.1f}N, "
                    f"F_drag={F_drag:.1f}N, F_net={F_net:.1f}N, vel={velocity:.2f}m/s, state={force_data['state']}")
        
        return F_net
    
    def update_chain_dynamics(self, floaters, generator_torque, sprocket_radius):
        """
        Update chain dynamics by calculating forces from all floaters and 
        computing resulting acceleration.
        
        Args:
            floaters: List of floater objects
            generator_torque (float): Resistive torque from generator (N⋅m)
            sprocket_radius (float): Radius of drive sprocket (m)
            
        Returns:
            tuple: (chain_acceleration, net_force_total, power_output)
        """
        # Calculate total moving mass
        M_total = sum(f.mass for f in floaters) + self.chain_mass
        
        # Calculate net force from all floaters
        F_net_total = 0.0
        for i, floater in enumerate(floaters):
            # Determine floater velocity based on chain velocity and position
            if self.is_floater_ascending(floater):
                floater_velocity = self.v_chain  # Positive (upward)
            else:
                floater_velocity = -self.v_chain  # Negative (downward)
            
            # Update floater velocity for other calculations
            floater.velocity = floater_velocity
            
            # Calculate forces and add to total
            floater_force = self.calculate_floater_forces(floater, floater_velocity)
            F_net_total += floater_force
            
            logger.debug(f"Floater {i}: ascending={self.is_floater_ascending(floater)}, "
                        f"vel={floater_velocity:.2f}m/s, force={floater_force:.1f}N")
        
        # Include friction force (opposes motion)
        if abs(self.v_chain) > 1e-6:
            F_friction = self.friction_coefficient * M_total * self.g
            F_net_total -= F_friction * math.copysign(1, self.v_chain)
        
        # Include generator resistance force
        if abs(generator_torque) > 1e-6 and abs(sprocket_radius) > 1e-6:
            F_gen = generator_torque / sprocket_radius
            F_net_total -= F_gen * math.copysign(1, self.v_chain)
        else:
            F_gen = 0.0
        
        # Calculate chain acceleration
        if M_total > 0:
            a_chain = F_net_total / M_total
        else:
            a_chain = 0.0
            logger.warning("Total mass is zero or negative!")
        
        # Calculate power output
        omega = self.v_chain / sprocket_radius if abs(sprocket_radius) > 1e-6 else 0.0
        power_output = generator_torque * abs(omega)  # Always positive power
        
        # Log chain dynamics for debugging
        logger.debug(f"Chain dynamics: F_net={F_net_total:.1f}N, M_total={M_total:.1f}kg, "
                    f"a_chain={a_chain:.3f}m/s², power_out={power_output:.1f}W")
        
        # Stage 2: Record velocity and acceleration history
        self.velocity_history.append({
            'time': self.time,
            'velocity': self.v_chain
        })
        self.acceleration_history.append({
            'time': self.time,
            'acceleration': a_chain
        })
        
        return a_chain, F_net_total, power_output
    
    def is_floater_ascending(self, floater):
        """
        Determine if floater is on ascending side of chain loop.
        
        Args:
            floater: Floater object with angle property
            
        Returns:
            bool: True if ascending (0 to π), False if descending (π to 2π)
        """
        if hasattr(floater, 'angle'):
            angle_normalized = floater.angle % (2 * math.pi)
            return 0 <= angle_normalized < math.pi
        elif hasattr(floater, 'theta'):
            theta_normalized = floater.theta % (2 * math.pi)
            return 0 <= theta_normalized < math.pi
        else:
            # Fallback: assume ascending if no position info
            logger.warning(f"Floater has no angle/theta attribute, assuming ascending")
            return True
    
    def integrate_motion(self, acceleration):
        """
        Integrate chain motion using Euler method.
        
        Args:
            acceleration (float): Chain acceleration (m/s²)
        """
        # Update velocity
        self.v_chain += acceleration * self.dt
        
        # Update position/angle
        if abs(self.v_chain) > 1e-6:
            distance_moved = self.v_chain * self.dt
            # Assuming sprocket radius for angle calculation
            # This will be refined when sprocket radius is available
            sprocket_radius = 1.0  # Default, should be passed as parameter
            self.theta_chain += distance_moved / sprocket_radius
            
            # Normalize angle to [0, 2π)
            self.theta_chain = self.theta_chain % (2 * math.pi)
        
        # Update time
        self.time += self.dt
    
    def update_floater_positions(self, floaters, sprocket_radius=1.0, enhanced_physics=None):
        """
        Update all floater positions based on chain motion.
        
        Args:
            floaters: List of floater objects
            sprocket_radius (float): Radius of drive sprocket (m)
            enhanced_physics (dict): Dictionary containing H1, H2, H3 physics modules
        """
        if abs(self.v_chain) > 1e-6:
            # Calculate angular displacement
            distance_moved = self.v_chain * self.dt
            angular_displacement = distance_moved / sprocket_radius
            
            for floater in floaters:
                # Update floater angle/theta
                if hasattr(floater, 'angle'):
                    floater.angle += angular_displacement
                    floater.angle = floater.angle % (2 * math.pi)
                elif hasattr(floater, 'theta'):
                    floater.theta += angular_displacement
                    floater.theta = floater.theta % (2 * math.pi)
                
                # Update other floater state if it has an update method
                if hasattr(floater, 'update'):
                    # Pass enhanced physics to floater update if available
                    if enhanced_physics:
                        floater.update(self.dt, enhanced_physics)
                    else:
                        floater.update(self.dt)
    
    def step(self, floaters, generator_torque, sprocket_radius, enhanced_physics=None):
        """
        Perform one physics time step.
        
        Args:
            floaters: List of floater objects
            generator_torque (float): Generator resistive torque (N⋅m)
            sprocket_radius (float): Sprocket radius (m)
            enhanced_physics (dict): Dictionary containing H1, H2, H3 physics modules
            
        Returns:
            dict: Physics state data for this step
        """
        # Calculate forces and acceleration
        a_chain, F_net_total, power_output = self.update_chain_dynamics(
            floaters, generator_torque, sprocket_radius
        )
        
        # Integrate motion
        self.integrate_motion(a_chain)
        
        # Update floater positions with enhanced physics
        self.update_floater_positions(floaters, sprocket_radius, enhanced_physics)
        
        # Update energy tracking
        self.cumulative_energy_out += power_output * self.dt
        
        # Stage 2: Calculate energy efficiency
        if self.energy_input > 0:
            self.energy_efficiency = (self.cumulative_energy_out / self.energy_input) * 100.0
        
        # Return state data
        return {
            'time': self.time,
            'chain_velocity': self.v_chain,
            'chain_acceleration': a_chain,
            'net_force_total': F_net_total,
            'angular_velocity': self.v_chain / sprocket_radius,
            'power_output': power_output,
            'energy_output': self.cumulative_energy_out,
            'energy_input': self.energy_input,
            'energy_efficiency': self.energy_efficiency
        }
    
    def get_state(self):
        """
        Get current physics engine state.
        
        Returns:
            dict: Current state information
        """
        return {
            'time': self.time,
            'chain_velocity': self.v_chain,
            'chain_angle': self.theta_chain,
            'energy_output': self.cumulative_energy_out,
            'energy_input': self.energy_input,
            'net_energy': self.cumulative_energy_out - self.energy_input,
            'instantaneous_power': self.instantaneous_power,
            'peak_power': self.peak_power,
            'energy_efficiency': self.energy_efficiency
        }
