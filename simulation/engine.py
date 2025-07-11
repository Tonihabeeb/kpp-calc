"""
SimulationEngine: orchestrates all simulation modules
Coordinates state updates, manages simulation loop,
and handles cross-module interactions
"""

import time
import threading
import math
import logging
from typing import Any, Dict, List, Optional, Union
from queue import Queue

from simulation.grid_services import (
    GridServicesCoordinator,
    GridServicesConfig,
    GridServicesState,
    GridConditions
)

from simulation.control.integrated_control_system import (
    IntegratedControlSystem,
    ControlConfig,
    ControlState
)

from simulation.physics import (
    PhysicsEngine,
    PhysicsConfig,
    PhysicsState
)

from simulation.components.floater.enhanced_floater import (
    EnhancedFloater,
    EnhancedFloaterConfig,
    FloaterState
)

from simulation.components.environment import (
    Environment,
    EnvironmentConfig
)

from simulation.components.pneumatics import (
    PneumaticSystem,
    PneumaticConfig
)

from simulation.components.drivetrain import (
    IntegratedDrivetrain,
    DrivetrainConfig
)

from simulation.schemas import (
    PhysicsResults,
    FloaterPhysicsData,
    EnhancedPhysicsData,
    ComponentStatus,
    ManagerType,
    SimulationError,
    ManagerInterface,
    SimulationState,
    SystemState,
    BatteryState,
    EnvironmentState,
    PneumaticState,
    DrivetrainState
)

class DrivetrainCompatibilityWrapper:
    """Compatibility wrapper for IntegratedDrivetrain to match legacy interface"""
    
    def __init__(self, integrated_drivetrain):
        self.drivetrain = integrated_drivetrain
        self.angular_velocity = 0.0
        self.angular_position = 0.0
        self.chain_radius = 1.0  # Default chain radius
        
    def get_state(self):
        """Get state in legacy format"""
        state = self.drivetrain.get_drivetrain_state()
        return {
            'angular_velocity': self.angular_velocity,
            'angular_position': self.angular_position,
            'clutch_engagement': 1.0 if state.clutch_state.value == 'engaged' else 0.0,
            'kinetic_energy': self.drivetrain.get_flywheel_energy(),
            'output_energy': 0.0,  # Will be calculated
            'current_power': state.output_power,
            'h3_active': True  # Integrated drivetrain always has H3
        }
    
    def update(self, dt, net_torque=None):
        """Update drivetrain state"""
        if net_torque is not None and net_torque > 0:
            # Start drivetrain if we have positive torque
            input_speed = self.angular_velocity * 60 / (2 * math.pi)  # Convert rad/s to RPM
            if input_speed <= 0:
                input_speed = 100.0  # Default speed if not moving
            self.drivetrain.start_drivetrain(input_speed, net_torque)
        else:
            # Stop drivetrain if no torque
            self.drivetrain.stop_drivetrain()
        
        # Update internal state
        state = self.drivetrain.get_drivetrain_state()
        self.angular_velocity = state.input_speed * 2 * math.pi / 60  # Convert RPM to rad/s
        self.angular_position += self.angular_velocity * dt
    
    def get_chain_velocity(self):
        """Get chain velocity"""
        return self.angular_velocity * self.chain_radius
    
    def get_speed(self):
        """Get angular speed in rad/s"""
        return self.angular_velocity
    
    def get_power(self):
        """Get output power"""
        state = self.drivetrain.get_drivetrain_state()
        return state.output_power

class SimulationConfig:
    """Configuration for the simulation engine"""
    def __init__(self, **kwargs):
        # Basic simulation parameters
        self.time_step = kwargs.get('time_step', 0.01)  # seconds
        self.num_floaters = kwargs.get('num_floaters', 60)
        self.tank_height = kwargs.get('tank_height', 10.0)  # meters
        self.rated_power = kwargs.get('rated_power', 50000.0)  # 50 kW default
        
        # Enhancement flags
        self.enable_h1 = kwargs.get('enable_h1', False)
        self.enable_h2 = kwargs.get('enable_h2', False)
        self.enable_h3 = kwargs.get('enable_h3', False)
        
        # Enhancement parameters
        self.nanobubble_fraction = kwargs.get('nanobubble_fraction', 0.2)
        self.thermal_expansion_coeff = kwargs.get('thermal_expansion_coeff', 0.001)
        self.flywheel_inertia = kwargs.get('flywheel_inertia', 10.0)
        
        # Efficiency parameters
        self.mechanical_efficiency = kwargs.get('mechanical_efficiency', 0.95)
        self.electrical_efficiency = kwargs.get('electrical_efficiency', 0.92)

        # Motion limits
        self.max_velocity = kwargs.get('max_velocity', 10.0)  # m/s
        self.max_angular_velocity = kwargs.get('max_angular_velocity', 20.0)  # rad/s

class SimulationEngine:
    """
    Simulation engine class.
    Coordinates all simulation components and manages the simulation loop.
    """
    
    def __init__(self, config: Optional[Union[Dict[str, Any], SimulationConfig]] = None):
        """
        Initialize the simulation engine.
        
        Args:
            config: Configuration for the simulation
        """
        # Convert dict config to SimulationConfig if needed
        if isinstance(config, dict):
            self.config = SimulationConfig(**config)
        else:
            self.config = config or SimulationConfig()
            
        self.logger = logging.getLogger(__name__)
        self.is_running = False
        self.simulation_thread = None
        self.state_queue = Queue()
        
        # Component management
        self.components: Dict[str, Any] = {}
        self.component_status: Dict[str, ComponentStatus] = {}
        
        # Error tracking
        self.error_count = 0
        self.errors: List[SimulationError] = []
        
        # Performance metrics
        self.total_energy = 0.0
        self.total_power = 0.0
        self.efficiency = 0.0
        self.step_count = 0
        self.step_time = 0.0
        
        # Time configuration
        self.time_step = self.config.time_step
        self.simulation_time = 0.0
        
        # Initialize components
        self._initialize_components()
    
    def _initialize_components(self):
        """Initialize simulation components."""
        self.logger.info("Initializing simulation components...")
        
        try:
            # Initialize environment
            env_config = EnvironmentConfig(
                water_density=1000.0,
                water_temperature=20.0,
                enable_h1=self.config.enable_h1,
                nanobubble_fraction=self.config.nanobubble_fraction,
                enable_h2=self.config.enable_h2,
                thermal_expansion_coeff=self.config.thermal_expansion_coeff
            )
            self.environment = Environment(env_config)
            
            # Initialize drivetrain
            drivetrain_config = DrivetrainConfig(
                rated_power=self.config.rated_power,
                rated_speed=1500.0,
                rated_torque=318.3,
                gear_ratio=1.0,
                sprocket_ratio=1.0,
                clutch_torque_capacity=500.0,
                flywheel_moment_of_inertia=self.config.flywheel_inertia,
                max_chain_tension=50000.0,
                efficiency_nominal=self.config.mechanical_efficiency,
                max_speed=2000.0
            )
            self.drivetrain = IntegratedDrivetrain(drivetrain_config)
            
            # Initialize pneumatic system
            pneumatic_config = PneumaticConfig(
                enable_h2=self.config.enable_h2,
                thermal_expansion_coeff=self.config.thermal_expansion_coeff,
                isothermal_efficiency=0.9
            )
            self.pneumatic_system = PneumaticSystem(pneumatic_config)
            
            # Initialize floaters
            self.floaters = []
            floater_config = EnhancedFloaterConfig(
                volume=0.04,  # 40L
                mass_empty=5.0,  # 5kg
                cross_section=0.1  # 0.1m²
            )
            num_floaters = self.config.num_floaters
            tank_height = self.config.tank_height
            for i in range(num_floaters):
                floater = EnhancedFloater(floater_config)
                # Evenly space floaters around the loop
                floater.position = (i / num_floaters) * tank_height
                if i < num_floaters // 2:
                    # First half: buoyant (ascending)
                    floater.is_buoyant = True
                    floater.mass_water = 0.0
                    floater.mass_air = 1.225 * floater.volume
                    floater.velocity = abs(0.1)  # small upward velocity
                else:
                    # Second half: water-filled (descending)
                    floater.is_buoyant = False
                    floater.mass_water = 1000.0 * floater.volume
                    floater.mass_air = 0.0
                    floater.velocity = -abs(0.1)  # small downward velocity
                self.floaters.append(floater)
            
            # Initialize physics engine with all components
            physics_config = PhysicsConfig(
                time_step=self.time_step,
                tank_height=self.config.tank_height,
                enable_h1=self.config.enable_h1,
                enable_h2=self.config.enable_h2,
                enable_h3=self.config.enable_h3,
                nanobubble_fraction=self.config.nanobubble_fraction,
                thermal_expansion_coeff=self.config.thermal_expansion_coeff,
                flywheel_inertia=self.config.flywheel_inertia,
                max_velocity=10.0,  # m/s
                max_acceleration=5.0,  # m/s²
                max_angular_velocity=20.0  # rad/s
            )
            self.physics_engine = PhysicsEngine(physics_config)
            
            # Register components with physics engine
            self.physics_engine.set_environment(self.environment)
            # Create compatibility wrapper for drivetrain
            self.drivetrain_wrapper = DrivetrainCompatibilityWrapper(self.drivetrain)
            self.physics_engine.set_drivetrain(self.drivetrain_wrapper)
            self.physics_engine.set_pneumatics(self.pneumatic_system)
            self.physics_engine.set_floaters(self.floaters)
            
            # Initialize control system
            control_config = ControlConfig(
                max_power=self.config.rated_power,
                max_speed=2000.0,  # RPM
                target_frequency=50.0,  # Hz
                response_time_target=0.1,  # seconds
                optimization_enabled=True,
                fault_tolerance=0.05,  # 5%
                pid_kp=1.0,
                pid_ki=0.1,
                pid_kd=0.01,
                grid_sync_tolerance=0.02  # 2%
            )
            self.control_system = IntegratedControlSystem(control_config)
            
            # Initialize grid services
            grid_config = GridServicesConfig(
                rated_power=self.config.rated_power,
                nominal_frequency=50.0,
                nominal_voltage=1.0,
                target_power_factor=0.98,
                frequency_priority=1.0,
                voltage_priority=0.8,
                power_factor_priority=0.6,
                storage_priority=0.9,
                demand_response_priority=0.7,
                economic_priority=0.5,
                update_rate=0.1
            )
            self.grid_services = GridServicesCoordinator(grid_config)
            
            self.logger.info("All simulation components initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Error initializing components: {e}")
            raise
    
    def start(self):
        """Start the simulation."""
        if self.is_running:
            self.logger.warning("Simulation is already running")
            return
        
        self.is_running = True
        self.simulation_thread = threading.Thread(target=self._simulation_loop)
        self.simulation_thread.start()
        self.logger.info("Simulation started")
    
    def stop(self):
        """Stop the simulation."""
        self.is_running = False
        if self.simulation_thread:
            self.simulation_thread.join()
        self.logger.info("Simulation stopped")
    
    def step(self) -> SimulationState:
        """
        Execute one simulation step.
        Performs physics calculations, updates component states,
        and handles interactions between components.
        
        Returns:
            SimulationState: Current state of the simulation
        """
        try:
            # Get current states from all components
            component_states = {
                'environment': self.environment.get_state(),
                'drivetrain': self.drivetrain_wrapper.get_state(),
                'pneumatics': self.pneumatic_system.get_state(),
                'floaters': [f.get_state() for f in self.floaters]
            }
            
            # Use drivetrain state dict directly
            drivetrain_state = component_states['drivetrain']
            env_state = component_states['environment']
            pneumatic_state = component_states['pneumatics']
            
            # Create simulation state (pass drivetrain_state as dict)
            sim_state = SimulationState(
                time=self.simulation_time,
                step_count=self.step_count,
                total_power=self.total_power,
                total_energy=self.total_energy,
                efficiency=self.efficiency,
                environment=env_state,
                pneumatics=pneumatic_state,
                drivetrain=drivetrain_state,
                floaters=component_states['floaters'],
                control=None,  # TODO: Add control state
                grid_services=None,  # TODO: Add grid services state
                errors=self.errors,
                component_status=self.component_status
            )
            
            # Update physics engine with current state
            physics_results = self.physics_engine.update(
                state=sim_state,
                time_step=self.time_step,
                component_states=component_states
            )
            
            # Update environment conditions
            if self.config.enable_h1:
                self.environment.set_nanobubble_fraction(self.config.nanobubble_fraction)
            if self.config.enable_h2:
                self.environment.set_thermal_expansion_coeff(self.config.thermal_expansion_coeff)
            
            # Update each floater's physics
            for floater in self.floaters:
                # Calculate forces using buoyant state for H1/H2 effects
                buoyant_force = self.environment.compute_buoyant_force(
                    volume=floater.volume,
                    depth=abs(floater.position),
                    is_ascending=floater.is_buoyant  # Use buoyant state instead of velocity
                )

                drag_force = self.environment.compute_drag_force(
                    velocity=floater.velocity,
                    cross_section=floater.cross_section,
                    is_ascending=floater.is_buoyant  # Use buoyant state instead of velocity
                )

                # Update floater state
                floater.update(
                    time_step=self.time_step,
                    environment=self.environment
                )

                # Check for state transitions (injection/venting)
                if floater.position <= 0 and not floater.is_buoyant:
                    # Bottom - inject air
                    self.pneumatic_system.inject_air(floater)
                    floater.set_buoyant(True)

                elif floater.position >= self.config.tank_height and floater.is_buoyant:
                    # Top - vent air
                    self.pneumatic_system.vent_air(floater)
                    floater.set_buoyant(False)
            
            # Calculate net torque from all floaters
            net_torque = sum(f.compute_torque(self.drivetrain_wrapper.chain_radius) for f in self.floaters)
            
            # Update drivetrain with net torque
            if self.config.enable_h3:
                # H3 mode: Use flywheel and clutch
                self.drivetrain_wrapper.update(
                    dt=self.time_step,
                    net_torque=net_torque
                )
            else:
                # Normal mode: Direct drive
                self.drivetrain_wrapper.update(
                    dt=self.time_step,
                    net_torque=net_torque
                )
            
            # Update simulation metrics
            self.total_power = physics_results.total_power
            self.total_energy = physics_results.total_energy
            self.efficiency = physics_results.efficiency
            
            # Safety checks
            if any(abs(f.velocity) > self.config.max_velocity for f in self.floaters):
                self.logger.warning("Velocity limit exceeded")
                
            if abs(self.drivetrain_wrapper.angular_velocity) > self.config.max_angular_velocity:
                self.logger.warning("Angular velocity limit exceeded")
            
            # Update simulation time
            self.simulation_time += self.time_step
            self.step_count += 1
            
            return sim_state
            
        except Exception as e:
            import traceback
            self.logger.error(f"Error in simulation step: {e}\n{traceback.format_exc()}")
            self.report_error(SimulationError(
                message=str(e),
                component="engine",
                severity="high"
            ))
            raise
    
    def _simulation_loop(self):
        """
        Main simulation loop.
        Runs continuously while is_running is True.
        Maintains consistent time step and handles state updates.
        """
        self.logger.info("Starting simulation loop")
        
        try:
            while self.is_running:
                loop_start = time.time()
                
                try:
                    # Execute simulation step
                    state = self.step()
                except Exception as e:
                    import traceback
                    self.logger.error(f"Exception in simulation loop: {e}\n{traceback.format_exc()}")
                    self.report_error(SimulationError(
                        message=str(e),
                        component="engine",
                        severity="critical"
                    ))
                    self.stop()
                    break
                
                # Put state in queue for external access
                try:
                    self.state_queue.put_nowait(state)
                except:
                    # Queue full - drop oldest state
                    try:
                        self.state_queue.get_nowait()
                        self.state_queue.put_nowait(state)
                    except:
                        pass
                
                # Calculate time to sleep
                loop_duration = time.time() - loop_start
                sleep_time = max(0, self.time_step - loop_duration)
                
                # Track performance
                self.step_time = loop_duration
                
                if loop_duration > self.time_step:
                    self.logger.warning(
                        f"Simulation loop taking longer than time step "
                        f"({loop_duration:.3f}s > {self.time_step:.3f}s)"
                    )
                
                # Sleep remaining time
                if sleep_time > 0:
                    time.sleep(sleep_time)
                    
        except Exception as e:
            self.logger.error(f"Error in simulation loop: {e}")
            self.report_error(SimulationError(
                message=str(e),
                component="engine",
                severity="critical"
            ))
            self.stop()
            raise

    def register_component(self, name: str, component: Any) -> bool:
        """Register a simulation component."""
        try:
            self.components[name] = component
            self.component_status[name] = ComponentStatus.READY
            self.logger.info(f"Component {name} registered successfully")
            return True
        except Exception as e:
            self.logger.error(f"Error registering component {name}: {e}")
            return False
    
    def get_components(self) -> Dict[str, Any]:
        """Get all registered components."""
        return self.components
    
    def report_error(self, error: SimulationError):
        """Report a simulation error."""
        self.errors.append(error)
        self.error_count += 1
        self.logger.error(f"Simulation error: {error.error_code} - {error.message}")
    
    def get_state(self) -> SimulationState:
        """Get current simulation state."""
        return SimulationState(
            time=self.simulation_time,
            step_count=self.step_count,
            total_power=self.total_power,
            total_energy=self.total_energy,
            efficiency=self.efficiency,
            environment=self.environment.get_state() if hasattr(self, 'environment') else None,
            pneumatics=self.pneumatic_system.get_state() if hasattr(self, 'pneumatic_system') else None,
            drivetrain=self.drivetrain_wrapper.get_state() if hasattr(self, 'drivetrain_wrapper') else None,
            floaters=[f.get_state() for f in self.floaters] if hasattr(self, 'floaters') else [],
            control=self.control_system.get_state() if hasattr(self, 'control_system') else None,
            grid_services=self.grid_services.get_state() if hasattr(self, 'grid_services') else None,
            errors=self.errors,
            component_status=self.component_status
        )

    def set_parameters(self, params: Dict[str, Any]) -> bool:
        """
        Update simulation parameters.
        
        Args:
            params: Dictionary of parameters to update
        
        Returns:
            bool: True if successful
        """
        try:
            # Update enhancement flags
            if 'enable_h1' in params:
                self.config.enable_h1 = bool(params['enable_h1'])
                if hasattr(self, 'environment'):
                    self.environment.set_h1_enabled(self.config.enable_h1)
            
            if 'enable_h2' in params:
                self.config.enable_h2 = bool(params['enable_h2'])
                if hasattr(self, 'environment'):
                    self.environment.set_h2_enabled(self.config.enable_h2)
                if hasattr(self, 'pneumatic_system'):
                    self.pneumatic_system.set_h2_enabled(self.config.enable_h2)
            
            if 'enable_h3' in params:
                self.config.enable_h3 = bool(params['enable_h3'])
                # H3 is always enabled in integrated drivetrain
            
            # Update enhancement parameters
            if 'nanobubble_fraction' in params:
                self.config.nanobubble_fraction = float(params['nanobubble_fraction'])
                if hasattr(self, 'environment'):
                    self.environment.set_nanobubble_fraction(self.config.nanobubble_fraction)
            
            if 'thermal_expansion_coeff' in params:
                self.config.thermal_expansion_coeff = float(params['thermal_expansion_coeff'])
                if hasattr(self, 'environment'):
                    self.environment.set_thermal_expansion_coeff(self.config.thermal_expansion_coeff)
                if hasattr(self, 'pneumatic_system'):
                    self.pneumatic_system.set_thermal_expansion_coeff(self.config.thermal_expansion_coeff)
            
            if 'flywheel_inertia' in params:
                self.config.flywheel_inertia = float(params['flywheel_inertia'])
                # Flywheel inertia is configured at initialization in integrated drivetrain
            
            # Update physics engine with new parameters
            if hasattr(self, 'physics_engine'):
                self.physics_engine.update_parameters(params)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating parameters: {e}")
            self.report_error(SimulationError(str(e)))
            return False

