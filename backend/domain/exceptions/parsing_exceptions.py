"""Business-rule violations for document parsing.

Plain Python exceptions, no framework dependency — translated into HTTP
responses at the api/ boundary (see core/exceptions.py), keeping status
codes out of business logic per domain/exceptions/README.md.
"""


class DocumentParsingError(Exception):
    """Raised when a document's bytes cannot be turned into text — e.g. a
    corrupted PDF or a .docx whose zip package is malformed. Distinct
    from `domain.exceptions.upload_exceptions.InvalidFileContentError`,
    which is decided before parsing is ever attempted (magic bytes only);
    this covers failures that only surface once a format-specific parser
    library actually opens the file."""
