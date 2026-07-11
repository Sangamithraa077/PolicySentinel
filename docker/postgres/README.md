# docker/postgres/ — PostgreSQL Container Config

Uses the official `postgres:16-alpine` image directly (no custom Dockerfile needed).

## `init/`
SQL/shell scripts placed here are executed once, in alphabetical order, by the official Postgres entrypoint **only on first container start** (empty data volume). Mounted read-only into `/docker-entrypoint-initdb.d/` by `docker-compose.yml`.

`001_schema.sql` only bootstraps the `pgcrypto`/`citext` extensions — it does **not** create tables, types, or seed data. The schema itself is owned by Alembic (`backend/alembic/versions/`); sample data comes from `scripts/setup/seed_database.py`, run as a separate, repeatable step (not from here), so it also works against a database that wasn't just freshly initialized.
