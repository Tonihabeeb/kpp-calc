#!/usr/bin/env python3
"""
Fix simulation parameters to prevent crashes
"""
import json

def fix_simulation_parameters():
    """Fix problematic simulation parameters"""
    
    # Load current parameters
    with open('kpp_tuned_parameters.json', 'r') as f:
        params = json.load(f)
    
    print("🔍 CURRENT PROBLEMATIC PARAMETERS:")
    print(f"  target_power: {params['target_power']:,.0f} W ({params['target_power']/1000000:.1f} MW)")
    print(f"  time_step: {params['time_step']} s")
    print(f"  num_floaters: {params['num_floaters']}")
    print(f"  air_pressure: {params['air_pressure']:,.0f} Pa")
    
    # Create stable parameters
    stable_params = params.copy()
    stable_params.update({
        'target_power': 50000.0,      # 50 kW instead of 3.5 MW
        'time_step': 0.01,            # Smaller time step for stability  
        'num_floaters': 10,           # Reasonable number
        'air_pressure': 250000.0,     # 2.5 bar (250 kPa)
        'target_rpm': 500.0,          # Lower RPM for stability
        'gear_ratio': 10.0,           # Lower gear ratio
        'floater_volume': 0.3,        # Smaller volume
        'floater_mass_empty': 12.0    # Lighter floaters
    })
    
    # Save stable parameters
    with open('kpp_stable_parameters.json', 'w') as f:
        json.dump(stable_params, f, indent=2)
    
    print("\n✅ CREATED STABLE PARAMETERS:")
    print(f"  target_power: {stable_params['target_power']:,.0f} W ({stable_params['target_power']/1000:.0f} kW)")
    print(f"  time_step: {stable_params['time_step']} s")
    print(f"  num_floaters: {stable_params['num_floaters']}")
    print(f"  air_pressure: {stable_params['air_pressure']:,.0f} Pa")
    print(f"  target_rpm: {stable_params['target_rpm']} RPM")
    
    return stable_params

if __name__ == "__main__":
    fix_simulation_parameters() 