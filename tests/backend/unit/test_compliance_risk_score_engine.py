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

    # Total deductions expected = 15 + 8 + 3 + 10 (for type missing) + 5 + 8 = 49
    # Compliance Score = 100 - 49 = 51
    # Risk Score = 49
    result = engine.calculate_score(conflicts, recommendations)

    assert result["compliance_score"] == 51.0
    assert result["risk_score"] == 49.0
    assert result["risk_level"] == "High"  # 49 is between 46 and 75
    assert "High" in result["risk_level"]
