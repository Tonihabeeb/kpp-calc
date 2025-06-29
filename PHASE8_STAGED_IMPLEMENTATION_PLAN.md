# KPP Simulation Upgrade - Staged Implementation Plan

## Overview

This document outlines a comprehensive staged implementation plan to upgrade the KPP simulation backend for physical realism, correct force/torque handling, and robust real-time single-client operation as described in `first-patch.md`.

## Current State Analysis

The current simulation system (`simulation/engine.py`) already has many advanced components integrated:
- Integrated drivetrain system with sprocket, clutch, and flywheel
- Advanced generator with electrical system integration
- Enhanced physics modules (fluid, thermal, chain systems)
- Comprehensive control systems and grid services
- Loss models and transient event controllers

However, the core simulation loop needs restructuring to ensure proper time-stepping physics and force integration as outlined in the patch.

## Implementation Stages

### Stage 1: Core Physics Engine Refactoring (Priority: High)
**Duration: 1-2 weeks**

#### Objectives:
- Implement proper time-stepping simulation loop with correct force calculations
- Ensure all relevant forces are calculated and applied at each time step
- Establish robust single-client operation

#### Tasks:

1. **Refactor Simulation Loop Architecture**
   - Create new `PhysicsEngine` class to handle core physics calculations
   - Separate physics calculations from component integrations
   - Implement proper Euler integration for time-stepping

2. **Force Calculation Standardization**
   - Implement comprehensive force calculation for each floater:
     - Buoyant force: `F_B = ρ_water × V × g`
     - Gravitational force: `F_W = m × g` (mass depends on filled/empty state)
     - Hydrodynamic drag: `F_D = 0.5 × ρ_water × C_d × A × v²`
   - Ensure force directions are correctly applied based on motion

3. **Chain Constraint Dynamics**
   - Implement proper chain coupling where all floaters move with same chain velocity
   - Calculate net force from all floaters: `F_net = Σ(floater_forces)`
   - Compute chain acceleration: `a_chain = F_net / M_total`

4. **Generator Load Integration**
   - Convert generator torque to equivalent force: `F_gen = τ_gen / R`
   - Include generator resistance in net force calculation
   - Calculate electrical power output: `P_out = τ_gen × ω`

#### Implementation Details:

```python
class PhysicsEngine:
    def __init__(self, params):
        self.dt = params.get('time_step', 0.1)
        self.rho_water = 1000.0  # kg/m³
        self.g = 9.81  # m/s²
        
    def calculate_floater_forces(self, floater, velocity):
        # Buoyant force (constant, upward)
        F_buoy = self.rho_water * floater.volume * self.g
        
        # Weight force (depends on state)
        if floater.state == "heavy":
            mass = floater.container_mass + self.rho_water * floater.volume
        else:
            mass = floater.container_mass
        F_weight = mass * self.g
        
        # Drag force (opposes motion)
        F_drag = 0.5 * self.rho_water * floater.Cd * floater.area * velocity**2
        
        # Net force calculation based on position
        if floater.is_ascending():
            return F_buoy - F_weight - F_drag
        else:
            return F_weight - F_buoy - F_drag
    
    def update_chain_dynamics(self, floaters, v_chain, generator_torque, sprocket_radius):
        # Calculate total mass
        M_total = sum(f.mass for f in floaters) + self.chain_mass
        
        # Calculate net force from all floaters
        F_net_total = 0.0
        for floater in floaters:
            floater_velocity = v_chain if floater.is_ascending() else -v_chain
            F_net_total += self.calculate_floater_forces(floater, floater_velocity)
        
        # Include generator resistance
        F_gen = generator_torque / sprocket_radius
        F_net_total -= F_gen * math.copysign(1, v_chain)
        
        # Calculate acceleration
        a_chain = F_net_total / M_total
        
        return a_chain, F_net_total
```

#### Files to Modify:
- `simulation/engine.py` - Main simulation loop refactoring
- `simulation/components/floater.py` - Enhanced force calculations
- Create `simulation/physics/physics_engine.py` - New physics engine

---

### Stage 2: State Management and Event Handling (Priority: High)
**Duration: 1 week**

#### Objectives:
- Implement proper floater state transitions (injection/venting)
- Track energy consumption for air compression
- Ensure events occur at correct physical locations

#### Tasks:

1. **Event Detection System**
   - Implement precise bottom/top detection using angular position
   - Create event handlers for air injection and venting
   - Ensure events don't trigger multiple times per floater per cycle

2. **Energy Tracking**
   - Calculate compression energy: `W_inject = P_depth × V_air`
   - Track cumulative energy input and output
   - Implement energy balance verification

3. **State Synchronization**
   - Ensure floater mass updates immediately affect force calculations
   - Coordinate state changes with physics engine updates

#### Implementation Details:

```python
class EventHandler:
    def __init__(self, tank_depth):
        self.tank_depth = tank_depth
        self.bottom_zone = 0.1  # radians
        self.top_zone = 0.1     # radians
        self.energy_input = 0.0
        
    def handle_injection(self, floater):
        if floater.state == "heavy" and floater.angle < self.bottom_zone:
            # State transition
            floater.state = "light"
            floater.mass = floater.container_mass
            
            # Energy calculation
            P_depth = 101325 + 1000 * 9.81 * self.tank_depth  # Pa
            W_inject = P_depth * floater.volume  # Joules
            self.energy_input += W_inject
            
            return True
        return False
    
    def handle_venting(self, floater):
        if floater.state == "light" and abs(floater.angle - math.pi) < self.top_zone:
            floater.state = "heavy"
            floater.mass = floater.container_mass + 1000 * floater.volume
            return True
        return False
```

#### Files to Modify:
- `simulation/components/floater.py` - State management methods
- Create `simulation/physics/event_handler.py` - Event detection and handling
- `simulation/engine.py` - Integrate event handling into main loop

---

### Stage 3: Integration and Validation Framework (Priority: Medium)
**Duration: 1 week**

#### Objectives:
- Integrate new physics engine with existing advanced components
- Create validation and testing framework
- Ensure compatibility with existing features

#### Tasks:

1. **Component Integration**
   - Integrate new physics engine with existing `IntegratedDrivetrain`
   - Maintain compatibility with advanced generator and electrical systems
   - Preserve existing control system functionality

2. **Validation Framework**
   - Implement physics validation tests (energy conservation, force balance)
   - Create unit tests for individual components
   - Add logging for debugging and verification

3. **Parameter Optimization**
   - Tune time step size for stability and accuracy
   - Optimize generator torque settings for realistic operation
   - Validate against expected physical behavior

#### Implementation Details:

```python
class ValidationFramework:
    def __init__(self):
        self.energy_tolerance = 0.01  # 1% tolerance
        
    def validate_energy_conservation(self, energy_in, energy_out, losses):
        total_energy = energy_out + losses
        conservation_error = abs(total_energy - energy_in) / energy_in
        return conservation_error < self.energy_tolerance
    
    def validate_force_balance(self, forces):
        net_force = sum(forces)
        return abs(net_force) < 1e-6  # Nearly zero at equilibrium
    
    def run_physics_tests(self, simulation):
        # Test suite for physics validation
        results = {}
        
        # Test 1: Single floater behavior
        results['single_floater'] = self.test_single_floater(simulation)
        
        # Test 2: Energy balance
        results['energy_balance'] = self.test_energy_balance(simulation)
        
        # Test 3: Equilibrium behavior
        results['equilibrium'] = self.test_equilibrium(simulation)
        
        return results
```

#### Files to Modify:
- `simulation/engine.py` - Integration with existing components
- Create `validation/physics_validation.py` - Validation framework
- Create `tests/test_physics_engine.py` - Unit tests

---

### Stage 4: Real-time Optimization and Streaming (Priority: Medium)
**Duration: 1 week**

#### Objectives:
- Optimize simulation for real-time performance
- Enhance data streaming for single-client operation
- Implement robust error handling

#### Tasks:

1. **Performance Optimization**
   - Profile simulation loop for bottlenecks
   - Optimize force calculations using vectorization where possible
   - Implement adaptive time stepping if needed

2. **Enhanced Data Streaming**
   - Expand data output to include all physics quantities
   - Implement configurable data sampling rates
   - Add real-time performance monitoring

3. **Error Handling and Recovery**
   - Implement numerical stability checks
   - Add graceful degradation for extreme parameters
   - Create robust restart mechanisms

#### Implementation Details:

```python
class RealTimeOptimizer:
    def __init__(self, target_fps=10):
        self.target_fps = target_fps
        self.frame_time = 1.0 / target_fps
        self.performance_history = []
        
    def optimize_timestep(self, computation_time, current_dt):
        # Adaptive time stepping based on computation performance
        if computation_time > self.frame_time * 0.8:
            # Computation taking too long, increase dt
            return min(current_dt * 1.1, 0.2)
        elif computation_time < self.frame_time * 0.3:
            # Computation very fast, decrease dt for accuracy
            return max(current_dt * 0.9, 0.01)
        return current_dt
    
    def monitor_performance(self, step_time, physics_time, output_time):
        self.performance_history.append({
            'total_time': step_time,
            'physics_time': physics_time,
            'output_time': output_time,
            'utilization': step_time / self.frame_time
        })
        
        # Keep only recent history
        if len(self.performance_history) > 100:
            self.performance_history.pop(0)
```

#### Files to Modify:
- `simulation/engine.py` - Performance optimization
- `app.py` or `start_server.py` - Enhanced streaming
- Create `utils/performance_monitor.py` - Performance monitoring

---

### Stage 5: Documentation and Future-Proofing (Priority: Low)
**Duration: 1 week**

#### Objectives:
- Create comprehensive documentation
- Prepare hooks for future H1/H2/H3 implementations
- Establish coding standards and maintenance guidelines

#### Tasks:

1. **Technical Documentation**
   - Document all physics equations and implementations
   - Create API documentation for new components
   - Write user guide for parameter tuning

2. **Future Enhancement Hooks**
   - Add placeholders for H1 (nanobubbles) effects
   - Prepare framework for H2 (thermal assist) integration
   - Design architecture for H3 (pulse/coast) control

3. **Code Quality and Maintenance**
   - Implement comprehensive logging
   - Add code comments and docstrings
   - Create maintenance and debugging guides

#### Implementation Details:

```python
class HypothesisFramework:
    """Framework for future hypothesis implementations"""
    
    def __init__(self):
        self.h1_enabled = False  # Nanobubbles
        self.h2_enabled = False  # Thermal assist
        self.h3_enabled = False  # Pulse/coast
        
    def apply_h1_effects(self, floater, base_drag):
        """Apply H1 nanobubbles effect to reduce drag"""
        if self.h1_enabled and not floater.is_ascending():
            # Reduce effective drag for descending floaters
            nanobubble_factor = 0.8  # 20% drag reduction
            return base_drag * nanobubble_factor
        return base_drag
    
    def apply_h2_effects(self, floater, base_buoyancy):
        """Apply H2 thermal assist to enhance buoyancy"""
        if self.h2_enabled and floater.is_ascending():
            # Increase effective buoyancy due to thermal expansion
            thermal_factor = 1.1  # 10% buoyancy increase
            return base_buoyancy * thermal_factor
        return base_buoyancy
    
    def apply_h3_control(self, generator_torque, cycle_phase):
        """Apply H3 pulse/coast control strategy"""
        if self.h3_enabled:
            # Implement pulse/coast logic
            if cycle_phase == "coast":
                return 0.0  # Disengage generator
            elif cycle_phase == "pulse":
                return generator_torque * 2.0  # Double torque during pulse
        return generator_torque
```

#### Files to Create:
- `docs/physics_documentation.md` - Comprehensive physics documentation
- `docs/api_reference.md` - API documentation
- `simulation/future/hypothesis_framework.py` - Future enhancement framework

---

## Implementation Timeline

| Stage | Duration | Dependencies | Key Deliverables |
|-------|----------|--------------|------------------|
| Stage 1 | 1-2 weeks | None | Core physics engine, proper force calculations |
| Stage 2 | 1 week | Stage 1 | Event handling, energy tracking |
| Stage 3 | 1 week | Stages 1-2 | Integration, validation framework |
| Stage 4 | 1 week | Stages 1-3 | Performance optimization, real-time streaming |
| Stage 5 | 1 week | All previous | Documentation, future-proofing |

**Total Duration: 5-6 weeks**

## Risk Mitigation

1. **Compatibility Issues**: Maintain backward compatibility with existing components through adapter patterns
2. **Performance Degradation**: Implement performance monitoring and adaptive optimization
3. **Numerical Stability**: Use validated integration methods and stability checks
4. **Scope Creep**: Focus strictly on backend physics; defer frontend enhancements to later phases

## Success Criteria

1. **Physical Realism**: All forces correctly calculated and applied each time step
2. **Energy Conservation**: Energy balance validation within 1% tolerance
3. **Stable Operation**: Continuous operation without crashes or numerical instabilities
4. **Performance**: Real-time operation at 10+ FPS with multiple floaters
5. **Extensibility**: Clean architecture ready for H1/H2/H3 implementations

## Next Steps

1. Begin Stage 1 implementation immediately
2. Set up development branch for physics engine work
3. Create test scenarios for validation
4. Establish performance benchmarks
5. Coordinate with existing codebase integration points

This staged approach ensures systematic improvement while maintaining system stability and preparing for future enhancements as outlined in the KPP simulation upgrade requirements.
