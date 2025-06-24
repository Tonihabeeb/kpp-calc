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
import math
from simulation.components.floater import Floater
from simulation.components.drivetrain import Drivetrain
from simulation.components.generator import Generator
from simulation.components.environment import Environment
from simulation.components.pneumatics import PneumaticSystem
from simulation.components.control import Control
from simulation.components.sensors import Sensors
from simulation.components.clutch import OverrunningClutch
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
                air_fill_time=params.get('air_fill_time', 0.5),
                added_mass=params.get('floater_added_mass', 5.0),
                phase_offset=2*math.pi*i/params.get('num_floaters',1)
            )
            for i in range(params.get('num_floaters', 1))
        ]
        
        self.control = Control(self)
        self.sensors = Sensors(self)
        self.clutch = OverrunningClutch(
            tau_eng=params.get('clutch_tau_eng', 200),
            slip_time=params.get('clutch_slip_time', 0.2),
            w_min=params.get('clutch_w_min', 5),
            w_max=params.get('clutch_w_max', 40)
        )
        
        self.data_log = []
        self.total_energy = 0.0
        self.pulse_count = 0
        self.thread = None
        logger.info("SimulationEngine initialized with modular components.")
        # Initialize default chain geometry for torque calculations
        self.set_chain_geometry()

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
        # Force an initial pulse at t=0 to kick off the system
        if self.time == 0.0:
            logger.info("Forcing initial pulse at t=0.0")
            self.trigger_pulse()
        while self.running:
            logger.debug(f"Step start: t={self.time:.2f}")
            for i, floater in enumerate(self.floaters):
                logger.debug(f"Floater {i}: theta={getattr(floater, 'theta', 0.0):.2f}, filled={getattr(floater, 'is_filled', False)}, pos={floater.get_cartesian_position() if hasattr(floater, 'get_cartesian_position') else 'N/A'}")
            logger.debug(f"Drivetrain: omega_chain={getattr(self.drivetrain, 'omega_chain', 0.0):.2f}, omega_flywheel={getattr(self.drivetrain, 'omega_flywheel', 0.0):.2f}, clutch_engaged={getattr(self.drivetrain, 'clutch_engaged', False)}")
            logger.debug(f"Generator: target_omega={getattr(self.generator, 'target_omega', 0.0):.2f}, target_power={getattr(self.generator, 'target_power', 0.0):.2f}")
            self.step(self.dt)
            time.sleep(self.dt)
        logger.info("Simulation loop stopped.")

    def stop(self):
        self.running = False
        logger.info("Simulation stopped.")

    def set_chain_geometry(self, major_axis=5.0, minor_axis=10.0):
        """
        Set the geometry of the elliptical/circular chain and initialize floaters' theta.
        """
        self.chain_major_axis = major_axis
        self.chain_minor_axis = minor_axis
        self.chain_radius = (major_axis + minor_axis) / 2  # Approximate mean radius
        n = len(self.floaters)
        for i, floater in enumerate(self.floaters):
            floater.set_chain_params(major_axis, minor_axis, self.chain_radius)
            floater.set_theta(2 * math.pi * i / n)

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

        # 2a. Update chain kinematics: advance all floaters' theta
        omega_chain = self.drivetrain.omega_chain
        for floater in self.floaters:
            prev_theta = getattr(floater, 'theta', 0.0)
            floater.set_theta(prev_theta + omega_chain * dt)
            # If floater completes a revolution, vent and reset
            # Detect top sprocket crossing (180° pivot)
            if prev_theta % (2*math.pi) < math.pi and floater.theta % (2*math.pi) >= math.pi:
                floater.pivot()

            # Detect bottom sprocket crossing (360° pivot + water drainage)
            if prev_theta < 2 * math.pi and floater.theta >= 2 * math.pi:
                floater.pivot()
                floater.drain_water()
                floater.is_filled = False
                floater.fill_progress = 0.0
                # Trigger air injection after drainage
                self.pneumatics.trigger_injection(floater)
            floater.update(dt)

        # After kinematics update, track energy losses
        drag_loss_sum = sum(f.drag_loss for f in self.floaters)
        dissolution_loss_sum = sum(f.dissolution_loss for f in self.floaters)
        venting_loss_sum = sum(f.venting_loss for f in self.floaters)

        # 3. Calculate net torque from all floaters (vertical force × chain radius at each theta)
        total_chain_torque = 0.0
        base_buoy_torque = 0.0
        pulse_torque = 0.0
        for i, floater in enumerate(self.floaters):
            x, y = floater.get_cartesian_position()
            vertical_force = floater.get_vertical_force()
            # Log per-floater forces
            logger.debug(f"Floater {i}: x={x:.2f}, y={y:.2f}, vertical_force={vertical_force:.2f}, is_filled={floater.is_filled}, fill_progress={floater.fill_progress:.2f}, state={getattr(floater, 'state', 'N/A')}")
            # Torque contributions use horizontal lever arm x for ripple smoothing
            buoy_force = floater.compute_buoyant_force()
            base_buoy_torque += buoy_force * x
            # Pulse torque using lever arm x
            jet_force = floater.compute_pulse_jet_force()
            if abs(jet_force) > 1e-3:
                pulse_torque += jet_force * x
            # Total chain torque from vertical force and lever arm x
            total_chain_torque += vertical_force * x
        # Combine all torque components and apply drivetrain efficiency
        raw_torque = total_chain_torque + pulse_torque
        input_torque = raw_torque * self.drivetrain.efficiency
        logger.info(f"Torque breakdown: base_buoy_torque={base_buoy_torque:.2f}, pulse_torque={pulse_torque:.2f}, total_chain_torque={total_chain_torque:.2f}")

        # 4. Get generator load based on drivetrain speed
        flywheel_speed_rad_s = self.drivetrain.omega_flywheel
        load_torque = self.generator.get_load_torque(flywheel_speed_rad_s)

        # 5. Update drivetrain dynamics with input and load torques
        self.drivetrain.update_dynamics(input_torque, load_torque, dt)

        # --- Clutch logic integration ---
        # Calculate net torque available to the shaft
        tau_net = input_torque - load_torque  # - friction if modeled
        omega = self.drivetrain.omega_flywheel
        c = self.clutch.update(tau_net, omega, dt)
        tau_to_generator = c * tau_net
        # Update shaft speed with clutch effect (simplified, add friction if needed)
        # For now, update drivetrain with tau_to_generator as the load
        self.drivetrain.update_dynamics(tau_to_generator, load_torque, dt)
        # Log clutch state
        logger.info(f"Clutch: state={self.clutch.state.state}, c={self.clutch.state.c:.2f}, tau_net={tau_net:.2f}, tau_to_generator={tau_to_generator:.2f}, omega={omega:.2f}")

        # 6. Calculate power output
        power_output = self.generator.calculate_power_output(flywheel_speed_rad_s)
        self.total_energy += power_output * dt
        # 7. Track energy losses
        # Capture clutch state for logging
        clutch_state_val = self.clutch.state.state
        drag_loss_sum = sum(f.drag_loss for f in self.floaters)
        dissolution_loss_sum = sum(f.dissolution_loss for f in self.floaters)
        venting_loss_sum = sum(f.venting_loss for f in self.floaters)

        # Compute net energy balance
        net_energy_balance = power_output - (drag_loss_sum + dissolution_loss_sum + venting_loss_sum)
        self.log_state(
            power_output,
            input_torque,
            base_buoy_torque=base_buoy_torque,
            pulse_torque=pulse_torque,
            total_chain_torque=total_chain_torque,
            tau_net=tau_net,
            tau_to_generator=tau_to_generator,
            clutch_c=c,
            clutch_state=clutch_state_val,
            drag_loss=drag_loss_sum,
            dissolution_loss=dissolution_loss_sum,
            venting_loss=venting_loss_sum,
            net_energy=net_energy_balance
        )
        # 7. Collect and log data
        self.time += dt

    def log_state(self, power_output, torque, base_buoy_torque=None, pulse_torque=None, total_chain_torque=None, tau_net=None, tau_to_generator=None, clutch_c=None, clutch_state=None, drag_loss=None, dissolution_loss=None, venting_loss=None, net_energy=None):
        """
        Collect and log the current state of the simulation, including torque breakdowns and clutch state.
        """
        print(f"LOG_STATE: t={self.time:.2f}, power={power_output:.2f}, torque={torque:.2f}, base_buoy_torque={base_buoy_torque}, pulse_torque={pulse_torque}, clutch_c={clutch_c}, clutch_state={clutch_state}, drag_loss={drag_loss}, dissolution_loss={dissolution_loss}, venting_loss={venting_loss}, net_energy={net_energy}")
        drivetrain_state = self.drivetrain.get_state()
        # Compute overall mechanical efficiency (output electrical power / mechanical input power)
        omega_fly = drivetrain_state['omega_flywheel_rpm'] * (2 * math.pi / 60)
        if torque and omega_fly:
            overall_eff = power_output / (torque * omega_fly)
        else:
            overall_eff = 0.0
        # Compute average floater velocity
        if self.floaters:
            avg_velocity = sum(abs(f.velocity) for f in self.floaters) / len(self.floaters)
        else:
            avg_velocity = 0.0
        state = {
            'time': self.time,
            'power': power_output,
            'torque': torque,
            'base_buoy_torque': base_buoy_torque,
            'pulse_torque': pulse_torque,
            'total_chain_torque': total_chain_torque,
            'tau_net': tau_net,
            'tau_to_generator': tau_to_generator,
            'clutch_c': clutch_c,
            'clutch_state': clutch_state,
            'total_energy': self.total_energy,
            'pulse_count': self.pulse_count,
            'flywheel_speed_rpm': drivetrain_state['omega_flywheel_rpm'],
            'chain_speed_rpm': drivetrain_state['omega_chain_rpm'],
            'clutch_engaged': drivetrain_state['clutch_engaged'],
            'tank_pressure': self.pneumatics.tank_pressure,
            'overall_efficiency': overall_eff,
            'avg_floater_velocity': avg_velocity,
            'floaters': [f.to_dict() for f in self.floaters]
        }
        # Include energy loss and net energy data
        state['drag_loss'] = drag_loss
        state['dissolution_loss'] = dissolution_loss
        state['venting_loss'] = venting_loss
        state['net_energy'] = net_energy
        self.data_log.append(state)
        self.data_queue.put(state)
        logger.debug(f"Step: t={self.time:.2f}, power={power_output:.2f}, torque={torque:.2f}, base_buoy_torque={base_buoy_torque}, pulse_torque={pulse_torque}, clutch_c={clutch_c}, clutch_state={clutch_state}")

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

    def reset(self):
        """
        Resets the entire simulation to its initial state.
        """
        self.time = 0.0
        self.total_energy = 0.0
        self.pulse_count = 0
        self.last_pulse_time = -999
        self.data_log.clear()

        self.drivetrain.reset()
        self.generator.reset()
        self.pneumatics.reset()
        for i, floater in enumerate(self.floaters):
            floater.reset()
            # Set the first floater unfilled at the bottom to kickstart the cycle
            if i == 0:
                floater.is_filled = False
                floater.fill_progress = 0.0
                floater.set_theta(0.0)
            else:
                floater.is_filled = True
                floater.fill_progress = 1.0
                floater.set_theta(2 * math.pi * i / len(self.floaters))
        # Set chain geometry and trigger a pulse for the first floater
        self.set_chain_geometry()
        # --- Calibrated startup: set floaters for continuous movement ---
        n = len(self.floaters)
        for i, floater in enumerate(self.floaters):
            floater.set_theta(2 * math.pi * i / n)
            x, y = floater.get_cartesian_position()
            if y > 0:
                floater.is_filled = True
                floater.fill_progress = 1.0
                floater.state = 'FILLED'
            else:
                floater.is_filled = False
                floater.fill_progress = 0.0
                floater.state = 'EMPTY'
        # Ensure one floater at injection is ready to fill (simulate injection point at theta=0)
        self.floaters[0].set_theta(0.0)
        self.floaters[0].is_filled = True
        self.floaters[0].fill_progress = 0.0
        self.floaters[0].state = 'FILLING'
        logger.info("Floaters initialized for calibrated startup: ascending side buoyant, descending side drawing, one ready for injection.")
        self.pneumatics.trigger_injection(self.floaters[0])
        with self.data_queue.mutex:
            self.data_queue.queue.clear()
        logger.info("Simulation engine has been reset.")
        # Debug: Log initial floater states after calibrated placement
        for i, floater in enumerate(self.floaters):
            x, y = floater.get_cartesian_position()
            logger.debug(f"Floater {i}: theta={floater.theta:.2f}, x={x:.2f}, y={y:.2f}, is_filled={floater.is_filled}, fill_progress={floater.fill_progress:.2f}, state={floater.state}")
