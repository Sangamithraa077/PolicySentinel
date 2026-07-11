"""Reusable file storage service.

The one place any feature stores an uploaded artifact and gets back
where it landed plus its metadata. Wraps a `FileStorageInterface` (local
disk today; S3 or any other object store can be swapped in later by
adding a new `repositories/` implementation — this service, and
everything that calls it, stays unchanged) and owns the policy on top
of "write some bytes somewhere":

  - files are organized under companies/{company_id}/policies/{policy_id}/,
    so everything belonging to one company, and one policy within it,
    lives together — the caller supplies those ids, this service doesn't
    know or care where they came from
  - the stored filename is always generated (never the caller's original
    filename — no path-traversal surface, no collisions from two users
    uploading "policy.pdf"), and a collision is actively checked for and
    avoided before writing, not just assumed impossible from UUID entropy
  - every store() returns the path AND the file's metadata (size, hash,
    content type, timestamp) in one result
  - retrieve() reads a stored file back by path (e.g. for downloads),
    translating a missing file into the same domain exception store()
    uses rather than leaking a bare FileNotFoundError

Deliberately narrow: this service only stores/retrieves bytes and
reports back what it stored. It has no opinion on what a valid file
looks like (see services/validate_policy_document_service.py) and
doesn't touch the database (see services/persist_policy_upload_service.py
and services/policy_management_service.py) — keeping it usable for
whatever the next thing that needs to store or read back a file is.
"""

from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime

from domain.exceptions.file_storage_exceptions import FileStorageError
from domain.interfaces.file_storage_interface import FileStorageInterface

_MAX_FILENAME_ATTEMPTS = 5


@dataclass(frozen=True)
class StoredFile:
    storage_path: str
    stored_filename: str
    content_type: str
    size_bytes: int
    sha256: str
    stored_at: datetime


class FileStorageService:
    def __init__(self, storage: FileStorageInterface) -> None:
        self._storage = storage

    def store(
        self,
        content: bytes,
        *,
        company_id: uuid.UUID,
        policy_id: uuid.UUID,
        extension: str,
        content_type: str = "application/octet-stream",
    ) -> StoredFile:
        namespace = f"companies/{company_id}/policies/{policy_id}"
        storage_path = self._unique_path(namespace, extension)
        self._storage.save(storage_path, content, content_type=content_type)

        return StoredFile(
            storage_path=storage_path,
            stored_filename=storage_path.rsplit("/", 1)[-1],
            content_type=content_type,
            size_bytes=len(content),
            sha256=hashlib.sha256(content).hexdigest(),
            stored_at=datetime.now(UTC),
        )

    def retrieve(self, storage_path: str) -> bytes:
        try:
            return self._storage.load(storage_path)
        except FileNotFoundError as exc:
            raise FileStorageError(f"Stored file not found at '{storage_path}'.") from exc

    def delete(self, storage_path: str) -> None:
        self._storage.delete(storage_path)

    def _unique_path(self, namespace: str, extension: str) -> str:
        for _ in range(_MAX_FILENAME_ATTEMPTS):
            candidate = f"{namespace}/{uuid.uuid4().hex}{extension}"
            if not self._storage.exists(candidate):
                return candidate
        raise FileStorageError(
            f"Could not generate a collision-free filename under '{namespace}' "
            f"after {_MAX_FILENAME_ATTEMPTS} attempts."
        )
