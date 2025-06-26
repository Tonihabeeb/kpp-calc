# KPP Simulation System: Complete Data Flow Analysis

## 📋 Executive Summary

This document provides a thorough analysis of how data flows through the KPP (Kinetic Pulse Power) simulation system, from frontend inputs to backend processing and back to frontend outputs.

## 🏗️ System Architecture Overview

```
┌─────────────────┐    HTTP/WebSocket    ┌─────────────────┐    Method Calls    ┌─────────────────┐
│   Frontend      │ ◄──────────────────► │   Flask App     │ ◄─────────────────► │ Simulation      │
│   (Browser)     │                      │   (app.py)      │                     │ Engine          │
└─────────────────┘                      └─────────────────┘                     └─────────────────┘
      │                                           │                                        │
      │ User Interactions                         │ Route Handlers                         │ Component Updates
      ▼                                           ▼                                        ▼
┌─────────────────┐                      ┌─────────────────┐                     ┌─────────────────┐
│ - Input Fields  │                      │ - Parameter     │                     │ - Floaters      │
│ - Buttons       │                      │   Updates       │                     │ - Generator     │
│ - Sliders       │                      │ - Control       │                     │ - Drivetrain    │
│ - Charts        │                      │   Commands      │                     │ - Control       │
└─────────────────┘                      └─────────────────┘                     └─────────────────┘
```

## 🔄 Complete Data Flow Paths

### 1. INPUT FLOW: Frontend → Backend

#### **1.1 Parameter Updates (Form Submission)**

**Frontend (index.html):**
```html
<form id="paramsForm">
    <label>Number of Floaters: <input type="number" name="num_floaters" value="8"></label>
    <label>Floater Volume: <input type="number" name="floater_volume" value="0.3"></label>
    <label>Air Pressure: <input type="number" name="airPressure" value="3.0"></label>
    <!-- ... more parameters ... -->
    <button type="submit">Update Params</button>
</form>
```

**JavaScript (main.js):**
```javascript
document.getElementById('paramsForm').addEventListener('submit', function(e) {
    e.preventDefault();
    const formData = new FormData(this);
    const params = Object.fromEntries(formData.entries());
    
    // Convert numeric fields
    ['num_floaters', 'floater_volume', 'airPressure', ...].forEach(key => {
        if (params[key]) params[key] = parseFloat(params[key]);
    });
    
    fetch('/update_params', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(params)
    });
});
```

**Flask Route (app.py):**
```python
@app.route("/update_params", methods=["POST"])
def update_params():
    params = request.get_json() or {}
    engine.update_params(params)  # ← Calls simulation engine
    return ("OK", 200)
```

**Simulation Engine (engine.py):**
```python
def update_params(self, new_params):
    """Update simulation parameters dynamically"""
    self.params.update(new_params)
    
    # Update component parameters
    for i, floater in enumerate(self.floaters):
        floater.volume = new_params.get('floater_volume', floater.volume)
        floater.mass = new_params.get('floater_mass_empty', floater.mass)
        # ... update other floater properties
    
    # Update pneumatic system
    self.pneumatics.target_pressure = new_params.get('airPressure', self.pneumatics.target_pressure)
    
    # Update generator parameters
    self.generator.update_config(new_params)
```

#### **1.2 Control Commands (Button Clicks)**

**Frontend Buttons:**
```html
<button id="startBtn">Start</button>
<button id="stopBtn">Stop</button>
<button id="pulseBtn">Trigger Pulse</button>
```

**JavaScript Event Handlers:**
```javascript
document.getElementById('startBtn').addEventListener('click', function() {
    fetch('/start', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({})
    });
});

document.getElementById('pulseBtn').addEventListener('click', function() {
    fetch('/trigger_pulse', {method: 'POST'});
});
```

**Flask Control Routes:**
```python
@app.route("/start", methods=["POST"])
def start_simulation():
    params = request.get_json() or {}
    engine.reset()                    # ← Reset simulation state
    engine.update_params(params)      # ← Apply any parameters
    
    if not engine.thread or not engine.thread.is_alive():
        engine.running = True
        engine.thread = threading.Thread(target=engine.run, daemon=True)
        engine.thread.start()        # ← Start simulation thread
    return ("Simulation started", 200)

@app.route("/trigger_pulse", methods=["POST"])
def trigger_pulse():
    success = engine.trigger_pulse()  # ← Direct method call
    return ("Pulse triggered" if success else "Pulse failed", 200)
```

### 2. PROCESSING FLOW: Internal System Operation

#### **2.1 Simulation Loop (engine.py)**

```python
def run(self):
    """Main simulation loop - runs in separate thread"""
    self.running = True
    while self.running:
        self.step(self.dt)           # ← Core simulation step
        time.sleep(self.dt)          # ← Real-time pacing

def step(self, dt):
    """Single simulation step - where all the magic happens"""
    
    # 1. Check for pulse trigger
    if self.time - self.last_pulse_time >= self.params.get('pulse_interval', 2.0):
        self.trigger_pulse()
    
    # 2. Update pneumatic system
    self.pneumatics.update(dt)
    
    # 3. Update all floaters
    for floater in self.floaters:
        floater.update(dt, self.environment)
    
    # 4. Calculate forces and torques
    total_chain_torque = sum(f.compute_chain_torque(self.sprocket_radius) 
                           for f in self.floaters)
    
    # 5. Update drivetrain
    drivetrain_output = self.integrated_drivetrain.update(
        chain_tension=total_chain_torque, 
        electrical_load_torque=electrical_load_torque, 
        dt=dt
    )
    
    # 6. Update electrical system
    electrical_output = self.integrated_electrical_system.update(
        mechanical_torque=drivetrain_output['gearbox_output_torque'],
        shaft_speed=drivetrain_output['flywheel_speed_rpm'] * (2*pi/60),
        dt=dt
    )
    
    # 7. Update control system
    control_output = self.integrated_control_system.update(
        system_state=current_state, dt=dt
    )
    
    # 8. Log and queue data
    self.log_state(power_output, torque, ...)  # ← Generates output data
```

#### **2.2 Component Interactions**

**Floater Physics (floater.py):**
```python
def update(self, dt, environment):
    """Update floater state"""
    # 1. Calculate buoyant force
    buoyant_force = self.compute_buoyant_force()
    
    # 2. Calculate drag force
    drag_force = self.compute_drag_force()
    
    # 3. Update position and velocity
    net_force = buoyant_force - drag_force
    acceleration = net_force / self.effective_mass
    self.velocity += acceleration * dt
    self.position += self.velocity * dt
    
    # 4. Calculate chain torque contribution
    return self.compute_chain_torque(sprocket_radius)
```

**Generator Model (advanced_generator.py):**
```python
def update(self, shaft_speed, load_factor, dt):
    """Update generator electrical output"""
    # 1. Calculate electromagnetic torque
    self.torque = self._calculate_electromagnetic_torque(shaft_speed, load_factor)
    
    # 2. Calculate mechanical power input
    self.mechanical_power = self.torque * shaft_speed
    
    # 3. Calculate losses
    self._calculate_losses(shaft_speed, load_factor)
    
    # 4. Calculate electrical power output
    self.electrical_power = max(0.0, self.mechanical_power - self.total_losses)
    
    # 5. Calculate efficiency
    self.efficiency = self.electrical_power / self.mechanical_power if self.mechanical_power > 0 else 0.0
    
    return self._get_state_dict()
```

### 3. OUTPUT FLOW: Backend → Frontend

#### **3.1 Real-time Data Streaming (Server-Sent Events)**

**Flask SSE Route (app.py):**
```python
@app.route("/stream")
def stream():
    """Server-Sent Events endpoint for real-time data streaming"""
    def event_stream():
        while True:
            try:
                # Get latest data from engine
                if not engine.data_queue.empty():
                    data = engine.data_queue.get()    # ← Get from simulation queue
                    
                    # Format for frontend
                    yield f"data: {json.dumps(data)}\n\n"
                else:
                    # Send heartbeat
                    yield f"data: {json.dumps({'heartbeat': True})}\n\n"
                
                time.sleep(0.1)  # 10 Hz update rate
            except Exception as e:
                logger.error(f"SSE error: {e}")
                break
    
    return Response(event_stream(), mimetype="text/plain")
```

**Data State Structure (engine.py):**
```python
def log_state(self, power_output, torque, ...):
    """Create comprehensive state dictionary"""
    state = {
        # Basic metrics
        'time': self.time,
        'power': power_output,                    # ← Main power output
        'torque': torque,                        # ← Main torque
        'overall_efficiency': efficiency,
        
        # Mechanical system
        'flywheel_speed_rpm': flywheel_rpm,
        'chain_speed_rpm': chain_rpm,
        'clutch_engaged': clutch_engaged,
        
        # Floater states
        'floaters': [
            {
                'volume': f.volume,
                'mass': f.mass,
                'position': f.position,
                'velocity': f.velocity,
                'is_filled': f.is_filled,
                'fill_progress': f.fill_progress
            } for f in self.floaters
        ],
        
        # Advanced systems
        'enhanced_losses': enhanced_state,
        'thermal_state': thermal_state,
        'electrical_synchronized': electrical_output.get('synchronized', False),
        'grid_power_output': electrical_output.get('grid_power_output', 0.0),
        
        # Control system
        'control_mode': control_output.get('mode', 'normal'),
        'fault_status': control_output.get('faults', {}),
        
        # Performance metrics
        'pneumatic_performance': pneumatic_performance,
        'grid_services_performance': grid_services_performance,
        'advanced_generator': generator_output
    }
    
    self.data_queue.put(state)  # ← Send to frontend via SSE
    return state
```

#### **3.2 Frontend Real-time Updates**

**JavaScript SSE Handler (main.js):**
```javascript
function connectSSE() {
    eventSource = new EventSource('/stream');
    
    eventSource.onmessage = function(event) {
        const data = JSON.parse(event.data);
        if (!data.heartbeat) {
            updateFromSSEData(data);  // ← Process incoming data
        }
    };
}

function updateFromSSEData(data) {
    // 1. Update charts
    if (data.time !== undefined) {
        addData(torqueChart, data.time, data.torque || 0);
        addData(powerChart, data.time, (data.power || 0) / 1000);  // Convert to kW
        addData(effChart, data.time, (data.overall_efficiency || 0) * 100);
    }
    
    // 2. Update summary displays
    document.getElementById('summaryTime').textContent = (data.time || 0).toFixed(2);
    document.getElementById('summaryTorque').textContent = (data.torque || 0).toFixed(2);
    document.getElementById('summaryPower').textContent = ((data.power || 0) / 1000).toFixed(2);
    
    // 3. Update floater table
    if (data.floaters) {
        updateFloaterTable(data.floaters);
    }
    
    // 4. Update advanced metrics
    updatePneumaticStatus(data);
}
```

#### **3.3 API Endpoints for Data Queries**

**Summary Data Endpoint:**
```python
@app.route("/data/summary")
def summary_data():
    """Get current simulation summary"""
    latest = engine.collect_state()  # ← Get latest state
    
    return {
        'time': latest.get('time', 0),
        'torque': latest.get('torque', 0),
        'power': latest.get('power', 0),        # ← Power output
        'efficiency': latest.get('overall_efficiency', 0),
        'clutch_engaged': latest.get('clutch_engaged', False),
        'status': 'active' if latest.get('power', 0) > 0 else 'running'
    }
```

**Detailed System Status:**
```python
@app.route("/data/electrical_status")
def electrical_status():
    """Get detailed electrical system status"""
    latest = engine.collect_state()
    
    return {
        'advanced_generator': latest.get('advanced_generator', {}),
        'electrical_power': latest.get('grid_power_output', 0.0),
        'synchronization': latest.get('electrical_synchronized', False),
        'load_factor': latest.get('electrical_load_factor', 0.0),
        'efficiency': latest.get('electrical_efficiency', 0.0)
    }
```

## 🔧 Key Integration Points

### **Parameter Mapping Table**

| Frontend Input | Parameter Key | Engine Component | Effect |
|----------------|---------------|------------------|--------|
| `num_floaters` | `num_floaters` | `self.floaters` | Number of floater objects created |
| `floater_volume` | `floater_volume` | `floater.volume` | Buoyancy calculation |
| `airPressure` | `airPressure` | `pneumatics.target_pressure` | Air injection pressure |
| `sprocket_radius` | `sprocket_radius` | `drivetrain.sprocket_radius` | Torque multiplication |
| `flywheel_inertia` | `flywheel_inertia` | `drivetrain.flywheel_inertia` | Energy storage capacity |
| `pulse_interval` | `pulse_interval` | `trigger_pulse()` timing | Pulse frequency |
| `nanobubble_frac` | `nanobubble_frac` | `fluid_system.h1_active` | H1 effect activation |
| `thermal_coeff` | `thermal_coeff` | `thermal_model.thermal_expansion` | H2 effect strength |

### **Data State Hierarchy**

```
simulation_state = {
    ├── Basic Metrics
    │   ├── time: simulation_time
    │   ├── power: electrical_power_output  ← Main result
    │   ├── torque: mechanical_torque
    │   └── efficiency: overall_system_efficiency
    │
    ├── Mechanical Systems
    │   ├── floaters[]: individual_floater_states
    │   ├── drivetrain: speeds, torques, clutch_status
    │   └── pneumatics: pressure, flow_rates, thermodynamics
    │
    ├── Electrical Systems  
    │   ├── generator: power, torque, efficiency, losses
    │   ├── power_electronics: conversion, synchronization
    │   └── grid_interface: voltage, frequency, power_factor
    │
    ├── Control Systems
    │   ├── integrated_control: timing, load_management
    │   ├── fault_detection: active_faults, safety_status
    │   └── optimization: recommendations, performance
    │
    └── Advanced Features
        ├── enhanced_losses: detailed_loss_breakdown
        ├── thermal_modeling: component_temperatures
        ├── grid_services: frequency_response, voltage_support
        └── performance_analytics: efficiency_tracking, energy_balance
}
```

## 🎯 Critical Data Flow Points

### **1. Parameter Validation Chain**
```
Frontend Input → JavaScript Validation → Flask Route → Engine.update_params() → Component Updates → Immediate Effect
```

### **2. Real-time Feedback Loop**
```
Simulation Step → State Calculation → Queue Data → SSE Stream → Frontend Update → Chart Rendering → User Visibility
```

### **3. Control Command Execution**
```
Button Click → HTTP Request → Flask Route → Engine Method → Component Action → State Change → Real-time Display
```

## 🚀 Performance Considerations

### **Update Frequencies:**
- **Simulation Loop**: 10 Hz (every 0.1 seconds)
- **SSE Data Stream**: 10 Hz (matches simulation)
- **Chart Updates**: 10 Hz (with performance optimization)
- **Parameter Updates**: On-demand (user initiated)

### **Data Volume Management:**
- **Chart History**: Limited to last 100 points per chart
- **Queue Size**: Bounded to prevent memory issues
- **SSE Buffer**: Automatic cleanup on client disconnect

### **Thread Safety:**
- **Simulation Thread**: Dedicated thread for physics calculations
- **Flask Thread**: Handles HTTP requests
- **Queue Communication**: Thread-safe data exchange
- **State Locking**: Prevents race conditions during parameter updates

## 📊 Data Validation & Error Handling

### **Input Validation:**
```javascript
// Frontend validation
function validateParameters(params) {
    if (params.num_floaters < 1 || params.num_floaters > 20) {
        throw new Error("Number of floaters must be between 1-20");
    }
    if (params.floater_volume <= 0) {
        throw new Error("Floater volume must be positive");
    }
    // ... more validations
}
```

### **Backend Error Handling:**
```python
@app.route("/update_params", methods=["POST"])
def update_params():
    try:
        params = request.get_json() or {}
        validate_params(params)  # Custom validation
        engine.update_params(params)
        return ("OK", 200)
    except ValueError as e:
        return (f"Invalid parameters: {e}", 400)
    except Exception as e:
        logger.error(f"Parameter update error: {e}")
        return ("Internal error", 500)
```

## 🔍 Debugging & Monitoring

### **Data Flow Debugging:**
1. **Frontend Console**: `console.log()` for JavaScript debugging
2. **Network Tab**: Monitor HTTP requests and SSE data
3. **Backend Logs**: Flask and simulation engine logging
4. **CSV Export**: Raw simulation data for analysis
5. **State Inspection**: Real-time state viewing endpoints

### **Performance Monitoring:**
- **SSE Connection Status**: Real-time connection indicator
- **Data Queue Health**: Queue size and throughput monitoring
- **Simulation Performance**: Step timing and processing load
- **Memory Usage**: Object lifecycle and garbage collection

This comprehensive data flow analysis shows how the KPP simulation system creates a seamless pipeline from user interactions to real-time physics simulation and back to visual feedback, enabling users to control and monitor a complex multi-physics system through an intuitive web interface.
