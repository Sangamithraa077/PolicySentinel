"""Pydantic schemas for the Executive Compliance Dashboard resources."""

from __future__ import annotations

import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class ExecutiveSummaryResponse(BaseModel):
    total_policies: int
    total_clauses: int
    total_obligations: int
    active_conflicts: int
    resolved_conflicts: int
    pending_recommendations: int
    compliance_score: float
    risk_score: float
    risk_level: str
    risk_summary: str
    average_policy_health_score: float | None = 100.0

    model_config = ConfigDict(from_attributes=True)


class ComplianceAuditLogResponse(BaseModel):
    id: uuid.UUID
    company_id: uuid.UUID
    event_type: str
    user_identifier: str
    description: str
    occurred_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ComplianceAuditLogListResponse(BaseModel):
    items: list[ComplianceAuditLogResponse]
    total: int
