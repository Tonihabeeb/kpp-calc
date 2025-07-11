# Phase 4 Configuration Guide

## Overview
This guide provides detailed configuration information for all Phase 4 components of the KPP simulator. Each component can be configured through configuration files and runtime parameters to optimize performance and adapt to specific requirements.

## Table of Contents
1. [Grid Services Coordinator](#grid-services-coordinator)
2. [Battery Storage System](#battery-storage-system)
3. [Demand Response System](#demand-response-system)
4. [Economic Optimization System](#economic-optimization-system)

## Grid Services Coordinator

### Basic Configuration
```python
# config/grid_services/coordinator_config.py

COORDINATOR_CONFIG = {
    # Resource management
    'available_capacity': 1000.0,     # kW
    'update_interval': 1.0,           # seconds
    'max_services': 10,
    
    # Service priorities
    'service_priorities': {
        'frequency_response': 'HIGH',
        'voltage_support': 'MEDIUM',
        'energy_arbitrage': 'LOW'
    },
    
    # Performance settings
    'performance_logging': True,
    'metrics_interval': 300,          # seconds
    'history_retention': 7            # days
}
```

### Service Configuration
```python
# config/grid_services/services_config.py

SERVICES_CONFIG = {
    'frequency_response': {
        'enabled': True,
        'capacity_limit': 300.0,      # kW
        'response_time': 0.5,         # seconds
        'droop': 0.05,
        'deadband': 0.0002           # Hz
    },
    
    'voltage_support': {
        'enabled': True,
        'capacity_limit': 200.0,      # kW
        'voltage_range': (0.95, 1.05),
        'reactive_power': 0.3
    },
    
    'energy_arbitrage': {
        'enabled': True,
        'capacity_limit': 500.0,      # kW
        'min_price_difference': 10.0,  # $/MWh
        'max_duration': 4             # hours
    }
}
```

## Battery Storage System

### Physical Configuration
```python
# config/storage/battery_config.py

BATTERY_CONFIG = {
    # Physical parameters
    'capacity': 1000.0,              # kWh
    'max_power': 500.0,              # kW
    'min_soc': 0.1,                  # 10%
    'max_soc': 0.9,                  # 90%
    
    # Efficiency parameters
    'charge_efficiency': 0.95,
    'discharge_efficiency': 0.95,
    'self_discharge_rate': 0.001,    # per hour
    
    # Thermal parameters
    'optimal_temp': 25.0,            # °C
    'max_temp': 40.0,                # °C
    'min_temp': 10.0,                # °C
    'thermal_resistance': 0.1,        # °C/kW
    
    # Lifecycle parameters
    'cycle_life': 5000,
    'calendar_life': 10,             # years
    'depth_of_discharge': 0.8
}
```

### Service Configuration
```python
# config/storage/services_config.py

STORAGE_SERVICES_CONFIG = {
    'grid_stabilization': {
        'enabled': True,
        'power_reserve': 100.0,      # kW
        'response_time': 0.1,        # seconds
        'frequency_deadband': 0.0002  # Hz
    },
    
    'energy_arbitrage': {
        'enabled': True,
        'min_price_diff': 10.0,      # $/MWh
        'max_cycles_per_day': 2,
        'min_cycle_revenue': 50.0     # $
    },
    
    'peak_shaving': {
        'enabled': True,
        'peak_threshold': 800.0,     # kW
        'response_time': 1.0,        # seconds
        'max_duration': 2            # hours
    }
}
```

## Demand Response System

### Forecasting Configuration
```python
# config/demand_response/forecasting_config.py

FORECASTING_CONFIG = {
    # Model parameters
    'model_type': 'lstm',
    'features': [
        'time_of_day',
        'day_of_week',
        'temperature',
        'humidity',
        'historical_load'
    ],
    
    # Training parameters
    'training_window': 30,           # days
    'validation_split': 0.2,
    'batch_size': 32,
    'epochs': 100,
    
    # Prediction parameters
    'forecast_horizon': 24,          # hours
    'update_interval': 900,          # seconds
    'confidence_interval': 0.95
}
```

### Curtailment Configuration
```python
# config/demand_response/curtailment_config.py

CURTAILMENT_CONFIG = {
    # Control parameters
    'min_reduction': 50.0,           # kW
    'max_reduction': 200.0,          # kW
    'ramp_rate': 10.0,              # kW/minute
    'min_notice': 300,              # seconds
    
    # Load management
    'priority_loads': [
        'critical_process_1',
        'life_safety_systems',
        'essential_services'
    ],
    'non_curtailable_load': 200.0,   # kW
    'max_events_per_day': 2,
    'min_recovery_time': 3600        # seconds
}
```

## Economic Optimization System

### Market Configuration
```python
# config/economic/market_config.py

MARKET_CONFIG = {
    # Market parameters
    'market_id': 'energy_market_1',
    'participant_id': 'kpp_plant_1',
    'update_interval': 300,          # seconds
    
    # Trading parameters
    'min_bid_size': 100.0,          # kW
    'max_bid_size': 500.0,          # kW
    'price_threshold': 50.0,         # $/MWh
    'min_profit_margin': 0.1,
    
    # Position limits
    'max_position_size': 1000.0,     # kW
    'position_duration': 3600,       # seconds
    'max_open_positions': 5
}
```

### Risk Management Configuration
```python
# config/economic/risk_config.py

RISK_CONFIG = {
    # Risk parameters
    'risk_tolerance': 0.2,
    'max_drawdown': 0.1,
    'stop_loss': 0.05,
    'var_confidence': 0.99,
    
    # Position limits
    'position_limits': {
        'hourly': 1000.0,           # kW
        'daily': 5000.0,            # kW
        'weekly': 20000.0           # kW
    },
    
    # Hedging configuration
    'hedging_instruments': [
        'futures',
        'options',
        'swaps'
    ],
    'hedge_ratio': 0.7,
    'max_hedge_cost': 0.1           # % of position value
}
```

## Environment Variables
```bash
# .env

# System configuration
KPP_ENV=production                  # or development, testing
LOG_LEVEL=INFO                      # DEBUG, INFO, WARNING, ERROR
DATA_DIR=/path/to/data

# Grid services
GRID_SERVICES_ENABLED=true
MAX_SERVICES=10
PERFORMANCE_LOGGING=true

# Storage system
BATTERY_ENABLED=true
THERMAL_MONITORING=true
LIFECYCLE_TRACKING=true

# Demand response
FORECASTING_ENABLED=true
CURTAILMENT_ENABLED=true
EMERGENCY_DR_ENABLED=true

# Economic optimization
MARKET_ENABLED=true
RISK_MANAGEMENT_ENABLED=true
AUTO_HEDGING=true

# API endpoints
MARKET_API_URL=https://market.example.com/api
WEATHER_API_URL=https://weather.example.com/api
GRID_API_URL=https://grid.example.com/api
```

## Configuration Best Practices

### 1. Environment-specific Configuration
- Use different configuration files for development, testing, and production
- Override sensitive values using environment variables
- Document all configuration options

### 2. Performance Optimization
- Adjust update intervals based on system capabilities
- Configure appropriate batch sizes and processing windows
- Balance resource allocation across services

### 3. Security Considerations
- Store sensitive data in environment variables
- Use secure connections for external APIs
- Implement appropriate access controls

### 4. Monitoring and Logging
- Enable performance logging in production
- Configure appropriate metric collection intervals
- Set up error reporting and alerting

### 5. Resource Management
- Configure realistic capacity limits
- Set appropriate thresholds for services
- Implement failsafe values

## Configuration Validation

### Validation Script
```python
# scripts/validate_config.py

def validate_config():
    """Validate all configuration files"""
    errors = []
    warnings = []
    
    # Validate coordinator config
    if not validate_coordinator_config():
        errors.append("Invalid coordinator configuration")
    
    # Validate battery config
    if not validate_battery_config():
        errors.append("Invalid battery configuration")
    
    # Validate demand response config
    if not validate_dr_config():
        errors.append("Invalid demand response configuration")
    
    # Validate economic config
    if not validate_economic_config():
        errors.append("Invalid economic configuration")
    
    # Report results
    if errors:
        raise ConfigurationError("\n".join(errors))
    
    if warnings:
        logger.warning("\n".join(warnings))
    
    return True
```

### Usage
```bash
# Validate configuration
python scripts/validate_config.py

# Apply configuration
python scripts/apply_config.py --env production
```

## Troubleshooting

### Common Configuration Issues

1. **Resource Conflicts**
   - Check service priority configuration
   - Verify capacity allocations
   - Review update intervals

2. **Performance Issues**
   - Adjust batch sizes and processing windows
   - Optimize update intervals
   - Review resource allocation

3. **Integration Problems**
   - Verify API endpoints
   - Check authentication configuration
   - Validate data formats

### Configuration Checklist

- [ ] Environment variables set correctly
- [ ] Configuration files present for all components
- [ ] Validation script passes without errors
- [ ] Resource limits properly configured
- [ ] Security settings reviewed
- [ ] Monitoring enabled
- [ ] Backup configuration available 