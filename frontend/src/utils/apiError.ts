import { isAxiosError } from "axios";

import type { ApiErrorResponse } from "@/types";

/** Extracts the backend's `error.message` from a failed request, falling
 * back to a generic message for network errors or unexpected shapes. */
export function extractApiErrorMessage(error: unknown, fallback: string): string {
  if (isAxiosError<ApiErrorResponse>(error)) {
    const message = error.response?.data?.error?.message;
    if (message) return message;
    if (error.code === "ERR_NETWORK") {
      return "Couldn't reach the server. Check that the backend is running.";
    }
  }
  return fallback;
}
