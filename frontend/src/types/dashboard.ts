export interface ExecutiveSummary {
  total_policies: number;
  total_clauses: number;
  total_obligations: number;
  active_conflicts: number;
  resolved_conflicts: number;
  pending_recommendations: number;
  compliance_score: number;
  risk_score: number;
  risk_level: string;
  risk_summary: string;
}

export interface ComplianceAuditLogEntry {
  id: string;
  company_id: string;
  event_type: string;
  user_identifier: string;
  description: string;
  occurred_at: string;
}

export interface ComplianceAuditLogList {
  items: ComplianceAuditLogEntry[];
  total: number;
}
