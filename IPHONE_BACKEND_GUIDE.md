# 📱 iPhone Backend Connection & OpenWeather API Setup

## 🔑 Step 1: Update Your Paid OpenWeather API Key

You just purchased the paid version! Here's how to add it:

### Update .env File

1. Open: `c:\Users\Kqumo\black ice weather\quantum-black-ice\.env`

2. Replace the existing API key with your NEW paid API key:
```
OPENWEATHER_API_KEY=YOUR_NEW_PAID_API_KEY_HERE
```

3. Save the file

### Update Railway Environment Variables

Your Railway deployment needs the new key too:

1. Go to https://railway.app
2. Open your project: `quantum-black-ice`
3. Click on your service
4. Go to **Variables** tab
5. Add/Update:
   ```
   OPENWEATHER_API_KEY = YOUR_NEW_PAID_API_KEY_HERE
   ```
6. Click **Add** or **Update**
7. Railway will auto-redeploy with new key!

---

## 📱 Step 2: Check iPhone Backend Connection

### Option A: Test Local Connection (Same WiFi)

**From your PC:**
1. Find your PC's IP address:
```powershell
ipconfig
```
Look for **IPv4 Address** (e.g., `192.168.1.103`)

2. Start the server:
```powershell
cd "c:\Users\Kqumo\black ice weather\quantum-black-ice"
python backend/quick_start_no_ws.py
```

**From your iPhone:**
1. Make sure iPhone is on **SAME WiFi** as PC
2. Open Safari
3. Go to: `http://YOUR_IP:5000`
   - Example: `http://192.168.1.103:5000`
4. You should see the mobile app!

### Option B: Test Railway Connection (From Anywhere)

**From your iPhone:**
1. Open Safari
2. Go to your Railway URL:
   ```
   https://web-production-59bc.up.railway.app
   ```
3. Should see mobile app
4. Allow location when prompted
5. Weather should load!

---

## 🧪 Step 3: Test Backend APIs

### Test from iPhone Safari

Once the app loads, open **Safari Developer Console**:

**On Mac:**
1. Connect iPhone to Mac via USB
2. On Mac: Safari → Develop → [Your iPhone] → [Your Page]
3. Check Console for errors

**Quick Test URLs (open in Safari):**

1. **Health Check:**
   ```
   https://web-production-59bc.up.railway.app/api/health
   ```
   Should show: `{"status": "healthy", ...}`

2. **Weather API (Detroit):**
   ```
   https://web-production-59bc.up.railway.app/api/weather/current?lat=42.3314&lon=-83.0458
   ```
   Should show weather data JSON

3. **Mobile App:**
   ```
   https://web-production-59bc.up.railway.app
   ```
   Should load full app

---

## 🔍 Troubleshooting iPhone Backend Issues

### Issue 1: "Cannot connect to server"

**Causes:**
- Railway app not deployed yet
- Server crashed
- Wrong URL

**Solutions:**
1. Check Railway deployment status at https://railway.app
2. Check Railway logs for errors
3. Verify URL is correct
4. Try redeploying from Railway dashboard

### Issue 2: "Getting location..." never finishes

**Causes:**
- Location permission denied
- GPS disabled
- Backend not responding

**Solutions:**
1. **Allow location permission:**
   - iOS Settings → Safari → Location → While Using App
2. **Enable GPS:**
   - Settings → Privacy → Location Services → ON
3. **Test with manual location:**
   - Click "Use Detroit, MI" button in app

### Issue 3: Weather data not loading

**Causes:**
- API key invalid
- API key not set in Railway
- CORS issues (should be fixed now)

**Solutions:**
1. **Check API key is valid:**
   ```powershell
   # Test locally
   curl "http://api.openweathermap.org/data/2.5/weather?lat=42.3314&lon=-83.0458&appid=YOUR_API_KEY"
   ```
2. **Verify Railway has API key:**
   - Railway → Variables → Check OPENWEATHER_API_KEY
3. **Check Railway logs for API errors**

### Issue 4: CORS errors in console

**Should be fixed!** But if still happening:
- Clear Safari cache
- Force refresh: Cmd+Shift+R
- Check `config.js` is using `window.location.origin`

---

## 📊 Check Backend Status Dashboard

### View Railway Logs

**Option 1: Railway Dashboard**
1. Go to https://railway.app
2. Click your project
3. Click **Deployments**
4. Click latest deployment
5. Click **View Logs**

**Option 2: Railway CLI**
```powershell
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# View logs
cd "c:\Users\Kqumo\black ice weather\quantum-black-ice"
railway logs
```

### What to Look For

**Good signs:**
```
✅ Server ready at http://localhost:5000
✅ Quantum Predictor ready
✅ NOAA weather service ready
INFO:werkzeug: * Running on all addresses (0.0.0.0)
```

**Bad signs:**
```
❌ ModuleNotFoundError: No module named 'xxx'
❌ TypeError: xxx
❌ ConnectionError: xxx
❌ Exit code 1
```

---

## 🎯 Complete Test Checklist

### Local Backend (PC to iPhone on WiFi)

- [ ] PC server running: `python backend/quick_start_no_ws.py`
- [ ] PC IP found: `ipconfig`
- [ ] iPhone on same WiFi
- [ ] iPhone can access: `http://YOUR_IP:5000`
- [ ] App loads on iPhone
- [ ] Location permission granted
- [ ] Weather data loads
- [ ] Predictions display

### Railway Backend (Anywhere)

- [ ] Railway deployment successful
- [ ] Railway logs show "Server ready"
- [ ] Health check works: `/api/health`
- [ ] Weather API works: `/api/weather/current?lat=42&lon=-83`
- [ ] iPhone can access Railway URL
- [ ] App loads on iPhone
- [ ] Weather fetches automatically
- [ ] No CORS errors in console

---

## 🚀 Quick Start Commands

### Start Local Server
```powershell
cd "c:\Users\Kqumo\black ice weather\quantum-black-ice"
python backend/quick_start_no_ws.py
```

### Test Local Health
```powershell
curl http://localhost:5000/api/health
```

### Test Local Weather API
```powershell
curl "http://localhost:5000/api/weather/current?lat=42.3314&lon=-83.0458"
```

### Deploy to Railway
```powershell
# Changes auto-deploy when you push to GitHub
git add .
git commit -m "Update OpenWeather API key"
git push origin main

# Or use Railway CLI
railway up
```

---

## 💡 OpenWeather API Paid vs Free

Your paid version gives you:

### Free Tier (What you had)
- ❌ 60 calls/minute
- ❌ Basic weather data
- ❌ Current weather only

### Paid Tier (What you have now)
- ✅ Higher rate limits (depends on plan)
- ✅ Forecast data (5-day, hourly)
- ✅ Historical data
- ✅ More detailed weather info
- ✅ Better accuracy

**The app will automatically use all available data from your paid API!**

---

## 📱 Add App to iPhone Home Screen

Once backend is working:

1. Open app in Safari: `https://web-production-59bc.up.railway.app`
2. Tap **Share** button (square with arrow up)
3. Scroll down, tap **Add to Home Screen**
4. Tap **Add**
5. **Done!** App icon appears on home screen
6. Opens like native app (no Safari UI)

---

## 🔐 Security Note

**Never commit API keys to GitHub!**

Your `.env` file is in `.gitignore` ✅

But always double-check:
```powershell
git status
```
Should NOT show `.env` as changed/added

---

## 📞 Quick Reference

### Your Endpoints

**Railway (Production):**
```
Mobile:  https://web-production-59bc.up.railway.app
API:     https://web-production-59bc.up.railway.app/api/health
Weather: https://web-production-59bc.up.railway.app/api/weather/current?lat=X&lon=Y
```

**Local (Development):**
```
Mobile:  http://localhost:5000
Phone:   http://192.168.1.103:5000
API:     http://localhost:5000/api/health
Weather: http://localhost:5000/api/weather/current?lat=X&lon=Y
```

---

## ✅ Next Steps

1. **Update API key** in `.env` file
2. **Update API key** in Railway Variables
3. **Wait for Railway to redeploy** (2-3 minutes)
4. **Test on iPhone** - open Railway URL
5. **Add to home screen** for easy access!

**Your paid API will give you better weather data and predictions!** 🌤️⚡
