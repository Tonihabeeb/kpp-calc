"""
Simulation API Routes
"""

from typing import Dict, Any
from datetime import datetime
import json
import time
import logging

from flask import Blueprint, Response, jsonify, render_template, request, current_app, stream_with_context
from utils.component_manager import get_component_manager

simulation_bp = Blueprint('simulation', __name__)

@simulation_bp.route('/api/simulation/control', methods=['POST'])
def control_simulation():
    """Control simulation execution"""
    try:
        logger = logging.getLogger("simulation_api")
        data = request.get_json()
        if not data or 'action' not in data:
            return jsonify({
                'error': 'Missing action parameter'
            }), 400
        
        action = data['action']
        if action not in ['start', 'pause', 'reset', 'speed']:
            return jsonify({
                'error': 'Invalid action. Must be "start", "pause", "reset", or "speed"'
            }), 400
        
        # Get component manager
        component_manager = get_component_manager()
        
        # Debug: print state before action
        logger.info(f"Simulation state before action '{action}': {component_manager.get_simulation_state()}")
        
        success = False
        message = ""
        
        if action == 'start':
            # Start simulation (non-blocking)
            try:
                success = component_manager.start_simulation()
                if success:
                    message = 'Simulation started successfully'
                else:
                    message = 'Simulation failed to start (may already be running)'
            except Exception as e:
                success = False
                message = f'Error starting simulation: {str(e)}'
            
        elif action == 'pause':
            success = component_manager.pause_simulation()
            message = 'Simulation paused successfully'
            
        elif action == 'reset':
            success = component_manager.reset_simulation()
            message = 'Simulation reset successfully'
            
        elif action == 'speed':
            speed = data.get('speed', 1.0)
            success = component_manager.set_simulation_speed(speed)
            message = f'Simulation speed set to {speed}x'
        
        # Debug: print state after action
        logger.info(f"Simulation state after action '{action}': {component_manager.get_simulation_state()}")
        if success:
            return jsonify({
                'success': True,
                'message': message
            })
        else:
            return jsonify({
                'error': f'Failed to {action} simulation'
            }), 500
            
    except Exception as e:
        import traceback
        logging.getLogger("simulation_api").error(f"Exception in control_simulation: {e}\n{traceback.format_exc()}")
        return jsonify({
            'error': f'Error controlling simulation: {str(e)}'
        }), 500

def generate_simulation_data():
    """Generate simulation data stream with 3D floater positions"""
    from flask import current_app
    
    while True:
        try:
            # Wrap the entire generator logic in an application context
            with current_app.app_context():
                # Get component manager directly from Flask app extensions
                component_manager = current_app.extensions['component_manager']
                
                # Get current simulation state (simplified)
                state = component_manager.get_simulation_state()
                
                # Create simplified data structure to avoid complex access
                data = {
                    'timestamp': datetime.now().isoformat(),
                    
                    # Basic metrics from state dictionary
                    'power': state.get('power', 0),
                    'torque': state.get('torque', 0),
                    'rpm': state.get('rpm', 0),
                    'efficiency': state.get('efficiency', 0),
                    'step_count': state.get('step_count', 0),
                    'simulation_status': state.get('status', 'unknown'),
                    
                    # Simplified component states
                    'electrical': {
                        'voltage': state.get('component_states', {}).get('electrical_system', {}).get('voltage', 0),
                        'current': state.get('component_states', {}).get('electrical_system', {}).get('current', 0)
                    },
                    'mechanical': {
                        'chain_speed': state.get('component_states', {}).get('mechanical_system', {}).get('chain_speed', 0),
                        'clutch_engaged': state.get('component_states', {}).get('mechanical_system', {}).get('clutch_engaged', False)
                    },
                    'pneumatic': {
                        'pressure': state.get('component_states', {}).get('pneumatic_system', {}).get('pressure', 0),
                        'compressor_active': state.get('component_states', {}).get('pneumatic_system', {}).get('compressor_active', False)
                    },
                    
                    # Simplified floater data (no complex object access)
                    'floaters': [
                        {
                            'id': i,
                            'position': (i / 60) * 10.0,
                            'velocity': 0.0,
                            'is_buoyant': i < 30
                        }
                        for i in range(60)
                    ],
                    
                    # Enhancement states
                    'enhancements': {
                        'h1_enabled': state.get('h1_active', False),
                        'h2_enabled': state.get('h2_active', False),
                        'h3_enabled': state.get('h3_active', False)
                    }
                }
                
                # Send data
                yield f"data: {json.dumps(data)}\n\n"
            
            # Wait before next update
            time.sleep(0.1)  # 10Hz update rate
            
        except Exception as e:
            print(f"Error generating simulation data: {e}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
            time.sleep(1)  # Wait longer on error

@simulation_bp.route('/stream')
def stream():
    """Stream simulation data"""
    return Response(
        stream_with_context(generate_simulation_data()),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive'
        }
    )

@simulation_bp.route('/api/simulation/state')
def get_simulation_state():
    """Get current simulation state with diagnostics"""
    try:
        component_manager = get_component_manager()
        state = component_manager.get_simulation_state()
        
        # Get system diagnostics
        diagnostics = {
            'system_health': 'healthy',
            'warnings': [],
            'errors': [],
            'performance_metrics': {
                'cpu_usage': 0.0,
                'memory_usage': 0.0,
                'simulation_fps': 10.0,
                'last_update_time': datetime.now().isoformat()
            }
        }
        
        # Check for potential issues
        try:
            if state.get('power', 0) < -100:
                diagnostics['warnings'].append('High power consumption detected')
                diagnostics['system_health'] = 'warning'
            
            if abs(state.get('torque', 0)) > 1000:
                diagnostics['warnings'].append('High torque detected - check system load')
                diagnostics['system_health'] = 'warning'
            
            if state.get('rpm', 0) > 100:
                diagnostics['warnings'].append('High RPM detected - check for overspeed')
                diagnostics['system_health'] = 'warning'
            
            if state.get('efficiency', 0) < 0:
                diagnostics['warnings'].append('Negative efficiency detected')
                diagnostics['system_health'] = 'warning'
                
        except Exception as diag_error:
            diagnostics['errors'].append(f'Diagnostic error: {str(diag_error)}')
            diagnostics['system_health'] = 'error'
        
        return jsonify({
            'timestamp': datetime.now().isoformat(),
            'power': state.get('power', 0),
            'torque': state.get('torque', 0),
            'rpm': state.get('rpm', 0),
            'efficiency': state.get('efficiency', 0),
            'mechanical_efficiency': state.get('mechanical_efficiency', 0),
            'electrical_efficiency': state.get('electrical_efficiency', 0),
            'total_energy': state.get('total_energy', 0),
            'step_count': state.get('step_count', 0),
            'status': state.get('status', 'unknown'),
            'diagnostics': diagnostics
        })
    except Exception as e:
        return jsonify({
            'error': f'Error getting simulation state: {str(e)}',
            'diagnostics': {
                'system_health': 'error',
                'errors': [f'State retrieval failed: {str(e)}'],
                'warnings': [],
                'performance_metrics': {
                    'cpu_usage': 0.0,
                    'memory_usage': 0.0,
                    'simulation_fps': 0.0,
                    'last_update_time': datetime.now().isoformat()
                }
            }
        }), 500

@simulation_bp.route('/api/simulation/parameters', methods=['POST'])
def update_parameters():
    """Update simulation parameters with validation"""
    try:
        data = request.get_json()
        if not data or 'parameter' not in data or 'value' not in data:
            return jsonify({
                'error': 'Missing parameter or value'
            }), 400
        
        parameter = data['parameter']
        value = data['value']
        
        # Parameter validation rules
        validation_rules = {
            'floater_count': {
                'min': 10,
                'max': 100,
                'type': int,
                'message': 'Floater count must be between 10 and 100'
            },
            'floater_mass': {
                'min': 1.0,
                'max': 20.0,
                'type': float,
                'message': 'Floater mass must be between 1.0 and 20.0 kg'
            },
            'chain_tension': {
                'min': 100.0,
                'max': 2000.0,
                'type': float,
                'message': 'Chain tension must be between 100 and 2000 N'
            },
            'water_level': {
                'min': 2.0,
                'max': 15.0,
                'type': float,
                'message': 'Water level must be between 2.0 and 15.0 m'
            },
            'h1_intensity': {
                'min': 0,
                'max': 100,
                'type': int,
                'message': 'H1 intensity must be between 0 and 100%'
            },
            'h2_intensity': {
                'min': 0,
                'max': 100,
                'type': int,
                'message': 'H2 intensity must be between 0 and 100%'
            },
            'h3_intensity': {
                'min': 0,
                'max': 100,
                'type': int,
                'message': 'H3 intensity must be between 0 and 100%'
            },
            'enable_h1': {
                'type': bool,
                'message': 'H1 enable must be boolean'
            },
            'enable_h2': {
                'type': bool,
                'message': 'H2 enable must be boolean'
            },
            'enable_h3': {
                'type': bool,
                'message': 'H3 enable must be boolean'
            },
            'simulation_speed': {
                'min': 0.1,
                'max': 10.0,
                'type': float,
                'message': 'Simulation speed must be between 0.1x and 10x'
            },
            'time_step': {
                'min': 0.01,
                'max': 0.5,
                'type': float,
                'message': 'Time step must be between 0.01 and 0.5 seconds'
            }
        }
        
        # Validate parameter
        if parameter not in validation_rules:
            return jsonify({
                'error': f'Unknown parameter: {parameter}'
            }), 400
        
        rule = validation_rules[parameter]
        
        # Type validation
        try:
            if rule['type'] == int:
                value = int(value)
            elif rule['type'] == float:
                value = float(value)
            elif rule['type'] == bool:
                value = bool(value)
        except (ValueError, TypeError):
            return jsonify({
                'error': f'Invalid type for {parameter}. Expected {rule["type"].__name__}'
            }), 400
        
        # Range validation
        if 'min' in rule and value < rule['min']:
            return jsonify({
                'error': f'{parameter} value {value} is below minimum {rule["min"]}'
            }), 400
        
        if 'max' in rule and value > rule['max']:
            return jsonify({
                'error': f'{parameter} value {value} is above maximum {rule["max"]}'
            }), 400
        
        # Get component manager
        component_manager = get_component_manager()
        
        # Update parameter based on type
        try:
            if parameter == 'floater_count':
                component_manager.update_floater_count(value)
            elif parameter == 'floater_mass':
                component_manager.update_floater_mass(value)
            elif parameter == 'chain_tension':
                component_manager.update_chain_tension(value)
            elif parameter == 'water_level':
                component_manager.update_water_level(value)
            elif parameter == 'h1_intensity':
                component_manager.update_h1_intensity(value / 100.0)  # Convert to 0-1 range
            elif parameter == 'h2_intensity':
                component_manager.update_h2_intensity(value / 100.0)  # Convert to 0-1 range
            elif parameter == 'h3_intensity':
                component_manager.update_h3_intensity(value / 100.0)  # Convert to 0-1 range
            elif parameter == 'enable_h1':
                component_manager.enable_h1(value)
            elif parameter == 'enable_h2':
                component_manager.enable_h2(value)
            elif parameter == 'enable_h3':
                component_manager.enable_h3(value)
            elif parameter == 'simulation_speed':
                component_manager.set_simulation_speed(value)
            elif parameter == 'time_step':
                component_manager.set_time_step(value)
            else:
                return jsonify({
                    'error': f'Unknown parameter: {parameter}'
                }), 400
            
            return jsonify({
                'success': True,
                'message': f'Updated {parameter} to {value}',
                'validated_value': value
            })
            
        except Exception as e:
            return jsonify({
                'error': f'Failed to update {parameter}: {str(e)}'
            }), 500
        
    except Exception as e:
        return jsonify({
            'error': f'Error updating parameter: {str(e)}'
        }), 500

@simulation_bp.route('/api/simulation/compressor', methods=['POST'])
def control_compressor():
    """Control compressor state"""
    try:
        data = request.get_json()
        if not data or 'action' not in data:
            return jsonify({
                'error': 'Missing action parameter'
            }), 400
        
        action = data['action']
        if action not in ['start', 'stop']:
            return jsonify({
                'error': 'Invalid action. Must be "start" or "stop"'
            }), 400
        
        # Get component manager
        component_manager = get_component_manager()
        
        # Control compressor
        if action == 'start':
            success = component_manager.start_compressor()
        else:
            success = component_manager.stop_compressor()
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Compressor {action}ed successfully'
            })
        else:
            return jsonify({
                'error': f'Failed to {action} compressor'
            }), 500
            
    except Exception as e:
        return jsonify({
            'error': f'Error controlling compressor: {str(e)}'
        }), 500

@simulation_bp.route('/api/simulation/diagnostics')
def get_system_diagnostics():
    """Get comprehensive system diagnostics"""
    try:
        import psutil
        import os
        
        # Get system metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Get process metrics
        process = psutil.Process(os.getpid())
        process_memory = process.memory_info()
        
        # Get component manager for simulation metrics
        component_manager = get_component_manager()
        state = component_manager.get_simulation_state()
        
        diagnostics = {
            'timestamp': datetime.now().isoformat(),
            'system_health': 'healthy',
            'warnings': [],
            'errors': [],
            
            'system_metrics': {
                'cpu_usage_percent': cpu_percent,
                'memory_usage_percent': memory.percent,
                'memory_available_gb': memory.available / (1024**3),
                'disk_usage_percent': disk.percent,
                'disk_free_gb': disk.free / (1024**3)
            },
            
            'process_metrics': {
                'process_memory_mb': process_memory.rss / (1024**2),
                'process_cpu_percent': process.cpu_percent(),
                'process_threads': process.num_threads(),
                'process_open_files': len(process.open_files()),
                'process_connections': len(process.connections())
            },
            
            'simulation_metrics': {
                'step_count': getattr(state, 'step_count', 0),
                'simulation_speed': getattr(state, 'simulation_speed', 1.0),
                'status': getattr(state, 'status', 'unknown'),
                'last_update_time': datetime.now().isoformat()
            },
            
            'component_status': {
                'physics_engine': 'active',
                'electrical_system': 'active',
                'mechanical_system': 'active',
                'pneumatic_system': 'active',
                'grid_services': 'active'
            }
        }
        
        # Check for system issues
        if cpu_percent > 80:
            diagnostics['warnings'].append('High CPU usage detected')
            diagnostics['system_health'] = 'warning'
        
        if memory.percent > 85:
            diagnostics['warnings'].append('High memory usage detected')
            diagnostics['system_health'] = 'warning'
        
        if disk.percent > 90:
            diagnostics['warnings'].append('Low disk space detected')
            diagnostics['system_health'] = 'warning'
        
        if process_memory.rss > 500 * 1024 * 1024:  # 500MB
            diagnostics['warnings'].append('High process memory usage')
            diagnostics['system_health'] = 'warning'
        
        return jsonify(diagnostics)
        
    except ImportError:
        return jsonify({
            'error': 'psutil not available for system diagnostics',
            'timestamp': datetime.now().isoformat(),
            'system_health': 'unknown'
        }), 500
    except Exception as e:
        return jsonify({
            'error': f'Error getting system diagnostics: {str(e)}',
            'timestamp': datetime.now().isoformat(),
            'system_health': 'error'
        }), 500

@simulation_bp.route('/api/simulation/logs')
def get_simulation_logs():
    """Get recent simulation logs"""
    try:
        # This would typically read from a log file
        # For now, return a sample log structure
        logs = [
            {
                'timestamp': datetime.now().isoformat(),
                'level': 'INFO',
                'message': 'Simulation started successfully',
                'component': 'simulation_engine'
            },
            {
                'timestamp': datetime.now().isoformat(),
                'level': 'INFO',
                'message': 'Physics engine initialized',
                'component': 'physics_engine'
            }
        ]
        
        return jsonify({
            'logs': logs,
            'total_count': len(logs)
        })
        
    except Exception as e:
        return jsonify({
            'error': f'Error getting simulation logs: {str(e)}'
        }), 500

@simulation_bp.route('/api/ping')
def ping():
    """Simple ping endpoint to test server connectivity"""
    return jsonify({'status': 'pong', 'timestamp': datetime.now().isoformat()})

@simulation_bp.route('/api/simulation/debug_state')
def debug_simulation_state():
    """Dump the full internal state of the component manager for debugging"""
    try:
        print("[DEBUG] debug_simulation_state: Starting")
        component_manager = get_component_manager()
        print(f"[DEBUG] debug_simulation_state: Got component manager: {component_manager}")
        
        state = {}
        
        # Test basic attributes first
        try:
            state['component_manager_type'] = str(type(component_manager))
            state['is_active'] = getattr(component_manager, 'is_active', 'NOT_FOUND')
            print(f"[DEBUG] debug_simulation_state: is_active = {state['is_active']}")
        except Exception as e:
            state['error_is_active'] = str(e)
            print(f"[DEBUG] debug_simulation_state: Error getting is_active: {e}")
        
        # Test simulation state
        try:
            sim_state = getattr(component_manager, '_simulation_state', None)
            if sim_state:
                state['simulation_state_keys'] = list(sim_state.keys()) if isinstance(sim_state, dict) else str(type(sim_state))
                state['simulation_status'] = sim_state.get('status', 'NOT_FOUND') if isinstance(sim_state, dict) else 'NOT_DICT'
            else:
                state['simulation_state'] = 'None'
            print(f"[DEBUG] debug_simulation_state: simulation_state = {state.get('simulation_state_keys', 'ERROR')}")
        except Exception as e:
            state['error_simulation_state'] = str(e)
            print(f"[DEBUG] debug_simulation_state: Error getting simulation_state: {e}")
        
        # Test thread status
        try:
            update_thread = getattr(component_manager, 'update_thread', None)
            if update_thread:
                state['update_thread_alive'] = update_thread.is_alive()
                state['update_thread_type'] = str(type(update_thread))
            else:
                state['update_thread'] = 'None'
            print(f"[DEBUG] debug_simulation_state: update_thread = {state.get('update_thread_alive', 'ERROR')}")
        except Exception as e:
            state['error_update_thread'] = str(e)
            print(f"[DEBUG] debug_simulation_state: Error getting update_thread: {e}")
        
        # Test components
        try:
            components = getattr(component_manager, 'components', {})
            state['components'] = list(components.keys()) if isinstance(components, dict) else str(type(components))
            print(f"[DEBUG] debug_simulation_state: components = {state['components']}")
        except Exception as e:
            state['error_components'] = str(e)
            print(f"[DEBUG] debug_simulation_state: Error getting components: {e}")
        
        print(f"[DEBUG] debug_simulation_state: Final state = {state}")
        return jsonify(state)
        
    except Exception as e:
        print(f"[DEBUG] debug_simulation_state: Main exception: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Error dumping debug state: {str(e)}'}), 500

@simulation_bp.route('/simulation')
def simulation_dashboard():
    """Render simulation dashboard"""
    return render_template('simulation.html')

