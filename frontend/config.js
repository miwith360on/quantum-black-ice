// Frontend runtime configuration for API endpoints
// When hosted on Vercel, point to the Render backend.
// Change these if your backend domain changes.
(function(){
  if (!window.API_BASE_URL) {
    window.API_BASE_URL = "https://quantum-black-ice.onrender.com";
  }
  if (!window.WS_BASE_URL) {
    window.WS_BASE_URL = window.API_BASE_URL;
  }
})();