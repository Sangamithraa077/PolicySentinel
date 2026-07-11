"""Use case: turn an uploaded policy document's raw bytes into clean,
structure-preserving plain text.

Deliberately stops there — it does not split the text into clauses (see
domain/README.md's note on the future Knowledge Graph ingestion use
case) and does not call the AI layer. It only extracts and cleans text.

Dispatches to one `DocumentParserInterface` implementation per
extension via a plain dict registry, so adding a new document type is
"write a parser in parsing/, add one line to the registry" rather than
a change to this service's logic. `build_default_document_parsing_service()`
wires up the registry this codebase currently supports (.txt, .md,
.pdf, .docx); callers that want a different set of formats can
construct `DocumentParsingService` directly with their own mapping.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from backend.domain.exceptions.upload_exceptions import UnsupportedFileTypeError
from backend.domain.interfaces.document_parser_interface import DocumentParserInterface
from backend.parsing.docx_parser import DocxDocumentParser
from backend.parsing.pdf_parser import PdfDocumentParser
from backend.parsing.plain_text_parser import PlainTextDocumentParser
from backend.utils.text_cleaning import clean_extracted_text


@dataclass(frozen=True)
class ParsedDocument:
    text: str
    extension: str
    character_count: int


class DocumentParsingService:
    def __init__(self, parsers: Mapping[str, DocumentParserInterface]) -> None:
        self._parsers = dict(parsers)

    def parse(self, content: bytes, extension: str) -> ParsedDocument:
        normalized = extension.lower()
        parser = self._parsers.get(normalized)
        if parser is None:
            allowed = ", ".join(sorted(self._parsers))
            raise UnsupportedFileTypeError(
                f"'{normalized or '(no extension)'}' has no registered document parser. "
                f"Supported types: {allowed}."
            )

        text = clean_extracted_text(parser.parse(content))
        return ParsedDocument(text=text, extension=normalized, character_count=len(text))


def build_default_document_parsing_service() -> DocumentParsingService:
    text_parser = PlainTextDocumentParser()
    return DocumentParsingService(
        {
            ".txt": text_parser,
            ".md": text_parser,
            ".pdf": PdfDocumentParser(),
            ".docx": DocxDocumentParser(),
        }
    )
