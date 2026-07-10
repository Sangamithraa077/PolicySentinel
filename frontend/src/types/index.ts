/**
 * Shared TypeScript types, mirroring backend schemas/ as real API
 * contracts are implemented. Placeholder only — no domain types yet.
 */

export interface ApiErrorResponse {
  error: {
    code: string;
    message: string;
    details?: unknown;
  };
}
