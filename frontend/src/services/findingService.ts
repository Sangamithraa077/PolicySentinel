import { apiClient } from "@/services/apiClient";
import type { FindingListResponse, Finding } from "@/types/finding";

export interface ListFindingsParams {
  policyId?: string;
  findingType?: string;
  limit?: number;
  offset?: number;
}

export async function listFindings(params: ListFindingsParams = {}): Promise<FindingListResponse> {
  const response = await apiClient.get<FindingListResponse>("/findings", {
    params: {
      policy_id: params.policyId,
      finding_type: params.findingType,
      limit: params.limit ?? 50,
      offset: params.offset ?? 0,
    },
  });
  return response.data;
}

export async function getFinding(findingId: string): Promise<Finding> {
  const response = await apiClient.get<Finding>(`/findings/${findingId}`);
  return response.data;
}
