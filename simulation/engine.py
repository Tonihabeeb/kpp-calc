from __future__ import annotations

import time
from typing import Dict, List

from .floater import Floater
from .pulse_physics import PulsePhysics
import config


class SimulationEngine:
    """Core simulation engine advancing all components in fixed time steps."""

    def __init__(self, params: Dict, data_queue):
        self.params = params
        self.data_queue = data_queue
        self.running = False
        self.dt = params.get('time_step', 0.1)
        self.total_time = params.get('total_time', 10.0)
        self.time = 0.0

        num_floaters = params.get('num_floaters', 1)
        self.floaters: List[Floater] = [Floater(i, params) for i in range(num_floaters)]

        self.pulse_physics = PulsePhysics(
            floater_mass=params.get('floater_mass_empty', 18.0),
            floater_volume=params.get('floater_volume', 0.3),
            air_fill_time=params.get('air_fill_time', 0.5),
            air_pressure=params.get('air_pressure', 300000),
            air_flow_rate=params.get('air_flow_rate', 0.6),
            sprocket_radius=params.get('sprocket_radius', 0.5),
            flywheel_inertia=params.get('flywheel_inertia', 50.0),
        )
        self.pulse_interval = params.get('pulse_interval', 2.0)
        self.last_pulse_time = 0.0

    def update_params(self, params: Dict) -> None:
        self.params.update(params)
        self.dt = self.params.get('time_step', self.dt)
        self.total_time = self.params.get('total_time', self.total_time)

    def trigger_pulse(self) -> bool:
        for floater in self.floaters:
            if not floater.is_pulsing and floater.state != 'pulsing':
                floater.start_pulse(self.time)
                return True
        return False

    def step(self, dt: float) -> Dict:
        if self.time - self.last_pulse_time >= self.pulse_interval:
            if self.trigger_pulse():
                self.last_pulse_time = self.time

        for floater in self.floaters:
            floater.update(dt, self.params, self.time)

        total_force = sum(f.force for f in self.floaters)
        base_torque = abs(total_force) * self.pulse_physics.r_sprocket
        pulse_torque = sum(f.pulse_force for f in self.floaters) * self.pulse_physics.r_sprocket
        total_torque = base_torque + pulse_torque

        self.pulse_physics.update_clutch_dynamics(total_torque, dt)
        power = self.pulse_physics.get_power_output()
        velocity = sum(f.velocity for f in self.floaters) / len(self.floaters)

        state = self.collect_state()
        state.update({'torque': total_torque, 'power': power, 'velocity': velocity,
                      'pulse_torque': pulse_torque, 'base_torque': base_torque,
                      'flywheel_speed': self.pulse_physics.omega_flywheel,
                      'chain_speed': self.pulse_physics.omega_chain,
                      'clutch_engaged': self.pulse_physics.clutch_engaged})
        self.data_queue.put(state)
        self.time += dt
        return state

    def run(self):
        self.running = True
        while self.running and self.time < self.total_time:
            self.step(self.dt)
            time.sleep(self.dt)

    def pause(self):
        self.running = False

    def collect_state(self) -> Dict:
        return {'time': self.time, 'floaters': [f.to_dict() for f in self.floaters]}
