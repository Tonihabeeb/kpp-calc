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
        self.drag_coeff = 0.5  # Example drag coefficient
        self.fluid_density = 1000  # Water, kg/m^3
        self.g = 9.81
        self.buoyancy = 0.0
        self.gravity = 0.0
        self.drag = 0.0
        self.net_force = 0.0

    def update(self, dt, params):
        # Update properties from params if changed
        self.mass = params.get('floater_mass_empty', self.mass)
        self.volume = params.get('floater_volume', self.volume)
        self.area = params.get('floater_area', self.area)
        # Forces
        self.gravity = self.mass * self.g
        self.buoyancy = self.fluid_density * self.g * self.volume
        self.drag = 0.5 * self.fluid_density * self.velocity**2 * self.drag_coeff * (1 if self.velocity >= 0 else -1) * self.area
        self.net_force = self.buoyancy - self.gravity - self.drag
        self.force = self.net_force
        # Acceleration
        acceleration = self.net_force / self.mass
        # Update velocity and position
        self.velocity += acceleration * dt
        self.position += self.velocity * dt
        # Optionally, add floor/ceiling or state logic

    def to_dict(self):
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
            'net_force': self.net_force
        }
