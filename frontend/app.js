/**
 * Quantum Black Ice Detection System - Main JavaScript
 */

const API_BASE_URL = 'http://localhost:5000/api';

let map = null;
let currentMarker = null;

// Initialize application
document.addEventListener('DOMContentLoaded', () => {
    initializeMap();
    initializeEventListeners();
    loadStatistics();
    checkSystemHealth();
    
    // Update statistics periodically
    setInterval(loadStatistics, 60000); // Every minute
});

// Initialize Leaflet map
function initializeMap() {
    map = L.map('map').setView([40.7128, -74.0060], 10); // Default to New York
    
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors',
        maxZoom: 18
    }).addTo(map);
    
    // Add click handler for map
    map.on('click', (e) => {
        const { lat, lng } = e.latlng;
        document.getElementById('latitude').value = lat.toFixed(4);
        document.getElementById('longitude').value = lng.toFixed(4);
    });
}

// Event listeners
function initializeEventListeners() {
    document.getElementById('monitorBtn').addEventListener('click', monitorLocation);
    document.getElementById('getCurrentLocationBtn').addEventListener('click', useCurrentLocation);
}

// Check system health
async function checkSystemHealth() {
    try {
        const response = await fetch(`${API_BASE_URL}/health`);
        const data = await response.json();
        
        if (data.status === 'healthy') {
            updateStatus('online', 'System Online');
        } else {
            updateStatus('warning', 'System Warning');
        }
    } catch (error) {
        updateStatus('offline', 'System Offline');
        console.error('Health check failed:', error);
    }
}

// Update system status indicator
function updateStatus(status, text) {
    const dot = document.getElementById('statusDot');
    const statusText = document.getElementById('statusText');
    
    dot.className = `status-dot status-${status}`;
    statusText.textContent = text;
}

// Get user's current location
function useCurrentLocation() {
    if ('geolocation' in navigator) {
        updateStatus('loading', 'Getting location...');
        
        navigator.geolocation.getCurrentPosition(
            (position) => {
                const lat = position.coords.latitude;
                const lon = position.coords.longitude;
                
                document.getElementById('latitude').value = lat.toFixed(4);
                document.getElementById('longitude').value = lon.toFixed(4);
                
                map.setView([lat, lon], 12);
                monitorLocation();
            },
            (error) => {
                alert('Unable to get your location: ' + error.message);
                updateStatus('warning', 'Location unavailable');
            }
        );
    } else {
        alert('Geolocation is not supported by your browser');
    }
}

// Monitor a specific location
async function monitorLocation() {
    const lat = parseFloat(document.getElementById('latitude').value);
    const lon = parseFloat(document.getElementById('longitude').value);
    
    if (isNaN(lat) || isNaN(lon)) {
        alert('Please enter valid latitude and longitude');
        return;
    }
    
    updateStatus('loading', 'Analyzing...');
    
    try {
        const response = await fetch(`${API_BASE_URL}/black-ice/monitor?lat=${lat}&lon=${lon}`);
        const data = await response.json();
        
        if (data.error) {
            throw new Error(data.error);
        }
        
        displayResults(data);
        updateMapMarker(lat, lon, data.prediction.risk_level);
        updateStatus('online', 'Analysis Complete');
        
    } catch (error) {
        alert('Error monitoring location: ' + error.message);
        updateStatus('warning', 'Analysis Failed');
        console.error(error);
    }
}

// Display analysis results
function displayResults(data) {
    const { weather, prediction, history } = data;
    
    // Update risk level display
    updateRiskDisplay(prediction);
    
    // Update weather conditions
    updateConditions(weather);
    
    // Update factors
    updateFactors(prediction.factors);
    
    // Update recommendations
    updateRecommendations(prediction.recommendations);
    
    // Update history
    updateHistory(history);
    
    // Update timestamp
    document.getElementById('timestamp').textContent = 
        `Updated: ${new Date().toLocaleTimeString()}`;
}

// Update risk level display
function updateRiskDisplay(prediction) {
    const riskLevel = document.getElementById('riskLevel');
    const probability = document.getElementById('probability');
    const gaugeFill = document.getElementById('gaugeFill');
    const riskCard = document.getElementById('riskCard');
    
    // Update text
    riskLevel.textContent = prediction.risk_level.toUpperCase();
    probability.textContent = `${prediction.probability}% Probability`;
    
    // Update gauge
    gaugeFill.style.width = `${prediction.probability}%`;
    
    // Update colors based on risk level
    riskCard.className = `card risk-${prediction.risk_level}`;
    gaugeFill.className = `gauge-fill gauge-${prediction.risk_level}`;
}

// Update weather conditions display
function updateConditions(weather) {
    const grid = document.getElementById('conditionsGrid');
    
    grid.innerHTML = `
        <div class="condition-item">
            <span class="condition-icon">🌡️</span>
            <span class="condition-label">Temperature</span>
            <span class="condition-value">${weather.temperature.toFixed(1)}°C</span>
        </div>
        <div class="condition-item">
            <span class="condition-icon">💧</span>
            <span class="condition-label">Humidity</span>
            <span class="condition-value">${weather.humidity}%</span>
        </div>
        <div class="condition-item">
            <span class="condition-icon">🌫️</span>
            <span class="condition-label">Dew Point</span>
            <span class="condition-value">${weather.dew_point.toFixed(1)}°C</span>
        </div>
        <div class="condition-item">
            <span class="condition-icon">💨</span>
            <span class="condition-label">Wind Speed</span>
            <span class="condition-value">${weather.wind_speed.toFixed(1)} m/s</span>
        </div>
        <div class="condition-item">
            <span class="condition-icon">☁️</span>
            <span class="condition-label">Conditions</span>
            <span class="condition-value">${weather.description}</span>
        </div>
        <div class="condition-item">
            <span class="condition-icon">👁️</span>
            <span class="condition-label">Visibility</span>
            <span class="condition-value">${(weather.visibility / 1000).toFixed(1)} km</span>
        </div>
    `;
}

// Update risk factors
function updateFactors(factors) {
    const list = document.getElementById('factorsList');
    
    if (factors.length === 0) {
        list.innerHTML = '<p class="placeholder">No significant risk factors detected</p>';
        return;
    }
    
    list.innerHTML = factors.map(factor => `
        <div class="factor-item">
            <div class="factor-header">
                <strong>${factor.name}</strong>
                <span class="factor-score">${factor.score.toFixed(1)} pts</span>
            </div>
            <p class="factor-description">${factor.description}</p>
        </div>
    `).join('');
}

// Update recommendations
function updateRecommendations(recommendations) {
    const list = document.getElementById('recommendationsList');
    
    if (recommendations.length === 0) {
        list.innerHTML = '<p class="placeholder">No recommendations at this time</p>';
        return;
    }
    
    list.innerHTML = '<ul>' + recommendations.map(rec => 
        `<li>${rec}</li>`
    ).join('') + '</ul>';
}

// Update history display
function updateHistory(history) {
    const list = document.getElementById('historyList');
    
    if (!history || history.length === 0) {
        list.innerHTML = '<p class="placeholder">No history available</p>';
        return;
    }
    
    list.innerHTML = history.slice(0, 10).map(entry => {
        const time = new Date(entry.timestamp).toLocaleString();
        return `
            <div class="history-item risk-${entry.risk_level}">
                <span class="history-time">${time}</span>
                <span class="history-risk">${entry.risk_level.toUpperCase()}</span>
                <span class="history-prob">${entry.probability}%</span>
            </div>
        `;
    }).join('');
}

// Update map marker
function updateMapMarker(lat, lon, riskLevel) {
    // Remove existing marker
    if (currentMarker) {
        map.removeLayer(currentMarker);
    }
    
    // Color based on risk level
    const colors = {
        none: 'green',
        low: 'blue',
        moderate: 'yellow',
        high: 'orange',
        extreme: 'red'
    };
    
    const icon = L.divIcon({
        className: 'custom-marker',
        html: `<div style="background-color: ${colors[riskLevel]}; width: 20px; height: 20px; border-radius: 50%; border: 2px solid white;"></div>`,
        iconSize: [20, 20]
    });
    
    currentMarker = L.marker([lat, lon], { icon }).addTo(map);
    currentMarker.bindPopup(`<strong>Risk: ${riskLevel.toUpperCase()}</strong>`).openPopup();
    
    map.setView([lat, lon], 12);
}

// Load system statistics
async function loadStatistics() {
    try {
        const response = await fetch(`${API_BASE_URL}/statistics`);
        const data = await response.json();
        
        document.getElementById('totalPredictions').textContent = data.total_predictions;
        document.getElementById('activeAlerts').textContent = data.active_alerts;
        document.getElementById('avgProbability').textContent = `${data.avg_probability_24h}%`;
        
    } catch (error) {
        console.error('Error loading statistics:', error);
    }
}
