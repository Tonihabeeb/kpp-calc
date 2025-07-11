import time
import logging
from typing import Any, Dict, Optional, List
from simulation.schemas import ComponentStatus, ManagerInterface, ManagerType, SimulationError
from enum import Enum
from abc import ABC, abstractmethod
"""
Base manager interface and common utilities for KPP Simulator managers.
Provides standardized interface, error handling, and performance monitoring.
"""


class BaseManager:
    """Base class for all managers in the simulation"""
    
    def __init__(self, manager_type: ManagerType):
        self.interface = ManagerInterface(
            manager_type=manager_type,
            status=ComponentStatus.INACTIVE
        )
        self.logger = logging.getLogger(f"{self.__class__.__name__}")
        
    def initialize(self) -> bool:
        """Initialize the manager"""
        try:
            self.interface.status = ComponentStatus.ACTIVE
            return True
        except Exception as e:
            self.handle_error("INIT_ERROR", str(e))
            return False
            
    def shutdown(self) -> bool:
        """Shutdown the manager"""
        try:
            self.interface.status = ComponentStatus.INACTIVE
            return True
        except Exception as e:
            self.handle_error("SHUTDOWN_ERROR", str(e))
            return False
            
    def handle_error(self, error_code: str, message: str, component: Optional[str] = None) -> None:
        """Handle and log an error"""
        error = SimulationError(
            error_code=error_code,
            message=message,
            component=component,
            timestamp=0.0  # TODO: Add proper timestamp
        )
        self.interface.errors.append(error)
        self.logger.error(f"{error_code}: {message}")
        
        if self.interface.status != ComponentStatus.ERROR:
            self.interface.status = ComponentStatus.ERROR
            
    def clear_errors(self) -> None:
        """Clear all errors"""
        self.interface.errors = []
        if self.interface.status == ComponentStatus.ERROR:
            self.interface.status = ComponentStatus.ACTIVE
            
    def register_component(self, component_id: str) -> bool:
        """Register a new component"""
        try:
            if component_id not in self.interface.components:
                self.interface.components[component_id] = ComponentStatus.INACTIVE
                return True
            return False
        except Exception as e:
            self.handle_error("REGISTRATION_ERROR", str(e), component_id)
            return False
            
    def unregister_component(self, component_id: str) -> bool:
        """Unregister a component"""
        try:
            if component_id in self.interface.components:
                del self.interface.components[component_id]
                return True
            return False
        except Exception as e:
            self.handle_error("UNREGISTRATION_ERROR", str(e), component_id)
            return False
            
    def update_component_status(self, component_id: str, status: ComponentStatus) -> bool:
        """Update the status of a component"""
        try:
            if component_id in self.interface.components:
                self.interface.components[component_id] = status
                return True
            return False
        except Exception as e:
            self.handle_error("STATUS_UPDATE_ERROR", str(e), component_id)
            return False
            
    def get_component_status(self, component_id: str) -> Optional[ComponentStatus]:
        """Get the status of a component"""
        return self.interface.components.get(component_id)
        
    def get_active_components(self) -> List[str]:
        """Get a list of active components"""
        return [
            component_id
            for component_id, status in self.interface.components.items()
            if status == ComponentStatus.ACTIVE
        ]
        
    def get_error_components(self) -> List[str]:
        """Get a list of components in error state"""
        return [
            component_id
            for component_id, status in self.interface.components.items()
            if status == ComponentStatus.ERROR
        ]
        
    def is_healthy(self) -> bool:
        """Check if the manager is in a healthy state"""
        return (
            self.interface.status == ComponentStatus.ACTIVE and
            not self.interface.errors and
            all(
                status != ComponentStatus.ERROR
                for status in self.interface.components.values()
            )
        )

