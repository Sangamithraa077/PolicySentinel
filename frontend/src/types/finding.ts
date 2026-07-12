import type { ObligationCompact, PolicyCompact } from "@/types/conflict";

export interface Finding {
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

  // Extended advanced findings fields
  relationship_type: string | null;
  explanation: string | null;
  confidence_score: number | null;
  temporal_conflict: string | null;
  strength_conflict: string | null;
  staleness_status: string | null;
  detected_parameters: string | null;

  source_policy: PolicyCompact;
  target_policy: PolicyCompact;
  source_obligation: ObligationCompact | null;
  target_obligation: ObligationCompact | null;
}

export interface FindingListResponse {
  items: Finding[];
  total: number;
}
