import math
import logging
from typing import Any, Dict, Optional, Union
from .sprocket import Sprocket
from .one_way_clutch import OneWayClutch, PulseCoastController
from .gearbox import create_kpp_gearbox
from .flywheel import Flywheel, FlywheelController
    from config.components.drivetrain_config import DrivetrainConfig as NewDrivetrainConfig
    from chain tension input to generator output.
"""
Integrated integrated_drivetrain system combining sprockets, gearbox, clutch,
     and flywheel.
This represents the complete mechanical power transmission system for the KPP.
"""

