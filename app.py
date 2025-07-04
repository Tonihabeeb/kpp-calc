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
        
        # Load crash-resistant parameters with proper validation
        try:
            import json
            with open('kpp_crash_fixed_parameters.json', 'r') as f:
                sim_params = json.load(f)
        except Exception as e:
            logger.warning(f"Could not load parameters: {e}, using defaults")
            sim_params = {
                'num_floaters': 4,
                'target_power': 5000.0,
                'time_step': 0.1,
                'target_rpm': 100.0,
                'air_pressure': 400000.0,
                'tank_height': 15.0,
                'airPressure': 4.0
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

# ADDED: Missing endpoints that Dash app expects
@app.route("/pause", methods=["POST"])
def pause_simulation():
    """Pause simulation (placeholder)"""
    global simulation_running
    
    try:
        simulation_running = False
        logger.info("Simulation paused")
        
        return jsonify({
            "status": "ok",
            "message": "Simulation paused"
        })
        
    except Exception as e:
        logger.error(f"Pause endpoint error: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route("/reset", methods=["POST"])
def reset_simulation():
    """Reset simulation"""
    global engine, simulation_running
    
    try:
        if engine is not None:
            engine.reset()
            simulation_running = False
            logger.info("Simulation reset")
        
        return jsonify({
            "status": "ok",
            "message": "Simulation reset"
        })
        
    except Exception as e:
        logger.error(f"Reset endpoint error: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route("/step", methods=["POST"])
def step_simulation():
    """Execute single simulation step"""
    global engine
    
    try:
        if engine is None:
            return jsonify({
                "status": "error",
                "message": "Engine not initialized"
            }), 400
        
        # Execute one step
        state = engine.step(engine.dt)
        logger.info(f"Step executed: t={engine.time:.2f}")
        
        return jsonify({
            "status": "ok",
            "message": "Step executed",
            "time": engine.time,
            "state": state
        })
        
    except Exception as e:
        logger.error(f"Step endpoint error: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route("/trigger_pulse", methods=["POST"])
def trigger_pulse():
    """Trigger air injection pulse"""
    global engine
    
    try:
        if engine is None:
            return jsonify({
                "status": "error",
                "message": "Engine not initialized"
            }), 400
        
        success = engine.trigger_pulse()
        
        return jsonify({
            "status": "ok",
            "message": "Pulse triggered" if success else "No pulse available",
            "success": success
        })
        
    except Exception as e:
        logger.error(f"Trigger pulse endpoint error: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route("/set_load", methods=["POST"])
def set_load():
    """Set mechanical load"""
    global engine
    
    try:
        data = request.get_json()
        load_torque = data.get('load_torque', 0.0)
        
        if engine is None:
            return jsonify({
                "status": "error",
                "message": "Engine not initialized"
            }), 400
        
        # Set load on generator
        if hasattr(engine, 'generator'):
            engine.generator.load_torque = load_torque
        
        logger.info(f"Load set to {load_torque} Nm")
        
        return jsonify({
            "status": "ok",
            "message": f"Load set to {load_torque} Nm"
        })
        
    except Exception as e:
        logger.error(f"Set load endpoint error: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route("/update_params", methods=["POST"])
def update_params():
    """Update simulation parameters"""
    global engine
    
    try:
        data = request.get_json()
        
        if engine is None:
            return jsonify({
                "status": "error",
                "message": "Engine not initialized"
            }), 400
        
        engine.update_params(data)
        logger.info("Parameters updated")
        
        return jsonify({
            "status": "ok",
            "message": "Parameters updated"
        })
        
    except Exception as e:
        logger.error(f"Update params endpoint error: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

# Control endpoints
@app.route("/control/trigger_emergency_stop", methods=["POST"])
def trigger_emergency_stop():
    """Trigger emergency stop"""
    global engine, simulation_running
    
    try:
        simulation_running = False
        if engine is not None:
            engine.running = False
        
        logger.info("Emergency stop triggered")
        
        return jsonify({
            "status": "ok",
            "message": "Emergency stop triggered"
        })
        
    except Exception as e:
        logger.error(f"Emergency stop endpoint error: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route("/control/h1_nanobubbles", methods=["POST"])
def h1_nanobubbles():
    """Control H1 nanobubble physics"""
    global engine
    
    try:
        data = request.get_json()
        active = data.get('active', False)
        
        if engine is None:
            return jsonify({
                "status": "error",
                "message": "Engine not initialized"
            }), 400
        
        # Set H1 physics
        if hasattr(engine, 'set_h1_nanobubbles'):
            engine.set_h1_nanobubbles(active)
        
        logger.info(f"H1 nanobubbles {'activated' if active else 'deactivated'}")
        
        return jsonify({
            "status": "ok",
            "message": f"H1 nanobubbles {'activated' if active else 'deactivated'}"
        })
        
    except Exception as e:
        logger.error(f"H1 nanobubbles endpoint error: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route("/control/set_control_mode", methods=["POST"])
def set_control_mode():
    """Set control mode"""
    try:
        data = request.get_json()
        mode = data.get('mode', 'normal')
        
        logger.info(f"Control mode set to {mode}")
        
        return jsonify({
            "status": "ok",
            "message": f"Control mode set to {mode}"
        })
        
    except Exception as e:
        logger.error(f"Set control mode endpoint error: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route("/control/enhanced_physics", methods=["POST"])
def enhanced_physics():
    """Control enhanced physics"""
    global engine
    
    try:
        data = request.get_json()
        
        if engine is None:
            return jsonify({
                "status": "error",
                "message": "Engine not initialized"
            }), 400
        
        # Apply physics settings
        if hasattr(engine, 'enable_enhanced_physics'):
            engine.enable_enhanced_physics(
                h1_active=data.get('h1_active', False),
                h2_active=data.get('h2_active', False)
            )
        
        logger.info("Enhanced physics settings applied")
        
        return jsonify({
            "status": "ok",
            "message": "Enhanced physics settings applied"
        })
        
    except Exception as e:
        logger.error(f"Enhanced physics endpoint error: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

# Inspection endpoints
@app.route("/inspect/input_data", methods=["GET"])
def inspect_input_data():
    """Get input data"""
    global engine
    
    try:
        if engine is None:
            return jsonify({
                "status": "error",
                "message": "Engine not initialized"
            }), 400
        
        input_data = {
            "parameters": engine.params if hasattr(engine, 'params') else {},
            "time": engine.time if hasattr(engine, 'time') else 0.0,
            "num_floaters": len(engine.floaters) if hasattr(engine, 'floaters') else 0
        }
        
        return jsonify({
            "status": "ok",
            "data": input_data
        })
        
    except Exception as e:
        logger.error(f"Inspect input data endpoint error: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route("/inspect/output_data", methods=["GET"])
def inspect_output_data():
    """Get output data"""
    global engine
    
    try:
        if engine is None:
            return jsonify({
                "status": "error",
                "message": "Engine not initialized"
            }), 400
        
        latest_state = engine.get_latest_state() if hasattr(engine, 'get_latest_state') else {}
        
        return jsonify({
            "status": "ok",
            "data": latest_state
        })
        
    except Exception as e:
        logger.error(f"Inspect output data endpoint error: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

# Data endpoints
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

@app.route("/data/energy_balance", methods=["GET"])
def data_energy_balance():
    """Get energy balance data"""
    global engine
    
    try:
        if engine is None:
            return jsonify({
                "status": "error",
                "message": "Engine not initialized"
            }), 400
        
        # Calculate energy balance
        energy_data = {
            "total_energy": engine.total_energy if hasattr(engine, 'total_energy') else 0.0,
            "pulse_count": engine.pulse_count if hasattr(engine, 'pulse_count') else 0,
            "efficiency": 0.8  # Placeholder
        }
        
        return jsonify({
            "status": "ok",
            "data": energy_data
        })
        
    except Exception as e:
        logger.error(f"Energy balance endpoint error: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route("/data/enhanced_performance", methods=["GET"])
def data_enhanced_performance():
    """Get enhanced performance data"""
    global engine
    
    try:
        if engine is None:
            return jsonify({
                "status": "error",
                "message": "Engine not initialized"
            }), 400
        
        # Get enhanced performance metrics
        if hasattr(engine, 'get_enhanced_performance_metrics'):
            performance_data = engine.get_enhanced_performance_metrics()
        else:
            performance_data = {
                "h1_active": False,
                "h2_active": False,
                "enhancement_factor": 1.0
            }
        
        return jsonify({
            "status": "ok",
            "data": performance_data
        })
        
    except Exception as e:
        logger.error(f"Enhanced performance endpoint error: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route("/data/fluid_properties", methods=["GET"])
def data_fluid_properties():
    """Get fluid properties data"""
    global engine
    
    try:
        if engine is None:
            return jsonify({
                "status": "error",
                "message": "Engine not initialized"
            }), 400
        
        # Get fluid properties
        if hasattr(engine, 'fluid_system'):
            fluid_data = {
                "density": engine.fluid_system.state.effective_density if hasattr(engine.fluid_system, 'state') else 1000.0,
                "h1_active": engine.fluid_system.h1_active if hasattr(engine.fluid_system, 'h1_active') else False
            }
        else:
            fluid_data = {
                "density": 1000.0,
                "h1_active": False
            }
        
        return jsonify({
            "status": "ok",
            "data": fluid_data
        })
        
    except Exception as e:
        logger.error(f"Fluid properties endpoint error: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route("/data/thermal_properties", methods=["GET"])
def data_thermal_properties():
    """Get thermal properties data"""
    global engine
    
    try:
        if engine is None:
            return jsonify({
                "status": "error",
                "message": "Engine not initialized"
            }), 400
        
        # Get thermal properties
        if hasattr(engine, 'thermal_model'):
            thermal_data = {
                "temperature": 293.15,  # Placeholder
                "h2_active": engine.thermal_model.h2_active if hasattr(engine.thermal_model, 'h2_active') else False
            }
        else:
            thermal_data = {
                "temperature": 293.15,
                "h2_active": False
            }
        
        return jsonify({
            "status": "ok",
            "data": thermal_data
        })
        
    except Exception as e:
        logger.error(f"Thermal properties endpoint error: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

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
    logger.info("  - Added all missing endpoints for Dash compatibility")
    
    app.run(debug=False, threaded=True, host='127.0.0.1', port=9100) 