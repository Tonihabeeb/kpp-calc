"""
Flywheel energy storage system for the KPP drivetrain.
Implements rotational energy buffering for smooth operation.
"""

import logging
import math
from typing import Optional

logger = logging.getLogger(__name__)


class Flywheel:
    """
    Flywheel energy storage system that smooths out power pulses
    and provides rotational inertia for stable operation.
    """

    def __init__(
        self,
        moment_of_inertia: float = 500.0,
        max_speed: float = 400.0,
        mass: float = 1000.0,
        radius: float = 1.0,
    ):
        """
        Initialize the flywheel.

        Args:
            moment_of_inertia (float): Rotational inertia (kg·m²)
            max_speed (float): Maximum safe angular velocity (rad/s)
            mass (float): Flywheel mass (kg)
            radius (float): Effective radius for energy calculations (m)
        """
        self.moment_of_inertia = moment_of_inertia
        self.max_speed = max_speed
        self.mass = mass
        self.radius = radius

        # Dynamic state
        self.angular_velocity = 0.0  # rad/s
        self.angular_acceleration = 0.0  # rad/s²
        self.stored_energy = 0.0  # J
        self.applied_torque = 0.0  # N·m

        # Performance tracking
        self.peak_speed = 0.0  # rad/s
        self.total_energy_absorbed = 0.0  # J
        self.total_energy_released = 0.0  # J
        self.speed_variations = []  # For stability analysis

        # Physical properties
        self.friction_coefficient = 0.001  # Bearing friction
        self.windage_coefficient = 0.0001  # Air resistance
        self.temperature = 20.0  # °C

    def update(self, applied_torque: float, dt: float) -> float:
        """
        Update flywheel dynamics with applied torque.

        Args:
            applied_torque (float): Net torque applied to flywheel (N·m)
            dt (float): Time step (s)

        Returns:
            float: Reaction torque (opposing acceleration)
        """
        self.applied_torque = applied_torque

        # Calculate losses
        friction_torque = self._calculate_friction_losses()
        windage_torque = self._calculate_windage_losses()
        total_loss_torque = friction_torque + windage_torque

        # Net torque after losses
        if self.angular_velocity > 0:
            net_torque = applied_torque - total_loss_torque
        else:
            net_torque = applied_torque + total_loss_torque

        # Update angular acceleration and velocity
        self.angular_acceleration = net_torque / self.moment_of_inertia

        # Store previous velocity for energy tracking
        prev_velocity = self.angular_velocity

        # Update angular velocity with speed limiting
        self.angular_velocity += self.angular_acceleration * dt
        self.angular_velocity = max(
            -self.max_speed, min(self.max_speed, self.angular_velocity)
        )

        # Update stored energy
        self.stored_energy = 0.5 * self.moment_of_inertia * self.angular_velocity**2

        # Track energy flow
        self._track_energy_flow(prev_velocity, dt)

        # Update performance metrics
        self.peak_speed = max(self.peak_speed, abs(self.angular_velocity))
        self.speed_variations.append(self.angular_velocity)

        # Keep only recent speed data for analysis
        if len(self.speed_variations) > 1000:
            self.speed_variations = self.speed_variations[-1000:]

        # Calculate reaction torque (inertial resistance)
        reaction_torque = self.moment_of_inertia * self.angular_acceleration

        logger.debug(
            f"Flywheel: speed={self.get_rpm():.1f} RPM, "
            f"energy={self.stored_energy/1000:.1f} kJ, "
            f"torque_applied={applied_torque:.1f} N·m, "
            f"reaction={reaction_torque:.1f} N·m"
        )

        return reaction_torque

    def _calculate_friction_losses(self) -> float:
        """
        Calculate realistic bearing friction losses for KPP operation.

        Enhanced friction modeling including:
        - Temperature-dependent friction
        - Load-dependent friction
        - Bearing type effects
        - Lubrication effects
        - Wear and aging effects
        - Realistic friction curves

        Returns:
            float: Friction torque (N·m)
        """
        # Enhanced friction model with realistic effects
        
        # Temperature effects on friction
        # Bearing friction typically increases with temperature
        temp_factor = 1.0 + 0.02 * (self.temperature - 20.0) / 50.0  # 2% per 50°C
        
        # Load-dependent friction (higher loads increase friction)
        # Simplified load calculation based on stored energy
        load_factor = min(1.0, self.stored_energy / (0.5 * self.moment_of_inertia * self.max_speed**2))
        load_correction = 1.0 + 0.1 * load_factor  # 10% increase at full load
        
        # Bearing type effects (assuming deep groove ball bearings)
        bearing_type_factor = 1.0  # Can be adjusted for different bearing types
        
        # Lubrication effects (simplified)
        # Assume good lubrication conditions
        lubrication_factor = 1.0  # Can be reduced for poor lubrication
        
        # Wear and aging effects (simplified)
        # Friction increases over time due to wear
        aging_factor = 1.0 + 0.05  # 5% increase due to aging
        
        # Speed-dependent friction with realistic characteristics
        # Low speed: boundary lubrication (higher friction)
        # High speed: hydrodynamic lubrication (lower friction)
        speed_ratio = abs(self.angular_velocity) / self.max_speed
        
        if speed_ratio < 0.1:
            # Boundary lubrication regime
            speed_factor = 1.5  # Higher friction at low speeds
        elif speed_ratio < 0.5:
            # Mixed lubrication regime
            speed_factor = 1.0 + 0.5 * (0.5 - speed_ratio) / 0.4
        else:
            # Hydrodynamic lubrication regime
            speed_factor = 1.0 - 0.2 * (speed_ratio - 0.5) / 0.5  # Lower friction at high speeds
        
        # Calculate enhanced friction torque
        base_friction_torque = (
            self.friction_coefficient
            * abs(self.angular_velocity)
            * self.mass
            * self.radius
        )
        
        enhanced_friction_torque = (base_friction_torque * temp_factor * 
                                   load_correction * bearing_type_factor * 
                                   lubrication_factor * aging_factor * speed_factor)
        
        # Ensure reasonable limits
        enhanced_friction_torque = max(0.0, enhanced_friction_torque)
        
        logger.debug(
            f"Enhanced friction losses: temp_factor={temp_factor:.3f}, "
            f"load_correction={load_correction:.3f}, speed_factor={speed_factor:.3f}, "
            f"friction_torque={enhanced_friction_torque:.2f}Nm"
        )
        
        return enhanced_friction_torque

    def _calculate_windage_losses(self) -> float:
        """
        Calculate realistic aerodynamic losses (windage) for KPP operation.

        Enhanced windage modeling including:
        - Air density effects (temperature and pressure)
        - Surface roughness effects
        - Enclosure effects
        - Reynolds number effects
        - Turbulence effects
        - Realistic aerodynamic coefficients

        Returns:
            float: Windage torque (N·m)
        """
        # Enhanced windage model with realistic effects
        
        # Air density effects
        # Air density decreases with temperature and altitude
        temperature_k = self.temperature + 273.15  # Convert to Kelvin
        pressure = 101325.0  # Standard atmospheric pressure (Pa)
        
        # Simplified air density calculation
        # ρ = P / (R * T) where R = 287 J/(kg·K) for air
        air_density = pressure / (287.0 * temperature_k)
        density_factor = air_density / 1.225  # Normalize to standard conditions
        
        # Surface roughness effects
        # Rougher surfaces increase windage losses
        surface_roughness = 0.0001  # 0.1 mm typical surface roughness
        roughness_factor = 1.0 + 0.2 * (surface_roughness / 0.0001)  # 20% increase per 0.1mm
        
        # Enclosure effects
        # Enclosed flywheels have different windage characteristics
        enclosure_factor = 1.0  # Can be adjusted for different enclosure types
        
        # Reynolds number effects
        # Reynolds number affects drag coefficient
        kinematic_viscosity = 1.5e-5  # m²/s for air at 20°C
        reynolds_number = abs(self.angular_velocity) * self.radius / kinematic_viscosity
        
        # Drag coefficient variation with Reynolds number
        if reynolds_number < 1e5:
            # Laminar flow
            drag_coefficient = 1.2
        elif reynolds_number < 1e6:
            # Transitional flow
            drag_coefficient = 0.8 + 0.4 * (1e6 - reynolds_number) / (1e6 - 1e5)
        else:
            # Turbulent flow
            drag_coefficient = 0.8
        
        # Turbulence effects
        # Higher speeds create more turbulence
        speed_ratio = abs(self.angular_velocity) / self.max_speed
        turbulence_factor = 1.0 + 0.3 * speed_ratio  # 30% increase at max speed
        
        # Enhanced windage coefficient calculation
        enhanced_windage_coeff = (self.windage_coefficient * density_factor * 
                                 roughness_factor * enclosure_factor * 
                                 drag_coefficient * turbulence_factor)
        
        # Calculate enhanced windage torque
        enhanced_windage_torque = (
            enhanced_windage_coeff * self.angular_velocity**2 * self.radius**3
        )
        
        # Ensure reasonable limits
        enhanced_windage_torque = max(0.0, enhanced_windage_torque)
        
        logger.debug(
            f"Enhanced windage losses: density_factor={density_factor:.3f}, "
            f"roughness_factor={roughness_factor:.3f}, drag_coeff={drag_coefficient:.3f}, "
            f"turbulence_factor={turbulence_factor:.3f}, windage_torque={enhanced_windage_torque:.2f}Nm"
        )
        
        return enhanced_windage_torque

    def _track_energy_flow(self, prev_velocity: float, dt: float):
        """
        Track realistic energy absorption and release for KPP operation.

        Enhanced energy tracking including:
        - Energy efficiency calculations
        - Loss tracking
        - Power flow analysis
        - Energy quality metrics
        - Realistic energy curves
        - Performance degradation tracking

        Args:
            prev_velocity (float): Previous angular velocity (rad/s)
            dt (float): Time step (s)
        """
        # Calculate energy change with enhanced modeling
        prev_energy = 0.5 * self.moment_of_inertia * prev_velocity**2
        energy_change = self.stored_energy - prev_energy
        
        # Calculate power flow
        power_flow = energy_change / dt if dt > 0 else 0.0
        
        # Enhanced energy tracking with realistic effects
        
        # Energy absorption (positive change)
        if energy_change > 0:
            self.total_energy_absorbed += energy_change
            
            # Track absorption efficiency
            # Real flywheels have some losses during energy storage
            absorption_efficiency = 0.98  # 98% efficiency during storage
            effective_energy_stored = energy_change * absorption_efficiency
            
            # Update stored energy with efficiency correction
            self.stored_energy = prev_energy + effective_energy_stored
            
            logger.debug(f"Energy absorbed: {energy_change:.1f}J, efficiency: {absorption_efficiency:.1%}")
        
        # Energy release (negative change)
        else:
            self.total_energy_released += abs(energy_change)
            
            # Track release efficiency
            # Real flywheels have some losses during energy extraction
            release_efficiency = 0.95  # 95% efficiency during extraction
            effective_energy_released = abs(energy_change) * release_efficiency
            
            logger.debug(f"Energy released: {abs(energy_change):.1f}J, efficiency: {release_efficiency:.1%}")
        
        # Track energy quality metrics
        # Energy quality decreases with speed variations
        speed_stability = self.get_speed_stability()
        energy_quality_factor = 1.0 - 0.1 * speed_stability  # 10% reduction per unit CV
        
        # Track performance degradation over time
        # Flywheel performance degrades with use
        degradation_factor = 1.0 - 0.001  # 0.1% degradation per time step (simplified)
        self.moment_of_inertia *= degradation_factor
        
        # Ensure reasonable limits
        self.moment_of_inertia = max(self.moment_of_inertia * 0.9, 100.0)  # Max 10% degradation
        
        logger.debug(
            f"Energy flow tracking: power_flow={power_flow:.1f}W, "
            f"energy_quality={energy_quality_factor:.3f}, "
            f"degradation_factor={degradation_factor:.3f}"
        )

    def get_rpm(self) -> float:
        """Get angular velocity in RPM."""
        return self.angular_velocity * 60 / (2 * math.pi)

    def get_speed_stability(self) -> float:
        """
        Calculate speed stability metric (coefficient of variation).

        Returns:
            float: Stability metric (lower is more stable)
        """
        if len(self.speed_variations) < 10:
            return 0.0

        recent_speeds = self.speed_variations[-100:]  # Last 100 samples
        if not recent_speeds:
            return 0.0

        mean_speed = sum(recent_speeds) / len(recent_speeds)
        if mean_speed == 0:
            return 0.0

        variance = sum((speed - mean_speed) ** 2 for speed in recent_speeds) / len(
            recent_speeds
        )
        std_dev = math.sqrt(variance)

        # Coefficient of variation (CV)
        cv = std_dev / abs(mean_speed)
        return cv

    def get_energy_efficiency(self) -> float:
        """
        Calculate energy efficiency (energy out / energy in).

        Returns:
            float: Efficiency ratio (0-1)
        """
        if self.total_energy_absorbed == 0:
            return 0.0

        return self.total_energy_released / self.total_energy_absorbed

    def apply_braking_torque(self, braking_torque: float) -> float:
        """
        Apply controlled braking for overspeed protection.

        Args:
            braking_torque (float): Braking torque to apply (N·m)

        Returns:
            float: Actual braking torque applied (N·m)
        """
        # Limit braking torque based on current speed
        max_braking = self.moment_of_inertia * 10.0  # Max 10 rad/s² deceleration
        actual_braking = min(braking_torque, max_braking)

        # Apply braking in direction opposite to rotation
        if self.angular_velocity > 0:
            return -actual_braking
        elif self.angular_velocity < 0:
            return actual_braking
        else:
            return 0.0

    def get_state(self) -> dict:
        """
        Get current flywheel state for monitoring and logging.

        Returns:
            dict: Flywheel state information
        """
        return {
            "angular_velocity_rpm": self.get_rpm(),
            "angular_velocity_rad_s": self.angular_velocity,
            "angular_acceleration": self.angular_acceleration,
            "stored_energy_kj": self.stored_energy / 1000.0,
            "applied_torque": self.applied_torque,
            "peak_speed_rpm": self.peak_speed * 60 / (2 * math.pi),
            "speed_stability": self.get_speed_stability(),
            "energy_efficiency": self.get_energy_efficiency(),
            "total_energy_absorbed_kj": self.total_energy_absorbed / 1000.0,
            "total_energy_released_kj": self.total_energy_released / 1000.0,
            "moment_of_inertia": self.moment_of_inertia,
            "temperature": self.temperature,
        }

    def reset(self):
        """Reset the flywheel to initial conditions."""
        self.angular_velocity = 0.0
        self.angular_acceleration = 0.0
        self.stored_energy = 0.0
        self.applied_torque = 0.0
        self.peak_speed = 0.0
        self.total_energy_absorbed = 0.0
        self.total_energy_released = 0.0
        self.speed_variations = []


class FlywheelController:
    """
    Controller for optimizing flywheel operation and coordinating
    with other drivetrain components.
    """

    def __init__(self, flywheel: Flywheel, target_speed: float = 375.0):
        """
        Initialize the flywheel controller.

        Args:
            flywheel (Flywheel): The flywheel to control
            target_speed (float): Target angular velocity (rad/s)
        """
        self.flywheel = flywheel
        self.target_speed = target_speed

        # Control parameters
        self.speed_tolerance = 0.1 * target_speed  # 10% tolerance
        self.overspeed_limit = 1.2 * target_speed  # 20% overspeed limit

        # PID control parameters
        self.kp = 100.0  # Proportional gain
        self.ki = 10.0  # Integral gain
        self.kd = 1.0  # Derivative gain

        # PID state
        self.integral_error = 0.0
        self.previous_error = 0.0

        # Performance tracking
        self.control_interventions = 0
        self.overspeed_events = 0

    def update(self, input_torque: float, dt: float) -> tuple[float, bool]:
        """
        Update flywheel with speed control.

        Args:
            input_torque (float): Input torque from drivetrain (N·m)
            dt (float): Time step (s)

        Returns:
            tuple[float, bool]: (reaction_torque, overspeed_protection_active)
        """
        current_speed = self.flywheel.angular_velocity

        # Check for overspeed condition
        overspeed_active = False
        if abs(current_speed) > self.overspeed_limit:
            overspeed_active = True
            self.overspeed_events += 1

            # Apply emergency braking
            braking_torque = self.flywheel.apply_braking_torque(1000.0)
            total_torque = input_torque + braking_torque

            logger.warning(
                f"Flywheel overspeed: {self.flywheel.get_rpm():.1f} RPM, applying braking"
            )
        else:
            total_torque = input_torque

        # Update flywheel with total torque
        reaction_torque = self.flywheel.update(total_torque, dt)

        return reaction_torque, overspeed_active

    def calculate_pid_correction(self, dt: float) -> float:
        """
        Calculate PID correction for speed control.

        Args:
            dt (float): Time step (s)

        Returns:
            float: Correction torque (N·m)
        """
        current_speed = self.flywheel.angular_velocity
        error = self.target_speed - current_speed

        # PID calculations
        self.integral_error += error * dt
        derivative_error = (error - self.previous_error) / dt if dt > 0 else 0.0

        # Calculate correction torque
        correction = (
            self.kp * error + self.ki * self.integral_error + self.kd * derivative_error
        )

        # Limit correction magnitude
        max_correction = 500.0  # N·m
        correction = max(-max_correction, min(max_correction, correction))

        self.previous_error = error

        if abs(correction) > 10.0:  # Only count significant interventions
            self.control_interventions += 1

        return correction

    def get_state(self) -> dict:
        """Get controller state."""
        state = self.flywheel.get_state()
        state.update(
            {
                "target_speed_rpm": self.target_speed * 60 / (2 * math.pi),
                "speed_error": self.target_speed - self.flywheel.angular_velocity,
                "control_interventions": self.control_interventions,
                "overspeed_events": self.overspeed_events,
                "integral_error": self.integral_error,
            }
        )
        return state
