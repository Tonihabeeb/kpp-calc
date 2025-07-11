"""
Floater interaction physics for KPP simulation.
Handles:
- Collision detection and response
- Wake effects between floaters
- Chain spacing constraints
- Fluid interaction effects
"""

import numpy as np
from typing import List, Dict, Tuple, Optional
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class CollisionData:
    """Data for collision response"""
    point: np.ndarray  # Contact point
    normal: np.ndarray  # Contact normal
    depth: float  # Penetration depth
    relative_velocity: np.ndarray  # Relative velocity at contact

def check_aabb_collision(pos1: np.ndarray,
                        dim1: np.ndarray,
                        pos2: np.ndarray,
                        dim2: np.ndarray) -> bool:
    """
    Check Axis-Aligned Bounding Box (AABB) collision.
    
    Args:
        pos1, pos2: Center positions [x,y,z]
        dim1, dim2: Dimensions [L,W,H]
        
    Returns:
        True if AABBs overlap
    """
    # Check overlap in each axis
    for axis in range(3):
        if (abs(pos1[axis] - pos2[axis]) > 
            (dim1[axis] + dim2[axis]) / 2):
            return False
    return True

def compute_collision_response(collision: CollisionData,
                             mass1: float,
                             mass2: float,
                             restitution: float = 0.5) -> Tuple[np.ndarray, np.ndarray]:
    """
    Compute collision impulse using impulse-based dynamics.
    
    Args:
        collision: Collision data
        mass1, mass2: Masses of colliding bodies
        restitution: Coefficient of restitution
        
    Returns:
        Tuple of impulse vectors for both bodies
    """
    # Compute relative normal velocity
    normal_vel = np.dot(collision.relative_velocity, collision.normal)
    
    if normal_vel > 0:
        return np.zeros(3), np.zeros(3)  # Bodies separating
    
    # Compute impulse magnitude
    j = -(1 + restitution) * normal_vel
    j /= (1/mass1 + 1/mass2)
    
    # Convert to impulse vectors
    impulse1 = j * collision.normal
    impulse2 = -impulse1
    
    return impulse1, impulse2

def detect_chain_constraint_violation(pos1: np.ndarray,
                                    pos2: np.ndarray,
                                    chain_spacing: float) -> Optional[np.ndarray]:
    """
    Check if chain spacing constraint is violated.
    
    Args:
        pos1, pos2: Positions of adjacent floaters
        chain_spacing: Required spacing
        
    Returns:
        Correction vector if constraint violated, None otherwise
    """
    delta = pos2 - pos1
    distance = np.linalg.norm(delta)
    
    if abs(distance - chain_spacing) > 0.01:  # Allow small tolerance
        # Compute correction to maintain spacing
        correction = (chain_spacing - distance) * delta/distance
        return correction
    return None

def compute_wake_effect(pos1: np.ndarray,
                       vel1: np.ndarray,
                       dim1: np.ndarray,
                       pos2: np.ndarray,
                       water_density: float) -> float:
    """
    Compute wake reduction factor for downstream floater.
    
    Args:
        pos1: Position of upstream floater
        vel1: Velocity of upstream floater
        dim1: Dimensions of upstream floater
        pos2: Position of potentially affected floater
        water_density: Water density
        
    Returns:
        Wake reduction factor (0-1) for drag calculation
    """
    speed = np.linalg.norm(vel1)
    if speed < 1e-6:
        return 0.0
    
    # Compute wake direction (normalized velocity)
    wake_dir = vel1 / speed
    
    # Vector from floater 1 to floater 2
    delta = pos2 - pos1
    distance = np.linalg.norm(delta)
    
    # Check if floater 2 is downstream (dot product with wake direction)
    alignment = np.dot(delta/distance, wake_dir)
    if alignment < 0:
        return 0.0  # Not in wake
    
    # Wake width grows with sqrt(distance)
    wake_width = dim1[0] + 0.2 * np.sqrt(distance)
    
    # Lateral distance from wake centerline
    lateral_offset = np.linalg.norm(delta - alignment*distance*wake_dir)
    
    if lateral_offset > wake_width:
        return 0.0  # Outside wake
    
    # Wake effect decreases with distance and lateral offset
    distance_factor = np.exp(-distance / (5.0 * dim1[0]))
    width_factor = (1.0 - (lateral_offset/wake_width)**2)
    
    # Maximum wake reduction (at high Reynolds numbers)
    max_reduction = 0.3  # Up to 30% drag reduction
    
    return max_reduction * distance_factor * width_factor

def apply_floater_interactions(floaters: List[Dict],
                             chain_spacing: float,
                             environment: Dict) -> List[Dict[str, np.ndarray]]:
    """
    Compute and apply all interaction effects between floaters.
    
    Args:
        floaters: List of floater state dictionaries
        chain_spacing: Required spacing between floaters
        environment: Environmental conditions
        
    Returns:
        List of interaction forces for each floater
    """
    n_floaters = len(floaters)
    interaction_forces = [{} for _ in range(n_floaters)]
    
    try:
        # Check all pairs of floaters
        for i in range(n_floaters):
            for j in range(i+1, n_floaters):
                fi = floaters[i]
                fj = floaters[j]
                
                # Skip if too far apart
                if np.linalg.norm(fi['position'] - fj['position']) > 3*chain_spacing:
                    continue
                
                # Check for collisions
                if check_aabb_collision(fi['position'], fi['dimensions'],
                                     fj['position'], fj['dimensions']):
                    # Compute collision data
                    delta = fj['position'] - fi['position']
                    normal = delta / np.linalg.norm(delta)
                    rel_vel = fj['velocity'] - fi['velocity']
                    
                    collision = CollisionData(
                        point=(fi['position'] + fj['position'])/2,
                        normal=normal,
                        depth=np.linalg.norm(delta),
                        relative_velocity=rel_vel
                    )
                    
                    # Compute collision response
                    impulse_i, impulse_j = compute_collision_response(
                        collision, fi['mass'], fj['mass'])
                    
                    # Add collision forces
                    if 'collision' not in interaction_forces[i]:
                        interaction_forces[i]['collision'] = impulse_i
                    else:
                        interaction_forces[i]['collision'] += impulse_i
                        
                    if 'collision' not in interaction_forces[j]:
                        interaction_forces[j]['collision'] = impulse_j
                    else:
                        interaction_forces[j]['collision'] += impulse_j
                
                # Check chain spacing constraints for adjacent floaters
                if j == (i + 1) % n_floaters:  # Circular chain
                    correction = detect_chain_constraint_violation(
                        fi['position'], fj['position'], chain_spacing)
                    
                    if correction is not None:
                        # Add constraint forces
                        if 'constraint' not in interaction_forces[i]:
                            interaction_forces[i]['constraint'] = -correction/2
                        else:
                            interaction_forces[i]['constraint'] -= correction/2
                            
                        if 'constraint' not in interaction_forces[j]:
                            interaction_forces[j]['constraint'] = correction/2
                        else:
                            interaction_forces[j]['constraint'] += correction/2
                
                # Compute wake effects
                # Check if j is affected by i's wake
                wake_factor_j = compute_wake_effect(
                    fi['position'], fi['velocity'], fi['dimensions'],
                    fj['position'], environment['water_density'])
                
                if wake_factor_j > 0:
                    interaction_forces[j]['wake_reduction'] = wake_factor_j
                
                # Check if i is affected by j's wake
                wake_factor_i = compute_wake_effect(
                    fj['position'], fj['velocity'], fj['dimensions'],
                    fi['position'], environment['water_density'])
                
                if wake_factor_i > 0:
                    interaction_forces[i]['wake_reduction'] = wake_factor_i
        
        return interaction_forces
        
    except Exception as e:
        logger.error(f"Floater interaction computation failed: {e}")
        return [{} for _ in range(n_floaters)]

def apply_fluid_interaction_effects(floater: Dict,
                                  nearby_floaters: List[Dict],
                                  environment: Dict) -> Dict[str, float]:
    """
    Compute fluid interaction effects (beyond simple wake).
    
    Args:
        floater: State of current floater
        nearby_floaters: States of nearby floaters
        environment: Environmental conditions
        
    Returns:
        Dictionary of interaction effects
    """
    effects = {}
    
    try:
        # Count floaters in local neighborhood
        local_density = 0
        for other in nearby_floaters:
            distance = np.linalg.norm(floater['position'] - other['position'])
            if distance < 2.0:  # Within 2m
                local_density += 1/(1 + distance)
        
        # Modify local fluid properties based on crowding
        if local_density > 1:
            # Increased effective viscosity due to disturbed flow
            effects['viscosity_factor'] = 1.0 + 0.1 * local_density
            
            # Reduced effective density due to aeration/mixing
            effects['density_factor'] = 1.0 - 0.05 * min(local_density, 3.0)
        
        # Check for channeling effects (floaters creating preferential flow paths)
        aligned_count = 0
        for other in nearby_floaters:
            delta = other['position'] - floater['position']
            if np.abs(np.dot(delta, np.array([0, 0, 1]))) > 0.8 * np.linalg.norm(delta):
                aligned_count += 1
        
        if aligned_count >= 2:
            # Enhanced vertical flow due to channeling
            effects['flow_enhancement'] = 1.0 + 0.1 * aligned_count
        
        return effects
        
    except Exception as e:
        logger.error(f"Fluid interaction computation failed: {e}")
        return {} 