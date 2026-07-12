"""Pydantic schemas for Advanced Findings API resources."""

from __future__ import annotations

import uuid
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from backend.schemas.conflicts import ObligationCompactResponse, PolicyCompactResponse


class FindingResponse(BaseModel):
    id: uuid.UUID
    source_policy_id: uuid.UUID
    target_policy_id: uuid.UUID
    source_obligation_id: uuid.UUID | None = None
    target_obligation_id: uuid.UUID | None = None
    conflict_type: str
    similarity_score: float
    severity: str
    ai_explanation: str | None = None
    status: str
    created_at: datetime

    # Extended advanced findings fields
    relationship_type: str | None = None
    explanation: str | None = None
    confidence_score: float | None = None
    temporal_conflict: str | None = None
    strength_conflict: str | None = None
    staleness_status: str | None = None
    detected_parameters: str | None = None

    source_policy: PolicyCompactResponse
    target_policy: PolicyCompactResponse
    source_obligation: ObligationCompactResponse | None = None
    target_obligation: ObligationCompactResponse | None = None

    model_config = ConfigDict(from_attributes=True)


class FindingListResponse(BaseModel):
    items: list[FindingResponse]
    total: int
