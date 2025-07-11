GUI Features of the KPP Simulator
 Interactive Controls: The simulator’s interface provides a set of buttons for selecting different operating
 modes and enhancements. Five mode buttons are available: Conventional Cycle, H1: Resonant Bubbles, 
H2: Thermal Amplification, H3: Drivetrain, and an Integrated Cycle that combines all H1–H3
 enhancements . Each button triggers a scenario via a JavaScript 
1
 3
 startAnimation(mode) function,
 highlighting the active button and resetting the scene to apply the chosen mode’s effects. A “Reset Camera
 & State” button is also provided to stop the simulation and return the 3D scene to its initial state . These
 buttons function as toggles for the hypothesized enhancements, aligning with the user-driven scenario
 selection envisioned in design documents (where enabling H1/H2/H3 is part of the simulation parameters)
 . However, the GUI only allows one preset combination at a time (each mode or all-in-one), rather than
 arbitrary on/off toggling of each enhancement in any combination.
 2
 4
 6
 3D Simulation Display: The core of the GUI is a real-time 3D visualization of the Kinetic Power Plant
 mechanism. The entire browser window serves as a canvas for a Three.js-rendered scene, showing the
 vertical water shaft, floaters on a chain, sprockets at top and bottom, and ancillary equipment like a
 generator/flywheel assembly. Users can interact with the view by orbiting, panning, or zooming the camera
 (mouse controls are enabled as noted in the instructions overlay) . The visual elements are designed to
 convey the system’s mechanics: floaters colored differently when ascending versus descending, a
 translucent cylinder for the water column, and mechanical components in distinct colors. For example, in
 the current implementation ascending floaters use a green material and descending floaters use blue (a
 simple form of color-coding buoyant vs. heavy floaters), whereas earlier prototypes envisioned light-blue vs.
 gray floaters . There is also a representation of the flywheel and generator: a cylindrical flywheel mesh
 and a boxy generator mesh are placed on the top platform . Notably, a dedicated visual for the air
 compressor/piping (which was present in a prior static HMI mockup ) is absent in the current interactive
 3D scene – the GUI does not explicitly show the compressor unit or its operation beyond what’s implicitly
 reflected in system power.
 9
 11
 7
 8
 5
 Information Panel: A small overlay panel provides textual context for the selected mode. When a scenario
 is activated, the GUI populates this panel with a title and description explaining what is being visualized
 . For instance, in H1 mode the title is set to “H1: Resonant Bubble Column” with a description about
 reduced drag via nanobubbles, H2 mode describes an isothermal expansion “kick” to ascending floaters,
 and H3 mode is labeled “‘Kick-and-Coast’ Drivetrain” focusing on the flywheel smoothing power pulses
 . The info panel helps the user connect the visual changes to their theoretical purpose. This corresponds
 to the system design goal of educating the user on each enhancement’s role. The panel is initially hidden
 and only fades into view when a simulation is running .
 10
 12
 Live Metrics Display – Power Gauge: The GUI features a “System Power” gauge that updates in real time
 during simulation runs. This is a textual readout in kW accompanied by a horizontal bar indicator . The
 gauge is initially gray and centered at 0 kW (50% bar fill) and then dynamically shifts color and fill based on
 the instantaneous net power output: positive power turns the text green with a growing green bar to the
 right, while negative power (net loss) turns the display red with the bar receding to the left . For
 example, in Conventional mode the simulation sets a negative power output (around –50 kW) to illustrate
 13
 14
 15
 1
16
 that the basic buoyancy machine would not produce net power . In contrast, the H2 mode produces
 pulsating positive power (peaks during “kick” events) and the Integrated mode stabilizes around a large
 positive output (~523 kW, meant to reflect the claimed 500 kW scale) . This power gauge is the
 primary real-time telemetry shown to the user. It aligns conceptually with the generator output metric from
 the simulation engine (net power after accounting for losses), which is a key result the backend computes
 each timestep. However, the current gauge is driven by front-end logic with hardcoded illustrative values for
 each mode, rather than streaming actual calculations from the physics engine.
 17
 19
 22
 27
 23
 28
 24
 18
 25
 21
 18
 Visualization of H1–H3 Effects: The GUI’s 3D animation incorporates special visual cues to represent the
 advanced hypotheses: - H1 (Nanobubbles) – When H1 mode is active, the scene enables a light-colored
 “nanobubble water” layer in the shaft , illustrating that the water in the descending column has been
 altered (made less dense or less viscous). In the animation logic, H1 also causes descending floaters to
 move faster than normal (simulating reduced drag). This visually reinforces the intended effect of H1: lower
 resistance on the down-going side. There is no separate numerical slider for nanobubble concentration 
the effect is either off or on via the mode toggle. In the actual simulation backend, H1 is supposed to be
 modeled by reducing water density or drag coefficient in force calculations . The GUI’s
 implementation mimics this qualitatively (faster descent, different water appearance) but does not
 quantitatively tie into a backend parameter for fluid density – it’s a visual stand-in rather than a direct
 coupling to the physics engine’s H1 variable. - H2 (Thermal Buoyancy Boost) – In H2 mode, the GUI highlights
 moments of an extra buoyancy “kick” for ascending floaters. Internally, the animation flags certain points in
 the cycle (e.g. when a floater has just started rising) and temporarily tints the floater red to indicate a burst
 of energy . During these moments, the power gauge spikes higher (e.g. simulating a surge above the
 base 180 kW output) . This is meant to represent the near-isothermal expansion of air in the floater
 providing extra lift and work output. In a real simulation, H2 would be implemented by modifying the
 buoyant force over time (e.g. accounting for thermal expansion of air to sustain lift) and would reflect in the
 power calculation continuously . In the GUI, the effect is scripted rather than computed: the red
 f
 lash and temporary power boost are hard-coded to illustrate H2’s concept, rather than resulting from a
 thermodynamic calculation. There is currently no direct user control to adjust the magnitude or timing of
 the thermal effect; it’s fixed in the animation. - H3 (Flywheel “Kick-and-Coast”) – In H3 mode, the presence of a
 f
 lywheel in the 3D scene becomes significant. The flywheel model spins up visibly during short “kick”
 intervals and slows down during lulls, and it has an emissive glow that brightens when spin rate is high
 . Meanwhile, the power gauge in H3 mode is steadier – the front-end logic keeps the displayed output
 around a constant level (e.g. ~150 kW) despite the pulsed input, to imply that the flywheel is smoothing out
 the power delivery . This directly corresponds to the H3 hypothesis of using a flywheel and clutch to
 store excess energy from bursts and release it during gaps, evening out the generator load. The design
 documents describe including a flywheel in the drivetrain module for this purpose , and the need for
 a clutch control mechanism to alternate between free coasting and power extraction . The GUI reflects
 these ideas in a simplified manner: the visual spinning and glowing of the flywheel indicate energy being
 absorbed and released, but no actual user-adjustable controls for a clutch or flywheel engagement are
 present. The entire H3 sequence is pre-programmed (with periodic “kick” impulses), and the user cannot, for
 instance, change when the generator is engaged or disengaged – the control logic is implicit. In the real
 simulator backend, one would expect a more explicit modeling of the flywheel inertia and clutch logic as
 part of the control module, affecting torque and RPM in real time; the current GUI does not interface with
 such a dynamic model, it only emulates the expected outcome visually.
 20
 29
 30
 31
 21
 26
 Overall, the GUI provides an immersive visualization with interactive scenario selection and a live power
 readout. These features map onto key aspects of the KPP system (floaters moving in real time, power
 2
generation, and the special enhancements) in an intuitive way. Next, we evaluate how each GUI feature
 aligns with the actual simulation functionality behind the scenes.
 Alignment of GUI Features with Simulation
 Backend
 Each element of the GUI corresponds to a physical or logical aspect of the KPP system. We examine whether
 these UI features are merely illustrative or truly backed by simulation computations:
 • 
• 
32
 33
 Floater Dynamics & Buoyancy: The visual motion of floaters in the GUI is qualitatively consistent
 with the simulator’s physics. The backend simulation (per design specs) treats each floater as an
 object with position, velocity, buoyant force, drag, etc., updating each time-step according to forces
 . In the GUI, floaters continuously circulate: rising on one side and descending on the other,
 at speeds that the script adjusts per mode (e.g. faster descent with H1, etc.). This reflects the general
 behavior the engine would calculate (floaters accelerating under buoyancy or weight and reaching a
 terminal velocity due to drag). However, the GUI’s floater motion is not driven by the physics
 engine in real-time – it’s computed by the front-end script. There is no evidence that the float
 positions in the UI are being updated from actual force integration from the backend; instead, the
 positions are determined by a preset mathematical path and speed factor . For instance, in
 conventional mode the floaters all move at a uniform base speed, whereas in a true simulation their
 velocity would be determined by solving Newton’s laws with buoyant and drag forces each moment.
 The alignment is conceptual (floaters move through the cycle correctly) but not numerical.
 Importantly, the number of floaters and geometry in the GUI (10 visible floaters on a short loop) is
 a downsized visual sample and does not match one-to-one with the backend’s parameters (which
 might simulate dozens of floaters along a 21.6 m tall loop). This likely was to keep the 3D scene
 uncluttered and performant. The physics engine, however, is expected to handle all floaters in the
 system (e.g. 66 floaters for a full-scale loop) and compute forces on each . In summary, the GUI
 correctly illustrates floater kinematics and buoyancy qualitatively, but it is not actually reading the
 backend’s computed positions or velocities. Any changes in floater dynamics due to parameter
 tweaks (mass, drag coefficient, etc.) on the backend would not automatically reflect in the current
 GUI, since those controls are not wired in.
 34
 5
 35
 Generator Torque and Power Output: The net power produced (or consumed) by the system is a
 crucial result from the simulation engine – it combines the mechanical output of the floaters driving
 the generator and subtracts losses like drag and compressor work. In the backend design, power is
 calculated each step from torque and angular speed, and efficiency can be derived . The GUI’s
 “System Power” gauge is intended to mirror this outcome. Each scenario button effectively sets a
 different power profile in the animation script: Conventional shows a constant negative power (the
 system can’t overcome its losses), H1 yields a small positive power, H2 produces an oscillating power
 output with high peaks, H3 gives a moderate steady power with pulses absorbed, and Integrated
 shows a high stable power output (on the order of the claimed 500 kW) . These behaviors
 align with the expectations from the hypotheses – e.g. the documentation anticipated that without
 enhancements the system would likely have net negative or zero output, while combining all
 enhancements could theoretically yield a large positive net output. However, the current power
 values in the GUI are hard-coded for demonstration. For example, finalPower = 523 kW is simply
 36
 38
 39
 37
 3
40
 assigned in Integrated mode , and –50 kW in conventional mode, rather than being computed
 from first principles. In the real simulator engine, the power would be derived from summing
 torques of all floaters on the sprocket and subtracting the compressor’s power draw per cycle. The
 GUI’s gauge does not (at this time) connect to a live calculation of torque or compressor energy – it’s
 updated via the front-end animation loop using assumed values . Therefore, while the presence
 of a power display is in line with the backend’s purpose (reporting power output), the values shown
 are not dynamically coming from the backend physics. The integration of this gauge with the
 simulation is incomplete: if one were to change a parameter like float volume or compressor
 efficiency in the engine, the GUI gauge would not automatically change accordingly because it isn’t
 actually querying the engine’s result. The groundwork for alignment is there (a placeholder for real
 power metrics), but full coupling would require hooking this gauge up to the simulation loop’s data
 (e.g. via a streaming API). 
18
 • 
• 
Air Compressor and Pumping Power: A significant part of the KPP’s physics is the air compressor
 that injects air into floaters. In the simulation backend, compressor behavior (pressure, flow rate,
 work input) needs to be modeled to calculate net energy balance. The current GUI does not have
 any direct interactive feature or readout for the compressor. There is no slider to adjust
 compressor motor power or an indicator for airflow rate or pressure. The only place the
 compressor’s effect appears is implicitly in the net power: the conventional mode’s –50 kW
 presumably includes the compressor’s consumption outweighing the mechanical output, and the
 positive outputs in other modes would be net of compressor input. Visually, earlier design iterations
 had included a green-colored box and pipe to represent the air compressor system , but in
 the implemented interactive GUI these components are either omitted or not emphasized (the 3D
 scene built in code does not add a compressor object). This suggests that the GUI is not actively
 simulating or displaying compressor dynamics (like tank pressure or on/off valve states). It’s a gap
 between the backend and frontend: the backend would ideally track compressor torque/power at
 each step (and perhaps allow control strategies like pulsing the compressor), but the frontend
 provides no window into that aside from the lump sum effect on total power. If the technical
 specification called for monitoring compressor performance or efficiency, those features are missing
 in the UI. Aligning this in future would mean including either a numeric display of compressor power
 usage or animations of air injection events. As of now, the user cannot see, for instance, how H2’s
 isothermal approach reduces compressor work; they only see the outcome as extra net power on the
 gauge.
 19
 41
 20
 21
 42
 H1 – Nanobubble Drag Reduction: In the physics engine, H1 would modify fluid properties (like
 effective density or drag) to reduce resistance on descending floaters . The GUI’s H1 mode
 does visually represent this concept: the descending side water is drawn in a lighter color (cyan) to
 signify the nanobubble-enriched water , and descending floaters clearly move faster than they do
 in conventional mode (indicating they encounter less drag). This is a qualitative alignment with the
 backend functionality – it confirms to the user that “H1 = lower drag, faster descent.” If the backend
 has a parameter for nanobubble fraction or efficacy, that is not exposed in the GUI (no slider or input
 for how strong the H1 effect is). Moreover, because the GUI’s implementation is internal, any
 quantitative difference (e.g. 10% drag reduction vs 50%) cannot be adjusted or read from actual
 simulation data in the current state. Essentially, the H1 toggle in the GUI turns on a visual simulation
 of H1’s impact, but it does not verify whether the backend’s H1 model is active or producing the
 expected gain. Since the GUI’s power gauge in H1 mode shows a small positive output (~+10 kW) ,
 one can infer the designer intended that H1 alone might tip the balance slightly positive. This is
 43
 4
consistent with the hypothesis that nanobubbles alone could yield a modest improvement. However,
 without integration, we cannot confirm if the real engine’s calculations (using reduced $
 \rho_{\text{water}}$ in buoyancy/drag formulas) produce that same +10 kW – the GUI simply
 assumes it for demonstration. Conclusion: H1’s presence in the GUI matches a corresponding
 planned feature in the simulation engine, but the linkage is not live. The GUI successfully
 communicates the idea of H1, yet does not pull actual data from the engine’s H1 calculations (which
 themselves may or may not be fully implemented in code yet).
 • 
• 
23
 H2 – Thermal “Kick” Enhancement: The backend algorithm for H2 would involve thermodynamic
 calculations – modeling how injecting air in a near-isothermal manner (or heating the air/water)
 gives additional buoyant force or does additional work on ascent. Practically, this could mean a
 f
 loater has extra upward force beyond what ambient-temperature buoyancy alone would provide,
 perhaps in a short interval after injection. The GUI aligns with this via the kick visualization: twice per
 cycle, an ascending floater flashes red and the power output jumps momentarily . This
 correlates with the idea of a burst of power when the H2 effect is realized (for example, when a
 f
 loater has newly injected warm air expanding, or some thermal exchange happening). The front
end sets the H2 mode’s baseline final power to ~180 kW and triples it during the brief kick windows
 , then drops to half for the rest of the cycle, creating a pulsating power curve. Such a pattern
 conveys that H2 provides intermittent boosts. Does this correspond to something the backend
 computes? If the simulation were running, one might expect to see a smoother continuous increase
 in buoyant force for H2 floaters, or perhaps a noticeable jump when the air is injected (if modeling a
 discrete event). The alignment here is weaker quantitatively: the GUI imposes a specific pattern
 of increase (likely for dramatic effect). In reality, the magnitude and timing of H2’s benefit would
 depend on thermal parameters (temperature difference, heat transfer rate) – none of which are
 adjustable in the interface. There’s no field to input water temperature or nanobubble fraction, for
 instance. So, while H2 is represented, it’s done in a static, scripted manner. The user cannot tell
 from the GUI whether the backend is actually calculating anything like air expansion work; they only
 see a conceptual outcome. We must assume at this stage that the GUI is ahead of the backend here– illustrating an intended effect that the physics engine might not yet produce on its own. To fully
 align, the backend’s H2 model (e.g. increased buoyant force due to lower effective density or added
 pressure in floaters) would need to drive the numbers that the GUI displays. As of now, H2 in the GUI
 aligns in spirit with the intended simulation functionality (increasing buoyancy via thermal means),
 but is not functionally tied to backend calculations or any real thermodynamic state in the sim.
 31
 26
 27
 44
 18
 H3 – Pulse/Coast Drivetrain (Flywheel and Clutch): The H3 feature is about mechanical energy
 management – using a flywheel to smooth out the rotational speed and store energy from pulses.
 Backend-wise, this means introducing rotational inertia (flywheel moment of inertia) and a clutch
 control that alternates between periods of accumulation and generation. The algorithm blueprint
 explicitly mentions including a flywheel in the model and a clutch to engage/disengage generator
 load . The GUI clearly has a flywheel object and shows it spinning at variable speeds. When the
 H3 mode “kicks” occur (analogous to short bursts of torque input), the GUI increases the flywheel’s
 rotation speed considerably and even changes its glow color, while keeping the generator output
 relatively smooth . This is a visual analog to the idea that the flywheel is absorbing those
 kicks (hence spinning faster) and preventing the generator output from spiking (hence gauge
 remains steady green). This element of the GUI is well-aligned with the concept of H3: it
 demonstrates the “kick-and-coast” behavior mentioned in documentation . The limitation is that,
 in the current state, the flywheel’s behavior in the GUI is predetermined by front-end logic.
 45
 5
46
 29
 31
 47
 There is no actual simulation of angular momentum or a user-controllable clutch. The front-end
 simply checks if a “kick” window is active and then chooses a flywheel speed (e.g. 20 rad/s during a
 kick vs 5 rad/s otherwise in H3 mode) . It does not model continuous spin-up or spin-down
 based on torque exchange; it toggles between two speeds. The clutch action (engage/disengage) is
 not something the user can trigger or see explicitly – one infers it from the behavior (when flywheel
 speeds up, presumably the generator was momentarily disengaged). In a true backend simulation,
 H3 would require solving differential equations for the flywheel’s speed as torque is applied or
 removed, and logic to engage the generator intermittently. None of that complexity is reflected or
 controllable in the GUI. In terms of alignment, the GUI has successfully incorporated the presence
 of a flywheel and its qualitative effect on system power, matching the blueprint’s description of H3’s
 role . But it falls short of being an interactive or faithful representation of the actual dynamics– it’s more of a canned demonstration. As such, H3 in the GUI is only superficially linked to backend
 functionality (since the backend’s H3 module, if implemented, would involve internal state not
 exposed here).
 • 
Real-Time Loop and Data Streaming: A crucial aspect of the simulation architecture is the time
stepped loop running continuously and providing live outputs . The GUI does run its own
 animation loop on the front-end – calling 
50
 52
 53
 51
 48
 49
 requestAnimationFrame and updating the scene many
 times per second . This achieves a smooth real-time animation. However, this loop is entirely
 separate from the Python simulation loop described in Stage 1/2 guides. In the intended design, the
 Flask backend would run the simulation in real-time and stream data (via Server-Sent Events or
 similar) to the browser, where JavaScript would handle incoming data to update visuals and charts
 . Currently, the GUI does not utilize any data streaming from the server – there is no
 EventSource or WebSocket opened, and no AJAX calls fetching simulation results per tick. The
 animate() function in the JavaScript is effectively a client-side physics surrogate, not a
 rendering of server-provided state. This means the front-end’s time loop and the back-end’s time
 loop (if the latter is running at all) are not synchronized or connected. For example, the design
 documents suggest yielding JSON data each time-step (time, torque, power, efficiency, etc.) ,
 but the GUI as implemented does not consume any such events. It doesn’t plot charts from
 streaming data, nor does it update the 3D scene from an external state – it uses its internally
 calculated positions and power values. Therefore, the full real-time coupling between frontend
 and backend is not yet achieved. The GUI’s responsiveness is good (since it’s self-contained), but it
 essentially bypasses the backend simulation rather than leveraging it. This is a clear area where
 integration falls short of the technical specification, which envisioned a tight loop of backend
 computations feeding frontend visualizations in real time .
 56
 • 
57
 54
 55
 Control Module Logic: The simulation architecture includes a control logic module to handle valve
 actuation, compressor control, and clutch engagement, potentially even an RL agent input .
 In the GUI, there is no explicit representation of control logic. The process of opening valves at
 the right time or controlling the generator torque is not directly visualized. Some aspects of control
 are implicitly embedded in the scenario animations – e.g., the fact that floaters seamlessly switch
 from filled with air to filled with water at top and bottom suggests an underlying control sequence
 (valves opening at the correct moments), and the H3 pulses imply a clutch timing. But these are
 scripted outcomes rather than interactive controls or sensors. The user cannot, for instance, delay a
 valve opening or see a float “waiting” at the bottom if timing is off – every floater cycles perfectly in
 the GUI. Essentially, the GUI assumes an ideal control logic and does not allow experimentation with
 it. It neither displays any sensor signals nor provides toggles for actuators (except the broad
 58
 59
 6
scenario toggles). By comparison, the backend design allows for different control strategies to be
 tested and even an AI control mode. None of that is accessible via the current interface. Alignment
 here is minimal: the GUI doesn’t misrepresent control logic (it simply doesn’t show it), but it also
 doesn’t reflect the complexity that the simulation’s control module would handle. The “Control Unit”
 in the blueprint also mentioned user-driven scenario selection as one of its tasks , and that part is
 handled by the GUI (the scenario buttons effectively load different control configurations: e.g. H1 on/
 off). But beyond selecting the scenario at start, the user has no further control logic interaction
 during the run.
 59
 • 
60
 61
 Real-Time Telemetry & Charts: According to the technical specifications, the front-end was
 supposed to include live charts for various metrics (torque, power, efficiency over time) and possibly
 a way to log or export data . In the implemented GUI, the only telemetry shown live is the
 power gauge. There are no Chart.js graphs plotting time-series of torque or efficiency. This is a
 notable deviation from the plan to have “one chart per metric” updating in real-time .
 Additionally, there are no controls to start/stop logging or to download a CSV of the run, even
 though the backend concept included a data logger and an export route . It appears these
 features are not integrated yet. The GUI does have Chart.js included on a different page
 62
 63
 53
 64
 65
 (test.html) for static analytical charts (comparing claims vs reality in a narrative) , but not
 in the simulator interface itself. Thus, the alignment of the GUI with the intended monitoring
 capabilities is weak – the user cannot observe how torque varies through the cycle, how efficiency
 might improve with enhancements, or any per-floater telemetry. Only a single aggregate value
 (power) is shown, and even that is not plotted over time, just instantaneously displayed (the gauge
 updates but doesn’t keep history). 
In summary, each major GUI feature has a corresponding concept in the simulation backend, but many are
 implemented in the front-end in a simplified or hard-coded way rather than being dynamically linked to
 the simulator calculations. The table below summarizes the alignment:
 • 
• 
• 
• 
• 
• 
• 
• 
Mode Toggles (Conventional, H1, H2, H3, Integrated): Correspondence: Yes, these map to enabling/
 disabling features in the sim. Integration: Partial – they switch front-end mode and would
 conceptually set backend parameters, but currently do not send any data to backend (the backend
 would need to know which features are on to simulate them).
 Floaters & Mechanics Visualization: Correspondence: Yes, shows the physical system (floaters,
 chain, sprockets, flywheel) the sim models. Integration: Front-end computes motion internally; not
 fed by backend physics in real-time.
 Power Gauge: Correspondence: Yes, displays net power output, key result of sim. Integration: Not live
 data – uses predefined values per scenario; not linked to actual compute_power from engine.
 H1 Visual Effect: Correspondence: Models reduced drag in sim. Integration: Cosmetic only – doesn’t
 reflect a real variable or accept input for nanobubble %.
 H2 Visual Effect: Correspondence: Models buoyancy boost in sim. Integration: Scripted pulses – not
 driven by actual thermodynamic calc or adjustable.
 H3 Visual Effect: Correspondence: Models flywheel & clutch in sim. Integration: Predefined behavior 
not dynamically simulating inertia or controlled by backend logic.
 Controls for Params: Correspondence: (Planned: e.g. sliders for float count, etc.) Integration: Missing– no such controls in UI yet.
 Live Charts (torque, etc.): Correspondence: (Planned in design) Integration: Missing – not
 implemented in GUI.
 7
• 
Data Streaming/Sync: Correspondence: (Planned SSE feed) Integration: Not implemented – GUI runs
 in isolation, no SSE usage.
 Next, we discuss to what extent the “full-featured” UI described in the design documents has been realized
 and highlight which features are fully implemented, partially implemented, or missing.
 Comparison to Design Goals and Implementation
 Status
 The current GUI implementation falls somewhere between a prototype and a fully integrated simulation
 dashboard. The design blueprints (Simulator Implementation Guide, Technical Specification, Stage 1/2
 Guides) outlined a comprehensive web-based UI with real-time interaction and feedback, including
 streaming data and user-adjustable parameters. We compare those goals with the actual state of the 
kpp
calc GUI:
 • 
53
 Planned: Live-Updating Charts for Key Metrics. Status: Not implemented. The technical spec
 expected multiple Chart.js line charts (e.g. showing torque vs. time, power vs. time, efficiency vs.
 time) updating as the simulation runs . In the repository’s GUI, no such charts appear – the only
 dynamic metric display is the power gauge. There is also no chart of floater positions or velocities.
 This is a significant gap, as it means the user cannot visually confirm how metrics evolve during a
 cycle beyond the single number. Implementing these charts would require hooking into the
 simulation loop data stream (or the front-end’s own loop data), which as noted hasn’t been done yet.
 • 
Planned: User Controls for Simulation Parameters. Status: Missing in GUI. The design called for
 input controls (sliders, numeric fields) for parameters like number of floaters, floater volume, drag
 coefficient, water depth, perhaps nanobubble fraction or water temperature, etc., with JavaScript
 sending updates to the backend so the simulation can adjust on the fly . None of these
 controls are present in the current interface. The GUI has no form inputs except the preset mode
 buttons. For example, a slider for “Nanobubble injection rate” or a checkbox for “Enable H2” would
 be expected from the spec, but instead the user has only fixed scenario choices. This indicates the UI
 is not yet an experimental platform where one can vary parameters and immediately see results 
it’s more of a fixed demo. The absence of a 
68
 66
 67
 /set_params fetch usage in the code confirms that
 interactive parameter adjustment isn’t wired in . To reach the intended functionality, this is a
 critical area to develop.
 69
 • 
Planned: Integration via Flask SSE (Simulation Driven Updates). Status: Not integrated. As
 discussed, the front-end is not connected to the Flask server’s streaming endpoint. The Stage 1
 guide introduced a streaming approach (Server-Sent Events) to push simulation data incrementally
 70
 71
 . Stage 2 solidified this by describing an EventSource on the client listening to 
61
 /stream for
 JSON messages . In the current repository, we do not see any usage of 
EventSource or similar– indicating that the front-end page is likely running standalone, or the integration work is
 incomplete. Possibly, the development is being done in phases and the visual aspects were tackled
 f
 irst, with backend coupling to follow. At this stage, the “full-featured UI” is not fully integrated
 with the simulation backend: it does not consume live simulation data, nor influence the
 8
simulation through interactive input beyond initial mode selection. Essentially, the simulation and
 GUI are running in parallel rather than as a single cohesive system.
 • 
• 
57
 Planned: Display of Real-Time Telemetry and Logging. Status: Partially met. The UI does show
 real-time telemetry, but in a very limited form (just the power reading). The system blueprints
 emphasized logging all relevant data and possibly showing telemetry for each floater or subsystem
 . For example, one might expect a table or readouts of current RPM, current torque, efficiency
 percentage, etc., or at least the ability to download the log after a run. The current GUI doesn’t show
 detailed telemetry nor provide a log export. It’s possible that some logging happens in the backend
 (if the simulation is running in Flask, it might collect data), but since the UI isn’t displaying it or
 providing a download, that functionality is effectively hidden or unused at the moment. This means
 the goal of using the simulator for analysis (not just visualization) is not fully met yet. The focus so
 far seems heavier on visualization (the 3D model and animations) than on quantitative analysis
 tools.
 Planned: Alignment with Simulator Architecture (One-to-One Feature Mapping). Status: In
 progress. Many elements of the UI correspond by name to items in the architecture (H1, H2, H3,
 f
 loaters, generator, etc.), showing that the developer has kept the design goals in mind. The
 presence of these features at all is a positive – it indicates the eventual intent to map them to real
 calculations. For instance, the inclusion of a flywheel in the 3D scene and an “Integrated Cycle” mode
 reflects the system blueprint’s vision of testing combined enhancements . However, because
 some are placeholders, the mapping is not functional yet. The control flow in the actual simulator
 (sensors triggering actions) has no visibility in the UI, which we noted. On the other hand, the time
stepping concept is mirrored by the continuous animation. The modular approach (separating
 base cycle vs. each hypothesis) is actually nicely represented by the scenario buttons – one can
 isolate each hypothesis’s effect, much like modular toggles. So the GUI’s structure does align with
 the system design on a conceptual level (e.g., try H1 alone, H2 alone, etc., akin to enabling/disabling
 modules). The shortfall is turning those conceptual toggles into actual simulation configurations and
 reflecting real outcomes. We can say the GUI implements the interface layer described in the
 blueprints, but without the full backend connection, it operates as a mock or stub. This is not
 unexpected in an early implementation: often the frontend is built with dummy data first, then
 hooked to real data.
 45
 72
 To clearly enumerate which features are fully realized versus which are partial or missing, we break them
 down below:
 1
 Fully Implemented & Working Features: - Mode Selection Buttons: All five scenario buttons function in the
 UI to start/stop the respective animations . Visually and interactively, this feature is complete – the user
 can switch modes, and the UI responds as designed. It’s integrated in the sense of front-end behavior,
 though not yet tied to backend computation. - 3D Mechanical Simulation (Animation): The real-time 3D
 graphics of the KPP (floaters looping on chain, turning sprockets, etc.) are fully implemented. The scene
 contains the major mechanical parts (tank, floaters, sprockets, drive shaft, flywheel, generator) and runs
 smoothly. The visual differentiation (colors for different components, fog for depth, etc.) is done .
 This fulfills the goal of an immersive visualization of the KPP’s mechanism. - Power Gauge Display: The power
 meter with dynamic color and bar feedback is implemented and updates every frame . It correctly
 shows negative vs positive and changes in magnitude in sync with the animation. As a UI element, it’s
 working as intended, providing an immediate sense of system output. - Hypothesis Visual Indicators: Each
 73
 18
 13
 74
 9
enhancement’s visual effect (nanobubble water for H1, red “kick” floaters for H2, spinning flywheel for H3) is
 implemented in the GUI’s animation logic. These run automatically in the appropriate modes, giving visual
 affirmation that the mode is active. They are not placeholders – they actively change the animation. 
Scenario Descriptions: The info-panel text for each scenario populates as expected , providing context.
 This content likely came from system documentation or was written to match it, and it’s fully integrated into
 the UI flow.
 75
 11
 Partially Implemented or Non-Functional Backing: - Backend-Driven Simulation Data: The loop exists on
 the frontend, but presently it’s not consuming backend data. If the Flask simulation engine is running, the
 UI doesn’t reflect its live outputs. So we have a partial implementation of the “simulation loop connection”.
 The structure for showing results exists (e.g. the power gauge could show real power), but the wiring
 (EventSource and JSON handling) is absent. In other words, the UI is ready to display streaming data but is
 using internally generated data instead. - Physics Accuracy of Animations: The motions and values in the GUI
 are only an approximation of real physics. For example, floaters in reality might accelerate from rest at the
 bottom; in the UI they move at constant loop speed (except H1 slightly faster descending branch). The
 timing of H2 kicks is arbitrary. This is a partial implementation – the physics engine calculations are not
 actually driving the animation. We consider this partial because the framework is there (the code has
 places where forces could be injected), but currently uses a simplified model. - H1/H2/H3 Functional
 Integration: While the UI shows these modes, the actual functional logic behind them is only partly there.
 H1 mode likely sets some flag in the engine to reduce drag, H2 might set a parameter for extra buoyancy,
 and H3 might enable a flywheel model. We need to verify if those exist in the engine code (which we don’t
 see here), but assuming they do, the UI does not control their magnitude or reflect nuanced outcomes – it
 just toggles an on/off state. For example, H1 could have a spectrum (0% to 100% nanobubble infusion); the
 UI only has “off” vs “on (some fixed effect)”. Similarly, H3 could have different flywheel sizes or clutch timings– not adjustable here. Thus the UI implements the presence of these features but not the depth. - Scenarios
 vs. Combined Toggles: The UI provides only the predefined scenarios. If a user wanted to test, say, H1 and H2
 together without H3 (a partial combination), there is no mode for that specifically. They have to run
 integrated (which includes H3 as well) or run individually. This is a design choice, but it suggests partial
 implementation of scenario flexibility. The backend likely could accept any combination of H1/H2/H3 flags.
 The front-end just hasn’t exposed all combinations (except “all on”). This is a minor gap, but noteworthy for
 completeness. - UI Responsiveness to Backend Changes: If the simulation backend were modified (for
 example, a new parameter or an altered physical model), the current UI would not automatically
 accommodate it due to lack of dynamic linking. This is a general partial integration concern. For instance, if
 the backend added a new hypothesis H4, the GUI has no provision to incorporate that without code
 changes. The current setup is somewhat hard-coded for H1–H3.
 Missing or Not Yet Implemented Features: - Real-Time Charts: As mentioned, no live plotting of time-series
 data is present, despite being a key goal. The user cannot observe the evolution of metrics over simulation
 time in a chart form. - Parameter Adjustment Controls: No sliders or input boxes exist for adjusting the
 simulation input parameters (e.g. float count, floater mass, water density, compressor power limit, etc.). All
 those remain fixed in the code or backend. The absence of a configuration form means the “simulator”
 aspect is limited – one cannot perform sensitivity analysis or try custom values through the UI. - Detailed
 Telemetry/Indicators: Apart from power, other potentially useful outputs are missing on the interface. For
 example, RPM of the generator/flywheel, torque on the shaft, system efficiency, air consumption rate,
 etc., are not shown. The blueprints envisioned logging many of these for analysis . A full-featured
 dashboard might have gauges or readouts for several of these. Currently, the user is left to infer some of
 these from the animation (e.g., flywheel speed by looking at it, floater speed by animation) but no numeric
 57
 10
values. - Compressor Control & Status: There is no explicit representation of the compressor’s status (running/
 stopped) or any control to turn off air injection (to, say, simulate failure or test freewheel). Also missing is
 any indicator of energy spent on compression vs energy generated – which would be crucial to
 understanding net power. - Start/Stop/Pause Simulation: The UI does not provide a pause or step-through
 functionality. It assumes continuous running once a mode is started, until the user possibly hits reset or
 switches mode. A robust simulator UI might allow pausing the simulation or advancing one time-step at a
 time for inspection. That’s not present. - Data Export: No button or link to download the simulation data
 (time series) as a CSV or similar. Stage 2 plans mentioned a 
62
 /download_csv route for logged data , but
 the front-end has no exposure of that. So users cannot easily take the results to analyze offline or verify
 conservation of energy, etc. - Error/Boundary Handling: Not visible in UI is any messaging for edge cases 
e.g., if the simulation becomes unstable or if a parameter is out of range. The current GUI presumably
 doesn’t encounter those because it’s on rails, but a finished product would need to handle such scenarios
 (which could involve showing warnings or disabling incompatible toggles). This falls outside the happy path
 currently implemented.
 Considering these points, it’s evident that while the GUI achieves a compelling demonstration of the KPP
 concepts, it is not yet the fully interactive research tool described in the documents. Many planned
 features are either only partially realized or not present at all. The system architecture as designed is only
 superficially mirrored by the GUI at this stage.
 Recommendations for Full Integration
 To transform the current GUI into a fully integrated simulation interface, the following steps are
 recommended:
 1. Connect the GUI to the Simulation Backend via Streaming Data: The highest priority is to hook up the
 front-end to live simulation outputs. Implement the Flask server’s SSE 
/stream endpoint as outlined (if
 not already done), and in the GUI use a JavaScript 
61
 EventSource to receive data frames . Upon each
 message, update the UI elements based on the actual data. For example, instead of using a hardcoded
 finalPower = 523 kW for integrated mode, let the backend compute power in each time-step and
 stream it. The GUI’s power gauge should then display the streamed 
55
 power value . Similarly, floaters’
 positions could be streamed (though that’s a lot of data per frame; an alternative is to compute positions
 front-end but validate against backend in aggregate). At minimum, ensure that the gauge and any added
 charts reflect the simulation’s true behavior. This will turn the GUI from a mock-up into a real monitoring
 dashboard. Make sure to handle the stream in a non-blocking way so the Three.js animation can still run 
for instance, use the stream data to update chart datasets and perhaps periodically reconcile the animation
 state (or drive the animation entirely from data if desired). The latency of SSE (tens of ms) is usually fine for
 chart updates (10 Hz update is often enough for perception ). For the 3D animation, if extremely precise
 sync is needed, a different approach might be required, but a reasonable strategy is to use the backend’s
 positions if available at maybe 10–20 Hz updates, and interpolate smoothly in between on the front-end.
 76
 2. Implement Live Charts for Key Metrics: Leverage Chart.js (already included in the project) to create
 real-time line charts of metrics like torque, power, efficiency, maybe floater count or pump pressure. The
 Stage 2 guide even suggests how to push data into Chart.js datasets and call 
77
 chart.update() on each
 new data event . Start with two charts that were central to earlier analysis: one for Power vs. Time and
 one for Net Torque vs. Time (or perhaps efficiency). Use distinct colors for different runs or indicate which
 11
scenario is active on the chart. This will allow users to visualize performance over a cycle. For example, the
 power chart in H2 mode would show the pulsating power curve, verifying the effect, and in H3 mode it
 would show a flatter line – a direct, quantitative validation of the flywheel’s smoothing effect. The charts
 should update continuously as data streams in. Additionally, consider a static plot of one full cycle once it’s
 completed (if cycles are identifiable), to easily compare the cycle shape between modes. If performance is a
 concern, the data could be throttled (only plot every nth point) or the simulation can be run for a fixed
 duration and then paused for review.
 3. Add User-Tunable Parameter Controls: Introduce input widgets that allow the user to modify
 simulation parameters on the fly. HTML range sliders or number inputs can be added for the most
 impactful parameters. Examples: - Floaters Count or Mass: Slider to adjust how many floaters (or their
 weight/volume). The backend would use this in calculations of buoyancy and inertia. - Drag Coefficient: A
 slider or dropdown to simulate different drag scenarios (this indirectly could represent nanobubble efficacy
 beyond on/off). - Nanobubble % (H1 intensity): If the model supports a variable fraction, let user set a
 percentage. The backend can linearly scale water density as per that fraction . The GUI could even reflect
 it by making the waterH1 material more or less opaque to indicate concentration. - Thermal ΔT or H2
 Boost Level: Provide a control for how strong the thermal assist is (e.g., temperature difference or
 expansion ratio). The physics engine can translate this to a buoyancy multiplier. The UI might link it to the
 magnitude of the “kick” (e.g. how red it flashes or how much power spike). - Flywheel Inertia (H3
 smoothing): A slider for flywheel size – larger inertia would mean slower acceleration but steadier output.
 The simulation can incorporate this into its equations; the UI might reflect it by adjusting how rapidly the
 f
 lywheel model spins up or the difference between coast and engaged speeds. - Compressor Power or
 Efficiency: An important parameter could be how much power the compressor consumes or how efficient it
 is. A slider could alter this, immediately affecting net power. The user could see on the gauge how
 increasing compressor load eventually makes net power negative, for instance. These controls should use
 20
 JavaScript fetch/AJAX to call a Flask route (e.g. 
78
 /set_params ) sending the new value . The backend
 should update the simulation’s parameters in real-time (the Stage 2 guide details using these updates on
 next loop iteration). The UI should also update any displayed parameter labels if shown. Including these
 controls turns the GUI into a true simulator interface, letting users explore “what if” scenarios rather than
 just watching predefined ones.
 4. Expand Feedback and Telemetry in the UI: Besides charts, consider adding numeric readouts or small
 gauges for other outputs: - Current RPM of Generator: This would come from the simulation’s state
 (related to floater speed and gearbox ratio). It helps users correlate what they see (floater speed, flywheel
 spin) with actual numbers. - Torque on Drive Shaft: Display the instantaneous torque or an average torque.
 This is useful to understand mechanical load and could tie into when clutch engages (torque might drop to
 zero when disengaged). - Efficiency: If the simulation computes efficiency (ratio of output energy to input
 energy), show this as a percentage live. It’s a key metric to judge the value of enhancements. - Compressor
 Air Flow or Pressure: If available, show the air injection rate or pressure in the compressor line during
 operation. This would illustrate H2’s concept (isothermal vs isentropic behavior could be inferred). - Energy
 Metrics: Perhaps a cumulative energy generated vs consumed, or net energy of a cycle. This could simply
 be displayed at end of a run. If adding too many numbers at once clutters the UI, consider a collapsible
 sidebar or a tabbed info panel that the user can toggle to see detailed stats. The current minimalist design
 is nice for visualization, so these could be optional or appear on pause.
 5. Incorporate Control Logic Visualization: This is more advanced, but to truly align with the full simulator,
 the UI could depict some of the control processes. A few ideas: - Visually indicate when valves open or
 12
close. For example, a small icon or color change at the bottom and top of the tank when air injection or
 venting happens. In the simulation, that would be event-driven; the GUI can listen for an event (or deduce
 from floater state) and animate a valve icon. - Show the clutch state in H3 mode – perhaps a light that
 turns on when the generator is engaged vs off when freewheel. This could correspond to torque being
 transmitted or not. If the simulation outputs a boolean or mode for clutch, use that. - Indicate compressor
 on/off or load level – e.g., an icon of a compressor that lights up proportional to power draw, or even a
 simple text “Compressor: ON (50 kW)” vs “OFF”. - Sensors feedback: If the control logic uses sensors (like
 f
 loat at top sensor), the UI might not explicitly show sensors, but could highlight a floater when a sensor is
 triggered, to illustrate feedback loops. These additions would make the simulation less of a black box. They
 help the user see that behind the smooth motion there are timed events being controlled. It also serves
 educational purposes – understanding that the KPP requires coordination (not just passive physics).
 21
 6. Ensure Backend Physics Covers All Shown Features: Parallel to improving the GUI, the backend
 simulation code must robustly implement what the GUI is portraying. This means verifying that: - The
 buoyancy and drag model is in place for normal operation. - H1’s effect is actually applied in calculations
 (reducing drag force or effective water density) when H1 is enabled . - H2’s effect is implemented
 (perhaps as an added force or reduced required compressor energy due to thermal input). This could be
 tricky, but even a simplified model (like a percentage increase in buoyant force for the first part of ascent)
 would do. The key is that the engine should output higher power with H2 on, matching what the GUI
 indicates. - H3’s mechanism is modeled: introduce a flywheel inertia and simulate the clutch. Possibly use a
 boolean or timer in the simulation to engage/disengage based on an optimal strategy (e.g., disengage
 when floaters are at top/bottom to let them coast, re-engage to extract power at optimal times). The sim
 should then output a smoother power curve. The GUI’s current preset can be replaced by the sim’s actual
 power vs time, which hopefully will be similar if H3 works. Also output the flywheel speed if possible – and
 use it in the GUI for the spin animation instead of fixed speeds. If any of these are not yet implemented in
 the engine, prioritize adding them, because once the GUI is connected to real data, any missing physics will
 show up as a discrepancy (e.g., if H2 isn’t coded, the power might not actually spike, and the GUI would
 need to stop faking it and instead reflect reality).
 7. Introduce Pause/Reset and Simulation Length Control: Provide the user some control over the
 simulation timeline. Currently, the simulation runs indefinitely in a loop. It might be useful to allow running
 the sim for a specified duration (say one full cycle or a user-set time) and then auto-pausing. A “Pause”
 button could freeze the simulation (stop advancing time on backend and suspend front-end animation) 
useful for examining numbers or switching view orientation. A “Resume” would continue. The existing reset
 already brings it to initial state; that’s fine for restarting. Also, if the simulation supports stepping, a “Step”
 button to advance one increment could help with detailed analysis, though that is a bonus feature. Ensuring
 that the GUI and simulation can start, stop, and restart cleanly (no accumulation of old data or multiple
 overlapping streams) will be important once connected. This may involve managing the SSE connection
 (closing it on pause, reopening on resume or new run) and resetting backend state appropriately.
 8. Enhance the User Experience with Guidance and Output Clarity: As features grow, consider the user
 interface layout and clarity: - Group controls and indicators logically (e.g., all input sliders together in a
 controls section, and all outputs together in a results section on screen). The current design puts controls
 on the left panel and the power gauge on the right, which is fine. New charts might go below or above the
 3D view, or in a modal. Maintain a clean look with Tailwind styling as used. - Add tooltips or brief
 descriptions for new sliders so users know what they do (especially for technical parameters). - Possibly
 allow the legend (color explanation) that was in earlier static HMI to be accessible, so users unfamiliar with
 13
the colors can check what green vs blue vs red floater means. This could be a small info icon that toggles a
 legend. - If the simulator might run in slow motion or real-time, consider a speed slider for the front-end
 animation (just to speed up or slow down the visualization relative to real time, without affecting calc). This
 helps when analyzing a slow process or speeding through a long simulation. - Test the interface for
 different scenarios to ensure stability. For example, if a user cranks nanobubble fraction to maximum and
 thermal to max, does the backend handle it and does the UI still show sane outputs (or do floaters fly off
 screen)? Some limits or clamping might be needed and corresponding UI validation.
 By implementing the above recommendations, the KPP simulator GUI will evolve into the rich, fully
integrated interface envisioned in the project documentation. It will allow users not only to watch the KPP
 operate under various hypothetical improvements, but also to directly see the numerical outcomes and
 adjust parameters to ask “what if” questions. Essentially, these changes will align the GUI’s interactive
 capabilities with the simulation’s full analytical power, marrying the immersive 3D visualization with robust
 engineering data and control. This will greatly enhance both the demonstration value and the research
 utility of the KPP simulation platform, turning it from a conceptual showcase into a practical experimental
 and educational tool.
 Sources:
 KPP Simulator GUI Implementation (HTML/JS from Tonihabeeb/kpp-calc repo)
 Stage 2 Real-Time Simulation Upgrade – Technical Guide (Design specs for frontend/backend
 integration)
 KPP R&D Simulator Algorithm Blueprint (System architecture for H1, H2, H3 and control logic)
 Stage 1 Simulation Loop Upgrade Guide (Initial streaming simulation approach in Flask)
 GUI source code for scenario behaviors and visuals (H1/H2/H3 mode logic in JavaScript)
 Earlier prototype notes and HMI markup for KPP (for conceptual consistency of features)
 simulation 3d.html
 file://file-CexdUHw7U4aRDqQPUWiPWg
 Kinetic Power Plant (KPP) R&D Simulator Algorithm Blueprint.pdf
 file://file-DEKb2MeVDubPyHbxBzQBuC
 one unit HMI.html
 file://file-BcZ8CLpuuxVf2HnL9S2xXE
 Stage 2 Upgrade_ Real
Time Simulation Implementation Guide.pdf
 file://file-UVKDQgJCEP8LPwraen4Q7s
 Stage 1 Implementation Guide_ Real-Time Simulation Loop Upgrade.pdf
 file://file-GpMuyKuXh2AZkbDqvhrgVu
 test.html
 file://file-FEwDKshSzxnqvGCt8SSib2
 • 1 13
 • 
53 66
 • 29 79
 • 48 70
 • 38 26
 • 80 8
 1 2 4 5 7 9 10 11 12 13 14 15 16 17 18 19 22 23 24 26 27 28 35 38 39 40 43 44 45 46
 47 51 72 73 74 75
 3 29 30 31 57 58 59 79
 6 8 34 41 42 50 80
 20 21 25 32 33 36 37 52 53 54 55 56 60 61 62 63 66 67 68 69 76 77 78
 48 49 70 71
 64 65
 14