import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";

import { listPolicies, deletePolicy } from "@/services/policyService";

export function usePolicies() {
  return useQuery({
    queryKey: ["policies"],
    queryFn: () => listPolicies({ limit: 50 }),
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
