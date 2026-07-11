"""End-to-end tests for the Policy Upload module — full HTTP requests
against a real FastAPI app (TestClient), a real PostgreSQL test database,
and real disk storage. Exercises every layer together: upload, metadata
storage, retrieval/download, soft-delete, validation, and error handling.
"""

from __future__ import annotations

import io
import uuid
import zipfile

import pytest
from fastapi.testclient import TestClient

UPLOAD_URL = "/api/v1/uploads/policies"
POLICIES_URL = "/api/v1/policies"


def _make_docx_bytes(text: str) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("word/document.xml", f"<w:document>{text}</w:document>")
    return buffer.getvalue()


def _upload(
    client: TestClient,
    seeded_company_and_user,
    *,
    filename: str = "security-policy.txt",
    content: bytes = b"All employees must use MFA.",
    content_type: str = "text/plain",
    policy_title: str = "Security Policy",
    version_number: int = 1,
    description: str | None = "Initial rollout",
    company_id: str | None = None,
    uploaded_by_user_id: str | None = None,
):
    company, user = seeded_company_and_user
    data = {
        "company_id": str(company.id) if company_id is None else company_id,
        "uploaded_by_user_id": str(user.id) if uploaded_by_user_id is None else uploaded_by_user_id,
        "policy_title": policy_title,
        "version_number": str(version_number),
    }
    if description is not None:
        data["description"] = description
    files = {"file": (filename, content, content_type)}
    return client.post(UPLOAD_URL, data=data, files=files)


# --- File upload ---------------------------------------------------------


@pytest.mark.file_upload
def test_upload_returns_201_with_full_metadata(client: TestClient, seeded_company_and_user) -> None:
    company, user = seeded_company_and_user

    response = _upload(client, seeded_company_and_user)

    assert response.status_code == 201
    body = response.json()
    assert body["original_filename"] == "security-policy.txt"
    assert body["extension"] == ".txt"
    assert body["content_type"] == "text/plain"
    assert body["size_bytes"] == len(b"All employees must use MFA.")
    assert body["company_id"] == str(company.id)
    assert body["uploaded_by_user_id"] == str(user.id)
    assert body["policy_title"] == "Security Policy"
    assert body["version_number"] == 1
    assert body["description"] == "Initial rollout"
    assert uuid.UUID(body["policy_id"])
    assert uuid.UUID(body["policy_version_id"])
    assert body["sha256"]
    assert body["uploaded_at"]


@pytest.mark.file_upload
def test_upload_accepts_pdf_and_docx(client: TestClient, seeded_company_and_user) -> None:
    pdf_response = _upload(
        client,
        seeded_company_and_user,
        filename="policy.pdf",
        content=b"%PDF-1.4 minimal pdf bytes",
        content_type="application/pdf",
        policy_title="PDF Policy",
    )
    docx_response = _upload(
        client,
        seeded_company_and_user,
        filename="policy.docx",
        content=_make_docx_bytes("Docx policy body"),
        content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        policy_title="Docx Policy",
    )

    assert pdf_response.status_code == 201
    assert pdf_response.json()["extension"] == ".pdf"
    assert docx_response.status_code == 201
    assert docx_response.json()["extension"] == ".docx"


# --- Metadata storage ------------------------------------------------------


@pytest.mark.metadata_storage
def test_uploaded_policy_metadata_is_visible_via_get_policy(
    client: TestClient, seeded_company_and_user
) -> None:
    upload_response = _upload(client, seeded_company_and_user, policy_title="Retention Policy")
    policy_id = upload_response.json()["policy_id"]

    detail_response = client.get(f"{POLICIES_URL}/{policy_id}")

    assert detail_response.status_code == 200
    detail = detail_response.json()
    assert detail["title"] == "Retention Policy"
    assert detail["status"] == "draft"
    assert len(detail["versions"]) == 1
    version = detail["versions"][0]
    assert version["original_filename"] == "security-policy.txt"
    assert version["is_current"] is True
    assert detail["current_version"]["version_number"] == 1


@pytest.mark.metadata_storage
def test_uploaded_policy_appears_in_list(client: TestClient, seeded_company_and_user) -> None:
    company, _ = seeded_company_and_user
    _upload(client, seeded_company_and_user, policy_title="Listed Policy")

    list_response = client.get(POLICIES_URL, params={"company_id": str(company.id)})

    assert list_response.status_code == 200
    body = list_response.json()
    assert body["total"] == 1
    assert body["items"][0]["title"] == "Listed Policy"


# --- File retrieval (download) ---------------------------------------------


@pytest.mark.file_retrieval
def test_download_returns_the_exact_uploaded_bytes(client: TestClient, seeded_company_and_user) -> None:
    original_content = b"Byte-for-byte identical content check."
    upload_response = _upload(
        client, seeded_company_and_user, content=original_content, filename="download-me.txt"
    )
    policy_id = upload_response.json()["policy_id"]

    download_response = client.get(f"{POLICIES_URL}/{policy_id}/download")

    assert download_response.status_code == 200
    assert download_response.content == original_content
    assert download_response.headers["content-type"].startswith("text/plain")
    assert "download-me.txt" in download_response.headers["content-disposition"]


# --- File deletion (soft delete) --------------------------------------------


@pytest.mark.file_deletion
def test_delete_then_get_returns_404_and_drops_from_list(
    client: TestClient, seeded_company_and_user
) -> None:
    company, _ = seeded_company_and_user
    upload_response = _upload(client, seeded_company_and_user, policy_title="Policy To Delete")
    policy_id = upload_response.json()["policy_id"]

    delete_response = client.delete(f"{POLICIES_URL}/{policy_id}")
    assert delete_response.status_code == 204

    get_response = client.get(f"{POLICIES_URL}/{policy_id}")
    assert get_response.status_code == 404

    list_response = client.get(POLICIES_URL, params={"company_id": str(company.id)})
    assert list_response.json()["total"] == 0


@pytest.mark.file_deletion
def test_delete_does_not_remove_the_file_from_storage(
    client: TestClient, seeded_company_and_user, file_storage_service
) -> None:
    upload_response = _upload(client, seeded_company_and_user, policy_title="Soft Deleted Policy")
    storage_path = upload_response.json()["storage_path"]
    policy_id = upload_response.json()["policy_id"]

    client.delete(f"{POLICIES_URL}/{policy_id}")

    # The underlying bytes are still retrievable directly from storage --
    # only the database record (and the API's view of it) is gone.
    assert file_storage_service.retrieve(storage_path) is not None


# --- Validation --------------------------------------------------------------


@pytest.mark.validation
def test_upload_rejects_unsupported_file_extension(client: TestClient, seeded_company_and_user) -> None:
    response = _upload(
        client,
        seeded_company_and_user,
        filename="malware.exe",
        content=b"binary",
        content_type="application/octet-stream",
    )

    assert response.status_code == 415
    assert response.json()["error"]["code"] == "unsupported_file_type"


@pytest.mark.validation
def test_upload_rejects_empty_file(client: TestClient, seeded_company_and_user) -> None:
    response = _upload(client, seeded_company_and_user, content=b"")

    assert response.status_code == 415
    assert response.json()["error"]["code"] == "invalid_file_content"


@pytest.mark.validation
def test_upload_rejects_file_exceeding_size_limit(client: TestClient, seeded_company_and_user) -> None:
    # conftest.py overrides the validation service with a 1 MB limit for tests.
    oversized_content = b"x" * (1024 * 1024 + 1)

    response = _upload(client, seeded_company_and_user, content=oversized_content)

    assert response.status_code == 413
    assert response.json()["error"]["code"] == "file_too_large"


@pytest.mark.validation
def test_upload_rejects_content_that_does_not_match_extension(
    client: TestClient, seeded_company_and_user
) -> None:
    response = _upload(
        client,
        seeded_company_and_user,
        filename="fake.pdf",
        content=b"this is not a pdf at all",
        content_type="application/pdf",
    )

    assert response.status_code == 415
    assert response.json()["error"]["code"] == "invalid_file_content"


@pytest.mark.validation
def test_upload_rejects_missing_required_form_fields(client: TestClient, seeded_company_and_user) -> None:
    company, _ = seeded_company_and_user
    files = {"file": ("policy.txt", b"content", "text/plain")}

    # policy_title omitted entirely.
    response = client.post(
        UPLOAD_URL,
        data={"company_id": str(company.id), "uploaded_by_user_id": str(uuid.uuid4())},
        files=files,
    )

    assert response.status_code == 422


@pytest.mark.validation
def test_upload_rejects_malformed_company_id(client: TestClient, seeded_company_and_user) -> None:
    response = _upload(client, seeded_company_and_user, company_id="not-a-uuid")

    assert response.status_code == 422


# --- Error handling ----------------------------------------------------------


@pytest.mark.error_handling
def test_upload_returns_404_for_unknown_company(client: TestClient, seeded_company_and_user) -> None:
    response = _upload(client, seeded_company_and_user, company_id=str(uuid.uuid4()))

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "company_not_found"


@pytest.mark.error_handling
def test_upload_returns_404_for_unknown_uploader(client: TestClient, seeded_company_and_user) -> None:
    response = _upload(client, seeded_company_and_user, uploaded_by_user_id=str(uuid.uuid4()))

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "user_not_found"


@pytest.mark.error_handling
def test_get_unknown_policy_returns_404(client: TestClient) -> None:
    response = client.get(f"{POLICIES_URL}/{uuid.uuid4()}")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "policy_not_found"


@pytest.mark.error_handling
def test_download_unknown_policy_returns_404(client: TestClient) -> None:
    response = client.get(f"{POLICIES_URL}/{uuid.uuid4()}/download")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "policy_not_found"


@pytest.mark.error_handling
def test_download_unknown_version_number_returns_404(
    client: TestClient, seeded_company_and_user
) -> None:
    upload_response = _upload(client, seeded_company_and_user, policy_title="Only One Version")
    policy_id = upload_response.json()["policy_id"]

    response = client.get(f"{POLICIES_URL}/{policy_id}/download", params={"version_number": 99})

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "policy_version_not_found"


@pytest.mark.error_handling
def test_delete_unknown_policy_returns_404(client: TestClient) -> None:
    response = client.delete(f"{POLICIES_URL}/{uuid.uuid4()}")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "policy_not_found"


@pytest.mark.error_handling
def test_delete_is_not_repeatable(client: TestClient, seeded_company_and_user) -> None:
    upload_response = _upload(client, seeded_company_and_user, policy_title="Delete Once")
    policy_id = upload_response.json()["policy_id"]

    first = client.delete(f"{POLICIES_URL}/{policy_id}")
    second = client.delete(f"{POLICIES_URL}/{policy_id}")

    assert first.status_code == 204
    assert second.status_code == 404
