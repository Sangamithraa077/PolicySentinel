import { apiClient } from "@/services/apiClient";
import type { ExecutiveSummary, ComplianceAuditLogList } from "@/types/dashboard";

export async function getExecutiveSummary(companyId: string): Promise<ExecutiveSummary> {
  const response = await apiClient.get<ExecutiveSummary>("/compliance-dashboard/summary", {
    params: { company_id: companyId },
  });
  return response.data;
}

export async function listComplianceAuditLogs(
  companyId: string,
  limit: number = 50,
  offset: number = 0
): Promise<ComplianceAuditLogList> {
  const response = await apiClient.get<ComplianceAuditLogList>("/compliance-dashboard/audit-logs", {
    params: { company_id: companyId, limit, offset },
  });
  return response.data;
}
