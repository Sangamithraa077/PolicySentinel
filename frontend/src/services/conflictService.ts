import { apiClient } from "@/services/apiClient";
import type { ConflictListResponse, Conflict } from "@/types/conflict";

export interface ListConflictsParams {
  policyId?: string;
  severity?: string;
  conflictType?: string;
  status?: string;
  search?: string;
  limit?: number;
  offset?: number;
}

export async function listConflicts(params: ListConflictsParams = {}): Promise<ConflictListResponse> {
  const response = await apiClient.get<ConflictListResponse>("/conflicts", {
    params: {
      policy_id: params.policyId,
      severity: params.severity,
      conflict_type: params.conflictType,
      status: params.status,
      search: params.search,
      limit: params.limit ?? 50,
      offset: params.offset ?? 0,
    },
  });
  return response.data;
}

export async function getConflict(conflictId: string): Promise<Conflict> {
  const response = await apiClient.get<Conflict>(`/conflicts/${conflictId}`);
  return response.data;
}

export async function updateConflictStatus(conflictId: string, status: string): Promise<Conflict> {
  const response = await apiClient.patch<Conflict>(`/conflicts/${conflictId}/status`, {
    status,
  });
  return response.data;
}
