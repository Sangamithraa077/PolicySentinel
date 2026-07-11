"""SQLAlchemy engine and session factory.

One process-wide `Engine` (and the `QueuePool` it owns) is created at
import time from `Settings` — `create_engine()` is lazy and doesn't open
a connection until first use, so this is safe to do at module scope
rather than deferring to the app's startup event.

Request-scoped `Session` objects are handed out through `get_db()`
(`api/dependencies/database.py`), never through this module directly —
that keeps a single, consistent session lifecycle (one session per
request, closed at the end of it) regardless of which router uses it.
"""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from config.settings import get_settings

settings = get_settings()

engine: Engine = create_engine(
    settings.DATABASE_URL,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_timeout=settings.DB_POOL_TIMEOUT,
    pool_recycle=settings.DB_POOL_RECYCLE_SECONDS,
    # Verifies each pooled connection with a lightweight ping before handing
    # it to a request, so a connection Postgres (or a NAT/LB in between)
    # silently dropped doesn't surface as a query failure mid-request.
    pool_pre_ping=True,
    echo=settings.DB_ECHO,
    future=True,
)

# expire_on_commit=False: ORM objects returned by a service after a commit
# stay usable (e.g. for response serialization) without triggering a fresh
# SELECT on next attribute access.
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)


def get_db_session() -> Generator[Session, None, None]:
    """Yield a `Session`, closing it unconditionally when the caller is done.

    Framework-agnostic generator — `api/dependencies/database.py` wraps
    this as the actual FastAPI `Depends()` provider. Kept separate so it
    can also be used outside a request context (scripts, tests) via
    `contextlib.contextmanager(get_db_session)()`.
    """
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
