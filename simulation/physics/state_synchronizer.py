import time
import logging
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

"""
State Synchronization System for KPP Simulation (Stage 2)
Ensures immediate synchronization between floater state changes and physics calculations.
"""

class SyncStatus(str, Enum):
    """Synchronization status enumeration"""
    SYNCHRONIZED = "synchronized"
    DESYNCHRONIZED = "desynchronized"
    CORRECTING = "correcting"
    ERROR = "error"

@dataclass
class SyncOperation:
    """Synchronization operation data"""
    timestamp: float
    floater_id: int
    operation_type: str
    old_value: Any
    new_value: Any
    success: bool
    error_message: Optional[str] = None

@dataclass
class SyncMetrics:
    """Synchronization metrics"""
    total_operations: int = 0
    successful_operations: int = 0
    failed_operations: int = 0
    average_sync_time: float = 0.0
    last_sync_time: float = 0.0
    error_rate: float = 0.0

class StateSynchronizer:
    """
    Real-time state synchronization system for KPP simulation.
    Ensures consistency between floater states and physics calculations.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the state synchronizer.
        
        Args:
            config: Configuration dictionary for synchronization
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # Synchronization settings
        self.auto_sync_enabled = True
        self.sync_interval = self.config.get('sync_interval', 0.01)  # seconds
        self.max_sync_delay = self.config.get('max_sync_delay', 0.1)  # seconds
        
        # State tracking
        self.sync_history: List[SyncOperation] = []
        self.last_sync_time = 0.0
        self.error_count = 0
        self.correction_count = 0
        
        # Performance metrics
        self.sync_metrics = SyncMetrics()
        self.sync_times: List[float] = []
        
        # Floater state cache
        self.floater_states: Dict[int, Dict[str, Any]] = {}
        
        # Physics constants
        self.gravity = 9.81  # m/s²
        self.water_density = 1000.0  # kg/m³
        self.air_density = 1.225  # kg/m³
        
        # Mass configuration
        self.container_mass = self.config.get('container_mass', 10.0)  # kg
        self.water_mass_per_volume = self.config.get('water_mass_per_volume', 1000.0)  # kg/m³
        
        self.logger.info("State synchronizer initialized with auto_sync=%s", self.auto_sync_enabled)
    
    def validate_mass_state_consistency(self, floater: Any, floater_id: int) -> Tuple[bool, str]:
        """
        Validate mass-state consistency for a floater.
        
        Args:
            floater: Floater object
            floater_id: Floater identifier
            
        Returns:
            Tuple of (is_consistent, error_message)
        """
        try:
            # Get floater properties
            state = getattr(floater, 'state', 'empty')
            mass = getattr(floater, 'mass', 0.0)
            volume = getattr(floater, 'volume', 0.4)
            air_fill_level = getattr(floater, 'air_fill_level', 0.0)
            
            # Calculate expected mass based on state
            if state == 'empty' or state == 'venting':
                # Light state: container mass only
                expected_mass = self.container_mass
            elif state == 'full' or state == 'filling':
                # Heavy state: container + water mass
                water_volume = volume * (1.0 - air_fill_level)
                expected_mass = self.container_mass + (water_volume * self.water_mass_per_volume)
            else:
                # Unknown state
                return False, f"Unknown state: {state}"
            
            # Check mass consistency with tolerance
            mass_tolerance = 0.1  # kg
            mass_difference = abs(mass - expected_mass)
            
            if mass_difference > mass_tolerance:
                return False, f"Mass inconsistency: expected={expected_mass:.2f}kg, actual={mass:.2f}kg"
            
            return True, "Mass state consistent"
            
        except Exception as e:
            return False, f"Mass validation error: {str(e)}"
    
    def correct_mass_state(self, floater: Any, floater_id: int) -> SyncOperation:
        """
        Correct mass-state inconsistency.
        
        Args:
            floater: Floater object
            floater_id: Floater identifier
            
        Returns:
            Synchronization operation result
        """
        start_time = time.time()
        
        try:
            # Get current state
            state = getattr(floater, 'state', 'empty')
            volume = getattr(floater, 'volume', 0.4)
            air_fill_level = getattr(floater, 'air_fill_level', 0.0)
            old_mass = getattr(floater, 'mass', 0.0)
            
            # Calculate correct mass
            if state == 'empty' or state == 'venting':
                new_mass = self.container_mass
            elif state == 'full' or state == 'filling':
                water_volume = volume * (1.0 - air_fill_level)
                new_mass = self.container_mass + (water_volume * self.water_mass_per_volume)
            else:
                new_mass = old_mass  # Keep current mass for unknown states
            
            # Update floater mass
            floater.mass = new_mass
            
            # Create sync operation
            sync_op = SyncOperation(
                timestamp=start_time,
                floater_id=floater_id,
                operation_type="mass_correction",
                old_value=old_mass,
                new_value=new_mass,
                success=True
            )
            
            self.correction_count += 1
            self.logger.info("Mass corrected for floater %d: %.2f kg -> %.2f kg", 
                           floater_id, old_mass, new_mass)
            
            return sync_op
            
        except Exception as e:
            sync_op = SyncOperation(
                timestamp=start_time,
                floater_id=floater_id,
                operation_type="mass_correction",
                old_value=getattr(floater, 'mass', 0.0),
                new_value=getattr(floater, 'mass', 0.0),
                success=False,
                error_message=str(e)
            )
            
            self.error_count += 1
            self.logger.error("Mass correction failed for floater %d: %s", floater_id, e)
            
            return sync_op
    
    def validate_velocity_consistency(self, floater: Any, floater_id: int, 
                                    chain_velocity: float) -> Tuple[bool, str]:
        """
        Validate velocity consistency with chain motion.
        
        Args:
            floater: Floater object
            floater_id: Floater identifier
            chain_velocity: Chain velocity (m/s)
            
        Returns:
            Tuple of (is_consistent, error_message)
        """
        try:
            # Get floater properties
            velocity = getattr(floater, 'velocity', 0.0)
            position = getattr(floater, 'position', 0.0)
            tank_height = self.config.get('tank_height', 10.0)
            
            # Determine expected velocity based on position
            # Bottom half: ascending (positive velocity)
            # Top half: descending (negative velocity)
            if position < tank_height / 2:
                expected_velocity = abs(chain_velocity)
            else:
                expected_velocity = -abs(chain_velocity)
            
            # Check velocity consistency with tolerance
            velocity_tolerance = 0.5  # m/s
            velocity_difference = abs(velocity - expected_velocity)
            
            if velocity_difference > velocity_tolerance:
                return False, f"Velocity inconsistency: expected={expected_velocity:.2f}m/s, actual={velocity:.2f}m/s"
            
            return True, "Velocity consistent"
            
        except Exception as e:
            return False, f"Velocity validation error: {str(e)}"
    
    def correct_velocity_consistency(self, floater: Any, floater_id: int, 
                                   chain_velocity: float) -> SyncOperation:
        """
        Correct velocity inconsistency.
        
        Args:
            floater: Floater object
            floater_id: Floater identifier
            chain_velocity: Chain velocity (m/s)
            
        Returns:
            Synchronization operation result
        """
        start_time = time.time()
        
        try:
            # Get current velocity
            old_velocity = getattr(floater, 'velocity', 0.0)
            position = getattr(floater, 'position', 0.0)
            tank_height = self.config.get('tank_height', 10.0)
            
            # Calculate correct velocity
            if position < tank_height / 2:
                new_velocity = abs(chain_velocity)
            else:
                new_velocity = -abs(chain_velocity)
            
            # Update floater velocity
            floater.velocity = new_velocity
            
            # Create sync operation
            sync_op = SyncOperation(
                timestamp=start_time,
                floater_id=floater_id,
                operation_type="velocity_correction",
                old_value=old_velocity,
                new_value=new_velocity,
                success=True
            )
            
            self.correction_count += 1
            self.logger.info("Velocity corrected for floater %d: %.2f m/s -> %.2f m/s", 
                           floater_id, old_velocity, new_velocity)
            
            return sync_op
            
        except Exception as e:
            sync_op = SyncOperation(
                timestamp=start_time,
                floater_id=floater_id,
                operation_type="velocity_correction",
                old_value=getattr(floater, 'velocity', 0.0),
                new_value=getattr(floater, 'velocity', 0.0),
                success=False,
                error_message=str(e)
            )
            
            self.error_count += 1
            self.logger.error("Velocity correction failed for floater %d: %s", floater_id, e)
            
            return sync_op
    
    def validate_physics_consistency(self, floater: Any, floater_id: int) -> Tuple[bool, str]:
        """
        Validate overall physics consistency.
        
        Args:
            floater: Floater object
            floater_id: Floater identifier
            
        Returns:
            Tuple of (is_consistent, error_message)
        """
        try:
            # Check position bounds
            position = getattr(floater, 'position', 0.0)
            tank_height = self.config.get('tank_height', 10.0)
            
            if position < 0.0 or position > tank_height:
                return False, f"Position out of bounds: {position:.2f}m"
            
            # Check velocity bounds
            velocity = getattr(floater, 'velocity', 0.0)
            max_velocity = self.config.get('max_velocity', 10.0)
            
            if abs(velocity) > max_velocity:
                return False, f"Velocity out of bounds: {velocity:.2f}m/s"
            
            # Check state consistency
            state = getattr(floater, 'state', 'empty')
            air_fill_level = getattr(floater, 'air_fill_level', 0.0)
            
            if state == 'empty' and air_fill_level > 0.1:
                return False, f"State inconsistency: empty state with air_fill_level={air_fill_level:.2f}"
            
            if state == 'full' and air_fill_level < 0.9:
                return False, f"State inconsistency: full state with air_fill_level={air_fill_level:.2f}"
            
            return True, "Physics consistent"
            
        except Exception as e:
            return False, f"Physics validation error: {str(e)}"
    
    def synchronize_floater_state(self, floater: Any, floater_id: int, 
                                chain_velocity: float) -> List[SyncOperation]:
        """
        Synchronize floater state with physics calculations.
        
        Args:
            floater: Floater object
            floater_id: Floater identifier
            chain_velocity: Chain velocity (m/s)
            
        Returns:
            List of synchronization operations performed
        """
        start_time = time.time()
        sync_operations = []
        
        try:
            # Validate mass-state consistency
            mass_consistent, mass_error = self.validate_mass_state_consistency(floater, floater_id)
            if not mass_consistent:
                mass_correction = self.correct_mass_state(floater, floater_id)
                sync_operations.append(mass_correction)
            
            # Validate velocity consistency
            velocity_consistent, velocity_error = self.validate_velocity_consistency(floater, floater_id, chain_velocity)
            if not velocity_consistent:
                velocity_correction = self.correct_velocity_consistency(floater, floater_id, chain_velocity)
                sync_operations.append(velocity_correction)
            
            # Validate overall physics consistency
            physics_consistent, physics_error = self.validate_physics_consistency(floater, floater_id)
            if not physics_consistent:
                # Log physics inconsistency but don't auto-correct
                self.logger.warning("Physics inconsistency for floater %d: %s", floater_id, physics_error)
            
            # Update sync metrics
            sync_time = time.time() - start_time
            self.sync_times.append(sync_time)
            self.sync_metrics.total_operations += len(sync_operations)
            self.sync_metrics.successful_operations += sum(1 for op in sync_operations if op.success)
            self.sync_metrics.failed_operations += sum(1 for op in sync_operations if not op.success)
            
            # Calculate average sync time
            if len(self.sync_times) > 0:
                self.sync_metrics.average_sync_time = sum(self.sync_times) / len(self.sync_times)
            
            # Calculate error rate
            if self.sync_metrics.total_operations > 0:
                self.sync_metrics.error_rate = self.sync_metrics.failed_operations / self.sync_metrics.total_operations
            
            self.sync_metrics.last_sync_time = start_time
            
            # Add operations to history
            self.sync_history.extend(sync_operations)
            
            # Log sync results
            if sync_operations:
                self.logger.info("Synchronized floater %d: %d operations, time=%.3fs", 
                               floater_id, len(sync_operations), sync_time)
            
            return sync_operations
            
        except Exception as e:
            self.logger.error("Synchronization error for floater %d: %s", floater_id, e)
            self.error_count += 1
            return []
    
    def synchronize_all_floaters(self, floaters: List[Any], chain_velocity: float) -> Dict[str, Any]:
        """
        Synchronize all floaters.
        
        Args:
            floaters: List of floater objects
            chain_velocity: Chain velocity (m/s)
            
        Returns:
            Synchronization summary
        """
        start_time = time.time()
        total_operations = 0
        total_corrections = 0
        total_errors = 0
        
        for i, floater in enumerate(floaters):
            operations = self.synchronize_floater_state(floater, i, chain_velocity)
            total_operations += len(operations)
            total_corrections += sum(1 for op in operations if op.success)
            total_errors += sum(1 for op in operations if not op.success)
        
        sync_time = time.time() - start_time
        
        summary = {
            'timestamp': start_time,
            'total_floaters': len(floaters),
            'total_operations': total_operations,
            'total_corrections': total_corrections,
            'total_errors': total_errors,
            'sync_time': sync_time,
            'success_rate': total_corrections / max(total_operations, 1)
        }
        
        # Log summary periodically
        if total_operations > 0 and self.sync_metrics.total_operations % 100 == 0:
            self.logger.info("Sync summary: %d operations, %d corrections, %.1f%% success rate", 
                           total_operations, total_corrections, summary['success_rate'] * 100)
        
        return summary
    
    def get_sync_metrics(self) -> SyncMetrics:
        """
        Get synchronization metrics.
        
        Returns:
            Synchronization metrics
        """
        return self.sync_metrics
    
    def get_sync_history(self, limit: Optional[int] = None) -> List[SyncOperation]:
        """
        Get synchronization history.
        
        Args:
            limit: Maximum number of operations to return
            
        Returns:
            List of synchronization operations
        """
        if limit is None:
            return self.sync_history.copy()
        else:
            return self.sync_history[-limit:]
    
    def clear_history(self) -> None:
        """Clear synchronization history."""
        self.sync_history.clear()
        self.sync_times.clear()
        self.logger.info("Synchronization history cleared")
    
    def reset(self) -> None:
        """Reset state synchronizer."""
        self.sync_history.clear()
        self.sync_times.clear()
        self.floater_states.clear()
        self.last_sync_time = 0.0
        self.error_count = 0
        self.correction_count = 0
        self.sync_metrics = SyncMetrics()
        self.logger.info("State synchronizer reset")

