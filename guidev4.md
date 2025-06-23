KPP Simulator Pre-Stage Upgrade Implementation
 Guide
 1
 Overview: This guide details a comprehensive restructuring of the Kinetic Power Plant (KPP) simulator
 codebase into a robust, modular, and scalable architecture. The pre-stage upgrade focuses on reorganizing
 the simulation into discrete components and establishing a solid foundation for future enhancements (real
time physics, visualization, hypothesis modules H1–H3, dynamic control, etc.). The design emphasizes
 modularity, clarity, and extensibility , aligning the code structure with the KPP subsystems and future
 upgrade stages. Each section below addresses a key aspect of the implementation plan, including project
 layout, module interfaces, error handling, coding standards, simulation loop design, Flask integration,
 configuration management, and code examples. All code is targeting Python 3.10+ on a Windows
compatible platform, using Flask as the web UI backend.
 1. Directory Structure & Project Layout
 We will adopt a clean, scalable project structure that clearly separates core concerns: the simulation
 engine, physical models, web application (Flask UI), utilities, configuration, and assets. This separation of
 concerns makes the system easier to navigate and extend . Below is a proposed directory tree:
 1
 2
 KPP_Simulator/                     # Root project directory
 ├── app.py                   # Flask app initialization and main routes (UI 
entry)
 ├── simulation/              # Simulation package
 │   ├── __init__.py
 │   ├── engine.py            # Simulation engine class (core loop orchestration)
 │   ├── controller.py        # Real-time simulation controller (orchestrator)
 │   └── components/          # Physical model components (modular subsystems)
 │       ├── __init__.py
 │       ├── floater.py       # Floater dynamics module (buoyancy, motion)
 │       ├── chain.py         # Chain & motion integration module
 │       ├── fluid.py         # Fluid system module (water properties, drag, H1)
 │       ├── thermal.py       # Thermal modeling module (heat exchange, H2)
 │       ├── drivetrain.py    # Drivetrain & gearbox module
 │       ├── generator.py     # Generator & power calculation module
 │       └── control.py       # Control system module (clutch, valves, 
injections, H3)
 ├── config/
 │   ├── __init__.py
 │   ├── config.py            # Configuration logic (defaults, loading JSON/YAML)
 │   └── default_config.json  # Example configuration file (JSON format for 
parameters)
 1
├── utils/                   # Shared utilities and helpers
 │   ├── __init__.py
 │   ├── errors.py            # Custom exception classes and error handling hooks
 │   └── logging_setup.py     # Logger configuration (optional, can also be in 
config.py)
 ├── routes/                  # Flask blueprint routes
 │   ├── __init__.py
 │   ├── stream.py           # SSE streaming endpoint blueprint (for real-time 
data)
 │   └── simulation_api.py   # Simulation API blueprint (e.g., to start/pause 
sim, set params)
 ├── templates/               # HTML Jinja templates for the web UI
 │   ├── index.html          # Main UI page with input form and visualization 
placeholders
 │   └── simulation.html     # Simulation page or results dashboard
 ├── static/                  # Static assets (CSS, JS, images for UI)
 │   └── js/                 # (e.g., client-side SSE/EventSource handling, 
Chart.js code)
 ├── tests/                   # Unit tests for modules (optional, for future QA)
 │   └── ...                
├── CONTRIBUTING.md          # Contribution guidelines (code style, naming, 
etc.)
 ├── README.md                # Project README with overview and setup 
instructions
 └── requirements.txt         # Python dependencies (Flask, numpy, etc.)
 Structure Rationale: This layout groups similar functionality together, making it easier to maintain and
 extend. The 
simulation/ package contains the core physics engine and subcomponents (floaters, fluid,
 etc.) isolated from any UI code. Each major physical subsystem is implemented in its own module under
 simulation/components/ . The Flask web application lives in 
3
 app.py (and 
routes/ for route
 definitions), with templates and static files in dedicated folders, cleanly separating the web interface from
 simulation logic . Shared utilities (like error handling and logging) and configuration files are likewise
 isolated. This modular project structure will allow independent development and testing of each component
 and clearly delineates responsibilities between the backend simulation and frontend interface .
 1
 2. Module Interface Definitions
 4
 2
 In the new design, each major subsystem of the KPP simulator is encapsulated in a dedicated module or
 class with a well-defined interface. This object-oriented approach ensures that components mirror the real
 system’s subsystems and interact via clear contracts . Below we define interfaces for each component
 module, including key classes, attributes, and methods (with suggested signatures and docstrings). The
 emphasis is on clarity and extensibility – each module can be developed and tested independently, and
 future enhancements (e.g. hypothesis H1–H3 effects) can be integrated by extending these interfaces.
 • 
Floater Dynamics Module (
 floater.py ): Represents the buoyant floater objects and their
 motion dynamics. This defines a 
Floater class (or 
FloaterDynamics ) for an individual floater. 
2
Attributes might include physical properties like 
volume (volume of floater), 
mass , and 
area
 (cross-sectional area for drag), as well as state variables such as 
position (vertical position or
 angle along the loop), 
velocity , and a flag for whether the floater is filled with air or water
 • 
• 
• 
• 
• 
• 
• 
• 
• 
• 
• 
(is_filled). Methods should include: 
update(dt: float) -> None : Calculate forces on the floater for the current state and time-step 
dt (buoyant force, gravitational force, drag force) and update its kinematic state (velocity and
 position). This could use Euler integration or another integration scheme. For example, compute net
 force 
F_net = F_buoyancy - F_gravity - F_drag and then update 
mass)*dt and 
position += velocity*dt . The 
velocity += (F_net/
 update method encapsulates how a single
 f
 loater’s state evolves in one simulation step.
 compute_buoyant_force() -> float : Compute the upward buoyant force on the floater (e.g. 
ρ_water * volume * g ), possibly considering partial submergence or variable density if H1/H2
 are active.
 compute_drag_force() -> float : Compute the drag force opposing motion (
 ρ_water * A * v^2 ), using the floater’s velocity and properties .
 0.5 * C_d * 
5
 6
 (Other helper methods as needed, e.g. to toggle floater fill state or compute weight = 
Each floater instance can also hold a reference to global parameters like gravity 
mass * g ).
 g and fluid density;
 these can be passed from a Fluid/Environment module or taken from config constants.
 Chain & Motion Integration Module (
 chain.py ): Manages the kinematic coupling of multiple
 f
 loaters on the endless chain loop and their synchronized motion. We can define a 
Chain (or
 ChainMechanism ) class. Responsibilities: ensure that floaters move together in a loop, and
 handle transitions at top and bottom (e.g. resetting a floater’s position from top to bottom once it
 completes a cycle). Attributes may include a list of 
floater objects (or references to all floaters
 on the chain), the loop length or vertical span, and perhaps the sprocket radius or chain speed.
 Methods could include:
 advance(dt: float) -> None : Move the chain and all attached floaters by one time step 
dt .
 This might involve rotating the chain by a small angle proportional to floater velocity and updating
 each floater’s position along the loop. Essentially, this ensures each floater’s 
position is updated
 consistently (e.g., if one floater goes up, another comes down). It may call each floater’s 
update
 method or impose constraints (like constant spacing between floaters).
 synchronize(floaters: List[Floater]) -> None : (If needed) re-align or initialize floaters
 on the chain (e.g., evenly distribute floaters along the loop at start).
 The Chain module might also compute chain tension or slip if needed, but initially it can be a simple
 kinematic integrator linking floater motions.
 Fluid System Module (
 fluid.py ): Provides water/fluid properties and calculations, including
 effects of nanobubble injection (Hypothesis H1) on fluid density or drag. This could be implemented
 as a class 
Fluid or as a set of functions in the module. The interface should supply:
 Constants: e.g. 
density of water (ρ_water), perhaps viscosity or others if needed. These can be
 loaded from configuration (default 1000 kg/m³ for water) .
 get_density() -> float : Return the current effective water density. If nanobubble H1 is active,
 7
 this may return a reduced density (e.g. 
ρ_effective = ρ_water * (1 - nb_fraction) if 
3
8
 • 
• 
• 
• 
• 
• 
• 
• 
• 
• 
nb_fraction is the fraction of volume composed of nanobubbles) . The fraction or effect
 magnitude can be part of parameters.
 compute_drag(C_d: float, area: float, velocity: float) -> float : Compute drag
 force using the drag equation
 9
 a method of 
 given a drag coefficient and floater parameters. This could also be
 Fluid class if stateful (for example, if drag coefficient could be altered by
 nanobubbles).
 If using a class 
FluidEnvironment , attributes might include global fluid properties (density,
 temperature, nanobubble fraction, etc.), which can be updated by other modules (e.g., a control
 system injecting nanobubbles could adjust a property here).
 Note: For simplicity, initial implementation can treat these as pure functions or static methods since
 water properties are mostly static (with optional modifiers for H1/H2). This module centralizes fluid
related calculations and constants.
 Thermal Modeling Module (
 thermal.py ): Handles thermal effects and near-isothermal
 expansion modeling (Hypothesis H2). This module can adjust buoyancy calculations or fluid
 properties based on temperature or heat exchange. An example interface could be a class
 ThermalModel or functions:
 adjust_density_for_temperature(base_density: float, water_temp: float, 
ref_temp: float=293) -> float : Calculate effective water density given a temperature
 difference (e.g., using a linear expansion coefficient α: 
ρ_eff = ρ_base * (1 - α * ΔT) as a
 simple model)
 8
 10
 . In an isothermal expansion scenario, the idea is that warmer water or
 expanding air could reduce water density or otherwise boost buoyancy – the exact model can be
 refined, but the interface should allow computing modified forces.
 compute_thermal_buoyancy_gain(...) -> float : Alternatively, compute additional upward
 force or efficiency gain from thermal assistance.
 The Thermal module might also include modeling of heat exchange: e.g. if each floater has an
 internal air volume, track its temperature and pressure. For now, we keep it abstract – the module
 should expose a way for the floater update to incorporate thermal effects (perhaps by altering fluid
 density or directly providing a buoyancy correction factor).
 Drivetrain & Gearbox Module (
 drivetrain.py ): Represents the mechanical drivetrain that
 converts the chain motion into generator input. We define a class 
Drivetrain that encapsulates
 gears, shafts, and possibly a flywheel (for hypothesis H3 pulse-and-coast). Attributes might include
 gear ratio between the chain sprocket and generator, drivetrain efficiency (losses), and optionally a
 f
 lywheel inertia or clutch state. Methods:
 compute_torque(chain_force: float) -> float : Calculate the torque delivered to the
 generator shaft given the net force on the chain and the sprocket radius (τ = F_net * R) . This
 could also factor in gear ratio: e.g. output torque = chain_torque * gear_ratio (if gear ratio < 1, it
 increases speed at cost of torque).
 apply_load(generator_torque: float) -> float : Determine how the generator’s
 resistance (load torque) feeds back to the chain. For instance, the module could reduce chain
 acceleration based on generator load (ensuring energy consistency).
 11
 4
• 
update(dt: float, chain_speed: float) -> float : Step the drivetrain dynamics forward
 by dt, possibly updating the rotational speed of the generator or flywheel. It could return the
 generator’s angular speed or similar. This is a placeholder for more detailed dynamics (e.g. if
 simulating rotational inertia).
 • 
• 
• 
• 
• 
• 
• 
• 
(Future H3 integration: manage a flywheel’s speed and a clutch that can disengage the generator. In
 H3 pulse mode, the control might periodically disconnect the generator to let the flywheel spool up,
 then reconnect to extract energy. The interface might include methods like 
engage_clutch() /
 disengage_clutch() and modeling of flywheel stored energy. In this pre-stage, we just ensure
 the structure can accommodate these.)
 Generator & Power Calculation Module (
 generator.py ): Calculates electrical output from
 mechanical input. The 
Generator class (or module) would focus on converting torque and
 rotational speed into power. Attributes might include generator efficiency, rated capacity, and any
 electrical parameters needed. Methods:
 compute_power(torque: float, angular_speed: float) -> float : Compute
 instantaneous power output (e.g. P = torque * ω, potentially multiplied by efficiency factor and any
 unit conversions). This gives the power generated at a given moment.
 update(dt: float, input_torque: float) -> None : Optionally, update internal state (if
 tracking generator speed or an electrical subsystem). If we assume quasi-steady state, the generator
 might not need complex state; but if including electrical dynamics or capacitor storage, it could be
 expanded.
 The generator module could also accumulate energy output over time, or integrate with a future
 power electronics model (for grid interface or storage). For now, its interface is mainly to provide
 calculated power outputs from mechanical inputs.
 Control System Module (
 control.py ): Encapsulates the control logic for valves, air injection,
 clutch operation, and other active controls. We define a class 
ControlSystem (or 
Controller ).
 In this pre-stage, the control logic will be simplistic or a stub, but we lay out the interface for future
 development (which might involve rule-based logic or an AI agent). Attributes may include
 references to other components it controls (e.g. it may hold or be given pointers to the
 Drivetrain , 
Floaters , and 
Air Injection/Venting system to actuate them). It might also
 track setpoints or mode (manual vs. automated, etc.). Methods:
 update_control(sim_state) -> None : Examine the current simulation state (e.g. positions of
 f
 loaters, generator speed, etc.) and issue commands to actuators. For example, if a floater reaches
 the bottom, the control system would trigger the air injection valve to fill it; when it reaches the top,
 trigger venting. Similarly, it could engage/disengage the clutch or adjust a throttle on the generator
 torque. In the pre-stage, we can implement a placeholder that, for instance, automatically opens/
 closes valves based on floater position thresholds or simply logs actions. The method can accept a 
sim_state object or the main simulation engine as context.
 set_parameter(name: str, value: Any) -> None : Provide a way to adjust control
 parameters (like enabling/disabling H1, H2, H3 or setting a control mode) at runtime. This will be
 useful when hooking up UI controls (sliders to change nanobubble percentage, etc.).
 5
• 
• 
• 
• 
• 
• 
• 
Note: This module is designed to allow plugging in advanced logic later. We could define a base class
 ControlStrategy and subclass it for different strategies (manual, PID, or RL agent). For now,
 ControlSystem can be a concrete simple controller.
 Real-Time Simulation Controller (
 controller.py ): Coordinates the simulation loop in real-time
 and integrates with the Flask app for live updates. We propose a class 
SimulationController (or
 RealTimeController ) responsible for managing the simulation thread or generator for
 streaming. Responsibilities: starting and stopping the simulation loop, keeping track of time, and
 ensuring thread-safe communication of simulation data to the web layer. Methods:
 start(sim_engine: SimulationEngine) -> None : Begin the simulation loop, possibly in a
 background thread or asynchronous task. This could set up a thread that calls 
sim_engine.run()
 repeatedly and pushes data into a queue or directly yields to an SSE response. In the simplest case
 (using Flask’s SSE generator), this might not need an explicit thread if using the generator pattern 
but having a controller class allows more flexibility (for example, switching to a model where the
 simulation runs continuously and clients can attach to the stream).
 stop() -> None : Gracefully stop the simulation loop. In a threaded model, this might signal the
 thread to exit.
 is_running() -> bool : Status check.
 The controller can also mediate real-time parameter changes: e.g., if the user adjusts a parameter
 via an API call, the controller can update the running simulation’s parameters on the fly (by invoking
 methods on 
sim_engine or 
control module).
 Integration with Flask: The controller might not be strictly necessary for the initial SSE approach
 (since Flask can yield from the simulation loop directly), but designing it now provides a clear place
 to add real-time synchronization features later (like ensuring simulation steps align with wall-clock
 time, or coordinating multiple clients). For now, we may implement a minimal controller or even
 combine this with the 
engine logic, but we document it as a separate concept for clarity.
 Each module/class will include docstrings explaining its purpose and usage. The design follows solid OOP
 principles: for example, one could create an abstract base class for simulation components (if desired) to
 enforce an 
update() interface across floaters, drivetrain, etc., but that can be overkill – instead we simply
 ensure each has a clearly documented update method where appropriate. By structuring into classes/
 modules as above, we align with the real KPP system components , making it easier to reason about
 and extend (e.g., adding a new “floaters” type or an alternate fluid model would mean adding/modifying a
 module, without altering unrelated parts).
 12
 3. Error Handling and Debugging Hooks
 13
 Robust error handling is built into the design to aid debugging and ensure the simulator fails gracefully if
 something goes wrong. We will embed logging and exception handling throughout the code at function,
 class, and module levels:
 • 
Logging with Python’s 
logging module: Each module will get its own logger (using 
logging.getLogger(__name__) so that logs are namespaced by module). We'll configure the
 logging system globally (for example, in 
logging_setup.py or at the start of 
app.py ) to output
 timestamps, module names, and severity levels in each message. For instance, using a format like 
'%(asctime)s [%(levelname)s] %(name)s - %(message)s' will give structured trace
 6
outputs that include where (which module) a message came from. Logging levels will be used
 consistently:
 • 
• 
• 
• 
DEBUG: for fine-grained step-by-step information (e.g., forces calculated on each floater,
 intermediate values each loop iteration).
 INFO: for high-level events (e.g., simulation started/stopped, major state changes).
 WARNING: for abnormal situations that are handled (e.g., a configuration value out of expected
 range, using a fallback).
 ERROR/CRITICAL: for exceptions or critical failures (with stack traces).
 Example usage: inside 
Floater.update() , after computing forces, we might log a debug message:
 logger.debug(f"Floater {id}: pos={self.position:.2f}, vel={self.velocity:.2f}, 
F_net={net_force:.1f}N") . This would help trace the simulation progression when needed. The
 logging system will be configured so that in development or debug mode we can enable debug logs, while
 in normal run we might keep it at info or warning level to reduce verbosity.
 • 
• 
• 
• 
• 
Custom Exceptions: We will define custom exception classes in 
utils/errors.py to represent
 simulation-specific error conditions. For example:
 SimulationError(Exception) : a base class for all custom errors in the simulation.
 ConfigError(SimulationError) : for invalid configuration values (e.g., negative time step).
 PhysicsError(SimulationError) : for physically impossible situations or calculation errors (e.g.
 divide by zero in an equation, or non-convergent iteration in a future more complex solver).
 ControlError(SimulationError) : for issues in the control module (e.g., invalid state
 transitions).
 Using custom exceptions makes it easier to catch and handle specific errors at higher levels. For instance, if
 the simulation loop catches a 
PhysicsError , it could log it and safely stop the simulation rather than
 letting an unhandled exception crash the program.
 • 
Try/Except Wrapping & Debug Hooks: The main simulation loop (in 
engine.py ) will be wrapped
 in try/except blocks to catch any unexpected errors per iteration. If an exception is caught during a
 time-step update, the engine can log the exception with 
logger.exception (which logs the stack
 trace) for post-mortem analysis, and then either propagate the exception (to be handled by the Flask
 route and reported to the user) or handle it (e.g., stop the simulation and mark the state as error).
 For example:
 try:
 component.update(dt)
 except Exception as e:
 logger.exception("Error updating component %s: %s", component, e)
 raise
 This ensures we get a full traceback in the logs whenever something fails, aiding debugging.
 • 
Structured Trace Outputs: By using logging with consistent formatting and including relevant state
 info in messages, the debug output will serve as a “trace” of the simulation. We can even log at the
 start and end of each major function. For instance, at the top of 
log 
"Simulation started with params X" , and at the end 
SimulationEngine.run() we
 "Simulation finished after 
7
N steps" . In the control system, if a valve is opened or closed, log an info or debug message about
 it. These hooks not only help in debugging but also in understanding the sequence of events during
 the simulation.
 • 
• 
Assertions and Validations: Within methods, we can use assertions or explicit checks to validate
 critical assumptions (for example, ensure that fluid density is positive, or a floater’s mass is not zero,
 etc.). If an assumption is violated, raising a custom exception or assertion can halt the simulation in a
 controlled manner and provide a clear error message. Such errors would be caught by the
 surrounding try/except in the simulation loop and logged.
 Development Debug Mode: We might allow a “debug mode” flag in configuration which, when
 enabled, triggers more verbose logging or additional checks. For example, if 
DEBUG_MODE=True in
 config, the simulation might log each floater’s state each step. This can be controlled via config or
 environment variable and documented in CONTRIBUTING.md for developers.
 In summary, the simulator will fail loudly and informatively: any runtime issue should produce a clear log
 (and exception message if propagated) indicating where it happened and ideally the values involved. This
 will make future upgrades safer, as problems can be traced to their source. During this pre-stage, we set up
 the scaffolding for error handling, so that as new features are added, developers have a clear pattern to
 follow for logging and exceptions.
 4. Naming Conventions and Code Style
 We will enforce strict and consistent coding style across the project, following Python’s PEP 8 guidelines for
 naming and formatting. This not only makes the codebase clean and professional, but also easier for
 multiple contributors to work on. Key conventions include:
 • 
• 
• 
• 
• 
• 
Snake_case for functions and variables: All function names, methods, and variable names will use
 14
 lowercase with underscores to separate words . For example, 
time_step , 
compute_buoyant_force , 
total_time are in snake_case. This improves readability and is the Python
 standard.
 PascalCase (CapWords) for class names: Class names will use capitalized words concatenated, e.g. 
SimulationEngine , 
Floater , 
ControlSystem
 at a glance.
 15
 . This differentiates classes from functions
 Constants in UPPER_CASE: Any constant values (physical constants like 
G , 
RHO_WATER , or
 configuration keys that remain fixed) will be written in all caps. For example, 
GRAVITY = 9.81 .
 Module and file names: Lowercase, short, and descriptive (e.g. 
fluid.py , 
drivetrain.py ).
 Since our structure already groups modules in folders, we avoid overly long module names. This
 follows PEP 8’s recommendation that module filenames be lowercase (possibly with underscores) for
 consistency.
 Method and attribute naming: Follows function naming (lowercase_with_underscores). Accessor or
 boolean methods might be named like 
is_active or 
has_finished() to clearly indicate
 booleans.
 Formatting: We will use 4 spaces for indentation, no hard tabs, with a typical max line length
 around 79-100 characters (PEP 8 suggests 79 for code, 72 for comments; we can allow up to 100 if it
 8
improves readability). Code blocks will be separated by blank lines where appropriate, and we will
 include docstrings for modules, classes, and functions per PEP 257.
 • 
• 
• 
• 
• 
• 
Imports ordering: Use Python’s recommended order: standard library imports first, then third-party
 libraries, then local application imports, each separated by a blank line.
 Tools for enforcement: We recommend using flake8 as a linter to catch style issues and black as an
 auto-formatter to ensure consistent formatting. For example, black can be run before commits to
 automatically format the code (adhering to an 88 or 100 char line length as configured), and flake8
 can be part of a CI pipeline to flag any lint errors (unused variables, wrong naming, etc.). In the 
CONTRIBUTING.md stub, we will outline these practices:
 E.g., “All code should conform to PEP 8 style. Run 
black . before committing to format code. Use 
flake8 to detect any linting errors. Name variables and functions clearly in snake_case, classes in
 PascalCase. Write docstrings for all public classes and functions.”
 We will also mention using type hints (Python typing) as part of code style for clarity – since Python
 3.10+, we can take advantage of type annotations to make interfaces self-documenting. Contributors
 should include type hints for function parameters and return types in new code (as we will do in our
 skeleton).
 Commenting and Documentation: Code should be self-explanatory where possible, but complex
 logic will have comments. We will avoid unnecessary comments for trivial things (instead strive for
 self-documenting names), but we will include comments to explain non-obvious calculations or
 decisions. Module header comments can outline the module’s purpose.
 Docstrings: Each module, class, and function will have a concise docstring describing its purpose,
 parameters, and return values. For example, 
class Floater: """Represents a buoyant 
floater and handles its physics.""" , and method 
def update(dt): """Update 
floater's position and velocity by one time step dt.""" . This is crucial for
 maintainability and for generating documentation if needed.
 By enforcing these naming conventions and style rules, we ensure the codebase remains readable and
 maintainable as it grows. The CONTRIBUTING.md will serve as a quick reference for any new developer to
 understand these standards. Adhering to these standards from this pre-stage sets a professional tone and
 reduces technical debt in future stages.
 14
 (For reference, PEP 8 guidelines state: “Function names should be lowercase, with words separated by underscores
 as necessary” and “Class names should normally use the CapWords convention” , which are exactly the
 conventions we will follow.)
 5. Simulation Loop Staging and Integration Plan
 15
 The core of the simulator is the time-stepped simulation loop which advances the state of the system in
 increments of Δt. In this pre-stage, we will refactor the existing one-shot calculation (if the current code
 computes the outcome for a single cycle) into a robust loop that can simulate over time. This prepares the
 system for real-time execution and streaming.
 Time-Step Loop Design: We will implement the simulation engine (in 
engine.py ) as an extensible class
 SimulationEngine that manages the overall simulation state and orchestrates calls to component
 modules each time step. The main loop will look conceptually like:
 9
t = 0.0
 while t < total_time:
 # compute forces & updates for each component
 floater.update(dt)
 ... (other components update)
 t += dt
 record or yield outputs for this step
 This loop runs from 
t=0 to the configured 
total_time (for example, 10 seconds or one full cycle) in
 increments of 
16
 dt (time step, e.g. 0.1 s) . At each iteration, it invokes the necessary physics calculations
 and updates the state of each module. For instance, all floaters would update their positions/velocities, then
 the drivetrain computes new torque, the generator computes power, etc., using the state resulting from
 that time step.
 SimulationEngine Interface: The 
SimulationEngine class will encapsulate this loop and related
 functionality: - Attributes: It will store simulation parameters (perhaps in a 
config object), the current simulation time 
params dict or a structured
 current_time , the time step 
dt , total duration
 total_time , and contain or reference the component objects (e.g. a list of 
floaters , an instance of
 drivetrain , etc.). It may also maintain a results log or buffer for outputs (time series of key metrics). 
Initialization:
 __init__(params) will set up the simulation. For example, it might create the specified
 number of Floater objects (based on a parameter like 
floater_count ) and store them in
 self.floaters list. It will also initialize other components (drivetrain, generator, etc.) possibly with
 parameters from 
params . Global constants like gravity could be pulled from the config. - 
method: We can provide a method 
step()
 step() that advances the simulation by one time step (dt). This
 method would call 
update(dt) on each relevant component in the correct order, then compute any
 derived global metrics for that step (such as total torque or power). For instance: 1. For each floater in
 self.floaters : call 
floater.update(dt) (which updates its position/velocity based on forces). 2.
 After floaters are moved, determine net force/torque on the chain; pass that to drivetrain:
 drivetrain.update(dt, chain_speed) or compute 
chain_torque = sum(...) then
 generator_torque = drivetrain.compute_torque(chain_force) . 3. Update generator:
 generator_power = generator.compute_power(torque, angular_speed) . 4. Update control
 system (if any real-time control decisions each step): 
control.update_control(state) . 5. Advance the
 simulation time 
self.current_time += self.dt . - 
run() method: This can implement the full loop
 from start to finish. There are a couple of design options: - Batch mode:
 run() could simply loop
 internally and collect all results into a list, then return the list of results at the end (suitable for non-real-time
 use, e.g., generating a plot after simulation). - Generator mode: To better support real-time streaming,
 run() can be implemented as a generator that yields results at each time step. Flask can directly stream
 from this generator in an SSE route (see Section 6). For example, 
run() could yield a dictionary of output
 metrics at each iteration (time, positions, power, etc.). This follows the pattern of using a generator to
 stream simulation data . 
17
 We can actually implement both: have an internal loop that yields data, and if one wants a list, they could do
 list(engine.run()) . For pre-stage, we might focus on the generator usage since it aligns with real
time integration. - Pause/Resume capability: Though not fully required at this stage, we plan the structure
 to allow pausing. This could mean the loop checks some flag each iteration (set by the controller to break
 10
out). The 
SimulationEngine could expose methods 
pause() and 
resume() which the
 RealTimeController or Flask route can trigger. In a simple SSE generator scenario, pausing might be
 achieved by terminating the generator; resuming would require starting a new generator where it left off
 (which could be complex). A more advanced approach is to run the loop in a separate thread continuously
 and simply stop sending data when paused – but for now, a straightforward approach is acceptable (stop
 the loop when pause requested, perhaps via exception or flag, and return).
 Real-Time Integration Considerations: We intend for this loop to integrate with a real-time UI. For now,
 our loop will run as fast as possible for the given dt. In the future, if we want to synchronize with wall-clock
 (so that 1 second of simulation corresponds to 1 real second), we might introduce a 
time.sleep(dt) in
 each iteration of the SSE generator (or use a more sophisticated scheduler). In Stage 1 and Stage 2
 upgrades, the SSE approach was suggested (yielding from Flask route with 
18
 time.sleep(dt) to pace
 updates) . We will structure our code such that adding a delay is easy (e.g., in the SSE generator function,
 after 
sim.step() , do a 
time.sleep(dt) before yielding, to throttle to real-time). 
Data Logging: The simulation loop will accumulate results in a structured way. For example, after each
 step() , we create a dict with key outputs (time, positions, velocity, torque, power, etc.) and either append
 it to an internal list (for later use like downloading a CSV) and/or yield it via SSE. We might maintain
 self.log = [] inside 
SimulationEngine to collect time-series data. This log can later be accessed
 for offline analysis or saving to file. The Stage 2 design explicitly calls for a data logger for time-series ,
 which we are accounting for here.
 By designing the simulation loop in 
20
 19
 SimulationEngine to be self-contained and iterative, we prepare
 for Stage 1 and Stage 2 upgrades. Stage 1 introduced the concept of a time-stepping loop in place of a
 one-shot calc, and Stage 2 required streaming outputs and dynamic updates – our implementation aligns
 with those goals. In fact, the Stage 2 guide suggests having a Floater class and simulation loop updating
 each floater’s state each time-step , which is exactly what we implement. Moreover, by encapsulating the
 loop in a class, we make it easier to manage (start, stop, modify parameters on the fly) as opposed to a
 single procedural function.
 In summary, the SimulationEngine will act as the heart of the simulator, advancing all components in
 lockstep through time. It’s designed to be extensible: if we add a new component (say a new hypothesis
 module that affects forces), we can integrate it into the loop with minimal changes elsewhere. The next
 section will discuss how this loop ties into the Flask app via streaming.
 6. Basic Flask Integration Hooks
 To interface our simulation with users (for input and real-time visualization), we integrate it with a Flask web
 application. We set up the Flask app in a modular way using Blueprints for clarity, and prepare endpoints
 for starting the simulation, streaming data, and rendering a UI. Even though real-time streaming (SSE) will
 be fully realized in Stage 1/2, we implement the fundamental hooks now.
 Flask App Structure: In 
app.py , we will create the Flask application and register blueprints. We anticipate
 at least three blueprint groupings: - UI routes (maybe a blueprint or just routes in app.py): for rendering
 HTML pages (e.g., the main index page with the form, and perhaps a simulation dashboard page). In this
 simple setup, we can have an index route in app.py itself. - Simulation API routes (e.g., 
routes/
 11
simulation_api.py ): endpoints to handle user inputs, start/stop commands, parameter updates, etc. For
 instance, a POST route 
/start_simulation to accept form parameters and initialize a simulation (this
 could simply render the simulation page or kick off streaming). - Streaming routes (
 routes/stream.py ):
 an endpoint for Server-Sent Events (SSE) that continuously streams simulation data to the client.
 We will use Flask’s blueprint mechanism to organize these. For example, 
stream.py will define
 stream_bp = Blueprint('stream', __name__) and a route 
/stream on that blueprint. In
 app.py , we’ll do 
app.register_blueprint(stream_bp) .
 Starting Simulation: A typical flow could be: 1. User fills parameters on an HTML form and clicks "Start
 Simulation". 2. The form POSTs to 
/start_simulation route. We parse the inputs and perhaps store
 them (or merge into our config). 3. We then render a template (e.g., 
simulation.html ) that includes
 client-side code to connect to the SSE stream (using JavaScript EventSource). 4. The template (or an
 immediate redirect) causes the browser to open the SSE connection to 
/stream (including query params
 or using stored config on server side).
 In our pre-stage, we create the stub for 
/start_simulation and 
/stream . For now, /
 start_simulation can simply render a template and pass parameters, without starting any long process
 yet (since SSE will handle the actual loop). The heavy lifting happens in the 
/stream route.
 SSE Streaming Endpoint (
 /stream ): This route returns a streaming response that keeps the connection
 open and sends events as the simulation runs. Flask supports this by returning a 
Response with a
 generator function. We will implement something like:
 @stream_bp.route('/stream')
 def stream():
 # (Potentially initialize or reset simulation here)
 def generate():
 for step_data in sim_engine.run(): # sim_engine is an instance of 
SimulationEngine
 yield f"data: {json.dumps(step_data)}\n\n"
 yield "data: [DONE]\n\n"
 return Response(generate(), mimetype='text/event-stream')
 Key points: - The 
Content-Type (mimetype) is 
text/event-stream to indicate an SSE response. - Each
 message is prefixed with "
 data: " and followed by two newlines, per SSE protocol. - We use 
json.dumps
 to serialize our data dict to JSON string for each event. - After sending all data, we optionally send a special
 [DONE] event or simply let the generator end. (We've included a 
[DONE] marker to signal completion,
 which the client can detect if needed.)
 22
 21
 18
 This design is directly in line with Flask SSE usage examples . The SSE endpoint will push new metrics
 to the browser continuously . On the client side, a simple JavaScript can listen to these events and
 update the UI (e.g., updating charts or text fields in real-time).
 12
Blueprint and App Initialization: For modularity, 
routes/stream.py contains the above route, and we
 import and register it in 
app.py . Similarly, we could have 
routes/simulation_api.py with something
 like:
 sim_api_bp = Blueprint('sim_api', __name__)
 @sim_api_bp.route('/start_simulation', methods=['POST'])
 def start_simulation():
 params = {k: float(v) for k,v in request.form.items()}
 # Possibly store these params in a global config or session
 return render_template('simulation.html', params=params)
 This stub just passes parameters to a template. In a more advanced version, it might also initialize the
 SimulationEngine with those params and keep it ready. However, because our SSE route here is self
contained (it creates/uses the SimulationEngine inside), we might not need to persist it between the two
 routes for now. Simpler: the SSE route can read global config or default params (or query args).
 Error Logging in Flask: We will integrate our logging so that any exceptions in the Flask routes or during
 streaming also get logged. Flask by default will log to stderr on exceptions; we can improve by using our
 own logger. For instance, we might wrap the SSE generator in try/except to yield an error message event if
 something fails (and log it server-side). Additionally, we can use Flask's 
@app.errorhandler to catch
 unhandled exceptions and log them via our logging system, returning a friendly error to the user.
 Threading vs. Generator: Flask’s SSE approach as above works in a single thread (each request is handled,
 the generator yields over time). We must ensure the Flask app is run with 
threaded=True or in an
 environment that supports concurrency so that the streaming response doesn’t block the entire server .
 (In development, app.run(threaded=True) is fine; in production, a WSGI like gevent or gunicorn with
 appropriate workers can handle SSE.) If we wanted to run the simulation in a background thread separate
 from the request context, we could do that (start a thread on 
23
 /start_simulation and have 
/stream
 just feed from a queue). However, initially, the generator pattern is simpler. We'll note this in code
 comments as a potential future change if needed.
 UI Hooks: We create a basic 
index.html template with a form for inputs (number of floaters, etc.) and a
 "Start Simulation" button. After starting, 
simulation.html template (or the same page via AJAX) will
 have a section for results (like a placeholder for charts or text updates). We include a small JavaScript
 snippet to handle the SSE: 
<script>
 var source = new EventSource("/stream");
 source.onmessage = function(event) {
 if(event.data === "[DONE]") {
 source.close();
 console.log("Simulation complete");
 return;
 }
 13
var data = JSON.parse(event.data);
 // TODO: update HTML elements or charts with the data
 console.log("Received data:", data);
 };
 </script>
 This is a simple example of receiving events. In Stage 2, this would be expanded to actually plot charts using
 Chart.js and interactive controls
 24
 and working with minimal data.
 . For now, we just ensure that the pipeline from server to client is set up
 Blueprint for UI: Optionally, use a blueprint for UI (especially if we have multiple pages). It might be
 overkill, so we may keep UI routes in app.py for simplicity. E.g., 
@app.route('/')
 def index():
 return render_template('index.html')
 with an index template listing input fields.
 Security & Config: As this is a local simulation tool, we may not need user authentication. But we should
 use Flask’s best practices, like not exposing the server to the open internet without proper safeguards.
 That’s beyond scope, but worth a note in docs if relevant.
 In summary, the Flask integration in pre-stage will yield: - A working route to start the simulation (even if it’s
 stubby). - A working SSE route that streams dummy or basic simulation data in real-time to the client. 
Templates and JS ready to consume that stream. - The groundwork for more complex interactions (like a 
set_params endpoint to adjust parameters live, which Stage 2 mentions ). We won’t fully implement 
/
 22 /
 set_params now, but we design knowing we can add it easily (likely as part of 
simulation_api
 blueprint, updating the SimulationEngine or global config when called).
 By modularizing into blueprints, our Flask code remains organized. The Flask app is effectively the bridge
 between the simulation backend and the frontend visualization , and our implementation ensures the
 two sides are loosely coupled (communication via JSON messages over SSE, which is a clean interface).
 25
 7. Configuration and Parameters System
 Configuring the simulator’s many parameters (physical constants, simulation settings, toggles for
 hypotheses, etc.) in a flexible way is crucial. We will implement a centralized configuration system that can
 load parameters from a file (JSON or YAML) and provide them to the rest of the code.
 Global Constants and Defaults: Some values are universal constants (e.g., gravity 
standard water density 
g = 9.81 m/s^2 ,
 rho_water = 1000 kg/m^3 ). These can be defined in 
config/config.py or
 within a physics constants module. For accessibility, we might define them in 
config.py and import
 wherever needed, or attach them to a config object. For example: 
14
G = 9.81 # gravitational acceleration (m/s^2)
 RHO_WATER = 1000.0 # density of water (kg/m^3)
 DEFAULT_Cd = 0.8 # default drag coefficient (could be adjusted by H1)
 These constants could also live in a physics module; either way, they’re centralized for easy change.
 Simulation Parameters: These include time step 
dt , total simulation time, number of floaters, physical
 dimensions, and any toggles (like whether to enable nanobubble effect, etc.). We will create a default
 configuration dictionary in 
config.py that lists all such parameters with default values. For instance: 
DEFAULT_PARAMS = {
 "time_step": 0.1,
 "total_time": 10.0,
 "floater_count": 8,
 "enable_hypothesis": {"H1": False, "H2": False, "H3": False},
 "fluid": {"nanobubble_fraction": 0.0, "water_temp": 293.15}, # example 
nested config
 "drivetrain": {"gear_ratio": 1.0, "efficiency": 0.95},
 // ... other defaults ...
 }
 This dictionary provides baseline values that the simulation will use if not overridden.
 Loading from YAML/JSON: To allow users or developers to adjust configuration without modifying code,
 we support external config files: - We provide an example 
default_config.json (or 
.yaml ) in the
 config/ directory. This can contain any subset of parameters to override the defaults. - In 
config.py ,
 we implement logic to load this file at startup. For example, using Python’s built-in 
json library: 
import json, os
 config_path = os.path.join(os.path.dirname(__file__), "default_config.json")
 if os.path.exists(config_path):
 with open(config_path) as f:
 file_config = json.load(f)
 # Merge file_config into DEFAULT_PARAMS
 for key, val in file_config.items():
 if isinstance(val, dict) and key in DEFAULT_PARAMS:
 DEFAULT_PARAMS[key].update(val)
 else:
 DEFAULT_PARAMS[key] = val
 This way, any value specified in the JSON will override the default. We perform a deep merge for nested
 dictionaries (so one can override just a subfield like nanobubble_fraction without rewriting the whole
 nested structure). - If YAML is preferred, we could use 
PyYAML library (
 yaml.safe_load ). Since 
15
PyYAML might not be in baseline dependencies, JSON might be simpler using the built-in library. We will
 mention both options. For example, if a 
config.yaml is present, load it accordingly.
 Accessing Config in Code: There are a few patterns: - Global dict: Modules can import 
config and use
 config.DEFAULT_PARAMS['time_step'] . This is straightforward but requires referencing keys which
 could be error-prone (typos, etc.). - Dataclass: Create dataclasses for structured config. For instance,
 SimulationConfig as a dataclass with fields 
time_step: float , 
could 
then 
instantiate 
it 
from 
the 
total_time: float , etc. We
 DEFAULT_PARAMS 
dict 
(using
 SimulationConfig(**DEFAULT_PARAMS) , adjusting for nested dicts appropriately). This gives attribute
 access (e.g., 
config.time_step ). - Simple Namespace: Alternatively, convert the DEFAULT_PARAMS dict to
 an object (e.g., using 
types.SimpleNamespace or a custom class) for attribute-style access.
 For this stage, a dictionary is fine and flexible. We will ensure consistent usage: e.g., the engine will take
 params dict (either passing the whole DEFAULT_PARAMS or a copy of it possibly updated by user input).
 Components will take needed values from there. We prefer passing specific values to constructors rather
 than the whole dict to reduce coupling, but the engine could pass a reference to config to components if
 needed for dynamic updates.
 Environmental Config: Consider using environment variables or a 
.env file for configurations like debug
 mode, etc., but since this is primarily a code-driven config and possibly a desktop app scenario, we’ll stick to
 f
 ile-based config.
 Example: Suppose the user wants to change gravity or water density for an experiment (maybe testing on
 another planet or with saltwater). Instead of digging in code, they can copy 
default_config.json ,
 change G or 
RHO_WATER values, and restart the app – the new values will apply. Or for enabling a
 hypothesis, set 
"enable_hypothesis": {"H1": true} in the config file or via UI, and the simulation
 will incorporate it.
 Parameter Submission via UI: Through the Flask UI, when the form is submitted, we capture parameters
 (like floater count, etc.) and can override the config for that simulation run. We might merge those into
 DEFAULT_PARAMS or better, create a new params dict per run (so as not to globally change defaults). For
 instance, in 
/start_simulation , do: 
params = config.DEFAULT_PARAMS.copy()
 params.update(form_data_dict)
 and then use 
params for that simulation instance. The SSE route could retrieve these if stored (perhaps in 
session or a global variable). In the future, a dedicated 
/set_params endpoint can allow adjusting
 certain parameters mid-run (the SimulationController would handle applying them safely).
 In summary, the configuration system ensures all magic numbers are centralized and easily adjustable,
 and that simulations can be reconfigured without code changes. We support JSON (and by extension easily
 YAML if needed) for user-friendly config files. The code examples will illustrate loading a config and using it
 to initialize the simulation.
 16
8. Suggested Libraries and Tools
 We aim to use minimal yet powerful libraries to implement the above features. Here is a list of baseline
 libraries and tools that the project will use (or recommend), with their purpose:
 • 
• 
• 
• 
• 
• 
• 
• 
• 
• 
Flask – The web framework for building the UI and API endpoints. Flask provides the routing,
 templating (Jinja2), and server capabilities we need. It’s lightweight and suitable for this local
 simulation interface.
 NumPy – A fundamental package for numerical computations. Even if the physics is simple now,
 NumPy will be useful for vectorized calculations (e.g., if we later simulate arrays of floaters or need
 linear algebra for forces). It's also needed if we integrate any scientific computations. We can start by
 using it for any array-based math or to possibly optimize calculations inside update loops.
 typing (Python standard library) – We will use type hints (like 
List[float] , 
Dict[str, Any] ,
 etc.) to make the code self-documenting. The 
typing module provides these annotations. It also
 includes helpful types like 
TypedDict or 
Protocol if we want to formalize interfaces later.
 dataclasses (Python 3.10+ std lib) – We may use dataclasses for structured data objects like
 configuration or for simple containers (e.g., a dataclass for floater state could be an alternative to a
 class with only data). Dataclasses automatically generate init and repr methods, which is useful for
 logging state as well.
 logging (Python std lib) – As described, for logging debug and error information. We’ll use the built
in logging module to avoid external dependencies.
 queue (Python std lib) – If we implement threading for real-time simulation, the 
queue.Queue
 class can be useful to safely pass data from a simulation thread to the Flask thread. In the current
 SSE generator approach we may not need it, but we include it as a suggested tool anticipating
 possible use in Stage 2 if a background thread is used (the thread can put simulation data into a
 queue, and the Flask route thread can read from it).
 pytest (optional for testing) – We encourage writing tests for the physics modules and others.
 Pytest is a great framework for unit testing. For example, one could write tests for 
Floater.compute_buoyant_force() to ensure it matches expected values. This is optional but
 good for future development; we can include it in requirements for development.
 f
 lake8 and black (development tools) – As mentioned, flake8 (linter) and black (formatter) will be
 used to maintain code style automatically. Black ensures code formatting consistency, and flake8 will
 warn about unused variables, style issues, etc.
 Werkzeug and its SSE support – Flask’s SSE doesn’t need an extra library, but it’s good to know Flask
 is built on Werkzeug which handles the low-level details. We might rely on the Flask documentation’s
 SSE pattern (no separate install needed, just ensuring to yield with proper format).
 JSON/YAML parsing – Using Python’s 
json module (in std lib) for config. If YAML is desired, 
pyyaml could be added to requirements (not strictly baseline, but easy to add) to parse YAML
 config files.
 All the above libraries are cross-platform (Windows-friendly) and compatible with Python 3.10+. We ensure
 our code (e.g., type hints using modern syntax like 
list[int] which is 3.9+ short form) is using features
 available in 3.10.
 One more note: for future expansions like visualization, we might use Matplotlib for generating plots or
 Chart.js on the frontend. The Stage 2 mentions Chart.js for live charts , but that’s a frontend library
 (JavaScript). We don’t need Matplotlib in pre-stage, but we keep it in mind (the blueprint had a plotting
 24
 17
module). If we include any plot generation in the future (e.g., to show a static efficiency curve after run),
 Matplotlib could be listed in requirements as needed. For now, our focus is on the core simulation and
 streaming, not heavy plotting.
 To summarize, the required runtime libraries are minimal (Flask, NumPy), and the rest are either part of
 Python standard or for development. This keeps the installation lightweight. In the 
requirements.txt
 we would list at least: 
flask
 numpy
 (and possibly 
pytest for dev, plus 
matplotlib , 
pyyaml commented out or as optional). The guiding
 principle is to use well-supported libraries for reliability and future-proofing (e.g., using 
Gymnasium or 
Stable-Baselines3 for RL integration later, as hinted in the R&D blueprint
 later stages and are not baseline).
 9. Demonstration Code Files
 26
 – but those will come in
 Below we present minimal but functional code skeletons for key parts of the system. These code snippets
 illustrate how the classes and modules might be implemented following the above design. Each example
 includes docstrings and basic logic to show the structure. (In a real project, these would be fleshed out with
 full calculations, but here we focus on interfaces and integration points.)
 File: 
simulation/components/floater.py
 # simulation/components/floater.py
 from config import G, RHO_WATER
 class Floater:
 """Represents a buoyant floater in the KPP. Handles buoyancy and motion."""
 def __init__(self, volume: float, mass: float, area: float, Cd: float =
 0.8):
 """
        Initialize a Floater.
        :param volume: Volume of the floater (m^3)
        :param mass: Mass of the floater (kg) when filled with water
        :param area: Cross-sectional area for drag (m^2)
        :param Cd: Drag coefficient (dimensionless)
        """
 self.volume = volume
 self.mass = mass
 self.area = area
 self.Cd = Cd # drag coefficient
 self.position: float = 0.0 # vertical position (m or relative units)
 18
self.velocity: float = 0.0 # vertical velocity (m/s)
 self.is_filled: bool = False # whether currently filled with air 
(buoyant)
 # Note: if is_filled is False, assume filled with water (heavier).
 def compute_buoyant_force(self)-> float:
 """Compute buoyant force based on current floater state."""
 # Buoyant force = density of fluid * displaced volume * g.
 # If the floater is filled with air, it displaces its full volume; 
# if not (water-filled), buoyancy might be negligible (or volume of 
displaced water is small).
 displaced_volume = self.volume if self.is_filled else 0.0
 return RHO_WATER * displaced_volume * G
 def compute_drag_force(self)-> float:
 """Compute drag force opposing motion (simple quadratic drag)."""
 # Drag = 0.5 * C_d * rho * A * v^2, direction opposite to velocity.
 drag_mag = 0.5 * self.Cd * RHO_WATER * self.area * (self.velocity ** 2)
 # Apply direction: if moving upward (velocity>0), drag is downward 
(negative for position axis).
 if self.velocity > 0:
 return-drag_mag
 else:
 return drag_mag
 def update(self, dt: float):
 """
        Update floater's velocity and position over a time step dt using a 
simple physics integration.
        Considers buoyancy, gravity, and drag forces.
        """
 # Compute forces
 F_buoy = self.compute_buoyant_force()
 F_gravity =- self.mass * G # weight force (negative = downward)
 F_drag = self.compute_drag_force()
 # Net force (positive upward)
 F_net = F_buoy + F_gravity + F_drag
 # Acceleration (m/s^2) = F_net / mass
 a = F_net / self.mass
 # Update kinematics (Euler integration)
 self.velocity += a * dt
 self.position += self.velocity * dt
 # Boundary conditions (if top or bottom reached, handle in chain or 
control)
 # TODO: integrate with chain module for cyclic position reset at top/
 bottom.
 19
Explanation: This 
Floater class encapsulates the dynamics of a single floater. It computes buoyant force
 using Archimedes’ principle and drag force using a quadratic drag formula . The 
5
 6
 update() method
 applies Newton’s second law (F=ma) and integrates velocity and position over the time step. We included a
 simple check to invert drag depending on direction. The attribute 
is_filled is a placeholder to indicate
 whether the floater has air (making it buoyant) or is filled with water (heavy) – in a more complete model,
 this would toggle at bottom/top via the control system or chain logic. The class uses constants 
G and
 RHO_WATER from config for gravity and fluid density. We’ve marked where chain integration might handle
 resetting position when a floater goes over the top.
 File: 
simulation/engine.py
 # simulation/engine.py
 from simulation.components.floater import Floater
 from simulation.components.drivetrain import Drivetrain
 from simulation.components.generator import Generator
 from simulation.components.control import ControlSystem
 # (Import other components as needed, e.g., Chain, Fluid, Thermal)
 import logging, math
 logger = logging.getLogger(__name__)
 class SimulationEngine:
 """
    Core simulation engine that manages the KPP simulation loop.
    It holds the system components and advances the simulation in time steps.
    """
 def __init__(self, params: dict):
 """
        Initialize the simulation engine with given parameters.
        :param params: Dictionary of simulation parameters (time step, total 
time, counts, etc.)
        """
 self.params = params
 # Extract key parameters with defaults
 self.dt: float = params.get("time_step", 0.1)
 self.total_time: float = params.get("total_time", 10.0)
 self.current_time: float = 0.0
 # Initialize components based on params
 count = int(params.get("floater_count", 1))
 floater_vol = params.get("floater_volume", 1.0) # example volume per 
floater
 floater_mass = params.get("floater_mass", 50.0) # e.g., 50 kg when 
water-filled
 floater_area = params.get("floater_area", 0.2)
 # Create floaters
 20
self.floaters = [Floater(volume=floater_vol, mass=floater_mass,
 area=floater_area)
 for _ in range(count)]
 # Initialize other components
 self.drivetrain = Drivetrain(params.get("drivetrain", {}))
 self.generator = Generator(params.get("generator", {}))
 self.control = ControlSystem(params.get("control", {}))
 # (Chain and Fluid are not explicitly stored; floaters + drivetrain 
suffice for base)
 self.results_log = [] # will hold results dicts for each step 
(optional)
 logger.info("SimulationEngine initialized with %d floaters, dt=%.3f, 
total_time=%.1f",
 count, self.dt, self.total_time)
 def step(self)-> dict:
 """
        Advance the simulation by one time step (dt). Updates all components and 
returns metrics.
        :return: Dictionary of key metrics after this step (time, power, etc.)
        """
 # Update floaters dynamics
 for floater in self.floaters:
 floater.update(self.dt)
 # Compute net torque from floaters on drivetrain (simplified).
 # For simplicity, assume each floater contributes torque = F_net * R 
(with R a fixed radius).
 # Here we approximate net force from first floater for demo (in real, 
sum all appropriately).
 net_force = 0.0
 if self.floaters:
 # e.g., use first floater's net force via buoyancy minus weight 
(drag not contributing to lift on wheel ideally)
 f = self.floaters[0]
 net_force = RHO_WATER * f.volume * (1 if f.is_filled else 0) * G
f.mass * G
 torque = self.drivetrain.compute_torque(net_force)
 power = self.generator.compute_power(torque, angular_speed=1.0) # 
assume some angular speed or get from drivetrain
 # Control system update (e.g., might toggle floater fill state at 
boundaries)
 self.control.update_control(self)
 # Log or prepare output metrics
 metrics = {
 "time": round(self.current_time, 3),
 21
"torque": torque,
 "power": power
 }
 # (We could also include floater positions/velocities in metrics if 
needed)
 self.results_log.append(metrics)
 logger.debug("t=%.3f s: torque=%.2f Nm, power=%.2f W",
 self.current_time, torque, power)
 # Advance time
 self.current_time += self.dt
 return metrics
 def run(self):
 """
        Run the simulation from t=0 to t=total_time. 
        Generator that yields result metrics at each time step (for streaming or 
logging).
        """
 # Reset current time and optionally clear log
 self.current_time = 0.0
 self.results_log.clear()
 logger.info("Starting simulation loop...")
 # Loop until total_time is reached or exceeded
 while self.current_time < self.total_time- 1e-9:
 try:
 result = self.step()
 except Exception as e:
 # If any error in step, log and break out
 logger.exception("Simulation error at t=%.3f: %s",
 self.current_time, e)
 # Yield an error status (optional) or break
 result = {"error": str(e)}
 yield result
 break
 yield result
 logger.info("Simulation loop completed at t=%.3f", self.current_time)
 Explanation: The 
SimulationEngine manages multiple components. In 
__init__ , we extract
 parameters (time step, total time, number of floaters, etc.) from the provided params dict. We instantiate
 Floater objects in a list, and also create 
Drivetrain , 
Generator , and 
ControlSystem instances,
 passing in their respective config sub-dicts. In this minimal demo, 
Drivetrain and 
be simple (we will show skeletons next). The 
Generator might
 step() method updates each floater, then computes a net
 force and converts it to torque and power. We simplified the torque computation: in a real model, you’d sum
 contributions of all floaters on the ascending side minus descending, etc., but here we just approximate
 using one floater’s net buoyant force for demonstration. The 
ControlSystem.update_control(self)
 call passes the engine (so the control system can inspect global state and possibly modify components; for
 example, it could set 
floater.is_filled=True when position ~ bottom, etc.). 
22
The 
run() method is a generator that yields a results dict at each step, making it suitable for SSE
 streaming. We log the start and end of the loop. Any exception inside 
step() is caught; we log it and yield
 an error message in the stream then break out. This prevents the server from hanging silently if something
 goes wrong in the physics. With this structure, the 
/stream route can simply iterate over
 engine.run() and send each yielded dict to the client. 
We also maintain 
results_log – this could be used for a download or analysis endpoint, or to display
 f
 inal results. For instance, after run, one could take 
engine.results_log and save to CSV or compute
 summary statistics.
 (We used 
RHO_WATER and G inside step for quick net force calc; in practice, floaters themselves track forces,
 and drivetrain might integrate multiple floaters. This is a placeholder to show how components connect.)
 Note how logging is used at info level for major events and debug for each step’s data. This matches our
 error/debug plan.
 File: 
app.py
 # app.py - Flask application setup and main routes
 from flask import Flask, request, render_template, Response, jsonify
 import logging
 from routes.stream import stream_bp
 # from routes.simulation_api import sim_api_bp  (future blueprint for control 
endpoints)
 app = Flask(__name__)
 # Register blueprints
 app.register_blueprint(stream_bp)
 # app.register_blueprint(sim_api_bp)  # if we had one for /start_simulation, /
 set_params, etc.
 # Configure logging format (could also be done in config or main entry)
 logging.basicConfig(level=logging.INFO,
 format="%(asctime)s [%(levelname)s] %(name)s - %(message)s")
 @app.route("/")
 def index():
 """Render the main page with input form."""
 return render_template("index.html")
 @app.route("/start_simulation", methods=["POST"])
 def start_simulation():
 """
    Handle form submission to start a new simulation.
 23
    Parses input parameters and returns the simulation page.
    """
 # Parse user inputs from form (all are strings initially)
 user_params = {}
 for key, val in request.form.items():
 # Try to interpret as float or int where appropriate
 try:
 num = float(val)
 # If the number is an integer (e.g. count), store as int
 user_params[key] = int(num) if num.is_integer() else num
 except ValueError:
 user_params[key] = val # for non-numeric inputs, store raw
 # Here we could merge user_params into our config.DEFAULT_PARAMS if needed
 # For now, just pass them through via template or global
 return render_template("simulation.html", params=user_params)
 if __name__ == "__main__":
 app.run(debug=True, threaded=True)
 Explanation: In 
app.py , we create the Flask app and register the blueprint for streaming (and
 placeholder for other blueprints). We also set up basic logging configuration so that our logging from the
 simulation modules will output to the console with timestamps. We define an 
main page (with the form). The 
index route to serve the
 start_simulation route collects form inputs and converts them to
 numbers if possible. It then renders 
simulation.html passing the parameters (so the template or client
 script can use them). We do not actually start the simulation here — that will happen when the client opens
 the SSE stream. However, we could optionally kick off something or store the params (for example, save in a
 global or session for the stream route to use). In this design, we rely on either global config or query
 parameters to convey settings to 
/stream . For instance, if 
user_params contains a 
time_step , the
 template could initiate the stream with a URL like 
/stream?dt=0.05&floater_count=10 etc. (Not
 shown here for brevity.)
 Finally, we include the typical 
if __name__ == "__main__": app.run(...) to run the app in
 development mode. We use 
23
 threaded=True to ensure SSE can function without blocking other requests
 . In production deployment, this would be configured differently, but that’s outside scope.
 File: 
utils/errors.py
 # utils/errors.py
 class SimulationError(Exception):
 """Base exception for errors in KPP simulation."""
 pass
 class ConfigError(SimulationError):
 """Raised for invalid or missing configuration parameters."""
 pass
 24
class PhysicsError(SimulationError):
 """Raised for errors in physical calculations (e.g., non-physical 
result)."""
 pass
 class ControlError(SimulationError):
 """Raised for errors in the control logic."""
 pass
 # Additional exception types can be defined as needed for specific modules.
 Explanation: This defines a hierarchy of custom exceptions. They currently don’t add new functionality
 beyond naming, but having these distinct classes allows us to use 
except PhysicsError: or 
except 
SimulationError: in various places to handle specific issues. For example, if a calculation in the thermal
 module determines an impossible state (maybe negative pressure), it could 
raise 
PhysicsError("Unphysical state encountered in thermal model") . The SimulationEngine
 might catch 
SimulationError generally to handle all these uniformly. This module can be expanded
 with utility functions if needed (e.g., an 
assert_param(condition, message) that raises ConfigError if
 condition fails).
 File: 
config/config.py
 # config/config.py
 import os, json
 # Physical constants
 G = 9.81 # gravity (m/s^2)
 RHO_WATER = 1000.0 # water density (kg/m^3)
 # Default simulation parameters
 DEFAULT_PARAMS = {
 "time_step": 0.1,
 "total_time": 10.0,
 "floater_count": 8,
 "floater_volume": 1.0, # m^3
 "floater_mass": 50.0,
 "floater_area": 0.2,
 # kg
 # m^2 cross-section
 "drivetrain": { "gear_ratio": 1.0, "efficiency": 1.0 }, # simplistic 
defaults
 "generator": { "efficiency": 1.0 },
 "control": { "mode": "basic" },
 "enable_hypothesis": { "H1": False, "H2": False, "H3": False }
 }
 # Try loading external config file (JSON)
 config_path = os.path.join(os.path.dirname(__file__), "default_config.json")
 25
if os.path.exists(config_path):
 try:
 with open(config_path) as f:
 user_conf = json.load(f)
 # Merge user_conf into DEFAULT_PARAMS
 for key, val in user_conf.items():
 if isinstance(val, dict) and key in DEFAULT_PARAMS:
 # merge dict (nested config)
 DEFAULT_PARAMS[key].update(val)
 else:
 DEFAULT_PARAMS[key] = val
 print(f"[Config] Loaded overrides from {config_path}")
 except Exception as e:
 print(f"[Config] Warning: failed to load config file: {e}")
 # Note: If YAML support is needed instead, we could use pyyaml to load a .yaml 
file similarly.
 Explanation: This config module defines constants and a dict of default parameters. It then attempts to
 load 
default_config.json and merge it. The merging logic preserves nested structures (like if the JSON
 provides 
"drivetrain": {"gear_ratio": 2.0} , it will update just that subkey). If the file isn’t present
 or fails to load, it prints a warning but continues with defaults. This means out of the box, the simulator
 works with the built-in defaults, but an advanced user can create a JSON to tweak settings.
 We included a note about YAML; supporting it would just require reading a 
.yaml with PyYAML and doing
 a similar merge. For now, JSON is chosen for simplicity.
 Modules like 
SimulationEngine can use 
config.DEFAULT_PARAMS as the baseline. For example, in
 Flask when starting a simulation, one could do: 
from config import DEFAULT_PARAMS
 params = DEFAULT_PARAMS.copy()
 # update params with any user inputs...
 engine = SimulationEngine(params)
 This approach ensures all parts of code use consistent parameter values.
 File: 
routes/stream.py
 # routes/stream.py
 from flask import Blueprint, Response, request
 import json
 from simulation.engine import SimulationEngine
 26
import config
 stream_bp = Blueprint('stream', __name__)
 @stream_bp.route('/stream')
 def stream():
 """
    SSE endpoint that streams simulation data in real-time.
    Starts a new SimulationEngine and yields JSON data for each time step.
    """
 # Merge default params with any overrides from request args (if provided)
 sim_params = config.DEFAULT_PARAMS.copy()
 try:
 dt_override = request.args.get('dt')
 if dt_override:
 sim_params["time_step"] = float(dt_override)
 T_override = request.args.get('T')
 if T_override:
 sim_params["total_time"] = float(T_override)
 count = request.args.get('floater_count')
 if count:
 sim_params["floater_count"] = int(count)
 # (We could handle more params similarly)
 except ValueError as e:
 # If conversion fails, we ignore or log it. In real usage, send an error event 
or 400 response.
 print(f"Param parsing error: {e}")
 # Instantiate simulation engine for this run
 sim_engine = SimulationEngine(sim_params)
 def generate():
 # Run the simulation and stream each step's data
 for step_data in sim_engine.run():
 # step_data is already a dict from SimulationEngine.step()
 yield "data: " + json.dumps(step_data) + "\n\n"
 # Once done, indicate completion
 yield "data: [DONE]\n\n"
 return Response(generate(), mimetype='text/event-stream')
 Explanation: This blueprint defines the 
/stream endpoint. We demonstrate reading optional query
 parameters (
 dt , T, 
floater_count ) to override the simulation parameters. For example, the client
 could do 
fetch('/stream?dt=0.05&T=5') to run with a 0.05s timestep for 5 seconds total. We merge
 these into a fresh copy of 
DEFAULT_PARAMS to not alter the global defaults. Then we create a new
 SimulationEngine instance using these parameters. The 
generate() inner function calls
 27
sim_engine.run() and yields each piece of data as an SSE event. Finally, we return a Flask 
Response
 streaming this generator.
 This implementation ensures each client connection runs its own simulation instance from scratch (isolating
 runs). In a more advanced scenario, one might reuse a single simulation for all or manage multiple, but
 that’s beyond our current need.
 The output of this stream will be a sequence of JSON messages, each containing at least 
time , 
torque , 
power (as we defined in 
SimulationEngine.step() ), and then a "[DONE]" marker. The frontend
 should handle these accordingly.
 Note: We used 
json.dumps for safety (Flask can sometimes jsonify automatically, but SSE needs the
 specific format). Also, we catch 
ValueError in case of bad query inputs and simply print a warning. In a
 robust app, we might return a 
400 Bad Request for invalid params; here we just default to ignoring
 them.
 These code examples form the skeleton of the system. They are written to be minimal yet functional – for
 instance, if you run the Flask app, the 
/stream route will generate simulation data (albeit with simplistic
 physics calculations). They illustrate how the pieces come together: - 
f
 loaters. - 
floater.py defines physics for
 engine.py uses that, plus drivetrain, etc., to advance the simulation. - 
app.py and
 stream.py show how the simulation is invoked via web interface and streamed out. - 
errors.py and
 config.py support the robustness and configurability of the app.
 Each file and class has docstrings as per our style guide, and we have placeholders (
 TODO comments) for
 where future expansion will occur (e.g., in Floater.update for chain boundaries, or in engine for more
 precise torque sums).
 10. Notes for Future Expansion
 With the pre-stage refactoring in place, the KPP simulator is organized and ready for iterative
 enhancements. We have strategically left hooks, TODOs, and clear interfaces to facilitate the following
 future expansions:
 • 
Integration of Hypothesis Modules (H1, H2, H3): The architecture already separates concerns so
 that H1 (nanobubble effect) can be implemented by extending the Fluid system (e.g., adjusting water
 density or drag coefficient in 
Fluid or within 
Floater.update() as a factor)
 8
 . H2 (thermal
 assist) can be integrated via the Thermal module, perhaps by adjusting buoyant force calculations or
 adding a pressure/temperature state to floaters. H3 (pulse mode with flywheel and clutch) will
 involve expanding the Drivetrain and ControlSystem – we’ve anticipated this by designing Drivetrain
 to potentially include a flywheel and by leaving methods to engage/disengage clutch. In code, one
 might find a 
• 
# TODO: implement H1 nanobubble effect in floater or fluid calculations,
 indicating where to plug in that logic once the formulas are finalized.
 CFD Support for Fluid Dynamics: If higher fidelity fluid dynamics are required (perhaps using an
 external CFD solver or a library like PyChrono for fluid-solid interaction
 27
 ), our modular design will
 allow substituting or augmenting the simple drag model. For example, the 
Fluid module could be
 28
swapped out with a class that calls a CFD library to get forces on floaters. Since floaters currently call
 a simple 
compute_drag_force , we could instead have them query a 
FluidDynamics
 component. The interface would remain similar (providing drag force for a given state), so the rest of
 the simulation loop doesn’t change. We have intentionally kept the fluid calculations in one place to
 ease this replacement.
 • 
• 
• 
• 
• 
AI Design Agent and Reinforcement Learning Hooks: The ControlSystem is designed to
 accommodate sophisticated logic. We can integrate an RL agent by abstracting the control policy.
 For instance, we could implement the OpenAI Gym (Gymnasium) interface around our simulation
 (reset, step, etc.)
 28
 . The RL agent could operate by observing the simulation state (positions,
 velocities, etc.) and deciding actions (like when to open valves or clutch). Our architecture note to
 possibly use a 
ControlStrategy base class means we could have a 
RLControlSystem(ControlSystem) that overrides 
update_control to defer decisions to an
 external agent. We would also incorporate an interface for the agent to input actions. The
 simulation’s modular design means an agent could be slotted in without altering the physics
 modules.
 Multi-Floater Visualization and Animation: Currently, the front-end is basic, but future upgrades
 will likely involve real-time visualization of all floaters moving. We can integrate a WebGL or Three.js
 based 3D visualization or a Canvas 2D animation. Our SSE already streams the data needed
 (positions, etc.). We might add more data per floater to the stream (the Stage 2 SSE example shows
 sending a list of floaters’ positions/velocities
 29
 ). The UI (perhaps using a JavaScript library or a
 custom canvas drawing) can subscribe to these and animate floaters on screen. The architecture is
 ready for that: just extend what data is yielded and update the JS handler. We have placed the data
 logging in results such that adding per-floater info is straightforward.
 Power Electronics and Grid Interface: In later stages, if we simulate the electrical side (generator
 behavior under varying load, or connecting to a grid/inverter), we can introduce a new module, e.g., 
ElectricalSystem or expand the Generator class. Because Generator is separate, one could
 replace the simple efficiency model with a more detailed one (including maybe a PI controller for
 generator torque, or even simulate a battery). The modular design means adding such a component
 doesn’t ripple through the code – we’d give the SimulationEngine a new object to update each loop
 (or incorporate it into generator.update). We also left a placeholder for generator “export” (in Stage
 2, a 
/download_csv for logged data was mentioned
 22
 , which we can implement by dumping 
results_log ).
 Scalability and Performance: As we add complexity (especially with many floaters or advanced
 physics), we might consider performance tuning. Our pre-stage code can easily be adapted to use
 NumPy arrays for bulk operations (for example, updating all floaters in a vectorized fashion). If
 needed, modules like PyCuda or parallel processing could be integrated. Because our code is
 structured by responsibility, one could identify bottlenecks (say the drag computation for each
 f
 loater) and optimize that in isolation.
 Testing and Verification: With the modular design, we should add unit tests as we implement new
 features to verify correctness (e.g., test that adding H1 increases efficiency as expected). The pre
stage guide sets this up by isolating logic (e.g., one can test 
Floater.update() in a vacuum by
 mocking zero drag or such). In future, a continuous integration could run these tests to catch
 regressions as new features (like RL control or new physics) are integrated.
 In the codebase, we've marked several 
TODO comments where these future integrations will occur: - In
 floater.py , a 
# TODO: handle hitting top/bottom boundaries suggests where the chain or
 control logic will intervene to change 
is_filled state (tie-in with Air Injection system). - In 
engine.py ,
 29
one could add 
# TODO: sum contributions of all floaters for accurate torque once a
 detailed model is ready, and 
# TODO: integrate thermal effects if needed. - In 
control.py , a
 # TODO: implement advanced control strategies or RL agent hook can be placed in
 update_control . - In 
drivetrain.py , a 
# TODO: include flywheel dynamics for H3 would
 remind developers to add inertia and clutch logic.
 4
 By planning these expansions now, we ensure the pre-stage architecture will smoothly accommodate Stage
 1 (real-time loop with SSE, which we have essentially achieved in scaffolding) and Stage 2 (interactive real
time control and visualization) upgrades, as well as more research-oriented features later. The modular,
 object-oriented foundation laid in this guide is built to evolve – each future module can be plugged in with
 minimal changes to existing code, fulfilling the goal of a maintainable and scalable KPP simulation platform
 .
 1
 2
 3
 5
 6
 7
 9
 11
 25
 f
 ile://file-3HVVUCDUgivcJmxNAkMx7U
 4
 12
 13
 26
 27
 28
 Flask-Based KPP Simulator Implementation Blueprint.pdf
 Kinetic Power Plant (KPP) R&D Simulator Algorithm Blueprint.pdf
 f
 ile://file-DEKb2MeVDubPyHbxBzQBuC
 8
 10
 18
 19
 20
 22
 24
 29
 Stage 2 Upgrade_ Real-Time Simulation Implementation Guide.pdf
 f
 ile://file-UVKDQgJCEP8LPwraen4Q7s
 14
 15
 PEP 8 – Style Guide for Python Code | peps.python.org
 https://peps.python.org/pep-0008/
 16
 17
 21
 23
 Stage 1 Implementation Guide_ Real-Time Simulation Loop Upgrade.pdf
 f
 ile://file-GpMuyKuXh2AZkbDqvhrgVu
 30