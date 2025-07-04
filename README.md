# KPP Force Calculation Simulator

## Overview
This project is a modular, maintainable simulation of the KPP force calculation system, following the architecture and coding standards described in `guide-prestage.md`. The simulator models the physics of floaters, drivetrain, generator, fluid environment, pneumatic system, and control logic, and provides a real-time web interface for visualization and control.

## Services and Ports
The KPP simulator consists of multiple services running on different ports:

- **Backend API (Flask)**: `http://localhost:9100` - Main simulation backend with REST API
- **WebSocket Server (FastAPI)**: `ws://localhost:9101` - Real-time data streaming
- **Main Dashboard (Dash)**: `http://localhost:9102` - Full-featured web interface
- **Simple UI (Dash)**: `http://localhost:9103` - Lightweight control interface

## Architecture
- **simulation/components/environment.py**: Water properties, H1/H2 logic (nanobubble, thermal boost)
- **simulation/components/pneumatics.py**: Air injection, venting, compressor logic
- **simulation/components/floater.py**: Floater physics (buoyancy, drag, state)
- **simulation/components/drivetrain.py**: Chain, clutch, and generator coupling (H3 logic)
- **simulation/components/generator.py**: Power output calculation
- **simulation/components/control.py**: High-level control logic (stub, ready for extension)
- **simulation/components/sensors.py**: (Stub) For future sensor simulation
- **simulation/engine.py**: SimulationEngine orchestrates all modules, manages state, and coordinates the simulation loop
- **app.py**: Flask web app, all endpoints interact with the SimulationEngine only
- **tests/**: Unit tests for all main modules

## Running the App

### Quick Start (All Services)
1. Install requirements:
   ```sh
   pip install -r requirements.txt
   ```
2. Start all services at once:
   ```sh
   start_all.bat
   ```
   Or manually start each service:

### Manual Startup
1. **Backend API**:
   ```sh
   python app.py
   ```
   Access at: `http://localhost:9100`

2. **WebSocket Server**:
   ```sh
   python main.py
   ```
   Runs on: `ws://localhost:9101`

3. **Main Dashboard**:
   ```sh
   python dash_app.py
   ```
   Access at: `http://localhost:9102`

4. **Simple UI** (Optional):
   ```sh
   python simple_ui.py
   ```
   Access at: `http://localhost:9103`

## Running the Tests
1. From the project root, run:
   ```sh
   python -m unittest discover tests
   ```
   This will run all unit tests for the model modules.

## Developer Notes
- All modules are strictly separated and interact only via method calls and references, never global state.
- Each class and method is documented with Google-style docstrings.
- Logging is used throughout for debugging and tracing state changes.
- The architecture is designed for easy extension: add new modules or logic by subclassing or expanding the relevant component.
- For details on the design and extension points, see `guide-prestage.md`.

## Extending the Simulator
- Add new physics or hypotheses by extending the relevant component (e.g., add new fluid effects in `Environment`, new control strategies in `Control`).
- UI callbacks should always interact with the SimulationEngine, never with physics or state directly.
- For advanced features (e.g., sensors, new outputs), add a new module and integrate it via composition in `engine.py`.

---
For any questions, see the in-line comments and docstrings in each module, or refer to the implementation guide.
