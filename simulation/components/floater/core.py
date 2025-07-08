import math

import logging

import time

from typing import Any, Dict, List, Optional, Union

from dataclasses import dataclass

from enum import Enum



# Import floater subsystems

from .validation import FloaterValidator

from .thermal import ThermalModel, ThermalState

from .state_machine import FloaterStateMachine

from .pneumatic import PneumaticSystem

from .buoyancy import BuoyancyCalculator, BuoyancyResult

from config.components.floater_config import FloaterConfig as NewFloaterConfig



"""

Core floater physics and control.

Coordinates all floater subsystems and provides unified interface.

"""



class FloaterState(str, Enum):

    """Floater state enumeration"""

    EMPTY = "empty"

    FILLING = "filling"

    FULL = "full"

    VENTING = "venting"

    ERROR = "error"



@dataclass

class FloaterConfig:

    """Floater configuration data structure"""

    mass_empty: float = 10.0  # kg

    volume: float = 0.4  # m³

    radius: float = 0.1  # m

    height: float = 0.5  # m

    material_density: float = 2500.0  # kg/m³

    max_pressure: float = 500000.0  # Pa

    min_pressure: float = 100000.0  # Pa

    thermal_conductivity: float = 50.0  # W/m·K

    specific_heat: float = 900.0  # J/kg·K



# Legacy compatibility alias

LegacyFloaterConfig = FloaterConfig



@dataclass

class FloaterPhysicsData:

    """Floater physics data structure"""

    position: float = 0.0  # m

    velocity: float = 0.0  # m/s

    angle: float = 0.0  # radians

    mass: float = 10.0  # kg

    air_fill_level: float = 0.0  # 0.0 to 1.0

    pressure: float = 101325.0  # Pa

    temperature: float = 293.15  # K

    buoyancy_force: float = 0.0  # N

    net_force: float = 0.0  # N

    energy: float = 0.0  # J



class Floater:

    """

    Complete floater physics and control system.

    Manages state transitions, physics calculations, and subsystem coordination.

    """

    

    def __init__(self, config: Optional[FloaterConfig] = None, floater_id: int = 0):

        """

        Initialize the floater.

        

        Args:

            config: Floater configuration

            floater_id: Unique floater identifier

        """

        self.config = config or FloaterConfig()

        self.floater_id = floater_id

        self.logger = logging.getLogger(f"{__name__}.floater_{floater_id}")

        

        # State management

        self.state = FloaterState.EMPTY

        self.state_history: List[FloaterState] = []

        self.state_transition_time = time.time()

        

        # Physics state

        self.physics_data = FloaterPhysicsData()

        self.physics_data.mass = self.config.mass_empty

        

        # Performance tracking

        self.performance_metrics = {

            'total_cycles': 0,

            'successful_cycles': 0,

            'failed_cycles': 0,

            'average_cycle_time': 0.0,

            'total_energy_consumed': 0.0,

            'total_energy_generated': 0.0,

            'efficiency': 0.0

        }

        

        # Subsystem interfaces (will be initialized by external systems)

        self.buoyancy_calculator = None

        self.thermal_model = None

        self.state_machine = None

        self.pneumatic_system = None

        

        # Event tracking

        self.last_injection_time = 0.0

        self.last_venting_time = 0.0

        self.cycle_start_time = 0.0

        

        # Error handling

        self.error_count = 0

        self.last_error = None

        self.error_threshold = 5

        

        self.logger.info("Floater %d initialized with state: %s", floater_id, self.state)

    

    def update_position(self, new_position: float, dt: float = 0.01) -> None:

        """

        Update floater position and calculate velocity.

        

        Args:

            new_position: New position (m)

            dt: Time step (s)

        """

        try:

            # Calculate velocity

            if dt > 0:

                self.physics_data.velocity = (new_position - self.physics_data.position) / dt

            

            # Update position

            self.physics_data.position = new_position

            

            # Calculate angle based on position

            tank_height = 10.0  # Default tank height

            normalized_position = self.physics_data.position / tank_height

            self.physics_data.angle = normalized_position * math.pi

            

            # Validate and clamp position bounds
            if self.physics_data.position < 0.0:
                self.logger.warning("Position below bounds: %.2f m, clamping to 0.0", self.physics_data.position)
                self.physics_data.position = 0.0
            elif self.physics_data.position > tank_height:
                self.logger.warning("Position above bounds: %.2f m, clamping to %.1f", self.physics_data.position, tank_height)
                self.physics_data.position = tank_height
            

        except Exception as e:

            self.logger.error("Error updating position: %s", e)

            self._handle_error("position_update_error", str(e))

    

    def calculate_buoyancy_force(self) -> float:
        """
        Calculate buoyancy force based on current state using Archimedes' principle.

        The buoyancy force is calculated as: F_b = ρ_water × V_displaced × g
        where:
            - ρ_water = water density (1000 kg/m³)
            - V_displaced = volume of water displaced by the floater
            - g = gravitational acceleration (9.81 m/s²)

        The displaced volume varies based on floater state:
            - EMPTY/VENTING: Full floater volume displaced
            - FULL/FILLING: Only container volume displaced (reduced by air fill level)

        If a thermal model is available, a thermal correction factor is applied to the buoyancy force.

        Returns:
            Buoyancy force (N) - positive upward force
        """
        try:

            # Get water properties

            water_density = 1000.0  # kg/m³

            gravity = 9.81  # m/s²

            

            # Calculate displaced volume

            if self.state in [FloaterState.EMPTY, FloaterState.VENTING]:

                # Empty floater: full volume displaced

                displaced_volume = self.config.volume

            elif self.state in [FloaterState.FULL, FloaterState.FILLING]:

                # Full floater: only container volume displaced

                displaced_volume = self.config.volume * (1.0 - self.physics_data.air_fill_level)

            else:

                displaced_volume = self.config.volume

            

            # Calculate buoyancy force: F_b = rho_water x V x g

            buoyancy_force = water_density * displaced_volume * gravity

            

            # Apply thermal effects if thermal model is available

            if self.thermal_model:

                thermal_factor = self.thermal_model.calculate_thermal_buoyancy(

                    self.physics_data.temperature, 293.15, displaced_volume

                )

                buoyancy_force *= thermal_factor

            

            self.physics_data.buoyancy_force = buoyancy_force

            return buoyancy_force

            

        except Exception as e:

            self.logger.error("Error calculating buoyancy force: %s", e)

            self._handle_error("buoyancy_calculation_error", str(e))

            return 0.0

    

    def calculate_net_force(self) -> float:

        """

        Calculate net force on the floater.

        

        Returns:

            Net force (N)

        """

        try:

            gravity = 9.81  # m/s²

            

            # Gravitational force: F_g = m x g

            gravitational_force = self.physics_data.mass * gravity

            

            # Buoyancy force

            buoyancy_force = self.calculate_buoyancy_force()

            

            # Drag force (simplified): F_d = 0.5 x rho x C_d x A x v²

            water_density = 1000.0  # kg/m³

            drag_coefficient = 0.5

            cross_sectional_area = math.pi * self.config.radius ** 2

            velocity = self.physics_data.velocity

            drag_force = 0.5 * water_density * drag_coefficient * cross_sectional_area * velocity ** 2

            

            # Net force: F_net = F_b - F_g - F_d

            net_force = buoyancy_force - gravitational_force - drag_force

            

            self.physics_data.net_force = net_force

            return net_force

            

        except Exception as e:

            self.logger.error("Error calculating net force: %s", e)

            self._handle_error("net_force_calculation_error", str(e))

            return 0.0

    

    def update_mass(self) -> None:

        """

        Update floater mass based on current state and air fill level.

        """

        try:

            # Base mass (container)

            base_mass = self.config.mass_empty

            

            # Water mass based on air fill level

            water_volume = self.config.volume * (1.0 - self.physics_data.air_fill_level)

            water_density = 1000.0  # kg/m³

            water_mass = water_volume * water_density

            

            # Air mass (negligible but included for completeness)

            air_volume = self.config.volume * self.physics_data.air_fill_level

            air_density = 1.225  # kg/m³

            air_mass = air_volume * air_density

            

            # Total mass

            total_mass = base_mass + water_mass + air_mass

            

            self.physics_data.mass = total_mass

            

        except Exception as e:

            self.logger.error("Error updating mass: %s", e)

            self._handle_error("mass_update_error", str(e))

    

    def inject_air(self, volume: float, pressure: float) -> bool:

        """

        Inject air into the floater.

        

        Args:

            volume: Air volume to inject (m³)

            pressure: Injection pressure (Pa)

            

        Returns:

            True if injection successful, False otherwise

        """

        try:

            # Validate injection parameters

            if volume <= 0 or volume > self.config.volume:

                self.logger.error("Invalid injection volume: %.3f m³", volume)

                return False

            

            if pressure < self.config.min_pressure or pressure > self.config.max_pressure:

                self.logger.error("Invalid injection pressure: %.0f Pa", pressure)

                return False

            

            # Check if floater is in correct state

            if self.state not in [FloaterState.EMPTY, FloaterState.FILLING]:

                self.logger.warning("Cannot inject air in state: %s", self.state)

                return False

            

            # Calculate new air fill level

            current_air_volume = self.config.volume * self.physics_data.air_fill_level

            new_air_volume = current_air_volume + volume

            new_air_fill_level = new_air_volume / self.config.volume

            

            # Ensure air fill level doesn't exceed 1.0

            if new_air_fill_level > 1.0:

                new_air_fill_level = 1.0

                volume = self.config.volume - current_air_volume

            

            # Update floater state

            self.physics_data.air_fill_level = new_air_fill_level

            self.physics_data.pressure = pressure

            

            # Update state

            if new_air_fill_level >= 0.95:  # 95% full

                self._transition_state(FloaterState.FULL)

            else:

                self._transition_state(FloaterState.FILLING)

            

            # Update mass

            self.update_mass()

            

            # Track injection

            self.last_injection_time = time.time()

            

            # Calculate energy cost

            energy_cost = self._calculate_injection_energy(volume, pressure)

            self.performance_metrics['total_energy_consumed'] += energy_cost

            

            self.logger.info("Air injection successful: %.3f m³ at %.0f Pa", volume, pressure)

            return True

            

        except Exception as e:

            self.logger.error("Error during air injection: %s", e)

            self._handle_error("injection_error", str(e))

            return False

    

    def vent_air(self) -> bool:

        """

        Vent air from the floater.

        

        Returns:

            True if venting successful, False otherwise

        """

        try:

            # Check if floater is in correct state

            if self.state not in [FloaterState.FULL, FloaterState.VENTING]:

                self.logger.warning("Cannot vent air in state: %s", self.state)

                return False

            

            # Calculate vented volume

            vented_volume = self.config.volume * self.physics_data.air_fill_level

            

            # Update floater state

            self.physics_data.air_fill_level = 0.0

            self.physics_data.pressure = 101325.0  # Atmospheric pressure

            

            # Update state

            self._transition_state(FloaterState.EMPTY)

            

            # Update mass

            self.update_mass()

            

            # Track venting

            self.last_venting_time = time.time()

            

            # Complete cycle

            self._complete_cycle()

            

            self.logger.info("Air venting successful: %.3f m³ vented", vented_volume)

            return True

            

        except Exception as e:

            self.logger.error("Error during air venting: %s", e)

            self._handle_error("venting_error", str(e))

            return False

    

    def _transition_state(self, new_state: FloaterState) -> None:

        """

        Transition to a new state.

        

        Args:

            new_state: New floater state

        """

        try:

            old_state = self.state

            self.state = new_state

            self.state_history.append(new_state)

            self.state_transition_time = time.time()

            

            self.logger.info("State transition: %s -> %s", old_state, new_state)

            

        except Exception as e:

            self.logger.error("Error during state transition: %s", e)

            self._handle_error("state_transition_error", str(e))

    

    def _complete_cycle(self) -> None:

        """

        Complete a full cycle (empty -> full -> empty).

        """

        try:

            self.performance_metrics['total_cycles'] += 1

            

            # Calculate cycle time

            if self.cycle_start_time > 0:

                cycle_time = time.time() - self.cycle_start_time

                self.performance_metrics['average_cycle_time'] = (

                    (self.performance_metrics['average_cycle_time'] * (self.performance_metrics['total_cycles'] - 1) + cycle_time) /

                    self.performance_metrics['total_cycles']

                )

            

            # Start new cycle

            self.cycle_start_time = time.time()

            

            self.logger.info("Cycle %d completed", self.performance_metrics['total_cycles'])

            

        except Exception as e:

            self.logger.error("Error completing cycle: %s", e)

            self._handle_error("cycle_completion_error", str(e))

    

    def _calculate_injection_energy(self, volume: float, pressure: float) -> float:

        """

        Calculate energy required for air injection.

        

        Args:

            volume: Air volume (m³)

            pressure: Injection pressure (Pa)

            

        Returns:

            Energy cost (J)

        """

        try:

            # Isothermal compression work: W = P x V x ln(P_final/P_initial)

            initial_pressure = 101325.0  # Atmospheric pressure

            if pressure > initial_pressure:

                energy = initial_pressure * volume * math.log(pressure / initial_pressure)

            else:

                energy = 0.0

            

            return energy

            

        except Exception as e:

            self.logger.error("Error calculating injection energy: %s", e)

            return 0.0

    

    def _handle_error(self, error_type: str, error_message: str) -> None:

        """

        Handle errors and update error tracking.

        

        Args:

            error_type: Type of error

            error_message: Error message

        """

        self.error_count += 1

        self.last_error = f"{error_type}: {error_message}"

        

        if self.error_count >= self.error_threshold:

            self._transition_state(FloaterState.ERROR)

            self.logger.error("Error threshold exceeded, transitioning to ERROR state")

    

    def get_physics_data(self) -> FloaterPhysicsData:

        """

        Get current physics data.

        

        Returns:

            Current physics data

        """

        return self.physics_data

    

    def get_state(self) -> FloaterState:

        """

        Get current floater state.

        

        Returns:

            Current state

        """

        return self.state

    

    def get_performance_metrics(self) -> Dict[str, Any]:

        """

        Get performance metrics.

        

        Returns:

            Performance metrics dictionary

        """

        return self.performance_metrics.copy()

    

    def get_state_history(self) -> List[FloaterState]:

        """

        Get state history.

        

        Returns:

            List of previous states

        """

        return self.state_history.copy()

    

    def reset(self) -> None:

        """Reset floater to initial state."""

        self.state = FloaterState.EMPTY

        self.state_history.clear()

        self.physics_data = FloaterPhysicsData()

        self.physics_data.mass = self.config.mass_empty

        self.performance_metrics = {

            'total_cycles': 0,

            'successful_cycles': 0,

            'failed_cycles': 0,

            'average_cycle_time': 0.0,

            'total_energy_consumed': 0.0,

            'total_energy_generated': 0.0,

            'efficiency': 0.0

        }

        self.error_count = 0

        self.last_error = None

        self.cycle_start_time = 0.0

        self.logger.info("Floater %d reset", self.floater_id)



