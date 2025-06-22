# app.py
from flask import Flask, render_template, request, send_file
from simulation.engine_realtime import RealTimeSimulationEngine as SimulationEngine
from simulation.floater import Floater
import os
import json
import io
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import queue

app = Flask(__name__)

# Set up the data queue and initial params for the real-time engine
sim_data_queue = queue.Queue()
sim_params = {
    'num_floaters': 8,
    'floater_volume': 0.04,
    'floater_mass_empty': 2.0,
    'floater_area': 0.1,
    'airPressure': 1.0
}
engine = SimulationEngine(sim_params, sim_data_queue)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/start", methods=["POST"])
def start_simulation():
    params = request.get_json() or {}
    engine.update_params(params)
    # If the data queue is empty, put an initial state
    if engine.data_queue.empty():
        state = engine.collect_state()
        state['torque'] = 0
        state['power'] = 0
        state['velocity'] = 0
        state['floaters'] = [f.to_dict() for f in engine.floaters]
        engine.data_queue.put(state)
    if not getattr(engine, 'running', False):
        import threading
        threading.Thread(target=engine.run, daemon=True).start()
    return ("Simulation started", 200)

@app.route("/stop", methods=["POST"])
def stop_simulation():
    engine.stop()
    return ("Simulation stopped", 200)

@app.route("/update_params", methods=["POST"])
def update_params():
    params = request.get_json() or {}
    engine.update_params(params)
    return ("OK", 200)

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
        'floaters': latest.get('floaters', [])
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
    times, torques, powers = [], [], []
    with engine.data_queue.mutex:
        data_list = list(engine.data_queue.queue)
    for entry in data_list:
        times.append(entry.get('time', 0))
        torques.append(entry.get('torque', 0))
        powers.append(entry.get('power', 0))
    return {
        'time': times,
        'torque': torques,
        'power': powers
    }

@app.route("/reset", methods=["POST"])
def reset_simulation():
    # Stop the engine if running
    engine.stop()
    # Clear the data queue
    with engine.data_queue.mutex:
        engine.data_queue.queue.clear()
    # Reset engine state
    engine.time = 0.0
    engine.data_log = []
    # Recreate floaters with current params
    num_floaters = engine.params.get('num_floaters', 1)
    engine.floaters = [Floater(i, engine.params) for i in range(num_floaters)]
    return ("Simulation reset", 200)

if __name__ == "__main__":
    app.run(debug=True)
