# observability.py
"""
KPP Simulator - Backend Observability & Tracing System
Provides end-to-end trace-ID correlation for Flask/Dash applications
"""

import uuid
import logging
import time
import json
import functools
from typing import Dict, Any, Optional
from flask import g, request, current_app
from datetime import datetime
import threading
from collections import defaultdict, deque

# Trace header constant
TRACE_HEADER = "X-Trace-ID"

# Global trace storage for analytics
trace_storage = defaultdict(lambda: deque(maxlen=100))
trace_lock = threading.Lock()

class TraceContext:
    """Context manager for trace operations"""
    
    def __init__(self, trace_id: str, operation: str = "unknown"):
        self.trace_id = trace_id
        self.operation = operation
        self.start_time = time.time()
        self.metadata = {}
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time
        self.log_completion(duration, exc_type is not None)
    
    def add_metadata(self, key: str, value: Any):
        """Add metadata to the trace context"""
        self.metadata[key] = value
    
    def log_completion(self, duration: float, had_error: bool):
        """Log trace completion with timing and error info"""
        log_entry = {
            'trace_id': self.trace_id,
            'operation': self.operation,
            'duration_ms': round(duration * 1000, 2),
            'had_error': had_error,
            'timestamp': datetime.utcnow().isoformat(),
            'metadata': self.metadata
        }
        
        with trace_lock:
            trace_storage[self.trace_id].append(log_entry)
        
        logger = logging.getLogger("trace")
        if had_error:
            logger.error(f"Trace {self.trace_id} completed with error after {duration*1000:.2f}ms")
        else:
            logger.info(f"Trace {self.trace_id} completed successfully in {duration*1000:.2f}ms")

class ObservabilityLogger:
    """Enhanced logger with trace-ID context"""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.name = name
    
    def _log_with_trace(self, level: int, message: str, *args, **kwargs):
        """Log with trace-ID context if available"""
        trace_id = getattr(g, 'trace_id', 'NO-TRACE')
        
        # Format message with trace context
        formatted_message = f"[{trace_id}] {message}"
        
        # Add trace_id to extra context
        extra = kwargs.get('extra', {})
        extra['trace_id'] = trace_id
        kwargs['extra'] = extra
        
        self.logger.log(level, formatted_message, *args, **kwargs)
    
    def debug(self, message: str, *args, **kwargs):
        self._log_with_trace(logging.DEBUG, message, *args, **kwargs)
    
    def info(self, message: str, *args, **kwargs):
        self._log_with_trace(logging.INFO, message, *args, **kwargs)
    
    def warning(self, message: str, *args, **kwargs):
        self._log_with_trace(logging.WARNING, message, *args, **kwargs)
    
    def error(self, message: str, *args, **kwargs):
        self._log_with_trace(logging.ERROR, message, *args, **kwargs)
    
    def critical(self, message: str, *args, **kwargs):
        self._log_with_trace(logging.CRITICAL, message, *args, **kwargs)

def get_trace_logger(name: str) -> ObservabilityLogger:
    """Get a trace-aware logger instance"""
    return ObservabilityLogger(name)

def trace_operation(operation_name: str):
    """Decorator to trace function operations"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            trace_id = getattr(g, 'trace_id', str(uuid.uuid4()))
            
            with TraceContext(trace_id, operation_name) as trace_ctx:
                trace_ctx.add_metadata('function', func.__name__)
                trace_ctx.add_metadata('args_count', len(args))
                trace_ctx.add_metadata('kwargs_keys', list(kwargs.keys()))
                
                try:
                    result = func(*args, **kwargs)
                    trace_ctx.add_metadata('success', True)
                    return result
                except Exception as e:
                    trace_ctx.add_metadata('success', False)
                    trace_ctx.add_metadata('error', str(e))
                    raise
        
        return wrapper
    return decorator

def init_observability(app):
    """Initialize observability hooks for Flask/Dash application"""
    
    # Configure logging format to include trace IDs
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(trace_id)s | %(name)s | %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('kpp_traces.log')
        ]
    )
    
    # Create trace-aware logger
    trace_logger = get_trace_logger("observability")
    
    # Determine if this is a Dash app (has .server attribute) or Flask app
    flask_app = app.server if hasattr(app, 'server') else app
    
    @flask_app.before_request
    def _setup_trace_context():
        """Setup trace context for each request"""
        # Get or generate trace ID
        trace_id = request.headers.get(TRACE_HEADER)
        if not trace_id:
            trace_id = str(uuid.uuid4())
        
        # Store in Flask global context
        g.trace_id = trace_id
        g.request_start_time = time.time()
        
        # Log request start
        trace_logger.info(f"Request started: {request.method} {request.path}")
        trace_logger.debug(f"Request headers: {dict(request.headers)}")
        
        # Log request body for POST/PUT requests
        if request.method in ['POST', 'PUT', 'PATCH'] and request.content_length:
            if request.content_length < 1024:  # Only log small payloads
                try:
                    body = request.get_data(as_text=True)
                    trace_logger.debug(f"Request body: {body}")
                except:
                    trace_logger.debug("Request body: [Binary or unreadable data]")
        
        # Store trace context for analytics
        with trace_lock:
            trace_storage[trace_id].append({
                'event': 'request_start',
                'timestamp': datetime.utcnow().isoformat(),
                'method': request.method,
                'path': request.path,
                'user_agent': request.headers.get('User-Agent', 'Unknown'),
                'remote_addr': request.remote_addr
            })
    
    @flask_app.after_request
    def _finalize_trace_context(response):
        """Finalize trace context and inject trace ID into response"""
        trace_id = getattr(g, 'trace_id', 'UNKNOWN')
        start_time = getattr(g, 'request_start_time', time.time())
        
        # Calculate request duration
        duration = time.time() - start_time
        
        # Inject trace ID into response headers
        response.headers[TRACE_HEADER] = trace_id
        
        # Log response
        trace_logger.info(f"Request completed: {response.status_code} in {duration*1000:.2f}ms")
        
        # Store completion event
        with trace_lock:
            trace_storage[trace_id].append({
                'event': 'request_complete',
                'timestamp': datetime.utcnow().isoformat(),
                'status_code': response.status_code,
                'duration_ms': round(duration * 1000, 2),
                'response_size': len(response.get_data()) if response.get_data() else 0
            })
        
        return response
    
    @flask_app.errorhandler(Exception)
    def _handle_trace_errors(error):
        """Handle errors with trace context"""
        trace_id = getattr(g, 'trace_id', 'ERROR-NO-TRACE')
        trace_logger.error(f"Unhandled exception: {str(error)}")
        
        # Store error event
        with trace_lock:
            trace_storage[trace_id].append({
                'event': 'error',
                'timestamp': datetime.utcnow().isoformat(),
                'error_type': type(error).__name__,
                'error_message': str(error)
            })
        
        # Return error response with trace ID
        error_response = {
            'error': str(error),
            'trace_id': trace_id,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        return error_response, 500
    
    # Add trace analytics endpoints
    @flask_app.route('/observability/traces')
    def get_traces():
        """Get all trace data for analysis"""
        with trace_lock:
            # Convert deques to lists for JSON serialization
            all_traces = {trace_id: list(events) for trace_id, events in trace_storage.items()}
        
        return {
            'traces': all_traces,
            'total_traces': len(all_traces),
            'timestamp': datetime.utcnow().isoformat()
        }
    
    @flask_app.route('/observability/traces/<trace_id>')
    def get_trace(trace_id):
        """Get specific trace data"""
        with trace_lock:
            trace_data = list(trace_storage.get(trace_id, []))
        
        if not trace_data:
            return {'error': f'Trace {trace_id} not found'}, 404
        
        return {
            'trace_id': trace_id,
            'events': trace_data,
            'event_count': len(trace_data)
        }
    
    @flask_app.route('/observability/health')
    def observability_health():
        """Health check endpoint for observability system"""
        return {
            'status': 'healthy',
            'active_traces': len(trace_storage),
            'total_events': sum(len(events) for events in trace_storage.values()),
            'timestamp': datetime.utcnow().isoformat(),
            'version': '1.0.0'
        }
    
    # Use standard logging for initialization (no trace context available yet)
    logging.getLogger("observability").info("Observability system initialized successfully")

def get_current_trace_id() -> Optional[str]:
    """Get the current trace ID from Flask context"""
    return getattr(g, 'trace_id', None)

def create_child_trace(parent_trace_id: str, operation: str) -> str:
    """Create a child trace ID for sub-operations"""
    child_id = f"{parent_trace_id}-{operation}-{int(time.time() * 1000)}"
    return child_id

def log_simulation_tick(trace_id: str, tick_data: Dict[str, Any]):
    """Log simulation tick data with trace context"""
    with trace_lock:
        trace_storage[trace_id].append({
            'event': 'simulation_tick',
            'timestamp': datetime.utcnow().isoformat(),
            'tick_data': tick_data
        })

def log_callback_execution(trace_id: str, callback_name: str, inputs: Dict, outputs: Dict, duration: float):
    """Log Dash callback execution with trace context"""
    with trace_lock:
        trace_storage[trace_id].append({
            'event': 'dash_callback',
            'timestamp': datetime.utcnow().isoformat(),
            'callback_name': callback_name,
            'inputs': inputs,
            'outputs': outputs,
            'duration_ms': round(duration * 1000, 2)
        })

# Export commonly used functions
__all__ = [
    'init_observability',
    'get_trace_logger',
    'trace_operation',
    'get_current_trace_id',
    'create_child_trace',
    'log_simulation_tick',
    'log_callback_execution',
    'TraceContext',
    'TRACE_HEADER'
] 