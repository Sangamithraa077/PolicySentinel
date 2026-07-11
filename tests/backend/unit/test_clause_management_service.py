"""Unit tests for ClauseManagementService against a fake, in-memory
ClauseRepositoryInterface -- no real database (see integration/ for
real keyword/pagination search behavior). Covers that the service
delegates search/get correctly and translates a missing clause into
ClauseNotFoundError.
"""

from __future__ import annotations

import uuid
from collections.abc import Sequence

import pytest

from backend.domain.entities.clause import PolicyClause
from backend.domain.exceptions.clause_exceptions import ClauseNotFoundError
from backend.domain.interfaces.clause_repository_interface import ClauseRepositoryInterface, StoredClause
from backend.services.clause_management_service import ClauseManagementService


class InMemoryClauseRepository(ClauseRepositoryInterface):
    def __init__(self, clauses: list[StoredClause]) -> None:
        self.clauses = clauses
        self.search_calls: list[dict[str, object]] = []

    def save_all(
        self,
        clauses: Sequence[PolicyClause],
        *,
        policy_id: uuid.UUID,
        policy_version_id: uuid.UUID,
    ) -> None:
        raise NotImplementedError("not exercised here -- see test_store_segmented_clauses_service")

    def list_for_policy_version(self, policy_version_id: uuid.UUID) -> list[StoredClause]:
        raise NotImplementedError("not exercised here")

    def get(self, clause_id: uuid.UUID) -> StoredClause | None:
        return next((c for c in self.clauses if c.id == clause_id), None)

    def search(
        self,
        *,
        policy_id: uuid.UUID | None = None,
        policy_version_id: uuid.UUID | None = None,
        keyword: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[StoredClause], int]:
        self.search_calls.append(
            {
                "policy_id": policy_id,
                "policy_version_id": policy_version_id,
                "keyword": keyword,
                "limit": limit,
                "offset": offset,
            }
        )
        return self.clauses, len(self.clauses)

    def delete_for_policy_version(self, policy_version_id: uuid.UUID) -> None:
        raise NotImplementedError("not exercised here")


def make_stored_clause(**overrides: object) -> StoredClause:
    defaults: dict[str, object] = {
        "id": uuid.uuid4(),
        "policy_id": uuid.uuid4(),
        "policy_version_id": uuid.uuid4(),
        "parent_clause_id": None,
        "clause_number": "1",
        "heading": "Introduction",
        "text": "Introduction",
        "order_index": 0,
    }
    defaults.update(overrides)
    return StoredClause(**defaults)  # type: ignore[arg-type]


@pytest.mark.file_retrieval
def test_search_forwards_all_filters_to_the_repository() -> None:
    repository = InMemoryClauseRepository([])
    service = ClauseManagementService(repository)
    policy_id, version_id = uuid.uuid4(), uuid.uuid4()

    service.search(
        policy_id=policy_id, policy_version_id=version_id, keyword="retention", limit=10, offset=5
    )

    assert repository.search_calls == [
        {
            "policy_id": policy_id,
            "policy_version_id": version_id,
            "keyword": "retention",
            "limit": 10,
            "offset": 5,
        }
    ]


@pytest.mark.file_retrieval
def test_search_returns_the_repositorys_page_and_total() -> None:
    clauses = [make_stored_clause(), make_stored_clause()]
    repository = InMemoryClauseRepository(clauses)
    service = ClauseManagementService(repository)

    items, total = service.search()

    assert items == clauses
    assert total == 2


@pytest.mark.file_retrieval
def test_get_clause_returns_the_matching_clause() -> None:
    clause = make_stored_clause()
    repository = InMemoryClauseRepository([clause])
    service = ClauseManagementService(repository)

    result = service.get_clause(clause.id)

    assert result == clause


@pytest.mark.error_handling
def test_get_clause_raises_not_found_for_unknown_id() -> None:
    repository = InMemoryClauseRepository([])
    service = ClauseManagementService(repository)

    with pytest.raises(ClauseNotFoundError):
        service.get_clause(uuid.uuid4())
