"""Integration tests for PolicyManagementService — real PostgreSQL plus
a real FileStorageService. Covers "File retrieval" and "File deletion"
(soft-delete) verification categories.
"""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy.orm import Session

from backend.domain.exceptions.policy_exceptions import PolicyNotFoundError, PolicyVersionNotFoundError
from backend.models.clause import Clause
from backend.models.policy import Policy
from backend.models.policy_version import PolicyVersion
from backend.repositories.clause_repository import ClauseRepository
from backend.services.clause_segmentation_service import ClauseSegmentationService
from backend.services.file_storage_service import FileStorageService
from backend.services.persist_policy_upload_service import PersistPolicyUploadService
from backend.services.policy_management_service import PolicyManagementService
from backend.services.store_segmented_clauses_service import StoreSegmentedClausesService
from backend.services.validate_policy_document_service import ValidatedPolicyDocument


def _upload_a_policy(
    db_session: Session,
    file_storage_service: FileStorageService,
    seeded_company_and_user,
    *,
    title: str,
    content: bytes = b"policy body",
) -> uuid.UUID:
    company, user = seeded_company_and_user
    persist_service = PersistPolicyUploadService(db_session, file_storage_service)
    validated = ValidatedPolicyDocument(
        original_filename=f"{title}.txt",
        extension=".txt",
        content_type="text/plain",
        content=content,
        size_bytes=len(content),
    )
    result = persist_service.persist(
        validated,
        company_id=company.id,
        uploaded_by_user_id=user.id,
        policy_title=title,
        version_number=1,
        description=None,
    )
    return result.policy_id


def _make_service(
    db_session: Session, file_storage_service: FileStorageService
) -> PolicyManagementService:
    return PolicyManagementService(db_session, file_storage_service, ClauseRepository(db_session))


@pytest.mark.file_retrieval
def test_list_policies_returns_only_non_deleted_policies_for_the_company(
    db_session: Session, file_storage_service: FileStorageService, seeded_company_and_user
) -> None:
    company, _ = seeded_company_and_user
    _upload_a_policy(db_session, file_storage_service, seeded_company_and_user, title="Policy A")
    _upload_a_policy(db_session, file_storage_service, seeded_company_and_user, title="Policy B")
    deleted_policy_id = _upload_a_policy(
        db_session, file_storage_service, seeded_company_and_user, title="Policy C (deleted)"
    )
    service = _make_service(db_session, file_storage_service)
    service.delete_policy(deleted_policy_id)

    items, total = service.list_policies(company_id=company.id)

    assert total == 2
    assert {p.title for p in items} == {"Policy A", "Policy B"}


@pytest.mark.file_retrieval
def test_get_policy_returns_details_and_versions(
    db_session: Session, file_storage_service: FileStorageService, seeded_company_and_user
) -> None:
    policy_id = _upload_a_policy(
        db_session, file_storage_service, seeded_company_and_user, title="Data Handling Policy"
    )
    service = _make_service(db_session, file_storage_service)

    policy, versions = service.get_policy(policy_id)

    assert policy.title == "Data Handling Policy"
    assert len(versions) == 1
    assert versions[0].version_number == 1


@pytest.mark.error_handling
def test_get_policy_raises_not_found_for_unknown_id(
    db_session: Session, file_storage_service: FileStorageService
) -> None:
    service = _make_service(db_session, file_storage_service)

    with pytest.raises(PolicyNotFoundError):
        service.get_policy(uuid.uuid4())


@pytest.mark.file_retrieval
def test_get_download_returns_the_original_bytes_and_filename(
    db_session: Session, file_storage_service: FileStorageService, seeded_company_and_user
) -> None:
    policy_id = _upload_a_policy(
        db_session,
        file_storage_service,
        seeded_company_and_user,
        title="Incident Response Policy",
        content=b"specific bytes to verify",
    )
    service = _make_service(db_session, file_storage_service)

    download = service.get_download(policy_id)

    assert download.content == b"specific bytes to verify"
    assert download.filename == "Incident Response Policy.txt"
    assert download.content_type == "text/plain"


@pytest.mark.error_handling
def test_get_download_raises_policy_not_found_for_unknown_id(
    db_session: Session, file_storage_service: FileStorageService
) -> None:
    service = _make_service(db_session, file_storage_service)

    with pytest.raises(PolicyNotFoundError):
        service.get_download(uuid.uuid4())


@pytest.mark.error_handling
def test_get_download_raises_version_not_found_for_unknown_version_number(
    db_session: Session, file_storage_service: FileStorageService, seeded_company_and_user
) -> None:
    policy_id = _upload_a_policy(
        db_session, file_storage_service, seeded_company_and_user, title="Vendor Risk Policy"
    )
    service = _make_service(db_session, file_storage_service)

    with pytest.raises(PolicyVersionNotFoundError):
        service.get_download(policy_id, version_number=99)


@pytest.mark.file_deletion
def test_delete_policy_soft_deletes_policy_and_its_versions(
    db_session: Session, file_storage_service: FileStorageService, seeded_company_and_user
) -> None:
    policy_id = _upload_a_policy(
        db_session, file_storage_service, seeded_company_and_user, title="Retiring Policy"
    )
    service = _make_service(db_session, file_storage_service)

    service.delete_policy(policy_id)

    db_session.expire_all()
    policy = db_session.get(Policy, policy_id)
    versions = db_session.query(PolicyVersion).filter(PolicyVersion.policy_id == policy_id).all()

    assert policy.deleted_at is not None
    assert all(v.deleted_at is not None for v in versions)

    with pytest.raises(PolicyNotFoundError):
        service.get_policy(policy_id)


@pytest.mark.file_deletion
def test_delete_policy_leaves_the_underlying_file_on_disk(
    db_session: Session, file_storage_service: FileStorageService, seeded_company_and_user
) -> None:
    # Soft delete means recoverable, not gone -- the stored file itself is
    # untouched even though the policy no longer appears in listings.
    policy_id = _upload_a_policy(
        db_session, file_storage_service, seeded_company_and_user, title="Policy To Soft Delete"
    )
    service = _make_service(db_session, file_storage_service)
    db_session.expire_all()
    version = (
        db_session.query(PolicyVersion).filter(PolicyVersion.policy_id == policy_id).one()
    )
    storage_path = version.source_file_reference

    service.delete_policy(policy_id)

    assert file_storage_service.retrieve(storage_path) is not None


@pytest.mark.error_handling
def test_delete_policy_raises_not_found_for_unknown_id(
    db_session: Session, file_storage_service: FileStorageService
) -> None:
    service = _make_service(db_session, file_storage_service)

    with pytest.raises(PolicyNotFoundError):
        service.delete_policy(uuid.uuid4())


@pytest.mark.file_deletion
def test_delete_policy_soft_deletes_the_clauses_of_its_removed_version(
    db_session: Session, file_storage_service: FileStorageService, seeded_company_and_user
) -> None:
    policy_id = _upload_a_policy(
        db_session, file_storage_service, seeded_company_and_user, title="Policy With Clauses"
    )
    version = db_session.query(PolicyVersion).filter(PolicyVersion.policy_id == policy_id).one()
    clauses = ClauseSegmentationService().segment("1. Introduction\n\nBody text.")
    StoreSegmentedClausesService(ClauseRepository(db_session)).store(
        clauses, policy_id=policy_id, policy_version_id=version.id
    )
    service = _make_service(db_session, file_storage_service)

    service.delete_policy(policy_id)

    db_session.expire_all()
    stored_clause = db_session.get(Clause, clauses[0].id)
    assert stored_clause is not None
    assert stored_clause.deleted_at is not None
    assert ClauseRepository(db_session).list_for_policy_version(version.id) == []
