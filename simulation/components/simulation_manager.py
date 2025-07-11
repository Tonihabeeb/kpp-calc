"""
Enhanced simulation manager with integrated physics engine.
"""

from typing import Dict, Optional, Any
import logging
import threading
from dataclasses import dataclass

from kpp_simulator.core.physics_engine import PhysicsEngine, PhysicsConfig
from simulation.components.floater.state_machine import FloaterStateMachine
from simulation.components.control.system import ControlSystem
from simulation.components.pneumatic.system import PneumaticSystem
from simulation.integration.physics_integration import PhysicsIntegration, IntegrationConfig

@dataclass
class SimulationConfig:
    """Simulation configuration"""
    physics: PhysicsConfig = PhysicsConfig()
    integration: IntegrationConfig = IntegrationConfig()
    enable_validation: bool = True
    log_level: str = "INFO"

class SimulationManager:
    """
    Enhanced simulation manager with integrated physics.
    Coordinates all simulation components and data flow.
    """
    
    def __init__(self, config: Optional[SimulationConfig] = None):
        """
        Initialize simulation manager.
        
        Args:
            config: Simulation configuration
        """
        self.config = config or SimulationConfig()
        
        # Configure logging
        logging.basicConfig(level=self.config.log_level)
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.physics = PhysicsEngine(self.config.physics)
        self.state_machine = FloaterStateMachine()
        self.control = ControlSystem()
        self.pneumatics = PneumaticSystem()
        
        # Initialize integration layer
        self.integration = PhysicsIntegration(
            physics_engine=self.physics,
            state_machine=self.state_machine,
            control_system=self.control,
            pneumatic_system=self.pneumatics,
            config=self.config.integration
        )
        
        # Thread safety
        self._lock = threading.Lock()
        self._running = False
        
        self.logger.info("Enhanced simulation manager initialized")
    
    def start(self) -> bool:
        """Start simulation"""
        with self._lock:
            if self._running:
                return False
            
            try:
                # Start integration layer
                if not self.integration.start():
                    raise RuntimeError("Failed to start physics integration")
                
                self._running = True
                self.logger.info("Simulation started")
                return True
                
            except Exception as e:
                self.logger.error(f"Failed to start simulation: {e}")
                self._running = False
                return False
    
    def stop(self):
        """Stop simulation"""
        with self._lock:
            if not self._running:
                return
            
            try:
                # Stop integration layer
                self.integration.stop()
                
                self._running = False
                self.logger.info("Simulation stopped")
                
            except Exception as e:
                self.logger.error(f"Error stopping simulation: {e}")
    
    def get_state(self) -> Dict[str, Any]:
        """Get complete simulation state"""
        try:
            return {
                'running': self._running,
                'physics': self.physics.get_state(),
                'integration': self.integration.get_status(),
                'state_machine': {
                    'state': self.state_machine.current_state,
                    'history': self.state_machine.get_history()
                },
                'control': self.control.get_status(),
                'pneumatics': self.pneumatics.get_status()
            }
        except Exception as e:
            self.logger.error(f"Error getting simulation state: {e}")
            return {'error': str(e)}
    
    def update_config(self, new_config: Dict[str, Any]) -> bool:
        """
        Update simulation configuration.
        
        Args:
            new_config: Dictionary of configuration updates
            
        Returns:
            True if update successful
        """
        try:
            with self._lock:
                # Update physics config
                if 'physics' in new_config:
                    self.physics.config = PhysicsConfig(**new_config['physics'])
                
                # Update integration config
                if 'integration' in new_config:
                    self.integration.config = IntegrationConfig(**new_config['integration'])
                
                # Update general config
                if 'enable_validation' in new_config:
                    self.config.enable_validation = new_config['enable_validation']
                
                if 'log_level' in new_config:
                    self.config.log_level = new_config['log_level']
                    logging.getLogger().setLevel(new_config['log_level'])
                
                self.logger.info("Configuration updated")
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to update configuration: {e}")
            return False
    
    def reset(self):
        """Reset simulation to initial state"""
        with self._lock:
            try:
                # Stop if running
                if self._running:
                    self.stop()
                
                # Reset all components
                self.physics.reset()
                self.state_machine.reset()
                self.control.reset()
                self.pneumatics.reset()
                
                self.logger.info("Simulation reset")
                
            except Exception as e:
                self.logger.error(f"Error resetting simulation: {e}")
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get simulation performance metrics"""
        try:
            return {
                'physics': self.physics.performance_metrics,
                'state_machine': self.state_machine.get_metrics(),
                'control': self.control.get_metrics(),
                'pneumatics': self.pneumatics.get_metrics()
            }
        except Exception as e:
            self.logger.error(f"Error getting metrics: {e}")
            return {'error': str(e)} 