"""
Battery Storage System - Phase 7 Week 4 Day 22-24

Comprehensive battery storage system for grid services including:
- Energy arbitrage and economic optimization
- Grid stabilization services  
- Backup power functionality
- State of charge management
- Fast response capabilities

Key Features:
- Fast response energy storage (<1 second)
- Energy arbitrage based on electricity prices
- Backup power functionality during outages
- Advanced state of charge management
- Thermal management and safety monitoring
"""

import math
import time
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum


class BatteryMode(Enum):
    """Battery operating modes"""
    IDLE = "idle"
    CHARGING = "charging"
    DISCHARGING = "discharging"
    STABILIZING = "stabilizing"
    BACKUP = "backup"
    MAINTENANCE = "maintenance"


@dataclass
class BatterySpecs:
    """Battery system specifications"""
    nominal_capacity_kwh: float = 500.0  # Battery capacity in kWh
    max_power_kw: float = 250.0          # Maximum charge/discharge power
    efficiency: float = 0.95              # Round-trip efficiency
    min_soc: float = 0.1                 # Minimum state of charge (10%)
    max_soc: float = 0.95                # Maximum state of charge (95%)
    thermal_limit_c: float = 45.0        # Maximum operating temperature
    cycle_life: int = 6000               # Expected cycle life
    depth_of_discharge: float = 0.85     # Maximum depth of discharge


@dataclass
class BatteryState:
    """Current battery system state"""
    soc: float = 0.5                     # State of charge (0-1)
    voltage: float = 400.0               # DC bus voltage
    current: float = 0.0                 # DC current (positive = charging)
    temperature: float = 25.0            # Battery temperature (°C)
    cycle_count: float = 0.0             # Number of charge/discharge cycles (can be fractional)
    health: float = 1.0                  # Battery health factor (0-1)
    available_energy_kwh: float = 0.0    # Available energy for discharge
    available_capacity_kwh: float = 0.0  # Available capacity for charging


class BatteryStorageSystem:
    """
    Advanced battery storage system for grid services and economic optimization.
    
    Provides comprehensive battery management including energy arbitrage,
    grid stabilization, backup power, and state monitoring.
    """
    
    def __init__(self, specs: Optional[BatterySpecs] = None):
        """Initialize battery storage system"""
        self.specs = specs or BatterySpecs()
        self.state = BatteryState()
        self.mode = BatteryMode.IDLE
        
        # Operating parameters
        self.last_update = time.time()
        self.power_setpoint = 0.0  # Current power setpoint (kW, positive = charging)
        self.active = False
        
        # Performance tracking
        self.total_energy_charged = 0.0
        self.total_energy_discharged = 0.0
        self.arbitrage_revenue = 0.0
        self.grid_service_revenue = 0.0
        self.operation_hours = 0.0
        
        # Control parameters
        self.response_time = 0.5  # Response time in seconds
        self.ramp_rate = 100.0    # Power ramp rate (kW/s)
        
        # Economic parameters
        self.charge_price_threshold = 50.0   # $/MWh - charge below this price
        self.discharge_price_threshold = 80.0 # $/MWh - discharge above this price
        self.grid_service_rate = 25.0        # $/MWh for grid services
        
        # Initialize state
        self._update_available_capacity()
        
    def update(self, dt: float, grid_conditions: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update battery system state and control
        
        Args:
            dt: Time step in seconds
            grid_conditions: Current grid conditions
            
        Returns:
            Updated battery status and performance metrics
        """
        if not self.active:
            return self._get_status()
            
        # Update operation time
        self.operation_hours += dt / 3600.0
        
        # Get current conditions
        electricity_price = grid_conditions.get('electricity_price', 60.0)  # $/MWh
        grid_frequency = grid_conditions.get('frequency', 50.0)
        grid_voltage = grid_conditions.get('voltage', 1.0)
        load_demand = grid_conditions.get('load_demand', 0.0)
        
        # Determine operating mode and power setpoint
        self._determine_operating_mode(electricity_price, grid_frequency, grid_voltage, load_demand)
        
        # Execute power control
        actual_power = self._execute_power_control(dt)
        
        # Update battery state
        self._update_battery_state(dt, actual_power)
        
        # Update thermal model
        self._update_thermal_state(dt, actual_power)
        
        # Update degradation model
        self._update_battery_health(dt, actual_power)
        
        # Calculate revenue
        self._calculate_revenue(dt, actual_power, electricity_price)
        
        return self._get_status()
    
    def _determine_operating_mode(self, price: float, frequency: float, voltage: float, load: float):
        """Determine optimal operating mode based on grid conditions"""
        
        # Priority 1: Grid stabilization (emergency conditions)
        if abs(frequency - 50.0) > 0.2 or abs(voltage - 1.0) > 0.05:
            self.mode = BatteryMode.STABILIZING
            
            # Frequency support
            if frequency < 49.8:  # Under-frequency
                self.power_setpoint = -self.specs.max_power_kw * 0.8  # Discharge
            elif frequency > 50.2:  # Over-frequency  
                self.power_setpoint = self.specs.max_power_kw * 0.8   # Charge
            
            # Voltage support (adjust reactive power, simplified as real power here)
            elif voltage < 0.95:  # Under-voltage
                self.power_setpoint = -self.specs.max_power_kw * 0.6  # Discharge
            elif voltage > 1.05:  # Over-voltage
                self.power_setpoint = self.specs.max_power_kw * 0.6   # Charge
            
            return
        
        # Priority 2: Economic arbitrage
        if price <= self.charge_price_threshold and self.state.soc < self.specs.max_soc:
            self.mode = BatteryMode.CHARGING
            # Charge at maximum rate during low prices
            available_charge_power = min(
                self.specs.max_power_kw,
                (self.specs.max_soc - self.state.soc) * self.specs.nominal_capacity_kwh * 2  # 2-hour charge rate
            )
            self.power_setpoint = available_charge_power
            
        elif price >= self.discharge_price_threshold and self.state.soc > self.specs.min_soc:
            self.mode = BatteryMode.DISCHARGING
            # Discharge at optimal rate during high prices
            available_discharge_power = min(
                self.specs.max_power_kw,
                (self.state.soc - self.specs.min_soc) * self.specs.nominal_capacity_kwh * 2  # 2-hour discharge rate
            )
            self.power_setpoint = -available_discharge_power
            
        else:
            # Priority 3: Peak shaving or idle
            if load > 200.0:  # High load condition
                self.mode = BatteryMode.DISCHARGING
                # Moderate discharge for peak shaving
                self.power_setpoint = -min(50.0, self.specs.max_power_kw * 0.3)
            else:
                self.mode = BatteryMode.IDLE
                self.power_setpoint = 0.0
    
    def _execute_power_control(self, dt: float) -> float:
        """Execute power control with ramp rate limiting"""
        
        # Apply SOC limits
        if self.power_setpoint > 0:  # Charging
            if self.state.soc >= self.specs.max_soc:
                self.power_setpoint = 0.0
            else:
                # Limit charging power based on available capacity
                max_charge_power = (self.specs.max_soc - self.state.soc) * self.specs.nominal_capacity_kwh / (dt/3600.0)
                self.power_setpoint = min(self.power_setpoint, max_charge_power)
        
        elif self.power_setpoint < 0:  # Discharging
            if self.state.soc <= self.specs.min_soc:
                self.power_setpoint = 0.0
            else:
                # Limit discharging power based on available energy
                max_discharge_power = -(self.state.soc - self.specs.min_soc) * self.specs.nominal_capacity_kwh / (dt/3600.0)
                self.power_setpoint = max(self.power_setpoint, max_discharge_power)
        
        # Apply ramp rate limiting
        max_change = self.ramp_rate * dt
        if abs(self.power_setpoint) > max_change:
            if self.power_setpoint > 0:
                actual_power = min(self.power_setpoint, max_change)
            else:
                actual_power = max(self.power_setpoint, -max_change)
        else:
            actual_power = self.power_setpoint
        
        return actual_power
    
    def _update_battery_state(self, dt: float, power: float):
        """Update battery state of charge and electrical parameters"""
        
        # Calculate energy change
        if power > 0:  # Charging
            energy_change = power * dt / 3600.0 * self.specs.efficiency
        else:  # Discharging
            energy_change = power * dt / 3600.0 / self.specs.efficiency
        
        # Update state of charge
        soc_change = energy_change / self.specs.nominal_capacity_kwh
        self.state.soc = max(0.0, min(1.0, self.state.soc + soc_change))
        
        # Update electrical parameters
        self.state.current = power / self.state.voltage if self.state.voltage > 0 else 0.0
        
        # Update voltage based on SOC (simplified model)
        base_voltage = 400.0
        voltage_variation = 50.0 * (self.state.soc - 0.5)  # ±25V variation
        self.state.voltage = base_voltage + voltage_variation
        
        # Update available capacities
        self._update_available_capacity()
        
        # Track energy flows
        if power > 0:
            self.total_energy_charged += abs(energy_change)
        else:
            self.total_energy_discharged += abs(energy_change)
    
    def _update_available_capacity(self):
        """Update available energy and capacity"""
        self.state.available_energy_kwh = (self.state.soc - self.specs.min_soc) * self.specs.nominal_capacity_kwh
        self.state.available_capacity_kwh = (self.specs.max_soc - self.state.soc) * self.specs.nominal_capacity_kwh
    
    def _update_thermal_state(self, dt: float, power: float):
        """Update battery temperature based on power and ambient conditions"""
        
        # Simplified thermal model
        ambient_temp = 25.0  # °C
        thermal_resistance = 0.1  # °C/kW
        thermal_capacity = 50.0   # kJ/°C
        
        # Heat generation from losses
        if power > 0:  # Charging
            heat_generation = power * (1 - self.specs.efficiency)
        else:  # Discharging
            heat_generation = abs(power) * (1 - self.specs.efficiency)
        
        # Temperature rise from heat generation
        temp_rise = heat_generation * thermal_resistance
        
        # Cooling to ambient
        cooling_rate = (self.state.temperature - ambient_temp) / thermal_capacity
        
        # Update temperature
        temp_change = (temp_rise - cooling_rate) * dt / 60.0  # Per minute
        self.state.temperature += temp_change
        
        # Apply thermal limits
        if self.state.temperature > self.specs.thermal_limit_c:
            # Reduce power capability due to thermal limits
            self.specs.max_power_kw *= 0.9
    
    def _update_battery_health(self, dt: float, power: float):
        """Update battery health based on cycling and aging"""
        
        # Simplified aging model
        if abs(power) > 0.1 * self.specs.max_power_kw:
            # Count as partial cycle
            cycle_fraction = abs(power) / self.specs.max_power_kw * dt / 3600.0
            self.state.cycle_count += cycle_fraction
            
            # Health degradation
            health_loss = cycle_fraction / self.specs.cycle_life
            self.state.health = max(0.7, self.state.health - health_loss)
            
            # Reduce capacity based on health
            self.specs.nominal_capacity_kwh *= self.state.health
    
    def _calculate_revenue(self, dt: float, power: float, price: float):
        """Calculate revenue from battery operations"""
        
        energy_mwh = abs(power) * dt / 3600.0 / 1000.0  # Convert to MWh
        
        if self.mode == BatteryMode.CHARGING:
            # Cost of charging
            self.arbitrage_revenue -= energy_mwh * price
            
        elif self.mode == BatteryMode.DISCHARGING:
            # Revenue from discharging
            self.arbitrage_revenue += energy_mwh * price
            
        elif self.mode == BatteryMode.STABILIZING:
            # Revenue from grid services
            self.grid_service_revenue += energy_mwh * self.grid_service_rate
    
    def _get_status(self) -> Dict[str, Any]:
        """Get current battery system status"""
        return {
            'active': self.active,
            'mode': self.mode.value,
            'soc': self.state.soc,
            'soc_percent': self.state.soc * 100,
            'power_output_kw': -self.power_setpoint,  # Negative for discharge (output)
            'power_setpoint_kw': self.power_setpoint,
            'voltage': self.state.voltage,
            'current': self.state.current,
            'temperature': self.state.temperature,
            'health': self.state.health,
            'cycle_count': self.state.cycle_count,
            'available_energy_kwh': self.state.available_energy_kwh,
            'available_capacity_kwh': self.state.available_capacity_kwh,
            'total_energy_charged': self.total_energy_charged,
            'total_energy_discharged': self.total_energy_discharged,
            'arbitrage_revenue': self.arbitrage_revenue,
            'grid_service_revenue': self.grid_service_revenue,
            'total_revenue': self.arbitrage_revenue + self.grid_service_revenue,
            'operation_hours': self.operation_hours,
            'response_time': self.response_time
        }
    
    def start_service(self):
        """Start battery storage service"""
        self.active = True
        self.last_update = time.time()
    
    def stop_service(self):
        """Stop battery storage service"""
        self.active = False
        self.mode = BatteryMode.IDLE
        self.power_setpoint = 0.0
    
    def set_economic_parameters(self, charge_threshold: float, discharge_threshold: float, service_rate: float):
        """Update economic operating parameters"""
        self.charge_price_threshold = charge_threshold
        self.discharge_price_threshold = discharge_threshold
        self.grid_service_rate = service_rate
    
    def emergency_discharge(self, power_kw: float) -> bool:
        """Emergency discharge for grid support"""
        if self.state.soc > self.specs.min_soc:
            max_power = min(power_kw, self.specs.max_power_kw, 
                          self.state.available_energy_kwh * 2)  # 30-min discharge
            self.power_setpoint = -max_power
            self.mode = BatteryMode.STABILIZING
            return True
        return False
    
    def emergency_charge(self, power_kw: float) -> bool:
        """Emergency charge for grid support"""
        if self.state.soc < self.specs.max_soc:
            max_power = min(power_kw, self.specs.max_power_kw,
                          self.state.available_capacity_kwh * 2)  # 30-min charge
            self.power_setpoint = max_power
            self.mode = BatteryMode.STABILIZING
            return True
        return False
    
    def reset_performance_metrics(self):
        """Reset performance tracking metrics"""
        self.total_energy_charged = 0.0
        self.total_energy_discharged = 0.0
        self.arbitrage_revenue = 0.0
        self.grid_service_revenue = 0.0
        self.operation_hours = 0.0
    
    def get_forecasted_availability(self, hours_ahead: int) -> Dict[str, float]:
        """Forecast battery availability for grid services"""
        # Simplified forecast based on current SOC and typical patterns
        avg_soc = 0.5
        soc_trend = (self.state.soc - avg_soc) * 0.1  # Trend toward average
        
        forecasted_soc = max(0.1, min(0.9, self.state.soc + soc_trend * hours_ahead))
        
        return {
            'forecasted_soc': forecasted_soc,
            'available_energy_kwh': (forecasted_soc - self.specs.min_soc) * self.specs.nominal_capacity_kwh,
            'available_capacity_kwh': (self.specs.max_soc - forecasted_soc) * self.specs.nominal_capacity_kwh,
            'max_discharge_power_kw': self.specs.max_power_kw * self.state.health,
            'max_charge_power_kw': self.specs.max_power_kw * self.state.health
        }
    
    def is_storing(self) -> bool:
        """Check if battery is currently active in any storage mode"""
        return self.active and self.mode != BatteryMode.IDLE
    
    def reset(self):
        """Reset battery storage system to initial state"""
        self.stop_service()
        self.state.soc = 0.5
        self.state.temperature = 25.0
        self.state.cycle_count = 0
        self.state.health = 1.0
        self.reset_performance_metrics()
        self._update_available_capacity()
    
    def get_status(self) -> Dict[str, Any]:
        """Get current battery system status"""
        return self._get_status()


def create_battery_storage_system(capacity_kwh: float = 500.0, max_power_kw: float = 250.0) -> BatteryStorageSystem:
    """
    Factory function to create a battery storage system
    
    Args:
        capacity_kwh: Battery capacity in kWh
        max_power_kw: Maximum power rating in kW
        
    Returns:
        Configured BatteryStorageSystem instance
    """
    specs = BatterySpecs(
        nominal_capacity_kwh=capacity_kwh,
        max_power_kw=max_power_kw
    )
    return BatteryStorageSystem(specs)
