1. Define Your Target State
Goal:

Only one simulation engine.

Tracks every floater, every second/millisecond, updating all forces/positions/torques/power in real time.

UI shows:

Real-time torque/power (live chart)

Real-time floater position/status (animated or tabular)

Adjustable inputs (possibly live, or at start of simulation)

Simulation controls (start, pause, stop, reset, step)

All other “summary” metrics (efficiency, total output, losses, etc.)

2. Upgrade the Backend Simulation Engine
a. Core Approach
Use a discrete time loop (dt = time step, e.g. 0.1s) in your simulation engine.

Each floater is an object with its own position, velocity, state (ascending, descending, filling, venting), forces acting on it.

At each timestep, update all floaters, sum their effects, update drivetrain, log the results.

b. Suggested Engine Skeleton (Pythonic OOP style)
python
Copy
Edit
# simulation/engine.py

class Floater:
    def __init__(self, id, position, velocity, state, ...):
        self.id = id
        self.position = position
        self.velocity = velocity
        self.state = state  # 'ascending', 'descending', etc.
        # ...other properties as needed

    def update(self, dt, params):
        # Update floater state/position/velocity based on physics
        pass

class KPPSystem:
    def __init__(self, params):
        self.floaters = [Floater(i, ...) for i in range(params['n_floaters'])]
        self.time = 0
        self.data_log = []
        # ...initialize all needed parameters

    def step(self, dt):
        # Update all floaters and collect system-wide metrics
        for floater in self.floaters:
            floater.update(dt, self.params)
        # Aggregate forces, compute torque, update system state, log data
        self.time += dt
        self.data_log.append(self.collect_state())

    def collect_state(self):
        # Return all relevant simulation outputs for logging/plotting
        return {
            'time': self.time,
            'torque': ...,
            'power': ...,
            'floater_states': [(f.position, f.velocity, f.state) for f in self.floaters],
            # ...more metrics
        }
The UI just calls step(dt) repeatedly and updates the display.

3. Refactor Your Flask Frontend
a. Real-Time Update Strategy
Use AJAX (fetch from /state every 0.2s) or WebSocket for live data.

UI “Start Simulation” launches the backend loop (in a background thread or with async).

b. Example: Flask+AJAX Loop
python
Copy
Edit
# app.py (simplified)

import threading, time
from flask import Flask, render_template, jsonify, request
from simulation.engine import KPPSystem

app = Flask(__name__)
sim = None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/start', methods=['POST'])
def start_sim():
    global sim
    params = ...  # parse from request.form
    sim = KPPSystem(params)
    def run_sim():
        while sim.time < params['total_time']:
            sim.step(params['dt'])
            time.sleep(params['dt'])
    threading.Thread(target=run_sim).start()
    return '', 204

@app.route('/state')
def state():
    # Return latest simulation state for plotting in browser
    if sim is None:
        return jsonify({})
    return jsonify(sim.data_log[-1])
4. UI/Frontend Recommendations
Show:

Live updating charts (torque, power vs time, e.g. Chart.js or Matplotlib via images)

Table/list of floater states (position, velocity, current force)

Controls: Start, Pause, Reset, Change Params

Start simple (update every 0.5s via AJAX), then add animation later if needed.

5. Remove the Old Static Simulation
Once real-time works, phase out the old single-shot simulation function.

Keep “summary” metrics calculated as aggregates from the real-time run.

6. Upgrade Steps in Sequence
Step 1: Extract floater physics into a Floater class if not done yet.
Step 2: Rewrite the simulation loop to step all floaters every dt, log results.
Step 3: Refactor Flask backend to manage a global simulation object, expose state via API.
Step 4: Build a JS loop in your HTML to fetch /state every 0.2-0.5 seconds and update the plots/UI.
Step 5: Test—compare to previous simulation to check correctness.
Step 6: Phase out the cycle-based calculation (optional, for code cleanliness).

7. Example Code Fragments
Floater update method (very simplified):
python
Copy
Edit
def update(self, dt, params):
    # Compute forces
    buoyancy = ...  # from self.position, params['water_density'], etc.
    drag = ...      # from self.velocity, params['drag_coeff'], etc.
    # Net acceleration (F = ma)
    net_force = buoyancy - drag - self.get_weight(params)
    acceleration = net_force / self.get_mass(params)
    self.velocity += acceleration * dt
    self.position += self.velocity * dt
    # Handle state transitions (at top/bottom)
    ...
Flask AJAX for UI (HTML/JS):
html
Copy
Edit
<script>
function update() {
  fetch('/state')
    .then(response => response.json())
    .then(data => {
      // Update charts/tables here
    });
  setTimeout(update, 500);
}
update();
</script>
Summary: What You Need to Do
Refactor backend into OOP per-floater simulation.

Expose live simulation state via API to frontend.

Remove/merge old cycle-based code.

Test with live updating UI (start with one plot and table).

Iterate and add features as needed (controls, adjustable parameters, better charts).

