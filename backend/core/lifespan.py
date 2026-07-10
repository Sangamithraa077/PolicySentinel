"""Application startup and shutdown lifecycle.

Uses FastAPI's lifespan context manager (the modern replacement for the
deprecated on_event("startup"/"shutdown") hooks). Currently only logs
lifecycle transitions — this is the designated extension point for future
infrastructure wiring (DB connection pools, Neo4j driver, etc.), which is
intentionally not implemented here.
"""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    logger.info("Application startup: PolicySentinel backend initializing")

    # Extension point (not implemented): open PostgreSQL connection pool,
    # open Neo4j driver, warm caches, etc. Attach resources to app.state
    # here so request-scoped dependencies can retrieve them.

    yield

    logger.info("Application shutdown: PolicySentinel backend shutting down")

    # Extension point (not implemented): dispose PostgreSQL connection pool,
    # close Neo4j driver, flush any buffered work.
