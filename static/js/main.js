/**
 * KPP Simulator Real-Time Dashboard
 * Handles all frontend interactions, real-time data streaming, and visualization
 */

class KPPSimulator {
    constructor() {
        this.eventSource = null;
        this.charts = {};
        this.isRunning = false;
        this.isPaused = false;
        this.data = {
            time: [],
            force: [],
            position: [],
            velocity: [],
            pneumatic_pressure: [],
            fluid_pressure: [],
            temperature: []
        };
        this.maxDataPoints = 100;
        
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.initializeCharts();
        this.updateStatus();
        this.connectEventSource();
    }

    setupEventListeners() {
        // Control buttons
        document.getElementById('startBtn')?.addEventListener('click', () => this.startSimulation());
        document.getElementById('stopBtn')?.addEventListener('click', () => this.stopSimulation());
        document.getElementById('pauseBtn')?.addEventListener('click', () => this.pauseSimulation());
        document.getElementById('stepBtn')?.addEventListener('click', () => this.stepSimulation());
        document.getElementById('triggerBtn')?.addEventListener('click', () => this.triggerPulse());

        // Parameter controls
        document.getElementById('applyParams')?.addEventListener('click', () => this.applyParameters());
        document.getElementById('resetParams')?.addEventListener('click', () => this.resetParameters());

        // Real-time parameter sliders
        const sliders = document.querySelectorAll('.param-slider');
        sliders.forEach(slider => {
            slider.addEventListener('input', (e) => this.updateParameterDisplay(e.target));
        });
    }

    initializeCharts() {
        // Force Chart
        const forceCtx = document.getElementById('forceChart');
        if (forceCtx) {
            this.charts.force = new Chart(forceCtx, {
                type: 'line',
                data: {
                    labels: this.data.time,
                    datasets: [{
                        label: 'Force (N)',
                        data: this.data.force,
                        borderColor: '#3498db',
                        backgroundColor: 'rgba(52, 152, 219, 0.1)',
                        borderWidth: 2,
                        fill: true,
                        tension: 0.4
                    }]
                },
                options: this.getChartOptions('Force (N)')
            });
        }

        // Position Chart
        const positionCtx = document.getElementById('positionChart');
        if (positionCtx) {
            this.charts.position = new Chart(positionCtx, {
                type: 'line',
                data: {
                    labels: this.data.time,
                    datasets: [{
                        label: 'Position (m)',
                        data: this.data.position,
                        borderColor: '#2ecc71',
                        backgroundColor: 'rgba(46, 204, 113, 0.1)',
                        borderWidth: 2,
                        fill: true,
                        tension: 0.4
                    }]
                },
                options: this.getChartOptions('Position (m)')
            });
        }

        // Velocity Chart
        const velocityCtx = document.getElementById('velocityChart');
        if (velocityCtx) {
            this.charts.velocity = new Chart(velocityCtx, {
                type: 'line',
                data: {
                    labels: this.data.time,
                    datasets: [{
                        label: 'Velocity (m/s)',
                        data: this.data.velocity,
                        borderColor: '#e74c3c',
                        backgroundColor: 'rgba(231, 76, 60, 0.1)',
                        borderWidth: 2,
                        fill: true,
                        tension: 0.4
                    }]
                },
                options: this.getChartOptions('Velocity (m/s)')
            });
        }

        // Pressure Chart (Combined)
        const pressureCtx = document.getElementById('pressureChart');
        if (pressureCtx) {
            this.charts.pressure = new Chart(pressureCtx, {
                type: 'line',
                data: {
                    labels: this.data.time,
                    datasets: [
                        {
                            label: 'Pneumatic Pressure (Pa)',
                            data: this.data.pneumatic_pressure,
                            borderColor: '#9b59b6',
                            backgroundColor: 'rgba(155, 89, 182, 0.1)',
                            borderWidth: 2,
                            fill: false,
                            tension: 0.4
                        },
                        {
                            label: 'Fluid Pressure (Pa)',
                            data: this.data.fluid_pressure,
                            borderColor: '#f39c12',
                            backgroundColor: 'rgba(243, 156, 18, 0.1)',
                            borderWidth: 2,
                            fill: false,
                            tension: 0.4
                        }
                    ]
                },
                options: this.getChartOptions('Pressure (Pa)')
            });
        }

        // Temperature Chart
        const tempCtx = document.getElementById('temperatureChart');
        if (tempCtx) {
            this.charts.temperature = new Chart(tempCtx, {
                type: 'line',
                data: {
                    labels: this.data.time,
                    datasets: [{
                        label: 'Temperature (K)',
                        data: this.data.temperature,
                        borderColor: '#e67e22',
                        backgroundColor: 'rgba(230, 126, 34, 0.1)',
                        borderWidth: 2,
                        fill: true,
                        tension: 0.4
                    }]
                },
                options: this.getChartOptions('Temperature (K)')
            });
        }
    }

    getChartOptions(yAxisLabel) {
        return {
            responsive: true,
            maintainAspectRatio: false,
            animation: {
                duration: 0
            },
            interaction: {
                intersect: false,
                mode: 'index'
            },
            plugins: {
                legend: {
                    position: 'top',
                    labels: {
                        color: '#2c3e50',
                        font: {
                            size: 12
                        }
                    }
                },
                tooltip: {
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    titleColor: '#fff',
                    bodyColor: '#fff',
                    borderColor: '#3498db',
                    borderWidth: 1
                }
            },
            scales: {
                x: {
                    display: true,
                    title: {
                        display: true,
                        text: 'Time (s)',
                        color: '#2c3e50'
                    },
                    grid: {
                        color: 'rgba(0, 0, 0, 0.1)'
                    }
                },
                y: {
                    display: true,
                    title: {
                        display: true,
                        text: yAxisLabel,
                        color: '#2c3e50'
                    },
                    grid: {
                        color: 'rgba(0, 0, 0, 0.1)'
                    }
                }
            }
        };
    }

    connectEventSource() {
        if (this.eventSource) {
            this.eventSource.close();
        }

        this.eventSource = new EventSource('/stream');

        this.eventSource.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                this.updateDisplay(data);
            } catch (error) {
                console.error('Error parsing SSE data:', error);
            }
        };

        this.eventSource.onerror = (error) => {
            console.error('SSE connection error:', error);
            this.updateConnectionStatus(false);
        };

        this.eventSource.onopen = () => {
            console.log('SSE connection established');
            this.updateConnectionStatus(true);
        };
    }

    updateDisplay(data) {
        // Update status indicators
        this.isRunning = data.is_running || false;
        this.isPaused = data.is_paused || false;
        this.updateStatus();

        // Update real-time values
        if (data.outputs) {
            this.updateValueDisplays(data.outputs);
            this.updateCharts(data.outputs);
        }

        // Update system info
        if (data.system_info) {
            this.updateSystemInfo(data.system_info);
        }
    }

    updateValueDisplays(outputs) {
        const displayMap = {
            'force-value': outputs.total_force?.toFixed(3) || '0.000',
            'position-value': outputs.position?.toFixed(4) || '0.0000',
            'velocity-value': outputs.velocity?.toFixed(4) || '0.0000',
            'pneumatic-pressure-value': outputs.pneumatic_pressure?.toFixed(2) || '0.00',
            'fluid-pressure-value': outputs.fluid_pressure?.toFixed(2) || '0.00',
            'temperature-value': outputs.temperature?.toFixed(2) || '0.00'
        };

        Object.entries(displayMap).forEach(([id, value]) => {
            const element = document.getElementById(id);
            if (element) {
                element.textContent = value;
            }
        });
    }

    updateCharts(outputs) {
        if (!outputs.time) return;

        const currentTime = outputs.time;

        // Add new data points
        Object.keys(this.data).forEach(key => {
            if (outputs[key] !== undefined) {
                this.data[key].push(outputs[key]);
            }
        });

        // Limit data points to prevent memory issues
        if (this.data.time.length > this.maxDataPoints) {
            Object.keys(this.data).forEach(key => {
                this.data[key].shift();
            });
        }

        // Update all charts
        Object.values(this.charts).forEach(chart => {
            chart.update('none');
        });
    }

    updateSystemInfo(systemInfo) {
        const infoElement = document.getElementById('system-info');
        if (infoElement && systemInfo) {
            infoElement.innerHTML = `
                <div class="system-metric">
                    <span class="metric-label">CPU Usage:</span>
                    <span class="metric-value">${systemInfo.cpu_percent || 0}%</span>
                </div>
                <div class="system-metric">
                    <span class="metric-label">Memory:</span>
                    <span class="metric-value">${systemInfo.memory_percent || 0}%</span>
                </div>
                <div class="system-metric">
                    <span class="metric-label">Update Rate:</span>
                    <span class="metric-value">${systemInfo.update_rate || 0} Hz</span>
                </div>
            `;
        }
    }

    updateStatus() {
        const statusElement = document.getElementById('status');
        const startBtn = document.getElementById('startBtn');
        const stopBtn = document.getElementById('stopBtn');
        const pauseBtn = document.getElementById('pauseBtn');
        const stepBtn = document.getElementById('stepBtn');

        if (statusElement) {
            if (this.isRunning && !this.isPaused) {
                statusElement.textContent = 'Running';
                statusElement.className = 'status running';
            } else if (this.isPaused) {
                statusElement.textContent = 'Paused';
                statusElement.className = 'status paused';
            } else {
                statusElement.textContent = 'Stopped';
                statusElement.className = 'status stopped';
            }
        }

        // Update button states
        if (startBtn) startBtn.disabled = this.isRunning && !this.isPaused;
        if (stopBtn) stopBtn.disabled = !this.isRunning && !this.isPaused;
        if (pauseBtn) {
            pauseBtn.disabled = !this.isRunning;
            pauseBtn.textContent = this.isPaused ? 'Resume' : 'Pause';
        }
        if (stepBtn) stepBtn.disabled = this.isRunning && !this.isPaused;
    }

    updateConnectionStatus(connected) {
        const indicator = document.getElementById('connection-indicator');
        if (indicator) {
            indicator.className = connected ? 'connected' : 'disconnected';
            indicator.title = connected ? 'Connected to server' : 'Disconnected from server';
        }
    }

    updateParameterDisplay(slider) {
        const display = document.getElementById(slider.id + '-display');
        if (display) {
            display.textContent = parseFloat(slider.value).toFixed(3);
        }
    }

    async startSimulation() {
        try {
            const response = await fetch('/start', { method: 'POST' });
            const result = await response.json();
            this.showNotification(result.message || 'Simulation started', 'success');
        } catch (error) {
            this.showNotification('Failed to start simulation', 'error');
            console.error('Start simulation error:', error);
        }
    }

    async stopSimulation() {
        try {
            const response = await fetch('/stop', { method: 'POST' });
            const result = await response.json();
            this.showNotification(result.message || 'Simulation stopped', 'info');
        } catch (error) {
            this.showNotification('Failed to stop simulation', 'error');
            console.error('Stop simulation error:', error);
        }
    }

    async pauseSimulation() {
        try {
            const response = await fetch('/pause', { method: 'POST' });
            const result = await response.json();
            this.showNotification(result.message || 'Simulation paused/resumed', 'info');
        } catch (error) {
            this.showNotification('Failed to pause/resume simulation', 'error');
            console.error('Pause simulation error:', error);
        }
    }

    async stepSimulation() {
        try {
            const response = await fetch('/step', { method: 'POST' });
            const result = await response.json();
            this.showNotification('Simulation stepped', 'info');
        } catch (error) {
            this.showNotification('Failed to step simulation', 'error');
            console.error('Step simulation error:', error);
        }
    }

    async triggerPulse() {
        try {
            const response = await fetch('/trigger_pulse', { method: 'POST' });
            const result = await response.json();
            this.showNotification('Pulse triggered', 'success');
        } catch (error) {
            this.showNotification('Failed to trigger pulse', 'error');
            console.error('Trigger pulse error:', error);
        }
    }

    async applyParameters() {
        try {
            const params = this.collectParameters();
            const response = await fetch('/set_params', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(params)
            });
            const result = await response.json();
            this.showNotification('Parameters updated', 'success');
        } catch (error) {
            this.showNotification('Failed to update parameters', 'error');
            console.error('Apply parameters error:', error);
        }
    }

    collectParameters() {
        const params = {};
        const sliders = document.querySelectorAll('.param-slider');
        
        sliders.forEach(slider => {
            const paramName = slider.id.replace('-slider', '');
            params[paramName] = parseFloat(slider.value);
        });

        return params;
    }

    resetParameters() {
        const sliders = document.querySelectorAll('.param-slider');
        sliders.forEach(slider => {
            const defaultValue = slider.getAttribute('data-default') || slider.min;
            slider.value = defaultValue;
            this.updateParameterDisplay(slider);
        });
        this.showNotification('Parameters reset to defaults', 'info');
    }

    showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.textContent = message;

        // Add to page
        document.body.appendChild(notification);

        // Animate in
        setTimeout(() => notification.classList.add('show'), 10);

        // Remove after delay
        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => document.body.removeChild(notification), 300);
        }, 3000);
    }

    clearCharts() {
        Object.keys(this.data).forEach(key => {
            this.data[key] = [];
        });
        Object.values(this.charts).forEach(chart => {
            chart.update();
        });
    }

    destroy() {
        if (this.eventSource) {
            this.eventSource.close();
        }
        Object.values(this.charts).forEach(chart => {
            chart.destroy();
        });
    }
}

// Initialize the simulator when the page loads
document.addEventListener('DOMContentLoaded', () => {
    window.kppSimulator = new KPPSimulator();
});

// Handle page unload
window.addEventListener('beforeunload', () => {
    if (window.kppSimulator) {
        window.kppSimulator.destroy();
    }
});
