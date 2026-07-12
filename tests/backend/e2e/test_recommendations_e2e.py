"""End-to-end tests for the Recommendations API endpoints."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.models.policy import Policy
from backend.models.conflict import Conflict
from backend.models.recommendation import Recommendation


def test_recommendations_e2e_workflow(
    client: TestClient,
    db_session: Session,
    seeded_company_and_user
) -> None:
    company, user = seeded_company_and_user

    # 1. Setup mock Conflict & Recommendation records
    policy_a = Policy(company=company, title="Corporate Security v1")
    policy_b = Policy(company=company, title="Corporate Security v2")
    db_session.add_all([policy_a, policy_b])
    db_session.flush()

    conflict = Conflict(
        source_policy_id=policy_a.id,
        target_policy_id=policy_b.id,
        conflict_type="contradiction",
        similarity_score=0.15,
        severity="high",
        ai_explanation="Encryption guidelines mismatch",
        status="Open"
    )
    db_session.add(conflict)
    db_session.flush()

    rec1 = Recommendation(
        conflict_id=conflict.id,
        recommendation_summary="Change to AES-256",
        suggested_action="Align encryption standard",
        original_clause="Clause using triple DES",
        revised_clause="Clause using AES-256",
        reason="AES-256 is current standards",
        ai_model="mock",
        confidence_score=0.95,
        status="Pending"
    )
    rec2 = Recommendation(
        conflict_id=conflict.id,
        recommendation_summary="Remove deprecated SSL v3",
        suggested_action="Remove deprecation",
        original_clause="SSL v3 is permitted",
        revised_clause="TLS 1.3 must be used",
        reason="SSL v3 is insecure",
        ai_model="mock",
        confidence_score=0.75,
        status="Accepted"
    )
    db_session.add_all([rec1, rec2])
    db_session.commit()

    # 2. Test List Endpoint
    response = client.get("/api/v1/recommendations")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2

    # 3. Test Filter by Status
    response = client.get("/api/v1/recommendations?status=Accepted")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["recommendation_summary"] == "Remove deprecated SSL v3"

    # 4. Test Filter by Confidence Score
    response = client.get("/api/v1/recommendations?confidence_score=0.80")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["recommendation_summary"] == "Change to AES-256"

    # 5. Test Details Endpoint
    response = client.get(f"/api/v1/recommendations/{rec1.id}")
    assert response.status_code == 200
    rec_details = response.json()
    assert rec_details["id"] == str(rec1.id)
    assert rec_details["status"] == "Pending"
    assert rec_details["original_clause"] == "Clause using triple DES"

    # 6. Test PATCH status endpoint
    response = client.patch(
        f"/api/v1/recommendations/{rec1.id}/status",
        json={"status": "Accepted"}
    )
    assert response.status_code == 200
    updated_rec = response.json()
    assert updated_rec["status"] == "Accepted"

    # Verify database persistence
    db_session.refresh(rec1)
    assert rec1.status == "Accepted"
