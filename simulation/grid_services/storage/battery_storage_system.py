import time
from typing import Any, Dict, Optional
from enum import Enum
from dataclasses import dataclass

class BatteryState(Enum):
    """Battery operating states"""
    IDLE = "idle"
    CHARGING = "charging"
    DISCHARGING = "discharging"
    FAULT = "fault"
    MAINTENANCE = "maintenance"

@dataclass
class BatteryStorageConfig:
    """Configuration for battery storage system"""
    capacity: float = 1000.0  # kWh
    max_charge_rate: float = 250.0  # kW
    max_discharge_rate: float = 250.0  # kW
    min_soc: float = 0.1  # Minimum state of charge (10%)
    max_soc: float = 0.9  # Maximum state of charge (90%)
    charge_efficiency: float = 0.95  # Battery charging efficiency
    discharge_efficiency: float = 0.95  # Battery discharging efficiency
    thermal_limit: float = 45.0  # Maximum temperature in Celsius
    response_time: float = 0.1  # Response time in seconds
    degradation_factor: float = 0.0001  # Capacity degradation per cycle

@dataclass
class BatteryStorageState:
    """Battery storage system state"""
    state_of_charge: float = 0.5  # Current state of charge (0-1)
    power_output: float = 0.0  # Current power output (kW)
    temperature: float = 25.0  # Current temperature (Celsius)
    operating_state: BatteryState = BatteryState.IDLE
    cycle_count: int = 0
    available_capacity: float = 1000.0  # Available capacity considering degradation
    last_maintenance: float = 0.0  # Timestamp of last maintenance
    cumulative_energy_in: float = 0.0  # Total energy charged (kWh)
    cumulative_energy_out: float = 0.0  # Total energy discharged (kWh)

class BatteryStorageSystem:
    """
    Battery energy storage system for grid services including energy arbitrage,
    grid stabilization, and backup power functionality.
    """
    
    def __init__(self, config: Optional[BatteryStorageConfig] = None):
        """Initialize battery storage system"""
        self.config = config or BatteryStorageConfig()
        self.state = BatteryStorageState(available_capacity=self.config.capacity)
        self.last_update_time = time.time()
        self.requested_power = 0.0
    
    def update(self, grid_state: Dict[str, Any], time_step: float) -> float:
        """
        Update battery state and calculate power response
        
        Args:
            grid_state: Current grid state including frequency, voltage, prices
            time_step: Time step since last update in seconds
            
        Returns:
            Power output (positive for discharge, negative for charge)
        """
        try:
            if self.state.operating_state == BatteryState.FAULT:
                return 0.0
                
            # Update thermal state
            self._update_thermal_state(time_step)
            
            # Check for maintenance needs
            if self._check_maintenance_needed():
                self.state.operating_state = BatteryState.MAINTENANCE
                return 0.0
            
            # Calculate optimal power output based on grid conditions
            power_output = self._calculate_power_output(grid_state)
            
            # Apply battery constraints
            power_output = self._apply_constraints(power_output, time_step)
            
            # Update state of charge
            self._update_state_of_charge(power_output, time_step)
            
            # Update metrics
            self._update_metrics(power_output, time_step)
            
            return power_output
            
        except Exception as e:
            self.state.operating_state = BatteryState.FAULT
            return 0.0
    
    def request_power_output(self, power: float) -> float:
        """
        Request a specific power output from the battery
        
        Args:
            power: Requested power output in kW (positive for discharge, negative for charge)
            
        Returns:
            Actual power output that will be provided
        """
        try:
            # Apply battery constraints
            constrained_power = self._apply_constraints(power, self.config.response_time)
            
            # Update state
            self.requested_power = constrained_power
            self.state.power_output = constrained_power
            
            # Update state of charge for the response time period
            self._update_state_of_charge(constrained_power, self.config.response_time)
            
            return constrained_power
            
        except Exception as e:
            self.state.operating_state = BatteryState.FAULT
            return 0.0
    
    def _calculate_power_output(self, grid_state: Dict[str, Any]) -> float:
        """Calculate optimal power output based on grid conditions"""
        # Grid stabilization response
        freq_dev = grid_state.get('frequency', 50.0) - 50.0
        voltage_dev = grid_state.get('voltage', 1.0) - 1.0
        
        # Economic optimization
        price = grid_state.get('electricity_price', 0.0)
        price_threshold = grid_state.get('price_threshold', 0.0)
        
        # Calculate power response
        stabilization_power = -freq_dev * 100.0  # Simple droop response
        economic_power = 0.0
        
        if price > price_threshold and self.state.state_of_charge > self.config.min_soc:
            economic_power = self.config.max_discharge_rate  # Discharge when prices are high
        elif price < price_threshold and self.state.state_of_charge < self.config.max_soc:
            economic_power = -self.config.max_charge_rate  # Charge when prices are low
            
        # Combine responses with priority to grid stabilization
        return stabilization_power + 0.5 * economic_power
    
    def _apply_constraints(self, power_output: float, time_step: float) -> float:
        """Apply battery operational constraints to power output"""
        # Check state of charge limits
        if power_output > 0 and self.state.state_of_charge <= self.config.min_soc:
            return 0.0  # Cannot discharge below minimum SOC
        if power_output < 0 and self.state.state_of_charge >= self.config.max_soc:
            return 0.0  # Cannot charge above maximum SOC
            
        # Apply rate limits
        power_output = max(-self.config.max_charge_rate,
                          min(self.config.max_discharge_rate, power_output))
                          
        # Apply thermal constraints
        if self.state.temperature >= self.config.thermal_limit:
            return min(0.0, power_output)  # Only allow charging when hot
            
        return power_output
    
    def _update_state_of_charge(self, power_output: float, time_step: float) -> None:
        """Update battery state of charge based on power output"""
        energy_change = power_output * time_step  # kWh
        
        if energy_change > 0:  # Discharging
            efficiency = self.config.discharge_efficiency
            self.state.cumulative_energy_out += energy_change
        else:  # Charging
            efficiency = self.config.charge_efficiency
            self.state.cumulative_energy_in += abs(energy_change)
            
        # Update state of charge
        soc_change = energy_change * efficiency / self.state.available_capacity
        self.state.state_of_charge = max(0.0, min(1.0,
            self.state.state_of_charge - soc_change))
            
        # Update operating state
        if abs(power_output) < 0.1:
            self.state.operating_state = BatteryState.IDLE
        elif power_output > 0:
            self.state.operating_state = BatteryState.DISCHARGING
        else:
            self.state.operating_state = BatteryState.CHARGING
    
    def _update_thermal_state(self, time_step: float) -> None:
        """Update battery temperature based on operation"""
        # Simple thermal model
        power_loss = abs(self.state.power_output) * (1 - self.config.charge_efficiency)
        temp_rise = power_loss * 0.01 * time_step  # Simplified thermal calculation
        cooling = (self.state.temperature - 25.0) * 0.1 * time_step  # Natural cooling
        self.state.temperature += temp_rise - cooling
    
    def _check_maintenance_needed(self) -> bool:
        """Check if maintenance is needed based on cycles and time"""
        current_time = time.time()
        maintenance_interval = 30 * 24 * 3600  # 30 days
        
        return (current_time - self.state.last_maintenance > maintenance_interval or
                self.state.cycle_count > 1000)
    
    def _update_metrics(self, power_output: float, time_step: float) -> None:
        """Update battery performance metrics"""
        if power_output > 0:
            self.state.cycle_count = int(self.state.cycle_count + time_step / (24 * 3600))  # Partial cycle counting
            
        # Update capacity degradation
        cycles_since_last = time_step / (24 * 3600)
        degradation = cycles_since_last * self.config.degradation_factor
        self.state.available_capacity *= (1 - degradation)
    
    def get_state(self) -> Dict[str, Any]:
        """Get current battery state"""
        return {
            'state_of_charge': self.state.state_of_charge,
            'power_output': self.state.power_output,
            'temperature': self.state.temperature,
            'operating_state': self.state.operating_state.value,
            'available_capacity': self.state.available_capacity,
            'cycle_count': self.state.cycle_count,
            'cumulative_energy_in': self.state.cumulative_energy_in,
            'cumulative_energy_out': self.state.cumulative_energy_out
        }
    
    def reset(self) -> None:
        """Reset battery state"""
        self.state = BatteryStorageState(available_capacity=self.config.capacity)
        self.last_update_time = time.time()

def create_battery_storage_system(config: Optional[Dict[str, Any]] = None) -> BatteryStorageSystem:
    """
    Factory function to create a battery storage system with optional configuration
    
    Args:
        config: Optional dictionary with configuration parameters
        
    Returns:
        Configured BatteryStorageSystem instance
    """
    if config is None:
        return BatteryStorageSystem()
        
    battery_config = BatteryStorageConfig(
        capacity=config.get('capacity', 1000.0),
        max_charge_rate=config.get('max_charge_rate', 250.0),
        max_discharge_rate=config.get('max_discharge_rate', 250.0),
        min_soc=config.get('min_soc', 0.1),
        max_soc=config.get('max_soc', 0.9),
        charge_efficiency=config.get('charge_efficiency', 0.95),
        discharge_efficiency=config.get('discharge_efficiency', 0.95),
        thermal_limit=config.get('thermal_limit', 45.0),
        response_time=config.get('response_time', 0.1),
        degradation_factor=config.get('degradation_factor', 0.0001)
    )
    
    return BatteryStorageSystem(config=battery_config)

