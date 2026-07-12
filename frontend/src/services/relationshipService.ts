import { apiClient } from "@/services/apiClient";
import type { RelationshipListResponse, Relationship } from "@/types/relationship";

export interface ListRelationshipsParams {
  policyId?: string;
  relationshipType?: string;
  limit?: number;
  offset?: number;
}

export async function listRelationships(params: ListRelationshipsParams = {}): Promise<RelationshipListResponse> {
  const response = await apiClient.get<RelationshipListResponse>("/relationships", {
    params: {
      policy_id: params.policyId,
      relationship_type: params.relationshipType,
      limit: params.limit ?? 50,
      offset: params.offset ?? 0,
    },
  });
  return response.data;
}

export async function getRelationship(relationshipId: string): Promise<Relationship> {
  const response = await apiClient.get<Relationship>(`/relationships/${relationshipId}`);
  return response.data;
}
