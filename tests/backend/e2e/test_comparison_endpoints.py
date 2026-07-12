"""E2E/Integration tests for policy version comparison API endpoints."""

from __future__ import annotations

import pytest
import uuid
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.models.policy import Policy
from backend.models.policy_version import PolicyVersion
from backend.models.clause import Clause
from backend.models.obligation import Obligation
from backend.models.enums import PolicyDocumentFileType

pytestmark = pytest.mark.api_response


def test_compare_endpoint_flow(client: TestClient, db_session: Session, seeded_company_and_user) -> None:
    company, user = seeded_company_and_user

    policy = Policy(company=company, title="Comparison E2E Policy")
    db_session.add(policy)
    db_session.flush()

    version_a = PolicyVersion(
        policy=policy,
        version_number=1,
        source_file_reference="path/a.pdf",
        file_hash="hasha",
        uploaded_by=user,
        original_filename="a.pdf",
        size_bytes=512,
        file_type=PolicyDocumentFileType.PDF,
        uploaded_at=datetime.now(timezone.utc),
    )
    version_b = PolicyVersion(
        policy=policy,
        version_number=2,
        source_file_reference="path/b.pdf",
        file_hash="hashb",
        uploaded_by=user,
        original_filename="b.pdf",
        size_bytes=512,
        file_type=PolicyDocumentFileType.PDF,
        uploaded_at=datetime.now(timezone.utc),
    )
    db_session.add_all([version_a, version_b])
    db_session.flush()

    c_a = Clause(policy_id=policy.id, policy_version_id=version_a.id, clause_number="1", text="Version A clause text", order_index=1)
    c_b = Clause(policy_id=policy.id, policy_version_id=version_b.id, clause_number="1", text="Version B clause text", order_index=1)
    db_session.add_all([c_a, c_b])
    db_session.flush()

    ob_a = Obligation(
        clause_id=c_a.id,
        policy_id=policy.id,
        subject="Staff",
        action="attend training",
        object="security training",
        modality="Must",
        compliance_category="Security",
        confidence_score=0.95,
        ai_model="mock"
    )
    ob_b = Obligation(
        clause_id=c_b.id,
        policy_id=policy.id,
        subject="Staff",
        action="attend training",
        object="security training",
        modality="Must",
        compliance_category="Security",
        confidence_score=0.95,
        ai_model="mock"
    )
    db_session.add_all([ob_a, ob_b])
    db_session.commit()

    # Trigger POST /api/v1/comparison/compare
    payload = {
        "version_a_id": str(version_a.id),
        "version_b_id": str(version_b.id)
    }
    response = client.post("/api/v1/comparison/compare", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert data["version_a_id"] == str(version_a.id)
    assert data["version_b_id"] == str(version_b.id)

    # Comparisons list
    assert len(data["comparisons"]) == 1
    assert data["comparisons"][0]["obligation_a_id"] == str(ob_a.id)
    assert data["comparisons"][0]["obligation_b_id"] == str(ob_b.id)
    assert data["comparisons"][0]["category"] == "Exact Match"

    # Conflicts list (should have a duplicate warning since it is identical)
    assert len(data["conflicts"]) == 1
    assert data["conflicts"][0]["type"] == "duplicate"
    assert data["conflicts"][0]["severity"] == "low"


def test_compare_endpoint_not_found(client: TestClient) -> None:
    payload = {
        "version_a_id": str(uuid.uuid4()),
        "version_b_id": str(uuid.uuid4())
    }
    response = client.post("/api/v1/comparison/compare", json=payload)
    assert response.status_code == 404
