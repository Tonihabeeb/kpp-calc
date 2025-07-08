#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KPP Simulator Dash Application
Main entry point for the Plotly Dash frontend
"""

import time
import requests
import json
import logging
import dash_bootstrap_components as dbc
import dash
from dash import dcc, html, Input, Output, State, callback
from datetime import datetime
import plotly.graph_objs as go

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Dash app
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    suppress_callback_exceptions=True
)

# App layout
app.layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            html.H1("🚀 KPP Simulator Dashboard", className="text-center mb-4"),
            html.Hr()
        ])
    ]),
    
    # Status Section
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("📊 System Status"),
                dbc.CardBody([
                    html.Div(id="system-status", children="Loading..."),
                    dcc.Interval(id="status-interval", interval=1000, n_intervals=0)
                ])
            ])
        ], width=6),
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("⚡ Performance Metrics"),
                dbc.CardBody([
                    html.Div(id="performance-metrics", children="Loading..."),
                    dcc.Interval(id="metrics-interval", interval=2000, n_intervals=0)
                ])
            ])
        ], width=6)
    ], className="mb-4"),
    
    # Control Section
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("🎛️ Simulation Controls"),
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            dbc.Button("▶️ Start", id="start-btn", color="success", className="me-2"),
                            dbc.Button("⏸️ Pause", id="pause-btn", color="warning", className="me-2"),
                            dbc.Button("⏹️ Stop", id="stop-btn", color="danger", className="me-2"),
                        ])
                    ], className="mb-3"),
                    dbc.Row([
                        dbc.Col([
                            html.Label("Number of Floaters:"),
                            dcc.Slider(
                                id="num-floaters-slider",
                                min=4, max=100, step=2, value=66,
                                marks={i: str(i) for i in [4, 20, 40, 60, 80, 100]}
                            )
                        ])
                    ])
                ])
            ])
        ], width=6),
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("⚙️ Parameters"),
                dbc.CardBody([
                    html.Div(id="parameters-display", children="Loading parameters..."),
                    dcc.Interval(id="params-interval", interval=5000, n_intervals=0)
                ])
            ])
        ], width=6)
    ], className="mb-4"),
    
    # Charts Section
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("📈 Real-time Charts"),
                dbc.CardBody([
                    dcc.Graph(id="power-chart", style={"height": "300px"}),
                    dcc.Interval(id="chart-interval", interval=1000, n_intervals=0)
                ])
            ])
        ])
    ], className="mb-4"),
    
    # Logs Section
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("📝 System Logs"),
                dbc.CardBody([
                    html.Div(id="logs-display", style={"height": "200px", "overflow-y": "scroll"}),
                    dcc.Interval(id="logs-interval", interval=3000, n_intervals=0)
                ])
            ])
        ])
    ])
], fluid=True)

# Callbacks
@app.callback(
    Output("system-status", "children"),
    Input("status-interval", "n_intervals")
)
def update_system_status(n):
    """Update system status"""
    try:
        response = requests.get("http://localhost:9100/status", timeout=2)
        if response.status_code == 200:
            data = response.json()
            is_running = data.get("is_running", False)
            status_color = "success" if is_running else "danger"
            status_text = "🟢 Running" if is_running else "🔴 Stopped"
            
            return [
                dbc.Alert(f"Status: {status_text}", color=status_color, className="mb-2"),
                html.P(f"Timestamp: {datetime.now().strftime('%H:%M:%S')}"),
                html.P(f"Components: {len(data.get('components', {}))} active")
            ]
        else:
            return dbc.Alert("❌ Cannot connect to backend", color="danger")
    except Exception as e:
        return dbc.Alert(f"❌ Error: {str(e)}", color="danger")

@app.callback(
    Output("performance-metrics", "children"),
    Input("metrics-interval", "n_intervals")
)
def update_performance_metrics(n):
    """Update performance metrics"""
    try:
        response = requests.get("http://localhost:9100/status", timeout=2)
        if response.status_code == 200:
            data = response.json()
            components = data.get("components", {})
            
            # Extract metrics
            drivetrain = components.get("drivetrain", {})
            power = drivetrain.get("electrical_power", 0)
            torque = drivetrain.get("mechanical_torque", 0)
            efficiency = drivetrain.get("efficiency", 0)
            
            return [
                html.P(f"⚡ Power: {power:.1f} kW"),
                html.P(f"🔧 Torque: {torque:.1f} N·m"),
                html.P(f"📊 Efficiency: {efficiency:.1%}"),
                html.P(f"🕒 Last Update: {datetime.now().strftime('%H:%M:%S')}")
            ]
        else:
            return html.P("❌ No data available")
    except Exception as e:
        return html.P(f"❌ Error: {str(e)}")

@app.callback(
    Output("parameters-display", "children"),
    Input("params-interval", "n_intervals")
)
def update_parameters(n):
    """Update parameters display"""
    try:
        response = requests.get("http://localhost:9100/parameters/defaults", timeout=2)
        if response.status_code == 200:
            params = response.json()
            
            return [
                html.P(f"🏊 Floaters: {params.get('num_floaters', 'N/A')}"),
                html.P(f"📦 Volume: {params.get('floater_volume', 'N/A')} m³"),
                html.P(f"💨 Pressure: {params.get('air_pressure', 'N/A')/1000:.1f} kPa"),
                html.P(f"⏱️ Interval: {params.get('pulse_interval', 'N/A')} s")
            ]
        else:
            return html.P("❌ Cannot load parameters")
    except Exception as e:
        return html.P(f"❌ Error: {str(e)}")

@app.callback(
    Output("power-chart", "figure"),
    Input("chart-interval", "n_intervals")
)
def update_power_chart(n):
    """Update power chart"""
    try:
        response = requests.get("http://localhost:9100/status", timeout=2)
        if response.status_code == 200:
            data = response.json()
            components = data.get("components", {})
            drivetrain = components.get("drivetrain", {})
            
            # Create sample data (in real implementation, this would be historical data)
            power = drivetrain.get("electrical_power", 0)
            torque = drivetrain.get("mechanical_torque", 0)
            
            # Create time series data
            now = datetime.now()
            times = [now.strftime('%H:%M:%S')]
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=times,
                y=[power],
                mode='lines+markers',
                name='Electrical Power (kW)',
                line=dict(color='blue')
            ))
            fig.add_trace(go.Scatter(
                x=times,
                y=[torque/100],  # Scale torque for visibility
                mode='lines+markers',
                name='Torque/100 (N·m)',
                line=dict(color='red')
            ))
            
            fig.update_layout(
                title="Real-time Power and Torque",
                xaxis_title="Time",
                yaxis_title="Value",
                height=300
            )
            
            return fig
        else:
            # Return empty chart
            return go.Figure().add_annotation(
                text="No data available",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False
            )
    except Exception as e:
        # Return error chart
        return go.Figure().add_annotation(
            text=f"Error: {str(e)}",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False
        )

@app.callback(
    Output("logs-display", "children"),
    Input("logs-interval", "n_intervals")
)
def update_logs(n):
    """Update system logs"""
    try:
        # In a real implementation, this would fetch actual logs
        logs = [
            f"[{datetime.now().strftime('%H:%M:%S')}] System running normally",
            f"[{datetime.now().strftime('%H:%M:%S')}] All components healthy",
            f"[{datetime.now().strftime('%H:%M:%S')}] Performance metrics updated"
        ]
        
        return [html.P(log) for log in logs]
    except Exception as e:
        return html.P(f"Error loading logs: {str(e)}")

# Control callbacks
@app.callback(
    Output("start-btn", "disabled"),
    Output("pause-btn", "disabled"),
    Output("stop-btn", "disabled"),
    Input("start-btn", "n_clicks"),
    Input("pause-btn", "n_clicks"),
    Input("stop-btn", "n_clicks"),
    prevent_initial_call=True
)
def handle_control_buttons(start_clicks, pause_clicks, stop_clicks):
    """Handle control button clicks"""
    ctx = dash.callback_context
    if not ctx.triggered:
        return False, False, False
    
    button_id = ctx.triggered[0]["prop_id"].split(".")[0]
    
    try:
        if button_id == "start-btn":
            response = requests.post("http://localhost:9100/start", timeout=2)
            if response.status_code == 200:
                return True, False, False
        elif button_id == "pause-btn":
            # Pause functionality would be implemented here
            return False, True, False
        elif button_id == "stop-btn":
            response = requests.post("http://localhost:9100/stop", timeout=2)
            if response.status_code == 200:
                return False, False, True
    except Exception as e:
        logger.error(f"Control error: {e}")
    
    return False, False, False

@app.callback(
    Output("num-floaters-slider", "value"),
    Input("num-floaters-slider", "value")
)
def update_floaters(value):
    """Update number of floaters"""
    try:
        # In a real implementation, this would update the simulation parameters
        logger.info(f"Updating floaters to: {value}")
        return value
    except Exception as e:
        logger.error(f"Floaters update error: {e}")
        return value

if __name__ == "__main__":
    logger.info("Starting KPP Simulator Dashboard...")
    logger.info("Dashboard will be available at: http://localhost:9103")
    
    try:
        app.run(
            host="0.0.0.0",
            port=9103,
            debug=False,
            dev_tools_hot_reload=False
        )
    except Exception as e:
        logger.error(f"Dashboard startup error: {e}")
        raise

