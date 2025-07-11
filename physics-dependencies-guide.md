KPP Simulator Physics Layer Upgrade Guide
 Overview and Approach
 The Kinetic Power Plant (KPP) simulator is being upgraded to replace its legacy physics logic with modern,
 high-fidelity models. The simulator’s code is organized into modular components (e.g. 
drivetrain.py , 
pneumatics.py , 
control.py ) under a 
1
 floater.py , 
models/ package , corresponding to
 real KPP subsystems. In the KPP concept, an endless chain of floaters moves through a water-filled tank:
 f
 loaters are filled with air at the bottom (becoming buoyant and rising) and emptied at the top (becoming
 heavy and sinking), causing continuous chain rotation that drives a generator . Key subsystems include
 Floaters & Chain Mechanics, Water/Fluid Environment, Air Injection & Pneumatics, Drivetrain & Generator,
 and the Control system . 
2
 3
 4
 This guide outlines a staged implementation plan to integrate advanced Python libraries into each
 subsystem, aligning with the existing structure and ensuring backward compatibility with the current UI
 (Flask/Chart.js or Dash) and data outputs. We will proceed subsystem by subsystem, verifying each upgrade
 in isolation before full integration. The mapping of new technologies to subsystems is as follows:
 • 
• 
• 
• 
• 
Floaters & Chain: Use PyChrono for multibody dynamics and real-time physics, with PyDy/SymPy if
 needed for deriving or validating equations.
 Water Environment (Hydrodynamics): Leverage FluidDyn (and built-in physics) for fluid flow
 effects (drag, buoyancy adjustments) and use CoolProp for accurate fluid property data if needed.
 Air Injection & Pneumatics: Use CoolProp for thermodynamic properties of air/water and SimPy
 for event-based simulation of air injection timing and compressor operation.
 Drivetrain & Generator: Use PyChrono to simulate mechanical rotation (shaft, clutch, flywheel) and
 integrate PyPSA to model the electrical generator and power output.
 Control System: Use SimPy (and possibly Python async features) for scheduling control events
 (valve timing, clutch engagement) and allow future use of advanced strategies. Consider JAX/
 Numba for any performance-critical calculations (e.g. vectorized physics updates) to utilize GPU or
 multithreading as needed.
 Throughout each stage, we will maintain the simulator’s real-time update loop and UI communication.
 Legacy calculations will be phased out one module at a time – ensuring that at each step the simulator’s
 outputs and behavior remain consistent (or intentionally improved) and the existing Flask/Dash interface
 remains responsive. We will preserve the current APIs where possible, introducing new interfaces only when
 necessary to support the advanced models. A controller will manage the simulation loop in a separate
 thread or asynchronous task, so that heavy physics computations do not block the UI thread . The
 following sections detail the upgrade plan for each subsystem.
 Stage 1: Floater & Chain Mechanics (PyChrono Integration)
 5
 Subsystem Scope: Floaters and Chain Mechanics – This module represents floaters moving on the chain loop
 through water, experiencing upward buoyant force on ascent and weight on descent. It converts the net
 1
force from all floaters into chain tension and shaft torque . In code, this logic is in
 3
 models/floater.py (and possibly a 
1
 chain.py ) . Upgrading this subsystem will introduce a
 multibody physics engine for realistic dynamics.
 • 
6
 Functional Replacement Plan: Replace the simplified kinematic and force-balancing logic of
 f
 loaters/chain with a PyChrono-based physics simulation. PyChrono (the Python wrapper of Project
 Chrono) can simulate constrained rigid bodies, joints, and forces in real time . We will model
 each floater as a rigid body attached to a chain or guided path. The chain itself can be represented
 either as a series of linked bodies (for high fidelity) or abstracted as a continuous belt that constrains
 f
 loater motion along a loop. The legacy approach likely computed net force per floater and summed
 them; in the new approach, PyChrono will compute interactions: buoyant and drag forces (applied as
 external forces) cause floaters to accelerate, and a constraint or joint will translate their motion into
 rotation of the chain sprockets. This yields realistic dynamics including inertia, acceleration, and
 tension in the system. We will use PyChrono’s multibody dynamics solver to handle the equations of
 motion instead of manually coding Euler updates . (For verification or simpler cases, PyDy/
 SymPy can be used to derive equations of motion for a single floater and chain segment, but
 PyChrono will handle the full multibody simulation directly.)
 7
 8
 • 
• 
Library Integration Steps: First, install and import PyChrono (available via Anaconda/Pip) and
 initialize a Chrono simulation system within the simulator. Define Chrono bodies for each floater
 (with appropriate mass, volume, and geometry for collision if needed). Define a path or constraints
 to mimic the chain: one approach is to use two sprocket wheels (top and bottom) and link floaters via
 a revolute joint to the chain path. If simulating actual chain links is too slow, we can constrain
 f
 loaters to move along a fixed loop path (e.g., using a Chrono 
10
 ChLinePath or a pair of guide rails
 on either side). Apply buoyant force to each floater’s body each simulation step: e.g., for a
 submerged floater, apply an upward force = ρ_water * V * g (Archimedes’ principle) , and for
 water-filled (descending) floaters apply weight and reduced buoyancy. Similarly, compute drag force
 = ½ * C_d * A * ρ * v² opposite to motion and apply it via Chrono’s force APIs. We will also add a
 Chrono revolute joint for the chain sprocket/shaft, so that as floaters move, they drive the rotation of
 the sprocket. This may involve coupling floater motion to the sprocket via constraints or a motor
 element in Chrono. Chrono’s flexibility with joints, motors, and constraints will allow modeling a one
way bearing or slip (freewheel) later in the drivetrain stage . The integration steps are: (1) create
 Chrono physical objects for floaters, chain/shaft, and define their initial positions (e.g., equally
 spaced floaters around the loop); (2) apply gravitational acceleration in the Chrono world and a
 custom force callback for buoyancy and drag on each floater; (3) each simulation tick, advance the
 Chrono simulation by Δt (e.g. 0.02s) which updates positions and velocities; (4) retrieve the sprocket
 angle/velocity to pass to the drivetrain, and floater positions for visualization.
 11
 9
 API / Interface Changes: Maintain a similar interface for the rest of the code by wrapping the
 PyChrono simulation inside the Floater/Chain module. For example, the 
Floater class can become
 a lightweight wrapper around a Chrono body, providing methods like 
get_position() or
 get_velocity() that internally query the Chrono state. The simulation loop (perhaps in
 simulation.py or 
engine.py ) might previously call 
Floater.update(dt) for each floater to
 manually integrate motion; now it will call a single Chrono integration step for all floaters at once,
 then update any necessary state variables. We ensure that 
drivetrain can still obtain the net
 torque or chain speed – for instance, we might add a method 
compute_chain_torque() that
 uses Chrono results (sum of forces on ascending vs descending floaters times sprocket radius) if
 2
needed. If the original code tracked floater positions in a list or array for animation, we will adapt it
 to pull positions from the Chrono simulation at each time-step. Backwards compatibility: We keep
 input and output data structures the same. For example, if the UI expects an array of floater angles
 or a total chain rotation angle each frame, we will populate that from Chrono. Internally, time
stepping may shift from an explicit Python loop to Chrono’s internal solver, but we encapsulate this
 so that external modules (control, UI) are unaware of the change except for improved realism. 
• 
• 
Performance Tuning: Using a compiled physics engine like Chrono will significantly increase realism
 but may incur performance costs, especially if many floaters and chain links are simulated. To
 mitigate this, we will tune the model complexity: for instance, using a simplified chain model (or a
 single “belt” constraint) rather than dozens of rigid link bodies, to reduce the number of contacts and
 constraints being solved. Chrono is written in C++ and is optimized; it can handle multibody
 simulations efficiently and even supports parallelization for large scenarios . We should enable
 Chrono’s parallel solver for constraint handling if available, and consider using a larger integration
 step if high frequency dynamics (like small vibrations) can be neglected (ensuring stability of the
 solver). If performance still lags, one strategy is to vectorize or parallelize any custom force
 computations: e.g., computing drag on all floaters using NumPy at once, or offloading calculations
 to GPU via libraries like JAX/Numba for acceleration. The modular design allows identifying
 bottlenecks (say, drag force on each floater) and optimizing them in isolation . For example, if
 computing buoyancy and drag for each floater each step becomes expensive for large numbers, we
 can utilize NumPy arrays or Numba to compute all forces in a batch . Chrono’s integration step
 itself is in C++, so the main overhead is Python<->Chrono interactions; we minimize per-step Python
 calls by applying forces in a single callback function if possible. In summary, we anticipate real-time
 performance with a moderate number of floaters (dozens) and a time-step ~20 ms ; if needed, we
 will adjust detail levels or leverage Chrono’s parallelism to keep the simulation running in real time.
 12
 13
 5
 13
 14
 Real-Time Update & UI Integration: The floaters’ new physics will be integrated with the UI such
 that the user sees the same or improved outputs. Each simulation step, after advancing Chrono, we
 will collect updated floater positions (and perhaps velocities) to drive the on-screen animation (e.g.,
 moving markers in Chart.js or a Plotly graph). Because Chrono uses its own time integration, we
 must ensure the simulation loop remains synchronized with the real-time UI update interval. Ideally,
 we run the Chrono step at a fixed Δt and the UI at a refresh rate (perhaps every N steps or a few
 times per second). A SimulationController will run the physics loop in a background thread and
 stream out data asynchronously , so the UI (Flask/Dash) remains responsive. We’ll ensure thread
safe communication of data (e.g., using a shared queue or Flask server-sent events). The UI should
 not require changes: for example, if previously the floater positions were computed and then fed to
 a chart of chain angle or displayed as an animation, we continue providing the same data (just
 coming from Chrono now). If using Dash, a dcc.Interval callback can call a function that fetches the
 latest simulation state. For Chart.js with SSE, the simulation thread will emit JSON including floater
 angles, chain speed, etc., at regular intervals. In either case, the user shouldn’t notice anything
 except smoother physics. The introduction of Chrono allows future 3D visualizations (via Three.js or
 WebGL), but initially we will keep the existing 2D representation – just updating it with more
 physically-accurate motion data. We will rigorously test that the system still runs in real-time (or
 faster) so that the UI charts update without lag. If the new physics introduces slight delays (due to
 computations), we may decouple the visual update rate from the physics tick rate (e.g., run physics
 at 100 Hz but send data to UI at 20–50 Hz). Crucially, all existing simulator functionality – like
 pausing, resetting, or changing parameters on the fly – will be preserved. The Controller will mediate
 3
15
 any real-time parameter changes: if the user adjusts a floater property or toggles a hypothesis, it will
 update the Chrono model accordingly even while running . By the end of this stage, the floaters
 and chain behavior will be running on a robust physics engine, laying the groundwork for upgrades
 to other subsystems.
 Stage 2: Hydrodynamic Environment (Fluid Properties & Drag)
 Subsystem Scope: Water Environment (Hydrodynamics) – This component models the surrounding water and
 f
 luid effects on the system. It provides water properties (density, viscosity) and computes forces like drag on
 moving floaters. It also incorporates the KPP’s H1 enhancement (nanobubble injection to reduce water
 16
 density/drag) . In the current structure this is likely in 
17
 environment.py (or part of 
floater.py
 calculations) . The upgrade will improve accuracy of fluid forces and allow dynamic fluid property
 modeling.
 • 
• 
18
 19
 Functional Replacement Plan: We will enhance the fluid dynamics modeling by integrating
 advanced fluid property libraries and preparing hooks for higher-fidelity simulations. In the legacy
 simulator, drag and buoyancy were probably calculated with simple formulas using constant
 coefficients. Now, we will use CoolProp for accurate thermophysical properties of fluids and
 potentially FluidDyn (or its sub-packages) for more advanced fluid flow computations. CoolProp is
 an open-source database of fluid properties (density, viscosity, etc.) with formulations based on high
accuracy reference data . Using CoolProp, we can obtain water density as a function of
 temperature or pressure, which could be important if we simulate temperature changes (for H2
 effects) or depth-dependent pressure. We can also retrieve air properties for bubbles if needed. For
 drag force, we will initially continue using the standard quadratic drag law, but we will calibrate the
 drag coefficient (
 C_d ) and possibly include Reynolds-number dependence or other effects if
 needed. FluidDyn can be introduced to manage more complex fluid dynamics tasks – for example, if
 we wanted to simulate unsteady flow or wake effects, or just to follow best practices in structuring
 f
 luid simulation code. FluidDyn is a framework offering tools for fluid simulations (e.g., 
20
 21
 fluidsim )
 and data processing in Python . While we do not plan to run a full CFD in real-time, we design
 the environment module such that one could swap out the simple drag model for a more advanced
 one (even one calling an external CFD or a precomputed lookup table of drag forces). The functional
 plan is to treat the Environment as the authoritative source of fluid properties and forces: floaters or
 other modules will query it for water density, buoyancy forces, and drag forces. With H1
 (nanobubbles), instead of a fixed parameter tweak, we can model it as a reduction in effective water
 density or viscosity. This effect can be toggled via a parameter and the environment module will
 apply the physics accordingly (e.g., 
rho_water = base_rho * (1 - H1_factor) ). Overall, this
 stage upgrades the environment from a static placeholder to a dynamic, configurable fluid model
 that supports the KPP enhancements.
 Library Integration Steps: Integrate CoolProp by installing it (via pip) and importing its 
PropsSI
 function for fluid properties. In the environment module, we will use CoolProp to get water
 properties: for instance, 
rho = PropsSI("D", "T", T_water, "P", P_water, "Water") for
 density at a given temperature and pressure. If the simulator assumes standard conditions, we
 might simply call 
PropsSI("D", "T", 293.15, "P", 101325, "Water") once for density
 ~1000 kg/m³. The key benefit is if we later incorporate temperature changes (e.g., H2 thermal effect
 warming the water), CoolProp can give updated density or heat capacity. We also use CoolProp for
 air properties in the H2 context (e.g., air density inside floaters, see Stage 3). Next, if using FluidDyn/
 4
Fluidsim for drag: we could use it to validate our drag formula or to organize our code (FluidDyn
 emphasizes clean, modular code for fluid dynamics). For example, if FluidDyn has a function for drag
 coefficient vs Reynolds number, we might use that instead of a constant. Integration might be as
 simple as using a FluidDyn utility if available, or just structuring our code in a similar fashion (since
 FluidDyn’s core package 
fluiddyn provides utilities for numerical computations, we ensure
 compatibility if we later plug in a FluidDyn simulation). Additionally, we ensure the floater bodies in
 Chrono are assigned fluid interaction parameters. Chrono itself doesn’t simulate fluids, but we
 already apply forces manually. We could enhance this by perhaps implementing a fluid drag
 module: e.g., maintain a list of floaters and in each step have Environment.compute_drag(floater) ->
 force. This keeps physics modular (floaters ask environment for drag) . If we decide to
 incorporate external CFD data, we might design the environment such that it can fetch precomputed
 drag forces from a table or even call an external routine (in a separate thread to not stall the main
 loop). The integration steps are: (1) Refactor drag force calculation into environment module (if not
 already separated); (2) Use CoolProp calls to set base fluid properties (density, bulk modulus if
 needed) and update these if any conditions (like temperature) change during simulation; (3)
 Implement the nanobubble effect (H1) as a factor that reduces density or drag coefficient when
 activated; (4) Optionally, include a placeholder to connect to FluidDyn/CFD – e.g., an interface
 get_drag_force(v) that currently uses the formula, but is designed so we can override it with
 higher-fidelity models easily . 
22
 • 
23
 API Changes: The environment was likely accessed implicitly (global constants for density, etc., or a
 simple function). After this upgrade, we formalize it as an 
methods: e.g., 
Environment class with clearly defined
 get_density(depth) to get water density (could return reduced density if H1 is
 on), 
get_drag_force(floater) which computes drag based on the floater’s state (velocity,
 cross-sectional area, drag coefficient). Floater computations will call these methods rather than
 using hardcoded constants. This abstracts the fluid properties behind an API, which preserves
 compatibility because we will ensure that from the perspective of Floater or Simulation, they still
 just get a number for drag force or density – they need not know it’s coming from CoolProp. If any UI
 elements or config files provided fluid parameters (like user might input water density or drag
 coefficient), we keep those as overrides: the Environment can initialize with defaults from CoolProp
 but then apply user overrides if given. This way, existing user settings remain effective. We might
 add new outputs or logs (for debugging) such as reporting the actual density being used (especially
 if H1 is variable over time). However, no changes are required in the UI data format – drag forces are
 typically not directly shown, only their effect on power which will reflect automatically. 
• 
Performance Tuning: The fluid environment calculations are relatively light. CoolProp calls are fast
 (written in C++); even if called every step, computing a few fluid properties is negligible compared to
 the physics engine. If we did find it slow (e.g., repeated PropsSI calls), we could cache results for
 typical conditions (since water density won’t change significantly frame-to-frame unless we simulate
 drastic temperature swings). The drag formula is O(n) with number of floaters – very cheap, but if we
 wanted, we could vectorize drag computations using NumPy if computing for many floaters
 simultaneously. FluidDyn integration, if we ever call an external simulation or a more complex
 calculation, would be more expensive; in such case we might run that in a coarse time-step (e.g.,
 update drag forces from CFD every second, not every 20 ms) or in parallel. For now, our improved
 model remains algebraic and should not threaten real-time performance. We will keep the option to
 disable advanced features: for example, if H1 is turned off, we skip any extra computation (just use
 constant density). Similarly, if we include any random fluctuations (maybe to simulate turbulence),
 5
ensure they are inexpensive or optional. By structuring the environment module cleanly, if a
 particular calculation becomes a bottleneck, we can optimize or replace it without affecting other
 parts of the code . 
13
 • 
Real-Time & UI Integration: The environment module mostly works behind the scenes, so UI
 integration is minimal. We do need to ensure that any user controls related to the environment take
 effect. For example, the simulator might allow toggling Nanobubble Mode (H1) – when the user does
 this, the control or environment module should immediately update the density/drag parameters
 and perhaps log a message. Because our simulation runs continuously, we must carefully handle
 sudden changes: e.g., if H1 is turned on mid-simulation, all floaters’ buoyant forces should adjust.
 This can be done smoothly by just using the new density value in subsequent force calculations (the
 effect will be a gradual shift in net force as floaters continue moving – acceptable). If the UI displays
 any environment parameters (like water density or drag coefficient), we will update those readouts
 with new values from our module. The Chart.js or Dash interface might not currently show such
 internal parameters, but if it does (say, an efficiency improvement metric for H1), then providing that
 is straightforward. We will also ensure that any charts of forces or energies include the effects of the
 new model (e.g., if logging power lost to drag, that calculation would now be more accurate).
 Importantly, the environment upgrade should not disrupt the real-time loop: calls to CoolProp and
 our drag calculations are done within the simulation step and are very fast, so the 50 Hz update loop
 will remain smooth. By the end of this stage, the simulator will have a robust fluid environment
 model that improves physical accuracy (especially for later thermal and drag-reduction effects) while
 maintaining real-time performance and transparency to the user.
 Stage 3: Pneumatics – Air Injection & Compressor System (CoolProp
 + SimPy)
 Subsystem Scope: Air Injection System (Pneumatics) – This subsystem handles the compressed air supply
 and valves that inject air into floaters at the bottom and release it at the top, as well as the compressor
 mechanics. It controls each floater’s buoyancy state (air-filled or water-filled) and accounts for the work/
 energy of the compressor, including thermal effects (KPP hypothesis H2) . In code, this is contained in
 25
 models/pneumatics.py (and possibly part of 
24
 control.py for timing). Upgrading this subsystem
 will introduce thermodynamic calculations via CoolProp and event-driven timing via SimPy to accurately
 model the injection process.
 • 
Functional Replacement Plan: We will replace the simplistic on/off buoyancy toggle logic with a
 physically-based pneumatic model. In the current simulator, when a floater reaches the bottom,
 likely its state is instantly switched to air-filled (buoyant) and perhaps a fixed energy cost is added for
 the compressor. The upgrade will make this a dynamic process: when a floater is injected with air, we
 simulate the transient of filling, pressure equalization, and the resulting buoyancy force over time.
 CoolProp will be used to compute properties of air and the thermodynamic cycles: for example, the
 process of pumping air into a floater (at high pressure from a compressor) can be modeled either as
 an isothermal or adiabatic process. We can calculate how much air mass (or volume at pressure) is
 injected and what pressure the floater interior reaches, as well as the temperature change (H2 posits
 extracting work from heat – meaning if the air expands, it cools, drawing heat from ambient water).
 Meanwhile, SimPy will be utilized to coordinate these events in simulation time. SimPy is a discrete
event simulation framework for Python where processes (like an "injection event") can be modeled
 6
as generator functions with 
26
 27
 yield statements to wait for time or triggers . We will use it to
 model the valve operations and compressor cycles: e.g., open valve, inject air for X seconds (until
 f
 loater is full), then close valve; allow compressor to recover pressure, etc. This brings realistic
 sequencing instead of instantaneous changes. The plan is to create a PneumaticSystem class that
 manages an air reservoir (or compressor state) and all valves. Each floater will have an associated
 valve that the control system can open at the right time. When opened, rather than immediately
 switching buoyancy, we will simulate the air flow. For simplicity, we might assume the floater fills in a
 f
 ixed duration (user-defined or computed) – during that time the floater’s buoyancy will gradually
 increase from zero to full. The energy expended by the compressor to inject the air will be computed
 using thermodynamic relations (e.g., compressor work = Δ enthalpy of air + losses). Using CoolProp,
 if we know initial and final states (pressure, temperature) of the air, we can compute the required
 energy and possibly the heat exchanged with water (H2 effect: if the air is allowed to heat up from
 water, it expands, giving extra buoyancy). If needed, we can subdivide the fill into time-steps to
 update buoyancy continuously. SimPy will allow the timing to be decoupled from the main loop in a
 clear way – i.e., we can have a process that says "at time t, start injection, for next 0.5 s gradually fill,
 at t+0.5 s stop injection". This aligns with the real-time nature (0.5 s in simulation might correspond
 to some number of steps). Summarizing, the new pneumatic model will treat air injection as a
 process with finite duration and compute thermodynamic state changes for accuracy, rather than a
 crude instantaneous toggle.
 • 
Library Integration Steps: Begin by using CoolProp to get properties of air and (if needed) water.
 For instance, we can determine the density of air at the compressor output (high pressure) and
 inside the floater. Steps: (1) Define parameters: target pressure of air inside floater, compressor
 supply pressure, initial floater water-filled state (at hydrostatic pressure). (2) When injection starts,
 use CoolProp’s 
PropsSI to compute properties such as air density, internal energy, etc., at the
 given pressure and ambient temperature. If implementing H2 (thermal buoyancy boost), we might
 include a calculation where the cold air injected warms up from water: e.g., use CoolProp to find air
 density after isothermal expansion to ambient temperature vs adiabatic case – the difference could
 24
 be an extra buoyancy (H2 effect) . (3) Use SimPy by creating a 
simpy.Environment() that runs
 alongside the simulation clock. We will create a generator function for each injection event. For
 example, 
def inject_floater(env, floater): that yields a 
env.timeout(fill_time) to
 represent the filling duration. During that time, we might linearly interpolate buoyancy from 0 to full,
 or for more realism, maybe model it as an exponential approach if governed by a first-order system
 (though a linear ramp is simpler and likely sufficient unless detailed fluid dynamics of filling are
 considered). We can also create a compressor process: e.g., a process that cycles on and off to
 maintain an air reservoir pressure. This could involve yielding 
env.timeout(on_time) to
 pressurize, then off, etc., or if continuous, just accounting for energy usage. Integration-wise, the
 main simulation loop will advance in small steps; concurrently, we run 
env.step() for the SimPy
 environment each loop to process any events scheduled at the current simulation time. Alternatively,
 since SimPy can also be advanced in real-time mode, we might synchronize SimPy’s time with the
 simulation time. Each time a floater reaches bottom, the control triggers a SimPy process:
 env.process(inject_floater(env, floater_i)) . That process will handle the timing of
 opening/closing the valve and updating the floater’s buoyant force (perhaps by directly modifying a
 property in the Floater object or via a callback each small step). We will integrate these such that at
 each physics tick, if a floater is mid-filling, we calculate the partial buoyancy (e.g., fraction of air filled
 * full buoyant force). After fill completes, the floater is marked fully air-filled. Similarly, when a floater
 gets to the top, instead of an instantaneous switch to water-filled, we can simulate an air release
 7
event. However, since venting might be very quick relative to simulation step, we might still treat it as
 instantaneous (or a very short SimPy event). The compressor’s impact on energy: we will calculate
 the work done for each injection using thermodynamic formulas (e.g., isothermal compression work
 = nRT * ln(P_final/P_initial), or adiabatic formulas) and subtract that from net energy or log it. If the
 generator output is considered net of compressor, we will incorporate this in the power calculations
 (Stage 4). The integration sequence: (a) Instantiate a SimPy environment in the 
PneumaticSystem
 class; (b) modify the control logic to trigger pneumatic processes instead of directly toggling floaters;
 (c) update the Floater class to accept gradual buoyancy changes (e.g., a method to set its fill level or
 directly modulate its volume of air); (d) use CoolProp within those processes to compute any needed
 state variables (final pressure, temperature after filling, etc.). 
• 
• 
and 
API / Interface Changes: This upgrade will introduce more complex interactions between control,
 pneumatics, 
f
 loaters. 
Originally, 
the 
interface 
might 
been:
 pneumatics.inject(floater) simply made the floater buoyant and perhaps increased a
 compressor energy counter. Now, 
have 
pneumatics.inject(floater) will likely initiate a process and
 immediately return (non-blocking), with the actual effects on the floater occurring over time. We
 might implement this as 
PneumaticSystem.start_injection(floater_id) which enqueues
 the event in SimPy. The Floater class may gain an attribute like 
fill_fraction or a state
 (is_filling) to represent that it’s in transition. The control module which calls for injections will
 need slight adjustments: instead of marking the floater filled at a certain time, it will call the
 pneumatic system and perhaps stop worrying about that floater until it’s done. We could have a
 callback or simply rely on the floater’s state updating. Another interface consideration is the
 compressor’s power draw: previously, if the simulator tracked compressor power as a constant or
 formula, 
now 
we 
will 
compute 
it. 
We 
might 
add 
a 
method
 pneumatics.get_compressor_power() that returns current power consumption (e.g., when
 compressor is on) to allow the drivetrain/generator module to account for it. In terms of UI and
 configuration, if the user can set injection timing or compressor behavior, those settings still apply
 but perhaps with more nuance. For example, a user-set “injection interval” might have been
 implemented as a periodic timer; with SimPy, we might still use that interval as the target cycle time.
 We must ensure any user adjustments (like turning off injection or changing pressure) are handled:
 e.g., provide functions to change compressor pressure setpoint or abort an ongoing injection if
 needed (for a manual emergency stop). Backward compatibility: From an external viewpoint, the
 results should be similar – floaters still become buoyant at the bottom and heavy at the top – but
 now with a short delay and more physics. The UI likely doesn’t show the intermediate fill state
 explicitly (unless we choose to add an animation detail); it will mainly see a small smoothing in the
 torque curve rather than a step change. We will verify that any logged values (like count of floaters
 f
 illed, or cycle time) remain reasonable. If any code in control or elsewhere assumed instantaneous
 change, we will adjust it to either wait for or not double-count the changes. Possibly we will maintain
 a boolean state 
is_filled for each floater for compatibility, but define it such that it flips to true
 only after the fill process completes (for any logic that checks it). We will thoroughly test the
 transitions to ensure no logic breaks (e.g., ensure one floater is not injected twice if timing overlaps 
SimPy will handle by queuing if needed).
 Performance Tuning: The pneumatic simulation introduces some overhead due to SimPy
 scheduling and CoolProp calculations, but it should remain lightweight. SimPy’s event system is
 efficient for a moderate number of events (we’ll have at most one injection event per floater per
 cycle, plus compressor cycling). The time resolution of SimPy events can be coarser than the physics
 8
step – e.g., we don’t need to schedule every 20 ms of fill as a separate event; we can simply linearly
 interpolate in the physics loop. Thus, SimPy might only handle a few dozen events per simulated
 minute, which is trivial. If we choose to simulate filling in finer detail, we could break it into a handful
 of sub-steps (maybe update buoyancy 10 times over the fill period) – even that is not a performance
 concern with tens of floaters. CoolProp property calls for air are also fast, and we might call them
 only at start/end of injection (to know final state). If more frequent calls are needed (e.g., computing
 air properties at intermediate pressures during filling), we could approximate or use cached values;
 however, given the short duration, assuming linear or adiabatic changes is fine. We will also ensure
 that adding these calculations doesn’t cause the simulation to fall behind real time: since the physics
 loop is continuous, we might need to handle the case where injection events overlap with many
 f
 loaters. If too many floaters fill at once (which normally wouldn’t happen in a properly phased
 system), the cumulative computations could add up. But the KPP design likely staggers injections; if
 not, we might impose a slight offset. Another aspect is multi-threading: SimPy itself runs in the main
 Python thread (as part of the simulation loop). If the compressor model were more complex (e.g.,
 solving ODEs for pressure dynamics), we might consider moving some calc to a background thread,
 but that seems unnecessary. One possible heavy operation is PDF generation or logging at the end 
if we log detailed thermodynamic data, ensure it doesn’t interfere with the loop (maybe accumulate
 and dump after stop). In summary, the pneumatic module should comfortably run in real-time. If
 any performance issue arises, options include simplifying the fill process modeling (e.g., treat it as
 instant but with calculated energy cost – a fallback) or using Numba to accelerate repetitive calcs. We
 will also test on lower-end hardware to ensure the chosen level of detail is appropriate.
 • 
Real-Time Update & UI Integration: Maintaining UI responsiveness and simulator functionality is
 paramount. The air injection upgrade should mostly be invisible to the user in terms of operation 
f
 loaters will still appear to become buoyant at roughly the bottom of the tank. The UI’s real-time
 charts (e.g., power output vs time) may actually look smoother: previously a floater might have
 caused a sudden jump in torque when filled; now the torque increase will ramp up over a fraction of
 a second, which is more physical. This should not negatively affect the Chart.js graphs (which update
 say every 100 ms) – in fact it avoids spiky data. If the UI includes any indicator of compressor status
 (perhaps not originally, but we could imagine showing compressor power draw or pressure), we will
 integrate that: e.g., a gauge for compressor load could be added in Dash or an HTML element
 updated via SSE. Even if not, at least in a log or console we will output the compressor energy used
 so that net power can be calculated (the blueprint’s goal is to show net output considering
 compressor loss). Backwards compatibility is maintained in that all existing UI controls (like “toggle
 compressor on/off” if it exists, or any manual injection trigger) will still work. The control system will
 be updated in Stage 5 to coordinate with this pneumatic model, but we ensure that from the user’s
 perspective, pressing "Start simulation" still kicks off the periodic injection cycle – now managed by
 SimPy processes under the hood. Real-time response: Because we run physics in a separate thread
 (or asynchronous loop), we must also ensure that events scheduled via SimPy occur at the correct
 simulation times even if the wall-clock timing differs slightly (e.g., if the sim slows, the injection still
 happens at the correct simulated interval, albeit wall-clock slower – which is fine). The UI might have
 some latency in reflecting an event (like showing a new floater filled count), but that’s expected if
 simulation runs slower than real-time. Generally, however, we design for real-time or faster-than
real-time execution, so the UI will keep up. In testing, we will verify that the sequence of floater fills
 and drops still produces the expected cycle (e.g., the system reaches a steady state RPM and power
 output similar to the old model). Any differences (like slightly higher efficiency due to H2, or different
 timing) will be validated to ensure they are reasonable improvements rather than bugs. The end
 9
result of this stage is a much more realistic pneumatic subsystem that captures the nuances of air
 injection and compressor workload, without sacrificing the interactive experience of the simulator.
 Stage 4: Drivetrain & Generator (PyChrono Mechanical + PyPSA
 Electrical)
 28
 Subsystem Scope: Drivetrain and Generator – This includes the mechanical drive components (chain
 sprockets, gearbox, one-way clutch, flywheel) and the electric generator that converts shaft rotation into
 power . The drivetrain module (in 
models/drivetrain.py ) computes the rotational dynamics: it
 takes the chain’s torque and applies it to an inertia (flywheel/generator), possibly smoothing it using a
 clutch/flywheel (H3 hypothesis), and calculates output power. The generator part may be embedded or
 separate (
 29
 generator.py in some designs ). Upgrading this subsystem will use PyChrono for the
 mechanical side and PyPSA for the electrical side to achieve a high-fidelity simulation of power conversion.
 • 
11
 Functional Replacement Plan: We will improve the drivetrain model by explicitly simulating the
 shaft and flywheel dynamics with PyChrono (rather than simple equations) and by integrating an
 electrical power systems model via PyPSA. In the legacy simulator, the drivetrain likely computed
 angular acceleration = net_torque / inertia each step to update rotational speed, and applied a
 constant efficiency to compute electrical power. H3 (the clutch/flywheel enhancement) may have
 been only conceptual or simply simulated by adjusting torque smoothing. With PyChrono, we can
 create a physical model of the drivetrain: a rotating body representing the combined inertia of the
 chain, sprocket, and flywheel, with a one-way clutch that allows the flywheel to spin freely when the
 chain torque is negative (preventing back-driving the chain). We will implement the clutch behavior
 either through Chrono’s joint constraints or via logic: Chrono’s vehicle/powertrain module supports
 1D drivetrain elements like clutches and brakes , which we can use to model the engage/
 disengage. The flywheel effect will naturally emerge from having a large inertia in the system. On
 the generator side, we integrate PyPSA (Python for Power System Analysis) to model how the
 mechanical rotation produces electrical output. PyPSA is a toolbox for simulating and optimizing
 electrical power systems, including models for generators, storage, and networks . In our
 context, we can use PyPSA in a simplified way: represent the generator as a component with a
 certain efficiency, perhaps a maximum power limit, connected to an electrical load or grid. Each
 simulation step, we will provide the mechanical power (torque * angular speed) to the PyPSA model,
 which can then compute electrical quantities (like current, voltage, frequency if AC, etc.). If the
 generator is grid-connected, one might assume it maintains synchronous speed, but given KPP likely
 uses the flywheel to smooth output, we might treat it as a DC generator charging a battery or
 feeding an inverter. We will initially use PyPSA to compute steady-state conversion: e.g., given
 mechanical power, apply efficiency to get electrical power, possibly simulate losses or constraints (if
 generator has a limit, PyPSA can impose it and spill excess as heat). If we extend to multiple periods
 or optimize, PyPSA could optimize dispatch, but that’s beyond real-time scope. However, using PyPSA
 sets the stage for analyzing scenarios like grid interaction or energy storage in the future.
 Essentially, PyPSA will handle the electrical side with rigor, while Chrono handles the mechanical
 transient dynamics. The functional goal is a drivetrain that accurately responds to torque changes
 (no more instant speed jumps – inertia and clutch will cause gradual speed changes) and a generator
 model that can reflect the effect of electrical load (e.g., if we simulate varying electrical load, how it
 affects shaft speed).
 30
 10
• 
Library Integration Steps: On the mechanical side, integrate PyChrono by extending the Chrono
 model from Stage 1. We already have a Chrono revolute joint for the main sprocket/shaft. Now, we
 will attach a flywheel body to that shaft (or simply attribute an appropriate inertia to the shaft
 body). If using Chrono’s 1D powertrain elements: we can create a Chrono shaft object with a given
 moment of inertia, and connect the chain’s sprocket to this shaft via a clutch element. Chrono’s one
way clutch (if available) would be ideal – it transmits torque in one direction and freewheels in the
 other. If not directly available, we can simulate it by logic each step: if the chain torque is positive
 (driving), we apply it to accelerate the shaft; if it’s negative (chain pulling back, which might happen
 when floaters on the descending side outweigh ascending at some moment), we disengage 
meaning we don’t apply a decelerating torque to the shaft, effectively letting the chain slip (this
 protects the flywheel from negative torque and implements the one-way clutch). To implement that
 with Chrono, one way is to use a ChLinkMotorTorque that we control: when chain torque > 0, apply
 that torque to the shaft; when chain torque <= 0, set the motor torque to zero (so the chain isn’t
 driving the shaft, and the chain would just slack or not exert backward torque). Additionally, the
 control system might periodically disengage the clutch even under positive torque (pulse mode), but
 that will be handled in Stage 5. Next, define the gearbox ratio if any: we can simply incorporate that
 into torque calculation (e.g., if a gearbox ratio N:1 between chain sprocket and generator shaft, the
 torque is multiplied, speed divided, etc.). Possibly implement as another Chrono constraint or just as
 a factor in equations. Once the Chrono model is set, we use it to update shaft speed: Chrono will
 integrate the shaft rotation given the net torque (chain input minus generator resistive torque). On
 the electrical side, set up PyPSA. We will create a PyPSA 
Network with at least two buses: one
 mechanical or generator bus and one load/grid bus. However, since PyPSA is primarily for electrical
 networks, we might model the generator as an element that converts mechanical to electrical. PyPSA
 includes standard generator models with efficiency and possibly minimum/maximum output .
 30
 We can do: 
net.add("Bus", "generator_bus") , 
net.add("Bus", "grid_bus") . Then add
 a 
generator: 
net.add("Generator", 
"KPP_Gen", 
bus="generator_bus", 
p_nom=some_value, efficiency=gen_eff) . Also add a link between generator_bus and
 grid_bus or a load on grid_bus to represent that power is being delivered. In a static simulation,
 PyPSA can solve a power flow. But since our system is one generator, one sink, this is
 straightforward: the generator will produce whatever mechanical power is given (times efficiency) as
 electrical output, which goes into the load or grid. We might not actually need PyPSA to solve
 anything if it’s just a one-to-one mapping, but using PyPSA becomes more useful if we consider
 scenarios like the generator reaching a limit or the grid having a certain frequency constraint. At
 minimum, PyPSA gives us a structured way to incorporate these calculations and extend to multiple
 time-step analysis if needed. Integration steps: (1) Initialize PyPSA network at simulator start, define
 generator component. (2) Each simulation step, after obtaining the shaft’s angular speed (ω) and
 torque (τ) from Chrono, calculate mechanical power P_mech = τ * ω. Then update the PyPSA
 generator: set its 
p_max_pu or 
p_set to P_mech (converted to whatever units PyPSA expects,
 likely MW if we use SI properly and scale). (3) Run a PyPSA power flow or simply compute output =
 P_mech * efficiency. PyPSA might need to be “stepped” if we set up a multi-period simulation; but for
 real-time, we can cheat: just use PyPSA’s formula or use its network object to compute current flows.
 Another approach: skip solving AC power flow (since one generator feeding infinite bus is trivial) and
 directly compute output power and perhaps assume generator torque = electrical torque (with
 efficiency). PyPSA can still be used to accumulate energy or handle more complex cases later. (4)
 Retrieve the electrical power output and any other metrics (voltage, etc., if relevant) for logging/UI. If
 grid interaction was to be modeled (like frequency feedback on the generator speed), we’d integrate
 11
that, but likely we assume generator is controlled to provide whatever torque is demanded by the
 mechanical side (or vice versa if we had speed governing, but that’s beyond current scope). 
• 
• 
API / Interface Changes: The drivetrain upgrade will largely be internal to the module, with minimal
 interface change outwardly. The main Simulation loop or control used to maybe call
 drivetrain.update(dt, chain_torque) and get back 
angular_speed or 
power . Now,
 since the floater physics (Stage 1) and drivetrain are both using Chrono, we might not even need to
 explicitly pass torque – the floaters could be directly coupled in the Chrono model. However, to keep
 things clear and modular, we may still compute net chain torque in Python (summing buoyant forces
 * radius) and feed it into the Chrono drivetrain as described. We will maintain methods like
 drivetrain.get_speed() or 
get_power() , but under the hood these will pull from the
 Chrono/PyPSA state instead of a manual calc. For example, 
drivetrain.get_speed() might now
 do 
omega = chrono_shaft.GetPos_dt() (angular velocity), whereas before it updated an
 internal variable. 
drivetrain.get_power() might do 
P = generator_electrical_power
 from PyPSA rather than 
torque * omega * efficiency . If the UI or logging expects certain
 f
 ields (like mechanical power, electrical power, RPM), we ensure to provide them. We might also
 introduce new API endpoints if needed: e.g., to configure the flywheel inertia or clutch mode (so that
 these can be tweaked via config or UI). But these can be done via existing config systems (just
 reading values). One notable interface expansion is the separation of generator losses: originally a
 single efficiency number might have been applied to compute net power. Now we have an explicit
 model, so we may want to output both mechanical power and electrical power for clarity. If not
 already, we’ll add logging of generator mechanical input vs electrical output, to demonstrate the
 efficiency and any curtailment (if generator caps out). This does not break compatibility – it adds
 information. If the UI only displays electrical output (net), it can continue to do so, using our
 computed value. Backward compatibility considerations: we will calibrate the new model such that
 under nominal conditions it replicates the old behavior. For instance, if previously at steady state the
 chain torque produced 5 kW of power with 80% efficiency -> 4 kW electrical, we will set the generator
 efficiency such that we get the same 4 kW for that torque and speed. This ensures the user sees
 familiar results for known scenarios. Differences will appear when using the clutch or transient
 events, but those are intended improvements. The clutch engagement will still be controlled by the
 control system (or autonomous one-way action), but its presence is largely internal – externally, the
 effect is smoothed power. We will have a method or attribute to enable/disable H3 (the pulse mode
 clutch): if disabled, we effectively lock the clutch (the shaft always engaged, meaning the model
 reduces to a normal direct drive). This gives backward comparability if someone wants to see the
 “no-flywheel” case. 
Performance Tuning: The mechanical simulation of the drivetrain via Chrono is computationally
 trivial compared to the floaters: it’s a single rotational degree of freedom (or a few if we separate
 f
 lywheel, shaft, etc.), and Chrono can handle that at very high speeds. The additional overhead of the
 clutch logic is minimal (a conditional check each step or solving a constraint – Chrono’s 1D constraint
 solver for clutches is very fast). PyPSA’s computations are also lightweight for a single generator
 system. PyPSA is built to handle large network optimizations, so a single power flow solve per time
step is negligible. In fact, we might not even need an iterative solve – one generator to an infinite
 bus is direct calculation. Even if we did a full AC power flow each step, with one node it’s a simple
 equation. The main point is that introducing PyPSA does not slow the real-time loop meaningfully. To
 be safe, we might use PyPSA in a mode where it doesn’t reoptimize network topology each time;
 basically, initialize once, then at each step just update generator dispatch. If needed, PyPSA allows
 12
adding a time series of data and solving offline, but here we want online. If for some reason
 integrating PyPSA directly is cumbersome (since it’s more geared to offline simulations), an
 alternative is to use a simpler library (or even just our own code) for the generator and reserve
 PyPSA for later analysis. However, since the task specifically includes PyPSA, we will incorporate it at
 least for validation and future-proofing. Another consideration: if in future the electrical model
 becomes more complex (multiple generators or linking to a grid model), we may need to partition
 the problem – possibly running the electrical simulation at a slower rate or asynchronously. But at
 the moment, one can easily run the small PyPSA network calculation every 20 ms without issue.
 Regarding parallelization: Chrono will handle multi-threading for the mechanical if we had many
 constraints (not needed here), and PyPSA can utilize numpy which might use multiple cores in linear
 algebra (but again trivial size). Memory overhead for these libraries is minor relative to modern
 systems. We should ensure that data transfer between Chrono and PyPSA each step (which is just a
 couple of floats: torque and speed) is efficient – no issues there. We will include the generator
 calculations in the same thread as the simulation loop to keep things synchronous (so we don’t need
 locks or communication overhead). If using a separate thread for simulation, then that thread will
 also run PyPSA; the UI thread remains separate. Overall, Stage 4’s enhancements are not expected to
 threaten the real-time performance. 
• 
Real-Time Update & UI Integration: After this upgrade, the output metrics and user experience
 should greatly benefit. The UI charts for shaft speed (RPM) and power output will show the effect of
 the flywheel smoothing – instead of jagged oscillations each time a floater engages, the RPM will
 f
 luctuate less (the flywheel inertia filters it) and the power output will be more stable. If the UI
 previously plotted instantaneous power, it will now reflect the smoothed power (unless we choose to
 show both instantaneous mechanical power and generator output for comparison). We will maintain
 the net power output display as before (taking into account generator efficiency and subtracting
 compressor power). In fact, now that we explicitly compute compressor power in Stage 3 and
 generator output in Stage 4, net power = generator electrical output - compressor electrical
 input can be computed and could be shown to the user as overall system power. If the UI has a field
 for efficiency or similar, we’ll update its calculation to use these new values (e.g., efficiency = net
 electrical out / energy from buoyancy). The UI should remain responsive: the simulation thread will
 be doing slightly more work to update Chrono and PyPSA, but well within the available time budget
 per frame. Chart.js (if used) will simply get data points that are perhaps less erratic. In a Flask SSE
 setup, we ensure that each SSE event includes the needed data. For example, if previously we sent
 {"time": t, "power": P} , we continue to do so, but ensure P is the electrical power delivered (or
 explicitly state if otherwise). Perhaps we add fields like 
"rpm": shaft_speed or
 "flywheel_energy": E if wanting to visualize the flywheel, though not strictly required. For a
 Dash interface, similarly, the callbacks will grab the updated values from the simulation state. The
 control inputs from the UI, such as toggling the clutch mode (H3 on/off) or adjusting a flywheel size,
 can be implemented. If a user unchecks H3 (meaning no pulse mode), the control logic will simply
 not disengage the clutch except the one-way function (so effectively always engaged). If the user
 changes generator parameters (if such UI exists, e.g., efficiency or load), the PyPSA model can be
 updated on the fly (PyPSA allows changing object parameters between solves). We will also ensure
 backwards behavior: for example, if previously the simulator immediately zeroed out power when
 the chain stopped, our model will do the same (if shaft stops, generator output stops). The one-way
 clutch prevents negative power flow (generator cannot drive the chain backward), which is physically
 correct and matches the idea of a ratchet in KPP – previously the code may have just not considered
 negative power, so now it’s naturally enforced. In testing, we will run scenarios with and without the
 13
clutch engaged to verify that, e.g., in continuous mode (clutch locked), the power oscillates more,
 and in pulse mode it smooths out, validating H3’s effect. The UI may show these differences in plots,
 which is a desired outcome to demonstrate the benefit of the enhancement. All UI elements (charts,
 numeric readouts) will continue to update seamlessly each interval. In summary, by the end of
 Stage 4 the simulator’s drive-train and generator are modeled with high fidelity, capturing inertia
 and electromechanical conversion, while the user interface still behaves as before but with more
 insightful outputs (smoother power curve, explicit accounting of losses).
 Stage 5: Control System Enhancements (SimPy Scheduling &
 Advanced Logic)
 4
 Subsystem Scope: Control System – This module coordinates all timed actions in the simulator: air injection
 timing, clutch engagement/disengagement, and any feedback control like maintaining speed or optimizing
 performance . It monitors the state of floaters, speed, etc., and issues commands to subsystems (open/
 close valves, engage clutch) according to a strategy. The control logic is in 
models/control.py .
 Upgrading this will involve using SimPy (and possibly Python concurrency) to handle event scheduling in a
 clearer way, and setting up the architecture for more advanced control (like different strategies or even AI
 controllers in the future).
 • 
31
 Functional Replacement Plan: We will restructure the control logic from a likely simple loop or
 conditional-based system into a more robust, event-driven scheme. In the legacy simulator, control
 might have been implemented as part of each time-step: e.g., “if a floater is at bottom, inject now; if
 at top, release; pulse clutch every N seconds by checking time mod N,” etc. This can become complex
 and interdependent. Using SimPy, we can model each control sequence as a process. For example,
 the injection cycle can be a process that repeats continuously: every T seconds, trigger an injection on
 the next available floater. The clutch pulse logic can be another process: engage clutch for X seconds,
 disengage for Y seconds, repeat. SimPy allows these processes to wait on timers or events, making the
 code simpler to reason about. We will also incorporate a notion of different control modes
 (strategies). The upgraded design could define an abstract 
32
 33
 ControlStrategy (as noted in design
 documents) so that one could plug in a manual mode, a simple periodic mode, or an advanced
 feedback controller or RL agent in the future . Initially, we implement the simple strategy
 equivalent to current behavior: periodic injection and periodic clutching. But we structure it such
 that switching to a different strategy is easy (maybe via a setting). The control system will now
 explicitly interact with the SimPy environment from Stage 3 (we may use one global
 simpy.Environment for both pneumatic and control events, or separate but synchronized ones).
 Essentially, control will orchestrate SimPy processes for the various subsystems: one process
 handles the injection schedule (starting SimPy processes for each actual injection event), another
 handles clutch toggling schedule, and possibly processes for any monitoring or safety checks (for
 instance, we could have a process that monitors if the speed exceeds a limit and then triggers an
 emergency action). By doing this, the control logic is no longer buried in the time-step loop with a
 bunch of if-statements – instead, it’s timeline-based which is more intuitive. For example, injection
 process: 
while True: yield env.timeout(interval); choose a floater and initiate 
injection . 
Clutch 
process:
 while True: yield env.timeout(coast_duration); disengage clutch; yield 
env.timeout(pulse_duration); engage clutch . These processes run concurrently in SimPy.
 We will also ensure the control can handle real-time adjustments: e.g., if the user changes a
 14
parameter like the injection interval or disables an enhancement, the control processes should
 adapt. This might mean restarting a process with a new interval or simply reading a global variable
 each cycle. Another improvement is to incorporate some feedback: for instance, if we want to
 regulate the chain speed to a setpoint, we could implement a simple PID controller that adjusts the
 injection timing or the fraction of floaters filled to maintain that speed. Given the complexity of the
 physics now, a feedback controller might significantly improve performance (e.g., injecting a bit
 earlier or later if speed deviates). We can include a basic version: e.g., monitor RPM, and if it’s above
 target, skip an injection or disengage clutch longer, if below target, maybe shorten the coast. These
 details can be iterative, but the upgrade paves the way by providing a clear structure to do so. 
• 
Library Integration Steps: The primary library here is SimPy, which we have partially introduced in
 Stage 3 for pneumatics. In Stage 3, SimPy was used to time the injection events themselves. Now we
 will also use it to schedule when to start those events. This could all be done within the same SimPy
 environment. We can create long-running processes for periodic actions. Steps: (1) Decide on control
 strategy mode (initially “Scheduled Cycle” mode replicating existing timing). (2) For the injection
 schedule: suppose the current design injects one floater every X seconds (to have a steady sequence
 of rising floaters). We implement 
def cycle_injection(env): while True: yield 
env.timeout(X); trigger injection of next floater . The “trigger injection” will call
 pneumatic.start_injection(floater) as defined earlier. We need a way to get the next
 f
 loater – perhaps floaters are indexed and injection sequence is cyclic. We can maintain an index or
 queue of floaters that are ready (initially all floaters empty except maybe one already buoyant in
 cycle). We know the order because floaters are attached on the chain. Alternatively, simply inject one
 f
 loater every X seconds in the same order (SimPy doesn’t inherently know floater positions, so we
 rely on timing to correspond with them reaching bottom). This is a slight approximation: ideally, we’d
 inject exactly when a specific floater hits bottom. We could improve by synchronizing with physics:
 e.g., monitor a particular floater’s position. However, because all floaters are evenly spaced and chain
 speed is roughly constant in steady operation, the periodic injection works. If we want precision: we
 can set an event when a floater is at bottom – but detecting that event can be done by checking
 position each step (which we already do possibly). Instead, we might continue to use a conditional
 check each step as a backup: if floater angle ~0 (bottom), and not already filled, then inject. But to
 leverage SimPy fully, one could create an Event that floater triggers when reaching bottom. This is
 complex to wire in current architecture (would require Chrono callback or periodic check raising a
 SimPy event). Given time, the simpler approach is fine: schedule by time, which is effectively what a
 human-designed controller would do by syncing to cycle time. (3) For clutch control: implement a
 process if H3 is enabled. For example, suppose the pulse strategy is “engage for 2s, disengage
 (freewheel) for 2s” repeatedly. Then 
def clutch_control(env): while True: 
clutch.engaged = True; yield env.timeout(2); clutch.engaged = False; yield 
env.timeout(2) . The 
clutch.engaged property would interface with the drivetrain model
 (when False, we program the Chrono motor to not transmit torque as described). Initially, we might
 set the timing static or make it depend on cycle (e.g., disengage during the heavy part of cycle, etc.,
 which would require sync – perhaps fine-tuned later). (4) Integrate control processes with the main
 simulation: the simulation thread will call 
env.step() each tick to advance SimPy’s internal clock
 in lockstep with simulation time. Alternatively, we might let SimPy run ahead if it’s waiting on long
 timeouts and only interact when needed. But it’s simpler to advance it stepwise: e.g., each 20ms tick,
 we do 
env.step() or 
env.advance(0.02) to process any events that should occur in that
 interval. SimPy will execute any processes whose waits expire in that timeframe, triggering our
 control actions exactly on time. (5) Provide hooks for dynamic changes: we will store the interval X,
 15
clutch durations, etc., in variables that can be updated. If the user changes them via UI (or an
 algorithm changes them), those changes will take effect on the next cycle. If needed, we can also
 stop and restart processes: e.g., if the user dramatically changes the injection rate, we could cancel
 the old 
cycle_injection process and start a new one with the new interval. SimPy allows us to
 keep references to processes and kill them (
 process.interrupt() or simply not loop). We will
 also incorporate safety processes: e.g., a watchdog that if simulation is paused or stopped, or if an
 error occurs, will interrupt ongoing processes to avoid stray events after stop. Since our
 SimulationController will handle stop events gracefully (signaling threads to end) , we tie into
 34
 that to also shut down SimPy environment or simply not call 
35
 env.step() when sim is paused. 
• 
API / Interface Changes: The control module interface might remain similar for external callers but
 change internally. Possibly earlier the Simulation loop would call something like
 control.update(dt) every tick to let control do whatever (like check conditions). We can keep
 control.update(dt) but implement it to advance the SimPy environment by 
dt and handle
 any immediate logic not covered by SimPy processes. The external code (like simulation engine) thus
 remains calling control.update as before. However, now control.update will not explicitly inject
 valves, etc., on conditions; those are in SimPy processes. Instead, it will primarily synchronize time. If
 some immediate conditional logic is still needed (like emergency cutoff if some parameter goes out
 of range in that exact step), we can keep a minimal check in control.update or use SimPy events for
 those as well. For instance, if we want to trigger a shutdown if speed > max, we could either
 continuously check in update or model it by an event that monitors speed (SimPy doesn’t directly
 support event on a condition without polling unless we integrate with simulation state events). We
 may leave such rare logic as simple if-statement in update for reliability. The interface to subsystems
 (pneumatic and drivetrain) has changed slightly (they now have dedicated methods to perform
 actions), but control was already calling something similar. Now, for example, instead of directly
 f
 lipping 
floater.is_filled , control will call 
pneumatic.start_injection(floater) .
 Instead of directly toggling a clutch variable, control will use 
drivetrain.clutch_engage() or
 set a property that we provide. We will add those small methods to the respective modules to
 encapsulate the new logic. For UI interactions: if the user manually triggers an injection via UI (if
 such a feature exists, e.g., a button to inject now), we need to handle it. We can either treat it as a
 special case in control (listening for that command and then directly calling 
15
 start_injection ), or
 simulate it via SimPy by sending an event (like env.timeout(0) to schedule immediate injection). Since
 the UI is on a different thread (likely main thread), it could call a function in control which puts an
 event into the simulation thread’s context (perhaps via a thread-safe queue). The
 SimulationController can handle param changes on the fly by invoking methods on the control
 module . So if user triggers injection, the controller calls control.inject_now(), which then uses the
 pneumatic system to inject immediately. That fits fine with our design since
 pneumatic.start_injection can be called anytime. If injection is already ongoing or floater already
 f
 illed, control should guard against conflicts (which it would in any case). We also ensure that
 toggling of H1/H2/H3 from UI is handled: e.g., if user disables H3 (clutch pulse), control can either
 cancel the clutch SimPy process or simply stop disengaging (by setting clutch always engaged). We
 might implement that by having the clutch process check a flag each cycle and exit if H3 is turned
 off. If H3 is turned on later, we can restart the process. The user-facing interface (dashboard or
 input form) doesn’t change, but the behavior might: previously, maybe the user had to input an
 injection interval; now the same input is used but the control executes more precisely. If the user
 changes that interval slider during a run, previously the code might or might not have responded
 16
immediately; in our design it will (the SimPy process will use the new interval next loop or we restart
 it). This makes the simulator more interactive. 
• 
• 
Performance Tuning: The control logic itself is not computationally heavy – mostly waiting and a
 few condition checks. Using SimPy adds negligible overhead. The only thing to watch is that we do
 not flood the system with events. But our design avoids that: the processes mostly wait for seconds
 at a time, which in simulation steps might be dozens of ticks where nothing happens (SimPy handles
 that efficiently). When an event time comes, executing a few lines (e.g., call start_injection) is trivial.
 We will ensure to not create infinite event chains inadvertently. One potential issue is if the
 simulation runs much faster than real time and we use real-time delays in control. But we treat all
 time in simulation seconds, so that’s fine. If the simulation is paused or runs slower, SimPy doesn’t
 mind – it’s just following simulation time. There's also a note in SimPy docs: it’s not meant for
 continuous simulation, but here we blend discrete events with continuous steps. SimPy is fine as
 long as events are scheduled; it doesn’t intervene otherwise. We do need to ensure thread safety: we
 will run SimPy in the simulation thread, so no race conditions there. When adjusting control
 parameters from the UI, we do it via the controller which locks or ensures proper sync (likely
 negligible issues if just setting a variable). Another performance aspect is logic complexity: if we later
 add an RL agent (as hinted by design) , that could be heavy (involving neural nets). In that
 scenario, we might integrate the agent inference as part of control update. If it’s too slow, offload to
 another thread or use JAX to jit it. But currently, our control is simple enough that the overhead is
 measured in microseconds. We just highlight that our architecture allows insertion of an advanced
 controller (even hooking up an OpenAI Gym interface to train an RL agent using the simulation) ,
 without changing the physics modules. 
33
 33
 5
 15
 Real-Time & UI Integration: With the control system revamped, the simulator will maintain (and
 likely improve) its interactive behavior. For example, currently the simulator might not gracefully
 handle rapid user changes or might have tight coupling of UI and simulation timing. Our design, by
 having a SimulationController and using asynchronous processes, means the simulation can be
 paused, resumed, or adjusted on the fly more smoothly . The UI will still use the same
 controls: sliders for timing, checkboxes for H1/H2/H3, start/stop buttons, etc., but the underlying
 implementation now ensures these actions are handled in a coordinated way. For instance, clicking
 "Pause" will signal the simulation thread to halt; our control processes will naturally pause because
 we stop advancing SimPy time. When resumed, they pick up where left off (which is fine for our
 processes as they are mostly periodic; a slight phase shift is not an issue, or we could reset if
 needed). If the user changes the injection interval slider, the control process can dynamically adapt
 (maybe it reads the value each cycle, so the next injection uses the new interval). If the user turns off
 injection entirely (maybe setting interval to 0 or clicking a stop-injection toggle), the control can
 respond by not scheduling new injections (could simply break out of the loop or skip when interval is
 0). Similarly, for clutch control, a user toggle for H3 immediately changes whether the clutch process
 runs. In a Dash or Flask UI, these user actions might call an API endpoint or callback that calls our
 control methods via the SimulationController. We will ensure those methods acquire any needed
 locks or use thread-safe flags so as not to corrupt the simulation state mid-step (though changing a
 parameter is low-risk). Another UI aspect is monitoring: we can expose more internal state to the UI
 for transparency. For example, we could show what the control is doing: which floater is being
 injected now, time to next injection, whether clutch is currently engaged or coasting, etc. This could
 be done via additional fields in the SSE data or Dash callback outputs. Even if not asked explicitly, it
 could be useful for developers. Regardless, we’ll log those events (e.g., "t=5s: Injecting floater 3",
 17
"t=5.2s: Clutch disengaged") for debugging and possibly display on UI console if exists. The real-time
 loop will remain stable with the control interventions because SimPy ensures actions happen exactly
 when scheduled, avoiding race conditions that might have occurred with ad-hoc timing code. By the
 end of Stage 5, the simulator will have a flexible control system that can easily incorporate changes
 and advanced strategies, all while preserving the user interface and overall functionality (the user
 can still run the sim and see outputs as before, but now the control is smarter and more reliable).
 Stage 6: Integration, Testing & Performance Tuning (Parallelization
 and Final Adjustments)
 In this final stage, we integrate all upgraded components, ensure they work together seamlessly, and apply
 best practices for code structure, performance, and maintainability. We will also address backward
 compatibility thoroughly and set up the project for future development.
 • 
• 
Subsystem Integration and Sequence of Replacement: The upgrade has been carried out in
 logical stages corresponding to subsystems, but in implementation we should integrate
 incrementally to manage risk. A suggested sequence is: (1) Introduce PyChrono for floater/chain
 mechanics first (Stage 1) and verify basic motion and power output against the legacy model. Keep
 the old pneumatics and control logic initially (so floaters still toggle buoyancy instantly as before) to
 isolate variables. (2) Then integrate the pneumatic system upgrade (Stage 3) with CoolProp and
 SimPy events. At this point, floaters will fill gradually – test again that power output and cycle timing
 remain reasonable, adjusting the fill duration to mimic the original cycle timing unless the goal is to
 intentionally change it. (3) Next, integrate the drivetrain/flywheel and generator improvements
 (Stage 4). After this, the mechanical simulation is fully Chrono-based and the electrical output is via
 PyPSA. Test the system’s steady-state: it should reach an equilibrium speed and power; compare this
 with the prior stage to ensure consistency (accounting for efficiency differences). (4) Integrate the
 advanced control (Stage 5) to coordinate everything. This is last because it depends on the others.
 Now test the entire simulation end-to-end: start, run, change parameters, stop – ensure no part is
 breaking or producing nonsensical data. At each integration step, maintain an option (maybe a
 config flag) to fall back to the previous logic for validation. For example, keep a boolean in settings
 like 
use_new_pneumatics ; when false, use the old instant fill method. This helps verify that under
 identical conditions, the new model doesn’t inadvertently introduce bugs (differences should be
 explainable by the improved physics, not errors). Over time, once confident, these legacy code paths
 can be removed, fully replacing legacy logic with the new models.
 Real-Time Loop and UI Responsiveness: With all pieces in place, one critical check is real-time
 performance. The simulator should ideally run faster than or equal to real wall-clock speed for a
 given scenario, to allow live visualization. We will profile the simulation loop to identify any slow
 points. If, say, PyChrono’s step or CoolProp calls are taking significant time, we consider
 optimization. One approach for heavy computations is using Numba or JAX to accelerate Python
 code. For instance, if we had a very large number of floaters (hundreds) and were computing forces
 in Python, we could JIT-compile that section. JAX could even allow running those calculations on GPU
 for massive simulations, although in our current scale it may not be necessary. We also consider
 multi-threading for performance: Chrono itself might be able to use multiple threads internally
 (Chrono has a parallel mode for collision detection, etc. , though our scenario is not collision
heavy). If the simulation loop still has headroom, we might utilize Python’s threading or asyncio to
 12
 18
5
 offload tasks that don’t need to be synchronous. For example, logging or writing data to disk can
 happen in another thread to not stall the physics. If using Flask with SSE, ensure the SSE loop yields
 often enough to not time out the client – which is inherently handled by our background thread
 design . We will test UI interactions (like dragging a slider) while the sim is running to confirm
 there’s no lag in response; if there is, we might throttle some physics updates (e.g., update UI values
 every 2nd tick instead of every tick). The simulation controller design from earlier ensures thread
safe parameter updates
 15
 • 
, so quick changes won’t corrupt state.
 Code Structure and Maintainability: All new components should be organized according to the
 project’s modular architecture. We maintain a clear separation: physics models in 
subpackage, UI in 
dashboard/ or Flask app, utils in 
simulation/
 utils/ , etc. Each subsystem (floater,
 pneumatics, drivetrain, control, etc.) remains in its own module/class with a clean interface .
 This means, for example, the 
36
 38
 37
 Floater class handles its own physics and doesn’t directly
 manipulate others – it might call environment for drag, but it doesn’t reach into drivetrain, etc.
 Communication between modules happens through the SimulationEngine/Controller orchestrating
 them or via well-defined calls (e.g., control calls pneumatics which in turn affects floaters). This
 adheres to encapsulation and makes testing easier. We add docstrings and comments to all new
 classes and methods, explaining usage and assumptions. The design is aligned with real KPP
 components, which aids readability . We also apply consistent coding standards (naming,
 formatting) as outlined in any project guidelines or PEP8. For error handling, we use the logging and
 exception framework established in the project . For instance, if CoolProp fails to find a fluid
 property, we catch that and log a meaningful error (perhaps falling back to an approximate
 constant). We add debug logging in critical places (force calculations, state changes) which can be
 enabled for troubleshooting . This is especially important given the added complexity – it will help
 future developers or researchers to trace what’s happening, e.g., confirming that an injection event
 was triggered at the right time and the forces on floaters changed accordingly.
 39
 41
 • 
40
 Dependency Management: Incorporating multiple advanced libraries means we must manage
 dependencies carefully. We will update the project’s 
requirements.txt or environment file to
 include versions for PyChrono, PyDy/Sympy, CoolProp, SimPy, PyPSA, FluidDyn, JAX/Numba (if used)
 etc. It’s crucial to document the installation process because some of these (PyChrono especially)
 may require specific steps or have large binaries. For example, PyChrono can be installed via conda;
 we might recommend in documentation: “Install PyChrono via 
conda install -c 
projectchrono pychrono for your platform” since that provides pre-compiled binaries . If
 using pip, ensure the pip package is available and note any version constraints (e.g., PyChrono
 version that matches Chrono 7 vs 6). We also consider platform compatibility: Chrono and possibly
 FluidDyn might have OS-specific issues; we’ll test on Windows (the target per design) and ideally
 Linux. In requirements, pin versions that we tested (to avoid surprises from future major changes).
 For PyPSA, which is pure Python, a specific version pin (like 
7
 pypsa>=0.18 ) ensures we have the
 needed features. JAX is optional; if included, note that installing JAX with GPU support requires a
 separate step (which we might outline but possibly leave commented out if not everyone has GPUs).
 We might modularize these such that the simulator can still run without certain extras: e.g., one
 could run the simulation without PyPSA if they only care about mechanical power (the code would
 then default to the old efficiency calc). To enable that, we could catch ImportError for PyPSA and
 issue a warning, continuing with a fallback. Similarly for FluidDyn – if not installed, just use basic
 drag. This gives flexibility. However, if the goal is to use all advanced features, we can require them
 all and instruct the user to install everything. Packaging-wise, if this project is to be distributed, we
 19
might consider grouping these heavy libs as an extra (like 
pip install kpp-simulator[full] ).
 For now, listing them in documentation and requirements is sufficient. We will also manage internal
 dependencies: our modules should import each other carefully to avoid circular imports. Likely, the
 SimulationEngine will import all modules to tie them together. Control will import pneumatics (to call
 injection) and drivetrain (to toggle clutch). We should structure it so that lower-level modules (like
 Floater, Pneumatic) do not import higher ones. Using events and callbacks can help decouple; for
 example, Floater doesn’t need to know about control – it just exposes properties that control reads.
 This was in place in the pre-upgrade design and we continue that separation .
 38
 • 
• 
Testing and Validation: Before declaring success, we conduct thorough testing of the upgraded
 simulator. This includes unit tests for each module if possible: e.g., test Floater alone by applying a
 buoyant force and seeing if Chrono moves it correctly; test Pneumatic calculations by verifying that
 injecting a floater increases buoyancy gradually and that compressor energy usage matches
 theoretical values in a simple scenario (we can compare to hand calculations or a small script); test
 the control timing by logging events and ensuring the intervals are correct. Automated tests can be
 added to a 
43
 44
 tests/ directory, leveraging the modular design to instantiate modules in isolation
 . Additionally, we do system-level tests: run the full simulation for a few cycles and check
 conservation of energy (does the energy from buoyancy minus losses equal electrical output within
 expected range?), check that enabling/disabling each hypothesis (H1, H2, H3) has the qualitative
 expected effect (e.g., turning H1 on should result in a measurable drop in drag power losses and
 increase in net power). We also want to ensure no regression: run the new simulator with all
 enhancements off versus the old simulator – outputs like power and speed over time should align
 closely. Differences are acceptable only where the old model was simplistic and the new one is more
 realistic (we document those). Finally, we test the UI manually: use the web interface to adjust
 parameters and see that simulation responds (floaters should still animate, charts update, etc.). Pay
 attention to edge cases like extremely high injection rate, or zero load on generator, or a floater
 getting stuck (which shouldn’t happen physically, but maybe if a parameter is weird). Our improved
 error handling will help catch any “PhysicsError” or similar if something goes out of expected bounds
 . 
45
 42
 10
 Preserving Simulator Functionality: Even after replacement of all legacy logic, the simulator’s
 primary functionality – providing a real-time, interactive simulation of the KPP – is preserved or
 enhanced. Backward compatibility means a user familiar with the old simulator can use the new one
 without re-learning it. All inputs (floater count, volume, injection timing, etc.) remain the same, just
 more accurately used. All outputs (power curves, efficiency calculations, state displays) remain,
 possibly with additional insight. The UI will continue to use Chart.js graphs or the Dash dashboard,
 but now fed by the new core. If the UI was built on Flask with SSE and Chart.js, we ensure our
 simulation thread pushes data with the same JSON schema, so the existing JavaScript doesn’t break.
 If moving to Dash, we translate the same data into callback outputs – either way, from the user’s
 perspective, the charts look familiar. We will confirm that things like data logging to CSV still work
 (the data logger likely reads from simulation variables or logs we maintain; we updated those to
 capture the new model’s data, e.g., including per-floater details if needed, as blueprint suggests
 future expansion to log every floater’s state ). Where we have changed internals, we either hide it
 or document it. For example, the user might not know that we now use PyPSA for the generator 
they just see a “Generator efficiency” parameter like before. If we’ve introduced any slight changes in
 behavior (like a short delay in floaters reaching full buoyancy), we can mention it in release notes as
 an improvement but generally it won’t confuse users since the concept remains the same.
 46
 20
Importantly, the simulator stability and reliability should improve: thanks to better numerical
 integration, there should be fewer unrealistic jumps, and thanks to structured code, fewer bugs from
 tangled logic. The UI response should be at least as good as before – our thread-based approach
 ensures that heavy physics calculation doesn’t freeze the webpage . If anything, by smoothing
 the physics, the UI might appear more fluid. 
Conclusion and Future Work: At this point, the legacy physics code can be fully retired and replaced
 with our modern physics layer. We have implemented a world-class standard simulation: using a
 proven physics engine (Chrono) for multibody dynamics, a thermodynamic library (CoolProp) for
 accurate fluid properties, a discrete-event simulator (SimPy) for proper sequencing, and a power
 systems tool (PyPSA) for electrical modeling – all integrated into the KPP simulator architecture. The
 code is organized, documented, and maintainable. We have preserved backward compatibility and
 real-time interactivity, so users can transition to the new simulator without issues while enjoying far
 more realism. Looking forward, this robust foundation allows exploring advanced control techniques
 (even AI-based control by leveraging the modular design to plug in an RL agent ), scaling up the
 simulation (perhaps simulating multiple KPP units or longer time spans by leveraging JAX for speed),
 or coupling with external tools (like CFD or grid simulators) with minimal changes to the core
 structure . This staged implementation ensures that each improvement is validated and the
 overall system performance remains excellent. The result is a cutting-edge simulation platform for
 the Kinetic Power Plant concept, ready for both interactive use and rigorous analysis.
 Sources:
 KPP Simulator Architecture Blueprint – module structure and subsystem definitions
 Project Chrono Documentation – PyChrono physics engine capabilities
 KPP Design Specification – buoyancy, drag, and system forces in KPP
 SimPy Documentation – process-based discrete-event simulation (real-time stepping)
 PyPSA Documentation – power system analysis toolbox for generator and network modeling
 FluidDyn Documentation – Python framework for fluid dynamics research (for future fluid modeling)
 Upgrade Design Notes – performance tuning and parallelization considerations in simulator
 architecture
 KPP_SIMULATOR_BLUEPRINT.md
 https://github.com/Tonihabeeb/KPP/blob/66187363172d220a01bbc9310618c5ff34e888d0/KPP_SIMULATOR_BLUEPRINT.md
 guidev4.md
 https://github.com/Tonihabeeb/kpp-calc/blob/8c02a82ab86efe686aca463058b50afa395446b8/done-upgrades_files/guidev4.md
 Project Chrono - An Open-Source Physics Engine
 https://projectchrono.org/
 PyDy: Multibody Dynamics with Python — PyDy Website
 https://www.pydy.org/
 Welcome to CoolProp — CoolProp 6.8.0 documentation
 http://www.coolprop.org/contents.html
 5
 • 
33
 47 48
 1. 1 3
 2. 6 7
 3. 9 10
 4. 26 27
 5. 30
 6. 
20 21
 7. 
13 5
 1 2 3 4 9 10 14 16 17 24 25 28 31
 5 13 15 22 23 29 32 33 34 35 36 37 38 39 40 41 42 43 44 45 46 47 48
 6 7 11 12
 8
 18
 21
19
 CoolProp/CoolProp: Thermophysical properties for the masses
 https://github.com/CoolProp/CoolProp
 20
 21
 FluidDyn documentation — FluidDyn 0.9.0 documentation
 https://fluiddyn.readthedocs.io/en/latest/
 26
 27
 Overview — SimPy 4.1.2.dev8+g81c7218 documentation
 https://simpy.readthedocs.io/en/latest/
 30
 PyPSA: Python for Power System Analysis | Journal of Open Research Software
 https://openresearchsoftware.metajnl.com/articles/10.5334/jors.188
 22