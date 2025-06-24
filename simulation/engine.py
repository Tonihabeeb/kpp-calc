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
        self.time = 0.0
        self.dt = params.get('time_step', 0.1)
        self.last_pulse_time = -999 # Allow immediate first pulse

        self.environment = Environment()
        self.pneumatics = PneumaticSystem(
            target_pressure=params.get('target_pressure', 5.0)
        )
        self.drivetrain = Drivetrain(
            gear_ratio=params.get('gear_ratio', 16.7),
            efficiency=params.get('drivetrain_efficiency', 0.95),
            sprocket_radius=params.get('sprocket_radius', 0.5),
            flywheel_inertia=params.get('flywheel_inertia', 50.0)
        )
        self.generator = Generator(
            efficiency=params.get('generator_efficiency', 0.92),
            target_power=params.get('target_power', 530000.0),
            target_rpm=params.get('target_rpm', 375.0)
        )
        self.floaters = [
            Floater(
                volume=params.get('floater_volume', 0.3),
                mass=params.get('floater_mass_empty', 18.0),
                area=params.get('floater_area', 0.035),
                Cd=params.get('floater_Cd', 0.8),
                air_fill_time=params.get('air_fill_time', 0.5)
            )
            for _ in range(params.get('num_floaters', 1))
        ]
        
        self.control = Control(self)
        self.sensors = Sensors(self)
        
        self.data_log = []
        self.total_energy = 0.0
        self.pulse_count = 0
        self.thread = None
        logger.info("SimulationEngine initialized with modular components.")

    def update_params(self, params):
        """
        Update simulation parameters and component parameters.
        """
        self.params.update(params)
        self.drivetrain.update_params(self.params)
        self.generator.update_params(self.params)
        
        # Update existing floaters instead of recreating them
        for floater in self.floaters:
            floater.volume = self.params.get('floater_volume', floater.volume)
            floater.mass = self.params.get('floater_mass_empty', floater.mass)
            floater.area = self.params.get('floater_area', floater.area)
            floater.Cd = self.params.get('floater_Cd', floater.Cd)
            floater.air_fill_time = self.params.get('air_fill_time', floater.air_fill_time)

        logger.info("Simulation parameters updated.")

    def trigger_pulse(self):
        """
        Trigger air injection pulse on the next available floater via the pneumatic system.
        """
        for floater in self.floaters:
            if not floater.is_filled and floater.fill_progress == 0.0:
                if self.pneumatics.trigger_injection(floater):
                    self.pulse_count += 1
                    logger.info(f"Pulse triggered on a floater. Total pulses: {self.pulse_count}")
                    return True
        logger.info("No available floater or insufficient pressure for pulse trigger.")
        return False

    def run(self):
        self.running = True
        logger.info("Simulation loop started.")
        while self.running:
            self.step(self.dt)
            time.sleep(self.dt)
        logger.info("Simulation loop stopped.")

    def stop(self):
        self.running = False
        logger.info("Simulation stopped.")

    def step(self, dt):
        """
        Perform a single simulation step using the modular components.
        """
        if dt <= 0:
            raise ValueError("Time step dt must be positive.")

        # 1. Check for pulse trigger
        if self.time - self.last_pulse_time >= self.params.get('pulse_interval', 2.0):
            if self.trigger_pulse():
                self.last_pulse_time = self.time

        # 2. Update component states
        self.pneumatics.update(dt)
        for floater in self.floaters:
            floater.update(dt)

        # 3. Calculate forces and torques
        total_chain_force = sum(f.force for f in self.floaters)
        input_torque = self.drivetrain.compute_input_torque(total_chain_force)

        # 4. Get generator load based on drivetrain speed
        flywheel_speed_rad_s = self.drivetrain.omega_flywheel
        load_torque = self.generator.get_load_torque(flywheel_speed_rad_s)

        # 5. Update drivetrain dynamics with input and load torques
        self.drivetrain.update_dynamics(input_torque, load_torque, dt)

        # 6. Calculate power output
        power_output = self.generator.calculate_power_output(flywheel_speed_rad_s)
        self.total_energy += power_output * dt

        # 7. Collect and log data
        self.log_state(power_output, input_torque)
        self.time += dt

    def log_state(self, power_output, torque):
        """
        Collect and log the current state of the simulation.
        """
        drivetrain_state = self.drivetrain.get_state()
        state = {
            'time': self.time,
            'power': power_output,
            'torque': torque,
            'total_energy': self.total_energy,
            'pulse_count': self.pulse_count,
            'flywheel_speed_rpm': drivetrain_state['omega_flywheel_rpm'],
            'chain_speed_rpm': drivetrain_state['omega_chain_rpm'],
            'clutch_engaged': drivetrain_state['clutch_engaged'],
            'tank_pressure': self.pneumatics.tank_pressure,
            'floaters': [f.to_dict() for f in self.floaters]
        }
        self.data_log.append(state)
        self.data_queue.put(state)
        logger.debug(f"Step: t={self.time:.2f}, power={power_output:.2f}, torque={torque:.2f}")

    def collect_state(self):
        """
        Return the latest simulation state.
        """
        if not self.data_log:
            return {}
        return self.data_log[-1]

    def start_thread(self):
        if not self.thread or not self.thread.is_alive():
            self.thread = threading.Thread(target=self.run, daemon=True)
            self.thread.start()
            logger.info("Simulation thread started.")
