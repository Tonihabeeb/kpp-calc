document.addEventListener('DOMContentLoaded', function() {
    // Chart.js setup
    let torqueChart, powerChart, pulseChart, effChart;
    const torqueCtx = document.getElementById('torqueChart').getContext('2d');
    const powerCtx = document.getElementById('powerChart').getContext('2d');
    const pulseCtx = document.getElementById('pulseChart').getContext('2d');
    const effCtx = document.getElementById('effChart').getContext('2d');

    // SSE connection
    let eventSource = null;
    let isConnected = false;

    // Initialize charts
    torqueChart = new Chart(torqueCtx, {
        type: 'line',
        data: { 
            labels: [], 
            datasets: [{ 
                label: 'Total Torque', 
                data: [], 
                borderColor: 'blue', 
                fill: false,
                tension: 0.1
            }] 
        },
        options: { 
            responsive: true, 
            scales: { 
                x: { 
                    title: { display: true, text: 'Time (s)' },
                    ticks: {
                        callback: function(value, index, values) {
                            return Number(this.getLabelForValue(value)).toFixed(2);
                        }
                    }
                }, 
                y: { title: { display: true, text: 'Torque (Nm)' } } 
            },
            animation: false,
            plugins: {
                legend: { display: true }
            }
        }
    });

    powerChart = new Chart(powerCtx, {
        type: 'line',
        data: { 
            labels: [], 
            datasets: [{ 
                label: 'Power Output', 
                data: [], 
                borderColor: 'green', 
                fill: false,
                tension: 0.1
            }] 
        },
        options: { 
            responsive: true, 
            scales: { 
                x: { 
                    title: { display: true, text: 'Time (s)' },
                    ticks: {
                        callback: function(value, index, values) {
                            return Number(this.getLabelForValue(value)).toFixed(2);
                        }
                    }
                }, 
                y: { title: { display: true, text: 'Power (kW)' } } 
            },
            animation: false,
            plugins: {
                legend: { display: true }
            }
        }
    });

    pulseChart = new Chart(pulseCtx, {
        type: 'line',
        data: { 
            labels: [], 
            datasets: [
                { 
                    label: 'Base Torque', 
                    data: [], 
                    borderColor: 'orange', 
                    fill: false,
                    tension: 0.1
                },
                { 
                    label: 'Pulse Torque', 
                    data: [], 
                    borderColor: 'red', 
                    fill: false,
                    tension: 0.1
                }
            ] 
        },
        options: { 
            responsive: true, 
            scales: { 
                x: { 
                    title: { display: true, text: 'Time (s)' },
                    ticks: {
                        callback: function(value, index, values) {
                            return Number(this.getLabelForValue(value)).toFixed(2);
                        }
                    }
                }, 
                y: { title: { display: true, text: 'Torque (Nm)' } } 
            },
            animation: false,
            plugins: {
                legend: { display: true }
            }
        }
    });

    // Efficiency Chart (GuideV3.md requirement)
    effChart = new Chart(effCtx, {
        type: 'line',
        data: { 
            labels: [], 
            datasets: [{ 
                label: 'Efficiency', 
                data: [], 
                borderColor: 'purple', 
                fill: false,
                tension: 0.1
            }] 
        },
        options: { 
            responsive: true, 
            scales: { 
                x: { 
                    title: { display: true, text: 'Time (s)' },
                    ticks: {
                        callback: function(value, index, values) {
                            return Number(this.getLabelForValue(value)).toFixed(2);
                        }
                    }
                }, 
                y: { 
                    title: { display: true, text: 'Efficiency (%)' },
                    min: 0,
                    max: 100
                } 
            },
            animation: false,
            plugins: {
                legend: { display: true }
            }
        }
    });    // SSE Connection Management (GuideV3.md pattern)
    function connectSSE() {
        if (eventSource) {
            eventSource.close();
        }

        eventSource = new EventSource('/stream');
        
        eventSource.onopen = function() {
            isConnected = true;
            updateConnectionStatus('Connected', 'connected');
            console.log('SSE Connected');
        };

        eventSource.onmessage = function(event) {
            try {
                const data = JSON.parse(event.data);
                if (!data.heartbeat) {
                    updateFromSSEData(data);
                }
            } catch (e) {
                console.error('Error parsing SSE data:', e);
            }
        };

        eventSource.onerror = function(event) {
            isConnected = false;
            updateConnectionStatus('Disconnected', 'disconnected');
            console.log('SSE Error:', event);
            
            // Reconnect after 3 seconds
            setTimeout(connectSSE, 3000);
        };
    }

    // Helper to add data to a Chart.js chart (from GuideV3.md)
    function addData(chart, label, value) {
        chart.data.labels.push(label);
        chart.data.datasets.forEach((ds) => ds.data.push(value));
        
        // Keep only last 100 points for performance
        if (chart.data.labels.length > 100) {
            chart.data.labels.shift();
            chart.data.datasets.forEach((ds) => ds.data.shift());
        }
        
        chart.update('none'); // 'none' for better performance
    }

    function updateConnectionStatus(status, className) {
        const statusElement = document.getElementById('sseStatus');
        statusElement.textContent = status;
        statusElement.className = className;
    }    // Data history for charts
    const chartData = {
        time: [],
        torque: [],
        power: [],
        efficiency: [],
        baseTorque: [],
        pulseTorque: []
    };

    function updateFromSSEData(data) {
        // Use GuideV3.md pattern for real-time chart updates
        if (data.time !== undefined) {
            const timeFormatted = Number(data.time).toFixed(2);
            
            // Add new data points to charts using GuideV3.md addData helper
            addData(torqueChart, timeFormatted, data.torque || 0);
            addData(powerChart, timeFormatted, (data.power || 0) / 1000); // Convert to kW
            // Use overall_efficiency (fraction) *100 for percent
            addData(effChart, timeFormatted, (data.overall_efficiency || 0) * 100);
            
            // Update pulse chart (multiple datasets)
            if (pulseChart.data.labels.length > 100) {
                pulseChart.data.labels.shift();
                pulseChart.data.datasets.forEach((ds) => ds.data.shift());
            }
            pulseChart.data.labels.push(timeFormatted);
            pulseChart.data.datasets[0].data.push(data.base_buoy_torque || 0);
            pulseChart.data.datasets[1].data.push(data.pulse_torque || 0);
            pulseChart.update('none');
        }

        // Update summary
        updateSummary(data);

        // Update per-floater state table (GuideV3.md requirement)
        if (data.floaters) {
            updateFloaterTable(data.floaters);
        }

        // Update pneumatic system status (Phase 7)
        updatePneumaticStatus(data);
    }

    // Phase 7: Update pneumatic system status
    function updatePneumaticStatus(data) {
        // Update basic pneumatic metrics in summary
        if (data.tank_pressure !== undefined) {
            document.getElementById('tankPressure').textContent = (data.tank_pressure / 100000).toFixed(2); // Convert Pa to bar
        }
        
        // Update pneumatic performance metrics
        if (data.pneumatic_performance) {
            const perf = data.pneumatic_performance;
            document.getElementById('pneumaticEfficiency').textContent = (perf.average_efficiency * 100).toFixed(2);
            document.getElementById('capacityFactor').textContent = (perf.capacity_factor * 100).toFixed(2);
            document.getElementById('thermalEfficiency').textContent = (perf.thermal_efficiency * 100).toFixed(2);
            
            // Update detailed performance metrics
            document.getElementById('avgEfficiency').textContent = (perf.average_efficiency * 100).toFixed(2);
            document.getElementById('peakEfficiency').textContent = (perf.peak_efficiency * 100).toFixed(2);
            document.getElementById('powerFactor').textContent = perf.power_factor.toFixed(3);
            document.getElementById('availability').textContent = (perf.availability * 100).toFixed(2);
        }
        
        // Update energy balance information
        if (data.pneumatic_energy) {
            const energy = data.pneumatic_energy;
            document.getElementById('totalInputEnergy').textContent = (energy.total_input_energy / 1000).toFixed(2); // Convert J to kJ
            document.getElementById('totalOutputEnergy').textContent = (energy.total_output_energy / 1000).toFixed(2);
            document.getElementById('overallEfficiency').textContent = (energy.overall_efficiency * 100).toFixed(2);
            document.getElementById('energyBalanceError').textContent = Math.abs(energy.energy_balance_error || 0).toFixed(3);
            document.getElementById('conservationValid').textContent = energy.conservation_valid ? 'Yes' : 'No';
            document.getElementById('thermalContribution').textContent = ((energy.thermal_contribution || 0) * 100).toFixed(2);
        }
        
        // Update optimization recommendations
        if (data.pneumatic_optimization) {
            const opt = data.pneumatic_optimization;
            document.getElementById('recommendationCount').textContent = opt.recommendation_count || 0;
            
            const recList = document.getElementById('recommendationsList');
            if (opt.latest_recommendations && opt.latest_recommendations.length > 0) {
                recList.innerHTML = '';
                opt.latest_recommendations.forEach(rec => {
                    const li = document.createElement('li');
                    li.innerHTML = `<strong>${rec.target}</strong>: ${rec.description} (${(rec.expected_improvement * 100).toFixed(1)}% improvement, ${(rec.confidence * 100).toFixed(0)}% confidence)`;
                    recList.appendChild(li);
                });
            } else {
                recList.innerHTML = '<li>No recommendations available</li>';
            }
        }
    }

    // Fetch detailed pneumatic data periodically
    function fetchPneumaticData() {
        fetch('/data/pneumatic_status')
            .then(response => response.json())
            .then(data => {
                if (data.status !== 'no_data') {
                    updatePneumaticStatus(data);
                }
            })
            .catch(error => console.error('Error fetching pneumatic data:', error));
    }

    // Start periodic updates for pneumatic data
    setInterval(fetchPneumaticData, 2000); // Update every 2 seconds

    function updateCharts() {
        // Update torque chart
        torqueChart.data.labels = chartData.time;
        torqueChart.data.datasets[0].data = chartData.torque;
        torqueChart.update('none');

        // Update power chart
        powerChart.data.labels = chartData.time;
        powerChart.data.datasets[0].data = chartData.power;
        powerChart.update('none');

        // Update pulse chart
        pulseChart.data.labels = chartData.time;
        pulseChart.data.datasets[0].data = chartData.baseTorque;
        pulseChart.data.datasets[1].data = chartData.pulseTorque;
        pulseChart.update('none');

        // Update efficiency chart
        const efficiencyData = chartData.time.map((_, index) => {
            const power = chartData.power[index];
            const torque = chartData.torque[index];
            return power && torque ? (power / (torque * 10)) * 100 : 0;
        });
        effChart.data.labels = chartData.time;
        effChart.data.datasets[0].data = efficiencyData;
        effChart.update('none');
    }

    function updateSummary(data) {
        document.getElementById('summaryTime').textContent = data.time ? Number(data.time).toFixed(2) : '0.00';
        document.getElementById('summaryTorque').textContent = data.torque ? Number(data.torque).toFixed(2) : '0.00';
        document.getElementById('summaryPower').textContent = data.power ? (data.power / 1000).toFixed(2) : '0.00';
        document.getElementById('summaryVelocity').textContent = data.avg_floater_velocity ? Number(data.avg_floater_velocity).toFixed(2) : '0.00';
        
        // Pulse metrics
        document.getElementById('baseTorque').textContent = data.base_buoy_torque ? Number(data.base_buoy_torque).toFixed(2) : '0.00';
        document.getElementById('pulseTorque').textContent = data.pulse_torque ? Number(data.pulse_torque).toFixed(2) : '0.00';
        document.getElementById('pulseCount').textContent = data.pulse_count || '0';
        document.getElementById('clutchStatus').textContent = data.clutch_state || (data.clutch_engaged ? 'Engaged' : 'Disengaged');
        
        // Mechanical status
        document.getElementById('chainSpeed').textContent = data.chain_speed_rpm ? Number(data.chain_speed_rpm).toFixed(2) : '0.00';
        document.getElementById('flywheelSpeed').textContent = data.flywheel_speed_rpm ? Number(data.flywheel_speed_rpm).toFixed(2) : '0.00';
        
        // Count active pulses
        let activePulses = 0;
        if (data.floaters) {
            activePulses = data.floaters.filter(f => f.is_pulsing).length;
        }
        document.getElementById('activePulses').textContent = activePulses;
        
        // Display overall mechanical efficiency
        document.getElementById('efficiency').textContent = data.overall_efficiency ? (data.overall_efficiency * 100).toFixed(2) : '0.00';
    }

    function updateFloatersTable(floaters) {
        const tbody = document.getElementById('floatersTableBody');
        tbody.innerHTML = '';
        
        floaters.forEach(f => {
            const row = document.createElement('tr');
            
            // Add pulse indicator class
            if (f.is_pulsing) {
                row.classList.add('pulsing');
            }
            
            row.innerHTML = `
                <td>${f.id}</td>
                <td>${f.position ? Number(f.position).toFixed(2) : '0.00'}</td>
                <td>${f.velocity ? Number(f.velocity).toFixed(2) : '0.00'}</td>
                <td>${f.state || 'idle'}</td>
                <td>${f.force ? Number(f.force).toFixed(2) : '0.00'}</td>
                <td>${f.buoyancy ? Number(f.buoyancy).toFixed(2) : '0.00'}</td>
                <td>${f.gravity ? Number(f.gravity).toFixed(2) : '0.00'}</td>
                <td>${f.drag ? Number(f.drag).toFixed(2) : '0.00'}</td>
                <td>${f.net_force ? Number(f.net_force).toFixed(2) : '0.00'}</td>
                <td class="pulse-force">${f.pulse_force ? Number(f.pulse_force).toFixed(2) : '0.00'}</td>
                <td class="fill-progress">${f.fill_progress ? (Number(f.fill_progress) * 100).toFixed(1) + '%' : '0.0%'}</td>
            `;
            tbody.appendChild(row);
        });
    }

    // Per-floater state table update (GuideV3.md requirement)
    function updateFloaterTable(floaters) {
        const table = document.getElementById('floaterTable');
        
        // Clear existing rows except header
        table.querySelectorAll('tr.floaterRow').forEach(row => row.remove());
        
        floaters.forEach((f, i) => {
            const row = table.insertRow();
            row.classList.add('floaterRow');
            row.insertCell().innerText = i + 1;
            row.insertCell().innerText = f.pos ? f.pos.toFixed(2) : '0.00';
            row.insertCell().innerText = f.vel ? f.vel.toFixed(2) : '0.00';
            row.insertCell().innerText = f.buoy ? f.buoy.toFixed(2) : '0.00';
            row.insertCell().innerText = f.drag ? f.drag.toFixed(2) : '0.00';
            row.insertCell().innerText = f.state || 'idle';
            row.insertCell().innerText = f.fluid_density ? f.fluid_density.toFixed(1) : '1000.0';
            
            // Highlight pulsing floaters
            if (f.is_pulsing) {
                row.style.backgroundColor = '#ffeb3b';
            }
        });
    }

    // Fallback polling for when SSE is not available
    function fallbackUpdate() {
        if (!isConnected) {
            fetch('/data/summary').then(r => r.json()).then(data => {
                updateSummary(data);
                if (data.floaters) {
                    updateFloatersTable(data.floaters);
                }
            }).catch(console.error);
        }
    }

    // Poll every 2 seconds as fallback
    setInterval(fallbackUpdate, 2000);

    // Controls
    document.getElementById('startBtn').onclick = function() {
        const form = document.getElementById('paramsForm');
        const formData = new FormData(form);
        const params = {};
        for (const [key, value] of formData.entries()) {
            params[key] = isNaN(value) ? value : Number(value);
        }
        fetch('/start', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(params)
        });
    };

    document.getElementById('pauseBtn').onclick = function() {
        fetch('/pause', { method: 'POST' });
    };

    document.getElementById('stopBtn').onclick = function() {
        fetch('/stop', { method: 'POST' });
    };

    document.getElementById('resetBtn').onclick = function() {
        fetch('/reset', { method: 'POST' });
        // Clear chart data
        chartData.time = [];
        chartData.torque = [];
        chartData.power = [];
        chartData.baseTorque = [];
        chartData.pulseTorque = [];
        updateCharts();
    };

    document.getElementById('stepBtn').onclick = function() {
        fetch('/step', { method: 'POST' });
    };

    document.getElementById('pulseBtn').onclick = function() {
        fetch('/trigger_pulse', { method: 'POST' })
            .then(response => {
                if (!response.ok) {
                    alert('No available floater for pulse');
                }
            });
    };

    // Parameter controls (GuideV3.md requirement)
    document.getElementById('nanobubbleSlider').oninput = function(e) {
        const value = e.target.value / 100.0;
        document.getElementById('nanobubbleValue').textContent = e.target.value + '%';
        
        fetch('/set_params', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ nanobubble_frac: value })
        });
    };

    document.getElementById('heatCoeff').onchange = function(e) {
        fetch('/set_params', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ thermal_coeff: parseFloat(e.target.value) })
        });
    };

    document.getElementById('waterTemp').onchange = function(e) {
        fetch('/set_params', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ water_temp: parseFloat(e.target.value) })
        });
    };

    document.getElementById('airPressure').onchange = function(e) {
        fetch('/set_params', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ air_pressure: parseFloat(e.target.value) })
        });
    };

    // Parameter form submission
    document.getElementById('paramsForm').onsubmit = function(e) {
        e.preventDefault();
        
        const formData = new FormData(e.target);
        const params = {};
        
        // Convert form data to proper types
        for (let [key, value] of formData.entries()) {
            if (['num_floaters'].includes(key)) {
                params[key] = parseInt(value);
            } else if (key === 'nanobubble_frac') {
                params[key] = parseFloat(value) / 100.0; // Convert percentage to fraction
            } else {
                params[key] = parseFloat(value);
            }
        }
        
        fetch('/set_params', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(params)
        });
    };

    // Generator load control
    document.getElementById('setLoadBtn').onclick = function() {
        const userLoad = parseFloat(document.getElementById('userLoadInput').value);
        fetch('/set_load', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_load_torque: userLoad })
        })
        .then(response => response.text())
        .then(msg => {
            document.getElementById('setLoadStatus').textContent = msg;
        })
        .catch(err => {
            document.getElementById('setLoadStatus').textContent = 'Error setting load';
        });
    };

    // Handle parameter form submission for dynamic tuning
    const paramsForm = document.getElementById('paramsForm');
    paramsForm.addEventListener('submit', function(e) {
        e.preventDefault();
        const formData = new FormData(paramsForm);
        const params = {};
        formData.forEach((value, key) => {
            params[key] = parseFloat(value);
        });
        fetch('/set_params', {
            method: 'POST',
            headers: {'Content-Type':'application/json'},
            body: JSON.stringify(params)
        }).then(response => response.json())
          .then(data => console.log('Params updated:', data));
    });

    // Initialize SSE connection
    connectSSE();

    // ========================================================================================
    // PHASE 8: INTEGRATED SYSTEMS DATA FETCHING AND UI UPDATES
    // ========================================================================================

    // Advanced system data fetching functions
    function fetchIntegratedSystemsData() {
        // Fetch drivetrain data
        fetch('/data/drivetrain_status')
            .then(response => response.json())
            .then(data => {
                if (data && typeof data === 'object') {
                    updateDrivetrainUI(data);
                }
            })
            .catch(error => console.error('Error fetching drivetrain data:', error));
        
        // Fetch electrical data  
        fetch('/data/electrical_status')
            .then(response => response.json())
            .then(data => {
                if (data && typeof data === 'object') {
                    updateElectricalUI(data);
                }
            })
            .catch(error => console.error('Error fetching electrical data:', error));
        
        // Fetch control system data
        fetch('/data/control_status')
            .then(response => response.json())
            .then(data => {
                if (data && typeof data === 'object') {
                    updateControlUI(data);
                }
            })
            .catch(error => console.error('Error fetching control data:', error));
        
        // Fetch grid services data
        fetch('/data/grid_services_status')
            .then(response => response.json())
            .then(data => {
                if (data && typeof data === 'object') {
                    updateGridServicesUI(data);
                }
            })
            .catch(error => console.error('Error fetching grid services data:', error));
        
        // Fetch enhanced losses data
        fetch('/data/enhanced_losses')
            .then(response => response.json())
            .then(data => {
                if (data && typeof data === 'object') {
                    updateEnhancedLossesUI(data);
                }
            })
            .catch(error => console.error('Error fetching enhanced losses data:', error));
        
        // Fetch system overview
        fetch('/data/system_overview')
            .then(response => response.json())
            .then(data => {
                if (data && typeof data === 'object') {
                    updateSystemOverviewUI(data);
                }
            })
            .catch(error => console.error('Error fetching system overview:', error));
    }

    function updateDrivetrainUI(data) {
        // Update drivetrain metrics
        document.getElementById('sprocketTorque').textContent = (data.sprocket_torque || 0).toFixed(2);
        document.getElementById('gearboxTorque').textContent = (data.gearbox_output_torque || 0).toFixed(2);
        document.getElementById('flywheelSpeedAdvanced').textContent = (data.flywheel_speed_rpm || 0).toFixed(1);
        document.getElementById('chainTensionAdvanced').textContent = (data.chain_tension || 0).toFixed(1);
        document.getElementById('clutchStatusAdvanced').textContent = data.clutch_engaged ? 'Engaged' : 'Disengaged';
        
        // Update performance metrics
        document.getElementById('drivetrainEfficiency').textContent = ((data.system_efficiency || 0) * 100).toFixed(2);
        document.getElementById('storedEnergy').textContent = ((data.flywheel_stored_energy || 0) / 1000).toFixed(2);
        
        const powerFlow = data.power_flow || {};
        document.getElementById('powerTransfer').textContent = ((powerFlow.output_power || 0) / 1000).toFixed(1);
        
        const advancedMetrics = data.advanced_metrics || {};
        document.getElementById('operatingTime').textContent = ((advancedMetrics.operating_time || 0) / 3600).toFixed(2);
        document.getElementById('pulseCountAdvanced').textContent = advancedMetrics.pulse_count || 0;
    }

    function updateElectricalUI(data) {
        // Update power generation metrics
        document.getElementById('gridPowerOutput').textContent = ((data.grid_power_output || 0) / 1000).toFixed(1);
        document.getElementById('electricalEfficiency').textContent = ((data.electrical_efficiency || 0) * 100).toFixed(2);
        document.getElementById('loadFactor').textContent = ((data.load_factor || 0) * 100).toFixed(1);
        document.getElementById('loadTorqueCommand').textContent = (data.electrical_load_torque || 0).toFixed(1);
        
        // Update grid interface
        document.getElementById('gridSynchronized').textContent = data.synchronized ? 'Yes' : 'No';
        document.getElementById('gridVoltage').textContent = (data.grid_voltage || 0).toFixed(1);
        document.getElementById('gridFrequency').textContent = (data.grid_frequency || 0).toFixed(2);
        
        const powerQuality = data.power_quality || {};
        document.getElementById('powerFactorAdvanced').textContent = (powerQuality.power_factor || 0).toFixed(3);
        
        // Update performance summary
        const performanceMetrics = data.performance_metrics || {};
        document.getElementById('energyGenerated').textContent = (performanceMetrics.total_energy_generated_kwh || 0).toFixed(2);
        document.getElementById('energyDelivered').textContent = (performanceMetrics.total_energy_delivered_kwh || 0).toFixed(2);
        document.getElementById('operatingHours').textContent = (performanceMetrics.operating_hours || 0).toFixed(2);
        document.getElementById('capacityFactorElectrical').textContent = (performanceMetrics.capacity_factor_percent || 0).toFixed(1);
    }

    function updateControlUI(data) {
        // Update control state
        document.getElementById('controlMode').textContent = data.control_mode || 'Unknown';
        document.getElementById('systemHealth').textContent = ((data.system_health || 0) * 100).toFixed(1);
        
        const faultStatus = data.fault_status || {};
        const activeFaults = faultStatus.active_faults || [];
        document.getElementById('activeFaults').textContent = activeFaults.length;
        document.getElementById('pneumaticControlActive').textContent = data.pneumatic_control_executed ? 'Active' : 'Inactive';
        
        // Update commands & timing
        const timingCommands = data.timing_commands || {};
        const loadCommands = data.load_commands || {};
        const gridCommands = data.grid_commands || {};
        
        document.getElementById('timingAdjustment').textContent = (timingCommands.pulse_timing_adjustment || 0).toFixed(3);
        document.getElementById('loadTarget').textContent = ((loadCommands.target_load_factor || 0) * 100).toFixed(1);
        document.getElementById('gridVoltageSetpoint').textContent = (gridCommands.voltage_setpoint || 480).toFixed(1);
        document.getElementById('gridFrequencySetpoint').textContent = (gridCommands.frequency_setpoint || 60.0).toFixed(1);
        
        // Update emergency systems
        const emergencyStatus = data.emergency_status || {};
        const systemStatus = data.system_status || {};
        document.getElementById('emergencyStatus').textContent = emergencyStatus.status || 'Normal';
        document.getElementById('systemStatus').textContent = systemStatus.state || 'Unknown';
    }

    function updateGridServicesUI(data) {
        // Update active services
        document.getElementById('activeServicesCount').textContent = data.active_services_count || 0;
        document.getElementById('coordinationStatus').textContent = data.coordination_status || 'Unknown';
        document.getElementById('totalPowerCommand').textContent = (data.total_power_command_mw || 0).toFixed(3);
        
        // Update active services list
        const activeServices = data.active_services || [];
        const servicesList = document.getElementById('servicesListItems');
        servicesList.innerHTML = '';
        
        if (activeServices.length === 0) {
            const li = document.createElement('li');
            li.textContent = 'No active services';
            servicesList.appendChild(li);
        } else {
            activeServices.forEach(service => {
                const li = document.createElement('li');
                li.textContent = service;
                servicesList.appendChild(li);
            });
        }
        
        // Update performance metrics
        const performanceDiv = document.getElementById('gridServicesPerformance');
        const performanceMetrics = data.performance_metrics || {};
        
        if (Object.keys(performanceMetrics).length > 0) {
            performanceDiv.innerHTML = `
                <pre>${JSON.stringify(performanceMetrics, null, 2)}</pre>
            `;
        } else {
            performanceDiv.innerHTML = '<p>Performance metrics will be displayed here when available.</p>';
        }
    }

    function updateEnhancedLossesUI(data) {
        // Update system losses
        document.getElementById('totalSystemLosses').textContent = (data.total_system_losses || 0).toFixed(1);
        
        const mechanicalLosses = data.mechanical_losses || {};
        document.getElementById('mechanicalLosses').textContent = (mechanicalLosses.total_losses || 0).toFixed(1);
        document.getElementById('electricalLosses').textContent = (data.electrical_losses || 0).toFixed(1);
        document.getElementById('thermalLosses').textContent = (data.thermal_losses || 0).toFixed(1);
        
        // Update component temperatures
        const componentTemps = data.component_temperatures || {};
        document.getElementById('sprocketTemp').textContent = componentTemps.sprocket ? componentTemps.sprocket.toFixed(1) : '--';
        document.getElementById('gearboxTemp').textContent = componentTemps.gearbox ? componentTemps.gearbox.toFixed(1) : '--';
        document.getElementById('clutchTemp').textContent = componentTemps.clutch ? componentTemps.clutch.toFixed(1) : '--';
        document.getElementById('flywheelTemp').textContent = componentTemps.flywheel ? componentTemps.flywheel.toFixed(1) : '--';
        document.getElementById('generatorTemp').textContent = componentTemps.generator ? componentTemps.generator.toFixed(1) : '--';
        
        // Update thermal management
        const thermalState = data.thermal_state || {};
        document.getElementById('overallThermalEfficiency').textContent = ((thermalState.overall_thermal_efficiency || 1.0) * 100).toFixed(2);
        document.getElementById('coolingSystemStatus').textContent = thermalState.cooling_system_active ? 'Active' : 'Inactive';
    }

    function updateSystemOverviewUI(data) {
        // Update power flow summary
        const powerGen = data.power_generation || {};
        document.getElementById('mechanicalPowerInput').textContent = ((powerGen.mechanical_power || 0) / 1000).toFixed(1);
        document.getElementById('electricalPowerOutput').textContent = ((powerGen.electrical_power || 0) / 1000).toFixed(1);
        document.getElementById('gridPowerDelivery').textContent = ((powerGen.electrical_power || 0) / 1000).toFixed(1);
        
        const systemStatus = data.system_status || {};
        document.getElementById('overallSystemEfficiency').textContent = ((systemStatus.overall_efficiency || 0) * 100).toFixed(2);
        
        // Update system health
        const mechanicalSystems = data.mechanical_systems || {};
        const controlSystems = data.control_systems || {};
        const gridServices = data.grid_services || {};
        const pneumaticSystems = data.pneumatic_systems || {};
        
        // Determine health status based on efficiency and faults
        const drivetrainHealthStatus = (mechanicalSystems.system_efficiency || 0) > 0.8 ? 'Normal' : 'Warning';
        const electricalHealthStatus = powerGen.grid_synchronized ? 'Normal' : 'Warning';
        const controlHealthStatus = (controlSystems.faults_active || 0) === 0 ? 'Normal' : 'Error';
        const pneumaticHealthStatus = (pneumaticSystems.average_efficiency || 0) > 0.7 ? 'Normal' : 'Warning';
        const gridHealthStatus = (gridServices.services_active || 0) > 0 ? 'Normal' : 'Normal';
        
        updateHealthStatus('drivetrainHealth', drivetrainHealthStatus);
        updateHealthStatus('electricalHealth', electricalHealthStatus);
        updateHealthStatus('controlHealth', controlHealthStatus);
        updateHealthStatus('pneumaticHealth', pneumaticHealthStatus);
        updateHealthStatus('gridServicesHealth', gridHealthStatus);
        
        // Update operational summary
        document.getElementById('simulationTime').textContent = (systemStatus.simulation_time || 0).toFixed(2);
        document.getElementById('totalEnergyGenerated').textContent = ((systemStatus.total_energy || 0) / 1000).toFixed(2);
        document.getElementById('gridSyncStatus').textContent = powerGen.grid_synchronized ? 'Yes' : 'No';
        document.getElementById('operationalStatus').textContent = systemStatus.operational ? 'Online' : 'Offline';
    }

    function updateHealthStatus(elementId, status) {
        const element = document.getElementById(elementId);
        element.textContent = status;
        element.className = `status-${status.toLowerCase()}`;
    }

    // Control system interaction handlers
    document.getElementById('emergencyStopBtn').onclick = function() {
        if (confirm('Are you sure you want to trigger emergency stop?')) {
            fetch('/control/trigger_emergency_stop', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ reason: 'Manual emergency stop from UI' })
            })
            .then(response => response.json())
            .then(data => {
                console.log('Emergency stop response:', data);
                alert(data.status === 'success' ? 'Emergency stop activated' : 'Emergency stop failed: ' + data.message);
            })
            .catch(error => {
                console.error('Error triggering emergency stop:', error);
                alert('Error triggering emergency stop');
            });
        }
    };

    document.getElementById('startupBtn').onclick = function() {
        fetch('/control/initiate_startup', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ reason: 'Manual startup from UI' })
        })        .then(response => response.json())
        .then(data => {
            console.log('Startup response:', data);
            alert(data.status === 'success' ? 'Startup sequence initiated' : 'Startup failed: ' + data.message);
        })
        .catch(error => {
            console.error('Error initiating startup:', error);
            alert('Error initiating startup');
        });
    };

    // ========================================================================================
    // PHASE 8: INDIVIDUAL SYSTEM UPDATE FUNCTIONS
    // ========================================================================================

    function updateDrivetrainStatus(data) {
        if (data && data.status === 'success' && data.data) {
            const dt = data.data;
            document.getElementById('drivetrainShaftSpeed').textContent = (dt.shaft_speed || 0).toFixed(1);
            document.getElementById('drivetrainFlywheelSpeed').textContent = (dt.flywheel_speed || 0).toFixed(1);
            document.getElementById('drivetrainChainTension').textContent = (dt.chain_tension || 0).toFixed(1);
            document.getElementById('drivetrainLoadTorque').textContent = (dt.generator_load_torque || 0).toFixed(1);
            document.getElementById('drivetrainEfficiency').textContent = ((dt.system_efficiency || 0) * 100).toFixed(1);
            document.getElementById('drivetrainPowerLoss').textContent = (dt.power_loss || 0).toFixed(1);
            document.getElementById('drivetrainInputEnergy').textContent = ((dt.input_energy || 0) / 3600000).toFixed(3);
            document.getElementById('drivetrainOutputEnergy').textContent = ((dt.output_energy || 0) / 3600000).toFixed(3);
        }
    }

    function updateElectricalStatus(data) {
        if (data && data.status === 'success' && data.data) {
            const es = data.data;
            document.getElementById('electricalPowerOutput').textContent = ((es.power_output || 0) / 1000).toFixed(1);
            document.getElementById('electricalVoltage').textContent = (es.voltage || 0).toFixed(1);
            document.getElementById('electricalCurrent').textContent = (es.current || 0).toFixed(1);
            document.getElementById('electricalFrequency').textContent = (es.frequency || 0).toFixed(1);
            document.getElementById('electricalGridVoltage').textContent = (es.grid_voltage || 0).toFixed(0);
            document.getElementById('electricalGridFrequency').textContent = (es.grid_frequency || 0).toFixed(1);
            document.getElementById('electricalPowerFactor').textContent = (es.grid_power_factor || 0).toFixed(2);
            document.getElementById('electricalEnergyGenerated').textContent = ((es.total_energy_generated || 0) / 3600000).toFixed(3);
        }
    }

    function updateControlStatus(data) {
        if (data && data.status === 'success' && data.data) {
            const cs = data.data;
            document.getElementById('controlMode').textContent = cs.mode || 'Unknown';
            document.getElementById('controlSetpoint').textContent = ((cs.setpoint || 0) / 1000).toFixed(1);
            document.getElementById('controlOutput').textContent = ((cs.output || 0) * 100).toFixed(1);
            
            if (cs.load_management) {
                document.getElementById('controlPowerError').textContent = ((cs.load_management.power_error || 0) / 1000).toFixed(1);
            }
            
            if (cs.fault_status) {
                document.getElementById('controlActiveFaults').textContent = cs.fault_status.active_faults ? cs.fault_status.active_faults.length : 0;
                document.getElementById('controlHealthScore').textContent = ((cs.fault_status.system_health || 1.0) * 100).toFixed(1);
            }
            
            if (cs.grid_stability) {
                document.getElementById('controlGridCompliance').textContent = cs.grid_stability.grid_compliance ? 'Yes' : 'No';
            }
            
            if (cs.performance) {
                document.getElementById('controlUptime').textContent = (cs.performance.uptime || 0).toFixed(1);
            }
        }
    }

    function updateGridServicesStatus(data) {
        if (data && data.status === 'success' && data.data) {
            const gs = data.data;
            document.getElementById('gridServiceType').textContent = gs.service_type || 'Energy';
            document.getElementById('gridBidPrice').textContent = (gs.bid_price || 0).toFixed(2);
            document.getElementById('gridRevenue').textContent = (gs.revenue || 0).toFixed(2);
            document.getElementById('gridCapacityFactor').textContent = ((gs.capacity_factor || 0) * 100).toFixed(1);
            document.getElementById('gridFrequencyResponse').textContent = gs.frequency_response_active ? 'Enabled' : 'Disabled';
            document.getElementById('gridVoltageSupport').textContent = gs.voltage_support_active ? 'Enabled' : 'Disabled';
            document.getElementById('gridReactivePower').textContent = ((gs.reactive_power || 0) / 1000).toFixed(1);
            document.getElementById('gridStability').textContent = gs.grid_stable ? 'Stable' : 'Unstable';
        }
    }

    function updateLossAnalysis(data) {
        if (data && data.status === 'success' && data.data) {
            const la = data.data;
            if (la.loss_breakdown) {
                const lb = la.loss_breakdown;
                document.getElementById('lossMechanical').textContent = (lb.mechanical_losses || 0).toFixed(1);
                document.getElementById('lossBearing').textContent = (lb.bearing_losses || 0).toFixed(1);
                document.getElementById('lossGearbox').textContent = (lb.gear_losses || 0).toFixed(1);
                document.getElementById('lossWindage').textContent = (lb.windage_losses || 0).toFixed(1);
                document.getElementById('lossGenerator').textContent = (lb.generator_losses || 0).toFixed(1);
                document.getElementById('lossPowerElectronics').textContent = (lb.power_electronics_losses || 0).toFixed(1);
                document.getElementById('lossTransformer').textContent = (lb.transformer_losses || 0).toFixed(1);
                document.getElementById('lossTotalLoss').textContent = (la.total_losses || 0).toFixed(1);
            }
        }
    }

    // Fetch and update individual system data
    function fetchDrivetrainData() {
        fetch('/data/drivetrain_status')
            .then(response => response.json())
            .then(data => updateDrivetrainStatus(data))
            .catch(error => console.error('Error fetching drivetrain data:', error));
    }

    function fetchElectricalData() {
        fetch('/data/electrical_status')
            .then(response => response.json())
            .then(data => updateElectricalStatus(data))
            .catch(error => console.error('Error fetching electrical data:', error));
    }

    function fetchControlData() {
        fetch('/data/control_status')
            .then(response => response.json())
            .then(data => updateControlStatus(data))
            .catch(error => console.error('Error fetching control data:', error));
    }

    function fetchGridServicesData() {
        fetch('/data/grid_services_status')
            .then(response => response.json())
            .then(data => updateGridServicesStatus(data))
            .catch(error => console.error('Error fetching grid services data:', error));
    }

    function fetchLossAnalysisData() {
        fetch('/data/enhanced_losses')
            .then(response => response.json())
            .then(data => updateLossAnalysis(data))
            .catch(error => console.error('Error fetching loss analysis data:', error));
    }

    // Start periodic updates for all advanced systems (every 3 seconds)
    function startAdvancedSystemUpdates() {
        setInterval(() => {
            fetchDrivetrainData();
            fetchElectricalData();
            fetchControlData();
            fetchGridServicesData();
            fetchLossAnalysisData();
        }, 3000);
    }

    // Initialize advanced system updates
    startAdvancedSystemUpdates();    // Start periodic updates for integrated systems (every 2 seconds to avoid overwhelming the server)
    setInterval(fetchIntegratedSystemsData, 2000);

    // ========================================================================================
    // PHYSICS MODULES CONTROLS AND DATA FETCHING (Chain, Fluid, Thermal)
    // ========================================================================================

    // Physics modules data fetching
    function fetchPhysicsData() {
        // Fetch comprehensive physics status
        fetch('/data/physics_status')
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    updatePhysicsUI(data.physics_status);
                }
            })
            .catch(error => console.error('Error fetching physics data:', error));
        
        // Fetch enhanced performance metrics
        fetch('/data/enhanced_performance')
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    updateEnhancedPerformanceUI(data.metrics);
                }
            })
            .catch(error => console.error('Error fetching enhanced performance:', error));
    }

    function updatePhysicsUI(physicsStatus) {
        const chainStatus = physicsStatus.chain_system || {};
        const fluidProperties = physicsStatus.fluid_system || {};
        const thermalProperties = physicsStatus.thermal_system || {};
        const h1Status = physicsStatus.h1_status || {};
        const h2Status = physicsStatus.h2_status || {};
        
        // Update physics status displays (add these to HTML if they don't exist)
        if (document.getElementById('chainTensionPhysics')) {
            document.getElementById('chainTensionPhysics').textContent = (chainStatus.tension || 0).toFixed(1);
        }
        if (document.getElementById('chainVelocity')) {
            document.getElementById('chainVelocity').textContent = (chainStatus.linear_velocity || 0).toFixed(2);
        }
        if (document.getElementById('fluidDensity')) {
            document.getElementById('fluidDensity').textContent = (fluidProperties.effective_density || 1000).toFixed(1);
        }
        if (document.getElementById('h1Status')) {
            document.getElementById('h1Status').textContent = h1Status.active ? 'Active' : 'Inactive';
        }
        if (document.getElementById('h2Status')) {
            document.getElementById('h2Status').textContent = h2Status.active ? 'Active' : 'Inactive';
        }
        if (document.getElementById('buoyancyEnhancement')) {
            document.getElementById('buoyancyEnhancement').textContent = (h2Status.buoyancy_enhancement * 100 || 0).toFixed(1);
        }
    }

    function updateEnhancedPerformanceUI(metrics) {
        if (document.getElementById('h1Enhancement')) {
            document.getElementById('h1Enhancement').textContent = (metrics.h1_buoyancy_enhancement * 100 || 0).toFixed(1);
        }
        if (document.getElementById('h2Enhancement')) {
            document.getElementById('h2Enhancement').textContent = (metrics.h2_thermal_enhancement * 100 || 0).toFixed(1);
        }
        if (document.getElementById('totalEnhancement')) {
            document.getElementById('totalEnhancement').textContent = (metrics.total_physics_enhancement * 100 || 0).toFixed(1);
        }
    }

    // Physics control functions
    window.controlH1Nanobubbles = function() {
        const active = document.getElementById('h1Active')?.checked || false;
        const bubbleFraction = parseFloat(document.getElementById('bubbleFraction')?.value || 0.05);
        const dragReduction = parseFloat(document.getElementById('dragReduction')?.value || 0.1);
        
        fetch('/control/h1_nanobubbles', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                active: active,
                bubble_fraction: bubbleFraction,
                drag_reduction: dragReduction
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                console.log('H1 nanobubbles updated:', data);
            } else {
                console.error('H1 control error:', data.message);
            }
        })
        .catch(error => console.error('Error controlling H1:', error));
    };

    window.controlH2Thermal = function() {
        const active = document.getElementById('h2Active')?.checked || false;
        const efficiency = parseFloat(document.getElementById('h2Efficiency')?.value || 0.8);
        const buoyancyBoost = parseFloat(document.getElementById('buoyancyBoost')?.value || 0.05);
        const compressionImprovement = parseFloat(document.getElementById('compressionImprovement')?.value || 0.15);
        
        fetch('/control/h2_thermal', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                active: active,
                efficiency: efficiency,
                buoyancy_boost: buoyancyBoost,
                compression_improvement: compressionImprovement
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                console.log('H2 thermal updated:', data);
            } else {
                console.error('H2 control error:', data.message);
            }
        })
        .catch(error => console.error('Error controlling H2:', error));
    };

    window.setWaterTemperature = function() {
        const temperature = parseFloat(document.getElementById('waterTemperature')?.value || 20.0);
        
        fetch('/control/water_temperature', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ temperature: temperature })
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                console.log('Water temperature updated:', data);
            } else {
                console.error('Temperature control error:', data.message);
            }
        })
        .catch(error => console.error('Error setting temperature:', error));
    };

    window.enableEnhancedPhysics = function() {
        fetch('/control/enhanced_physics', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ enable: true, h1_active: true, h2_active: true })
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                console.log('Enhanced physics enabled:', data);
                // Update UI checkboxes
                if (document.getElementById('h1Active')) document.getElementById('h1Active').checked = true;
                if (document.getElementById('h2Active')) document.getElementById('h2Active').checked = true;
            } else {
                console.error('Enhanced physics error:', data.message);
            }
        })
        .catch(error => console.error('Error enabling enhanced physics:', error));
    };

    window.disableEnhancedPhysics = function() {
        fetch('/control/enhanced_physics', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ enable: false })
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                console.log('Enhanced physics disabled:', data);
                // Update UI checkboxes
                if (document.getElementById('h1Active')) document.getElementById('h1Active').checked = false;
                if (document.getElementById('h2Active')) document.getElementById('h2Active').checked = false;
            } else {
                console.error('Enhanced physics error:', data.message);
            }
        })
        .catch(error => console.error('Error disabling enhanced physics:', error));
    };

    // Start periodic physics data fetching
    setInterval(fetchPhysicsData, 3000); // Update every 3 seconds

    // ========================================================================================
    // END PHYSICS MODULES CONTROLS AND DATA FETCHING
    // ========================================================================================

    // ========================================================================================
    // END PHASE 8: INTEGRATED SYSTEMS DATA FETCHING AND UI UPDATES
    // ========================================================================================
});
