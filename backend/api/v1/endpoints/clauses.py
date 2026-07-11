"""Clause endpoints — list/search and detail.

Only orchestrates: calls into `services/clause_management_service.py`
and shapes the response. No document parsing, no segmentation, no AI.

Deletion is deliberately not exposed here as its own endpoint: a clause
only ever disappears as a side effect of `DELETE /policies/{policy_id}`
removing its owning policy version (see
`services/policy_management_service.py::delete_policy`) — there is no
standalone "delete this clause" operation.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query

from backend.api.dependencies.clauses import get_clause_management_service
from backend.domain.interfaces.clause_repository_interface import StoredClause
from backend.schemas.clauses import ClauseListResponse, ClauseResponse
from backend.services.clause_management_service import ClauseManagementService

router = APIRouter()


def _clause_response(clause: StoredClause) -> ClauseResponse:
    return ClauseResponse(
        id=clause.id,
        policy_id=clause.policy_id,
        policy_version_id=clause.policy_version_id,
        parent_clause_id=clause.parent_clause_id,
        clause_number=clause.clause_number,
        heading=clause.heading,
        text=clause.text,
        order_index=clause.order_index,
    )


@router.get(
    "",
    response_model=ClauseListResponse,
    summary="List or search clauses",
    description=(
        "Lists clauses, optionally filtered to one policy and/or one policy version, and/or "
        "matching a keyword against clause text/heading. Omitting all filters lists every "
        "clause. Combine `policy_id` (or `policy_version_id`) with `keyword` to search within "
        "one policy's clauses."
    ),
)
def list_clauses(
    policy_id: uuid.UUID | None = Query(None, description="Filter to clauses of one policy"),
    policy_version_id: uuid.UUID | None = Query(
        None, description="Filter to clauses of one specific policy version"
    ),
    keyword: str | None = Query(
        None,
        min_length=1,
        description="Case-insensitive keyword search over clause text and heading",
    ),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    service: ClauseManagementService = Depends(get_clause_management_service),
) -> ClauseListResponse:
    items, total = service.search(
        policy_id=policy_id,
        policy_version_id=policy_version_id,
        keyword=keyword,
        limit=limit,
        offset=offset,
    )
    return ClauseListResponse(
        items=[_clause_response(clause) for clause in items],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/{clause_id}", response_model=ClauseResponse, summary="Get clause details")
def get_clause(
    clause_id: uuid.UUID,
    service: ClauseManagementService = Depends(get_clause_management_service),
) -> ClauseResponse:
    clause = service.get_clause(clause_id)
    return _clause_response(clause)
