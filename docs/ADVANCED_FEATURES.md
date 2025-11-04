# 🚀 Advanced Features Guide

## Overview
This guide covers the three cutting-edge technologies integrated into the Quantum Black Ice Detection System:

1. **🤖 AI/ML Deep Learning Models** - TensorFlow-powered LSTM neural networks
2. **📡 Real-Time WebSocket Data Streaming** - Live updates with Socket.IO
3. **🛰️ Satellite & Weather Radar Integration** - Live radar and satellite imagery

---

## 1. AI/ML Deep Learning Models

### Technology Stack
- **TensorFlow 2.20.0** - Google's machine learning framework
- **Keras 3.12.0** - High-level neural network API
- **NumPy 2.3.4** - Numerical computing library
- **LSTM Architecture** - Long Short-Term Memory neural networks for time series

### Features
- **Pattern Recognition**: Learns from historical weather sequences
- **Multi-Factor Analysis**: 10 weather features analyzed simultaneously
- **Confidence Scoring**: Probability distribution across all risk levels
- **Continuous Learning**: Model can be retrained with new data

### Architecture
```
Input Layer (6 timesteps × 10 features)
    ↓
LSTM Layer (128 units) + Dropout (0.3)
    ↓
LSTM Layer (64 units) + Dropout (0.3)
    ↓
Dense Layer (64 units) + Dropout (0.2)
    ↓
Dense Layer (32 units)
    ↓
Output Layer (5 risk levels - softmax)
```

### API Endpoints

#### Get ML Prediction
```http
POST /api/ml/predict
Content-Type: application/json

{
  "weather_sequence": [
    {
      "temperature": 32,
      "humidity": 85,
      "dew_point": 30,
      "wind_speed": 10,
      "precipitation": 0.5,
      "pressure": 1013,
      "cloud_cover": 75,
      "temp_change_rate": -2
    },
    // ... more historical data points (up to 6)
  ]
}
```

Response:
```json
{
  "risk_level": "high",
  "confidence": 0.87,
  "all_probabilities": {
    "none": 0.02,
    "low": 0.05,
    "moderate": 0.06,
    "high": 0.87,
    "extreme": 0.00
  },
  "model": "deep_learning_lstm",
  "is_trained": true
}
```

#### Get Model Information
```http
GET /api/ml/model-info
```

Response:
```json
{
  "tensorflow_available": true,
  "model_loaded": true,
  "is_trained": true,
  "model_path": "../models/black_ice_model.h5",
  "sequence_length": 6,
  "feature_count": 10,
  "features": [
    "temperature", "humidity", "dew_point", "wind_speed",
    "precipitation", "pressure", "cloud_cover", "hour_of_day",
    "day_of_year", "temp_change_rate"
  ],
  "training_history": []
}
```

#### Train the Model
```http
POST /api/ml/train
Content-Type: application/json

{
  "training_data": [
    [
      [/* weather sequence */],
      "high"  // actual risk level
    ],
    // ... more training examples
  ],
  "epochs": 50,
  "batch_size": 32
}
```

### Usage Examples

#### Python
```python
import requests

# Prepare weather history
weather_history = [
    {
        "temperature": 32,
        "humidity": 85,
        "dew_point": 30,
        "wind_speed": 10,
        "precipitation": 0.5,
        "pressure": 1013,
        "cloud_cover": 75,
        "temp_change_rate": -2
    }
    # Add more historical points
]

# Get prediction
response = requests.post(
    'http://localhost:5000/api/ml/predict',
    json={'weather_sequence': weather_history}
)
prediction = response.json()
print(f"Risk: {prediction['risk_level']}")
print(f"Confidence: {prediction['confidence'] * 100:.1f}%")
```

#### JavaScript
```javascript
// Fetch ML prediction
async function getMLPrediction(weatherHistory) {
    const response = await fetch('http://localhost:5000/api/ml/predict', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ weather_sequence: weatherHistory })
    });
    
    const data = await response.json();
    console.log('Risk:', data.risk_level);
    console.log('Confidence:', (data.confidence * 100).toFixed(1) + '%');
    
    return data;
}
```

---

## 2. Real-Time WebSocket Data Streaming

### Technology Stack
- **Flask-SocketIO 5.5.1** - WebSocket integration for Flask
- **Socket.IO 4.x** - Real-time bidirectional event-based communication
- **Room-Based Broadcasting** - Location-specific data streams

### Features
- **Live Updates**: Weather data streams every 60 seconds
- **Instant Alerts**: Push notifications for weather warnings
- **Location Subscriptions**: Subscribe to multiple locations simultaneously
- **Automatic Reconnection**: Handles connection drops gracefully
- **Low Latency**: Sub-second data delivery

### Events

#### Client → Server Events

##### Connect
```javascript
socket = io('http://localhost:5000');

socket.on('connect', () => {
    console.log('Connected to server');
});
```

##### Subscribe to Location
```javascript
socket.emit('subscribe_location', {
    lat: 42.3601,
    lon: -71.0589
});
```

##### Unsubscribe from Location
```javascript
socket.emit('unsubscribe_location', {
    lat: 42.3601,
    lon: -71.0589
});
```

##### Request Manual Update
```javascript
socket.emit('request_update', {
    type: 'weather',  // 'weather', 'prediction', 'radar', or 'all'
    location: { lat: 42.3601, lon: -71.0589 }
});
```

#### Server → Client Events

##### Weather Update
```javascript
socket.on('weather_update', (data) => {
    console.log('Weather:', data);
    // data.location: "42.3601,-71.0589"
    // data.data: { temperature, humidity, ... }
    // data.timestamp: "2025-11-04T12:00:00"
});
```

##### Prediction Update
```javascript
socket.on('prediction_update', (data) => {
    console.log('Prediction:', data);
    // data.location: "42.3601,-71.0589"
    // data.data: { risk_level, probability, ... }
    // data.timestamp: "2025-11-04T12:00:00"
});
```

##### Radar Update
```javascript
socket.on('radar_update', (data) => {
    console.log('Radar:', data);
    // data.location: "42.3601,-71.0589"
    // data.data: { radar: {...}, alerts: [...] }
    // data.timestamp: "2025-11-04T12:00:00"
});
```

##### Weather Alert
```javascript
socket.on('weather_alert', (data) => {
    console.log('ALERT:', data);
    // data.alert: { headline, severity, urgency, ... }
    // data.timestamp: "2025-11-04T12:00:00"
});
```

##### Connection Status
```javascript
socket.on('connection_status', (data) => {
    console.log('Status:', data);
    // data.connected: true
    // data.client_id: "abc123..."
    // data.timestamp: "2025-11-04T12:00:00"
});
```

### API Endpoint

#### WebSocket Status
```http
GET /api/websocket/status
```

Response:
```json
{
  "active_connections": 5,
  "subscribed_locations": 3,
  "location_details": {
    "42.3601,-71.0589": 2,
    "40.7128,-74.0060": 1,
    "34.0522,-118.2437": 2
  },
  "socketio_available": true,
  "timestamp": "2025-11-04T12:00:00"
}
```

### Complete Example

```html
<!DOCTYPE html>
<html>
<head>
    <script src="https://cdn.socket.io/4.5.4/socket.io.min.js"></script>
</head>
<body>
    <div id="status">Connecting...</div>
    <div id="weather"></div>
    
    <script>
        const socket = io('http://localhost:5000');
        
        socket.on('connect', () => {
            document.getElementById('status').textContent = 'Connected ✅';
            
            // Subscribe to Boston
            socket.emit('subscribe_location', {
                lat: 42.3601,
                lon: -71.0589
            });
        });
        
        socket.on('weather_update', (data) => {
            const weatherDiv = document.getElementById('weather');
            weatherDiv.innerHTML = `
                <h3>Weather Update</h3>
                <p>Temperature: ${data.data.temperature}°F</p>
                <p>Humidity: ${data.data.humidity}%</p>
                <p>Time: ${data.timestamp}</p>
            `;
        });
        
        socket.on('weather_alert', (data) => {
            alert('⚠️ ' + data.alert.headline);
        });
        
        socket.on('disconnect', () => {
            document.getElementById('status').textContent = 'Disconnected ❌';
        });
    </script>
</body>
</html>
```

---

## 3. Satellite & Weather Radar Integration

### Technology Stack
- **RainViewer API** - Animated precipitation radar
- **NOAA Weather.gov** - Official weather alerts
- **OpenWeatherMap Tiles** - Weather overlay layers
- **Iowa State Mesonet** - GOES satellite imagery

### Features
- **Live Precipitation Radar**: Animated radar showing rain/snow
- **Satellite Imagery**: Visible, infrared, and water vapor
- **Weather Overlays**: Temperature, wind, clouds, precipitation
- **NOAA Alerts**: Official weather warnings and advisories
- **Time Animation**: Historical and forecast radar frames

### API Endpoints

#### Get Radar Layers
```http
GET /api/radar/layers?lat=42.3601&lon=-71.0589
```

Response:
```json
{
  "success": true,
  "radar": {
    "provider": "RainViewer",
    "layers": [
      {
        "time": 1730736000,
        "path": "/v2/radar/1730736000/256/{z}/{x}/{y}/2/1_1.png",
        "url": "https://tilecache.rainviewer.com/v2/radar/1730736000/256/{z}/{x}/{y}/2/1_1.png"
      }
    ],
    "host": "tilecache.rainviewer.com",
    "generated": 1730736000
  },
  "alerts": [
    {
      "event": "Winter Storm Warning",
      "severity": "Severe",
      "urgency": "Expected",
      "headline": "Winter Storm Warning until 6:00 PM EST",
      "description": "Heavy snow expected...",
      "onset": "2025-11-04T12:00:00-05:00",
      "expires": "2025-11-04T18:00:00-05:00"
    }
  ],
  "timestamp": "2025-11-04T12:00:00",
  "location": {"lat": 42.3601, "lon": -71.0589}
}
```

#### Get Satellite Imagery
```http
GET /api/satellite/imagery?lat=42.3601&lon=-71.0589&type=visible
```

Response:
```json
{
  "success": true,
  "layer": {
    "name": "GOES Visible",
    "description": "Visible satellite imagery",
    "url": "https://mesonet.agron.iastate.edu/cache/tile.py/1.0.0/goes-visible-1km/{z}/{x}/{y}.png",
    "attribution": "NOAA GOES via Iowa State Mesonet"
  },
  "available_layers": ["visible", "infrared", "water_vapor"],
  "timestamp": "2025-11-04T12:00:00"
}
```

#### Get Composite Layers (All-in-One)
```http
GET /api/radar/composite?lat=42.3601&lon=-71.0589
```

Response:
```json
{
  "success": true,
  "radar": { /* RainViewer data */ },
  "satellite": { /* Satellite layer */ },
  "weather_overlays": {
    "precipitation": {
      "name": "Precipitation",
      "url": "https://tile.openweathermap.org/map/precipitation_new/{z}/{x}/{y}.png?appid=YOUR_KEY",
      "opacity": 0.6
    },
    "clouds": { /* ... */ },
    "temperature": { /* ... */ },
    "wind": { /* ... */ }
  },
  "alerts": [ /* NOAA alerts */ ],
  "timestamp": "2025-11-04T12:00:00"
}
```

### Leaflet Integration

```javascript
// Initialize map
const map = L.map('map').setView([42.3601, -71.0589], 10);

// Base map
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(map);

// Add radar layer
async function addRadarLayer() {
    const response = await fetch('/api/radar/layers?lat=42.3601&lon=-71.0589');
    const data = await response.json();
    
    if (data.success && data.radar.layers.length > 0) {
        const radarUrl = data.radar.layers[0].url;
        
        L.tileLayer(radarUrl, {
            opacity: 0.6,
            attribution: 'RainViewer'
        }).addTo(map);
    }
}

// Add satellite layer
async function addSatelliteLayer() {
    const response = await fetch('/api/satellite/imagery?lat=42.3601&lon=-71.0589&type=visible');
    const data = await response.json();
    
    if (data.success) {
        L.tileLayer(data.layer.url, {
            opacity: 0.7,
            attribution: data.layer.attribution
        }).addTo(map);
    }
}

// Add weather overlays
async function addWeatherOverlays() {
    const response = await fetch('/api/radar/composite?lat=42.3601&lon=-71.0589');
    const data = await response.json();
    
    if (data.success) {
        // Add precipitation
        if (data.weather_overlays.precipitation) {
            L.tileLayer(data.weather_overlays.precipitation.url, {
                opacity: data.weather_overlays.precipitation.opacity
            }).addTo(map);
        }
        
        // Add temperature
        if (data.weather_overlays.temperature) {
            L.tileLayer(data.weather_overlays.temperature.url, {
                opacity: data.weather_overlays.temperature.opacity
            }).addTo(map);
        }
    }
}

// Load all layers
addRadarLayer();
addSatelliteLayer();
addWeatherOverlays();
```

---

## Using the Advanced Dashboard

### Accessing the Dashboard
1. Start the backend server:
   ```bash
   cd backend
   python app.py
   ```

2. Open the advanced dashboard:
   ```
   frontend/advanced-dashboard.html
   ```

### Features

#### 🤖 AI/ML Panel
- Shows model status (trained/untrained)
- Displays current prediction with confidence level
- Visualizes probability distribution across all risk levels
- Updates automatically with new weather data

#### 📡 WebSocket Panel
- Connection status indicator
- Live activity log showing all updates
- Active client count
- Last update timestamp

#### 🛰️ Radar & Satellite Panel
- Toggle individual weather layers:
  - Precipitation Radar
  - Cloud Cover
  - Temperature
  - Wind Speed
  - Satellite Imagery
- Layers update automatically

#### 📍 Location Control
- Enter custom coordinates
- Use current GPS location
- Map centers on selected location
- All data updates for new location

### Tips
1. **For Best Results**: Keep the dashboard open for 5-10 minutes to build weather history for ML predictions
2. **Multiple Locations**: Open multiple browser tabs to monitor different areas
3. **Performance**: Disable layers you don't need to reduce bandwidth
4. **Alerts**: Weather alerts appear as banners and in the WebSocket log

---

## Configuration

### Environment Variables
Add to `.env` file:
```bash
# Required for radar overlays
OPENWEATHER_API_KEY=your_api_key_here

# Optional
FLASK_ENV=development
PORT=5000
```

### Dependencies
Install all required packages:
```bash
pip install -r requirements.txt
```

Required packages:
- `tensorflow==2.20.0` - AI/ML
- `numpy==2.3.4` - Numerical computing
- `flask-socketio==5.5.1` - WebSocket server
- `python-socketio==5.14.3` - WebSocket client
- `flask==3.0.0` - Web framework
- `flask-cors==4.0.0` - CORS support
- `requests==2.31.0` - HTTP client

---

## Troubleshooting

### TensorFlow Not Loading
**Symptom**: ML predictions use fallback model

**Solutions**:
1. Ensure TensorFlow installed: `pip install tensorflow`
2. Check Python version (requires 3.9-3.13)
3. On Windows, may need Visual C++ redistributables

### WebSocket Not Connecting
**Symptom**: WebSocket status shows "Disconnected"

**Solutions**:
1. Ensure flask-socketio installed: `pip install flask-socketio python-socketio`
2. Check if port 5000 is open
3. Verify CORS settings in browser
4. Check browser console for errors

### Radar Layers Not Loading
**Symptom**: Map shows but no weather overlays

**Solutions**:
1. Add OpenWeatherMap API key to `.env`
2. Check network connection
3. Verify API rate limits not exceeded
4. Check browser console for 404 errors

### Model Not Training
**Symptom**: ML model stays in "untrained" state

**Solution**: Train the model with historical data:
```python
training_data = [
    ([weather_sequence1], 'high'),
    ([weather_sequence2], 'moderate'),
    # ... more examples
]

response = requests.post(
    'http://localhost:5000/api/ml/train',
    json={
        'training_data': training_data,
        'epochs': 50
    }
)
```

---

## Performance Optimization

### Backend
- **Caching**: Radar data cached for 5 minutes
- **Batch Updates**: WebSocket sends updates in batches
- **Connection Pooling**: Reuses HTTP connections

### Frontend
- **Debouncing**: Map updates debounced to prevent excessive requests
- **Lazy Loading**: Layers loaded only when toggled on
- **Memory Management**: Old log entries automatically pruned

### Recommendations
- Use `async_mode='threading'` for SocketIO on Windows
- Limit active radar layers to 2-3 simultaneously
- Clear browser cache if performance degrades
- Increase update intervals for slower connections

---

## Next Steps

### Enhance ML Model
1. Collect historical black ice incident data
2. Train model with real-world examples
3. Implement continuous learning pipeline
4. Add model versioning and rollback

### Expand Radar Coverage
1. Integrate additional radar sources (NEXRAD, Weather Underground)
2. Add historical radar playback
3. Implement radar animation controls
4. Add custom color schemes

### WebSocket Enhancements
1. Add user authentication
2. Implement private channels
3. Add message queuing for reliability
4. Build mobile app with WebSocket support

---

## Resources

- **TensorFlow**: https://www.tensorflow.org/
- **Socket.IO**: https://socket.io/
- **RainViewer API**: https://www.rainviewer.com/api.html
- **NOAA API**: https://www.weather.gov/documentation/services-web-api
- **Leaflet.js**: https://leafletjs.com/

---

**🎉 Congratulations!** You now have a cutting-edge black ice detection system with AI/ML, real-time streaming, and satellite radar integration!
