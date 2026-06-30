// In production (served by Flask on any host) the frontend is on the
// same origin as the API, so relative /api works everywhere.
// In local dev with python -m http.server :8000 the API is on :5000,
// so fall back to the full localhost URL.
window.API_BASE_URL =
  (window.location.port === "8000" && window.location.hostname === "127.0.0.1")
    ? "http://127.0.0.1:5000/api"
    : "/api";
