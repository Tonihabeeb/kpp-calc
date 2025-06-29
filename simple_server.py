#!/usr/bin/env python3
"""
Simple KPP Simulator Web Interface Test
Minimal Flask app to test the frontend without full simulation engine
"""

from flask import Flask, render_template, jsonify, Response
import json
import time
import threading
import queue
from collections import deque

app = Flask(__name__)

# Simple test data queue
test_data_queue = queue.Queue()

# Simulate some test data
def generate_test_data():
    """Generate test data for the frontend"""
    while True:
        test_data = {
            "timestamp": time.time(),
            "time": time.time() % 100,  # Reset every 100 seconds
            "torque": 1500 + 500 * (0.5 + 0.5 * time.time() % 1),  # Oscillating torque
            "power": 250000 + 50000 * (0.5 + 0.5 * time.time() % 1),  # Oscillating power
            "efficiency": 0.85 + 0.1 * (0.5 + 0.5 * time.time() % 1),  # Oscillating efficiency
            "system_state": {
                "h1_active": True,
                "h2_active": False,
                "h3_active": True,
                "enhanced_physics_enabled": True
            },
            "enhanced_forces": {
                "h1_nanobubble_force": 100 + 50 * (time.time() % 1),
                "h2_thermal_force": 0,
                "h3_pulse_force": 200 + 100 * (time.time() % 2)
            },
            "parameters": {
                "nanobubble_frac": 0.05,
                "thermal_coeff": 0.0001,
                "pulse_enabled": True
            },
            "floaters": [
                {
                    "id": i,
                    "buoyancy": 800 + 100 * (i + time.time()) % 1,
                    "drag": 50 + 25 * (i + time.time()) % 1,
                    "net_force": 750 + 75 * (i + time.time()) % 1,
                    "pulse_force": 100 if i % 2 == 0 else 0,
                    "position": (i * 45) % 360,
                    "velocity": 2.5 + 0.5 * (i + time.time()) % 1,
                    "state": "filled" if i % 3 == 0 else "empty"
                }
                for i in range(8)
            ]
        }
        test_data_queue.put(test_data)
        time.sleep(0.1)  # 10Hz update rate

# Start test data generation in background
data_thread = threading.Thread(target=generate_test_data, daemon=True)
data_thread.start()

@app.route('/')
def index():
    """Serve the main dashboard"""
    return render_template('index.html')

@app.route('/stream')
def stream():
    """Server-Sent Events endpoint for real-time data"""
    def event_stream():
        while True:
            try:
                if not test_data_queue.empty():
                    data = test_data_queue.get()
                else:
                    # Send heartbeat
                    data = {
                        "heartbeat": True,
                        "timestamp": time.time(),
                        "server_status": "running"
                    }
                
                yield f"data: {json.dumps(data)}\n\n"
                time.sleep(0.1)
                
            except GeneratorExit:
                break
            except Exception as e:
                print(f"Stream error: {e}")
                yield f"data: {json.dumps({'error': str(e)})}\n\n"

    response = Response(event_stream(), mimetype="text/event-stream")
    response.headers["Cache-Control"] = "no-cache"
    response.headers["Access-Control-Allow-Origin"] = "*"
    return response

@app.route('/start', methods=['POST'])
def start_simulation():
    """Start simulation (test endpoint)"""
    return jsonify({"status": "success", "message": "Test simulation started"})

@app.route('/stop', methods=['POST'])
def stop_simulation():
    """Stop simulation (test endpoint)"""
    return jsonify({"status": "success", "message": "Test simulation stopped"})

@app.route('/set_params', methods=['POST'])
def set_params():
    """Set parameters (test endpoint)"""
    return jsonify({"status": "success", "message": "Parameters updated (test mode)"})

@app.route('/get_output_schema', methods=['GET'])
def get_output_schema():
    """Get API schema (test endpoint)"""
    return jsonify({
        "api_version": "1.0-test",
        "status": "Test mode - simplified KPP simulator",
        "endpoints": ["/", "/stream", "/start", "/stop", "/set_params"]
    })

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "mode": "test",
        "timestamp": time.time(),
        "message": "KPP Simulator Test Interface Running"
    })

if __name__ == '__main__':
    print("🚀 Starting KPP Simulator Test Interface...")
    print("📊 Dashboard: http://localhost:5000")
    print("❤️  Health Check: http://localhost:5000/health")
    print("📡 Data Stream: http://localhost:5000/stream")
    print("=" * 50)
    
    try:
        app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)
    except Exception as e:
        print(f"❌ Server failed to start: {e}")
        import traceback
        traceback.print_exc()
