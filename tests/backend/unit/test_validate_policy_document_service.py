"""Unit tests for ValidatePolicyDocumentService — pure logic, no I/O, no
database, no HTTP. Covers the "Validation" and "Error handling"
verification categories for the Policy Upload module.
"""

from __future__ import annotations

import io

import pytest
from starlette.datastructures import Headers, UploadFile

from backend.domain.exceptions.upload_exceptions import (
    FileTooLargeError,
    InvalidFileContentError,
    UnsupportedFileTypeError,
)
from backend.services.validate_policy_document_service import ValidatePolicyDocumentService

pytestmark = pytest.mark.asyncio


def make_upload_file(filename: str, content: bytes, content_type: str = "application/octet-stream") -> UploadFile:
    return UploadFile(
        file=io.BytesIO(content),
        filename=filename,
        headers=Headers({"content-type": content_type}),
    )


@pytest.mark.validation
async def test_valid_txt_file_passes_validation() -> None:
    service = ValidatePolicyDocumentService(max_upload_size_mb=1)
    upload = make_upload_file("policy.txt", b"Some plain text policy content.", "text/plain")

    result = await service.validate(upload)

    assert result.original_filename == "policy.txt"
    assert result.extension == ".txt"
    assert result.content_type == "text/plain"
    assert result.size_bytes == len(b"Some plain text policy content.")
    assert result.content == b"Some plain text policy content."


@pytest.mark.validation
async def test_valid_md_file_passes_validation() -> None:
    service = ValidatePolicyDocumentService(max_upload_size_mb=1)
    upload = make_upload_file("policy.md", b"# Heading\n\nBody.", "text/markdown")

    result = await service.validate(upload)

    assert result.extension == ".md"


@pytest.mark.validation
async def test_valid_pdf_file_passes_validation() -> None:
    service = ValidatePolicyDocumentService(max_upload_size_mb=1)
    upload = make_upload_file("policy.pdf", b"%PDF-1.4 fake but correctly signed", "application/pdf")

    result = await service.validate(upload)

    assert result.extension == ".pdf"


@pytest.mark.validation
async def test_valid_docx_file_passes_validation() -> None:
    service = ValidatePolicyDocumentService(max_upload_size_mb=1)
    upload = make_upload_file(
        "policy.docx",
        b"PK\x03\x04 fake but correctly signed zip header",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )

    result = await service.validate(upload)

    assert result.extension == ".docx"


@pytest.mark.validation
@pytest.mark.error_handling
async def test_unsupported_extension_is_rejected() -> None:
    service = ValidatePolicyDocumentService(max_upload_size_mb=1)
    upload = make_upload_file("policy.exe", b"binary content", "application/octet-stream")

    with pytest.raises(UnsupportedFileTypeError):
        await service.validate(upload)


@pytest.mark.validation
@pytest.mark.error_handling
async def test_missing_extension_is_rejected() -> None:
    service = ValidatePolicyDocumentService(max_upload_size_mb=1)
    upload = make_upload_file("policy_without_extension", b"content", "text/plain")

    with pytest.raises(UnsupportedFileTypeError):
        await service.validate(upload)


@pytest.mark.validation
@pytest.mark.error_handling
async def test_empty_file_is_rejected() -> None:
    service = ValidatePolicyDocumentService(max_upload_size_mb=1)
    upload = make_upload_file("policy.txt", b"", "text/plain")

    with pytest.raises(InvalidFileContentError):
        await service.validate(upload)


@pytest.mark.validation
@pytest.mark.error_handling
async def test_oversized_file_is_rejected() -> None:
    service = ValidatePolicyDocumentService(max_upload_size_mb=1)
    oversized_content = b"x" * (1024 * 1024 + 1)
    upload = make_upload_file("policy.txt", oversized_content, "text/plain")

    with pytest.raises(FileTooLargeError):
        await service.validate(upload)


@pytest.mark.validation
@pytest.mark.error_handling
async def test_pdf_extension_with_non_pdf_content_is_rejected() -> None:
    service = ValidatePolicyDocumentService(max_upload_size_mb=1)
    upload = make_upload_file("policy.pdf", b"this is not really a pdf", "application/pdf")

    with pytest.raises(InvalidFileContentError):
        await service.validate(upload)


@pytest.mark.validation
@pytest.mark.error_handling
async def test_docx_extension_with_non_zip_content_is_rejected() -> None:
    service = ValidatePolicyDocumentService(max_upload_size_mb=1)
    upload = make_upload_file(
        "policy.docx",
        b"not a zip archive",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )

    with pytest.raises(InvalidFileContentError):
        await service.validate(upload)


@pytest.mark.validation
@pytest.mark.error_handling
async def test_text_extension_with_embedded_nul_byte_is_rejected() -> None:
    service = ValidatePolicyDocumentService(max_upload_size_mb=1)
    upload = make_upload_file("policy.txt", b"looks like text\x00but has a NUL byte", "text/plain")

    with pytest.raises(InvalidFileContentError):
        await service.validate(upload)


@pytest.mark.validation
async def test_content_type_header_is_echoed_but_not_trusted_for_validation() -> None:
    # A .txt file whose client-supplied Content-Type is wrong should still
    # pass -- the extension + magic-byte/NUL-byte checks are authoritative,
    # not the browser-supplied header.
    service = ValidatePolicyDocumentService(max_upload_size_mb=1)
    upload = make_upload_file("policy.txt", b"plain text content", "application/pdf")

    result = await service.validate(upload)

    assert result.content_type == "application/pdf"
    assert result.extension == ".txt"
