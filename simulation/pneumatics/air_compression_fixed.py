"""
Phase 1.1: Core Air Compression Module for KPP Pneumatic System

This module implements the comprehensive air compression and storage system
based on the detailed physics described in pneumatics-upgrade.md.

Key Features:
- Realistic compressor model with power consumption and efficiency curves
- Pressure tank with ideal gas law implementation
- Heat generation and cooling during compression
- Variable pressure ratios for different depths
"""

import math
import logging
from typing import Dict, Tuple, Optional
from dataclasses import dataclass
from utils.logging_setup import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

@dataclass
class CompressorSpec:
    """Compressor specifications and operating characteristics."""
    power_rating: float = 4200.0  # Watts (4.2 kW reference from document)
    efficiency: float = 0.85  # Compression efficiency
    max_pressure: float = 400000.0  # Pa (4 atm absolute)
    max_flow_rate: float = 0.05  # m³/s at standard conditions
    heat_removal_efficiency: float = 0.7  # Fraction of compression heat removed

@dataclass
class PressureTankSpec:
    """Pressure tank specifications."""
    volume: float = 1.0  # m³
    max_pressure: float = 450000.0  # Pa (4.5 atm safety limit)
    min_operating_pressure: float = 150000.0  # Pa (1.5 atm minimum)
    safety_margin: float = 1.1  # Safety factor for pressure calculations

class AirCompressionSystem:
    """
    Comprehensive air compression system implementing realistic physics.
    
    This system models:
    - Electric compressor with power input and efficiency
    - Heat generation during compression with cooling
    - Pressure tank storage with ideal gas law
    - Energy calculations for compression work
    """
    
    def __init__(self, 
                 compressor_spec: Optional[CompressorSpec] = None,
                 tank_spec: Optional[PressureTankSpec] = None,
                 ambient_temperature: float = 293.15,  # K (20°C)
                 ambient_pressure: float = 101325.0):  # Pa (1 atm)
        """
        Initialize the air compression system.
        
        Args:
            compressor_spec: Compressor specifications
            tank_spec: Pressure tank specifications
            ambient_temperature: Ambient temperature in Kelvin
            ambient_pressure: Ambient pressure in Pascals
        """
        self.compressor = compressor_spec or CompressorSpec()
        self.tank = tank_spec or PressureTankSpec()
        self.ambient_temperature = ambient_temperature
        self.ambient_pressure = ambient_pressure
        
        # Gas constant for air (R_specific = R/M_air)
        self.gas_constant = 287.0  # J/(kg·K) for dry air
        
        # Adiabatic index for air
        self.gamma = 1.4
        
        # Current system state
        self.tank_pressure = ambient_pressure  # Pa
        self.tank_temperature = ambient_temperature  # K
        self.compressor_running = False
        self.air_mass_in_tank = self._calculate_initial_air_mass()
        
        # Energy tracking
        self.total_energy_consumed = 0.0  # J
        self.total_compression_work = 0.0  # J
        self.total_heat_generated = 0.0  # J
        self.total_heat_removed = 0.0  # J
        
        logger.info(f"AirCompressionSystem initialized: {self.compressor.power_rating/1000:.1f} kW compressor, "
                   f"{self.tank.volume:.2f} m³ tank")
    
    def _calculate_initial_air_mass(self) -> float:
        """Calculate initial mass of air in tank at ambient conditions."""
        # Using ideal gas law: PV = nRT = (m/M)RT
        # Rearranged: m = PV/(R_specific * T)
        return (self.ambient_pressure * self.tank.volume) / (self.gas_constant * self.ambient_temperature)
    
    def get_required_injection_pressure(self, depth: float) -> float:
        """
        Calculate minimum pressure required for air injection at given depth.
        
        Args:
            depth: Water depth in meters
            
        Returns:
            Required injection pressure in Pa
        """
        # Hydrostatic pressure at depth
        water_density = 1000.0  # kg/m³
        gravity = 9.81  # m/s²
        hydrostatic_pressure = water_density * gravity * depth
        
        # Add ambient pressure and valve/flow losses margin
        valve_losses = 10000.0  # Pa (10 kPa margin for valve resistance)
        
        required_pressure = self.ambient_pressure + hydrostatic_pressure + valve_losses
        return required_pressure
    
    def calculate_isothermal_compression_work(self, volume_at_ambient: float, 
                                            target_pressure: float) -> float:
        """
        Calculate theoretical isothermal compression work.
        
        Args:
            volume_at_ambient: Volume of air at ambient conditions (m³)
            target_pressure: Target pressure for compression (Pa)
            
        Returns:
            Compression work in Joules
        """
        pressure_ratio = target_pressure / self.ambient_pressure
        work = (self.ambient_pressure * volume_at_ambient * 
                math.log(pressure_ratio))
        return work
    
    def calculate_adiabatic_compression_work(self, volume_at_ambient: float,
                                           target_pressure: float) -> float:
        """
        Calculate adiabatic compression work using correct formula.
        
        Args:
            volume_at_ambient: Volume of air at ambient conditions (m³)
            target_pressure: Target pressure for compression (Pa)
            
        Returns:
            Compression work in Joules
        """
        pressure_ratio = target_pressure / self.ambient_pressure
        # Correct adiabatic work formula: W = (P1*V1*γ/(γ-1)) * (1 - (1/PR)^((γ-1)/γ))
        work = ((self.ambient_pressure * volume_at_ambient * self.gamma) / (self.gamma - 1) * 
                (1 - (1/pressure_ratio)**((self.gamma - 1)/self.gamma)))
        return work
    
    def calculate_actual_compression_work(self, volume_at_ambient: float,
                                        target_pressure: float,
                                        heat_removal_fraction: Optional[float] = None) -> Tuple[float, float, float]:
        """
        Calculate actual compression work considering heat removal.
        
        Args:
            volume_at_ambient: Volume of air at ambient conditions (m³)
            target_pressure: Target pressure for compression (Pa)
            heat_removal_fraction: Fraction of heat removed (None uses compressor default)
            
        Returns:
            Tuple of (actual_work, heat_generated, heat_removed) in Joules
        """
        if heat_removal_fraction is None:
            heat_removal_fraction = self.compressor.heat_removal_efficiency
        
        # Calculate isothermal and adiabatic work
        isothermal_work = self.calculate_isothermal_compression_work(volume_at_ambient, target_pressure)
        adiabatic_work = self.calculate_adiabatic_compression_work(volume_at_ambient, target_pressure)
        
        # Actual work is between isothermal and adiabatic based on heat removal
        actual_work = isothermal_work + (1 - heat_removal_fraction) * (adiabatic_work - isothermal_work)
        
        # Heat generated and removed
        heat_generated = adiabatic_work - isothermal_work
        heat_removed = heat_removal_fraction * heat_generated
        
        return actual_work, heat_generated, heat_removed
    
    def update_tank_pressure_after_compression(self, air_volume_added: float,
                                             compression_pressure: float) -> None:
        """
        Update tank pressure after adding compressed air.
        
        Args:
            air_volume_added: Volume of air added at ambient conditions (m³)
            compression_pressure: Pressure of compressed air (Pa)
        """
        # Calculate mass of air added
        air_mass_added = (self.ambient_pressure * air_volume_added) / (self.gas_constant * self.ambient_temperature)
        
        # Add to tank
        self.air_mass_in_tank += air_mass_added
        
        # Calculate new pressure using ideal gas law
        # Assuming tank temperature stays near ambient due to heat removal
        self.tank_pressure = (self.air_mass_in_tank * self.gas_constant * self.tank_temperature) / self.tank.volume
        
        logger.debug(f"Tank pressure updated: {self.tank_pressure/1000:.1f} kPa after adding {air_volume_added*1000:.1f} L")
    
    def can_supply_pressure(self, required_pressure: float) -> bool:
        """
        Check if tank can supply required pressure.
        
        Args:
            required_pressure: Required pressure in Pa
            
        Returns:
            True if tank pressure is sufficient
        """
        return self.tank_pressure >= required_pressure * self.tank.safety_margin
    
    def consume_air_from_tank(self, volume_at_tank_pressure: float) -> bool:
        """
        Remove air from tank during injection.
        
        Args:
            volume_at_tank_pressure: Volume of air consumed at tank pressure (m³)
            
        Returns:
            True if air was successfully consumed
        """
        if volume_at_tank_pressure <= 0:
            return True
        
        # Calculate mass of air removed
        air_mass_removed = (self.tank_pressure * volume_at_tank_pressure) / (self.gas_constant * self.tank_temperature)
        
        if air_mass_removed > self.air_mass_in_tank:
            logger.warning("Insufficient air in tank for consumption request")
            return False
        
        # Remove air and update pressure
        self.air_mass_in_tank -= air_mass_removed
        self.tank_pressure = (self.air_mass_in_tank * self.gas_constant * self.tank_temperature) / self.tank.volume
        
        logger.debug(f"Consumed {volume_at_tank_pressure*1000:.1f} L from tank, "
                    f"pressure now {self.tank_pressure/1000:.1f} kPa")
        return True
    
    def calculate_compressor_power_for_flow(self, volume_flow_rate: float,
                                          target_pressure: float) -> float:
        """
        Calculate electrical power required for given flow rate and pressure.
        
        Args:
            volume_flow_rate: Air flow rate at ambient conditions (m³/s)
            target_pressure: Target compression pressure (Pa)
            
        Returns:
            Required electrical power in Watts
        """
        # Calculate compression work per unit time
        work_per_second, _, _ = self.calculate_actual_compression_work(volume_flow_rate, target_pressure)
        
        # Account for compressor efficiency
        electrical_power = work_per_second / self.compressor.efficiency
        
        return electrical_power
    
    def get_maximum_flow_rate_at_pressure(self, target_pressure: float) -> float:
        """
        Calculate maximum flow rate at given pressure within power limits.
        
        Args:
            target_pressure: Target compression pressure (Pa)
            
        Returns:
            Maximum flow rate in m³/s at ambient conditions
        """
        # Binary search for maximum flow rate
        min_flow = 0.0
        max_flow = self.compressor.max_flow_rate
        tolerance = 1e-6
        
        while max_flow - min_flow > tolerance:
            test_flow = (min_flow + max_flow) / 2
            required_power = self.calculate_compressor_power_for_flow(test_flow, target_pressure)
            
            if required_power <= self.compressor.power_rating:
                min_flow = test_flow
            else:
                max_flow = test_flow
        
        return min_flow
    
    def run_compressor(self, dt: float, target_pressure: Optional[float] = None) -> Dict[str, float]:
        """
        Run compressor for given time step.
        
        Args:
            dt: Time step in seconds
            target_pressure: Target pressure (uses tank max if None)
            
        Returns:
            Dictionary with compression results
        """
        if target_pressure is None:
            target_pressure = self.tank.max_pressure * 0.9  # 90% of max as default target
        
        # Check if compressor should run
        if self.tank_pressure >= target_pressure:
            self.compressor_running = False
            return {
                'running': False,
                'power_consumed': 0.0,
                'air_compressed': 0.0,
                'work_done': 0.0,
                'heat_generated': 0.0,
                'tank_pressure': self.tank_pressure
            }
        
        self.compressor_running = True
        
        # Calculate maximum flow rate at target pressure
        max_flow_rate = self.get_maximum_flow_rate_at_pressure(target_pressure)
        
        # Volume compressed in this time step
        volume_compressed = max_flow_rate * dt
        
        # Calculate compression work and energy
        work_done, heat_generated, heat_removed = self.calculate_actual_compression_work(
            volume_compressed, target_pressure)
        
        # Electrical power consumed
        power_consumed = work_done / dt / self.compressor.efficiency
        
        # Update tank pressure
        self.update_tank_pressure_after_compression(volume_compressed, target_pressure)
        
        # Update energy tracking
        self.total_energy_consumed += power_consumed * dt
        self.total_compression_work += work_done
        self.total_heat_generated += heat_generated
        self.total_heat_removed += heat_removed
        
        logger.debug(f"Compressor running: {power_consumed/1000:.2f} kW, "
                    f"compressed {volume_compressed*1000:.1f} L, "
                    f"tank pressure {self.tank_pressure/1000:.1f} kPa")
        
        return {
            'running': True,
            'power_consumed': power_consumed,
            'air_compressed': volume_compressed,
            'work_done': work_done,
            'heat_generated': heat_generated,
            'tank_pressure': self.tank_pressure,
            'flow_rate': max_flow_rate
        }
    
    def get_system_status(self) -> Dict[str, float]:
        """Get comprehensive system status."""
        return {
            'tank_pressure_pa': self.tank_pressure,
            'tank_pressure_bar': self.tank_pressure / 100000.0,
            'tank_pressure_atm': self.tank_pressure / 101325.0,
            'air_mass_kg': self.air_mass_in_tank,
            'compressor_running': self.compressor_running,
            'total_energy_consumed_kwh': self.total_energy_consumed / 3600000.0,
            'total_compression_work_kj': self.total_compression_work / 1000.0,
            'compression_efficiency': (self.total_compression_work / self.total_energy_consumed 
                                     if self.total_energy_consumed > 0 else 0.0),
            'tank_fill_percentage': min(100.0, (self.tank_pressure / self.tank.max_pressure) * 100.0)
        }
    
    def reset_system(self) -> None:
        """Reset system to initial conditions."""
        self.tank_pressure = self.ambient_pressure
        self.tank_temperature = self.ambient_temperature
        self.compressor_running = False
        self.air_mass_in_tank = self._calculate_initial_air_mass()
        self.total_energy_consumed = 0.0
        self.total_compression_work = 0.0
        self.total_heat_generated = 0.0
        self.total_heat_removed = 0.0
        
        logger.info("Air compression system reset to initial conditions")


def create_standard_kpp_compressor() -> AirCompressionSystem:
    """Create a standard KPP air compression system with realistic parameters."""
    compressor_spec = CompressorSpec(
        power_rating=4200.0,  # 4.2 kW from document
        efficiency=0.85,
        max_pressure=300000.0,  # 3 atm for ~20m depth capability
        max_flow_rate=0.05,  # 50 L/s
        heat_removal_efficiency=0.75
    )
    
    tank_spec = PressureTankSpec(
        volume=0.5,  # 500L tank
        max_pressure=350000.0,  # 3.5 atm safety limit
        min_operating_pressure=150000.0,  # 1.5 atm minimum
        safety_margin=1.1
    )
    
    return AirCompressionSystem(compressor_spec, tank_spec)
