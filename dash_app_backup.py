import time
import queue
import plotly.graph_objs as go
import plotly.express as px
import pandas as pd
import logging
import json
import dash_bootstrap_components as dbc
import dash
from simulation.engine import SimulationEngine
from datetime import datetime
from dash import dcc, html, Input, Output, State, callback
from config.parameter_schema import get_default_parameters, validate_parameters_batch
        import traceback
#!/usr/bin/env python3
"""
KPP Simulator Dash Application
Main entry point for the Plotly Dash frontend
"""

