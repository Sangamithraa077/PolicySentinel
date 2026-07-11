"""Business-rule violations for clause storage.

Plain Python exceptions, no framework dependency — translated into HTTP
responses at the api/ boundary (see core/exceptions.py), keeping status
codes out of business logic per domain/exceptions/README.md.
"""


class ClauseStorageError(Exception):
    """Raised when a batch of segmented clauses cannot be persisted for a
    policy version — e.g. `policy_id`/`policy_version_id` don't reference
    an existing row, or a clause's `parent_id` doesn't reference another
    clause earlier in the same batch."""


class ClauseNotFoundError(Exception):
    """Raised when a referenced clause_id doesn't exist (or is soft-deleted)."""
