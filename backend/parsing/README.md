# parsing/ — Infrastructure Layer: Document Text Extraction

Concrete implementations of `domain/interfaces/document_parser_interface.py` — one per supported file format (`PlainTextDocumentParser` for `.txt`/`.md`, `PdfDocumentParser`, `DocxDocumentParser`). Each wraps a format-specific library (or the stdlib, for plain text) and turns raw bytes into structural plain text; none of them clean whitespace or split text into clauses — see `services/document_parsing_service.py` for orchestration and `utils/text_cleaning.py` for cleanup.

Kept isolated, like `ai/`, `graph/`, and `reasoning/`, so a parsing library can be swapped or a new file format added without touching `services/` business logic.
