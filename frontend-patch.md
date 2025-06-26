Kinetic Power Plant (KPP) Simulator Patch &
Integration Plan
1. Frontend Modifications (HTML/JavaScript)
Normalize Control Elements & Naming: Refactor all input, select, and button elements in the
HTML to use consistent snake_case identifiers for parameters. For example, rename an input ID like
airPressureInput to air_pressure and a slider for nanobubble percentage to
nanobubble_frac . Ensure the HTML name attributes (if used in forms) match these snake_case
parameter names. This uniform naming will simplify binding and reduce mistakes in parameter
mapping. All controls (sliders, toggles, buttons) should be organized in a logical form structure with
clear labels. For instance, add a labeled checkbox for the Pulse Mode ( <input type="checkbox"
id="pulse_enabled"> ) to toggle H3, and sliders/fields for Air Pressure, Nanobubble Fraction,
Thermal Coefficient (H2 heat assist factor), etc., using snake_case IDs.
Unified Event Binding via updateParam() : In the main JavaScript (e.g. main.js or a script
section), create a single function updateParam(param, value) that sends the new parameter
value to the backend. This function should issue a fetch('/set_params', {...}) POST request
with a JSON payload of { param: value } . For example:
function updateParam(paramName, value) {
fetch('/set_params', {
method: 'POST',
headers: { 'Content-Type': 'application/json' },
body: JSON.stringify({ [paramName]: value })
}).catch(err => console.error('Param update failed:', err));
}
Then, attach all UI controls to this function. Use event listeners (e.g. oninput for sliders, onchange for
number fields, onclick for buttons) to call updateParam with the appropriate param name. This
replaces repetitive inline handlers with a single mechanism . For instance, for a nanobubble
percentage slider with ID nanobubble_frac , do:
document.getElementById('nanobubble_frac').oninput = (e) => {
updateParam('nanobubble_frac', parseFloat(e.target.value));
};
Similarly, bind the pulse mode toggle:
•
•
1 2
1
document.getElementById('pulse_enabled').onchange = (e) => {
updateParam('pulse_enabled', e.target.checked);
};
This unified approach ensures all controls consistently invoke the same backend update route . It also
makes maintenance easier, since adding a new control only requires giving it the correct ID and adding one
listener line.
Dynamic Chart Updates with SSE: Use Chart.js to display live simulation data and update it in realtime
via Server-Sent Events (SSE). Ensure the HTML includes <canvas> elements for each chart
(e.g. torqueChart , powerChart , effChart , etc.) and that Chart.js is imported. In the JS
initialization, create Chart.js line charts for each metric, with empty datasets initially. For example,
initialize a torque chart with:
const ctx = document.getElementById('torqueChart').getContext('2d');
const torqueChart = new Chart(ctx, {
type: 'line',
data: { labels: [], datasets: [{ label: 'Torque (Nm)', data: [] }] },
options: { scales: { x: { title: { display: true, text: 'Time (s)' } } } }
});
// Similarly initialize powerChart, effChart, etc.
Next, open an SSE connection to the backend stream:
const source = new EventSource('/stream');
source.onmessage = function(event) {
const d = JSON.parse(event.data);
// Update charts with new data point:
addData(torqueChart, d.time, d.torque);
addData(powerChart, d.time, d.power);
addData(effChart, d.time, d.efficiency);
// ... (handle floaters data separately below)
};
Here addData is a helper that pushes a new data point into a Chart.js chart and calls chart.update()
. For example:
function addData(chart, label, value) {
chart.data.labels.push(label);
chart.data.datasets[0].data.push(value);
chart.update();
}
3
•
4 5
2
This will dynamically inject the incoming values into the charts on each SSE message, animating the lines in
real-time . Make sure to limit the length of stored data (e.g. remove oldest points) to prevent memory
bloat during long runs.
Floater Data Table Alignment: If the frontend includes a table or list of per-floater data (e.g.
showing each floater’s forces or state), update its rendering logic to match the new backend payload
structure. The SSE d.floaters array will contain objects with keys like buoyancy , drag ,
net_force , and pulse_force for each floater (in addition to position/velocity if provided). First,
extend the HTML table header to include Net Force and Pulse Force columns, alongside existing
ones for Buoyancy and Drag. Then, in the SSE handler, after updating the charts, also refresh the
floater table: clear the old rows and populate a new row for each floater in d.floaters . For
example:
const table = document.getElementById('floaterTable');
// Remove old rows:
table.querySelectorAll('tr.floaterRow').forEach(row => row.remove());
// Add a row for each floater:
d.floaters.forEach((f, i) => {
const row = table.insertRow();
row.className = 'floaterRow';
row.insertCell().innerText = i + 1; // Floater index
row.insertCell().innerText = f.buoyancy.toFixed(2); // Buoyancy (N)
row.insertCell().innerText = f.drag.toFixed(2); // Drag (N)
row.insertCell().innerText = f.net_force.toFixed(2); // Net Force (N)
row.insertCell().innerText = f.pulse_force.toFixed(2); // Pulse Force
(N)
});
This ensures the UI displays per-floater forces consistently with what the backend sends (initially, floaters
had buoy and drag only ; after the patch they will include net_force and pulse_force ).
Verify that the table updates at the same SSE frequency as the charts, giving the user a real-time view of
each floater’s state.
SSE Failure Fallback: Implement a fallback UI to handle SSE disconnections or errors. While
browsers will automatically attempt to reconnect to an EventSource, it’s good to inform the user if
updates stop. Use the EventSource.onopen , onerror , or onclose callbacks. For example,
show a status indicator (like a small green dot for “Live” that turns red on disconnect) or an alert
message if the SSE stream closes unexpectedly. For instance:
source.onerror = function(e) {
console.error("SSE connection error", e);
document.getElementById('statusIndicator').innerText = "Disconnected";
// Optionally, attempt to reconnect or prompt user to reload
};
6
•
7 8
•
3
Add a corresponding element in HTML (like <span id="statusIndicator" class="text-sm textred-
600"></span> initially set to “Live”). This way, if the backend or network fails, the UI will clearly
indicate that real-time updates have stopped and may suggest refreshing the page. This improves
robustness of the user experience in case of server issues or connectivity loss.
2. Backend Patching (Python/Flask)
Parameter Schema Definition: Introduce a PARAM_SCHEMA in the Flask backend (e.g. in
simulation.py or a config module) that defines all expected input parameters along with their
types, units, and valid ranges. This could be a dictionary such as:
PARAM_SCHEMA = {
"air_pressure": {"type": float, "unit": "bar", "min": 0.0, "max":
10.0},
"nanobubble_frac":{"type": float, "unit": "%", "min": 0.0, "max":
100.0},
"thermal_coeff": {"type": float, "unit": "–", "min": 0.0, "max": 1.0},
"num_floaters": {"type": int, "unit": "count", "min": 1, "max": 100},
"pulse_enabled": {"type": bool, "unit": "bool" },
// ... any other parameters
}
(Here thermal_coeff represents the thermal boost factor in an abstract unit; adjust naming if needed,
e.g. thermal_expansion_coeff .) This schema will serve as the authoritative reference for what
parameters the frontend can set. Include any new parameters introduced for H1/H2 (nanobubble fraction,
thermal expansion factor) and H3 (pulse mode toggle), as well as existing ones (e.g. floater dimensions,
water depth, drag coefficient, etc. if present). Defining types and ranges helps with validation and prevents
out-of-bounds or invalid inputs from disrupting the simulation.
Enhanced /set_params Route: Update the Flask route that handles parameter updates (POST /
set_params ) to use the above schema for validation. This route should parse
request.get_json() to get a dict of incoming parameters. For each key in the payload, verify it
is a recognized parameter in PARAM_SCHEMA . Then, convert and validate the value: e.g., check type
(cast to float/int/bool as specified) and range. If a value is out of allowed range or of wrong type,
respond with an error (HTTP 400 and a message indicating which param is invalid). Only after
validation, apply the change to the simulation state. For example:
@app.route('/set_params', methods=['POST'])
def set_params():
data = request.get_json() or {}
for param, val in data.items():
if param not in PARAM_SCHEMA:
return jsonify({"error": f"Unknown parameter '{param}'"}), 400
schema = PARAM_SCHEMA[param]
# Type conversion
•
•
4
try:
if schema["type"] is float:
val_converted = float(val)
elif schema["type"] is int:
val_converted = int(val)
elif schema["type"] is bool:
# Interpret "true"/"false" strings or booleans
val_converted = True if str(val).lower() in ("true", "1") else
False
except ValueError:
return jsonify({"error": f"Invalid type for {param}"}), 400
# Range check
if "min" in schema and val_converted < schema["min"] or \
"max" in schema and val_converted > schema["max"]:
return jsonify({"error": f"Value for {param} out of range"}), 400
# Passed validation – apply to simulation
sim.set_param(param, val_converted) # or set attribute directly
return ('', 204)
This robust handling ensures that only valid, safe values reach the simulation. The simulation engine’s
internal state (or a parameters object) should be updated accordingly. For instance, if using direct
attributes, apply like sim.air_pressure = val_converted for each known key . Note that in
the existing code, parameters might have been updated without checks ; we are now adding proper
validation around that.
Consistent Parameter Propagation: Ensure that the parameter names used in the Flask app match
exactly those expected in the simulation engine. Normalize any inconsistencies in casing or spelling.
For example, if the simulation code expects sim.air_pressure and sim.nanobubble_frac ,
the /set_params route should use those exact names (as done above). The patch provided in the
blueprint already uses snake_case keys like nanobubble_frac , thermal_coeff ,
num_floaters , air_pressure . Audit the simulation code for any mismatches – e.g., if the
engine uses self.pulseEnabled or self.pulse_enable for H3, standardize it to
pulse_enabled everywhere. Update attribute names in the simulation class if necessary to
maintain consistency (this might involve minor changes in the physics update loop to use the new
names). After this, the chain is uniform: UI -> JSON -> Flask -> Simulation all referring to parameters
by one canonical name each.
Refactor SSE /stream Output: Modify the streaming endpoint (Server-Sent Events route) to send
a more comprehensive data structure each update. The SSE generator currently likely yields JSON
with time, torque, etc., and an array of floaters with a couple of fields . We will extend this.
Include a timestamp field (if not present) – using simulation time is fine (e.g. time in seconds). For
torque breakdown, add fields that decompose the sources of torque. For example, if not already
tracked, compute: torque_buoyant (torque from buoyant upward forces minus gravity on
descending side), torque_drag (the opposing torque from drag forces), and
torque_generator (the load torque from the generator/flywheel). These can be packaged under
a torque_components object in the output for clarity. For instance:
9 10
11
•
10
•
7 8
5
data = {
"time": sim.time,
"torque": sim.torque_total, # total net torque on the shaft
"power": sim.power_output, # current generator power (W)
"efficiency": sim.efficiency, # overall system efficiency (%)
"torque_components": {
"buoyant": sim.torque_buoyant,
"drag": sim.torque_drag,
"generator": sim.torque_generator
},
"floaters": [
{
"buoyancy": f.buoyancy,
"drag": f.drag,
"net_force": f.net_force,
"pulse_force": f.pulse_force
} for f in sim.floaters
]
}
yield "data: " + json.dumps(data) + "\n\n"
This structure ensures that each SSE message contains a rich snapshot of the system state. The floaters
list now has explicitly named fields: buoyancy (upward Archimedes force in N), drag (hydrodynamic drag in
N), net_force (the net force on that floater, e.g. buoyancy minus weight minus drag), and pulse_force (any
additional force from active air injection, if applicable). These correspond to the columns we updated on the
frontend. The main section includes overall torque and power for the system, and efficiency which can
represent instantaneous efficiency (output power / input power). The new torque_components helps in
debugging and analysis, showing how the total torque is composed. Make sure these fields are computed
in the simulation loop (see section 3). If certain components are not readily available, you can calculate
them on the fly (e.g., sim.torque_buoyant = … inside the physics update, etc.) before streaming. The
SSE output should continue to stream at a steady interval (e.g. every 100 ms as before), using yield with
the proper SSE format (as in the existing code) .
Drivetrain & Pneumatic Efficiency Metrics: Augment the simulation to calculate efficiency metrics
for subsystems and include them in the SSE output. Specifically, compute drivetrain efficiency and
pneumatic efficiency and add them to the data stream (and logs). Drivetrain efficiency could be
defined as the ratio of mechanical power delivered to the generator vs. mechanical power available
from net buoyancy (after drag losses). Pneumatic efficiency could be the ratio of the buoyant work
extracted from floaters vs. the compressor energy input to inject the air. Implementing these may
require tracking cumulative energies: for example, integrate generator power over time (output
energy) and compressor motor power over time (input energy). However, for real-time output, you
might output instantaneous values or running averages. For now, you could approximate: if
sim.power is generator electrical power and sim.compressor_power is the current
compressor power draw (if available), then drivetrain_eff = sim.power / (sim.power +
losses) or a fixed value if assuming generator efficiency, etc., and pneumatic_eff =
(buoyant_force * floater_displacement_speed) / compressor_power at that moment,
12
•
6
for instance. Since detailed implementation depends on what the simulation already computes, we
mainly ensure placeholders are there. For example, include data["eff_drivetrain"] =
sim.eff_drivetrain and data["eff_pneumatic"] = sim.eff_pneumatic in the SSE JSON.
These can be calculated in the simulation loop (section 3 discusses the physics changes). The goal is
to have these fields available so the frontend (or developer) can observe efficiency of these modules
in real time. If such values are not yet calculated, initially set them to something like
sim.eff_drivetrain = sim.efficiency (overall efficiency) and sim.eff_pneumatic =
sim.efficiency or 1.0 as placeholders, then refine in the physics engine. Including the fields now
ensures the output schema is forward-compatible with more detailed calculations.
/get_output_schema Debug Endpoint: Add a new Flask route /get_output_schema that
returns (in JSON format) the structure of the output data. This will help frontend developers or
testers understand what fields to expect in the SSE stream. The route can construct a representative
schema dictionary (or simply describe the keys and types). For example:
@app.route('/get_output_schema', methods=['GET'])
def get_output_schema():
schema = {
"time": "float (s)",
"torque": "float (N·m, net torque)",
"power": "float (W, generator output)",
"efficiency": "float (%, overall system efficiency)",
"torque_components": {
"buoyant": "float (N·m, torque from buoyancy/gravity)",
"drag": "float (N·m, torque lost to drag)",
"generator": "float (N·m, torque from generator load)"
},
"floaters": [{
"buoyancy": "float (N)",
"drag": "float (N)",
"net_force": "float (N)",
"pulse_force": "float (N)"
}],
"eff_drivetrain": "float (%, efficiency of drivetrain)",
"eff_pneumatic": "float (%, efficiency of pneumatic system)"
}
return jsonify(schema)
}
This is an example; adjust based on the actual fields you implement. Essentially, hitting this endpoint should
return a JSON describing each field’s name and meaning (and units). This is extremely helpful for debugging
and for the frontend to dynamically adjust if needed. It also serves as up-to-date documentation of the
streaming data format. Since this is a read-only introspection, it can be open to GET requests without issue.
•
7
3. Realism and Force Modeling Enhancements
Enforce Physical Limits: Modify the physics engine ( simulation.py or engine.py ) to respect
fundamental physical limits, ensuring the simulation does not produce non-physical results. For
buoyant force, apply Archimedes’ principle strictly: . The code likely
already does this for fully submerged floaters , but make sure it cannot exceed that (e.g., if any
calculation tries to amplify buoyancy beyond what displaced water allows, cap it). Similarly, ensure
torque and energy outputs remain within realistic bounds. Add a check on each cycle for energy
conservation: the net mechanical energy output should not exceed the energy put in by the
compressor plus potential energy differences. If it does, log a warning or error (this could indicate a
bug or an unrealistic condition). The feasibility analysis shows that without special hypotheses, the
KPP cannot output net energy because compressing the air costs more than the buoyant work
recovered . Our simulator should reflect this reality: for example, if the user sets extreme values
(e.g., very high nanobubble fraction or thermal boost), ensure the simulation doesn’t yield efficiency
> 100% over a cycle. If it does, flag it in the logs (the user might be attempting a scenario that
violates energy conservation). Also enforce any obvious bounds like non-negative pressures,
proportions ≤100%, etc., in the physics calculations (these tie into the input validation in the Flask
layer, but double-checking in the engine adds safety).
Accurate Drag Modeling: Replace any simplified or placeholder drag calculation with the standard
drag equation: . In the simulation code, where each floater’s velocity is
updated, compute drag force using this formula. Ensure that you have reasonable values for drag
coefficient and cross-sectional area of a floater (these could be parameterized or computed
from floater geometry). Apply drag in the opposite direction of motion (if a floater is moving upward,
drag force is downward, etc.). This will likely reduce the net force on fast-moving floaters and is
necessary for realism – previously, if a linear or constant drag was used, the dynamics would be off.
Test the effect: the floaters should reach a terminal velocity when buoyant force equals drag +
weight for ascending floaters. If needed, include a Cd parameter in PARAM_SCHEMA so it can be
adjusted via UI. This change will cause floaters with higher speeds to experience significantly more
resistance, in line with real fluid dynamics.
Integrate H1 (Nanobubble Drag Reduction): Implement the effect of Hypothesis 1 (H1) –
nanobubble-induced drag and density reduction – in the physics engine. H1 posits that seeding
water with micro/nanobubbles reduces its density and the drag on objects moving through it
. In the simulation, interpret the parameter nanobubble_frac (perhaps representing the void
fraction percentage of gas in water, or an index of bubble concentration) to adjust fluid properties.
Two primary effects to model:
Reduced Effective Density: Decrease the water density on the descending side (where bubbles
would lighten the water) proportional to nanobubble_frac . For example, if
nanobubble_frac = 0.10 (10%), you might reduce water density by 10% on that side. You can
implement this by having separate densities for the ascending vs descending sides, or simpler: apply
density reduction to drag/buoyancy calculations for sinking floaters only. A straightforward approach
in code:
•
Fbuoyant = ρwater ⋅ Vsubmerged ⋅ g
13
14
•
F = drag C ρ Av 2
1
d water
2 13
Cd A
•
15
16
•
8
base_rho = WATER_DENSITY # normal density (e.g. 1000 kg/m^3)
effective_rho = base_rho * (1 - params.nanobubble_frac)
Then use effective_rho for the drag and buoyancy of descending (heavy) floaters. This models
the water being “lighter” due to bubbles , thus less buoyant force opposing the weight of a
sinking floater and lower drag.
Reduced Drag Coefficient: Alternatively or additionally, simulate drag reduction by reducing the
drag coefficient when nanobubbles are present. Studies on microbubble drag reduction show
that enough bubbles can disrupt boundary layers and reduce friction by up to ~50% at high
concentrations . You could incorporate this as:
effective_Cd = base_Cd * (1 - drag_reduction_factor *
params.nanobubble_frac)
where drag_reduction_factor might be, say, 0.5 if 100% nanobubble setting cuts drag in half.
This is a simplification, but it provides a tunable way to simulate H1’s effect on drag. Use
effective_Cd in the drag equation for floaters in water with bubbles (likely the descending side).
These changes should be made in the floater update logic. For example, if you have a Floater.update()
method, it can check the floater’s current position or which side of the loop it’s on, and apply the density/
drag adjustments accordingly . The result will be that heavy (water-filled) floaters experience less
upward buoyant force opposing their descent and less drag, thereby descending more easily – which
matches the intended benefit of H1 . Make sure to only apply the reduction where appropriate (you
might decide that ascending side should not be affected or is affected differently; the hypothesis primarily
targets aiding the descending side). The nanobubble_frac parameter should be adjustable via the
frontend (we’ve already provided a slider for it), so the simulation should respond in real time: try setting it
to 0 vs a high value and observe that the net torque increases when nanobubbles are “on” (since drag and
opposing buoyancy are reduced).
Incorporate H2 (Thermal Boost via Near-Isothermal Expansion): Implement Hypothesis 2 (H2) in
the simulation by boosting the buoyant force when air expands in the floater with heat input. In
practical terms, H2 means the injected air does more work because it absorbs ambient heat, not
cooling as much during expansion . To simulate this, increase the effective buoyancy force for
ascending floaters when H2 is enabled. One way is to reduce the density of the air inside the floater
less than it would normally drop. However, since our simulation likely doesn’t model detailed
thermodynamics, we can approximate H2 as an “extra buoyancy” factor. For example, have a
parameter like thermal_coeff (or reuse thermal_coeff from Stage 2 code) that scales
buoyant force on the ascending side. If normally a floater’s buoyant force is , with thermal
boost we might say:
buoyant_force = rho_water * V * g * (1 + params.thermal_coeff)
where thermal_coeff is 0 for no boost and, say, 0.1 for a 10% buoyancy increase due to thermal
energy. Essentially this is injecting extra energy equivalent to heating the air (making it expand more
17 18
•
Cd
19
20 21
22 23
•
24
ρwaterV g
9
or stay hotter) which yields more force. In the Stage 2 guide, a more detailed approach was to adjust
water density by temperature difference , but since we may not simulate water temperature, we
can treat thermal_coeff as a direct boost factor. If the simulation already tracks air temperature
or expansion, tie thermal_coeff into that calculation. Otherwise, the above direct modification is
a reasonable stand-in: e.g., if H2 is toggled on, use a preset boost (the user might input a
percentage). Make sure this only applies when floaters are ascending (air-filled) since that’s when
expansion does work. The result is that with H2 on, ascending floaters generate more force/torque
than they normally would, effectively pulling in some ambient heat energy – but remember, this is
still subject to overall efficiency checks (if you boost buoyancy too much without accounting for a
heat source, you could violate energy balance – consider logging a warning if thermal_coeff is
set extremely high). As part of this, you might maintain a reference water temperature and current
water temperature in the model, but unless needed, a simpler approach is fine.
Synchronize Floater Fill/Vent with Compressor & Tank Logic: Add a more realistic model for air
availability. The simulator should track the state of the compressed air tank and the compressor’s
output, and only inject air into a floater if sufficient pressure is available. Implement a variable like
sim.air_tank_pressure or sim.air_reserve that represents the current pressure or volume
of compressed air ready for injection. Each time a floater is at the bottom and needs to be filled with
air, check this value:
Determine a threshold for injection (e.g., if air_tank_pressure <
required_pressure_to_inject , then the floater cannot be filled yet).
If pressure is adequate, proceed to inject: set that floater’s state to buoyant (air-filled), and
immediately reduce the air_tank_pressure to simulate using some air. You might reduce it by a
fixed amount or by an amount proportional to floater volume.
If pressure is too low, delay the injection: let the floater continue in its heavy (water-filled) state
instead of becoming buoyant. This means the cycle might have a gap (one floater that was supposed
to rise stays heavy and goes around again). Log an event in this case (e.g., "Skipping floater
fill at time X: insufficient pressure" ). This reflects reality – the compressor couldn’t
keep up, which was identified as a likely issue in the real KPP .
Continuously simulate the compressor adding pressure to the tank over time. For example, have a
compressor capacity parameter (perhaps the user can set compressor flow rate). Each simulation
step, increase air_tank_pressure by a small amount to simulate the compressor working. If the
compressor is off or pulse mode dictates it only runs at certain times, incorporate that logic too.
This synchronization ensures that back-to-back floater injections are only possible if the compressor (and
any intermediate storage) can supply the air. It will result in more realistic behavior: if the user tries to run
the machine too fast or with too many floaters without sufficient compressor power, not every floater will
get filled. Over time, the system might reach a steady state where, say, only every second floater gets air (if
compressor is undersized). This is an important part of realism and will likely reveal why the claimed output
is hard to achieve without the hypotheses. All of this logic can reside in the main simulation loop or in a
dedicated compressor/tank module. As a simple integration, you might maintain
sim.air_tank_pressure and update it each sim.step() . Floater objects could have a state (e.g.,
25
•
•
•
•
26
•
10
f.filled boolean) that only flips to true (air-filled) if pressure was available; otherwise stays false (waterfilled).
Clutch, Flywheel, and Generator Timing (Pulse Mode): Review and update how torque and forces
are applied in the simulation when H3 (pulse-and-coast mode) is enabled. The simulator should have
a concept of a clutch that can engage or disengage the generator/flywheel from the main shaft.
Implement a boolean flag sim.clutch_engaged that is toggled according to pulse_enabled
logic or a timing schedule. For example, if pulse_enabled is true, you might run a cycle where for
X seconds the clutch is disengaged (generator produces no resistive torque), then for Y seconds it’s
engaged (generator applies load). This can be a simple loop using simulation time to switch state, or
respond to events (like a number of floaters accumulated on the ascending side). The algorithm
blueprint suggests a fixed timing or event-based strategy :
When clutch_engaged = False (coast phase), the generator torque should be 0, allowing the
chain and flywheel to accelerate freely under the net force of the floaters. In the simulation, you
implement this by not applying generator resistance in the equations of motion. Practically, if you
have a variable for generator torque, set sim.torque_generator = 0 during coast.
When clutch_engaged = True (pulse phase), apply the generator load torque. This could be a
constant resistive torque or one proportional to generator speed/power if a more detailed model
exists. In our case, you might simply restore the normal calculation of generator torque (which could
be something like - generator_load * angular_velocity or a PID controlling speed). The
important part is that the simulation sees a sudden increase in opposing torque when the clutch
engages.
If a flywheel is part of the model (perhaps represented by an increased moment of inertia on the
system), ensure that it remains connected to the chain in both phases (unless you simulate the
flywheel itself being isolated, but typically the clutch in KPP disengages the generator, not the
flywheel). The flywheel will store kinetic energy during the coast (speeding up) and then give some
back during the pulse (slowing down as it helps drive the generator) . You should see this in
the simulation as a smaller drop in speed when the clutch engages, compared to no flywheel.
To implement the timing, you could use a simple counter or use the simulation time: e.g., if
(sim.time // (X+Y)) < X then disengaged, else engaged, in a repeating cycle. Or toggle based on
number of floaters: e.g., disengage when a certain number of heavy floaters are about to pull (to let them
gain speed) and engage when buoyant floaters reach peak torque. For now, a fixed period might be simpler.
Provide the period or duty cycle as parameters (could add pulse_on_duration and
pulse_off_duration to the schema for fine-tuning).
After implementing, ensure that when pulse_enabled is off (normal mode), sim.clutch_engaged
stays True continuously (generator always engaged, the default continuous mode). And when
pulse_enabled is on, the torque in the system alternates accordingly. Check that net torque and chain
speed behave plausibly: in coast phase, speed should increase (net positive torque accelerating the system);
in pulse phase, speed will drop or stabilize as generator extracts energy. Verify the floaters' net forces still
contribute correctly: the net force per floater doesn’t change with clutch state, but the acceleration of the
system does since the resisting torque changes.
Additionally, update logging (see next section) to mark when clutch engages/disengages if possible. For
instance, log a message "Clutch disengaged at t=12.0s, entering coast phase" and
•
27 28
•
•
•
29 28
11
"Clutch re-engaged at t=17.0s, generator load on" for clarity. This will help in analyzing the
output and ensuring the timing is correct.
4. Synchronization and Logging
Comprehensive State Logging: Augment the backend to log all relevant state changes and timeseries
data for analysis. The simulator should maintain a structured log (e.g. a list of dictionaries
sim.log = [] ) where each entry is a snapshot of the system at a time step. We will log every
update cycle (or a subset if data rate is high, but ideally each SSE step). Each log entry should include
timestamp, system outputs, and per-floater details similar to the SSE data. For example, an entry
could be:
sim.log.append({
"time": sim.time,
"torque": sim.torque_total,
"power": sim.power_output,
"efficiency": sim.efficiency,
"torque_buoyant": sim.torque_buoyant,
"torque_drag": sim.torque_drag,
"torque_generator": sim.torque_generator,
"floaters": [
{"buoyancy": f.buoyancy, "drag": f.drag, "net_force": f.net_force,
"pulse_force": f.pulse_force}
for f in sim.floaters
],
"clutch_engaged": sim.clutch_engaged,
"air_tank_pressure": sim.air_tank_pressure
})
This example includes a few extra fields like clutch_engaged and air_tank_pressure to capture the
state of H3 and compressor; include any others that are relevant (e.g., compressor power, flywheel speed,
etc.). The idea is to make the log a complete record of the simulation run. Ensure this logging happens
inside the simulation loop each step (but be mindful of performance if the step size is very small – logging
every single step might generate a huge log quickly; you could log every Nth step or throttle if needed). We
will use this log for both debugging during development and for output export.
Event and Anomaly Logging: Add explicit log messages for significant events or anomalies in the
simulation. Use Python’s logging module or simple print statements (that go to console) for runtime
observation, and/or include an "events" list in the sim.log entries for critical issues.
Examples:
When a floater is supposed to fill with air but air_tank_pressure is insufficient, log something
like: logging.warning(f"t={sim.time:.2f}s: Pressure too low to fill floater
{floater_id}, skipping injection.") . This warns that the cycle is disrupted due to low
pressure.
•
•
•
12
If a torque spike occurs (e.g., when clutch engages, you might see a sudden jump in torque or
deceleration), log that: logging.info(f"t={sim.time:.2f}s: Clutch engaged, generator
torque spike = {sim.torque_generator:.1f} N·m") .
If any physical limiters activate (for example, if you implement a max torque or safety cutoff), log
those events.
State changes like clutch engage/disengage can be logged as mentioned (this can be done in the
same place where you toggle the state).
These logs will be invaluable for developers to trace the simulation behavior. They are not necessarily
exposed to the end-user in the UI, but could be written to a console or a file. Ensure that these messages
are descriptive and include timestamps for correlation with the numeric data.
Structured JSON/CSV Output: Maintain the log in a format easily exportable as JSON or CSV. Since
we already accumulate sim.log as a list of dicts, it’s naturally JSON-serializable (could be huge, but
for moderate simulation durations it’s fine). We can provide two ways to retrieve it:
On-Demand JSON Dump: A route like /download_json (or even reuse /get_output_schema
by extending it to data – but better separate) that returns jsonify(sim.log) so the entire run’s
data can be fetched by developers.
CSV Download: As suggested in Stage 2, implement an endpoint /download_csv that streams the
log as CSV . The code from the guide can be adapted – it iterates over sim.log and writes
out a line per entry. We will extend it to include new fields. For example:
@app.route('/download_csv')
def download_csv():
def generate_csv():
# Write header
yield
"time,torque,power,efficiency,torque_buoyant,torque_drag,torque_generator";
for i in range(len(sim.floaters)):
yield f",f{i+1}_buoyancy,f{i+1}_drag,f{i+1}_net_force,f{i+1}
_pulse_force"
yield "\n"
# Write each log entry
for entry in sim.log:
line = f"{entry['time']},{entry['torque']},{entry['power']},
{entry['efficiency']},{entry.get('torque_buoyant', '')},
{entry.get('torque_drag', '')},{entry.get('torque_generator', '')}"
for f in entry['floaters']:
line += f",{f['buoyancy']},{f['drag']},{f['net_force']},
{f['pulse_force']}"
line += "\n"
yield line
response = Response(generate_csv(), mimetype='text/csv')
response.headers['Content-Disposition'] = 'attachment;
filename="sim_data.csv"'
return response
•
•
•
•
•
•
30 31
13
This will produce a CSV with time, total torque, power, efficiency, then optional torque components,
followed by columns for each floater’s forces. The header generation above dynamically adds
columns for however many floaters are in the simulation (f1_buoyancy, f1_drag, etc.). The approach
streams the CSV to avoid memory issues. The blueprint’s simpler example only logged time, torque,
power, efficiency ; we’ve expanded it. Developers can open this CSV in Excel or Python for
analysis.
Test the CSV download after a simulation run to ensure the formatting is correct and all expected data is
present. If the log is very large, the download may be heavy; consider allowing the user to specify a time
range or sample rate for export in the future (not mandatory for this patch, but a note for usage).
Time Stamps and Simulation Totals: In the logs, include cumulative or final results if useful. For
example, at the end of a run (if the simulation is not continuous), you could compute total energy
input, total energy output, and overall efficiency. If the simulation runs indefinitely (real-time), this
might not apply unless we define a stop condition. However, since our focus is real-time, it’s fine to
just log stepwise. The timestamp in each entry ( time ) should be simulation time in seconds
(starting from 0 at simulation start). This is already included in SSE and log entries. If real wall-clock
time is needed for debugging, you can also add a real timestamp (perhaps when the message was
sent) but it’s less critical. The simulation time suffices for analyzing performance (e.g., we can see
how things change per second of simulated operation).
In summary, by logging everything in structured form, we make the simulator’s behavior transparent. This
will not only help in debugging and verifying the patch features (H1, H2, H3 effects, etc.) but also allows
deeper analysis of why the KPP either achieves or fails to achieve certain outputs (e.g., we can confirm via
logs that without H1/H2, drag dissipates most of the energy, etc. per the feasibility study).
5. File-Level Patch Instructions
Below is a breakdown of specific file changes, indicating where to apply the above modifications in the
codebase. For each file/module, we list the major updates to implement:
main.js (Frontend Script)
Parameter Event Handlers: In the initialization section of main.js , bind all control inputs to the
unified updateParam function. For example, select elements by ID for each slider/toggle and
assign their event. Remove any duplicate or old event functions (like separate
onAirPressureChange() or similar) and replace them with calls to updateParam . This may
involve creating a helper to map DOM IDs to param names if they differ, but since we normalized IDs
to snake_case, you can often use the ID directly. For instance, if an input has id="air_pressure" ,
you can do:
document.getElementById('air_pressure').oninput = e =>
updateParam('air_pressure', parseFloat(e.target.value));
Do this for each adjustable parameter (air pressure, nanobubble fraction, thermal coefficient,
number of floaters, etc.). For boolean toggles (checkboxes), use onchange and pass
31
•
•
14
e.target.checked to updateParam. This ensures all UI controls send their data via fetch('/
set_params') to the backend immediately when changed .
SSE Connection Setup: Locate or add the code that starts the EventSource to /stream . Ensure it is
only started after the page loads (e.g., wrap in window.onload or place at bottom of body). The
code should be as shown in section 1:
const source = new EventSource('/stream');
source.onmessage = function(event) {
const d = JSON.parse(event.data);
// update charts and table...
};
source.onerror = function(event) {
console.error("SSE error:", event);
// perhaps update UI status indicator here
};
Remove any older polling or AJAX-loop code if it existed (SSE replaces it). We want a single persistent
SSE connection. Make sure to handle event.data parsing and updating of all relevant UI elements
(charts, tables, numeric displays, etc.). This code likely lives in main.js already in some form;
refactor it to use the new data structure ( d.efficiency instead of d.eff if we renamed it, etc.).
Use the addData pattern for charts as given above . If an updateCharts() function
existed that took data and manually manipulated chart datasets, you can simplify it now by using
our unified approach: i.e., just call addData(torqueChart, d.time, d.torque) etc., inside the
SSE message handler, rather than rebuilding chart data arrays from scratch.
Update Chart Data Ingestion: If the charts were initially populated only after simulation end or via
a one-time result, change them to live-update mode. In main.js , ensure each SSE message adds a
new point to the charts. As described, you might have a helper function
addData(chart, label, value) (if not, implement it). Remove any code that redraws the
whole chart each time; with Chart.js, we want to append to existing data for performance. Also
consider trimming the dataset: if the simulation runs indefinitely, add logic to remove old data
points from charts after a certain length (to prevent the graph from growing unbounded). For
example, keep the last N seconds of data:
if (chart.data.labels.length > MAX_POINTS) {
chart.data.labels.shift();
chart.data.datasets[0].data.shift();
}
before pushing new data. This detail can be adjusted based on UI needs. The main point is to ensure
charts reflect the streaming data in real time, as recommended .
1 2
•
4 5
•
6
15
Floater Table Update: In main.js (within the SSE handler), implement the code to refresh the
floaters table per the new data format. The Stage 2 guide provided pseudocode for this .
Concretely, find where the table might have been updated (perhaps a function like
updateFloaterTable(data) existed). Refactor it to:
Clear existing rows (except header).
Loop over d.floaters array from SSE data. For each floater (with index i ):
Insert a new table row ( document.getElementById('floaterTable').insertRow() ).
Fill cells with: Floater index, formatted position (if available in d.floaters[i].pos ),
velocity (if d.floaters[i].vel exists), buoyancy, drag, net_force, pulse_force.
Use toFixed(2) or similar to format numeric values for readability. Make sure the
property names ( buoyancy , drag , etc.) match exactly what the backend sends (after you
update SSE output). Initially, it might be buoy and drag , which we changed to full
names in the patch; adjust accordingly in the JS. If position/velocity aren’t in the SSE (our new
output only included forces for brevity), you can omit those columns or add them if needed.
The HTML table structure (with <th> headers for each column) should be updated to align
with these keys. This table update should run on each SSE message. Verify that the number of
rows matches sim.num_floaters (if not, you might need to also update if the number of
floaters can change at runtime—if num_floaters is adjustable, when it changes you
should recreate the table header or at least handle the differing array length dynamically).
UI Fallback Indicator: Add a small piece of code to manage the SSE status indicator or alert. For
example, if you created a <span id="statusIndicator"> or a hidden <div
id="disconnectAlert">Disconnected</div> , toggle it in source.onerror as described
earlier. This likely will be new code in main.js . Keep it minimal (just setting text or showing a
hidden element). This doesn’t interfere with simulation but is good UX.
After these changes, the main.js script should be cleaner and more unified. You’ll have one function
handling all param updates, one SSE handler updating all visuals, and modular helper functions (like
addData ). Test the frontend: start the simulator, adjust each control one by one and observe that the
backend receives the changes (you can check Flask logs or add printouts in /set_params ), and that
charts and tables update continuously from SSE data. If something doesn’t appear, use the browser console
to ensure no JS errors (common ones might be if you refer to a wrong field name in d ). Fix any such
mismatches.
index.html (UI Template)
Form & Input Elements: Go through the HTML template and modify the control elements to match
the new parameter naming and structure. Each input or control should have:
Snake_case id/name: e.g., <input type="range" id="air_pressure"
name="air_pressure" ...> for air pressure. Do this for all (nanobubble fraction, thermal
coefficient, etc.). Using the same ID as the parameter name allows the JS to directly use it for
updateParam . If the form was using camelCase, change it here accordingly.
Labeling and grouping: Ensure each input has a <label> for clarity. For example:
•
32 33
•
•
◦
◦
◦
8
•
•
•
•
16
<label for="air_pressure">Air Pressure (bar):</label>
<input type="range" id="air_pressure" min="0" max="10" step="0.1"
value="1.0">
<span id="air_pressure_val">1.0 bar</span>
You might include a span to display the current value next to the slider (optional but user-friendly). If
so, update that span’s text in the slider’s oninput event as well.
New controls: Add HTML elements for any parameters that didn’t exist in the original UI. For
instance, if pulse_enabled (H3 toggle) wasn’t present, add a checkbox:
<label for="pulse_enabled">Pulse Mode (H3) Enabled:</label>
<input type="checkbox" id="pulse_enabled">
Similarly, if thermal coefficient (H2) wasn’t adjustable via UI before, add an input (could be a number
input or another slider). From the Stage 2 snippet, they had a number input for “Heat Coeff” . You
might use a range 0–1 or 0–100% depending on interpretation. For simplicity, a number input with
step (like 0.01 step) is fine.
Floaters table placeholder: Ensure there is a <table id="floaterTable"> in the HTML if not
already. It should have a header row with <th> for each column: e.g., “Floater #, Buoyancy (N),
Drag (N), Net Force (N), Pulse Force (N)”. (Include Position/Velocity if those are going to be shown.)
The body will be filled by JS. The Stage 2 guide provided an example header . For instance:
<table id="floaterTable" class="table-auto text-sm">
<tr>
<th>Floater</th><th>Buoyancy (N)</th><th>Drag (N)</th><th>Net Force
(N)</th><th>Pulse Force (N)</th>
</tr>
<!-- rows will be injected here -->
</table>
Include this in the layout where it makes sense (perhaps below the charts or to the side).
Script Includes: Ensure the HTML loads the required scripts. This includes Chart.js (as a <script
src=".../chart.js"></script> in the head or end of body) and your main.js (if it’s a
separate file, include it with a script tag at end of body). Also include any CSS or frameworks needed
(Tailwind, etc., as seen in the provided HTML files). From the snippet we know Chart.js is included
. Verify these references are correct and up-to-date.
Initial Values and Sync: Set initial form control values to match the simulation’s default parameters.
For example, if sim.air_pressure starts at 1.0 bar, make the slider default 1.0. If
pulse_enabled default is False, leave the checkbox unchecked initially. This avoids a jump when
the user first touches a control (because if the UI and backend are out of sync, the first update might
•
34
•
32
•
35
•
17
send an abrupt change). One strategy is to have the backend render the template with current
values (using Jinja2 if this is a Flask template). But if that’s not in place, manually match them now.
Fallback UI Elements: Add any HTML elements needed for the SSE disconnect indicator, if you
decided to use one. For example, a small status text or icon somewhere in the header or footer.
Could be as simple as: <div id="status" class="text-xs text-gray-500">Connected</
div> . The JS will update this to “Disconnected” and perhaps add a red style if error. This is optional,
but since we mentioned it, include it in HTML for completeness.
After editing index.html , the interface should have all controls visible and labeled, and the overall layout
should remain user-friendly (you might use a simple grid or flex layout to organize sliders and charts). Test
the form elements manually: open the page, verify sliders move and show values, check that the checkbox
toggles, etc. When connected to the backend, also verify that on refresh the default values make sense (for
instance, if nanobubble_frac default is 0, the slider should show 0).
(If the project uses templating, some of these changes might be in a template file rather than a static .html. The
instructions apply regardless – update the corresponding template.)
simulation.py / engine.py (Physics Engine)
Parameter Schema Usage: At the top of this module, define the PARAM_SCHEMA (if not defined
elsewhere) or at least define the default values for each parameter. The simulation engine should
either read from a central config or have its own copy of expected params. If you placed
PARAM_SCHEMA in the Flask app file, ensure the simulation knows about constraints (perhaps via
assertions or checks). At minimum, initialize new parameters: e.g., add
self.nanobubble_frac = 0.0 , self.thermal_coeff = 0.0 , and
self.pulse_enabled = False in the simulation’s constructor or init function. This ensures the
simulation has all the attributes that the Flask route might set. Also include self.num_floaters if
not already, and make sure changing it (via set_params) triggers a re-initialization of floaters (in the
provided patch diff, they call sim.reset_floaters() when num_floaters changes ).
Implement such a reset_floaters method to rebuild the floater list/objects when count
changes.
Main Simulation Loop Changes: In the function or loop where physics is updated (could be
Simulator.step() or within a generator for SSE), integrate the new physics logic:
Apply H1 effects: adjust water density or drag coefficient based on self.nanobubble_frac . If
you have separate handling for ascending vs descending floaters, apply accordingly. For example, in
computing forces for a floater, do:
rho = WATER_DENSITY
Cd = BASE_CD
if floater.is_descending: # define how to check this
rho = rho * (1 - self.nanobubble_frac) # lighter water
•
•
36
•
•
18
Cd = Cd * (1 - 0.5 * self.nanobubble_frac) # example 50% max drag
reduction
Then use rho in buoyancy and drag formulas, and Cd in drag formula. This encapsulates the H1
logic in the physics step.
Apply H2 effects: if self.thermal_coeff > 0, increase buoyancy for ascending floaters. For
example:
if floater.is_ascending:
buoyant_force = WATER_DENSITY * floater.volume * G * (1 +
self.thermal_coeff)
else:
buoyant_force = WATER_DENSITY * floater.volume * G
Or if you incorporate it as an adjustment to air density, do something like (pseudo-code)
air_temp_effect = self.thermal_coeff * (water_temp - ref_temp) as in Stage 2 ,
but given we lack temp, the simpler boost is fine. Essentially, ensure buoyant force is magnified
when thermal boost is on. (Also account for the fact that thermal boost might require a heat source;
in reality ambient heat is used, which the whitepaper treated as “free”, but if you wanted, you could
eventually log the thermal energy used – not needed now.)
Enforce drag formula: Wherever drag is calculated, replace the old formula with . You
need the floater’s velocity relative to water. If you have floater.velocity as an upward speed,
you can do:
drag_force = 0.5 * rho * Cd * floater.area * (floater.velocity ** 2)
drag_force = min(drag_force, some_max) # optionally cap if needed
drag_force *= -1 * np.sign(floater.velocity) # oppose motion
(Using sign to set direction: if velocity is positive upward, drag is negative downward, etc.) Use the
adjusted rho and Cd from above for H1.
Net force & acceleration: Compute each floater’s net force = buoyant_force (upward) + weight
(downward, i.e. ) + drag_force (downward for upward motion, upward for downward motion) +
any pulse_force. Pulse force could be modeled as a short upward thrust when air is injected. For
example, when a floater switches from water-filled to air-filled (at the bottom), you might apply an
upward impulse to simulate the air rushing in. If you choose to simulate this, you could add:
if floater.just_injected:
pulse_force = some_impulse_value # e.g. proportional to injection
pressure
else:
pulse_force = 0
and include that in net force. This might be complex to calibrate; a simpler interpretation is that
pulse_force is just informational, not actually affecting motion (since the effect of injection is mostly
that the floater is now buoyant). However, if the design has a noticeable kick (like a jet), you could
•
25
• 0.5ρCdAv
2
•
−mg
19
add a brief upward force. In any case, calculate floater.net_force and store all components
( floater.buoyancy , floater.drag , etc.) for use in output.
Integration & Movement: Update floater positions and velocities using the net force. Likely you
already have something like:
a = net_force / floater.mass
floater.velocity += a * dt
floater.position += floater.velocity * dt
Keep those, and ensure dt is the simulation time step (from params or fixed). If you implemented
physical limits, you might do something like: if floater.position reaches top or bottom bounds,
handle that (wrap around if using a loop model, or teleport to other end if simulating a continuous
chain).
Compressor & fill logic: Implement the compressor logic as described. This might not be in the
same loop as forces – it could be in a control section where you detect if a floater is at bottom. If you
have a list of floaters in order, you might check each step if any floater’s position is at the bottom
threshold and not yet filled. If yes and pulse_enabled is false or irrelevant at that moment (H3
doesn't directly affect filling), then:
If air_tank_pressure >= required_pressure : set floater.filled=True (meaning
it becomes buoyant) and decrease air_tank_pressure .
Else: keep floater.filled=False (stays heavy) and maybe mark it to try next time. Also
simulate air_tank_pressure recharge: each step do air_tank_pressure +=
compressor_rate * dt up to a max. The compressor rate and required_pressure can be
constants or derived from params (if available). Ensure that when a floater is filled, you
appropriately update its mass (water out, air in) or however the buoyancy is handled (possibly
your buoyancy calculation implicitly handles filled vs not by volume, but if not, you might
toggle floater’s volume of air vs water). Likely, you have a simpler approach: e.g., maybe
floaters have two states and different effective density. If not, an easy way: define
floater.mass = floater.mass_air_filled if filled else
floater.mass_water_filled . So when you toggle filled , update floater.mass
accordingly (and maybe reset velocity if you think the injection changes conditions suddenly –
but that might be negligible if done instantly).
After these changes, the physics engine will be more complex but also more true-to-life. Important: Test
the physics in various configurations: - All enhancements off (nanobubble_frac=0, thermal_coeff=0,
pulse_enabled=False): The simulator should behave like a basic buoyancy machine. Check that net torque
likely settles around zero or a small value due to drag (in line with KPP baseline claims that it wouldn't run
itself). - H1 on (e.g., nanobubble_frac=0.1): Drag on descending side should drop; see if net torque
increases. Perhaps log average net torque over time to confirm. - H2 on (thermal_coeff say 0.1): Ascending
force increases; net torque should increase as well. - H3 on: The output should come in bursts. You might
see the chain speed oscillate. Check the logs for clutch events and ensure the pattern (coast/pulse) is
happening. - Also try edge cases: extreme values like nanobubble_frac = 0.5 (50% void, unrealistic but just to
see if code handles it), or pulse mode with very short pulses, etc.
Tweak as needed (like drag reduction factor or thermal boost effect) to keep the simulation stable. It’s okay
if the “enhanced” modes show improved performance, but they should still obey physics (no perpetual
motion without input; if you see efficiency >100% consistently with some settings, that indicates our model
•
•
◦
◦
20
is granting free energy – consider adding an energy draw for thermal boost if thermal_coeff is high, or a
diminishing return on nanobubbles at high concentration as hinted by research ).
Torque & Power Calculation: After updating forces on each floater, compute the system’s torque
and power. If not already done, sum contributions of floaters to net torque on the main shaft. For
example, if each floater is attached to a chain over a sprocket of radius R, then each floater’s torque
contribution is (taking upward forces as positive torque) . Sum all floaters’
torques for total shaft torque. Alternatively, if you have known number of floaters on each side, you
could compute net torque as (sum of upward forces on one side minus sum of downward forces on
the other) * R. Use whichever method your model is structured for. After finding
sim.torque_total , compute generator power: if generator is engaged,
(angular speed times generator torque). If you have the chain speed or angular velocity of the wheel,
use that. If not explicitly, you might approximate power output as net torque * some angular velocity
(which might be derived from floater linear velocity over sprocket radius). Ensure to update
sim.power_output each step. Also calculate efficiency = (output power / input power). Input
power in this system mainly comes from the compressor. If you have a measure of compressor
power usage (say, compressor_power = pressure * flow_rate or something), use it. If not,
you can approximate input power by the work done to inject air: whenever you fill a floater, you add
potential energy (buoyancy) to the system equal to the weight of displaced water * height – which
came from compressor work. Summing these over time and comparing to generator output gives
efficiency. But for now, perhaps use a simpler placeholder: efficiency = output / (output +
compressor_consumed) or update sim.efficiency gradually if easier. The key is,
sim.efficiency should move between 0 and 100% and likely be low or <1 in normal mode,
maybe improve with enhancements but realistically still <100%. This value is what we output and
chart.
With torque breakdown: assign sim.torque_buoyant , sim.torque_drag , etc., if you can compute
them separately. For example, torque_buoyant could be the torque from buoyant forces minus weight
(i.e., if there were no drag or generator, what torque would the floats produce?). torque_drag could be
negative, equal to the total drag force * radius (for all floaters). torque_generator is negative when
engaged (resisting). If you cannot easily separate buoyant vs weight (since weight just offsets buoyancy on
descending side), you might define torque_buoyant as the net torque if drag and generator were zero
(which effectively includes gravity effect). This might be confusing; an alternative is: torque_up from all
ascending floaters (buoyancy minus their drag), torque_down from all descending (weight minus their drag),
and then net = torque_up - torque_down - generator_torque. But in output, simpler to present the losses:
drag torque and generator torque as the two opposing components. So you could set: - torque_buoyant
= torque_total + |torque_drag| + |torque_generator| (the hypothetical torque if no losses), -
torque_drag = -|torque_drag_loss| , - torque_generator = -|torque_generator_load| .
The exact values aren’t as critical as ensuring the fields convey meaningful info. Make sure to use these in
SSE output (section 2).
Integration with Logging: As you update the physics, also update what gets logged each step. The
code snippet for logging in section 4 serves as a guide. Right after you compute all the forces and
update states for the step, create a log entry with all the values. That way, nothing is missed. If you
added new simulation variables (like air_tank_pressure , clutch_engaged ), include them too.
This will aid debugging of this physics logic by examining the logs.
37
•
τi = Fnet,i × R 38
P = ω × τgenerator
•
21
By the end of these changes in simulation.py/engine.py , the simulator will handle the new
parameters and reflect the hypotheses: H1 and H2 tunable via their parameters (and visible in outputs), and
H3 via pulse mode. The machine’s behavior should qualitatively match expectations: - Without
enhancements, it stalls or barely turns (net torque ~ zero due to drag ). - H1 reduces drag/opposition,
giving net positive torque but still likely < required (depending on how much you reduce drag). - H2
increases buoyant work, boosting torque. - H3 creates an oscillating torque/power output, possibly
improving average efficiency by avoiding continuous drag (like pulse-and-glide improves car efficiency
).
routes.py (Flask Routes)
(Assuming your Flask routes are defined in a module routes.py or directly in app.py . Adapt accordingly.)
Import/Setup: Make sure to import any new modules at the top (e.g., if you moved
PARAM_SCHEMA to a config file, import it, or if using json for schema route, import jsonify, etc.).
Also ensure the simulation instance ( sim ) is accessible here.
PATCH /set_params : In this route function, implement the validation and updates as described in
section 2. If the route was previously very simple (just assigning values without checks ), replace
that with the loop over data items and schema checks. Use the PARAM_SCHEMA to validate types
and ranges. Then apply to sim . You might have a method sim.set_param(name, value)
which updates the attribute and also triggers any immediate effects needed (for example, if
name=="num_floaters" , that method could call self.reset_floaters() ). Alternatively,
handle that logic in the route: after setting all values, check if num_floaters was in data and if so
call sim.reset_floaters() explicitly (as shown in the patch diff where they did it after setting
sim.num_floaters ). The provided example in Stage 2 simply casts and assigns ; we are
adding more robustness. End by returning a 204 No Content on success (which means no
response body, just success), as in the example . If an error occurs, return a 400 with JSON error
as described. This way the frontend can potentially handle an error (though in our case, front-end
isn’t explicitly coded for it yet, but it’s good practice).
MODIFY /stream : In the SSE route, after patching the simulation loop, update the output format.
Use the new data structure assembled in simulation engine or assemble it here from sim . For
instance:
@app.route('/stream')
def stream():
def generate():
while True:
sim.step()
# advance simulation by one step (assuming internal dt)
data = sim.get_output_data() # if you have a helper that
returns dict
# If not, build dict here using sim's attributes:
# data = {
# "time": sim.time, "torque": sim.torque_total, "power":
26
39
40
•
•
11
41 42 43
43
•
22
sim.power_output, ...
# }
yield f"data: {json.dumps(data)}\n\n"
time.sleep(sim.dt) # sleep for dt seconds, or a fixed interval
return Response(generate(), mimetype='text/event-stream')
Make sure the keys in data exactly match what the frontend expects (we decided on names like
"efficiency" instead of "eff" , so use those). If you changed sim.eff to sim.efficiency
property, reflect that . Also include the new fields: torque_components or individual
torque breakdown values, and the extended floater info. This route should now continuously stream
full JSON frames including all forces and states, which the frontend will parse. Test this by running
the Flask app and visiting /stream directly in a browser or curl – you should see a stream of
data: {...} lines. Also possibly test /set_params via curl to ensure it returns 204 and actually
updates sim (for example, change a param and see if sim’s state changes or log reflects it).
NEW /get_output_schema : Implement this route in routes.py as described. It’s
straightforward since it just returns a JSON. You can either manually craft the schema dict (as in
section 2 example) or programmatically generate it from PARAM_SCHEMA and known output keys. A
simple manual dict is fine here because the output structure is static (doesn't change per run). Be
sure to include all the keys we send over SSE. The user can call this from a browser or via fetch to get
documentation. This endpoint should be added to Flask with methods=['GET'] . Test it by hitting
the URL; verify you get the JSON structure.
Logging Routes (Optional): While not explicitly requested, if you followed section 4 to implement /
download_csv or a JSON download, you would add those routes here too. For completeness,
consider adding:
@app.route('/download_csv')
def download_csv():
# similar generate_csv as above
@app.route('/download_json')
def download_json():
return jsonify(sim.log)
The Stage 2 guide shows how to stream CSV , which we adapted. These routes provide a way
to retrieve the collected data. Since the plan asks for CSV-ready logging, adding at least the CSV
route is recommended. (If you do add them, also maybe place a link or button in index.html as
shown in the guide so the user can click to download when needed.)
CORS / Misc: If this simulator is purely local, CORS is not an issue, but if the frontend might be
served separately, ensure the Flask app allows requests (you might use Flask-CORS or just not
needed if same domain). Mentioning this just for thoroughness – likely not needed in local scenario.
44 45
•
•
30 31
46
•
23
In summary, the changes in routes.py tie together the frontend and simulation: improved /
set_params for robust runtime control, an enriched /stream that pushes all necessary data, and utility
routes to understand and export the data. These modifications work in tandem with the frontend changes.
Double-check after implementation: - Start the Flask app, open the web UI. Verify that moving a slider
triggers a POST to /set_params (Flask console log should show a 204 for that). If an invalid value is
somehow sent, the route should log an error. - Ensure the SSE stream starts when the page loads (Flask
console will show GET /stream and keep it open). If you make parameter changes, the simulation variables
should actually update mid-stream (for example, toggle pulse mode on and off and see if the pattern of
torque/power changes live). - Try the /get_output_schema in a browser to ensure it’s correct. - If added,
try downloading the CSV after letting it run a few seconds – open it to see if columns make sense.
output.py (Output Formatter & SSE Helper)
(If the project has a separate module for formatting output or managing SSE and logs, apply these changes in
that context. Some codebases separate concerns by having an output or utils file to build JSON frames, etc. We'll
cover those tasks here.)
SSE Data Formatting: If the assembly of the SSE JSON data was done outside the route (e.g., a
function in output.py ), update that function to include the new fields. For instance, if you have
def format_output(sim) -> dict: ... , ensure it gathers sim.efficiency , the
floaters list with all forces, and so on. Essentially mirror the structure we outlined. The Stage 2
blueprint inlined it in the route , but you might have refactored it. Just make sure no field is
missing or mismatched (common mistakes: using outdated names like eff vs efficiency or
forgetting to add net_force ). Use the examples from the blueprint and our additions as reference
for correctness.
JSON vs. CSV Logging: If output.py handles writing logs to file or converting to CSV, update it to
account for new fields. For instance, if it had a function to dump sim.log to a file, make sure it
writes all keys. If it maintained a list of fieldnames for CSV, update that list. Given we’ve implemented
on-demand CSV download, you might not need a separate output file on disk, but if you do (for
persistent logging), consider adding an option to save the CSV after simulation ends.
Timestamp formatting: If you want real-world timestamp (wall clock), you could add in output
formatting, but simulation time is usually sufficient. However, if this output module writes to a file,
maybe include a real timestamp when writing to differentiate runs.
Ensure Thread-Safety for SSE: Flask’s SSE is using a generator; if the output module uses any global
state, ensure it’s not modified concurrently. Probably not a concern here if everything is in sim
object.
Testing Output Module: If there’s a unit test or a simple invocation for output formatting, run it. For
example, call format_output(sim) after one simulation step and inspect the dict. It should have
all keys and valid values (no NaNs or None). If floaters list is huge, that’s fine (it will have as many
entries as floaters). This is just a sanity check.
•
47 8
•
•
•
•
24
Image/Plot Output (if any): The original blueprint mentioned Matplotlib plots in an older setup.
Since we’ve shifted to real-time Chart.js, you might not be generating static images anymore. If any
code remains that saves plots or images in static/plots/ , consider whether it’s still needed.
Possibly not, since Chart.js covers live plotting. You can keep the plotting utility but it’s outside our
real-time loop now. No action needed unless explicitly integrating it.
Finally, to conclude: once all patches are applied, run the simulator end-to-end. Interact with the UI to
ensure everything is working in concert: - Adjust sliders: see immediate effect on simulation (for example,
increase air_pressure might slightly increase buoyant force in next injection – although actually buoyant
force is fixed by water density and volume, air_pressure would mainly affect compressor energy; depends
on how we use that param in simulation, which could be to determine required pressure threshold). - Turn
on Pulse Mode: watch charts; torque might oscillate, and “Pulse Mode Enabled” log events appear. -
Increase Nanobubble %: watch drag values drop in the floater table, and net force per floater rise, and
possibly an increase in total power or efficiency over time. - Increase Thermal Coefficient: watch buoyancy
values on ascending floaters increase (perhaps you could print buoyancy of a particular floater to verify). -
Download CSV after 30 seconds: open it and ensure columns make sense, e.g., Floaters 1..N each have their
forces.
Throughout the patch process, prioritize correctness and clarity in code. Add comments in the code where
needed to explain these new sections, so future devs understand why e.g. we skip filling a floater
(referencing physics/limitations) or how pulse timing is done. Given this is a handoff to a dev team, wellcommented
code coupled with this document will help them maintain and further improve the simulator.
Stage 2 Upgrade_ Real-Time Simulation Implementation Guide.pdf
file://file-UVKDQgJCEP8LPwraen4Q7s
Flask-Based KPP Simulator Implementation Blueprint.pdf
file://file-3HVVUCDUgivcJmxNAkMx7U
KPP Feasibility and Claims Analysis_.docx
file://file-1JPZjZMPCt1FnZ7Y2psKxd
Kinetic Power Plant (KPP) Technology White Paper.pdf
file://file-Wn4JQYdoC26QBSWsGJd8r8
Kinetic Power Plant (KPP) 500 kW System Analysis.pdf
file://file-GPte2w2G1YktAXD2vdpggq
Kinetic Power Plant (KPP) R&D Simulator Algorithm Blueprint.pdf
file://file-DEKb2MeVDubPyHbxBzQBuC
•
1 2 3 4 5 6 7 8 9 10 11 12 20 21 25 30 31 32 33 34 35 36 41 42 43 44 45 46 47
13 38
14 24 26
15 16 17 18 22 37
19 23
27 28 29 39 40
25