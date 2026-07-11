# scripts/ — Operational Scripts

- `setup/` — one-time environment bootstrap scripts (installing dependencies, seeding config)
  - `seed_database.py` — populates a local Postgres with sample companies, departments, users, policies/versions, and regulatory reference data. Idempotent (skips if already seeded); run with `python scripts/setup/seed_database.py` after `alembic upgrade head`.
  - `verify_database.py` — checks connectivity, migration status, table creation, relationships (FK constraints + seeded data resolving correctly), and seed data; prints a report and writes it to `backend/logs/db_verification_report.txt`. Exits non-zero on failure, so it doubles as a CI/pre-flight gate. Run with `python scripts/setup/verify_database.py` any time after `seed_database.py`.
- `migrations/` — database/graph schema migration helper scripts (wraps Alembic/Neo4j migration tooling)
- `deployment/` — build/deploy helper scripts for CI/CD

Kept outside `backend/` and `frontend/` since these operate across the whole stack.
