"""Unit tests for FileStorageService against a fake, in-memory
FileStorageInterface — no real disk I/O (see integration/ for that).
Covers path organization, collision handling, and metadata computation.
"""

from __future__ import annotations

import hashlib
import uuid

import pytest

from domain.exceptions.file_storage_exceptions import FileStorageError
from domain.interfaces.file_storage_interface import FileStorageInterface
from services.file_storage_service import FileStorageService


class InMemoryFileStorage(FileStorageInterface):
    def __init__(self) -> None:
        self.files: dict[str, bytes] = {}
        self.saved_content_types: dict[str, str | None] = {}

    def save(self, relative_path: str, content: bytes, *, content_type: str | None = None) -> str:
        self.files[relative_path] = content
        self.saved_content_types[relative_path] = content_type
        return relative_path

    def load(self, relative_path: str) -> bytes:
        if relative_path not in self.files:
            raise FileNotFoundError(relative_path)
        return self.files[relative_path]

    def exists(self, relative_path: str) -> bool:
        return relative_path in self.files

    def delete(self, relative_path: str) -> None:
        self.files.pop(relative_path, None)


@pytest.mark.file_upload
def test_store_organizes_path_by_company_and_policy() -> None:
    storage = InMemoryFileStorage()
    service = FileStorageService(storage)
    company_id = uuid.uuid4()
    policy_id = uuid.uuid4()

    stored = service.store(
        b"content", company_id=company_id, policy_id=policy_id, extension=".txt"
    )

    expected_prefix = f"companies/{company_id}/policies/{policy_id}/"
    assert stored.storage_path.startswith(expected_prefix)
    assert stored.storage_path.endswith(".txt")
    assert stored.stored_filename == stored.storage_path.rsplit("/", 1)[-1]
    assert storage.exists(stored.storage_path)


@pytest.mark.metadata_storage
def test_store_returns_correct_metadata() -> None:
    storage = InMemoryFileStorage()
    service = FileStorageService(storage)
    content = b"policy document bytes"

    stored = service.store(
        content,
        company_id=uuid.uuid4(),
        policy_id=uuid.uuid4(),
        extension=".pdf",
        content_type="application/pdf",
    )

    assert stored.size_bytes == len(content)
    assert stored.sha256 == hashlib.sha256(content).hexdigest()
    assert stored.content_type == "application/pdf"
    assert stored.stored_at is not None


@pytest.mark.file_upload
def test_store_never_reuses_the_caller_supplied_filename() -> None:
    # Two uploads of files that would otherwise collide by original name
    # must never collide on disk -- the stored filename is always generated.
    storage = InMemoryFileStorage()
    service = FileStorageService(storage)
    company_id, policy_id = uuid.uuid4(), uuid.uuid4()

    first = service.store(b"a", company_id=company_id, policy_id=policy_id, extension=".txt")
    second = service.store(b"b", company_id=company_id, policy_id=policy_id, extension=".txt")

    assert first.storage_path != second.storage_path
    assert storage.exists(first.storage_path)
    assert storage.exists(second.storage_path)


@pytest.mark.error_handling
def test_store_raises_file_storage_error_when_collision_free_name_cannot_be_found(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    storage = InMemoryFileStorage()
    service = FileStorageService(storage)
    # Force exists() to always report a collision, simulating exhausted retries.
    monkeypatch.setattr(storage, "exists", lambda relative_path: True)

    with pytest.raises(FileStorageError):
        service.store(b"content", company_id=uuid.uuid4(), policy_id=uuid.uuid4(), extension=".txt")


@pytest.mark.file_retrieval
def test_retrieve_returns_stored_content() -> None:
    storage = InMemoryFileStorage()
    service = FileStorageService(storage)
    stored = service.store(b"retrievable content", company_id=uuid.uuid4(), policy_id=uuid.uuid4(), extension=".txt")

    assert service.retrieve(stored.storage_path) == b"retrievable content"


@pytest.mark.file_retrieval
@pytest.mark.error_handling
def test_retrieve_translates_missing_file_into_file_storage_error() -> None:
    storage = InMemoryFileStorage()
    service = FileStorageService(storage)

    with pytest.raises(FileStorageError):
        service.retrieve("companies/does/not/exist.txt")


@pytest.mark.file_deletion
def test_delete_removes_stored_file() -> None:
    storage = InMemoryFileStorage()
    service = FileStorageService(storage)
    stored = service.store(b"to be deleted", company_id=uuid.uuid4(), policy_id=uuid.uuid4(), extension=".txt")

    service.delete(stored.storage_path)

    assert not storage.exists(stored.storage_path)
