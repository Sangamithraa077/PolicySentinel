"""Service class for retrieving executive compliance summaries and listing audit history records."""

from __future__ import annotations

import logging
import uuid
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from backend.models.policy import Policy
from backend.models.clause import Clause
from backend.models.obligation import Obligation
from backend.models.conflict import Conflict
from backend.models.recommendation import Recommendation
from backend.models.compliance_audit_log import ComplianceAuditLog
from backend.services.compliance_risk_score_engine import ComplianceRiskScoreEngine

logger = logging.getLogger(__name__)


class ComplianceDashboardService:
    def __init__(self, db: Session) -> None:
        self._db = db
        self._score_engine = ComplianceRiskScoreEngine()

    def get_executive_summary(self, company_id: uuid.UUID) -> dict[str, any]:
        """Calculates and aggregates executive level metrics and risk score for a company."""
        # 1. Policies belonging to the company
        policies_query = select(Policy.id).where(
            Policy.company_id == company_id,
            Policy.deleted_at.is_(None)
        )
        policy_ids = self._db.scalars(policies_query).all()
        total_policies = len(policy_ids)

        if total_policies == 0:
            return {
                "total_policies": 0,
                "total_clauses": 0,
                "total_obligations": 0,
                "active_conflicts": 0,
                "resolved_conflicts": 0,
                "pending_recommendations": 0,
                "compliance_score": 100.0,
                "risk_score": 0.0,
                "risk_level": "Low",
                "risk_summary": "No policies uploaded yet. Compliance risk is evaluated as Low."
            }

        # 2. Total clauses
        total_clauses = self._db.scalar(
            select(func.count(Clause.id)).where(Clause.policy_id.in_(policy_ids))
        ) or 0

        # 3. Total obligations
        total_obligations = self._db.scalar(
            select(func.count(Obligation.id)).where(Obligation.policy_id.in_(policy_ids))
        ) or 0

        # 4. Conflicts
        # Any conflicts where the target policy (or source policy) belongs to the company
        conflicts_query = select(Conflict).where(
            Conflict.target_policy_id.in_(policy_ids),
            Conflict.deleted_at.is_(None)
        )
        conflicts = self._db.scalars(conflicts_query).all()

        active_conflicts_count = sum(1 for c in conflicts if c.status != "Resolved")
        resolved_conflicts_count = sum(1 for c in conflicts if c.status == "Resolved")

        # 5. Recommendations
        # Query recommendations belonging to conflicts of this company
        conflict_ids = [c.id for c in conflicts]
        recommendations = []
        if conflict_ids:
            recommendations_query = select(Recommendation).where(
                Recommendation.conflict_id.in_(conflict_ids),
                Recommendation.deleted_at.is_(None)
            )
            recommendations = self._db.scalars(recommendations_query).all()

        pending_recs_count = sum(1 for r in recommendations if r.status == "Pending")

        # 6. Compliance Score & Risk Level calculation
        scoring = self._score_engine.calculate_score(conflicts, recommendations)

        return {
            "total_policies": total_policies,
            "total_clauses": total_clauses,
            "total_obligations": total_obligations,
            "active_conflicts": active_conflicts_count,
            "resolved_conflicts": resolved_conflicts_count,
            "pending_recommendations": pending_recs_count,
            "compliance_score": scoring["compliance_score"],
            "risk_score": scoring["risk_score"],
            "risk_level": scoring["risk_level"],
            "risk_summary": scoring["risk_summary"]
        }

    def list_audit_history(
        self,
        company_id: uuid.UUID,
        limit: int = 50,
        offset: int = 0
    ) -> tuple[list[ComplianceAuditLog], int]:
        """Lists the paginated immutable audit entries for a company."""
        query = select(ComplianceAuditLog).where(
            ComplianceAuditLog.company_id == company_id
        )

        total_query = select(func.count()).select_from(query.subquery())
        total = self._db.scalar(total_query) or 0

        items_query = query.order_by(ComplianceAuditLog.occurred_at.desc(), ComplianceAuditLog.id).limit(limit).offset(offset)
        items = self._db.scalars(items_query).all()

        return list(items), total


def record_compliance_audit_log(
    db: Session,
    company_id: uuid.UUID,
    event_type: str,
    user_identifier: str,
    description: str
) -> ComplianceAuditLog:
    """Creates and persists an immutable compliance audit entry."""
    entry = ComplianceAuditLog(
        company_id=company_id,
        event_type=event_type,
        user_identifier=user_identifier,
        description=description
    )
    db.add(entry)
    db.flush()
    return entry
