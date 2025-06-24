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
            addData(effChart, timeFormatted, data.efficiency || 0);
            
            // Update pulse chart (multiple datasets)
            if (pulseChart.data.labels.length > 100) {
                pulseChart.data.labels.shift();
                pulseChart.data.datasets.forEach((ds) => ds.data.shift());
            }
            pulseChart.data.labels.push(timeFormatted);
            pulseChart.data.datasets[0].data.push(data.base_torque || 0);
            pulseChart.data.datasets[1].data.push(data.pulse_torque || 0);
            pulseChart.update('none');
        }

        // Update summary
        updateSummary(data);

        // Update per-floater state table (GuideV3.md requirement)
        if (data.floaters) {
            updateFloaterTable(data.floaters);
        }
    }

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
        document.getElementById('summaryVelocity').textContent = data.velocity ? Number(data.velocity).toFixed(2) : '0.00';
        
        // Pulse metrics
        document.getElementById('baseTorque').textContent = data.base_torque ? Number(data.base_torque).toFixed(2) : '0.00';
        document.getElementById('pulseTorque').textContent = data.pulse_torque ? Number(data.pulse_torque).toFixed(2) : '0.00';
        document.getElementById('pulseCount').textContent = data.pulse_count || '0';
        document.getElementById('clutchStatus').textContent = data.clutch_engaged ? 'Engaged' : 'Disengaged';
        
        // Mechanical status
        document.getElementById('chainSpeed').textContent = data.chain_speed ? Number(data.chain_speed).toFixed(2) : '0.00';
        document.getElementById('flywheelSpeed').textContent = data.flywheel_speed ? Number(data.flywheel_speed).toFixed(2) : '0.00';
        
        // Count active pulses
        let activePulses = 0;
        if (data.floaters) {
            activePulses = data.floaters.filter(f => f.is_pulsing).length;
        }
        document.getElementById('activePulses').textContent = activePulses;
        
        // Calculate efficiency (simplified)
        const efficiency = data.power && data.torque ? (data.power / (data.torque * 10)) * 100 : 0;
        document.getElementById('efficiency').textContent = efficiency.toFixed(2);
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

    // Initialize SSE connection
    connectSSE();
});
