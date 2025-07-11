"""
Enhanced force calculations for KPP simulation.
Includes:
- Advanced buoyancy with partial submersion
- Reynolds number dependent drag
- Wake effects
- Added mass effects
- Surface tension
"""

import numpy as np
from typing import Dict, Tuple, Optional
import logging

logger = logging.getLogger(__name__)

def compute_hydrostatic_pressure(depth: float, 
                               water_density: float,
                               gravity: float) -> float:
    """
    Compute hydrostatic pressure at given depth.
    
    Args:
        depth: Depth below surface (m)
        water_density: Water density (kg/m³)
        gravity: Gravitational acceleration (m/s²)
        
    Returns:
        Pressure in Pascals
    """
    return water_density * gravity * depth + 101325.0  # Add atmospheric pressure

def compute_submersion_factor(position: np.ndarray,
                            dimensions: np.ndarray,
                            water_level: float) -> float:
    """
    Calculate fraction of floater submerged in water.
    
    Args:
        position: Center position [x,y,z]
        dimensions: Floater dimensions [L,W,H]
        water_level: Water surface height
        
    Returns:
        Fraction submerged (0-1)
    """
    height = dimensions[2]
    bottom = position[2] - height/2
    top = position[2] + height/2
    
    if top <= water_level:
        return 1.0  # Fully submerged
    elif bottom >= water_level:
        return 0.0  # Fully out
    else:
        # Partial submersion
        submerged_height = water_level - bottom
        return min(1.0, max(0.0, submerged_height / height))

def compute_reynolds_number(velocity: float,
                          characteristic_length: float,
                          fluid_density: float,
                          fluid_viscosity: float) -> float:
    """
    Calculate Reynolds number for flow regime determination.
    
    Args:
        velocity: Flow velocity (m/s)
        characteristic_length: Characteristic dimension (m)
        fluid_density: Fluid density (kg/m³)
        fluid_viscosity: Dynamic viscosity (Pa·s)
        
    Returns:
        Reynolds number (dimensionless)
    """
    return (fluid_density * abs(velocity) * characteristic_length / 
            fluid_viscosity)

def get_drag_coefficient(reynolds: float, shape: str = 'rectangular') -> float:
    """
    Get drag coefficient based on Reynolds number and shape.
    
    Args:
        reynolds: Reynolds number
        shape: Shape descriptor ('rectangular', 'cylindrical', etc.)
        
    Returns:
        Drag coefficient Cd
    """
    # Base coefficients for different shapes
    base_coefficients = {
        'rectangular': 1.05,
        'cylindrical': 0.47,
        'streamlined': 0.04
    }
    
    base_cd = base_coefficients.get(shape, 1.0)
    
    if reynolds < 1:
        return base_cd * 24/reynolds  # Stokes flow
    elif reynolds < 1000:
        return base_cd * (1 + 0.15 * reynolds**0.687)  # Transitional
    else:
        return base_cd  # Fully turbulent

def compute_enhanced_buoyancy(volume: float,
                            water_density: float,
                            gravity: float,
                            submersion: float,
                            pressure: float,
                            temperature: float,
                            reference_temperature: float = 293.15,
                            enable_thermal: bool = False) -> float:
    """
    Compute enhanced buoyant force with thermal effects.
    
    Args:
        volume: Floater volume (m³)
        water_density: Water density (kg/m³)
        gravity: Gravitational acceleration (m/s²)
        submersion: Fraction submerged (0-1)
        pressure: Local pressure (Pa)
        temperature: Current temperature (K)
        reference_temperature: Reference temperature (K)
        enable_thermal: Whether to include thermal expansion
        
    Returns:
        Buoyant force magnitude (N)
    """
    # Base buoyant force
    force = water_density * volume * gravity * submersion
    
    if enable_thermal:
        # Thermal expansion factor (simplified ideal gas)
        thermal_factor = temperature / reference_temperature
        # Pressure compression factor (isothermal assumption)
        pressure_factor = 101325.0 / pressure
        # Combined effect on volume
        volume_factor = thermal_factor * pressure_factor
        force *= volume_factor
    
    return force

def compute_enhanced_drag(velocity: np.ndarray,
                         dimensions: np.ndarray,
                         water_density: float,
                         viscosity: float,
                         shape: str = 'rectangular',
                         wake_reduction: float = 0.0) -> np.ndarray:
    """
    Compute enhanced drag force with wake effects.
    
    Args:
        velocity: Velocity vector (m/s)
        dimensions: Floater dimensions [L,W,H] (m)
        water_density: Water density (kg/m³)
        viscosity: Dynamic viscosity (Pa·s)
        shape: Shape descriptor
        wake_reduction: Wake reduction factor (0-1)
        
    Returns:
        Drag force vector (N)
    """
    speed = np.linalg.norm(velocity)
    if speed < 1e-6:
        return np.zeros(3)
    
    # Calculate Reynolds number
    characteristic_length = dimensions[0]  # Use length
    reynolds = compute_reynolds_number(float(speed), characteristic_length,
                                     water_density, viscosity)
    
    # Get drag coefficient
    cd = get_drag_coefficient(reynolds, shape)
    
    # Calculate reference area (projected area in flow direction)
    # This is simplified; could be enhanced with proper 3D orientation
    reference_area = dimensions[0] * dimensions[1]
    
    # Apply wake reduction if specified
    effective_density = water_density * (1.0 - wake_reduction)
    
    # Calculate drag force magnitude
    force_magnitude = 0.5 * cd * effective_density * reference_area * speed**2
    
    # Convert to vector (opposite to velocity direction)
    return -force_magnitude * (velocity / speed)

def compute_added_mass_force(acceleration: np.ndarray,
                           volume: float,
                           water_density: float,
                           shape: str = 'rectangular') -> np.ndarray:
    """
    Compute added mass force (virtual mass effect).
    
    Args:
        acceleration: Acceleration vector (m/s²)
        volume: Floater volume (m³)
        water_density: Water density (kg/m³)
        shape: Shape descriptor
        
    Returns:
        Added mass force vector (N)
    """
    # Added mass coefficients for different shapes
    added_mass_coefficients = {
        'rectangular': 1.0,
        'cylindrical': 0.5,
        'streamlined': 0.1
    }
    
    Ca = added_mass_coefficients.get(shape, 1.0)
    
    # Added mass = Ca * ρ * V
    added_mass = Ca * water_density * volume
    
    # F = ma
    return -added_mass * acceleration

def compute_surface_tension(perimeter: float,
                          surface_tension_coeff: float = 0.072,  # N/m for water
                          contact_angle: float = np.pi/2) -> float:
    """
    Compute surface tension force at water interface.
    
    Args:
        perimeter: Wetted perimeter (m)
        surface_tension_coeff: Surface tension coefficient (N/m)
        contact_angle: Contact angle (radians)
        
    Returns:
        Surface tension force magnitude (N)
    """
    return perimeter * surface_tension_coeff * np.cos(contact_angle)

def compute_all_forces(floater_state: Dict,
                      environment: Dict) -> Dict[str, np.ndarray]:
    """
    Compute all forces acting on a floater.
    
    Args:
        floater_state: Dictionary containing floater state
        environment: Dictionary containing environmental conditions
        
    Returns:
        Dictionary of force vectors by type
    """
    try:
        forces = {}
        
        # Extract parameters
        position = floater_state['position']
        velocity = floater_state['velocity']
        acceleration = floater_state.get('acceleration', np.zeros(3))
        dimensions = floater_state['dimensions']
        volume = floater_state['volume']
        
        # Compute submersion
        submersion = compute_submersion_factor(
            position, dimensions, environment['water_level'])
        
        # Compute local pressure
        depth = max(0, environment['water_level'] - position[2])
        pressure = compute_hydrostatic_pressure(
            depth, environment['water_density'], environment['gravity'])
        
        # Buoyant force
        forces['buoyancy'] = np.array([0, 0, compute_enhanced_buoyancy(
            volume=volume,
            water_density=environment['water_density'],
            gravity=environment['gravity'],
            submersion=submersion,
            pressure=pressure,
            temperature=floater_state.get('temperature', 293.15),
            enable_thermal=environment.get('H2_active', False)
        )])
        
        # Drag force
        forces['drag'] = compute_enhanced_drag(
            velocity=velocity,
            dimensions=dimensions,
            water_density=environment['water_density'],
            viscosity=environment['viscosity'],
            wake_reduction=environment.get('wake_reduction', 0.0)
        )
        
        # Added mass force
        forces['added_mass'] = compute_added_mass_force(
            acceleration=acceleration,
            volume=volume,
            water_density=environment['water_density']
        )
        
        # Surface tension (only if partially submerged)
        if 0 < submersion < 1:
            # Approximate wetted perimeter
            perimeter = 2 * (dimensions[0] + dimensions[1])
            st_force = compute_surface_tension(perimeter)
            forces['surface_tension'] = np.array([0, 0, st_force])
        
        return forces
        
    except Exception as e:
        logger.error(f"Force computation failed: {e}")
        return {'error': np.zeros(3)} 