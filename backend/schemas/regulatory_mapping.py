"""Pydantic schemas for AI Regulatory Mappings."""
from __future__ import annotations

import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class RegulatoryMappingResponse(BaseModel):
    id: uuid.UUID
    policy_id: uuid.UUID
    obligation_id: uuid.UUID
    framework_name: str
    regulation_id: str
    clause_number: str
    confidence_score: float
    ai_explanation: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RegulatoryMappingListResponse(BaseModel):
    items: list[RegulatoryMappingResponse]
    total: int


class RegulatoryFrameworkClauseResponse(BaseModel):
    id: uuid.UUID
    regulatory_framework_id: uuid.UUID
    clause_reference: str
    title: str
    text: str
    category: str | None = None

    model_config = ConfigDict(from_attributes=True)


class RegulatoryFrameworkResponse(BaseModel):
    id: uuid.UUID
    name: str
    jurisdiction: str | None = None
    issuing_body: str | None = None
    edition_or_version: str | None = None
    description: str | None = None
    clauses: list[RegulatoryFrameworkClauseResponse] = []

    model_config = ConfigDict(from_attributes=True)


class PolicyHealthScoreResponse(BaseModel):
    score: float
    grade: str
    summary: str
    risk_factors: list[str]

