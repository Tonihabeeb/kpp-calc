KPP Simulator Pre-Stage Upgrade 
Implementation Guide
 1. Objectives and Scope of the Pre-Stage Upgrade
 The Pre-Stage upgrade is a comprehensive refactoring of the Kinetic Power Plant (KPP) Simulator’s
 codebase to establish a scalable, maintainable architecture. This stage focuses on reorganizing and
 encapsulating all core simulation components into discrete Python modules and classes, without altering
 the underlying physics calculations or changing user-visible functionality. Key objectives include:
 • 
• 
• 
• 
• 
• 
Modularization of Core Components: Separating the simulator’s major subsystems – floaters, fluid
 environment, drivetrain & generator, pneumatic/air system, hypotheses H1–H3, sensors, and the
 simulation time-loop controller – into independent modules and classes. Each component will have a
 single responsibility and well-defined interface, following a consistent modeling structure.
 Preservation of Physics and Behavior: Migrating existing computational logic (buoyancy, drag,
 torque, power, etc.) into the new class structure without changing the physics formulas or
 operational behaviors. All calculations from the legacy code are retained, ensuring the simulation’s
 numeric outputs remain consistent.
 Enhanced Interoperability: Designing clear data interfaces and communication pathways between
 modules (using method calls, shared data classes, or service layers) so that components interact
 cleanly. Dependency injection will be used to supply components with the collaborators or
 configuration they need, avoiding global variables and tight coupling.
 Robust Logging and Debugging: Introducing a unified logging system and debugging hooks
 across the simulation. Every class and critical function will include error handling with traceable
 exceptions and detailed logs. This ensures that any runtime issues can be diagnosed with full
 context, and developers can enable debug output for step-by-step tracing of the simulation.
 Maintain Web UI Compatibility: The refactored backend will be integrated transparently with the
 existing Dash/Flask web interface. All current input forms, outputs, and user interactions will
 continue to function unchanged. The new modular backend will sit behind the same API endpoints
 and produce the same output data format, so the front-end sees no difference – it simply delegates
 to a structured engine instead of monolithic code.
 Future-Proof Design: Although this upgrade does not yet introduce new physics features, it
 establishes an architecture aligned with upcoming stages (e.g. real-time loop in Stage 1, advanced
 control in Stage 2). The new design will facilitate later integration of high-fidelity CFD models and AI
driven control or optimization modules. By enforcing clean separation of concerns now, we ensure
 the simulator is extensible for industrial-scale simulation and experimentation going forward.
 1
This guide presents a detailed implementation plan fulfilling the above goals. We outline the new module
 structure, how each piece of legacy code maps into it, the design of class interfaces and communication,
 logging/error-handling strategy, coding standards to follow, and integration steps with the existing
 interface. Throughout, we use professional software engineering practices (consistent naming,
 documentation, testing hooks) to create a maintainable codebase ready for future enhancements.
 2. Modular Architecture Design
 In the refactored KPP simulator, each major subsystem of the physical model is implemented as an
 independent Python module or class. This section describes the proposed architecture, including the
 directory organization and the role of each module. The design cleanly separates the physics engine from
 the web interface, which follows best practices for clarity and maintainability. All modules will reside under a
 top-level package (e.g. 
kpp_simulator ), with sub-packages as needed for logical grouping.
 2.1 Project Structure and Module Layout
 Below is the directory structure for the refactored simulator. It illustrates how code will be organized into
 modules and sub-packages, each corresponding to a core component or feature of the simulation:
 kpp_simulator/               # Top-level package for the KPP Simulator
 ├── app.py                  # Flask/Dash application (existing web interface 
entry point)
 ├── simulation/             # Package for simulation engine and models
 │   ├── __init__.py
 │   ├── controller.py       # SimulatorController class managing the time loop 
and overall simulation
 │   ├── floater.py          # Floater class and possibly FloaterGroup management
 │   ├── environment.py      # Environment class (fluid properties, gravity, 
etc.)
 │   ├── drivetrain.py       # Drivetrain & Generator class (mechanical power 
conversion)
 │   ├── pneumatic.py        # Pneumatic system class (air compressor, injection 
& venting)
 │   ├── sensors.py          # Sensor classes (simulated sensors and monitoring)
 │   └── hypotheses/         # Sub-package for hypothesis H1, H2, H3 enhancements
 │       ├── __init__.py
 │       ├── h1_nanobubbles.py   # Module or class for H1 Nanobubble effects
 │       ├── h2_isothermal.py    # Module or class for H2 Isothermal expansion 
effects
 │       └── h3_pulse_mode.py    # Module or class for H3 Pulse-mode drivetrain 
logic
 ├── utils/
 │   ├── __init__.py
 │   ├── logger.py           # Logger setup and Logger class for unified logging
 │   └── exceptions.py       # Custom exception classes for detailed error 
reporting
 2
├── static/                 # (if applicable) static files (e.g. images for 
plots)
 ├── templates/              # (if applicable) HTML templates for the web 
interface
 └── requirements.txt        # Python dependencies (Flask, Dash, NumPy, etc.)
 Figure: Proposed project structure – The core simulation logic resides in the 
simulation package,
 broken into distinct modules per subsystem. The Flask application (
 app.py ) remains at top-level to handle
 web requests and will import and use the simulation controller. This separation of concerns aligns with the
 recommended design for clarity and extensibility.
 Each module in this structure encapsulates a part of the simulation:
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
simulation/controller.py : Contains the Simulation Controller (e.g. 
SimulatorController class) which orchestrates the simulation loop (time-stepping) and
 coordinates interactions between all other components.
 simulation/floater.py : Defines the Floater class, representing an individual floater object (or
 possibly manages a collection of floaters). Handles floater-specific properties and physics (buoyant
 force, drag, motion).
 simulation/environment.py : Defines the Environment class for the fluid environment (water
 properties, ambient conditions). Provides parameters like water density, gravity, and possibly
 methods to compute environmental effects.
 simulation/drivetrain.py : Contains the Drivetrain (and Generator) class modeling the
 mechanical energy conversion – including chain dynamics, sprocket radius, generator load/torque
 calculations, flywheel/clutch (for H3) etc.
 simulation/pneumatic.py : Contains the PneumaticSystem class for the compressed air
 system – injection at the bottom, venting at top, compressor power usage, etc., as well as any
 calculations for air pressure/work.
 simulation/sensors.py : Contains definitions for Sensor classes (e.g. PositionSensor,
 PressureSensor, SpeedSensor) to simulate readings of various parts of the system. These can be
 used by the controller or logging to mimic real-world sensor data and trigger control logic.
 simulation/hypotheses/ : A sub-package grouping the implementation of each enhancement
 hypothesis:
 h1_nanobubbles.py – logic for H1: Nanobubbles (reduced fluid density/drag effects).
 h2_isothermal.py – logic for H2: Near-isothermal expansion (thermal assist for buoyancy /
 reduced compressor work).
 h3_pulse_mode.py – logic for H3: Pulse & Coast mode (intermittent drivetrain loading, flywheel
 energy storage). Each hypothesis can be implemented as a class or a set of functions that modify the
 base physics; they are kept separate for clarity and to enable toggling them on/off independently.
 utils/logger.py : Defines a Logger utility or class to configure and provide a unified logging
 interface across modules.
 utils/exceptions.py : Defines custom exception classes (e.g. 
SimulationError , 
PhysicsError , etc.) used to wrap lower-level errors with contextual information.
 All these modules share a consistent modeling structure: for example, each physical component class
 (Floater, Drivetrain, etc.) will expose methods for initialization, state updates per time-step, and any queries
 or commands relevant to that component. They will interact through clearly defined interfaces rather than
 3
implicit global variables, enabling independent development and testing of each part. In the following
 subsections, we describe each core module/class in detail, including how legacy code maps into it and
 example class definitions.
 2.2 Floater Module (
 floater.py )
 Role: The Floater class represents an individual floater (container) moving through the water. It
 encapsulates all properties and behaviors of a floater, including geometry, mass, buoyant and drag forces
 calculation, and motion updates. In a multi-floater system (e.g. 66 floaters on the chain), we will either
 instantiate multiple Floater objects or have the Floater class handle aggregate behavior. For simplicity and
 scalability, the design will treat each floater as an object, possibly managed by the SimulatorController or a
 list structure.
 Legacy Code Mapping: In the current code, computations related to floaters are likely done in functions
 such as 
1
 compute_force() (which presumably calculates net force on a floater, combining buoyancy,
 gravity, drag)
 . These calculations will be moved inside the Floater class. For example:
 • 
• 
The buoyant force formula (Archimedes’ principle) and drag force formula currently in the code will
 become methods or internal calculations in 
Floater.update() or 
Floater.compute_forces() . Each Floater will know its volume, mass, and velocity, and will call
 the Environment for water density or other fluid properties to compute these forces.
 The state variables like position and velocity, previously stored in a 
now be attributes of the Floater instance (
 state structure or global, will
 self.position , 
• 
self.velocity ). This ensures each
 f
 loater tracks its own state over time, and makes variable tracking explicit and encapsulated.
 If the legacy code treated all floaters collectively (e.g. a single net force for the system), we will adapt
 it to per-floater calculations. The net effect on the drivetrain can then be computed by summing
 contributions from all floaters (or by symmetry, multiplying one floater’s effect by the number in
 certain simplified models).
 Responsibilities & Interactions: The Floater class will typically include: - Attributes for static properties:
 volume, cross-sectional area, mass (empty and when filled with water), etc. - Attributes for dynamic state:
 current position (e.g. angle or vertical coordinate along the loop), velocity, acceleration, whether it’s filled
 with air or water, etc. - A method like 
update(dt, environment) that updates the floater’s state by
 computing forces and integrating motion over a time-step 
dt . This method will: 1. Query the
 Environment for needed parameters (e.g. water density, gravity). 2. Compute buoyant force = ρ_water *
 displaced_volume * g, where displaced_volume might equal floater volume if fully submerged and filled
 with air. Gravity (weight) force = mass * g. Drag force = 0.5 * C_d * ρ_water * A * v^2 (opposing motion).
 These formulas remain unchanged from legacy code. 3. Sum forces to get net force (taking direction into
 account – upward buoyancy vs downward weight/drag). 4. Update velocity and position using the net force
 (e.g. simple Euler integration: 
v_new = v_old + (F_net/m) * dt ; 
dt ). - Methods to interact with other systems: e.g. 
pos_new = pos_old + v_new * 
attach_air() or 
vent() could be called by the
 Pneumatic system to change the floater’s state (switching its buoyancy when air is injected or released). The
 Floater might expose methods like 
fill_with_air() and 
fill_with_water() that adjust its mass
 (between “light” and “heavy” states). - If needed, sensor hooks: e.g. the Floater can contain a method or
 property to indicate if it has reached the top or bottom (this could be used by sensors or control logic).
 4
We emphasize dependency injection in this design: the Floater should not directly import global
 simulation parameters. Instead, it will be provided with the 
Environment (or specific values) each time it
 needs them. For instance, 
Floater.update(dt, env) takes an Environment object as parameter, or the
 Floater stores a reference to an Environment set at initialization. This way, if we later replace the
 Environment (e.g. with a more complex fluid model), the Floater code doesn’t change – it just uses whatever
 environment is given.
 Below is an example class template for the Floater module, illustrating structure, attributes, and an update
 routine with proper documentation and logging:
 # simulation/floater.py
 from utils.logger import Logger
 class Floater:
 """
    Represents a single floater in the KPP simulation.
    Attributes:
        volume (float): Displacement volume of the floater (m^3).
        mass_empty (float): Mass of the floater when empty (kg).
        area (float): Cross-sectional area for drag calculations (m^2).
        position (float): Current position of the floater along the loop (m or 
rad).
        velocity (float): Current upward velocity of the floater (m/s).
        filled_with_air (bool): Whether the floater is currently filled with air 
(True) or water (False).
    """
 def __init__(self, volume: float, mass_empty: float, area: float,
 initial_position: float = 0.0):
 self.volume = volume
 self.mass_empty = mass_empty
 self.area = area
 self.position = initial_position
 self.velocity = 0.0
 self.filled_with_air = False
 self.logger = Logger.get_logger(self.__class__.__name__)
 # Effective mass when filled_with_air will be just the floater 
structure; when filled_with_water, add water mass.
 @property
 def mass(self)-> float:
 """Current mass of the floater (kg), including water if not filled with 
air."""
 if self.filled_with_air:
 return self.mass_empty # only the floater structure
 5
else:
 # add mass of water filling the volume
 water_mass = self.volume * self.environment.water_density # 
environment will be set via injection
 return self.mass_empty + water_mass
 def update(self, dt: float, environment):
 """
        Update floater's kinematic state by one time step.
        Parameters:
            dt (float): Time step interval in seconds.
            environment (Environment): The simulation environment providing 
fluid properties (density, gravity).
        """
 try:
 # Calculate forces
 rho = environment.get_water_density()
 # water density (kg/m^3), may include H1 effect if environment is configured
 g = environment.gravity # gravitational acceleration (m/s^2)
 buoyant_force = rho * self.volume * g # Archimedes' principle 
(upward force if filled with air)
 weight_force = self.mass * g # downward force
 # Drag force (opposes motion): direction depends on velocity sign
 drag_coefficient = environment.get_drag_coefficient() # could be 
base or modified by H1
 drag_force = 0.5 * drag_coefficient * rho * self.area *
 (self.velocity ** 2)
 drag_force = drag_force * (-1 if self.velocity > 0 else 1)
 # oppose direction of motion
 # Net force on floater (taking upward as positive)
 net_force = 0.0
 if self.filled_with_air:
 # Floater is buoyant (ascending side): buoyancy up minus weight 
and drag down
 net_force = buoyant_force-weight_force + drag_force
 else:
 # Floater is heavy (descending side): weight down minus buoyancy (if any) minus 
drag (drag acts upward here)
 net_force =-weight_force + drag_force
 # buoyant_force is zero or negligible when filled with water
 # Update kinematics (Euler integration)
 acceleration = net_force / self.mass
 self.velocity += acceleration * dt
 self.position += self.velocity * dt
 self.logger.debug(f"Floater update: pos={self.position:.3f}, 
6
vel={self.velocity:.3f}, netF={net_force:.1f}")
 except Exception as e:
 # Log exception with context and re-raise as a simulation error
 self.logger.error(f"Error updating floater at position 
{self.position}: {e}")
 raise
 Example: 
Floater class skeleton. – The class stores floater parameters and state. The 
update method
 preserves the original physics calculations for buoyancy, drag, and weight, using values from an
 Environment object rather than global constants. Note how we calculate forces in the same way as the
 legacy code (buoyant force = ρ·V·g, drag as in the drag equation). A property 
mass computes the effective
 mass depending on whether the floater is filled with water. We include robust error handling: any exception
 in physics calculations is caught, logged with context (floater position, etc.), and re-raised (possibly as a
 custom exception from 
utils.exceptions ). Logging is done via a 
Logger utility for traceability. This
 approach ensures variable tracking (position, velocity, etc.) is encapsulated per floater and that the
 integration is numerically stable for small 
dt steps (Euler method as in legacy code, with potential to later
 upgrade to more stable integrators). It also makes the floater behavior modular so it can be independently
 tested (e.g. update a single floater in a controlled environment) and easily extended.
 2.3 Environment Module (
 environment.py )
 Role: The Environment class provides the ambient and fluid properties for the simulation. This typically
 includes constants like gravitational acceleration 
g , water density ρ, possibly water temperature or
 viscosity, etc. In the upgraded design, Environment acts as a central reference for any component that
 needs external parameters (floaters, pneumatic system, etc.). By encapsulating these properties, we can
 later substitute more complex models (for example, depth-dependent pressure or even a CFD-based
 environment) without changing the other classes – they all refer to the Environment interface.
 Legacy Code Mapping: In legacy code, values like 
g = 9.81 m/s² or 
rho_water = 1000 kg/m³ might
 have been hard-coded or defined in a constants section. These will now reside in the Environment class.
 Additionally: - If the code had separate modules or functions for fluid physics (e.g., a buoyancy module or
 drag calculation that needed density), those functions will either become methods of Floater (as shown) or
 be accessible through Environment (e.g., 
environment.get_water_density() returning the possibly
 adjusted density). - The nanobubble hypothesis (H1) effect, which reduces effective water density or drag
 on the descending side, can be integrated here. For instance, the Environment could hold a flag or
 parameter for nanobubble usage and adjust the density accordingly when queried. Similarly, drag
 coefficient adjustments for H1 could be managed here or in the Floater. (Another approach is to implement
 H1 in the 
hypotheses/h1_nanobubbles.py module and have Environment call that logic if active – we
 discuss hypotheses separately below.)
 Responsibilities & Interactions: The Environment class will likely include: - Attributes: 
base 
water_density , perhaps 
temperature , 
gravity (g) ,
 viscosity , etc., and toggles or parameters for active
 hypotheses (like 
nanobubble_fraction or 
thermal_expansion_coeff if modeling H1/H2). - Methods
 to retrieve properties: e.g. 
get_water_density(ascending: bool) could return normal 1000 kg/m³ for
 ascending side and a slightly reduced density for descending side if nanobubbles (H1) are active. Similarly,
 get_drag_coefficient() might return a base drag coefficient or a reduced one if H1 is on. This cleanly
 7
encapsulates how hypotheses modify environmental properties. - Possibly methods like
 pressure_at_depth(depth) if needed by pneumatic calculations (to compute hydrostatic pressure for
 air injection). - The Environment will be passed to other components (via parameters or stored references)
 so they can query it instead of using global constants.
 Here is a sample Environment class outline:
 # simulation/environment.py
 class Environment:
 """
    Environment model holding global fluid properties and environmental 
parameters.
    """
 def __init__(self, water_density: float = 1000.0, gravity: float = 9.81):
 """
        Initialize the environment.
        Parameters:
            water_density (float): Density of water (kg/m^3) under normal 
conditions.
            gravity (float): Gravitational acceleration (m/s^2).
        """
 self.base_density = water_density
 self.gravity = gravity
 # Hypothesis-related parameters:
 self.nanobubble_active = False # H1: if True, nanobubble drag 
reduction is applied
 self.density_reduction = 0.0
 # fraction or value to reduce density 
when H1 active
 self.drag_reduction = 0.0
 # fraction to reduce drag coefficient if H1 active
 self.thermal_active = False
 # H2: if True, isothermal/thermal assist is considered
 self.water_temperature = None # current water temperature if needed 
for H2
 self.ref_temperature = None
 # Additional properties (viscosity, etc.) can be added as needed
 def get_water_density(self, ascending: bool = True)-> float:
 """Return effective water density (kg/m^3). If H1 (nanobubbles) is 
active and floater is descending, density may be reduced."""
 rho = self.base_density
 if self.nanobubble_active and not ascending:
 # Apply a small density reduction for descending side (H1 effect)
 rho = rho * (1.0- self.density_reduction) # e.g., 5% reduction
 return rho
 8
def get_drag_coefficient(self)-> float:
 """Return effective drag coefficient for floaters. Applies H1 drag 
reduction if active."""
 # Base drag coefficient (from empirical data or default)
 Cd = 0.8
 if self.nanobubble_active:
 Cd *= (1.0- self.drag_reduction)
 # e.g., 20% reduction in drag due to microbubbles
 return Cd
 Example: 
Environment class snippet. – The Environment holds fundamental constants and applies global
 effects like H1’s modifications. In this example, if 
nanobubble_active is 
True , the water density
 returned for a descending floater might be 950 kg/m³ (a 5% reduction, achieved by
 density_reduction=0.05 ). Similarly, drag coefficient can be scaled down by, say, 20% when
 nanobubbles are on. The Floater’s update logic can call 
env.get_water_density(ascending=...) to
 get the correct density for buoyancy calculation depending on the floater’s state (ascending or descending
 side). By centralizing this in Environment, we ensure that all floaters experience consistent effects from
 hypotheses and we can tweak these formulas in one place. The Environment also makes it straightforward
 to incorporate H2 (thermal effects) globally if needed (for instance, adjusting density or directly adjusting
 buoyant force or pump work, though H2 will primarily affect the pneumatic system as described later).
 2.4 Drivetrain & Generator Module (
 drivetrain.py )
 Role: The Drivetrain class models the mechanical linkage between floaters and the power generator. In KPP,
 as floaters move, they exert torque on a chain or wheel that drives a generator. This module will handle: 
Summing torques contributed by floaters (or directly computing net torque if using a simplified aggregate
 model). - Modeling the rotational dynamics: e.g. if needed, angular velocity of the main shaft, gear ratios, a
 f
 lywheel for smoothing, and the generator load (resistance torque). - Computing the power output from
 the generator and possibly the instantaneous efficiency.
 Legacy Code Mapping: The legacy functions 
compute_torque(state, force, params) and
 1
 compute_power(state, torque, params) will be moved here: - 
compute_torque likely used
 the force from floaters and multiplied by a lever arm (wheel radius) to get torque. In the new structure, the
 Drivetrain class will have a method (e.g. 
calculate_torque(floaters) ) that iterates over all Floater
 objects, computes each floater’s current force contribution, and sums the torques. Alternatively, if the
 simulation simplified this by considering one floater’s net force, it would multiply that by number of floaters
 * radius. This logic is preserved but encapsulated in the Drivetrain. - 
compute_power likely took torque
 and perhaps rotational speed to compute electrical power. The Drivetrain will handle that as well, possibly in
 an 
update() method that after computing torque, applies generator efficiency or load to compute power
 output. - If the original code had a compressor torque or some coupling between compressor and
 drivetrain (since the compressor draws power), that might also be integrated here or in the pneumatic
 system. The mapping will clarify: e.g., if 
compute_power subtracted compressor power from gross
 mechanical power to yield net power, we will maintain that but clearly separate generator output vs
 compressor input.
 9
Responsibilities & Interactions: Key aspects of the Drivetrain module: - Attributes for system
 configuration: sprocket radius (lever arm for torque), gear ratio, generator efficiency, maybe the count of
 f
 loaters (if needed for torque calc). - State attributes: rotational speed (rad/s) of the main shaft, possibly
 angle, and a flywheel or inertia if simulating dynamics. In a simple steady-state model, rotational speed
 might be assumed constant (or derived from floater linear velocity and gear ratio). - Method to compute net
 torque on the drivetrain: for example, 
compute_net_torque(floater_forces) 
where
 floater_forces might be provided by summing buoyancy minus weight of ascending vs descending
 f
 loaters. Alternatively, the SimulatorController can compute net force difference and call Drivetrain with that
 value. The Drivetrain will multiply net force by wheel radius (and any mechanical advantage) to get torque. 
Compute power output: e.g. 
compute_power(torque) given the rotational speed. If chain speed or
 angular velocity is known (maybe determined by how fast floaters rise), power = torque * angular_speed.
 We ensure the formula matches what was done (the legacy 
compute_power likely did something similar
 with perhaps efficiency factored in). - Apply generator load: We may include a simple model where
 generator exerts a counter-torque proportional to desired load or to maintain a certain speed. This could be
 parameterized as a constant or left for future control logic. At Pre-Stage, it might be as simple as assuming
 the system runs at steady speed, so we just report the power. - For H3 (Pulse Mode): In normal operation
 (no H3), the Drivetrain might always engage the generator. H3 introduces a mode where the generator
 alternately disengages (allowing system to speed up) and then engages to extract energy in bursts. In our
 modular design, H3 logic will be handled via the hypothesis module (or via a setting in Drivetrain). Possibly,
 H3 could be implemented by adjusting an effective generator torque over time. We will ensure the
 Drivetrain class is designed so that such control can be added – e.g. a method to engage/disengage or a
 parameter for clutch state. At Pre-Stage, we may simply stub this out (e.g., an 
pulse_mode_active flag
 that is not yet fully utilized, but reserved for Stage 2 implementation).
 Here’s an outline of the Drivetrain class:
 # simulation/drivetrain.py
 class Drivetrain:
 """
    Models the chain drivetrain and generator of the KPP.
    Handles torque computation and power conversion.
    """
 def __init__(self, wheel_radius: float, gear_ratio: float = 1.0,
 generator_efficiency: float = 1.0):
 """
        Initialize the drivetrain.
        Parameters:
            wheel_radius (float): Radius of the sprocket or wheel that the 
floaters drive (meters).
            gear_ratio (float): Gear ratio between the chain and generator (if 
any).
            generator_efficiency (float): Efficiency factor of the generator 
(0-1).
        """
 10
self.wheel_radius = wheel_radius
 self.gear_ratio = gear_ratio
 self.generator_efficiency = generator_efficiency
 self.angular_speed = 0.0
 # rad/s of main shaft (could be derived from floater velocity)
 self.torque = 0.0 # latest computed torque on the shaft (N·m)
 self.power_output = 0.0 # latest power output of generator (W)
 self.pulse_mode_active = False
 self.flywheel_inertia = 0.0 # inertia of flywheel for H3, if used
 self.clutch_engaged = True # whether generator is engaged (for H3 
pulse mode)
 self.logger = Logger.get_logger(self.__class__.__name__)
 def compute_torque_from_forces(self, floater_forces: list)-> float:
 """
        Compute net torque on the drive wheel given forces from floaters.
        Each force is assumed tangential to the wheel (along chain).
        """
 # Sum forces on the ascending side minus descending side if provided 
separately.
 # Here floater_forces could be net upward force of each floater 
(positive for upward).
 net_force = sum(floater_forces) # assuming sign convention: positive = 
upward force
 # Torque = net_force * radius (simple model)
 self.torque = net_force * self.wheel_radius
 return self.torque
 def update_power(self, angular_speed: float):
 """
        Update generator power output based on current torque and angular speed.
        Parameters:
            angular_speed (float): Current angular velocity of the drivetrain 
(rad/s).
        """
 self.angular_speed = angular_speed
 # Power = torque * angular_speed (rotational power). Apply efficiency 
factor.
 raw_power = self.torque * self.angular_speed
 self.power_output = raw_power * self.generator_efficiency
 self.logger.debug(f"Drivetrain: torque={self.torque:.1f} N·m, 
omega={angular_speed:.2f} rad/s, power={self.power_output:.1f} W")
 return self.power_output
 def update_pulse_mode(self, dt: float):
 """
        (Optional for H3) Update flywheel and clutch if pulse mode is active.
 11
        This method adjusts torque distribution between flywheel and generator.
        """
 if not self.pulse_mode_active:
 return
 # Example: if clutch is disengaged, don't transfer torque to generator, 
instead accelerate flywheel.
 if not self.clutch_engaged:
 # Increase flywheel speed based on torque (store energy in flywheel)
 # (Detailed dynamics would be implemented here)
 pass
 else:
 # Clutch engaged: generator extracts power (already handled in 
compute_torque and update_power)
 pass
 Example: 
Drivetrain class snippet. – This class computes torque from forces and then power from torque.
 In the 
compute_torque_from_forces , we assume we receive a list of forces (for example, each floater’s
 net force contribution; alternatively it could accept separate sums for ascending vs descending). The net
 force times radius gives torque, matching the physics. The 
update_power method multiplies torque by
 angular speed to get power (the simulation will have to determine angular speed; e.g., if chain linear speed
 is known from floaters, angular_speed = linear_speed / radius). Efficiency less than 1 can be applied to
 account for losses. Logging captures the computed torque and power each update for debugging. We also
 stub out a 
update_pulse_mode method to illustrate where H3 logic would go – for Pre-Stage this could
 remain unimplemented or simply toggled off, but it shows the design anticipates later addition of the pulse
and-coast mode (flywheel dynamics, clutch control). The SimulatorController (described later) will call
 Drivetrain.compute_torque_from_forces each step (providing forces from the Floater instances)
 and then call 
update_power with the current angular speed to get the instantaneous power output.
 2.5 Pneumatic System Module (
 pneumatic.py )
 Role: The PneumaticSystem class handles the compressed air injection and venting process, as well as
 compressor power consumption. It effectively models the thermodynamic aspects: how much energy is
 required to pump air into a floater at depth, how the presence of compressed air changes buoyancy, etc. It
 may also include any valve timing logic (though full control logic might come later, at least we can simulate
 the basic cycle of injecting at bottom and venting at top).
 2
 Legacy Code Mapping: If the current code included computations related to the compressor or pump work
 (for example, calculating the energy needed to inject air into a floater, or the torque drawn by the
 compressor motor), those will be moved into this module. Possibly identified in the prompt by “compressor
 torque” or similar references : - There might be a function to compute the work needed to inject a given
 volume of air at a certain pressure (depth). The blueprint suggests formulas for isothermal vs adiabatic
 compression work. If the legacy code had such a calculation (maybe 
of 
compute_power 
subtraction), 
it 
compute_compressor_work or part
 will 
reside 
here 
e.g.
 PneumaticSystem.compute_injection_work(volume, depth) . - The Pneumatic module will
 interface with Floater objects: when a floater reaches the bottom, the Pneumatic system’s method (say
 as 
inject_air(floater) ) will set 
floater.filled_with_air = True and when at top,
 vent_air(floater) sets it False, etc. It might also track the timing or count of floaters filled. - Any
 12
mention of “hypotheses H2: isothermal expansion” is directly relevant here. H2 claims near-isothermal
 compression (meaning injecting air requires less energy because heat is absorbed from water). In code, this
 translates to using an isothermal formula for work rather than adiabatic. We will incorporate that via either
 a parameter or the hypothesis module: - If H2 is active, use $W = P_0 V \ln(P_{\text{depth}}/P_0)$ formula
 for injection work (isothermal). - If H2 is not active, use a higher work estimate (adiabatic) for the same
 process. - The Pneumatic system will thus preserve the physics: the energy cost to inject air will be
 computed and can be logged or subtracted from net power.
 Responsibilities & Interactions: The PneumaticSystem class will likely: - Contain parameters for the
 compressor, such as rated power, efficiency, and possibly current power usage. - Provide methods for the
 simulation loop to call when a floater reaches injection point or venting point. E.g.,
 inject_air(floater) which: - Calculates the work (energy) required using the current depth (which
 could be the environment’s depth parameter) and maybe updates a cumulative energy counter or
 instantaneous power draw. - Marks the floater as filled with air (which will immediately change its buoyancy
 in the next time steps). - Possibly simulate pressure dynamics in a simple way (e.g., assume constant
 pressure injection equal to hydrostatic pressure at bottom). - Provide data for logging: e.g., total
 compressor energy used, instantaneous compressor power draw (which could be used to adjust net
 output). - It will interact with Environment (for pressure via depth and water density) and Floater (to change
 f
 loater state). It might also inform Drivetrain or SimulatorController for net power calc (since net electrical
 output = generator output - compressor input ideally).
 Here is how we might sketch the PneumaticSystem class:
 # simulation/pneumatic.py
 import math
 class PneumaticSystem:
 """
    Simulates the pneumatic components: air compressor, injection and venting of 
floaters.
    """
 def __init__(self, compressor_power_limit: float = 5500.0):
 """
        Initialize the pneumatic system.
        Parameters:
            compressor_power_limit (float): Max compressor power (W) for 
reference (e.g. 5.5 kW).
        """
 self.compressor_power_limit = compressor_power_limit
 self.compressor_energy_used = 0.0 # cumulative energy (J) used for air 
injection
 self.use_isothermal = False
 # H2 hypothesis toggle
 self.logger = Logger.get_logger(self.__class__.__name__)
 13
def inject_air(self, floater, environment):
 """
        Inject air into the given floater (at bottom of loop). Computes energy 
required and updates floater state.
        """
 # Calculate depth (we might use environment.water_depth if floaters have a known 
path depth)
 depth = environment.water_depth if hasattr(environment, 'water_depth')
 else 0.0
 # Pressure at depth (Pa):
 P0 = 101325.0 # atmospheric pressure
 rho = environment.base_density
 P_depth = P0 + rho * environment.gravity * depth
 # Volume of air to inject = floater volume (assuming fully displace 
water)
 V = floater.volume
 # Work needed to inject air:
 if self.use_isothermal:
 # H2 active: isothermal compression work
 work = P0 * V * math.log(P_depth / P0)
 else:
 # Adiabatic compression work (gamma ~ 1.4 for diatomic air)
 gamma = 1.4
 work = (P_depth * V- P0 * V) / (gamma- 1)
 self.compressor_energy_used += work # accumulate energy consumption
 self.logger.info(f"Injected air into floater: work={work:.1f} J (total 
energy used={self.compressor_energy_used:.1f} J)")
 # Update floater state
 floater.filled_with_air = True
 def vent_air(self, floater):
 """
        Vent air from the given floater (at top of loop). Marks floater as 
filled with water.
        """
 floater.filled_with_air = False
 # No energy required to vent (passive release), but could log event
 self.logger.info("Vented air from floater at top.")
 Example: 
PneumaticSystem class snippet. – The 
inject_air method uses physics to calculate the work
 required to inject air at depth. If H2 is active (
 use_isothermal = True ), we apply the isothermal
 compression formula, otherwise an adiabatic approximation. This matches what the hypothesis H2 intends– reducing compressor work by thermal assistance. The computed work (in Joules) is added to a running
 total 
compressor_energy_used (for later energy balance or efficiency calculations). The method then
 sets the floater’s state to buoyant (air-filled). The 
vent_air method simply flips the floater back to water
f
 illed at the top; in a refined model it might also release compressed air back to atmosphere (which we
 14
assume doesn’t consume energy, though in reality you might capture some energy but that’s beyond
 scope). The PneumaticSystem doesn’t itself advance in time; it reacts to events (bottom reached, top
 reached). The SimulatorController will call 
inject_air or 
vent_air at appropriate times, likely
 determined by sensor triggers or position checks. We log the injection events for traceability – including the
 energy calculation which is critical for verifying the hypothesis claims (e.g., we can see how H2 reduces the
 work required). 
2.6 Sensor Module (
 sensors.py )
 Role: The Sensors module provides classes that emulate sensors and instrumentation in the KPP system.
 While sensors are not complex in terms of physics, separating them allows us to simulate control logic
 triggers and monitoring without entangling them in the core physics code. Sensors could include: - Position
 sensors (to detect when a floater reaches certain positions like bottom or top). - Pressure sensors (to detect
 if a floater is filled with air or water, or measure internal pressure). - Speed/rotation sensors (e.g. to measure
 generator RPM or chain speed). - Torque sensors, flow meters, etc., if needed for advanced control or
 monitoring.
 At Pre-Stage, these sensors might mainly be used for logging or simple event triggers (like calling
 inject_air when a floater reaches bottom). They set the stage for future control unit integration
 (Stage 2 or beyond, where a controller logic or an AI agent would use sensor inputs to make decisions).
 Legacy Code Mapping: The current code likely did not have a separate sensor abstraction – any “sensing”
 was probably implicit (like checking a condition in code). We will formalize that: - For example, where legacy
 code might do 
if position >= some_height: vent the floater , we will create a
 PositionSensor that monitors floater.position and triggers an action (or simply logs the event). - There
 may be no direct legacy functions for sensors, so this is more of an addition to improve structure. Thus, no
 heavy computations here, just refactoring conditional logic into classes.
 to 
the 
Responsibilities & Interactions: A possible approach is to create simple sensor classes that hold a
 reference 
variable 
they 
measure and a threshold or condition: - e.g.,
 PositionSensor(threshold= some_height, trigger="above") that can check a Floater’s position
 and return True if condition met. - Or a 
SensorManager in the SimulatorController that loops through
 defined sensors each time-step and handles their signals (like if bottom sensor triggers, call
 pneumatic.inject_air). - We can also integrate sensor readings into the output log/stream (to mimic real
 telemetry).
 For implementation: - Each sensor class could have a method 
read() or 
is_triggered() returning a
 boolean. - Alternatively, sensors might register callbacks in the controller. For now, a straightforward polling
 in the simulation loop is fine. - We should ensure sensors are modular (one class per sensor type or a
 generic sensor class that can be configured with a lambda condition).
 A very simple example, focusing on how it ties into simulation:
 # simulation/sensors.py
 class PositionSensor:
 15
"""Simulates a binary position sensor that triggers when a floater crosses a 
certain position."""
 def __init__(self, position_threshold: float, trigger_when="above"):
 """
        Parameters:
            position_threshold (float): The position (or level) at which the 
sensor triggers.
            trigger_when (str): Condition for triggering, e.g. "above" or 
"below" the threshold.
        """
 self.position_threshold = position_threshold
 self.trigger_when = trigger_when
 def check(self, floater)-> bool:
 """Check if the floater triggers this sensor."""
 if self.trigger_when == "above":
 return floater.position >= self.position_threshold
 else:
 return floater.position <= self.position_threshold
 class SpeedSensor:
 """Simulates a sensor that measures rotational speed of the generator (RPM 
or rad/s)."""
 def __init__(self, drivetrain):
 self.drivetrain = drivetrain
 def read(self)-> float:
 """Return the current angular speed (rad/s) of the drivetrain."""
 return self.drivetrain.angular_speed
 Example: Sensor classes. – The 
PositionSensor can be used to detect events like floater reached top or
 f
 loater 
reached 
bottom. 
For 
example, 
we might instantiate 
top_sensor 
= 
PositionSensor(position_threshold=environment.water_depth, trigger_when="above") to
 detect when a floater’s vertical position exceeds the water depth (meaning it’s at the top). In the simulation
 loop, we can check 
if top_sensor.check(floater): pneumatic.vent_air(floater) . Similarly a
 bottom sensor would trigger injection. The 
SpeedSensor (or other continuous sensors) can be used
 simply to log values (e.g. generator speed for plotting). While the Pre-Stage implementation doesn’t involve
 a sophisticated control system, having these classes in place organizes how such logic will be added later. It
 also aligns with industrial simulation practice where sensor data is separate from the actual state variables,
 enabling realistic integration with control algorithms or AI agents.
 2.7 Simulation Controller / Time Loop (
 controller.py )
 Role: The SimulatorController (or Engine) is the brain of the simulation loop. It creates instances of all the
 above components, manages the progression of time steps, and orchestrates interactions (calling updates
 on floaters, computing forces, coordinating pneumatic injections, updating drivetrain, logging data, etc.).
 16
This is essentially the new structured version of what the legacy 
engine.py likely did in a one-off manner– now extended to run iteratively over time.
 Legacy Code Mapping: The legacy 
engine.py (or equivalent) performed a one-shot calculation: reading
 inputs, computing all outputs once (perhaps at a certain operating point or single cycle) and returning
 results. According to the Stage 1 guide, the current engine is a “one-shot” that needs to be turned into a
 loop. In this Pre-Stage, we will refactor engine logic into the controller class but still preserve a similar
 interface to the outside. Concretely: - The new 
SimulatorController.simulate() method will
 incorporate what the Stage 1 guide outlines: a loop from t=0 to t=T with increments of dt, calling the same
 physics functions each step. We will move those function calls inside our class methods (as described for
 Floater, Drivetrain, etc.). - The existing top-level function (perhaps named 
run_calculation or similar in
 the web app) will now instantiate SimulatorController and call its simulate method. We may keep a wrapper
 in 
engine.py to preserve the original function signature for the web interface, but internally it delegates
 to 
SimulatorController . - The outputs that were collected (e.g. a dictionary of results or a list of
 outputs) will now be assembled from the controller’s data. In our design, the controller can accumulate
 results in a list or data structure each time step (time, power, torque, etc.) to be returned or streamed.
 Responsibilities & Interactions: The SimulatorController coordinates everything: - Initialization: It will
 take the simulation parameters (possibly we define a 
SimulationConfig or use the
 SimulationParams dataclass as suggested in the blueprint) and use them to create the Environment,
 Floater(s), Drivetrain, Pneumatic, etc. It will also set initial conditions (initial floater positions, etc.). For
 example, if number of floaters is N, it might create a list of Floater objects spaced evenly around the loop. 
Time loop (
 simulate method): It will loop over time steps: 1. For each Floater, call
 floater.update(dt, environment) to get new position/velocity and implicitly update internal forces
 (the Floater could store last computed net force if needed). 2. Determine if any sensor events occur (e.g., if a
 f
 loater reached bottom -> call 
pneumatic.inject_air , if reached top -> 
pneumatic.vent_air ).
 Alternatively, this can be done by checking floater positions directly if sensors are not explicitly used. 3.
 Compute net force/torque on drivetrain: collect forces from floaters (e.g., each buoyant force minus weight
 for 
ascending 
f
 loaters 
minus 
descending, 
etc.) 
call
 drivetrain.compute_torque_from_forces(force_list) . 4. Update generator power: if linear or
 angular speed is known, call 
and 
drivetrain.update_power(angular_speed) . In a simple model,
 angular_speed can be derived from floater velocity (e.g., chain linear speed v => angular ω = v / radius). If
 the loop is running at steady-state speed, we might keep ω constant based on inputs. In dynamic mode, ω
 could change if net torque is not zero (but simulating acceleration of the entire system might require
 differential equations – at Pre-Stage we might assume quasi-steady per step). 5. Log or record outputs for
 this time step: time, maybe average floater speed, current torque, power, efficiency, etc. This could be
 appended to a list of results. 6. Increase time by dt and repeat.
 • 
• 
• 
• 
Logging and error handling: The controller will wrap the loop in try/except to catch any error from
 components and log them. It can use the Logger to record high-level simulation progress or stats
 (e.g., at the end of simulation, log total energy out, total energy in).
 Interfaces: The controller will provide an interface for the web app. For example, a method 
simulate_until(time_final, dt) that returns the results (or perhaps yields results generator
style for streaming). We might implement both:
 A generator 
run() that yields after each step (to support real-time streaming later).
 A method that runs to completion and returns a data structure (for the current interface which likely
 expects a final result for rendering a static page).
 17
Given this design, here’s a conceptual code snippet for the SimulatorController:
 # simulation/controller.py
 class SimulatorController:
 """
    Controls the simulation loop and coordinates all components.
    """
 def __init__(self, params):
 """
        Initialize all components of the simulation based on input parameters.
        Parameters:
            params (dict or SimulationParams): Configuration for the simulation 
(floater count, dimensions, etc.).
        """
 # Unpack parameters (could use a dataclass for strong typing)
 num_floaters = params.get('num_floaters', 1)
 floater_volume = params.get('floater_volume', 1.0)
 floater_mass = params.get('floater_mass_empty', 50.0)
 floater_area = params.get('floater_area', 1.0)
 wheel_radius = params.get('wheel_radius', 1.5)
 water_depth = params.get('water_depth', 10.0)
 # Create environment
 self.environment = Environment(water_density=1000.0, gravity=9.81)
 self.environment.nanobubble_active = params.get('use_nanobubbles',
 False)
 self.environment.density_reduction = 0.05 # 5% density reduction if H1 
(could come from params)
 self.environment.drag_reduction = 0.2
 # 20% drag reduction if H1
 # Create components
 self.floaters = []
 for i in range(num_floaters):
 # Initialize each floater (for simplicity, all at rest, possibly 
evenly spaced vertically)
 initial_pos = (i * water_depth/num_floaters) % water_depth
 floater = Floater(volume=floater_volume, mass_empty=floater_mass,
 area=floater_area, initial_position=initial_pos)
 self.floaters.append(floater)
 self.drivetrain = Drivetrain(wheel_radius=wheel_radius, gear_ratio=1.0,
 generator_efficiency=1.0)
 self.pneumatic =
 PneumaticSystem(compressor_power_limit=params.get('compressor_power_limit',
 5500.0))
 self.pneumatic.use_isothermal = params.get('use_isothermal', False)
 # Sensor setup (top and bottom sensors for injection/venting triggers)
 18
self.top_sensor = PositionSensor(position_threshold=water_depth,
 trigger_when="above")
 self.bottom_sensor = PositionSensor(position_threshold=0.0,
 trigger_when="below")
 # Time tracking
 self.current_time = 0.0
 self.results_log = [] # list to store results each step if needed
 def step(self, dt: float):
 """
        Advance the simulation by one time step (dt seconds).
        """
 # Update all floaters
 for floater in self.floaters:
 floater.update(dt, self.environment)
 # Check sensors for this floater
 if self.bottom_sensor.check(floater) and not
 floater.filled_with_air:
 # Floater reaching bottom triggers air injection
 self.pneumatic.inject_air(floater, self.environment)
 if self.top_sensor.check(floater) and floater.filled_with_air:
 # Floater reaching top triggers venting
 self.pneumatic.vent_air(floater)
 # Compute net forces from floaters for drivetrain
 forces = []
 for floater in self.floaters:
 # Calculate net upward force on this floater for torque calculation 
(buoyant - weight for ascending, negative for descending)
 # We can approximate net force from internal state: buoyant_force - 
weight (drag negligible for net torque if symmetric, but we'll include drag 
too).
 rho =
 self.environment.get_water_density(ascending=(floater.filled_with_air))
 buoyant = rho * floater.volume * self.environment.gravity
 weight = floater.mass * self.environment.gravity
 net_upward = buoyant-weight # drag omitted for torque sum or 
could include sign of velocity influence if needed
 forces.append(net_upward)
 self.drivetrain.compute_torque_from_forces(forces)
 # Update power (derive angular speed from floater velocity if 
applicable)
 avg_velocity = sum(f.velocity for f in self.floaters) /
 len(self.floaters)
 angular_speed = avg_velocity / self.drivetrain.wheel_radius # 
simplistic link between linear and angular speed
 self.drivetrain.update_power(angular_speed)
 # Log results for this step
 self.current_time += dt
 19
self.results_log.append({
 'time': self.current_time,
 'torque': self.drivetrain.torque,
 'power': self.drivetrain.power_output,
 'efficiency': self.compute_efficiency()
 })
 def simulate(self, total_time: float, dt: float):
 """Run the simulation loop from t=0 to t=total_time (seconds)."""
 self.current_time = 0.0
 self.results_log.clear()
 try:
 while self.current_time < total_time:
 self.step(dt)
 # Simulation complete, results_log is filled
 return self.results_log
 except Exception as e:
 # Log and propagate the error
 Logger.get_logger("SimulatorController").error(f"Simulation aborted 
at t={self.current_time:.2f}s: {e}")
 raise
 def compute_efficiency(self)-> float:
 """
        Compute instantaneous efficiency if applicable (output power vs input 
power).
        For now, output is drivetrain.power_output, input is compressor power 
usage rate.
        """
 if self.drivetrain.power_output is None:
 return 0.0
 # Compute compressor input power (current, approximate as energy used in this 
step divided by dt)
 # This is a simplistic approach; a more detailed model might have 
compressor power at each step.
 compressor_power = 0.0
 # (We could track energy used difference or assume steady compressor 
usage if continuous)
 if self.pneumatic.compressor_energy_used and len(self.results_log) > 0:
 # energy used in this step ~ diff in compressor_energy_used / dt
 last_energy = self.results_log[-1].get('comp_energy', 0.0)
 compressor_power = (self.pneumatic.compressor_energy_used
last_energy) / dt
 # Avoid division by zero
 if (self.drivetrain.power_output + compressor_power) == 0:
 return 0.0
 20
return self.drivetrain.power_output / (self.drivetrain.power_output +
 compressor_power)
 Example: SimulatorController loop excerpt. – This snippet shows how the controller ties everything together. In
 __init__ , we use the 
params (which could be input from UI) to configure components. We instantiate
 multiple floaters and maintain them in a list. We also set up sensors for top and bottom detection using
 threshold values (water depth, etc.). In 
step() , each floater is updated for the time step, and we
 immediately check if that floater triggered a bottom or top event to call the pneumatic system methods. We
 then gather forces from floaters to compute torque on the drivetrain and update power. We log time,
 torque, power, and a computed efficiency (here efficiency is just a placeholder demonstration: output /
 (output + input), where input would be compressor power; this uses 
difference as a proxy for power usage).
 compressor_energy_used
 The control loop uses a simple integration and check approach, which reflects the instructions from Stage 1
 (repeatedly call the same physics computations inside a loop). In fact, our 
step essentially consolidates
 what was pseudocode in Stage 1 (compute forces, update state, record outputs) but does so using our
 object-oriented structure rather than standalone functions. The 
simulate() method runs the loop until
 total_time , aggregating results. Notice the robust try/except around the loop: if any component raises
 an exception (which they log), the controller catches it, logs a high-level error with timestamp, and re-raises
 it to be handled by the UI or higher-level logic, ensuring traceability of errors.
 Variable tracking and numerical stability: By updating each floater incrementally with small 
dt , we
 maintain numerical stability similar to any explicit integration scheme – any potential stability issues can be
 mitigated by reducing 
dt or using better integrators later (which is easier to swap in this architecture).
 The design tracks important variables (position, velocity, torque, etc.) at each step explicitly in stateful
 objects, which prevents errors like losing track of a global state. All data needed for output or further
 analysis is either stored in these objects or logged in 
results_log .
 3. Inter-Class Communication and Dependency Injection
 A cornerstone of this refactoring is clear interfaces between modules. Rather than sharing data through
 global variables or tightly coupling classes, each component interacts with others through well-defined
 methods and data structures. This decoupling is aided by dependency injection – providing objects or
 values to a class, instead of the class fetching them itself – which improves testability and modularity.
 Key communication patterns in our design:
 • 
Environment Access: Instead of hard-coding constants, classes like Floater and Pneumatic access
 f
 luid properties via an Environment instance. We inject the 
update(dt, 
methods (
 Environment object into Floater
 environment) ) or into the Floater at construction
 (floater.environment
 = 
env ) so that floaters can call methods like
 env.get_water_density() . This means if we replace Environment with a more complex one (say
 a CFD-based subclass), the Floater code remains unchanged as long as the interface
 (get_water_density, etc.) is the same.
 21
• 
• 
• 
• 
• 
• 
• 
Floater-Drivetrain Interaction: Floaters do not directly talk to the Drivetrain. Instead, the
 SimulatorController mediates – it collects forces from floaters and passes them to Drivetrain. This is
 a simple form of service layer: the controller acts as an intermediary, so Floater doesn’t need to know
 anything about torque or the existence of a generator. This separation follows the single
responsibility principle and makes it easy to modify the drivetrain calculation without touching
 Floater logic.
 Floater-Pneumatic Interaction: We avoid having Floaters themselves decide when to inject or vent
 (that would blur responsibilities). Instead, either sensors or the controller detect conditions and call
 PneumaticSystem methods with the Floater as an argument. This way, Floater just exposes an
 attribute 
filled_with_air and the Pneumatic system toggles it. The Pneumatic system, in turn,
 doesn’t need to know details of the Floater beyond that interface (we could define an interface
 FloaterInterface with just 
volume and a property to set filled_with_air). We use dependency
 injection by passing the Floater object to PneumaticSystem’s methods – this is effectively injecting
 the dependency (the specific floater to act on) at call time.
 Use of Sensor Outputs: The controller uses Sensor objects to decouple the event detection from the
 action. For instance, 
bottom_sensor.check(floater) returns a simple boolean which the
 controller uses to decide on injection. In a more complex system, sensors could register callbacks
 with a central event dispatcher. For now, a polling approach is sufficient and clear. The key is that
 sensors don’t directly call pneumatic or modify floaters – they only provide information, which the
 controller (or a control logic module) uses. This pattern will allow easy integration of automated
 control or AI: we could have a Control module listening to sensor triggers and issuing commands to
 pneumatic or drivetrain, without rewriting the physics modules.
 Hypothesis Modules Usage: The hypothesis modules (H1, H2, H3) are integrated via dependency
 injection and parameter flags:
 H1 (Nanobubbles) – we inject its effects by setting properties in Environment (density and drag
 reduction factors) or by replacing certain methods. Alternatively, we could have a strategy class for
 drag that Environment uses. But the simplest is what we showed: Environment knows if
 nanobubbles are active and applies the effect globally.
 H2 (Isothermal) – we inject this by toggling 
pneumatic.use_isothermal . The formula difference
 is handled internally in PneumaticSystem based on that flag. This is a form of dependency injection
 at initialization: the controller reads the user’s H2 choice and sets the pneumatic system accordingly.
 H3 (Pulse Mode) – we prepare for this by having Drivetrain accept a mode flag or method
 (update_pulse_mode). In the future, a Hypothesis H3 module could override how 
Drivetrain.update_power works or manage the clutch timing. At Pre-Stage, the controller can
 simply not engage any special behavior unless H3 is flagged. But thanks to the structure, adding
 that behavior means either:
 ◦ 
◦ 
Extending Drivetrain with an if 
pulse_mode_active (as stubbed) – minimal intrusion.
 Or using a separate 
PulseModeController that works with Drivetrain (which can be
 injected if H3 is on).
 In summary, loose coupling is achieved by: - Passing objects like 
Environment , 
floater , 
drivetrain into methods rather than having those methods fetch global singletons. - Centralizing
 coordination in SimulatorController, so components don’t implicitly depend on each other’s internals. 
22
Using simple data containers (like a 
params dict or dataclass) to bundle configuration that gets passed in,
 rather than scattering configuration reads in each module.
 This approach echoes best practices and ensures each module can be developed and tested in isolation. For
 example, one could write a unit test for 
PneumaticSystem.inject_air by creating a dummy Floater
 with known volume and an Environment, without needing the whole simulation running. Likewise, Floater’s
 update can be tested given a static environment. The well-defined interfaces (e.g., Floater requires an
 environment object providing density and gravity; Drivetrain requires forces list; Pneumatic requires floater
 and environment, etc.) serve as contracts between modules.
 4. Error Handling, Logging, and Debugging Strategy
 To ensure the refactored simulator is robust and traceable, we are implementing a comprehensive logging
 and error-handling framework:
 • 
• 
• 
• 
Central Logger Utility: The 
utils/logger.py module will configure Python’s built-in 
logging
 module for the entire application. We will set up multiple log levels (DEBUG for detailed step-by-step
 traces, INFO for high-level events, WARNING/ERROR for issues). All classes will retrieve a logger
 instance (for example, named after the class or module) via a helper function or class. This could be
 as simple as: 
import logging
 logging.basicConfig(filename='simulation.log', level=logging.DEBUG,
 format='%(asctime)s [%(name)s] %(levelname)s: %
 (message)s')
 class Logger:
 @staticmethod
 def get_logger(name):
 return logging.getLogger(name)
 By doing this in one place, all modules can use 
Logger.get_logger(__name__) or 
Logger.get_logger(ClassName) to get a logger. We already used this in the code snippets
 (each class storing 
self.logger = Logger.get_logger(...) ). The log configuration directs
 output to a file (
 simulation.log ) and includes timestamps, module names, etc., for easy
 debugging.
 Logging in Each Module: We add logging statements throughout the code:
 Debug-level logs for step-by-step values (e.g., each floater’s force and position update, drivetrain
 torque/power calculations, etc.). In debug mode, one could reconstruct the sequence of events and
 see intermediate values which helps in diagnosing issues or verifying physics.
 Info-level logs for significant events (e.g., injection/venting actions, simulation start/end, reaching a
 steady state, total output, etc.).
 23
• 
Error-level logs whenever an exception is caught. We ensure every 
except logs the exception
 message and relevant context (like which floater or time step) before propagating it.
 • 
• 
• 
• 
• 
Traceable Exceptions: We define custom exceptions in 
utils/exceptions.py such as: 
class SimulationError(Exception):
 """Generic exception for simulation errors, to wrap lower-level 
exceptions."""
 pass
 class FloaterError(SimulationError):
 """Exception raised for errors in Floater calculations."""
 def __init__(self, floater_id, message):
 super().__init__(f"Floater {floater_id}: {message}")
 The purpose is to wrap any unexpected errors with more context. For instance, if something in
 Floater.update causes a ZeroDivisionError or ValueError, we catch it and raise a 
FloaterError with
 the floater id or position included. The SimulatorController might catch a generic 
SimulationError and then log it and abort. This way, if an error occurs deep in the physics, the
 logs and exception message will clearly indicate which part failed. This is crucial for debugging a
 complex system with many floaters and time steps.
 Debugging Hooks: In addition to passive logging, we will incorporate a few features to facilitate
 debugging:
 A global debug flag or logging level that can be set via configuration (perhaps through a config file
 or environment variable). When debug is on, the simulator could run slower but with more verbosity
 or even interactive pauses.
 We might include an interactive mode hook: for example, if an environment variable 
SIM_DEBUG_MODE is true, the SimulatorController could break after each iteration or at a specific
 time and wait for user input (or drop into a Python debugger). This is optional, but a commented-out
 or easily activatable section in code can assist developers. For instance, in the 
step() loop we
 could have: 
if self.current_time >= debug_break_time:
 import pdb; pdb.set_trace()
 This wouldn’t be in production use, but the structure allows such insertion without disrupting the
 design.
 Assertions for numerical sanity: We can pepper the code with assertions to catch physically
 impossible values early. For example, after updating a floater, we might assert that its position
 remains within [0, water_depth] (if that’s expected), or that energy values aren’t negative. If an
 assertion fails, it raises an AssertionError which we catch and log as an error, helping catch bugs.
 24
Logging Outputs and Diagnostics: The simulation will produce a log file (
 • 
simulation.log ) that
 can be consulted for a post-mortem analysis. Additionally, some logs might be exposed to the user
 via the interface in future (e.g., showing warnings if something goes out of bounds). For now, the
 focus is on developer-facing diagnostics.
 By instrumenting the simulator with these logging and error-handling measures, we ensure complete
 traceability of the simulation. If the simulator outputs seem incorrect, one can enable DEBUG logging and
 see the sequence of forces, positions, torques at each time step to identify where it diverged from
 expectation. Moreover, any crash or exception will not be silent – it will bubble up with a clear message of
 what went wrong and where. This is particularly important before introducing more complex features, so
 that the baseline behavior is trustworthy.
 For completeness, below is a simplified example of the Logger utility class (as might be found in 
logger.py ):
 # utils/logger.py
 import logging
 utils/
 # Configure root logger (this can be done once in the application entry point)
 logging.basicConfig(
 level=logging.DEBUG,
 filename="simulation.log",
 filemode="w",
 format="%(asctime)s [%(name)s] %(levelname)s: %(message)s"
 )
 class Logger:
 """Utility class for obtaining configured logger instances."""
 @staticmethod
 def get_logger(name: str):
 """Get a logger with the given name, creating it if not already 
exists."""
 return logging.getLogger(name)
 And in 
utils/exceptions.py , for example:
 # utils/exceptions.py
 class SimulationError(Exception):
 """Base class for simulation-related exceptions."""
 pass
 class FloaterError(SimulationError):
 """Exception for errors in Floater computations."""
 25
def __init__(self, floater_id, message):
 super().__init__(f"Floater {floater_id}: {message}")
 class EnvironmentError(SimulationError):
 """Exception for errors in Environment or invalid parameters."""
 # ... similarly define init or pass
 With this setup, our classes use 
self.logger = Logger.get_logger("Floater") etc., and in
 exception handling we do: 
except Exception as e:
 self.logger.error(f"Exception in update: {e}")
 raise FloaterError(self.id, str(e))
 Thus, every error gets logged and turned into a SimulationError subtype which can be caught by the
 SimulatorController or by the Flask app to display an error message to the user if needed.
 5. Legacy Code Migration Plan
 We will now map the legacy code components from the current GitHub repository (
 Tonihabeeb/kpp
calc ) to the new modular structure. This mapping ensures that every important piece of logic is carried
 over (or eliminated if obsolete), and it identifies any changes needed in function interfaces to fit the new
 design.
 Below is a table outlining the migration of key legacy functions and code sections into the new modules,
 along with actions (migrate, refactor, or remove):
 Legacy Code (module or
 function)
 New Module/Class
 Migration Action & Notes
 Refactor: The procedural logic in 
engine.py
 SimulatorController.simulate()
 engine.py (main
 simulation script, one-shot
 calc)
 simulation/controller.py
 (SimulatorController class)
 replaced by a loop, but wrapped in a class. We will retain any existing
 interface for the Flask app by creating a function 
engine.simulate(params) that instantiates 
SimulatorController and calls its 
returning results. The legacy code’s structure of computing force,
 torque, power in sequence is preserved inside the new class’s step
 function.
 26
Legacy Code (module or
 function)
 New Module/Class
 Migration Action & Notes
 Migrate & Inline: The force calculation (buoyancy, drag, etc.) will now
 occur inside 
Floater.update() , using data from the Floater’s
 Environment instead of a separate function call
 compute_force(state, 
params)
 state and 
Floater.update() (and Environment)
 Floater.update
 formula is unchanged; we ensure 
force in the same way 
compute_force
 included buoyancy and drag logic, those lines move into Floater (see
 Floater example above). This function can then be 
legacy code.
 Migrate & Refactor: The legacy 
compute_torque
 compute_torque(state, 
force, params)
 Drivetrain.compute_torque_from_forces()
 force and multiplied by radius to get torque. In new code, we
 accumulate forces from all floaters (or net force) and implement this
 in the Drivetrain. If the old function assumed a single floater’s net
 force, we’ll adapt it to multiple floaters by summing forces first
 (consistent with physical principle). The interface changes: instead of
 passing 
state and 
force , we call 
drivetrain.compute_torque_from_forces(list_of_forces)
 Any reference to 
compute_torque
 compute_power(state, 
torque, params)
 Drivetrain.update_power()
 will be replaced by this method call via the controller. The old function
 is then removed.
 Migrate & Refactor: The legacy code’s power calculation is moved to 
Drivetrain.update_power . Likely it multiplied torque by angular
 velocity (implied by chain speed or given in params) to get mechanical
 power, and perhaps applied generator efficiency. We will ensure to
 include any efficiency or unit conversion. The new method takes 
angular_speed as input instead of deriving it from state (since
 state handling is now internal). The legacy calls to 
will be replaced with 
drivetrain.update_power(ω)
 in legacy can be removed.
 Migrate: If the code had any separate calculation for buoyant force or
 drag (for instance a function 
buoyant_force(volume)
 constant for water density, drag coefficient), those are now
 Buoyancy & Drag constants
 or functions (e.g., if there
 were 
buoyancy.py or
 simply constants in engine)
 simulation/physics handled in Floater/
 Environment
 encapsulated. For example, water density and 
Environment . Drag coefficient might have been a constant or
 input; it’s now provided via 
Environment.get_drag_coefficient()
 deleted from their old places. All calls that used those constants will
 use Environment or Floater’s internal calculation.
 27
Legacy Code (module or
 function)
 New Module/Class
 Migration Action & Notes
 Refactor: In legacy code, H1 might have been handled by modifying
 density or drag directly in formulas when a flag is set. We move this
 logic to 
Nanobubble effect
 integration (H1 logic)
 Environment & 
hypotheses/
 h1_nanobubbles.py
 Environment.get_water_density
 get_drag_coefficient (or to a function in 
h1_nanobubbles.py that Environment calls). The existing flags or
 conditions (like 
if use_nanobubbles: ...
 removed from scattered locations and centralized. Interfaces: the UI
 input for H1 will set 
env.nanobubble_active=True
 computation function was likely present, so this is more structural
 change.
 Refactor: If legacy code had a special-case formula for compression
 work when H2 is enabled (or perhaps none at all if not implemented
 yet), we implement it as shown in 
Isothermal compression
 logic (H2)
 PneumaticSystem.compute_injection_work()
 & 
hypotheses/h2_isothermal.py
 The flag 
PneumaticSystem.inject_air
 use_isothermal (coming from UI) toggles which formula
 is used. Any old computation of compressor work (maybe a constant
 offset) is replaced by these formulas. The interface from UI remains a
 boolean flag for H2; internally, 
PneumaticSystem
 Pulse mode logic (H3)
 Drivetrain.update_pulse_mode() & 
hypotheses/h3_pulse_mode.py
 need for legacy code deletion if it wasn’t implemented; otherwise
 remove old conditional code.
 Migrate/Stubs: Legacy code might not have implemented H3 at all
 (since it’s complex). If there were placeholder calculations (e.g., an
 assumption of increased efficiency or a different mode), we will
 isolate those. For now, we add a placeholder method in Drivetrain and
 plan to flesh it out in later stages. Any references in code to a “pulse
 mode” or H3 (perhaps toggling generator on/off) will be
 encapsulated. We remove or comment out incomplete legacy code
 and instead ensure the structure is ready to receive H3 logic later.
 Refactor: Originally, the app might have passed many parameters
 around or used them globally. We consolidate these into a 
structure. The 
SimulatorController.__init__
 needed values and pass to each component. This means functions
 Global parameters (e.g.,
 number of floaters,
 dimensions, etc.)
 params (dict or dataclass) & various class init
 params dict now are methods that refer to object
 that took a 
attributes. For example, 
compute_force(state, params)
 params for floater properties; now Floater already has those
 properties. We will remove parameter passing where unnecessary
 (since each class has what it needs). We keep 
level configuration and for the Flask interface.
 28
Legacy Code (module or
 function)
 New Module/Class
 Migration Action & Notes
 Output assembly (e.g.,
 creating result dict of
 outputs for UI)
 SimulatorController.results_log or return
 value
 Migrate: The legacy engine likely produced a dictionary or tuple of
 outputs (net power, efficiencies, etc.). In the new setup, we
 accumulate time-series data. To maintain compatibility, if the UI
 expects a single result (like total energy or final efficiency), the
 controller can compute that at end and return similarly. We may write
 an adapter: for example, an 
engine.simulate()
 Flask) that calls 
controller.simulate()
 results_log to extract the final or key values (or generate plots,
 etc.). No core physics code is lost; this is just refactoring how results
 are packaged.
 Refactor: The Flask routes (in 
app.py
 something like 
result = engine.run(inputs)
 to 
result = engine.simulate(inputs)
 Flask app integration
 (app.py routes calling
 engine)
 app.py updated to use new controller
 engine.py with a facade function, 
change. We ensure that whatever 
app.py
 outputs to render in a template) is still provided. If needed, we
 transform the new data structure to match the old. The rest of the
 Flask app (templates, static files) remains the same, so this is a
 minimal change.
 Any deprecated or
 experimental code not in
 use (e.g., test functions,
 print statements)
 Removed
 Delete: During refactoring, if we find any code that is not part of the
 main simulation flow (old test routines, debug prints, redundant
 calculations that were replaced by newer ones), we will remove them
 to clean the codebase. For instance, if there was an old alternative
 formula kept for reference but not used, that can be taken out
 (assuming the analysis confirms it’s safe). The goal is a clean package
 without dead code.
 Notes: We will maintain a version control commit history to track these migrations. Each major migration
 (e.g., creating Floater class and moving code into it, etc.) can be one commit, referencing this plan for
 justification. This way, the mapping above is verifiable in the repository’s history.
 Additionally, after migration, we’ll run a thorough test to ensure that given the same inputs, the new code
 produces the same outputs as the legacy code. Minor differences might occur (e.g. due to the time-stepping
 versus one-shot calculation, or if we fixed a bug during refactoring), but physically they should align. If
 discrepancies are found, we will use the logging to trace and correct them.
 29
6. Coding Standards and Documentation
 Throughout the refactoring, we adhere to professional software engineering standards to make the code
 readable, maintainable, and extensible:
 • 
• 
• 
• 
• 
• 
Naming Conventions: We use PascalCase for class names (e.g., 
Floater , 
PneumaticSystem , 
SimulatorController ) 
and 
snake_case 
for 
compute_torque_from_forces , 
variables 
water_density , 
and 
functions 
(e.g.,
 time_step ). This uniformity ensures the
 codebase looks consistent and intention-revealing. Constants, if any, will be all caps (though in
 Python we might put them in Config or Environment rather than as global constants). These
 conventions follow PEP 8 style guidelines.
 Docstrings and Comments: Every module, class, and public method will have a NumPy-style
 docstring explaining its purpose, parameters, returns, and any important details. For example, as
 shown in the code snippets, classes have a summary and attributes listed; methods describe their
 behavior and parameters. We favor clarity in docstrings to aid future developers (or ourselves) in
 understanding the code quickly. Inline comments will be added for complex logic sections, especially
 where we implement physics formulas, to note the source of the formula or any assumption. If any
 formula comes from a reference, we can cite it in a comment or docstring.
 Type Hints: We include Python type hints for function parameters and return types (as seen in
 snippets like 
def update(self, dt: float, environment: Environment) -> None: ). This
 helps with static analysis and makes the interfaces more explicit. We assume Python 3.8+ is in use,
 so type annotations are fine.
 Module structure and imports: Each module at the top will import what it needs with absolute
 imports from the package (e.g. 
from kpp_simulator.simulation.environment import 
Environment ) to make dependencies clear. We avoid circular imports by design (the structure is
 mostly hierarchical: controller imports all models, models don’t import controller, etc.). If needed, we
 might use forward declarations or interface abstractions to break circular dependencies (for
 instance, if a Floater needs to notify the controller, we’d likely handle that via controller checking
 f
 loater state instead).
 Directory Layout Justification: The layout given earlier is meant for large-scale simulation
 engines, separating concerns clearly. Physics and simulation code is under 
simulation/ , distinct
 from web 
app.py and any visualization assets. This mirrors common practices in complex
 applications where backend logic is isolated from interface code. We also made a sub-package for
 hypotheses to keep those optional features modular; one can imagine toggling them or even
 loading them dynamically (for example, one could disable that sub-package if only baseline physics
 is needed). The 
utils folder holds generic utilities like logging and exceptions that could be
 reused or extended (for instance, we might add a 
utils/config.py if configuration management
 grows).
 Testing and Validation: Although not explicitly requested, we plan for easy testing. The modular
 design means we can create unit tests for each module. For instance, we can test that
 Environment.get_water_density() returns expected values with nanobubbles on/off, or that
 30
PneumaticSystem.inject_air yields less work when 
use_isothermal=True vs False for the
 same conditions, verifying H2’s effect quantitatively matches theory. We can also test a single time
step in SimulatorController against a known scenario. By structuring code into pure functions and
 methods with clearly defined inputs/outputs, writing tests or even performing manual calculation
 checks becomes straightforward.
 • 
• 
• 
Documentation: In addition to docstrings, we will likely create a README or developer guide (could
 be part of repository) summarizing how to run the simulator, how the code is organized (much like
 this plan), and how to add new features. This is important as the project grows (especially moving
 toward CFD integration or AI control, where multiple contributors might be involved).
 Code Snippets in Documentation: We will incorporate snippets (like we did above) into the project
 documentation to illustrate typical usage of classes. For example, showing how to instantiate and
 run the simulation from a Python shell for a quick test: 
from kpp_simulator.simulation.controller import SimulatorController
 params = {'num_floaters': 66, 'floater_volume': 0.1, ...}
 sim = SimulatorController(params)
 results = sim.simulate(total_time=10.0, dt=0.1)
 print(results[-1]['power'], "W net power")
 This serves as both a test and an example for users.
 Maintainability: By abiding by these standards, the code will be easier to maintain. New
 contributors (or ourselves in a few months) can read the docstrings to grasp each component’s role.
 The consistent style prevents trivial issues that distract (like inconsistent naming or unclear variable
 purpose). Moreover, future stages (like introducing a reinforcement learning agent or a high-fidelity
 f
 luid model) can be done by extending classes or adding new ones without needing to rewrite the
 entire system.
 To visualize the directory and module organization, we provided a textual tree earlier; one could also
 draw a UML diagram of class relationships. While not included here, we conceptually have something like:
 SimulatorController uses Environment, contains many Floater, one Drivetrain, one PneumaticSystem, and
 some Sensors. Floater uses Environment. PneumaticSystem uses Environment and Floater. Drivetrain is
 independent but takes input from floaters via controller. This relatively simple relationship map will be
 documented for clarity so that later we can see where, say, a new “ControlUnit” module might fit (likely
 SimulatorController or a subclass will integrate it).
 In summary, the coding standards and documentation ensure that the refactored code is not just
 functionally correct, but also clean, readable, and well-documented, meeting professional expectations.
 7. Integration with the Dash/Flask Web Interface
 One of the requirements is that the new backend integrates seamlessly with the existing Dash-based Flask
 web interface. The user interface should not have to change significantly (or at all) as a result of the
 31
refactoring – instead, we adapt the backend to fit the interface’s expectations. Here’s how we will achieve
 that:
 • 
• 
• 
Preserve API Endpoints: If the Flask app (
 app.py ) currently defines routes like 
/calculate or
 uses callback functions to run the simulation upon form submission, we will keep those routes. The
 only change is what they call internally. For example: 
# Original
 @app.route('/run_simulation', methods=['POST'])
 def run_simulation():
 params = parse_request(...) # get form data
 result = engine.calculate(params) # legacy call
 return render_template('results.html', data=result)
 We will replace 
engine.calculate with our new interface. We might implement an 
in the new structure as a lightweight wrapper: 
# New engine.py (for compatibility)
 from simulation.controller import SimulatorController
 def calculate(params: dict):
 sim = SimulatorController(params)
 results = sim.simulate(params.get('total_time', 10.0),
 params.get('time_step', 0.1))
 # Possibly process results into desired output format
 final = results[-1] # example: take final step data
 return final
 This way, the Flask route can still do 
engine.py
 result = engine.calculate(params) and get a similar
 object as before (for instance, a dictionary with 
power , 
torque , etc., presumably to display). By
 keeping this function name and signature, the front-end code does not need to change at all. It’s
 a facade over the new class-based engine.
 Dash Callbacks / Front-End Data Flow: If the interface uses Dash (which often involves callbacks for
 updating graphs), it likely calls some Python function for calculations. We will ensure those callbacks
 now use the new modules:
 For example, if a Dash callback was doing something like: 
def update_graph(num_floaters, volume, ...):
 outputs = engine.run_simulation(num_floaters, volume, ...)
 return make_fig_from(outputs)
 We’ll point 
engine.run_simulation to our new SimulatorController. Possibly we can simplify by
 pre-computing all time series and then just returning the data needed for the graph.
 32
• 
Ensuring real-time: The question suggests the UI is Dash-based with possibly real-time interaction.
 Stage 1 and 2 guides mention using server-sent events (SSE) and Chart.js for live updates. Those
 changes are Stage 1/2 though – for Pre-Stage, the interface might still be static (submit form -> get
 results and static charts). We won’t implement SSE at this stage (unless the legacy already had some
 form of it, but likely not). Instead, we keep the same pattern (compute then render).
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
If the web interface displays charts (Matplotlib or Plotly images), we ensure to generate those the
 same way:
 ◦ 
◦ 
Possibly the legacy code generated Matplotlib figures for torque vs time, etc., saved them to 
static/plots/ and the HTML refers to those images. We will keep that approach for now.
 The SimulatorController after simulation could call a 
plotting utility (maybe we add 
simulation/plotting.py ) that plots the results_log data into images. This is an ancillary
 task: maintain output format.
 We can incorporate the existing plotting code (if any) into a 
Plotting class or function, or
 simply keep it procedural but call it from our new engine.
 Parameter Passing: The front-end form likely collects inputs (like number of floaters, etc.) and the
 backend code parsed them into a dict or variables. We will use the same keys expected by our
 params . The 
SimulatorController can accept either the dict or we convert to our
 SimulationParams 
dataclass 
if 
we implement one. Since we designed
 SimulatorController.__init__ to fetch keys like 
'num_floaters' , 
'floater_volume' ,
 etc., it should match whatever the HTML form names are. If not, we adjust either the parsing or the
 keys to remain consistent.
 No UI Change Visible: From a user’s perspective, after this refactor, they should operate the
 simulator exactly as before:
 They input values in the form, click run, and get results (numbers and charts) in the same format.
 If previously it took a couple seconds to compute and then displayed a page, it should behave
 similarly. (Performance might slightly differ but likely negligibly for the same computations).
 All labels, units, and text on the results page remain the same unless there was a clear mistake
 before.
 If any new information is now available (like we can now provide time-series data), we will not expose
 it unless requested, to stick to “transparent” integration. Later stages can introduce new UI elements
 for the new capabilities (like live graphs in Stage 2).
 Testing with the Web UI: We will test the refactored simulator by running the Flask app and
 performing the typical user interactions. This is to catch any integration bugs such as:
 Missing imports (if app.py was not updated to import the new engine or controller).
 Data type mismatches (e.g., if the template expected an integer and we gave it a float).
 File path issues for plots (ensuring any plot images are saved in correct static path).
 Multi-user or multi-run issues (the new design mostly uses local variables, reducing shared state,
 which is good for handling multiple requests safely – but we should confirm no global state leaks;
 33
e.g., 
results_log is within the controller instance, so concurrent runs would have separate
 instances).
 • 
• 
• 
• 
• 
• 
Dash/Flask Conventions: If the app uses Dash, it might rely on a global 
app.layout and
 callbacks rather than Flask routes. In that case, integration means ensuring our functions work
 under the Dash callback. Because Dash is still Python on backend, it should be fine. If Dash expects a
 quick response but we want to do a long simulation, we might not address that until Stage 1’s
 streaming. Pre-Stage, presumably the simulation was already doing a calculation potentially heavy
 but acceptable.
 Maintaining Global Session (if any): In some Flask apps, they store parameters or results in
 flask.session or global variables for subsequent requests (or to avoid recomputation). We
 should see if legacy did that. With our design:
 We can regenerate everything each run (which is fine for moderate simulation durations).
 Or we could store the 
SimulatorController in a global variable to allow pausing/resuming (but
 likely not needed until live sim).
 Given “transparently”, we likely just do the simplest: compute fresh each time user runs it, as before.
 Compatibility Layer Duration: The 
engine.py compatibility wrapper can remain for now.
 Eventually, when front-end is rewritten to fully leverage the new structure (like SSE or interactive
 control), that wrapper might be removed and 
app.py can directly use 
SimulatorController .
 But that’s a future refactor – not doing it now avoids unnecessary front-end changes.
 In conclusion, the new modular backend will plug into the old interface with minimal adjustments. We
 essentially preserve function signatures and output formats so that from the outside it behaves
 identically. The heavy lifting just happens in our new organized way internally. This allows us to improve the
 code without interrupting usage or requiring the user to learn a new interface. Once verified, the users (or
 stakeholders) should notice improved reliability (and perhaps slight performance improvement), but no
 confusion or downtime in using the simulator.
 8. Alignment with Future Upgrades (CFD Integration and AI
 Experimentation)
 The Pre-Stage upgraded architecture is deliberately designed with the future in mind. By enforcing a
 modular, object-oriented structure now, we ensure that the simulator can serve as a solid foundation for
 advanced features planned in later stages – including high-fidelity fluid dynamics and AI-driven
 optimization or control strategies. We highlight how this new design aligns with those long-term goals:
 • 
• 
CFD-Ready Fluid Dynamics: In later development, the simple buoyancy and drag calculations might
 be replaced or augmented by a CFD solver or a more sophisticated fluid model to capture complex
 effects. Thanks to our refactoring:
 The Environment class is the focal point for fluid properties. To integrate CFD, we could create a
 subclass of Environment or a new module that interfaces with a CFD library (for example, one that
 can compute forces on objects given flow conditions). Because Floater asks Environment for forces
 34
or densities, we can modify Environment’s methods to call out to a CFD simulation (or take inputs
 from a precomputed CFD dataset). This swap would not require changing Floater’s logic – fulfilling an
 easy plug-in of more advanced physics.
 • 
• 
• 
• 
• 
• 
• 
• 
• 
The modular separation also means we can run the KPP simulation in co-simulation with a CFD tool:
 e.g., at each time step, get drag force from an external solver. Our architecture could allow the
 Environment to be an adapter to an external service. This extensibility is only possible because we
 now have clear boundaries between components.
 The design mirrors how many industrial simulators are structured: a core framework orchestrating
 specialized modules (a physics engine, a fluid solver, etc.). We are laying that framework now on a
 small scale, so scaling up will be natural.
 Advanced Hypotheses Implementation: The H1, H2, H3 modules we created as placeholders can
 be fleshed out with more complex logic or even experimental algorithms:
 H1 (Nanobubbles): If future R&D provides a complex model for drag reduction (say, as a function of
 bubble size, flow rate, etc.), we can implement that inside 
h1_nanobubbles.py and adjust
 Environment accordingly. Our current code already reduces density/drag by constants; improving it
 might involve time-dependent effects or interactions with CFD (like local density variation). The
 structure is ready to accommodate that.
 H2 (Thermal): Perhaps a future model will simulate heat exchange more dynamically or involve a
 thermodynamic state for each floater’s air. We could then expand PneumaticSystem to track air
 temperature, or even create an 
Air class. Because we modularized pneumatic aspects, these
 additions won’t tangle with unrelated parts (e.g., the drivetrain doesn’t care how H2 is implemented;
 it just sees the final torque).
 H3 (Pulse Mode & Control): This likely ties into control algorithms and mechanical additions
 (flywheels, clutches). Our Drivetrain class already has fields for inertia and clutch state. In Stage 2 or
 Stage 3, we might introduce a ControlUnit module (as hinted in the R&D blueprint) that decides
 when to engage/disengage the clutch. Our current design allows that: we could have
 SimulatorController consult a control logic class each step for commanding the drivetrain or
 pneumatic system. Because sensors are separate, providing data to a control algorithm is
 straightforward.
 The clear delineation of hypotheses in code also makes it easier to run experiments: for instance,
 one can turn H1/H2/H3 on or off in the parameters without side-effects. We can even run
 combinations (our code permits multiple to be active together, e.g., nanobubbles + isothermal) to
 see integrated effects – something valuable for research.
 AI-Enhanced Experimentation: One goal is to integrate reinforcement learning or other AI to test
 control strategies. Our architecture supports this in several ways:
 Isolation of Control Logic: Right now, the SimulatorController is fairly simple and deterministic. We
 can evolve this by adding a new module (say 
control.py with a 
ControlAgent or using
 external RL libraries) that interacts mainly via sensors and actuators (pneumatic valves, clutch,
 generator load). Because our physics are decoupled from control, one could plug in an AI agent that
 at each time step observes the state (we can furnish it with sensor readings: positions, speeds, etc.)
 and outputs actions (inject or vent air, engage or disengage clutch, adjust generator resistance).
 35
Implementing this would not require rewriting the physics engine – just connecting a new loop or
 agent in the SimulatorController. For example, instead of our simple sensor check: 
if bottom_sensor.check(f): pneumatic.inject_air(f)
 we might have: 
action = control_agent.decide(f.state, sensor_readings)
 if action == "inject": pneumatic.inject_air(f)
 And that 
• 
• 
• 
• 
control_agent could be an AI policy.
 Data Logging and Visualization: We already log everything in a structured way. This data can feed
 into training AI models or analyzing performance. The architecture allows easy extraction of time
series data from simulations, which is critical for AI (they need a lot of simulation data to learn).
 Scalability: If we incorporate an AI that tries many simulations (hyperparameter searches, etc.), our
 code’s modular nature means it can be run headless (without the UI) in a loop. E.g., one can import
 SimulatorController in a separate script to run 100 simulations with different control policies.
 This is facilitated by not entangling the simulation with Flask or global state.
 Extensibility for New Features: Beyond what’s listed, a modular design is generally easier to
 extend. For instance, if later we want to simulate multiple units together (farm of KPPs), we could
 create a higher-level class that contains multiple SimulatorControllers or shares an Environment.
 Because each SimulatorController is self-contained, they won’t conflict. Or if a new hypothesis (say
 H4) comes up, we can add another module without touching existing ones.
 Performance Considerations: While not a primary focus of Pre-Stage, being modular also allows
 future optimization. For example, if profiling shows the Floater update is slow for 66 floaters, we
 could vectorize that using NumPy or numba – since it’s isolated, we can swap out its implementation
 without affecting others. Or we could run certain components in parallel threads/processes (maybe
 compute each floater in parallel) since state sharing is controlled. The logging and structure help
 identify bottlenecks clearly.
 To tie this with the full upgrade path: the blueprint documents envision a transition from this refactored
 simulator to a real-time interactive tool with live graphs and even possibly coupling to external solvers or
 controllers. Our Pre-Stage implementation is the necessary groundwork for that evolution: - Stage 1 (Real
Time Loop & Streaming) will be trivial to implement now: we already have a loop; converting it to a
 generator for SSE output is straightforward. The SimulatorController could easily yield data each iteration. 
Stage 2 (Enhanced UI and dynamic control) slots into the architecture by adding control logic and using our
 logging for Chart.js integration. We have effectively pre-structured the code as the Stage 2 guide expects
 (with a Floater class per floater, etc.). - The final vision of a full R&D simulator with AI and CFD is achievable
 because the system components mirror the real subsystems (as described in the R&D blueprint). We have
 classes for each major subsystem, consistent with the blueprint's modular breakdown, meaning our
 codebase can grow in the same way the problem description is structured.
 36
In essence, this Pre-Stage upgrade brings the project to a professional-grade architecture that bridges the
 gap between a simple calculator and a research-grade simulator. It ensures that all subsequent
 enhancements – whether adding complexity in physics or in control intelligence – build on a solid,
 organized foundation. The alignment with later stages is not just incidental, it’s deliberate: we built the
 scaffolding so that each new feature fits in naturally, avoiding the need for another major refactor down the
 line.
 9. Conclusion
 This implementation plan outlined a detailed approach to refactoring the KPP Simulator into a modular,
 maintainable architecture. By splitting the system into clear components (Floaters, Environment, Drivetrain,
 Pneumatics, Sensors, Controller, Hypothesis modules) and applying rigorous software engineering
 practices, we achieve a simulator engine that is easier to understand, extend, and debug. The legacy code’s
 physics calculations have been preserved exactly within this new structure – ensuring continuity in results 
while the codebase itself becomes far more robust against errors and amenable to future upgrades.
 We provided examples of class definitions, method implementations, and module interactions to illustrate
 how the refactored code will look and operate. The use of logging, exception handling, and documentation
 will greatly aid both development and usage, as issues can be traced and the code can be self-taught by
 reading docstrings and logs. A migration mapping was given to serve as a checklist during development:
 developers can systematically move each piece of the old code into its new home and verify nothing is lost
 or incorrectly translated.
 After implementing this Pre-Stage upgrade, the KPP simulator will be immediately better structured and
 ready for the next steps (Stage 1 real-time simulation loop, Stage 2 interactive control and live visualization,
 and beyond). Crucially, the web interface remains functional and unchanged from the user’s perspective 
all improvements are under the hood, which is ideal for incremental development. 
This guide will serve as a reference throughout the refactoring process, and later as documentation for new
 contributors to quickly grasp the system’s design. By following this plan, we will have a KPP simulation
 codebase that not only answers the current needs but also scales to meet the ambitious research and
 development goals of the project. The Pre-Stage upgrade is therefore a foundational investment that sets
 the stage for a sophisticated, industrial-grade Kinetic Power Plant simulator. 
1
 2
 Stage 1 Implementation Guide_ Real-Time Simulation Loop Upgrade.pdf
 f
 ile://file-GpMuyKuXh2AZkbDqvhrgVu
 37