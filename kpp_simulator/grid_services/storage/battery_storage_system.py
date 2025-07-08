"""
Battery Storage System for KPP Simulator
Implements energy storage and grid services
"""

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
from datetime import datetime, timedelta

from ...core.physics_engine import PhysicsEngine
from ...electrical.electrical_system import IntegratedElectricalSystem
from ...control_systems.control_system import IntegratedControlSystem


class StorageMode(Enum):
    """Battery storage modes"""
    CHARGING = "charging"
    DISCHARGING = "discharging"
    IDLE = "idle"
    MAINTENANCE = "maintenance"
    ERROR = "error"


class StorageService(Enum):
    """Storage services"""
    ENERGY_ARBITRAGE = "energy_arbitrage"
    FREQUENCY_RESPONSE = "frequency_response"
    VOLTAGE_SUPPORT = "voltage_support"
    POWER_QUALITY = "power_quality"
    PEAK_SHAVING = "peak_shaving"
    LOAD_LEVELING = "load_leveling"


@dataclass
class BatteryState:
    """Battery state information"""
    timestamp: datetime
    state_of_charge: float  # 0.0 to 1.0
    voltage: float  # V
    current: float  # A
    power: float  # kW
    temperature: float  # °C
    health: float  # 0.0 to 1.0


@dataclass
class StorageAction:
    """Storage action data"""
    timestamp: datetime
    action_type: str
    power: float
    energy: float
    service: StorageService
    duration: timedelta
    efficiency: float


@dataclass
class StorageConfiguration:
    """Battery storage configuration"""
    capacity: float  # kWh
    max_power: float  # kW
    min_soc: float  # 0.0 to 1.0
    max_soc: float  # 0.0 to 1.0
    charge_efficiency: float  # 0.0 to 1.0
    discharge_efficiency: float  # 0.0 to 1.0
    self_discharge_rate: float  # per hour
    cycle_life: int  # cycles
    response_time: float  # seconds


class BatteryStorageSystem:
    """
    Battery Storage System for energy storage and grid services
    
    Features:
    - State of charge management
    - Energy arbitrage optimization
    - Grid services delivery
    - Performance monitoring and optimization
    - Thermal management
    - Health monitoring
    """
    
    def __init__(self, 
                 physics_engine: PhysicsEngine,
                 electrical_system: IntegratedElectricalSystem,
                 control_system: IntegratedControlSystem):
        """
        Initialize the Battery Storage System
        
        Args:
            physics_engine: Core physics engine
            electrical_system: Integrated electrical system
            control_system: Integrated control system
        """
        self.physics_engine = physics_engine
        self.electrical_system = electrical_system
        self.control_system = control_system
        
        # System state
        self.is_active = False
        self.current_mode = StorageMode.IDLE
        self.active_service = None
        
        # Battery configuration
        self.config = StorageConfiguration(
            capacity=1000.0,  # kWh
            max_power=500.0,  # kW
            min_soc=0.1,  # 10%
            max_soc=0.9,  # 90%
            charge_efficiency=0.95,
            discharge_efficiency=0.95,
            self_discharge_rate=0.001,  # 0.1% per hour
            cycle_life=5000,
            response_time=0.1  # 100ms
        )
        
        # Battery state
        self.current_state = BatteryState(
            timestamp=datetime.now(),
            state_of_charge=0.5,  # 50%
            voltage=400.0,
            current=0.0,
            power=0.0,
            temperature=25.0,
            health=1.0
        )
        
        # History tracking
        self.state_history: List[BatteryState] = []
        self.action_history: List[StorageAction] = []
        
        # Performance tracking
        self.performance_metrics = {
            'total_energy_charged': 0.0,  # kWh
            'total_energy_discharged': 0.0,  # kWh
            'total_cycles': 0,
            'average_efficiency': 0.0,
            'availability': 1.0,
            'response_time': 0.0,
            'service_revenue': 0.0,
            'arbitrage_revenue': 0.0
        }
        
        # Service tracking
        self.active_services: Dict[StorageService, Dict[str, Any]] = {}
        self.service_performance: Dict[StorageService, Dict[str, Any]] = {}
        
        # Economic parameters
        self.electricity_prices: List[Tuple[datetime, float]] = []
        self.price_forecast: List[Tuple[datetime, float]] = []
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        self.logger.info("Battery Storage System initialized")
    
    def start(self):
        """Start the battery storage system"""
        self.is_active = True
        self.current_mode = StorageMode.IDLE
        self.logger.info("Battery Storage System started")
    
    def stop(self):
        """Stop the battery storage system"""
        self.is_active = False
        self.current_mode = StorageMode.IDLE
        self.active_service = None
        self.logger.info("Battery Storage System stopped")
    
    def update(self, dt: float):
        """
        Update the battery storage system
        
        Args:
            dt: Time step in seconds
        """
        if not self.is_active:
            return
        
        # Update battery state
        self._update_battery_state(dt)
        
        # Execute active service
        if self.active_service:
            self._execute_service(dt)
        
        # Update performance metrics
        self._update_performance_metrics(dt)
        
        # Store state history
        self._store_state_history()
    
    def _update_battery_state(self, dt: float):
        """Update battery state"""
        # Update timestamp
        self.current_state.timestamp = datetime.now()
        
        # Apply self-discharge
        self_discharge = self.config.self_discharge_rate * dt / 3600  # Convert to per-second
        self.current_state.state_of_charge -= self_discharge
        
        # Ensure SOC stays within limits
        self.current_state.state_of_charge = np.clip(
            self.current_state.state_of_charge,
            self.config.min_soc,
            self.config.max_soc
        )
        
        # Update voltage based on SOC (simplified model)
        self.current_state.voltage = 350.0 + (self.current_state.state_of_charge * 100.0)
        
        # Update temperature (simplified thermal model)
        if self.current_state.power != 0:
            temp_change = (self.current_state.power / self.config.max_power) * 0.1 * dt
            self.current_state.temperature += temp_change
        else:
            # Cool down
            temp_change = -0.01 * dt
            self.current_state.temperature += temp_change
        
        # Limit temperature
        self.current_state.temperature = np.clip(self.current_state.temperature, 0.0, 60.0)
        
        # Update health (simplified degradation model)
        if self.current_state.power != 0:
            degradation = 0.000001 * dt  # Very small degradation per second
            self.current_state.health -= degradation
        
        # Ensure health stays positive
        self.current_state.health = max(0.0, self.current_state.health)
    
    def _execute_service(self, dt: float):
        """Execute active storage service"""
        if not self.active_service:
            return
        
        service_config = self.active_services.get(self.active_service)
        if not service_config:
            return
        
        # Get service parameters
        target_power = service_config.get('target_power', 0.0)
        service_type = service_config.get('service_type', 'power')
        
        # Execute based on service type
        if service_type == 'power':
            self._execute_power_service(target_power, dt)
        elif service_type == 'energy':
            self._execute_energy_service(target_power, dt)
    
    def _execute_power_service(self, target_power: float, dt: float):
        """Execute power-based service"""
        current_power = self.current_state.power
        
        if target_power > current_power:
            # Need to increase power (discharge)
            power_increase = min(target_power - current_power, self.config.max_power - current_power)
            self._discharge_battery(power_increase, dt)
        elif target_power < current_power:
            # Need to decrease power (charge)
            power_decrease = min(current_power - target_power, current_power + self.config.max_power)
            self._charge_battery(power_decrease, dt)
    
    def _execute_energy_service(self, target_energy: float, dt: float):
        """Execute energy-based service"""
        current_energy = self.current_state.state_of_charge * self.config.capacity
        
        if target_energy > current_energy:
            # Need to store energy (charge)
            energy_needed = min(target_energy - current_energy, 
                              (self.config.max_soc - self.current_state.state_of_charge) * self.config.capacity)
            power_needed = energy_needed / dt
            self._charge_battery(power_needed, dt)
        elif target_energy < current_energy:
            # Need to release energy (discharge)
            energy_release = min(current_energy - target_energy,
                               (self.current_state.state_of_charge - self.config.min_soc) * self.config.capacity)
            power_release = energy_release / dt
            self._discharge_battery(power_release, dt)
    
    def _charge_battery(self, power: float, dt: float):
        """Charge the battery"""
        if self.current_state.state_of_charge >= self.config.max_soc:
            return
        
        # Calculate energy to charge
        energy = power * dt / 3600  # Convert to kWh
        
        # Apply efficiency
        actual_energy = energy * self.config.charge_efficiency
        
        # Update SOC
        soc_increase = actual_energy / self.config.capacity
        self.current_state.state_of_charge += soc_increase
        
        # Update power and current
        self.current_state.power = -power  # Negative for charging
        self.current_state.current = -power * 1000 / self.current_state.voltage  # A
        
        # Update mode
        self.current_mode = StorageMode.CHARGING
        
        # Update performance metrics
        self.performance_metrics['total_energy_charged'] += actual_energy
        
        self.logger.debug(f"Battery charging: {power:.2f} kW, SOC: {self.current_state.state_of_charge:.3f}")
    
    def _discharge_battery(self, power: float, dt: float):
        """Discharge the battery"""
        if self.current_state.state_of_charge <= self.config.min_soc:
            return
        
        # Calculate energy to discharge
        energy = power * dt / 3600  # Convert to kWh
        
        # Check available energy
        available_energy = (self.current_state.state_of_charge - self.config.min_soc) * self.config.capacity
        energy = min(energy, available_energy)
        
        # Apply efficiency
        actual_energy = energy / self.config.discharge_efficiency
        
        # Update SOC
        soc_decrease = actual_energy / self.config.capacity
        self.current_state.state_of_charge -= soc_decrease
        
        # Update power and current
        actual_power = energy * 3600 / dt  # Convert back to kW
        self.current_state.power = actual_power  # Positive for discharging
        self.current_state.current = actual_power * 1000 / self.current_state.voltage  # A
        
        # Update mode
        self.current_mode = StorageMode.DISCHARGING
        
        # Update performance metrics
        self.performance_metrics['total_energy_discharged'] += energy
        
        self.logger.debug(f"Battery discharging: {actual_power:.2f} kW, SOC: {self.current_state.state_of_charge:.3f}")
    
    def _update_performance_metrics(self, dt: float):
        """Update performance metrics"""
        # Calculate average efficiency
        total_energy_in = self.performance_metrics['total_energy_charged']
        total_energy_out = self.performance_metrics['total_energy_discharged']
        
        if total_energy_in > 0:
            self.performance_metrics['average_efficiency'] = total_energy_out / total_energy_in
        
        # Calculate cycles (simplified)
        total_energy_throughput = total_energy_in + total_energy_out
        self.performance_metrics['total_cycles'] = int(total_energy_throughput / self.config.capacity)
        
        # Update response time
        self.performance_metrics['response_time'] = self.config.response_time
    
    def _store_state_history(self):
        """Store battery state history"""
        # Create a copy of current state
        state_copy = BatteryState(
            timestamp=self.current_state.timestamp,
            state_of_charge=self.current_state.state_of_charge,
            voltage=self.current_state.voltage,
            current=self.current_state.current,
            power=self.current_state.power,
            temperature=self.current_state.temperature,
            health=self.current_state.health
        )
        
        self.state_history.append(state_copy)
        
        # Limit history size
        if len(self.state_history) > 10000:
            self.state_history.pop(0)
    
    def start_service(self, service: StorageService, parameters: Dict[str, Any]) -> bool:
        """
        Start a storage service
        
        Args:
            service: Service to start
            parameters: Service parameters
            
        Returns:
            True if service started successfully
        """
        if self.active_service:
            self.logger.warning(f"Cannot start {service.value}: {self.active_service.value} already active")
            return False
        
        # Configure service
        self.active_services[service] = parameters
        self.active_service = service
        
        # Initialize service performance tracking
        self.service_performance[service] = {
            'start_time': datetime.now(),
            'total_energy': 0.0,
            'total_revenue': 0.0,
            'response_count': 0
        }
        
        self.logger.info(f"Storage service started: {service.value}")
        return True
    
    def stop_service(self) -> bool:
        """
        Stop the active storage service
        
        Returns:
            True if service stopped successfully
        """
        if not self.active_service:
            return False
        
        # Record service completion
        if self.active_service in self.service_performance:
            service_data = self.service_performance[self.active_service]
            service_data['end_time'] = datetime.now()
            service_data['duration'] = service_data['end_time'] - service_data['start_time']
        
        # Clear active service
        self.active_service = None
        self.current_mode = StorageMode.IDLE
        self.current_state.power = 0.0
        self.current_state.current = 0.0
        
        self.logger.info("Storage service stopped")
        return True
    
    def get_available_capacity(self) -> float:
        """Get available storage capacity"""
        return self.current_state.state_of_charge * self.config.capacity
    
    def get_available_power(self) -> float:
        """Get available power capacity"""
        if self.current_mode == StorageMode.CHARGING:
            return self.config.max_power
        else:
            return self.config.max_power
    
    def set_soc(self, soc: float):
        """Set state of charge"""
        soc = np.clip(soc, self.config.min_soc, self.config.max_soc)
        self.current_state.state_of_charge = soc
        self.logger.info(f"State of charge set to: {soc:.3f}")
    
    def get_current_status(self) -> Dict[str, Any]:
        """Get current system status"""
        return {
            'is_active': self.is_active,
            'mode': self.current_mode.value,
            'active_service': self.active_service.value if self.active_service else None,
            'state_of_charge': self.current_state.state_of_charge,
            'voltage': self.current_state.voltage,
            'current': self.current_state.current,
            'power': self.current_state.power,
            'temperature': self.current_state.temperature,
            'health': self.current_state.health,
            'available_capacity': self.get_available_capacity(),
            'available_power': self.get_available_power()
        }
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics"""
        return self.performance_metrics.copy()
    
    def get_state_history(self, duration: timedelta = timedelta(hours=1)) -> List[BatteryState]:
        """Get battery state history for specified duration"""
        cutoff_time = datetime.now() - duration
        return [s for s in self.state_history if s.timestamp >= cutoff_time]
    
    def get_action_history(self, duration: timedelta = timedelta(hours=1)) -> List[StorageAction]:
        """Get action history for specified duration"""
        cutoff_time = datetime.now() - duration
        return [a for a in self.action_history if a.timestamp >= cutoff_time]
    
    def clear_history(self):
        """Clear state and action history"""
        self.state_history.clear()
        self.action_history.clear()
        self.logger.info("History cleared")
    
    def reset_performance_metrics(self):
        """Reset performance metrics"""
        self.performance_metrics = {
            'total_energy_charged': 0.0,
            'total_energy_discharged': 0.0,
            'total_cycles': 0,
            'average_efficiency': 0.0,
            'availability': 1.0,
            'response_time': 0.0,
            'service_revenue': 0.0,
            'arbitrage_revenue': 0.0
        }
        
        self.logger.info("Performance metrics reset") 