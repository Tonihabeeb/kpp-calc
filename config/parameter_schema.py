# Parameter schema for KPP Simulator

def get_default_parameters():
    """Return a dictionary of default simulation parameters."""
    return {
        'num_floaters': 8,
        'floater_volume': 0.3,
        'floater_mass_empty': 18.0,
        'floater_area': 0.035,
        'floater_Cd': 0.8,
        'air_fill_time': 0.5,
        'air_pressure': 300000,
        'air_flow_rate': 0.6,
        'jet_efficiency': 0.85,
        'sprocket_radius': 0.5,
        'flywheel_inertia': 50.0,
        'pulse_interval': 2.0,
        'thermal_coeff': 0.0001,
        'water_temp': 20.0,
        'ref_temp': 20.0
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
