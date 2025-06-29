Detailed Plan for Enhancing the KPP Simulation’s
 Realism and Performance
 1. Clarification of Approach and Key Suggestions
 What “robust single-client realism” means: We should focus on making the physics simulation itself as
 accurate and stable as possible for one user/session, without worrying about multi-user or distributed
 complexity at this stage. In practice, this means restructuring and patching the existing code so that all
 physical forces and processes in the KPP system are modeled correctly, and the simulation runs in real
time with a single client (e.g. one Flask server instance and one browser) receiving the data stream.
 What we suggest doing: The core suggestion is to upgrade the backend physics engine of the simulator
 for correctness and efficiency. This involves: 
• 
• 
• 
Converting any one-off or static calculations into a proper time-stepping simulation loop (if not
 done already). This loop will update the system state in small time increments, capturing dynamic
 behavior over time
 1
 3
 4
 2
 . This ensures realism (objects accelerate, move, and interact
 continuously, rather than via a single static calculation). 
Including all relevant forces and torques in the model. We need to double-check that buoyant
 force, gravity, drag, and any friction or load forces are all calculated and applied at each time step
 . Any missing physics will be added so the science is correct. For example, ensure we
 compute buoyancy via Archimedes’ principle and drag via the drag equation for each floater ,
 and include gravity (weight) and any other mechanical resistances.
 Mapping and state management for floaters: Represent the multiple floaters and their positions
 around the chain loop, rather than just a single object. This means each floater’s state (air-filled or
 water-filled), position (along the loop), and velocity will be tracked. We will implement logic
 (“handlers”) to swap a floater’s state at the correct moments – injecting air at the bottom and venting
 at the top
 7
 8
 5
 6
 . This ensures the buoyancy cycle (heavy going down, light going up) is simulated
 9
 • 
• 
realistically .
 Integrating the mechanical and electrical components: Incorporate a model for the drivetrain
 and generator so that the force imbalance turns into shaft torque and electrical power. The
 simulation should include a torque from the generator (a resistive load) opposing the motion .
 We also account for the energy input by the air compressor during injection – while this doesn’t
 directly apply a force on the chain, we will log the compressor’s energy consumption to evaluate net
 energy. (As noted in the feasibility analysis, the work to compress air at depth fundamentally
 exceeds the buoyant work obtained without special tricks
 science honest.)
 8
 10
 , so we must track that to keep the
 Optimizing performance: Ensure the new loop and calculations are efficient for real-time use. This
 might involve choosing a reasonable time step, using numpy for vectorized operations on multiple
 f
 loaters, and structuring the code cleanly so it can run smoothly in a Flask route without blocking.
 We’re effectively creating a lightweight physics engine specialized for the KPP. Since we’re focusing
 1
on a single client, we don’t need complex concurrency – a simple loop (possibly running in a
 background thread or via SSE streaming) will suffice.
 In summary, we suggest refactoring the simulator into clear modules (physics calculations, simulation loop,
 event handlers) and adding any missing physics so that the single-client simulation is both physically
 accurate and performs in real-time**. Next, we break down the specific steps to achieve this.
 2. Ensuring a Robust Single-Client Realistic Simulation
 At this stage, we limit the scope to one simulation instance (one client). This means we can simplify certain
 aspects like thread synchronization or multiple simultaneous simulations, and instead concentrate on
 making the one simulation loop robust and correct. Key actions in this regard:
 • 
• 
• 
• 
Use a continuous simulation loop: If not already implemented, the Flask backend should run the
 simulation in a loop that increments time in small steps (
 2
 11
 dt ). This can be done within a route (using
 Server-Sent Events to stream results) or in a background thread started by a route. The Stage 1 guide
 already proposed a pattern for this loop . We will adopt that, making sure it runs indefinitely
 (or until a set end time) and yields data at each step. This ensures the client sees a smooth, real-time
 progression of the simulation rather than just an instantaneous result.
 No multi-client complications: We will assume only one client is receiving the data, so we don’t
 need to handle multiple simultaneous SSE streams or locking on the simulation state. The single
 loop can continuously update the state and stream data without interference. This keeps things
 simple and “robust” because we avoid race conditions or inconsistent states across clients. The code
 should, however, be structured to easily allow future extension to multiple clients (for example, by
 using thread-safe data or copying state for each client if needed, but this we can defer).
 Responsive parameter handling for one user: In a single-client setting, if the user changes a
 parameter (like toggling a hypothesis or changing a slider), we can safely update the simulation
 parameters on the fly. The Stage 2 design suggests having a 
13
 /set_params endpoint for this
 . We should ensure that our simulation loop reads the latest parameters each iteration (or
 whenever they change). For now, focusing on realism, we might not implement full interactive
 control, but we should design the code so that all key parameters (number of floaters, float
 volume, water depth, drag coefficient, load torque, etc.) are centralized and can be modified
 easily. This can be done by storing them in a dictionary or a small config object that the simulation
 loop references on each cycle.
 Time-step selection: To balance realism and performance, choose a suitable 
smaller 
12
 dt (time step). A
 dt (e.g. 0.01 s) improves accuracy in the physics integration but uses more CPU, whereas a
 larger 
dt (e.g. 0.1 s) is faster but might miss quick events (like the instant of injection) or cause
 instability. We might start with 0.1 s for basic testing, and if the motion is fast or the results seem
 rough, refine to smaller steps. Because it’s a single client on a local machine, performance should be
 manageable even at reasonably fine time steps (the physics is not too heavy with a modest number
 of floaters). We can make 
14
 15
 dt configurable via the input form. For stability, we’ll use simple Euler
 integration first (as shown in Stage 1 ), but note that if the simulation becomes stiff or
 oscillatory, we might consider a more stable integration (like semi-implicit Euler or a small Runge
Kutta). Initially, Euler is acceptable given small dt and the desire to keep it simple.
 2
• 
Testing the loop with one client: We should test the patched simulator with one web client to
 ensure that it streams data correctly and doesn’t crash or freeze. This includes verifying that the
 Response with 
16
 text/event-stream is set up properly and that the browser receives updates.
 If any performance issues arise (like the loop computation taking longer than real time), we may add
 a small 
time.sleep() or adjust dt to effectively throttle to real-time. Since we’re focusing on a
 single client, we can even allow a slight overspeed if needed (the client will just receive data faster
 than real time). The main point is that the simulation should be robust – i.e., it should run to
 completion (or indefinitely) without numerical errors or crashes, and handle edge cases (like what
 happens when all floaters become balanced, or if the user inputs extreme values).
 By solidifying the single-client loop and physics, we establish a strong foundation. Next, we ensure the
 physical realism of the simulation, which is the core scientific aspect.
 3. Prioritizing Physical Realism and Scientific Accuracy
 At this stage, we want the science to be correct – meaning our simulation should reflect real physical laws
 for the KPP system. We will implement all relevant equations and processes so that the behavior is realistic.
 Here’s our plan for ensuring physical realism:
 3.1 Accurate Force Calculations for Each Floater
 Each floater experiences several forces as it moves through the water: buoyant force, gravitational force,
 and drag force (and possibly frictional forces if any). We need to calculate these correctly:
 • 
• 
17
 Buoyant Force (Upward): We apply Archimedes’ principle: the buoyant force $F_B$ equals the
 weight of the displaced fluid. For a floater of volume $V$ in water of density $\rho_{\text{water}}$, $
 $F_B = \rho_{\text{water}} \cdot V \cdot g,$$ directed upward . This formula assumes the floater
 is fully submerged. In our simulation, floaters will always be submerged in the tank (except possibly
 slight emergence at the very top, which we can ignore or handle later), so we use the full volume for
 buoyancy. Example: If $V = 0.04~\text{m}^3$ (40 liters) and $\rho_{\text{water}}=1000~\text{kg/m}
 ^3$, then $F_B \approx 1000 \cdot 0.04 \cdot 9.81 \approx 392~\text{N}$ upward . We will use a
 realistic density (1000 kg/m³ for water) and $g=9.81~\text{m/s}^2$. (If needed later, we can refine $
 \rho_{\text{water}}$ as a function of temperature or nanobubble content for H1/H2 effects, but by
 default use standard density.)
 18
 Gravitational Force (Weight, Downward): Each floater has weight $F_W = m \cdot g$, directed
 downward. Here $m$ (mass) of a floater will change depending on its state:
 • 
• 
When the floater is filled with water (“heavy” state), its mass $m_{\text{heavy}} = m_{\text{container}}
 + m_{\text{water inside}}$. If the container’s internal volume is $V$, then $m_{\text{water inside}} =
 \rho_{\text{water}}\cdot V$. The container itself has some dry mass (material, perhaps metal or
 plastic). We’ll use a parameter for the container’s empty mass. For example, if the container weighs
 20 N in air (~2 kg), that’s $m_{\text{container}}\approx2~\text{kg}$. The water filling 40 L would be
 $40~\text{kg}$. So $m_{\text{heavy}}\approx42~\text{kg}$.
 When the floater is filled with air (“light” state), its mass $m_{\text{light}} = m_{\text{container}} +
 m_{\text{air inside}}$. Air mass is negligible (0.04 m³ of air is about 0.05 kg at STP, slightly more at
 3
pressure, but still small compared to water). We can approximate $m_{\text{air inside}}\approx0$ for
 simplicity. So $m_{\text{light}}\approx m_{\text{container}}$ (≈2 kg in the example). We will store or
 compute each floater’s mass based on state, and then weight force $F_W = m \cdot 9.81$. 
• 
• 
• 
• 
• 
• 
Buoyancy vs Weight: Note that in heavy state, the floater’s weight is largely canceled by buoyancy
 of the water it displaces – effectively the net force due to weight and buoyancy for a full-of-water
 f
 loater is about the weight of the container itself (since the water’s weight = displaced water’s
 buoyant force). In light state, buoyancy hugely exceeds the floater’s weight (since we removed that
 water mass), yielding a strong upward net force . Our simulation will capture this by updating the
 mass and re-calculating forces whenever the floater changes state.
 9
 Hydrodynamic Drag (Resistive force opposite motion): As floaters move through water, drag will
 oppose their motion, slowing their ascent or descent. We will implement the drag force using the
 quadratic drag equation
 6
 : $$F_D = \frac{1}{2} C_d \, \rho_{\text{water}} \, A \, v^2,$$ where:
 $C_d$ is the drag coefficient (dimensionless). We will use a reasonable estimate (e.g. $C_d \approx
 0.8$ for a rectangular container, but this can be a user input).
 $A$ is the cross-sectional area of the floater moving through water (projected area in the direction of
 motion). If the floater is oriented broadside as it moves, $A$ could be roughly the front area of the
 container. We can set this based on geometry (for instance, if a 40 L container is roughly a cube of 40
 L volume, one side area might be ~0.2 m²). This too can be parameterized.
 $v$ is the relative velocity of the floater through water. In our case, since the water is static and only
 the floater moves, $v$ is the floater’s velocity. Drag acts opposite the direction of motion. So for an
 ascending (light) floater (moving up), drag is downward; for a descending (heavy) floater (moving
 down), drag is upward. We must account for this in our force balance. We’ll calculate $F_D$ for each
 f
 loater and apply it with the correct sign.
 Other forces: At this stage, we might ignore minor forces like added mass (inertia of water) or
 viscous damping beyond drag. However, one force to consider is mechanical friction in the system
 (e.g. friction in bearings or between chain and guide). This is not mentioned explicitly in the
 documents, but for completeness, we could include a simple friction model (like a constant friction
 torque or a percentage of the load). Since we want scientific accuracy, we might set this to zero or a
 very small value initially (assuming a well-lubricated system), unless empirical data suggests
 otherwise. We will, however, include generator resistance as a torque (discussed later) which is
 effectively another force opposing motion.
 Implementing the force calculations in code: We can create or update functions (or methods) to compute
 these forces. For clarity and extendability, it’s useful to encapsulate this in a 
Floater class. Each
 Floater object can have a method to compute its current forces given the current velocity (and perhaps
 global parameters like water density). For example:
 class Floater:
 def __init__(self, volume, container_mass, Cd, area, initial_angle,
 state="heavy"):
 self.volume = volume
 # m^3
 self.container_mass = container_mass # kg
 4
self.Cd = Cd
 self.area = area
 self.angle = initial_angle
 self.state = state
 # Initialize mass based on state
 if state == "heavy":
 self.mass = self.container_mass + (1000 * volume) # water mass 
# drag coefficient
 # cross-sectional area in m^2
 # angle (or position) along the loop
 # "heavy" or "light"
 inside
 else:
 self.mass = self.container_mass # air mass negligible
 self.buoyancy = 1000 * volume * 9.81
 # constant buoyant force magnitude (N)
 self.velocity = 0.0 # velocity along the loop (m/s), will be set by 
chain
 # Note: position along loop can be derived from angle and tank geometry 
if needed
 def compute_forces(self):
 # Gravitational force
 weight = self.mass * 9.81 # N, downward
 # Buoyant force (upward)
 F_buoy = self.buoyancy
 submersion)
 # Drag force (opposes motion)
 v = self.velocity
 F_drag = 0.5 * 1000 * self.Cd * self.area * (v ** 2)
 # Now determine net force direction for output:
 if v >= 0: # moving upward (ascending)
 # Upward velocity means this floater must be light (should be 
"light" state ideally)
 # Drag is downward, opposing upward motion
 F_net = F_buoy- weight- F_drag
 else:
 # (we treat buoyancy as constant for full 
# moving downward (descending, v < 0)
 # Downward velocity (negative v) means floater is heavy
 # Opposing drag acts upward (opposite to motion), which in this case opposes 
weight
 F_net = weight- F_buoy- F_drag
 return F_net
 In this snippet, we assume upward motion (
 v >= 0 ) corresponds to a light floater (buoyant, so buoyancy
 > weight typically) and downward motion corresponds to a heavy floater. The net force 
F_net is calculated
 accordingly. We’ll use this in the simulation loop. (Note: We use 
1000 kg/m³ for water density directly here
 for simplicity; in practice, make it a parameter 
rho_water in a config so that H1 effects or temperature
 can adjust it.)
 5
3.2 Coupling Floaters via the Chain (Constraint Dynamics)
 In a real KPP, all floaters are attached to a chain or belt, meaning they are not free to move independently 
they move in unison, like cars on a conveyor. This is a crucial physical constraint: the velocity of every
 f
 loater is the same at a given moment (aside from direction flips around the loop). Ascending floaters and
 descending floaters share the same speed magnitude (one up, one down), because they are linked by the
 chain. We must represent this in our simulation; otherwise, we might erroneously let floaters move at
 different speeds or pass each other, which would be unphysical.
 To implement the chain constraint and resulting dynamics: - We introduce a global rotational coordinate
 for the chain loop. For example, let $\theta$ represent the rotation angle of the chain (or equivalently the
 position of the chain along the drive sprocket). Incrementing $\theta$ advances all floaters along the loop.
 We can also work in terms of linear distance along the loop, but angle is convenient if we know the sprocket
 radius $R$. - The chain imposes that all floaters move at the same chain speed. We maintain a single
 angular velocity $\omega$ (or linear velocity $v_{\text{chain}}$) for the entire loop. Each floater’s velocity
 will be derived from this chain velocity. For instance, $v_{\text{floater, upward}} = \omega R$ upward, and
 $v_{\text{floater, downward}} = \omega R$ downward (if we define $\omega$ such that positive $\omega$
 corresponds to floaters moving up on the ascending side). - We ensure that in the code, we do not
 integrate each floater’s motion separately with its own acceleration (which would decouple them).
 Instead, we will compute a single net acceleration of the chain from the net forces on all floaters.
 Calculating net force/torque on the chain: At any moment, some floaters are on the ascending side (light,
 moving up) and some on the descending side (heavy, moving down). Due to the chain, an upward motion of
 the ascending side corresponds to a downward motion of the descending side. Both contribute to driving
 the chain in the same rotation direction: - Ascending (light) floaters provide an upward force which tends to
 pull the chain up on that side. - Descending (heavy) floaters provide a downward force on the other side,
 which also pulls the chain (down on that side, but that turns the sprocket the same way as the up force on
 the other side). 
19
 We sum up contributions from all floaters: - For each ascending floater (light): net force contributing =
 $F_{\text{buoy}} - F_{\text{weight}} - F_{\text{drag}}$ (this will be positive if buoyancy exceeds weight+drag)
 . - For each descending floater (heavy): net force contributing = $F_{\text{weight}} - F_{\text{buoy}} 
F_{\text{drag}}$ (this will be positive if weight exceeds buoyancy+drag). These forces all act to rotate the
 chain in the forward direction (assuming we define forward as the direction that has light floaters going up).
 We can compute a net force imbalance = (sum of upward side forces) minus (sum of downward side forces
 if they acted opposite, but since we set it up so both are positive contributions, we actually just sum
 appropriate signs as above). An equivalent approach is to calculate torque about the sprocket directly: for
 each floater, $ \tau_i = F_{net,i} \times R$. Summing those gives total torque from the floaters on the chain. 
Important: Because the chain links the motion, the acceleration of the entire system is determined by
 the net force and the total mass/inertia. In a linear sense: $a_{\text{chain}} = \frac{F_{\text{net (up 
down)}}}{M_{\text{total}}}$, where $M_{\text{total}}$ is the total mass of all moving parts on the loop (all
 f
 loaters plus the equivalent mass of the chain itself moving vertically). It may be more straightforward to do
 this as a rotation: $\tau_{\text{net}} = I_{\text{total}} \alpha$, where $I_{\text{total}}$ is the total rotational
 inertia of the system (including floaters and the rotating assembly). However, since floaters are moving
 linearly (albeit constrained), we can get away with a linear treatment for their motion and a separate
 rotational inertia for the shaft if needed. 
6
For now, a simple approach: - Compute net force $F_{\text{net,total}} = \sum_{\text{floaters asc}}(F_b - F_w 
F_d) + \sum_{\text{floaters desc}}(F_w - F_b - F_d)$. (Our 
Floater.compute_forces() from earlier
 effectively gives each floater’s $F_{\text{net,i}}$ already accounting for direction.) - Compute an effective
 mass for the system. If we have $N$ floaters total, all are moving (either up or down). The total mass being
 accelerated = sum of all floater masses (since all are moving with the chain) + the mass of the chain
 (converted to an equivalent mass moving vertically on each side). If the chain’s mass is $m_{\text{chain}}$,
 you could split half on each side, but since both sides move, total moving mass includes the whole chain.
 We might also include an equivalent mass for rotating parts like the sprocket and generator rotor. To
 include the generator’s inertia properly, it’s easier to do torque & rotational inertia, but if the rotational
 inertia $I$ of the system is known, one can convert it to a linear equivalent mass via $m_{\text{equiv}} = I /
 R^2$ for the chain radius. For simplicity, we might ignore rotational inertia of generator in the initial realism
 pass (assuming quasi-steady or that generator’s inertia is small compared to floaters+chain, or we simply
 account for generator as a torque, not inertia). - Then $a = F_{\text{net,total}} / M_{\text{total}}$ gives the
 acceleration of the chain (ascending side acceleration upward). All floaters will share this acceleration.
 Code integration: We can implement the above in the simulation loop. Instead of each floater updating its
 own velocity independently, we do something like:
 # Assume we have a list of Floater objects: floaters
 # and global variables: R (sprocket radius), m_chain, I_rotor (generator 
rotational inertia, optional)
 # and maybe a constant friction_force or friction_torque.
 M_total = sum(f.mass for f in floaters) + m_chain # total mass of moving parts 
(kg)
 # Compute net force from floaters
 F_net_total = 0.0
 for f in floaters:
 # Set each floater's velocity based on current chain velocity (v_chain).
 # If chain_velocity is positive, ascending side floaters have +v, descending 
have -v.
 # We can determine side by angle: say angle in [0, π) = ascending, [π, 2π) = 
descending.
 if 0 <= f.angle < math.pi:
 # Ascending side (moving up)
 f.velocity = v_chain # positive upward
 else:
 # Descending side (moving down)
 f.velocity =-v_chain # negative (downward)
 # Now compute net force on this floater:
 F_net_total += f.compute_forces()
 # Include any constant friction opposing motion (approximate as a force for 
linear model)
 F_fric = friction_coef * M_total * 9.81 # e.g., a fraction of total weight, or 
other model
 F_net_total-= math.copysign(F_fric, F_net_total) # subtract friction opposing 
7
motion
 # Compute acceleration of the chain (m/s^2)
 a_chain = F_net_total / M_total
 # Update chain velocity and position
 v_chain += a_chain * dt
 distance_moved = v_chain * dt
 In this pseudocode: - 
v_chain is the linear speed of the chain (positive means floaters on the 0–π side go
 up). - We determine each floater’s velocity sign by its angle position (0 to π rad = front/ascending side, π to
 2π = back/descending side). This assumes 0 rad corresponds to bottom of the loop, π rad to top of the loop
 (we can adjust if needed). - We sum forces from each floater (using our earlier method that accounts for
 drag, buoyancy, weight properly for whichever direction the floater is moving). - We then subtract a friction
 force if desired (here shown as a simple model: e.g., 
friction_coef could be a very small number like
 0.01 representing 1% of total weight as friction just to introduce some damping; we apply it opposite to the
 direction of motion). - Then we compute acceleration and integrate velocity and position.
 By doing it this way, all floaters share the same 
v_chain and thus stay synchronized, and the
 acceleration is global, not per floater.
 Rotation and torque: The above was in linear terms. We can also do it in rotational terms around the drive
 wheel: - Compute net torque from floaters: $\tau_{\text{float}} = F_{\text{net,total}} \times R$. - Include a
 friction torque $\tau_{\text{fric}}$ (which could be constant or proportional to $\omega$). - Include
 generator resistive torque $\tau_{\text{gen}}$ (discussed in next section). - Then $\alpha = \tau_{\text{net}} /
 I_{\text{total}}$. If we compute $I_{\text{total}}$ (moment of inertia of all floaters and chain about the
 sprocket), that’s a bit involved. But one way is $I_{\text{total}} = \sum m_{\text{each}}(R^2)$ for each floater
 and the chain’s mass (like treating them at radius R). This basically gives $I_{\text{total}} = M_{\text{total}}
 R^2$. So $\alpha = F_{\text{net,total}} R / (M_{\text{total}} R^2) = F_{\text{net,total}}/(M_{\text{total}} R)$.
 This is consistent with the linear $a = F/M$ (since $a = \alpha R$). So either approach is consistent; we just
 have to be careful to include any additional inertia (like a flywheel or generator rotor) by adding to
 $I_{\text{total}}`.
 Given our simpler linear implementation above, we can stick to that for now – it avoids confusion with
 rotational units as long as we remember to convert generator torque to an equivalent force on the chain
 (i.e., $F_{\text{gen}} = \tau_{\text{gen}}/R$ to subtract from $F_{\text{net,total}}$). We will incorporate that
 next.
 3.3 Event Handlers for Injection and Venting
 7
 8
 Physical realism demands that we correctly handle the moments when floaters change state: at the bottom
 and top of the loop. These moments involve air injection at the bottom and venting/refilling with water
 at the top . We will implement these as event handlers or conditional checks each time step:
 • 
• 
Bottom Injection Event: When a heavy floater reaches the bottom of the tank, we inject
 compressed air into it, expelling the water and making it buoyant. In the simulation, this means:
 The floater’s state flips from "heavy" to "light".
 8
• 
We instantly change its mass: subtract the water mass and add the (negligible) air mass. For our
 model, effectively $m$ goes from ~$m_{\text{container}}+ \rho_{\text{water}}V$ to
 ~$m_{\text{container}}$.
 • 
• 
• 
• 
10
 We may also want to capture the energy used by the compressor for this injection. This doesn’t
 affect the mechanics at the moment of injection (we assume the injection is very fast, completed
 while the floater is at the bottom and held in place briefly). But for energy accounting, we can
 calculate the work done to inject air at pressure. A rough calculation: Work $W_{\text{inject}} \approx
 P_{\text{depth}} \times V_{\text{air}}$ (assuming isothermal for simplicity). Here $P_{\text{depth}} =
 P_{\text{atm}} + \rho g h$ (pressure at injection depth above atmosphere) and $V_{\text{air}}$ is the
 volume of air injected (which is ~ the floater volume $V$). We will add this $W_{\text{inject}}$ to a
 running energy input counter. This allows computing net energy later. According to the analysis,
 the energy cost here is quite large , so it’s important for realism to track it.
 We ensure the buoyant force remains the same (since volume doesn’t change), but now net force will
 drastically increase because the weight force dropped.
 Implementation: We need to detect when a floater “reaches bottom.” If we use an angle
 representation (0 rad at bottom, moving upward as angle increases), one way is to check if a floater’s
 angle passes through 0. For example, if previously its angle was just slightly positive and after an
 update it became slightly negative (or equivalently, if we keep angle in [0, 2π) by modulo, we can
 track if it goes below a small threshold). Another approach is to track the sequence of floaters – e.g.,
 always inject the one that is next in line to bottom once the chain moved a certain amount. The
 simplest might be:
 ◦ 
◦ 
Define a small angular window for bottom (say angle ∈ [0, θ_threshold]) to represent being
 in the injection zone. If a floater is in this zone and is heavy, flip it to light. We must also
 ensure we don’t flip the same floater repeatedly if it lingers in that zone for multiple time
 steps. So perhaps track whether we’ve already injected it this cycle. We can add a boolean flag 
f.injected or use the state itself as indicator (if it’s heavy and at bottom, do injection and
 now it’s light, so we won’t do it again until it completes a full loop).
 We should also synchronize injection with the physics: likely, in reality, the chain might pause
 briefly to inject, or a clutch disengages. However, to keep things simple and continuous, we
 assume the injection happens quickly enough not to stop the motion. We’ll simply apply the
 state change and let the simulation proceed.
 Code example for bottom injection handling: 
bottom_zone = 0.1 # rad, define bottom zone half-angle (maybe 0.1 rad ~ 
5.7 degrees)
 for f in floaters:
 # Normalize angle to [0, 2π)
 f.angle = f.angle % (2*math.pi)
 # Check bottom zone
 if f.state == "heavy" and f.angle < bottom_zone:
 # Trigger injection event
 f.state = "light"
 # Update mass: remove water mass
 f.mass = f.container_mass # (air mass negligible)
 # Log energy used for compression
 depth = tank_depth # (we can define tank_depth in meters for 
9
bottom depth)
 P_depth = 101325 + 1000*9.81*depth # Pa (atmospheric + 
hydrostatic)
 W_inject = P_depth * f.volume # in Joules (isothermal approx.)
 energy_input += W_inject
 # (We assume injection completes instantaneously at this time step)
 This will convert the floater to buoyant as it hits bottom. We use 
f.angle < bottom_zone as a
 simple trigger. Depending on the time step and speed, we might need to catch if it “skipped” over
 zero; but with small dt that’s unlikely. We can refine by also checking if 
f.angle + f.velocity*dt crossed zero. For now, this should be okay.
 • 
• 
• 
• 
Top Venting Event: When a light floater reaches the top of the water column, the air is vented and it
 refills with water, becoming heavy again
 7
 8
 . In simulation terms:
 Floater’s state flips from "light" to "heavy".
 Its mass increases by adding the water mass back (and removing the air, which was negligible).
 We might not need to add energy here, because venting typically releases the air (possibly losing the
 small amount of compressed air energy to the atmosphere). If anything, there’s a slight loss of
 energy as the compressed air is vented (not recovered), but we can ignore that or account as a small
 inefficiency. The main effect is just the mass increase.
 • 
• 
• 
Again, detect the event: if a floater’s angle is around π (180°, the top of the loop) and it’s light, then
 vent. Similar strategy: define a top zone around π. For example, if $|\text{angle} - \pi| <
 \theta_{\text{threshold}}$ and state is light, perform vent.
 Code example for top venting: 
top_angle = math.pi
 top_zone = 0.1 # rad tolerance for top
 for f in floaters:
 # ... after updating f.angle ...
 if f.state == "light" and abs(f.angle- top_angle) < top_zone:
 # Trigger venting event
 f.state = "heavy"
 f.mass = f.container_mass + 1000 * f.volume # add water mass back
 # (Optional: log that compressed air is lost; we could count this 
as lost energy or just ignore since we already counted compressor input. If 
needed, we could subtract a small amount of energy output as well to 
indicate no recovery of air energy.)
 After venting, the floater is heavy and will begin to accelerate downward on the next time steps.
 20
 21
 By handling these events, we ensure the simulation cycles through the proper sequence of floater states,
 matching the described KPP cycle . It’s crucial for physical realism since the buoyant force only does
 work when the floaters are toggled correctly.
 10
Verification of realism: With these in place, our simulation will show heavy floaters going down (pulled by
 gravity), being converted to light at bottom, then rising (pulled by buoyancy), then converted to heavy at
 top, and so on – continuously driving the chain. This matches the conceptual description of KPP’s
 mechanism . 
9
 22
 3.4 Mechanical and Electrical Component Modeling
 Beyond the floaters and fluid forces, realism requires modeling the drivetrain mechanics and the
 generator (electrical load), as well as accounting for the compressor’s effect on energy.
 • 
• 
• 
• 
• 
• 
Drivetrain & Chain Mechanics: We have implicitly modeled the chain’s effect by coupling floater
 motion. We should also account for:
 The radius of the sprocket or wheel ($R$) that the chain runs on (which converts linear force to
 torque). We already use this in force-to-torque conversions. We should choose a value (say $R = 0.5$
 m as an example) and use it consistently.
 The inertia of rotating parts: If the chain is attached to a shaft/flywheel/generator, that rotating
 mass will resist changes in speed. A large inertia would smooth the motion (like a flywheel storing
 energy, as per H3 concept
 23
 ). Initially, we might not include a separate inertia beyond the
 f
 loaters+chain mass (which we included linearly). If needed, we can add a parameter for additional
 rotational inertia. For now, we will assume modest inertia or incorporate it in the effective mass as
 discussed.
 Gear or transmission: The KPP might have a gearbox. If so, and if we wanted to model it, we’d have
 to adjust torques and speeds by gear ratio. For simplicity, assume a direct drive (1:1 ratio between
 chain sprocket and generator). This is scientifically fine to start with; gear efficiency can be
 considered later.
 Friction: We already included a simple friction. We might refine this later (like static vs kinetic
 friction, but likely small relative to drag, etc.).
 8
 Generator (Electrical Load): The generator provides a resisting torque on the drivetrain,
 converting mechanical work into electrical energy . We need to model this resisting torque in
 the simulation:
 24
 • 
• 
• 
In simplest terms, we could model the generator as a constant torque opposing rotation (like
 attaching a dynamometer or brake). For example, the user might specify a generator load that draws
 a certain torque, or a target electrical power. However, in reality, generator behavior can be more
 complex – often the torque depends on speed and load characteristics.
 A simple linear model: $\tau_{\text{gen}} = k_{\text{gen}} \omega$, i.e., proportional to angular
 speed (this would mimic a generator connected to a resistive load, where faster spinning generates
 more counter EMF and hence more torque). But if $k_{\text{gen}}$ is too high, it can also stall the
 system. Alternatively, we might simply specify a fixed torque representing the generator’s
 electromagnetic resistance at a given operating point.
 For now, let’s allow a constant resistive torque as a parameter (in N·m). We subtract this from the net
 torque driving the acceleration. This will lead to an equilibrium speed when the buoyant force-driven
 torque equals the generator torque (plus friction), producing steady rotation and steady power
 output.
 11
• 
We will also calculate electrical power output = $\tau_{\text{gen}} \cdot \omega$ (generator torque
 times angular velocity) as the instantaneous electrical power being generated. We can integrate that
 over time (or sum power*dt) to get electrical energy output, to compare with compressor energy
 input, for checking net energy.
 • 
• 
• 
• 
Code inclusion: 
# After computing F_net_total from floaters and friction:
 # Convert generator torque to equivalent force:
 F_gen = tau_gen / R # where tau_gen is a chosen constant resistive torque 
(N·m)
 # Subtract it from net force (opposes motion). Direction: if chain is 
moving forward (v_chain positive), generator force opposes it.
 F_net_total-= F_gen * math.copysign(1, v_chain)
 # subtract in appropriate direction
 # Now F_net_total is reduced by generator load.
 # (Alternatively, include generator in torque form:
 # tau_net = F_net_total*R - tau_gen; then alpha = tau_net / I_total, which 
is equivalent to what we're doing.)
 # Compute power output (instantaneous)
 power_output = tau_gen * (v_chain / R) # because ω = v_chain/R, so τ*ω = 
τ*(v_chain/R)
 # If v_chain is in m/s, then v_chain/R = ω (rad/s), so this gives power in 
watts.
 cumulative_energy_out += power_output * dt
 Here we treat 
tau_gen as a constant for simplicity. We could tie it to a desired power or a certain
 load curve. For example, if we wanted a 500 kW output at some speed, we could adjust 
tau_gen
 accordingly. But keeping it fixed is fine for now. We will see the rotation speed settle where buoyant
 input = generator resistive torque (if it can reach such a point).
 Compressor (Air Injection) Energy: We already mentioned logging the energy input for each
 injection. To reiterate:
 We maintain 
energy_input (Joules) for compressor work. Each time a floater is injected at
 bottom, add $W_{\text{inject}}$. If needed, we can refine this with thermodynamic formulas (e.g., an
 isothermal compression: $W = P_{\text{atm}} V \ln(\frac{P_{\text{depth}}}{P_{\text{atm}}})$ or an
 adiabatic formula). But even a simplified $P_{\text{depth}} \cdot V$ is a decent approximation of the
 work needed. This ensures the simulation’s energy accounting reflects reality (i.e., we’re not creating
 free energy from buoyancy without paying the compressor cost). As the analysis showed, ignoring
 this would violate energy conservation .
 10
 We might also consider the compressor’s effect on the air volume: as the floater rises, if the
 container is sealed, the air expands due to decreasing water pressure. The white paper mentioned
 that as floats rise, the air can expand and push out a bit more water . In our model, we assumed
 the water was fully expelled at injection, so we don’t simulate further expansion. For realism, one
 could model that maybe only, say, 90% of water is expelled at injection, leaving some water inside;
 25
 12
then as pressure drops, that remaining water gets pushed out gradually. This would complicate the
 model significantly (we’d need to track internal air pressure and remaining water). Given our current
 scope, we will assume full purge at injection for simplicity – it’s a reasonable approximation if the
 injection is powerful enough. The thermal expansion (H2 hypothesis) can be introduced later to
 amplify buoyancy if needed.
 • 
Putting it together (Main loop integration): Now we combine all pieces (floaters forces, chain
 acceleration, generator, events) into the simulation loop. Below is a consolidated pseudocode
 integrating physical realism:
 # Initialize simulation state
 t = 0.0
 v_chain = 0.0
 # chain linear velocity (m/s)
 theta = 0.0
 # chain rotation (rad) if needed for output
 energy_input = 0.0 # Joules, compressor work input
 cumulative_energy_out = 0.0 # Joules, electrical energy generated
 results = []
 # to log results if needed
 # Main simulation time-stepping loop
 while t < total_time:
 # 1. Determine forces on each floater
 F_net_total = 0.0
 for f in floaters:
 # Update floater velocity based on chain velocity and its direction
 if 0 <= f.angle < math.pi:
 # ascending side
 f.velocity = v_chain
 else:
 f.velocity =-v_chain
 # upward velocity
 # descending side
 # downward velocity
 # Compute forces for this floater
 F_net_total += f.compute_forces()
 # 2. Include friction and generator forces
 # Friction (simple model)
 F_net_total-= math.copysign(friction_force, v_chain) # static value or 0 
if not defined
 # Generator resistance
 F_gen = tau_gen / R # equivalent force from generator torque
 F_net_total-= math.copysign(F_gen, v_chain)
 # 3. Compute acceleration of chain and update kinematics
 M_total = sum(f.mass for f in floaters) + m_chain
 a_chain = F_net_total / M_total
 # Update chain velocity and position
 v_chain += a_chain * dt
 # (Optional: limit v_chain >= 0 if we assume it won't reverse; in rare cases if 
generator is too strong, v_chain might reverse, but in KPP it should ideally 
always go one way.)
 theta += (v_chain / R) * dt # update rotation angle if needed (rad)
 13
# 4. Advance floater positions along the loop
 # The distance each floater moves along the chain this step:
 distance = v_chain * dt
 # Update angles for each floater
 for f in floaters:
 # Angle increase or decrease? If chain moves forward, ascending side 
floats' angle should increase from 0 toward π, descending from π to 2π.
 # Assuming forward motion means floaters go from bottom (0) to top (π) 
to bottom (2π which wraps to 0).
 # So we increment angle by +dtheta for all floats for forward motion.
 dtheta = (distance / R) # positive if moving forward
 f.angle += dtheta
 # Wrap angle within 0 to 2π
 if f.angle >= 2*math.pi:
 f.angle-= 2*math.pi
 # 5. Handle events: Injection at bottom, Venting at top
 for f in floaters:
 # Bottom injection
 if f.state == "heavy" and f.angle < bottom_zone:
 f.state = "light"
 # Update mass (remove water)
 f.mass = f.container_mass
 # Compute injection energy
 W_inject = (101325 + 1000*9.81*tank_depth) * f.volume # J
 energy_input += W_inject
 # Top venting
 if f.state == "light" and abs(f.angle-math.pi) < top_zone:
 f.state = "heavy"
 f.mass = f.container_mass + 1000 * f.volume
 # (No significant energy added or removed here, aside from losing 
compressed air)
 # 6. Compute output power (for logging)
 # angular speed ω = v_chain / R
 omega = v_chain / R
 power_out = tau_gen * omega # instantaneous electrical power
 cumulative_energy_out += power_out * dt
 # 7. Log data for this step if needed (time, chain speed, acceleration, 
forces, energies, etc.)
 results.append({
 'time': t,
 'chain_velocity': v_chain,
 'chain_accel': a_chain,
 'net_force': F_net_total,
 'omega': omega,
 'torque_gen': tau_gen,
 'power_out': power_out,
 'energy_in': energy_input,
 'energy_out': cumulative_energy_out,
 14
# we can also log floaters' individual states if needed:
 'floaters': [{'angle': f.angle, 'state': f.state, 'vel': f.velocity} for
 f in floaters]
 })
 # 8. Increment time
 t += dt
 This pseudo-code demonstrates the flow of data and calculations each time step in a realistic manner: 1.
 Compute forces on floaters (buoyancy, weight, drag) and sum net force. 2. Subtract resistances (friction,
 generator). 3. Compute acceleration and update chain velocity (all floaters’ velocity). 4. Move all floaters by
 the appropriate amount along the loop. 5. Handle state changes at boundaries (bottom/top). 6. Compute
 power output and accumulate energy. 7. Log or output the data (which will be sent to client). 8. Loop to next
 time step.
 With this structure, all forces are accounted for and applied correctly at each step, satisfying the
 requirement that “all forces are calculated and handled correctly.” The science (buoyancy, Newton’s laws,
 energy conservation) is respected in the model. 
Note: We might need to tune some parameters (like friction_force or tau_gen) to get a stable operating
 point. For example, if tau_gen is very high, the system might accelerate slowly or even stall if buoyant force
 can’t overcome it. If tau_gen is zero, the system might accelerate continually (limited by drag and friction)
 until drag = buoyant net force in steady state. That’s fine physically (it would reach terminal velocity when
 drag and other resistances balance net buoyancy). Including a generator torque makes it more interesting
 by converting that mechanical work to electricity, and will also create a new equilibrium point.
 3.5 Data Flow and Verification
 Ensuring the flow of data means that the outputs of one part of the physics correctly feed into the next.
 We’ve structured the loop so that: - Forces are computed from the current state (positions, velocities, etc.). 
Those forces determine acceleration, which updates velocities and positions. - Events update masses, which
 will affect next iteration’s forces. - Throughout, we log relevant outputs (forces, torque, power, states) in
 each loop iteration.
 This systematic update guarantees that if there’s any issue (e.g., energy seeming to be created from
 nothing), we can pinpoint it by examining the logged terms: - Check that when a floater goes from heavy to
 light, there’s a corresponding spike in buoyant force and that we logged compressor energy input. - Check
 that the sum of forces becomes zero at steady state (when acceleration stops, net force should be zero,
 meaning buoyant forces are balanced by drag + weight + generator load). - Verify energy balance: over a full
 cycle, ideally (in a conventional scenario) the net energy output should be negative or zero because of
 losses (the known analysis result ). If we implement H1/H2 later, we might see some improvements, but
 if our baseline physics is correct, we should see that without H1/H2 the system can’t output net energy. That
 is a good scientific validity check.
 10
 We can use the logged 
energy_input and 
energy_out to calculate efficiency or net gain. E.g., at end
 of simulation: 
net_energy = energy_out - energy_input . We expect a negative or zero net for
 baseline (meaning we spent more compressing air than we got in electricity), consistent with physics .
 Later, if H1/H2 are added, we’d check if they can tip that balance.
 10
 15
By focusing on these physics aspects now, we ensure the simulation is a correct scientific tool. Once this is
 confirmed, we can safely move on to more advanced or front-end features, knowing the core is solid.
 4. Backend-Focused Enhancements (Deferring Frontend Upgrades)
 At this point, we intentionally defer any complex frontend or multi-client work. The goal is to keep the
 front-end minimal (perhaps a simple form and a streaming text or basic chart) and concentrate all our
 efforts on the backend logic: handlers, references, connections, mapping, calculations, equations, physics,
 mechanics, electrical components, etc., as you specified. Below are the specific backend enhancements and
 how to implement them:
 4.1 Refactoring Code Structure (Handlers, Mapping, and References)
 26
 27
 It’s important to organize the code logically so that each part of the physics is handled in a clear way.
 Adopting some of the blueprint’s suggestions : - Module separation: Keep the physics code
 separate from Flask routes. E.g., have a 
simulation/ directory with files like 
formulas), 
engine.py (for the simulation loop), etc. The Flask 
physics.py (for force
 app.py will import and use these, but not
 contain physics logic itself. This makes it easier to test and modify the physics without touching web code. 
Floater and Simulation classes: We already used a 
Floater class in examples. We can also implement a
 higher-level 
Simulation class or similar to encapsulate the list of floaters and global state (time,
 energies, etc.), and provide methods like 
step(dt) to advance the simulation. This class can also manage
 the event handling for injection/venting in its 
step method, which is cleaner than doing it all in one big
 loop externally. - Handlers and events: Instead of scattering the injection/vent logic in the main loop, we
 can implement it as part of the Simulation or Floater logic: - For example, 
inject_air() and 
Simulation.step() can call
 self.check_events() either before or after the physics update. Or each Floater could have methods
 like 
vent() that adjust its state. Then the simulation just needs to detect when to
 call those. This makes the code more readable. For instance: 
class Simulation:
 def __init__(...):
 self.floaters = [...] # list of Floater objects
 self.time = 0.0
 self.v_chain = 0.0
 # other global states...
 def step(self, dt):
 # compute forces, update velocities etc (as above)
 ...
 # after updating floater positions:
 for f in self.floaters:
 if f.state == "heavy" and f.at_bottom():
 self.inject_air(f)
 if f.state == "light" and f.at_top():
 self.vent(f)
 ...
 self.time += dt
 return output_data # maybe return a dict of current state for streaming
 16
def inject_air(self, floater):
 floater.state = "light"
 floater.mass = floater.container_mass
 # log energy, etc.
 def vent(self, floater):
 floater.state = "heavy"
 floater.mass = floater.container_mass + 1000*floater.volume
 In the above, `f.at_bottom()` and `f.at_top()` could be helper methods (or 
properties) of Floater that check its angle against threshold:
 ```python
 class Floater:
    ...
    def at_bottom(self):
        return self.angle % (2*math.pi) < bottom_zone
    def at_top(self):
        # Check if angle is near π (180°)
        return abs((self.angle % (2*math.pi)) - math.pi) < top_zone
 ```
 Using these abstractions (“handlers”) improves code clarity and maintainability.
 • 
• 
• 
Mapping and references: By “mapping”, we mean mapping the floater’s position (angle) to physical
 locations (like bottom or top) and mapping the forces to the resulting motion. We have effectively
 done that by using the angle to determine states and using the chain velocity to map to each
 f
 loater’s velocity. We should double-check the geometric mapping: e.g., if the distance between
 bottom and top is the height of the water column (say $H$), and if the chain length around the loop
 is maybe $2H$ (for vertical sections) plus some slack around sprockets, the angle corresponds to a
 vertical position via $y = R \theta$ (if $\theta$ is measured along the sprocket). However, since we
 simplify the path as a circle for angle calculation, it’s conceptually consistent: 0 rad = bottom, π rad =
 top, linear mapping along the semicircle of radius equal to half the distance etc. In any case, we
 don’t need the exact $y$ coordinate for realism beyond knowing bottom vs top. 
If needed for output, we can compute a floater’s vertical position from angle: maybe assume a loop
 shaped roughly like a circle or rectangle. A simple approach: map angle to vertical coordinate:
 ◦ 
◦ 
For 0 to π: ascending side, could map $y = (\theta/\pi) \cdot H$ (0 at bottom, $H$ at top).
 For π to 2π: descending side, map $y = H - ((\theta-\pi)/\pi)\cdot H$ (going back down). This is
 a bit hacky but gives an approximate idea if one wants to animate it or confirm heights. It’s
 not strictly necessary for physics, since forces don’t explicitly depend on $y$ except for
 pressure in injection energy calc (we use tank_depth for that).
 References to global parameters: Ensure that values like water density, gravity, tank depth,
 number of floaters, etc., are not hard-coded in multiple places. Instead, define them in one place
 (like a config dict or as attributes of Simulation). For example, 
self.rho_water = 1000 , 
self.g = 9.81 , 
self.tank_depth = 10 (if 10 m water column), etc. This way, if we want to
 change a parameter or do sensitivity analysis, we change it once. It also allows hooking up the front
17
end controls to these values easily (e.g., user inputs a new depth, we update 
sim.tank_depth and
 use it in injection energy calc).
 • 
Validation of equations with references: It might be useful to compare our simulation formulas
 with references or known equations in literature to ensure correctness. For buoyancy and drag,
 we’ve already aligned with standard formulas
 5
 . For the energy, the analysis document gives a
 reference point: e.g. they calculated required air flow and pointed out huge discrepancies
 28
 . While
 we can’t directly simulate that without multi-cycle aggregated data, we can ensure our single-cycle
 outputs (like volume of air per cycle, etc.) could be measured. If needed, we might include counters
 for how many floaters per minute are injected, etc., to compare to the 5.41 m³/min number
 mentioned.
 4.2 Ensuring Correct Calculations and Equations
 17
 We have outlined the key equations. Let’s recap and ensure they’re correctly implemented: - Archimedes’
 principle: We directly use it for buoyant force . (We assume full submersion; if partial, we’d multiply by
 submerged fraction, but our design always submerges floaters fully between bottom and top.) - Newton’s
 second law: Net force = mass * acceleration for linear motion, and net torque = $I * \alpha$ for rotation.
 We use the linear version for chain acceleration ($a = F_{\text{net}}/M_{\text{total}}$). This is the backbone
 of the simulation loop. - Drag equation: We implemented $F_D = 1/2 \rho C_d A v^2$ . We should
 double-check units: $\rho$ (~1000 kg/m³), $C_d$ (dimensionless), $A$ (m²), $v$ (m/s) -> $F_D$ in Newtons,
 which is correct. We assume $C_d$ and $A$ are provided reasonably. If the user interface doesn’t have
 these, we can default them or infer $A$ from floater volume by assuming a shape. - Energy calculations:
 We calculate power output as $\tau_{\text{gen}} * \omega$. The units: N·m * rad/s = J/s (Watts). Our
 integration of 
cumulative_energy_out and 
6
 energy_input uses dt (s) so they end up in Joules. We
 should ensure consistency (we started with SI units everywhere, so it’s fine). - Thermodynamics (if any): We
 are approximating the thermodynamic processes (injection treated as instantaneous isothermal for energy
 calc; expansion effects ignored initially). This is acceptable for now. In the future, if we add H2 (thermal
 assist), we might incorporate temperature changes. We have placeholders like we could adjust effective $
 \rho_{\text{water}}$ for nanobubbles or modify buoyancy to simulate added lift from expansion. For now,
 everything follows “normal” physics, which is what the user wants at this stage.
 We will verify these calculations with small test scenarios: - If we run the sim with a single floater (just to
 test), we should see: when it’s heavy it goes down, when light goes up, etc. But with one floater, motion
 would be jerky (since when it’s the only one, once it becomes light, there’s nothing on the other side until it
 goes around, etc.). In reality KPP has multiple floaters to smooth that out. So we will primarily test with
 multiple floaters (say 8 or 10). - Check extremes: if drag is zero and no generator, the system would
 accelerate until limited by maybe friction or numeric stability – likely reaching very high speed unrealistic. In
 reality drag increases with speed and will naturally limit it (terminal velocity). Our model includes drag, so it
 should find a terminal velocity even with no generator. That’s a good check: does the simulation reach a
 steady speed on its own? It should, because as speed increases, drag $F_D \propto v^2$ grows until net
 force zero. - If we add generator load, the terminal speed will be lower (since some force goes into
 generator torque) but the system might still reach some equilibrium where buoyant drive = drag +
 generator + friction.
 18
4.3 Mechanical & Electrical Components Details
 We have partially covered this, but to emphasize the elements: - Floaters and Fluid (Buoyancy module) 
Already implemented. - Air Injection/Venting (Pneumatic module) – We have an initial model. A future
 enhancement could be to simulate the air compressor dynamics (like pressure build-up, multiple floaters
 requiring continuous airflow). For now, we treat it in a lumped way per floater event. This is fine. 
Drivetrain & Generator (Mechanical/Electrical) – We introduced a constant generator torque. In a more
 realistic simulator, we might let the user specify, for example, a target generator power output and then
 adjust $\tau_{\text{gen}}$ dynamically to try to maintain that (which could simulate an active generator
 control or load following). Or we could simulate an electrical load that draws a current proportional to
 generator speed (which is analogous to $\tau \propto \omega$). - For now, a fixed $\tau_{\text{gen}}$ is
 effectively like putting a braking torque that will either stall the system if too high or be overcome if
 buoyancy is strong enough. - We should ensure $\tau_{\text{gen}}$ is chosen within reason. If the user
 wants to simulate a certain output power, note that maximum buoyant force per float times radius gives a
 max torque. For example, 392 N buoyant on 0.5 m radius = 196 N·m per float (if chain had one floater at a
 time contributing). With multiple floaters, maybe a few can contribute at once, but it won’t exceed certain
 multiples. The analysis said needing >1e6 N net force for 500 kW , which is far beyond baseline. So if we
 set $\tau_{\text{gen}}$ too high, the simulation will show near-zero speed (stall) because buoyant torque
 can’t overcome it. That’s fine – it demonstrates the claims issue. If we want to see motion, we might use a
 smaller $\tau_{\text{gen}}` initially. - We’ll document that parameter so the user can tweak it and see what
 happens (e.g., try a range that yields some net motion). - Monitoring output metrics: The backend should
 provide outputs like time-series of torque, power, efficiency, etc. We have included these in the results
 logging. We could also compute an instantaneous efficiency = output power / (input power from
 compressor) at each moment, but since input power is in pulses at injections, it might be better to compute
 cumulative energy efficiency = (total energy_out / total energy_in). We can do that at end or on the fly (we
 logged energies, so easy to compute at any time). These outputs will later be displayed on front-end charts
 (as Stage 2 mentions using Chart.js to plot in real-time ).
 29
 30
 31
 4.4 Preparing for Future Upgrades (H1, H2, H3, Frontend)
 While focusing on the backend now, it’s wise to keep the design extensible so that later we can implement: 
H1: Nanobubbles effect – This would effectively reduce the density or drag of water. We can simulate this
 by a parameter that lowers $\rho_{\text{water}}$ or $C_d$ for descending floats. For instance, a
 nanobubble_frac that reduces effective density: $\rho_{\text{eff}} = \rho (1 - f)$ as suggested .
 We can include this in 
23
 32
 33
 Floater.compute_forces() easily (just multiply the buoyancy and drag
 computations by whatever factor if needed when the floater is on descending side, since that’s where
 nanobubbles are supposed to help). We won’t implement fully now, but we will leave hooks. - H2: Thermal
 assist – This would increase buoyancy work on ascent by keeping the air warm (expanding more). In the
 sim, it could be an increase in effective buoyant force or reduced air density inside (but since we keep
 volume constant, an alternate way is to say the float’s buoyancy is slightly higher than normal or its weight
 effectively reduced more). Another way is to allow a slight volume increase (if floaters not rigid), but likely
 easier is to directly add an extra force or efficiency factor to buoyancy on ascent. For now, our base model is
 adiabatic-like (no extra help). Later we can add a multiplier to $F_B$ on ascent if H2 is on. - H3: Pulse/Coast
 and Flywheel – This involves complex control: using a flywheel to store energy and releasing it in bursts
 . To simulate, we might allow the generator to engage/disengage via a clutch, and include a flywheel
 inertia. We could simulate a scenario where for a few seconds we let the chain accelerate without generator
 load (storing energy in flywheel/inertia as higher speed), then engage generator briefly to extract a big
 19
power pulse, then repeat. This requires a control logic. We won’t do it now, but our structure is ready for it:
 we have tau_gen as a parameter; we could make it time-dependent or conditional in the loop to
 represent clutching. And we have an implicit inertia (M_total) which could include a flywheel mass to
 smooth things. So later, adding an on/off control for generator torque is feasible.
 Frontend deferral: We will keep the front-end very basic: one page to start simulation and perhaps
 text or simple charts to view results. We might not implement the full Chart.js live update just yet,
 but ensure the backend can stream JSON data (time, values) correctly. The Stage 2 plan describes
 how the front-end should eventually look – multiple charts for torque, power, etc., and
 controls to update parameters in real-time. We’ll get to that once the backend physics are validated.
 In code, our /stream route already yields JSON events per time-step . The client can later
 use that to plot graphs. For now, even logging the data or printing some summary at end is enough
 to test realism.
 In conclusion, by implementing the above plan, we will patch the existing system to have a robust, realistic
 physics simulation of the Kinetic Power Plant. All forces (buoyancy, gravity, drag, etc.) are computed each
 step and correctly applied , the floaters’ state changes are handled at the proper times, and the
 mechanical-electrical interactions are modeled. This will greatly enhance the realism and fidelity of the
 simulation, creating a sound basis for future enhancements (both in adding the special hypotheses H1–H3
 and improving the front-end and multi-client capabilities in later stages).
 Sources:
 KPP operating principle and forces (buoyant vs heavy side)
 Physics formulas for buoyancy and drag
 Simulator architecture and H1/H2 effects suggestion
 Drivetrain and generator modeling
 Feasibility analysis emphasizing energy balance and need for H1–H3
 Stage 1 Implementation Guide_ Real-Time Simulation Loop Upgrade.pdf
 file://file-GpMuyKuXh2AZkbDqvhrgVu
 Flask-Based KPP Simulator Implementation Blueprint.pdf
 file://file-3HVVUCDUgivcJmxNAkMx7U
 Kinetic Power Plant (KPP) R&D Simulator Algorithm Blueprint.pdf
 file://file-DEKb2MeVDubPyHbxBzQBuC
 Kinetic Power Plant (KPP) Technology White Paper.pdf
 file://file-Wn4JQYdoC26QBSWsGJd8r8
 KPP Feasibility and Claims Analysis_.docx
 file://file-1JPZjZMPCt1FnZ7Y2psKxd
 Stage 2 Upgrade_ Real-Time Simulation Implementation Guide.pdf
 file://file-UVKDQgJCEP8LPwraen4Q7s
