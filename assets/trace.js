// assets/trace.js
// KPP Simulator - Client-side Observability & Tracing System
// Provides DevTools-friendly logging of all HTTP requests and UI interactions

(function () {
  'use strict';

  /** Generate or reuse page-session trace root */
  const rootTrace = crypto.randomUUID();
  const sessionStart = Date.now();

  console.info(`[TRACE] 🔍 KPP Observability System initialized with root trace: ${rootTrace}`);

  /** Inject X-Trace-ID into every request */
  function injectTraceID(headers = {}) {
    const traceId = `${rootTrace}-${Date.now()}`;
    const enhancedHeaders = { ...headers, 'X-Trace-ID': traceId };
    return enhancedHeaders;
  }

  /** Enhanced logging with consistent formatting */
  function logWithTrace(type, data) {
    const timestamp = new Date().toISOString();
    const elapsed = Date.now() - sessionStart;
    console.debug(`[${type}] ${timestamp} (+${elapsed}ms)`, data);
  }

  /** Patch fetch for comprehensive request logging */
  const _fetch = window.fetch;
  window.fetch = function (url, opts = {}) {
    const startTime = performance.now();
    
    // Inject trace ID
    opts.headers = injectTraceID(opts.headers || {});
    
    // Log request details
    logWithTrace('FETCH', {
      method: opts.method || 'GET',
      url: url,
      headers: opts.headers,
      body: opts.body ? (typeof opts.body === 'string' ? opts.body : '[Binary Data]') : null,
      trace_id: opts.headers['X-Trace-ID']
    });
    
    // Execute request and log response
    return _fetch(url, opts).then(response => {
      const endTime = performance.now();
      const duration = endTime - startTime;
      
      logWithTrace('FETCH_RESPONSE', {
        url: url,
        status: response.status,
        statusText: response.statusText,
        duration_ms: Math.round(duration),
        trace_id: opts.headers['X-Trace-ID'],
        headers: Object.fromEntries(response.headers.entries())
      });
      
      return response;
    }).catch(error => {
      const endTime = performance.now();
      const duration = endTime - startTime;
      
      logWithTrace('FETCH_ERROR', {
        url: url,
        error: error.message,
        duration_ms: Math.round(duration),
        trace_id: opts.headers['X-Trace-ID']
      });
      
      throw error;
    });
  };

  /** Patch XMLHttpRequest for comprehensive XHR logging */
  const _send = XMLHttpRequest.prototype.send;
  const _open = XMLHttpRequest.prototype.open;
  
  XMLHttpRequest.prototype.open = function(method, url, ...args) {
    this._method = method;
    this._url = url;
    this._startTime = performance.now();
    return _open.call(this, method, url, ...args);
  };

  XMLHttpRequest.prototype.send = function (body) {
    const traceId = `${rootTrace}-${Date.now()}`;
    this.setRequestHeader('X-Trace-ID', traceId);
    
    // Log request
    logWithTrace('XHR', {
      method: this._method,
      url: this._url,
      body: body ? (typeof body === 'string' ? body : '[Binary Data]') : null,
      trace_id: traceId
    });
    
    // Add response logging
    const originalOnReadyStateChange = this.onreadystatechange;
    this.onreadystatechange = function() {
      if (this.readyState === 4) {
        const endTime = performance.now();
        const duration = endTime - this._startTime;
        
        logWithTrace('XHR_RESPONSE', {
          url: this._url,
          status: this.status,
          statusText: this.statusText,
          duration_ms: Math.round(duration),
          trace_id: traceId,
          response_length: this.responseText ? this.responseText.length : 0
        });
      }
      
      if (originalOnReadyStateChange) {
        originalOnReadyStateChange.call(this);
      }
    };
    
    return _send.call(this, body);
  };

  /** Comprehensive UI event logging */
  const uiEvents = ['click', 'input', 'change', 'submit', 'keydown', 'focus', 'blur'];
  
  uiEvents.forEach(eventType => {
    document.addEventListener(eventType, function(e) {
      const target = e.target;
      const eventData = {
        type: eventType,
        target: {
          tagName: target.tagName,
          id: target.id || null,
          className: target.className || null,
          value: target.value || null,
          innerText: target.innerText ? target.innerText.substring(0, 100) : null
        },
        timestamp: Date.now(),
        trace_context: rootTrace
      };
      
      // Add specific event data
      if (eventType === 'keydown') {
        eventData.key = e.key;
        eventData.code = e.code;
      }
      
      if (eventType === 'click') {
        eventData.coordinates = { x: e.clientX, y: e.clientY };
      }
      
      logWithTrace('UI', eventData);
    }, true);
  });

  /** WebSocket monitoring */
  const originalWebSocket = window.WebSocket;
  window.WebSocket = function(url, protocols) {
    const ws = new originalWebSocket(url, protocols);
    const wsTraceId = `${rootTrace}-ws-${Date.now()}`;
    
    logWithTrace('WS_CONNECT', {
      url: url,
      protocols: protocols,
      trace_id: wsTraceId
    });
    
    const originalSend = ws.send;
    ws.send = function(data) {
      logWithTrace('WS_SEND', {
        url: url,
        data: typeof data === 'string' ? data : '[Binary Data]',
        trace_id: wsTraceId
      });
      return originalSend.call(this, data);
    };
    
    ws.addEventListener('message', function(event) {
      let messageData = event.data;
      let parsedData = null;
      
      try {
        parsedData = JSON.parse(messageData);
      } catch (e) {
        // Data is not JSON
      }
      
      logWithTrace('WS_MESSAGE', {
        url: url,
        data: parsedData || messageData,
        trace_id: wsTraceId,
        message_trace_id: parsedData?.trace_id || null
      });
    });
    
    ws.addEventListener('close', function(event) {
      logWithTrace('WS_CLOSE', {
        url: url,
        code: event.code,
        reason: event.reason,
        trace_id: wsTraceId
      });
    });
    
    ws.addEventListener('error', function(event) {
      logWithTrace('WS_ERROR', {
        url: url,
        error: event.error || 'WebSocket error',
        trace_id: wsTraceId
      });
    });
    
    return ws;
  };

  /** Trace ID accessor for debugging */
  window.KPP_TRACE = {
    getRootTrace: () => rootTrace,
    getNewTraceId: () => `${rootTrace}-${Date.now()}`,
    sessionStart: sessionStart,
    version: '1.0.0'
  };

  /** Page lifecycle logging */
  window.addEventListener('load', function() {
    logWithTrace('PAGE', {
      event: 'load',
      url: window.location.href,
      trace_id: rootTrace
    });
  });

  window.addEventListener('beforeunload', function() {
    logWithTrace('PAGE', {
      event: 'beforeunload',
      url: window.location.href,
      trace_id: rootTrace,
      session_duration_ms: Date.now() - sessionStart
    });
  });

  console.info(`[TRACE] ✅ KPP Client-side observability system ready. Use window.KPP_TRACE for debugging.`);
})(); 