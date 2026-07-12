"""Pydantic schemas for Policy Comparison and Conflict Detection."""

from __future__ import annotations

import uuid
from pydantic import BaseModel, Field


class CompareRequest(BaseModel):
    version_a_id: uuid.UUID = Field(..., description="ID of policy version A")
    version_b_id: uuid.UUID = Field(..., description="ID of policy version B")


class ComparisonResultItem(BaseModel):
    obligation_a_id: uuid.UUID
    obligation_b_id: uuid.UUID
    similarity_score: float
    category: str


class ConflictDetail(BaseModel):
    subject: str | None = None
    action: str | None = None
    object: str | None = None
    modality_a: str | None = None
    modality_b: str | None = None
    time_constraint_a: str | None = None
    time_constraint_b: str | None = None


class ConflictItem(BaseModel):
    type: str
    severity: str
    description: str
    obligation_a_id: uuid.UUID | None = None
    obligation_b_id: uuid.UUID | None = None
    details: ConflictDetail


class CompareResponse(BaseModel):
    version_a_id: uuid.UUID
    version_b_id: uuid.UUID
    comparisons: list[ComparisonResultItem]
    conflicts: list[ConflictItem]
