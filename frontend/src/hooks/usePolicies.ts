import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";

import { useWorkspace } from "@/hooks/useWorkspace";
import { listPolicies, deletePolicy } from "@/services/policyService";

/**
 * Defaults to the active company set in Settings (see WorkspaceContext) so
 * every page that lists policies is automatically scoped to the workspace
 * the user picked, instead of always operating across every tenant. Pass
 * an explicit companyId to opt out (e.g. the company directory needs the
 * unfiltered list to discover companies in the first place).
 */
export function usePolicies(options: { companyId?: string; limit?: number } = {}) {
  const { identity, preferences } = useWorkspace();
  const companyId = options.companyId ?? identity.companyId ?? undefined;
  const limit = options.limit ?? preferences.rowsPerPage;

  return useQuery({
    queryKey: ["policies", companyId, limit],
    queryFn: () => listPolicies({ companyId, limit }),
  });
}

export function useDeletePolicy() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (policyId: string) => deletePolicy(policyId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["policies"] });
    },
  });
}
