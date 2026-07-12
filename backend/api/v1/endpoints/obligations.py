"""Obligation endpoints — list/search and detail."""

from __future__ import annotations

import uuid
from fastapi import APIRouter, Depends, Query

from backend.api.dependencies.obligations import get_obligation_management_service
from backend.models.obligation import Obligation as ObligationRecord
from backend.schemas.obligations import ObligationListResponse, ObligationResponse
from backend.services.obligation_management_service import ObligationManagementService

router = APIRouter()


def _obligation_response(record: ObligationRecord) -> ObligationResponse:
    return ObligationResponse(
        id=record.id,
        clause_id=record.clause_id,
        policy_id=record.policy_id,
        subject=record.subject,
        action=record.action,
        object=record.object,
        modality=record.modality,
        conditions=record.conditions,
        time_constraint=record.time_constraint,
        compliance_category=record.compliance_category,
        confidence_score=record.confidence_score,
        ai_model=record.ai_model,
        created_at=record.created_at,
        updated_at=record.updated_at,
    )


@router.get(
    "",
    response_model=ObligationListResponse,
    summary="List or search obligations",
    description=(
        "Lists obligations, optionally filtered by policy_id, clause_id, compliance_category, "
        "and/or modality, and/or matching a keyword against subject/action/object/conditions/time_constraint. "
        "Omitting all filters lists every obligation."
    ),
)
def list_obligations(
    policy_id: uuid.UUID | None = Query(None, description="Filter by policy ID"),
    clause_id: uuid.UUID | None = Query(None, description="Filter by clause ID"),
    compliance_category: str | None = Query(None, description="Filter by compliance category"),
    modality: str | None = Query(None, description="Filter by modality (Must, Shall, Should, May)"),
    keyword: str | None = Query(
        None,
        min_length=1,
        description="Case-insensitive keyword search over subject, action, object, conditions, and time constraints",
    ),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    service: ObligationManagementService = Depends(get_obligation_management_service),
) -> ObligationListResponse:
    items, total = service.search_obligations(
        policy_id=policy_id,
        clause_id=clause_id,
        compliance_category=compliance_category,
        modality=modality,
        keyword=keyword,
        limit=limit,
        offset=offset,
    )
    return ObligationListResponse(
        items=[_obligation_response(item) for item in items],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/{obligation_id}", response_model=ObligationResponse, summary="Get obligation details")
def get_obligation(
    obligation_id: uuid.UUID,
    service: ObligationManagementService = Depends(get_obligation_management_service),
) -> ObligationResponse:
    obligation = service.get_obligation(obligation_id)
    return _obligation_response(obligation)
