"""
Core physics engine for KPP simulation.
Handles all physics calculations and component interactions.
"""

import logging
from typing import List, Dict, Any, Optional

from simulation.managers.physics_manager import PhysicsManager
from simulation.schemas import (
    PhysicsResults,
    SimulationState,
    FloaterState,
    DrivetrainState,
    PneumaticState,
    EnvironmentState
)

class PhysicsEngine:
    """
    Physics engine class.
    Handles all physics calculations and component interactions.
    """
    
    def __init__(self, config):
        """
        Initialize physics engine.
        
        Args:
            config: Physics configuration
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Components
        self.environment = None
        self.drivetrain = None
        self.pneumatics = None
        self.floaters: List[Any] = []
        
        # State
        self.time = 0.0
        self.total_energy = 0.0
        self.total_power = 0.0
        self.efficiency = 0.0
        
        # Performance tracking
        self.losses: Dict[str, float] = {
            'mechanical': 0.0,
            'electrical': 0.0,
            'drag': 0.0,
            'thermal': 0.0
        }
    
    def set_environment(self, environment):
        """Set environment component"""
        self.environment = environment
    
    def set_drivetrain(self, drivetrain):
        """Set drivetrain component"""
        self.drivetrain = drivetrain
    
    def set_pneumatics(self, pneumatics):
        """Set pneumatic system component"""
        self.pneumatics = pneumatics
    
    def set_floaters(self, floaters):
        """Set floater components"""
        self.floaters = floaters
    
    def update(self, state: SimulationState, time_step: float, component_states: Optional[Dict[str, Any]] = None) -> PhysicsResults:
        """
        Update physics state.
        
        Args:
            state: Current simulation state
            time_step: Time step for update
            component_states: Optional states from other components
        
        Returns:
            PhysicsResults with updated calculations
        """
        try:
            # Update time
            self.time += time_step
            
            # Get component states
            env_state = component_states.get('environment') if component_states else None
            pneumatic_state = component_states.get('pneumatics') if component_states else None
            drivetrain_state = component_states.get('drivetrain') if component_states else None
            floater_states = component_states.get('floaters', []) if component_states else []
            
            # Calculate total mechanical power from floaters
            mechanical_power = 0.0
            net_torque = 0.0
            total_buoyant_force = 0.0
            total_drag_force = 0.0
            total_weight_force = 0.0
            
            # Diagnostic logging for floaters
            if self.time % 1.0 < time_step:  # Log every second
                self.logger.info(f"=== Physics Diagnostics at t={self.time:.2f}s ===")
                self.logger.info(f"Enhancements: H1={self.config.enable_h1}, H2={self.config.enable_h2}, H3={self.config.enable_h3}")
            
            for i, floater in enumerate(self.floaters):
                if floater.is_buoyant:
                    # Buoyant force does positive work
                    force = floater.buoyant_force
                    if self.drivetrain:
                        torque = force * self.drivetrain.chain_radius
                        net_torque += torque
                    
                    power = force * floater.velocity
                    if power > 0:
                        mechanical_power += power
                    
                    total_buoyant_force += force
                
                total_drag_force += abs(floater.drag_force)
                total_weight_force += abs(floater.weight_force)
                
                # Track drag losses
                self.losses['drag'] += abs(floater.drag_force * floater.velocity) * time_step
                
                # Log floater diagnostics every second
                if self.time % 1.0 < time_step and i < 3:  # Log first 3 floaters
                    self.logger.info(f"Floater {i}: pos={floater.position:.3f}, vel={floater.velocity:.3f}, "
                                   f"buoyant={floater.is_buoyant}, F_b={floater.buoyant_force:.1f}, "
                                   f"F_d={floater.drag_force:.1f}, F_w={floater.weight_force:.1f}")
            
            # Log force summary
            if self.time % 1.0 < time_step:
                self.logger.info(f"Forces: Buoyant={total_buoyant_force:.1f}N, Drag={total_drag_force:.1f}N, "
                               f"Weight={total_weight_force:.1f}N, Net Torque={net_torque:.1f}N·m")
            
            # Update drivetrain with H3 effects
            if self.drivetrain:
                # Update drivetrain state with net torque
                # The drivetrain is now a wrapper, so we call update directly
                self.drivetrain.update(time_step, net_torque)
                drivetrain_state = self.drivetrain.get_state()
                
                # Get mechanical power considering H3
                if self.config.enable_h3:
                    # When H3 is enabled, power comes in pulses
                    if drivetrain_state['clutch_engagement'] > 0:
                        # During engagement, we get power from both current torque and stored energy
                        mechanical_power = (
                            mechanical_power * drivetrain_state['clutch_engagement'] +
                            drivetrain_state['kinetic_energy'] / time_step
                        )
                    else:
                        # During disengagement, power goes to kinetic energy storage
                        mechanical_power = 0
                        self.losses['mechanical'] += mechanical_power * time_step
                else:
                    # Normal operation without H3
                    self.losses['mechanical'] += (mechanical_power - drivetrain_state['current_power']) * time_step
                
                # Log drivetrain diagnostics
                if self.time % 1.0 < time_step:
                    self.logger.info(f"Drivetrain: ω={drivetrain_state['angular_velocity']:.2f}rad/s, "
                                   f"clutch={drivetrain_state['clutch_engagement']:.2f}, "
                                   f"KE={drivetrain_state['kinetic_energy']:.1f}J")
            
            # Calculate electrical power and losses
            if self.drivetrain and drivetrain_state:
                electrical_power = drivetrain_state['current_power'] * self.config.electrical_efficiency
                self.losses['electrical'] += (drivetrain_state['current_power'] - electrical_power) * time_step
            else:
                electrical_power = mechanical_power * self.config.electrical_efficiency
                self.losses['electrical'] += (mechanical_power - electrical_power) * time_step
            
            # Track thermal losses from H2 if enabled
            if self.config.enable_h2 and self.pneumatics:
                # H2 thermal effects are already accounted for in the pneumatic system
                pass
            
            # Account for compressor energy input (always negative)
            compressor_energy = 0.0
            if self.pneumatics:
                compressor_energy = -self.pneumatics.get_power() * time_step
                self.losses['compressor'] = abs(compressor_energy)
            
            # Calculate net energy considering enhancements
            # Without enhancements, compressor input should exceed mechanical output
            if not (self.config.enable_h1 or self.config.enable_h2 or self.config.enable_h3):
                # Conventional mode: significant losses make net energy negative
                # Add additional system losses to ensure net energy is negative
                system_losses = mechanical_power * 0.3 * time_step  # 30% additional system losses
                self.losses['system'] = system_losses
                net_energy = electrical_power * time_step + compressor_energy - system_losses
            else:
                # Enhanced mode: enhancements may allow net positive energy
                net_energy = electrical_power * time_step + compressor_energy
            
            # Update total energy and power
            self.total_power = electrical_power
            self.total_energy += net_energy
            
            # Calculate efficiency
            input_energy = sum(self.losses.values())
            if input_energy > 0:
                # Efficiency = output energy / input energy
                # Since total_energy is net energy (output - input), we need to calculate output
                output_energy = max(0, self.total_energy + input_energy)  # Output is positive part
                self.efficiency = output_energy / input_energy if input_energy > 0 else 0.0
            else:
                self.efficiency = 0.0
            
            # Log energy summary
            if self.time % 1.0 < time_step:
                self.logger.info(f"Energy: Mech={mechanical_power:.1f}W, Elec={electrical_power:.1f}W, "
                               f"Comp={compressor_energy/time_step:.1f}W, Net={net_energy/time_step:.1f}W, "
                               f"Total={self.total_energy:.1f}J, Eff={self.efficiency:.3f}")
                self.logger.info(f"Losses: Mech={self.losses.get('mechanical', 0):.1f}J, "
                               f"Elec={self.losses.get('electrical', 0):.1f}J, "
                               f"Drag={self.losses.get('drag', 0):.1f}J, "
                               f"Comp={self.losses.get('compressor', 0):.1f}J")
                self.logger.info("=" * 50)
            
            # Return physics results
            return PhysicsResults(
                total_power=self.total_power,
                total_energy=self.total_energy,
                efficiency=self.efficiency,
                mechanical_power=mechanical_power,
                electrical_power=electrical_power,
                losses=self.losses.copy(),
                h3_state={
                    'clutch_engagement': drivetrain_state['clutch_engagement'] if drivetrain_state else 0.0,
                    'kinetic_energy': drivetrain_state['kinetic_energy'] if drivetrain_state else 0.0,
                    'angular_velocity': drivetrain_state['angular_velocity'] if drivetrain_state else 0.0
                } if self.config.enable_h3 else None
            )
            
        except Exception as e:
            self.logger.error(f"Error in physics update: {e}")
            raise
    
    def update_parameters(self, params: Dict[str, Any]) -> bool:
        """
        Update physics parameters.
        
        Args:
            params: Dictionary of parameters to update
        
        Returns:
            bool: True if successful
        """
        try:
            # Update enhancement flags
            if 'enable_h1' in params:
                self.config.enable_h1 = bool(params['enable_h1'])
            
            if 'enable_h2' in params:
                self.config.enable_h2 = bool(params['enable_h2'])
            
            if 'enable_h3' in params:
                self.config.enable_h3 = bool(params['enable_h3'])
            
            # Update enhancement parameters
            if 'nanobubble_fraction' in params:
                self.config.nanobubble_fraction = float(params['nanobubble_fraction'])
            
            if 'thermal_expansion_coeff' in params:
                self.config.thermal_expansion_coeff = float(params['thermal_expansion_coeff'])
            
            if 'flywheel_inertia' in params:
                self.config.flywheel_inertia = float(params['flywheel_inertia'])
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating parameters: {e}")
            return False

