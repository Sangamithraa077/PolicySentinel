"""File upload endpoints.

Only orchestrates: validates the request shape, delegates to
`services/validate_policy_document_service.py` (is this a real, allowed
policy document?) and `services/persist_policy_upload_service.py`
(storing the file via `services/file_storage_service.py` and writing
the database records), and shapes the response. No business logic
lives here.
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, UploadFile, status

from api.dependencies.uploads import (
    get_persist_policy_upload_service,
    get_validate_policy_document_service,
)
from schemas.uploads import PolicyDocumentUploadResponse
from services.persist_policy_upload_service import PersistPolicyUploadService
from services.validate_policy_document_service import ValidatePolicyDocumentService

router = APIRouter()


@router.post(
    "/policies",
    response_model=PolicyDocumentUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a policy document",
    description=(
        "Accepts a policy document (.txt, .md, .pdf, .docx), validates its type and "
        "size, stores it (organized by company and policy), and records it as version "
        "1 of a brand-new policy (this endpoint does not yet support attaching a new "
        "version to an existing policy). Does not parse the document content or run "
        "any AI extraction."
    ),
)
async def upload_policy_document(
    file: Annotated[UploadFile, File(description="The policy document to upload")],
    company_id: Annotated[uuid.UUID, Form(description="The company this policy belongs to")],
    uploaded_by_user_id: Annotated[uuid.UUID, Form(description="The user performing the upload")],
    policy_title: Annotated[str, Form(min_length=1, description="Title for the new policy")],
    version_number: Annotated[int, Form(ge=1, description="Version number for this upload")] = 1,
    description: Annotated[
        str | None, Form(description="Optional description of this version")
    ] = None,
    validate_service: ValidatePolicyDocumentService = Depends(get_validate_policy_document_service),
    persist_service: PersistPolicyUploadService = Depends(get_persist_policy_upload_service),
) -> PolicyDocumentUploadResponse:
    validated = await validate_service.validate(file)
    persisted = persist_service.persist(
        validated,
        company_id=company_id,
        uploaded_by_user_id=uploaded_by_user_id,
        policy_title=policy_title,
        version_number=version_number,
        description=description,
    )
    return PolicyDocumentUploadResponse(
        original_filename=persisted.original_filename,
        stored_filename=persisted.stored_filename,
        storage_path=persisted.storage_path,
        extension=persisted.extension,
        content_type=persisted.content_type,
        size_bytes=persisted.size_bytes,
        sha256=persisted.sha256,
        uploaded_at=persisted.uploaded_at,
        policy_id=persisted.policy_id,
        policy_version_id=persisted.policy_version_id,
        company_id=persisted.company_id,
        policy_title=persisted.policy_title,
        version_number=persisted.version_number,
        description=persisted.description,
        uploaded_by_user_id=persisted.uploaded_by_user_id,
    )
