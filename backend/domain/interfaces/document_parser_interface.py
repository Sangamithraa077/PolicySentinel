"""Port for turning a document's raw bytes into structural plain text.

`services/document_parsing_service.py` depends only on this interface
and dispatches to one implementation per file extension; concrete
implementations (PDF, DOCX, plain text today) live in `parsing/` and are
registered with the service via dependency injection — a new document
type is added by writing one new implementation and registering it,
without touching the service or any existing parser.

Implementations extract structure (paragraph/page breaks) but are not
responsible for whitespace cleanup — that is centralized in
`utils/text_cleaning.py` so every format benefits identically and a new
parser doesn't need to reimplement it.
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class DocumentParserInterface(ABC):
    @abstractmethod
    def parse(self, content: bytes) -> str:
        """Extract structural plain text from a document's raw bytes.

        Raises `domain.exceptions.parsing_exceptions.DocumentParsingError`
        if `content` cannot be read as this parser's format.
        """
