"""DTOs for policy management endpoints.

Status/file-type fields are typed as plain `str` here rather than
importing the enums straight from `models/` — keeps the public API
contract decoupled from DB structure (see schemas/README.md), even
though today the values happen to match exactly.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class PolicyVersionSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    version_number: int
    status: str
    original_filename: str
    file_type: str
    size_bytes: int
    description: str | None
    uploaded_by_user_id: uuid.UUID
    uploaded_at: datetime
    is_current: bool


class PolicySummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    company_id: uuid.UUID
    company_name: str | None = None
    title: str
    policy_code: str | None
    category: str | None
    status: str
    current_version: PolicyVersionSummary | None
    created_at: datetime
    updated_at: datetime


class PolicyDetail(PolicySummary):
    owning_department_id: uuid.UUID | None
    versions: list[PolicyVersionSummary]


class PolicyListResponse(BaseModel):
    items: list[PolicySummary]
    total: int
    limit: int
    offset: int
