"""Service for retrieving, filtering, searching, and managing compliance conflicts."""

from __future__ import annotations

import logging
import uuid
from sqlalchemy import select, or_, func
from sqlalchemy.orm import Session, aliased

from backend.models.conflict import Conflict
from backend.models.obligation import Obligation

logger = logging.getLogger(__name__)


class ConflictManagementService:
    def __init__(self, db: Session) -> None:
        self._db = db

    def search_conflicts(
        self,
        *,
        policy_id: uuid.UUID | None = None,
        severity: str | None = None,
        conflict_type: str | None = None,
        status: str | None = None,
        search: str | None = None,
        limit: int = 20,
        offset: int = 0
    ) -> tuple[list[Conflict], int]:
        """Lists and filters conflicts based on status, type, severity, and search keywords."""
        conditions = [Conflict.deleted_at.is_(None)]

        if policy_id:
            conditions.append(or_(
                Conflict.source_policy_id == policy_id,
                Conflict.target_policy_id == policy_id
            ))

        if severity:
            conditions.append(Conflict.severity.ilike(severity))

        if conflict_type:
            conditions.append(Conflict.conflict_type.ilike(conflict_type))

        if status:
            conditions.append(Conflict.status.ilike(status))

        # Build query
        src_ob = aliased(Obligation)
        tgt_ob = aliased(Obligation)

        query = (
            select(Conflict)
            .outerjoin(src_ob, src_ob.id == Conflict.source_obligation_id)
            .outerjoin(tgt_ob, tgt_ob.id == Conflict.target_obligation_id)
            .where(*conditions)
        )

        if search:
            search_pattern = f"%{search}%"
            query = query.where(
                or_(
                    Conflict.ai_explanation.ilike(search_pattern),
                    src_ob.subject.ilike(search_pattern),
                    src_ob.action.ilike(search_pattern),
                    src_ob.object.ilike(search_pattern),
                    tgt_ob.subject.ilike(search_pattern),
                    tgt_ob.action.ilike(search_pattern),
                    tgt_ob.object.ilike(search_pattern),
                )
            )

        # Count total matches
        total_query = select(func.count()).select_from(query.subquery())
        total = self._db.scalar(total_query) or 0

        # Sort and paginate
        items_query = query.order_by(Conflict.created_at.desc(), Conflict.id).limit(limit).offset(offset)
        items = self._db.scalars(items_query).all()

        return list(items), total

    def get_conflict_details(self, conflict_id: uuid.UUID) -> Conflict | None:
        """Retrieves a single conflict record by ID."""
        return self._db.scalar(
            select(Conflict)
            .where(Conflict.id == conflict_id, Conflict.deleted_at.is_(None))
        )

    def update_conflict_status(self, conflict_id: uuid.UUID, status: str) -> Conflict | None:
        """Updates the status of a conflict (e.g. Open, Reviewed, Resolved)."""
        valid_statuses = {"open", "reviewed", "resolved"}
        if status.lower() not in valid_statuses:
            raise ValueError(f"Invalid status '{status}'. Must be one of {valid_statuses}")

        conflict = self.get_conflict_details(conflict_id)
        if conflict is None:
            return None

        # Map to proper case
        status_map = {"open": "Open", "reviewed": "Reviewed", "resolved": "Resolved"}
        conflict.status = status_map[status.lower()]
        self._db.commit()
        return conflict
