// Constitutional Web Interface JavaScript
// Handles Enter key functionality and interactions

// Constitutional Enter Key functionality
function handleEnterKey(event, buttonId) {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        document.getElementById(buttonId).click();
    }
}

// Submit query form
document.addEventListener('DOMContentLoaded', function() {
    const queryForm = document.getElementById('query-form');
    if (queryForm) {
        queryForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const queryInput = document.getElementById('query-input');
            const responseArea = document.getElementById('response-area');
            const responseContent = document.getElementById('response-content');
            const submitButton = document.getElementById('submit-query');
            
            // Disable form during submission
            queryInput.disabled = true;
            submitButton.disabled = true;
            submitButton.classList.add('loading');
            submitButton.textContent = 'Processing...';
            
            try {
                const formData = new FormData(queryForm);
                const response = await fetch('/web/query', {
                    method: 'POST',
                    body: formData
                });
                
                const data = await response.json();
                
                if (data.success) {
                    responseContent.textContent = data.response;
                    responseArea.style.display = 'block';
                    
                    // Scroll to response
                    responseArea.scrollIntoView({ behavior: 'smooth', block: 'start' });
                } else {
                    responseContent.textContent = `Error: ${data.error || 'Failed to process query'}`;
                    responseArea.style.display = 'block';
                }
            } catch (error) {
                console.error('Query submission error:', error);
                responseContent.textContent = `Error: ${error.message}`;
                responseArea.style.display = 'block';
            } finally {
                // Re-enable form
                queryInput.disabled = false;
                submitButton.disabled = false;
                submitButton.classList.remove('loading');
                submitButton.textContent = 'Submit Question';
            }
        });
    }
});

// Report task functionality
function reportTask() {
    const query = "I want to report a completed task on my farm";
    document.getElementById('query-input').value = query;
    document.getElementById('submit-query').click();
}

// Get farm data functionality
function getFarmData() {
    const query = "Show me the latest data and statistics about my farm";
    document.getElementById('query-input').value = query;
    document.getElementById('submit-query').click();
}

// Show day details for weather
function showDayDetails(date) {
    console.log(`Showing details for ${date}`);
    // This could expand the day's hourly forecast or show more details
    const query = `What's the detailed weather forecast for ${date}?`;
    document.getElementById('query-input').value = query;
    document.getElementById('submit-query').click();
}

// Update weather data
async function updateWeather() {
    try {
        // Get farmer ID from hidden input or session
        const farmerIdInput = document.querySelector('input[name="farmer_id"]');
        if (!farmerIdInput) {
            console.log('No farmer ID found, skipping weather update');
            return;
        }
        
        const farmerId = farmerIdInput.value;
        const response = await fetch(`/web/weather/${farmerId}`);
        
        if (response.ok) {
            const weatherData = await response.json();
            updateWeatherDisplay(weatherData);
        } else {
            console.error('Failed to fetch weather data');
        }
    } catch (error) {
        console.error('Weather update error:', error);
    }
}

// Update weather display
function updateWeatherDisplay(weatherData) {
    // Update current weather
    const tempElement = document.querySelector('.weather-temp');
    const conditionElement = document.querySelector('.weather-condition');
    
    if (tempElement && weatherData.current_temp) {
        tempElement.textContent = `${weatherData.current_temp}°C`;
    }
    
    if (conditionElement && weatherData.condition) {
        conditionElement.textContent = weatherData.condition;
    }
    
    // Update hourly forecast
    const hourlyContainer = document.getElementById('hourly-forecast');
    if (hourlyContainer && weatherData.hourly_forecast) {
        hourlyContainer.innerHTML = weatherData.hourly_forecast.map(hour => `
            <div class="hour-item">
                <div class="hour-time">${hour.time}</div>
                <div class="hour-icon">${hour.icon}</div>
                <div class="hour-temp">${hour.temp}°</div>
            </div>
        `).join('');
    }
    
    // Update daily forecast if needed
    updateDailyForecast(weatherData.daily_forecast);
}

// Update daily forecast
function updateDailyForecast(dailyForecast) {
    if (!dailyForecast) return;
    
    const weatherTimeline = document.querySelector('.weather-timeline');
    if (weatherTimeline) {
        weatherTimeline.innerHTML = dailyForecast.map(day => `
            <div class="weather-day" onclick="showDayDetails('${day.date}')">
                <div class="day-header">${day.day_name}</div>
                <div class="day-icon">${day.icon}</div>
                <div class="day-temp">
                    <span class="temp-high">${day.temp_high}°</span>
                    <span class="temp-low">${day.temp_low}°</span>
                </div>
                <div class="day-condition">${day.condition}</div>
            </div>
        `).join('');
    }
}

// Auto-resize textarea
document.addEventListener('DOMContentLoaded', function() {
    const textarea = document.getElementById('query-input');
    if (textarea) {
        textarea.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = (this.scrollHeight) + 'px';
        });
    }
});

// Keyboard shortcuts
document.addEventListener('keydown', function(e) {
    // Ctrl/Cmd + Enter to submit from anywhere
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
        const submitButton = document.getElementById('submit-query');
        if (submitButton && !submitButton.disabled) {
            submitButton.click();
        }
    }
    
    // Escape to clear response
    if (e.key === 'Escape') {
        const responseArea = document.getElementById('response-area');
        if (responseArea && responseArea.style.display !== 'none') {
            responseArea.style.display = 'none';
        }
    }
});

// Log constitutional compliance
console.log('🏛️ Constitutional Web Interface initialized');
console.log('📏 Font size:', getComputedStyle(document.documentElement).getPropertyValue('--font-large'));
console.log('🎨 Color scheme: Brown & Olive constitutional palette');
console.log('⌨️ Enter key support: Enabled');
console.log('🥭 MANGO RULE: Ready for Bulgarian mango farmers');