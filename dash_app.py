import websockets
import time as time_module
import time
import threading
import queue
import plotly.graph_objs as go
import json
import gc
import dash_bootstrap_components as dbc
import asyncio
import requests
import logging
import dash
from urllib3.util.retry import Retry
from threading import Lock
from collections import deque
from dash import Input, Output, State, dcc, html

# Import simulation components (commented out until implemented)
# from utils.logging_setup import setup_logging
# from simple_browser_monitor import init_simple_browser_monitor
# from observability import get_trace_logger, init_observability
from simulation.engine import SimulationEngine
from config.parameter_schema import get_default_parameters

#!/usr/bin/env python3
"""
KPP Simulator Dash Application
Main entry point for the Plotly Dash frontend
"""

