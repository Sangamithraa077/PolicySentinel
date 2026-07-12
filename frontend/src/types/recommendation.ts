/**
 * Mirrors backend schemas/recommendations.py.
 */

export interface Recommendation {
  id: string;
  conflict_id: string;
  recommendation_summary: string;
  suggested_action: string;
  original_clause: string | null;
  revised_clause: string | null;
  reason: string;
  ai_model: string;
  confidence_score: number;
  status: string;
  created_at: string;
}

export interface RecommendationListResponse {
  items: Recommendation[];
  total: number;
}
