# scripts/ — Operational Scripts

- `setup/` — one-time environment bootstrap scripts (installing dependencies, seeding config)
- `migrations/` — database/graph schema migration helper scripts (wraps Alembic/Neo4j migration tooling)
- `deployment/` — build/deploy helper scripts for CI/CD

Kept outside `backend/` and `frontend/` since these operate across the whole stack.
