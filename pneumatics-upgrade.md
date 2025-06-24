Pneumatic System of a Kinetic Power Plant: From Air Compression to Buoyant Power
Imagine a tall water-filled tower with a continuous loop of hollow floaters (like upside-down buckets) attached to a chain. This is the core of a Kinetic Power Plant (KPP). The floaters are heavy when filled with water and light when filled with air. The system uses compressed air to make floaters buoyant at the bottom of the tank, causing them to rise and turn the chain, which drives a generator. At the top, the air is released so the floaters refill with water and become heavy, sinking back down to repeat the cycle. In this narrative, we’ll walk through each stage of the KPP’s pneumatic system – from the air compressor charging an air tank, to injecting air into a submerged floater, the floater’s buoyant ascent, venting at the top, and back to control and thermodynamics. We will explain each module in sequence with intuitive language, realistic values, and relevant equations, so even a curious reader with no prior knowledge can follow along. Let’s begin at the source: the air compressor and storage system.
Compressor and Air Storage
The journey starts with the air compressor, which provides the pressurized air that will later be used to lift the floaters. In a KPP, the compressor is typically an electrical machine (often a piston or rotary compressor) that draws in ambient air at atmospheric pressure and forces it into a storage tank at a higher pressure. This requires a significant energy input – compressors consume mechanical/electrical power to do the work of compression. For example, one demonstration KPP used a 4.2 kW three-phase air compressor to charge its air reservoir
scribd.com
. That means the compressor was drawing about 4.2 kilojoules of energy per second to pressurize air. The compressor’s flow rate (how much air it can pump per minute) and pressure rating determine how quickly the system can refill the air tank and how deep a floater can be injected with air. A typical industrial compressor of a few kilowatts might deliver on the order of 10–100 liters of air per second at moderate pressure, but this greatly depends on design. In our example, a 4.2 kW compressor might supply on the order of several cubic feet per minute of air at the required pressure (tens of liters per second), but the exact flow will vary with operating pressure. Pressure and flow requirements: The compressor must generate pressure higher than the hydrostatic pressure at the bottom of the water tank, because it has to inject air against the weight of the water. Water is heavy – pressure increases about 1 atmosphere for every 10 meters of depth
pmel.noaa.gov
. (1 atmosphere is ≈101 kPa or 14.7 psi.) For instance, if the floaters are injected at 10 m depth, the water pressure there is roughly 1 bar (≈100 kPa) above atmospheric pressure. So the compressor might need to supply air at around 2 atm absolute pressure (about 200 kPa, combining the 1 atm ambient + 1 atm from water) plus a margin to overcome losses. Deeper systems require higher pressures: e.g. at 25 m depth, pressure is ≈3.5 atm absolute. The flow rate must be high enough to fill each floater in the brief time it sits at the bottom (we’ll discuss timing shortly). This can be demanding – delivering a large volume of air at high pressure quickly is a power-intensive task. Air storage tank and pressure control: The compressed air is usually stored in a pressure tank or reservoir to smooth out the supply. The compressor cycles on and off (or varies its output) to keep the tank at a target pressure. A pressure sensor and regulator/relief valve ensure the tank doesn’t exceed safe limits. As air is pumped in, the tank’s pressure rises. The relationship between pressure (P), volume (V), and the amount of air (number of moles n) in the tank follows the ideal gas law: 
∗
∗
𝑃
𝑉
=
𝑛
𝑅
𝑇
,
∗
∗
∗∗PV=nRT,∗∗ where R is the gas constant and T is absolute temperature
britannica.com
. If the tank volume is fixed, adding more air (n increases) will raise P (assuming T stays around ambient). In many analyses, we assume isothermal compression, meaning the air stays near the same temperature as the surroundings (heat from compression is removed). Under that assumption, P is roughly proportional to n (since T constant, V fixed). In reality, compressing air heats it up (think of how a bicycle pump gets warm). If not cooled, the pressure will be higher initially due to the hot air, then drop as the air cools in the tank. KPP systems often include intercoolers or use the water tank to help cool the compressed air, approximating isothermal conditions to improve efficiency. To illustrate the compression process, consider taking air at atmospheric pressure 
𝑃
𝑎
𝑡
𝑚
P 
atm
​
  and compressing it to the injection pressure 
𝑃
𝑑
𝑒
𝑝
𝑡
ℎ
P 
depth
​
  needed for the floater depth. The minimum theoretical work (energy) needed, assuming ideal isothermal compression, is given by: 
𝑊
in
=
𝑛
𝑅
𝑇
ln
⁡
 ⁣
(
𝑃
𝑑
𝑒
𝑝
𝑡
ℎ
𝑃
𝑎
𝑡
𝑚
)
,
W 
in
​
 =nRTln( 
P 
atm
​
 
P 
depth
​
 
​
 ), which can also be written using initial pressure-volume as 
𝑊
in
=
𝑃
𝑎
𝑡
𝑚
𝑉
𝑎
𝑡
𝑚
ln
⁡
(
𝑃
𝑑
𝑒
𝑝
𝑡
ℎ
/
𝑃
𝑎
𝑡
𝑚
)
W 
in
​
 =P 
atm
​
 V 
atm
​
 ln(P 
depth
​
 /P 
atm
​
 )
file-1jpzjzmpct1fnz7y2pskxd
. Here 
𝑉
𝑎
𝑡
𝑚
V 
atm
​
  is the volume of air at atmospheric conditions that we compress. This formula comes from integrating the pressure-volume work for an ideal gas during compression. It shows that the energy cost grows with the pressure ratio – compressing to a higher multiple of atmospheric pressure costs disproportionately more energy (logarithmically). For example, suppose each floater will contain 0.1 m³ of air at depth (when injected). If the depth pressure is 2 atm (approx 10 m depth), then by Boyle’s Law that air would occupy 0.2 m³ at the surface (since 
𝑃
𝑎
𝑡
𝑚
𝑉
𝑎
𝑡
𝑚
=
𝑃
𝑑
𝑒
𝑝
𝑡
ℎ
𝑉
𝑖
𝑛
𝑗
P 
atm
​
 V 
atm
​
 =P 
depth
​
 V 
inj
​
 ). Plugging into the formula:
𝑃
𝑎
𝑡
𝑚
≈
101
×
10
3
 
Pa
,
𝑉
𝑎
𝑡
𝑚
=
0.2
 
m
3
,
𝑃
𝑑
𝑒
𝑝
𝑡
ℎ
=
2
𝑃
𝑎
𝑡
𝑚
P 
atm
​
 ≈101×10 
3
 Pa,V 
atm
​
 =0.2m 
3
 ,P 
depth
​
 =2P 
atm
​
 .
𝑊
in
=
101,000
×
0.2
×
ln
⁡
(
2
)
≈
14,000
 
J
.
W 
in
​
 =101,000×0.2×ln(2)≈14,000J. So about 14 kJ of work is the theoretical minimum to compress 0.2 m³ of air to 2 atm (if perfectly cooled). That’s roughly the energy to lift a 1000 kg car by 1.4 m, just to put in perspective – not trivial. Real compressors are less than 100% efficient, so maybe 18–20 kJ or more would actually be expended for that amount of air. The air storage tank allows the compressor to do this work in advance and store the energy as pressure. The tank is typically maintained at a set pressure (say a bit above the required injection pressure). A pressure switch might turn the compressor on when tank pressure drops too low and off when it’s high enough. This way, when a floater is ready to be filled, there is a reserve of compressed air ready to deploy quickly. If the tank is large relative to the volume used per injection, the pressure will only drop slightly each time, keeping the injection pressure relatively constant for each floater. If the tank is too small, the pressure could dip during an injection, leading to slower or incomplete fills – so sizing and pressure regulation are important. Power losses and energy cost: Compressing air inherently has losses. Any heat that is removed (by cooling the air for isothermal assumption) is energy that doesn’t go into the air’s stored pressure energy – effectively a loss. If the compression is adiabatic (no heat removal during compression), then the air gets hotter and you end up doing more work. For diatomic gases like air, the adiabatic work is 
𝑊
=
𝑃
2
𝑉
2
−
𝑃
1
𝑉
1
𝛾
−
1
W= 
γ−1
P 
2
​
 V 
2
​
 −P 
1
​
 V 
1
​
 
​
  with 
𝛾
≈
1.4
γ≈1.4. This yields higher energy than the isothermal case. In practice, real compressors fall somewhere in between – they remove some heat via fins or water jackets, but not perfectly. Additionally, mechanical friction, electrical motor losses, etc., mean you pay more energy in than the ideal formulas suggest. It’s also worth noting that compressing air is expensive in energy terms compared to the mechanical work we might get out later. As we’ll see, the buoyant energy we can extract from a volume of air is usually less than the energy we spent compressing that air in the first place. This is a fundamental reason why a buoyancy power plant cannot be a perpetual motion machine – it’s essentially using a lot of energy to create a buoyant force that does a bit less energy of work. In fact, for any significant depth, the energy required to compress air to that pressure will always exceed the energy obtained from the buoyant lift, even before accounting for losses
file-1jpzjzmpct1fnz7y2pskxd
. We’ll quantify this in a moment when examining the injection and buoyancy.
Air Injection Control at the Bottom
Now let’s follow the compressed air as it gets used. The KPP uses a control system (often a PLC – Programmable Logic Controller) to manage when and how air is injected into each floater at the bottom of the tank. The floaters are attached to a chain or conveyor that rotates continuously. As each floater reaches the bottom (“the lower vertex” of the loop), it is in position to be filled with air. The timing has to be just right: inject too early or too late and you waste air or fail to fill the floater properly. Injection sequence: In a typical cycle, once the system is up to pressure, the PLC opens a valve connecting the high-pressure air reservoir to a nozzle or pipe leading into the lowest floater
scribd.com
. For example, in one description: after the compressor has run for a few minutes to build up operating pressure, the controller opens an electro-pneumatic valve, and “the compressed air enters the pipe and goes to the bottom of the well where it pumps the water out of the lowest system chamber (float). Under the influence of Archimedes’ law this float gains thrust upward...”
scribd.com
. In other words, the air rushes into the submerged floater and forces the water out. The water that was inside the floater is expelled back into the surrounding tank (essentially “pumping” it upwards out of the floater). The floater, now filled with air instead of water, becomes much lighter (indeed positively buoyant) and immediately starts to rise. The control system typically ensures that only one floater is filled at a time, and it coordinates with the motion of the chain. As the first floater starts ascending, the next empty floater on the chain comes into the bottom position. At that moment, a mechanism (often a mechanical valve coupler or a rotating distributor) connects the air supply to this next floater. The compressed air then fills that one, and so on in sequence
scribd.com
. Essentially, with each segment of chain that comes around, a floater gets injected with air, creating a continuous procession of rising floaters. A description from a brochure puts it succinctly: “The compressor pumps air in the lowest container. The lifting force moves the container upwards and brings the next container in the right position to be filled with air.”
reddit.com
. This timing logic is crucial: you want a smooth operation where by the time one floater has been filled and departs upward, the next one arrives and is promptly filled, so the chain experiences a steady upward thrust on one side. Valve actuation and volume per floater: How does the air actually get into the floater? There are a couple of design approaches:
Mechanical coupling: In some designs, each floater has an automatic inlet valve that aligns with a fixed air feed pipe at the bottom. When the floater reaches the bottom position, the two valves connect (like a plug and socket)
reddit.com
. The PLC then opens the master valve so air flows from the tank into the floater through this connection. The valve might stay open for a set duration or until a certain pressure/volume is delivered. Once the floater is filled (water mostly pushed out), the valve closes (either automatically or as the floater moves away).
Open-bottom floater: In other implementations, the floater can be like an open-bottomed chamber (imagine an upside-down cup). At the bottom, a nozzle simply blows air up into the cup, displacing the water. Since the cup is open at the bottom, one might wonder why the air doesn’t just escape immediately – but as long as the floater is kept upright, the air will stay “trapped” at the top of the floater by the water pressure (like an inverted glass holding air underwater). In such a case, a separate valve isn’t needed to hold the air in – it’s naturally trapped until the floater tilts or surfaces (we’ll discuss that in venting). Some systems might still use a one-way flap to prevent premature escape. The volume of air per floater is basically the internal volume of the floater minus any residual water left. Typically, you want to inject enough air to eject most of the water, maximizing buoyancy. However, the system might not fill it 100% with air if not needed – controlling the amount of air can fine-tune the buoyant force. In fact, the KPP’s proprietary control is largely about “regulating the amount of air injected into each float”
fcnp.com
 to optimize performance. Too little air and the floater won’t generate enough lift; too much and you waste compressed air for marginal extra lift.
Let’s apply some physics equations to the injection at depth. To push water out at depth H, the injected air must have pressure slightly above the ambient water pressure at that depth. The water exerts a hydrostatic pressure 
𝑃
water
=
𝑃
surface
+
𝜌
𝑔
𝐻
P 
water
​
 =P 
surface
​
 +ρgH, where 
𝜌
ρ is water density (~1000 kg/m³) and 
𝑔
g is gravity (~9.81 m/s²). For example at 10 m, 
𝜌
𝑔
𝐻
≈
98,100
 Pa
≈
0.97
 atm
ρgH≈98,100 Pa≈0.97 atm. So the air needs to be a bit above that to flow in. In practice, the required injection pressure might be: 
𝑃
inject
≈
𝑃
water
(
𝐻
)
+
Δ
𝑃
valves
,
P 
inject
​
 ≈P 
water
​
 (H)+ΔP 
valves
​
 , where 
Δ
𝑃
valves
ΔP 
valves
​
  is a small overhead to overcome valve and flow resistance. If our 10 m depth example has 
𝑃
water
≈
1.97
P 
water
​
 ≈1.97 atm absolute, the compressor might supply, say, 2.1 atm to ensure good flow. The mass flow rate during injection can be very high – air rushes in to displace water rapidly. If a floater volume is 100 L and we fill it in 2 seconds, that’s 50 L/s flow at high pressure. Such flow requires a powerful compressor or a sizable reservoir dump. In reality, the injection might take a bit longer (several seconds), or the system might even momentarily slow the chain to allow filling. It’s a design choice: continuous motion vs. a “stop-fill-go” cycle. Many KPP demos seem to operate nearly continuously, implying quick injections. Hydrostatic pressure and work: As mentioned earlier, injecting air at depth is essentially doing the work to lift that water out of the floater back to the surface. In fact, one can view the process this way: filling the bucket with air = lifting the water that was in the bucket up to the surface level
physics.stackexchange.com
. The work done by the air in pushing out the water is equal to the weight of that water times the height it’s lifted (approximately the depth H). If we inject a volume 
𝑉
inj
V 
inj
​
  (at depth conditions) of air, we displace that same volume of water. The weight of that water is 
𝜌
𝑔
𝑉
inj
ρgV 
inj
​
 . Lifting it by height H (from bottom to surface) requires 
𝑊
out
=
𝜌
𝑔
𝑉
inj
𝐻
W 
out
​
 =ρgV 
inj
​
 H of work (this will later appear as the potential energy of the water that’s been raised)
file-1jpzjzmpct1fnz7y2pskxd
. This 
𝑊
out
W 
out
​
  is actually the mechanical work that the buoyant floater will eventually do (since displacing water and rising is what yields energy). If we again plug numbers: with 
𝑉
inj
=
0.1
 m
3
,
𝜌
=
1000
 kg/m
3
,
𝑔
=
9.81
,
𝐻
=
10
V 
inj
​
 =0.1 m 
3
 ,ρ=1000 kg/m 
3
 ,g=9.81,H=10 m, 
𝑊
out
=
1000
×
9.81
×
0.1
×
10
≈
9810
 
J
.
W 
out
​
 =1000×9.81×0.1×10≈9810J. That’s about 9.8 kJ of potential energy gained by that water (and thus available via buoyancy to do work on the system) – which is notably less than the ~14 kJ we calculated as needed to compress the air for this process. In general, analyzing these formulas shows that 
𝑊
in
W 
in
​
  (compression work) grows with pressure ratio (logarithmically), while 
𝑊
out
W 
out
​
  (buoyant lift) grows only linearly with depth and actually inversely with that same pressure (because at greater depth you need more pressure which makes a given amount of air correspond to less volume at depth)
file-1jpzjzmpct1fnz7y2pskxd
. The result: 
𝑊
in
>
𝑊
out
W 
in
​
 >W 
out
​
  for any realistic depth, meaning you can’t get more energy out than you put in – in fact you get less, which is why additional energy input is needed to keep the compressor running. Injection duration and impact on buoyancy: In practice, the injection happens over a short time. When the valve opens, high-pressure air floods the floater. Initially, the floater is filled with water (at rest, open to the tank). As air enters, it forms a bubble that pushes water out through any openings. If the floater has an outlet at the bottom, you’ll see a gush of water coming out as the air displaces it. The duration might be on the order of 1–5 seconds, depending on flow and floater size. During this time, the floater begins to uplift (you might imagine it tugging on the chain as soon as enough water is out). By the end of injection, the floater should be mostly air-filled and positively buoyant. A well-timed injection will result in the floater reaching full (or desired) buoyancy just as it leaves the bottom station. One must also consider that if multiple floaters were to be injected too closely in time, the air supply might be insufficient. The control logic can skip an injection if the tank pressure isn’t high enough, allowing the floater to remain filled with water (thus it won’t produce lift on that cycle). However, skipping would make the system unbalanced (one heavy floater going up while others are light), so usually the system is designed so the compressor and tank can keep up with the scheduled injections. The user interface of a simulation might allow adjusting the air pressure or number of floaters, and indeed, if you lower the available pressure too much or increase floats beyond capacity, the PLC would have to delay or skip injections to avoid partial fills. In a real KPP, if pressure is below a safe threshold, the PLC will simply wait (holding the valve closed) until the compressor raises the reservoir pressure again. This might momentarily pause the cycle or cause the heavy floater to be pulled up by others (reducing net output, and eventually the system would stop if too many are unfilled). In summary, the injection control system ensures each floater is filled only when adequate pressure is available – this prevents situations where a floater is only half-filled with air (which would yield less buoyancy and could destabilize the smooth rotation). The energy balance per cycle thus shapes the compressor duty: how much air (and thus energy) is needed per floater, and how often. If, say, each floater uses ~14 kJ of compressor work and yields ~9.8 kJ of lift work, and floaters are filled once every few seconds, the compressor’s power draw must at least match that rate. For instance, one floater every 3 seconds means ~4.7 kJ/s of output in buoyancy (which is ~1.6 kW of mechanical work available). The compressor input in that scenario would be perhaps ~7 kJ/s (~2.3 kW) to supply the air continuously. If the generator and other losses are taken into account, you’d typically find that the compressor is a net consumer of power – no surprise per physics. (Some over-unity claims aside, a legitimate analysis shows you always put in more via the compressor than you get out in the generator
file-1jpzjzmpct1fnz7y2pskxd
.) What’s important for our narrative is that compressor work input and buoyant work output are accounted for in the control so that the system runs steadily without pressure dropping too low or floaters not filling properly.
Floater Buoyancy and Ascent Behavior
Now we have a floater filled with air at the bottom – what happens next? This is where Archimedes’ principle comes into play. Archimedes’ principle states that the buoyant force on an object equals the weight of the fluid displaced by that object
courses.lumenlearning.com
. In simpler terms, when the floater is filled with air, it displaces a volume of water equal to its own submerged volume, and the water tries to push it upward with a force equal to the weight of that displaced water. Before filling, the floater was full of water and had a density about equal to water (plus the weight of its material), so it was neutrally buoyant or slightly heavy. After injection, most of that water is gone – replaced by low-density air – so the floater + remaining water weighs much less than the water it displaces. The upward buoyant force might be on the order of thousands of newtons for a big floater. For example, a 0.1 m³ air-filled floater displaces 0.1 m³ of water which weighs ~981 N (~100 kgf). If the floater’s own weight plus any residual water is, say, 20 kg (~196 N), then you have a net upward force of roughly 785 N. This force accelerates the floater upward and also translates into a torque on the chain that ultimately turns the generator (with gears to control speed/torque). When the air was injected, it pushed out most of the water inside the floater (you can think of the floater now like a balloon or a beach ball underwater). The instant the floater is released (valve closed or it departs the nozzle), it begins ascending. The motion might start a bit slower and then speed up – but in many KPP designs the ascent speed is regulated by the chain and generator (the generator provides resistance that limits how fast the chain of floaters can move). In fact, one description notes that the generator acts as a speed governor for the lifting bodies
ecoprius.pl
 – the floats would shoot up faster if free, but the mechanical load keeps the rise at a steady rate, extracting energy in the process. Let’s consider the pressure and expansion aspects as the floater rises. The floater at the bottom had high-pressure air inside (equal to the water pressure at depth, e.g. ~2 atm at 10 m). If the floater is a rigid closed container sealed after injection, then initially the air inside is at ~2 atm. As the floater rises, the water pressure outside drops. If the container were truly rigid and sealed, the internal air would remain at the same volume – which means its pressure would remain higher than the outside ambient as it goes up. By the time it nears the surface (1 atm outside), it might still have ~2 atm inside pushing outward. This would stress the container and also means the floater is carrying a high-pressure bubble. In practice, many floats might not be completely rigid or sealed – some designs allow the air to expand and vent gradually. For instance, if the floater has an open bottom (the diving bell scenario), the internal air will expand as external pressure drops, pushing a bit more water out from the bottom opening as it rises. In that case, the internal air pressure always equalizes to the surrounding water pressure at the same depth (plus a tiny bit to overcome surface tension). This is similar to how a bubble expands as it rises in water. If the float’s design keeps it upright, that expanding air just means the bubble of air occupies slightly more of the floater volume at shallow depth than it did at the bottom. This yields a bit of extra buoyancy near the top. No matter the design, the air will expand to some degree during ascent – either by the floater’s internal water being further pushed out or by the container walls flexing or by air simply being at higher pressure until venting. This expansion is an important process: it means the air is doing work (pushing out water or pushing on the container), and in doing so the air cools down (if no heat is added). This is essentially the reverse of compression: as pressure decreases, the air’s internal energy drops if it does work on the environment. One analysis noted: “The gas expands on the way upwards... but where does the energy for the expansion come from? Aha, the air cools down!”
physics.stackexchange.com
. So the thermal energy of the compressed air partly goes into doing expansion work. If the floater is open-bottomed, by the time it reaches near the surface, the air inside may have expanded nearly to atmospheric pressure (pushing out any last water). If it’s sealed, the expansion might be less until the vent opens, but either way the air’s pressure will eventually equalize to ambient when released. Another subtle effect: because the air inside is at higher pressure (especially initially), some of it can dissolve into the water (Henry’s law). High-pressure air in contact with water will have its nitrogen, oxygen, etc. dissolve in small amounts into the water, just like a soda can keeps CO₂ dissolved under pressure. At 2 atm, more gas will dissolve than at 1 atm
pmel.noaa.gov
. However, in the short time of a floater cycle, this gas absorption is likely minimal and quickly reverses when pressure drops (you might get tiny bubbles coming out of solution). We mention it for completeness: the water inside or around the floater might absorb a bit of air at the bottom and release it as the floater rises (similar to how divers can get gas coming out of blood if they ascend too fast). But this doesn’t drastically change the buoyancy – it’s a small mass of gas. Upward motion dynamics: The floater accelerates upward until it reaches a terminal velocity or is limited by the chain speed. The net force is 
𝐹
𝑛
𝑒
𝑡
=
𝐹
buoyancy
−
𝐹
weight
F 
net
​
 =F 
buoyancy
​
 −F 
weight
​
 . Using our previous rough numbers, 
𝐹
net
∼
785
 N
F 
net
​
 ∼785 N upward for a 0.1 m³ floater. If the floater (plus chain attachment etc.) weighs 20 kg, the net accelerating force is like lifting ~80 kgf. If free, it would accelerate at 
𝐹
/
𝑚
=
785
𝑁
/
20
kg
≈
39
m/s
2
F/m=785N/20kg≈39m/s 
2
  initially (about 4g!) – which shows how strong buoyancy can be. But in reality, it won’t accelerate that hard because the chain and generator impose a constraint, and drag forces in water increase with speed. Most likely, the floater rises at a relatively steady speed of maybe 0.5–1 m/s in a controlled KPP, converting that force into torque on the chain. The motion is smooth and continuous, with a new floater entering at bottom as one leaves at top, maintaining a kind of buoyant conveyor belt. During ascent, the pressure around the floater drops (hydrostatic pressure decreases). If the floater’s air can expand (open design), it will expand and thus maintain pressure equilibrium. This expansion can increase the volume of the air bubble – effectively the floater displaces a bit more water near the top than it did at the bottom, giving it a tad more buoyant force up high. This effect provides a slight buoyancy boost as it rises, because the same amount of air occupies a larger volume in the lower-pressure environment near the surface. If the expansion is isothermal (we’ll discuss that next), the air might double in volume from 10 m to surface (going from 2 atm to 1 atm). That means by the time it reaches the top, the floater could displace twice the volume of water compared to bottom (assuming its design allows that expansion). However, a real floater likely can’t double its displacement because it has a finite internal volume. In an open-bottom design, it might have still had some water in it at depth that gets pushed out by expansion on the way up. In any case, the buoyant force might increase slightly as it ascends. If the system is designed properly, this doesn’t cause issues – in fact it can help sustain torque. Some designs might actually count on that expansion to top off the displacement. One important thing is that the air inside cools as it expands (adiabatic cooling). If the water is warmer than the expanding air, heat will flow from the water into the air. We’ll cover this in detail in the thermodynamics section, but essentially the water can act as a heat reservoir to keep the air warmer (and more expanded) than it would be if it expanded without heat input. This is sometimes called a thermal buoyancy boost – the idea that the water’s heat compensates for the cooling of the air, making the expansion closer to isothermal (constant temperature) rather than adiabatic. In practical terms: if the water is, say, 20°C and the compressed air starts at 20°C but would cool to, say, 0°C upon expanding, the water might warm it back up toward 20°C as it rises. This keeps the air’s volume larger (since warmer gas at a given pressure takes more volume). If, on the other hand, the air remained hotter than water (perhaps if not enough cooling happened during compression or the water is cold), heat would flow from the air to the water, and the air could end up even colder by the time it reaches top, slightly reducing buoyancy
allmystery.de
. The balance of these temperatures can affect performance – more on that soon. So, our floater is now near the top of the tank, full of (perhaps expanded) air, pushing upward with a strong force. It has done work on the chain all along its ascent (turning the generator, or at least contributing to lifting the descending side floaters). Now it’s time for it to release the air so it can sink back down. This happens via the venting mechanism.
Venting Mechanism at the Top (Float Reset)
When a floater reaches the top of the water column, it needs to get rid of the air inside it and refill with water, resetting it to a heavy state to go down the other side. KPP designs achieve this in a passive, automatic way – often using the motion of the floater itself. Two common mechanisms were hinted at: tilting the floater or letting it breach the water surface. The goal is to expose an opening so that the compressed air can escape. In many systems, as the float nears the very top, it is guided by rails or cams that tilt it slightly, or the chain path might actually carry the float out of the water for an instant. For example, one description says each container actually “leaves the water for a short period of time. When [it] dips back into the water it again fills with water.”
reddit.com
. By popping out of the water momentarily at the top, the floater’s open bottom (or a vent hole) is directly exposed to the atmosphere – the pressurized air inside then rushes out because it’s now unconfined (it might make a splashing whoosh as it escapes). Even if it doesn’t fully leave the water, tilting it can allow the trapped air to spill out as a big bubble. If you imagine holding an inverted cup of air underwater and then tipping it, the air will flow out and rise. The KPP uses this principle: at the top, either via a slight tilt or by breaching, the air escapes automatically (no powered valve needed up top). When the air is released, two things happen:
The internal pressure of the floater immediately equalizes to atmospheric. The air that was at, say, ~2 atm inside vents out (you’ll see bubbles reaching the surface or just a release to open air).
Water rushes back in to fill the void. Usually, the floater is open-bottomed or has an intake such that once the air is gone, water can flood in from below (since the floater is submerged or partially submerged). This re-fills the floater with water, making it heavy again. Some descriptions say “on the top of the well the compressed air discharges and the water gets pumped in”
scribd.com
 – but note that “pumped in” here doesn’t mean an active pump, it’s just the water being pushed in by atmospheric pressure/gravity once the air is gone.
This venting process is passive: no compressor or motor is needed to let the air out; it’s simply the floater reaching a position where its air is no longer trapped. In some KPPs, the float might have a little flapper valve that opens when it hits a stop at the top, but the simplest method is geometry (tilt or breach). The timing is such that as soon as the float has finished doing its useful work (at the top of travel), it vents quickly. Resetting the floater’s weight: Once filled with water, the floater’s density is again higher (or equal to) water, so it will sink down the return side of the loop. Gravity now pulls it down, which actually can help the chain continue moving (some designs try to harness the downward side too, but in an ideal case the downward-moving heavy floaters mostly just balance part of the upward load). At minimum, the heavy floaters going down ensure that when they reach bottom, they are ready to be filled with air again. This continuous alternation of light (air-filled) floaters going up and heavy (water-filled) floaters going down is what makes the system cyclic. The venting dynamics: The release of air and influx of water can be quite rapid – often taking a second or two. If the floater is open to atmosphere at the top, the pressurized air might whoosh out in a fraction of a second (it may even make a loud hiss or bubbling). Water, being much denser, will glug in to replace it. If the openings are large (like the whole bottom is open), water floods in almost instantly as the air leaves. If there’s a smaller vent, the exchange might be a bit slower, potentially creating a time constant for filling. For instance, if a float had only a small hole, it might take a few seconds to completely flood as air escapes gradually. In well-designed systems, the opening is generous enough that this is not a bottleneck – usually by the time the floater has moved a short distance downward, it’s full of water. Some floats have a clever valve that ensures they fill completely. For example, a snorkel-like tube may allow air out at the top and then act as a siphon to pull water in. However, this is detail – the key is, the float is back to being essentially full of water by the time it starts its descent. The chain often has a guide to keep floaters upright when they enter the water again, to avoid trapping any residual air. If a floater didn’t fill fully with water (say a bubble remained inside), it would lessen its weight and could upset the balance. That’s why breaching or a good tilt is important – you want all the air out. Many KPP videos show a burst of bubbles at the top, indicating the air release. After venting, the floater now goes down on the return side (often outside the main tank or in a separate channel) simply under gravity. It might still be attached to the chain, ensuring a continuous loop. The system now essentially has a column of heavy water-filled floaters going down and buoyant air-filled floaters going up on the other side. This contrast is what drives the rotation. To summarize the venting stage: as a floater reaches the top, it automatically loses its air (via a tilt or by briefly exiting the water)
reddit.com
, the trapped air escapes and is not reused (it’s released to the atmosphere or into the open tank). Consequently, the floater fills with water and becomes heavy, ready to be pulled downward. The cycle then repeats when that floater hits bottom again and gets re-injected with fresh compressed air. One might wonder: isn’t releasing the air wasteful? Couldn’t we recapture that air and send it back to the compressor intake? In theory, one could collect the air (it will mostly just mix with the atmosphere at the top). Some experimental setups might channel the vented air into a pipe. However, since the air is at atmospheric pressure when released (assuming it’s fully expanded or at least vented at the top), you don’t gain much by recirculating it – the compressor anyway takes suction from ambient. The only thing you lose is any heat in that air. Some have considered using the cold air from expansion for something or the bubbles for aeration, but that’s beyond our scope. In KPP, the vented air is essentially an exhaust – the working fluid (air) is not a closed loop; it’s taken from the environment by the compressor and dumped out after doing its lifting job. The speed of flooding (water refilling the floater) might also have a minor effect: if it were too slow, the floater might remain partly buoyant a bit too long at the top. But generally, gravity and pressure difference make sure it fills quickly. Some systems have the float even over-rotate or get forced under to guarantee filling (like dunking it). Often, passive flaps are designed such that once the float is underwater again, they open to let water rush in freely. With venting complete, the floater (now just another water-filled bucket) travels down to the bottom to repeat the cycle. The continuous operation relies on orchestrating all these steps in harmony, which is the job of the control system.
Thermodynamic Considerations and “Thermal Buoyancy Boost”
We touched on the thermal aspects of compression and expansion, but let’s delve a bit deeper. The KPP’s pneumatic cycle can be thought of as a thermodynamic cycle involving heat and work. Understanding this gives insight into efficiency and the so-called “thermal buoyancy boost” where water heat helps the process. Compression heating and expansion cooling: When the compressor compresses the air, the air gets hot (unless perfectly cooled). This is wasted heat if not utilized. Many compressors will have after-coolers, possibly using the water from the tank as a heat sink, to dump this heat. So typically the compressed air in the tank might be close to ambient temperature (thanks to cooling) or slightly above. Now, when that air is injected into the floater and then allowed to expand on the way up, it tends to cool down (adiabatic expansion drops temperature). If no heat enters the air during ascent, by the time it reaches the top the air could be significantly colder than the water. This is where heat transfer from water to air can play a role. Water has a large thermal capacity; as the cool air bubble is in contact with water, heat will flow into the air, warming it. This additional heat intake from the water effectively increases the air’s pressure/volume compared to the adiabatic case. In other words, it makes the expansion closer to isothermal (constant temperature) by continuously absorbing heat from the surrounding water. If the expansion were truly isothermal (at, say, the water temperature ~20°C the whole way), the air would follow Boyle’s Law 
𝑃
𝑉
=
constant
PV=constant. The work done by the buoyant expansion would equal the heat absorbed from water (per the first law of thermodynamics). In the best case scenario for buoyancy, the air stays at water temperature throughout the ascent – meaning the water effectively warms the expanding air, keeping its pressure a bit higher than it would be if it just expanded without heat exchange. This yields a larger final volume of air in the floater at the top, hence more displaced water, i.e. a bit more buoyant work output. This is what we refer to as a “thermal buoyancy boost”: the idea that the surrounding water’s heat energy contributes to the work output by heating the expanding air. In effect, the system would be acting partly like a heat engine, taking thermal energy from water and converting some of it to mechanical work (lifting the floater). This is not free energy – it’s just energy from the water’s thermal reservoir (which will be cooled by a tiny amount). If the water is relatively warm and the air expansion is slow enough, the process leans toward isothermal. If the expansion is rapid or the water is cool, it’s closer to adiabatic (more cooling of air, less heat drawn in). To visualize: If at 10 m depth the air in the floater was ~2 atm and, say, 20°C, adiabatic expansion to 1 atm might drop it to perhaps 0°C (just as an illustration). If water is 20°C, it will heat that air bubble as it rises, maybe ending around, say, 15°C instead of 0°C by the time it vents. That means the air has a higher volume (or pressure) than it would if it were 0°C, giving extra lift. One forum discussion describes it well: “If the water is hotter, then the expanding air can take in heat, gaining energy, expand and increase buoyancy. If the air is warmer than the water, then the air will be cooled down, lose energy, shrink, and buoyancy is reduced.”
allmystery.de
. Thus, for optimal buoyancy, you’d prefer the water to be warm relative to the injected air’s temperature during expansion. In the KPP context, the designers might try to use this effect. For example, heat of compression could be recycled: if the compressor is cooled by the tank water (dumping heat into the water), and the expanding air then absorbs that heat back during ascent, it’s a form of energy loop (still not a net gain, but an efficiency improvement). One could jokingly say the KPP tries to act like a combined heat pump + heat engine: the compressor acts as a heat pump, pushing heat into the water (from the air it compressed), and the rising air acts as a heat engine, taking heat out of water to do extra work. However, practical limitations (temperature differences are small, and you can’t perfectly reclaim all that heat) mean you can’t break even this way – the Second Law of Thermodynamics ensures there’s no free lunch. But it does mean the water’s thermal energy can slightly augment the mechanical cycle if conditions are right. Some simulations might allow toggling between adiabatic vs. isothermal expansion assumptions for the floaters. Adiabatic (no heat exchange) is simpler to calculate but gives less buoyancy (cooled air has less volume). Isothermal (full heat exchange with water) gives more buoyancy – sometimes called “thermal boost”. To simulate it, one could assume the air in the floater always stays at water temperature as it rises. In reality, the truth is in between. If the float rises quickly, expansion is closer to adiabatic. If it rises slowly or has large surface area contact with water, it’s closer to isothermal. The KPP likely operates slow enough and with enough water contact (the air is usually in direct contact with water inside the floater) that it’s near-isothermal expansion. The water is also probably fairly constant in temperature from top to bottom (maybe a slight cooling at top if environment cool, but large volume likely well-mixed). So one can assume the air draws heat from water as needed. So what does this mean in numbers? If our 0.1 m³ at depth example was isothermal, at 2 atm bottom to 1 atm top, the air volume doubles to 0.2 m³ by the time it surfaces (if it can expand into that much space). If adiabatic, maybe it would only expand to, say, 0.18 m³ due to being colder. The difference (0.02 m³ of water volume) is the extra lift gained via heat. That corresponds to ~0.02 m³ * 1000 kg/m³ * 9.81 * 10 m / 2 = ~0.981 kJ extra energy (very rough, half of the water column average force times distance). Not huge, but some. The user’s mention of “thermal buoyancy boost” likely refers to leveraging this heat intake to maximize output. From a design perspective, ensuring the air is cooled during compression and that the water is warm will maximize efficiency. If the compressor’s heat is dumped into the water, the water warms a bit which in turn helps buoyancy. Of course, if the water gets too warm over time, that’s just heat from the compressor – effectively returning some input energy in another form. In summary, thermodynamics in KPP:
The compressor input work largely turns into heat (some lost, some in air).
The expanding air can absorb heat from water, making the expansion closer to isothermal which increases buoyant work output slightly.
The net result is still that you cannot get all the compressor work back as mechanical energy – some of it has been converted to heat and dissipated. But considering thermal effects is important for accurately simulating the system’s performance (especially if trying to close energy balances or explain why it can’t be over-unity). Essentially, the water acts as a thermal reservoir that can give or take heat from the air depending on temperature differences, which influences the pressure-volume trajectory of the air in the floater.
Control System Coordination and Operation
Finally, let’s discuss how the entire process is orchestrated by the control system. A KPP might look mechanically simple (just floaters, chains, and an air hose), but it actually relies on careful control logic to run smoothly and safely. A Programmable Logic Controller (PLC) or similar unit is typically used to monitor pressures, positions, and to actuate valves and the compressor. Key responsibilities of the control system include:
Maintaining Air Pressure: The PLC monitors the pressure in the air reservoir. If pressure drops near the minimum needed for injection, the PLC will trigger the compressor to turn on (or speed up). Conversely, if the pressure is at setpoint, it may idle the compressor to save energy. For example, “the PLC turns on the air compressor and waits several minutes until operating pressure is reached in the reservoir”
scribd.com
. Throughout operation, a pressure transducer feeds readings to the controller so it can keep the pressure within a target band (say, 10–15% above the minimum injection pressure required). This prevents injecting air that’s too low pressure to fully displace water. If the pressure is insufficient at the moment a floater arrives, the PLC might delay opening the injection valve for a moment until pressure builds up.
Sequencing the Injection Valve: The controller knows (via sensors or timers) when a floater is in position at the bottom. It will then open the solenoid or motorized valve to shoot air into that floater
scribd.com
. It likely keeps it open for a set duration or until a certain volume flows. Some systems might use a sensor (like detecting when water stops flowing out, or a float switch inside the floater) to determine when it’s full. However, timing is often enough if the supply pressure is steady and the floater volume is known. After injection, it closes the valve before the floater moves away, and readies for the next one. In the earlier descriptions we had, a mechanical valve connection was also involved – so the PLC may actually just keep the main feed pressurized and the physical alignment does the rest. But generally, the injection event is precisely controlled to avoid air wastage (shutting off as soon as the floater is filled).
Coordinating with Floater Positions: There may be an encoder or sensor on the chain to indicate floater positions (like “float #1 at bottom now”). Alternatively, a simple approach is to use the fact that one full rotation corresponds to a certain time (if speed is constant), so it can operate on a timed cycle. More sophisticated systems might have optical or magnetic sensors that detect a specific floater reaching the bottom (perhaps a switch triggered by the floater or chain link). The PLC uses this to know when to open valves. For example, “the next chamber gets in the lowest position... the valve connects and the chamber gets filled...”
scribd.com
 implies a synchronized handoff. If something is off (say a floater is misaligned), the PLC could detect a pressure drop anomaly or a position error and stop the cycle for safety.
Handling Abnormal Conditions: If the air pressure is too low (compressor can’t keep up or has fault), the PLC might skip injections. Practically, it would just not open the valve for that cycle – the floater stays full of water and goes up still heavy. If one float goes up heavy, the net torque might drop, possibly slowing the system (the PLC could detect generator speed change). It might then pause further injections until pressure is back up, or slow the chain drive if it’s actively driven. In demo systems, often the weight of descending floats and the momentum keep it going, but continued skips would stop it. The PLC could also choose to shut down if pressure falls below a safe margin to avoid partial fills (which could cause violent partial buoyancy or water hammer effects in the pipes).
User Controls and Settings: The system may allow operators to set the desired tank pressure, or number of active floaters, via a UI (user interface). For instance, a “pressure slider” could effectively change the compressor’s target pressure. A higher pressure would increase buoyant force (and power output) but also increase compressor power draw. The PLC would maintain whatever pressure setpoint is chosen. Similarly, a “number of floaters” setting might mean the ability to detach some floats or not fill certain ones to simulate having fewer. The PLC would then only inject every 2nd floater, for example. It ensures no two floaters are filled at once (unless designed otherwise) to avoid overloading the air supply. The coordination logic might look like: if pressure > P_min and floater at bottom, then inject; else skip and wait. There could also be interlocks like not opening the injection valve if the vent valve (if any) at top is somehow stuck, etc., though in passive vent designs that’s not an issue.
Compressor Cycling and Energy Management: The PLC also might cycle the compressor in an energy-efficient way. Compressors often work better running longer cycles than rapid on-off. So the PLC might allow pressure to drop to a lower threshold before kicking compressor on full, then charge up to an upper threshold and turn off (hysteresis control). This is akin to how an air compressor in a workshop kicks in at a certain low pressure and stops at high. In doing so, it might let the pressure vary a bit. The injection logic can accommodate some fluctuation; however, it must ensure that even at the lowest allowed pressure, there is still enough to fill a floater. If not, it will wait. In an example from the Rosch documentation, the compressor was run for a few minutes to reach operating pressure, and only then did the PLC start connecting the air to floats
scribd.com
. During continuous operation, it likely maintains that pressure with small deviations.
Safety and Shutdown: The control system monitors for any anomalies: e.g., if a floater doesn’t vent properly (maybe a float is stuck and comes around still containing air – which could mean it’s still buoyant on the wrong side), the system might detect an imbalance or a sensor might catch that air wasn’t vented (perhaps a pressure sensor at top or a visual inspection system). It could then stop the cycle to prevent mechanical damage. It also monitors compressor temperature/overload, generator load, etc. A KPP has significant forces, so safety stops are critical (e.g., an emergency stop that vents the air and halts the chain).
In essence, the PLC acts as the conductor of an orchestra, ensuring compressor, valves, and floaters are all in sync. One could outline a simplified logic as follows:
Initialize: Ensure the tank is filled with water and all floaters are water-filled. Compressor is off.
Pressure buildup: Turn on compressor until reservoir reaches target pressure (say 110% of needed)
scribd.com
.
Begin cycle: When pressure ready, start the chain/generator (or if the rising floaters drive it, allow it to start). Open injection valve for bottom float as it arrives.
Injection phase: Open valve for a set time (or until a sensor indicates float full). Then close.
Repeat for each floater: Each time a new floater arrives bottom, check pressure. If 
𝑃
>
𝑃
min
⁡
P>P 
min
​
 , inject. If 
𝑃
P is low, delay injection (maybe skip this floater) while compressor catches up.
Venting phase (passive): This happens automatically at top; the PLC might not need to do anything, but it could monitor if the venting occurred (perhaps by a pressure drop in floater or a tilt sensor).
Compressor control: If pressure drops below X, run compressor; if rises to Y, stop compressor. Keep within band.
Adjust for load: If generator load increases (say you hooked up more electrical load), the chain might slow, thus injection timing might shift; PLC could compensate by adjusting compressor output or allowing a bit lower speed.
Stop conditions: If stop command or emergency, it would likely vent remaining air (maybe a solenoid vent valve on the reservoir) and ensure floaters all sink, bringing system to a halt.
One notable mention in an article was: “it takes 21st-century electronics to make the device work” despite it being basically chains, floats, and compressor
fcnp.com
. This highlights that the precise control of timing and energy is crucial. The system has to balance the input and output so that it runs continuously without stalling or over-pressurizing. If the compressor falls behind, the control might reduce the generator load (somehow) or just eventually stop injection until recovered. In a simulation UI, one could play with a slider for air pressure: increasing it would show more buoyant force per floater (maybe faster chain speed or more power output), but one would also see the compressor working harder (maybe indicated by energy consumption). A slider for number of floaters engaged would show that with more floaters (or more frequent injection events), the compressor might struggle if not sized up, possibly resulting in pressure drop. The PLC logic we described would then skip some injections to avoid completely draining pressure. This could manifest as some floats not being filled (so you’d see them not contributing buoyancy, and the system output dropping). The user can learn that there is an optimal balance where compressor capacity matches the cycle’s air consumption. Finally, the control system ensures coordination such that each module operates in the right sequence: compressor builds pressure, valve injects at right time, float rises, vent occurs, etc., without collision or starvation. If everything is tuned, the KPP runs in a steady cyclic rhythm – air in at bottom, float up, air out at top, float down – converting pneumatic energy into kinetic energy and then into electrical energy via the generator. But as the laws of physics dictate, the electrical energy out will always be less than the electrical energy used by the compressor (plus some from the environment in the form of water heat cooling the compressor and warming the air). The control system doesn’t violate physics; it just smartly orchestrates the energy flows to keep the machine running as smoothly as possible. In conclusion, we have traced the path: compressed air (stored at high pressure) is delivered to a floater at depth, doing work by displacing water and giving the floater buoyancy. The floater rises, converting that work into mechanical energy while the air expands and cools (sometimes taking heat from water for a boost). At the top, the air is released and the floater refills with water, resetting its state. The cycle repeats with careful control ensuring timing and pressure are maintained. All modules – compressor, storage tank, injection valves, floaters, and venting system – work together in a synchronized dance. The narrative of the air in a Kinetic Power Plant is thus one of energy transformation: electrical energy to compressed air, to buoyant mechanical energy, and back to electrical via the generator, with every step governed by classical physics (Archimedes’ principle, ideal gas law, hydrostatics, thermodynamics). While the idea of generating surplus energy from buoyancy alone is “too good to be true” (since we must pay the piper in compression work)
fcnp.com
,
reddit.com
, the KPP is an intriguing demonstration of these principles in action – a complex interplay of pneumatics, mechanics, and control making for a continuous power machine (albeit one that follows conservation of energy). Each component, from the compressor’s hum to the floater’s splash, plays a role in this physically accurate story of energy circulating through air and water to do useful work.