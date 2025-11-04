/**
 * Route Dashboard JavaScript
 * Multi-location route monitoring with maps and radar
 */

const API_BASE_URL = 'http://localhost:5000/api';

let map = null;
let waypoints = [];
let routeLayer = null;
let markersLayer = null;
let heatmapLayer = null;
let currentRoute = null;
let savedRoutes = [];

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    initializeMap();
    initializeEventListeners();
    loadSavedRoutes();
    checkSystemHealth();
});

// Initialize map
function initializeMap() {
    map = L.map('routeMap').setView([40.7128, -74.0060], 6);
    
    // Base layer
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors',
        maxZoom: 18
    }).addTo(map);
    
    // Initialize layers
    markersLayer = L.layerGroup().addTo(map);
    
    // Map click handler - add waypoints
    map.on('click', (e) => {
        addWaypoint(e.latlng.lat, e.latlng.lng);
    });
}

// Event listeners
function initializeEventListeners() {
    document.getElementById('analyzeRouteBtn').addEventListener('click', analyzeRoute);
    document.getElementById('clearRouteBtn').addEventListener('click', clearRoute);
    document.getElementById('saveRouteBtn').addEventListener('click', openSaveModal);
    
    // Map layer toggles
    document.querySelectorAll('.map-toggle').forEach(btn => {
        btn.addEventListener('click', (e) => {
            document.querySelectorAll('.map-toggle').forEach(b => b.classList.remove('active'));
            e.target.classList.add('active');
            switchMapLayer(e.target.dataset.layer);
        });
    });
    
    // Overlay controls
    document.getElementById('showHeatmap').addEventListener('change', toggleHeatmap);
    document.getElementById('showRadar').addEventListener('change', toggleRadar);
    document.getElementById('showAlerts').addEventListener('change', toggleAlerts);
    
    // Quick location presets
    document.querySelectorAll('.location-preset').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const lat = parseFloat(e.target.dataset.lat);
            const lon = parseFloat(e.target.dataset.lon);
            map.setView([lat, lon], 12);
            checkLocationWeather(lat, lon);
        });
    });
    
    // Save route modal
    document.querySelector('.close').addEventListener('click', closeSaveModal);
    document.getElementById('saveRouteForm').addEventListener('submit', saveRoute);
}

// System health check
async function checkSystemHealth() {
    try {
        const response = await fetch(`${API_BASE_URL}/health`);
        const data = await response.json();
        
        if (data.status === 'healthy') {
            updateStatus('online', 'System Online');
        }
    } catch (error) {
        updateStatus('offline', 'System Offline');
    }
}

function updateStatus(status, text) {
    const dot = document.getElementById('statusDot');
    const statusText = document.getElementById('statusText');
    
    dot.className = `status-dot status-${status}`;
    statusText.textContent = text;
}

// Add waypoint
function addWaypoint(lat, lon, name = null) {
    const waypointName = name || `Point ${waypoints.length + 1}`;
    
    waypoints.push({
        lat: lat,
        lon: lon,
        name: waypointName
    });
    
    // Add marker
    const marker = L.marker([lat, lon], {
        icon: createWaypointIcon(waypoints.length)
    }).addTo(markersLayer);
    
    marker.bindPopup(`<strong>${waypointName}</strong><br>${lat.toFixed(4)}, ${lon.toFixed(4)}`);
    
    // Update UI
    updateWaypointsList();
    updateRouteVisualization();
    
    // Enable analyze button
    if (waypoints.length >= 2) {
        document.getElementById('analyzeRouteBtn').disabled = false;
        document.getElementById('saveRouteBtn').disabled = false;
    }
}

function createWaypointIcon(number) {
    return L.divIcon({
        className: 'waypoint-marker',
        html: `<div class="marker-pin">${number}</div>`,
        iconSize: [30, 30],
        iconAnchor: [15, 30]
    });
}

// Update waypoints list UI
function updateWaypointsList() {
    const list = document.getElementById('waypointsList');
    
    if (waypoints.length === 0) {
        list.innerHTML = '<p class="placeholder">No waypoints added</p>';
        return;
    }
    
    list.innerHTML = waypoints.map((wp, index) => `
        <div class="waypoint-item">
            <span class="waypoint-number">${index + 1}</span>
            <div class="waypoint-info">
                <strong>${wp.name}</strong>
                <small>${wp.lat.toFixed(4)}, ${wp.lon.toFixed(4)}</small>
            </div>
            <button class="btn-icon" onclick="removeWaypoint(${index})" title="Remove">✕</button>
        </div>
    `).join('');
}

// Update route visualization
function updateRouteVisualization() {
    // Remove existing route layer
    if (routeLayer) {
        map.removeLayer(routeLayer);
    }
    
    if (waypoints.length < 2) return;
    
    // Draw route line
    const latlngs = waypoints.map(wp => [wp.lat, wp.lon]);
    routeLayer = L.polyline(latlngs, {
        color: '#64c8ff',
        weight: 4,
        opacity: 0.7
    }).addTo(map);
    
    // Fit map to route
    map.fitBounds(routeLayer.getBounds(), { padding: [50, 50] });
}

// Remove waypoint
function removeWaypoint(index) {
    waypoints.splice(index, 1);
    
    // Rebuild markers
    markersLayer.clearLayers();
    waypoints.forEach((wp, i) => {
        const marker = L.marker([wp.lat, wp.lon], {
            icon: createWaypointIcon(i + 1)
        }).addTo(markersLayer);
        marker.bindPopup(`<strong>${wp.name}</strong>`);
    });
    
    updateWaypointsList();
    updateRouteVisualization();
    
    if (waypoints.length < 2) {
        document.getElementById('analyzeRouteBtn').disabled = true;
        document.getElementById('saveRouteBtn').disabled = true;
    }
}

// Clear route
function clearRoute() {
    waypoints = [];
    markersLayer.clearLayers();
    if (routeLayer) {
        map.removeLayer(routeLayer);
    }
    
    updateWaypointsList();
    document.getElementById('analyzeRouteBtn').disabled = true;
    document.getElementById('saveRouteBtn').disabled = true;
    document.getElementById('routeAnalysisCard').style.display = 'none';
}

// Analyze route
async function analyzeRoute() {
    if (waypoints.length < 2) {
        alert('Please add at least 2 waypoints');
        return;
    }
    
    updateStatus('loading', 'Analyzing route...');
    
    try {
        const response = await fetch(`${API_BASE_URL}/route/analyze`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ waypoints })
        });
        
        const data = await response.json();
        
        if (data.error) {
            throw new Error(data.error);
        }
        
        currentRoute = data;
        displayRouteAnalysis(data);
        visualizeDangerZones(data.danger_zones);
        updateStatus('online', 'Analysis Complete');
        
    } catch (error) {
        alert('Error analyzing route: ' + error.message);
        updateStatus('warning', 'Analysis Failed');
    }
}

// Display route analysis
function displayRouteAnalysis(data) {
    const card = document.getElementById('routeAnalysisCard');
    card.style.display = 'block';
    
    const summary = data.route_summary;
    
    // Update summary cards
    document.getElementById('routeDistance').textContent = `${summary.total_distance_km} km`;
    document.getElementById('maxRisk').textContent = `${summary.max_risk_probability}%`;
    document.getElementById('safetyScore').textContent = `${summary.safety_score}/100`;
    document.getElementById('dangerZones').textContent = summary.danger_zone_count;
    
    // Display recommendations
    const recDiv = document.getElementById('routeRecommendations');
    recDiv.innerHTML = '<ul>' + data.recommendations.map(rec => 
        `<li>${rec}</li>`
    ).join('') + '</ul>';
    
    // Display danger zones
    displayDangerZones(data.danger_zones);
    
    // Display segments
    displaySegments(data.segments);
}

// Display danger zones
function displayDangerZones(zones) {
    const list = document.getElementById('dangerZonesList');
    
    if (zones.length === 0) {
        list.innerHTML = '<p class="success">✅ No danger zones detected on this route</p>';
        return;
    }
    
    list.innerHTML = zones.map(zone => `
        <div class="danger-zone-item risk-${zone.risk_level}">
            <div class="zone-header">
                <strong>${zone.location}</strong>
                <span class="risk-badge ${zone.risk_level}">${zone.risk_level.toUpperCase()}</span>
            </div>
            <p>Segment ${zone.segment_id + 1} - ${zone.probability}% probability</p>
            <button class="btn-link" onclick="focusOnLocation(${zone.coordinates.lat}, ${zone.coordinates.lon})">
                📍 Show on map
            </button>
        </div>
    `).join('');
}

// Display segments
function displaySegments(segments) {
    const list = document.getElementById('segmentsList');
    
    list.innerHTML = segments.map(seg => {
        if (seg.error) {
            return `
                <div class="segment-item error">
                    <strong>Segment ${seg.segment_id + 1}</strong>
                    <p>Error: ${seg.error}</p>
                </div>
            `;
        }
        
        return `
            <div class="segment-item risk-${seg.risk_level}">
                <div class="segment-header">
                    <strong>Segment ${seg.segment_id + 1}</strong>
                    <span class="risk-badge ${seg.risk_level}">${seg.probability}%</span>
                </div>
                <div class="segment-details">
                    <small>📏 ${seg.distance_km} km</small>
                    <small>🌡️ ${seg.weather.temperature}°C</small>
                    <small>💧 ${seg.weather.humidity}%</small>
                </div>
            </div>
        `;
    }).join('');
}

// Visualize danger zones on map
function visualizeDangerZones(zones) {
    zones.forEach(zone => {
        const circle = L.circle([zone.coordinates.lat, zone.coordinates.lon], {
            color: getRiskColor(zone.risk_level),
            fillColor: getRiskColor(zone.risk_level),
            fillOpacity: 0.3,
            radius: 1000
        }).addTo(markersLayer);
        
        circle.bindPopup(`
            <strong>⚠️ Danger Zone</strong><br>
            ${zone.location}<br>
            Risk: ${zone.risk_level.toUpperCase()}<br>
            Probability: ${zone.probability}%
        `);
    });
}

function getRiskColor(level) {
    const colors = {
        none: '#10b981',
        low: '#3b82f6',
        moderate: '#f59e0b',
        high: '#f97316',
        extreme: '#ef4444'
    };
    return colors[level] || '#666';
}

// Focus on location
function focusOnLocation(lat, lon) {
    map.setView([lat, lon], 14);
}

// Check location weather
async function checkLocationWeather(lat, lon) {
    try {
        const response = await fetch(`${API_BASE_URL}/weather/current?lat=${lat}&lon=${lon}`);
        const data = await response.json();
        
        const div = document.getElementById('liveConditions');
        div.innerHTML = `
            <div class="condition-grid">
                <div class="condition-item">
                    <span class="condition-icon">🌡️</span>
                    <strong>${data.temperature}°C</strong>
                    <small>Temperature</small>
                </div>
                <div class="condition-item">
                    <span class="condition-icon">💧</span>
                    <strong>${data.humidity}%</strong>
                    <small>Humidity</small>
                </div>
                <div class="condition-item">
                    <span class="condition-icon">💨</span>
                    <strong>${data.wind_speed} m/s</strong>
                    <small>Wind</small>
                </div>
                <div class="condition-item">
                    <span class="condition-icon">☁️</span>
                    <strong>${data.weather}</strong>
                    <small>Conditions</small>
                </div>
            </div>
        `;
    } catch (error) {
        console.error('Error fetching weather:', error);
    }
}

// Map layer switching
function switchMapLayer(layer) {
    // Implementation for different map tiles
    console.log('Switching to layer:', layer);
}

function toggleHeatmap() {
    console.log('Toggle heatmap');
}

function toggleRadar() {
    console.log('Toggle radar');
}

function toggleAlerts() {
    console.log('Toggle alerts');
}

// Save route modal
function openSaveModal() {
    document.getElementById('saveRouteModal').style.display = 'block';
}

function closeSaveModal() {
    document.getElementById('saveRouteModal').style.display = 'none';
}

async function saveRoute(e) {
    e.preventDefault();
    
    const name = document.getElementById('routeName').value;
    const description = document.getElementById('routeDescription').value;
    
    try {
        const response = await fetch(`${API_BASE_URL}/routes/save`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, description, waypoints })
        });
        
        const data = await response.json();
        
        if (data.error) {
            throw new Error(data.error);
        }
        
        alert('Route saved successfully!');
        closeSaveModal();
        loadSavedRoutes();
        
    } catch (error) {
        alert('Error saving route: ' + error.message);
    }
}

// Load saved routes
async function loadSavedRoutes() {
    try {
        const response = await fetch(`${API_BASE_URL}/routes/saved`);
        const data = await response.json();
        
        savedRoutes = data.routes || [];
        displaySavedRoutes();
        
    } catch (error) {
        console.error('Error loading saved routes:', error);
    }
}

function displaySavedRoutes() {
    const list = document.getElementById('savedRoutesList');
    
    if (savedRoutes.length === 0) {
        list.innerHTML = '<p class="placeholder">No saved routes yet</p>';
        return;
    }
    
    list.innerHTML = savedRoutes.map(route => `
        <div class="saved-route-item">
            <div class="route-info">
                <strong>${route.name}</strong>
                <small>${route.waypoints.length} waypoints</small>
            </div>
            <div class="route-actions">
                <button class="btn-icon" onclick="loadRoute(${route.id})" title="Load">📂</button>
                <button class="btn-icon" onclick="quickAnalyze(${route.id})" title="Quick Analyze">⚡</button>
            </div>
        </div>
    `).join('');
}

function loadRoute(routeId) {
    const route = savedRoutes.find(r => r.id === routeId);
    if (!route) return;
    
    clearRoute();
    route.waypoints.forEach(wp => {
        addWaypoint(wp.lat, wp.lon, wp.name);
    });
}

async function quickAnalyze(routeId) {
    const route = savedRoutes.find(r => r.id === routeId);
    if (!route) return;
    
    loadRoute(routeId);
    setTimeout(() => analyzeRoute(), 500);
}
