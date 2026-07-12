import { useQuery } from "@tanstack/react-query";
import {
  listRegulatoryMappings,
  getPolicyHealthScore,
  getRegulatoryFrameworks,
} from "@/services/regulatoryMappingService";

export function useRegulatoryMappings(params: {
  policyId?: string;
  frameworkName?: string;
  limit?: number;
  offset?: number;
}) {
  return useQuery({
    queryKey: ["regulatory-mappings", params.policyId, params.frameworkName, params.limit, params.offset],
    queryFn: () => listRegulatoryMappings(params),
  });
}

export function usePolicyHealthScore(policyId: string | undefined) {
  return useQuery({
    queryKey: ["policy-health", policyId],
    queryFn: () => getPolicyHealthScore(policyId!),
    enabled: Boolean(policyId),
  });
}

export function useRegulatoryFrameworks() {
  return useQuery({
    queryKey: ["regulatory-frameworks"],
    queryFn: getRegulatoryFrameworks,
  });
}
