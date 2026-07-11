-- =====================================================================
-- PolicySentinel — Postgres container bootstrap
--
-- Alembic now owns the schema (backend/alembic/versions/, starting with
-- *_initial_schema.py) — every table, enum type, constraint, index, and
-- trigger lives there, versioned. This file's only job is to make sure
-- the extensions those migrations depend on exist before any migration
-- runs, since docker-entrypoint-initdb.d scripts execute as the bootstrap
-- superuser (extensions may not be creatable by the app's own DB role).
--
-- Do NOT add tables, types, or indexes here — that would duplicate the
-- migrations and fail the second time either one runs. If you need a
-- schema change, write an Alembic migration (see backend/alembic/README.md).
-- =====================================================================

CREATE EXTENSION IF NOT EXISTS pgcrypto; -- gen_random_uuid()
CREATE EXTENSION IF NOT EXISTS citext; -- case-insensitive email
