# api/ — Presentation Layer

Exposes the system to the outside world over HTTP. This is the **Presentation Layer** in Clean Architecture: it translates HTTP requests into calls against the Application Layer (`services/`) and translates results back into HTTP responses.

## Responsibilities
- Route definitions (REST endpoints) grouped by API version
- Request/response wiring using `schemas/` (never `models/` directly)
- Dependency injection wiring (auth guards, DB sessions, service instances)
- Input validation at the transport boundary

## Structure
- `v1/` — version 1 of the REST API. Future breaking changes get a `v2/` sibling, not a rewrite of `v1/`.
- `v1/endpoints/` — one router module per resource/domain concept (e.g. policies, conflicts, uploads)
- `dependencies/` — FastAPI dependency providers (e.g. `get_current_user`, `get_db_session`)

## Rules of thumb
- No business logic here — endpoints should read like: validate → call service → return response.
- No direct database or graph queries — always go through `services/` and `repositories/`.
