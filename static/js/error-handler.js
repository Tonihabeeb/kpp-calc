/**
 * Enhanced Error Handler and Data Validator for KPP Simulator
 * Stage 4: Comprehensive error handling, data validation, and recovery
 * 
 * Features:
 * - Centralized error handling and logging
 * - Data validation and sanitization
 * - Automatic error recovery strategies
 * - User-friendly error messages
 * - Performance issue detection
 */

class ErrorHandler {
    constructor() {
        this.errorLog = [];
        this.maxLogSize = 100;
        this.errorCounts = {};
        this.suppressedErrors = new Set();
        
        // Error severity levels
        this.severity = {
            LOW: 'low',
            MEDIUM: 'medium',
            HIGH: 'high',
            CRITICAL: 'critical'
        };
        
        // Recovery strategies
        this.recoveryStrategies = {
            'connection_error': this.recoverConnection.bind(this),
            'data_validation_error': this.recoverDataValidation.bind(this),
            'ui_error': this.recoverUI.bind(this),
            'performance_error': this.recoverPerformance.bind(this)
        };
        
        console.log('🛡️ ErrorHandler initialized');
    }
    
    /**
     * Handle error with context and recovery
     */
    handleError(error, context = {}) {
        const errorInfo = {
            timestamp: Date.now(),
            message: error.message || error,
            stack: error.stack,
            context: context,
            severity: this.determineSeverity(error, context),
            type: this.determineErrorType(error, context)
        };
        
        // Log error
        this.logError(errorInfo);
        
        // Show user notification
        this.showUserNotification(errorInfo);
        
        // Attempt recovery
        this.attemptRecovery(errorInfo);
        
        return errorInfo;
    }
    
    /**
     * Determine error severity
     */
    determineSeverity(error, context) {
        // Critical errors that break core functionality
        if (context.component === 'sse' || context.component === 'backend') {
            return this.severity.CRITICAL;
        }
        
        // High severity for simulation or data errors
        if (context.component === 'simulation' || context.component === 'data') {
            return this.severity.HIGH;
        }
        
        // Medium for UI components
        if (context.component === 'ui' || context.component === 'charts') {
            return this.severity.MEDIUM;
        }
        
        // Low for non-critical features
        return this.severity.LOW;
    }
    
    /**
     * Determine error type for recovery strategy
     */
    determineErrorType(error, context) {
        if (context.component === 'sse' || error.message?.includes('connection')) {
            return 'connection_error';
        }
        
        if (context.component === 'data' || error.message?.includes('validation')) {
            return 'data_validation_error';
        }
        
        if (context.component === 'ui' || context.component === 'charts') {
            return 'ui_error';
        }
        
        if (error.message?.includes('performance') || context.performance) {
            return 'performance_error';
        }
        
        return 'general_error';
    }
    
    /**
     * Log error with deduplication
     */
    logError(errorInfo) {
        const errorKey = `${errorInfo.type}_${errorInfo.message}`;
        
        // Count error occurrences
        this.errorCounts[errorKey] = (this.errorCounts[errorKey] || 0) + 1;
        
        // Suppress frequent duplicate errors
        if (this.errorCounts[errorKey] > 5) {
            if (!this.suppressedErrors.has(errorKey)) {
                console.warn(`⚠️ Suppressing frequent error: ${errorKey}`);
                this.suppressedErrors.add(errorKey);
            }
            return;
        }
        
        // Add to error log
        this.errorLog.push(errorInfo);
        
        // Trim log if too large
        if (this.errorLog.length > this.maxLogSize) {
            this.errorLog.shift();
        }
        
        // Console logging based on severity
        const logMethod = this.getLogMethod(errorInfo.severity);
        logMethod(`❌ [${errorInfo.severity.toUpperCase()}] ${errorInfo.type}:`, errorInfo);
    }
    
    /**
     * Get appropriate console log method
     */
    getLogMethod(severity) {
        switch (severity) {
            case this.severity.CRITICAL:
                return console.error;
            case this.severity.HIGH:
                return console.error;
            case this.severity.MEDIUM:
                return console.warn;
            default:
                return console.log;
        }
    }
    
    /**
     * Show user-friendly error notification
     */
    showUserNotification(errorInfo) {
        // Only show high/critical errors to users
        if (errorInfo.severity === this.severity.LOW) {
            return;
        }
        
        const message = this.getUserFriendlyMessage(errorInfo);
        const notificationElement = this.getOrCreateNotificationElement();
        
        // Set notification content
        notificationElement.innerHTML = `
            <div class="error-notification ${errorInfo.severity}">
                <div class="error-icon">⚠️</div>
                <div class="error-content">
                    <div class="error-title">${this.getErrorTitle(errorInfo.type)}</div>
                    <div class="error-message">${message}</div>
                </div>
                <button class="error-close" onclick="this.parentElement.style.display='none'">×</button>
            </div>
        `;
        
        notificationElement.style.display = 'block';
        
        // Auto-hide after delay (except critical errors)
        if (errorInfo.severity !== this.severity.CRITICAL) {
            setTimeout(() => {
                notificationElement.style.display = 'none';
            }, 5000);
        }
    }
    
    /**
     * Get user-friendly error message
     */
    getUserFriendlyMessage(errorInfo) {
        const messages = {
            'connection_error': 'Connection to the server was lost. Attempting to reconnect...',
            'data_validation_error': 'Invalid data received from server. Using safe defaults.',
            'ui_error': 'A display issue occurred. The interface will recover automatically.',
            'performance_error': 'System performance is degraded. Reducing update frequency.',
            'general_error': 'An unexpected error occurred. Please refresh if issues persist.'
        };
        
        return messages[errorInfo.type] || messages['general_error'];
    }
    
    /**
     * Get error title
     */
    getErrorTitle(errorType) {
        const titles = {
            'connection_error': 'Connection Issue',
            'data_validation_error': 'Data Issue',
            'ui_error': 'Display Issue',
            'performance_error': 'Performance Issue',
            'general_error': 'System Issue'
        };
        
        return titles[errorType] || titles['general_error'];
    }
    
    /**
     * Get or create notification element
     */
    getOrCreateNotificationElement() {
        let element = document.getElementById('error-notifications');
        if (!element) {
            element = document.createElement('div');
            element.id = 'error-notifications';
            element.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                z-index: 10000;
                max-width: 400px;
                display: none;
            `;
            document.body.appendChild(element);
        }
        return element;
    }
    
    /**
     * Attempt error recovery
     */
    attemptRecovery(errorInfo) {
        const strategy = this.recoveryStrategies[errorInfo.type];
        if (strategy) {
            try {
                strategy(errorInfo);
            } catch (recoveryError) {
                console.error('❌ Recovery strategy failed:', recoveryError);
            }
        }
    }
    
    /**
     * Connection error recovery
     */
    recoverConnection(errorInfo) {
        console.log('🔄 Attempting connection recovery...');
        
        // Notify real-time manager to attempt reconnection
        if (window.realTimeDataManager) {
            window.realTimeDataManager.connect();
        }
        
        // Update UI to show reconnection status
        const statusElement = document.getElementById('sseStatus');
        if (statusElement) {
            statusElement.textContent = 'Reconnecting...';
        }
    }
    
    /**
     * Data validation error recovery
     */
    recoverDataValidation(errorInfo) {
        console.log('🔄 Attempting data validation recovery...');
        
        // Clear problematic data
        if (window.chartManager) {
            window.chartManager.clearInvalidData();
        }
        
        if (window.floaterTableManager) {
            window.floaterTableManager.resetToDefaults();
        }
    }
    
    /**
     * UI error recovery
     */
    recoverUI(errorInfo) {
        console.log('🔄 Attempting UI recovery...');
        
        // Reinitialize charts if they exist
        if (window.chartManager && errorInfo.context.component === 'charts') {
            setTimeout(() => {
                window.chartManager.reinitializeCharts();
            }, 1000);
        }
        
        // Reset floater table if needed
        if (window.floaterTableManager && errorInfo.context.component === 'floaterTable') {
            window.floaterTableManager.reset();
        }
    }
    
    /**
     * Performance error recovery
     */
    recoverPerformance(errorInfo) {
        console.log('🔄 Attempting performance recovery...');
        
        // Reduce update frequency
        if (window.realTimeDataManager) {
            window.realTimeDataManager.updateRate = Math.min(
                window.realTimeDataManager.updateRate * 2,
                500 // Max 500ms between updates
            );
        }
        
        // Simplify charts
        if (window.chartManager) {
            window.chartManager.enablePerformanceMode();
        }
    }
    
    /**
     * Get error statistics
     */
    getErrorStats() {
        const stats = {
            totalErrors: this.errorLog.length,
            errorsByType: {},
            errorsBySeverity: {},
            suppressedErrors: this.suppressedErrors.size,
            recentErrors: this.errorLog.slice(-10)
        };
        
        // Count by type and severity
        this.errorLog.forEach(error => {
            stats.errorsByType[error.type] = (stats.errorsByType[error.type] || 0) + 1;
            stats.errorsBySeverity[error.severity] = (stats.errorsBySeverity[error.severity] || 0) + 1;
        });
        
        return stats;
    }
    
    /**
     * Clear error log
     */
    clearErrorLog() {
        this.errorLog = [];
        this.errorCounts = {};
        this.suppressedErrors.clear();
        console.log('🗑️ Error log cleared');
    }
    
    /**
     * Export error log for debugging
     */
    exportErrorLog() {
        const data = {
            timestamp: Date.now(),
            errors: this.errorLog,
            stats: this.getErrorStats()
        };
        
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `kpp-error-log-${Date.now()}.json`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
        
        console.log('📁 Error log exported');
    }
}

/**
 * Data Validator for ensuring data integrity
 */
class DataValidator {
    constructor() {
        this.schemas = this.initializeSchemas();
        this.validationRules = this.initializeValidationRules();
        
        console.log('✅ DataValidator initialized');
    }
    
    /**
     * Initialize data schemas
     */
    initializeSchemas() {
        return {
            simulationData: {
                required: ['time', 'power', 'torque'],
                optional: ['efficiency', 'floaters', 'physics_status', 'system_status'],
                types: {
                    time: 'number',
                    power: 'number',
                    torque: 'number',
                    efficiency: 'number'
                }
            },
            floaterData: {
                required: ['id', 'position', 'velocity'],
                optional: ['force', 'temperature', 'pressure'],
                types: {
                    id: 'number',
                    position: 'object',
                    velocity: 'object',
                    force: 'object'
                }
            },
            physicsStatus: {
                required: ['h1_active', 'h2_active', 'h3_active'],
                types: {
                    h1_active: 'boolean',
                    h2_active: 'boolean',
                    h3_active: 'boolean'
                }
            }
        };
    }
    
    /**
     * Initialize validation rules
     */
    initializeValidationRules() {
        return {
            ranges: {
                time: { min: 0, max: Number.MAX_SAFE_INTEGER },
                power: { min: -1000, max: 10000 },
                torque: { min: -1000, max: 1000 },
                efficiency: { min: 0, max: 1 },
                temperature: { min: -100, max: 200 },
                pressure: { min: 0, max: 1000 }
            },
            arrays: {
                floaters: { maxLength: 1000 },
                positions: { dimensions: 3 },
                velocities: { dimensions: 3 }
            }
        };
    }
    
    /**
     * Validate simulation data
     */
    validateSimulationData(data) {
        if (!data || typeof data !== 'object') {
            return { valid: false, errors: ['Data is not an object'] };
        }
        
        const errors = [];
        const schema = this.schemas.simulationData;
        
        // Check required fields
        schema.required.forEach(field => {
            if (!(field in data)) {
                errors.push(`Missing required field: ${field}`);
            }
        });
        
        // Validate types and ranges
        Object.entries(schema.types).forEach(([field, expectedType]) => {
            if (field in data) {
                const value = data[field];
                
                if (typeof value !== expectedType) {
                    errors.push(`Field ${field} should be ${expectedType}, got ${typeof value}`);
                } else if (expectedType === 'number') {
                    const range = this.validationRules.ranges[field];
                    if (range && (value < range.min || value > range.max)) {
                        errors.push(`Field ${field} out of range: ${value} (expected ${range.min}-${range.max})`);
                    }
                }
            }
        });
        
        // Validate floaters array if present
        if (data.floaters && Array.isArray(data.floaters)) {
            const floaterErrors = this.validateFloaterArray(data.floaters);
            errors.push(...floaterErrors);
        }
        
        // Validate physics status if present
        if (data.physics_status) {
            const physicsErrors = this.validatePhysicsStatus(data.physics_status);
            errors.push(...physicsErrors);
        }
        
        return {
            valid: errors.length === 0,
            errors: errors,
            data: this.sanitizeData(data, schema)
        };
    }
    
    /**
     * Validate floater array
     */
    validateFloaterArray(floaters) {
        const errors = [];
        const maxLength = this.validationRules.arrays.floaters.maxLength;
        
        if (floaters.length > maxLength) {
            errors.push(`Too many floaters: ${floaters.length} (max ${maxLength})`);
            return errors;
        }
        
        floaters.forEach((floater, index) => {
            const floaterErrors = this.validateFloater(floater, index);
            errors.push(...floaterErrors);
        });
        
        return errors;
    }
    
    /**
     * Validate individual floater
     */
    validateFloater(floater, index) {
        const errors = [];
        const schema = this.schemas.floaterData;
        
        schema.required.forEach(field => {
            if (!(field in floater)) {
                errors.push(`Floater ${index}: Missing required field ${field}`);
            }
        });
        
        // Validate position and velocity vectors
        ['position', 'velocity'].forEach(vectorField => {
            if (floater[vectorField]) {
                if (!this.isValidVector(floater[vectorField])) {
                    errors.push(`Floater ${index}: Invalid ${vectorField} vector`);
                }
            }
        });
        
        return errors;
    }
    
    /**
     * Validate physics status
     */
    validatePhysicsStatus(physicsStatus) {
        const errors = [];
        const schema = this.schemas.physicsStatus;
        
        schema.required.forEach(field => {
            if (!(field in physicsStatus)) {
                errors.push(`Physics status: Missing required field ${field}`);
            } else if (typeof physicsStatus[field] !== 'boolean') {
                errors.push(`Physics status: Field ${field} should be boolean`);
            }
        });
        
        return errors;
    }
    
    /**
     * Check if value is a valid 3D vector
     */
    isValidVector(vector) {
        return vector && 
               typeof vector === 'object' && 
               'x' in vector && 'y' in vector && 'z' in vector &&
               typeof vector.x === 'number' && 
               typeof vector.y === 'number' && 
               typeof vector.z === 'number' &&
               !isNaN(vector.x) && !isNaN(vector.y) && !isNaN(vector.z);
    }
    
    /**
     * Sanitize data by applying safe defaults
     */
    sanitizeData(data, schema) {
        const sanitized = { ...data };
        
        // Apply safe defaults for invalid numbers
        Object.entries(schema.types).forEach(([field, type]) => {
            if (type === 'number' && field in sanitized) {
                if (isNaN(sanitized[field]) || !isFinite(sanitized[field])) {
                    sanitized[field] = 0;
                }
            }
        });
        
        return sanitized;
    }
    
    /**
     * Get validation summary
     */
    getValidationSummary() {
        return {
            schemas: Object.keys(this.schemas),
            rules: this.validationRules,
            version: '1.0.0'
        };
    }
}

// Create global instances
window.errorHandler = new ErrorHandler();
window.dataValidator = new DataValidator();

// Global error handler for unhandled errors
window.addEventListener('error', (event) => {
    window.errorHandler.handleError(event.error, {
        component: 'global',
        file: event.filename,
        line: event.lineno
    });
});

// Global promise rejection handler
window.addEventListener('unhandledrejection', (event) => {
    window.errorHandler.handleError(event.reason, {
        component: 'promise',
        type: 'unhandled_rejection'
    });
});

console.log('✅ Enhanced Error Handler and Data Validator loaded');
