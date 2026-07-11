"""Port for persisting, retrieving, searching, and removing a policy's
clauses.

`services/store_segmented_clauses_service.py` and
`services/clause_management_service.py` depend only on this interface;
the concrete implementation (`repositories/clause_repository.py`,
SQLAlchemy/Postgres today) can change without touching either service's
logic.

`save_all` takes `domain.entities.clause.PolicyClause` — the full
structural shape `services/clause_segmentation_service.py` produces,
including `level`/`marker_type`, which exist only to get the hierarchy
right at write time. Reads return `StoredClause`, reflecting exactly
what the `clauses` table persists (see `models/clause.py` and the
storage task's own field list) — `level`/`marker_type` aren't columns,
so `StoredClause` doesn't claim to have them back.
"""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass

from backend.domain.entities.clause import PolicyClause


@dataclass(frozen=True)
class StoredClause:
    id: uuid.UUID
    policy_id: uuid.UUID
    policy_version_id: uuid.UUID
    parent_clause_id: uuid.UUID | None
    clause_number: str | None
    heading: str | None
    text: str
    order_index: int


class ClauseRepositoryInterface(ABC):
    @abstractmethod
    def save_all(
        self,
        clauses: Sequence[PolicyClause],
        *,
        policy_id: uuid.UUID,
        policy_version_id: uuid.UUID,
    ) -> None:
        """Persist `clauses` for one policy version.

        Each clause's own `id` (already assigned at segmentation time)
        and `parent_id` are used as-is for the stored row's primary key
        and self-referential `parent_clause_id`. `clauses` must be
        ordered so every parent precedes its children — exactly the
        order `ClauseSegmentationService.segment()` returns — since the
        self-referential foreign key is enforced as each row is written.
        """

    @abstractmethod
    def list_for_policy_version(self, policy_version_id: uuid.UUID) -> list[StoredClause]:
        """Every clause stored for `policy_version_id`, ordered by
        `order_index`."""

    @abstractmethod
    def get(self, clause_id: uuid.UUID) -> StoredClause | None:
        """The clause with `clause_id`, or `None` if it doesn't exist (or
        is soft-deleted)."""

    @abstractmethod
    def search(
        self,
        *,
        policy_id: uuid.UUID | None = None,
        policy_version_id: uuid.UUID | None = None,
        keyword: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[StoredClause], int]:
        """Clauses matching every given filter (AND'd together), ordered
        by `order_index`, paginated by `limit`/`offset`.

        `keyword`, when given, matches case-insensitively against a
        clause's `text` or `heading`. All filters are optional; calling
        with none of them lists every clause.

        Returns `(page, total)` — `total` is the full match count
        ignoring `limit`/`offset`, for computing how many pages exist.
        """

    @abstractmethod
    def delete_for_policy_version(self, policy_version_id: uuid.UUID) -> None:
        """Soft-delete every clause stored for `policy_version_id`.

        Does not commit — called from
        `services/policy_management_service.py::delete_policy`, which
        soft-deletes the owning policy version in the same transaction
        and commits once, so a failure partway through never leaves
        clauses deleted for a version that ends up not being removed.
        """
