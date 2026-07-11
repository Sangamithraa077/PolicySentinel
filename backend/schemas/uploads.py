"""DTOs for file upload endpoints."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class PolicyDocumentUploadResponse(BaseModel):
    # File metadata (see services/file_storage_service.py)
    original_filename: str = Field(description="The filename as sent by the client")
    stored_filename: str = Field(description="The generated, collision-free filename on disk")
    storage_path: str = Field(description="Path relative to the uploads directory")
    extension: str
    content_type: str = Field(description="Client-reported MIME type — informational only")
    size_bytes: int
    sha256: str
    uploaded_at: datetime

    # Persisted record metadata (see services/persist_policy_upload_service.py)
    policy_id: uuid.UUID
    policy_version_id: uuid.UUID
    company_id: uuid.UUID
    policy_title: str
    version_number: int
    description: str | None
    uploaded_by_user_id: uuid.UUID
