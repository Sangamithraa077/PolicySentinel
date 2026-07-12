"""Debug endpoints for development and testing."""

from __future__ import annotations

import tempfile
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select

from backend.api.dependencies.database import DbSession
from backend.api.dependencies.uploads import get_file_storage_service
from backend.domain.interfaces.file_storage_interface import FileStorageInterface
from backend.models.enums import PolicyDocumentFileType
from backend.models.policy_version import PolicyVersion
from backend.parsing.pdf_text_extractor import extract_text
from backend.repositories.local_file_storage_repository import LocalFileStorageRepository
from backend.services.file_storage_service import FileStorageService

router = APIRouter()


@router.get(
    "/extract/{policy_id}",
    status_code=status.HTTP_200_OK,
    summary="Extract text from policy PDF",
    description="Development testing endpoint to retrieve an uploaded PDF path and extract its text page-by-page.",
)
def debug_extract_pdf(
    policy_id: uuid.UUID,
    db: DbSession,
    file_storage: FileStorageService = Depends(get_file_storage_service),
) -> dict:
    """Retrieve the uploaded PDF path for the given policy_id and extract its text."""
    storage = file_storage._storage
    # Find the latest non-deleted PDF version of the policy
    version = db.scalar(
        select(PolicyVersion)
        .where(
            PolicyVersion.policy_id == policy_id,
            PolicyVersion.deleted_at.is_(None),
            PolicyVersion.file_type == PolicyDocumentFileType.PDF,
        )
        .order_by(PolicyVersion.version_number.desc())
    )

    if version is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No PDF policy version found for policy '{policy_id}'.",
        )

    # If local disk storage, resolve file path directly
    if isinstance(storage, LocalFileStorageRepository):
        pdf_path = storage._root / version.source_file_reference
        if not pdf_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"PDF file does not exist on disk.",
            )
        try:
            text = extract_text(pdf_path)
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to extract text from PDF: {exc}",
            )
    else:
        # Fallback for cloud/S3 storage backends
        try:
            content = storage.load(version.source_file_reference)
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
                tmp.write(content)
                tmp_path = Path(tmp.name)
            try:
                text = extract_text(tmp_path)
            finally:
                tmp_path.unlink(missing_ok=True)
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to retrieve or extract cloud PDF content: {exc}",
            )

    return {
        "policy_id": policy_id,
        "policy_version_id": version.id,
        "original_filename": version.original_filename,
        "text": text,
        "extracted_text": text,
    }
