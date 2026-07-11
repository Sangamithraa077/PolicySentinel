"""Use case: persist a validated policy document as a new Policy +
PolicyVersion pair, storing its file along the way.

Talks to the ORM (models/) directly rather than through a repository
interface — no PolicyRepository abstraction exists yet, and building
one for this single write path would be premature; introduce it if a
second use case needs to reuse this persistence logic.

Every upload through this endpoint creates a brand-new Policy (there is
no "add a version to an existing policy" flow yet), owned by the given
company, with no department assignment — that's a later triage step.

The Policy row is flushed (INSERTed within the transaction, not yet
committed) before the file is stored, specifically so the file storage
service can organize the file under .../policies/{policy_id}/ — the
policy has to exist to be organized by. If anything fails afterward —
storage error, or the PolicyVersion insert itself — the transaction is
rolled back and, if the file was already written, it's deleted too, so
a failed upload never leaves an orphan behind in either the database or
storage.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.domain.exceptions.policy_exceptions import CompanyNotFoundError, UserNotFoundError
from backend.models.company import Company
from backend.models.enums import PolicyDocumentFileType, PolicyStatus, PolicyVersionStatus
from backend.models.policy import Policy
from backend.models.policy_version import PolicyVersion
from backend.models.user import User
from backend.services.file_storage_service import FileStorageService, StoredFile
from backend.services.validate_policy_document_service import ValidatedPolicyDocument

_EXTENSION_TO_FILE_TYPE: dict[str, PolicyDocumentFileType] = {
    ".txt": PolicyDocumentFileType.TXT,
    ".md": PolicyDocumentFileType.MD,
    ".pdf": PolicyDocumentFileType.PDF,
    ".docx": PolicyDocumentFileType.DOCX,
}


@dataclass(frozen=True)
class PersistedPolicyUpload:
    policy_id: uuid.UUID
    policy_version_id: uuid.UUID
    company_id: uuid.UUID
    policy_title: str
    version_number: int
    description: str | None
    uploaded_by_user_id: uuid.UUID
    original_filename: str
    stored_filename: str
    storage_path: str
    extension: str
    content_type: str
    size_bytes: int
    sha256: str
    uploaded_at: datetime


class PersistPolicyUploadService:
    def __init__(self, db: Session, file_storage: FileStorageService) -> None:
        self._db = db
        self._file_storage = file_storage

    def persist(
        self,
        validated: ValidatedPolicyDocument,
        *,
        company_id: uuid.UUID,
        uploaded_by_user_id: uuid.UUID,
        policy_title: str,
        version_number: int,
        description: str | None,
    ) -> PersistedPolicyUpload:
        stored: StoredFile | None = None
        try:
            company = self._db.scalar(
                select(Company).where(Company.id == company_id, Company.deleted_at.is_(None))
            )
            if company is None:
                raise CompanyNotFoundError(f"Company '{company_id}' does not exist.")

            uploader = self._db.scalar(
                select(User).where(User.id == uploaded_by_user_id, User.deleted_at.is_(None))
            )
            if uploader is None:
                raise UserNotFoundError(f"User '{uploaded_by_user_id}' does not exist.")

            policy = Policy(
                company=company,
                owning_department=None,
                title=policy_title,
                status=PolicyStatus.DRAFT,
            )
            self._db.add(policy)
            self._db.flush()  # allocates policy.id so the file can be organized under it

            stored = self._file_storage.store(
                validated.content,
                company_id=company.id,
                policy_id=policy.id,
                extension=validated.extension,
                content_type=validated.content_type,
            )

            version = PolicyVersion(
                policy=policy,
                version_number=version_number,
                source_file_reference=stored.storage_path,
                file_hash=stored.sha256,
                uploaded_by=uploader,
                status=PolicyVersionStatus.DRAFT,
                original_filename=validated.original_filename,
                size_bytes=stored.size_bytes,
                file_type=_EXTENSION_TO_FILE_TYPE[validated.extension],
                description=description,
                uploaded_at=stored.stored_at,
            )
            policy.current_version = version

            self._db.add(version)
            self._db.commit()
        except Exception:
            self._db.rollback()
            if stored is not None:
                self._file_storage.delete(stored.storage_path)
            raise

        return PersistedPolicyUpload(
            policy_id=policy.id,
            policy_version_id=version.id,
            company_id=company.id,
            policy_title=policy.title,
            version_number=version.version_number,
            description=version.description,
            uploaded_by_user_id=uploader.id,
            original_filename=validated.original_filename,
            stored_filename=stored.stored_filename,
            storage_path=stored.storage_path,
            extension=validated.extension,
            content_type=stored.content_type,
            size_bytes=stored.size_bytes,
            sha256=stored.sha256,
            uploaded_at=stored.stored_at,
        )
