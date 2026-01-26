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
const APP_VERSION = '3.0.2-missing-cards-fix';

console.log('🔧 API_BASE configured as:', API_BASE);
console.log('🌍 Current origin:', window.location.origin);
console.log('📱 App version:', APP_VERSION);

// Populate environment badge
try {
    const badge = document.getElementById('env-badge');
    if (badge) {
        const txt = document.getElementById('env-text');
        txt.textContent = `UI ${APP_VERSION} • API ${(API_BASE.replace('https://','')).split('?')[0]}`;
        badge.style.display = 'flex';
    }
} catch(e) { /* ignore */ }

// Theme toggle
const themeBtn = document.getElementById('theme-btn');
if (themeBtn) {
    themeBtn.addEventListener('click', () => {
        document.documentElement.classList.toggle('theme-light');
        const nowLight = document.documentElement.classList.contains('theme-light');
        console.log('🎨 Theme switched to', nowLight ? 'light' : 'dark');
    });
}

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
    
    // Show manual location option immediately
    showManualLocationPrompt();
    
    // Try to get user location (will override manual if successful)
    getUserLocation();
    
    // Initialize WebSocket
    initializeWebSocket();
    
    // Check ML model status
    checkMLStatus();
    
    // Setup event listeners
    setupEventListeners();
    
    // Start periodic updates
    startPeriodicUpdates();
    
    // Initialize performance optimizations
    initBatteryMonitoring();
    precacheAssets();
    startBackgroundLocationTracking();
    
    // Load 24-hour forecast on startup (after location is set)
    setTimeout(() => {
        if (currentLocation.lat && currentLocation.lng) {
            fetch24HourRiskForecast();
        }
    }, 3000);
    
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

// Helper function to use default location
function useDefaultLocation(reason) {
    console.log('📍 Using default location:', reason);
    currentLocation.lat = 42.3314;
    currentLocation.lng = -83.0458;
    updateLocationText('Detroit, MI (default)');
    
    // Update map to default location
    map.setView([currentLocation.lat, currentLocation.lng], 12);
    
    // Add marker for default location
    if (userMarker) {
        map.removeLayer(userMarker);
    }
    userMarker = L.marker([currentLocation.lat, currentLocation.lng], {
        icon: L.divIcon({
            className: 'user-location-marker',
            html: '<div style="background: #FF6B6B; width: 16px; height: 16px; border-radius: 50%; border: 3px solid white; box-shadow: 0 2px 8px rgba(0,0,0,0.3);"></div>',
            iconSize: [22, 22]
        })
    }).addTo(map);
    
    showAlert(reason + ' Using Detroit, MI. You can manually set your location.', 'warning');
    showManualLocationPrompt();
    
    // Fetch weather data for default location
    fetchWeatherData();
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
        showManualLocationPrompt();
        return;
    }
    
    // Check permission status first
    if (navigator.permissions) {
        try {
            const permissionStatus = await navigator.permissions.query({ name: 'geolocation' });
            console.log('📍 Geolocation permission:', permissionStatus.state);
            
            if (permissionStatus.state === 'denied') {
                console.warn('⚠️ Location permission denied by user');
                showAlert('📍 Location access denied. Please enable in browser settings or enter location manually.', 'warning');
                showManualLocationPrompt();
                return;
            }
        } catch (e) {
            console.log('⚠️ Permission API not available, proceeding with location request');
        }
    }
    
    updateLocationText('Getting location...');
    console.log('📍 Requesting location...');
    
    // Show helpful message for network access
    const isLocalIP = window.location.hostname.match(/^192\.168\.|^10\.|^172\.(1[6-9]|2[0-9]|3[01])\./);
    if (isLocalIP) {
        console.log('💡 Accessing via local IP - some browsers may block geolocation');
        showAlert('💡 If location prompt doesn\'t appear, try accessing via localhost or use manual entry', 'info');
    }
    
    // Add manual timeout fallback (in case browser timeout fails)
    let locationTimeout = setTimeout(() => {
        console.warn('⏰ Manual location timeout triggered (15s)');
        if (!currentLocation.lat || currentLocation.lat === 0) {
            useDefaultLocation('Location request timed out after 15 seconds.');
        }
    }, 15000);
    
    navigator.geolocation.getCurrentPosition(
        async (position) => {
            clearTimeout(locationTimeout);
            currentLocation.lat = position.coords.latitude;
            currentLocation.lng = position.coords.longitude;
            
            console.log('✅ Location obtained:', currentLocation);
            
            // Update location text immediately with coordinates
            updateLocationText(`${currentLocation.lat.toFixed(4)}, ${currentLocation.lng.toFixed(4)}`);
            showAlert('✅ Location detected successfully!', 'success');
            
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
            
            // Get location name (non-blocking)
            reverseGeocode(currentLocation.lat, currentLocation.lng).catch(err => {
                console.warn('Reverse geocoding failed, keeping coordinates:', err);
            });
            
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
            clearTimeout(locationTimeout);
            console.error('❌ Location error:', error);
            
            let errorMessage = 'Unable to get your location. ';
            
            switch(error.code) {
                case error.PERMISSION_DENIED:
                    errorMessage += 'Permission denied.';
                    console.error('📍 User denied location permission');
                    break;
                case error.POSITION_UNAVAILABLE:
                    errorMessage += 'Location unavailable.';
                    console.error('📍 Position unavailable');
                    break;
                case error.TIMEOUT:
                    errorMessage += 'Location request timed out.';
                    console.error('📍 Location timeout');
                    break;
                default:
                    errorMessage += 'Unknown error.';
            }
            
            useDefaultLocation(errorMessage);
        },
        {
            enableHighAccuracy: true,
            timeout: 10000, // 10 seconds timeout
            maximumAge: 300000 // 5 minutes
        }
    );
}

// Show manual location input
function showManualLocationPrompt() {
    const alertBanner = document.getElementById('alert-banner');
    const alertText = document.getElementById('alert-text');
    
    alertText.innerHTML = `
        <div style="width: 100%;">
            <div style="margin-bottom: 12px;">
                <strong>📍 Set Your Location</strong><br>
                <span style="font-size: 13px;">Enter your city or ZIP code, or use demo location</span>
            </div>
            <div style="display: flex; gap: 8px; flex-wrap: wrap; align-items: center;">
                <input type="text" id="manual-location-input" placeholder="e.g., New York, 10001" 
                       style="flex: 1; min-width: 180px; padding: 10px 12px; border-radius: 8px; border: 1px solid rgba(255,255,255,0.3); background: rgba(0,0,0,0.3); color: white; font-size: 14px;">
                <button onclick="searchManualLocation()" 
                        style="padding: 10px 20px; background: linear-gradient(135deg, #4F46E5, #06B6D4); color: white; border: none; border-radius: 8px; cursor: pointer; font-weight: 600; font-size: 14px;">
                    🔍 Search
                </button>
                <button onclick="useDefaultLocation()" 
                        style="padding: 10px 16px; background: rgba(255,255,255,0.1); color: white; border: 1px solid rgba(255,255,255,0.2); border-radius: 8px; cursor: pointer; font-size: 14px;">
                    🎯 Demo
                </button>
            </div>
        </div>
    `;
    
    alertBanner.style.display = 'flex';
    alertBanner.classList.remove('success', 'error', 'info');
    alertBanner.classList.add('warning');
    
    // Add enter key support
    setTimeout(() => {
        const input = document.getElementById('manual-location-input');
        if (input) {
            input.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    searchManualLocation();
                }
            });
            input.focus();
        }
    }, 100);
}

// Search manual location
async function searchManualLocation() {
    const input = document.getElementById('manual-location-input');
    const query = input?.value.trim();
    
    if (!query) {
        showAlert('Please enter a location', 'warning');
        return;
    }
    
    showAlert('🔍 Searching for location...', 'info');
    
    try {
        const response = await fetch(
            `https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(query)}&format=json&limit=1`
        );
        const data = await response.json();
        
        if (data && data.length > 0) {
            currentLocation.lat = parseFloat(data[0].lat);
            currentLocation.lng = parseFloat(data[0].lon);
            
            console.log('✅ Manual location set:', currentLocation);
            
            updateLocationText(data[0].display_name.split(',')[0]);
            map.setView([currentLocation.lat, currentLocation.lng], 12);
            
            // Add marker
            if (userMarker) {
                map.removeLayer(userMarker);
            }
            
            userMarker = L.marker([currentLocation.lat, currentLocation.lng], {
                icon: L.divIcon({
                    className: 'user-location-marker',
                    html: '<div style="background: #10B981; width: 16px; height: 16px; border-radius: 50%; border: 3px solid white; box-shadow: 0 2px 8px rgba(0,0,0,0.3);"></div>',
                    iconSize: [22, 22]
                })
            }).addTo(map);
            
            // Fetch weather
            fetchWeatherData();
            
            showAlert('✅ Location set successfully!', 'success');
            
            // Close alert after 2 seconds
            setTimeout(() => {
                document.getElementById('alert-banner').style.display = 'none';
            }, 2000);
        } else {
            showAlert('❌ Location not found. Try a different search term.', 'error');
        }
    } catch (error) {
        console.error('Manual location search error:', error);
        showAlert('❌ Search failed. Please try again.', 'error');
    }
}

// Use default demo location
function useDefaultLocation() {
    currentLocation.lat = 42.3314;
    currentLocation.lng = -83.0458;
    
    updateLocationText('Detroit, MI (Demo)');
    map.setView([currentLocation.lat, currentLocation.lng], 12);
    
    if (userMarker) {
        map.removeLayer(userMarker);
    }
    
    userMarker = L.marker([currentLocation.lat, currentLocation.lng], {
        icon: L.divIcon({
            className: 'user-location-marker',
            html: '<div style="background: #F59E0B; width: 16px; height: 16px; border-radius: 50%; border: 3px solid white; box-shadow: 0 2px 8px rgba(0,0,0,0.3);"></div>',
            iconSize: [22, 22]
        })
    }).addTo(map);
    
    fetchWeatherData();
    
    showAlert('✅ Using demo location (Detroit)', 'success');
    
    setTimeout(() => {
        document.getElementById('alert-banner').style.display = 'none';
    }, 2000);
}

// Make functions globally accessible
window.searchManualLocation = searchManualLocation;
window.useDefaultLocation = useDefaultLocation;

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
    // Guard against missing data
    if (!data) {
        console.warn('⚠️ updateWeatherDisplay called without data');
        return;
    }
    
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
    let resultText = data.message || `Risk: ${riskLevel} (${Math.round(confidence)}% confidence)`;
    
    // Add data freshness info if available
    if (data.data_freshness) {
        const freshness = data.data_freshness;
        if (freshness.freshness_penalty > 0.1) {
            resultText += `\n⚠️ Confidence reduced by ${Math.round(freshness.freshness_penalty * 100)}% due to ${freshness.explanation}`;
        }
    }
    
    predictionResult.textContent = resultText;
    
    // Display data freshness indicators (if available)
    if (data.data_freshness && typeof displayDataFreshness === 'function') {
        displayDataFreshness(data.data_freshness);
    }
    
    // Show feedback buttons (if available)
    if (typeof displayFeedbackButtons === 'function') {
        displayFeedbackButtons(data);
    }
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
async function getBIFIPrediction(weatherData, retryCount = 0) {
    const maxRetries = 2;
    
    try {
        const response = await fetch(`${API_BASE}/api/bifi/calculate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ weather_data: weatherData }),
            timeout: 10000 // 10 second timeout
        });
        
        if (!response.ok) {
            const errorText = await response.text().catch(() => 'Unknown error');
            throw new Error(`BIFI HTTP ${response.status}: ${errorText}`);
        }
        
        const data = await response.json();
        if (data.success && data.bifi) {
            // Add interpretation to bifi object
            data.bifi.interpretation = data.interpretation;
            updateBIFIDisplay(data.bifi);
            clearBIFIError();
        } else {
            console.warn('⚠️ BIFI missing data:', Object.keys(data));
            showBIFIFallback('Incomplete data received');
        }
    } catch (error) {
        console.error('❌ BIFI prediction failed:', error);
        
        // Retry logic for network errors
        if (retryCount < maxRetries && (error.name === 'TypeError' || error.message.includes('fetch'))) {
            console.log(`🔄 Retrying BIFI calculation (${retryCount + 1}/${maxRetries})...`);
            await new Promise(resolve => setTimeout(resolve, 1000 * (retryCount + 1))); // Exponential backoff
            return getBIFIPrediction(weatherData, retryCount + 1);
        }
        
        // Show fallback UI after retries exhausted
        showBIFIFallback(error.message);
    }
}

// Show BIFI fallback UI when calculation fails
function showBIFIFallback(errorMessage) {
    const bifiCard = document.querySelector('.bifi-card');
    const scoreEl = document.getElementById('bifi-score');
    const levelEl = document.getElementById('bifi-level');
    const interpretEl = document.getElementById('bifi-interpretation');
    
    if (bifiCard) {
        bifiCard.className = 'card bifi-card bifi-moderate';
    }
    
    // Calculate simple fallback score
    const temp = currentLocation.weather?.temperature || 32;
    const humidity = currentLocation.weather?.humidity || 70;
    
    let score = 0;
    if (temp < 28) score += 40;
    else if (temp < 32) score += 35;
    else if (temp < 35) score += 25;
    else if (temp < 40) score += 15;
    
    if (humidity > 80) score += 30;
    else if (humidity > 70) score += 20;
    else if (humidity > 60) score += 10;
    
    score = Math.min(score, 100);
    
    if (scoreEl) scoreEl.textContent = Math.round(score);
    if (levelEl) {
        const level = score > 60 ? 'HIGH' : score > 40 ? 'MODERATE' : 'LOW';
        levelEl.textContent = level + ' (Est.)';
        levelEl.style.color = score > 60 ? '#FF4500' : score > 40 ? '#FFD700' : '#32CD32';
    }
    if (interpretEl) {
        interpretEl.textContent = '⚠️ Using estimated values - Full calculation unavailable';
    }
    
    console.warn('⚠️ Using fallback BIFI estimation:', errorMessage);
}

// Clear BIFI error state
function clearBIFIError() {
    // Error state cleared - normal display active
}

// Fallback: Get QFPM individually
async function getQFPMPrediction(weatherData, retryCount = 0) {
    const maxRetries = 2;
    
    try {
        // Use standard QFPM endpoint (quick_start.py only has /predict)
        const endpoint = '/api/qfpm/predict';
        
        const requestBody = {
            weather_data: weatherData
        };
        
        // Add location context if available
        if (currentLocation.lat && currentLocation.lng) {
            requestBody.lat = currentLocation.lat;
            requestBody.lon = currentLocation.lng;
            console.log('🛣️ Using QFPM with location context');
        }
        
        const response = await fetch(`${API_BASE}${endpoint}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(requestBody),
            timeout: 10000 // 10 second timeout
        });
        
        if (!response.ok) {
            const errorText = await response.text().catch(() => 'Unknown error');
            
            // Handle 503 specifically - service may not be available yet
            if (response.status === 503) {
                console.warn('⚠️ QFPM service unavailable (503) - using fallback');
                showQFPMFallback('Service temporarily unavailable');
                return; // Don't throw error, just use fallback
            }
            
            throw new Error(`QFPM HTTP ${response.status}: ${errorText}`);
        }
        
        const data = await response.json();
        console.log('⚛️ QFPM response received:', data);
        
        // Log if using real RWIS data
        if (data.data_sources && data.data_sources.rwis_available) {
            console.log('✅ Using REAL road surface temp from RWIS sensor!');
            if (data.rwis_sensor) {
                console.log(`📍 Sensor: ${data.rwis_sensor.name} (${data.rwis_sensor.distance_miles.toFixed(1)} mi away)`);
                console.log(`🌡️ Road temp: ${data.rwis_sensor.road_temp}°F`);
            }
        }
        
        // Log precipitation data
        if (data.precipitation) {
            console.log(`🌧️ Precipitation: ${data.precipitation.type} - Risk: ${data.precipitation.black_ice_risk}`);
        }
        
        if (data.success && data.summary) {
            updateQFPMDisplay({ summary: data.summary, data_sources: data.data_sources, rwis_sensor: data.rwis_sensor, precipitation: data.precipitation });
            // Clear any previous error messages
            clearQFPMError();
        } else {
            console.warn('⚠️ QFPM missing summary:', Object.keys(data));
            showQFPMFallback('Incomplete data received');
        }
    } catch (error) {
        console.error('❌ QFPM error:', error.message);
        
        // Retry logic for network errors (not for 503)
        if (retryCount < maxRetries && (error.name === 'TypeError' || error.message.includes('fetch'))) {
            console.log(`🔄 Retrying QFPM prediction (${retryCount + 1}/${maxRetries})...`);
            await new Promise(resolve => setTimeout(resolve, 1000 * (retryCount + 1))); // Exponential backoff
            return getQFPMPrediction(weatherData, retryCount + 1);
        }
        
        // Show fallback UI after retries exhausted
        showQFPMFallback(error.message);
    }
}

// Show QFPM fallback UI when prediction fails
function showQFPMFallback(errorMessage) {
    const qfpmAlert = document.getElementById('qfpm-alert');
    if (qfpmAlert) {
        qfpmAlert.textContent = `⚠️ QFPM unavailable - Using basic forecast`;
        qfpmAlert.style.borderColor = '#FFA500';
        qfpmAlert.style.backgroundColor = 'rgba(255, 165, 0, 0.1)';
    }
    
    // Show simplified forecast based on current conditions
    const temp = currentLocation.weather?.temperature || 32;
    const humidity = currentLocation.weather?.humidity || 70;
    
    // Basic risk estimation
    let riskProb = 0;
    if (temp < 32) riskProb = 70;
    else if (temp < 35) riskProb = 50;
    else if (temp < 40) riskProb = 30;
    else riskProb = 10;
    
    // Adjust for humidity
    if (humidity > 80) riskProb += 15;
    else if (humidity > 70) riskProb += 10;
    
    riskProb = Math.min(riskProb, 95);
    
    // Update with fallback values
    updateForecastItem('30', riskProb);
    updateForecastItem('60', riskProb + 5);
    updateForecastItem('90', riskProb + 10);
    
    console.warn('⚠️ Using fallback QFPM estimation:', errorMessage);
}

// Clear QFPM error state
function clearQFPMError() {
    const qfpmAlert = document.getElementById('qfpm-alert');
    if (qfpmAlert) {
        qfpmAlert.style.backgroundColor = '';
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
    if (!qfpmData || !qfpmData.summary) {
        console.warn('⚠️ QFPM display called with missing data:', qfpmData);
        return;
    }
    
    const summary = qfpmData.summary;
    const probs = summary.freeze_probability;
    
    if (!probs) {
        console.warn('⚠️ QFPM summary missing freeze_probability:', summary);
        return;
    }
    
    // Update 30-min forecast
    updateForecastItem('30', probs['30_min']);
    updateForecastItem('60', probs['60_min']);
    updateForecastItem('90', probs['90_min']);
    
    // Update alert message
    document.getElementById('qfpm-alert').textContent = summary.alert_message || '⚛️ Quantum prediction ready';
    document.getElementById('qfpm-alert').style.borderColor = summary.color || '#667eea';
    
    // Highlight peak risk time
    const peakTime = summary.peak_risk_time;
    document.querySelectorAll('.forecast-item').forEach(item => {
        item.style.borderLeftColor = 'transparent';
    });
    const peakEl = document.getElementById(`forecast-${peakTime}`);
    if (peakEl) {
        peakEl.style.borderLeftColor = summary.color || '#667eea';
    }
    
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

        if (!response.ok) {
            throw new Error(`Road temp HTTP ${response.status}`);
        }

        const data = await response.json();
        console.log('🌡️ RWIS response received:', data);
        
        // Backend returns road_temp_data; older frontend expected road_temp. Support both.
        const roadTempPayload = data.road_temp || data.road_temp_data;
        if (data.success && roadTempPayload) {
            updateRoadTempDisplay(roadTempPayload);
        } else {
            console.warn('⚠️ Road temp payload missing expected key:', Object.keys(data));
        }
    } catch (error) {
        console.error('❌ Road temp error:', error);
    }
}

// Precipitation Type
async function getPrecipitationType() {
    try {
        // Fetch current precip type
        const typeRes = await fetch(
            `${API_BASE}/api/precipitation/type?lat=${currentLocation.lat}&lon=${currentLocation.lng}`
        );
        if (!typeRes.ok) throw new Error(`Precip Type HTTP ${typeRes.status}`);
        const typeData = await typeRes.json();
        console.log('🌨️ Precipitation type response received:', typeData);
        
        const precipPayload = typeData.precipitation_type || typeData.precipitation;

        // Also fetch next hours forecast for the timeline UI
        let hourly = [];
        try {
            const fcRes = await fetch(
                `${API_BASE}/api/precipitation/forecast?lat=${currentLocation.lat}&lon=${currentLocation.lng}&hours=3`
            );
            if (fcRes.ok) {
                const fc = await fcRes.json();
                hourly = Array.isArray(fc.hourly_forecast) ? fc.hourly_forecast : [];
            }
        } catch (e) {
            console.warn('⚠️ Precipitation hourly forecast unavailable:', e.message);
        }

        if (typeData.success && precipPayload) {
            // Normalize shape to include an array for forecast_next_hour that UI expects
            const normalized = {
                ...precipPayload,
                forecast_next_hour: hourly.map(h => ({
                    time: h.time,
                    type: h.precipitation_type
                }))
            };
            updatePrecipTypeDisplay(normalized);
        } else {
            console.warn('⚠️ Precipitation type payload missing expected key:', Object.keys(typeData));
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
    if (!roadTempData) {
        console.warn('⚠️ Road temp display called with null data');
        return;
    }
    
    const tempValueEl = document.getElementById('road-temp-value');
    const distanceEl = document.getElementById('sensor-distance');
    const confidenceEl = document.getElementById('sensor-confidence');
    const airTempEl = document.getElementById('air-temp-compare');
    const diffEl = document.getElementById('temp-difference');
    const messageEl = document.getElementById('road-temp-message');
    
    if (roadTempData.road_temp_f !== null && roadTempData.road_temp_f !== undefined) {
        tempValueEl.textContent = `${roadTempData.road_temp_f.toFixed(0)}°F`;
        
        if (roadTempData.road_temp_f <= 32) {
            tempValueEl.style.color = '#dc2626';
        } else if (roadTempData.road_temp_f <= 35) {
            tempValueEl.style.color = '#f59e0b';
        } else {
            tempValueEl.style.color = '#10b981';
        }
        
        distanceEl.textContent = `${roadTempData.distance_miles.toFixed(1)} mi away`;
        
        const confidence = (roadTempData.confidence || 'low').toUpperCase();
        confidenceEl.textContent = confidence;
        
        if (confidence === 'HIGH') {
            confidenceEl.style.background = '#10b981';
        } else if (confidence === 'MEDIUM') {
            confidenceEl.style.background = '#f59e0b';
        } else {
            confidenceEl.style.background = '#dc2626';
        }
        
        if (roadTempData.air_temp_f !== null && roadTempData.air_temp_f !== undefined) {
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
        messageEl.textContent = roadTempData.message || '⚠️ No RWIS sensors within 25 miles - using air temperature';
        messageEl.style.color = '#f59e0b';
    }
    
    console.log('🌡️ Road temp updated:', roadTempData.road_temp_f);
}

function updatePrecipTypeDisplay(precipTypeData) {
    if (!precipTypeData) {
        console.warn('⚠️ Precipitation display called with null data');
        return;
    }
    
    const iconEl = document.getElementById('precip-icon');
    const typeEl = document.getElementById('precip-type');
    const riskBadgeEl = document.getElementById('precip-risk-badge');
    const riskLevelEl = document.getElementById('precip-risk-level');
    const hourlyEl = document.getElementById('precip-hourly');
    const warningEl = document.getElementById('precip-warning');
    
    const precipType = precipTypeData.current_type || 'unknown';
    
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
    const riskLevel = (precipTypeData.black_ice_risk || 'low').toUpperCase();
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
    if (Array.isArray(precipTypeData.forecast_next_hour) && precipTypeData.forecast_next_hour.length > 0) {
        const hourlyHTML = precipTypeData.forecast_next_hour.slice(0, 3).map(hour => {
            const time = hour.time ? new Date(hour.time).getHours() : '--';
            const ampm = time >= 12 ? 'PM' : 'AM';
            const displayTime = (time % 12 || 12) + ampm;
            
            return `
                <div class="hour-item">
                    <div class="hour-time">${displayTime}</div>
                    <div class="hour-type">${icons[hour.type] || '❓'} ${(hour.type || 'unknown').replace('_', ' ')}</div>
                </div>
            `;
        }).join('');
        
        hourlyEl.innerHTML = hourlyHTML;
    } else {
        hourlyEl.innerHTML = '<div class="hour-item"><div class="hour-time">N/A</div><div class="hour-type">No forecast available</div></div>';
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

// ============================================================================
// NEW DATA VISUALIZATIONS
// ============================================================================

// 24-Hour Risk Forecast Chart
let riskForecastChart = null;
let historicalData = [];

async function fetch24HourRiskForecast() {
    console.log('📊 Fetching 24-hour forecast...');
    
    if (!currentLocation.lat || !currentLocation.lng) {
        console.warn('⚠️ No location available for forecast');
        showAlert('⚠️ Please enable location to view forecast', 'warning');
        return;
    }
    
    showAlert('📊 Loading 24-hour forecast...', 'info');
    
    try {
        const url = `${API_BASE}/api/forecast/24hour?lat=${currentLocation.lat}&lon=${currentLocation.lng}`;
        console.log('🔗 Fetching:', url);
        
        const response = await fetch(url);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        console.log('📊 Forecast response:', data);
        
        if (data.success && data.hourly_forecast && data.hourly_forecast.length > 0) {
            display24HourChart(data.hourly_forecast);
            cacheData('forecast_24h', data, 30 * 60 * 1000); // Cache for 30 minutes
            showAlert('✅ 24-hour forecast loaded!', 'success');
        } else {
            throw new Error(data.error || 'No forecast data available');
        }
    } catch (error) {
        console.error('❌ 24-hour forecast error:', error);
        showAlert(`❌ Unable to load forecast: ${error.message}`, 'error');
    }
}

function display24HourChart(hourlyData, container) {
    // Create or update the chart card
    let chartCard = document.getElementById('forecast-chart-card');
    
    if (!chartCard) {
        const targetContainer = container || document.querySelector('.main-content');
        chartCard = document.createElement('div');
        chartCard.id = 'forecast-chart-card';
        chartCard.className = 'card forecast-chart-card';
        chartCard.innerHTML = `
            <h2 class="card-title">📊 24-Hour Risk Forecast</h2>
            <canvas id="risk-forecast-canvas"></canvas>
            <div class="chart-legend">
                <div class="legend-item"><span class="legend-dot high"></span> High Risk (>60%)</div>
                <div class="legend-item"><span class="legend-dot medium"></span> Medium Risk (30-60%)</div>
                <div class="legend-item"><span class="legend-dot low"></span> Low Risk (<30%)</div>
            </div>
        `;
        
        if (container) {
            container.appendChild(chartCard);
        } else {
            targetContainer.insertBefore(chartCard, targetContainer.firstChild);
        }
    }
    
    // Simple canvas drawing (lightweight alternative to Chart.js)
    const canvas = document.getElementById('risk-forecast-canvas');
    const ctx = canvas.getContext('2d');
    
    // Set canvas size
    canvas.width = canvas.offsetWidth || 300;
    canvas.height = 200;
    
    const width = canvas.width;
    const height = canvas.height;
    const padding = 40;
    
    // Clear canvas
    ctx.clearRect(0, 0, width, height);
    
    // Draw grid
    ctx.strokeStyle = 'rgba(255,255,255,0.1)';
    ctx.lineWidth = 1;
    
    for (let i = 0; i <= 4; i++) {
        const y = padding + (height - 2 * padding) * i / 4;
        ctx.beginPath();
        ctx.moveTo(padding, y);
        ctx.lineTo(width - padding, y);
        ctx.stroke();
        
        // Y-axis labels
        ctx.fillStyle = 'rgba(255,255,255,0.6)';
        ctx.font = '10px Inter';
        ctx.fillText(`${100 - i * 25}%`, 5, y + 3);
    }
    
    // Draw risk line
    ctx.strokeStyle = '#667eea';
    ctx.lineWidth = 3;
    ctx.beginPath();
    
    const dataPoints = hourlyData.slice(0, 24);
    const xStep = (width - 2 * padding) / (dataPoints.length - 1);
    
    dataPoints.forEach((point, index) => {
        const x = padding + index * xStep;
        const riskValue = point.black_ice_probability || point.risk || 0;
        const y = height - padding - (riskValue / 100) * (height - 2 * padding);
        
        if (index === 0) {
            ctx.moveTo(x, y);
        } else {
            ctx.lineTo(x, y);
        }
        
        // Draw point
        ctx.fillStyle = getRiskColor(riskValue);
        ctx.fillRect(x - 3, y - 3, 6, 6);
    });
    
    ctx.stroke();
    
    // X-axis time labels (every 4 hours)
    ctx.fillStyle = 'rgba(255,255,255,0.6)';
    ctx.font = '10px Inter';
    
    for (let i = 0; i < dataPoints.length; i += 4) {
        const x = padding + i * xStep;
        try {
            const time = new Date(dataPoints[i].time);
            const timeStr = isNaN(time.getTime()) ? `${i}h` : `${time.getHours()}:00`;
            ctx.fillText(timeStr, x - 15, height - 10);
        } catch (e) {
            console.warn('⚠️ Invalid time format:', dataPoints[i].time);
            ctx.fillText(`${i}h`, x - 15, height - 10);
        }
    }
    
    console.log('📊 24-hour forecast chart rendered');
}

function getRiskColor(risk) {
    if (risk > 60) return '#EF4444';
    if (risk > 30) return '#F59E0B';
    return '#10B981';
}

// Heatmap Layers (Temperature, Precipitation, Wind)
async function toggleHeatmapLayer(type) {
    console.log(`🗺️ Toggling ${type} heatmap`);
    
    const existingLayer = window[`${type}HeatmapLayer`];
    
    if (existingLayer) {
        map.removeLayer(existingLayer);
        window[`${type}HeatmapLayer`] = null;
        showAlert(`${type} heatmap hidden`, 'info');
        return;
    }
    
    if (!currentLocation.lat || !currentLocation.lng) {
        showAlert('⚠️ Please enable location to view heatmaps', 'warning');
        return;
    }
    
    showAlert(`Loading ${type} heatmap...`, 'info');
    
    try {
        const url = `${API_BASE}/api/heatmap/${type}?lat=${currentLocation.lat}&lon=${currentLocation.lng}&radius=50000`;
        console.log('🔗 Fetching heatmap:', url);
        
        const response = await fetch(url);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        console.log(`🗺️ ${type} heatmap response:`, data);
        
        if (data.success && data.heatmap_data && data.heatmap_data.length > 0) {
            displayHeatmap(type, data.heatmap_data);
            showAlert(`✅ ${type} heatmap loaded!`, 'success');
        } else {
            throw new Error(data.error || 'No heatmap data available');
        }
    } catch (error) {
        console.error(`❌ ${type} heatmap error:`, error);
        showAlert(`❌ ${type} heatmap unavailable: ${error.message}`, 'warning');
    }
}

function displayHeatmap(type, heatmapData) {
    // Create canvas overlay for heatmap
    const bounds = map.getBounds();
    const canvas = document.createElement('canvas');
    canvas.width = 512;
    canvas.height = 512;
    
    const ctx = canvas.getContext('2d');
    const imageData = ctx.createImageData(512, 512);
    
    // Color gradients based on type
    const gradients = {
        temperature: [[0, 0, 255], [0, 255, 0], [255, 255, 0], [255, 0, 0]],
        precipitation: [[255, 255, 255], [0, 150, 255], [0, 50, 200]],
        wind: [[200, 200, 200], [255, 200, 0], [255, 100, 0], [200, 0, 0]]
    };
    
    // Fill canvas with heatmap data
    heatmapData.forEach(point => {
        const x = Math.floor((point.lon - bounds.getWest()) / (bounds.getEast() - bounds.getWest()) * 512);
        const y = Math.floor((bounds.getNorth() - point.lat) / (bounds.getNorth() - bounds.getSouth()) * 512);
        
        if (x >= 0 && x < 512 && y >= 0 && y < 512) {
            const intensity = point.value;
            const color = interpolateColor(gradients[type], intensity);
            const index = (y * 512 + x) * 4;
            
            imageData.data[index] = color[0];
            imageData.data[index + 1] = color[1];
            imageData.data[index + 2] = color[2];
            imageData.data[index + 3] = 150; // Alpha
        }
    });
    
    ctx.putImageData(imageData, 0, 0);
    
    // Add as map overlay
    const imageUrl = canvas.toDataURL();
    const overlay = L.imageOverlay(imageUrl, bounds, { opacity: 0.5 }).addTo(map);
    window[`${type}HeatmapLayer`] = overlay;
    
    console.log(`🗺️ ${type} heatmap displayed`);
}

function interpolateColor(gradient, value) {
    const index = value * (gradient.length - 1);
    const lower = Math.floor(index);
    const upper = Math.ceil(index);
    const t = index - lower;
    
    const c1 = gradient[lower] || gradient[0];
    const c2 = gradient[upper] || gradient[gradient.length - 1];
    
    return [
        Math.round(c1[0] + (c2[0] - c1[0]) * t),
        Math.round(c1[1] + (c2[1] - c1[1]) * t),
        Math.round(c1[2] + (c2[2] - c1[2]) * t)
    ];
}

// Time-lapse Replay Visualization
let timelapseInterval = null;
let timelapseData = [];
let timelapseIndex = 0;

async function startTimelapse() {
    console.log('⏱️ Starting time-lapse');
    
    if (timelapseInterval) {
        stopTimelapse();
        return;
    }
    
    if (!currentLocation.lat || !currentLocation.lng) {
        showAlert('⚠️ Please enable location to view time-lapse', 'warning');
        return;
    }
    
    showAlert('⏱️ Loading 6-hour history...', 'info');
    
    // Fetch last 6 hours of data
    try {
        const response = await fetch(
            `${API_BASE}/api/historical/6hours?lat=${currentLocation.lat}&lon=${currentLocation.lng}`
        );
        const data = await response.json();
        
        if (data.success) {
            timelapseData = data.hourly_data;
            timelapseIndex = 0;
            
            showAlert('▶️ Time-lapse started (last 6 hours)', 'info');
            
            timelapseInterval = setInterval(() => {
                if (timelapseIndex >= timelapseData.length) {
                    stopTimelapse();
                    return;
                }
                
                const frame = timelapseData[timelapseIndex];
                displayTimelapseFrame(frame);
                timelapseIndex++;
            }, 500); // 0.5 seconds per hour
        }
    } catch (error) {
        console.error('❌ Timelapse error:', error);
        showAlert('Time-lapse unavailable', 'error');
    }
}

function stopTimelapse() {
    if (timelapseInterval) {
        clearInterval(timelapseInterval);
        timelapseInterval = null;
        showAlert('⏹️ Time-lapse stopped', 'info');
    }
}

function displayTimelapseFrame(frame) {
    // Update display with historical frame
    document.getElementById('temp-text').textContent = `${frame.temperature}°F`;
    document.getElementById('humidity-text').textContent = `${frame.humidity}%`;
    document.getElementById('wind-text').textContent = `${frame.wind_speed} mph`;
    
    // Show timestamp overlay
    let timeOverlay = document.getElementById('timelapse-overlay');
    if (!timeOverlay) {
        timeOverlay = document.createElement('div');
        timeOverlay.id = 'timelapse-overlay';
        timeOverlay.style.cssText = 'position:fixed;top:100px;right:20px;background:rgba(0,0,0,0.8);color:white;padding:10px 20px;border-radius:8px;font-weight:600;z-index:10000;';
        document.body.appendChild(timeOverlay);
    }
    
    const time = new Date(frame.timestamp);
    timeOverlay.textContent = `⏱️ ${time.toLocaleTimeString()}`;
}

// Comparison Mode (Today vs Yesterday)
let comparisonMode = false;
let todayData = null;
let yesterdayData = null;

async function toggleComparisonMode() {
    console.log('🔄 Toggling comparison mode');
    comparisonMode = !comparisonMode;
    
    if (comparisonMode) {
        if (!currentLocation.lat || !currentLocation.lng) {
            showAlert('⚠️ Please enable location to compare data', 'warning');
            comparisonMode = false;
            return;
        }
        showAlert('📊 Loading comparison data...', 'info');
        await fetchComparisonData();
        displayComparison();
        showAlert('✅ Comparison mode enabled', 'success');
    } else {
        hideComparison();
        showAlert('📊 Comparison mode disabled', 'info');
    }
}

async function fetchComparisonData() {
    if (!currentLocation.lat || !currentLocation.lng) return;
    
    try {
        // Fetch today's data
        const todayResponse = await fetch(
            `${API_BASE}/api/weather/current?lat=${currentLocation.lat}&lon=${currentLocation.lng}`
        );
        todayData = await todayResponse.json();
        
        // Fetch yesterday's data at same time
        const yesterdayResponse = await fetch(
            `${API_BASE}/api/historical/yesterday?lat=${currentLocation.lat}&lon=${currentLocation.lng}`
        );
        yesterdayData = await yesterdayResponse.json();
    } catch (error) {
        console.error('❌ Comparison data error:', error);
    }
}

function displayComparison(container) {
    let compareCard = document.getElementById('comparison-card');
    
    if (!compareCard) {
        const targetContainer = container || document.querySelector('.main-content');
        compareCard = document.createElement('div');
        compareCard.id = 'comparison-card';
        compareCard.className = 'card comparison-card';
        
        if (container) {
            container.appendChild(compareCard);
        } else {
            targetContainer.insertBefore(compareCard, targetContainer.children[1]);
        }
    }
    
    const tempDiff = todayData.temperature - yesterdayData.temperature;
    const riskDiff = (todayData.black_ice_risk || 0) - (yesterdayData.black_ice_risk || 0);
    
    compareCard.innerHTML = `
        <h2 class="card-title">🔄 Today vs Yesterday</h2>
        <div class="comparison-grid">
            <div class="comparison-item">
                <div class="compare-label">Temperature</div>
                <div class="compare-today">${todayData.temperature}°F</div>
                <div class="compare-diff ${tempDiff > 0 ? 'higher' : 'lower'}">
                    ${tempDiff > 0 ? '↑' : '↓'} ${Math.abs(tempDiff).toFixed(1)}°F
                </div>
                <div class="compare-yesterday">${yesterdayData.temperature}°F yesterday</div>
            </div>
            <div class="comparison-item">
                <div class="compare-label">Black Ice Risk</div>
                <div class="compare-today">${todayData.black_ice_risk || 0}%</div>
                <div class="compare-diff ${riskDiff > 0 ? 'worse' : 'better'}">
                    ${riskDiff > 0 ? '↑' : '↓'} ${Math.abs(riskDiff).toFixed(0)}%
                </div>
                <div class="compare-yesterday">${yesterdayData.black_ice_risk || 0}% yesterday</div>
            </div>
            <div class="comparison-item">
                <div class="compare-label">Humidity</div>
                <div class="compare-today">${todayData.humidity}%</div>
                <div class="compare-yesterday">${yesterdayData.humidity}% yesterday</div>
            </div>
        </div>
    `;
    
    console.log('📊 Comparison display updated');
}

function hideComparison() {
    const compareCard = document.getElementById('comparison-card');
    if (compareCard) {
        compareCard.remove();
    }
}

// ============================================================================
// PERFORMANCE OPTIMIZATIONS
// ============================================================================

// Smart Caching System
const dataCache = new Map();

function cacheData(key, data, ttl = 5 * 60 * 1000) {
    dataCache.set(key, {
        data: data,
        timestamp: Date.now(),
        ttl: ttl
    });
}

function getCachedData(key) {
    const cached = dataCache.get(key);
    
    if (!cached) return null;
    
    const age = Date.now() - cached.timestamp;
    
    if (age > cached.ttl) {
        dataCache.delete(key);
        return null;
    }
    
    console.log(`💾 Using cached ${key} (${(age / 1000).toFixed(0)}s old)`);
    return cached.data;
}

// Battery-Aware Update System
let batteryLevel = 1.0;
let isCharging = true;

async function initBatteryMonitoring() {
    if ('getBattery' in navigator) {
        try {
            const battery = await navigator.getBattery();
            
            batteryLevel = battery.level;
            isCharging = battery.charging;
            
            battery.addEventListener('levelchange', () => {
                batteryLevel = battery.level;
                adjustUpdateFrequency();
            });
            
            battery.addEventListener('chargingchange', () => {
                isCharging = battery.charging;
                adjustUpdateFrequency();
            });
            
            console.log(`🔋 Battery: ${(batteryLevel * 100).toFixed(0)}% (${isCharging ? 'charging' : 'discharging'})`);
        } catch (error) {
            console.log('⚠️ Battery API not available');
        }
    }
}

function adjustUpdateFrequency() {
    if (batteryLevel < 0.2 && !isCharging) {
        // Low battery - reduce updates
        currentSettings.refreshInterval = 300; // 5 minutes
        console.log('🔋 Low battery: Reduced update frequency to 5 min');
        showAlert('⚡ Battery saver mode active', 'info');
    } else if (batteryLevel < 0.5 && !isCharging) {
        // Medium battery - moderate updates
        currentSettings.refreshInterval = 120; // 2 minutes
        console.log('🔋 Medium battery: Update frequency 2 min');
    } else {
        // Good battery or charging - normal updates
        currentSettings.refreshInterval = 60; // 1 minute
    }
    
    applySettings();
}

// Lazy Loading for Map Layers
const layerLoadQueue = [];
let isLoadingLayers = false;

function queueLayerLoad(layerType, loadFunction) {
    layerLoadQueue.push({ type: layerType, load: loadFunction });
    
    if (!isLoadingLayers) {
        processLayerQueue();
    }
}

async function processLayerQueue() {
    if (layerLoadQueue.length === 0) {
        isLoadingLayers = false;
        return;
    }
    
    isLoadingLayers = true;
    const layer = layerLoadQueue.shift();
    
    console.log(`🗺️ Loading layer: ${layer.type}`);
    
    try {
        await layer.load();
    } catch (error) {
        console.error(`❌ Failed to load ${layer.type}:`, error);
    }
    
    // Wait a bit before loading next layer
    setTimeout(processLayerQueue, 500);
}

// Image Compression for User Uploads (future feature)
function compressImage(file, maxWidth = 800, quality = 0.8) {
    return new Promise((resolve) => {
        const reader = new FileReader();
        
        reader.onload = (e) => {
            const img = new Image();
            
            img.onload = () => {
                const canvas = document.createElement('canvas');
                let width = img.width;
                let height = img.height;
                
                if (width > maxWidth) {
                    height *= maxWidth / width;
                    width = maxWidth;
                }
                
                canvas.width = width;
                canvas.height = height;
                
                const ctx = canvas.getContext('2d');
                ctx.drawImage(img, 0, 0, width, height);
                
                canvas.toBlob((blob) => {
                    resolve(new File([blob], file.name, {
                        type: 'image/jpeg',
                        lastModified: Date.now()
                    }));
                }, 'image/jpeg', quality);
            };
            
            img.src = e.target.result;
        };
        
        reader.readAsDataURL(file);
    });
}

// Background Location Updates
let backgroundLocationWatcher = null;

function startBackgroundLocationTracking() {
    if (!navigator.geolocation) return;
    
    backgroundLocationWatcher = navigator.geolocation.watchPosition(
        (position) => {
            const newLat = position.coords.latitude;
            const newLng = position.coords.longitude;
            
            // Only update if moved significantly (>100m)
            const distance = calculateDistance(
                currentLocation.lat, currentLocation.lng,
                newLat, newLng
            );
            
            if (distance > 0.1) { // 100m
                currentLocation.lat = newLat;
                currentLocation.lng = newLng;
                
                console.log(`📍 Location updated: moved ${(distance * 1000).toFixed(0)}m`);
                
                // Update map
                map.setView([newLat, newLng]);
                
                if (userMarker) {
                    userMarker.setLatLng([newLat, newLng]);
                }
                
                // Fetch new data for location
                fetchWeatherData();
            }
        },
        (error) => {
            console.error('Background location error:', error);
        },
        {
            enableHighAccuracy: false, // Save battery
            timeout: 30000,
            maximumAge: 300000 // 5 minutes
        }
    );
}

function calculateDistance(lat1, lon1, lat2, lon2) {
    const R = 6371; // Earth's radius in km
    const dLat = (lat2 - lat1) * Math.PI / 180;
    const dLon = (lon2 - lon1) * Math.PI / 180;
    
    const a = Math.sin(dLat/2) * Math.sin(dLat/2) +
              Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
              Math.sin(dLon/2) * Math.sin(dLon/2);
    
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
    
    return R * c; // Distance in km
}

// Progressive Web App Caching
async function precacheAssets() {
    if ('caches' in window) {
        try {
            const cache = await caches.open('black-ice-v1');
            
            const assets = [
                '/mobile.html',
                '/mobile.js',
                '/mobile-styles.css',
                '/icons/icon-192.png',
                '/icons/icon-512.png'
            ];
            
            await cache.addAll(assets);
            console.log('✅ Assets pre-cached');
        } catch (error) {
            console.error('❌ Pre-cache failed:', error);
        }
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
    
    // Visualization Controls
    const btnForecastChart = document.getElementById('btn-forecast-chart');
    const btnComparison = document.getElementById('btn-comparison');
    const btnTimelapse = document.getElementById('btn-timelapse');
    const btnTempHeatmap = document.getElementById('btn-temp-heatmap');
    const btnPrecipHeatmap = document.getElementById('btn-precip-heatmap');
    const btnWindHeatmap = document.getElementById('btn-wind-heatmap');
    
    console.log('🎨 Visualization buttons found:', {
        chart: !!btnForecastChart,
        comparison: !!btnComparison,
        timelapse: !!btnTimelapse,
        tempHeatmap: !!btnTempHeatmap,
        precipHeatmap: !!btnPrecipHeatmap,
        windHeatmap: !!btnWindHeatmap
    });
    
    if (btnForecastChart) {
        btnForecastChart.addEventListener('click', () => {
            console.log('📈 Forecast chart button clicked');
            const chart = document.getElementById('forecast-chart-card');
            if (chart) {
                chart.remove();
                btnForecastChart.classList.remove('active');
                showAlert('📊 Forecast chart hidden', 'info');
            } else {
                fetch24HourRiskForecast();
                btnForecastChart.classList.add('active');
            }
        });
    } else {
        console.warn('❌ Forecast chart button not found');
    }
    
    if (btnComparison) {
        btnComparison.addEventListener('click', () => {
            console.log('🔄 Comparison button clicked');
            toggleComparisonMode();
            btnComparison.classList.toggle('active');
        });
    } else {
        console.warn('❌ Comparison button not found');
    }
    
    if (btnTimelapse) {
        btnTimelapse.addEventListener('click', () => {
            console.log('⏱️ Timelapse button clicked');
            if (timelapseInterval) {
                stopTimelapse();
                btnTimelapse.classList.remove('active');
            } else {
                startTimelapse();
                btnTimelapse.classList.add('active');
            }
        });
    } else {
        console.warn('❌ Timelapse button not found');
    }
    
    if (btnTempHeatmap) {
        btnTempHeatmap.addEventListener('click', () => {
            console.log('🌡️ Temperature heatmap button clicked');
            toggleHeatmapLayer('temperature');
            btnTempHeatmap.classList.toggle('active');
        });
    } else {
        console.warn('❌ Temp heatmap button not found');
    }
    
    if (btnPrecipHeatmap) {
        btnPrecipHeatmap.addEventListener('click', () => {
            console.log('💧 Precipitation heatmap button clicked');
            toggleHeatmapLayer('precipitation');
            btnPrecipHeatmap.classList.toggle('active');
        });
    } else {
        console.warn('❌ Precip heatmap button not found');
    }
    
    if (btnWindHeatmap) {
        btnWindHeatmap.addEventListener('click', () => {
            console.log('💨 Wind heatmap button clicked');
            toggleHeatmapLayer('wind');
            btnWindHeatmap.classList.toggle('active');
        });
    } else {
        console.warn('❌ Wind heatmap button not found');
    }
    
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
                // Fetch fresh weather data instead of updating without data
                fetchWeatherData();
            }, currentSettings.refreshInterval * 1000);
        }
        
        // Apply map style immediately
        applyMapStyle(currentSettings.mapStyle);
        
        // Apply traffic layer setting
        if (currentSettings.showTraffic && !trafficLayer) {
            fetchTrafficLayer();
        } else if (!currentSettings.showTraffic && trafficLayer) {
            map.removeLayer(trafficLayer);
            trafficLayer = null;
        }
        
        // Apply bridge hazards setting
        if (currentSettings.showBridges && currentLocation.lat) {
            document.getElementById('road-risk-layer').checked = true;
            fetchRoadRisks();
        } else if (!currentSettings.showBridges) {
            clearRoadRiskMarkers();
        }
        
        // Update displayed temperatures if currently showing
        convertTemperaturesInUI();
    }
    
    // Apply map style function
    function applyMapStyle(style) {
        // Remove existing tile layers except user marker
        map.eachLayer((layer) => {
            if (layer instanceof L.TileLayer) {
                map.removeLayer(layer);
            }
        });
        
        // Add new tile layer based on style
        let tileUrl, options;
        
        switch(style) {
            case 'satellite':
                tileUrl = 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}';
                options = { attribution: 'Esri, Maxar, Earthstar Geographics' };
                break;
            case 'dark':
                tileUrl = 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png';
                options = { attribution: 'CartoDB' };
                break;
            case 'street':
            default:
                tileUrl = 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png';
                options = { attribution: 'OpenStreetMap' };
                break;
        }
        
        L.tileLayer(tileUrl, options).addTo(map);
        
        // Re-add user marker if it exists
        if (userMarker) {
            userMarker.addTo(map);
        }
        
        console.log('✅ Map style changed to:', style);
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
    
    // Viz tab buttons
    const vizToggleForecast = document.getElementById('viz-toggle-forecast');
    const vizToggleComparison = document.getElementById('viz-toggle-comparison');
    const vizToggleTimelapse = document.getElementById('viz-toggle-timelapse');
    const vizToggleTemp = document.getElementById('viz-toggle-temp');
    const vizTogglePrecip = document.getElementById('viz-toggle-precip');
    const vizToggleWind = document.getElementById('viz-toggle-wind');
    
    if (vizToggleForecast) {
        vizToggleForecast.addEventListener('click', () => {
            const content = document.getElementById('viz-content-forecast');
            const isVisible = content.style.display !== 'none';
            
            if (isVisible) {
                content.style.display = 'none';
                vizToggleForecast.classList.remove('active');
                // Remove chart if it exists
                const chart = document.getElementById('forecast-chart-card');
                if (chart) chart.remove();
            } else {
                content.style.display = 'block';
                vizToggleForecast.classList.add('active');
                // Create chart in this container
                fetch24HourRiskForecast(content);
            }
        });
    }
    
    if (vizToggleComparison) {
        vizToggleComparison.addEventListener('click', () => {
            const content = document.getElementById('viz-content-comparison');
            const isVisible = content.style.display !== 'none';
            
            if (isVisible) {
                content.style.display = 'none';
                vizToggleComparison.classList.remove('active');
                comparisonMode = false;
                hideComparison();
            } else {
                content.style.display = 'block';
                vizToggleComparison.classList.add('active');
                comparisonMode = true;
                fetchComparisonData().then(() => displayComparison(content));
            }
        });
    }
    
    if (vizToggleTimelapse) {
        const startBtn = document.getElementById('timelapse-start');
        const stopBtn = document.getElementById('timelapse-stop');
        
        vizToggleTimelapse.addEventListener('click', () => {
            const content = document.getElementById('viz-content-timelapse');
            const isVisible = content.style.display !== 'none';
            
            if (isVisible) {
                content.style.display = 'none';
                vizToggleTimelapse.classList.remove('active');
                stopTimelapse();
            } else {
                content.style.display = 'block';
                vizToggleTimelapse.classList.add('active');
            }
        });
        
        if (startBtn) {
            startBtn.addEventListener('click', () => {
                startTimelapse();
                startBtn.style.display = 'none';
                stopBtn.style.display = 'inline-block';
            });
        }
        
        if (stopBtn) {
            stopBtn.addEventListener('click', () => {
                stopTimelapse();
                stopBtn.style.display = 'none';
                startBtn.style.display = 'inline-block';
            });
        }
    }
    
    if (vizToggleTemp) {
        vizToggleTemp.addEventListener('click', () => {
            toggleHeatmapLayer('temperature');
            vizToggleTemp.classList.toggle('active');
            showAlert('Switch to Map tab to see temperature heatmap', 'info');
        });
    }
    
    if (vizTogglePrecip) {
        vizTogglePrecip.addEventListener('click', () => {
            toggleHeatmapLayer('precipitation');
            vizTogglePrecip.classList.toggle('active');
            showAlert('Switch to Map tab to see precipitation heatmap', 'info');
        });
    }
    
    if (vizToggleWind) {
        vizToggleWind.addEventListener('click', () => {
            toggleHeatmapLayer('wind');
            vizToggleWind.classList.toggle('active');
            showAlert('Switch to Map tab to see wind heatmap', 'info');
        });
    }
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
    
    // Hide/show views
    const mainContent = document.querySelector('.main-content');
    const vizView = document.getElementById('viz-view');
    
    if (view === 'viz') {
        // Show viz view, hide main content
        mainContent.style.display = 'none';
        vizView.style.display = 'block';
        window.scrollTo({ top: 0, behavior: 'smooth' });
    } else {
        // Show main content, hide viz view
        mainContent.style.display = 'block';
        vizView.style.display = 'none';
        
        // Scroll to relevant section
        if (view === 'map') {
            document.querySelector('.map-card').scrollIntoView({ behavior: 'smooth' });
        } else if (view === 'alerts') {
            document.querySelector('.activity-card').scrollIntoView({ behavior: 'smooth' });
        } else {
            window.scrollTo({ top: 0, behavior: 'smooth' });
        }
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

// Display data freshness indicators
function displayDataFreshness(freshnessData) {
    if (!freshnessData || !freshnessData.sources) return;
    
    // Find or create freshness container
    let freshnessContainer = document.getElementById('data-freshness-container');
    if (!freshnessContainer) {
        freshnessContainer = document.createElement('div');
        freshnessContainer.id = 'data-freshness-container';
        freshnessContainer.className = 'data-freshness-container';
        
        // Insert after prediction display
        const predictionSection = document.querySelector('.ai-prediction');
        if (predictionSection && predictionSection.parentNode) {
            predictionSection.parentNode.insertBefore(freshnessContainer, predictionSection.nextSibling);
        }
    }
    
    // Build freshness HTML
    let html = '<div class="freshness-header">📊 Data Sources</div>';
    html += '<div class="freshness-items">';
    
    for (const source of freshnessData.sources) {
        const statusIcon = source.status === 'fresh' ? '✅' :
                          source.status === 'recent' ? '🟡' :
                          source.status === 'stale' ? '🟠' :
                          source.status === 'very_stale' ? '🔴' : '⚫';
        
        html += `
            <div class="freshness-item" style="border-left: 3px solid ${source.color}">
                <span class="freshness-icon">${statusIcon}</span>
                <span class="freshness-source">${source.source.toUpperCase()}</span>
                <span class="freshness-age">${source.age_display} ago</span>
            </div>
        `;
    }
    
    html += '</div>';
    
    // Add overall confidence info
    if (freshnessData.freshness_penalty > 0.05) {
        html += `
            <div class="freshness-warning">
                ⚠️ Confidence reduced by ${Math.round(freshnessData.freshness_penalty * 100)}%: ${freshnessData.explanation}
            </div>
        `;
    }
    
    freshnessContainer.innerHTML = html;
}

// Display feedback buttons for user to report actual conditions
function displayFeedbackButtons(predictionData) {
    let feedbackContainer = document.getElementById('feedback-container');
    
    if (!feedbackContainer) {
        feedbackContainer = document.createElement('div');
        feedbackContainer.id = 'feedback-container';
        feedbackContainer.className = 'feedback-container';
        
        // Insert after data freshness or prediction
        const freshnessContainer = document.getElementById('data-freshness-container');
        const predictionSection = document.querySelector('.ai-prediction');
        const insertAfter = freshnessContainer || predictionSection;
        
        if (insertAfter && insertAfter.parentNode) {
            insertAfter.parentNode.insertBefore(feedbackContainer, insertAfter.nextSibling);
        }
    }
    
    const html = `
        <div class="feedback-header">🚗 What are road conditions actually like?</div>
        <div class="feedback-subtitle">Help improve predictions</div>
        <div class="feedback-buttons">
            <button class="feedback-btn feedback-dry" onclick="submitFeedback('dry')">
                <span class="feedback-icon">☀️</span>
                <span class="feedback-label">Dry</span>
            </button>
            <button class="feedback-btn feedback-wet" onclick="submitFeedback('wet')">
                <span class="feedback-icon">💧</span>
                <span class="feedback-label">Wet</span>
            </button>
            <button class="feedback-btn feedback-icy" onclick="submitFeedback('icy')">
                <span class="feedback-icon">🧊</span>
                <span class="feedback-label">Icy</span>
            </button>
            <button class="feedback-btn feedback-snow" onclick="submitFeedback('snow')">
                <span class="feedback-icon">❄️</span>
                <span class="feedback-label">Snow</span>
            </button>
        </div>
        <div id="feedback-status" class="feedback-status"></div>
    `;
    
    feedbackContainer.innerHTML = html;
    
    // Store prediction data for feedback submission
    window.currentPredictionData = predictionData;
}

// Submit feedback report
async function submitFeedback(actualCondition) {
    if (!currentLocation.lat || !currentLocation.lng) {
        showFeedbackStatus('❌ Location required', 'error');
        return;
    }
    
    try {
        const predictionData = window.currentPredictionData || {};
        
        const response = await fetch(`${API_BASE}/api/feedback/submit`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                lat: currentLocation.lat,
                lon: currentLocation.lng,
                actual_condition: actualCondition,
                predicted_condition: predictionData.risk_level || predictionData.prediction,
                predicted_probability: predictionData.probability,
                metadata: {
                    temperature: predictionData.temperature,
                    timestamp: new Date().toISOString()
                }
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showFeedbackStatus('✅ Thank you! Report submitted', 'success');
            // Also fetch and show nearby reports
            fetchNearbyReports();
        } else {
            showFeedbackStatus('❌ Failed to submit', 'error');
        }
    } catch (error) {
        console.error('Feedback submission error:', error);
        showFeedbackStatus('❌ Error submitting report', 'error');
    }
}

// Show feedback status message
function showFeedbackStatus(message, type) {
    const statusEl = document.getElementById('feedback-status');
    if (!statusEl) return;
    
    statusEl.textContent = message;
    statusEl.className = `feedback-status feedback-status-${type}`;
    statusEl.style.display = 'block';
    
    // Hide after 3 seconds
    setTimeout(() => {
        statusEl.style.display = 'none';
    }, 3000);
}

// Fetch and display nearby reports
async function fetchNearbyReports() {
    if (!currentLocation.lat || !currentLocation.lng) return;
    
    try {
        const response = await fetch(
            `${API_BASE}/api/feedback/nearby?lat=${currentLocation.lat}&lon=${currentLocation.lng}&radius=5&max_age_hours=2`
        );
        
        const data = await response.json();
        
        if (data.success && data.reports.length > 0) {
            displayNearbyReports(data.reports);
        }
    } catch (error) {
        console.error('Error fetching nearby reports:', error);
    }
}

// Display nearby reports
function displayNearbyReports(reports) {
    let reportsContainer = document.getElementById('nearby-reports-container');
    
    if (!reportsContainer) {
        reportsContainer = document.createElement('div');
        reportsContainer.id = 'nearby-reports-container';
        reportsContainer.className = 'nearby-reports-container';
        
        const feedbackContainer = document.getElementById('feedback-container');
        if (feedbackContainer && feedbackContainer.parentNode) {
            feedbackContainer.parentNode.insertBefore(reportsContainer, feedbackContainer.nextSibling);
        }
    }
    
    let html = '<div class="reports-header">📍 Nearby Reports (last 2 hours)</div>';
    html += '<div class="reports-list">';
    
    for (const report of reports.slice(0, 5)) {
        const conditionEmoji = {
            'dry': '☀️',
            'wet': '💧',
            'icy': '🧊',
            'snow': '❄️'
        }[report.actual_condition] || '🚗';
        
        const timeAgo = getTimeAgo(report.timestamp);
        
        html += `
            <div class="report-item">
                <span class="report-icon">${conditionEmoji}</span>
                <div class="report-details">
                    <div class="report-condition">${report.actual_condition.toUpperCase()}</div>
                    <div class="report-meta">${report.distance_miles} mi away • ${timeAgo}</div>
                </div>
            </div>
        `;
    }
    
    html += '</div>';
    reportsContainer.innerHTML = html;
}

// Get human-readable time ago
function getTimeAgo(timestamp) {
    const now = new Date();
    const then = new Date(timestamp);
    const diffMs = now - then;
    const diffMins = Math.floor(diffMs / 60000);
    
    if (diffMins < 1) return 'just now';
    if (diffMins < 60) return `${diffMins}min ago`;
    
    const diffHours = Math.floor(diffMins / 60);
    return `${diffHours}hr ago`;
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
