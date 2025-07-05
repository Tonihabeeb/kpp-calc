"""
Control system module.
Coordinates high-level control logic for the KPP simulator (stub for future expansion).
"""

# High-level control logic for the simulation (stub, ready for extension)
# Manages control strategies and system-level decisions

import logging

from utils.logging_setup import setup_logging

setup_logging()
logger = logging.getLogger(__name__)


class Control:
    """
    Control system for the KPP simulator.
    Monitors and coordinates actions between subsystems (now with rule-based closed-loop logic).
    """

    def __init__(
        self,
        simulation=None,
        floaters=None,
        pneumatic=None,
        sensors=None,
        top_sensor=None,
        bottom_sensor=None,
        drivetrain=None,
        target_rpm=20.0,
        Kp=1.0,
        Ki=0.0,
        Kd=0.0,
        use_clutch=False,
        T_eng=2.0,
        T_free=2.0,
    ):
        """
        Initialize the control system.

        Args:
            simulation: Reference to the Simulation object (optional).
            floaters: List of Floater objects.
            pneumatic: PneumaticSystem object.
            sensors: Sensors manager object.
            top_sensor: PositionSensor for top position.
            bottom_sensor: PositionSensor for bottom position.
        """
        self.simulation = simulation
        self.floaters = floaters
        self.pneumatic = pneumatic
        self.sensors = sensors
        self.top_sensor = top_sensor
        self.bottom_sensor = bottom_sensor
        self.drivetrain = drivetrain
        self.target_rpm = target_rpm
        self.Kp = Kp
        self.Ki = Ki
        self.Kd = Kd
        self.prev_error = 0.0
        self.int_error = 0.0
        self.use_clutch = use_clutch
        self.T_eng = T_eng
        self.T_free = T_free
        logger.info("Control system initialized.")

    def update(self, dt: float) -> None:
        """
        Update control logic (full closed-loop FSM, PID, clutch, compressor).

        Args:
            dt (float): Time step (s).
        """
        if (
            not self.floaters
            or not self.pneumatic
            or not self.top_sensor
            or not self.bottom_sensor
        ):
            logger.warning(
                "Control update skipped: missing references to floaters, pneumatic, or sensors."
            )
            return
        t_now = getattr(self, "current_time", 0.0)
        # Floater FSM
        for floater in self.floaters:
            # EMPTY: At bottom, enough pressure, start filling
            if (
                floater.state == "EMPTY"
                and self.bottom_sensor.check(floater)
                and self.pneumatic.tank_pressure > 1.5
            ):
                floater.state = "FILLING"
                floater.fill_start_time = t_now
                self.pneumatic.trigger_injection(floater)
            # FILLING: Wait for fill duration or pressure, then stop
            elif floater.state == "FILLING":
                fill_duration = getattr(
                    self.pneumatic, "fill_time", 0.5
                )  # fallback default
                target_pressure = getattr(self.pneumatic, "target_pressure", 3.0)
                if (
                    t_now - (floater.fill_start_time or 0)
                ) >= fill_duration or floater.internal_pressure >= target_pressure:
                    floater.state = "FILLED"
                    # Close injection valve (handled by physics, or set_filled)
                    floater.set_filled(True)
            # FILLED: At top, start venting
            elif floater.state == "FILLED" and self.top_sensor.check(floater):
                floater.state = "VENTING"
                floater.vent_start_time = t_now
                self.pneumatic.vent_air(floater)
            # VENTING: Wait for vent duration, then stop
            elif floater.state == "VENTING":
                vent_duration = getattr(
                    self.pneumatic, "vent_time", 0.5
                )  # fallback default
                if (t_now - (floater.vent_start_time or 0)) >= vent_duration:
                    floater.state = "EMPTY"
                    floater.set_filled(False)
        logger.debug("Floater FSM update completed.")
        # Compressor control (hysteresis)
        P_min = getattr(self.pneumatic, "P_min", 1.5)
        P_max = getattr(self.pneumatic, "P_max", self.pneumatic.target_pressure)
        if self.pneumatic.tank_pressure < P_min or any(
            f.state == "FILLING" for f in self.floaters
        ):
            self.pneumatic.compressor_on = True
        elif self.pneumatic.tank_pressure > P_max:
            self.pneumatic.compressor_on = False
        # Generator torque PID and clutch control
        if not self.drivetrain:
            logger.warning("No drivetrain reference for PID/clutch control.")
            return
        # Get generator speed (RPM)
        rpm = self.drivetrain.omega_flywheel * 60 / (2 * 3.141592653589793)
        error = self.target_rpm - rpm
        self.int_error += error * dt
        derr = (error - self.prev_error) / dt if dt > 0 else 0.0
        torque_cmd = self.Kp * error + self.Ki * self.int_error + self.Kd * derr
        # Clamp torque
        T_min = 0.0
        T_max = getattr(self.drivetrain, "max_torque", 10000.0)
        torque_cmd = max(min(torque_cmd, T_max), T_min)
        self.prev_error = error
        # Clutch logic
        clutch_engaged = True
        if self.use_clutch:
            if (t_now % (self.T_eng + self.T_free)) < self.T_eng:
                clutch_engaged = True
            else:
                clutch_engaged = False
        self.drivetrain.clutch_engaged = clutch_engaged
        # Apply generator torque only if clutch engaged
        if clutch_engaged:
            if hasattr(self.drivetrain, "set_generator_torque"):
                self.drivetrain.set_generator_torque(torque_cmd)
            else:
                # If no setter, store as attribute for physics to use
                self.drivetrain.load_torque = torque_cmd
        else:
            if hasattr(self.drivetrain, "set_generator_torque"):
                self.drivetrain.set_generator_torque(0.0)
            else:
                self.drivetrain.load_torque = 0.0
        logger.debug(
            f"PID: rpm={rpm:.2f}, error={error:.2f}, torque_cmd={torque_cmd:.2f}, clutch={clutch_engaged}"
        )

    def reset(self):
        """Reset the control system state."""
        self.prev_error = 0.0
        self.int_error = 0.0
        logger.info("Control system reset.")
