# auth/ — Infrastructure/Application: JWT Authentication

Handles JWT token issuance, validation, and refresh logic, plus password hashing utilities. Exposes services consumed by `api/dependencies/` (e.g. `get_current_user`) and `api/v1/endpoints/auth.py`.

Kept as its own module (rather than folded into `services/`) because authentication is a cross-cutting infrastructure concern used by nearly every request, not a single business use case.
