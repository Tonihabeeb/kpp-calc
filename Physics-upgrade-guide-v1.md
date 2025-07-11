Plan for Physics Upgrades in the KPP Simulator
Overview and Objectives
The goal of this upgrade is to integrate a realistic physics engine into the existing Kinetic Power Plant
(KPP) simulator, replacing simplistic or legacy logic with accurate buoyancy-driven dynamics. We will
preserve all current simulator features (3D visualization, real-time updates, etc.) while introducing
comprehensive physics modeling. Every aspect of the KPP cycle – from floaters rising and sinking to energy
generation – will be simulated according to physical principles. The upgraded physics module will
seamlessly integrate with the current codebase, meaning the new calculations will hook into the existing
simulation loop, UI, and data streams without breaking functionality. By following best practices in
simulation design and software architecture, this plan ensures a world-class, extensible simulator that
mimics realistic operation of the KPP technology. Key objectives include:
Accuracy: Model buoyant forces, drag, gravity, and torque based on physics equations (Archimedes’
principle, drag equation, etc.) .
Completeness: Simulate the full floater cycle (air injection at bottom, ascent, venting at top, descent)
with appropriate state changes and timing .
Advanced Enhancements: Incorporate the three KPP “know-how” hypotheses – H1 (nanobubble
drag/density modulation), H2 (thermal-assisted buoyancy), and H3 (pulse-and-coast drivetrain with
flywheel) – as optional physics effects that can be toggled for experimentation .
Real-Time Interactivity: Maintain a responsive real-time loop so users can adjust parameters on the
fly (e.g. number of floaters, H1/H2 on/off, etc.) and see immediate effects in the output charts and
possibly in the 3D scene. This involves using server-sent events (SSE) to stream simulation data and
updating the frontend in realtime .
By achieving these goals, we will transform the simulator into a powerful tool that faithfully reproduces
the KPP’s operation for R&D and demonstration purposes, while still being easy for developers to work
with.
Key Physics Components to Implement
To upgrade the simulator’s physics, we need to implement several core components. Below is a breakdown
of each physics aspect and how it will be handled:
Buoyancy (Archimedes’ Principle): Each floater experiences an upward buoyant force equal to the
weight of the fluid it displaces . We will calculate buoyant force per floater as: F<sub>b</sub> =
ρ<sub>water</sub> · V · g, where V is the floater’s submerged volume. For a fully submerged floater
of fixed volume, ρ (water density) and g are constants, so F<sub>b</sub> is essentially constant when
filled with air . However, buoyancy can change if the floater’s volume or the fluid density changes
(see H1/H2 below). We will add a function compute_buoyant_force(volume, rho) in the
physics module (if not already present) to return ρ·g·V . This will be used whenever a floater is in a
buoyant state (filled with air). If the floater is not fully filled with air or not fully submerged, the
•
1 2
•
3 4
•
5
•
6 7
•
1
8
9
1
formula will use the appropriate displaced volume or fluid density accordingly (e.g. if only partially
submerged, but in our closed system we assume full submersion on the active sections). All buoyant
forces act upward on the ascending side of the chain .
Weight and Gravity: Every floater has weight acting downward. For a floater filled with water
(descending side), its weight (mass * g) is much higher than when filled with air. In simulation, each
floater will have properties like mass_empty (structure mass), mass_water (mass of water when
full), etc. When a floater is filled with water, its total mass = mass_empty + mass_water; when filled
with air, total mass = mass_empty + mass_air (mass_air is negligible compared to water). We will
compute the gravitational force as F<sub>g</sub> = m · g, acting downward . This force provides
the downward pull on the descending side floaters. Notably, a water-filled floater still displaces
water, but that buoyant force just offsets some of its weight (exactly equal to the weight of displaced
water) . In our net force calculation, if a floater is water-filled (not buoyant), the buoyant force will
effectively cancel out the weight of the water inside, leaving only the floater’s own structure weight
contributing to net force . We will implement logic such that:
If floater.isBuoyant (filled with air): apply full buoyant force ρ·V·g upward .
If not buoyant (filled with water): buoyant force is effectively ρ·V·g – (mass of internal water * g),
resulting in a small net buoyancy (from the floater structure only) . For simplicity, we may treat
non-buoyant floaters as having zero net buoyant lift (since water weight cancels displaced water),
focusing on their weight downward . This approximation is in line with the blueprint’s approach.
Hydrodynamic Drag: As floaters move through water, drag will resist their motion. We will model
drag using the drag equation: F<sub>d</sub> = ½ · C<sub>d</sub> · ρ<sub>water</sub> · A · v² .
Here C<sub>d</sub> is a drag coefficient (shape-dependent), A is the cross-sectional area of the
floater, and v is the velocity of the floater relative to water. Drag always acts opposite to the direction
of motion: on ascending floaters drag pulls downward, on descending floaters drag pulls upward
. In implementation, for each floater we will compute
drag_force = 0.5 * Cd * rho_water * A * v**2 . We then apply it with a sign opposite to
the velocity sign (e.g. if upward velocity, drag = –F<sub>d</sub>; if downward, drag = +F<sub>d</
sub> upwards ). The drag coefficient C<sub>d</sub> can be a constant (legacy default around 0.8
for a blunt object ) but will be adjustable (especially for H1 scenarios). We will include a
compute_drag_force(Cd, area, vel, rho) helper in physics calculations. This drag modeling
ensures that floats don’t move unrealistically fast and that energy is lost to fluid resistance, matching
real-world behavior.
Net Force and Motion (Floater Dynamics): For each floater, the net vertical force is the sum of
buoyancy (upward), minus weight (downward), plus drag (which could be up or down depending on
motion) . We will compute F<sub>net</sub> for each floater each time-step using a function like
net_force_on_floater(floater) that internally calls the buoyancy and drag calculations
. Once we have F<sub>net</sub>, we update the floater’s velocity and position using Newton’s
second law and integration over the time-step: a = F<sub>net</sub> / m, then v_new = v_old + a·Δt, and
pos_new = pos_old + v_new·Δt. We will implement this using a simple Euler integration each tick (which
was introduced in Stage 1) . Because all floaters are attached via a chain, in reality their
motions are constrained to the chain’s movement. To simplify, we assume the chain is taut and all
floaters move at the same speed (they share a common velocity along the loop). This means we
10
•
11
12
13
• 14
•
13
15
•
16
17
18
19
20
•
21
22
23
24 25
2
could compute net forces on all floaters and sum up torques, but the acceleration of the whole loop
will be determined by the aggregate force imbalance. In practice, a simpler approach is: compute
total torque on the drive sprocket from all floaters, then update a single angular velocity for the
chain/generator system. However, to keep it straightforward for coding, we can also simulate one
representative floater and scale up forces, or simulate all floaters moving in sync. Recommended
approach: treat the entire set of floaters as a system but track individual floater states for realism.
Each floater’s position will be updated along the loop (with appropriate wrap-around from top to
bottom), but enforce that all floaters share the same angular displacement increment per step (since
the chain links them). We will maintain an array of floater objects (or dicts) with properties like
position_along_loop (or a simple y-position for vertical coordinate), velocity , and state
(buoyant or heavy). All floaters’ velocities can be set equal to the chain velocity each frame to
maintain consistency, but their individual forces still contribute to net torque and energy. This
approach ensures visual correctness (multiple floaters at different points) while physics-wise the
chain behaves as one body. We will also include friction or generator resistance as part of net
force/torque (discussed under H3 drivetrain).
Torque and Power Calculation: The net force from the floaters is converted to a torque on the
sprocket or drive shaft that turns the generator. For each floater, we can compute its torque
contribution as τ = F<sub>net</sub> · R, where R is the sprocket radius . Upward net forces
produce positive (driving) torque; forces on the opposite side produce opposite torque. The total
system torque is the sum of contributions from all ascending and descending floaters. In a
balanced ideal cycle, the buoyant side’s torque minus the heavy side’s torque yields the net driving
torque available to spin the generator . We will implement a summation each time-step: iterate
through all floaters, compute each F<sub>net</sub>, project it to torque (taking into account
whether the floater is on the upward or downward path), and sum up. This total torque is then used
to update the angular velocity of the drivetrain via α = τ / I (where I is the rotational inertia of the
chain + flywheel + generator). For simplicity, we might start by assuming quasi-steady speed (or very
large I to smooth changes), but with H3 we will handle dynamic speed changes. We will also
calculate instantaneous power output as P = τ · ω (torque times angular velocity) for the generator,
and track energy (integrate power over time) to evaluate efficiency. This will allow the simulator to
report metrics like instantaneous power, net energy generated vs. consumed (compressor work),
etc., fulfilling the original analysis goals.
Floater State Transitions (Air Injection and Venting): A critical part of the physics is the cycle of
each floater being filled with air at the bottom and emptied at the top . We will implement a
simple state machine or triggers for floaters:
At Bottom: When a floater reaches the bottom of the loop (y ~ 0 in our vertical coordinate), it enters
the injection zone. At this point, we will switch the floater’s state to buoyant ( isBuoyant = true ).
This means setting its internal mass of water to 0 (or removing most of it) and possibly giving it an
initial upward velocity “kick” if desired (to simulate the sudden buoyant thrust when air is injected).
We should also account for the compressor energy input here – we can log how much energy is
spent to inject air (based on pressure and volume, although a simple approach is fine). The
simulation will likely treat injection as instantaneous for now (in reality it’s a short pulse) – we can
simply flip the state in one time-step and adjust masses. A check valve logic can be abstracted; we
assume once state flips to buoyant, water is out and floater is full of air.
•
2
10
•
3 26
•
3
Upward Travel: As the floater ascends, it remains buoyant until it reaches the top. During ascent, we
might gradually adjust buoyancy for H2 (see below) but otherwise the floater stays in buoyant state
with constant volume displacement. We track its motion under forces as described.
At Top: When the floater approaches the top of the loop (y ~ tank height), we trigger venting. This
will switch the floater’s state to non-buoyant ( isBuoyant = false ), meaning we consider it now
filled with water again. In practical terms, we will instantly add the mass of water back into the
floater (mass_total increases), and recompute any forces from that point as a heavy object. The air is
released (possibly to atmosphere), but the simulation can just drop the buoyancy to zero at this
moment. The floater then begins its downward journey. We assume the refill is immediate upon
venting due to water pressure (which is a reasonable approximation given the design) .
Downward Travel: The floater now sinks under gravity. We simulate its motion with weight and drag
as the dominating forces (buoyancy is minimal when full of water). It continues until it again reaches
bottom, closing the cycle.
We will implement these transitions by checking floater positions each loop iteration. For example, if
floater.position <= 0 (or within some epsilon of bottom), and it’s not already buoyant, then
inject (set buoyant). If floater.position >= tank_height and it is buoyant, then vent (set nonbuoyant).
In a continuous simulation, the exact trigger might use a small zone or event scheduling.
Ensuring these state changes happen at the correct time step is important for stability. This simple
mechanism ensures the simulator follows the full mechanical cycle of the KPP .
Note: We may incorporate a slight delay or condition to ensure one floater finishes injection before
the next starts (if needed to avoid two injections at once, though if floaters are spaced evenly, it
should naturally stagger). The control logic (if any) can be as simple as above or more sophisticated
later (e.g., only inject if the generator load allows, etc., possibly controlled by a separate module as
the blueprint suggests). Initially, a deterministic periodic injection based on position is sufficient.
H1 – Nanobubble Density/Drag Modulation****: The first enhancement hypothesis (H1) posits that
injecting nanobubbles into the water column (particularly on the descending side) can reduce water
density or drag, making it easier for the heavy floaters to sink (and reducing opposing drag on the
ascending side) . To model H1 in our simulator, we will introduce a parameter (e.g.
nanobubble_fraction or simply a boolean flag for H1). The effect in physics terms can be
modeled in a couple of ways:
Reduced Fluid Density: We can simulate that the water on the descending side has an effectively lower
density (mix of water and bubbles). For example, if nanobubbles reduce density by X%, we multiply
ρ<sub>water</sub> by (1 – X) when computing forces on descending floaters . This directly
reduces buoyant force (which is good for sinking, as less upward buoyancy opposes the weight) and
also reduces drag force (since drag ∝ ρ). The Stage 2 guide suggests exactly this approach:
rho_water = base_density * (1 – nanobubble_frac) . We will implement this such that in the drag and
buoyancy calculations, we use a lower rho for floats currently on the descending leg. Ascending side
could be considered normal water (full density) if we want to be precise. To implement this
seamlessly, inside the per-floater force calculation we can check if floater.isAscending (we might
define this based on its position or state) and if not (meaning descending) and H1 is enabled, use
reduced rho for that floater. We might add a property or method to determine if a floater is on the
ascent or descent path (e.g., by its index or position along loop).
Reduced Drag Coefficient: Another approach (or additional effect) is that nanobubbles might
effectively reduce turbulence and drag. We could encode H1 as a reduction in the drag coefficient
•
•
26 4
•
•
3 4
•
•
5
•
27
27
•
4
C<sub>d</sub> for descending floats. For instance, if base C<sub>d</sub> is 0.8, maybe under H1 it
drops to 0.4 for those floats. This would significantly cut the drag force opposing their motion,
allowing faster descent and less energy loss. The blueprint hints that H1 is mainly about drag
reduction . We could combine both effects by treating nanobubbles as reducing effective
density (which inherently reduces drag force) – this is simpler to implement than adjusting Cd
dynamically. We will allow the nanobubble_frac parameter to tune how strong the effect is (0 =
off, 1 = extremely aerated). For example, nanobubble_frac = 0.2 would mean 20% density reduction
on that side, which reduces buoyant force and drag accordingly . The simulation will recalculate
forces each time-step using the updated rho, meaning as long as H1 is active, every step the
descending floaters feel lighter fluid.
Visualization/Integration: We will ensure the existing UI can reflect H1. In the current 3D scene,
there was a “H1: Resonant Bubbles” mode that simply made a lighter-colored water column visible
. With the new physics, we will tie this mode to actually enabling the nanobubble physics in the
backend. The control button for H1 can send a parameter update ( /set_params endpoint) to set
nanobubble_frac > 0. The simulation then immediately uses the modified density for forces .
The result should be that the descending floaters move faster (due to less drag/resistance) and the
net torque improves modestly because the heavy side is not being held back as much. We expect a
small net power gain with H1, consistent with the claims (e.g., our demo assumed an output from –
50 kW to +10 kW flipping) – the real simulation will show whatever physics result from the
parameters chosen .
H2 – Thermal-Assisted Buoyancy (Isothermal Expansion): The second hypothesis (H2) is that by
keeping the expanding air warm (near-isothermal expansion), the floaters get an extra buoyancy
“kick” as they rise . In practical terms, as a floater ascends, the water pressure decreases; if the
injected air can expand without cooling too much (absorbing heat from surroundings), it will
maintain higher pressure/volume and expel more water, yielding more lift. To simulate H2, we will
allow the buoyant force of a floater to increase during ascent instead of remaining strictly constant.
Two approaches to model this:
Dynamic Volume Expansion: We can simulate that a floater is not 100% filled with air at the bottom
(perhaps it’s, say, 90% air, 10% water at injection completion), and as it rises the air gradually
expands to fill 100% by the top, pushing out that remaining water. This means the effective displaced
volume (air volume) increases with decreasing depth. We could model the volume of air in the
floater as a function of pressure (using Boyle’s law for isothermal process: P·V = constant). For
simplicity, assume at bottom the air occupies volume V0 under pressure P0 (which is higher due to
depth), and at a higher position where pressure is lower, the volume could increase to V1. Instead of
doing a complex calc, we might parametrically say buoyant force increases by a certain fraction from
bottom to top when H2 is enabled. For example, we can introduce a factor or schedule: at bottom,
buoyant force = ρ·V·g (slightly less than full volume buoyancy if some water remains), and by top, buoyant
force = ρ·V<sub>full</sub>·g (full volume). To implement, we can make buoyant force a function of height:
F<sub>b</sub>(y) = ρ·g·[V_base + (V_full – V_base) * f(y)], where f(y) might be a normalized function of
height (0 at bottom, 1 at top). A simpler approach is to just give a short boost* in buoyancy at a certain
point to mimic the expansion energy release. The demo code, for instance, highlighted a “kick”
around certain fractions of the cycle . We can do better by continuously varying it.
Effective Density/Thermal Factor: Another implementation path (suggested in Stage 2 guide) is to
adjust the fluid density slightly based on a thermal expansion coefficient . For example, treat the
local water density as slightly lower if water temperature is higher (thermal expansion of water) or
28 29
30
•
31
32 33
34 35
•
5
•
36 37
•
38
5
directly adjust buoyant force by a factor. The guide shows: rho_water *= (1 - α * ΔT) then
buoyant_force = rho_water * V * g . This is a bit abstract, but essentially if the water or system is
warmer, ρ is less, meaning less buoyancy – which is opposite of what we want for lift. Instead, a
better interpretation: if H2 is active, we could directly amplify the buoyant force by a certain
percentage to represent the extra lift gained. For instance, if H2 yields a 10% more work from
buoyancy, we could multiply F<sub>b</sub> by 1.1 when computing net force on an ascending
floater. However, to be physically sound, we will simulate it as time-varying buoyancy: recalculate
the floater’s displaced volume as it moves up. We might approximate pressure vs depth linearly for
small depths. For coding ease: define floater.air_volume that increases slightly every update
while ascending (or compute it from current depth: deeper in water = higher pressure = less
volume). This way, the buoyant force calculation uses a volume that grows as floater.position
increases. Since implementing thermodynamics might be complex, we will tune this with a
parameter (e.g. use_isothermal = True/False and maybe a percentage gain factor). The
important outcome is that with H2 on, the ascending floats do more work – we see a higher net
torque or a burst of power output during certain parts of the cycle .
Implementation Details: We add logic in the floater update: if H2 enabled and floater is buoyant,
adjust its buoyant force. This could be as simple as: floater.buoyancy *= (1 +
thermal_boost) where thermal_boost could be a small fraction or a function of time. Or update
the volume used in buoyant_force calc: e.g., effective_volume = base_volume * (1 + β *
(current_height/tank_height)) to linearly increase volume with height. We should be careful
not to double-count energy (if we output efficiency calculations, the compressor input might be
lower if not all water was expelled initially). The simulator could integrate the buoyant force over the
ascent to show how much extra work was gained vs. the adiabatic case . Initially, we might skip
detailed thermodynamic calc and use a simplified boost that a coder can implement easily, with
comments that this represents the isothermal expansion effect.
User Controls & UI: We will tie the H2 control (e.g., a button or checkbox in UI) to enabling this
effect. If using a parameter like thermal_expansion_coeff or a boolean flag, the
/set_params endpoint will toggle it . The front-end “H2: Thermal Amplification” button
currently just shows a description ; in the upgraded version it will also initiate the physics change.
We will ensure that when H2 is on, the simulation logs show increased efficiency or power. For
example, one expected result: the peak torque from a buoyant floater might be higher or sustain
longer than without H2. This should reflect in the output charts (e.g., a higher power spike),
consistent with the intended “kick” . We will validate that turning H2 off returns the buoyant force
behavior to normal (for code stability).
H3 – Pulse-and-Coast Drivetrain (Flywheel & Clutch): The third enhancement (H3) involves the
mechanical side: using a flywheel to store energy and a clutch to intermittently engage the
generator, allowing the system to pulse during high-torque moments and coast through low-torque
parts . Implementing H3 requires adding rotational dynamics to the simulation:
We introduce a concept of angular velocity (ω) for the chain and attached rotating components. In
the simplest model, the entire loop of floaters and sprockets can be treated as a rotating belt system
with a certain moment of inertia (I). We will also include a flywheel inertia if H3 is active (adding to I)
and possibly allow the generator load to be toggled.
Without H3 (Conventional): the generator is continuously engaged, providing a constant resisting
torque proportional to electrical load. In simulation, we might model this as a damping torque that
38
39 40
•
8
•
33
41
39
•
42 43
•
•
6
always opposes motion. If the net buoyancy torque is not enough to overcome it, the system will not
sustain motion (which is why a conventional buoyancy engine might show net negative output) .
We can simulate a fixed opposing torque or simply observe that net energy is negative when H3 is
off and no special strategies are used, as our earlier analysis indicated.
With H3: We allow the clutch to disengage the generator at strategic times, letting the floaters
accelerate the system (increase ω) without doing work against the generator. Then, when a burst of
buoyant force is available (e.g., multiple floats lifting strongly), the clutch engages and the
flywheel+chain’s stored kinetic energy is transferred to the generator in a pulse. To implement this,
we will add a control logic that modulates the generator torque: essentially a function of time or
cycle progress. For example, we could specify that during certain portions of the cycle (when a fresh
floater has just been injected and starts rising), the generator is disengaged (torque = 0, allowing
free acceleration), and after the float reaches mid-height, we engage (apply torque to extract energy
and slow the system). In code, this could be a simple conditional: if kick_phase is true, set
generator_torque = 0; else generator_torque = some value (or a function like proportional to ω to
simulate generator loading). The demo’s animation logic simulated this with a boolean kick
triggered at two intervals in the cycle – we will make it more physics-based but the idea is
similar.
We also model the flywheel: essentially added inertia so that when the generator is disengaged, the
system can speed up (store energy kinetically), and when engaged, that stored energy can be
released as output. In code, we’ll have a parameter I (moment of inertia). We update ω each timestep
by: α = (τ_net - τ_load) / I. Here τ_net is torque from buoyancy minus weight (as calculated), and
τ_load is the resistive torque from generator (which we modulate). With a larger I (flywheel on), ω
changes more slowly, smoothing out the motion (i.e., floaters won’t instantly accelerate/decelerate).
The clutch basically makes τ_load = 0 in certain intervals. We will likely implement H3 with a simple
toggle or even automatically: if H3 on, periodically set generator_engaged = False around the
peak buoyancy moments. For a more advanced approach, we could use sensor input (e.g., detect
when a new floater is injected and just starting to rise – a good time to disengage so it can gain
momentum, then engage once it’s up).
Power and Efficiency: With this pulsing implemented, we expect the simulator to show higher net
output during engaged periods and minimal negative work during disengaged periods, improving
overall efficiency. The code will log instantaneous power as before; with H3, that power might come
in bursts rather than a steady small output . We will integrate power over time to compute
total energy output vs input for a cycle to verify the benefit.
Integration Details: We will add any new state variables needed (e.g., sim.angular_velocity ,
sim.inertia , sim.generator_torque etc.). The front-end controls can have an H3 button;
when activated, it sets a flag in backend to use the pulse logic. We may also visualize flywheel speed
– e.g., in the 3D scene the flywheel object could spin according to ω, and perhaps glow when storing
energy (the demo did change emissive color with speed) . We can feed the flywheel rotation
speed from simulation to the front-end via SSE (the Stage 2 SSE already allows streaming custom
fields like per-floater data ; we can add sim.omega or similar). The power gauge in the UI will
now be driven by actual sim.power values rather than predefined numbers, so it will reflect the
negative/positive and pulses of power properly.
Ensure Stability: When implementing H3, we should test that toggling the generator torque doesn’t
cause numerical instability. Likely we’ll keep Δt small (e.g., 0.1s or 0.05s) to accurately capture
acceleration. We’ll also ensure that when H3 is off, we default to a continuous moderate generator
load such that the system reaches a steady state (possibly zero or negative net output as expected).
When H3 is on, we simulate at least one full cycle to evaluate net gain.
44
•
45 46
•
•
47 40
•
48 49
50
•
7
Integration with the Existing Codebase
Upgrading the physics will require changes primarily in the simulation backend code, but we must do so
in a way that integrates cleanly with the current structure. Here’s how we will ensure a seamless integration:
Module Structure: The codebase should be organized into modules separating physics from the
web interface. According to the earlier blueprint, we have a simulation/physics.py ,
simulation/engine.py , etc. . We will add our new physics functions (buoyant_force,
drag_force, etc.) to physics.py (if not already present) and ensure they are used in the engine’s
simulation loop. The Stage 1 upgrade created a simulate() loop in engine.py to iterate over
time steps . We will modify that loop (or the sim.step() function in an OOP design) to
perform per-floater updates as described. For clarity and maintainability, we will likely implement a
Floater class (as suggested in Stage 2) to encapsulate each floater’s properties and an update
method . This class can reside in simulation/engine.py or a new simulation/
floater.py . It will have fields like position, velocity, volume, mass, state, etc., and an
update(dt, params) that calculates forces and updates its own state. The engine will hold a list
of Floater instances (e.g., sim.floaters ).
Replacing Legacy Logic: The existing code (legacy) may have had a single-cycle calculation or even
hardcoded animations (as in the 3D demo). We are replacing that with a continuous simulation
loop. The real-time loop from Stage 1 and Stage 2 is already designed to yield data at each time step
. We will plug our physics calculations into this loop. Concretely, where the legacy might have
just computed one output or used dummy values (like fixed speeds or preset power outputs), we
now compute actual forces each iteration. For example:
In the loop, instead of force = compute_force(state) that may have been simplistic, we will
do: iterate through sim.floaters , for each compute F_net (using our physics functions) and
update its state. Then compute total_torque from all floaters. Then update any global state like
angular velocity.
If the old code had compute_power() assuming constant speed, we replace it to calculate
sim.power = sim.torque * sim.angular_velocity at each step (ensuring units
consistency).
We must also maintain any legacy output format expected. For instance, if previously the results
were stored or plotted, we keep collecting time-series of position, velocity, torque, power, efficiency,
etc. The Stage 1/2 instructions explicitly said to store outputs each step . We will continue that:
e.g., append to sim.log a dict of metrics each timestep. This ensures features like CSV download
remain functional (the Stage 2 provided a /download_csv route for the log ).
Callbacks and APIs: We will add or update any Flask routes needed to control the new physics. The
UI likely has controls for enabling H1, H2, H3 (perhaps as buttons). We might implement these as
part of the simulation start or via separate API calls. The Stage 2 plan suggests a /set_params
POST endpoint to update parameters like nanobubble_frac, thermal_coeff, etc. on the fly . We
will implement that, so that when the user toggles a feature or slider in the frontend, an AJAX call
updates the back-end parameter immediately. Our simulation loop will read those updated
parameters on the next iteration (since we store them in a sim object or a global config). For
example, if the user clicks "H1", we send { nanobubble_frac: 0.3 } (or simply a boolean to
enable it with a preset fraction) to /set_params , and our backend sets sim.nanobubble_frac
•
51
52 53
54 55
•
56 57
•
•
•
58
59 60
•
32 61
8
accordingly. The next loop will then use the modified density for water as described. This real-time
interactivity is crucial to allow experimentation without restarting the simulation.
We also ensure the /stream SSE endpoint continues to function. In fact, we will expand the data it
streams. Currently it was designed to send time, position, velocity, torque, power, etc. as JSON
. We will now include possibly multiple floater positions or other info. For performance, we might
not stream every floater’s full state by default (if there are many floaters, that’s a lot of data). But we
can stream a summary: e.g., positions of a few representative floaters or just the lead floater; or
stream the angular position of the chain and maybe highlight one floater in the front-end. The
Stage 2 snippet shows including a list of floaters with pos, vel, buoy, drag in the SSE data – this is
a good approach in development. We can implement that and perhaps limit to sending every Nth
floater to keep payload small. The front-end can use this to update charts or even the 3D view.
3D Visualization Integration: The existing 3D simulation ( simulation3d.html ) currently runs its
own animation loop independent of physics, with hardcoded outcomes. As a final polish, we can
integrate the backend physics with the 3D front-end. This would mean instead of internally
computing floater movement in JavaScript, we subscribe to the SSE stream in the front-end and
update the Three.js scene objects according to the positions from the physics engine. For example,
each SSE message gives an array of floater positions; the JS could iterate through floaters[i]
objects and set object.position.y = data.floaters[i].pos (and maybe toggle colors if
buoyant or not). This would synchronize the 3D visualization with the physics simulation in realtime,
providing a true “digital twin” feel. It is an integration task: we add an EventSource('/
stream') in the 3D page and use the data in the onmessage handler to update the scene. We
must disable the existing manual animation in that mode to avoid conflict. Since this is a more
advanced step, we can plan it as an optional integration if time permits. Even without tying to 3D,
the physics engine outputs will be observable via charts and numeric logs (which might be
sufficient). But for a world-class simulator, linking the two would be ideal.
Legacy Feature Parity: We ensure that nothing is lost. For example, the current UI legend, control
buttons, and info panels (which describe each mode) should still make sense. We can update the text
if needed to reflect that these modes are now actively simulated rather than illustrative. All previous
capabilities (camera controls, reset button, etc.) remain as they were – e.g., Reset should still reset
the view and now perhaps reset the simulation state (we might tie the reset button to reinitialize the
simulation, clearing velocities and resetting floaters to start positions). That could be done by calling
a backend route to reinitialize, or by simply reloading the page. We prefer a smoother approach:
implement a /reset endpoint in Flask that re-instantiates the Simulation object and the front-end
can reconnect to a fresh stream. This way the user can start/stop easily.
Data Logging and Analysis: We continue to log all relevant data. In fact, with new physics, we might
log more: e.g., compressor energy used per injection (so we can compute net energy), efficiency at
each cycle, etc. The plan is to accumulate data in sim.log list (time, torque, power, maybe total
energy, etc.) every step . We have a download CSV feature as per Stage 2; that will be updated
to include any new fields we added (like if we add “floaters_count” or “H1_on” flags, etc., though not
necessary). Before finalizing, we will verify that the log outputs make sense and match expectations
from physics (for example, check that over one full cycle, energy_out - energy_in ≈ 0 for
conventional mode to confirm conservation, and >0 for combined H1/H2/H3 if the claim is it
produces net power).
•
62
63
50
•
•
•
64 60
9
Performance Considerations: Given the simulation runs in real-time, we ensure our loop is
efficient. Using Python with potentially many floaters might be a concern; we can mitigate by using
NumPy arrays for vectorized force calculations if needed. The blueprint even suggested using SciPy
or PyChrono for more advanced physics , but to keep it straightforward for a normal coder,
our plan sticks to custom computation (which is fine for tens or hundreds of floaters). We will set a
reasonable default number of floaters (e.g. 60 as in design). If performance lags, options include
lowering the update frequency (e.g., stream every 0.2s instead of 0.1s) or simplifying drag calcs.
These adjustments can be documented.
Step-by-Step Upgrade Plan
Finally, here is a stepwise guide a developer can follow to implement the above physics upgrades in order:
Define Physics Functions and Constants: In the physics module, add functions for
buoyant_force(volume, rho) , drag_force(Cd, area, vel, rho) , and any constants (g,
rho_water, default_Cd) if not already defined . Also define any initial parameters for H1, H2,
H3 (e.g., nanobubble_frac = 0.0 , thermal_boost = 0.0 or booleans,
flywheel_inertia , etc.). These will be adjustable later, but start with defaults (H1 off, H2 off, no
flywheel).
Introduce the Floater Data Structure: Create a Floater class (or equivalent structure) to hold
each floater’s state . Properties should include: position (vertical or along loop), velocity,
volume, cross_area, mass_empty, mass_air, mass_water, isBuoyant (bool), and maybe a reference to
whether it’s on ascending side (this could be inferred from position relative to half-loop). Also include
a method update_forces(dt, params) that:
Determines current fluid density (if H1 and floater on descent, use reduced rho).
Computes buoyant force (if isBuoyant) or net buoyant effect if not (per earlier logic).
Computes weight force (m*g).
Computes drag (with sign).
Sums to get net force F_net.
Updates acceleration, velocity, and position (Euler integration).
Use small time-step dt (e.g., 0.1s or as set in params) so integration is stable . If using a global
chain approach, you might skip per-floater velocity update and do a global velocity – but updating
each for visualization is fine.
Initialize Floaters: In the simulation engine (when a simulation starts or resets), create the list of
floaters. For example, if 60 floaters, distribute them evenly around the loop. You can assign initial
positions linearly spaced and alternate their state (half buoyant, half heavy) so that the loop is in
equilibrium to start (e.g., all ascending ones buoyant, all descending heavy). Each floater’s initial
velocity can be 0. The arrangement might be like: index 0 at bottom just injected (buoyant), floaters
1...N/2 on ascent, N/2 at top venting, etc. Or simply start all heavy and stationary and then begin
injecting one by one – but an even start avoids a big transient. This setup ensures a realistic starting
condition.
•
65 66
1.
67 9
2.
68 54
3.
4.
5.
6.
7.
8.
56 24
9.
10
Implement the Simulation Loop: Modify engine.py ’s main loop ( simulate() or the generator
in SSE route) to iterate over time. At each time-step:
Loop through each floater in sim.floaters and call its update method to compute forces and
update positions/velocities for this small step. However, to ensure the chain moves as one, you
might want to compute the net torque first, update a shared angular acceleration/velocity, and then
impose that back on floater velocities. A simpler method for now: assume all floaters have the same
velocity = sim.chain_velocity, update that one velocity by net force, and then just move all floaters by
that amount (this enforces the constraint exactly). The net force to use would be sum of all floaters’
F_net (projected to vertical motion) divided by total mass (or use torque and inertia for rotation). This
is more advanced; initially, you can allow floaters to move independently but you may notice it
violates the chain constraint slightly. If that’s the case, adjust to a linked motion model later.
Check for state transitions: after updating positions, see if any floater crossed the bottom or top
threshold. If so, flip its state (buoyant <-> heavy) accordingly . When flipping to buoyant at
bottom, you may want to zero its velocity or give a small upward push. When flipping to heavy at
top, perhaps set velocity to match the chain (they should continue moving downward smoothly – if
we treat chain unified, this is automatic).
Apply H3 logic: Determine if at the current time-step the generator is engaged or not. This could be
based on cycle progress or a simple periodic toggle. For example, if using cycle time T, you might
disengage for first 20% of cycle, engage for next 30%, etc., based on where you predict buoyant
force peaks. The blueprint suggests using sensors or an RL agent eventually , but we can
hardcode a pattern for now (or even detect torque sign changes: e.g., when net torque becomes
positive, engage generator to take that power). Implement this by adjusting sim.torque or better,
subtract a generator_torque term from net torque when engaged. A very simple approach is: if
H3 on, skip generator load (i.e., let system accelerate) until a floater has ascended a certain distance,
then impose a generator load equal to a fraction of the current torque or a constant. This yields the
pulse-and-coast effect.
Update chain angular velocity: Using the net torque (post-generator), update angular velocity:
omega += (torque / I) * dt . Then you can update an angular position if needed or just use
omega to compute how far the chain moved. However, since we already updated floaters via their
own calcs, we may not need to separately compute omega for motion – but we do need it for power.
So maintain sim.omega . Optionally, cross-check that if floaters moved inconsistently with omega,
adjust them. (This part can be iteratively refined. In a basic implementation, you might not explicitly
use omega to drive motion but rather derive it from one floater’s velocity.)
Calculate power and efficiency: Compute instantaneous generator power = generator_torque *
omega (if generator_torque is engaged; if disengaged, power = 0 output at that moment, though
system is gaining kinetic energy). Also compute compressor power input when injecting air: if an
injection happened this step, estimate energy used (e.g., use pressure * volume or a fixed value per
injection) and account for it as negative (input) power during that moment. Efficiency can be
computed as (output energy / input energy). These metrics can be accumulated or smoothed over a
cycle. Append the current values (time, net torque, omega, output power, etc.) to the results list
or sim.log for logging .
Yield data for SSE: Format the JSON with the desired fields (time, power, torque, efficiency, maybe
positions of a few floaters or the first floater, etc.) and yield it with the SSE data prefix . A short
time.sleep(dt) can be used to control frame rate (or let the loop run as fast as possible if dt
is small and rely on network delay).
10.
11.
12.
3 26
13.
69 70
14.
15.
58 64
16.
7
71
11
Frontend Updates (Charts and Controls): Ensure the HTML template has input controls for the new
parameters and that they fire AJAX requests to the backend. For example, add a checkbox or toggle
for “Enable H1 (nanobubbles)”, which calls /set_params with nanobubble_frac =some default
like 0.2. Similarly for H2 and H3 (H3 might toggle a mode rather than a numeric value). Additionally,
set up Chart.js charts if not already done to plot torque, power, etc. in real-time . The SSE
EventSource on the frontend will push new points to these charts on each message . We
should add charts for at least: Torque vs time, Power vs time, perhaps Efficiency vs time. We can also
have a chart or indicator for chain speed (rpm) or for a single floater’s position over time to see the
cycle. The existing analysis page had some charts focusing on “airflow vs needed” etc., but those
might not be real-time. Our focus is the simulation output now.
3D Visualization Integration (Optional but Recommended): Upgrade the Three.js visualization to
reflect real physics. This can be done by either embedding the 3D view in the main simulation page
or by modifying simulation3d.html to connect to the SSE stream. For a seamless result, it might
be easier to integrate the 3D canvas into the Flask template and have one unified interface (so the
user doesn’t have to start an animation manually – it just runs). However, doing so is more involved.
As an alternative, you can keep the separate 3D page but add a small script in it:
On clicking “Conventional Cycle” or others, instead of running the hardcoded animation, initiate the
SSE connection to the running simulation (ensuring the simulation was started). Then listen to
events: for each event’s data.floaters list, update the floaters meshes positions and colors.
You’d also update the power gauge UI from data.power instead of using the fake logic.
Essentially, the front-end becomes a dumb renderer of whatever the backend is doing. This ensures
no divergence between what the physics says and what is shown.
If combining is tricky, at least ensure that the plan to upgrade physics doesn’t break the ability to
show those animations. Perhaps we initially let the 3D remain as-is for concept demonstration, and
focus the live results in charts. A world-class simulator eventually has them combined, so it’s a goal
to aim for after the physics core is solid.
Testing & Validation: After implementing, perform tests for each scenario:
Conventional (H1=H2=H3 off): The simulator should show that no net power is produced (likely
negative after accounting for compressor). Check that floaters reach a steady cycling motion or
identify if it stalls (if generator load too high, it might stall – in which case perhaps simulate an
external drive just to keep it moving for analysis). Ensure forces look balanced (e.g., buoyant side vs
heavy side). This validates basic buoyancy and weight calcs.
H1 on: Verify that descending floaters fall faster or easier. Look at torque: ideally the heavy side
contributes a bit more (or wastes less energy) so net output is slightly improved. Ensure no
instability (very low rho could cause floats to drop too fast; keep fractions reasonable).
H2 on: Check that buoyant force or output power is higher during ascent. Possibly you’ll see a spike
in torque when a floater is near bottom (if we gave a kick) or gradually increasing torque as it rises.
Compare energy output of a cycle with and without H2 to see if it matches expectation (should be
higher with H2 at the expense of presumably same compressor input).
H3 on: This is a bit complex to test. Watch that during disengaged phase, ω (speed) indeed
increases, and during engaged phase, power output spikes and ω drops some. Over multiple cycles,
see if the average power out minus compressor power in is positive (the claim of net generation). If
17.
72 73
74 75
18.
19.
20.
21.
22.
23.
24.
25.
12
the numbers are unrealistic (e.g., output energy >> input), double-check formulas to avoid any
hidden energy creation not justified by the hypotheses. The simulation should obey energy
conservation except for the hypothesized gains (which themselves must be physically plausible).
All tests: ensure the system remains stable (no runaway increasing speed unless that’s expected
under no load; we may add a gentle damping to represent friction). Also verify that the real-time
performance is good (the loop can iterate at the intended rate without lag; if not, consider increasing
dt or reducing complexity).
Documentation and Cleanup: Finally, document the new code with comments so any developer or
researcher can understand the implementation. Use clear naming (e.g., nanobubble_frac ,
use_isothermal , use_flywheel ) for toggles. Remove any truly obsolete code from the legacy
system that is no longer used (for instance, if we fully integrate the 3D view with physics, you can
remove the old dummy animation logic, but do so carefully after verification). The guide itself (this
document) can be saved as a Markdown file in the repo for future reference. It will serve as both a
development roadmap and a user manual for the physics features.
By following these steps, a developer should be able to upgrade the KPP simulator’s physics in a structured
way. The end result will be a comprehensive, professional-grade simulator: one that not only visualizes
the KPP concept but quantitatively simulates its performance under various enhancements. All
enhancements H1, H2, H3 will be integrated per best practices, and the simulator will remain interactive
and extensible for further experiments (like trying different numbers of floaters, depths, etc.). Each module
will work in concert – floaters providing forces , the injection/vent system providing state control , the
drivetrain converting force to power with clutch control – to mimic the real KPP operation as faithfully as
possible in real-time. This upgrade will position the simulator as a valuable R&D tool going forward,
enabling testing of control strategies and validating the KPP concept against the laws of physics.
Sources and References
KPP Physics and Forces (buoyancy, drag, torque): KPP Simulator Blueprint
Full Floater Cycle and Control (injection, venting, drivetrain): KPP Algorithm Blueprint
Hypotheses H1, H2, H3 descriptions: KPP R&D Enhancements and Implementation Guide
Real-Time Simulation Loop and SSE integration: Stage 1 & 2 Guides
Demo Values and Animation Logic for comparison: 3D Simulator Code (used to ensure our
physics outputs align qualitatively with expected behavior).
Flask-Based KPP Simulator
Implementation Blueprint.pdf
file://file-3HVVUCDUgivcJmxNAkMx7U
Kinetic Power Plant (KPP) R&D Simulator Algorithm Blueprint.pdf
file://file-DEKb2MeVDubPyHbxBzQBuC
Stage 2 Upgrade_ Real-
Time Simulation Implementation Guide.pdf
file://file-UVKDQgJCEP8LPwraen4Q7s
26.
27.
76 3
43
• 1 2
• 3 4
• 5 77
• 24 7
• 39 40
1 2 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 28 29 51 67
3 4 5 26 42 43 65 66 69 70 76
6 7 27 30 32 33 38 50 54 55 57 59 60 61 63 64 68 71 72 73 74 75 77
13
Stage 1 Implementation Guide_ Real-Time Simulation Loop Upgrade.pdf
file://file-GpMuyKuXh2AZkbDqvhrgVu
simulation 3d.html
file://file-CexdUHw7U4aRDqQPUWiPWg
24 25 52 53 56 58 62
31 34 35 36 37 39 40 41 44 45 46 47 48 49
14