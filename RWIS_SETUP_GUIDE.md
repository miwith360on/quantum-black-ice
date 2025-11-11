# 🛣️ Real-World Data Integration Guide

## Overview
Your Quantum Black Ice Detection System now integrates **real-world data** from:
- **RWIS Sensors** (Road Weather Information System) - Real road surface temperatures from DOT sensors
- **NOAA Precipitation** - Detect freezing rain, sleet, snow (critical for black ice)

## 🆓 Free API Setup (5 minutes)

### 1. MesoWest RWIS Data (Real Road Surface Temps)

**What you get:**
- Real road surface temperatures from DOT highway sensors
- Road subsurface temperatures
- Road conditions (wet, icy, snow-covered, etc.)
- **FREE: 5,000 requests/day** (more than enough for personal use)

**Sign up (100% FREE):**
1. Go to: https://synopticdata.com/mesonet/signup/
2. Fill out the form:
   - Name, Email, Username
   - Purpose: "Personal black ice detection app"
   - Data Usage: "Road weather monitoring"
3. **Check your email** for activation link
4. Login and go to "API Services" → "Tokens"
5. Copy your API token (starts with a long string like `abc123...`)

**Add to your .env file:**
```bash
MESOWEST_API_TOKEN=your_token_here
```

### 2. NOAA Precipitation Data (Already FREE!)

**What you get:**
- Freezing rain detection (instant black ice!)
- Sleet, snow, rain detection
- Precipitation intensity
- **NO API KEY NEEDED** - NOAA Weather.gov is completely free!

Already integrated and working! 🎉

## 🚀 New Enhanced Endpoints

### 1. Enhanced QFPM (Uses Real Road Temps)
```
POST /api/qfpm/enhanced
{
  "weather_data": {
    "temperature": 32,
    "humidity": 85,
    "wind_speed": 10
  },
  "lat": 42.3314,
  "lon": -83.0458
}
```

**Returns:**
- Quantum freeze probability matrix
- **Real road surface temp** from nearby RWIS sensor (if available)
- Precipitation type and black ice risk
- Data source information

### 2. Get Real Road Surface Temps
```
GET /api/rwis/road-temp?lat=42.3314&lon=-83.0458&radius_miles=25
```

**Returns:**
```json
{
  "success": true,
  "count": 5,
  "sensors": [
    {
      "name": "I-75 @ 14 Mile Rd",
      "road_temp": 28.5,
      "subsurface_temp": 30.2,
      "road_condition": "ice warning",
      "distance_miles": 2.3,
      "lat": 42.45,
      "lon": -83.12
    }
  ]
}
```

### 3. Get Precipitation Type
```
GET /api/precipitation/type?lat=42.3314&lon=-83.0458
```

**Returns:**
```json
{
  "success": true,
  "current_type": "freezing_rain",
  "intensity": "moderate",
  "black_ice_risk": "critical",
  "forecast_next_hour": "Freezing rain likely",
  "temperature": 31,
  "wind_speed": "10 mph"
}
```

## 📊 How It Works

### Before (Simulated Data):
```
Air Temperature: 32°F
↓
QFPM uses air temp
↓
Estimated freeze risk
```

### After (Real-World Data):
```
Air Temperature: 32°F
+
Real Road Surface: 28°F (from RWIS sensor 2.3 miles away)
+
Precipitation: Freezing Rain (from NOAA)
↓
QFPM uses ACTUAL road temp
↓
MUCH MORE ACCURATE freeze risk!
```

## 🎯 Benefits

### 1. Real Road Surface Temps
- **Air temp ≠ Road temp** (roads are often 5-10°F colder!)
- RWIS sensors measure **actual pavement temperature**
- Located on highways and bridges (high-risk areas)

### 2. Freezing Rain Detection
- **Freezing rain = instant black ice** (rain freezes on contact)
- Critical for real-time alerts
- Most dangerous precipitation type

### 3. Enhanced Accuracy
- Combines quantum prediction with real-world validation
- Falls back gracefully when sensors unavailable
- Multi-source data fusion

## 🔧 Testing Your Setup

### Test RWIS Connection:
```bash
curl "http://localhost:5000/api/rwis/road-temp?lat=42.3314&lon=-83.0458&radius_miles=25"
```

### Test Precipitation Detection:
```bash
curl "http://localhost:5000/api/precipitation/type?lat=42.3314&lon=-83.0458"
```

### Test Enhanced QFPM:
```bash
curl -X POST http://localhost:5000/api/qfpm/enhanced \
  -H "Content-Type: application/json" \
  -d '{
    "weather_data": {"temperature": 32, "humidity": 85, "wind_speed": 10},
    "lat": 42.3314,
    "lon": -83.0458
  }'
```

## 📍 Finding RWIS Sensors Near You

Good locations to test (known to have RWIS sensors):
- **Detroit, MI**: `lat=42.3314, lon=-83.0458`
- **Chicago, IL**: `lat=41.8781, lon=-87.6298`
- **Minneapolis, MN**: `lat=44.9778, lon=-93.2650`
- **Denver, CO**: `lat=39.7392, lon=-104.9903`

Most highways in northern states have RWIS sensors!

## ⚠️ Rate Limits

### MesoWest (with free token):
- 5,000 requests/day
- ~3 requests/minute average
- Perfect for personal use!

### NOAA Weather.gov:
- No documented limit
- Be reasonable (don't spam!)
- Already optimized with caching

## 🔐 Security Note

**Never commit your .env file to GitHub!**

Your `.gitignore` should include:
```
.env
.env.local
*.env
```

## 📱 Mobile Integration

The mobile app will automatically use enhanced QFPM when:
1. You set `MESOWEST_API_TOKEN` in your environment
2. The backend is deployed with the token
3. You're within range of RWIS sensors

Otherwise, it gracefully falls back to air temperature estimates.

## 🎉 You're All Set!

Once you add the `MESOWEST_API_TOKEN` to your environment:
- Restart your Flask server
- The system will automatically use real road temps
- Check logs for "✅ Using real road surface temp"

No code changes needed - it's plug and play! 🚀
