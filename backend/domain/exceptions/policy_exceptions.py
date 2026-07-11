"""Business-rule violations for policy/policy-version persistence.

Plain Python exceptions, no framework dependency — translated into HTTP
responses at the api/ boundary (see core/exceptions.py).
"""


class CompanyNotFoundError(Exception):
    """Raised when a referenced company_id doesn't exist (or is soft-deleted)."""


class UserNotFoundError(Exception):
    """Raised when a referenced user_id doesn't exist (or is soft-deleted)."""


class PolicyNotFoundError(Exception):
    """Raised when a referenced policy_id doesn't exist (or is soft-deleted)."""


class PolicyVersionNotFoundError(Exception):
    """Raised when a policy has no version matching what was asked for
    (e.g. no current version set, or an explicit version_number that
    doesn't exist / is soft-deleted)."""
