import { apiClient } from "@/services/apiClient";

export interface ApiMetadata {
  name: string;
  version: string;
  api_version: string;
}

/** Hits the aggregate router's own metadata route (backend/api/v1/router.py's
 * `api_metadata`) — a lightweight, always-available way to confirm the
 * frontend can actually reach the configured backend and to surface which
 * build it's talking to. */
export async function getApiMetadata(): Promise<ApiMetadata> {
  const response = await apiClient.get<ApiMetadata>("/");
  return response.data;
}
