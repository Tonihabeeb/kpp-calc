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

# Import our existing simulation engine
from simulation.engine import SimulationEngine
from config.parameter_schema import get_default_parameters, validate_parameters_batch

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Dash app with Bootstrap theme
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "KPP Simulator Dashboard"

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
        logger.info("Simulation engine initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize simulation engine: {e}")
        return False

def get_simulation_data():
    """Get current simulation data in Dash-compatible format"""
    if not sim_engine:
        return {
            "time": 0,
            "power": 0,
            "torque": 0,
            "efficiency": 0,
            "status": "not_initialized",
            "error": "Simulation engine not initialized"
        }
    
    try:
        # Get comprehensive output data
        data = sim_engine.get_output_data()
        
        # Add metadata for Dash
        data["status"] = "running" if getattr(sim_engine, "running", False) else "stopped"
        data["timestamp"] = time.time()
        data["health"] = "healthy"
        
        return data
    except Exception as e:
        logger.error(f"Error getting simulation data: {e}")
        return {
            "time": 0,
            "power": 0,
            "torque": 0,
            "efficiency": 0,
            "status": "error",
            "error": str(e)
        }

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
    """Create real-time metrics cards"""
    return dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4(id="power-value", children="0 W", className="text-primary"),
                    html.P("Power Output", className="text-muted mb-0")
                ])
            ])
        ], width=3),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4(id="torque-value", children="0 Nm", className="text-success"),
                    html.P("Torque", className="text-muted mb-0")
                ])
            ])
        ], width=3),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4(id="efficiency-value", children="0%", className="text-warning"),
                    html.P("Efficiency", className="text-muted mb-0")
                ])
            ])
        ], width=3),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4(id="time-value", children="0 s", className="text-info"),
                    html.P("Simulation Time", className="text-muted mb-0")
                ])
            ])
        ], width=3)
    ], className="mb-4")

def create_charts_section():
    """Create the main charts section"""
    return dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Power & Torque"),
                dbc.CardBody([
                    dcc.Graph(id="power-torque-chart")
                ])
            ])
        ], width=6),
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("System Efficiency"),
                dbc.CardBody([
                    dcc.Graph(id="efficiency-chart")
                ])
            ])
        ], width=6)
    ], className="mb-4")

def create_parameters_panel():
    """Create the parameters control panel"""
    return dbc.Card([
        dbc.CardHeader(html.H5("Simulation Parameters", className="mb-0")),
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    html.Label("Number of Floaters"),
                    dcc.Slider(
                        id="num-floaters-slider",
                        min=4, max=16, step=2, value=8,
                        marks={i: str(i) for i in range(4, 17, 2)},
                        tooltip={"placement": "bottom", "always_visible": True}
                    )
                ], width=6),
                dbc.Col([
                    html.Label("Floater Volume (m³)"),
                    dcc.Slider(
                        id="floater-volume-slider",
                        min=0.1, max=1.0, step=0.1, value=0.3,
                        marks={i/10: f"{i/10}" for i in range(1, 11)},
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

def create_advanced_parameters_panel():
    """Create comprehensive advanced parameters panel"""
    return dbc.Card([
        dbc.CardHeader(html.H5("Advanced Parameters", className="mb-0")),
        dbc.CardBody([
            # Physical Properties
            html.H6("Physical Properties", className="text-primary"),
            dbc.Row([
                dbc.Col([
                    html.Label("Floater Mass Empty (kg)"),
                    dcc.Slider(
                        id="floater-mass-slider",
                        min=10, max=30, step=1, value=18,
                        marks={i: str(i) for i in range(10, 31, 5)},
                        tooltip={"placement": "bottom", "always_visible": True}
                    )
                ], width=6),
                dbc.Col([
                    html.Label("Floater Area (m²)"),
                    dcc.Slider(
                        id="floater-area-slider",
                        min=0.01, max=0.1, step=0.005, value=0.035,
                        marks={i/100: f"{i/100:.2f}" for i in range(1, 11, 2)},
                        tooltip={"placement": "bottom", "always_visible": True}
                    )
                ], width=6)
            ], className="mb-3"),
            
            # Pneumatic System
            html.H6("Pneumatic System", className="text-primary"),
            dbc.Row([
                dbc.Col([
                    html.Label("Air Fill Time (s)"),
                    dcc.Slider(
                        id="air-fill-time-slider",
                        min=0.1, max=2.0, step=0.1, value=0.5,
                        marks={i/10: f"{i/10}" for i in range(1, 21, 5)},
                        tooltip={"placement": "bottom", "always_visible": True}
                    )
                ], width=4),
                dbc.Col([
                    html.Label("Air Flow Rate (m³/s)"),
                    dcc.Slider(
                        id="air-flow-rate-slider",
                        min=0.1, max=2.0, step=0.1, value=0.6,
                        marks={i/10: f"{i/10}" for i in range(1, 21, 5)},
                        tooltip={"placement": "bottom", "always_visible": True}
                    )
                ], width=4),
                dbc.Col([
                    html.Label("Jet Efficiency"),
                    dcc.Slider(
                        id="jet-efficiency-slider",
                        min=0.5, max=1.0, step=0.05, value=0.85,
                        marks={i/100: f"{i/100:.2f}" for i in range(50, 101, 10)},
                        tooltip={"placement": "bottom", "always_visible": True}
                    )
                ], width=4)
            ], className="mb-3"),
            
            # Mechanical System
            html.H6("Mechanical System", className="text-primary"),
            dbc.Row([
                dbc.Col([
                    html.Label("Sprocket Radius (m)"),
                    dcc.Slider(
                        id="sprocket-radius-slider",
                        min=0.1, max=1.0, step=0.1, value=0.5,
                        marks={i/10: f"{i/10}" for i in range(1, 11)},
                        tooltip={"placement": "bottom", "always_visible": True}
                    )
                ], width=6),
                dbc.Col([
                    html.Label("Flywheel Inertia (kg⋅m²)"),
                    dcc.Slider(
                        id="flywheel-inertia-slider",
                        min=10, max=100, step=10, value=50,
                        marks={i: str(i) for i in range(10, 101, 20)},
                        tooltip={"placement": "bottom", "always_visible": True}
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
            ])
        ])
    ], className="mb-4")

def create_advanced_controls_panel():
    """Create advanced simulation controls"""
    return dbc.Card([
        dbc.CardHeader(html.H5("Advanced Controls", className="mb-0")),
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    dbc.ButtonGroup([
                        dbc.Button("Single Step", id="step-btn", color="info", size="sm"),
                        dbc.Button("Trigger Pulse", id="pulse-btn", color="warning", size="sm"),
                        dbc.Button("Emergency Stop", id="emergency-btn", color="danger", size="sm")
                    ])
                ], width=8),
                dbc.Col([
                    html.Div(id="advanced-status", className="text-end")
                ], width=4)
            ])
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

# Main App Layout
app.layout = dbc.Container([
    # Data stores for state management
    dcc.Store(id="simulation-data-store"),
    dcc.Store(id="chart-data-store", data={"time": [], "power": [], "torque": [], "efficiency": []}),
    
    # Real-time update interval
    dcc.Interval(
        id="interval-component",
        interval=1000,  # Update every 1 second (1Hz)
        n_intervals=0
    ),
    
    # Layout components
    create_header(),
    create_control_panel(),
    create_metrics_cards(),
    create_charts_section(),
    create_parameters_panel(),
    create_advanced_parameters_panel(),
    create_physics_controls_panel(),
    create_advanced_controls_panel(),
    create_system_overview_panel(),
    
    # Footer
    html.Hr(),
    html.Footer([
        html.P([
            "KPP Simulator Dashboard v2.0 | ",
            html.A("Documentation", href="#", target="_blank"),
            " | Built with Plotly Dash"
        ], className="text-center text-muted")
    ])
], fluid=True)

# Callbacks

@app.callback(
    Output("simulation-data-store", "data"),
    Input("interval-component", "n_intervals"),
    prevent_initial_call=False
)
def update_simulation_data(n_intervals):
    """Update simulation data store with latest data"""
    return get_simulation_data()

@app.callback(
    [Output("power-value", "children"),
     Output("torque-value", "children"),
     Output("efficiency-value", "children"),
     Output("time-value", "children"),
     Output("simulation-status", "children")],
    Input("simulation-data-store", "data")
)
def update_metrics_display(data):
    """Update the metrics cards with current values"""
    if not data:
        return "0 W", "0 Nm", "0%", "0 s", "Not Connected"
    
    power = data.get("power", 0)
    torque = data.get("torque", 0)
    efficiency = data.get("efficiency", 0) * 100  # Convert to percentage
    time_val = data.get("time", 0)
    status = data.get("status", "unknown")
    
    # Format values
    power_str = f"{power:.1f} W" if power < 1000 else f"{power/1000:.2f} kW"
    torque_str = f"{torque:.1f} Nm"
    efficiency_str = f"{efficiency:.1f}%"
    time_str = f"{time_val:.1f} s"
    
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
    
    return power_str, torque_str, efficiency_str, time_str, status_badge

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
    current_chart_data["efficiency"].append(new_data.get("efficiency", 0) * 100)
    
    # Keep only last 100 points for performance
    max_points = 100
    for key in current_chart_data:
        if len(current_chart_data[key]) > max_points:
            current_chart_data[key] = current_chart_data[key][-max_points:]
    
    return current_chart_data

@app.callback(
    Output("power-torque-chart", "figure"),
    Input("chart-data-store", "data")
)
def update_power_torque_chart(chart_data):
    """Update the power and torque chart"""
    if not chart_data or not chart_data.get("time"):
        # Empty chart
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
    
    # Add power trace
    fig.add_trace(go.Scatter(
        x=chart_data["time"],
        y=chart_data["power"],
        mode="lines",
        name="Power (W)",
        line=dict(color="blue", width=2)
    ))
    
    # Add torque trace on secondary y-axis
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
    Input("chart-data-store", "data")
)
def update_efficiency_chart(chart_data):
    """Update the efficiency chart"""
    if not chart_data or not chart_data.get("time"):
        # Empty chart
        fig = go.Figure()
        fig.add_annotation(
            text="No data available",
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
    """Handle simulation control button clicks"""
    global sim_engine
    
    ctx = dash.callback_context
    if not ctx.triggered:
        return False
    
    button_id = ctx.triggered[0]["prop_id"].split(".")[0]
    
    try:
        if button_id == "start-btn" and sim_engine:
            # Update parameters before starting
            params = {
                "num_floaters": int(num_floaters),
                "floater_volume": float(floater_volume),
                "air_pressure": float(air_pressure),
                "pulse_interval": float(pulse_interval)
            }
            
            # Validate parameters
            validation_result = validate_parameters_batch(params)
            if validation_result["valid"]:
                sim_engine.update_params(validation_result["validated_params"])
                sim_engine.running = True
                # Start simulation in background thread if needed
                logger.info("Simulation started")
            else:
                logger.error(f"Parameter validation failed: {validation_result['errors']}")
                
        elif button_id == "stop-btn" and sim_engine:
            sim_engine.running = False
            logger.info("Simulation stopped")
            
        elif button_id == "pause-btn" and sim_engine:
            sim_engine.running = False
            logger.info("Simulation paused")
            
        elif button_id == "reset-btn" and sim_engine:
            sim_engine.reset()
            sim_engine.running = False
            logger.info("Simulation reset")
            
    except Exception as e:
        logger.error(f"Error in simulation control: {e}")
    
    return False  # Never disable start button permanently

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 KPP Simulator Dash Application Starting...")
    print("=" * 60)
    
    # Initialize simulation
    if initialize_simulation():
        print("✅ Simulation engine initialized")
    else:
        print("❌ Failed to initialize simulation engine")
    
    print("🌐 Dashboard will be available at: http://127.0.0.1:8050")
    print("📊 Real-time updates at 1Hz")
    print("Press Ctrl+C to stop the server")
    print("=" * 60)
    
    try:
        app.run(debug=True, host='127.0.0.1', port=8050)
    except Exception as e:
        print(f"❌ Failed to start Dash server: {e}")
        import traceback
        traceback.print_exc()
