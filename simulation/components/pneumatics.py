"""
Pneumatic System module.
Handles air injection, venting, and compressor logic for the KPP simulator.
Includes Phase 5 advanced thermodynamic modeling and thermal boost capabilities.
"""

from typing import Optional, Union
import logging
from utils.logging_setup import setup_logging
# Phase 5 imports - Advanced thermodynamic modeling
from simulation.pneumatics.thermodynamics import (
    ThermodynamicProperties, CompressionThermodynamics, 
    ExpansionThermodynamics, ThermalBuoyancyCalculator,
    AdvancedThermodynamics
)
from simulation.pneumatics.heat_exchange import (
    WaterThermalReservoir, IntegratedHeatExchange
)

setup_logging()
logger = logging.getLogger(__name__)

class PneumaticSystem:
    """
    Represents the compressed air system for floaters.
    Handles injection, venting, and compressor logic for the KPP simulator.
    
    Phase 5 enhancements:
    - Advanced thermodynamic modeling
    - Heat exchange with water reservoir
    - Thermal buoyancy boost calculations
    - Complete thermodynamic cycle analysis
    """
    def __init__(self,
                 tank_pressure: float = 5.0,  # bar
                 tank_volume: float = 0.1,    # m^3
                 compressor_power: float = 5.0,  # kW
                 target_pressure: float = 5.0,
                 # Phase 5 parameters
                 enable_thermodynamics: bool = True,
                 water_temperature: float = 293.15,  # K
                 expansion_mode: str = 'mixed'):
        """
        Initialize the pneumatic system.

        Args:
            tank_pressure (float): Initial tank pressure (bar).
            tank_volume (float): Tank volume (m^3).
            compressor_power (float): Compressor power (kW).
            target_pressure (float): Target pressure to maintain (bar).
            enable_thermodynamics (bool): Enable Phase 5 thermodynamic modeling.
            water_temperature (float): Water temperature for thermal calculations (K).
            expansion_mode (str): Expansion mode ('adiabatic', 'isothermal', 'mixed').
        """
        # All pneumatic state is encapsulated here for clarity and future extension.
        self.initial_pressure = tank_pressure
        self.tank_pressure = tank_pressure
        self.tank_volume = tank_volume
        self.compressor_power = compressor_power
        self.target_pressure = target_pressure
        self.compressor_on = False
        self.energy_used = 0.0
        
        # Phase 5: Advanced thermodynamic capabilities
        self.enable_thermodynamics = enable_thermodynamics
        if self.enable_thermodynamics:
            self.thermo_props = ThermodynamicProperties()
            self.compression_thermo = CompressionThermodynamics()
            self.expansion_thermo = ExpansionThermodynamics(water_temperature)
            self.thermal_buoyancy = ThermalBuoyancyCalculator()
            self.advanced_thermo = AdvancedThermodynamics(water_temperature, expansion_mode)
            self.water_reservoir = WaterThermalReservoir()
            self.heat_exchange = IntegratedHeatExchange()
            
            # Thermodynamic state tracking
            self.thermal_energy_boost = 0.0
            self.compression_heat_generated = 0.0
            self.thermal_efficiency_factor = 1.0
            
            logger.info(f"Phase 5 thermodynamics enabled: water={water_temperature:.1f}K, mode={expansion_mode}")
        
        logger.info(f"PneumaticSystem initialized: pressure={tank_pressure} bar, volume={tank_volume} m^3")

    def trigger_injection(self, floater) -> bool:
        """
        Trigger the air injection process for a floater.

        Args:
            floater: The Floater object to start filling.

        Returns:
            bool: True if injection was successfully started, False otherwise.
        """
        # Simplified check for available pressure
        if self.tank_pressure > 1.5: # Some threshold above atmospheric
            floater.start_filling()
            # Model a pressure drop for the injection
            pressure_drop = floater.volume / self.tank_volume * 0.5 # Simplified model
            self.tank_pressure -= pressure_drop
            logger.info(f"Triggered injection for a floater. Tank pressure dropped to {self.tank_pressure:.2f} bar.")
            return True
        else:
            logger.warning("Injection failed: tank pressure too low.")
            return False

    def vent_air(self, vent_duration: Optional[float] = None, target_pressure: Optional[float] = None, floater=None):
        """
        Vent air from system or floater.
        
        Args:
            vent_duration: Duration of venting (s) - for system venting
            target_pressure: Target pressure after venting (Pa) - for system venting  
            floater: Floater object to vent (legacy support)
            
        Returns:
            dict: Venting results or None for floater venting
        """
        # Legacy floater venting support
        if floater is not None:
            floater.set_filled(False)
            logger.info("Vented air from Floater at top.")
            return {'legacy': True}
        
        # New system venting functionality
        if vent_duration is None or target_pressure is None:
            return {'volume_vented': 0.0, 'final_pressure': self.tank_pressure * 100000.0}
            
        initial_pressure = self.tank_pressure * 100000.0  # Convert to Pa
        
        # Calculate volume vented based on duration and pressure difference
        max_vent_rate = 0.005  # m³/s typical vent rate
        volume_vented = vent_duration * max_vent_rate
        
        # Calculate pressure reduction
        pressure_reduction = (volume_vented / self.tank_volume) * initial_pressure * 0.4
        final_pressure = max(target_pressure, initial_pressure - pressure_reduction)
        
        # Update tank pressure
        self.tank_pressure = final_pressure / 100000.0  # Convert back to bar
        
        logger.info(f"Air vented: {volume_vented:.4f} m³, pressure: {final_pressure/100000:.2f} bar")
        
        return {
            'volume_vented': volume_vented,
            'final_pressure': final_pressure,
            'pressure_reduction': pressure_reduction
        }

    def calculate_thermal_buoyancy_boost(self, air_volume: float, air_temperature: float, 
                                       water_temperature: float, depth: float) -> float:
        """
        Calculate thermal buoyancy boost using Phase 5 thermodynamics.
        
        Args:
            air_volume: Volume of air (m³)
            air_temperature: Air temperature (K)
            water_temperature: Water temperature (K)
            depth: Water depth (m)
            
        Returns:
            float: Additional buoyant force from thermal effects (N)
        """
        if not self.enable_thermodynamics:
            return 0.0
        
        try:
            # Temperature differential effect
            temp_ratio = air_temperature / water_temperature
            
            # Pressure at depth
            water_pressure = 101325.0 + 1000 * 9.81 * depth
            
            # Thermal expansion effect on buoyancy
            thermal_expansion_factor = (temp_ratio - 1.0) * 0.1  # Simplified model
            base_buoyancy = air_volume * 1000 * 9.81  # Base buoyant force
            thermal_boost = base_buoyancy * thermal_expansion_factor
            
            return max(0.0, thermal_boost)
            
        except Exception as e:
            logger.warning(f"Thermal buoyancy boost calculation failed: {e}")
            return 0.0

    def get_thermodynamic_cycle_analysis(self, air_volume: float, ascent_time: float) -> dict:
        """
        Perform complete thermodynamic cycle analysis for optimization.
        
        Args:
            air_volume: Air volume for analysis (m³)
            ascent_time: Time for ascent phase (s)
            
        Returns:
            dict: Complete thermodynamic cycle results
        """
        if not self.enable_thermodynamics:
            return {}
        
        try:
            # Convert bar to Pa
            injection_pressure = self.tank_pressure * 100000.0
            surface_pressure = 101325.0
            injection_temp = 290.15  # Assume slightly cooled air
            base_buoyancy = 78.5    # Approximate base buoyancy force
            
            return self.advanced_thermo.complete_thermodynamic_cycle(
                air_volume, injection_pressure, surface_pressure,
                injection_temp, ascent_time, base_buoyancy)
                
        except Exception as e:
            logger.warning(f"Thermodynamic cycle analysis failed: {e}")
            return {}

    def update(self, dt: float) -> None:
        """
        Update compressor state and energy usage.
        Args:
            dt (float): Time step (s).
        """
        # Automatically switch compressor ON if pressure is below target
        if self.tank_pressure < self.target_pressure and not self.compressor_on:
            self.compressor_on = True
            logger.info("Compressor turned ON (pressure below target).")
        # Automatically switch compressor OFF if pressure is at or above target
        if self.tank_pressure >= self.target_pressure and self.compressor_on:
            self.compressor_on = False
            logger.info("Compressor reached target pressure and turned OFF.")
        # If compressor is on and pressure is below target, increase pressure gradually
        if self.compressor_on:
            # Simplified pressure increase model
            pressure_increase = (self.compressor_power / self.tank_volume) * dt * 0.1
            self.tank_pressure += pressure_increase
            self.energy_used += self.compressor_power * dt
            logger.debug(f"Compressor running: pressure={self.tank_pressure:.2f} bar, energy_used={self.energy_used:.2f} kJ")
        # Clamp pressure to target if slightly exceeded due to increment
        if self.tank_pressure > self.target_pressure:
            self.tank_pressure = self.target_pressure

    def reset(self):
        """
        Resets the pneumatic system to its initial state.
        """
        self.tank_pressure = self.initial_pressure
        logger.info("PneumaticSystem state has been reset.")

    def calculate_compression_work(self, initial_pressure: float, final_pressure: float, volume: float) -> float:
        """
        Calculate work required for air compression.
        
        Args:
            initial_pressure: Initial air pressure (Pa)
            final_pressure: Final compressed pressure (Pa)
            volume: Air volume being compressed (m³)
            
        Returns:
            float: Compression work required (J)
        """
        if not self.enable_thermodynamics:
            # Simple approximation without thermodynamics
            return volume * (final_pressure - initial_pressure)
        
        try:
            return self.compression_thermo.isothermal_compression_work(
                initial_pressure, final_pressure, volume)
        except Exception as e:
            logger.warning(f"Compression work calculation failed: {e}")
            # Fallback calculation
            return volume * (final_pressure - initial_pressure)

    def inject_air(self, target_depth: float, water_pressure: float, duration: float) -> dict:
        """
        Inject air at specified depth and pressure conditions.
        
        Args:
            target_depth: Target depth for injection (m)
            water_pressure: Water pressure at target depth (Pa)
            duration: Injection duration (s)
            
        Returns:
            dict: Injection results with volume_injected and pressure
        """
        # Calculate injection pressure (must overcome water pressure)
        injection_pressure = max(water_pressure * 1.1, self.tank_pressure * 100000.0)
        
        # Calculate volume injected based on tank capacity and duration
        max_flow_rate = 0.01  # m³/s typical flow rate
        volume_injected = min(duration * max_flow_rate, self.tank_volume * 0.5)
        
        # Update tank pressure (simplified model)
        pressure_drop = (volume_injected / self.tank_volume) * 0.3
        self.tank_pressure = max(1.0, self.tank_pressure - pressure_drop)
        
        logger.info(f"Air injection: {volume_injected:.4f} m³ at {injection_pressure/100000:.2f} bar")
        
        return {
            'volume_injected': volume_injected,
            'pressure': injection_pressure,
            'tank_pressure_after': self.tank_pressure
        }

    def calculate_buoyancy_change(self, air_volume: float, depth: float, water_temperature: float) -> dict:
        """
        Calculate buoyancy changes due to air injection and expansion.
        
        Args:
            air_volume: Volume of air injected (m³)
            depth: Water depth (m)
            water_temperature: Water temperature (K)
            
        Returns:
            dict: Buoyancy analysis results
        """
        water_pressure = 101325.0 + 1000 * 9.81 * depth  # Hydrostatic pressure
        water_density = 1000.0  # kg/m³
        
        # Calculate volume expansion as air rises
        surface_pressure = 101325.0
        pressure_ratio = water_pressure / surface_pressure
        expanded_volume = air_volume * pressure_ratio
        
        # Calculate buoyancy force
        buoyancy_force = expanded_volume * water_density * 9.81
        
        # Add thermal effects if enabled
        thermal_boost = 0.0
        if self.enable_thermodynamics:
            try:
                # Create a mock floater-like object for thermal calculation
                class MockFloater:
                    def __init__(self, vol, temp):
                        self.air_volume = vol
                        self.air_temperature = water_temperature + 5.0  # Slightly warmed
                
                mock_floater = MockFloater(air_volume, water_temperature)
                thermal_boost = self.calculate_thermal_buoyancy_boost(
                    air_volume, mock_floater.air_temperature, water_temperature, depth)
            except Exception as e:
                logger.warning(f"Thermal boost calculation failed: {e}")
        
        return {
            'buoyancy_force': buoyancy_force + thermal_boost,
            'volume_expansion': expanded_volume - air_volume,
            'thermal_boost': thermal_boost,
            'pressure_ratio': pressure_ratio
        }

    def analyze_thermodynamic_cycle(self, initial_pressure: float, final_pressure: float,
                                  initial_temperature: float, expansion_ratio: float) -> dict:
        """
        Analyze complete thermodynamic cycle for efficiency calculations.
        
        Args:
            initial_pressure: Initial cycle pressure (Pa)
            final_pressure: Final cycle pressure (Pa)
            initial_temperature: Initial temperature (K)
            expansion_ratio: Volume expansion ratio
            
        Returns:
            dict: Thermodynamic cycle analysis results
        """
        if not self.enable_thermodynamics:
            return {
                'efficiency': 0.3,  # Default efficiency
                'net_work': 1000.0,  # Default work (J)
                'heat_input': 3333.0,
                'heat_output': 2333.0
            }
        
        try:
            # Use advanced thermodynamics for cycle analysis
            volume = 0.01  # Typical volume for analysis
            ascent_time = 30.0  # Typical ascent time
            base_buoyancy = 78.5  # Typical buoyancy force
            
            cycle_results = self.advanced_thermo.complete_thermodynamic_cycle(
                volume, initial_pressure, final_pressure,
                initial_temperature, ascent_time, base_buoyancy)
            
            # Extract key results
            return {
                'efficiency': cycle_results.get('thermal_efficiency', 0.35),
                'net_work': cycle_results.get('net_work', 1200.0),
                'heat_input': cycle_results.get('heat_input', 3500.0),
                'heat_output': cycle_results.get('heat_output', 2300.0),
                'expansion_work': cycle_results.get('expansion_work', 800.0),
                'compression_work': cycle_results.get('compression_work', -400.0)
            }
            
        except Exception as e:
            logger.warning(f"Thermodynamic cycle analysis failed: {e}")
            return {
                'efficiency': 0.3,
                'net_work': 1000.0,
                'heat_input': 3333.0,
                'heat_output': 2333.0
            }
