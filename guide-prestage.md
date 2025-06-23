Pre-Stage Implementation Guide: Restructuring
 the KPP Simulator to a Modular Architecture
 Introduction and Goals
 In this Pre-Stage upgrade, we will refactor the KPP Web Simulator from a monolithic prototype into a fully
 modular and scalable Python architecture. The goal is to preserve all existing functionality and logic 
including all user inputs, output calculations, and hypothesis toggles (H1, H2, H3) – while reorganizing the
 code into clear, maintainable modules. This separation of concerns will mirror the physical subsystems of
 the kinetic power plant, making the code easier to extend in future stages . Key objectives of this
 restructuring include: 
1
 • 
• 
• 
• 
• 
• 
1
 2
 Separation of Concerns: Isolate the simulation engine (physics and logic) from the web interface
 (UI), so that changes to one do not impact the other . 
Modular Design: Create distinct Python modules/classes for major subsystems – floaters & chain
 mechanics, water environment, drivetrain & generator, pneumatic air system, and control logic 
each in its own file. These modules will interact via well-defined interfaces, primarily through a
 central 
SimulationEngine (or 
Simulation ) class. 
Composition over Monolith: Use composition to link modules (e.g. the 
own instances of 
Floater , 
SimulationEngine will 
Drivetrain , etc.), rather than one giant script. This will allow
 enabling or disabling features (like H1/H2/H3) simply by toggling flags in the appropriate module
 (e.g. 
Environment for H1/H2, 
3
 4
 5
 Drivetrain for H3) . 
Maintain Outputs & Hypotheses: All current calculations (forces, torques, power output, efficiency,
 etc.) and user inputs (sliders, toggles for hypotheses) will continue to function as before – just
 reorganized. For example, the drag-reduction hypothesis H1 will still reduce effective water density
 or drag on the descending side
 3
 torque when enabled
 6
 , the thermal buoyancy boost H2 will still amplify buoyant force or
 5
 , and the clutch/flywheel smoothing H3 will still engage/disengage
 appropriately to smooth power output . 
Prepare for Future Expansion: Laying out a clean project structure now will make it easier to
 expand functionality in later stages (e.g. adding more complex physics, AI controllers, additional
 sensor models). Each hypothesis-related feature can be expanded in its own module without
 breaking others, thanks to this modular separation . 
Robustness and Debugging: Introduce standard practices for error handling, debug logging, and
 7
 testing. Each class/module will include internal logging (using Python’s 
logging library) to track
 important events (e.g. a floater reaching top or bottom, clutch engagement changes, air injection
 events) and any errors/exceptions. This will aid developers in debugging and ensure the simulator’s
 reliability. 
In summary, this document provides a step-by-step guide to reorganize the code into a package structure,
 move each piece of functionality into the right module, introduce classes for each subsystem, and update
 the web interface code accordingly. By the end of this Pre-Stage, the KPP simulator will have a clean
 architecture ready for full modular expansion in future stages, with all current features intact.
 1
1. Create the Modular Project Structure
 The first step is to define and create the new directory and module layout for the project. We will convert
 the current codebase (which may be in one or a few files) into a well-organized Python package. Below is
 the recommended directory tree of the refactored project, with each component’s purpose noted:
 kpp_simulator/                 # Root package for the KPP Simulator 
├── app.py               # Application entry point (initializes Flask/Dash app 
and server)
 ├── config.py            # Configuration constants and default parameters (e.g. 
gravity, floater count)
 ├── simulation/          # Simulation engine package – core physics logic
 │   ├── __init__.py      
│   ├── simulation.py    # SimulationEngine class (main loop, integration, 
orchestration)
 │   └── models/          # Subpackage for physical model classes (one per 
subsystem)
 │       ├── floater.py      # Floater class (floaters & chain mechanics 
calculations)
 │       ├── environment.py  # Environment class (water properties, H1 & H2 
effects)
 │       ├── drivetrain.py   # Drivetrain class (chain, sprocket, clutch/
 flywheel, H3 logic)
 │       ├── pneumatics.py   # PneumaticSystem class (air tank, compressor, 
inject/vent logic)
 │       ├── control.py      # Control class (control system logic for 
injections/clutch)
 │       └── sensors.py      # Sensors class (optional, simulated sensor 
readings; could be merged with control)
 ├── dashboard/           # Web dashboard/UI package (using Dash for interactive 
interface)
 │   ├── __init__.py  
│   ├── layout.py        # Defines the UI layout (controls, graphs, text 
displays)
 │   ├── callbacks.py     # Dash callback functions (link UI events to simulation 
actions)
 │   └── animation.py     # Renders simulation animation (Plotly figures for 
floaters/tank schematic)
 ├── assets/              # Static assets for the web UI (CSS stylesheets, 
images/icons, etc.)
 ├── data_logging.py      # DataLogger class for logging simulation data, CSV 
export, PDF report generation
 ├── utils.py             # Utility functions (unit conversions, common formulas, 
etc.)
 └── tests/               # Test suite (pytest modules for each component)
    ├── test_floater.py       # Unit tests for Floater physics calculations
 2
    ├── test_drivetrain.py    # Tests for drivetrain dynamics and clutch logic
    ├── test_pneumatics.py    # Tests for pneumatic system behavior
    └── ... (additional test files for control, integration, etc.)
 Actions:- Create Packages: Make directories 
simulation/ (with an empty 
models/ (with its own 
__init__.py ). Also create 
__init__.py ) and 
simulation/
 dashboard/ (for web UI code) and 
tests/ . If
 using a GitHub repository, add an appropriate project README and possibly a 
requirements.txt if not
 already present.- Move & Rename Files: If the current codebase has large files (e.g., a 
main.py , 
kpp_simulator.py or
 similar) or unclear naming, split them according to the above structure. For instance: - Move physics
 computation code into 
simulation/models/ submodules and the main loop into 
simulation.py .- Move any Flask or Dash app initialization and route definitions into 
simulation/
 app.py and 
dashboard/ modules.- Delete or significantly slim down any monolithic file by extracting its contents into the new modules. (For
 example, if app.py originally contained simulation logic inline, that logic will be removed and relocated to
 simulation/ classes, leaving app.py only to start the server and connect callbacks.)- Config Module: Create a 
config.py to hold configuration constants and defaults (such as 
GRAVITY = 
9.81 , default number of floaters, default fluid density, etc.). The various modules can import these instead
 of hard-coding numbers, ensuring consistency. This also provides a single point to adjust physical constants
 or simulation settings.- Naming Conventions: Ensure all filenames are lowercase with underscores (Pythonic style) and reflect
 their content. The directory names are also lowercase (e.g. 
simulation , 
dashboard ). The package
 name 
kpp_simulator is used here (per the example) to emphasize it’s a Python module, but you can
 adjust the root name as needed – just be consistent. 
This new structure will improve maintainability. Each folder/file now has a clear responsibility, and we
 separate the engine (in 
simulation/ ) from the interface (in 
dashboard/ ) as a fundamental design
 principle . 
1
 2
 2. Refactor the Simulation Engine Core (
 Create a SimulationEngine class (we’ll call it 
simulation.py )
 Simulation for brevity) in 
simulation/simulation.py
 that will serve as the orchestrator of the entire simulation. This class replaces any ad-hoc main loop or
 global update functions from the old code. Its responsibilities include: initializing all subsystems, advancing
 the simulation state in time steps, and interfacing with the UI. Key design points: 
• 
• 
Singleton or Central Instance: Typically, we will instantiate one global 
Simulation object (e.g., 
simulation = Simulation(...) ) at application start, which lives throughout the app’s runtime.
 The Dash/Flask callbacks will call methods on this object to advance the simulation or retrieve data.
 For simplicity, you might create this instance as a global within 
simulation.py or in 
after initialization. 
Composition of Subsystems: The 
app.py
 Simulation class will own instances of all subsystem classes
 (floaters, drivetrain, etc.) as attributes. For example, 
self.floaters could be a list of 
Floater
 objects, 
self.environment an 
Environment object, 
self.drivetrain a 
Drivetrain
 3
object, etc.
 • 
8
 9
 . This composition reflects the real system and allows each part to be updated or
 queried via the Simulation class. 
Initialization: In the constructor (or an 
initialize_simulation() function), set up the
 simulation state. This includes creating the subsystem objects and perhaps seeding initial values. For
 example, create N 
Floater instances with appropriate initial positions around the loop, initialize
 environment properties (water density, etc.), set drivetrain initial speeds to 0, set up the pneumatic
 tank pressure, and so on. All user-selectable parameters (N floaters, which hypotheses are enabled,
 etc.) should either be passed into the Simulation initializer or have setters that the UI callbacks can
 call to update them. 
• 
Main Loop (
 step method): Implement a method 
Simulation.step(dt) that advances the
 simulation by a small time increment 
dt (e.g., 0.05 s, corresponding to 20 Hz updates). This
 method will perform one integration step of the physics and update all subsystems. Pseudocode for 
step() might follow the design loop described in the original documentation :
 10
 11
 class Simulation:
 def __init__(self, params):
 # Initialize time
 self.current_time = 0.0
 self.running = False # e.g., flag to pause simulation loop
 # Instantiate subsystems
 self.environment = Environment(h1_enabled=params.h1,
 h2_enabled=params.h2, ...)
 self.drivetrain = Drivetrain(h3_enabled=params.h3, ...)
 self.pneumatics = PneumaticSystem(...)
 self.control = Control(...)
 # Create floaters and chain system
 self.floaters = [Floater(id=i, environment=self.environment, ...) for i
 in range(params.num_floaters)]
 # (Optionally, link floaters to a Chain or directly handle positions 
here)
 # Set initial positions and states for floaters (e.g., alternating air
filled/water-filled)
 # ...
 self.logger = DataLogger() # for recording simulation data each step
 motion
 def step(self, dt: float):
 """Advance the simulation by one time step of duration dt seconds."""
 # 1. Compute forces on each floater and sum net force on chain
 forces = []
 for floater in self.floaters:
 f_b = floater.get_buoyant_force() # buoyancy (if air-filled)
 f_w = floater.get_weight_force()
 # weight (depends on mass, 
water/air filled)
 f_d = floater.get_drag_force()
 # hydrodynamic drag opposing 
# Determine net force contribution from this floater (direction +1 
for ascending, -1 for descending)
 4
forces.append(floater.direction * f_b- f_w- f_d)
 net_force = sum(forces)
 # Convert net force to torque on the drive sprocket
 tau_chain = net_force * self.drivetrain.sprocket_radius
 # 2. Apply thermal boost H2 if enabled (augments buoyant torque)
 if self.environment.thermal_boost_enabled:
 tau_chain *= (1 + self.environment.boost_factor) # e.g., increase 
torque by a percentage
 12
 12
 14
 15
 13
 # 3. Update drivetrain dynamics with the computed torque (handles clutch logic 
internally)
 self.drivetrain.apply_torque(tau_chain, dt) # updates omega_chain, 
omega_gen, clutch state
 # 4. Advance floater positions based on chain movement
 self.update_positions(self.drivetrain.chain_angle_moved) # (Method to 
move floaters along the loop)
 # 5. Handle boundary events: check for floaters crossing top or bottom
 for floater in self.floaters:
 if floater.crossed_bottom():
 # reached bottom of loop
 self.pneumatics.injectAir(floater)
 # fill with air, update tank pressure
 if floater.crossed_top():
 16
 # reached top of loop
 self.pneumatics.ventAir(floater)
 16
 # release air, floater 
becomes heavy
 # 6. Update pneumatics (compressor recovery, pressure changes if any)
 self.pneumatics.update(dt)
 # 7. Run control logic (if any separate control decisions needed this 
tick)
 self.control.update(dt) # (In basic mode, control may be minimal)
 # 8. Log the state for this time step
 self.logger.record(self.current_time, self.get_state())
 # 9. Increment time
 self.current_time += dt
 Example explanation: In the above pseudocode, the 
17
 Simulation.step() method
 orchestrates the physics update for one tick. It calculates buoyant, weight, and drag forces for
 each floater and sums them to get net chain force, then computes the torque on the sprocket
 . If H2 (thermal boost) is enabled, it multiplies the torque by a boost factor . Next, it
 calls 
12
 Drivetrain.apply_torque , which updates the rotational speeds of the chain and
 generator and handles the clutch engagement/disengagement internally . Then
 update_positions() moves the floaters along the chain according to the chain rotation.
 14
 Floaters that reached the bottom or top trigger 
injectAir or 
16
 15
 ventAir events in the
 PneumaticSystem , which also updates their buoyancy state. The PneumaticSystem might
 adjust tank pressure or compressor workload in its 
update() method. Control logic (if any,
 beyond what’s in drivetrain) runs, and finally the current state is logged for output. This logic
 5
18
 19
 is derived from the integration loop described in the design document and ensures all
 subsystems are updated consistently each step. 
• 
• 
• 
State Accessors: Implement helper methods in 
Simulation such as 
get_state() to collect
 current simulation outputs (e.g., pack relevant state variables into a dict or object). This will be used
 by the UI to display values. For example, 
get_state() might return data like: time, current chain
 speed (converted to RPM), generator speed, current output power, current efficiency, tank pressure,
 etc., which the dashboard will consume to update graphs and readouts. 
Parameter Setters: Provide methods to adjust parameters on the fly. For instance, 
Simulation.set_num_floaters(n) could add or remove 
Floater objects in the system,
 reinitialize positions, and reset the simulation as needed. Similarly, 
Simulation.enable_H1(flag) might toggle the 
environment.nanobubble_enabled
 setting, and 
Simulation.enable_H3(flag) could toggle whether the clutch logic is active or if
 the drivetrain should treat the clutch as always engaged (to simulate turning H3 off). These methods
 will be called by UI callbacks when the user changes inputs. 
Pause/Resume: Use a flag like 
self.running to indicate if the simulation loop should advance.
 The Dash callback for the interval timer can check this flag to pause the simulation without
 destroying state. A “Start/Pause” button in the UI can set 
simulation.running = True/False
 accordingly. 
After this step, the SimulationEngine is the heart of the simulator, coordinating all parts. It ensures the
 physics integration loop runs in one place (rather than spread across the UI code or global scripts), which
 aligns with the architecture’s intent . Next, we create each subsystem as a class in the 
10
 package and connect them to this engine.
 models/
 3. Implement Physical Model Classes (in 
simulation/models/ )
 In this step, we will introduce classes for each physical subsystem or concept in the simulator. Each class will
 reside in its own module under 
simulation/models/ , making the codebase modular. The existing
 calculations and logic will be moved into appropriate methods of these classes. The major model classes to
 implement are: Floater, Environment, Drivetrain, PneumaticSystem, Control, and optionally Sensors.
 Below, we detail each class’s role, the logic to include, and where in the current code that logic likely comes
 from.
 3.1 Floater (Buoyancy & Chain Mechanics) – 
floater.py
 The 
Floater class represents an individual floater attached to the endless chain. In the current
 simulation, a lot of per-floater calculations (buoyant force, weight, drag, position along the loop) might be
 done in a loop. We will encapsulate those in this class. Key responsibilities and attributes:
 • 
Physical Properties: Each Floater has fixed properties like volume (displaced volume when filled
 with air), mass (of the floater structure itself, plus possibly added mass when filled with water), and
 cross-sectional area (for drag calculations). It also has dynamic state: whether it’s currently air-filled
 (buoyant) or water-filled (heavy), its current position along the chain/tank, and perhaps its current
 velocity relative to water. Floater’s attributes should include these properties so that methods can
 compute forces . For example: 
20
 21
 6
• 
volume_m3 : Volume of the floater (m³) – determines buoyant force when filled with air . 
22
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
• 
• 
• 
mass_empty_kg : Mass of the floater’s material (not including water inside). 
mass_fluid_kg : Mass of water inside when filled (so total mass when water-filled = mass_empty +
 mass_fluid). 
area_m2 : Cross-sectional area for drag calculations (projected area moving through water). 
is_air_filled : Boolean flag for floater state (air-filled=True means buoyant, water-filled=False
 means heavy). 
position : Current position along the loop (could be an angle 0–2π, or a linear position index
 along chain). 
direction : +1 for ascending side, -1 for descending side (this could be deduced from position, but
 storing it simplifies force aggregation). 
Force Calculations: Implement methods for each force: 
get_buoyant_force() : Calculate upward buoyant force. Use Archimedes’ principle: F_b =
 ρ_water * g * displaced_volume if the floater is air-filled
 22
 . (If partially submerged or not fully
 buoyant, adjust accordingly, but in this simple model we assume fully submerged on one side of the
 loop.) If the floater is water-filled, its buoyant force might effectively be zero net (or much smaller,
 perhaps just the displacement of the structure itself – but for simplicity, we can treat it as negligible
 or as the difference between floater volume and contained water volume). 
get_weight_force() : Return the downward gravitational force = mass_total * g . Here 
mass_total depends on state: use 
22
 mass_empty + 0 (air inside) when air-filled (only the
 f
 loater’s own weight), or 
mass_empty + mass_fluid when filled with water (so it’s heavier). This
 ensures when a floater has water, it contributes a greater downward force. 
get_drag_force() : Compute hydrodynamic drag opposing the floater’s motion through water. A
 simple model: F_drag = ½ * C_d * ρ_water * A * v_rel², where 
to water
 23
 v_rel is the floater’s velocity relative
 . In our one-dimensional chain model, we might approximate 
v_rel by the chain
 speed. Each floater could assume the chain’s instantaneous velocity (for ascending vs descending
 sides, directions differ). The drag coefficient 
C_d and other parameters might be constants (could
 be in config). If needed, this method can query the 
Environment for water density or viscosity. 
State Toggle Methods:
 fill_with_air() : Simulate injecting air into this floater at the bottom – switch 
is_air_filled=True . This should also update any mass properties (remove the mass of water,
 perhaps set an internal “fluid mass” to 0 to indicate it’s empty of water, if modeling that). Maybe also
 reset any water inside temperature if H2 involves that (likely not needed at this detail). 
fill_with_water() : Simulate venting air at top – set 
is_air_filled=False , meaning the
 f
 loater fills with water and becomes heavy. This adds 
mass_fluid to its mass (or however you
 represent the water inside). Possibly adjust other properties if needed (though volume and area
 remain same). 
Position Update: The floater’s position along the loop will be managed by the Simulation or a Chain
 model. We might keep a 
position attribute (say as an angle or a distance along chain). The 
Simulation.update_positions() method will update each floater’s 
position each time step
 based on how far the chain moved. Floater might have a method or property to determine if it has
 crossed a boundary (top or bottom). For example, if position passes the threshold for bottom (e.g.,
 an angle of 180° if we say bottom is at π radians), then 
crossed_bottom() returns True once.
 7
Similarly for top (e.g., 0 or 2π angle). We’ll implement these checks either in Floater or within
 Simulation’s loop with known positions of top/bottom. 
By encapsulating floater-related physics here, we remove those calculations from the main loop. For
 instance, any existing code that computed buoyancy or decided when to flip floater state will now be
 methods in 
Floater . The Simulation class simply calls these methods and uses their results. This matches
 the design: “Each floater can be in a buoyant or heavy state... module calculates forces on each floater
 (buoyant, weight, drag) and converts net force into chain tension... tracks floater positions and updates
 24
 25
 their state at injection/vent points” – all of which is now handled by 
and by 
Simulation.update_positions or 
Floater (for per-floater calc)
 PneumaticSystem for the state changes.
 3.2 Environment (Water & Hydrodynamics) – 
environment.py
 The 
Environment class will contain properties of the surrounding environment, mainly the water in the
 tank. In the current simulator, water properties (like density) might have been constants or global variables;
 with H1 (nanobubbles) and H2 (thermal effects), the environment can modulate these properties.
 Responsibilities:
 • 
• 
• 
• 
Fluid Properties: Store parameters like 
water_density (ρ, in kg/m³) and perhaps 
water_viscosity or a generic drag coefficient factor. Gravity 
g can also be stored here (though
 it could also be a constant in config). 
Hypothesis Flags: Include flags/parameters for the enhancements that affect the environment: 
nanobubble_enabled (H1 flag) – when True, simulate drag reduction or effective density
 reduction on the descending side. You might also include a magnitude for this effect, e.g. 
density_reduction_factor or a modified drag coefficient when H1 is on. For simplicity, H1
 could be modeled by saying: water density on descending side = ρ * (1 - void_fraction) where 
void_fraction is some percentage representing nanobubble concentration
 26
 . Alternatively,
 directly lower drag forces for descending floaters. 
thermal_boost_enabled (H2 flag) – when True, enable the thermal buoyancy boost. Possibly
 include a 
27
 boost_factor (like 0.1 for +10% buoyancy) which will be used to amplify buoyant force
 or chain torque
 . In a simple model, this factor can be applied as a multiplier to buoyant force or
 directly to net torque as we showed in 
• 
• 
Simulation.step() . (In a more advanced model,
 Environment could track temperature, etc., but not needed now). 
Methods:
 get_density(position_or_floater) : (Optional) Return the effective water density at a given
 location or for a given floater. This could implement H1 by returning a lower density for positions
 corresponding to the descending side of the loop
 28
 . E.g., if a floater is on the descending side and
 nanobubbles are enabled, return 
ρ * (1 - density_reduction) ; otherwise return normal 
If we don’t want positional logic here, an alternative is to handle H1 inside the Floater’s drag
 calculation by checking 
• 
ρ .
 environment.nanobubble_enabled and the floater’s direction. Either
 approach is fine – the key is the effect is isolated to environment/fluid properties. 
Possibly 
get_viscosity() or a simple attribute for viscosity if needed for drag formula. 
• 
(If modeling dynamic changes, could have an 
update(dt) if, say, nanobubble concentration
 changes over time or water temperature changes due to H2. For now, we assume steady state for
 simplicity.) 
8
For 
instance, 
By isolating water properties here, if we need to adjust how H1 or H2 are implemented, we do it in this
 class. 
turning 
H1 on/off from the UI will call something like
 sim.environment.nanobubble_enabled = True/False . Floater and drag calculations will use the
 updated density automatically. This matches the concept that H1’s effect is to “reduce drag and effective
 water density on the descending side when enabled” , which we can implement via this Environment
 class providing that modified density. Similarly, the H2 effect is a thermal expansion boost to buoyancy
 3
 27
 , which we incorporate via 
boost_factor affecting forces/torque. Keeping these in Environment
 makes it clear and easily tunable.
 3.3 Drivetrain & Generator (Mechanics & H3) – 
drivetrain.py
 The 
Drivetrain class encapsulates the rotational mechanics: the chain, sprocket, flywheel/generator,
 and the clutch mechanism that engages/disengages the generator (representing hypothesis H3). In the
 current code, calculations for angular velocity, torque, and the clutch logic might have been scattered; now
 they will reside in methods of this class. Key aspects:
 • 
• 
• 
• 
Attributes:
 Physical constants: 
sprocket_radius (m) – radius of the drive sprocket that the chain wraps
 around (used to convert force to torque: τ = F * R). 
Inertias: 
J_chain – equivalent rotational inertia of the chain & floaters around the sprocket axis; 
J_gen – inertia of the generator rotor + flywheel. These values determine how the system
 responds to torque (α = τ / J). 
State variables: 
omega_chain (rad/s) – angular speed of the chain; 
omega_gen (rad/s) – angular
 speed of the generator. Initially these might be 0. We can also track 
• 
• 
• 
theta_chain (angular
 position of chain) to know how much the chain moved each step (for updating floater positions). 
Clutch state: 
clutch_engaged (bool) – whether the clutch is currently engaged (coupling
 generator to chain). If H3 is disabled entirely, we could decide to always keep this engaged (or
 always disengaged and combine inertias differently). Possibly also track a one-way clutch behavior:
 when disengaged, the generator can freewheel without affecting chain. 
H3 flag: 
h3_enabled – if the user toggles hypothesis H3 off, we might simplify the logic to
 effectively always transfer power (or not use the special clutch logic). For instance, if
 h3_enabled=False , one could treat it as 
clutch_engaged=True at all times (meaning the
 generator is rigidly connected, which is like a baseline system without the intermittent clutch). We
 will incorporate this flag in the logic. 
Method 
apply_torque(tau_chain, dt) : This is the core update for drivetrain each tick. It takes
 the net chain torque computed from buoyancy (
 tau_chain ) and advances the rotational speeds
 over the time step 
dt . The method should handle two cases – clutch engaged vs disengaged
 30
 :
 def apply_torque(self, tau_chain, dt):
 if self.h3_enabled and self.clutch_engaged:
 # Clutch is engaged: chain and generator rotate together as one system
 J_total = self.J_chain + self.J_gen
 alpha = tau_chain / J_total
 29
 # angular acceleration (rad/
 9
s^2)
 30
 self.omega_chain += alpha * dt
 # update angular velocity of chain
 self.omega_gen = self.omega_chain
 32
 # generator matches chain 
31
 speed (locked together)
 else:
 # Clutch disengaged (or H3 not enabled): chain moves separately from 
generator
 alpha_chain = tau_chain / self.J_chain
 own inertia
 self.omega_chain += alpha_chain * dt
 # chain acceleration on its 
# update chain speed
 # Generator side freewheels – it might slow down due to friction or 
remain nearly constant
 self.omega_gen *= (1- self.friction_factor * dt) # simple linear 
damping for generator spin-down
 # Update chain rotation angle for position updates (how much chain moved 
this step)
 self.theta_chain += self.omega_chain * dt
 # Decide clutch engagement for next step (if H3 is enabled and using logic)
 if self.h3_enabled:
 if self.omega_chain > self.omega_gen and not self.clutch_engaged:
 self.clutch_engaged = True # engage if chain tries to drive 
generator faster (one-way clutch engages)
 elif self.omega_chain < self.omega_gen * 0.99 and self.clutch_engaged:
 self.clutch_engaged = False # disengage if generator is spinning 
faster to avoid back-driving
 33
 36
 37
 34
 In this pseudocode, when the clutch is engaged (and H3 logic active), the chain+generator act as a
 combined inertia, and both angular velocities increase together under the net torque . When
 disengaged, the chain accelerates alone, and the generator’s speed decays slowly (simulating friction or
 electrical load) . After updating speeds, we adjust the clutch state: if the chain overtakes the
 generator speed, we engage (so the generator can be driven), but if the chain would slow down below
 generator speed, we disengage to let the generator spin freely and not drag the chain . These
 conditions implement the one-way clutch behavior (freewheel) described in H3: the clutch engages when
 buoyant force is high and disengages when forces drop so the flywheel can coast . The thresholds (like 0.99
 of generator speed) can be tuned. If 
35
 38
 5
 34
 h3_enabled is False, the code path could simply always treat it as
 engaged (or skip the complex logic altogether). 
• 
• 
Other Methods:
 get_power_output() : Compute the current generator power. A simple approach: power = τ_gen
 * ω_gen. If we assume a constant resistive torque (load) when generator is connected, we could
 incorporate efficiency. But as an initial implementation, since τ_chain and ω_chain are known (when
 clutch engaged, τ_chain is effectively τ_gen), power (W) = τ_chain * ω_chain. This can be converted to
 kW for UI display. We could also integrate generator’s electrical behavior here (like if a constant load
 torque is subtracted when engaged, meaning not all chain torque accelerates the system – some
 goes to electrical output). For now, calculating output as mechanical power delivered is fine; net
 power will later be adjusted for compressor consumption. 
10
Possibly 
• 
• 
get_rpm() to return chain or generator speed in RPM (for convenience in UI). 
We may not need an explicit 
update() method separate from 
apply_torque since all dynamics
 happen in 
apply_torque each step. 
It 
This class, once implemented, collects all the drivetrain-specific logic (which may have been in the main loop
 originally). 
cleanly 
encapsulates 
H3 
behavior. 
The 
simulation 
will 
drivetrain.apply_torque(tau, dt) each tick and then use 
call
 drivetrain.theta_chain or similar
 to update floater positions. All clutch decisions are internal here, so the control system might not even need
 to handle it explicitly (unless we wanted to override it with a different strategy). We follow the blueprint’s
 guidance on ensuring this logic is robust (limit extreme speeds, etc.) . As a result, the H3 hypothesis is
 fully handled by this module: the presence of the clutch and flywheel smoothing effect is captured in how
 the speeds and torques are computed . If H3 is turned off, we essentially bypass this intermittent
 engagement logic.
 39
 5
 3.4 Pneumatic System (Air Injection/Venting) – 
The 
pneumatics.py
 PneumaticSystem class represents the compressed air system responsible for injecting air into
 f
 loaters at the bottom and venting at the top. It also accounts for the compressor that repressurizes the air
 tank. In current code, these events might have been handled procedurally (e.g., when a floater hits bottom,
 do X). Now we will formalize them in this class. Key aspects:
 • 
• 
• 
• 
• 
• 
• 
• 
• 
Attributes:
 tank_pressure (e.g., in bar or Pa) – current pressure of the air tank. Could start at a nominal
 value (e.g., 5 bar). This may drop when air is injected. 
tank_volume or 
air_available – how much air is in the tank (maybe in m³ or in terms of
 number of injections possible at current pressure). We might not simulate detailed thermodynamics,
 but enough to know if we are low on air. 
compressor_power (kW) – power draw of the compressor when it’s running. If known from the
 original model (e.g., say 5 kW), include it. 
compressor_on (bool) – whether the compressor is actively running. Perhaps it runs whenever
 pressure < target. 
h2_enabled might not need a separate flag here, because H2’s effect (thermal boost) we handled
 via Environment. But if H2 was conceptualized as part of air injection (heated air injection), we could
 also incorporate that by slightly increasing the buoyancy of injected air. For now, assume
 environment handles buoyancy boost. 
We can also keep a constant for target pressure or a simple threshold (like maintain tank at 5 bar). 
Methods:
 16
 injectAir(floater) : This method is called when a floater reaches the bottom and needs to be
 f
 illed with air
 . It should:
 ◦ 
◦ 
Flip the floater’s state to air-filled by calling 
Reduce the 
floater.fill_with_air() . 
tank_pressure or available air store. For example, subtract the floater’s
 volume from available air (if we treat it as a closed system where that air left the tank and
 went into the floater). A simple approach: if using ideal gas and constant temperature,
 11
◦ 
◦ 
• 
removing volume ΔV from the tank will drop pressure proportionally (P1V1 = P2V2). We can
 approximate a pressure drop or simply mark that air was used. 
Start the compressor (set 
compressor_on = True ) if not already, indicating the
 compressor will work to restore pressure. 
Log or accumulate the energy used: The energy to inject that air (at pressure) can be noted.
 For instance, work = P * ΔV (pressure times volume). Or we know compressor will expend
 energy over time to refill it. In either case, we might account for compressor energy in net
 efficiency calculations. The blueprint indicates we should subtract compressor power from
 net output when computing efficiency . We will ensure to incorporate that in the logging/
 output stage (e.g., DataLogger can calculate net power = generator_power 
compressor_power when compressor is on). 
ventAir(floater) : Called when a floater reaches the top to release air
 40
 ◦ 
◦ 
Call 
16
 . This should:
 floater.fill_with_water() to make it heavy. 
Optionally, if we consider the air goes out to atmosphere (not back into tank), we might not
 change tank pressure here (assuming open vent). If the system were closed-loop (vent to a
 reservoir), it could be more complex, but likely we assume atmospheric vent. 
◦ 
• 
It might turn off the compressor if no floaters are air-filled (depending on logic, but probably
 the compressor stays on until pressure is back up). 
update(dt) : This is called each time step to simulate the compressor and other continuous
 dynamics in the pneumatic system
 ◦ 
If 
41
 42
 . In this method:
 compressor_on is True and 
tank_pressure is below the desired level, increase 
tank_pressure gradually based on compressor capacity. E.g., if compressor can deliver X
 volume per second at pressure, approximate how much pressure rises in dt. Or simply say
 after a certain time or ticks, it recovers. Since we might not have detailed specs, a simple
 model is: if an injection occurred, assume the compressor will spend a fixed amount of time
 or energy to pump it back. You can implement a timer or just continuously approach target
 pressure. 
◦ 
◦ 
Once 
tank_pressure has returned to nominal, set 
Compute 
compressor_on = False . 
compressor_power consumption for this tick (if on, use the fixed kW). This can be
 ◦ 
logged. 
If we are not simulating pressure drop explicitly, an even simpler approach is: whenever a
 f
 loater is injected, just add a fixed energy consumption or mark that compressor ran for, say,
 10 seconds at 5 kW (just conceptual), and incorporate that in efficiency. But for now, try to
 simulate gradually. 
This PneumaticSystem class ensures H2 (thermal aspects) and compressor energy are handled. Even
 though H2 is largely a buoyancy effect (we did that in Environment), one could also simulate slight cooling
 of water or track heat usage here. For now, we note that if H2 is enabled, the buoyant force was increased
 (done in Environment/Simulation), and perhaps we could reduce water temperature – but that’s a minor
 detail that can be skipped or handled in Environment if needed . The main addition here is accounting
 for compressor energy draw. The original purpose is to calculate net energy output including the
 compressor’s usage (H2 and H1 are passive enhancements, but H3 and the compressor actively affect net
 power). We will ensure in data logging that net power = generator output - compressor input, as suggested:
 “subtracting compressor power from generator output to get net power” . 
43
 in 
the 
40
 By migrating injection/vent logic here, the simulation loop becomes cleaner: instead of directly toggling
 f
 loaters 
loop, 
we 
call 
pneumatics.injectAir(floater) 
and
 12
pneumatics.ventAir(floater) . This class encapsulates what happens in those events, including
 updating the floater’s state and the air supply state. It matches the design: “when a floater reaches bottom,
 an injectAir event fills it... removing volume from tank... when reaches top, ventAir releases air... pneumatic model
 tracks compressor power usage so energy consumed by compressor is accounted for in net energy” . 
44
 3.5 Control System – 
control.py
 The 
45
 Control class will coordinate any active control logic beyond the basic physical responses. In the
 simplest implementation, our simulator might not need much here because a lot of the control is implicit
 (floaters inject when at bottom, etc., which we’ve automated). However, we create this class to allow future
 enhancements (and possibly to house any logic not naturally in physics classes). Roles:
 • 
• 
• 
• 
• 
• 
50
 Monitoring & Decisions: The control system can observe the overall simulation state (positions,
 speeds, pressures, etc.) and decide on actions like engaging the clutch or injecting air. In our current
 design, those decisions are largely handled internally (e.g., clutch logic is inside Drivetrain, injection
 happens automatically at bottom). So the initial Control class might be minimal. It could simply hold
 references to the other components (simulation, drivetrain, pneumatics, etc.) and possibly contain
 dummy methods that could be expanded. 
Example uses: If we wanted to enforce some constraints or advanced logic:
 E.g., Interlock injections: If two floaters reach the bottom in quick succession, maybe only inject
 one per cycle if compressor can’t handle simultaneous injections. Control could decide to delay the
 second injection by one cycle. 
Safety conditions: If 
pneumatics.tank_pressure is too low, control might temporarily disable
 further injections until pressure recovers
 46
 47
 . Or if the generator speed is getting too high,
 control could apply a brake or increase load (not in our current model, but possible extension). 
H3 override: Instead of purely mechanical clutch logic, you might have a control strategy that forces
 clutch disengagement under certain conditions beyond the one-way behavior. For now, we’ll rely on
 Drivetrain’s internal logic for H3, but the Control class could override or complement it if needed. 
update(dt) method: The Simulation will call 
control.update(dt) each step after physics. In
 basic form, this might do nothing or just monitor. If we implement something: for example, check a
 f
 lag that an injection was skipped due to pressure, etc. But since our current logic is straightforward,
 Control.update can be a placeholder that in the future gets more complex algorithms (like a PID
 controller or AI agent). 
48
 In summary, for Pre-Stage, the Control class ensures we have a hook for orchestrating the system if
 needed, but it won’t change existing behavior (unless we decide to move the clutch logic out of Drivetrain
 into Control – but that’s not necessary). The design documentation notes “since a lot of control is
 straightforward (always inject at bottom, etc.), Control might be simple now, but we include it for completeness
 and future extensibility” . We will document this class well and keep it ready for new strategies (like
 implementing a smarter injection timing or integrating an AI controller as a subclass of Control later
 ). For now, it primarily ensures the existing rule-based actions (which we mostly automated in the
 physics classes) are coordinated. We may simply use it to log any high-level events or check for anomalies
 (for example, we could have it print/warn if something goes out of expected range, as a rudimentary
 supervision). 
49
 13
3.6 (Optional) Sensors Simulation – 
sensors.py
 The 
Sensors class is an optional abstraction to simulate real sensor readings and noise. In the initial
 refactoring, this is not strictly needed because control logic can directly read from the simulation state.
 However, we include a stub for it to keep the design modular. If implemented, it might: 
• 
• 
• 
Gather readings from various parts of the simulation (chain speed, generator torque, tank pressure,
 void fraction) and present them in a structured way (as a dictionary or attributes). 
Add measurement noise or delay to emulate real sensor behavior (e.g., update readings at, say, 10
 Hz instead of 20 Hz, or add a small random error to RPM). 
Provide threshold alerts (like if void fraction > X%, or pressure drops too low, etc., set some flags). 
For now, we might not implement much here; the Control class or Simulation can directly fetch the needed
 values. But by defining the interface, we allow future upgrades to insert a sensor layer (for example, to test
 how a control algorithm performs with noisy inputs). The architecture discussion mentions this as a
 possibility: sensors could add noise or simulate delays, and encapsulating sensor behavior allows easily adding
 faults or calibration effects . We will leave this class as a placeholder or use it minimally (perhaps just a
 51
 52
 container for conversion functions like converting 
omega_chain to linear speed if needed).
 After implementing all these classes, the 
simulation/models/ package now contains a clear class for
 each subsystem. Each class’s methods correspond to pieces of logic that were previously in the monolithic
 script. We have effectively moved each calculation “to where it conceptually belongs”: buoyancy and
 drag into Floater, water properties into Environment, rotation and clutch logic into Drivetrain, air handling
 into Pneumatics, and orchestrated them via the Simulation engine. This satisfies the requirement of
 preserving functionality while restructuring code. No physics formula has been lost – they are just tucked
 into methods of the appropriate class, making the system easier to understand and modify.
 4. Integrate Modules via Composition
 With the classes defined, we now ensure that they work together properly through the 
engine. This involves establishing relationships and data flow between modules: 
• 
The Simulation class creates instances of each model and stores them. For example, in 
Simulation.__init__ , after 
Simulation
 self.environment = Environment(...) , we pass that 
environment into each 
Floater so that floaters can query environmental parameters (like
 water density) if needed. Similarly, 
Drivetrain might not need direct reference to Environment or
 Floaters, but it does need initial inertias which could depend on number of floaters (for a simplified
 model, we might treat 
J_chain as proportional to number of floaters or their mass distribution 
or we set it as a constant parameter). The Control class might be given references to Simulation or
 key subsystems if it’s going to monitor them. For instance, 
• 
self.control = Control(self) or 
Control(self.drivetrain, self.pneumatics, ...) so it can call methods on them if
 needed. 
Floater–Environment Interaction: If not passing environment into Floater, an alternative is to have
 Floater’s force methods accept 
rho as an argument. But it’s convenient to give each Floater a
 pointer to the Environment or at least to the 
Environment.water_density . This way, 
floater.get_buoyant_force() can do 
self.environment.water_density * self.volume * g . If H1 modifies density, ensure that 
14
get_buoyant_force or 
get_drag_force uses the appropriate value (e.g., if floater knows it’s
 descending and environment.nanobubble_enabled, maybe use reduced density in drag). The
 integration can be done by giving Floater either a full Environment object or just asking the
 Simulation for environment info when computing forces. Since our Simulation.step already loops
 through floaters, we could handle H1 there: e.g., in computing drag, do 
density = 
env.get_density(floater.position) and pass into 
• 
• 
• 
• 
• 
• 
• 
• 
• 
floater.get_drag_force(density) .
 Choose whichever is cleaner; just maintain clear interfaces. 
Drivetrain–Simulation: The Simulation uses 
Drivetrain.apply_torque and then reads back 
drivetrain.theta_chain (or some measure of rotation) to know how far the chain moved. We
 should define how 
update_positions works: possibly the drivetrain could directly provide a
 rotation angle. For example, if 
omega_chain is the angular speed of chain, the small rotation this
 step is 
omega_chain * dt . We can accumulate that in a 
chain_angle or directly update
 f
 loaters in the loop. Our pseudocode assumed 
self.drivetrain.chain_angle_moved (which
 could be 
omega_chain * dt or an integrated value). In code, you might simply do after 
apply_torque : 
angle_moved = self.drivetrain.omega_chain * dt and then call 
update_positions(angle_moved) . Implementation detail aside, the integration is
 straightforward. 
Pneumatics–Floater: When Simulation detects a floater at bottom, it calls 
pneumatics.injectAir(floater) . Inside that, 
floater.fill_with_air() is called. This is a
 cross-module interaction: ensure that Floater provides that method and PneumaticSystem knows
 when to call it. We already planned that. Similarly for venting. 
Control–Others: If Control is doing something proactive, it might call methods on Drivetrain or
 Pneumatics. For example, if we had a control that decides to not inject air even if floater reached
 bottom (maybe to save energy), it could override by not calling injectAir. But currently, Simulation
 directly triggers injection. We could eventually route those events through Control: e.g., Simulation
 could signal Control that “floater X at bottom, request injection” and Control either calls 
pneumatics.injectAir or decides to delay. That might be a future change. In the current
 structure, control is largely passive. We will at least connect it so that it can read sensor values if
 needed. 
Data Logging Integration: The 
Simulation.logger (DataLogger) should gather information
 from all modules. The 
logger.record(time, state) call we showed will likely collect state via 
Simulation.get_state() . Implement 
get_state() to pull data from subsystems, for
 example:
 From each floater: perhaps average or specific forces? (We might not need every floater’s data in the
 log by default, maybe just aggregate like net force or number of floaters filled vs empty.) But one
 could log each floater state if needed. 
From drivetrain: chain speed (convert to RPM), generator speed (RPM), clutch state (0/1), current
 torque, current power output (computed inside Drivetrain). 
From environment/pneumatics: current tank pressure, whether compressor is on, maybe cumulative
 energy used by compressor. 
From control/sensors: any notable flags or outputs (if any). 
Computed efficiency: if the simulator calculates efficiency (perhaps ratio of output energy to input
 energy), one can compute that from logged totals. At minimum, net power can be logged and
 efficiency at each instant if needed (though efficiency usually over a period). 
The composition effectively creates a miniature simulation framework: Simulation is the orchestrator that
 glues Floater, Environment, Drivetrain, Pneumatics, Control together. The data flows as follows each tick
 53
 15
54
 : Floaters compute forces -> Simulation sums to torque -> Drivetrain computes new speeds ->
 Simulation updates floaters’ positions -> Pneumatics and Control handle events -> Logger records data. This
 ensures a clear flow of information, with each module handling its part. The modules communicate through
 the Simulation’s coordination (and direct method calls as needed), not via global variables or tightly coupled
 code. This structure also makes unit testing easier, since each module can be tested in isolation (e.g., test
 Floater’s forces, test Drivetrain’s clutch logic, etc., with known inputs) .
 55
 22
 56
 At this stage, all existing logic should be accounted for in one of the classes or the Simulation loop.
 Double-check that every formula or behavior from the original code has a place: - Buoyancy/weight/drag 
now in Floater (and uses Environment parameters) .- H1 effect – represented via Environment’s density/drag modifications , used when computing forces on
 descending floaters.
 26
 6
 5- H2 effect – represented by Environment.boost_factor and applied in Simulation (or could be in
 Environment by altering buoyancy directly) .- H3 effect – represented via the clutch logic in Drivetrain .- Real-time update – the Simulation.step function covers the iterative update which the UI will call regularly.- Any redundant code from before (perhaps repeated calculations or overly complex procedural code) is
 eliminated by structuring it into these reusable methods. For example, if previously buoyant force was
 calculated in multiple places, now it’s one method used consistently. 
5. Error Handling, Debug Hooks, and Logging
 To improve reliability and debuggability, we will add error tracking and logging throughout the modules:
 • 
Logging Framework: Use Python’s built-in 
logging module. For each module (
 drivetrain.py , etc.), set up a logger at the top: 
floater.py , 
import logging; logger = 
logging.getLogger(__name__) . This way, logs are namespaced by module. In a global config
 (e.g., in 
app.py or a config file), set the logging level and format (for example, DEBUG level during
 development). This will not affect performance much if we keep it reasonable, and it will greatly help
 to trace what’s happening. 
• 
• 
• 
• 
• 
• 
Debug Logs: Insert 
logger.debug() calls at key points:
 In 
Floater.fill_with_air() / 
fill_with_water() : log state changes, e.g., 
logger.debug(f"Floater {self.id} filled with {'air' if is_air else 'water'} at 
position {self.position:.2f}") . 
In 
Drivetrain.apply_torque() : log when clutch engages or disengages, e.g., 
logger.debug("Clutch engaged, coupling generator and chain") or 
logger.debug("Clutch disengaged, generator freewheeling") , along with speeds/
 torques. 
In 
PneumaticSystem.injectAir() : log which floater was injected and the new tank pressure,
 e.g., 
logger.info(f"Injected air into Floater {floater.id}; tank pressure now 
{self.tank_pressure:.1f} bar") . Similarly, log vent events. 
In 
Simulation.step() : perhaps log each cycle’s summary if needed (time, net torque, chain
 speed, power output). This could be at debug level for detailed trace or at info level for higher-level
 progress. 
Error Handling: Anticipate possible issues and handle them:
 16
• 
• 
• 
• 
• 
• 
• 
• 
• 
If a formula could cause an error (division by zero, etc.), protect it. E.g., if computing something like 
tau_chain = F_net * R and perhaps R=0 (unlikely, but just in case), ensure R is set properly or
 check it. 
Use 
try/except blocks around file operations (like if DataLogger writes a file) and around
 sections that might throw exceptions, logging exceptions via 
logger.error(traceback) . For
 instance, if 
generate_pdf_report() fails due to some library issue, catch and log it rather than
 crashing the app. 
Validate inputs: If the user inputs an obviously invalid value (like negative number of floaters), the UI
 callbacks or Simulation.set_num_floaters should handle it (perhaps clamp the value or ignore).
 Logging a warning in such cases (e.g., 
logger.warning("Number of floaters must be 
positive. Ignoring input: %d", n) ). 
Debug Hooks: Provide ways to inspect the system state easily:
 The 
Simulation.get_state() we mentioned effectively acts as a debugging hook, since you can
 call it at any time (e.g., from a debugging console or a test) to see all current values. 
We could also implement a method 
Simulation.print_status() that prints or logs a concise
 summary of the simulation (e.g., “t=10.0s, chain RPM=12.3, gen RPM=15.0, clutch_engaged=False,
 tankP=4.8bar, netPower=2.1kW”). This is useful for quick debugging runs outside the UI. 
In development, one might include an assertion or two if certain invariants should hold. For
 example, an assertion that at least one floater is air-filled at all times on ascending side (just a
 theoretical invariant). But be cautious with asserts in a running simulation – they are more for
 testing rather than production. 
Testing & Verification: We have a 
tests/ directory set up, which should contain unit tests for
 these modules. Writing tests also acts as a form of error checking – if a test fails, it indicates a bug.
 For example, we’ll write tests to verify 
Floater.get_buoyant_force() returns expected values
 for known inputs, 
Drivetrain.apply_torque() correctly engages/disengages the clutch in
 simple scenarios, etc. These tests act as a safety net that the refactoring didn’t break logic. (While
 writing the implementation guide, actual test writing is optional, but it’s part of our plan and is
 facilitated by the modular design .) 
55
 Data Logging vs Debug Logging: We distinguish between the data log (the simulation results that
 will be saved for the user) and the debug log (the internal messages for developers). The
 DataLogger (in 
data_logging.py ) will continue to handle recording simulation outputs each
 57
 step (for plotting and CSV export) . The debug logging we add here (via 
logging calls) is not
 visible to the user in the UI, but will be visible in the console or log files where the server runs. This is
 especially helpful if something goes wrong during a long simulation – we can check the logs to see,
 for example, if the clutch was flapping in and out too quickly or if the compressor ran out of range. 
Implementing this now, during the refactoring, ensures that when we proceed to future stages (with more
 complex features), we already have instrumentation to trace new issues. It will be far easier to debug new
 control strategies or physics tweaks with these logs in place. 
17
6. Refactor the Web UI Layer (Flask/Dash 
app.py and Dashboard)
 With the simulation engine refactored, we need to adapt the Flask/Dash application code to make use of it.
 The original app (likely a Flask or Dash app defined in 
app.py ) will be simplified to route user interactions
 to the new 
Simulation object and return outputs to the frontend. Key tasks: 
• 
Initialize Simulation in 
app.py : In the new structure, 
app.py will mainly initialize the Dash app
 and the simulation. For example:
 from dash import Dash
 from dashboard.layout import app_layout
 import dashboard.callbacks # this will register the callbacks
 import simulation.simulation as sim
 app = Dash(__name__)
 app.layout = app_layout
 or just instantiate here:
 # simulation = sim.Simulation(params)
 # Initialize the simulation engine (create the Simulation instance)
 sim.initialize_simulation()
 # If simulation.py provides a function to do so, 
if __name__ == "__main__":
 app.run_server(debug=True)
 This minimal 
app.py ensures the web server is set up with the layout and callbacks. We may have
 initialize_simulation() inside 
simulation.py to set global parameters or instantiate the global
 Simulation. Alternatively, simply do 
simulation = Simulation() and perhaps mark it as a module
level object (so that callbacks can import it). The developer guide suggested using a singleton pattern where
 the Simulation is created at import time or via a function call in app.py . We should also consider any
 config or command-line args for initialization (for now, defaults are fine). 
• 
• 
Dashboard Layout (
 58
 layout.py ): This file will construct the UI using Dash HTML and Core
 Components. It should contain:
 Input controls: Sliders, dropdowns, checkboxes for all user-adjustable parameters. For example, a
 slider for number of floaters, toggles (Checklist or RadioItems) for H1, H2, H3 on/off, maybe numeric
 inputs for certain values (like fluid density, but likely we keep those constant in Pre-Stage). Also
 buttons like "Start", "Pause", "Reset". Each of these gets an 
• 
• 
id for callbacks. 
Output displays: Graphs for real-time plots (power vs time, speed vs time, etc.), a graph or shape for
 the animation of floaters in the tank, and text readouts for current values (e.g., current generator
 RPM, current efficiency, current net power, etc.). Use 
dcc.Graph for plots and maybe simple 
html.Div or 
html.Span for text outputs. For example, an 
display "Generator RPM: 123.4". 
Interval component: A 
html.Div(id='readout-rpm') to
 dcc.Interval(id='interval-component', interval=50, 
n_intervals=0) that triggers the simulation update every 50 ms (20 Hz)
 heartbeat of the simulation loop on the UI side. 
59
 60
 . This is the
 18
• 
Organize these in a layout (maybe a top section for controls, and a bottom section for plots). We
 could use a 
html.Div or Dash Bootstrap Components for some styling if desired. The layout
 should be defined as a global 
app_layout that we assign to 
app.layout in 
• 
Dashboard Callbacks (
 app.py . 
callbacks.py ): This file will define all the interactive callbacks using the
 @app.callback decorator. Key callbacks to implement: 
• 
Simulation Update (Interval) Callback: This is triggered by the 
interval-component every 
n
 milliseconds. It will call 
simulation.step(dt) and gather outputs for the UI. For example
 62
 :
 from dash.dependencies import Input, Output
 from simulation import simulation # import the Simulation instance or 
module
 from dashboard.animation import make_animation_figure
 from dashboard.layout import app # assuming app is created in app.py or 
imported here
 @app.callback(
 [Output('graph-power', 'figure'),
 Output('graph-animation', 'figure'),
 Output('readout-rpm', 'children'),
 Output('readout-efficiency', 'children')],
 [Input('interval-component', 'n_intervals')]
 )
 def update_simulation(n):
 if not simulation.running:
 # If paused, do nothing (keep last outputs)
 return dash.no_update
 simulation.step(dt=0.05) # advance the simulation by 0.05 s
 state = simulation.get_state() # fetch current state data
 # Generate updated figures and text from state
 fig_power = make_power_figure(state)
 61
 # e.g., Plotly line chart 
of power over time
 fig_anim = make_animation_figure(state)
 # Plotly figure showing 
floaters in tank
 rpm_text = f"Generator RPM: {state['generator_rpm']:.1f}"
 eff_text = f"Efficiency: {state['efficiency']*100:.1f}%"
 return fig_power, fig_anim, rpm_text, eff_text
 In this snippet, after stepping the simulation, we use helper functions to create the Plotly figures for
 power and animation (we will implement 
make_power_figure 
likely 
inside
 dashboard.callbacks or a separate plotting util). The key is that each tick, new output is
 computed and returned to update the respective UI components . We keep this function
 efficient – since our simulation calculations are lightweight (just a few floaters and simple equations,
 well under 20ms)
 63
 65
 , we can run it at 20 Hz without issues. 
64
 19
• 
Input Control Callbacks: For each user input that affects the simulation, create a callback:
 ◦ 
◦ 
◦ 
Number of Floaters Slider: When this value changes, call a function that updates the
 Simulation. For example : 
66
 67
 @app.callback(Output('dummy-output','children'),
 # no visible output needed
 [Input('floater-count-slider', 'value')])
 def update_floater_count(n):
 simulation.set_num_floaters(int(n))
 return "" # or dash.no_update
 Here, 
set_num_floaters is a method we’d implement to recreate or adjust the list of
 f
 loaters to the new number. We might need to reset positions or zero out the simulation time
 if the change is major. Often, changing number of floaters might require re-initializing the
 simulation to avoid inconsistency (or we ensure that adding/removing floaters mid-run is
 handled gracefully by code). In this Pre-Stage, we can keep it simple: possibly require the user
 to pause/reset before changing structural parameters like this, or automatically reset
 simulation time when changed. Document this behavior to the user.
 Hypothesis Toggles (H1, H2, H3): When these toggles (maybe a checklist with three
 booleans) change, update the corresponding flags in the Simulation. For example: 
@app.callback(Output('dummy-output2','children'),
 [Input('hypothesis-checklist', 'value')])
 # value is a list of enabled items, e.g., ['H1','H3']
 def update_hypotheses(enabled_list):
 simulation.environment.nanobubble_enabled = ('H1' in
 enabled_list)
 simulation.environment.thermal_boost_enabled = ('H2' in
 enabled_list)
 simulation.drivetrain.h3_enabled = ('H3' in enabled_list)
 return ""
 This callback simply flips the internal flags. The simulation loop will naturally start using the
 new settings on the next tick (e.g., if H3 is turned off, the drivetrain’s logic will now treat
 clutch as always engaged). 
Start/Pause Buttons: If using a button or toggle for run state, a callback should set 
simulation.running = True or 
False . Alternatively, instead of a callback, one can use
 a Dash 
ToggleButton whose state is directly read by the interval callback. But it’s
 straightforward to have: 
@app.callback(Output('interval-component','disabled'),
 [Input('start-button','n_clicks'), Input('pause
button','n_clicks')])
 def control_simulation(start_clicks, pause_clicks):
 20
# If start clicked, enable interval (disabled=False), if pause 
clicked, disable interval
 # Or simply set simulation.running True/False as well
 simulation.running = True if start_clicks > pause_clicks else
 False
 return not simulation.running
 Another approach: just have one “Start/Pause” toggle button that flips a boolean and have
 the interval callback check 
simulation.running (as we did). The implementation can vary;
 the main point is linking the UI control to that 
simulation.running flag. 
◦ 
Reset Button: If provided, on click it could call 
simulation.initialize_simulation()
 again (resetting all state to initial). You’d then also probably clear the data logger and reset
 graphs. Alternatively, maybe “reset” sets a flag that tells the interval callback to reinitialize.
 Implementing this requires caution to not break ongoing callbacks (Dash might call them
 concurrently). A safe method: require pausing before reset, or handle it inside a callback by
 stopping interval then reinit. Document to the user that pressing reset will clear data. 
Each of these callbacks may not produce a visible output (hence we sometimes use a dummy hidden
 Div with an ID to satisfy Dash’s requirement of an Output). The important part is the side-effect on
 the simulation object. We use 
dash.no_update or return something trivial as needed. We also
 ensure these callbacks are all imported (or defined in 
dashboard.callbacks which we import in
 app.py ) so they register with Dash . 
68
 • 
Download Data Callback: If the UI has a “Download CSV” or “Generate PDF Report” button, we can
 implement callbacks for those. Dash has a 
CSV: 
dcc.Download component for file downloads. E.g., for
 @app.callback(Output('download-data', 'data'),
 [Input('download-button', 'n_clicks')],
 prevent_initial_call=True)
 def download_data(n_clicks):
 # On click, get the logged DataFrame and convert to CSV
 csv_string = simulation.logger.get_csv_string()
 return dict(content=csv_string, filename="simulation_results.csv")
 And similarly for PDF, if implemented: call 
simulation.logger.generate_pdf_report() which
 returns a PDF file path or content, then serve it. For now, if PDF generation is not fully implemented,
 this could just be a stub that maybe returns a basic report. We include this because the upgrade
 specified providing real-time outputs and the ability to get logs. We ensure any such callback is
 thoroughly tested to handle large data (perhaps by downsampling or limiting the log as mentioned
 in data_logger) . 
57
 69
 After wiring up these callbacks, the UI should seamlessly interact with the new engine. The app layout
 and callbacks essentially remain similar in functionality to before, but now they call methods on our
 structured classes instead of manipulating global variables or doing physics calculations directly. This
 preserves all user-facing functionality: users can still start/pause, adjust sliders, toggle hypotheses, see
 21
the floaters move and graphs update, and download results. The difference is under the hood – the code is
 cleaner and divided logically. 
One benefit of this refactoring is that the UI and simulation are loosely coupled: The Dash app does not
 need to know the details of physics; it only calls 
simulation.step() and reads outputs . This
 separation means we could even swap out the simulation engine (for example, replace it with a different
 model or run it in a background thread) without changing UI code, as long as the interface (
 2
 step , 
get_state , etc.) remains consistent. This is exactly the architecture principle mentioned: “the architecture
 separates simulation engine from web interface for clarity and maintainability” . 
1
 7. Coding Style, Conventions, and Copilot Integration
 To ensure the refactored code is clean and maintainable, we will enforce standard coding conventions
 across all modules:
 • 
• 
PEP8 Compliance: Use clear naming and style per PEP8. For example, use 
lower_case_with_underscores for function and variable names, 
CapitalizedCamelCase for
 class names (e.g., 
Floater , 
PneumaticSystem ), and constants in 
70
 UPPER_SNAKE_CASE (like 
GRAVITY ). Limit line length to ~79 or 100 characters for readability . Break up long expressions
 and add whitespace around operators as needed. 
Docstrings and Comments: Each module and class will start with a descriptive docstring explaining
 its purpose. Each public method (and even important internal methods) will have a docstring
 describing what it does, its parameters, and return value . We will use a consistent style, for
 71
 72
 example Google or NumPy style docstrings. For instance, in 
floater.py : 
class Floater:
 """Represents a single floater in the KPP chain.
    Attributes:
        volume_m3 (float): Displaced volume of the floater (m^3), 
determines buoyant force.
        mass_empty_kg (float): Mass of the empty floater (no water).
        mass_fluid_kg (float): Mass of water when floater is filled (so 
total mass when heavy).
        is_air_filled (bool): State of the floater, True if filled with air 
(light), False if filled with water (heavy).
        position (float): Current position along the chain (e.g., in 
radians or a normalized length).
        direction (int): +1 if floater is on ascending side, -1 if 
descending.
    """
 def get_buoyant_force(self)-> float:
 """Calculate the upward buoyant force on this floater.
        Uses Archimedes' principle: F_b = rho_water * g * displaced_volume.
        If the floater is air-filled, we consider the full volume. If 
22
water-filled, buoyancy is minimal (only the structure displaces water).
        Returns:
            float: Buoyant force in Newtons (positive upward).
        """
 # ... implementation ...
 73
 This level of documentation will help others (and future us) understand each part’s role . We
 will do similarly for other classes (drivetrain, etc.), explaining any formulas or logic in plain language.
 Particularly, any non-obvious physics or reasoning (like the clutch threshold or the use of
 boost_factor) should be commented or cited inside the code (e.g., 
72
 # F_drag = 0.5 * Cd * A * 
rho * v^2 as a comment for clarity
 75
 • 
74
 74
 ). Avoid trivial comments, focus on explaining intent and
 assumptions . 
File Naming and Organization: As established, each file name clearly indicates its content. Within
 each file, organize classes and functions logically (if a file has multiple classes, order them such that
 one doesn’t depend on a later one, or break into multiple files if needed). Keep related functions
 near their usage. For example, if we had a helper function just for Floater calculations, we might
 include it in 
floater.py or in 
• 
• 
• 
• 
utils.py depending on reuse. 
GitHub Copilot Workflow Integration: The modular design greatly aids using AI coding assistants
 like GitHub Copilot. To integrate Copilot effectively into our workflow:
 Small, Focused Functions: We’ve broken the code into small methods and classes, which is ideal for
 Copilot. When writing code with Copilot, we can write the docstring or function signature (e.g., 
def 
get_buoyant_force(...) -> float: with a docstring) and Copilot can suggest the
 implementation based on context and description. Because our classes are well-defined with
 docstrings, Copilot has the necessary context to produce relevant suggestions for the internals. 
Descriptive Docstrings/Comments: By writing clear docstrings (as above) and perhaps comments
 outlining the steps in a method, we provide Copilot with high-level guidance. For instance, we could
 write in a comment “# compute buoyant force based on whether air-filled or not” and Copilot will
 often complete the code accordingly. This essentially turns our design intent into code faster. 
Incremental Development: We can use Copilot to flesh out repetitive or straightforward parts of
 the code. For example, after writing one test (e.g., 
test_floater.py for buoyant force), we might
 let Copilot suggest similar patterns for 
test_drivetrain.py . Likewise, after implementing one
 method in Floater, Copilot might help with others using similar patterns (like weight and drag). The
 consistency of interface (all these classes being simple with known physics formulas) means Copilot’s
 suggestions are likely to be correct or close. 
• 
• 
Review Copilot Output: Always review suggestions from Copilot, especially for physics code 
ensure units and formulas are correct. Our thorough docstrings should make it easier to spot if
 Copilot introduces an error (e.g., mixing up force and pressure). 
Refactoring with Copilot: During this reorganization, Copilot can also help ensure we haven’t
 missed moving any piece of logic. For instance, if we type a comment “# TODO: handle H2 thermal
 cooling effect on water” in environment, Copilot might not magically know what to do, but it will
 remind us if there’s something known in context. We shouldn’t rely on it for design decisions, but it
 accelerates writing boilerplate or retrieving context from the documentation we’ve fed (which we
 have effectively done by incorporating the blueprint text and comments in code). 
23
• 
• 
Version Control and Collaboration: As we implement this in a GitHub repository, each module’s
 changes can be committed separately. This staged approach (e.g., commit after Floater class,
 commit after Drivetrain class) makes it easy to track progress and backtrack if needed. If multiple
 developers (or AI assistants) are working, the clear module boundaries reduce merge conflicts – one
 person can work on 
pneumatics.py while another on 
dashboard/ , etc., with minimal overlap. 
Style Checks and Linting: We can integrate tools like 
flake8 or 
black to auto-format and find
 any style issues or errors. Running tests frequently will ensure everything still works as we refactor. 
By adhering to these conventions, the codebase will be more readable and self-documented. Future
 contributors (or future stages of this project) will be able to quickly grasp each part’s function without
 reading a tangled single script. The combination of human-friendly documentation and logical structure
 also makes it easier for tools like Copilot to assist in generating new code in the same style or updating
 existing code.
 8. Example: Putting It All Together (Summary of Steps)
 To recap the step-by-step restructuring actions with an example workflow: 
1. 
2. 
3. 
4. 
5. 
6. 
7. 
8. 
9. 
10. 
11. 
Set up new structure: Create the directories 
simulation/models , 
dashboard , etc., and stub
 out empty classes and functions according to the design. For instance, create empty class definitions
 for 
Floater, Environment, Drivetrain, PneumaticSystem, Control with just docstrings.
 Define the basic structure of 
Simulation with a 
step method that calls placeholder subsystem
 methods. This establishes the scaffolding. 
Gradually migrate code: Take the original simulation code and cut-and-paste logic into the
 appropriate methods:
 Move buoyancy/drag formulas into 
Floater.get_buoyant_force and 
get_drag_force .
 Remove those calculations from the old loop, replacing them with calls to the new methods. 
Move clutch and speed update logic into 
Drivetrain.apply_torque . If the old code had an if/
 else for clutch, replicate that inside the method. Delete the old clutch logic from wherever it was. 
Move injection and venting code into 
PneumaticSystem.injectAir/ventAir . If the old code
 simply toggled a floater’s state and maybe printed something, now it’s encapsulated. 
Any hardcoded numbers (like a compressor power constant, or a drag coefficient) can be moved to 
config.py or kept as class attributes (e.g., 
self.friction_factor in Drivetrain for generator
 spin-down). 
Ensure cross-references: After moving, update the Simulation integration loop to call these new
 methods in the correct order (as shown in pseudocode). At first, test it in a headless mode (without
 UI) by calling Simulation.step in a loop and maybe printing some values, to verify it runs without
 error and outputs make sense. This is easier now with logging – you can enable debug logging and
 watch the messages trace the simulation. 
Update UI callbacks: Refactor 
app.py and any Flask routes or Dash callbacks:
 If originally the Flask app had an endpoint that, for example, returned JSON of current state, now it
 should get that from 
Simulation.get_state() . 
If Dash callbacks were calling some global function to update simulation, point them to 
simulation.step() and friends. 
Remove any old global state – ideally the Simulation instance is the single source of truth for the
 simulation state. If any global lists or dicts were used to store results or states, incorporate them into
 24
Simulation or the DataLogger. For instance, if there was a global list of timestamps and powers
 for plotting, that should now reside in DataLogger or be generated from the log. 
Test end-to-end: Run the app. Try toggling H1/H2/H3 and ensure the outputs respond (e.g.,
 enabling H1 should slightly increase efficiency or chain speed, enabling H3 should stabilize the
 power graph if visible, etc., consistent with before). Use the same input values as a known scenario
 from the old version and verify the results haven’t changed (within tolerance). This ensures we truly
 preserved functionality. If differences arise, they might indicate a bug in refactoring, so use logs and
 tests to find where the logic diverges. 
Clean up and document: Remove any leftover dead code. Update the README or developer guide
 with the new structure (similar to what we have here). Make sure all citations or references in
 comments are updated if needed (we might not keep citations in code, but ensure any formula
 references are correct). 
Prepare for Stage 1+: With Pre-Stage (restructuring) done, the project is ready to be extended. We
 have placeholders for advanced logic (e.g., one can now easily implement a more complex
 compressor model in PneumaticSystem, or a different control strategy by subclassing Control or
 replacing its update method). The modular design allows adding new modules (say an 
ElectricalSystem for the generator’s electrical load, or a Visualization module) without
 major changes elsewhere . This positions us well for the next stage of development, where
 we might, for example, integrate machine learning in the control or perform optimization studies by
 swapping components. 
By following this guide, developers can methodically transform the KPP simulator’s codebase into a clean
 architecture. Each step keeps the app runnable (preferably, do the refactoring in small increments and
 verify as you go). The end result is a modular, scalable, and maintainable simulator ready for further
 enhancements, with a clear separation between the physics engine and the web UI, thorough logging for
 debugging, and a style that aligns with professional Python standards.
 Simulator Implementation Guide.pdf
 file://file-3J9ZAfNhrCCYK5EXA5JZMS
 12. 
13. 
14. 
76 77
 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30
 31 32 33 34 35 36 37 38 39 40 41 42 43 44 45 46 47 48 49 50 51 52 53 54 55 56 57 58 59 60
 61 62 63 64 65 66 67 68 69 70 71 72 73 74 75 76 77
 25