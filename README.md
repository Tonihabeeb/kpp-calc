# KPP Simulator - Advanced Kinetic Power Plant Simulation

A sophisticated real-time simulation of a Kinetic Power Plant (KPP) with integrated electrical systems, enhanced physics, and professional monitoring capabilities.

## 🚀 Features

### **Core Simulation Engine**
- **Real-time Physics**: Advanced fluid dynamics, thermodynamics, and mechanical systems
- **Electrical Integration**: Complete electrical system with grid synchronization
- **Enhanced Physics**: H1 nanobubbles, H2 thermal enhancement, H3 pulse-coast operation
- **Field-Oriented Control (FOC)**: Precise motor control with advanced algorithms
- **Pressure Recovery System**: 22% energy recovery from vented air

### **Professional Dashboard**
- **Real-time Visualization**: Live charts, metrics, and system status
- **Advanced Controls**: Parameter adjustment with validation and recommendations
- **System Overview**: Component health monitoring and diagnostics
- **Professional UI**: Modern, responsive interface with Bootstrap 5

### **Real-time Synchronization**
- **Master Clock Server**: Centralized timing coordination at 30 FPS
- **WebSocket Streaming**: Real-time data broadcasting across all components
- **Trace Logging**: Request correlation and performance monitoring
- **Fallback Mechanisms**: Robust error handling and recovery

### **Advanced Control Systems**
- **Parameter Validation**: Real-time constraint checking and recommendations
- **Emergency Controls**: Immediate shutdown and safety systems
- **Multiple Control Modes**: Normal, manual, emergency operation
- **Intelligent Optimization**: AI-powered parameter recommendations

## 🏗️ Architecture

### **Server Components**

| Component | Port | Purpose | Features |
|-----------|------|---------|----------|
| **Master Clock** | 9201 | Synchronization Hub | 30 FPS timing, client management, metrics |
| **Backend API** | 9100 | Core Simulation Engine | Physics engine, electrical system, 100+ endpoints |
| **WebSocket Server** | 9101 | Real-time Data | Data streaming, trace logging, fallback |
| **Dash Dashboard** | 9103 | User Interface | Professional UI, controls, visualization |

### **System Integration**
```
Master Clock (9201) ←→ Backend API (9100)
       ↓                    ↓
WebSocket Server (9101) ←→ Dash Dashboard (9103)
```

## 🛠️ Installation

### **Prerequisites**
```bash
# Python 3.8+ required
python --version

# Install dependencies
pip install -r requirements.txt
```

### **Key Dependencies**
- **FastAPI**: Modern web framework for APIs
- **Dash**: Interactive web applications
- **WebSockets**: Real-time communication
- **Matplotlib**: Data visualization
- **NumPy**: Numerical computations
- **Requests**: HTTP client library

## 🚀 Quick Start

### **1. Start Master Clock Server (Required First)**
```bash
python realtime_sync_master_fixed.py
```
**Status**: http://localhost:9201/health

### **2. Start Backend API Server**
```bash
python app.py
```
**Status**: http://localhost:9100/status

### **3. Start WebSocket Server**
```bash
python main.py
```
**Status**: http://localhost:9101/state

### **4. Start Dashboard**
```bash
python dash_app.py
```
**Access**: http://localhost:9103

## 📊 Performance Specifications

### **Electrical System Performance**
- **Peak Power Output**: 34.6 kW electrical
- **Chain Tension**: 39,500 N maximum
- **Mechanical Torque**: 660 N·m
- **Overall Efficiency**: 85-92%
- **Electrical Engagement**: Bootstrap at 2kW+ mechanical power

### **System Performance**
- **Update Rate**: 30 FPS synchronized
- **Response Time**: <100ms control commands
- **Data Throughput**: 20+ real-time parameters
- **Stability**: Automatic failure recovery

## ⚙️ Configuration

### **Recommended Basic Parameters**
```json
{
  "num_floaters": 66,
  "floater_volume": 0.4,
  "air_pressure": 400000,
  "pulse_interval": 2.2,
  "tank_height": 25.0,
  "target_power": 530000
}
```

### **Advanced Physics Parameters**
```json
{
  "h1_enabled": true,
  "nanobubble_fraction": 0.05,
  "drag_reduction": 0.12,
  "h2_enabled": true,
  "thermal_efficiency": 0.8,
  "buoyancy_boost": 0.06,
  "h3_enabled": true,
  "pulse_duration": 2.0,
  "coast_duration": 1.0
}
```

### **Electrical System Parameters**
```json
{
  "foc_enabled": true,
  "foc_torque_kp": 120.0,
  "foc_flux_kp": 90.0,
  "pressure_recovery_efficiency": 0.22,
  "power_factor_target": 0.92
}
```

## 🎛️ Usage Guide

### **Dashboard Controls**

#### **Basic Parameters Panel**
- **Number of Floaters**: 4-100 (even numbers recommended)
- **Floater Volume**: 0.1-1.0 m³
- **Air Pressure**: 100,000-500,000 Pa
- **Pulse Interval**: 0.5-5.0 seconds

#### **Advanced Parameters Panel**
- **Physical Properties**: Mass, area, flow rates
- **Pneumatic System**: Fill times, pressure recovery
- **Water Jet Physics**: Efficiency, thrust optimization
- **Mechanical System**: Sprocket radius, flywheel inertia
- **Field-Oriented Control**: FOC parameters and gains

#### **Enhanced Physics Controls**
- **H1 Nanobubble Physics**: Drag reduction up to 12%
- **H2 Thermal Enhancement**: Buoyancy boost up to 6%
- **H3 Pulse-Coast Operation**: Optimized timing cycles
- **Environmental Controls**: Temperature management

### **Simulation Controls**
1. **Start**: Initialize and begin simulation
2. **Pause**: Temporarily halt simulation
3. **Stop**: End simulation and reset
4. **Reset**: Clear data and return to initial state
5. **Step**: Execute single simulation step

### **Advanced Controls**
- **Emergency Stop**: Immediate system shutdown
- **Trigger Pulse**: Manual air injection
- **Set Load**: Adjust mechanical load torque
- **Control Mode**: Switch between operation modes

## 📈 Monitoring & Analytics

### **Real-time Metrics**
- **Power Output**: Electrical power generation (kW)
- **Torque**: Mechanical torque (N·m)
- **Efficiency**: Overall system efficiency (%)
- **Chain Tension**: Mechanical chain force (N)
- **Flywheel Speed**: Rotational speed (RPM)
- **Pulse Count**: Number of air injection cycles

### **System Health**
- **Component Status**: Individual system health
- **Connection Status**: Server connectivity
- **Performance Metrics**: Frame rates, latencies
- **Error Tracking**: Fault detection and logging

### **Data Export**
- **CSV Export**: Download simulation data
- **Real-time Streaming**: WebSocket data feed
- **Historical Data**: Past simulation records
- **Performance Reports**: System analytics

## 🔧 API Endpoints

### **Core Simulation**
- `POST /start` - Start simulation
- `POST /stop` - Stop simulation
- `POST /pause` - Pause simulation
- `POST /reset` - Reset simulation
- `POST /step` - Single simulation step

### **Parameter Management**
- `POST /update_params` - Update simulation parameters
- `GET /parameters` - Get current parameters
- `POST /parameters/validate` - Validate parameters
- `GET /parameters/recommendations` - Get AI recommendations

### **Control Systems**
- `POST /control/trigger_emergency_stop` - Emergency shutdown
- `POST /control/enhanced_physics` - Enable physics enhancements
- `POST /control/h1_nanobubbles` - Nanobubble physics control
- `POST /control/h2_thermal` - Thermal enhancement control

### **Data & Monitoring**
- `GET /status` - System status
- `GET /data/live` - Real-time data
- `GET /data/summary` - System summary
- `GET /health` - Health check

## 🐛 Troubleshooting

### **Common Issues**

#### **Import Errors**
```bash
# Fixed: Use modern imports
from urllib3.util.retry import Retry  # ✅ Modern
# from requests.packages.urllib3.util.retry import Retry  # ❌ Deprecated
```

#### **Connection Issues**
- **Master Clock Not Available**: Start `realtime_sync_master_fixed.py` first
- **WebSocket Disconnection**: Automatic reconnection implemented
- **Backend Timeout**: Rate limiting prevents resource exhaustion

#### **Performance Issues**
- **High CPU Usage**: Rate limiting active (2 requests/second)
- **Memory Leaks**: Periodic garbage collection implemented
- **Slow Response**: Connection pooling and caching active

### **Verification Commands**
```bash
# Check all servers
curl http://localhost:9201/health    # Master Clock
curl http://localhost:9100/status    # Backend API
curl http://localhost:9101/state     # WebSocket Server
# Open http://localhost:9103         # Dashboard
```

## 🔬 Advanced Features

### **Enhanced Physics Engine**
- **H1 Nanobubble Physics**: Microbubble drag reduction
- **H2 Thermal Enhancement**: Temperature-optimized buoyancy
- **H3 Pulse-Coast Operation**: Energy-efficient timing
- **Water Jet Physics**: Enhanced propulsion efficiency

### **Electrical Integration**
- **Field-Oriented Control**: Precise motor control algorithms
- **Grid Synchronization**: Power factor and frequency control
- **Electrical Engagement**: Automatic bootstrap logic
- **Load Management**: Dynamic load balancing

### **Observability System**
- **Trace Logging**: Request correlation across services
- **Performance Metrics**: Real-time system analytics
- **Error Tracking**: Comprehensive fault detection
- **Health Monitoring**: Component status tracking

## 📚 Documentation

### **Technical Documentation**
- **API Reference**: Complete endpoint documentation
- **Architecture Guide**: System design and integration
- **Physics Models**: Mathematical formulations
- **Control Systems**: Algorithm descriptions

### **User Guides**
- **Getting Started**: Quick setup and first simulation
- **Parameter Tuning**: Optimization strategies
- **Troubleshooting**: Common issues and solutions
- **Advanced Usage**: Expert-level features

## 🤝 Contributing

### **Development Setup**
```bash
# Clone repository
git clone <repository-url>
cd kpp-simulator

# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
python -m pytest tests/

# Code quality
python -m flake8 .
python -m black .
```

### **Code Standards**
- **Type Hints**: All functions properly typed
- **Error Handling**: Comprehensive exception management
- **Documentation**: Docstrings for all functions
- **Testing**: Unit and integration tests

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Physics Engine**: Advanced fluid dynamics and thermodynamics
- **Electrical System**: Grid integration and power electronics
- **Real-time Architecture**: Synchronized multi-server design
- **Professional UI**: Modern dashboard and controls

---

**KPP Simulator v2.0** - Advanced Kinetic Power Plant Simulation with Integrated Electrical Systems and Enhanced Physics
