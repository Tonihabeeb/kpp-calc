"""
Loss Monitoring API Routes
"""

from typing import Dict, Any, List
from datetime import datetime
import json

from flask import Blueprint, jsonify, request
from simulation.components.loss_tracking_system import LossTrackingSystem
from utils.component_manager import get_component_manager

loss_monitoring_bp = Blueprint('loss_monitoring', __name__)

@loss_monitoring_bp.route('/api/losses/current', methods=['GET'])
def get_current_losses():
    """Get current system losses"""
    try:
        # Get loss tracking system from component manager
        loss_tracking = get_component_manager().get_loss_tracking_system()
        if not loss_tracking:
            return jsonify({
                'error': 'Loss tracking system not initialized'
            }), 500
        
        # Get current state
        current_state = loss_tracking.get_current_state()
        if not current_state:
            # Return default state if no current state exists
            return jsonify({
                'timestamp': datetime.now().isoformat(),
                'total_losses': 0.0,
                'mechanical_losses': 0.0,
                'electrical_losses': 0.0,
                'thermal_losses': 0.0,
                'overall_efficiency': 1.0,
                'cumulative_energy_loss': 0.0,
                'average_efficiency': 1.0,
                'status': 'no_data'
            })
        
        system_losses = current_state.system_losses
        
        return jsonify({
            'timestamp': current_state.timestamp.isoformat(),
            'total_losses': system_losses.total_losses,
            'mechanical_losses': system_losses.mechanical_losses,
            'electrical_losses': system_losses.electrical_losses,
            'thermal_losses': system_losses.thermal_losses,
            'overall_efficiency': system_losses.overall_efficiency,
            'cumulative_energy_loss': current_state.cumulative_energy_loss,
            'average_efficiency': current_state.average_efficiency,
            'status': 'active'
        })
        
    except Exception as e:
        return jsonify({
            'error': f'Error getting current losses: {str(e)}'
        }), 500

@loss_monitoring_bp.route('/api/losses/history', methods=['GET'])
def get_loss_history():
    """Get loss history"""
    try:
        # Get loss tracking system
        loss_tracking = get_component_manager().get_loss_tracking_system()
        if not loss_tracking:
            return jsonify({
                'error': 'Loss tracking system not initialized'
            }), 500
        
        # Get optional limit parameter
        limit = request.args.get('limit', type=int)
        
        # Get history
        history = loss_tracking.get_history(limit=limit)
        
        # Convert to JSON-serializable format
        history_data = []
        for state in history:
            history_data.append({
                'timestamp': state.timestamp.isoformat(),
                'total_losses': state.system_losses.total_losses,
                'mechanical_losses': state.system_losses.mechanical_losses,
                'electrical_losses': state.system_losses.electrical_losses,
                'thermal_losses': state.system_losses.thermal_losses,
                'overall_efficiency': state.system_losses.overall_efficiency,
                'cumulative_energy_loss': state.cumulative_energy_loss,
                'average_efficiency': state.average_efficiency
            })
        
        return jsonify(history_data)
        
    except Exception as e:
        return jsonify({
            'error': f'Error getting loss history: {str(e)}'
        }), 500

@loss_monitoring_bp.route('/api/losses/performance', methods=['GET'])
def get_performance_metrics():
    """Get loss-related performance metrics"""
    try:
        # Get loss tracking system
        loss_tracking = get_component_manager().get_loss_tracking_system()
        if not loss_tracking:
            return jsonify({
                'error': 'Loss tracking system not initialized'
            }), 500
        
        # Get performance metrics
        metrics = loss_tracking.get_performance_metrics()
        
        return jsonify(metrics)
        
    except Exception as e:
        return jsonify({
            'error': f'Error getting performance metrics: {str(e)}'
        }), 500

@loss_monitoring_bp.route('/api/losses/optimization', methods=['GET'])
def get_optimization_suggestions():
    """Get loss optimization suggestions"""
    try:
        # Get loss tracking system
        loss_tracking = get_component_manager().get_loss_tracking_system()
        if not loss_tracking:
            return jsonify({
                'error': 'Loss tracking system not initialized'
            }), 500
        
        # Get optimization suggestions
        suggestions = loss_tracking.get_optimization_suggestions()
        
        return jsonify(suggestions)
        
    except Exception as e:
        return jsonify({
            'error': f'Error getting optimization suggestions: {str(e)}'
        }), 500

@loss_monitoring_bp.route('/api/losses/component/<component_id>', methods=['GET'])
def get_component_losses(component_id: str):
    """Get losses for a specific component"""
    try:
        # Get loss tracking system
        loss_tracking = get_component_manager().get_loss_tracking_system()
        if not loss_tracking:
            return jsonify({
                'error': 'Loss tracking system not initialized'
            }), 500
        
        # Get current state
        current_state = loss_tracking.get_current_state()
        if not current_state:
            # Return default component state if no current state exists
            default_component_state = {
                'mechanical': {
                    'power_loss': 0.0,
                    'energy_loss': 0.0,
                    'efficiency': 1.0,
                    'temperature_rise': 0.0,
                    'wear_rate': 0.0
                },
                'electrical': {
                    'power_loss': 0.0,
                    'energy_loss': 0.0,
                    'efficiency': 1.0,
                    'temperature_rise': 0.0,
                    'wear_rate': 0.0
                },
                'thermal': {
                    'power_loss': 0.0,
                    'energy_loss': 0.0,
                    'efficiency': 1.0,
                    'temperature_rise': 0.0,
                    'wear_rate': 0.0
                }
            }
            return jsonify(default_component_state)
        
        # Get component losses
        component_losses = current_state.component_losses.get(component_id)
        if not component_losses:
            return jsonify({
                'error': f'No loss data found for component: {component_id}'
            }), 404
        
        # Convert loss results to JSON-serializable format
        loss_data = {}
        for loss_type, loss_result in component_losses.items():
            loss_data[loss_type] = {
                'power_loss': loss_result.power_loss,
                'energy_loss': loss_result.energy_loss,
                'efficiency': loss_result.efficiency,
                'temperature_rise': loss_result.temperature_rise,
                'wear_rate': loss_result.wear_rate
            }
        
        return jsonify(loss_data)
        
    except Exception as e:
        return jsonify({
            'error': f'Error getting component losses: {str(e)}'
        }), 500 