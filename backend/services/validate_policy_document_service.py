"""Use case: validate an uploaded policy document and read its bytes.

Deliberately stops there — it does not store the file (see
services/file_storage_service.py), does not persist any database
records (see services/persist_policy_upload_service.py), does not parse
the document into clauses/obligations, and does not call the AI layer.

Validation is extension-based (the only thing under the client's
control that could be trusted) plus a lightweight content check: a
`Content-Type` header is echoed back as metadata but never trusted for
validation, since browsers set it inconsistently and it's trivial to
spoof. Binary formats are checked against their real file signature
(magic bytes); text formats are checked for the absence of embedded
NUL bytes as a cheap "this probably isn't binary garbage" heuristic.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from fastapi import UploadFile

from domain.exceptions.upload_exceptions import (
    FileTooLargeError,
    InvalidFileContentError,
    UnsupportedFileTypeError,
)

ALLOWED_EXTENSIONS = frozenset({".txt", ".md", ".pdf", ".docx"})

_READ_CHUNK_SIZE = 1024 * 1024  # 1 MiB

# Real file signatures for the binary formats we accept. .docx is a zip
# archive (Office Open XML), so it shares the ordinary zip signature.
_MAGIC_SIGNATURES: dict[str, bytes] = {
    ".pdf": b"%PDF-",
    ".docx": b"PK\x03\x04",
}
_TEXT_EXTENSIONS = frozenset({".txt", ".md"})


@dataclass(frozen=True)
class ValidatedPolicyDocument:
    original_filename: str
    extension: str
    content_type: str
    content: bytes
    size_bytes: int


class ValidatePolicyDocumentService:
    def __init__(self, max_upload_size_mb: int) -> None:
        self._max_bytes = max_upload_size_mb * 1024 * 1024

    async def validate(self, file: UploadFile) -> ValidatedPolicyDocument:
        original_filename = file.filename or "untitled"
        extension = Path(original_filename).suffix.lower()

        if extension not in ALLOWED_EXTENSIONS:
            allowed = ", ".join(sorted(ALLOWED_EXTENSIONS))
            raise UnsupportedFileTypeError(
                f"'{extension or '(no extension)'}' is not a supported file type. "
                f"Allowed types: {allowed}."
            )

        content = await self._read_within_size_limit(file)
        _validate_content_matches_extension(extension, content)

        return ValidatedPolicyDocument(
            original_filename=original_filename,
            extension=extension,
            content_type=file.content_type or "application/octet-stream",
            content=content,
            size_bytes=len(content),
        )

    async def _read_within_size_limit(self, file: UploadFile) -> bytes:
        buffer = bytearray()
        while True:
            chunk = await file.read(_READ_CHUNK_SIZE)
            if not chunk:
                break
            buffer.extend(chunk)
            if len(buffer) > self._max_bytes:
                raise FileTooLargeError(
                    f"File exceeds the maximum allowed size of "
                    f"{self._max_bytes // (1024 * 1024)} MB."
                )
        if not buffer:
            raise InvalidFileContentError("Uploaded file is empty.")
        return bytes(buffer)


def _validate_content_matches_extension(extension: str, content: bytes) -> None:
    signature = _MAGIC_SIGNATURES.get(extension)
    if signature is not None and not content.startswith(signature):
        raise InvalidFileContentError(f"File content does not match its extension ({extension}).")

    if extension in _TEXT_EXTENSIONS and b"\x00" in content:
        raise InvalidFileContentError(
            f"File content does not appear to be plain text, despite the {extension} extension."
        )
