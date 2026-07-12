"""Integration tests for the Recommendation database model."""

from __future__ import annotations

import pytest
from sqlalchemy.orm import Session
from sqlalchemy import select

from backend.models.policy import Policy
from backend.models.conflict import Conflict
from backend.models.recommendation import Recommendation


def test_recommendation_model_database_relations(db_session: Session, seeded_company_and_user) -> None:
    company, user = seeded_company_and_user

    # 1. Create source and target policies
    policy_a = Policy(company=company, title="Company Standards")
    policy_b = Policy(company=company, title="Supplier Requirements")
    db_session.add_all([policy_a, policy_b])
    db_session.flush()

    # 2. Create Conflict
    conflict = Conflict(
        source_policy_id=policy_a.id,
        target_policy_id=policy_b.id,
        conflict_type="missing",
        similarity_score=0.25,
        severity="medium",
        ai_explanation="Omission detected",
        status="Open"
    )
    db_session.add(conflict)
    db_session.flush()

    # 3. Create Recommendation pointing to the Conflict
    recommendation = Recommendation(
        conflict_id=conflict.id,
        recommendation_summary="Integrate gap obligation.",
        suggested_action="Add missing obligation",
        original_clause="Original clause snippet",
        revised_clause="Revised clause suggested snippet",
        reason="Preserves compliance controls.",
        ai_model="mock-gemini",
        confidence_score=0.92,
        status="Pending"
    )
    db_session.add(recommendation)
    db_session.commit()

    # 4. Assertions on relations
    db_recommendation = db_session.scalar(
        select(Recommendation).where(Recommendation.conflict_id == conflict.id)
    )
    assert db_recommendation is not None
    assert db_recommendation.id == recommendation.id
    assert db_recommendation.conflict.id == conflict.id
    assert db_recommendation.status == "Pending"
    assert db_recommendation.confidence_score == 0.92

    # Verify back-populating relationship on Conflict
    db_session.refresh(conflict)
    assert len(conflict.recommendations) == 1
    assert conflict.recommendations[0].id == recommendation.id
