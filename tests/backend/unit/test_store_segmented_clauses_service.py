"""Unit tests for StoreSegmentedClausesService against a fake, in-memory
ClauseRepositoryInterface -- no real database (see integration/ for
that). Covers that the service delegates storage and read-back
correctly without adding any logic of its own.
"""

from __future__ import annotations

import uuid
from collections.abc import Sequence

import pytest

from backend.domain.entities.clause import ClauseMarkerType, PolicyClause
from backend.domain.interfaces.clause_repository_interface import ClauseRepositoryInterface, StoredClause
from backend.services.store_segmented_clauses_service import StoreSegmentedClausesService


class InMemoryClauseRepository(ClauseRepositoryInterface):
    def __init__(self) -> None:
        self.saved: list[StoredClause] = []
        self.save_all_calls: list[tuple[uuid.UUID, uuid.UUID]] = []

    def save_all(
        self,
        clauses: Sequence[PolicyClause],
        *,
        policy_id: uuid.UUID,
        policy_version_id: uuid.UUID,
    ) -> None:
        self.save_all_calls.append((policy_id, policy_version_id))
        self.saved = [
            StoredClause(
                id=c.id,
                policy_id=policy_id,
                policy_version_id=policy_version_id,
                parent_clause_id=c.parent_id,
                clause_number=c.clause_number,
                heading=c.heading,
                text=c.text,
                order_index=c.order_index,
            )
            for c in clauses
        ]

    def list_for_policy_version(self, policy_version_id: uuid.UUID) -> list[StoredClause]:
        return [c for c in self.saved if c.policy_version_id == policy_version_id]

    def get(self, clause_id: uuid.UUID) -> StoredClause | None:
        return next((c for c in self.saved if c.id == clause_id), None)

    def search(
        self,
        *,
        policy_id: uuid.UUID | None = None,
        policy_version_id: uuid.UUID | None = None,
        keyword: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[StoredClause], int]:
        raise NotImplementedError("not exercised here -- see test_clause_management_service.py")

    def delete_for_policy_version(self, policy_version_id: uuid.UUID) -> None:
        self.saved = [c for c in self.saved if c.policy_version_id != policy_version_id]


def make_clause(order_index: int = 0, parent_id: uuid.UUID | None = None) -> PolicyClause:
    return PolicyClause(
        id=uuid.uuid4(),
        parent_id=parent_id,
        order_index=order_index,
        level=1,
        marker_type=ClauseMarkerType.HEADING,
        clause_number="1",
        heading="Introduction",
        text="Introduction",
    )


@pytest.mark.metadata_storage
def test_store_saves_clauses_with_given_policy_and_version_ids() -> None:
    repository = InMemoryClauseRepository()
    service = StoreSegmentedClausesService(repository)
    policy_id, policy_version_id = uuid.uuid4(), uuid.uuid4()
    clauses = [make_clause()]

    service.store(clauses, policy_id=policy_id, policy_version_id=policy_version_id)

    assert repository.save_all_calls == [(policy_id, policy_version_id)]


@pytest.mark.metadata_storage
def test_store_returns_the_repositorys_read_back_result() -> None:
    repository = InMemoryClauseRepository()
    service = StoreSegmentedClausesService(repository)
    policy_id, policy_version_id = uuid.uuid4(), uuid.uuid4()
    clause = make_clause()

    result = service.store([clause], policy_id=policy_id, policy_version_id=policy_version_id)

    assert len(result) == 1
    assert result[0].id == clause.id
    assert result[0].policy_id == policy_id
    assert result[0].policy_version_id == policy_version_id


@pytest.mark.metadata_storage
@pytest.mark.clause_ordering
def test_store_preserves_order_and_parent_ids_across_multiple_clauses() -> None:
    repository = InMemoryClauseRepository()
    service = StoreSegmentedClausesService(repository)
    policy_id, policy_version_id = uuid.uuid4(), uuid.uuid4()
    heading = make_clause(order_index=0)
    child = make_clause(order_index=1, parent_id=heading.id)

    result = service.store(
        [heading, child], policy_id=policy_id, policy_version_id=policy_version_id
    )

    assert [c.order_index for c in result] == [0, 1]
    assert result[1].parent_clause_id == heading.id
