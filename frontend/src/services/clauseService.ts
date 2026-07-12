import { apiClient } from "@/services/apiClient";
import type { ClauseListResponse } from "@/types/clause";

/** GET /clauses's max allowed page size (see backend/api/v1/endpoints/clauses.py) —
 * used as the default so the clause viewer loads a whole document in one request
 * for documents with 200 clauses or fewer. */
export const MAX_CLAUSE_PAGE_SIZE = 200;

export interface ListClausesParams {
  policyId?: string;
  policyVersionId?: string;
  keyword?: string;
  limit?: number;
  offset?: number;
}

/** Lists (or, with `keyword`, searches) clauses. Undefined params are
 * dropped by axios rather than sent as empty query values. */
export async function listClauses(params: ListClausesParams = {}): Promise<ClauseListResponse> {
  const response = await apiClient.get<ClauseListResponse>("/clauses", {
    params: {
      policy_id: params.policyId,
      policy_version_id: params.policyVersionId,
      keyword: params.keyword,
      limit: params.limit ?? MAX_CLAUSE_PAGE_SIZE,
      offset: params.offset ?? 0,
    },
  });
  return response.data;
}

export async function getClause(clauseId: string): Promise<any> {
  const response = await apiClient.get<any>(`/clauses/${clauseId}`);
  return response.data;
}
