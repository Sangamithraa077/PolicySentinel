import type { ObligationCompact, PolicyCompact } from "@/types/conflict";

export interface Relationship {
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

  // Relationship classification specific fields
  relationship_type: string | null;
  explanation: string | null;
  confidence_score: number | null;

  source_policy: PolicyCompact;
  target_policy: PolicyCompact;
  source_obligation: ObligationCompact | null;
  target_obligation: ObligationCompact | null;
}

export interface RelationshipListResponse {
  items: Relationship[];
  total: number;
}
