/**
 * Enhanced Main Application Controller for KPP Simulator
 * Integrates all Stage 3 components: parameter management, charts, and tables
 * Coordinates with SSE streaming and backend API
 */

document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 Enhanced KPP Simulator UI Loading...');
    
    // Global application state
    const app = {
        isConnected: false,
        eventSource: null,
        managers: {},
        simulationRunning: false,
        lastUpdateTime: 0
    };
    
    // Initialize all managers
    initializeManagers();
    
    // Setup event listeners
    setupControlButtons();
    setupSSEConnection();
    
    // Setup connection monitoring
    setupConnectionMonitoring();
    
    console.log('✅ Enhanced KPP Simulator UI Loaded Successfully');
    
    /**
     * Initialize all management modules
     */
    function initializeManagers() {
        // Wait for managers to be available
        const checkManagers = setInterval(() => {
            if (window.parameterManager && window.chartManager && window.floaterTableManager) {
                app.managers.parameters = window.parameterManager;
                app.managers.charts = window.chartManager;
                app.managers.floaterTable = window.floaterTableManager;
                
                console.log('✅ All managers initialized and connected');
                clearInterval(checkManagers);
                
                // Initialize default state
                updatePhysicsStatusIndicators({
                    h1_active: false,
                    h2_active: false,
                    h3_active: false
                });
                
            }
        }, 100);
        
        // Timeout after 5 seconds
        setTimeout(() => {
            clearInterval(checkManagers);
            if (!app.managers.parameters) {
                console.error('❌ Failed to initialize managers within timeout');
            }
        }, 5000);
    }
    
    /**
     * Setup control button event listeners
     */
    function setupControlButtons() {
        // Simulation control buttons
        const buttons = {
            start: document.getElementById('startBtn'),
            pause: document.getElementById('pauseBtn'),
            stop: document.getElementById('stopBtn'),
            reset: document.getElementById('resetBtn'),
            step: document.getElementById('stepBtn'),
            pulse: document.getElementById('pulseBtn')
        };
        
        // Start simulation
        if (buttons.start) {
            buttons.start.addEventListener('click', () => {
                sendSimulationCommand('start');
                app.simulationRunning = true;
                updateButtonStates();
            });
        }
        
        // Pause simulation
        if (buttons.pause) {
            buttons.pause.addEventListener('click', () => {
                sendSimulationCommand('pause');
                app.simulationRunning = false;
                updateButtonStates();
            });
        }
        
        // Stop simulation
        if (buttons.stop) {
            buttons.stop.addEventListener('click', () => {
                sendSimulationCommand('stop');
                app.simulationRunning = false;
                updateButtonStates();
                clearAllData();
            });
        }
        
        // Reset simulation
        if (buttons.reset) {
            buttons.reset.addEventListener('click', () => {
                sendSimulationCommand('reset');
                app.simulationRunning = false;
                updateButtonStates();
                clearAllData();
            });
        }
        
        // Step simulation
        if (buttons.step) {
            buttons.step.addEventListener('click', () => {
                sendSimulationCommand('step');
            });
        }
        
        // Trigger pulse
        if (buttons.pulse) {
            buttons.pulse.addEventListener('click', () => {
                sendSimulationCommand('pulse');
            });
        }
        
        console.log('✅ Control buttons initialized');
    }
    
    /**
     * Send simulation commands to backend
     */
    async function sendSimulationCommand(command) {
        try {
            console.log(`📤 Sending command: ${command}`);
            
            const response = await fetch(`/${command}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            if (response.ok) {
                const result = await response.json();
                console.log(`✅ Command ${command} successful:`, result);
                
                // Handle specific command responses
                if (command === 'reset' || command === 'stop') {
                    clearAllData();
                }
            } else {
                console.error(`❌ Command ${command} failed:`, response.status);
            }
            
        } catch (error) {
            console.error(`❌ Error sending command ${command}:`, error);
        }
    }
    
    /**
     * Setup enhanced SSE connection with real-time data manager
     */
    function setupSSEConnection() {
        // Wait for enhanced managers to be available
        const checkEnhancedManagers = setInterval(() => {
            if (window.realTimeDataManager && window.errorHandler && window.dataValidator) {
                initializeEnhancedSSE();
                clearInterval(checkEnhancedManagers);
            }
        }, 100);
        
        // Timeout after 5 seconds
        setTimeout(() => {
            clearInterval(checkEnhancedManagers);
            if (!window.realTimeDataManager) {
                console.warn('⚠️ Enhanced SSE managers not available, falling back to basic SSE');
                setupBasicSSEConnection();
            }
        }, 5000);
    }
    
    /**
     * Initialize enhanced SSE with real-time data manager
     */
    function initializeEnhancedSSE() {
        console.log('🚀 Initializing enhanced SSE connection...');
        
        // Setup real-time data manager callbacks
        window.realTimeDataManager.on('onConnect', (data) => {
            app.isConnected = true;
            console.log('✅ Enhanced SSE connected');
        });
        
        window.realTimeDataManager.on('onDisconnect', (data) => {
            app.isConnected = false;
            console.log('❌ Enhanced SSE disconnected');
        });
        
        window.realTimeDataManager.on('onData', (data) => {
            handleEnhancedSimulationData(data);
        });
        
        window.realTimeDataManager.on('onError', (errorData) => {
            window.errorHandler.handleError(errorData.error, {
                component: 'sse',
                data: errorData.data
            });
        });
        
        window.realTimeDataManager.on('onStatusChange', (statusData) => {
            updateEnhancedConnectionStatus(statusData);
        });
        
        // Start the enhanced connection
        window.realTimeDataManager.connect();
    }
    
    /**
     * Handle enhanced simulation data with validation
     */
    function handleEnhancedSimulationData(data) {
        try {
            // Validate data using enhanced validator
            const validation = window.dataValidator.validateSimulationData(data);
            
            if (!validation.valid) {
                console.warn('⚠️ Data validation failed:', validation.errors);
                
                // Use sanitized data if available
                if (validation.data) {
                    data = validation.data;
                } else {
                    return; // Skip invalid data
                }
            }
            
            // Throttle updates to prevent UI overload
            const now = Date.now();
            if (now - app.lastUpdateTime < 50) {  // 20 FPS max
                return;
            }
            app.lastUpdateTime = now;
            
            // Update all UI components with error handling
            updateUIComponentsSafely(data);
            
        } catch (error) {
            window.errorHandler.handleError(error, {
                component: 'data_processing',
                data: data
            });
        }
    }
    
    /**
     * Update UI components with error handling
     */
    function updateUIComponentsSafely(data) {
        // Update charts with error handling
        try {
            if (app.managers.charts) {
                app.managers.charts.updateCharts(data);
            }
        } catch (error) {
            window.errorHandler.handleError(error, {
                component: 'charts',
                operation: 'update'
            });
        }
        
        // Update floater table with error handling
        try {
            if (app.managers.floaterTable) {
                app.managers.floaterTable.updateTable(data);
            }
        } catch (error) {
            window.errorHandler.handleError(error, {
                component: 'floaterTable',
                operation: 'update'
            });
        }
        
        // Update summary displays with error handling
        try {
            updateSummaryDisplays(data);
        } catch (error) {
            window.errorHandler.handleError(error, {
                component: 'summary',
                operation: 'update'
            });
        }
        
        // Update physics status with error handling
        try {
            if (data.physics_status) {
                updatePhysicsStatusIndicators(data.physics_status);
            }
        } catch (error) {
            window.errorHandler.handleError(error, {
                component: 'physics_status',
                operation: 'update'
            });
        }
        
        // Update system status with error handling
        try {
            if (data.system_status) {
                updateSystemStatus(data.system_status);
            }
        } catch (error) {
            window.errorHandler.handleError(error, {
                component: 'system_status',
                operation: 'update'
            });
        }
    }
    
    /**
     * Update enhanced connection status with quality metrics
     */
    function updateEnhancedConnectionStatus(statusData) {
        const statusElement = document.getElementById('sseStatus');
        const containerElement = document.getElementById('connection-status');
        const qualityElement = document.getElementById('connectionQuality');
        const latencyElement = document.getElementById('connectionLatency');
        
        if (statusElement && containerElement) {
            // Update basic status
            const connected = window.realTimeDataManager.isConnected;
            statusElement.textContent = connected ? 'Connected' : 'Disconnected';
            containerElement.className = `status-indicator ${connected ? 'connected' : 'disconnected'}`;
            
            // Update quality indicator
            if (qualityElement && statusData.quality) {
                qualityElement.textContent = `Quality: ${statusData.quality}`;
                qualityElement.className = `quality-${statusData.quality}`;
            }
            
            // Update latency
            if (latencyElement && statusData.latency) {
                latencyElement.textContent = `${Math.round(statusData.latency)}ms`;
            }
        }
    }
    
    /**
     * Fallback to basic SSE connection if enhanced version fails
     */
    function setupBasicSSEConnection() {
        connectSSE();
        
        // Setup automatic reconnection
        setInterval(() => {
            if (!app.isConnected && !app.eventSource) {
                console.log('🔄 Attempting SSE reconnection...');
                connectSSE();
            }
        }, 5000);
    }
    
    /**
     * Connect to SSE stream
     */
    function connectSSE() {
        if (app.eventSource) {
            app.eventSource.close();
        }
        
        try {
            app.eventSource = new EventSource('/stream');
            
            app.eventSource.onopen = function(event) {
                app.isConnected = true;
                updateConnectionStatus(true);
                console.log('✅ SSE connection established');
            };
            
            app.eventSource.onmessage = function(event) {
                try {
                    const data = JSON.parse(event.data);
                    handleSimulationData(data);
                } catch (error) {
                    console.error('❌ Error parsing SSE data:', error);
                }
            };
            
            app.eventSource.onerror = function(event) {
                console.error('❌ SSE connection error:', event);
                app.isConnected = false;
                updateConnectionStatus(false);
                
                // Close and cleanup
                if (app.eventSource) {
                    app.eventSource.close();
                    app.eventSource = null;
                }
            };
            
        } catch (error) {
            console.error('❌ Failed to create SSE connection:', error);
            app.isConnected = false;
            updateConnectionStatus(false);
        }
    }
    
    /**
     * Handle incoming simulation data
     */
    function handleSimulationData(data) {
        // Throttle updates to prevent UI overload
        const now = Date.now();
        if (now - app.lastUpdateTime < 50) {  // 20 FPS max
            return;
        }
        app.lastUpdateTime = now;
        
        // Update all UI components
        if (app.managers.charts) {
            app.managers.charts.updateCharts(data);
        }
        
        if (app.managers.floaterTable) {
            app.managers.floaterTable.updateTable(data);
        }
        
        // Update summary displays
        updateSummaryDisplays(data);
        
        // Update physics status
        if (data.physics_status) {
            updatePhysicsStatusIndicators(data.physics_status);
        }
        
        // Update system status
        if (data.system_status) {
            updateSystemStatus(data.system_status);
        }
    }
    
    /**
     * Update summary display elements
     */
    function updateSummaryDisplays(data) {
        const summaryElements = {
            'summaryTime': data.time,
            'summaryTorque': data.torque,
            'summaryPower': data.power,
            'summaryVelocity': data.average_velocity,
            'baseTorque': data.base_torque,
            'pulseTorque': data.pulse_torque,
            'pulseCount': data.pulse_count,
            'efficiency': data.efficiency
        };
        
        Object.entries(summaryElements).forEach(([elementId, value]) => {
            const element = document.getElementById(elementId);
            if (element && value !== undefined) {
                if (typeof value === 'number') {
                    element.textContent = value.toFixed(2);
                } else {
                    element.textContent = value;
                }
            }
        });
        
        // Update clutch status
        const clutchElement = document.getElementById('clutchStatus');
        if (clutchElement && data.system_status) {
            clutchElement.textContent = data.system_status.clutch_engaged ? 'Engaged' : 'Disengaged';
            clutchElement.style.color = data.system_status.clutch_engaged ? '#28a745' : '#6c757d';
        }
    }
    
    /**
     * Update physics status indicators
     */
    function updatePhysicsStatusIndicators(physicsStatus) {
        const indicators = [
            { id: 'h1', active: physicsStatus.h1_active, label: 'Nanobubbles' },
            { id: 'h2', active: physicsStatus.h2_active, label: 'Thermal' },
            { id: 'h3', active: physicsStatus.h3_active, label: 'Pulse Control' }
        ];
        
        indicators.forEach(indicator => {
            const light = document.getElementById(`${indicator.id}-light`);
            const value = document.getElementById(`${indicator.id}-value`);
            
            if (light && value) {
                if (indicator.active) {
                    light.classList.add('active');
                    light.classList.remove('inactive');
                    value.textContent = 'Active';
                    value.style.color = '#28a745';
                } else {
                    light.classList.remove('active');
                    light.classList.add('inactive');
                    value.textContent = 'Inactive';
                    value.style.color = '#6c757d';
                }
            }
        });
    }
    
    /**
     * Update system status displays
     */
    function updateSystemStatus(systemStatus) {
        // Update air pressure
        const pressureElement = document.getElementById('tankPressure');
        if (pressureElement && systemStatus.air_pressure !== undefined) {
            pressureElement.textContent = systemStatus.air_pressure.toFixed(2);
        }
        
        // Update other system parameters as available
        Object.entries(systemStatus).forEach(([key, value]) => {
            const element = document.getElementById(key);
            if (element && typeof value === 'number') {
                element.textContent = value.toFixed(2);
            }
        });
    }
    
    /**
     * Update connection status indicator
     */
    function updateConnectionStatus(connected) {
        const statusElement = document.getElementById('sseStatus');
        const containerElement = document.getElementById('connection-status');
        
        if (statusElement && containerElement) {
            if (connected) {
                statusElement.textContent = 'Connected';
                containerElement.className = 'status-indicator connected';
            } else {
                statusElement.textContent = 'Disconnected';
                containerElement.className = 'status-indicator disconnected';
            }
        }
    }
    
    /**
     * Update button states based on simulation status
     */
    function updateButtonStates() {
        const startBtn = document.getElementById('startBtn');
        const pauseBtn = document.getElementById('pauseBtn');
        const stopBtn = document.getElementById('stopBtn');
        
        if (startBtn && pauseBtn && stopBtn) {
            if (app.simulationRunning) {
                startBtn.disabled = true;
                pauseBtn.disabled = false;
                stopBtn.disabled = false;
            } else {
                startBtn.disabled = false;
                pauseBtn.disabled = true;
                stopBtn.disabled = true;
            }
        }
    }
    
    /**
     * Clear all data displays
     */
    function clearAllData() {
        if (app.managers.charts) {
            app.managers.charts.clearAllCharts();
        }
        
        if (app.managers.floaterTable) {
            app.managers.floaterTable.clearTable();
        }
        
        // Clear summary displays
        const summaryElements = [
            'summaryTime', 'summaryTorque', 'summaryPower', 'summaryVelocity',
            'baseTorque', 'pulseTorque', 'pulseCount', 'efficiency'
        ];
        
        summaryElements.forEach(elementId => {
            const element = document.getElementById(elementId);
            if (element) {
                element.textContent = '0.00';
            }
        });
        
        console.log('✅ All data displays cleared');
    }
    
    /**
     * Setup connection monitoring and diagnostics
     */
    function setupConnectionMonitoring() {
        // Log connection status every 30 seconds
        setInterval(() => {
            if (app.isConnected && app.managers.charts) {
                const stats = app.managers.charts.getChartStats();
                console.log('📊 Chart Stats:', stats);
            }
            
            if (app.managers.floaterTable) {
                const tableStats = app.managers.floaterTable.getTableStats();
                console.log('📊 Table Stats:', tableStats);
            }
        }, 30000);
        
        // Performance monitoring
        let frameCount = 0;
        let lastFpsTime = Date.now();
        
        setInterval(() => {
            frameCount++;
            const now = Date.now();
            if (now - lastFpsTime >= 1000) {
                console.log(`📊 UI Update Rate: ${frameCount} FPS`);
                frameCount = 0;
                lastFpsTime = now;
            }
        }, 16); // ~60 FPS monitoring
    }
    
    /**
     * Export functionality for data download
     */
    function exportData(format = 'csv') {
        if (format === 'csv' && app.managers.floaterTable) {
            const csvData = app.managers.floaterTable.exportToCSV();
            downloadFile(csvData, `kpp-floater-data-${Date.now()}.csv`, 'text/csv');
        }
        
        // Could add chart data export here
        console.log(`📊 Data exported as ${format}`);
    }
    
    /**
     * Download file helper
     */
    function downloadFile(data, filename, mimeType) {
        const blob = new Blob([data], { type: mimeType });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
    }
    
    // Make key functions globally available for debugging
    window.kppApp = {
        app,
        exportData,
        clearAllData,
        updatePhysicsStatusIndicators,
        sendSimulationCommand
    };
    
    console.log('🎯 Enhanced KPP Simulator Ready!');
});
