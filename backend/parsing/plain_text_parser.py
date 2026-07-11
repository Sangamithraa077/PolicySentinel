"""Plain text extraction for `.txt` and `.md`.

Both formats already *are* plain text — markdown's structure (headings,
lists, ...) is expressed directly in the characters themselves, so there
is nothing to extract, only bytes to decode. UTF-8 is tried first since
it's the overwhelmingly common case for uploaded documents; a file saved
in a legacy single-byte encoding still decodes (as Latin-1, which maps
every byte to a codepoint and never raises) rather than being rejected.
"""

from __future__ import annotations

from backend.domain.interfaces.document_parser_interface import DocumentParserInterface


class PlainTextDocumentParser(DocumentParserInterface):
    def parse(self, content: bytes) -> str:
        try:
            text = content.decode("utf-8")
        except UnicodeDecodeError:
            text = content.decode("latin-1")
        return text.replace("\r\n", "\n").replace("\r", "\n")
