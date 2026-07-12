"""E2E tests for Obligation API endpoints."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.models.policy import Policy
from backend.models.policy_version import PolicyVersion
from backend.models.clause import Clause
from backend.models.obligation import Obligation
from backend.models.enums import PolicyDocumentFileType


@pytest.fixture
def seeded_policy_with_obligations(db_session: Session, seeded_company_and_user):
    company, user = seeded_company_and_user

    policy = Policy(company=company, title="E2E Obligations Policy")
    db_session.add(policy)
    db_session.flush()

    version = PolicyVersion(
        policy=policy,
        version_number=1,
        source_file_reference="dummy/path.pdf",
        file_hash="dummyhash",
        uploaded_by=user,
        original_filename="dummy.pdf",
        size_bytes=1024,
        file_type=PolicyDocumentFileType.PDF,
        uploaded_at=datetime.now(timezone.utc),
    )
    db_session.add(version)
    db_session.flush()

    clause1 = Clause(
        policy_id=policy.id,
        policy_version_id=version.id,
        clause_number="1.1",
        heading="Data Security",
        text="All administrators must encrypt keys.",
    )
    clause2 = Clause(
        policy_id=policy.id,
        policy_version_id=version.id,
        clause_number="1.2",
        heading="Audit Logging",
        text="The CISO should maintain access logs.",
    )
    db_session.add_all([clause1, clause2])
    db_session.flush()

    ob1 = Obligation(
        clause_id=clause1.id,
        policy_id=policy.id,
        subject="All administrators",
        action="encrypt",
        object="keys",
        modality="Must",
        conditions="None",
        time_constraint=None,
        compliance_category="Cryptography",
        confidence_score=0.99,
        ai_model="gemini-2.5-flash",
    )
    ob2 = Obligation(
        clause_id=clause2.id,
        policy_id=policy.id,
        subject="CISO",
        action="maintain",
        object="access logs",
        modality="Should",
        conditions="None",
        time_constraint="Always",
        compliance_category="Logging",
        confidence_score=0.92,
        ai_model="gemini-2.5-flash",
    )
    db_session.add_all([ob1, ob2])
    db_session.commit()

    return policy, version, [clause1, clause2], [ob1, ob2]


def test_list_and_filter_obligations(client: TestClient, seeded_policy_with_obligations) -> None:
    policy, version, clauses, obligations = seeded_policy_with_obligations

    # 1. List all obligations
    response = client.get("/api/v1/obligations")
    assert response.status_code == 200
    body = response.json()
    assert body["total"] >= 2
    assert len(body["items"]) >= 2

    # 2. Filter by policy_id
    response = client.get("/api/v1/obligations", params={"policy_id": str(policy.id)})
    assert response.status_code == 200
    items = response.json()["items"]
    assert len(items) == 2
    assert {str(obligations[0].id), str(obligations[1].id)} == {x["id"] for x in items}

    # 3. Filter by compliance_category
    response = client.get("/api/v1/obligations", params={"compliance_category": "Cryptography", "policy_id": str(policy.id)})
    assert response.status_code == 200
    items = response.json()["items"]
    assert len(items) == 1
    assert items[0]["id"] == str(obligations[0].id)

    # 4. Filter by modality
    response = client.get("/api/v1/obligations", params={"modality": "Should", "policy_id": str(policy.id)})
    assert response.status_code == 200
    items = response.json()["items"]
    assert len(items) == 1
    assert items[0]["id"] == str(obligations[1].id)


def test_search_obligations_by_keyword(client: TestClient, seeded_policy_with_obligations) -> None:
    policy, version, clauses, obligations = seeded_policy_with_obligations

    # Search by keyword matching object of first obligation, isolated by policy
    response = client.get("/api/v1/obligations", params={"policy_id": str(policy.id), "keyword": "keys"})
    assert response.status_code == 200
    items = response.json()["items"]
    assert len(items) == 1
    assert items[0]["id"] == str(obligations[0].id)

    # Search by keyword matching subject of second obligation, isolated by policy
    response = client.get("/api/v1/obligations", params={"policy_id": str(policy.id), "keyword": "CISO"})
    assert response.status_code == 200
    items = response.json()["items"]
    assert len(items) == 1
    assert items[0]["id"] == str(obligations[1].id)


def test_get_obligation_details(client: TestClient, seeded_policy_with_obligations) -> None:
    policy, version, clauses, obligations = seeded_policy_with_obligations
    ob = obligations[0]

    response = client.get(f"/api/v1/obligations/{ob.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(ob.id)
    assert data["clause_id"] == str(ob.clause_id)
    assert data["policy_id"] == str(ob.policy_id)
    assert data["subject"] == "All administrators"
    assert data["action"] == "encrypt"
    assert data["object"] == "keys"
    assert data["modality"] == "Must"
    assert data["compliance_category"] == "Cryptography"
    assert data["confidence_score"] == 0.99
    assert data["ai_model"] == "gemini-2.5-flash"


def test_get_unknown_obligation_returns_404(client: TestClient) -> None:
    unknown_id = uuid.uuid4()
    response = client.get(f"/api/v1/obligations/{unknown_id}")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "obligation_not_found"
