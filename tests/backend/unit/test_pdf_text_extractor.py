"""Unit tests for the PDF text extraction service (using PyMuPDF)."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from backend.domain.exceptions.parsing_exceptions import DocumentParsingError
from backend.parsing.pdf_text_extractor import extract_text


def make_large_pdf(*page_texts: str) -> bytes:
    """Hand-build a multi-page PDF with a wide MediaBox to prevent PyMuPDF
    from clipping long lines of text during extraction."""
    objs: list[bytes] = [b"<</Type/Catalog/Pages 2 0 R>>"]
    page_count = len(page_texts)
    kids = " ".join(f"{3 + i} 0 R" for i in range(page_count))
    objs.append(f"<</Type/Pages/Kids[{kids}]/Count {page_count}>>".encode())
    content_obj_start = 3 + page_count
    font_obj = content_obj_start + page_count
    for i in range(page_count):
        objs.append(
            (
                f"<</Type/Page/Parent 2 0 R/Resources<</Font<</F1 {font_obj} 0 R>>>>"
                f"/MediaBox[0 0 1000 200]/Contents {content_obj_start + i} 0 R>>"
            ).encode()
        )
    for text in page_texts:
        stream = f"BT /F1 24 Tf 10 100 Td ({text}) Tj ET".encode()
        objs.append(b"<</Length %d>>\nstream\n%s\nendstream" % (len(stream), stream))
    objs.append(b"<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>")

    buf = bytearray(b"%PDF-1.4\n")
    offsets = []
    for i, obj in enumerate(objs, start=1):
        offsets.append(len(buf))
        buf += f"{i} 0 obj".encode() + obj + b"endobj\n"
    xref_offset = len(buf)
    buf += f"xref\n0 {len(objs) + 1}\n".encode()
    buf += b"0000000000 65535 f \n"
    for offset in offsets:
        buf += f"{offset:010d} 00000 n \n".encode()
    buf += f"trailer<</Size {len(objs) + 1}/Root 1 0 R>>\nstartxref\n{xref_offset}\n%%EOF".encode()
    return bytes(buf)


def test_extract_text_succeeds_with_valid_pdf() -> None:
    # Construct a minimal PDF with 2 pages
    pdf_bytes = make_large_pdf("Hello page one", "Hello page two")

    with tempfile.TemporaryDirectory() as tmpdir:
        pdf_path = Path(tmpdir) / "test.pdf"
        pdf_path.write_bytes(pdf_bytes)

        # Extract text and verify
        extracted = extract_text(pdf_path)
        
        assert "Hello page one" in extracted
        assert "Hello page two" in extracted
        assert "\n\n" in extracted  # Verify pages/blocks are joined with spacing


def test_extract_text_cleans_excess_whitespace() -> None:
    # PDF page with excess spacing
    pdf_bytes = make_large_pdf("Hello    page    one    with    excess    spaces")

    with tempfile.TemporaryDirectory() as tmpdir:
        pdf_path = Path(tmpdir) / "test.pdf"
        pdf_path.write_bytes(pdf_bytes)

        extracted = extract_text(pdf_path)
        assert extracted == "Hello page one with excess spaces"


def test_extract_text_raises_on_invalid_pdf_path() -> None:
    # Passing a non-existent path should raise DocumentParsingError
    with pytest.raises(DocumentParsingError) as exc_info:
        extract_text("non_existent_file_path_12345.pdf")
        
    assert "Failed to open PDF file" in str(exc_info.value)
