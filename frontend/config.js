// Frontend runtime configuration for API endpoints
// When hosted on Vercel, point to the Render backend.
// Change these if your backend domain changes.
(function(){
  // Allow Vercel env override if present
  const vercelBase = window?.process?.env?.VERCEL_PUBLIC_API_BASE;
  const fallback = "https://web-production-5be55.up.railway.app";

  if (!window.API_BASE_URL) {
    window.API_BASE_URL = vercelBase || fallback;
  }
  if (!window.WS_BASE_URL) {
    window.WS_BASE_URL = window.API_BASE_URL;
  }
})();