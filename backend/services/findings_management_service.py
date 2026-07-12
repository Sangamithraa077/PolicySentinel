"""Service for querying, filtering, and retrieving advanced compliance findings."""

from __future__ import annotations

import logging
import uuid
from sqlalchemy import select, or_, func
from sqlalchemy.orm import Session, aliased

from backend.models.conflict import Conflict
from backend.models.obligation import Obligation

logger = logging.getLogger(__name__)


class FindingsManagementService:
    def __init__(self, db: Session) -> None:
        self._db = db

    def search_findings(
        self,
        *,
        policy_id: uuid.UUID | None = None,
        finding_type: str | None = None,
        limit: int = 20,
        offset: int = 0
    ) -> tuple[list[Conflict], int]:
        """Lists and filters advanced findings (temporal, strength, stale) with pagination."""
        conditions = [Conflict.deleted_at.is_(None)]

        if policy_id:
            conditions.append(or_(
                Conflict.source_policy_id == policy_id,
                Conflict.target_policy_id == policy_id
            ))

        if finding_type:
            ftype = finding_type.lower()
            if ftype == "temporal":
                conditions.append(or_(
                    Conflict.temporal_conflict.is_not(None),
                    Conflict.temporal_conflict != "none"
                ))
                conditions.append(Conflict.temporal_conflict != "none")
            elif ftype == "strength":
                conditions.append(or_(
                    Conflict.strength_conflict.is_not(None),
                    Conflict.strength_conflict != "NONE"
                ))
                conditions.append(Conflict.strength_conflict != "NONE")
            elif ftype == "stale":
                conditions.append(Conflict.staleness_status.in_(["Review Required", "Outdated"]))

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

    def get_finding_details(self, finding_id: uuid.UUID) -> Conflict | None:
        """Retrieves detailed fields of a specific compliance finding by ID."""
        return self._db.scalar(
            select(Conflict)
            .where(Conflict.id == finding_id, Conflict.deleted_at.is_(None))
        )
