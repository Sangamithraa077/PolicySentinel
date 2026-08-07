"""Postgres-backed implementation of `FileStorageInterface`.

Stores file bytes as rows in the `stored_files` table instead of on local
disk — see `models/file_blob.py` for why (Render's free-tier ephemeral
disk loses everything `LocalFileStorageRepository` writes on every
redeploy).

Deliberately reuses the caller's own request-scoped `Session` rather than
opening a separate connection: a `save()` only `flush()`es, it doesn't
commit, so when this is used from a write flow that shares its session
(e.g. `PersistPolicyUploadService`, via `api/dependencies/uploads.py`),
the file row becomes part of the *same* transaction as the Policy/
PolicyVersion rows it belongs to — both commit together, or both roll
back together, exactly like `LocalFileStorageRepository`'s disk write
plus that same service's explicit delete-on-failure achieved before, just
without a separate compensating action needed.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.domain.interfaces.file_storage_interface import FileStorageInterface
from backend.models.file_blob import FileBlob


class PostgresFileStorageRepository(FileStorageInterface):
    def __init__(self, db: Session) -> None:
        self._db = db

    def save(self, relative_path: str, content: bytes, *, content_type: str | None = None) -> str:
        self._db.add(
            FileBlob(
                storage_path=relative_path,
                content=content,
                content_type=content_type,
                size_bytes=len(content),
            )
        )
        # Flushed (not committed) so a duplicate storage_path surfaces here,
        # against the collision-avoidance loop in FileStorageService, rather
        # than at some later unrelated flush/commit in the same request.
        self._db.flush()
        return relative_path

    def load(self, relative_path: str) -> bytes:
        content = self._db.scalar(
            select(FileBlob.content).where(FileBlob.storage_path == relative_path)
        )
        if content is None:
            raise FileNotFoundError(relative_path)
        return content

    def exists(self, relative_path: str) -> bool:
        return (
            self._db.scalar(
                select(FileBlob.storage_path).where(FileBlob.storage_path == relative_path)
            )
            is not None
        )

    def delete(self, relative_path: str) -> None:
        blob = self._db.get(FileBlob, relative_path)
        if blob is not None:
            self._db.delete(blob)
