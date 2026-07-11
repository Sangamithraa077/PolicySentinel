"""Application startup and shutdown lifecycle.

Uses FastAPI's lifespan context manager (the modern replacement for the
deprecated on_event("startup"/"shutdown") hooks). The PostgreSQL engine
itself is created eagerly at import time (`database/session.py`) rather
than here — `create_engine()` is lazy and opens no sockets, so there's
nothing to "start"; what belongs here is disposing it cleanly on
shutdown. Neo4j driver wiring remains an extension point (not
implemented here).
"""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from database.session import engine

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    logger.info("Application startup: PolicySentinel backend initializing")

    # Extension point (not implemented): open Neo4j driver, warm caches,
    # etc. Attach resources to app.state here so request-scoped
    # dependencies can retrieve them.

    yield

    logger.info("Application shutdown: PolicySentinel backend shutting down")

    engine.dispose()

    # Extension point (not implemented): close Neo4j driver, flush any
    # buffered work.
