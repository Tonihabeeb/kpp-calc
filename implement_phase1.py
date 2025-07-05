#!/usr/bin/env python3
"""
Phase 1 Implementation Script
Creates the modular floater component structure and initial files.
"""

import os
import shutil
from pathlib import Path

def create_directory_structure():
    """Create the new floater package directory structure"""
    print("🔧 Creating Phase 1 directory structure...")
    
    # Define the new structure
    floater_package = Path("simulation/components/floater")
    
    # Create directories
    directories = [
        floater_package,
        floater_package / "tests",
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        print(f"  ✓ Created: {directory}")
    
    return floater_package

def create_init_file(floater_package):
    """Create the floater package __init__.py file"""
    print("\n📦 Creating floater package __init__.py...")
    
    init_content = '''"""
Floater component package.
Provides modular floater physics and control.
"""

from .core import Floater
from .pneumatic import PneumaticSystem, PneumaticState
from .buoyancy import BuoyancyCalculator
from .state_machine import FloaterStateMachine
from .thermal import ThermalModel
from .validation import FloaterValidator

__all__ = [
    'Floater',
    'PneumaticSystem', 
    'PneumaticState',
    'BuoyancyCalculator',
    'FloaterStateMachine',
    'ThermalModel',
    'FloaterValidator'
]
'''
    
    init_file = floater_package / "__init__.py"
    with open(init_file, 'w', encoding='utf-8') as f:
        f.write(init_content)
    
    print(f"  ✓ Created: {init_file}")

def create_pneumatic_module(floater_package):
    """Create the pneumatic system module"""
    print("\n💨 Creating pneumatic system module...")
    
    pneumatic_content = '''"""
Pneumatic system for floater air injection and venting.
Handles air filling, venting, and pressure management.
"""

import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class PneumaticState:
    """Represents the current pneumatic state of a floater"""
    fill_state: str = "empty"  # 'empty', 'filling', 'full', 'venting'
    air_fill_level: float = 0.0  # 0.0 to 1.0
    pneumatic_pressure: float = 101325.0  # Pa
    target_air_volume: float = 0.0  # m³
    injection_start_time: float = 0.0
    total_air_injected: float = 0.0
    injection_complete: bool = False
    air_temperature: float = 293.15  # K
    last_injection_energy: float = 0.0  # J
    thermal_energy_contribution: float = 0.0  # J
    expansion_work_done: float = 0.0  # J
    venting_energy_loss: float = 0.0  # J

class PneumaticSystem:
    """Handles pneumatic operations for a single floater"""
    
    def __init__(self, 
                 air_fill_time: float = 0.5,
                 air_pressure: float = 300000,
                 air_flow_rate: float = 0.6,
                 jet_efficiency: float = 0.85):
        self.air_fill_time = air_fill_time
        self.air_pressure = air_pressure
        self.air_flow_rate = air_flow_rate
        self.jet_efficiency = jet_efficiency
        self.state = PneumaticState()
    
    def start_injection(self, target_volume: float, injection_pressure: float, 
                       current_time: float) -> bool:
        """Start air injection process"""
        if self.state.fill_state != "empty":
            logger.warning("Cannot start injection: floater not empty")
            return False
        
        self.state.fill_state = "filling"
        self.state.target_air_volume = target_volume
        self.state.pneumatic_pressure = injection_pressure
        self.state.injection_start_time = current_time
        self.state.total_air_injected = 0.0
        self.state.injection_complete = False
        
        logger.info(f"Started air injection: target={target_volume:.3f}m³")
        return True
    
    def update_injection(self, injected_volume: float, dt: float) -> None:
        """Update injection progress"""
        if self.state.fill_state != "filling":
            return
        
        self.state.total_air_injected += injected_volume
        self.state.air_fill_level = min(1.0, 
            self.state.total_air_injected / self.state.target_air_volume)
        
        # Check if injection is complete
        if self.state.air_fill_level >= 1.0:
            self.complete_injection()
    
    def complete_injection(self) -> None:
        """Complete the injection process"""
        self.state.fill_state = "full"
        self.state.injection_complete = True
        self.state.air_fill_level = 1.0
        logger.info("Air injection completed")
    
    def start_venting(self, current_time: float) -> bool:
        """Start air venting process"""
        if self.state.fill_state != "full":
            logger.warning("Cannot start venting: floater not full")
            return False
        
        self.state.fill_state = "venting"
        logger.info("Started air venting")
        return True
    
    def update_venting(self, venting_rate: float, dt: float) -> bool:
        """Update venting progress"""
        if self.state.fill_state != "venting":
            return False
        
        # Reduce air fill level
        air_volume_lost = venting_rate * dt
        self.state.air_fill_level = max(0.0, 
            self.state.air_fill_level - air_volume_lost)
        
        # Check if venting is complete
        if self.state.air_fill_level <= 0.0:
            self.complete_venting()
            return True
        
        return False
    
    def complete_venting(self) -> None:
        """Complete the venting process"""
        self.state.fill_state = "empty"
        self.state.air_fill_level = 0.0
        self.state.total_air_injected = 0.0
        logger.info("Air venting completed")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current pneumatic status"""
        return {
            "fill_state": self.state.fill_state,
            "air_fill_level": self.state.air_fill_level,
            "pneumatic_pressure": self.state.pneumatic_pressure,
            "target_air_volume": self.state.target_air_volume,
            "total_air_injected": self.state.total_air_injected,
            "injection_complete": self.state.injection_complete,
            "air_temperature": self.state.air_temperature,
            "last_injection_energy": self.state.last_injection_energy,
            "thermal_energy_contribution": self.state.thermal_energy_contribution,
            "expansion_work_done": self.state.expansion_work_done,
            "venting_energy_loss": self.state.venting_energy_loss
        }
'''
    
    pneumatic_file = floater_package / "pneumatic.py"
    with open(pneumatic_file, 'w', encoding='utf-8') as f:
        f.write(pneumatic_content)
    
    print(f"  ✓ Created: {pneumatic_file}")

def create_buoyancy_module(floater_package):
    """Create the buoyancy calculations module"""
    print("\n🌊 Creating buoyancy calculations module...")
    
    buoyancy_content = '''"""
Buoyancy calculations for floater physics.
Handles buoyant force, pressure effects, and density calculations.
"""

import math
import logging
from typing import Optional
from dataclasses import dataclass

from config.config import RHO_WATER, RHO_AIR, G

logger = logging.getLogger(__name__)

@dataclass
class BuoyancyResult:
    """Result of buoyancy calculation"""
    buoyant_force: float
    displaced_volume: float
    effective_density: float
    pressure_effect: float
    thermal_effect: float

class BuoyancyCalculator:
    """Calculates buoyant forces and related physics"""
    
    def __init__(self, tank_height: float = 10.0):
        self.tank_height = tank_height
    
    def calculate_basic_buoyancy(self, volume: float, depth: float) -> float:
        """Calculate basic buoyant force (Archimedes' principle)"""
        return RHO_WATER * G * volume
    
    def calculate_enhanced_buoyancy(self, 
                                  volume: float, 
                                  depth: float,
                                  air_fill_level: float,
                                  air_pressure: float,
                                  water_temperature: float = 293.15) -> BuoyancyResult:
        """Calculate enhanced buoyancy with pressure and thermal effects"""
        
        # Basic buoyant force
        basic_force = self.calculate_basic_buoyancy(volume, depth)
        
        # Pressure effect on air volume
        pressure_effect = self._calculate_pressure_effect(
            volume, depth, air_fill_level, air_pressure)
        
        # Thermal effect on air expansion
        thermal_effect = self._calculate_thermal_effect(
            volume, air_fill_level, water_temperature)
        
        # Effective displaced volume
        air_volume = volume * air_fill_level
        water_volume = volume * (1 - air_fill_level)
        displaced_volume = water_volume + (air_volume * pressure_effect)
        
        # Total buoyant force
        total_force = basic_force + pressure_effect + thermal_effect
        
        # Effective density
        effective_density = (RHO_WATER * water_volume + 
                           RHO_AIR * air_volume) / volume
        
        return BuoyancyResult(
            buoyant_force=total_force,
            displaced_volume=displaced_volume,
            effective_density=effective_density,
            pressure_effect=pressure_effect,
            thermal_effect=thermal_effect
        )
    
    def _calculate_pressure_effect(self, volume: float, depth: float,
                                 air_fill_level: float, air_pressure: float) -> float:
        """Calculate pressure effect on buoyancy"""
        # Pressure increases with depth
        water_pressure = 101325 + RHO_WATER * G * depth
        
        # Air volume changes with pressure (Boyle's law)
        if air_pressure > 0:
            pressure_ratio = water_pressure / air_pressure
            compressed_air_volume = volume * air_fill_level / pressure_ratio
            pressure_effect = RHO_WATER * G * compressed_air_volume
        else:
            pressure_effect = 0.0
        
        return pressure_effect
    
    def _calculate_thermal_effect(self, volume: float, air_fill_level: float,
                                water_temperature: float) -> float:
        """Calculate thermal effect on buoyancy"""
        # Air expands with temperature (Charles's law)
        reference_temp = 293.15  # 20°C
        if water_temperature > reference_temp:
            temp_ratio = water_temperature / reference_temp
            expanded_air_volume = volume * air_fill_level * temp_ratio
            thermal_effect = RHO_WATER * G * expanded_air_volume
        else:
            thermal_effect = 0.0
        
        return thermal_effect
'''
    
    buoyancy_file = floater_package / "buoyancy.py"
    with open(buoyancy_file, 'w', encoding='utf-8') as f:
        f.write(buoyancy_content)
    
    print(f"  ✓ Created: {buoyancy_file}")

def create_state_machine_module(floater_package):
    """Create the state machine module"""
    print("\n🔄 Creating state machine module...")
    
    state_machine_content = '''"""
State machine for floater operation cycles.
Manages transitions between empty, filling, full, and venting states.
"""

import logging
from enum import Enum
from typing import Optional, Callable
from dataclasses import dataclass

logger = logging.getLogger(__name__)

class FloaterState(Enum):
    """Floater operational states"""
    EMPTY = "empty"
    FILLING = "filling"
    FULL = "full"
    VENTING = "venting"
    TRANSITION = "transition"

@dataclass
class StateTransition:
    """Represents a state transition"""
    from_state: FloaterState
    to_state: FloaterState
    condition: Callable
    action: Optional[Callable] = None

class FloaterStateMachine:
    """Manages floater state transitions"""
    
    def __init__(self):
        self.current_state = FloaterState.EMPTY
        self.transitions = self._define_transitions()
        self.state_history = []
    
    def _define_transitions(self) -> list[StateTransition]:
        """Define all possible state transitions"""
        return [
            StateTransition(
                FloaterState.EMPTY,
                FloaterState.FILLING,
                lambda context: context.get('injection_requested', False),
                self._on_start_filling
            ),
            StateTransition(
                FloaterState.FILLING,
                FloaterState.FULL,
                lambda context: context.get('injection_complete', False),
                self._on_filling_complete
            ),
            StateTransition(
                FloaterState.FULL,
                FloaterState.VENTING,
                lambda context: context.get('venting_requested', False),
                self._on_start_venting
            ),
            StateTransition(
                FloaterState.VENTING,
                FloaterState.EMPTY,
                lambda context: context.get('venting_complete', False),
                self._on_venting_complete
            )
        ]
    
    def update(self, context: dict) -> FloaterState:
        """Update state machine based on current context"""
        old_state = self.current_state
        
        # Check for valid transitions
        for transition in self.transitions:
            if (transition.from_state == self.current_state and 
                transition.condition(context)):
                
                # Execute transition
                if transition.action:
                    transition.action(context)
                
                self.current_state = transition.to_state
                self.state_history.append({
                    'from_state': old_state,
                    'to_state': self.current_state,
                    'timestamp': context.get('time', 0.0)
                })
                
                logger.info(f"Floater state transition: {old_state} -> {self.current_state}")
                break
        
        return self.current_state
    
    def _on_start_filling(self, context: dict) -> None:
        """Action when starting to fill"""
        logger.debug("Starting air injection")
    
    def _on_filling_complete(self, context: dict) -> None:
        """Action when filling is complete"""
        logger.debug("Air injection completed")
    
    def _on_start_venting(self, context: dict) -> None:
        """Action when starting to vent"""
        logger.debug("Starting air venting")
    
    def _on_venting_complete(self, context: dict) -> None:
        """Action when venting is complete"""
        logger.debug("Air venting completed")
    
    def get_state_info(self) -> dict:
        """Get current state information"""
        return {
            'current_state': self.current_state.value,
            'state_history': self.state_history[-10:],  # Last 10 transitions
            'total_transitions': len(self.state_history)
        }
'''
    
    state_machine_file = floater_package / "state_machine.py"
    with open(state_machine_file, 'w', encoding='utf-8') as f:
        f.write(state_machine_content)
    
    print(f"  ✓ Created: {state_machine_file}")

def create_thermal_module(floater_package):
    """Create the thermal effects module"""
    print("\n🌡️ Creating thermal effects module...")
    
    thermal_content = '''"""
Thermal effects on floater physics.
Handles heat transfer, temperature effects, and thermal expansion.
"""

import logging
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)

@dataclass
class ThermalState:
    """Thermal state of a floater"""
    air_temperature: float = 293.15  # K
    water_temperature: float = 293.15  # K
    surface_area_air_water: float = 0.0  # m²
    heat_transfer_coefficient: float = 150.0  # W/m²K
    thermal_energy_contribution: float = 0.0  # J
    expansion_work_done: float = 0.0  # J

class ThermalModel:
    """Models thermal effects on floater physics"""
    
    def __init__(self, 
                 heat_transfer_coefficient: float = 150.0,
                 specific_heat_air: float = 1005.0,  # J/kg·K
                 specific_heat_water: float = 4186.0):  # J/kg·K
        self.heat_transfer_coefficient = heat_transfer_coefficient
        self.specific_heat_air = specific_heat_air
        self.specific_heat_water = specific_heat_water
    
    def calculate_heat_transfer(self, 
                              air_volume: float,
                              water_volume: float,
                              air_temp: float,
                              water_temp: float,
                              surface_area: float,
                              dt: float) -> float:
        """Calculate heat transfer between air and water"""
        if surface_area <= 0 or abs(air_temp - water_temp) < 0.1:
            return 0.0
        
        # Heat transfer rate (W)
        heat_rate = (self.heat_transfer_coefficient * 
                    surface_area * 
                    (water_temp - air_temp))
        
        # Heat energy transferred (J)
        heat_energy = heat_rate * dt
        
        return heat_energy
    
    def update_temperatures(self, 
                           thermal_state: ThermalState,
                           heat_energy: float,
                           air_mass: float,
                           water_mass: float,
                           dt: float) -> ThermalState:
        """Update temperatures based on heat transfer"""
        if air_mass <= 0 or water_mass <= 0:
            return thermal_state
        
        # Temperature changes
        air_temp_change = heat_energy / (air_mass * self.specific_heat_air)
        water_temp_change = -heat_energy / (water_mass * self.specific_heat_water)
        
        # Update temperatures
        new_air_temp = thermal_state.air_temperature + air_temp_change
        new_water_temp = thermal_state.water_temperature + water_temp_change
        
        # Update thermal state
        thermal_state.air_temperature = new_air_temp
        thermal_state.water_temperature = new_water_temp
        thermal_state.thermal_energy_contribution = heat_energy
        
        return thermal_state
    
    def calculate_thermal_expansion(self, 
                                  volume: float,
                                  temperature: float,
                                  reference_temp: float = 293.15) -> float:
        """Calculate thermal expansion of air volume"""
        # Thermal expansion coefficient for air (1/K)
        alpha_air = 3.67e-3
        
        if temperature > reference_temp:
            expansion_ratio = 1 + alpha_air * (temperature - reference_temp)
            expanded_volume = volume * expansion_ratio
            return expanded_volume - volume
        else:
            return 0.0
    
    def calculate_expansion_work(self, 
                               pressure: float,
                               volume_change: float) -> float:
        """Calculate work done by thermal expansion"""
        # Work = P * ΔV
        return pressure * volume_change
'''
    
    thermal_file = floater_package / "thermal.py"
    with open(thermal_file, 'w', encoding='utf-8') as f:
        f.write(thermal_content)
    
    print(f"  ✓ Created: {thermal_file}")

def create_validation_module(floater_package):
    """Create the validation module"""
    print("\n✅ Creating validation module...")
    
    validation_content = '''"""
Validation for floater parameters and state.
Ensures physical constraints and operational limits.
"""

import logging
from typing import Dict, Any, List, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ValidationResult:
    """Result of parameter validation"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    corrected_values: Dict[str, Any]

class FloaterValidator:
    """Validates floater parameters and state"""
    
    def __init__(self):
        self.constraints = self._define_constraints()
    
    def _define_constraints(self) -> Dict[str, Dict[str, Any]]:
        """Define physical and operational constraints"""
        return {
            'volume': {
                'min': 0.01,  # m³
                'max': 10.0,  # m³
                'description': 'Floater volume'
            },
            'mass': {
                'min': 0.1,   # kg
                'max': 1000.0, # kg
                'description': 'Floater mass'
            },
            'drag_coefficient': {
                'min': 0.0,
                'max': 2.0,
                'description': 'Drag coefficient'
            },
            'position': {
                'min': 0.0,   # m
                'max': 25.0,  # m
                'description': 'Vertical position'
            },
            'velocity': {
                'min': -10.0, # m/s
                'max': 10.0,  # m/s
                'description': 'Vertical velocity'
            },
            'air_pressure': {
                'min': 50000,  # Pa
                'max': 1000000, # Pa
                'description': 'Air pressure'
            }
        }
    
    def validate_parameters(self, params: Dict[str, Any]) -> ValidationResult:
        """Validate floater parameters"""
        errors = []
        warnings = []
        corrected_values = {}
        
        for param_name, value in params.items():
            if param_name in self.constraints:
                constraint = self.constraints[param_name]
                
                # Check minimum value
                if value < constraint['min']:
                    errors.append(
                        f"{constraint['description']} ({param_name}) "
                        f"must be >= {constraint['min']}, got {value}"
                    )
                    corrected_values[param_name] = constraint['min']
                
                # Check maximum value
                elif value > constraint['max']:
                    errors.append(
                        f"{constraint['description']} ({param_name}) "
                        f"must be <= {constraint['max']}, got {value}"
                    )
                    corrected_values[param_name] = constraint['max']
        
        # Cross-parameter validation
        cross_validation_result = self._validate_cross_parameters(params)
        errors.extend(cross_validation_result['errors'])
        warnings.extend(cross_validation_result['warnings'])
        
        is_valid = len(errors) == 0
        
        return ValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            corrected_values=corrected_values
        )
    
    def _validate_cross_parameters(self, params: Dict[str, Any]) -> Dict[str, List[str]]:
        """Validate relationships between parameters"""
        errors = []
        warnings = []
        
        # Check density constraint
        if 'volume' in params and 'mass' in params:
            volume = params['volume']
            mass = params['mass']
            
            if volume > 0:
                density = mass / volume
                if density > 1000:  # Water density
                    errors.append(
                        f"Floater density ({density:.1f} kg/m³) "
                        f"exceeds water density (1000 kg/m³)"
                    )
                elif density > 800:
                    warnings.append(
                        f"High floater density ({density:.1f} kg/m³) "
                        f"may affect buoyancy"
                    )
        
        # Check position within tank height
        if 'position' in params and 'tank_height' in params:
            position = params['position']
            tank_height = params['tank_height']
            
            if position > tank_height:
                errors.append(
                    f"Position ({position}m) exceeds tank height ({tank_height}m)"
                )
        
        return {'errors': errors, 'warnings': warnings}
    
    def validate_state(self, state: Dict[str, Any]) -> ValidationResult:
        """Validate floater state"""
        errors = []
        warnings = []
        corrected_values = {}
        
        # Check air fill level
        air_fill_level = state.get('air_fill_level', 0.0)
        if not 0.0 <= air_fill_level <= 1.0:
            errors.append(f"Air fill level must be 0-1, got {air_fill_level}")
            corrected_values['air_fill_level'] = max(0.0, min(1.0, air_fill_level))
        
        # Check velocity limits
        velocity = state.get('velocity', 0.0)
        if abs(velocity) > 10.0:
            warnings.append(f"High velocity detected: {velocity} m/s")
        
        # Check position bounds
        position = state.get('position', 0.0)
        if position < 0.0:
            errors.append(f"Position cannot be negative: {position}")
            corrected_values['position'] = 0.0
        
        is_valid = len(errors) == 0
        
        return ValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            corrected_values=corrected_values
        )
'''
    
    validation_file = floater_package / "validation.py"
    with open(validation_file, 'w', encoding='utf-8') as f:
        f.write(validation_content)
    
    print(f"  ✓ Created: {validation_file}")

def create_core_module(floater_package):
    """Create the core floater module"""
    print("\n🎯 Creating core floater module...")
    
    core_content = '''"""
Core floater physics and control.
Coordinates all floater subsystems and provides unified interface.
"""

import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass

from .pneumatic import PneumaticSystem, PneumaticState
from .buoyancy import BuoyancyCalculator, BuoyancyResult
from .state_machine import FloaterStateMachine, FloaterState
from .thermal import ThermalModel, ThermalState
from .validation import FloaterValidator, ValidationResult

logger = logging.getLogger(__name__)

@dataclass
class FloaterConfig:
    """Configuration for a floater"""
    volume: float
    mass: float
    area: float = 0.1
    drag_coefficient: float = 0.8
    air_fill_time: float = 0.5
    air_pressure: float = 300000
    air_flow_rate: float = 0.6
    jet_efficiency: float = 0.85
    tank_height: float = 10.0

class Floater:
    """
    Refactored floater with modular subsystems.
    Coordinates pneumatic, buoyancy, thermal, and state machine components.
    """
    
    def __init__(self, config: FloaterConfig):
        # Validate configuration
        self.validator = FloaterValidator()
        validation_result = self.validator.validate_parameters(config.__dict__)
        
        if not validation_result.is_valid:
            raise ValueError(f"Invalid floater configuration: {validation_result.errors}")
        
        if validation_result.warnings:
            for warning in validation_result.warnings:
                logger.warning(warning)
        
        # Store configuration
        self.config = config
        
        # Initialize subsystems
        self.pneumatic = PneumaticSystem(
            air_fill_time=config.air_fill_time,
            air_pressure=config.air_pressure,
            air_flow_rate=config.air_flow_rate,
            jet_efficiency=config.jet_efficiency
        )
        
        self.buoyancy_calculator = BuoyancyCalculator(tank_height=config.tank_height)
        self.state_machine = FloaterStateMachine()
        self.thermal_model = ThermalModel()
        
        # State variables
        self.position = 0.0
        self.velocity = 0.0
        self.thermal_state = ThermalState()
        
        # Performance tracking
        self.drag_loss = 0.0
        self.dissolution_loss = 0.0
        self.venting_loss = 0.0
        
        logger.info(f"Floater initialized with volume={config.volume}m³, mass={config.mass}kg")
    
    def update(self, dt: float, fluid_system=None) -> None:
        """Update floater physics and state"""
        # Update state machine
        context = self._build_context()
        self.state_machine.update(context)
        
        # Update pneumatic system
        self._update_pneumatic(dt)
        
        # Calculate forces
        buoyancy_result = self._calculate_buoyancy()
        drag_force = self._calculate_drag(fluid_system)
        
        # Apply forces
        net_force = buoyancy_result.buoyant_force - drag_force - self.config.mass * 9.81
        
        # Update motion
        acceleration = net_force / self.config.mass
        self.velocity += acceleration * dt
        self.position += self.velocity * dt
        
        # Apply constraints
        self._apply_constraints()
        
        # Update thermal effects
        self._update_thermal(dt)
        
        # Validate state
        self._validate_state()
    
    def _build_context(self) -> Dict[str, Any]:
        """Build context for state machine"""
        return {
            'injection_requested': self.pneumatic.state.fill_state == "empty",
            'injection_complete': self.pneumatic.state.injection_complete,
            'venting_requested': self.pneumatic.state.fill_state == "full",
            'venting_complete': self.pneumatic.state.fill_state == "empty",
            'time': 0.0  # TODO: Get from simulation time
        }
    
    def _update_pneumatic(self, dt: float) -> None:
        """Update pneumatic system"""
        # This would integrate with the pneumatic control system
        pass
    
    def _calculate_buoyancy(self) -> BuoyancyResult:
        """Calculate buoyant force"""
        depth = self.config.tank_height - self.position
        return self.buoyancy_calculator.calculate_enhanced_buoyancy(
            volume=self.config.volume,
            depth=depth,
            air_fill_level=self.pneumatic.state.air_fill_level,
            air_pressure=self.pneumatic.state.pneumatic_pressure,
            water_temperature=self.thermal_state.water_temperature
        )
    
    def _calculate_drag(self, fluid_system=None) -> float:
        """Calculate drag force"""
        # Simplified drag calculation
        velocity_magnitude = abs(self.velocity)
        drag_force = (0.5 * 1000 * velocity_magnitude**2 * 
                     self.config.area * self.config.drag_coefficient)
        
        # Update drag loss
        self.drag_loss = drag_force * velocity_magnitude * 0.1  # dt approximation
        
        return drag_force
    
    def _apply_constraints(self) -> None:
        """Apply physical constraints"""
        # Position constraints
        self.position = max(0.0, min(self.config.tank_height, self.position))
        
        # Velocity constraints
        max_velocity = 10.0
        self.velocity = max(-max_velocity, min(max_velocity, self.velocity))
        
        # Stop at boundaries
        if self.position <= 0.0 and self.velocity < 0:
            self.velocity = 0.0
        elif self.position >= self.config.tank_height and self.velocity > 0:
            self.velocity = 0.0
    
    def _update_thermal(self, dt: float) -> None:
        """Update thermal effects"""
        # Calculate heat transfer
        air_volume = self.config.volume * self.pneumatic.state.air_fill_level
        water_volume = self.config.volume * (1 - self.pneumatic.state.air_fill_level)
        
        heat_energy = self.thermal_model.calculate_heat_transfer(
            air_volume=air_volume,
            water_volume=water_volume,
            air_temp=self.thermal_state.air_temperature,
            water_temp=self.thermal_state.water_temperature,
            surface_area=self.thermal_state.surface_area_air_water,
            dt=dt
        )
        
        # Update thermal state
        air_mass = air_volume * 1.225  # Air density
        water_mass = water_volume * 1000  # Water density
        
        self.thermal_state = self.thermal_model.update_temperatures(
            self.thermal_state, heat_energy, air_mass, water_mass, dt
        )
    
    def _validate_state(self) -> None:
        """Validate current state"""
        state = {
            'position': self.position,
            'velocity': self.velocity,
            'air_fill_level': self.pneumatic.state.air_fill_level
        }
        
        validation_result = self.validator.validate_state(state)
        
        if not validation_result.is_valid:
            logger.error(f"Invalid floater state: {validation_result.errors}")
        
        if validation_result.warnings:
            for warning in validation_result.warnings:
                logger.warning(warning)
    
    def get_force(self) -> float:
        """Get total vertical force"""
        buoyancy_result = self._calculate_buoyancy()
        drag_force = self._calculate_drag()
        weight = self.config.mass * 9.81
        
        return buoyancy_result.buoyant_force - drag_force - weight
    
    def get_status(self) -> Dict[str, Any]:
        """Get comprehensive floater status"""
        return {
            'position': self.position,
            'velocity': self.velocity,
            'state': self.state_machine.current_state.value,
            'pneumatic': self.pneumatic.get_status(),
            'thermal': {
                'air_temperature': self.thermal_state.air_temperature,
                'water_temperature': self.thermal_state.water_temperature,
                'thermal_energy': self.thermal_state.thermal_energy_contribution
            },
            'losses': {
                'drag_loss': self.drag_loss,
                'dissolution_loss': self.dissolution_loss,
                'venting_loss': self.venting_loss
            },
            'state_machine': self.state_machine.get_state_info()
        }
    
    def reset(self) -> None:
        """Reset floater to initial state"""
        self.position = 0.0
        self.velocity = 0.0
        self.pneumatic.state = PneumaticState()
        self.thermal_state = ThermalState()
        self.state_machine.current_state = FloaterState.EMPTY
        self.drag_loss = 0.0
        self.dissolution_loss = 0.0
        self.venting_loss = 0.0
'''
    
    core_file = floater_package / "core.py"
    with open(core_file, 'w', encoding='utf-8') as f:
        f.write(core_content)
    
    print(f"  ✓ Created: {core_file}")

def create_test_files(floater_package):
    """Create basic test files"""
    print("\n🧪 Creating test files...")
    
    # Create test directory
    test_dir = floater_package / "tests"
    test_dir.mkdir(exist_ok=True)
    
    # Create __init__.py for tests
    test_init = test_dir / "__init__.py"
    test_init.touch()
    
    # Create basic test file
    test_file = test_dir / "test_pneumatic.py"
    test_content = '''"""
Basic tests for pneumatic system.
"""

import pytest
from ..pneumatic import PneumaticSystem, PneumaticState

class TestPneumaticSystem:
    def test_initialization(self):
        """Test pneumatic system initialization"""
        pneumatic = PneumaticSystem()
        assert pneumatic.state.fill_state == "empty"
        assert pneumatic.state.air_fill_level == 0.0
    
    def test_start_injection(self):
        """Test starting air injection"""
        pneumatic = PneumaticSystem()
        success = pneumatic.start_injection(0.5, 300000, 0.0)
        assert success is True
        assert pneumatic.state.fill_state == "filling"
        assert pneumatic.state.target_air_volume == 0.5
'''
    
    with open(test_file, 'w', encoding='utf-8') as f:
        f.write(test_content)
    
    print(f"  ✓ Created: {test_file}")

def create_backup_original():
    """Create backup of original floater.py"""
    print("\n💾 Creating backup of original floater.py...")
    
    original_file = Path("simulation/components/floater.py")
    backup_file = Path("simulation/components/floater_original_backup.py")
    
    if original_file.exists():
        shutil.copy2(original_file, backup_file)
        print(f"  ✓ Backup created: {backup_file}")
    else:
        print("  ⚠️ Original floater.py not found, skipping backup")

def main():
    """Main implementation function"""
    print("🚀 Starting Phase 1 Implementation")
    print("=" * 50)
    
    try:
        # Create directory structure
        floater_package = create_directory_structure()
        
        # Create backup
        create_backup_original()
        
        # Create all modules
        create_init_file(floater_package)
        create_pneumatic_module(floater_package)
        create_buoyancy_module(floater_package)
        create_state_machine_module(floater_package)
        create_thermal_module(floater_package)
        create_validation_module(floater_package)
        create_core_module(floater_package)
        
        # Create test files
        create_test_files(floater_package)
        
        print("\n" + "=" * 50)
        print("✅ Phase 1 Implementation Complete!")
        print("\n📁 New Structure Created:")
        print("  simulation/components/floater/")
        print("  ├── __init__.py")
        print("  ├── core.py")
        print("  ├── pneumatic.py")
        print("  ├── buoyancy.py")
        print("  ├── state_machine.py")
        print("  ├── thermal.py")
        print("  ├── validation.py")
        print("  └── tests/")
        print("      └── test_pneumatic.py")
        
        print("\n🔄 Next Steps:")
        print("  1. Test the new modules: python -m pytest simulation/components/floater/tests/")
        print("  2. Update engine.py to use new Floater class")
        print("  3. Run integration tests to ensure compatibility")
        print("  4. Begin Phase 2: Configuration Management")
        
    except Exception as e:
        print(f"\n❌ Implementation failed: {e}")
        raise

if __name__ == "__main__":
    main() 