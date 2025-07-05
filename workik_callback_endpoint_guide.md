# Workik Interactive Debugging Guide: Callback and Endpoint Integration

## Context Setup for Workik

```python
# Workik Context for KPP Simulator Callback/Endpoint Analysis
CONTEXT = {
    "project": "KPP Simulator - Callback and Endpoint Integration Analysis",
    "frameworks": {
        "web": ["Flask", "Flask-SocketIO", "Dash"],
        "simulation": ["Custom Physics Engine", "Real-time Simulation"],
        "async": ["Eventlet", "Threading"]
    },
    "architecture": {
        "frontend": "Dash web interface with real-time updates",
        "backend": "Flask REST API with WebSocket streaming",
        "simulation": "Real-time physics simulation engine",
        "callbacks": "Event-driven callback system"
    },
    "key_concepts": {
        "callbacks": "Event handlers, route handlers, simulation step functions",
        "endpoints": "REST API endpoints, WebSocket events, data streaming",
        "integration": "Frontend-backend communication, real-time data flow",
        "mapping": "Callback-to-endpoint relationships, data flow patterns"
    },
    "critical_functions": [
        "app.py route handlers",
        "simulation.engine.SimulationEngine.step()",
        "WebSocket event handlers",
        "Dash callback functions"
    ],
    "debugging_focus": [
        "Callback execution flow",
        "Endpoint response patterns",
        "Data transformation between layers",
        "Error propagation across callbacks"
    ]
}
```

## Interactive Debugging Workflow

### Step 1: Callback Mapping Analysis

**Target**: Map all callbacks to their corresponding endpoints and data flows

**Breakpoints to Set**:
```python
# Flask route handlers
breakpoint_1 = "app.py:start_simulation() - Route entry point"
breakpoint_2 = "app.py:data_live() - Real-time data streaming"
breakpoint_3 = "app.py:step_simulation() - Single step execution"

# Simulation engine callbacks
breakpoint_4 = "simulation/engine.py:step() - Main simulation step"
breakpoint_5 = "simulation/engine.py:log_state() - State logging callback"
breakpoint_6 = "simulation/engine.py:trigger_pulse() - Event trigger"

# WebSocket handlers
breakpoint_7 = "app.py:stream() - WebSocket data streaming"
breakpoint_8 = "app.py:data_live() - Live data endpoint"
```

**Variables to Monitor**:
```python
critical_variables = {
    "request_data": "Incoming request data and parameters",
    "simulation_state": "Current simulation state object",
    "response_data": "Outgoing response data structure",
    "callback_chain": "Sequence of callbacks being executed",
    "error_state": "Error information and propagation"
}
```

### Step 2: Endpoint Integration Analysis

**Target**: Analyze endpoint integration patterns and data flow

**Integration Points to Examine**:
```python
integration_points = {
    "frontend_backend": "Dash callback → Flask endpoint communication",
    "simulation_web": "Simulation engine → Web interface data flow",
    "realtime_streaming": "WebSocket → Frontend real-time updates",
    "error_handling": "Error propagation across layers"
}
```

**Expected Workik AI Suggestions**:
```python
ai_suggestions = [
    "Add request validation middleware for all endpoints",
    "Implement consistent error response format across endpoints",
    "Add performance monitoring for callback execution times",
    "Create callback dependency graph for better debugging",
    "Implement circuit breakers for critical simulation callbacks",
    "Add request/response logging for endpoint debugging"
]
```

## Debugging Scenarios

### Scenario 1: Callback Chain Analysis

**Problem**: Understanding the complete callback execution chain from frontend to simulation

**Debugging Steps**:
1. **Set breakpoint** at `app.py:start_simulation()`
2. **Trace execution** through the following chain:
   ```
   Frontend → Flask Route → Engine Initialization → Simulation Start → State Updates
   ```
3. **Monitor variables** at each step:
   - Request parameters
   - Engine state changes
   - Response data structure
   - Error conditions

**Workik AI Expected Help**:
- Identify missing error handling in callback chain
- Suggest performance optimizations for long callback chains
- Recommend breaking complex callbacks into smaller functions
- Detect potential race conditions in concurrent callbacks

### Scenario 2: Endpoint Response Mapping

**Problem**: Mapping endpoint responses to frontend expectations

**Debugging Steps**:
1. **Set breakpoint** at `app.py:data_live()`
2. **Examine response structure**:
   ```python
   response_structure = {
       "status": "success/error",
       "data": "simulation_data",
       "timestamp": "current_time",
       "performance": "execution_metrics"
   }
   ```
3. **Trace data transformation** from simulation to frontend format

**Workik AI Expected Help**:
- Identify data format mismatches between layers
- Suggest response structure improvements
- Recommend caching strategies for expensive data transformations
- Detect unnecessary data serialization overhead

### Scenario 3: Real-time Data Flow

**Problem**: Debugging real-time data streaming from simulation to frontend

**Debugging Steps**:
1. **Set breakpoint** at `app.py:stream()` (WebSocket handler)
2. **Monitor data flow**:
   ```
   Simulation Step → State Collection → Data Serialization → WebSocket Send → Frontend Update
   ```
3. **Check for bottlenecks** in real-time data pipeline

**Workik AI Expected Help**:
- Identify performance bottlenecks in real-time data flow
- Suggest data compression for large state objects
- Recommend batching strategies for frequent updates
- Detect memory leaks in streaming data

### Scenario 4: Error Propagation Analysis

**Problem**: Understanding how errors propagate through callback chains

**Debugging Steps**:
1. **Set breakpoint** at error handling locations
2. **Trace error flow**:
   ```
   Simulation Error → Engine Error Handler → Flask Error Response → Frontend Error Display
   ```
3. **Monitor error context** and recovery mechanisms

**Workik AI Expected Help**:
- Identify missing error handling in callback chains
- Suggest error recovery strategies
- Recommend error logging improvements
- Detect error masking or loss of error context

## Workik AI Integration Commands

### For Callback Analysis
```python
# Analyze callback performance
workik.analyze_performance("simulation.engine.SimulationEngine.step")

# Map callback dependencies
workik.map_dependencies("app.py:start_simulation")

# Check for callback issues
workik.check_callbacks([
    "app.py:start_simulation",
    "app.py:data_live", 
    "simulation.engine.SimulationEngine.step"
])
```

### For Endpoint Analysis
```python
# Analyze endpoint patterns
workik.analyze_endpoints([
    "/start", "/stop", "/step", "/data/live"
])

# Check endpoint integration
workik.check_integration("frontend_backend")

# Validate response formats
workik.validate_responses("app.py:data_live")
```

### For Real-time Debugging
```python
# Monitor real-time data flow
workik.monitor_dataflow("simulation.engine.SimulationEngine.step")

# Check WebSocket performance
workik.analyze_websocket("app.py:stream")

# Debug callback timing
workik.debug_timing("app.py:data_live")
```

## Expected Workik AI Insights

### Performance Insights
```python
expected_insights = {
    "callback_performance": [
        "Simulation step callback takes 150ms on average",
        "State logging callback adds 20ms overhead",
        "WebSocket data serialization is bottleneck"
    ],
    "endpoint_performance": [
        "/data/live endpoint responds in 50ms average",
        "Large state objects cause slow serialization",
        "Missing caching for static data"
    ],
    "integration_issues": [
        "Frontend expects different data format than backend provides",
        "Error responses lack consistent structure",
        "Missing request validation in 3 endpoints"
    ]
}
```

### Optimization Recommendations
```python
optimization_recommendations = [
    "Implement state compression to reduce WebSocket payload size",
    "Add response caching for static simulation parameters",
    "Break large callback functions into smaller, focused functions",
    "Add request rate limiting to prevent simulation overload",
    "Implement circuit breakers for critical simulation operations",
    "Add comprehensive error handling with proper error codes"
]
```

## Integration Testing with Workik

### Test Callback Integration
```python
# Test callback chain execution
workik.test_callback_chain([
    "frontend_request",
    "flask_route_handler", 
    "engine_initialization",
    "simulation_execution",
    "response_generation"
])

# Test error propagation
workik.test_error_propagation("simulation_error")

# Test performance under load
workik.test_performance("concurrent_requests")
```

### Test Endpoint Mapping
```python
# Test endpoint response mapping
workik.test_endpoint_mapping("/data/live")

# Test real-time data flow
workik.test_realtime_flow("websocket_streaming")

# Test error handling
workik.test_error_handling("invalid_requests")
```

## Debugging Checklist

### Callback Analysis
- [ ] Map all callback functions and their purposes
- [ ] Identify callback execution chains
- [ ] Check for callback performance bottlenecks
- [ ] Verify error handling in callbacks
- [ ] Test callback concurrency and thread safety

### Endpoint Analysis
- [ ] Map all endpoints and their HTTP methods
- [ ] Validate request/response data formats
- [ ] Check endpoint error handling
- [ ] Test endpoint performance under load
- [ ] Verify endpoint security and validation

### Integration Analysis
- [ ] Trace data flow between frontend and backend
- [ ] Check real-time data streaming performance
- [ ] Validate error propagation across layers
- [ ] Test integration under various error conditions
- [ ] Verify data consistency across layers

## Workik AI Commands for Quick Analysis

```python
# Quick callback overview
workik.overview("callbacks")

# Quick endpoint overview  
workik.overview("endpoints")

# Quick integration overview
workik.overview("integration")

# Find performance issues
workik.find_issues("performance")

# Find integration issues
workik.find_issues("integration")

# Generate optimization report
workik.generate_report("callback_endpoint_optimization")
```

This Workik guide provides a comprehensive framework for debugging callback and endpoint integration issues in the KPP simulator, leveraging AI assistance for deeper analysis and optimization recommendations. 