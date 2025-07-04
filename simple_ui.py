import dash
from dash import dcc, html, Input, Output, callback
import dash_bootstrap_components as dbc
import requests
import json
import time

# Configuration
BACKEND_URL = "http://localhost:9100"
UI_PORT = 9103

# Create simple working Dash app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "Simple KPP Control"

app.layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            html.H1("KPP Simulator - Simple Control", className="text-center mb-4"),
            html.Hr(),
            
            # Status display
            html.Div(id="status-display", className="mb-3"),
            
            # Control buttons
            dbc.ButtonGroup([
                dbc.Button("Start Simulation", id="start-btn", color="success", className="me-2"),
                dbc.Button("Stop Simulation", id="stop-btn", color="danger", className="me-2"),
                dbc.Button("Check Status", id="status-btn", color="info")
            ], className="mb-3"),
            
            # Output area
            html.Div(id="output-area", className="mt-3"),
            
            # Auto-refresh
            dcc.Interval(id="auto-refresh", interval=2000, n_intervals=0)
        ])
    ])
], fluid=True)

@app.callback(
    Output("output-area", "children"),
    [Input("start-btn", "n_clicks"),
     Input("stop-btn", "n_clicks"),
     Input("status-btn", "n_clicks")],
    prevent_initial_call=True
)
def handle_buttons(start_clicks, stop_clicks, status_clicks):
    ctx = dash.callback_context
    if not ctx.triggered:
        return ""
    
    button_id = ctx.triggered[0]["prop_id"].split(".")[0]
    
    try:
        if button_id == "start-btn":
            response = requests.post(f"{BACKEND_URL}/start", timeout=5)
            return dbc.Alert(f"Start: {response.json()}", color="success")
        elif button_id == "stop-btn":
            response = requests.post(f"{BACKEND_URL}/stop", timeout=5)
            return dbc.Alert(f"Stop: {response.json()}", color="warning")
        elif button_id == "status-btn":
            response = requests.get(f"{BACKEND_URL}/status", timeout=5)
            data = response.json()
            return dbc.Alert(f"Status: {data.get('simulation_engine', 'unknown')}", color="info")
    except Exception as e:
        return dbc.Alert(f"Error: {e}", color="danger")

@app.callback(
    Output("status-display", "children"),
    Input("auto-refresh", "n_intervals")
)
def update_status(n):
    try:
        response = requests.get(f"{BACKEND_URL}/status", timeout=2)
        data = response.json()
        status = data.get('simulation_engine', 'unknown')
        color = "success" if status == "running" else "secondary"
        return dbc.Badge(f"Simulation: {status}", color=color, className="fs-6")
    except:
        return dbc.Badge("Simulation: disconnected", color="danger", className="fs-6")

if __name__ == "__main__":
    print(f"Starting Simple KPP UI on http://localhost:{UI_PORT}")
    app.run(debug=False, host="0.0.0.0", port=UI_PORT) 