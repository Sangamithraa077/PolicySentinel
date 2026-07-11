"""DOCX text extraction, via `python-docx`.

Structure is preserved at paragraph/table granularity, walked in
document order via `Document.iter_inner_content()`: each paragraph (a
heading, a list item, a body paragraph, or an intentionally empty
paragraph the author used as a section break) becomes one line, and
each table becomes one line per row with cells joined by " | " — a
readable, tab-free rendering that survives whitespace normalization
(services/text_normalization_service.py) intact rather than being
dropped, since policy documents commonly use tables for things like
obligation/deadline matrices.

`python-docx` can raise a range of exception types for a `.docx` whose
zip package or XML is malformed (its own `PackageNotFoundError`, but
also lower-level exceptions from `lxml`) — normalized to
`DocumentParsingError` here, same rationale as `pdf_parser.py`.
"""

from __future__ import annotations

import io

from docx import Document
from docx.table import Table
from docx.text.paragraph import Paragraph

from backend.domain.exceptions.parsing_exceptions import DocumentParsingError
from backend.domain.interfaces.document_parser_interface import DocumentParserInterface


class DocxDocumentParser(DocumentParserInterface):
    def parse(self, content: bytes) -> str:
        try:
            document = Document(io.BytesIO(content))
            lines = [_render(item) for item in document.iter_inner_content()]
        except Exception as exc:
            raise DocumentParsingError(f"Could not read DOCX content: {exc}") from exc

        return "\n".join(lines)


def _render(item: Paragraph | Table) -> str:
    if isinstance(item, Table):
        return _render_table(item)
    return item.text


def _render_table(table: Table) -> str:
    rows = [" | ".join(cell.text for cell in row.cells) for row in table.rows]
    return "\n".join(rows)
