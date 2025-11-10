// Mobile PWA - Main JavaScript
// Quantum Black Ice Detection System - Mobile Version

// Configuration with overrides
const __params = new URLSearchParams(window.location.search);
const __API_OVERRIDE = __params.get('api');
const __WS_OVERRIDE = __params.get('ws');

const API_BASE = (typeof window !== 'undefined' && window.API_BASE_URL)
    ? window.API_BASE_URL
    : (__API_OVERRIDE || (window.location.origin.includes('localhost') 
        ? 'http://localhost:5000' 
        : window.location.origin));

const WS_BASE = (typeof window !== 'undefined' && window.WS_BASE_URL)
    ? window.WS_BASE_URL
    : (__WS_OVERRIDE || API_BASE);

// App version for cache detection
const APP_VERSION = '3.0.1-accuracy-upgrades';

console.log('🔧 API_BASE configured as:', API_BASE);
console.log('🌍 Current origin:', window.location.origin);
console.log('📱 App version:', APP_VERSION);

// Check if accuracy upgrades are available
if (typeof getAccuracyUpgrades !== 'function') {
    console.error('❌ CRITICAL: Accuracy upgrade functions missing! Browser cache issue detected.');
    console.warn('🔄 Please do a hard refresh: Ctrl+Shift+R (Windows) or Cmd+Shift+R (Mac)');
    
    // Show alert to user
    setTimeout(() => {
        if (typeof showAlert === 'function') {
            showAlert('⚠️ App update detected! Please refresh your browser (Ctrl+Shift+R) to load new features.', 'warning');
        } else {
            alert('⚠️ App update detected! Please refresh your browser (Ctrl+Shift+R or pull down to refresh on mobile) to load new accuracy features.');
        }
    }, 2000);
} else {
    console.log('✅ Accuracy upgrades loaded successfully');
}

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
    // Prefer polling on localhost/dev to avoid websocket upgrade errors with
    // Werkzeug dev server. Use real websockets in production.
    const wsTransports = (API_BASE.includes('localhost') || API_BASE.includes('127.0.0.1'))
        ? ['polling']
        : ['websocket', 'polling'];
    
    socket = io(WS_BASE, {
        transports: wsTransports,
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
        
        // Get advanced predictions (BIFI, QFPM, IoT Mesh)
        getAdvancedPredictions(data);
        
        // Get new accuracy upgrade predictions
        getAccuracyUpgrades(data);
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

// ============ ADVANCED PREDICTIONS ============

// Get all advanced predictions in one call
async function getAdvancedPredictions(weatherData) {
    try {
        // Try the combined endpoint first
        const response = await fetch(`${API_BASE}/api/advanced/predict`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                weather_data: weatherData,
                lat: currentLocation.lat,
                lon: currentLocation.lng
            })
        });
        
        if (response.ok) {
            const data = await response.json();
            console.log('✅ Advanced predictions received:', data);
            
            if (data.success) {
                updateBIFIDisplay(data.predictions.bifi);
                updateQFPMDisplay(data.predictions.qfpm);
                if (data.predictions.mesh) {
                    updateMeshDisplay(data.predictions.mesh);
                }
                
                // Initialize IoT sensors if not already done
                if (!window.sensorsInitialized && currentLocation.lat) {
                    initializeMeshNetwork();
                }
                return; // Success, exit early
            }
        }
    } catch (error) {
        console.error('❌ Advanced predictions error:', error);
    }
    
    // Fallback: Call endpoints individually
    console.log('⚠️ Using fallback individual endpoints');
    await getBIFIPrediction(weatherData);
    await getQFPMPrediction(weatherData);
    if (!window.sensorsInitialized && currentLocation.lat) {
        initializeMeshNetwork();
    }
}

// Fallback: Get BIFI individually
async function getBIFIPrediction(weatherData) {
    try {
        const response = await fetch(`${API_BASE}/api/bifi/calculate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ weather_data: weatherData })
        });
        
        if (response.ok) {
            const data = await response.json();
            if (data.success && data.bifi) {
                // Add interpretation to bifi object
                data.bifi.interpretation = data.interpretation;
                updateBIFIDisplay(data.bifi);
            }
        }
    } catch (error) {
        console.error('❌ BIFI error:', error);
    }
}

// Fallback: Get QFPM individually
async function getQFPMPrediction(weatherData) {
    try {
        const response = await fetch(`${API_BASE}/api/qfpm/predict`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ weather_data: weatherData })
        });
        
        if (response.ok) {
            const data = await response.json();
            if (data.success && data.summary) {
                updateQFPMDisplay({ summary: data.summary });
            }
        }
    } catch (error) {
        console.error('❌ QFPM error:', error);
    }
}

// Update BIFI display
function updateBIFIDisplay(bifiData) {
    if (!bifiData) return;
    
    const score = bifiData.bifi_score;
    const level = bifiData.risk_level;
    const interpretation = bifiData.interpretation;
    const components = bifiData.components;
    
    // Update score circle
    document.getElementById('bifi-score').textContent = Math.round(score);
    document.getElementById('bifi-level').textContent = level;
    document.getElementById('bifi-level').style.color = bifiData.risk_color;
    
    // Add risk level class
    const bifiCard = document.querySelector('.bifi-card');
    bifiCard.className = 'card bifi-card bifi-' + level.toLowerCase();
    
    // Update interpretation
    document.getElementById('bifi-interpretation').textContent = interpretation;
    
    // Update component bars
    updateComponentBar('temp', components.temperature);
    updateComponentBar('humidity', components.humidity);
    updateComponentBar('dewpoint', components.dew_point);
    updateComponentBar('wind', components.wind);
    
    console.log(`📊 BIFI: ${score}/100 (${level})`);
}

function updateComponentBar(name, value) {
    const bar = document.getElementById(`bifi-${name}-bar`);
    const val = document.getElementById(`bifi-${name}-val`);
    
    if (bar && val) {
        bar.style.width = value + '%';
        val.textContent = Math.round(value);
        
        // Color based on value
        if (value > 70) {
            bar.style.background = 'linear-gradient(90deg, #FF4500, #8B0000)';
        } else if (value > 40) {
            bar.style.background = 'linear-gradient(90deg, #FFD700, #FF4500)';
        } else {
            bar.style.background = 'linear-gradient(90deg, #32CD32, #9ACD32)';
        }
    }
}

// Update QFPM forecast display
function updateQFPMDisplay(qfpmData) {
    if (!qfpmData || !qfpmData.summary) return;
    
    const summary = qfpmData.summary;
    const probs = summary.freeze_probability;
    
    // Update 30-min forecast
    updateForecastItem('30', probs['30_min']);
    updateForecastItem('60', probs['60_min']);
    updateForecastItem('90', probs['90_min']);
    
    // Update alert message
    document.getElementById('qfpm-alert').textContent = summary.alert_message;
    document.getElementById('qfpm-alert').style.borderColor = summary.color;
    
    // Highlight peak risk time
    const peakTime = summary.peak_risk_time;
    document.querySelectorAll('.forecast-item').forEach(item => {
        item.style.borderLeftColor = 'transparent';
    });
    document.getElementById(`forecast-${peakTime}`).style.borderLeftColor = summary.color;
    
    console.log(`⚛️ QFPM: Peak risk at ${peakTime} (${summary.risk_level})`);
}

function updateForecastItem(timeKey, probability) {
    const probEl = document.getElementById(`qfpm-${timeKey}`);
    const barEl = document.getElementById(`qfpm-${timeKey}-bar`);
    
    if (probEl && barEl) {
        probEl.textContent = probability + '%';
        barEl.style.width = probability + '%';
        
        // Color based on probability
        if (probability > 70) {
            barEl.style.background = 'linear-gradient(90deg, #8B0000, #FF0000)';
        } else if (probability > 40) {
            barEl.style.background = 'linear-gradient(90deg, #FFD700, #FF4500)';
        } else {
            barEl.style.background = 'linear-gradient(90deg, #667eea, #764ba2)';
        }
    }
}

// Update IoT mesh network display
function updateMeshDisplay(meshData) {
    if (!meshData) return;
    
    document.getElementById('mesh-sensor-count').textContent = meshData.nearby_sensors || 0;
    document.getElementById('mesh-confidence').textContent = meshData.confidence || 'LOW';
    document.getElementById('mesh-freeze-alerts').textContent = meshData.freeze_alerts?.length || 0;
    document.getElementById('mesh-message').textContent = meshData.message || '🌐 No sensors in area';
    
    // Color-code confidence
    const confidenceEl = document.getElementById('mesh-confidence');
    if (meshData.confidence === 'HIGH') {
        confidenceEl.style.color = '#32CD32';
    } else if (meshData.confidence === 'MEDIUM') {
        confidenceEl.style.color = '#FFD700';
    } else {
        confidenceEl.style.color = '#FF4500';
    }
    
    console.log(`🌐 Mesh: ${meshData.nearby_sensors} sensors, ${meshData.confidence} confidence`);
}

// ==================== NEW ACCURACY UPGRADES ====================

// Get all accuracy upgrade data
async function getAccuracyUpgrades(weatherData) {
    if (!currentLocation.lat || !currentLocation.lng) return;
    
    console.log('🎯 Fetching accuracy upgrades...');
    
    // Fetch all new data in parallel
    await Promise.all([
        getOvernightPrediction(weatherData),
        getWetPavementStatus(),
        getRoadTemperature(),
        getPrecipitationType(),
        getBridgeFreezeRisk(weatherData)
    ]);
}

// Overnight Freeze Prediction
async function getOvernightPrediction(weatherData) {
    try {
        const response = await fetch(`${API_BASE}/api/overnight/freeze-prediction`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                current_temp_f: weatherData.temperature,
                dew_point_f: weatherData.dew_point,
                wind_speed_mph: weatherData.wind_speed,
                cloud_cover_percent: weatherData.cloud_cover || 0
            })
        });
        
        if (response.ok) {
            const data = await response.json();
            if (data.success && data.overnight_prediction) {
                updateOvernightDisplay(data.overnight_prediction);
            }
        }
    } catch (error) {
        console.error('❌ Overnight prediction error:', error);
    }
}

// Wet Pavement Status
async function getWetPavementStatus() {
    try {
        const response = await fetch(
            `${API_BASE}/api/precipitation/recent?lat=${currentLocation.lat}&lon=${currentLocation.lng}&hours_back=6`
        );
        
        if (response.ok) {
            const data = await response.json();
            if (data.success && data.recent_precipitation) {
                updateWetPavementDisplay(data.recent_precipitation);
            }
        }
    } catch (error) {
        console.error('❌ Wet pavement error:', error);
    }
}

// Real Road Temperature from RWIS
async function getRoadTemperature() {
    try {
        const response = await fetch(
            `${API_BASE}/api/rwis/road-temp?lat=${currentLocation.lat}&lon=${currentLocation.lng}&radius_miles=25`
        );
        
        if (response.ok) {
            const data = await response.json();
            if (data.success && data.road_temp) {
                updateRoadTempDisplay(data.road_temp);
            }
        }
    } catch (error) {
        console.error('❌ Road temp error:', error);
    }
}

// Precipitation Type
async function getPrecipitationType() {
    try {
        const response = await fetch(
            `${API_BASE}/api/precipitation/type?lat=${currentLocation.lat}&lon=${currentLocation.lng}`
        );
        
        if (response.ok) {
            const data = await response.json();
            if (data.success && data.precipitation_type) {
                updatePrecipTypeDisplay(data.precipitation_type);
            }
        }
    } catch (error) {
        console.error('❌ Precipitation type error:', error);
    }
}

// Bridge Freeze Risk
async function getBridgeFreezeRisk(weatherData) {
    try {
        const response = await fetch(`${API_BASE}/api/bridge/freeze-risk`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                current_temp_f: weatherData.temperature,
                wind_speed_mph: weatherData.wind_speed,
                humidity_percent: weatherData.humidity,
                bridge_type: 'steel',
                bridge_length_ft: 200
            })
        });
        
        if (response.ok) {
            const data = await response.json();
            if (data.success && data.bridge_freeze) {
                updateBridgeDisplay(data.bridge_freeze);
            }
        }
    } catch (error) {
        console.error('❌ Bridge freeze error:', error);
    }
}

// Update Overnight Freeze Display
function updateOvernightDisplay(overnightData) {
    if (!overnightData) return;
    
    const freezeTimeEl = document.getElementById('freeze-time');
    const countdownEl = document.getElementById('freeze-countdown');
    const minTempEl = document.getElementById('overnight-min-temp');
    const coolingRateEl = document.getElementById('cooling-rate');
    const riskBadgeEl = document.getElementById('overnight-risk-badge');
    const riskLevelEl = document.getElementById('overnight-risk-level');
    const messageEl = document.getElementById('overnight-message');
    
    if (overnightData.will_freeze_tonight) {
        const freezeTime = new Date(overnightData.freeze_time);
        const hours = freezeTime.getHours();
        const minutes = freezeTime.getMinutes();
        const ampm = hours >= 12 ? 'PM' : 'AM';
        const displayHours = hours % 12 || 12;
        
        freezeTimeEl.textContent = `${displayHours}:${minutes.toString().padStart(2, '0')} ${ampm}`;
        countdownEl.textContent = `in ${overnightData.hours_until_freeze.toFixed(1)} hours`;
        
        // Risk level styling
        const riskLevel = overnightData.risk_level.toUpperCase();
        riskLevelEl.textContent = riskLevel;
        
        if (riskLevel === 'CRITICAL') {
            riskBadgeEl.style.background = '#dc2626';
        } else if (riskLevel === 'HIGH') {
            riskBadgeEl.style.background = '#f59e0b';
        } else if (riskLevel === 'MODERATE') {
            riskBadgeEl.style.background = '#eab308';
        } else {
            riskBadgeEl.style.background = '#10b981';
        }
        
        messageEl.textContent = overnightData.warning_message || '🌙 Roads will freeze overnight';
    } else {
        freezeTimeEl.textContent = 'No freeze';
        countdownEl.textContent = 'expected tonight';
        riskLevelEl.textContent = 'LOW';
        riskBadgeEl.style.background = '#10b981';
        messageEl.textContent = '✅ Roads should remain clear overnight';
    }
    
    minTempEl.textContent = `${overnightData.minimum_temp_f.toFixed(0)}°F`;
    coolingRateEl.textContent = `${overnightData.cooling_rate_per_hour.toFixed(1)}°F/hr`;
    
    console.log('🌙 Overnight prediction updated:', overnightData.freeze_time);
}

// Update Wet Pavement Display
function updateWetPavementDisplay(precipData) {
    if (!precipData) return;
    
    const indicatorEl = document.getElementById('pavement-wet-indicator');
    const statusTextEl = document.getElementById('pavement-status-text');
    const multiplierEl = document.getElementById('risk-multiplier');
    const hoursSinceEl = document.getElementById('hours-since-precip');
    const warningEl = document.getElementById('wet-pavement-warning');
    
    if (precipData.pavement_likely_wet) {
        indicatorEl.querySelector('.indicator-circle').style.background = '#3b82f6';
        statusTextEl.textContent = 'PAVEMENT WET';
        statusTextEl.style.color = '#3b82f6';
        
        const multiplier = precipData.black_ice_risk_multiplier.toFixed(1);
        multiplierEl.textContent = `${multiplier}x`;
        multiplierEl.style.color = multiplier >= 2.5 ? '#dc2626' : '#f59e0b';
        
        hoursSinceEl.textContent = `${precipData.hours_since_precipitation.toFixed(1)} hours ago`;
        warningEl.textContent = precipData.warning_message || '⚠️ Wet pavement increases black ice risk';
        warningEl.style.color = '#f59e0b';
    } else {
        indicatorEl.querySelector('.indicator-circle').style.background = '#10b981';
        statusTextEl.textContent = 'PAVEMENT DRY';
        statusTextEl.style.color = '#10b981';
        
        multiplierEl.textContent = '1.0x';
        multiplierEl.style.color = '#10b981';
        
        if (precipData.had_recent_precipitation) {
            hoursSinceEl.textContent = `${precipData.hours_since_precipitation.toFixed(1)} hours ago (evaporated)`;
            warningEl.textContent = '✅ Pavement has dried';
        } else {
            hoursSinceEl.textContent = 'No recent precipitation';
            warningEl.textContent = '✅ No recent precipitation detected';
        }
        warningEl.style.color = '#10b981';
    }
    
    console.log('💧 Wet pavement updated:', precipData.pavement_likely_wet);
}

// Update Road Temperature Display
function updateRoadTempDisplay(roadTempData) {
    if (!roadTempData) return;
    
    const tempValueEl = document.getElementById('road-temp-value');
    const distanceEl = document.getElementById('sensor-distance');
    const confidenceEl = document.getElementById('sensor-confidence');
    const airTempEl = document.getElementById('air-temp-compare');
    const diffEl = document.getElementById('temp-difference');
    const messageEl = document.getElementById('road-temp-message');
    
    if (roadTempData.road_temp_f !== null) {
        tempValueEl.textContent = `${roadTempData.road_temp_f.toFixed(0)}°F`;
        
        if (roadTempData.road_temp_f <= 32) {
            tempValueEl.style.color = '#dc2626';
        } else if (roadTempData.road_temp_f <= 35) {
            tempValueEl.style.color = '#f59e0b';
        } else {
            tempValueEl.style.color = '#10b981';
        }
        
        distanceEl.textContent = `${roadTempData.distance_miles.toFixed(1)} mi away`;
        
        const confidence = roadTempData.confidence.toUpperCase();
        confidenceEl.textContent = confidence;
        
        if (confidence === 'HIGH') {
            confidenceEl.style.background = '#10b981';
        } else if (confidence === 'MEDIUM') {
            confidenceEl.style.background = '#f59e0b';
        } else {
            confidenceEl.style.background = '#dc2626';
        }
        
        if (roadTempData.air_temp_f !== null) {
            airTempEl.textContent = `${roadTempData.air_temp_f.toFixed(0)}°F`;
            const diff = roadTempData.air_temp_f - roadTempData.road_temp_f;
            diffEl.textContent = `${diff >= 0 ? '+' : ''}${diff.toFixed(0)}°F`;
            
            if (Math.abs(diff) >= 5) {
                diffEl.style.color = '#f59e0b';
            }
        }
        
        messageEl.textContent = roadTempData.message || '✅ Real road surface temperature from DOT sensor';
        messageEl.style.color = '#10b981';
    } else {
        tempValueEl.textContent = '--°F';
        distanceEl.textContent = 'No sensors nearby';
        confidenceEl.textContent = 'N/A';
        confidenceEl.style.background = '#6b7280';
        messageEl.textContent = '⚠️ No RWIS sensors within 25 miles - using air temperature';
        messageEl.style.color = '#f59e0b';
    }
    
    console.log('🌡️ Road temp updated:', roadTempData.road_temp_f);
}

// Update Precipitation Type Display
function updatePrecipTypeDisplay(precipTypeData) {
    if (!precipTypeData) return;
    
    const iconEl = document.getElementById('precip-icon');
    const typeEl = document.getElementById('precip-type');
    const riskBadgeEl = document.getElementById('precip-risk-badge');
    const riskLevelEl = document.getElementById('precip-risk-level');
    const hourlyEl = document.getElementById('precip-hourly');
    const warningEl = document.getElementById('precip-warning');
    
    const precipType = precipTypeData.current_type;
    
    // Set icon based on type
    const icons = {
        'none': '☀️',
        'rain': '🌧️',
        'snow': '❄️',
        'sleet': '🌨️',
        'freezing_rain': '🧊',
        'unknown': '🌫️'
    };
    
    iconEl.textContent = icons[precipType] || '❓';
    typeEl.textContent = precipType.replace('_', ' ').toUpperCase();
    
    // Risk level styling
    const riskLevel = precipTypeData.black_ice_risk.toUpperCase();
    riskLevelEl.textContent = `${riskLevel} RISK`;
    
    if (riskLevel === 'CRITICAL') {
        riskBadgeEl.style.background = '#dc2626';
        typeEl.style.color = '#dc2626';
        warningEl.textContent = '🚨 FREEZING RAIN - IMMEDIATE BLACK ICE DANGER!';
        warningEl.style.color = '#dc2626';
        warningEl.style.fontWeight = 'bold';
    } else if (riskLevel === 'HIGH') {
        riskBadgeEl.style.background = '#f59e0b';
        typeEl.style.color = '#f59e0b';
        warningEl.textContent = precipTypeData.warning_message || '⚠️ High black ice risk';
        warningEl.style.color = '#f59e0b';
    } else if (riskLevel === 'MODERATE') {
        riskBadgeEl.style.background = '#eab308';
        typeEl.style.color = '#eab308';
        warningEl.textContent = precipTypeData.warning_message || 'ℹ️ Moderate black ice risk';
        warningEl.style.color = '#eab308';
    } else {
        riskBadgeEl.style.background = '#10b981';
        typeEl.style.color = '#10b981';
        warningEl.textContent = '✅ Low black ice risk from precipitation';
        warningEl.style.color = '#10b981';
    }
    
    // Update hourly forecast (show next 3 hours)
    if (precipTypeData.forecast_next_hour) {
        const hourlyHTML = precipTypeData.forecast_next_hour.slice(0, 3).map(hour => {
            const time = new Date(hour.time).getHours();
            const ampm = time >= 12 ? 'PM' : 'AM';
            const displayTime = (time % 12 || 12) + ampm;
            
            return `
                <div class="hour-item">
                    <div class="hour-time">${displayTime}</div>
                    <div class="hour-type">${icons[hour.type] || '❓'} ${hour.type.replace('_', ' ')}</div>
                </div>
            `;
        }).join('');
        
        hourlyEl.innerHTML = hourlyHTML;
    }
    
    console.log('🌨️ Precipitation type updated:', precipType);
}

// Update Bridge Freeze Display
function updateBridgeDisplay(bridgeData) {
    if (!bridgeData) return;
    
    const freezeTempEl = document.getElementById('bridge-freeze-temp');
    const dangerZoneEl = document.getElementById('bridge-danger-zone');
    const factorsEl = document.getElementById('bridge-factors');
    const warningEl = document.getElementById('bridge-warning');
    
    freezeTempEl.textContent = `${bridgeData.bridge_freeze_temp_f.toFixed(0)}°F`;
    
    const tempDiff = bridgeData.bridge_freeze_temp_f - 32;
    dangerZoneEl.textContent = `${tempDiff.toFixed(0)}°F warmer`;
    
    // Styling based on freeze temp
    if (bridgeData.bridge_freeze_temp_f <= 35) {
        freezeTempEl.style.color = '#dc2626';
    } else if (bridgeData.bridge_freeze_temp_f <= 38) {
        freezeTempEl.style.color = '#f59e0b';
    } else {
        freezeTempEl.style.color = '#eab308';
    }
    
    // Show risk factors
    const factors = [];
    if (bridgeData.wind_impact_f > 1) {
        factors.push(`High wind (+${bridgeData.wind_impact_f.toFixed(1)}°F)`);
    }
    if (bridgeData.humidity_impact_f > 1) {
        factors.push(`High humidity (+${bridgeData.humidity_impact_f.toFixed(1)}°F)`);
    }
    if (bridgeData.material_offset_f >= 3) {
        factors.push(`Steel bridge (+${bridgeData.material_offset_f}°F)`);
    }
    
    if (factors.length > 0) {
        factorsEl.innerHTML = factors.map(f => `<div class="factor-item">• ${f}</div>`).join('');
    } else {
        factorsEl.innerHTML = '<div class="factor-item">• Standard conditions</div>';
    }
    
    // Warning message
    if (bridgeData.currently_frozen) {
        warningEl.textContent = '🚨 BRIDGES ARE FREEZING NOW!';
        warningEl.style.color = '#dc2626';
        warningEl.style.fontWeight = 'bold';
    } else if (bridgeData.will_freeze_soon) {
        warningEl.textContent = bridgeData.warning_message || `⚠️ Bridges will freeze in ${bridgeData.minutes_until_freeze} minutes`;
        warningEl.style.color = '#f59e0b';
    } else {
        warningEl.textContent = bridgeData.warning_message || '✅ Bridges above freezing temperature';
        warningEl.style.color = '#10b981';
    }
    
    console.log('🌉 Bridge freeze updated:', bridgeData.bridge_freeze_temp_f);
}

// ==================== END ACCURACY UPGRADES ====================

// Initialize IoT mesh network
async function initializeMeshNetwork() {
    if (!currentLocation.lat || !currentLocation.lng) return;
    
    try {
        const response = await fetch(`${API_BASE}/api/mesh/initialize`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                lat: currentLocation.lat,
                lon: currentLocation.lng,
                radius_miles: 10,
                sensor_count: 15
            })
        });
        
        if (!response.ok) throw new Error('Mesh initialization failed');
        
        const data = await response.json();
        console.log('✅ IoT Mesh initialized:', data.sensors_created, 'sensors');
        
        window.sensorsInitialized = true;
        
        // Simulate sensor readings
        simulateSensorReadings();
    } catch (error) {
        console.error('❌ Mesh initialization error:', error);
    }
}

// Simulate sensor readings based on current weather
async function simulateSensorReadings() {
    try {
        const weatherResponse = await fetch(
            `${API_BASE}/api/weather/current?lat=${currentLocation.lat}&lon=${currentLocation.lng}`
        );
        const weatherData = await weatherResponse.json();
        
        const response = await fetch(`${API_BASE}/api/mesh/simulate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                weather_data: weatherData
            })
        });
        
        if (!response.ok) throw new Error('Sensor simulation failed');
        
        const data = await response.json();
        console.log('✅ Simulated', data.sensors_updated, 'sensor readings');
        
        // Fetch updated sensor data
        fetchSensorData();
    } catch (error) {
        console.error('❌ Sensor simulation error:', error);
    }
}

// Fetch and display sensor data on map
let sensorMarkers = [];
let showingSensors = false;

async function fetchSensorData() {
    if (!currentLocation.lat || !currentLocation.lng) return;
    
    try {
        const response = await fetch(
            `${API_BASE}/api/mesh/sensors?lat=${currentLocation.lat}&lon=${currentLocation.lng}&radius_miles=10`
        );
        
        if (!response.ok) throw new Error('Sensor fetch failed');
        
        const data = await response.json();
        
        if (data.success && data.sensors) {
            window.sensorData = data.sensors;
            updateMeshDisplay(data.summary);
            
            if (showingSensors) {
                displaySensorsOnMap(data.sensors);
            }
        }
    } catch (error) {
        console.error('❌ Sensor fetch error:', error);
    }
}

// Display sensor markers on map
function displaySensorsOnMap(sensors) {
    // Clear existing markers
    sensorMarkers.forEach(marker => map.removeLayer(marker));
    sensorMarkers = [];
    
    sensors.forEach(sensor => {
        const isFreezing = sensor.readings.surface_temp <= 32;
        
        const marker = L.marker([sensor.location.lat, sensor.location.lon], {
            icon: L.divIcon({
                className: isFreezing ? 'sensor-marker freeze-alert' : 'sensor-marker',
                html: '🌡️',
                iconSize: [32, 32]
            })
        });
        
        // Create popup with sensor data
        const popup = `
            <div class="sensor-popup">
                <div class="popup-title">${sensor.type.replace('_', ' ').toUpperCase()}</div>
                <div class="popup-data">
                    <div class="data-item">
                        <span class="data-label">Air Temp</span>
                        <span class="data-value">${sensor.readings.temperature?.toFixed(1)}°F</span>
                    </div>
                    <div class="data-item">
                        <span class="data-label">Surface</span>
                        <span class="data-value">${sensor.readings.surface_temp?.toFixed(1)}°F</span>
                    </div>
                    <div class="data-item">
                        <span class="data-label">Friction</span>
                        <span class="data-value">${sensor.readings.friction_index?.toFixed(2)}</span>
                    </div>
                    <div class="data-item">
                        <span class="data-label">Humidity</span>
                        <span class="data-value">${sensor.readings.humidity?.toFixed(0)}%</span>
                    </div>
                </div>
                <div style="margin-top: 8px; font-size: 11px; color: #666;">
                    ${sensor.distance_miles.toFixed(1)} mi away
                </div>
            </div>
        `;
        
        marker.bindPopup(popup);
        marker.addTo(map);
        sensorMarkers.push(marker);
    });
    
    console.log('📍 Displayed', sensors.length, 'sensor markers');
}

// Toggle sensor display
function toggleSensorsOnMap() {
    showingSensors = !showingSensors;
    
    if (showingSensors) {
        if (window.sensorData) {
            displaySensorsOnMap(window.sensorData);
        } else {
            fetchSensorData();
        }
        document.getElementById('toggle-sensors-btn').querySelector('.btn-text').textContent = 'Hide Sensors';
    } else {
        sensorMarkers.forEach(marker => map.removeLayer(marker));
        sensorMarkers = [];
        document.getElementById('toggle-sensors-btn').querySelector('.btn-text').textContent = 'Show Sensors on Map';
    }
}

// Event listeners
function setupEventListeners() {
    // Refresh button
    document.getElementById('refresh-btn').addEventListener('click', () => {
        fetchWeatherData();
        addActivityItem('Manually refreshed');
    });
    
    // Toggle sensors button
    document.getElementById('toggle-sensors-btn').addEventListener('click', toggleSensorsOnMap);
    
    // Settings Modal Management
    const settingsModal = document.getElementById('settings-modal');
    const settingsBtn = document.getElementById('settings-btn');
    const settingsClose = document.getElementById('settings-close');
    const saveSettingsBtn = document.getElementById('save-settings');
    
    // Default settings
    const defaultSettings = {
        soundEnabled: true,
        vibrationEnabled: true,
        tempUnit: 'F',
        distanceUnit: 'mi',
        autoRefreshEnabled: true,
        refreshInterval: 60,
        mapStyle: 'street',
        showTraffic: true,
        showBridges: true,
        highRiskThreshold: 60,
        mediumRiskThreshold: 30
    };
    
    let currentSettings = { ...defaultSettings };
    
    // Open settings modal
    settingsBtn.addEventListener('click', () => {
        settingsModal.style.display = 'flex';
        loadSettings();
    });
    
    // Close modal
    settingsClose.addEventListener('click', () => {
        settingsModal.style.display = 'none';
    });
    
    // Close on background click
    settingsModal.addEventListener('click', (e) => {
        if (e.target === settingsModal) {
            settingsModal.style.display = 'none';
        }
    });
    
    // Load settings from localStorage
    function loadSettings() {
        const saved = localStorage.getItem('quantumBlackIceSettings');
        if (saved) {
            currentSettings = { ...defaultSettings, ...JSON.parse(saved) };
        }
        
        // Apply settings to UI
        document.getElementById('sound-enabled').checked = currentSettings.soundEnabled;
        document.getElementById('vibration-enabled').checked = currentSettings.vibrationEnabled;
        document.getElementById('temp-unit').value = currentSettings.tempUnit;
        document.getElementById('distance-unit').value = currentSettings.distanceUnit;
        document.getElementById('auto-refresh-enabled').checked = currentSettings.autoRefreshEnabled;
        document.getElementById('refresh-interval').value = currentSettings.refreshInterval;
        document.getElementById('map-style').value = currentSettings.mapStyle;
        document.getElementById('show-traffic').checked = currentSettings.showTraffic;
        document.getElementById('show-bridges').checked = currentSettings.showBridges;
        document.getElementById('high-risk-threshold').value = currentSettings.highRiskThreshold;
        document.getElementById('medium-risk-threshold').value = currentSettings.mediumRiskThreshold;
        
        // Update slider values
        document.getElementById('high-risk-value').textContent = currentSettings.highRiskThreshold + '%';
        document.getElementById('medium-risk-value').textContent = currentSettings.mediumRiskThreshold + '%';
    }
    
    // Update slider values in real-time
    document.getElementById('high-risk-threshold').addEventListener('input', (e) => {
        document.getElementById('high-risk-value').textContent = e.target.value + '%';
    });
    
    document.getElementById('medium-risk-threshold').addEventListener('input', (e) => {
        document.getElementById('medium-risk-value').textContent = e.target.value + '%';
    });
    
    // Save settings
    saveSettingsBtn.addEventListener('click', () => {
        // Gather all settings
        currentSettings = {
            soundEnabled: document.getElementById('sound-enabled').checked,
            vibrationEnabled: document.getElementById('vibration-enabled').checked,
            tempUnit: document.getElementById('temp-unit').value,
            distanceUnit: document.getElementById('distance-unit').value,
            autoRefreshEnabled: document.getElementById('auto-refresh-enabled').checked,
            refreshInterval: parseInt(document.getElementById('refresh-interval').value),
            mapStyle: document.getElementById('map-style').value,
            showTraffic: document.getElementById('show-traffic').checked,
            showBridges: document.getElementById('show-bridges').checked,
            highRiskThreshold: parseInt(document.getElementById('high-risk-threshold').value),
            mediumRiskThreshold: parseInt(document.getElementById('medium-risk-threshold').value)
        };
        
        // Save to localStorage
        localStorage.setItem('quantumBlackIceSettings', JSON.stringify(currentSettings));
        
        // Apply settings
        applySettings();
        
        // Show success message
        showAlert('✅ Settings saved successfully!', 'success');
        
        // Close modal
        settingsModal.style.display = 'none';
    });
    
    // Apply settings to the app
    function applySettings() {
        // Update auto-refresh interval
        if (window.refreshInterval) {
            clearInterval(window.refreshInterval);
        }
        
        if (currentSettings.autoRefreshEnabled) {
            window.refreshInterval = setInterval(() => {
                updateWeatherDisplay();
                updateQuantumPredictions();
                updateIOTReadings();
                updateTrafficConditions();
            }, currentSettings.refreshInterval * 1000);
        }
        
        // Update displayed temperatures if currently showing
        convertTemperaturesInUI();
        
        // Note: Map style, traffic, and bridge layers would be applied when map is initialized
        // These settings are used by updateMap() and similar functions
    }
    
    // Convert all temperatures in the UI based on unit preference
    function convertTemperaturesInUI() {
        const tempElements = document.querySelectorAll('[data-temp-f]');
        tempElements.forEach(el => {
            const tempF = parseFloat(el.getAttribute('data-temp-f'));
            if (!isNaN(tempF)) {
                if (currentSettings.tempUnit === 'C') {
                    const tempC = (tempF - 32) * 5/9;
                    el.textContent = tempC.toFixed(1) + '°C';
                } else {
                    el.textContent = tempF.toFixed(1) + '°F';
                }
            }
        });
    }
    
    // Helper function to get current temperature unit
    function getCurrentTempUnit() {
        return currentSettings.tempUnit;
    }
    
    // Helper function to format temperature with current unit
    function formatTemperature(tempF) {
        if (currentSettings.tempUnit === 'C') {
            const tempC = (tempF - 32) * 5/9;
            return tempC.toFixed(1) + '°C';
        }
        return tempF.toFixed(1) + '°F';
    }
    
    // Helper function to format distance with current unit
    function formatDistance(miles) {
        if (currentSettings.distanceUnit === 'km') {
            const km = miles * 1.60934;
            return km.toFixed(2) + ' km';
        }
        return miles.toFixed(2) + ' mi';
    }
    
    // Load settings on page load
    loadSettings();
    applySettings();
    
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
