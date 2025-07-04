Deep Technical Description of the 500 kW Kinetic
Power Plant (KPP) Technology
System Overview
The Kinetic Power Plant (KPP) is an innovative energy system that produces continuous electric power by
harnessing buoyancy and gravity in a closed-loop, pneumatic-mechanical process . In essence, it is a
self-contained power plant module (nominally 500 kW per module) that uses water-filled shafts, multiple
buoyant floats, compressed air, and a generator to convert the mechanical work of rising and falling
floats into electricity. Each KPP module operates 24/7 without traditional fuel or weather dependence,
producing emission-free base-load power . The technology was developed by Rosch Innovations AG
(marketed via Save The Planet AG and partners like Ki-Tech Global) as a scalable solution for clean energy –
modules can be combined for multi-megawatt installations (e.g. 1 MW, 5 MW, up to 100 MW plants) with
built-in redundancy for reliability .
At its core, a KPP module is a 25 m deep vertical shaft (typically a cylindrical water-filled well) containing an
endless conveyor belt of hollow buoyant containers (“floats”) that continuously cycle up and down .
As floats rise on one side and descend on the other, they drive a gear and generator assembly at the top,
delivering electrical power. A programmable logic controller (PLC), air compressor, and valve system
manage the injection and release of compressed air in each float, ensuring the system runs in a stable selfsustaining
loop . The following sections will delve into the physics principles, component
interactions, and control mechanisms in detail, focusing on the 500 kW KPP module and how multiple
modules can be synchronized in larger plants.
Physics Principles: Buoyancy and Gravity in Energy Conversion
The KPP exploits fundamental physics principles – chiefly Archimedes’ principle of buoyancy – to create a
continuous mechanical rotation from the opposing forces of buoyancy and gravity . Each float (a
hollow container) can be filled with either water or air. When filled with air, the float becomes substantially
buoyant, experiencing an upward force equal to the weight of the displaced water (Archimedes’ law). When
filled with water (or when the air is removed), the float loses buoyancy (essentially becoming neutrally
buoyant aside from its own weight), causing it to descend under gravity.
In the KPP design, the floats on the ascending side of the conveyor are injected with compressed air,
displacing water and making them buoyant. This creates a strong upward thrust force on each float, which
in aggregate drives the conveyor belt upwards on that side . Meanwhile, on the descending side,
floats have had their air removed (refilled with water) at the top, so they are heavier (less buoyant) and fall
downward. The weight of the water-filled floats plus gravity assists this downward motion. Thus, the system
is akin to an “overbalanced” wheel: one side of the loop is buoyant and going up, the other side is heavier
and going down. The net torque from this imbalance continuously turns the conveyor and the attached
drive shaft .
1 2
3 4
5 6
7
8 9
1 4
10 8
8 11
1
Archimedes’ Principle: The buoyant force on a float is F_b = ρ_water * V_displaced * g , where
ρ_water is water density and V_displaced is the volume of water displaced. For a large float, this force can
be substantial. The KPP harnesses this force by allowing controlled volumes of air into the floats at depth,
causing them to displace water. Each 500 kW module is engineered such that the total buoyant uplift on the
ascending floats exceeds the downward force on the descending side (accounting for the weight of floats
and any resistance), thereby providing a net driving force to rotate the system’s shaft and generator
.
Gravity and Potential Energy: As floats rise, they effectively convert the potential energy imparted by the
compressed air (which pushed out the water) into kinetic energy of motion. At the top, when the air is
released and water refills the float, the float regains weight and potential energy (relative to the bottom)
which will be given up on the way down. This interplay of buoyancy and gravity repeats continuously. In an
ideal lossless system, the energy required to inject air at the bottom (against water pressure) would equal
the energy extracted by the rising float. However, the KPP introduces several innovations (described later) to
enhance efficiency and yield surplus energy output . Essentially, the system leverages the pressure
difference between the bottom and top of the water column: injecting air at depth does work on the water,
and the buoyant ascent of that air (inside floats) performs work on the drivetrain. By carefully managing
this cycle, the KPP converts a portion of that work into electrical energy while the system self-loops.
It should be noted that the KPP’s operation involves complex thermodynamics and fluid dynamics.
Compressed air expands as it rises (doing work on the water), and water being displaced or re-entering
floats has inertia and drag. The design must account for these to maintain continuous rotation. In practice,
the system’s control strategy and physical enhancements allow it to overcome losses and produce net
power, as discussed in later sections.
Mechanical Design and Components
Each 500 kW KPP module consists of a set of integrated mechanical components working in concert:
Water Tank / Shaft: A vertical cylindrical shaft ~25 m tall (often installed partially underground)
filled with water serves as the medium for buoyancy . The shaft’s diameter is on the order of a
few meters (≈2 m in demo plants ) to accommodate the floats and the conveyor framework. The
shaft must be robust and waterproof; typically it’s a steel-reinforced structure or borehole lined with
metal or concrete to contain the water column. At the very top of the shaft, there is a headspace or
mechanism for floats to transition around the conveyor loop; likewise at the bottom there is a curved
path or sprocket mechanism.
Floats (Buoyant Chambers): These are hollow containers (cylinders) attached at regular intervals
to the conveyor belt/chain system . They are usually made of durable lightweight material
(e.g. plastic or composite) to withstand water pressure and repeated cycling. Each float has an
internal valve assembly that connects to an external compressed air feed when it reaches the
bottom of the loop. When the float is at the very bottom of the shaft, this valve aligns with a fixed air
injection nozzle or pipe leading from the compressor . At the top of the shaft, each float has
another valve or opening that releases the air and allows water to re-enter. The floats are designed
to automatically open/close these valves at the correct positions (often using mechanical linkages or
triggers in sync with the conveyor’s motion) . In effect, at the bottom position, a float’s valve
1
12
13 14
•
15
15
•
16 7
17
17
2
opens to receive air; at the top position, a valve opens to vent the air and let water in, resetting the
float for the downward journey.
Conveyor Belt and Guiding System: The floats are mounted or connected to a continuous looped
conveyor system – this can be a chain drive or belt drive with sprockets at the top and bottom of
the shaft . The conveyor holds the floats in a fixed orientation and guides their path from bottom
to top on one side and top to bottom on the other, forming a closed loop (often called a paternoster
mechanism in design ). The top sprocket (or wheel) of the conveyor is a critical element: it is
coupled to the main drive shaft. As the floats move, they turn this sprocket; the mechanical rotation
is transmitted through a gearbox (speed increaser) to the electrical generator. The conveyor and
sprockets are built to handle the large forces involved (tension from floats, buoyant lift, weight on
the other side) – often using steel chains and gears. Guide rails or tracks inside the shaft ensure the
floats move smoothly and do not swing or jam. The entire assembly has to be low-friction and robust
to minimize mechanical losses and wear during continuous operation.
Air Compressor and Pressure Vessel: At the heart of the pneumatic subsystem is a high-pressure
air compressor (typically multi-phase electric compressor). For a 500 kW module, a compressor on
the order of a few kilowatts power input is used to provide the compressed air supply (e.g. ~4–5 kW
compressor was used in a 15 kW prototype, and larger modules would use proportionally sized
compressors) . The compressor draws in ambient air and pressurizes it to a level sufficient to
overcome the water pressure at the bottom of the shaft. For a ~25 m water depth, this means the air
injection pressure must be ~3–4 bar above atmospheric pressure (approximately 4–5 bar absolute).
The compressed air is stored in a pressure reservoir (tank) to provide a buffer and smooth supply
. The reservoir is connected to injection piping that runs to the bottom of the shaft. Electricallyactuated
pneumatic valves (solenoid or motorized valves) controlled by the PLC regulate the flow
of compressed air from the reservoir into each float when it docks at the bottom . After injection,
the valve closes and the float begins its ascent filled with air. The compressor typically runs
intermittently or as needed to maintain the reservoir pressure, and it represents the primary energy
input to the system.
Electric Generator and Gearbox: Each 500 kW module has an associated electric generator
mounted (usually) at the top of the shaft, driven by the main shaft of the conveyor via a gear
multiplier . Because the floats move relatively slowly (constrained by water drag and the need
for controlled ascent speed), the raw rotational speed of the conveyor sprocket is fairly low. A
gearbox (or belt drive with appropriate ratio) multiplies this rotation speed to match the operational
speed of the generator. The generator itself is a three-phase AC generator, often a permanentmagnet
synchronous generator using high-strength neodymium magnets for high efficiency .
Rosch claims to use a proprietary generator design with minimal losses – essentially “nextgeneration”
generators that can approach near 100% efficiency by using advanced magnetic
materials and optimized windings . In practice, this means the generator can produce grid-quality
AC power (e.g. 380 V three-phase, 50 Hz in European spec) when spun at the correct speed .
The generator also inherently provides a load torque (braking) on the mechanical system when
producing power; this resistance is crucial for controlling the ascent speed of the floats (too little
load and the system would accelerate, too much and it would stall). Thus, the generator’s load is an
integral part of system control, acting as a brake to regulate the conveyor’s motion .
•
7
11
•
13
8
8
•
18
19
19
20 21
22 12
3
Control Cabinet and Instrumentation: The entire KPP module is orchestrated by a control system
(typically a PLC-based cabinet) . This includes sensors and controllers for various parameters:
pressure sensors in the air tank, position or timing sensors for floats (to know when a float is at
bottom/top), rotational speed sensors on the shaft, and electrical meters on the generator output.
The control cabinet houses the PLC which runs the automation sequence (compressor control,
timing the opening of valves for air injection, switching the generator output, etc.). It also often
includes the power electronics interfaces – for example, contactors or switches to connect the
generator to the load or grid once the system is up to the correct speed and frequency .
Instrumentation such as voltmeters, ammeters, frequency meters and indicators are provided for
the operators to monitor performance . In demonstration setups, resistive loads (e.g. immersion
heaters) have been used to absorb the generated power under controlled conditions , whereas in
a real plant the output would be tied into an electrical grid or load center.
Figure: Internal View of a KPP Module (Shaft and Conveyor System) – This image shows a look down into a
KPP shaft. On the right, the chain conveyor and guide structure are visible (rust-colored sprocket and chain), and
on the left a cylindrical float (orange) is attached to the conveyor. As the chain moves, floats travel upward (filled
with air) on one side and downward (filled with water) on the other side
.
Operational Cycle of the 500 kW KPP Module
A single KPP module operates in a continuous cycle. Below is a step-by-step description of one complete
cycle for a given float, illustrating how the components interact and how energy flows through the system:
Starting Conditions: Initially, the shaft is filled with water and the floats on the conveyor are all
submerged. The system starts with the floats mostly filled with water (no buoyant force driving the
system). The PLC engages the air compressor to pressurize the air reservoir to the required
operating pressure (this can take a few minutes to reach steady-state pressure) . Once pressure is
available, the system is ready to begin rotation.
•
8 9
20
20
23
7
1.
8
4
Air Injection at Bottom: As the conveyor moves (either via a starter motor or manual priming for
the first cycle), a float arrives at the bottom position of the loop. Here, a pneumatic coupling
engages: the PLC opens a valve linking the compressed air feed to the float’s internal valve .
Compressed air rushes into the float’s chamber, forcing water out of the float (usually through a
one-way water outlet at the bottom of the float). This effectively replaces the water inside the float
with air. The injection is very rapid; the float is designed to fill with air in a brief moment when
aligned at the bottom. Once the float is filled (or a preset time/pressure is reached), the PLC closes
the air valve. The float is now positively buoyant – it has substantially less weight than the water it
displaces, yielding a strong upward force .
The air injection process is a key energy input: compressing air to e.g. ~4 bar and injecting the
necessary volume consumes energy. However, the KPP uses a unique air compressor design with a
pressure-exchanger to perform this step very efficiently . The compressor may inject air in
pulses at the optimal part of the cycle rather than continuously, to minimize wasted work . (For
example, “pulsing” the air when the float’s valve is fully open and water displacement is most
effective, then stopping – this avoids excess compression when not needed.) Additionally, as the float
fills, the expulsion of water through the bottom can create a “water jet” effect – the exiting water
jets downward into the tank which, by reaction, provides a small extra upward thrust to the float .
All these techniques improve the net energy balance of injection.
Buoyant Ascent: Once filled with air, the float immediately begins to rise along the upward side of
the shaft, carried by the buoyant force. It pushes upward on the conveyor, contributing to the
clockwise rotation of the entire chain (as seen from the side) . As multiple floats on the
ascending side are filled with air, their combined buoyant forces drive the conveyor and overcome
the weight (and drag) of floats on the opposite side. The mechanical energy from the rising floats is
transmitted through the chain and gears, spinning the top sprocket and the attached generator
shaft. The PLC does not engage the generator’s electrical load until a certain speed is reached (to
avoid overloading the system during start-up) . Typically, the system needs to attain its nominal
rotation speed corresponding to the generator’s target frequency (e.g. 50 Hz). During this ramp-up,
the floats continue to be sequentially filled with air at the bottom as each new float reaches the
bottom position. The KPP design ensures a smooth continuous rotation: as one float moves up, the
next float enters position to be filled with air, maintaining a near-steady torque.
As the float ascends, the water pressure around it decreases (since pressure is higher at 25 m
depth and lower near the top). The air inside the float will expand slightly. The float designs
accommodate this by allowing some water to be expelled on the way up or by having flexible
bladders. By the time the float nears the top, the internal air may have expanded to fill the float
completely, and its pressure drops to near atmospheric. This ensures that when the float reaches the
top, it is filled with low-pressure air, ready to be released without explosive force. The controlled
expansion of air inside effectively does additional work on the water (pushing out more water)
during ascent. The system may harness this via the aforementioned water-jet effect and by
capturing some of the escaping air energy at the top (details on that below).
Air Release at Top: When the float reaches the top of the shaft, it transitions around the top
sprocket from the ascending side to the descending side. At this point, a mechanism triggers the
float’s top valve to open, releasing the air that was inside. The compressed air, now expanded to
near 1 atm, is vented – typically into an upper collection chamber or directly to the atmosphere
2.
8
24 7
3.
4
25
26
4.
24
20
5.
6.
5
above the water. Simultaneously, water is allowed to flood back into the float, re-filling it
completely . Now the float has essentially returned to its heavy state (filled with water). The
release of air at the top is a crucial moment: the KPP employs a pressure exchange strategy here.
Rather than simply wasting the pressurized air, some systems use a pressure recovery – for
instance, channeling the venting air through a turbine or using it to pre-charge another chamber. In
Rosch’s design, they mention a “pressure exchanger” which could imply that the outgoing air’s
energy is partially recovered to assist either the next compression cycle or to generate a bit of power.
(The specifics are proprietary, but conceptually this could work similarly to energy-recovery
ventilators or hydraulic pressure exchangers used in desalination, transferring pressure from one
fluid stream to another to reduce net compressor work.) In any case, after venting, the float is full of
water and ready to start its descent.
Gravitational Descent: Once on the descending side, the now heavy (water-filled) float is pulled
downward by gravity. Importantly, the KPP integrates a method to reduce resistance on the downgoing
side: the introduction of micro-bubbles into the water around the descending floats .
By injecting a stream of tiny air bubbles into the water on the descent side, the effective density of
the water is lowered, which in turn reduces the buoyant force acting upward on those
descending floats (making them “heavier” in context). In other words, micro-bubbles create a
partial cavitation or aeration of the water, so the downward floats encounter less drag and less
residual buoyancy, thus falling faster and exerting more downward pull on the conveyor . These
micro-bubbles might be generated by diverting a small fraction of compressed air or by using the
pulsating compressor output during times floats are not being filled. The result is that the
descending side offers minimal resistance and in fact helps maintain the conveyor rotation, ensuring
that most of the work from the ascending floats goes into spinning the generator rather than lifting
the opposite side. The floats continue down to the bottom, guided by the conveyor. By the time a
float reaches the bottom, it has expelled any residual air and is completely waterlogged (often there
are vent holes to ensure no trapped air remains). It is now back at the starting position.
Cycle Repeats Continuously: As each float in turn reaches the bottom, the PLC opens the air valve
and the cycle repeats for that float . Multiple floats are at various stages: typically, a new float
gets injected with air every few seconds (depending on the number of floats and speed of the belt).
This overlapping sequence creates a continuous rotation and a steady mechanical output. After
initial start-up, the system is designed to run autonomously with the compressor cycling to maintain
pressure and the PLC managing timing. When the target speed and generator frequency are
reached (e.g. generator spinning such that it produces 50 Hz AC), the PLC connects the generator’s
output to the electrical load or grid via a three-phase breaker or synchronizing device . At this
point, the KPP module is fully online, delivering ~500 kW of electrical power while the compressor
and control system consume only a fraction of that (the difference being the net output).
Throughout this process, numerous feedback controls ensure stable operation. For example, if the
generator load increases (drawing more torque), the rotation might slow slightly, which the PLC can detect
and respond to by adjusting the compressor duty cycle or allowing more floats to be filled to increase
torque. Conversely, if the system spins too fast (light load), the PLC might reduce air injection or introduce
an electrical brake until balance is restored. The generator itself, being effectively a brake, is perhaps the
most important stabilizer – it will naturally limit speed by converting excess kinetic energy into electricity.
This “governor” effect means the system finds an equilibrium where the mechanical power from buoyancy
equals the sum of electrical output plus losses. According to reports and tests, that equilibrium yields a
27
7.
28 29
29
8.
24
20
6
i need more details on this part,
surplus of electrical power after covering the compressor’s needs . For instance, one demonstration
showed ~4.2 kW of compressor power enabling a 12 kW generator output on a smaller prototype – a
testament to the efficiency enhancements in the design.
Figure: Prototype KPP Demonstration (Thailand) – This image shows a small-scale KPP setup during
assembly/testing. The orange conveyor with floats can be seen looping over a top support frame. Such prototypes
validate the operating principles: compressed air is injected at the bottom (the green drum at center may simulate
the water tank), floats rise on the right, and the conveyor turns the top pulley connected to a generator. Early tests
reported significantly more output power than input power, demonstrating the KPP’s novel efficiency .
Control Systems and Electronics
The KPP is a mechatronic system requiring active control for safe and optimal performance. The control
architecture centers on a PLC (Programmable Logic Controller), which is industrially robust and capable of
real-time control logic. The PLC is programmed with the sequence logic and PID controllers necessary for
the following functions:
Compressor Control: Maintaining the air supply pressure is crucial. The PLC monitors the air
pressure sensor in the reservoir . When pressure drops below a setpoint (due to floats being
filled), the PLC signals the compressor to run. Once the pressure is back to the desired range, the
compressor can be turned off or idled. This on/off or load/unload control maintains a stable
pressure (for example, ~4 bar) for consistent float filling. The PLC may also adjust compressor output
based on the rate of air usage – for instance, if many floats are being filled quickly (high load
conditions), the compressor might run continuously or at higher capacity.
Valve Timing and Float Coordination: Perhaps the most critical control aspect is timing when to
inject air into each float. The PLC needs to know when a float is correctly positioned at the bottom
injection point. This can be achieved via position sensors or encoders. Common methods include a
rotary encoder on the main shaft (to track conveyor position) or proximity sensors/limit switches that
detect a particular float or marker on the conveyor. Using these, the PLC knows the exact moment a
13 14
13
30
•
8
•
7
float’s valve aligns with the air feed pipe. It then triggers the solenoid valve to open, delivering
compressed air to that float . After a calibrated duration (or when a pressure/flow condition is
met indicating the float is filled), the PLC closes the valve. This sequence repeats for each passing
float. The timing is crucial: too short an injection might under-fill a float (less buoyancy), too long
could waste air. The PLC likely uses a fixed timing based on experiments or a feedback (e.g. a flow
sensor indicating when water is expelled).
Additionally, at the top of the shaft, float valves might be mostly passive (opening automatically when
reaching a cam or stopper). However, some designs might include active control at the top valve as well
(for example, to momentarily hold a float until a certain position or to control the release rate of air to avoid
pressure spikes). The PLC coordinates all these such that only the intended float is filled or vented at any
given time. The result is a smooth, almost continuous handoff of floats being filled and floats being
released in a rhythmic cycle.
Generator and Load Control: The generator in a 500 kW KPP is likely a synchronous machine that
needs to produce consistent frequency and voltage. The PLC monitors the generator speed
(frequency) and output voltage using sensors/meters in the control cabinet . At startup, the PLC
keeps the generator isolated from the external load or grid via an output breaker. Only once the
conveyor/generator is spinning at the correct speed (e.g. 1500 RPM for 50 Hz, depending on pole
count) and the output is at the correct voltage, the PLC will close the breaker to connect the
generator to the load . If synchronizing to a grid, synchronization relays ensure phase matching
before connection. In an off-grid scenario, the generator might establish the grid, so it would simply
close onto the local load bus.
Once connected, the PLC (and associated voltage regulators) will control the generator’s field or excitation
(if it’s a wound-field machine) to regulate voltage. However, since Rosch uses a permanent magnet
generator, regulation may be done via power electronics (e.g. an AC-DC-AC converter) or by controlling the
load. An important control aspect is managing the load sharing: as the generator is loaded, the increased
electromagnetic torque automatically slows the rotation slightly, which in turn is countered by the buoyancy
drive providing more torque – the system naturally finds a new equilibrium. The PLC might also control
dump loads or pitch in backup modules as needed to keep frequency stable. For instance, if load suddenly
drops (reducing generator braking), the system might accelerate – to prevent overspeed, the PLC could
temporarily cut compressor input (reducing buoyant force) or engage a resistor bank to soak up excess
power until balance is restored.
Safety and Interlocks: The control system includes numerous safety features. If any parameter
goes out of safe range – for example, overpressure in the air tank, overspeed of the generator, or
an unexpected stop in conveyor movement – the PLC will execute an emergency shutdown
sequence. This typically would vent the air pressure (safe release), open electrical circuit breakers to
disconnect the generator, and engage a mechanical brake to stop the conveyor if needed. Water
level sensors might detect any leakage or change in water volume in the shaft. The PLC also ensures
that backup modules (in multi-module plants) kick in if one module is taken offline, to maintain
power output.
User Interface and Monitoring: The system likely has an HMI (Human-Machine Interface) panel or
SCADA integration where operators can see the status (pressures, speeds, power output,
temperatures of components, etc.). The measurement cabinet mentioned in documentation
8
•
20
20
•
•
8
contains visual and sound indicators, as well as instruments for three-phase voltages, currents, and
frequency . Through this interface, the internal R&D and simulator teams can monitor exactly
how the system behaves and verify that the simulation matches reality.
In summary, the electronics and control of the KPP ensure that the mechanical buoyancy engine runs
smoothly and safely. By automatically timing the injections and maintaining the generator’s operational
parameters, the control system allows KPP to function as a stable power source. For simulation purposes,
every aspect of this control loop – from compressor behavior to valve timing and generator load response –
must be modeled to accurately reflect the real system’s dynamics.
Generator and Power Output Characteristics
The generator in the KPP plays a dual role: energy converter and speed regulator. The design is a threephase
AC generator with advanced features: - It uses neodymium permanent magnets, which allow for a
high efficiency and high power density design . Such a generator is essentially a permanent magnet
synchronous generator (PMSG). PMSGs do not require external field excitation, which simplifies the system
(no need for slip rings or separate excitation control) and improves efficiency (less energy wasted as field
losses). Rosch’s claim is that this generator design brings efficiency “close to 100%” – practically,
efficiencies in the high 90% range are achievable with low-loss core steel and strong magnets. - The
generator is likely a multi-pole machine to produce grid frequency at relatively low rotational speeds.
However, given the slow buoyancy motion, a gearbox is employed to step up the conveyor speed. For
example, if the floats cause the conveyor to move at, say, 5 RPM, a gearbox might increase that to the
required RPM for 50 Hz. Alternatively, the system could use an electronic inverter: rectify the generator
output and then invert to 50/60 Hz. The evidence suggests a direct AC generation approach (with gear) was
used in prototypes (they report 3×380 V, 50 Hz directly from the generator when at full speed) . - The
power electronics associated may include an AC synchronizer or a grid-tie inverter depending on
configuration. In larger installations, multiple generators might be synchronized to a common bus. This can
be done by using inverters for each or by mechanically locking their speeds to the grid frequency. Since
each 500 kW unit is independent, the simpler method is likely using inverters or modern grid-tie converters
for flexibility. However, one could also run each generator as a synchronous generator tied to the grid, and
they would automatically stay in phase via the grid coupling (much like multiple alternators in a power
plant). The KPP documentation highlights that once full speed is reached, the generator is connected via a
three-phase switch , implying a direct grid connection when synchronous.
One important characteristic is that the generator’s electromagnetic torque provides a braking force on
the buoyancy mechanism . By controlling the electrical load (either through a governor or via how
much current is drawn), the system can adjust how fast the floats rise. In practical terms, the heavier the
electrical load (up to the 500 kW limit), the more the generator resists turning – this slows the conveyor until
the mechanical input (buoyancy) matches the electrical output. The PLC will ensure this balance is met by
perhaps adding more air (all floats active) or if overloaded, by shedding some load or using the reserve
modules. A finely tuned KPP will operate at a steady state where each float injection and release happens at
a constant interval, the conveyor turns at constant speed, and the generator outputs at constant frequency.
Resonance and Advanced Theories: The KPP literature sometimes mentions exotic terms like “circularly
polarized gravito-electromagnetism” and the ECE (Einstein-Cartan-Evans) theory in context of the generator
. As lead engineer, one may interpret this as the company’s theoretical research into maximizing
electrical extraction. It hints that the generator and circuit might be designed to leverage resonant circuits
20
19
19
20 21
20
12 22
31
9
or novel electromagnetic effects to improve efficiency. For example, running certain coils in resonance could
recapture some reactive energy or utilizing particular magnetic circuit geometries could minimize counter-
EMF losses. While these aspects go beyond classical design, the practical takeaway is that the generator
and its drive electronics are highly optimized for efficiency and minimal losses, ensuring that virtually
all mechanical energy from the buoyancy wheel is converted to useful electricity . This means low
internal resistance, low hysteresis losses, and potentially power factor correction so that the mechanical
system “sees” a smooth resistive load rather than any jerky or pulsating torques.
For simulation purposes, modeling the generator would involve its torque-speed curve and electrical
characteristics. A simple approach is to model it as an ideal AC generator with an efficiency factor and a
governor controlling torque to maintain speed. The electrical output from one module (500 kW at 50 Hz)
can be represented as a voltage source in the simulator that is frequency-locked by the rotation speed of
the buoyancy engine.
Efficiency Enhancements and Energy Balance
One of the most striking claims of the KPP technology is that it produces more electrical energy than the
electrical energy it consumes (for air compression and control) – effectively a net energy producer. While
this challenges conventional thermodynamics, Rosch and partners attribute the success to multiple
efficiency innovations and careful energy management in the system. As the lead engineering team, it’s
important to understand these enhancements, as they must be reflected correctly in the theoretical model
and any high-fidelity simulations:
Microbubble Injection (Cavitation Assistance): As mentioned earlier, microbubble injection on the
descending side reduces the density of water and thus its buoyant support on the down-going floats
. In practical terms, by pumping tiny air bubbles into the water around the descending
floats, the floats experience less upward push. This means they fall faster and with greater force,
contributing more to turning the chain. If done optimally, the energy to create these bubbles (which
could be minimal if using waste air or clever fluidic devices) is less than the gain achieved by easing
the floats’ descent. Microbubbles can be generated, for instance, by diverting some compressed air
through micro-porous diffusers near the bottom of the descending side. The phenomenon of
reduced buoyancy via microbubbles is well documented (it’s known to even sink ships in extreme
cases) . The key is that the introduction of bubbles must be done in an energy-efficient way
to truly improve net output. Rosch’s IP likely includes a method to produce microbubbles (perhaps
using the pulsed air mechanism or vented air from floats) without expending significant extra
energy . For our model, we can consider that the effective weight of descending floats is
increased (or conversely, the energy needed to raise them is reduced) by a certain factor due to
microbubbles, effectively tipping the balance further in favor of net positive work.
Water Jet Propulsion: As air is injected and water is expelled from a float’s bottom, those water jets
provide an extra upward thrust on the float (action-reaction). Rosch identified that as the float
ascends, the trapped air will expand, continuously forcing water out in jets below the float . This
not only helps clear the water from inside, but the downward jet streams push against the
surrounding water, giving an upward push (like a small rocket effect). This effect adds to the buoyant
force. It’s essentially making use of the expansion energy of the air (which came from the
compression work) in a directed way rather than letting it dissipate. In design, floats might have
nozzles or shaped outlets to maximize this thrust. Though not a huge contributor compared to
19
•
28 29
29
32
•
26
10
buoyancy, it improves the force vs. depth profile of the float’s journey – possibly maintaining more
thrust even in the upper portions of the tank.
Pulsed Air Injection: Instead of a steady flow compressor, KPP uses pulsed air delivery for
efficiency . The idea is to compress air in an energy-efficient manner (for example, allowing the
compressor motor to work at optimal RPM/load) and then deliver the air to the floats in short bursts
exactly when needed. This avoids unnecessary idling at high pressure or blowing excess air.
Moreover, by pulsing, there is speculation that it could induce oscillations or use resonance that
lower the energy cost of compression. One theory is that pulsing might be used to reduce the
buoyancy of downward containers as well – possibly meaning timed pulses create a pressure
wave that momentarily pushes down on the water above descending floats, aiding their descent or
injecting microbubbles at specific intervals. In any case, the compressor’s effective efficiency is
enhanced by intelligent control. For modeling, one could implement the compressor as having a
higher effective efficiency (lower input per unit air) because it only works when needed and
recaptures some energy (perhaps during the off-cycle, the compressed air cools and that heat is
recycled, etc.).
High-Efficiency Generator (Neodymium Magnets): By using a near-lossless generator, the
electrical conversion efficiency is maximized . Conventional generators might be 90–95% efficient
at this scale; KPP’s may be 97–98%. This reduces losses (heat) and ensures most mechanical energy
becomes electrical. This by itself doesn’t create energy but ensures less is wasted as heat, tipping the
net balance favorably.
Low-Friction and Smooth Mechanics: While not explicitly stated in marketing, the mechanical
design is undoubtedly optimized for minimal friction (using bearings, low-friction coatings) and
minimal drag aside from what’s functionally needed. The floats likely have an aerodynamic (or rather
hydrodynamic) shape to ease their passage through water. The chain and sprockets are well
lubricated. Any reduction in friction means less of the buoyant work is lost and more goes to
generation. For simulation, frictional losses can be a parameter that is kept very low.
Possibility of Environmental Energy: Some analyses (external) suggest that if the KPP indeed
outputs excess energy, it might be drawing on an external source, such as slight cooling of the
water/air (thermal energy from the environment) or gravitational potential if somehow gravity is
being “used up” (exploiting some novel physics of the gravity field) . As lead engineers, our focus
is on the observable engineering: heat may be generated in compression and dissipated; water
temperature might drop slightly if that heat is converted to mechanical work, etc. The design likely
tries to reclaim as much as possible (for example, using the cooling of expanding air to possibly
condense moisture or something beneficial). While these are speculative, a thorough simulator
could incorporate thermodynamic aspects: e.g., tracking water temperature over time, which might
supply a tiny fraction of energy if cooled (in essence functioning akin to a heat pump capturing
ambient heat to do work). However, given that the KPP is marketed as a closed-loop buoyancy
system, the official stance is that clever engineering and physics principles allow it to achieve overunity
performance (with the caveat that this challenges standard theory, but it has been
demonstrated in practice per provided test results).
In quantitative terms, consider a 500 kW module: if it outputs 500 kW and uses, say, 100 kW for
compressors and control, it would have an efficiency ratio of 5:1 (output:input). The enhancements above
•
25
33
•
19
•
•
34
11
aim to push this ratio as high as possible. In one report, a smaller scale device had ~11.36 kW out for
1.66 kW in (≈7:1) . For larger systems, targets might be slightly lower ratios but still significant. The
design also incorporates redundancy to keep efficiency optimal – e.g., having extra floats or spare modules
ensures the plant can run at full capacity even if one unit is down for maintenance, avoiding efficiency
losses due to downtime.
Modularity and Multi-Unit Synchronization
One of the strengths of KPP technology is its modularity and scalability. The base 500 kW unit can be
thought of as a building block. Multiple such units can operate in parallel to achieve higher total power, and
they can be coordinated to ensure stable combined output. Here’s how modular integration is designed:
Physical Modularity: In a large installation, multiple KPP shafts (with their float systems) are
constructed side by side. For example, a 5 MW plant may consist of 10 active shafts (each 500 kW)
plus additional reserve shafts for backup . Ki-Tech Global’s data specifies a 5 MW KPP has “10 +
4 water tanks, generators, compressors and control systems (10 in operation, 4 for back-up)” .
Indeed, an installed 5 MW plant uses 14 vertical modules, each module akin to the one described in
this paper, but only 10 are running at any given time at full load – the other 4 can be rotated in
during maintenance or peak support. These shafts are usually all housed in one facility footprint (for
5 MW, about 1500 m² area) with some common infrastructure . The modules are typically
independent in terms of mechanical operation – there are no moving mechanical linkages between
separate modules, which is advantageous for reliability (one can stop while others continue).
Electrical Synchronization: When multiple generators feed a common grid or bus, they must be
synchronized in frequency and phase. The KPP’s control systems handle this by either grid-tying each
generator with proper synchronization or by using a master-slave control approach. One common
strategy: designate one unit as the master frequency reference (or simply use the external grid as
reference). All other unit controllers then adjust their generator’s output to match that frequency
and share the load. In practice, if all units are tied to a grid, each generator will naturally fall into
phase with the grid (as synchronous generators) and share load according to their governor
settings. The PLCs in each unit likely communicate or at least are calibrated so that each provides
~500 kW when needed. Should one unit falter or be intentionally taken offline, the others can pick up
the slack (if within their capacity or with the help of a standby unit coming online). Modern power
management might use an independent power management system (PMS) that oversees the
dispatch of multiple modules, turning them on or off to match demand or to perform maintenance
rotations.
Compressed Air Supply in Multi-Unit Setup: Each module has its own compressor system.
However, for efficiency, a large plant might use a centralized compressed air system feeding multiple
floats pipelines, or at least each module’s compressor might be sized to also support a backup
module in case of one compressor failure. There could be a network of air reservoirs interconnected
for redundancy. But generally, keeping modules self-contained (each with its compressor and tank)
isolates faults and simplifies design. If one module’s air system fails, only that module is affected and
a backup module can step in.
Control Coordination: At the plant level, a supervisory controller likely exists to coordinate modules.
For instance, when ramping the plant output up or down, it might stagger the engagement of
30
•
6
35
15
•
•
•
12
modules (to avoid all compressors starting at once causing a spike, or to sync the generator
connection one by one). In a simulator, one would incorporate a top-level control loop that can send
start/stop or load adjust commands to each module’s PLC. The internal PLC still handles the fine
control of its floats and compressor, but the supervisory system might tell it “run at 100%” or “go to
standby”. The KPP modules are inherently stable when running steady, so adding more modules
simply multiplies the power available.
Grid Integration: When multiple 500 kW outputs combine, the plant’s electrical output can be either
combined at a common bus then stepped up via a transformer for transmission, or each module
could have a smaller transformer and combine at high voltage. The synchronization means all
modules must produce identical frequency and phase. If the plant is in an off-grid configuration (like
powering a microgrid or isolated facility), one module might operate in voltage-control mode
forming the grid, and the others operate in droop control to share load. Because KPP modules can
respond to load changes by virtue of their physics (and PLC adjustments), they can function similarly
to conventional generators in grid stabilization. In fact, marketing claims that KPP provides grid
stability and balancing services due to its controllability .
Modular Expansion: One advantage of modular design is scalability – to increase capacity, you
install more 500 kW units. The design is such that adding modules is linear and does not
fundamentally change how each unit works. This is useful for incremental expansion (e.g., start with
1 MW (two modules) and later add more modules to reach 5 MW or more, reusing much of the
existing infrastructure). The control software would simply have more units to manage. Ki-Tech
mentions the KPP is “totally dispatchable, with scope for expansion whenever needed” ,
underscoring this modular growth capability.
Redundancy and Maintenance: The inclusion of backup modules (e.g., the “+4” in 5 MW plant)
indicates that at any time a subset of modules can be taken offline for maintenance while the plant
still delivers full power with the remaining ones. The mechanical design of each module is relatively
simple (fewer moving parts than a turbine, for instance), so maintenance might involve inspecting
chains, bearings, and seals, or servicing the compressor. This can be done one module at a time,
during which the others carry the load. In a simulator, one can simulate failure of a module and
ensure the control system responds by ramping up a standby unit.
In summary, synchronizing multiple KPP units involves electrical coordination and a supervisory control
layer, but each 500 kW unit is a self-contained generator. The modular approach provides flexibility (units
can be operated independently or together) and reliability (spares can instantly replace any unit that goes
down). From a systems perspective, the KPP plant behaves like an array of generators – akin to a multiengine
power station – all driven by the same principle of buoyancy. The simulator should handle the
interactions of multiple units on a shared electrical network and possibly shared resource (like if multiple
modules draw from the same water reservoir or if waste heat in one affects others via water temperature,
though in a large water volume that’s minimal).
•
36 37
•
38
•
13
Theoretical and Applied Physics Considerations
To design an accurate simulator and advance R&D, it’s useful to address the theoretical underpinnings at a
system level:
Energy Flow and Thermodynamics: The KPP challenges the conventional energy conservation
mindset. In analyzing it, one must carefully track all energy inputs and outputs. The primary input is
the work done by the compressor on the air. That energy goes into pressurizing air and eventually
is converted into potential energy of the buoyant floats (and some into heat). The outputs are the
electrical energy generated and any losses (mostly heat in air compression, friction, turbulence in
water, and generator resistive losses). For a true closed-loop, steady-state operation, the claim is that
output > input because losses are minimized and some normally lost energies are recaptured (e.g.
expansion work of air and possibly environmental heat). When modeling, one might incorporate the
thermodynamic process: air compression (likely near-adiabatic compression with heat dissipated),
then air expansion in floats (cooling the air, heating the water slightly), etc. If indeed additional
energy is drawn from the environment (like from cooling of the surrounding water or air), it
effectively means the KPP could be operating as a kind of heat engine, where the “fuel” is low-grade
ambient thermal energy being converted to mechanical work via the oscillating pressure of air and
water. This is not stated explicitly by the makers, but it’s one way to rationalize the energy balance.
The simulator can test different assumptions: is the water cooling over time? Is air coming out cold?
Those could indicate energy drawn from ambient.
Fluid Mechanics: The motion of floats in water involves drag force, added mass effect, and possibly
flow-induced vibration. At 25 m depth, the floats might ascend at a moderate speed (perhaps on the
order of 1–2 m/s). The Reynolds number for flow around them is high, and there will be turbulence.
The microbubbles on the down side further complicate fluid dynamics by changing water density
and viscosity. Accurately simulating this would normally require CFD-level modeling. However, for
system simulation, one can use simplified empirical coefficients for drag and added mass. The
Archimedes force is straightforward when float is fully submerged and filled with air: F_b =
ρ*g*V . If float remains fully submerged the whole way, F_b is roughly constant until near the very
top (if it starts to break the surface, but presumably the loop keeps them submerged throughout).
Drag force will oppose motion: F_drag = 0.5 * ρ * C_d * A * v^2 upward for ascending
floats (slowing them) and downward for descending floats (slowing descent). Microbubbles
effectively lower ρ or the C_d on the descending side. If the microbubble density is high, one could
model the descending side water as having an effective density ρ’ less than normal. This helps in
simulation to show less buoyant resistance and faster drop.
Mechanical Dynamics: The conveyor-float system is a multi-body mechanism. However, because the
floats are uniformly distributed and operate cyclically, one can model the net torque on the main
sprocket from all floats as a somewhat continuous function (rather than discrete jerks) after initial
transients. The inertia of the system (moving mass of floats, water interaction, plus rotating inertia of
generator and gearbox) provides smoothing. Nonetheless, there may be slight torque ripple as each
float engages/disengages air. A detailed model might simulate each float’s contribution as it moves.
For stability analysis, one might look at the system’s natural frequency (like a mass-spring-damper,
where buoyancy provides a “spring” and the inertia of rotating parts is the mass, and damping from
drag and generator load). The presence of the generator’s load (which is proportional to speed for a
•
•
•
14
generator connected to a grid – effectively a stiff torque-speed characteristic) means the system is
heavily damped and will not runaway easily.
Magnetics and Resonance: If the design indeed leverages some resonant circuit in the generator or
uses the “magnetic potential,” simulation might include an electrical resonance (like LC circuits tuned
to certain frequencies in the generator’s coils). For example, it’s conceivable that the generator coils
and capacitors form a resonance at 50 Hz that reduces the net load the prime mover sees for
reactive power (thus only real power is drawn). In standard power engineering, a power factor of 1 is
ideal – here they might be achieving that through resonance. Additionally, if one subscribes to the
more speculative “gravito-magnetic” ideas, they would assert that the rotating mass of the system in
Earth’s gravitational and magnetic field might have subtle effects. Such effects are extremely small
and typically negligible, but the marketing hints at cutting-edge physics being at play . For the
R&D team, it may be worth exploring if high-frequency oscillations or certain magnetic field
orientations in the generator contribute anything beyond normal electromagnetic induction –
however, no concrete evidence of such exotic effects is given in mainstream literature. It’s more likely
used as a theoretical narrative to justify the observations.
In designing a simulator, the focus should remain on verified physics: buoyancy, fluid flow, and classical
mechanics/electrical engineering. The aforementioned enhancements (microbubbles, etc.) can be
implemented as adjustments to parameters that improve the net energy outcome consistent with the
empirical results. Ensuring that the simulated KPP behaves “exactly as the real one” means tuning these
parameters until the model’s input-output power and dynamic response match measured data from the
actual KPP.
For instance, one can calibrate the drag coefficients or microbubble density effect such that the simulator
predicts a compressor power of ~X kW and generator output ~Y kW, matching test reports (like 4.2 kW in,
12 kW out in small scale , or presumably ~100 kW in, 500 kW out in a full module). Once calibrated, the
simulator can then be used to explore different scenarios (e.g., how does the system respond if one float’s
valve sticks, or if grid frequency changes, etc.) and to train the control system logic under various
conditions.
Technical Design Summary
Bringing all pieces together, a 500 kW KPP module is an assembly of mechanical, fluid, and electrical
subsystems that must operate in harmony. When broken down: - Mechanical subsystem: 25 m well, ~2 m
diameter; chain conveyor with perhaps a dozen or more floats; top and bottom sprockets; gear/drive
coupling to generator. - Fluid subsystem: water as working fluid in tank; air supply at ~4 bar; valves and
piping for air injection; possibly an air recirculation for microbubbles. - Electrical subsystem: 500 kW PM
generator, switchgear, control electronics, and a ~10–20 kW (estimated) compressor motor plus small
motors for valves. - Control subsystem: PLC with analog and digital I/O, running sequences and ensuring
synchronization of events; protective relays and emergency stop logic.
From a design integration perspective, special attention is paid to the timing and phasing of events. There’s
a remarkable choreography: the instant a float locks into bottom position, air must shoot in; as it departs
upwards, the next float is just moments behind. Meanwhile, at the top, floats must vent exactly when they
crest so as not to resist the turn. If any timing is off, floats could either not gain enough lift or could cause a
jam. Thus, sensors likely detect a float approaching bottom and pre-pressurize the connection, etc.
•
31
13
15
Mechanically, the tolerances must be tight but also allow for smooth release (perhaps using funnel-like
guides for the air nozzle into the float valve).
The control software likely includes a startup routine (gradually pressurize, fill floats one by one, wait for
speed), a normal operation loop (continuous fill timing), and a shutdown (where perhaps it stops injecting
air and lets the system come to rest, or actively brakes it). One challenge is avoiding any resonant
oscillation: the interplay of buoyant force and the heavy chain could possibly oscillate (imagine floats
bouncing in water). The generator’s damping and possibly additional dampers (like water itself is damping)
should suppress this. A well-tuned system will reach a steady rotation speed and not oscillate in speed or
torque significantly. The PLC might have to adjust if, say, all floats happen to align in a way that causes a
torque pulse.
Multi-Unit (500 kW Module) Synchronization and Control
In a multi-module plant, each module operates as described, but a higher-level logic ensures they
coordinate: - Parallel Operation: All active modules feed into a common electrical point. To increase total
output, more modules’ generators are loaded; to decrease, some may be idled or their output throttled
(perhaps by slight speed reduction via their compressor input). The modules are inherently droop-like
controlled: if one tries to run faster, it will take more load and slow, etc. So they share load in proportion to
their settings. The supervisory control might simply set all modules to the same setpoint. - Sequencing: If
one module is taken offline, the control will ramp up another (opening its breaker after syncing and starting
its compressor). This might be done seamlessly to avoid output fluctuation. - Modularity in Simulation:
One can simulate each 500 kW module as an object with an interface (e.g., an AC power output and perhaps
an air intake or something if linking compressors). Then simulate 10 of them running together, possibly
communicating via a central scheduler. This object-oriented approach mirrors the actual modular design.
The KPP is a novel system blending classical hydro-mechanical engineering with clever control and possibly
new physics interpretations. Its design documentation and demonstrations (in Thailand and by third parties
like TÜV or Dekra as cited ) show that it can work as claimed, producing continuous power. For the
internal R&D and simulator teams, the goal is to replicate this behavior in a virtual environment,
validate it against real data, and then use the model to predict performance under all conditions. This
requires capturing the detailed physics (buoyancy, airflow, mechanics) and control logic described above.
In conclusion, the 500 kW Kinetic Power Plant module is an intricately designed system where
components act and react in a coordinated cycle: air compressors inject life (buoyancy) into floats, floats
push the chain, the chain spins the generator, and the generator’s resistance in turn governs the floats’
motion. By leveraging applied physics (Archimedes’ principle, fluid dynamics) and innovative engineering
(pressure exchangers, microbubble drag reduction, high-efficiency magnetics), the KPP achieves a selfsustaining
energy generation process. Multiple such modules can be synchronized for higher output,
showcasing the concept’s scalability and modularity. For simulation and further development,
understanding each subsystem’s dynamics and interactions – as detailed in this paper – is critical to ensure
the virtual models behave exactly like the real KPP, thereby allowing the team to refine the design and
control strategies for even better performance in future iterations.
Sources:
Ki-TECH Global AS – Kinetic Power Plants product info
39
• 5 6
16
World Vision Green Energy – KPP Technology overview
Eco-Prius (Poland) – KPP description and features
Rosch Innovations – Technical brochure & operational description
Vision KPP Energy (Blog) – Summary of KPP operation and components
J. Lozano, Evaluation of KPP Technology – analysis of efficiency enhancers (microbubbles, pulsed air, etc.)
Alfred Evert, Flexible Buoyancy Power Station – discussion of buoyancy power concept and performance
Technology KPP – WVGE – World vision green energy
https://wvge-me.com/technology-kpp/
Eco-Prius - KPP Kinetic Power Plant
https://ecoprius.pl/en/kpp-kinetic-power-plant.html
We offer KPP - Kinetic Power Plants
https://www.ki-tech.global/what-we-offer
Rosch Thrust Kinetic Power Plant | PDF
https://www.scribd.com/doc/298597473/Rosch-Thrust-Kinetic-Power-Plant
KPP – Kinetic Power Plants – Vision KPP Energy
https://visionkppenergy.wordpress.com/2018/03/06/kpp-kinetic-power-plants/
Microsoft Word - eft950en.doc
https://www.shlabs.pl/eft950e.pdf
Microsoft Word - Evaluation of KPP Technology by Javier Lozano, Electrical Engineer
from Stanford University.docx
https://www.nexus.fr/wp-content/uploads/2016/09/Evaluation-of-KPP-Technology-by-Javier-Lozano-Electrical-Engineer-from-
Stanford-University.pdf
• 1 12
• 40 4
• 8 9
• 10 28
•
41 29
•
42 30
1 3 12
2 4 15 31 36 37 39 40
5 6 35 38
7 8 9 13 17 18 20 21 23 24 27
10 16 22 28
11 14 30 34 42
19 25 26 29 32 33 41
17
Kinetic Power Plant Technical Design – Detailed
Addendum
Pressure Exchanger System
Mechanical Layout and Components
The KPP’s pressure exchanger system manages the injection of compressed air into each floater at the
bottom of the water column and the venting of air at the top. Mechanically, this subsystem consists of an air
compressor (with an integrated pressure-exchanger device), high-pressure air lines, injection valves at the
base of the tank, and outlet/vent valves at the top. Each floater (a sealed or semisealed chamber) has an
inlet valve at its bottom that connects to the pressurized air supply and a one-way outlet (or check valve) to
purge water. At the bottom position, a floater aligns with an injector nozzle or manifold that delivers a burst
of high-pressure air from the compressor/accumulator. This air rushes into the floater, forcing the water out
through the check valve (usually downward into the tank). The mechanical layout ensures the injector forms
a tight seal with the floater only at the bottom dwell position, preventing significant air loss to the
surroundings during the fill event. At the top of the cycle, each floater’s vent valve opens (or the floater
simply reaches an open-top manifold), releasing air either to atmosphere or back to a low-pressure return
line. The floats then refill with water, completing the cycle. The pressure-exchanger integrated into the
compressor is a specialized mechanism designed to make the air transfer extremely efficient. In essence, it
minimizes throttling losses and may recover some of the energy from the expelling water or expanding air.
For example, it could use the water’s pressure (as it’s expelled) or the residual pressure of vented air to prepressurize
incoming air – analogous to energy recovery devices in desalination systems. This unique
compressor/pressure-exchanger design enables near-isothermal compression and expansion, reducing the
energy required for air injection and improving overall efficiency of the buoyancy engine. All piping and
valves in the pressure exchange loop are rated for the working pressure (often on the order of 2–3 atm in
KPP designs) and fast actuation to keep up with the cycle timing.
Thermodynamic Model and Equations
Thermodynamically, the air injection process is modeled as a rapid expansion of compressed air into the
floater, ideally with heat exchange so that it approximates an isothermal expansion. At the moment of
injection, the compressed air must overcome the hydrostatic pressure at the bottom of the tank. The
required injection pressure (just to begin inflow) is determined by pressure balance:
where is atmospheric pressure, is water density, is gravitational acceleration, and is the depth of
injection (height of water above the floater). For example, in a 10 m water column, is about 2 atm
(1 atm ambient + 1 atm from water). The compressor provides air above this pressure to rapidly push out
the water. The work done injecting air into one floater can be estimated by the work of isothermal
compression/expansion for the volume of air added. If is the floater’s internal volume (at atmospheric
pinject ≥ pbottom = p0 + ρwgH,
p0 ρw g H
pbottom
Vf
1
conditions) and we assume the air is injected near-isothermally (maintaining water temperature ), the
energy input (per cycle per floater) from the compressor is approximately:
for an ideal isothermal process. This equation comes from the integral with
(isothermal), yielding . In practice, will be close to plus some margin
for flow. For instance, injecting air to 2 atm into a floater of volume 0.1 m³ (at STP equivalent) requires on
the order of . Some of this energy is immediately converted into the potential energy of
the raised water (expelled from the floater), and the rest is stored as increased internal energy of the
compressed air. As the floater rises, that compressed air will expand and cool (or warm, depending on heat
exchange), affecting the net energy. We consider two thermodynamic extremes:
Adiabatic injection (no heat exchange during the fast fill): The air entering the floater undergoes a
rapid expansion and cools significantly. This results in a lower pressure inside the floater after filling
(since const for adiabatic). The floater may not expel all water if the air cools and pressure
drops before full purge. However, as the floater later warms up from the surrounding water, the air
inside gains heat, expanding and doing additional work (pushing out water as it rises). This thermal
buoyancy boost is one of the KPP’s intended effects – essentially extracting heat from the
environment to increase buoyant force. The energy gain from this heating is often referred to as H2
effect. We can quantify it by comparing isothermal vs adiabatic processes: the additional work from
ambient heat is roughly if the injected air at temperature eventually
warms to water temperature . Colloquially, this means if cold compressed air (say from an
adiabatic expansion) is injected and then warms up by ΔT, the expansion due to that heating yields
extra upward push for “free.”
Isothermal injection (with perfect heat exchange during fill): In this ideal case, the air does not cool
as it expands into the floater; it continuously absorbs heat from the water to stay at . This
requires a slower injection or a pre-heating of air. The work required to inject is less in an isothermal
process than adiabatic (since the air does some work on the water while heat flows in). The KPP
design seeks to approach this isothermal ideal by using heat exchangers or by carefully timing the
air release/entry so that the water’s thermal energy is utilized. If achieved, the buoyant lift gained
per floater is maximized for the given pressure. Any energy remaining in the compressed air when it
reaches the top is wasted if simply vented. In fact, if the air is released slowly at the top (isothermally
expanding to atmospheric pressure), the unrecovered energy can be calculated as
. This represents the lost work potential when the highpressure
air returns to atmospheric pressure. A well-designed pressure exchanger system tries to
reclaim some of this potential – for example, by routing the released air into an expansion chamber
or using it to pre-charge other floaters – thereby improving efficiency.
In summary, the pressure exchanger system is modeled by combining ideal gas behavior with liquid
displacement. The mass flow of air into a floater is approximately (if filling to pressure ).
This same mass of water (by volume) is expelled. The energy balance per floater involves the compressor
work input, the gain in gravitational potential energy of the displaced water and risen floater, and heat
exchanged with the environment. By including equations of state and assuming near-isothermal conditions,
T
Winject ≈ p0Vf ln , p0
pinject
W = ∫ p dV V0
Vf pV = const
W = p0V0 ln(pinject/p0) pinject pbottom
Winject ∼ 1.0 kJ
•
pV γ =
Qadded = nRT ln Tair,in
Twater Tair,in
Twater
•
Twater
Eunreleased =
pbottomVf ln p − 0
pbottom (p − bottom p0)Vf
m = RT
pinjectVf pinject
2
the system can be analyzed to verify that the net energy output cannot exceed input unless external heat is
absorbed (which is exactly what H2 seeks to exploit). We include these thermodynamic equations in the
design to simulate how tuning the air injection (pressure, timing, temperature) affects performance. For
instance, injecting air at the precise moment a floater reaches bottom and possibly using a thermal jacket
on the injector can help ensure the expansion is as thermalized as possible, boosting buoyancy with
ambient heat.
Timing Logic and Valve Control
Timing is critical for the pressure exchanger system. Each floater only has a brief window at the bottom
where it can be filled with air. The control system uses sensors (or encoder positions on the chain) to detect
a floater’s approach to the injection zone. The injection valve opens at the exact moment the floater’s inlet
aligns with the air nozzle. In practice, a pulse injection strategy is used: the air is released in a short, powerful
burst rather than a slow bleed. This ensures the floater is filled rapidly while it is correctly positioned, and it
also improves efficiency by injecting only when most effective (i.e. when the pressure differential is lowest at
the bottom dead-center position). Our design models a configurable injection duration (e.g. 0.5 s) during
which the valve remains open and air flows in. The flow may be approximated as constant for that duration,
or as tapering off if pressure equalizes. The valve timing is coordinated such that if the chain speed
increases, the controller shortens the injection pulse accordingly (and vice versa for slower chain). If the
chain were moving so fast that the floater doesn’t have enough time in the injector zone to fully fill, the
system either issues a warning or in a real design would use multiple injectors in series. In simulation, we
assume the control is ideal and always fills the floater to the desired level by the time it leaves the bottom.
At the top, a similar timing applies: just as the floater crests the sprocket and begins the descent, a valve
opens to vent the air. In many designs, this is simply a passive valve that opens once the floater is no
longer submerged (exposing it to atmosphere). The venting is almost instantaneous in our model – we
toggle the floater state from buoyant to heavy at the top position. In reality, venting could be slightly
delayed or occur over a small angle of chain travel to avoid jarring. We incorporate an option for a vent
duration (a fraction of a second) to smoothly transition the floater from air-filled to water-filled. This
prevents an unrealistically abrupt change in buoyancy in the simulation.
The coordination of bottom injection and top venting is handled by a state machine within the controller: a
floater state flips from “heavy” (water-filled) to “light” (air-filled) when it enters the bottom zone and back to
heavy when it passes the top zone. Sensors (or simply known chain position indices) trigger these state
changes. Importantly, the pressure exchanger (compressor and accumulator) must be synchronized with
this timing. The compressor keeps an air reservoir at the target pressure (say 2 atm). When an injection
event is triggered, a high-flow solenoid valve between the air reservoir and the floater opens. The rapid air
delivery causes a momentary pressure dip in the reservoir. After the valve closes, the compressor kicks in (if
needed) to restore pressure. In an advanced design, the pressure exchanger device could be a rotating
spool or piston that transfers a volume of high-pressure air into the floater while taking the same volume of
lower-pressure air (from the vent or environment) into the compressor intake. The effect is that the
injection is energetically optimized: only the difference in pressure has to be supplied by the compressor,
the rest of the air movement is achieved by exchange. Although our simulation does not explicitly model
the internal mechanism of the pressure-exchange compressor, we assume an efficiency gain (user-settable)
that reflects this technology (for example, a 20% reduction in compressor work compared to a standard
compressor at the same pressure).
3
In summary, the valve logic ensures that air is injected only at the correct phase of the floater’s cycle and
for the minimum duration required to achieve buoyancy. This pulse timing not only improves efficiency but
also avoids waste (air is not flowing except when needed). The outcome is a series of discrete air pulses
synchronized with the arrival of floaters, rather than a continuous bleed. This synchronization is
fundamental to hypothesis H2: by injecting in bursts at the optimal timing, the system more closely
approaches an isothermal, reversible process, minimizing entropy generation and maximizing the
conversion of input energy into useful work.
Mass and Energy Flow Integration
The pressure exchanger system interacts with other subsystems by providing buoyant force to the floaters
and imposing a load on the drivetrain in the form of compressor power draw. The mass flow of air into the
system can be substantial: for example, a real 500 kW KPP might inject on the order of tens of cubic meters
of air per minute at STP. In our model, every time a floater is filled, we deduct the corresponding air volume
from an idealized compressed air tank. We track the air usage rate (e.g. in m³/min) and compare it to the
compressor’s capacity. If the user inputs a compressor capacity of, say, 1.5 m³/min at 5.5 kW (a figure
inspired by reference designs), and the system at a given speed is using 1.8 m³/min, the simulation will flag
that the compressor cannot keep up (pressure would eventually drop). The compressor in the simulation is
modeled as a constant power drain by default, or a feedback-controlled device that maintains reservoir
pressure by turning on/off (in which case the power draw becomes intermittent). For simplicity, we often
assume steady compressor operation at a fixed power, and we calculate net output power as generator
electrical output minus this compressor power.
Energy flow-wise, consider one cycle of one floater: The compressor supplies a certain energy . Once
the floater is filled, the buoyant force does work on the chain as the floater rises, contributing to
mechanical energy that spins the drivetrain. When the floater vents at the top, the compressed air carries
away some energy (if vented to atmosphere, that energy is lost; if recaptured via the pressure exchanger, a
portion returns to the system). The water that was expelled at the bottom re-enters the floater at the top,
which in theory returns the gravitational potential energy that was invested in lifting it out (though in
practice, much of that energy went into the mechanical work extracted by the chain). In a perfect cycle
ignoring losses, the energy input by the compressor would equal the sum of: (a) the mechanical work
extracted by the generator, (b) the thermal energy absorbed from the environment (if any), and (c) the
leftover energy in the expanded air at top (wasted if not recovered). Our model computes the net energy
per cycle for each floater:
where for the ascent (approximately for full float volume over
height ), and is the compressor input for that floater (as discussed above). Losses like drag
(H1 hypothesis) and mechanical inefficiencies will reduce , while thermal inputs (H2)
effectively increase it by allowing more force for the same air mass. We ensure the mass conservation in
the model: every kilogram of air injected eventually leaves at the top; every liter of water expelled at bottom
re-enters at top. The compressor is the only net source of energy (aside from any thermal uptake), and the
generator is where useful energy leaves the system. This integrated view confirms that without H2 (no heat
input), the system cannot output more energy than the compressor puts in (indeed, it will be less, due to
losses). With H2, some ambient heat is turned into extra mechanical work, boosting efficiency above the
baseline. We incorporate these effects by adjusting the effective buoyant force if H2 mode is on, to
Winject
Enet = Ebuoyancy work − Einjection work,
Ebuoyancy work = ∫ Fbuoy dh ρwgVfH Vf
H Einjection work
Ebuoyancy work
4
simulate increased floater volume or lift (e.g. treating the process as isothermal yields a higher buoyant
impulse than adiabatic).
In conclusion, the pressure exchanger system is a tightly orchestrated mechanism combining mechanics
(valves, compressor, floaters) and thermodynamics (compressed air expansion, heat exchange). It
ensures that floaters are alternately filled with air and water at the correct times, and it strives to do so with
minimal energy loss. The mechanical design of the injector and valves must withstand repetitive rapid
cycling and high pressure differentials, while the thermodynamic design (insulation or heat exchange) must
handle temperature changes of the air. The result is a series of buoyant “pulses” feeding the drivetrain –
these pulses are the input that the next sections (drivetrain and control) will convert into smooth rotation
and electricity.
Drivetrain Mechanics
Chain and Sprocket Torque Transmission
The KPP’s drivetrain begins with the chain and sprocket system that converts the linear force of buoyant
floaters into rotational torque. The floaters are attached to an endless loop chain that runs over a bottom
sprocket (submerged in the water tank) and a top sprocket. The top sprocket is keyed to the main drive
shaft, so as the chain moves, it turns this shaft. The net upward force on the ascending side minus the
downward force on the descending side creates a net tension difference in the chain. This net force
around the sprocket radius produces a torque:
For instance, if at a given moment 3 floaters on the ascending side are buoyant (pulling up) and 3 on the
descending side are heavy (pulling down), the net force might be on the order of hundreds of newtons
(depending on floater buoyancy). With a sprocket radius of 0.15 m, even a 100 N net force yields 15 N·m of
torque. The simulator calculates instantaneous each time-step from the current floater distribution
and buoyancy forces. In steady operation, floaters are spaced evenly so that as one exits at the top, a new
one is injected at the bottom. This leads to a quasi-continuous input torque with periodic ripples each time
a floater is added or removed. However, because floaters may not be uniformly distributed at every moment
(especially during start-up or if hypotheses like H1/H2 alter some floaters more than others), can
fluctuate.
We assume the chain does not slip on the sprocket teeth (ideal engagement). The chain’s own weight also
adds to the tension on the descending side, but in our model that is considered part of the static load (or
effectively increases the floater weight on that side). Any friction in the chain links or bending around
sprockets can be modeled as a small fractional loss – we include an efficiency factor for the chain, e.g. 98–
99% efficient, to account for bending hysteresis and water drag on the chain. This effectively subtracts a
small torque proportional to . We also account for the inertia of the moving chain. The chain and
attached floaters constitute a moving mass that, when converted to rotation at the sprocket, contributes an
effective moment of inertia . We can estimate by distributing the mass of one span of
chain+floaters to the sprocket radius: , where is the portion of chain mass that is
accelerating with the sprocket (for a long continuous chain, effectively the mass of floaters moving upward
minus those moving downward, but since one side decelerates while the other accelerates, it’s complex; we
Fnet
R
τchain = Fnet ⋅ R.
τchain
τchain
τchain
Jchain Jchain
Jchain ≈ meffR
2 meff
5
simplify by taking half the total moving mass as contributing). In practice, we might lump this inertia into
the flywheel or drive shaft for simulation simplicity, unless high-fidelity dynamics are needed.
To give a concrete example from known KPP specs: a system with a 21.6 m tall loop and 66 floaters was
described in a design document. If that system runs at a chain speed of 0.2 m/s, a sprocket circumference
of 1 m (≈0.159 m radius) would turn at 0.2 Hz (~12 RPM). The chain tension might be, say, 2000 N (if many
floaters contribute a large buoyant force), yielding . This torque
is delivered to the low-speed shaft connected to the sprocket. The drivetrain must handle this high torque
at low rotational speed, which is where the next stage (gearbox) comes in. We design the sprocket and
chain to handle peak torques (with a safety factor), meaning chain links, teeth, and the shaft are sized for
possibly thousands of N·m without yielding. Tensioners are included in the chain loop to remove slack and
ensure smooth engagement of teeth, particularly because the one-way clutch (discussed later) can cause
the chain to periodically go from loaded to unloaded. A chain tensioner or a spring-loaded idler sprocket
keeps the chain taut so it doesn’t whip when torque is removed (the simulation assumes ideal tension, but a
real system would include this).
Gear Ratio Selection and Shafting
Because the chain sprocket rotates relatively slowly (a few to tens of RPM) and the generator typically needs
to spin much faster for efficient electrical generation, a gearbox is employed. We specify a gear ratio
to step up the speed. For example, an earlier prototype referenced an overall ~39:1 ratio (taking
9.6 RPM at the chain to ~375 RPM generator). In our technical design, we allow the gear ratio to be adjusted
to suit different generator types. The gearbox could be a multi-stage arrangement (e.g., a low-speed large
sprocket to a smaller gear, then perhaps a planetary gear set) or a single-stage if the ratio is modest. For
analysis, we treat it as one equivalent ratio. The relationships are:
neglecting losses. Here is angular speed and is torque. The power is conserved (minus losses), so
ideally . The high-level design must consider gear ratio selection as a trade-off
between torque and speed: higher ratios reduce the torque on the generator and increase its speed.
Generators have optimal speed ranges (e.g., a 50 Hz alternator might want ~1500 RPM for 4-pole or ~1800
RPM for 60 Hz, unless using power electronics to decouple frequency). In the KPP, using power electronics
(inverter) allows variable speed, so the ratio can be chosen for mechanical convenience – often to ensure
the generator is in a good efficiency zone (e.g., a PM generator might be more efficient above a few
hundred RPM).
We also include efficiency factors for the gearbox. Real gears have friction and windage losses. A welldesigned
gearbox might be ~95% efficient per stage; for a multi-stage 39:1, overall perhaps 90%. We model
this as a constant fraction loss: e.g., 10% of mechanical power lost as heat. Alternatively, we can model a
constant no-load loss (bearing and oil drag) plus a load-proportional loss (to reflect gear tooth friction).
For simplicity in the simulation, we often use a single efficiency value (like 0.9) to reduce available. The
shaft linking the sprocket to the gearbox (low-speed shaft) must transmit high torque (several hundred
N·m in our example). Its design involves choosing a diameter and material to avoid excessive shear stress
or twisting. We likely use a hollow steel shaft for strength-to-weight. Similarly, the high-speed shaft from
gearbox to generator/flywheel sees much lower torque but high speed (and potentially pulsating torque if
τchain = 2000 × 0.159 ≈ 318 N\cdotpm
N =
ωgen/ωchain
ωgen = N ⋅ ωchain, τgen = ,
N
τchain
ω τ
τchainωchain = τgenωgen
τgen
6
not fully smoothed). We ensure to specify quality bearings for both shafts. Bearings introduce a drag torque
(from seals and lubrication) and a frictional loss roughly proportional to speed. For example, large roller
bearings might consume a few N·m at high speed due to oil churning. In our model, this is very small
relative to hundreds of N·m of torque, so it can be lumped into the mechanical efficiency or ignored for
simplicity. But if needed, a term like can be included (with tuned to a few N·m at
operating speed).
The gear ratio selection also affects the reflected inertia. The generator and flywheel inertia, when
referred back to the chain side, is multiplied by . Conversely, the chain and sprocket inertia referred to
the generator side is divided by . Typically, the generator’s own inertia is small compared to a purposebuilt
flywheel, but when engaged, the combined inertia seen at the chain is
. One goal in design is to have sufficient inertia on the generator side (via
flywheel) to smooth the pulses, but not so much as to make the system unresponsive or excessively stress
the floaters (too much inertia means floaters would have to do more work to accelerate it each pulse). Thus,
gear ratio indirectly influences pulse dynamics: a higher N (more speed, less torque) means the same
absolute inertia on the generator shaft reflects as much larger inertia against the chain. In our detailed
model, we allow experimenting with N and inertia to see the effect on speed oscillations.
All shafts are assumed rigid and aligned (we ignore torsional compliance in the shafts in the current model
– any twist or spring effect is small given the short lengths and high stiffness, although a torsional springdamper
could be introduced to model couplings if needed). Keyed connections or splines are used to
transmit torque through the gearbox to the generator. We also note that the one-way clutch (discussed
next) is typically placed on the low-speed shaft or at an intermediate stage, depending on design. In our
configuration, we assume the one-way clutch is between the gearbox output and the flywheel/generator, on
the high-speed shaft. This means the gear ratio is always engaged, and the clutch affects whether the
generator sees the chain’s motion or freewheels.
One-Way Clutch Configuration and Flywheel Buffering
To manage the pulsating input from the buoyant chain, the KPP drivetrain includes a one-way clutch
(overrunning clutch) and a flywheel. The one-way clutch’s mechanical configuration is such that it locks
when the drive side (chain/gearbox) tries to rotate faster than the driven side (generator/flywheel), and
slips (freewheels) when the drive side is slower. Physically, this can be a sprag clutch or roller clutch on the
high-speed shaft coupling the gearbox to the flywheel. When engaged, it effectively rigidly connects the
shafts; when disengaged, the generator shaft can spin independently (coasting) while the chain shaft might
even stop or slow. This clutch is oriented to transmit torque in the forward direction (chain driving
generator) only. If the generator/flywheel tends to drive the chain (reverse torque), the clutch opens
automatically. In steady operation, this means whenever a buoyant force pulse would accelerate the chain
above the current generator speed, the clutch locks and transfers that energy to the generator/flywheel. If
the buoyant force then drops such that the chain would decelerate below the generator speed, the clutch
disengages, preventing the generator inertia from dragging the chain backward.
The flywheel is mounted on the same shaft as the generator (or directly forms the rotor of the generator in
some designs). It is a heavy rotating disc or drum whose purpose is to store kinetic energy. Its moment of
inertia is chosen based on the degree of smoothing required. The energy stored is ; at
operating speed, a modest inertia can store a significant amount of energy due to the squared speed term.
For example, a 100 kg flywheel of radius 0.5 m (roughly ) spinning at 300 RPM (31.4
τbearing = kbearωshaft kbear
N 2
N 2
Jref = (Jflywheel +
Jgen)N +
−2 Jsprocket/chain
Jflywheel E = Jω 2
1 2
J ≈ 12.5 kg\cdotpm2
7
rad/s) stores ~6150 J. If a buoyant pulse delivers 100 J, the flywheel’s speed will change only a little
(absorbing the pulse), rather than all that energy immediately going into electrical output. In our design, we
allow the flywheel size to be specified either directly in or in terms of a smoothing factor (like a time
constant or percentage speed droop). The simulator treats the flywheel as an added inertia on the
generator shaft.
Bearing and drag considerations: The flywheel and generator share bearings which must handle the
combined weight and radial loads. There will be some friction, but since these are typically low-loss (often
air or magnetic bearings are even considered in high-end flywheels), we treat this loss as negligible or
included in generator efficiency. We also ensure the flywheel is properly enclosed for safety (as it can be a
high-speed rotating mass).
Impulse and torque buffering: When a buoyant floater is injected, a sudden torque spike enters the chain.
Without a flywheel, this would directly result in a spike of generator acceleration and potentially oscillatory
motion (or electrical power pulsation). With the flywheel-clutch system, here’s what happens step-by-step:
At the moment of a torque spike (floater rises), the chain accelerates. If this would make the chain
shaft exceed the current flywheel speed, the clutch engages. The excess torque is then transmitted
to the flywheel-generator system. Because the flywheel has large inertia, it absorbs the impulse by
accelerating slightly (its RPM increases a small amount). The generator also speeds up
correspondingly, but much less than it would without the flywheel (since now the effective inertia is
high).
Once that pulse passes (e.g., between floaters, torque might drop), the chain might have less torque
than the generator’s resistive torque. At this point, the one-way clutch disengages (freewheels). The
generator and flywheel will continue spinning on their own inertia, smoothly providing power, while
the chain is allowed to slow down slightly without dragging on the generator. Essentially, the stored
kinetic energy in the flywheel covers for the missing torque during this lull, maintaining generator
rotation.
When the next floater comes (next pulse), if chain speeds up again, the clutch re-engages and the
cycle repeats. The flywheel may speed up a bit more or recover any speed loss from the previous
interval.
This intermittent engagement is why we call it “pulse-and-coast” operation. Mechanically, the one-way
clutch experiences cyclic loading: it must lock and transmit torque during pulses and spin freely otherwise.
We ensure to specify a clutch with a high cycle life and appropriate torque rating (peak torque maybe 2–3×
average to handle spikes). The clutch also has a slight lag or slip torque threshold by nature (a tiny angular
difference between driving and driven race is needed to engage). We ignore that small nuance in
calculation, assuming near-instant lock when conditions met.
Torsional coupling: When the clutch is engaged, the chain, gearbox, flywheel, and generator are all
coupled as one rotational system. Their inertias add, and their speeds equalize. We account for this by
adding the flywheel inertia to the system’s equations of motion when engaged. When disengaged, the
chain side and generator side are separate – effectively two independent inertial systems. This conditional
coupling can be thought of as a two-state system: in state 1 (clutch engaged), and torques
equilibrate; in state 2 (clutch free), the chain and generator each spin with their own speed and only the
J
•
•
•
ωchain = ωgen
8
chain’s own frictional drag resists it. We model the transition as instantaneous for now. In a real system, the
engagement might be slightly cushioned by a compliant element or the natural slip in the clutch.
The effect on torque-speed behavior is significant. With the flywheel, the generator sees a much
smoother torque input. Imagine plotting the torque at the generator shaft over time: instead of sharp
peaks for each floater, it would hover around an average with smaller oscillations. The chain torque (input)
might spike to, say, 300 N·m for a brief moment, but the generator might only see a rise from 50 N·m to
60 N·m as the flywheel absorbs the rest by accelerating. Over a full cycle, the generator/flywheel will have
converted those absorbed pulses into a slightly higher speed, which then gradually comes down as it
delivers steady power out. We can illustrate this with a torque and speed graph:
Figure: Dynamic response of the drivetrain with flywheel smoothing. Top: Net buoyant torque at the chain sprocket
(blue curve) comes in pulses as each floater is injected (here two pulses over 8 s). The red dashed line is the
generator resistive torque (load) which is relatively constant in this example. Whenever the input torque exceeds
the generator load, the flywheel accelerates (clutch engaged). When input drops below the load, the clutch
disengages and the flywheel/generator coast. Bottom: Generator speed over the same period with (dashed line)
and without (solid line) the flywheel-clutch system. The flywheel (dashed) dramatically reduces speed fluctuations,
absorbing the pulses (note the small ~5% speed rise on each pulse) and maintaining near-constant speed between
pulses, whereas a direct-coupled system (solid) would see large speed oscillations. This behavior confirms that the
one-way clutch and flywheel effectively convert unsteady torque bursts into a smoother rotational input.
In the figure above, we see that impulse absorption by the flywheel results in minor speed changes (the
flywheel acts as a buffer), while without it the speed would vary widely. The design criterion for the flywheel
inertia is often that the speed variation (Δω/ω) is kept below a certain percentage (for power quality or
mechanical reasons). If the inertia is too low, the generator could slow down or speed up excessively each
cycle; too high and the system becomes sluggish to changes (and more costly). We aim for a compromise:
for example, a 5–10% speed ripple at most. The corresponding inertia can be computed from the expected
torque impulse ΔT and allowable Δω: . We include this calculation in our design analysis to
guide flywheel sizing.
Mechanical Losses and Inertia of Components
For completeness, we enumerate the moments of inertia and losses of each drivetrain component:
Floater Chain Assembly: As mentioned, the moving mass of floaters and chain contributes an
equivalent rotational inertia . We typically lump this into the sprocket’s reflected inertia. For
example, if 5% of the system mass (floaters + chain) is effectively accelerating with the sprocket (the
rest balanced or counterweighted by descending side), and that mass is , then
. With m and say kg (for a large system with many floaters and
heavy chain), could be ~ . This is substantial and
comparable to a flywheel’s inertia, meaning the chain itself provides some natural smoothing (a
heavy chain won’t accelerate instantly). However, much of this inertia is continuously lifted (so not all
contributes to rotation due to gravity coupling), so we use an effective value that our simulation can
calibrate by energy equivalence.
Sprocket and Low-Speed Shaft: The sprocket is typically a steel wheel, perhaps 1 m diameter, but
much of its mass is near the rim (teeth and a thick rim to engage the chain). Its inertia might be on
Jrequired ≈ Δω
ΔT ⋅Δt
•
Jchain
M Jchain ≈
0.05MR2 R = 0.15 M = 1000
Jchain 0.05 × 1000 × 0.152 = 11.25 kg\cdotpm2
•
9
the order of 2–5 kg·m². The low-speed shaft adds a small inertia (solid steel shaft, diameter maybe
50 mm, length 1 m yields ). We include these but they are minor compared to
chain and flywheel.
Gearbox: The gears themselves rotate; the largest gear (attached to the sprocket shaft) could add
some inertia (gear of radius ~0.3 m, mass few tens of kg -> ). Gears on the highspeed
side have negligible inertia once reflected back (divided by ). We account for gear inertia if
needed, but often combine it with the shafts they are on.
High-Speed Shaft and Couplings: These are lighter and smaller radius, so inertia is very low. We
might ignore them.
One-Way Clutch: It has internal elements (sprags/rollers), but these are small. Friction in the clutch
appears when overrunning, but it’s minimal (maybe a few N·m drag when freewheeling). We include
a tiny drag when clutch is disengaged to avoid having the generator run indefinitely in simulation (a
real generator would have iron and windage losses providing drag anyway).
Flywheel: As discussed, its inertia is the main tuning parameter. We might assume a value, e.g.,
for a moderately sized system, or more for large smoothing. This can be
a solid steel disc of certain dimensions (for reference, a 1 m diameter, 50 mm thick steel disc ~
(radius 0.5 m, mass ~154 kg) has . So
achieving would need smaller or lighter disc, or composite high-density rim designs). We can
specify the flywheel geometry if needed (rim and hub style for maximizing inertia per mass).
Generator Rotor: The generator’s rotor (with magnets or windings) also has inertia. If it’s a 500 kW
class machine, its rotor could weigh hundreds of kg but radius maybe 0.3–0.5 m. Rough guess
. It’s smaller than a dedicated flywheel typically. When the clutch is engaged,
adds to to resist acceleration; when disengaged, it is just part of the coasting mass.
Bearing drag and windage: Summing up all rotating components, we usually budget a constant loss
torque for miscellaneous frictions. For example, at nominal speed, total passive losses might be 1% of rated
torque. If rated torque at generator is, say, 100 N·m (for 500 kW at 5000 RPM, hypothetically), 1% is 1 N·m
friction. At lower speed (375 RPM, torque ~12.7 kN·m on low-speed side in our earlier example), 1% is
~127 N·m, which seems high for friction. In practice, friction is more or less proportional to speed and not
that large; our 1% was an oversimplification. Instead, we might set a fixed mechanical loss of a few hundred
watts (which at low speed is quite small torque, and at high speed is moderate). For example, 500 W loss at
375 RPM corresponds to torque . So on the low-speed
side that’s only ~4 N·m after gear reduction (if 39:1). We incorporate something along these lines so that
even when not producing power, the system will eventually coast down due to these losses.
In conclusion, the drivetrain mechanics are designed to efficiently transmit power from the buoyant force
to the generator, while smoothing out the pulsations using the clutch and flywheel. Equations for torque
conversion, gear ratio, and moment of inertia transformations are included in our model to capture how a
sudden force on the chain results in a gradual change in generator speed. By analyzing torque-speed
graphs and impulse response, we verify that the chosen flywheel and clutch configuration indeed buffer the
energy: short, high-torque impulses are spread out as smaller changes in rotational kinetic energy, yielding
J < 0.1 kg\cdotpm2
•
J ∼ 1 kg\cdotpm2
N 2
•
•
•
Jflywheel = 5 kg\cdotpm2
J = 1/2MR2 ≈ 1/2 ⋅ 154 ⋅ 0.52 ≈ 19.25 kg\cdotpm2
J = 5
•
Jgen ≈ 2 kg\cdotpm2
Jgen Jflywheel
T = P /ω ≈ 500/(2π ⋅ 6.25) ≈ 12.7 N\cdotpm
10
a near-steady generator output. The next section will detail how the control system actively manages this
process to ensure optimal performance and protection of the mechanical components.
Control of Mechanical Systems
Clutch and Flywheel Engagement Logic
The mechanical clutch-flywheel system, while largely passive in operation, is overseen by a control logic that
monitors speeds and torques to determine engagement state. We model this as a simple two-state state
machine: ENGAGED (clutch locked) and DISENGAGED (clutch open). The transition conditions are based on
the relative speed of the chain vs. the generator, or equivalently the torque direction:
ENGAGE when the chain tends to accelerate the generator: formally, if (i.e. the chain
shaft is trying to turn faster than the generator shaft), then engage the clutch. In practice, we
implement this by checking if the instantaneous net buoyant torque on the chain (after gearbox)
exceeds the generator’s electromagnetic resisting torque. If , that excess
will cause acceleration, so the clutch should lock to transfer power to the flywheel/generator. This
typically happens at the moment of a floater injection or when multiple floaters are concurrently
producing an above-average force. The controller might add a slight hysteresis or threshold to avoid
rapid chattering (e.g., require to exceed by a tiny fraction, or torque exceed by a few N·m,
before locking).
DISENGAGE when the generator would otherwise slow the chain: if , meaning the
chain is turning slower or its torque drops below what’s needed to maintain generator speed, then
release the clutch. In torque terms, if , the generator would begin to drive
the chain (which we don’t want), so we disengage so that the generator instead draws from the
flywheel’s inertia. Upon disengagement, the chain is effectively no longer loaded by the generator, so
any shortage of torque just results in the chain slowing slightly (which corresponds to floaters not
rising as quickly momentarily, but since they are continuous, this is acceptable). The control ensures
no negative torque is transmitted back to the chain – this is crucial for avoiding the scenario where
the heavy generator could pull floaters downward, undoing their work.
We do not typically need an active actuator for this clutch; a mechanical overrunning clutch handles it.
However, in the simulation and concept, we treat it as if a controller is “deciding” engage/disengage based
on sensor input because it helps in understanding system states. We simulate sensor inputs: a chain speed
sensor (e.g., a rotary encoder on the sprocket) and a generator speed sensor (encoder on the generator
shaft). The controller continuously compares these speeds. It may also use a torque sensor or estimator
on the chain shaft to more directly apply the torque condition logic. Modern control systems could even
infer chain torque from motor current if it were motor-driven, but here it’s passive. So practically, we rely on
speed comparison as our condition.
We can describe the logic in pseudo-code form:
if (omega_chain >= omega_gen + epsilon) and clutch_state == DISENGAGED:
clutch_state = ENGAGED
• ωchain > ωgen
τchain, after gear > τgen, load
ωchain ωgen
• ωchain < ωgen
τchain, after gear < τgen, load
11
if (omega_chain < omega_gen - epsilon) and clutch_state == ENGAGED:
clutch_state = DISENGAGED
where epsilon is a small tolerance to prevent chattering. This effectively mirrors the overrunning clutch
behavior. In engaged state, we set the system equations to couple the inertia and apply torque to the
generator. In disengaged, we decouple them.
The controller also monitors for certain fault conditions: overspeed of the flywheel/generator (if the
flywheel accelerates too much due to consecutive pulses without load, the controller might apply an
emergency electrical load or even a brake to prevent damage). Similarly, if a very large unexpected torque
occurs (perhaps a floater stuck or an impact), the clutch might protect the system by disengaging if the
speed reversal is detected. We can incorporate a rule like: if exceeds a threshold or changes too
rapidly, or if chain tension spikes beyond a limit, disengage clutch to isolate the generator. These are
protective measures beyond normal operation (acting like a torque limiter).
In summary, the clutch control logic is simple and primarily based on speed matching. We use the state
machine concept to analyze and verify that at any given time the system is in the correct state. During each
simulation timestep, we update:
Compute (from chain position or previous step plus accel).
Compute (previous gen speed plus any accel from flywheel torque).
If tends to exceed , set clutch = ENGAGED (and enforce thereafter in that
step).
If would fall below (meaning generator inertia is driving it), set clutch = DISENGAGED.
Apply torques accordingly: in engaged mode, transfer as much torque as needed (up to available) to
accelerate generator; in freewheel mode, zero torque is transferred (chain side torque goes to
accelerating/decelerating chain only, generator runs on flywheel inertia).
By simulating this, we saw qualitatively the behavior: smooth generator rotation with minor blips, proving
the control logic achieves the desired outcome.
Generator Load and Torque Control (FOC)
The generator in KPP is likely a synchronous or permanent magnet machine feeding power to the grid or an
inverter. We incorporate an active generator torque control system, typically implemented via Field-
Oriented Control (FOC) in the inverter. FOC allows us to control the generator’s electromagnetic torque
output by adjusting the currents in the stator in real-time, decoupling torque production from flux. In
simpler terms, the inverter can act like a programmable brake on the generator: we can command a certain
torque (or power) and the inverter will drive currents to achieve it, regardless of generator speed (within
design limits).
The control strategy for the generator has a few possible modes:
Speed-regulation mode (grid frequency lock): Here, the controller tries to hold the generator at a
target speed (which corresponds to a target frequency if directly grid-tied). If the KPP is meant to
deliver constant frequency AC, this mode is essential. The controller measures the generator speed
(or grid phase) and increases or decreases torque to maintain the speed. For example, if the
ωgen
• ωchain
• ωgen
• ωchain ωgen ωchain = ωgen
• ωchain ωgen
•
•
12
generator starts to speed up (perhaps because a strong buoyant pulse came and the flywheel
couldn’t absorb all of it), the controller will increase electrical torque (draw more current, more
power) to counteract the acceleration. Conversely, if the generator tends to slow (during a lull), the
controller will decrease electrical load to let the flywheel’s inertia keep it spinning. This is analogous
to a governor on a turbine – it maintains stable RPM by modulating load. We can implement a PID
control on speed: etc. By tuning this, we ensure small speed
deviations result in corrective torque adjustments. The net effect is that the generator “sees” an
approximately constant speed, and any excess energy from pulses is immediately converted to
electrical output (preventing large speed rise) – effectively the flywheel and generator share the
smoothing task. In our simulation, we allow an option for “constant speed mode” which mimics this.
If enabled, the output power will fluctuate instead (since the controller is taking in the pulses as
extra electrical power). If disabled, we run “passive mode” where the generator has a fixed resistive
torque and speed is allowed to vary with the flywheel (which was the scenario we illustrated earlier).
Torque (or Power)-regulation mode: We can also set the generator to draw a fixed torque (or a
torque that follows a predefined schedule). For instance, a simple approach is to apply a constant
electromagnetic torque that equals the time-averaged torque from buoyancy. This yields a steady
power output on average, and the flywheel will handle deviations. In this mode, speed will vary
slightly around the setpoint (this is the passive mode in the simulator context). The advantage of
torque-control is it’s simple and can be optimal for energy capture (like maximum power point
tracking in renewables). The downside is the generator speed may wander, which if connected to a
grid, requires decoupling (hence usually an inverter is needed to allow variable speed with constant
frequency output).
Given the KPP likely uses an inverter to deliver power (since the concept allows variable speed), we have
flexibility. We can hold speed near constant for grid sync, or let it vary for possibly better efficiency and less
mechanical stress.
FOC implementation: In either case, an FOC or similar vector control will take the torque command and
regulate the d-q axis currents in the generator. The controller will monitor the generator’s current and
voltage, and use a resolver or encoder for rotor position to align the currents properly. This runs at a high
bandwidth (kHz), much faster than the mechanical changes, so effectively the electrical torque can be
considered an instantly controllable input from the perspective of mechanical dynamics.
We model the generator’s effect as a controlled torque source opposing the rotation. For example, if the
user sets a generator load of 10 kW at a certain speed, the controller will apply a resisting torque
(adjusted for efficiency). If speed changes, either power changes or torque is adjusted depending on mode.
In speed-control mode, we adjust torque to hold speed; in torque-control mode, we hold torque constant
regardless of speed (so power will vary as ). We may also implement a power limit – e.g., if too
many floaters push at once, the mechanical input could exceed generator rating. In that case, the controller
could intentionally let speed rise (storing in flywheel) or dump the excess into a braking resistor if the
inverter can’t feed it to the grid (our simulation can flag an overload event instead). Conversely, if input is
low, the controller might lighten the torque to avoid excessive slow-down.
Balancing float-derived torque: The ultimate goal is to balance the generator’s electromagnetic torque
with the average mechanical torque from the floaters such that the system runs at steady state. If
perfectly balanced, the flywheel will neither speed up nor slow down on average – all buoyancy input goes
ΔTgen = Kp(ωtarget − ωgen) +…
•
T = ω
P
P = T ω
13
straight to electrical output minus losses. The controller might implement a slow outer loop to adjust the
target torque or speed to achieve this balance. For example, if over several cycles the flywheel’s speed is
creeping up, it means input > output; the controller can increase load slightly to draw more power. If speed
is trending down, output > input; reduce load. This is analogous to frequency-droop control or MPPT logic.
We can simulate this by having the controller monitor the flywheel speed and maintain it around a setpoint
by trimming generator load.
Sensors involved here include the speed sensors and possibly a torque or current sensor for the generator.
In a real system, generator current is measured and controlled, and speed is measured. Floater position
sensors might not directly affect generator control, but the system could anticipate pulses. For instance, if a
floater injection is about to happen (known from position), a smart controller could momentarily lower the
generator torque just as the pulse hits, allowing the flywheel to absorb more, then ramp up torque to
extract that energy smoothly. This is an advanced strategy that could reduce peak stress. Our design
mentions this as a possibility: since we can predict when pulses occur (the cycle is known), we could
implement feed-forward control that schedules clutch engagement and slight generator torque
modulation in sync with the pulses. However, given the one-way clutch automates engagement, the main
feed-forward opportunity is adjusting generator load before a pulse. For example, just before a floater is
injected, the controller could reduce the generator’s resisting torque a bit (allowing the flywheel to speed up
easier), then after the pulse, increase torque to recover the energy. This effectively mimics what the passive
system does naturally, so the benefit might be minor if the flywheel is properly sized. Nonetheless, it could
fine-tune power quality.
Sensor Integration and State Machine Control
Our control system uses a combination of sensor inputs to decide on states and control actions:
Floater Position Sensors: These could be limit switches or optical sensors at the bottom and top to
detect a floater’s presence. When a floater is detected at bottom, the controller commands the
injection valve to open for the preset duration (as discussed in the pressure exchanger section).
Similarly, a top sensor triggers venting if an active mechanism is needed (often top venting can be
passive). Additionally, by knowing the index of the floater, the controller can infer where all other
floaters are (if evenly spaced). This gives a periodic cue for timing pulses. The position information is
primarily used for pneumatic control (valves), but as noted, it can be used to anticipate mechanical
loading changes as well.
Chain Tension/Torque Sensor: A strain gauge on the chain or a torque transducer on the sprocket
shaft can provide real-time measurement of . In our simulation, we compute this from physics,
but a real controller might use this to detect how many floaters are currently providing force. We can
use this signal to decide clutch engagement in lieu of speed: e.g., if chain torque rises above
generator torque, that implies a positive acceleration tendency (so engage clutch). It correlates with
our speed logic. A sudden drop in chain torque might cue a disengagement event if not already
detected by speed. Tension sensors can also serve for safety (detect overload conditions, jammed
chain, etc., and trigger shutdown if necessary).
Shaft Speed Sensors: As described, encoders on both chain drive and generator are crucial. These
provide the primary input to the clutch logic (speed comparison) and also feed the generator torque
control loop (for either maintaining speed or calculating power output). The resolution of these
•
•
τchain
•
14
encoders should be high enough to detect small speed differences quickly, ensuring prompt clutch
control. In an overrunning clutch, the engagement actually happens automatically without electronic
input, but if we have a secondary clutch or brake that could override, the controller would actuate it
based on these sensors.
Generator Electrical Sensors: The inverter will measure currents and voltages from the generator.
From these, it can estimate/compute the electromagnetic torque (for a PM synchronous machine,
, where is quadrature axis current). We effectively use these to implement our torque
control. The controller’s software “knows” the commanded torque and can cross-check actual current
to ensure it’s achieved.
Flywheel Speed (if separate from gen): If the flywheel is directly on gen shaft, one sensor covers
both. If not, we’d measure it too. We assume it’s on the same shaft here.
All these sensors feed into a control algorithm that can be represented as a flow diagram with states:
Monitor phase (continuous): Read , , chain torque , etc.
State decision: If clutch currently disengaged and (or ), transition to
ENGAGED. If clutch engaged and , transition to DISENGAGED.
Apply control: In ENGAGED state, couple inertias and allow torque flow. In DISENGAGED, separate
them.
Generator torque control: Regardless of clutch state, set generator torque according to mode. In
speed mode, use speed error to adjust . In torque mode, keep constant (or follow a
predefined vs. speed curve if simulating something like a MPPT or droop).
Injection control: Separately, check bottom sensor – if floater present and not currently air-filled,
open valve for injection duration. Check top sensor – if floater present and air-filled, open vent (or
just mark it as water-filled).
Safety checks: If any sensor indicates an anomaly (overspeed, overtorque, etc.), override controls:
e.g., disengage clutch, cut injection, apply brakes, etc.
This loop runs continuously (in simulation, each time step ~10–50 ms; in real hardware, maybe faster for the
electrical control portion, and slightly slower for the mechanical logic if needed).
The synchronization of buoyant pulses is thus achieved inherently: the floater cycle provides pulses at
regular intervals (say one pulse every few seconds). The clutch engagement is automatically synchronized
to these because it responds to the torque/speed conditions they create. However, the controller can
enhance synchronization by anticipating them. Knowing the time or chain length between floaters, it can
predict when the next pulse will occur. We could schedule the generator control to slightly lower resistance
just before that time, as discussed. The state machine could have a predictive state like “PULSE INCOMING”
a short moment before a known injection event, then “PULSE ACTIVE” during the floater’s rise, then “COAST”
after. But since the mechanical clutch responds so quickly, our design currently doesn’t require explicit
predictive action – it’s handled by feedback.
One area where synchronization is critical is in the pneumatic injection relative to chain motion
(addressed earlier): the controller ensures that injection happens only when the floater is aligned, otherwise
air might be wasted or injected at the wrong time. That is a timing synchronization. Mechanically, we also
•
T ≈ ktIq Iq
•
1. ωchain ωgen Tc
2. ωchain > ωgen Tc > Tgen
ωchain < ωgen
3.
4.
Tgen Tgen
5.
6.
15
ensure that multiple floaters don’t accidentally get injected simultaneously due to timing jitter – the control
prevents opening more than one injector at once, unless the system is designed for multi-floater injection.
Power Electronics and Generator Control
In modern KPP implementations, the generator is grid-connected via a power electronics converter (AC/DC/
AC likely). This provides a high level of control over generator torque and also decouples generator speed
from grid frequency. Our design includes a Vector Control Unit as part of the controller, which takes the
torque command determined by the higher-level logic and translates it into current commands for the
inverter. We assume the existence of a DC bus or some energy storage to smooth power if needed (since
pulses will cause power surges). The inverter could either feed into the grid or a load. The torque control
via FOC works as follows: measure rotor position (θ) via encoder, transform measured currents to d-q
frame, use PI controllers to regulate q-current to demand (for torque) and d-current to 0 (for field
weakening or unity power factor as desired). The output are voltage commands that the PWM converter
applies to the generator. This runs typically at a few kHz, keeping electrical dynamics much faster than
mechanical.
We incorporate a simplified model: . The controller sets based on desired
torque. The generator also has a torque limit (max current) and we include an efficiency (say 95%). We
compute electrical output power as . If we simulate the grid connection, we might also
compute an AC frequency. For example, if we maintain 375 RPM, we might call that 50 Hz output (assuming
a certain pole count). Since an inverter ultimately would regulate frequency, we won’t delve into that, but it’s
worth noting in a real system, the inverter would output perfect 50/60 Hz regardless of generator speed, as
long as it controls torque to manage speed.
The generator control thus acts to balance the mechanical torque: in steady state, average generator
torque equals average chain torque (minus losses). If H3 (flywheel/clutch) is active, that average is over a
cycle and the flywheel buffers the difference within the cycle. If H3 were disabled (a scenario we can
simulate), then the controller alone would have to handle the pulsating torque – which would mean either
the generator experiences oscillating torque (if torque mode) or oscillating speed (if speed mode) or the
controller tries to counteract each pulse (which could lead to very dynamic power output). The combination
of both the mechanical and electrical control yields the smoothest result: the mechanical side filters the
fastest, largest pulses, and the electrical side takes care of maintaining long-term stability and fine control.
Finally, we ensure that the control system is robust: multiple feedback loops (speed loop outside, current/
torque loop inside) are tuned so the system is stable. The state machine for clutch has hysteresis to avoid
rapid switching if operating near the threshold. And sensor inputs are filtered to avoid noise triggering false
state changes. The result is a coordinated system where buoyant energy is maximally harnessed – each
floater’s work is either immediately converted to electricity or temporarily stored in the flywheel to be
released a moment later, with minimal loss. We continuously monitor key parameters: floater positions (for
proper timing), chain torque (for overload or slack conditions), flywheel speed (for overspeed), and
generator load (for power output and potential overcurrent). The control system will alert or intervene if,
say, net output becomes negative (meaning compressor load exceeds generation – the system would then
eventually slow and stop) or if thermal limits are reached (not covered in detail here, but e.g., if water
temperature drops too much due to repeated H2 usage, which could be sensed and then injection strategy
altered).
Tgen, electromagnetic = k ⋅ iq iq
ηgen
Pe = τgenωgenηgen
16
In summary, the control of mechanical systems in KPP uses a blend of passive mechanical design (oneway
clutch) and active electronic control (generator inverter). The one-way clutch ensures that
mechanical power flows in the correct direction and automatically synchronizes with the buoyant cycle. The
flywheel provides inertia to smooth short-term fluctuations. On a slower timescale, the generator’s torque is
actively modulated to maintain stability and deliver usable electrical output. State machine models make it
easy to reason about the system: for each phase of the floater cycle (injection impulse vs coasting interval),
the controller’s state and actions are well-defined. By mapping these states to simulation code, we can
implement and test various scenarios (e.g., turning off H3 to see unsmoothed output, or varying flywheel
size, or switching control modes) and verify the system behaves as expected. The integrated control
approach keeps the KPP running efficiently and protects it from transient shocks, ultimately contributing to
a higher net output and a stable, controllable power supply.
17