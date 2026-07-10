# domain/exceptions/ — Domain-Specific Exceptions

Custom exception types representing business rule violations (e.g. `PolicyConflictDetectedError`, `InvalidPolicyDocumentError`, `StalePolicyError`). These are raised by `domain/` and `services/` code and translated into HTTP responses at the `api/` boundary — keeping HTTP status codes out of business logic.
