"""Service class implementing the Compliance Risk Score calculation engine."""

from __future__ import annotations

import logging
from backend.models.conflict import Conflict
from backend.models.recommendation import Recommendation

logger = logging.getLogger(__name__)


class ComplianceRiskScoreEngine:
    def __init__(
        self,
        high_conflict_weight: float = 15.0,
        medium_conflict_weight: float = 8.0,
        low_conflict_weight: float = 3.0,
        missing_obligation_weight: float = 10.0,
        pending_recommendation_weight: float = 5.0,
        rejected_recommendation_weight: float = 8.0
    ) -> None:
        self.high_conflict_weight = high_conflict_weight
        self.medium_conflict_weight = medium_conflict_weight
        self.low_conflict_weight = low_conflict_weight
        self.missing_obligation_weight = missing_obligation_weight
        self.pending_recommendation_weight = pending_recommendation_weight
        self.rejected_recommendation_weight = rejected_recommendation_weight

    def calculate_score(
        self,
        conflicts: list[Conflict],
        recommendations: list[Recommendation]
    ) -> dict[str, any]:
        """Calculates compliance score, risk score, risk level, and a summary of findings."""
        deductions = 0.0

        # 1. Unresolved/Active conflicts (status != 'Resolved')
        active_conflicts = [c for c in conflicts if c.status != "Resolved"]
        
        high_severity_conflicts = [c for c in active_conflicts if c.severity.lower() == "high"]
        medium_severity_conflicts = [c for c in active_conflicts if c.severity.lower() == "medium"]
        low_severity_conflicts = [c for c in active_conflicts if c.severity.lower() == "low"]

        deductions += len(high_severity_conflicts) * self.high_conflict_weight
        deductions += len(medium_severity_conflicts) * self.medium_conflict_weight
        deductions += len(low_severity_conflicts) * self.low_conflict_weight

        # 2. Missing obligations (conflicts of type 'missing')
        missing_conflicts = [c for c in active_conflicts if c.conflict_type.lower() == "missing"]
        deductions += len(missing_conflicts) * self.missing_obligation_weight

        # 3. Recommendations (Pending & Rejected counts)
        pending_recommendations = [r for r in recommendations if r.status == "Pending"]
        rejected_recommendations = [r for r in recommendations if r.status == "Rejected"]

        deductions += len(pending_recommendations) * self.pending_recommendation_weight
        deductions += len(rejected_recommendations) * self.rejected_recommendation_weight

        # Compliance score: bounded 0 to 100
        compliance_score = max(0.0, 100.0 - deductions)
        
        # Risk Score: 100 - Compliance Score
        risk_score = 100.0 - compliance_score

        # Risk Level mapping
        if risk_score <= 20:
            risk_level = "Low"
        elif risk_score <= 45:
            risk_level = "Medium"
        elif risk_score <= 75:
            risk_level = "High"
        else:
            risk_level = "Critical"

        # Generate summary
        if deductions == 0:
            risk_summary = "All compliance checks are fully clear. No policy conflicts, missing obligations, or pending recommendations."
        else:
            active_conf_count = len(active_conflicts)
            pending_rec_count = len(pending_recommendations)
            risk_summary = (
                f"Compliance risk is evaluated as {risk_level} (Score: {compliance_score:.0f}). "
                f"Detected {active_conf_count} active conflicts ({len(high_severity_conflicts)} High, "
                f"{len(medium_severity_conflicts)} Medium, {len(low_severity_conflicts)} Low) "
                f"and {pending_rec_count} pending AI resolution recommendations requiring review."
            )

        return {
            "compliance_score": round(compliance_score, 1),
            "risk_score": round(risk_score, 1),
            "risk_level": risk_level,
            "risk_summary": risk_summary
        }
