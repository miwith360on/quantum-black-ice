# 🚂 Railway URL Guide

## Your App URLs

When deployed to Railway, your app will be accessible at multiple URLs:

### Main URLs
```
https://web-production-59bc.up.railway.app/          → Mobile App (Default)
https://web-production-59bc.up.railway.app/mobile    → Mobile App (Explicit)
https://web-production-59bc.up.railway.app/desktop   → Desktop Version
https://web-production-59bc.up.railway.app/route-dashboard → Route Monitor
https://web-production-59bc.up.railway.app/advanced  → Advanced Dashboard
```

### All Routes Available

#### Mobile PWA (Recommended for phones)
- `/` - Default, redirects to mobile
- `/mobile`
- `/mobile.html`

#### Desktop Interface
- `/desktop`
- `/index.html`

#### Route Monitoring
- `/route-dashboard`
- `/route-dashboard.html`

#### Advanced Features
- `/advanced`
- `/advanced-dashboard.html`

---

## 📱 Best URLs for Different Devices

### iPhone / Android
**Recommended**: Just use the base URL!
```
https://web-production-59bc.up.railway.app
```
Automatically loads mobile version ✅

### Tablet (iPad, etc.)
```
https://web-production-59bc.up.railway.app/desktop
```
Better for larger screens

### Computer (Desktop/Laptop)
```
https://web-production-59bc.up.railway.app/desktop
```
Full-featured interface

### Route Monitoring (Any device)
```
https://web-production-59bc.up.railway.app/route-dashboard
```

---

## 🎯 Default Behavior

When someone visits your Railway URL (base domain), they automatically get:
- ✅ Mobile-optimized interface
- ✅ PWA features (Add to Home Screen)
- ✅ GPS location detection
- ✅ Offline support
- ✅ Touch-friendly controls

**No need to add `/mobile.html`** - it's automatic!

---

## 📲 Add to Home Screen

### iPhone
1. Visit: `https://web-production-59bc.up.railway.app`
2. Tap Share button
3. Tap "Add to Home Screen"
4. Done! Icon appears on home screen

### Android
1. Visit: `https://web-production-59bc.up.railway.app`
2. Tap menu (3 dots)
3. Tap "Add to Home screen" or "Install app"
4. Done! Works like native app

---

## 🔗 Share URLs

### Simple (Recommended)
```
Check out my Black Ice Detection app:
https://web-production-59bc.up.railway.app
```

### Specific Versions
```
Mobile: https://web-production-59bc.up.railway.app/mobile
Desktop: https://web-production-59bc.up.railway.app/desktop
Route Monitor: https://web-production-59bc.up.railway.app/route-dashboard
```

---

## 🚀 API Endpoints

Your app also has these API endpoints:

### Health Check
```
GET https://web-production-59bc.up.railway.app/api/health
```

### Current Weather
```
GET https://web-production-59bc.up.railway.app/api/weather/current?lat=42.3314&lon=-83.0458
```

### Black Ice Prediction
```
GET https://web-production-59bc.up.railway.app/api/predictions/black-ice?lat=42.3314&lon=-83.0458
```

### Quantum Prediction
```
GET https://web-production-59bc.up.railway.app/api/predictions/quantum?lat=42.3314&lon=-83.0458
```

---

## ✅ Quick Test

After deploying, test your app:

1. **Mobile Test**: Visit base URL on phone
   ```
   https://web-production-59bc.up.railway.app
   ```
   Should see mobile interface with GPS prompt

2. **API Test**: Check health endpoint
   ```
   https://web-production-59bc.up.railway.app/api/health
   ```
   Should return JSON with `"status": "healthy"`

3. **Add to Home Screen**: Try adding to phone home screen
   Should work like native app

---

## 🎉 You're Done!

Your Railway deployment automatically:
- ✅ Redirects `/` to mobile version
- ✅ Serves all pages (mobile, desktop, dashboards)
- ✅ Provides API endpoints
- ✅ Works on any device
- ✅ No need to type `/mobile.html`

**Just share the base URL and let users access from anywhere!**
