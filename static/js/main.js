document.addEventListener('DOMContentLoaded', function() {
    // Chart.js setup
    let torqueChart, powerChart;
    const torqueCtx = document.getElementById('torqueChart').getContext('2d');
    const powerCtx = document.getElementById('powerChart').getContext('2d');

    torqueChart = new Chart(torqueCtx, {
        type: 'line',
        data: { labels: [], datasets: [{ label: 'Torque', data: [], borderColor: 'blue', fill: false }] },
        options: { responsive: true, scales: { x: { title: { display: true, text: 'Time (s)' } }, y: { title: { display: true, text: 'Torque (Nm)' } } } }
    });
    // When creating the chart, update the label and y-axis title to kW
    powerChart = new Chart(powerCtx, {
        type: 'line',
        data: { labels: [], datasets: [{ label: 'Power', data: [], borderColor: 'green', fill: false }] },
        options: { responsive: true, scales: { x: { title: { display: true, text: 'Time (s)' } }, y: { title: { display: true, text: 'Power (kW)' } } } }
    });

    function updateCharts() {
        fetch('/data/history').then(r => r.json()).then(data => {
            torqueChart.data.labels = data.time;
            torqueChart.data.datasets[0].data = data.torque;
            torqueChart.update();
            powerChart.data.labels = data.time;
            // Convert power to kW for the chart
            powerChart.data.datasets[0].data = data.power.map(p => p / 1000);
            powerChart.update();
        });
    }

    function updateSummaryAndFloaters() {
        fetch('/data/summary').then(r => r.json()).then(data => {
            document.getElementById('summaryTime').textContent = data.time ? Number(data.time).toFixed(2) : '0.00';
            document.getElementById('summaryTorque').textContent = data.torque ? Number(data.torque).toFixed(2) : '0.00';
            // Show power in kW with two decimals
            const powerKW = data.power ? (data.power / 1000).toFixed(2) : '0.00';
            document.getElementById('summaryPower').textContent = powerKW;
            document.getElementById('summaryVelocity').textContent = data.velocity ? Number(data.velocity).toFixed(2) : '0.00';
            // Update floaters table
            if (data.floaters) {
                const tbody = document.getElementById('floatersTableBody');
                tbody.innerHTML = '';
                data.floaters.forEach(f => {
                    const row = document.createElement('tr');
                    row.innerHTML = `
                        <td>${f.id}</td>
                        <td>${f.position ? Number(f.position).toFixed(2) : '0.00'}</td>
                        <td>${f.velocity ? Number(f.velocity).toFixed(2) : '0.00'}</td>
                        <td>${f.state}</td>
                        <td>${f.force ? Number(f.force).toFixed(2) : '0.00'}</td>
                        <td>${f.buoyancy ? Number(f.buoyancy).toFixed(2) : '0.00'}</td>
                        <td>${f.gravity ? Number(f.gravity).toFixed(2) : '0.00'}</td>
                        <td>${f.drag ? Number(f.drag).toFixed(2) : '0.00'}</td>
                        <td>${f.net_force ? Number(f.net_force).toFixed(2) : '0.00'}</td>
                    `;
                    tbody.appendChild(row);
                });
            }
        });
    }

    // Poll for updates every second
    setInterval(function() {
        updateCharts();
        updateSummaryAndFloaters();
    }, 1000);

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
    };
    document.getElementById('stepBtn').onclick = function() {
        fetch('/step', { method: 'POST' });
    };
    document.getElementById('paramsForm').onsubmit = function(e) {
        e.preventDefault();
        const formData = new FormData(this);
        const params = {};
        for (const [key, value] of formData.entries()) {
            params[key] = isNaN(value) ? value : Number(value);
        }
        fetch('/update_params', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(params)
        });
    };
});
