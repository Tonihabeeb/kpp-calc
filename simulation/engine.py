# SimulationEngine: orchestrates all simulation modules
# Coordinates state updates, manages simulation loop, and handles cross-module interactions
"""
Simulation engine class.
Coordinates all simulation components and manages the simulation loop.
"""

import time
import json
import threading
import logging
from simulation.components.floater import Floater
from simulation.components.drivetrain import Drivetrain
from simulation.components.generator import Generator
from simulation.components.environment import Environment
from simulation.components.pneumatics import PneumaticSystem
from simulation.components.control import Control
from simulation.components.sensors import Sensors
from simulation.pulse_physics import PulsePhysics
from utils.logging_setup import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

class SimulationEngine:
    """
    Main simulation engine for the KPP system.
    Orchestrates all components and manages simulation state and loop.
    """
    def __init__(self, params, data_queue):
        """
        Initialize the simulation engine and all components.

        Args:
            params (dict): Simulation parameters.
            data_queue (queue.Queue): Queue for streaming simulation data.
        """
        self.params = params
        self.data_queue = data_queue
        self.running = False
        self.environment = Environment(
            water_density=params.get('water_density', 1000.0),
            water_viscosity=params.get('water_viscosity', 1.0e-3),
            gravity=params.get('gravity', 9.81),
            nanobubble_enabled=params.get('nanobubble_enabled', False),
            density_reduction_factor=params.get('density_reduction_factor', 0.1),
            thermal_boost_enabled=params.get('thermal_boost_enabled', False),
            boost_factor=params.get('boost_factor', 0.1)
        )
        self.pneumatics = PneumaticSystem(
            tank_pressure=params.get('tank_pressure', 5.0),
            tank_volume=params.get('tank_volume', 0.1),
            compressor_power=params.get('compressor_power', 5.0),
            target_pressure=params.get('target_pressure', 5.0)
        )
        self.control = Control(self)
        self.sensors = Sensors(self)
        self.floaters = [
            Floater(
                volume=params.get('floater_volume', 0.3),
                mass=params.get('floater_mass_empty', 18.0),
                area=params.get('floater_area', 0.035),
                Cd=params.get('floater_Cd', 0.8)
            )
            for _ in range(params.get('num_floaters', 1))
        ]
        self.drivetrain = Drivetrain(params.get('gear_ratio', 1.0), params.get('drivetrain_efficiency', 1.0), params.get('sprocket_radius', 1.0))
        self.generator = Generator(params.get('generator_efficiency', 1.0))
        self.time = 0.0
        self.dt = 0.1  # time step in seconds
        self.data_log = []
        self.sse_clients = []
        self.total_energy = 0.0
        self.total_distance = 0.0
        self.pulse_count = 0
        self.thread = None
        self.last_pulse_time = 0.0
        self.pulse_physics = PulsePhysics(
            floater_mass=params.get('floater_mass_empty', 18.0),
            floater_volume=params.get('floater_volume', 0.3),
            floater_area=params.get('floater_area', 0.035),
            drag_coefficient=params.get('floater_Cd', 0.8),
            air_fill_time=params.get('air_fill_time', 0.5),
            air_pressure=params.get('air_pressure', 300000),
            air_flow_rate=params.get('air_flow_rate', 0.6),
            jet_efficiency=params.get('jet_efficiency', 0.85),
            sprocket_radius=params.get('sprocket_radius', 0.5),
            flywheel_inertia=params.get('flywheel_inertia', 50.0)
        )
        logger.info("SimulationEngine initialized with parameters: %s", params)

    def add_sse_client(self, client_generator):
        self.sse_clients.append(client_generator)
        logger.debug("Added SSE client. Total clients: %d", len(self.sse_clients))

    def remove_sse_client(self, client_generator):
        if client_generator in self.sse_clients:
            self.sse_clients.remove(client_generator)
            logger.debug("Removed SSE client. Total clients: %d", len(self.sse_clients))

    def send_sse_data(self, data):
        json_data = json.dumps(data)
        for client in self.sse_clients.copy():
            try:
                client.send(f"data: {json_data}\n\n")
            except Exception as e:
                logger.warning(f"SSE client send failed: {e}")
                self.sse_clients.remove(client)

    def update_params(self, params):
        """
        Update simulation parameters and reinitialize components if necessary.

        Args:
            params (dict): Dictionary of parameters to update.
        """
        self.params.update(params)
        self.floaters = [
            Floater(
                volume=self.params.get('floater_volume', 0.3),
                mass=self.params.get('floater_mass_empty', 18.0),
                area=self.params.get('floater_area', 0.035),
                Cd=self.params.get('floater_Cd', 0.8)
            )
            for _ in range(self.params.get('num_floaters', 1))
        ]
        self.drivetrain.update_params(self.params)
        self.generator.update_params(self.params)
        logger.info("Simulation parameters updated: %s", params)

    def trigger_pulse(self):
        """
        Trigger air injection pulse on the next available floater.

        Returns:
            bool: True if a pulse was triggered, False otherwise.
        """
        for floater in self.floaters:
            if not floater.is_filled:
                floater.set_filled(True)
                self.pulse_count += 1
                logger.info(f"Pulse triggered on floater. Pulse count: {self.pulse_count}")
                return True
        logger.info("No available floater for pulse trigger.")
        return False

    def reset_pulse_physics(self):
        self.pulse_physics.omega_chain = 0.0
        self.pulse_physics.omega_flywheel = 0.0
        self.pulse_physics.clutch_engaged = False
        logger.info("Pulse physics reset.")

    def run(self):
        """
        Start the simulation loop.
        """
        self.running = True
        logger.info("Simulation loop started.")
        while self.running:
            self.step(self.dt)
            time.sleep(self.dt)
        logger.info("Simulation loop stopped.")

    def stop(self):
        """
        Stop the simulation loop.
        """
        self.running = False
        logger.info("Simulation stopped.")

    def step(self, dt):
        """
        Perform a single simulation step.

        Args:
            dt (float): Time step (s).
        """
        if dt <= 0:
            logger.error("Time step dt must be positive.")
            raise ValueError("Time step dt must be positive.")
        # Pulse scheduling (migrated from engine_realtime)
        if self.time - self.last_pulse_time >= self.params.get('pulse_interval', 2.0):
            if self.trigger_pulse():
                self.last_pulse_time = self.time
        # Update all floaters
        for floater in self.floaters:
            floater.update(dt, self.params, self.time)
        # Calculate total forces and torques using PulsePhysics
        total_force = sum(floater.force for floater in self.floaters)
        pulse_forces = sum(getattr(floater, 'pulse_force', 0.0) for floater in self.floaters)
        base_torque = sum(abs(floater.force) for floater in self.floaters) * self.pulse_physics.r_sprocket
        pulse_torque = pulse_forces * self.pulse_physics.r_sprocket
        total_torque = base_torque + pulse_torque
        # Update flywheel and clutch dynamics
        self.pulse_physics.update_clutch_dynamics(total_torque, dt)
        flywheel_speed = self.pulse_physics.omega_flywheel
        chain_speed = self.pulse_physics.omega_chain
        # Generator load and power
        target_rpm = 375.0
        target_omega = target_rpm * (2 * 3.14159 / 60)
        target_power = 530000.0
        if flywheel_speed < 1.0:
            power_consumed = 0.0
        elif flywheel_speed < target_omega:
            speed_ratio = flywheel_speed / target_omega
            power_consumed = target_power * 0.2 * (speed_ratio ** 2)
        elif flywheel_speed <= target_omega * 1.2:
            power_consumed = target_power
        else:
            speed_ratio = flywheel_speed / target_omega
            power_consumed = target_power * min(3.0, 1.5 * speed_ratio)
        if flywheel_speed > 0.1:
            load_torque = power_consumed / flywheel_speed
            self.pulse_physics.omega_flywheel *= (1.0 - load_torque * dt * 0.001)
            self.pulse_physics.omega_flywheel = max(0.0, self.pulse_physics.omega_flywheel)
        power_output = power_consumed
        theoretical_max_power = max(1.0, total_torque * self.pulse_physics.omega_chain)
        efficiency = (power_output / theoretical_max_power * 100) if theoretical_max_power > 0 else 0.0
        efficiency = max(0.0, min(100.0, efficiency))
        velocity = sum(floater.velocity for floater in self.floaters) / len(self.floaters) if self.floaters else 0
        self.total_energy += power_output * dt
        self.total_distance += velocity * dt
        logger.debug(f"Step: t={self.time:.2f}, power={power_output:.2f}, torque={total_torque:.2f}, efficiency={efficiency:.2f}")
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
        self.time += dt

    def collect_state(self):
        """
        Collect the current simulation state.

        Returns:
            dict: Dictionary of the simulation state.
        """
        return {
            'time': self.time,
            'floaters': [floater.to_dict() for floater in self.floaters]
        }

    def start_thread(self):
        if not self.thread or not self.thread.is_alive():
            self.thread = threading.Thread(target=self.run, daemon=True)
            self.thread.start()
            logger.info("Simulation thread started.")
