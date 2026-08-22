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

from backend.domain.exceptions.policy_exceptions import CompanyNotFoundError, UserNotFoundError
from backend.models.enums import PolicyDocumentFileType, PolicyStatus, PolicyVersionStatus
from backend.models.policy import Policy
from backend.models.policy_version import PolicyVersion
from backend.services.file_storage_service import FileStorageService
from backend.services.persist_policy_upload_service import PersistPolicyUploadService
from backend.services.validate_policy_document_service import ValidatedPolicyDocument


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


def test_persist_automatically_extracts_text_for_pdf(
    db_session: Session, file_storage_service: FileStorageService, seeded_company_and_user
) -> None:
    from tests.backend.unit.test_pdf_text_extractor import make_large_pdf
    
    company, user = seeded_company_and_user
    service = PersistPolicyUploadService(db_session, file_storage_service)

    pdf_content = make_large_pdf("This is a PDF document content for auto extraction testing.")
    validated = ValidatedPolicyDocument(
        original_filename="auto-extracted.pdf",
        extension=".pdf",
        content_type="application/pdf",
        content=pdf_content,
        size_bytes=len(pdf_content),
    )

    result = service.persist(
        validated,
        company_id=company.id,
        uploaded_by_user_id=user.id,
        policy_title="Auto Extract PDF Policy",
        version_number=1,
        description="PDF upload",
    )

    # Verify that the PDF's text was automatically extracted and saved in the database
    version = db_session.get(PolicyVersion, result.policy_version_id)
    assert version is not None
    assert version.extracted_text == "This is a PDF document content for auto extraction testing."

    # Verify that the clauses were segmented and stored in the database
    from backend.models.clause import Clause
    clauses = db_session.scalars(
        select(Clause).where(Clause.policy_version_id == version.id)
    ).all()
    assert len(clauses) > 0
    assert clauses[0].text == "This is a PDF document content for auto extraction testing."

    # Verify that obligations were automatically extracted and stored
    from backend.models.obligation import Obligation
    obligations = db_session.scalars(
        select(Obligation).where(Obligation.policy_id == result.policy_id)
    ).all()
    assert len(obligations) > 0
    assert obligations[0].clause_id == clauses[0].id
    assert obligations[0].subject is not None
    assert obligations[0].action is not None
    assert obligations[0].object is not None


def test_persist_automatically_detects_conflicts(
    db_session: Session, file_storage_service: FileStorageService, seeded_company_and_user
) -> None:
    from datetime import datetime, timezone
    from tests.backend.unit.test_pdf_text_extractor import make_large_pdf
    from backend.models.policy import Policy
    from backend.models.policy_version import PolicyVersion
    from backend.models.clause import Clause
    from backend.models.obligation import Obligation
    from backend.models.conflict import Conflict
    from backend.models.enums import PolicyDocumentFileType

    company, user = seeded_company_and_user

    # 1. Pre-seed an existing policy with obligations for the same company
    existing_policy = Policy(company=company, title="Existing Policy")
    db_session.add(existing_policy)
    db_session.flush()

    existing_version = PolicyVersion(
        policy=existing_policy,
        version_number=1,
        source_file_reference="path/existing.pdf",
        file_hash="hash_existing",
        uploaded_by=user,
        original_filename="existing.pdf",
        size_bytes=512,
        file_type=PolicyDocumentFileType.PDF,
        uploaded_at=datetime.now(timezone.utc),
    )
    db_session.add(existing_version)
    db_session.flush()

    existing_policy.current_version = existing_version
    db_session.flush()

    existing_clause = Clause(
        policy_id=existing_policy.id,
        policy_version_id=existing_version.id,
        clause_number="1",
        text="Staff must observe security boundaries.",
        order_index=1
    )
    db_session.add(existing_clause)
    db_session.flush()

    existing_obligation = Obligation(
        clause_id=existing_clause.id,
        policy_id=existing_policy.id,
        subject="Staff members",
        action="observe boundaries",
        object="security boundaries",
        modality="Must",
        compliance_category="Security Awareness",
        confidence_score=0.98,
        ai_model="mock"
    )
    db_session.add(existing_obligation)
    db_session.commit()

    # 2. Trigger the automated upload pipeline for a new policy
    service = PersistPolicyUploadService(db_session, file_storage_service)
    pdf_content = make_large_pdf("This is a PDF document content for auto extraction testing.")
    validated = ValidatedPolicyDocument(
        original_filename="new-policy.pdf",
        extension=".pdf",
        content_type="application/pdf",
        content=pdf_content,
        size_bytes=len(pdf_content),
    )

    result = service.persist(
        validated,
        company_id=company.id,
        uploaded_by_user_id=user.id,
        policy_title="New Uploaded Policy",
        version_number=1,
        description="Auto conflict pipeline test",
    )

    # 3. Verify that conflicts were automatically detected and stored in the database
    conflicts = db_session.scalars(
        select(Conflict).where(Conflict.target_policy_id == result.policy_id)
    ).all()

    # Since the mock generator generates deterministic obligations, the compared obligations
    # between the newly uploaded policy and the existing one should match rules
    assert len(conflicts) > 0
    assert conflicts[0].source_policy_id == existing_policy.id
    assert conflicts[0].target_policy_id == result.policy_id


def test_persist_auto_creates_missing_company_and_user(
    db_session: Session, file_storage_service: FileStorageService
) -> None:
    from backend.models.company import Company
    from backend.models.user import User

    service = PersistPolicyUploadService(db_session, file_storage_service)
    new_company_id = uuid.uuid4()
    new_user_id = uuid.uuid4()

    result = service.persist(
        _validated_txt(),
        company_id=new_company_id,
        uploaded_by_user_id=new_user_id,
        policy_title="Auto Created Organization Policy",
        version_number=1,
        description="Testing auto create features",
        auto_create_missing=True,
    )

    # Check that company and user exist in DB
    company = db_session.get(Company, new_company_id)
    user = db_session.get(User, new_user_id)

    assert company is not None
    assert company.id == new_company_id
    assert company.name == f"Company {str(new_company_id)[:8]}"

    assert user is not None
    assert user.id == new_user_id
    assert user.company_id == new_company_id



