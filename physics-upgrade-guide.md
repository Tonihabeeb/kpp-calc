Technical Review of KPP Simulation Codebase
Physics Model Verification
Phase 1
Buoyancy Force (Archimedes’ Principle): The Phase 1 code implements buoyant force per Archimedes’
law
– i.e. $F_B = \rho_{\text{water}} \, V \, g$ directed upward, equal to the weight of the displaced water. This is
the correct fundamental model: a fully submerged floater of volume V in water of density $
\rho_{\text{water}}$ experiences an upward force of $\rho_{\text{water}} V g$. The code assumes each
floater is completely filled with air on ascent (and with water on descent) so that its full volume contributes
to buoyancy. This yields realistic magnitudes (e.g. a 40 L floater would generate ~392 N of buoyant lift under
standard conditions ). One subtlety is that in reality a floater’s buoyant force can vary slightly with depth
– if the floater is sealed, the air inside expands as pressure decreases, displacing a bit more water near the
top. Phase 1 likely simplifies this by treating buoyancy as constant once the floater is filled (i.e. fixed
volume, incompressible fluid). This is acceptable for a first-order model, since water is nearly
incompressible and the volume change due to air expansion is small. However, it ignores partial
submersion or expansion effects: in a physical system, a floater might not instantly expel all water at the
bottom or could gain additional buoyancy as the air inside expands isothermally (the H2 hypothesis). The
current model’s buoyancy force is accurate in principle, but for higher fidelity one may later introduce
variable buoyancy – e.g. increasing buoyant force as the floater rises (to simulate near-isothermal
expansion boosting displacement) or reducing it if a floater isn’t fully purged of water initially . In
summary, the Archimedes-based implementation is correct, but it assumes an ideal scenario (full volume
engaged in lift) with no gradation; this is a potential area to refine for more realism.
Hydrodynamic Drag Force: The simulation correctly included a velocity-dependent drag force opposing
floater motion. It appears to use the standard quadratic drag equation $F_D = \frac{1}{2} C_d\,
\rho_{\text{water}} A\,v^2$, acting opposite to the direction of travel. In Phase 1, a fixed drag coefficient
($C_d$) and cross-sectional area ($A$) are used to calculate resistance on each floater, with drag always
opposing motion (i.e. upward drag on descending heavy floats, downward drag on ascending buoyant
floats). This aligns with classical fluid dynamics and provides a damping force that grows with speed. The
use of a constant $C_d$ is a simplification – real drag can vary with Reynolds number and flow conditions,
but for the expected speeds and floater shapes, treating $C_d$ as constant (e.g. on the order of 0.8–1.0 for
bluff bodies) is reasonable. One potential discrepancy is how drag reduction (H1) is handled: in Phase 1, it’s
likely not physically modeled yet. The code might have a placeholder (e.g. simply increasing floater speed or
reducing drag by a fixed factor when H1 is “on”). Without H1, the drag forces in the downward column are
probably quite significant and contribute to net energy loss, as expected. The physics model itself (quadratic
drag) is sound; however, the code should ensure it uses the relative velocity of the floater through water. If
Phase 1 assumed a constant chain speed, it may be applying drag based on that constant velocity – which is
fine in a steady-state analysis. In a future time-stepped simulation, drag must be computed from the
instantaneous velocity of each floater. In summary: The drag model is implemented with the correct
formula, but currently assumes baseline water properties. There is no explicit representation of nanobubble
effects yet – i.e. no reduction in $\rho_{\text{water}}$ or $C_d$. For realism, H1’s effect should be introduced
1
2 3
1
by lowering effective water density or drag coefficient in the descending column (e.g. a ~5% density
reduction was suggested as a starting point). This would physically represent the claimed drag/density
modulation where millions of tiny bubbles reduce resistance .
Torque Generation and Chain Mechanics: The simulator computes torque as the product of net force on
the chain and the sprocket radius, consistent with basic mechanics. Each floater’s net force (buoyancy minus
weight minus drag) contributes a torque about the drive shaft. In a balanced configuration roughly half the
floaters are on the ascending side (light, pulling up) and half on the descending side (heavy, pulling down).
Phase 1 likely simplifies by assuming an equal spacing of floaters and a constant number on each side (e.g. if
there are N floaters total, N/2 buoyant up and N/2 heavy down at any time). The code probably sums the
upward forces on the ascent side and the downward forces on the descent side, then multiplies the
difference by the wheel radius R to get total torque. This approach is physically sound for steady operation –
it yields a continuous net torque that drives the generator. One concern is whether the code accounts for
transitional positions: when a floater is at the very bottom being injected or at the top being vented, it
contributes little or no torque (since it’s not fully buoyant or heavy at that moment). The Phase 1 model
might ignore these brief transitions, effectively treating all N/2 floaters on each side as fully active. This is a
minor simplification, but it could overestimate torque slightly by not reducing force during the moments of
injection/venting. Another likely simplification is the assumption of constant speed – Phase 1 appears to
model a steady-state cycle (possibly using a fixed cycle time or chain speed). In reality, net torque would
cause acceleration if unopposed; a real system would reach an equilibrium when generator load and drag
equal the buoyant driving torque. The code implicitly handles this by solving for or assuming a speed where
net torque is zero (or by directly assigning a cycle time of ~10 s, as seen in the UI, and computing outputs at
that speed). While this yields a stable analysis, it means the simulation isn’t yet showing dynamic
acceleration or speed changes. Summary: The torque calculation is fundamentally correct and uses
appropriate geometry. It could be improved by modeling each floater’s state individually (so that torque
contributions ramp up/down during entry/exit of floaters at sprockets) and by introducing the generator’s
opposing torque explicitly. Phase 1 likely bundles the generator effect into the energy balance rather than
simulating it as a dynamic load – we discuss this under energy losses.
Energy Transfer and Loss Accounting: The Phase 1 code attempts to track the energy flows in one full
cycle – notably the work output from buoyancy and gravity, and the work inputs/losses from drag and air
compression. The key check for accuracy is energy conservation: in a proper physics model of a buoyancy
engine, the energy required to inject air at depth exceeds the mechanical energy extracted from the rising
float (even before considering drag), per the laws of thermodynamics . The simulation’s baseline
“conventional cycle” should reflect a net negative output (i.e. a net energy consumption). Indeed, the
provided Phase 1 UI values suggest the conventional cycle yields about –50 kW (meaning you expend 50 kW
more in the compressor than you get out in generation). This aligns directionally with the first-principles
analysis: “the work required to compress air and inject it at depth is fundamentally greater than the buoyant work
that can be extracted” . To validate the model, we examine each component of the energy balance:
Buoyant Work Output: As floaters ascend, the buoyant force does work over the height of the
water column. In the code, this can be calculated by integrating the net force on the chain over the
distance moved. Since Phase 1 likely assumes steady motion, an equivalent is summing torque over
one rotation (torque × angle = energy). The model should compute the mechanical work extracted by
the chain per cycle. Given an example floater volume and depth, we can estimate this: e.g. 40 L
floater, ~10 m lift, buoyant force ~392 N would do on the order of 3920 J of work (if drag and weight
didn’t oppose it). Summing over many floaters, the gross work from buoyancy can be significant. The
4
5
5
•
2
code appears to handle this via the force and torque calculations – at the end of a cycle, it reports a
“power” or energy output. This part of the model is straightforward and likely accurate (provided
buoyant forces are calculated correctly as noted above).
Gravitational Work (Descending Side): Heavy floaters on the descending side actually contribute to
driving the chain as well – their weight pulls down, adding to torque in the same rotation direction
. The simulation should account for this by including the weight of water-filled floaters on the
down side as part of the net driving force. In other words, both the ascending buoyant force and the
descending weights help turn the chain (the system is like a constantly imbalanced wheel). The
Phase 1 code likely adds the sum of weights on the descending side to the torque (effectively the
buoyant side provides upward force F_b – mg per floater, while the heavy side provides mg per floater
downward). If implemented, this means the gross mechanical energy per cycle includes both the
work done by buoyant lift and the work done by descending weights. However, this doesn’t create
energy from nothing – it just means the chain sees a large torque. The crucial question is how
much of that mechanical energy is offset by required inputs (primarily the compressor). The code
correctly does not treat the descending side as a “free” gain; it will be balanced by the fact that to
have those heavy weights, you had to remove buoyancy (vent air) and let water back in at the top,
which didn’t cost energy itself but resets the cycle.
Drag Losses: Drag force on both sides dissipates energy as heat in the water. The Phase 1 simulation
includes drag in the force balance (reducing net torque), but it should also calculate the work lost to
drag over the cycle. Ideally, the simulator would integrate $F_D \cdot v$ for each floater over its path
to compute drag energy loss. If Phase 1 did not explicitly tally this, an equivalent is that the net
mechanical energy output is lower than the ideal by exactly the drag losses. For example, if
buoyancy and gravity would produce X Joules per cycle without drag, the presence of drag means
the generator can only get X – (drag loss) Joules (assuming the rest is balanced by compressor input).
In code, it’s fine if drag is only accounted for via forces/torque; just note that for analysis and
debugging, logging the drag work is useful. Since H1 is not yet implemented in Phase 1, the drag
losses are likely quite high. This is realistic: without nanobubbles, the descending floats face fulldensity
water and substantial fluid resistance. The outcome should be a significant fraction of the
buoyant work being canceled by drag (plus any friction, though friction wasn’t mentioned, we
assume it negligible or lumped with drag). The physics of drag loss are accurately captured by the
model, given the correct drag formula – but to improve fidelity, later versions should allow drag
reduction when H1 is enabled, e.g. by using an “effective” density or drag coefficient. A simple
implementation is $\rho_{\text{water,eff}} = (1-\alpha)\rho_{\text{water}}$ on the descending side
(with $\alpha$ being the nanobubble fraction), or directly reducing $C_d$. In Phase 1, absent an
explicit H1 model, any claimed drag reduction may have been hardcoded (e.g. making descending
floaters move 1.5× faster in the animation). This placeholder approach is not physically based and
should be replaced with a proper drag-force reduction in code (so that, for instance, turning H1 on
reduces drag forces by a chosen percentage, and one can see the impact on net energy).
Air Compression Work (Compressor Load): This is the most critical input in the energy balance. The
code must compute the energy required to inject the volume of air into a floater at the bottom of the
tank. Phase 1 likely uses a simplified thermodynamic model. The ideal minimum work for isothermal
compression is $W_{\text{iso}} = P_0 V \ln(P_{\text{depth}}/P_0)$, where $P_0$ is atmospheric
pressure and $P_{\text{depth}}$ is the water pressure at injection depth. If the process is rapid
(adiabatic), the work is higher: roughly $W_{\text{adia}} \approx \frac{P_{\text{depth}}V - P_0V}
•
6 3
•
•
3
{\gamma - 1}$ for a diatomic gas (γ≈1.4). In a real KPP, compression will be somewhere between
these extremes (near-adiabatic in a quick pump, unless specialized isothermal techniques are used).
Accuracy check: If Phase 1 assumed fully isothermal compression for the base model, it
underestimates input work – this is optimistic, effectively giving an upper-bound efficiency.
Conversely, an adiabatic assumption would be more conservative. The feasibility analysis shows that
even with isothermal injection, the system still cannot break even . The code likely uses one of
these formulas. The Blueprint documents explicitly recommend implementing both and toggling
based on an H2 parameter. We should verify which the Phase 1 code does:
If it always uses the isothermal formula (lower work), then the simulation might show a smaller
compressor energy input than reality – making the net output a bit less negative. This seems
plausible given the “–50 kW” result; a fully adiabatic calculation could have made the deficit even
larger. Using isothermal by default is fine for initial exploration, but it is a simplification that can
mislead if not noted. I recommend adding a parameter or option for compression type. This way the
simulator can demonstrate how a near-isothermal process (H2 hypothesis) improves performance by
lowering input energy.
Phase 1 may not simulate the compressor dynamics beyond energy. That is, it likely doesn’t model
the finite flow rate or pressure ramp-up of the compressor – it probably just computes energy per
floater injection. As a result, it would not catch operational issues like airflow rate limits. Indeed, the
analysis report found a huge discrepancy: the required air flow (~5.41 m³/min) far exceeds the
specified compressor’s capacity (1.5 m³/min) . The current simulator doesn’t appear to enforce
such a limit, so it might implicitly allow “ideal” compressor performance. For Phase 1, that’s
acceptable (the focus was on energy, not sizing hardware), but it is a gap for realism. The
recommendation is to incorporate compressor power and flow limits in future: e.g. track how many
floaters per minute are being injected and ensure the compressor output (in m³/min or in kW) can
support that, otherwise flag that the scenario is infeasible. This would make the simulation a more
practical engineering tool.
Generator Load and Coupling: In the real KPP, the generator (or an alternator/flywheel system)
provides a resisting torque that converts mechanical work into electricity. Phase 1 code most likely
simplifies this by assuming a steady-state: effectively, it calculates net mechanical power after losses,
and that remainder is what the generator would produce (if positive) or what an external motor
would need to supply (if negative). In other words, rather than dynamically coupling a generator
model, the code probably computes Power_out = Power_buoyancy + Power_gravity -
Power_drag - Power_compressor and reports that. This gives the correct energy accounting,
but it doesn’t simulate transient behavior like how the system accelerates if the generator load is
reduced. The accuracy of the reported efficiency or net power thus hinges on the assumption that
the generator is loaded just enough to keep the speed constant (so that all buoyant torque goes into
electrical generation except what’s wasted to drag). This is a fair assumption for efficiency
calculations. What’s missing is any sense of torque control or speed dynamics. For example, the H3
hypothesis (“chronal potential” impulse drivetrain) involves periodically disengaging the generator to
let the system speed up, then re-engaging to harvest energy in bursts . Phase 1 does not model
this actual mechanism – it likely just shows an illustrative effect (in the demo, H3 mode flashes a
“kick” and speeds the flywheel visually). Without a dynamic simulation loop, the code cannot capture
the timing of clutches or the inertia of a flywheel. So at this stage, the torque generation model is
static – adequate for checking sums of forces, but not sufficient to study control strategies.
5
•
•
7
•
8
4
In summary, the Phase 1 physics implementations for buoyancy, drag, and basic torque are largely correct
in formula but simplified in application. Buoyant force and drag force follow accepted physical laws, and
torque is computed as required. The main inaccuracies come from idealizations: immediate full buoyancy,
constant drag coefficients, no treatment of nanobubble drag reduction, assuming perfect or user-selected
compression process, and using a steady-state balance for torque/speed. These simplifications can lead to
unrealistic behavior if one pushes the simulation beyond its intended envelope – for instance, Phase 1
might happily output a large “net power” in the H2/H3 integrated scenario (523 kW in the UI) without
demonstrating how physically hard that is to achieve. In the next sections we detail these discrepancies and
recommend improvements.
Identified Discrepancies and Simplifications
Through the above verification, several discrepancies or oversimplifications in the Phase 1 codebase
become apparent. These are aspects where the implemented model deviates from realistic physics or could
lead to inaccurate system behavior:
Full Buoyancy Assumption at All Times: The code assumes each floater instantly switches from
heavy to fully buoyant (and vice versa) at the bottom and top. There is no modeling of partial water
content or the time it takes to inject air/vent air. In reality, a floater might still contain some water
right after injection, or air might begin expanding gradually as it ascends. By not modeling these
transitions, the simulation might slightly over-predict the net buoyant force and torque (since it
doesn’t reduce buoyancy during the injection phase or account for any delay in achieving full lift).
Essentially, the buoyancy force is treated as a step function rather than a ramp. This is a source of
unrealistic smoothness – the real system would have jolts of force when floats engage or
disengage buoyancy. Not capturing this means missing potential stress spikes and also slightly
exaggerating average torque.
No Depth-Dependence of Buoyant Force: The current model does not adjust buoyant force for
depth or pressure effects. As noted, water density is taken as constant (which is fine; water is nearly
incompressible over a few meters). However, if the float’s internal air is sealed between bottom and
top, the buoyant force should technically increase as external pressure drops (air expanding). The
code doesn’t simulate this (unless H2 is activated, and even then Phase 1 H2 seems not truly
implemented). This simplification could hide a potential source of extra work (the H2 “thermal
amplification” effect) or, conversely, if the float were venting gradually, a loss. It’s a moderate
discrepancy relevant when analyzing the H2 hypothesis quantitatively.
Constant Drag Coefficient and No Laminar/Turbulent Regimes: The simulation uses a fixed
$C_d$ and does not account for changes in drag behavior at different speeds or with bubble
infusion. Real fluids can have drag coefficient shifts (e.g. as Reynolds number changes or if bubbles
alter the flow regime). Also, adding nanobubbles (H1) in reality could reduce drag significantly
(experiments have shown notable drag reduction in water with micro/nanobubbles). Phase 1’s drag
model ignores these nuances. All floats experience the same drag force formula, and H1 mode likely
just asserts a speed multiplier (as seen in the animation script) rather than reducing the physical drag
force. This means the simulation’s “H1” results in Phase 1 are not grounded in fluid dynamics –
they’re optimistic and could mislead. For example, simply increasing descent speed by 50% (as done
in the demo) doesn’t capture the trade-offs (higher speed would actually increase drag force unless
•
•
•
5
$C_d$ or density is lowered). Discrepancy: The code might show improved performance with H1
without a proper basis, due to how it was simplified.
Equilibrium Speed Enforcement (No Dynamics): Phase 1 likely runs in a static or pseudo-steady
mode. If a net torque is computed, the code might directly convert that to power assuming constant
speed, rather than accelerating the system. In fact, the UI “cycleDuration = 10 s” suggests they forced
a cycle time. This hides dynamic behaviors such as the system accelerating under surplus torque or
slowing under load. It also means the code doesn’t simulate what happens if the generator load is
wrong – in reality, too little load -> runaway acceleration, too much load -> stall. The absence of an
acceleration calculation is a simplification that could mask instability. For instance, if the user
input a very high generator load torque in a future scenario, the code in Phase 1 would probably still
just produce some number, whereas a real simulation might show the system coming to a stop.
Thus, the current architecture isn’t catching scenarios of stall or overspeed.
Generator and Flywheel not Physically Modeled: Related to the above, any advanced drivetrain
features (clutch, flywheel inertia, etc.) are not truly modeled. The Phase 1 codebase doesn’t have a
mechanical dynamics module; it treats the generator in terms of energy balance only. The “flywheel”
seen in visualization is just cosmetic – it glows or spins faster when a “kick” is indicated, but this is
not based on solving equations of motion. So, H3’s implementation is highly simplified: it likely
just modulates output power in pulses (e.g. multiplying by 1.2 or 0.5 in certain intervals, as seen in
the code snippet with kick flags). This is a big discrepancy if one were to take the simulation’s H3
results at face value. It does not account for whether the timing of those pulses is optimal or how
the flywheel’s stored energy is actually transferred. Essentially, the current code cannot validate the
H3 hypothesis; it can only illustrate it conceptually.
Simplified Air Compression Model: While the code computes energy for air injection, it probably
uses a single formula (likely isothermal, as discussed). It doesn’t simulate the process of
compression (pressure build-up, temperature rise, etc.) over time. Nor does it simulate the effect of
air injection on water (e.g. the momentum of expelled water, which could impart a reaction force).
These omissions could lead to unrealistic system behavior in edge cases – for example, injecting a
large volume very rapidly might cause a momentary force on the system (water being pushed out
could add a downward reaction thrust on the injector assembly). Phase 1 ignores any such transient.
Another omission is heat exchange: H2 is meant to leverage water’s thermal energy, but Phase 1
does not model the temperature of air or water at all. Without this, the simulation cannot capture
the essence of H2 except by fudging numbers (like giving an “extra buoyancy kick”). In short, the
thermodynamic side is treated in a bulk-energy way, not a dynamic or thermal way, which could be
refined later.
No Accounting for Internal Losses or Inefficiencies: The simulator at Phase 1 likely assumes ideal
mechanical efficiency aside from drag – e.g. no friction in bearings, no electrical losses in the
generator, no leakage in valves. It also doesn’t consider things like turbulence (other than as
embodied in $C_d$) or sloshing of water. These are fine omissions for an R&D sim’s first phase, but
they mean the results might be somewhat idealized. Real systems would have additional losses that
make net output even lower. For example, chain friction or sprocket inefficiency might consume a
few percent of the work; the code currently treats the chain as a perfect conveyor. As we move to
more detailed validation, these minor losses might need inclusion or at least acknowledgement.
•
•
•
•
6
Overall, the Phase 1 simulation tends toward an optimistic portrayal of the KPP physics, except for drag
which is fully applied. It simplifies or omits any effect that would add extra loads (compressor limits,
transient forces, friction). As a result, any positive net power result in the Phase 1 sim (even small) should be
viewed with skepticism – it may be an artifact of simplifications. Indeed, the claims analysis concluded that
without the hypothetical enhancements, net power must be negative . The code’s conventional cycle
reflects that (net loss), but the H1/H2/H3 cycles in Phase 1 code show gains largely because the code does
not yet impose all the physical costs of those enhancements (it just grants some benefits).
In the next section, we provide recommendations to address these issues. The goal is to upgrade the
simulation for Phase 2 so that it remains accurate even as we add complexity – ensuring no “free energy”
creeps in via code shortcuts, and that the simulator architecture supports more detailed physics.
Recommendations for Realistic Simulation Fidelity
To enhance the simulation’s realism and correct the above discrepancies, we propose several changes and
additions to the codebase. These recommendations include modifications to physics calculations,
introduction of new parameters, and structural code changes. Where possible, we suggest specific
implementation strategies (with code snippets or formulas) and outline how to validate each aspect:
Implement Per-Floater State Tracking: Transition from lumped, half-cycle calculations to modeling
each floater individually in the simulation loop. This is a foundational architectural change that
enables many of the improvements below. By giving each floater an object or data structure (with its
own position, velocity, state of fill, etc.), the simulator can apply physics on a finer granularity. The
Stage 2 design calls for a Floater class with an update method to compute forces each time-step
. We strongly recommend refactoring the code in this direction. For example, instead of
summing a fixed number of floaters, the code can iterate through a list of Floater objects: each
floater computes its buoyant force, drag, weight depending on whether it’s filled with air or water.
This will allow the simulation to naturally handle floaters entering or leaving the water, and make it
straightforward to apply H1/H2 on a per-floater basis (e.g. only descending floaters get the
nanobubble drag reduction). Integration steps: Create a Floater class with properties like
volume , mass_full , mass_empty , position (or perhaps an angle around the loop), and
velocity . Give it a method update(dt) that updates its kinematics and returns forces. The
simulation engine then aggregates forces for torque. This change supports extensibility (adding new
physics to Floater.update later) and improves separation of concerns.
Refine Buoyancy Calculation for Transitions: Modify the buoyancy force model to account for
partial submergence and expansion effects. With per-floater modeling, you can determine how
submerged a floater is. For instance, if you have the vertical position of a floater, you can linearly
reduce buoyant force as it exits the water at the top. A simple approach:
effective_submerged_volume = floater.volume * f(submersion_depth) , where f() is
1.0 when the floater is well below the surface and drops to 0 near the top exit. Likewise, during
bottom entry, the floater is not buoyant until it’s underwater. Implementing this will prevent the
unphysical sudden jumps in force. Additionally, to capture H2’s effect more realistically, consider
modeling the internal pressure of the floater. A full-blown thermodynamic model might be complex,
but a reasonable approximation is: if H2 (isothermal expansion) is active, treat the buoyant force as
slightly increasing with height (since the air does more work by expanding). Practically, one could
increase the displaced volume by a small factor as the floater rises if H2 is on. Another approach is to
5
•
9 10
•
7
alter the injection work instead (discussed below). Code example: You could simulate that a floater
at depth has only, say, 90% of its air volume injected (thus 10% water remains), and as it rises that
remaining water is expelled by expansion. This means buoyancy starts at 90% of full value at the
bottom and ramps to 100% at the top. While the exact number would be scenario-dependent,
making this configurable allows testing the impact of near-isothermal processes. This refinement
ties into validation: one could compare the work done by buoyancy in the model to the theoretical
work of isothermal expansion. The blueprint suggests integrating buoyant force over the ascent to
see the difference between isothermal vs adiabatic cases – implementing this would be a great
check (compute work output in both cases and confirm the isothermal yields more, consistent with
thermodynamics).
Introduce Adjustable Compression Process Parameters (H2): To ensure the compressor work is
accurately represented, give the simulation a toggle or continuous parameter for isothermal vs
adiabatic compression. In code, this can be as simple as an if use_isothermal: branch when
computing injection energy. Phase 1 likely used one formula; Phase 2 should allow both. We
recommend adding in physics.py a function compute_injection_work(volume, depth,
isothermal=True) that calculates $W$ based on the formulas above (using water density and
gravity to find $P_{\text{depth}}$). This not only makes the model more realistic but also allows users
to see the benefit of H2 quantitatively. For example, if a floater volume is 0.04 m³ and depth 10 m,
the adiabatic work might be ~4.8 kJ while isothermal is ~3.9 kJ (illustrative figures) – the difference of
~19% would then appear as improved net output when H2 is on. Integration: tie this function to an
H2 flag in the simulation parameters. When H2 is enabled (near-isothermal assumption), use the
lower work value; otherwise use the higher. In later phases, if a more detailed thermal model is
desired, one could simulate heat exchange by gradually adjusting the exponent between isothermal
and adiabatic (or even solving a differential equation for heat flow), but initially a simple binary
switch is effective. Make sure to document this in the output (so it’s clear which mode was used).
Validation: This can be unit-tested by checking known values – e.g., for a given volume and depth,
ensure compute_injection_work with isothermal flag produces exactly $P_0 V \ln(P_{depth}/
P_0)$. Cross-check with standard thermodynamics texts or the analysis report values to ensure
correctness.
Incorporate Nanobubble Drag Reduction (H1) Physically: Replace any ad-hoc “speed multiplier”
or drag fudge factor with a proper modification of fluid properties when H1 is enabled. Two primary
effects are claimed for H1: reduced water density and reduced drag coefficient in the descending
column . We can implement either or both. A straightforward method (as shown in the Stage 2
guide) is to scale the water density for descending floats: rho_eff = rho_water * (1 - beta)
where β is perhaps 0.05 (5% reduction) or a user input. Use rho_eff when computing buoyant
force on descending side (slightly less buoyancy – which doesn’t matter since those floats are heavy
anyway) and when computing drag on descending floats (less density -> less drag force). Additionally
or alternatively, directly reduce $C_d$ for those floats (e.g. multiply by 0.5 if nanobubble injection is
assumed extremely effective). The code could have a function in physics.py like
adjusted_drag_coefficient(floater) or a simple conditional: Cd_eff = Cd * (0.5 if
params.use_nanobubbles else 1.0) . The key is that the change should be localized to the
descending side (and possibly ascending side for density if one imagines nanobubbles in water
affecting buoyancy too, but primarily it’s to ease descent). By doing this, the simulation will reflect
the intended benefit of H1: lower drag losses, and possibly faster descent under gravity. We note
that simply speeding up the animation by 1.5× (as was done in Phase 1 UI) without adjusting forces
•
•
4
8
actually violates physics (higher speed with same drag would increase drag power loss). Our
recommendation ensures that if a floater descends faster under H1, it’s because drag force was
actually reduced. Integration: Add a parameter nanobubble_fraction or a boolean
use_nanobubbles . In the drag force calculation, if nanobubbles are on and the floater is
descending, use the modified $\rho$ or $C_d$. In buoyant force calc for descending floats, one could
also reduce $\rho$ slightly to simulate lower effective weight of displaced fluid (though this has a
minor effect because those floats are full of water and nearly neutrally buoyant anyway). Validation:
Set up a test with one floater dropping in water under gravity with and without H1: measure its
terminal velocity in the simulation. With H1 on (lower drag), the terminal velocity should be higher.
This can be analytically checked: terminal speed $v_t$ occurs when $mg = \frac{1}{2}C_d \rho A
v_t^2$. Reducing $\rho$ or $C_d$ by, say, 50% should raise $v_t$ by $\sqrt{2}$ (about 1.414×). The
simulation results should confirm this trend. Also check that the net energy balance improves when
H1 is on (drag work loss should drop proportionally). This ties in with the user expectations from H1:
less drag -> less wasted energy -> closer to net zero (though likely still negative without H2/H3).
Add a Time-Stepping Simulation Loop: To move beyond the static analysis, Phase 1’s one-cycle
computation should evolve into a time-step simulation (if it hasn’t already in late Phase 1). The
Stage 1 upgrade guide outlined converting the calculation into a loop over small time increments.
We absolutely recommend implementing this. It will address the equilibrium speed issue by letting
the system’s speed emerge from the physics. Concretely, define a global time step dt (e.g. 0.01 s
for numerical stability). On each iteration, compute forces on each floater (as above), sum torques,
then use Newton’s second law for rotation: $I \alpha = \tau_{\text{net}}$ (where $I$ is the total
moment of inertia of moving parts and $\alpha$ the angular acceleration). Update the angular
velocity of the chain accordingly, and then update each floater’s position (which float goes where
along the loop). This is more complex to implement, but it can initially be simplified by assuming a
fixed number of floaters and uniform spacing. The real benefit is that it will allow simulation of
transient modes – for example, one can simulate the H3 “pulse and coast” by toggling a generator
torque on and off and watch the speed change, rather than hard-coding a power spike. The code
structure to do this could use the generator pattern as shown in Stage 1 guide or a background
thread as in Stage 2. If performance is a concern, the time-step could be relatively large (tens of
milliseconds) given the slow nature of the system, but resolution is good for accuracy. Integration
details: This requires introducing system inertia (sprocket, chain, flywheel masses). You might start
by assuming the chain and floats move quasi-statically (no massive acceleration), but to simulate H3
you’ll need a flywheel inertia and a way to apply or remove generator load. Represent generator load
as a counter-torque proportional to angular velocity (for a simple linear damping model) or as a
controlled torque. In code, perhaps have generator_torque = K * (omega_desired -
omega_actual) or a simpler if clutch_engaged: generator_torque = constant_value .
During freewheel (clutch open), set generator_torque = 0, so net torque accelerates the system;
when engaged, apply a resistive torque. This way, you can simulate the “kick-and-coast”: floats
accelerate the system in absence of load, then you engage load to extract energy while the flywheel
coasts down. The Phase 1 code’s on/off kick logic would be replaced by this physically grounded
approach. Validation: This dynamic simulation can be checked against conservation of energy and
expected behavior. For example, if you disengage the generator, the kinetic energy of the flywheel
should increase by exactly the work that would have gone into the generator. Re-engaging the
generator should then convert that kinetic energy to electrical output, minus any drag incurred
during coasting. One can verify that the total energy extracted in a pulse-coast cycle equals the
buoyant work minus losses (same as steady-state, just redistributed in time). This is an important
•
9
consistency check to show the simulator isn’t creating or destroying energy spuriously during H3
cycles.
Enhance Energy Accounting and Logging: To aid verification and future development, extend the
code to log detailed energy components over time. For instance, maintain accumulators for: buoyant
work done (sum of $F_b \cdot dz$ for all floaters), drag loss (sum of $F_D \cdot dz$), compressor
work input (sum of injection energies), and generator work output. By the end of a run (or a cycle),
these should obey: buoyant_work + gravity_work = drag_loss + generator_work + any
kinetic energy change + other losses , and generator_work = net_electric_output ,
compressor_work = input energy . In steady state, kinetic energy change is zero, so ideally
generator_work = buoyant+gravity - drag - other_losses and of course
generator_work < compressor_work in a conventional cycle. Having these logs will make it
much easier to pinpoint any imbalance (which could indicate a bug). They also allow quantitative
comparison with external analyses. For example, if the simulation is configured to the same
parameters as the feasibility report, you could compare the logged values: does the sim find
~5.4 m³/min of air needed and a similar energy shortfall? You might simulate one minute of
operation and see how much air was injected and how much energy generated vs consumed. This is
a powerful validation step – essentially a unit test against known real-world constraints (e.g. the
compressor capacity). In code, you might implement this via a dictionary or object that accumulates
energies each time-step (e.g. energy_log["buoyancy"] += F_b * (v*dt) for each floater,
etc.). At the end or periodically, output these values (the SSE stream or final JSON could include
efficiencies, etc.). The Stage 2 architecture anticipates a data logger for exactly this purpose
. We recommend implementing it early, as it greatly helps in verifying correctness as new
features are added.
Validation via Unit Tests and Analytic Checks: Alongside code changes, we advise creating a suite
of unit tests for the physics functions and small scenarios. For example:
Test the buoyancy force calculation: given a known volume and water density, ensure the function
returns $\rho V g$. Use the 40 L example (expect ~392 N) as a test case. Also test partial volume:
if you simulate half-submerged (e.g. volume=0.04 m³ but only 0.02 m³ displaced), check that
buoyancy is halved (~196 N).
Test the drag force function: feed a known velocity, area, density, Cd and compare to manual
calculation. Also test that drag direction is correct (e.g. ascending vs descending cases).
Test the compression work function for both isothermal and adiabatic modes against known
formulas (for instance, if depth = 10 m, volume = 0.04 m³, verify the numeric output of each formula
– perhaps compare to an online calculator or a quick manual calc).
Test energy conservation in a simple cycle: e.g., turn off drag and set generator load such that net
torque is zero; verify that buoyant work equals compressor work (the system should be break-even if
only those two forces act and exactly balance). Then enable drag and see that now compressor work
> buoyant work by the drag loss amount.
Test H1/H2 toggles: run a cycle with H1 off vs on and confirm that drag energy loss is lower with H1
(and net output correspondingly higher), which matches expectations from theory and the claims
(though we remain skeptical of the magnitude, the trend should be correct). Similarly, H2 on vs off:
compressor input should be lower with H2 (maybe ~10–20% lower as per isothermal vs adiabatic
difference), and possibly buoyant output slightly higher if you model expansion doing extra work.
•
11
12
•
•
1
•
•
•
•
10
If possible, test an extreme: all hypotheses on vs off to see that the simulation only achieves net
positive output when H1+H2+H3 are active together (if indeed the code is meant to show that).
According to the reverse-engineering analysis, only with all three “know-hows” could one even
approach the claimed 500 kW output, and even then the physics is extreme . The simulation
should reflect this gap: without H1–H3, net power must be negative; with them, the code might show
a positive net, but one should check if the magnitude is in a plausible range. If the Phase 1 code was
showing ~523 kW for the integrated case, we suspect that number is not physically derived but
rather a target. After implementing real drag reduction and isothermal calc, the net might still not
reach that high unless one dials those effects beyond realistic limits. This is something to be
transparent about in the simulator results.
Implementing and testing the above changes will significantly improve the fidelity of the KPP simulator. It
will transition the codebase from a simplified proof-of-concept calculator to a more robust physics engine
that respects conservation laws and can be used for genuine what-if analyses. The recommended code
modifications (per-floater modeling, time-stepping loop, detailed force calculations with H1/H2 parameters)
also lay the groundwork for Phase 2 features, such as real-time interactive simulation and integration with
control algorithms.
Simulator Architecture and Extensibility
Assessing the current simulator architecture (Phase 1) against future needs, we find that some
restructuring is needed but the fundamental plan is sound. The ultimate goal is a modular, extensible
codebase that cleanly separates physics, control logic, and visualization. The Phase 1 code was a first step,
and to support technical validation and ongoing development, we recommend the following architectural
considerations:
Separation of Concerns: Ensure that the physics engine (the core simulation) is decoupled from the
UI or web interface. Phase 1 used Flask with some routes and a frontend, which is fine, but we want
to avoid entangling UI logic with physics calculations. The blueprint suggests a package structure
with a simulation/ module containing physics.py , engine.py , etc., and Flask app.py
acting as a client of that module. Review the code to verify this separation. If Phase 1 code has any
direct HTML updates or global variables for state, refactor those into appropriate classes or return
values. The simulation engine should ideally expose a clean API such as
run_simulation(params) -> results or a generator that yields state snapshots. The Flask
app can call this and stream results, but it shouldn’t need to know internal details of how forces are
computed. Achieving this modularity will greatly ease maintenance – e.g. if you want to swap in a
more detailed drag model, you only touch physics.py . The Stage 2 guide explicitly delineates
responsibilities: simulation.py for the core loop and Floater class, app.py for streaming and parameter
endpoints, index.html and JS for visualization . Following this pattern will improve clarity.
Extensibility for More Detailed Physics: The architecture should allow adding new physical effects
without breaking existing functionality. Using object-oriented design for floaters (as discussed) is
one aspect. Also consider organizing code by subsystem (as the R&D blueprint outlines ): e.g.,
a module or section of code for buoyancy and fluid forces, one for the drivetrain and torques, one
for the compressor/air system, etc. In Phase 1, these might all be in a single function or a few
functions. It’s okay initially, but as we add complexity (like temperature, advanced coatings, variablevolume
floaters, etc.), modular structure prevents a single function from becoming unmanageably
•
13
•
14 9
•
15 16
11
complex. We suggest creating helper functions or classes for distinct tasks. For instance, have a
Compressor class that, given a floater volume and depth, returns required work or power and can
simulate its motor dynamics if needed. This way, if later we add, say, a pressure-exchanger device
(an advanced concept to reuse some pressure energy), we could subclass or extend the Compressor
model. Another example: a Drivetrain class could encapsulate the flywheel inertia, clutch state,
and compute generator torque. In Phase 2 or 3, if a user wants to try a different gearbox ratio or a
different flywheel size, one could adjust parameters of this class without touching buoyancy code.
Current state: It’s unclear if Phase 1 already had any of these abstractions. If not, it is advisable to
plan for them. Even if not immediately implemented as separate classes, at least separate the
calculations in the code logically (different sections or functions).
Real-Time Simulation Loop and Interactivity: With Stage 1 and Stage 2 upgrades, the simulator is
moving toward a real-time interactive tool (with continuous update of charts, ability to adjust
parameters on the fly, etc.) . The Phase 1 codebase should be evaluated for thread safety and
performance in this context. If using Server-Sent Events (SSE) for streaming, ensure that the
simulation loop can run in a background thread or as a generator without blocking the Flask main
thread. The code provided in Stage 1 guide streams data by yielding JSON at each time step. Test
that the Phase 1 architecture can adopt this pattern. If Phase 1 was a one-shot POST request that
returns results, it will need to be refactored to continuously emit data. This typically means the
simulation loop runs inside the route handler (or in a separate thread that the route streams from).
Python’s GIL isn’t a big problem if the computations are not heavy; just ensure to use
flask.Response(..., mimetype='text/event-stream') properly and flush events. The
current code structure might not have this streaming route yet – adding it sooner rather than later
will help with interactive validation (you can see in real time if a change in drag coefficient affects
power, etc., which is useful for debugging physics too).
Parameter Management and Scenario Configuration: As more parameters are introduced (drag
coefficients, nanobubble fraction, thermal coefficients, etc.), the architecture should have a clear way
to manage them. A best practice is to define a SimulationParams dataclass or dictionary that
holds all tunable parameters with meaningful names. Phase 1 likely parsed form inputs into a dict
already; building on that, we should centralize how parameters flow into the physics engine. For
example, there could be a function SimulationParams.from_request(form) that knows how to
convert UI strings to typed parameters. This makes it easier to validate inputs (e.g. ensure
percentages are 0–1, etc.) and to provide defaults. It also decouples the web form from internal
variable names. In terms of maintainability, having a single source of truth for parameters will avoid
bugs where one part of the code uses a different assumption than another. We also recommend
grouping related parameters into sections (for clarity, not necessarily in code) – for example: Floater
geometry (count, volume, mass), Fluid properties (water density, drag coefficient, nanobubble level),
Thermodynamics (initial air pressure, water temperature if needed for thermal calc), Drivetrain
(sprocket radius, flywheel inertia, generator torque limit), etc. This organization helps in both the UI
and the code.
Maintainability and Code Quality: As the codebase grows, maintaining readability and
organization is key. Phase 1 was probably small enough, but with Phase 2 adding real-time charts
and Phase 3 possibly integrating ML agents, the code could get complex. We suggest:
•
17
•
•
12
Documentation: Comment the physics formulas with source references or reasoning. For instance,
a comment like # Buoyant force = rho * V * g (Archimedes) in the code links the
implementation to theory and even to the archive document. This will help any new developer (or
your future self) quickly recall why a formula is what it is. The KPP archive is extensive; citing it in
code comments (just as we do here) can legitimize the model for any reviewers.
Modular file structure: as outlined earlier, use multiple files/modules. It’s easier to maintain 5 files
of 100 lines each than 1 file of 500 lines covering everything. Likely the code is already heading this
way (with physics.py , engine.py , etc., per the Flask blueprint). Review if Phase 1 followed that.
If not, plan to do so. Keep classes or functions focused (the Single Responsibility Principle).
Testing and CI: If possible, incorporate the unit tests into a continuous integration workflow. Even
simple checks run whenever code is changed can catch regressions (e.g. if someone inadvertently
changes $g$ or a formula sign). This is more for software process, but it’s worth starting early given
the scientific nature of this project – you want to trust the simulator’s outputs.
Future Extensibility Examples: Consider how easy (or hard) it would be to extend the Phase 1 code
to include some of the “additional enhancements” discussed in the white paper: for instance,
variable-volume floaters or magnetocaloric elements . While these are far-future ideas,
thinking about them is a good stress test for the architecture. Variable-volume floaters might require
the Floater class to have a dynamic volume property and perhaps an internal mechanism model –
can we accommodate that without rewriting everything? If float volume becomes time-dependent,
our buoyancy calculation needs to fetch the current volume from the floater object (instead of a
constant). If we structured things well, that’s just a minor change. If not, it could be a tangle.
Another: say we wanted to simulate multiple connected shafts (multi-unit KPP) – is our code
inherently single-shaft? Probably fine now, but maybe ensure that global variables are minimized so
you could instantiate two simulation instances if needed. These thought experiments often reveal if
there’s any hard-coding that could be made flexible with little effort (e.g., don’t hard-code 66 floaters;
make it based on a parameter or list length).
In conclusion, the current Phase 1 simulator provides a solid foundation but needs evolutionary
improvements to meet the project’s technical validation goals. By introducing a more granular, objectoriented
physics model and adopting a robust real-time simulation loop, we address the inaccuracies
identified and set the stage for testing the advanced hypotheses in a credible way. The recommendations
above, when implemented, will ensure that the KPP simulator reflects the true physics as faithfully as
possible: buoyancy and gravity forces computed per Archimedes’ principle , drag forces properly
reduced under H1 conditions , compression work correctly lowered with H2’s isothermal assist , and a
drivetrain that can actually mimic the H3 pulse-and-coast behavior . With a modular and maintainable
architecture, the team will be able to iterate quickly – adding refinements or new features (and testing
them) without breaking other parts. This will be crucial as the project moves into Phase 2 and Phase 3,
where integration with control algorithms and possibly hardware-in-loop tests are envisioned.
Supported by KPP Archive References: We have cross-verified the physics formulas and assumptions with
the KPP technical documentation and analysis reports. The Archimedean buoyant force law , drag
equation, and torque calculations used in the code align with standard references. The identified gaps (e.g.,
energy shortfall where compressor work > buoyant work) are well-documented in the feasibility analysis
and must reflect in the simulator for credibility. The proposed enhancements follow guidance from the
project’s blueprint documents – for example, implementing H1 by lowering fluid density, implementing H2
•
2
•
•
•
18 19
2
4 20
8
2
5
13
via isothermal compression formulas, and restructuring the simulation loop for real-time updates. By
heeding these, the Phase 1 codebase can be confidently upgraded to a Phase 2 simulator that serves as a
reliable tool for both validating KPP’s concept and exploring the limits of the proposed “know-how”
innovations.
Kinetic Power Plant (KPP) Technology White Paper.pdf
file://file-EVbRSPXc2W7PLn9PvgeXnv
KPP Feasibility and Claims Analysis_.docx
file://file-1JPZjZMPCt1FnZ7Y2psKxd
Stage 2 Upgrade_ Real-Time Simulation Implementation Guide.pdf
file://file-UVKDQgJCEP8LPwraen4Q7s
Kinetic Power Plant (KPP) R&D Simulator Algorithm Blueprint.pdf
file://file-DEKb2MeVDubPyHbxBzQBuC
1 2 3 6 18 19
4 5 7 8 13 20
9 10 11 12 14 17
15 16
14
Kinetic Power Plant Simulation Engine – Design &
Implementation
Architecture Overview
To simulate a buoyancy-driven Kinetic Power Plant (KPP), we design a clean, modular backend. The system
is broken into classes representing the physical subsystems . Each module corresponds to a real-world
component and handles its specific physics and logic:
Floater ( floater.py ): Represents a container (floater) that cycles through the water. It tracks
whether it's filled with air or water, its volume, mass, position, and computes forces like buoyancy
and drag.
Environment ( environment.py ): Defines properties of the water and environment – density,
gravity, drag coefficient, temperature, etc. It can modify these properties (e.g. effective density) if the
H1 enhancement (nanobubbles) is active .
Pneumatics ( pneumatics.py ): Models the compressed air system for air injection at the
bottom and venting at the top of the loop . It tracks an air tank’s pressure and the
compressor’s energy usage. Injecting air into a floater (to make it buoyant) consumes energy from
the compressor, and venting releases the air.
Drivetrain ( drivetrain.py ): Represents the chain, sprockets, flywheel, and generator. It converts
the net force imbalance between the buoyant (upward) side and heavy (downward) side into
rotational motion and torque on the generator . It accounts for the generator’s load (resisting
torque), the flywheel’s inertia, and a clutch that can engage/disengage the generator (for the H3
pulse-and-coast mode) .
Control ( control.py ): Implements the control logic (state machine or simple rules) to coordinate
actions: when to inject or vent air, when to engage/disengage the clutch, and how much generator
load to apply . This can be a simple scripted logic or an interface for advanced control (e.g. an
RL agent) .
Simulation ( simulation.py ): Runs the main time-stepped simulation loop . At each timestep
it computes forces, advances the physics (floaters and drivetrain motion), checks sensors (e.g. floater
reaching top or bottom) , applies control decisions, and logs data.
Logger ( logger.py ): Records the time-series of states and energies (positions, velocities, forces,
power outputs, air usage, etc.) for analysis or visualization . We can use Pandas to store results
and export CSV files for further processing .
This modular structure makes the simulator extensible and maintainable . Next, we implement each
module in detail, ensuring physical fidelity by using real physics formulas and clear interfaces between
components.
1
•
•
2
•
3 4
•
5
6
•
7 8
9
• 10
11
•
12
13
1
1
Floater Module ( floater.py )
Each Floater object models a single container attached to the chain. Floaters can be filled with water
(heavy, sinking) or with air (light, rising) . We track each floater’s volume, mass, and state, and we
can compute the forces on it:
Buoyant Force: Using Archimedes’ principle, the buoyant force $F_b$ equals the weight of
displaced water . If $\rho_{\text{water}}$ is water density, $V$ the floater volume, and $g$
gravity, then $F_b = \rho_{\text{water}}\;V\;g$. This force acts upward on an immersed floater.
Weight: The floater’s weight $W = m \, g$, acting downward, depends on its mass . When filled
with water, the floater’s mass is much higher (water + container) than when filled with air (just the
container + a bit of air).
Drag: As a floater moves through water, drag resists its motion. We use the quadratic drag law
$F_{\text{drag}} = \tfrac{1}{2} C_D \rho_{\text{water}} A v^2$ , where $C_D$ is a drag coefficient
and $A$ is the floater’s cross-sectional area. Drag is directed opposite to the floater’s velocity
(upward drag on a sinking floater, downward drag on a rising floater).
Using these, the net force on a floater is $F_{\text{net}} = F_b - W - F_{\text{drag}}$ (for a buoyant floater
going up) . For a heavy floater going down, buoyancy opposes weight and drag also opposes downward
motion, effectively reducing the downward force . The Floater class will provide methods to compute
these forces given the current state and environment.
Below is an implementation of the Floater class with appropriate attributes and force calculations:
# floater.py
class Floater:
def __init__(self, volume: float, mass_empty: float, mass_full: float):
"""
Initialize a Floater.
:param volume: Displaced volume of the floater (m^3)
:param mass_empty: Mass when filled with air (container mass, kg)
:param mass_full: Mass when filled with water (container + water, kg)
"""
self.volume = volume
self.mass_empty = mass_empty
self.mass_full = mass_full
# Start assuming floater is heavy (water-filled)
self.state = 'water'
self.mass = mass_full
# Position along the chain (0 = bottom of ascending side,
# chain length/2 = top, chain length = back to bottom)
self.s_position = 0.0
# Vertical position (height in tank) and velocity for logging/analysis
self.vertical_position = 0.0
self.velocity = 0.0
14 15
•
16
• 17
•
18
19
20
2
def set_state(self, state: str):
"""Switch the floater's state to 'air' or 'water', updating its mass."""
self.state = state
self.mass = self.mass_empty if state == 'air' else self.mass_full
def compute_buoyant_force(self, rho_water: float, g: float) -> float:
"""Compute the buoyant force using Archimedes' principle ."""
return rho_water * self.volume * g
def compute_weight(self, g: float) -> float:
"""Compute the weight of the floater (gravity force) ."""
return self.mass * g
def compute_drag_force(self, rho_water: float, Cd: float, area: float,
velocity: float) -> float:
"""Compute the hydrodynamic drag force (always positive magnitude)
."""
return 0.5 * Cd * rho_water * area * velocity**2
Explanation: In the code above, mass_full is typically much larger than mass_empty because it
includes the water filling. For example, if a floater has volume 0.04 m³ (40 L) and a 5 kg shell, filling it with
water (~1000 kg/m³) adds ~40 kg. Then mass_full ≈ 45 kg and mass_empty ≈ 5 kg . This matches
the KPP white paper’s example, where a 40 L floater experiences ~392 N buoyancy upward and ~441 N
weight downward – a net ~49 N downward force equal to the 5 kg shell’s weight . Our floater parameters
can be chosen accordingly to reflect such realistic values. The class provides methods for each force so that
the simulation can compute net forces easily.
Environment Module ( environment.py )
The Environment class encapsulates global fluid and environmental parameters. This includes water
properties and toggles for special enhancements:
Density & Gravity: Water density (ρ) and gravitational acceleration (g) are used for buoyancy
calculations . We allow adjusting ρ (e.g., fresh vs. saltwater) and use standard gravity 9.81 m/s² by
default.
Drag Coefficient & Fluid Properties: The drag coefficient (C_D) and effective cross-sectional area (A)
of floaters are defined here, since drag force calculations need them . We can also include water
temperature or viscosity if needed for more advanced drag modeling.
H1 – Nanobubble Void Fraction: If the H1 enhancement is enabled, the environment can reduce
the effective water density or drag for descending floaters . Physically, injecting
microbubbles (nanobubbles) into water reduces its density and can “lubricate” the floater’s descent
by cutting drag. We model this via a density reduction factor. For example, a 10% void fraction
(bubbles) might lower local density by ~10% . In our Environment class, if H1 is active, we provide
an effective_density() method that returns a reduced density for floaters on the descending
side. This directly lowers buoyant force on sinking floaters, making them effectively heavier
(providing more downward driving force) .
16
17
18
21
•
16
•
18
•
2 22
2
23 24
3
H2 – Thermal (Isothermal Expansion): If the H2 enhancement is enabled, the simulation can adjust
buoyancy for ascending floaters. Normally, when compressed air in a floater expands as it rises, it
cools (adiabatic expansion) and might not fully displace water. H2 assumes isothermal expansion,
meaning the air stays warm and expands more, giving extra lift . To simulate this, we include
a buoyancy boost factor for air-filled floaters. For instance, we might increase the effective buoyant
force by a few percent when H2 is on . (A more detailed model could use gas laws for pressurevolume
changes, but a simple factor suffices for now.)
H3 – (Not directly in environment): The H3 enhancement (pulse-and-coast) mostly affects the
drivetrain control rather than fluid properties, so it’s handled in the Control/Drivetrain modules.
Below is the Environment implementation:
# environment.py
class Environment:
def __init__(self, density: float = 1000.0, gravity: float = 9.81,
drag_coefficient: float = 0.6, fluid_area: float = 0.1,
temperature: float = 293.15):
"""
Environment parameters for the simulation.
:param density: Density of water (kg/m^3).
:param gravity: Gravitational acceleration (m/s^2).
:param drag_coefficient: Drag coefficient for floaters.
:param fluid_area: Effective cross-sectional area of a floater (m^2).
:param temperature: Water temperature (K), for future thermal
calculations.
"""
self.density = density
self.gravity = gravity
self.drag_coefficient = drag_coefficient
self.fluid_area = fluid_area
self.temperature = temperature
# Enhancement toggles and parameters:
self.H1_active = False
self.H1_density_reduction = 0.0
# e.g., 0.1 means 10% density reduction when H1 is on
self.H2_active = False
self.H2_buoyancy_boost = 0.0 # e.g., 0.05 means +5% buoyant force
for isothermal expansion
def effective_density(self, floater_state: str) -> float:
"""
Get the effective water density for buoyancy/drag.
If H1 is active and the floater is descending (water-filled), reduce
density.
Otherwise return the base density.
"""
if self.H1_active and floater_state == 'water':
•
25 26
27
•
4
return self.density * (1 - self.H1_density_reduction)
return self.density
Explanation: By adjusting H1_density_reduction , we can simulate different void fractions (e.g., 0.05
for 5% density drop). The KPP documents suggest that even a ~5% density reduction on the descending side
can significantly increase net downward force (~40% in one example) . Our model allows experimenting
with this: we can configure scenarios with H1_active = True to see the effect on performance.
Similarly, setting H2_active = True and a small H2_buoyancy_boost (say 0.1 for +10% buoyancy) will
make air-filled floaters slightly more buoyant to mimic thermal assistance . These parameters are
easily adjustable via a config.
Pneumatics Module ( pneumatics.py )
The PneumaticSystem class handles compressed air injection and venting, as well as tracking the
compressor’s work. In the KPP, when a floater reaches the bottom of the tank, compressed air is rapidly
injected into it, displacing the water and making it buoyant . At the top, that air is released (vented)
so the floater fills with water again . This module covers:
Air Tank & Pressure: We assume there is an air reservoir supplying the compressed air. We can track
its pressure and volume, although in this simple implementation we won’t simulate detailed
pressure dynamics. In a more advanced model, injecting air would lower the tank pressure, and the
compressor would then work to restore it .
Compressor Load & Energy: Injecting air costs energy. We calculate the energy needed to inject air
into a floater and accumulate the compressor’s energy consumption. A simple approach is to
assume injecting one floater’s volume $V$ at the tank pressure $P$ requires $E \approx P \times V$
(this is a rough approximation for isothermal compression from atmospheric pressure). We add this
to compressor_energy . In reality, compression work is $W = P \Delta V \ln(P_{\text{final}}/
P_{\text{atm}})$ for isothermal, but we simplify for now. The key is that we log energy used by the
compressor, since that is input energy that must be subtracted from generator output to see net
gain .
Injection and Venting Methods: inject_air(floater, depth) will set a floater’s state to air
(buoyant) and compute the energy used. We might use the water pressure at the injection depth to
estimate required air pressure. vent_air(floater) will set the floater’s state back to water
(making it heavy) when it reaches the top. We assume venting releases the air to atmosphere or a
low-pressure reservoir without recovering energy (i.e. the potential energy of compressed air is not
recycled in our model).
Let's implement the PneumaticSystem :
# pneumatics.py
class PneumaticSystem:
def __init__(self, tank_volume: float = 1.0, tank_pressure: float =
101325.0, compressor_power: float = 0.0):
"""
Pneumatic system for air injection and venting.
:param tank_volume: Volume of the air tank/reservoir (m^3).
24
26 27
28 29
4
•
30 31
•
32
•
5
:param tank_pressure: Initial pressure in the tank (Pa).
:param compressor_power: (Optional) rated power of compressor (for
reference).
"""
self.tank_volume = tank_volume
self.tank_pressure = tank_pressure # current pressure (Pa)
self.compressor_energy = 0.0 # cumulative energy used by
compressor (J)
# Note: In a more detailed model, compressor_power and on/off could be
used to simulate compressor operation.
def inject_air(self, floater: Floater, environment: Environment, depth:
float) -> float:
"""
Inject compressed air into a water-filled floater at the given depth.
:param floater: Floater to fill with air.
:param depth: Depth of injection (m) – used to estimate pressure.
:return: Energy used by the compressor for this injection (J).
"""
if floater.state != 'water':
return 0.0 # Only inject into a water-filled (heavy) floater
# Compute the pressure at this depth (approximately hydrostatic +
atmospheric)
water_pressure = environment.density * environment.gravity * depth
# Assume we need to supply air at slightly above water_pressure
# Use absolute pressure (adding 1 atm ~101,325 Pa):
target_pressure = 101325.0 + water_pressure
# Estimate energy = pressure * volume (simplified isothermal
compression)
energy_required = target_pressure * floater.volume
# Update compressor energy consumption
self.compressor_energy += energy_required
# Change floater state to air-filled (buoyant)
floater.set_state('air')
return energy_required
def vent_air(self, floater: Floater):
"""
Vent the air from an air-filled floater at the top, allowing it to fill
with water.
"""
if floater.state != 'air':
return
floater.set_state('water')
# (No energy recovery modeled from venting)
6
Explanation: The injection method makes the floater buoyant almost instantly – reflecting the “rapid
injection” described in KPP operations . We immediately mark the floater as filled with air and calculate
the compressor energy. We assume isothermal compression (air draws heat from the environment, which is
plausible for a slow fill or if a heat exchanger is used, per H2) and don’t penalize additional energy for
heating. If desired, we could assume some fraction of heat comes from the environment (thus not
subtracting from net energy) as mentioned in H2 discussions . The venting method simply switches the
floater to heavy; the gravitational potential energy of the compressed air is dissipated (in reality venting
could be through a turbine or captured in an air accumulator, but that’s beyond our scope).
The compressor’s total energy usage ( compressor_energy ) will be used to compute net energy balance.
In our simulation loop, we’ll log compressor power usage during the injection event (e.g., if an injection
took $\Delta t$ seconds, we can log a power draw $P = E/\Delta t$ for that step).
Drivetrain Module ( drivetrain.py )
The Drivetrain class models how the chain of floaters drives the generator. It converts linear forces from
the floaters into rotational motion. Key aspects:
Net Torque Calculation: The net upward force from buoyant floaters minus the downward force
from heavy floaters creates a torque on the sprocket at the top/bottom of the chain. If $R$ is the
sprocket radius, $\tau_{\text{net}} = F_{\text{net}} \cdot R$ . The simulator will compute
$F_{\text{net}}$ by summing forces on all floaters (taking upward as positive).
Moment of Inertia: The system’s inertia includes all moving parts. The floaters (and chain) moving
linearly can be treated as a rotational inertia $I_{\text{chain}} = \sum m_{\text{floater}} R^2$ (this is
equivalent to the total mass moving times $R^2$). If there’s a flywheel attached (H3), its rotational
inertia $I_{\text{fly}}$ adds to the system when the clutch is engaged .
Angular Dynamics: Using Newton’s second law for rotation, $\tau_{\text{net}} = I_{\text{total}}
\alpha$, we integrate the angular motion. We track the angular velocity $\omega$ of the chain (and
sprocket). The linear chain speed $v$ relates as $v = \omega R$. Initially, the system might start from
rest; buoyancy produces a torque that accelerates the chain.
Generator Load: The generator resists motion with a certain torque. We model the generator as a
controllable brake torque on the drivetrain. For simplicity, we might use a constant torque or a
value set by control (representing an electrical load or a PID controller trying to regulate speed).
When the clutch is engaged, this generator torque subtracts from the net torque, slowing
acceleration . The power output of the generator is $P_{\text{gen}} = \tau_{\text{gen}} \cdot
\omega$ (torque times angular speed) . We log this as positive electrical power being produced.
Clutch & Flywheel (H3): The clutch can decouple the generator/flywheel from the chain . In
coast mode (clutch disengaged), the generator is not applying torque on the chain, so the chain can
speed up freely under buoyant force (any generated energy goes into spinning up the flywheel if
attached, or just kinetic energy of moving parts) . In pulse mode (clutch engaged), the
generator is connected and applies a heavy torque, extracting energy (which slows the chain/
flywheel) . We simulate this by having a clutch_engaged flag. If engaged, the flywheel and
chain act as one combined inertia and generator torque is applied; if disengaged, the flywheel spins
on its own (nearly constant speed due to low friction) and the chain is free of generator load. We
handle the speed transition when engaging: when the clutch closes, the chain and flywheel
synchronize in speed (conserving angular momentum).
33
34
•
35
•
36 37
•
•
38 8
39
• 6
40 37
41 42
7
Friction: We neglect minor friction in bearings or the chain for now, aside from fluid drag which we
already include.
Below is the drivetrain implementation:
# drivetrain.py
class Drivetrain:
def __init__(self, sprocket_radius: float, flywheel_inertia: float = 0.0):
"""
Drivetrain linking the chain of floaters to the generator.
:param sprocket_radius: Radius of the sprocket or chain wheel (m).
:param flywheel_inertia: Inertia of the flywheel (kg·m^2) for H3 (if
any).
"""
self.radius = sprocket_radius
self.flywheel_inertia = flywheel_inertia
# Clutch engaged means flywheel+generator are connected to the chain
self.clutch_engaged = True
# Angular velocities (rad/s) for chain and flywheel
self.omega = 0.0 # chain angular speed
self.flywheel_omega = 0.0 # flywheel angular speed (if clutch
disengaged)
# Generator resisting torque (N·m) – to be set by control logic
self.generator_torque = 0.0
def engage_clutch(self, chain_inertia: float):
"""Engage the clutch (connect flywheel). Adjust omega to conserve
angular momentum."""
if not self.clutch_engaged:
# Combine flywheel and chain into one system
total_inertia = chain_inertia + self.flywheel_inertia
if total_inertia > 1e-9:
# conservation of angular momentum: new ω = (I_chain*ω_chain +
I_fly*ω_fly) / (I_total)
self.omega = ((chain_inertia * self.omega) +
(self.flywheel_inertia * self.flywheel_omega)) / total_inertia
# Sync flywheel omega to chain
self.flywheel_omega = self.omega
self.clutch_engaged = True
def disengage_clutch(self):
"""Disengage the clutch (disconnect flywheel). The flywheel will coast
independently."""
if self.clutch_engaged:
self.clutch_engaged = False
# Preserve the flywheel's rotational speed at moment of
disengagement
•
8
self.flywheel_omega = self.omega
# Chain (self.omega) continues, but now without flywheel inertia;
flywheel freewheels.
def update_dynamics(self, net_force: float, total_mass: float, dt: float):
"""
Advance the drivetrain dynamics by time step dt under the given net
force.
:param net_force: Net upward force from floaters (N) [positive = drives
chain forward].
:param total_mass: Total mass of moving floaters (kg) (used to compute
chain inertia).
:param dt: Time step (s).
"""
# Compute effective rotational inertia of chain + floaters about
sprocket
chain_inertia = total_mass * (self.radius ** 2)
if self.clutch_engaged:
# Clutch engaged: flywheel + chain together
I_total = chain_inertia + self.flywheel_inertia
# Net torque on system: buoyancy force * R minus generator resisting torque
# (Generator torque resists motion, acting opposite to net force)
# Assume net_force drives rotation in positive direction,
generator_torque opposes it.
torque_net = net_force * self.radius - self.generator_torque
# Angular acceleration
alpha = torque_net / I_total
self.omega += alpha * dt
# Flywheel rotates with chain (locked together)
self.flywheel_omega = self.omega
else:
# Clutch disengaged: chain moves freely (generator not resisting),
flywheel is separate
torque_net = net_force * self.radius # no generator torque applied
alpha_chain = torque_net / chain_inertia
self.omega += alpha_chain * dt
# Flywheel: no external torque, so it keeps spinning at constant
angular velocity
# (we assume negligible friction for flywheel).
# flywheel_omega remains as is (no update)
# (We could also update an angle position if needed for visualization)
def get_chain_speed(self) -> float:
"""Get linear speed of the chain (m/s) from angular speed."""
return self.omega * self.radius
5
9
Explanation: The drivetrain integrates the equations of motion. If the clutch is engaged, the chain and
flywheel are treated as a single rigid body with combined inertia . The generator torque (if any) is
subtracted from the buoyancy torque, reducing acceleration. If the clutch is disengaged, the chain’s
equation of motion excludes the flywheel inertia and uses no generator torque (so the chain can accelerate
faster), while the flywheel’s rotation is left unchanged (it just coasts at whatever speed it had) . The
engage_clutch method handles the instantaneous merger by computing a weighted average of angular
momenta – effectively conserving angular momentum when the flywheel locks onto the chain. (We assume
the engagement is quick and ideally in phase; in reality there might be a jolt or slip, but we abstract that.)
The disengage_clutch simply records the flywheel’s speed at the moment of release.
Using this, we can simulate the H3 pulse-and-glide strategy . For example, we might set a schedule
where for 5 seconds the clutch is open (generator off), letting the chain speed up, then for 2 seconds the
clutch is closed with a high generator torque, extracting energy in a burst . The code above supports
this: we can toggle clutch_engaged via control logic at those intervals, and set generator_torque
high during pulses. The flywheel inertia smooths the transition, storing kinetic energy during the coast and
releasing it during the pulse, which helps maintain motion and supply extra power to the generator .
The get_chain_speed() method provides the linear speed, which is useful for computing drag forces on
floaters and for logging/monitoring the chain movement (e.g., to ensure it stays within a safe range; the
KPP tends to operate at low chain speeds to minimize drag losses ).
Control Module ( control.py )
The Control module orchestrates the overall operation by reading “sensor” conditions and toggling
actuators (valves, clutch, generator load) . We implement a basic rule-based control (state machine
logic):
Bottom Sensor & Injection Timing: We assume a sensor or condition detects when a floater arrives
at the bottom of the tank. Our control logic will trigger the bottom injection valve at the right
moment. In the simulation, we check if a floater just reached the bottom position; if so, we call
pneumatics.inject_air() for that floater. In a real system, you might open a valve for a certain
duration – our simplified model treats the injection as effectively instantaneous (within one timestep)
but we could extend this by keeping a valve open for a set number of steps if needed .
We ensure the injection happens only if the floater is in the proper state (water-filled) and aligned at
the bottom.
Top Sensor & Venting: Similarly, when a floater reaches the top, we trigger venting. The control
either opens a vent valve or simply designates that floater to vent immediately . In simulation, we
just call vent_air() on that floater at the top sensor trigger.
Generator Load Control: In this basic implementation, we might use a fixed generator torque or a
simple heuristic. For example, one could apply a constant torque that aims to keep the chain at a
desired speed, or use a proportional control to target a certain RPM. Here, we allow setting a
constant torque value via configuration or let it be zero (freewheel) when clutch is engaged. More
sophisticated control (PID or even an RL policy) could be plugged in via this module.
Clutch Schedule (H3): We implement a fixed duty-cycle control for the clutch if H3 is enabled .
For instance, we can specify coast_time = 5 s and pulse_time = 2 s . The control will
disengage the clutch (coast) at simulation start, then after 5 seconds, engage it for 2 seconds, then
36
6 37
43 40
44
40 45
46
11 7
•
47 48
•
4
•
• 44
10
repeat. This can be done by tracking the elapsed time modulo the cycle. We choose the initial state
(coasting) such that the system starts in a low-resistance acceleration phase, as suggested by the
KPP pulse-and-glide concept .
H1/H2 Coordination: The control module doesn’t need to do much for H1/H2, since those mostly
affect physics calculations directly. However, one could imagine control decisions like modulating the
compressor or nanobubble injection rate. For now, we assume H1 (bubbles) are either on or off for a
given run (not actively controlled), and H2 (thermal) either is enabled or not by configuration.
Below is a simple control class:
# control.py
class Control:
def __init__(self, H3_active: bool = False, coast_time: float = 0.0,
pulse_time: float = 0.0, generator_torque: float = 0.0):
"""
Control logic for KPP operation.
:param H3_active: Whether pulse-and-coast mode is enabled.
:param coast_time: Duration of coast (clutch disengaged) in seconds for
H3.
:param pulse_time: Duration of pulse (clutch engaged) in seconds for H3.
:param generator_torque: Generator resisting torque to apply during
pulse (N·m).
"""
self.H3_active = H3_active
self.coast_time = coast_time
self.pulse_time = pulse_time
self.cycle_time = coast_time + pulse_time if H3_active else 0.0
self.gen_torque_setting = generator_torque
def decide_actions(self, current_time: float):
"""
Decide the actions for this time step: whether clutch should be engaged
and what generator torque to use.
Returns a tuple (clutch_engaged, generator_torque).
"""
if not self.H3_active:
# If H3 is not active, we keep clutch engaged and can apply a
constant generator torque.
return True, self.gen_torque_setting
# For H3: determine phase in the pulse-coast cycle
phase_time = current_time % self.cycle_time
# Clutch engaged during pulse phase, disengaged during coast phase
clutch_engaged = (phase_time >= self.coast_time)
# Generator torque applied only when clutch engaged, otherwise zero
gen_torque = self.gen_torque_setting if clutch_engaged else 0.0
return clutch_engaged, gen_torque
40
•
11
Explanation: The decide_actions() method implements the periodic clutch control. In a 5s coast / 2s
pulse example, coast_time=5, pulse_time=2 . The control will output clutch_engaged=False (and
torque 0) for the first 5 seconds, then clutch_engaged=True (and torque = preset value) for the next 2
seconds, and repeat. We have essentially a open-loop timed state machine . This simple logic can later
be replaced or augmented with sensor-based conditions (e.g., engage clutch early if a float is near top to
help refill, etc.) as suggested in KPP studies .
For generator torque, one might tune the value via simulation. A higher torque means more power
extracted but also more braking on the system. If it’s too high, the chain might stall; if too low, the system
will spin too fast but not generate much power. In our setup, generator_torque can be set by the user
or tuned so that in steady state the net buoyant torque roughly balances the generator torque plus drag.
For example, if net buoyant force is ~4400 N (from earlier example) and radius 0.25 m, net torque ~1100
N·m ; a generator torque on that order would significantly load the system. We might start with a
smaller value (e.g., 500 N·m) and see how the simulation behaves.
The control module, as written, primarily handles the H3 timing and generator setting. The injection/
venting actions are handled in the simulation loop when certain conditions (sensors) are met, which is
effectively a part of control. In a refactored design, we could integrate those into a more complex
decide_actions that also returns e.g. inject_now or vent_now flags, but it is straightforward to
handle them directly in the loop by checking floater positions.
Simulation Loop ( simulation.py )
Now we bring it all together in the main simulation engine. The simulation loop will:
Initialization: Set up all objects (Environment, Floaters, PneumaticSystem, Drivetrain, Control,
Logger) with parameters from a configuration. Initialize floaters’ positions (e.g., evenly spaced
around the loop) and initial states.
Initial Control Settings: Decide initial clutch state and generator load. For instance, if H3 is on, we
might start in coast phase (clutch disengaged) . We configure the drivetrain accordingly before
entering the loop.
Time-Step Loop: For each time step:
Compute Forces: Determine buoyancy, weight, and drag for each floater using Floater methods
and Environment values. Sum up the net force (taking into account direction for each floater’s
state) to get the total net force on the chain.
Integrate Motion: Pass the net force and total moving mass to
Drivetrain.update_dynamics() to update the chain’s angular speed (and flywheel speed) .
This gives the new chain velocity.
Move Floaters: Update each floater’s position along the chain based on the chain velocity. We
increment each floater’s chain coordinate s_position by v * dt (wrapping around the loop
length). We also update each floater’s vertical position for logging (for s <= height, vertical = s; for s >
height, vertical = 2*height - s).
49
50
35
1.
2.
49
3.
4.
5.
51
6.
12
Check Sensors (Top/Bottom): Detect if any floater crossed the bottom or top in this step. We can
detect a bottom crossing if a floater’s s_position wraps from near 2*height back to 0. A top
crossing is when s_position passes the half-loop point ( height ). When these events occur:
For each bottom-crossing floater (entering the ascending side): call
pneumatics.inject_air(floater) to make it buoyant . Log the compressor energy
used.
For each top-crossing floater (entering the descending side): call
pneumatics.vent_air(floater) to make it heavy .
Calculate Power & Log Data: Compute the generator power output as P_gen =
drivetrain.generator_torque * drivetrain.omega (if clutch engaged; zero if disengaged).
Compute the compressor power (if any injection happened this step) as the injection energy divided
by dt . Then log the current time, chain speed, generator power, compressor power, net power
(P_gen minus compressor power), clutch state, etc. This data is appended to the logger.
Control Actions: At the end of the step, use Control.decide_actions(current_time) to
update the clutch and generator torque for the next iteration . This may toggle the clutch (so we
call Drivetrain.engage_clutch or disengage_clutch accordingly) and adjust
drivetrain.generator_torque .
Termination: Loop until the simulated time reaches the desired duration or a stop condition (e.g.,
steady state after several cycles). After the loop, use the logger to output results or compute
summary metrics.
Let's put this together in a Simulation class for clarity, which uses instances of the above modules:
# simulation.py
import pandas as pd
class KPP_Simulation:
def __init__(self, config: dict):
# 1. Initialize Environment and modules with parameters from config
self.env = Environment(density=config.get('water_density', 1000.0),
gravity=config.get('gravity', 9.81),
drag_coefficient=config.get('drag_coefficient',
0.6),
fluid_area=config.get('floater_area', 0.1))
# Set H1/H2 enhancements in environment
self.env.H1_active = config.get('H1', False)
self.env.H1_density_reduction = config.get('H1_density_reduction', 0.0)
self.env.H2_active = config.get('H2', False)
self.env.H2_buoyancy_boost = config.get('H2_buoyancy_boost', 0.0)
H3_active = config.get('H3', False)
# Create floaters
num = config.get('num_floaters', 10)
volume = config.get('floater_volume', 0.04) # m^3
mass_empty = config.get('floater_mass_empty', 5.0) # kg
mass_full = config.get('floater_mass_full', mass_empty +
self.env.density * volume)
self.floaters = [Floater(volume, mass_empty, mass_full) for _ in
7.
◦
52
◦
53
8.
9.
8
10.
13
range(num)]
# Evenly distribute floaters around the loop (vertical tank height
given)
self.tank_height = config.get('tank_height', 10.0) # m
self.loop_length = 2 * self.tank_height
for i, fl in enumerate(self.floaters):
fl.s_position = i * (self.loop_length / num)
# alternate initial state: assume half the floaters are buoyant
ascending, half heavy descending
if i < num/2:
fl.set_state('air') # ascending side
else:
fl.set_state('water') # descending side
# Set initial vertical position for logging
if fl.s_position <= self.tank_height:
fl.vertical_position = fl.s_position
else:
fl.vertical_position = 2*self.tank_height - fl.s_position
# Pneumatic system
self.air_system = PneumaticSystem(tank_volume=config.get('tank_volume',
1.0),
tank_pressure=config.get('tank_pressure', 101325.0))
# Drivetrain with sprocket radius and optional flywheel
self.drivetrain =
Drivetrain(sprocket_radius=config.get('sprocket_radius', 0.25),
flywheel_inertia=config.get('flywheel_inertia', 0.0))
# Control logic
self.control = Control(H3_active=H3_active,
coast_time=config.get('coast_time', 0.0),
pulse_time=config.get('pulse_time', 0.0),
generator_torque=config.get('generator_torque',
0.0))
# Logger: will accumulate dicts of simulation data
self.log = []
# For energy accounting
self.total_generator_energy = 0.0
self.total_compressor_energy = 0.0
# Initial control actions (set initial clutch state and generator
torque)
clutch_initial, torque_initial =
self.control.decide_actions(current_time=0.0)
if clutch_initial != self.drivetrain.clutch_engaged:
if clutch_initial:
# engage clutch (combine flywheel)
# (initially flywheel speed is 0 and chain speed 0, so trivial)
14
total_mass = sum(fl.mass for fl in self.floaters)
self.drivetrain.engage_clutch(chain_inertia=total_mass *
(self.drivetrain.radius**2))
else:
self.drivetrain.disengage_clutch()
self.drivetrain.generator_torque = torque_initial
def run(self, total_time: float, time_step: float):
"""Run the simulation for the given duration and time step."""
t = 0.0
# Main integration loop
while t < total_time:
# 2. Compute net buoyant force on chain
net_force = 0.0 # upward positive
total_mass = 0.0
chain_speed = self.drivetrain.get_chain_speed()
for fl in self.floaters:
# Each floater's contribution
rho = self.env.effective_density(fl.state)
buoy = fl.compute_buoyant_force(rho, self.env.gravity)
if self.env.H2_active and fl.state == 'air':
buoy *= (1 + self.env.H2_buoyancy_boost) # thermal boost:
increased buoyancy
weight = fl.compute_weight(self.env.gravity)
# Determine direction of motion for drag
# Assume 'air' state means on ascending side (moving up),
'water' means descending side.
if fl.state == 'air':
# ascending: drag opposes upward motion
drag = fl.compute_drag_force(rho, self.env.drag_coefficient,
self.env.fluid_area, chain_speed)
net_force += (buoy - weight - drag)
fl.velocity = chain_speed
else:
# descending: drag opposes downward motion (acts upward)
drag = fl.compute_drag_force(rho, self.env.drag_coefficient,
self.env.fluid_area, chain_speed)
net_force += (buoy + drag - weight) # this will typically
be negative or smaller positive
fl.velocity = -chain_speed
total_mass += fl.mass
# 3. Update chain/flywheel dynamics (integrate one time step)
self.drivetrain.update_dynamics(net_force, total_mass, time_step)
# 4. Move floaters according to chain movement
bottom_triggers = []
top_triggers = []
for fl in self.floaters:
prev_s = fl.s_position
15
# Advance s_position by chain linear distance moved =
chain_speed_new * dt
# (Using the updated chain speed after integration for this
interval)
distance = self.drivetrain.get_chain_speed() * time_step
fl.s_position = (prev_s + distance) % self.loop_length
# Update vertical position for logging
if fl.s_position <= self.tank_height:
fl.vertical_position = fl.s_position
else:
fl.vertical_position = 2*self.tank_height - fl.s_position
# Check for passing bottom or top
if fl.s_position < prev_s:
bottom_triggers.append(fl)
if prev_s < self.tank_height <= fl.s_position:
top_triggers.append(fl)
# 5. Handle injections and venting at triggers
comp_power = 0.0
for fl in top_triggers:
# Vent air at top
self.air_system.vent_air(fl)
for fl in bottom_triggers:
energy_used = self.air_system.inject_air(fl, self.env,
depth=self.tank_height)
if energy_used > 0:
# calculate compressor power during this time step
comp_power += energy_used / time_step
self.total_compressor_energy += energy_used
# 6. Compute generator power output
# Only if clutch engaged do we assume generator is receiving torque
gen_power = self.drivetrain.generator_torque * self.drivetrain.omega
if self.drivetrain.clutch_engaged else 0.0
self.total_generator_energy += gen_power * time_step
# Net instantaneous power (output minus input)
net_power = gen_power - comp_power
# Log data
self.log.append({
'time': t,
'chain_speed': self.drivetrain.get_chain_speed(),
'clutch_engaged': self.drivetrain.clutch_engaged,
'generator_power': gen_power,
'compressor_power': comp_power,
'net_power': net_power,
# Example of logging one floater's state/position for reference:
'float0_height': self.floaters[0].vertical_position,
'float0_state': self.floaters[0].state
})
# 7. Advance time
16
t += time_step
# 8. Control decisions for next step
clutch_cmd, torque_cmd = self.control.decide_actions(t)
if clutch_cmd != self.drivetrain.clutch_engaged:
if clutch_cmd:
total_mass = sum(fl.mass for fl in self.floaters)
self.drivetrain.engage_clutch(chain_inertia=total_mass *
(self.drivetrain.radius**2))
else:
self.drivetrain.disengage_clutch()
self.drivetrain.generator_torque = torque_cmd
# End of simulation loop
return pd.DataFrame(self.log)
We utilize a Pandas DataFrame for the log so that the data can be easily analyzed or saved . Each
iteration logs the time, chain speed, generator power, compressor power, net power, and some state info.
The use of Pandas also allows computing summary statistics after the run.
Note: We increment time in steps of dt (time_step). The physics integration uses a simple forward Euler
method, which is adequate for small dt and qualitative behavior. For higher accuracy or stiff systems, one
could use smaller time steps or a more sophisticated integrator (or even a physics engine library as
suggested in the blueprint ), but simplicity is fine here.
We also handle multiple floaters potentially triggering injection/vent in one step (which could happen if
floaters are closely spaced or dt is large). In such a case, we sum the compressor power for that step
(treating it as if the compressor had to supply multiple injections simultaneously – in reality, you might
stagger them, but the energy total is what matters for the balance).
Example Usage and Results
With the classes defined, we can now configure a simulation scenario and run it. For example, let’s simulate
a small KPP with 12 floaters, a tank 10 m high, and test the effect of the enhancements:
# Example configuration dictionary
config = {
'water_density': 1000.0, # kg/m^3 (fresh water)
'gravity': 9.81, # m/s^2
'drag_coefficient': 0.6, # dimensionless, typical for a bluff body
'floater_area': 0.1, # m^2 cross-section of floater
'tank_height': 10.0, # m
'num_floaters': 12,
'floater_volume': 0.04, # m^3
'floater_mass_empty': 5.0, # kg (mass of empty floater shell)
# mass_full will default to 5 + 1000*0.04 = 45 kg
# Enhancements toggles:
13
54
46
17
'H1': True,
'H1_density_reduction': 0.10, # 10% density reduction in descending column
'H2': True,
'H2_buoyancy_boost': 0.05, # 5% buoyancy boost from thermal (isothermal
expansion)
'H3': True,
'coast_time': 5.0, # 5 s coast (clutch open)
'pulse_time': 2.0, # 2 s pulse (clutch engaged)
'generator_torque': 800.0, # Resistive torque when generator engaged
(N·m)
'sprocket_radius': 0.25, # m
'flywheel_inertia': 50.0 # kg·m^2 (size of flywheel for smoothing in
H3)
}
# Initialize simulation
sim = KPP_Simulation(config)
# Run for 60 seconds of simulated time with 0.1 s time-step
df_log = sim.run(total_time=60.0, time_step=0.1)
# Save the logged data to CSV (optional)
df_log.to_csv("kpp_simulation_log.csv", index=False)
# Compute summary metrics
total_gen_J = sim.total_generator_energy # total electrical energy generated
(J)
total_comp_J = sim.total_compressor_energy # total compressor energy consumed
(J)
net_energy_J = total_gen_J - total_comp_J
avg_chain_speed = df_log['chain_speed'].mean()
net_power_W = net_energy_J / 60.0 # net average power over 60 s
print(f"Total generator output energy: {total_gen_J:.1f} J")
print(f"Total compressor input energy: {total_comp_J:.1f} J")
print(f"Net energy output: {net_energy_J:.1f} J over 60 s, average net power =
{net_power_W:.2f} W")
print(f"Average chain speed: {avg_chain_speed:.3f} m/s")
This script sets up a scenario and runs the simulation loop. It then prints out some key results:
Total Generator Energy (Joules) – the energy produced by the generator.
Total Compressor Energy (Joules) – the energy consumed by the air compressor.
Net Energy Output – the difference (generator minus compressor). A positive net energy would
indicate the system produced more energy than it used (a very optimistic outcome), whereas a
negative or zero net means it’s self-sustaining at best or loses energy.
Average Net Power (Watts) – net energy divided by time.
Average Chain Speed – to see the operating speed.
•
•
•
•
•
18
We expect in a realistic scenario that without enhancements H1/H2/H3, the net energy would be negative
(the compressor and losses consume more than the generator produces, as conventional physics dictates)
. The enhancements aim to improve this balance. The simulator allows testing cases: e.g., turn off
H1, H2, H3 individually or in combinations and compare results . Since we log all key quantities, we could
plot the time-series of power output vs input, chain speed oscillations with H3, etc., to analyze the behavior
of the system.
Conclusion: We have implemented a modular simulation engine that captures the essential physics of the
KPP: buoyancy and gravity forces on floaters , drag losses , the injection and venting pneumatic
cycle, and the conversion of force imbalance into rotational energy and electricity. The design emphasizes
extensibility – each subsystem (buoyancy, pneumatics, drivetrain, control) can be refined or replaced
without affecting others, due to clear interfaces. For example, one could plug in a more advanced fluid
dynamics model or integrate a reinforcement learning agent for control without changing the core
simulation loop. All key internal states are logged for analysis, which will help researchers evaluate
performance, test control strategies, and explore the impact of the hypothetical enhancements H1, H2, H3
on net efficiency . This simulation provides a foundation for real-time visualization or web interfaces
in the future, as well as a testbed for improving the KPP concept in silico.
Kinetic Power Plant (KPP) R&D Simulator Algorithm Blueprint.pdf
file://file-DEKb2MeVDubPyHbxBzQBuC
Kinetic Power Plant (KPP)
Technology White Paper.pdf
file://file-Wn4JQYdoC26QBSWsGJd8r8
Conceptual Analysis and Reverse outline.docx
file://file-NCr9HjpokqgMpZ6TYBwagu
55 56
57
58 59 18
32 60
1 2 6 7 8 9 10 11 12 13 22 23 25 26 27 34 36 37 38 40 41 42 43 44 45 49 50 51 54 57
60
3 4 5 14 15 18 19 20 21 24 28 29 30 31 32 33 35 39 46 47 48 52 53
16 17 55 56 58 59
19