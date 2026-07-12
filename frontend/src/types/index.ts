/**
 * Shared, cross-feature TypeScript types. Feature-specific domain types
 * (e.g. Policy) live in their own files here, such as types/policy.ts.
 */

export interface ApiErrorResponse {
  error: {
    code: string;
    message: string;
    details?: unknown;
  };
}

export * from "./obligation";
