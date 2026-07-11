"""Business-rule violations for policy document uploads.

Plain Python exceptions, no framework dependency — translated into HTTP
responses at the api/ boundary (see core/exceptions.py), keeping status
codes out of business logic per domain/exceptions/README.md.
"""


class UnsupportedFileTypeError(Exception):
    """Raised when an uploaded file's extension isn't one PolicySentinel accepts."""


class FileTooLargeError(Exception):
    """Raised when an uploaded file exceeds the configured size limit."""


class InvalidFileContentError(Exception):
    """Raised when a file is empty, or its content doesn't match its
    claimed type (e.g. a .pdf whose bytes aren't actually a PDF)."""
