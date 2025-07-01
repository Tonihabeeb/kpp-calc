# Flask web app entry point
# All endpoints interact with the SimulationEngine only
# Handles real-time simulation, streaming, and control requests

# app.py
from flask import Flask, render_template, request, send_file, Response
from simulation.engine import SimulationEngine
from simulation.components.floater import Floater
from utils.backend_logger import setup_backend_logger
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
import csv
from collections import deque
from flask_cors import CORS

# Initialize the backend logger
setup_backend_logger('simulation.log')

app = Flask(__name__)
CORS(app)

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
engine.reset()

# Add a global list to store simulation data for analysis
collected_data = []

# Thread-safe deque for real-time input/output data collection
# Store input and output data for analysis
input_data = deque(maxlen=1000)  # Store the last 1000 inputs
output_data = deque(maxlen=1000)  # Store the last 1000 outputs

# Background thread for real-time analysis
def analyze_data():
    while True:
        try:
            # Analyze input data
            if input_data:
                latest_input = input_data[-1]
                app.logger.debug(f"Analyzing input: {latest_input}")

            # Analyze output data
            if output_data:
                latest_output = output_data[-1]
                app.logger.debug(f"Analyzing output: {latest_output}")

            time.sleep(0.5)  # Adjust analysis frequency as needed
        except Exception as e:
            app.logger.error(f"Error in data analysis thread: {e}")

# Start the analysis thread
analysis_thread = threading.Thread(target=analyze_data, daemon=True)
analysis_thread.start()

@app.before_request
def log_request_info():
    app.logger.info("Request Headers: %s", request.headers)
    app.logger.info("Request Body: %s", request.get_data())

@app.after_request
def log_response_info(response):
    app.logger.info("Response Status: %s", response.status)
    app.logger.info("Response Headers: %s", response.headers)

    # Collect data from the /data/summary endpoint for analysis
    if request.endpoint == 'summary_data' and response.status_code == 200:
        try:
            data = response.get_json()
            collected_data.append(data)
        except Exception as e:
            app.logger.error(f"Failed to collect data: {e}")

    # Collect output data from responses
    try:
        if response.status_code == 200 and request.endpoint:
            output_record = {
                'endpoint': request.endpoint,
                'status_code': response.status_code,
                'data': response.get_json() if response.is_json else {},
                'timestamp': time.time()
            }
            output_data.append(output_record)
    except Exception as e:
        app.logger.error(f"Failed to collect output data: {e}")
    
    return response

@app.route("/")
def index():
    return "KPP Simulator Backend is Running. Use the Dash UI at http://localhost:8050"

@app.route("/stream")
def stream():
    """Server-Sent Events endpoint for real-time data streaming"""
    import csv
    import os
    log_file = 'realtime_log.csv'
    # Align CSV fields with SimulationEngine.log_state() output
    log_fields = [
        'time', 'power', 'torque', 'base_buoy_torque', 'pulse_torque', 'total_chain_torque',
        'tau_net', 'tau_to_generator', 'clutch_c', 'clutch_state', 'total_energy', 'pulse_count',
        'flywheel_speed_rpm', 'chain_speed_rpm', 'clutch_engaged', 'tank_pressure',
        'overall_efficiency', 'avg_floater_velocity'
    ]
    # Write header if file does not exist
    if not os.path.exists(log_file):
        with open(log_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=log_fields)
            writer.writeheader()

    def event_stream():
        while True:
            try:
                # Get latest data from engine
                if not engine.data_queue.empty():
                    data = engine.data_queue.get()
                    output_data.append(data)  # Collect data for analysis
                    # Write to CSV in real time
                    with open(log_file, 'a', newline='') as f:
                        writer = csv.DictWriter(f, fieldnames=log_fields)
                        # Map engine state keys directly to CSV columns
                        row = {k: data.get(k, '') for k in log_fields}
                        writer.writerow(row)
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
    app.logger.info("/start endpoint triggered.")
    try:
        params = request.get_json() or {}
        app.logger.info(f"Received start params: {params}")
        # Reset engine for clean start
        engine.reset()
        engine.update_params(params)
        engine.log_state(
            power_output=0.0,
            torque=0.0,
            base_buoy_force=0.0,
            pulse_force=0.0,
            total_vertical_force=0.0,
            tau_net=0.0,
            tau_to_generator=0.0,
            clutch_c=(engine.clutch.state.c if engine.clutch.state else 0.0),
            clutch_state=(engine.clutch.state.state if engine.clutch.state else None)
        )
        # Start simulation thread if not already running
        if not hasattr(engine, 'thread') or engine.thread is None or not engine.thread.is_alive():
            engine.running = True
            engine.thread = threading.Thread(target=engine.run, daemon=True)
            engine.thread.start()
            app.logger.info("Simulation thread started.")
        else:
            app.logger.info("Simulation thread already running.")
        return ("Simulation started", 200)
    except Exception as e:
        app.logger.error(f"Error in /start: {e}")
        return (json.dumps({"status": "error", "message": str(e)}), 500, {'ContentType':'application/json'})

@app.route("/stop", methods=["POST"])
def stop_simulation():
    app.logger.info("/stop endpoint triggered.")
    try:
        engine.running = False
        if hasattr(engine, 'thread') and engine.thread is not None:
            app.logger.info("Simulation thread stopped.")
        return ("Simulation stopped", 200)
    except Exception as e:
        app.logger.error(f"Error in /stop: {e}")
        return (json.dumps({"status": "error", "message": str(e)}), 500, {'ContentType':'application/json'})

@app.route("/pause", methods=["POST"])
def pause_simulation():
    app.logger.info("/pause endpoint triggered.")
    try:
        engine.running = False
        app.logger.info("Simulation paused.")
        return ("Simulation paused", 200)
    except Exception as e:
        app.logger.error(f"Error in /pause: {e}")
        return (json.dumps({"status": "error", "message": str(e)}), 500, {'ContentType':'application/json'})

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
def set_simulation_params():
    """Endpoint to dynamically update simulation parameters."""
    params = request.get_json() or {}
    engine.update_params(params)
    return (json.dumps({'status': 'ok', 'updated_params': params}), 200, {'ContentType':'application/json'})

@app.route("/data/summary")
def summary_data():
    # Get the latest data from the queue if available
    try:
        latest = engine.data_queue.queue[-1] if not engine.data_queue.empty() else None
    except Exception:
        latest = None
    if not latest:
        return {}
    # Map to engine state keys
    return {
        'time': latest.get('time', 0),
        'torque': latest.get('torque', 0),
        'power': latest.get('power', 0),
        'avg_floater_velocity': latest.get('avg_floater_velocity', 0),
        'floaters': latest.get('floaters', []),
        'pulse_torque': latest.get('pulse_torque', 0),
        'base_buoy_torque': latest.get('base_buoy_torque', 0),
        'pulse_count': latest.get('pulse_count', 0),
        'flywheel_speed_rpm': latest.get('flywheel_speed_rpm', 0),
        'chain_speed_rpm': latest.get('chain_speed_rpm', 0),
        'clutch_engaged': latest.get('clutch_engaged', False),
        'overall_efficiency': latest.get('overall_efficiency', 0)
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
    # Return full time series for all simulation state metrics
    with engine.data_queue.mutex:
        data_list = list(engine.data_queue.queue)
    # Define all history fields
    history_fields = [
        'time', 'power', 'torque', 'base_buoy_torque', 'pulse_torque', 'total_chain_torque',
        'tau_net', 'tau_to_generator', 'clutch_c', 'clutch_state', 'total_energy', 'pulse_count',
        'flywheel_speed_rpm', 'chain_speed_rpm', 'clutch_engaged', 'tank_pressure',
        'overall_efficiency', 'avg_floater_velocity'
    ]
    # Build lists for each field
    history = {}
    for field in history_fields:
        history[field] = [entry.get(field, 0) for entry in data_list]
    return history

@app.route("/reset", methods=["POST"])
def reset_simulation():
    app.logger.info("/reset endpoint triggered.")
    try:
        engine.reset()
        engine.running = False
        app.logger.info("Simulation reset.")
        return ("Simulation reset", 200)
    except Exception as e:
        app.logger.error(f"Error in /reset: {e}")
        return (json.dumps({"status": "error", "message": str(e)}), 500, {'ContentType':'application/json'})

@app.route('/download_csv')
def download_csv():
    """CSV export endpoint as specified in GuideV3.md"""
    def generate_csv():
        # Updated CSV header to include all relevant fields
        yield 'time,torque,power,base_buoy_torque,pulse_torque,total_chain_torque,tau_net,tau_to_generator,clutch_c,clutch_state,flywheel_speed,chain_speed,clutch_engaged,pulse_count\n'
        
        # Get data from engine's data log
        with engine.data_queue.mutex:
            data_list = list(engine.data_queue.queue)
        
        for entry in data_list:
            yield f"{entry.get('time', 0)},{entry.get('torque', 0)},{entry.get('power', 0)},{entry.get('base_buoy_torque', 0)},{entry.get('pulse_torque', 0)},{entry.get('total_chain_torque', 0)},{entry.get('tau_net', 0)},{entry.get('tau_to_generator', 0)},{entry.get('clutch_c', 0)},{entry.get('clutch_state', '')},{entry.get('flywheel_speed_rpm', 0)},{entry.get('chain_speed_rpm', 0)},{entry.get('clutch_engaged', 0)},{entry.get('pulse_count', 0)}\n"
    
    # Stream CSV to client with proper headers
    response = Response(generate_csv(), mimetype='text/csv')
    response.headers['Content-Disposition'] = 'attachment; filename="sim_data.csv"'
    return response

@app.route('/export_collected_data', methods=['GET'])
def export_collected_data():
    """Export collected simulation data to a CSV file."""
    output_file = 'collected_simulation_data.csv'
    try:
        with open(output_file, 'w', newline='') as csvfile:
            fieldnames = ['time', 'torque', 'power', 'velocity', 'pulse_torque', 'base_torque', 'pulse_count', 'flywheel_speed', 'chain_speed', 'clutch_engaged']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            writer.writeheader()
            writer.writerows(collected_data)

        return send_file(output_file, as_attachment=True)
    except Exception as e:
        app.logger.error(f"Failed to export collected data: {e}")
        return ("Failed to export data", 500)

@app.route('/inspect/input_data', methods=['GET'])
def inspect_input_data():
    """Endpoint to inspect collected input data."""
    try:
        return {'input_data': list(input_data)}, 200
    except Exception as e:
        app.logger.error(f"Failed to retrieve input data: {e}")
        return {'error': 'Failed to retrieve input data'}, 500

@app.route('/inspect/output_data', methods=['GET'])
def inspect_output_data():
    """Endpoint to inspect collected output data."""
    try:
        return {'output_data': list(output_data)}, 200
    except Exception as e:
        app.logger.error(f"Failed to retrieve output data: {e}")
        return {'error': 'Failed to retrieve output data'}, 500

# Thread for real-time analysis
def analyze_real_time_data():
    while True:
        if output_data:
            try:
                # Analyze the latest data
                latest_data = output_data[-1]
                app.logger.debug(f"Analyzing data: {latest_data}")

                # Monitor key metrics
                torque = latest_data.get('torque', 0)
                power = latest_data.get('power', 0)
                efficiency = latest_data.get('efficiency', 0)
                clutch_engaged = latest_data.get('clutch_engaged', False)

                # Log behavioral insights
                if clutch_engaged:
                    app.logger.info(f"Clutch engaged at time {latest_data.get('time', 0):.2f}s.")
                if efficiency < 50:
                    app.logger.warning(f"Low efficiency detected: {efficiency:.2f}% at time {latest_data.get('time', 0):.2f}s.")
                if torque > 1000:
                    app.logger.warning(f"High torque spike detected: {torque:.2f} Nm at time {latest_data.get('time', 0):.2f}s.")

                # Add more behavioral analysis as needed

                time.sleep(0.1)  # Adjust analysis frequency as needed
            except Exception as e:
                app.logger.error(f"Error during real-time analysis: {e}")

# Start the analysis thread
analysis_thread = threading.Thread(target=analyze_real_time_data, daemon=True)
analysis_thread.start()

@app.route("/set_load", methods=["POST"])
def set_load():
    """Set the generator load torque (Nm) via user input."""
    data = request.get_json() or {}
    user_load = data.get('user_load_torque', None)
    if user_load is not None:
        engine.generator.set_user_load(float(user_load))
        return (f"User load set to {user_load} Nm", 200)
    else:
        return ("Missing user_load_torque in request", 400)

@app.route('/data/live', methods=['GET'])
def data_live():
    """Return the full simulation data log as JSON for direct analysis."""
    with engine.data_queue.mutex:
        data_list = list(engine.data_queue.queue)
    return {'data': data_list}, 200

@app.route("/data/pneumatic_status")
def pneumatic_status():
    """Get comprehensive pneumatic system status including performance and energy data"""
    try:
        latest = engine.data_queue.queue[-1] if not engine.data_queue.empty() else None
    except Exception:
        latest = None
    
    if not latest:
        return {'status': 'no_data'}
    
    pneumatic_data = {
        'tank_pressure': latest.get('tank_pressure', 0.0),
        'performance': latest.get('pneumatic_performance', {}),
        'energy': latest.get('pneumatic_energy', {}),
        'optimization': latest.get('pneumatic_optimization', {}),
        'timestamp': latest.get('time', 0.0)
    }
    
    return pneumatic_data

@app.route("/data/optimization_recommendations")
def optimization_recommendations():
    """Get current optimization recommendations from the pneumatic performance analyzer"""
    try:
        if hasattr(engine, 'pneumatic_performance_analyzer'):
            recommendations = engine.pneumatic_performance_analyzer.generate_optimization_recommendations()
            return {
                'recommendations': [
                    {
                        'target': rec.target.value,
                        'expected_improvement': rec.expected_improvement,
                        'confidence': rec.confidence,
                        'description': rec.description,
                        'priority': 'medium'  # Default priority
                    }
                    for rec in recommendations
                ],
                'count': len(recommendations),
                'timestamp': engine.time
            }
        else:
            return {'recommendations': [], 'count': 0, 'error': 'Performance analyzer not available'}
    except Exception as e:
        return {'recommendations': [], 'count': 0, 'error': str(e)}

@app.route("/data/energy_balance")
def energy_balance():
    """Get detailed energy balance information from the pneumatic energy analyzer"""
    try:
        if hasattr(engine, 'pneumatic_energy_analyzer'):
            energy_summary = engine.pneumatic_energy_analyzer.get_energy_summary()
            conservation = engine.pneumatic_energy_analyzer.validate_energy_conservation()
            
            return {
                'energy_summary': energy_summary or {},
                'conservation': conservation or {},
                'timestamp': engine.time
            }
        else:
            return {'error': 'Energy analyzer not available'}
    except Exception as e:
        return {'error': str(e)}

# ========================================================================================
# PHASE 8: INTEGRATED SYSTEMS API ENDPOINTS
# ========================================================================================

@app.route("/data/drivetrain_status")
def drivetrain_status():
    """Get comprehensive drivetrain system status from integrated drivetrain"""
    try:
        latest = engine.data_queue.queue[-1] if not engine.data_queue.empty() else None
    except Exception:
        latest = None
    
    if not latest:
        return {'status': 'no_data'}
    
    # Extract drivetrain data from the latest simulation state
    drivetrain_data = {
        'flywheel_speed_rpm': latest.get('flywheel_speed_rpm', 0.0),
        'chain_speed_rpm': latest.get('chain_speed_rpm', 0.0),
        'clutch_engaged': latest.get('clutch_engaged', False),
        'system_efficiency': latest.get('system_efficiency', 0.0),
        'gearbox_output_torque': latest.get('gearbox_output_torque', 0.0),
        'chain_tension': latest.get('chain_tension', 0.0),
        'sprocket_torque': latest.get('sprocket_torque', 0.0),
        'flywheel_stored_energy': latest.get('flywheel_stored_energy', 0.0),
        'power_flow': {
            'input_power': latest.get('mechanical_power_input', 0.0),
            'output_power': latest.get('power', 0.0),
            'power_loss': latest.get('total_power_loss', 0.0)
        },
        'advanced_metrics': {
            'clutch_engagement_factor': latest.get('clutch_c', 0.0),
            'operating_time': latest.get('time', 0.0),
            'pulse_count': latest.get('pulse_count', 0),
            'overall_efficiency': latest.get('overall_efficiency', 0.0)
        },
        'timestamp': latest.get('time', 0.0)
    }
    
    return drivetrain_data

@app.route("/data/electrical_status")
def electrical_status():
    """Get comprehensive electrical system status from integrated electrical system"""
    try:
        latest = engine.data_queue.queue[-1] if not engine.data_queue.empty() else None
    except Exception:
        latest = None
    
    if not latest:
        return {'status': 'no_data'}
    
    # Extract electrical system data
    electrical_data = {
        'grid_power_output': latest.get('grid_power_output', 0.0),
        'electrical_efficiency': latest.get('electrical_efficiency', 0.0),
        'electrical_load_torque': latest.get('electrical_load_torque', 0.0),
        'synchronized': latest.get('electrical_synchronized', False),
        'load_factor': latest.get('electrical_load_factor', 0.0),
        'grid_voltage': latest.get('grid_voltage', 480.0),
        'grid_frequency': latest.get('grid_frequency', 60.0),
        'power_quality': {
            'power_factor': latest.get('power_factor', 0.0),
            'voltage_regulation': latest.get('voltage_regulation', 1.0),
            'frequency_stability': latest.get('frequency_stability', 0.0)
        },
        'performance_metrics': {
            'total_energy_generated_kwh': latest.get('total_energy_generated_kwh', 0.0),
            'total_energy_delivered_kwh': latest.get('total_energy_delivered_kwh', 0.0),
            'operating_hours': latest.get('operating_hours', 0.0),
            'capacity_factor_percent': latest.get('capacity_factor_percent', 0.0)
        },
        'timestamp': latest.get('time', 0.0)
    }
    
    return electrical_data

@app.route("/data/control_status")
def control_status():
    """Get comprehensive control system status from integrated control system"""
    try:
        latest = engine.data_queue.queue[-1] if not engine.data_queue.empty() else None
    except Exception:
        latest = None
    
    if not latest:
        return {'status': 'no_data'}
    
    # Extract control system data
    control_data = {
        'control_mode': latest.get('control_mode', 'normal'),
        'timing_commands': latest.get('timing_commands', {}),
        'load_commands': latest.get('load_commands', {}),
        'grid_commands': latest.get('grid_commands', {}),
        'fault_status': latest.get('fault_status', {}),
        'control_performance': latest.get('control_performance', {}),
        'pneumatic_control_executed': latest.get('pneumatic_control_executed', False),
        'system_health': latest.get('system_health', 1.0),
        'emergency_status': latest.get('emergency_status', {}),
        'system_status': latest.get('system_status', {}),
        'timestamp': latest.get('time', 0.0)
    }
    
    return control_data

@app.route("/data/grid_services_status")
def grid_services_status():
    """Get comprehensive grid services status and performance"""
    try:
        latest = engine.data_queue.queue[-1] if not engine.data_queue.empty() else None
    except Exception:
        latest = None
    
    if not latest:
        return {'status': 'no_data'}
    
    # Extract grid services data
    grid_services_data = latest.get('grid_services', {})
    grid_services_performance = latest.get('grid_services_performance', {})
    
    combined_data = {
        'grid_services': grid_services_data,
        'performance_metrics': grid_services_performance,
        'coordination_status': grid_services_data.get('coordination_status', 'Unknown'),
        'active_services_count': grid_services_data.get('service_count', 0),
        'total_power_command_mw': grid_services_data.get('total_power_command_mw', 0.0),
        'active_services': grid_services_data.get('active_services', []),
        'timestamp': latest.get('time', 0.0)
    }
    
    return combined_data

@app.route("/data/enhanced_losses")
def enhanced_losses_status():
    """Get detailed loss analysis from the enhanced loss model"""
    try:
        latest = engine.data_queue.queue[-1] if not engine.data_queue.empty() else None
    except Exception:
        latest = None
    
    if not latest:
        return {'status': 'no_data'}
    
    # Extract enhanced loss model data
    enhanced_losses = latest.get('enhanced_losses', {})
    thermal_state = latest.get('thermal_state', {})
    component_temperatures = latest.get('component_temperatures', {})
    
    loss_data = {
        'total_system_losses': enhanced_losses.get('total_system_losses', 0.0),
        'system_efficiency': enhanced_losses.get('system_efficiency', 0.0),
        'mechanical_losses': enhanced_losses.get('mechanical_losses', {}),
        'electrical_losses': enhanced_losses.get('electrical_losses', 0.0),
        'thermal_losses': enhanced_losses.get('thermal_losses', 0.0),
        'thermal_state': thermal_state,
        'component_temperatures': component_temperatures,
        'timestamp': latest.get('time', 0.0)
    }
    
    return loss_data

@app.route("/data/system_overview")
def system_overview():
    """Get comprehensive system overview combining all integrated systems"""
    try:
        latest = engine.data_queue.queue[-1] if not engine.data_queue.empty() else None
    except Exception:
        latest = None
    
    if not latest:
        return {'status': 'no_data'}
    
    # Combine key metrics from all systems
    overview = {
        'system_status': {
            'operational': engine.running,
            'simulation_time': latest.get('time', 0.0),
            'overall_efficiency': latest.get('overall_efficiency', 0.0),
            'total_energy': latest.get('total_energy', 0.0),
            'pulse_count': latest.get('pulse_count', 0)
        },
        'power_generation': {
            'mechanical_power': latest.get('mechanical_power_input', 0.0),
            'electrical_power': latest.get('grid_power_output', 0.0),
            'grid_synchronized': latest.get('electrical_synchronized', False),
            'load_factor': latest.get('electrical_load_factor', 0.0)
        },
        'mechanical_systems': {
            'flywheel_speed_rpm': latest.get('flywheel_speed_rpm', 0.0),
            'chain_tension': latest.get('chain_tension', 0.0),
            'clutch_engaged': latest.get('clutch_engaged', False),
            'system_efficiency': latest.get('system_efficiency', 0.0)
        },
        'control_systems': {
            'control_mode': latest.get('control_mode', 'normal'),
            'faults_active': len(latest.get('fault_status', {}).get('active_faults', [])),
            'pneumatic_control_active': latest.get('pneumatic_control_executed', False),
            'system_health': latest.get('system_health', 1.0)
        },
        'grid_services': {
            'services_active': latest.get('grid_services', {}).get('service_count', 0),
            'power_command_mw': latest.get('grid_services', {}).get('total_power_command_mw', 0.0),
            'coordination_status': latest.get('grid_services', {}).get('coordination_status', 'Unknown')
        },
        'pneumatic_systems': {
            'tank_pressure': latest.get('tank_pressure', 0.0),
            'average_efficiency': latest.get('pneumatic_performance', {}).get('average_efficiency', 0.0),
            'optimization_opportunities': len(latest.get('pneumatic_optimization', {}).get('latest_recommendations', []))
        },
        'thermal_management': {
            'component_temperatures': latest.get('component_temperatures', {}),
            'thermal_efficiency': latest.get('thermal_state', {}).get('overall_thermal_efficiency', 1.0),
            'cooling_active': latest.get('thermal_state', {}).get('cooling_system_active', False)
        },
        'timestamp': latest.get('time', 0.0)
    }
    
    return overview

@app.route("/control/set_control_mode", methods=["POST"])
def set_control_mode():
    """Set the control system mode (normal, emergency, manual, etc.)"""
    data = request.get_json() or {}
    control_mode = data.get('control_mode', 'normal')
    
    try:
        # This would typically call a method on the integrated control system
        # For now, we'll update the simulation parameters
        engine.update_params({'control_mode': control_mode})
        return {'status': 'success', 'control_mode': control_mode}, 200
    except Exception as e:
        return {'status': 'error', 'message': str(e)}, 500

@app.route("/control/trigger_emergency_stop", methods=["POST"])
def trigger_emergency_stop():
    """Trigger emergency stop sequence"""
    data = request.get_json() or {}
    reason = data.get('reason', 'Manual emergency stop')
    
    try:
        if hasattr(engine, 'trigger_emergency_stop'):
            response = engine.trigger_emergency_stop(reason)
            return {'status': 'success', 'emergency_response': response}, 200
        else:
            # Fallback to stopping the simulation
            engine.running = False
            return {'status': 'success', 'message': 'Simulation stopped (emergency)'}, 200
    except Exception as e:
        return {'status': 'error', 'message': str(e)}, 500

@app.route("/control/initiate_startup", methods=["POST"])
def initiate_startup():
    """Initiate controlled system startup sequence"""
    data = request.get_json() or {}
    reason = data.get('reason', 'Manual startup')
    
    try:
        if hasattr(engine, 'initiate_startup'):
            success = engine.initiate_startup(reason)
            return {'status': 'success', 'startup_initiated': success}, 200
        else:
            # Fallback to starting the simulation
            engine.running = True
            if not engine.thread or not engine.thread.is_alive():
                engine.thread = threading.Thread(target=engine.run, daemon=True)
                engine.thread.start()
            return {'status': 'success', 'message': 'Simulation started'}, 200
    except Exception as e:
        return {'status': 'error', 'message': str(e)}, 500

@app.route("/data/transient_status")
def transient_status():
    """Get transient event controller status"""
    try:
        if hasattr(engine, 'get_transient_status'):
            status = engine.get_transient_status()
            return {'status': 'success', 'transient_status': status}, 200
        else:
            return {'status': 'unavailable', 'message': 'Transient controller not available'}, 200
    except Exception as e:
        return {'status': 'error', 'message': str(e)}, 500

# ========================================================================================
# PHYSICS MODULES API ENDPOINTS (Chain, Fluid, Thermal)
# ========================================================================================

@app.route("/data/physics_status")
def physics_status():
    """Get comprehensive physics modules status"""
    try:
        if hasattr(engine, 'get_physics_status'):
            status = engine.get_physics_status()
            return {'status': 'success', 'physics_status': status}, 200
        else:
            return {'status': 'unavailable', 'message': 'Physics modules not available'}, 200
    except Exception as e:
        return {'status': 'error', 'message': str(e)}, 500

@app.route("/control/h1_nanobubbles", methods=["POST"])
def control_h1_nanobubbles():
    """Control H1 nanobubble effects"""
    try:
        data = request.get_json()
        active = data.get('active', False)
        bubble_fraction = data.get('bubble_fraction', 0.05)
        drag_reduction = data.get('drag_reduction', 0.1)
        
        if hasattr(engine, 'set_h1_nanobubbles'):
            engine.set_h1_nanobubbles(active, bubble_fraction, drag_reduction)
            return {'status': 'success', 'h1_active': active, 
                   'bubble_fraction': bubble_fraction, 'drag_reduction': drag_reduction}, 200
        else:
            return {'status': 'unavailable', 'message': 'H1 control not available'}, 200
    except Exception as e:
        return {'status': 'error', 'message': str(e)}, 500

@app.route("/control/h2_thermal", methods=["POST"])
def control_h2_thermal():
    """Control H2 thermal effects"""
    try:
        data = request.get_json()
        active = data.get('active', False)
        efficiency = data.get('efficiency', 0.8)
        buoyancy_boost = data.get('buoyancy_boost', 0.05)
        compression_improvement = data.get('compression_improvement', 0.15)
        
        if hasattr(engine, 'set_h2_thermal'):
            engine.set_h2_thermal(active, efficiency, buoyancy_boost, compression_improvement)
            return {'status': 'success', 'h2_active': active, 'efficiency': efficiency,
                   'buoyancy_boost': buoyancy_boost, 'compression_improvement': compression_improvement}, 200
        else:
            return {'status': 'unavailable', 'message': 'H2 control not available'}, 200
    except Exception as e:
        return {'status': 'error', 'message': str(e)}, 500

@app.route("/control/water_temperature", methods=["POST"])
def set_water_temperature():
    """Set water temperature"""
    try:
        data = request.get_json()
        temperature = data.get('temperature', 20.0)  # Default 20°C
        
        if hasattr(engine, 'set_water_temperature'):
            engine.set_water_temperature(temperature)
            return {'status': 'success', 'temperature': temperature}, 200
        else:
            return {'status': 'unavailable', 'message': 'Temperature control not available'}, 200
    except Exception as e:
        return {'status': 'error', 'message': str(e)}, 500

@app.route("/control/enhanced_physics", methods=["POST"])
def control_enhanced_physics():
    """Enable/disable both H1 and H2 enhanced physics effects"""
    try:
        data = request.get_json()
        h1_active = data.get('h1_active', True)
        h2_active = data.get('h2_active', True)
        enable = data.get('enable', True)
        
        if hasattr(engine, 'enable_enhanced_physics') and hasattr(engine, 'disable_enhanced_physics'):
            if enable:
                engine.enable_enhanced_physics(h1_active, h2_active)
            else:
                engine.disable_enhanced_physics()
            return {'status': 'success', 'enabled': enable, 'h1_active': h1_active, 'h2_active': h2_active}, 200
        else:
            return {'status': 'unavailable', 'message': 'Enhanced physics control not available'}, 200
    except Exception as e:
        return {'status': 'error', 'message': str(e)}, 500

@app.route("/data/enhanced_performance")
def enhanced_performance():
    """Get enhanced performance metrics with H1/H2 effects"""
    try:
        if hasattr(engine, 'get_enhanced_performance_metrics'):
            metrics = engine.get_enhanced_performance_metrics()
            return {'status': 'success', 'metrics': metrics}, 200
        else:
            return {'status': 'unavailable', 'message': 'Enhanced performance metrics not available'}, 200
    except Exception as e:
        return {'status': 'error', 'message': str(e)}, 500

@app.route("/data/fluid_properties")
def fluid_properties():
    """Get current fluid system properties"""
    try:
        if hasattr(engine, 'fluid_system'):
            properties = engine.fluid_system.get_fluid_properties()
            return {'status': 'success', 'fluid_properties': properties}, 200
        else:
            return {'status': 'unavailable', 'message': 'Fluid system not available'}, 200
    except Exception as e:
        return {'status': 'error', 'message': str(e)}, 500

@app.route("/data/thermal_properties")
def thermal_properties():
    """Get current thermal system properties"""
    try:
        if hasattr(engine, 'thermal_model'):
            properties = engine.thermal_model.get_thermal_properties()
            return {'status': 'success', 'thermal_properties': properties}, 200
        else:
            return {'status': 'unavailable', 'message': 'Thermal system not available'}, 200
    except Exception as e:
        return {'status': 'error', 'message': str(e)}, 500

@app.route("/data/chain_status")
def chain_status():
    """Get current chain system status"""
    try:
        if hasattr(engine, 'chain_system'):
            status = engine.chain_system.get_state()
            return {'status': 'success', 'chain_status': status}, 200
        else:
            return {'status': 'unavailable', 'message': 'Chain system not available'}, 200
    except Exception as e:
        return {'status': 'error', 'message': str(e)}, 500

# ========================================================================================
# END PHYSICS MODULES API ENDPOINTS
# ========================================================================================

# ========================================================================================
# END PHASE 8: INTEGRATED SYSTEMS API ENDPOINTS
# ========================================================================================

if __name__ == "__main__":
    app.run(debug=True, threaded=True)
