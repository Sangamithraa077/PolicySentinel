import { useQuery } from "@tanstack/react-query";

import { listPolicies } from "@/services/policyService";

export function usePolicies() {
  return useQuery({
    queryKey: ["policies"],
    queryFn: () => listPolicies({ limit: 50 }),
  });
}
