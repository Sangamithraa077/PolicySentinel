# tests/ — Automated Tests

- `backend/unit/` — isolated tests for `domain/`, `services/` (with infrastructure mocked via `domain/interfaces/`)
- `backend/integration/` — tests exercising real PostgreSQL/Neo4j via `repositories/`, `graph/`
- `backend/e2e/` — full API request/response tests against a running FastAPI app
- `frontend/` — component and integration tests for the React app

Mirrors the `backend/`/`frontend/` source layout so tests are easy to locate.
