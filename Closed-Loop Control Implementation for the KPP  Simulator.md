Closed-Loop Control Implementation for the KPP
 Simulator
 Introduction
 In the Kinetic Power Plant (KPP) simulator, the current 
1
 control.py module uses open-loop logic 
meaning actuators follow pre-set sequences without feedback. To improve performance and realism, we
 need to replace this with a closed-loop control framework. Closed-loop control uses sensor feedback
 (floater positions, pressures, speeds, etc.) to adjust actuators in real time, ensuring stable and efficient
 operation . This guide outlines a physics-based implementation of such a control system, covering the
 control of air injection and venting, clutch engagement, and generator torque. We will design a modular
 controller with per-floater state machines and global supervision, respecting physical constraints (e.g.
 torque and RPM limits, air pressure thresholds) and optimizing objectives like steady power output and
 sustained motion above stall speed . The solution will be extensible for advanced strategies (e.g. PID
 tuning or reinforcement learning control) and integration with real hardware.
 2
 3
 Modular Control Framework Overview
 To manage the KPP’s multiple subsystems, we implement a modular control framework. The control logic
 is organized into distinct modules or controllers, each responsible for a specific actuator or subsystem, all
 coordinated by a central control unit (which can be a class in 
control.py ). Key control modules include: 
• 
• 
• 
• 
4
 5
 Floater Control (Air Injection & Venting): Handles the timing of bottom air injection and top
 venting for each floater. This uses a finite state machine per floater to decide when to open/close
 valves based on position sensors and time/pressure criteria . 
Generator Torque Control: Adjusts the generator’s electromagnetic torque (load) in response to
 chain speed or power output feedback. A feedback controller (e.g. PID) modulates torque to
 maintain a target speed or power, preventing stall or overspeed . 
Clutch Control: Engages or disengages the generator (or flywheel) from the drivetrain. In normal
 operation the clutch stays engaged, but a pulse-and-coast strategy (periodically disengaging to let
 the system free-run, then re-engaging) can be implemented for smoother output . 
Compressor/Air Supply Control: Manages the air compressor and pressure tank. It ensures
 sufficient air pressure for injection by turning the compressor on/off based on pressure sensor
 readings (e.g. using hysteresis between minimum and maximum pressure thresholds) . 
1
 9
 6
 7
 8
 These controllers work in concert: sensor inputs feed into the control logic, which computes actuator
 commands each simulation step. By isolating each function, we can test and tune modules independently
 . For example, one could swap a rule-based injector logic with a different algorithm or an RL agent
 without altering the rest of the simulator . This modular design also mirrors the real KPP
 subsystems, aiding future hardware integration.
 9
 10
 1
Sensors and Actuators: In the simulator, we model various sensors and actuators that the control logic will
 use:
 • 
• 
• 
• 
Position Sensors: A bottom sensor detects when a floater reaches the bottom injection zone, and a 
top sensor detects when a floater nears the top for venting
 4
 5
 . These can be implemented as
 boolean flags set when a floater’s vertical position crosses a threshold. 
Pressure Sensors: We have a floater internal pressure sensor (or equivalently a sensor for the air
 inside the floater) to gauge fill level, and a tank pressure sensor for the compressor’s air reservoir.
 The tank sensor ensures we only inject air when sufficient pressure is available . 
Speed/Tachometer: A generator RPM sensor (or chain speed sensor) provides feedback on rotational
 speed. This is crucial for torque control to maintain speed and avoid stall/overspeed . 
Actuators: The control logic can open/close the air injection valve at the bottom and air vent valve
 at the top for each floater station. It controls the generator’s electromagnetic torque (via adjusting
 load or a brake). It also toggles the clutch and turns the compressor motor on or off (or adjusts its
 11
 1
 drive). In code, these would be functions or methods like 
open_valve(position) , 
set_generator_torque(value) , 
engage_clutch(bool) , 
interfacing with the physics model.
 The control unit in 
compressor_on() etc.,
 control.py will read all sensor inputs each time-step and update each actuator
 command accordingly. We next detail each control module’s logic, including objectives, constraints, and
 relevant physics.
 Control Objectives and Constraints
 When designing the closed-loop controllers, we must enforce physical constraints and aim for certain
 performance objectives:
 • 
• 
• 
Maintain Stable Power Output: The net electrical output of the generator should be relatively
 smooth and continuous, despite the pulsating nature of buoyant forces. The control system should
 avoid large oscillations in generator torque or speed by proper timing of actions and use of the
 f
 lywheel/clutch for smoothing
 3
 3
 . For instance, if multiple floaters lift simultaneously (a surge of
 torque), the controller can temporarily increase load to harness this extra energy and prevent
 overspeed . 
Sustain Above Stall Speed: The chain and floaters must keep moving continuously. The controller
 must prevent scenarios where the system grinds to a halt due to excessive load or poor timing. A 
minimum RPM threshold can be defined; if the generator speed falls near this stall point, the
 control logic should react (e.g. reduce generator torque to let the system accelerate, or ensure an
 upcoming floater injection happens promptly). Likewise, a maximum RPM limit is set for safety – if
 approached, the controller can increase load or engage a brake to avoid overspeed . 
Min/Max Torque Limits: The generator torque command is bounded by the machine’s capabilities.
 We enforce 
1
 T_min ≤ T_command ≤ T_max . Typically, T_max is the generator’s rated torque
 (beyond which it cannot provide more braking force), and T_min may be zero (no load) or even
 negative if regenerative/motoring mode is allowed (though in normal operation we likely use 0 as
 minimum braking torque). The control logic must saturate any computed torque to this range and
 handle saturation gracefully (for example, if a PID controller demands a high torque beyond T_max,
 it will just apply T_max). 
2
• 
• 
• 
• 
Air Pressure Constraints: The compressor’s air supply has a finite pressure. We define a minimum
 operating pressure P_min below which injection is not effective (the floater might not fill properly)
 and a maximum P_max as a safety limit for the tank. The control will delay or avoid opening the
 injection valve if tank pressure is below P_min
 11
 . Similarly, it will stop the compressor once P_max is
 reached to prevent overload. A hysteresis control is used to avoid rapid toggling: for example, turn
 the compressor on when pressure drops slightly below P_min, and turn it off when pressure rises
 above P_max . 
8
 User-Specified Configuration: The control logic should work for varying numbers of floaters, floater
 volumes, and chain geometries as set by the user. If the user increases the number of floaters, the
 controller will simply manage more floats (the state machine runs for each floater in the loop).
 Floater volume affects buoyant force and the amount of air needed – the injection control may use
 volume in computing the air mass or time needed to achieve buoyancy. Chain geometry (depth of
 tank, distance between floaters, sprocket radius, etc.) influences timing (how long from bottom to
 top) and required torque (longer chains or larger sprockets may change torque conversion). All these
 parameters are taken from the simulator’s configuration, so our control algorithms should reference
 them instead of hard-coding values. For example, the buoyant force on a floater is 
12
 13
 F_buoyant = 
ρ_water * g * V_displaced – with floater volume $V$ set by the user, the controller can
 estimate the force available when filled . The torque on the sprocket from one floater would
 be 
14
 τ_f = F_buoyant * R_sprocket (force times sprocket radius) , and the net torque
 driving the generator is the sum of torques from all buoyant floaters minus the weight of
 descending ones and losses. The generator power is $P = τ_{\text{gen}} * ω_{\text{gen}}$ ,
 which we log and try to keep steady. These equations guide the control decisions – for instance,
 knowing the expected buoyant force helps decide how much load the generator can handle without
 stalling. 
15
 Real-Time Load Matching: In some scenarios, the KPP may be connected to a variable load or grid
 demand. Our control framework is designed to accommodate a power setpoint if provided. For
 example, if the user or an external system specifies a desired power output, the torque controller
 can adjust to maintain that output (subject to physical limits). This can be done by dynamically
 altering the target RPM or directly using a power-feedback loop (since $P = τ * ω$, the controller can
 modulate torque to reach the desired $P$ given the current speed). Initially, we focus on constant
speed or maximum-efficiency control, but the structure allows adding a higher-level supervisor that
 tunes the generator torque to match load demand in real time. 
Extensibility to Advanced Control: The modular design ensures we can plug in different control
 strategies. For example, a PID controller might govern generator speed; later, an RL agent could take
 over the same actuator by observing sensor states and outputting torque or valve commands .
 By encapsulating the decision-making (policy) separately from the plant interface, we make it easy to
 switch between manual, PID, or AI controllers. Similarly, each floater’s valve logic could be replaced
 or augmented by a learning algorithm that optimizes timing. We will structure the code such that
 these substitutions are straightforward (e.g., a flag to use RL vs. rule-based logic, or a strategy
 pattern for the controller classes).
 10
 With these goals and constraints in mind, we now detail each control module’s implementation.
 3
Floater Air Injection & Venting Control (Floater FSM)
 Each floater goes through a cyclic sequence of states as it traverses the loop: it gets filled with air at the
 bottom (to become buoyant and rise) and vented at the top (to become heavy and sink). We implement this
 via a finite state machine (FSM) per floater, which triggers the appropriate valve actions at the correct
 times. The states and transitions are:
 • 
EMPTY (Water-Filled): The floater’s internal ballast tank is filled with water (no air), making it heavy.
 This is the state for floaters on the descending side. When an EMPTY floater reaches the bottom
 position (detected by the bottom sensor), the control logic initiates an air injection: we open the
 bottom injection valve for that floater and transition the floater’s state to FILLING. In code: 
4
 if floater.state == "EMPTY" and bottom_sensor_triggered(floater):
 open_valve("injection", floater.id)
 floater.state = "FILLING"
 floater.fill_start_time = t_now
 # start air injection
 # record injection start time
 Rationale: The valve is kept closed until the floater is correctly positioned at the intake. Once aligned,
 opening the valve allows compressed air to rush in, displacing water out of the floater . We assume
 the simulator’s physics will handle the air–water exchange and buoyancy change once the valve is open. The
 compressor should ideally already have pressure built up for this injection (compressor control is discussed
 later). 
• 
16
 17
 FILLING: In this state, the floater is receiving air through the open valve. We maintain this state for a
 certain duration or until a condition indicates the floater is sufficiently buoyant. There are a few ways
 to determine when to stop filling:
 • 
• 
• 
A timer based on estimated fill time, computed from floater volume and compressor airflow rate.
 An internal pressure sensor reading – e.g. stop when internal air pressure equals the surrounding
 water pressure at that depth (meaning the floater is essentially full of air) .
 A buoyancy threshold – e.g. stop when the floater’s net buoyant force exceeds its weight by a
 margin (ensuring it will rise). 
13
 In our implementation, we can use a simple time threshold or check pressure if available. For example: 
if floater.state == "FILLING":
 # Example condition: inject for a preset duration or until target pressure 
met
 if t_now- floater.fill_start_time >= fill_duration or
 floater.internal_pressure >= target_pressure:
 close_valve("injection", floater.id) # stop air injection
 floater.state = "FILLED"
 18
 19
 This closes the bottom valve and marks the floater as FILLED (air-filled) . At this point the floater is
 positively buoyant and will begin to ascend the upward side of the tank. The Archimedes buoyant force
 now acting on it is $F_b = \rho_{\text{water}} \cdot g \cdot V_{\text{air}}$ (approximately equal to the weight
 4
of water displaced by the air volume in the floater). This upward force minus the floater’s weight provides a
 net upward thrust that turns the chain and sprocket. The simulator’s physics engine will translate that into a
 torque on the drive shaft (e.g., net torque = $F_{net} \times R_{sprocket}$). The control logic doesn’t need to
 compute this force directly every time-step – it’s inherently handled by physics – but we keep it in mind for
 understanding system behavior. We do log the amount of air injected and the time it took, which can be
 useful for efficiency calculations and for tuning the fill duration. 
• 
FILLED (Air-Filled): In this state, the valve is closed and the floater is moving upward, full of air. No
 direct control action is needed during ascent except perhaps monitoring. However, as the floater
 approaches the top of the water tank, the control must prepare to vent the air. A top position
 sensor will trigger when the floater is at or near the top. When this sensor trips for a FILLED floater,
 we initiate venting: 
if floater.state == "FILLED" and top_sensor_triggered(floater):
 open_valve("vent", floater.id)
 floater.state = "VENTING"
 floater.vent_start_time = t_now
 # start venting air at top
 # record vent start time
 5
 22
 This transitions the floater to VENTING and opens the top vent valve . In a real system, this might be a
 passive flap or an active valve that releases the compressed air to atmosphere. In simulation, opening the
 valve will let the floater’s internal air escape. We try to time the vent such that by the time the floater passes
 over the top sprocket and starts descending, it has lost most of its air . Often the vent valve might be
 opened just before the floater fully emerges from the water to ensure any remaining air is expelled quickly
 . 
• 
20
 21
 VENTING: While venting, the floater’s air is released and water starts to flood back in, making it
 heavy. We keep the top valve open for a brief period (vent duration) or until a sensor indicates the
 f
 loater is essentially full of water (e.g., an internal pressure sensor reading ~ambient pressure,
 meaning no air left). After that, we close the vent: 
if floater.state == "VENTING":
 if t_now- floater.vent_start_time >= vent_duration: # or 
floater.internal_pressure <= atmosphere
 close_valve("vent", floater.id)
 floater.state = "EMPTY"
 23
 This marks the floater as EMPTY again , completing the cycle. The floater goes over the top and now
 descends on the other side with its weight pulling the chain down. Gravity acting on the mass of the water
f
 illed floater contributes additional torque to the system on the descending side. We log the venting event
 as well (time and amount of air released). The cycle will repeat when this floater returns to bottom.
 Concurrent FSM Operation: We create such an FSM for each floater in the system. In code, this can be
 managed by iterating through all floaters each time-step and updating their state based on sensor
 conditions and timers, as in the pseudocode above. Many floaters will be in different states around the loop
 (some rising, some descending, etc.), and the control logic handles each independently but in a coordinated
 way. For example, if one floater’s bottom sensor triggers, we might start filling it even while another floater
 5
might simultaneously be venting at the top. The modular FSM design naturally supports multiple floaters:
 each floater object can carry its own 
state , 
fill_start_time , 
24
 vent_start_time , etc., and the
 control loop checks each one . This approach is simpler to implement than a strictly event-driven
 scheduler, and with a small time step (50–100 ms) it effectively captures the events in real time .
 26
 25
 Actuator Sequencing Considerations: Only one floater at a time will be at the bottom injector position, so
 typically only one injection valve opens at once in our setup (assuming a single injection point). The FSM
 logic inherently ensures that as soon as that floater moves up, the state changes and eventually the next
 f
 loater arriving will trigger injection. At the top, similarly one floater vents at a time. We must ensure valves
 do not remain open too long or open too early. For instance, if the fill time is too short, the floater might not
 gain enough buoyancy (resulting in sluggish ascent); too long and we waste compressed air. These
 parameters (fill_duration, vent_duration or pressure targets) can be tuned through simulation. In future,
 more sophisticated control could adjust injection amount adaptively (based on measured chain speed or
 power needs). For now, a reasonable fixed duration or threshold-based approach, as shown above, suffices
 .
 27
 Generator Torque and Speed Control
 The generator (or alternator) converts mechanical rotation into electrical power, and its load provides a
 resistive torque on the drivetrain. In the simulator, we can directly control the generator’s torque or load
 via the control module. The goal of generator control is twofold: (1) regulate the system’s speed (RPM) to
 avoid stalls or runaway speeds, and (2) deliver the desired power output in a stable manner. We achieve
 this through a feedback controller, typically a PID (Proportional–Integral–Derivative) loop, that adjusts
 torque based on the error between a target setpoint and the measured value.
 Speed Control (Stall/Overspeed Prevention): A straightforward strategy is to maintain a constant target
 speed (angular velocity) for the chain/generator. For example, suppose we aim for the chain to rotate at
 ω_target (which corresponds to a certain RPM). Each time-step, we read the current generator speed
 (ω_measured from the RPM sensor). The control logic computes the error: 
err = ω_target - 
ω_measured . The controller then sets the generator torque command to reduce this error. A simple
 proportional controller would do 
28
 T_command = K_p * err , where K_p is a gain. A full PID would
 incorporate integral (to eliminate steady error) and derivative (to damp oscillations) terms. When the
 f
 loaters produce excess torque (ω_measured tends to rise above target), the error becomes negative and
 the controller increases generator torque (because a positive err means we are below target speed, a
 negative err means we are above target so we need more braking torque to slow it). Conversely, if the
 system is slowing down below target (err positive), the controller reduces generator torque, easing the load
 so the buoyant force can speed it back up . This feedback ensures a roughly constant speed . It
 directly prevents stall: if the speed drops toward the minimum, the controller will drop torque to near zero,
 allowing the floats’ net force to accelerate the system again. It also prevents overspeed: if the chain starts
 accelerating too much (perhaps many floats buoyant at once, or after a clutch disengage), the controller will
 apply more resistive torque to curb the speed . Essentially, the generator controller acts like an
 electronic governor.
 28
 30
 29
 In implementation, after computing a raw torque command from the PID, we clamp it to [T_min, T_max] as
 discussed. We also incorporate a stall guard: if ω_measured falls below a threshold (say 5% of nominal
 speed), and perhaps if we detect that floaters are still supposed to be providing force, we might
 momentarily set T_command = 0 to let the system accelerate freely. (In extreme cases, if the system came to
 6
a stop, an external kick or using the motor/generator in reverse might be required, but ideally our control
 avoids this regime.) We also incorporate an overspeed check: if ω_measured exceeds a safe limit, we can
 apply max torque and even consider tripping the clutch or an emergency brake in a real system. These are
 safety conditions that wrap around the normal PID loop.
 Power or Load Matching: Instead of (or in addition to) constant speed, we might have a target power
 output. The controller can be configured to maintain constant output power if desired . To do this, it
 monitors electrical power $P = T_{\text{gen}} \cdot ω$ and compares it to P_target. The error 
29
 eP = 
P_target - P_meas can then be fed to a controller that adjusts torque. However, maintaining strict
 constant power might cause more speed variation. One compromise is to mostly regulate speed, but slowly
 adjust the speed setpoint to meet an average power target. In any case, the code structure allows switching
 the control objective. For initial implementation, we will likely use speed control (target RPM) via PID, as it’s
 simpler and ensures the mechanism runs smoothly . Later, a supervisory loop or the user can choose a
 different mode (e.g., if grid demand is high, allow the speed to droop a bit to generate more power).
 29
 Physical Equations: The generator’s effect on the system is modeled as a torque opposing rotation. In the
 physics engine, applying a torque $τ_{\text{gen}}$ opposite to the direction of motion causes a deceleration
 given by $τ_{\text{net}} = I_{\text{total}} \alpha$ (where $I$ is the total moment of inertia of the moving
 parts, and $α$ is angular acceleration). Our control loop essentially decides $τ_{\text{gen}}$ each step. The
 power extracted is $P = τ_{\text{gen}} \cdot ω$ (if in consistent units), which we can calculate for logging.
 Higher torque yields higher power extraction but more slowing force on the chain. There are limits: if
 $τ_{\text{gen}}$ exceeds the net buoyant torque driving the system, the chain will decelerate (possibly to
 zero if fully balanced or exceeded). At steady state, the controller will find a $τ_{\text{gen}}$ where
 $τ_{\text{buoyancy}} \approx τ_{\text{gen}}$ (plus losses), and the chain moves at a roughly constant speed.
 This is analogous to an equilibrium where input power from rising floaters equals output electrical power
 plus losses.
 In code, the generator control might look like: 
# Speed control PID (executed every time-step)
 rpm = measure_generator_rpm()
 error = target_rpm- rpm
 # PID controller (with state maintained between steps for integral/derivative)
 derr = (error- prev_error) / dt
 integral_error += error * dt
 torque_command = Kp*error + Ki*integral_error + Kd*derr
 # Apply torque limits
 torque_command = max(min(torque_command, T_max), T_min)
 set_generator_torque(torque_command)
 prev_error = error
 This pseudocode assumes we have some persistent variables for 
prev_error and 
integral_error .
 T_min might be 0 (no load) and T_max a specified max. The 
set_generator_torque() function would
 communicate with the drivetrain model to apply this as a braking torque on the shaft. If the clutch is
 disengaged (see next section), the controller might temporarily do nothing or accumulate the integral term
 without applying torque because the generator is not connected.
 7
Real-time Demand Input: If we introduce a variable demand, the above could be extended: e.g.,
 target_rpm might be adjusted dynamically or replaced with a power-based control. For example, if
 desired_power changes, one could compute a new torque setpoint as 
T = desired_power / (ω + 
ε) (where ε avoids divide-by-zero, and ω is current speed). Then use that as a feed-forward term in the
 torque controller. But careful coordination is needed to avoid sudden jumps – possibly a secondary PI loop
 for power could adjust the speed setpoint slowly. This is an advanced topic; the key point is our closed-loop
 structure and code modularity allow adding this feature without redesigning everything.
 Clutch Engagement Control (Pulse-and-Coast Mode)
 7
 The KPP design may include a clutch between the chain drive (with attached flywheel) and the generator.
 The clutch can be disengaged to decouple the generator, allowing the chain and flywheel to spin freely
 (coast) without generator load, then re-engaged to extract energy in bursts. The primary reason to do this is
 hypothesis H3: by pulsing the load, one can smooth out the effect of unsteady buoyant forces and possibly
 reduce losses . In practice, a continuously engaged generator might cause the chain to move in a
 somewhat jerky fashion as each floater provides a pulse of lift. By letting it coast, the floaters can gain
 speed (storing kinetic energy in the flywheel), and then when engaged, that kinetic energy is drawn out
 more smoothly.
 31
 Clutch States: The clutch has two states – Engaged (generator connected) or Disengaged (generator free,
 no torque transfer). We implement a simple state machine or schedule for the clutch: for instance, a pulse
 timing method might engage for X seconds, then disengage for Y seconds, in a repeating cycle .
 Alternatively, triggers can be event-based: e.g., disengage at moments when adding load would be
 inefficient or when we want to accelerate the system, and engage when the system has kinetic energy to
 harvest. The control logic can use sensor information to decide this. For example, it could monitor the net
 torque from floaters or the number of floaters currently lifting vs. sinking: - If a large net positive torque is
 about to act on the system (say several floaters just started rising while few are descending), the controller
 might disengage the clutch to let the chain accelerate freely (storing that energy in the flywheel’s speed)
 . - Once those floaters reach mid-ascent or the burst of buoyant force has passed (and perhaps fewer
 are in lift positions), the controller engages the clutch to have the generator absorb energy while the
 f
 loaters continue their motion
 31
 . This timing can also be tuned or learned.
 7
 For initial implementation, a simpler approach is to use a fixed duty cycle or a condition on speed: 
Example: If the chain speed exceeds a certain value (indicating plenty of kinetic energy), engage the clutch
 to put load and slow it down; if the chain speed drops below a lower threshold, disengage to let it speed up
 again. This is analogous to bang-bang control and can be used to keep speed within a band when
 continuous control is not as effective. However, it may introduce oscillations. A timed approach (engage for
 2 seconds, disengage for 2 seconds, etc.) is easier to implement but may not adapt to changing conditions.
 We will start with a basic configurable strategy and leave room for improvement or RL optimization.
 In code, clutch control might be as simple as: 
if use_pulse_mode:
 # Example: toggle clutch every T_pulse interval
 if (t_now % (T_engaged + T_free)) < T_engaged:
 clutch_engaged = True
 8
else:
 clutch_engaged = False
 set_clutch(clutch_engaged)
 else:
 # Default: always engaged
 set_clutch(True)
 When 
clutch_engaged = False , the 
set_generator_torque should effectively be set to zero (or the
 physics model should ignore generator torque) so that the generator stops resisting the motion. In our
 simulation, we can model this by simply not applying torque when the clutch is open. If using a physics
 engine that supports joint constraints, it could actually disable the joint between generator and shaft .
 32
 Flywheel Effect: We assume there is a flywheel inertia attached to the chain (either the chain itself and
 sprockets provide some inertia, or an explicit flywheel). When the clutch is disengaged, the flywheel + chain
 will speed up under the unopposed buoyant forces (aside from minor friction and drag) . This stores
 energy as rotational kinetic energy. When we re-engage the clutch, the generator feels a sudden torque
 demand as it now has to slow down the flywheel (converting that kinetic energy to electrical). The flywheel
 thus helps deliver a more continuous power even if the buoyant force is not continuous – it essentially
 smooths out the delivery by acting as an energy buffer . Our control logic for clutch will ideally
 coordinate with generator control: e.g., we might disable the PID speed controller during coasting (since
 the generator is disconnected, we don’t want it trying to apply torque). Instead, we might just let the speed
 rise. Once engaged, we could either resume normal speed control or even apply a high torque briefly to
 quickly extract energy (depending on strategy). Care must be taken to avoid very abrupt engagement – in a
 real system, one would likely use a clutch that can slip or engage gradually to avoid shock. In simulation, an
 instantaneous engage is okay if the physics engine can handle the impulse (or we ramp the torque in one
 step).
 32
 33
 34
 Extensibility: Because manual tuning of a pulse-and-coast sequence can be tricky (too long coasting may
 overspeed, too short may underutilize potential, etc.), we design the code to allow experimenting. Perhaps
 a set of parameters for clutch timing or a placeholder for an RL agent to control the clutch. For now, our
 implementation can include a simple mode that the user can enable (H3 on/off). If off, clutch remains
 engaged 100% (standard operation). If on, use either fixed timing or a basic conditional rule as above. We
 will monitor the results (e.g., see if the generator power output graph becomes smoother or net energy
 improves, as expected ). The code structure might put clutch logic in its own function or within the
 35
 control policy, and it will read needed sensor info (like 
decide.
 Compressor and Air Supply Control
 floater_positions or 
current_time ) to
 The compressed air system provides the working fluid (air) to inject into floaters. It typically consists of a
 compressor motor, an air tank/accumulator, and valves. In simulation, we focus on controlling the
 compressor (on/off or speed) and tracking the tank pressure. The objective is to ensure there’s always
 sufficient pressure for the next injection, while minimizing the compressor’s energy consumption (since it’s
 a parasitic load that subtracts from net output).
 9
On-Off Control with Hysteresis: We implement a simple closed-loop control for tank pressure using two
 thresholds: - P_max: desired high pressure (compressor off threshold). - P_min: low pressure threshold
 (compressor on threshold).
 The logic each time-step: 
if tank_pressure < P_min:
 compressor_on()
 # turn on compressor (or increase speed)
 elif tank_pressure > P_max:
 compressor_off()
 # turn off (or idle)
 36
 This is a hysteresis band to avoid rapid cycling . For example, we might set P_min = 8 bar and P_max = 10
 bar. The compressor will run until 10 bar, then stay off until pressure drops to 8 bar, and so on. Additionally,
 we will force the compressor on during an injection event if needed. When a bottom valve opens, a large
 volume of air is about to flow out of the tank into the floater, causing a pressure dip. To keep pressure up,
 we can preemptively run the compressor when an injection is in progress . In practice, a more advanced
 model might simulate pressure dynamics via $dP/dt$ equations, but an approximation is fine: e.g., if any
 f
 loater is in FILLING state (valve open), run the compressor at full power continuously until that fill is done.
 This ensures maximum airflow. After filling, the compressor can continue until P_max is reached then shut
 off.
 37
 Airflow and Power: The compressor’s effect on pressure can be modeled by some rate (e.g., adding $\Delta
 P$ per second depending on motor power and tank volume). Similarly, when a valve is open, air flows out
 and reduces pressure. We may implement a simplistic model: for each time-step $\Delta t$ that the
 injection valve is open, reduce the tank air mass by a certain amount (based on floater volume and pressure
 differential), and from that deduce pressure drop (using ideal gas law $P V = m R T$ if assuming isothermal,
 or just a fixed drop per volume). The compressor when on adds air mass (or pressure) at a certain rate (e.g.,
 in simulation units, +0.5 bar per second of runtime, depending on its power). The compressor’s power
 consumption should also be accounted for in net energy calculations – typically $P_{\text{compressor}} =
 \frac{\dot{m}_{air}}{\eta} \cdot (\text{compression work per unit mass})$. We might not need a detailed
 thermodynamic model; it could be as simple as subtracting a fixed wattage when the compressor is on (or a
 variable one if speed control is implemented). The user can specify an efficiency or we can assume, say, 70%
 efficiency for compression. This way, we include the cost of running the compressor in the energy balance.
 In code, a simplified update might be: 
# Pseudocode for compressor and tank update each step:
 if compressor_active:
 tank_pressure += compressor_rate * dt # increase pressure
 compressor_energy += compressor_power * dt # accumulate energy consumption
 if any(floater.state == "FILLING" for floater in floaters):
 # simulate pressure drop from injection
 tank_pressure-= injection_rate * dt # drop pressure according to airflow 
out
 if tank_pressure < 0: tank_pressure = 0
 10
# Clamp pressure between 0 and P_max (safety)
 tank_pressure = min(tank_pressure, P_max_limit)
 Then apply the on/off logic as given to set 
compressor_active (this would actually be done before the
 above update in practice). In a more realistic model, 
injection_rate could depend on the pressure
 difference between tank and water (higher when tank pressure is high and floater is empty, then reducing
 as pressures equalize). Also, if multiple floaters could theoretically be filling at once (in our base design only
 one at a time), we’d account for that air usage.
 Coordination with Floater Control: The compressor control ties in with the floater FSM: we delay opening
 a bottom valve if 
tank_pressure < P_min . In practice, our code might check: 
if floater.state == "EMPTY" and at_bottom and tank_pressure >= P_min:
 # allow injection (as shown earlier)
 ...
 else if floater.state == "EMPTY" and at_bottom and tank_pressure < P_min:
 # not enough pressure; maybe wait (do nothing this step, compressor will 
ramp up)
 pass
 This ensures we don’t start filling with inadequate pressure, which could result in partial fills and stall the
 cycle. The simulator might also show an alert if pressure is frequently dipping too low, indicating the
 compressor or tank is undersized.
 Multiple Floaters & User Settings: With more floaters or larger float volume, air consumption per cycle
 increases. The user’s configuration might necessitate a larger compressor (higher compressor_rate). We can
 expose such a parameter. The control logic remains the same, but it’s important to tune P_min/P_max
 relative to those volumes. For example, if floaters are large, perhaps P_min should be higher to ensure
 enough air to fill one completely. These details can be refined through simulation testing.
 Extensibility: The compressor control is currently a simple bang-bang (on/off) controller. In the future, one
 could implement a PID pressure controller to drive the compressor motor speed or a variable valve to
 maintain pressure more precisely. Also, an RL agent could conceivably manage compressor timing for
 efficiency (e.g. learning to only compress at certain times to optimize net energy ). Our modular
 approach would allow replacing the on/off logic with a more advanced controller easily.
 38
 Time-Step Integration and Main Control Loop
 Integrating the control logic with the simulator’s main loop is crucial for real-time operation. The simulator
 runs in discrete time steps (
 dt typically 0.05–0.1 s). At each step, we update physics, read sensors, decide
 on control actions, and apply those actions. Pseudocode for the combined loop is as follows:
 1. 
Physics Update: Advance the simulation by one time step 
dt . This involves computing forces
 (buoyancy, gravity, drag) and integrating motions. For example: calculate buoyant force on each
 f
 loater ($F_b = ρ g V_{\text{submerged}}$) , gravity on each (Weight = m * g), net force/torque on
 12
 11
the chain, and update velocities and positions
 2. 
3. 
39
 40
 . The physics engine or integration code
 handles this, producing the new state (positions of floaters, chain speed, etc.). 
Sensor Reading: Using the updated state, we simulate sensor readings
 4. 
5. 
6. 
7. 
41
 . For instance:
 bottom_sensor_triggered(f) returns True if floater f’s position is at the bottom (within some
 threshold).
 top_sensor_triggered(f) similarly for the top position.
 measure_internal_pressure(f) returns the current internal air pressure of floater f (if tracked
 in the physics model).
 measure_generator_rpm() returns current generator rotational speed (from the drivetrain
 model).
 tank_pressure is tracked as part of the pneumatic model. These values are stored for use in the
 control logic. In code, this could simply be checking attributes (e.g. a floater’s 
8. 
y coordinate) or
 calling functions that encapsulate the check. 
Control Decision: The control module (which we’re implementing) now processes the sensor data to
 decide actions for this step
 42
 agent choose an action here
 43
 44
 . If we had an RL agent, we would form an observation and let the
 . In our rule-based design, we directly implement the logic (as
 9. 
10. 
11. 
12. 
13. 
14. 
15. 
16. 
17. 
18. 
4
 5
 detailed in sections above):
 Iterate through each floater and update its FSM state, possibly opening/closing valves as conditions
 meet (injection/venting logic) .
 Check and update the compressor control (turn on/off based on pressure).
 Compute the generator torque command via the PID controller using the measured speed (and/or
 power).
 Decide clutch state (engage/disengage) based on the chosen strategy (pulse timing or always
 engaged). These decisions together form the action for this time-step. We ensure that all constraints
 are respected: e.g., if the PID wants a torque beyond limits, we clamp it now; if a floater is supposed
 to inject but pressure is too low, we hold off opening that valve. This decision step is effectively the
 core of 
control.py . 
Actuation: Apply the decided actions to the simulation environment
 45
 46
 . This means:
 Call functions to actually open/close valves in the model. For example, if 
open_valve("injection", floater.id) was invoked in the logic, this might set a flag in the
 f
 loater or pneumatic system that causes the physics model to allow air flow into that floater. If a
 valve was closed, we set that flag false so no flow occurs. 
Set the generator torque in the drivetrain model (e.g., call
 drivetrain.set_load_torque(torque_command)). This tells the physics engine to apply that resistive
 torque for the next integration step. 
Set the clutch state in the drivetrain model (e.g., drivetrain.clutch_engaged = True/False or call a
 method to engage/disengage the clutch joint). If disengaged, the drivetrain should ignore generator
 torque application. 
Turn the compressor on or off: e.g., set compressor.power = rated_power when on, or 0 when off,
 and perhaps update 
47
 tank_pressure as described.
 These actuator commands immediately influence the next physics update. For instance, if we open a
 bottom valve now, in the next cycle the physics will simulate air flow and buoyancy increase; if we
 increase generator torque now, the next cycle will see a greater opposing torque slowing the
 rotation . 
Logging and Monitoring: Each step, we log relevant data for analysis and debugging . This
 includes sensor readings (positions, pressures), control actions taken (valve states, torque values),
 and resulting performance metrics (generator power, chain speed, etc.). Logging is important for
 48
 12
verifying that the control logic is working as intended and to tune parameters. For example, we can
 check a time-series of generator RPM to see if our PID is keeping it near target, or look at tank
 pressure over time to ensure it stays within limits. If needed, we can also implement on-screen or file
 logging of any alert conditions (like “Pressure too low to inject! – delaying injection”). 
19. 
20. 
Visualization Update: In a live simulator (especially since this is a web-based simulator per the
 spec), after each step we update the display of floater positions, perhaps animate the chain, and
 update numeric indicators for power, efficiency, etc.
 49
 50
 . This doesn’t affect the control logic but
 is useful for the user. 
Loop Continuation: Increase simulation time by dt and loop back to physics update
 51
 . The loop
 continues until the simulation end condition (which might be a fixed time or some steady-state
 detection).
 This main loop ensures tight coordination between physics and control. By running at a time-step of e.g.
 0.05 s (20 Hz), we capture control events with sufficient granularity. This update rate is realistic for a PLC or
 microcontroller in an actual KPP control system as well (20 Hz control is common for mechanical systems).
 One important note is that all control actions are effectively simultaneous within a step – in the code, we
 might compute them in a certain order, but we should apply them after reading sensors to represent a
 synchronous update. For instance, we don’t want the act of opening a valve to influence the sensor
 readings in the same cycle; it should only affect the next cycle’s physics. Our pseudocode accounts for that by
 f
 irst reading sensors, then deciding, then acting. This avoids logical race conditions.
 To illustrate the loop flow, consider a brief example sequence: a floater arrives at bottom, sensor triggers ->
 control opens valve (injection starts); the next few steps injection continues, then stops after fill_duration ->
 f
 loater ascends; later top sensor triggers -> control opens vent; after vent_duration -> closes vent.
 Meanwhile, every step the generator PID is adjusting torque to keep speed ~constant, and the compressor
 kicks on as soon as injection started (pressure drop) and refills tank. All these happen seamlessly in the
 loop. If multiple floaters are spaced, their injection/venting events will overlap in time but the control FSM
 handles each independently in those few lines of code within the loop.
 Code Structure and Implementation Notes
 We propose organizing the control logic into classes or functions within 
control.py for clarity and
 extensibility. For example, we might have: - A 
ControlUnit class that holds references to all subsystems
 (floaters, drivetrain, pneumatics) and implements an 
update(dt) method containing the loop logic
 above. It can have sub-methods for each control task (e.g., 
update_floaters() , 
update_generator() ). - A 
FloaterControl class or simply using the Floater objects themselves to
 hold state and provide methods like 
inject_air() or 
vent_air() . However, since the logic ties closely
 with sensors, it might be simplest to implement in one place in the control loop as shown in pseudocode. 
The 
ControlUnit can be initialized with parameters like setpoints (target RPM or power), limits, and
 possibly references to a higher-level strategy (manual, PID, RL). It can load those from user input or a config
 at simulation start .
 52
 An example partial implementation outline in 
control.py might look like: 
13
class ControlUnit:
 def __init__(self, floater_list, drivetrain, pneumatics, target_rpm):
 self.floaters = floater_list
 self.drivetrain = drivetrain # contains generator and clutch
 self.pneumatics = pneumatics # contains compressor, tank
 self.target_rpm = target_rpm
 # PID controller state
 self.prev_err = 0.0
 self.int_err = 0.0
 # maybe load Kp, Ki, Kd from config
 def update(self, dt, current_time):
 # 1. Read sensors
 bottom_triggers = [f.check_bottom_sensor() for f in self.floaters]
 top_triggers
 = [f.check_top_sensor() for f in self.floaters]
 rpm = self.drivetrain.get_generator_speed()
 tank_p = self.pneumatics.tank_pressure
 # 2. Floater FSM control
 for i, floater in enumerate(self.floaters):
 if floater.state == 'EMPTY' and bottom_triggers[i] and tank_p >=
 self.pneumatics.P_min:
 floater.state = 'FILLING'
 floater.fill_start_time = current_time
 self.pneumatics.open_injection_valve(floater)
 elif floater.state == 'FILLING':
 if current_time- floater.fill_start_time >=
 self.pneumatics.fill_time or floater.internal_pressure >=
 floater.target_pressure:
 self.pneumatics.close_injection_valve(floater)
 floater.state = 'FILLED'
 if floater.state == 'FILLED' and top_triggers[i]:
 floater.state = 'VENTING'
 floater.vent_start_time = current_time
 self.pneumatics.open_vent_valve(floater)
 elif floater.state == 'VENTING':
 if current_time- floater.vent_start_time >=
 self.pneumatics.vent_time:
 self.pneumatics.close_vent_valve(floater)
 floater.state = 'EMPTY'
 # 3. Compressor control
 if tank_p < self.pneumatics.P_min:
 self.pneumatics.compressor_on()
 elif tank_p > self.pneumatics.P_max:
 self.pneumatics.compressor_off()
 # Also if any injection valve open, ensure compressor on
 14
if any(f.state == 'FILLING' for f in self.floaters):
 self.pneumatics.compressor_on()
 # 4. Generator torque control (PID)
 error = self.target_rpm- rpm
 self.int_err += error * dt
 derr = (error- self.prev_err) / dt
 torque_cmd = Kp*error + Ki*self.int_err + Kd*derr
 # clamp torque
 torque_cmd = max(min(torque_cmd, self.drivetrain.T_max),
 self.drivetrain.T_min)
 self.prev_err = error
 # 5. Clutch control
 if self.drivetrain.use_clutch:
 if current_time % (T_eng + T_free) < T_eng:
 self.drivetrain.clutch_engaged = True
 else:
 self.drivetrain.clutch_engaged = False
 else:
 self.drivetrain.clutch_engaged = True
 # 6. Apply generator torque (only if clutch engaged or to flywheel)
 if self.drivetrain.clutch_engaged:
 self.drivetrain.set_generator_torque(torque_cmd)
 else:
 self.drivetrain.set_generator_torque(0.0) # free spinning
 # (Physics update will handle applying torques next step)
 The above pseudocode is a rough integration of earlier logic. In practice, the actual code may differ
 (especially how valves and compressor are controlled through classes). But it shows the structure: read
 sensors, update each subsystem’s control, then issue commands.
 File Structure: We recommend following the modular file structure that separates physics models and
 control. For example, as suggested in the project blueprint, we could have a 
models/ directory with
 floater.py , 
drivetrain.py , 
54
 . 
The 
simulation.py 
pneumatics.py , and a 
control.py for the control logic class
 53
 main loop would instantiate the ControlUnit and call
 ControlUnit.update(dt) every step, after updating the physics . This separation means the control
 logic is not buried inside the physics update code, making it easier to modify or replace. It also mirrors real
world systems where control software is distinct from the physical system model. If not already, consider
 55
 refactoring any monolithic code into this structure for clarity: for instance, ensure 
control.py contains
 only control-related computations and triggers, while the effects of those triggers (like changing floater
 buoyancy when valve opens) are handled in the physics model (perhaps in 
pneumatics.py or within the
 Floater class’s update).
 15
Future Hardware Integration Strategy
 Designing the control logic with modularity and clear interfaces lays the groundwork for transitioning from
 simulation to a real KPP hardware controller. Key considerations for real-world implementation include:
 • 
• 
• 
• 
• 
Sensor Interface: In simulation, sensor values are directly read from internal state. In hardware,
 they would come from physical sensors (e.g., limit switches, pressure transducers, encoders). By
 abstracting sensor reads (e.g., having functions like 
check_bottom_sensor() ), we can later map
 those to hardware I/O calls or PLC registers. The control algorithms themselves remain unchanged 
they don’t need to know if a floater is at bottom because a simulation Y-coordinate crossed a
 threshold or because a real switch closed; they just get a boolean or value. We might employ a HAL
 (Hardware Abstraction Layer) pattern where the ControlUnit calls an interface that is implemented
 differently for simulation vs. hardware. 
Actuator Interface: Similarly, in simulation 
open_valve(floater) might set a state in the
 model, whereas in hardware it would send a signal to a solenoid or motor driver. By giving actuators
 semantic commands (open/close, set torque value), we can reuse the logic. For instance,
 set_generator_torque(x) in hardware might translate to sending a command to a variable
 load controller or to a motor if we ever drive the chain. A real compressor might be simply an on/off
 relay for the motor, which matches our 
compressor_on/off control exactly.
 56
 Timing and Communication: The 50–100 ms control loop can be executed on an industrial
 controller or microcontroller. We must consider sensor latency and actuator response. In the
 simulator, everything is instantaneous for simplicity. In reality, valves take some milliseconds to
 open/close, the compressor has a spin-up time, and sensors might update at certain rates. We could
 simulate some of these (adding a small delay or first-order lag to valve actions) to test robustness
 . In hardware, one would incorporate those into the control design (perhaps adding a safety
 margin to the fill timing, etc.). The FSM approach is quite suitable for PLC implementation as well 
PLC ladder logic or state charts can mirror these states (EMPTY, FILLING, etc.) triggered by sensor
 inputs. The pseudocode we wrote could be translated to structured text or ladder logic on a PLC
 controlling real valves.
 Calibration and Tuning: The simulation allows trying different parameters (PID gains, fill durations,
 pressure thresholds) safely. Those tuned values provide a starting point for real hardware, though
 differences in real fluid dynamics mean further tuning on-site will be needed. We suggest using the
 simulator to conduct many tests (e.g., varying number of floaters, or adding noise to sensors to see
 how the controller copes ) – this will inform how to harden the control for real life (maybe adding
 f
 ilters, or interlocks if something goes wrong, like a floater failing to fill). 
56
 Monitoring and Fail-safes: A real system would have additional safety logic: e.g., if a floater doesn’t
 f
 ill in expected time, close valves to avoid dumping too much air; if pressure is not building even with
 compressor on, trigger an alarm. We can simulate some fault conditions to ensure our control code
 is structured to handle them. The modular approach means we could plug in an override state if
 needed (for instance, an emergency stop that immediately closes all valves and cuts power). In
 hardware, the control program and safety PLC would handle that; in simulation, we could
 incorporate checks and a “paused” state for the control loop if needed.
 16
Incremental Deployment: Eventually, to use this control logic on hardware, one might integrate it
 with actual sensor readings. If using Python in a PC that interfaces with the KPP hardware (less likely
 for real-time, but possible with proper libraries), the same control.py class could be used,
 replacing the physics engine updates with actual sensor polling. More realistically, the control logic
 would be reimplemented in a PLC or microcontroller environment. The clear state machine and PID
 algorithms outlined here are standard and can be directly coded in those environments. The
 simulator effectively serves as a digital twin, and by keeping the control logic similar to how one
 would do it in PLC, we ease the transition. For example, using state variables and simple logic is
 something that can be auto-coded or manually coded easily.
 In summary, the closed-loop control logic we developed for the KPP simulator not only improves the
 simulation’s fidelity and performance (by reacting to the system’s state in real time), but it is structured in a
 way that can inform actual KPP control system development. By leveraging physics equations for decision
 thresholds and maintaining modular code, we ensure that the control is both realistic and extensible 
ready for testing different strategies (like PID vs RL) and eventually guiding a physical kinetic power plant.
 Conclusion
 We have transformed the KPP simulator’s control from an open-loop sequence to a comprehensive closed
loop control system. This implementation guide covered the design of each control module – floaters’
 injection/venting state machine, generator torque PID control, clutch logic, and compressor management 
with attention to physical realism (buoyancy, torque, power equations) and constraints. We provided
 pseudocode and code structure recommendations to assist in implementing this in the control.py
 module, ensuring it integrates smoothly with the simulator’s main loop and physics engine. By organizing
 the control logic into modular components and using sensor feedback throughout, the simulator will
 achieve stable and efficient operation closer to a real KPP. Furthermore, the design is prepared for future
 enhancements like advanced control algorithms or direct use with hardware interfaces. With this guide,
 simulation engineers and control developers should be able to implement the closed-loop controller,
 yielding a more interactive and accurate KPP simulation and a stepping stone toward real-world
 deployment of the kinetic power plant’s control system. 
Sources: The above design principles and sequence are informed by the KPP system descriptions and
 simulator blueprint , ensuring our implementation aligns with the intended operation of the
 buoyancy-driven energy generator. 
Kinetic Power Plant (KPP) R&D
 Simulator Algorithm Blueprint.pdf
 file://file-DEKb2MeVDubPyHbxBzQBuC
 [PDF] natural vibrations – one degree of freedom - Freestudy
 http://www.freestudy.co.uk/d225/t10.pdf
 Unit 1 Fluid Properties and Hydrostatic Forces | PDF | Pressure ...
 https://pt.scribd.com/document/417485439/Unit-1-Fluid-Properties-and-Hydrostatic-Forces
 • 
57 4 29 8
 1 2 3 4 5 6 7 8 9 10 11 12 13 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32
 33 34 36 37 38 39 40 41 42 43 44 45 46 47 48 49 50 51 52 56 57
 14
 15
 17
35
 53
 54
 55
 KPP Web Simulator – Technical Specification and Implementation Blueprint.pdf
 f
 ile://file-7rB6rbPcXP294uk4G722fb
 18