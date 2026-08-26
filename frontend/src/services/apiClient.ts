import axios from "axios";

/**
 * The one place `VITE_API_BASE_URL` is read. Every other file that needs
 * the backend's base URL (e.g. policyService.ts's direct-download link,
 * which can't go through `apiClient` since it's a plain <a href>, not an
 * axios request) must import this constant rather than reading
 * `import.meta.env.VITE_API_BASE_URL` itself — one shared source avoids
 * the base URL (and any future host/protocol change) drifting out of
 * sync between files.
 *
 * Includes the API version prefix (e.g. `http://localhost:8000/api/v1`,
 * see .env.example) — every backend route is mounted under
 * `settings.API_V1_PREFIX` (see backend/main.py), so callers append only
 * the resource path (`/policies`, `/clauses`, ...), never `/api/v1` again.
 *
 * `VITE_API_BASE_URL` is a Vite build-time value baked into the bundle by
 * `vite build` — the production Docker image (docker/frontend/Dockerfile)
 * never sets it, so without a fallback this would compile to `undefined`
 * and every request would go out with no base URL at all. `/api/v1`
 * matches nginx.conf's reverse proxy (`location /api/`), so the built
 * bundle keeps working via a same-origin relative path in production,
 * while local dev still gets the explicit absolute URL from `.env`.
 */
export const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ||
  (import.meta.env.DEV ? "http://localhost:8001/api/v1" : "/api/v1");

/**
 * Shared Axios instance for all backend REST calls. Feature-specific
 * services (e.g. policyService.ts) should import and use this instance
 * rather than calling axios directly, so base URL, headers, and
 * interceptors stay centralized.
 *
 * No default Content-Type is set here — axios already sets
 * `application/json` automatically for plain object request bodies. A
 * hardcoded default would win over that for every request, including
 * `FormData` uploads (see policyService.ts), which need the browser to
 * set `multipart/form-data` itself with the correct boundary; a
 * manually-set static Content-Type would ship without one and the
 * server couldn't parse the body.
 */
export const apiClient = axios.create({
  baseURL: API_BASE_URL,
});

// Extension point (not implemented): request interceptor to attach an auth
// token once authentication exists, e.g.:
// apiClient.interceptors.request.use((config) => { ... return config; });

// Extension point (not implemented): response interceptor for centralized
// error handling (e.g. redirect to login on 401), e.g.:
// apiClient.interceptors.response.use((res) => res, (error) => { ... });

export default apiClient;
