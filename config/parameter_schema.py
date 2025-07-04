# Parameter schema for KPP Simulator

def get_default_parameters():
    """Return a dictionary of default simulation parameters."""
    return {
        # Floater System Configuration (Scaled to full KPP specifications)
        'num_floaters': 66,  # Full KPP specification: 66 floaters total
        'floater_volume': 0.4,  # m³ per floater (matches technical document)
        'floater_mass_empty': 16.0,  # kg per floater
        'floater_area': 0.1,  # m² cross-sectional area (increased for larger system)
        'floater_Cd': 0.6,  # Drag coefficient (optimized for water flow)
        'air_fill_time': 0.5,  # seconds to fill floater with air
        'air_pressure': 400000,  # Pa (4.0 bar for 25m depth - sufficient pressure)
        'air_flow_rate': 1.2,  # m³/s air flow rate
        'jet_efficiency': 0.85,  # Water jet propulsion efficiency
        
        # Water Tank Configuration
        'tank_height': 25.0,  # m - Full KPP specification height
        'water_density': 1000.0,  # kg/m³
        'water_temperature': 293.15,  # K (20°C)
        
        # Mechanical System Configuration
        'sprocket_radius': 1.2,  # m (larger for 25m system)
        'sprocket_teeth': 24,  # More teeth for larger sprocket
        'flywheel_inertia': 500.0,  # kg⋅m² (increased for 500kW system)
        'gear_ratio': 39.0,  # Speed increase ratio (matches technical document)
        
        # Pneumatic System Configuration
        'target_pressure': 400000.0,  # Pa (4.0 bar injection pressure)
        'compressor_power': 25000.0,  # W (25kW compressor for 500kW system)
        'pressure_recovery_enabled': True,  # Enable pressure recovery system
        'pressure_recovery_efficiency': 0.22,  # 22% energy recovery
        
        # Timing and Control Configuration
        'pulse_interval': 2.2,  # seconds between pulses (adjusted for 66 floaters)
        'target_generator_speed': 375.0,  # RPM (grid synchronized)
        'clutch_engagement_threshold': 0.1,  # rad/s
        
        # Power and Electrical Configuration
        'target_power': 530000.0,  # W (530kW rated power)
        'rated_voltage': 480.0,  # V line-to-line
        'rated_frequency': 50.0,  # Hz
        'generator_efficiency': 0.94,  # High efficiency PM generator
        'power_factor_target': 0.92,  # Target power factor
        
        # Enhanced Physics Configuration
        'h1_active': True,  # Enable nanobubble drag reduction
        'h1_bubble_fraction': 0.05,  # 5% nanobubble fraction
        'h1_drag_reduction': 0.12,  # 12% drag reduction
        'h2_active': True,  # Enable thermal enhancement
        'h2_efficiency': 0.8,  # Thermal recovery efficiency
        'h2_buoyancy_boost': 0.06,  # 6% buoyancy boost
        'h3_active': True,  # Enable pulse-coast operation
        
        # Control System Configuration
        'foc_enabled': True,  # Enable Field-Oriented Control
        'torque_controller_kp': 120.0,  # FOC torque controller gains
        'torque_controller_ki': 60.0,
        'flux_controller_kp': 90.0,  # FOC flux controller gains
        'flux_controller_ki': 45.0,
        
        # Environmental Configuration
        'ambient_temperature': 293.15,  # K (20°C)
        'gravity': 9.81,  # m/s²
        'atmospheric_pressure': 101325.0,  # Pa
        
        # Safety and Limits
        'max_chain_tension': 100000.0,  # N (100kN maximum chain tension)
        'max_floater_speed': 3.0,  # m/s maximum floater speed
        'emergency_stop_enabled': True,
        
        # Performance Monitoring
        'enable_performance_tracking': True,
        'enable_energy_analysis': True,
        'enable_grid_services': True,
        
        # Legacy compatibility (adjusted for new scale)
        'thermal_coeff': 0.0001,
        'water_temp': 20.0,  # °C
        'ref_temp': 20.0,    # °C
    }

def get_floater_distribution(num_floaters: int) -> dict:
    """
    Calculate optimal floater distribution ensuring equal ascending/descending 
    and proper sprocket transition management.
    
    Args:
        num_floaters: Total number of floaters
        
    Returns:
        dict: Floater distribution configuration
    """
    # Ensure even number for equal ascending/descending split
    if num_floaters % 2 != 0:
        num_floaters += 1  # Round up to even number
        
    # Calculate distribution
    ascending_floaters = num_floaters // 2 - 1  # -1 for transition floater
    descending_floaters = num_floaters // 2 - 1  # -1 for transition floater
    transition_floaters = 2  # Always 2 floaters in transition (top and bottom sprockets)
    
    return {
        'total_floaters': num_floaters,
        'ascending_floaters': ascending_floaters,
        'descending_floaters': descending_floaters,
        'transition_floaters': transition_floaters,
        'floaters_per_side': num_floaters // 2,
        'angular_spacing': 2 * 3.14159 / num_floaters,  # radians between floaters
        'ensures_equal_distribution': ascending_floaters == descending_floaters,
    }

def validate_kpp_system_parameters(params: dict) -> dict:
    """
    Validate KPP system parameters for physical consistency and safety.
    
    Args:
        params: Parameter dictionary to validate
        
    Returns:
        dict: Validation results with corrections
    """
    validated = params.copy()
    errors = []
    warnings = []
    
    # Validate floater distribution
    num_floaters = validated.get('num_floaters', 66)
    if num_floaters % 2 != 0:
        warnings.append(f"num_floaters ({num_floaters}) should be even for equal distribution. Rounding up.")
        validated['num_floaters'] = num_floaters + 1
        
    # Validate tank height vs air pressure
    tank_height = validated.get('tank_height', 25.0)
    air_pressure = validated.get('air_pressure', 350000.0)
    min_pressure = 101325.0 + (1000.0 * 9.81 * tank_height)  # Atmospheric + hydrostatic
    
    if air_pressure < min_pressure * 1.1:  # Need 10% margin
        errors.append(f"Air pressure {air_pressure/1000:.0f}kPa too low for {tank_height}m tank. "
                     f"Need minimum {min_pressure*1.1/1000:.0f}kPa")
                     
    # Validate power scaling consistency
    target_power = validated.get('target_power', 530000.0)
    compressor_power = validated.get('compressor_power', 25000.0)
    
    if compressor_power > target_power * 0.15:  # Should be <15% of output
        warnings.append(f"Compressor power ({compressor_power/1000:.0f}kW) seems high "
                       f"relative to target power ({target_power/1000:.0f}kW)")
                       
    # Validate floater volume vs tank height
    floater_volume = validated.get('floater_volume', 0.4)
    if floater_volume < 0.1 or floater_volume > 1.0:
        warnings.append(f"Floater volume {floater_volume:.2f}m³ outside typical range (0.1-1.0 m³)")
        
    return {
        'valid': len(errors) == 0,
        'validated_params': validated,
        'errors': errors,
        'warnings': warnings,
        'floater_distribution': get_floater_distribution(validated['num_floaters']),
    }

def validate_parameters_batch(params):
    """Validate a batch of simulation parameters. Returns dict with 'valid', 'validated_params', and 'errors'."""
    defaults = get_default_parameters()
    validated = {}
    errors = []
    for key, default in defaults.items():
        value = params.get(key, default)
        # Basic type/range checks
        if isinstance(default, int):
            try:
                value = int(value)
            except Exception:
                errors.append(f"{key} must be an integer.")
                continue
        elif isinstance(default, float):
            try:
                value = float(value)
            except Exception:
                errors.append(f"{key} must be a float.")
                continue
        # Add more validation as needed (e.g., range checks)
        validated[key] = value
    valid = len(errors) == 0
    return {'valid': valid, 'validated_params': validated, 'errors': errors}
