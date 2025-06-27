/**
 * Parameter Manager for KPP Simulator
 * Handles unified parameter updates, validation, and UI synchronization
 * Stage 3.2 Implementation
 */

class ParameterManager {
    constructor() {
        // Initialize parameter state and event listeners
        this.parameters = {};
        this.updateQueue = [];
        this.isUpdating = false;
        this.debounceTimer = null;
        
        this.initializeEventListeners();
        this.loadParameterDefaults();
        
        console.log('✅ ParameterManager initialized');
    }
    
    /**
     * Initialize all parameter control event listeners
     */
    initializeEventListeners() {
        // Get the main form
        const form = document.getElementById('paramsForm');
        if (!form) {
            console.error('❌ Parameter form not found');
            return;
        }
        
        // Handle form submission
        form.addEventListener('submit', (e) => {
            e.preventDefault();
            this.submitAllParameters();
        });
        
        // Handle individual parameter changes
        this.setupRangeSliders();
        this.setupCheckboxes();
        this.setupNumberInputs();
        
        console.log('✅ Parameter event listeners initialized');
    }
    
    /**
     * Setup range slider controls with real-time value display
     */
    setupRangeSliders() {
        const sliders = [
            { id: 'nanobubble_fraction', display: 'nanobubble_fraction_val', format: 'percentage' },
            { id: 'drag_reduction_factor', display: 'drag_reduction_factor_val', format: 'percentage' },
            { id: 'thermal_efficiency', display: 'thermal_efficiency_val', format: 'percentage' },
            { id: 'pulse_duty_cycle', display: 'pulse_duty_cycle_val', format: 'percentage' }
        ];
        
        sliders.forEach(slider => {
            const input = document.getElementById(slider.id);
            const display = document.getElementById(slider.display);
            
            if (input && display) {
                // Update display on input
                input.addEventListener('input', (e) => {
                    const value = parseFloat(e.target.value);
                    display.textContent = this.formatValue(value, slider.format);
                    
                    // Queue parameter update with debouncing
                    this.queueParameterUpdate(slider.id, value);
                });
                
                // Initialize display
                const initialValue = parseFloat(input.value);
                display.textContent = this.formatValue(initialValue, slider.format);
                
                console.log(`✅ Range slider ${slider.id} initialized`);
            }
        });
    }
    
    /**
     * Setup checkbox controls for enabling/disabling physics systems
     */
    setupCheckboxes() {
        const checkboxes = [
            'h1_enabled',
            'h2_enabled', 
            'h3_enabled',
            'pulse_enabled'
        ];
        
        checkboxes.forEach(id => {
            const checkbox = document.getElementById(id);
            if (checkbox) {
                checkbox.addEventListener('change', (e) => {
                    const value = e.target.checked;
                    this.queueParameterUpdate(id, value);
                    
                    // Update physics status indicators
                    this.updatePhysicsStatus(id, value);
                    
                    console.log(`📋 ${id}: ${value ? 'enabled' : 'disabled'}`);
                });
                
                console.log(`✅ Checkbox ${id} initialized`);
            }
        });
    }
    
    /**
     * Setup number input controls
     */
    setupNumberInputs() {
        const numberInputs = [
            'bubble_generator_power',
            'surface_area',
            'water_temperature',
            'pulse_duration',
            'coast_duration'
        ];
        
        numberInputs.forEach(id => {
            const input = document.getElementById(id);
            if (input) {
                input.addEventListener('change', (e) => {
                    const value = parseFloat(e.target.value);
                    if (!isNaN(value)) {
                        this.queueParameterUpdate(id, value);
                        console.log(`🔢 ${id}: ${value}`);
                    }
                });
                
                console.log(`✅ Number input ${id} initialized`);
            }
        });
    }
    
    /**
     * Queue a parameter update with debouncing to avoid excessive API calls
     */
    queueParameterUpdate(paramName, value) {
        // Store the parameter change
        this.parameters[paramName] = value;
        
        // Clear existing timer
        if (this.debounceTimer) {
            clearTimeout(this.debounceTimer);
        }
        
        // Set new timer for batched update
        this.debounceTimer = setTimeout(() => {
            this.sendParameterUpdates();
        }, 300); // 300ms debounce
    }
    
    /**
     * Send accumulated parameter updates to backend
     */
    async sendParameterUpdates() {
        if (this.isUpdating || Object.keys(this.parameters).length === 0) {
            return;
        }
        
        this.isUpdating = true;
        const updatedParams = { ...this.parameters };
        this.parameters = {}; // Clear queue
        
        try {
            console.log('📤 Sending parameter updates:', updatedParams);
            
            const response = await fetch('/set_params', {
                method: 'PATCH',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(updatedParams)
            });
            
            const result = await response.json();
            
            if (response.ok) {
                console.log('✅ Parameters updated successfully:', result);
                this.showUpdateStatus('success', 'Parameters updated');
                
                // Update parameter state
                if (result.updated_parameters) {
                    this.handleParameterUpdateResponse(result.updated_parameters);
                }
            } else {
                console.error('❌ Parameter update failed:', result);
                this.showUpdateStatus('error', result.error || 'Update failed');
            }
            
        } catch (error) {
            console.error('❌ Parameter update error:', error);
            this.showUpdateStatus('error', 'Network error');
        } finally {
            this.isUpdating = false;
        }
    }
    
    /**
     * Submit all form parameters at once
     */
    async submitAllParameters() {
        const form = document.getElementById('paramsForm');
        if (!form) return;
        
        const formData = new FormData(form);
        const allParams = {};
        
        // Convert FormData to object
        for (const [key, value] of formData.entries()) {
            // Handle different input types
            const element = form.elements[key];
            if (element) {
                if (element.type === 'checkbox') {
                    allParams[key] = element.checked;
                } else if (element.type === 'number' || element.type === 'range') {
                    allParams[key] = parseFloat(value) || 0;
                } else {
                    allParams[key] = value;
                }
            }
        }
        
        try {
            console.log('📤 Submitting all parameters:', allParams);
            
            const response = await fetch('/set_params', {
                method: 'PATCH',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(allParams)
            });
            
            const result = await response.json();
            
            if (response.ok) {
                console.log('✅ All parameters submitted successfully');
                this.showUpdateStatus('success', `Updated ${Object.keys(allParams).length} parameters`);
            } else {
                console.error('❌ Parameter submission failed:', result);
                this.showUpdateStatus('error', result.error || 'Submission failed');
            }
            
        } catch (error) {
            console.error('❌ Parameter submission error:', error);
            this.showUpdateStatus('error', 'Network error');
        }
    }
    
    /**
     * Load default parameters from backend
     */
    async loadParameterDefaults() {
        try {
            const response = await fetch('/get_output_schema');
            const schema = await response.json();
            
            if (response.ok && schema.default_parameters) {
                console.log('✅ Loaded default parameters:', schema.default_parameters);
                // Could populate form with defaults here if needed
            }
        } catch (error) {
            console.warn('⚠️ Could not load default parameters:', error);
        }
    }
    
    /**
     * Handle successful parameter update response
     */
    handleParameterUpdateResponse(updatedParams) {
        // Update any UI elements that need to reflect the new values
        Object.entries(updatedParams).forEach(([key, value]) => {
            const element = document.getElementById(key);
            if (element) {
                if (element.type === 'range') {
                    // Update range slider display
                    const displayId = key + '_val';
                    const display = document.getElementById(displayId);
                    if (display) {
                        display.textContent = this.formatValue(value, 'percentage');
                    }
                }
            }
        });
    }
    
    /**
     * Update physics status indicators
     */
    updatePhysicsStatus(systemId, enabled) {
        const statusMap = {
            'h1_enabled': { lightId: 'h1-light', valueId: 'h1-value', label: 'Nanobubbles' },
            'h2_enabled': { lightId: 'h2-light', valueId: 'h2-value', label: 'Thermal' },
            'h3_enabled': { lightId: 'h3-light', valueId: 'h3-value', label: 'Pulse Control' }
        };
        
        const status = statusMap[systemId];
        if (status) {
            const light = document.getElementById(status.lightId);
            const value = document.getElementById(status.valueId);
            
            if (light && value) {
                if (enabled) {
                    light.classList.add('active');
                    light.classList.remove('inactive');
                    value.textContent = 'Active';
                } else {
                    light.classList.remove('active');
                    light.classList.add('inactive');
                    value.textContent = 'Inactive';
                }
            }
        }
    }
    
    /**
     * Show parameter update status to user
     */
    showUpdateStatus(type, message) {
        // Create or update status message
        let statusDiv = document.getElementById('parameter-status');
        if (!statusDiv) {
            statusDiv = document.createElement('div');
            statusDiv.id = 'parameter-status';
            statusDiv.style.cssText = `
                position: fixed;
                top: 60px;
                right: 10px;
                padding: 0.5em 1em;
                border-radius: 4px;
                font-weight: bold;
                z-index: 1000;
                transition: opacity 0.3s ease;
            `;
            document.body.appendChild(statusDiv);
        }
        
        // Set style based on type
        if (type === 'success') {
            statusDiv.style.backgroundColor = '#d4edda';
            statusDiv.style.color = '#155724';
            statusDiv.style.border = '1px solid #c3e6cb';
        } else {
            statusDiv.style.backgroundColor = '#f8d7da';
            statusDiv.style.color = '#721c24';
            statusDiv.style.border = '1px solid #f5c6cb';
        }
        
        statusDiv.textContent = message;
        statusDiv.style.opacity = '1';
        
        // Auto-hide after 3 seconds
        setTimeout(() => {
            statusDiv.style.opacity = '0';
        }, 3000);
    }
    
    /**
     * Format values for display
     */
    formatValue(value, format) {
        switch (format) {
            case 'percentage':
                return `${(value * 100).toFixed(1)}%`;
            case 'decimal':
                return value.toFixed(3);
            case 'integer':
                return Math.round(value).toString();
            default:
                return value.toString();
        }
    }
    
    /**
     * Get current parameter values from form
     */
    getCurrentParameters() {
        const form = document.getElementById('paramsForm');
        if (!form) return {};
        
        const params = {};
        const formData = new FormData(form);
        
        for (const [key, value] of formData.entries()) {
            const element = form.elements[key];
            if (element) {
                if (element.type === 'checkbox') {
                    params[key] = element.checked;
                } else if (element.type === 'number' || element.type === 'range') {
                    params[key] = parseFloat(value) || 0;
                } else {
                    params[key] = value;
                }
            }
        }
        
        return params;
    }
    
    /**
     * Reset all parameters to defaults
     */
    async resetToDefaults() {
        try {
            const response = await fetch('/get_output_schema');
            const schema = await response.json();
            
            if (response.ok && schema.default_parameters) {
                // Update form with default values
                const form = document.getElementById('paramsForm');
                if (form) {
                    Object.entries(schema.default_parameters).forEach(([key, value]) => {
                        const element = form.elements[key];
                        if (element) {
                            if (element.type === 'checkbox') {
                                element.checked = value;
                            } else {
                                element.value = value;
                            }
                            
                            // Trigger change event to update displays
                            element.dispatchEvent(new Event('change'));
                        }
                    });
                }
                
                console.log('✅ Reset to default parameters');
                this.showUpdateStatus('success', 'Reset to defaults');
            }
        } catch (error) {
            console.error('❌ Reset failed:', error);
            this.showUpdateStatus('error', 'Reset failed');
        }
    }
}

// Initialize parameter manager when DOM is ready
let parameterManager = null;

document.addEventListener('DOMContentLoaded', function() {
    parameterManager = new ParameterManager();
    
    // Make it globally accessible for debugging
    window.paramManager = parameterManager;
});

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ParameterManager;
}
