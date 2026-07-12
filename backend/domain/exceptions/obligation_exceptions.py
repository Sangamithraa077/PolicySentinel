"""Business-rule exceptions for compliance obligations."""

from __future__ import annotations


class ObligationNotFoundError(Exception):
    """Raised when a referenced obligation_id doesn't exist (or is soft-deleted)."""
