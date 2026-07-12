"""End-to-end tests for the Debug REST API endpoints."""

from __future__ import annotations

import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.backend.unit.test_pdf_text_extractor import make_large_pdf

pytestmark = pytest.mark.api_response

UPLOAD_URL = "/api/v1/uploads/policies"
DEBUG_EXTRACT_URL = "/api/v1/debug/extract"


def test_extract_text_endpoint_succeeds_for_pdf(client: TestClient, seeded_company_and_user) -> None:
    company, user = seeded_company_and_user

    # 1. Generate and upload a valid PDF
    pdf_bytes = make_large_pdf("Hello debug page extraction")
    upload_data = {
        "company_id": str(company.id),
        "uploaded_by_user_id": str(user.id),
        "policy_title": "Debug Test Policy",
        "version_number": "1",
    }
    files = {"file": ("test_policy.pdf", pdf_bytes, "application/pdf")}
    
    upload_response = client.post(UPLOAD_URL, data=upload_data, files=files)
    assert upload_response.status_code == 201
    policy_id = upload_response.json()["policy_id"]

    # 2. Query the debug extraction endpoint
    extract_response = client.get(f"{DEBUG_EXTRACT_URL}/{policy_id}")
    print("EXTRACT RESPONSE STATUS:", extract_response.status_code)
    print("EXTRACT RESPONSE JSON:", extract_response.json())
    assert extract_response.status_code == 200

    resp_json = extract_response.json()
    assert resp_json["policy_id"] == policy_id
    assert resp_json["original_filename"] == "test_policy.pdf"
    assert resp_json["text"] == "Hello debug page extraction"
    assert resp_json["extracted_text"] == "Hello debug page extraction"


def test_extract_text_endpoint_returns_404_for_non_existent_policy(client: TestClient) -> None:
    non_existent_id = str(uuid.uuid4())
    response = client.get(f"{DEBUG_EXTRACT_URL}/{non_existent_id}")
    assert response.status_code == 404
    assert "No PDF policy version found" in response.json()["error"]["message"]


def test_extract_text_endpoint_returns_404_for_non_pdf_policy(client: TestClient, seeded_company_and_user) -> None:
    company, user = seeded_company_and_user

    # Upload a text document instead of a PDF
    upload_data = {
        "company_id": str(company.id),
        "uploaded_by_user_id": str(user.id),
        "policy_title": "Debug Test Text Policy",
        "version_number": "1",
    }
    files = {"file": ("test_policy.txt", b"plain text", "text/plain")}
    
    upload_response = client.post(UPLOAD_URL, data=upload_data, files=files)
    assert upload_response.status_code == 201
    policy_id = upload_response.json()["policy_id"]

    # Requesting extraction should fail with 404 since it's not a PDF
    extract_response = client.get(f"{DEBUG_EXTRACT_URL}/{policy_id}")
    assert extract_response.status_code == 404
    assert "No PDF policy version found" in extract_response.json()["error"]["message"]
