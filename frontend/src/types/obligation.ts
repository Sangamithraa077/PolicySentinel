/**
 * Mirrors backend schemas/obligations.py.
 */

export interface Obligation {
  id: string;
  clause_id: string;
  policy_id: string;
  subject: string;
  action: string;
  object: string;
  modality: string;
  conditions: string | null;
  time_constraint: string | null;
  compliance_category: string;
  confidence_score: number;
  ai_model: string;
  created_at: string;
  updated_at: string;
}

export interface ObligationListResponse {
  items: Obligation[];
  total: number;
  limit: number;
  offset: number;
}
