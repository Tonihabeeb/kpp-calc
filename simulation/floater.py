class Floater:
    def __init__(self, id, params):
        self.id = id
        self.position = 0.0
        self.velocity = 0.0
        self.state = 'idle'  # could be 'ascending', 'descending', etc.
        self.force = 0.0
        self.mass = params.get('floater_mass_empty', 2.0)
        self.volume = params.get('floater_volume', 0.04)
        self.area = params.get('floater_area', 0.1)
        self.drag_coeff = 0.3  # More realistic drag coefficient for underwater objects
        self.base_fluid_density = 1000  # Base water density, kg/m^3
        self.fluid_density = 1000  # Current water density (affected by H1/H2)
        self.g = 9.81
        self.buoyancy = 0.0
        self.gravity = 0.0
        self.drag = 0.0
        self.net_force = 0.0
        
        # H1/H2 effect parameters
        self.nanobubble_frac = params.get('nanobubble_frac', 0.0)  # H1: nanobubble fraction
        self.thermal_expansion_coeff = params.get('thermal_coeff', 0.0001)  # H2: thermal expansion
        self.water_temp = params.get('water_temp', 20.0)  # Current water temperature
        self.ref_temp = params.get('ref_temp', 20.0)  # Reference temperature
        
        # Pulse-related attributes
        self.is_pulsing = False
        self.pulse_start_time = 0.0
        self.pulse_duration = params.get('air_fill_time', 0.5)
        self.pulse_force = 0.0
        self.fill_progress = 0.0
        
        # Air injection parameters
        self.air_pressure = params.get('air_pressure', 300000)  # Pa
        self.air_flow_rate = params.get('air_flow_rate', 0.6)   # m³/s
        self.water_jet_efficiency = params.get('jet_efficiency', 0.85)

    def start_pulse(self, current_time):
        """Start air injection pulse"""
        self.is_pulsing = True
        self.pulse_start_time = current_time
        self.fill_progress = 0.0
        self.state = 'pulsing'

    def calculate_pulse_forces(self):
        """Calculate additional forces during air injection pulse"""
        if not self.is_pulsing or self.fill_progress >= 1.0:
            return 0.0
        
        import math
        
        # Air injection rate
        dV_dt = self.air_flow_rate
        
        # Buoyancy pulse force (sudden increase in buoyant volume)
        F_buoyancy_pulse = self.fluid_density * self.g * dV_dt * self.pulse_duration
        
        # Water jet force (reaction to water displacement)
        v_jet = math.sqrt(2 * self.air_pressure / self.fluid_density)
        F_water_jet = self.water_jet_efficiency * self.fluid_density * dV_dt * v_jet
        
        return F_buoyancy_pulse + F_water_jet

    def calculate_h1_h2_effects(self, params):
        """
        Calculate H1 (nanobubble) and H2 (thermal expansion) effects on water density
        
        H1 Effect: Nanobubbles reduce effective water density
        H2 Effect: Thermal expansion affects water density
        """
        # Update parameters from simulation
        self.nanobubble_frac = params.get('nanobubble_frac', 0.0)
        self.thermal_expansion_coeff = params.get('thermal_coeff', 0.0001)
        self.water_temp = params.get('water_temp', 20.0)
        
        # H1 effect: reduce water density by nanobubble fraction
        rho_h1 = self.base_fluid_density * (1.0 - self.nanobubble_frac)
        
        # H2 effect: adjust density by temperature (thermal expansion)
        temp_delta = self.water_temp - self.ref_temp
        rho_h2 = rho_h1 * (1.0 - self.thermal_expansion_coeff * temp_delta)
        
        # Update current fluid density
        self.fluid_density = max(100.0, rho_h2)  # Ensure minimum density
        
        return self.fluid_density

    def update(self, dt, params, current_time=0.0):
        # Update H1/H2 effects first
        self.calculate_h1_h2_effects(params)
        
        # Update other properties from params if changed
        self.mass = params.get('floater_mass_empty', self.mass)
        self.volume = params.get('floater_volume', self.volume)
        self.area = params.get('floater_area', self.area)
        self.pulse_duration = params.get('air_fill_time', self.pulse_duration)
        self.air_pressure = params.get('air_pressure', self.air_pressure)
        self.air_flow_rate = params.get('air_flow_rate', self.air_flow_rate)
        
        # Update pulse progress
        if self.is_pulsing:
            elapsed_time = current_time - self.pulse_start_time
            self.fill_progress = min(1.0, elapsed_time / self.pulse_duration)
            
            if self.fill_progress >= 1.0:
                self.is_pulsing = False
                self.state = 'ascending'
        
        # Forces (now using updated fluid_density from H1/H2 effects)
        self.gravity = self.mass * self.g
        self.buoyancy = self.fluid_density * self.g * self.volume
        
        # Drag force: F_drag = 0.5 * ρ * v² * Cd * A (always opposes motion)
        # Fixed: velocity should be squared, and drag should be zero when velocity is zero
        if abs(self.velocity) > 0.001:  # Avoid division by zero
            self.drag = 0.5 * self.fluid_density * self.velocity * abs(self.velocity) * self.drag_coeff * self.area
        else:
            self.drag = 0.0
        
        # Add pulse force if pulsing
        self.pulse_force = self.calculate_pulse_forces() if self.is_pulsing else 0.0
        
        # Net force: upward positive
        self.net_force = self.buoyancy - self.gravity - self.drag + self.pulse_force
        self.force = self.net_force
        
        # Acceleration
        acceleration = self.net_force / self.mass
        
        # Update velocity and position with realistic limits
        self.velocity += acceleration * dt
        
        # Clamp velocity to realistic values (max 10 m/s for underwater movement)
        self.velocity = max(-10.0, min(10.0, self.velocity))
        
        self.position += self.velocity * dt
          # Clamp position and velocity to reasonable values
        if self.position < 0:
            self.position = 0
            self.velocity = max(0, self.velocity)  # Only allow upward velocity at bottom

    def to_dict(self):
        """Return floater state as dictionary for serialization"""
        return {
            'id': self.id,
            'position': self.position,
            'velocity': self.velocity,
            'state': self.state,
            'force': self.force,
            'mass': self.mass,
            'volume': self.volume,
            'area': self.area,
            'buoyancy': self.buoyancy,
            'gravity': self.gravity,
            'drag': self.drag,
            'net_force': self.net_force,
            'is_pulsing': self.is_pulsing,
            'pulse_force': self.pulse_force,
            'fill_progress': self.fill_progress,
            # H1/H2 effects
            'fluid_density': self.fluid_density,
            'nanobubble_frac': self.nanobubble_frac,
            'thermal_expansion_coeff': self.thermal_expansion_coeff,
            'water_temp': self.water_temp,
            # Simplified names for frontend compatibility
            'pos': self.position,
            'vel': self.velocity,
            'buoy': self.buoyancy
        }
