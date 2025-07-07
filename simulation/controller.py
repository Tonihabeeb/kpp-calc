import logging
from utils.logging_setup import setup_logging
from utils.errors import SimulationError
from simulation.plotting import PlottingUtility
from simulation.hypotheses.h3_pulse_mode import H3PulseMode
from simulation.hypotheses.h2_isothermal import H2Isothermal
from simulation.hypotheses.h1_nanobubbles import H1Nanobubbles
from simulation.components.sensors import Sensors
from simulation.components.position_sensor import PositionSensor
from simulation.components.pneumatics import PneumaticSystem
from simulation.components.integrated_drivetrain import create_standard_kpp_drivetrain
from simulation.components.floater.core import LegacyFloaterConfig
from simulation.components.floater import Floater
from simulation.components.environment import Environment
from simulation.components.control import Control
"""
SimulatorController: Orchestrates the simulation loop and module interactions.
Implements the architecture described in guideprestagegap.md.
"""

