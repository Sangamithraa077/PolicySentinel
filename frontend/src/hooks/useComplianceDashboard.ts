import { useQuery } from "@tanstack/react-query";
import { getExecutiveSummary, listComplianceAuditLogs } from "@/services/dashboardService";

export function useExecutiveSummary(companyId: string | undefined) {
  return useQuery({
    queryKey: ["compliance-summary", companyId],
    queryFn: () => getExecutiveSummary(companyId!),
    enabled: Boolean(companyId),
  });
}

export function useComplianceAuditLogs(companyId: string | undefined, limit: number = 50, offset: number = 0) {
  return useQuery({
    queryKey: ["compliance-audit-logs", companyId, limit, offset],
    queryFn: () => listComplianceAuditLogs(companyId!, limit, offset),
    enabled: Boolean(companyId),
  });
}
