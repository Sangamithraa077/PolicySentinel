import { apiClient } from "@/services/apiClient";
import type { ObligationListResponse, Obligation } from "@/types/obligation";

export const MAX_OBLIGATION_PAGE_SIZE = 200;

export interface ListObligationsParams {
  policyId?: string;
  clauseId?: string;
  complianceCategory?: string;
  modality?: string;
  keyword?: string;
  limit?: number;
  offset?: number;
}

export async function listObligations(params: ListObligationsParams = {}): Promise<ObligationListResponse> {
  const response = await apiClient.get<ObligationListResponse>("/obligations", {
    params: {
      policy_id: params.policyId,
      clause_id: params.clauseId,
      compliance_category: params.complianceCategory,
      modality: params.modality,
      keyword: params.keyword || undefined,
      limit: params.limit ?? MAX_OBLIGATION_PAGE_SIZE,
      offset: params.offset ?? 0,
    },
  });
  return response.data;
}

export async function getObligation(obligationId: string): Promise<Obligation> {
  const response = await apiClient.get<Obligation>(`/obligations/${obligationId}`);
  return response.data;
}
