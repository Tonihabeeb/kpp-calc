import time
from simulation.floater import Floater

class RealTimeSimulationEngine:
    def __init__(self, params, data_queue):
        self.params = params
        self.data_queue = data_queue
        self.running = False
        self.floaters = [Floater(i, params) for i in range(params.get('num_floaters', 1))]
        self.time = 0.0
        self.dt = 0.1  # time step in seconds
        self.data_log = []

    def update_params(self, params):
        old_num = self.params.get('num_floaters', 1)
        new_num = params.get('num_floaters', old_num)
        self.params.update(params)
        # Recreate floaters if number changes, or update all floaters if other params change
        if new_num != old_num:
            self.floaters = [Floater(i, self.params) for i in range(new_num)]
        else:
            for floater in self.floaters:
                floater.mass = self.params.get('floater_mass_empty', 2.0)
                floater.volume = self.params.get('floater_volume', 0.04)
                floater.area = self.params.get('floater_area', 0.1)
                # Optionally reset other properties if needed

    def run(self):
        self.running = True
        while self.running:
            self.step(self.dt)
            time.sleep(self.dt)

    def stop(self):
        self.running = False

    def step(self, dt):
        for floater in self.floaters:
            floater.update(dt, self.params)
        # Calculate system-wide instantaneous values
        torque = sum(floater.force for floater in self.floaters)
        power = sum(floater.force * floater.velocity for floater in self.floaters)
        velocity = sum(floater.velocity for floater in self.floaters) / len(self.floaters) if self.floaters else 0
        # Integrate power and velocity for total energy and distance
        if not hasattr(self, 'total_energy'):
            self.total_energy = 0.0
        if not hasattr(self, 'total_distance'):
            self.total_distance = 0.0
        self.total_energy += power * dt  # Joules
        self.total_distance += velocity * dt  # meters
        state = self.collect_state()
        state['torque'] = torque
        state['power'] = power
        state['velocity'] = velocity
        state['total_energy'] = self.total_energy
        state['total_distance'] = self.total_distance
        self.data_log.append(state)
        self.data_queue.put(state)
        self.time += dt

    def collect_state(self):
        return {
            'time': self.time,
            'floaters': [f.to_dict() for f in self.floaters]
        }
