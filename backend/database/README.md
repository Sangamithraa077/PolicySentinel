# database/ — Infrastructure Layer: Persistence Setup

Owns the low-level connection lifecycle for PostgreSQL (e.g. SQLAlchemy engine/session factory, connection pooling, Alembic migration wiring). This is **Infrastructure Layer** — it implements persistence concerns that the Domain and Application layers depend on only through abstractions (`repositories/`).

## Typical contents (once implemented)
- Engine/session factory
- Base declarative model class
- Alembic migration environment
- Health-check helpers for the database connection
