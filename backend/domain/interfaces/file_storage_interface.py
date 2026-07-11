"""Port for persisting uploaded file bytes.

`services/file_storage_service.py` depends only on this interface; the
concrete implementation (local disk today, potentially S3/object
storage later) lives in `repositories/` and is supplied via dependency
injection — the storage mechanism can change without touching the
service's business rules (organization, collision-avoidance, metadata).
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class FileStorageInterface(ABC):
    @abstractmethod
    def save(self, relative_path: str, content: bytes, *, content_type: str | None = None) -> str:
        """Persist `content` at `relative_path` under the storage root.

        `content_type` is accepted so cloud backends (e.g. S3's object
        `ContentType`) can be given it directly; backends with no such
        concept (local disk) are free to ignore it.

        Returns the relative path the content was actually stored at.
        """

    @abstractmethod
    def load(self, relative_path: str) -> bytes:
        """Read back the full content stored at `relative_path`.

        Raises `FileNotFoundError` if nothing is stored there.
        """

    @abstractmethod
    def exists(self, relative_path: str) -> bool:
        """Whether something is already stored at `relative_path`."""

    @abstractmethod
    def delete(self, relative_path: str) -> None:
        """Best-effort removal of a previously stored file."""
