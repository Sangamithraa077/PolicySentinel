"""Service for retrieving, filtering, and managing obligation relationship findings."""

from __future__ import annotations

import logging
import uuid
from sqlalchemy import select, or_, func
from sqlalchemy.orm import Session, aliased

from backend.models.conflict import Conflict
from backend.models.obligation import Obligation

logger = logging.getLogger(__name__)


class RelationshipManagementService:
    def __init__(self, db: Session) -> None:
        self._db = db

    def search_relationships(
        self,
        *,
        policy_id: uuid.UUID | None = None,
        relationship_type: str | None = None,
        limit: int = 20,
        offset: int = 0
    ) -> tuple[list[Conflict], int]:
        """Lists and filters relationship findings based on type, policy ID, and offset pagination."""
        conditions = [
            Conflict.deleted_at.is_(None),
            Conflict.relationship_type.is_not(None),
        ]

        if policy_id:
            conditions.append(or_(
                Conflict.source_policy_id == policy_id,
                Conflict.target_policy_id == policy_id
            ))

        if relationship_type:
            conditions.append(Conflict.relationship_type.ilike(relationship_type))

        # Build query
        src_ob = aliased(Obligation)
        tgt_ob = aliased(Obligation)

        query = (
            select(Conflict)
            .outerjoin(src_ob, src_ob.id == Conflict.source_obligation_id)
            .outerjoin(tgt_ob, tgt_ob.id == Conflict.target_obligation_id)
            .where(*conditions)
        )

        # Count total matches
        total_query = select(func.count()).select_from(query.subquery())
        total = self._db.scalar(total_query) or 0

        # Sort and paginate
        items_query = query.order_by(Conflict.created_at.desc(), Conflict.id).limit(limit).offset(offset)
        items = self._db.scalars(items_query).all()

        return list(items), total

    def get_relationship_details(self, relationship_id: uuid.UUID) -> Conflict | None:
        """Retrieves a single relationship classification finding by ID."""
        return self._db.scalar(
            select(Conflict)
            .where(
                Conflict.id == relationship_id,
                Conflict.relationship_type.is_not(None),
                Conflict.deleted_at.is_(None)
            )
        )
