"""Service for listing, searching, and fetching obligations."""

from __future__ import annotations

import uuid
from sqlalchemy import select, func, or_
from sqlalchemy.orm import Session

from backend.models.obligation import Obligation
from backend.domain.exceptions.obligation_exceptions import ObligationNotFoundError


class ObligationManagementService:
    def __init__(self, db: Session) -> None:
        self._db = db

    def search_obligations(
        self,
        *,
        policy_id: uuid.UUID | None = None,
        clause_id: uuid.UUID | None = None,
        compliance_category: str | None = None,
        modality: str | None = None,
        keyword: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[Obligation], int]:
        """Searches obligations based on various filters and keywords."""
        conditions = [Obligation.deleted_at.is_(None)]

        if policy_id is not None:
            conditions.append(Obligation.policy_id == policy_id)
        if clause_id is not None:
            conditions.append(Obligation.clause_id == clause_id)
        if compliance_category is not None:
            conditions.append(Obligation.compliance_category.ilike(compliance_category))
        if modality is not None:
            conditions.append(Obligation.modality.ilike(modality))
        if keyword:
            pattern = f"%{keyword.replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_')}%"
            conditions.append(
                or_(
                    Obligation.subject.ilike(pattern, escape="\\"),
                    Obligation.action.ilike(pattern, escape="\\"),
                    Obligation.object.ilike(pattern, escape="\\"),
                    Obligation.conditions.ilike(pattern, escape="\\"),
                    Obligation.time_constraint.ilike(pattern, escape="\\"),
                )
            )

        from backend.models.clause import Clause

        total = self._db.scalar(
            select(func.count()).select_from(Obligation).where(*conditions)
        ) or 0

        items = self._db.scalars(
            select(Obligation)
            .join(Clause, Clause.id == Obligation.clause_id)
            .where(*conditions)
            .order_by(Clause.order_index, Obligation.created_at, Obligation.id)
            .limit(limit)
            .offset(offset)
        ).all()

        return list(items), total

    def get_obligation(self, obligation_id: uuid.UUID) -> Obligation:
        """Retrieves details of a single obligation."""
        obligation = self._db.scalar(
            select(Obligation).where(
                Obligation.id == obligation_id,
                Obligation.deleted_at.is_(None)
            )
        )
        if obligation is None:
            raise ObligationNotFoundError(f"Obligation '{obligation_id}' does not exist.")
        return obligation
