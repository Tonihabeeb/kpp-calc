import time
import threading
import queue
import matplotlib.pyplot as plt
import matplotlib
import logging
import json
import io
from utils.backend_logger import setup_backend_logger
from simulation.engine import SimulationEngine
from simulation.components.floater import Floater
from flask import Flask, Response, jsonify, render_template, request, send_file
from config.parameter_schema import (
from collections import deque
    import os
    import csv
        import traceback
        import pkg_resources
# Flask web app entry point
# All endpoints interact with the SimulationEngine only
# Handles real-time simulation, streaming, and control requests

