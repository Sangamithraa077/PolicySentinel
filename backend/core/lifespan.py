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

from backend.database.session import engine
from backend.graph.neo4j_client import Neo4jClient

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    logger.info("Application startup: PolicySentinel backend initializing")

    # Initialize Neo4j client and verify connectivity
    try:
        neo4j_client = Neo4jClient()
        neo4j_client.verify_connectivity()
        app.state.neo4j_client = neo4j_client
    except Exception as exc:
        logger.error("Failed to initialize or connect to Neo4j during startup: %s", exc)

    yield

    logger.info("Application shutdown: PolicySentinel backend shutting down")

    engine.dispose()

    # Close Neo4j driver
    if hasattr(app.state, "neo4j_client") and app.state.neo4j_client:
        try:
            app.state.neo4j_client.close()
        except Exception as exc:
            logger.error("Error closing Neo4j client during lifespan shutdown: %s", exc)
