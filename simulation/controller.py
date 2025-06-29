"""
SimulatorController: Orchestrates the simulation loop and module interactions.
Implements the architecture described in guideprestagegap.md.
"""

import logging

from simulation.components.control import Control
from simulation.components.drivetrain import Drivetrain
from simulation.components.environment import Environment
from simulation.components.floater import Floater
from simulation.components.pneumatics import PneumaticSystem
from simulation.components.position_sensor import PositionSensor
from simulation.components.sensors import Sensors
from simulation.hypotheses.h1_nanobubbles import H1Nanobubbles
from simulation.hypotheses.h2_isothermal import H2Isothermal
from simulation.hypotheses.h3_pulse_mode import H3PulseMode
from simulation.plotting import PlottingUtility
from utils.errors import ControlError, PhysicsError, SimulationError
from utils.logging_setup import setup_logging

setup_logging()
logger = logging.getLogger(__name__)


class SimulatorController:
    """
    Main simulation controller. Manages all components and the simulation loop.
    Implements dependency injection, logging, and error handling as described in the guide.
    """

    def __init__(self, params: dict):
        self.params = params
        self.environment = Environment(
            water_density=params.get("water_density", 1000.0),
            nanobubble_enabled=params.get("nanobubble_frac", 0.0) > 0.0,
            density_reduction_factor=params.get("nanobubble_frac", 0.0),
            thermal_boost_enabled=params.get("thermal_coeff", 0.0) > 0.0,
            boost_factor=params.get("thermal_coeff", 0.0),
        )
        self.floaters = [
            Floater(
                volume=params.get("floater_volume", 0.3),
                mass=params.get("floater_mass_empty", 18.0),
                area=params.get("floater_area", 0.035),
                drag_coefficient=params.get("drag_coefficient", 0.8),
                position=(
                    i * params.get("water_depth", 10.0) / params.get("num_floaters", 8)
                )
                % params.get("water_depth", 10.0),
            )
            for i in range(params.get("num_floaters", 8))
        ]
        self.drivetrain = Drivetrain(
            gear_ratio=params.get("gear_ratio", 1.0),
            efficiency=params.get("drivetrain_efficiency", 1.0),
            sprocket_radius=params.get("sprocket_radius", 0.5),
        )
        self.pneumatic = PneumaticSystem(
            tank_pressure=params.get("air_pressure", 3.0),
            tank_volume=params.get("tank_volume", 0.1),
            compressor_power=params.get("compressor_power", 5.0),
            target_pressure=params.get("air_pressure", 3.0),
        )
        self.sensors = Sensors()
        water_depth = params.get("water_depth", 10.0)
        self.top_sensor = PositionSensor(
            position_threshold=water_depth, trigger_when="above"
        )
        self.bottom_sensor = PositionSensor(
            position_threshold=0.0, trigger_when="below"
        )
        # Pass drivetrain and control params to Control
        self.control = Control(
            floaters=self.floaters,
            pneumatic=self.pneumatic,
            sensors=self.sensors,
            top_sensor=self.top_sensor,
            bottom_sensor=self.bottom_sensor,
            drivetrain=self.drivetrain,
            target_rpm=params.get("target_rpm", 20.0),
            Kp=params.get("Kp", 1.0),
            Ki=params.get("Ki", 0.0),
            Kd=params.get("Kd", 0.0),
            use_clutch=params.get("use_clutch", False),
            T_eng=params.get("T_eng", 2.0),
            T_free=params.get("T_free", 2.0),
        )
        self.h1 = H1Nanobubbles()
        self.h2 = H2Isothermal()
        self.h3 = H3PulseMode()
        self.current_time = 0.0
        self.results_log = []
        self.plotting_utility = PlottingUtility()
        logger.info("SimulatorController initialized.")

    def step(self, dt: float):
        """
        Advance the simulation by one time step (dt seconds).
        """
        try:
            # Closed-loop control: let Control decide actuator actions
            self.control.update(dt)
            for floater in self.floaters:
                floater.update(dt)
            # Compute net forces from floaters for drivetrain
            forces = []
            for floater in self.floaters:
                # Calculate net upward force for torque calculation
                rho = self.environment.get_density(floater)
                buoyant = rho * floater.volume * self.environment.gravity
                weight = floater.mass * self.environment.gravity
                net_upward = buoyant - weight
                forces.append(net_upward)
            # Use Drivetrain.compute_input_torque instead of compute_torque
            torque = self.drivetrain.compute_input_torque(sum(forces))
            # Update power (derive angular speed from floater velocity)
            avg_velocity = sum(f.velocity for f in self.floaters) / len(self.floaters)
            angular_speed = (
                avg_velocity / self.drivetrain.sprocket_radius
                if self.drivetrain.sprocket_radius
                else 0.0
            )
            # Log results for this step
            self.current_time += dt
            self.results_log.append(
                {
                    "time": self.current_time,
                    "torque": torque,
                    "power": torque * angular_speed,
                    "efficiency": self.compute_efficiency(torque * angular_speed),
                }
            )
        except Exception as e:
            logger.error(f"Exception in simulation step: {e}")
            raise SimulationError(str(e))

    def simulate(self, total_time: float, dt: float):
        """
        Run the simulation loop from t=0 to t=total_time (seconds).
        """
        self.current_time = 0.0
        self.results_log.clear()
        try:
            while self.current_time < total_time:
                self.step(dt)

            # Generate and save plots after simulation
            time_series_data = {
                "time": [entry["time"] for entry in self.results_log],
                "torque": [entry["torque"] for entry in self.results_log],
                "power": [entry["power"] for entry in self.results_log],
                "efficiency": [entry["efficiency"] for entry in self.results_log],
            }

            self.plotting_utility.plot_time_series(
                data=time_series_data,
                title="Simulation Results: Torque vs Time",
                xlabel="Time (s)",
                ylabel="Torque (Nm)",
                filename="torque_vs_time.png",
            )

            self.plotting_utility.plot_time_series(
                data=time_series_data,
                title="Simulation Results: Power vs Time",
                xlabel="Time (s)",
                ylabel="Power (W)",
                filename="power_vs_time.png",
            )

            self.plotting_utility.plot_time_series(
                data=time_series_data,
                title="Simulation Results: Efficiency vs Time",
                xlabel="Time (s)",
                ylabel="Efficiency (%)",
                filename="efficiency_vs_time.png",
            )

            return self.results_log
        except Exception as e:
            logger.error(f"Simulation aborted at t={self.current_time:.2f}s: {e}")
            raise

    def compute_efficiency(self, power_output: float) -> float:
        """
        Compute instantaneous efficiency (output power vs input power).
        """
        compressor_power = self.pneumatic.compressor_power
        if (power_output + compressor_power) == 0:
            return 0.0
        return power_output / (power_output + compressor_power)
