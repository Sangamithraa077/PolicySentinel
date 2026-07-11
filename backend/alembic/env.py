"""Alembic migration environment.

Wired to the FastAPI app's own configuration (`config.settings`) rather
than a separately-maintained connection string, so `alembic upgrade head`
always targets the same database the app connects to — one source of
truth for `DATABASE_URL` (env var / `.env`, see ARCHITECTURE.md §12).

`target_metadata` points at `Base.metadata` after importing `models`, so
`alembic revision --autogenerate` can diff against the full set of ORM
models, not just whichever one happened to be imported first.
"""

from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

import models  # noqa: F401 -- import populates Base.metadata as a side effect
from alembic import context
from config.settings import get_settings
from database.base import Base

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Overwrite whatever (blank) sqlalchemy.url is in alembic.ini with the
# same DATABASE_URL the running application uses.
settings = get_settings()
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode (emits SQL, no DB connection).

    Used by `alembic upgrade head --sql` to preview/export DDL without a
    live database — handy for review or for environments where migrations
    are applied out-of-band.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode against a live connection."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
