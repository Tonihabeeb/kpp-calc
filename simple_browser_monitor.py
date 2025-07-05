#!/usr/bin/env python3
"""
Simple Browser Monitor for KPP Simulator
Basic monitoring system that works reliably
"""

import json
import logging
import os
from datetime import datetime
from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimpleBrowserMonitor:
    def __init__(self, port=9104):
        self.port = port
        self.app = Flask(__name__)
        CORS(self.app)
        self.console_logs = []
        self.network_requests = []
        self.user_interactions = []
        self.errors = []
        self.is_collecting = True  # Start collecting by default
        self.setup_routes()
        
        # Create log directory
        os.makedirs("browser_logs", exist_ok=True)
        
    def setup_routes(self):
        @self.app.route('/')
        def index():
            return render_template_string("""
            <!DOCTYPE html>
            <html>
            <head>
                <title>KPP Browser Monitor</title>
                <style>
                    body { font-family: Arial, sans-serif; margin: 20px; }
                    .container { max-width: 1200px; margin: 0 auto; }
                    .section { margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }
                    .log-entry { margin: 5px 0; padding: 5px; background: #f5f5f5; border-radius: 3px; }
                    .error { background: #ffe6e6; border-left: 3px solid #ff0000; }
                    .warn { background: #fff3cd; border-left: 3px solid #ffc107; }
                    .log { background: #d1ecf1; border-left: 3px solid #17a2b8; }
                    button { margin: 5px; padding: 8px 15px; border: none; border-radius: 3px; cursor: pointer; }
                    .btn-primary { background: #007bff; color: white; }
                    .btn-success { background: #28a745; color: white; }
                    .btn-danger { background: #dc3545; color: white; }
                    .status { padding: 10px; margin: 10px 0; border-radius: 5px; }
                    .status.collecting { background: #d4edda; color: #155724; }
                    .status.stopped { background: #f8d7da; color: #721c24; }
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>KPP Browser Monitor</h1>
                    
                    <div class="section">
                        <h2>Controls</h2>
                        <div id="status" class="status collecting">🟢 Collection Active</div>
                        <button class="btn-success" onclick="startCollection()">Start Collection</button>
                        <button class="btn-danger" onclick="stopCollection()">Stop Collection</button>
                        <button class="btn-primary" onclick="clearLogs()">Clear Logs</button>
                        <button class="btn-primary" onclick="openKPPDashboard()">Open KPP Dashboard</button>
                        <button class="btn-primary" onclick="exportLogs()">Export Logs</button>
                    </div>
                    
                    <div class="section">
                        <h2>Console Logs <span id="console-count">(0)</span></h2>
                        <div id="console-logs"></div>
                    </div>
                    
                    <div class="section">
                        <h2>Network Requests <span id="network-count">(0)</span></h2>
                        <div id="network-requests"></div>
                    </div>
                    
                    <div class="section">
                        <h2>User Interactions <span id="interaction-count">(0)</span></h2>
                        <div id="user-interactions"></div>
                    </div>
                    
                    <div class="section">
                        <h2>Errors <span id="error-count">(0)</span></h2>
                        <div id="errors"></div>
                    </div>
                </div>
                
                <script>
                    function updateLogs() {
                        fetch('/api/logs/console')
                            .then(response => response.json())
                            .then(data => {
                                const container = document.getElementById('console-logs');
                                const count = document.getElementById('console-count');
                                count.textContent = '(' + data.logs.length + ')';
                                container.innerHTML = data.logs.map(log => 
                                    '<div class="log-entry ' + log.data.level + '">' + log.timestamp + ': ' + log.data.message + '</div>'
                                ).join('');
                            });
                            
                        fetch('/api/logs/network')
                            .then(response => response.json())
                            .then(data => {
                                const container = document.getElementById('network-requests');
                                const count = document.getElementById('network-count');
                                count.textContent = '(' + data.requests.length + ')';
                                container.innerHTML = data.requests.map(req => 
                                    '<div class="log-entry">' + req.timestamp + ': ' + req.data.method + ' ' + req.data.url + ' (' + req.data.status + ')</div>'
                                ).join('');
                            });
                            
                        fetch('/api/logs/interactions')
                            .then(response => response.json())
                            .then(data => {
                                const container = document.getElementById('user-interactions');
                                const count = document.getElementById('interaction-count');
                                count.textContent = '(' + data.interactions.length + ')';
                                container.innerHTML = data.interactions.map(interaction => 
                                    '<div class="log-entry">' + interaction.timestamp + ': ' + interaction.data.type + ' on ' + interaction.data.element + '</div>'
                                ).join('');
                            });
                            
                        fetch('/api/logs/errors')
                            .then(response => response.json())
                            .then(data => {
                                const container = document.getElementById('errors');
                                const count = document.getElementById('error-count');
                                count.textContent = '(' + data.errors.length + ')';
                                container.innerHTML = data.errors.map(error => 
                                    '<div class="log-entry error">' + error.timestamp + ': ' + error.data.message + '</div>'
                                ).join('');
                            });
                            
                        // Update status
                        fetch('/api/collection/status')
                            .then(response => response.json())
                            .then(data => {
                                const status = document.getElementById('status');
                                if (data.is_collecting) {
                                    status.className = 'status collecting';
                                    status.textContent = '🟢 Collection Active';
                                } else {
                                    status.className = 'status stopped';
                                    status.textContent = '🔴 Collection Stopped';
                                }
                            });
                    }
                    
                    function startCollection() {
                        fetch('/api/collection/start', {method: 'POST'})
                            .then(() => {
                                console.log('Collection started');
                                updateLogs();
                            });
                    }
                    
                    function stopCollection() {
                        fetch('/api/collection/stop', {method: 'POST'})
                            .then(() => {
                                console.log('Collection stopped');
                                updateLogs();
                            });
                    }
                    
                    function clearLogs() {
                        fetch('/api/logs/clear', {method: 'POST'})
                            .then(() => {
                                console.log('Logs cleared');
                                updateLogs();
                            });
                    }
                    
                    function openKPPDashboard() {
                        window.open('http://localhost:9103', '_blank');
                    }
                    
                    function exportLogs() {
                        fetch('/api/logs/export')
                            .then(response => response.blob())
                            .then(blob => {
                                const url = window.URL.createObjectURL(blob);
                                const a = document.createElement('a');
                                a.href = url;
                                a.download = 'kpp_browser_logs_' + new Date().toISOString().slice(0,19).replace(/:/g,'-') + '.json';
                                a.click();
                            });
                    }
                    
                    // Update logs every 2 seconds
                    setInterval(updateLogs, 2000);
                    updateLogs();
                </script>
            </body>
            </html>
            """)
        
        @self.app.route('/api/events', methods=['POST'])
        def receive_event():
            if not self.is_collecting:
                return jsonify({'status': 'ignored', 'message': 'Collection stopped'})
                
            try:
                event = request.json
                event_type = event.get('type')
                data = event.get('data', {})
                timestamp = event.get('timestamp', datetime.now().isoformat())
                
                log_entry = {
                    'timestamp': timestamp,
                    'data': data
                }
                
                if event_type == 'console':
                    self.console_logs.append(log_entry)
                    logger.info(f"Console: {data.get('message', '')}")
                elif event_type == 'network':
                    self.network_requests.append(log_entry)
                    logger.info(f"Network: {data.get('method', '')} {data.get('url', '')}")
                elif event_type == 'interaction':
                    self.user_interactions.append(log_entry)
                    logger.info(f"Interaction: {data.get('type', '')} on {data.get('element', '')}")
                elif event_type == 'error':
                    self.errors.append(log_entry)
                    logger.error(f"Error: {data.get('message', '')}")
                
                # Keep only last 1000 entries
                if len(self.console_logs) > 1000:
                    self.console_logs = self.console_logs[-1000:]
                if len(self.network_requests) > 1000:
                    self.network_requests = self.network_requests[-1000:]
                if len(self.user_interactions) > 1000:
                    self.user_interactions = self.user_interactions[-1000:]
                if len(self.errors) > 500:
                    self.errors = self.errors[-500:]
                
                return jsonify({'status': 'success'})
                
            except Exception as e:
                logger.error(f"Error processing event: {e}")
                return jsonify({'status': 'error', 'message': str(e)}), 500
        
        @self.app.route('/api/collection/start', methods=['POST'])
        def start_collection():
            self.is_collecting = True
            logger.info("Browser event collection started")
            return jsonify({'status': 'success', 'message': 'Collection started'})
            
        @self.app.route('/api/collection/stop', methods=['POST'])
        def stop_collection():
            self.is_collecting = False
            logger.info("Browser event collection stopped")
            return jsonify({'status': 'success', 'message': 'Collection stopped'})
            
        @self.app.route('/api/collection/status')
        def get_collection_status():
            return jsonify({'is_collecting': self.is_collecting})
            
        @self.app.route('/api/logs/console')
        def get_console_logs():
            return jsonify({'logs': self.console_logs[-100:]})
            
        @self.app.route('/api/logs/network')
        def get_network_logs():
            return jsonify({'requests': self.network_requests[-100:]})
            
        @self.app.route('/api/logs/interactions')
        def get_interaction_logs():
            return jsonify({'interactions': self.user_interactions[-100:]})
            
        @self.app.route('/api/logs/errors')
        def get_error_logs():
            return jsonify({'errors': self.errors[-50:]})
            
        @self.app.route('/api/logs/clear', methods=['POST'])
        def clear_logs():
            self.console_logs.clear()
            self.network_requests.clear()
            self.user_interactions.clear()
            self.errors.clear()
            return jsonify({'status': 'success', 'message': 'Logs cleared'})
            
        @self.app.route('/api/logs/export')
        def export_logs():
            export_data = {
                'export_timestamp': datetime.now().isoformat(),
                'console_logs': self.console_logs,
                'network_requests': self.network_requests,
                'user_interactions': self.user_interactions,
                'errors': self.errors
            }
            
            # Save to file
            filename = f"browser_logs/kpp_browser_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, 'w') as f:
                json.dump(export_data, f, indent=2)
            
            return jsonify(export_data)
    
    def get_monitoring_script(self):
        return """
        // Simple KPP Browser Monitoring Script
        (function() {
            'use strict';
            
            const MONITORING_ENDPOINT = 'http://localhost:9104';
            let isMonitoring = false;
            
            // Console monitoring
            const originalConsole = {
                log: console.log,
                warn: console.warn,
                error: console.error,
                info: console.info
            };
            
            function sendEvent(type, data) {
                if (!isMonitoring) return;
                
                const event = {
                    type: type,
                    data: data,
                    timestamp: new Date().toISOString(),
                    url: window.location.href
                };
                
                fetch(MONITORING_ENDPOINT + '/api/events', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(event)
                }).catch(err => {
                    // Silently fail to avoid console spam
                });
            }
            
            // Override console methods
            console.log = function(...args) {
                originalConsole.log.apply(console, args);
                sendEvent('console', { level: 'log', message: args.join(' ') });
            };
            
            console.warn = function(...args) {
                originalConsole.warn.apply(console, args);
                sendEvent('console', { level: 'warn', message: args.join(' ') });
            };
            
            console.error = function(...args) {
                originalConsole.error.apply(console, args);
                sendEvent('console', { level: 'error', message: args.join(' ') });
                sendEvent('error', { message: args.join(' ') });
            };
            
            console.info = function(...args) {
                originalConsole.info.apply(console, args);
                sendEvent('console', { level: 'info', message: args.join(' ') });
            };
            
            // Network monitoring
            const originalFetch = window.fetch;
            window.fetch = function(...args) {
                const url = args[0];
                const options = args[1] || {};
                
                return originalFetch.apply(this, args)
                    .then(response => {
                        sendEvent('network', {
                            method: options.method || 'GET',
                            url: url,
                            status: response.status
                        });
                        return response;
                    })
                    .catch(error => {
                        sendEvent('network', {
                            method: options.method || 'GET',
                            url: url,
                            status: 'error',
                            error: error.message
                        });
                        throw error;
                    });
            };
            
            // User interaction monitoring
            ['click', 'input', 'change', 'submit'].forEach(eventType => {
                document.addEventListener(eventType, function(event) {
                    const target = event.target;
                    sendEvent('interaction', {
                        type: eventType,
                        element: target.tagName + (target.id ? '#' + target.id : '') + (target.className ? '.' + target.className.split(' ')[0] : ''),
                        value: target.value || null
                    });
                }, true);
            });
            
            // Error monitoring
            window.addEventListener('error', function(event) {
                sendEvent('error', {
                    message: event.message,
                    filename: event.filename,
                    lineno: event.lineno
                });
            });
            
            // Start monitoring
            function startMonitoring() {
                isMonitoring = true;
                console.log('KPP Browser monitoring started');
                sendEvent('console', { level: 'info', message: 'KPP Browser monitoring initialized' });
            }
            
            // Auto-start monitoring
            if (document.readyState === 'loading') {
                document.addEventListener('DOMContentLoaded', startMonitoring);
            } else {
                startMonitoring();
            }
            
        })();
        """
    
    def start(self):
        logger.info(f"Starting Simple Browser Monitor on port {self.port}")
        self.app.run(host='0.0.0.0', port=self.port, debug=False, threaded=True)

def init_simple_browser_monitor(port=9104):
    return SimpleBrowserMonitor(port)

if __name__ == "__main__":
    monitor = SimpleBrowserMonitor()
    print("Simple KPP Browser Monitor")
    print("=" * 30)
    print(f"Dashboard: http://localhost:{monitor.port}")
    print("Starting service...")
    monitor.start() 