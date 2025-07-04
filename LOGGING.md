# KPP Simulator Observability Logging Guide

This document explains the comprehensive logging system implemented for the KPP Simulator's observability and debugging capabilities.

## Overview

The observability system provides structured logging with trace-ID correlation across all components:
- **Client-side events** (browser console)
- **Server-side operations** (Flask/Dash)
- **Real-time streaming** (WebSocket)
- **Simulation engine** (physics calculations)

## Log Format

### 1. Server-Side Log Format

```
timestamp | level | trace_id | module | message
```

**Example:**
```
2024-01-15 10:30:01,123 | INFO | abc123-def456 | kpp_backend | Request started: POST /start
2024-01-15 10:30:01,168 | INFO | abc123-def456 | kpp_backend | Simulation started successfully
2024-01-15 10:30:01,168 | INFO | abc123-def456 | kpp_backend | Request completed: 200 in 45.23ms
```

### 2. Client-Side Log Format

```
[EVENT_TYPE] timestamp (+elapsed_ms) { event_data }
```

**Example:**
```
[UI] 2024-01-15T10:30:00.000Z (+150ms) {
  type: "click",
  target: { tagName: "BUTTON", id: "start-btn" },
  coordinates: { x: 150, y: 200 },
  trace_context: "abc123-def456"
}
```

### 3. WebSocket Log Format

```
timestamp | level | session_id | message
```

**Example:**
```
2024-01-15 10:30:00 | INFO | ws-session-789 | WebSocket core initialized with session trace: xyz789-abc123
2024-01-15 10:30:01 | INFO | ws-session-789 | WebSocket connection established with trace client-456
2024-01-15 10:30:05 | INFO | ws-session-789 | WebSocket tick 25: 1 active clients, power=65551.75W
```

## Log Files

### 1. Primary Log Files

| File | Purpose | Location | Rotation |
|------|---------|----------|----------|
| `kpp_traces.log` | Trace correlation data | Project root | 10MB, keep 5 |
| `simulation.log` | Simulation engine logs | Project root | 50MB, keep 3 |
| `console.log` | Browser console (client) | Browser DevTools | N/A |

### 2. Log File Structure

#### kpp_traces.log
Contains structured trace events in JSON format:
```json
{
  "trace_id": "abc123-def456",
  "operation": "start_simulation",
  "duration_ms": 45.23,
  "had_error": false,
  "timestamp": "2024-01-15T10:30:01.123Z",
  "metadata": {
    "function": "start_simulation",
    "args_count": 0,
    "success": true
  }
}
```

#### simulation.log
Contains simulation engine operational logs:
```
[2024-01-15 10:30:01] INFO in simulation.engine: Simulation started
[2024-01-15 10:30:01] INFO in simulation.engine: Tick completed: ω_chain=477.0
[2024-01-15 10:30:01] WARNING in simulation.engine: High torque detected: 251.71 Nm
```

## Trace ID System

### 1. Trace ID Format

```
root-session-id + operation + timestamp
```

**Examples:**
- `abc123-def456-start-1705312201123` (Start simulation)
- `abc123-def456-tick-25-1705312205000` (WebSocket tick 25)
- `abc123-def456-fetch-1705312201000` (Data fetch)

### 2. Trace ID Hierarchy

```
Root Session ID (page load)
├── UI Event (click)
├── HTTP Request (/start)
│   ├── Server Processing
│   └── Response
├── WebSocket Connection
│   ├── Tick 1
│   ├── Tick 2
│   └── ...
└── Page Unload
```

## Logging Levels

### 1. Server-Side Levels

| Level | Usage | Example |
|-------|-------|---------|
| `DEBUG` | Detailed debugging | Request headers, function parameters |
| `INFO` | General information | Request start/complete, simulation status |
| `WARNING` | Potential issues | High torque, low efficiency |
| `ERROR` | Error conditions | Exception handling, failed operations |
| `CRITICAL` | System failures | Engine crash, data corruption |

### 2. Client-Side Levels

| Level | Usage | Example |
|-------|-------|---------|
| `console.debug` | Detailed tracing | HTTP request details, UI events |
| `console.info` | System status | Initialization, page lifecycle |
| `console.warn` | Potential issues | Network errors, validation failures |
| `console.error` | Error conditions | Request failures, JavaScript errors |

## Log Analysis

### 1. Command Line Analysis

#### Search by Trace ID
```bash
# Find all events for a specific trace
grep "abc123-def456" kpp_traces.log

# Find trace completion events
grep "completed successfully" kpp_traces.log

# Find error events
grep "had_error.*true" kpp_traces.log
```

#### Performance Analysis
```bash
# Find slow operations (>100ms)
grep "duration_ms.*[1-9][0-9][0-9]" kpp_traces.log

# Count operations by type
grep "operation.*start_simulation" kpp_traces.log | wc -l

# Find WebSocket performance
grep "WebSocket tick.*active clients" simulation.log
```

#### Error Analysis
```bash
# Find all errors
grep "ERROR" simulation.log

# Find specific error types
grep "Exception in.*endpoint" simulation.log

# Find WebSocket errors
grep "WebSocket error" simulation.log
```

### 2. API-Based Analysis

#### Get All Traces
```bash
curl http://localhost:9100/observability/traces
```

#### Get Specific Trace
```bash
curl http://localhost:9100/observability/traces/abc123-def456
```

#### Health Check
```bash
curl http://localhost:9100/observability/health
```

### 3. Real-Time Monitoring

#### Tail Logs
```bash
# Monitor all traces
tail -f kpp_traces.log

# Monitor simulation
tail -f simulation.log

# Monitor specific trace
tail -f kpp_traces.log | grep "abc123-def456"
```

#### Filter by Time
```bash
# Recent events (last 5 minutes)
grep "$(date -d '5 minutes ago' '+%Y-%m-%d %H:%M')" kpp_traces.log

# Today's events
grep "$(date '+%Y-%m-%d')" kpp_traces.log
```

## Log Rotation

### 1. Automatic Rotation

The system implements automatic log rotation:

```python
# Log rotation configuration
handlers=[
    RotatingFileHandler(
        'kpp_traces.log',
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    ),
    RotatingFileHandler(
        'simulation.log',
        maxBytes=50*1024*1024,  # 50MB
        backupCount=3
    )
]
```

### 2. Manual Rotation

```bash
# Rotate logs manually
logrotate -f /etc/logrotate.d/kpp-simulator

# Archive old logs
tar -czf kpp_logs_$(date +%Y%m%d).tar.gz kpp_traces.log.* simulation.log.*
```

## Performance Considerations

### 1. Log Volume

**Typical log volumes:**
- **kpp_traces.log**: ~1MB/hour during active simulation
- **simulation.log**: ~5MB/hour during active simulation
- **Client console**: ~100KB/hour per user session

### 2. Performance Impact

**Minimal impact design:**
- Async logging for non-critical events
- Structured data to reduce parsing overhead
- Trace ID reuse to minimize string operations
- Configurable log levels for production

### 3. Storage Requirements

**Daily storage estimates:**
- **Development**: ~50MB/day
- **Testing**: ~200MB/day
- **Production**: ~500MB/day (with multiple users)

## Debugging Workflows

### 1. User Issue Investigation

```bash
# 1. Get user's trace ID from browser console
# 2. Search server logs
grep "user-trace-id" kpp_traces.log

# 3. Analyze complete flow
curl http://localhost:9100/observability/traces/user-trace-id

# 4. Check for errors
grep "user-trace-id.*error" kpp_traces.log
```

### 2. Performance Investigation

```bash
# 1. Find slow operations
grep "duration_ms.*[5-9][0-9][0-9]" kpp_traces.log

# 2. Analyze specific operation
grep "operation.*slow_operation" kpp_traces.log

# 3. Check WebSocket performance
grep "WebSocket tick.*duration" simulation.log
```

### 3. Error Investigation

```bash
# 1. Find recent errors
grep "ERROR.*$(date '+%Y-%m-%d')" simulation.log

# 2. Get error context
grep -A 5 -B 5 "specific_error" simulation.log

# 3. Check trace correlation
grep "error_trace_id" kpp_traces.log
```

## Production Deployment

### 1. Log Configuration

```python
# Production logging configuration
logging.basicConfig(
    level=logging.INFO,  # Reduce debug noise
    format="%(asctime)s | %(levelname)s | %(trace_id)s | %(name)s | %(message)s",
    handlers=[
        RotatingFileHandler('kpp_traces.log', maxBytes=10*1024*1024, backupCount=5),
        RotatingFileHandler('simulation.log', maxBytes=50*1024*1024, backupCount=3),
        logging.StreamHandler()  # Console output for monitoring
    ]
)
```

### 2. Monitoring Setup

```bash
# Set up log monitoring
tail -f kpp_traces.log | grep "ERROR\|CRITICAL" | while read line; do
    # Send alert
    echo "KPP Error: $line" | mail -s "KPP Alert" admin@example.com
done
```

### 3. Backup Strategy

```bash
# Daily log backup
0 2 * * * tar -czf /backup/kpp_logs_$(date +\%Y\%m\%d).tar.gz /path/to/logs/*.log
```

## Best Practices

### 1. Logging Guidelines

- **Use structured logging** with consistent format
- **Include trace IDs** in all log entries
- **Log at appropriate levels** (DEBUG for development, INFO for production)
- **Include context** for debugging (user actions, system state)
- **Avoid sensitive data** in logs (passwords, personal information)

### 2. Performance Guidelines

- **Use async logging** for non-critical events
- **Implement log rotation** to manage disk space
- **Monitor log volume** and adjust levels as needed
- **Use structured data** to enable automated analysis

### 3. Debugging Guidelines

- **Start with trace ID** from user report
- **Follow the complete flow** from UI to server
- **Check for error patterns** across multiple traces
- **Use API endpoints** for structured analysis
- **Monitor real-time** during active debugging

## Troubleshooting

### Common Issues

1. **Missing trace IDs:**
   - Check observability initialization
   - Verify client-side script loading
   - Check browser console for errors

2. **Log file not created:**
   - Check write permissions
   - Verify disk space
   - Check logging configuration

3. **High log volume:**
   - Adjust log levels
   - Implement filtering
   - Set up log rotation

4. **Performance impact:**
   - Use async logging
   - Reduce debug output
   - Implement sampling

### Debug Commands

```bash
# Check log file permissions
ls -la *.log

# Check disk space
df -h

# Check log file sizes
ls -lh *.log

# Monitor log writing
strace -e trace=write -p $(pgrep python)

# Check for log errors
grep "ERROR.*logging" simulation.log
``` 