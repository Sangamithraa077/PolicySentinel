"""Integration tests for LocalFileStorageRepository — real disk I/O
against a temp directory (tmp_path). No database involved.
"""

from __future__ import annotations

import stat
import sys
from pathlib import Path

import pytest

from backend.repositories.local_file_storage_repository import LocalFileStorageRepository

_IS_WINDOWS = sys.platform.startswith("win")


@pytest.mark.file_upload
def test_save_writes_file_to_disk_under_the_storage_root(tmp_path: Path) -> None:
    repo = LocalFileStorageRepository(tmp_path)

    repo.save("companies/c1/policies/p1/doc.txt", b"hello policy")

    written = tmp_path / "companies" / "c1" / "policies" / "p1" / "doc.txt"
    assert written.exists()
    assert written.read_bytes() == b"hello policy"


@pytest.mark.file_retrieval
def test_load_round_trips_saved_content(tmp_path: Path) -> None:
    repo = LocalFileStorageRepository(tmp_path)
    repo.save("a/b/doc.txt", b"round trip me")

    assert repo.load("a/b/doc.txt") == b"round trip me"


@pytest.mark.error_handling
def test_load_missing_file_raises_file_not_found_error(tmp_path: Path) -> None:
    repo = LocalFileStorageRepository(tmp_path)

    with pytest.raises(FileNotFoundError):
        repo.load("does/not/exist.txt")


def test_exists_reflects_disk_state(tmp_path: Path) -> None:
    repo = LocalFileStorageRepository(tmp_path)

    assert not repo.exists("a/doc.txt")
    repo.save("a/doc.txt", b"content")
    assert repo.exists("a/doc.txt")


@pytest.mark.file_deletion
def test_delete_removes_file_from_disk(tmp_path: Path) -> None:
    repo = LocalFileStorageRepository(tmp_path)
    repo.save("a/doc.txt", b"content")

    repo.delete("a/doc.txt")

    assert not repo.exists("a/doc.txt")
    assert not (tmp_path / "a" / "doc.txt").exists()


@pytest.mark.file_deletion
def test_delete_of_missing_file_is_a_no_op() -> None:
    repo = LocalFileStorageRepository(Path.cwd())
    # Should not raise even though nothing was ever stored at this path.
    repo.delete("never/existed.txt")


@pytest.mark.error_handling
@pytest.mark.validation
def test_path_traversal_outside_the_storage_root_is_rejected(tmp_path: Path) -> None:
    repo = LocalFileStorageRepository(tmp_path)

    with pytest.raises(ValueError):
        repo.save("../../etc/passwd", b"malicious")


@pytest.mark.skipif(_IS_WINDOWS, reason="POSIX permission bits are a no-op on Windows")
def test_saved_files_and_directories_are_owner_only_on_posix(tmp_path: Path) -> None:
    repo = LocalFileStorageRepository(tmp_path)
    repo.save("a/b/doc.txt", b"content")

    file_mode = stat.S_IMODE((tmp_path / "a" / "b" / "doc.txt").stat().st_mode)
    dir_mode = stat.S_IMODE((tmp_path / "a" / "b").stat().st_mode)

    assert file_mode == stat.S_IRUSR | stat.S_IWUSR
    assert dir_mode == stat.S_IRWXU
