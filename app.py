import logging
import time
from flask import Flask, jsonify, request
from flask_cors import CORS

# Import simulation components
from simulation.managers.thread_safe_engine import ThreadSafeEngine
from config.parameter_schema import get_default_parameters, get_parameter_constraints, validate_parameters_batch

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Initialize thread-safe simulation engine at startup
engine = ThreadSafeEngine(config=get_default_parameters())

@app.route('/start', methods=['POST'])
def start_simulation():
    """Start the simulation"""
    try:
        engine.start()
        logger.info("Simulation started successfully")
        return jsonify({"status": "running"})
    except Exception as e:
        logger.error(f"Failed to start simulation: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/stop', methods=['POST'])
def stop_simulation():
    """Stop the simulation"""
    try:
        engine.stop()
        logger.info("Simulation stopped successfully")
        return jsonify({"status": "stopped"})
    except Exception as e:
        logger.error(f"Failed to stop simulation: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/status')
def get_status():
    """Get current simulation status"""
    try:
        state = engine.get_state()
        return jsonify(state)
    except Exception as e:
        logger.error(f"Failed to get status: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/parameters/defaults')
def get_default_parameters_endpoint():
    """Get default parameters"""
    try:
        return jsonify(get_default_parameters())
    except Exception as e:
        logger.error(f"Failed to get default parameters: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/parameters/constraints')
def get_parameter_constraints_endpoint():
    """Get parameter constraints"""
    try:
        return jsonify(get_parameter_constraints())
    except Exception as e:
        logger.error(f"Failed to get parameter constraints: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/parameters', methods=['POST'])
def update_parameters():
    """Update simulation parameters"""
    try:
        new_params = request.get_json()
        if not new_params:
            return jsonify({"error": "No parameters provided"}), 400
        
        # Validate parameters
        validation_result = validate_parameters_batch(new_params)
        if not validation_result.get("valid", False):
            return jsonify({"error": "Invalid parameters", "details": validation_result.get("errors", [])}), 400
        
        # For now, just return success - parameter application will be handled in later phases
        return jsonify({"status": "valid", "message": "Parameters validated successfully"})
        
    except Exception as e:
        logger.error(f"Failed to update parameters: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=9100, threaded=True)
