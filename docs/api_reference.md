# KPP Simulation API Reference

## Overview

This document provides comprehensive API documentation for the KPP simulation system, covering all major components, classes, and methods implemented in the upgraded physics engine.

## Core Physics Engine

### PhysicsEngine

The main physics calculation engine that handles time-stepping simulation and force integration.

```python
class PhysicsEngine:
    """Core physics engine for KPP simulation with proper time-stepping and force calculations."""
```

#### Constructor

```python
def __init__(self, params: dict)
```

**Parameters:**
- `params` (dict): Configuration parameters including:
  - `time_step` (float): Simulation time step in seconds (default: 0.1)
  - `rho_water` (float): Water density in kg/m³ (default: 1000.0)
  - `gravity` (float): Gravitational acceleration in m/s² (default: 9.81)
  - `chain_mass` (float): Total chain mass in kg
  - `tank_depth` (float): Tank depth in meters

#### Methods

##### calculate_floater_forces

```python
def calculate_floater_forces(self, floater: Floater, velocity: float) -> float
```

Calculates the net force acting on a floater based on its current state and motion.

**Parameters:**
- `floater` (Floater): The floater object
- `velocity` (float): Current chain velocity in m/s

**Returns:**
- `float`: Net force in Newtons (positive = upward/forward)

**Force Components:**
- Buoyant force: `F_B = ρ_water × V × g`
- Weight force: `F_W = m × g` (varies with filled/empty state)
- Drag force: `F_D = 0.5 × ρ_water × C_d × A × v²`

##### update_chain_dynamics

```python
def update_chain_dynamics(self, floaters: List[Floater], v_chain: float, 
                         generator_torque: float, sprocket_radius: float) -> Tuple[float, float]
```

Updates chain dynamics based on all acting forces.

**Parameters:**
- `floaters` (List[Floater]): List of all floaters in the system
- `v_chain` (float): Current chain velocity in m/s
- `generator_torque` (float): Generator resistance torque in N⋅m
- `sprocket_radius` (float): Sprocket radius in meters

**Returns:**
- `Tuple[float, float]`: (chain_acceleration, net_force)

## Event Handling System

### AdvancedEventHandler

Manages floater state transitions and energy tracking with precise position-based event detection.

```python
class AdvancedEventHandler:
    """Advanced event handler with energy tracking and zone-based detection."""
```

#### Constructor

```python
def __init__(self, tank_depth: float, config: dict = None)
```

**Parameters:**
- `tank_depth` (float): Tank depth in meters
- `config` (dict): Configuration parameters including:
  - `bottom_zone_angle` (float): Bottom detection zone in radians
  - `top_zone_angle` (float): Top detection zone in radians
  - `energy_efficiency` (float): Compression efficiency factor

#### Methods

##### handle_injection_event

```python
def handle_injection_event(self, floater: Floater, angle: float) -> bool
```

Handles air injection event when floater reaches bottom zone.

**Parameters:**
- `floater` (Floater): Target floater
- `angle` (float): Current angular position in radians

**Returns:**
- `bool`: True if injection occurred, False otherwise

##### handle_venting_event

```python
def handle_venting_event(self, floater: Floater, angle: float) -> bool
```

Handles air venting event when floater reaches top zone.

**Parameters:**
- `floater` (Floater): Target floater
- `angle` (float): Current angular position in radians

**Returns:**
- `bool`: True if venting occurred, False otherwise

##### get_energy_metrics

```python
def get_energy_metrics(self) -> dict
```

Returns comprehensive energy tracking metrics.

**Returns:**
- `dict`: Energy metrics including:
  - `total_input` (float): Total energy input in Joules
  - `compression_work` (float): Work done in compression
  - `efficiency` (float): Overall system efficiency

## State Management

### StateSynchronizer

Ensures immediate synchronization between floater states and physics calculations.

```python
class StateSynchronizer:
    """Synchronizes floater state changes with physics engine updates."""
```

#### Methods

##### synchronize_floater_state

```python
def synchronize_floater_state(self, floater: Floater, physics_engine: PhysicsEngine) -> None
```

Synchronizes floater state with physics engine immediately after state change.

**Parameters:**
- `floater` (Floater): Floater with updated state
- `physics_engine` (PhysicsEngine): Physics engine to update

## Validation Framework

### ValidationFramework

Comprehensive validation system for physics accuracy and system consistency.

```python
class ValidationFramework:
    """Framework for validating physics accuracy and system consistency."""
```

#### Methods

##### validate_energy_conservation

```python
def validate_energy_conservation(self, energy_in: float, energy_out: float, 
                                losses: float) -> bool
```

Validates energy conservation within tolerance limits.

**Parameters:**
- `energy_in` (float): Total energy input in Joules
- `energy_out` (float): Total energy output in Joules
- `losses` (float): System losses in Joules

**Returns:**
- `bool`: True if energy is conserved within tolerance

##### validate_force_balance

```python
def validate_force_balance(self, forces: List[float]) -> bool
```

Validates force balance at equilibrium conditions.

**Parameters:**
- `forces` (List[float]): List of all forces in the system

**Returns:**
- `bool`: True if forces are balanced within tolerance

##### run_comprehensive_validation

```python
def run_comprehensive_validation(self, simulation_data: dict) -> dict
```

Runs complete validation suite on simulation data.

**Parameters:**
- `simulation_data` (dict): Complete simulation state and history

**Returns:**
- `dict`: Validation results with pass/fail status for each test

## Real-time Optimization

### RealTimeOptimizer

Optimizes simulation performance for real-time operation.

```python
class RealTimeOptimizer:
    """Real-time performance optimizer with adaptive time-stepping."""
```

#### Methods

##### optimize_timestep

```python
def optimize_timestep(self, computation_time: float, current_dt: float) -> float
```

Dynamically adjusts time step based on computational performance.

**Parameters:**
- `computation_time` (float): Time taken for last simulation step
- `current_dt` (float): Current time step size

**Returns:**
- `float`: Optimized time step size

##### get_performance_metrics

```python
def get_performance_metrics(self) -> dict
```

Returns real-time performance metrics.

**Returns:**
- `dict`: Performance data including FPS, utilization, and timing breakdowns

## Monitoring System

### RealTimeMonitor

Comprehensive monitoring system for simulation health and performance.

```python
class RealTimeMonitor:
    """Real-time monitoring system for simulation health and performance."""
```

#### Methods

##### monitor_system_health

```python
def monitor_system_health(self, simulation_state: dict) -> dict
```

Monitors overall system health and stability.

**Parameters:**
- `simulation_state` (dict): Current simulation state

**Returns:**
- `dict`: Health metrics and alert status

##### generate_alerts

```python
def generate_alerts(self, metrics: dict) -> List[dict]
```

Generates alerts based on monitoring metrics.

**Parameters:**
- `metrics` (dict): Current system metrics

**Returns:**
- `List[dict]`: List of active alerts with severity and descriptions

## Data Types and Structures

### Floater

Enhanced floater class with state management and physics integration.

#### Properties

- `state` (str): Current state ("heavy" or "light")
- `mass` (float): Current mass in kg
- `volume` (float): Volume in m³
- `area` (float): Cross-sectional area in m²
- `Cd` (float): Drag coefficient
- `container_mass` (float): Empty container mass in kg
- `angle` (float): Angular position in radians

#### Methods

##### is_ascending

```python
def is_ascending(self) -> bool
```

Determines if floater is currently ascending.

**Returns:**
- `bool`: True if ascending, False if descending

##### update_mass

```python
def update_mass(self, new_state: str) -> None
```

Updates floater mass based on state change.

**Parameters:**
- `new_state` (str): New floater state ("heavy" or "light")

## Configuration Parameters

### Default Configuration

```python
DEFAULT_CONFIG = {
    'physics': {
        'time_step': 0.1,           # seconds
        'rho_water': 1000.0,        # kg/m³
        'gravity': 9.81,            # m/s²
        'chain_mass': 1000.0,       # kg
    },
    'validation': {
        'energy_tolerance': 0.01,    # 1% tolerance
        'force_tolerance': 1e-6,     # Nearly zero
        'stability_threshold': 1e-3, # Stability limit
    },
    'optimization': {
        'target_fps': 10,           # Target frame rate
        'adaptive_timestep': True,  # Enable adaptive stepping
        'performance_history': 100, # History buffer size
    },
    'monitoring': {
        'alert_thresholds': {
            'energy_error': 0.05,   # 5% energy error threshold
            'force_imbalance': 0.1, # Force imbalance threshold
            'performance_drop': 0.7 # Performance utilization threshold
        }
    }
}
```

## Error Handling

### Common Exceptions

#### PhysicsEngineError

Raised when physics calculations encounter invalid states or parameters.

#### ValidationError

Raised when validation checks fail beyond acceptable tolerances.

#### OptimizationError

Raised when real-time optimization cannot maintain target performance.

## Usage Examples

### Basic Simulation Setup

```python
from simulation.physics.physics_engine import PhysicsEngine
from simulation.physics.advanced_event_handler import AdvancedEventHandler
from simulation.physics.state_synchronizer import StateSynchronizer

# Initialize components
physics_engine = PhysicsEngine({
    'time_step': 0.05,
    'tank_depth': 10.0
})

event_handler = AdvancedEventHandler(tank_depth=10.0)
state_sync = StateSynchronizer()

# Run simulation step
for step in range(1000):
    # Calculate forces and update dynamics
    acceleration, net_force = physics_engine.update_chain_dynamics(
        floaters, velocity, generator_torque, sprocket_radius
    )
    
    # Handle events
    for floater in floaters:
        if event_handler.handle_injection_event(floater, floater.angle):
            state_sync.synchronize_floater_state(floater, physics_engine)
```

### Validation and Monitoring

```python
from validation.physics_validation import ValidationFramework
from simulation.monitoring.real_time_monitor import RealTimeMonitor

validator = ValidationFramework()
monitor = RealTimeMonitor()

# Validate system
validation_results = validator.run_comprehensive_validation(simulation_data)

# Monitor performance
health_metrics = monitor.monitor_system_health(simulation_state)
alerts = monitor.generate_alerts(health_metrics)
```

## Version Information

- **API Version**: 2.0.0
- **Last Updated**: Stage 5 Implementation
- **Compatibility**: Python 3.8+
- **Dependencies**: NumPy, SciPy, Flask (for web interface)

## Support and Maintenance

For technical support or bug reports, refer to the maintenance documentation in `docs/maintenance_guide.md`.

For performance tuning and optimization guidelines, see `docs/performance_tuning.md`.
