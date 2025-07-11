"""
KPP Simulator Flask Application
"""

from flask import Flask, render_template, redirect, url_for, send_from_directory, jsonify
from kpp_simulator.managers.component_manager import ComponentManager
from routes.loss_monitoring_api import loss_monitoring_bp
from routes.simulation_api import simulation_bp
import os
import time
from datetime import datetime

class FlaskComponentManager:
    """Flask extension for component manager"""
    
    def __init__(self, app=None):
        self.component_manager = None
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize the component manager with the Flask application"""
        self.component_manager = ComponentManager()
        
        # Store extension
        app.extensions['component_manager'] = self.component_manager
        
        # Initialize components in proper order (dependencies first)
        with app.app_context():
            # Initialize simulation first (creates physics engine and simulation engine)
            self.component_manager.initialize_simulation()
            
            # Initialize drivetrain system (depends on physics engine)
            self.component_manager.initialize_drivetrain_system()
            
            # Initialize electrical system (depends on physics engine)
            self.component_manager.initialize_electrical_system()
            
            # Initialize loss tracking last (depends on drivetrain and electrical systems)
            self.component_manager.initialize_loss_tracking()
            
        # Start the component manager
        # self.component_manager.start()  # <-- Only start when user triggers via API

def create_app(config=None):
    """Create Flask application"""
    app = Flask(__name__)
    
    # Load configuration
    if config:
        app.config.update(config)
    
    # Initialize component manager extension
    component_manager = FlaskComponentManager()
    component_manager.init_app(app)
    
    # Register blueprints
    app.register_blueprint(loss_monitoring_bp)
    app.register_blueprint(simulation_bp)
    
    # Root route - redirect to simulation dashboard
    @app.route('/')
    def index():
        """Redirect to main simulation dashboard"""
        return redirect(url_for('simulation'))
    
    # Favicon route to prevent 404 errors
    @app.route('/favicon.ico')
    def favicon():
        """Serve favicon or return empty response"""
        try:
            return send_from_directory(os.path.join(app.root_path, 'static'),
                                     'favicon.ico', mimetype='image/vnd.microsoft.icon')
        except:
            # Return empty response if favicon doesn't exist
            return '', 204
    
    # Add dashboard route
    @app.route('/dashboard')
    def dashboard():
        """Render loss monitoring dashboard"""
        return render_template('loss_monitoring.html')
    
    # Add simulation route
    @app.route('/simulation')
    def simulation():
        """Render simulation dashboard"""
        return render_template('simulation.html')
    
    # Add performance monitoring route
    @app.route('/performance')
    def performance():
        """Render performance monitoring dashboard"""
        return render_template('performance_monitoring.html')
    
    # Performance monitoring endpoints
    @app.route('/api/performance')
    def get_performance():
        """Get detailed system performance metrics"""
        try:
            # Get basic system metrics
            import psutil
            cpu_percent = psutil.cpu_percent()
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Get detailed performance monitoring data
            try:
                from simulation.monitoring.performance_monitor import get_performance_monitor
                performance_monitor = get_performance_monitor()
                performance_summary = performance_monitor.get_performance_summary()
            except Exception as e:
                performance_summary = {'status': 'error', 'message': str(e)}
            
            return jsonify({
                'system_metrics': {
                    'cpu_percent': cpu_percent,
                    'memory_percent': memory.percent,
                    'memory_available_gb': memory.available / (1024**3),
                    'disk_percent': disk.percent,
                    'disk_free_gb': disk.free / (1024**3),
                },
                'simulation_performance': performance_summary,
                'timestamp': time.time()
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/performance/export')
    def export_performance_data():
        """Export performance data to JSON file"""
        try:
            from simulation.monitoring.performance_monitor import get_performance_monitor
            performance_monitor = get_performance_monitor()
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"performance_export_{timestamp}.json"
            filepath = os.path.join('logs', 'performance', filename)
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            performance_monitor.export_performance_data(filepath)
            
            return jsonify({
                'status': 'success',
                'message': f'Performance data exported to {filename}',
                'filepath': filepath
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/performance/clear')
    def clear_performance_data():
        """Clear performance monitoring history"""
        try:
            from simulation.monitoring.performance_monitor import get_performance_monitor
            performance_monitor = get_performance_monitor()
            performance_monitor.clear_history()
            
            return jsonify({
                'status': 'success',
                'message': 'Performance history cleared'
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/status')
    def status():
        """API status endpoint for health checks"""
        try:
            return jsonify({
                'status': 'running',
                'service': 'KPP Simulator Backend API',
                'timestamp': time.time(),
                'version': '1.0.0'
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    return app

if __name__ == '__main__':
    app = create_app()
    
    # Hardened Flask server startup for Windows
    try:
        app.run(
            debug=True,
            threaded=True,
            host='127.0.0.1',
            port=9100,
            use_reloader=False  # Always disable reloader to prevent socket issues
        )
    except Exception as e:
        print(f"[CRITICAL] Failed to start Flask server: {e}")
        import traceback
        traceback.print_exc()
        print("[CRITICAL] Try running with a production WSGI server if issues persist.")
