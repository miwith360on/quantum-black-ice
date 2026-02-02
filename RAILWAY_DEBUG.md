# Railway Connection Debugging

## Quick Test URLs

If your Railway domain is: `https://your-app.railway.app`

Test these URLs from your phone's browser:

1. **Health Check**: `https://your-app.railway.app/api/health`
   - Should return JSON with status: "healthy"

2. **Mobile App**: `https://your-app.railway.app/mobile`
   - Should load the mobile interface

3. **Root**: `https://your-app.railway.app/`
   - Should load the mobile app (default)

## Common Issues

### 1. Railway Not Deployed Yet
- Check Railway dashboard: https://railway.app
- Look for "Deployment Status" - should be green checkmark
- If building, wait for build to complete

### 2. Domain Not Working
- Railway gives you a domain like: `quantum-black-ice-production.up.railway.app`
- Try with HTTPS (not HTTP): `https://`
- Check Railway settings for your custom domain

### 3. CORS Issues
- Our app has CORS enabled for all origins: `CORS(app, resources={r"/*": {"origins": "*"}})`
- Should work from any domain

### 4. Mobile Connection
- Make sure you're on WiFi or cellular data (not local network)
- Try incognito/private browsing mode
- Clear browser cache

## Check Railway Status

1. Go to Railway dashboard
2. Click on your project
3. Check "Deployments" tab
4. Look for latest commit: "fix: Add gunicorn to requirements.txt for deployment"
5. Should show:
   - ✅ Build succeeded
   - ✅ Deploy succeeded
   - 🟢 Healthy

## Get Your Railway URL

From Railway dashboard:
1. Click "Settings"
2. Under "Domains" section
3. Copy the `.railway.app` URL
4. That's your app URL

## Test Connection

From your phone:
```
1. Open browser
2. Go to: https://your-app.railway.app/api/health
3. Should see:
   {
     "status": "healthy",
     "timestamp": "...",
     "service": "Quantum Black Ice Detection (No WebSocket)"
   }
```

If that works, then go to: `https://your-app.railway.app/mobile`

## Still Not Working?

Check Railway logs:
1. Go to Railway dashboard
2. Click "Deployments"
3. Click latest deployment
4. Click "View Logs"
5. Look for errors

Common errors:
- "ModuleNotFoundError" - missing package in requirements.txt
- "Address already in use" - port conflict (shouldn't happen on Railway)
- "CORS error" - origin not allowed (we have `*` so shouldn't happen)

## Local vs Production

Your phone needs to use:
- ❌ NOT: `http://localhost:5000` (only works on your PC)
- ✅ YES: `https://your-app.railway.app` (works from anywhere)

The config.js file automatically detects this:
- On localhost → uses `http://localhost:5000`
- On Railway → uses `https://your-app.railway.app`

## Need Help?

Tell me:
1. What URL are you trying to access?
2. What error message do you see (if any)?
3. Does `https://your-app.railway.app/api/health` work in your phone browser?
