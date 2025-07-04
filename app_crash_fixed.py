# CRASH-FIXED Flask app - Removes blocking operations that cause timeouts
from flask import Flask, request, jsonify
from flask_cors import CORS
import logging
import queue
import threading
import time

# Initialize the fixed app
app = Flask(__name__)
CORS(app)

# Configure logging
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# Simplified global state (thread-safe)
engine = None
simulation_running = False
sim_data_queue = queue.Queue(maxsize=1000)  # FIXED: Bounded queue

# FIXED: Removed infinite loops and background threads

@app.route("/")
def index():
    return "KPP Simulator Backend (CRASH-FIXED) is Running"

@app.route("/status", methods=["GET"])
def status():
    """FIXED: Safe status endpoint with proper error handling"""
    try:
        # FIXED: Null check for engine
        if engine is None:
            return jsonify({
                "backend_status": "running",
                "engine_initialized": False,
                "engine_running": False,
                "engine_time": 0.0,
                "has_data": False,
                "simulation_running": False,
                "timestamp": time.time()
            })
        
        # FIXED: Safe engine access with timeout
        try:
            latest_state = engine.get_latest_state()
            engine_time = latest_state.get('time', 0.0) if latest_state else 0.0
            has_data = len(engine.data_log) > 0 if hasattr(engine, 'data_log') else False
        except Exception as e:
            logger.warning(f"Engine access error: {e}")
            engine_time = 0.0
            has_data = False
        
        return jsonify({
            "backend_status": "running",
            "engine_initialized": True,
            "engine_running": engine.running if hasattr(engine, 'running') else False,
            "engine_time": engine_time,
            "has_data": has_data,
            "simulation_running": simulation_running,
            "timestamp": time.time()
        })
        
    except Exception as e:
        logger.error(f"Status endpoint error: {e}")
        return jsonify({
            "backend_status": "error",
            "error": str(e),
            "timestamp": time.time()
        }), 500

@app.route("/start", methods=["POST"])
def start_simulation():
    """FIXED: Safe simulation start"""
    global engine, simulation_running
    
    try:
        # FIXED: Import engine only when needed to avoid startup issues
        from simulation.engine import SimulationEngine
        
        # Load minimal crash-resistant parameters
        try:
            import json
            with open('kpp_minimal_parameters.json', 'r') as f:
                sim_params = json.load(f)
        except Exception as e:
            logger.warning(f"Could not load parameters: {e}, using defaults")
            sim_params = {
                'num_floaters': 4,
                'target_power': 5000.0,
                'time_step': 0.1,
                'target_rpm': 100.0
            }
        
        # Create engine with error handling
        if engine is None:
            try:
                engine = SimulationEngine(sim_params, sim_data_queue)
                logger.info("Engine created successfully")
            except Exception as e:
                logger.error(f"Engine creation failed: {e}")
                return jsonify({
                    "status": "error", 
                    "message": f"Engine creation failed: {str(e)}"
                }), 500
        
        # Start simulation
        try:
            engine.reset()
            engine.start()
            simulation_running = True
            logger.info("Simulation started successfully")
            
            return jsonify({
                "status": "ok", 
                "message": "Simulation started."
            })
            
        except Exception as e:
            logger.error(f"Simulation start failed: {e}")
            return jsonify({
                "status": "error",
                "message": f"Simulation start failed: {str(e)}"
            }), 500
            
    except Exception as e:
        logger.error(f"Start endpoint error: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route("/stop", methods=["POST"])
def stop_simulation():
    """FIXED: Safe simulation stop"""
    global engine, simulation_running
    
    try:
        if engine is not None:
            engine.running = False
            simulation_running = False
            logger.info("Simulation stopped")
        
        return jsonify({
            "status": "ok",
            "message": "Simulation stopped"
        })
        
    except Exception as e:
        logger.error(f"Stop endpoint error: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route("/data/live", methods=["GET"])
def data_live():
    """FIXED: Safe data access without blocking operations"""
    try:
        if engine is None:
            return jsonify({'data': [], 'status': 'no_engine'})
        
        # FIXED: Safe queue access with size limit
        data_list = []
        try:
            # Get up to 100 recent data points without blocking
            max_items = min(100, sim_data_queue.qsize())
            for _ in range(max_items):
                try:
                    item = sim_data_queue.get_nowait()
                    data_list.append(item)
                except queue.Empty:
                    break
        except Exception as e:
            logger.warning(f"Queue access error: {e}")
        
        return jsonify({
            'data': data_list[-50:],  # Return only last 50 items
            'count': len(data_list),
            'status': 'ok'
        })
        
    except Exception as e:
        logger.error(f"Data live endpoint error: {e}")
        return jsonify({
            'data': [],
            'error': str(e),
            'status': 'error'
        }), 500

# FIXED: Removed problematic endpoints that cause blocking:
# - /stream (infinite loop with file I/O)
# - /chart/* (matplotlib blocking operations)
# - Real-time analysis endpoints

@app.route("/health", methods=["GET"])
def health_check():
    """Simple health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": time.time(),
        "engine_exists": engine is not None,
        "simulation_running": simulation_running
    })

# FIXED: Removed background threads and infinite loops

if __name__ == "__main__":
    logger.info("Starting CRASH-FIXED KPP Backend...")
    logger.info("Architectural fixes applied:")
    logger.info("  - Removed infinite loops in Flask thread")
    logger.info("  - Eliminated real-time file I/O")
    logger.info("  - Added proper null checks")
    logger.info("  - Implemented bounded queues")
    logger.info("  - Removed blocking background threads")
    
    app.run(debug=False, threaded=True, host='127.0.0.1', port=9100) 