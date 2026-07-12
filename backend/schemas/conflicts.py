"""Pydantic schemas for Conflict API resources."""

from __future__ import annotations

import uuid
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class ObligationCompactResponse(BaseModel):
    id: uuid.UUID
    subject: str
    action: str
    object: str
    modality: str
    conditions: str | None = None
    time_constraint: str | None = None
    compliance_category: str


class PolicyCompactResponse(BaseModel):
    id: uuid.UUID
    title: str


class ConflictResponse(BaseModel):
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

    source_policy: PolicyCompactResponse
    target_policy: PolicyCompactResponse
    source_obligation: ObligationCompactResponse | None = None
    target_obligation: ObligationCompactResponse | None = None

    model_config = ConfigDict(from_attributes=True)


class ConflictListResponse(BaseModel):
    items: list[ConflictResponse]
    total: int
