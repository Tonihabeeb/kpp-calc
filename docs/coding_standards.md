# KPP Simulation Coding Standards and Best Practices

## Overview

This document establishes coding standards, best practices, and guidelines for maintaining and extending the KPP simulation system. These standards ensure code quality, maintainability, and consistency across all components.

## Code Style and Formatting

### Python Style Guide

Follow PEP 8 with the following specific guidelines:

#### Naming Conventions

```python
# Classes: PascalCase
class PhysicsEngine:
    pass

class AdvancedEventHandler:
    pass

# Functions and variables: snake_case
def calculate_floater_forces(floater, velocity):
    chain_tension = get_chain_tension()
    return net_force

# Constants: UPPER_SNAKE_CASE
MAX_SIMULATION_TIME = 3600.0
DEFAULT_TIME_STEP = 0.1
GRAVITATIONAL_ACCELERATION = 9.81

# Private methods and variables: leading underscore
class SimulationEngine:
    def __init__(self):
        self._internal_state = {}
    
    def _update_internal_metrics(self):
        pass
```

#### Type Hints

Always use type hints for function parameters and return values:

```python
from typing import Dict, List, Optional, Tuple, Union
import numpy as np

def calculate_forces(floater: 'Floater', 
                    velocity: float, 
                    parameters: Dict[str, float]) -> Tuple[float, float]:
    """Calculate forces with proper type annotations."""
    return net_force, acceleration

def validate_state(state: Dict[str, Any]) -> bool:
    """Validate simulation state."""
    return True

def get_floater_list() -> List['Floater']:
    """Return list of floaters."""
    return []
```

#### Documentation Standards

Use Google-style docstrings:

```python
def calculate_buoyancy_force(floater: 'Floater', fluid_density: float) -> float:
    """Calculate buoyancy force acting on a floater.
    
    Uses Archimedes' principle to calculate the upward buoyant force
    based on the displaced fluid volume and density.
    
    Args:
        floater: The floater object containing volume and state information
        fluid_density: Density of the surrounding fluid in kg/m³
        
    Returns:
        Buoyancy force in Newtons (positive = upward)
        
    Raises:
        ValueError: If floater volume is negative or fluid density is non-positive
        
    Example:
        >>> floater = Floater(volume=0.1, state='light')
        >>> force = calculate_buoyancy_force(floater, 1000.0)
        >>> print(f"Buoyancy force: {force:.2f} N")
    """
    if floater.volume < 0:
        raise ValueError("Floater volume must be positive")
    if fluid_density <= 0:
        raise ValueError("Fluid density must be positive")
        
    return fluid_density * floater.volume * GRAVITATIONAL_ACCELERATION
```

## Architecture Patterns

### Component Design

#### Single Responsibility Principle

Each class should have one reason to change:

```python
# Good: Single responsibility
class ForceCalculator:
    """Handles only force calculations."""
    def calculate_buoyancy(self, volume: float, density: float) -> float:
        return volume * density * GRAVITATIONAL_ACCELERATION
        
class StateManager:
    """Handles only state transitions."""
    def transition_floater_state(self, floater: 'Floater', new_state: str) -> None:
        floater.state = new_state

# Avoid: Multiple responsibilities
class FloaterManager:  # Don't do this
    def calculate_forces(self, floater):
        pass  # Force calculation
    def update_state(self, floater):
        pass  # State management
    def log_events(self, event):
        pass  # Logging
```

#### Dependency Injection

Use dependency injection for better testability:

```python
class SimulationEngine:
    def __init__(self, 
                 physics_engine: PhysicsEngine,
                 event_handler: EventHandler,
                 validator: ValidationFramework):
        self.physics_engine = physics_engine
        self.event_handler = event_handler
        self.validator = validator
        
    def run_simulation_step(self) -> None:
        # Use injected dependencies
        forces = self.physics_engine.calculate_forces()
        events = self.event_handler.process_events()
        self.validator.validate_state()
```

#### Interface Segregation

Use abstract base classes for interfaces:

```python
from abc import ABC, abstractmethod

class PhysicsModelInterface(ABC):
    """Interface for physics models."""
    
    @abstractmethod
    def calculate_forces(self, state: Dict[str, Any]) -> np.ndarray:
        """Calculate forces based on current state."""
        pass
        
    @abstractmethod
    def validate_state(self, state: Dict[str, Any]) -> bool:
        """Validate that state is compatible with model."""
        pass

class BasicPhysicsModel(PhysicsModelInterface):
    """Basic implementation of physics model."""
    
    def calculate_forces(self, state: Dict[str, Any]) -> np.ndarray:
        # Implementation
        return np.array([0.0, 0.0, 0.0])
        
    def validate_state(self, state: Dict[str, Any]) -> bool:
        return True
```

## Error Handling

### Exception Hierarchy

Define custom exceptions for different error types:

```python
class KPPSimulationError(Exception):
    """Base exception for KPP simulation errors."""
    pass

class PhysicsEngineError(KPPSimulationError):
    """Errors in physics calculations."""
    pass

class ValidationError(KPPSimulationError):
    """Validation failures."""
    pass

class ConfigurationError(KPPSimulationError):
    """Configuration-related errors."""
    pass

# Usage
def calculate_forces(floater: 'Floater') -> float:
    try:
        if floater.volume <= 0:
            raise PhysicsEngineError(f"Invalid floater volume: {floater.volume}")
        return calculate_buoyancy_force(floater)
    except Exception as e:
        raise PhysicsEngineError(f"Force calculation failed: {e}") from e
```

### Error Recovery

Implement graceful error recovery:

```python
class ErrorRecoverySystem:
    def __init__(self):
        self.recovery_strategies = {
            PhysicsEngineError: self._recover_physics_error,
            ValidationError: self._recover_validation_error
        }
        
    def handle_error(self, error: Exception, context: Dict[str, Any]) -> bool:
        """Handle error with appropriate recovery strategy."""
        error_type = type(error)
        if error_type in self.recovery_strategies:
            return self.recovery_strategies[error_type](error, context)
        return False
        
    def _recover_physics_error(self, error: PhysicsEngineError, 
                              context: Dict[str, Any]) -> bool:
        """Recover from physics calculation errors."""
        # Reset to last known good state
        # Reduce time step
        # Use fallback calculations
        return True
```

## Testing Standards

### Unit Test Structure

```python
import unittest
import numpy as np
from unittest.mock import Mock, patch

class TestPhysicsEngine(unittest.TestCase):
    """Test suite for PhysicsEngine class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.params = {
            'time_step': 0.1,
            'rho_water': 1000.0,
            'gravity': 9.81
        }
        self.physics_engine = PhysicsEngine(self.params)
        self.mock_floater = Mock()
        self.mock_floater.volume = 0.1
        self.mock_floater.state = 'light'
        
    def tearDown(self):
        """Clean up after tests."""
        pass
        
    def test_calculate_buoyancy_force_light_floater(self):
        """Test buoyancy calculation for light floater."""
        # Arrange
        expected_force = 1000.0 * 0.1 * 9.81  # ρ * V * g
        
        # Act
        force = self.physics_engine.calculate_buoyancy_force(self.mock_floater)
        
        # Assert
        self.assertAlmostEqual(force, expected_force, places=2)
        
    def test_calculate_buoyancy_force_invalid_volume(self):
        """Test error handling for invalid volume."""
        # Arrange
        self.mock_floater.volume = -0.1
        
        # Act & Assert
        with self.assertRaises(PhysicsEngineError):
            self.physics_engine.calculate_buoyancy_force(self.mock_floater)
            
    @patch('simulation.physics.physics_engine.calculate_drag_force')
    def test_total_force_calculation(self, mock_drag):
        """Test total force calculation with mocked dependencies."""
        # Arrange
        mock_drag.return_value = 50.0
        velocity = 2.0
        
        # Act
        total_force = self.physics_engine.calculate_floater_forces(
            self.mock_floater, velocity
        )
        
        # Assert
        mock_drag.assert_called_once_with(self.mock_floater, velocity)
        self.assertIsInstance(total_force, float)
```

### Integration Test Patterns

```python
class TestPhysicsIntegration(unittest.TestCase):
    """Integration tests for physics system."""
    
    def test_complete_simulation_step(self):
        """Test complete simulation step with all components."""
        # Create real objects (not mocks)
        physics_engine = PhysicsEngine(DEFAULT_PARAMS)
        event_handler = AdvancedEventHandler(tank_depth=10.0)
        validator = ValidationFramework()
        
        # Set up test scenario
        floaters = create_test_floaters(count=4)
        initial_energy = calculate_system_energy(floaters)
        
        # Run simulation steps
        for step in range(100):
            physics_engine.update_chain_dynamics(floaters, 1.0, 100.0, 0.5)
            event_handler.process_events(floaters)
            
        # Validate results
        final_energy = calculate_system_energy(floaters)
        energy_conservation = validator.validate_energy_conservation(
            initial_energy, final_energy, 0.0
        )
        
        self.assertTrue(energy_conservation)
```

### Performance Testing

```python
import time
import cProfile

class TestPerformance(unittest.TestCase):
    """Performance tests for critical components."""
    
    def test_physics_engine_performance(self):
        """Test physics engine performance requirements."""
        physics_engine = PhysicsEngine(DEFAULT_PARAMS)
        floaters = create_test_floaters(count=8)
        
        # Measure performance
        start_time = time.time()
        iterations = 1000
        
        for _ in range(iterations):
            physics_engine.update_chain_dynamics(floaters, 1.0, 100.0, 0.5)
            
        end_time = time.time()
        
        # Calculate FPS
        fps = iterations / (end_time - start_time)
        
        # Assert minimum performance requirements
        self.assertGreater(fps, 10.0, "Physics engine must achieve >10 FPS")
        
    def profile_simulation_step(self):
        """Profile simulation step for optimization."""
        # Use cProfile for detailed performance analysis
        profiler = cProfile.Profile()
        profiler.enable()
        
        # Run simulation
        simulation_engine = SimulationEngine()
        simulation_engine.run_simulation(duration=10.0)
        
        profiler.disable()
        profiler.dump_stats('simulation_profile.prof')
```

## Configuration Management

### Configuration Structure

```python
from dataclasses import dataclass
from typing import Dict, Any
import json

@dataclass
class PhysicsConfig:
    """Configuration for physics engine."""
    time_step: float = 0.1
    rho_water: float = 1000.0
    gravity: float = 9.81
    chain_mass: float = 1000.0
    
@dataclass
class ValidationConfig:
    """Configuration for validation framework."""
    energy_tolerance: float = 0.01
    force_tolerance: float = 1e-6
    stability_threshold: float = 1e-3
    
@dataclass
class SimulationConfig:
    """Main simulation configuration."""
    physics: PhysicsConfig
    validation: ValidationConfig
    monitoring_enabled: bool = True
    logging_level: str = "INFO"
    
    @classmethod
    def from_file(cls, config_path: str) -> 'SimulationConfig':
        """Load configuration from JSON file."""
        with open(config_path, 'r') as f:
            data = json.load(f)
        
        return cls(
            physics=PhysicsConfig(**data['physics']),
            validation=ValidationConfig(**data['validation']),
            monitoring_enabled=data.get('monitoring_enabled', True),
            logging_level=data.get('logging_level', "INFO")
        )
        
    def to_file(self, config_path: str) -> None:
        """Save configuration to JSON file."""
        data = {
            'physics': self.physics.__dict__,
            'validation': self.validation.__dict__,
            'monitoring_enabled': self.monitoring_enabled,
            'logging_level': self.logging_level
        }
        
        with open(config_path, 'w') as f:
            json.dump(data, f, indent=2)
```

## Logging Standards

### Structured Logging

```python
import logging
import json
from datetime import datetime

class StructuredLogger:
    """Structured logger for simulation events."""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self._setup_handlers()
        
    def _setup_handlers(self):
        """Set up log handlers with structured format."""
        handler = logging.StreamHandler()
        formatter = StructuredFormatter()
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
        
    def log_physics_event(self, event_type: str, data: Dict[str, Any]):
        """Log physics-related events."""
        self.logger.info("Physics event", extra={
            'event_type': event_type,
            'component': 'physics_engine',
            'data': data,
            'timestamp': datetime.utcnow().isoformat()
        })
        
    def log_performance_metric(self, metric_name: str, value: float, unit: str):
        """Log performance metrics."""
        self.logger.info("Performance metric", extra={
            'metric_name': metric_name,
            'value': value,
            'unit': unit,
            'component': 'performance_monitor',
            'timestamp': datetime.utcnow().isoformat()
        })

class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured logs."""
    
    def format(self, record):
        log_entry = {
            'level': record.levelname,
            'message': record.getMessage(),
            'timestamp': datetime.utcnow().isoformat(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Add extra fields if present
        if hasattr(record, 'event_type'):
            log_entry['event_type'] = record.event_type
        if hasattr(record, 'component'):
            log_entry['component'] = record.component
        if hasattr(record, 'data'):
            log_entry['data'] = record.data
            
        return json.dumps(log_entry)
```

## Performance Guidelines

### Memory Management

```python
import weakref
from typing import WeakSet

class MemoryEfficientSimulation:
    """Example of memory-efficient simulation design."""
    
    def __init__(self):
        self._floater_references: WeakSet = weakref.WeakSet()
        self._cached_calculations: Dict[str, Any] = {}
        self._max_cache_size = 1000
        
    def add_floater(self, floater: 'Floater'):
        """Add floater with weak reference."""
        self._floater_references.add(floater)
        
    def clear_old_cache_entries(self):
        """Clear old cache entries to prevent memory leaks."""
        if len(self._cached_calculations) > self._max_cache_size:
            # Remove oldest 50% of entries
            items = list(self._cached_calculations.items())
            items_to_keep = items[len(items)//2:]
            self._cached_calculations = dict(items_to_keep)
```

### Optimization Patterns

```python
import numpy as np
from functools import lru_cache

class OptimizedCalculations:
    """Examples of optimization patterns."""
    
    @lru_cache(maxsize=128)
    def calculate_drag_coefficient(self, reynolds_number: float) -> float:
        """Cached drag coefficient calculation."""
        # Expensive calculation cached automatically
        return 0.47 * (1 + 0.15 * reynolds_number**0.687)
        
    def vectorized_force_calculation(self, floaters: List['Floater']) -> np.ndarray:
        """Vectorized calculation for better performance."""
        # Extract properties as arrays
        volumes = np.array([f.volume for f in floaters])
        densities = np.array([f.effective_density for f in floaters])
        
        # Vectorized calculation
        buoyancy_forces = volumes * densities * GRAVITATIONAL_ACCELERATION
        
        return buoyancy_forces
```

## Code Review Checklist

### Pre-Commit Checklist

- [ ] All functions have type hints
- [ ] All public methods have docstrings
- [ ] Unit tests written for new functionality
- [ ] Performance impact assessed
- [ ] Error handling implemented
- [ ] Logging added for important events
- [ ] Configuration externalized
- [ ] Memory usage considered
- [ ] Thread safety addressed if applicable

### Code Review Guidelines

1. **Functionality**: Does the code solve the intended problem correctly?
2. **Design**: Is the code well-structured and maintainable?
3. **Performance**: Are there any performance concerns?
4. **Security**: Are there any security vulnerabilities?
5. **Testing**: Is the code adequately tested?
6. **Documentation**: Is the code properly documented?
7. **Standards**: Does the code follow established standards?

## Maintenance Procedures

### Regular Maintenance Tasks

1. **Weekly**:
   - Review error logs
   - Check performance metrics
   - Update dependencies
   
2. **Monthly**:
   - Run full test suite
   - Review and update documentation
   - Performance profiling
   
3. **Quarterly**:
   - Security audit
   - Dependency vulnerability scan
   - Architecture review

### Debugging Guidelines

```python
import pdb
import traceback

def debug_simulation_step(simulation_engine, debug_mode=False):
    """Example debugging approach."""
    try:
        if debug_mode:
            pdb.set_trace()  # Interactive debugging
            
        result = simulation_engine.run_step()
        
        # Log intermediate values for debugging
        logger.debug("Simulation step completed", extra={
            'chain_velocity': simulation_engine.chain_velocity,
            'total_energy': simulation_engine.total_energy,
            'active_floaters': len(simulation_engine.floaters)
        })
        
        return result
        
    except Exception as e:
        # Detailed error information
        error_info = {
            'error_type': type(e).__name__,
            'error_message': str(e),
            'traceback': traceback.format_exc(),
            'simulation_state': simulation_engine.get_state_dict()
        }
        
        logger.error("Simulation step failed", extra=error_info)
        raise
```

This coding standards document should be followed by all developers working on the KPP simulation system to ensure code quality, maintainability, and consistency.
