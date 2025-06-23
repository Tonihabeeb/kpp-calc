Stage 1 Implementation Guide: Real-Time
 Simulation Loop Upgrade
 1. Modify the Simulation Engine (
 engine.py ). Replace the one-shot calculation with a time-stepping
 loop. Define a 
simulate function (or similar) that reads the user inputs and runs until a final time. For
 example:
 # engine.py
 def simulate(initial_state, params):
 dt = params.get('time_step', 0.1)
 total_time = params.get('total_time', 10.0)
 t = 0.0
 state = initial_state.copy()
 results = []
 while t <= total_time:
 # **Preserve existing physics calculations:** call the same force/torque 
functions as before
 force = compute_force(state, params)
 # existing function
 torque = compute_torque(state, force, params)
 power = compute_power(state, torque, params)
 # **Update floater state (example: simple Euler integration):**
 state.position += state.velocity * dt
 state.velocity += (force / state.mass) * dt
 # **Record outputs for this time step:**
 results.append({
 'time': t,
 'position': state.position,
 'velocity': state.velocity,
 'torque': torque,
 'power': power
 })
 t += dt
 1
return results
 • 
This loop increments time by 
functions (
 dt until 
total_time . At each step it calls the existing physics
 compute_force , 
compute_torque , etc.) unchanged and then updates the floater’s
 • 
• 
position/velocity. 
All original formulas and modules (e.g. buoyancy, drag, compressor torque, etc.) remain the same;
 simply invoke them inside the loop. 
Store or accumulate the time-series of outputs (
 position , 
velocity , 
lists or other structures. (Later we will stream or plot these.) 
torque , 
power , etc.) in
 This pattern (generator/function yielding data per time-step) is supported by Flask. Flask can stream a
 generator’s output by yielding pieces from an inner loop . For example, 
1
 one time-step at a time instead of returning one final result.
 2. Update the Flask Backend (
 simulate() could yield results
 app.py ). Add a route to start and stream the simulation. For instance, use
 Server-Sent Events (SSE): 
# app.py (Flask application)
 from flask import Flask, request, Response, render_template, jsonify
 import json
 from engine import simulate # import the simulation loop
 app = Flask(__name__)
 @app.route('/start_simulation', methods=['POST'])
 def start_simulation():
 # Parse all form inputs into params dictionary
 params = { key: float(val) for key, val in request.form.items() }
 # Optionally, pass these params to a template or use session as needed.
 return render_template('simulation.html', params=params)
 @app.route('/stream')
 def stream():
 # This route returns a streaming response (text/event-stream)
 # It can read parameters from query args if needed (or use the ones passed 
earlier)
 dt = float(request.args.get('dt', 0.1))
 total_time = float(request.args.get('T', 10.0))
 initial_state = {'position': 0.0, 'velocity': 0.0, 'mass': 1.0} # example 
initial state
 def generate():
 t = 0.0
 state = initial_state.copy()
 2
# Simulation loop: yields one JSON event per time step
 while t <= total_time:
 force = compute_force(state, {'dt': dt})
 torque = compute_torque(state, force, {'dt': dt})
 power = compute_power(state, torque, {'dt': dt})
 # Update state (Euler integration example)
 state['position'] += state['velocity'] * dt
 state['velocity'] += (force / state['mass']) * dt
 # Prepare JSON data for this time step
 data = {
 'time': t,
 'position': state['position'],
 'velocity': state['velocity'],
 'torque': torque,
 'power': power
 }
 yield f"data: {json.dumps(data)}\n\n"
 t += dt
 # Signal end of stream
 yield "data: [DONE]\n\n"
 # Return a Response that streams 'generate()' with the SSE MIME type
 return Response(generate(), mimetype='text/event-stream')
 • 
• 
In 
start_simulation , collect all form inputs via 
request.form and forward them as needed.
 (For example, you can pass them into the template or store them in a global/session.) Using 
request.form to retrieve POSTed form data is standard in Flask . 
The 
/stream route returns a 
2
 Response whose body is a generator. In each iteration it yields a
 line starting with 
data: and ending with 
\n\n
 • 
3
 , which conforms to the SSE format. The
 browser will keep this HTTP connection open and process each event as it arrives . 
Important: set 
3
 4
 3
 mimetype='text/event-stream' so that the client treats this as a live stream
 . For example, the Flask docs and community examples show 
return 
Response(generate(), mimetype='text/event-stream') when streaming . 
• 
Ensure Flask runs with threading enabled (e.g. 
4
 5
 app.run(threaded=True) ) so the streaming
 connection doesn’t block other requests . 
6
 3. Adapt the HTML Front-End. Modify the templates (e.g. 
index.html or 
simulation.html ) to add a
 “Start Simulation” button and client-side code to receive streamed data. For example:
 <!-- templates/simulation.html -->
 <form id="paramForm">
 <!-- existing input fields -->
 3
<input type="number" name="dt" placeholder="Time step (dt)"
 value="{{ params.get('dt',0.1) }}">
 <input type="number" name="T" placeholder="Total time (T)"
 value="{{ params.get('T',10) }}">
 <!-- ... other inputs ... -->
 <button type="button" id="startBtn">Start Simulation</button>
 </form>
 <div id="results">
 <!-- place to show dynamic output (charts, logs, etc.) -->
 </div>
 <script>
 // When the user clicks Start, open an SSE connection to '/stream'
 document.getElementById('startBtn').addEventListener('click', function() {
 // Option 1: send form parameters via query string
 const dt = document.querySelector('input[name="dt"]').value;
 const T = document.querySelector('input[name="T"]').value;
 const url = `/stream?dt=${dt}&T=${T}`;
 // Open EventSource for server-sent events
 const source = new EventSource(url);
 source.onmessage = function(event) {
 if (event.data === "[DONE]") {
 source.close();
 return;
 }
 const data = JSON.parse(event.data);
 // **Update the page with new data:** e.g., append to a log or update 
charts
 const log = document.getElementById('results');
 log.innerHTML += `<p>t=${data.time.toFixed(2)}s: pos=$
 {data.position.toFixed(2)}, vel=${data.velocity.toFixed(2)}, torque=$
 {data.torque.toFixed(2)}</p>`;
 // (Optionally update plots here using data.torque, data.power, etc.)
 };
 });
 </script>
 • 
• 
• 
Start Button: We changed the start button to type="button" to prevent form submission and handle
 it in JavaScript. When clicked, it reads form values and constructs an EventSource. 
EventSource: This JavaScript API opens a persistent connection to 
/stream . Each time the server
 yields a line 
data: {...} , the 
onmessage handler runs. (This is identical to examples in MDN
 and StackOverflow .) 
7
 8
 Updating Results: In the handler we parse 
event.data (JSON) and update the DOM. Here we
 simply append lines of text for torque, power, etc. In a real app, you’d typically update a chart: for
 example, send the data to a client-side plotting library or refresh a Matplotlib-generated image. 
4
Ending the Stream: When the server yields 
• 
"[DONE]" , we close the EventSource. This mimics the
 SSE end-of-stream pattern .
 9
 7
 If you prefer using pure HTML (no JS libraries), you can also embed a hidden element or use 
swap="outerHTML"> with 
<div hx
10
 htmx as in the example . But using plain EventSource/JS as above is
 straightforward and built-in.
 4. Integrate and Test in VS Code. Open your project in VS Code and apply the changes:
 • 
• 
• 
• 
Install Dependencies: Ensure you have Flask and Matplotlib installed. For example, in the
 integrated terminal run: 
pip install Flask matplotlib
 Edit Files:
 engine.py: Add the 
simulate function with the time loop as shown above. Import and reuse your
 existing physics functions (no need to rewrite formulas). 
app.py: Add the new routes (
 /start_simulation and 
call 
simulate in a streaming response. Use 
/stream ) or modify an existing route to
 flask.Response(..., mimetype='text/event
stream') as above
 4
 11
 . Also ensure 
app.run(..., threaded=True) in the 
if __name__ == '__main__': block to allow concurrent streaming . 
6
 • 
Templates: Update your HTML (e.g. 
templates/index.html or 
templates/
 simulation.html ) to include the Start button and EventSource script. Insert a 
<div> or similar
 element where you will display live output. 
• 
Run the App: In VS Code’s terminal, start the Flask app. For example: 
export FLASK_APP=app.py
 flask run
 or simply 
python app.py . Open a browser to 
http://localhost:5000 , fill in the form, and
 click Start Simulation. You should see live updates appearing as the simulation runs.
 Throughout development, use print/log statements or Flask’s debugging output to verify that your loop is
 iterating and sending data. Check the browser console and network tab: you should see a GET to 
that stays open and streams multiple event packets.
 /stream
 5. (Optional) Next Steps: After Stage 1, you can enhance the simulator. For example: - Real-time Plotting:
 Replace text logs with live charts. You might use a JS chart library (e.g. Chart.js or D3) to animate torque/
 power over time in the browser. Alternatively, generate Matplotlib plots on the server and update them
 periodically (but a JavaScript solution is smoother).- Pause/Resume: Add controls to pause or resume the simulation, which involves keeping the state on the
 server and reusing it.- Advanced Integration: Implement a more accurate integrator (e.g. Runge–Kutta) if needed, or break
 5
physics into smaller sub-modules (current loops, wind loads, etc.) to be added in Stage 2.- Improved UI: Use WebSockets (Flask-SocketIO) for bidirectional real-time interaction if you need user
 inputs during the run. 
Each of these could be a subsequent stage. For now, Stage 1 ensures the core loop and streaming interface
 work, preserving all existing physics calculations.
 Sources: Flask supports streaming generators via 
4
 1
 Response(generate(), mimetype='text/event
stream') , and browsers can consume SSE streams with JavaScript’s 
EventSource interface
 7
 . These patterns guide the implementation above. 
3
 1
 Streaming Contents — Flask Documentation (3.1.x)
 https://flask.palletsprojects.com/en/stable/patterns/streaming/
 2
 Python Flask - Request Object - GeeksforGeeks
 https://www.geeksforgeeks.org/python/python-flask-request-object/
 3
 6
 7
 11
 python - How to implement server push in Flask framework? - Stack Overflow
 https://stackoverflow.com/questions/12232304/how-to-implement-server-push-in-flask-framework
 4
 9
 Simulating Real-Time Chats using Flask's Server-Sent Events | Hippocampus's Garden
 https://hippocampus-garden.com/flask_sse/
 5
 10
 Streaming data from Flask to HTMX using Server-Side Events (SSE) | mathspp
 https://mathspp.com/blog/streaming-data-from-flask-to-htmx-using-server-side-events
 8
 Using server-sent events - Web APIs | MDN
 https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events/Using_server-sent_events
 6