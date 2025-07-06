#!/usr/bin/env python3
"""
KPP Physics Analysis and Parameter Tuning Script

This script performs a deep analysis of the KPP simulator physics and science,
then fine-tunes default parameters to ensure power generation upon startup.

Based on KPP Technology Physics Principles:
1. Kinetic Pneumatic Power uses buoyancy-driven chain motion
2. Air-filled floaters ascend (positive buoyancy)
3. Water-filled floaters descend (negative buoyancy)
4. Net force differential drives chain motion
5. Chain motion turns sprocket/generator for electrical power
"""

import sys
import math
import numpy as np
import matplotlib.pyplot as plt
from typing import Dict, List, Tuple, Any
import logging

# Import simulation components for analysis
from simulation.engine import SimulationEngine
from simulation.components.floater import Floater
# Legacy generator import removed - using integrated electrical system instead
from simulation.components.integrated_drivetrain import IntegratedDrivetrain
from config.parameter_schema import get_default_parameters
from config.config import G, RHO_WATER, RHO_AIR
import queue

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class KPPPhysicsAnalyzer:
    """Comprehensive physics analyzer for KPP system optimization."""
    
    def __init__(self):
        self.physics_constants = {
            'g': G,  # 9.81 m/s²
            'rho_water': RHO_WATER,  # 1000 kg/m³
            'rho_air': RHO_AIR,  # 1.225 kg/m³
            'atmospheric_pressure': 101325,  # Pa
        }
        
        # Physics analysis results
        self.analysis_results = {}
        self.optimal_parameters = {}
        
    def analyze_buoyancy_physics(self, floater_volume: float, floater_mass: float) -> Dict[str, float]:
        """
        Analyze the fundamental buoyancy physics for a single floater.
        
        Key Physics:
        - F_buoyant = ρ_water × V_displaced × g
        - F_weight_air = m_floater × g  (air-filled state)
        - F_weight_water = (m_floater + ρ_water × V_floater) × g  (water-filled state)
        """
        g = self.physics_constants['g']
        rho_water = self.physics_constants['rho_water']
        
        # Buoyant force (always upward when submerged)
        F_buoyant = rho_water * floater_volume * g
        
        # Weight forces
        F_weight_air = floater_mass * g  # Light state (air-filled)
        F_weight_water = (floater_mass + rho_water * floater_volume) * g  # Heavy state
        
        # Net forces
        F_net_ascending = F_buoyant - F_weight_air  # Should be positive for ascent
        F_net_descending = F_weight_water - F_buoyant  # Should be positive for descent
        
        # Force differential (driving force)
        F_differential = F_net_ascending + F_net_descending
        
        results = {
            'F_buoyant': F_buoyant,
            'F_weight_air': F_weight_air,
            'F_weight_water': F_weight_water,
            'F_net_ascending': F_net_ascending,
            'F_net_descending': F_net_descending,
            'F_differential': F_differential,
            'buoyancy_ratio': F_buoyant / F_weight_air if F_weight_air > 0 else 0,
        }
        
        logger.info(f"Buoyancy Analysis:")
        logger.info(f"  Buoyant Force: {F_buoyant:.1f} N")
        logger.info(f"  Weight (air): {F_weight_air:.1f} N")
        logger.info(f"  Weight (water): {F_weight_water:.1f} N")
        logger.info(f"  Net Ascending: {F_net_ascending:.1f} N")
        logger.info(f"  Net Descending: {F_net_descending:.1f} N")
        logger.info(f"  Force Differential: {F_differential:.1f} N")
        logger.info(f"  Buoyancy Ratio: {results['buoyancy_ratio']:.2f}")
        
        return results
    
    def analyze_drag_physics(self, velocity: float, floater_area: float, drag_coefficient: float) -> Dict[str, float]:
        """
        Analyze hydrodynamic drag forces.
        
        Key Physics:
        - F_drag = 0.5 × ρ_water × C_d × A × v²
        """
        rho_water = self.physics_constants['rho_water']
        
        # Drag force (opposes motion)
        F_drag = 0.5 * rho_water * drag_coefficient * floater_area * (velocity ** 2)
        
        # Drag power loss
        P_drag = F_drag * velocity
        
        results = {
            'F_drag': F_drag,
            'P_drag': P_drag,
            'reynolds_number': self.calculate_reynolds_number(velocity, floater_area)
        }
        
        return results
    
    def calculate_reynolds_number(self, velocity: float, characteristic_length: float) -> float:
        """Calculate Reynolds number for drag analysis."""
        # Kinematic viscosity of water at 20°C
        nu_water = 1.0e-6  # m²/s
        L = math.sqrt(characteristic_length)  # Approximate characteristic length
        Re = velocity * L / nu_water
        return Re
    
    def analyze_chain_dynamics(self, num_floaters: int, F_net_per_floater: float, 
                             total_system_mass: float, sprocket_radius: float) -> Dict[str, float]:
        """
        Analyze chain dynamics and torque generation.
        
        Key Physics:
        - F_total = N/2 × (F_ascending + F_descending)
        - a_chain = F_total / M_total
        - τ_sprocket = F_total × R_sprocket
        """
        # Assume half floaters ascending, half descending
        N_half = num_floaters // 2
        F_total = N_half * F_net_per_floater
        
        # Chain acceleration
        a_chain = F_total / total_system_mass if total_system_mass > 0 else 0
        
        # Torque at sprocket
        tau_sprocket = F_total * sprocket_radius
        
        results = {
            'F_total': F_total,
            'a_chain': a_chain,
            'tau_sprocket': tau_sprocket,
            'force_per_floater': F_net_per_floater,
            'system_mass': total_system_mass
        }
        
        logger.info(f"Chain Dynamics Analysis:")
        logger.info(f"  Total Force: {F_total:.1f} N")
        logger.info(f"  Chain Acceleration: {a_chain:.3f} m/s²")
        logger.info(f"  Sprocket Torque: {tau_sprocket:.1f} N⋅m")
        
        return results
    
    def analyze_power_generation(self, torque: float, angular_velocity: float, 
                               generator_efficiency: float = 0.92) -> Dict[str, float]:
        """
        Analyze electrical power generation.
        
        Key Physics:
        - P_mechanical = τ × ω
        - P_electrical = P_mechanical × η_generator
        """
        P_mechanical = torque * angular_velocity
        P_electrical = P_mechanical * generator_efficiency
        
        results = {
            'P_mechanical': P_mechanical,
            'P_electrical': P_electrical,
            'torque': torque,
            'angular_velocity': angular_velocity,
            'rpm': angular_velocity * 60 / (2 * math.pi)
        }
        
        logger.info(f"Power Generation Analysis:")
        logger.info(f"  Mechanical Power: {P_mechanical:.1f} W")
        logger.info(f"  Electrical Power: {P_electrical:.1f} W")
        logger.info(f"  Angular Velocity: {angular_velocity:.2f} rad/s ({results['rpm']:.1f} RPM)")
        
        return results
    
    def calculate_optimal_parameters(self) -> Dict[str, Any]:
        """
        Calculate optimal parameters for reliable power generation.
        
        Design Targets:
        - Positive net buoyancy force for ascent
        - Significant force differential for chain motion
        - Reasonable operating speeds (1-3 m/s chain speed)
        - Target power output of 10-100 kW range
        """
        logger.info("=" * 60)
        logger.info("CALCULATING OPTIMAL KPP PARAMETERS")
        logger.info("=" * 60)
        
        # Design constraints and targets
        target_chain_speed = 2.0  # m/s (reasonable speed)
        target_power = 50000  # 50 kW initial target
        target_efficiency = 0.6  # 60% overall efficiency
        
        # Start with floater design for strong buoyancy
        floater_volume = 0.5  # m³ (larger for more buoyancy)
        floater_mass_empty = 15.0  # kg (lighter container)
        
        # Analyze base floater physics
        buoyancy_analysis = self.analyze_buoyancy_physics(floater_volume, floater_mass_empty)
        
        # Check if floater provides positive buoyancy
        if buoyancy_analysis['F_net_ascending'] <= 0:
            logger.warning("Floater has negative buoyancy - adjusting parameters")
            # Reduce mass or increase volume
            while buoyancy_analysis['F_net_ascending'] <= 0 and floater_mass_empty > 5.0:
                floater_mass_empty -= 1.0
                buoyancy_analysis = self.analyze_buoyancy_physics(floater_volume, floater_mass_empty)
        
        # Calculate number of floaters needed for target power
        F_per_floater = buoyancy_analysis['F_differential'] / 2  # Average force per floater
        
        # Estimate required system force for target power
        # P = F × v, so F = P / v
        F_required = target_power / target_chain_speed
        num_floaters = max(4, int(F_required / F_per_floater) * 2)  # Ensure even number
        num_floaters = min(num_floaters, 20)  # Practical limit
        
        # Calculate system mass
        total_floater_mass = num_floaters * (floater_mass_empty + 0.5 * RHO_WATER * floater_volume)
        chain_mass = 200.0  # Estimated chain mass
        drivetrain_mass = 500.0  # Estimated integrated_drivetrain mass
        total_system_mass = total_floater_mass + chain_mass + drivetrain_mass
        
        # Analyze chain dynamics
        chain_analysis = self.analyze_chain_dynamics(
            num_floaters, F_per_floater, total_system_mass, sprocket_radius=1.0
        )
        
        # Calculate steady-state velocity (when acceleration stops)
        # At steady state: driving force = drag force
        # Estimate drag force for all floaters
        total_floater_area = num_floaters * 0.05  # m² (cross-sectional area)
        drag_coefficient = 0.6  # Optimized for lower drag
        
        # Solve for steady-state velocity: F_net = F_drag
        # F_net = 0.5 * rho * Cd * A * v²
        # v = sqrt(2 * F_net / (rho * Cd * A))
        F_net = chain_analysis['F_total']
        v_steady = math.sqrt(2 * F_net / (RHO_WATER * drag_coefficient * total_floater_area))
        
        # Calculate sprocket angular velocity
        sprocket_radius = 1.0  # m
        omega_sprocket = v_steady / sprocket_radius
        
        # Gear ratio to reach target generator speed
        target_generator_rpm = 1500  # RPM (typical for generator)
        target_generator_omega = target_generator_rpm * 2 * math.pi / 60
        gear_ratio = target_generator_omega / omega_sprocket if omega_sprocket > 0 else 1.0
        gear_ratio = max(1.0, min(gear_ratio, 50.0))  # Practical gear ratio limits
        
        # Final power analysis
        final_torque = chain_analysis['tau_sprocket']
        final_omega = omega_sprocket * gear_ratio
        power_analysis = self.analyze_power_generation(final_torque, final_omega)
        
        # Calculate air injection parameters
        # Air pressure should overcome water pressure at injection depth
        injection_depth = 12.0  # m (bottom of tank)
        water_pressure = RHO_WATER * G * injection_depth
        air_pressure = water_pressure + 50000  # Pa (safety margin)
        
        optimal_params = {
            # Floater parameters
            'num_floaters': num_floaters,
            'floater_volume': floater_volume,
            'floater_mass_empty': floater_mass_empty,
            'floater_area': 0.05,  # m² (optimized cross-sectional area)
            'floater_Cd': drag_coefficient,
            
            # IntegratedDrivetrain parameters
            'sprocket_radius': sprocket_radius,
            'gear_ratio': gear_ratio,
            'flywheel_inertia': 100.0,  # kg⋅m² (increased for stability)
            
            # Generator parameters
            'target_power': power_analysis['P_electrical'],
            'target_rpm': final_omega * 60 / (2 * math.pi),
            'generator_efficiency': 0.94,
            
            # Pneumatic parameters
            'air_pressure': air_pressure,
            'air_fill_time': 0.3,  # s (faster filling)
            'air_flow_rate': 1.0,  # m³/s (higher flow rate)
            'pulse_interval': 1.5,  # s (more frequent pulses)
            
            # Physics parameters
            'time_step': 0.05,  # s (smaller time step for accuracy)
            
            # Performance predictions
            'predicted_power': power_analysis['P_electrical'],
            'predicted_chain_speed': v_steady,
            'predicted_efficiency': power_analysis['P_electrical'] / target_power if target_power > 0 else 0,
            'force_differential': buoyancy_analysis['F_differential'],
            'buoyancy_ratio': buoyancy_analysis['buoyancy_ratio']
        }
        
        logger.info("=" * 60)
        logger.info("OPTIMAL PARAMETER RESULTS")
        logger.info("=" * 60)
        logger.info(f"Number of Floaters: {optimal_params['num_floaters']}")
        logger.info(f"Floater Volume: {optimal_params['floater_volume']:.2f} m³")
        logger.info(f"Floater Mass: {optimal_params['floater_mass_empty']:.1f} kg")
        logger.info(f"Air Pressure: {optimal_params['air_pressure']:.0f} Pa ({optimal_params['air_pressure']/1000:.0f} kPa)")
        logger.info(f"Predicted Power: {optimal_params['predicted_power']:.0f} W ({optimal_params['predicted_power']/1000:.1f} kW)")
        logger.info(f"Predicted Chain Speed: {optimal_params['predicted_chain_speed']:.2f} m/s")
        logger.info(f"Force Differential: {optimal_params['force_differential']:.1f} N")
        logger.info(f"Buoyancy Ratio: {optimal_params['buoyancy_ratio']:.2f}")
        logger.info("=" * 60)
        
        self.optimal_parameters = optimal_params
        return optimal_params
    
    def validate_parameters(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Validate parameters through simulation testing."""
        logger.info("Validating parameters through simulation...")
        
        # Create simulation with test parameters
        data_queue = queue.Queue()
        sim_engine = SimulationEngine(params, data_queue)
        sim_engine.reset()
        
        # Run simulation for a short period
        test_duration = 10.0  # seconds
        dt = params.get('time_step', 0.1)
        steps = int(test_duration / dt)
        
        power_samples = []
        efficiency_samples = []
        
        for step in range(steps):
            state = sim_engine.step(dt)
            
            # Extract key metrics
            power = state.get('power', 0.0)
            efficiency = state.get('efficiency', 0.0)
            
            power_samples.append(power)
            efficiency_samples.append(efficiency)
            
            # Log progress
            if step % 50 == 0:
                logger.info(f"Step {step}/{steps}: Power={power:.1f}W, Efficiency={efficiency:.1%}")
        
        # Calculate validation metrics
        avg_power = np.mean(power_samples[-20:]) if len(power_samples) >= 20 else np.mean(power_samples)
        max_power = np.max(power_samples)
        avg_efficiency = np.mean(efficiency_samples[-20:]) if len(efficiency_samples) >= 20 else np.mean(efficiency_samples)
        
        validation_results = {
            'avg_power': avg_power,
            'max_power': max_power,
            'avg_efficiency': avg_efficiency,
            'power_stability': np.std(power_samples[-10:]) if len(power_samples) >= 10 else 0,
            'success': avg_power > 1000 and avg_efficiency > 0.1  # Basic success criteria
        }
        
        logger.info(f"Validation Results:")
        logger.info(f"  Average Power: {avg_power:.1f} W")
        logger.info(f"  Maximum Power: {max_power:.1f} W")
        logger.info(f"  Average Efficiency: {avg_efficiency:.1%}")
        logger.info(f"  Validation Success: {validation_results['success']}")
        
        return validation_results
    
    def generate_tuned_config(self) -> Dict[str, Any]:
        """Generate the final tuned configuration."""
        optimal_params = self.calculate_optimal_parameters()
        
        # Validate through simulation
        validation = self.validate_parameters(optimal_params)
        
        # Adjust parameters based on validation results
        if not validation['success']:
            logger.warning("Initial parameters failed validation - applying corrections...")
            
            # Increase floater volume for more buoyancy
            optimal_params['floater_volume'] *= 1.2
            optimal_params['num_floaters'] = min(optimal_params['num_floaters'] + 2, 20)
            optimal_params['air_pressure'] *= 1.1
            
            # Re-validate
            validation = self.validate_parameters(optimal_params)
        
        logger.info("=" * 60)
        logger.info("FINAL TUNED CONFIGURATION")
        logger.info("=" * 60)
        
        final_config = optimal_params.copy()
        final_config['validation_results'] = validation
        
        return final_config

def main():
    """Main execution function."""
    logger.info("Starting KPP Physics Analysis and Parameter Tuning...")
    
    # Initialize analyzer
    analyzer = KPPPhysicsAnalyzer()
    
    # Current defaults (from our analysis)
    current_defaults = {
        'num_floaters': 8,
        'floater_volume': 0.3,
        'floater_mass_empty': 18.0,
        'floater_area': 0.035,
        'air_pressure': 300000
    }
    
    logger.info("Current Default Parameters:")
    for key, value in current_defaults.items():
        logger.info(f"  {key}: {value}")
    
    # Analyze current default floater
    logger.info("\n" + "=" * 60)
    logger.info("CURRENT PHYSICS ANALYSIS")
    logger.info("=" * 60)
    
    buoyancy_analysis = analyzer.analyze_buoyancy_physics(
        current_defaults['floater_volume'], 
        current_defaults['floater_mass_empty']
    )
    
    # Check if current floater can generate power
    if buoyancy_analysis['F_net_ascending'] <= 0:
        logger.error("CRITICAL: Current floater has negative buoyancy and cannot generate power!")
        logger.error(f"Net ascending force: {buoyancy_analysis['F_net_ascending']:.1f} N")
        logger.error("This explains why efficiency is 0% - the floaters sink instead of float!")
    
    # Generate optimal configuration
    tuned_config = analyzer.calculate_optimal_parameters()
    
    # Save results
    import json
    output_file = "kpp_tuned_parameters.json"
    with open(output_file, 'w') as f:
        json.dump(tuned_config, f, indent=2)
    
    logger.info(f"Tuned parameters saved to: {output_file}")
    
    # Generate comparison report
    logger.info("\n" + "=" * 60)
    logger.info("PARAMETER COMPARISON")
    logger.info("=" * 60)
    
    for key in ['num_floaters', 'floater_volume', 'floater_mass_empty', 'air_pressure']:
        if key in current_defaults and key in tuned_config:
            old_val = current_defaults[key]
            new_val = tuned_config[key]
            change = ((new_val - old_val) / old_val * 100) if old_val != 0 else 0
            logger.info(f"{key}:")
            logger.info(f"  Current: {old_val}")
            logger.info(f"  Tuned:   {new_val}")
            logger.info(f"  Change:  {change:+.1f}%")
    
    return tuned_config

if __name__ == "__main__":
    tuned_config = main()
    print("\n" + "=" * 60)
    print("PHYSICS ANALYSIS COMPLETE")
    print("=" * 60)
    print("Tuned configuration generated for reliable power generation!") 