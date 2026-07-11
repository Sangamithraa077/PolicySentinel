"""SQLAlchemy-backed implementation of `ClauseRepositoryInterface`.

Maps between the framework-agnostic `domain.entities.clause.PolicyClause`
(write side, produced by clause segmentation) / `StoredClause` (read
side) and `models.clause.Clause`, the ORM row — isolating that mapping
here is what lets `services/store_segmented_clauses_service.py` stay
ignorant of SQLAlchemy entirely (see repositories/README.md).

`clause_type` is left `None` on every row this repository writes:
segmentation only determines document structure, never what a clause
*means* (obligation/definition/prohibition/...) — that's a separate,
likely AI-assisted classification step this repository has no part in.
`extracted_by` is always `ExtractionMethod.RULE_BASED`, since this whole
pipeline (parsing -> normalization -> segmentation -> this repository)
never calls the AI layer.

Transaction ownership differs by method, deliberately: `save_all` is a
complete, self-contained use case (nothing else composes with it), so
it commits and rolls back on its own, same reasoning as
`FileStorageService`. `delete_for_policy_version` is always called from
inside `services/policy_management_service.py::delete_policy`'s larger
transaction (policy + its versions + their clauses, all soft-deleted
together or not at all), so it only stages the change and leaves
committing to that caller — committing here too would let a partial
cascade survive if a later step in that larger transaction failed.
"""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from datetime import UTC, datetime

from sqlalchemy import ColumnElement, func, or_, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.domain.entities.clause import PolicyClause
from backend.domain.exceptions.clause_exceptions import ClauseStorageError
from backend.domain.interfaces.clause_repository_interface import (
    ClauseRepositoryInterface,
    StoredClause,
)
from backend.models.clause import Clause as ClauseRecord
from backend.models.enums import ExtractionMethod


class ClauseRepository(ClauseRepositoryInterface):
    def __init__(self, db: Session) -> None:
        self._db = db

    def save_all(
        self,
        clauses: Sequence[PolicyClause],
        *,
        policy_id: uuid.UUID,
        policy_version_id: uuid.UUID,
    ) -> None:
        for clause in clauses:
            self._db.add(
                ClauseRecord(
                    id=clause.id,
                    policy_id=policy_id,
                    policy_version_id=policy_version_id,
                    parent_clause_id=clause.parent_id,
                    clause_number=clause.clause_number,
                    heading=clause.heading,
                    text=_non_blank_text(clause),
                    clause_type=None,
                    order_index=clause.order_index,
                    extracted_by=ExtractionMethod.RULE_BASED,
                )
            )

        try:
            self._db.commit()
        except IntegrityError as exc:
            self._db.rollback()
            raise ClauseStorageError(
                f"Could not store clauses for policy version '{policy_version_id}': {exc}"
            ) from exc

    def list_for_policy_version(self, policy_version_id: uuid.UUID) -> list[StoredClause]:
        records = self._db.scalars(
            select(ClauseRecord)
            .where(
                ClauseRecord.policy_version_id == policy_version_id,
                ClauseRecord.deleted_at.is_(None),
            )
            .order_by(ClauseRecord.order_index)
        ).all()
        return [_to_stored_clause(record) for record in records]

    def get(self, clause_id: uuid.UUID) -> StoredClause | None:
        record = self._db.scalar(
            select(ClauseRecord).where(
                ClauseRecord.id == clause_id, ClauseRecord.deleted_at.is_(None)
            )
        )
        return _to_stored_clause(record) if record is not None else None

    def search(
        self,
        *,
        policy_id: uuid.UUID | None = None,
        policy_version_id: uuid.UUID | None = None,
        keyword: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[StoredClause], int]:
        conditions: list[ColumnElement[bool]] = [ClauseRecord.deleted_at.is_(None)]
        if policy_id is not None:
            conditions.append(ClauseRecord.policy_id == policy_id)
        if policy_version_id is not None:
            conditions.append(ClauseRecord.policy_version_id == policy_version_id)
        if keyword:
            pattern = f"%{_escape_for_ilike(keyword)}%"
            conditions.append(
                or_(
                    ClauseRecord.text.ilike(pattern, escape="\\"),
                    ClauseRecord.heading.ilike(pattern, escape="\\"),
                )
            )

        total = (
            self._db.scalar(select(func.count()).select_from(ClauseRecord).where(*conditions))
            or 0
        )
        records = self._db.scalars(
            select(ClauseRecord)
            .where(*conditions)
            .order_by(ClauseRecord.order_index, ClauseRecord.id)
            .limit(limit)
            .offset(offset)
        ).all()
        return [_to_stored_clause(record) for record in records], total

    def delete_for_policy_version(self, policy_version_id: uuid.UUID) -> None:
        self._db.execute(
            update(ClauseRecord)
            .where(
                ClauseRecord.policy_version_id == policy_version_id,
                ClauseRecord.deleted_at.is_(None),
            )
            .values(deleted_at=datetime.now(UTC))
        )


def _escape_for_ilike(value: str) -> str:
    # Postgres ILIKE treats %, _, and the escape character itself as
    # metacharacters -- without this, searching for e.g. "50%" would
    # match "50" followed by anything, not the literal text "50%".
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def _non_blank_text(clause: PolicyClause) -> str:
    # The clauses_text_not_blank check constraint requires non-empty
    # text; segmentation can produce an empty body for a marker line
    # with no trailing content and nothing following it before the next
    # marker (e.g. a lone "Section 1" with nothing else in the document).
    stripped = clause.text.strip()
    if stripped:
        return stripped
    return clause.heading or clause.clause_number or "(no content)"


def _to_stored_clause(record: ClauseRecord) -> StoredClause:
    return StoredClause(
        id=record.id,
        policy_id=record.policy_id,
        policy_version_id=record.policy_version_id,
        parent_clause_id=record.parent_clause_id,
        clause_number=record.clause_number,
        heading=record.heading,
        text=record.text,
        order_index=record.order_index,
    )
