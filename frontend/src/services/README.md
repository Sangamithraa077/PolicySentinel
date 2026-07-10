# services/ — API Client Layer

Wraps all HTTP calls to the FastAPI backend (e.g. `policyService.ts`, `authService.ts`, `conflictService.ts`). Centralizes the base HTTP client (headers, auth token attachment, error handling) so components and hooks never call `fetch`/`axios` directly.
