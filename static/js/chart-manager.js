/**
 * Enhanced Chart Manager for KPP Simulator
 * Handles real-time data visualization with physics effects
 * Stage 3.3 Implementation
 */

class ChartManager {
    constructor() {
        // Chart instances
        this.charts = {};
        this.chartData = {};
        this.maxDataPoints = 100;
        this.updateInterval = 100; // ms
        
        // Data tracking
        this.timeLabels = [];
        this.lastUpdateTime = 0;
        
        this.initializeCharts();
        console.log('✅ ChartManager initialized with enhanced physics visualization');
    }
    
    /**
     * Initialize all chart instances with enhanced configurations
     */
    initializeCharts() {
        // Primary Torque Components Chart
        this.initializeTorqueChart();
        
        // Power Output Chart
        this.initializePowerChart();
        
        // Physics Forces Chart (NEW)
        this.initializePhysicsChart();
        
        // System Efficiency Chart
        this.initializeEfficiencyChart();
        
        // Pulse Analysis Chart
        this.initializePulseChart();
        
        // Thermal Profile Chart (NEW)
        this.initializeThermalChart();
        
        console.log('✅ All charts initialized successfully');
    }
    
    /**
     * Enhanced Torque Chart with component breakdown
     */
    initializeTorqueChart() {
        const ctx = document.getElementById('torqueChart');
        if (!ctx) {
            console.warn('⚠️ Torque chart canvas not found');
            return;
        }
        
        this.charts.torque = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [
                    {
                        label: 'Net Torque',
                        data: [],
                        borderColor: '#007bff',
                        backgroundColor: 'rgba(0, 123, 255, 0.1)',
                        fill: false,
                        tension: 0.1,
                        borderWidth: 2
                    },
                    {
                        label: 'Buoyant Torque',
                        data: [],
                        borderColor: '#28a745',
                        backgroundColor: 'rgba(40, 167, 69, 0.1)',
                        fill: false,
                        tension: 0.1,
                        borderWidth: 1
                    },
                    {
                        label: 'Drag Torque',
                        data: [],
                        borderColor: '#dc3545',
                        backgroundColor: 'rgba(220, 53, 69, 0.1)',
                        fill: false,
                        tension: 0.1,
                        borderWidth: 1
                    },
                    {
                        label: 'Generator Load',
                        data: [],
                        borderColor: '#6c757d',
                        backgroundColor: 'rgba(108, 117, 125, 0.1)',
                        fill: false,
                        tension: 0.1,
                        borderWidth: 1
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                animation: false,
                interaction: {
                    intersect: false,
                    mode: 'index'
                },
                scales: {
                    x: {
                        title: { display: true, text: 'Time (s)' },
                        ticks: { maxTicksLimit: 10 }
                    },
                    y: {
                        title: { display: true, text: 'Torque (Nm)' },
                        grid: { color: 'rgba(0,0,0,0.1)' }
                    }
                },
                plugins: {
                    legend: { 
                        display: true,
                        position: 'top'
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return `${context.dataset.label}: ${context.parsed.y.toFixed(2)} Nm`;
                            }
                        }
                    }
                }
            }
        });
        
        console.log('✅ Torque chart initialized with component breakdown');
    }
    
    /**
     * Power Output Chart
     */
    initializePowerChart() {
        const ctx = document.getElementById('powerChart');
        if (!ctx) return;
        
        this.charts.power = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [
                    {
                        label: 'Electrical Power',
                        data: [],
                        borderColor: '#ff6b35',
                        backgroundColor: 'rgba(255, 107, 53, 0.1)',
                        fill: true,
                        tension: 0.1,
                        borderWidth: 2
                    },
                    {
                        label: 'Mechanical Power',
                        data: [],
                        borderColor: '#4ecdc4',
                        backgroundColor: 'rgba(78, 205, 196, 0.1)',
                        fill: false,
                        tension: 0.1,
                        borderWidth: 1
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                animation: false,
                scales: {
                    x: { title: { display: true, text: 'Time (s)' } },
                    y: { title: { display: true, text: 'Power (kW)' } }
                },
                plugins: {
                    legend: { display: true }
                }
            }
        });
        
        console.log('✅ Power chart initialized');
    }
    
    /**
     * NEW: Physics Forces Chart for H1, H2, H3 effects
     */
    initializePhysicsChart() {
        const ctx = document.getElementById('physicsChart');
        if (!ctx) return;
        
        this.charts.physics = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [
                    {
                        label: 'H1 Nanobubble Force',
                        data: [],
                        borderColor: '#9b59b6',
                        backgroundColor: 'rgba(155, 89, 182, 0.1)',
                        fill: false,
                        tension: 0.1,
                        borderWidth: 2
                    },
                    {
                        label: 'H2 Thermal Force',
                        data: [],
                        borderColor: '#e74c3c',
                        backgroundColor: 'rgba(231, 76, 60, 0.1)',
                        fill: false,
                        tension: 0.1,
                        borderWidth: 2
                    },
                    {
                        label: 'H3 Pulse Force',
                        data: [],
                        borderColor: '#f39c12',
                        backgroundColor: 'rgba(243, 156, 18, 0.1)',
                        fill: false,
                        tension: 0.1,
                        borderWidth: 2
                    },
                    {
                        label: 'Combined Enhancement',
                        data: [],
                        borderColor: '#2ecc71',
                        backgroundColor: 'rgba(46, 204, 113, 0.2)',
                        fill: true,
                        tension: 0.1,
                        borderWidth: 3
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                animation: false,
                scales: {
                    x: { title: { display: true, text: 'Time (s)' } },
                    y: { title: { display: true, text: 'Force (N)' } }
                },
                plugins: {
                    legend: { display: true },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return `${context.dataset.label}: ${context.parsed.y.toFixed(2)} N`;
                            }
                        }
                    }
                }
            }
        });
        
        console.log('✅ Physics forces chart initialized');
    }
    
    /**
     * Enhanced Efficiency Chart
     */
    initializeEfficiencyChart() {
        const ctx = document.getElementById('effChart');
        if (!ctx) return;
        
        this.charts.efficiency = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [
                    {
                        label: 'Overall Efficiency',
                        data: [],
                        borderColor: '#17a2b8',
                        backgroundColor: 'rgba(23, 162, 184, 0.1)',
                        fill: true,
                        tension: 0.1,
                        borderWidth: 2
                    },
                    {
                        label: 'Drivetrain Efficiency',
                        data: [],
                        borderColor: '#6f42c1',
                        backgroundColor: 'rgba(111, 66, 193, 0.1)',
                        fill: false,
                        tension: 0.1,
                        borderWidth: 1
                    },
                    {
                        label: 'Pneumatic Efficiency',
                        data: [],
                        borderColor: '#fd7e14',
                        backgroundColor: 'rgba(253, 126, 20, 0.1)',
                        fill: false,
                        tension: 0.1,
                        borderWidth: 1
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                animation: false,
                scales: {
                    x: { title: { display: true, text: 'Time (s)' } },
                    y: { 
                        title: { display: true, text: 'Efficiency (%)' },
                        min: 0,
                        max: 100
                    }
                },
                plugins: { legend: { display: true } }
            }
        });
        
        console.log('✅ Efficiency chart initialized');
    }
    
    /**
     * Enhanced Pulse Analysis Chart
     */
    initializePulseChart() {
        const ctx = document.getElementById('pulseChart');
        if (!ctx) return;
        
        this.charts.pulse = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [
                    {
                        label: 'Clutch State',
                        data: [],
                        borderColor: '#20c997',
                        backgroundColor: 'rgba(32, 201, 151, 0.3)',
                        fill: true,
                        tension: 0.1,
                        borderWidth: 2,
                        stepped: true  // Step chart for binary states
                    },
                    {
                        label: 'Pulse Phase',
                        data: [],
                        borderColor: '#6610f2',
                        backgroundColor: 'rgba(102, 16, 242, 0.2)',
                        fill: true,
                        tension: 0.1,
                        borderWidth: 2,
                        stepped: true
                    },
                    {
                        label: 'Duty Cycle %',
                        data: [],
                        borderColor: '#e83e8c',
                        backgroundColor: 'rgba(232, 62, 140, 0.1)',
                        fill: false,
                        tension: 0.1,
                        borderWidth: 1
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                animation: false,
                scales: {
                    x: { title: { display: true, text: 'Time (s)' } },
                    y: { 
                        title: { display: true, text: 'State / %' },
                        min: 0,
                        max: 100
                    }
                },
                plugins: { legend: { display: true } }
            }
        });
        
        console.log('✅ Pulse analysis chart initialized');
    }
    
    /**
     * NEW: Thermal Profile Chart
     */
    initializeThermalChart() {
        const ctx = document.getElementById('thermalChart');
        if (!ctx) return;
        
        this.charts.thermal = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [
                    {
                        label: 'Water Temperature',
                        data: [],
                        borderColor: '#dc3545',
                        backgroundColor: 'rgba(220, 53, 69, 0.1)',
                        fill: true,
                        tension: 0.1,
                        borderWidth: 2
                    },
                    {
                        label: 'Target Temperature',
                        data: [],
                        borderColor: '#ffc107',
                        backgroundColor: 'rgba(255, 193, 7, 0.1)',
                        fill: false,
                        tension: 0.1,
                        borderWidth: 1,
                        borderDash: [5, 5]  // Dashed line for target
                    },
                    {
                        label: 'Thermal Efficiency',
                        data: [],
                        borderColor: '#28a745',
                        backgroundColor: 'rgba(40, 167, 69, 0.1)',
                        fill: false,
                        tension: 0.1,
                        borderWidth: 1,
                        yAxisID: 'y1'  // Secondary Y axis
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                animation: false,
                scales: {
                    x: { title: { display: true, text: 'Time (s)' } },
                    y: { 
                        title: { display: true, text: 'Temperature (°C)' },
                        position: 'left'
                    },
                    y1: {
                        type: 'linear',
                        display: true,
                        position: 'right',
                        title: { display: true, text: 'Efficiency (%)' },
                        grid: { drawOnChartArea: false },
                        min: 0,
                        max: 100
                    }
                },
                plugins: { legend: { display: true } }
            }
        });
        
        console.log('✅ Thermal profile chart initialized');
    }
    
    /**
     * Update all charts with new simulation data
     */
    updateCharts(data) {
        if (!data || !data.time) return;
        
        const currentTime = parseFloat(data.time);
        
        // Throttle updates to prevent performance issues
        if (currentTime - this.lastUpdateTime < this.updateInterval / 1000) {
            return;
        }
        this.lastUpdateTime = currentTime;
        
        // Update time labels
        this.updateTimeLabels(currentTime);
        
        // Update individual charts
        this.updateTorqueChart(data);
        this.updatePowerChart(data);
        this.updatePhysicsChart(data);
        this.updateEfficiencyChart(data);
        this.updatePulseChart(data);
        this.updateThermalChart(data);
        
        // Limit data points to prevent memory issues
        this.trimDataHistory();
    }
    
    /**
     * Update time labels for all charts
     */
    updateTimeLabels(currentTime) {
        this.timeLabels.push(currentTime.toFixed(2));
        
        // Update all chart labels
        Object.values(this.charts).forEach(chart => {
            if (chart && chart.data) {
                chart.data.labels = [...this.timeLabels];
            }
        });
    }
    
    /**
     * Update torque chart with component breakdown
     */
    updateTorqueChart(data) {
        const chart = this.charts.torque;
        if (!chart) return;
        
        const torqueData = data.torque_components || {};
        
        // Add data points
        chart.data.datasets[0].data.push(data.torque || 0);  // Net torque
        chart.data.datasets[1].data.push(torqueData.buoyant || 0);  // Buoyant
        chart.data.datasets[2].data.push(Math.abs(torqueData.drag || 0));  // Drag (absolute)
        chart.data.datasets[3].data.push(Math.abs(torqueData.generator || 0));  // Generator load
        
        chart.update('none');  // Update without animation
    }
    
    /**
     * Update power chart
     */
    updatePowerChart(data) {
        const chart = this.charts.power;
        if (!chart) return;
        
        chart.data.datasets[0].data.push(data.power || 0);  // Electrical power
        chart.data.datasets[1].data.push((data.torque || 0) * (data.angular_velocity || 0) / 1000);  // Mechanical power
        
        chart.update('none');
    }
    
    /**
     * Update physics forces chart (H1, H2, H3)
     */
    updatePhysicsChart(data) {
        const chart = this.charts.physics;
        if (!chart) return;
        
        const physicsData = data.physics_forces || {};
        
        chart.data.datasets[0].data.push(physicsData.h1_nanobubble_force || 0);
        chart.data.datasets[1].data.push(physicsData.h2_thermal_force || 0);
        chart.data.datasets[2].data.push(physicsData.h3_pulse_force || 0);
        chart.data.datasets[3].data.push(
            (physicsData.h1_nanobubble_force || 0) + 
            (physicsData.h2_thermal_force || 0) + 
            (physicsData.h3_pulse_force || 0)
        );
        
        chart.update('none');
    }
    
    /**
     * Update efficiency chart
     */
    updateEfficiencyChart(data) {
        const chart = this.charts.efficiency;
        if (!chart) return;
        
        chart.data.datasets[0].data.push(data.efficiency || 0);
        chart.data.datasets[1].data.push(data.drivetrain_efficiency || 0);
        chart.data.datasets[2].data.push(data.pneumatic_efficiency || 0);
        
        chart.update('none');
    }
    
    /**
     * Update pulse analysis chart
     */
    updatePulseChart(data) {
        const chart = this.charts.pulse;
        if (!chart) return;
        
        const systemStatus = data.system_status || {};
        const physicsStatus = data.physics_status || {};
        
        chart.data.datasets[0].data.push(systemStatus.clutch_engaged ? 100 : 0);
        chart.data.datasets[1].data.push(physicsStatus.h3_pulse_active ? 100 : 0);
        chart.data.datasets[2].data.push((data.duty_cycle || 0) * 100);
        
        chart.update('none');
    }
    
    /**
     * Update thermal profile chart
     */
    updateThermalChart(data) {
        const chart = this.charts.thermal;
        if (!chart) return;
        
        const thermalData = data.thermal_data || {};
        
        // Convert Kelvin to Celsius if needed
        const waterTemp = (thermalData.current_temperature_K || 293.15) - 273.15;
        const targetTemp = (thermalData.target_temperature_K || 298.15) - 273.15;
        
        chart.data.datasets[0].data.push(waterTemp);
        chart.data.datasets[1].data.push(targetTemp);
        chart.data.datasets[2].data.push((thermalData.thermal_efficiency || 0) * 100);
        
        chart.update('none');
    }
    
    /**
     * Trim data history to prevent memory issues
     */
    trimDataHistory() {
        if (this.timeLabels.length > this.maxDataPoints) {
            // Remove oldest data points
            const removeCount = this.timeLabels.length - this.maxDataPoints;
            this.timeLabels.splice(0, removeCount);
            
            // Trim all chart datasets
            Object.values(this.charts).forEach(chart => {
                if (chart && chart.data) {
                    chart.data.labels = [...this.timeLabels];
                    chart.data.datasets.forEach(dataset => {
                        if (dataset.data.length > this.maxDataPoints) {
                            dataset.data.splice(0, removeCount);
                        }
                    });
                }
            });
        }
    }
    
    /**
     * Clear all chart data
     */
    clearAllCharts() {
        this.timeLabels = [];
        
        Object.values(this.charts).forEach(chart => {
            if (chart && chart.data) {
                chart.data.labels = [];
                chart.data.datasets.forEach(dataset => {
                    dataset.data = [];
                });
                chart.update();
            }
        });
        
        console.log('✅ All charts cleared');
    }
    
    /**
     * Resize all charts (useful for responsive design)
     */
    resizeCharts() {
        Object.values(this.charts).forEach(chart => {
            if (chart) {
                chart.resize();
            }
        });
    }
    
    /**
     * Get chart statistics for debugging
     */
    getChartStats() {
        const stats = {};
        Object.entries(this.charts).forEach(([name, chart]) => {
            if (chart && chart.data) {
                stats[name] = {
                    datasets: chart.data.datasets.length,
                    dataPoints: chart.data.datasets[0]?.data.length || 0,
                    labels: chart.data.labels.length
                };
            }
        });
        return stats;
    }
}

// Initialize chart manager when DOM is ready
let chartManager = null;

document.addEventListener('DOMContentLoaded', function() {
    chartManager = new ChartManager();
    
    // Make it globally accessible
    window.chartManager = chartManager;
});

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ChartManager;
}
