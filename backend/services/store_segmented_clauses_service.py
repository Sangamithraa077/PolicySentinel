"""Use case: persist an already-segmented clause tree for one policy
version.

Deliberately thin — `services/clause_segmentation_service.py` decides
the structure (headings, hierarchy, numbering); this service only
attaches the ownership ids (`policy_id`, `policy_version_id`)
segmentation itself has no reason to know about and hands the list to
`domain/interfaces/clause_repository_interface.py`. No classification,
no obligation extraction: clauses are stored exactly as segmented.
"""

from __future__ import annotations

import uuid
from collections.abc import Sequence

from backend.domain.entities.clause import PolicyClause
from backend.domain.interfaces.clause_repository_interface import (
    ClauseRepositoryInterface,
    StoredClause,
)


class StoreSegmentedClausesService:
    def __init__(self, clause_repository: ClauseRepositoryInterface) -> None:
        self._clause_repository = clause_repository

    def store(
        self,
        clauses: Sequence[PolicyClause],
        *,
        policy_id: uuid.UUID,
        policy_version_id: uuid.UUID,
    ) -> list[StoredClause]:
        self._clause_repository.save_all(
            clauses, policy_id=policy_id, policy_version_id=policy_version_id
        )
        return self._clause_repository.list_for_policy_version(policy_version_id)
