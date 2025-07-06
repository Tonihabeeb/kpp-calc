#!/usr/bin/env python3
"""
KPP Simulator Dash Application
Main entry point for the Plotly Dash frontend
"""

import asyncio
import json
import logging
import queue
import threading
import time
from collections import deque

import dash
import dash_bootstrap_components as dbc
import plotly.graph_objs as go
import requests
import websockets
from dash import Input, Output, State, dcc, html

from config.parameter_schema import get_default_parameters

# Import our existing simulation engine
from simulation.engine import SimulationEngine
from utils.logging_setup import setup_logging

# import dash_daq as daq  # Only needed if actually used in the rendered UI


# Configure logging
setup_logging()

# ADDED: Connection pooling and request management to fix ERR_INSUFFICIENT_RESOURCES
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry


# Create a session with connection pooling and limits
def create_http_session():
    """Create HTTP session with connection pooling and retry logic"""
    session = requests.Session()

    # Configure retry strategy
    retry_strategy = Retry(
        total=3,
        backoff_factor=0.3,
        status_forcelist=[429, 500, 502, 503, 504],
    )

    # Configure HTTP adapter with connection pooling
    adapter = HTTPAdapter(
        pool_connections=5,  # Number of connection pools
        pool_maxsize=10,  # Maximum number of connections in pool
        max_retries=retry_strategy,
        pool_block=False,  # Don't block when pool is full
    )

    session.mount("http://", adapter)
    session.mount("https://", adapter)

    return session


# Global HTTP session for connection reuse
http_session = create_http_session()

# ADDED: Rate limiting and caching to prevent resource exhaustion
import time as time_module
from threading import Lock

# Rate limiting variables
_last_request_time = 0
_cached_data = None
_cache_lock = Lock()
_request_count = 0
_max_requests_per_second = 2  # Limit to 2 requests per second


def should_throttle_request():
    """Check if we should throttle the request to prevent resource exhaustion"""
    global _last_request_time, _request_count

    current_time = time_module.time()

    # Reset counter every second
    if current_time - _last_request_time >= 1.0:
        _request_count = 0
        _last_request_time = current_time

    # Check if we've exceeded the limit
    if _request_count >= _max_requests_per_second:
        return True

    _request_count += 1
    return False


# ADDED: Memory management to prevent memory leaks
import gc


def cleanup_memory():
    """Periodic memory cleanup to prevent leaks"""
    # Force garbage collection
    gc.collect()

    # Clear any large data structures periodically
    global _cached_data
    with _cache_lock:
        # Keep only recent data to prevent memory buildup
        if _cached_data and isinstance(_cached_data, dict):
            # Limit cached data size
            if len(str(_cached_data)) > 10000:  # If data is getting too large
                _cached_data = {
                    "time": _cached_data.get("time", 0.0),
                    "power": _cached_data.get("power", 0.0),
                    "torque": _cached_data.get("torque", 0.0),
                    "status": _cached_data.get("status", "unknown"),
                }


# Import observability system
from observability import get_trace_logger, init_observability

# Configuration
DASH_PORT = 9103
BACKEND_URL = "http://localhost:9100"
WEBSOCKET_URL = "ws://localhost:9101"

# Initialize Dash app with enhanced styling
external_stylesheets = [
    dbc.themes.BOOTSTRAP,  # Bootstrap 5
    "https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap",
    "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css",
]

app = dash.Dash(
    __name__,
    external_stylesheets=external_stylesheets,
    suppress_callback_exceptions=True,
    assets_folder="static",  # Configure static assets folder
    meta_tags=[
        {"name": "viewport", "content": "width=device-width, initial-scale=1"},
        {"name": "description", "content": "KPP Simulator Dashboard - Professional Control Interface"},
    ],
)
app.title = "KPP Simulator Dashboard"

# Initialize observability system for Dash
init_observability(app)

# Get trace-aware logger for Dash
trace_logger = get_trace_logger("kpp_dash")


# Synchronized data manager for real-time updates
class SynchronizedDataManager:
    """Manages real-time data from master clock for smooth visualization"""

    def __init__(self, master_clock_url="ws://localhost:9201/sync"):
        self.master_clock_url = master_clock_url
        self.latest_frame = {"time": 0.0, "power": 0.0, "torque": 0.0, "efficiency": 0.0, "status": "initializing"}
        self.connected = False
        self.frame_buffer = deque(maxlen=200)  # 200 frames = ~6.7 seconds at 30 FPS
        self.connection = None
        self.running = False

    async def connect_to_master_clock(self):
        """Connect to master clock for synchronized updates"""
        try:
            self.connection = await websockets.connect(
                f"{self.master_clock_url}?type=frontend", ping_interval=10, ping_timeout=5
            )
            self.connected = True
            logging.info("Dash frontend connected to master clock")

            # Start listening for frames
            await self.listen_for_frames()

        except Exception as e:
            logging.error(f"Failed to connect to master clock: {e}")
            self.connected = False

    async def listen_for_frames(self):
        """Listen for synchronized frames from master clock"""
        try:
            async for message in self.connection:
                frame_data = json.loads(message)

                if frame_data.get("type") == "frame_update":
                    frame = frame_data.get("frame", {})

                    # Update latest frame for Dash callbacks
                    self.latest_frame = {
                        "time": frame.get("simulation_time", 0.0),
                        "power": frame.get("power", 0.0),
                        "torque": frame.get("torque", 0.0),
                        "power_output": frame.get("power", 0.0),
                        "overall_efficiency": frame.get("efficiency", 0.0),
                        "chain_tension": frame.get("metadata", {}).get("chain_tension", 0.0),
                        "flywheel_speed_rpm": frame.get("metadata", {}).get("flywheel_speed_rpm", 0.0),
                        "chain_speed_rpm": frame.get("metadata", {}).get("chain_speed_rpm", 0.0),
                        "clutch_engaged": frame.get("metadata", {}).get("clutch_engaged", False),
                        "pulse_count": frame.get("metadata", {}).get("pulse_count", 0),
                        "tank_pressure": frame.get("metadata", {}).get("tank_pressure", 0.0),
                        "electrical_engagement": frame.get("power", 0.0) > 1000,
                        "status": frame.get("status", "unknown"),
                        "health": "synchronized",
                        "timestamp": frame.get("timestamp", time.time()),
                        "frame_id": frame.get("frame_id", 0),
                        "grid_power_output": frame.get("power", 0.0),
                    }

                    # Buffer frame for interpolation
                    self.frame_buffer.append(self.latest_frame)

        except websockets.exceptions.ConnectionClosed:
            logging.warning("Master clock connection closed")
            self.connected = False
        except Exception as e:
            logging.error(f"Error listening for frames: {e}")
            self.connected = False

    def start_background_connection(self):
        """Start master clock connection in background thread"""

        def run_async():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(self.connect_to_master_clock())
            except Exception as e:
                logging.error(f"Background connection error: {e}")
            finally:
                loop.close()

        if not self.running:
            self.running = True
            threading.Thread(target=run_async, daemon=True).start()

    def get_latest_data(self):
        """Get latest synchronized data for Dash callbacks"""
        return self.latest_frame


# Global synchronized data manager
sync_data_manager = SynchronizedDataManager()

# Global simulation engine instance
# We'll embed the engine directly for optimal performance
sim_engine = None
default_params = get_default_parameters()


def initialize_simulation():
    """Initialize the simulation engine with default parameters"""
    global sim_engine
    try:
        # Create a data queue for the simulation engine
        data_queue = queue.Queue()
        sim_engine = SimulationEngine(default_params, data_queue)
        sim_engine.reset()
        logging.info("Simulation engine initialized successfully")
        return True
    except Exception as e:
        logging.error(f"Failed to initialize simulation engine: {e}")
        return False


def validate_ws_data(data):
    """Validate WebSocket data structure"""
    try:
        if not isinstance(data, dict):
            return False, "Data must be a dictionary"

        # More flexible validation - only check for basic structure
        # Don't require specific fields since the data format may vary
        if len(data) == 0:
            return False, "Data dictionary is empty"

        # Accept any dictionary with at least one key-value pair
        # This allows for flexible data formats from different sources
        return True, None

    except Exception as e:
        return False, f"Validation error: {str(e)}"


# Layout Components


# --- Component creation functions (moved before layout) ---
def create_advanced_parameters_panel():
    """Create advanced parameters panel with enhanced KPP system controls"""
    return dbc.Card(
        [
            dbc.CardHeader(html.H5("Advanced Parameters", className="mb-0")),
            dbc.CardBody(
                [
                    # Physical Properties
                    html.H6("Physical Properties", className="text-primary"),
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    html.Label(
                                        [
                                            "Floater Mass (kg) ",
                                            html.I(
                                                "?",
                                                id="floater-mass-help",
                                                style={"cursor": "pointer", "color": "#888"},
                                            ),
                                        ]
                                    ),
                                    dcc.Slider(
                                        id="floater-mass-slider",
                                        min=5,
                                        max=30,
                                        step=1,
                                        value=16,  # Updated to new default
                                        marks={i: str(i) for i in range(5, 31, 5)},
                                        tooltip={"placement": "bottom", "always_visible": True},
                                    ),
                                    html.Div(id="advanced-floater-mass-error"),
                                    dbc.Tooltip(
                                        "Mass of empty floater (kg). Range: 5-30 kg.",
                                        target="floater-mass-help",
                                        placement="top",
                                    ),
                                ],
                                width=6,
                            ),
                            dbc.Col(
                                [
                                    html.Label(
                                        [
                                            "Floater Area (m²) ",
                                            html.I(
                                                "?",
                                                id="floater-area-help",
                                                style={"cursor": "pointer", "color": "#888"},
                                            ),
                                        ]
                                    ),
                                    dcc.Slider(
                                        id="floater-area-slider",
                                        min=0.01,
                                        max=0.2,
                                        step=0.01,
                                        value=0.1,  # Updated to new default
                                        marks={round(i / 100, 2): f"{i/100:.2f}" for i in range(1, 21, 5)},
                                        tooltip={"placement": "bottom", "always_visible": True},
                                    ),
                                    html.Div(id="advanced-floater-area-error"),
                                    dbc.Tooltip(
                                        "Exposed cross-sectional area of floater (m²). Range: 0.01-0.2 m².",
                                        target="floater-area-help",
                                        placement="top",
                                    ),
                                ],
                                width=6,
                            ),
                        ],
                        className="mb-3",
                    ),
                    # Pneumatic System with Pressure Recovery
                    html.H6("Pneumatic System & Pressure Recovery", className="text-success"),
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    html.Label(
                                        [
                                            "Air Fill Time (s) ",
                                            html.I(
                                                "?",
                                                id="air-fill-time-help",
                                                style={"cursor": "pointer", "color": "#888"},
                                            ),
                                        ]
                                    ),
                                    dcc.Slider(
                                        id="air-fill-time-slider",
                                        min=0.1,
                                        max=2.0,
                                        step=0.1,
                                        value=0.5,
                                        marks={i / 10: f"{i/10}" for i in range(1, 21, 5)},
                                        tooltip={"placement": "bottom", "always_visible": True},
                                    ),
                                    html.Div(id="advanced-air-fill-time-error"),
                                    dbc.Tooltip(
                                        "Time to fill a floater with air (seconds). Range: 0.1-2.0 s.",
                                        target="air-fill-time-help",
                                        placement="top",
                                    ),
                                ],
                                width=4,
                            ),
                            dbc.Col(
                                [
                                    html.Label(
                                        [
                                            "Air Flow Rate (m³/s) ",
                                            html.I(
                                                "?",
                                                id="air-flow-rate-help",
                                                style={"cursor": "pointer", "color": "#888"},
                                            ),
                                        ]
                                    ),
                                    dcc.Slider(
                                        id="air-flow-rate-slider",
                                        min=0.1,
                                        max=2.0,
                                        step=0.1,
                                        value=1.2,  # Updated to new default
                                        marks={i / 10: f"{i/10}" for i in range(1, 21, 5)},
                                        tooltip={"placement": "bottom", "always_visible": True},
                                    ),
                                    html.Div(id="advanced-air-flow-rate-error"),
                                    dbc.Tooltip(
                                        "Air flow rate into floater (m³/s). Range: 0.1-2.0 m³/s.",
                                        target="air-flow-rate-help",
                                        placement="top",
                                    ),
                                ],
                                width=4,
                            ),
                            dbc.Col(
                                [
                                    html.Label(
                                        [
                                            "Pressure Recovery Efficiency ",
                                            html.I(
                                                "?",
                                                id="pressure-recovery-help",
                                                style={"cursor": "pointer", "color": "#888"},
                                            ),
                                        ]
                                    ),
                                    dcc.Slider(
                                        id="pressure-recovery-slider",
                                        min=0.1,
                                        max=0.4,
                                        step=0.02,
                                        value=0.22,  # New parameter
                                        marks={i / 100: f"{i/100:.2f}" for i in range(10, 41, 10)},
                                        tooltip={"placement": "bottom", "always_visible": True},
                                    ),
                                    html.Div(id="pressure-recovery-error"),
                                    dbc.Tooltip(
                                        "Pressure recovery system efficiency (0.1-0.4). Higher values recover more energy from vented air.",
                                        target="pressure-recovery-help",
                                        placement="top",
                                    ),
                                ],
                                width=4,
                            ),
                        ],
                        className="mb-3",
                    ),
                    # Water Jet Physics
                    html.H6("Water Jet Physics", className="text-info"),
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    html.Label(
                                        [
                                            "Jet Efficiency ",
                                            html.I(
                                                "?",
                                                id="jet-efficiency-help",
                                                style={"cursor": "pointer", "color": "#888"},
                                            ),
                                        ]
                                    ),
                                    dcc.Slider(
                                        id="jet-efficiency-slider",
                                        min=0.5,
                                        max=1.0,
                                        step=0.05,
                                        value=0.85,
                                        marks={i / 100: f"{i/100:.2f}" for i in range(50, 101, 10)},
                                        tooltip={"placement": "bottom", "always_visible": True},
                                    ),
                                    html.Div(id="advanced-jet-efficiency-error"),
                                    dbc.Tooltip(
                                        "Efficiency of water jet propulsion (0.5-1.0). Higher values provide more thrust.",
                                        target="jet-efficiency-help",
                                        placement="top",
                                    ),
                                ],
                                width=6,
                            ),
                            dbc.Col(
                                [
                                    dbc.Switch(
                                        id="water-jet-enabled-switch",
                                        label="Enable Water Jet Physics",
                                        value=True,  # New parameter - enabled by default
                                        className="mt-3",
                                    ),
                                    html.Div(id="water-jet-error"),
                                ],
                                width=6,
                            ),
                        ],
                        className="mb-3",
                    ),
                    # Mechanical System (Enhanced)
                    html.H6("Mechanical System", className="text-warning"),
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    html.Label(
                                        [
                                            "Sprocket Radius (m) ",
                                            html.I(
                                                "?",
                                                id="sprocket-radius-help",
                                                style={"cursor": "pointer", "color": "#888"},
                                            ),
                                        ]
                                    ),
                                    dcc.Slider(
                                        id="sprocket-radius-slider",
                                        min=0.5,
                                        max=2.0,
                                        step=0.1,
                                        value=1.2,  # Updated to new default
                                        marks={i / 10: f"{i/10}" for i in range(5, 21, 5)},
                                        tooltip={"placement": "bottom", "always_visible": True},
                                    ),
                                    html.Div(id="advanced-sprocket-radius-error"),
                                    dbc.Tooltip(
                                        "Radius of main sprocket (meters). Range: 0.5-2.0 m.",
                                        target="sprocket-radius-help",
                                        placement="top",
                                    ),
                                ],
                                width=6,
                            ),
                            dbc.Col(
                                [
                                    html.Label(
                                        [
                                            "Flywheel Inertia (kg⋅m²) ",
                                            html.I(
                                                "?",
                                                id="flywheel-inertia-help",
                                                style={"cursor": "pointer", "color": "#888"},
                                            ),
                                        ]
                                    ),
                                    dcc.Slider(
                                        id="flywheel-inertia-slider",
                                        min=50,
                                        max=600,
                                        step=50,
                                        value=500,  # Updated to new default
                                        marks={i: str(i) for i in range(50, 601, 100)},
                                        tooltip={"placement": "bottom", "always_visible": True},
                                    ),
                                    html.Div(id="advanced-flywheel-inertia-error"),
                                    dbc.Tooltip(
                                        "Rotational inertia of flywheel (kg⋅m²). Range: 50-600 kg⋅m².",
                                        target="flywheel-inertia-help",
                                        placement="top",
                                    ),
                                ],
                                width=6,
                            ),
                        ],
                        className="mb-3",
                    ),
                    # Field-Oriented Control (FOC)
                    html.H6("Field-Oriented Control (FOC)", className="text-danger"),
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    dbc.Switch(
                                        id="foc-enabled-switch",
                                        label="Enable FOC Control",
                                        value=True,  # New parameter - enabled by default
                                        className="mb-2",
                                    ),
                                    html.Div(id="foc-enabled-error"),
                                ],
                                width=4,
                            ),
                            dbc.Col(
                                [
                                    html.Label("Torque Controller Kp"),
                                    dcc.Slider(
                                        id="foc-torque-kp-slider",
                                        min=50,
                                        max=200,
                                        step=10,
                                        value=120,  # New parameter
                                        marks={i: str(i) for i in range(50, 201, 50)},
                                        tooltip={"placement": "bottom", "always_visible": True},
                                    ),
                                    html.Div(id="foc-torque-kp-error"),
                                ],
                                width=4,
                            ),
                            dbc.Col(
                                [
                                    html.Label("Flux Controller Kp"),
                                    dcc.Slider(
                                        id="foc-flux-kp-slider",
                                        min=40,
                                        max=150,
                                        step=10,
                                        value=90,  # New parameter
                                        marks={i: str(i) for i in range(40, 151, 30)},
                                        tooltip={"placement": "bottom", "always_visible": True},
                                    ),
                                    html.Div(id="foc-flux-kp-error"),
                                ],
                                width=4,
                            ),
                        ],
                        className="mb-3",
                    ),
                    # --- Submit button for advanced parameters ---
                    dbc.Button(
                        "Submit Advanced Parameters",
                        id="submit-advanced-params-btn",
                        color="primary",
                        className="mt-3",
                        n_clicks=0,
                    ),
                ]
            ),
        ],
        className="mb-4",
    )


def create_physics_controls_panel():
    """Create H1/H2/H3 enhanced physics controls panel"""
    return dbc.Card(
        [
            dbc.CardHeader(html.H5("Enhanced Physics Controls", className="mb-0")),
            dbc.CardBody(
                [
                    # H1 Nanobubble Physics (Updated)
                    html.H6("H1 Nanobubble Drag Reduction", className="text-success"),
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    dbc.Switch(
                                        id="h1-enabled-switch",
                                        label="Enable H1 Nanobubbles",
                                        value=True,  # Changed to enabled by default
                                        className="mb-2",
                                    ),
                                    html.Div(id="h1-switch-error"),
                                ],
                                width=4,
                            ),
                            dbc.Col(
                                [
                                    html.Label("Nanobubble Fraction"),
                                    dcc.Slider(
                                        id="nanobubble-fraction-slider",
                                        min=0.0,
                                        max=0.1,
                                        step=0.01,
                                        value=0.05,  # Updated default
                                        marks={i / 100: f"{i/100:.2f}" for i in range(0, 11, 2)},
                                        tooltip={"placement": "bottom", "always_visible": True},
                                    ),
                                    html.Div(id="nanobubble-fraction-error"),
                                ],
                                width=4,
                            ),
                            dbc.Col(
                                [
                                    html.Label("Drag Reduction (%)"),
                                    dcc.Slider(
                                        id="drag-reduction-slider",
                                        min=0.0,
                                        max=0.25,
                                        step=0.01,
                                        value=0.12,  # New parameter
                                        marks={i / 100: f"{i:.0f}%" for i in range(0, 26, 5)},
                                        tooltip={"placement": "bottom", "always_visible": True},
                                    ),
                                    html.Div(id="drag-reduction-error"),
                                ],
                                width=4,
                            ),
                        ],
                        className="mb-3",
                    ),
                    # H2 Thermal Enhancement Physics (Updated)
                    html.H6("H2 Thermal Enhancement", className="text-info"),
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    dbc.Switch(
                                        id="h2-enabled-switch",
                                        label="Enable H2 Thermal Effects",
                                        value=True,  # Changed to enabled by default
                                        className="mb-2",
                                    ),
                                    html.Div(id="h2-switch-error"),
                                ],
                                width=4,
                            ),
                            dbc.Col(
                                [
                                    html.Label("Thermal Efficiency"),
                                    dcc.Slider(
                                        id="thermal-efficiency-slider",
                                        min=0.5,
                                        max=1.0,
                                        step=0.05,
                                        value=0.8,  # Updated parameter
                                        marks={i / 100: f"{i/100:.2f}" for i in range(50, 101, 10)},
                                        tooltip={"placement": "bottom", "always_visible": True},
                                    ),
                                    html.Div(id="thermal-efficiency-error"),
                                ],
                                width=4,
                            ),
                            dbc.Col(
                                [
                                    html.Label("Buoyancy Boost (%)"),
                                    dcc.Slider(
                                        id="buoyancy-boost-slider",
                                        min=0.0,
                                        max=0.15,
                                        step=0.01,
                                        value=0.06,  # New parameter
                                        marks={i / 100: f"{i:.0f}%" for i in range(0, 16, 3)},
                                        tooltip={"placement": "bottom", "always_visible": True},
                                    ),
                                    html.Div(id="buoyancy-boost-error"),
                                ],
                                width=4,
                            ),
                        ],
                        className="mb-3",
                    ),
                    # H3 Pulse-Coast Operation (New)
                    html.H6("H3 Pulse-Coast Operation", className="text-warning"),
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    dbc.Switch(
                                        id="h3-enabled-switch",
                                        label="Enable H3 Pulse-Coast Mode",
                                        value=True,  # New parameter - enabled by default
                                        className="mb-2",
                                    ),
                                    html.Div(id="h3-switch-error"),
                                ],
                                width=4,
                            ),
                            dbc.Col(
                                [
                                    html.Label("Pulse Duration (s)"),
                                    dcc.Slider(
                                        id="pulse-duration-slider",
                                        min=0.5,
                                        max=3.0,
                                        step=0.1,
                                        value=2.0,  # New parameter
                                        marks={i / 10: f"{i/10:.1f}" for i in range(5, 31, 5)},
                                        tooltip={"placement": "bottom", "always_visible": True},
                                    ),
                                    html.Div(id="pulse-duration-error"),
                                ],
                                width=4,
                            ),
                            dbc.Col(
                                [
                                    html.Label("Coast Duration (s)"),
                                    dcc.Slider(
                                        id="coast-duration-slider",
                                        min=0.2,
                                        max=2.0,
                                        step=0.1,
                                        value=1.0,  # New parameter
                                        marks={i / 10: f"{i/10:.1f}" for i in range(2, 21, 5)},
                                        tooltip={"placement": "bottom", "always_visible": True},
                                    ),
                                    html.Div(id="coast-duration-error"),
                                ],
                                width=4,
                            ),
                        ],
                        className="mb-3",
                    ),
                    # Temperature Controls (Updated)
                    html.H6("Environmental Temperature", className="text-secondary"),
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    html.Label("Water Temperature (°C)"),
                                    dcc.Slider(
                                        id="water-temp-slider",
                                        min=5,
                                        max=50,
                                        step=1,
                                        value=20,  # Updated to Celsius
                                        marks={i: f"{i}°C" for i in range(5, 51, 10)},
                                        tooltip={"placement": "bottom", "always_visible": True},
                                    ),
                                    html.Div(id="water-temp-error"),
                                ],
                                width=6,
                            ),
                            dbc.Col(
                                [
                                    html.Label("Ambient Temperature (°C)"),
                                    dcc.Slider(
                                        id="ambient-temp-slider",
                                        min=5,
                                        max=50,
                                        step=1,
                                        value=20,  # New parameter
                                        marks={i: f"{i}°C" for i in range(5, 51, 10)},
                                        tooltip={"placement": "bottom", "always_visible": True},
                                    ),
                                    html.Div(id="ambient-temp-error"),
                                ],
                                width=6,
                            ),
                        ],
                        className="mb-3",
                    ),
                    # Submit button
                    dbc.Button(
                        "Submit Physics Controls",
                        id="submit-physics-controls-btn",
                        color="success",
                        className="mt-3",
                        n_clicks=0,
                    ),
                ]
            ),
        ],
        className="mb-4",
    )


def create_system_overview_panel():
    """Create system overview panel"""
    return dbc.Card(
        [
            dbc.CardHeader(html.H5("System Overview", className="mb-0")),
            dbc.CardBody(
                [
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    html.H6("IntegratedDrivetrain Status", className="text-primary"),
                                    html.Div(id="integrated_drivetrain-overview", children="Initializing..."),
                                ],
                                width=6,
                            ),
                            dbc.Col(
                                [
                                    html.H6("Electrical System", className="text-success"),
                                    html.Div(id="electrical-overview", children="Initializing..."),
                                ],
                                width=6,
                            ),
                        ],
                        className="mb-3",
                    ),
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    html.H6("Control System", className="text-info"),
                                    html.Div(id="control-overview", children="Initializing..."),
                                ],
                                width=6,
                            ),
                            dbc.Col(
                                [
                                    html.H6("Physics Engine", className="text-warning"),
                                    html.Div(id="physics-overview", children="Initializing..."),
                                ],
                                width=6,
                            ),
                        ]
                    ),
                ]
            ),
        ],
        className="mb-4",
    )


def create_header():
    """Create the main header section"""
    return dbc.Navbar(
        dbc.Container(
            [
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                html.Div(
                                    [
                                        html.I(
                                            className="fas fa-bolt",
                                            style={"fontSize": "2rem", "marginRight": "0.75rem", "color": "#60a5fa"},
                                        ),
                                        dbc.NavbarBrand(
                                            "KPP Simulator Dashboard",
                                            className="text-gradient",
                                            style={"fontSize": "1.75rem", "fontWeight": "700"},
                                        ),
                                    ],
                                    className="d-flex align-items-center",
                                )
                            ],
                            width="auto",
                        ),
                        dbc.Col(
                            [
                                html.Div(
                                    [
                                        html.Div(id="connection-status", className="text-end"),
                                        html.Small("v2.0 Professional", className="text-light opacity-75"),
                                    ]
                                )
                            ],
                            width="auto",
                            className="ms-auto text-end",
                        ),
                    ],
                    align="center",
                    className="w-100",
                )
            ],
            fluid=True,
        ),
        color="primary",
        dark=True,
        className="mb-4 shadow-smooth",
    )


def create_control_panel():
    """Create the simulation control panel"""
    return dbc.Card(
        [
            dbc.CardHeader(
                [
                    html.Div(
                        [
                            html.I(className="fas fa-play-circle", style={"marginRight": "0.5rem"}),
                            html.H5("Simulation Controls", className="mb-0 d-inline"),
                        ]
                    )
                ]
            ),
            dbc.CardBody(
                [
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    dbc.ButtonGroup(
                                        [
                                            dbc.Button(
                                                [html.I(className="fas fa-play me-2"), "Start"],
                                                id="start-btn",
                                                color="success",
                                                size="lg",
                                                className="px-4",
                                            ),
                                            dbc.Button(
                                                [html.I(className="fas fa-pause me-2"), "Pause"],
                                                id="pause-btn",
                                                color="warning",
                                                size="lg",
                                                className="px-4",
                                            ),
                                            dbc.Button(
                                                [html.I(className="fas fa-stop me-2"), "Stop"],
                                                id="stop-btn",
                                                color="danger",
                                                size="lg",
                                                className="px-4",
                                            ),
                                            dbc.Button(
                                                [html.I(className="fas fa-redo me-2"), "Reset"],
                                                id="reset-btn",
                                                color="secondary",
                                                size="lg",
                                                className="px-4",
                                            ),
                                        ]
                                    )
                                ],
                                width=8,
                            ),
                            dbc.Col(
                                [html.Div(id="simulation-status", className="text-end align-self-center")],
                                width=4,
                                className="d-flex align-items-center justify-content-end",
                            ),
                        ]
                    )
                ]
            ),
        ],
        className="mb-4 shadow-smooth",
    )


def create_metrics_cards():
    """Create real-time metrics cards with enhanced data"""
    return dbc.Row(
        [
            dbc.Col(
                [
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.I(
                                        className="fas fa-bolt",
                                        style={"fontSize": "1.5rem", "color": "#2563eb", "marginBottom": "0.5rem"},
                                    ),
                                    html.H4(id="power-value", children="0 W", className="metric-value"),
                                    html.P("Power Output", className="metric-label"),
                                    html.Small(id="grid-power", children="Grid: 0 W", className="text-success"),
                                ],
                                className="metric-card",
                            )
                        ],
                        className="h-100",
                    )
                ],
                width=3,
            ),
            dbc.Col(
                [
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.I(
                                        className="fas fa-cog",
                                        style={"fontSize": "1.5rem", "color": "#059669", "marginBottom": "0.5rem"},
                                    ),
                                    html.H4(id="torque-value", children="0 Nm", className="metric-value"),
                                    html.P("Torque", className="metric-label"),
                                    html.Small(id="flywheel-rpm", children="RPM: 0", className="text-info"),
                                ],
                                className="metric-card",
                            )
                        ],
                        className="h-100",
                    )
                ],
                width=3,
            ),
            dbc.Col(
                [
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.I(
                                        className="fas fa-tachometer-alt",
                                        style={"fontSize": "1.5rem", "color": "#f59e0b", "marginBottom": "0.5rem"},
                                    ),
                                    html.H4(id="efficiency-value", children="0%", className="metric-value"),
                                    html.P("Overall Efficiency", className="metric-label"),
                                    html.Small(
                                        id="electrical-eff", children="Electrical: 0%", className="text-warning"
                                    ),
                                ],
                                className="metric-card",
                            )
                        ],
                        className="h-100",
                    )
                ],
                width=3,
            ),
            dbc.Col(
                [
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.I(
                                        className="fas fa-clock",
                                        style={"fontSize": "1.5rem", "color": "#3b82f6", "marginBottom": "0.5rem"},
                                    ),
                                    html.H4(id="time-value", children="0 s", className="metric-value"),
                                    html.P("Simulation Time", className="metric-label"),
                                    html.Small(id="pulse-count", children="Pulses: 0", className="text-secondary"),
                                ],
                                className="metric-card",
                            )
                        ],
                        className="h-100",
                    )
                ],
                width=3,
            ),
        ],
        className="mb-4",
    )


def create_metric_selector():
    """Create a checklist for selecting which metrics to display on the charts"""
    return dbc.Card(
        [
            dbc.CardHeader("Select Metrics to Display"),
            dbc.CardBody(
                [
                    dcc.Checklist(
                        id="metric-selector",
                        options=[
                            {"label": "Power (W)", "value": "power"},
                            {"label": "Torque (Nm)", "value": "torque"},
                            {"label": "Efficiency (%)", "value": "efficiency"},
                        ],
                        value=["power", "torque", "efficiency"],
                        inline=True,
                        inputStyle={"marginRight": "5px", "marginLeft": "10px"},
                    )
                ]
            ),
        ],
        className="mb-3",
    )


def create_charts_section():
    """Create the main charts section"""
    return dbc.Row(
        [
            dbc.Col(
                [
                    dbc.Card(
                        [
                            dbc.CardHeader(
                                [
                                    html.Div(
                                        [
                                            html.I(className="fas fa-chart-line me-2"),
                                            html.H6("Power & Torque", className="mb-0 d-inline"),
                                        ]
                                    )
                                ]
                            ),
                            dbc.CardBody(
                                [
                                    dcc.Graph(
                                        id="power-torque-chart",
                                        figure={
                                            "data": [
                                                {
                                                    "x": [],
                                                    "y": [],
                                                    "type": "scatter",
                                                    "mode": "lines",
                                                    "name": "Power (W)",
                                                    "line": {"color": "#2563eb", "width": 3},
                                                },
                                                {
                                                    "x": [],
                                                    "y": [],
                                                    "type": "scatter",
                                                    "mode": "lines",
                                                    "name": "Torque (Nm)",
                                                    "line": {"color": "#059669", "width": 3},
                                                    "yaxis": "y2",
                                                },
                                            ],
                                            "layout": {
                                                "title": {
                                                    "text": "Power & Torque vs Time",
                                                    "font": {"size": 18, "family": "Inter"},
                                                },
                                                "xaxis": {"title": "Time (s)", "gridcolor": "#e5e7eb"},
                                                "yaxis": {"title": "Power (W)", "side": "left", "gridcolor": "#e5e7eb"},
                                                "yaxis2": {
                                                    "title": "Torque (Nm)",
                                                    "side": "right",
                                                    "overlaying": "y",
                                                    "gridcolor": "#e5e7eb",
                                                },
                                                "legend": {"x": 0.01, "y": 0.99},
                                                "height": 400,
                                                "plot_bgcolor": "rgba(0,0,0,0)",
                                                "paper_bgcolor": "rgba(0,0,0,0)",
                                                "font": {"family": "Inter"},
                                            },
                                        },
                                        config={"responsive": True, "displayModeBar": False},
                                        animate=False,
                                    )
                                ],
                                className="chart-container",
                            ),
                        ],
                        className="shadow-smooth",
                    )
                ],
                width=6,
            ),
            dbc.Col(
                [
                    dbc.Card(
                        [
                            dbc.CardHeader(
                                [
                                    html.Div(
                                        [
                                            html.I(className="fas fa-tachometer-alt me-2"),
                                            html.H6("System Efficiency", className="mb-0 d-inline"),
                                        ]
                                    )
                                ]
                            ),
                            dbc.CardBody(
                                [
                                    dcc.Graph(
                                        id="efficiency-chart",
                                        figure={
                                            "data": [
                                                {
                                                    "x": [],
                                                    "y": [],
                                                    "type": "scatter",
                                                    "mode": "lines",
                                                    "name": "Overall Efficiency",
                                                    "line": {"color": "#f59e0b", "width": 3},
                                                    "fill": "tonexty",
                                                }
                                            ],
                                            "layout": {
                                                "title": {
                                                    "text": "System Efficiency vs Time",
                                                    "font": {"size": 18, "family": "Inter"},
                                                },
                                                "xaxis": {"title": "Time (s)", "gridcolor": "#e5e7eb"},
                                                "yaxis": {
                                                    "title": "Efficiency (%)",
                                                    "range": [0, 100],
                                                    "gridcolor": "#e5e7eb",
                                                },
                                                "height": 400,
                                                "plot_bgcolor": "rgba(0,0,0,0)",
                                                "paper_bgcolor": "rgba(0,0,0,0)",
                                                "font": {"family": "Inter"},
                                            },
                                        },
                                        config={"responsive": True, "displayModeBar": False},
                                        animate=False,
                                    )
                                ],
                                className="chart-container",
                            ),
                        ],
                        className="shadow-smooth",
                    )
                ],
                width=6,
            ),
        ],
        className="mb-4",
    )


def create_basic_parameters_panel():
    """Create basic parameters panel"""
    return dbc.Card(
        [
            dbc.CardHeader(html.H5("Basic Parameters", className="mb-0")),
            dbc.CardBody(
                [
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    html.Label("Number of Floaters"),
                                    dcc.Slider(
                                        id="num-floaters-slider",
                                        min=4,
                                        max=100,
                                        step=2,
                                        value=66,
                                        marks={i: str(i) for i in range(4, 101, 8)},
                                        tooltip={"placement": "bottom", "always_visible": True},
                                    ),
                                    html.Div(id="basic-floater-mass-error"),
                                ],
                                width=6,
                            ),
                            dbc.Col(
                                [
                                    html.Label("Floater Volume (m³)"),
                                    dcc.Slider(
                                        id="floater-volume-slider",
                                        min=0.1,
                                        max=1.0,
                                        step=0.1,
                                        value=0.4,
                                        marks={round(i / 10, 1): f"{i/10:.1f}" for i in range(1, 11)},
                                        tooltip={"placement": "bottom", "always_visible": True},
                                    ),
                                    html.Div(id="basic-floater-area-error"),
                                ],
                                width=6,
                            ),
                        ],
                        className="mb-3",
                    ),
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    html.Label("Air Pressure (Pa)"),
                                    dcc.Slider(
                                        id="air-pressure-slider",
                                        min=100000,
                                        max=500000,
                                        step=50000,
                                        value=400000,
                                        marks={i: f"{i//1000}k" for i in range(100000, 501000, 100000)},
                                        tooltip={"placement": "bottom", "always_visible": True},
                                    ),
                                    html.Div(id="basic-air-fill-time-error"),
                                ],
                                width=6,
                            ),
                            dbc.Col(
                                [
                                    html.Label("Pulse Interval (s)"),
                                    dcc.Slider(
                                        id="pulse-interval-slider",
                                        min=0.5,
                                        max=5.0,
                                        step=0.5,
                                        value=2.2,
                                        marks={i / 2: f"{i/2}" for i in range(1, 11)},
                                        tooltip={"placement": "bottom", "always_visible": True},
                                    ),
                                    html.Div(id="basic-air-flow-rate-error"),
                                ],
                                width=6,
                            ),
                        ]
                    ),
                    # Enhanced parameters section
                    html.Hr(),
                    html.H6("Enhanced System Parameters", className="text-primary mt-3"),
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    html.Label("Tank Height (m)"),
                                    dcc.Slider(
                                        id="tank-height-slider",
                                        min=10,
                                        max=30,
                                        step=1,
                                        value=25,
                                        marks={i: str(i) for i in range(10, 31, 5)},
                                        tooltip={"placement": "bottom", "always_visible": True},
                                    ),
                                    html.Div(id="tank-height-error"),
                                ],
                                width=6,
                            ),
                            dbc.Col(
                                [
                                    html.Label("Target Power (kW)"),
                                    dcc.Slider(
                                        id="target-power-slider",
                                        min=75,
                                        max=600,
                                        step=25,
                                        value=530,
                                        marks={i: str(i) for i in range(75, 601, 100)},
                                        tooltip={"placement": "bottom", "always_visible": True},
                                    ),
                                    html.Div(id="target-power-error"),
                                ],
                                width=6,
                            ),
                        ],
                        className="mb-3",
                    ),
                ]
            ),
        ],
        className="mb-4",
    )


def create_advanced_controls_tab():
    """Create the Advanced Controls tab with all missing backend endpoints, each with its own output display area."""
    return dbc.Container(
        [
            html.H4("Advanced Controls & Diagnostics", className="mb-3 text-primary"),
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Button("Single Step", id="btn-step", color="info", className="mb-2", n_clicks=0),
                            html.Div(id="output-step", className="mb-2 small text-monospace"),
                            dbc.Button(
                                "Trigger Pulse",
                                id="btn-trigger-pulse",
                                color="warning",
                                className="mb-2 ms-2",
                                n_clicks=0,
                            ),
                            html.Div(id="output-trigger-pulse", className="mb-2 small text-monospace"),
                            dbc.InputGroup(
                                [
                                    dbc.Input(
                                        id="input-set-load", type="number", placeholder="Set Load Torque (Nm)", min=0
                                    ),
                                    dbc.Button("Set Load", id="btn-set-load", color="secondary", n_clicks=0),
                                ],
                                className="mb-2",
                            ),
                            html.Div(id="output-set-load", className="mb-2 small text-monospace"),
                            dbc.Button(
                                "Trigger Emergency Stop",
                                id="btn-emergency-stop",
                                color="danger",
                                className="mb-2",
                                n_clicks=0,
                            ),
                            html.Div(id="output-emergency-stop", className="mb-2 small text-monospace"),
                            dbc.Form(
                                [
                                    dbc.Checkbox(id="input-h1-active", className="me-1"),
                                    dbc.Label("H1 Active", html_for="input-h1-active", className="me-2"),
                                    dbc.Input(
                                        id="input-h1-fraction",
                                        type="number",
                                        min=0,
                                        max=1,
                                        step=0.01,
                                        placeholder="Bubble Fraction",
                                        className="me-2",
                                        style={"width": "150px", "display": "inline-block"},
                                    ),
                                    dbc.Input(
                                        id="input-h1-drag",
                                        type="number",
                                        min=0,
                                        max=1,
                                        step=0.01,
                                        placeholder="Drag Reduction",
                                        className="me-2",
                                        style={"width": "150px", "display": "inline-block"},
                                    ),
                                    dbc.Button(
                                        "Set H1 Nanobubbles", id="btn-h1-nanobubbles", color="primary", n_clicks=0
                                    ),
                                ],
                                className="mb-2 d-flex align-items-center",
                            ),
                            html.Div(id="output-h1-nanobubbles", className="mb-2 small text-monospace"),
                            dbc.InputGroup(
                                [
                                    dbc.Select(
                                        id="select-control-mode",
                                        options=[
                                            {"label": "Normal", "value": "normal"},
                                            {"label": "Manual", "value": "manual"},
                                            {"label": "Emergency", "value": "emergency"},
                                            {"label": "Paused", "value": "paused"},
                                        ],
                                        value="normal",
                                        style={"width": "200px"},
                                    ),
                                    dbc.Button(
                                        "Set Control Mode", id="btn-set-control-mode", color="secondary", n_clicks=0
                                    ),
                                ],
                                className="mb-2",
                            ),
                            html.Div(id="output-set-control-mode", className="mb-2 small text-monospace"),
                        ],
                        width=6,
                    ),
                    dbc.Col(
                        [
                            dbc.Button(
                                "Show Input Data",
                                id="btn-show-input-data",
                                color="secondary",
                                className="mb-2",
                                n_clicks=0,
                            ),
                            html.Div(id="output-show-input-data", className="mb-2 small text-monospace"),
                            dbc.Button(
                                "Show Output Data",
                                id="btn-show-output-data",
                                color="secondary",
                                className="mb-2 ms-2",
                                n_clicks=0,
                            ),
                            html.Div(id="output-show-output-data", className="mb-2 small text-monospace"),
                            dbc.Button(
                                "Show Energy Balance",
                                id="btn-show-energy-balance",
                                color="secondary",
                                className="mb-2 ms-2",
                                n_clicks=0,
                            ),
                            html.Div(id="output-show-energy-balance", className="mb-2 small text-monospace"),
                            dbc.Button(
                                "Show Enhanced Performance",
                                id="btn-show-enhanced-performance",
                                color="secondary",
                                className="mb-2",
                                n_clicks=0,
                            ),
                            html.Div(id="output-show-enhanced-performance", className="mb-2 small text-monospace"),
                            dbc.Button(
                                "Show Fluid Properties",
                                id="btn-show-fluid-properties",
                                color="secondary",
                                className="mb-2 ms-2",
                                n_clicks=0,
                            ),
                            html.Div(id="output-show-fluid-properties", className="mb-2 small text-monospace"),
                            dbc.Button(
                                "Show Thermal Properties",
                                id="btn-show-thermal-properties",
                                color="secondary",
                                className="mb-2 ms-2",
                                n_clicks=0,
                            ),
                            html.Div(id="output-show-thermal-properties", className="mb-2 small text-monospace"),
                        ],
                        width=6,
                    ),
                ]
            ),
        ],
        fluid=True,
    )


# Main App Layout
app.layout = dbc.Container(
    [
        # --- Custom CSS Link ---
        html.Link(rel="stylesheet", href="/assets/kpp_dashboard.css"),
        # --- Data Stores (always visible) ---
        dcc.Store(
            id="simulation-data-store",
            data={
                "time": 0.0,
                "power": 0.0,
                "torque": 0.0,
                "power_output": 0.0,
                "overall_efficiency": 0.0,
                "chain_tension": 0.0,
                "flywheel_speed_rpm": 0.0,
                "chain_speed_rpm": 0.0,
                "clutch_engaged": False,
                "pulse_count": 0,
                "tank_pressure": 0.0,
                "electrical_engagement": False,
                "status": "stopped",
                "health": "initializing",
                "timestamp": 0.0,
                "frame_id": 0,
                "components": {},
                "grid_power_output": 0.0,
            },
        ),
        dcc.Store(id="parameters-store"),
        dcc.Store(id="last-parameters-store"),
        dcc.Store(id="parameter-presets-store", data={}),
        dcc.Store(id="chart-data-store", data={"time": [], "power": [], "torque": [], "efficiency": []}),
        dcc.Store(id="notification-store", data={"show": False, "message": "", "color": "danger"}),
        # --- Error and Health Alerts (always visible) ---
        html.Div(id="error-banner", style={"display": "none"}),
        dbc.Alert(id="system-health-alert", color="success", is_open=False, dismissable=True, className="mb-2"),
        # Preset selector UI
        html.Div(
            [
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                html.Label("Parameter Preset:"),
                                dcc.Dropdown(
                                    id="preset-dropdown",
                                    options=[],
                                    value=None,
                                    placeholder="Select preset",
                                    style={"width": 220, "display": "inline-block"},
                                ),
                                dbc.Button(
                                    "Save Preset", id="save-preset-btn", color="primary", size="sm", className="ms-2"
                                ),
                                dbc.Button(
                                    "Delete Preset", id="delete-preset-btn", color="danger", size="sm", className="ms-2"
                                ),
                            ],
                            width=8,
                        ),
                    ],
                    className="mb-2",
                ),
            ]
        ),
        # Synchronized real-time interval (30 FPS for smooth animations)
        dcc.Interval(
            id="interval-component", interval=5000, n_intervals=0
        ),  # 5 Hz for stable performance (reduced from 1 Hz)
        dcc.Interval(id="realtime-interval", interval=5000, n_intervals=0),  # 5 second updates (reduced from 1 second)
        # Layout components
        create_header(),
        create_control_panel(),
        create_metrics_cards(),
        create_metric_selector(),
        create_charts_section(),
        create_basic_parameters_panel(),
        # --- Fixed Advanced Parameters Panel (always visible) ---
        html.Hr(),
        html.H4("Advanced Parameters", className="text-primary"),
        create_advanced_parameters_panel(),
        # --- Fixed Physics Controls Panel (always visible) ---
        html.Hr(),
        html.H4("Enhanced Physics Controls", className="text-primary"),
        create_physics_controls_panel(),
        # --- Fixed System Overview Panel (always visible) ---
        html.Hr(),
        html.H4("System Overview", className="text-primary"),
        create_system_overview_panel(),
        # --- Advanced Controls (always visible) ---
        html.Hr(),
        html.H4("Advanced Controls", className="text-primary"),
        create_advanced_controls_tab(),
        # Footer
        html.Hr(),
        html.Footer(
            [
                html.P(
                    [
                        "KPP Simulator Dashboard v2.0 | ",
                        html.A("Documentation", href="#", target="_blank"),
                        " | Built with Plotly Dash",
                    ],
                    className="text-center text-muted",
                )
            ]
        ),
        # --- Notification Components (always visible) ---
        dbc.Toast(
            id="notification-toast",
            header="Notification",
            is_open=False,
            dismissable=True,
            icon="danger",
            duration=6000,
            style={"position": "fixed", "top": 20, "right": 20, "minWidth": 350, "zIndex": 9999},
        ),
    ],
    fluid=True,
)

# Callbacks


@app.callback(
    Output("chart-data-store", "data"), [Input("simulation-data-store", "data")], State("chart-data-store", "data")
)
def update_chart_data(new_data, current_chart_data):
    """Update chart data store with new simulation data"""
    if not new_data or not current_chart_data:
        return {"time": [], "power": [], "torque": [], "efficiency": []}

    # Only append data if we have valid time and it's newer than last point
    current_time = new_data.get("time", 0)
    if current_time > 0:
        # Check if this is a new data point
        if not current_chart_data["time"] or current_time > current_chart_data["time"][-1]:
            # Append new data point
            current_chart_data["time"].append(current_time)
            current_chart_data["power"].append(new_data.get("power", 0))
            current_chart_data["torque"].append(new_data.get("torque", 0))
            current_chart_data["efficiency"].append(
                new_data.get("overall_efficiency", 0) * 100
            )  # Convert to percentage

    # Keep only last 100 points for performance
    max_points = 100
    for key in current_chart_data:
        if len(current_chart_data[key]) > max_points:
            current_chart_data[key] = current_chart_data[key][-max_points:]

    return current_chart_data


@app.callback(
    Output("power-torque-chart", "figure"), [Input("chart-data-store", "data"), Input("metric-selector", "value")]
)
def update_power_torque_chart(chart_data, selected_metrics):
    """Update the power and torque chart based on selected metrics"""
    if not chart_data or not chart_data.get("time"):
        fig = go.Figure()
        fig.add_annotation(text="No data available", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
        fig.update_layout(title="Power & Torque vs Time", xaxis_title="Time (s)", yaxis_title="Value")
        return fig

    fig = go.Figure()
    if "power" in selected_metrics:
        fig.add_trace(
            go.Scatter(
                x=chart_data["time"],
                y=chart_data["power"],
                mode="lines",
                name="Power (W)",
                line=dict(color="blue", width=2),
            )
        )
    if "torque" in selected_metrics:
        fig.add_trace(
            go.Scatter(
                x=chart_data["time"],
                y=chart_data["torque"],
                mode="lines",
                name="Torque (Nm)",
                line=dict(color="green", width=2),
                yaxis="y2",
            )
        )
    fig.update_layout(
        title="Power & Torque vs Time",
        xaxis_title="Time (s)",
        yaxis=dict(title="Power (W)", side="left"),
        yaxis2=dict(title="Torque (Nm)", side="right", overlaying="y"),
        legend=dict(x=0.01, y=0.99),
        height=400,
    )
    return fig


@app.callback(
    Output("efficiency-chart", "figure"), [Input("chart-data-store", "data"), Input("metric-selector", "value")]
)
def update_efficiency_chart(chart_data, selected_metrics):
    """Update the efficiency chart based on selected metrics"""
    if not chart_data or not chart_data.get("time") or "efficiency" not in selected_metrics:
        fig = go.Figure()
        fig.add_annotation(
            text="No data available or not selected", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False
        )
        fig.update_layout(title="System Efficiency", xaxis_title="Time (s)", yaxis_title="Efficiency (%)")
        return fig
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=chart_data["time"],
            y=chart_data["efficiency"],
            mode="lines",
            name="Overall Efficiency",
            line=dict(color="orange", width=2),
            fill="tonexty",
        )
    )
    fig.update_layout(
        title="System Efficiency vs Time",
        xaxis_title="Time (s)",
        yaxis_title="Efficiency (%)",
        yaxis=dict(range=[0, 100]),
        height=400,
    )
    return fig


# Removed duplicate callback - connection status is now handled by update_status_indicators


# --- Main callback for WebSocket data and parameter updates ---
@app.callback(
    [
        Output("parameters-store", "data"),
        Output("last-parameters-store", "data"),
        Output("notification-store", "data"),
        Output("parameter-presets-store", "data"),
        Output("preset-dropdown", "options"),
        Output("preset-dropdown", "value"),
    ],
    [
        Input("interval-component", "n_intervals"),
        Input("preset-dropdown", "value"),
        Input("submit-advanced-params-btn", "n_clicks"),
        Input("submit-physics-controls-btn", "n_clicks"),
        Input("save-preset-btn", "n_clicks"),
        Input("delete-preset-btn", "n_clicks"),
    ],
    [
        State("parameter-presets-store", "data"),
        State("parameters-store", "data"),
        State("floater-mass-slider", "value"),
        State("floater-area-slider", "value"),
        State("air-fill-time-slider", "value"),
        State("air-flow-rate-slider", "value"),
        State("jet-efficiency-slider", "value"),
        State("sprocket-radius-slider", "value"),
        State("flywheel-inertia-slider", "value"),
        State("h1-enabled-switch", "value"),
        State("nanobubble-fraction-slider", "value"),
        State("h2-enabled-switch", "value"),
        State("thermal-efficiency-slider", "value"),
        State("water-temp-slider", "value"),
        State("ambient-temp-slider", "value"),
    ],
    prevent_initial_call=False,
)
def unified_param_notification_preset_callback(
    n_intervals,
    preset_value,
    adv_n_clicks,
    physics_n_clicks,
    save_preset,
    delete_preset,
    presets,
    current_params,
    floater_mass,
    floater_area,
    air_fill_time,
    air_flow_rate,
    jet_efficiency,
    sprocket_radius,
    flywheel_inertia,
    h1_enabled,
    nano_frac,
    h2_enabled,
    thermal_efficiency,
    water_temp,
    ambient_temp,
):
    pass

    import dash

    ctx = dash.callback_context
    notification = {"show": False, "message": "", "color": "info"}
    params = dash.no_update
    last_params = dash.no_update
    dash.no_update
    preset_options = dash.no_update
    preset_value_out = dash.no_update

    # Handle parameter submission
    if ctx.triggered and ctx.triggered[0]["prop_id"] == "submit-advanced-params-btn.n_clicks":
        if adv_n_clicks:
            try:
                # Prepare parameters for backend including all enhancements
                backend_params = {
                    "floater_mass_empty": floater_mass,
                    "floater_area": floater_area,
                    "air_fill_time": air_fill_time,
                    "air_flow_rate": air_flow_rate,
                    "jet_efficiency": jet_efficiency,
                    "sprocket_radius": sprocket_radius,
                    "flywheel_inertia": flywheel_inertia,
                    # Enhanced parameters from new controls
                    "pressure_recovery_efficiency": current_params.get("pressure_recovery_efficiency", 0.22),
                    "water_jet_enabled": current_params.get("water_jet_enabled", True),
                    "foc_enabled": current_params.get("foc_enabled", True),
                    "foc_torque_kp": current_params.get("foc_torque_kp", 120.0),
                    "foc_flux_kp": current_params.get("foc_flux_kp", 90.0),
                    "tank_height": current_params.get("tank_height", 25.0),
                    "target_power": current_params.get("target_power", 530000.0),
                }

                # Send to backend using pooled session
                response = http_session.post(f"{BACKEND_URL}/update_params", json=backend_params, timeout=5)
                if response.status_code == 200:
                    notification = {
                        "show": True,
                        "message": "Advanced parameters updated successfully",
                        "color": "success",
                    }
                    params = backend_params
                else:
                    notification = {
                        "show": True,
                        "message": f"Failed to update parameters: {response.text}",
                        "color": "danger",
                    }
            except Exception as e:
                notification = {"show": True, "message": f"Error updating parameters: {e}", "color": "danger"}

    # Handle physics controls submission
    if ctx.triggered and ctx.triggered[0]["prop_id"] == "submit-physics-controls-btn.n_clicks":
        if physics_n_clicks:
            try:
                # Prepare enhanced physics parameters
                physics_params = {
                    # H1 Nanobubble Physics
                    "h1_enabled": h1_enabled,
                    "nanobubble_frac": nano_frac if h1_enabled else 0.0,
                    "drag_reduction": current_params.get("drag_reduction", 0.12),
                    # H2 Thermal Enhancement
                    "h2_enabled": h2_enabled,
                    "thermal_efficiency": thermal_efficiency if h2_enabled else 0.8,
                    "buoyancy_boost": current_params.get("buoyancy_boost", 0.06),
                    # H3 Pulse-Coast Operation
                    "h3_enabled": current_params.get("h3_enabled", True),
                    "pulse_duration": current_params.get("pulse_duration", 2.0),
                    "coast_duration": current_params.get("coast_duration", 1.0),
                    # Environmental
                    "water_temp": water_temp + 273.15,  # Convert to Kelvin for backend
                    "ambient_temp": ambient_temp + 273.15,  # Convert to Kelvin for backend
                }

                # Send to backend using pooled session
                response = http_session.post(f"{BACKEND_URL}/control/enhanced_physics", json=physics_params, timeout=5)
                if response.status_code == 200:
                    notification = {
                        "show": True,
                        "message": "Physics controls updated successfully",
                        "color": "success",
                    }
                    params = physics_params
                else:
                    notification = {
                        "show": True,
                        "message": f"Failed to update physics controls: {response.text}",
                        "color": "danger",
                    }
            except Exception as e:
                notification = {"show": True, "message": f"Error updating physics controls: {e}", "color": "danger"}

    return params, last_params, notification, presets, preset_options, preset_value_out


# --- Callback for simulation control buttons ---
@app.callback(
    [
        Output("start-btn", "disabled"),
        Output("stop-btn", "disabled"),
        Output("pause-btn", "disabled"),
        Output("reset-btn", "disabled"),
    ],
    [
        Input("start-btn", "n_clicks"),
        Input("stop-btn", "n_clicks"),
        Input("pause-btn", "n_clicks"),
        Input("reset-btn", "n_clicks"),
        Input("simulation-data-store", "data"),
    ],  # Add simulation data as input
    prevent_initial_call=True,
)
def handle_simulation_controls(start_clicks, stop_clicks, pause_clicks, reset_clicks, simulation_data):
    pass

    ctx = dash.callback_context
    if not ctx.triggered:
        # Check current simulation status to set initial button states
        if simulation_data:
            status = simulation_data.get("status", "stopped")
            if status == "running":
                return True, False, False, False  # Start disabled, others enabled
            else:
                return False, True, True, True  # Start enabled, others disabled
        return False, True, True, True

    button_id = ctx.triggered[0]["prop_id"].split(".")[0]

    try:
        if button_id == "start-btn":
            response = http_session.post(f"{BACKEND_URL}/start", timeout=10)
            if response.status_code == 200:
                return True, False, False, False  # Start disabled, others enabled
            else:
                print(f"Start button failed: {response.status_code} - {response.text}")
                return False, True, True, True  # Keep start enabled if failed
        elif button_id == "stop-btn":
            response = http_session.post(f"{BACKEND_URL}/stop", timeout=10)
            if response.status_code == 200:
                return False, True, True, True  # Start enabled, others disabled
            else:
                return True, False, False, False  # Keep stop enabled if failed
        elif button_id == "pause-btn":
            response = http_session.post(f"{BACKEND_URL}/pause", timeout=10)
            if response.status_code == 200:
                return False, False, True, False  # Pause disabled, others enabled
            else:
                return True, False, False, False  # Keep pause enabled if failed
        elif button_id == "reset-btn":
            response = http_session.post(f"{BACKEND_URL}/reset", timeout=10)
            if response.status_code == 200:
                return False, True, True, True  # Start enabled, others disabled
            else:
                return True, False, False, False  # Keep reset enabled if failed
    except Exception as e:
        print(f"Error in simulation control: {e}")
        # Return current state based on simulation data
        if simulation_data:
            status = simulation_data.get("status", "stopped")
            if status == "running":
                return True, False, False, False
            else:
                return False, True, True, True

    return False, True, True, True


# --- Callback for action buttons (step, pulse, load, etc.) ---
@app.callback(
    [
        Output("output-step", "children"),
        Output("output-trigger-pulse", "children"),
        Output("output-set-load", "children"),
        Output("output-emergency-stop", "children"),
        Output("output-h1-nanobubbles", "children"),
        Output("output-set-control-mode", "children"),
        Output("output-show-input-data", "children"),
        Output("output-show-output-data", "children"),
        Output("output-show-energy-balance", "children"),
        Output("output-show-enhanced-performance", "children"),
        Output("output-show-fluid-properties", "children"),
        Output("output-show-thermal-properties", "children"),
    ],
    [
        Input("btn-step", "n_clicks"),
        Input("btn-trigger-pulse", "n_clicks"),
        Input("btn-set-load", "n_clicks"),
        Input("btn-emergency-stop", "n_clicks"),
        Input("btn-h1-nanobubbles", "n_clicks"),
        Input("btn-set-control-mode", "n_clicks"),
        Input("btn-show-input-data", "n_clicks"),
        Input("btn-show-output-data", "n_clicks"),
        Input("btn-show-energy-balance", "n_clicks"),
        Input("btn-show-enhanced-performance", "n_clicks"),
        Input("btn-show-fluid-properties", "n_clicks"),
        Input("btn-show-thermal-properties", "n_clicks"),
    ],
    [State("input-set-load", "value"), State("select-control-mode", "value"), State("simulation-data-store", "data")],
    prevent_initial_call=True,
)
def handle_action_outputs(
    step_clicks,
    pulse_clicks,
    load_clicks,
    emergency_clicks,
    h1_clicks,
    mode_clicks,
    input_clicks,
    output_clicks,
    energy_clicks,
    performance_clicks,
    fluid_clicks,
    thermal_clicks,
    load_value,
    control_mode,
    sim_data,
):
    import requests

    ctx = dash.callback_context
    if not ctx.triggered:
        return [""] * 12

    button_id = ctx.triggered[0]["prop_id"].split(".")[0]

    try:
        if button_id == "btn-step":
            response = requests.post(f"{BACKEND_URL}/step")
            return f"Step executed: {response.json()}", "", "", "", "", "", "", "", "", "", "", ""

        elif button_id == "btn-trigger-pulse":
            response = requests.post(f"{BACKEND_URL}/trigger_pulse")
            return "", f"Pulse triggered: {response.json()}", "", "", "", "", "", "", "", "", "", ""

        elif button_id == "btn-set-load":
            if load_value:
                response = requests.post(f"{BACKEND_URL}/set_load", json={"load_torque": float(load_value)})
                return "", "", f"Load set to {load_value} Nm: {response.json()}", "", "", "", "", "", "", "", "", ""
            return "", "", "Please enter a load value", "", "", "", "", "", "", "", "", ""

        elif button_id == "btn-emergency-stop":
            response = requests.post(f"{BACKEND_URL}/control/trigger_emergency_stop")
            return "", "", "", f"Emergency stop triggered: {response.json()}", "", "", "", "", "", "", "", ""

        elif button_id == "btn-h1-nanobubbles":
            response = requests.post(f"{BACKEND_URL}/control/h1_nanobubbles", json={"active": True})
            return "", "", "", "", f"H1 nanobubbles activated: {response.json()}", "", "", "", "", "", "", ""

        elif button_id == "btn-set-control-mode":
            if control_mode:
                response = requests.post(f"{BACKEND_URL}/control/set_control_mode", json={"mode": control_mode})
                return (
                    "",
                    "",
                    "",
                    "",
                    "",
                    f"Control mode set to {control_mode}: {response.json()}",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                )
            return "", "", "", "", "", "Please select a control mode", "", "", "", "", "", ""

        elif button_id == "btn-show-input-data":
            response = requests.get(f"{BACKEND_URL}/inspect/input_data")
            return "", "", "", "", "", "", f"Input data: {response.json()}", "", "", "", "", ""

        elif button_id == "btn-show-output-data":
            response = requests.get(f"{BACKEND_URL}/inspect/output_data")
            return "", "", "", "", "", "", "", f"Output data: {response.json()}", "", "", "", ""

        elif button_id == "btn-show-energy-balance":
            response = requests.get(f"{BACKEND_URL}/data/energy_balance")
            return "", "", "", "", "", "", "", "", f"Energy balance: {response.json()}", "", "", ""

        elif button_id == "btn-show-enhanced-performance":
            response = requests.get(f"{BACKEND_URL}/data/enhanced_performance")
            return "", "", "", "", "", "", "", "", "", f"Enhanced performance: {response.json()}", "", ""

        elif button_id == "btn-show-fluid-properties":
            response = requests.get(f"{BACKEND_URL}/data/fluid_properties")
            return "", "", "", "", "", "", "", "", "", "", f"Fluid properties: {response.json()}", ""

        elif button_id == "btn-show-thermal-properties":
            response = requests.get(f"{BACKEND_URL}/data/thermal_properties")
            return "", "", "", "", "", "", "", "", "", "", "", f"Thermal properties: {response.json()}"

    except Exception as e:
        error_msg = f"Error: {str(e)}"
        if button_id == "btn-step":
            return error_msg, "", "", "", "", "", "", "", "", "", "", ""
        elif button_id == "btn-trigger-pulse":
            return "", error_msg, "", "", "", "", "", "", "", "", "", ""
        elif button_id == "btn-set-load":
            return "", "", error_msg, "", "", "", "", "", "", "", "", ""
        elif button_id == "btn-emergency-stop":
            return "", "", "", error_msg, "", "", "", "", "", "", "", ""
        elif button_id == "btn-h1-nanobubbles":
            return "", "", "", "", error_msg, "", "", "", "", "", "", ""
        elif button_id == "btn-set-control-mode":
            return "", "", "", "", "", error_msg, "", "", "", "", "", ""
        elif button_id == "btn-show-input-data":
            return "", "", "", "", "", "", error_msg, "", "", "", "", ""
        elif button_id == "btn-show-output-data":
            return "", "", "", "", "", "", "", error_msg, "", "", "", ""
        elif button_id == "btn-show-energy-balance":
            return "", "", "", "", "", "", "", "", error_msg, "", "", ""
        elif button_id == "btn-show-enhanced-performance":
            return "", "", "", "", "", "", "", "", "", error_msg, "", ""
        elif button_id == "btn-show-fluid-properties":
            return "", "", "", "", "", "", "", "", "", "", error_msg, ""
        elif button_id == "btn-show-thermal-properties":
            return "", "", "", "", "", "", "", "", "", "", "", error_msg

    return [""] * 12


# --- Callback for basic parameters validation ---
@app.callback(
    [
        Output("basic-floater-mass-error", "children"),
        Output("basic-floater-area-error", "children"),
        Output("basic-air-fill-time-error", "children"),
        Output("basic-air-flow-rate-error", "children"),
    ],
    [
        Input("num-floaters-slider", "value"),
        Input("floater-volume-slider", "value"),
        Input("air-pressure-slider", "value"),
        Input("pulse-interval-slider", "value"),
    ],
    prevent_initial_call=True,
)
def validate_basic_parameters(num_floaters, floater_volume, air_pressure, pulse_interval):
    errors = ["", "", "", ""]

    # Validate num_floaters
    if num_floaters and (num_floaters < 4 or num_floaters > 100):
        errors[0] = "Number of floaters must be between 4 and 100"

    # Validate floater_volume
    if floater_volume and (floater_volume < 0.1 or floater_volume > 1.0):
        errors[1] = "Floater volume must be between 0.1 and 1.0 m³"

    # Validate air_pressure
    if air_pressure and (air_pressure < 1.0 or air_pressure > 10.0):
        errors[2] = "Air pressure must be between 1.0 and 10.0 bar"

    # Validate pulse_interval
    if pulse_interval and (pulse_interval < 0.5 or pulse_interval > 10.0):
        errors[3] = "Pulse interval must be between 0.5 and 10.0 seconds"

    return errors


# --- Callback for advanced parameters validation ---
@app.callback(
    [
        Output("advanced-floater-mass-error", "children"),
        Output("advanced-floater-area-error", "children"),
        Output("advanced-air-fill-time-error", "children"),
        Output("advanced-air-flow-rate-error", "children"),
        Output("advanced-jet-efficiency-error", "children"),
        Output("advanced-sprocket-radius-error", "children"),
        Output("advanced-flywheel-inertia-error", "children"),
    ],
    [
        Input("floater-mass-slider", "value"),
        Input("floater-area-slider", "value"),
        Input("air-fill-time-slider", "value"),
        Input("air-flow-rate-slider", "value"),
        Input("jet-efficiency-slider", "value"),
        Input("sprocket-radius-slider", "value"),
        Input("flywheel-inertia-slider", "value"),
    ],
    prevent_initial_call=True,
)
def validate_advanced_parameters(
    floater_mass, floater_area, air_fill_time, air_flow_rate, jet_efficiency, sprocket_radius, flywheel_inertia
):
    errors = ["", "", "", "", "", "", ""]

    # Validate floater_mass
    if floater_mass and (floater_mass < 5.0 or floater_mass > 50.0):
        errors[0] = "Floater mass must be between 5.0 and 50.0 kg"

    # Validate floater_area
    if floater_area and (floater_area < 0.01 or floater_area > 0.1):
        errors[1] = "Floater area must be between 0.01 and 0.1 m²"

    # Validate air_fill_time
    if air_fill_time and (air_fill_time < 0.1 or air_fill_time > 2.0):
        errors[2] = "Air fill time must be between 0.1 and 2.0 seconds"

    # Validate air_flow_rate
    if air_flow_rate and (air_flow_rate < 0.1 or air_flow_rate > 2.0):
        errors[3] = "Air flow rate must be between 0.1 and 2.0 m³/s"

    # Validate jet_efficiency
    if jet_efficiency and (jet_efficiency < 0.5 or jet_efficiency > 0.95):
        errors[4] = "Jet efficiency must be between 0.5 and 0.95"

    # Validate sprocket_radius
    if sprocket_radius and (sprocket_radius < 0.1 or sprocket_radius > 1.0):
        errors[5] = "Sprocket radius must be between 0.1 and 1.0 m"

    # Validate flywheel_inertia
    if flywheel_inertia and (flywheel_inertia < 10.0 or flywheel_inertia > 200.0):
        errors[6] = "Flywheel inertia must be between 10.0 and 200.0 kg·m²"

    return errors


# --- Callback for physics controls validation ---
@app.callback(
    [
        Output("h1-switch-error", "children"),
        Output("nanobubble-fraction-error", "children"),
        Output("h2-switch-error", "children"),
        Output("thermal-efficiency-error", "children"),
        Output("water-temp-error", "children"),
        Output("ambient-temp-error", "children"),
    ],
    [
        Input("h1-enabled-switch", "value"),
        Input("nanobubble-fraction-slider", "value"),
        Input("h2-enabled-switch", "value"),
        Input("thermal-efficiency-slider", "value"),
        Input("water-temp-slider", "value"),
        Input("ambient-temp-slider", "value"),
    ],
    prevent_initial_call=True,
)
def validate_physics_controls(h1_enabled, nano_frac, h2_enabled, thermal_efficiency, water_temp, ambient_temp):
    errors = ["", "", "", "", "", ""]

    # Validate nanobubble fraction
    if h1_enabled and nano_frac and (nano_frac < 0.0 or nano_frac > 1.0):
        errors[1] = "Nanobubble fraction must be between 0.0 and 1.0"

    # Validate thermal efficiency
    if h2_enabled and thermal_efficiency and (thermal_efficiency < 0.0001 or thermal_efficiency > 0.01):
        errors[3] = "Thermal efficiency must be between 0.0001 and 0.01"

    # Validate water temperature
    if water_temp and (water_temp < 0.0 or water_temp > 100.0):
        errors[4] = "Water temperature must be between 0.0 and 100.0 °C"

    # Validate ambient temperature
    if ambient_temp and (ambient_temp < 0.0 or ambient_temp > 100.0):
        errors[5] = "Ambient temperature must be between 0.0 and 100.0 °C"

    return errors


# TEMPORARILY DISABLED - Add a new callback to fetch real-time data from Flask server
# @app.callback(
#     Output("simulation-data-store", "data"),
#     [Input("realtime-interval", "n_intervals")],
#     prevent_initial_call=False
# )
def fetch_realtime_data_DISABLED(n_intervals):
    """Fetch real-time simulation data from Flask server"""
    try:
        # Get the latest simulation status from Flask with shorter timeout
        response = requests.get(f"{BACKEND_URL}/status", timeout=2)
        if response.status_code == 200:
            status_data = response.json()

            # Get real-time data from the latest queue entry with shorter timeout
            response2 = requests.get(f"{BACKEND_URL}/data/live", timeout=2)
            if response2.status_code == 200:
                live_data = response2.json()
                if live_data.get("data") and len(live_data["data"]) > 0:
                    # Get the latest data point
                    latest = live_data["data"][-1]

                    # Map the data to the format expected by the UI
                    simulation_data = {
                        "time": latest.get("time", 0.0),
                        "power": latest.get("power", 0.0),
                        "torque": latest.get("torque", 0.0),
                        "power_output": latest.get("power", 0.0),  # Alias for power
                        "overall_efficiency": latest.get("overall_efficiency", 0.0),
                        "chain_tension": latest.get("chain_tension", 0.0),
                        "flywheel_speed_rpm": latest.get("flywheel_speed_rpm", 0.0),
                        "chain_speed_rpm": latest.get("chain_speed_rpm", 0.0),
                        "clutch_engaged": latest.get("clutch_engaged", False),
                        "pulse_count": latest.get("pulse_count", 0),
                        "tank_pressure": latest.get("tank_pressure", 0.0),
                        "status": "running" if status_data.get("simulation_engine") == "running" else "stopped",
                        "health": status_data.get("status", "unknown"),
                        "components": status_data.get("components", {}),
                        "timestamp": latest.get("time", 0.0),
                    }

                    return simulation_data

        # Fallback: return current status if live data unavailable
        return {
            "time": 0.0,
            "power": 0.0,
            "torque": 0.0,
            "power_output": 0.0,
            "overall_efficiency": 0.0,
            "status": "disconnected",
            "health": "unknown",
        }

    except requests.exceptions.Timeout:
        # Handle timeout specifically to avoid hanging
        return {
            "time": 0.0,
            "power": 0.0,
            "torque": 0.0,
            "power_output": 0.0,
            "overall_efficiency": 0.0,
            "status": "timeout",
            "health": "timeout",
        }
    except Exception as e:
        logging.error(f"Error fetching real-time data: {e}")
        return {
            "time": 0.0,
            "power": 0.0,
            "torque": 0.0,
            "power_output": 0.0,
            "overall_efficiency": 0.0,
            "status": "error",
            "health": "error",
            "error": str(e),
        }


# Fix callback to update metrics cards with correct IDs
@app.callback(
    [
        Output("power-value", "children"),
        Output("torque-value", "children"),
        Output("efficiency-value", "children"),
        Output("time-value", "children"),
        Output("grid-power", "children"),
        Output("flywheel-rpm", "children"),
        Output("electrical-eff", "children"),
        Output("pulse-count", "children"),
    ],
    [Input("simulation-data-store", "data")],
    prevent_initial_call=False,
)
def update_metrics_cards(simulation_data):
    """Update the metrics cards with real-time data"""
    if not simulation_data:
        return "0.0 kW", "0.0 Nm", "0.0%", "0.0 s", "Grid: 0 kW", "RPM: 0", "Electrical: 0%", "Pulses: 0"

    try:
        power = simulation_data.get("power", 0.0) / 1000.0  # Convert W to kW
        torque = simulation_data.get("torque", 0.0)
        efficiency = simulation_data.get("overall_efficiency", 0.0) * 100  # Convert to percentage
        time_val = simulation_data.get("time", 0.0)
        flywheel_rpm = simulation_data.get("flywheel_speed_rpm", 0.0)
        pulse_count_val = simulation_data.get("pulse_count", 0)

        return (
            f"{power:.1f} kW",
            f"{torque:.1f} Nm",
            f"{efficiency:.1f}%",
            f"{time_val:.1f} s",
            f"Grid: {power:.1f} kW",  # Same as power for now
            f"RPM: {flywheel_rpm:.0f}",
            f"Electrical: {efficiency:.1f}%",  # Same as overall for now
            f"Pulses: {pulse_count_val}",
        )
    except Exception as e:
        logging.error(f"Error updating metrics: {e}")
        return "Error", "Error", "Error", "Error", "Error", "Error", "Error", "Error"


# Add callback to update system status indicators
@app.callback(
    [Output("simulation-status", "children"), Output("connection-status", "children")],
    [Input("simulation-data-store", "data")],
    prevent_initial_call=False,
)
def update_status_indicators(simulation_data):
    """Update simulation and connection status indicators"""
    if not simulation_data:
        return (
            html.Span("Stopped", className="status-indicator status-stopped"),
            html.Span("Disconnected", className="status-indicator status-stopped"),
        )

    # Update simulation status
    status = simulation_data.get("status", "unknown")
    if status == "running":
        sim_indicator = html.Span("Running", className="status-indicator status-running")
    elif status == "stopped":
        sim_indicator = html.Span("Stopped", className="status-indicator status-stopped")
    elif status == "error":
        sim_indicator = html.Span("Error", className="status-indicator status-stopped")
    elif status == "disconnected":
        sim_indicator = html.Span("Disconnected", className="status-indicator status-stopped")
    elif status == "timeout":
        sim_indicator = html.Span("Timeout", className="status-indicator status-stopped")
    elif status == "initializing":
        sim_indicator = html.Span("Initializing", className="status-indicator status-connecting")
    elif status == "success":
        sim_indicator = html.Span("Success", className="status-indicator status-running")
    else:
        sim_indicator = html.Span("Connecting", className="status-indicator status-connecting")

    # Update connection status
    health = simulation_data.get("health", "unknown")
    if health in ["healthy", "synchronized", "fallback_websocket"] or status == "running":
        conn_indicator = html.Span("Connected", className="status-indicator status-running")
    elif health in ["error", "timeout"]:
        conn_indicator = html.Span("Error", className="status-indicator status-stopped")
    elif health in ["no_connection", "unknown"]:
        conn_indicator = html.Span("Disconnected", className="status-indicator status-stopped")
    elif health == "initializing":
        conn_indicator = html.Span("Initializing", className="status-indicator status-connecting")
    elif health == "running":  # Handle running as health value
        conn_indicator = html.Span("Connected", className="status-indicator status-running")
    else:
        conn_indicator = html.Span("Connecting", className="status-indicator status-connecting")

    return sim_indicator, conn_indicator


# REMOVED CONFLICTING CALLBACK - Button states are now controlled by handle_simulation_controls() only


# WebSocket-based real-time data fetching - FIXED VERSION
@app.callback(
    Output("simulation-data-store", "data"), [Input("realtime-interval", "n_intervals")], prevent_initial_call=True
)
def fetch_synchronized_data(n_intervals):
    """Fetch real-time simulation data with rate limiting to prevent resource exhaustion"""
    global _cached_data

    # Initialize master clock connection on first call
    if n_intervals == 1:
        sync_data_manager.start_background_connection()
        logging.info("Starting synchronized data connection to master clock")

    # ADDED: Periodic memory cleanup to prevent leaks
    if n_intervals % 60 == 0:  # Every 60 seconds
        cleanup_memory()

    # ADDED: Rate limiting to prevent ERR_INSUFFICIENT_RESOURCES
    if should_throttle_request():
        # Return cached data if we're being throttled
        with _cache_lock:
            if _cached_data is not None:
                return _cached_data

    try:
        # Get latest synchronized data
        if sync_data_manager.connected:
            # Use synchronized data from master clock
            synchronized_data = sync_data_manager.get_latest_data()

            # Log successful sync occasionally for monitoring
            if n_intervals % 300 == 0:  # Every 10 seconds at 1 Hz
                logging.info(
                    f"Synchronized data: t={synchronized_data['time']:.1f}s, "
                    f"P={synchronized_data['power']:.0f}W, "
                    f"frame_id={synchronized_data.get('frame_id', 0)}"
                )

            # Cache the data for throttling
            with _cache_lock:
                _cached_data = synchronized_data

            return synchronized_data

        # Fallback to WebSocket server if master clock not available
        response = requests.get("http://localhost:9101/state", timeout=0.5)
        if response.status_code == 200:
            ws_data = response.json()

            if ws_data.get("status") == "success":
                kpp_data = ws_data.get("simulation_data", {})

                if kpp_data:
                    # Map to expected format
                    fallback_data = {
                        "time": kpp_data.get("time", 0.0),
                        "power": kpp_data.get("power", 0.0),
                        "torque": kpp_data.get("torque", 0.0),
                        "power_output": kpp_data.get("grid_power", kpp_data.get("power", 0.0)),
                        "overall_efficiency": kpp_data.get("overall_efficiency", kpp_data.get("efficiency", 0.0)),
                        "chain_tension": kpp_data.get("chain_tension", 0.0),
                        "flywheel_speed_rpm": kpp_data.get("flywheel_speed", 0.0),
                        "chain_speed_rpm": kpp_data.get("chain_speed_rpm", 0.0),
                        "clutch_engaged": kpp_data.get("clutch_engaged", False),
                        "pulse_count": kpp_data.get("pulse_count", 0),
                        "tank_pressure": kpp_data.get("tank_pressure", 0.0),
                        "electrical_engagement": kpp_data.get("electrical_engagement", False),
                        "status": kpp_data.get(
                            "status", "success"
                        ),  # Use 'success' if WebSocket response is successful
                        "health": "fallback_websocket",  # Indicates fallback mode
                        "timestamp": kpp_data.get("time", 0.0),
                        "components": {},
                        "grid_power_output": kpp_data.get("grid_power", 0.0),
                    }

                    if n_intervals % 300 == 0:  # Every 10 seconds at 30 FPS
                        logging.warning(f"Using fallback WebSocket data: t={fallback_data['time']:.1f}s")

                    return fallback_data

        # No data available from any source
        return {
            "time": 0.0,
            "power": 0.0,
            "torque": 0.0,
            "power_output": 0.0,
            "overall_efficiency": 0.0,
            "status": "disconnected",
            "health": "no_connection",
            "timestamp": time.time(),
            "components": {},
            "grid_power_output": 0.0,
        }

    except Exception as e:
        # Log errors but don't crash
        if n_intervals % 300 == 0:  # Every 10 seconds at 30 FPS
            logging.warning(f"Data fetch error: {e}")

        return {
            "time": 0.0,
            "power": 0.0,
            "torque": 0.0,
            "power_output": 0.0,
            "overall_efficiency": 0.0,
            "status": "error",
            "health": "error",
            "timestamp": time.time(),
            "error": str(e),
            "components": {},
            "grid_power_output": 0.0,
        }


from simple_browser_monitor import init_simple_browser_monitor

# Initialize browser monitoring (runs on port 9104 by default)
browser_monitor = init_simple_browser_monitor(port=9104)

# Inject the monitoring script into the Dash app's HTML template
app.index_string = app.index_string.replace(
    "</head>", f"<script>{browser_monitor.get_monitoring_script()}</script></head>"
)

if __name__ == "__main__":
    import logging

    logging.info("Starting Dash app on http://localhost:9103 ...")
    app.run(debug=True, host="0.0.0.0", port=9103)
