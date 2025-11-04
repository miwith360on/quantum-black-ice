# 🚀 Quick Start - Advanced Features

Get up and running with AI/ML, WebSocket streaming, and Satellite Radar in 5 minutes!

---

## Prerequisites

- Python 3.9+ installed
- OpenWeatherMap API key (free at https://openweathermap.org/api)
- Modern web browser (Chrome, Firefox, Edge)
- ~500MB disk space for TensorFlow

---

## Installation

### 1. Install Dependencies

```bash
cd "C:\Users\Kqumo\black ice weather\quantum-black-ice"
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

This installs:
- ✅ TensorFlow 2.20.0 (AI/ML)
- ✅ Flask-SocketIO 5.5.1 (WebSocket)
- ✅ NumPy, Keras, and other dependencies

### 2. Configure API Key

Edit `.env` file:
```bash
OPENWEATHER_API_KEY=your_actual_api_key_here
```

---

## Running the System

### Start Backend Server

```bash
cd backend
python app.py
```

You should see:
```
🌨️  Quantum Black Ice Detection System starting on port 5000
🤖 AI/ML Model: Not trained yet
🛰️  Radar Service: Active
📡 WebSocket: Enabled
```

### Open Advanced Dashboard

1. Open `frontend/advanced-dashboard.html` in your browser
2. Click "Use My Location" or enter coordinates
3. Watch the magic happen! ✨

---

## Features Overview

### 🤖 AI/ML Panel (Top Left)

**What it does:**
- Uses LSTM neural network to predict black ice
- Learns from weather patterns over time
- Shows confidence levels and probability distribution

**How to use:**
1. System automatically starts collecting weather history
2. After 3+ data points, ML predictions activate
3. Green bar shows confidence level
4. Chart shows probability for each risk level

**Status indicators:**
- 🟢 Green = Model trained and ready
- 🟡 Yellow = Model loaded but untrained (using fallback)
- 🔴 Red = TensorFlow not available

### 📡 WebSocket Panel (Top Center)

**What it does:**
- Streams live weather updates
- Pushes instant alerts
- No page refresh needed!

**How to use:**
1. Connect automatically when dashboard loads
2. Watch the activity log for live updates
3. See "Last Update" timestamp change
4. Get instant weather alerts

**What to watch for:**
- 🟢 Connected = Receiving live updates
- 🔴 Disconnected = Check if backend is running
- Log shows all events in real-time

### 🛰️ Radar Panel (Top Right)

**What it does:**
- Shows live precipitation radar
- Displays satellite imagery
- Adds weather overlays to map

**How to use:**
1. Check boxes to enable layers:
   - 🌧️ Precipitation = Rain/snow radar
   - ☁️ Cloud Cover = Cloud layer
   - 🌡️ Temperature = Heat map
   - 💨 Wind Speed = Wind visualization
   - 🛰️ Satellite = GOES imagery

2. Layers appear on map below
3. Toggle on/off as needed

**Tips:**
- Don't enable all layers at once (slow)
- Precipitation radar most useful
- Satellite shows big picture

### 🗺️ Interactive Map

**Features:**
- Base map with your location
- Weather radar overlays
- Satellite imagery
- Multiple layer types

**Controls:**
- Zoom: Mouse wheel or +/- buttons
- Pan: Click and drag
- Change location: Use inputs below map

---

## Common Tasks

### Monitor Your Location

1. Open advanced dashboard
2. Click "📍 Use My Location"
3. Allow browser location access
4. System starts monitoring automatically

### Monitor Another Location

1. Enter latitude and longitude in boxes
2. Click "Update Location"
3. Map centers on new location
4. All data updates for that area

### View Weather Alerts

When severe weather detected:
- 🔴 Red banner appears at top
- Alert logged in WebSocket panel
- Automatically disappears after 10 seconds

### Check ML Confidence

Look at the confidence bar in AI/ML panel:
- 0-50% = Low confidence (needs more data)
- 50-75% = Medium confidence
- 75-100% = High confidence (reliable)

### Enable Radar Animations

1. Check "🌧️ Precipitation Radar"
2. Radar tiles load on map
3. Updates every 2 minutes automatically
4. Shows past hour of precipitation

---

## Testing the System

### Quick Test Script

```bash
python test_advanced_features.py
```

This tests:
- ✅ AI/ML model loading
- ✅ Radar data retrieval
- ✅ Satellite imagery
- ✅ WebSocket availability

Expected output:
```
🚀 ADVANCED FEATURES TEST
===========================
✅ AI/ML Deep Learning: READY
✅ Satellite & Radar: READY
✅ Real-Time WebSocket: READY
```

### Manual Testing

1. **Test AI/ML:**
   - Visit: http://localhost:5000/api/ml/model-info
   - Should show: `"tensorflow_available": true`

2. **Test Radar:**
   - Visit: http://localhost:5000/api/radar/layers?lat=42.36&lon=-71.05
   - Should show: `"success": true`

3. **Test WebSocket:**
   - Open advanced dashboard
   - Check "Connected ✅" in WebSocket panel
   - Watch for live updates in log

---

## Troubleshooting

### Problem: "TensorFlow not available"

**Solution:**
```bash
pip install tensorflow numpy
```

### Problem: "WebSocket library not available"

**Solution:**
```bash
pip install flask-socketio python-socketio
```

### Problem: "Radar layers not showing"

**Causes:**
1. Missing API key in `.env`
2. Internet connection issue
3. API rate limit exceeded

**Solution:**
1. Add API key to `.env`
2. Check internet connection
3. Wait a few minutes and try again

### Problem: "ML predictions all equal"

**Explanation:** Model is untrained and making random guesses

**Solution:**
- This is normal for new installations
- Model improves with historical data
- Or train it with real data (see ADVANCED_FEATURES.md)

### Problem: "WebSocket disconnects frequently"

**Causes:**
1. Firewall blocking port 5000
2. Backend server crashed
3. Browser extensions interfering

**Solution:**
1. Check firewall settings
2. Restart backend: `python app.py`
3. Try incognito/private browsing

---

## API Quick Reference

### AI/ML Endpoints

```
POST /api/ml/predict
GET  /api/ml/model-info
POST /api/ml/train
```

### Radar Endpoints

```
GET /api/radar/layers?lat=42.36&lon=-71.05
GET /api/satellite/imagery?lat=42.36&lon=-71.05&type=visible
GET /api/radar/composite?lat=42.36&lon=-71.05
```

### WebSocket Events

```javascript
// Client sends:
socket.emit('subscribe_location', {lat, lon})
socket.emit('unsubscribe_location', {lat, lon})

// Server sends:
socket.on('weather_update', data => {...})
socket.on('prediction_update', data => {...})
socket.on('radar_update', data => {...})
socket.on('weather_alert', data => {...})
```

---

## Performance Tips

### Optimize Backend

1. **Cache settings** (already configured):
   - Radar data: 5 minutes
   - Weather data: 60 seconds

2. **Limit subscriptions:**
   - Monitor 1-3 locations max
   - Too many = slower updates

### Optimize Frontend

1. **Limit active layers:**
   - Enable 2-3 layers maximum
   - More layers = more bandwidth

2. **Close unused tabs:**
   - Each tab = 1 WebSocket connection
   - Limit to 2-3 tabs

3. **Clear browser cache:**
   - Occasionally clear cache
   - Prevents memory leaks

---

## Next Steps

### Learn More

- 📚 **Full Documentation:** `docs/ADVANCED_FEATURES.md`
- 🗺️ **Route Monitoring:** `docs/ROUTE_MONITOR_GUIDE.md`
- 🔧 **API Reference:** See README.md

### Enhance Your System

1. **Train ML Model:**
   - Collect historical data
   - Use `/api/ml/train` endpoint
   - See ADVANCED_FEATURES.md

2. **Add More Locations:**
   - Open multiple dashboards
   - Subscribe to different cities
   - Compare conditions

3. **Build Integrations:**
   - Use WebSocket in your apps
   - Integrate with automation tools
   - Build mobile notifications

---

## Support

### Having Issues?

1. Check `test_advanced_features.py` output
2. Review backend console for errors
3. Check browser console (F12) for errors
4. Verify all dependencies installed

### Getting Help

- Check documentation in `docs/`
- Review API examples in ADVANCED_FEATURES.md
- Test individual endpoints with Postman/curl

---

## Success Checklist

✅ Backend running on port 5000
✅ All three status lights green in dashboard
✅ WebSocket shows "Connected ✅"
✅ Map displays with your location
✅ At least one radar layer enabled
✅ Activity log showing updates
✅ No errors in browser console

**If all checked: You're ready to go! 🎉**

---

**Happy monitoring! Stay safe on those icy roads! 🌨️🚗**
