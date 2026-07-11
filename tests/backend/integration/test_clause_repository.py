"""Integration tests for ClauseRepository / StoreSegmentedClausesService
-- real PostgreSQL (via the conftest.py test database), which also
exercises the `d7a145d9bdc8_add_clause_hierarchy_and_ownership`
Alembic migration this repository depends on (policy_id,
parent_clause_id, nullable clause_number/clause_type, the
'rule_based' extraction_method value). Covers "Metadata storage" for
the clause storage module: round-tripping id/policy/version/parent/
number/heading/text/order through the database, plus the self-
referential foreign key ordering that makes hierarchy persistence work
at all.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

import pytest
from sqlalchemy.orm import Session

from backend.domain.exceptions.clause_exceptions import ClauseStorageError
from backend.models.clause import Clause
from backend.models.enums import ExtractionMethod, PolicyDocumentFileType, PolicyStatus, PolicyVersionStatus
from backend.models.policy import Policy
from backend.models.policy_version import PolicyVersion
from backend.repositories.clause_repository import ClauseRepository
from backend.services.clause_segmentation_service import ClauseSegmentationService
from backend.services.store_segmented_clauses_service import StoreSegmentedClausesService


@pytest.fixture
def seeded_policy_version(db_session: Session, seeded_company_and_user):
    company, user = seeded_company_and_user
    policy = Policy(
        company=company, owning_department=None, title="Test Policy", status=PolicyStatus.DRAFT
    )
    db_session.add(policy)
    db_session.flush()

    version = PolicyVersion(
        policy=policy,
        version_number=1,
        source_file_reference="companies/x/policies/y/z.txt",
        file_hash="deadbeef",
        uploaded_by=user,
        status=PolicyVersionStatus.DRAFT,
        original_filename="policy.txt",
        size_bytes=100,
        file_type=PolicyDocumentFileType.TXT,
        description=None,
        uploaded_at=datetime.now(UTC),
    )
    db_session.add(version)
    db_session.commit()
    return policy, version


@pytest.mark.metadata_storage
def test_store_persists_full_hierarchy_and_round_trips_all_required_fields(
    db_session: Session, seeded_policy_version
) -> None:
    policy, version = seeded_policy_version
    text = (
        "1. Introduction\n\nIntro text.\n\n"
        "1.1 Purpose\n\nPurpose text.\n\n"
        "(a) First requirement\n\n"
        "- supporting detail"
    )
    clauses = ClauseSegmentationService().segment(text)
    service = StoreSegmentedClausesService(ClauseRepository(db_session))

    stored = service.store(clauses, policy_id=policy.id, policy_version_id=version.id)

    assert len(stored) == len(clauses) == 4
    assert {s.id for s in stored} == {c.id for c in clauses}

    heading = next(s for s in stored if s.clause_number == "1")
    subheading = next(s for s in stored if s.clause_number == "1.1")
    item = next(s for s in stored if s.clause_number == "(a)")
    bullet = next(s for s in stored if s.clause_number is None)

    assert heading.policy_id == policy.id
    assert heading.policy_version_id == version.id
    assert heading.parent_clause_id is None
    assert heading.heading == "Introduction"
    assert heading.text == "Introduction\n\nIntro text."
    assert heading.order_index == 0

    assert subheading.parent_clause_id == heading.id
    assert item.parent_clause_id == subheading.id
    assert bullet.parent_clause_id == item.id
    assert bullet.text == "supporting detail"


@pytest.mark.metadata_storage
def test_stored_clauses_are_unclassified_and_rule_based(
    db_session: Session, seeded_policy_version
) -> None:
    policy, version = seeded_policy_version
    clauses = ClauseSegmentationService().segment("1. Introduction\n\nBody.")
    service = StoreSegmentedClausesService(ClauseRepository(db_session))

    service.store(clauses, policy_id=policy.id, policy_version_id=version.id)

    record = db_session.get(Clause, clauses[0].id)
    assert record is not None
    assert record.clause_type is None
    assert record.extracted_by == ExtractionMethod.RULE_BASED


@pytest.mark.metadata_storage
def test_clause_with_no_content_falls_back_to_non_blank_text(
    db_session: Session, seeded_policy_version
) -> None:
    policy, version = seeded_policy_version
    # A lone "Section 1" heading with nothing else in the document --
    # segmentation gives it empty text (no trailing title, no body).
    clauses = ClauseSegmentationService().segment("Section 1")
    assert clauses[0].text == ""
    service = StoreSegmentedClausesService(ClauseRepository(db_session))

    stored = service.store(clauses, policy_id=policy.id, policy_version_id=version.id)

    assert stored[0].text == "Section 1"  # falls back to clause_number, never blank


@pytest.mark.file_retrieval
@pytest.mark.clause_ordering
def test_list_for_policy_version_returns_clauses_ordered_by_sequence(
    db_session: Session, seeded_policy_version
) -> None:
    policy, version = seeded_policy_version
    clauses = ClauseSegmentationService().segment("1. First\n\n2. Second\n\n3. Third")
    repository = ClauseRepository(db_session)
    repository.save_all(clauses, policy_id=policy.id, policy_version_id=version.id)

    result = repository.list_for_policy_version(version.id)

    assert [c.clause_number for c in result] == ["1", "2", "3"]
    assert [c.order_index for c in result] == [0, 1, 2]


@pytest.mark.error_handling
def test_save_all_raises_clause_storage_error_for_unknown_policy_version(
    db_session: Session, seeded_policy_version
) -> None:
    policy, _ = seeded_policy_version
    clauses = ClauseSegmentationService().segment("1. Introduction")
    repository = ClauseRepository(db_session)

    with pytest.raises(ClauseStorageError):
        repository.save_all(clauses, policy_id=policy.id, policy_version_id=uuid.uuid4())


@pytest.mark.file_retrieval
def test_get_returns_the_matching_clause(db_session: Session, seeded_policy_version) -> None:
    policy, version = seeded_policy_version
    clauses = ClauseSegmentationService().segment("1. Introduction\n\nBody.")
    repository = ClauseRepository(db_session)
    repository.save_all(clauses, policy_id=policy.id, policy_version_id=version.id)

    result = repository.get(clauses[0].id)

    assert result is not None
    assert result.id == clauses[0].id
    assert result.clause_number == "1"


@pytest.mark.file_retrieval
def test_get_returns_none_for_unknown_clause(db_session: Session) -> None:
    repository = ClauseRepository(db_session)

    assert repository.get(uuid.uuid4()) is None


@pytest.mark.file_retrieval
def test_search_filters_by_policy_id(db_session: Session, seeded_policy_version) -> None:
    policy, version = seeded_policy_version
    clauses = ClauseSegmentationService().segment("1. Introduction")
    repository = ClauseRepository(db_session)
    repository.save_all(clauses, policy_id=policy.id, policy_version_id=version.id)

    matching, total = repository.search(policy_id=policy.id)
    non_matching, non_matching_total = repository.search(policy_id=uuid.uuid4())

    assert total == 1
    assert matching[0].clause_number == "1"
    assert non_matching_total == 0
    assert non_matching == []


@pytest.mark.file_retrieval
def test_search_matches_keyword_case_insensitively_in_text_or_heading(
    db_session: Session, seeded_policy_version
) -> None:
    policy, version = seeded_policy_version
    clauses = ClauseSegmentationService().segment(
        "1. Data Retention\n\nRecords are KEPT for seven years.\n\n2. Access\n\nRestricted."
    )
    repository = ClauseRepository(db_session)
    repository.save_all(clauses, policy_id=policy.id, policy_version_id=version.id)

    by_text, text_total = repository.search(policy_id=policy.id, keyword="kept")
    by_heading, heading_total = repository.search(policy_id=policy.id, keyword="retention")

    assert text_total == 1
    assert by_text[0].clause_number == "1"
    assert heading_total == 1
    assert by_heading[0].clause_number == "1"


@pytest.mark.file_retrieval
def test_search_keyword_with_wildcard_characters_is_treated_literally(
    db_session: Session, seeded_policy_version
) -> None:
    # Without escaping, ILIKE '%50%%' would match "50" followed by
    # anything (the second '%' is a wildcard, not a literal percent).
    policy, version = seeded_policy_version
    clauses = ClauseSegmentationService().segment("1. Discount\n\nUp to 50% off applies.")
    repository = ClauseRepository(db_session)
    repository.save_all(clauses, policy_id=policy.id, policy_version_id=version.id)

    literal_match, literal_total = repository.search(policy_id=policy.id, keyword="50%")
    no_match, no_match_total = repository.search(policy_id=policy.id, keyword="50X")

    assert literal_total == 1
    assert literal_match[0].clause_number == "1"
    assert no_match_total == 0
    assert no_match == []


@pytest.mark.file_retrieval
@pytest.mark.clause_ordering
def test_search_paginates_with_limit_and_offset(
    db_session: Session, seeded_policy_version
) -> None:
    policy, version = seeded_policy_version
    clauses = ClauseSegmentationService().segment("1. First\n\n2. Second\n\n3. Third")
    repository = ClauseRepository(db_session)
    repository.save_all(clauses, policy_id=policy.id, policy_version_id=version.id)

    page, total = repository.search(policy_id=policy.id, limit=2, offset=1)

    assert total == 3
    assert [c.clause_number for c in page] == ["2", "3"]


@pytest.mark.file_deletion
def test_delete_for_policy_version_soft_deletes_without_committing(
    db_session: Session, seeded_policy_version
) -> None:
    policy, version = seeded_policy_version
    clauses = ClauseSegmentationService().segment("1. Introduction")
    repository = ClauseRepository(db_session)
    repository.save_all(clauses, policy_id=policy.id, policy_version_id=version.id)

    repository.delete_for_policy_version(version.id)
    db_session.rollback()

    # Rolling back an uncommitted delete_for_policy_version leaves the
    # clause intact -- proves the method doesn't commit on its own.
    assert repository.get(clauses[0].id) is not None

    repository.delete_for_policy_version(version.id)
    db_session.commit()

    assert repository.get(clauses[0].id) is None
    assert repository.list_for_policy_version(version.id) == []
