# models/ — Infrastructure Layer: ORM Models

SQLAlchemy ORM models mapping `domain/entities/` to PostgreSQL tables. These are persistence-framework-specific and belong to the **Infrastructure Layer** — the Domain Layer must never import from here directly.

Kept separate from `schemas/` (API DTOs) so that database structure can evolve independently of the public API contract.
