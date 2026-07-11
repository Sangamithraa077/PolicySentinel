"""End-to-end tests for the Clause REST API — full HTTP requests against
a real FastAPI app (TestClient) and a real PostgreSQL test database.

Clauses aren't created via HTTP yet (no "segment this policy" endpoint
exists) -- each test seeds them directly through the same
services/repository the storage task built
(ClauseSegmentationService -> StoreSegmentedClausesService ->
ClauseRepository, sharing the request's own `db_session`) and then
exercises the read/search/delete-cascade behavior purely over HTTP.
"""

from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.domain.entities.clause import PolicyClause
from backend.repositories.clause_repository import ClauseRepository
from backend.services.clause_segmentation_service import ClauseSegmentationService
from backend.services.store_segmented_clauses_service import StoreSegmentedClausesService

# Every test here drives the real HTTP API end to end, so all of them
# verify "API responses" in addition to whatever behavior each is
# individually marked for.
pytestmark = pytest.mark.api_response

UPLOAD_URL = "/api/v1/uploads/policies"
POLICIES_URL = "/api/v1/policies"
CLAUSES_URL = "/api/v1/clauses"


def _upload(client: TestClient, seeded_company_and_user, *, policy_title: str) -> dict:
    company, user = seeded_company_and_user
    data = {
        "company_id": str(company.id),
        "uploaded_by_user_id": str(user.id),
        "policy_title": policy_title,
        "version_number": "1",
    }
    files = {"file": ("policy.txt", b"placeholder", "text/plain")}
    response = client.post(UPLOAD_URL, data=data, files=files)
    assert response.status_code == 201
    return response.json()


def _seed_clauses(
    db_session: Session, *, policy_id: str, policy_version_id: str, text: str
) -> list[PolicyClause]:
    clauses = ClauseSegmentationService().segment(text)
    StoreSegmentedClausesService(ClauseRepository(db_session)).store(
        clauses, policy_id=uuid.UUID(policy_id), policy_version_id=uuid.UUID(policy_version_id)
    )
    return clauses


# --- List clauses for a policy ----------------------------------------------


@pytest.mark.file_retrieval
@pytest.mark.clause_ordering
def test_list_clauses_for_a_policy(
    client: TestClient, db_session: Session, seeded_company_and_user
) -> None:
    upload = _upload(client, seeded_company_and_user, policy_title="Clause List Policy")
    _seed_clauses(
        db_session,
        policy_id=upload["policy_id"],
        policy_version_id=upload["policy_version_id"],
        text="1. Introduction\n\nIntro text.\n\n2. Scope\n\nScope text.",
    )

    response = client.get(CLAUSES_URL, params={"policy_id": upload["policy_id"]})

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 2
    assert [item["clause_number"] for item in body["items"]] == ["1", "2"]
    assert all(item["policy_id"] == upload["policy_id"] for item in body["items"])


@pytest.mark.file_retrieval
def test_list_clauses_filters_by_policy_version(
    client: TestClient, db_session: Session, seeded_company_and_user
) -> None:
    upload = _upload(client, seeded_company_and_user, policy_title="Version Scoped Policy")
    _seed_clauses(
        db_session,
        policy_id=upload["policy_id"],
        policy_version_id=upload["policy_version_id"],
        text="1. Only Clause",
    )

    response = client.get(
        CLAUSES_URL, params={"policy_version_id": upload["policy_version_id"]}
    )

    assert response.status_code == 200
    assert response.json()["total"] == 1


# --- Get clause details -------------------------------------------------------


@pytest.mark.file_retrieval
def test_get_clause_details(
    client: TestClient, db_session: Session, seeded_company_and_user
) -> None:
    upload = _upload(client, seeded_company_and_user, policy_title="Clause Detail Policy")
    clauses = _seed_clauses(
        db_session,
        policy_id=upload["policy_id"],
        policy_version_id=upload["policy_version_id"],
        text="1. Introduction\n\nIntro text.",
    )

    response = client.get(f"{CLAUSES_URL}/{clauses[0].id}")

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == str(clauses[0].id)
    assert body["clause_number"] == "1"
    assert body["heading"] == "Introduction"
    assert body["text"] == "Introduction\n\nIntro text."
    assert body["policy_id"] == upload["policy_id"]
    assert body["policy_version_id"] == upload["policy_version_id"]
    assert body["parent_clause_id"] is None
    assert body["order_index"] == 0


@pytest.mark.error_handling
def test_get_unknown_clause_returns_404(client: TestClient) -> None:
    response = client.get(f"{CLAUSES_URL}/{uuid.uuid4()}")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "clause_not_found"


# --- Search clauses by keyword ------------------------------------------------


@pytest.mark.file_retrieval
def test_search_clauses_by_keyword(
    client: TestClient, db_session: Session, seeded_company_and_user
) -> None:
    upload = _upload(client, seeded_company_and_user, policy_title="Searchable Policy")
    _seed_clauses(
        db_session,
        policy_id=upload["policy_id"],
        policy_version_id=upload["policy_version_id"],
        text=(
            "1. Data Retention\n\nRecords must be retained for seven years.\n\n"
            "2. Access Control\n\nOnly authorized staff may access records."
        ),
    )

    response = client.get(
        CLAUSES_URL, params={"policy_id": upload["policy_id"], "keyword": "authorized"}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["clause_number"] == "2"


@pytest.mark.file_retrieval
def test_search_clauses_by_keyword_is_case_insensitive(
    client: TestClient, db_session: Session, seeded_company_and_user
) -> None:
    upload = _upload(client, seeded_company_and_user, policy_title="Case Insensitive Policy")
    _seed_clauses(
        db_session,
        policy_id=upload["policy_id"],
        policy_version_id=upload["policy_version_id"],
        text="1. Confidentiality\n\nAll STAFF must sign an NDA.",
    )

    response = client.get(
        CLAUSES_URL, params={"policy_id": upload["policy_id"], "keyword": "staff"}
    )

    assert response.status_code == 200
    assert response.json()["total"] == 1


@pytest.mark.file_retrieval
def test_search_clauses_with_no_matches_returns_empty_page(
    client: TestClient, db_session: Session, seeded_company_and_user
) -> None:
    upload = _upload(client, seeded_company_and_user, policy_title="No Match Policy")
    _seed_clauses(
        db_session,
        policy_id=upload["policy_id"],
        policy_version_id=upload["policy_version_id"],
        text="1. Introduction\n\nBody text.",
    )

    response = client.get(
        CLAUSES_URL, params={"policy_id": upload["policy_id"], "keyword": "nonexistentword"}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 0
    assert body["items"] == []


# --- Delete clauses when a policy version is removed --------------------------


@pytest.mark.file_deletion
def test_deleting_the_policy_removes_its_clauses(
    client: TestClient, db_session: Session, seeded_company_and_user
) -> None:
    upload = _upload(client, seeded_company_and_user, policy_title="Policy To Retire")
    clauses = _seed_clauses(
        db_session,
        policy_id=upload["policy_id"],
        policy_version_id=upload["policy_version_id"],
        text="1. Introduction\n\nBody text.",
    )
    clause_id = clauses[0].id

    assert client.get(f"{CLAUSES_URL}/{clause_id}").status_code == 200

    delete_response = client.delete(f"{POLICIES_URL}/{upload['policy_id']}")
    assert delete_response.status_code == 204

    get_response = client.get(f"{CLAUSES_URL}/{clause_id}")
    assert get_response.status_code == 404
    assert get_response.json()["error"]["code"] == "clause_not_found"

    list_response = client.get(CLAUSES_URL, params={"policy_id": upload["policy_id"]})
    assert list_response.json()["total"] == 0
