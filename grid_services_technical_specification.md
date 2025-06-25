# Grid Services Technical Specification

## Document Information
- **Version**: 1.0
- **Date**: December 2024
- **Phase**: 7 - Advanced Grid Services
- **Status**: Specification

## Table of Contents
1. [Overview](#overview)
2. [Frequency Response Services](#frequency-response-services)
3. [Voltage Support Services](#voltage-support-services)
4. [Demand Response Integration](#demand-response-integration)
5. [Energy Storage Integration](#energy-storage-integration)
6. [Grid Services Coordination](#grid-services-coordination)
7. [Economic Optimization](#economic-optimization)
8. [Performance Requirements](#performance-requirements)
9. [Interface Specifications](#interface-specifications)
10. [Testing Requirements](#testing-requirements)

## Overview

The Advanced Grid Services system transforms the KPP simulation into a comprehensive grid asset capable of providing multiple grid stability, power quality, and economic optimization services. This specification defines the technical requirements, interfaces, and performance criteria for all grid services.

### System Architecture
```
┌─────────────────────────────────────────────────────────┐
│                Main Simulation Engine                   │
└─────────────────────┬───────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────┐
│            Grid Services Coordinator                    │
│  • Service prioritization                              │
│  • Resource allocation                                 │
│  • Revenue optimization                                │
│  • Conflict resolution                                 │
└─────┬─────────┬─────────┬─────────┬─────────────────────┘
      │         │         │         │
┌─────▼──┐ ┌────▼───┐ ┌───▼────┐ ┌──▼──────┐
│Frequency│ │Voltage │ │Demand  │ │Energy   │
│Response │ │Support │ │Response│ │Storage  │
│Services │ │Services│ │        │ │         │
└────────┘ └────────┘ └────────┘ └─────────┘
```

## Frequency Response Services

### 1. Primary Frequency Control (PFC)

#### Technical Requirements
- **Response Time**: <2 seconds from frequency deviation detection
- **Dead Band**: ±0.02 Hz (configurable ±0.01 to ±0.05 Hz)
- **Droop Setting**: 2-5% (configurable)
- **Response Range**: ±10% of rated power
- **Accuracy**: ±1% of commanded response

#### Operating Characteristics
```python
class PrimaryFrequencyControlSpec:
    RESPONSE_TIME_MAX = 2.0  # seconds
    DEAD_BAND_DEFAULT = 0.02  # Hz
    DEAD_BAND_RANGE = (0.01, 0.05)  # Hz
    DROOP_DEFAULT = 0.04  # 4%
    DROOP_RANGE = (0.02, 0.05)  # 2-5%
    RESPONSE_RANGE = 0.10  # ±10% of rated power
    ACCURACY_REQUIREMENT = 0.01  # ±1%
    NOMINAL_FREQUENCY = 60.0  # Hz (50.0 for European systems)
```

#### Response Curve
```
Power Response (p.u.)
     ▲
     │     ┌───────────────────
     │    ╱
 0.1 │   ╱
     │  ╱
   0 ├─┼─────────────────────► Frequency (Hz)
     │  │ Dead Band
-0.1 │   ╲
     │    ╲
     │     └───────────────────
     │
   59.8  60.0  60.2
```

### 2. Secondary Frequency Control (SFC)

#### Technical Requirements
- **Response Time**: <5 minutes to full response
- **AGC Signal Processing**: Real-time processing of Automatic Generation Control signals
- **Regulation Range**: ±5% of rated power
- **Ramp Rate**: 20% of rated power per minute
- **Accuracy**: ±1% of AGC signal

#### AGC Signal Interface
```python
class AGCSignalSpec:
    SIGNAL_RANGE = (-1.0, 1.0)  # Normalized ±1.0
    UPDATE_RATE = 1.0  # seconds
    REGULATION_CAPACITY = 0.05  # 5% of rated power
    RAMP_RATE = 0.20  # 20% per minute
    RESPONSE_TIME_MAX = 300.0  # 5 minutes
    ACCURACY_REQUIREMENT = 0.01  # ±1%
```

### 3. Synthetic Inertia

#### Technical Requirements
- **Response Time**: <500ms to frequency transients
- **ROCOF Threshold**: 0.5 Hz/s (configurable)
- **Inertia Constant**: 2-8 seconds (configurable)
- **Response Duration**: 10-30 seconds
- **Measurement Window**: 100ms for ROCOF calculation

#### Inertia Response Characteristics
```python
class SyntheticInertiaSpec:
    RESPONSE_TIME_MAX = 0.5  # seconds
    ROCOF_THRESHOLD_DEFAULT = 0.5  # Hz/s
    ROCOF_THRESHOLD_RANGE = (0.1, 1.0)  # Hz/s
    INERTIA_CONSTANT_DEFAULT = 4.0  # seconds
    INERTIA_CONSTANT_RANGE = (2.0, 8.0)  # seconds
    RESPONSE_DURATION_DEFAULT = 10.0  # seconds
    MEASUREMENT_WINDOW = 0.1  # seconds
```

## Voltage Support Services

### 1. Reactive Power Management

#### Technical Requirements
- **Q Capacity**: ±60% of rated active power
- **Voltage Range**: 0.88-1.10 per unit
- **Droop Setting**: 3% (configurable 1-5%)
- **Response Time**: <1 second
- **Power Factor Range**: 0.85 leading to 0.95 lagging

#### Q-V Characteristic Curve
```
Reactive Power (p.u.)
     ▲
     │
 0.6 │ ┌─────────────────────
     │╱
     │
   0 ├─────────────────────► Voltage (p.u.)
     │                    ╲
     │                     ╲
-0.6 │                      └─────
     │
    0.88  0.95  1.0  1.05  1.10
```

#### Technical Specifications
```python
class ReactivePowerSpec:
    Q_CAPACITY = 0.6  # ±60% of rated power
    VOLTAGE_RANGE = (0.88, 1.10)  # per unit
    DROOP_DEFAULT = 0.03  # 3%
    DROOP_RANGE = (0.01, 0.05)  # 1-5%
    RESPONSE_TIME_MAX = 1.0  # seconds
    POWER_FACTOR_RANGE = (0.85, 0.95)  # leading to lagging
    DEAD_BAND = 0.02  # ±2% voltage dead band
```

### 2. Dynamic Voltage Support

#### Technical Requirements
- **Fast Response Time**: <100ms for voltage transients
- **Voltage Deviation Threshold**: ±2% for fast response
- **Fast Response Capacity**: 30% of total Q capacity
- **Coordination**: Interface with other voltage control devices
- **Ride-Through Capability**: LVRT/HVRT per grid codes

#### Dynamic Response Specifications
```python
class DynamicVoltageSpec:
    FAST_RESPONSE_TIME = 0.1  # seconds
    VOLTAGE_THRESHOLD = 0.02  # ±2% per unit
    FAST_RESPONSE_CAPACITY = 0.3  # 30% of Q capacity
    COORDINATION_DELAY = 0.05  # 50ms coordination delay
    LVRT_CURVE = {  # Low Voltage Ride Through
        0.00: 0.15,  # 0% voltage for 150ms
        0.88: 3.0,   # 88% voltage for 3s
        0.90: 60.0   # 90% voltage for 60s
    }
```

## Demand Response Integration

### 1. Load Curtailment Services

#### Technical Requirements
- **Response Time**: <5 minutes for emergency curtailment
- **Curtailment Levels**: 10%, 25%, 50%, 75% reduction
- **Duration**: 30 minutes to 6 hours
- **Recovery Time**: <15 minutes to normal operation
- **Communication**: DR-enabled communication interface

#### Curtailment Priority Levels
```python
class LoadCurtailmentSpec:
    RESPONSE_TIME_EMERGENCY = 300  # 5 minutes
    RESPONSE_TIME_ECONOMIC = 900   # 15 minutes
    CURTAILMENT_LEVELS = [0.1, 0.25, 0.5, 0.75]  # 10-75%
    DURATION_RANGE = (1800, 21600)  # 30min to 6hr
    RECOVERY_TIME_MAX = 900  # 15 minutes
    
    PRIORITY_LEVELS = {
        'emergency': 1,      # Grid reliability
        'economic': 2,       # Price response
        'environmental': 3,  # Environmental benefits
        'voluntary': 4       # Customer voluntary
    }
```

### 2. Peak Shaving and Load Forecasting

#### Technical Requirements
- **Forecast Horizon**: 24 hours ahead
- **Forecast Accuracy**: <5% MAPE (Mean Absolute Percentage Error)
- **Update Frequency**: Hourly forecast updates
- **Peak Detection**: 85% of peak capacity threshold
- **Optimization Horizon**: 4-hour rolling optimization

#### Forecasting Specifications
```python
class LoadForecastingSpec:
    FORECAST_HORIZON = 24  # hours
    ACCURACY_REQUIREMENT = 0.05  # 5% MAPE
    UPDATE_FREQUENCY = 3600  # seconds (hourly)
    PEAK_THRESHOLD = 0.85  # 85% of peak capacity
    OPTIMIZATION_HORIZON = 4  # hours
    
    FORECAST_INPUTS = [
        'historical_load',
        'weather_forecast',
        'calendar_data',
        'economic_indicators'
    ]
```

## Energy Storage Integration

### 1. Battery Storage System

#### Technical Requirements
- **Power Rating**: 20% of KPP rated power
- **Energy Capacity**: 4-hour duration at rated power
- **Response Time**: <20ms for grid services
- **Round-Trip Efficiency**: >90%
- **Cycle Life**: >6000 cycles at 80% depth of discharge

#### Battery Specifications
```python
class BatteryStorageSpec:
    POWER_RATING_RATIO = 0.20  # 20% of KPP rated power
    ENERGY_DURATION = 4.0  # hours at rated power
    RESPONSE_TIME_MAX = 0.02  # 20ms
    EFFICIENCY_ROUNDTRIP = 0.90  # 90%
    CYCLE_LIFE_MIN = 6000  # cycles
    DEPTH_OF_DISCHARGE = 0.80  # 80%
    
    SOC_LIMITS = {
        'min': 0.10,  # 10% minimum SOC
        'max': 0.95,  # 95% maximum SOC
        'target': 0.50  # 50% target SOC
    }
```

### 2. Grid Stabilization Services

#### Technical Requirements
- **Frequency Response**: <1 second using battery
- **Voltage Support**: Reactive power from inverters
- **Black Start**: Capability to restart grid sections
- **Island Operation**: Maintain local loads during outages
- **Seamless Transfer**: Smooth transition between grid/island modes

#### Grid Stabilization Specifications
```python
class GridStabilizationSpec:
    FREQUENCY_RESPONSE_TIME = 1.0  # seconds
    VOLTAGE_RESPONSE_TIME = 0.1  # seconds
    BLACK_START_CAPACITY = 0.05  # 5% of rated power
    ISLAND_DURATION_MAX = 4.0  # hours
    TRANSFER_TIME_MAX = 0.1  # 100ms seamless transfer
    
    STABILIZATION_MODES = {
        'frequency_support': {'priority': 1, 'capacity': 0.15},
        'voltage_support': {'priority': 2, 'capacity': 0.10},
        'black_start': {'priority': 3, 'capacity': 0.05},
        'island_operation': {'priority': 4, 'capacity': 1.0}
    }
```

## Grid Services Coordination

### Service Prioritization Matrix
```python
SERVICE_PRIORITY_MATRIX = {
    # Priority 1: Emergency/Safety Services
    'emergency_shutdown': 1,
    'fault_response': 2,
    'black_start': 3,
    
    # Priority 2: Grid Stability Services
    'frequency_regulation': 4,
    'voltage_support': 5,
    'synthetic_inertia': 6,
    
    # Priority 3: Economic Services
    'energy_arbitrage': 7,
    'peak_shaving': 8,
    'demand_response': 9,
    
    # Priority 4: Optimization Services
    'market_optimization': 10,
    'efficiency_optimization': 11
}
```

### Resource Allocation Algorithm
- **Hierarchical Priority**: Emergency services override all others
- **Resource Sharing**: Multiple services can share resources if compatible
- **Dynamic Reallocation**: Real-time reallocation based on grid conditions
- **Revenue Optimization**: Maximize revenue within operational constraints

## Economic Optimization

### Market Participation
- **Energy Markets**: Day-ahead and real-time energy markets
- **Ancillary Services**: Frequency regulation, spinning reserve, voltage support
- **Capacity Markets**: Long-term capacity commitment
- **Demand Response**: Economic demand response programs

### Bidding Strategy
```python
class BiddingStrategy:
    MARKET_TYPES = [
        'day_ahead_energy',
        'real_time_energy',
        'frequency_regulation',
        'spinning_reserve',
        'voltage_support',
        'capacity'
    ]
    
    BIDDING_PARAMETERS = {
        'price_threshold': 50.0,  # $/MWh minimum price
        'quantity_increment': 1.0,  # MW bid increments
        'risk_tolerance': 0.05,  # 5% risk tolerance
        'profit_margin': 0.15  # 15% profit margin
    }
```

## Performance Requirements

### Response Time Requirements
| Service | Response Time | Accuracy | Availability |
|---------|--------------|----------|--------------|
| Primary Frequency Control | <2 seconds | ±1% | >99% |
| Secondary Frequency Control | <5 minutes | ±1% | >98% |
| Synthetic Inertia | <500ms | ±2% | >99% |
| Reactive Power Management | <1 second | ±2% | >98% |
| Dynamic Voltage Support | <100ms | ±1% | >99% |
| Load Curtailment | <5 minutes | ±2% | >95% |
| Battery Response | <20ms | ±1% | >99% |

### Economic Performance Targets
- **Revenue Optimization**: Maximize annual revenue from grid services
- **Market Participation**: >95% bid acceptance rate
- **Price Forecasting**: <10% MAPE for day-ahead prices
- **Operational Efficiency**: >98% equipment availability

## Interface Specifications

### Grid Connection Interface
- **Communication Protocol**: IEC 61850 or DNP3
- **Data Update Rate**: 100ms for critical measurements
- **Security**: Encrypted communication with authentication
- **Redundancy**: Dual communication paths

### Market Interface
- **Market Protocols**: OASIS standards for market communication
- **Bid Submission**: Real-time bid submission capability
- **Settlement**: Automated settlement data processing
- **Reporting**: Real-time and historical performance reporting

### Control Interface
- **SCADA Integration**: Interface with utility SCADA systems
- **Remote Control**: Secure remote control capability
- **Monitoring**: Real-time performance monitoring
- **Alarms**: Critical alarm notification system

## Testing Requirements

### Unit Testing
- Individual service controller testing
- Algorithm validation testing
- Performance requirement verification
- Error condition handling

### Integration Testing
- Multi-service coordination testing
- Grid interface testing
- Market interface testing
- Economic optimization testing

### Performance Testing
- Response time validation
- Accuracy requirement testing
- Load testing under maximum capacity
- Stress testing under adverse conditions

### Validation Testing
- Real-world scenario simulation
- Grid code compliance verification
- Market rule compliance testing
- Safety system validation

### Test Coverage Requirements
- **Code Coverage**: >95% line coverage
- **Functional Coverage**: 100% requirement coverage
- **Performance Coverage**: All performance requirements tested
- **Integration Coverage**: All interfaces tested

## Compliance and Standards

### Grid Codes
- IEEE 1547 (Interconnection Standards)
- NERC Standards (Reliability Standards)
- Local utility interconnection requirements
- Regional transmission organization requirements

### Market Rules
- FERC Order 841 (Energy Storage Participation)
- ISO/RTO market rules compliance
- Demand response program requirements
- Ancillary service market rules

### Safety Standards
- IEEE C37.90 (Relay Protection)
- UL 1741 (Inverter Safety)
- IEC 61850 (Communication Protocols)
- NEMA Standards (Electrical Equipment)

## Documentation Requirements

### Technical Documentation
- System architecture documentation
- Interface specification documents
- Operating procedures
- Maintenance procedures

### Compliance Documentation
- Grid code compliance reports
- Market rule compliance documentation
- Safety certification documents
- Performance test reports

### User Documentation
- Operations manual
- Troubleshooting guide
- Performance optimization guide
- Training materials

This technical specification provides the foundation for implementing Phase 7 Advanced Grid Services, ensuring that all requirements, interfaces, and performance criteria are clearly defined and testable.
