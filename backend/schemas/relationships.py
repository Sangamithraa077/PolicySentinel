"""Pydantic schemas for Relationship API resources."""

from __future__ import annotations

import uuid
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from backend.schemas.conflicts import ObligationCompactResponse, PolicyCompactResponse


class RelationshipResponse(BaseModel):
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

    # Relationship classification specific fields
    relationship_type: str | None = None
    explanation: str | None = None
    confidence_score: float | None = None

    source_policy: PolicyCompactResponse
    target_policy: PolicyCompactResponse
    source_obligation: ObligationCompactResponse | None = None
    target_obligation: ObligationCompactResponse | None = None

    model_config = ConfigDict(from_attributes=True)


class RelationshipListResponse(BaseModel):
    items: list[RelationshipResponse]
    total: int
