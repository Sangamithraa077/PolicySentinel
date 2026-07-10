import axios from "axios";

/**
 * Shared Axios instance for all backend REST calls. Feature-specific
 * services (e.g. a future policyService.ts) should import and use this
 * instance rather than calling axios directly, so base URL, headers, and
 * interceptors stay centralized.
 */
export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

// Extension point (not implemented): request interceptor to attach an auth
// token once authentication exists, e.g.:
// apiClient.interceptors.request.use((config) => { ... return config; });

// Extension point (not implemented): response interceptor for centralized
// error handling (e.g. redirect to login on 401), e.g.:
// apiClient.interceptors.response.use((res) => res, (error) => { ... });

export default apiClient;
