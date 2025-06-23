"""Simulation engine class (stub)."""

import time
import json
from simulation.components.floater import Floater
from simulation.components.drivetrain import Drivetrain
from simulation.components.generator import Generator

class SimulationEngine:
    def __init__(self, params, data_queue):
        self.params = params
        self.data_queue = data_queue
        self.running = False
        self.floaters = [
            Floater(
                volume=params.get('floater_volume', 0.3),
                mass=params.get('floater_mass_empty', 18.0),
                area=params.get('floater_area', 0.035),
                Cd=params.get('floater_Cd', 0.8)
            )
            for _ in range(params.get('num_floaters', 1))
        ]
        self.drivetrain = Drivetrain(params)
        self.generator = Generator(params)
        self.time = 0.0
        self.dt = 0.1  # time step in seconds
        self.data_log = []
        self.sse_clients = []
        self.total_energy = 0.0
        self.total_distance = 0.0
        self.pulse_count = 0

    def add_sse_client(self, client_generator):
        self.sse_clients.append(client_generator)

    def remove_sse_client(self, client_generator):
        if client_generator in self.sse_clients:
            self.sse_clients.remove(client_generator)

    def send_sse_data(self, data):
        json_data = json.dumps(data)
        for client in self.sse_clients.copy():
            try:
                client.send(f"data: {json_data}\n\n")
            except:
                self.sse_clients.remove(client)

    def update_params(self, params):
        """
        Update simulation parameters and reinitialize components if necessary.
        :param params: Dictionary of parameters to update.
        """
        self.params.update(params)
        self.floaters = [
            Floater(
                volume=params.get('floater_volume', 0.3),
                mass=params.get('floater_mass_empty', 18.0),
                area=params.get('floater_area', 0.035),
                Cd=params.get('floater_Cd', 0.8)
            )
            for _ in range(params.get('num_floaters', 1))
        ]
        self.drivetrain.update_params(params)
        self.generator.update_params(params)

    def trigger_pulse(self):
        """
        Trigger air injection pulse on the next available floater.
        :return: True if a pulse was triggered, False otherwise.
        """
        for floater in self.floaters:
            if not floater.is_filled:
                floater.is_filled = True
                self.pulse_count += 1
                return True
        return False

    def run(self):
        """
        Start the simulation loop.
        """
        self.running = True
        while self.running:
            self.step(self.dt)
            time.sleep(self.dt)

    def stop(self):
        """
        Stop the simulation loop.
        """
        self.running = False

    def step(self, dt):
        """
        Perform a single simulation step.
        :param dt: Time step (s).
        """
        for floater in self.floaters:
            floater.update(dt, self.params, self.time)

        total_force = sum(floater.force for floater in self.floaters)
        torque = self.drivetrain.calculate_torque(total_force)
        angular_speed = self.drivetrain.gear_ratio * self.drivetrain.sprocket_radius
        power = self.generator.calculate_power(torque, angular_speed)

        self.total_energy += power * dt
        self.total_distance += sum(floater.velocity for floater in self.floaters) * dt

        state = self.collect_state()
        state.update({
            'torque': torque,
            'power': power,
            'total_energy': self.total_energy,
            'total_distance': self.total_distance
        })

        self.data_log.append(state)
        self.data_queue.put(state)

        self.time += dt

    def collect_state(self):
        """
        Collect the current simulation state.
        :return: Dictionary of the simulation state.
        """
        return {
            'time': self.time,
            'floaters': [floater.to_dict() for floater in self.floaters]
        }
