import { apiClient } from "@/services/apiClient";
import type { ObligationCompact } from "@/types/conflict";

export interface RegulatoryMapping {
  id: string;
  policy_id: string;
  obligation_id: string;
  framework_name: string;
  regulation_id: string;
  clause_number: string;
  confidence_score: number;
  ai_explanation: string;
  created_at: string;
  obligation?: ObligationCompact;
}

export interface RegulatoryMappingListResponse {
  items: RegulatoryMapping[];
  total: number;
}

export interface PolicyHealthScore {
  score: number;
  grade: string;
  summary: string;
  risk_factors: string[];
}

export interface RegulatoryFramework {
  id: string;
  name: string;
  jurisdiction: string | null;
  issuing_body: string | null;
  description: string | null;
}

export async function listRegulatoryMappings(params: {
  policyId?: string;
  frameworkName?: string;
  limit?: number;
  offset?: number;
} = {}): Promise<RegulatoryMappingListResponse> {
  const response = await apiClient.get<RegulatoryMappingListResponse>("/regulatory-mappings", {
    params: {
      policy_id: params.policyId,
      framework_name: params.frameworkName,
      limit: params.limit ?? 100,
      offset: params.offset ?? 0,
    },
  });
  return response.data;
}

export async function getPolicyHealthScore(policyId: string): Promise<PolicyHealthScore> {
  const response = await apiClient.get<PolicyHealthScore>(`/regulatory-mappings/health/${policyId}`);
  return response.data;
}

export async function getRegulatoryFrameworks(): Promise<RegulatoryFramework[]> {
  const response = await apiClient.get<RegulatoryFramework[]>("/regulatory-mappings/frameworks");
  return response.data;
}
