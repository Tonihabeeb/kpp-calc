/**
 * Enhanced Real-Time Data Manager for KPP Simulator
 * Stage 4: Advanced SSE client with robust error handling, 
 * connection management, and data validation
 * 
 * Features:
 * - Automatic reconnection with exponential backoff
 * - Data validation and error recovery
 * - Connection quality monitoring
 * - Offline mode handling
 * - Performance metrics tracking
 */

class RealTimeDataManager {
    constructor() {
        // Connection state
        this.eventSource = null;
        this.isConnected = false;
        this.connectionAttempts = 0;
        this.maxRetries = 10;
        this.retryDelay = 1000; // Start with 1 second
        this.maxRetryDelay = 30000; // Max 30 seconds
        
        // Data processing
        this.lastDataTime = 0;
        this.dataBuffer = [];
        this.bufferSize = 100;
        this.updateRate = 50; // Minimum ms between updates
        
        // Performance monitoring
        this.metrics = {
            messagesReceived: 0,
            errorsEncountered: 0,
            reconnections: 0,
            avgLatency: 0,
            lastHeartbeat: 0
        };
        
        // Event callbacks
        this.callbacks = {
            onConnect: [],
            onDisconnect: [],
            onData: [],
            onError: [],
            onStatusChange: []
        };
        
        // Connection quality monitoring
        this.connectionQuality = 'unknown';
        this.latencyHistory = [];
        this.maxLatencyHistory = 20;
        
        console.log('🔌 RealTimeDataManager initialized');
    }
    
    /**
     * Start the SSE connection with automatic retry
     */
    connect() {
        if (this.eventSource && this.eventSource.readyState !== EventSource.CLOSED) {
            console.log('⚠️ Connection already exists');
            return;
        }
        
        this.connectionAttempts++;
        console.log(`🔌 Attempting SSE connection (attempt ${this.connectionAttempts})`);
        
        try {
            this.eventSource = new EventSource('/stream');
            this.setupEventHandlers();
            
        } catch (error) {
            console.error('❌ Failed to create EventSource:', error);
            this.handleConnectionError(error);
        }
    }
    
    /**
     * Setup SSE event handlers with comprehensive error handling
     */
    setupEventHandlers() {
        // Connection opened
        this.eventSource.onopen = (event) => {
            this.onConnectionOpen(event);
        };
        
        // Data received
        this.eventSource.onmessage = (event) => {
            this.onDataReceived(event);
        };
        
        // Connection error
        this.eventSource.onerror = (event) => {
            this.onConnectionError(event);
        };
    }
    
    /**
     * Handle successful connection
     */
    onConnectionOpen(event) {
        this.isConnected = true;
        this.connectionAttempts = 0;
        this.retryDelay = 1000; // Reset retry delay
        this.metrics.reconnections++;
        this.connectionQuality = 'good';
        
        console.log('✅ SSE connection established');
        this.updateConnectionStatus('connected');
        this.notifyCallbacks('onConnect', { event, timestamp: Date.now() });
        
        // Start connection monitoring
        this.startConnectionMonitoring();
    }
    
    /**
     * Handle incoming data with validation and processing
     */
    onDataReceived(event) {
        const receiveTime = Date.now();
        
        try {
            // Parse and validate data
            const rawData = JSON.parse(event.data);
            const validatedData = this.validateData(rawData);
            
            if (!validatedData) {
                throw new Error('Data validation failed');
            }
            
            // Update metrics
            this.metrics.messagesReceived++;
            this.updateLatencyMetrics(validatedData, receiveTime);
            
            // Handle heartbeat
            if (validatedData.heartbeat) {
                this.handleHeartbeat(validatedData);
                return;
            }
            
            // Throttle updates for performance
            if (receiveTime - this.lastDataTime < this.updateRate) {
                this.bufferData(validatedData);
                return;
            }
            
            this.lastDataTime = receiveTime;
            this.processData(validatedData);
            
        } catch (error) {
            console.error('❌ Error processing SSE data:', error);
            this.metrics.errorsEncountered++;
            this.notifyCallbacks('onError', { error, data: event.data });
        }
    }
    
    /**
     * Handle connection errors with retry logic
     */
    onConnectionError(event) {
        console.error('❌ SSE connection error:', event);
        
        this.isConnected = false;
        this.updateConnectionStatus('disconnected');
        this.notifyCallbacks('onDisconnect', { event, timestamp: Date.now() });
        
        // Close existing connection
        if (this.eventSource) {
            this.eventSource.close();
            this.eventSource = null;
        }
        
        // Attempt reconnection with exponential backoff
        this.scheduleReconnection();
    }
    
    /**
     * Schedule reconnection with exponential backoff
     */
    scheduleReconnection() {
        if (this.connectionAttempts >= this.maxRetries) {
            console.error('❌ Max reconnection attempts reached');
            this.updateConnectionStatus('failed');
            return;
        }
        
        const delay = Math.min(this.retryDelay * Math.pow(2, this.connectionAttempts - 1), this.maxRetryDelay);
        
        console.log(`⏰ Reconnecting in ${delay}ms (attempt ${this.connectionAttempts + 1}/${this.maxRetries})`);
        
        setTimeout(() => {
            this.connect();
        }, delay);
    }
    
    /**
     * Validate incoming data structure
     */
    validateData(data) {
        if (!data || typeof data !== 'object') {
            return null;
        }
        
        // Basic validation for expected fields
        const expectedFields = ['time', 'power', 'torque'];
        const hasRequiredFields = expectedFields.some(field => data.hasOwnProperty(field));
        
        if (!hasRequiredFields && !data.heartbeat) {
            console.warn('⚠️ Data missing required fields:', data);
            return null;
        }
        
        // Sanitize numeric values
        if (data.time !== undefined && (isNaN(data.time) || data.time < 0)) {
            data.time = 0;
        }
        
        if (data.power !== undefined && isNaN(data.power)) {
            data.power = 0;
        }
        
        if (data.torque !== undefined && isNaN(data.torque)) {
            data.torque = 0;
        }
        
        return data;
    }
    
    /**
     * Handle heartbeat messages for connection monitoring
     */
    handleHeartbeat(data) {
        this.metrics.lastHeartbeat = Date.now();
        console.log('💓 Heartbeat received');
        
        // Update connection quality based on heartbeat timing
        this.assessConnectionQuality();
    }
    
    /**
     * Process validated data and notify subscribers
     */
    processData(data) {
        // Add metadata
        data._metadata = {
            receiveTime: Date.now(),
            messageCount: this.metrics.messagesReceived,
            connectionQuality: this.connectionQuality
        };
        
        // Notify all data callbacks
        this.notifyCallbacks('onData', data);
        
        // Log data flow (debug mode)
        if (window.kppDebugMode) {
            console.log('📊 Data processed:', data);
        }
    }
    
    /**
     * Buffer data for batch processing during high update rates
     */
    bufferData(data) {
        this.dataBuffer.push(data);
        
        if (this.dataBuffer.length >= this.bufferSize) {
            // Process oldest data when buffer is full
            const oldestData = this.dataBuffer.shift();
            this.processData(oldestData);
        }
    }
    
    /**
     * Update latency metrics
     */
    updateLatencyMetrics(data, receiveTime) {
        if (data.timestamp) {
            const latency = receiveTime - (data.timestamp * 1000);
            this.latencyHistory.push(latency);
            
            if (this.latencyHistory.length > this.maxLatencyHistory) {
                this.latencyHistory.shift();
            }
            
            // Calculate average latency
            this.metrics.avgLatency = this.latencyHistory.reduce((a, b) => a + b, 0) / this.latencyHistory.length;
        }
    }
    
    /**
     * Assess connection quality based on metrics
     */
    assessConnectionQuality() {
        const now = Date.now();
        const timeSinceHeartbeat = now - this.metrics.lastHeartbeat;
        const avgLatency = this.metrics.avgLatency;
        
        if (timeSinceHeartbeat > 5000) {
            this.connectionQuality = 'poor';
        } else if (avgLatency > 1000) {
            this.connectionQuality = 'fair';
        } else {
            this.connectionQuality = 'good';
        }
        
        this.notifyCallbacks('onStatusChange', {
            quality: this.connectionQuality,
            latency: avgLatency,
            timeSinceHeartbeat
        });
    }
    
    /**
     * Start connection monitoring intervals
     */
    startConnectionMonitoring() {
        // Check connection quality every 5 seconds
        setInterval(() => {
            this.assessConnectionQuality();
        }, 5000);
        
        // Log metrics every 30 seconds
        setInterval(() => {
            this.logMetrics();
        }, 30000);
    }
    
    /**
     * Register callback for events
     */
    on(event, callback) {
        if (this.callbacks[event]) {
            this.callbacks[event].push(callback);
        }
    }
    
    /**
     * Remove callback
     */
    off(event, callback) {
        if (this.callbacks[event]) {
            const index = this.callbacks[event].indexOf(callback);
            if (index > -1) {
                this.callbacks[event].splice(index, 1);
            }
        }
    }
    
    /**
     * Notify all callbacks for an event
     */
    notifyCallbacks(event, data) {
        if (this.callbacks[event]) {
            this.callbacks[event].forEach(callback => {
                try {
                    callback(data);
                } catch (error) {
                    console.error(`❌ Error in ${event} callback:`, error);
                }
            });
        }
    }
    
    /**
     * Update connection status in UI
     */
    updateConnectionStatus(status) {
        const statusElement = document.getElementById('sseStatus');
        const containerElement = document.getElementById('connection-status');
        const qualityElement = document.getElementById('connectionQuality');
        
        if (statusElement && containerElement) {
            statusElement.textContent = status.charAt(0).toUpperCase() + status.slice(1);
            containerElement.className = `status-indicator ${status}`;
            
            // Add quality indicator
            if (qualityElement && this.connectionQuality !== 'unknown') {
                qualityElement.textContent = `(${this.connectionQuality})`;
                qualityElement.className = `quality-${this.connectionQuality}`;
            }
        }
    }
    
    /**
     * Force disconnect
     */
    disconnect() {
        if (this.eventSource) {
            this.eventSource.close();
            this.eventSource = null;
        }
        
        this.isConnected = false;
        this.updateConnectionStatus('disconnected');
        console.log('🔌 SSE connection manually closed');
    }
    
    /**
     * Get current metrics
     */
    getMetrics() {
        return {
            ...this.metrics,
            connectionQuality: this.connectionQuality,
            isConnected: this.isConnected,
            bufferSize: this.dataBuffer.length
        };
    }
    
    /**
     * Log comprehensive metrics
     */
    logMetrics() {
        const metrics = this.getMetrics();
        console.log('📊 RealTime Metrics:', metrics);
    }
    
    /**
     * Clear all buffered data
     */
    clearBuffer() {
        this.dataBuffer = [];
        console.log('🗑️ Data buffer cleared');
    }
    
    /**
     * Enable/disable debug mode
     */
    setDebugMode(enabled) {
        window.kppDebugMode = enabled;
        console.log(`🐛 Debug mode ${enabled ? 'enabled' : 'disabled'}`);
    }
}

// Create global instance
window.realTimeDataManager = new RealTimeDataManager();

console.log('✅ Enhanced Real-Time Data Manager loaded');
