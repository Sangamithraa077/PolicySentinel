/**
 * Mirrors backend schemas/clauses.py. Field names match the API's JSON
 * wire format (snake_case) directly rather than introducing a camelCase
 * translation layer.
 */

export interface Clause {
  id: string;
  policy_id: string;
  policy_version_id: string;
  parent_clause_id: string | null;
  clause_number: string | null;
  heading: string | null;
  text: string;
  order_index: number;
}

export interface ClauseListResponse {
  items: Clause[];
  total: number;
  limit: number;
  offset: number;
}
