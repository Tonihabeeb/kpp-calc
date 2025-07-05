"""
Core floater physics and control.
Coordinates all floater subsystems and provides unified interface.
"""

import logging
from typing import Dict, Any, Optional, Union
from dataclasses import dataclass

from .pneumatic import PneumaticSystem, PneumaticState
from .buoyancy import BuoyancyCalculator, BuoyancyResult
from .state_machine import FloaterStateMachine, FloaterState
from .thermal import ThermalModel, ThermalState
from .validation import FloaterValidator, ValidationResult

# PHASE 2: Import new configuration system
try:
    from config.components.floater_config import FloaterConfig as NewFloaterConfig
    NEW_CONFIG_AVAILABLE = True
except ImportError:
    NEW_CONFIG_AVAILABLE = False
    NewFloaterConfig = None

logger = logging.getLogger(__name__)

@dataclass
class LegacyFloaterConfig:
    """Legacy configuration for a floater (backward compatibility)"""
    volume: float
    mass: float
    area: float = 0.1
    drag_coefficient: float = 0.8
    air_fill_time: float = 0.5
    air_pressure: float = 300000
    air_flow_rate: float = 0.6
    jet_efficiency: float = 0.85
    tank_height: float = 10.0

# Type alias for backward compatibility
FloaterConfig = Union[NewFloaterConfig, LegacyFloaterConfig] if NEW_CONFIG_AVAILABLE else LegacyFloaterConfig

class Floater:
    """
    Refactored floater with modular subsystems.
    Coordinates pneumatic, buoyancy, thermal, and state machine components.
    """
    
    def __init__(self, config: FloaterConfig):
        # PHASE 2: Handle both new and legacy configuration formats
        self.using_new_config = NEW_CONFIG_AVAILABLE and isinstance(config, NewFloaterConfig)
        
        if self.using_new_config:
            logger.info("Using new configuration system for floater")
            # New config system provides validation automatically
            self.config = config
            config_dict = config.to_dict()
        else:
            logger.info("Using legacy configuration system for floater")
            # Validate legacy configuration
            self.validator = FloaterValidator()
            validation_result = self.validator.validate_parameters(config.__dict__)
            
            if not validation_result.is_valid:
                raise ValueError(f"Invalid floater configuration: {validation_result.errors}")
            
            if validation_result.warnings:
                for warning in validation_result.warnings:
                    logger.warning(warning)
            
            self.config = config
            config_dict = config.__dict__
        
        # Initialize subsystems with configuration values
        self.pneumatic = PneumaticSystem(
            air_fill_time=config_dict.get('air_fill_time', 0.5),
            air_pressure=config_dict.get('air_pressure', 300000),
            air_flow_rate=config_dict.get('air_flow_rate', 0.6),
            jet_efficiency=config_dict.get('jet_efficiency', 0.85)
        )
        
        self.buoyancy_calculator = BuoyancyCalculator(
            tank_height=config_dict.get('tank_height', 10.0)
        )
        self.state_machine = FloaterStateMachine()
        
        # Initialize thermal model with config values if available
        thermal_props = config_dict.get('thermal_properties', {}) if self.using_new_config else {}
        self.thermal_model = ThermalModel(
            heat_transfer_coefficient=thermal_props.get('heat_transfer_coefficient', 150.0),
            specific_heat_air=thermal_props.get('specific_heat_air', 1005.0),
            specific_heat_water=thermal_props.get('specific_heat_water', 4186.0)
        )
        
        # State variables
        self.position = 0.0
        self.velocity = 0.0
        self.thermal_state = ThermalState()
        
        # Performance tracking
        self.drag_loss = 0.0
        self.dissolution_loss = 0.0
        self.venting_loss = 0.0
        
        logger.info(f"Floater initialized with volume={config_dict.get('volume', 0.4)}m³, mass={config_dict.get('mass', 16.0)}kg")
    
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
        # Get configuration values safely
        tank_height = self.config.tank_height if hasattr(self.config, 'tank_height') else 10.0
        volume = self.config.volume if hasattr(self.config, 'volume') else 0.4
        
        depth = tank_height - self.position
        return self.buoyancy_calculator.calculate_enhanced_buoyancy(
            volume=volume,
            depth=depth,
            air_fill_level=self.pneumatic.state.air_fill_level,
            air_pressure=self.pneumatic.state.pneumatic_pressure,
            water_temperature=self.thermal_state.water_temperature
        )
    
    def _calculate_drag(self, fluid_system=None) -> float:
        """Calculate drag force"""
        # Get configuration values safely
        area = self.config.area if hasattr(self.config, 'area') else 0.1
        drag_coefficient = self.config.drag_coefficient if hasattr(self.config, 'drag_coefficient') else 0.8
        
        # Simplified drag calculation
        velocity_magnitude = abs(self.velocity)
        drag_force = (0.5 * 1000 * velocity_magnitude**2 * 
                     area * drag_coefficient)
        
        # Update drag loss
        self.drag_loss = drag_force * velocity_magnitude * 0.1  # dt approximation
        
        return drag_force
    
    def _apply_constraints(self) -> None:
        """Apply physical constraints"""
        # Get configuration values safely
        tank_height = self.config.tank_height if hasattr(self.config, 'tank_height') else 10.0
        max_velocity = getattr(self.config, 'max_velocity', 10.0) if hasattr(self.config, 'max_velocity') else 10.0
        
        # Position constraints
        self.position = max(0.0, min(tank_height, self.position))
        
        # Velocity constraints
        self.velocity = max(-max_velocity, min(max_velocity, self.velocity))
        
        # Stop at boundaries
        if self.position <= 0.0 and self.velocity < 0:
            self.velocity = 0.0
        elif self.position >= tank_height and self.velocity > 0:
            self.velocity = 0.0
    
    def _update_thermal(self, dt: float) -> None:
        """Update thermal effects"""
        # Get configuration values safely
        volume = self.config.volume if hasattr(self.config, 'volume') else 0.4
        
        # Calculate heat transfer
        air_volume = volume * self.pneumatic.state.air_fill_level
        water_volume = volume * (1 - self.pneumatic.state.air_fill_level)
        
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
        # Only validate if using legacy config (new config has built-in validation)
        if not self.using_new_config and hasattr(self, 'validator'):
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
        # Get configuration values safely
        mass = self.config.mass if hasattr(self.config, 'mass') else 16.0
        
        buoyancy_result = self._calculate_buoyancy()
        drag_force = self._calculate_drag()
        weight = mass * 9.81
        
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
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert floater state to dictionary (backward compatibility)"""
        return {
            'position': self.position,
            'velocity': self.velocity,
            'is_filled': self.is_filled,
            'fill_progress': self.fill_progress,
            'state': self.state,
            'volume': self.volume,
            'mass': self.mass,
            'area': self.area,
            'buoyant_force': self.compute_buoyant_force(),
            'jet_force': self.compute_pulse_jet_force(),
            'drag_loss': self.drag_loss,
            'dissolution_loss': self.dissolution_loss,
            'venting_loss': self.venting_loss
        }
    
    def reset(self) -> None:
        """Reset floater to initial state"""
        self.position = 0.0
        self.velocity = 0.0
        self.thermal_state = ThermalState()
        self.pneumatic.reset()
        self.state_machine.reset()
        
        # Reset performance tracking
        self.drag_loss = 0.0
        self.dissolution_loss = 0.0
        self.venting_loss = 0.0
    
    def set_chain_params(self, major_axis: float, minor_axis: float, chain_radius: float) -> None:
        """Set chain geometry parameters (backward compatibility)"""
        self.chain_major_axis = major_axis
        self.chain_minor_axis = minor_axis
        self.chain_radius = chain_radius
    
    def set_theta(self, theta: float) -> None:
        """Set angular position (for chain integration)"""
        # This would be used for chain-driven motion
        pass
    
    # === BACKWARD COMPATIBILITY METHODS ===
    
    def start_filling(self) -> None:
        """Start filling the floater with air (backward compatibility)"""
        if hasattr(self.pneumatic, 'start_filling'):
            self.pneumatic.start_filling()
        else:
            # Legacy compatibility - set fill state
            self.pneumatic.state.fill_state = "filling"
            logger.debug("Started filling floater (legacy mode)")
    
    def compute_buoyant_force(self) -> float:
        """Compute buoyant force (backward compatibility)"""
        buoyancy_result = self._calculate_buoyancy()
        return buoyancy_result.buoyant_force
    
    def compute_pulse_jet_force(self) -> float:
        """Compute pulse jet force (backward compatibility)"""
        # Simplified jet force calculation based on pneumatic state
        if hasattr(self.pneumatic, 'state') and self.pneumatic.state.fill_state == "filling":
            # Calculate jet force based on air flow and efficiency
            air_flow_rate = getattr(self.config, 'air_flow_rate', 0.6)
            jet_efficiency = getattr(self.config, 'jet_efficiency', 0.85)
            air_pressure = getattr(self.config, 'air_pressure', 300000)
            
            # Simplified jet force calculation: F = ρ * A * v²
            # Where v is derived from pressure and flow rate
            velocity = (air_pressure / 1000) ** 0.5  # Simplified velocity from pressure
            jet_force = 1.225 * 0.01 * velocity**2 * jet_efficiency * air_flow_rate
            
            logger.debug(f"Pulse jet force: {jet_force:.2f} N")
            return jet_force
        
        return 0.0
    
    def get_cartesian_position(self) -> tuple[float, float]:
        """Get cartesian position (backward compatibility)"""
        # Legacy floaters only have vertical position
        return (0.0, self.position)
    
    @property
    def is_filled(self) -> bool:
        """Check if floater is filled (backward compatibility)"""
        if hasattr(self.pneumatic, 'state'):
            return self.pneumatic.state.fill_state == "full"
        return False
    
    @is_filled.setter
    def is_filled(self, value: bool) -> None:
        """Set floater fill state (backward compatibility)"""
        if hasattr(self.pneumatic, 'state'):
            if value:
                self.pneumatic.state.fill_state = "full"
                self.pneumatic.state.air_fill_level = 1.0
            else:
                self.pneumatic.state.fill_state = "empty"
                self.pneumatic.state.air_fill_level = 0.0
            logger.debug(f"Floater fill state set to {'filled' if value else 'empty'}")
    
    @property
    def volume(self) -> float:
        """Get floater volume (backward compatibility)"""
        return getattr(self.config, 'volume', 0.4)
    
    @property
    def area(self) -> float:
        """Get floater area (backward compatibility)"""
        return getattr(self.config, 'area', 0.1)
    
    @property
    def mass(self) -> float:
        """Get floater mass (backward compatibility)"""
        return getattr(self.config, 'mass', 16.0)
    
    @property
    def fill_progress(self) -> float:
        """Get fill progress (backward compatibility)"""
        if hasattr(self.pneumatic, 'state'):
            return self.pneumatic.state.air_fill_level
        return 0.0
    
    @fill_progress.setter
    def fill_progress(self, value: float) -> None:
        """Set fill progress (backward compatibility)"""
        if hasattr(self.pneumatic, 'state'):
            self.pneumatic.state.air_fill_level = max(0.0, min(1.0, value))
            logger.debug(f"Floater fill progress set to {value:.2f}")
    
    @property
    def state(self) -> str:
        """Get floater state (backward compatibility)"""
        if hasattr(self.state_machine, 'current_state'):
            return self.state_machine.current_state.value
        return 'EMPTY'
    
    @state.setter
    def state(self, value: str) -> None:
        """Set floater state (backward compatibility)"""
        if hasattr(self.pneumatic, 'state'):
            if value.upper() in ['FILLED', 'FULL']:
                self.pneumatic.state.fill_state = "full"
                self.pneumatic.state.air_fill_level = 1.0
            elif value.upper() in ['EMPTY']:
                self.pneumatic.state.fill_state = "empty"
                self.pneumatic.state.air_fill_level = 0.0
            elif value.upper() in ['FILLING']:
                self.pneumatic.state.fill_state = "filling"
            logger.debug(f"Floater state set to {value}")
