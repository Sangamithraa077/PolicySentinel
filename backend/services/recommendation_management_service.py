"""Service for retrieving, filtering, and updating AI compliance recommendations."""

from __future__ import annotations

import logging
import uuid
from datetime import datetime
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from backend.models.recommendation import Recommendation

logger = logging.getLogger(__name__)


class RecommendationManagementService:
    def __init__(self, db: Session) -> None:
        self._db = db

    def search_recommendations(
        self,
        *,
        status: str | None = None,
        confidence_score: float | None = None,
        limit: int = 50,
        offset: int = 0
    ) -> tuple[list[Recommendation], int]:
        """Lists and filters AI recommendations by status and confidence score."""
        conditions = [Recommendation.deleted_at.is_(None)]

        if status:
            conditions.append(Recommendation.status.ilike(status))

        if confidence_score is not None:
            conditions.append(Recommendation.confidence_score >= confidence_score)

        query = select(Recommendation).where(*conditions)

        # Count total matches
        total_query = select(func.count()).select_from(query.subquery())
        total = self._db.scalar(total_query) or 0

        # Sort and paginate
        items_query = query.order_by(Recommendation.created_at.desc(), Recommendation.id).limit(limit).offset(offset)
        items = self._db.scalars(items_query).all()

        return list(items), total

    def get_recommendation_details(self, rec_id: uuid.UUID) -> Recommendation | None:
        """Retrieves details for a single recommendation by ID."""
        return self._db.scalar(
            select(Recommendation)
            .where(Recommendation.id == rec_id, Recommendation.deleted_at.is_(None))
        )

    def update_recommendation_status(
        self,
        rec_id: uuid.UUID,
        status: str,
        reviewer_name: str | None = None,
        review_comments: str | None = None
    ) -> Recommendation | None:
        """Accepts or rejects an AI recommendation, updating status, recording reviewer inputs, and logging the audit event."""
        valid_statuses = {"accepted", "rejected", "pending"}
        norm_status = status.strip().lower()
        if norm_status not in valid_statuses:
            raise ValueError(f"Invalid recommendation status '{status}'. Must be one of {valid_statuses}")

        recommendation = self.get_recommendation_details(rec_id)
        if recommendation is None:
            return None

        status_map = {"accepted": "Accepted", "rejected": "Rejected", "pending": "Pending"}
        old_status = recommendation.status
        new_status = status_map[norm_status]

        recommendation.status = new_status
        if reviewer_name:
            recommendation.reviewer_name = reviewer_name
            recommendation.reviewed_at = datetime.utcnow()
        if review_comments:
            recommendation.review_comments = review_comments
        
        # Log event
        logger.info(
            "Recommendation %s status updated from %s to %s for conflict %s",
            rec_id,
            old_status,
            new_status,
            recommendation.conflict_id
        )
        
        try:
            from backend.services.compliance_dashboard_service import record_compliance_audit_log
            conflict_record = recommendation.conflict
            user_email = reviewer_name or "System"
            company_id = None
            if conflict_record:
                if conflict_record.target_policy:
                    company_id = conflict_record.target_policy.company_id
                    if not reviewer_name and conflict_record.target_policy.current_version and conflict_record.target_policy.current_version.uploaded_by:
                        user_email = conflict_record.target_policy.current_version.uploaded_by.email
            
            if company_id:
                record_compliance_audit_log(
                    self._db,
                    company_id,
                    "Recommendation Approval/Rejection",
                    user_email,
                    f"Recommendation '{recommendation.recommendation_summary[:40]}...' status updated from '{old_status}' to '{new_status}'"
                )
        except Exception as audit_err:
            logger.error("Failed to write recommendation approval audit log: %s", audit_err)

        self._db.commit()
        return recommendation
