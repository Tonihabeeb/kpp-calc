"""
Power Electronics and Grid Interface System for Phase 3 Implementation
Models inverters, transformers, grid synchronization, and power conditioning.
"""

import math
import logging
from typing import Dict, Tuple, Optional, Any
import numpy as np

logger = logging.getLogger(__name__)


class PowerElectronics:
    """
    Power electronics system modeling inverters, transformers, and grid interface.
    
    Models:
    - AC-DC-AC conversion (generator to grid)
    - Power factor correction
    - Voltage regulation
    - Grid synchronization
    - Harmonic filtering
    - Protection systems
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize power electronics system.
        
        Args:
            config (dict): Power electronics configuration
        """
        if config is None:
            config = {}
            
        # Converter specifications
        self.rated_power = config.get('rated_power', 530000.0)  # W
        self.input_voltage = config.get('input_voltage', 480.0)  # V (generator output)
        self.dc_link_voltage = config.get('dc_link_voltage', 800.0)  # V
        self.output_voltage = config.get('output_voltage', 13800.0)  # V (grid voltage)
        self.grid_frequency = config.get('grid_frequency', 60.0)  # Hz
        
        # Component efficiencies
        self.rectifier_efficiency = config.get('rectifier_efficiency', 0.97)
        self.inverter_efficiency = config.get('inverter_efficiency', 0.96)
        self.transformer_efficiency = config.get('transformer_efficiency', 0.985)
        self.filter_efficiency = config.get('filter_efficiency', 0.995)
        
        # Control parameters
        self.power_factor_target = config.get('power_factor_target', 0.95)
        self.voltage_regulation_range = config.get('voltage_regulation', 0.05)  # ±5%
        self.frequency_tolerance = config.get('frequency_tolerance', 0.1)  # ±0.1 Hz
        self.sync_time_constant = config.get('sync_time_constant', 2.0)  # s
        
        # Protection limits
        self.max_current = config.get('max_current', self.rated_power / (math.sqrt(3) * self.input_voltage * 0.9))
        self.max_voltage_deviation = config.get('max_voltage_deviation', 0.15)  # ±15%
        self.max_frequency_deviation = config.get('max_frequency_deviation', 1.0)  # ±1 Hz
        
        # State variables
        self.input_power = 0.0  # W
        self.output_power = 0.0  # W
        self.dc_link_power = 0.0  # W
        self.input_voltage_actual = self.input_voltage  # V
        self.output_voltage_actual = self.output_voltage  # V
        self.grid_frequency_actual = self.grid_frequency  # Hz
        self.power_factor_actual = 1.0
        self.is_synchronized = False
        self.sync_progress = 0.0  # 0-1
        
        # Component states
        self.rectifier_losses = 0.0  # W
        self.inverter_losses = 0.0  # W
        self.transformer_losses = 0.0  # W
        self.filter_losses = 0.0  # W
        self.total_losses = 0.0  # W
        self.overall_efficiency = 0.0
        
        # Protection status
        self.protection_active = False
        self.fault_conditions = []
        
        logger.info(f"Power electronics initialized: {self.rated_power/1000:.0f}kW, "
                   f"{self.input_voltage}V → {self.output_voltage}V")
    
    def update(self, generator_power: float, generator_voltage: float, 
               generator_frequency: float, grid_conditions: Dict[str, float], dt: float) -> Dict[str, float]:
        """
        Update power electronics system.
        
        Args:
            generator_power (float): Generator electrical power (W)
            generator_voltage (float): Generator voltage (V)
            generator_frequency (float): Generator frequency (Hz)
            grid_conditions (dict): Grid voltage, frequency, etc.
            dt (float): Time step (s)
            
        Returns:
            dict: Power electronics state and output
        """
        self.input_power = generator_power
        self.input_voltage_actual = generator_voltage
        
        # Check for fault conditions
        self._check_protection_systems(generator_voltage, generator_frequency, grid_conditions)
        
        if self.protection_active:
            # Protection active - no power transfer
            self.output_power = 0.0
            self.is_synchronized = False
            return self._get_state_dict()
        
        # Grid synchronization
        self._update_synchronization(generator_frequency, grid_conditions, dt)
        
        if not self.is_synchronized:
            # Not synchronized - no power transfer
            self.output_power = 0.0
            return self._get_state_dict()
        
        # Power conversion through stages
        self._calculate_power_conversion()
        
        # Voltage regulation
        self._regulate_output_voltage(grid_conditions)
        
        # Power factor correction
        self._correct_power_factor()
        
        return self._get_state_dict()
    
    def _check_protection_systems(self, voltage: float, frequency: float, grid_conditions: Dict[str, float]):
        """
        Monitor protection systems and fault conditions.
        
        Args:
            voltage (float): Generator voltage (V)
            frequency (float): Generator frequency (Hz)
            grid_conditions (dict): Grid parameters
        """
        self.fault_conditions.clear()
        
        # Voltage protection
        voltage_deviation = abs(voltage - self.input_voltage) / self.input_voltage
        if voltage_deviation > self.max_voltage_deviation:
            self.fault_conditions.append(f"Voltage deviation: {voltage_deviation*100:.1f}%")
        
        # Frequency protection
        frequency_deviation = abs(frequency - self.grid_frequency)
        if frequency_deviation > self.max_frequency_deviation:
            self.fault_conditions.append(f"Frequency deviation: {frequency_deviation:.2f}Hz")
        
        # Grid voltage protection
        grid_voltage = grid_conditions.get('voltage', self.output_voltage)
        grid_voltage_deviation = abs(grid_voltage - self.output_voltage) / self.output_voltage
        if grid_voltage_deviation > self.max_voltage_deviation:
            self.fault_conditions.append(f"Grid voltage deviation: {grid_voltage_deviation*100:.1f}%")
        
        # Overcurrent protection
        if self.input_power > 0 and voltage > 0:
            current = self.input_power / (math.sqrt(3) * voltage)
            if current > self.max_current:
                self.fault_conditions.append(f"Overcurrent: {current:.1f}A > {self.max_current:.1f}A")
        
        # Set protection status
        self.protection_active = len(self.fault_conditions) > 0
        
        if self.protection_active:
            logger.warning(f"Protection active: {', '.join(self.fault_conditions)}")
    
    def _update_synchronization(self, generator_frequency: float, grid_conditions: Dict[str, float], dt: float):
        """
        Update grid synchronization status.
        
        Args:
            generator_frequency (float): Generator frequency (Hz)
            grid_conditions (dict): Grid parameters
            dt (float): Time step (s)
        """
        grid_frequency = grid_conditions.get('frequency', self.grid_frequency)
        frequency_error = abs(generator_frequency - grid_frequency)
        
        # Synchronization criteria
        freq_ok = frequency_error < self.frequency_tolerance
        voltage_ok = abs(self.input_voltage_actual - self.input_voltage) / self.input_voltage < 0.1
        
        if freq_ok and voltage_ok:
            # Move towards synchronization
            self.sync_progress += dt / self.sync_time_constant
            self.sync_progress = min(1.0, self.sync_progress)
            
            if self.sync_progress >= 1.0:
                self.is_synchronized = True
        else:
            # Move away from synchronization
            self.sync_progress -= dt / (self.sync_time_constant * 0.5)
            self.sync_progress = max(0.0, self.sync_progress)
            
            if self.sync_progress <= 0.0:
                self.is_synchronized = False
        
        self.grid_frequency_actual = grid_frequency
        
        if self.is_synchronized:
            logger.debug(f"Grid synchronized: f_gen={generator_frequency:.2f}Hz, f_grid={grid_frequency:.2f}Hz")
    
    def _calculate_power_conversion(self):
        """
        Calculate power flow through conversion stages.
        """
        # Stage 1: AC-DC Rectifier
        rectifier_input = self.input_power
        self.rectifier_losses = rectifier_input * (1 - self.rectifier_efficiency)
        self.dc_link_power = rectifier_input - self.rectifier_losses
        
        # Stage 2: DC-AC Inverter
        inverter_input = self.dc_link_power
        self.inverter_losses = inverter_input * (1 - self.inverter_efficiency)
        inverter_output = inverter_input - self.inverter_losses
        
        # Stage 3: Transformer
        transformer_input = inverter_output
        self.transformer_losses = transformer_input * (1 - self.transformer_efficiency)
        transformer_output = transformer_input - self.transformer_losses
        
        # Stage 4: Output Filter
        filter_input = transformer_output
        self.filter_losses = filter_input * (1 - self.filter_efficiency)
        self.output_power = filter_input - self.filter_losses
        
        # Total losses and efficiency
        self.total_losses = (self.rectifier_losses + self.inverter_losses + 
                           self.transformer_losses + self.filter_losses)
        
        if self.input_power > 0:
            self.overall_efficiency = self.output_power / self.input_power
        else:
            self.overall_efficiency = 0.0
    
    def _regulate_output_voltage(self, grid_conditions: Dict[str, float]):
        """
        Regulate output voltage to match grid requirements.
        
        Args:
            grid_conditions (dict): Grid parameters
        """
        target_voltage = grid_conditions.get('voltage', self.output_voltage)
        voltage_error = target_voltage - self.output_voltage_actual
        
        # Simple proportional control
        voltage_correction = voltage_error * 0.1  # 10% gain
        self.output_voltage_actual += voltage_correction
        
        # Limit voltage regulation range
        max_deviation = self.output_voltage * self.voltage_regulation_range
        self.output_voltage_actual = max(self.output_voltage - max_deviation,
                                       min(self.output_voltage + max_deviation,
                                           self.output_voltage_actual))
    
    def _correct_power_factor(self):
        """
        Calculate and correct power factor.
        """
        # Simplified power factor calculation
        if self.output_power > 0:
            # Power factor typically decreases with light loading
            load_factor = self.output_power / self.rated_power
            
            if load_factor > 0.8:
                self.power_factor_actual = self.power_factor_target
            elif load_factor > 0.3:
                self.power_factor_actual = 0.85 + 0.1 * (load_factor - 0.3) / 0.5
            else:
                self.power_factor_actual = 0.75 + 0.1 * load_factor / 0.3
        else:
            self.power_factor_actual = 1.0
    
    def _get_state_dict(self) -> Dict[str, float]:
        """
        Get comprehensive power electronics state.
        
        Returns:
            dict: Complete system state
        """
        return {
            # Power flow
            'input_power': self.input_power,
            'output_power': self.output_power,
            'dc_link_power': self.dc_link_power,
            'overall_efficiency': self.overall_efficiency,
            
            # Voltages and frequencies
            'input_voltage': self.input_voltage_actual,
            'output_voltage': self.output_voltage_actual,
            'dc_link_voltage': self.dc_link_voltage,
            'grid_frequency': self.grid_frequency_actual,
            
            # Power quality
            'power_factor': self.power_factor_actual,
            'is_synchronized': self.is_synchronized,
            'sync_progress': self.sync_progress,
            
            # Loss breakdown
            'rectifier_losses': self.rectifier_losses,
            'inverter_losses': self.inverter_losses,
            'transformer_losses': self.transformer_losses,
            'filter_losses': self.filter_losses,
            'total_losses': self.total_losses,
            
            # Protection
            'protection_active': self.protection_active,
            'fault_count': len(self.fault_conditions)
        }
    
    def reset(self):
        """
        Reset power electronics to initial state.
        """
        self.input_power = 0.0
        self.output_power = 0.0
        self.dc_link_power = 0.0
        self.is_synchronized = False
        self.sync_progress = 0.0
        self.protection_active = False
        self.fault_conditions.clear()
        
        self.rectifier_losses = 0.0
        self.inverter_losses = 0.0
        self.transformer_losses = 0.0
        self.filter_losses = 0.0
        self.total_losses = 0.0
        self.overall_efficiency = 0.0
        
        logger.info("Power electronics system reset")


class GridInterface:
    """
    Grid interface and monitoring system.
    
    Simulates grid conditions and monitors grid connection status.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize grid interface.
        
        Args:
            config (dict): Grid configuration parameters
        """
        if config is None:
            config = {}
            
        # Grid parameters
        self.nominal_voltage = config.get('nominal_voltage', 13800.0)  # V
        self.nominal_frequency = config.get('nominal_frequency', 60.0)  # Hz
        self.short_circuit_power = config.get('short_circuit_power', 50e6)  # VA
        self.grid_impedance = config.get('grid_impedance', 0.1)  # Ohms
        
        # Grid stability parameters
        self.voltage_variation = config.get('voltage_variation', 0.02)  # ±2%
        self.frequency_variation = config.get('frequency_variation', 0.05)  # ±0.05 Hz
        
        # Current state
        self.voltage = self.nominal_voltage
        self.frequency = self.nominal_frequency
        self.power_demand = 0.0  # W
        self.is_connected = True
        
        logger.info(f"Grid interface initialized: {self.nominal_voltage/1000:.1f}kV, {self.nominal_frequency}Hz")
    
    def update(self, dt: float) -> Dict[str, float]:
        """
        Update grid conditions.
        
        Args:
            dt (float): Time step (s)
            
        Returns:
            dict: Grid conditions
        """
        # Simulate small grid variations
        import random
        
        voltage_noise = random.uniform(-self.voltage_variation, self.voltage_variation)
        frequency_noise = random.uniform(-self.frequency_variation, self.frequency_variation)
        
        self.voltage = self.nominal_voltage * (1 + voltage_noise)
        self.frequency = self.nominal_frequency + frequency_noise
        
        return {
            'voltage': self.voltage,
            'frequency': self.frequency,
            'power_demand': self.power_demand,
            'is_connected': self.is_connected,
            'short_circuit_power': self.short_circuit_power
        }
    
    def set_power_demand(self, power: float):
        """
        Set grid power demand.
        
        Args:
            power (float): Power demand (W)        """
        self.power_demand = max(0.0, power)
    
    def disconnect(self):
        """Disconnect from grid."""
        self.is_connected = False
        logger.warning("Grid disconnected")
    
    def reconnect(self):
        """Reconnect to grid."""
        self.is_connected = True
        logger.info("Grid reconnected")
    
    def apply_control_commands(self, commands: Dict[str, Any]):
        """
        Apply control system commands to grid interface.
        
        Args:
            commands (dict): Control commands
        """
        if 'voltage_setpoint' in commands:
            # For grid interface, voltage setpoint affects monitoring/regulation
            target_voltage = commands['voltage_setpoint']
            logger.debug(f"Grid interface voltage setpoint updated to {target_voltage:.1f}V")
        
        if 'frequency_setpoint' in commands:
            # For grid interface, frequency setpoint affects monitoring/regulation
            target_frequency = commands['frequency_setpoint']
            logger.debug(f"Grid interface frequency setpoint updated to {target_frequency:.1f}Hz")
        
        if 'control_mode' in commands:
            control_mode = commands['control_mode']
            logger.debug(f"Grid interface control mode: {control_mode}")
            
            # Handle emergency modes
            if control_mode == 'emergency' or control_mode == 'fault':
                logger.warning("Grid interface entering emergency mode")
            elif control_mode == 'normal':
                logger.info("Grid interface returning to normal operation")


def create_kmp_power_electronics(config: Optional[Dict[str, Any]] = None) -> Tuple[PowerElectronics, GridInterface]:
    """
    Create standard KMP power electronics and grid interface.
    
    Args:
        config (dict): Optional configuration overrides
        
    Returns:
        tuple: (PowerElectronics, GridInterface) instances
    """
    default_pe_config = {
        'rated_power': 530000.0,  # 530 kW
        'input_voltage': 480.0,   # Generator output
        'output_voltage': 13800.0,  # Medium voltage grid
        'rectifier_efficiency': 0.97,
        'inverter_efficiency': 0.96,
        'transformer_efficiency': 0.985,
        'overall_target_efficiency': 0.92  # 92% overall PE efficiency
    }
    
    default_grid_config = {
        'nominal_voltage': 13800.0,  # 13.8 kV
        'nominal_frequency': 60.0,
        'voltage_variation': 0.02,
        'frequency_variation': 0.05
    }
    
    if config:
        if 'power_electronics' in config:
            default_pe_config.update(config['power_electronics'])
        if 'grid' in config:
            default_grid_config.update(config['grid'])
    
    power_electronics = PowerElectronics(default_pe_config)
    grid_interface = GridInterface(default_grid_config)
    
    logger.info("Created KMP power electronics and grid interface systems")
    
    return power_electronics, grid_interface
