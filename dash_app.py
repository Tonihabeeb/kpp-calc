#!/usr/bin/env python3
"""
KPP Simulator Dash Application
Main entry point for the Plotly Dash frontend
"""

import dash
from dash import dcc, html, Input, Output, State, callback
import dash_bootstrap_components as dbc
import plotly.graph_objs as go
import plotly.express as px
import pandas as pd
import json
import time
import queue
from datetime import datetime
import logging
import requests
from dash_extensions import WebSocket
from dash.exceptions import PreventUpdate
# import dash_daq as daq  # Only needed if actually used in the rendered UI

# Import our existing simulation engine
from simulation.engine import SimulationEngine
from config.parameter_schema import get_default_parameters, validate_parameters_batch

# Configure logging
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s in %(module)s: %(message)s')

# Initialize Dash app with Bootstrap theme
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "KPP Simulator Dashboard"

# Global simulation engine instance
# We'll embed the engine directly for optimal performance
sim_engine = None
default_params = get_default_parameters()

# Set the backend API URL at the top of the file for all requests
BACKEND_URL = "http://localhost:5001"

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

# Layout Components
def create_header():
    """Create the main header section"""
    return dbc.Navbar(
        dbc.Container([
            dbc.Row([
                dbc.Col([
                    html.Img(src="/assets/kpp-logo.png", height="40px", className="me-2") if False else None,
                    dbc.NavbarBrand("KPP Simulator Dashboard", className="ms-2")
                ], width="auto"),
                dbc.Col([
                    html.Div(id="connection-status", className="text-end")
                ], width="auto", className="ms-auto")
            ], align="center", className="w-100")
        ], fluid=True),
        color="primary",
        dark=True,
        className="mb-4"
    )

def create_control_panel():
    """Create the simulation control panel"""
    return dbc.Card([
        dbc.CardHeader(html.H5("Simulation Controls", className="mb-0")),
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    dbc.ButtonGroup([
                        dbc.Button("Start", id="start-btn", color="success", size="sm"),
                        dbc.Button("Pause", id="pause-btn", color="warning", size="sm"),
                        dbc.Button("Stop", id="stop-btn", color="danger", size="sm"),
                        dbc.Button("Reset", id="reset-btn", color="secondary", size="sm")
                    ])
                ], width=6),
                dbc.Col([
                    html.Div(id="simulation-status", className="text-end")
                ], width=6)
            ])
        ])
    ], className="mb-4")

def create_metrics_cards():
    """Create real-time metrics cards with enhanced data"""
    return dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4(id="power-value", children="0 W", className="text-primary"),
                    html.P("Power Output", className="text-muted mb-0"),
                    html.Small(id="grid-power", children="Grid: 0 W", className="text-success")
                ])
            ])
        ], width=3),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4(id="torque-value", children="0 Nm", className="text-success"),
                    html.P("Torque", className="text-muted mb-0"),
                    html.Small(id="flywheel-rpm", children="RPM: 0", className="text-info")
                ])
            ])
        ], width=3),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4(id="efficiency-value", children="0%", className="text-warning"),
                    html.P("Overall Efficiency", className="text-muted mb-0"),
                    html.Small(id="electrical-eff", children="Electrical: 0%", className="text-warning")
                ])
            ])
        ], width=3),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4(id="time-value", children="0 s", className="text-info"),
                    html.P("Simulation Time", className="text-muted mb-0"),
                    html.Small(id="pulse-count", children="Pulses: 0", className="text-secondary")
                ])
            ])
        ], width=3)
    ], className="mb-4")

def create_metric_selector():
    """Create a checklist for selecting which metrics to display on the charts"""
    return dbc.Card([
        dbc.CardHeader("Select Metrics to Display"),
        dbc.CardBody([
            dcc.Checklist(
                id="metric-selector",
                options=[
                    {"label": "Power (W)", "value": "power"},
                    {"label": "Torque (Nm)", "value": "torque"},
                    {"label": "Efficiency (%)", "value": "efficiency"},
                ],
                value=["power", "torque", "efficiency"],
                inline=True,
                inputStyle={"margin-right": "5px", "margin-left": "10px"}
            )
        ])
    ], className="mb-3")

def create_charts_section():
    """Create the main charts section"""
    return dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Power & Torque"),
                dbc.CardBody([
                    dcc.Graph(
                        id="power-torque-chart",
                        figure={
                            "data": [
                                {"x": [], "y": [], "type": "scatter", "mode": "lines", "name": "Power (W)", "line": {"color": "blue", "width": 2}},
                                {"x": [], "y": [], "type": "scatter", "mode": "lines", "name": "Torque (Nm)", "line": {"color": "green", "width": 2}, "yaxis": "y2"}
                            ],
                            "layout": {
                                "title": "Power & Torque vs Time",
                                "xaxis": {"title": "Time (s)"},
                                "yaxis": {"title": "Power (W)", "side": "left"},
                                "yaxis2": {"title": "Torque (Nm)", "side": "right", "overlaying": "y"},
                                "legend": {"x": 0.01, "y": 0.99},
                                "height": 400
                            }
                        },
                        config={"responsive": True},
                        animate=False
                    )
                ])
            ])
        ], width=6),
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("System Efficiency"),
                dbc.CardBody([
                    dcc.Graph(
                        id="efficiency-chart",
                        figure={
                            "data": [
                                {"x": [], "y": [], "type": "scatter", "mode": "lines", "name": "Overall Efficiency", "line": {"color": "orange", "width": 2}, "fill": "tonexty"}
                            ],
                            "layout": {
                                "title": "System Efficiency vs Time",
                                "xaxis": {"title": "Time (s)"},
                                "yaxis": {"title": "Efficiency (%)", "range": [0, 100]},
                                "height": 400
                            }
                        },
                        config={"responsive": True},
                        animate=False
                    )
                ])
            ])
        ], width=6)
    ], className="mb-4")

def create_basic_parameters_panel():
    """Create basic parameters control panel"""
    return dbc.Card([
        dbc.CardHeader(html.H5("Basic Parameters", className="mb-0")),
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    html.Label("Number of Floaters"),
                    dcc.Slider(
                        id="num-floaters-slider",
                        min=4, max=100, step=2, value=8,
                        marks={i: str(i) for i in range(4, 101, 8)},
                        tooltip={"placement": "bottom", "always_visible": True}
                    )
                ], width=6),
                dbc.Col([
                    html.Label("Floater Volume (m³)"),
                    dcc.Slider(
                        id="floater-volume-slider",
                        min=0.1, max=1.0, step=0.1, value=0.3,
                        marks={round(i/10, 1): f"{i/10:.1f}" for i in range(1, 11)},
                        tooltip={"placement": "bottom", "always_visible": True}
                    )
                ], width=6)
            ], className="mb-3"),
            dbc.Row([
                dbc.Col([
                    html.Label("Air Pressure (Pa)"),
                    dcc.Slider(
                        id="air-pressure-slider",
                        min=100000, max=500000, step=50000, value=300000,
                        marks={i: f"{i//1000}k" for i in range(100000, 501000, 100000)},
                        tooltip={"placement": "bottom", "always_visible": True}
                    )
                ], width=6),
                dbc.Col([
                    html.Label("Pulse Interval (s)"),
                    dcc.Slider(
                        id="pulse-interval-slider",
                        min=0.5, max=5.0, step=0.5, value=2.0,
                        marks={i/2: f"{i/2}" for i in range(1, 11)},
                        tooltip={"placement": "bottom", "always_visible": True}
                    )
                ], width=6)
            ])
        ])
    ], className="mb-4")

def create_advanced_controls_tab():
    """Create the Advanced Controls tab with all missing backend endpoints, each with its own output display area."""
    return dbc.Container([
        html.H4("Advanced Controls & Diagnostics", className="mb-3 text-primary"),
        dbc.Row([
            dbc.Col([
                dbc.Button("Single Step", id="btn-step", color="info", className="mb-2", n_clicks=0),
                html.Div(id="output-step", className="mb-2 small text-monospace"),
                dbc.Button("Trigger Pulse", id="btn-trigger-pulse", color="warning", className="mb-2 ms-2", n_clicks=0),
                html.Div(id="output-trigger-pulse", className="mb-2 small text-monospace"),
                dbc.InputGroup([
                    dbc.Input(id="input-set-load", type="number", placeholder="Set Load Torque (Nm)", min=0),
                    dbc.Button("Set Load", id="btn-set-load", color="secondary", n_clicks=0)
                ], className="mb-2"),
                html.Div(id="output-set-load", className="mb-2 small text-monospace"),
                dbc.Button("Trigger Emergency Stop", id="btn-emergency-stop", color="danger", className="mb-2", n_clicks=0),
                html.Div(id="output-emergency-stop", className="mb-2 small text-monospace"),
                dbc.Form([
                    dbc.Checkbox(id="input-h1-active", className="me-1"),
                    dbc.Label("H1 Active", html_for="input-h1-active", className="me-2"),
                    dbc.Input(id="input-h1-fraction", type="number", min=0, max=1, step=0.01, placeholder="Bubble Fraction", className="me-2", style={"width": "150px", "display": "inline-block"}),
                    dbc.Input(id="input-h1-drag", type="number", min=0, max=1, step=0.01, placeholder="Drag Reduction", className="me-2", style={"width": "150px", "display": "inline-block"}),
                    dbc.Button("Set H1 Nanobubbles", id="btn-h1-nanobubbles", color="primary", n_clicks=0)
                ], className="mb-2 d-flex align-items-center"),
                html.Div(id="output-h1-nanobubbles", className="mb-2 small text-monospace"),
                dbc.InputGroup([
                    dbc.Select(id="select-control-mode", options=[
                        {"label": "Normal", "value": "normal"},
                        {"label": "Manual", "value": "manual"},
                        {"label": "Emergency", "value": "emergency"},
                        {"label": "Paused", "value": "paused"},
                    ], value="normal", style={"width": "200px"}),
                    dbc.Button("Set Control Mode", id="btn-set-control-mode", color="secondary", n_clicks=0)
                ], className="mb-2"),
                html.Div(id="output-set-control-mode", className="mb-2 small text-monospace"),
            ], width=6),
            dbc.Col([
                dbc.Button("Show Input Data", id="btn-show-input-data", color="secondary", className="mb-2", n_clicks=0),
                html.Div(id="output-show-input-data", className="mb-2 small text-monospace"),
                dbc.Button("Show Output Data", id="btn-show-output-data", color="secondary", className="mb-2 ms-2", n_clicks=0),
                html.Div(id="output-show-output-data", className="mb-2 small text-monospace"),
                dbc.Button("Show Energy Balance", id="btn-show-energy-balance", color="secondary", className="mb-2 ms-2", n_clicks=0),
                html.Div(id="output-show-energy-balance", className="mb-2 small text-monospace"),
                dbc.Button("Show Enhanced Performance", id="btn-show-enhanced-performance", color="secondary", className="mb-2", n_clicks=0),
                html.Div(id="output-show-enhanced-performance", className="mb-2 small text-monospace"),
                dbc.Button("Show Fluid Properties", id="btn-show-fluid-properties", color="secondary", className="mb-2 ms-2", n_clicks=0),
                html.Div(id="output-show-fluid-properties", className="mb-2 small text-monospace"),
                dbc.Button("Show Thermal Properties", id="btn-show-thermal-properties", color="secondary", className="mb-2 ms-2", n_clicks=0),
                html.Div(id="output-show-thermal-properties", className="mb-2 small text-monospace"),
            ], width=6)
        ])
    ], fluid=True)

# Main App Layout
app.layout = dbc.Container([
    dbc.Alert(id="system-health-alert", color="success", is_open=False, dismissable=True, className="mb-2"),
    dcc.Store(id="parameters-store"),  # Store for backend parameters
    dcc.Store(id="last-parameters-store"),  # Store for last-fetched parameters (for highlighting)
    dcc.Store(id="parameter-presets-store", storage_type="local"),  # Store for parameter presets (browser localStorage)
    dcc.Store(id="simulation-data-store"),
    dcc.Store(id="chart-data-store", data={"time": [], "power": [], "torque": [], "efficiency": []}),
    dcc.Store(id="notification-store", data={"show": False, "message": "", "color": "danger"}),  # Notification state
    
    # Preset selector UI
    html.Div([
        dbc.Row([
            dbc.Col([
                html.Label("Parameter Preset:"),
                dcc.Dropdown(id="preset-dropdown", options=[], value=None, placeholder="Select preset", style={"width": 220, "display": "inline-block"}),
                dbc.Button("Save Preset", id="save-preset-btn", color="primary", size="sm", className="ms-2"),
                dbc.Button("Delete Preset", id="delete-preset-btn", color="danger", size="sm", className="ms-2"),
            ], width=8),
        ], className="mb-2"),
    ]),
    
    # Real-time update interval
    dcc.Interval(
        id="interval-component",
        interval=500,  # Update every 0.5 second (2Hz)
        n_intervals=0
    ),
    
    # Layout components
    create_header(),
    create_control_panel(),
    create_metrics_cards(),
    create_metric_selector(),
    create_charts_section(),
    create_basic_parameters_panel(),

    # --- New: Tabbed interface for advanced controls ---
    dbc.Tabs([
        dbc.Tab(label="Advanced Parameters", tab_id="advanced-params"),
        dbc.Tab(label="Physics Controls", tab_id="physics-controls"),
        dbc.Tab(label="System Overview", tab_id="system-overview")
    ], id="parameter-tabs", active_tab="advanced-params", className="mb-3"),
    html.Div(id="parameter-content"),
    # --- End new tabs ---

    # Advanced Features (from legacy version)
    html.Hr(),
    html.H4("Advanced Features", className="text-primary"),
    
    # Add tabs for advanced features
    dbc.Tabs([
        dbc.Tab(label="Advanced Parameters", tab_id="advanced-params-legacy"),
        dbc.Tab(label="Physics Controls", tab_id="physics-controls-legacy"), 
        dbc.Tab(label="System Overview", tab_id="system-overview-legacy"),
        dbc.Tab(label="Analytics", tab_id="analytics"),
        dbc.Tab(create_advanced_controls_tab(), label="Advanced Controls", tab_id="advanced-controls"),
    ], id="advanced-tabs", active_tab="advanced-params-legacy"),
    
    html.Div(id="advanced-content"),
    
    # Footer
    html.Hr(),
    html.Footer([
        html.P([
            "KPP Simulator Dashboard v2.0 | ",
            html.A("Documentation", href="#", target="_blank"),
            " | Built with Plotly Dash"
        ], className="text-center text-muted")
    ]),
    
    dbc.Toast(
        id="notification-toast",
        header="Notification",
        is_open=False,
        dismissable=True,
        icon="danger",
        duration=6000,
        style={"position": "fixed", "top": 20, "right": 20, "minWidth": 350, "zIndex": 9999}
    ),
    WebSocket(id="ws", url="ws://localhost:5001/socket.io/?EIO=4&transport=websocket"),
], fluid=True)

# --- Tab content panels ---
def create_advanced_parameters_panel():
    """Create comprehensive advanced parameters panel with tooltips"""
    return dbc.Card([
        dbc.CardHeader(html.H5("Advanced Parameters", className="mb-0")),
        dbc.CardBody([
            # Physical Properties
            html.H6("Physical Properties", className="text-primary"),
            dbc.Row([
                dbc.Col([
                    html.Label([
                        "Floater Mass Empty (kg) ",
                        html.I("?", id="floater-mass-help", style={"cursor": "pointer", "color": "#888"})
                    ]),
                    dcc.Slider(
                        id="floater-mass-slider",
                        min=10, max=30, step=1, value=18,
                        marks={round(i, 0): str(i) for i in range(10, 31, 5)},
                        tooltip={"placement": "bottom", "always_visible": True}
                    ),
                    dbc.Tooltip(
                        "Mass of a single floater (kg). Range: 10-30 kg.",
                        target="floater-mass-help", placement="top"
                    )
                ], width=6),
                dbc.Col([
                    html.Label([
                        "Floater Area (m²) ",
                        html.I("?", id="floater-area-help", style={"cursor": "pointer", "color": "#888"})
                    ]),
                    dcc.Slider(
                        id="floater-area-slider",
                        min=0.01, max=0.1, step=0.005, value=0.035,
                        marks={round(i/100, 2): f"{i/100:.2f}" for i in range(1, 11, 2)},
                        tooltip={"placement": "bottom", "always_visible": True}
                    ),
                    dbc.Tooltip(
                        "Exposed cross-sectional area of floater (m²). Range: 0.01-0.1 m².",
                        target="floater-area-help", placement="top"
                    )
                ], width=6)
            ], className="mb-3"),
            # Pneumatic System
            html.H6("Pneumatic System", className="text-primary"),
            dbc.Row([
                dbc.Col([
                    html.Label([
                        "Air Fill Time (s) ",
                        html.I("?", id="air-fill-time-help", style={"cursor": "pointer", "color": "#888"})
                    ]),
                    dcc.Slider(
                        id="air-fill-time-slider",
                        min=0.1, max=2.0, step=0.1, value=0.5,
                        marks={i/10: f"{i/10}" for i in range(1, 21, 5)},
                        tooltip={"placement": "bottom", "always_visible": True}
                    ),
                    dbc.Tooltip(
                        "Time to fill a floater with air (seconds). Range: 0.1-2.0 s.",
                        target="air-fill-time-help", placement="top"
                    )
                ], width=4),
                dbc.Col([
                    html.Label([
                        "Air Flow Rate (m³/s) ",
                        html.I("?", id="air-flow-rate-help", style={"cursor": "pointer", "color": "#888"})
                    ]),
                    dcc.Slider(
                        id="air-flow-rate-slider",
                        min=0.1, max=2.0, step=0.1, value=0.6,
                        marks={i/10: f"{i/10}" for i in range(1, 21, 5)},
                        tooltip={"placement": "bottom", "always_visible": True}
                    ),
                    dbc.Tooltip(
                        "Air flow rate into floater (m³/s). Range: 0.1-2.0 m³/s.",
                        target="air-flow-rate-help", placement="top"
                    )
                ], width=4),
                dbc.Col([
                    html.Label([
                        "Jet Efficiency ",
                        html.I("?", id="jet-efficiency-help", style={"cursor": "pointer", "color": "#888"})
                    ]),
                    dcc.Slider(
                        id="jet-efficiency-slider",
                        min=0.5, max=1.0, step=0.05, value=0.85,
                        marks={i/100: f"{i/100:.2f}" for i in range(50, 101, 10)},
                        tooltip={"placement": "bottom", "always_visible": True}
                    ),
                    dbc.Tooltip(
                        "Efficiency of air jet injection (0.5-1.0, unitless).",
                        target="jet-efficiency-help", placement="top"
                    )
                ], width=4)
            ], className="mb-3"),
            # Mechanical System
            html.H6("Mechanical System", className="text-primary"),
            dbc.Row([
                dbc.Col([
                    html.Label([
                        "Sprocket Radius (m) ",
                        html.I("?", id="sprocket-radius-help", style={"cursor": "pointer", "color": "#888"})
                    ]),
                    dcc.Slider(
                        id="sprocket-radius-slider",
                        min=0.1, max=1.0, step=0.1, value=0.5,
                        marks={i/10: f"{i/10}" for i in range(1, 11)},
                        tooltip={"placement": "bottom", "always_visible": True}
                    ),
                    dbc.Tooltip(
                        "Radius of main sprocket (meters). Range: 0.1-1.0 m.",
                        target="sprocket-radius-help", placement="top"
                    )
                ], width=6),
                dbc.Col([
                    html.Label([
                        "Flywheel Inertia (kg⋅m²) ",
                        html.I("?", id="flywheel-inertia-help", style={"cursor": "pointer", "color": "#888"})
                    ]),
                    dcc.Slider(
                        id="flywheel-inertia-slider",
                        min=10, max=100, step=10, value=50,
                        marks={i: str(i) for i in range(10, 101, 20)},
                        tooltip={"placement": "bottom", "always_visible": True}
                    ),
                    dbc.Tooltip(
                        "Rotational inertia of flywheel (kg⋅m²). Range: 10-100 kg⋅m².",
                        target="flywheel-inertia-help", placement="top"
                    )
                ], width=6)
            ], className="mb-3")
        ])
    ], className="mb-4")

def create_physics_controls_panel():
    """Create H1/H2 physics controls panel"""
    return dbc.Card([
        dbc.CardHeader(html.H5("Enhanced Physics Controls", className="mb-0")),
        dbc.CardBody([
            # H1 Nanobubble Physics
            html.H6("H1 Nanobubble Physics", className="text-success"),
            dbc.Row([
                dbc.Col([
                    dbc.Switch(
                        id="h1-enabled-switch",
                        label="Enable H1 Nanobubbles",
                        value=False
                    )
                ], width=6),
                dbc.Col([
                    html.Label("Nanobubble Fraction"),
                    dcc.Slider(
                        id="nanobubble-fraction-slider",
                        min=0.0, max=1.0, step=0.05, value=0.05,
                        marks={i/10: f"{i/10}" for i in range(0, 11, 2)},
                        tooltip={"placement": "bottom", "always_visible": True}
                    )
                ], width=6)
            ], className="mb-3"),
            
            # H2 Thermal Physics
            html.H6("H2 Thermal Physics", className="text-warning"),
            dbc.Row([
                dbc.Col([
                    dbc.Switch(
                        id="h2-enabled-switch",
                        label="Enable H2 Thermal Effects",
                        value=False
                    )
                ], width=6),
                dbc.Col([
                    html.Label("Thermal Coefficient"),
                    dcc.Slider(
                        id="thermal-coeff-slider",
                        min=0.0, max=0.001, step=0.0001, value=0.0001,
                        marks={i/10000: f"{i/10000:.4f}" for i in range(0, 11, 2)},
                        tooltip={"placement": "bottom", "always_visible": True}
                    )
                ], width=6)
            ], className="mb-3"),
            
            # Water Temperature
            html.H6("Environmental Controls", className="text-info"),
            dbc.Row([
                dbc.Col([
                    html.Label("Water Temperature (°C)"),
                    dcc.Slider(
                        id="water-temp-slider",
                        min=0, max=50, step=1, value=20,
                        marks={i: f"{i}°C" for i in range(0, 51, 10)},
                        tooltip={"placement": "bottom", "always_visible": True}
                    )
                ], width=6),
                dbc.Col([
                    html.Label("Reference Temperature (°C)"),
                    dcc.Slider(
                        id="ref-temp-slider",
                        min=0, max=50, step=1, value=20,
                        marks={i: f"{i}°C" for i in range(0, 51, 10)},
                        tooltip={"placement": "bottom", "always_visible": True}
                    )
                ], width=6)
            ]),
            # Submit button
            dbc.Button("Submit Physics Controls", id="submit-physics-controls-btn", color="primary", className="mt-2")
        ])
    ], className="mb-4")

def create_system_overview_panel():
    """Create comprehensive system overview panel"""
    return dbc.Card([
        dbc.CardHeader(html.H5("System Overview", className="mb-0")),
        dbc.CardBody([
            dbc.Row([
                # Drivetrain Status
                dbc.Col([
                    html.H6("Drivetrain", className="text-primary"),
                    html.Div(id="drivetrain-overview")
                ], width=3),
                # Electrical Status  
                dbc.Col([
                    html.H6("Electrical", className="text-success"),
                    html.Div(id="electrical-overview")
                ], width=3),
                # Control Status
                dbc.Col([
                    html.H6("Control", className="text-warning"),
                    html.Div(id="control-overview")
                ], width=3),
                # Physics Status
                dbc.Col([
                    html.H6("Physics", className="text-info"),
                    html.Div(id="physics-overview")
                ], width=3)
            ])
        ])
    ], className="mb-4")

# --- Tab content callback ---
@app.callback(
    Output("parameter-content", "children"),
    Input("parameter-tabs", "active_tab")
)
def update_tab_content(active_tab):
    """Update content based on active tab"""
    if active_tab == "advanced-params":
        return create_advanced_parameters_panel()
    elif active_tab == "physics-controls":
        return create_physics_controls_panel()
    elif active_tab == "system-overview":
        return create_system_overview_panel()
    return html.Div("Select a tab")

# Callbacks

@app.callback(
    Output("simulation-data-store", "data"),
    Input("interval-component", "n_intervals"),
    prevent_initial_call=False
)
def update_simulation_data(n_intervals):
    """Fetch latest simulation data from backend via HTTP GET"""
    import time
    backend_url = "http://localhost:5001/data/summary"
    start_time = time.time()
    print(f"[Dash Callback] update_simulation_data called at {start_time:.2f}, n_intervals={n_intervals}")
    try:
        print(f"[Dash Callback] Sending GET request to {backend_url}")
        resp = requests.get(backend_url, timeout=5)
        elapsed = time.time() - start_time
        print(f"[Dash Callback] Response received in {elapsed:.3f} seconds, status={resp.status_code}")
        if resp.status_code == 200:
            print(f"[Dash Callback] Data: {resp.json()}")
            return resp.json()
        else:
            print(f"[Dash Callback] Error: {resp.text}")
            return {"status": "error", "error": resp.text}
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"[Dash Callback] Exception after {elapsed:.3f} seconds: {e}")
        logging.error(f"Error fetching simulation data: {e}")
        return {"status": "error", "error": str(e)}

@app.callback(
    [Output("power-value", "children"),
     Output("torque-value", "children"),
     Output("efficiency-value", "children"),
     Output("time-value", "children"),
     Output("grid-power", "children"),
     Output("flywheel-rpm", "children"),
     Output("electrical-eff", "children"),
     Output("pulse-count", "children"),
     Output("simulation-status", "children")],
    Input("simulation-data-store", "data")
)
def update_metrics_display(data):
    """Update the enhanced metrics cards with current values"""
    if not data:
        return (
            "0 W", "0 Nm", "0%", "0 s", "Grid: 0 W", "RPM: 0", "Electrical: 0%", "Pulses: 0", "Not Connected"
        )
    power = data.get("power", 0)
    torque = data.get("torque", 0)
    # Use overall_efficiency if present, else fallback to efficiency
    efficiency = data.get("overall_efficiency", data.get("efficiency", 0)) * 100
    time_val = data.get("time", 0)
    grid_power = data.get("grid_power_output", 0)
    flywheel_rpm = data.get("flywheel_speed_rpm", 0)
    electrical_eff = data.get("electrical_efficiency", 0) * 100
    pulse_count = data.get("pulse_count", 0)
    status = data.get("status", "unknown")

    # Format values
    power_str = f"{power:.1f} W" if power < 1000 else f"{power/1000:.2f} kW"
    torque_str = f"{torque:.1f} Nm"
    efficiency_str = f"{efficiency:.1f}%"
    time_str = f"{time_val:.1f} s"
    grid_str = f"Grid: {grid_power:.0f} W" if grid_power < 1000 else f"Grid: {grid_power/1000:.1f} kW"
    rpm_str = f"RPM: {flywheel_rpm:.0f}"
    elec_eff_str = f"Electrical: {electrical_eff:.1f}%"
    pulse_str = f"Pulses: {pulse_count}"

    # Status with color coding
    status_colors = {
        "running": "success",
        "stopped": "secondary",
        "paused": "warning",
        "error": "danger",
        "not_initialized": "secondary"
    }
    status_color = status_colors.get(status, "secondary")
    status_badge = dbc.Badge(status.replace("_", " ").title(), color=status_color)

    return (
        power_str, torque_str, efficiency_str, time_str,
        grid_str, rpm_str, elec_eff_str, pulse_str, status_badge
    )

@app.callback(
    Output("chart-data-store", "data"),
    [Input("simulation-data-store", "data")],
    State("chart-data-store", "data")
)
def update_chart_data(new_data, current_chart_data):
    """Update chart data store with new simulation data"""
    if not new_data or not current_chart_data:
        return {"time": [], "power": [], "torque": [], "efficiency": []}
    
    # Append new data point
    current_chart_data["time"].append(new_data.get("time", 0))
    current_chart_data["power"].append(new_data.get("power", 0))
    current_chart_data["torque"].append(new_data.get("torque", 0))
    current_chart_data["efficiency"].append(new_data.get("overall_efficiency", 0) * 100)  # Use overall_efficiency
    
    # Keep only last 100 points for performance
    max_points = 100
    for key in current_chart_data:
        if len(current_chart_data[key]) > max_points:
            current_chart_data[key] = current_chart_data[key][-max_points:]
    
    return current_chart_data

@app.callback(
    Output("power-torque-chart", "figure"),
    [Input("chart-data-store", "data"),
     Input("metric-selector", "value")]
)
def update_power_torque_chart(chart_data, selected_metrics):
    """Update the power and torque chart based on selected metrics"""
    if not chart_data or not chart_data.get("time"):
        fig = go.Figure()
        fig.add_annotation(
            text="No data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False
        )
        fig.update_layout(
            title="Power & Torque vs Time",
            xaxis_title="Time (s)",
            yaxis_title="Value"
        )
        return fig
    
    fig = go.Figure()
    if "power" in selected_metrics:
        fig.add_trace(go.Scatter(
            x=chart_data["time"],
            y=chart_data["power"],
            mode="lines",
            name="Power (W)",
            line=dict(color="blue", width=2)
        ))
    if "torque" in selected_metrics:
        fig.add_trace(go.Scatter(
            x=chart_data["time"],
            y=chart_data["torque"],
            mode="lines",
            name="Torque (Nm)",
            line=dict(color="green", width=2),
            yaxis="y2"
        ))
    fig.update_layout(
        title="Power & Torque vs Time",
        xaxis_title="Time (s)",
        yaxis=dict(title="Power (W)", side="left"),
        yaxis2=dict(title="Torque (Nm)", side="right", overlaying="y"),
        legend=dict(x=0.01, y=0.99),
        height=400
    )
    return fig

@app.callback(
    Output("efficiency-chart", "figure"),
    [Input("chart-data-store", "data"),
     Input("metric-selector", "value")]
)
def update_efficiency_chart(chart_data, selected_metrics):
    """Update the efficiency chart based on selected metrics"""
    if not chart_data or not chart_data.get("time") or "efficiency" not in selected_metrics:
        fig = go.Figure()
        fig.add_annotation(
            text="No data available or not selected",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False
        )
        fig.update_layout(
            title="System Efficiency",
            xaxis_title="Time (s)",
            yaxis_title="Efficiency (%)"
        )
        return fig
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=chart_data["time"],
        y=chart_data["efficiency"],
        mode="lines",
        name="Overall Efficiency",
        line=dict(color="orange", width=2),
        fill="tonexty"
    ))
    fig.update_layout(
        title="System Efficiency vs Time",
        xaxis_title="Time (s)",
        yaxis_title="Efficiency (%)",
        yaxis=dict(range=[0, 100]),
        height=400
    )
    return fig

@app.callback(
    Output("connection-status", "children"),
    Input("simulation-data-store", "data")
)
def update_connection_status(data):
    """Update connection status indicator"""
    if not data:
        return dbc.Badge("Disconnected", color="danger")
    
    if data.get("status") == "error":
        return dbc.Badge("Error", color="danger")
    elif data.get("health") == "healthy":
        return dbc.Badge("Connected", color="success")
    else:
        return dbc.Badge("Unknown", color="warning")

# Control button callbacks
@app.callback(
    Output("start-btn", "disabled"),
    [Input("start-btn", "n_clicks"),
     Input("stop-btn", "n_clicks"),
     Input("pause-btn", "n_clicks"),
     Input("reset-btn", "n_clicks")],
    [State("num-floaters-slider", "value"),
     State("floater-volume-slider", "value"),
     State("air-pressure-slider", "value"),
     State("pulse-interval-slider", "value")]
)
def handle_simulation_controls(start_clicks, stop_clicks, pause_clicks, reset_clicks,
                             num_floaters, floater_volume, air_pressure, pulse_interval):
    """Handle simulation control button clicks via HTTP requests to Flask backend"""
    ctx = dash.callback_context
    if not ctx.triggered:
        return False
    
    button_id = ctx.triggered[0]["prop_id"].split(".")[0]
    backend_url = "http://localhost:5001"
    try:
        if button_id == "start-btn":
            params = {
                "num_floaters": int(num_floaters),
                "floater_volume": float(floater_volume),
                "air_pressure": float(air_pressure),
                "pulse_interval": float(pulse_interval)
            }
            resp = requests.post(f"{backend_url}/start", json=params, timeout=5)
            if resp.status_code != 200:
                logging.error(f"Failed to start simulation: {resp.text}")
        elif button_id == "stop-btn":
            resp = requests.post(f"{backend_url}/stop", timeout=5)
            if resp.status_code != 200:
                logging.error(f"Failed to stop simulation: {resp.text}")
        elif button_id == "pause-btn":
            resp = requests.post(f"{backend_url}/pause", timeout=5)
            if resp.status_code != 200:
                logging.error(f"Failed to pause simulation: {resp.text}")
        elif button_id == "reset-btn":
            resp = requests.post(f"{backend_url}/reset", timeout=5)
            if resp.status_code != 200:
                logging.error(f"Failed to reset simulation: {resp.text}")
    except Exception as e:
        logging.error(f"Error in simulation control HTTP request: {e}")
    return False  # Never disable start button permanently

def test_backend_connectivity():
    backend_url = "http://127.0.0.1:5001/status"  # Update this if needed
    try:
        resp = requests.get(backend_url, timeout=3)
        if resp.status_code == 200:
            logging.info(f"Backend connectivity test: SUCCESS ({resp.text})")
        else:
            logging.error(f"Backend connectivity test: FAIL (status {resp.status_code})")
    except Exception as e:
        logging.error(f"Backend connectivity test: ERROR ({e})")

test_backend_connectivity()

@app.callback(
    [Output("notification-toast", "is_open"),
     Output("notification-toast", "children"),
     Output("notification-toast", "icon")],
    Input("notification-store", "data")
)
def display_notification(notification):
    if notification and notification.get("show", False):
        return True, notification.get("message", ""), notification.get("color", "danger")
    return False, "", "danger"

# Example: Update notification-store on backend error or connection lost
@app.callback(
    Output("notification-store", "data"),
    Input("simulation-data-store", "data"),
    prevent_initial_call=True
)
def notify_on_error(data):
    if not data:
        return {"show": True, "message": "No data received from backend.", "color": "danger"}
    if data.get("status") == "error":
        return {"show": True, "message": f"Backend error: {data.get('error', 'Unknown error')}", "color": "danger"}
    if data.get("status") == "stopped":
        return {"show": True, "message": "Simulation stopped.", "color": "warning"}
    return {"show": False, "message": "", "color": "info"}

# --- Advanced WebSocket Debugging and Validation ---
def validate_ws_data(data):
    required_fields = ["time", "power", "torque", "pulse_count", "status"]
    errors = []
    for field in required_fields:
        if field not in data:
            errors.append(f"Missing field: {field}")
    if errors:
        return False, "; ".join(errors)
    # Type checks (example)
    if not isinstance(data["time"], (int, float)):
        errors.append("'time' must be a number")
    if not isinstance(data["power"], (int, float)):
        errors.append("'power' must be a number")
    if not isinstance(data["torque"], (int, float)):
        errors.append("'torque' must be a number")
    if not isinstance(data["pulse_count"], int):
        errors.append("'pulse_count' must be an integer")
    if not isinstance(data["status"], str):
        errors.append("'status' must be a string")
    if errors:
        return False, "; ".join(errors)
    return True, ""

@app.callback(
    Output("simulation-data-store", "data"),
    Output("notification-store", "data"),
    Input("ws", "message"),
    prevent_initial_call=True
)
def update_data_from_ws(message):
    import json
    import logging
    if message and message["data"]:
        try:
            data = json.loads(message["data"])
            valid, err = validate_ws_data(data)
            if not valid:
                logging.error(f"[WebSocket] Invalid message: {err}")
                return dash.no_update, {"show": True, "message": f"WebSocket data error: {err}", "color": "danger"}
            logging.info(f"[WebSocket] Received valid message: {data}")
            return data, {"show": False, "message": "", "color": "info"}
        except Exception as e:
            logging.error(f"[WebSocket] Exception: {e}")
            return dash.no_update, {"show": True, "message": f"WebSocket exception: {e}", "color": "danger"}
    return dash.no_update, dash.no_update

def format_response(resp):
    if isinstance(resp, dict):
        import json
        return json.dumps(resp, indent=2)
    return str(resp)

# 1. /step (POST)
@app.callback(
    Output("output-step", "children"),
    Output("notification-store", "data"),
    Input("btn-step", "n_clicks"),
    prevent_initial_call=True
)
def call_step(n):
    if n == 0:
        raise PreventUpdate
    try:
        r = requests.post(f"{BACKEND_URL}/step", timeout=5)
        return r.text, {"show": False, "message": "", "color": "info"}
    except Exception as e:
        return "", {"show": True, "message": f"Step error: {e}", "color": "danger"}

# 2. /trigger_pulse (POST)
@app.callback(
    Output("output-trigger-pulse", "children"),
    Output("notification-store", "data"),
    Input("btn-trigger-pulse", "n_clicks"),
    prevent_initial_call=True
)
def call_trigger_pulse(n):
    if n == 0:
        raise PreventUpdate
    try:
        r = requests.post(f"{BACKEND_URL}/trigger_pulse", timeout=5)
        return r.text, {"show": False, "message": "", "color": "info"}
    except Exception as e:
        return "", {"show": True, "message": f"Trigger pulse error: {e}", "color": "danger"}

# 3. /set_load (POST)
@app.callback(
    Output("output-set-load", "children"),
    Output("notification-store", "data"),
    Input("btn-set-load", "n_clicks"),
    State("input-set-load", "value"),
    prevent_initial_call=True
)
def call_set_load(n, value):
    if n == 0 or value is None:
        raise PreventUpdate
    try:
        r = requests.post(f"{BACKEND_URL}/set_load", json={"user_load_torque": value}, timeout=5)
        return r.text, {"show": False, "message": "", "color": "info"}
    except Exception as e:
        return "", {"show": True, "message": f"Set load error: {e}", "color": "danger"}

# 4. /control/trigger_emergency_stop (POST)
@app.callback(
    Output("output-emergency-stop", "children"),
    Output("notification-store", "data"),
    Input("btn-emergency-stop", "n_clicks"),
    prevent_initial_call=True
)
def call_emergency_stop(n):
    if n == 0:
        raise PreventUpdate
    try:
        r = requests.post(f"{BACKEND_URL}/control/trigger_emergency_stop", json={"reason": "Manual from UI"}, timeout=5)
        return format_response(r.json()), {"show": False, "message": "", "color": "info"}
    except Exception as e:
        return "", {"show": True, "message": f"Emergency stop error: {e}", "color": "danger"}

# 5. /control/h1_nanobubbles (POST)
@app.callback(
    Output("output-h1-nanobubbles", "children"),
    Output("notification-store", "data"),
    Input("btn-h1-nanobubbles", "n_clicks"),
    State("input-h1-active", "value"),
    State("input-h1-fraction", "value"),
    State("input-h1-drag", "value"),
    prevent_initial_call=True
)
def call_h1_nanobubbles(n, active, fraction, drag):
    if n == 0:
        raise PreventUpdate
    try:
        payload = {
            "active": bool(active),
            "bubble_fraction": fraction if fraction is not None else 0.05,
            "drag_reduction": drag if drag is not None else 0.1
        }
        r = requests.post(f"{BACKEND_URL}/control/h1_nanobubbles", json=payload, timeout=5)
        return format_response(r.json()), {"show": False, "message": "", "color": "info"}
    except Exception as e:
        return "", {"show": True, "message": f"H1 nanobubbles error: {e}", "color": "danger"}

# 6. /control/set_control_mode (POST)
@app.callback(
    Output("output-set-control-mode", "children"),
    Output("notification-store", "data"),
    Input("btn-set-control-mode", "n_clicks"),
    State("select-control-mode", "value"),
    prevent_initial_call=True
)
def call_set_control_mode(n, mode):
    if n == 0:
        raise PreventUpdate
    try:
        r = requests.post(f"{BACKEND_URL}/control/set_control_mode", json={"control_mode": mode}, timeout=5)
        return format_response(r.json()), {"show": False, "message": "", "color": "info"}
    except Exception as e:
        return "", {"show": True, "message": f"Set control mode error: {e}", "color": "danger"}

# 7. /inspect/input_data (GET)
@app.callback(
    Output("output-show-input-data", "children"),
    Output("notification-store", "data"),
    Input("btn-show-input-data", "n_clicks"),
    prevent_initial_call=True
)
def call_show_input_data(n):
    if n == 0:
        raise PreventUpdate
    try:
        r = requests.get(f"{BACKEND_URL}/inspect/input_data", timeout=5)
        return format_response(r.json()), {"show": False, "message": "", "color": "info"}
    except Exception as e:
        return "", {"show": True, "message": f"Show input data error: {e}", "color": "danger"}

# 8. /inspect/output_data (GET)
@app.callback(
    Output("output-show-output-data", "children"),
    Output("notification-store", "data"),
    Input("btn-show-output-data", "n_clicks"),
    prevent_initial_call=True
)
def call_show_output_data(n):
    if n == 0:
        raise PreventUpdate
    try:
        r = requests.get(f"{BACKEND_URL}/inspect/output_data", timeout=5)
        return format_response(r.json()), {"show": False, "message": "", "color": "info"}
    except Exception as e:
        return "", {"show": True, "message": f"Show output data error: {e}", "color": "danger"}

# 9. /data/energy_balance (GET)
@app.callback(
    Output("output-show-energy-balance", "children"),
    Output("notification-store", "data"),
    Input("btn-show-energy-balance", "n_clicks"),
    prevent_initial_call=True
)
def call_show_energy_balance(n):
    if n == 0:
        raise PreventUpdate
    try:
        r = requests.get(f"{BACKEND_URL}/data/energy_balance", timeout=5)
        return format_response(r.json()), {"show": False, "message": "", "color": "info"}
    except Exception as e:
        return "", {"show": True, "message": f"Show energy balance error: {e}", "color": "danger"}

# 10. /data/enhanced_performance (GET)
@app.callback(
    Output("output-show-enhanced-performance", "children"),
    Output("notification-store", "data"),
    Input("btn-show-enhanced-performance", "n_clicks"),
    prevent_initial_call=True
)
def call_show_enhanced_performance(n):
    if n == 0:
        raise PreventUpdate
    try:
        r = requests.get(f"{BACKEND_URL}/data/enhanced_performance", timeout=5)
        return format_response(r.json()), {"show": False, "message": "", "color": "info"}
    except Exception as e:
        return "", {"show": True, "message": f"Show enhanced performance error: {e}", "color": "danger"}

# 11. /data/fluid_properties (GET)
@app.callback(
    Output("output-show-fluid-properties", "children"),
    Output("notification-store", "data"),
    Input("btn-show-fluid-properties", "n_clicks"),
    prevent_initial_call=True
)
def call_show_fluid_properties(n):
    if n == 0:
        raise PreventUpdate
    try:
        r = requests.get(f"{BACKEND_URL}/data/fluid_properties", timeout=5)
        return format_response(r.json()), {"show": False, "message": "", "color": "info"}
    except Exception as e:
        return "", {"show": True, "message": f"Show fluid properties error: {e}", "color": "danger"}

# 12. /data/thermal_properties (GET)
@app.callback(
    Output("output-show-thermal-properties", "children"),
    Output("notification-store", "data"),
    Input("btn-show-thermal-properties", "n_clicks"),
    prevent_initial_call=True
)
def call_show_thermal_properties(n):
    if n == 0:
        raise PreventUpdate
    try:
        r = requests.get(f"{BACKEND_URL}/data/thermal_properties", timeout=5)
        return format_response(r.json()), {"show": False, "message": "", "color": "info"}
    except Exception as e:
        return "", {"show": True, "message": f"Show thermal properties error: {e}", "color": "danger"}

# --- System Overview Callbacks ---
@app.callback(
    [Output("drivetrain-overview", "children"),
     Output("electrical-overview", "children"),
     Output("control-overview", "children"),
     Output("physics-overview", "children")],
    Input("simulation-data-store", "data")
)
def update_system_overview(data):
    empty_status = html.Small("No data", className="text-muted")
    if not data:
        return empty_status, empty_status, empty_status, empty_status

    # Drivetrain Overview
    drivetrain = dbc.Card([
        dbc.CardHeader("Drivetrain Status"),
        dbc.CardBody([
            html.P(f"Output RPM: {data.get('output_rpm', 'N/A')}", className="mb-1"),
            html.P(f"Torque: {data.get('torque', 'N/A')} Nm", className="mb-1"),
            html.P(f"Clutch Engaged: {data.get('clutch_engaged', 'N/A')}", className="mb-1")
        ])
    ], color="primary", inverse=True)

    # Electrical Overview
    electrical = dbc.Card([
        dbc.CardHeader("Electrical Status"),
        dbc.CardBody([
            html.P(f"Grid Power: {data.get('grid_power_output', 0):.0f}W", className="mb-1"),
            html.P(f"Sync: {'Yes' if data.get('electrical_synchronized', False) else 'No'}", className="mb-1"),
            html.P(f"Load Factor: {data.get('electrical_load_factor', 0)*100:.1f}%", className="mb-1 text-muted")
        ])
    ], color="success", inverse=True)

    # Control Overview
    control = dbc.Card([
        dbc.CardHeader("Control Status"),
        dbc.CardBody([
            html.P(f"Mode: {data.get('control_mode', 'Normal').title()}", className="mb-1"),
            html.P(f"Health: {data.get('system_health', 1.0)*100:.0f}%", className="mb-1"),
            html.P(f"Status: Active", className="mb-1 text-muted")
        ])
    ], color="warning", inverse=True)

    # Physics Overview
    h1_active = data.get('nanobubble_frac', 0) > 0
    h2_active = data.get('thermal_coeff', 0.0001) != 0.0001
    physics = dbc.Card([
        dbc.CardHeader("Physics Status"),
        dbc.CardBody([
            html.P(f"H1 Nanobubbles: {'Active' if h1_active else 'Inactive'}", className="mb-1"),
            html.P(f"H2 Thermal: {'Active' if h2_active else 'Inactive'}", className="mb-1"),
            html.P(f"Water Temp: {data.get('water_temp', 20):.1f}°C", className="mb-1 text-muted")
        ])
    ], color="info", inverse=True)

    return drivetrain, electrical, control, physics

# --- Fetch parameters from backend on app load and after update ---
@app.callback(
    [Output("parameters-store", "data"), Output("last-parameters-store", "data")],
    Input("interval-component", "n_intervals"),
    State("parameters-store", "data"),
    prevent_initial_call=False
)
def fetch_parameters_callback(n, last_params):
    import requests
    try:
        resp = requests.get(f"{BACKEND_URL}/parameters", timeout=5)
        if resp.status_code == 200:
            params = resp.json()
            return params, last_params
        else:
            return {}, last_params
    except Exception:
        return {}, last_params

# --- Parameter Preset Management ---
@app.callback(
    [Output("parameter-presets-store", "data"), Output("preset-dropdown", "options"), Output("preset-dropdown", "value"), Output("notification-store", "data")],
    [Input("save-preset-btn", "n_clicks"), Input("delete-preset-btn", "n_clicks"), Input("preset-dropdown", "value")],
    [State("parameter-presets-store", "data"), State("parameters-store", "data")],
    prevent_initial_call=True
)
def manage_presets(save_clicks, delete_clicks, selected_preset, presets, current_params):
    import dash
    ctx = dash.callback_context
    if not presets:
        presets = {}
    if ctx.triggered:
        btn_id = ctx.triggered[0]["prop_id"].split(".")[0]
        if btn_id == "save-preset-btn" and current_params:
            # Save current params as a new preset
            import datetime
            preset_name = f"Preset {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            presets[preset_name] = current_params
            options = [{"label": k, "value": k} for k in presets.keys()]
            return presets, options, preset_name, {"show": True, "message": f"Preset '{preset_name}' saved.", "color": "success"}
        elif btn_id == "delete-preset-btn" and selected_preset and selected_preset in presets:
            del presets[selected_preset]
            options = [{"label": k, "value": k} for k in presets.keys()]
            return presets, options, None, {"show": True, "message": f"Preset '{selected_preset}' deleted.", "color": "danger"}
        elif btn_id == "preset-dropdown" and selected_preset and selected_preset in presets:
            # Just update dropdown value, no notification
            options = [{"label": k, "value": k} for k in presets.keys()]
            return presets, options, selected_preset, {"show": False, "message": "", "color": "info"}
    options = [{"label": k, "value": k} for k in presets.keys()]
    return presets, options, selected_preset, {"show": False, "message": "", "color": "info"}

# --- Apply preset to controls when selected ---
@app.callback(
    Output("parameters-store", "data"),
    Input("preset-dropdown", "value"),
    State("parameter-presets-store", "data"),
    prevent_initial_call=True
)
def apply_preset(selected_preset, presets):
    if presets and selected_preset and selected_preset in presets:
        return presets[selected_preset]
    return dash.no_update

# --- Highlight changed parameter controls ---
# Example for floater-mass-slider (repeat for all controls as needed)
@app.callback(
    Output("floater-mass-slider", "style"),
    [Input("parameters-store", "data"), Input("last-parameters-store", "data")]
)
def highlight_floater_mass(params, last_params):
    if not params or not last_params:
        return {}
    if params.get("floater_mass_empty") != last_params.get("floater_mass_empty"):
        return {"border": "2px solid orange"}
    return {}

# --- Map all parameter controls to backend values ---
# Basic parameters
@app.callback(Output("num-floaters-slider", "value"), Input("parameters-store", "data"))
def set_num_floaters(params):
    return params.get("num_floaters", 8)

@app.callback(Output("floater-volume-slider", "value"), Input("parameters-store", "data"))
def set_floater_volume(params):
    return params.get("floater_volume", 0.3)

@app.callback(Output("air-pressure-slider", "value"), Input("parameters-store", "data"))
def set_air_pressure(params):
    return params.get("air_pressure", 300000)

@app.callback(Output("pulse-interval-slider", "value"), Input("parameters-store", "data"))
def set_pulse_interval(params):
    return params.get("pulse_interval", 2.0)

# Advanced parameters
@app.callback(Output("floater-mass-slider", "value"), Input("parameters-store", "data"))
def set_floater_mass(params):
    return params.get("floater_mass_empty", 18.0)

@app.callback(Output("floater-area-slider", "value"), Input("parameters-store", "data"))
def set_floater_area(params):
    return params.get("floater_area", 0.035)

@app.callback(Output("air-fill-time-slider", "value"), Input("parameters-store", "data"))
def set_air_fill_time(params):
    return params.get("air_fill_time", 0.5)

@app.callback(Output("air-flow-rate-slider", "value"), Input("parameters-store", "data"))
def set_air_flow_rate(params):
    return params.get("air_flow_rate", 0.6)

@app.callback(Output("jet-efficiency-slider", "value"), Input("parameters-store", "data"))
def set_jet_efficiency(params):
    return params.get("jet_efficiency", 0.85)

@app.callback(Output("sprocket-radius-slider", "value"), Input("parameters-store", "data"))
def set_sprocket_radius(params):
    return params.get("sprocket_radius", 0.5)

@app.callback(Output("flywheel-inertia-slider", "value"), Input("parameters-store", "data"))
def set_flywheel_inertia(params):
    return params.get("flywheel_inertia", 50.0)

# Physics controls
@app.callback(Output("h1-enabled-switch", "value"), Input("parameters-store", "data"))
def set_h1_enabled(params):
    # Assume nanobubble_frac > 0 means enabled
    return params.get("nanobubble_frac", 0.0) > 0

@app.callback(Output("nanobubble-fraction-slider", "value"), Input("parameters-store", "data"))
def set_nanobubble_fraction(params):
    return params.get("nanobubble_frac", 0.0)

@app.callback(Output("h2-enabled-switch", "value"), Input("parameters-store", "data"))
def set_h2_enabled(params):
    # Assume thermal_coeff > default means enabled
    return params.get("thermal_coeff", 0.0001) > 0.0001

@app.callback(Output("thermal-coeff-slider", "value"), Input("parameters-store", "data"))
def set_thermal_coeff(params):
    return params.get("thermal_coeff", 0.0001)

@app.callback(Output("water-temp-slider", "value"), Input("parameters-store", "data"))
def set_water_temp(params):
    return params.get("water_temp", 20.0)

@app.callback(Output("ref-temp-slider", "value"), Input("parameters-store", "data"))
def set_ref_temp(params):
    return params.get("ref_temp", 20.0)

# --- Submit advanced parameters and refresh store ---
@app.callback(
    [Output("notification-store", "data"), Output("parameters-store", "data")],
    Input("submit-physics-controls-btn", "n_clicks"),
    [State("h1-enabled-switch", "value"),
     State("nanobubble-fraction-slider", "value"),
     State("h2-enabled-switch", "value"),
     State("thermal-coeff-slider", "value"),
     State("water-temp-slider", "value"),
     State("ref-temp-slider", "value")],
    prevent_initial_call=True
)
def submit_physics_controls(n_clicks, h1_enabled, nanobubble_fraction, h2_enabled, thermal_coeff, water_temp, ref_temp):
    import requests
    payload = {
        "nanobubble_frac": nanobubble_fraction if h1_enabled else 0.0,
        "thermal_coeff": thermal_coeff if h2_enabled else 0.0001,
        "water_temp": water_temp,
        "ref_temp": ref_temp
    }
    try:
        resp = requests.post(f"{BACKEND_URL}/parameters", json=payload, timeout=5)
        if resp.status_code == 200:
            params = requests.get(f"{BACKEND_URL}/parameters").json()
            return ({"show": True, "message": "Physics controls updated.", "color": "success"}, params)
        else:
            return ({"show": True, "message": f"Failed: {resp.text}", "color": "danger"}, dash.no_update)
    except Exception as e:
        return ({"show": True, "message": f"Error: {e}", "color": "danger"}, dash.no_update)

# --- Validation ranges for advanced parameters ---
ADV_PARAM_RANGES = {
    "floater_mass_empty": (10, 30),
    "floater_area": (0.01, 0.1),
    "air_fill_time": (0.1, 2.0),
    "air_flow_rate": (0.1, 2.0),
    "jet_efficiency": (0.5, 1.0),
    "sprocket_radius": (0.1, 1.0),
    "flywheel_inertia": (10, 100),
}

# --- Validation feedback for advanced parameters ---
def validate_param(value, param):
    min_val, max_val = ADV_PARAM_RANGES[param]
    if value is None:
        return False, f"Value required."
    if value < min_val or value > max_val:
        return False, f"Must be between {min_val} and {max_val}."
    return True, ""

# --- Highlight and error message for each advanced parameter ---
# Example for floater-mass-slider
@app.callback(
    [Output("floater-mass-slider", "style"), Output("floater-mass-slider-error", "children")],
    [Input("floater-mass-slider", "value")]
)
def validate_floater_mass(value):
    valid, msg = validate_param(value, "floater_mass_empty")
    style = {"border": "2px solid red"} if not valid else {}
    error = msg if not valid else ""
    return style, error

# Repeat for all advanced parameter sliders
@app.callback(
    [Output("floater-area-slider", "style"), Output("floater-area-slider-error", "children")],
    [Input("floater-area-slider", "value")]
)
def validate_floater_area(value):
    valid, msg = validate_param(value, "floater_area")
    style = {"border": "2px solid red"} if not valid else {}
    error = msg if not valid else ""
    return style, error

@app.callback(
    [Output("air-fill-time-slider", "style"), Output("air-fill-time-slider-error", "children")],
    [Input("air-fill-time-slider", "value")]
)
def validate_air_fill_time(value):
    valid, msg = validate_param(value, "air_fill_time")
    style = {"border": "2px solid red"} if not valid else {}
    error = msg if not valid else ""
    return style, error

@app.callback(
    [Output("air-flow-rate-slider", "style"), Output("air-flow-rate-slider-error", "children")],
    [Input("air-flow-rate-slider", "value")]
)
def validate_air_flow_rate(value):
    valid, msg = validate_param(value, "air_flow_rate")
    style = {"border": "2px solid red"} if not valid else {}
    error = msg if not valid else ""
    return style, error

@app.callback(
    [Output("jet-efficiency-slider", "style"), Output("jet-efficiency-slider-error", "children")],
    [Input("jet-efficiency-slider", "value")]
)
def validate_jet_efficiency(value):
    valid, msg = validate_param(value, "jet_efficiency")
    style = {"border": "2px solid red"} if not valid else {}
    error = msg if not valid else ""
    return style, error

@app.callback(
    [Output("sprocket-radius-slider", "style"), Output("sprocket-radius-slider-error", "children")],
    [Input("sprocket-radius-slider", "value")]
)
def validate_sprocket_radius(value):
    valid, msg = validate_param(value, "sprocket_radius")
    style = {"border": "2px solid red"} if not valid else {}
    error = msg if not valid else ""
    return style, error

@app.callback(
    [Output("flywheel-inertia-slider", "style"), Output("flywheel-inertia-slider-error", "children")],
    [Input("flywheel-inertia-slider", "value")]
)
def validate_flywheel_inertia(value):
    valid, msg = validate_param(value, "flywheel_inertia")
    style = {"border": "2px solid red"} if not valid else {}
    error = msg if not valid else ""
    return style, error

# --- Prevent submission if any errors exist ---
@app.callback(
    [Output("notification-store", "data"), Output("parameters-store", "data")],
    Input("submit-advanced-params-btn", "n_clicks"),
    [State("floater-mass-slider", "value"),
     State("floater-area-slider", "value"),
     State("air-fill-time-slider", "value"),
     State("air-flow-rate-slider", "value"),
     State("jet-efficiency-slider", "value"),
     State("sprocket-radius-slider", "value"),
     State("flywheel-inertia-slider", "value")],
    prevent_initial_call=True
)
def submit_advanced_params(n_clicks, floater_mass, floater_area, air_fill_time, air_flow_rate, jet_efficiency, sprocket_radius, flywheel_inertia):
    import requests
    # Validate all
    vals = [
        (floater_mass, "floater_mass_empty"),
        (floater_area, "floater_area"),
        (air_fill_time, "air_fill_time"),
        (air_flow_rate, "air_flow_rate"),
        (jet_efficiency, "jet_efficiency"),
        (sprocket_radius, "sprocket_radius"),
        (flywheel_inertia, "flywheel_inertia"),
    ]
    errors = [validate_param(v, k)[0] for v, k in vals]
    if not all(errors):
        return ({"show": True, "message": "Fix validation errors before submitting.", "color": "danger"}, dash.no_update)
    payload = {
        "floater_mass_empty": floater_mass,
        "floater_area": floater_area,
        "air_fill_time": air_fill_time,
        "air_flow_rate": air_flow_rate,
        "jet_efficiency": jet_efficiency,
        "sprocket_radius": sprocket_radius,
        "flywheel_inertia": flywheel_inertia
    }
    try:
        resp = requests.post(f"{BACKEND_URL}/parameters", json=payload, timeout=5)
        if resp.status_code == 200:
            params = requests.get(f"{BACKEND_URL}/parameters").json()
            return ({"show": True, "message": "Advanced parameters updated.", "color": "success"}, params)
        else:
            return ({"show": True, "message": f"Failed: {resp.text}", "color": "danger"}, dash.no_update)
    except Exception as e:
        return ({"show": True, "message": f"Error: {e}", "color": "danger"}, dash.no_update)

# --- System Health and Alerts ---
def get_system_health(data, params):
    # Simple rules for demo: can be expanded
    if not data:
        return ("danger", "No simulation data received.")
    if data.get("error"):
        return ("danger", f"Simulation error: {data['error']}")
    if "efficiency" in data and data["efficiency"] < 0.5:
        return ("warning", "System efficiency is critically low.")
    # Check for parameter out of range
    for k, v in (params or {}).items():
        if k in ADV_PARAM_RANGES:
            minv, maxv = ADV_PARAM_RANGES[k]
            if v < minv or v > maxv:
                return ("warning", f"Parameter {k} out of range.")
    return ("success", "System healthy.")

@app.callback(
    [Output("system-health-alert", "color"), Output("system-health-alert", "children"), Output("system-health-alert", "is_open")],
    [Input("simulation-data-store", "data"), Input("parameters-store", "data")],
    [State("system-health-alert", "is_open")]
)
def update_system_health(data, params, is_open):
    color, msg = get_system_health(data, params)
    open_alert = color != "success" or is_open  # Show alert if not healthy
    return color, msg, open_alert

# --- User Customization for Dashboard Cards ---
METRIC_CARDS = [
    {"id": "power-value", "label": "Power Output"},
    {"id": "grid-power", "label": "Grid Power"},
    {"id": "flywheel-rpm", "label": "Flywheel RPM"},
    {"id": "efficiency", "label": "Efficiency"},
    {"id": "pulse-count", "label": "Pulse Count"},
]

# Add a store for user card preferences
# dcc.Store(id="card-prefs-store", storage_type="local"),

# Add a button to open the customization modal
# dbc.Button("Customize Dashboard", id="open-card-customize-btn", color="secondary", className="mb-2"),

# Modal for customization
# dbc.Modal([
#     dbc.ModalHeader("Customize Dashboard Cards"),
#     dbc.ModalBody([
#         dcc.Checklist(
#             id="card-visibility-checklist",
#             options=[{"label": c["label"], "value": c["id"]} for c in METRIC_CARDS],
#             value=[c["id"] for c in METRIC_CARDS],
#             inline=False
#         ),
#         html.Br(),
#         daq.GraduatedBar(
#             id="card-order-bar",
#             label="Drag to reorder (not implemented in UI-only stub)",
#             showCurrentValue=True,
#             max=len(METRIC_CARDS)-1,
#             min=0,
#             step=1,
#             value=0
#         ),
#         # For real drag-and-drop, use dash-sortable or dash-draggable (not included here)
#     ]),
#     dbc.ModalFooter([
#         dbc.Button("Save", id="save-card-prefs-btn", color="primary"),
#         dbc.Button("Cancel", id="close-card-customize-btn", color="secondary"),
#     ]),
# ], id="card-customize-modal", is_open=False),

# Callback to open/close modal
# @app.callback(
#     Output("card-customize-modal", "is_open"),
#     [Input("open-card-customize-btn", "n_clicks"), Input("close-card-customize-btn", "n_clicks"), Input("save-card-prefs-btn", "n_clicks")],
#     [State("card-customize-modal", "is_open")],
# )
# def toggle_card_customize_modal(open_n, close_n, save_n, is_open):
#     ctx = dash.callback_context
#     if not ctx.triggered:
#         return is_open
#     btn_id = ctx.triggered[0]["prop_id"].split(".")[0]
#     if btn_id in ["open-card-customize-btn"]:
#         return True
#     if btn_id in ["close-card-customize-btn", "save-card-prefs-btn"]:
#         return False
#     return is_open

# Callback to save preferences
# @app.callback(
#     Output("card-prefs-store", "data"),
#     Input("save-card-prefs-btn", "n_clicks"),
#     State("card-visibility-checklist", "value"),
#     prevent_initial_call=True
# )
# def save_card_prefs(n_clicks, visible_cards):
#     return {"visible": visible_cards}

# Render metric cards based on preferences
# In create_metrics_cards(), use card-prefs-store to determine which cards to show and in what order

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 KPP Simulator Dash Application Starting...")
    print("=" * 60)
    
    # Initialize simulation
    if initialize_simulation():
        print("✅ Simulation engine initialized")
    else:
        print("❌ Failed to initialize simulation engine")
    
    print("🌐 Dashboard will be available at: http://127.0.0.1:8051")
    print("📊 Real-time updates at 2Hz")
    print("Press Ctrl+C to stop the server")
    print("=" * 60)
    
    try:
        app.run(debug=True, host='127.0.0.1', port=8051)
    except Exception as e:
        print(f"❌ Failed to start Dash server: {e}")
        import traceback
        traceback.print_exc()
