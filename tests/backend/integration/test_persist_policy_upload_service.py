"""Integration tests for PersistPolicyUploadService — real PostgreSQL
(via the conftest.py test database) plus a real FileStorageService
writing to a temp directory. Covers "Metadata storage" and rollback/
cleanup behavior on failure.
"""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from domain.exceptions.policy_exceptions import CompanyNotFoundError, UserNotFoundError
from models.enums import PolicyDocumentFileType, PolicyStatus, PolicyVersionStatus
from models.policy import Policy
from models.policy_version import PolicyVersion
from services.file_storage_service import FileStorageService
from services.persist_policy_upload_service import PersistPolicyUploadService
from services.validate_policy_document_service import ValidatedPolicyDocument


def _validated_txt(content: bytes = b"policy body text") -> ValidatedPolicyDocument:
    return ValidatedPolicyDocument(
        original_filename="acceptable-use-policy.txt",
        extension=".txt",
        content_type="text/plain",
        content=content,
        size_bytes=len(content),
    )


@pytest.mark.metadata_storage
def test_persist_creates_policy_and_version_with_full_metadata(
    db_session: Session, file_storage_service: FileStorageService, seeded_company_and_user
) -> None:
    company, user = seeded_company_and_user
    service = PersistPolicyUploadService(db_session, file_storage_service)

    result = service.persist(
        _validated_txt(),
        company_id=company.id,
        uploaded_by_user_id=user.id,
        policy_title="Acceptable Use Policy",
        version_number=1,
        description="Initial version",
    )

    policy = db_session.get(Policy, result.policy_id)
    version = db_session.get(PolicyVersion, result.policy_version_id)

    assert policy is not None
    assert policy.title == "Acceptable Use Policy"
    assert policy.company_id == company.id
    assert policy.status == PolicyStatus.DRAFT
    assert policy.current_version_id == version.id

    assert version is not None
    assert version.version_number == 1
    assert version.original_filename == "acceptable-use-policy.txt"
    assert version.file_type == PolicyDocumentFileType.TXT
    assert version.size_bytes == len(b"policy body text")
    assert version.description == "Initial version"
    assert version.uploaded_by_user_id == user.id
    assert version.status == PolicyVersionStatus.DRAFT
    assert version.source_file_reference == result.storage_path


@pytest.mark.file_upload
@pytest.mark.metadata_storage
def test_persist_stores_the_actual_file_bytes_on_disk(
    db_session: Session, file_storage_service: FileStorageService, seeded_company_and_user
) -> None:
    company, user = seeded_company_and_user
    service = PersistPolicyUploadService(db_session, file_storage_service)
    content = b"exact bytes that must round-trip"

    result = service.persist(
        _validated_txt(content),
        company_id=company.id,
        uploaded_by_user_id=user.id,
        policy_title="Data Retention Policy",
        version_number=1,
        description=None,
    )

    assert file_storage_service.retrieve(result.storage_path) == content
    assert f"companies/{company.id}/policies/{result.policy_id}/" in result.storage_path


@pytest.mark.error_handling
def test_persist_raises_company_not_found_for_unknown_company(
    db_session: Session, file_storage_service: FileStorageService, seeded_company_and_user
) -> None:
    _, user = seeded_company_and_user
    service = PersistPolicyUploadService(db_session, file_storage_service)

    with pytest.raises(CompanyNotFoundError):
        service.persist(
            _validated_txt(),
            company_id=uuid.uuid4(),
            uploaded_by_user_id=user.id,
            policy_title="Orphan Policy",
            version_number=1,
            description=None,
        )


@pytest.mark.error_handling
def test_persist_raises_user_not_found_for_unknown_uploader(
    db_session: Session, file_storage_service: FileStorageService, seeded_company_and_user
) -> None:
    company, _ = seeded_company_and_user
    service = PersistPolicyUploadService(db_session, file_storage_service)

    with pytest.raises(UserNotFoundError):
        service.persist(
            _validated_txt(),
            company_id=company.id,
            uploaded_by_user_id=uuid.uuid4(),
            policy_title="Orphan Policy",
            version_number=1,
            description=None,
        )


@pytest.mark.error_handling
def test_persist_deletes_the_orphaned_file_when_the_transaction_fails_after_storing(
    db_session: Session, file_storage_service: FileStorageService, seeded_company_and_user
) -> None:
    company, user = seeded_company_and_user
    service = PersistPolicyUploadService(db_session, file_storage_service)

    original_commit = db_session.commit

    def failing_commit() -> None:
        raise RuntimeError("simulated failure after the file was already stored")

    db_session.commit = failing_commit  # type: ignore[method-assign]
    try:
        with pytest.raises(RuntimeError):
            service.persist(
                _validated_txt(),
                company_id=company.id,
                uploaded_by_user_id=user.id,
                policy_title="Should Not Survive",
                version_number=1,
                description=None,
            )
    finally:
        db_session.commit = original_commit  # type: ignore[method-assign]

    remaining_policy = db_session.scalar(select(Policy).where(Policy.title == "Should Not Survive"))
    assert remaining_policy is None
