# Quantum Black Ice Detection System

<div align="center">

![Black Ice](https://img.shields.io/badge/Status-Active-success)
![Python](https://img.shields.io/badge/Python-3.9+-blue)
![Flask](https://img.shields.io/badge/Flask-3.0-lightgrey)
![TensorFlow](https://img.shields.io/badge/TensorFlow-2.20-orange)
![WebSocket](https://img.shields.io/badge/WebSocket-Live-brightgreen)
![License](https://img.shields.io/badge/License-MIT-green)

**Winter safety intelligence for black ice, route risk, and real-time road conditions**

[Features](#features) • [Installation](#installation) • [Quick Start](#quick-start) • [Overview](#-about) • [API Documentation](#api-documentation)

</div>

---

## 🌨️ About

Quantum Black Ice is a winter safety platform built to help people make better decisions when roads are most dangerous. It blends real-time weather data, route-aware risk assessment, and local freeze forecasting to surface high-risk conditions before they become hazardous.

Black ice is difficult to see, forms quickly, and can appear on bridges, ramps, shaded roads, and colder stretches of pavement before drivers notice it. This system is designed to make that risk more visible, explainable, and actionable.

### Why this matters

- Safer winter travel decisions
- Better awareness around bridges and overpasses
- Clearer local risk guidance during overnight freezes
- Trustworthy, practical forecasting for communities and fleets

## ✨ Features

### � **NEW! Cutting-Edge Technologies**

#### 🤖 AI/ML Deep Learning Models
- **TensorFlow LSTM Neural Networks** for pattern recognition
- **Historical learning** from weather sequences
- **Multi-factor analysis** (10 weather features)
- **Confidence scoring** with probability distributions
- **Continuous learning** capability with retraining API

#### 📡 Real-Time WebSocket Data Streaming
- **Live updates** every 30-60 seconds (no page refresh needed)
- **Push notifications** for weather alerts
- **Location-based subscriptions** (monitor multiple areas)
- **Instant danger zone alerts**
- **Sub-second latency** for critical updates

#### 🛰️ Satellite & Weather Radar Integration
- **Live precipitation radar** from RainViewer
- **NOAA satellite imagery** (visible, infrared, water vapor)
- **Weather overlay layers** (temperature, wind, clouds)
- **Official NOAA weather alerts**
- **Animated radar** showing past and forecast

### 🗺️ Multi-Location Route Monitor
- **Monitor entire commute routes** with waypoint-based analysis
- **Segment-by-segment risk assessment** for complete route safety
- **Save favorite routes** (home-to-work, school runs, delivery routes)
- **Danger zone identification** with visual map markers
- **Route safety scoring** (0-100 scale)
- **Quick location presets** for major cities
- **Interactive map layers** (standard, satellite, terrain)
- **Real-time weather overlays** and risk heatmaps

### 🔮 Quantum-Inspired Interface
- Animated particle system background
- Real-time risk visualization
- Interactive map with location markers
- Responsive design for all devices

### 🌡️ Weather Monitoring
- Real-time weather data from OpenWeatherMap API
- Temperature, humidity, dew point tracking
- Wind speed and precipitation monitoring
- Visibility and cloud cover analysis

### 🧠 Intelligent Prediction
- Multi-factor risk assessment algorithm
- Probability calculation (0-100%)
- Five-level risk classification (None, Low, Moderate, High, Extreme)
- Contributing factors analysis

### 📊 Data & Analytics
- SQLite database for historical data
- Prediction history tracking
- System statistics dashboard
- Active alerts monitoring

### 🚨 Safety Features
- Real-time risk alerts
- Location-specific recommendations
- Historical trend analysis
- Geolocation support

## 🚀 Installation

### Prerequisites

- Python 3.9 or higher
- Modern web browser
- OpenWeatherMap API key (free tier available)

### Step 1: Clone the Repository

```bash
cd quantum-black-ice
```

### Step 2: Set Up Python Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Step 3: Configure Environment Variables

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and add your OpenWeatherMap API key
# Get a free API key at: https://openweathermap.org/api
```

Edit `.env` file:
```env
OPENWEATHER_API_KEY=your_actual_api_key_here
FLASK_ENV=development
PORT=5000
```

### Step 4: Initialize Database

```bash
cd backend
python -c "from database import Database; db = Database(); db.initialize()"
```

## 🎯 Usage

### Starting the Backend Server

```bash
cd backend
python app.py
```

The API server will start on `http://localhost:5000`

### Opening the Frontend

Simply open `frontend/index.html` in your web browser, or use a local server:

```bash
cd frontend
# Using Python's built-in server:
python -m http.server 8000
# Then open http://localhost:8000
```

### 🗺️ Using Route Monitor Dashboard

For multi-location route monitoring:
- Open `frontend/route-dashboard.html` in your browser
- Or click "🗺️ Route Monitor" button from main dashboard
- See `ROUTE_MONITOR_GUIDE.md` for complete guide

### Using the Application

1. **Enter Location**: 
   - Manually enter latitude/longitude coordinates
   - Or click "Use My Location" to use your current position
   - Or click anywhere on the map

2. **Monitor Conditions**:
   - Click "Monitor Location" to analyze current conditions
   - View real-time risk assessment
   - Check contributing factors

3. **Review Recommendations**:
   - Read safety recommendations based on risk level
   - Check historical trends
   - Monitor active alerts

## 📡 API Documentation

### Base URL
```
http://localhost:5000/api
```

### Endpoints

#### Health Check
```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-11-04T12:00:00",
  "service": "Quantum Black Ice Detection System"
}
```

#### Get Current Weather
```http
GET /weather/current?lat=40.7128&lon=-74.0060
```

**Parameters:**
- `lat` (float): Latitude
- `lon` (float): Longitude

**Response:**
```json
{
  "temperature": -1.5,
  "humidity": 85,
  "dew_point": -2.1,
  "wind_speed": 2.5,
  "precipitation": 0.5,
  "weather": "Clear",
  "description": "clear sky"
}
```

#### Predict Black Ice
```http
POST /black-ice/predict
Content-Type: application/json

{
  "temperature": -1.5,
  "humidity": 85,
  "dew_point": -2.1,
  "wind_speed": 2.5,
  "precipitation": 0.5,
  "lat": 40.7128,
  "lon": -74.0060
}
```

**Response:**
```json
{
  "risk_level": "high",
  "probability": 78.5,
  "risk_score": 78.5,
  "factors": [
    {
      "name": "Critical Temperature Range",
      "score": 35.0,
      "description": "Surface temperature -1.5°C is in dangerous range"
    }
  ],
  "recommendations": [
    "WARNING: High black ice risk - exercise extreme caution",
    "Reduce speed significantly and increase following distance"
  ]
}
```

#### Monitor Location
```http
GET /black-ice/monitor?lat=40.7128&lon=-74.0060
```

**Response:**
```json
{
  "location": {"lat": 40.7128, "lon": -74.0060},
  "weather": {...},
  "prediction": {...},
  "history": [...],
  "timestamp": "2025-11-04T12:00:00"
}
```

#### Get Active Alerts
```http
GET /alerts
```

#### Get Statistics
```http
GET /statistics
```

## 🧮 Prediction Algorithm

The black ice prediction system uses a multi-factor analysis approach:

### Risk Factors

1. **Temperature** (40 points max)
   - Maximum risk at 0°C (32°F)
   - Range: -5°C to +2°C

2. **Humidity** (25 points max)
   - Higher humidity increases risk
   - Threshold: 80%+

3. **Dew Point Convergence** (20 points max)
   - Temperature near dew point
   - Indicates condensation likely

4. **Wind Speed** (15 points max)
   - Low wind allows ice formation
   - Threshold: < 3 m/s

5. **Recent Precipitation** (20 points max)
   - Provides moisture for ice
   - Recent rain/snow significantly increases risk

### Risk Levels

- **None**: 0-19% probability
- **Low**: 20-39% probability
- **Moderate**: 40-59% probability
- **High**: 60-79% probability
- **Extreme**: 80-100% probability

## 🗂️ Project Structure

```
quantum-black-ice/
├── backend/
│   ├── app.py                  # Flask application
│   ├── weather_service.py      # Weather API integration
│   ├── black_ice_predictor.py  # Prediction engine
│   └── database.py             # Database operations
├── frontend/
│   ├── index.html              # Main HTML
│   ├── app.js                  # Application logic
│   ├── particles.js            # Particle effects
│   └── styles.css              # Styling
├── data/
│   └── black_ice.db            # SQLite database (auto-created)
├── .github/
│   └── copilot-instructions.md # Development guidelines
├── requirements.txt            # Python dependencies
├── .env.example                # Environment template
└── README.md                   # This file
```

## 🔧 Configuration

### Environment Variables

- `OPENWEATHER_API_KEY`: Your OpenWeatherMap API key (required)
- `FLASK_ENV`: Development or production mode
- `PORT`: Backend server port (default: 5000)
- `DATABASE_PATH`: SQLite database location

### API Rate Limits

The free tier of OpenWeatherMap allows:
- 1,000 API calls per day
- 60 calls per minute

## 🧪 Testing

Run the prediction algorithm with test data:

```python
from backend.black_ice_predictor import BlackIcePredictor

predictor = BlackIcePredictor()
result = predictor.predict(
    temperature=-1.0,
    humidity=85,
    dew_point=-2.0,
    wind_speed=2.5,
    precipitation=0.5
)
print(result)
```

## 🛡️ Safety Disclaimer

**⚠️ IMPORTANT**: This system provides predictions based on available meteorological data. It should be used as a supplementary tool and not as the sole basis for travel decisions. Always:

- Exercise caution when driving in winter conditions
- Follow official weather warnings and road advisories
- Use your judgment and experience
- When in doubt, delay travel or seek alternate routes

## 📈 Future Enhancements

- [ ] Machine learning model training with historical data
- [ ] Integration with road sensor networks
- [ ] Mobile app development
- [ ] Push notifications for alerts
- [ ] Multi-location monitoring dashboard
- [ ] Road surface temperature estimation
- [ ] Social reporting features
- [ ] Integration with navigation systems

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- OpenWeatherMap for providing weather data API
- Leaflet.js for mapping capabilities
- Flask and Python community
- All contributors and testers

## 📞 Support

If you encounter any issues or have questions:

1. Check the [API Documentation](#api-documentation)
2. Review the [Installation](#installation) steps
3. Open an issue on GitHub

---

<div align="center">

**Built with ❄️ for safer winter driving**

Made by passionate developers committed to road safety

</div>
