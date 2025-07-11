"""
Integration layer for enhanced physics engine.
Connects physics calculations with state machine and control systems.
"""

from typing import Dict, Optional, Any
import logging
import threading
from dataclasses import dataclass

from kpp_simulator.core.physics_engine import PhysicsEngine, PhysicsConfig, PhysicsState
from simulation.components.floater.state_machine import FloaterStateMachine, FloaterState
from simulation.components.control.system import ControlSystem
from simulation.components.pneumatic.system import PneumaticSystem

@dataclass
class IntegrationConfig:
    """Configuration for physics integration"""
    update_rate: float = 10.0  # Hz
    control_update_rate: float = 1.0  # Hz
    state_update_rate: float = 2.0  # Hz
    max_queue_size: int = 100

class PhysicsIntegration:
    """
    Integrates enhanced physics engine with existing systems.
    Handles:
    - State machine synchronization
    - Control system feedback
    - Real-time data flow
    - Thread safety
    - Error recovery
    """
    
    def __init__(self,
                 physics_engine: PhysicsEngine,
                 state_machine: FloaterStateMachine,
                 control_system: ControlSystem,
                 pneumatic_system: PneumaticSystem,
                 config: Optional[IntegrationConfig] = None):
        """
        Initialize integration layer.
        
        Args:
            physics_engine: Enhanced physics engine instance
            state_machine: Floater state machine instance
            control_system: Control system instance
            pneumatic_system: Pneumatic system instance
            config: Integration configuration
        """
        self.physics = physics_engine
        self.state_machine = state_machine
        self.control = control_system
        self.pneumatics = pneumatic_system
        self.config = config or IntegrationConfig()
        
        self.logger = logging.getLogger(__name__)
        
        # Thread safety
        self._lock = threading.Lock()
        self._running = False
        self._update_thread = None
        
        # State tracking
        self.last_physics_state: Optional[Dict[str, Any]] = None
        self.last_control_update = 0.0
        self.last_state_update = 0.0
        
        self.logger.info("Physics integration layer initialized")
    
    def start(self) -> bool:
        """Start integration layer"""
        with self._lock:
            if self._running:
                return False
            
            try:
                self._running = True
                self._update_thread = threading.Thread(
                    target=self._update_loop,
                    daemon=True
                )
                self._update_thread.start()
                self.logger.info("Physics integration started")
                return True
                
            except Exception as e:
                self.logger.error(f"Failed to start physics integration: {e}")
                self._running = False
                return False
    
    def stop(self):
        """Stop integration layer"""
        with self._lock:
            self._running = False
            if self._update_thread:
                self._update_thread.join()
                self._update_thread = None
        self.logger.info("Physics integration stopped")
    
    def _update_loop(self):
        """Main update loop"""
        update_interval = 1.0 / self.config.update_rate
        
        while self._running:
            try:
                # Update physics with proper timing
                self.physics.update(update_interval)
                
                # Get latest physics state
                physics_state = self.physics.get_state()
                self.last_physics_state = physics_state
                
                # Check if control update needed
                if (physics_state['time'] - self.last_control_update >=
                        1.0 / self.config.control_update_rate):
                    self._update_control(physics_state)
                    self.last_control_update = physics_state['time']
                
                # Check if state machine update needed
                if (physics_state['time'] - self.last_state_update >=
                        1.0 / self.config.state_update_rate):
                    self._update_state_machine(physics_state)
                    self.last_state_update = physics_state['time']
                
            except Exception as e:
                self.logger.error(f"Physics integration update failed: {e}")
                # Continue running but log error
    
    def _update_control(self, physics_state: Dict[str, Any]):
        """Update control system with physics data"""
        try:
            # Extract relevant physics data for control
            control_data = {
                'position': physics_state['position'],
                'velocity': physics_state['velocity'],
                'forces': physics_state['forces'],
                'energy': physics_state['energy']
            }
            
            # Add enhanced physics data if available
            if 'buoyancy_results' in physics_state:
                control_data['buoyancy'] = physics_state['buoyancy_results']
            if 'drag_results' in physics_state:
                control_data['drag'] = physics_state['drag_results']
            
            # Update control system
            self.control.update(control_data)
            
            # Get control commands
            commands = self.control.get_commands()
            
            # Apply control commands to pneumatic system
            self.pneumatics.apply_commands(commands)
            
        except Exception as e:
            self.logger.error(f"Control update failed: {e}")
    
    def _update_state_machine(self, physics_state: Dict[str, Any]):
        """Update state machine with physics data"""
        try:
            # Determine appropriate state based on physics
            if physics_state.get('validation', {}).get('stability', {}).get('passed', True):
                # Normal operation states
                if physics_state['position'][2] < -5.0:  # Deep submersion
                    new_state = FloaterState.FULL
                elif physics_state['position'][2] > -0.1:  # Near surface
                    new_state = FloaterState.EMPTY
                else:
                    new_state = FloaterState.FILLING
            else:
                # Error state if physics validation fails
                new_state = FloaterState.ERROR
            
            # Update state machine
            self.state_machine.transition_to(new_state)
            
        except Exception as e:
            self.logger.error(f"State machine update failed: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get integration layer status"""
        return {
            'running': self._running,
            'last_physics_state': self.last_physics_state,
            'last_control_update': self.last_control_update,
            'last_state_update': self.last_state_update,
            'state_machine_state': self.state_machine.current_state,
            'control_status': self.control.get_status(),
            'pneumatic_status': self.pneumatics.get_status()
        } 