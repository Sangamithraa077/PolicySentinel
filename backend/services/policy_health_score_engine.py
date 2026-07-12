"""Engine for calculating policy health scores based on conflicts, staleness, mappings, and reviews."""
from __future__ import annotations

import logging
import uuid
from typing import TypedDict, List
from sqlalchemy import select, or_
from sqlalchemy.orm import Session

from backend.models.conflict import Conflict
from backend.models.obligation import Obligation
from backend.models.policy import Policy
from backend.models.policy_version import PolicyVersion
from backend.models.regulatory_mapping import RegulatoryMapping
from backend.models.recommendation import Recommendation
from backend.services.ai.staleness_detection_service import StalenessDetectionService

logger = logging.getLogger(__name__)


class HealthWeights(TypedDict, total=False):
    base_score: float
    conflict_penalty_critical: float
    conflict_penalty_high: float
    conflict_penalty_medium: float
    conflict_penalty_low: float
    stale_obligation_penalty: float
    missing_mapping_penalty: float
    approved_recommendation_bonus: float


DEFAULT_WEIGHTS: HealthWeights = {
    "base_score": 100.0,
    "conflict_penalty_critical": 15.0,
    "conflict_penalty_high": 10.0,
    "conflict_penalty_medium": 5.0,
    "conflict_penalty_low": 2.0,
    "stale_obligation_penalty": 8.0,
    "missing_mapping_penalty": 5.0,
    "approved_recommendation_bonus": 5.0,
}


class PolicyHealthScoreResult:
    def __init__(
        self,
        score: float,
        grade: str,
        summary: str,
        risk_factors: List[str]
    ) -> None:
        self.score = score
        self.grade = grade
        self.summary = summary
        self.risk_factors = risk_factors

    def to_dict(self) -> dict:
        return {
            "score": round(self.score, 1),
            "grade": self.grade,
            "summary": self.summary,
            "risk_factors": self.risk_factors
        }


# Thread-safe simple transient memory cache
_HEALTH_SCORE_CACHE = {}

class PolicyHealthScoreEngine:
    def __init__(self, db: Session, weights: HealthWeights | None = None) -> None:
        self._db = db
        self._weights = {**DEFAULT_WEIGHTS, **(weights or {})}

    def calculate_health_score(self, policy_id: uuid.UUID) -> PolicyHealthScoreResult:
        """Calculates policy health score (0-100), grade, summary, and top risk factors with TTL caching."""
        import time
        cache_key = (str(policy_id), frozenset(self._weights.items()))
        now = time.time()
        
        if cache_key in _HEALTH_SCORE_CACHE:
            cached_result, cached_time = _HEALTH_SCORE_CACHE[cache_key]
            if now - cached_time < 10.0: # 10 second TTL
                logger.info("Returning cached Policy Health Score for policy %s", policy_id)
                return cached_result

        logger.info("Calculating Policy Health Score for policy %s", policy_id)
        
        policy = self._db.get(Policy, policy_id)
        if not policy:
            return PolicyHealthScoreResult(0.0, "F", "Policy not found.", ["Policy record missing"])

        score = self._weights["base_score"]
        risk_factors: List[str] = []
        
        # 1. Fetch active conflicts involving this policy
        conflicts = self._db.scalars(
            select(Conflict).where(
                or_(Conflict.source_policy_id == policy_id, Conflict.target_policy_id == policy_id),
                Conflict.deleted_at.is_(None)
            )
        ).all()
        
        critical_count = 0
        high_count = 0
        med_count = 0
        low_count = 0
        
        for conf in conflicts:
            severity = (conf.severity or "medium").lower()
            if severity == "critical":
                critical_count += 1
                score -= self._weights["conflict_penalty_critical"]
            elif severity == "high":
                high_count += 1
                score -= self._weights["conflict_penalty_high"]
            elif severity == "low":
                low_count += 1
                score -= self._weights["conflict_penalty_low"]
            else:
                med_count += 1
                score -= self._weights["conflict_penalty_medium"]

        if critical_count > 0 or high_count > 0:
            risk_factors.append(f"Contains {critical_count} critical and {high_count} high severity conflicts.")
        elif med_count > 0:
            risk_factors.append(f"Contains {med_count} medium severity conflicts.")

        # 2. Fetch obligations for this policy to check mappings and staleness
        obligations = self._db.scalars(
            select(Obligation).where(
                Obligation.policy_id == policy_id,
                Obligation.deleted_at.is_(None)
            )
        ).all()
        
        missing_mappings_count = 0
        mapped_count = 0
        
        for ob in obligations:
            mapping = self._db.scalar(
                select(RegulatoryMapping).where(
                    RegulatoryMapping.obligation_id == ob.id,
                    RegulatoryMapping.deleted_at.is_(None)
                )
            )
            if not mapping or mapping.framework_name == "NONE":
                missing_mappings_count += 1
                score -= self._weights["missing_mapping_penalty"]
            else:
                mapped_count += 1

        if missing_mappings_count > 0:
            risk_factors.append(f"Has {missing_mappings_count} obligations missing regulatory framework mappings.")

        # 3. Check for stale policy versions
        versions = self._db.scalars(
            select(PolicyVersion).where(
                PolicyVersion.policy_id == policy_id,
                PolicyVersion.deleted_at.is_(None)
            )
        ).all()
        
        stale_service = StalenessDetectionService()
        stale_versions_count = 0
        
        for ver in versions:
            stale_res = stale_service.detect_staleness(ver)
            if stale_res.status in ["Review Required", "Outdated"]:
                stale_versions_count += 1
                score -= self._weights["stale_obligation_penalty"]

        if stale_versions_count > 0:
            risk_factors.append(f"Policy contains {stale_versions_count} stale or review-required revisions.")

        # 4. Offsetting bonuses for approved recommendations
        approved_recommendations_count = 0
        for conf in conflicts:
            rec = self._db.scalar(
                select(Recommendation).where(
                    Recommendation.conflict_id == conf.id,
                    Recommendation.status.in_(["Approved", "Accepted"]),
                    Recommendation.deleted_at.is_(None)
                )
            )
            if rec:
                approved_recommendations_count += 1
                score += self._weights["approved_recommendation_bonus"]

        # Clamp score between 0.0 and 100.0
        score = max(0.0, min(100.0, score))
        
        # Calculate grade
        if score >= 90.0:
            grade = "A"
        elif score >= 80.0:
            grade = "B"
        elif score >= 70.0:
            grade = "C"
        elif score >= 60.0:
            grade = "D"
        else:
            grade = "F"

        # Formulate summary
        if score >= 90.0:
            summary = "Excellent health. The policy has high regulatory alignment, no severe unresolved conflicts, and up-to-date revisions."
        elif score >= 75.0:
            summary = "Good health. Few moderate issues exist; review unresolved conflict findings or missing compliance mappings."
        elif score >= 60.0:
            summary = "Fair health. Policy possesses several compliance risks, outdated effective dates, or active conflicts requiring resolution."
        else:
            summary = "Critical risk. Policy has significant gaps, missing external standard alignments, or severe structural conflicts."

        result = PolicyHealthScoreResult(score, grade, summary, risk_factors)
        _HEALTH_SCORE_CACHE[cache_key] = (result, now)
        return result
