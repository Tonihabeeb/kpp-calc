# KPP Frontend Patch Implementation - Staged Execution Plan

## Overview
Based on the comprehensive frontend-patch.md requirements, this document provides a practical 7-stage implementation plan to transform the KPP simulator frontend into a production-ready, real-time system with enhanced physics modeling and improved UI controls.

## Current State Analysis
- ✅ Flask backend with simulation engine
- ✅ Basic Chart.js implementation  
- ✅ SSE streaming infrastructure
- ✅ Parameter form controls
- ⚠️ Mixed naming conventions (camelCase/snake_case)
- ⚠️ No unified parameter validation
- ⚠️ Limited physics hypothesis implementation
- ⚠️ No comprehensive error handling

---

## **STAGE 1: Parameter Normalization & Unified Control System** 
**Timeline: 2-3 days | Priority: Critical Foundation**

### Objectives
- Standardize all parameter naming to snake_case
- Implement unified parameter update mechanism
- Add robust parameter validation schema

### Tasks

#### 1.1 Backend Parameter Schema (Day 1)
```python
# File: config/parameter_schema.py (NEW)
PARAM_SCHEMA = {
    'air_pressure': {'type': float, 'unit': 'bar', 'min': 0.1, 'max': 10.0, 'default': 3.0},
    'nanobubble_frac': {'type': float, 'unit': '%', 'min': 0.0, 'max': 1.0, 'default': 0.0},
    'thermal_coeff': {'type': float, 'unit': '-', 'min': 0.0, 'max': 1.0, 'default': 0.0001},
    'pulse_enabled': {'type': bool, 'unit': 'bool', 'default': False},
    'num_floaters': {'type': int, 'unit': 'count', 'min': 1, 'max': 20, 'default': 8},
    'floater_volume': {'type': float, 'unit': 'm³', 'min': 0.1, 'max': 1.0, 'default': 0.3},
    'floater_mass_empty': {'type': float, 'unit': 'kg', 'min': 5.0, 'max': 50.0, 'default': 18.0},
    'floater_area': {'type': float, 'unit': 'm²', 'min': 0.01, 'max': 0.1, 'default': 0.035},
    'air_fill_time': {'type': float, 'unit': 's', 'min': 0.1, 'max': 2.0, 'default': 0.5},
    'air_flow_rate': {'type': float, 'unit': 'm³/s', 'min': 0.1, 'max': 2.0, 'default': 0.6},
    'jet_efficiency': {'type': float, 'unit': '-', 'min': 0.5, 'max': 1.0, 'default': 0.85},
    'sprocket_radius': {'type': float, 'unit': 'm', 'min': 0.1, 'max': 2.0, 'default': 0.5},
    'flywheel_inertia': {'type': float, 'unit': 'kg⋅m²', 'min': 10.0, 'max': 200.0, 'default': 50.0},
    'pulse_interval': {'type': float, 'unit': 's', 'min': 0.5, 'max': 10.0, 'default': 2.0},
    'water_temp': {'type': float, 'unit': '°C', 'min': 0.0, 'max': 100.0, 'default': 20.0}
}
```

#### 1.2 Enhanced /set_params Route (Day 1)
```python
# File: routes/api_routes.py (MODIFY app.py)
@app.route('/set_params', methods=['POST'])
def set_params():
    data = request.get_json() or {}
    errors = []
    
    for param, value in data.items():
        if param not in PARAM_SCHEMA:
            errors.append(f"Unknown parameter: {param}")
            continue
            
        schema = PARAM_SCHEMA[param]
        
        # Type validation and conversion
        try:
            if schema['type'] is float:
                converted_value = float(value)
            elif schema['type'] is int:
                converted_value = int(value)
            elif schema['type'] is bool:
                converted_value = bool(value) if isinstance(value, bool) else str(value).lower() in ('true', '1', 'yes')
        except (ValueError, TypeError):
            errors.append(f"Invalid type for {param}: expected {schema['type'].__name__}")
            continue
            
        # Range validation
        if 'min' in schema and converted_value < schema['min']:
            errors.append(f"{param} below minimum: {converted_value} < {schema['min']}")
            continue
        if 'max' in schema and converted_value > schema['max']:
            errors.append(f"{param} above maximum: {converted_value} > {schema['max']}")
            continue
            
        # Apply to simulation
        setattr(engine, param, converted_value)
        
        # Special handling for parameter-dependent resets
        if param == 'num_floaters':
            engine.reset_floaters()
            
    if errors:
        return jsonify({'errors': errors}), 400
        
    return '', 204
```

#### 1.3 Frontend Parameter Normalization (Day 2)
```html
<!-- File: templates/index.html - Normalize all input IDs -->
<form id="paramsForm">
    <h3>Basic Parameters</h3>
    <label>Number of Floaters: <input type="number" id="num_floaters" name="num_floaters" value="8" min="1" max="20"></label>
    <label>Floater Volume (m³): <input type="number" id="floater_volume" name="floater_volume" value="0.3" step="0.01"></label>
    <label>Air Pressure (bar): <input type="number" id="air_pressure" name="air_pressure" value="3.0" step="0.1"></label>
    
    <h3>H1/H2 Physics Enhancement</h3>
    <label>Nanobubble Fraction: <input type="range" id="nanobubble_frac" name="nanobubble_frac" min="0" max="100" value="0"> <span id="nanobubble_frac_val">0%</span></label>
    <label>Thermal Coefficient: <input type="number" id="thermal_coeff" name="thermal_coeff" step="0.0001" value="0.0001"></label>
    
    <h3>H3 Pulse Mode</h3>
    <label>Pulse Mode Enabled: <input type="checkbox" id="pulse_enabled" name="pulse_enabled"></label>
    <label>Pulse Interval (s): <input type="number" id="pulse_interval" name="pulse_interval" value="2.0" step="0.1"></label>
</form>
```

#### 1.4 Unified JavaScript Event Binding (Day 2-3)
```javascript
// File: static/js/main.js - Replace scattered event handlers
function updateParam(paramName, value) {
    fetch('/set_params', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ [paramName]: value })
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(err => Promise.reject(err));
        }
    })
    .catch(err => {
        console.error('Parameter update failed:', err);
        showErrorMessage(err.errors ? err.errors.join(', ') : 'Update failed');
    });
}

// Bind all controls to unified handler
document.addEventListener('DOMContentLoaded', function() {
    // Number inputs
    document.querySelectorAll('input[type="number"]').forEach(input => {
        input.addEventListener('input', (e) => {
            updateParam(e.target.id, parseFloat(e.target.value));
        });
    });
    
    // Range sliders
    document.querySelectorAll('input[type="range"]').forEach(slider => {
        slider.addEventListener('input', (e) => {
            const value = parseFloat(e.target.value);
            updateParam(e.target.id, value / 100); // Convert percentage to fraction
            document.getElementById(e.target.id + '_val').textContent = value + '%';
        });
    });
    
    // Checkboxes
    document.querySelectorAll('input[type="checkbox"]').forEach(checkbox => {
        checkbox.addEventListener('change', (e) => {
            updateParam(e.target.id, e.target.checked);
        });
    });
});
```

### Deliverables
- ✅ Consistent snake_case parameter naming across frontend/backend
- ✅ Robust parameter validation with error reporting
- ✅ Unified parameter update mechanism
- ✅ Error handling and user feedback

---

## **STAGE 2: Enhanced Physics Implementation (H1, H2, H3)**
**Timeline: 3-4 days | Priority: High - Core functionality**

### Objectives
- Implement Hypothesis 1 (Nanobubble drag reduction)
- Implement Hypothesis 2 (Thermal expansion boost)  
- Implement Hypothesis 3 (Pulse mode with clutch control)
- Add realistic drag modeling and physical limits

### Tasks

#### 2.1 H1 - Nanobubble Physics Implementation (Day 1)
```python
# File: simulation/physics/nanobubble_physics.py (NEW)
class NanobubblePhysics:
    def __init__(self):
        self.base_water_density = 1000.0  # kg/m³
        self.base_drag_coefficient = 0.47  # Sphere
        
    def get_effective_density(self, nanobubble_frac, position='descending'):
        """Apply density reduction for nanobubble effect"""
        if position == 'descending':
            # Nanobubbles reduce effective water density
            return self.base_water_density * (1 - nanobubble_frac)
        return self.base_water_density
        
    def get_effective_drag_coefficient(self, nanobubble_frac, velocity):
        """Apply drag reduction from boundary layer disruption"""
        # Research shows up to 50% drag reduction at high bubble concentrations
        drag_reduction_factor = 0.5 * nanobubble_frac
        return self.base_drag_coefficient * (1 - drag_reduction_factor)

# File: simulation/components/floater.py - Integrate H1 effects
def calculate_forces(self, nanobubble_frac=0.0):
    # Determine position in cycle
    position = 'ascending' if self.velocity > 0 else 'descending'
    
    # H1: Apply nanobubble effects
    effective_density = self.nanobubble_physics.get_effective_density(
        nanobubble_frac, position
    )
    effective_cd = self.nanobubble_physics.get_effective_drag_coefficient(
        nanobubble_frac, abs(self.velocity)
    )
    
    # Calculate buoyancy with adjusted density
    self.buoyancy = effective_density * self.submerged_volume * G
    
    # Calculate drag with improved formula: F_drag = 0.5 * ρ * Cd * A * v²
    drag_magnitude = 0.5 * effective_density * effective_cd * self.area * (self.velocity ** 2)
    self.drag = -drag_magnitude * np.sign(self.velocity)  # Oppose motion
    
    # Net force calculation
    self.net_force = self.buoyancy - self.weight + self.drag
    
    return self.net_force
```

#### 2.2 H2 - Thermal Expansion Implementation (Day 2)
```python
# File: simulation/physics/thermal_physics.py (NEW)
class ThermalPhysics:
    def __init__(self):
        self.reference_temp = 20.0  # °C
        
    def calculate_thermal_boost(self, thermal_coeff, water_temp, ref_temp, position='ascending'):
        """Calculate thermal expansion boost for ascending floaters"""
        if position == 'ascending' and thermal_coeff > 0:
            # Thermal boost only applies to air-filled ascending floaters
            temp_diff = water_temp - ref_temp
            return 1 + (thermal_coeff * temp_diff)
        return 1.0

# File: simulation/components/floater.py - Integrate H2 effects  
def calculate_forces(self, nanobubble_frac=0.0, thermal_coeff=0.0, water_temp=20.0):
    # ... H1 calculations ...
    
    # H2: Apply thermal expansion boost
    position = 'ascending' if self.velocity > 0 else 'descending'
    thermal_boost = self.thermal_physics.calculate_thermal_boost(
        thermal_coeff, water_temp, self.reference_temp, position
    )
    
    # Apply thermal boost to buoyancy for ascending floaters
    if position == 'ascending':
        self.buoyancy *= thermal_boost
        
    # Net force calculation
    self.net_force = self.buoyancy - self.weight + self.drag
    
    return self.net_force
```

#### 2.3 H3 - Pulse Mode Implementation (Day 3-4)
```python
# File: simulation/control/pulse_controller.py (NEW)
class PulseController:
    def __init__(self, pulse_interval=2.0, duty_cycle=0.5):
        self.pulse_interval = pulse_interval
        self.duty_cycle = duty_cycle  # Fraction of time clutch is engaged
        self.last_pulse_time = 0.0
        self.clutch_engaged = False
        
    def update_clutch_state(self, current_time):
        """Update clutch engagement based on pulse timing"""
        time_in_cycle = (current_time - self.last_pulse_time) % self.pulse_interval
        
        if time_in_cycle < (self.pulse_interval * self.duty_cycle):
            # Pulse phase - clutch engaged
            if not self.clutch_engaged:
                self.clutch_engaged = True
                logging.info(f"t={current_time:.2f}s: Clutch engaged, entering pulse phase")
        else:
            # Coast phase - clutch disengaged
            if self.clutch_engaged:
                self.clutch_engaged = False
                logging.info(f"t={current_time:.2f}s: Clutch disengaged, entering coast phase")
                
        return self.clutch_engaged

# File: simulation/engine.py - Integrate pulse control
def step(self):
    # ... existing physics calculations ...
    
    # H3: Update clutch state if pulse mode enabled
    if self.params.get('pulse_enabled', False):
        clutch_engaged = self.pulse_controller.update_clutch_state(self.time)
        
        # Apply generator load only when clutch engaged
        if clutch_engaged:
            self.torque_generator = self.calculate_generator_torque()
        else:
            self.torque_generator = 0.0  # Free-spinning during coast
    else:
        # Normal continuous mode
        self.torque_generator = self.calculate_generator_torque()
        clutch_engaged = True
        
    # Update total torque
    self.torque_total = self.calculate_net_torque() - self.torque_generator
```

### Deliverables
- ✅ H1 nanobubble physics with density and drag reduction
- ✅ H2 thermal expansion boost for ascending floaters
- ✅ H3 pulse mode with clutch control and timing
- ✅ Realistic drag equation implementation
- ✅ Physical limits and energy conservation checks

---

## **STAGE 3: Real-Time Data Streaming Enhancement**
**Timeline: 2-3 days | Priority: High - User experience**

### Objectives
- Enhance SSE output with comprehensive data structure
- Implement dynamic chart updates with new data fields
- Add floater table with real-time force display
- Implement connection status and error handling

### Tasks

#### 3.1 Enhanced SSE Data Structure (Day 1)
```python
# File: app.py - Enhanced /stream endpoint
@app.route('/stream')
def stream():
    def generate():
        while engine.running:
            engine.step()
            
            # Build comprehensive data structure
            data = {
                'time': engine.time,
                'torque': engine.torque_total,
                'power': engine.power_output / 1000,  # Convert to kW
                'efficiency': engine.efficiency * 100,  # Convert to percentage
                'torque_components': {
                    'buoyant': engine.torque_buoyant,
                    'drag': engine.torque_drag,
                    'generator': engine.torque_generator
                },
                'floaters': [
                    {
                        'buoyancy': f.buoyancy,
                        'drag': f.drag, 
                        'net_force': f.net_force,
                        'pulse_force': getattr(f, 'pulse_force', 0.0),
                        'position': f.position,
                        'velocity': f.velocity
                    } for f in engine.floaters
                ],
                'system_state': {
                    'clutch_engaged': getattr(engine, 'clutch_engaged', True),
                    'air_tank_pressure': getattr(engine, 'air_tank_pressure', 0.0),
                    'water_temp': engine.params.get('water_temp', 20.0)
                },
                'efficiency_breakdown': {
                    'drivetrain': getattr(engine, 'eff_drivetrain', engine.efficiency),
                    'pneumatic': getattr(engine, 'eff_pneumatic', engine.efficiency)
                }
            }
            
            yield f"data: {json.dumps(data)}\\n\\n"
            time.sleep(0.1)  # 10 Hz update rate
            
    return Response(generate(), mimetype='text/event-stream',
                   headers={'Cache-Control': 'no-cache'})
```

#### 3.2 Dynamic Chart Updates (Day 2)
```javascript
// File: static/js/main.js - Enhanced chart handling
function addData(chart, label, value, maxPoints = 100) {
    chart.data.labels.push(label);
    chart.data.datasets[0].data.push(value);
    
    // Limit data points to prevent memory bloat
    if (chart.data.labels.length > maxPoints) {
        chart.data.labels.shift();
        chart.data.datasets[0].data.shift();
    }
    
    chart.update('none'); // No animation for real-time
}

// Enhanced SSE message handler
function handleSSEMessage(event) {
    const data = JSON.parse(event.data);
    
    // Update main charts
    addData(torqueChart, data.time.toFixed(2), data.torque);
    addData(powerChart, data.time.toFixed(2), data.power);
    addData(effChart, data.time.toFixed(2), data.efficiency);
    
    // Update torque breakdown chart
    updateTorqueBreakdown(data.torque_components);
    
    // Update floater table
    updateFloaterTable(data.floaters);
    
    // Update system status
    updateSystemStatus(data.system_state);
    
    // Update efficiency breakdown
    updateEfficiencyDisplay(data.efficiency_breakdown);
}

function updateFloaterTable(floaters) {
    const table = document.getElementById('floaterTable');
    
    // Remove existing data rows (keep header)
    table.querySelectorAll('tr.floater-row').forEach(row => row.remove());
    
    // Add row for each floater
    floaters.forEach((floater, index) => {
        const row = table.insertRow();
        row.className = 'floater-row';
        
        row.insertCell().textContent = index + 1;
        row.insertCell().textContent = floater.position.toFixed(2);
        row.insertCell().textContent = floater.velocity.toFixed(2);
        row.insertCell().textContent = floater.buoyancy.toFixed(1);
        row.insertCell().textContent = floater.drag.toFixed(1);
        row.insertCell().textContent = floater.net_force.toFixed(1);
        row.insertCell().textContent = floater.pulse_force.toFixed(1);
    });
}
```

#### 3.3 Connection Status & Error Handling (Day 3)
```javascript
// File: static/js/main.js - SSE connection management
function initializeSSE() {
    if (eventSource) {
        eventSource.close();
    }
    
    eventSource = new EventSource('/stream');
    
    eventSource.onopen = function(event) {
        isConnected = true;
        updateConnectionStatus('Connected', 'success');
        console.log('SSE connection established');
    };
    
    eventSource.onmessage = handleSSEMessage;
    
    eventSource.onerror = function(event) {
        isConnected = false;
        updateConnectionStatus('Connection Error', 'error');
        console.error('SSE connection error:', event);
        
        // Auto-reconnect after 3 seconds
        setTimeout(() => {
            if (!isConnected) {
                initializeSSE();
            }
        }, 3000);
    };
    
    eventSource.onclose = function(event) {
        isConnected = false;
        updateConnectionStatus('Disconnected', 'warning');
        console.log('SSE connection closed');
    };
}

function updateConnectionStatus(status, type) {
    const statusElement = document.getElementById('sseStatus');
    statusElement.textContent = status;
    statusElement.className = `status-${type}`;
}
```

### Deliverables
- ✅ Comprehensive SSE data structure with all physics components
- ✅ Real-time chart updates with torque breakdown
- ✅ Dynamic floater force table
- ✅ Connection status monitoring and auto-reconnect
- ✅ Error handling and user feedback

---

## **STAGE 4: Advanced Physics & System Modeling**
**Timeline: 2-3 days | Priority: Medium - Realism enhancement**

### Objectives
- Implement compressed air tank and compressor modeling
- Add energy conservation checks and physical limits
- Enhance torque and power calculations
- Add system health monitoring

### Tasks

#### 4.1 Compressed Air System (Day 1-2)
```python
# File: simulation/components/air_system.py (NEW)
class CompressedAirSystem:
    def __init__(self, tank_volume=1.0, max_pressure=10.0, compressor_flow=0.1):
        self.tank_volume = tank_volume  # m³
        self.max_pressure = max_pressure  # bar
        self.current_pressure = max_pressure  # Start full
        self.compressor_flow_rate = compressor_flow  # m³/s at standard pressure
        self.pressure_threshold = 3.0  # Minimum pressure for floater fill
        
    def can_fill_floater(self, required_volume=0.3):
        """Check if sufficient pressure for floater fill"""
        return self.current_pressure >= self.pressure_threshold
        
    def fill_floater(self, floater_volume=0.3):
        """Use compressed air to fill floater"""
        if self.can_fill_floater(floater_volume):
            # Calculate pressure drop from air usage
            pressure_used = (floater_volume / self.tank_volume) * self.current_pressure
            self.current_pressure = max(0, self.current_pressure - pressure_used)
            return True
        return False
        
    def update_compressor(self, dt, running=True):
        """Update air tank pressure from compressor"""
        if running and self.current_pressure < self.max_pressure:
            # Add air based on compressor capacity
            pressure_gain = (self.compressor_flow_rate * dt / self.tank_volume) * self.max_pressure
            self.current_pressure = min(self.max_pressure, self.current_pressure + pressure_gain)

# Integration in simulation engine
def step(self):
    # Update air system
    self.air_system.update_compressor(self.dt, running=True)
    
    # Check floater filling capability
    for floater in self.floaters:
        if floater.needs_air_fill():
            if self.air_system.fill_floater(floater.volume):
                floater.fill_with_air()
                logging.info(f"t={self.time:.2f}s: Floater filled, tank pressure: {self.air_system.current_pressure:.1f} bar")
            else:
                logging.warning(f"t={self.time:.2f}s: Insufficient pressure to fill floater, skipping")
```

#### 4.2 Energy Conservation & Physical Limits (Day 2-3)
```python
# File: simulation/physics/energy_monitor.py (NEW)
class EnergyMonitor:
    def __init__(self):
        self.total_energy_input = 0.0
        self.total_energy_output = 0.0
        self.compressor_energy = 0.0
        self.generator_energy = 0.0
        
    def update(self, dt, compressor_power, generator_power):
        """Track energy flows"""
        self.compressor_energy += compressor_power * dt
        self.generator_energy += generator_power * dt
        
        self.total_energy_input = self.compressor_energy
        self.total_energy_output = self.generator_energy
        
    def check_energy_conservation(self):
        """Verify energy conservation (output <= input)"""
        efficiency = (self.total_energy_output / self.total_energy_input) if self.total_energy_input > 0 else 0
        
        if efficiency > 1.0:
            logging.warning(f"Energy conservation violation: efficiency = {efficiency:.2%}")
            return False
        return True
        
    def get_instantaneous_efficiency(self, current_output_power, current_input_power):
        """Calculate instantaneous efficiency"""
        if current_input_power > 0:
            return min(1.0, current_output_power / current_input_power)
        return 0.0
```

### Deliverables
- ✅ Realistic compressed air tank and compressor modeling
- ✅ Energy conservation monitoring and warnings
- ✅ Physical limits enforcement
- ✅ Enhanced system health tracking

---

## **STAGE 5: Data Export & Analytics**
**Timeline: 1-2 days | Priority: Medium - Analysis support**

### Objectives
- Implement comprehensive logging system
- Add CSV/JSON export functionality
- Create data analysis endpoints
- Add debugging and monitoring tools

### Tasks

#### 5.1 Comprehensive Logging (Day 1)
```python
# File: simulation/monitoring/data_logger.py (NEW)
class SimulationDataLogger:
    def __init__(self):
        self.log = []
        self.events = []
        
    def log_step(self, engine):
        """Log comprehensive state data each simulation step"""
        entry = {
            'time': engine.time,
            'torque': engine.torque_total,
            'power': engine.power_output,
            'efficiency': engine.efficiency,
            'torque_components': {
                'buoyant': engine.torque_buoyant,
                'drag': engine.torque_drag, 
                'generator': engine.torque_generator
            },
            'floaters': [
                {
                    'buoyancy': f.buoyancy,
                    'drag': f.drag,
                    'net_force': f.net_force,
                    'position': f.position,
                    'velocity': f.velocity
                } for f in engine.floaters
            ],
            'system_state': {
                'clutch_engaged': getattr(engine, 'clutch_engaged', True),
                'air_tank_pressure': getattr(engine, 'air_tank_pressure', 0.0),
                'water_temp': engine.params.get('water_temp', 20.0)
            }
        }
        self.log.append(entry)
        
    def log_event(self, event_type, message, time):
        """Log significant events"""
        self.events.append({
            'time': time,
            'type': event_type,
            'message': message
        })

# File: app.py - Export endpoints
@app.route('/download_csv')
def download_csv():
    def generate_csv():
        # Header
        yield "time,torque,power,efficiency,torque_buoyant,torque_drag,torque_generator"
        for i in range(engine.params['num_floaters']):
            yield f",f{i+1}_buoyancy,f{i+1}_drag,f{i+1}_net_force,f{i+1}_position,f{i+1}_velocity"
        yield "\\n"
        
        # Data rows
        for entry in engine.data_logger.log:
            line = f"{entry['time']:.3f},{entry['torque']:.2f},{entry['power']:.1f},{entry['efficiency']:.3f}"
            line += f",{entry['torque_components']['buoyant']:.2f},{entry['torque_components']['drag']:.2f},{entry['torque_components']['generator']:.2f}"
            
            for floater in entry['floaters']:
                line += f",{floater['buoyancy']:.2f},{floater['drag']:.2f},{floater['net_force']:.2f},{floater['position']:.3f},{floater['velocity']:.3f}"
            
            yield line + "\\n"
    
    response = Response(generate_csv(), mimetype='text/csv')
    response.headers['Content-Disposition'] = 'attachment; filename="kpp_simulation_data.csv"'
    return response

@app.route('/get_output_schema')
def get_output_schema():
    schema = {
        'time': 'float (s) - Simulation time',
        'torque': 'float (N·m) - Net torque on main shaft',
        'power': 'float (W) - Generator electrical output',
        'efficiency': 'float (%) - Overall system efficiency',
        'torque_components': {
            'buoyant': 'float (N·m) - Torque from buoyancy forces',
            'drag': 'float (N·m) - Torque lost to drag',
            'generator': 'float (N·m) - Generator load torque'
        },
        'floaters': [{
            'buoyancy': 'float (N) - Buoyant force',
            'drag': 'float (N) - Drag force',
            'net_force': 'float (N) - Net force on floater',
            'pulse_force': 'float (N) - Additional pulse injection force',
            'position': 'float (m) - Vertical position',
            'velocity': 'float (m/s) - Vertical velocity'
        }],
        'system_state': {
            'clutch_engaged': 'bool - H3 clutch engagement state',
            'air_tank_pressure': 'float (bar) - Compressed air pressure',
            'water_temp': 'float (°C) - Water temperature'
        }
    }
    return jsonify(schema)
```

### Deliverables
- ✅ Comprehensive simulation data logging
- ✅ CSV export with all parameters and forces
- ✅ JSON schema documentation endpoint
- ✅ Event logging for significant occurrences

---

## **STAGE 6: UI Polish & User Experience**
**Timeline: 2-3 days | Priority: Medium - User satisfaction**

### Objectives
- Enhance visual design and layout
- Add real-time status indicators
- Implement user feedback and validation
- Optimize performance and responsiveness

### Tasks

#### 6.1 Enhanced UI Layout (Day 1-2)
```html
<!-- File: templates/index.html - Enhanced layout -->
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>KPP Simulator - Real-Time Physics v3.0</title>
    <link rel="stylesheet" href="/static/css/enhanced_style.css">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
</head>
<body class="bg-gray-50">
    <!-- Header with status -->
    <header class="bg-blue-600 text-white p-4 shadow-lg">
        <div class="flex justify-between items-center">
            <h1 class="text-2xl font-bold">KPP Simulator - Real-Time Physics v3.0</h1>
            <div class="flex items-center space-x-4">
                <div id="connection-status" class="flex items-center">
                    <i id="status-icon" class="fas fa-circle text-red-500 mr-2"></i>
                    <span id="sseStatus">Disconnected</span>
                </div>
                <div class="text-sm">
                    <span>Time: </span><span id="sim-time" class="font-mono">0.00s</span>
                </div>
            </div>
        </div>
    </header>

    <!-- Main content grid -->
    <div class="container mx-auto p-4 grid grid-cols-12 gap-4">
        <!-- Control Panel -->
        <aside class="col-span-3 bg-white rounded-lg shadow p-4">
            <h2 class="text-xl font-semibold mb-4">Control Panel</h2>
            
            <!-- Simulation Controls -->
            <div class="mb-6">
                <h3 class="font-medium mb-2">Simulation</h3>
                <div class="flex space-x-2 mb-3">
                    <button id="startBtn" class="btn btn-success flex-1">
                        <i class="fas fa-play mr-1"></i>Start
                    </button>
                    <button id="pauseBtn" class="btn btn-warning flex-1">
                        <i class="fas fa-pause mr-1"></i>Pause
                    </button>
                    <button id="resetBtn" class="btn btn-danger flex-1">
                        <i class="fas fa-reset mr-1"></i>Reset
                    </button>
                </div>
            </div>

            <!-- Parameter Forms with organized sections -->
            <form id="paramsForm" class="space-y-4">
                <!-- H1: Nanobubble Effects -->
                <div class="param-section">
                    <h3 class="param-section-title">H1: Nanobubble Effects</h3>
                    <div class="param-group">
                        <label class="param-label">
                            Nanobubble Fraction
                            <input type="range" id="nanobubble_frac" min="0" max="100" value="0" class="range-input">
                            <span id="nanobubble_frac_val" class="param-value">0%</span>
                        </label>
                    </div>
                </div>

                <!-- H2: Thermal Effects -->
                <div class="param-section">
                    <h3 class="param-section-title">H2: Thermal Enhancement</h3>
                    <div class="param-group">
                        <label class="param-label">
                            Thermal Coefficient
                            <input type="number" id="thermal_coeff" step="0.0001" value="0.0001" class="number-input">
                        </label>
                        <label class="param-label">
                            Water Temperature (°C)
                            <input type="number" id="water_temp" step="0.1" value="20.0" class="number-input">
                        </label>
                    </div>
                </div>

                <!-- H3: Pulse Mode -->
                <div class="param-section">
                    <h3 class="param-section-title">H3: Pulse Mode</h3>
                    <div class="param-group">
                        <label class="checkbox-label">
                            <input type="checkbox" id="pulse_enabled" class="checkbox-input">
                            <span class="checkbox-text">Enable Pulse Mode</span>
                        </label>
                        <label class="param-label">
                            Pulse Interval (s)
                            <input type="number" id="pulse_interval" step="0.1" value="2.0" class="number-input">
                        </label>
                    </div>
                </div>
            </form>
        </aside>

        <!-- Main Charts Area -->
        <main class="col-span-6 space-y-4">
            <!-- Primary Charts -->
            <div class="grid grid-cols-2 gap-4">
                <div class="chart-card">
                    <h3 class="chart-title">Torque Output</h3>
                    <canvas id="torqueChart"></canvas>
                </div>
                <div class="chart-card">
                    <h3 class="chart-title">Power Output</h3>
                    <canvas id="powerChart"></canvas>
                </div>
            </div>
            
            <!-- Secondary Charts -->
            <div class="grid grid-cols-2 gap-4">
                <div class="chart-card">
                    <h3 class="chart-title">System Efficiency</h3>
                    <canvas id="effChart"></canvas>
                </div>
                <div class="chart-card">
                    <h3 class="chart-title">Torque Breakdown</h3>
                    <canvas id="torqueBreakdownChart"></canvas>
                </div>
            </div>
        </main>

        <!-- System Status & Data -->
        <aside class="col-span-3 space-y-4">
            <!-- Live Metrics -->
            <div class="status-card">
                <h3 class="status-title">Live Metrics</h3>
                <div class="metric-grid">
                    <div class="metric-item">
                        <span class="metric-label">Torque:</span>
                        <span id="live-torque" class="metric-value">0.0 Nm</span>
                    </div>
                    <div class="metric-item">
                        <span class="metric-label">Power:</span>
                        <span id="live-power" class="metric-value">0.0 kW</span>
                    </div>
                    <div class="metric-item">
                        <span class="metric-label">Efficiency:</span>
                        <span id="live-efficiency" class="metric-value">0.0%</span>
                    </div>
                </div>
            </div>

            <!-- Floater Forces Table -->
            <div class="table-card">
                <h3 class="table-title">Floater Forces</h3>
                <div class="table-container">
                    <table id="floaterTable" class="force-table">
                        <thead>
                            <tr>
                                <th>#</th>
                                <th>Buoy(N)</th>
                                <th>Drag(N)</th>
                                <th>Net(N)</th>
                            </tr>
                        </thead>
                        <tbody>
                            <!-- Dynamic rows -->
                        </tbody>
                    </table>
                </div>
            </div>

            <!-- Export Controls -->
            <div class="export-card">
                <h3 class="export-title">Data Export</h3>
                <div class="export-buttons">
                    <a href="/download_csv" class="btn btn-outline" target="_blank">
                        <i class="fas fa-download mr-1"></i>CSV
                    </a>
                    <button id="exportJson" class="btn btn-outline">
                        <i class="fas fa-download mr-1"></i>JSON
                    </button>
                </div>
            </div>
        </aside>
    </div>
</body>
</html>
```

#### 6.2 Enhanced CSS Styling (Day 2)
```css
/* File: static/css/enhanced_style.css */
:root {
    --primary-color: #3b82f6;
    --success-color: #10b981;
    --warning-color: #f59e0b;
    --danger-color: #ef4444;
    --gray-50: #f9fafb;
    --gray-100: #f3f4f6;
    --gray-200: #e5e7eb;
    --gray-600: #4b5563;
    --gray-800: #1f2937;
}

.container {
    max-width: 1400px;
}

/* Button Styles */
.btn {
    @apply px-4 py-2 rounded-md font-medium transition-colors duration-200 flex items-center justify-center;
}

.btn-success {
    @apply bg-green-500 text-white hover:bg-green-600;
}

.btn-warning {
    @apply bg-yellow-500 text-white hover:bg-yellow-600;
}

.btn-danger {
    @apply bg-red-500 text-white hover:bg-red-600;
}

.btn-outline {
    @apply border border-gray-300 text-gray-700 hover:bg-gray-50;
}

/* Parameter Controls */
.param-section {
    @apply border border-gray-200 rounded-lg p-3 mb-3;
}

.param-section-title {
    @apply font-semibold text-gray-800 mb-2 flex items-center;
}

.param-group {
    @apply space-y-2;
}

.param-label {
    @apply block text-sm font-medium text-gray-700 mb-1;
}

.number-input, .range-input {
    @apply w-full px-3 py-1 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500;
}

.param-value {
    @apply text-sm font-mono text-blue-600 ml-2;
}

.checkbox-label {
    @apply flex items-center space-x-2 cursor-pointer;
}

.checkbox-input {
    @apply w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500;
}

/* Chart Cards */
.chart-card {
    @apply bg-white rounded-lg shadow p-4 min-h-[300px];
}

.chart-title {
    @apply text-lg font-semibold text-gray-800 mb-3 text-center;
}

/* Status Cards */
.status-card, .table-card, .export-card {
    @apply bg-white rounded-lg shadow p-4;
}

.status-title, .table-title, .export-title {
    @apply text-lg font-semibold text-gray-800 mb-3;
}

.metric-grid {
    @apply grid grid-cols-1 gap-2;
}

.metric-item {
    @apply flex justify-between items-center py-1;
}

.metric-label {
    @apply text-sm text-gray-600;
}

.metric-value {
    @apply text-sm font-mono font-semibold text-blue-600;
}

/* Table Styles */
.table-container {
    @apply max-h-64 overflow-y-auto;
}

.force-table {
    @apply w-full text-xs;
}

.force-table th {
    @apply bg-gray-50 px-2 py-1 text-left font-medium text-gray-700 sticky top-0;
}

.force-table td {
    @apply px-2 py-1 border-b border-gray-100 font-mono;
}

/* Connection Status */
.status-connected #status-icon {
    @apply text-green-500;
}

.status-error #status-icon {
    @apply text-red-500;
}

.status-warning #status-icon {
    @apply text-yellow-500;
}

/* Export Buttons */
.export-buttons {
    @apply flex space-x-2;
}

/* Responsive Design */
@media (max-width: 1024px) {
    .container {
        @apply grid-cols-1;
    }
    
    aside {
        @apply col-span-1;
    }
    
    main {
        @apply col-span-1;
    }
}
```

### Deliverables
- ✅ Modern, responsive UI design
- ✅ Organized parameter controls with visual grouping
- ✅ Real-time status indicators and live metrics
- ✅ Enhanced chart presentation and data tables
- ✅ Professional visual design

---

## **STAGE 7: Testing, Integration & Documentation**
**Timeline: 2-3 days | Priority: Critical - Quality assurance**

### Objectives
- Comprehensive end-to-end testing
- Performance optimization
- Integration verification
- User documentation and deployment guide

### Tasks

#### 7.1 Comprehensive Testing (Day 1-2)
```python
# File: tests/test_frontend_integration.py (NEW)
import pytest
import json
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class TestFrontendIntegration:
    @pytest.fixture
    def driver(self):
        driver = webdriver.Chrome()
        driver.get("http://localhost:5000")
        yield driver
        driver.quit()
    
    def test_parameter_updates(self, driver):
        """Test parameter updates through UI"""
        # Test nanobubble slider
        slider = driver.find_element(By.ID, "nanobubble_frac")
        slider.click()
        driver.execute_script("arguments[0].value = 50", slider)
        slider.send_keys("")  # Trigger change event
        
        time.sleep(1)  # Allow backend processing
        
        # Verify parameter was received (check console logs or backend state)
        
    def test_sse_connection(self, driver):
        """Test SSE connection and data reception"""
        # Wait for connection indicator
        status = WebDriverWait(driver, 10).until(
            EC.text_to_be_present_in_element((By.ID, "sseStatus"), "Connected")
        )
        assert status
        
        # Start simulation
        start_button = driver.find_element(By.ID, "startBtn")
        start_button.click()
        
        # Wait for data updates
        time.sleep(5)
        
        # Check if charts are updating
        torque_chart = driver.find_element(By.ID, "torqueChart")
        assert torque_chart.is_displayed()
        
    def test_hypothesis_effects(self, driver):
        """Test H1, H2, H3 hypothesis implementations"""
        # Test H1 - Nanobubble effects
        self._set_slider_value(driver, "nanobubble_frac", 30)
        
        # Test H2 - Thermal effects  
        thermal_input = driver.find_element(By.ID, "thermal_coeff")
        thermal_input.clear()
        thermal_input.send_keys("0.1")
        
        # Test H3 - Pulse mode
        pulse_checkbox = driver.find_element(By.ID, "pulse_enabled")
        pulse_checkbox.click()
        
        # Verify system responds to changes
        time.sleep(10)
        
        # Check for expected behavior changes in metrics
        
    def _set_slider_value(self, driver, slider_id, value):
        slider = driver.find_element(By.ID, slider_id)
        driver.execute_script(f"arguments[0].value = {value}", slider)
        driver.execute_script("arguments[0].dispatchEvent(new Event('input'))", slider)

# File: tests/test_physics_validation.py (NEW)
class TestPhysicsValidation:
    def test_energy_conservation(self):
        """Verify energy conservation in simulation"""
        # Run simulation with known parameters
        # Check that efficiency never exceeds 100%
        # Verify energy input >= energy output
        
    def test_h1_nanobubble_effects(self):
        """Test H1 nanobubble physics implementation"""
        # Test drag reduction with different nanobubble fractions
        # Verify density reduction effects
        
    def test_h2_thermal_effects(self):
        """Test H2 thermal expansion physics"""
        # Test thermal boost calculations
        # Verify temperature-dependent effects
        
    def test_h3_pulse_mode(self):
        """Test H3 pulse mode clutch control"""
        # Test clutch engagement timing
        # Verify pulse vs coast phases
```

#### 7.2 Performance Optimization (Day 2)
```javascript
// File: static/js/performance_optimizations.js
class PerformanceManager {
    constructor() {
        this.updateQueue = [];
        this.lastUpdate = 0;
        this.updateInterval = 100; // 10 Hz max update rate
        this.maxDataPoints = 200;
    }
    
    queueUpdate(updateFunction) {
        this.updateQueue.push(updateFunction);
        this.processQueue();
    }
    
    processQueue() {
        const now = Date.now();
        if (now - this.lastUpdate >= this.updateInterval) {
            // Process all queued updates
            this.updateQueue.forEach(update => update());
            this.updateQueue = [];
            this.lastUpdate = now;
        }
    }
    
    optimizeChartData(chart) {
        // Limit data points to prevent memory bloat
        if (chart.data.labels.length > this.maxDataPoints) {
            const removeCount = chart.data.labels.length - this.maxDataPoints;
            chart.data.labels.splice(0, removeCount);
            chart.data.datasets.forEach(dataset => {
                dataset.data.splice(0, removeCount);
            });
        }
    }
}

// Implement virtual scrolling for floater table if many floaters
class VirtualFloaterTable {
    constructor(tableElement, rowHeight = 25) {
        this.table = tableElement;
        this.rowHeight = rowHeight;
        this.visibleRows = Math.ceil(tableElement.clientHeight / rowHeight);
        this.scrollTop = 0;
    }
    
    updateTable(floaterData) {
        const startIndex = Math.floor(this.scrollTop / this.rowHeight);
        const endIndex = Math.min(startIndex + this.visibleRows, floaterData.length);
        
        // Clear existing rows
        const tbody = this.table.querySelector('tbody');
        tbody.innerHTML = '';
        
        // Render only visible rows
        for (let i = startIndex; i < endIndex; i++) {
            const row = this.createFloaterRow(floaterData[i], i);
            tbody.appendChild(row);
        }
    }
}
```

#### 7.3 User Documentation (Day 3)
```markdown
# File: docs/USER_GUIDE.md (NEW)
# KPP Simulator User Guide

## Quick Start
1. Start the Flask application: `python app.py`
2. Open browser to `http://localhost:5000`
3. Click "Start" to begin real-time simulation
4. Adjust parameters to see live effects

## Physics Hypotheses

### H1: Nanobubble Effects
- **Control**: Nanobubble Fraction slider (0-100%)
- **Effect**: Reduces drag and water density on descending side
- **Research Basis**: Microbubble boundary layer disruption

### H2: Thermal Enhancement  
- **Control**: Thermal Coefficient input
- **Effect**: Increases buoyancy for ascending floaters via thermal expansion
- **Research Basis**: Near-isothermal air expansion with ambient heat

### H3: Pulse Mode
- **Control**: Pulse Mode checkbox + Pulse Interval
- **Effect**: Alternates between coast (no generator load) and pulse (full load) phases
- **Research Basis**: Pulse-and-coast efficiency optimization

## Parameter Guidelines

### Safe Operating Ranges
- Nanobubble Fraction: 0-30% (higher values may be unrealistic)
- Thermal Coefficient: 0-0.1 (conservative thermal effects)
- Pulse Interval: 1-5 seconds (optimal cycling)

### Troubleshooting
- **Connection Issues**: Check SSE status indicator, refresh if disconnected
- **No Data Updates**: Verify simulation is started, check browser console
- **Performance Issues**: Reduce update frequency or data history length

## Data Export
- **CSV Export**: Full time-series data with all parameters
- **Live Monitoring**: Real-time charts and floater force tables
- **Schema Documentation**: Available at `/get_output_schema`
```

### Deliverables
- ✅ Comprehensive test suite with Selenium automation
- ✅ Performance optimizations for real-time operation
- ✅ Physics validation and energy conservation checks
- ✅ Complete user documentation and deployment guide

---

## **Final Validation & Production Readiness**

### Success Criteria
- [ ] All parameter controls update simulation in real-time
- [ ] H1, H2, H3 hypotheses implemented and functional
- [ ] SSE streaming works reliably with comprehensive data
- [ ] Charts update smoothly without performance issues
- [ ] Floater force table displays accurate real-time data
- [ ] Error handling and connection recovery work properly
- [ ] CSV export contains complete simulation data
- [ ] Energy conservation monitoring prevents impossible results
- [ ] UI is responsive and professional
- [ ] All tests pass and system is stable

### Performance Targets
- **SSE Update Rate**: 10 Hz (100ms intervals)
- **Chart Response Time**: < 50ms per update
- **Parameter Update Latency**: < 100ms
- **Memory Usage**: Stable over long runs (no leaks)
- **CPU Usage**: < 30% during normal operation

### Risk Mitigation
- **SSE Connection Loss**: Auto-reconnect with user notification
- **Parameter Validation Errors**: Clear error messages and rollback
- **Performance Degradation**: Data point limiting and chart optimization
- **Physics Instability**: Bounds checking and energy conservation monitoring

---

## **Implementation Notes**

1. **Prioritization**: Stages 1-3 are critical path; Stages 4-7 can be parallelized
2. **Testing Strategy**: Test each stage thoroughly before proceeding
3. **Rollback Plan**: Keep backup of working versions at each stage
4. **Documentation**: Update technical documentation as features are implemented
5. **User Feedback**: Gather feedback early from Stage 3 onwards

This staged implementation ensures a systematic, testable approach to delivering the comprehensive frontend patch while maintaining system stability and user experience throughout the development process.
