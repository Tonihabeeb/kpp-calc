Stage 2 Upgrade: Real-Time Simulation
 Implementation Guide
 To meet the new requirements, restructure the simulator into clear modules and enhance both backend
 and frontend. The backend (Flask app) will handle the physics simulation (per-floater state, H1/H2 effects),
 manage parameter updates, and stream/log data. The frontend (HTML/JS with Chart.js) will display live
 charts and controls. The architecture is roughly: 
• 
• 
• 
• 
Simulation Engine (backend module) – encapsulates floaters and physical calculations. Each
 f
 loater is an object with attributes (position, velocity, buoyancy, drag). The engine’s update loop
 computes new states each time-step, applying H1/H2 effects (see below) and writing results to a
 log. 
Flask Server (
 app.py ) – defines routes: a streaming endpoint (
 /stream ) that yields JSON data
 via Server-Sent Events (SSE), REST endpoints (e.g. 
/set_params ) to update parameters, and an
 export endpoint (
 /download_csv ) for logged data. The SSE endpoint keeps a 
1
 2
 text/event
stream connection open to push new metrics to the browser . 
Data Logger – collects time-series (torque, power, efficiency, and each floater’s state). This can be a
 list or buffer in the simulation engine that is appended each time-step. 
Frontend (templates + static JS) – an HTML page (e.g. 
index.html ) that includes Chart.js charts
 (one per metric) and UI controls (sliders/numeric fields). JavaScript creates Chart.js line charts and
 opens an 
EventSource("/stream") to receive updates. On each SSE message, the JS callback
 parses the JSON and pushes new data into the charts, then calls 
chart.update() to refresh .
 Controls (e.g. 
3
 <input type="range"> ) have JS event handlers that send their current values to
 Flask (e.g. via 
fetch('/set_params', ...) ), causing the simulation engine to immediately
 adjust its variables. 
Each module’s responsibility is:- simulation.py (or similar): defines a 
Floater class and a simulation loop. The loop updates every
 f
 loater’s position, velocity, etc., incorporating H1 (nanobubble buoyancy effect) and H2 (thermal buoyancy).
 It also computes system-level outputs (torque, power, efficiency).- app.py: imports the simulation engine. Starts a background thread or uses the SSE generator to
 advance the simulation each loop. Defines Flask routes for streaming data, updating parameters, and
 exporting logs.- 
templates/index.html : includes 
<canvas> elements for charts and input elements for parameters.- 
static/js/ : contains Chart.js setup and SSE event handlers, plus AJAX functions for controls. 
Backend Changes (Simulation and Data Flow)
 1. 
Per-Floater State & H1/H2 Effects: In the simulation loop, represent each floater with an object
 tracking position, velocity, buoyancy force and drag. For example:
 1
class Floater:
 def __init__(self, ...):
 self.position = ...
 self.velocity = ...
 # other properties
 def update(self, dt, params):
 # Compute forces: buoyancy, drag, gravity, etc.
 # H1 effect: reduce water density by nanobubble fraction
 rho_water = base_density * (1- params.nanobubble_frac)
 # H2 effect: adjust density by temperature (thermal expansion)
 rho_water *= (1- params.thermal_expansion_coeff *
 (params.water_temp- params.ref_temp))
 buoyant_force = rho_water * volume * g
 # Update velocity/position using forces and dt
 # ...
 Here, H1 is modeled by lowering 
rho_water based on the nanobubble percentage, and H2 by a
 linear thermal expansion term (e.g. 
ρ_new = ρ_ref*(1 - α·ΔT) ). (You can adjust formulas as
 needed; the key is to recalc density and buoyancy in each step.) After updating each floater, the loop
 should compute net torque/power/efficiency and append all values to a shared log list for export.
 2. 
SSE Streaming Route (
 /stream ): Add a Flask route that returns a streaming response with MIME
 type 
text/event-stream . For example (in 
app.py ):
 + from flask import Response
 + import json
 + import time
 + @app.route('/stream')
 + def stream():
 +     def generate():
 +         while True:
 +             # Advance simulation by one time step
 +             sim.step(dt, params)  
+             # Collect output data
 +             data = {
 +                 'time':   sim.current_time,
 +                 'torque': sim.torque, 
+                 'power':  sim.power,
 +                 'eff':    sim.efficiency,
 +                 # optionally per-floater states
 +                 'floaters': [
 +                     {'pos': f.position, 'vel': f.velocity, 'buoy': 
f.buoyancy, 'drag': f.drag}
 +                     for f in sim.floaters
 2
+                 ]
 +             }
 +             # Send as SSE: prefix with "data: " and double newline
 +             yield f"data: {json.dumps(data)}\n\n"
 +             time.sleep(0.1)  # or appropriate time step
 +     # Return SSE response (keeps connection open)
 +     return Response(generate(), mimetype='text/event-stream')
 1
 This uses the pattern from
 2
 2
 . Each yielded line is sent to the browser’s EventSource. Note the 
time.sleep(…) controls update rate. The browser will automatically re-connect if needed. (Run
 Flask with 
threaded=True so streaming does not block other requests.)
 3. 
4. 
Parameter Update Endpoints: For each adjustable parameter (nanobubble %, heat-transfer rate,
 number of floaters, etc.), add a Flask route to receive updates. For example:
 from flask import request
 @app.route('/set_params', methods=['POST'])
 def set_params():
 data = request.get_json()
 # Update simulation parameters immediately
 sim.nanobubble_frac = float(data.get('nanobubble_frac',
 sim.nanobubble_frac))
 sim.thermal_expansion_coeff = float(data.get('thermal_coeff',
 sim.thermal_expansion_coeff))
 sim.num_floaters = int(data.get('num_floaters', sim.num_floaters))
 sim.air_pressure = float(data.get('air_pressure', sim.air_pressure))
 return ('', 204)
 In the frontend, JavaScript can call this endpoint (e.g. via 
fetch ) whenever a slider/input changes.
 The simulation engine should use these updated values on the next loop iteration, so effects are
 instantaneous.
 Logging and Export: Maintain a log of all output values (each timestep’s metrics and floater states).
 To allow downloading as CSV, add a route such as:
 + @app.route('/download_csv')
 + def download_csv():
 +     def generate_csv():
 +         # CSV header
 +         yield 'time,torque,power,efficiency\n'
 +         for entry in sim.log:  # sim.log holds time-series entries
 +             yield f"{entry.time},{entry.torque},{entry.power},
 {entry.efficiency}\n"
 +     # Stream CSV to client with proper headers
 4
 3
+     response = Response(generate_csv(), mimetype='text/csv')
 +     response.headers['Content-Disposition'] = 'attachment; 
filename=\"sim_data.csv\"'
 +     return response
 This uses Flask’s ability to stream a response in pieces
 4
 . The browser will prompt to download 
sim_data.csv . You can similarly provide a “View Data” page by rendering an HTML table from 
sim.log .
 Frontend Changes (Real-Time UI & Controls)
 1. 
Include Chart.js and Define Charts: In your template (e.g. 
Chart.js library and 
templates/index.html ), add the
 <canvas> elements for each chart (torque, power, efficiency, floater positions,
 etc.). For example:
 <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
 ...
 <canvas id="torqueChart" width="400" height="200"></canvas>
 <canvas id="powerChart" width="400" height="200"></canvas>
 <canvas id="effChart"
 width="400" height="200"></canvas>
 Then initialize each chart in JS. For instance:
 <script>
 // Torque chart
 const torqueCtx = document.getElementById('torqueChart').getContext('2d');
 const torqueChart = new Chart(torqueCtx, {
 type: 'line',
 data: { labels: [], datasets: [{ label: 'Torque', data: [] }] },
 options: { scales: { x: { title: { display: true, text: 'Time 
(s)' }}} }
 });
 // Similarly create powerChart, effChart...
 </script>
 2. 
data from 
/stream . In JavaScript:
 Connect to SSE and Update Charts in Real Time: Use the EventSource API to receive streaming
 <script>
 const source = new EventSource("/stream");
 source.onmessage = function(event) {
 const d = JSON.parse(event.data);
 // Add new data points to charts and update
 addData(torqueChart, d.time, d.torque);
 4
addData(powerChart, d.time, d.power);
 addData(effChart,
 d.time, d.eff);
 // Optionally update per-floater charts using d.floaters array
 3
 };
 // Helper to add data to a Chart.js chart (from )
 function addData(chart, label, value) {
 chart.data.labels.push(label);
 chart.data.datasets.forEach((ds) => ds.data.push(value));
 chart.update();
 }
 </script>
 Each time a message arrives, we parse the JSON and call 
addData() . This pushes the new point
 into the chart’s data array and calls 
chart.update()
 3
 , which causes Chart.js to redraw the line
 in real time. You may want to trim old data to avoid infinite growth.
 3. 
Display Per-Floater State: For detailed floater info, you can either create additional charts (e.g. one
 line per floater on a shared plot) or show values in a table. For example, a simple HTML table can be
 dynamically updated:
 <table id="floaterTable">
 <tr><th>Floater</th><th>Position</th><th>Velocity</th><th>Buoyancy</
 th><th>Drag</th></tr>
 <!-- JS can fill rows here -->
 </table>
 Then in the SSE handler:
 // Clear existing rows except header
 const table = document.getElementById('floaterTable');
 table.querySelectorAll('tr.floaterRow').forEach(row => row.remove());
 d.floaters.forEach((f, i) => {
 const row = table.insertRow();
 row.classList.add('floaterRow');
 row.insertCell().innerText = i+1;
 row.insertCell().innerText = f.pos.toFixed(2);
 row.insertCell().innerText = f.vel.toFixed(2);
 row.insertCell().innerText = f.buoy.toFixed(2);
 row.insertCell().innerText = f.drag.toFixed(2);
 });
 Alternatively, Chart.js supports multiple datasets, so you could plot each floater’s position on one
 chart (with tooltips showing values on hover).
 5
4. 
5. 
Add Control Inputs for Parameters: In the HTML, add range sliders or input fields for each
 adjustable parameter. For example:
 <label>Nanobubble %: <input type="range" id="nanobubbleSlider" min="0"
 max="100" value="0"></label>
 <label>Heat Coeff: <input type="number" id="heatCoeff" step="0.01"
 value="0.1"></label>
 <!-- more controls as needed -->
 Attach JS event listeners that POST the new values to Flask. E.g.:
 <script>
 document.getElementById('nanobubbleSlider').oninput = function(e) {
 fetch('/set_params', {
 method: 'POST',
 headers: {'Content-Type': 'application/json'},
 body: JSON.stringify({ nanobubble_frac: e.target.value/100.0 })
 });
 };
 document.getElementById('heatCoeff').onchange = function(e) {
 fetch('/set_params', {
 method: 'POST',
 headers: {'Content-Type': 'application/json'},
 body: JSON.stringify({ thermal_coeff: parseFloat(e.target.value) })
 });
 };
 // Add similar handlers for other inputs (num floaters, air pressure, etc.)
 </script>
 This way, when a user moves a slider or changes a field, the new value is sent to 
/set_params and
 immediately incorporated into the simulation loop.
 Export and View Data: Add a link or button in the UI to download the logged data:
 <a href="/download_csv" target="_blank">Download CSV</a>
 Clicking this will hit the 
/download_csv route and prompt the user to save 
can also create a separate page (e.g. 
sim_data.csv . You
 /data_table ) that renders the log in an HTML 
quick glance is needed.
 File and Line-Level Changes
 <table> if a
 Below are example patch snippets showing how you might integrate these upgrades into your project files.
 (Adjust file names and line numbers to your codebase.)
 6
--- a/app.py
 +++ b/app.py
 @@ -1,5 +1,7 @@
 from flask import Flask, render_template, Response, request
 +import json, time
 app = Flask(__name__)
# Import or initialize your simulation engine, e.g.:
 import simulation
 +sim = simulation.Simulator()
 +# Stream route for real-time data (SSE)
 +@app.route('/stream')
 +def stream():
 +    def event_stream():
 +        while True:
 +            sim.step(0.1)  # advance simulation by dt
 +            data = {
 +                'time': sim.t,
 +                'torque': sim.torque,
 +                'power': sim.power,
 +                'eff': sim.efficiency,
 +                'floaters': [
 +                    {'pos': f.position, 'vel': f.velocity, 'buoy': f.buoyancy, 
'drag': f.drag}
 +                    for f in sim.floaters
 +                ]
 +            }
 +            yield f"data: {json.dumps(data)}\n\n"
 +            time.sleep(0.1)
 +    return Response(event_stream(), mimetype='text/event-stream')
 +# Endpoint to update parameters at runtime
 +@app.route('/set_params', methods=['POST'])
 +def set_params():
 +    data = request.get_json()
 +    if 'nanobubble_frac' in data:
 +        sim.nanobubble_frac = float(data['nanobubble_frac'])
 +    if 'thermal_coeff' in data:
 +        sim.thermal_expansion_coeff = float(data['thermal_coeff'])
 +    if 'num_floaters' in data:
 +        sim.num_floaters = int(data['num_floaters'])
 +        sim.reset_floaters()
 +    if 'air_pressure' in data:
 +        sim.air_pressure = float(data['air_pressure'])
 +    return ('', 204)
 7
+# Export simulation log as CSV
 +@app.route('/download_csv')
 +def download_csv():
 +    def generate_csv():
 +        yield 'time,torque,power,efficiency\n'
 +        for entry in sim.log:
 +            yield f"{entry.time},{entry.torque},{entry.power},
 {entry.efficiency}\n"
 +    resp = Response(generate_csv(), mimetype='text/csv')
 +    resp.headers['Content-Disposition'] = 'attachment; 
filename=\"sim_data.csv\"'
 +    return resp
 These changes add the new endpoints and use the SSE pattern (note the 
text/event-stream MIME
 type)
 1
 updates.
 2
 . Make sure 
sim.step() calls your updated simulation logic including H1/H2 and per-floater
 In your template file (e.g. templates/index.html), integrate Chart.js and controls. Example additions:--- a/templates/index.html
 +++ b/templates/index.html
 @@ -20,6 +20,7 @@
 <head>
  <title>KPP Simulator Dashboard</title>
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
 +  <script src="https://cdnjs.cloudflare.com/ajax/libs/jquery/3.6.0/
 jquery.min.js"></script>
 </head>
 <body>
  <h1>KPP Simulation</h1>
 @@ -30,6 +31,20 @@
  <!-- Charts -->
  <canvas id="torqueChart" width="400" height="200"></canvas>
  <canvas id="powerChart"  width="400" height="200"></canvas>
  <canvas id="effChart"    width="400" height="200"></canvas>
 +  <!-- Floater state table -->
 +  <table id="floaterTable" border="1">
 +    <tr><th>Floater</th><th>Position</th><th>Velocity</th><th>Buoyancy</
 th><th>Drag</th></tr>
 +  </table>
 +  <!-- Controls -->
 +  <label>Nanobubble %:
 +    <input type="range" id="nanobubbleSlider" min="0" max="100" value="0">
 +  </label>
 8
+  <label>Heat Exp. Coeff:
 +    <input type="number" id="heatCoeff" step="0.01" value="0.1">
 +  </label>
 +  <label>Num Floaters:
 +    <input type="number" id="numFloaters" min="1" max="100" value="10">
 +  </label>
 +  <label>Air Pressure:
 +    <input type="number" id="airPressure" step="0.1" value="1.0">
 +  </label>
 <script>
 // Initialize charts
 const torqueChart = new Chart(
 document.getElementById('torqueChart'),
 { type: 'line',
 data: { labels: [], datasets: [{ label: 'Torque', data: [], borderColor:
 'red' }] },
 options: { responsive: true }
 }
 );
 const powerChart = new Chart(
 document.getElementById('powerChart'),
 { type: 'line',
 data: { labels: [], datasets: [{ label: 'Power', data: [], borderColor:
 'green' }] },
 options: { responsive: true }
 }
 );
 const effChart = new Chart(
 document.getElementById('effChart'),
 { type: 'line',
 data: { labels: [], datasets: [{ label: 'Efficiency', data: [],
 borderColor: 'blue' }] },
 options: { responsive: true }
 }
 );
 // Listen to SSE stream for live data updates
 const source = new EventSource("/stream");
 source.onmessage = function(event) {
 const d = JSON.parse(event.data);
 // Update charts (push new data and call chart.update())
 addData(torqueChart, d.time, d.torque);
 addData(powerChart, d.time, d.power);
 addData(effChart,
 d.time, d.eff);
 // Update floater table
 3
 9
$('#floaterTable tr.floaterRow').remove();
 d.floaters.forEach((f, i) => {
 $('#floaterTable').append(
 `<tr class="floaterRow"><td>${i+1}</td>` +
 `<td>${f.pos.toFixed(2)}</td><td>${f.vel.toFixed(2)}</td>` +
 `<td>${f.buoy.toFixed(2)}</td><td>${f.drag.toFixed(2)}</td></tr>`
 );
 });
 };
 // Helper to add a point to a Chart.js chart (as per Chart.js docs)
 function addData(chart, label, value) {
 chart.data.labels.push(label);
 chart.data.datasets.forEach((ds) => ds.data.push(value));
 chart.update();
 }
 // Parameter controls -> send to server on change
 $('#nanobubbleSlider').on('input', function() {
 fetch('/set_params', {
 method: 'POST',
 headers: {'Content-Type': 'application/json'},
 body: JSON.stringify({ nanobubble_frac: this.value / 100.0 })
 });
 });
 $('#heatCoeff').on('change', function() {
 fetch('/set_params', {
 method: 'POST',
 headers: {'Content-Type': 'application/json'},
 body: JSON.stringify({ thermal_coeff: parseFloat(this.value) })
 });
 });
 $('#numFloaters').on('change', function() {
 fetch('/set_params', {
 method: 'POST',
 headers: {'Content-Type': 'application/json'},
 body: JSON.stringify({ num_floaters: parseInt(this.value) })
 });
 });
 $('#airPressure').on('change', function() {
 fetch('/set_params', {
 method: 'POST',
 headers: {'Content-Type': 'application/json'},
 body: JSON.stringify({ air_pressure: parseFloat(this.value) })
 });
 });
 </script>
 3
 10
<!-- Download link for CSV log -->
 <p><a href="/download_csv" target="_blank">Download Simulation Data (CSV)</a></
 p>
 These additions wire the frontend controls to the backend and display live-updating charts. When new data
 arrives via SSE, each chart’s 
addData() is called and then 
3
 chart.update() is invoked (per Chart.js
 docs) to redraw the line. The per-floater table is reconstructed on each message. The sliders and inputs
 use jQuery to POST their values to 
/set_params , and the Flask route updates the simulation immediately.
 References: We use Flask’s SSE streaming (returning a 
1
 2
 Response with 
mimetype='text/event
stream' ) as recommended in examples . Chart.js is updated in real time by appending to its 
arrays and calling 
3
 data
 chart.update() . CSV export is implemented with a streaming response and
 proper 
4
 Content-Disposition header . All code above should be adapted into your existing Flask app
 (insert the added lines as shown) and will produce a fully functional, real-time dashboard as described. 
1
 python - How to implement server push in Flask framework? - Stack Overflow
 https://stackoverflow.com/questions/12232304/how-to-implement-server-push-in-flask-framework
 2
 Building a Real-time Dashboard with Flask and Svelte | TestDriven.io
 https://testdriven.io/blog/flask-svelte/
 3
 javascript - How to make chart js display values in real time? - Stack Overflow
 https://stackoverflow.com/questions/74280609/how-to-make-chart-js-display-values-in-real-time
 4
 python - Create and download a CSV file from a Flask view - Stack Overflow
 https://stackoverflow.com/questions/28011341/create-and-download-a-csv-file-from-a-flask-view
 11