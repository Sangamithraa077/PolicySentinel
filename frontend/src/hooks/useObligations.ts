import { useQuery } from "@tanstack/react-query";
import { listObligations, getObligation } from "@/services/obligationService";
import type { ListObligationsParams } from "@/services/obligationService";

export function useObligations(params: ListObligationsParams) {
  return useQuery({
    queryKey: [
      "obligations",
      params.policyId,
      params.clauseId,
      params.complianceCategory,
      params.modality,
      params.keyword,
      params.limit,
      params.offset,
    ],
    queryFn: () => listObligations(params),
    enabled: Boolean(params.policyId),
  });
}

export function useObligationDetails(obligationId: string | undefined) {
  return useQuery({
    queryKey: ["obligation", obligationId],
    queryFn: () => getObligation(obligationId!),
    enabled: Boolean(obligationId),
  });
}
