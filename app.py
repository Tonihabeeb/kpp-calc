# Flask web app entry point
# All endpoints interact with the SimulationEngine only
# Handles real-time simulation, streaming, and control requests

# app.py
from flask import Flask, render_template, request, send_file, Response
from simulation.engine import SimulationEngine
from simulation.components.floater import Floater
import os
import json
import io
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import queue
import threading
import time
import logging

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Set up the data queue and initial params for the real-time engine
sim_data_queue = queue.Queue()
sim_params = {
    'num_floaters': 8,
    'floater_volume': 0.3,  # Larger volume for better buoyancy
    'floater_mass_empty': 18.0,  # Heavier for more realistic mass
    'floater_area': 0.035,  # Smaller cross-sectional area for less drag
    'airPressure': 3.0,
    # New pulse physics parameters
    'air_fill_time': 0.5,
    'air_pressure': 300000,
    'air_flow_rate': 0.6,
    'jet_efficiency': 0.85,
    'sprocket_radius': 0.5,
    'flywheel_inertia': 50.0,
    'pulse_interval': 2.0,
    # H1/H2 effect parameters
    'nanobubble_frac': 0.0,  # H1: nanobubble fraction (0-1)
    'thermal_coeff': 0.0001,  # H2: thermal expansion coefficient
    'water_temp': 20.0,  # Current water temperature (°C)
    'ref_temp': 20.0,  # Reference temperature (°C)
    # Generator: 530kW @ 375RPM (load calculated automatically)
}
engine = SimulationEngine(sim_params, sim_data_queue)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/stream")
def stream():
    """Server-Sent Events endpoint for real-time data streaming"""
    def event_stream():
        while True:
            try:
                # Get latest data from engine
                if not engine.data_queue.empty():
                    data = engine.data_queue.get()
                    yield f"data: {json.dumps(data)}\n\n"
                else:
                    # Send heartbeat
                    yield f"data: {json.dumps({'heartbeat': True})}\n\n"
                time.sleep(0.1)
            except GeneratorExit:
                break
            except Exception as e:
                yield f"data: {json.dumps({'error': str(e)})}\n\n"
    
    return Response(event_stream(), mimetype='text/event-stream')

@app.route("/start", methods=["POST"])
def start_simulation():
    logging.debug("/start endpoint triggered.")
    params = request.get_json() or {}
    logging.debug(f"Received params: {params}")
    engine.update_params(params)
    # If the data queue is empty, put an initial state
    if engine.data_queue.empty():
        state = engine.collect_state()
        state['torque'] = 0
        state['power'] = 0
        state['velocity'] = 0
        state['floaters'] = [f.to_dict() for f in engine.floaters]
        engine.data_queue.put(state)
        logging.debug("Initial state added to data queue.")
    # Always start a new simulation thread if not alive
    if not engine.thread or not engine.thread.is_alive():
        engine.running = True
        engine.thread = threading.Thread(target=engine.run, daemon=True)
        engine.thread.start()
        logging.debug("Simulation thread started.")
    return ("Simulation started", 200)

@app.route("/stop", methods=["POST"])
def stop_simulation():
    engine.running = False
    return ("Simulation stopped", 200)

@app.route("/pause", methods=["POST"])
def pause_simulation():
    engine.running = False
    return ("Simulation paused", 200)

@app.route("/step", methods=["POST"])
def step_simulation():
    """Perform a single simulation step"""
    engine.step(engine.dt)
    return ("Step completed", 200)

@app.route("/trigger_pulse", methods=["POST"])
def trigger_pulse():
    """Manually trigger an air injection pulse"""
    success = engine.trigger_pulse()
    if success:
        return ("Pulse triggered", 200)
    else:
        return ("No available floater for pulse", 400)

@app.route("/update_params", methods=["POST"])
def update_params():
    params = request.get_json() or {}
    engine.update_params(params)
    return ("OK", 200)

@app.route("/set_params", methods=["POST"])
def set_params():
    """Set parameters endpoint as specified in GuideV3.md"""
    data = request.get_json() or {}
    
    # Update simulation parameters immediately
    if 'nanobubble_frac' in data:
        engine.params['nanobubble_frac'] = float(data['nanobubble_frac'])
    if 'thermal_coeff' in data:
        engine.params['thermal_coeff'] = float(data['thermal_coeff'])
    if 'water_temp' in data:
        engine.params['water_temp'] = float(data['water_temp'])
    if 'num_floaters' in data:
        new_num = int(data['num_floaters'])
        if new_num != len(engine.floaters):
            engine.floaters = [Floater(volume=engine.params.get('floater_volume', 0.3),
                                       mass=engine.params.get('floater_mass_empty', 18.0),
                                       area=engine.params.get('floater_area', 0.035),
                                       Cd=engine.params.get('floater_Cd', 0.8))
                               for _ in range(new_num)]
        engine.params['num_floaters'] = new_num
    if 'air_pressure' in data:
        engine.params['air_pressure'] = float(data['air_pressure'])
    if 'pulse_interval' in data:
        engine.params['pulse_interval'] = float(data['pulse_interval'])
    
    # Update engine with new params
    engine.update_params(engine.params)
    return ('', 204)

@app.route("/data/summary")
def summary_data():
    # Get the latest data from the queue if available
    try:
        latest = engine.data_queue.queue[-1] if not engine.data_queue.empty() else None
    except Exception:
        latest = None
    if not latest:
        return {}
    # Use the instantaneous values directly from the simulation state
    return {
        'time': latest.get('time', 0),
        'torque': latest.get('torque', 0),
        'power': latest.get('power', 0),
        'velocity': latest.get('velocity', 0),
        'floaters': latest.get('floaters', []),
        'pulse_torque': latest.get('pulse_torque', 0),
        'base_torque': latest.get('base_torque', 0),
        'pulse_count': latest.get('pulse_count', 0),
        'flywheel_speed': latest.get('flywheel_speed', 0),
        'chain_speed': latest.get('chain_speed', 0),
        'clutch_engaged': latest.get('clutch_engaged', False)
    }

@app.route("/chart/<metric>.png")
def chart_image(metric):
    # Collect history from the queue for plotting
    times, torques, powers = [], [], []
    with engine.data_queue.mutex:
        data_list = list(engine.data_queue.queue)
    for entry in data_list:
        times.append(entry.get('time', 0))
        floaters = entry.get('floaters', [])
        torques.append(sum(f.get('force', 0) for f in floaters))
        powers.append(sum(f.get('force', 0) * f.get('velocity', 0) for f in floaters))
    fig, ax = plt.subplots(figsize=(6, 3))
    fig.patch.set_facecolor('white')
    ax.set_facecolor('white')
    if metric == "torque" and times:
        ax.plot(times, torques, color='blue')
        ax.set_ylabel("Torque (Nm)")
    elif metric == "power" and times:
        ax.plot(times, powers, color='green')
        ax.set_ylabel("Power (W)")
    else:
        ax.text(0.5, 0.5, "No data", ha='center', va='center', fontsize=16)
    ax.set_xlabel("Time (s)")
    buf = io.BytesIO()
    plt.tight_layout()
    plt.savefig(buf, format='png', facecolor=fig.get_facecolor())
    plt.close(fig)
    buf.seek(0)
    return send_file(buf, mimetype='image/png')

@app.route("/data/history")
def data_history():
    # Return full time series for torque and power (instantaneous values)
    times, torques, powers, pulse_torques = [], [], [], []
    with engine.data_queue.mutex:
        data_list = list(engine.data_queue.queue)
    for entry in data_list:
        times.append(entry.get('time', 0))
        torques.append(entry.get('torque', 0))
        powers.append(entry.get('power', 0))
        pulse_torques.append(entry.get('pulse_torque', 0))
    return {
        'time': times,
        'torque': torques,
        'power': powers,
        'pulse_torque': pulse_torques
    }

@app.route("/reset", methods=["POST"])
def reset_simulation():
    engine.running = False
    with engine.data_queue.mutex:
        engine.data_queue.queue.clear()
    engine.time = 0.0
    engine.data_log = []
    engine.total_energy = 0.0
    engine.total_distance = 0.0
    engine.pulse_count = 0
    engine.last_pulse_time = 0.0
    # Reset pulse physics
    engine.pulse_physics.omega_chain = 0.0
    engine.pulse_physics.omega_flywheel = 0.0
    engine.pulse_physics.clutch_engaged = False
    # Reset floaters
    num_floaters = engine.params.get('num_floaters', 1)
    engine.floaters = [Floater(volume=engine.params.get('floater_volume', 0.3),
                             mass=engine.params.get('floater_mass_empty', 18.0),
                             area=engine.params.get('floater_area', 0.035),
                             Cd=engine.params.get('floater_Cd', 0.8))
                   for _ in range(num_floaters)]
    return ("Simulation reset", 200)

@app.route('/download_csv')
def download_csv():
    """CSV export endpoint as specified in GuideV3.md"""
    def generate_csv():
        # CSV header
        yield 'time,torque,power,efficiency,pulse_torque,chain_speed,flywheel_speed\n'
        
        # Get data from engine's data log
        with engine.data_queue.mutex:
            data_list = list(engine.data_queue.queue)
        
        for entry in data_list:
            time_val = entry.get('time', 0)
            torque_val = entry.get('torque', 0)
            power_val = entry.get('power', 0)
            efficiency_val = entry.get('efficiency', 0)
            pulse_torque_val = entry.get('pulse_torque', 0)
            chain_speed_val = entry.get('chain_speed', 0)
            flywheel_speed_val = entry.get('flywheel_speed', 0)
            
            yield f"{time_val},{torque_val},{power_val},{efficiency_val},{pulse_torque_val},{chain_speed_val},{flywheel_speed_val}\n"
    
    # Stream CSV to client with proper headers
    response = Response(generate_csv(), mimetype='text/csv')
    response.headers['Content-Disposition'] = 'attachment; filename="sim_data.csv"'
    return response

if __name__ == "__main__":
    app.run(debug=True, threaded=True)
