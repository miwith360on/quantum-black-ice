/**
 * Advanced Dashboard - Integrates AI/ML, WebSocket, and Radar features
 */

const API_URL = 'http://localhost:5000/api';
let map = null;
let socket = null;
let currentLocation = { lat: 42.3601, lon: -71.0589 }; // Default: Boston
let weatherHistory = [];
let radarLayers = {};
let currentMarker = null;

// Initialize everything when page loads
document.addEventListener('DOMContentLoaded', () => {
    initializeMap();
    checkMLModel();
    initializeWebSocket();
    setupLayerToggles();
    
    // Get user location by default
    useCurrentLocation();
});

/**
 * Initialize the Leaflet map
 */
function initializeMap() {
    map = L.map('map').setView([currentLocation.lat, currentLocation.lon], 10);
    
    // Base map layer
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors',
        maxZoom: 19
    }).addTo(map);
    
    // Add current location marker
    currentMarker = L.marker([currentLocation.lat, currentLocation.lon], {
        icon: L.divIcon({
            className: 'custom-marker',
            html: '<div style="background: #00d4ff; width: 20px; height: 20px; border-radius: 50%; border: 3px solid white; box-shadow: 0 0 15px #00d4ff;"></div>',
            iconSize: [20, 20]
        })
    }).addTo(map);
    
    console.log('✅ Map initialized');
}

/**
 * Check ML Model Status
 */
async function checkMLModel() {
    try {
        const response = await fetch(`${API_URL}/ml/model-info`);
        const data = await response.json();
        
        const mlStatus = document.getElementById('mlStatus');
        const modelStatus = document.getElementById('modelStatus');
        
        if (data.tensorflow_available && data.model_loaded) {
            mlStatus.className = 'status-indicator status-active';
            modelStatus.textContent = data.is_trained ? '🟢 Trained & Ready' : '🟡 Untrained (using fallback)';
        } else {
            mlStatus.className = 'status-indicator status-inactive';
            modelStatus.textContent = '🔴 TensorFlow not available';
        }
        
        console.log('✅ ML Model checked:', data);
    } catch (error) {
        console.error('❌ Error checking ML model:', error);
        document.getElementById('modelStatus').textContent = '🔴 Connection error';
    }
}

/**
 * Initialize WebSocket Connection
 */
function initializeWebSocket() {
    if (typeof io === 'undefined') {
        console.warn('⚠️ Socket.IO library not loaded');
        addLogEntry('WebSocket library not available', 'alert');
        return;
    }
    
    socket = io('http://localhost:5000', {
        transports: ['websocket', 'polling']
    });
    
    socket.on('connect', () => {
        console.log('✅ WebSocket connected');
        document.getElementById('wsStatus').className = 'status-indicator status-active';
        document.getElementById('wsConnection').textContent = 'Connected ✅';
        addLogEntry('🟢 Connected to WebSocket server');
        
        // Subscribe to current location
        socket.emit('subscribe_location', {
            lat: currentLocation.lat,
            lon: currentLocation.lon
        });
    });
    
    socket.on('disconnect', () => {
        console.log('❌ WebSocket disconnected');
        document.getElementById('wsStatus').className = 'status-indicator status-inactive';
        document.getElementById('wsConnection').textContent = 'Disconnected ❌';
        addLogEntry('🔴 Disconnected from server', 'alert');
    });
    
    socket.on('weather_update', (data) => {
        console.log('🌤️ Weather update received:', data);
        addLogEntry(`🌤️ Weather update: ${data.data.temperature}°F`, 'update');
        document.getElementById('lastUpdate').textContent = new Date().toLocaleTimeString();
        
        // Store in history for ML
        weatherHistory.push(data.data);
        if (weatherHistory.length > 6) {
            weatherHistory.shift(); // Keep last 6 hours
        }
        
        // Trigger ML prediction with history
        if (weatherHistory.length >= 3) {
            getMLPrediction();
        }
    });
    
    socket.on('prediction_update', (data) => {
        console.log('🔮 Prediction update:', data);
        addLogEntry(`🔮 Prediction: ${data.data.risk_level}`, 'update');
    });
    
    socket.on('radar_update', (data) => {
        console.log('🛰️ Radar update:', data);
        addLogEntry('🛰️ Radar data refreshed', 'update');
        updateRadarLayers(data.data);
    });
    
    socket.on('weather_alert', (data) => {
        console.log('⚠️ Weather alert:', data);
        showAlert(data.alert);
        addLogEntry(`⚠️ ALERT: ${data.alert.headline}`, 'alert');
    });
    
    socket.on('connection_status', (data) => {
        console.log('📊 Connection status:', data);
    });
}

/**
 * Add entry to WebSocket log
 */
function addLogEntry(message, type = 'normal') {
    const log = document.getElementById('wsLog');
    const entry = document.createElement('div');
    entry.className = `log-entry ${type}`;
    entry.textContent = `[${new Date().toLocaleTimeString()}] ${message}`;
    
    log.insertBefore(entry, log.firstChild);
    
    // Keep only last 20 entries
    while (log.children.length > 20) {
        log.removeChild(log.lastChild);
    }
}

/**
 * Get ML Prediction
 */
async function getMLPrediction() {
    try {
        const response = await fetch(`${API_URL}/ml/predict`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                weather_sequence: weatherHistory
            })
        });
        
        const data = await response.json();
        
        // Update UI with ML prediction
        document.getElementById('mlPrediction').textContent = 
            `${data.risk_level.toUpperCase()} (${data.model})`;
        
        const confidence = Math.round(data.confidence * 100);
        document.getElementById('confidenceBar').style.width = `${confidence}%`;
        document.getElementById('confidenceBar').textContent = `${confidence}%`;
        
        // Update probability chart
        if (data.all_probabilities) {
            updateProbabilityChart(data.all_probabilities);
        }
        
        console.log('✅ ML Prediction:', data);
    } catch (error) {
        console.error('❌ Error getting ML prediction:', error);
    }
}

/**
 * Update probability chart
 */
function updateProbabilityChart(probabilities) {
    const chart = document.getElementById('probabilityChart');
    chart.innerHTML = '';
    
    const levels = ['none', 'low', 'moderate', 'high', 'extreme'];
    const colors = ['#00ff00', '#90ee90', '#ffff00', '#ff8c00', '#ff0000'];
    
    levels.forEach((level, index) => {
        const prob = probabilities[level] || 0;
        const percent = Math.round(prob * 100);
        
        const barDiv = document.createElement('div');
        barDiv.className = 'prob-bar';
        
        const fillDiv = document.createElement('div');
        fillDiv.className = 'prob-bar-fill';
        fillDiv.style.height = `${percent}px`;
        fillDiv.style.background = colors[index];
        fillDiv.textContent = `${percent}%`;
        
        const labelDiv = document.createElement('div');
        labelDiv.className = 'prob-label';
        labelDiv.textContent = level;
        
        barDiv.appendChild(fillDiv);
        barDiv.appendChild(labelDiv);
        chart.appendChild(barDiv);
    });
}

/**
 * Setup radar layer toggles
 */
function setupLayerToggles() {
    document.getElementById('layerPrecipitation').addEventListener('change', (e) => {
        toggleRadarLayer('precipitation', e.target.checked);
    });
    
    document.getElementById('layerClouds').addEventListener('change', (e) => {
        toggleRadarLayer('clouds', e.target.checked);
    });
    
    document.getElementById('layerTemperature').addEventListener('change', (e) => {
        toggleRadarLayer('temperature', e.target.checked);
    });
    
    document.getElementById('layerWind').addEventListener('change', (e) => {
        toggleRadarLayer('wind', e.target.checked);
    });
    
    document.getElementById('layerSatellite').addEventListener('change', (e) => {
        toggleRadarLayer('satellite', e.target.checked);
    });
}

/**
 * Toggle radar layer on/off
 */
async function toggleRadarLayer(layerName, enabled) {
    if (enabled) {
        await loadRadarLayer(layerName);
    } else {
        if (radarLayers[layerName]) {
            map.removeLayer(radarLayers[layerName]);
            delete radarLayers[layerName];
        }
    }
}

/**
 * Load radar layer
 */
async function loadRadarLayer(layerName) {
    try {
        const response = await fetch(
            `${API_URL}/radar/composite?lat=${currentLocation.lat}&lon=${currentLocation.lon}`
        );
        const data = await response.json();
        
        if (data.success) {
            let layerUrl = null;
            
            if (layerName === 'satellite') {
                layerUrl = data.satellite?.url;
            } else if (data.weather_overlays && data.weather_overlays[layerName]) {
                layerUrl = data.weather_overlays[layerName].url;
            }
            
            if (layerUrl) {
                // Remove existing layer
                if (radarLayers[layerName]) {
                    map.removeLayer(radarLayers[layerName]);
                }
                
                // Add new layer
                radarLayers[layerName] = L.tileLayer(layerUrl, {
                    opacity: 0.6,
                    attribution: 'Weather Data'
                }).addTo(map);
                
                document.getElementById('radarStatus').className = 'status-indicator status-active';
                console.log(`✅ Loaded ${layerName} layer`);
            }
        }
    } catch (error) {
        console.error(`❌ Error loading ${layerName} layer:`, error);
    }
}

/**
 * Update radar layers from WebSocket
 */
function updateRadarLayers(radarData) {
    // Refresh active layers
    Object.keys(radarLayers).forEach(layerName => {
        const checkbox = document.getElementById(`layer${layerName.charAt(0).toUpperCase() + layerName.slice(1)}`);
        if (checkbox && checkbox.checked) {
            loadRadarLayer(layerName);
        }
    });
}

/**
 * Show weather alert
 */
function showAlert(alert) {
    const banner = document.getElementById('alertBanner');
    banner.textContent = `⚠️ ${alert.headline || alert.event || 'Weather Alert'}`;
    banner.style.display = 'block';
    
    setTimeout(() => {
        banner.style.display = 'none';
    }, 10000);
}

/**
 * Update location
 */
async function updateLocation() {
    const lat = parseFloat(document.getElementById('latInput').value);
    const lon = parseFloat(document.getElementById('lonInput').value);
    
    if (isNaN(lat) || isNaN(lon)) {
        alert('Please enter valid coordinates');
        return;
    }
    
    currentLocation = { lat, lon };
    
    // Update map
    map.setView([lat, lon], 10);
    currentMarker.setLatLng([lat, lon]);
    
    // Subscribe to new location via WebSocket
    if (socket && socket.connected) {
        socket.emit('subscribe_location', { lat, lon });
        addLogEntry(`📍 Subscribed to new location: ${lat.toFixed(4)}, ${lon.toFixed(4)}`);
    }
    
    // Reload active radar layers
    Object.keys(radarLayers).forEach(layerName => {
        loadRadarLayer(layerName);
    });
    
    // Reset weather history
    weatherHistory = [];
    
    console.log('✅ Location updated:', currentLocation);
}

/**
 * Use current geolocation
 */
function useCurrentLocation() {
    if ('geolocation' in navigator) {
        navigator.geolocation.getCurrentPosition(
            (position) => {
                document.getElementById('latInput').value = position.coords.latitude.toFixed(4);
                document.getElementById('lonInput').value = position.coords.longitude.toFixed(4);
                updateLocation();
            },
            (error) => {
                console.error('❌ Geolocation error:', error);
                alert('Could not get your location. Please enter coordinates manually.');
            }
        );
    } else {
        alert('Geolocation not supported by your browser');
    }
}

/**
 * Update WebSocket stats periodically
 */
setInterval(async () => {
    try {
        const response = await fetch(`${API_URL}/websocket/status`);
        const data = await response.json();
        document.getElementById('activeClients').textContent = data.active_connections || 0;
    } catch (error) {
        // Silently fail
    }
}, 5000);
