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
        missing_conflicts = [c for c in active_conflicts if c.conflict_type.lower() == "missing"]

        # Conflict density with diminishing penalty dampening
        raw_conflict_penalty = (
            (len(high_severity_conflicts) * 4.0) +
            (len(medium_severity_conflicts) * 1.5) +
            (len(low_severity_conflicts) * 0.5) +
            (len(missing_conflicts) * 2.0)
        )
        if raw_conflict_penalty == 0:
            conflict_penalty = 0.0
        else:
            conflict_penalty = min(40.0, 40.0 * (raw_conflict_penalty / (raw_conflict_penalty + 100.0)))

        # 3. Recommendations (Pending & Rejected counts)
        pending_recommendations = [r for r in recommendations if r.status == "Pending"]
        rejected_recommendations = [r for r in recommendations if r.status == "Rejected"]

        pending_penalty = min(10.0, len(pending_recommendations) * 0.1)
        rejected_penalty = min(5.0, len(rejected_recommendations) * 1.0)

        deductions = conflict_penalty + pending_penalty + rejected_penalty

        # Compliance score: bounded between 35.0 and 100.0
        compliance_score = max(35.0, min(100.0, round(100.0 - deductions, 1)))
        
        # Risk Score: 100 - Compliance Score
        risk_score = round(100.0 - compliance_score, 1)

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
