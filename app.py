import queue
import matplotlib
import logging
import time
import numpy as np
import matplotlib.pyplot as plt
import io
import csv
import re
import os
import json
from typing import Dict, Any
from flask_cors import CORS
from flask import Flask, Response, jsonify, request, send_from_directory

# Import simulation components (commented out until implemented)
# from simulation.managers.thread_safe_engine import ThreadSafeEngine
# from simulation.managers.state_manager import StateManager
from simulation.engine import SimulationEngine
from config.parameter_schema import validate_parameters_batch, get_parameter_constraints, get_default_parameters  # type: ignore
# from config import ConfigManager

# CRASH-FIXED Flask app - Removes blocking operations that cause timeouts
