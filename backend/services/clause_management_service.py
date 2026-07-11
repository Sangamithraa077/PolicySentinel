"""Use case: read, search, and fetch details of clauses already stored
for a policy (or a specific policy version).

Thin orchestration over `domain/interfaces/clause_repository_interface.py`
— no document parsing, no segmentation, no AI.

Clause deletion is deliberately not exposed here as its own operation:
per the storage task, clauses are removed only as a cascading side
effect of their owning policy version being removed, which is
`services/policy_management_service.py::delete_policy`'s job (it calls
the same `ClauseRepositoryInterface.delete_for_policy_version` this
service reads through) — there is no standalone "delete this clause"
use case.
"""

from __future__ import annotations

import uuid

from backend.domain.exceptions.clause_exceptions import ClauseNotFoundError
from backend.domain.interfaces.clause_repository_interface import (
    ClauseRepositoryInterface,
    StoredClause,
)


class ClauseManagementService:
    def __init__(self, clause_repository: ClauseRepositoryInterface) -> None:
        self._clause_repository = clause_repository

    def search(
        self,
        *,
        policy_id: uuid.UUID | None = None,
        policy_version_id: uuid.UUID | None = None,
        keyword: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[StoredClause], int]:
        return self._clause_repository.search(
            policy_id=policy_id,
            policy_version_id=policy_version_id,
            keyword=keyword,
            limit=limit,
            offset=offset,
        )

    def get_clause(self, clause_id: uuid.UUID) -> StoredClause:
        clause = self._clause_repository.get(clause_id)
        if clause is None:
            raise ClauseNotFoundError(f"Clause '{clause_id}' does not exist.")
        return clause
