/**
 * Mirrors backend schemas/conflicts.py.
 */

export interface ObligationCompact {
  id: string;
  subject: string;
  action: string;
  object: string;
  modality: string;
  conditions: string | null;
  time_constraint: string | null;
  compliance_category: string;
}

export interface PolicyCompact {
  id: string;
  title: string;
}

export interface Conflict {
  id: string;
  source_policy_id: string;
  target_policy_id: string;
  source_obligation_id: string | null;
  target_obligation_id: string | null;
  conflict_type: string;
  similarity_score: number;
  severity: string;
  ai_explanation: string | null;
  status: string;
  created_at: string;

  source_policy: PolicyCompact;
  target_policy: PolicyCompact;
  source_obligation: ObligationCompact | null;
  target_obligation: ObligationCompact | null;
}

export interface ConflictListResponse {
  items: Conflict[];
  total: number;
}
