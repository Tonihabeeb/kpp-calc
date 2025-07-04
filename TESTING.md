# KPP Simulator Observability Testing Guide

This document provides comprehensive testing procedures for the KPP Simulator's observability and debugging system.

## Overview

The observability system provides end-to-end trace correlation across:
- **Client-side actions** (UI events, HTTP requests)
- **Server-side processing** (Flask endpoints, Dash callbacks)
- **Real-time streaming** (WebSocket frames)

## Prerequisites

1. **Install test dependencies:**
   ```bash
   pip install pytest pytest-asyncio pytest-mock
   ```

2. **Start the KPP simulator services:**
   ```bash
   # Terminal 1: Flask backend
   python app.py
   
   # Terminal 2: WebSocket server
   python main.py
   
   # Terminal 3: Dash frontend
   python dash_app.py
   ```

## Testing Workflow

### 1. Unit Tests

Run the observability unit tests:
```bash
python -m pytest tests/test_observability.py -v
```

**Expected Output:**
```
test_trace_id_generation PASSED
test_child_trace_creation PASSED
test_trace_logger_creation PASSED
test_trace_operation_decorator PASSED
test_trace_context_manager PASSED
test_simulation_tick_logging PASSED
test_callback_execution_logging PASSED
test_trace_header_injection PASSED
test_trace_header_propagation PASSED
test_observability_endpoints PASSED
test_trace_storage_endpoints PASSED
test_dash_app_initialization PASSED
test_websocket_trace_injection PASSED
test_trace_id_uniqueness PASSED
test_trace_id_format PASSED
```

### 2. Integration Testing

#### A. Client-Side Tracing

1. **Open Chrome DevTools:**
   - Press F12 or right-click → Inspect
   - Go to Console tab
   - Clear console (Ctrl+L)

2. **Load the Dashboard:**
   - Navigate to `http://localhost:9102`
   - Verify initialization message appears:
   ```
   [TRACE] 🔍 KPP Observability System initialized with root trace: <uuid>
   [TRACE] ✅ KPP Client-side observability system ready
   ```

3. **Test UI Event Logging:**
   - Click various buttons (Start, Stop, etc.)
   - Verify console logs show:
   ```
   [UI] 2024-01-15T10:30:00.000Z (+150ms) {
     type: "click",
     target: { tagName: "BUTTON", id: "start-btn", ... },
     coordinates: { x: 150, y: 200 },
     trace_context: "<root-trace-id>"
   }
   ```

4. **Test HTTP Request Logging:**
   - Trigger any action that makes API calls
   - Verify console shows:
   ```
   [FETCH] 2024-01-15T10:30:01.000Z (+1000ms) {
     method: "POST",
     url: "http://localhost:9100/start",
     trace_id: "<trace-id>"
   }
   [FETCH_RESPONSE] 2024-01-15T10:30:01.050Z (+1050ms) {
     url: "http://localhost:9100/start",
     status: 200,
     duration_ms: 50,
     trace_id: "<trace-id>"
   }
   ```

#### B. Server-Side Tracing

1. **Check Flask Backend Logs:**
   ```bash
   # In Flask terminal, verify logs show trace IDs:
   [2024-01-15 10:30:01] INFO | <trace-id> | kpp_backend | Request started: POST /start
   [2024-01-15 10:30:01] INFO | <trace-id> | kpp_backend | Simulation started successfully
   [2024-01-15 10:30:01] INFO | <trace-id> | kpp_backend | Request completed: 200 in 45.23ms
   ```

2. **Test Trace Header Propagation:**
   ```bash
   curl -H "X-Trace-ID: test-trace-123" http://localhost:9100/status
   # Verify response includes: X-Trace-ID: test-trace-123
   ```

3. **Check Observability Endpoints:**
   ```bash
   # Health check
   curl http://localhost:9100/observability/health
   
   # Trace data
   curl http://localhost:9100/observability/traces
   ```

#### C. WebSocket Tracing

1. **Check WebSocket Server Logs:**
   ```bash
   # In WebSocket terminal, verify:
   [2024-01-15 10:30:00] INFO | WebSocket core initialized with session trace: <session-id>
   [2024-01-15 10:30:01] INFO | WebSocket connection established with trace <client-id>
   [2024-01-15 10:30:05] INFO | WebSocket tick 25: 1 active clients, power=65551.75W
   ```

2. **Inspect WebSocket Frames:**
   - Open Chrome DevTools → Network tab
   - Filter by "WS" (WebSocket)
   - Click on the WebSocket connection
   - Verify frames contain trace IDs:
   ```json
   {
     "tick": 1,
     "timestamp": 1705312200.123,
     "trace_id": "<tick-trace-id>",
     "client_trace_id": "<client-trace-id>",
     "data": {
       "kpp_simulation": {
         "power": 65551.75,
         "trace_id": "<fetch-trace-id>"
       }
     }
   }
   ```

### 3. End-to-End Trace Correlation

#### A. Complete User Journey Test

1. **Start a simulation:**
   - Click "Start Simulation" button
   - Note the trace ID from console logs

2. **Verify trace correlation:**
   ```bash
   # Search logs for the trace ID
   grep "<trace-id>" kpp_traces.log
   
   # Should show complete flow:
   # - UI click event
   # - HTTP request to /start
   # - Server processing
   # - WebSocket data updates
   ```

3. **Check trace analytics:**
   ```bash
   curl http://localhost:9100/observability/traces/<trace-id>
   ```

#### B. Error Scenario Testing

1. **Simulate network error:**
   - Stop the Flask backend
   - Try to start simulation
   - Verify error logging with trace IDs

2. **Check error handling:**
   ```bash
   # Verify error responses include trace IDs
   curl -X POST http://localhost:9100/start
   # Should return: {"error": "...", "trace_id": "<trace-id>"}
   ```

## Debugging with DevTools

### 1. Console Filtering

Use console filters to focus on specific trace types:
- `[UI]` - User interface events
- `[FETCH]` - HTTP requests
- `[XHR]` - XMLHttpRequest calls
- `[WS]` - WebSocket events
- `[PAGE]` - Page lifecycle events

### 2. Network Analysis

1. **HTTP Requests:**
   - Network tab → XHR filter
   - Check "X-Trace-ID" header in request/response
   - Verify timing information

2. **WebSocket Frames:**
   - Network tab → WS filter
   - Inspect frame payloads for trace IDs
   - Monitor frame timing and frequency

### 3. Performance Profiling

1. **Performance tab:**
   - Record during simulation
   - Look for trace ID correlation in timeline
   - Identify bottlenecks

2. **Memory tab:**
   - Monitor memory usage during long sessions
   - Check for memory leaks in trace storage

## Log Analysis

### 1. Trace Log File

The system creates `kpp_traces.log` with structured trace data:
```bash
# View recent traces
tail -f kpp_traces.log

# Search for specific trace
grep "trace-id-123" kpp_traces.log

# Count events by type
grep "event.*request_start" kpp_traces.log | wc -l
```

### 2. Log Format

Each log entry includes:
```
timestamp | level | trace_id | module | message
```

### 3. Trace Analytics

Access trace analytics via API:
```bash
# Get all traces
curl http://localhost:9100/observability/traces

# Get specific trace
curl http://localhost:9100/observability/traces/<trace-id>

# Health check
curl http://localhost:9100/observability/health
```

## Performance Testing

### 1. Load Testing

```bash
# Test with multiple concurrent users
ab -n 100 -c 10 http://localhost:9100/status

# Test WebSocket connections
# (Use WebSocket testing tools)
```

### 2. Memory Usage

Monitor memory usage during extended operation:
```bash
# Check Python process memory
ps aux | grep python

# Monitor log file size
ls -lh kpp_traces.log
```

## Troubleshooting

### Common Issues

1. **Missing trace IDs:**
   - Check if observability system is initialized
   - Verify client-side script is loaded
   - Check browser console for errors

2. **Log file not created:**
   - Check write permissions
   - Verify logging configuration
   - Check disk space

3. **WebSocket connection issues:**
   - Verify WebSocket server is running
   - Check CORS configuration
   - Monitor WebSocket server logs

### Debug Commands

```bash
# Check all services are running
netstat -tulpn | grep -E "(9100|9101|9102)"

# Check log files
tail -f kpp_traces.log
tail -f simulation.log

# Test observability endpoints
curl http://localhost:9100/observability/health
curl http://localhost:9101/

# Monitor system resources
htop
```

## Success Criteria

A successful observability implementation should demonstrate:

1. ✅ **Complete trace correlation** from UI click to server response
2. ✅ **WebSocket frame inspection** with trace IDs
3. ✅ **DevTools-friendly logging** with consistent formatting
4. ✅ **Error handling** with trace context
5. ✅ **Performance monitoring** with timing data
6. ✅ **Analytics endpoints** for trace analysis

## Next Steps

After successful testing:

1. **Production deployment** with appropriate log rotation
2. **Alerting setup** for error conditions
3. **Metrics dashboard** for operational monitoring
4. **Performance optimization** based on trace analysis 