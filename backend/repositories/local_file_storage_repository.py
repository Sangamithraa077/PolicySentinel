"""Local-disk implementation of `FileStorageInterface`.

Writes under a fixed storage root (`Settings.UPLOAD_DIR`); every path is
resolved and checked against that root before any filesystem write, so a
`relative_path` can never escape it — defense in depth, since callers in
practice only ever pass paths this codebase generated itself, never raw
user input.

Directories are created `0700` and files `0600` (owner-only) — belt and
suspenders on top of path containment, since these files may contain
sensitive policy content. On Windows this is a no-op (POSIX permission
bits don't apply), which is fine: the primary deployment target is the
Linux containers in docker/backend/.
"""

from __future__ import annotations

import os
import stat
from pathlib import Path

from backend.domain.interfaces.file_storage_interface import FileStorageInterface

_DIR_MODE = stat.S_IRWXU  # 0o700
_FILE_MODE = stat.S_IRUSR | stat.S_IWUSR  # 0o600


class LocalFileStorageRepository(FileStorageInterface):
    def __init__(self, root: Path) -> None:
        self._root = root.resolve()
        self._root.mkdir(parents=True, exist_ok=True)
        os.chmod(self._root, _DIR_MODE)

    def save(self, relative_path: str, content: bytes, *, content_type: str | None = None) -> str:
        # content_type has no local-filesystem equivalent (it exists for
        # cloud backends, e.g. S3's ContentType) -- intentionally unused.
        destination = self._resolve(relative_path)
        self._mkdir_secure(destination.parent)
        destination.write_bytes(content)
        os.chmod(destination, _FILE_MODE)
        return relative_path

    def load(self, relative_path: str) -> bytes:
        return self._resolve(relative_path).read_bytes()

    def exists(self, relative_path: str) -> bool:
        return self._resolve(relative_path).exists()

    def delete(self, relative_path: str) -> None:
        self._resolve(relative_path).unlink(missing_ok=True)

    def _resolve(self, relative_path: str) -> Path:
        destination = (self._root / relative_path).resolve()
        if destination != self._root and self._root not in destination.parents:
            raise ValueError(f"'{relative_path}' escapes the storage root")
        return destination

    def _mkdir_secure(self, directory: Path) -> None:
        """Create `directory` (and any missing parents under the storage
        root) as 0700 — `Path.mkdir(parents=True, mode=...)` only applies
        `mode` to the leaf directory, not the parents it creates along
        the way, so each level needs an explicit chmod."""
        to_create = []
        current = directory
        while current != self._root and not current.exists():
            to_create.append(current)
            current = current.parent
        directory.mkdir(parents=True, exist_ok=True)
        for created in to_create:
            os.chmod(created, _DIR_MODE)
