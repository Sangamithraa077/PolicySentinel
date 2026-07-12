"""Neo4j Database Client for managing driver lifecycle and graph connectivity."""
from __future__ import annotations

import logging
import neo4j
from typing import Generator, Any
from contextlib import contextmanager

from backend.config.settings import Settings, get_settings

logger = logging.getLogger(__name__)


class Neo4jClient:
    _instance: Neo4jClient | None = None
    _driver: neo4j.Driver | None = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(Neo4jClient, cls).__new__(cls)
        return cls._instance

    def __init__(self, settings: Settings | None = None) -> None:
        if self._driver is not None:
            return

        self._settings = settings or get_settings()
        uri = self._settings.NEO4J_URI
        user = self._settings.NEO4J_USER
        password = self._settings.NEO4J_PASSWORD

        logger.info("Initializing Neo4j driver at URI: %s", uri)
        try:
            self._driver = neo4j.GraphDatabase.driver(
                uri,
                auth=(user, password)
            )
        except Exception as exc:
            logger.error("Failed to initialize Neo4j driver: %s", exc)
            self._driver = None

    def verify_connectivity(self) -> bool:
        """Verifies if the connection to the Neo4j database is active and healthy."""
        if not self._driver:
            logger.error("Neo4j driver is not initialized.")
            return False

        try:
            # Under newer versions of Neo4j driver, verify_connectivity() is available on the driver instance
            self._driver.verify_connectivity()
            logger.info("Successfully verified connectivity to Neo4j graph database.")
            return True
        except Exception as exc:
            logger.error("Connectivity verification failed with Neo4j database: %s", exc)
            return False

    @contextmanager
    def get_session(self, database: str = "neo4j", **kwargs) -> Generator[neo4j.Session, None, None]:
        """Provides a context-managed Neo4j database session."""
        if not self._driver:
            raise RuntimeError("Cannot open session: Neo4j driver is not initialized.")

        session = self._driver.session(database=database, **kwargs)
        try:
            yield session
        finally:
            session.close()

    def close(self) -> None:
        """Closes the active Neo4j driver session pool."""
        if self._driver:
            logger.info("Closing Neo4j database driver connection pool.")
            try:
                self._driver.close()
            except Exception as exc:
                logger.error("Error closing Neo4j driver: %s", exc)
            finally:
                self._driver = None
                Neo4jClient._driver = None
