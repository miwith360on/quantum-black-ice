# Railway Deployment Checklist

## ✅ Files Created
- [x] Procfile
- [x] railway.toml
- [x] runtime.txt
- [x] app.py updated for Railway

## 🚀 Deploy Steps

1. **Push to GitHub:**
```bash
git add .
git commit -m "Railway deployment ready"
git push origin main
```

2. **Deploy on Railway:**
- Go to https://railway.app/dashboard
- New Project → Deploy from GitHub
- Select: quantum-black-ice repo
- Auto-deploy starts!

3. **Get URL:**
- Railway assigns: https://your-app.up.railway.app
- Mobile: /mobile.html
- Desktop: /advanced-dashboard.html

## 📱 Test URL
Once deployed, access from anywhere:
- https://your-app.up.railway.app/mobile.html

## ⚙️ Optional: Add Environment Variable
- OPENWEATHER_API_KEY (for weather overlay tiles)

## 🎯 Ready for snow week in Michigan! ❄️
