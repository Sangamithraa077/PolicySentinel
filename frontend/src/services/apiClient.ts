import axios from "axios";

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
  baseURL: import.meta.env.VITE_API_BASE_URL,
});

// Extension point (not implemented): request interceptor to attach an auth
// token once authentication exists, e.g.:
// apiClient.interceptors.request.use((config) => { ... return config; });

// Extension point (not implemented): response interceptor for centralized
// error handling (e.g. redirect to login on 401), e.g.:
// apiClient.interceptors.response.use((res) => res, (error) => { ... });

export default apiClient;
