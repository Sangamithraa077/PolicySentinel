import { useQuery } from "@tanstack/react-query";

import { listPolicies } from "@/services/policyService";

export interface CompanyDirectoryEntry {
  companyId: string;
  policyCount: number;
  companyName: string;
}

/**
 * Discovers known companies by fetching policies unscoped by company,
 * grouping by company_id and extracting company name from policy title prefix.
 */
export function useCompanyDirectory() {
  return useQuery({
    queryKey: ["company-directory"],
    queryFn: async (): Promise<CompanyDirectoryEntry[]> => {
      const response = await listPolicies({ limit: 200 });
      const counts = new Map<string, number>();
      const names = new Map<string, string>();
      if (response && response.items) {
        for (const policy of response.items) {
          counts.set(policy.company_id, (counts.get(policy.company_id) ?? 0) + 1);
          if (policy.company_name) {
            names.set(policy.company_id, policy.company_name);
          } else if (!names.has(policy.company_id) && policy.title) {
            const parts = policy.title.split(" - ");
            if (parts.length > 1 && parts[0].trim()) {
              names.set(policy.company_id, parts[0].trim());
            }
          }
        }
      }
      return Array.from(counts.entries())
        .map(([companyId, policyCount]) => ({
          companyId,
          policyCount,
          companyName: names.get(companyId) || `Company ${companyId.slice(0, 8)}`,
        }))
        .sort((a, b) => b.policyCount - a.policyCount);
    },
  });
}
