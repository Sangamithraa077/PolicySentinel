"""PDF text extraction, via `pypdf`.

Structure is preserved at page granularity: each page's text is kept
together and pages are joined with a blank line, mirroring how a reader
would perceive page breaks as section breaks. `pypdf` can raise a wide
variety of exception types for malformed or encrypted PDFs (its own
`PdfReadError`, but also `ValueError`/`KeyError` from deep inside its
parser on sufficiently corrupt input) — all of them are normalized to
`DocumentParsingError` here so callers only ever need to handle one
exception type at this boundary, regardless of which library is behind
it.
"""

from __future__ import annotations

import io

from pypdf import PdfReader

from backend.domain.exceptions.parsing_exceptions import DocumentParsingError
from backend.domain.interfaces.document_parser_interface import DocumentParserInterface


class PdfDocumentParser(DocumentParserInterface):
    def parse(self, content: bytes) -> str:
        try:
            reader = PdfReader(io.BytesIO(content))
            pages = [page.extract_text() or "" for page in reader.pages]
        except Exception as exc:
            raise DocumentParsingError(f"Could not read PDF content: {exc}") from exc

        return "\n\n".join(pages)
