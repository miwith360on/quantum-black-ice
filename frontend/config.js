// Frontend runtime configuration for API endpoints
// Automatically uses the same domain the frontend is served from
// This prevents CORS issues when deployed to Railway
(function(){
  // If already set by environment, use that
  if (window.API_BASE_URL) {
    return;
  }

  // Auto-detect: use the same origin as the frontend
  // This works for Railway, Vercel, localhost, etc.
  const currentOrigin = window.location.origin;
  
  // If on localhost, use localhost backend
  // Otherwise, use the same domain (Railway serves both frontend and backend)
  if (currentOrigin.includes('localhost')) {
    window.API_BASE_URL = 'http://localhost:5000';
  } else {
    // Use the same domain - Railway serves backend and frontend together
    window.API_BASE_URL = currentOrigin;
  }
  
  window.WS_BASE_URL = window.API_BASE_URL;
  
  console.log('🔧 Config.js: API_BASE_URL =', window.API_BASE_URL);
})();