import time
import json
from simulation.floater import Floater
from simulation.pulse_physics import PulsePhysics

class RealTimeSimulationEngine:
    def __init__(self, params, data_queue):
        self.params = params
        self.data_queue = data_queue
        self.running = False
        self.floaters = [Floater(i, params) for i in range(params.get('num_floaters', 1))]
        self.time = 0.0
        self.dt = 0.1  # time step in seconds
        self.data_log = []        # Initialize pulse physics
        self.pulse_physics = PulsePhysics(
            floater_mass=params.get('floater_mass_empty', 18.0),
            floater_volume=params.get('floater_volume', 0.3),
            air_fill_time=params.get('air_fill_time', 0.5),
            air_pressure=params.get('air_pressure', 300000),
            air_flow_rate=params.get('air_flow_rate', 0.6),
            sprocket_radius=params.get('sprocket_radius', 0.5),
            flywheel_inertia=params.get('flywheel_inertia', 50.0),
            # Realistic mechanical constraints
            max_chain_speed_rpm=30.0,        # 30 RPM max for large chains
            max_generator_rpm=400.0,         # 400 RPM max for 530kW generator  
            bearing_friction_coeff=0.02,     # 2% bearing friction (realistic)
            chain_friction_coeff=0.05,       # 5% chain friction (realistic)
            max_torque_capacity=20000.0      # 20,000 Nm torque limit (realistic)
        )
        
        # Pulse scheduling
        self.pulse_interval = params.get('pulse_interval', 2.0)  # seconds between pulses
        self.last_pulse_time = 0.0
        self.pulse_active = False
          # SSE stream data
        self.sse_clients = []
        # Advanced metrics
        self.total_energy = 0.0
        self.total_distance = 0.0
        self.pulse_count = 0

    def add_sse_client(self, client_generator):
        """Add SSE client for real-time streaming"""
        self.sse_clients.append(client_generator)
    
    def remove_sse_client(self, client_generator):
        """Remove SSE client"""
        if client_generator in self.sse_clients:
            self.sse_clients.remove(client_generator)

    def send_sse_data(self, data):
        """Send data to all SSE clients"""
        json_data = json.dumps(data)
        for client in self.sse_clients.copy():  # Copy to avoid modification during iteration
            try:
                client.send(f"data: {json_data}\n\n")
            except:
                # Remove disconnected clients
                self.sse_clients.remove(client)
    
    def update_params(self, params):
        # Validate and clamp parameters to realistic ranges
        validated_params = {}
        
        # Basic parameters validation
        validated_params['num_floaters'] = max(1, min(100, params.get('num_floaters', 8)))
        validated_params['floater_volume'] = max(0.01, min(10.0, params.get('floater_volume', 0.3)))
        validated_params['floater_mass_empty'] = max(0.1, min(1000.0, params.get('floater_mass_empty', 18.0)))
        validated_params['floater_area'] = max(0.001, min(10.0, params.get('floater_area', 0.035)))
        validated_params['airPressure'] = max(0.1, min(50.0, params.get('airPressure', 3.0)))
        
        # Pulse physics parameters validation
        validated_params['air_fill_time'] = max(0.1, min(5.0, params.get('air_fill_time', 0.5)))
        validated_params['air_pressure'] = max(100000, min(1000000, params.get('air_pressure', 300000)))
        validated_params['air_flow_rate'] = max(0.1, min(10.0, params.get('air_flow_rate', 0.6)))
        validated_params['jet_efficiency'] = max(0.1, min(1.0, params.get('jet_efficiency', 0.85)))
        validated_params['sprocket_radius'] = max(0.1, min(2.0, params.get('sprocket_radius', 0.5)))
        validated_params['flywheel_inertia'] = max(1.0, min(1000.0, params.get('flywheel_inertia', 50.0)))
        validated_params['pulse_interval'] = max(0.5, min(10.0, params.get('pulse_interval', 2.0)))
        validated_params['load_torque'] = max(0.0, min(10000.0, params.get('load_torque', 100.0)))
        
        # H1/H2 effect parameters validation
        validated_params['nanobubble_frac'] = max(0.0, min(1.0, params.get('nanobubble_frac', 0.0)))
        validated_params['thermal_coeff'] = max(0.0, min(0.01, params.get('thermal_coeff', 0.0001)))
        validated_params['water_temp'] = max(-10.0, min(100.0, params.get('water_temp', 20.0)))
        validated_params['ref_temp'] = max(-10.0, min(100.0, params.get('ref_temp', 20.0)))
        
        old_num = self.params.get('num_floaters', 1)
        new_num = validated_params['num_floaters']
        self.params.update(validated_params)        # Update pulse physics parameters
        self.pulse_physics = PulsePhysics(
            floater_mass=validated_params['floater_mass_empty'],
            floater_volume=validated_params['floater_volume'],
            air_fill_time=validated_params['air_fill_time'],
            air_pressure=validated_params['air_pressure'],
            air_flow_rate=validated_params['air_flow_rate'],
            sprocket_radius=params.get('sprocket_radius', 0.5),
            flywheel_inertia=params.get('flywheel_inertia', 50.0),
            # Realistic mechanical constraints
            max_chain_speed_rpm=30.0,        # 30 RPM max for large chains
            max_generator_rpm=400.0,         # 400 RPM max for 530kW generator  
            bearing_friction_coeff=0.02,     # 2% bearing friction (realistic)
            chain_friction_coeff=0.05,       # 5% chain friction (realistic)
            max_torque_capacity=20000.0      # 20,000 Nm torque limit (realistic)
        )
        
        self.pulse_interval = params.get('pulse_interval', 2.0)
        
        # Recreate floaters if number changes, or update all floaters if other params change
        if new_num != old_num:
            self.floaters = [Floater(i, self.params) for i in range(new_num)]
        else:
            for floater in self.floaters:
                floater.mass = self.params.get('floater_mass_empty', 2.0)
                floater.volume = self.params.get('floater_volume', 0.04)
                floater.area = self.params.get('floater_area', 0.1)
                floater.air_pressure = self.params.get('air_pressure', 300000)
                floater.air_flow_rate = self.params.get('air_flow_rate', 0.6)
                floater.mass = self.params.get('floater_mass_empty', 2.0)
                floater.volume = self.params.get('floater_volume', 0.04)
                floater.area = self.params.get('floater_area', 0.1)
                floater.air_pressure = self.params.get('air_pressure', 300000)
                floater.air_flow_rate = self.params.get('air_flow_rate', 0.6)

    def trigger_pulse(self):
        """Trigger air injection pulse on next available floater"""
        for floater in self.floaters:
            if not floater.is_pulsing and floater.state != 'pulsing':
                floater.start_pulse(self.time)
                self.pulse_count += 1
                return True
        return False

    def run(self):
        self.running = True
        while self.running:
            self.step(self.dt)
            time.sleep(self.dt)

    def stop(self):
        self.running = False

    def step(self, dt):
        # Check for pulse timing
        if self.time - self.last_pulse_time >= self.pulse_interval:
            if self.trigger_pulse():
                self.last_pulse_time = self.time
        
        # Update all floaters
        for floater in self.floaters:
            floater.update(dt, self.params, self.time)
        
        # Calculate total forces and torques
        total_force = sum(floater.force for floater in self.floaters)
        pulse_forces = sum(floater.pulse_force for floater in self.floaters)        # Calculate torques using pulse physics
        base_torque = sum(abs(floater.force) for floater in self.floaters) * self.pulse_physics.r_sprocket
        pulse_torque = pulse_forces * self.pulse_physics.r_sprocket
        total_torque = base_torque + pulse_torque
          # Update flywheel and clutch dynamics with generator load resistance
        self.pulse_physics.update_clutch_dynamics(total_torque, dt)
        
        # Get flywheel speed and apply realistic limits
        flywheel_speed = self.pulse_physics.omega_flywheel
        chain_speed = self.pulse_physics.omega_chain
        
        # Emergency speed limiting to prevent unrealistic values
        max_flywheel_speed = 100.0  # Max ~955 RPM (way above rated 375 RPM)
        max_chain_speed = 10.0      # Max ~95 RPM (way above target 20-25 RPM)
        
        if flywheel_speed > max_flywheel_speed:
            self.pulse_physics.omega_flywheel = max_flywheel_speed
            flywheel_speed = max_flywheel_speed
            
        if chain_speed > max_chain_speed:
            self.pulse_physics.omega_chain = max_chain_speed
            chain_speed = max_chain_speed
        
        # Calculate power consumption by 530kW generator with heat resistor load
        # This prevents power accumulation by modeling actual electrical load
        target_rpm = 375.0  # Generator rated RPM
        target_omega = target_rpm * (2 * 3.14159 / 60)  # 39.27 rad/s
        target_power = 530000.0  # 530 kW
        
        if flywheel_speed < 1.0:
            # No power generation at very low speeds
            power_consumed = 0.0
        elif flywheel_speed < target_omega:
            # Partial load generation (proportional to speed squared for realistic behavior)
            speed_ratio = flywheel_speed / target_omega
            power_consumed = target_power * 0.2 * (speed_ratio ** 2)
        elif flywheel_speed <= target_omega * 1.2:
            # Rated operation zone - consume rated power
            power_consumed = target_power  # Constant 530kW load
        else:
            # Over-speed protection - consume more power to limit speed
            speed_ratio = flywheel_speed / target_omega
            power_consumed = target_power * min(3.0, 1.5 * speed_ratio)  # Cap at 1.59MW max
        
        # Apply load torque back to the flywheel to consume energy
        if flywheel_speed > 0.1:
            load_torque = power_consumed / flywheel_speed
            # Apply braking torque to slow down the flywheel
            self.pulse_physics.omega_flywheel *= (1.0 - load_torque * dt * 0.001)
            self.pulse_physics.omega_flywheel = max(0.0, self.pulse_physics.omega_flywheel)
        
        # Power output is the power consumed by the generator (converted to heat)
        power_output = power_consumed
        
        # Calculate efficiency (power output / theoretical max power)
        theoretical_max_power = max(1.0, total_torque * self.pulse_physics.omega_chain)
        efficiency = (power_output / theoretical_max_power * 100) if theoretical_max_power > 0 else 0.0
        efficiency = max(0.0, min(100.0, efficiency))  # Clamp to 0-100%
        
        # Average velocity
        velocity = sum(floater.velocity for floater in self.floaters) / len(self.floaters) if self.floaters else 0
        
        # Integration for totals
        self.total_energy += power_output * dt  # Joules
        self.total_distance += velocity * dt  # meters
          # Collect state
        state = self.collect_state()
        state.update({
            'torque': total_torque,
            'power': power_output,
            'efficiency': efficiency,
            'velocity': velocity,
            'total_energy': self.total_energy,
            'total_distance': self.total_distance,
            'pulse_torque': pulse_torque,
            'base_torque': base_torque,
            'pulse_count': self.pulse_count,
            'flywheel_speed': self.pulse_physics.omega_flywheel,
            'chain_speed': self.pulse_physics.omega_chain,
            'clutch_engaged': self.pulse_physics.clutch_engaged
        })
        
        self.data_log.append(state)
        self.data_queue.put(state)
        
        # Send to SSE clients
        self.send_sse_data(state)
        
        self.time += dt

    def collect_state(self):
        return {
            'time': self.time,
            'floaters': [f.to_dict() for f in self.floaters]
        }
