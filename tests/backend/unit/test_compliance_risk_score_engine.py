import pytest
from backend.services.compliance_risk_score_engine import ComplianceRiskScoreEngine
from backend.models.conflict import Conflict
from backend.models.recommendation import Recommendation


def test_compliance_risk_score_engine_all_clear():
    engine = ComplianceRiskScoreEngine()
    result = engine.calculate_score([], [])
    
    assert result["compliance_score"] == 100.0
    assert result["risk_score"] == 0.0
    assert result["risk_level"] == "Low"
    assert "fully clear" in result["risk_summary"]


def test_compliance_risk_score_engine_deductions():
    engine = ComplianceRiskScoreEngine(
        high_conflict_weight=15,
        medium_conflict_weight=8,
        low_conflict_weight=3,
        missing_obligation_weight=10,
        pending_recommendation_weight=5,
        rejected_recommendation_weight=8
    )

    # 1. Create mock conflicts
    # Let's mock conflicts using simple objects or class mocks
    class MockConflict:
        def __init__(self, severity, conflict_type, status="Open"):
            self.severity = severity
            self.conflict_type = conflict_type
            self.status = status

    class MockRecommendation:
        def __init__(self, status):
            self.status = status

    conflicts = [
        MockConflict(severity="High", conflict_type="contradictory"), # -15
        MockConflict(severity="Medium", conflict_type="duplicate"),    # -8
        MockConflict(severity="Low", conflict_type="missing"),         # -3 (low conflict) + -10 (missing obligation conflict type) = -13
    ]
    
    recommendations = [
        MockRecommendation(status="Pending"),  # -5
        MockRecommendation(status="Rejected"), # -8
        MockRecommendation(status="Accepted"), # -0
    ]

    # Calibrated dampening curve calculations:
    # raw_penalty = (1 * 4.0) + (1 * 1.5) + (1 * 0.5) + (1 * 2.0) = 8.0
    # conflict_penalty = 40.0 * (8.0 / 108.0) ~ 2.96
    # pending_penalty = 0.1, rejected_penalty = 1.0 -> total deductions ~ 4.06
    # compliance_score = 100 - 4.1 = 95.9, risk_score = 4.1, risk_level = Low
    result = engine.calculate_score(conflicts, recommendations)

    assert result["compliance_score"] == 95.9
    assert result["risk_score"] == 4.1
    assert result["risk_level"] == "Low"
    assert "Low" in result["risk_level"]
