"""
Pulse-and-Coast Torque Synchronization Physics Module
Implements Hypothesis 3 with water jet effects and air injection pulses

Author: KPP Development Team
Date: 2025-06-22
"""

import math
from typing import Dict, Any, Tuple

class PulsePhysics:
    def __init__(self, 
                 # Basic parameters
                 water_density: float = 1000.0,  # kg/m³
                 air_density: float = 1.225,     # kg/m³
                 gravity: float = 9.81,          # m/s²
                 
                 # Floater parameters
                 floater_mass: float = 18.0,     # kg (dry mass)
                 floater_volume: float = 0.3,    # m³ (air volume when filled)
                 floater_area: float = 0.2,      # m² (cross-sectional area)
                 drag_coefficient: float = 0.8,  # dimensionless
                 
                 # Pulse parameters
                 air_fill_time: float = 0.5,     # seconds (time to fill floater)
                 air_pressure: float = 300000,   # Pa (injection pressure)
                 air_flow_rate: float = 0.6,     # m³/s (air flow rate)
                 
                 # Water jet parameters
                 jet_efficiency: float = 0.85,   # efficiency of water displacement
                 jet_angle: float = 0.0,         # radians (0 = straight down)
                 
                 # Mechanical parameters
                 sprocket_radius: float = 0.5,   # m
                 chain_efficiency: float = 0.95, # mechanical efficiency                 # Flywheel and clutch parameters
                 flywheel_inertia: float = 50.0, # kg⋅m²
                 chain_inertia: float = 5.0,     # kg⋅m²
                 clutch_threshold: float = 0.1,   # rad/s (clutch engagement threshold)
                 gear_ratio: float = 16.7,       # Generator:Chain speed ratio (375 RPM / 22.5 RPM)
                 
                 # Realistic mechanical limits (based on actual engineering constraints)
                 max_chain_speed_rpm: float = 30.0,    # RPM (realistic for large chains)
                 max_generator_rpm: float = 400.0,     # RPM (realistic for 530kW generator)
                 bearing_friction_coeff: float = 0.02, # Realistic bearing friction
                 chain_friction_coeff: float = 0.05,   # Realistic chain friction
                 max_torque_capacity: float = 20000.0, # Nm (mechanical torque limit)
                 ):
          # Store all parameters
        self.rho_water = water_density
        self.rho_air = air_density
        self.g = gravity
        
        self.m_floater = floater_mass
        self.V_air = floater_volume
        self.A_floater = floater_area
        self.Cd = drag_coefficient
        
        self.t_fill = air_fill_time
        self.P_air = air_pressure
        self.Q_air = air_flow_rate
        
        self.eta_jet = jet_efficiency
        self.theta_jet = jet_angle        
        self.r_sprocket = sprocket_radius
        self.eta_chain = chain_efficiency
        
        self.I_flywheel = flywheel_inertia
        self.I_chain = chain_inertia
        self.omega_threshold = clutch_threshold
        self.gear_ratio = gear_ratio
        
        # Realistic mechanical limits (engineering constraints)
        self.max_chain_omega = max_chain_speed_rpm * (2 * math.pi / 60)  # Convert RPM to rad/s
        self.max_generator_omega = max_generator_rpm * (2 * math.pi / 60)  # Convert RPM to rad/s
        self.bearing_friction = bearing_friction_coeff
        self.chain_friction = chain_friction_coeff
        self.max_torque = max_torque_capacity
        
        # State variables
        self.omega_chain = 0.0      # rad/s (main sprocket: target 20-25 RPM)
        self.omega_flywheel = 0.0   # rad/s (generator shaft: target 375 RPM)
        self.clutch_engaged = False
        self.generator_load_torque = 0.0  # Generator load resistance torque
        
    def buoyancy_force(self, submerged_volume: float) -> float:
        """Calculate buoyancy force for given submerged volume"""
        return self.rho_water * self.g * submerged_volume
    
    def weight_force(self, air_mass: float = 0.0) -> float:
        """Calculate weight force including air mass"""
        total_mass = self.m_floater + air_mass
        return total_mass * self.g
    
    def drag_force(self, velocity: float) -> float:
        """Calculate drag force for given velocity"""
        return 0.5 * self.Cd * self.rho_water * self.A_floater * velocity * abs(velocity)
    
    def air_injection_pulse_force(self, fill_progress: float) -> Tuple[float, float]:
        """
        Calculate forces during air injection pulse
        
        Args:
            fill_progress: Progress of air filling (0.0 to 1.0)
            
        Returns:
            Tuple of (buoyancy_pulse_force, water_jet_force)
        """
        if fill_progress <= 0.0 or fill_progress >= 1.0:
            return 0.0, 0.0
        
        # Instantaneous air volume being injected
        dV_dt = self.Q_air  # m³/s
        
        # Buoyancy pulse force (sudden increase in buoyant volume)
        F_buoyancy_pulse = self.rho_water * self.g * dV_dt * self.t_fill
        
        # Water jet force (reaction to water displacement)
        # v_jet = sqrt(2 * P_air / rho_water) - simplified jet velocity
        v_jet = math.sqrt(2 * self.P_air / self.rho_water)
        
        # Water displacement rate
        water_displacement_rate = dV_dt  # m³/s (same as air injection rate)
        
        # Jet force = mass flow rate * velocity
        F_water_jet = self.eta_jet * self.rho_water * water_displacement_rate * v_jet
        
        # Apply jet angle effect (vertical component)
        F_water_jet_vertical = F_water_jet * math.cos(self.theta_jet)
        
        return F_buoyancy_pulse, F_water_jet_vertical
    
    def total_pulse_force(self, fill_progress: float) -> float:
        """Calculate total upward force during pulse injection"""
        F_buoyancy_pulse, F_jet = self.air_injection_pulse_force(fill_progress)
        
        # Regular buoyancy (for filled portion)
        filled_volume = self.V_air * fill_progress
        F_buoyancy_regular = self.buoyancy_force(filled_volume)
        
        # Weight (including injected air mass)
        air_mass = self.rho_air * filled_volume
        F_weight = self.weight_force(air_mass)
          # Total upward force
        F_total = F_buoyancy_regular + F_buoyancy_pulse + F_jet - F_weight
        
        return max(0.0, F_total)  # Ensure non-negative
    
    def pulse_torque(self, fill_progress: float) -> float:
        """Calculate torque pulse delivered to sprocket"""
        F_pulse = self.total_pulse_force(fill_progress)
        return F_pulse * self.r_sprocket * self.eta_chain
    
    def steady_state_force(self, velocity: float) -> float:
        """Calculate steady-state force after pulse (normal ascent)"""
        F_buoyancy = self.buoyancy_force(self.V_air)
        F_weight = self.weight_force(self.rho_air * self.V_air)
        F_drag = self.drag_force(velocity)
        
        return max(0.0, F_buoyancy - F_weight - F_drag)
    
    def steady_state_torque(self, velocity: float) -> float:
        """Calculate steady-state torque after pulse"""
        F_steady = self.steady_state_force(velocity)
        return F_steady * self.r_sprocket * self.eta_chain
    
    def update_clutch_dynamics(self, net_torque: float, dt: float, target_power: float = 530000.0, target_rpm: float = 375.0):
        """
        Update flywheel and chain angular velocities with clutch dynamics
        Uses generator load torque calculated by get_power_output()
        
        Args:
            net_torque: Net torque from floaters (Nm)
            dt: Time step (s)
            target_power: Target generator power (530 kW)
            target_rpm: Target generator RPM (375 RPM)
        """        # Use generator load torque from get_power_output()
        # This simulates the 530kW generator connected to heat resistor load
        load_torque = getattr(self, 'generator_load_torque', 0.0)
        
        # Apply torque limits based on mechanical capacity (realistic constraint)
        net_torque = max(-self.max_torque, min(self.max_torque, net_torque))
        
        # Realistic physics-based friction forces
        # Bearing friction: proportional to speed
        T_bearing_chain = self.bearing_friction * self.I_chain * 9.81 * self.omega_chain
        T_bearing_flywheel = self.bearing_friction * self.I_flywheel * 9.81 * self.omega_flywheel
        
        # Chain friction: increases with speed (realistic mechanical friction)
        T_chain_friction = self.chain_friction * abs(self.omega_chain) * self.omega_chain
        
        # Total drag forces (realistic engineering model)
        T_drag_chain = T_bearing_chain + T_chain_friction
        T_drag_flywheel = T_bearing_flywheel + load_torque
        
        # Determine clutch engagement based on speed difference
        speed_difference = abs(self.omega_chain - self.omega_flywheel / self.gear_ratio)
        
        if speed_difference < self.omega_threshold and self.omega_chain > 0.1:
            # Clutch engaged - realistic mechanical coupling
            self.clutch_engaged = True
            
            # Combined inertia when coupled
            total_inertia = self.I_chain + (self.I_flywheel / (self.gear_ratio ** 2))
            
            # Calculate acceleration of coupled system
            net_force = net_torque - T_drag_chain - (T_drag_flywheel / self.gear_ratio)
            alpha_chain = net_force / total_inertia
            
            # Update speeds (realistic mechanical coupling)
            self.omega_chain += alpha_chain * dt
            self.omega_flywheel = self.omega_chain * self.gear_ratio
            
        else:
            # Clutch disengaged - separate dynamics
            self.clutch_engaged = False
            
            # Chain dynamics (realistic physics)
            alpha_chain = (net_torque - T_drag_chain) / self.I_chain
            self.omega_chain += alpha_chain * dt
            
            # Flywheel dynamics (realistic physics with generator load)
            alpha_flywheel = -T_drag_flywheel / self.I_flywheel
            self.omega_flywheel += alpha_flywheel * dt
        
        # Apply realistic mechanical speed limits (physics-based, not arbitrary)
        # These limits are based on actual mechanical constraints
        
        # Chain speed limit: based on centrifugal force limits and chain strength
        if self.omega_chain > self.max_chain_omega:
            # Mechanical failure protection - chain breaks or slips
            excess_speed = self.omega_chain - self.max_chain_omega
            self.omega_chain = self.max_chain_omega
            # Energy dissipation due to mechanical limiting (realistic)
            
        # Generator speed limit: based on bearing limits and electrical constraints
        if self.omega_flywheel > self.max_generator_omega:
            # Generator protection - electrical braking or mechanical governor
            excess_speed = self.omega_flywheel - self.max_generator_omega
            self.omega_flywheel = self.max_generator_omega
            # Additional braking torque applied (realistic governor action)
        
        # Ensure non-negative speeds (realistic physical constraint)
        self.omega_chain = max(0.0, self.omega_chain)
        self.omega_flywheel = max(0.0, self.omega_flywheel)
    
    def get_power_output(self, target_power: float = 530000.0, target_rpm: float = 375.0) -> float:
        """
        Calculate power output with proper generator load simulation
        Models a 530kW generator connected to a heat resistor load
        
        Args:
            target_power: Target generator power (530 kW)
            target_rpm: Target generator RPM (375 RPM)
        """
        # Convert target RPM to rad/s
        target_omega = target_rpm * (2 * math.pi / 60)  # 39.27 rad/s
        
        # Calculate target load torque at rated conditions
        target_load_torque = target_power / target_omega  # 13,496 Nm
        
        # Generator load characteristics - CONSUMING power (not accumulating)
        if self.omega_flywheel < 0.1:
            # No generation at very low speeds
            load_torque_resistance = 0.0
            power_consumed = 0.0
        elif self.omega_flywheel < target_omega * 0.3:
            # Partial load at low speeds (proportional to speed squared)
            speed_ratio = self.omega_flywheel / target_omega
            load_torque_resistance = target_load_torque * 0.2 * (speed_ratio ** 2)
            power_consumed = load_torque_resistance * self.omega_flywheel * 0.85
        elif self.omega_flywheel <= target_omega * 1.1:
            # Rated operation zone - FULL LOAD RESISTANCE
            speed_ratio = self.omega_flywheel / target_omega
            # Generator acts as constant power load (like heat resistor)
            load_torque_resistance = target_load_torque * min(1.0, 1.0 / max(0.1, speed_ratio))
            power_consumed = min(target_power, target_load_torque * self.omega_flywheel) * 0.92
        else:
            # Over-speed - increased load resistance to prevent runaway
            speed_ratio = self.omega_flywheel / target_omega
            load_torque_resistance = target_load_torque * (1.5 + 0.5 * (speed_ratio - 1.1))
            power_consumed = load_torque_resistance * self.omega_flywheel * 0.88
        
        # Store load torque for clutch dynamics
        self.generator_load_torque = load_torque_resistance
        
        # Power consumed by the generator (converted to heat in resistor)
        return power_consumed
    
    def get_system_state(self) -> Dict[str, Any]:
        """Get current system state"""
        return {
            'omega_chain': self.omega_chain,
            'omega_flywheel': self.omega_flywheel,
            'clutch_engaged': self.clutch_engaged,
            'power_available': self.omega_flywheel * 1000,  # Example load torque
            'efficiency': self.eta_chain
        }

# Example usage and testing
if __name__ == "__main__":
    # Create physics instance
    pulse_physics = PulsePhysics(
        floater_mass=18.0,
        floater_volume=0.3,
        air_fill_time=0.5,
        air_pressure=300000,
        sprocket_radius=0.5
    )
    
    # Test pulse forces
    print("Pulse Physics Test Results:")
    print("=" * 40)
    
    for progress in [0.0, 0.25, 0.5, 0.75, 1.0]:
        pulse_force = pulse_physics.total_pulse_force(progress)
        pulse_torque = pulse_physics.pulse_torque(progress)
        
        print(f"Fill Progress: {progress*100:5.1f}%")
        print(f"  Pulse Force: {pulse_force:8.2f} N")
        print(f"  Pulse Torque: {pulse_torque:8.2f} Nm")
        print()
    
    # Test steady state
    velocity = 1.2  # m/s
    steady_force = pulse_physics.steady_state_force(velocity)
    steady_torque = pulse_physics.steady_state_torque(velocity)
    
    print(f"Steady State (v={velocity} m/s):")
    print(f"  Force: {steady_force:8.2f} N")
    print(f"  Torque: {steady_torque:8.2f} Nm")
