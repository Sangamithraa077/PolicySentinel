import { useQuery } from "@tanstack/react-query";

import { listPolicies } from "@/services/policyService";

export interface CompanyDirectoryEntry {
  companyId: string;
  policyCount: number;
}

/**
 * There's no /companies endpoint (see backend/models/company.py — the API
 * never exposes company name/listing), so this discovers known companies
 * the only way available: fetching policies unscoped by company and
 * grouping by company_id. Good enough for a switcher populated from
 * whatever tenants actually have data; it won't surface an empty company
 * with zero policies, but there's nothing to show for one anyway.
 */
export function useCompanyDirectory() {
  return useQuery({
    queryKey: ["company-directory"],
    queryFn: async (): Promise<CompanyDirectoryEntry[]> => {
      const response = await listPolicies({ limit: 200 });
      const counts = new Map<string, number>();
      for (const policy of response.items) {
        counts.set(policy.company_id, (counts.get(policy.company_id) ?? 0) + 1);
      }
      return Array.from(counts.entries())
        .map(([companyId, policyCount]) => ({ companyId, policyCount }))
        .sort((a, b) => b.policyCount - a.policyCount);
    },
  });
}
