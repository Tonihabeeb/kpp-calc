# KPP Force Calculation Simulator

## Overview
This project is a modular, maintainable simulation of the KPP force calculation system, following the architecture and coding standards described in `guide-prestage.md`. The simulator models the physics of floaters, drivetrain, generator, fluid environment, pneumatic system, and control logic, and provides a real-time web interface for visualization and control.

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
1. Install requirements:
   ```sh
   pip install -r requirements.txt
   ```
2. Start the Flask app:
   ```sh
   python app.py
   ```
3. Open your browser to `http://localhost:5000` to use the web interface.

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
