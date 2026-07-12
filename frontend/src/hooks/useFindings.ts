import { useQuery } from "@tanstack/react-query";
import { listFindings, getFinding } from "@/services/findingService";
import type { ListFindingsParams } from "@/services/findingService";

export function useFindings(params: ListFindingsParams) {
  return useQuery({
    queryKey: [
      "findings",
      params.policyId,
      params.findingType,
      params.limit,
      params.offset,
    ],
    queryFn: () => listFindings(params),
  });
}

export function useFindingDetails(findingId: string | undefined) {
  return useQuery({
    queryKey: ["finding", findingId],
    queryFn: () => getFinding(findingId!),
    enabled: Boolean(findingId),
  });
}
