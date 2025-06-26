# KPP Frontend Patch Implementation Plan

## Overview
This document outlines a staged implementation plan for the KPP Simulator Frontend Patch, focusing on real-time data streaming, enhanced physics modeling, and improved user interface controls.

## Implementation Timeline: 5 Stages (2-3 weeks total)

---

## **Stage 1: Backend API Foundation** (3-4 days)
*Priority: Critical - Foundation for all frontend work*

### Objectives
- Establish robust backend API endpoints
- Implement parameter validation and management
- Set up Server-Sent Events (SSE) streaming infrastructure

### Tasks

#### 1.1 Parameter Schema & Validation (Day 1)
```python
# File: config/parameter_schema.py (NEW)
PARAM_SCHEMA = {
    'air_pressure': {'type': float, 'min': 0.1, 'max': 10.0, 'default': 1.0},
    'nanobubble_frac': {'type': float, 'min': 0.0, 'max': 1.0, 'default': 0.0},
    'thermal_coeff': {'type': float, 'min': 0.0, 'max': 1.0, 'default': 0.0},
    'pulse_enabled': {'type': bool, 'default': False},
    'num_floaters': {'type': int, 'min': 1, 'max': 20, 'default': 4},
    # ... additional parameters
}
```

#### 1.2 Enhanced Flask Routes (Day 2)
```python
# File: routes/api_routes.py (NEW or MODIFY app.py)
@app.route('/set_params', methods=['PATCH'])
def set_params():
    # Implement robust parameter validation
    # Update simulation instance
    # Return structured responses
    
@app.route('/get_output_schema', methods=['GET'])
def get_output_schema():
    # Return API documentation
    
@app.route('/stream')
def stream():
    # Enhanced SSE with comprehensive data
```

#### 1.3 Simulation Engine Updates (Day 3-4)
```python
# File: simulation/engine.py (MODIFY)
class SimulationEngine:
    def get_output_data(self) -> Dict[str, Any]:
        # Comprehensive data structure for SSE
        return {
            "time": self.time,
            "torque": self.torque_total,
            "power": self.power_output,
            "efficiency": self.efficiency,
            "torque_components": {
                "buoyant": self.torque_buoyant,
                "drag": self.torque_drag,
                "generator": self.torque_generator
            },
            "floaters": [
                {
                    "buoyancy": f.buoyancy,
                    "drag": f.drag,
                    "net_force": f.net_force,
                    "pulse_force": f.pulse_force
                } for f in self.floaters
            ],
            "eff_drivetrain": self.eff_drivetrain,
            "eff_pneumatic": self.eff_pneumatic
        }
```

### Deliverables
- ✅ Validated parameter schema system
- ✅ Robust `/set_params` endpoint with validation
- ✅ Enhanced `/stream` endpoint with comprehensive data
- ✅ `/get_output_schema` documentation endpoint
- ✅ Updated simulation engine output methods

### Testing
- API endpoint testing with Postman/curl
- Parameter validation edge cases
- SSE stream continuity testing

---

## **Stage 2: Enhanced Physics Implementation** (4-5 days)
*Priority: High - Core simulation improvements*

### Objectives
- Implement H1, H2, H3 hypothesis effects
- Add realistic drag modeling and physical constraints
- Integrate compressor and pneumatic system logic

### Tasks

#### 2.1 H1 Nanobubble Physics (Day 1)
```python
# File: simulation/physics/nanobubble_effects.py (NEW)
class NanobubblePhysics:
    def apply_density_reduction(self, base_density: float, nanobubble_frac: float) -> float:
        return base_density * (1 - nanobubble_frac)
    
    def apply_drag_reduction(self, base_cd: float, nanobubble_frac: float) -> float:
        drag_reduction_factor = 0.5  # 50% max reduction
        return base_cd * (1 - drag_reduction_factor * nanobubble_frac)
```

#### 2.2 H2 Thermal Boost Implementation (Day 2)
```python
# File: simulation/physics/thermal_effects.py (NEW)
class ThermalBoost:
    def calculate_enhanced_buoyancy(self, base_buoyancy: float, thermal_coeff: float) -> float:
        return base_buoyancy * (1 + thermal_coeff)
```

#### 2.3 H3 Pulse Mode & Clutch Logic (Day 2-3)
```python
# File: simulation/control/pulse_control.py (NEW)
class PulseController:
    def __init__(self, pulse_on_duration: float = 5.0, pulse_off_duration: float = 5.0):
        self.pulse_on_duration = pulse_on_duration
        self.pulse_off_duration = pulse_off_duration
        self.clutch_engaged = True
        
    def update_clutch_state(self, simulation_time: float) -> bool:
        # Implement pulse timing logic
        pass
```

#### 2.4 Realistic Drag & Force Modeling (Day 3-4)
```python
# File: simulation/physics/fluid_dynamics.py (MODIFY)
def calculate_drag_force(velocity: float, area: float, cd: float, fluid_density: float) -> float:
    """Standard drag equation: F = 0.5 * ρ * Cd * A * v²"""
    return 0.5 * fluid_density * cd * area * (velocity ** 2) * np.sign(velocity)
```

#### 2.5 Compressor & Air Tank Logic (Day 4-5)
```python
# File: simulation/pneumatics/compressor_system.py (NEW)
class CompressorSystem:
    def __init__(self, tank_capacity: float, compressor_rate: float):
        self.air_tank_pressure = 0.0
        self.tank_capacity = tank_capacity
        self.compressor_rate = compressor_rate
        
    def can_inject_air(self, required_pressure: float) -> bool:
        return self.air_tank_pressure >= required_pressure
        
    def inject_air(self, volume: float) -> bool:
        # Implement air injection logic with pressure reduction
        pass
        
    def update_compressor(self, dt: float):
        # Simulate compressor adding pressure over time
        pass
```

### Deliverables
- ✅ H1 nanobubble effects implementation
- ✅ H2 thermal boost mechanics
- ✅ H3 pulse mode and clutch control
- ✅ Realistic drag force calculations
- ✅ Compressor and air tank simulation
- ✅ Physical constraint enforcement

### Testing
- Physics validation with extreme parameter values
- Energy conservation checks
- Pulse mode timing verification

---

## **Stage 3: Frontend UI Enhancement** (3-4 days)
*Priority: High - User interface improvements*

### Objectives
- Update HTML template with new controls
- Implement unified parameter management
- Add real-time data visualization components

### Tasks

#### 3.1 HTML Template Updates (Day 1)
```html
<!-- File: templates/index.html (MODIFY) -->
<div class="controls-section">
    <h3>Hypothesis Controls</h3>
    
    <!-- H1 Nanobubble Controls -->
    <div class="control-group">
        <label for="nanobubble_frac">Nanobubble Fraction (H1):</label>
        <input type="range" id="nanobubble_frac" name="nanobubble_frac" 
               min="0" max="1" step="0.01" value="0">
        <span id="nanobubble_frac_val">0%</span>
    </div>
    
    <!-- H2 Thermal Controls -->
    <div class="control-group">
        <label for="thermal_coeff">Thermal Coefficient (H2):</label>
        <input type="range" id="thermal_coeff" name="thermal_coeff" 
               min="0" max="1" step="0.01" value="0">
        <span id="thermal_coeff_val">0%</span>
    </div>
    
    <!-- H3 Pulse Mode -->
    <div class="control-group">
        <label for="pulse_enabled">Pulse Mode (H3):</label>
        <input type="checkbox" id="pulse_enabled" name="pulse_enabled">
        <span>Enable Pulse & Coast</span>
    </div>
</div>

<!-- Enhanced Floater Table -->
<table id="floaterTable" class="data-table">
    <thead>
        <tr>
            <th>Floater #</th>
            <th>Buoyancy (N)</th>
            <th>Drag (N)</th>
            <th>Net Force (N)</th>
            <th>Pulse Force (N)</th>
        </tr>
    </thead>
    <tbody id="floaterTableBody">
        <!-- Dynamically populated -->
    </tbody>
</table>
```

#### 3.2 JavaScript Event Management (Day 2)
```javascript
// File: static/js/main.js (MODIFY)
class ParameterManager {
    constructor() {
        this.initializeEventHandlers();
    }
    
    initializeEventHandlers() {
        // Unified parameter update system
        const controls = ['air_pressure', 'nanobubble_frac', 'thermal_coeff', 'pulse_enabled'];
        controls.forEach(controlId => {
            const element = document.getElementById(controlId);
            if (element) {
                element.addEventListener('input', (e) => this.updateParam(controlId, e.target.value));
            }
        });
    }
    
    async updateParam(paramName, value) {
        const data = {};
        data[paramName] = paramName === 'pulse_enabled' ? value === 'on' : parseFloat(value);
        
        try {
            const response = await fetch('/set_params', {
                method: 'PATCH',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(data)
            });
            
            if (!response.ok) {
                console.error('Parameter update failed:', response.status);
            }
        } catch (error) {
            console.error('Network error:', error);
        }
    }
}
```

#### 3.3 Enhanced Data Visualization (Day 3)
```javascript
// File: static/js/charts.js (NEW)
class ChartManager {
    constructor() {
        this.initializeCharts();
        this.maxDataPoints = 100; // Keep last 100 points
    }
    
    initializeCharts() {
        // Torque Components Chart
        this.torqueChart = new Chart(document.getElementById('torqueChart'), {
            type: 'line',
            data: {
                labels: [],
                datasets: [
                    {
                        label: 'Total Torque',
                        data: [],
                        borderColor: 'rgb(75, 192, 192)',
                        tension: 0.1
                    },
                    {
                        label: 'Buoyant Torque',
                        data: [],
                        borderColor: 'rgb(54, 162, 235)',
                        tension: 0.1
                    },
                    {
                        label: 'Drag Torque',
                        data: [],
                        borderColor: 'rgb(255, 99, 132)',
                        tension: 0.1
                    }
                ]
            },
            options: {
                responsive: true,
                scales: {
                    x: { display: true, title: { display: true, text: 'Time (s)' }},
                    y: { display: true, title: { display: true, text: 'Torque (N⋅m)' }}
                }
            }
        });
        
        // Efficiency Chart
        this.efficiencyChart = new Chart(document.getElementById('efficiencyChart'), {
            type: 'line',
            data: {
                labels: [],
                datasets: [
                    {
                        label: 'Overall Efficiency',
                        data: [],
                        borderColor: 'rgb(153, 102, 255)',
                        tension: 0.1
                    },
                    {
                        label: 'Drivetrain Efficiency',
                        data: [],
                        borderColor: 'rgb(255, 159, 64)',
                        tension: 0.1
                    },
                    {
                        label: 'Pneumatic Efficiency',
                        data: [],
                        borderColor: 'rgb(75, 192, 192)',
                        tension: 0.1
                    }
                ]
            }
        });
    }
    
    updateCharts(data) {
        this.addDataPoint(this.torqueChart, data.time, [
            data.torque, 
            data.torque_components.buoyant, 
            data.torque_components.drag
        ]);
        
        this.addDataPoint(this.efficiencyChart, data.time, [
            data.efficiency,
            data.eff_drivetrain,
            data.eff_pneumatic
        ]);
    }
    
    addDataPoint(chart, time, values) {
        chart.data.labels.push(time.toFixed(1));
        values.forEach((value, index) => {
            chart.data.datasets[index].data.push(value);
        });
        
        // Trim old data
        if (chart.data.labels.length > this.maxDataPoints) {
            chart.data.labels.shift();
            chart.data.datasets.forEach(dataset => dataset.data.shift());
        }
        
        chart.update('none'); // No animation for real-time
    }
}
```

#### 3.4 Floater Table Management (Day 4)
```javascript
// File: static/js/floater-table.js (NEW)
class FloaterTableManager {
    constructor() {
        this.tableBody = document.getElementById('floaterTableBody');
    }
    
    updateTable(floatersData) {
        // Clear existing rows
        this.tableBody.innerHTML = '';
        
        // Add new rows
        floatersData.forEach((floater, index) => {
            const row = this.tableBody.insertRow();
            row.innerHTML = `
                <td>${index + 1}</td>
                <td>${floater.buoyancy.toFixed(2)}</td>
                <td>${floater.drag.toFixed(2)}</td>
                <td>${floater.net_force.toFixed(2)}</td>
                <td>${floater.pulse_force.toFixed(2)}</td>
            `;
        });
    }
}
```

### Deliverables
- ✅ Updated HTML template with new controls
- ✅ Unified parameter management system
- ✅ Enhanced Chart.js visualizations
- ✅ Real-time floater data table
- ✅ Responsive UI design

### Testing
- UI responsiveness across different screen sizes
- Parameter control functionality
- Chart performance with continuous data
- Table update efficiency

---

## **Stage 4: Real-Time Data Integration** (2-3 days)
*Priority: High - SSE integration and data flow*

### Objectives
- Implement Server-Sent Events client-side
- Integrate real-time data with UI components
- Add connection status and error handling

### Tasks

#### 4.1 SSE Client Implementation (Day 1)
```javascript
// File: static/js/sse-client.js (NEW)
class SSEClient {
    constructor() {
        this.eventSource = null;
        this.isConnected = false;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.chartManager = new ChartManager();
        this.floaterTable = new FloaterTableManager();
        this.statusIndicator = document.getElementById('connectionStatus');
    }
    
    connect() {
        if (this.eventSource) {
            this.eventSource.close();
        }
        
        this.eventSource = new EventSource('/stream');
        
        this.eventSource.onopen = (event) => {
            console.log('SSE connected');
            this.isConnected = true;
            this.reconnectAttempts = 0;
            this.updateConnectionStatus('Connected', 'success');
        };
        
        this.eventSource.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                this.handleDataUpdate(data);
            } catch (error) {
                console.error('Error parsing SSE data:', error);
            }
        };
        
        this.eventSource.onerror = (event) => {
            console.error('SSE error:', event);
            this.isConnected = false;
            this.updateConnectionStatus('Disconnected', 'error');
            this.attemptReconnect();
        };
    }
    
    handleDataUpdate(data) {
        // Update charts
        this.chartManager.updateCharts(data);
        
        // Update floater table
        this.floaterTable.updateTable(data.floaters);
        
        // Update numerical displays
        this.updateNumericDisplays(data);
        
        // Update system status
        this.updateSystemStatus(data);
    }
    
    updateNumericDisplays(data) {
        const displays = {
            'current-power': data.power.toFixed(1) + ' W',
            'current-torque': data.torque.toFixed(2) + ' N⋅m',
            'current-efficiency': data.efficiency.toFixed(1) + '%',
            'simulation-time': data.time.toFixed(1) + ' s'
        };
        
        Object.entries(displays).forEach(([id, value]) => {
            const element = document.getElementById(id);
            if (element) element.textContent = value;
        });
    }
    
    updateConnectionStatus(status, type) {
        if (this.statusIndicator) {
            this.statusIndicator.textContent = status;
            this.statusIndicator.className = `status-${type}`;
        }
    }
    
    attemptReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
            setTimeout(() => this.connect(), 2000 * this.reconnectAttempts);
        }
    }
}
```

#### 4.2 Data Flow Integration (Day 2)
```javascript
// File: static/js/app.js (NEW - Main Application)
class KPPSimulatorApp {
    constructor() {
        this.parameterManager = new ParameterManager();
        this.sseClient = new SSEClient();
        this.initialize();
    }
    
    initialize() {
        // Initialize components
        this.setupEventListeners();
        
        // Start SSE connection
        this.sseClient.connect();
        
        // Initialize UI state
        this.loadInitialParameters();
    }
    
    setupEventListeners() {
        // Download buttons
        document.getElementById('downloadCSV')?.addEventListener('click', () => {
            window.open('/download_csv', '_blank');
        });
        
        document.getElementById('downloadJSON')?.addEventListener('click', () => {
            window.open('/download_json', '_blank');
        });
        
        // Schema documentation
        document.getElementById('viewSchema')?.addEventListener('click', async () => {
            try {
                const response = await fetch('/get_output_schema');
                const schema = await response.json();
                this.displaySchema(schema);
            } catch (error) {
                console.error('Error fetching schema:', error);
            }
        });
    }
    
    async loadInitialParameters() {
        // Load default parameters from schema
        try {
            const response = await fetch('/get_output_schema');
            const schema = await response.json();
            // Set initial UI values based on defaults
        } catch (error) {
            console.error('Error loading initial parameters:', error);
        }
    }
    
    displaySchema(schema) {
        // Display schema in a modal or dedicated section
        const schemaDisplay = document.getElementById('schemaDisplay');
        if (schemaDisplay) {
            schemaDisplay.innerHTML = `<pre>${JSON.stringify(schema, null, 2)}</pre>`;
        }
    }
}

// Initialize application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.kppApp = new KPPSimulatorApp();
});
```

#### 4.3 Error Handling & Resilience (Day 3)
```javascript
// File: static/js/error-handler.js (NEW)
class ErrorHandler {
    constructor() {
        this.errorLog = [];
        this.maxLogEntries = 50;
        this.setupGlobalErrorHandling();
    }
    
    setupGlobalErrorHandling() {
        window.addEventListener('error', (event) => {
            this.logError('JavaScript Error', event.error);
        });
        
        window.addEventListener('unhandledrejection', (event) => {
            this.logError('Unhandled Promise Rejection', event.reason);
        });
    }
    
    logError(type, error) {
        const errorEntry = {
            timestamp: new Date().toISOString(),
            type: type,
            message: error.message || error.toString(),
            stack: error.stack
        };
        
        this.errorLog.push(errorEntry);
        
        // Trim log if too large
        if (this.errorLog.length > this.maxLogEntries) {
            this.errorLog.shift();
        }
        
        console.error(type + ':', error);
        this.displayErrorNotification(errorEntry);
    }
    
    displayErrorNotification(error) {
        // Create temporary error notification
        const notification = document.createElement('div');
        notification.className = 'error-notification';
        notification.innerHTML = `
            <div class="error-content">
                <strong>Error:</strong> ${error.message}
                <button onclick="this.parentElement.parentElement.remove()">×</button>
            </div>
        `;
        
        document.body.appendChild(notification);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (notification.parentElement) {
                notification.remove();
            }
        }, 5000);
    }
    
    getErrorLog() {
        return this.errorLog;
    }
}
```

### Deliverables
- ✅ Robust SSE client implementation
- ✅ Real-time data integration with UI
- ✅ Connection status monitoring
- ✅ Error handling and recovery
- ✅ Data export functionality

### Testing
- SSE connection stability
- Data synchronization accuracy
- Error recovery mechanisms
- Network interruption handling

---

## **Stage 5: Logging & Analytics Enhancement** (2-3 days)
*Priority: Medium - Data export and analysis tools*

### Objectives
- Implement comprehensive data logging
- Add CSV/JSON export functionality
- Create analytics and debugging tools

### Tasks

#### 5.1 Backend Logging System (Day 1)
```python
# File: simulation/logging/data_logger.py (NEW)
class SimulationDataLogger:
    def __init__(self, max_entries: int = 10000):
        self.log_entries = []
        self.max_entries = max_entries
        self.start_time = time.time()
        
    def log_simulation_state(self, sim_engine):
        """Log complete simulation state"""
        entry = {
            "timestamp": time.time() - self.start_time,
            "time": sim_engine.time,
            "torque": sim_engine.torque_total,
            "power": sim_engine.power_output,
            "efficiency": sim_engine.efficiency,
            "torque_components": {
                "buoyant": getattr(sim_engine, 'torque_buoyant', 0),
                "drag": getattr(sim_engine, 'torque_drag', 0),
                "generator": getattr(sim_engine, 'torque_generator', 0)
            },
            "system_state": {
                "clutch_engaged": getattr(sim_engine, 'clutch_engaged', True),
                "air_tank_pressure": getattr(sim_engine, 'air_tank_pressure', 0),
                "compressor_active": getattr(sim_engine, 'compressor_active', False)
            },
            "floaters": [
                {
                    "id": i,
                    "buoyancy": f.buoyancy,
                    "drag": f.drag,
                    "net_force": f.net_force,
                    "pulse_force": f.pulse_force,
                    "position": getattr(f, 'position', 0),
                    "velocity": getattr(f, 'velocity', 0),
                    "state": getattr(f, 'state', 'unknown')
                } for i, f in enumerate(sim_engine.floaters)
            ],
            "parameters": {
                "nanobubble_frac": getattr(sim_engine, 'nanobubble_frac', 0),
                "thermal_coeff": getattr(sim_engine, 'thermal_coeff', 0),
                "pulse_enabled": getattr(sim_engine, 'pulse_enabled', False)
            }
        }
        
        self.log_entries.append(entry)
        
        # Trim log if too large
        if len(self.log_entries) > self.max_entries:
            self.log_entries.pop(0)
            
    def get_csv_data(self) -> str:
        """Generate CSV representation of logged data"""
        if not self.log_entries:
            return "No data logged"
            
        # Generate dynamic header based on floater count
        sample_entry = self.log_entries[0]
        num_floaters = len(sample_entry['floaters'])
        
        header = [
            "timestamp", "sim_time", "torque", "power", "efficiency",
            "torque_buoyant", "torque_drag", "torque_generator",
            "clutch_engaged", "air_tank_pressure"
        ]
        
        # Add floater columns
        for i in range(num_floaters):
            header.extend([
                f"f{i+1}_buoyancy", f"f{i+1}_drag", 
                f"f{i+1}_net_force", f"f{i+1}_pulse_force"
            ])
            
        # Generate CSV content
        csv_lines = [",".join(header)]
        
        for entry in self.log_entries:
            row = [
                f"{entry['timestamp']:.3f}",
                f"{entry['time']:.3f}",
                f"{entry['torque']:.6f}",
                f"{entry['power']:.6f}",
                f"{entry['efficiency']:.6f}",
                f"{entry['torque_components']['buoyant']:.6f}",
                f"{entry['torque_components']['drag']:.6f}",
                f"{entry['torque_components']['generator']:.6f}",
                str(entry['system_state']['clutch_engaged']),
                f"{entry['system_state']['air_tank_pressure']:.3f}"
            ]
            
            # Add floater data
            for floater in entry['floaters']:
                row.extend([
                    f"{floater['buoyancy']:.6f}",
                    f"{floater['drag']:.6f}",
                    f"{floater['net_force']:.6f}",
                    f"{floater['pulse_force']:.6f}"
                ])
                
            csv_lines.append(",".join(row))
            
        return "\n".join(csv_lines)
```

#### 5.2 Enhanced Export Routes (Day 2)
```python
# File: routes/export_routes.py (NEW)
from flask import Response, jsonify, request
import json

@app.route('/download_csv')
def download_csv():
    """Stream CSV data for download"""
    def generate_csv():
        csv_data = simulation_logger.get_csv_data()
        yield csv_data
        
    response = Response(generate_csv(), mimetype='text/csv')
    response.headers['Content-Disposition'] = 'attachment; filename="kpp_simulation_data.csv"'
    return response

@app.route('/download_json')
def download_json():
    """Download complete simulation log as JSON"""
    return jsonify({
        "metadata": {
            "export_time": time.time(),
            "total_entries": len(simulation_logger.log_entries),
            "simulation_duration": simulation_logger.log_entries[-1]['time'] if simulation_logger.log_entries else 0
        },
        "data": simulation_logger.log_entries
    })

@app.route('/analytics/summary')
def get_analytics_summary():
    """Provide analytics summary of current simulation"""
    if not simulation_logger.log_entries:
        return jsonify({"error": "No data available"})
        
    entries = simulation_logger.log_entries
    
    # Calculate statistics
    powers = [e['power'] for e in entries]
    efficiencies = [e['efficiency'] for e in entries]
    torques = [e['torque'] for e in entries]
    
    summary = {
        "duration": entries[-1]['time'] - entries[0]['time'],
        "total_entries": len(entries),
        "power_stats": {
            "avg": sum(powers) / len(powers),
            "max": max(powers),
            "min": min(powers)
        },
        "efficiency_stats": {
            "avg": sum(efficiencies) / len(efficiencies),
            "max": max(efficiencies),
            "min": min(efficiencies)
        },
        "torque_stats": {
            "avg": sum(torques) / len(torques),
            "max": max(torques),
            "min": min(torques)
        }
    }
    
    return jsonify(summary)
```

#### 5.3 Frontend Analytics Dashboard (Day 3)
```javascript
// File: static/js/analytics.js (NEW)
class AnalyticsDashboard {
    constructor() {
        this.summaryData = null;
        this.setupAnalyticsUI();
    }
    
    setupAnalyticsUI() {
        // Add analytics section to UI
        const analyticsSection = document.createElement('div');
        analyticsSection.id = 'analyticsSection';
        analyticsSection.className = 'analytics-dashboard';
        analyticsSection.innerHTML = `
            <h3>Simulation Analytics</h3>
            <div class="analytics-grid">
                <div class="stat-card">
                    <h4>Average Power</h4>
                    <span id="avg-power">-- W</span>
                </div>
                <div class="stat-card">
                    <h4>Peak Efficiency</h4>
                    <span id="peak-efficiency">-- %</span>
                </div>
                <div class="stat-card">
                    <h4>Runtime</h4>
                    <span id="runtime">-- s</span>
                </div>
                <div class="stat-card">
                    <h4>Data Points</h4>
                    <span id="data-points">--</span>
                </div>
            </div>
            <div class="analytics-controls">
                <button id="refreshAnalytics">Refresh Analytics</button>
                <button id="exportAnalytics">Export Summary</button>
            </div>
        `;
        
        // Insert after main charts
        const chartsSection = document.querySelector('.charts-container');
        if (chartsSection) {
            chartsSection.parentNode.insertBefore(analyticsSection, chartsSection.nextSibling);
        }
        
        // Setup event listeners
        document.getElementById('refreshAnalytics')?.addEventListener('click', () => {
            this.refreshAnalytics();
        });
        
        document.getElementById('exportAnalytics')?.addEventListener('click', () => {
            this.exportAnalytics();
        });
        
        // Auto-refresh every 30 seconds
        setInterval(() => this.refreshAnalytics(), 30000);
    }
    
    async refreshAnalytics() {
        try {
            const response = await fetch('/analytics/summary');
            const data = await response.json();
            
            if (data.error) {
                console.warn('Analytics error:', data.error);
                return;
            }
            
            this.summaryData = data;
            this.updateAnalyticsDisplay(data);
            
        } catch (error) {
            console.error('Error fetching analytics:', error);
        }
    }
    
    updateAnalyticsDisplay(data) {
        const updates = {
            'avg-power': data.power_stats.avg.toFixed(1) + ' W',
            'peak-efficiency': data.efficiency_stats.max.toFixed(1) + '%',
            'runtime': data.duration.toFixed(1) + ' s',
            'data-points': data.total_entries.toString()
        };
        
        Object.entries(updates).forEach(([id, value]) => {
            const element = document.getElementById(id);
            if (element) element.textContent = value;
        });
    }
    
    async exportAnalytics() {
        if (!this.summaryData) {
            alert('No analytics data available');
            return;
        }
        
        const blob = new Blob([JSON.stringify(this.summaryData, null, 2)], {
            type: 'application/json'
        });
        
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `kpp_analytics_${new Date().toISOString().slice(0, 19)}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }
}
```

### Deliverables
- ✅ Comprehensive data logging system
- ✅ CSV and JSON export functionality
- ✅ Real-time analytics dashboard
- ✅ Performance statistics tracking
- ✅ Data export utilities

### Testing
- Large dataset export performance
- Analytics calculation accuracy
- Memory usage with extended logging
- Export file integrity

---

## **Integration & Testing Plan**

### Integration Timeline (2 days)
1. **Stage Integration** (1 day)
   - Combine all stage deliverables
   - Resolve interface conflicts
   - End-to-end testing

2. **Performance Optimization** (1 day)
   - SSE stream optimization
   - Chart rendering performance
   - Memory leak detection

### Testing Strategy

#### Functional Testing
- [ ] Parameter validation and UI response
- [ ] Physics hypothesis effects (H1, H2, H3)
- [ ] Real-time data accuracy
- [ ] Export functionality
- [ ] Connection recovery

#### Performance Testing
- [ ] Extended simulation runs (1+ hours)
- [ ] High-frequency data updates
- [ ] Multiple concurrent users
- [ ] Memory usage monitoring
- [ ] Network interruption recovery

#### User Acceptance Testing
- [ ] UI responsiveness and usability
- [ ] Scientific accuracy of outputs
- [ ] Data export workflows
- [ ] Error handling user experience

---

## **Deployment & Documentation**

### Deployment Checklist
- [ ] Production environment setup
- [ ] Dependency installation and verification
- [ ] Database/logging configuration
- [ ] Performance monitoring setup
- [ ] Backup and recovery procedures

### Documentation Deliverables
- [ ] User manual with feature explanations
- [ ] API documentation with examples
- [ ] Developer setup guide
- [ ] Physics model documentation
- [ ] Troubleshooting guide

---

## **Success Criteria**

### Technical Criteria
- ✅ All physics hypotheses (H1, H2, H3) functional
- ✅ Real-time data streaming with <100ms latency
- ✅ UI responsive across desktop and tablet devices
- ✅ Data export functions working reliably
- ✅ No memory leaks during extended operation

### User Experience Criteria
- ✅ Intuitive parameter adjustment interface
- ✅ Clear visualization of simulation effects
- ✅ Reliable connection status feedback
- ✅ Accessible data export and analysis tools

### Scientific Criteria
- ✅ Physics simulations match theoretical expectations
- ✅ Energy conservation respected in all modes
- ✅ Parameter effects clearly observable in outputs
- ✅ Logging sufficient for detailed analysis

---

## **Risk Mitigation**

### Technical Risks
- **SSE Connection Stability**: Implement robust reconnection logic
- **Performance with Complex Physics**: Use efficient calculation methods
- **Browser Compatibility**: Test across major browsers
- **Data Export Size Limits**: Implement pagination/streaming

### Project Risks
- **Scope Creep**: Maintain focus on core requirements
- **Integration Complexity**: Plan for buffer time between stages
- **Testing Coverage**: Automated testing for critical paths
- **Documentation Gaps**: Continuous documentation throughout development

---

## **Post-Implementation Support**

### Maintenance Plan
- Regular dependency updates
- Performance monitoring and optimization
- User feedback integration
- Bug fix prioritization

### Enhancement Roadmap
- Advanced analytics and ML insights
- Mobile application development
- Multi-user collaboration features
- Advanced physics model extensions

---

*This implementation plan provides a structured approach to delivering the KPP Frontend Patch with clear stages, deliverables, and success criteria. Each stage builds upon the previous one, ensuring a stable and progressive development process.*
