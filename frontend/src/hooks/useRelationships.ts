import { useQuery } from "@tanstack/react-query";
import { listRelationships, getRelationship } from "@/services/relationshipService";
import type { ListRelationshipsParams } from "@/services/relationshipService";

export function useRelationships(params: ListRelationshipsParams) {
  return useQuery({
    queryKey: [
      "relationships",
      params.policyId,
      params.relationshipType,
      params.limit,
      params.offset,
    ],
    queryFn: () => listRelationships(params),
  });
}

export function useRelationshipDetails(relationshipId: string | undefined) {
  return useQuery({
    queryKey: ["relationship", relationshipId],
    queryFn: () => getRelationship(relationshipId!),
    enabled: Boolean(relationshipId),
  });
}
