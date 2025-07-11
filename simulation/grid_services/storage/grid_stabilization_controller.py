import time
from typing import Any, Dict, Optional
from dataclasses import dataclass, field
from enum import Enum

class StabilizationMode(Enum):
    """Grid stabilization operating modes"""
    NORMAL = "normal"
    FREQUENCY_SUPPORT = "frequency_support"
    VOLTAGE_SUPPORT = "voltage_support"
    EMERGENCY = "emergency"

@dataclass
class GridStabilizationConfig:
    """Configuration for grid stabilization controller"""
    frequency_droop: float = 0.05  # 5% droop
    voltage_droop: float = 0.1  # 10% droop
    frequency_deadband: float = 0.02  # Hz
    voltage_deadband: float = 0.02  # p.u.
    max_power_output: float = 250.0  # kW
    response_time: float = 0.1  # seconds
    frequency_priority: float = 1.0
    voltage_priority: float = 0.8

@dataclass
class StabilizationState:
    """Grid stabilization controller state"""
    mode: StabilizationMode = StabilizationMode.NORMAL
    power_output: float = 0.0
    frequency_response: float = 0.0
    voltage_response: float = 0.0
    last_update_time: float = 0.0
    performance_metrics: Dict[str, float] = field(default_factory=lambda: {
        'frequency_deviations_corrected': 0,
        'voltage_deviations_corrected': 0,
        'total_energy_provided': 0.0,
        'response_time_avg': 0.0
    })

    def __post_init__(self):
        if self.performance_metrics is None:
            self.performance_metrics = {
                'frequency_deviations_corrected': 0,
                'voltage_deviations_corrected': 0,
                'total_energy_provided': 0.0,
                'response_time_avg': 0.0
            }

class GridStabilizationController:
    """
    Grid stabilization controller that coordinates battery response
    for frequency and voltage support.
    """
    
    def __init__(self, config: Optional[GridStabilizationConfig] = None):
        """Initialize grid stabilization controller"""
        self.config = config or GridStabilizationConfig()
        self.state = StabilizationState()
        
    def update(self, grid_state: Dict[str, Any], battery_state: Dict[str, Any],
              time_step: float) -> float:
        """
        Update stabilization control and calculate required power output
        
        Args:
            grid_state: Current grid measurements
            battery_state: Current battery system state
            time_step: Time step since last update in seconds
            
        Returns:
            Required power output from battery (kW)
        """
        try:
            # Determine operating mode
            self._update_mode(grid_state)
            
            # Calculate required responses
            freq_response = self._calculate_frequency_response(grid_state)
            volt_response = self._calculate_voltage_response(grid_state)
            
            # Combine responses based on priority and mode
            power_output = self._combine_responses(freq_response, volt_response)
            
            # Apply battery constraints
            power_output = self._apply_battery_constraints(power_output, battery_state)
            
            # Update metrics
            self._update_metrics(grid_state, power_output, time_step)
            
            self.state.power_output = power_output
            return power_output
            
        except Exception as e:
            self.state.mode = StabilizationMode.EMERGENCY
            return 0.0
    
    def _update_mode(self, grid_state: Dict[str, Any]) -> None:
        """Update operating mode based on grid conditions"""
        freq_dev = abs(grid_state.get('frequency', 50.0) - 50.0)
        volt_dev = abs(grid_state.get('voltage', 1.0) - 1.0)
        
        if freq_dev > 0.5 or volt_dev > 0.1:  # Severe deviation
            self.state.mode = StabilizationMode.EMERGENCY
        elif freq_dev > self.config.frequency_deadband:
            self.state.mode = StabilizationMode.FREQUENCY_SUPPORT
        elif volt_dev > self.config.voltage_deadband:
            self.state.mode = StabilizationMode.VOLTAGE_SUPPORT
        else:
            self.state.mode = StabilizationMode.NORMAL
    
    def _calculate_frequency_response(self, grid_state: Dict[str, Any]) -> float:
        """Calculate power response for frequency support"""
        nominal_freq = 50.0
        freq = grid_state.get('frequency', nominal_freq)
        freq_dev = freq - nominal_freq
        
        if abs(freq_dev) <= self.config.frequency_deadband:
            return 0.0
            
        # Droop response calculation
        response = -(freq_dev / nominal_freq) * (self.config.max_power_output / 
                                               self.config.frequency_droop)
                                               
        self.state.frequency_response = response
        return response
    
    def _calculate_voltage_response(self, grid_state: Dict[str, Any]) -> float:
        """Calculate power response for voltage support"""
        nominal_volt = 1.0
        volt = grid_state.get('voltage', nominal_volt)
        volt_dev = volt - nominal_volt
        
        if abs(volt_dev) <= self.config.voltage_deadband:
            return 0.0
            
        # Droop response calculation
        response = -(volt_dev / nominal_volt) * (self.config.max_power_output /
                                               self.config.voltage_droop)
                                               
        self.state.voltage_response = response
        return response
    
    def _combine_responses(self, freq_response: float, volt_response: float) -> float:
        """Combine frequency and voltage responses based on priority and mode"""
        if self.state.mode == StabilizationMode.EMERGENCY:
            # In emergency, use the larger response
            return max(abs(freq_response), abs(volt_response)) * (
                1 if freq_response > 0 else -1)
                
        elif self.state.mode == StabilizationMode.FREQUENCY_SUPPORT:
            # Prioritize frequency response
            return freq_response + 0.5 * volt_response
            
        elif self.state.mode == StabilizationMode.VOLTAGE_SUPPORT:
            # Prioritize voltage response
            return volt_response + 0.5 * freq_response
            
        else:  # NORMAL mode
            # Weighted combination
            return (self.config.frequency_priority * freq_response +
                   self.config.voltage_priority * volt_response)
    
    def _apply_battery_constraints(self, power_output: float,
                                 battery_state: Dict[str, Any]) -> float:
        """Apply battery system constraints to power output"""
        # Check battery state
        if battery_state.get('operating_state') in ['fault', 'maintenance']:
            return 0.0
            
        # Apply power limits
        power_output = max(-self.config.max_power_output,
                          min(self.config.max_power_output, power_output))
                          
        # Consider battery state of charge
        soc = battery_state.get('state_of_charge', 0.5)
        if power_output > 0 and soc < 0.1:  # Discharge
            return 0.0
        if power_output < 0 and soc > 0.9:  # Charge
            return 0.0
            
        return power_output
    
    def _update_metrics(self, grid_state: Dict[str, Any], power_output: float,
                       time_step: float) -> None:
        """Update performance metrics"""
        freq_dev = abs(grid_state.get('frequency', 50.0) - 50.0)
        volt_dev = abs(grid_state.get('voltage', 1.0) - 1.0)
        
        # Count corrected deviations
        if freq_dev > self.config.frequency_deadband and power_output != 0:
            self.state.performance_metrics['frequency_deviations_corrected'] += 1
            
        if volt_dev > self.config.voltage_deadband and power_output != 0:
            self.state.performance_metrics['voltage_deviations_corrected'] += 1
            
        # Update energy metrics
        energy = abs(power_output * time_step)
        self.state.performance_metrics['total_energy_provided'] += energy
        
        # Update response time metrics
        current_time = time.time()
        response_time = current_time - self.state.last_update_time
        self.state.performance_metrics['response_time_avg'] = (
            0.9 * self.state.performance_metrics['response_time_avg'] +
            0.1 * response_time
        )
        self.state.last_update_time = current_time
    
    def get_state(self) -> Dict[str, Any]:
        """Get current controller state"""
        return {
            'mode': self.state.mode.value,
            'power_output': self.state.power_output,
            'frequency_response': self.state.frequency_response,
            'voltage_response': self.state.voltage_response,
            'performance_metrics': self.state.performance_metrics
        }
    
    def reset(self) -> None:
        """Reset controller state"""
        self.state = StabilizationState()


def create_standard_grid_stabilization_controller() -> GridStabilizationController:
    """
    Create a grid stabilization controller with standard configuration.
    
    Returns:
        GridStabilizationController instance with standard settings
    """
    config = GridStabilizationConfig(
        frequency_droop=0.05,
        voltage_droop=0.1,
        frequency_deadband=0.02,
        voltage_deadband=0.02,
        max_power_output=250.0,
        response_time=0.1,
        frequency_priority=1.0,
        voltage_priority=0.8
    )
    return GridStabilizationController(config)

