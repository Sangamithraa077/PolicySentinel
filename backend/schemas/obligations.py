"""Pydantic schemas for Obligation resources."""

from __future__ import annotations

import uuid
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class ObligationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    clause_id: uuid.UUID
    policy_id: uuid.UUID
    subject: str
    action: str
    object: str
    modality: str
    conditions: str | None = None
    time_constraint: str | None = None
    compliance_category: str
    confidence_score: float
    ai_model: str
    created_at: datetime
    updated_at: datetime


class ObligationListResponse(BaseModel):
    items: list[ObligationResponse]
    total: int
    limit: int
    offset: int
