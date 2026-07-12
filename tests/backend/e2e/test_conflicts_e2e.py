"""E2E/Integration tests for compliance conflict API endpoints."""

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
from backend.models.conflict import Conflict
from backend.models.enums import PolicyDocumentFileType

pytestmark = pytest.mark.api_response


def test_conflicts_endpoints_flow(client: TestClient, db_session: Session, seeded_company_and_user) -> None:
    company, user = seeded_company_and_user

    # 1. Create two policies belonging to the same company
    policy_a = Policy(company=company, title="Company Code of Conduct")
    policy_b = Policy(company=company, title="External Vendor Standards")
    db_session.add_all([policy_a, policy_b])
    db_session.flush()

    version_a = PolicyVersion(
        policy=policy_a,
        version_number=1,
        source_file_reference="path/conduct.pdf",
        file_hash="hashconduct",
        uploaded_by=user,
        original_filename="conduct.pdf",
        size_bytes=1024,
        file_type=PolicyDocumentFileType.PDF,
        uploaded_at=datetime.now(timezone.utc),
    )
    version_b = PolicyVersion(
        policy=policy_b,
        version_number=1,
        source_file_reference="path/vendor.pdf",
        file_hash="hashvendor",
        uploaded_by=user,
        original_filename="vendor.pdf",
        size_bytes=1024,
        file_type=PolicyDocumentFileType.PDF,
        uploaded_at=datetime.now(timezone.utc),
    )
    db_session.add_all([version_a, version_b])
    db_session.flush()

    c_a = Clause(policy_id=policy_a.id, policy_version_id=version_a.id, clause_number="1", text="Clause A", order_index=1)
    c_b = Clause(policy_id=policy_b.id, policy_version_id=version_b.id, clause_number="2", text="Clause B", order_index=1)
    db_session.add_all([c_a, c_b])
    db_session.flush()

    ob_a = Obligation(
        clause_id=c_a.id,
        policy_id=policy_a.id,
        subject="Vendors",
        action="encrypt",
        object="data",
        modality="Must",
        compliance_category="Security",
        confidence_score=0.95,
        ai_model="mock"
    )
    ob_b = Obligation(
        clause_id=c_b.id,
        policy_id=policy_b.id,
        subject="Vendors",
        action="encrypt",
        object="data",
        modality="Should",
        compliance_category="Security",
        confidence_score=0.95,
        ai_model="mock"
    )
    db_session.add_all([ob_a, ob_b])
    db_session.flush()

    # Pre-seed Conflict record representing contradiction
    conflict = Conflict(
        source_policy_id=policy_a.id,
        target_policy_id=policy_b.id,
        source_obligation_id=ob_a.id,
        target_obligation_id=ob_b.id,
        conflict_type="contradiction",
        similarity_score=0.85,
        severity="high",
        ai_explanation="Opposing Modality: Must vs Should for data encryption.",
        status="Open"
    )
    db_session.add(conflict)
    db_session.commit()

    # 2. Test GET /api/v1/conflicts
    response = client.get("/api/v1/conflicts")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["id"] == str(conflict.id)
    assert data["items"][0]["source_policy"]["title"] == "Company Code of Conduct"
    assert data["items"][0]["target_obligation"]["modality"] == "Should"

    # Test filtering by status
    response_filter_status = client.get("/api/v1/conflicts", params={"status": "Open"})
    assert response_filter_status.json()["total"] == 1
    
    response_filter_status_none = client.get("/api/v1/conflicts", params={"status": "Resolved"})
    assert response_filter_status_none.json()["total"] == 0

    # Test keyword search
    response_search = client.get("/api/v1/conflicts", params={"search": "encryption"})
    assert response_search.json()["total"] == 1

    response_search_none = client.get("/api/v1/conflicts", params={"search": "nonexistent"})
    assert response_search_none.json()["total"] == 0

    # 3. Test GET /api/v1/conflicts/{id}
    response_details = client.get(f"/api/v1/conflicts/{conflict.id}")
    assert response_details.status_code == 200
    assert response_details.json()["id"] == str(conflict.id)

    # 4. Test PATCH /api/v1/conflicts/{id}/status
    response_patch = client.patch(f"/api/v1/conflicts/{conflict.id}/status", json={"status": "Reviewed"})
    assert response_patch.status_code == 200
    assert response_patch.json()["status"] == "Reviewed"

    # Verify db state
    db_session.refresh(conflict)
    assert conflict.status == "Reviewed"

    # Invalid status value returns 400
    response_patch_invalid = client.patch(f"/api/v1/conflicts/{conflict.id}/status", json={"status": "Invalid"})
    assert response_patch_invalid.status_code == 400
