# Parameter schema for KPP Simulator

# Enhanced parameter validation system with comprehensive rules and intelligent recommendations

def get_default_parameters():
    """Return a dictionary of default simulation parameters."""
    return {
        # Floater System Configuration (Scaled to full KPP specifications)
        "num_floaters": 66,  # Full KPP specification: 66 floaters total
        "floater_volume": 0.4,  # m³ per floater (matches technical document)
        "floater_mass_empty": 16.0,  # kg per floater
        "floater_area": 0.1,  # m² cross-sectional area (increased for larger system)
        "floater_Cd": 0.6,  # Drag coefficient (optimized for water flow)
        "air_fill_time": 0.5,  # seconds to fill floater with air
        "air_pressure": 400000,  # Pa (4.0 bar for 25m depth - sufficient pressure)
        "air_flow_rate": 1.2,  # m³/s air flow rate
        "jet_efficiency": 0.85,  # Water jet propulsion efficiency
        # Water Tank Configuration
        "tank_height": 25.0,  # m - Full KPP specification height
        "water_density": 1000.0,  # kg/m³
        "water_temperature": 293.15,  # K (20°C)
        # Mechanical System Configuration
        "sprocket_radius": 1.2,  # m (larger for 25m system)
        "sprocket_teeth": 24,  # More teeth for larger sprocket
        "flywheel_inertia": 500.0,  # kg⋅m² (increased for 500kW system)
        "gear_ratio": 39.0,  # Speed increase ratio (matches technical document)
        # Pneumatic System Configuration
        "target_pressure": 400000.0,  # Pa (4.0 bar injection pressure)
        "compressor_power": 25000.0,  # W (25kW compressor for 500kW system)
        "pressure_recovery_enabled": True,  # Enable pressure recovery system
        "pressure_recovery_efficiency": 0.22,  # 22% energy recovery
        # Timing and Control Configuration
        "pulse_interval": 2.2,  # seconds between pulses (adjusted for 66 floaters)
        "target_generator_speed": 375.0,  # RPM (grid synchronized)
        "clutch_engagement_threshold": 0.1,  # rad/s
        # Power and Electrical Configuration
        "target_power": 530000.0,  # W (530kW rated power)
        "rated_voltage": 480.0,  # V line-to-line
        "rated_frequency": 50.0,  # Hz
        "generator_efficiency": 0.94,  # High efficiency PM generator
        "power_factor_target": 0.92,  # Target power factor
        # Enhanced Physics Configuration
        "h1_active": True,  # Enable nanobubble drag reduction
        "h1_bubble_fraction": 0.05,  # 5% nanobubble fraction
        "h1_drag_reduction": 0.12,  # 12% drag reduction
        "h2_active": True,  # Enable thermal enhancement
        "h2_efficiency": 0.8,  # Thermal recovery efficiency
        "h2_buoyancy_boost": 0.06,  # 6% buoyancy boost
        "h3_active": True,  # Enable pulse-coast operation
        # Control System Configuration
        "foc_enabled": True,  # Enable Field-Oriented Control
        "torque_controller_kp": 120.0,  # FOC torque controller gains
        "torque_controller_ki": 60.0,
        "flux_controller_kp": 90.0,  # FOC flux controller gains
        "flux_controller_ki": 45.0,
        # Environmental Configuration
        "ambient_temperature": 293.15,  # K (20°C)
        "gravity": 9.81,  # m/s²
        "atmospheric_pressure": 101325.0,  # Pa
        # Safety and Limits
        "max_chain_tension": 100000.0,  # N (100kN maximum chain tension)
        "max_floater_speed": 3.0,  # m/s maximum floater speed
        "emergency_stop_enabled": True,
        # Performance Monitoring
        "enable_performance_tracking": True,
        "enable_energy_analysis": True,
        "enable_grid_services": True,
        # Legacy compatibility (adjusted for new scale)
        "thermal_coeff": 0.0001,
        "water_temp": 20.0,  # °C
        "ref_temp": 20.0,  # °C
    }


def get_parameter_constraints():
    """Return comprehensive parameter constraints for validation."""
    return {
        "num_floaters": {
            "min": 4, "max": 200, "type": int,
            "description": "Number of floaters",
            "critical": True,
            "recommendation": "Should be even number for balanced operation"
        },
        "floater_volume": {
            "min": 0.1, "max": 2.0, "type": float,
            "description": "Floater volume in m³",
            "critical": True,
            "recommendation": "Typical range: 0.1-1.0 m³ for most systems"
        },
        "floater_mass_empty": {
            "min": 5.0, "max": 100.0, "type": float,
            "description": "Empty floater mass in kg",
            "critical": False,
            "recommendation": "Should be proportional to floater volume"
        },
        "floater_area": {
            "min": 0.01, "max": 0.5, "type": float,
            "description": "Floater cross-sectional area in m²",
            "critical": False,
            "recommendation": "Affects drag and buoyancy"
        },
        "floater_Cd": {
            "min": 0.1, "max": 2.0, "type": float,
            "description": "Drag coefficient",
            "critical": False,
            "recommendation": "Typical range: 0.5-1.0 for streamlined shapes"
        },
        "air_fill_time": {
            "min": 0.1, "max": 5.0, "type": float,
            "description": "Air fill time in seconds",
            "critical": False,
            "recommendation": "Shorter times increase power density"
        },
        "air_pressure": {
            "min": 100000, "max": 2000000, "type": float,
            "description": "Air pressure in Pa",
            "critical": True,
            "recommendation": "Must exceed hydrostatic pressure + safety margin"
        },
        "air_flow_rate": {
            "min": 0.1, "max": 10.0, "type": float,
            "description": "Air flow rate in m³/s",
            "critical": False,
            "recommendation": "Should match compressor capacity"
        },
        "jet_efficiency": {
            "min": 0.5, "max": 0.95, "type": float,
            "description": "Water jet propulsion efficiency",
            "critical": False,
            "recommendation": "Higher efficiency reduces energy losses"
        },
        "tank_height": {
            "min": 5.0, "max": 100.0, "type": float,
            "description": "Tank height in meters",
            "critical": True,
            "recommendation": "Affects required air pressure and power output"
        },
        "water_density": {
            "min": 950.0, "max": 1050.0, "type": float,
            "description": "Water density in kg/m³",
            "critical": False,
            "recommendation": "Varies with temperature and salinity"
        },
        "water_temperature": {
            "min": 273.15, "max": 373.15, "type": float,
            "description": "Water temperature in Kelvin",
            "critical": False,
            "recommendation": "Affects fluid properties and efficiency"
        },
        "sprocket_radius": {
            "min": 0.1, "max": 5.0, "type": float,
            "description": "Sprocket radius in meters",
            "critical": False,
            "recommendation": "Larger radius increases mechanical advantage"
        },
        "sprocket_teeth": {
            "min": 8, "max": 100, "type": int,
            "description": "Number of sprocket teeth",
            "critical": False,
            "recommendation": "More teeth provide smoother operation"
        },
        "flywheel_inertia": {
            "min": 10.0, "max": 2000.0, "type": float,
            "description": "Flywheel inertia in kg·m²",
            "critical": False,
            "recommendation": "Higher inertia improves stability"
        },
        "gear_ratio": {
            "min": 1.0, "max": 100.0, "type": float,
            "description": "Gear ratio",
            "critical": False,
            "recommendation": "Higher ratios increase output speed"
        },
        "target_pressure": {
            "min": 100000, "max": 2000000, "type": float,
            "description": "Target pressure in Pa",
            "critical": True,
            "recommendation": "Should match air_pressure for consistency"
        },
        "compressor_power": {
            "min": 1000, "max": 100000, "type": float,
            "description": "Compressor power in W",
            "critical": False,
            "recommendation": "Should be <15% of target_power"
        },
        "pulse_interval": {
            "min": 0.5, "max": 20.0, "type": float,
            "description": "Pulse interval in seconds",
            "critical": False,
            "recommendation": "Shorter intervals increase power density"
        },
        "target_generator_speed": {
            "min": 50.0, "max": 1000.0, "type": float,
            "description": "Target generator speed in RPM",
            "critical": False,
            "recommendation": "Should match grid frequency requirements"
        },
        "target_power": {
            "min": 1000, "max": 5000000, "type": float,
            "description": "Target power in W",
            "critical": True,
            "recommendation": "Main system power rating"
        },
        "rated_voltage": {
            "min": 100.0, "max": 15000.0, "type": float,
            "description": "Rated voltage in V",
            "critical": False,
            "recommendation": "Should match electrical system requirements"
        },
        "rated_frequency": {
            "min": 25.0, "max": 60.0, "type": float,
            "description": "Rated frequency in Hz",
            "critical": False,
            "recommendation": "Should match grid frequency"
        },
        "generator_efficiency": {
            "min": 0.8, "max": 0.98, "type": float,
            "description": "Generator efficiency",
            "critical": False,
            "recommendation": "Higher efficiency reduces losses"
        },
        "power_factor_target": {
            "min": 0.8, "max": 1.0, "type": float,
            "description": "Target power factor",
            "critical": False,
            "recommendation": "Higher power factor improves grid compatibility"
        },
        "h1_bubble_fraction": {
            "min": 0.01, "max": 0.2, "type": float,
            "description": "H1 nanobubble fraction",
            "critical": False,
            "recommendation": "Typical range: 0.02-0.1"
        },
        "h1_drag_reduction": {
            "min": 0.05, "max": 0.3, "type": float,
            "description": "H1 drag reduction factor",
            "critical": False,
            "recommendation": "Typical range: 0.1-0.2"
        },
        "h2_efficiency": {
            "min": 0.5, "max": 0.95, "type": float,
            "description": "H2 thermal efficiency",
            "critical": False,
            "recommendation": "Higher efficiency improves thermal recovery"
        },
        "h2_buoyancy_boost": {
            "min": 0.01, "max": 0.2, "type": float,
            "description": "H2 buoyancy boost factor",
            "critical": False,
            "recommendation": "Typical range: 0.05-0.15"
        },
        "torque_controller_kp": {
            "min": 10.0, "max": 500.0, "type": float,
            "description": "FOC torque controller proportional gain",
            "critical": False,
            "recommendation": "Higher gains increase response speed"
        },
        "torque_controller_ki": {
            "min": 5.0, "max": 200.0, "type": float,
            "description": "FOC torque controller integral gain",
            "critical": False,
            "recommendation": "Eliminates steady-state error"
        },
        "max_chain_tension": {
            "min": 1000.0, "max": 1000000.0, "type": float,
            "description": "Maximum chain tension in N",
            "critical": True,
            "recommendation": "Safety limit for mechanical system"
        },
        "max_floater_speed": {
            "min": 0.5, "max": 10.0, "type": float,
            "description": "Maximum floater speed in m/s",
            "critical": True,
            "recommendation": "Safety limit for floater operation"
        }
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
        "total_floaters": num_floaters,
        "ascending_floaters": ascending_floaters,
        "descending_floaters": descending_floaters,
        "transition_floaters": transition_floaters,
        "floaters_per_side": num_floaters // 2,
        "angular_spacing": 2 * 3.14159 / num_floaters,  # radians between floaters
        "ensures_equal_distribution": ascending_floaters == descending_floaters,
    }


def validate_parameter_value(param_name: str, value, constraint: dict) -> dict:
    """
    Validate a single parameter value against its constraints.
    
    Args:
        param_name: Name of the parameter
        value: Value to validate
        constraint: Constraint dictionary from get_parameter_constraints()
    
    Returns:
        dict: Validation result with status, errors, warnings, and recommendations
    """
    result = {
        "valid": True,
        "errors": [],
        "warnings": [],
        "recommendations": [],
        "corrected_value": value
    }
    
    # Type validation
    expected_type = constraint.get("type", type(value))
    try:
        if expected_type == int:
            value = int(value)
        elif expected_type == float:
            value = float(value)
        elif expected_type == bool:
            if isinstance(value, str):
                value = value.lower() in ("true", "1", "yes", "on")
            else:
                value = bool(value)
    except (ValueError, TypeError):
        result["valid"] = False
        result["errors"].append(f"{param_name} must be of type {expected_type.__name__}")
        return result
    
    # Range validation
    if "min" in constraint and value < constraint["min"]:
        result["valid"] = False
        result["errors"].append(
            f"{param_name} ({value}) is below minimum {constraint['min']}. "
            f"Description: {constraint.get('description', 'No description')}"
        )
        if constraint.get("critical", False):
            result["corrected_value"] = constraint["min"]
    
    if "max" in constraint and value > constraint["max"]:
        result["valid"] = False
        result["errors"].append(
            f"{param_name} ({value}) is above maximum {constraint['max']}. "
            f"Description: {constraint.get('description', 'No description')}"
        )
        if constraint.get("critical", False):
            result["corrected_value"] = constraint["max"]
    
    # Add recommendations
    if "recommendation" in constraint:
        result["recommendations"].append({
            "parameter": param_name,
            "recommendation": constraint["recommendation"]
        })
    
    return result


def validate_cross_parameters(params: dict) -> dict:
    """
    Validate cross-parameter relationships and dependencies.
    
    Args:
        params: Parameter dictionary to validate
    
    Returns:
        dict: Cross-validation results
    """
    result = {
        "valid": True,
        "errors": [],
        "warnings": [],
        "recommendations": [],
        "corrected_params": {}
    }
    
    # Tank height vs air pressure validation
    tank_height = params.get("tank_height", 25.0)
    air_pressure = params.get("air_pressure", 400000.0)
    atmospheric_pressure = params.get("atmospheric_pressure", 101325.0)
    
    # Calculate minimum required pressure (atmospheric + hydrostatic + 10% safety margin)
    hydrostatic_pressure = 1000.0 * 9.81 * tank_height  # kg/m³ * m/s² * m
    min_required_pressure = (atmospheric_pressure + hydrostatic_pressure) * 1.1
    
    if air_pressure < min_required_pressure:
        result["valid"] = False
        result["errors"].append(
            f"Air pressure ({air_pressure/1000:.0f} kPa) is insufficient for tank height ({tank_height:.1f} m). "
            f"Minimum required: {min_required_pressure/1000:.0f} kPa "
            f"(atmospheric: {atmospheric_pressure/1000:.0f} kPa + hydrostatic: {hydrostatic_pressure/1000:.0f} kPa + 10% safety margin)"
        )
        result["corrected_params"]["air_pressure"] = min_required_pressure
        result["corrected_params"]["target_pressure"] = min_required_pressure
    
    # Power scaling validation
    target_power = params.get("target_power", 530000.0)
    compressor_power = params.get("compressor_power", 25000.0)
    
    if compressor_power > target_power * 0.15:
        result["warnings"].append(
            f"Compressor power ({compressor_power/1000:.1f} kW) is high relative to target power ({target_power/1000:.0f} kW). "
            f"Recommended: <15% of target power"
        )
        recommended_compressor = target_power * 0.1
        result["corrected_params"]["compressor_power"] = recommended_compressor
        result["recommendations"].append({
            "parameter": "compressor_power",
            "current": f"{compressor_power/1000:.1f} kW",
            "recommended": f"{recommended_compressor/1000:.1f} kW",
            "reason": "Should be <15% of target power for efficiency"
        })
    
    # Floater distribution validation
    num_floaters = params.get("num_floaters", 66)
    if num_floaters % 2 != 0:
        result["warnings"].append(
            f"Number of floaters ({num_floaters}) should be even for balanced operation. "
            f"Recommended: {num_floaters + 1}"
        )
        result["corrected_params"]["num_floaters"] = num_floaters + 1
    
    # Tank volume vs floater volume validation
    floater_volume = params.get("floater_volume", 0.4)
    tank_height = params.get("tank_height", 25.0)
    
    # Rough estimate of tank volume (assuming cylindrical tank)
    tank_diameter = tank_height * 0.4  # Assume tank diameter is 40% of height
    tank_volume = 3.14159 * (tank_diameter/2)**2 * tank_height
    total_floater_volume = floater_volume * num_floaters
    
    if total_floater_volume > tank_volume * 0.15:  # More than 15% of tank volume
        result["warnings"].append(
            f"Total floater volume ({total_floater_volume:.1f} m³) may be too large for tank volume (~{tank_volume:.1f} m³). "
            f"Recommended: <15% of tank volume"
        )
        recommended_volume = tank_volume * 0.1 / num_floaters  # 10% of tank volume
        result["corrected_params"]["floater_volume"] = recommended_volume
        result["recommendations"].append({
            "parameter": "floater_volume",
            "current": f"{floater_volume:.2f} m³",
            "recommended": f"{recommended_volume:.2f} m³",
            "reason": f"Total volume should be <15% of tank volume (~{tank_volume:.1f} m³)"
        })
    
    # Pressure consistency validation
    air_pressure = params.get("air_pressure", 400000.0)
    target_pressure = params.get("target_pressure", 400000.0)
    
    if abs(air_pressure - target_pressure) > air_pressure * 0.1:  # More than 10% difference
        result["warnings"].append(
            f"Air pressure ({air_pressure/1000:.0f} kPa) and target pressure ({target_pressure/1000:.0f} kPa) "
            f"should be consistent. Recommended: Set target_pressure = air_pressure"
        )
        result["corrected_params"]["target_pressure"] = air_pressure
    
    return result


def validate_parameters_batch(params: dict) -> dict:
    """
    Enhanced parameter validation with comprehensive error checking and recommendations.
    
    Args:
        params: Parameter dictionary to validate
    
    Returns:
        dict: Validation results with detailed feedback
    """
    defaults = get_default_parameters()
    constraints = get_parameter_constraints()
    
    result = {
        "valid": True,
        "validated_params": {},
        "errors": [],
        "warnings": [],
        "recommendations": [],
        "corrected_params": {},
        "missing_params": [],
        "floater_distribution": None
    }
    
    # Validate each parameter
    for param_name, default_value in defaults.items():
        value = params.get(param_name, default_value)
        constraint = constraints.get(param_name, {})
        
        if param_name in constraints:
            validation = validate_parameter_value(param_name, value, constraint)
            
            if not validation["valid"]:
                result["valid"] = False
                result["errors"].extend(validation["errors"])
            
            result["warnings"].extend(validation["warnings"])
            result["recommendations"].extend(validation["recommendations"])
            
            # Use corrected value if available
            final_value = validation["corrected_value"]
        else:
            final_value = value
        
        result["validated_params"][param_name] = final_value
    
    # Check for missing critical parameters
    critical_params = [name for name, constraint in constraints.items() if constraint.get("critical", False)]
    for param_name in critical_params:
        if param_name not in params:
            result["missing_params"].append(param_name)
            result["warnings"].append(f"Critical parameter '{param_name}' not provided, using default value")
    
    # Cross-parameter validation
    cross_validation = validate_cross_parameters(result["validated_params"])
    
    if not cross_validation["valid"]:
        result["valid"] = False
        result["errors"].extend(cross_validation["errors"])
    
    result["warnings"].extend(cross_validation["warnings"])
    result["recommendations"].extend(cross_validation["recommendations"])
    result["corrected_params"].update(cross_validation["corrected_params"])
    
    # Apply corrections
    for param_name, corrected_value in result["corrected_params"].items():
        result["validated_params"][param_name] = corrected_value
    
    # Calculate floater distribution
    num_floaters = result["validated_params"]["num_floaters"]
    result["floater_distribution"] = get_floater_distribution(num_floaters)
    
    # Generate summary
    result["summary"] = {
        "total_parameters": len(defaults),
        "validated_parameters": len(result["validated_params"]),
        "critical_errors": len([e for e in result["errors"] if "critical" in e.lower()]),
        "warnings_count": len(result["warnings"]),
        "recommendations_count": len(result["recommendations"]),
        "missing_critical": len([p for p in result["missing_params"] if p in critical_params]),
        "success_probability": "High" if result["valid"] and len(result["errors"]) == 0 else "Medium" if len(result["errors"]) <= 2 else "Low"
    }
    
    return result


def validate_kpp_system_parameters(params: dict) -> dict:
    """
    Legacy function for backward compatibility.
    Now calls the enhanced validate_parameters_batch function.
    
    Args:
        params: Parameter dictionary to validate

    Returns:
        dict: Validation results with corrections
    """
    return validate_parameters_batch(params)
