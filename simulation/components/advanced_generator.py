"""
Advanced Generator Model for Phase 3 Implementation
Enhanced electromagnetic modeling with realistic generator characteristics.
"""

import logging
import math
from typing import Any, Dict, Optional


logger = logging.getLogger(__name__)


class AdvancedGenerator:
    """
    Advanced generator model with realistic electromagnetic characteristics.

    Models:
    - Electromagnetic torque curves
    - Efficiency maps based on speed and load
    - Magnetic saturation effects
    - Iron losses (hysteresis and eddy current)
    - Copper losses (I²R)
    - Mechanical losses (bearing friction, windage)
    - Grid synchronization requirements
    - Reactive power and power factor
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize advanced generator with comprehensive electromagnetic modeling.

        Args:
            config (dict): Generator configuration parameters
        """
        if config is None:
            config = {}

        # Basic electrical parameters
        self.rated_power = config.get("rated_power", 530000.0)  # W
        self.rated_voltage = config.get("rated_voltage", 480.0)  # V (line-to-line)
        self.rated_frequency = config.get("rated_frequency", 50.0)  # Hz
        self.rated_speed = config.get("rated_speed", 375.0)  # RPM
        self.pole_pairs = config.get("pole_pairs", 4)  # Number of pole pairs

        # Electromagnetic parameters
        self.stator_resistance = config.get("stator_resistance", 0.02)  # Ohms per phase
        self.stator_reactance = config.get("stator_reactance", 0.15)  # Ohms per phase
        self.magnetizing_reactance = config.get("magnetizing_reactance", 3.0)  # Ohms
        self.rotor_resistance = config.get("rotor_resistance", 0.025)  # Ohms referred to stator
        self.rotor_reactance = config.get("rotor_reactance", 0.18)  # Ohms referred to stator

        # Mechanical parameters
        self.rotor_inertia = config.get("rotor_inertia", 12.0)  # kg⋅m²
        self.bearing_friction_coeff = config.get("bearing_friction", 0.001)  # N⋅m⋅s/rad
        self.windage_loss_coeff = config.get("windage_loss", 0.5)  # W⋅s²/rad²

        # Efficiency curve parameters
        self.iron_loss_constant = config.get("iron_loss_constant", 2500.0)  # W
        self.copper_loss_factor = config.get("copper_loss_factor", 1.2)  # Multiplier for I²R losses

        # Control parameters
        self.max_slip = config.get("max_slip", 0.05)  # Maximum slip for stable operation
        self.min_excitation = config.get("min_excitation", 0.1)  # Minimum field excitation
        self.power_factor_target = config.get("power_factor", 0.92)  # Target power factor

        # FOC (Field-Oriented Control) parameters
        self.foc_enabled = config.get("foc_enabled", True)
        self.d_axis_current = 0.0  # Direct axis current (flux control)
        self.q_axis_current = 0.0  # Quadrature axis current (torque control)
        self.flux_reference = config.get("flux_reference", 1.0)  # Per unit flux reference
        self.torque_controller_kp = config.get("torque_kp", 100.0)  # Torque PI controller gains
        self.torque_controller_ki = config.get("torque_ki", 50.0)
        self.flux_controller_kp = config.get("flux_kp", 80.0)  # Flux PI controller gains
        self.flux_controller_ki = config.get("flux_ki", 40.0)

        # FOC controller state
        self.torque_error_integral = 0.0
        self.flux_error_integral = 0.0
        self.previous_torque_error = 0.0
        self.previous_flux_error = 0.0

        # State variables
        self.angular_velocity = 0.0  # rad/s
        self.slip = 0.0  # Per unit slip
        self.torque = 0.0  # N⋅m
        self.electrical_power = 0.0  # W
        self.mechanical_power = 0.0  # W
        self.efficiency = 0.0  # Overall efficiency
        self.power_factor = 0.0  # Current power factor
        self.field_excitation = 1.0  # Per unit field excitation

        # Loss breakdown
        self.iron_losses = 0.0  # W
        self.copper_losses = 0.0  # W
        self.mechanical_losses = 0.0  # W
        self.total_losses = 0.0  # W

        # Calculated constants
        self.rated_omega = self.rated_speed * (2 * math.pi / 60)  # rad/s
        self.synchronous_speed = 120 * self.rated_frequency / (2 * self.pole_pairs)  # RPM
        self.synchronous_omega = self.synchronous_speed * (2 * math.pi / 60)  # rad/s
        self.rated_torque = self.rated_power / self.rated_omega  # N⋅m

        logger.info(
            f"Advanced generator initialized: {self.rated_power/1000:.0f}kW, "
            f"{self.rated_speed}RPM, {self.pole_pairs} pole pairs"
        )

    def update(self, shaft_speed: float, load_factor: float, dt: float) -> Dict[str, float]:
        """
        Update generator state with advanced electromagnetic modeling.

        Args:
            shaft_speed (float): Mechanical shaft speed (rad/s)
            load_factor (float): Electrical load factor (0-1)
            dt (float): Time step (s)

        Returns:
            dict: Generator state and performance metrics
        """
        self.angular_velocity = shaft_speed

        # Calculate slip
        self.slip = (self.synchronous_omega - shaft_speed) / self.synchronous_omega
        self.slip = max(min(self.slip, self.max_slip), -self.max_slip)  # Limit slip

        # Apply FOC control if enabled
        if self.foc_enabled:
            self.torque = self._calculate_foc_torque(load_factor, dt)
        else:
            # Fall back to conventional electromagnetic torque calculation
            self.torque = self._calculate_electromagnetic_torque(self.slip, load_factor)

        # Calculate mechanical power input
        self.mechanical_power = self.torque * shaft_speed

        # Calculate losses
        self._calculate_losses(shaft_speed, load_factor)

        # Calculate electrical power output
        self.electrical_power = max(0.0, self.mechanical_power - self.total_losses)

        # Calculate overall efficiency
        if self.mechanical_power > 0:
            self.efficiency = self.electrical_power / self.mechanical_power
        else:
            self.efficiency = 0.0

        # Calculate power factor
        self.power_factor = self._calculate_power_factor(load_factor)

        return self._get_state_dict()

    def _calculate_electromagnetic_torque(self, slip: float, load_factor: float) -> float:
        """
        Calculate realistic electromagnetic torque for KPP operation.

        Enhanced electromagnetic modeling including:
        - Saturation effects
        - Temperature-dependent resistance
        - Harmonic effects
        - Magnetic field variations
        - Realistic efficiency curves
        - Dynamic response characteristics

        Args:
            slip (float): Generator slip (per unit)
            load_factor (float): Load factor (0-1)

        Returns:
            float: Electromagnetic torque (N⋅m)
        """
        if abs(slip) < 1e-6:
            slip = 1e-6  # Avoid division by zero

        # Enhanced equivalent circuit calculations with realistic effects

        # Temperature-dependent resistance (copper resistance increases with temperature)
        temperature = 293.15 + (load_factor * 50.0)  # Simplified thermal model
        temp_factor = 1.0 + 0.00393 * (temperature - 293.15)  # Copper temperature coefficient
        stator_resistance_temp = self.stator_resistance * temp_factor
        rotor_resistance_temp = self.rotor_resistance * temp_factor

        # Effective rotor resistance with slip
        rotor_resistance_effective = rotor_resistance_temp / slip

        # Saturation effects on reactance
        saturation_factor = self._calculate_saturation_factor(load_factor)
        stator_reactance_sat = self.stator_reactance * saturation_factor
        rotor_reactance_sat = self.rotor_reactance * saturation_factor

        # Total impedance with enhanced modeling
        z_real = stator_resistance_temp + rotor_resistance_effective
        z_imag = stator_reactance_sat + rotor_reactance_sat
        z_magnitude = math.sqrt(z_real**2 + z_imag**2)

        # Enhanced current calculation with realistic effects
        voltage_per_phase = self.rated_voltage / math.sqrt(3)

        # Harmonic distortion factor (typical 3-5% in real generators)
        harmonic_factor = 1.0 + 0.04 * load_factor  # 4% harmonic distortion at full load

        # Magnetic field variations due to load
        field_variation = 1.0 + 0.1 * (load_factor - 0.5)  # ±5% field variation

        # Calculate current with enhanced effects
        current = (
            voltage_per_phase * load_factor * self.field_excitation * field_variation * harmonic_factor
        ) / z_magnitude

        # Enhanced torque calculation with realistic electromagnetic effects
        # Torque = (3 * P * I² * R₂) / (ω_s * s)
        # Where P = pole pairs, I = current, R₂ = rotor resistance, ω_s = synchronous speed, s = slip

        # Realistic electromagnetic torque
        electromagnetic_torque = (3 * self.pole_pairs * current**2 * rotor_resistance_temp) / (
            self.synchronous_omega * abs(slip)
        )

        # Apply efficiency curve effects
        efficiency_factor = self._estimate_efficiency(self.angular_velocity, load_factor)
        electromagnetic_torque *= efficiency_factor

        # Dynamic response characteristics (simplified)
        # Real generators have some inertia in torque response
        torque_response_factor = 1.0 - 0.05 * abs(slip)  # 5% reduction at high slip

        final_torque = electromagnetic_torque * torque_response_factor

        # Ensure reasonable limits
        final_torque = max(0.0, min(final_torque, self.rated_torque * 1.2))

        logger.debug(
            f"Enhanced electromagnetic torque: slip={slip:.4f}, load={load_factor:.2f}, "
            f"temp_factor={temp_factor:.3f}, saturation={saturation_factor:.3f}, "
            f"torque={final_torque:.1f}Nm"
        )

        return final_torque

        # Torque calculation
        torque_constant = (3 * self.pole_pairs) / self.synchronous_omega
        torque = torque_constant * (current**2 * self.rotor_resistance / slip)

        # Apply saturation effects
        saturation_factor = self._calculate_saturation_factor(current)
        torque *= saturation_factor

        return min(torque, self.rated_torque * 1.5)  # Limit maximum torque

    def _calculate_saturation_factor(self, current: float) -> float:
        """
        Calculate magnetic saturation effects.

        Args:
            current (float): Stator current (A)

        Returns:
            float: Saturation factor (0-1)
        """
        rated_current = self.rated_power / (math.sqrt(3) * self.rated_voltage * self.power_factor_target)
        current_ratio = current / rated_current

        # Simplified saturation curve
        if current_ratio < 0.8:
            return 1.0
        elif current_ratio < 1.2:
            return 1.0 - 0.2 * (current_ratio - 0.8) / 0.4
        else:
            return 0.8 - 0.3 * (current_ratio - 1.2)

    def _calculate_losses(self, speed: float, load_factor: float):
        """
        Calculate realistic comprehensive loss breakdown for KPP operation.

        Enhanced loss modeling including:
        - Temperature-dependent losses
        - Harmonic losses
        - Saturation effects on losses
        - Aging effects
        - Environmental factors
        - Realistic loss curves

        Args:
            speed (float): Shaft speed (rad/s)
            load_factor (float): Load factor (0-1)
        """
        # Enhanced iron losses with realistic effects
        speed_ratio = speed / self.rated_omega

        # Temperature effects on iron losses
        temperature = 293.15 + (load_factor * 50.0)  # Simplified thermal model
        temp_correction = 1.0 + 0.02 * (temperature - 293.15) / 100.0  # 2% per 100K

        # Harmonic effects on iron losses (higher harmonics increase losses)
        harmonic_factor = 1.0 + 0.15 * load_factor  # 15% increase at full load due to harmonics

        # Saturation effects on iron losses
        saturation_factor = self._calculate_saturation_factor(load_factor)
        saturation_correction = 1.0 + 0.1 * (1.0 - saturation_factor)  # Higher losses when saturated

        # Base iron losses with enhanced modeling
        base_iron_losses = self.iron_loss_constant * (speed_ratio**2)
        self.iron_losses = base_iron_losses * temp_correction * harmonic_factor * saturation_correction

        # Enhanced copper losses with realistic effects
        current_ratio = load_factor * self.field_excitation

        # Temperature-dependent copper resistance
        temp_factor = 1.0 + 0.00393 * (temperature - 293.15)  # Copper temperature coefficient

        # Harmonic effects on copper losses (skin effect and proximity effect)
        harmonic_copper_factor = 1.0 + 0.08 * load_factor  # 8% increase due to harmonics

        # Aging effects on copper losses (resistance increases over time)
        aging_factor = 1.0 + 0.05  # 5% increase due to aging (simplified)

        # Enhanced copper losses
        self.copper_losses = (
            (self.rated_power * 0.02)
            * (current_ratio**2)
            * self.copper_loss_factor
            * temp_factor
            * harmonic_copper_factor
            * aging_factor
        )

        # Enhanced mechanical losses with realistic effects
        # Bearing losses with temperature effects
        bearing_temp_factor = 1.0 + 0.01 * (temperature - 293.15) / 50.0  # 1% per 50K
        friction_loss = self.bearing_friction_coeff * speed * bearing_temp_factor

        # Windage losses with air density effects
        # Air density decreases with temperature
        air_density_factor = 273.15 / temperature  # Simplified air density correction
        windage_loss = self.windage_loss_coeff * (speed**2) * air_density_factor

        # Additional mechanical losses (seals, etc.)
        seal_losses = 0.02 * self.rated_power * load_factor  # 2% of rated power at full load

        self.mechanical_losses = friction_loss + windage_loss + seal_losses

        # Environmental effects on total losses
        # Humidity effects (simplified)
        humidity_factor = 1.0 + 0.02  # 2% increase due to humidity

        # Altitude effects (simplified)
        altitude_factor = 1.0 + 0.01  # 1% increase due to altitude

        # Calculate total losses with environmental corrections
        base_total_losses = self.iron_losses + self.copper_losses + self.mechanical_losses
        self.total_losses = base_total_losses * humidity_factor * altitude_factor

        # Ensure losses don't exceed mechanical power input
        mechanical_power = self.torque * speed
        self.total_losses = min(self.total_losses, mechanical_power * 0.95)  # Max 95% losses

        logger.debug(
            f"Enhanced losses: iron={self.iron_losses:.1f}W, copper={self.copper_losses:.1f}W, "
            f"mechanical={self.mechanical_losses:.1f}W, total={self.total_losses:.1f}W, "
            f"temp={temperature-273.15:.1f}°C"
        )

    def _calculate_power_factor(self, load_factor: float) -> float:
        """
        Calculate power factor based on loading conditions.

        Args:
            load_factor (float): Load factor (0-1)

        Returns:
            float: Power factor
        """
        # Power factor typically decreases at light loads
        if load_factor < 0.3:
            return self.power_factor_target * (0.6 + 0.4 * load_factor / 0.3)
        else:
            return self.power_factor_target

    def get_load_torque(self, speed: float, target_power: Optional[float] = None) -> float:
        """
        Calculate required load torque for given speed and power.

        Args:
            speed (float): Shaft speed (rad/s)
            target_power (float): Desired power output (W)

        Returns:
            float: Required load torque (N⋅m)
        """
        # Ensure we have a valid target power
        if target_power is None:
            power_to_use = self.rated_power
        else:
            power_to_use = target_power

        # Ensure target_power is valid
        if not isinstance(power_to_use, (int, float)) or power_to_use <= 0:
            power_to_use = self.rated_power

        if speed < 0.1:
            return 0.0

        # Account for efficiency
        estimated_efficiency = self._estimate_efficiency(speed, power_to_use / self.rated_power)

        # Ensure we have valid efficiency
        if estimated_efficiency is None or estimated_efficiency <= 0:
            estimated_efficiency = 0.85  # Default efficiency

        mechanical_power_needed = power_to_use / estimated_efficiency

        return mechanical_power_needed / speed

    def _estimate_efficiency(self, speed: float, load_factor: float) -> float:
        """
        Estimate efficiency for given operating conditions.

        Args:
            speed (float): Shaft speed (rad/s)
            load_factor (float): Load factor (0-1)

        Returns:
            float: Estimated efficiency
        """
        # Simplified efficiency estimation
        speed_ratio = speed / self.rated_omega

        # Base efficiency curve
        if load_factor < 0.2:
            base_eff = 0.75
        elif load_factor < 0.5:
            base_eff = 0.85 + 0.08 * (load_factor - 0.2) / 0.3
        elif load_factor < 1.0:
            base_eff = 0.93 - 0.01 * (load_factor - 0.5) / 0.5
        else:
            base_eff = 0.92 - 0.05 * (load_factor - 1.0)

        # Speed correction
        if speed_ratio < 0.8:
            speed_factor = 0.95
        elif speed_ratio < 1.2:
            speed_factor = 1.0
        else:
            speed_factor = 0.98

        return max(0.5, base_eff * speed_factor)

    def _get_state_dict(self) -> Dict[str, float]:
        """
        Get comprehensive generator state.

        Returns:
            dict: Complete generator state information
        """
        return {
            # Primary outputs
            "electrical_power": self.electrical_power,
            "mechanical_power": self.mechanical_power,
            "torque": self.torque,
            "efficiency": self.efficiency,
            "power_factor": self.power_factor,
            # Operating conditions
            "speed_rpm": self.angular_velocity * 60 / (2 * math.pi),
            "slip": self.slip,
            "field_excitation": self.field_excitation,
            # Loss breakdown
            "iron_losses": self.iron_losses,
            "copper_losses": self.copper_losses,
            "mechanical_losses": self.mechanical_losses,
            "total_losses": self.total_losses,
            # Electrical parameters
            "voltage": self.rated_voltage,
            "frequency": self.rated_frequency,
            "synchronous_speed_rpm": self.synchronous_speed,
        }

    def set_field_excitation(self, excitation: float):
        """
        Set generator field excitation.

        Args:
            excitation (float): Field excitation (per unit, 0-1.2)
        """
        self.field_excitation = max(self.min_excitation, min(1.2, excitation))
        logger.debug(f"Generator field excitation set to {self.field_excitation:.3f} pu")

    def reset(self):
        """
        Reset generator to initial state.
        """
        self.angular_velocity = 0.0
        self.slip = 0.0
        self.torque = 0.0
        self.electrical_power = 0.0
        self.mechanical_power = 0.0
        self.efficiency = 0.0
        self.power_factor = 0.0
        self.field_excitation = 1.0

        self.iron_losses = 0.0
        self.copper_losses = 0.0
        self.mechanical_losses = 0.0
        self.total_losses = 0.0

        logger.info("Advanced generator state reset")

    def set_user_load(self, load_torque: float):
        """
        Set the user-specified load torque.

        Args:
            load_torque (float): User load torque in N⋅m
        """
        # Store the user load torque
        self.user_load_torque = load_torque
        logger.info(f"Generator user load set to {load_torque:.2f} N⋅m")

    def get_user_load(self) -> float:
        """
        Get the current user-specified load torque.

        Returns:
            float: Current user load torque in N⋅m
        """
        return getattr(self, "user_load_torque", 0.0)

    def _calculate_foc_torque(self, torque_demand: float, dt: float) -> float:
        """
        Calculate electromagnetic torque using Field-Oriented Control (FOC).

        FOC decouples torque and flux control by regulating d-axis and q-axis currents.
        This provides superior dynamic response and torque control accuracy.

        Args:
            torque_demand (float): Desired torque as fraction of rated (0-1)
            dt (float): Time step for PI controllers (s)

        Returns:
            float: Controlled electromagnetic torque (N⋅m)
        """
        # Target torque
        target_torque = torque_demand * self.rated_torque

        # Current torque feedback (simplified from actual measurements)
        actual_torque = self.torque

        # Torque error for PI controller
        torque_error = target_torque - actual_torque

        # PI control for q-axis current (torque producing current)
        # P term
        q_current_p = self.torque_controller_kp * torque_error

        # I term with anti-windup
        self.torque_error_integral += torque_error * dt
        # Anti-windup: limit integral term
        max_integral = self.rated_torque / self.torque_controller_ki
        self.torque_error_integral = max(-max_integral, min(max_integral, self.torque_error_integral))
        q_current_i = self.torque_controller_ki * self.torque_error_integral

        # Calculate q-axis current command
        self.q_axis_current = q_current_p + q_current_i

        # Limit q-axis current to rated values
        max_q_current = self.rated_power / (math.sqrt(3) * self.rated_voltage)
        self.q_axis_current = max(-max_q_current, min(max_q_current, self.q_axis_current))

        # D-axis current control for flux regulation
        target_flux = self.flux_reference
        # Simplified flux feedback (in real system would use flux observer)
        actual_flux = self.field_excitation

        flux_error = target_flux - actual_flux

        # PI control for d-axis current (flux producing current)
        d_current_p = self.flux_controller_kp * flux_error

        self.flux_error_integral += flux_error * dt
        max_flux_integral = 1.0 / self.flux_controller_ki
        self.flux_error_integral = max(-max_flux_integral, min(max_flux_integral, self.flux_error_integral))
        d_current_i = self.flux_controller_ki * self.flux_error_integral

        self.d_axis_current = d_current_p + d_current_i

        # Limit d-axis current
        max_d_current = max_q_current * 0.3  # Typically much smaller than q-axis
        self.d_axis_current = max(-max_d_current, min(max_d_current, self.d_axis_current))

        # Calculate torque from FOC currents
        # For PM synchronous motor: T = (3/2) * P * λ_pm * i_q
        # Where P is pole pairs, λ_pm is PM flux linkage, i_q is q-axis current
        torque_constant = (3.0 / 2.0) * self.pole_pairs * 0.5  # Simplified torque constant
        foc_torque = torque_constant * self.q_axis_current * self.field_excitation

        # Apply current limits and saturation
        total_current = math.sqrt(self.d_axis_current**2 + self.q_axis_current**2)
        if total_current > max_q_current:
            # Current limiting - reduce both currents proportionally
            scale_factor = max_q_current / total_current
            self.d_axis_current *= scale_factor
            self.q_axis_current *= scale_factor
            foc_torque *= scale_factor

        # Update field excitation based on d-axis current
        self.field_excitation = max(self.min_excitation, min(1.2, 1.0 + self.d_axis_current * 0.2))

        logger.debug(
            f"FOC Control: target_T={target_torque:.1f}Nm, actual_T={foc_torque:.1f}Nm, "
            f"i_d={self.d_axis_current:.2f}A, i_q={self.q_axis_current:.2f}A, "
            f"flux={self.field_excitation:.3f}pu"
        )

        return foc_torque

    def set_foc_parameters(
        self, torque_kp: Optional[float] = None, torque_ki: Optional[float] = None, flux_kp: Optional[float] = None, flux_ki: Optional[float] = None
    ):
        """
        Set FOC controller parameters for tuning.

        Args:
            torque_kp: Torque controller proportional gain
            torque_ki: Torque controller integral gain
            flux_kp: Flux controller proportional gain
            flux_ki: Flux controller integral gain
        """
        if torque_kp is not None:
            self.torque_controller_kp = torque_kp
        if torque_ki is not None:
            self.torque_controller_ki = torque_ki
        if flux_kp is not None:
            self.flux_controller_kp = flux_kp
        if flux_ki is not None:
            self.flux_controller_ki = flux_ki

        logger.info(
            f"FOC parameters updated: torque_kp={self.torque_controller_kp}, "
            f"torque_ki={self.torque_controller_ki}, flux_kp={self.flux_controller_kp}, "
            f"flux_ki={self.flux_controller_ki}"
        )

    def enable_foc(self, enabled: bool = True):
        """Enable or disable Field-Oriented Control."""
        self.foc_enabled = enabled
        if enabled:
            logger.info("Field-Oriented Control (FOC) enabled")
        else:
            logger.info("Field-Oriented Control (FOC) disabled - using conventional control")

    def get_foc_status(self) -> Dict[str, float]:
        """Get FOC control status and measurements."""
        return {
            "foc_enabled": self.foc_enabled,
            "d_axis_current": self.d_axis_current,
            "q_axis_current": self.q_axis_current,
            "total_current": math.sqrt(self.d_axis_current**2 + self.q_axis_current**2),
            "flux_reference": self.flux_reference,
            "field_excitation": self.field_excitation,
            "torque_error_integral": self.torque_error_integral,
            "flux_error_integral": self.flux_error_integral,
        }


def create_kmp_generator(config: Optional[Dict[str, Any]] = None) -> AdvancedGenerator:
    """
    Create a standard KMP generator with realistic parameters.

    Args:
        config (dict): Optional configuration overrides

    Returns:
        AdvancedGenerator: Configured generator instance
    """
    default_config = {
        "rated_power": 530000.0,  # 530 kW
        "rated_voltage": 480.0,  # 480V line-to-line
        "rated_frequency": 50.0,  # 50 Hz
        "rated_speed": 375.0,  # 375 RPM (matches flywheel target)
        "pole_pairs": 4,  # 8-pole machine
        "efficiency_at_rated": 0.94,  # 94% efficiency at rated conditions
        "power_factor": 0.92,  # 92% power factor
    }

    if config:
        default_config.update(config)

    generator = AdvancedGenerator(default_config)
    logger.info(
        f"Created KMP generator: {default_config['rated_power']/1000:.0f}kW, " f"{default_config['rated_speed']}RPM"
    )

    return generator
