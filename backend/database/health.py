"""Database connectivity health check.

Used by `api/health.py` to report whether PostgreSQL is actually
reachable, not just whether the process is alive.
"""

import logging

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from database.session import engine

logger = logging.getLogger(__name__)


def check_database_connection() -> bool:
    """Borrow a pooled connection and run a trivial round-trip query.

    Returns False rather than raising — this is a status check, not a
    request that should fail loudly.
    """
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return True
    except SQLAlchemyError:
        logger.warning("Database health check failed", exc_info=True)
        return False
