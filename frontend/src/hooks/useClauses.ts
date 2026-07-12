import { useQuery } from "@tanstack/react-query";

import { listClauses, getClause } from "@/services/clauseService";

/** The full, unfiltered clause set for a policy, in document order —
 * used to build the hierarchy tree and to look up ancestors for
 * search-result breadcrumbs. */
export function useClauses(policyId: string | undefined) {
  return useQuery({
    queryKey: ["clauses", policyId],
    queryFn: () => listClauses({ policyId }),
    enabled: Boolean(policyId),
  });
}

/** Keyword search within one policy's clauses, via the backend's search
 * endpoint — kept as a separate query (rather than filtering
 * useClauses's result client-side) so search actually exercises
 * GET /clauses?keyword=. */
export function useClauseSearch(policyId: string | undefined, keyword: string) {
  const trimmed = keyword.trim();
  return useQuery({
    queryKey: ["clauses", policyId, "search", trimmed],
    queryFn: () => listClauses({ policyId, keyword: trimmed }),
    enabled: Boolean(policyId) && trimmed.length > 0,
  });
}

export function useClauseDetails(clauseId: string | undefined) {
  return useQuery({
    queryKey: ["clause", clauseId],
    queryFn: () => getClause(clauseId!),
    enabled: Boolean(clauseId),
  });
}
