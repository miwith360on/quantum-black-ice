// Mobile PWA - Main JavaScript
// Quantum Black Ice Detection System - Mobile Version

// Configuration
const API_BASE = window.location.origin.includes('localhost') 
    ? 'http://localhost:5000' 
    : window.location.origin;

console.log('🔧 API_BASE configured as:', API_BASE);
console.log('🌍 Current origin:', window.location.origin);

// Global state
let map = null;
let socket = null;
let currentLocation = { lat: null, lng: null };
let userMarker = null;
let radarLayer = null;
let temperatureLayer = null;
let windLayer = null;
let satelliteLayer = null;
let trafficLayer = null;
let roadRiskMarkers = [];
let currentView = 'home';

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    console.log('🌨️ Black Ice Alert PWA initializing...');
    initializeApp();
});

// Main initialization
async function initializeApp() {
    // Test API connection first
    await testAPIConnection();
    
    // Register service worker
    registerServiceWorker();
    
    // Initialize map
    initializeMap();
    
    // Get user location
    await getUserLocation();
    
    // Initialize WebSocket
    initializeWebSocket();
    
    // Check ML model status
    checkMLStatus();
    
    // Setup event listeners
    setupEventListeners();
    
    // Start periodic updates
    startPeriodicUpdates();
    
    console.log('✅ App initialized successfully');
}

// Test API connection
async function testAPIConnection() {
    console.log('🔍 Testing API connection to:', API_BASE);
    try {
        const response = await fetch(`${API_BASE}/api/health`);
        if (response.ok) {
            const data = await response.json();
            console.log('✅ API health check passed:', data);
        } else {
            console.error('❌ API health check failed:', response.status, response.statusText);
            showAlert('Cannot connect to server. Please check your connection.', 'error');
        }
    } catch (error) {
        console.error('❌ API connection error:', error);
        showAlert(`Server connection failed: ${error.message}`, 'error');
    }
}

// Register Service Worker for PWA
function registerServiceWorker() {
    if ('serviceWorker' in navigator) {
        navigator.serviceWorker.register('/sw.js')
            .then(registration => {
                console.log('✅ Service Worker registered:', registration.scope);
                
                // Check for updates
                registration.addEventListener('updatefound', () => {
                    const newWorker = registration.installing;
                    newWorker.addEventListener('statechange', () => {
                        if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
                            showAlert('Update available! Refresh to get the latest version.', 'info');
                        }
                    });
                });
            })
            .catch(error => {
                console.error('❌ Service Worker registration failed:', error);
            });
    }
}

// Initialize Leaflet map
function initializeMap() {
    map = L.map('map', {
        zoomControl: false,
        attributionControl: false
    }).setView([42.3314, -83.0458], 10); // Default to Detroit
    
    // Add base tile layer
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19
    }).addTo(map);
    
    console.log('🗺️ Map initialized');
}

// Get user's GPS location
async function getUserLocation() {
    if (!navigator.geolocation) {
        console.error('Geolocation not supported');
        updateLocationText('Location not available');
        return;
    }
    
    updateLocationText('Getting location...');
    
    navigator.geolocation.getCurrentPosition(
        async (position) => {
            currentLocation.lat = position.coords.latitude;
            currentLocation.lng = position.coords.longitude;
            
            console.log('📍 Location obtained:', currentLocation);
            
            // Update map
            map.setView([currentLocation.lat, currentLocation.lng], 12);
            
            // Add user marker
            if (userMarker) {
                map.removeLayer(userMarker);
            }
            
            userMarker = L.marker([currentLocation.lat, currentLocation.lng], {
                icon: L.divIcon({
                    className: 'user-location-marker',
                    html: '<div style="background: #007AFF; width: 16px; height: 16px; border-radius: 50%; border: 3px solid white; box-shadow: 0 2px 8px rgba(0,0,0,0.3);"></div>',
                    iconSize: [22, 22]
                })
            }).addTo(map);
            
            // Get location name
            await reverseGeocode(currentLocation.lat, currentLocation.lng);
            
            // Subscribe to WebSocket updates for this location
            if (socket && socket.connected) {
                socket.emit('subscribe_location', {
                    lat: currentLocation.lat,
                    lng: currentLocation.lng
                });
            }
            
            // Fetch weather data
            fetchWeatherData();
            
            // Fetch road risks if layer is enabled
            if (document.getElementById('road-risk-layer').checked) {
                fetchRoadRisks();
            }
        },
        (error) => {
            console.error('Location error:', error);
            updateLocationText('Location unavailable');
            showAlert('Unable to get your location. Please enable location services.', 'warning');
        },
        {
            enableHighAccuracy: true,
            timeout: 10000,
            maximumAge: 300000 // 5 minutes
        }
    );
}

// Reverse geocode to get location name
async function reverseGeocode(lat, lng) {
    try {
        const response = await fetch(
            `https://nominatim.openstreetmap.org/reverse?lat=${lat}&lon=${lng}&format=json`
        );
        const data = await response.json();
        
        const locationName = data.address.city || data.address.town || data.address.village || 'Unknown';
        updateLocationText(locationName);
    } catch (error) {
        console.error('Reverse geocode error:', error);
        updateLocationText(`${lat.toFixed(2)}, ${lng.toFixed(2)}`);
    }
}

// Initialize WebSocket connection
function initializeWebSocket() {
    socket = io(API_BASE, {
        transports: ['websocket', 'polling'],
        reconnection: true,
        reconnectionDelay: 1000,
        reconnectionAttempts: 5
    });
    
    socket.on('connect', () => {
        console.log('✅ WebSocket connected:', socket.id);
        updateConnectionStatus(true);
        addActivityItem('Connected to live stream');
        
        // Subscribe to current location
        if (currentLocation.lat && currentLocation.lng) {
            socket.emit('subscribe_location', currentLocation);
        }
    });
    
    socket.on('disconnect', () => {
        console.log('❌ WebSocket disconnected');
        updateConnectionStatus(false);
        addActivityItem('Disconnected from live stream');
    });
    
    socket.on('weather_update', (data) => {
        console.log('🌤️ Weather update:', data);
        updateWeatherDisplay(data);
        addActivityItem(`Weather updated: ${data.temperature}°F`);
    });
    
    socket.on('prediction_update', (data) => {
        console.log('🤖 Prediction update:', data);
        updatePredictionDisplay(data);
        addActivityItem(`Risk level: ${data.risk_level}`);
    });
    
    socket.on('radar_update', (data) => {
        console.log('📡 Radar update:', data);
        updateRadarLayers(data);
        addActivityItem('Radar data updated');
    });
    
    socket.on('weather_alert', (data) => {
        console.log('⚠️ Weather alert:', data);
        showAlert(data.message, data.severity);
        addActivityItem(`Alert: ${data.message}`);
        
        // Vibrate if supported
        if ('vibrate' in navigator) {
            navigator.vibrate([200, 100, 200]);
        }
    });
    
    socket.on('connect_error', (error) => {
        console.error('WebSocket connection error:', error);
        updateConnectionStatus(false);
    });
}

// Check ML model status
async function checkMLStatus() {
    try {
        const response = await fetch(`${API_BASE}/api/ml/model-info`);
        const data = await response.json();
        
        updateMLStatus(data);
    } catch (error) {
        console.error('ML status check failed:', error);
        updateMLStatus({ status: 'error', message: 'Connection error' });
    }
}

// Fetch weather data
async function fetchWeatherData() {
    if (!currentLocation.lat || !currentLocation.lng) return;
    
    console.log('🌤️ Fetching weather for:', currentLocation);
    console.log('🔗 API URL:', `${API_BASE}/api/weather/current?lat=${currentLocation.lat}&lon=${currentLocation.lng}`);
    
    try {
        const response = await fetch(
            `${API_BASE}/api/weather/current?lat=${currentLocation.lat}&lon=${currentLocation.lng}`
        );
        
        console.log('📡 Weather response status:', response.status);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        console.log('✅ Weather data received:', data);
        
        updateWeatherDisplay(data);
        
        // Get ML prediction
        getPrediction(data);
    } catch (error) {
        console.error('❌ Weather fetch failed:', error);
        showAlert(`Unable to fetch weather data: ${error.message}`, 'error');
    }
}

// Get ML prediction
async function getPrediction(weatherData) {
    try {
        const response = await fetch(`${API_BASE}/api/ml/predict`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(weatherData)
        });
        const data = await response.json();
        
        updatePredictionDisplay(data);
        
        // Also get quantum prediction
        getQuantumPrediction(weatherData);
    } catch (error) {
        console.error('Prediction failed:', error);
    }
}

// Get Quantum prediction
async function getQuantumPrediction(weatherData) {
    try {
        const response = await fetch(`${API_BASE}/api/quantum/predict`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ weather_data: weatherData })
        });
        const data = await response.json();
        
        if (data.success && data.quantum_prediction) {
            updateQuantumDisplay(data.quantum_prediction);
        }
    } catch (error) {
        console.error('Quantum prediction failed:', error);
    }
}

// Update UI functions
function updateConnectionStatus(connected) {
    const statusEl = document.getElementById('connection-status');
    const statusDot = statusEl.querySelector('.status-dot');
    const statusText = statusEl.querySelector('.status-text');
    
    if (connected) {
        statusEl.classList.add('connected');
        statusEl.classList.remove('error');
        statusText.textContent = 'Live';
    } else {
        statusEl.classList.remove('connected');
        statusEl.classList.add('error');
        statusText.textContent = 'Offline';
    }
}

function updateLocationText(text) {
    document.getElementById('location-text').textContent = text;
}

function updateWeatherDisplay(data) {
    // Update temperature - round to 1 decimal place
    const temp = data.temperature || data.temp;
    const tempText = temp ? Math.round(temp * 10) / 10 : '--';
    document.getElementById('temp-text').textContent = `${tempText}°F`;
    
    // Update humidity - round to whole number
    const humidity = data.humidity;
    const humidityText = humidity ? Math.round(humidity) : '--';
    document.getElementById('humidity-text').textContent = `${humidityText}%`;
    
    // Update wind - round to 1 decimal place
    const wind = data.wind_speed || data.wind;
    const windText = wind ? Math.round(wind * 10) / 10 : '--';
    document.getElementById('wind-text').textContent = `${windText} mph`;
}

function updatePredictionDisplay(data) {
    const riskLevel = data.risk_level || data.prediction || 'Unknown';
    const confidence = data.confidence || 0;
    
    // Update risk circle
    const riskCircle = document.getElementById('risk-circle');
    const riskPercentage = document.getElementById('risk-percentage');
    const riskLabel = document.getElementById('risk-label');
    
    // Map risk level to percentage
    const riskMap = {
        'Very Low': 5,
        'Low': 25,
        'Medium': 50,
        'High': 75,
        'Very High': 95
    };
    
    const riskValue = riskMap[riskLevel] || 0;
    
    riskPercentage.textContent = `${riskValue}%`;
    riskLabel.textContent = riskLevel;
    
    // Update circle color
    riskCircle.className = 'risk-circle';
    if (riskValue < 30) riskCircle.classList.add('low');
    else if (riskValue < 60) riskCircle.classList.add('medium');
    else riskCircle.classList.add('high');
    
    // Update confidence bar
    const confidenceBar = document.getElementById('confidence-bar');
    const confidenceValue = document.getElementById('confidence-value');
    
    confidenceBar.style.width = `${confidence}%`;
    confidenceValue.textContent = `${Math.round(confidence)}%`;
    
    // Update prediction result
    const predictionResult = document.getElementById('prediction-result');
    predictionResult.textContent = data.message || `Risk: ${riskLevel} (${Math.round(confidence)}% confidence)`;
}

function updateQuantumDisplay(quantumData) {
    const quantumSection = document.getElementById('quantum-section');
    
    if (!quantumSection) {
        // Create quantum section if it doesn't exist
        const aiSection = document.querySelector('.ai-prediction');
        const quantumHTML = `
            <div id="quantum-section" class="quantum-prediction">
                <div class="section-header">
                    <h3>⚛️ Quantum Analysis</h3>
                    <div class="quantum-badge">5-Qubit Circuit</div>
                </div>
                <div class="quantum-metrics">
                    <div class="quantum-metric">
                        <div class="metric-label">Quantum Probability</div>
                        <div class="metric-value" id="quantum-probability">--</div>
                    </div>
                    <div class="quantum-metric">
                        <div class="metric-label">Entropy</div>
                        <div class="metric-value" id="quantum-entropy">--</div>
                    </div>
                    <div class="quantum-metric">
                        <div class="metric-label">Confidence</div>
                        <div class="metric-value" id="quantum-confidence">--</div>
                    </div>
                </div>
                <div class="qubit-states">
                    <div class="qubit-state" id="qubit-temp">
                        <span class="qubit-icon">Q0</span>
                        <span class="qubit-label">Temp</span>
                    </div>
                    <div class="qubit-state" id="qubit-humidity">
                        <span class="qubit-icon">Q1</span>
                        <span class="qubit-label">Humidity</span>
                    </div>
                    <div class="qubit-state" id="qubit-wind">
                        <span class="qubit-icon">Q2</span>
                        <span class="qubit-label">Wind</span>
                    </div>
                    <div class="qubit-state" id="qubit-precip">
                        <span class="qubit-icon">Q3</span>
                        <span class="qubit-label">Precip</span>
                    </div>
                    <div class="qubit-state" id="qubit-time">
                        <span class="qubit-icon">Q4</span>
                        <span class="qubit-label">Time</span>
                    </div>
                </div>
            </div>
        `;
        aiSection.insertAdjacentHTML('afterend', quantumHTML);
    }
    
    // Update quantum metrics
    const probability = (quantumData.probability * 100).toFixed(1);
    const entropy = quantumData.entropy.toFixed(3);
    const confidence = (quantumData.confidence * 100).toFixed(1);
    
    document.getElementById('quantum-probability').textContent = `${probability}%`;
    document.getElementById('quantum-entropy').textContent = entropy;
    document.getElementById('quantum-confidence').textContent = `${confidence}%`;
    
    // Update qubit state colors based on risk factors
    const qubits = ['temp', 'humidity', 'wind', 'precip', 'time'];
    const riskFactors = quantumData.quantum_metrics?.risk_factors || {};
    
    qubits.forEach((qubit, index) => {
        const qubitEl = document.getElementById(`qubit-${qubit}`);
        if (qubitEl) {
            const riskKey = Object.keys(riskFactors)[index];
            const riskValue = riskFactors[riskKey] || 0;
            
            // Color based on risk level
            if (riskValue < 0.3) {
                qubitEl.style.background = 'linear-gradient(135deg, #34C759, #30D158)';
            } else if (riskValue < 0.6) {
                qubitEl.style.background = 'linear-gradient(135deg, #FF9500, #FFB340)';
            } else {
                qubitEl.style.background = 'linear-gradient(135deg, #FF3B30, #FF6961)';
            }
        }
    });
}

function updateMLStatus(data) {
    const statusEl = document.getElementById('ml-status');
    const statusText = document.getElementById('ml-status-text');
    
    if (data.status === 'ready' || data.is_trained) {
        statusEl.querySelector('.status-dot').style.background = '#34C759';
        statusText.textContent = 'Model Active';
    } else if (data.status === 'error') {
        statusEl.querySelector('.status-dot').style.background = '#FF3B30';
        statusText.textContent = data.message || 'Connection error';
    } else {
        statusEl.querySelector('.status-dot').style.background = '#FF9500';
        statusText.textContent = 'Model Loading';
    }
}

function updateRadarLayers(data) {
    // Update radar layers on map
    if (data.radar_url && document.getElementById('radar-layer').checked) {
        if (radarLayer) map.removeLayer(radarLayer);
        radarLayer = L.tileLayer(data.radar_url).addTo(map);
    }
}

function addActivityItem(text) {
    const feed = document.getElementById('activity-feed');
    const now = new Date();
    const timeStr = now.toLocaleTimeString('en-US', { 
        hour: '2-digit', 
        minute: '2-digit' 
    });
    
    const item = document.createElement('div');
    item.className = 'activity-item';
    item.innerHTML = `
        <span class="activity-time">${timeStr}</span>
        <span class="activity-text">${text}</span>
    `;
    
    // Add to top
    feed.insertBefore(item, feed.firstChild);
    
    // Keep only last 10 items
    while (feed.children.length > 10) {
        feed.removeChild(feed.lastChild);
    }
}

function showAlert(message, severity = 'info') {
    const banner = document.getElementById('alert-banner');
    const text = document.getElementById('alert-text');
    
    text.textContent = message;
    banner.style.display = 'flex';
    
    // Auto-hide after 5 seconds
    setTimeout(() => {
        banner.style.display = 'none';
    }, 5000);
}

// Event listeners
function setupEventListeners() {
    // Refresh button
    document.getElementById('refresh-btn').addEventListener('click', () => {
        fetchWeatherData();
        addActivityItem('Manually refreshed');
    });
    
    // Settings button
    document.getElementById('settings-btn').addEventListener('click', () => {
        // Implement settings modal
        showAlert('Settings coming soon!', 'info');
    });
    
    // Alert close
    document.getElementById('alert-close').addEventListener('click', () => {
        document.getElementById('alert-banner').style.display = 'none';
    });
    
    // Map controls
    document.getElementById('locate-btn').addEventListener('click', () => {
        if (currentLocation.lat && currentLocation.lng) {
            map.setView([currentLocation.lat, currentLocation.lng], 12);
        } else {
            getUserLocation();
        }
    });
    
    document.getElementById('layers-btn').addEventListener('click', () => {
        const selector = document.getElementById('layer-selector');
        selector.style.display = selector.style.display === 'none' ? 'block' : 'none';
    });
    
    // Layer toggles
    document.getElementById('radar-layer').addEventListener('change', (e) => {
        if (e.target.checked) {
            fetchRadarLayer();
        } else if (radarLayer) {
            map.removeLayer(radarLayer);
        }
    });
    
    document.getElementById('temp-layer').addEventListener('change', (e) => {
        if (e.target.checked) {
            fetchTemperatureLayer();
        } else if (temperatureLayer) {
            map.removeLayer(temperatureLayer);
        }
    });
    
    document.getElementById('wind-layer').addEventListener('change', (e) => {
        if (e.target.checked) {
            fetchWindLayer();
        } else if (windLayer) {
            map.removeLayer(windLayer);
        }
    });
    
    document.getElementById('satellite-layer').addEventListener('change', (e) => {
        if (e.target.checked) {
            fetchSatelliteLayer();
        } else if (satelliteLayer) {
            map.removeLayer(satelliteLayer);
        }
    });
    
    document.getElementById('traffic-layer').addEventListener('change', (e) => {
        if (e.target.checked) {
            fetchTrafficLayer();
        } else if (trafficLayer) {
            map.removeLayer(trafficLayer);
        }
    });
    
    document.getElementById('road-risk-layer').addEventListener('change', (e) => {
        if (e.target.checked) {
            fetchRoadRisks();
        } else {
            clearRoadRiskMarkers();
        }
    });
    
    // Bottom navigation
    document.querySelectorAll('.nav-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const view = btn.dataset.view;
            switchView(view);
        });
    });
}

// Fetch radar layers
async function fetchRadarLayer() {
    try {
        const response = await fetch(`${API_BASE}/api/radar/layers`);
        const data = await response.json();
        
        if (data.layers && data.layers.length > 0) {
            const latestLayer = data.layers[data.layers.length - 1];
            if (radarLayer) map.removeLayer(radarLayer);
            radarLayer = L.tileLayer(latestLayer.url, {
                opacity: 0.6
            }).addTo(map);
        }
    } catch (error) {
        console.error('Radar layer fetch failed:', error);
    }
}

async function fetchTemperatureLayer() {
    // Temperature overlay (would need OpenWeatherMap API key)
    showAlert('Temperature layer requires API key', 'info');
}

async function fetchWindLayer() {
    // Wind overlay (would need OpenWeatherMap API key)
    showAlert('Wind layer requires API key', 'info');
}

async function fetchSatelliteLayer() {
    try {
        const response = await fetch(
            `${API_BASE}/api/satellite/imagery?lat=${currentLocation.lat}&lng=${currentLocation.lng}`
        );
        const data = await response.json();
        
        if (data.image_url) {
            if (satelliteLayer) map.removeLayer(satelliteLayer);
            satelliteLayer = L.tileLayer(data.image_url, {
                opacity: 0.5
            }).addTo(map);
        }
    } catch (error) {
        console.error('Satellite layer fetch failed:', error);
    }
}

async function fetchTrafficLayer() {
    console.log('🚦 Fetching traffic layer...');
    try {
        const response = await fetch(`${API_BASE}/api/traffic/tile-url`);
        const data = await response.json();
        
        if (data.available && data.tile_url) {
            if (trafficLayer) map.removeLayer(trafficLayer);
            trafficLayer = L.tileLayer(data.tile_url, {
                opacity: 0.7,
                zIndex: 1000
            }).addTo(map);
            console.log('✅ Traffic layer added');
            showAlert('Live traffic overlay enabled', 'success');
        } else {
            console.warn('⚠️ Traffic layer not available:', data.message);
            showAlert(data.message || 'Traffic layer requires Google Maps API key', 'info');
            // Uncheck the box
            document.getElementById('traffic-layer').checked = false;
        }
    } catch (error) {
        console.error('❌ Traffic layer fetch failed:', error);
        showAlert('Unable to load traffic data', 'error');
        document.getElementById('traffic-layer').checked = false;
    }
}

async function fetchRoadRisks() {
    if (!currentLocation.lat || !currentLocation.lng) {
        console.warn('⚠️ No location available for road risk analysis');
        return;
    }
    
    console.log('🌉 Fetching road risks...');
    try {
        const response = await fetch(
            `${API_BASE}/api/road/analyze?lat=${currentLocation.lat}&lon=${currentLocation.lng}&radius=5000`
        );
        const data = await response.json();
        
        console.log('✅ Road risks received:', data);
        
        // Clear existing markers
        clearRoadRiskMarkers();
        
        // Add bridge markers (RED - highest risk)
        data.bridges?.forEach(bridge => {
            const marker = L.marker(bridge.center, {
                icon: L.divIcon({
                    className: 'road-risk-marker bridge-marker',
                    html: '<span class="marker-icon">🌉</span>',
                    iconSize: [30, 30]
                })
            }).addTo(map);
            
            marker.bindPopup(`
                <div class="risk-popup">
                    <h3>⚠️ BRIDGE - HIGH RISK</h3>
                    <p><strong>${bridge.name}</strong></p>
                    <p>Bridges freeze FIRST! Risk multiplier: ${bridge.risk_multiplier}x</p>
                    <p>Distance: ${bridge.distance}m</p>
                </div>
            `);
            
            roadRiskMarkers.push(marker);
        });
        
        // Add overpass markers (ORANGE - high risk)
        data.overpasses?.forEach(overpass => {
            const marker = L.marker(overpass.center, {
                icon: L.divIcon({
                    className: 'road-risk-marker overpass-marker',
                    html: '<span class="marker-icon">🛣️</span>',
                    iconSize: [28, 28]
                })
            }).addTo(map);
            
            marker.bindPopup(`
                <div class="risk-popup">
                    <h3>⚠️ OVERPASS</h3>
                    <p><strong>${overpass.name}</strong></p>
                    <p>Elevated roads freeze early. Risk: ${overpass.risk_multiplier}x</p>
                    <p>Distance: ${overpass.distance}m</p>
                </div>
            `);
            
            roadRiskMarkers.push(marker);
        });
        
        // Add tunnel markers (YELLOW - moderate risk at entrances)
        data.tunnels?.forEach(tunnel => {
            const marker = L.marker(tunnel.center, {
                icon: L.divIcon({
                    className: 'road-risk-marker tunnel-marker',
                    html: '<span class="marker-icon">🚇</span>',
                    iconSize: [26, 26]
                })
            }).addTo(map);
            
            marker.bindPopup(`
                <div class="risk-popup">
                    <h3>⚠️ TUNNEL ENTRANCE</h3>
                    <p><strong>${tunnel.name}</strong></p>
                    <p>Ice forms at temperature transitions</p>
                    <p>Distance: ${tunnel.distance}m</p>
                </div>
            `);
            
            roadRiskMarkers.push(marker);
        });
        
        // Update hazards card
        updateHazardsDisplay(data);
        
        const totalHazards = (data.bridges?.length || 0) + 
                           (data.overpasses?.length || 0) + 
                           (data.tunnels?.length || 0);
        
        if (totalHazards > 0) {
            showAlert(`Found ${totalHazards} road hazards nearby`, 'warning');
        } else {
            showAlert('No major road hazards detected nearby', 'success');
        }
        
    } catch (error) {
        console.error('❌ Road risk fetch failed:', error);
        showAlert('Unable to load road risk data', 'error');
    }
}

function clearRoadRiskMarkers() {
    roadRiskMarkers.forEach(marker => map.removeLayer(marker));
    roadRiskMarkers = [];
}

function updateHazardsDisplay(data) {
    const content = document.getElementById('hazards-content');
    
    const totalBridges = data.bridges?.length || 0;
    const totalOverpasses = data.overpasses?.length || 0;
    const totalTunnels = data.tunnels?.length || 0;
    const totalCurves = data.dangerous_curves?.length || 0;
    
    if (totalBridges + totalOverpasses + totalTunnels === 0) {
        content.innerHTML = `
            <div class="no-hazards">
                <span class="success-icon">✅</span>
                <p>No major road hazards detected within 5km</p>
            </div>
        `;
        return;
    }
    
    let html = '<div class="hazards-list">';
    
    if (totalBridges > 0) {
        const closest = data.bridges[0];
        html += `
            <div class="hazard-item critical">
                <span class="hazard-icon">🌉</span>
                <div class="hazard-details">
                    <div class="hazard-title">⚠️ ${totalBridges} Bridge${totalBridges > 1 ? 's' : ''} Nearby</div>
                    <div class="hazard-subtitle">Closest: ${closest.name} (${closest.distance}m)</div>
                    <div class="hazard-warning">Bridges freeze FIRST - even if roads are clear!</div>
                </div>
            </div>
        `;
    }
    
    if (totalOverpasses > 0) {
        const closest = data.overpasses[0];
        html += `
            <div class="hazard-item high">
                <span class="hazard-icon">🛣️</span>
                <div class="hazard-details">
                    <div class="hazard-title">${totalOverpasses} Overpass${totalOverpasses > 1 ? 'es' : ''}</div>
                    <div class="hazard-subtitle">Closest: ${closest.name} (${closest.distance}m)</div>
                    <div class="hazard-warning">Elevated roads freeze before ground level</div>
                </div>
            </div>
        `;
    }
    
    if (totalTunnels > 0) {
        html += `
            <div class="hazard-item medium">
                <span class="hazard-icon">🚇</span>
                <div class="hazard-details">
                    <div class="hazard-title">${totalTunnels} Tunnel${totalTunnels > 1 ? 's' : ''}</div>
                    <div class="hazard-warning">Ice at temperature transitions</div>
                </div>
            </div>
        `;
    }
    
    if (totalCurves > 0) {
        html += `
            <div class="hazard-item medium">
                <span class="hazard-icon">🔄</span>
                <div class="hazard-details">
                    <div class="hazard-title">${totalCurves} Dangerous Curve${totalCurves > 1 ? 's' : ''}</div>
                    <div class="hazard-warning">Reduce speed if icy</div>
                </div>
            </div>
        `;
    }
    
    html += '</div>';
    content.innerHTML = html;
}

// View switching (for future multi-view support)
function switchView(view) {
    currentView = view;
    
    // Update active nav button
    document.querySelectorAll('.nav-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    document.querySelector(`[data-view="${view}"]`).classList.add('active');
    
    // Scroll to relevant section
    if (view === 'map') {
        document.querySelector('.map-card').scrollIntoView({ behavior: 'smooth' });
    } else if (view === 'alerts') {
        document.querySelector('.activity-card').scrollIntoView({ behavior: 'smooth' });
    } else {
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }
}

// Periodic updates
function startPeriodicUpdates() {
    // Update weather every 5 minutes
    setInterval(() => {
        if (currentLocation.lat && currentLocation.lng) {
            fetchWeatherData();
            addActivityItem('Auto-refresh');
        }
    }, 300000); // 5 minutes
    
    // Check ML status every minute
    setInterval(() => {
        checkMLStatus();
    }, 60000); // 1 minute
    
    // Update road risks every 10 minutes (if layer is enabled)
    setInterval(() => {
        if (document.getElementById('road-risk-layer').checked && currentLocation.lat) {
            fetchRoadRisks();
        }
    }, 600000); // 10 minutes
}

// Handle app install prompt
let deferredPrompt;

window.addEventListener('beforeinstallprompt', (e) => {
    e.preventDefault();
    deferredPrompt = e;
    
    // Show install button/banner
    showAlert('Add Black Ice Alert to your home screen for the best experience!', 'info');
});

window.addEventListener('appinstalled', () => {
    console.log('✅ PWA installed successfully');
    addActivityItem('App installed to home screen');
    deferredPrompt = null;
});

console.log('📱 Mobile app script loaded');
