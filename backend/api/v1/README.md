# api/v1/ — Version 1 REST Routes

Contains all route modules for API version 1. Each resource (policies, conflicts, uploads, dashboard, auth, etc.) gets its own router file under `endpoints/`, mounted onto a versioned prefix (e.g. `/api/v1/...`) at the application entrypoint.

Keeping versions in separate folders lets the platform evolve the contract (e.g. `/api/v2/`) without breaking existing integrations relied upon by other financial-institution systems.
