"""
Loss Tracking System for KPP Simulator
Integrates with drivetrain and electrical systems for comprehensive loss analysis.
"""

import logging
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime

from ..physics.integrated_loss_model import (
    IntegratedLossModel, SystemLosses, LossResult, LossType
)
from ..optimization.loss_optimization import LossOptimizer, OptimizationSuggestion

@dataclass
class LossTrackingState:
    """Loss tracking system state"""
    timestamp: datetime
    system_losses: SystemLosses
    component_losses: Dict[str, Dict[str, LossResult]]
    cumulative_energy_loss: float
    average_efficiency: float
    optimization_suggestions: List[Dict[str, Any]]

class LossTrackingSystem:
    """
    Comprehensive loss tracking system that integrates with all major components
    and provides real-time loss monitoring and optimization suggestions.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize loss tracking system"""
        self.logger = logging.getLogger(__name__)
        self.config = config or {}
        
        # Initialize loss model and optimizer
        self.loss_model = IntegratedLossModel()
        self.loss_optimizer = LossOptimizer(config)
        
        # Initialize state
        self.current_state = None
        self.history = []
        self.max_history_length = self.config.get('max_history_length', 1000)
        
        # Performance metrics
        self.peak_power_loss = 0.0
        self.total_energy_loss = 0.0
        self.start_time = datetime.now()
    
    def update(self, drivetrain_state: Any, electrical_state: Any) -> None:
        """
        Update loss tracking with current system state.
        
        Args:
            drivetrain_state: Current drivetrain system state
            electrical_state: Current electrical system state
        """
        try:
            # Calculate losses using integrated loss model
            system_losses = self.loss_model.calculate_system_losses(
                drivetrain_state, electrical_state
            )
            
            # Calculate component-specific losses
            component_losses = {
                'drivetrain': self.loss_model.calculate_drivetrain_losses(drivetrain_state),
                'generator': self.loss_model.calculate_generator_losses(electrical_state),
                'power_electronics': self.loss_model.calculate_power_electronics_losses(electrical_state)
            }
            
            # Update performance metrics
            self.peak_power_loss = max(self.peak_power_loss, system_losses.total_losses)
            self.total_energy_loss += system_losses.total_losses * self.config.get('time_step', 0.01)
            
            # Get optimization suggestions
            optimization_suggestions = self.loss_optimizer.get_optimization_suggestions(
                mechanical_losses=component_losses['drivetrain'],
                electrical_losses={**component_losses['generator'], **component_losses['power_electronics']},
                system_losses=system_losses
            )
            
            # Create new state
            new_state = LossTrackingState(
                timestamp=datetime.now(),
                system_losses=system_losses,
                component_losses=component_losses,
                cumulative_energy_loss=self.total_energy_loss,
                average_efficiency=self._calculate_average_efficiency(),
                optimization_suggestions=[{
                    'component': s.component,
                    'loss_type': s.loss_type,
                    'severity': s.severity,
                    'message': s.message,
                    'potential_savings': s.potential_savings,
                    'confidence': s.confidence,
                    'implementation_difficulty': s.implementation_difficulty,
                    'parameters': s.parameters
                } for s in optimization_suggestions]
            )
            
            # Update state and history
            self.current_state = new_state
            self.history.append(new_state)
            
            # Trim history if needed
            if len(self.history) > self.max_history_length:
                self.history = self.history[-self.max_history_length:]
            
        except Exception as e:
            self.logger.error(f"Error updating loss tracking: {e}")
            raise
    
    def get_current_state(self) -> Optional[LossTrackingState]:
        """Get current loss tracking state"""
        return self.current_state
    
    def get_history(self, limit: Optional[int] = None) -> List[LossTrackingState]:
        """
        Get loss tracking history.
        
        Args:
            limit: Optional limit on number of history entries to return
        
        Returns:
            List of historical states
        """
        if limit is not None:
            return self.history[-limit:]
        return self.history
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics"""
        current_state = self.get_current_state()
        if not current_state:
            return {}
        
        return {
            'peak_power_loss': self.peak_power_loss,
            'total_energy_loss': self.total_energy_loss,
            'average_efficiency': self._calculate_average_efficiency(),
            'uptime': (datetime.now() - self.start_time).total_seconds(),
            'current_efficiency': current_state.system_losses.overall_efficiency
        }
    
    def get_optimization_suggestions(self) -> List[Dict[str, Any]]:
        """Get current optimization suggestions"""
        current_state = self.get_current_state()
        if not current_state:
            return []
        return current_state.optimization_suggestions
    
    def _calculate_average_efficiency(self) -> float:
        """Calculate average system efficiency"""
        if not self.history:
            return 0.0
        
        total_efficiency = sum(state.system_losses.overall_efficiency for state in self.history)
        return total_efficiency / len(self.history) 