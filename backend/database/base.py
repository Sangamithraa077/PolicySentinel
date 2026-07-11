"""Declarative base shared by every ORM model in `models/`.

Owning this in `database/` (rather than `models/`) keeps the Infrastructure
Layer's persistence plumbing (engine/session factory will live alongside
this) separate from the model definitions themselves.
"""

from __future__ import annotations

from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase

# Stable, greppable constraint/index names for future Alembic autogeneration.
NAMING_CONVENTION = {
    "ix": "ix_%(table_name)s_%(column_0_N_name)s",
    "uq": "uq_%(table_name)s_%(column_0_N_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    """Declarative base for all ORM models.

    The schema itself (types, constraints, indexes, triggers) is owned by
    `docker/postgres/init/001_schema.sql`, not by `Base.metadata.create_all()`
    or Alembic autogeneration — these models map onto that schema, they
    don't generate it. CHECK constraints and partial unique indexes defined
    there are intentionally not re-declared here to avoid two sources of
    truth for the same rule.
    """

    metadata = MetaData(naming_convention=NAMING_CONVENTION)
