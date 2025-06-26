# Parameter Schema for KPP Simulator
# Defines all expected input parameters with types, units, and valid ranges

PARAM_SCHEMA = {
    # Basic Physical Parameters
    'air_pressure': {'type': float, 'unit': 'bar', 'min': 0.1, 'max': 10.0, 'default': 3.0},
    'num_floaters': {'type': int, 'unit': 'count', 'min': 1, 'max': 20, 'default': 8},
    'floater_volume': {'type': float, 'unit': 'm³', 'min': 0.1, 'max': 1.0, 'default': 0.3},
    'floater_mass_empty': {'type': float, 'unit': 'kg', 'min': 5.0, 'max': 50.0, 'default': 18.0},
    'floater_area': {'type': float, 'unit': 'm²', 'min': 0.01, 'max': 0.1, 'default': 0.035},
    
    # Pulse Physics Parameters
    'air_fill_time': {'type': float, 'unit': 's', 'min': 0.1, 'max': 2.0, 'default': 0.5},
    'air_flow_rate': {'type': float, 'unit': 'm³/s', 'min': 0.1, 'max': 2.0, 'default': 0.6},
    'jet_efficiency': {'type': float, 'unit': '-', 'min': 0.5, 'max': 1.0, 'default': 0.85},
    
    # Mechanical Parameters
    'sprocket_radius': {'type': float, 'unit': 'm', 'min': 0.1, 'max': 2.0, 'default': 0.5},
    'flywheel_inertia': {'type': float, 'unit': 'kg⋅m²', 'min': 10.0, 'max': 200.0, 'default': 50.0},
    'pulse_interval': {'type': float, 'unit': 's', 'min': 0.5, 'max': 10.0, 'default': 2.0},
    
    # H1: Nanobubble Effects
    'nanobubble_frac': {'type': float, 'unit': '%', 'min': 0.0, 'max': 1.0, 'default': 0.0},
    
    # H2: Thermal Enhancement
    'thermal_coeff': {'type': float, 'unit': '-', 'min': 0.0, 'max': 1.0, 'default': 0.0001},
    'water_temp': {'type': float, 'unit': '°C', 'min': 0.0, 'max': 100.0, 'default': 20.0},
    'ref_temp': {'type': float, 'unit': '°C', 'min': 0.0, 'max': 100.0, 'default': 20.0},
    
    # H3: Pulse Mode
    'pulse_enabled': {'type': bool, 'unit': 'bool', 'default': False},
    
    # Advanced Parameters
    'target_pressure': {'type': float, 'unit': 'bar', 'min': 1.0, 'max': 20.0, 'default': 5.0},
    'target_power': {'type': float, 'unit': 'W', 'min': 100000, 'max': 1000000, 'default': 530000},
    'target_rpm': {'type': float, 'unit': 'rpm', 'min': 100, 'max': 1000, 'default': 375}
}

def validate_parameter(param_name, value):
    """
    Validate a single parameter against the schema.
    
    Args:
        param_name (str): The parameter name
        value: The parameter value to validate
        
    Returns:
        tuple: (is_valid, converted_value, error_message)
    """
    if param_name not in PARAM_SCHEMA:
        return False, None, f"Unknown parameter: {param_name}"
    
    schema = PARAM_SCHEMA[param_name]
    
    # Type validation and conversion
    try:
        if schema['type'] is float:
            converted_value = float(value)
        elif schema['type'] is int:
            converted_value = int(value)
        elif schema['type'] is bool:
            if isinstance(value, bool):
                converted_value = value
            else:
                converted_value = str(value).lower() in ('true', '1', 'yes', 'on')
        else:
            return False, None, f"Unsupported parameter type: {schema['type']}"
    except (ValueError, TypeError) as e:
        return False, None, f"Invalid type for {param_name}: expected {schema['type'].__name__}, got {type(value).__name__}"
    
    # Range validation
    if 'min' in schema and converted_value < schema['min']:
        return False, None, f"{param_name} below minimum: {converted_value} < {schema['min']}"
    
    if 'max' in schema and converted_value > schema['max']:
        return False, None, f"{param_name} above maximum: {converted_value} > {schema['max']}"
    
    return True, converted_value, None

def get_default_parameters():
    """
    Get a dictionary of all default parameter values.
    
    Returns:
        dict: Default parameter values
    """
    return {param: schema['default'] for param, schema in PARAM_SCHEMA.items()}

def get_parameter_info(param_name):
    """
    Get detailed information about a parameter.
    
    Args:
        param_name (str): The parameter name
        
    Returns:
        dict: Parameter schema information or None if not found
    """
    return PARAM_SCHEMA.get(param_name)

def validate_parameters_batch(parameters):
    """
    Validate a batch of parameters.
    
    Args:
        parameters (dict): Dictionary of parameter name-value pairs
        
    Returns:
        tuple: (valid_params, errors)
            valid_params (dict): Successfully validated parameters
            errors (list): List of error messages
    """
    valid_params = {}
    errors = []
    
    for param_name, value in parameters.items():
        is_valid, converted_value, error = validate_parameter(param_name, value)
        if is_valid:
            valid_params[param_name] = converted_value
        else:
            errors.append(error)
    
    return valid_params, errors
