# Quick Start Guide

## 🚀 Get Started in 3 Steps

### 1. Get Your API Key
1. Go to [OpenWeatherMap](https://openweathermap.org/api)
2. Sign up for a free account
3. Get your API key from the dashboard

### 2. Configure the Application
Open the `.env` file and add your API key:
```env
OPENWEATHER_API_KEY=your_actual_api_key_here
```

### 3. Run the Application

**Start Backend:**
```bash
# Windows
start.bat

# macOS/Linux
./venv/bin/activate
cd backend
python app.py
```

**Open Frontend:**
Simply open `frontend/index.html` in your browser!

---

## 🧪 Test the System

### Test with Demo Coordinates

Try these locations known for black ice conditions:

**Minneapolis, MN (cold climate)**
- Latitude: 44.9778
- Longitude: -93.2650

**Buffalo, NY (lake effect)**
- Latitude: 42.8864
- Longitude: -78.8784

**Anchorage, AK (extreme cold)**
- Latitude: 61.2181
- Longitude: -149.9003

### Expected Behavior

1. **Green/Low Risk** when:
   - Temperature > 2°C
   - Low humidity
   - Good wind circulation

2. **Yellow/Moderate Risk** when:
   - Temperature 0-2°C
   - Moderate humidity
   - Light winds

3. **Red/High Risk** when:
   - Temperature -5°C to 0°C
   - High humidity (>80%)
   - Very light winds
   - Recent precipitation

---

## 📝 Troubleshooting

### API Not Responding
- Check if backend is running on port 5000
- Verify your API key in `.env`
- Check OpenWeatherMap API quota

### Frontend Not Loading Data
- Ensure CORS is enabled in Flask
- Check browser console for errors
- Verify API_BASE_URL in `frontend/app.js`

### Database Errors
- Ensure `data/` directory exists
- Check write permissions
- Re-run database initialization

---

## 🎯 Next Steps

Once running successfully:

1. **Monitor Your Area**: Use "Get My Location"
2. **Track History**: Watch how conditions change
3. **Set Alerts**: Note high-risk times
4. **Share Data**: Help others stay safe

Enjoy safer winter driving! ❄️🚗
