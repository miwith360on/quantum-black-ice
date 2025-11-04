# 🏗️ System Architecture

## Overview Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                      FRONTEND LAYER                                  │
│                                                                       │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐  │
│  │  Main Dashboard  │  │ Route Dashboard  │  │Advanced Dashboard│  │
│  │   (index.html)   │  │(route-dash.html) │  │(advanced-dash.)  │  │
│  │                  │  │                  │  │                  │  │
│  │ • Weather View   │  │ • Waypoint Map   │  │ • AI/ML Panel    │  │
│  │ • Risk Display   │  │ • Route Analysis │  │ • WebSocket Log  │  │
│  │ • Particle FX    │  │ • Saved Routes   │  │ • Radar Layers   │  │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘  │
│                                                                       │
│                    JavaScript + Leaflet.js + Socket.IO               │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
                                │ HTTP/REST + WebSocket
                                │
┌───────────────────────────────▼─────────────────────────────────────┐
│                      BACKEND LAYER (Flask)                           │
│                                                                       │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                    Flask Application (app.py)                 │   │
│  │  • REST API Endpoints (20+)                                   │   │
│  │  • WebSocket Server (Flask-SocketIO)                          │   │
│  │  • CORS Configuration                                         │   │
│  └────────────┬───────────────┬───────────────┬──────────────────┘   │
│               │               │               │                      │
│       ┌───────▼──────┐ ┌─────▼──────┐ ┌─────▼──────┐               │
│       │ Weather      │ │  Black Ice  │ │   Route    │               │
│       │ Service      │ │  Predictor  │ │  Monitor   │               │
│       │              │ │             │ │            │               │
│       │ • API calls  │ │ • 5 factors │ │ • Multi-   │               │
│       │ • Dew point  │ │ • Risk calc │ │   location │               │
│       └──────────────┘ └─────────────┘ └────────────┘               │
│                                                                       │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │           🚀 ADVANCED FEATURES (NEW!)                         │   │
│  │                                                                │   │
│  │  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐  │   │
│  │  │  ML Predictor  │  │  Radar Service │  │    WebSocket   │  │   │
│  │  │ (ml_predictor) │  │ (radar_service)│  │   Manager      │  │   │
│  │  │                │  │                │  │ (ws_server)    │  │   │
│  │  │ • TensorFlow   │  │ • RainViewer   │  │ • Socket.IO    │  │   │
│  │  │ • LSTM Network │  │ • NOAA Alerts  │  │ • Room-based   │  │   │
│  │  │ • 10 features  │  │ • Satellite    │  │ • Live Updates │  │   │
│  │  │ • Confidence   │  │ • Weather      │  │ • Push Alerts  │  │   │
│  │  │   Scoring      │  │   Overlays     │  │ • Subscriptions│  │   │
│  │  └────────────────┘  └────────────────┘  └────────────────┘  │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                       │
│  ┌──────────────────┐                                                │
│  │    Database      │                                                │
│  │   (SQLite)       │                                                │
│  │                  │                                                │
│  │ • Predictions    │                                                │
│  │ • Alerts         │                                                │
│  │ • Locations      │                                                │
│  │ • Routes         │                                                │
│  │ • Analyses       │                                                │
│  └──────────────────┘                                                │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
                                │ External APIs
                                │
┌───────────────────────────────▼─────────────────────────────────────┐
│                      EXTERNAL SERVICES                               │
│                                                                       │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐  │
│  │ OpenWeatherMap   │  │   RainViewer     │  │  NOAA/Weather.gov│  │
│  │                  │  │                  │  │                  │  │
│  │ • Current Weather│  │ • Radar Tiles    │  │ • Weather Alerts │  │
│  │ • Forecasts      │  │ • Precipitation  │  │ • Warnings       │  │
│  │ • Historical     │  │ • Animations     │  │ • Advisories     │  │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘  │
│                                                                       │
│  ┌──────────────────┐  ┌──────────────────┐                         │
│  │  Iowa Mesonet    │  │   OpenWeather    │                         │
│  │                  │  │   Tile Server    │                         │
│  │ • GOES Satellite │  │ • Weather Layers │                         │
│  │ • IR/Visible/WV  │  │ • Temp/Wind/Cloud│                         │
│  └──────────────────┘  └──────────────────┘                         │
└─────────────────────────────────────────────────────────────────────┘
```

## Data Flow

### 1. Standard Weather Check
```
User Request
    ↓
Frontend (index.html)
    ↓ [HTTP GET]
Flask API (/api/weather/current)
    ↓
WeatherService
    ↓ [External API]
OpenWeatherMap
    ↓ [JSON Response]
BlackIcePredictor (analyzes)
    ↓
Database (stores)
    ↓ [JSON Response]
Frontend (displays)
```

### 2. AI/ML Prediction Flow
```
Weather History (6 timesteps)
    ↓
Frontend (advanced-dashboard.js)
    ↓ [HTTP POST]
Flask API (/api/ml/predict)
    ↓
MLBlackIcePredictor
    ↓
TensorFlow LSTM Model
    ├─ Input: 10 features × 6 timesteps
    ├─ LSTM Layer 1: 128 units
    ├─ LSTM Layer 2: 64 units
    ├─ Dense Layers: 64 → 32
    └─ Output: 5 risk probabilities (softmax)
    ↓
Confidence Scoring
    ↓ [JSON Response]
Frontend (probability chart)
```

### 3. Real-Time WebSocket Flow
```
Frontend Loads
    ↓
Socket.IO Connection
    ↓
WebSocket Handshake
    ↓
Subscription (location)
    ↓
[Server Side Loop]
    ├─ Fetch Weather (every 60s)
    ├─ Run Prediction (every 30s)
    ├─ Check Radar (every 120s)
    └─ Monitor Alerts (every 10s)
    ↓
[Push to Clients]
    ├─ weather_update
    ├─ prediction_update
    ├─ radar_update
    └─ weather_alert
    ↓
Frontend Updates (live)
```

### 4. Radar/Satellite Integration
```
Map Loads
    ↓
User Enables Layer
    ↓ [HTTP GET]
Flask API (/api/radar/composite)
    ↓
RadarService
    ├─ RainViewer API (radar tiles)
    ├─ NOAA API (weather alerts)
    ├─ Mesonet (satellite imagery)
    └─ OpenWeather (overlays)
    ↓
Tile URLs Generated
    ↓ [JSON Response]
Leaflet.js
    ↓
Map Overlay Rendered
```

### 5. Route Analysis Flow
```
User Adds Waypoints
    ↓
Frontend (route-dashboard.js)
    ↓ [HTTP POST]
Flask API (/api/route/analyze)
    ↓
RouteMonitor
    ├─ Calculate segments
    ├─ For each segment:
    │   ├─ Get weather
    │   ├─ Run prediction
    │   └─ Score risk
    ↓
Aggregate Results
    ├─ Safety score (0-100)
    ├─ Danger zones
    └─ Segment details
    ↓ [JSON Response]
Frontend Map
    ├─ Draw route
    ├─ Mark danger zones
    └─ Display score
```

## Technology Stack

### Frontend
- **HTML5/CSS3** - Modern responsive design
- **JavaScript (ES6+)** - Client-side logic
- **Leaflet.js 1.9.4** - Interactive maps
- **Socket.IO 4.x** - WebSocket client
- **Particle.js** - Quantum-inspired animations

### Backend
- **Python 3.9+** - Core language
- **Flask 3.0** - Web framework
- **Flask-CORS** - Cross-origin support
- **Flask-SocketIO 5.5** - WebSocket server
- **SQLite** - Database
- **Requests** - HTTP client

### AI/ML
- **TensorFlow 2.20** - Deep learning framework
- **Keras 3.12** - Neural network API
- **NumPy 2.3** - Numerical computing
- **Architecture**: LSTM (Long Short-Term Memory)

### External APIs
- **OpenWeatherMap** - Weather data
- **RainViewer** - Radar imagery
- **NOAA/Weather.gov** - Official alerts
- **Iowa State Mesonet** - Satellite data

## File Structure

```
quantum-black-ice/
├── backend/
│   ├── app.py                    # Main Flask application
│   ├── weather_service.py        # Weather API integration
│   ├── black_ice_predictor.py    # Rule-based prediction
│   ├── ml_predictor.py           # 🆕 AI/ML deep learning
│   ├── radar_service.py          # 🆕 Radar/satellite integration
│   ├── websocket_server.py       # 🆕 Real-time streaming
│   ├── route_monitor.py          # Route analysis
│   └── database.py               # SQLite operations
│
├── frontend/
│   ├── index.html                # Main dashboard
│   ├── app.js                    # Main dashboard logic
│   ├── route-dashboard.html      # Route monitoring UI
│   ├── route-dashboard.js        # Route logic
│   ├── advanced-dashboard.html   # 🆕 Advanced features UI
│   ├── advanced-dashboard.js     # 🆕 Advanced features logic
│   ├── styles.css                # Main styles
│   └── particles.js              # Particle effects
│
├── data/
│   └── black_ice.db              # SQLite database
│
├── models/
│   └── black_ice_model.h5        # 🆕 Trained ML model (optional)
│
├── docs/
│   ├── README.md                 # Main documentation
│   ├── QUICKSTART.md             # Basic quick start
│   ├── QUICKSTART_ADVANCED.md    # 🆕 Advanced quick start
│   ├── ADVANCED_FEATURES.md      # 🆕 Complete feature guide
│   ├── ROUTE_MONITOR_GUIDE.md    # Route monitoring guide
│   └── API_DOCUMENTATION.md      # API reference
│
├── requirements.txt              # Python dependencies
├── .env                          # Environment variables
├── demo.py                       # Basic demo script
└── test_advanced_features.py     # 🆕 Advanced features test
```

## Key Design Decisions

### Why LSTM for ML?
- **Time Series Data**: Weather patterns change over time
- **Long-term Dependencies**: Conditions hours ago matter
- **Sequence Learning**: Learns from historical patterns
- **Proven Architecture**: Industry standard for weather prediction

### Why WebSocket over Polling?
- **Lower Latency**: Sub-second updates vs. seconds
- **Less Bandwidth**: Only send when data changes
- **Bidirectional**: Server can push alerts instantly
- **Better UX**: Real-time feel, no loading spinners

### Why Multiple Radar Sources?
- **Redundancy**: If one API fails, others work
- **Coverage**: Different APIs cover different areas
- **Data Quality**: RainViewer best for precipitation
- **Free Tier**: Mix of free APIs for cost control

### Why SQLite?
- **Simplicity**: No server setup needed
- **Portability**: Single file database
- **Performance**: Fast for read-heavy workloads
- **Zero Config**: Works out of the box

## Scalability Considerations

### Current Limitations
- Single server (no load balancing)
- SQLite (not distributed)
- In-memory WebSocket state
- No caching layer (Redis)

### To Scale Up (1000+ users)
1. **Database**: Migrate to PostgreSQL
2. **Caching**: Add Redis for radar tiles
3. **WebSocket**: Use Redis adapter for multi-server
4. **ML**: Move to dedicated inference server
5. **Load Balancer**: nginx with multiple Flask workers
6. **CDN**: Serve static files from CDN

### To Scale Out (10000+ users)
1. **Microservices**: Split by function
   - Weather service
   - Prediction service
   - Radar service
   - WebSocket service
2. **Message Queue**: RabbitMQ/Kafka for async
3. **Container Orchestration**: Kubernetes
4. **Distributed ML**: TensorFlow Serving cluster
5. **API Gateway**: Kong or AWS API Gateway

## Security Considerations

### Current Security
- ✅ CORS configured
- ✅ API key in environment variable
- ✅ Input validation on coordinates
- ⚠️ No rate limiting
- ⚠️ No authentication
- ⚠️ No HTTPS (development only)

### Production Checklist
- [ ] Add rate limiting (Flask-Limiter)
- [ ] Implement user authentication (JWT)
- [ ] Enable HTTPS (Let's Encrypt)
- [ ] Add request validation (marshmallow)
- [ ] Set up monitoring (Prometheus)
- [ ] Add logging (structured JSON logs)
- [ ] Secure API keys (secrets manager)
- [ ] Add CSRF protection
- [ ] Implement CSP headers
- [ ] Regular security audits

## Performance Metrics

### Current Performance (Local)
- **API Response Time**: 100-500ms
- **Weather Fetch**: 200-400ms
- **ML Prediction**: 50-150ms
- **Radar Load**: 1-2 seconds
- **WebSocket Latency**: <100ms
- **Database Query**: <50ms

### Optimization Targets
- **API**: <200ms (95th percentile)
- **ML**: <100ms (with GPU)
- **WebSocket**: <50ms
- **Page Load**: <2 seconds
- **Radar Update**: <500ms

---

**Last Updated**: November 4, 2025  
**Version**: 2.0 (Advanced Features)
