# KPP Simulation Physics Documentation

## Overview

This document provides comprehensive technical documentation for the KPP (Kinetic Pneumatic Power) simulation system, covering all physics equations, implementations, and architectural decisions made during the 5-stage upgrade process.

## Table of Contents

1. [Physics Fundamentals](#physics-fundamentals)
2. [Force Calculations](#force-calculations)
3. [Chain Dynamics](#chain-dynamics)
4. [Energy Conservation](#energy-conservation)
5. [State Management](#state-management)
6. [Real-time Optimization](#real-time-optimization)
7. [Validation Framework](#validation-framework)
8. [Component Integration](#component-integration)

## Physics Fundamentals

### Core Physics Engine

The KPP simulation is built around a time-stepping physics engine that implements proper Euler integration for accurate force and motion calculations.

#### Time-Stepping Integration

The simulation uses a fixed or adaptive time step `dt` to advance the system state:

```
Position: x(t+dt) = x(t) + v(t) * dt
Velocity: v(t+dt) = v(t) + a(t) * dt
Acceleration: a(t) = F_net(t) / M_total
```

Where:
- `x(t)` = position at time t
- `v(t)` = velocity at time t  
- `a(t)` = acceleration at time t
- `F_net(t)` = net force at time t
- `M_total` = total system mass

#### Physical Constants

| Constant | Symbol | Value | Units | Description |
|----------|---------|-------|-------|-------------|
| Water Density | ρ_water | 1000.0 | kg/m³ | Density of water |
| Gravitational Acceleration | g | 9.81 | m/s² | Standard gravity |
| Atmospheric Pressure | P_atm | 101325 | Pa | Standard atmospheric pressure |
| Air Gas Constant | R_air | 287.0 | J/(kg·K) | Specific gas constant for air |

## Force Calculations

### Floater Forces

Each floater experiences three primary forces that determine its motion:

#### 1. Buoyant Force

The buoyant force acts upward on all submerged floaters according to Archimedes' principle:

```
F_buoyant = ρ_water × V_floater × g
```

Where:
- `V_floater` = floater volume (m³)
- Direction: Always upward (+y)
- Magnitude: Constant for each floater

#### 2. Gravitational Force (Weight)

The gravitational force depends on the floater's current state (filled or empty):

```
F_weight = m_effective × g
```

Where:
```
m_effective = {
    m_container + ρ_water × V_floater  (if filled with water - "heavy" state)
    m_container                        (if filled with air - "light" state)
}
```

- `m_container` = mass of empty floater container (kg)
- Direction: Always downward (-y)

#### 3. Hydrodynamic Drag Force

Drag force opposes motion and depends on velocity:

```
F_drag = 0.5 × ρ_water × C_d × A_cross × |v|² × sign(v)
```

Where:
- `C_d` = drag coefficient (dimensionless, typically 0.6-0.8)
- `A_cross` = cross-sectional area perpendicular to motion (m²)
- `v` = floater velocity relative to water (m/s)
- `sign(v)` = direction factor (-1 if moving down, +1 if moving up)

#### Net Floater Force

The net force on each floater is:

```
F_net_floater = F_buoyant - F_weight - F_drag
```

For ascending floaters (light state):
```
F_net = ρ_water × V × g - m_container × g - 0.5 × ρ_water × C_d × A × v²
```

For descending floaters (heavy state):
```
F_net = ρ_water × V × g - (m_container + ρ_water × V) × g - 0.5 × ρ_water × C_d × A × v²
```

### H1 Nanobubble Effects (Future Enhancement)

When H1 nanobubble technology is enabled, the effective drag coefficient is reduced for descending floaters:

```
C_d_effective = C_d × (1 - η_nanobubble) for descending floaters
C_d_effective = C_d                       for ascending floaters
```

Where `η_nanobubble` is the drag reduction factor (typically 0.1-0.2).

### H2 Thermal Assist Effects (Future Enhancement)

When H2 thermal assist is enabled, the effective buoyancy is enhanced for ascending floaters:

```
F_buoyant_effective = F_buoyant × (1 + η_thermal) for ascending floaters
F_buoyant_effective = F_buoyant                    for descending floaters
```

Where `η_thermal` is the thermal buoyancy enhancement factor (typically 0.05-0.15).

### H3 Pulse-and-Coast Enhancement

The H3 enhancement introduces a flywheel and clutch mechanism to optimize power generation through pulse-and-coast operation.

#### Flywheel Dynamics

The flywheel adds rotational inertia to the system:

```
I_total = I_base + I_flywheel when H3 enabled
I_total = I_base           when H3 disabled
```

Where:
- `I_base` = base system inertia (chain + sprockets) (kg·m²)
- `I_flywheel` = additional flywheel inertia (typically 10.0 kg·m²)

#### Clutch Mechanism

The clutch controls generator engagement based on torque:

```
clutch_engagement = {
    1.0  if |τ_net| > τ_threshold
    0.0  if |τ_net| ≤ τ_threshold
}
```

Where:
- `τ_net` = net torque from floaters
- `τ_threshold` = engagement threshold (typically 0.7 × I_total)

The clutch engagement transitions smoothly:

```
engagement_rate = dt / response_time
engagement(t+dt) = min(1.0, engagement(t) + engagement_rate)  // engaging
engagement(t+dt) = max(0.0, engagement(t) - engagement_rate)  // disengaging
```

#### Power Generation

The effective generator torque depends on clutch engagement:

```
τ_generator = base_torque × clutch_engagement
```

Where:
- `base_torque` = -k × ω (proportional to angular velocity)
- `k` = generator torque constant

#### Energy Storage

The flywheel stores kinetic energy during coast phase:

```
E_kinetic = 0.5 × I_total × ω²
```

This energy is released during power generation when the clutch engages.

#### Operating Limits

The system enforces speed limits for safety:

```
ω_min ≤ ω ≤ ω_max
```

Where:
- `ω_min` = minimum operating speed (typically 1.0 rad/s)
- `ω_max` = maximum safe speed (typically 10.0 rad/s)

## Chain Dynamics

### Chain Constraint Model

The KPP system uses a chain constraint that couples all floater motions. All floaters connected to the chain move with the same tangential velocity:

```
v_chain = constant for all floaters at any given time
```

### Total System Mass

The total mass includes all floaters plus the chain itself:

```
M_total = Σ(m_floater_i) + m_chain
```

Where:
```
m_chain = L_chain × ρ_chain_linear
```

- `L_chain` = total chain length (m)
- `ρ_chain_linear` = chain mass per unit length (kg/m)

### Chain Force Balance

The net force on the entire chain system is the sum of all individual floater forces:

```
F_net_chain = Σ(F_net_floater_i) - F_generator_resistance
```

### Chain Acceleration

Using Newton's second law for the entire system:

```
a_chain = F_net_chain / M_total
```

### Generator Resistance Force

The generator creates a resistance force that opposes chain motion:

```
F_generator = τ_generator / R_sprocket
```

Where:
- `τ_generator` = generator torque (N·m)
- `R_sprocket` = sprocket radius (m)

Direction: Opposes chain motion (always acts as a brake)

### Chain Velocity Update

The chain velocity is updated each time step:

```
v_chain(t+dt) = v_chain(t) + a_chain(t) × dt
```

### Angular Position Update

For circular motion, the angular position of the chain (and all floaters) is updated:

```
θ(t+dt) = θ(t) + (v_chain(t) / R_sprocket) × dt
```

## Energy Conservation

### Energy Input (Air Compression)

Energy is input to the system during air injection events:

```
W_injection = P_injection × V_air
```

Where:
```
P_injection = P_atmospheric + ρ_water × g × depth
```

- `depth` = water depth at injection point (m)
- `V_air` = volume of air injected (m³)

### Energy Output (Electrical Generation)

Energy is extracted from the system via the generator:

```
P_electrical = τ_generator × ω_generator × η_generator
```

Where:
- `ω_generator` = generator angular velocity (rad/s)
- `η_generator` = generator efficiency (typically 0.9-0.95)

```
ω_generator = v_chain / R_sprocket × gear_ratio
```

### Energy Balance Validation

The system maintains energy conservation within tolerance:

```
E_total(t) = E_kinetic(t) + E_potential(t) + E_input_cumulative - E_output_cumulative - E_losses_cumulative
```

Where:
- `E_kinetic = 0.5 × M_total × v_chain²`
- `E_potential = Σ(m_floater_i × g × h_i)` for all floaters
- `E_losses` includes friction, drag, and heat losses

### Energy Efficiency

System efficiency is calculated as:

```
η_system = E_output_cumulative / E_input_cumulative
```

Typical target efficiency: 40-60%

## State Management

### Floater State Transitions

Floaters transition between two primary states based on their position and current state:

#### State Definitions

1. **Heavy State**: Floater filled with water
   - Mass: `m_container + ρ_water × V_floater`
   - Buoyancy: Negative (sinks)

2. **Light State**: Floater filled with air
   - Mass: `m_container`
   - Buoyancy: Positive (floats)

#### Transition Triggers

##### Injection Event (Heavy → Light)

Occurs when:
```
floater.state == "heavy" AND 
floater.angle < injection_zone_angle AND
system_pressure >= minimum_injection_pressure
```

Where:
- `injection_zone_angle` ≈ 0.1 radians (near bottom)
- `minimum_injection_pressure` = calculated based on depth

##### Venting Event (Light → Heavy)

Occurs when:
```
floater.state == "light" AND 
abs(floater.angle - π) < venting_zone_angle
```

Where:
- `venting_zone_angle` ≈ 0.1 radians (near top)

### State Synchronization

State changes must be immediately reflected in force calculations:

1. **Mass Update**: `floater.mass` updated instantly
2. **Force Recalculation**: Forces recalculated using new mass
3. **Energy Accounting**: Injection energy added to total input

## Real-time Optimization

### Adaptive Time Stepping

The simulation can dynamically adjust the time step based on performance and accuracy requirements:

#### Performance-Based Adaptation

```
if computation_time > target_frame_time × 0.8:
    dt_new = dt × min(1.2, target_frame_time / computation_time)
elif computation_time < target_frame_time × 0.3:
    dt_new = dt × 0.9
else:
    dt_new = dt
```

#### Accuracy-Based Adaptation

```
error_estimate = |a_chain| × dt² + |v_chain| × dt
if error_estimate > error_tolerance:
    dt_new = dt × 0.8
elif error_estimate < error_tolerance × 0.1:
    dt_new = dt × 1.1
```

#### Time Step Limits

```
dt_min ≤ dt ≤ dt_max
```

Typical values:
- `dt_min = 0.01 s`
- `dt_max = 0.5 s`
- `dt_target = 0.1 s`

### Numerical Stability Monitoring

The system continuously monitors for numerical instabilities:

#### Stability Checks

1. **Velocity Limit**: `|v_chain| < v_max` (typically 10 m/s)
2. **Acceleration Limit**: `|a_chain| < a_max` (typically 50 m/s²)
3. **Force Limit**: `|F_i| < F_max` for all forces (typically 100 kN)
4. **NaN Detection**: Check for invalid floating-point values

#### Stability Score

```
stability_score = 1.0 - (violation_count / total_checks)
```

Where `violation_count` is the number of stability violations in recent history.

### Force Calculation Optimization

For systems with many floaters, force calculations can be optimized:

#### Vectorized Calculations

When `n_floaters ≥ 4`, batch calculations can be performed:

```python
# Batch mass array
masses = np.array([f.mass for f in floaters])

# Batch volume array  
volumes = np.array([f.volume for f in floaters])

# Batch force calculation
F_buoyant = rho_water * volumes * g
F_weight = masses * g
```

## Validation Framework

### Physics Validation Tests

#### Energy Conservation Test

Validates that energy is conserved within tolerance:

```python
def test_energy_conservation(simulation, tolerance=0.01):
    E_initial = calculate_total_energy(simulation, t=0)
    run_simulation(simulation, duration=100.0)
    E_final = calculate_total_energy(simulation, t=100)
    
    E_input = sum(injection_energies)
    E_output = sum(generation_energies)
    E_losses = sum(dissipation_energies)
    
    E_expected = E_initial + E_input - E_output - E_losses
    error = abs(E_final - E_expected) / E_expected
    
    return error < tolerance
```

#### Force Balance Test

Validates that forces sum correctly:

```python
def test_force_balance(floaters, chain_acceleration, total_mass):
    F_total = sum(calculate_floater_force(f) for f in floaters)
    F_expected = total_mass * chain_acceleration
    
    error = abs(F_total - F_expected)
    return error < 1e-6  # Very small tolerance for force balance
```

#### Single Floater Test

Validates individual floater physics:

```python
def test_single_floater(floater, expected_behavior):
    # Test buoyancy calculation
    F_buoy = rho_water * floater.volume * g
    assert abs(F_buoy - expected_buoyancy) < 1e-3
    
    # Test weight calculation  
    F_weight = floater.mass * g
    assert abs(F_weight - expected_weight) < 1e-3
    
    # Test net force direction
    F_net = F_buoy - F_weight
    if floater.state == "light":
        assert F_net > 0  # Should float
    else:
        assert F_net < 0  # Should sink
```

### Performance Validation

#### Frame Rate Test

```python
def test_performance(simulation, target_fps=10.0):
    start_time = time.time()
    steps = 100
    
    for i in range(steps):
        simulation.step(simulation.dt)
    
    elapsed = time.time() - start_time
    actual_fps = steps / elapsed
    
    return actual_fps >= target_fps
```

#### Memory Usage Test

```python
def test_memory_usage(simulation, max_growth_mb=10.0):
    initial_memory = get_memory_usage()
    
    for i in range(1000):
        simulation.step(simulation.dt)
    
    final_memory = get_memory_usage()
    growth = final_memory - initial_memory
    
    return growth < max_growth_mb
```

## Component Integration

### H3 Pulse-and-Coast Enhancement

The H3 enhancement introduces a pulse-and-coast mechanism using a flywheel and clutch system to optimize power generation.

#### Flywheel Dynamics

The flywheel adds rotational inertia to the system:

```
I_total = I_base + I_flywheel (when H3 enabled)
I_total = I_base           (when H3 disabled)
```

Where:
- `I_base` = base system inertia (chain + sprockets)
- `I_flywheel` = additional flywheel inertia

#### Clutch Mechanism

The clutch engagement is controlled based on torque thresholds:

```
engagement = {
    1.0  if |τ_net| > τ_threshold
    0.0  if |τ_net| ≤ τ_threshold
}
```

Engagement transitions are smoothed using a response time parameter:

```
engagement_rate = dt / response_time
engagement(t+dt) = min(1.0, engagement(t) + engagement_rate)  // when engaging
engagement(t+dt) = max(0.0, engagement(t) - engagement_rate)  // when disengaging
```

#### Generator Coupling

The effective generator torque is modulated by clutch engagement:

```
τ_generator_effective = τ_generator_base × clutch_engagement
```

#### Energy Storage

The flywheel stores kinetic energy during coast phases:

```
E_kinetic = 0.5 × I_total × ω²
```

This energy is released during power generation phases when the clutch engages.

### Component Integration

The physics components are integrated through a comprehensive testing framework:

#### Integration Tests

1. Basic Physics Integration
   - Validates force calculations (buoyancy, drag, weight)
   - Ensures proper time-stepping and state updates
   - Verifies energy conservation

2. Enhancement Integration
   - Tests H1 nanobubble effects on drag reduction
   - Validates H2 thermal expansion impact on buoyancy
   - Verifies H3 pulse-and-coast behavior
   - Ensures enhancements work together correctly

3. State Management
   - Tests floater state transitions (injection/venting)
   - Validates clutch engagement/disengagement
   - Verifies proper energy tracking

#### Performance Validation

The system undergoes rigorous performance testing:

1. Real-time Operation
   - Validates update rates meet timing requirements
   - Ensures stable operation under various loads
   - Monitors resource usage (CPU, memory)

2. Scalability Tests
   - Tests with different floater counts (10-1000)
   - Validates performance with all enhancements active
   - Measures throughput and response times

3. System Benchmarks
   - Physics engine update performance
   - Component manager efficiency
   - Control system response times
   - Data throughput capabilities

### Event Handler Integration

```python
# Event handler processes state transitions
events = event_handler.process_events(floaters, current_time)

# Update energy accounting
physics_engine.energy_input += events.total_injection_energy

# Update floater states
for floater_id, new_state in events.state_changes.items():
    floaters[floater_id].state = new_state
    floaters[floater_id].mass = calculate_mass(new_state)
```

### Monitoring Integration

```python
# Collect performance data
performance_data = {
    'computation_time': step_duration,
    'v_chain': physics_state.chain_velocity,
    'stability_score': stability_monitor.get_score()
}

# Process through real-time controller
rt_result = real_time_controller.process_data(physics_state, performance_data)

# Apply optimization recommendations
if rt_result.adjust_timestep:
    simulation.dt = rt_result.new_timestep
```

## Error Handling and Recovery

### Numerical Error Detection

The system detects and handles various numerical errors:

1. **NaN/Infinity Values**: Detected in all calculated quantities
2. **Extreme Values**: Forces, velocities, or accelerations outside physical limits
3. **Energy Violations**: Large deviations from energy conservation
4. **Oscillations**: Rapid sign changes in forces or accelerations

### Recovery Strategies

#### Timestep Reduction

```python
def handle_numerical_instability(error_data, context):
    # Reduce timestep by 50%
    new_dt = context['current_dt'] * 0.5
    
    # Reset extreme velocities
    if abs(context['v_chain']) > 10.0:
        context['v_chain'] = context['v_chain'] * 0.1
    
    return {
        'success': True,
        'action': 'reduce_timestep',
        'new_dt': new_dt,
        'reset_velocities': True
    }
```

#### State Reset

```python
def handle_state_corruption(error_data, context):
    # Reset floater positions to valid locations
    for floater in context['floaters']:
        if floater.angle < 0 or floater.angle > 2*pi:
            floater.angle = floater.angle % (2*pi)
    
    # Reset extreme velocities
    if abs(context['v_chain']) > 20.0:
        context['v_chain'] = 0.0
    
    return {
        'success': True,
        'action': 'reset_state',
        'message': 'Reset invalid floater positions and velocities'
    }
```

## Future Enhancement Framework

The system is designed to easily accommodate future enhancements:

### H1 Nanobubble Integration Points

- **Drag Coefficient Modification**: `fluid_system.apply_h1_effects()`
- **Bubble Generation Model**: `nanobubble_system.generate_bubbles()`
- **Energy Cost Accounting**: `energy_system.add_h1_costs()`

### H2 Thermal Assist Integration Points

- **Thermal Model Integration**: `thermal_system.apply_h2_effects()`
- **Heat Exchanger Model**: `heat_exchanger.update_efficiency()`
- **Buoyancy Enhancement**: `buoyancy_calculator.apply_thermal_boost()`

### H3 Pulse/Coast Integration Points

- **Control Strategy**: `control_system.apply_h3_strategy()`
- **Generator Engagement**: `generator.set_engagement_mode()`
- **Cycle Optimization**: `optimizer.optimize_pulse_coast_cycle()`

## Troubleshooting Guide

### Common Issues and Solutions

#### Low System Efficiency

**Symptoms**: Energy efficiency below 30%
**Causes**:
- High drag coefficients
- Excessive generator torque
- Poor timing of injection/venting events

**Solutions**:
- Reduce drag coefficient to 0.6-0.8 range
- Optimize generator torque for maximum power point
- Tune injection/venting zone angles

#### Numerical Instabilities

**Symptoms**: NaN values, extreme forces, simulation crashes
**Causes**:
- Time step too large
- Extreme parameter values
- Rapid state transitions

**Solutions**:
- Reduce time step to 0.05s or smaller
- Enable adaptive timestep
- Add transition smoothing for state changes

#### Poor Performance

**Symptoms**: Frame rate below target, high CPU usage
**Causes**:
- Inefficient force calculations
- Too many validation checks
- Large time step requiring high precision

**Solutions**:
- Enable force calculation optimization
- Reduce validation frequency
- Tune time step for optimal performance/accuracy trade-off

## References

1. **Fluid Mechanics**: Munson, Young, and Okiishi - "Fundamentals of Fluid Mechanics"
2. **Numerical Methods**: Press et al. - "Numerical Recipes"
3. **Real-time Systems**: Liu - "Real-Time Systems"
4. **Control Systems**: Franklin, Powell, and Emami-Naeini - "Feedback Control of Dynamic Systems"

## Appendix

### Symbol Definitions

| Symbol | Description | Units |
|--------|-------------|-------|
| ρ | Density | kg/m³ |
| V | Volume | m³ |
| g | Gravitational acceleration | m/s² |
| F | Force | N |
| m | Mass | kg |
| v | Velocity | m/s |
| a | Acceleration | m/s² |
| τ | Torque | N·m |
| ω | Angular velocity | rad/s |
| θ | Angular position | rad |
| P | Pressure | Pa |
| η | Efficiency | dimensionless |
| C_d | Drag coefficient | dimensionless |
| A | Area | m² |
| dt | Time step | s |

### Unit Conversions

- 1 bar = 100,000 Pa
- 1 kW = 1,000 W
- 1 RPM = π/30 rad/s
- 1 atmosphere = 101,325 Pa
