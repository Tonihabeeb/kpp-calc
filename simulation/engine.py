import time
import threading
import math
import logging
from typing import Any, Dict, List, Optional, Union
from queue import Queue

# Import configuration modules
from config import ConfigManager
from config.parameter_schema import get_default_parameters, validate_kpp_system_parameters
from config.config import RHO_WATER, G  # Add physics constants

# Import simulation components
from simulation.grid_services.grid_services_coordinator import GridConditions, create_standard_grid_services_coordinator
from simulation.components.thermal import ThermalModel
from simulation.components.pneumatics import PneumaticSystem
from simulation.components.integrated_electrical_system import IntegratedElectricalSystem
from simulation.components.integrated_drivetrain import create_standard_kpp_drivetrain
from simulation.components.fluid import Fluid
from simulation.components.floater import Floater
from simulation.components.environment import Environment
from simulation.components.control import Control
from simulation.components.chain import Chain

"""
SimulationEngine: orchestrates all simulation modules
Coordinates state updates, manages simulation loop,
and handles cross-module interactions
"""


class SimulationEngine:
    """
    Simulation engine class.
    Coordinates all simulation components and manages the simulation loop.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the simulation engine.
        
        Args:
            config: Configuration dictionary for the simulation
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        self.is_running = False
        self.simulation_thread = None
        self.state_queue = Queue()
        
        # Initialize configuration manager
        self.config_manager = ConfigManager()
        
        # Initialize components
        self._initialize_components()
    
    def _initialize_components(self):
        """Initialize simulation components."""
        self.logger.info("Initializing simulation components...")
        
        try:
            # Initialize grid services
            self.grid_services = create_standard_grid_services_coordinator()
            
            # Initialize thermal model
            self.thermal_model = ThermalModel()
            
            # Initialize pneumatic system
            self.pneumatic_system = PneumaticSystem()
            
            # Initialize drivetrain
            self.drivetrain = create_standard_kpp_drivetrain()
            
            # Initialize fluid system
            self.fluid = Fluid()
            
            # Initialize floater
            self.floater = Floater()
            
            # Initialize environment
            self.environment = Environment()
            
            # Initialize control system
            self.control = Control()
            
            # Initialize chain system
            self.chain = Chain()
            
            self.logger.info("All simulation components initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Error initializing components: {e}")
            raise
    
    def start(self):
        """Start the simulation."""
        if self.is_running:
            self.logger.warning("Simulation is already running")
            return
        
        self.is_running = True
        self.simulation_thread = threading.Thread(target=self._simulation_loop)
        self.simulation_thread.start()
        self.logger.info("Simulation started")
    
    def stop(self):
        """Stop the simulation."""
        self.is_running = False
        if self.simulation_thread:
            self.simulation_thread.join()
        self.logger.info("Simulation stopped")
    
    def _simulation_loop(self):
        """Main simulation loop."""
        while self.is_running:
            try:
                self._update_simulation_state()
                time.sleep(0.01)  # 10ms timestep
            except Exception as e:
                self.logger.error(f"Error in simulation loop: {e}")
                self.is_running = False
                break
    
    def _update_simulation_state(self):
        """Update simulation state for one timestep."""
        try:
            # Update all component states
            if hasattr(self, 'floater'):
                self.floater.update_position(self.floater.physics_data.position + 0.1, 0.01)
            
            if hasattr(self, 'thermal_model'):
                self.thermal_model.update(0.01)
            
            if hasattr(self, 'pneumatic_system'):
                self.pneumatic_system.update(0.01)
            
            if hasattr(self, 'drivetrain'):
                self.drivetrain.update(0.01)
            
            if hasattr(self, 'environment'):
                self.environment.update(0.01)
            
            if hasattr(self, 'control'):
                self.control.update(0.01)
            
            # Update grid services
            if hasattr(self, 'grid_services'):
                self.grid_services.update(0.01)
                
        except Exception as e:
            self.logger.error(f"Error updating simulation state: {e}")
    
    def get_state(self) -> Dict[str, Any]:
        """Get current simulation state."""
        try:
            state = {
                "is_running": self.is_running,
                "timestamp": time.time(),
                "components": {}
            }
            
            # Add component states
            if hasattr(self, 'floater'):
                state["components"]["floater"] = self.floater.get_physics_data().__dict__
            
            if hasattr(self, 'thermal_model'):
                state["components"]["thermal"] = self.thermal_model.get_state()
            
            if hasattr(self, 'pneumatic_system'):
                state["components"]["pneumatic"] = self.pneumatic_system.get_state()
            
            if hasattr(self, 'drivetrain'):
                state["components"]["drivetrain"] = self.drivetrain.get_comprehensive_state()
            
            if hasattr(self, 'environment'):
                state["components"]["environment"] = self.environment.get_state()
            
            if hasattr(self, 'control'):
                state["components"]["control"] = self.control.get_state()
            
            if hasattr(self, 'grid_services'):
                state["components"]["grid_services"] = self.grid_services.get_state()
            
            return state
            
        except Exception as e:
            self.logger.error(f"Error getting simulation state: {e}")
            return {
                "is_running": self.is_running,
                "timestamp": time.time(),
                "error": str(e),
                "components": {}
            }

