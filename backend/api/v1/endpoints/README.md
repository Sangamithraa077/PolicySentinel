# api/v1/endpoints/ — Resource Routers

One file per resource, e.g.:
- `policies.py` — CRUD + listing for uploaded policy documents
- `conflicts.py` — endpoints exposing detected conflict/redundancy/staleness results
- `uploads.py` — file upload endpoints
- `auth.py` — login/refresh/logout endpoints
- `dashboard.py` — aggregate/summary endpoints for the frontend dashboard

Each router only orchestrates calls into `services/` — no business logic, no direct persistence access.
