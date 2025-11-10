# Legacy Render Deployment (Deprecated)

Render deployment instructions have been deprecated. The active, supported production path is:

* Backend: Railway (`Procfile`, `railway.toml`, `railway.json`)
* Frontend: Vercel (`vercel.json` rewrites + static caching)

This file is retained only for historical reference. Prefer reading `RAILWAY_DEPLOYMENT.md` for current steps.

## ✅ Migration Notes

1. Set default API base in `frontend/config.js` to your Railway domain.
2. Use Gunicorn + eventlet via `Procfile` for WebSocket support.
3. Remove any lingering `RENDER` env flags from automation scripts.
4. Update docs and bookmarks to the new Railway URL.

## 🗑️ Safe to Delete

You may delete this file once you confirm Railway is stable.

---

## Quick Railway Health Checks (Examples)

```powershell
curl https://web-production-EXAMPLE.up.railway.app/api/health
curl "https://web-production-EXAMPLE.up.railway.app/api/rwis/road-temp?lat=42.52&lon=-83.10&radius_miles=25"
```

Replace `web-production-EXAMPLE` with your actual Railway subdomain.

---

For active deployment guidance: see `RAILWAY_DEPLOYMENT.md`.
