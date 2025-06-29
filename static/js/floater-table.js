/**
 * Floater Table Manager for KPP Simulator
 * Handles dynamic floater state display with physics effects
 * Stage 3.4 Implementation
 */

class FloaterTableManager {
    constructor() {
        this.tableBody = null;
        this.floaterData = [];
        this.physicsData = {};
        this.updateCounter = 0;
        
        this.initializeTable();
        console.log('✅ FloaterTableManager initialized');
    }
    
    /**
     * Initialize the floater table structure
     */
    initializeTable() {
        const table = document.getElementById('floaterTable');
        if (!table) {
            console.error('❌ Floater table not found');
            return;
        }
        
        // Get or create table body
        this.tableBody = table.querySelector('tbody');
        if (!this.tableBody) {
            this.tableBody = document.createElement('tbody');
            table.appendChild(this.tableBody);
        }
        
        // Initialize with empty rows
        this.createEmptyRows(8); // Default 8 floaters
        
        console.log('✅ Floater table structure initialized');
    }
    
    /**
     * Create empty table rows for floaters
     */
    createEmptyRows(numFloaters) {
        this.tableBody.innerHTML = ''; // Clear existing rows
        
        for (let i = 0; i < numFloaters; i++) {
            const row = this.createFloaterRow(i);
            this.tableBody.appendChild(row);
        }
        
        console.log(`✅ Created ${numFloaters} floater table rows`);
    }
    
    /**
     * Create a single floater table row
     */
    createFloaterRow(index) {
        const row = document.createElement('tr');
        row.id = `floater-row-${index}`;
        row.className = 'floater-row';
        
        // Create cells with proper IDs for easy updates
        const cells = [
            { class: 'floater-id', content: `F${index + 1}` },
            { class: 'position', content: '0.00', id: `pos-${index}` },
            { class: 'velocity', content: '0.00', id: `vel-${index}` },
            { class: 'base-buoyancy', content: '0.0', id: `buoy-${index}` },
            { class: 'drag-force', content: '0.0', id: `drag-${index}` },
            { class: 'h1-effect', content: '0.0', id: `h1-${index}` },
            { class: 'h2-effect', content: '0.0', id: `h2-${index}` },
            { class: 'h3-pulse', content: '0.0', id: `h3-${index}` },
            { class: 'net-force', content: '0.0', id: `net-${index}` },
            { class: 'state', content: 'Idle', id: `state-${index}` },
            { class: 'physics-status', content: '---', id: `physics-${index}` }
        ];
        
        cells.forEach((cellData, cellIndex) => {
            const cell = document.createElement('td');
            cell.className = cellData.class;
            cell.textContent = cellData.content;
            if (cellData.id) {
                cell.id = cellData.id;
            }
            row.appendChild(cell);
        });
        
        return row;
    }
    
    /**
     * Update table with new floater data
     */
    updateTable(simulationData) {
        if (!simulationData || !this.tableBody) return;
        
        // Extract floater data from simulation
        const floaters = simulationData.floaters || [];
        const physicsForces = simulationData.physics_forces || {};
        const physicsStatus = simulationData.physics_status || {};
        
        // Update floater count if needed
        if (floaters.length !== this.tableBody.children.length) {
            this.createEmptyRows(floaters.length);
        }
        
        // Update each floater row
        floaters.forEach((floater, index) => {
            this.updateFloaterRow(index, floater, physicsForces, physicsStatus);
        });
        
        // Increment update counter for performance monitoring
        this.updateCounter++;
        if (this.updateCounter % 100 === 0) {
            console.log(`📊 Floater table updated ${this.updateCounter} times`);
        }
    }
    
    /**
     * Update a single floater row with new data
     */
    updateFloaterRow(index, floaterData, physicsForces, physicsStatus) {
        // Get the individual forces for this floater
        const h1Force = this.getFloaterPhysicsForce(physicsForces.h1_forces || [], index);
        const h2Force = this.getFloaterPhysicsForce(physicsForces.h2_forces || [], index);
        const h3Force = this.getFloaterPhysicsForce(physicsForces.h3_forces || [], index);
        
        // Calculate net force
        const baseForce = floaterData.buoyancy || 0;
        const dragForce = floaterData.drag || 0;
        const netForce = baseForce - dragForce + h1Force + h2Force + h3Force;
        
        // Update position (with bounds checking)
        const position = this.formatValue(floaterData.position || 0, 2);
        this.updateCell(`pos-${index}`, position, this.getPositionColor(floaterData.position || 0));
        
        // Update velocity (with direction indication)
        const velocity = this.formatValue(floaterData.velocity || 0, 3);
        this.updateCell(`vel-${index}`, velocity, this.getVelocityColor(floaterData.velocity || 0));
        
        // Update forces
        this.updateCell(`buoy-${index}`, this.formatValue(baseForce, 1));
        this.updateCell(`drag-${index}`, this.formatValue(Math.abs(dragForce), 1), '#dc3545');
        this.updateCell(`h1-${index}`, this.formatValue(h1Force, 1), this.getPhysicsColor(h1Force, physicsStatus.h1_active));
        this.updateCell(`h2-${index}`, this.formatValue(h2Force, 1), this.getPhysicsColor(h2Force, physicsStatus.h2_active));
        this.updateCell(`h3-${index}`, this.formatValue(h3Force, 1), this.getPhysicsColor(h3Force, physicsStatus.h3_active));
        this.updateCell(`net-${index}`, this.formatValue(netForce, 1), this.getNetForceColor(netForce));
        
        // Update state
        const state = this.determineFloaterState(floaterData, physicsStatus);
        this.updateCell(`state-${index}`, state, this.getStateColor(state));
        
        // Update physics status
        const physicsInfo = this.generatePhysicsStatus(physicsStatus, h1Force, h2Force, h3Force);
        this.updateCell(`physics-${index}`, physicsInfo);
    }
    
    /**
     * Update a single table cell with color coding
     */
    updateCell(cellId, value, color = null) {
        const cell = document.getElementById(cellId);
        if (cell) {
            cell.textContent = value;
            if (color) {
                cell.style.color = color;
                cell.style.fontWeight = '600';
            } else {
                cell.style.color = '';
                cell.style.fontWeight = '';
            }
        }
    }
    
    /**
     * Get physics force for specific floater
     */
    getFloaterPhysicsForce(forceArray, index) {
        if (Array.isArray(forceArray) && index < forceArray.length) {
            return forceArray[index] || 0;
        }
        return 0;
    }
    
    /**
     * Determine floater state based on data
     */
    determineFloaterState(floaterData, physicsStatus) {
        const position = floaterData.position || 0;
        const velocity = floaterData.velocity || 0;
        const isFilled = floaterData.is_filled || false;
        
        if (Math.abs(velocity) < 0.01) {
            return 'Idle';
        } else if (velocity > 0) {
            if (position > 10) {
                return 'Ascending';
            } else {
                return 'Rising';
            }
        } else {
            if (position < -10) {
                return 'Descending';
            } else {
                return 'Sinking';
            }
        }
    }
    
    /**
     * Generate physics status indicator
     */
    generatePhysicsStatus(physicsStatus, h1Force, h2Force, h3Force) {
        const active = [];
        
        if (physicsStatus.h1_active && Math.abs(h1Force) > 0.1) {
            active.push('H1');
        }
        if (physicsStatus.h2_active && Math.abs(h2Force) > 0.1) {
            active.push('H2');
        }
        if (physicsStatus.h3_active && Math.abs(h3Force) > 0.1) {
            active.push('H3');
        }
        
        return active.length > 0 ? active.join('+') : '---';
    }
    
    /**
     * Format numerical values for display
     */
    formatValue(value, decimals = 2) {
        if (typeof value !== 'number' || isNaN(value)) {
            return '0.00';
        }
        return value.toFixed(decimals);
    }
    
    /**
     * Get color based on position (depth-based coloring)
     */
    getPositionColor(position) {
        if (position > 15) return '#28a745';      // Deep green for high positions
        if (position > 5) return '#17a2b8';      // Blue for medium positions  
        if (position > -5) return '#6c757d';     // Gray for neutral
        if (position > -15) return '#fd7e14';    // Orange for low positions
        return '#dc3545';                        // Red for very low positions
    }
    
    /**
     * Get color based on velocity (direction-based coloring)
     */
    getVelocityColor(velocity) {
        if (Math.abs(velocity) < 0.01) return '#6c757d';  // Gray for stationary
        return velocity > 0 ? '#28a745' : '#dc3545';      // Green up, red down
    }
    
    /**
     * Get color for physics forces
     */
    getPhysicsColor(force, isActive) {
        if (!isActive) return '#6c757d';           // Gray when inactive
        if (Math.abs(force) < 0.1) return '#6c757d';  // Gray for negligible force
        return force > 0 ? '#28a745' : '#dc3545'; // Green positive, red negative
    }
    
    /**
     * Get color for net force
     */
    getNetForceColor(netForce) {
        if (Math.abs(netForce) < 1) return '#6c757d';     // Gray for small forces
        if (netForce > 50) return '#28a745';              // Strong green for high upward
        if (netForce > 0) return '#17a2b8';               // Blue for moderate upward
        if (netForce > -50) return '#fd7e14';             // Orange for moderate downward
        return '#dc3545';                                 // Red for strong downward
    }
    
    /**
     * Get color for floater state
     */
    getStateColor(state) {
        const stateColors = {
            'Idle': '#6c757d',
            'Rising': '#28a745',
            'Ascending': '#17a2b8',
            'Sinking': '#fd7e14',
            'Descending': '#dc3545'
        };
        return stateColors[state] || '#6c757d';
    }
    
    /**
     * Highlight specific floaters (for debugging or analysis)
     */
    highlightFloater(index, highlight = true) {
        const row = document.getElementById(`floater-row-${index}`);
        if (row) {
            if (highlight) {
                row.style.backgroundColor = '#fff3cd';
                row.style.border = '2px solid #ffc107';
            } else {
                row.style.backgroundColor = '';
                row.style.border = '';
            }
        }
    }
    
    /**
     * Sort table by column (optional feature)
     */
    sortTableByColumn(columnIndex, ascending = true) {
        const rows = Array.from(this.tableBody.children);
        
        rows.sort((a, b) => {
            const aValue = parseFloat(a.children[columnIndex].textContent) || 0;
            const bValue = parseFloat(b.children[columnIndex].textContent) || 0;
            
            return ascending ? aValue - bValue : bValue - aValue;
        });
        
        // Re-append sorted rows
        rows.forEach(row => this.tableBody.appendChild(row));
        
        console.log(`📊 Table sorted by column ${columnIndex}, ascending: ${ascending}`);
    }
    
    /**
     * Export table data as CSV
     */
    exportToCSV() {
        const headers = [
            'Floater', 'Position(m)', 'Velocity(m/s)', 'Base Buoyancy(N)', 
            'Drag Force(N)', 'H1 Effect(N)', 'H2 Effect(N)', 'H3 Pulse(N)', 
            'Net Force(N)', 'State', 'Physics Status'
        ];
        
        let csv = headers.join(',') + '\\n';
        
        Array.from(this.tableBody.children).forEach(row => {
            const rowData = Array.from(row.children).map(cell => 
                cell.textContent.replace(',', ';')  // Replace commas to avoid CSV issues
            );
            csv += rowData.join(',') + '\\n';
        });
        
        return csv;
    }
    
    /**
     * Get table statistics
     */
    getTableStats() {
        const rows = Array.from(this.tableBody.children);
        const stats = {
            totalFloaters: rows.length,
            activeFloaters: 0,
            averageNetForce: 0,
            physicsActiveCount: { h1: 0, h2: 0, h3: 0 }
        };
        
        let totalNetForce = 0;
        
        rows.forEach((row, index) => {
            const velocity = parseFloat(document.getElementById(`vel-${index}`)?.textContent || 0);
            const netForce = parseFloat(document.getElementById(`net-${index}`)?.textContent || 0);
            const physicsStatus = document.getElementById(`physics-${index}`)?.textContent || '';
            
            if (Math.abs(velocity) > 0.01) {
                stats.activeFloaters++;
            }
            
            totalNetForce += netForce;
            
            if (physicsStatus.includes('H1')) stats.physicsActiveCount.h1++;
            if (physicsStatus.includes('H2')) stats.physicsActiveCount.h2++;
            if (physicsStatus.includes('H3')) stats.physicsActiveCount.h3++;
        });
        
        stats.averageNetForce = totalNetForce / rows.length;
        
        return stats;
    }
    
    /**
     * Clear all table data
     */
    clearTable() {
        if (this.tableBody) {
            Array.from(this.tableBody.children).forEach((row, index) => {
                // Reset all cells to default values
                this.updateCell(`pos-${index}`, '0.00');
                this.updateCell(`vel-${index}`, '0.00');
                this.updateCell(`buoy-${index}`, '0.0');
                this.updateCell(`drag-${index}`, '0.0');
                this.updateCell(`h1-${index}`, '0.0');
                this.updateCell(`h2-${index}`, '0.0');
                this.updateCell(`h3-${index}`, '0.0');
                this.updateCell(`net-${index}`, '0.0');
                this.updateCell(`state-${index}`, 'Idle');
                this.updateCell(`physics-${index}`, '---');
            });
        }
        
        console.log('✅ Floater table cleared');
    }
}

// Initialize floater table manager when DOM is ready
let floaterTableManager = null;

document.addEventListener('DOMContentLoaded', function() {
    floaterTableManager = new FloaterTableManager();
    
    // Make it globally accessible
    window.floaterTableManager = floaterTableManager;
});

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = FloaterTableManager;
}
