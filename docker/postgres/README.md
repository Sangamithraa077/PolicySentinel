# docker/postgres/ — PostgreSQL Container Config

Uses the official `postgres:16-alpine` image directly (no custom Dockerfile needed).

## `init/`
SQL/shell scripts placed here are executed once, in alphabetical order, by the official Postgres entrypoint **only on first container start** (empty data volume). Mounted read-only into `/docker-entrypoint-initdb.d/` by `docker-compose.yml`.

Intended future use: creating extensions (e.g. `pgcrypto`), initial schemas, or seed reference data — not application migrations (those belong to Alembic, run separately via `scripts/migrations/`).

Currently empty — no initialization logic has been added yet.
