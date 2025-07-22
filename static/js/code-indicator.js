/**
 * Code Indicator - Shows live deployment status
 */

// Create and inject the code indicator HTML
function createCodeIndicator() {
    const indicator = document.createElement('div');
    indicator.className = 'code-indicator';
    indicator.id = 'codeIndicator';
    indicator.innerHTML = `
        <div class="version">Loading...</div>
        <div class="implementation"></div>
        <div class="features"></div>
        <div class="build"></div>
        <div class="deployed"></div>
    `;
    document.body.appendChild(indicator);
}

// Update the indicator with current code status
async function updateCodeIndicator() {
    try {
        const response = await fetch('/api/v1/code-status');
        const status = await response.json();
        
        const indicator = document.getElementById('codeIndicator');
        if (!indicator) return;
        
        indicator.querySelector('.version').textContent = status.version;
        indicator.querySelector('.implementation').textContent = status.implementation;
        indicator.querySelector('.build').textContent = `Build: ${status.build_id}`;
        indicator.querySelector('.deployed').textContent = `Deployed: ${status.deployment_display}`;
        
        // Update features
        const featuresDiv = indicator.querySelector('.features');
        featuresDiv.innerHTML = status.feature_summary.map(f => `<div>${f}</div>`).join('');
        
    } catch (error) {
        console.error('Failed to update code indicator:', error);
        const indicator = document.getElementById('codeIndicator');
        if (indicator) {
            indicator.style.display = 'none';
        }
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    createCodeIndicator();
    updateCodeIndicator();
    
    // Refresh every 30 seconds
    setInterval(updateCodeIndicator, 30000);
});