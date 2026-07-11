"""Use case: list, retrieve, download, and soft-delete uploaded policies.

Read-only listing/detail return ORM objects directly (the request's
session is still open when `schemas/policies.py` serializes them via
Pydantic's `from_attributes`) rather than mirroring every field into a
parallel dataclass — appropriate for straightforward reads, unlike the
write-side services in this module, which need that separation for
their cleanup-on-failure logic.

Purely CRUD over the Policy/PolicyVersion rows the upload flow already
created — no document parsing, no AI.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import ColumnElement, func, select, update
from sqlalchemy.orm import Session, selectinload

from domain.exceptions.policy_exceptions import PolicyNotFoundError, PolicyVersionNotFoundError
from models.enums import PolicyDocumentFileType, PolicyStatus
from models.policy import Policy
from models.policy_version import PolicyVersion
from services.file_storage_service import FileStorageService

_CONTENT_TYPES: dict[PolicyDocumentFileType, str] = {
    PolicyDocumentFileType.TXT: "text/plain",
    PolicyDocumentFileType.MD: "text/markdown",
    PolicyDocumentFileType.PDF: "application/pdf",
    PolicyDocumentFileType.DOCX: (
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    ),
}


@dataclass(frozen=True)
class PolicyDownload:
    filename: str
    content_type: str
    content: bytes


class PolicyManagementService:
    def __init__(self, db: Session, file_storage: FileStorageService) -> None:
        self._db = db
        self._file_storage = file_storage

    def list_policies(
        self,
        *,
        company_id: uuid.UUID | None = None,
        status: PolicyStatus | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[Policy], int]:
        conditions: list[ColumnElement[bool]] = [Policy.deleted_at.is_(None)]
        if company_id is not None:
            conditions.append(Policy.company_id == company_id)
        if status is not None:
            conditions.append(Policy.status == status)

        total = self._db.scalar(select(func.count()).select_from(Policy).where(*conditions)) or 0

        items = list(
            self._db.scalars(
                select(Policy)
                .where(*conditions)
                .options(selectinload(Policy.current_version))
                .order_by(Policy.created_at.desc())
                .limit(limit)
                .offset(offset)
            )
        )
        return items, total

    def get_policy(self, policy_id: uuid.UUID) -> tuple[Policy, list[PolicyVersion]]:
        """Returns the policy plus its non-deleted versions, newest first.

        Versions are fetched with a separate query rather than through
        `policy.versions` — reassigning/filtering that relationship
        collection in place would make SQLAlchemy think versions were
        being removed from the policy.
        """
        policy = self._db.scalar(
            select(Policy)
            .where(Policy.id == policy_id, Policy.deleted_at.is_(None))
            .options(selectinload(Policy.current_version))
        )
        if policy is None:
            raise PolicyNotFoundError(f"Policy '{policy_id}' does not exist.")

        versions = list(
            self._db.scalars(
                select(PolicyVersion)
                .where(PolicyVersion.policy_id == policy_id, PolicyVersion.deleted_at.is_(None))
                .order_by(PolicyVersion.version_number.desc())
            )
        )
        return policy, versions

    def get_download(
        self, policy_id: uuid.UUID, version_number: int | None = None
    ) -> PolicyDownload:
        policy = self._db.scalar(
            select(Policy).where(Policy.id == policy_id, Policy.deleted_at.is_(None))
        )
        if policy is None:
            raise PolicyNotFoundError(f"Policy '{policy_id}' does not exist.")

        if version_number is None:
            version = (
                self._db.scalar(
                    select(PolicyVersion).where(
                        PolicyVersion.id == policy.current_version_id,
                        PolicyVersion.deleted_at.is_(None),
                    )
                )
                if policy.current_version_id is not None
                else None
            )
            missing_label = "a current version"
        else:
            version = self._db.scalar(
                select(PolicyVersion).where(
                    PolicyVersion.policy_id == policy_id,
                    PolicyVersion.version_number == version_number,
                    PolicyVersion.deleted_at.is_(None),
                )
            )
            missing_label = f"version {version_number}"

        if version is None:
            raise PolicyVersionNotFoundError(f"Policy '{policy_id}' has no {missing_label}.")

        content = self._file_storage.retrieve(version.source_file_reference)
        content_type = _CONTENT_TYPES.get(version.file_type, "application/octet-stream")

        return PolicyDownload(
            filename=version.original_filename, content_type=content_type, content=content
        )

    def delete_policy(self, policy_id: uuid.UUID) -> None:
        """Soft-deletes the policy and, for consistency, every one of its
        non-deleted versions — a policy that's gone shouldn't leave
        versions behind that still look active. The underlying files are
        left in storage; soft delete means recoverable, not gone."""
        policy = self._db.scalar(
            select(Policy).where(Policy.id == policy_id, Policy.deleted_at.is_(None))
        )
        if policy is None:
            raise PolicyNotFoundError(f"Policy '{policy_id}' does not exist.")

        now = datetime.now(UTC)
        policy.deleted_at = now
        self._db.execute(
            update(PolicyVersion)
            .where(PolicyVersion.policy_id == policy_id, PolicyVersion.deleted_at.is_(None))
            .values(deleted_at=now)
        )
        self._db.commit()
